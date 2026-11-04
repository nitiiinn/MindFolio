"""FastAPI backend for the MindFolio React frontend.

Wraps the same ingestion / retrieval / llm / generation modules that app.py
(the Streamlit UI) uses, and exposes them as a small REST API.

Run locally:
    uvicorn server:app --reload --port 8000
"""
import os
import logging
import warnings
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

logging.getLogger("transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=r".*Accessing `__path__`.*")

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from ingestion.loader import load_multiple_pdfs
from ingestion.splitter import split_documents
from ingestion.embeddings import load_embedding_model
from ingestion.vectordb import create_vectorstore

from retrieval.retriever import create_retriever

from llm.model import answer_question, load_model_router
from llm.prompt import load_prompt, load_history_summarizer_prompt

from generation.notes_gen import generate_notes_content, build_notes_pdf, _parse_sections
from generation.quiz_gen import generate_quiz_content, build_quiz_pdf, _parse_quiz
from generation.flashcards_gen import generate_flashcards_content, build_flashcards_pdf

load_dotenv()

SESSION_TTL_SECONDS = 60 * 60

app = FastAPI(title="MindFolio API")

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed_origins.split(",") if o.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception):
    # Surface model/provider failures to the UI as a readable message instead of a bare 500.
    logging.getLogger("mindfolio").exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})

# ── Shared, lazily-created clients (same caching app.py does per session) ────
_shared = {"embedding_model": None, "router": None, "prompt": None}
_shared_lock = threading.Lock()


def _get_shared():
    with _shared_lock:
        if _shared["embedding_model"] is None:
            _shared["embedding_model"] = load_embedding_model()
        if _shared["router"] is None:
            _shared["router"] = load_model_router()
        if _shared["prompt"] is None:
            _shared["prompt"] = load_prompt()
    return _shared


# ── In-memory session store (replaces st.session_state) ──────────────────────
_sessions: dict[str, dict] = {}
_sessions_lock = threading.Lock()


def _expire_sessions():
    now = time.time()
    with _sessions_lock:
        for sid in [s for s, v in _sessions.items() if now - v["last_used"] > SESSION_TTL_SECONDS]:
            del _sessions[sid]


def _get_session(session_id: str) -> dict:
    _expire_sessions()
    with _sessions_lock:
        session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired. Please upload your documents again.")
    session["last_used"] = time.time()
    return session


def _stats(session: dict) -> dict:
    return {
        "files": session["files"],
        "pages": session["total_pages"],
        "chunks": session["total_chunks"],
        "queries": len(session["messages"]) // 2,
    }


# ── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/upload")
def upload(files: list[UploadFile] = File(...)):
    pdfs = [f for f in files if f.filename and f.filename.lower().endswith(".pdf")]
    if not pdfs:
        raise HTTPException(status_code=400, detail="Please upload at least one PDF file.")

    temp_dir = tempfile.mkdtemp()
    pdf_paths = []
    for uf in pdfs:
        path = os.path.join(temp_dir, os.path.basename(uf.filename))
        with open(path, "wb") as f:
            f.write(uf.file.read())
        pdf_paths.append(path)

    all_docs = load_multiple_pdfs(pdf_paths)
    if not all_docs:
        raise HTTPException(status_code=422, detail="No readable text was found in the uploaded PDFs.")
    chunks = split_documents(all_docs)

    shared = _get_shared()
    vectorstore = create_vectorstore(chunks, shared["embedding_model"])
    retriever = create_retriever(vectorstore, shared["router"])

    session_id = uuid.uuid4().hex
    session = {
        "files": [os.path.basename(uf.filename) for uf in pdfs],
        "total_pages": len(all_docs),
        "total_chunks": len(chunks),
        "vectorstore": vectorstore,
        "retriever": retriever,
        "messages": [],
        "pdfs": {},
        "last_used": time.time(),
    }
    with _sessions_lock:
        _sessions[session_id] = session

    return {"session_id": session_id, "stats": _stats(session)}


class ChatRequest(BaseModel):
    session_id: str
    query: str


@app.post("/api/chat")
def chat(req: ChatRequest):
    session = _get_session(req.session_id)
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    shared = _get_shared()
    router = shared["router"]
    retriever = session["retriever"]
    chat_history_list = session["messages"].copy()
    chat_history_str = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in chat_history_list[-4:])

    def get_docs():
        return retriever.invoke(query, chat_history=chat_history_str)

    def get_history_summary():
        if chat_history_list:
            history_str = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in chat_history_list[-6:])
            summarizer_prompt = load_history_summarizer_prompt()
            return router.complete(
                "history_summarization",
                [{"role": "user", "content": summarizer_prompt.format(chat_history=history_str)}],
            )
        return "None"

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_docs = executor.submit(get_docs)
        future_summary = executor.submit(get_history_summary)
        context_docs = future_docs.result()
        history_summary = future_summary.result()

    context = "\n".join(doc.page_content for doc in context_docs)
    sources = sorted(set(
        os.path.basename(doc.metadata.get("source_file", doc.metadata.get("source", "Unknown")))
        for doc in context_docs
    ))
    response = answer_question(router, shared["prompt"], query, context, history_summary=history_summary)

    if response.get("is_internet_search"):
        sources = ["Web Search"]
    elif response.get("is_conversational"):
        sources = []

    assistant_msg = {
        "role": "assistant",
        "content": response["answer"],
        "sources": sources,
        "is_internet_search": bool(response.get("is_internet_search")),
        "verification": {
            "hallucination_score": response.get("hallucination_score"),
            "reason": response.get("reason", ""),
        },
    }
    session["messages"].append({"role": "user", "content": query})
    session["messages"].append(assistant_msg)

    return {"message": assistant_msg, "stats": _stats(session)}


class SessionRequest(BaseModel):
    session_id: str


GENERATORS = {
    "notes": (generate_notes_content, build_notes_pdf),
    "quiz": (generate_quiz_content, build_quiz_pdf),
    "flashcards": (generate_flashcards_content, build_flashcards_pdf),
}

PDF_FILENAMES = {
    "notes": "study_notes.pdf",
    "quiz": "mcq_quiz.pdf",
    "flashcards": "flashcards.pdf",
}


@app.post("/api/generate/{kind}")
def generate(kind: str, req: SessionRequest):
    if kind not in GENERATORS:
        raise HTTPException(status_code=404, detail=f"Unknown generator '{kind}'.")
    session = _get_session(req.session_id)
    content_fn, build_fn = GENERATORS[kind]

    content_data = content_fn(_get_shared()["router"], session["retriever"])
    session["pdfs"][kind] = build_fn(content_data).getvalue()

    if kind == "notes":
        data = {
            "markdown": content_data["raw_text"],
            "sections": [{"title": t, "body": b} for t, b in _parse_sections(content_data["raw_text"])],
        }
    elif kind == "quiz":
        data = {"questions": _parse_quiz(content_data["raw_text"])}
    else:
        data = {"cards": content_data["cards"]}

    if kind != "notes" and not (data.get("questions") or data.get("cards")):
        logging.getLogger("mindfolio").warning(
            "Parsed no %s items from %s output:\n%s",
            kind, content_data.get("model_label"), content_data["raw_text"][:1500],
        )

    data["model_label"] = content_data.get("model_label")
    return {"kind": kind, "data": data}


@app.get("/api/download/{session_id}/{kind}")
def download(session_id: str, kind: str):
    session = _get_session(session_id)
    pdf = session["pdfs"].get(kind)
    if pdf is None:
        raise HTTPException(status_code=404, detail="Nothing generated yet.")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{PDF_FILENAMES[kind]}"'},
    )


@app.post("/api/session/{session_id}/clear-chat")
def clear_chat(session_id: str):
    session = _get_session(session_id)
    session["messages"] = []
    return {"stats": _stats(session)}


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str):
    with _sessions_lock:
        _sessions.pop(session_id, None)
    return {"status": "deleted"}

import os
import logging
import warnings
import tempfile

# Suppress noisy transformers lazy-module __path__ deprecation messages.
# These use Python's logging system, not warnings — so we silence the logger.
logging.getLogger("transformers").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", message=r".*Accessing `__path__`.*")

import streamlit as st
from dotenv import load_dotenv

from ingestion.loader import load_pdf, load_multiple_pdfs
from ingestion.splitter import split_documents
from ingestion.embeddings import load_embedding_model
from ingestion.vectordb import create_vectorstore

from retrieval.retriever import create_retriever

from llm.model import answer_question, load_model_router
from llm.prompt import load_prompt


from generation.notes_gen import generate_notes_content, build_notes_pdf
from generation.quiz_gen import generate_quiz_content, build_quiz_pdf
from generation.flashcards_gen import generate_flashcards_content, build_flashcards_pdf

load_dotenv()

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
 page_title="MindFolio",
 page_icon="",
 layout="wide",
 initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
 @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

 /* Global */
 .stApp {
  font-family: 'Inter', sans-serif;
 }

 /* Hero Header */
 .hero-header {
  background: transparent;
  padding: 2rem 2rem 1rem 2rem;
  margin-bottom: 1rem;
  text-align: center;
 }
 .hero-header h1 {
  color: #ECECEC;
  font-size: 2.2rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.5px;
 }
 .hero-header p {
  color: #9b9b9b;
  font-size: 1rem;
  margin: 0;
  font-weight: 400;
 }

 /* Stat Cards */
 .stat-card {
  background: #2F2F2F;
  border-radius: 12px;
  padding: 1.25rem;
  text-align: center;
  transition: opacity 0.2s ease;
 }
 .stat-card:hover {
  opacity: 0.9;
 }
 .stat-number {
  font-size: 1.8rem;
  font-weight: 600;
  color: #ECECEC;
  margin: 0;
 }
 .stat-label {
  color: #9b9b9b;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 0.3rem;
 }

 /* File Chips */
 .file-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #2F2F2F;
  border-radius: 8px;
  padding: 6px 14px;
  margin: 4px;
  font-size: 0.82rem;
  color: #ECECEC;
 }

 /* Chat Bubbles */
 .user-bubble {
  background: #2F2F2F;
  color: #ECECEC;
  padding: 0.75rem 1.25rem;
  border-radius: 1.5rem;
  margin: 0.5rem 0;
  max-width: 80%;
  margin-left: auto;
  font-size: 0.95rem;
  line-height: 1.6;
 }
 .assistant-bubble {
  background: transparent;
  color: #ECECEC;
  padding: 0.75rem 0;
  margin: 0.5rem 0;
  max-width: 100%;
  font-size: 0.95rem;
  line-height: 1.6;
 }

 /* Source Badge */
 .source-badge {
  display: inline-block;
  background: #2F2F2F;
  color: #9b9b9b;
  font-size: 0.72rem;
  padding: 3px 10px;
  border-radius: 6px;
  margin: 2px;
 }

 /* Processing indicator */
 .processing-box {
  background: transparent;
  border: 1px solid #383838;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  color: #9b9b9b;
  animation: pulse 2s infinite;
 }
 @keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
 }

 /* Generation success card */
 .gen-success {
  background: #2F2F2F;
  border-radius: 12px;
  padding: 1.25rem;
  text-align: center;
  color: #ECECEC;
  margin: 1rem 0;
 }
 .gen-success h3 {
  color: #ECECEC;
  font-weight: 500;
  margin: 0 0 0.5rem 0;
 }

 /* Tab styling */
 .gen-tab-header {
  background: transparent;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
  text-align: center;
 }
 .gen-tab-header h2 {
  color: #ECECEC;
  font-size: 1.3rem;
  font-weight: 500;
  margin: 0 0 0.3rem 0;
 }
 .gen-tab-header p {
  color: #9b9b9b;
  font-size: 0.85rem;
  margin: 0;
 }

 /* Hide default streamlit branding */
 #MainMenu {visibility: hidden;}
 footer {visibility: hidden;}
 header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Session State Initialization ─────────────────────────────────────────────
defaults = {
 "messages": [],
 "vectorstore": None,
 "retriever": None,
 "processed_files": [],
 "total_chunks": 0,
 "total_pages": 0,
 "embedding_model": None,
 "model_router": None,
 "prompt": None,
 "generated_notes_pdf": None,
 "generated_quiz_pdf": None,
 "generated_flashcards_pdf": None,
 "active_tab": "chat",
}
for key, val in defaults.items():
 if key not in st.session_state:
  st.session_state[key] = val

# ── Hero Header ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-header">
 <h1>MindFolio</h1>
 <p>Upload multiple PDFs — Chat, generate Notes, Quizzes & Flashcards with AI</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
 st.markdown("## Document Upload")
 st.markdown("---")

 uploaded_files = st.file_uploader(
  "Drop your PDFs here",
  type=["pdf"],
  accept_multiple_files=True,
  help="Upload one or more PDF files to analyze",
  key="pdf_uploader",
 )

 if uploaded_files:
  st.markdown(f"**{len(uploaded_files)} file(s) selected:**")
  for f in uploaded_files:
   size_kb = f.size / 1024
   size_str = f"{size_kb / 1024:.1f} MB" if size_kb > 1024 else f"{size_kb:.0f} KB"
   st.markdown(
    f'<div class="file-chip"> {f.name} <span style="color:#6366f1">({size_str})</span></div>',
    unsafe_allow_html=True,
   )

 st.markdown("---")

 process_btn = st.button(
  " Process Documents",
  use_container_width=True,
  disabled=not uploaded_files,
  type="primary",
 )

 # ── Generation Buttons ──
 if st.session_state.processed_files:
  st.markdown("---")
  st.markdown("## AI Generation")

  gen_col1, gen_col2, gen_col3 = st.columns(3)
  with gen_col1:
   notes_btn = st.button("", use_container_width=True, help="Generate Notes")
   st.markdown("<p style='text-align:center;color:#9ca3af;font-size:0.7rem;margin-top:-10px;'>Notes</p>", unsafe_allow_html=True)
  with gen_col2:
   quiz_btn = st.button("", use_container_width=True, help="Generate MCQ Quiz")
   st.markdown("<p style='text-align:center;color:#9ca3af;font-size:0.7rem;margin-top:-10px;'>Quiz</p>", unsafe_allow_html=True)
  with gen_col3:
   flash_btn = st.button("", use_container_width=True, help="Generate Flashcards")
   st.markdown("<p style='text-align:center;color:#9ca3af;font-size:0.7rem;margin-top:-10px;'>Cards</p>", unsafe_allow_html=True)

 else:
  notes_btn = False
  quiz_btn = False
  flash_btn = False

 # ── Stats Section ──
 if st.session_state.processed_files:
  st.markdown("---")
  st.markdown("## Knowledge Base")
  col1, col2 = st.columns(2)
  with col1:
   st.markdown(
    f'<div class="stat-card"><div class="stat-number">{len(st.session_state.processed_files)}</div><div class="stat-label">Documents</div></div>',
    unsafe_allow_html=True,
   )
  with col2:
   st.markdown(
    f'<div class="stat-card"><div class="stat-number">{st.session_state.total_pages}</div><div class="stat-label">Pages</div></div>',
    unsafe_allow_html=True,
   )
  st.markdown("")
  col3, col4 = st.columns(2)
  with col3:
   st.markdown(
    f'<div class="stat-card"><div class="stat-number">{st.session_state.total_chunks}</div><div class="stat-label">Chunks</div></div>',
    unsafe_allow_html=True,
   )
  with col4:
   st.markdown(
    f'<div class="stat-card"><div class="stat-number">{len(st.session_state.messages) // 2}</div><div class="stat-label">Queries</div></div>',
    unsafe_allow_html=True,
   )

  st.markdown("---")
  st.markdown("### Loaded Files")
  for fname in st.session_state.processed_files:
   st.markdown(
    f'<div class="file-chip"> {fname}</div>',
    unsafe_allow_html=True,
   )

 # ── Downloads Section ──
 has_downloads = any([
  st.session_state.generated_notes_pdf,
  st.session_state.generated_quiz_pdf,
  st.session_state.generated_flashcards_pdf,
 ])
 if has_downloads:
  st.markdown("---")
  st.markdown("## Downloads")
  if st.session_state.generated_notes_pdf:
   st.download_button(
    " Download Notes PDF",
    data=st.session_state.generated_notes_pdf,
    file_name="study_notes.pdf",
    mime="application/pdf",
    use_container_width=True,
   )
  if st.session_state.generated_quiz_pdf:
   st.download_button(
    " Download MCQ Quiz PDF",
    data=st.session_state.generated_quiz_pdf,
    file_name="mcq_quiz.pdf",
    mime="application/pdf",
    use_container_width=True,
   )
  if st.session_state.generated_flashcards_pdf:
   st.download_button(
    " Download Flashcards PDF",
    data=st.session_state.generated_flashcards_pdf,
    file_name="flashcards.pdf",
    mime="application/pdf",
    use_container_width=True,
   )

 st.markdown("---")
 reset_col1, reset_col2 = st.columns(2)
 with reset_col1:
  if st.button(" Clear Chat", use_container_width=True):
   st.session_state.messages = []
   st.session_state.active_tab = "chat"
   st.rerun()
 with reset_col2:
  if st.button(" Reset All", use_container_width=True):
   for key in list(st.session_state.keys()):
    del st.session_state[key]
   st.rerun()


# ── Process Documents ────────────────────────────────────────────────────────
if process_btn and uploaded_files:
 with st.spinner(""):
  st.markdown(
   '<div class="processing-box"> Processing your documents... This may take a moment.</div>',
   unsafe_allow_html=True,
  )

  progress = st.progress(0, text="Initializing...")

  # Step 1: Save uploaded files to temp directory
  progress.progress(10, text=" Saving uploaded files...")
  temp_dir = tempfile.mkdtemp()
  pdf_paths = []
  for uf in uploaded_files:
   path = os.path.join(temp_dir, uf.name)
   with open(path, "wb") as f:
    f.write(uf.getbuffer())
   pdf_paths.append(path)

  # Step 2: Load PDFs
  progress.progress(25, text=" Reading PDFs...")
  all_docs = load_multiple_pdfs(pdf_paths)
  total_pages = len(all_docs)

  # Step 3: Split into chunks
  progress.progress(45, text=" Splitting into chunks...")
  chunks = split_documents(all_docs)

  # Step 4: Load embedding model (cache it)
  progress.progress(60, text=" Loading embedding model...")
  if st.session_state.embedding_model is None:
   st.session_state.embedding_model = load_embedding_model()

  # Step 5: Create vector store
  progress.progress(75, text=" Building vector store...")
  st.session_state.vectorstore = create_vectorstore(
   chunks, st.session_state.embedding_model
  )

  # Step 6: Load routed model clients (cache them)
  progress.progress(85, text=" Loading AI router...")
  if st.session_state.model_router is None:
   st.session_state.model_router = load_model_router()
  if st.session_state.prompt is None:
   st.session_state.prompt = load_prompt()

  # Step 7: Create retriever
  progress.progress(92, text=" Setting up retriever...")
  st.session_state.retriever = create_retriever(
   st.session_state.vectorstore,
   st.session_state.model_router
  )

  # Done
  progress.progress(100, text=" Ready!")
  st.session_state.processed_files = [uf.name for uf in uploaded_files]
  st.session_state.total_chunks = len(chunks)
  st.session_state.total_pages = total_pages
  st.session_state.messages = []
  # Clear previous generations
  st.session_state.generated_notes_pdf = None
  st.session_state.generated_quiz_pdf = None
  st.session_state.generated_flashcards_pdf = None
  st.session_state.active_tab = "chat"

  st.rerun()


# ── Handle Generation Buttons ────────────────────────────────────────────────
def _run_generation(gen_type, content_fn, build_fn, session_key):
 """Shared generation logic for notes/report/flashcards."""
 st.session_state.active_tab = gen_type

 with st.spinner(""):
  # Generation progress
  progress = st.progress(0, text=f"Starting {gen_type} generation...")

  # Step 1: Generate content via LLM
  progress.progress(20, text=f" AI is analyzing your documents for {gen_type}...")
  content_data = content_fn(
   st.session_state.model_router,
   st.session_state.retriever
  )

  # Step 2: Build PDF
  progress.progress(80, text=f" Building {gen_type} PDF...")
  pdf_buffer = build_fn(content_data)

  # Step 3: Store result
  progress.progress(100, text=" Done!")
  st.session_state[session_key] = pdf_buffer.getvalue()

 return content_data


if notes_btn:
 content = _run_generation(
  "notes",
  generate_notes_content,
  build_notes_pdf,
  "generated_notes_pdf",
 )
 st.rerun()

if quiz_btn:
 content = _run_generation(
  "quiz",
  generate_quiz_content,
  build_quiz_pdf,
  "generated_quiz_pdf",
 )
 st.rerun()

if flash_btn:
 content = _run_generation(
  "flashcards",
  generate_flashcards_content,
  build_flashcards_pdf,
  "generated_flashcards_pdf",
 )
 st.rerun()


# ── Main Content Area ────────────────────────────────────────────────────────

if not st.session_state.processed_files:
 # ── Empty State ──
 st.markdown("")
 col_empty = st.columns([1, 3, 1])[1]
 with col_empty:
  st.markdown(
   """
   <div style="text-align: center; padding: 3rem 0; color: #6b7280;">
    <h3 style="color: #c4b5fd; font-weight: 600; font-size: 1.8rem; margin-bottom: 1rem;">Welcome to MindFolio</h3>
    <p style="color: #9ca3af; font-size: 1.1rem; max-width: 80%; margin: 0 auto; line-height: 1.6;">
     Upload your PDF documents in the sidebar on the left to start analyzing, chatting, and generating study materials.
    </p>
   </div>
   """,
   unsafe_allow_html=True,
  )
  st.markdown(
   """
   <div style="margin-top: 2rem; padding: 1.5rem; border: 1px dashed #374151; border-radius: 12px; text-align: center;">
    <p style="color: #9ca3af; font-size: 0.85rem; margin: 0;">
      <strong>Features available after processing:</strong><br><br>
      Chat with your documents&nbsp;&nbsp;•&nbsp;&nbsp;
      Generate study notes<br>
      Generate MCQ quizzes&nbsp;&nbsp;•&nbsp;&nbsp;
      Generate flashcards for revision
    </p>
   </div>
   """,
   unsafe_allow_html=True,
  )

else:
 # ── Tab Navigation ──
 tab_chat, tab_notes, tab_quiz, tab_flashcards = st.tabs([
  " Chat", " Notes", " MCQ Quiz", " Flashcards"
 ])

 # ════════════════════════════════════════════════════════════════
 # TAB: Chat
 # ════════════════════════════════════════════════════════════════
 with tab_chat:
  # Display chat messages
  for msg in st.session_state.messages:
   if msg["role"] == "user":
    st.markdown(
     f'<div class="user-bubble"> {msg["content"]}</div>',
     unsafe_allow_html=True,
    )
   else:
    st.markdown(
     f'<div class="assistant-bubble"> {msg["content"]}</div>',
     unsafe_allow_html=True,
    )
    if "sources" in msg and msg["sources"]:
     sources_html = " ".join(
      [f'<span class="source-badge"> {s}</span>' for s in msg["sources"]]
     )
     st.markdown(
      f'<div style="margin-left: 0.5rem; margin-bottom: 0.5rem;">Sources: {sources_html}</div>',
      unsafe_allow_html=True,
     )

  # Chat input
  if query := st.chat_input("Ask a question about your documents..."):
   st.session_state.messages.append({"role": "user", "content": query})
   st.markdown(
    f'<div class="user-bubble"> {query}</div>',
    unsafe_allow_html=True,
   )

   with st.spinner("🔎 Searching across your documents..."):
    context_docs = st.session_state.retriever.invoke(query)
    context = "\n".join([doc.page_content for doc in context_docs])
    sources = list(set(
     os.path.basename(doc.metadata.get("source_file", doc.metadata.get("source", "Unknown")))
     for doc in context_docs
    ))
    response = answer_question(
     st.session_state.model_router,
     st.session_state.prompt,
     query,
     context,
    )
    st.session_state.messages.append(
     {
      "role": "assistant",
      "content": response["answer"],
      "sources": sources,
      "verification": {
       "hallucination_score": response.get("hallucination_score"),
       "reason": response.get("reason", ""),
      },
     }
    )

   st.rerun()

 # ════════════════════════════════════════════════════════════════
 # TAB: Notes
 # ════════════════════════════════════════════════════════════════
 with tab_notes:
  st.markdown("""
  <div class="gen-tab-header">
   <h2> AI Study Notes</h2>
   <p>Automatically extract and organize key concepts, definitions, and summaries from your PDFs</p>
  </div>
  """, unsafe_allow_html=True)

  if st.session_state.generated_notes_pdf:
   st.markdown("""
   <div class="gen-success">
    <h3> Notes Generated Successfully!</h3>
    <p>Your study notes PDF is ready. Download it from the sidebar.</p>
   </div>
   """, unsafe_allow_html=True)

   st.download_button(
    " Download Study Notes PDF",
    data=st.session_state.generated_notes_pdf,
    file_name="study_notes.pdf",
    mime="application/pdf",
    use_container_width=True,
    type="primary",
   )
  else:
   st.markdown("")
   col_n = st.columns([1, 2, 1])[1]
   with col_n:
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #6b7280; border: 1px dashed #374151; border-radius: 12px;">
     <div style="font-size: 3rem; margin-bottom: 0.5rem;"></div>
     <p style="color: #9ca3af; margin-bottom: 1.5rem;">Generate AI study notes from your documents.</p>
    """, unsafe_allow_html=True)
    
    if st.button(" Generate Study Notes", use_container_width=True, type="primary", key="main_notes_btn"):
     _run_generation(
      "notes",
      generate_notes_content,
      build_notes_pdf,
      "generated_notes_pdf",
     )
     st.rerun()
     
    st.markdown("""
     <p style="color: #6b7280; font-size: 0.82rem; margin-top: 1rem;">
      Includes: Key concepts • Definitions • Summary points • Important formulas
     </p>
    </div>
    """, unsafe_allow_html=True)

 # ════════════════════════════════════════════════════════════════
 # TAB: Quiz
 # ════════════════════════════════════════════════════════════════
 with tab_quiz:
  st.markdown("""
  <div class="gen-tab-header">
   <h2> MCQ Practice Quiz</h2>
   <p>Generate a structured multiple-choice quiz to test your knowledge</p>
  </div>
  """, unsafe_allow_html=True)

  if st.session_state.generated_quiz_pdf:
   st.markdown("""
   <div class="gen-success">
    <h3> Quiz Generated Successfully!</h3>
    <p>Your practice quiz PDF is ready. Download it from the sidebar.</p>
   </div>
   """, unsafe_allow_html=True)

   st.download_button(
    " Download MCQ Quiz PDF",
    data=st.session_state.generated_quiz_pdf,
    file_name="mcq_quiz.pdf",
    mime="application/pdf",
    use_container_width=True,
    type="primary",
   )
  else:
   st.markdown("")
   col_r = st.columns([1, 2, 1])[1]
   with col_r:
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #6b7280; border: 1px dashed #374151; border-radius: 12px;">
     <div style="font-size: 3rem; margin-bottom: 0.5rem;"></div>
     <p style="color: #9ca3af; margin-bottom: 1.5rem;">Generate an interactive MCQ practice quiz from your documents.</p>
    """, unsafe_allow_html=True)
    
    if st.button(" Generate Practice Quiz", use_container_width=True, type="primary", key="main_quiz_btn"):
     _run_generation(
      "quiz",
      generate_quiz_content,
      build_quiz_pdf,
      "generated_quiz_pdf",
     )
     st.rerun()
     
    st.markdown("""
     <p style="color: #6b7280; font-size: 0.82rem; margin-top: 1rem;">
      Includes: 15-25 Questions • 4 Options per Question • Detailed Answer Key
     </p>
    </div>
    """, unsafe_allow_html=True)

 # ════════════════════════════════════════════════════════════════
 # TAB: Flashcards
 # ════════════════════════════════════════════════════════════════
 with tab_flashcards:
  st.markdown("""
  <div class="gen-tab-header">
   <h2> Study Flashcards</h2>
   <p>Generate question-answer flashcards for effective revision and self-testing</p>
  </div>
  """, unsafe_allow_html=True)

  if st.session_state.generated_flashcards_pdf:
   st.markdown("""
   <div class="gen-success">
    <h3> Flashcards Generated Successfully!</h3>
    <p>Your flashcards PDF is ready. Download it from the sidebar.</p>
   </div>
   """, unsafe_allow_html=True)

   st.download_button(
    " Download Flashcards PDF",
    data=st.session_state.generated_flashcards_pdf,
    file_name="flashcards.pdf",
    mime="application/pdf",
    use_container_width=True,
    type="primary",
   )
  else:
   st.markdown("")
   col_f = st.columns([1, 2, 1])[1]
   with col_f:
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #6b7280; border: 1px dashed #374151; border-radius: 12px;">
     <div style="font-size: 3rem; margin-bottom: 0.5rem;"></div>
     <p style="color: #9ca3af; margin-bottom: 1.5rem;">Generate interactive study flashcards from your documents.</p>
    """, unsafe_allow_html=True)
    
    if st.button(" Generate Flashcards", use_container_width=True, type="primary", key="main_flash_btn"):
     _run_generation(
      "flashcards",
      generate_flashcards_content,
      build_flashcards_pdf,
      "generated_flashcards_pdf",
     )
     st.rerun()
     
    st.markdown("""
     <p style="color: #6b7280; font-size: 0.82rem; margin-top: 1rem;">
      Includes: 8-15 Q&A cards • Factual recall • Conceptual understanding • Color-coded
     </p>
    </div>
    """, unsafe_allow_html=True)

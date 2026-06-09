"""
main.py — Quick CLI test script for the RAG pipeline.

Usage:
    1. Place a PDF file path below.
    2. Run: python main.py
    3. It will load, embed, and answer a sample query.
"""

from dotenv import load_dotenv

from ingestion.loader import load_pdf
from ingestion.splitter import split_documents
from ingestion.embeddings import load_embedding_model
from ingestion.vectordb import create_vectorstore

from retrieval.retriever import create_retriever

from llm.model import answer_question, load_model_router
from llm.prompt import load_prompt


load_dotenv()

# ── Step 1: Load and split the PDF ──
pdf_path = "your_file.pdf"  # <-- Replace with your PDF path
docs = load_pdf(pdf_path)
chunks = split_documents(docs)

# ── Step 2: Build the vector store ──
embedding_model = load_embedding_model()
vectorstore = create_vectorstore(chunks, embedding_model)

# ── Step 3: Set up the AI router and retriever ──
router = load_model_router()
prompt = load_prompt()
retriever = create_retriever(vectorstore, router)

# ── Step 4: Ask a question ──
query = "What is this document about?"

context_docs = retriever.invoke(query)
context = "\n".join([doc.page_content for doc in context_docs])

result = answer_question(router, prompt, query, context)

print("\nANSWER:\n")
print(result["answer"])
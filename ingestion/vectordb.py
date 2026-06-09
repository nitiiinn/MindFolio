"""
vectordb.py — Creates and manages the ChromaDB vector store.

ChromaDB stores our document chunks as vectors. We run it in-memory
so it works flawlessly on cloud hosting like Streamlit Community Cloud
without throwing 'readonly database' errors.
"""

from langchain_community.vectorstores import Chroma


def create_vectorstore(chunks, embedding_model):
    """Create a fresh in-memory ChromaDB vector store from document chunks.

    Since we re-create the database every time a user uploads new PDFs,
    we don't need to persist it to disk. Running in memory is faster
    and prevents file lock issues.
    """
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        # Omitting persist_directory forces Chroma to run entirely in RAM
    )

    return vectorstore
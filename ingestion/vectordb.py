"""
vectordb.py — Creates and manages the ChromaDB vector store.

ChromaDB stores our document chunks as vectors. We run it in-memory
so it works flawlessly on cloud hosting like Streamlit Community Cloud
without throwing 'readonly database' errors.
"""

import uuid
from langchain_community.vectorstores import Chroma


def create_vectorstore(chunks, embedding_model):
    """Create a fresh in-memory ChromaDB vector store from document chunks.

    We generate a unique collection name for each upload. This ensures that
    if a user uploads new files (or if multiple users use the app simultaneously),
    their documents never mix in the in-memory database.
    """
    collection_name = f"docs_{uuid.uuid4().hex}"
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        collection_name=collection_name,
        # Omitting persist_directory forces Chroma to run entirely in RAM
    )

    return vectorstore
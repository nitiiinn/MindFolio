"""
vectordb.py — Creates and manages the ChromaDB vector store.

ChromaDB stores our document chunks as vectors on disk (in ./chroma_db/).
When a user asks a question, we search this database to find the most
relevant chunks using cosine similarity.
"""

import os
import shutil
from langchain_community.vectorstores import Chroma


def create_vectorstore(chunks, embedding_model):
    """Create a fresh ChromaDB vector store from document chunks.

    We delete the old database each time because different PDFs
    should not mix their embeddings (it would confuse the search).
    """
    persist_dir = "./chroma_db"

    # Delete old database to start fresh with new documents
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=persist_dir,
    )

    return vectorstore
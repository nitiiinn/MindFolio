"""
embeddings.py — Converts text into numerical vectors using Mistral's API.

These vectors are stored in ChromaDB and used to find the most relevant
chunks when a user asks a question (semantic search).
"""

import math
import os
from typing import Iterable
from langchain_core.embeddings import Embeddings
from mistralai.client import Mistral


class MistralEmbeddings(Embeddings):
    """Calls the Mistral API to convert text into embedding vectors.

    Why Mistral API instead of a local model?
    - No need to install heavy packages (torch, sentence-transformers).
    - Much smaller deployment size (~300MB vs ~4GB).
    - Works great on free hosting like Streamlit Cloud.
    - PAISE NAHI HAI MUJHPE YEH SAB KHARIDNE KE LIYE 😅
    """

    def __init__(self, model_name: str = "mistral-embed", batch_size: int = 64):
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "Missing MISTRAL_API_KEY. Add it to your .env file."
            )
        self.client = Mistral(api_key=api_key)
        self.model_name = model_name
        self.batch_size = batch_size  # Max texts to embed in one API call

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of document chunks (used when uploading PDFs)."""
        import concurrent.futures
        
        batches = list(_batched(texts, self.batch_size))
        vectors = []
        
        # Use concurrent processing, preserving order with executor.map
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(self._embed_batch, batches)
            for batch_vectors in results:
                vectors.extend(batch_vectors)
                
        return vectors

    def embed_query(self, text: str) -> list[float]:
        """Embed a single user query (used when searching)."""
        return self._embed_batch([text])[0]

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Send a batch of texts to the Mistral API and get vectors back."""
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.model_name,
                    inputs=texts,
                )
                return [
                    _normalize_vector(item.embedding)
                    for item in response.data
                    if item.embedding is not None
                ]
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                print(f"Embedding API error: {e}. Retrying in {2 ** attempt} seconds...")
                time.sleep(2 ** attempt)


def load_embedding_model():
    """Factory function — creates and returns a MistralEmbeddings instance."""
    model_name = os.getenv("MISTRAL_EMBEDDING_MODEL", "mistral-embed")
    return MistralEmbeddings(model_name=model_name)


def _batched(items: list[str], batch_size: int) -> Iterable[list[str]]:
    """Split a list into smaller chunks of `batch_size`."""
    for index in range(0, len(items), batch_size):
        yield items[index:index + batch_size]


def _normalize_vector(vector: list[float]) -> list[float]:
    """Scale a vector to unit length (length = 1.0).

    This ensures cosine similarity works correctly when comparing vectors.
    """
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        return vector
    return [v / norm for v in vector]

import math
import os
from typing import Iterable
from langchain_core.embeddings import Embeddings
from mistralai.client import Mistral


class MistralEmbeddings(Embeddings):
    """LangChain-compatible embeddings adapter that avoids local torch loading."""

    def __init__(self, model_name: str = "mistral-embed", batch_size: int = 64):
        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "Missing MISTRAL_API_KEY. Add it to your environment or .env file."
            )

        self.client = Mistral(api_key=api_key)
        self.model_name = model_name
        self.batch_size = batch_size

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for batch in _batched(texts, self.batch_size):
            vectors.extend(self._embed_batch(batch))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text])[0]

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.model_name,
            inputs=texts,
        )
        return [
            _normalize_vector(item.embedding)
            for item in response.data
            if item.embedding is not None
        ]


def load_embedding_model():
    """Loads an API-backed embedding model without importing HuggingFace/torch."""
    model_name = os.getenv("MISTRAL_EMBEDDING_MODEL", "mistral-embed")
    return MistralEmbeddings(model_name=model_name)


def _batched(items: list[str], batch_size: int) -> Iterable[list[str]]:
    for index in range(0, len(items), batch_size):
        yield items[index:index + batch_size]


def _normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]

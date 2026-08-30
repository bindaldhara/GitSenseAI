"""LangChain Embeddings adapter for the FastEmbed ONNX model."""

from __future__ import annotations

from langchain_core.embeddings import Embeddings

from vector_store.embeddings import embed_texts


class SentenceTransformerEmbeddings(Embeddings):
    """Wrap the local ONNX embedding model for LangChain retrievers and vector stores."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return embed_texts(texts)

    def embed_query(self, text: str) -> list[float]:
        return embed_texts([text])[0]

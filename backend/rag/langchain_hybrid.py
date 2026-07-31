"""LangChain hybrid retrieval — BM25Retriever + vector retriever fused with EnsembleRetriever."""

from __future__ import annotations

import logging
from typing import Literal

from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from config import settings
from rag.bm25_store import bm25_index_exists, load_chunk_documents
from rag.chunk_identity import chunk_identity
from vector_store.embeddings import embed_texts
from vector_store.qdrant_store import COLLECTION_NAME, RetrievedChunk, search_repository_chunks

logger = logging.getLogger(__name__)

RetrievalMode = Literal["hybrid", "vector"]

def retrieved_chunk_to_document(chunk: RetrievedChunk) -> Document:
    return Document(
        page_content=chunk.text,
        metadata={
            "chunk_id": chunk_identity(
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                symbol_name=chunk.symbol_name,
            ),
            "file_path": chunk.file_path,
            "language": chunk.language,
            "chunk_kind": chunk.chunk_kind,
            "symbol_name": chunk.symbol_name,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "score": chunk.score,
        },
    )


def document_to_retrieved_chunk(document: Document, *, rank_score: float) -> RetrievedChunk:
    metadata = document.metadata
    symbol_name = metadata.get("symbol_name")
    return RetrievedChunk(
        file_path=str(metadata.get("file_path", "")),
        language=str(metadata.get("language", "")),
        chunk_kind=str(metadata.get("chunk_kind", "")),
        symbol_name=symbol_name if symbol_name else None,
        start_line=int(metadata.get("start_line", 0)),
        end_line=int(metadata.get("end_line", 0)),
        text=document.page_content,
        score=float(metadata.get("score", rank_score)),
    )


class RepositoryVectorRetriever(BaseRetriever):
    """LangChain retriever backed by the existing Qdrant similarity search."""

    repository_id: int = Field(description="Repository whose vectors to search.")
    k: int = Field(default=5, description="Number of chunks to return.")

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        query_vector = embed_texts([query])[0]
        chunks = search_repository_chunks(
            self.repository_id,
            query_vector,
            top_k=self.k,
        )
        return [retrieved_chunk_to_document(chunk) for chunk in chunks]


def _build_bm25_retriever(repository_id: int, *, k: int) -> BM25Retriever | None:
    documents = load_chunk_documents(repository_id)
    if not documents:
        return None

    retriever = BM25Retriever.from_documents(documents)
    retriever.k = k
    return retriever


def retrieve_repository_context(
    repository_id: int,
    question: str,
    *,
    top_k: int = 5,
    use_hybrid: bool | None = None,
) -> tuple[list[RetrievedChunk], RetrievalMode]:
    """Retrieve chunks using LangChain EnsembleRetriever (BM25 + vector) or vector-only."""
    hybrid_enabled = settings.hybrid_search_enabled if use_hybrid is None else use_hybrid
    candidate_k = max(top_k * settings.hybrid_candidate_multiplier, top_k)

    vector_retriever = RepositoryVectorRetriever(repository_id=repository_id, k=candidate_k)

    if not hybrid_enabled:
        documents = vector_retriever.invoke(question)[:top_k]
        return [_document_with_rank_score(doc, rank) for rank, doc in enumerate(documents, start=1)], "vector"

    if not bm25_index_exists(repository_id):
        logger.info(
            "BM25 index missing for repository_id=%s — falling back to vector-only retrieval.",
            repository_id,
        )
        documents = vector_retriever.invoke(question)[:top_k]
        return [_document_with_rank_score(doc, rank) for rank, doc in enumerate(documents, start=1)], "vector"

    bm25_retriever = _build_bm25_retriever(repository_id, k=candidate_k)
    if bm25_retriever is None:
        documents = vector_retriever.invoke(question)[:top_k]
        return [_document_with_rank_score(doc, rank) for rank, doc in enumerate(documents, start=1)], "vector"

    ensemble = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        c=settings.hybrid_rrf_k,
        id_key="chunk_id",
    )
    fused_documents = ensemble.invoke(question)[:top_k]
    chunks = [_document_with_rank_score(doc, rank) for rank, doc in enumerate(fused_documents, start=1)]

    logger.info(
        "LangChain hybrid retrieval for repository_id=%s returned %s chunks (collection=%s).",
        repository_id,
        len(chunks),
        COLLECTION_NAME,
    )
    return chunks, "hybrid"


def _document_with_rank_score(document: Document, rank: int) -> RetrievedChunk:
    # EnsembleRetriever does not expose fused scores; preserve vector/BM25 score when present.
    rank_score = 1.0 / rank
    return document_to_retrieved_chunk(document, rank_score=rank_score)

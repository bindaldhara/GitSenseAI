"""Persist repository chunk documents for LangChain BM25Retriever.

BM25 keyword indexes are built at query time by LangChain's ``BM25Retriever``
from the JSON document corpus saved during ingest. This module only handles
storage and loading — no custom BM25 scoring logic.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from langchain_core.documents import Document

from config import settings
from rag.chunk_identity import chunk_identity
from vector_store.chunker import Chunk

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Bm25ChunkRecord:
    file_path: str
    language: str
    chunk_kind: str
    symbol_name: str | None
    start_line: int
    end_line: int
    text: str


def _index_path(repository_id: int) -> Path:
    return settings.bm25_index_path / f"{repository_id}.json"


def _record_to_document(record: Bm25ChunkRecord) -> Document:
    return Document(
        page_content=record.text,
        metadata={
            "chunk_id": chunk_identity(
                file_path=record.file_path,
                start_line=record.start_line,
                end_line=record.end_line,
                symbol_name=record.symbol_name,
            ),
            "file_path": record.file_path,
            "language": record.language,
            "chunk_kind": record.chunk_kind,
            "symbol_name": record.symbol_name,
            "start_line": record.start_line,
            "end_line": record.end_line,
        },
    )


def build_bm25_index(repository_id: int, chunks: list[Chunk]) -> int:
    """Persist chunk documents for LangChain BM25 retrieval. Returns record count."""
    if not chunks:
        delete_bm25_index(repository_id)
        return 0

    records = [
        Bm25ChunkRecord(
            file_path=chunk.file_path,
            language=chunk.language,
            chunk_kind=chunk.kind,
            symbol_name=chunk.symbol_name,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            text=chunk.text,
        )
        for chunk in chunks
    ]

    settings.bm25_index_path.mkdir(parents=True, exist_ok=True)
    payload = {
        "repository_id": repository_id,
        "records": [asdict(record) for record in records],
    }
    _index_path(repository_id).write_text(json.dumps(payload), encoding="utf-8")
    logger.info("Saved BM25 document corpus for repository_id=%s with %s chunks.", repository_id, len(records))
    return len(records)


def load_chunk_documents(repository_id: int) -> list[Document]:
    """Load persisted chunk documents for LangChain BM25Retriever."""
    path = _index_path(repository_id)
    if not path.is_file():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = [Bm25ChunkRecord(**item) for item in payload.get("records", [])]
        return [_record_to_document(record) for record in records]
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        logger.warning("Failed to load BM25 documents for repository_id=%s.", repository_id, exc_info=True)
        return []


def delete_bm25_index(repository_id: int) -> bool:
    """Delete the on-disk BM25 document corpus for a repository."""
    if repository_id < 0:
        return False
    path = _index_path(repository_id)
    if not path.exists():
        return False
    path.unlink()
    logger.info("Deleted BM25 document corpus for repository_id=%s.", repository_id)
    return True


def bm25_index_exists(repository_id: int) -> bool:
    return _index_path(repository_id).is_file()


def count_bm25_chunks(repository_id: int) -> int:
    path = _index_path(repository_id)
    if not path.is_file():
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return len(payload.get("records", []))
    except (json.JSONDecodeError, OSError):
        return 0

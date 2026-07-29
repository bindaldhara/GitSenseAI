"""Hybrid chunking — symbol-based chunks with fixed-size fallback.

Strategy
--------
1. **Symbol-based** (preferred): For each parsed file, read the source and
   create one chunk per symbol (function, class, method, type).  Each chunk
   contains the symbol body plus a small header with file path and language
   for context.  Import-only symbols are skipped (too short / low signal).

2. **Fixed-size fallback**: Files that were parsed but had zero non-import
   symbols (e.g. config files, READMEs with supported extensions, init
   files) are split into overlapping windows of ``WINDOW_LINES`` lines with
   ``OVERLAP_LINES`` overlap so they are still indexed.

Why this file exists
--------------------
Chunking is decoupled from embedding so we can unit-test and tune chunk
strategy independently of the embedding model and Qdrant store.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from db import db_cursor

logger = logging.getLogger(__name__)

WINDOW_LINES = 60
OVERLAP_LINES = 10
MAX_CHUNK_CHARS = 4000  # hard limit — truncate if a single symbol is huge


@dataclass(frozen=True)
class Chunk:
    """A single text chunk ready for embedding."""

    repository_id: int
    file_path: str
    language: str
    kind: str  # "symbol" | "window"
    symbol_name: str | None  # set for symbol chunks
    start_line: int
    end_line: int
    text: str


@dataclass
class ChunkResult:
    """Aggregate stats returned after chunking a repository."""

    chunks: list[Chunk] = field(default_factory=list)
    symbol_chunk_count: int = 0
    window_chunk_count: int = 0
    files_chunked: int = 0


def chunk_repository(repository_id: int, clone_path: str | Path) -> ChunkResult:
    """Produce chunks for every parsed file of *repository_id*.

    Reads ``repository_files`` and ``repository_symbols`` from Postgres
    (populated by Day 4 parsing) and the raw source from the clone on disk.

    Parameters
    ----------
    repository_id:
        FK into the ``repositories`` table.
    clone_path:
        Absolute path to the cloned repository on disk.

    Returns
    -------
    A ``ChunkResult`` with all chunks and summary counts.
    """
    root = Path(clone_path)
    result = ChunkResult()

    files_with_symbols = _load_files_and_symbols(repository_id)

    for file_path, symbols in files_with_symbols.items():
        abs_path = root / file_path
        if not abs_path.exists():
            logger.warning("Source file missing on disk, skipping: %s", abs_path)
            continue

        try:
            source_text = abs_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            logger.warning("Cannot read file, skipping: %s", abs_path, exc_info=True)
            continue

        lines = source_text.splitlines(keepends=True)
        language = symbols[0]["language"] if symbols else "unknown"

        # Filter to meaningful symbols (skip imports and __file__ sentinel).
        meaningful = [s for s in symbols if s["kind"] not in ("import", "__file__")]

        if meaningful:
            for sym in meaningful:
                chunk_text = _extract_symbol_text(
                    lines, sym, file_path=file_path, language=language,
                )
                result.chunks.append(
                    Chunk(
                        repository_id=repository_id,
                        file_path=file_path,
                        language=language,
                        kind="symbol",
                        symbol_name=sym["name"],
                        start_line=sym["start_line"],
                        end_line=sym["end_line"],
                        text=chunk_text,
                    )
                )
                result.symbol_chunk_count += 1
        else:
            # Fixed-size fallback for files without meaningful symbols.
            for start, end in _window_ranges(len(lines)):
                window_text = _build_window_text(
                    lines, start, end, file_path=file_path, language=language,
                )
                result.chunks.append(
                    Chunk(
                        repository_id=repository_id,
                        file_path=file_path,
                        language=language,
                        kind="window",
                        symbol_name=None,
                        start_line=start + 1,
                        end_line=end,
                        text=window_text,
                    )
                )
                result.window_chunk_count += 1

        result.files_chunked += 1

    logger.info(
        "Chunked repository_id=%s — files=%s symbol_chunks=%s window_chunks=%s total=%s",
        repository_id,
        result.files_chunked,
        result.symbol_chunk_count,
        result.window_chunk_count,
        len(result.chunks),
    )
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_files_and_symbols(repository_id: int) -> dict[str, list[dict]]:
    """Return {file_path: [symbol_dicts]} from Postgres for a repository.

    Files with no symbols still appear with an empty list so the fallback
    chunker can handle them.
    """
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT f.path, f.language
            FROM repository_files AS f
            WHERE f.repository_id = %s
            ORDER BY f.path
            """,
            (repository_id,),
        )
        files: dict[str, list[dict]] = {}
        file_languages: dict[str, str] = {}
        for row in cursor.fetchall():
            files[row["path"]] = []
            file_languages[row["path"]] = row["language"]

        cursor.execute(
            """
            SELECT
                s.name,
                s.kind,
                s.start_line,
                s.end_line,
                s.signature,
                s.parent_name,
                f.path AS file_path,
                f.language
            FROM repository_symbols AS s
            INNER JOIN repository_files AS f ON f.id = s.file_id
            WHERE s.repository_id = %s
            ORDER BY f.path, s.start_line
            """,
            (repository_id,),
        )
        for row in cursor.fetchall():
            fp = row["file_path"]
            if fp in files:
                files[fp].append(dict(row))

        # Ensure files without symbols still carry language info for fallback chunking.
        for fp in files:
            if not files[fp]:
                files[fp] = [{"kind": "__file__", "language": file_languages[fp]}]

    return files


def _extract_symbol_text(
    lines: list[str],
    symbol: dict,
    *,
    file_path: str,
    language: str,
) -> str:
    """Build the chunk text for a single symbol."""
    start = max(symbol["start_line"] - 1, 0)  # 1-indexed → 0-indexed
    end = min(symbol["end_line"], len(lines))
    body = "".join(lines[start:end]).rstrip()

    header = f"# File: {file_path} | Language: {language} | Symbol: {symbol['name']} ({symbol['kind']})\n\n"
    text = header + body
    if len(text) > MAX_CHUNK_CHARS:
        text = text[:MAX_CHUNK_CHARS] + "\n… [truncated]"
    return text


def _window_ranges(total_lines: int) -> list[tuple[int, int]]:
    """Return (start_0indexed, end_0indexed_exclusive) pairs for overlapping windows."""
    if total_lines == 0:
        return []
    ranges: list[tuple[int, int]] = []
    start = 0
    while start < total_lines:
        end = min(start + WINDOW_LINES, total_lines)
        ranges.append((start, end))
        if end >= total_lines:
            break
        start += WINDOW_LINES - OVERLAP_LINES
    return ranges


def _build_window_text(
    lines: list[str],
    start: int,
    end: int,
    *,
    file_path: str,
    language: str,
) -> str:
    """Build the chunk text for a fixed-size window."""
    body = "".join(lines[start:end]).rstrip()
    header = f"# File: {file_path} | Language: {language} | Lines {start + 1}–{end}\n\n"
    text = header + body
    if len(text) > MAX_CHUNK_CHARS:
        text = text[:MAX_CHUNK_CHARS] + "\n… [truncated]"
    return text

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import HTTPException, status

from db import db_cursor
from parsers.extract import extract_symbols
from parsers.languages import MAX_FILE_BYTES, SKIP_DIRECTORY_NAMES, detect_language
from parsers.models import ParsedFile, ParseResult, SkippedFile

logger = logging.getLogger(__name__)

DEFAULT_SKIPPED_LIMIT = 100


def parse_repository(repository_id: int, clone_path: str | Path) -> ParseResult:
    """Walk a cloned repository, extract symbols, and replace persisted parse data."""
    root = Path(clone_path)
    if not root.exists() or not root.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Clone path does not exist or is not a directory: {clone_path}",
        )

    parsed_files, skipped_files = _walk_repository(root)
    clear_parsed_data(repository_id)
    _persist_parsed_files(repository_id, parsed_files)
    _persist_skipped_files(repository_id, skipped_files)

    symbol_count = sum(len(item.symbols) for item in parsed_files)
    logger.info(
        "Parsed repository_id=%s files=%s symbols=%s skipped=%s path=%s",
        repository_id,
        len(parsed_files),
        symbol_count,
        len(skipped_files),
        root,
    )
    return ParseResult(
        files=parsed_files,
        skipped_files=skipped_files,
        file_count=len(parsed_files),
        symbol_count=symbol_count,
        skipped_count=len(skipped_files),
    )


def clear_parsed_data(repository_id: int) -> None:
    """Remove previously stored files/symbols/skipped rows for a repository."""
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "DELETE FROM repository_symbols WHERE repository_id = %s",
            (repository_id,),
        )
        cursor.execute(
            "DELETE FROM repository_files WHERE repository_id = %s",
            (repository_id,),
        )
        cursor.execute(
            "DELETE FROM repository_skipped_files WHERE repository_id = %s",
            (repository_id,),
        )


def get_repository_parse_summary(
    repository_id: int,
    *,
    skipped_limit: int = DEFAULT_SKIPPED_LIMIT,
) -> dict:
    """Return parse counts plus a capped skipped-file list for the dashboard/API."""
    _ensure_repository_exists(repository_id)

    with db_cursor() as cursor:
        file_count = _count_rows(cursor, "repository_files", repository_id)
        symbol_count = _count_rows(cursor, "repository_symbols", repository_id)
        skipped_count = _count_rows(cursor, "repository_skipped_files", repository_id)
        by_language = _group_count(cursor, "repository_files", "language", repository_id)
        by_kind = _group_count(cursor, "repository_symbols", "kind", repository_id)
        by_skip_reason = _group_count(
            cursor,
            "repository_skipped_files",
            "reason",
            repository_id,
        )

        cursor.execute(
            """
            SELECT path, reason
            FROM repository_skipped_files
            WHERE repository_id = %s
            ORDER BY path ASC
            LIMIT %s
            """,
            (repository_id, skipped_limit),
        )
        skipped_files = list(cursor.fetchall())

    return {
        "repository_id": repository_id,
        "file_count": file_count,
        "symbol_count": symbol_count,
        "skipped_count": skipped_count,
        "by_language": by_language,
        "by_kind": by_kind,
        "by_skip_reason": by_skip_reason,
        "skipped_files": skipped_files,
        "skipped_returned": len(skipped_files),
        "skipped_limit": skipped_limit,
    }


def get_repository_symbols(
    repository_id: int,
    *,
    limit: int = 1000,
    skipped_limit: int = DEFAULT_SKIPPED_LIMIT,
) -> dict:
    """Return a parse summary plus a capped list of symbols for verification."""
    summary = get_repository_parse_summary(
        repository_id,
        skipped_limit=skipped_limit,
    )

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                s.id,
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
            ORDER BY f.path ASC, s.start_line ASC, s.id ASC
            LIMIT %s
            """,
            (repository_id, limit),
        )
        symbols = list(cursor.fetchall())

    return {
        **summary,
        "symbols": symbols,
        "symbols_returned": len(symbols),
        "symbols_limit": limit,
    }


def _ensure_repository_exists(repository_id: int) -> None:
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT id FROM repositories WHERE id = %s",
            (repository_id,),
        )
        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository with id {repository_id} was not found.",
            )


def _count_rows(cursor, table: str, repository_id: int) -> int:
    allowed_tables = {
        "repository_files",
        "repository_symbols",
        "repository_skipped_files",
    }
    if table not in allowed_tables:
        raise ValueError(f"Unsupported table for count: {table}")
    cursor.execute(
        f"SELECT COUNT(*) AS count FROM {table} WHERE repository_id = %s",
        (repository_id,),
    )
    return int(cursor.fetchone()["count"])


def _group_count(cursor, table: str, column: str, repository_id: int) -> dict[str, int]:
    allowed = {
        ("repository_files", "language"),
        ("repository_symbols", "kind"),
        ("repository_skipped_files", "reason"),
    }
    if (table, column) not in allowed:
        raise ValueError(f"Unsupported group query: {table}.{column}")
    cursor.execute(
        f"""
        SELECT {column} AS key, COUNT(*) AS count
        FROM {table}
        WHERE repository_id = %s
        GROUP BY {column}
        ORDER BY {column}
        """,
        (repository_id,),
    )
    return {row["key"]: int(row["count"]) for row in cursor.fetchall()}


def _walk_repository(root: Path) -> tuple[list[ParsedFile], list[SkippedFile]]:
    parsed: list[ParsedFile] = []
    skipped: list[SkippedFile] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if _is_under_skipped_directory(path, root):
            continue

        relative_path = path.relative_to(root).as_posix()
        language = detect_language(path)
        if language is None:
            skipped.append(
                SkippedFile(path=relative_path, reason="unsupported_language")
            )
            continue

        try:
            size_bytes = path.stat().st_size
        except OSError:
            skipped.append(SkippedFile(path=relative_path, reason="stat_error"))
            continue

        if size_bytes > MAX_FILE_BYTES:
            skipped.append(SkippedFile(path=relative_path, reason="oversized"))
            continue

        try:
            source = path.read_bytes()
        except OSError:
            skipped.append(SkippedFile(path=relative_path, reason="read_error"))
            continue

        if b"\x00" in source:
            skipped.append(SkippedFile(path=relative_path, reason="binary"))
            continue

        try:
            text = source.decode("utf-8")
        except UnicodeDecodeError:
            skipped.append(SkippedFile(path=relative_path, reason="decode_error"))
            continue

        line_count = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        if text == "":
            line_count = 0

        try:
            symbols = extract_symbols(source, language)
        except Exception:
            logger.warning("Failed to parse %s; skipping file", relative_path, exc_info=True)
            skipped.append(SkippedFile(path=relative_path, reason="parse_error"))
            continue

        stored_language = "typescript" if language == "tsx" else language
        parsed.append(
            ParsedFile(
                path=relative_path,
                language=stored_language,
                size_bytes=size_bytes,
                line_count=line_count,
                symbols=symbols,
            )
        )

    parsed.sort(key=lambda item: item.path)
    skipped.sort(key=lambda item: item.path)
    return parsed, skipped


def _persist_parsed_files(repository_id: int, parsed_files: list[ParsedFile]) -> None:
    if not parsed_files:
        return

    with db_cursor(commit=True) as cursor:
        for parsed_file in parsed_files:
            cursor.execute(
                """
                INSERT INTO repository_files (
                    repository_id, path, language, size_bytes, line_count
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    repository_id,
                    parsed_file.path,
                    parsed_file.language,
                    parsed_file.size_bytes,
                    parsed_file.line_count,
                ),
            )
            file_row = cursor.fetchone()
            if file_row is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to persist parsed file metadata.",
                )
            file_id = file_row["id"]

            for symbol in parsed_file.symbols:
                cursor.execute(
                    """
                    INSERT INTO repository_symbols (
                        repository_id,
                        file_id,
                        name,
                        kind,
                        start_line,
                        end_line,
                        signature,
                        parent_name
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        repository_id,
                        file_id,
                        symbol.name,
                        symbol.kind,
                        symbol.start_line,
                        symbol.end_line,
                        symbol.signature,
                        symbol.parent_name,
                    ),
                )


def _persist_skipped_files(repository_id: int, skipped_files: list[SkippedFile]) -> None:
    if not skipped_files:
        return

    with db_cursor(commit=True) as cursor:
        for skipped in skipped_files:
            cursor.execute(
                """
                INSERT INTO repository_skipped_files (repository_id, path, reason)
                VALUES (%s, %s, %s)
                """,
                (repository_id, skipped.path, skipped.reason),
            )


def _is_under_skipped_directory(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    return any(part in SKIP_DIRECTORY_NAMES for part in relative.parts[:-1])

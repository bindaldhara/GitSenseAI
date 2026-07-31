"""Shared chunk identity helpers for retrieval and deduplication."""


def chunk_identity(
    *,
    file_path: str,
    start_line: int,
    end_line: int,
    symbol_name: str | None,
) -> str:
    symbol = symbol_name or ""
    return f"{file_path}:{start_line}:{end_line}:{symbol}"

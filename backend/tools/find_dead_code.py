"""MCP tool for finding likely-unused symbols in a cloned repository.

This is intentionally a conservative static check. A symbol with no source
references can still be used through reflection, configuration, or a public
API, so results are candidates for review rather than safe-to-delete commands.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from fastapi import HTTPException

from parsers.extract import extract_symbols
from parsers.languages import MAX_FILE_BYTES, SKIP_DIRECTORY_NAMES, detect_language
from services.repository_service import get_repository_by_full_name, resolve_repository_clone_path
from tools.errors import ToolError
from tools.preflight import require_mcp_infrastructure

_IDENTIFIER = re.compile(r"\b[A-Za-z_$][A-Za-z0-9_$]*\b")
_ANALYZABLE_KINDS = {"function", "class", "type"}
_ENTRY_POINT_NAMES = frozenset({"main", "init", "Main", "App", "index", "default"})


def find_dead_code(
    repo_name: str,
    *,
    user_id: int | None = None,
    max_results: int = 100,
) -> dict:
    """Return likely-unused non-method symbols from an indexed repository.

    A candidate is a function, class, or type whose name only occurs at its
    declaration in supported source files. Methods are excluded because they
    are commonly invoked dynamically by frameworks or interfaces.
    """
    require_mcp_infrastructure()
    if not 1 <= max_results <= 500:
        raise ToolError("max_results must be between 1 and 500.")

    try:
        repository = get_repository_by_full_name(repo_name, user_id=user_id)
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        raise ToolError(detail) from exc

    if repository["status"] != "cloned":
        raise ToolError(
            f"Repository {repository['full_name']} is not ready (status={repository['status']}). "
            "Clone and index the repository first."
        )

    root = resolve_repository_clone_path(repository["clone_path"])
    if not root.is_dir():
        raise ToolError(
            f"The local clone for {repository['full_name']} is missing. "
            "Run clone_repo with the repository URL (or force_reindex=true) to re-clone and index it first."
        )

    files = _read_source_files(root)
    references = Counter(
        token
        for _path, _language, source in files
        for token in _IDENTIFIER.findall(source)
    )
    candidates = _find_candidates(files, references)
    candidates.sort(key=lambda item: (item["confidence"] != "high", item["file"], item["line"]))

    returned = candidates[:max_results]
    return {
        "ok": True,
        "repository_id": repository["id"],
        "full_name": repository["full_name"],
        "analyzed_file_count": len(files),
        "candidate_count": len(candidates),
        "candidates_returned": len(returned),
        "max_results": max_results,
        "candidates": returned,
        "note": (
            "Candidates have no static references beyond their declaration. "
            "Review public APIs, framework hooks, reflection, and configuration before removal."
        ),
    }


def _read_source_files(root: Path) -> list[tuple[str, str, str]]:
    files: list[tuple[str, str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file() or _is_skipped(path, root):
            continue
        language = detect_language(path)
        if language is None:
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        files.append((path.relative_to(root).as_posix(), language, source))
    return files


def _find_candidates(
    files: list[tuple[str, str, str]], references: Counter[str]
) -> list[dict]:
    candidates: list[dict] = []
    for file_path, language, source in files:
        for symbol in extract_symbols(source.encode("utf-8"), language):
            if symbol.kind not in _ANALYZABLE_KINDS or symbol.parent_name is not None:
                continue
            if _is_excluded_name(symbol.name):
                continue
            if references[symbol.name] != 1:
                continue
            candidates.append(
                {
                    "name": symbol.name,
                    "kind": symbol.kind,
                    "file": file_path,
                    "line": symbol.start_line,
                    "end_line": symbol.end_line,
                    "signature": symbol.signature,
                    "confidence": "high" if symbol.name.startswith("_") else "medium",
                    "reason": "No static references found outside this declaration.",
                }
            )
    return candidates


def _is_skipped(path: Path, root: Path) -> bool:
    return any(part in SKIP_DIRECTORY_NAMES for part in path.relative_to(root).parts[:-1])


def _is_excluded_name(name: str) -> bool:
    if len(name) < 2:
        return True
    if name in _ENTRY_POINT_NAMES:
        return True
    return name.startswith("__") and name.endswith("__")

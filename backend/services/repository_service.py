from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import which
from urllib.parse import urlparse

from fastapi import HTTPException, status

from config import settings
from db import db_cursor
from parsers import clear_parsed_data, parse_repository
from services.cleanup_hooks import (
    cleanup_graph_for_repository,
    cleanup_qdrant_for_repository,
    reembed_repository,
)


GITHUB_HOSTS = {"github.com", "www.github.com"}
REPO_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True)
class ParsedRepository:
    url: str
    full_name: str
    clone_path: Path
    provider: str = "github"


def parse_github_repository_url(raw_url: str) -> ParsedRepository:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc not in GITHUB_HOSTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only public GitHub repository URLs are supported.",
        )

    path_parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(path_parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Repository URL must look like https://github.com/owner/repository.",
        )

    owner, repo = path_parts
    repo = repo.removesuffix(".git")
    if not REPO_NAME_PATTERN.match(owner) or not REPO_NAME_PATTERN.match(repo):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Repository owner or name contains unsupported characters.",
        )

    full_name = f"{owner}/{repo}"
    clone_path = settings.repository_clone_path / owner / repo
    normalized_url = f"https://github.com/{full_name}"
    return ParsedRepository(url=normalized_url, full_name=full_name, clone_path=clone_path)


def list_repositories() -> list[dict]:
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, url, full_name, provider, status, clone_path, default_branch, created_at, updated_at
            FROM repositories
            ORDER BY created_at DESC
            """
        )
        return list(cursor.fetchall())


def get_repository_by_id(repository_id: int) -> dict:
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, url, full_name, provider, status, clone_path, default_branch, created_at, updated_at
            FROM repositories
            WHERE id = %s
            """,
            (repository_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository with id {repository_id} was not found.",
            )
        return row


def create_repository_submission(raw_url: str) -> dict:
    repository = parse_github_repository_url(raw_url)

    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id
            FROM repositories
            WHERE url = %s OR full_name = %s
            """,
            (repository.url, repository.full_name),
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This repository has already been submitted.",
            )

    ensure_clone_parent_directory(repository.clone_path)

    created_record = insert_repository_record(repository)
    try:
        default_branch = clone_repository(repository)
    except HTTPException as exc:
        mark_repository_status(created_record["id"], status_value="failed")
        raise exc
    except Exception as exc:
        mark_repository_status(created_record["id"], status_value="failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected repository cloning failure: {exc}",
        ) from exc

    result = _parse_and_finalize(
        created_record["id"],
        repository.clone_path,
        default_branch=default_branch,
    )

    # Embed after initial clone + parse.
    reembed_repository(created_record["id"], repository.full_name, str(repository.clone_path))
    return result


def delete_repository(repository_id: int) -> None:
    record = get_repository_by_id(repository_id)
    clone_path = Path(record["clone_path"])

    cleanup_qdrant_for_repository(repository_id, record["full_name"])
    cleanup_graph_for_repository(repository_id, record["full_name"])
    # Parsed files/symbols also cascade via FK on repository delete; clear early for clarity.
    clear_parsed_data(repository_id)
    remove_clone_directory(clone_path)

    with db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM repositories WHERE id = %s", (repository_id,))
        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository with id {repository_id} was not found.",
            )


def reindex_repository(repository_id: int) -> dict:
    record = get_repository_by_id(repository_id)
    repository = ParsedRepository(
        url=record["url"],
        full_name=record["full_name"],
        clone_path=Path(record["clone_path"]),
        provider=record["provider"],
    )

    # Clear derived indexes first so stale embeddings/graph/parse data cannot linger.
    cleanup_qdrant_for_repository(repository_id, repository.full_name)
    cleanup_graph_for_repository(repository_id, repository.full_name)
    clear_parsed_data(repository_id)

    mark_repository_status(repository_id, status_value="reindexing")
    remove_clone_directory(repository.clone_path)
    ensure_clone_parent_directory(repository.clone_path)

    try:
        default_branch = clone_repository(repository)
    except HTTPException as exc:
        mark_repository_status(repository_id, status_value="failed")
        raise exc
    except Exception as exc:
        mark_repository_status(repository_id, status_value="failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected repository re-index failure: {exc}",
        ) from exc

    updated = _parse_and_finalize(
        repository_id,
        repository.clone_path,
        default_branch=default_branch,
    )

    # Placeholder for Day 5+ chunking/embeddings after a successful re-clone + parse.
    reembed_repository(repository_id, repository.full_name, str(repository.clone_path))
    return updated


def _parse_and_finalize(
    repository_id: int,
    clone_path: Path,
    *,
    default_branch: str | None,
) -> dict:
    mark_repository_status(
        repository_id,
        status_value="parsing",
        default_branch=default_branch,
    )
    try:
        parse_repository(repository_id, clone_path)
    except HTTPException as exc:
        mark_repository_status(repository_id, status_value="failed")
        raise exc
    except Exception as exc:
        mark_repository_status(repository_id, status_value="failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Repository parsing failed: {exc}",
        ) from exc

    return mark_repository_status(
        repository_id,
        status_value="cloned",
        default_branch=default_branch,
    )


def insert_repository_record(repository: ParsedRepository) -> dict:
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO repositories (url, full_name, clone_path, status, provider)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, url, full_name, provider, status, clone_path, default_branch, created_at, updated_at
            """,
            (
                repository.url,
                repository.full_name,
                str(repository.clone_path),
                "cloning",
                repository.provider,
            ),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create repository record.",
            )
        return row


def mark_repository_status(
    repository_id: int,
    *,
    status_value: str,
    default_branch: str | None = None,
) -> dict:
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE repositories
            SET status = %s,
                default_branch = COALESCE(%s, default_branch),
                updated_at = NOW()
            WHERE id = %s
            RETURNING id, url, full_name, provider, status, clone_path, default_branch, created_at, updated_at
            """,
            (status_value, default_branch, repository_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update repository status.",
            )
        return row


def ensure_clone_parent_directory(clone_path: Path) -> None:
    clone_path.parent.mkdir(parents=True, exist_ok=True)


def clone_repository(repository: ParsedRepository) -> str | None:
    if repository.clone_path.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The clone target already exists on disk for this repository.",
        )

    if which("git") is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Git is not installed in the backend runtime, so cloning cannot start.",
        )

    command = [
        "git",
        "clone",
        "--depth",
        "1",
        repository.url,
        str(repository.clone_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        remove_clone_directory(repository.clone_path)
        stderr = completed.stderr.strip() or completed.stdout.strip() or "git clone failed"
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Repository cloning failed: {stderr}",
        )

    return read_default_branch(repository.clone_path)


def remove_clone_directory(clone_path: Path) -> None:
    if not clone_path.exists():
        return
    shutil.rmtree(clone_path)


def read_default_branch(clone_path: Path) -> str | None:
    head_file = clone_path / ".git" / "HEAD"
    if not head_file.exists():
        return None

    head_contents = head_file.read_text(encoding="utf-8").strip()
    prefix = "ref: refs/heads/"
    if head_contents.startswith(prefix):
        return head_contents.removeprefix(prefix)
    return None

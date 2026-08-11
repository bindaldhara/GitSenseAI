"""Persisted chat conversations and messages."""

from __future__ import annotations

import json

from fastapi import HTTPException, status

from db import db_cursor


def create_conversation(
    user_id: int,
    repository_id: int,
    *,
    title: str | None = None,
) -> dict:
    conversation_title = (title or "New conversation").strip() or "New conversation"
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO conversations (user_id, repository_id, title)
            VALUES (%s, %s, %s)
            RETURNING id, user_id, repository_id, title, created_at, updated_at
            """,
            (user_id, repository_id, conversation_title),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create conversation.",
            )
        return row


def list_conversations(
    user_id: int,
    *,
    repository_id: int | None = None,
    limit: int = 50,
) -> list[dict]:
    params: list = [user_id]
    repo_clause = ""
    if repository_id is not None:
        repo_clause = " AND repository_id = %s"
        params.append(repository_id)
    params.append(limit)

    with db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT id, user_id, repository_id, title, created_at, updated_at
            FROM conversations
            WHERE user_id = %s{repo_clause}
            ORDER BY updated_at DESC
            LIMIT %s
            """,
            params,
        )
        return list(cursor.fetchall())


def get_conversation(conversation_id: int, user_id: int) -> dict:
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, user_id, repository_id, title, created_at, updated_at
            FROM conversations
            WHERE id = %s AND user_id = %s
            """,
            (conversation_id, user_id),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found.",
            )
        return row


def list_conversation_messages(conversation_id: int, user_id: int) -> list[dict]:
    get_conversation(conversation_id, user_id)
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, conversation_id, role, content, metadata, created_at
            FROM conversation_messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC, id ASC
            """,
            (conversation_id,),
        )
        return list(cursor.fetchall())


def append_conversation_messages(
    conversation_id: int,
    user_id: int,
    *,
    user_content: str,
    assistant_content: str,
    assistant_metadata: dict | None = None,
) -> None:
    get_conversation(conversation_id, user_id)
    metadata_json = json.dumps(assistant_metadata or {})

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO conversation_messages (conversation_id, role, content, metadata)
            VALUES (%s, 'user', %s, '{}'::jsonb)
            """,
            (conversation_id, user_content),
        )
        cursor.execute(
            """
            INSERT INTO conversation_messages (conversation_id, role, content, metadata)
            VALUES (%s, 'assistant', %s, %s::jsonb)
            """,
            (conversation_id, assistant_content, metadata_json),
        )
        cursor.execute(
            """
            UPDATE conversations
            SET updated_at = NOW(),
                title = CASE
                    WHEN title = 'New conversation' THEN %s
                    ELSE title
                END
            WHERE id = %s
            """,
            (user_content[:80], conversation_id),
        )


def conversation_history_for_chat(conversation_id: int, user_id: int) -> list[dict[str, str]]:
    rows = list_conversation_messages(conversation_id, user_id)
    history: list[dict[str, str]] = []
    for row in rows:
        role = row["role"]
        if role in {"user", "assistant"}:
            history.append({"role": role, "content": row["content"]})
    return history

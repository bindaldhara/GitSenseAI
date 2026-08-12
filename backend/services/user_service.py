"""App user records linked to Supabase Auth identities."""

from __future__ import annotations

import re
import uuid

from db import db_cursor

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_id(user_id: int) -> dict | None:
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT id, email, created_at FROM users WHERE id = %s",
            (user_id,),
        )
        return cursor.fetchone()


def get_user_id_by_email(email: str) -> int | None:
    normalized = _normalize_email(email)
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (normalized,),
        )
        row = cursor.fetchone()
        return int(row["id"]) if row else None


def sync_user_from_supabase(supabase_id: str, email: str) -> dict:
    """Create or link a local user row for a Supabase-authenticated identity."""
    normalized = _normalize_email(email)
    if not _EMAIL_RE.match(normalized):
        raise ValueError("Invalid email in Supabase token.")

    parsed_id = uuid.UUID(str(supabase_id))

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "SELECT id, email, created_at FROM users WHERE supabase_id = %s",
            (str(parsed_id),),
        )
        row = cursor.fetchone()
        if row is not None:
            return row

        cursor.execute(
            "SELECT id, email, created_at, supabase_id FROM users WHERE email = %s",
            (normalized,),
        )
        row = cursor.fetchone()
        if row is not None:
            cursor.execute(
                """
                UPDATE users
                SET supabase_id = %s
                WHERE id = %s
                RETURNING id, email, created_at
                """,
                (str(parsed_id), row["id"]),
            )
            linked = cursor.fetchone()
            if linked is None:
                raise RuntimeError("Failed to link Supabase user.")
            return linked

        cursor.execute(
            """
            INSERT INTO users (supabase_id, email)
            VALUES (%s, %s)
            RETURNING id, email, created_at
            """,
            (str(parsed_id), normalized),
        )
        created = cursor.fetchone()
        if created is None:
            raise RuntimeError("Failed to create app user.")
        return created

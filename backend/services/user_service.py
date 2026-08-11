"""User registration and lookup."""

from __future__ import annotations

import re

from fastapi import HTTPException, status

from auth.security import hash_password, verify_password
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


def get_user_by_email(email: str) -> dict | None:
    with db_cursor() as cursor:
        cursor.execute(
            "SELECT id, email, password_hash, created_at FROM users WHERE email = %s",
            (_normalize_email(email),),
        )
        return cursor.fetchone()


def register_user(email: str, password: str) -> dict:
    normalized = _normalize_email(email)
    if not _EMAIL_RE.match(normalized):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email address.",
        )
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters.",
        )

    existing = get_user_by_email(normalized)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    password_hash = hash_password(password)
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO users (email, password_hash)
            VALUES (%s, %s)
            RETURNING id, email, created_at
            """,
            (normalized, password_hash),
        )
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user.",
            )
        return row


def authenticate_user(email: str, password: str) -> dict:
    row = get_user_by_email(email)
    if row is None or not verify_password(password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return {"id": row["id"], "email": row["email"], "created_at": row["created_at"]}

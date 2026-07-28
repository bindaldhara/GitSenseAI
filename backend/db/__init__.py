"""Database helpers for GitSense AI."""

from collections.abc import Iterator
from contextlib import contextmanager

from psycopg import Connection, connect
from psycopg.rows import dict_row

from config import settings


CREATE_REPOSITORIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL UNIQUE,
    clone_path TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    provider TEXT NOT NULL,
    default_branch TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def get_connection() -> Connection:
    return connect(settings.database_url, row_factory=dict_row)


@contextmanager
def db_cursor(commit: bool = False) -> Iterator:
    with get_connection() as connection:
        with connection.cursor() as cursor:
            yield cursor
        if commit:
            connection.commit()


def initialize_database() -> None:
    with db_cursor(commit=True) as cursor:
        cursor.execute(CREATE_REPOSITORIES_TABLE_SQL)

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

CREATE_REPOSITORY_FILES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS repository_files (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    language TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    line_count INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (repository_id, path)
);
"""

CREATE_REPOSITORY_SYMBOLS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS repository_symbols (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_id INTEGER NOT NULL REFERENCES repository_files(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    signature TEXT,
    parent_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

CREATE_REPOSITORY_FILES_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_repository_files_repository_id
ON repository_files (repository_id);
"""

CREATE_REPOSITORY_SYMBOLS_REPO_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_repository_symbols_repository_id
ON repository_symbols (repository_id);
"""

CREATE_REPOSITORY_SYMBOLS_FILE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_repository_symbols_file_id
ON repository_symbols (file_id);
"""

CREATE_REPOSITORY_SKIPPED_FILES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS repository_skipped_files (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    path TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (repository_id, path)
);
"""

CREATE_REPOSITORY_SKIPPED_FILES_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_repository_skipped_files_repository_id
ON repository_skipped_files (repository_id);
"""

CREATE_REPOSITORY_GRAPH_NODES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS repository_graph_nodes (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    node_key TEXT NOT NULL,
    node_type TEXT NOT NULL,
    label TEXT NOT NULL,
    file_path TEXT,
    symbol_kind TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (repository_id, node_key)
);
"""

CREATE_REPOSITORY_GRAPH_EDGES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS repository_graph_edges (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    source_key TEXT NOT NULL,
    target_key TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (repository_id, source_key, target_key, edge_type)
);
"""

CREATE_REPOSITORY_GRAPH_NODES_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_repository_graph_nodes_repository_id
ON repository_graph_nodes (repository_id);
"""

CREATE_REPOSITORY_GRAPH_EDGES_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_repository_graph_edges_repository_id
ON repository_graph_edges (repository_id);
"""

CREATE_USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

CREATE_CONVERSATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New conversation',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

CREATE_CONVERSATION_MESSAGES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS conversation_messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

CREATE_CONVERSATIONS_USER_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id);
"""

CREATE_CONVERSATIONS_REPO_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_conversations_repository_id ON conversations (repository_id);
"""

CREATE_CONVERSATION_MESSAGES_CONV_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_id
ON conversation_messages (conversation_id);
"""

ALTER_REPOSITORIES_USER_ID_SQL = """
ALTER TABLE repositories ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
"""

CREATE_REPOSITORIES_USER_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_repositories_user_id ON repositories (user_id);
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
        cursor.execute(CREATE_REPOSITORY_FILES_TABLE_SQL)
        cursor.execute(CREATE_REPOSITORY_SYMBOLS_TABLE_SQL)
        cursor.execute(CREATE_REPOSITORY_SKIPPED_FILES_TABLE_SQL)
        cursor.execute(CREATE_REPOSITORY_FILES_INDEX_SQL)
        cursor.execute(CREATE_REPOSITORY_SYMBOLS_REPO_INDEX_SQL)
        cursor.execute(CREATE_REPOSITORY_SYMBOLS_FILE_INDEX_SQL)
        cursor.execute(CREATE_REPOSITORY_SKIPPED_FILES_INDEX_SQL)
        cursor.execute(CREATE_REPOSITORY_GRAPH_NODES_TABLE_SQL)
        cursor.execute(CREATE_REPOSITORY_GRAPH_EDGES_TABLE_SQL)
        cursor.execute(CREATE_REPOSITORY_GRAPH_NODES_INDEX_SQL)
        cursor.execute(CREATE_REPOSITORY_GRAPH_EDGES_INDEX_SQL)
        cursor.execute(CREATE_USERS_TABLE_SQL)
        cursor.execute(ALTER_REPOSITORIES_USER_ID_SQL)
        cursor.execute(CREATE_REPOSITORIES_USER_INDEX_SQL)
        cursor.execute(CREATE_CONVERSATIONS_TABLE_SQL)
        cursor.execute(CREATE_CONVERSATION_MESSAGES_TABLE_SQL)
        cursor.execute(CREATE_CONVERSATIONS_USER_INDEX_SQL)
        cursor.execute(CREATE_CONVERSATIONS_REPO_INDEX_SQL)
        cursor.execute(CREATE_CONVERSATION_MESSAGES_CONV_INDEX_SQL)

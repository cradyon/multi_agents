from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

from app.persistence.models import CheckpointRecord, RunSummary, UserRecord


def _json_dumps(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _json_loads(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    data = json.loads(value)
    return data if isinstance(data, dict) else {}


def _normalize_db_path(db_path: str | Path) -> str:
    return str(Path(db_path).expanduser())


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


class _SQLiteBaseStore:
    def __init__(self, db_path: str | Path):
        self.db_path = _normalize_db_path(db_path)
        self._memory_connection: sqlite3.Connection | None = None
        self._is_memory = self.db_path == ":memory:"
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        if self._is_memory:
            if self._memory_connection is None:
                self._memory_connection = sqlite3.connect(self.db_path)
                self._memory_connection.row_factory = sqlite3.Row
            conn = self._memory_connection
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            if not self._is_memory:
                conn.close()

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_summaries (
                    summary_id TEXT PRIMARY KEY,
                    thread_id TEXT NOT NULL,
                    task TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_created ON checkpoints(thread_id, created_at DESC)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_summaries_thread_created ON run_summaries(thread_id, created_at DESC)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")


class SQLiteCheckpointStore(_SQLiteBaseStore):
    """Simple checkpoint history backed by SQLite."""

    def save(self, record: CheckpointRecord) -> CheckpointRecord:
        checkpoint_id = record.checkpoint_id or uuid4().hex
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO checkpoints (
                    checkpoint_id, thread_id, step_name, payload_json, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint_id,
                    record.thread_id,
                    record.step_name,
                    _json_dumps(record.payload),
                    _json_dumps(record.metadata),
                    record.created_at.isoformat(),
                ),
            )
        return CheckpointRecord(
            checkpoint_id=checkpoint_id,
            thread_id=record.thread_id,
            step_name=record.step_name,
            payload=dict(record.payload),
            metadata=dict(record.metadata),
            created_at=record.created_at,
        )

    def list(self, thread_id: str, limit: int = 50) -> list[CheckpointRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT checkpoint_id, thread_id, step_name, payload_json, metadata_json, created_at
                FROM checkpoints
                WHERE thread_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (thread_id, limit),
            ).fetchall()
        return [
            CheckpointRecord(
                checkpoint_id=row["checkpoint_id"],
                thread_id=row["thread_id"],
                step_name=row["step_name"],
                payload=_json_loads(row["payload_json"]),
                metadata=_json_loads(row["metadata_json"]),
                created_at=_parse_dt(row["created_at"]),
            )
            for row in rows
        ]

    def latest(self, thread_id: str) -> CheckpointRecord | None:
        checkpoints = self.list(thread_id=thread_id, limit=1)
        return checkpoints[0] if checkpoints else None


class SQLiteMemoryStore(_SQLiteBaseStore):
    """Lightweight memory store for run summaries."""

    def save(self, summary: RunSummary) -> RunSummary:
        summary_id = summary.summary_id or uuid4().hex
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO run_summaries (
                    summary_id, thread_id, task, summary, status, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary_id,
                    summary.thread_id,
                    summary.task,
                    summary.summary,
                    summary.status,
                    _json_dumps(summary.metadata),
                    summary.created_at.isoformat(),
                ),
            )
        return RunSummary(
            summary_id=summary_id,
            thread_id=summary.thread_id,
            task=summary.task,
            summary=summary.summary,
            status=summary.status,
            metadata=dict(summary.metadata),
            created_at=summary.created_at,
        )

    def list(self, thread_id: str | None = None, limit: int = 50) -> list[RunSummary]:
        query = """
            SELECT summary_id, thread_id, task, summary, status, metadata_json, created_at
            FROM run_summaries
        """
        params: tuple[Any, ...]
        if thread_id is None:
            query += " ORDER BY created_at DESC LIMIT ?"
            params = (limit,)
        else:
            query += " WHERE thread_id = ? ORDER BY created_at DESC LIMIT ?"
            params = (thread_id, limit)

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [
            RunSummary(
                summary_id=row["summary_id"],
                thread_id=row["thread_id"],
                task=row["task"],
                summary=row["summary"],
                status=row["status"],
                metadata=_json_loads(row["metadata_json"]),
                created_at=_parse_dt(row["created_at"]),
            )
            for row in rows
        ]

    def latest(self, thread_id: str) -> RunSummary | None:
        summaries = self.list(thread_id=thread_id, limit=1)
        return summaries[0] if summaries else None


class SQLiteUserStore(_SQLiteBaseStore):
    """User store for simple auth backed by the same SQLite database."""

    def create_user(self, username: str, password_hash: str) -> UserRecord:
        user_id = uuid4().hex
        created_at = datetime.utcnow().isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, username, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, username, password_hash, created_at),
            )
        return UserRecord(
            user_id=user_id,
            username=username,
            password_hash=password_hash,
            created_at=_parse_dt(created_at),
        )

    def get_user(self, username: str) -> UserRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT user_id, username, password_hash, created_at
                FROM users
                WHERE username = ?
                COLLATE NOCASE
                LIMIT 1
                """,
                (username,),
            ).fetchone()
        if row is None:
            return None
        return UserRecord(
            user_id=row["user_id"],
            username=row["username"],
            password_hash=row["password_hash"],
            created_at=_parse_dt(row["created_at"]),
        )

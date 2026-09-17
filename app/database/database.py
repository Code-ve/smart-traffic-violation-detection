"""
SQLite database connection and schema management.

Provides functions to initialise the database, obtain connections,
and ensure all required tables exist.  Uses the stdlib ``sqlite3``
module — no ORM required for this project's scope.
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

from app.config.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── SQL: Table definitions ───────────────────────────────────────────────

_SCHEMA_SQL = """
-- Processing sessions — one row per uploaded image/video
CREATE TABLE IF NOT EXISTS processing_sessions (
    id               TEXT PRIMARY KEY,
    filename         TEXT NOT NULL,
    file_type        TEXT NOT NULL DEFAULT 'video',
    started_at       TEXT NOT NULL,
    completed_at     TEXT,
    status           TEXT NOT NULL DEFAULT 'processing',
    total_frames     INTEGER DEFAULT 0,
    processed_frames INTEGER DEFAULT 0,
    total_vehicles   INTEGER DEFAULT 0,
    unique_vehicles  INTEGER DEFAULT 0,
    total_violations INTEGER DEFAULT 0,
    avg_fps          REAL DEFAULT 0.0,
    avg_inference_ms REAL DEFAULT 0.0,
    model_used       TEXT,
    output_path      TEXT
);

-- Individual object detections (sampled per session)
CREATE TABLE IF NOT EXISTS detections (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT NOT NULL REFERENCES processing_sessions(id),
    frame_number INTEGER NOT NULL,
    track_id     INTEGER,
    class_name   TEXT NOT NULL,
    confidence   REAL NOT NULL,
    x1           REAL NOT NULL,
    y1           REAL NOT NULL,
    x2           REAL NOT NULL,
    y2           REAL NOT NULL,
    timestamp    TEXT
);

-- Violation events
CREATE TABLE IF NOT EXISTS violations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT REFERENCES processing_sessions(id),
    timestamp       TEXT NOT NULL,
    violation_type  TEXT NOT NULL,
    track_id        INTEGER,
    vehicle_type    TEXT,
    confidence      REAL,
    frame_number    INTEGER,
    video_timestamp TEXT,
    evidence_path   TEXT,
    status          TEXT NOT NULL DEFAULT 'Detected',
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Indices for common queries
CREATE INDEX IF NOT EXISTS idx_detections_session ON detections(session_id);
CREATE INDEX IF NOT EXISTS idx_violations_session ON violations(session_id);
CREATE INDEX IF NOT EXISTS idx_violations_type    ON violations(violation_type);
CREATE INDEX IF NOT EXISTS idx_violations_status  ON violations(status);
"""


def _db_path() -> str:
    """Return the configured database file path, creating parent dirs."""
    path = get_settings().database_url
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    return path


def init_db() -> None:
    """
    Create all tables and indices if they do not exist.

    Safe to call multiple times — uses ``CREATE TABLE IF NOT EXISTS``.
    """
    path = _db_path()
    conn = sqlite3.connect(path)
    try:
        conn.executescript(_SCHEMA_SQL)
        conn.commit()
        logger.info("Database initialised at %s", path)
    finally:
        conn.close()


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager yielding a SQLite connection with ``Row`` factory.

    Usage::

        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM violations").fetchall()
    """
    path = _db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

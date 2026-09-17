"""
Data-access repository for processing sessions, detections, and violations.

All database reads and writes go through this module, keeping SQL
isolated from the rest of the application.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from app.database.database import get_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
#  Processing Sessions
# ═══════════════════════════════════════════════════════════════════════════

def create_session(
    filename: str,
    file_type: str = "video",
    model_used: str | None = None,
) -> str:
    """
    Create a new processing session and return its ID.
    """
    session_id = uuid.uuid4().hex[:12]
    now = datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO processing_sessions
               (id, filename, file_type, started_at, model_used)
               VALUES (?, ?, ?, ?, ?)""",
            (session_id, filename, file_type, now, model_used),
        )
    logger.info("Created session %s for %s", session_id, filename)
    return session_id


def update_session(session_id: str, **kwargs: Any) -> None:
    """
    Update arbitrary columns on a processing session.

    Example::

        update_session(sid, status="completed", total_frames=120)
    """
    if not kwargs:
        return
    cols = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [session_id]
    with get_connection() as conn:
        conn.execute(
            f"UPDATE processing_sessions SET {cols} WHERE id=?", vals
        )


def get_session(session_id: str) -> dict | None:
    """Return a session as a dict, or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM processing_sessions WHERE id=?", (session_id,)
        ).fetchone()
    return dict(row) if row else None


def get_all_sessions() -> list[dict]:
    """Return all sessions ordered by most recent first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM processing_sessions ORDER BY started_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════
#  Detections
# ═══════════════════════════════════════════════════════════════════════════

def create_detection(
    session_id: str,
    frame_number: int,
    class_name: str,
    confidence: float,
    x1: float, y1: float, x2: float, y2: float,
    track_id: int | None = None,
    timestamp: str | None = None,
) -> int:
    """Insert a single detection row and return its ID."""
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO detections
               (session_id, frame_number, track_id, class_name, confidence,
                x1, y1, x2, y2, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, frame_number, track_id, class_name, confidence,
             x1, y1, x2, y2, timestamp),
        )
    return cur.lastrowid  # type: ignore[return-value]


def create_detections_bulk(session_id: str, detections: list[dict]) -> None:
    """Insert multiple detections in one transaction."""
    if not detections:
        return
    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO detections
               (session_id, frame_number, track_id, class_name, confidence,
                x1, y1, x2, y2, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    session_id,
                    d["frame_number"],
                    d.get("track_id"),
                    d["class_name"],
                    d["confidence"],
                    d["x1"], d["y1"], d["x2"], d["y2"],
                    d.get("timestamp"),
                )
                for d in detections
            ],
        )


def get_detections(session_id: str, limit: int = 5000) -> list[dict]:
    """Return detections for a session."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM detections WHERE session_id=? ORDER BY frame_number LIMIT ?",
            (session_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════
#  Violations
# ═══════════════════════════════════════════════════════════════════════════

def create_violation(
    session_id: str | None,
    violation_type: str,
    track_id: int | None = None,
    vehicle_type: str | None = None,
    confidence: float | None = None,
    frame_number: int | None = None,
    video_timestamp: str | None = None,
    evidence_path: str | None = None,
) -> int:
    """Insert a violation event and return its ID."""
    now = datetime.now().isoformat()
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO violations
               (session_id, timestamp, violation_type, track_id, vehicle_type,
                confidence, frame_number, video_timestamp, evidence_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, now, violation_type, track_id, vehicle_type,
             confidence, frame_number, video_timestamp, evidence_path),
        )
    logger.info("Violation recorded: %s track=%s", violation_type, track_id)
    return cur.lastrowid  # type: ignore[return-value]


def get_violations(
    session_id: str | None = None,
    violation_type: str | None = None,
    vehicle_type: str | None = None,
    status: str | None = None,
    limit: int = 500,
) -> list[dict]:
    """
    Query violations with optional filters.

    All filter parameters are optional.  Passing None means no filter
    on that column.
    """
    clauses: list[str] = []
    params: list[Any] = []

    if session_id:
        clauses.append("session_id=?")
        params.append(session_id)
    if violation_type:
        clauses.append("violation_type=?")
        params.append(violation_type)
    if vehicle_type:
        clauses.append("vehicle_type=?")
        params.append(vehicle_type)
    if status:
        clauses.append("status=?")
        params.append(status)

    where = " AND ".join(clauses)
    sql = "SELECT * FROM violations"
    if where:
        sql += f" WHERE {where}"
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def update_violation_status(violation_id: int, new_status: str) -> bool:
    """
    Update the status of a violation (Detected → Reviewed → Resolved).

    Returns True if a row was updated.
    """
    valid = {"Detected", "Reviewed", "Resolved"}
    if new_status not in valid:
        return False
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE violations SET status=? WHERE id=?", (new_status, violation_id)
        )
    return cur.rowcount > 0


def count_violations(session_id: str | None = None) -> dict:
    """Return violation counts grouped by type."""
    sql = "SELECT violation_type, COUNT(*) as cnt FROM violations"
    params: list[Any] = []
    if session_id:
        sql += " WHERE session_id=?"
        params.append(session_id)
    sql += " GROUP BY violation_type"
    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return {row["violation_type"]: row["cnt"] for row in rows}

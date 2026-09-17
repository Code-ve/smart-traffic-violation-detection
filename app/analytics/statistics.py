"""
Analytics service — aggregates detection and violation data for the dashboard.

All data is sourced from the SQLite database, ensuring the dashboard
displays real results from actual processing sessions rather than
hard-coded values.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.database import repository as repo
from app.database.database import get_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """
    Provides aggregated statistics and chart-ready data.

    Every method queries the database — no caching or hard-coded data.
    """

    # ── Traffic statistics ───────────────────────────────────────────────

    def get_traffic_stats(self, session_id: str | None = None) -> dict[str, Any]:
        """
        Vehicle counts by type + totals.

        Returns dict with keys: total_vehicles, unique_vehicles, and
        per-class counts (car, motorcycle, bus, truck, etc.).
        """
        where = "WHERE session_id=?" if session_id else ""
        params: list[Any] = [session_id] if session_id else []

        with get_connection() as conn:
            # Per-class unique vehicle counts (by track_id)
            rows = conn.execute(
                f"""SELECT class_name,
                           COUNT(DISTINCT COALESCE(track_id, id)) as cnt
                    FROM detections {where}
                    GROUP BY class_name""",
                params,
            ).fetchall()

        vehicle_counts = {row["class_name"]: row["cnt"] for row in rows}
        total = sum(vehicle_counts.values())

        # Also get session-level summary if available
        unique = total
        if session_id:
            session = repo.get_session(session_id)
            if session:
                unique = session.get("unique_vehicles", total)

        return {
            "total_vehicles": total,
            "unique_vehicles": unique,
            "by_type": vehicle_counts,
        }

    # ── Violation statistics ─────────────────────────────────────────────

    def get_violation_stats(self, session_id: str | None = None) -> dict[str, Any]:
        """
        Violation counts by type + total + percentage.
        """
        where = "WHERE session_id=?" if session_id else ""
        params: list[Any] = [session_id] if session_id else []

        with get_connection() as conn:
            rows = conn.execute(
                f"""SELECT violation_type, COUNT(*) as cnt
                    FROM violations {where}
                    GROUP BY violation_type""",
                params,
            ).fetchall()

            total_violations = conn.execute(
                f"SELECT COUNT(*) as cnt FROM violations {where}", params,
            ).fetchone()["cnt"]

        by_type = {row["violation_type"]: row["cnt"] for row in rows}

        # Compute percentage against unique vehicles
        traffic = self.get_traffic_stats(session_id)
        unique = traffic["unique_vehicles"] or 1
        percentage = round(total_violations / unique * 100, 2) if unique > 0 else 0

        return {
            "total_violations": total_violations,
            "by_type": by_type,
            "violation_percentage": percentage,
        }

    # ── Timeline data (for charts) ──────────────────────────────────────

    def get_timeline_data(self, session_id: str) -> dict[str, Any]:
        """
        Detections and violations aggregated by frame ranges.
        Useful for "traffic volume over time" and "violations over time" charts.
        """
        bucket_size = 30  # group every 30 frames

        with get_connection() as conn:
            # Detection volume per bucket
            det_rows = conn.execute(
                """SELECT (frame_number / ?) * ? as bucket,
                          COUNT(*) as cnt
                   FROM detections WHERE session_id=?
                   GROUP BY bucket ORDER BY bucket""",
                (bucket_size, bucket_size, session_id),
            ).fetchall()

            # Violation timeline
            viol_rows = conn.execute(
                """SELECT frame_number, violation_type
                   FROM violations WHERE session_id=?
                   ORDER BY frame_number""",
                (session_id,),
            ).fetchall()

        detection_timeline = [
            {"frame": row["bucket"], "count": row["cnt"]} for row in det_rows
        ]
        violation_timeline = [
            {"frame": row["frame_number"], "type": row["violation_type"]}
            for row in viol_rows
        ]

        return {
            "detection_timeline": detection_timeline,
            "violation_timeline": violation_timeline,
        }

    # ── Confidence distribution ──────────────────────────────────────────

    def get_confidence_distribution(
        self, session_id: str | None = None, bins: int = 10,
    ) -> list[dict]:
        """
        Histogram of detection confidence scores.
        """
        where = "WHERE session_id=?" if session_id else ""
        params: list[Any] = [session_id] if session_id else []

        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT confidence FROM detections {where}", params,
            ).fetchall()

        confidences = [row["confidence"] for row in rows]
        if not confidences:
            return []

        bin_width = 1.0 / bins
        histogram: list[dict] = []
        for i in range(bins):
            low = round(i * bin_width, 2)
            high = round((i + 1) * bin_width, 2)
            count = sum(1 for c in confidences if low <= c < high)
            histogram.append({"range": f"{low:.1f}-{high:.1f}", "count": count})

        return histogram

    # ── Global summary ───────────────────────────────────────────────────

    def get_summary(self) -> dict[str, Any]:
        """
        Global summary across all processing sessions.
        """
        sessions = repo.get_all_sessions()
        total_sessions = len(sessions)
        completed = sum(1 for s in sessions if s.get("status") == "completed")
        total_frames = sum(s.get("total_frames", 0) for s in sessions)
        total_violations = sum(s.get("total_violations", 0) for s in sessions)
        total_vehicles = sum(s.get("unique_vehicles", 0) for s in sessions)

        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed,
            "total_frames_processed": total_frames,
            "total_vehicles_tracked": total_vehicles,
            "total_violations_detected": total_violations,
            "sessions": [
                {
                    "id": s["id"],
                    "filename": s["filename"],
                    "status": s["status"],
                    "started_at": s["started_at"],
                    "total_violations": s.get("total_violations", 0),
                    "unique_vehicles": s.get("unique_vehicles", 0),
                }
                for s in sessions[:20]  # Limit to recent 20
            ],
        }

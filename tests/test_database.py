"""Tests for the database layer — schema, CRUD, and queries."""

import pytest

from app.database import repository as repo


class TestDatabaseSchema:
    """Tests for database initialisation and table creation."""

    def test_tables_exist(self, temp_db):
        import sqlite3
        conn = sqlite3.connect(temp_db)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {t[0] for t in tables}
        conn.close()
        assert "processing_sessions" in table_names
        assert "detections" in table_names
        assert "violations" in table_names


class TestSessionRepository:
    """Tests for processing session CRUD."""

    def test_create_session(self, temp_db):
        sid = repo.create_session("test_video.mp4", "video", "yolov8n")
        assert len(sid) == 12

    def test_get_session(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        session = repo.get_session(sid)
        assert session is not None
        assert session["filename"] == "test.mp4"
        assert session["status"] == "processing"

    def test_update_session(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        repo.update_session(sid, status="completed", total_frames=100)
        session = repo.get_session(sid)
        assert session["status"] == "completed"
        assert session["total_frames"] == 100

    def test_get_all_sessions(self, temp_db):
        repo.create_session("a.mp4", "video")
        repo.create_session("b.mp4", "video")
        sessions = repo.get_all_sessions()
        assert len(sessions) == 2

    def test_get_nonexistent_session(self, temp_db):
        assert repo.get_session("nonexistent") is None


class TestDetectionRepository:
    """Tests for detection CRUD."""

    def test_create_detection(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        det_id = repo.create_detection(
            session_id=sid, frame_number=0, class_name="car",
            confidence=0.92, x1=100, y1=200, x2=300, y2=400, track_id=1,
        )
        assert det_id > 0

    def test_bulk_insert(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        dets = [
            {"frame_number": i, "class_name": "car", "confidence": 0.9,
             "x1": 0, "y1": 0, "x2": 50, "y2": 50, "track_id": i}
            for i in range(10)
        ]
        repo.create_detections_bulk(sid, dets)
        result = repo.get_detections(sid)
        assert len(result) == 10

    def test_get_detections_with_limit(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        dets = [
            {"frame_number": i, "class_name": "car", "confidence": 0.9,
             "x1": 0, "y1": 0, "x2": 50, "y2": 50}
            for i in range(20)
        ]
        repo.create_detections_bulk(sid, dets)
        result = repo.get_detections(sid, limit=5)
        assert len(result) == 5


class TestViolationRepository:
    """Tests for violation CRUD and filtering."""

    def test_create_violation(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        vid = repo.create_violation(
            session_id=sid, violation_type="RED_LIGHT_VIOLATION",
            track_id=1, vehicle_type="car", confidence=0.9, frame_number=50,
        )
        assert vid > 0

    def test_get_violations_no_filter(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        repo.create_violation(sid, "RED_LIGHT_VIOLATION", track_id=1, vehicle_type="car")
        repo.create_violation(sid, "SPEED_ZONE_VIOLATION", track_id=2, vehicle_type="truck")
        violations = repo.get_violations()
        assert len(violations) == 2

    def test_filter_by_type(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        repo.create_violation(sid, "RED_LIGHT_VIOLATION", vehicle_type="car")
        repo.create_violation(sid, "SPEED_ZONE_VIOLATION", vehicle_type="truck")
        result = repo.get_violations(violation_type="RED_LIGHT_VIOLATION")
        assert len(result) == 1
        assert result[0]["violation_type"] == "RED_LIGHT_VIOLATION"

    def test_filter_by_vehicle_type(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        repo.create_violation(sid, "RED_LIGHT_VIOLATION", vehicle_type="car")
        repo.create_violation(sid, "RED_LIGHT_VIOLATION", vehicle_type="truck")
        result = repo.get_violations(vehicle_type="truck")
        assert len(result) == 1

    def test_filter_by_status(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        repo.create_violation(sid, "RED_LIGHT_VIOLATION")
        result = repo.get_violations(status="Detected")
        assert len(result) == 1

    def test_update_violation_status(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        vid = repo.create_violation(sid, "RED_LIGHT_VIOLATION")
        success = repo.update_violation_status(vid, "Reviewed")
        assert success is True
        violations = repo.get_violations(status="Reviewed")
        assert len(violations) == 1

    def test_update_invalid_status(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        vid = repo.create_violation(sid, "RED_LIGHT_VIOLATION")
        success = repo.update_violation_status(vid, "InvalidStatus")
        assert success is False

    def test_count_violations(self, temp_db):
        sid = repo.create_session("test.mp4", "video")
        repo.create_violation(sid, "RED_LIGHT_VIOLATION")
        repo.create_violation(sid, "RED_LIGHT_VIOLATION")
        repo.create_violation(sid, "SPEED_ZONE_VIOLATION")
        counts = repo.count_violations(sid)
        assert counts["RED_LIGHT_VIOLATION"] == 2
        assert counts["SPEED_ZONE_VIOLATION"] == 1

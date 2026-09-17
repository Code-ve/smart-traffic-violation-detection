"""
Shared pytest fixtures for the test suite.
"""

import os
import sys
import tempfile
import sqlite3

import numpy as np
import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import init_db, _SCHEMA_SQL


@pytest.fixture()
def temp_db(tmp_path, monkeypatch):
    """Provide a temporary SQLite database for each test."""
    db_path = str(tmp_path / "test_traffic.db")
    monkeypatch.setenv("DATABASE_URL", db_path)

    # Also patch get_settings to return the temp path
    from app.config import settings as settings_module
    original = settings_module.get_settings

    def _patched():
        s = original()
        # Override the database_url field
        object.__setattr__(s, 'database_url', db_path)
        return s

    monkeypatch.setattr(settings_module, "get_settings", _patched)

    # Initialise schema
    conn = sqlite3.connect(db_path)
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    conn.close()

    return db_path


@pytest.fixture()
def sample_frame():
    """Generate a synthetic BGR frame (640×480×3)."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


@pytest.fixture()
def sample_detections():
    """Return a list of mock Detection objects."""
    from app.cv.detector import Detection
    return [
        Detection(class_name="car", confidence=0.92, x1=100, y1=200, x2=300, y2=400,
                  frame_number=0, track_id=1),
        Detection(class_name="motorcycle", confidence=0.85, x1=400, y1=100, x2=500, y2=300,
                  frame_number=0, track_id=2),
        Detection(class_name="truck", confidence=0.78, x1=50, y1=50, x2=250, y2=250,
                  frame_number=0, track_id=3),
    ]

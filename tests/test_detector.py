"""Tests for the VehicleDetector module."""

import pytest
import numpy as np

from app.cv.detector import Detection, VehicleDetector, TRAFFIC_CLASSES


class TestDetection:
    """Tests for the Detection dataclass."""

    def test_center(self):
        d = Detection(class_name="car", confidence=0.9, x1=100, y1=200, x2=300, y2=400)
        assert d.center == (200.0, 300.0)

    def test_width_height_area(self):
        d = Detection(class_name="bus", confidence=0.8, x1=0, y1=0, x2=100, y2=50)
        assert d.width == 100
        assert d.height == 50
        assert d.area == 5000

    def test_to_dict(self):
        d = Detection(class_name="car", confidence=0.9123, x1=10.5, y1=20.3,
                      x2=110.7, y2=120.9, frame_number=5, track_id=7)
        out = d.to_dict()
        assert out["class_name"] == "car"
        assert out["confidence"] == 0.9123
        assert out["track_id"] == 7
        assert out["frame_number"] == 5

    def test_track_id_default_none(self):
        d = Detection(class_name="truck", confidence=0.5, x1=0, y1=0, x2=50, y2=50)
        assert d.track_id is None


class TestVehicleDetector:
    """Tests for VehicleDetector initialisation and state."""

    def test_not_loaded_by_default(self):
        detector = VehicleDetector()
        assert detector.is_loaded is False

    def test_detect_raises_without_model(self):
        detector = VehicleDetector()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        with pytest.raises(Exception):  # ProcessingError
            detector.detect(frame)

    def test_traffic_classes_defined(self):
        assert "car" in TRAFFIC_CLASSES
        assert "motorcycle" in TRAFFIC_CLASSES
        assert "bus" in TRAFFIC_CLASSES
        assert "truck" in TRAFFIC_CLASSES
        assert "person" in TRAFFIC_CLASSES
        assert "bicycle" in TRAFFIC_CLASSES

"""Tests for the VehicleTracker module."""

import pytest

from app.cv.detector import Detection
from app.cv.tracker import VehicleTracker, TrackState


class TestTrackState:
    """Tests for TrackState dataclass."""

    def test_displacement_single_point(self):
        ts = TrackState(track_id=1, trajectory=[(10, 20)])
        assert ts.displacement == 0.0

    def test_displacement_two_points(self):
        ts = TrackState(track_id=1, trajectory=[(0, 0), (3, 4)])
        assert abs(ts.displacement - 5.0) < 0.01  # 3-4-5 triangle

    def test_last_center(self):
        ts = TrackState(track_id=1, trajectory=[(1, 2), (3, 4)])
        assert ts.last_center == (3, 4)

    def test_last_center_empty(self):
        ts = TrackState(track_id=1)
        assert ts.last_center is None


class TestVehicleTracker:
    """Tests for VehicleTracker."""

    def test_empty_initially(self):
        tracker = VehicleTracker()
        assert tracker.unique_count == 0
        assert tracker.all_track_ids == []

    def test_update_adds_tracks(self, sample_detections):
        tracker = VehicleTracker()
        tracker.update(sample_detections, frame_number=0)
        assert tracker.unique_count == 3
        assert set(tracker.all_track_ids) == {1, 2, 3}

    def test_skips_none_track_id(self):
        tracker = VehicleTracker()
        det = Detection(class_name="car", confidence=0.9, x1=0, y1=0, x2=50, y2=50,
                        track_id=None)
        tracker.update([det], frame_number=0)
        assert tracker.unique_count == 0

    def test_vehicle_counts(self, sample_detections):
        tracker = VehicleTracker()
        tracker.update(sample_detections, frame_number=0)
        counts = tracker.get_vehicle_counts()
        assert counts["car"] == 1
        assert counts["motorcycle"] == 1
        assert counts["truck"] == 1

    def test_trajectory_accumulates(self):
        tracker = VehicleTracker()
        for i in range(5):
            det = Detection(class_name="car", confidence=0.9,
                            x1=i*10, y1=i*10, x2=i*10+50, y2=i*10+50,
                            track_id=1)
            tracker.update([det], frame_number=i)

        traj = tracker.get_trajectory(1)
        assert len(traj) == 5

    def test_trajectory_max_length(self):
        tracker = VehicleTracker(max_trajectory_length=3)
        for i in range(10):
            det = Detection(class_name="car", confidence=0.9,
                            x1=i, y1=i, x2=i+50, y2=i+50, track_id=1)
            tracker.update([det], frame_number=i)

        traj = tracker.get_trajectory(1)
        assert len(traj) == 3

    def test_reset(self, sample_detections):
        tracker = VehicleTracker()
        tracker.update(sample_detections, frame_number=0)
        assert tracker.unique_count > 0
        tracker.reset()
        assert tracker.unique_count == 0

    def test_get_displacement(self):
        tracker = VehicleTracker()
        d1 = Detection(class_name="car", confidence=0.9, x1=0, y1=0, x2=50, y2=50, track_id=1)
        d2 = Detection(class_name="car", confidence=0.9, x1=30, y1=40, x2=80, y2=90, track_id=1)
        tracker.update([d1], frame_number=0)
        tracker.update([d2], frame_number=1)
        disp = tracker.get_displacement(1)
        assert disp > 0

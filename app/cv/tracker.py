"""
Vehicle tracker — maintains persistent track IDs and trajectories.

Uses Ultralytics' built-in tracking (ByteTrack / BoTSORT) through the
``VehicleDetector.detect_with_tracking()`` method.  This module provides
a higher-level wrapper that:

  • Accumulates per-track trajectory (centre-point history).
  • Counts unique vehicles.
  • Computes per-track displacement between consecutive frames.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np

from app.cv.detector import Detection
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TrackState:
    """Accumulated state for a single tracked vehicle."""

    track_id: int
    class_name: str = ""
    trajectory: list[tuple[float, float]] = field(default_factory=list)
    last_frame: int = 0
    last_confidence: float = 0.0
    frames_seen: int = 0

    @property
    def last_center(self) -> tuple[float, float] | None:
        return self.trajectory[-1] if self.trajectory else None

    @property
    def displacement(self) -> float:
        """Pixel displacement between the two most recent positions."""
        if len(self.trajectory) < 2:
            return 0.0
        p1 = np.array(self.trajectory[-2])
        p2 = np.array(self.trajectory[-1])
        return float(np.linalg.norm(p2 - p1))


class VehicleTracker:
    """
    High-level tracker that consumes ``Detection`` lists (already
    containing ``track_id``) and maintains per-vehicle state.

    Usage::

        tracker = VehicleTracker()
        # Each frame:
        tracker.update(detections_with_track_ids, frame_number)
        print(tracker.unique_count)
        print(tracker.get_trajectory(track_id=5))
    """

    def __init__(self, max_trajectory_length: int = 60) -> None:
        """
        Args:
            max_trajectory_length: Keep at most this many recent
                centre-points per track to bound memory usage.
        """
        self._tracks: dict[int, TrackState] = {}
        self._max_traj = max_trajectory_length

    # ── Public API ───────────────────────────────────────────────────────

    def update(self, detections: list[Detection], frame_number: int = 0) -> None:
        """
        Ingest the tracked detections for the current frame.

        Detections without a ``track_id`` are silently skipped.
        """
        for det in detections:
            tid = det.track_id
            if tid is None:
                continue

            cx, cy = det.center
            if tid not in self._tracks:
                self._tracks[tid] = TrackState(track_id=tid, class_name=det.class_name)

            state = self._tracks[tid]
            state.trajectory.append((cx, cy))
            if len(state.trajectory) > self._max_traj:
                state.trajectory = state.trajectory[-self._max_traj:]
            state.last_frame = frame_number
            state.last_confidence = det.confidence
            state.class_name = det.class_name
            state.frames_seen += 1

    @property
    def unique_count(self) -> int:
        """Number of unique vehicles tracked so far."""
        return len(self._tracks)

    @property
    def all_track_ids(self) -> list[int]:
        return list(self._tracks.keys())

    def get_state(self, track_id: int) -> TrackState | None:
        return self._tracks.get(track_id)

    def get_trajectory(self, track_id: int) -> list[tuple[float, float]]:
        state = self._tracks.get(track_id)
        return state.trajectory if state else []

    def get_displacement(self, track_id: int) -> float:
        """Pixel displacement for the most recent step of *track_id*."""
        state = self._tracks.get(track_id)
        return state.displacement if state else 0.0

    def get_vehicle_counts(self) -> dict[str, int]:
        """Count unique vehicles by class name."""
        counts: dict[str, int] = defaultdict(int)
        for state in self._tracks.values():
            counts[state.class_name] += 1
        return dict(counts)

    def get_all_trajectories(self) -> dict[int, list[tuple[float, float]]]:
        """Return all trajectories keyed by track_id."""
        return {tid: s.trajectory for tid, s in self._tracks.items()}

    def reset(self) -> None:
        """Clear all tracking state."""
        self._tracks.clear()
        logger.debug("Tracker state reset")

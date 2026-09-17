"""
Abstract base class for violation rules.

Every violation rule inherits from ``BaseViolationRule`` and implements
the ``check()`` method.  This keeps the rule engine extensible — new
rules can be added without modifying existing code (Open/Closed Principle).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.cv.detector import Detection


@dataclass
class ViolationEvent:
    """Structured record of a single violation occurrence."""

    violation_type: str
    track_id: int | None
    vehicle_type: str
    confidence: float
    frame_number: int
    video_timestamp: str
    detection: Detection

    def to_dict(self) -> dict:
        return {
            "violation_type": self.violation_type,
            "track_id": self.track_id,
            "vehicle_type": self.vehicle_type,
            "confidence": round(self.confidence, 4),
            "frame_number": self.frame_number,
            "video_timestamp": self.video_timestamp,
        }


class BaseViolationRule(ABC):
    """
    Abstract base for all violation rules.

    Subclasses must implement ``check()`` which receives the current
    frame's detections and tracking state, and returns zero or more
    ``ViolationEvent`` objects.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this rule."""
        ...

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Whether this rule is currently active."""
        ...

    @abstractmethod
    def check(
        self,
        detections: list[Detection],
        track_displacements: dict[int, float],
        frame_number: int,
        video_timestamp: str,
        config: dict[str, Any],
    ) -> list[ViolationEvent]:
        """
        Evaluate the rule against the current frame's data.

        Args:
            detections: Tracked detections for the current frame.
            track_displacements: track_id → pixel displacement since last frame.
            frame_number: Absolute frame index.
            video_timestamp: Human-readable timestamp (e.g. ``"00:01:24"``).
            config: Mutable runtime configuration dict (signal state, thresholds, etc.).

        Returns:
            List of ``ViolationEvent`` objects (may be empty).
        """
        ...

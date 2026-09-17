"""
Speed / zone violation rule (prototype).

Estimates vehicle speed using pixel-level displacement between frames.

**IMPORTANT DISCLAIMER**:
  Pixel displacement does **NOT** represent accurate real-world speed.
  Accurate speed measurement requires:
    1. Camera calibration (intrinsic + extrinsic parameters).
    2. Perspective transformation (homography).
    3. Real-world reference measurements (known distances in the scene).

  This module is a **prototype** that demonstrates the concept of
  zone-based speed estimation in a controlled academic setting.
  It must NOT be presented as legally valid speed enforcement.

Implementation:
  1. A displacement threshold (pixels/frame) is configured.
  2. For each tracked vehicle, the pixel displacement between the
     current and previous frame position is computed.
  3. If the displacement exceeds the threshold, a
     ``SPEED_ZONE_VIOLATION`` event is generated.
"""

from __future__ import annotations

from typing import Any

from app.config.settings import get_settings
from app.cv.detector import Detection
from app.violations.base import BaseViolationRule, ViolationEvent
from app.utils.logger import get_logger

logger = get_logger(__name__)


class SpeedZoneRule(BaseViolationRule):
    """
    Detect vehicles exceeding a pixel-displacement threshold.

    This is a prototype speed estimation — see module docstring for
    accuracy limitations.
    """

    @property
    def name(self) -> str:
        return "Speed / Zone Violation (Prototype)"

    @property
    def enabled(self) -> bool:
        return get_settings().speed_zone_enabled

    def check(
        self,
        detections: list[Detection],
        track_displacements: dict[int, float],
        frame_number: int,
        video_timestamp: str,
        config: dict[str, Any],
    ) -> list[ViolationEvent]:
        if not self.enabled:
            return []

        threshold = config.get(
            "speed_zone_displacement_threshold",
            get_settings().speed_zone_displacement_threshold,
        )

        violations: list[ViolationEvent] = []

        for det in detections:
            tid = det.track_id
            if tid is None:
                continue

            displacement = track_displacements.get(tid, 0.0)

            if displacement > threshold:
                logger.info(
                    "SPEED_ZONE_VIOLATION: track=%d displacement=%.1fpx frame=%d",
                    tid, displacement, frame_number,
                )
                violations.append(
                    ViolationEvent(
                        violation_type="SPEED_ZONE_VIOLATION",
                        track_id=tid,
                        vehicle_type=det.class_name,
                        confidence=det.confidence,
                        frame_number=frame_number,
                        video_timestamp=video_timestamp,
                        detection=det,
                    )
                )

        return violations

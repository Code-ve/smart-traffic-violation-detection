"""
Red-light violation rule.

Detects when a tracked vehicle crosses a configurable virtual stop line
while the traffic signal state is RED.

Implementation:
  1. A horizontal stop line is defined by its Y-coordinate (``red_light_line_y``).
  2. The signal state is a runtime-configurable value (``signal_state``).
  3. For each tracked detection whose bounding-box bottom edge has moved
     past the stop line while the signal is RED, a ``RED_LIGHT_VIOLATION``
     event is generated.

Limitations:
  • The signal state is manually set / simulated — this module does NOT
    perform automatic traffic-light recognition.
  • A dedicated traffic-light detection model would be required for
    automatic signal-state determination.
"""

from __future__ import annotations

from typing import Any

from app.config.settings import get_settings
from app.cv.detector import Detection
from app.violations.base import BaseViolationRule, ViolationEvent
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RedLightRule(BaseViolationRule):
    """Detect vehicles crossing the stop line during a RED signal."""

    def __init__(self) -> None:
        self._prev_positions: dict[int, float] = {}  # track_id → previous bottom-y

    @property
    def name(self) -> str:
        return "Red Light Violation"

    @property
    def enabled(self) -> bool:
        return get_settings().red_light_enabled

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

        signal = config.get("signal_state", get_settings().signal_state).upper()
        line_y = config.get("red_light_line_y", get_settings().red_light_line_y)

        if signal != "RED":
            # Update positions even when green so we have history
            for det in detections:
                if det.track_id is not None:
                    self._prev_positions[det.track_id] = det.y2
            return []

        violations: list[ViolationEvent] = []

        for det in detections:
            tid = det.track_id
            if tid is None:
                continue

            bottom_y = det.y2
            prev_y = self._prev_positions.get(tid)

            # Vehicle's bottom was above the line and is now at/below it
            if prev_y is not None and prev_y < line_y <= bottom_y:
                logger.info(
                    "RED_LIGHT_VIOLATION: track=%d class=%s frame=%d",
                    tid, det.class_name, frame_number,
                )
                violations.append(
                    ViolationEvent(
                        violation_type="RED_LIGHT_VIOLATION",
                        track_id=tid,
                        vehicle_type=det.class_name,
                        confidence=det.confidence,
                        frame_number=frame_number,
                        video_timestamp=video_timestamp,
                        detection=det,
                    )
                )

            self._prev_positions[tid] = bottom_y

        return violations

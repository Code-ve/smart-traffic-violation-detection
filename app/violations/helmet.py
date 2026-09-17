"""
Helmet violation rule.

Detects riders (motorcycle / bicycle) without helmets.

**IMPORTANT**:
  The standard COCO-pretrained YOLO model does NOT contain helmet
  classes.  This rule will **auto-disable** if the loaded model does
  not support helmet detection.

  To enable this rule, provide a custom-trained model that includes
  classes such as ``helmet``, ``no_helmet``, or equivalent labels,
  and set ``HELMET_ENABLED=true`` in your ``.env`` file.

  This design keeps the base application fully functional without
  pretending that generic YOLO can detect helmets.
"""

from __future__ import annotations

from typing import Any

from app.config.settings import get_settings
from app.cv.detector import Detection
from app.violations.base import BaseViolationRule, ViolationEvent
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Classes that a custom helmet model might define
_HELMET_CLASSES = {"no_helmet", "no-helmet", "without_helmet", "without-helmet"}
_RIDER_CLASSES = {"motorcycle", "bicycle"}


class HelmetRule(BaseViolationRule):
    """
    Detect riders without helmets.

    Auto-disables when the loaded model does not have helmet classes.
    """

    def __init__(self) -> None:
        self._model_has_helmet_classes: bool | None = None

    @property
    def name(self) -> str:
        return "Helmet Violation"

    @property
    def enabled(self) -> bool:
        return get_settings().helmet_enabled

    def check_model_support(self, available_classes: dict[int, str]) -> bool:
        """
        Check whether the currently loaded model contains helmet-related
        classes.  Call this once after the model is loaded.
        """
        class_names = {v.lower() for v in available_classes.values()}
        self._model_has_helmet_classes = bool(class_names & _HELMET_CLASSES)
        if not self._model_has_helmet_classes:
            logger.warning(
                "Helmet rule: model does not contain helmet classes — rule auto-disabled. "
                "Available classes: %s",
                ", ".join(sorted(class_names)),
            )
        else:
            logger.info("Helmet rule: model supports helmet detection")
        return self._model_has_helmet_classes

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
        if self._model_has_helmet_classes is False:
            return []

        violations: list[ViolationEvent] = []

        for det in detections:
            if det.class_name.lower() in _HELMET_CLASSES:
                logger.info(
                    "HELMET_VIOLATION: track=%d frame=%d",
                    det.track_id or -1, frame_number,
                )
                violations.append(
                    ViolationEvent(
                        violation_type="HELMET_VIOLATION",
                        track_id=det.track_id,
                        vehicle_type=det.class_name,
                        confidence=det.confidence,
                        frame_number=frame_number,
                        video_timestamp=video_timestamp,
                        detection=det,
                    )
                )

        return violations

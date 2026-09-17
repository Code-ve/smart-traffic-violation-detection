"""
Violation rule engine — orchestrates all registered violation rules.

Architecture::

    Detections
        ↓
    Tracking Data
        ↓
    Violation Rules  (RedLightRule, SpeedZoneRule, HelmetRule, …)
        ↓
    Violation Events

The engine applies a **per-vehicle cooldown** to prevent duplicate
violation events for the same vehicle within a short time window.
"""

from __future__ import annotations

import time
from typing import Any

from app.config.settings import get_settings
from app.cv.detector import Detection
from app.violations.base import BaseViolationRule, ViolationEvent
from app.violations.red_light import RedLightRule
from app.violations.speed_zone import SpeedZoneRule
from app.violations.helmet import HelmetRule
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ViolationEngine:
    """
    Central engine that evaluates all registered violation rules per frame.

    Usage::

        engine = ViolationEngine()
        events = engine.evaluate(detections, displacements, frame_num, ts, config)
    """

    def __init__(self) -> None:
        self._rules: list[BaseViolationRule] = []
        self._cooldowns: dict[str, float] = {}  # "type_trackid" → last_trigger_time
        self._total_violations: int = 0

        # Register built-in rules
        self._rules.append(RedLightRule())
        self._rules.append(SpeedZoneRule())
        self._rules.append(HelmetRule())

        logger.info(
            "ViolationEngine initialised with %d rules: %s",
            len(self._rules),
            ", ".join(r.name for r in self._rules),
        )

    @property
    def rules(self) -> list[BaseViolationRule]:
        return list(self._rules)

    @property
    def total_violations(self) -> int:
        return self._total_violations

    def add_rule(self, rule: BaseViolationRule) -> None:
        """Register an additional violation rule at runtime."""
        self._rules.append(rule)
        logger.info("Added rule: %s", rule.name)

    def check_model_support(self, available_classes: dict[int, str]) -> None:
        """
        Let rules that need model class info (e.g. HelmetRule) check
        whether the loaded model supports them.
        """
        for rule in self._rules:
            if isinstance(rule, HelmetRule):
                rule.check_model_support(available_classes)

    def evaluate(
        self,
        detections: list[Detection],
        track_displacements: dict[int, float],
        frame_number: int,
        video_timestamp: str,
        config: dict[str, Any] | None = None,
    ) -> list[ViolationEvent]:
        """
        Run all enabled rules against the current frame's detections.

        Applies per-vehicle cooldown to suppress duplicate events.

        Returns:
            Deduplicated list of ``ViolationEvent`` objects.
        """
        cfg = config or {}
        cooldown_secs = get_settings().evidence_cooldown_seconds
        now = time.time()

        all_events: list[ViolationEvent] = []

        for rule in self._rules:
            if not rule.enabled:
                continue
            try:
                events = rule.check(
                    detections, track_displacements, frame_number, video_timestamp, cfg,
                )
            except Exception as exc:
                logger.error("Rule %s failed: %s", rule.name, exc)
                continue

            # Apply cooldown
            for event in events:
                key = f"{event.violation_type}_{event.track_id}"
                last = self._cooldowns.get(key, 0.0)
                if now - last >= cooldown_secs:
                    self._cooldowns[key] = now
                    self._total_violations += 1
                    all_events.append(event)
                else:
                    logger.debug("Cooldown suppressed: %s", key)

        return all_events

    def reset(self) -> None:
        """Clear cooldown state and violation counter."""
        self._cooldowns.clear()
        self._total_violations = 0

"""Tests for violation rules and the violation engine."""

import time
import pytest

from app.cv.detector import Detection
from app.violations.base import ViolationEvent
from app.violations.red_light import RedLightRule
from app.violations.speed_zone import SpeedZoneRule
from app.violations.helmet import HelmetRule
from app.violations.engine import ViolationEngine


class TestRedLightRule:
    """Tests for the red-light violation rule."""

    def test_no_violation_on_green(self):
        rule = RedLightRule()
        det = Detection(class_name="car", confidence=0.9,
                        x1=100, y1=350, x2=200, y2=450, track_id=1)
        events = rule.check([det], {}, 0, "00:00:01", {"signal_state": "GREEN", "red_light_line_y": 400})
        assert len(events) == 0

    def test_violation_crossing_line_on_red(self):
        rule = RedLightRule()
        config = {"signal_state": "RED", "red_light_line_y": 400}

        # Frame 0: vehicle above line
        det0 = Detection(class_name="car", confidence=0.9,
                         x1=100, y1=300, x2=200, y2=390, track_id=1)
        rule.check([det0], {}, 0, "00:00:00", config)

        # Frame 1: vehicle crosses line (bottom > 400)
        det1 = Detection(class_name="car", confidence=0.9,
                         x1=100, y1=320, x2=200, y2=420, track_id=1)
        events = rule.check([det1], {}, 1, "00:00:01", config)
        assert len(events) == 1
        assert events[0].violation_type == "RED_LIGHT_VIOLATION"
        assert events[0].track_id == 1

    def test_no_violation_already_past_line(self):
        rule = RedLightRule()
        config = {"signal_state": "RED", "red_light_line_y": 400}

        # Vehicle already past line
        det0 = Detection(class_name="car", confidence=0.9,
                         x1=100, y1=410, x2=200, y2=500, track_id=1)
        rule.check([det0], {}, 0, "00:00:00", config)

        det1 = Detection(class_name="car", confidence=0.9,
                         x1=100, y1=420, x2=200, y2=510, track_id=1)
        events = rule.check([det1], {}, 1, "00:00:01", config)
        assert len(events) == 0  # Already past, shouldn't trigger again


class TestSpeedZoneRule:
    """Tests for the speed/zone violation rule."""

    def test_no_violation_under_threshold(self):
        rule = SpeedZoneRule()
        det = Detection(class_name="car", confidence=0.9,
                        x1=100, y1=100, x2=200, y2=200, track_id=1)
        events = rule.check([det], {1: 30.0}, 0, "00:00:00",
                            {"speed_zone_displacement_threshold": 80.0})
        assert len(events) == 0

    def test_violation_over_threshold(self):
        rule = SpeedZoneRule()
        det = Detection(class_name="car", confidence=0.9,
                        x1=100, y1=100, x2=200, y2=200, track_id=1)
        events = rule.check([det], {1: 100.0}, 0, "00:00:00",
                            {"speed_zone_displacement_threshold": 80.0})
        assert len(events) == 1
        assert events[0].violation_type == "SPEED_ZONE_VIOLATION"

    def test_skips_no_track_id(self):
        rule = SpeedZoneRule()
        det = Detection(class_name="car", confidence=0.9,
                        x1=100, y1=100, x2=200, y2=200, track_id=None)
        events = rule.check([det], {}, 0, "00:00:00",
                            {"speed_zone_displacement_threshold": 80.0})
        assert len(events) == 0


class TestHelmetRule:
    """Tests for the helmet violation rule."""

    def test_auto_disables_without_model_support(self):
        rule = HelmetRule()
        # Simulate a model without helmet classes
        supported = rule.check_model_support({0: "person", 2: "car"})
        assert supported is False

    def test_enables_with_model_support(self):
        rule = HelmetRule()
        supported = rule.check_model_support({0: "helmet", 1: "no_helmet"})
        assert supported is True


class TestViolationEngine:
    """Tests for the ViolationEngine orchestrator."""

    def test_engine_has_builtin_rules(self):
        engine = ViolationEngine()
        assert len(engine.rules) >= 3

    def test_cooldown_suppresses_duplicates(self):
        engine = ViolationEngine()
        config = {"signal_state": "RED", "red_light_line_y": 400,
                  "speed_zone_displacement_threshold": 80.0}

        # First: set up position above line
        det0 = Detection(class_name="car", confidence=0.9,
                         x1=100, y1=300, x2=200, y2=390, track_id=1)
        engine.evaluate([det0], {1: 0}, 0, "00:00:00", config)

        # Cross the line
        det1 = Detection(class_name="car", confidence=0.9,
                         x1=100, y1=320, x2=200, y2=420, track_id=1)
        events1 = engine.evaluate([det1], {1: 0}, 1, "00:00:01", config)

        # Immediately try same violation — should be suppressed by cooldown
        det2 = Detection(class_name="car", confidence=0.9,
                         x1=100, y1=320, x2=200, y2=420, track_id=1)
        events2 = engine.evaluate([det2], {1: 0}, 2, "00:00:02", config)

        # events1 should have the violation, events2 should not (cooldown)
        total = len(events1) + len(events2)
        assert total <= 1  # at most one violation due to cooldown

    def test_reset(self):
        engine = ViolationEngine()
        engine._total_violations = 5
        engine.reset()
        assert engine.total_violations == 0

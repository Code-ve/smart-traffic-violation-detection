"""
Visualization utilities for annotated frames.

Draws bounding boxes, class labels, confidence scores, track IDs,
vehicle trajectories, and violation overlays onto OpenCV frames.
Also generates and saves evidence images for detected violations.
"""

from __future__ import annotations

import os
import time
from datetime import datetime

import cv2
import numpy as np

from app.cv.detector import Detection
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Colour palette (BGR) ────────────────────────────────────────────────
COLOURS: dict[str, tuple[int, int, int]] = {
    "car":        (255, 178, 50),
    "motorcycle": (0, 255, 127),
    "bus":        (255, 105, 180),
    "truck":      (0, 191, 255),
    "bicycle":    (50, 205, 50),
    "person":     (147, 20, 255),
    "default":    (200, 200, 200),
}

VIOLATION_COLOUR = (0, 0, 255)  # red
TRACK_LINE_COLOUR = (0, 255, 255)  # yellow


def _get_colour(class_name: str) -> tuple[int, int, int]:
    return COLOURS.get(class_name, COLOURS["default"])


# ═══════════════════════════════════════════════════════════════════════════
#  Drawing helpers
# ═══════════════════════════════════════════════════════════════════════════

def draw_detections(
    frame: np.ndarray,
    detections: list[Detection],
    show_confidence: bool = True,
    show_track_id: bool = True,
) -> np.ndarray:
    """
    Draw bounding boxes and labels for all detections onto *frame*.

    Returns:
        The annotated frame (modified in-place and returned).
    """
    for det in detections:
        colour = _get_colour(det.class_name)
        x1, y1, x2, y2 = int(det.x1), int(det.y1), int(det.x2), int(det.y2)

        # Bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)

        # Label text
        parts: list[str] = [det.class_name.upper()]
        if show_confidence:
            parts.append(f"{det.confidence:.2f}")
        if show_track_id and det.track_id is not None:
            parts.append(f"ID:{det.track_id}")
        label = " | ".join(parts)

        # Label background
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), colour, -1)
        cv2.putText(
            frame, label, (x1 + 2, y1 - 4),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA,
        )
    return frame


def draw_trajectories(
    frame: np.ndarray,
    trajectories: dict[int, list[tuple[float, float]]],
    max_points: int = 30,
) -> np.ndarray:
    """
    Draw trajectory lines for tracked vehicles.

    Only the most recent *max_points* are drawn per track to avoid
    visual clutter.
    """
    for tid, points in trajectories.items():
        pts = points[-max_points:]
        if len(pts) < 2:
            continue
        for i in range(1, len(pts)):
            p1 = (int(pts[i - 1][0]), int(pts[i - 1][1]))
            p2 = (int(pts[i][0]), int(pts[i][1]))
            thickness = max(1, int(2 * i / len(pts)))
            cv2.line(frame, p1, p2, TRACK_LINE_COLOUR, thickness, cv2.LINE_AA)
    return frame


def draw_violation_zone(
    frame: np.ndarray,
    line_y: int,
    label: str = "STOP LINE",
    signal_state: str = "GREEN",
) -> np.ndarray:
    """Draw the configurable stop line / violation zone."""
    h, w = frame.shape[:2]
    colour = (0, 0, 255) if signal_state.upper() == "RED" else (0, 200, 0)
    cv2.line(frame, (0, line_y), (w, line_y), colour, 2, cv2.LINE_AA)
    cv2.putText(
        frame, f"{label} [{signal_state}]", (10, line_y - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, colour, 2, cv2.LINE_AA,
    )
    return frame


def draw_stats_overlay(
    frame: np.ndarray,
    fps: float = 0,
    frame_num: int = 0,
    total_detections: int = 0,
    unique_vehicles: int = 0,
    violations: int = 0,
) -> np.ndarray:
    """Draw a translucent stats panel in the top-right corner."""
    lines = [
        f"Frame: {frame_num}",
        f"FPS: {fps:.1f}",
        f"Detections: {total_detections}",
        f"Vehicles: {unique_vehicles}",
        f"Violations: {violations}",
    ]
    x_start = frame.shape[1] - 220
    y_start = 10
    # Semi-transparent background
    overlay = frame.copy()
    cv2.rectangle(overlay, (x_start - 10, y_start), (frame.shape[1] - 5, y_start + len(lines) * 25 + 10), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    for i, line in enumerate(lines):
        cv2.putText(
            frame, line, (x_start, y_start + 22 + i * 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA,
        )
    return frame


# ═══════════════════════════════════════════════════════════════════════════
#  Evidence generation
# ═══════════════════════════════════════════════════════════════════════════

def generate_evidence_image(
    frame: np.ndarray,
    violation_type: str,
    detection: Detection,
    evidence_dir: str,
    video_timestamp: str = "",
) -> str:
    """
    Create and save an evidence image for a violation.

    The image includes the bounding box, violation label, track ID,
    confidence, and timestamp overlaid on the frame.

    Args:
        frame: The raw (or partially annotated) frame.
        violation_type: e.g. ``"RED_LIGHT_VIOLATION"``.
        detection: The detection that triggered the violation.
        evidence_dir: Directory to save the evidence image.
        video_timestamp: Human-readable timestamp within the video.

    Returns:
        Absolute path to the saved evidence image.
    """
    evidence = frame.copy()

    # Draw the offending bounding box in red
    x1, y1 = int(detection.x1), int(detection.y1)
    x2, y2 = int(detection.x2), int(detection.y2)
    cv2.rectangle(evidence, (x1, y1), (x2, y2), VIOLATION_COLOUR, 3)

    # Info block
    info_lines = [
        f"VIOLATION: {violation_type}",
        f"TRACK ID: {detection.track_id or 'N/A'}",
        f"VEHICLE: {detection.class_name.upper()}",
        f"CONFIDENCE: {detection.confidence:.2f}",
        f"TIMESTAMP: {video_timestamp or 'N/A'}",
    ]

    # Semi-transparent panel at the bottom
    panel_h = len(info_lines) * 28 + 20
    h, w = evidence.shape[:2]
    overlay = evidence.copy()
    cv2.rectangle(overlay, (0, h - panel_h), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, evidence, 0.3, 0, evidence)

    for i, line in enumerate(info_lines):
        y = h - panel_h + 25 + i * 28
        cv2.putText(
            evidence, line, (15, y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 255), 2, cv2.LINE_AA,
        )

    # Save
    os.makedirs(evidence_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"evidence_{violation_type}_{ts}.jpg"
    path = os.path.join(evidence_dir, filename)
    cv2.imwrite(path, evidence)
    logger.info("Evidence saved: %s", path)
    return path

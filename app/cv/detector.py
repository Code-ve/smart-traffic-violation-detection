"""
YOLO-based vehicle and object detector.

Wraps the Ultralytics YOLO model to provide a clean detection interface
returning structured ``Detection`` objects.  The module is model-version
agnostic — any YOLO model (v5, v8, v11, etc.) supported by Ultralytics
can be used by configuring ``MODEL_PATH``.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from app.config.settings import get_settings
from app.utils.exceptions import ModelNotFoundError, ProcessingError
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Traffic-relevant COCO classes (name → COCO id)
TRAFFIC_CLASSES: dict[str, int] = {
    "person": 0,
    "bicycle": 1,
    "car": 2,
    "motorcycle": 3,
    "bus": 5,
    "truck": 7,
}


@dataclass
class Detection:
    """Structured representation of a single object detection."""

    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    frame_number: int = 0
    timestamp: str = ""
    track_id: int | None = None

    @property
    def center(self) -> tuple[float, float]:
        """Return the centre point of the bounding box."""
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary."""
        return {
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "x1": round(self.x1, 1),
            "y1": round(self.y1, 1),
            "x2": round(self.x2, 1),
            "y2": round(self.y2, 1),
            "frame_number": self.frame_number,
            "timestamp": self.timestamp,
            "track_id": self.track_id,
        }


class VehicleDetector:
    """
    YOLO-based object detector focused on traffic-relevant classes.

    Usage::

        detector = VehicleDetector()
        detector.load_model("models/yolov8n.pt")
        detections = detector.detect(frame)
    """

    def __init__(self) -> None:
        self._model = None
        self._model_path: str = ""
        self._model_name: str = ""
        self._available_classes: dict[int, str] = {}
        self._traffic_class_ids: list[int] = []
        self._last_inference_ms: float = 0.0

    # ── Model loading ────────────────────────────────────────────────────

    def load_model(self, model_path: str | None = None) -> None:
        """
        Load a YOLO model from disk.

        If *model_path* is ``None`` the path from application settings is used.
        If the file does not exist, Ultralytics will attempt to download a
        pretrained model automatically (for standard model names like
        ``yolov8n.pt``).

        Raises:
            ModelNotFoundError: If the model cannot be loaded.
        """
        from ultralytics import YOLO

        path = model_path or get_settings().model_path
        self._model_path = path
        self._model_name = Path(path).stem

        try:
            logger.info("Loading YOLO model: %s", path)
            self._model = YOLO(path)

            # Discover available class names
            self._available_classes = self._model.names  # type: ignore[assignment]
            self._traffic_class_ids = [
                cid for cid, name in self._available_classes.items()
                if name in TRAFFIC_CLASSES
            ]
            logger.info(
                "Model loaded — %d total classes, %d traffic-relevant",
                len(self._available_classes),
                len(self._traffic_class_ids),
            )
        except Exception as exc:
            logger.error("Failed to load model %s: %s", path, exc)
            raise ModelNotFoundError(path) from exc

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def available_classes(self) -> dict[int, str]:
        return dict(self._available_classes)

    @property
    def last_inference_ms(self) -> float:
        return self._last_inference_ms

    # ── Detection ────────────────────────────────────────────────────────

    def detect(
        self,
        frame: np.ndarray,
        confidence: float | None = None,
        iou: float | None = None,
        frame_number: int = 0,
        timestamp: str = "",
    ) -> list[Detection]:
        """
        Run inference on a single frame.

        Args:
            frame: BGR image as a NumPy array.
            confidence: Override the default confidence threshold.
            iou: Override the default IoU threshold.
            frame_number: Frame index (for metadata).
            timestamp: Human-readable timestamp string.

        Returns:
            List of ``Detection`` objects for traffic-relevant classes.

        Raises:
            ProcessingError: If the model is not loaded.
        """
        if self._model is None:
            raise ProcessingError("Model not loaded. Call load_model() first.")

        settings = get_settings()
        conf = confidence if confidence is not None else settings.confidence_threshold
        iou_thresh = iou if iou is not None else settings.iou_threshold

        t0 = time.perf_counter()
        results = self._model(
            frame,
            conf=conf,
            iou=iou_thresh,
            classes=self._traffic_class_ids or None,
            verbose=False,
        )
        self._last_inference_ms = (time.perf_counter() - t0) * 1000

        detections: list[Detection] = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = self._available_classes.get(cls_id, f"class_{cls_id}")
                conf_val = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(
                    Detection(
                        class_name=cls_name,
                        confidence=conf_val,
                        x1=x1, y1=y1, x2=x2, y2=y2,
                        frame_number=frame_number,
                        timestamp=timestamp,
                    )
                )

        return detections

    def detect_with_tracking(
        self,
        frame: np.ndarray,
        confidence: float | None = None,
        iou: float | None = None,
        frame_number: int = 0,
        timestamp: str = "",
        tracker: str | None = None,
        persist: bool = True,
    ) -> list[Detection]:
        """
        Run detection **with** built-in YOLO tracking (ByteTrack / BoTSORT).

        Returns ``Detection`` objects that include a ``track_id``.
        """
        if self._model is None:
            raise ProcessingError("Model not loaded. Call load_model() first.")

        settings = get_settings()
        conf = confidence if confidence is not None else settings.confidence_threshold
        iou_thresh = iou if iou is not None else settings.iou_threshold
        trk = tracker or settings.tracker_type

        # Build tracker config name expected by Ultralytics
        tracker_cfg = f"{trk}.yaml"

        t0 = time.perf_counter()
        results = self._model.track(
            frame,
            conf=conf,
            iou=iou_thresh,
            classes=self._traffic_class_ids or None,
            tracker=tracker_cfg,
            persist=persist,
            verbose=False,
        )
        self._last_inference_ms = (time.perf_counter() - t0) * 1000

        detections: list[Detection] = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                cls_id = int(box.cls[0])
                cls_name = self._available_classes.get(cls_id, f"class_{cls_id}")
                conf_val = float(box.conf[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                track_id = int(box.id[0]) if box.id is not None else None
                detections.append(
                    Detection(
                        class_name=cls_name,
                        confidence=conf_val,
                        x1=x1, y1=y1, x2=x2, y2=y2,
                        frame_number=frame_number,
                        timestamp=timestamp,
                        track_id=track_id,
                    )
                )

        return detections

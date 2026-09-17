"""
End-to-end video and image processing pipeline.

Orchestrates the full Computer Vision workflow:

    Input → Preprocessing → Detection → Tracking → Violation Analysis
        → Evidence Generation → Database Storage → Output

This is the central module that ties all CV components together.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

import cv2
import numpy as np

from app.config.settings import get_settings, ensure_directories
from app.cv.detector import Detection, VehicleDetector
from app.cv.tracker import VehicleTracker
from app.cv.preprocessing import PreprocessingPipeline, PreprocessConfig
from app.cv.visualization import (
    draw_detections,
    draw_trajectories,
    draw_violation_zone,
    draw_stats_overlay,
    generate_evidence_image,
)
from app.violations.engine import ViolationEngine
from app.database import repository as repo
from app.utils.exceptions import (
    InvalidImageError,
    InvalidVideoError,
    ProcessingError,
    CameraUnavailableError,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessingResult:
    """Summary of a completed processing session."""

    session_id: str
    filename: str
    file_type: str
    total_frames: int = 0
    processed_frames: int = 0
    total_detections: int = 0
    unique_vehicles: int = 0
    total_violations: int = 0
    avg_fps: float = 0.0
    avg_inference_ms: float = 0.0
    output_path: str = ""
    duration_seconds: float = 0.0
    detections: list[dict] = field(default_factory=list)
    violations: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "total_frames": self.total_frames,
            "processed_frames": self.processed_frames,
            "total_detections": self.total_detections,
            "unique_vehicles": self.unique_vehicles,
            "total_violations": self.total_violations,
            "avg_fps": round(self.avg_fps, 2),
            "avg_inference_ms": round(self.avg_inference_ms, 2),
            "output_path": self.output_path,
            "duration_seconds": round(self.duration_seconds, 2),
        }


# ── Shared state for the current processing session ──────────────────────
_current_progress: dict[str, Any] = {}


def get_processing_progress(session_id: str) -> dict:
    """Return the live progress for a running processing session."""
    return _current_progress.get(session_id, {})


class VideoProcessor:
    """
    Main processing pipeline for images and videos.

    Usage::

        processor = VideoProcessor()
        result = processor.process_image("photo.jpg")
        result = processor.process_video("traffic.mp4")
    """

    def __init__(self) -> None:
        self._detector = VehicleDetector()
        self._tracker = VehicleTracker()
        self._engine = ViolationEngine()
        self._pipeline = PreprocessingPipeline()
        self._settings = get_settings()
        self._runtime_config: dict[str, Any] = {
            "signal_state": self._settings.signal_state,
            "red_light_line_y": self._settings.red_light_line_y,
            "speed_zone_displacement_threshold": self._settings.speed_zone_displacement_threshold,
        }

    # ── Configuration ────────────────────────────────────────────────────

    def update_config(self, **kwargs: Any) -> None:
        """Update runtime configuration (signal state, thresholds, etc.)."""
        self._runtime_config.update(kwargs)
        logger.info("Runtime config updated: %s", kwargs)

    def load_model(self, model_path: str | None = None) -> None:
        """Load the YOLO model and inform the violation engine."""
        self._detector.load_model(model_path)
        self._engine.check_model_support(self._detector.available_classes)

    @property
    def is_model_loaded(self) -> bool:
        return self._detector.is_loaded

    # ── Image processing ─────────────────────────────────────────────────

    def process_image(self, image_path: str) -> ProcessingResult:
        """
        Detect objects in a single image.

        Returns:
            ``ProcessingResult`` with detections (no tracking / violations
            for single images).
        """
        if not self._detector.is_loaded:
            self.load_model()

        frame = cv2.imread(image_path)
        if frame is None:
            raise InvalidImageError(image_path)

        filename = os.path.basename(image_path)
        session_id = repo.create_session(
            filename=filename, file_type="image", model_used=self._detector.model_name,
        )

        # Preprocess
        processed = self._pipeline.process(frame)

        # Detect
        t0 = time.perf_counter()
        detections = self._detector.detect(processed, frame_number=0)
        inference_ms = (time.perf_counter() - t0) * 1000

        # Save detections to DB
        det_dicts = [d.to_dict() for d in detections]
        repo.create_detections_bulk(session_id, det_dicts)

        # Draw annotations on the original frame
        annotated = draw_detections(frame.copy(), detections)

        # Save annotated image
        ensure_directories()
        out_name = f"annotated_{os.path.splitext(filename)[0]}.jpg"
        out_path = os.path.join(self._settings.output_dir, out_name)
        cv2.imwrite(out_path, annotated)

        # Update session
        repo.update_session(
            session_id,
            status="completed",
            completed_at=datetime.now().isoformat(),
            total_frames=1,
            processed_frames=1,
            total_vehicles=len(detections),
            unique_vehicles=len(detections),
            avg_inference_ms=round(inference_ms, 2),
            output_path=out_path,
        )

        result = ProcessingResult(
            session_id=session_id,
            filename=filename,
            file_type="image",
            total_frames=1,
            processed_frames=1,
            total_detections=len(detections),
            unique_vehicles=len(detections),
            avg_fps=round(1000 / inference_ms, 2) if inference_ms > 0 else 0,
            avg_inference_ms=round(inference_ms, 2),
            output_path=out_path,
            detections=det_dicts,
        )
        logger.info("Image processed: %d detections", len(detections))
        return result

    # ── Video processing ─────────────────────────────────────────────────

    def process_video(
        self,
        video_path: str,
        progress_callback: Callable[[dict], None] | None = None,
    ) -> ProcessingResult:
        """
        Process a video end-to-end: detection, tracking, violations,
        evidence, and annotated output.

        Args:
            video_path: Path to the input video.
            progress_callback: Optional callable receiving progress dicts.

        Returns:
            ``ProcessingResult`` with full session summary.
        """
        if not self._detector.is_loaded:
            self.load_model()

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise InvalidVideoError(video_path)

        filename = os.path.basename(video_path)
        session_id = repo.create_session(
            filename=filename, file_type="video", model_used=self._detector.model_name,
        )

        # Video properties
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps_in = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Output video
        ensure_directories()
        out_name = f"processed_{os.path.splitext(filename)[0]}.mp4"
        out_path = os.path.join(self._settings.output_dir, out_name)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out_writer = cv2.VideoWriter(out_path, fourcc, fps_in, (width, height))

        self._tracker.reset()
        self._engine.reset()

        frame_skip = self._settings.frame_skip
        frame_idx = 0
        processed_count = 0
        total_detections = 0
        inference_times: list[float] = []
        all_violations: list[dict] = []
        detection_buffer: list[dict] = []
        start_time = time.time()
        last_detections: list[Detection] = []

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                video_ts = self._frame_to_timestamp(frame_idx, fps_in)

                if frame_idx % frame_skip == 0:
                    # Preprocess
                    processed = self._pipeline.process(frame)

                    # Detect + track
                    detections = self._detector.detect_with_tracking(
                        processed,
                        frame_number=frame_idx,
                        timestamp=video_ts,
                    )
                    last_detections = detections
                    processed_count += 1
                    total_detections += len(detections)
                    inference_times.append(self._detector.last_inference_ms)

                    # Update tracker state
                    self._tracker.update(detections, frame_idx)

                    # Compute displacements
                    displacements = {
                        d.track_id: self._tracker.get_displacement(d.track_id)
                        for d in detections if d.track_id is not None
                    }

                    # Evaluate violations
                    violations = self._engine.evaluate(
                        detections, displacements, frame_idx, video_ts, self._runtime_config,
                    )

                    # Handle violation events
                    for v in violations:
                        evidence_path = generate_evidence_image(
                            frame, v.violation_type, v.detection,
                            self._settings.evidence_dir, video_ts,
                        )
                        repo.create_violation(
                            session_id=session_id,
                            violation_type=v.violation_type,
                            track_id=v.track_id,
                            vehicle_type=v.vehicle_type,
                            confidence=v.confidence,
                            frame_number=v.frame_number,
                            video_timestamp=v.video_timestamp,
                            evidence_path=evidence_path,
                        )
                        all_violations.append(v.to_dict())

                    # Buffer detections (sample every 5th processed frame to control DB size)
                    if processed_count % 5 == 0:
                        detection_buffer.extend(d.to_dict() for d in detections)
                        if len(detection_buffer) >= 200:
                            repo.create_detections_bulk(session_id, detection_buffer)
                            detection_buffer.clear()

                # Annotate frame (use last detections even on skipped frames)
                annotated = frame.copy()
                annotated = draw_detections(annotated, last_detections)
                annotated = draw_trajectories(annotated, self._tracker.get_all_trajectories())
                annotated = draw_violation_zone(
                    annotated,
                    self._runtime_config.get("red_light_line_y", self._settings.red_light_line_y),
                    signal_state=self._runtime_config.get("signal_state", self._settings.signal_state),
                )

                elapsed = time.time() - start_time
                current_fps = processed_count / elapsed if elapsed > 0 else 0
                annotated = draw_stats_overlay(
                    annotated,
                    fps=current_fps,
                    frame_num=frame_idx,
                    total_detections=total_detections,
                    unique_vehicles=self._tracker.unique_count,
                    violations=self._engine.total_violations,
                )

                out_writer.write(annotated)

                # Progress reporting
                progress = {
                    "session_id": session_id,
                    "frame": frame_idx,
                    "total_frames": total_frames,
                    "processed": processed_count,
                    "detections": total_detections,
                    "unique_vehicles": self._tracker.unique_count,
                    "violations": self._engine.total_violations,
                    "fps": round(current_fps, 1),
                    "percent": round(frame_idx / max(total_frames, 1) * 100, 1),
                }
                _current_progress[session_id] = progress
                if progress_callback:
                    progress_callback(progress)

                frame_idx += 1

        finally:
            cap.release()
            out_writer.release()

        # Flush remaining detection buffer
        if detection_buffer:
            repo.create_detections_bulk(session_id, detection_buffer)

        elapsed = time.time() - start_time
        avg_inf = sum(inference_times) / len(inference_times) if inference_times else 0
        avg_fps = processed_count / elapsed if elapsed > 0 else 0

        # Update session
        repo.update_session(
            session_id,
            status="completed",
            completed_at=datetime.now().isoformat(),
            total_frames=frame_idx,
            processed_frames=processed_count,
            total_vehicles=total_detections,
            unique_vehicles=self._tracker.unique_count,
            total_violations=self._engine.total_violations,
            avg_fps=round(avg_fps, 2),
            avg_inference_ms=round(avg_inf, 2),
            output_path=out_path,
        )

        # Clean up progress
        _current_progress.pop(session_id, None)

        result = ProcessingResult(
            session_id=session_id,
            filename=filename,
            file_type="video",
            total_frames=frame_idx,
            processed_frames=processed_count,
            total_detections=total_detections,
            unique_vehicles=self._tracker.unique_count,
            total_violations=self._engine.total_violations,
            avg_fps=round(avg_fps, 2),
            avg_inference_ms=round(avg_inf, 2),
            output_path=out_path,
            duration_seconds=round(elapsed, 2),
            violations=all_violations,
        )
        logger.info(
            "Video processed: %d frames, %d detections, %d vehicles, %d violations in %.1fs",
            frame_idx, total_detections, self._tracker.unique_count,
            self._engine.total_violations, elapsed,
        )
        return result

    # ── Webcam (optional) ────────────────────────────────────────────────

    def process_webcam_frame(self, frame: np.ndarray, frame_number: int = 0) -> tuple[np.ndarray, list[Detection]]:
        """
        Process a single webcam frame: detect + track + annotate.

        Returns:
            Tuple of (annotated_frame, detections).
        """
        if not self._detector.is_loaded:
            self.load_model()

        processed = self._pipeline.process(frame)
        detections = self._detector.detect_with_tracking(
            processed, frame_number=frame_number,
        )
        self._tracker.update(detections, frame_number)

        annotated = frame.copy()
        annotated = draw_detections(annotated, detections)
        annotated = draw_trajectories(annotated, self._tracker.get_all_trajectories())
        return annotated, detections

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _frame_to_timestamp(frame_idx: int, fps: float) -> str:
        """Convert a frame index to ``HH:MM:SS`` format."""
        total_seconds = int(frame_idx / fps) if fps > 0 else 0
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

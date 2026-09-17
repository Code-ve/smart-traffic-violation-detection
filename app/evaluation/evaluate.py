"""
Model evaluation module.

Provides two evaluation capabilities:

1. **Dataset evaluation**: Computes mAP, precision, and recall using
   Ultralytics' built-in ``model.val()`` method on a labelled dataset.

2. **Inference benchmarking**: Measures average inference time and FPS
   on a set of sample images.

If no labelled dataset is provided, evaluation results are explicitly
marked as "Evaluation pending dataset/model execution" rather than
fabricating numbers.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.cv.detector import VehicleDetector
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ModelEvaluator:
    """
    Evaluate a YOLO model's accuracy and inference performance.

    Usage::

        evaluator = ModelEvaluator()
        metrics = evaluator.evaluate_model("models/yolov8n.pt", "data/val")
        bench = evaluator.benchmark_inference("models/yolov8n.pt", ["img1.jpg"])
    """

    def evaluate_model(
        self,
        model_path: str,
        dataset_yaml: str | None = None,
    ) -> dict[str, Any]:
        """
        Run YOLO validation on a labelled dataset.

        Args:
            model_path: Path to the YOLO model weights.
            dataset_yaml: Path to a YOLO-format dataset YAML file.
                If None, returns a placeholder result.

        Returns:
            Dictionary with precision, recall, mAP@0.5, mAP@0.5:0.95.
        """
        if not dataset_yaml or not os.path.exists(dataset_yaml):
            logger.warning("No dataset YAML provided — evaluation skipped")
            return {
                "status": "pending",
                "message": "Evaluation pending dataset/model execution. "
                           "Provide a YOLO-format dataset YAML to run evaluation.",
                "model": os.path.basename(model_path),
                "precision": None,
                "recall": None,
                "mAP50": None,
                "mAP50_95": None,
            }

        try:
            from ultralytics import YOLO

            logger.info("Running model evaluation: %s on %s", model_path, dataset_yaml)
            model = YOLO(model_path)
            results = model.val(data=dataset_yaml, verbose=False)

            metrics = {
                "status": "completed",
                "model": os.path.basename(model_path),
                "precision": round(float(results.results_dict.get("metrics/precision(B)", 0)), 4),
                "recall": round(float(results.results_dict.get("metrics/recall(B)", 0)), 4),
                "mAP50": round(float(results.results_dict.get("metrics/mAP50(B)", 0)), 4),
                "mAP50_95": round(float(results.results_dict.get("metrics/mAP50-95(B)", 0)), 4),
            }
            logger.info("Evaluation complete: %s", metrics)
            return metrics

        except Exception as exc:
            logger.error("Evaluation failed: %s", exc)
            return {
                "status": "error",
                "message": str(exc),
                "model": os.path.basename(model_path),
            }

    def benchmark_inference(
        self,
        model_path: str,
        image_paths: list[str] | None = None,
        num_synthetic: int = 10,
        resolution: tuple[int, int] = (640, 480),
    ) -> dict[str, Any]:
        """
        Measure average inference time and FPS.

        If no image paths are provided, generates synthetic test frames.

        Returns:
            Dictionary with avg_inference_ms, fps, num_images, resolution.
        """
        detector = VehicleDetector()
        try:
            detector.load_model(model_path)
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

        frames: list[np.ndarray] = []

        if image_paths:
            for p in image_paths:
                img = cv2.imread(p)
                if img is not None:
                    frames.append(img)

        if not frames:
            # Generate synthetic frames for benchmarking
            logger.info("Generating %d synthetic frames for benchmark", num_synthetic)
            for _ in range(num_synthetic):
                frame = np.random.randint(0, 255, (*resolution[::-1], 3), dtype=np.uint8)
                frames.append(frame)

        # Warm up
        if frames:
            detector.detect(frames[0])

        inference_times: list[float] = []
        for frame in frames:
            t0 = time.perf_counter()
            detector.detect(frame)
            inference_times.append((time.perf_counter() - t0) * 1000)

        avg_ms = sum(inference_times) / len(inference_times) if inference_times else 0
        fps = 1000 / avg_ms if avg_ms > 0 else 0

        result = {
            "status": "completed",
            "model": os.path.basename(model_path),
            "num_images": len(frames),
            "resolution": f"{resolution[0]}x{resolution[1]}",
            "avg_inference_ms": round(avg_ms, 2),
            "fps": round(fps, 2),
            "min_inference_ms": round(min(inference_times), 2) if inference_times else 0,
            "max_inference_ms": round(max(inference_times), 2) if inference_times else 0,
        }
        logger.info("Benchmark: %.1f ms avg, %.1f FPS", avg_ms, fps)
        return result

    def get_model_info(self, model_path: str) -> dict[str, Any]:
        """
        Return basic information about a YOLO model file.
        """
        if not os.path.exists(model_path):
            return {"status": "not_found", "path": model_path}

        size_mb = os.path.getsize(model_path) / (1024 * 1024)

        try:
            from ultralytics import YOLO
            model = YOLO(model_path)
            num_classes = len(model.names)
            class_names = list(model.names.values())
        except Exception:
            num_classes = 0
            class_names = []

        return {
            "status": "loaded",
            "path": model_path,
            "filename": os.path.basename(model_path),
            "size_mb": round(size_mb, 2),
            "num_classes": num_classes,
            "class_names": class_names,
        }

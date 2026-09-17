"""
Image / frame preprocessing pipeline.

Each preprocessing operation is individually toggleable and documented
with its rationale.  The pipeline is applied to every frame before
object detection to improve model performance and consistency.

Computer Vision concepts demonstrated:
  - Colour-space conversion (BGR ↔ RGB)
  - Spatial resizing with aspect-ratio preservation
  - Intensity normalisation
  - Gaussian blurring for noise reduction
  - Brightness / contrast adjustment
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PreprocessConfig:
    """Toggle and configure individual preprocessing steps."""

    resize: bool = True
    max_dimension: int = 1280
    """
    **Resize**: Down-scale large frames so the detector runs faster
    and uses less GPU/CPU memory.  Aspect ratio is preserved.
    """

    normalize: bool = False
    """
    **Normalise to [0, 1]**: Some models expect float32 input scaled to
    [0, 1].  YOLO handles this internally so it is OFF by default, but
    the capability is provided for custom models.
    """

    convert_color: bool = False
    target_color: int = cv2.COLOR_BGR2RGB
    """
    **Colour conversion**: OpenCV reads images in BGR by default.
    Some external models expect RGB.  YOLO handles this internally,
    so this is OFF by default.
    """

    blur: bool = False
    blur_kernel: int = 3
    """
    **Gaussian blur**: Reduces high-frequency noise that can cause
    false detections, especially in low-quality CCTV footage.
    Kernel must be odd.
    """

    brightness: bool = False
    brightness_alpha: float = 1.0  # contrast control (1.0 = no change)
    brightness_beta: float = 0.0   # brightness control (0 = no change)
    """
    **Brightness / contrast adjustment**: Compensates for under-exposed
    or over-exposed footage (e.g., night-time or direct sunlight).
    output = alpha * pixel + beta
    """


class PreprocessingPipeline:
    """
    Applies a configurable sequence of CV operations to input frames.

    Usage::

        pipeline = PreprocessingPipeline()
        processed = pipeline.process(raw_frame)
    """

    def __init__(self, config: PreprocessConfig | None = None) -> None:
        self.config = config or PreprocessConfig()

    def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply all enabled preprocessing steps in a fixed order:
        resize → colour convert → blur → brightness → normalise.

        Args:
            frame: Raw BGR frame from OpenCV.

        Returns:
            Preprocessed frame (same dtype unless normalisation is on).
        """
        out = frame.copy()

        if self.config.resize:
            out = self._resize(out)

        if self.config.convert_color:
            out = cv2.cvtColor(out, self.config.target_color)

        if self.config.blur:
            k = self.config.blur_kernel
            if k % 2 == 0:
                k += 1  # ensure odd
            out = cv2.GaussianBlur(out, (k, k), 0)

        if self.config.brightness:
            out = cv2.convertScaleAbs(
                out,
                alpha=self.config.brightness_alpha,
                beta=self.config.brightness_beta,
            )

        if self.config.normalize:
            out = out.astype(np.float32) / 255.0

        return out

    def _resize(self, frame: np.ndarray) -> np.ndarray:
        """Resize keeping aspect ratio so the largest side ≤ max_dimension."""
        h, w = frame.shape[:2]
        max_dim = self.config.max_dimension
        if max(h, w) <= max_dim:
            return frame

        scale = max_dim / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        logger.debug("Resized frame %dx%d → %dx%d", w, h, new_w, new_h)
        return resized

    @staticmethod
    def extract_frames(
        video_path: str,
        frame_skip: int = 1,
        max_frames: int | None = None,
    ):
        """
        Generator yielding ``(frame_number, frame)`` tuples from a video.

        Args:
            video_path: Path to the video file.
            frame_skip: Yield every N-th frame (1 = every frame).
            max_frames: Stop after this many yielded frames.

        Yields:
            Tuple of (absolute frame index, BGR numpy array).
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error("Cannot open video: %s", video_path)
            return

        idx = 0
        yielded = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if idx % frame_skip == 0:
                yield idx, frame
                yielded += 1
                if max_frames and yielded >= max_frames:
                    break
            idx += 1

        cap.release()
        logger.debug("Extracted %d frames from %s", yielded, video_path)

"""Tests for the preprocessing pipeline."""

import cv2
import numpy as np
import pytest

from app.cv.preprocessing import PreprocessingPipeline, PreprocessConfig


class TestPreprocessingPipeline:
    """Tests for individual preprocessing operations."""

    def test_resize_large_frame(self):
        config = PreprocessConfig(resize=True, max_dimension=640)
        pipeline = PreprocessingPipeline(config)
        # 1920×1080 frame
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        result = pipeline.process(frame)
        h, w = result.shape[:2]
        assert max(h, w) <= 640

    def test_no_resize_small_frame(self):
        config = PreprocessConfig(resize=True, max_dimension=1280)
        pipeline = PreprocessingPipeline(config)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = pipeline.process(frame)
        assert result.shape == frame.shape

    def test_gaussian_blur(self):
        config = PreprocessConfig(resize=False, blur=True, blur_kernel=5)
        pipeline = PreprocessingPipeline(config)
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = pipeline.process(frame)
        # Blurred image should have lower high-frequency content
        assert result.shape == frame.shape
        assert not np.array_equal(result, frame)

    def test_blur_even_kernel_corrected(self):
        config = PreprocessConfig(resize=False, blur=True, blur_kernel=4)
        pipeline = PreprocessingPipeline(config)
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        # Should not crash — even kernel is corrected to odd
        result = pipeline.process(frame)
        assert result.shape == frame.shape

    def test_normalize(self):
        config = PreprocessConfig(resize=False, normalize=True)
        pipeline = PreprocessingPipeline(config)
        frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
        result = pipeline.process(frame)
        assert result.dtype == np.float32
        assert result.max() <= 1.0
        assert abs(result.mean() - 128/255) < 0.01

    def test_brightness_adjustment(self):
        config = PreprocessConfig(
            resize=False, brightness=True, brightness_alpha=1.5, brightness_beta=20,
        )
        pipeline = PreprocessingPipeline(config)
        frame = np.ones((100, 100, 3), dtype=np.uint8) * 100
        result = pipeline.process(frame)
        # Result should be brighter
        assert result.mean() > frame.mean()

    def test_default_config_preserves_shape(self, sample_frame):
        pipeline = PreprocessingPipeline()
        result = pipeline.process(sample_frame)
        # Default only resizes if > 1280, our sample is 640×480
        assert result.shape == sample_frame.shape

    def test_colour_conversion(self):
        config = PreprocessConfig(resize=False, convert_color=True, target_color=cv2.COLOR_BGR2RGB)
        pipeline = PreprocessingPipeline(config)
        # Create a frame with known BGR values
        frame = np.zeros((10, 10, 3), dtype=np.uint8)
        frame[:, :, 0] = 255  # Blue channel
        result = pipeline.process(frame)
        # After BGR→RGB, blue channel (index 0) moves to index 2
        assert result[:, :, 2].mean() == 255  # Blue in RGB
        assert result[:, :, 0].mean() == 0    # Red in RGB


class TestFrameExtraction:
    """Tests for the frame extraction generator."""

    def test_extract_nonexistent_video(self):
        frames = list(PreprocessingPipeline.extract_frames("nonexistent.mp4"))
        assert len(frames) == 0

    def test_extract_with_frame_skip(self, tmp_path):
        # Create a tiny synthetic video
        video_path = str(tmp_path / "test.avi")
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        writer = cv2.VideoWriter(video_path, fourcc, 10, (64, 64))
        for i in range(30):
            frame = np.zeros((64, 64, 3), dtype=np.uint8)
            frame[:, :] = i * 8  # varying brightness
            writer.write(frame)
        writer.release()

        frames = list(PreprocessingPipeline.extract_frames(video_path, frame_skip=5))
        # With 30 frames and skip=5, we get frames 0,5,10,15,20,25 = 6 frames
        assert len(frames) == 6
        # Check frame indices
        indices = [f[0] for f in frames]
        assert indices == [0, 5, 10, 15, 20, 25]

    def test_max_frames_limit(self, tmp_path):
        video_path = str(tmp_path / "test2.avi")
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")
        writer = cv2.VideoWriter(video_path, fourcc, 10, (64, 64))
        for _ in range(20):
            writer.write(np.zeros((64, 64, 3), dtype=np.uint8))
        writer.release()

        frames = list(PreprocessingPipeline.extract_frames(video_path, max_frames=3))
        assert len(frames) == 3

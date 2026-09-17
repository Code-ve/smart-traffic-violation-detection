"""Tests for upload validation utilities."""

import pytest

from app.utils.validators import (
    validate_file_extension,
    validate_file_size,
    validate_file_content,
    generate_safe_filename,
    is_image_extension,
    is_video_extension,
)
from app.utils.exceptions import UnsupportedFileError, FileTooLargeError


class TestFileExtensionValidation:
    """Tests for extension validation."""

    def test_valid_image_extensions(self):
        for ext_file in ["photo.jpg", "image.jpeg", "pic.png", "img.bmp", "w.webp"]:
            result = validate_file_extension(ext_file)
            assert result.startswith(".")

    def test_valid_video_extensions(self):
        for ext_file in ["vid.mp4", "clip.avi", "movie.mov", "video.mkv"]:
            result = validate_file_extension(ext_file)
            assert result.startswith(".")

    def test_invalid_extension(self):
        with pytest.raises(UnsupportedFileError):
            validate_file_extension("file.exe")

    def test_no_extension(self):
        with pytest.raises(UnsupportedFileError):
            validate_file_extension("noext")

    def test_case_insensitive(self):
        result = validate_file_extension("photo.JPG")
        assert result == ".jpg"


class TestFileSizeValidation:
    """Tests for file size validation."""

    def test_valid_size(self):
        # 1 MB should be fine with default 100MB limit
        validate_file_size(1 * 1024 * 1024)

    def test_exceeds_limit(self):
        with pytest.raises(FileTooLargeError):
            validate_file_size(200 * 1024 * 1024)  # 200 MB


class TestFileContentValidation:
    """Tests for magic-byte content validation."""

    def test_jpeg_magic(self):
        content = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        assert validate_file_content(content, "image") is True

    def test_png_magic(self):
        content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        assert validate_file_content(content, "image") is True

    def test_mp4_magic(self):
        content = b"\x00\x00\x00\x20ftypmp4" + b"\x00" * 100
        assert validate_file_content(content, "video") is True

    def test_unknown_content_passes(self):
        # Unknown magic bytes should still pass (fallback behaviour)
        content = b"\x01\x02\x03\x04" + b"\x00" * 100
        assert validate_file_content(content, "image") is True


class TestSafeFilename:
    """Tests for safe filename generation."""

    def test_preserves_extension(self):
        safe = generate_safe_filename("dangerous file (1).mp4")
        assert safe.endswith(".mp4")
        assert "dangerous" not in safe

    def test_unique_names(self):
        name1 = generate_safe_filename("test.jpg")
        name2 = generate_safe_filename("test.jpg")
        assert name1 != name2  # UUID-based, always unique

    def test_no_directory_traversal(self):
        safe = generate_safe_filename("../../etc/passwd.jpg")
        assert "/" not in safe
        assert "\\" not in safe
        assert ".." not in safe


class TestExtensionChecks:
    """Tests for extension type checks."""

    def test_image_extensions(self):
        assert is_image_extension(".jpg") is True
        assert is_image_extension(".png") is True
        assert is_image_extension(".mp4") is False

    def test_video_extensions(self):
        assert is_video_extension(".mp4") is True
        assert is_video_extension(".avi") is True
        assert is_video_extension(".jpg") is False

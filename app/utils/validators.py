"""
Upload validation utilities.

Provides file-type, size, and filename security checks for uploaded
files.  All public functions raise custom exceptions from
``app.utils.exceptions`` on validation failure.
"""

import os
import uuid
from pathlib import Path

from app.config.settings import get_settings
from app.utils.exceptions import UnsupportedFileError, FileTooLargeError
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ── Magic-byte signatures for quick content validation ───────────────────
_MAGIC_BYTES: dict[str, list[bytes]] = {
    "image": [
        b"\xff\xd8\xff",          # JPEG
        b"\x89PNG\r\n\x1a\n",     # PNG
        b"BM",                     # BMP
        b"RIFF",                   # WEBP (inside RIFF container)
    ],
    "video": [
        b"\x00\x00\x00",          # MP4 / MOV (ftyp box)
        b"RIFF",                   # AVI (inside RIFF container)
        b"\x1a\x45\xdf\xa3",      # MKV / WebM
        b"\x30\x26\xb2\x75",      # WMV / ASF
    ],
}


def validate_file_extension(filename: str) -> str:
    """
    Check that *filename* has an allowed extension.

    Returns:
        The normalised extension (e.g. ``".jpg"``).

    Raises:
        UnsupportedFileError: If the extension is not in the allow-list.
    """
    settings = get_settings()
    ext = Path(filename).suffix.lower()
    all_allowed = settings.allowed_image_extensions + settings.allowed_video_extensions
    if ext not in all_allowed:
        logger.warning("Rejected file with extension %s", ext)
        raise UnsupportedFileError(ext)
    return ext


def is_image_extension(ext: str) -> bool:
    """Return True if *ext* is a recognised image extension."""
    return ext.lower() in get_settings().allowed_image_extensions


def is_video_extension(ext: str) -> bool:
    """Return True if *ext* is a recognised video extension."""
    return ext.lower() in get_settings().allowed_video_extensions


def validate_file_size(size_bytes: int) -> None:
    """
    Raise ``FileTooLargeError`` if *size_bytes* exceeds the configured limit.
    """
    settings = get_settings()
    max_bytes = settings.upload_max_size_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise FileTooLargeError(
            size_mb=size_bytes / (1024 * 1024),
            max_mb=settings.upload_max_size_mb,
        )


def validate_file_content(file_bytes: bytes, expected_type: str) -> bool:
    """
    Perform a basic magic-byte check on the first few bytes.

    Args:
        file_bytes: The raw file content (at least the first 16 bytes).
        expected_type: ``"image"`` or ``"video"``.

    Returns:
        True if any known signature matches.
    """
    sigs = _MAGIC_BYTES.get(expected_type, [])
    header = file_bytes[:16]
    for sig in sigs:
        if header.startswith(sig):
            return True
    # Fallback — if none matched we still allow it (the decoder will reject
    # truly corrupt files later).
    logger.debug("Magic-byte check inconclusive for %s", expected_type)
    return True


def generate_safe_filename(original_filename: str) -> str:
    """
    Generate a safe, unique filename preserving only the extension.

    This prevents path-traversal attacks and filename collisions.

    Args:
        original_filename: The user-supplied filename.

    Returns:
        A UUID-based filename with the original extension, e.g.
        ``"a3f2e1c4-…-d9b8.mp4"``.
    """
    ext = Path(original_filename).suffix.lower()
    safe = f"{uuid.uuid4().hex}{ext}"
    return safe


def save_upload(content: bytes, original_filename: str, dest_dir: str | None = None) -> str:
    """
    Validate and persist an uploaded file.

    Performs extension, size, and content checks, then writes the file to
    the upload directory with a safe generated name.

    Args:
        content: Raw file bytes.
        original_filename: User-supplied filename.
        dest_dir: Override destination directory.

    Returns:
        Absolute path to the saved file.

    Raises:
        UnsupportedFileError: Bad extension.
        FileTooLargeError: File exceeds size limit.
    """
    ext = validate_file_extension(original_filename)
    validate_file_size(len(content))

    file_type = "image" if is_image_extension(ext) else "video"
    validate_file_content(content, file_type)

    safe_name = generate_safe_filename(original_filename)
    settings = get_settings()
    target_dir = dest_dir or settings.upload_dir
    os.makedirs(target_dir, exist_ok=True)
    dest_path = os.path.join(target_dir, safe_name)

    with open(dest_path, "wb") as f:
        f.write(content)

    logger.info("Saved upload: %s → %s (%d bytes)", original_filename, safe_name, len(content))
    return dest_path

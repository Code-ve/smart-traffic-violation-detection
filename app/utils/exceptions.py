"""
Custom exception hierarchy.

These exceptions provide structured error handling throughout the
application.  The API layer catches them and returns user-friendly
error messages while the logging layer records full details.
"""


class TrafficSystemError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str = "An internal error occurred.", detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class ModelNotFoundError(TrafficSystemError):
    """Raised when the YOLO model file cannot be found or loaded."""

    def __init__(self, model_path: str = ""):
        super().__init__(
            message=f"Model not found: {model_path}",
            detail="Please download a YOLO model and place it in the models/ directory.",
        )


class InvalidVideoError(TrafficSystemError):
    """Raised when a video file cannot be opened or decoded."""

    def __init__(self, path: str = ""):
        super().__init__(
            message=f"Invalid or corrupt video file: {path}",
            detail="Ensure the file is a valid video in a supported format (mp4, avi, mov, mkv).",
        )


class InvalidImageError(TrafficSystemError):
    """Raised when an image file cannot be opened or decoded."""

    def __init__(self, path: str = ""):
        super().__init__(
            message=f"Invalid or corrupt image file: {path}",
            detail="Ensure the file is a valid image in a supported format (jpg, png, bmp, webp).",
        )


class UnsupportedFileError(TrafficSystemError):
    """Raised when the uploaded file type is not supported."""

    def __init__(self, extension: str = ""):
        super().__init__(
            message=f"Unsupported file type: {extension}",
            detail="Supported formats: jpg, jpeg, png, bmp, webp, mp4, avi, mov, mkv, wmv.",
        )


class FileTooLargeError(TrafficSystemError):
    """Raised when a file exceeds the maximum allowed size."""

    def __init__(self, size_mb: float = 0, max_mb: int = 100):
        super().__init__(
            message=f"File too large ({size_mb:.1f} MB). Maximum allowed: {max_mb} MB.",
        )


class DatabaseError(TrafficSystemError):
    """Raised for database connection or query failures."""

    def __init__(self, message: str = "Database operation failed.", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class ProcessingError(TrafficSystemError):
    """Raised when video/image processing fails."""

    def __init__(self, message: str = "Processing failed.", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class CameraUnavailableError(TrafficSystemError):
    """Raised when the webcam cannot be accessed."""

    def __init__(self):
        super().__init__(
            message="Webcam is not available.",
            detail="Ensure a camera is connected and not in use by another application.",
        )

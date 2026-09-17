"""
Application configuration using Pydantic BaseSettings.

Loads configuration from environment variables and .env file.
Provides safe defaults for all settings so the application can run
without any manual configuration.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


# Project root directory (smart-traffic-violation-detection/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Central configuration for the entire application.

    Values are loaded from environment variables first, then from a .env file
    located at the project root. Defaults are provided for every setting so
    the system can start without any .env file.
    """

    # ── Model ────────────────────────────────────────────────────────────
    model_path: str = Field(
        default=str(BASE_DIR / "models" / "yolov8n.pt"),
        description="Path to the YOLO model weights file.",
    )
    confidence_threshold: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score for detections.",
    )
    iou_threshold: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description="IoU threshold for Non-Maximum Suppression.",
    )
    tracker_type: str = Field(
        default="bytetrack",
        description="Tracker algorithm: 'bytetrack' or 'botsort'.",
    )

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = Field(
        default=str(BASE_DIR / "data" / "traffic.db"),
        description="SQLite database file path.",
    )

    # ── Directories ──────────────────────────────────────────────────────
    upload_dir: str = Field(default=str(BASE_DIR / "data" / "input"))
    output_dir: str = Field(default=str(BASE_DIR / "data" / "output"))
    evidence_dir: str = Field(default=str(BASE_DIR / "data" / "evidence"))

    # ── Upload Limits ────────────────────────────────────────────────────
    upload_max_size_mb: int = Field(
        default=100,
        description="Maximum upload file size in megabytes.",
    )
    allowed_image_extensions: list[str] = Field(
        default=[".jpg", ".jpeg", ".png", ".bmp", ".webp"],
    )
    allowed_video_extensions: list[str] = Field(
        default=[".mp4", ".avi", ".mov", ".mkv", ".wmv"],
    )

    # ── Processing ───────────────────────────────────────────────────────
    frame_skip: int = Field(
        default=1,
        ge=1,
        description="Process every N-th frame (1 = every frame).",
    )
    max_resolution: int = Field(
        default=1280,
        description="Maximum dimension (width or height) for input frames.",
    )

    # ── Violation Rules ──────────────────────────────────────────────────
    evidence_cooldown_seconds: float = Field(
        default=3.0,
        description="Seconds before the same vehicle can trigger the same violation again.",
    )

    # Red-light violation
    red_light_enabled: bool = True
    red_light_line_y: int = Field(
        default=400,
        description="Y-coordinate of the virtual stop line (pixels from top).",
    )
    signal_state: str = Field(
        default="GREEN",
        description="Current traffic signal state: RED or GREEN.",
    )

    # Speed / zone violation
    speed_zone_enabled: bool = True
    speed_zone_displacement_threshold: float = Field(
        default=80.0,
        description="Pixel displacement per frame that triggers a speed violation (prototype).",
    )

    # Helmet violation (requires custom model with helmet classes)
    helmet_enabled: bool = Field(
        default=False,
        description="Enable helmet violation detection (requires model with helmet classes).",
    )

    # ── Server ───────────────────────────────────────────────────────────
    host: str = "localhost"
    port: int = 8000
    debug: bool = True

    # ── Logging ──────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = Field(default=str(BASE_DIR / "app.log"))

    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


def ensure_directories(settings: Optional[Settings] = None) -> None:
    """Create required data directories if they do not exist."""
    s = settings or get_settings()
    for dir_path in [s.upload_dir, s.output_dir, s.evidence_dir]:
        os.makedirs(dir_path, exist_ok=True)

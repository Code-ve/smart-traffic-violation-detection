"""
Pydantic request/response schemas for the API.

Provides serialization, validation, and automatic OpenAPI documentation
for all API endpoints.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Response models ──────────────────────────────────────────────────────

class DetectionResponse(BaseModel):
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    track_id: Optional[int] = None
    frame_number: int = 0
    timestamp: str = ""


class ViolationResponse(BaseModel):
    id: int
    session_id: Optional[str] = None
    timestamp: str
    violation_type: str
    track_id: Optional[int] = None
    vehicle_type: Optional[str] = None
    confidence: Optional[float] = None
    frame_number: Optional[int] = None
    video_timestamp: Optional[str] = None
    evidence_path: Optional[str] = None
    status: str = "Detected"


class ProcessingResultResponse(BaseModel):
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


class SessionResponse(BaseModel):
    id: str
    filename: str
    file_type: str = "video"
    started_at: str
    completed_at: Optional[str] = None
    status: str = "processing"
    total_frames: int = 0
    processed_frames: int = 0
    total_vehicles: int = 0
    unique_vehicles: int = 0
    total_violations: int = 0
    avg_fps: float = 0.0
    avg_inference_ms: float = 0.0
    model_used: Optional[str] = None
    output_path: Optional[str] = None


class ProgressResponse(BaseModel):
    session_id: str
    frame: int = 0
    total_frames: int = 0
    processed: int = 0
    detections: int = 0
    unique_vehicles: int = 0
    violations: int = 0
    fps: float = 0.0
    percent: float = 0.0


class TrafficStatsResponse(BaseModel):
    total_vehicles: int = 0
    unique_vehicles: int = 0
    by_type: dict[str, int] = {}


class ViolationStatsResponse(BaseModel):
    total_violations: int = 0
    by_type: dict[str, int] = {}
    violation_percentage: float = 0.0


class AnalyticsSummaryResponse(BaseModel):
    total_sessions: int = 0
    completed_sessions: int = 0
    total_frames_processed: int = 0
    total_vehicles_tracked: int = 0
    total_violations_detected: int = 0
    sessions: list[dict] = []


# ── Request models ───────────────────────────────────────────────────────

class ViolationStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(Detected|Reviewed|Resolved)$")


class ConfigUpdate(BaseModel):
    signal_state: Optional[str] = None
    red_light_line_y: Optional[int] = None
    speed_zone_displacement_threshold: Optional[float] = None
    confidence_threshold: Optional[float] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

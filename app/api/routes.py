"""
FastAPI routes — all API endpoints and page-serving routes.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates

from app.api.schemas import (
    ConfigUpdate,
    ErrorResponse,
    ProcessingResultResponse,
    ViolationStatusUpdate,
)
from app.analytics.statistics import AnalyticsService
from app.config.settings import get_settings, BASE_DIR
from app.cv.video_processor import VideoProcessor, get_processing_progress
from app.database import repository as repo
from app.evaluation.evaluate import ModelEvaluator
from app.utils.exceptions import TrafficSystemError
from app.utils.logger import get_logger
from app.utils.validators import (
    validate_file_extension,
    validate_file_size,
    is_image_extension,
    is_video_extension,
    generate_safe_filename,
)

logger = get_logger(__name__)

router = APIRouter()

# ── Template engine ──────────────────────────────────────────────────────
_template_dir = os.path.join(BASE_DIR, "frontend", "templates")
templates = Jinja2Templates(directory=_template_dir)

# ── Shared processor instance ────────────────────────────────────────────
_processor = VideoProcessor()
_analytics = AnalyticsService()
_evaluator = ModelEvaluator()


# ═══════════════════════════════════════════════════════════════════════════
#  Page routes (serve HTML templates)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse(request=request, name="upload.html")


@router.get("/processing/{session_id}", response_class=HTMLResponse)
async def processing_page(request: Request, session_id: str):
    session = repo.get_session(session_id)
    return templates.TemplateResponse(
        request=request, name="processing.html", context={"session_id": session_id, "session": session}
    )


@router.get("/violations", response_class=HTMLResponse)
async def violations_page(request: Request):
    return templates.TemplateResponse(request=request, name="violations.html")


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    return templates.TemplateResponse(request=request, name="analytics.html")


@router.get("/evaluation", response_class=HTMLResponse)
async def evaluation_page(request: Request):
    return templates.TemplateResponse(request=request, name="evaluation.html")


# ═══════════════════════════════════════════════════════════════════════════
#  Upload & Processing API
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/api/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """Upload an image or video for processing."""
    try:
        filename = file.filename or "unknown"
        ext = validate_file_extension(filename)

        # Read content
        content = await file.read()
        validate_file_size(len(content))

        # Save with safe filename
        settings = get_settings()
        safe_name = generate_safe_filename(filename)
        os.makedirs(settings.upload_dir, exist_ok=True)
        save_path = os.path.join(settings.upload_dir, safe_name)
        with open(save_path, "wb") as f:
            f.write(content)

        logger.info("Upload saved: %s → %s (%d bytes)", filename, safe_name, len(content))

        # Ensure model is loaded
        if not _processor.is_model_loaded:
            try:
                _processor.load_model()
            except Exception as exc:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Model not available", "detail": str(exc)},
                )

        if is_image_extension(ext):
            # Process image synchronously (fast)
            result = _processor.process_image(save_path)
            return {
                "status": "completed",
                "type": "image",
                "result": result.to_dict(),
                "detections": result.detections,
            }
        else:
            # Process video in background
            session_id = repo.create_session(
                filename=filename, file_type="video", model_used=_processor._detector.model_name,
            )

            def _process_video_bg():
                try:
                    # Delete the pre-created session since process_video creates its own
                    # Actually, let's just use the processor directly
                    _processor.process_video(save_path)
                except Exception as exc:
                    logger.error("Background video processing failed: %s", exc)

            background_tasks.add_task(_process_video_bg)

            # Return immediately with a session ID for polling
            # The process_video method will create its own session
            return {
                "status": "processing",
                "type": "video",
                "message": "Video processing started in background",
                "filename": filename,
            }

    except TrafficSystemError as exc:
        return JSONResponse(
            status_code=400, content={"error": exc.message, "detail": exc.detail},
        )
    except Exception as exc:
        logger.error("Upload failed: %s", exc)
        return JSONResponse(
            status_code=500, content={"error": "Upload failed", "detail": str(exc)},
        )


@router.get("/api/sessions")
async def list_sessions():
    """List all processing sessions."""
    return repo.get_all_sessions()


@router.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get details for a specific session."""
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/api/sessions/{session_id}/progress")
async def get_progress(session_id: str):
    """Get live processing progress for a running session."""
    progress = get_processing_progress(session_id)
    if progress:
        return progress

    # Check if completed
    session = repo.get_session(session_id)
    if session and session.get("status") == "completed":
        return {
            "session_id": session_id,
            "status": "completed",
            "percent": 100,
            "total_frames": session.get("total_frames", 0),
            "processed": session.get("processed_frames", 0),
            "unique_vehicles": session.get("unique_vehicles", 0),
            "violations": session.get("total_violations", 0),
            "fps": session.get("avg_fps", 0),
        }

    return {"session_id": session_id, "status": "unknown", "percent": 0}


# ═══════════════════════════════════════════════════════════════════════════
#  Violations API
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/api/violations")
async def get_violations(
    session_id: str | None = None,
    violation_type: str | None = None,
    vehicle_type: str | None = None,
    status: str | None = None,
    limit: int = 500,
):
    """Query violations with optional filters."""
    return repo.get_violations(
        session_id=session_id,
        violation_type=violation_type,
        vehicle_type=vehicle_type,
        status=status,
        limit=limit,
    )


@router.patch("/api/violations/{violation_id}/status")
async def update_violation(violation_id: int, update: ViolationStatusUpdate):
    """Update a violation's status (Detected → Reviewed → Resolved)."""
    success = repo.update_violation_status(violation_id, update.status)
    if not success:
        raise HTTPException(status_code=404, detail="Violation not found or invalid status")
    return {"id": violation_id, "status": update.status}


# ═══════════════════════════════════════════════════════════════════════════
#  Analytics API
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/api/analytics/traffic")
async def get_traffic_stats(session_id: str | None = None):
    return _analytics.get_traffic_stats(session_id)


@router.get("/api/analytics/violations")
async def get_violation_stats(session_id: str | None = None):
    return _analytics.get_violation_stats(session_id)


@router.get("/api/analytics/timeline/{session_id}")
async def get_timeline(session_id: str):
    return _analytics.get_timeline_data(session_id)


@router.get("/api/analytics/confidence")
async def get_confidence(session_id: str | None = None):
    return _analytics.get_confidence_distribution(session_id)


@router.get("/api/analytics/summary")
async def get_summary():
    return _analytics.get_summary()


# ═══════════════════════════════════════════════════════════════════════════
#  Evaluation API
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/api/evaluation/info")
async def model_info():
    """Get information about the loaded model."""
    settings = get_settings()
    return _evaluator.get_model_info(settings.model_path)


@router.get("/api/evaluation/benchmark")
async def run_benchmark():
    """Run an inference benchmark on the current model."""
    settings = get_settings()
    return _evaluator.benchmark_inference(settings.model_path)


@router.get("/api/evaluation/evaluate")
async def run_evaluation(dataset: str | None = None):
    """Run full model evaluation (requires dataset YAML)."""
    settings = get_settings()
    return _evaluator.evaluate_model(settings.model_path, dataset)


# ═══════════════════════════════════════════════════════════════════════════
#  Configuration API
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/api/config")
async def get_config():
    """Return current runtime configuration."""
    settings = get_settings()
    return {
        "model_path": settings.model_path,
        "confidence_threshold": settings.confidence_threshold,
        "iou_threshold": settings.iou_threshold,
        "tracker_type": settings.tracker_type,
        "frame_skip": settings.frame_skip,
        "signal_state": _processor._runtime_config.get("signal_state", settings.signal_state),
        "red_light_line_y": _processor._runtime_config.get("red_light_line_y", settings.red_light_line_y),
        "speed_zone_displacement_threshold": _processor._runtime_config.get(
            "speed_zone_displacement_threshold", settings.speed_zone_displacement_threshold
        ),
        "red_light_enabled": settings.red_light_enabled,
        "speed_zone_enabled": settings.speed_zone_enabled,
        "helmet_enabled": settings.helmet_enabled,
    }


@router.post("/api/config")
async def update_config(update: ConfigUpdate):
    """Update runtime configuration (signal state, thresholds)."""
    changes = {k: v for k, v in update.model_dump().items() if v is not None}
    if changes:
        _processor.update_config(**changes)
    return {"updated": changes}


# ═══════════════════════════════════════════════════════════════════════════
#  Static file serving for evidence/output
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/api/evidence/{filename}")
async def serve_evidence(filename: str):
    """Serve an evidence image by filename."""
    settings = get_settings()
    path = os.path.join(settings.evidence_dir, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Evidence file not found")
    return FileResponse(path, media_type="image/jpeg")


@router.get("/api/output/{filename}")
async def serve_output(filename: str):
    """Serve a processed output file."""
    settings = get_settings()
    path = os.path.join(settings.output_dir, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Output file not found")
    return FileResponse(path)

"""
FastAPI application entry point.

Creates the application, mounts static files, registers routes,
and initialises the database on startup.

Run with:
    python -m app.main
"""

import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config.settings import get_settings, ensure_directories, BASE_DIR
from app.database.database import init_db
from app.utils.logger import setup_logging, get_logger


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    # ── Logging ──────────────────────────────────────────────────────────
    setup_logging(level=settings.log_level, log_file=settings.log_file)
    logger = get_logger(__name__)

    # ── FastAPI app ──────────────────────────────────────────────────────
    app = FastAPI(
        title="Smart Traffic Violation Detection & Analytics System",
        description="Computer Vision system for detecting traffic violations using YOLO.",
        version="1.0.0",
    )

    # ── Startup event ────────────────────────────────────────────────────
    @app.on_event("startup")
    async def startup():
        logger.info("Starting Smart Traffic Violation Detection System")
        ensure_directories(settings)
        init_db()
        logger.info("Database initialised")
        logger.info("Server running at http://%s:%s", settings.host, settings.port)

    # ── Static files ─────────────────────────────────────────────────────
    static_dir = os.path.join(BASE_DIR, "frontend", "static")
    os.makedirs(static_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Also serve evidence & output as static where needed
    evidence_dir = settings.evidence_dir
    output_dir = settings.output_dir
    os.makedirs(evidence_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    app.mount("/evidence", StaticFiles(directory=evidence_dir), name="evidence")
    app.mount("/output", StaticFiles(directory=output_dir), name="output")

    # ── Routes ───────────────────────────────────────────────────────────
    app.include_router(router)

    return app


app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

#!/usr/bin/env python
"""
Database initialisation script.

Run this once before starting the application to create the SQLite
database and all required tables.

Usage:
    python scripts/setup_db.py
"""

import sys
import os

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import init_db
from app.config.settings import ensure_directories, get_settings


def main() -> None:
    settings = get_settings()
    print(f"Initialising database at: {settings.database_url}")
    ensure_directories(settings)
    init_db()
    print("Database and directories created successfully.")
    print(f"  Upload dir:   {settings.upload_dir}")
    print(f"  Output dir:   {settings.output_dir}")
    print(f"  Evidence dir: {settings.evidence_dir}")


if __name__ == "__main__":
    main()

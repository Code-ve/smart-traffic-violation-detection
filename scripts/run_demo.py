#!/usr/bin/env python
"""
Demo runner — processes a sample video or image for quick demonstration.

Usage:
    python scripts/run_demo.py --input data/input/sample.mp4
    python scripts/run_demo.py --input data/input/photo.jpg
    python scripts/run_demo.py --input data/input/sample.mp4 --signal RED
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import init_db
from app.config.settings import ensure_directories, get_settings
from app.cv.video_processor import VideoProcessor
from app.utils.validators import is_image_extension, is_video_extension


def main() -> None:
    parser = argparse.ArgumentParser(description="Run traffic violation demo")
    parser.add_argument("--input", type=str, required=True, help="Path to image or video")
    parser.add_argument("--model", type=str, default=None, help="Path to YOLO model")
    parser.add_argument("--signal", type=str, default="GREEN", help="Signal state: RED or GREEN")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    # Initialise
    init_db()
    ensure_directories()

    processor = VideoProcessor()
    if args.model:
        processor.load_model(args.model)

    processor.update_config(signal_state=args.signal.upper())

    ext = os.path.splitext(args.input)[1].lower()

    if is_image_extension(ext):
        print(f"Processing image: {args.input}")
        result = processor.process_image(args.input)
    elif is_video_extension(ext):
        print(f"Processing video: {args.input}")
        result = processor.process_video(
            args.input,
            progress_callback=lambda p: print(
                f"\r  Frame {p['frame']}/{p['total_frames']} | "
                f"FPS: {p['fps']} | Vehicles: {p['unique_vehicles']} | "
                f"Violations: {p['violations']} | {p['percent']}%",
                end="",
            ),
        )
        print()  # newline after progress
    else:
        print(f"Unsupported file type: {ext}")
        sys.exit(1)

    print(f"\n{'=' * 50}")
    print(f"  Session: {result.session_id}")
    print(f"  Frames:  {result.processed_frames}/{result.total_frames}")
    print(f"  Detections: {result.total_detections}")
    print(f"  Unique vehicles: {result.unique_vehicles}")
    print(f"  Violations: {result.total_violations}")
    print(f"  Avg FPS: {result.avg_fps}")
    print(f"  Output: {result.output_path}")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    main()

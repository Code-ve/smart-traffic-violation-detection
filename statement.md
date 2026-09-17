# Problem Statement

## Problem Statement

Traffic violations are a leading cause of road accidents and fatalities globally. Manual monitoring of traffic by law enforcement is limited in scale, consistency, and efficiency. There is a growing need for automated systems that can assist in identifying traffic violations from video surveillance footage.

This project addresses the problem of **automated traffic violation detection** by building a Computer Vision prototype that processes traffic images and videos to detect vehicles, track them, and identify violations such as red-light running and speeding.

## Scope

This system is an **academic prototype** developed for the VITyarthi Computer Vision domain project evaluation. The scope includes:

- **Image-based vehicle detection** using YOLO object detection
- **Video-based vehicle tracking** using ByteTrack
- **Rule-based violation detection** (red-light, speed/zone, helmet)
- **Evidence generation** with annotated frames
- **Violation management** with SQLite storage
- **Analytics dashboard** with real-time charts
- **Model evaluation** with mAP and inference metrics

### Out of Scope

- Real-world deployment or legal enforcement
- Automatic traffic-light state recognition (simulated for demo)
- License plate recognition
- Multi-camera fusion
- Cloud deployment

## Target Users

1. **Academic evaluators** — Faculty assessing the project against CV domain requirements
2. **Students** — Demonstrating practical Computer Vision application
3. **Traffic researchers** — Exploring prototype violation detection approaches

## Proposed Solution

A modular Computer Vision system built in Python using:

- **OpenCV** for image/video I/O and preprocessing
- **Ultralytics YOLO** for real-time object detection
- **ByteTrack** for multi-object tracking with persistent IDs
- **Rule-based violation engine** with configurable violation rules
- **SQLite** for structured event storage
- **FastAPI** web interface for demonstration and interaction

### Architecture Overview

```
Input → Validation → Preprocessing → YOLO Detection → ByteTrack Tracking
    → Violation Rule Engine → Evidence Generation → SQLite Storage → Analytics Dashboard
```

## High-Level Features

| Feature | Description |
|---|---|
| Image Detection | Upload images for single-frame vehicle detection |
| Video Processing | Frame-by-frame detection with tracking and violation analysis |
| Vehicle Tracking | Persistent track IDs and trajectory visualization |
| Red-Light Violation | Virtual stop line with configurable signal state |
| Speed/Zone Violation | Pixel displacement-based prototype estimation |
| Evidence Capture | Annotated violation frames with metadata overlay |
| Analytics Dashboard | Interactive charts from real processing data |
| Model Evaluation | mAP, precision, recall, and inference benchmarks |

## Functional Modules

1. **Input & Video Processing** — Upload validation, frame extraction, format support
2. **Object Detection** — YOLO model inference with confidence scoring
3. **Object Tracking** — ByteTrack-based persistent vehicle tracking
4. **Violation Rule Engine** — Modular rule evaluation with cooldown
5. **Evidence Generation** — Annotated frame capture and storage
6. **Violation Management** — CRUD operations, filtering, status workflow
7. **Analytics** — Statistical aggregation and chart generation
8. **Model Evaluation** — Dataset validation and inference benchmarking

## Expected Outcome

A complete, runnable Computer Vision system that:

1. Accepts traffic images and videos as input
2. Detects and classifies vehicles using YOLO
3. Tracks vehicles across video frames with persistent IDs
4. Identifies configurable traffic violations using rule-based logic
5. Generates annotated evidence images for each violation
6. Stores all events in a structured SQLite database
7. Provides interactive analytics through a web dashboard
8. Reports model performance metrics for academic evaluation

The system demonstrates practical application of core Computer Vision concepts (detection, tracking, preprocessing, evaluation) in a real-world-inspired scenario, presented with professional documentation suitable for university viva defence.

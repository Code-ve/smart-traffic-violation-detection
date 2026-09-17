# Project Report — Smart Traffic Violation Detection & Analytics System

---

## 1. Cover Page

**Project Title**: Smart Traffic Violation Detection & Analytics System

**Domain**: Computer Vision

**Program**: VITyarthi — Build Your Own Project

**Date**: 2024

---

## 2. Introduction

Traffic violations are a significant contributor to road accidents worldwide. Automated traffic monitoring systems can assist law enforcement by detecting violations consistently and at scale. This project builds a Computer Vision prototype that demonstrates automated traffic violation detection from video footage using object detection, vehicle tracking, and rule-based analysis.

The system uses the YOLO (You Only Look Once) object detection architecture to identify vehicles in traffic scenes, ByteTrack for multi-object tracking with persistent IDs, and a configurable rule engine to detect violations such as running a red light or exceeding a speed threshold.

---

## 3. Problem Statement

Manual traffic monitoring is limited by human attention span, geographic coverage, and consistency. Violations often go undetected, especially at intersections without dedicated enforcement personnel.

This project addresses the problem by building a system that:
- Automatically detects vehicles in traffic footage
- Tracks vehicles across video frames
- Identifies configurable traffic violations
- Generates annotated evidence for each violation
- Provides analytics for traffic analysis

See `statement.md` for the full problem statement.

---

## 4. Objectives

1. Implement real-time vehicle detection using YOLO object detection
2. Track detected vehicles across video frames with persistent IDs
3. Build a configurable rule-based violation detection engine
4. Generate annotated evidence images for detected violations
5. Store all events in a structured database
6. Provide an interactive analytics dashboard
7. Evaluate model performance using standard CV metrics
8. Deliver a modular, testable, and documented codebase

---

## 5. Functional Requirements

| ID | Requirement | Status |
|---|---|---|
| FR1 | Upload and process traffic images | ✅ Implemented |
| FR2 | Upload and process traffic videos | ✅ Implemented |
| FR3 | Detect vehicles using YOLO | ✅ Implemented |
| FR4 | Track vehicles with persistent IDs | ✅ Implemented |
| FR5 | Detect red-light violations | ✅ Implemented |
| FR6 | Detect speed/zone violations (prototype) | ✅ Implemented |
| FR7 | Detect helmet violations (optional model) | ✅ Implemented (auto-disables) |
| FR8 | Generate evidence images | ✅ Implemented |
| FR9 | Store violations in database | ✅ Implemented |
| FR10 | Filter and manage violations | ✅ Implemented |
| FR11 | Display analytics dashboard | ✅ Implemented |
| FR12 | Evaluate model performance | ✅ Implemented |

---

## 6. Non-functional Requirements

| Requirement | Implementation |
|---|---|
| **Performance** | FPS tracking, inference time measurement, frame skipping |
| **Reliability** | Graceful error handling for invalid files, missing model, camera unavailable |
| **Usability** | Clean web interface with drag-and-drop upload, real-time stats |
| **Maintainability** | Modular architecture, separated layers, documented code |
| **Scalability** | Detector/model can be replaced via configuration |
| **Security** | Extension validation, MIME checking, safe filenames, size limits |
| **Error Handling** | Custom exception hierarchy with user-friendly messages |

---

## 7. System Architecture

The system follows a layered architecture:

1. **Presentation Layer** — HTML/CSS/JS web interface
2. **API Layer** — FastAPI REST endpoints
3. **Processing Layer** — Video processor orchestrating CV pipeline
4. **Business Logic Layer** — Violation engine and analytics
5. **Data Layer** — SQLite database and file system storage
6. **Infrastructure Layer** — Configuration, logging, error handling

See `docs/architecture.md` and `docs/diagrams/architecture.md` for diagrams.

---

## 8. Design Diagrams

The following diagrams are provided in Mermaid format in `docs/diagrams/`:

1. **Use Case Diagram** — Actors and system interactions
2. **Workflow Diagram** — Processing pipeline flow
3. **Architecture Diagram** — System layers and components
4. **Sequence Diagram** — Upload-to-analytics interaction flow
5. **Component/Class Diagram** — Major classes and relationships
6. **ER Diagram** — Database entities and relationships

---

## 9. Design Decisions & Rationale

Key design decisions documented in `docs/design-decisions.md`:

- **YOLO** chosen for speed-accuracy balance and Ultralytics ecosystem
- **ByteTrack** for zero-dependency multi-object tracking
- **SQLite** for zero-configuration database
- **FastAPI** for async support and automatic API documentation
- **Rule-based violations** for explainability and configurability
- **Server-rendered templates** for simplicity and single-deployment

---

## 10. Computer Vision Methodology

### 10.1 Object Detection

The system uses YOLO (You Only Look Once), a single-stage object detection architecture that processes an entire image in one forward pass. The detector:
- Divides the image into a grid
- Predicts bounding boxes and class probabilities for each cell
- Applies Non-Maximum Suppression (NMS) to remove overlapping detections

### 10.2 Preprocessing

Before detection, frames undergo configurable preprocessing:
- **Resize**: Down-scale to max 1280px to improve inference speed
- **Gaussian Blur**: Reduce noise in low-quality CCTV footage
- **Brightness Adjustment**: Compensate for poor lighting
- **Colour Conversion**: BGR ↔ RGB as needed by different models

### 10.3 Multi-Object Tracking

ByteTrack assigns persistent IDs to detected objects across frames using IoU-based association. The tracker:
- Associates detections to existing tracks using IoU overlap
- Creates new tracks for unmatched detections
- Maintains trajectory history for each vehicle

### 10.4 Violation Detection

Rule-based analysis on tracked detections:
- **Red-light**: Checks if vehicle bottom edge crosses stop line while signal is RED
- **Speed/zone**: Checks pixel displacement between frames against threshold
- **Helmet**: Checks for helmet-related classes in custom models (auto-disables otherwise)

---

## 11. Dataset Description

The system is designed to work with any traffic video/image. For formal evaluation, recommended datasets include:

| Dataset | Classes | Annotation | Source |
|---|---|---|---|
| COCO 2017 | 80 (incl. vehicles) | Bounding boxes | cocodataset.org |
| UA-DETRAC | Vehicles | Bounding boxes + tracking | detrac-db.rit.albany.edu |
| BDD100K | Vehicles + pedestrians | Multi-label | bdd-data.berkeley.edu |

See `docs/evaluation.md` for dataset format and preparation instructions.

---

## 12. Model Selection

YOLOv8 nano was selected as the default model. Detailed rationale is in `docs/design-decisions.md`.

---

## 13. Implementation Details

### 13.1 Project Structure

The project contains 30+ source files organized across 8 packages:
- `app/cv/` — Computer Vision modules (5 files)
- `app/violations/` — Violation rules and engine (5 files)
- `app/database/` — Database layer (2 files)
- `app/analytics/` — Analytics service (1 file)
- `app/evaluation/` — Model evaluation (1 file)
- `app/api/` — API routes and schemas (2 files)
- `app/config/` — Configuration (1 file)
- `app/utils/` — Utilities (3 files)

### 13.2 Key Classes

- `VehicleDetector` — Wraps YOLO for traffic-relevant detection
- `VehicleTracker` — Manages track state and trajectories
- `ViolationEngine` — Orchestrates rule evaluation with cooldown
- `VideoProcessor` — End-to-end processing pipeline
- `AnalyticsService` — Database aggregation for charts

---

## 14. Database Design

SQLite database with 3 tables:

1. **processing_sessions** — One row per uploaded file
2. **detections** — Individual object detections (sampled)
3. **violations** — Violation events with evidence paths

See `docs/diagrams/er_diagram.md` for the full ER diagram.

---

## 15. User Interface

The web interface includes 6 pages:
1. **Home** — Project overview with feature cards and CV pipeline
2. **Upload** — Drag-and-drop file upload with configuration
3. **Processing** — Live progress tracking for video analysis
4. **Violations** — Filterable violation table with evidence modal
5. **Analytics** — Chart.js dashboard with real data
6. **Evaluation** — Model metrics and inference benchmarks

---

## 16. Screenshots / Results

> **Placeholder**: Insert screenshots after running the application with a traffic video.
>
> Recommended screenshots:
> - Home page
> - Upload page with detected image
> - Processing page with live stats
> - Violations table with evidence
> - Analytics dashboard with charts
> - Evaluation page with metrics

---

## 17. Testing Approach

Tests are implemented using pytest across 7 test files with 50+ test cases:

- **test_detector.py** — Detection dataclass, model state
- **test_tracker.py** — Tracking, trajectories, displacement
- **test_violations.py** — Red-light, speed, helmet rules, engine cooldown
- **test_database.py** — Schema, CRUD, filtering
- **test_preprocessing.py** — Resize, blur, normalise, frame extraction
- **test_validators.py** — Extension, size, content validation
- **test_api.py** — Page routes, API endpoints, error handling

Model-dependent tests use mocked detections or synthetic frames.

---

## 18. Evaluation Methodology

See `docs/evaluation.md` for full details. The system supports:
- **Dataset evaluation**: mAP@0.5, mAP@0.5:0.95, precision, recall
- **Inference benchmarking**: Average latency (ms) and FPS

**Evaluation pending dataset/model execution** — no results have been fabricated.

---

## 19. Challenges Faced

1. **Model size vs performance** — Balancing detection accuracy with CPU inference speed
2. **Tracking continuity** — Vehicles can be lost during occlusion or rapid movement
3. **Violation accuracy** — Pixel-based speed estimation lacks real-world calibration
4. **Signal state** — Automatic traffic-light recognition requires a dedicated model
5. **Testing without GPU** — Unit tests mock the model to avoid GPU dependency

---

## 20. Learnings & Key Takeaways

1. YOLO's single-stage architecture enables practical real-time detection
2. Multi-object tracking adds significant value over frame-independent detection
3. Rule-based violation detection is transparent and explainable
4. Modular architecture enables independent development and testing of components
5. Preprocessing choices directly impact detection quality
6. Real-world deployment requires camera calibration and perspective transformation

---

## 21. Limitations

1. **Camera angle sensitivity** — Detection accuracy varies with viewing angle
2. **Occlusion** — Partially hidden vehicles may be missed
3. **Weather/lighting** — Night, rain, and glare reduce performance
4. **Speed estimation** — Pixel displacement ≠ real-world speed (requires calibration)
5. **Traffic light state** — Simulated, not automatically detected
6. **Helmet detection** — Not available in standard COCO-pretrained models
7. **Single camera** — No multi-camera fusion
8. **Model generalization** — Performance depends on training data similarity

---

## 22. Future Enhancements

1. Camera calibration and perspective transformation
2. Real-world speed estimation using homography
3. Automatic traffic-light state recognition (dedicated model)
4. Custom helmet detection model training
5. License plate recognition (OCR)
6. Multi-camera support with cross-camera tracking
7. Cloud deployment with GPU inference
8. Alert/notification system
9. Advanced tracking (DeepSORT with re-identification)
10. Model fine-tuning on traffic-specific datasets
11. Edge device deployment (NVIDIA Jetson)
12. Mobile application

---

## 23. References

1. Redmon, J., et al. "You Only Look Once: Unified, Real-Time Object Detection." CVPR 2016.
2. Jocher, G., et al. "Ultralytics YOLOv8." https://github.com/ultralytics/ultralytics
3. Zhang, Y., et al. "ByteTrack: Multi-Object Tracking by Associating Every Detection Box." ECCV 2022.
4. Lin, T., et al. "Microsoft COCO: Common Objects in Context." ECCV 2014.
5. OpenCV Documentation. https://docs.opencv.org/
6. FastAPI Documentation. https://fastapi.tiangolo.com/
7. SQLite Documentation. https://www.sqlite.org/docs.html

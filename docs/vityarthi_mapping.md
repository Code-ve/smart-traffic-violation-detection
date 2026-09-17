# VITyarthi Evaluation Mapping

This document maps the VITyarthi Build Your Own Project evaluation requirements to specific implementations in this project.

## Requirement Mapping

| Evaluation Requirement | Project Implementation | Location |
|---|---|---|
| **Problem Understanding** | Traffic violation detection — detecting vehicles and identifying rule violations from traffic footage | `statement.md`, `docs/project_report.md` §1-3 |
| **Functional Modules** | 8 modules: Input Processing, Detection, Tracking, Violation Engine, Evidence, Violation Management, Analytics, Evaluation | `app/cv/`, `app/violations/`, `app/analytics/`, `app/evaluation/` |
| **Non-functional Requirements** | Performance (FPS tracking), Security (upload validation), Reliability (error handling), Usability (web UI), Scalability (modular detector), Maintainability (separated layers) | `app/utils/validators.py`, `app/utils/exceptions.py`, `docs/design-decisions.md` |
| **Architecture** | Layered CV architecture: UI → API → Processing Pipeline → Storage | `docs/architecture.md`, `docs/diagrams/architecture.md` |
| **Workflow** | Input → Validation → Preprocessing → Detection → Tracking → Violation Analysis → Evidence → Storage → Analytics | `docs/workflow.md`, `docs/diagrams/workflow.md` |
| **Computer Vision Concepts** | YOLO object detection, OpenCV preprocessing, ByteTrack tracking, bounding boxes, confidence scores, mAP evaluation | `app/cv/detector.py`, `app/cv/preprocessing.py`, `app/cv/tracker.py` |
| **Design Diagrams** | Use Case, Workflow, Architecture, Sequence, Component, ER diagrams (Mermaid) | `docs/diagrams/` (6 diagram files) |
| **Database Design** | SQLite with 3 normalised tables: processing_sessions, detections, violations | `app/database/database.py`, `docs/diagrams/er_diagram.md` |
| **Testing** | 7 test files, 50+ test cases using pytest with mocked model, temp DB fixtures | `tests/` |
| **Git Readiness** | Clean `.gitignore`, no generated files, modular structure, MIT license | `.gitignore`, `LICENSE` |
| **Documentation** | README, problem statement, architecture, design decisions, project report, evaluation methodology | `README.md`, `statement.md`, `docs/` |
| **Model Selection** | YOLO chosen for real-time inference, accuracy–speed tradeoff, Ultralytics ecosystem | `docs/design-decisions.md` |
| **Evaluation** | mAP@0.5, mAP@0.5:0.95, precision, recall, inference FPS, model info | `app/evaluation/evaluate.py`, `scripts/evaluate_model.py` |

## Computer Vision Concepts Demonstrated

| CV Concept | Implementation |
|---|---|
| Object Detection | YOLO model inference via Ultralytics framework |
| Bounding Boxes | Drawn on frames with class labels and confidence scores |
| Confidence Scoring | Configurable threshold, displayed in UI and stored in DB |
| Non-Maximum Suppression | IoU threshold configured via `IOU_THRESHOLD` |
| Multi-Object Tracking | ByteTrack via Ultralytics `.track()` method |
| Persistent Track IDs | Assigned by tracker, used for violation logic |
| Vehicle Trajectories | Accumulated per track, visualised as polylines |
| Image Preprocessing | Resize, blur, brightness, normalisation, colour conversion |
| Frame Extraction | Video → frames with configurable skip rate |
| Model Evaluation | Precision, Recall, mAP computed via Ultralytics `.val()` |
| Inference Benchmarking | Average latency and FPS measurement |
| Evidence Annotation | Overlay: bounding box + violation type + track ID + timestamp |

## Module-to-File Mapping

| Module | Key Files |
|---|---|
| Input Processing | `app/cv/video_processor.py`, `app/utils/validators.py` |
| Object Detection | `app/cv/detector.py` |
| Preprocessing | `app/cv/preprocessing.py` |
| Object Tracking | `app/cv/tracker.py` |
| Violation Engine | `app/violations/engine.py`, `app/violations/red_light.py`, `app/violations/speed_zone.py`, `app/violations/helmet.py` |
| Evidence Generation | `app/cv/visualization.py` |
| Database | `app/database/database.py`, `app/database/repository.py` |
| Analytics | `app/analytics/statistics.py` |
| Evaluation | `app/evaluation/evaluate.py` |
| Web Interface | `app/api/routes.py`, `frontend/templates/`, `frontend/static/` |
| Configuration | `app/config/settings.py` |
| Logging | `app/utils/logger.py` |
| Error Handling | `app/utils/exceptions.py` |

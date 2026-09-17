# Design Decisions & Rationale

## Model Selection: YOLO

### Why Object Detection over Image Classification?

Image classification answers "What is in this image?" — but traffic monitoring requires "Where is each vehicle and what type is it?" Object detection provides both classification and localisation (bounding boxes), which are essential for:
- Counting individual vehicles
- Tracking vehicles across frames
- Determining spatial relationships (e.g., crossing a stop line)

### Why YOLO?

| Criterion | YOLO | Faster R-CNN | SSD |
|---|---|---|---|
| Speed | ✅ Very fast (real-time) | ❌ Slower | ⚠️ Medium |
| Accuracy | ✅ Good (v8+) | ✅ High | ⚠️ Lower |
| Single-stage | ✅ Yes | ❌ Two-stage | ✅ Yes |
| Ease of use | ✅ Ultralytics API | ❌ Complex setup | ⚠️ Medium |
| Tracking support | ✅ Built-in | ❌ Separate | ❌ Separate |
| Community | ✅ Large | ✅ Large | ⚠️ Declining |

YOLO (You Only Look Once) was chosen because:
1. **Real-time inference** — critical for video processing at reasonable FPS
2. **Single-stage architecture** — simpler to understand and explain in academic context
3. **Ultralytics ecosystem** — provides `.track()` with built-in ByteTrack, model download, and `.val()` for evaluation
4. **Model flexibility** — can swap between YOLOv8 nano (fast) and larger models (accurate) without code changes

### Accuracy vs Speed Tradeoff

| Model | Size | Parameters | Speed (CPU) | mAP@0.5 |
|---|---|---|---|---|
| YOLOv8n | 6 MB | 3.2M | ~80ms | 37.3 |
| YOLOv8s | 22 MB | 11.2M | ~150ms | 44.9 |
| YOLOv8m | 52 MB | 25.9M | ~320ms | 50.2 |

We default to **YOLOv8n** (nano) for:
- Small download size (~6 MB)
- Reasonable CPU inference speed
- Adequate accuracy for demonstration
- Users can switch to larger models for better accuracy

## Tracking: ByteTrack

ByteTrack was chosen over alternatives (DeepSORT, SORT) because:
1. Built into Ultralytics — no additional dependencies
2. Uses only bounding box IoU — no separate appearance model needed
3. Good performance on traffic scenarios
4. Simple to understand and explain

## Database: SQLite

SQLite was chosen over PostgreSQL/MySQL because:
1. Zero configuration — no server to install
2. Single file — easy to distribute and backup
3. Sufficient performance for prototype-scale data
4. Python stdlib support (`sqlite3`)

## Web Framework: FastAPI

FastAPI was chosen over Flask/Django because:
1. Async support for background video processing
2. Automatic OpenAPI documentation
3. Pydantic integration for request/response validation
4. Lightweight — no unnecessary complexity

## Violation Detection: Rule-based

Rule-based detection was chosen over ML-based violation classification because:
1. Explainable — each rule can be clearly documented and understood
2. No additional training data needed
3. Configurable — thresholds can be adjusted at runtime
4. Transparent — violations can be traced to specific rules
5. Appropriate for academic prototype scope

## Frontend: Server-rendered Templates

Jinja2 templates + vanilla JS were chosen over React/Vue/Angular because:
1. No build step — simpler project setup
2. Easier for students to understand and explain in viva
3. Single deployment — frontend served by the same FastAPI server
4. Sufficient for the dashboard UI requirements

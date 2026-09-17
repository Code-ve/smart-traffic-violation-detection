# Smart Traffic Violation Detection & Analytics System

A Computer Vision system for detecting and analyzing traffic violations using YOLO object detection, multi-object tracking, and rule-based violation analysis. Built as an academic prototype for the VITyarthi Build Your Own Project evaluation.

---

## Overview

This system processes traffic images and videos to:

1. **Detect** vehicles and relevant objects using YOLO
2. **Track** vehicles across video frames with persistent IDs
3. **Identify** configurable traffic violations (red-light, speed/zone)
4. **Generate** annotated evidence images for each violation
5. **Store** all events in a structured SQLite database
6. **Visualize** traffic analytics through an interactive web dashboard
7. **Evaluate** model performance with standard CV metrics

## Problem

Traffic violations contribute significantly to road accidents. Manual monitoring is limited in scale and consistency. Automated detection systems can assist by processing surveillance footage to identify violations continuously and objectively.

This project demonstrates how Computer Vision techniques can be applied to traffic violation detection as an academic prototype.

## Objectives

- Implement real-time vehicle detection using YOLO
- Track vehicles across video frames with persistent IDs and trajectories
- Build a configurable, explainable violation detection engine
- Generate annotated evidence for each detected violation
- Provide analytics from real processing data
- Document and evaluate the system academically

## Features

| Feature | Description |
|---|---|
| 🔍 Object Detection | YOLO-powered detection of cars, trucks, buses, motorcycles, bicycles, persons |
| 🎯 Vehicle Tracking | ByteTrack multi-object tracking with persistent IDs and trajectories |
| 🔴 Red-Light Violation | Virtual stop line with configurable signal state |
| ⚡ Speed/Zone Violation | Pixel displacement-based prototype speed estimation |
| ⛑️ Helmet Violation | Optional — auto-disables if model lacks helmet classes |
| 📸 Evidence Capture | Annotated violation frames with metadata overlay |
| 📊 Analytics Dashboard | Interactive Chart.js charts from real database data |
| 📈 Model Evaluation | mAP, precision, recall, and inference benchmarks |
| 🖥️ Web Interface | Clean, modern dark-themed UI with 6 pages |

## Computer Vision Pipeline

```
Input → Validation → Preprocessing → YOLO Detection → ByteTrack Tracking
    → Violation Rule Engine → Evidence Generation → SQLite Storage → Analytics
```

### Preprocessing Operations

| Operation | Purpose |
|---|---|
| Resize | Reduce resolution for faster inference while preserving aspect ratio |
| Gaussian Blur | Reduce noise in low-quality CCTV footage |
| Brightness Adjustment | Compensate for poor lighting conditions |
| Colour Conversion | BGR ↔ RGB conversion for model compatibility |

## System Architecture

```
┌──────────────────────────────────────┐
│       Web Interface (HTML/CSS/JS)    │
├──────────────────────────────────────┤
│       FastAPI REST API               │
├──────────────────────────────────────┤
│       Video Processor                │
│       ├── Preprocessing Pipeline     │
│       ├── YOLO Detector              │
│       ├── ByteTrack Tracker          │
│       └── Visualizer                 │
├──────────────────────────────────────┤
│       Violation Engine + Analytics   │
├──────────────────────────────────────┤
│       SQLite Database + File System  │
└──────────────────────────────────────┘
```

See `docs/architecture.md` and `docs/diagrams/` for detailed Mermaid diagrams.

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| Object Detection | Ultralytics YOLO (v8/v11) |
| Tracking | ByteTrack (via Ultralytics) |
| Image Processing | OpenCV, NumPy |
| Web Framework | FastAPI + Uvicorn |
| Frontend | HTML/CSS/JS + Jinja2 + Chart.js |
| Database | SQLite |
| Data Analysis | Pandas, Matplotlib |
| Testing | pytest |
| Configuration | Pydantic Settings + python-dotenv |

## Project Structure

```
smart-traffic-violation-detection/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   ├── routes.py              # All API endpoints
│   │   └── schemas.py             # Pydantic request/response models
│   ├── cv/
│   │   ├── detector.py            # YOLO detection wrapper
│   │   ├── tracker.py             # ByteTrack tracking wrapper
│   │   ├── preprocessing.py       # Frame preprocessing pipeline
│   │   ├── video_processor.py     # End-to-end processing pipeline
│   │   └── visualization.py       # Drawing and evidence generation
│   ├── violations/
│   │   ├── base.py                # Abstract violation rule
│   │   ├── engine.py              # Violation rule orchestrator
│   │   ├── red_light.py           # Red-light violation rule
│   │   ├── speed_zone.py          # Speed/zone violation rule
│   │   └── helmet.py              # Helmet violation rule (optional)
│   ├── database/
│   │   ├── database.py            # SQLite connection + schema
│   │   └── repository.py          # CRUD operations
│   ├── analytics/
│   │   └── statistics.py          # Aggregation queries
│   ├── evaluation/
│   │   └── evaluate.py            # mAP, precision, recall, benchmarks
│   ├── config/
│   │   └── settings.py            # Configuration management
│   └── utils/
│       ├── logger.py              # Logging setup
│       ├── exceptions.py          # Custom exceptions
│       └── validators.py          # Upload validation
├── frontend/
│   ├── templates/                 # 6 Jinja2 HTML templates
│   └── static/                    # CSS, JS, images
├── tests/                         # 7 test files, 50+ test cases
├── data/                          # Input, output, evidence directories
├── models/                        # YOLO model weights (gitignored)
├── docs/                          # Documentation + Mermaid diagrams
├── scripts/                       # Setup, demo, evaluation scripts
├── requirements.txt
├── .env.example
├── .gitignore
├── statement.md
├── LICENSE
└── README.md
```

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-username/smart-traffic-violation-detection.git
cd smart-traffic-violation-detection

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy environment configuration
cp .env.example .env

# 6. Initialize database
python scripts/setup_db.py
```

## Model Setup

The system requires a YOLO model. The default configuration expects `models/yolov8n.pt`.

### Option A: Automatic download (recommended)

The Ultralytics framework will automatically download `yolov8n.pt` on first run if it's not found locally.

### Option B: Manual download

```bash
# Download YOLOv8 nano
pip install ultralytics
yolo export model=yolov8n.pt format=pt
# Move to models/ directory
```

### Using a different model

Edit `.env` or set the environment variable:

```
MODEL_PATH=models/yolov8s.pt
```

Any Ultralytics-compatible YOLO model can be used.

## Dataset

This system works with any traffic images or videos. Place files in `data/input/`.

### Recommended public datasets

| Dataset | Description | URL |
|---|---|---|
| COCO 2017 | General detection (includes vehicles) | cocodataset.org |
| UA-DETRAC | Traffic-specific detection & tracking | detrac-db.rit.albany.edu |
| BDD100K | Diverse driving scenarios | bdd-data.berkeley.edu |

### Custom videos

Place any traffic video (MP4, AVI, MOV, MKV) in `data/input/` and upload through the web interface.

**Note**: Do not commit large video files to Git.

## Running the Application

```bash
# Start the web server
python -m app.main
```

Open your browser to **http://localhost:8000**

### Pages

| URL | Description |
|---|---|
| `/` | Home page |
| `/upload` | Upload and analyze images/videos |
| `/violations` | View and manage detected violations |
| `/analytics` | Interactive analytics dashboard |
| `/evaluation` | Model performance metrics |

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_violations.py -v

# Run with coverage (if coverage is installed)
pytest --cov=app tests/
```

## Model Evaluation

```bash
# Inference benchmark (no dataset needed)
python scripts/evaluate_model.py

# Full evaluation with dataset
python scripts/evaluate_model.py --dataset path/to/data.yaml

# Custom model
python scripts/evaluate_model.py --model models/yolov8s.pt
```

## Example Workflow

1. **Start the application**: `python -m app.main`
2. **Upload a video**: Go to `/upload`, drag a traffic video, click upload
3. **Configure signal**: Set signal state to RED to test red-light violations
4. **Process**: The system detects vehicles, tracks them, and checks for violations
5. **View violations**: Go to `/violations` to see detected violations with evidence
6. **Analytics**: Go to `/analytics` to see charts and statistics
7. **Evaluation**: Go to `/evaluation` to see model info and run benchmarks

### Command-line demo

```bash
python scripts/run_demo.py --input data/input/traffic_video.mp4 --signal RED
```

## Performance Considerations

- **Frame skipping**: Set `FRAME_SKIP=2` or higher for faster processing
- **Model size**: Use `yolov8n.pt` for CPU, `yolov8s.pt` or larger for GPU
- **Resolution**: `MAX_RESOLUTION=640` reduces memory usage
- **GPU**: CUDA-enabled GPU dramatically improves inference speed

## Limitations

| Limitation | Explanation |
|---|---|
| Camera angle | Detection accuracy varies with viewing angle |
| Occlusion | Partially hidden vehicles may be missed |
| Weather/lighting | Night, rain, and glare reduce performance |
| Speed estimation | Pixel displacement ≠ real-world speed (requires calibration) |
| Traffic light state | Simulated, not automatically detected |
| Helmet detection | Not available in COCO-pretrained models |
| Single camera | No multi-camera fusion |

**Important**: This is an academic prototype. Speed/zone violation detection uses pixel-based estimation and should NOT be presented as legally valid enforcement.

## Future Enhancements

- [ ] Camera calibration and perspective transformation
- [ ] Real-world speed estimation using homography
- [ ] Automatic traffic-light state recognition
- [ ] Custom helmet detection model
- [ ] License plate recognition (OCR)
- [ ] Multi-camera support
- [ ] Cloud deployment with GPU inference
- [ ] Alert/notification system
- [ ] Model fine-tuning on traffic datasets
- [ ] Edge device deployment (NVIDIA Jetson)

## Screenshots

![Targetted image](<Screenshot 2026-09-17 221649.png>) ----->![Analyzed version](<Screenshot 2026-09-17 222923.png>)

## DEMO Video
   https://drive.google.com/file/d/1xjtyBu9cKYK7tKhouwYcVRgl_WVlZ5L2/view?usp=sharing 
## Academic Relevance

This project demonstrates practical application of:

- **Object Detection** — YOLO architecture, bounding boxes, confidence scores, NMS
- **Multi-Object Tracking** — ByteTrack, persistent IDs, trajectory analysis
- **Image Preprocessing** — Resize, blur, colour conversion, normalisation
- **Model Evaluation** — mAP, precision, recall, inference benchmarking
- **Computer Vision Pipeline** — End-to-end from raw video to structured analytics
- **Software Engineering** — Modular architecture, testing, documentation, version control

See `docs/vityarthi_mapping.md` for the complete evaluation requirement mapping.


## License

MIT License — see [LICENSE](LICENSE) for details.

##MADE BY:
  Name: Pradyumn Krishna Arya
  Reg No.: 24BAI10668

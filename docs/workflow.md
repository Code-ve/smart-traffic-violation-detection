# Processing Workflow

## Overview

The system processes traffic images and videos through a multi-stage Computer Vision pipeline.

## Image Processing Workflow

1. **Input** → User uploads an image via the web interface
2. **Validation** → File extension, size, and content checks
3. **Preprocessing** → Resize to max dimension while preserving aspect ratio
4. **Detection** → YOLO model inference producing bounding boxes + class labels + confidence
5. **Annotation** → Draw bounding boxes, labels, and confidence on the frame
6. **Storage** → Save detections to SQLite, save annotated image to output directory
7. **Response** → Return detection results and annotated image to the user

## Video Processing Workflow

1. **Input** → User uploads a video file
2. **Validation** → File type and size checks
3. **Session Creation** → Create a processing session in the database
4. **Frame Loop** (for each frame):
   - **Read** → Extract frame from video
   - **Preprocess** → Resize, optional blur/brightness adjustment
   - **Detect + Track** → YOLO inference with ByteTrack tracking (`.track()`)
   - **Track Update** → Update trajectory history and displacement
   - **Violation Check** → Run all enabled rules against current detections
   - **Evidence** → If violation detected, generate and save evidence image
   - **Annotate** → Draw boxes, tracks, trajectories, stats overlay
   - **Write** → Write annotated frame to output video
   - **Progress** → Update processing progress for UI polling
5. **Completion** → Update session with final statistics
6. **Output** → Annotated video saved, violations stored, analytics available

See [Workflow Diagram](diagrams/workflow.md) for the Mermaid visualization.

# Evaluation Methodology

## Object Detection Metrics

### Precision
**Definition**: Of all detections the model predicted, what fraction were correct?

```
Precision = True Positives / (True Positives + False Positives)
```

High precision means few false alarms — the model rarely detects something that isn't there.

### Recall
**Definition**: Of all actual objects in the image, what fraction did the model detect?

```
Recall = True Positives / (True Positives + False Negatives)
```

High recall means the model misses few objects.

### mAP@0.5 (Mean Average Precision at IoU 0.5)
A detection is considered "correct" if its bounding box overlaps with the ground truth by at least 50% (IoU ≥ 0.5). The Average Precision (AP) is computed for each class, and mAP is the mean across all classes.

### mAP@0.5:0.95
A stricter metric — evaluates at multiple IoU thresholds (0.5, 0.55, 0.60, ..., 0.95) and averages. This penalises imprecise bounding boxes more heavily.

## Inference Performance Metrics

| Metric | Description |
|---|---|
| Average Inference Time (ms) | Mean time for one frame through the YOLO model |
| FPS | Frames per second = 1000 / avg_inference_ms |
| Model Size (MB) | Storage footprint of the weights file |
| Resolution | Input image dimensions used for benchmarking |

## Running Evaluation

### Dataset Evaluation (requires labelled dataset)

```bash
python scripts/evaluate_model.py --model models/yolov8n.pt --dataset path/to/data.yaml
```

### Inference Benchmark (no dataset needed)

```bash
python scripts/evaluate_model.py --model models/yolov8n.pt --num-synthetic 50
```

## Expected Dataset Format

The evaluation uses YOLO-format datasets with a YAML configuration:

```yaml
path: /path/to/dataset
train: images/train
val: images/val
names:
  0: person
  1: bicycle
  2: car
  3: motorcycle
  5: bus
  7: truck
```

Images should be in `images/val/` and labels in `labels/val/` (YOLO txt format: `class x_center y_center width height`).

## Recommended Datasets

| Dataset | Classes | Size | Use Case |
|---|---|---|---|
| COCO 2017 (val) | 80 (includes vehicles) | ~1 GB | General evaluation |
| UA-DETRAC | Vehicles | ~10 GB | Traffic-specific |
| BDD100K | Vehicles + pedestrians | ~7 GB | Diverse driving |

## Current Evaluation Status

**Evaluation pending dataset/model execution.**

The evaluation framework is fully implemented and will produce real metrics when run with a dataset. No numbers have been fabricated.

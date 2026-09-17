#!/usr/bin/env python
"""
Model evaluation CLI script.

Usage:
    python scripts/evaluate_model.py                    # Benchmark only
    python scripts/evaluate_model.py --dataset data.yaml  # Full evaluation
    python scripts/evaluate_model.py --model models/yolov8s.pt  # Custom model
"""

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.evaluation.evaluate import ModelEvaluator
from app.config.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate YOLO model performance")
    parser.add_argument("--model", type=str, default=None, help="Path to YOLO model")
    parser.add_argument("--dataset", type=str, default=None, help="Path to dataset YAML")
    parser.add_argument("--images", nargs="*", help="Image paths for benchmark")
    parser.add_argument("--num-synthetic", type=int, default=20, help="Synthetic frames for benchmark")
    args = parser.parse_args()

    settings = get_settings()
    model_path = args.model or settings.model_path
    evaluator = ModelEvaluator()

    print(f"\n{'=' * 60}")
    print(f"  Model Evaluation — {os.path.basename(model_path)}")
    print(f"{'=' * 60}\n")

    # Model info
    print("📋 Model Information:")
    info = evaluator.get_model_info(model_path)
    for k, v in info.items():
        if k != "class_names":
            print(f"   {k}: {v}")
    if info.get("class_names"):
        print(f"   classes: {', '.join(info['class_names'][:15])}{'...' if len(info.get('class_names', [])) > 15 else ''}")

    # Dataset evaluation
    print(f"\n📊 Dataset Evaluation:")
    metrics = evaluator.evaluate_model(model_path, args.dataset)
    for k, v in metrics.items():
        print(f"   {k}: {v}")

    # Inference benchmark
    print(f"\n⚡ Inference Benchmark:")
    bench = evaluator.benchmark_inference(
        model_path, args.images, num_synthetic=args.num_synthetic,
    )
    for k, v in bench.items():
        print(f"   {k}: {v}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()

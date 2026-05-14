#!/usr/bin/env python3
"""Run Surya OCR on one PNG, dump recognized lines top-to-bottom in reading order.

Usage: python run_surya.py <png_path>
"""

import sys
from pathlib import Path

from PIL import Image
from surya.detection import DetectionPredictor
from surya.foundation import FoundationPredictor
from surya.recognition import RecognitionPredictor

if len(sys.argv) < 2:
    print("usage: run_surya.py <png>", file=sys.stderr)
    sys.exit(2)

img_path = Path(sys.argv[1])
img = Image.open(img_path).convert("RGB")

print("Loading Surya predictors (foundation + recognition + detection)...", file=sys.stderr)
foundation = FoundationPredictor()
recognition = RecognitionPredictor(foundation)
detection = DetectionPredictor()

print(f"Running OCR on {img_path.name} ({img.size})...", file=sys.stderr)
results = recognition([img], task_names=["ocr_with_boxes"], det_predictor=detection, sort_lines=True)

result = results[0]
# result.text_lines is a list of TextLine objects with .text and .bbox
for line in result.text_lines:
    print(line.text)

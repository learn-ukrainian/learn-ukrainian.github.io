import pytest
import re
from datetime import datetime, timedelta
from pathlib import Path

def calculate_weighted_overall(scores):
    """
    Implements the weighted overall score calculation from phase-5-review.md.

    Overall = (Experience × 1.5 + Coherence × 1.0 + Relevance × 1.0 + Educational × 1.2 +
              Language × 1.1 + Pedagogy × 1.2 + Immersion × 1.0 + Activities × 1.3 +
              Richness × 0.9 + Beginner_Safety × 1.3 + LLM × 1.0 + Linguistic_Accuracy × 1.5) / 14.0
    """
    weights = {
        "Experience": 1.5, "Coherence": 1.0, "Relevance": 1.0, "Educational": 1.2,
        "Language": 1.1, "Pedagogy": 1.2, "Immersion": 1.0, "Activities": 1.3,
        "Richness": 0.9, "Beginner_Safety": 1.3, "LLM": 1.0, "Linguistic_Accuracy": 1.5
    }

    total_weighted = sum(scores[dim] * weights[dim] for dim in weights)
    return round(total_weighted / 14.0, 1)

def check_auto_fail(scores):
    """
    Checks if any dimension is below its auto-fail threshold.
    """
    thresholds = {
        "Experience": 7, "Coherence": 7, "Relevance": 7, "Educational": 7,
        "Language": 8, "Pedagogy": 7, "Immersion": 6, "Activities": 7,
        "Richness": 6, "Beginner_Safety": 7, "LLM": 7, "Linguistic_Accuracy": 9
    }

    failed_dims = []
    for dim, threshold in thresholds.items():
        if scores[dim] < threshold:
            failed_dims.append(dim)
    return failed_dims

def test_scoring_logic():
    # Perfect scores
    scores = {
        "Experience": 10, "Coherence": 10, "Relevance": 10, "Educational": 10,
        "Language": 10, "Pedagogy": 10, "Immersion": 10, "Activities": 10,
        "Richness": 10, "Beginner_Safety": 10, "LLM": 10, "Linguistic_Accuracy": 10
    }
    assert calculate_weighted_overall(scores) == 10.0
    assert len(check_auto_fail(scores)) == 0

    # Low Language score (auto-fail Language < 8)
    scores["Language"] = 7
    assert len(check_auto_fail(scores)) > 0
    assert "Language" in check_auto_fail(scores)

    # Low Linguistic Accuracy (auto-fail < 9)
    scores["Language"] = 10
    scores["Linguistic_Accuracy"] = 8
    assert "Linguistic_Accuracy" in check_auto_fail(scores)

def is_review_stale(review_path, module_path):
    """
    Checks if a review is older than the module it reviews.
    """
    if not review_path.exists() or not module_path.exists():
        return False

    review_time = review_path.stat().st_mtime
    module_time = module_path.stat().st_mtime

    return review_time < module_time

def test_stale_review_detection(tmp_path):
    module_file = tmp_path / "module.md"
    review_file = tmp_path / "review.md"

    # Create module first
    module_file.write_text("v1")
    # Wait a tiny bit or manually set time
    mtime_v1 = datetime.now().timestamp() - 10
    import os
    os.utime(module_file, (mtime_v1, mtime_v1))

    # Create review
    review_file.write_text("review of v1")
    mtime_review = datetime.now().timestamp()
    os.utime(review_file, (mtime_review, mtime_review))

    assert not is_review_stale(review_file, module_file)

    # Update module
    module_file.write_text("v2")
    mtime_v2 = datetime.now().timestamp() + 10
    os.utime(module_file, (mtime_v2, mtime_v2))

    assert is_review_stale(review_file, module_file)

def test_naturalness_scoring():
    # Naturalness scoring logic (from evaluate_naturalness)
    from scripts.audit.gates import evaluate_naturalness

    # PASS >= 8
    assert evaluate_naturalness(8, "PASS").status == "PASS"
    assert evaluate_naturalness(7, "PASS").status == "FAIL"
    # PENDING is INFO
    assert evaluate_naturalness(0, "PENDING").status == "INFO"

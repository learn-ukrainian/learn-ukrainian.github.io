import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from scripts.batch_fix_review import (
    extract_section,
    extract_score,
    extract_status,
    assemble_fix_prompt,
    assemble_review_prompt
)

def test_extract_section():
    content = """
Some text
===START===
Target content
===END===
More text
"""
    # Create a temp file
    with open("temp_output.txt", "w") as f:
        f.write(content)

    section = extract_section(Path("temp_output.txt"), "===START===", "===END===")
    assert section == "Target content"
    Path("temp_output.txt").unlink()

def test_extract_section_with_code_blocks():
    content = """
```
===START===
Target content
===END===
```
"""
    with open("temp_output.txt", "w") as f:
        f.write(content)

    section = extract_section(Path("temp_output.txt"), "===START===", "===END===")
    assert section == "Target content"
    Path("temp_output.txt").unlink()

def test_extract_score():
    assert extract_score("**Overall Score:** 9.5/10") == 9.5
    assert extract_score("Overall Score: 8/10") == 8.0
    assert extract_score("= **9.0/10**") == 9.0
    assert extract_score("No score here") is None

def test_extract_status():
    assert extract_status("**Status:** PASS") == "PASS"
    assert extract_status("**Status:** FAIL") == "FAIL"
    assert extract_status("Status: UNKNOWN") == "UNKNOWN"

@patch("pathlib.Path.read_text")
@patch("pathlib.Path.mkdir")
@patch("pathlib.Path.write_text")
def test_assemble_fix_prompt(mock_write, mock_mkdir, mock_read):
    mock_read.return_value = "Fix {REVIEW_PATH} in {CONTENT_PATH}"
    files = {
        "content": Path("content.md"),
        "activities": Path("activities.yaml"),
        "vocabulary": Path("vocab.yaml"),
        "plan": Path("plan.yaml"),
        "research": Path("research.md"),
        "orchestration": Path("orch/"),
    }
    review_path = Path("review.md")

    assemble_fix_prompt(files, review_path)

    # Check if write_text was called with replaced values
    args, _ = mock_write.call_args
    assert "review.md" in args[0]
    assert "content.md" in args[0]

@patch("scripts.batch_fix_review.get_audit_metrics")
@patch("scripts.batch_fix_review.count_items")
@patch("scripts.batch_fix_review.count_engagement")
@patch("scripts.batch_fix_review.get_module_title")
@patch("pathlib.Path.read_text")
@patch("pathlib.Path.mkdir")
@patch("pathlib.Path.write_text")
def test_assemble_review_prompt(mock_write, mock_mkdir, mock_read, mock_title, mock_eng, mock_items, mock_metrics):
    mock_read.return_value = "Review {CONTENT_PATH} with {AUDIT_WORD_COUNT} words"
    mock_metrics.return_value = {"audit_words": 1200, "word_percent": "120%", "overall_status": "PASS"}
    mock_items.return_value = 10
    mock_eng.return_value = 5
    mock_title.return_value = "Test Title"

    files = {
        "num": 1,
        "content": Path("content.md"),
        "activities": Path("activities.yaml"),
        "vocabulary": Path("vocab.yaml"),
        "plan": Path("plan.yaml"),
        "meta": Path("meta.yaml"),
        "research": Path("research.md"),
        "orchestration": Path("orch/"),
    }

    assemble_review_prompt(files, "a1")

    args, _ = mock_write.call_args
    assert "content.md" in args[0]
    assert "1200" in args[0]

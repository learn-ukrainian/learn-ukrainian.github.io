import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import shutil
import tempfile
from scripts.batch_fix_review import process_module

@pytest.fixture
def mock_repo(tmp_path):
    # Setup a mock repo structure
    repo = tmp_path / "repo"
    repo.mkdir()

    level_dir = repo / "curriculum/l2-uk-en/a1"
    level_dir.mkdir(parents=True)

    (level_dir / "activities").mkdir()
    (level_dir / "vocabulary").mkdir()
    (level_dir / "status").mkdir()
    (level_dir / "review").mkdir()
    (level_dir / "orchestration").mkdir()

    # Create a sample module
    content = "# Test Module\n\nContent here."
    (level_dir / "01-test.md").write_text(content)

    # Mock other files
    (level_dir / "activities/01-test.yaml").write_text("- type: quiz")
    (level_dir / "vocabulary/01-test.yaml").write_text("items: []")

    # Create mock templates
    template_dir = repo / "claude_extensions/phases/gemini"
    template_dir.mkdir(parents=True)
    (template_dir / "phase-fix.md").write_text("Fix {REVIEW_PATH}")
    (template_dir / "phase-5-review.md").write_text("Review {CONTENT_PATH} {AUDIT_WORD_COUNT}")

    return repo

@patch("scripts.batch_fix_review.REPO")
@patch("scripts.batch_fix_review.call_gemini_review")
@patch("scripts.batch_fix_review.run_audit")
def test_process_module_already_pass(mock_audit, mock_review, mock_repo_path, mock_repo):
    mock_repo_path.return_value = mock_repo
    # Mock an existing passing review
    orch_dir = mock_repo / "curriculum/l2-uk-en/a1/orchestration/test"
    orch_dir.mkdir(parents=True)
    (orch_dir / "phase-5-response.md").write_text("**Overall Score:** 9.5/10\n**Status:** PASS")

    with patch("scripts.batch_fix_review.REPO", mock_repo):
        result = process_module("a1", 1, "mock-model")

    assert result["status"] == "ALREADY_PASS"
    assert result["score"] == 9.5

@patch("scripts.batch_fix_review.REPO")
@patch("scripts.batch_fix_review.call_gemini_review")
@patch("scripts.batch_fix_review.call_gemini")
@patch("scripts.batch_fix_review.run_audit")
def test_process_module_fix_loop(mock_audit, mock_fix, mock_review, mock_repo_path, mock_repo):
    mock_repo_path.return_value = mock_repo

    # Initial review: FAIL (8.0)
    review_output = MagicMock()
    review_output.read_text.return_value = "===REVIEW_START===\n**Overall Score:** 8.0/10\n**Status:** FAIL\n===REVIEW_END==="
    review_output.exists.return_value = True
    mock_review.return_value = review_output

    # Fix output
    fix_output = MagicMock()
    # Make it long enough (> 100 chars)
    fixed_content = "# Fixed Content\n" + ("This is a long line of text to pass the length check. " * 5)
    fix_output.read_text.return_value = f"===CONTENT_START===\n{fixed_content}\n===CONTENT_END==="
    fix_output.exists.return_value = True
    mock_fix.return_value = fix_output

    # Audit: PASS
    mock_audit.return_value = True

    # Re-review: PASS (9.0)
    # We need to change the mock_review side effect or return value for second call
    mock_review.side_effect = [
        review_output, # initial
        MagicMock(read_text=MagicMock(return_value="===REVIEW_START===\n**Overall Score:** 9.0/10\n**Status:** PASS\n===REVIEW_END==="),
                  exists=MagicMock(return_value=True)) # re-review
    ]

    with patch("scripts.batch_fix_review.REPO", mock_repo):
        result = process_module("a1", 1, "mock-model")

    assert result["status"] == "FIXED"
    assert result["score_after"] == 9.0
    assert result["attempts"] == 1

    # Verify content was updated
    content_path = mock_repo / "curriculum/l2-uk-en/a1/01-test.md"
    assert "# Fixed Content" in content_path.read_text()

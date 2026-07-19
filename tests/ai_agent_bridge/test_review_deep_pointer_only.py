"""review-deep prompts must be pointer-only (no embedded diffs)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from ai_agent_bridge._dispatch_wrappers import (
    _list_review_path_names,
    _write_review_deep_path_prompt,
    _write_review_deep_pr_prompt,
)


def test_list_review_path_names_no_content(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("secret_payload_xyz\n", encoding="utf-8")
    listing = _list_review_path_names(tmp_path)
    assert "a.py" in listing
    assert "secret_payload_xyz" not in listing


def test_path_prompt_is_pointer_only(tmp_path: Path) -> None:
    target = tmp_path / "mod"
    target.mkdir()
    (target / "x.py").write_text("print('NO_EMBED')\n", encoding="utf-8")
    out = _write_review_deep_path_prompt(str(target), tmp_path)
    text = out.read_text(encoding="utf-8")
    assert "READ-ONLY REVIEW CONTRACT" in text
    assert "NO_EMBED" not in text
    assert "x.py" in text


def test_pr_prompt_is_pointer_only(tmp_path: Path) -> None:
    fake = {
        "title": "t",
        "url": "https://example.com/pull/1",
        "headRefOid": "abc123",
        "files": [{"path": "a.py", "additions": 1, "deletions": 0}],
    }
    with patch(
        "ai_agent_bridge._dispatch_wrappers._run_json_command",
        return_value=fake,
    ):
        out = _write_review_deep_pr_prompt("1", tmp_path)
    text = out.read_text(encoding="utf-8")
    assert "READ-ONLY REVIEW CONTRACT" in text
    assert "abc123" in text
    assert "a.py" in text
    assert "```diff" not in text
    assert "### Diff" not in text

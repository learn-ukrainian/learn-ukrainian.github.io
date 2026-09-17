"""Tests for CF-before-build preflight."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.build import cf_preflight as cf


def test_evaluate_comment_bodies_approve_on_exact_head():
    head = "a" * 40
    bodies = [
        f"Reviewer verdict: APPROVE\nExact head: {head}\nLooks good.",
    ]
    result = cf.evaluate_comment_bodies(bodies, head=head)
    assert result.clear is True


def test_evaluate_comment_bodies_request_changes_blocks():
    head = "b" * 40
    bodies = [
        f"Reviewer verdict: APPROVE\nhead: {head}",
        f"Reviewer verdict: REQUEST_CHANGES\nExact head: {head}\nP2 remains.",
    ]
    result = cf.evaluate_comment_bodies(bodies, head=head)
    assert result.clear is False
    assert "REQUEST_CHANGES" in result.reason


def test_clearance_file_requires_matching_head(tmp_path: Path):
    head = "c" * 40
    path = tmp_path / "cf_clearance.json"
    path.write_text(json.dumps({"head": head, "verdict": "APPROVE"}), encoding="utf-8")
    ok = cf.load_clearance_file(path)
    assert ok.clear and ok.head == head

    bad = cf.check_cf_preflight(
        repo_root=tmp_path,
        head="d" * 40,
        clearance_path=path,
        allow_github=False,
    )
    assert bad.clear is False
    assert "!= build HEAD" in bad.reason


def test_check_cf_preflight_module_dir_clearance(tmp_path: Path):
    head = "e" * 40
    module = tmp_path / "module"
    module.mkdir()
    (module / "cf_clearance.json").write_text(
        json.dumps({"head": head, "verdict": "APPROVED"}),
        encoding="utf-8",
    )
    result = cf.check_cf_preflight(
        repo_root=tmp_path,
        head=head,
        module_dir=module,
        allow_github=False,
    )
    assert result.clear is True

"""Tests for --no-resume default behavior (PR-A2, 2026-05-23)."""

import subprocess


def test_v7_build_help_lists_no_resume_not_resume() -> None:
    """--resume flag was removed; --no-resume is the new opt-out."""
    out = subprocess.run(
        [".venv/bin/python", "scripts/build/v7_build.py", "--help"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "--no-resume" in out, f"--no-resume missing from --help:\n{out}"
    assert "--resume" not in out, f"--resume should not be in --help:\n{out}"

"""Server-authoritative formal prompt admission (#9378), using real fixture renders."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pytest

from scripts.review.prompts import render as renderer
from scripts.review.prompts.check import AttemptIdsUnreadableError, parse_attempt_ids
from tests.review.test_prompts import _setup_lesson_fixture, _setup_plan_fixture, _write_rereview

SOURCE = Path(__file__).resolve().parents[2]
PROMPTS = Path("scripts/review/prompts")
IDS = {"review_id": "rev-bound", "attempt_id": "att-bound"}


def copy_review_checkout(target: Path) -> Path:
    """Reproduce the reviewer's plain copied-tree probe, without Git metadata."""
    target.mkdir(parents=True)
    for name in ("scripts", ".mcp", "agents_extensions"):
        shutil.copytree(SOURCE / name, target / name, symlinks=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copyfile(SOURCE / "requirements-lock.txt", target / "requirements-lock.txt")
    return target


def rendered_attempt(root, monkeypatch, *, checkout=SOURCE, kind="lesson", template_name=None):
    inputs = root / "inputs"
    if kind == "rereview":
        manifest, _ = _write_rereview(inputs, monkeypatch)
    elif kind == "plan":
        manifest, _, _ = _setup_plan_fixture(inputs, monkeypatch)
    else:
        manifest, _, _ = _setup_lesson_fixture(inputs, monkeypatch)
    monkeypatch.setattr(renderer, "REPO_ROOT", checkout)
    prompt_file = root / "prompt.md"
    prompt, _, _ = renderer.render_prompt(
        manifest, template_name, repo_root=inputs, prompts_dir=checkout / PROMPTS,
        output_path=prompt_file, **IDS,
    )
    args = argparse.Namespace(review_attempt=str(manifest), prompt_file=str(prompt_file))
    return args, prompt


def test_same_directory_symlink_alias_refuses(tmp_path, monkeypatch):
    copied = copy_review_checkout(tmp_path / "copied")
    (copied / PROMPTS / "alias.md.j2").symlink_to("lesson-review.md.j2")
    with pytest.raises(renderer.TemplateReadError, match="template_alias_refused"):
        rendered_attempt(tmp_path, monkeypatch, checkout=copied, template_name="alias.md.j2")


@pytest.mark.parametrize("key", ["review_id", "attempt_id"])
@pytest.mark.parametrize("value", ["[bound]", "{id: bound}"])
@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_nested_non_scalar_ids_refuse(key, value, newline):
    prompt = (
        "```yaml\nreview_schema: 1\nattempt: {review_id: bound, attempt_id: bound}\n"
        f"notes: {{{key}: {value}}}\n```\n"
    ).replace("\n", newline)
    with pytest.raises(AttemptIdsUnreadableError, match="non_scalar_attempt_id"):
        parse_attempt_ids(prompt)

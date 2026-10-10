"""Retirement is the first build gate, with no writes or other-input reads."""

import hashlib
from pathlib import Path

import pytest
import yaml

from scripts.build.fresh import assemble, cli, manifest, plan_manifest, plan_promote
from scripts.curriculum.evidence import lesson_lock
from scripts.curriculum.validate.loader import PlanError
from scripts.review import fixloop
from scripts.review.digest import generator


@pytest.fixture
def root(tmp_path):
    plans = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1"
    plans.mkdir(parents=True)
    path = plans / "old.yaml"
    path.write_text("invalid: [\n")
    record = {
        "retirement_schema": 1,
        "plans": [{"slug": "old", "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "old_position": 1}],
        "routes": [],
    }
    (plans / "_retired.yaml").write_text(yaml.safe_dump(record))
    return tmp_path


def snapshot(root):
    return {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}


@pytest.mark.parametrize(
    "command", ["render-prompt", "preflight", "write", "assemble", "build", "plan-manifest", "plan-promote"]
)
def test_cli_refuses_before_missing_evidence_and_writes_nothing(root, command, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_resolve_repo_root", lambda *a: root)
    before = snapshot(root)
    args = [command, "a1", "old"]
    if command in {"render-prompt", "preflight", "write", "assemble", "build"}:
        args += ["--lesson", "1"]
    if command == "write":
        args += ["--writer", "codex"]
    assert cli.main(args) == 1
    assert "plan_retired" in capsys.readouterr().err
    assert snapshot(root) == before


@pytest.mark.parametrize(
    "operation",
    [
        lambda root: cli._load_lesson_data("a1", "old", 1, repo_root=root),
        lambda root: assemble.assemble_lesson("a1", "old", 1, repo_root=root),
        lambda root: assemble.assemble_lesson(
            "a1", "old", 1, repo_root=root, plan_dict={}, pack_dict={}, words_dict={}, draft_dict={}),
        lambda root: lesson_lock.compute_lesson_lock("a1", "old", repo_root=root),
        lambda root: plan_manifest.write_plan_manifest("a1", "old", repo_root=root),
        lambda root: plan_promote.promote_plan("a1", "old", repo_root=root),
        lambda root: generator.build_digest("a1", "old", 1, repo_root=root),
        lambda root: fixloop.plan_lessons(root, "a1", "old"),
    ],
)
def test_direct_entrypoints_refuse_before_other_reads(root, operation, monkeypatch):
    before = snapshot(root)
    read_bytes, read_text = Path.read_bytes, Path.read_text
    allowed = {"old.yaml", "_retired.yaml"}

    def guarded_bytes(path):
        assert path.name in allowed, f"other input read before retirement: {path.name}"
        return read_bytes(path)

    def guarded_text(path, *args, **kwargs):
        assert path.name in allowed, f"other input read before retirement: {path.name}"
        return read_text(path, *args, **kwargs)

    with monkeypatch.context() as guard:
        guard.setattr(Path, "read_bytes", guarded_bytes)
        guard.setattr(Path, "read_text", guarded_text)
        with pytest.raises(PlanError, match="plan_retired"):
            operation(root)
    assert snapshot(root) == before


def test_lesson_manifest_refuses_without_reading_review_inputs(root):
    before = snapshot(root)
    plans = root / "curriculum/l2-uk-en/lesson-plans/a1"
    evidence = root / "curriculum/l2-uk-en/evidence/a1"
    with pytest.raises(PlanError, match="plan_retired"):
        manifest.write_manifest(
            "a1",
            "old",
            1,
            lesson_kind="lesson",
            state_dir=evidence / "_state/old",
            repo_root=root,
            plans_dir=plans,
            evidence_dir=evidence,
            position=1,
        )
    assert snapshot(root) == before


def test_retired_learner_state_is_reported_as_unrecomputable(root):
    path = "curriculum/l2-uk-en/evidence/a1/_state/old/learner-state.yaml"
    doc = {
        "kind": "lesson",
        "level": "a1",
        "slug": "old",
        "lesson": 1,
        "learner_state": {"sha256": "a" * 64},
        "inputs": {"learner_state": {"path": path, "sha256": "a" * 64}},
    }
    assert manifest._learner_state_change(doc, root)["current_sha256"] is None


def test_in_memory_inputs_cannot_bypass_retired_disk_plan(root):
    for operation in (
        lambda: lesson_lock.compute_lesson_lock("a1", "old", repo_root=root, plan_dict={}),
        lambda: assemble.assemble_lesson("a1", "old", 1, repo_root=root, plan_dict={}),
    ):
        with pytest.raises(PlanError, match="plan_retired"):
            operation()


def test_in_memory_inputs_cannot_bypass_invalid_record_without_disk_plan(tmp_path):
    plans = tmp_path / "curriculum/l2-uk-en/lesson-plans/a1"
    plans.mkdir(parents=True)
    (plans / "_retired.yaml").write_text("invalid: true\n")
    for operation in (
        lambda: lesson_lock.compute_lesson_lock("a1", "new", repo_root=tmp_path, plan_dict={}),
        lambda: assemble.assemble_lesson("a1", "new", 1, repo_root=tmp_path, plan_dict={}),
    ):
        before = snapshot(tmp_path)
        with pytest.raises(PlanError, match="retirement_record_invalid"):
            operation()
        assert snapshot(tmp_path) == before


def test_assembly_invalid_retirement_record_with_disk_plan_precedes_all_other_reads(root, monkeypatch):
    plans = root / "curriculum/l2-uk-en/lesson-plans/a1"
    (plans / "_retired.yaml").write_text("invalid: true\n")
    before = snapshot(root)
    read_text = Path.read_text

    def guarded_text(path, *args, **kwargs):
        assert path.name == "_retired.yaml", "other input read before inventory validation"
        return read_text(path, *args, **kwargs)

    with monkeypatch.context() as guard:
        guard.setattr(Path, "read_text", guarded_text)
        guard.setattr(Path, "read_bytes", lambda *_a: pytest.fail("plan bytes read before inventory validation"))
        with pytest.raises(PlanError, match="retirement_record_invalid"):
            assemble.assemble_lesson("a1", "old", 1, repo_root=root, plan_dict={})
    assert snapshot(root) == before


def test_changed_retired_bytes_get_ordinary_plan_failure_without_writes(root, monkeypatch):
    path = root / "curriculum/l2-uk-en/lesson-plans/a1/old.yaml"
    path.write_text("plan_schema: 2\nslug: old\nword_target: 10\n")
    before = snapshot(root)
    monkeypatch.setattr(assemble, "Sources", lambda: pytest.fail("Sources opened for invalid replacement"))
    report = assemble.assemble_lesson("a1", "old", 1, repo_root=root, plan_dict={})
    assert report["ok"] is False
    assert report["failure"]["code"] == "removed_v1_field"
    assert report["failure"]["check"] == 9
    assert snapshot(root) == before

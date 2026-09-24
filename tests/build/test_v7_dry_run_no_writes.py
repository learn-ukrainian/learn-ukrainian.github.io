"""#8679: ``v7_build --dry-run`` must not write under the content tree."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.build import linear_pipeline, run_archive, v7_build

pytestmark = pytest.mark.reads_content

LEVEL = "a1"
SLUG = "my-morning"
GATE_PASS = {"verdict": "PASS", "checks": {}}


class _WriterReached(Exception):
    """Raised by the mocked paid writer: proves a real run got past the gate."""


def _snapshot(root: Path) -> dict[str, str | None]:
    """Every path under ``root`` (dirs included) mapped to its content hash."""
    return {
        str(path.relative_to(root)): (hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None)
        for path in sorted(root.rglob("*"))
    }


@pytest.fixture
def content_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A tmp checkout whose canonical module dir is what ``--out``-less runs use."""
    root = tmp_path / "checkout"
    (root / "curriculum/l2-uk-en/a1").mkdir(parents=True)
    monkeypatch.setattr(v7_build, "PROJECT_ROOT", root)
    # The plan is read from the real repo; everything the build writes goes to `root`.
    monkeypatch.setattr(linear_pipeline, "build_knowledge_packet", lambda **_: "packet\n")
    monkeypatch.setattr(linear_pipeline, "build_wiki_manifest_data", lambda **_: {"articles": []})
    monkeypatch.setattr(linear_pipeline, "run_wiki_completeness_gate", lambda **_: dict(GATE_PASS))

    def paid_writer(*_args: Any, **_kwargs: Any) -> str:
        raise _WriterReached

    monkeypatch.setattr(linear_pipeline, "invoke_writer", paid_writer)
    monkeypatch.setattr(v7_build, "_enforce_cf_preflight", lambda *_a, **_k: None)
    return root


def _events(capsys: pytest.CaptureFixture[str]) -> list[dict[str, Any]]:
    events = []
    for line in capsys.readouterr().out.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _archive_env(monkeypatch: pytest.MonkeyPatch, root: Path) -> Path:
    """Point the build's run archive at ``root`` the way ``--worktree`` children do."""
    archive_dir = run_archive.archive_dir_for(root, level=LEVEL, slug=SLUG, run_id="run-1")
    monkeypatch.setenv(
        run_archive.ENV_KEY,
        json.dumps(
            {
                "project_root": str(root),
                "worktree_path": str(root),
                "archive_dir": str(archive_dir),
                "level": LEVEL,
                "slug": SLUG,
                "run_id": "run-1",
            }
        ),
    )
    return archive_dir


def test_dry_run_without_out_leaves_content_tree_byte_identical(
    content_root: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    archive_dir = _archive_env(monkeypatch, content_root)
    module_dir = v7_build._default_module_dir(LEVEL, SLUG)
    # A pre-existing module with prior artefacts: a dry run must leave these alone too.
    module_dir.mkdir(parents=True)
    (module_dir / "module.md").write_text("# Уже є\n", encoding="utf-8")
    before = _snapshot(content_root)

    assert v7_build._run(v7_build.parse_args([LEVEL, SLUG, "--dry-run"])) == 0

    assert _snapshot(content_root) == before
    assert not archive_dir.exists()
    events = _events(capsys)
    gate_done = next(e for e in events if e.get("phase") == "wiki_completeness_gate")
    assert gate_done["verdict"] == "PASS"
    assert gate_done["dry_run"] is True
    assert events[-1]["event"] == "module_done"
    assert events[-1]["dry_run"] is True


def test_dry_run_does_not_create_missing_module_directory(content_root: Path) -> None:
    before = _snapshot(content_root)

    assert v7_build._run(v7_build.parse_args([LEVEL, SLUG, "--dry-run"])) == 0

    assert not v7_build._default_module_dir(LEVEL, SLUG).exists()
    assert _snapshot(content_root) == before


def test_real_run_still_writes_the_gate_artefact(content_root: Path) -> None:
    module_dir = v7_build._default_module_dir(LEVEL, SLUG)

    # The mocked paid writer aborts the run right after the gate phase.
    assert v7_build._run(v7_build.parse_args([LEVEL, SLUG])) == 1

    gate = json.loads((module_dir / "wiki_completeness_gate.json").read_text(encoding="utf-8"))
    assert gate == GATE_PASS


def test_real_run_resumes_from_a_prior_gate_artefact(content_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module_dir = v7_build._default_module_dir(LEVEL, SLUG)
    module_dir.mkdir(parents=True)
    (module_dir / "knowledge_packet.md").write_text("packet\n", encoding="utf-8")
    (module_dir / "wiki_manifest.json").write_text("{}", encoding="utf-8")
    (module_dir / "wiki_completeness_gate.json").write_text(json.dumps(GATE_PASS), encoding="utf-8")

    def gate_must_not_rerun(**_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("resume should reuse the passing gate artefact")

    monkeypatch.setattr(linear_pipeline, "run_wiki_completeness_gate", gate_must_not_rerun)

    assert v7_build._run(v7_build.parse_args([LEVEL, SLUG])) == 1  # stops at the mocked writer

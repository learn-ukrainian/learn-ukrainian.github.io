from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.build import run_archive


def _start_archive(tmp_path: Path) -> tuple[run_archive.RunArchive, Path]:
    project_root = tmp_path / "project"
    worktree = tmp_path / "worktree"
    module_dir = worktree / "curriculum" / "l2-uk-en" / "a1" / "my-morning"
    module_dir.mkdir(parents=True)
    prior = (
        project_root
        / "curriculum"
        / "l2-uk-en"
        / "_orchestration"
        / "a1"
        / "my-morning"
        / "runs"
        / "20260518-120000"
    )
    prior.mkdir(parents=True)
    archive = run_archive.RunArchive.start(
        project_root=project_root,
        worktree_path=worktree,
        level="a1",
        slug="my-morning",
        run_id="20260519-123456",
        writer="codex-tools",
        model="gpt-5.5",
        effort="xhigh",
        prompt_sha="abc123",
        base_ref="base123",
    )
    return archive, module_dir


def _write_contract_artifacts(module_dir: Path) -> None:
    artifacts = {
        "writer_prompt.md": "writer prompt",
        "writer_output.raw.md": "raw writer output",
        "knowledge_packet.md": "knowledge",
        "wiki_manifest.json": "{}\n",
        "implementation_map.json": "{}\n",
        "python_qg.json": "{}\n",
        "python_qg_correction_r1.json": "{}\n",
        "wiki_coverage_gate.json": "{}\n",
        "wiki_coverage_correction_r1.json": "{}\n",
        "wiki_coverage_review.json": "{}\n",
        "llm_qg.json": "{}\n",
        "llm-qg-naturalness-prompt.md": "naturalness prompt",
        "my-morning.mdx": "---\ntitle: Test\n---\n",
    }
    for name, text in artifacts.items():
        (module_dir / name).write_text(text, encoding="utf-8")


def test_run_archive_copies_contract_artifacts_with_hyphenated_prompt(
    tmp_path: Path,
) -> None:
    archive, module_dir = _start_archive(tmp_path)
    _write_contract_artifacts(module_dir)

    archive.phase_started("writer")
    archive.phase_succeeded("writer", artifact_dir=module_dir)
    archive.terminal(status="complete", artifact_dir=module_dir)

    run_dir = archive.archive_dir
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))

    assert state["mode"] == "v7"
    assert state["track"] == "a1"
    assert state["slug"] == "my-morning"
    assert state["run_id"] == "20260519-123456"
    assert state["parent_run_id"] == "20260518-120000"
    assert state["status"] == "complete"
    assert state["failed_phase"] is None
    assert state["agent"] == "codex-tools"
    assert state["model"] == "gpt-5.5"
    assert state["effort"] == "xhigh"
    assert state["prompt_sha"] == "abc123"
    assert state["phases"]["writer"]["status"] == "complete"

    expected = {
        "state.json",
        "v7-writer-prompt.md",
        "writer_output.raw.md",
        "knowledge_packet.md",
        "wiki_manifest.json",
        "implementation_map.json",
        "python_qg.json",
        "python_qg_correction_r1.json",
        "wiki_coverage_gate.json",
        "wiki_coverage_correction_r1.json",
        "wiki_coverage_review.json",
        "llm_qg.json",
        "llm-qg-naturalness-prompt.md",
        "my-morning.mdx",
    }
    assert expected <= {path.name for path in run_dir.iterdir()}
    assert not (run_dir / "writer_prompt.md").exists()


def test_run_archive_writes_failed_mdx_frontmatter(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    archive, module_dir = _start_archive(tmp_path)
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text("level: a1\nslug: my-morning\nsequence: 1\n", encoding="utf-8")

    def fake_assemble_mdx(
        _module_dir: Path,
        output_path: Path,
        _plan_path: Path,
    ) -> str:
        mdx = "---\ntitle: Test\nbuild_status: draft\n---\n\nBody\n"
        output_path.write_text(mdx, encoding="utf-8")
        return mdx

    monkeypatch.setattr(run_archive.linear_pipeline, "assemble_mdx", fake_assemble_mdx)

    failed_mdx = archive.write_failed_mdx(
        module_dir=module_dir,
        plan_path=plan_path,
        failed_phase="python_qg",
    )
    archive.phase_failed("python_qg", artifact_dir=module_dir)
    archive.terminal(
        status="failed",
        failed_phase="python_qg",
        artifact_dir=module_dir,
        extra_paths=[failed_mdx] if failed_mdx is not None else None,
    )

    mdx = (archive.archive_dir / "my-morning.mdx").read_text(encoding="utf-8")
    state = json.loads((archive.archive_dir / "state.json").read_text("utf-8"))

    assert "build_status: failed" in mdx
    assert "failed_phase: python_qg" in mdx
    assert "build_status: draft" not in mdx
    assert state["status"] == "failed"
    assert state["failed_phase"] == "python_qg"


def test_parse_git_diff_stat_extracts_summary_and_paths() -> None:
    raw = """
 starlight/src/content/docs/a1/my-morning.mdx | 8 +++++---
 curriculum/l2-uk-en/a1/my-morning/module.md | 2 ++
 2 files changed, 7 insertions(+), 3 deletions(-)
"""

    summary = run_archive.parse_git_diff_stat(
        raw,
        run_id="20260519-123456",
        parent_run_id="20260518-120000",
        base_ref="base123",
        head_ref="head456",
    )

    assert summary["run_id"] == "20260519-123456"
    assert summary["parent_run_id"] == "20260518-120000"
    assert summary["base_ref"] == "base123"
    assert summary["head_ref"] == "head456"
    assert summary["files_changed"] == 2
    assert summary["insertions"] == 7
    assert summary["deletions"] == 3
    assert summary["paths"] == [
        {
            "path": "starlight/src/content/docs/a1/my-morning.mdx",
            "status": "modified",
            "insertions": 5,
            "deletions": 3,
        },
        {
            "path": "curriculum/l2-uk-en/a1/my-morning/module.md",
            "status": "added",
            "insertions": 2,
            "deletions": 0,
        },
    ]

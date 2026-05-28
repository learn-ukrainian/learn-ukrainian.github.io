from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.build import linear_pipeline, v7_build


def _install_pass_fixture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    mdx_error: Exception | None = None,
) -> tuple[SimpleNamespace, Path, Path]:
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text("level: a1\nslug: fixture\nsequence: 1\n", encoding="utf-8")
    module_dir = tmp_path / "module"
    telemetry_path = tmp_path / "events.jsonl"
    plan = {
        "level": "a1",
        "slug": "fixture",
        "sequence": 1,
        "content_outline": [],
    }

    def write_artifacts(target_dir: Path, artifacts: dict[str, str]) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        for name, text in artifacts.items():
            (target_dir / name).write_text(text, encoding="utf-8")

    def assemble_mdx(_module_dir: Path, mdx_path: Path, _plan_path: Path) -> None:
        if mdx_error is not None:
            raise mdx_error
        mdx_path.write_text("# Fixture\n", encoding="utf-8")

    monkeypatch.setattr(v7_build.linear_pipeline, "plan_path_for", lambda *_: plan_path)
    monkeypatch.setattr(v7_build.linear_pipeline, "load_plan", lambda _: plan)
    monkeypatch.setattr(v7_build.linear_pipeline, "validate_plan", lambda _: None)
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "build_knowledge_packet",
        lambda **_: "knowledge packet",
    )
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "build_wiki_manifest_data",
        lambda **_: {"slug": "fixture", "sequence_steps": []},
    )
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "run_wiki_completeness_gate",
        lambda **_: {"verdict": "PASS", "diagnostic": "fixture"},
    )
    monkeypatch.setattr(
        v7_build,
        "seed_implementation_map",
        lambda *_args, **_kwargs: {"schema_version": 1, "entries": []},
    )
    monkeypatch.setattr(
        v7_build,
        "write_implementation_map",
        lambda payload, path: path.write_text(json.dumps(payload), encoding="utf-8"),
    )
    monkeypatch.setattr(v7_build, "_writer_prompt", lambda **_: "writer prompt")
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "invoke_writer",
        lambda *_args, **_kwargs: "writer output",
    )
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "parse_writer_output",
        lambda _: {
            "module.md": "# Fixture\n",
            "activities.yaml": "[]\n",
            "vocabulary.yaml": "[]\n",
            "resources.yaml": "[]\n",
        },
    )
    monkeypatch.setattr(v7_build.linear_pipeline, "write_writer_artifacts", write_artifacts)
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "run_python_qg_with_corrections",
        lambda *_args, **_kwargs: {"gates": {"passed": True}},
    )
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "run_wiki_coverage_with_corrections",
        lambda **_: {"passed": True, "coverage_pct": 1.0},
    )
    monkeypatch.setattr(
        v7_build,
        "_run_wiki_coverage_review",
        lambda **_: {"overall_verdict": "PASS", "verdicts": []},
    )
    monkeypatch.setattr(
        v7_build,
        "_run_llm_qg",
        lambda **_: {
            "aggregate": {
                "min_score": 9.0,
                "verdict": "PASS",
                "terminal_verdict": "PASS",
            }
        },
    )
    monkeypatch.setattr(v7_build.linear_pipeline, "assemble_mdx", assemble_mdx)

    args = SimpleNamespace(
        level="a1",
        slug="fixture",
        writer="claude-tools",
        reviewer=None,
        dry_run=False,
        out=str(module_dir),
        writer_timeout=5,
        effort=None,
        no_resume=True,
    )
    return args, telemetry_path, module_dir


def _run_fixture(
    args: SimpleNamespace,
    telemetry_path: Path,
) -> tuple[int, list[dict[str, Any]]]:
    with linear_pipeline.telemetry_event_sink(telemetry_path):
        exit_code = v7_build._run(args)
    events = [
        json.loads(line)
        for line in telemetry_path.read_text(encoding="utf-8").splitlines()
    ]
    return exit_code, events


def test_terminal_pass_runs_mdx_and_emits_module_done(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args, telemetry_path, module_dir = _install_pass_fixture(monkeypatch, tmp_path)

    exit_code, events = _run_fixture(args, telemetry_path)

    phase_done = [event["phase"] for event in events if event["event"] == "phase_done"]
    assert exit_code == 0
    assert phase_done[-2:] == ["llm_qg", "mdx"]
    assert events[-1]["event"] == "module_done"
    assert (module_dir / "fixture.mdx").exists()


def test_mdx_failure_still_emits_terminal_event_when_archive_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args, telemetry_path, _module_dir = _install_pass_fixture(
        monkeypatch,
        tmp_path,
        mdx_error=ValueError("fixture mdx failure"),
    )

    def fail_archive(*_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("archive failure")

    monkeypatch.setattr(v7_build, "_archive_failure", fail_archive)

    exit_code, events = _run_fixture(args, telemetry_path)
    captured = capsys.readouterr()

    assert exit_code == 1
    assert events[-1]["event"] == "module_failed"
    assert events[-1]["phase"] == "mdx"
    assert events[-1]["reason"] == "fixture mdx failure"
    assert "failed in phase mdx: fixture mdx failure" in captured.err
    assert "failed to archive failure for phase mdx: archive failure" in captured.err

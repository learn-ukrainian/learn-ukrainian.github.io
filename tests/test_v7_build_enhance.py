from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts.build import v7_build

SLUG = "kalendarna-obriadovist-zvychai"


def _seed_content(module_dir: Path, *, include_resources: bool = True) -> None:
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.md").write_text("# Curated module\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    if include_resources:
        (module_dir / "resources.yaml").write_text("[]\n", encoding="utf-8")


def _install_plan(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> dict[str, Any]:
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        "level: folk\nslug: kalendarna-obriadovist-zvychai\nsequence: 1\n",
        encoding="utf-8",
    )
    plan = {
        "level": "folk",
        "slug": SLUG,
        "sequence": 1,
        "word_target": 800,
        "content_outline": [{"section": "Curated section"}],
    }
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "plan_path_for",
        lambda _level, _slug: plan_path,
    )
    monkeypatch.setattr(v7_build.linear_pipeline, "load_plan", lambda _path: plan)
    monkeypatch.setattr(v7_build.linear_pipeline, "validate_plan", lambda _plan: None)
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "curriculum_profile_for_level",
        lambda _level: "folk",
    )
    monkeypatch.setattr(
        v7_build,
        "_ensure_top_level_invocation_is_not_primary_checkout",
        lambda: None,
    )
    return plan


def test_enhance_skips_generation_and_runs_review_gates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_plan(monkeypatch, tmp_path)
    module_dir = tmp_path / "module"
    _seed_content(module_dir)
    events: list[dict[str, Any]] = []
    call_order: list[str] = []
    manifest = {
        "slug": SLUG,
        "wiki_path": "wiki/folk/kalendarna-obriadovist-zvychai.md",
        "sequence_steps": [],
        "l2_errors": [],
        "phonetic_rules": [],
        "decolonization_bans": [],
        "wiki_vocabulary_minimum": [],
    }

    monkeypatch.setattr(v7_build, "emit_event", lambda event, **fields: events.append({"event": event, **fields}))
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "build_knowledge_packet",
        lambda **_kwargs: pytest.fail("enhance must not build knowledge packets"),
    )
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "invoke_writer",
        lambda *_args, **_kwargs: pytest.fail("enhance must not invoke the writer"),
    )
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "build_wiki_manifest_data",
        lambda **_kwargs: manifest,
    )
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "run_wiki_completeness_gate",
        lambda **_kwargs: {"verdict": "PASS"},
    )

    def fake_python_qg(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        call_order.append("python_qg")
        return {"gates": {"passed": True}}

    def fake_wiki_coverage(**kwargs: Any) -> dict[str, Any]:
        call_order.append("wiki_coverage_gate")
        assert kwargs["writer_output"] == ""
        assert (module_dir / "implementation_map.json").exists()
        assert not (module_dir / "writer_output.raw.md").exists()
        return {"passed": True}

    def fake_wiki_review(**_kwargs: Any) -> dict[str, Any]:
        call_order.append("wiki_coverage_review")
        return {"overall_verdict": "PASS", "verdicts": []}

    def fake_llm_qg(**kwargs: Any) -> dict[str, Any]:
        call_order.append("llm_qg")
        assert kwargs["implementation_map"]["entries"] == []
        assert "kalendarna-obriadovist-zvychai" in kwargs["wiki_manifest"]
        return {
            "aggregate": {
                "min_score": 8.0,
                "verdict": "PASS",
                "terminal_verdict": "PASS",
                "failing_dims": [],
            },
            "dimensions": {},
        }

    def fake_assemble_mdx(_module_dir: Path, mdx_path: Path, _plan_path: Path) -> None:
        call_order.append("mdx")
        mdx_path.write_text("---\ntitle: Curated\n---\n", encoding="utf-8")

    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "run_python_qg_with_corrections",
        fake_python_qg,
    )
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "run_wiki_coverage_with_corrections",
        fake_wiki_coverage,
    )
    monkeypatch.setattr(v7_build, "_run_wiki_coverage_review", fake_wiki_review)
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "run_llm_qg_with_corrections",
        fake_llm_qg,
    )
    monkeypatch.setattr(v7_build.linear_pipeline, "assemble_mdx", fake_assemble_mdx)

    exit_code = v7_build.main(
        ["folk", SLUG, "--enhance", "--out", str(module_dir)]
    )

    skipped = {
        event["phase"]
        for event in events
        if event["event"] == "phase_skipped" and event["reason"] == "enhance"
    }
    metadata = {
        event["artifact"]: event["source"]
        for event in events
        if event["event"] == "enhance_metadata_ready"
    }
    assert exit_code == 0
    assert skipped == {
        "knowledge_packet",
        "writer",
        "stress_annotation",
        "ulp_fidelity_gate",
    }
    assert call_order == [
        "python_qg",
        "wiki_coverage_gate",
        "wiki_coverage_review",
        "llm_qg",
        "mdx",
    ]
    assert metadata == {
        "wiki_manifest.json": "generated",
        "implementation_map.json": "generated",
    }


def test_enhance_missing_content_file_errors_cleanly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_plan(monkeypatch, tmp_path)
    module_dir = tmp_path / "module"
    _seed_content(module_dir, include_resources=False)
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "build_wiki_manifest_data",
        lambda **_kwargs: pytest.fail("enhance must fail before metadata seeding"),
    )

    exit_code = v7_build.main(
        ["folk", SLUG, "--enhance", "--out", str(module_dir)]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "--enhance requires existing content files" in captured.err
    assert "resources.yaml" in captured.err
    assert not (module_dir / "wiki_manifest.json").exists()

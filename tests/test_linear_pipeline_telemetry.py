from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from scripts.build import linear_pipeline

pytestmark = pytest.mark.reads_content


def _qg_fixture_plan(tmp_path: Path) -> Path:
    """Minimal plan for run_python_qg unit tests (no curriculum/ checkout required)."""
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text(
        yaml.safe_dump(
            {
                "module": "a1-020",
                "level": "A1",
                "sequence": 20,
                "slug": "my-morning",
                "title": "Мій ранок",
                "subtitle": "Зворотні дієслова",
                "word_target": 89,
                "content_outline": [
                    {
                        "section": "Діалоги",
                        "words": 89,
                        "points": ["Introduce a morning dialogue."],
                    }
                ],
                "references": [
                    {"title": "Караман Grade 10, p.176", "verbatim_required": False}
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return plan_path


def test_telemetry_event_sink_appends_jsonl(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    telemetry = tmp_path / "events.jsonl"

    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline.emit_event("first", slug="x")
    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline.emit_event("second", slug="x")

    captured = capsys.readouterr()
    events = [json.loads(line) for line in telemetry.read_text("utf-8").splitlines()]

    assert captured.out == ""
    assert [event["event"] for event in events] == ["first", "second"]
    assert all(event["slug"] == "x" for event in events)


def test_python_qg_surface_policy_scans_yaml_sidecars(tmp_path: Path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text("## Урок\n\n**Я чекаю на автобус.**\n", encoding="utf-8")
    (module_dir / "activities.yaml").write_text(
        "- type: quiz\n"
        "  prompt: Обери відповідь.\n"
        "  note: As an AI, I cannot assist with this request.\n",
        encoding="utf-8",
    )
    (module_dir / "vocabulary.yaml").write_text("[]\n", encoding="utf-8")
    (module_dir / "resources.yaml").write_text("[]\n", encoding="utf-8")

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        return {word: [{"lemma": word}] for word in words}

    report = linear_pipeline.run_python_qg(
        module_dir,
        _qg_fixture_plan(tmp_path),
        verify_words_fn=verify_words,
    )

    surface_policy = report["gates"]["surface_policy"]
    assert surface_policy["passed"] is False
    assert any(
        finding["type"] == "ai_leakage" and finding["source"] == "activities.yaml"
        for finding in surface_policy["findings"]
    )


def test_mcp_tools_writer_runtime_gate_still_fires_for_empty_tool_calls() -> None:
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match="MCP_TOOLS_NEVER_INVOKED",
    ):
        linear_pipeline._enforce_tools_writer_runtime_gate(
            writer="gemini-tools",
            module="a1/1",
            phase_writer_summary={"tool_calls_total": 0},
        )


def test_resources_artifact_rejects_internal_wiki_urls() -> None:
    # On-site wiki articles have no public student-facing route (served only via
    # the internal /api/wiki API), so an internal `wiki/...` repo path renders as
    # a dead link. reading-task links must be public allowlisted URLs; the on-site
    # primary text reaches the learner through a :::primary-reading block instead.
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match="student-facing sources only",
    ):
        linear_pipeline._validate_writer_json_artifact(
            "resources.yaml",
            [
                {
                    "title": "Wiki: folk/kupalo",
                    "role": "reading",
                    "url": "wiki/folk/kupalo.md",
                    "notes": "прочитай локальний огляд теми",
                }
            ],
        )

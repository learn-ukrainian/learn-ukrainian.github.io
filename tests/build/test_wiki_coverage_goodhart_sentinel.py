from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from scripts.build import linear_pipeline, v7_build

VALID_EVIDENCE = '"This quoted excerpt gives enough surrounding lesson context."'


def _verdict(
    obligation_id: str,
    verdict: str,
    evidence: str = VALID_EVIDENCE,
) -> dict[str, str]:
    return {
        "obligation_id": obligation_id,
        "verdict": verdict,
        "evidence": evidence,
        "rationale": "fixture rationale",
    }


def _parse(
    verdicts: list[dict[str, str]],
    *,
    overall_verdict: str = "PASS",
) -> dict[str, Any]:
    return linear_pipeline.parse_wiki_coverage_review_response(
        json.dumps(
            {
                "verdicts": verdicts,
                "overall_verdict": overall_verdict,
                "summary": "fixture summary",
            },
            ensure_ascii=False,
        )
    )


def _install_v7_fixture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    review_result: dict[str, Any],
) -> tuple[SimpleNamespace, Path]:
    plan_path = tmp_path / "plan.yaml"
    plan_path.write_text("level: a1\nslug: fixture\nsequence: 1\n", encoding="utf-8")
    module_dir = tmp_path / "module"
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

    def write_implementation_map(payload: dict[str, Any], path: Path) -> None:
        path.write_text(json.dumps(payload), encoding="utf-8")

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
        v7_build,
        "seed_implementation_map",
        lambda *_args, **_kwargs: {"schema_version": 1, "entries": []},
    )
    monkeypatch.setattr(v7_build, "write_implementation_map", write_implementation_map)
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
    monkeypatch.setattr(v7_build, "_run_wiki_coverage_review", lambda **_: review_result)
    monkeypatch.setattr(
        v7_build,
        "_run_llm_qg",
        lambda **_: {"aggregate": {"min_score": 9.0, "verdict": "PASS"}},
    )
    monkeypatch.setattr(
        v7_build.linear_pipeline,
        "assemble_mdx",
        lambda _module_dir, mdx_path, _plan_path: mdx_path.write_text(
            "# Fixture\n",
            encoding="utf-8",
        ),
    )

    return (
        SimpleNamespace(
            level="a1",
            slug="fixture",
            writer="claude-tools",
            dry_run=False,
            out=str(module_dir),
            writer_timeout=5,
            effort=None,  # added 2026-05-13 in 9e5a6496b9 (--effort flag)
        ),
        tmp_path / "events.jsonl",
    )


def _run_v7_fixture(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    review_result: dict[str, Any],
) -> tuple[int, list[dict[str, Any]]]:
    args, telemetry_path = _install_v7_fixture(monkeypatch, tmp_path, review_result)
    with linear_pipeline.telemetry_event_sink(telemetry_path):
        exit_code = v7_build._run(args)
    events = [
        json.loads(line)
        for line in telemetry_path.read_text(encoding="utf-8").splitlines()
    ]
    return exit_code, events


def test_pass_only_verdicts_allow_overall_pass() -> None:
    result = _parse(
        [_verdict(f"step-{index}", "PASS") for index in range(5)],
        overall_verdict="PASS",
    )

    assert result["overall_verdict"] == "PASS"
    assert [item["verdict"] for item in result["verdicts"]] == ["PASS"] * 5


def test_keyword_stuffing_requires_overall_fail() -> None:
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match="overall_verdict must be FAIL",
    ):
        _parse(
            [
                _verdict("step-1", "PASS"),
                _verdict("err-1", "KEYWORD_STUFFING"),
            ],
            overall_verdict="PASS",
        )


@pytest.mark.parametrize("overall_verdict", ["PASS", "PARTIAL"])
def test_partial_only_is_soft_signal(overall_verdict: str) -> None:
    result = _parse(
        [
            _verdict("step-1", "PARTIAL"),
            _verdict("step-2", "PARTIAL"),
        ],
        overall_verdict=overall_verdict,
    )

    assert result["overall_verdict"] == overall_verdict
    assert [item["verdict"] for item in result["verdicts"]] == [
        "PARTIAL",
        "PARTIAL",
    ]


def test_fail_verdict_requires_overall_fail() -> None:
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match="overall_verdict must be FAIL",
    ):
        _parse(
            [_verdict("step-1", "FAIL")],
            overall_verdict="PARTIAL",
        )


def test_evidence_without_quote_marker_raises() -> None:
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match="evidence must be a quoted excerpt",
    ):
        _parse(
            [
                _verdict(
                    "step-1",
                    "PASS",
                    evidence="just plain text no quote chars",
                )
            ]
        )


def test_evidence_shorter_than_eight_chars_raises() -> None:
    with pytest.raises(
        linear_pipeline.LinearPipelineError,
        match="evidence must be a quoted excerpt",
    ):
        _parse([_verdict("step-1", "PASS", evidence='"tiny"')])


@pytest.mark.parametrize(
    "evidence",
    [
        '"This quoted excerpt is long enough for review."',
        "“This quoted excerpt is long enough for review.”",
        "«This quoted excerpt is long enough for review.»",
    ],
)
def test_quote_markers_are_accepted(evidence: str) -> None:
    result = _parse([_verdict("step-1", "PASS", evidence=evidence)])

    assert result["verdicts"][0]["evidence"] == evidence


def test_v7_build_emits_goodhart_sentinel_telemetry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    review_result = {
        "verdicts": [
            _verdict("step-1", "PASS"),
            _verdict("step-2", "PARTIAL"),
            _verdict("err-1", "KEYWORD_STUFFING"),
        ],
        "overall_verdict": "FAIL",
        "summary": "fixture summary",
    }

    exit_code, events = _run_v7_fixture(monkeypatch, tmp_path, review_result)
    event = next(
        item for item in events if item["event"] == "wiki_coverage_goodhart_sentinel"
    )

    assert exit_code == 1
    assert event["overall_verdict"] == "FAIL"
    assert event["keyword_stuffing_count"] == 1
    assert event["partial_count"] == 1
    assert event["total_verdicts"] == 3


def test_v7_build_fails_on_keyword_stuffing_overall_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    review_result = {
        "verdicts": [_verdict("err-1", "KEYWORD_STUFFING")],
        "overall_verdict": "FAIL",
        "summary": "fixture summary",
    }

    exit_code, events = _run_v7_fixture(monkeypatch, tmp_path, review_result)
    captured = capsys.readouterr()
    failure = next(item for item in events if item["event"] == "module_failed")

    assert exit_code == 1
    assert "v7_build failed in phase wiki_coverage_review" in captured.err
    assert failure["reason"] == "Wiki coverage review failed"


def test_prompt_template_renders_keyword_stuffing_instruction() -> None:
    prompt = linear_pipeline.render_wiki_coverage_review_prompt(
        {
            "level": "a1",
            "sequence": 1,
            "slug": "fixture",
            "word_target": 600,
        },
        "level: a1\nslug: fixture\n",
        "## module.md\n\nGenerated content",
        {"slug": "fixture", "sequence_steps": []},
        {"passed": True, "coverage_pct": 1.0},
    )

    assert "KEYWORD_STUFFING" in prompt


def test_prompt_template_enforces_strict_response_format() -> None:
    """Build #10 (2026-05-21) failed because the reviewer emitted prose
    narration around the JSON. The prompt must now explicitly forbid
    preamble/epilogue and demonstrate the all-PASS shape."""
    prompt = linear_pipeline.render_wiki_coverage_review_prompt(
        {
            "level": "a1",
            "sequence": 1,
            "slug": "fixture",
            "word_target": 600,
        },
        "level: a1\nslug: fixture\n",
        "## module.md\n\nGenerated content",
        {"slug": "fixture", "sequence_steps": []},
        {"passed": True, "coverage_pct": 1.0},
    )

    assert "Response Format — STRICT" in prompt
    assert "No preamble" in prompt
    assert "No epilogue" in prompt
    # All-PASS worked example so the reviewer has no excuse to narrate.
    assert '"overall_verdict": "PASS"' in prompt


def test_parser_recovers_from_prose_preamble_with_fenced_block() -> None:
    """Codex reviewer pattern from build #10: prose narration wrapping a
    fenced JSON payload. The parser must extract the fenced block."""
    response = (
        "I have verified all **18 obligations** in the wiki coverage manifest. "
        "Each one was checked against the cited artifact and the surrounding "
        "lesson context. Here is the structured output:\n\n"
        "```json\n"
        + json.dumps(
            {
                "verdicts": [_verdict("err-1", "PASS")],
                "overall_verdict": "PASS",
                "summary": "All obligations satisfied.",
            }
        )
        + "\n```\n\nLet me know if you need further detail."
    )

    parsed = linear_pipeline.parse_wiki_coverage_review_response(response)
    assert parsed["overall_verdict"] == "PASS"
    assert parsed["verdicts"][0]["obligation_id"] == "err-1"


def test_parser_recovers_from_prose_preamble_with_bare_object() -> None:
    """LLMs sometimes drop the fence and emit a bare object inside prose."""
    payload = json.dumps(
        {
            "verdicts": [_verdict("err-1", "PASS")],
            "overall_verdict": "PASS",
            "summary": "All obligations satisfied.",
        }
    )
    response = (
        "I have verified all obligations. The result is " + payload + " Thanks!"
    )

    parsed = linear_pipeline.parse_wiki_coverage_review_response(response)
    assert parsed["overall_verdict"] == "PASS"


def test_parser_still_handles_bare_json_payload() -> None:
    """Regression guard: well-formed responses without prose still parse."""
    payload = json.dumps(
        {
            "verdicts": [_verdict("err-1", "PASS")],
            "overall_verdict": "PASS",
            "summary": "OK.",
        }
    )
    parsed = linear_pipeline.parse_wiki_coverage_review_response(payload)
    assert parsed["overall_verdict"] == "PASS"


def test_parser_still_handles_outer_fenced_payload() -> None:
    payload = json.dumps(
        {
            "verdicts": [_verdict("err-1", "PASS")],
            "overall_verdict": "PASS",
            "summary": "OK.",
        }
    )
    parsed = linear_pipeline.parse_wiki_coverage_review_response(
        f"```json\n{payload}\n```"
    )
    assert parsed["overall_verdict"] == "PASS"


def test_parser_rejects_pure_prose_with_no_json() -> None:
    """Without any extractable JSON, the parser must still raise so the
    build doesn't silently succeed on a bare confirmation."""
    with pytest.raises(linear_pipeline.LinearPipelineError):
        linear_pipeline.parse_wiki_coverage_review_response(
            "I have verified all 18 obligations. They are all good."
        )

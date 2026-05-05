from __future__ import annotations

import json
from pathlib import Path

from scripts.build import linear_pipeline


def _events(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines()]


def test_writer_correction_unparseable_response_emits_diagnostic(tmp_path: Path) -> None:
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text("## Morning\n\nTest module.\n", encoding="utf-8")
    telemetry = tmp_path / "events.jsonl"

    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline._apply_writer_correction(
            "word_count",
            {"passed": False, "minimum": 100, "actual": 20},
            qg_report={"gates": {}},
            module_dir=module_dir,
            plan_path=tmp_path / "plan.yaml",
            writer_corrector=lambda _context: "I fixed the prose but emitted no artifacts.",
            writer="codex-tools",
            invoker=None,
        )

    events = _events(telemetry)
    assert [event["event"] for event in events] == ["writer_correction_unparseable"]
    assert events[0]["gate"] == "word_count"
    assert events[0]["response_preview"] == "I fixed the prose but emitted no artifacts."


def test_parse_writer_correction_module_only_extracts_single_block() -> None:
    """The patch-bounded correction parser accepts the contract format
    (one fenced ``markdown file=module.md`` block, no other prose)."""
    response = (
        "```markdown file=module.md\n"
        "## Morning\n\n"
        "Patched prose with the missing 50 words appended.\n"
        "```\n"
    )
    body = linear_pipeline.parse_writer_correction_module_only(response)
    assert body is not None
    assert body.startswith("## Morning")
    assert "Patched prose" in body
    assert body.endswith("\n")


def test_parse_writer_correction_module_only_accepts_short_form_label() -> None:
    """The parser also accepts ``markdown module.md`` and ``module.md``
    fence-info conventions — writers vary on this minor formatting."""
    response_short = "```markdown module.md\nbody1\n```"
    response_bare = "```module.md\nbody2\n```"
    assert linear_pipeline.parse_writer_correction_module_only(response_short) == "body1\n"
    assert linear_pipeline.parse_writer_correction_module_only(response_bare) == "body2\n"


def test_parse_writer_correction_module_only_rejects_zero_or_multi_blocks() -> None:
    """No fenced block, or multiple fenced blocks, returns None — the
    pipeline falls through to writer_correction_unparseable."""
    assert linear_pipeline.parse_writer_correction_module_only("just prose") is None
    multi = (
        "```markdown file=module.md\nfirst\n```\n\n"
        "```markdown file=module.md\nsecond\n```\n"
    )
    assert linear_pipeline.parse_writer_correction_module_only(multi) is None


def test_parse_writer_correction_module_only_rejects_empty_body() -> None:
    """A fenced block with no content is unparseable — writer is patching
    nothing, which violates the patch-bounded contract."""
    response = "```markdown file=module.md\n\n```"
    assert linear_pipeline.parse_writer_correction_module_only(response) is None


def test_writer_correction_module_only_writes_patched_module(tmp_path: Path) -> None:
    """End-to-end: a contract-shaped response patches module.md and emits
    no `writer_correction_unparseable` event."""
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(
        "## Morning\n\nOriginal prose.\n", encoding="utf-8"
    )
    telemetry = tmp_path / "events.jsonl"
    patched_response = (
        "```markdown file=module.md\n"
        "## Morning\n\n"
        "Original prose. Patched insert: добрий ранок!\n"
        "```\n"
    )

    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline._apply_writer_correction(
            "word_count",
            {"passed": False, "minimum": 100, "actual": 20},
            qg_report={"gates": {}},
            module_dir=module_dir,
            plan_path=tmp_path / "plan.yaml",
            writer_corrector=lambda _context: patched_response,
            writer="codex-tools",
            invoker=None,
        )

    # No diagnostic — the contract response parsed cleanly.
    events = (
        _events(telemetry)
        if telemetry.exists() and telemetry.stat().st_size > 0
        else []
    )
    assert events == [], (
        f"Expected no events, got: {[e['event'] for e in events]}"
    )
    # module.md was patched with the new prose.
    assert (module_dir / "module.md").read_text("utf-8") == (
        "## Morning\n\nOriginal prose. Patched insert: добрий ранок!\n"
    )


def test_writer_correction_strict_json_parse_gate_still_requires_full_artifacts(
    tmp_path: Path,
) -> None:
    """The strict_json_parse gate is the ONE writer-correction gate where
    the response must include all 4 artifact blocks — single-block response
    is unparseable for that gate because the original failure mode WAS the
    parse, so all artifacts need to be re-emitted."""
    module_dir = tmp_path / "module"
    module_dir.mkdir()
    (module_dir / "module.md").write_text(
        "## Morning\n\nOriginal prose.\n", encoding="utf-8"
    )
    telemetry = tmp_path / "events.jsonl"
    # A response that would parse as module-only but fails the
    # strict_json_parse contract because activities/vocabulary/resources
    # are absent.
    module_only_response = (
        "```markdown file=module.md\n## Morning\n\nPatched.\n```\n"
    )

    with linear_pipeline.telemetry_event_sink(telemetry):
        linear_pipeline._apply_writer_correction(
            "strict_json_parse",
            {"passed": False, "reason": "missing artifact"},
            qg_report={"gates": {}},
            module_dir=module_dir,
            plan_path=tmp_path / "plan.yaml",
            writer_corrector=lambda _context: module_only_response,
            writer="codex-tools",
            invoker=None,
        )

    events = _events(telemetry)
    assert [event["event"] for event in events] == ["writer_correction_unparseable"]
    assert events[0]["gate"] == "strict_json_parse"

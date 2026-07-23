"""Tests for scripts/lint/lint_fleet_roster.py (#5642 Δ1)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import yaml

from scripts.lint.lint_fleet_roster import (
    SEAT_FIELDS,
    format_eligible_table,
    format_seat_table,
    lint_fleet_roster,
    load_formal_review_eligible,
    load_orchestrator_seats,
    main,
    parse_eligible_projection,
    parse_seat_projection,
)


def _seat_block(seats: dict[str, dict[str, str]]) -> str:
    return (
        "<!-- fleet-roster-projection:begin orchestrator_seats -->\n"
        f"{format_seat_table(seats)}\n"
        "<!-- fleet-roster-projection:end orchestrator_seats -->\n"
    )


def _elig_block(eligible: dict[str, bool]) -> str:
    return (
        "<!-- fleet-roster-projection:begin formal_review_eligible -->\n"
        f"{format_eligible_table(eligible)}\n"
        "<!-- fleet-roster-projection:end formal_review_eligible -->\n"
    )


def _write_projection(path: Path, seats: dict[str, dict[str, str]], eligible: dict[str, bool]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# fixture\n\n" + _seat_block(seats) + "\n" + _elig_block(eligible),
        encoding="utf-8",
    )


def _mini_authorities(tmp: Path) -> tuple[Path, Path, dict, dict]:
    seats = {
        "agy": {
            "model_id": "gemini-3.6-flash-high",
            "effort": "high",
            "escalate_model_id": "gemini-3.1-pro-high",
            "escalate_effort": "high",
        },
        "claude": {
            "model_id": "claude-sonnet-5",
            "effort": "high",
            "escalate_model_id": "claude-fable-5",
            "escalate_effort": "xhigh",
        },
        "codex": {
            "model_id": "gpt-5.6-terra",
            "effort": "high",
            "escalate_model_id": "gpt-5.6-sol",
            "escalate_effort": "xhigh",
        },
        "grok": {
            "model_id": "grok-4.5",
            "effort": "high",
            "escalate_model_id": "grok-4.5",
            "escalate_effort": "high",
        },
    }
    eligible = {
        "agy": False,
        "claude": True,
        "codex": True,
        "cursor": False,
        "gemini": False,
        "glm-local": False,
        "grok": False,
        "kimi": False,
    }
    catalog = tmp / "model_catalog.yaml"
    catalog.write_text(
        yaml.safe_dump({"orchestrator_seats": seats}, sort_keys=True),
        encoding="utf-8",
    )
    endpoints = [
        {"name": name, "formal_review_eligible": flag} for name, flag in sorted(eligible.items())
    ]
    comms = tmp / "fleet_communications.yaml"
    comms.write_text(
        yaml.safe_dump({"version": 1, "endpoints": endpoints}, sort_keys=False),
        encoding="utf-8",
    )
    return catalog, comms, seats, eligible


def test_committed_projections_match_machine_authorities():
    """Green path against the real repo SSOT docs (never arm lint against known-red)."""
    issues = lint_fleet_roster()
    assert issues == [], [i.as_dict() for i in issues]
    seats = load_orchestrator_seats()
    assert "codex" in seats
    assert set(seats) == {"claude", "codex", "grok", "agy"}
    eligible = load_formal_review_eligible()
    assert eligible["codex"] is True
    assert eligible["claude"] is True
    for name in ("agy", "grok", "kimi"):
        assert eligible[name] is False


def test_cli_main_ok_on_repo():
    assert main([]) == 0


def test_seat_add_remove_pin_and_eligibility_flip_fail(tmp_path: Path):
    catalog, comms, seats, eligible = _mini_authorities(tmp_path)
    proj = tmp_path / "proj.md"

    # Corrected fixtures pass.
    _write_projection(proj, seats, eligible)
    assert lint_fleet_roster(
        catalog_path=catalog,
        comms_path=comms,
        projection_paths=[proj],
        project_root=tmp_path,
    ) == []

    # Seat remove (drop grok from projection).
    broken_seats = {k: v for k, v in seats.items() if k != "grok"}
    _write_projection(proj, broken_seats, eligible)
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert any("missing seat(s): grok" in i.message for i in issues)

    # Seat remove (Codex is a required HydrationCapsuleV1 driver).
    without_codex = {k: v for k, v in seats.items() if k != "codex"}
    _write_projection(proj, without_codex, eligible)
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert any("missing seat(s): codex" in i.message for i in issues)

    # Pin change.
    pin_changed = {k: dict(v) for k, v in seats.items()}
    pin_changed["claude"]["model_id"] = "claude-opus-4-8"
    _write_projection(proj, pin_changed, eligible)
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert any("claude" in i.message and "claude-opus-4-8" in i.message for i in issues)

    # Eligibility flip.
    flipped = dict(eligible)
    flipped["agy"] = True
    _write_projection(proj, seats, flipped)
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert any("agy" in i.message and "False" in i.message for i in issues)


def test_codex_required_as_driver_and_cf_eligible(tmp_path: Path):
    catalog, comms, seats, eligible = _mini_authorities(tmp_path)
    # Authority missing Codex as a driver → lint fails hard.
    missing_codex = {key: value for key, value in seats.items() if key != "codex"}
    catalog.write_text(
        yaml.safe_dump({"orchestrator_seats": missing_codex}, sort_keys=True),
        encoding="utf-8",
    )
    proj = tmp_path / "proj.md"
    _write_projection(proj, missing_codex, eligible)
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert any("codex must be an orchestrator_seats driver" in i.message for i in issues)

    valid_seats = dict(seats)
    catalog.write_text(
        yaml.safe_dump({"orchestrator_seats": valid_seats}, sort_keys=True),
        encoding="utf-8",
    )
    _write_projection(proj, valid_seats, eligible)
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert issues == []

    # Strip Codex CF eligibility → fails.
    bad_elig = dict(eligible)
    bad_elig["codex"] = False
    endpoints = [
        {"name": name, "formal_review_eligible": flag}
        for name, flag in sorted(bad_elig.items())
    ]
    comms.write_text(
        yaml.safe_dump({"version": 1, "endpoints": endpoints}, sort_keys=False),
        encoding="utf-8",
    )
    _write_projection(proj, valid_seats, bad_elig)
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert any("codex must remain formal_review_eligible: true" in i.message for i in issues)


def test_malformed_or_missing_markers_fail(tmp_path: Path):
    catalog, comms, seats, eligible = _mini_authorities(tmp_path)
    proj = tmp_path / "proj.md"
    proj.write_text("# no markers\n", encoding="utf-8")
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert any(i.kind == "orchestrator_seats" and "missing" in i.message for i in issues)
    assert any(i.kind == "formal_review_eligible" and "missing" in i.message for i in issues)

    # Unclosed begin.
    proj.write_text(
        "<!-- fleet-roster-projection:begin orchestrator_seats -->\n"
        f"{format_seat_table(seats)}\n",
        encoding="utf-8",
    )
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert any("unclosed" in i.message for i in issues)

    # Wrong header.
    proj.write_text(
        "<!-- fleet-roster-projection:begin orchestrator_seats -->\n"
        "| seat | wrong |\n| --- | --- |\n| claude | x |\n"
        "<!-- fleet-roster-projection:end orchestrator_seats -->\n"
        + _elig_block(eligible),
        encoding="utf-8",
    )
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert any("header must be" in i.message for i in issues)

    # Short separator row (CF F001): header has 5 cols but separator is 1 cell.
    data_rows = "\n".join(
        f"| {seat} | {r['model_id']} | {r['effort']} | {r['escalate_model_id']} | {r['escalate_effort']} |"
        for seat, r in sorted(seats.items())
    )
    proj.write_text(
        "<!-- fleet-roster-projection:begin orchestrator_seats -->\n"
        "| seat | model_id | effort | escalate_model_id | escalate_effort |\n"
        "| --- |\n"
        f"{data_rows}\n"
        "<!-- fleet-roster-projection:end orchestrator_seats -->\n"
        + _elig_block(eligible),
        encoding="utf-8",
    )
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert any("invalid table separator" in i.message for i in issues), [
        i.as_dict() for i in issues
    ]


def test_parsers_strip_markdown_emphasis():
    block = dedent(
        """\
        | seat | model_id | effort | escalate_model_id | escalate_effort |
        | --- | --- | --- | --- | --- |
        | **claude** | `claude-sonnet-5` | high | `claude-fable-5` | xhigh |
        """
    )
    seats = parse_seat_projection(block)
    assert seats["claude"]["model_id"] == "claude-sonnet-5"
    assert set(seats["claude"]) == set(SEAT_FIELDS)

    eblock = dedent(
        """\
        | endpoint | formal_review_eligible |
        | --- | --- |
        | **codex** | true |
        """
    )
    assert parse_eligible_projection(eblock) == {"codex": True}


def test_missing_projection_file_fails(tmp_path: Path):
    catalog, comms, _, _ = _mini_authorities(tmp_path)
    missing = tmp_path / "nope.md"
    issues = lint_fleet_roster(
        catalog_path=catalog,
        comms_path=comms,
        projection_paths=[missing],
        project_root=tmp_path,
    )
    assert any(i.kind == "io" and "missing" in i.message for i in issues)


def test_duplicate_normalized_orchestrator_seat_names_fail(tmp_path: Path):
    """Whitespace-distinct YAML keys must not silently collapse (CF r2 F001)."""
    catalog = tmp_path / "model_catalog.yaml"
    # PyYAML cannot emit two keys that only differ by surrounding spaces via a
    # normal dump; write the ambiguous authority textually.
    catalog.write_text(
        dedent(
            """\
            orchestrator_seats:
              claude:
                model_id: claude-sonnet-5
                effort: high
                escalate_model_id: claude-fable-5
                escalate_effort: xhigh
              " claude":
                model_id: claude-sonnet-5
                effort: high
                escalate_model_id: claude-fable-5
                escalate_effort: xhigh
            """
        ),
        encoding="utf-8",
    )
    from scripts.lint.lint_fleet_roster import load_orchestrator_seats

    try:
        load_orchestrator_seats(catalog)
        raise AssertionError("expected ValueError for duplicate normalized seats")
    except ValueError as exc:
        assert "duplicate orchestrator_seats name after normalize" in str(exc)


def test_unmatched_projection_end_marker_fails(tmp_path: Path):
    """Stray end markers must fail closed (CF r3 F001)."""
    catalog, comms, seats, eligible = _mini_authorities(tmp_path)
    proj = tmp_path / "proj.md"
    proj.write_text(
        _seat_block(seats)
        + "\n<!-- fleet-roster-projection:end orchestrator_seats -->\n"
        + _elig_block(eligible),
        encoding="utf-8",
    )
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert any("unmatched" in i.message and "end" in i.message for i in issues), [
        i.as_dict() for i in issues
    ]


def test_typoed_projection_marker_fails(tmp_path: Path):
    """Unknown/typoed fleet-roster-projection comments fail closed (CF r4 F001)."""
    catalog, comms, seats, eligible = _mini_authorities(tmp_path)
    proj = tmp_path / "proj.md"
    proj.write_text(
        _seat_block(seats)
        + "\n<!-- fleet-roster-projection:begin orchestrator_seatz -->\n"
        + _elig_block(eligible),
        encoding="utf-8",
    )
    issues = lint_fleet_roster(
        catalog_path=catalog, comms_path=comms, projection_paths=[proj], project_root=tmp_path
    )
    assert any(i.kind == "markers" and "malformed" in i.message for i in issues), [
        i.as_dict() for i in issues
    ]

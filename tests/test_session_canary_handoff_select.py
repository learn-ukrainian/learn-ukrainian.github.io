"""Handoff selection ranks one freshness date, with own-lane as a same-day tiebreak."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from scripts.session_canary import (
    codex_lane,
    diary,
    gemini_lane,
    glm_lane,
    grok_lane,
    handoff_select,
    kimi_lane,
)

_STREAM = [
    {"type": "binding_order", "body": f"Binding order {i} forbids shortcuts in this lane."} for i in range(1, 5)
] + [
    {"type": "negative_constraint", "body": "Never commit directly to main from a driver."},
    {"type": "negative_constraint", "body": "Never merge without an independent cross-family review."},
]

_LANES = (
    (codex_lane, "CODEX-DRIVER-HANDOFF.md"),
    (gemini_lane, "GEMINI-DRIVER-HANDOFF.md"),
    (kimi_lane, "KIMI-DRIVER-HANDOFF.md"),
    (glm_lane, "GLM-DRIVER-HANDOFF.md"),
    (grok_lane, "GROK-DRIVER-HANDOFF.md"),
)


def _write(path: Path, text: str, *, mtime: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.utime(path, (mtime, mtime))


def _epic(tmp_path: Path) -> Path:
    epic = tmp_path / ".claude" / "atlas-epic"
    epic.mkdir(parents=True)
    return epic


def _full(sentinel: str, *, session: str | None = None) -> str:
    heading = f"## Session {session}\n\n" if session else ""
    nxt = "\n".join(f"{i}. {sentinel} next item {i}" for i in range(1, 6))
    hands = "\n".join(f"- {sentinel} hands-off {i}" for i in range(1, 6))
    return f"# Handoff\n\n{heading}## Next drive order\n{nxt}\n\n## Hands-off\n{hands}\n"


def _existing(paths: list[Path]) -> list[str]:
    return [path.name for path in paths if path.is_file()]


def _patch_mint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(grok_lane, "_load_stream_entries", lambda *_args, **_kwargs: list(_STREAM))

    def _freeze(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="minted\n", stderr="")

    monkeypatch.setattr(grok_lane.subprocess, "run", _freeze)


def _mint(module, tmp_path: Path, extra: list[str] | None = None) -> int:
    return module.main(
        [
            "--repo",
            str(tmp_path),
            "mint",
            "--epic",
            "atlas",
            "--stream",
            "lane-test",
            "--out-dir",
            str(tmp_path / "canary"),
            *(extra or []),
        ]
    )


def _answers(tmp_path: Path) -> str:
    facts = json.loads((tmp_path / "canary" / "facts.json").read_text(encoding="utf-8"))
    return " ".join(fact["a"] for fact in facts)


@pytest.mark.parametrize(("lane", "own_name"), _LANES)
def test_stale_interim_loses_to_fresh_claude_when_own_file_is_absent(
    tmp_path: Path, lane, own_name: str | None
) -> None:
    epic = _epic(tmp_path)
    _write(epic / "INTERIM-DRIVER-HANDOFF.md", "stale interim\n", mtime=1_000)
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", "fresh claude\n", mtime=5_000)
    _write(
        epic / "INTERIM-DRIVER-HANDOFF.20260914T193444Z.superseded.md",
        "archived\n",
        mtime=9_000,
    )
    names = _existing(lane._handoff_candidates(tmp_path, "atlas"))
    assert names[0] == "CLAUDE-DRIVER-HANDOFF.md"
    assert "INTERIM-DRIVER-HANDOFF.md" in names
    assert all("superseded" not in name for name in names)
    if own_name is not None:
        assert own_name not in names


@pytest.mark.parametrize(("lane", "own_name"), [row for row in _LANES if row[1]])
def test_own_lane_handoff_wins_when_fresh(tmp_path: Path, lane, own_name: str) -> None:
    epic = _epic(tmp_path)
    _write(epic / "INTERIM-DRIVER-HANDOFF.md", "interim\n", mtime=1_000)
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", "claude\n", mtime=3_000)
    _write(epic / own_name, "own\n", mtime=5_000)
    assert _existing(lane._handoff_candidates(tmp_path, "atlas"))[0] == own_name


@pytest.mark.parametrize(("lane", "own_name"), [row for row in _LANES if row[1]])
def test_stale_own_lane_loses_to_a_fresher_claude_handoff(tmp_path: Path, lane, own_name: str) -> None:
    epic = _epic(tmp_path)
    _write(epic / own_name, "## Session 2026-09-18\n\nown\n", mtime=9_000_000_000)
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", "## Session 2026-09-23\n\nclaude\n", mtime=50)
    assert _existing(lane._handoff_candidates(tmp_path, "atlas"))[0] == "CLAUDE-DRIVER-HANDOFF.md"


@pytest.mark.parametrize(("lane", "own_name"), [row for row in _LANES if row[1]])
def test_same_day_own_lane_handoff_wins_the_tie(tmp_path: Path, lane, own_name: str) -> None:
    epic = _epic(tmp_path)
    _write(epic / own_name, "## Session 2026-09-23\n\nown\n", mtime=50)
    if own_name != "CLAUDE-DRIVER-HANDOFF.md":
        _write(epic / "CLAUDE-DRIVER-HANDOFF.md", "## Session 2026-09-23\n\nclaude\n", mtime=9_000_000_000)
    assert _existing(lane._handoff_candidates(tmp_path, "atlas"))[0] == own_name


def test_touched_undated_interim_loses_to_dated_claude(tmp_path: Path) -> None:
    epic = _epic(tmp_path)
    _write(epic / "INTERIM-DRIVER-HANDOFF.md", "# Interim\n\nno session heading\n", mtime=5_000_000_000)
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", "## Session 2026-09-23\n\nfresh\n", mtime=50)
    assert _existing(grok_lane._handoff_candidates(tmp_path, "atlas"))[0] == "CLAUDE-DRIVER-HANDOFF.md"


def test_grok_handoff_is_selectable_when_it_is_the_freshest(tmp_path: Path) -> None:
    epic = tmp_path / ".claude" / "infra-epic"
    epic.mkdir(parents=True)
    _write(epic / "GROK-DRIVER-HANDOFF.md", "## Session 2026-09-23\n\ngrok\n", mtime=50)
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", "## Session 2026-09-18\n\nclaude\n", mtime=9_000_000_000)
    _write(epic / "INTERIM-DRIVER-HANDOFF.md", "undated interim\n", mtime=9_000_000_000)
    ranked = _existing(grok_lane._handoff_candidates(tmp_path, "infra"))
    assert ranked[0] == "GROK-DRIVER-HANDOFF.md"
    assert "GROK-DRIVER-HANDOFF.md" in ranked


def test_session_heading_beats_equal_mtime_and_a_later_touch(tmp_path: Path) -> None:
    epic = _epic(tmp_path)
    interim = epic / "INTERIM-DRIVER-HANDOFF.md"
    claude = epic / "CLAUDE-DRIVER-HANDOFF.md"
    _write(interim, "## Session 2026-09-14\n\nstale\n", mtime=5_000_000_000)
    _write(claude, "## Session 2026-09-23\n\nfresh\n", mtime=50)
    # Equalize after the touched-stale case is covered by the huge interim mtime.
    ranked = _existing(grok_lane._handoff_candidates(tmp_path, "atlas"))
    assert ranked[0] == "CLAUDE-DRIVER-HANDOFF.md"

    os.utime(interim, (50, 50))
    os.utime(claude, (50, 50))
    ranked = _existing(grok_lane._handoff_candidates(tmp_path, "atlas"))
    assert ranked[0] == "CLAUDE-DRIVER-HANDOFF.md"


def test_ranker_drops_a_listed_superseded_file(tmp_path: Path) -> None:
    stale = tmp_path / "INTERIM-DRIVER-HANDOFF.20260914T193444Z.superseded.md"
    fresh = tmp_path / "CLAUDE-DRIVER-HANDOFF.md"
    _write(stale, "## Session 2026-09-23\n", mtime=9_000)
    _write(fresh, "plain\n", mtime=1)
    ranked = handoff_select.rank_handoff_candidates([stale, fresh], preferred=("INTERIM-DRIVER-HANDOFF.md",))
    assert [path.name for path in ranked] == ["CLAUDE-DRIVER-HANDOFF.md"]


def test_glm_bootstrap_candidates_match_the_mint_preference(tmp_path: Path) -> None:
    epic = _epic(tmp_path)
    _write(epic / "GLM-DRIVER-HANDOFF.md", "glm\n", mtime=1_000)
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", "claude\n", mtime=8_000)
    direct = [path.name for path in glm_lane._handoff_candidates(tmp_path, "atlas")]
    via_mint = [
        path.name
        for path in grok_lane._handoff_candidates(tmp_path, "atlas", preferred=["GLM-DRIVER-HANDOFF.md"])
    ]
    assert direct == via_mint
    assert direct[0] == "GLM-DRIVER-HANDOFF.md"


def test_mint_picks_fresh_claude_over_stale_interim(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    _write(epic / "INTERIM-DRIVER-HANDOFF.md", _full("interim-sentinel"), mtime=1_000)
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", _full("claude-sentinel", session="2026-09-23"), mtime=5_000)
    _write(
        epic / "INTERIM-DRIVER-HANDOFF.20260914T193444Z.superseded.md",
        _full("superseded-sentinel", session="2026-09-23"),
        mtime=9_000_000_000,
    )

    assert _mint(grok_lane, tmp_path) == 0
    answers = _answers(tmp_path)
    assert "claude-sentinel" in answers
    assert "interim-sentinel" not in answers
    assert "superseded-sentinel" not in answers
    meta = json.loads((tmp_path / "canary" / "mint_meta.json").read_text(encoding="utf-8"))
    assert meta["handoff"].endswith("CLAUDE-DRIVER-HANDOFF.md")


def test_mint_uses_newer_session_heading_when_the_stale_file_was_touched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    _write(
        epic / "INTERIM-DRIVER-HANDOFF.md",
        _full("interim-sentinel", session="2026-09-14"),
        mtime=5_000_000_000,
    )
    _write(
        epic / "CLAUDE-DRIVER-HANDOFF.md",
        _full("claude-sentinel", session="2026-09-23"),
        mtime=1_000,
    )

    assert _mint(grok_lane, tmp_path) == 0
    answers = _answers(tmp_path)
    assert "claude-sentinel" in answers
    assert "interim-sentinel" not in answers


def test_mint_own_lane_handoff_wins_when_fresh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    _write(epic / "CODEX-DRIVER-HANDOFF.md", _full("own-sentinel"), mtime=5_000)
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", _full("claude-sentinel"), mtime=3_000)
    _write(epic / "INTERIM-DRIVER-HANDOFF.md", _full("interim-sentinel"), mtime=1_000)

    assert _mint(codex_lane, tmp_path) == 0
    answers = _answers(tmp_path)
    assert "own-sentinel" in answers
    assert "claude-sentinel" not in answers
    assert "interim-sentinel" not in answers


def test_shortfall_falls_through_to_the_next_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    _write(epic / "CODEX-DRIVER-HANDOFF.md", "# Codex\n\nNo next or hands-off sections.\n", mtime=8_000)
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", _full("claude-sentinel"), mtime=1_000)

    assert _mint(codex_lane, tmp_path) == 0
    assert "claude-sentinel" in _answers(tmp_path)
    meta = json.loads((tmp_path / "canary" / "mint_meta.json").read_text(encoding="utf-8"))
    assert meta["handoff"].endswith("CLAUDE-DRIVER-HANDOFF.md")


def test_shortfall_error_lists_each_file_with_next_and_hands_off_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    _write(
        epic / "CLAUDE-DRIVER-HANDOFF.md",
        "## Next drive order\n1. only one claude next item\n",
        mtime=5_000,
    )
    _write(epic / "INTERIM-DRIVER-HANDOFF.md", "## Hands-off\n- one interim boundary\n", mtime=1_000)

    assert _mint(grok_lane, tmp_path) == 1
    err = capsys.readouterr().err
    assert "could only derive 9/10" in err
    claude = "CLAUDE-DRIVER-HANDOFF.md (next=1, hands-off=0)"
    interim = "INTERIM-DRIVER-HANDOFF.md (next=0, hands-off=1)"
    assert claude in err
    assert interim in err
    assert err.index(claude) < err.index(interim)


def test_explicit_handoff_overrides_a_fresher_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    explicit = tmp_path / "operator-handoff.md"
    _write(explicit, _full("explicit-sentinel"), mtime=100)
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", _full("claude-sentinel"), mtime=9_000)

    assert _mint(grok_lane, tmp_path, ["--handoff", str(explicit)]) == 0
    answers = _answers(tmp_path)
    assert "explicit-sentinel" in answers
    assert "claude-sentinel" not in answers


def test_explicit_shortfall_falls_through_before_failing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_mint(monkeypatch)
    explicit = tmp_path / "operator-handoff.md"
    _write(explicit, "# Operator\n\nEmpty of sections.\n", mtime=9_000)
    _write(_epic(tmp_path) / "CLAUDE-DRIVER-HANDOFF.md", _full("claude-sentinel"), mtime=1_000)

    assert _mint(grok_lane, tmp_path, ["--handoff", str(explicit)]) == 0
    assert "claude-sentinel" in _answers(tmp_path)


def test_kimi_board_matches_canary_handoff_after_fallthrough(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    _write(
        epic / "KIMI-DRIVER-HANDOFF.md",
        "# Kimi\n\n## Session 2026-09-23\n\nNo next or hands-off sections.\n",
        mtime=8_000,
    )
    _write(
        epic / "CLAUDE-DRIVER-HANDOFF.md",
        _full("claude-sentinel", session="2026-09-23"),
        mtime=1_000,
    )

    assert (
        kimi_lane.main(
            ["--repo", str(tmp_path), "mint", "--epic", "atlas", "--stream", "lane-test"]
        )
        == 0
    )
    meta = json.loads((epic / "canary" / "mint_meta.json").read_text(encoding="utf-8"))
    assert meta["handoff"].endswith("CLAUDE-DRIVER-HANDOFF.md")
    assert "claude-sentinel" in (epic / "canary" / "facts.json").read_text(encoding="utf-8")

    kimi_lane._write_cold_start(
        epic,
        epic="atlas",
        stream_id="lane-test",
        lease_summary="test",
        repo=tmp_path,
    )
    board = (epic / "KIMI-COLD-START.md").read_text(encoding="utf-8")
    assert meta["handoff"] in board
    bound = grok_lane._bound_handoff_path(tmp_path, "atlas")
    assert handoff_select.display_repo_path(tmp_path, bound) == meta["handoff"]


@pytest.mark.parametrize(
    ("lane", "board_name"),
    [
        (codex_lane, "CODEX-COLD-START.md"),
        (gemini_lane, "GEMINI-COLD-START.md"),
        (glm_lane, "GLM-COLD-START.md"),
        (kimi_lane, "KIMI-COLD-START.md"),
    ],
)
def test_cold_start_board_uses_the_recorded_mint_file(tmp_path: Path, lane, board_name: str) -> None:
    epic = _epic(tmp_path)
    canary = epic / "canary"
    canary.mkdir()
    own = {
        codex_lane: "CODEX-DRIVER-HANDOFF.md",
        gemini_lane: "GEMINI-DRIVER-HANDOFF.md",
        glm_lane: "GLM-DRIVER-HANDOFF.md",
        kimi_lane: "KIMI-DRIVER-HANDOFF.md",
    }[lane]
    _write(epic / own, "## Session 2026-09-23\n\nown\n", mtime=9_000)
    claude_text = "## Session 2026-09-23\n\nclaude\n"
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", claude_text, mtime=1)
    recorded = ".claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md"
    (canary / "mint_meta.json").write_text(
        json.dumps(
            {
                "handoff": recorded,
                "handoff_sha256": handoff_select.text_sha256(claude_text),
            }
        ),
        encoding="utf-8",
    )

    if lane is kimi_lane:
        lane._write_cold_start(
            epic, epic="atlas", stream_id="lane-test", lease_summary="test", repo=tmp_path
        )
    else:
        assert lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "atlas"]) == 0

    board = (epic / board_name).read_text(encoding="utf-8")
    assert f"**Handoff dual-write:** `{recorded}`" in board


def test_explicit_superseded_path_is_not_minted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    superseded = epic / "INTERIM-DRIVER-HANDOFF.20260914T193444Z.superseded.md"
    _write(superseded, _full("superseded-sentinel"), mtime=9_000)
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", _full("claude-sentinel"), mtime=1_000)

    assert _mint(grok_lane, tmp_path, ["--handoff", str(superseded)]) == 0
    answers = _answers(tmp_path)
    assert "claude-sentinel" in answers
    assert "superseded-sentinel" not in answers


def test_gemini_board_and_mint_both_fall_through_a_short_own_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Board before mint must name the same file mint records (#8588 finding 5)."""
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    _write(
        epic / "GEMINI-DRIVER-HANDOFF.md",
        "# Gemini\n\n## Session 2026-09-23\n\nNo next or hands-off sections.\n",
        mtime=9_000,
    )
    _write(
        epic / "CLAUDE-DRIVER-HANDOFF.md",
        _full("claude-sentinel", session="2026-09-23"),
        mtime=1_000,
    )

    assert (
        gemini_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "atlas", "--stream", "lane-test"])
        == 0
    )
    board = (epic / "GEMINI-COLD-START.md").read_text(encoding="utf-8")
    assert "**Handoff dual-write:** `.claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md`" in board

    assert _mint(gemini_lane, tmp_path) == 0
    meta = json.loads((tmp_path / "canary" / "mint_meta.json").read_text(encoding="utf-8"))
    assert meta["handoff"].endswith("CLAUDE-DRIVER-HANDOFF.md")
    assert "claude-sentinel" in _answers(tmp_path)


def test_score_and_board_fail_closed_when_the_recorded_handoff_is_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After mint, consumers use only the recorded file — never re-rank (#8588 finding 6)."""
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    gemini = epic / "GEMINI-DRIVER-HANDOFF.md"
    _write(gemini, _full("gemini-sentinel", session="2026-09-23"), mtime=9_000)
    _write(
        epic / "CLAUDE-DRIVER-HANDOFF.md",
        _full("claude-sentinel", session="2026-09-23"),
        mtime=1_000,
    )

    assert gemini_lane.main(["--repo", str(tmp_path), "mint", "--epic", "atlas", "--stream", "lane-test"]) == 0
    canary = epic / "canary"
    meta = json.loads((canary / "mint_meta.json").read_text(encoding="utf-8"))
    assert meta["handoff"].endswith("GEMINI-DRIVER-HANDOFF.md")
    facts = json.loads((canary / "facts.json").read_text(encoding="utf-8"))
    (canary / "probe.json").write_text(json.dumps({"anchors": facts}), encoding="utf-8")

    gemini.unlink()

    with pytest.raises(handoff_select.RecordedHandoffMissingError, match=re.escape("GEMINI-DRIVER-HANDOFF.md")):
        gemini_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "atlas", "--stream", "lane-test"])

    answers = tmp_path / "answers.json"
    answers.write_text(json.dumps({fact["id"]: fact["a"] for fact in facts}), encoding="utf-8")
    with pytest.raises(handoff_select.RecordedHandoffMissingError, match=re.escape("GEMINI-DRIVER-HANDOFF.md")):
        gemini_lane.main(
            [
                "--repo",
                str(tmp_path),
                "score",
                "--epic",
                "atlas",
                "--stream",
                "lane-test",
                "--answers",
                str(answers),
            ]
        )
    with pytest.raises(handoff_select.RecordedHandoffMissingError, match=re.escape("GEMINI-DRIVER-HANDOFF.md")):
        grok_lane.emit_hydrate_capsule(
            repo=tmp_path,
            epic="atlas",
            out_dir=canary,
            print_stdout=False,
        )

    # Restore the recorded file: the normal recorded-file path still wins.
    _write(gemini, _full("gemini-sentinel", session="2026-09-23"), mtime=9_000)
    bound = grok_lane._bound_handoff_path(tmp_path, "atlas", out_dir=canary)
    assert bound == gemini


def _stream_alone() -> list[dict[str, str]]:
    """Stream entries that yield 10 anchors with an empty handoff."""
    return [
        *_STREAM,
        {"type": "next_action", "body": "Stream next action one for this lane."},
        {"type": "next_action", "body": "Stream next action two for this lane."},
    ]


def _patch_stream(monkeypatch: pytest.MonkeyPatch, entries: list[dict[str, str]]) -> None:
    monkeypatch.setattr(grok_lane, "_load_stream_entries", lambda *_args, **_kwargs: list(entries))

    def _freeze(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="minted\n", stderr="")

    monkeypatch.setattr(grok_lane.subprocess, "run", _freeze)


def _score(tmp_path: Path, epic_canary: Path, facts: list[dict[str, str]]) -> int:
    (epic_canary / "probe.json").write_text(json.dumps({"anchors": facts}), encoding="utf-8")
    answers = tmp_path / "answers.json"
    answers.write_text(json.dumps({fact["id"]: fact["a"] for fact in facts}), encoding="utf-8")
    return grok_lane.main(
        [
            "--repo",
            str(tmp_path),
            "score",
            "--epic",
            "atlas",
            "--out-dir",
            str(epic_canary),
            "--answers",
            str(answers),
            "--no-hydrate",
        ]
    )


def test_stream_alone_board_and_mint_both_report_no_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stream supplies the anchors and no handoff file exists (#8588 finding 1)."""
    _patch_stream(monkeypatch, _stream_alone())
    _epic(tmp_path)

    assert (
        gemini_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "atlas", "--stream", "lane-test"])
        == 0
    )
    board = (tmp_path / ".claude" / "atlas-epic" / "GEMINI-COLD-START.md").read_text(encoding="utf-8")
    assert "**Handoff dual-write:** `(no handoff)`" in board
    assert "GEMINI-DRIVER-HANDOFF.md" not in board

    assert _mint(gemini_lane, tmp_path) == 0
    meta = json.loads((tmp_path / "canary" / "mint_meta.json").read_text(encoding="utf-8"))
    assert meta["handoff"] is None
    assert meta["handoff_sha256"] is None
    assert meta["n_anchors"] >= 10


def test_recorded_no_handoff_stays_when_a_file_appears_later(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A minted null is binding for score, board, and diary (#8588 finding 2)."""
    _patch_stream(monkeypatch, _stream_alone())
    epic = _epic(tmp_path)
    assert gemini_lane.main(["--repo", str(tmp_path), "mint", "--epic", "atlas", "--stream", "lane-test"]) == 0
    canary = epic / "canary"
    meta = json.loads((canary / "mint_meta.json").read_text(encoding="utf-8"))
    assert meta["handoff"] is None
    assert meta["handoff_sha256"] is None
    facts = json.loads((canary / "facts.json").read_text(encoding="utf-8"))

    late = epic / "GEMINI-DRIVER-HANDOFF.md"
    _write(late, _full("late-sentinel", session="2026-09-23"), mtime=9_000)
    before = late.read_text(encoding="utf-8")

    assert (
        gemini_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "atlas", "--stream", "lane-test"])
        == 0
    )
    board = (epic / "GEMINI-COLD-START.md").read_text(encoding="utf-8")
    assert "**Handoff dual-write:** `(no handoff)`" in board
    assert "GEMINI-DRIVER-HANDOFF.md" not in board

    assert diary.resolve_handoff_path(tmp_path, "atlas", out_dir=canary) is handoff_select.NO_HANDOFF
    assert grok_lane._bound_handoff_path(tmp_path, "atlas", out_dir=canary) is handoff_select.NO_HANDOFF

    assert _score(tmp_path, canary, facts) == 0
    scored = capsys.readouterr().out
    assert "diary: (no handoff)" in scored
    hydrate_rc, hydrate_meta = grok_lane.emit_hydrate_capsule(
        repo=tmp_path,
        epic="atlas",
        out_dir=canary,
        print_stdout=False,
    )
    assert hydrate_rc == 1
    assert hydrate_meta["error"] == "no_handoff"
    assert "late-sentinel" not in str(hydrate_meta)
    assert late.read_text(encoding="utf-8") == before


def test_unreadable_recorded_handoff_is_not_swallowed_by_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """PermissionError on the recorded file fails the score path (#8588 finding 3)."""
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    gemini = epic / "GEMINI-DRIVER-HANDOFF.md"
    _write(gemini, _full("gemini-sentinel", session="2026-09-23"), mtime=9_000)
    assert gemini_lane.main(["--repo", str(tmp_path), "mint", "--epic", "atlas", "--stream", "lane-test"]) == 0
    canary = epic / "canary"
    facts = json.loads((canary / "facts.json").read_text(encoding="utf-8"))

    real_read = Path.read_text

    def _read(self: Path, *args, **kwargs):
        if self.name == "GEMINI-DRIVER-HANDOFF.md":
            raise PermissionError("denied")
        return real_read(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", _read)

    assert handoff_select.recorded_mint_handoff(tmp_path, "atlas", canary) == gemini

    with pytest.raises(handoff_select.RecordedHandoffMissingError, match="PermissionError") as scored:
        _score(tmp_path, canary, facts)
    assert "GEMINI-DRIVER-HANDOFF.md" in str(scored.value)

    with pytest.raises(handoff_select.RecordedHandoffMissingError, match="PermissionError") as hydrated:
        grok_lane.emit_hydrate_capsule(
            repo=tmp_path,
            epic="atlas",
            out_dir=canary,
            print_stdout=False,
        )
    assert "GEMINI-DRIVER-HANDOFF.md" in str(hydrated.value)


def test_mint_uses_the_selected_text_when_the_file_changes_after_select(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rewrite between selection and fact building cannot mint eight anchors."""
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    original = _full("selected-sentinel", session="2026-09-23")
    path = epic / "CLAUDE-DRIVER-HANDOFF.md"
    _write(path, original, mtime=5_000)
    real_select = handoff_select.select_handoff

    def _select_then_rewrite(**kwargs):
        chosen = real_select(**kwargs)
        if chosen.path is not None:
            chosen.path.write_text("# rewritten\n\nno next or hands-off sections\n", encoding="utf-8")
        return chosen

    monkeypatch.setattr(handoff_select, "select_handoff", _select_then_rewrite)

    assert _mint(grok_lane, tmp_path) == 0
    assert "selected-sentinel" in _answers(tmp_path)
    assert "rewritten" not in _answers(tmp_path)
    meta = json.loads((tmp_path / "canary" / "mint_meta.json").read_text(encoding="utf-8"))
    assert meta["n_anchors"] >= 10
    assert meta["handoff_sha256"] == handoff_select.text_sha256(original)
    assert path.read_text(encoding="utf-8").startswith("# rewritten")


def test_living_edit_after_mint_is_a_notice_not_a_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A recorded file edited after mint still scores. The digest is a notice."""
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    gemini = epic / "GEMINI-DRIVER-HANDOFF.md"
    _write(gemini, _full("gemini-sentinel", session="2026-09-23"), mtime=9_000)
    assert gemini_lane.main(["--repo", str(tmp_path), "mint", "--epic", "atlas", "--stream", "lane-test"]) == 0
    canary = epic / "canary"
    facts = json.loads((canary / "facts.json").read_text(encoding="utf-8"))
    gemini.write_text(gemini.read_text(encoding="utf-8") + "\nextra line after mint\n", encoding="utf-8")

    assert (
        gemini_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "atlas", "--stream", "lane-test"])
        == 0
    )
    board = (epic / "GEMINI-COLD-START.md").read_text(encoding="utf-8")
    assert "**Handoff dual-write:** `.claude/atlas-epic/GEMINI-DRIVER-HANDOFF.md`" in board
    assert diary.resolve_handoff_path(tmp_path, "atlas", out_dir=canary) == gemini

    assert _score(tmp_path, canary, facts) == 0
    verdict = json.loads((canary / "last_verdict.json").read_text(encoding="utf-8"))
    assert verdict["handoff_changed_since_mint"] is True
    assert verdict["verdict"] == "PASS"


def test_absent_mint_meta_keeps_cold_start_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No mint record still selects: the board by anchors, the diary by freshness."""
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    _write(
        epic / "GEMINI-DRIVER-HANDOFF.md",
        "# Gemini\n\n## Session 2026-09-23\n\nNo next or hands-off sections.\n",
        mtime=9_000,
    )
    _write(
        epic / "CLAUDE-DRIVER-HANDOFF.md",
        _full("claude-sentinel", session="2026-09-23"),
        mtime=1_000,
    )
    assert handoff_select.recorded_mint_handoff(tmp_path, "atlas") is None

    assert (
        gemini_lane.main(["--repo", str(tmp_path), "bootstrap", "--epic", "atlas", "--stream", "lane-test"])
        == 0
    )
    board = (epic / "GEMINI-COLD-START.md").read_text(encoding="utf-8")
    assert "**Handoff dual-write:** `.claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md`" in board

    resolved = diary.resolve_handoff_path(tmp_path, "atlas")
    ranked = handoff_select.lane_handoff_candidates(
        tmp_path,
        "atlas",
        handoff_select.LANE_HANDOFF_NAMES,
    )
    assert resolved == handoff_select.chosen_handoff_path(ranked)
    assert resolved == epic / "GEMINI-DRIVER-HANDOFF.md"


def test_explicit_handoff_after_mint_does_not_rewrite_the_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``--handoff B`` stamps B for that call. mint_meta still names A."""
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    recorded = epic / "GEMINI-DRIVER-HANDOFF.md"
    _write(recorded, _full("gemini-sentinel", session="2026-09-23"), mtime=9_000)
    assert gemini_lane.main(["--repo", str(tmp_path), "mint", "--epic", "atlas", "--stream", "lane-test"]) == 0
    canary = epic / "canary"
    before = json.loads((canary / "mint_meta.json").read_text(encoding="utf-8"))
    facts = json.loads((canary / "facts.json").read_text(encoding="utf-8"))
    (canary / "probe.json").write_text(json.dumps({"anchors": facts}), encoding="utf-8")
    answers = tmp_path / "answers.json"
    answers.write_text(json.dumps({fact["id"]: fact["a"] for fact in facts}), encoding="utf-8")
    other = tmp_path / "operator-handoff.md"
    _write(other, _full("other-sentinel"), mtime=1)
    before_recorded = recorded.read_text(encoding="utf-8")

    rc = grok_lane.main(
        [
            "--repo",
            str(tmp_path),
            "score",
            "--epic",
            "atlas",
            "--out-dir",
            str(canary),
            "--answers",
            str(tmp_path / "answers.json"),
            "--no-hydrate",
            "--handoff",
            str(other),
        ]
    )
    assert rc == 0
    after = json.loads((canary / "mint_meta.json").read_text(encoding="utf-8"))
    assert after["handoff"] == before["handoff"]
    assert after["handoff_sha256"] == before["handoff_sha256"]
    assert after["handoff"].endswith("GEMINI-DRIVER-HANDOFF.md")
    assert "canary score PASS" in other.read_text(encoding="utf-8")
    assert recorded.read_text(encoding="utf-8") == before_recorded
    assert grok_lane._bound_handoff_path(tmp_path, "atlas", out_dir=canary) == recorded
    assert diary.resolve_handoff_path(tmp_path, "atlas", out_dir=canary) == recorded


def test_board_and_mint_share_a_custom_stream_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same --stream-limit selects the same handoff on the preview board and at mint."""
    entries = [
        {"type": "binding_order", "body": f"Binding order {i} forbids shortcuts in this lane."}
        for i in range(1, 5)
    ] + [
        {"type": "negative_constraint", "body": "Never commit directly to main from a driver."},
        {"type": "negative_constraint", "body": "Never merge without an independent cross-family review."},
        {"type": "next_action", "body": "Stream next action one for this lane."},
        {"type": "next_action", "body": "Stream next action two for this lane."},
    ]

    def _load(_stream_id: str, *, limit: int = 40) -> list[dict[str, str]]:
        return [dict(item) for item in entries[: int(limit)]]

    monkeypatch.setattr(grok_lane, "_load_stream_entries", _load)

    def _freeze(command, **_kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="minted\n", stderr="")

    monkeypatch.setattr(grok_lane.subprocess, "run", _freeze)
    epic = _epic(tmp_path)
    _write(
        epic / "GEMINI-DRIVER-HANDOFF.md",
        "# Gemini\n\n## Session 2026-09-23\n\nNo next or hands-off sections.\n",
        mtime=9_000,
    )
    _write(
        epic / "CLAUDE-DRIVER-HANDOFF.md",
        _full("claude-sentinel", session="2026-09-18"),
        mtime=1_000,
    )

    def board(limit: int) -> str:
        assert (
            gemini_lane.main(
                [
                    "--repo",
                    str(tmp_path),
                    "bootstrap",
                    "--epic",
                    "atlas",
                    "--stream",
                    "lane-test",
                    "--stream-limit",
                    str(limit),
                ]
            )
            == 0
        )
        return (epic / "GEMINI-COLD-START.md").read_text(encoding="utf-8")

    wide = board(8)
    assert "**Handoff binding:** preview" in wide
    assert "**Handoff dual-write:** `.claude/atlas-epic/GEMINI-DRIVER-HANDOFF.md`" in wide
    narrow = board(4)
    assert "**Handoff binding:** preview" in narrow
    assert "**Handoff dual-write:** `.claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md`" in narrow

    assert (
        gemini_lane.main(
            [
                "--repo",
                str(tmp_path),
                "mint",
                "--epic",
                "atlas",
                "--stream",
                "lane-test",
                "--stream-limit",
                "4",
            ]
        )
        == 0
    )
    meta = json.loads((epic / "canary" / "mint_meta.json").read_text(encoding="utf-8"))
    assert meta["handoff"].endswith("CLAUDE-DRIVER-HANDOFF.md")
    assert meta["stream_limit"] == 4
    assert meta["candidates"][0].endswith("GEMINI-DRIVER-HANDOFF.md")
    assert any(name.endswith("CLAUDE-DRIVER-HANDOFF.md") for name in meta["candidates"])

    stuck = board(8)
    assert "**Handoff binding:** recorded path" in stuck
    assert "**Handoff dual-write:** `.claude/atlas-epic/CLAUDE-DRIVER-HANDOFF.md`" in stuck
    assert "preview (not minted)" not in stuck


def test_rewrite_between_ranking_and_mint_keeps_the_ranked_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mint facts come from the text ranking already read, not a second read."""
    _patch_mint(monkeypatch)
    epic = _epic(tmp_path)
    original = _full("ranked-sentinel", session="2026-09-23")
    path = epic / "CLAUDE-DRIVER-HANDOFF.md"
    _write(path, original, mtime=5_000)
    real_load = handoff_select.load_and_rank_candidates

    def _load_then_rewrite(*args, **kwargs):
        loaded = real_load(*args, **kwargs)
        for item in loaded:
            if item.path.name == "CLAUDE-DRIVER-HANDOFF.md" and item.text:
                item.path.write_text("# rewritten\n\nno next or hands-off sections\n", encoding="utf-8")
        return loaded

    monkeypatch.setattr(handoff_select, "load_and_rank_candidates", _load_then_rewrite)

    assert _mint(grok_lane, tmp_path) == 0
    assert "ranked-sentinel" in _answers(tmp_path)
    assert "rewritten" not in _answers(tmp_path)
    assert path.read_text(encoding="utf-8").startswith("# rewritten")

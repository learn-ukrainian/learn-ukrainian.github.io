"""Handoff selection prefers the lane file, then the freshest valid candidate."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from scripts.session_canary import codex_lane, gemini_lane, glm_lane, grok_lane, handoff_select, kimi_lane

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
    (grok_lane, None),
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
def test_own_lane_handoff_outranks_a_newer_shared_file(tmp_path: Path, lane, own_name: str) -> None:
    epic = _epic(tmp_path)
    _write(epic / own_name, "own\n", mtime=1_000)
    _write(epic / "CLAUDE-DRIVER-HANDOFF.md", "newer shared\n", mtime=8_000)
    assert _existing(lane._handoff_candidates(tmp_path, "atlas"))[0] == own_name


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

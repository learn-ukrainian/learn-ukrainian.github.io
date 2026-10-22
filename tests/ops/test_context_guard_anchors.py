"""The context guard checks a lane handoff with the launcher's own anchor selector (#11404).

The Atlas lane died twice with a handoff the Codex launcher refused
(``error: could only derive 8/10 durable anchors``) while the guard had already
typed ``/quit``. These tests pin the shared verdict, the send-back before the
exit, the bounded retries, the fail-open path and the post-relaunch launcher
exit alert. Each docstring names the defect class it can fail for.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from scripts.ops import context_guard as cg
from scripts.session_canary import grok_lane, handoff_select
from tests.ops.test_context_guard import Harness, codex_pane

REPO = Path(__file__).resolve().parents[2]

STREAM = [
    {"type": "binding_order", "body": "Anchor check fixture binding order one."},
    {"type": "binding_order", "body": "Anchor check fixture binding order two."},
    {"type": "negative_constraint", "body": "Anchor check fixture negative constraint."},
]
CONFLICTING_STREAM = [
    {"type": "binding_order", "body": f"Another lane binding order {index}."} for index in range(1, 5)
] + [{"type": "negative_constraint", "body": f"Another lane negative constraint {index}."} for index in range(1, 3)]

NEXT_THREE = "\n".join(f"{index}. anchor-check next item {index}" for index in range(1, 4))
HANDS_TWO = "\n".join(f"- anchor-check hands-off rule {index}" for index in range(1, 3))
SENDER = "codex-atlas"
LANE = "atlas"
LAUNCHER_EXIT_RC1 = (
    "booting codex lane\n"
    "error: could only derive 8/10 durable anchors; tried .claude/atlas-epic/CODEX-DRIVER-HANDOFF.md "
    "(next=0, hands-off=2)\n"
    "lane-relaunch: launcher exited rc=1\n"
)


def handoff_text(*, next_heading: bool = True, hands_off_heading: bool = True) -> str:
    parts = ["# Handoff\n"]
    if next_heading:
        parts.append(f"## Next drive order\n{NEXT_THREE}\n")
    if hands_off_heading:
        parts.append(f"## Hands-off\n{HANDS_TWO}\n")
    return "\n".join(parts)


def lane_repo(tmp_path: Path, text: str | None) -> Path:
    repo = tmp_path / "repo"
    epic = repo / ".claude" / "atlas-epic"
    epic.mkdir(parents=True, exist_ok=True)
    if text is not None:
        (epic / "CODEX-DRIVER-HANDOFF.md").write_text(text, encoding="utf-8")
    return repo


@pytest.fixture
def launcher_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    """The launcher resolves the lane stream and its entries; pin both for the test."""
    monkeypatch.setattr(grok_lane, "launcher_stream_id", lambda _epic: "lane-test")
    monkeypatch.setattr(grok_lane, "_load_stream_entries", lambda *_args, **_kwargs: list(STREAM))


def shell_stream(selector: str) -> str:
    """The launcher's own stream for a selector, from the shell SSOT."""
    return subprocess.check_output(
        [
            "bash",
            "-c",
            'source "$1" && launcher_selector_stream "$2"',
            "lane-stream",
            str(REPO / "scripts/lib/handoff_identity.sh"),
            selector,
        ],
        text=True,
        timeout=2,
    ).strip()


def enter_handoff(h: Harness) -> None:
    """Watch -> handoff (done) without waiting for the context threshold."""
    h.tick(LANE)
    h.posted[SENDER] = cg.iso(h.moment)
    h.advance(5)
    h.tick(LANE)
    h.advance(5)


def anchor_sendbacks(h: Harness) -> list[str]:
    return [text for text in h.fake.typed(LANE) if text.startswith(cg.ANCHOR_SENDBACK_PREFIX)]


def alerts(h: Harness) -> list[str]:
    return [body for recipient, body in h.sent if recipient == "epics"]


def respawns(h: Harness) -> list[list[str]]:
    return [call for call in h.fake.calls if call[:2] == ["tmux", "respawn-pane"]]


def exit_typed(h: Harness) -> bool:
    return any(text in {"/exit", "/quit"} for text in h.fake.typed(LANE))


# ---- behaviour 1: the check before the exit command -------------------------------
def test_valid_handoff_still_exits(tmp_path: Path, launcher_stream: None) -> None:
    """Defect class: the guard blocks a lane whose handoff the launcher accepts."""
    lane_repo(tmp_path, handoff_text())
    h = Harness(tmp_path, **{LANE: codex_pane(40)})
    enter_handoff(h)
    h.tick(LANE)
    assert h.fake.typed(LANE) == ["/quit"]
    assert alerts(h) == []


@pytest.mark.parametrize(
    ("next_heading", "hands_off_heading", "anchors", "missing_name"),
    [
        (False, True, 7, "Next"),
        (True, False, 8, "Hands-off"),
        (False, False, 5, "Next and Hands-off"),
    ],
)
def test_short_handoff_is_sent_back_instead_of_exiting(
    tmp_path: Path,
    launcher_stream: None,
    next_heading: bool,
    hands_off_heading: bool,
    anchors: int,
    missing_name: str,
) -> None:
    """Defect class: lane exits with a handoff the launcher will refuse (anchors short)."""
    lane_repo(tmp_path, handoff_text(next_heading=next_heading, hands_off_heading=hands_off_heading))
    h = Harness(tmp_path, **{LANE: codex_pane(40)})
    enter_handoff(h)
    h.tick(LANE)
    assert not exit_typed(h)
    assert anchor_sendbacks(h), h.fake.typed(LANE)
    assert f"{anchors}/{grok_lane.N_ANCHORS}" in anchor_sendbacks(h)[0]
    assert missing_name in anchor_sendbacks(h)[0]
    assert h.state[LANE]["done_seen"] is False
    assert h.state[LANE]["anchor_sendbacks"] == 1
    assert len(alerts(h)) == 1 and f"{anchors}" in alerts(h)[0]


def test_the_same_failure_alerts_once_across_ticks(tmp_path: Path, launcher_stream: None) -> None:
    """Defect class: an alert storm from re-checking the same shortfall every tick."""
    lane_repo(tmp_path, handoff_text(next_heading=False))
    h = Harness(tmp_path, **{LANE: codex_pane(40)})
    enter_handoff(h)
    h.tick(LANE)
    assert len(alerts(h)) == 1
    for _ in range(2):
        h.advance(5)
        h.tick(LANE)
    assert len(alerts(h)) == 1
    assert not exit_typed(h)


def test_sendbacks_are_bounded_then_the_lane_is_left_running(tmp_path: Path, launcher_stream: None) -> None:
    """Defect class: unbounded send-backs, or a forced kill after a hopeless handoff."""
    lane_repo(tmp_path, handoff_text(next_heading=False))
    h = Harness(tmp_path, **{LANE: codex_pane(40)})
    enter_handoff(h)
    for _ in range(cg.ANCHOR_MAX_SENDBACKS + 2):
        h.tick(LANE)
        h.pane(LANE).text += "\n⏺ HANDOFF-DONE atlas .claude/atlas-epic/DRIVER-STATE.md"
        h.advance(5)
    assert len(anchor_sendbacks(h)) == cg.ANCHOR_MAX_SENDBACKS
    assert h.state[LANE]["anchor_blocked"] is True
    assert not exit_typed(h)
    blocked = [body for body in alerts(h) if "cannot produce a valid handoff" in body]
    assert len(blocked) == 1
    assert sum("would give" in body for body in alerts(h)) == 1


def test_handoff_file_missing_fails_open_with_one_alert(tmp_path: Path, launcher_stream: None) -> None:
    """Defect class: a missing handoff file wedges the lane instead of failing open."""
    lane_repo(tmp_path, None)
    h = Harness(tmp_path, **{LANE: codex_pane(40)})
    enter_handoff(h)
    h.tick(LANE)
    assert exit_typed(h)
    assert len(alerts(h)) == 1 and "no handoff file" in alerts(h)[0]


def test_helper_error_fails_open_and_alerts_once(tmp_path: Path, launcher_stream: None, monkeypatch) -> None:
    """Defect class: a bug in the new check wedges a lane that would otherwise rotate."""
    lane_repo(tmp_path, handoff_text())
    h = Harness(tmp_path, **{LANE: codex_pane(40)})

    def boom(**_kwargs):
        raise RuntimeError("selector unavailable")

    monkeypatch.setattr(grok_lane, "check_handoff_anchors", boom)
    enter_handoff(h)
    h.tick(LANE)
    assert exit_typed(h)
    assert len(alerts(h)) == 1 and "fail-open" in alerts(h)[0]
    h.advance(700)  # quit retry due: the gate runs again and must not alert again
    h.tick(LANE)
    assert len(alerts(h)) == 1


def test_human_controlled_lane_is_untouched_by_the_anchor_check(tmp_path: Path, launcher_stream: None) -> None:
    """Defect class: the guard types an anchor send-back into a human-controlled lane."""
    lane_repo(tmp_path, handoff_text(next_heading=False))
    h = Harness(tmp_path, **{LANE: codex_pane(40)})
    enter_handoff(h)
    h.advance(5)
    h.fake.clients = [(LANE, int(h.moment.timestamp()) - 30)]
    h.tick(LANE)
    assert h.fake.typed(LANE) == []
    assert alerts(h) == []


# ---- behaviour 2: post-relaunch launcher exit ------------------------------------
def relaunched(tmp_path: Path, launcher_stream: None) -> Harness:
    lane_repo(tmp_path, handoff_text())
    h = Harness(tmp_path, **{LANE: codex_pane(40)})
    enter_handoff(h)
    h.pane(LANE).agent = None
    h.advance(5)
    h.tick(LANE)  # respawn by the launcher plan
    assert len(respawns(h)) == 1
    assert h.state[LANE]["relaunch_watch"] == cg.iso(h.moment)
    return h


def test_launcher_exit_after_relaunch_alerts_once_with_the_stderr_tail(tmp_path: Path, launcher_stream: None) -> None:
    """Defect class: a relaunched launcher dies non-zero and nobody is told."""
    h = relaunched(tmp_path, launcher_stream)
    h.pane(LANE).text = LAUNCHER_EXIT_RC1
    h.advance(5)
    h.tick(LANE)
    assert len(alerts(h)) == 1
    alert = alerts(h)[0]
    assert "rc=1" in alert and "could only derive 8/10" in alert
    assert h.state[LANE]["relaunch_hold"] == 1
    for _ in range(3):
        h.advance(5)
        h.tick(LANE)
    assert len(alerts(h)) == 1
    assert len(respawns(h)) == 1


def test_launcher_that_stays_up_after_relaunch_does_not_alert(tmp_path: Path, launcher_stream: None) -> None:
    """Defect class: a healthy relaunch produces a false CTO alert."""
    h = relaunched(tmp_path, launcher_stream)
    h.pane(LANE).agent = "codex"
    h.advance(5)
    h.tick(LANE)
    assert alerts(h) == []
    assert "relaunch_watch" not in h.state[LANE]


def test_nonzero_launcher_exit_is_not_relaunched_in_a_loop(tmp_path: Path, launcher_stream: None) -> None:
    """Defect class: the guard respawns the same failing launcher every tick."""
    h = relaunched(tmp_path, launcher_stream)
    h.pane(LANE).text = LAUNCHER_EXIT_RC1
    h.advance(5)
    h.tick(LANE)
    h.pane(LANE).text = LAUNCHER_EXIT_RC1
    for _ in range(3):
        h.advance(5)
        h.tick(LANE)
    assert len(respawns(h)) == 1
    assert len(alerts(h)) == 1


# ---- behaviour 1 + AC-02: the guard and the launcher cannot drift ------------------
FIXTURES = {
    "valid": (True, True),
    "next-missing": (False, True),
    "hands-off-missing": (True, False),
    "both-missing": (False, False),
}


def launcher_selection(repo: Path):
    """Exactly what ``codex_lane mint`` selects: the Codex candidates + stream."""
    return grok_lane.select_handoff(
        repo=repo,
        epic="atlas",
        stream_id="lane-test",
        stream_entries=list(STREAM),
        candidates=handoff_select.load_codex_candidates(repo, "atlas"),
    )


@pytest.mark.parametrize("case", sorted(FIXTURES))
def test_shared_verdict_agrees_with_the_launcher_selector(tmp_path: Path, launcher_stream: None, case: str) -> None:
    """Defect class: the guard's check drifts from the launcher's ``select_handoff``."""
    next_heading, hands_off_heading = FIXTURES[case]
    repo = lane_repo(tmp_path, handoff_text(next_heading=next_heading, hands_off_heading=hands_off_heading))
    verdict = grok_lane.check_handoff_anchors(
        repo=repo,
        epic="atlas",
        candidates=handoff_select.load_codex_candidates(repo, "atlas"),
        stream_id="lane-test",
        stream_entries=STREAM,
    )
    selection = launcher_selection(repo)
    launcher_ok = bool(selection.reason) and selection.anchor_count >= grok_lane.N_ANCHORS
    if selection.reason:
        launcher_counts = grok_lane._handoff_section_counts(selection.text)
    else:
        _rel, _anchors, next_n, hands_n = max(selection.attempts, key=lambda attempt: attempt[1])
        launcher_counts = (next_n, hands_n)
    assert verdict.ok is launcher_ok
    assert verdict.anchors == selection.anchor_count
    assert (verdict.next_count, verdict.hands_off_count) == launcher_counts


@pytest.mark.parametrize("case", sorted(FIXTURES))
def test_guard_exit_decision_follows_the_launcher_selector(tmp_path: Path, launcher_stream: None, case: str) -> None:
    """Defect class: the guard exits where the launcher would refuse the handoff."""
    next_heading, hands_off_heading = FIXTURES[case]
    repo = lane_repo(tmp_path, handoff_text(next_heading=next_heading, hands_off_heading=hands_off_heading))
    launcher_ok = bool(launcher_selection(repo).reason)
    h = Harness(tmp_path, **{LANE: codex_pane(40)})
    enter_handoff(h)
    h.tick(LANE)
    assert exit_typed(h) is launcher_ok


def test_absent_handoff_is_reported_as_no_handoff_for_the_fail_open_path(tmp_path: Path, launcher_stream: None) -> None:
    """Defect class: an absent handoff is misreported as a shortfile the lane must rewrite."""
    repo = lane_repo(tmp_path, None)
    verdict = grok_lane.check_handoff_anchors(
        repo=repo,
        epic="atlas",
        candidates=handoff_select.load_codex_candidates(repo, "atlas"),
        stream_id="lane-test",
        stream_entries=STREAM,
    )
    key = "tried (no handoff)"
    assert verdict.no_handoff is True
    assert key in verdict.shortfall


def test_launcher_stream_ignores_a_conflicting_ambient_session_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    """Defect class: the guard's stream drifts from the launcher's shell selector via SESSION_STREAM_ID."""
    ambient = shell_stream("open-model-data")
    assert ambient != shell_stream(LANE)
    monkeypatch.setenv("SESSION_STREAM_ID", ambient)
    assert grok_lane.launcher_stream_id(LANE) == shell_stream(LANE)
    assert grok_lane.resolve_stream_id(LANE) == ambient


def test_ambient_session_stream_from_another_lane_cannot_exit_a_short_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Defect class: an ambient SESSION_STREAM_ID lets the guard exit a handoff the launcher refuses.

    The ambient stream carries enough entries to reach 10 anchors, while the
    lane's real stream (resolved by the shell SSOT, as the launcher does) does
    not. The guard must judge the real stream: matching ``select_handoff`` on
    that stream, it sends the lane back instead of typing ``/quit``.
    """
    repo = lane_repo(tmp_path, handoff_text(next_heading=False))
    ambient = shell_stream("open-model-data")
    assert ambient != shell_stream(LANE)
    monkeypatch.setenv("SESSION_STREAM_ID", ambient)

    def entries(stream_id: str, **_kwargs) -> list[dict[str, str]]:
        return list(CONFLICTING_STREAM) if stream_id == ambient else []

    monkeypatch.setattr(grok_lane, "_load_stream_entries", entries)
    lane_stream = shell_stream(LANE)
    launcher_ok = bool(
        grok_lane.select_handoff(
            repo=repo,
            epic=LANE,
            stream_id=lane_stream,
            stream_entries=entries(lane_stream),
            candidates=handoff_select.load_codex_candidates(repo, LANE),
        ).reason
    )
    assert not launcher_ok
    h = Harness(tmp_path, **{LANE: codex_pane(40)})
    enter_handoff(h)
    h.tick(LANE)
    assert not exit_typed(h), h.fake.typed(LANE)
    assert anchor_sendbacks(h), h.fake.typed(LANE)
    assert "next=0" in anchor_sendbacks(h)[0]

"""Sol Option-D post-compact hydrate capsule (bounded)."""

from __future__ import annotations

from pathlib import Path

from scripts.session_canary.diary import approx_tokens, build_hydrate_capsule


def _diary() -> str:
    return """# Harness diary

**Last diary stamp:** 2026-07-21T17:33Z

## 🚀 SESSION HANDOFF — 2026-07-21T16:17Z (cold-start this block)

### Binding rules
1. Layout A
2. Advisor gate

### Next drive (ordered)
1. No silent cutovers
2. Optional #5404

### Canary / proof
- ok

## 📌 Standing pins (do not drop without operator)

| Pin | Status |
| --- | --- |
| Layout A | binding |
| Plane | off |

## Hands-off
- Atlas product lane
- Primary product writes

## 📔 Diary — reverse chrono (newest first)

### 2026-07-21T17:33Z — merged
- #5588 MERGED

### 2026-07-21T17:19Z — opened
- PR open

### 2026-07-21T16:17Z — handoff
- cold-start

### 2026-07-21T09:00Z — older
- should usually drop when budget tight
"""


def test_hydrate_capsule_bounded_and_includes_next_drive() -> None:
    capsule, meta = build_hydrate_capsule(
        _diary(),
        epic="harness",
        stream_id="epic:4707",
        stream_tail="stream=epic:4707\n- [state] recent note",
        max_tokens=1400,
    )
    assert "HYDRATE CAPSULE" in capsule
    assert "Next drive" in capsule or "next drive" in capsule.lower()
    assert "Standing pins" in capsule or "Layout A" in capsule
    assert "RE-GROUND CHECKLIST" in capsule
    assert meta["has_reground_checklist"] is True
    assert meta["approx_tokens"] <= 1600
    assert meta["has_identity"] is True
    assert meta["has_next_drive"] is True
    assert approx_tokens(capsule) == meta["approx_tokens"]


def test_hydrate_includes_active_working_set_when_present() -> None:
    diary = _diary() + "\n## Active Working Set\n- pilot clone at /tmp/x\n- PR #274 merged\n"
    capsule, meta = build_hydrate_capsule(
        diary,
        epic="harness",
        stream_id="epic:4707",
        max_tokens=1400,
    )
    assert "Active Working Set" in capsule
    assert "pilot clone" in capsule
    assert meta["has_working_set"] is True
    assert "RE-GROUND CHECKLIST" in capsule


def test_hydrate_drops_low_priority_whole_sections_under_tiny_budget() -> None:
    capsule, meta = build_hydrate_capsule(
        _diary(),
        epic="harness",
        stream_id="epic:4707",
        stream_tail="- [state] " + ("x" * 2000),
        max_tokens=400,
    )
    # identity must remain
    assert "SESSION HANDOFF" in capsule or "HYDRATE" in capsule
    # stream or stamps may drop
    assert isinstance(meta["dropped_sections"], list)


def test_hydrate_cli_stdout(tmp_path: Path, monkeypatch) -> None:
    from scripts.session_canary import grok_lane

    epic_dir = tmp_path / ".claude" / "harness-epic"
    epic_dir.mkdir(parents=True)
    handoff = epic_dir / "INTERIM-DRIVER-HANDOFF.md"
    handoff.write_text(_diary(), encoding="utf-8")

    class NS:
        pass

    ns = NS()
    ns.repo = str(tmp_path)
    ns.epic = "harness"
    ns.stream = "epic:4707"
    ns.handoff = str(handoff)
    ns.out_dir = str(tmp_path / "canary")
    ns.max_tokens = 1400
    ns.max_stamps = 3
    ns.stream_limit = 5
    ns.no_stream = True
    ns.write = True

    rc = grok_lane.cmd_hydrate(ns)
    assert rc == 0
    written = Path(ns.out_dir) / "hydrate.md"
    assert written.is_file()
    assert "HYDRATE CAPSULE" in written.read_text(encoding="utf-8")


def test_score_auto_hydrates_on_pass(tmp_path: Path, monkeypatch, capsys) -> None:
    """score PASS prints AUTO-HYDRATE capsule without a separate hydrate call."""
    from scripts.session_canary import grok_lane

    epic_dir = tmp_path / ".claude" / "harness-epic"
    epic_dir.mkdir(parents=True)
    handoff = epic_dir / "INTERIM-DRIVER-HANDOFF.md"
    handoff.write_text(_diary(), encoding="utf-8")
    canary = tmp_path / ".claude" / "harness-epic" / "canary"
    canary.mkdir(parents=True)
    # Minimal probe + perfect answers so score returns PASS
    probe = {
        "anchors": [
            {"id": "a1", "q": "Q1", "a": "answer-one"},
            {"id": "a2", "q": "Q2", "a": "answer-two"},
        ]
    }
    import json as _json
    (canary / "probe.json").write_text(_json.dumps(probe), encoding="utf-8")
    answers = canary / "answers.json"
    answers.write_text(_json.dumps({"a1": "answer-one", "a2": "answer-two"}), encoding="utf-8")

    # Point canary dir via --out-dir and monkeypatch epic stream defaults
    class NS:
        pass

    ns = NS()
    ns.repo = str(tmp_path)
    ns.epic = "harness"
    ns.out_dir = str(canary)
    ns.answers = str(answers)
    ns.pass_ratio = 0.5  # 1/2 enough if threshold loose; use 0.5 with 2 anchors
    ns.threshold = 0.5
    ns.context_tokens = 1000
    ns.model = "test"
    ns.handoff = str(handoff)
    ns.next_drive = ""
    ns.pins = ""
    ns.open_prs = ""
    ns.hands_off = ""
    ns.pending_user = ""
    ns.worktrees = ""
    ns.no_hydrate = False
    ns.hydrate_write = False
    ns.hydrate_max_tokens = 1400

    # context_canary score subprocess — stub to PASS
    def fake_run(cmd, **kwargs):
        class R:
            returncode = 0
            stdout = "SCORE 2/2 = 1.00  ->  PASS\n"
            stderr = ""
        return R()

    monkeypatch.setattr(grok_lane.subprocess, "run", fake_run)
    rc = grok_lane.cmd_score(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "AUTO-HYDRATE" in out
    assert "HYDRATE CAPSULE" in out
    assert "POST-COMPACT RE-GROUND" in out
    assert "RE-GROUND CHECKLIST" in out


def test_score_no_hydrate_flag_skips(tmp_path: Path, monkeypatch, capsys) -> None:
    import json as _json

    from scripts.session_canary import grok_lane

    epic_dir = tmp_path / ".claude" / "harness-epic"
    epic_dir.mkdir(parents=True)
    handoff = epic_dir / "INTERIM-DRIVER-HANDOFF.md"
    handoff.write_text(_diary(), encoding="utf-8")
    canary = epic_dir / "canary"
    canary.mkdir(parents=True)
    probe = {"anchors": [{"id": "a1", "q": "Q1", "a": "answer-one"}]}
    (canary / "probe.json").write_text(_json.dumps(probe), encoding="utf-8")
    answers = canary / "answers.json"
    answers.write_text(_json.dumps({"a1": "answer-one"}), encoding="utf-8")

    class NS:
        pass

    ns = NS()
    ns.repo = str(tmp_path)
    ns.epic = "harness"
    ns.out_dir = str(canary)
    ns.answers = str(answers)
    ns.pass_ratio = 0.5
    ns.threshold = 0.5
    ns.context_tokens = 1000
    ns.model = "test"
    ns.handoff = str(handoff)
    ns.next_drive = ns.pins = ns.open_prs = ns.hands_off = ns.pending_user = ns.worktrees = ""
    ns.no_hydrate = True
    ns.hydrate_write = False
    ns.hydrate_max_tokens = 1400

    def fake_run(cmd, **kwargs):
        class R:
            returncode = 0
            stdout = "SCORE 1/1 = 1.00  ->  PASS\n"
            stderr = ""
        return R()

    monkeypatch.setattr(grok_lane.subprocess, "run", fake_run)
    rc = grok_lane.cmd_score(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "AUTO-HYDRATE" not in out

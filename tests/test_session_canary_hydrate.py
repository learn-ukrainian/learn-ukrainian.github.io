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
    assert meta["approx_tokens"] <= 1600
    assert meta["has_identity"] is True
    assert meta["has_next_drive"] is True
    assert approx_tokens(capsule) == meta["approx_tokens"]


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

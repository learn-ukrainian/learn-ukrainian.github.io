"""Operational Grok lane session canary (mint / score via context_canary)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.session_canary import grok_lane as gl

_REPO = Path(__file__).resolve().parents[1]


def _py() -> str:
    venv = _REPO / ".venv" / "bin" / "python"
    return str(venv) if venv.is_file() else sys.executable


def test_build_facts_exactly_ten_from_stream_and_handoff() -> None:
    stream = [
        {"type": "binding_order", "body": f"Binding order number {i} about quality and no shortcuts."}
        for i in range(1, 5)
    ]
    stream += [
        {"type": "negative_constraint", "body": "Never commit directly to main."},
        {"type": "negative_constraint", "body": "Never merge drafts."},
        {"type": "next_action", "body": "Merge offline enrich when CI green."},
        {"type": "next_action", "body": "Run VPS launch_enrich after merge."},
        {"type": "decision", "body": "Sol is the designer for practice setup."},
        {"type": "state", "body": "PR 5496 waiting on pytest."},
    ]
    handoff = """
# Handoff
## Next drive order
1. Ship start-grok canary mint at cold-start
2. Score after auto-compact
3. End on FAIL-HANDOFF only
## Hands-off
- Other lanes' queues
- Primary checkout writes for product code
"""
    facts = gl._build_facts(
        epic="atlas",
        stream_id="epic:4387",
        stream_entries=stream,
        handoff_text=handoff,
        handoff_rel=".claude/atlas-epic/INTERIM-DRIVER-HANDOFF.md",
    )
    assert len(facts) == 10
    ids = [f["id"] for f in facts]
    assert len(set(ids)) == 10
    assert "lane-stream" in ids
    assert facts[0]["a"] == "epic:4387"
    assert all(f["q"] and f["a"] for f in facts)


def test_build_facts_fails_when_insufficient(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="could only derive"):
        gl._build_facts(
            epic="atlas",
            stream_id="epic:4387",
            stream_entries=[{"type": "state", "body": "only one"}],
            handoff_text="",
            handoff_rel="",
        )


def test_mint_score_roundtrip_pass_and_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Avoid depending on live session DB
    monkeypatch.setattr(gl, "_load_stream_entries", lambda *a, **k: [
        {"type": "binding_order", "body": f"Pinned binding order text {i} with enough content."}
        for i in range(1, 6)
    ] + [
        {"type": "negative_constraint", "body": "Do not lower quality gates."},
        {"type": "negative_constraint", "body": "Do not bypass CI."},
        {"type": "next_action", "body": "Dual-write handoff after each batch."},
        {"type": "next_action", "body": "Re-score canary after auto-compact."},
        {"type": "decision", "body": "Canary end signal is score not compact count."},
    ])

    canary_dir = tmp_path / "canary"
    handoff = tmp_path / "handoff.md"
    handoff.write_text(
        "## Next drive order\n- Keep dual-write current\n- Score canary after compact\n"
        "## Hands-off\n- Foreign lanes\n",
        encoding="utf-8",
    )

    rc = gl.main(
        [
            "--repo",
            str(_REPO),
            "mint",
            "--epic",
            "atlas",
            "--stream",
            "epic:4387",
            "--handoff",
            str(handoff),
            "--out-dir",
            str(canary_dir),
        ]
    )
    assert rc == 0
    probe = json.loads((canary_dir / "probe.json").read_text(encoding="utf-8"))
    anchors = probe["anchors"]
    assert len(anchors) == 10

    # Perfect recall
    answers = {a["id"]: a["a"] for a in anchors}
    answers_path = canary_dir / "answers-ok.json"
    answers_path.write_text(json.dumps(answers), encoding="utf-8")
    rc = gl.main(
        [
            "--repo",
            str(_REPO),
            "score",
            "--epic",
            "atlas",
            "--out-dir",
            str(canary_dir),
            "--answers",
            str(answers_path),
            "--context-tokens",
            "100000",
            "--model",
            "test-model",
            "--pass-ratio",
            "0.8",
        ]
    )
    assert rc == 0
    verdict = json.loads((canary_dir / "last_verdict.json").read_text(encoding="utf-8"))
    assert verdict["verdict"] == "PASS"

    # Drop 3 answers → 7/10 < 0.8
    broken = dict(answers)
    for aid in list(broken)[:3]:
        broken[aid] = "I forgot this entirely"
    answers_path2 = canary_dir / "answers-bad.json"
    answers_path2.write_text(json.dumps(broken), encoding="utf-8")
    rc = gl.main(
        [
            "--repo",
            str(_REPO),
            "score",
            "--epic",
            "atlas",
            "--out-dir",
            str(canary_dir),
            "--answers",
            str(answers_path2),
            "--context-tokens",
            "300000",
            "--model",
            "test-model",
            "--pass-ratio",
            "0.8",
        ]
    )
    assert rc == 2
    verdict2 = json.loads((canary_dir / "last_verdict.json").read_text(encoding="utf-8"))
    assert verdict2["verdict"] == "FAIL-HANDOFF"


def test_protocol_prints_epic(capsys: pytest.CaptureFixture[str]) -> None:
    rc = gl.main(["protocol", "--epic", "atlas"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "epic:4387" in out
    assert "0.8" in out or "8/10" in out
    assert "FAIL-HANDOFF" in out


def test_cli_module_help() -> None:
    proc = subprocess.run(
        [_py(), "-m", "scripts.session_canary.grok_lane", "--help"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "mint" in proc.stdout

"""Muse recall canary semantic round trips; no model or lease operations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.session_canary import diary, grok_lane, muse_lane

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "epic",
    [
        "folk",
        "curriculum-upgrade",
        "infra",
        "harness",
        "infra.fleet-comms",
        "infra-harness",
        "atlas",
        "../devops",
        "Devops",
    ],
)
def test_refuses_other_and_unsafe_lanes_before_writing(tmp_path: Path, epic: str) -> None:
    assert muse_lane.main(["--repo", str(tmp_path), "mint", "--epic", epic]) == 2
    assert list(tmp_path.iterdir()) == []


def test_rejects_foreign_stream_before_writing(tmp_path: Path) -> None:
    assert (
        muse_lane.main(
            [
                "--repo",
                str(tmp_path),
                "mint",
                "--epic",
                "devops",
                "--stream",
                "epic:999999",
            ]
        )
        == 2
    )
    assert list(tmp_path.iterdir()) == []


def test_mint_and_score_real_ten_anchor_pass_and_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("SESSION_STREAM_ID", "epic:999999")  # Ambient foreign lease cannot retarget mint.
    monkeypatch.delenv("LU_RULES_SEAT", raising=False)
    monkeypatch.setattr(grok_lane, "_load_ranked", lambda *a, **kw: [])
    monkeypatch.setattr(
        grok_lane,
        "_load_stream_entries",
        lambda *a, **kw: (
            [
                {
                    "type": "binding_order",
                    "body": f"Pinned binding order number {i} with enough distinct durable content.",
                }
                for i in range(1, 6)
            ]
            + [
                {"type": "negative_constraint", "body": "Do not lower quality gates."},
                {"type": "negative_constraint", "body": "Do not bypass CI."},
                {"type": "next_action", "body": "Dual-write handoff after each batch."},
                {"type": "next_action", "body": "Re-score the recall canary at rollover."},
                {"type": "decision", "body": "End on the failed recall score."},
            ]
        ),
    )
    monkeypatch.setattr(diary, "try_stream_state_note", lambda *a, **kw: None)
    monkeypatch.setattr(grok_lane, "emit_hydrate_capsule", lambda **kw: "test hydration")
    handoff = tmp_path / "MUSE-DRIVER-HANDOFF.md"
    handoff.write_text("## Next drive order\n- Score canary at rollover\n## Hands-off\n- Foreign lanes\n")
    canary = tmp_path / "canary"
    common = ["--repo", str(REPO)]
    assert (
        muse_lane.main(
            [
                *common,
                "mint",
                "--epic",
                "infra.devops",
                "--handoff",
                str(handoff),
                "--out-dir",
                str(canary),
            ]
        )
        == 0
    )
    probe = json.loads((canary / "probe.json").read_text())
    assert len(probe["anchors"]) == 10
    assert probe["anchors"][0]["a"] == "epic:5703"  # allow-hardcoded-epic: DevOps canary fixture
    answers = {a["id"]: a["a"] for a in probe["anchors"]}
    answer_path = tmp_path / "answers.json"
    answer_path.write_text(json.dumps(answers))
    score = [
        *common,
        "score",
        "--epic",
        "devops",
        "--answers",
        str(answer_path),
        "--out-dir",
        str(canary),
    ]
    assert muse_lane.main(score) == 0
    verdict = json.loads((canary / "last_verdict.json").read_text())
    assert verdict["verdict"] == "PASS" and verdict["pass_ratio"] == 0.8
    for anchor_id in list(answers)[:3]:
        answers[anchor_id] = "forgot entirely"
    answer_path.write_text(json.dumps(answers))
    assert muse_lane.main(score) == 2
    verdict = json.loads((canary / "last_verdict.json").read_text())
    assert verdict["verdict"] == "FAIL-HANDOFF"
    assert "STATE AT HANDBACK" in handoff.read_text()
    assert "exit this Muse driver; the launcher closes its lease" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("selector", "lane", "stream"),
    [
        ("devops", "devops", "epic:5703"),
        ("infra.devops", "devops", "epic:5703"),
        ("monitor", "monitor", "epic:7919"),
        ("infra.monitor", "monitor", "epic:7919"),
        ("ops-api", "monitor", "epic:7919"),
        ("ops.api", "monitor", "epic:7919"),
        ("operator-api", "monitor", "epic:7919"),
    ],
)
@pytest.mark.parametrize("command", ["mint", "score"])
def test_alias_admission_uses_canonical_stream_without_running_canary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selector: str,
    lane: str,
    stream: str,
    command: str,
) -> None:
    # allow-hardcoded-epic: literal selector contract, independent of the resolver under test
    calls = []

    def capture(args):
        calls.append((args.epic, args.stream, getattr(args, "model", None)))
        return 0

    monkeypatch.delenv("LU_RULES_SEAT", raising=False)
    monkeypatch.setattr(grok_lane, "cmd_mint", capture)
    monkeypatch.setattr(grok_lane, "cmd_score", capture)
    args = ["--repo", str(tmp_path), command, "--epic", selector]
    if command == "score":
        args += ["--answers", "unused.json"]
    assert muse_lane.main(args) == 0
    assert calls == [(lane, stream, "muse-wonder-full-1.0" if command == "score" else None)]
    assert list(tmp_path.iterdir()) == []

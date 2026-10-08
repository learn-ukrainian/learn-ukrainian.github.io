from __future__ import annotations

import base64
import hashlib
import json
import shutil
import subprocess
import time
from copy import deepcopy
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.orchestration import task_closeout, task_identity, task_lifecycle

NOW = "2026-07-16T10:00:00Z"
HEAD = "a" * 40
MERGE = "b" * 40
REVIEW_URL = "https://github.com/org/repo/pull/77#issuecomment-1"


def _body(*, checked: bool = False, include_deploy: bool = False, include_certify: bool = False) -> str:
    mark = "x" if checked else " "
    lines = [
        f"- [{mark}] **AC-IMPL** — Implementation is verified.",
        f"- [{mark}] **AC-REVIEW** — Independent review passes.",
        f"- [{mark}] **AC-MERGE** — The pull request merges.",
    ]
    if include_deploy:
        lines.append(f"- [{mark}] **AC-DEPLOY** — The merged change deploys.")
    if include_certify:
        lines.append(f"- [{mark}] **AC-CERT** — The deployed change is certified.")
    lines.extend(
        [
            f"- [{mark}] **AC-CLOSE** — The issue is actually closed.",
            f"- [{mark}] **AC-CLEAN** — The task branch and worktree are cleaned.",
        ]
    )
    return "\n".join(lines) + "\n"


def _policy(
    *,
    include_deploy: bool = False,
    include_certify: bool = False,
    behavior_proof: bool = False,
) -> dict:
    policy = {
        "AC-IMPL": {"due_state": "IMPLEMENTATION_READY", "required_evidence": ["test"]},
        "AC-REVIEW": {"due_state": "REVIEW_PASSED", "required_evidence": ["review"]},
        "AC-MERGE": {"due_state": "MERGED", "required_evidence": ["github"]},
        "AC-CLOSE": {"due_state": "ISSUE_CLOSED", "required_evidence": ["github"]},
        "AC-CLEAN": {"due_state": "CLEANED_UP", "required_evidence": ["cleanup"]},
    }
    if include_deploy:
        policy["AC-DEPLOY"] = {"due_state": "DEPLOYED", "required_evidence": ["deployment"]}
    if include_certify:
        policy["AC-CERT"] = {"due_state": "CERTIFIED", "required_evidence": ["certification"]}
    if behavior_proof:
        policy["AC-IMPL"]["required_evidence"].append("behavior_proof")
        policy["AC-IMPL"]["behavior_proof_required"] = True
    return policy


def _identity(goal: str = "merge") -> dict:
    return task_identity.build_identity(
        repository="org/repo",
        stream_epic=10,
        stream_epic_url=None,
        github_issue_number=42,
        github_issue_url=None,
        semantic_title="Enforce task closeout",
        task_family="infrastructure",
        role="implementer",
        predecessor_task_id="thread-old",
        replacement_task_id="thread-new",
        lineage_id="lineage-closeout",
        generation=2,
        terminal_goal=goal,
        lifecycle_state="confirmed",
    )


def _ledger(goal: str = "merge", *, behavior_proof: bool = False) -> dict:
    deploy = goal in {"deploy", "certify"}
    certify = goal == "certify"
    snapshot = task_lifecycle.build_ac_snapshot(
        _body(include_deploy=deploy, include_certify=certify),
        _policy(
            include_deploy=deploy,
            include_certify=certify,
            behavior_proof=behavior_proof,
        ),
        finalized_at=NOW,
    )
    return task_lifecycle.build_lifecycle(
        _identity(goal),
        author_family="codex",
        ac_snapshot=snapshot,
        required_checks=["CI Gate"],
        now=NOW,
        pr_number=77,
    )


def _add(
    ledger: dict,
    ac_id: str,
    kind: str,
    *,
    url: str | None = None,
    details: dict | None = None,
) -> dict:
    updated, _ = task_lifecycle.add_evidence(
        ledger,
        ac_id=ac_id,
        evidence_type=kind,
        summary=f"verified {ac_id}",
        url=url,
        commit=None if kind in {"cleanup", "follow_up"} else HEAD,
        details=details,
        recorded_at=NOW,
    )
    return updated


def _ready_evidence(ledger: dict) -> dict:
    ledger = _add(ledger, "AC-IMPL", "test")
    return _add(
        ledger,
        "AC-REVIEW",
        "review",
        url=REVIEW_URL,
        details={"author_family": "codex", "reviewer_family": "gemini", "verdict": "pass"},
    )


def _replacement(ledger: dict, target: dict, **overrides: object) -> tuple[dict, dict]:
    args = {
        "ac_id": target["ac_id"],
        "evidence_type": target["type"],
        "summary": "corrected evidence",
        "url": target["url"],
        "commit": target["subject"]["commit"],
        "details": {**target["details"], "supersedes_evidence_id": target["id"]},
        "recorded_at": max(
            datetime.fromisoformat(target["recorded_at"]) + timedelta(seconds=1),
            datetime.fromisoformat(ledger["updated_at"]),
        ).astimezone(UTC).isoformat().replace("+00:00", "Z"),
        **overrides,
    }
    return task_lifecycle.add_evidence(ledger, **args)


def test_review_url_correction_retires_error_without_changing_history(tmp_path: Path) -> None:
    ledger = _add(_add(_ledger(), "AC-IMPL", "test"), "AC-REVIEW", "review",
                  url="https://github.com/org/repo/pull/77",
                  details={"author_family": "codex", "reviewer_family": "claude", "verdict": "pass"})
    observation = _observation(_body())
    ledger, receipt, _ = task_lifecycle.reconcile(ledger, observation, now=NOW)
    assert receipt["state"] == "BLOCKED_WITH_RECEIPT"
    original_bytes = task_lifecycle.canonical_json(ledger)
    old = ledger["evidence"][-1]
    corrected, new = _replacement(ledger, old, url=REVIEW_URL)
    observation["github"]["pr"]["auto_merge_enabled_at"] = "2026-07-16T12:00:00Z"
    result = task_lifecycle.evaluate(corrected, observation)
    assert result["state"] == "CI_PASSED"
    assert result["hard_blockers"] == []
    assert result["superseded_evidence_ids"] == [old["id"]]
    assert result["retired_evidence_errors"] == {
        old["id"]: "AC-REVIEW: review receipt URL is absent from authoritative PR comments",
    }
    replayed, replay_record = _replacement(corrected, old, url=REVIEW_URL)
    assert replayed == corrected
    assert replay_record == new
    path = tmp_path / "lifecycle.json"
    task_lifecycle.write_lifecycle(path, corrected)
    loaded = task_lifecycle.load_lifecycle(path)
    assert loaded == corrected
    assert task_lifecycle.canonical_json(ledger) == original_bytes
    assert loaded["evidence"][:-1] == ledger["evidence"]
    updated, _, _ = task_lifecycle.reconcile(loaded, observation, now=NOW)
    assert updated["observation_receipts"][0] == receipt
    for row in updated["evidence"]:
        assert row["id"] == task_lifecycle.digest(task_lifecycle._evidence_payload(row))
    assert "superseded_evidence_ids" not in task_lifecycle.canonical_json(updated)
    assert "retired_evidence_errors" not in task_lifecycle.canonical_json(updated)


@pytest.mark.parametrize("recorded_at", [
    NOW,
    "2026-07-16T09:59:59Z",
    "2026-07-16T11:00:00+01:00",  # Same instant, different spelling.
    "2026-07-16T11:59:59+02:00",  # Lexically later, chronologically earlier.
])
def test_correction_requires_later_target_timestamp_at_append_and_load(tmp_path: Path, recorded_at: str) -> None:
    ledger = _add(_ledger(), "AC-IMPL", "test")
    old = ledger["evidence"][-1]
    # An ordinary ledger update may predate its evidence; the target check must
    # independently reject these corrections at both append and load.
    ledger["updated_at"] = "2026-07-16T09:00:00Z"
    original = deepcopy(ledger)
    with pytest.raises(task_lifecycle.LifecycleError, match="strictly later than its target"):
        _replacement(ledger, old, recorded_at=recorded_at)
    corrected, _ = _replacement(ledger, old)
    row = corrected["evidence"][-1]
    row["recorded_at"] = recorded_at
    row["id"] = task_lifecycle.digest(task_lifecycle._evidence_payload(row))
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(corrected), encoding="utf-8")
    with pytest.raises(task_lifecycle.LifecycleError, match="strictly later than its target"):
        task_lifecycle.load_lifecycle(path)
    assert ledger == original


@pytest.mark.parametrize("recorded_at", ["2026-07-16T10:30:00Z", "2026-07-16T12:30:00+02:00"])
def test_new_correction_cannot_predate_previous_ledger_update(recorded_at: str) -> None:
    ledger = _add(_ledger(), "AC-IMPL", "test")
    old = ledger["evidence"][-1]
    ledger = task_lifecycle.set_remaining_scope(
        ledger, status="none", summary="", follow_up_issue=None,
        follow_up_stream_epic=None, evidence_ids=[], now="2026-07-16T11:00:00Z",
    )
    original = deepcopy(ledger)
    with pytest.raises(task_lifecycle.LifecycleError, match="must not predate ledger updated_at"):
        _replacement(ledger, old, recorded_at=recorded_at)
    assert ledger == original


@pytest.mark.parametrize("target_at,updated_at,recorded_at", [
    (NOW, NOW, "2026-07-16T10:00:00.1Z"),  # Lexically earlier, chronologically later.
    ("2026-07-16T11:00:00+02:00", NOW, NOW),  # Equal to prior update is allowed.
    (NOW, "2026-07-16T10:30:00Z", "2026-07-16T10:00:01-01:00"),
    (NOW, NOW, "2026-07-16t10:00:01z"),
])
def test_honest_correction_and_replay_after_later_update(
    tmp_path: Path, target_at: str, updated_at: str, recorded_at: str,
) -> None:
    ledger = _add(_ledger(), "AC-IMPL", "test")
    old = ledger["evidence"][-1]
    old["recorded_at"] = target_at
    old["id"] = task_lifecycle.digest(task_lifecycle._evidence_payload(old))
    ledger["updated_at"] = updated_at
    original_bytes = task_lifecycle.canonical_json(old)
    corrected, new = _replacement(ledger, old, recorded_at=recorded_at)
    assert corrected["updated_at"] == recorded_at
    assert task_lifecycle.canonical_json(corrected["evidence"][0]) == original_bytes
    updated = task_lifecycle.set_remaining_scope(
        corrected, status="none", summary="", follow_up_issue=None,
        follow_up_stream_epic=None, evidence_ids=[], now="2026-07-16T12:00:00Z",
    )
    path = tmp_path / "lifecycle.json"
    task_lifecycle.write_lifecycle(path, updated)
    loaded = task_lifecycle.load_lifecycle(path)
    replayed, replay_row = _replacement(loaded, old, recorded_at=recorded_at)
    assert replayed == loaded == updated
    assert replay_row == new


@pytest.mark.parametrize("recorded_at,error", [
    ("invalid", "valid timestamp"),
    ("2026-07-16T11:00:00", "timezone-aware timestamp"),
])
def test_correction_rejects_unparseable_timestamp(recorded_at: str, error: str) -> None:
    ledger = _add(_ledger(), "AC-IMPL", "test")
    with pytest.raises(task_lifecycle.LifecycleError, match=error):
        _replacement(ledger, ledger["evidence"][-1], recorded_at=recorded_at)


def test_ordinary_evidence_retains_existing_timestamp_semantics() -> None:
    ledger = _add(_ledger(), "AC-IMPL", "test")
    ledger["updated_at"] = "2026-07-16T12:00:00Z"
    updated, row = task_lifecycle.add_evidence(
        ledger, ac_id="AC-IMPL", evidence_type="test", summary="ordinary earlier evidence",
        url=None, commit=HEAD, details={}, recorded_at="2026-07-16T09:00:00Z",
    )
    assert updated["updated_at"] == row["recorded_at"] == "2026-07-16T09:00:00Z"
    assert task_lifecycle.validate_lifecycle(updated) == updated


@pytest.mark.parametrize("link", [None, True, 7, [], {}, "", "sha256:" + "A" * 64, "a" * 64, "sha256:abc"])
def test_malformed_supersession_rejected_at_append_and_load(tmp_path: Path, link: object) -> None:
    ledger = _add(_ledger(), "AC-IMPL", "test")
    old = ledger["evidence"][-1]
    with pytest.raises(task_lifecycle.LifecycleError, match="supersedes_evidence_id must be sha256"):
        _replacement(ledger, old, details={"supersedes_evidence_id": link})
    tampered = deepcopy(ledger)
    tampered["evidence"][0]["details"]["supersedes_evidence_id"] = link
    tampered["evidence"][0]["id"] = task_lifecycle.digest(task_lifecycle._evidence_payload(tampered["evidence"][0]))
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(task_lifecycle.LifecycleError, match="supersedes_evidence_id must be sha256"):
        task_lifecycle.load_lifecycle(path)


def test_unknown_forward_self_and_cyclic_supersession_rejected(tmp_path: Path) -> None:
    ledger = _add(_ledger(), "AC-IMPL", "test")
    old = ledger["evidence"][-1]
    with pytest.raises(task_lifecycle.LifecycleError, match="existing earlier"):
        _replacement(ledger, old, details={"supersedes_evidence_id": "sha256:" + "f" * 64})
    corrected, new = _replacement(ledger, old)
    forward = deepcopy(corrected)
    forward["evidence"].reverse()  # Both digests are valid, but the target is later.
    with pytest.raises(task_lifecycle.LifecycleError, match="existing earlier"):
        task_lifecycle.validate_lifecycle(forward)
    with pytest.raises(task_lifecycle.LifecycleError, match="existing earlier"):
        _replacement(ledger, old, details={"supersedes_evidence_id": new["id"]})
    # Self/cyclic tampering cannot preserve content-addressed row IDs either.
    for target in (old["id"], new["id"]):
        tampered = deepcopy(corrected)
        tampered["evidence"][0]["details"]["supersedes_evidence_id"] = target
        path = tmp_path / "tampered.json"
        path.write_text(json.dumps(tampered), encoding="utf-8")
        with pytest.raises(task_lifecycle.LifecycleError, match="digest is invalid"):
            task_lifecycle.load_lifecycle(path)


@pytest.mark.parametrize("overrides", [{"ac_id": "AC-REVIEW"}, {"evidence_type": "command"}])
def test_cross_criterion_or_type_supersession_rejected(overrides: dict) -> None:
    ledger = _add(_ledger(), "AC-IMPL", "test")
    with pytest.raises(task_lifecycle.LifecycleError, match="same criterion, type"):
        _replacement(ledger, ledger["evidence"][-1], **overrides)
    corrected, _ = _replacement(ledger, ledger["evidence"][-1])
    row = corrected["evidence"][-1]
    row["ac_id" if "ac_id" in overrides else "type"] = next(iter(overrides.values()))
    row["id"] = task_lifecycle.digest(task_lifecycle._evidence_payload(row))
    with pytest.raises(task_lifecycle.LifecycleError, match="same criterion, type"):
        task_lifecycle.validate_lifecycle(corrected)


@pytest.mark.parametrize("field,value", [("repository", "other/repo"), ("issue", 43), ("pr", 78)])
def test_cross_subject_supersession_rejected_on_load(tmp_path: Path, field: str, value: object) -> None:
    ledger = _add(_ledger(), "AC-IMPL", "test")
    ledger, _ = _replacement(ledger, ledger["evidence"][-1])
    row = ledger["evidence"][-1]
    row["subject"][field] = value
    row["id"] = task_lifecycle.digest(task_lifecycle._evidence_payload(row))
    path = tmp_path / "cross-context.json"
    path.write_text(json.dumps(ledger), encoding="utf-8")
    with pytest.raises(task_lifecycle.LifecycleError, match="does not match"):
        task_lifecycle.load_lifecycle(path)


def test_duplicate_superseder_rejected_at_append_and_load(tmp_path: Path) -> None:
    ledger = _add(_ledger(), "AC-IMPL", "test")
    old = ledger["evidence"][-1]
    corrected, row = _replacement(ledger, old)
    with pytest.raises(task_lifecycle.LifecycleError, match="already has a superseder"):
        _replacement(corrected, old, summary="second competing correction")
    duplicate = deepcopy(row)
    duplicate["summary"] = "second competing correction"
    duplicate["id"] = task_lifecycle.digest(task_lifecycle._evidence_payload(duplicate))
    corrected["evidence"].append(duplicate)
    path = tmp_path / "duplicate.json"
    path.write_text(json.dumps(corrected), encoding="utf-8")
    with pytest.raises(task_lifecycle.LifecycleError, match="already has a superseder"):
        task_lifecycle.load_lifecycle(path)


@pytest.mark.parametrize("old_valid", [False, True])
def test_invalid_chain_tip_blocks_and_never_inherits_proof(old_valid: bool) -> None:
    ledger = _ready_evidence(_ledger())
    old = ledger["evidence"][-1]
    if not old_valid:
        old["url"] = "https://github.com/org/repo/pull/77"
        old["id"] = task_lifecycle.digest(task_lifecycle._evidence_payload(old))
    ledger, middle = _replacement(ledger, old, url=REVIEW_URL)
    ledger, tip = _replacement(ledger, middle, commit="c" * 40)
    result = task_lifecycle.evaluate(ledger, _observation(_body()))
    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "AC-REVIEW" not in result["valid_evidence"]
    assert result["retired_evidence_errors"] == {}
    assert result["superseded_evidence_ids"] == [old["id"], middle["id"]]
    assert "AC-REVIEW: review evidence is not bound to current PR head" in result["hard_blockers"]
    url_error = "AC-REVIEW: review receipt URL is absent from authoritative PR comments"
    assert (url_error in result["hard_blockers"]) is (not old_valid)
    ledger, _ = _replacement(ledger, tip, commit=HEAD)
    observation = _observation(_body())
    observation["github"]["pr"]["auto_merge_enabled_at"] = "2026-07-16T12:00:00Z"
    repaired = task_lifecycle.evaluate(ledger, observation)
    assert repaired["hard_blockers"] == []
    assert set(repaired["retired_evidence_errors"]) == ({tip["id"]} if old_valid else {tip["id"], old["id"]})


def test_moved_head_requires_independent_test_ci_and_review_replacements() -> None:
    ledger = _ready_evidence(_ledger())
    ledger = _add(ledger, "AC-IMPL", "ci")
    observation = _observation(_body())
    observation["github"]["pr"]["head_sha"] = "c" * 40
    assert len(task_lifecycle.evaluate(ledger, observation)["hard_blockers"]) >= 3
    old_rows = deepcopy(ledger["evidence"])
    for old in old_rows:
        ledger, _ = _replacement(ledger, old, commit="c" * 40)
    observation["github"]["pr"]["auto_merge_enabled_at"] = "2026-07-16T12:00:00Z"
    result = task_lifecycle.evaluate(ledger, observation)
    assert result["state"] == "CI_PASSED"
    assert result["hard_blockers"] == []
    assert set(result["retired_evidence_errors"]) == {row["id"] for row in old_rows}
    assert ledger["evidence"][:len(old_rows)] == old_rows


@pytest.mark.parametrize("pr_state", ["OPEN", "MERGED"])
@pytest.mark.parametrize("replacement", [False, True], ids=["ordinary", "replacement"])
@pytest.mark.parametrize("review_style", ["Z", "negative-offset", "positive-offset", "fractional", "lowercase"])
@pytest.mark.parametrize("arming_style", ["Z", "negative-offset", "positive-offset", "fractional", "lowercase"])
@pytest.mark.parametrize("arming_delta", [-0.5, 0, 0.5], ids=["armed-early", "armed-equal", "armed-late"])
def test_review_timing_compares_utc_instants(
    pr_state: str, replacement: bool, review_style: str, arming_style: str, arming_delta: float,
) -> None:
    def spell(instant: datetime, style: str) -> str:
        if style == "negative-offset":
            return instant.astimezone(timezone(timedelta(hours=-3))).isoformat()
        if style == "positive-offset":
            return instant.astimezone(timezone(timedelta(hours=2))).isoformat()
        value = instant.isoformat(timespec="microseconds" if style == "fractional" else "auto")
        value = value.replace("+00:00", "Z")
        return value.lower() if style == "lowercase" else value

    review_instant = datetime(2026, 7, 16, 10, 30, tzinfo=UTC)
    recorded_at = spell(review_instant, review_style)
    armed_at = spell(review_instant + timedelta(seconds=arming_delta), arming_style)
    ledger = _ready_evidence(_ledger())
    ledger = _add(ledger, "AC-MERGE", "github")
    old = ledger["evidence"][1]
    original = deepcopy(ledger)
    if replacement:
        ledger, current = _replacement(ledger, old, recorded_at=recorded_at)
        assert ledger["evidence"][:-1] == original["evidence"]
    else:
        ledger, current = task_lifecycle.add_evidence(
            ledger, ac_id="AC-REVIEW", evidence_type="review", summary="current ordinary review",
            url=REVIEW_URL, commit=HEAD, details=old["details"], recorded_at=recorded_at,
        )
    observation = _observation(_body(), pr_state=pr_state)
    observation["github"]["pr"]["auto_merge_enabled_at"] = armed_at
    ledger_bytes = task_lifecycle.canonical_json(ledger)
    observation_bytes = task_lifecycle.canonical_json(observation)
    result = task_lifecycle.evaluate(ledger, observation)
    blocked = arming_delta < 0
    assert result["hard_blockers"] == (["auto-merge was armed before the verified review gate"] if blocked else [])
    assert result["state"] == ("BLOCKED_WITH_RECEIPT" if blocked else "CI_PASSED" if pr_state == "OPEN" else "MERGED")
    assert result["superseded_evidence_ids"] == ([old["id"]] if replacement else [])
    assert current["recorded_at"] == recorded_at
    assert current["id"] == task_lifecycle.digest(task_lifecycle._evidence_payload(current))
    assert task_lifecycle.canonical_json(ledger) == ledger_bytes
    assert task_lifecycle.canonical_json(observation) == observation_bytes


@pytest.mark.parametrize("pr_state", ["OPEN", "MERGED"])
@pytest.mark.parametrize("reverse", [False, True])
def test_review_timing_selects_latest_instant_before_maximum(pr_state: str, reverse: bool) -> None:
    ledger = _ready_evidence(_ledger())
    ledger = _add(ledger, "AC-MERGE", "github")
    times = ["2026-07-16T12:15:00+02:00", "2026-07-16T08:00:00-03:00"]  # 10:15Z, 11:00Z.
    for recorded_at in reversed(times) if reverse else times:
        ledger, _ = task_lifecycle.add_evidence(
            ledger, ac_id="AC-REVIEW", evidence_type="review", summary="additional valid review",
            url=REVIEW_URL, commit=HEAD, details=ledger["evidence"][1]["details"], recorded_at=recorded_at,
        )
    observation = _observation(_body(), pr_state=pr_state)
    observation["github"]["pr"]["auto_merge_enabled_at"] = "2026-07-16T10:30:00Z"
    result = task_lifecycle.evaluate(ledger, observation)
    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert result["hard_blockers"] == ["auto-merge was armed before the verified review gate"]


@pytest.mark.parametrize("pr_state", ["OPEN", "MERGED"])
@pytest.mark.parametrize("invalid_at", ["invalid", "2026-07-16T10:30:00", "2026-07-16T25:00:00Z"])
@pytest.mark.parametrize("field", ["review", "arming"])
def test_review_timing_invalid_timestamp_fails_closed(pr_state: str, invalid_at: str, field: str) -> None:
    ledger = _ready_evidence(_ledger())
    ledger = _add(ledger, "AC-MERGE", "github")
    observation = _observation(_body(), pr_state=pr_state)
    if field == "review":
        record = ledger["evidence"][1]
        record["recorded_at"] = invalid_at
        record["id"] = task_lifecycle.digest(task_lifecycle._evidence_payload(record))
    else:
        observation["github"]["pr"]["auto_merge_enabled_at"] = invalid_at
    ledger_bytes = task_lifecycle.canonical_json(ledger)
    observation_bytes = task_lifecycle.canonical_json(observation)
    with pytest.raises(task_lifecycle.LifecycleError):
        task_lifecycle.evaluate(ledger, observation)
    assert task_lifecycle.canonical_json(ledger) == ledger_bytes
    assert task_lifecycle.canonical_json(observation) == observation_bytes


@pytest.mark.parametrize("pr_state", ["OPEN", "MERGED"])
def test_review_timing_uses_only_effective_valid_rows(pr_state: str) -> None:
    ledger = _ready_evidence(_ledger())
    ledger = _add(ledger, "AC-MERGE", "github")
    old = ledger["evidence"][1]
    old["recorded_at"] = "2026-07-16T09:00:00Z"
    old["id"] = task_lifecycle.digest(task_lifecycle._evidence_payload(old))
    ledger, _ = _replacement(ledger, old, recorded_at=NOW)
    observation = _observation(_body(), pr_state=pr_state)
    result = task_lifecycle.evaluate(ledger, observation)
    assert "auto-merge was armed before the verified review gate" not in result["hard_blockers"]
    tip = ledger["evidence"][-1]
    ledger, _ = _replacement(ledger, tip, recorded_at="2026-07-16T13:00:00Z")
    late = task_lifecycle.evaluate(ledger, observation)
    assert "auto-merge was armed before the verified review gate" in late["hard_blockers"]


@pytest.mark.parametrize("pr_state", ["OPEN", "MERGED"])
def test_invalid_review_row_does_not_supply_timing_for_valid_sibling(pr_state: str) -> None:
    ledger = _ready_evidence(_ledger())
    ledger = _add(ledger, "AC-MERGE", "github")
    ledger, _ = task_lifecycle.add_evidence(
        ledger, ac_id="AC-REVIEW", evidence_type="review", summary="invalid later review",
        url="https://github.com/org/repo/pull/77", commit=HEAD,
        details={"author_family": "codex", "reviewer_family": "claude", "verdict": "pass"},
        recorded_at="2026-07-16T13:00:00Z",
    )
    result = task_lifecycle.evaluate(ledger, _observation(_body(), pr_state=pr_state))
    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "auto-merge was armed before the verified review gate" not in result["hard_blockers"]


def test_valid_certification_superseded_by_bad_head_does_not_certify() -> None:
    ledger = _ready_evidence(_ledger("certify"))
    for ac_id, kind in (("AC-MERGE", "github"), ("AC-DEPLOY", "deployment"), ("AC-CERT", "certification")):
        ledger = _add(ledger, ac_id, kind)
    old = ledger["evidence"][-1]
    ledger, bad = _replacement(ledger, old, commit="c" * 40)
    observation = _observation(_body(include_deploy=True, include_certify=True), pr_state="MERGED", deployed=True)
    result = task_lifecycle.evaluate(ledger, observation)
    assert result["last_success_state"] == "DEPLOYED"
    assert result["goal_reached"] is False
    assert "AC-CERT" not in result["valid_evidence"]
    assert result["retired_evidence_errors"] == {}
    ledger, _ = _replacement(ledger, bad, commit=HEAD)
    assert task_lifecycle.evaluate(ledger, observation)["last_success_state"] == "CERTIFIED"


def test_remaining_scope_cannot_reference_superseded_evidence() -> None:
    ledger = _add(_ledger(), "AC-IMPL", "follow_up")
    old = ledger["evidence"][-1]
    ledger, tip = _replacement(ledger, old)
    with pytest.raises(task_lifecycle.LifecycleError, match="superseded record"):
        task_lifecycle.set_remaining_scope(
            ledger, status="transferred", summary="transfer", follow_up_issue=43,
            follow_up_stream_epic=10, evidence_ids=[old["id"]], now=NOW,
        )
    transferred = task_lifecycle.set_remaining_scope(
        ledger, status="transferred", summary="transfer", follow_up_issue=43,
        follow_up_stream_epic=10, evidence_ids=[tip["id"]], now=NOW,
    )
    with pytest.raises(task_lifecycle.LifecycleError, match="superseded record"):
        _replacement(transferred, tip)


def test_behavior_proof_correction_does_not_inherit_receipt(tmp_path: Path) -> None:
    ledger = _ready_evidence(_ledger(behavior_proof=True))
    reference = _behavior_receipt_reference(tmp_path)
    ledger = _add(ledger, "AC-IMPL", "behavior_proof", details=reference)
    old = ledger["evidence"][-1]
    path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    path.write_bytes(path.read_bytes() + b"\n")
    bad_ref = deepcopy(reference)
    bad_ref["behavior_proof_receipt"]["receipt_path"] = str(tmp_path / "missing.json")
    ledger, bad = _replacement(ledger, old, details={**bad_ref, "supersedes_evidence_id": old["id"]})
    result = task_lifecycle.evaluate(ledger, _observation(_body()))
    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "behavior_proof" not in result["valid_evidence"]["AC-IMPL"]
    assert result["retired_evidence_errors"] == {}
    assert any("digest" in error for error in result["hard_blockers"])
    assert any("unreadable" in error for error in result["hard_blockers"])
    good_ref = _behavior_receipt_reference(tmp_path)
    ledger, _ = _replacement(ledger, bad, details={**good_ref, "supersedes_evidence_id": bad["id"]})
    assert task_lifecycle.evaluate(ledger, _observation(_body()))["hard_blockers"] == []


@pytest.mark.parametrize("gate", ["requested_changes", "ci", "draft", "missing_review_ac", "cleanup"])
def test_valid_correction_preserves_delivery_gates(gate: str) -> None:
    ledger = _ready_evidence(_ledger())
    ledger, _ = _replacement(ledger, ledger["evidence"][-1])
    observation = _observation(_body())
    if gate == "requested_changes":
        observation["github"]["pr"]["requested_changes"] = True
        expected = "unresolved requested changes"
    elif gate == "ci":
        observation["github"]["pr"]["checks"][0]["conclusion"] = "FAILURE"
        expected = "required CI failed"
    elif gate == "draft":
        observation["github"]["pr"]["is_draft"] = True
        expected = "PR remains a draft"
    elif gate == "missing_review_ac":
        ledger["ac_snapshot"]["criteria"][1]["required_evidence"].append("command")
        ledger["ac_snapshot"]["content_hash"] = task_lifecycle.ac_content_hash(ledger["ac_snapshot"]["criteria"])
        expected = "AC-REVIEW: missing typed evidence command"
    else:
        ledger = _add(ledger, "AC-MERGE", "github")
        observation = _observation(_body(checked=True), pr_state="MERGED", issue_state="CLOSED")
        expected = "merged task branch or dispatch worktree still requires cleanup"
    result = task_lifecycle.evaluate(ledger, observation)
    assert any(expected in item for item in [*result["hard_blockers"], *result["waiting"]])
    assert result["disposition"] != "complete"


@pytest.mark.parametrize("details,error", [
    ({"author_family": "codex", "reviewer_family": "codex", "verdict": "pass"}, "outside"),
    ({"author_family": "codex", "reviewer_family": "claude", "verdict": "fail"}, "must be pass"),
    ({"author_family": "claude", "reviewer_family": "codex", "verdict": "pass"}, "author family"),
])
def test_review_correction_preserves_family_and_verdict_validation(details: dict, error: str) -> None:
    ledger = _ready_evidence(_ledger())
    old = ledger["evidence"][-1]
    with pytest.raises(task_lifecycle.LifecycleError, match=error):
        _replacement(ledger, old, details={**details, "supersedes_evidence_id": old["id"]})


def _behavior_receipt_reference(tmp_path: Path, *, receipt_updates: dict | None = None) -> dict:
    input_sha256 = "c" * 64
    receipt = {
        "schema_version": "code-review-receipt.v1",
        "author": {"family": "openai"},
        "reviewer": {"family": "deepseek"},
        "target": {"head_sha": HEAD, "input_sha256": input_sha256},
        "behavior_proof": {
            "schema_version": "behavior-proof.v1",
            "source_aware": {
                "status": "pass",
                "clauses": [{"target_input_sha256": input_sha256}],
            },
            "source_blind": {
                "status": "pass",
                "blind_enforced": False,
                "clauses": [{"target_input_sha256": input_sha256}],
            },
        },
        "final_disposition": "clean",
        "exit_code": 0,
        "error": None,
    }
    receipt.update(receipt_updates or {})
    path = (tmp_path / "behavior-proof-receipt.json").resolve()
    receipt_bytes = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    path.write_bytes(receipt_bytes)
    return {
        "behavior_proof_receipt": {
            "receipt_path": str(path),
            "receipt_sha256": "sha256:" + hashlib.sha256(receipt_bytes).hexdigest(),
            "input_sha256": input_sha256,
            "target_sha": HEAD,
        }
    }


def _approved_actionable_receipt() -> dict:
    return {
        "final_disposition": "actionable",
        "exit_code": 1,
        "error": None,
        "reviewer_payload": {
            "overall": {"correctness": "correct"},
            "finding_ids": ["F001", "F002"],
        },
        "findings": [
            {
                "id": "F001",
                "outcome": "verified",
                "disposition": "in_scope_blocker",
                "disposition_rationale": "Acceptance record fulfilled without changing the head.",
            },
            {
                "id": "F002",
                "outcome": "verified",
                "disposition": "follow_up",
                "disposition_rationale": "Non-blocking hardening has a follow-up owner.",
            },
        ],
    }


def _observation(
    body: str,
    *,
    issue_state: str = "OPEN",
    pr_state: str = "OPEN",
    requested_changes: bool = False,
    checks: str = "SUCCESS",
    deployed: bool = False,
    clean: bool = False,
) -> dict:
    return {
        "schema_version": task_lifecycle.OBSERVATION_SCHEMA_VERSION,
        "observed_at": NOW,
        "github": {
            "repository": "org/repo",
            "registered_stream_epics": [10],
            "issue": {
                "number": 42,
                "state": issue_state,
                "body": body,
                "url": "https://github.com/org/repo/issues/42",
                "closed_at": NOW if issue_state == "CLOSED" else None,
                "parent_epic": 10, "parent_repository": "org/repo",
            },
            "pr": {
                "number": 77,
                "url": "https://github.com/org/repo/pull/77",
                "state": pr_state,
                "is_draft": False,
                "head_sha": HEAD,
                "head_branch": "codex/42-closeout",
                "merge_sha": MERGE if pr_state == "MERGED" else None,
                "merged_at": NOW if pr_state == "MERGED" else None,
                "auto_merge_enabled_at": NOW,
                "review_decision": "CHANGES_REQUESTED" if requested_changes else "APPROVED",
                "requested_changes": requested_changes,
                "reviews": [],
                "checks": [
                    {
                        "name": "CI Gate",
                        "status": "COMPLETED" if checks != "PENDING" else "IN_PROGRESS",
                        "conclusion": checks if checks != "PENDING" else "",
                    }
                ],
                "body": "Refs #42",
            },
            "comments": [{"url": REVIEW_URL, "body": "PASS", "created_at": NOW}],
            "deployments": [{"environment": "production", "state": "SUCCESS", "sha": MERGE}] if deployed else [],
            "follow_up": None,
        },
        "local": {
            "primary_checkout": "/repo",
            "primary_clean": True,
            "dispatch_worktree_used": True,
            "worktree": "/repo/.worktrees/dispatch/codex/42-closeout",
            "worktree_present": not clean,
            "actual_worktree_branch": "codex/42-closeout" if not clean else None,
            "worktree_branch_matches": not clean,
            "branch": "codex/42-closeout",
            "local_branch_present": not clean,
            "remote_branch_present": not clean,
            "commits": [{"sha": HEAD, "x_agent_trailers": ["X-Agent: codex/42-closeout"]}],
            "changed_paths": ["scripts/example.py"],
            "forbidden_paths": [],
        },
    }


def test_snapshot_uses_stable_ids_and_rejects_text_drift() -> None:
    ledger = _ready_evidence(_ledger())
    observation = _observation(_body().replace("The pull request merges.", "The PR maybe merges."))

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert any("drift" in blocker for blocker in result["hard_blockers"])
    assert ledger["ac_snapshot"]["content_hash"].startswith("sha256:")


def test_open_pr_reaches_ci_passed_but_is_not_terminal() -> None:
    ledger = _ready_evidence(_ledger())

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "CI_PASSED"
    assert result["disposition"] == "waiting"
    assert result["goal_reached"] is False


def test_merged_pr_with_open_issue_is_nonterminal() -> None:
    ledger = _add(_ready_evidence(_ledger()), "AC-MERGE", "github")

    result = task_lifecycle.evaluate(
        ledger,
        _observation(_body(checked=True), pr_state="MERGED"),
    )

    assert result["state"] == "MERGED"
    assert result["disposition"] == "waiting"
    assert "actually closed issue" in " ".join(result["waiting"])


def test_auto_close_keyword_is_not_treated_as_issue_closeout() -> None:
    ledger = _add(_ready_evidence(_ledger()), "AC-MERGE", "github")
    observation = _observation(_body(checked=True), pr_state="MERGED")
    observation["github"]["pr"]["body"] = "Fixes #42"

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] == "MERGED"
    assert result["goal_reached"] is True
    assert "actually closed issue" in " ".join(result["waiting"])


def test_closed_issue_with_unverified_postclose_acs_is_rejected() -> None:
    ledger = _add(_ready_evidence(_ledger()), "AC-MERGE", "github")

    result = task_lifecycle.evaluate(
        ledger,
        _observation(_body(checked=True), issue_state="CLOSED", pr_state="MERGED"),
    )

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert any("AC-CLOSE" in blocker for blocker in result["hard_blockers"])


def test_all_evidence_issue_close_and_cleanup_are_terminal() -> None:
    ledger = _add(_ready_evidence(_ledger()), "AC-MERGE", "github")
    ledger = _add(ledger, "AC-CLOSE", "github")
    ledger = _add(ledger, "AC-CLEAN", "cleanup")
    ledger, _, _ = task_lifecycle.reconcile(
        ledger,
        _observation(_body(checked=True), pr_state="MERGED"),
        now=NOW,
    )

    result = task_lifecycle.evaluate(
        ledger,
        _observation(_body(checked=True), issue_state="CLOSED", pr_state="MERGED", clean=True),
    )

    assert result["state"] == "CLEANED_UP"
    assert result["disposition"] == "complete"


def test_first_postmerge_reconcile_requires_retained_git_proof() -> None:
    ledger = _add(_ready_evidence(_ledger()), "AC-MERGE", "github")
    observation = _observation(_body(checked=True), pr_state="MERGED")
    observation["local"].update(
        {
            "dispatch_worktree_used": False,
            "worktree_present": False,
            "actual_worktree_branch": None,
            "worktree_branch_matches": False,
            "commits": [],
        }
    )

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "dispatch worktree" in " ".join(result["hard_blockers"])


@pytest.mark.parametrize(
    ("goal", "deployment", "certification", "expected"),
    [
        ("deploy", False, False, "MERGED"),
        ("certify", True, False, "DEPLOYED"),
    ],
)
def test_terminal_goals_cannot_degrade(goal: str, deployment: bool, certification: bool, expected: str) -> None:
    ledger = _ready_evidence(_ledger(goal))
    ledger = _add(ledger, "AC-MERGE", "github")
    if deployment:
        ledger = _add(ledger, "AC-DEPLOY", "deployment")
    if certification:
        ledger = _add(ledger, "AC-CERT", "certification")

    result = task_lifecycle.evaluate(
        ledger,
        _observation(
            _body(include_deploy=True, include_certify=goal == "certify"),
            pr_state="MERGED",
            deployed=deployment,
        ),
    )

    assert result["last_success_state"] == expected
    assert result["goal_reached"] is False


def test_certify_goal_reaches_certified_only_with_typed_evidence() -> None:
    ledger = _ready_evidence(_ledger("certify"))
    for ac_id, kind in (
        ("AC-MERGE", "github"),
        ("AC-DEPLOY", "deployment"),
        ("AC-CERT", "certification"),
    ):
        ledger = _add(ledger, ac_id, kind)

    result = task_lifecycle.evaluate(
        ledger,
        _observation(
            _body(include_deploy=True, include_certify=True),
            pr_state="MERGED",
            deployed=True,
        ),
    )

    assert result["last_success_state"] == "CERTIFIED"
    assert result["goal_reached"] is True


def test_wrong_identity_requested_changes_and_git_hygiene_fail_closed() -> None:
    ledger = _ready_evidence(_ledger())
    observation = _observation(_body(), requested_changes=True)
    observation["github"]["repository"] = "org/wrong"
    observation["local"]["commits"][0]["x_agent_trailers"] = []
    observation["local"]["forbidden_paths"] = [".python-version"]

    result = task_lifecycle.evaluate(ledger, observation)

    blockers = "\n".join(result["hard_blockers"])
    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "repository" in blockers
    assert "requested changes" in blockers
    assert "X-Agent" in blockers
    assert ".python-version" in blockers


def test_spoofed_dispatch_worktree_metadata_fails_closed() -> None:
    ledger = _ready_evidence(_ledger())
    observation = _observation(_body())
    observation["local"].update(
        {
            "worktree_present": False,
            "actual_worktree_branch": "codex/wrong",
            "worktree_branch_matches": False,
        }
    )

    result = task_lifecycle.evaluate(ledger, observation)

    blockers = " ".join(result["hard_blockers"])
    assert "absent from git worktree list" in blockers
    assert "did not match Git authority" in blockers


def test_unregistered_stream_epic_fails_closed() -> None:
    ledger = _ready_evidence(_ledger())
    observation = _observation(_body())
    observation["github"]["registered_stream_epics"] = [99]

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "registered issue-stream" in " ".join(result["hard_blockers"])


def test_remaining_scope_requires_exact_reciprocal_follow_up() -> None:
    ledger = _ready_evidence(_ledger())
    ledger = _add(ledger, "AC-MERGE", "github")
    ledger = _add(ledger, "AC-CLOSE", "follow_up")
    evidence_id = ledger["evidence"][-1]["id"]
    ledger = task_lifecycle.set_remaining_scope(
        ledger,
        status="transferred",
        summary="Move documentation follow-up.",
        follow_up_issue=99,
        follow_up_stream_epic=10,
        evidence_ids=[evidence_id],
        now=NOW,
    )
    observation = _observation(_body(checked=True), pr_state="MERGED")
    observation["github"]["follow_up"] = {
        "number": 99,
        "parent_epic": 11, "parent_repository": "org/repo",
        "reciprocal_links_verified": False,
    }

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "follow-up" in " ".join(result["hard_blockers"])


def test_identical_reconcile_is_idempotent() -> None:
    ledger = _ready_evidence(_ledger())
    observation = _observation(_body())

    once, receipt, replayed = task_lifecycle.reconcile(ledger, observation, now=NOW)
    twice, replay_receipt, replayed_again = task_lifecycle.reconcile(
        once, {**observation, "observed_at": "2026-07-16T10:01:00Z"}, now=NOW
    )

    assert replayed is False
    assert replayed_again is True
    assert replay_receipt["id"] == receipt["id"]
    assert len(twice["observation_receipts"]) == 1


def test_evidence_for_other_commit_is_stale() -> None:
    ledger = _ready_evidence(_ledger())
    ledger["evidence"][0]["subject"]["commit"] = "c" * 40
    ledger["evidence"][0]["id"] = task_lifecycle.digest(task_lifecycle._evidence_payload(ledger["evidence"][0]))
    ledger = task_lifecycle.validate_lifecycle(ledger)

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert any("current PR head" in blocker for blocker in result["hard_blockers"])


def test_user_visible_ac_requires_canonical_target_bound_behavior_receipt(
    tmp_path: Path,
) -> None:
    ledger = _ready_evidence(_ledger(behavior_proof=True))

    missing = task_lifecycle.evaluate(ledger, _observation(_body()))
    ledger = _add(
        ledger,
        "AC-IMPL",
        "behavior_proof",
        details=_behavior_receipt_reference(tmp_path),
    )
    valid = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert any("behavior_proof" in blocker for blocker in missing["hard_blockers"])
    assert "behavior_proof" in valid["valid_evidence"]["AC-IMPL"]
    assert valid["state"] == "CI_PASSED"


def test_changed_behavior_receipt_fails_digest_validation(tmp_path: Path) -> None:
    reference = _behavior_receipt_reference(tmp_path)
    ledger = _ready_evidence(_ledger(behavior_proof=True))
    ledger = _add(ledger, "AC-IMPL", "behavior_proof", details=reference)
    receipt_path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    receipt_path.write_text("{}\n", encoding="utf-8")

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "digest" in " ".join(result["hard_blockers"])


def test_approved_nonblocking_behavior_receipt_preserves_findings_and_snapshot(tmp_path: Path) -> None:
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=_approved_actionable_receipt())
    path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    original_bytes = path.read_bytes()
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL",
        "behavior_proof",
        details=reference,
    )
    original_ledger = deepcopy(ledger)

    updated, receipt, replayed = task_lifecycle.reconcile(ledger, _observation(_body()), now=NOW)

    assert receipt["state"] == "CI_PASSED"
    assert not receipt["hard_blockers"]
    assert replayed is False
    assert updated["ac_snapshot"] == original_ledger["ac_snapshot"]
    assert updated["evidence"] == original_ledger["evidence"]
    assert ledger == original_ledger
    assert path.read_bytes() == original_bytes


@pytest.mark.parametrize(
    ("field_path", "value"),
    [
        (("final_disposition",), "clean"),
        (("final_disposition",), "incomplete"),
        (("exit_code",), 0),
        (("exit_code",), 2),
        (("reviewer_payload", "overall", "correctness"), "incorrect"),
        (("reviewer_payload", "overall", "correctness"), "uncertain"),
        (("reviewer_payload",), None),
        (("reviewer_payload", "overall"), None),
        (("reviewer_payload", "finding_ids"), ["F001"]),
        (("reviewer_payload", "finding_ids"), ["F001", "F003"]),
        (("findings", 1, "id"), "F003"),
        (("reviewer_payload", "finding_ids"), None),
        (("findings",), None),
        (("findings", 1), None),
        (("findings", 1, "outcome"), "quote_missing"),
        (("findings", 1, "outcome"), None),
        (("findings", 1, "disposition"), None),
        (("findings", 1, "disposition"), " "),
        (("findings", 1, "disposition_rationale"), None),
        (("findings", 1, "disposition_rationale"), " "),
        (("findings", 1, "disposition"), "stop_and_escalate"),
        (("findings", 1, "disposition"), "STOP_AND_ESCALATE"),
        (("findings", 1, "disposition"), "stop_and_escalate "),
        (("findings", 1, "disposition"), "whatever"),
        (("error",), "envelope_proof_failed:tests_failed"),
        (("error",), ""),
        (("target", "head_sha"), "d" * 40),
        (("target", "input_sha256"), "d" * 64),
        (("reviewer", "family"), "openai"),
        (("schema_version",), "other-receipt.v1"),
        (("behavior_proof", "schema_version"), "other-proof.v1"),
        (("behavior_proof", "source_aware", "status"), "fail"),
        (("behavior_proof", "source_blind", "status"), "fail"),
        (("behavior_proof", "source_aware", "clauses"), []),
        (("behavior_proof", "source_blind", "clauses"), []),
    ],
    ids=[
        "clean-exit-one", "incomplete", "actionable-exit-zero", "actionable-exit-two",
        "incorrect", "uncertain", "missing-payload", "missing-overall",
        "omitted-finding-id", "mismatched-finding-id", "mismatched-receipt-id", "missing-payload-ids",
        "missing-findings", "malformed-finding", "unverified-second-finding",
        "missing-outcome", "missing-disposition", "blank-disposition",
        "missing-rationale", "blank-rationale", "stop-and-escalate",
        "mixed-case-disposition", "padded-disposition", "unknown-disposition",
        "forged-correct-with-error", "non-null-empty-error", "stale-target",
        "stale-fingerprint", "same-family", "noncanonical-receipt", "noncanonical-proof",
        "forged-correct-aware-failure", "forged-correct-blind-failure",
        "unbound-aware", "unbound-blind",
    ],
)
def test_actionable_behavior_receipt_refuses_each_failed_clause(
    tmp_path: Path, field_path: tuple, value: object,
) -> None:
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=_approved_actionable_receipt())
    path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    receipt = json.loads(path.read_bytes())
    entry = receipt
    for key in field_path[:-1]:
        entry = entry[key]
    entry[field_path[-1]] = value
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=receipt)
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "behavior_proof" not in result["valid_evidence"]["AC-IMPL"]
    assert any("behavior-proof" in blocker for blocker in result["hard_blockers"])


def test_actionable_behavior_receipt_without_findings_is_refused(tmp_path: Path) -> None:
    receipt = _approved_actionable_receipt()
    receipt["findings"] = []
    receipt["reviewer_payload"]["finding_ids"] = []
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=receipt)
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "behavior_proof" not in result["valid_evidence"]["AC-IMPL"]
    assert any("behavior-proof" in blocker for blocker in result["hard_blockers"])


@pytest.mark.parametrize("actionable", [False, True], ids=["clean", "actionable"])
def test_behavior_receipt_without_error_key_is_refused(tmp_path: Path, actionable: bool) -> None:
    reference = _behavior_receipt_reference(
        tmp_path, receipt_updates=_approved_actionable_receipt() if actionable else None,
    )
    path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    receipt = json.loads(path.read_bytes())
    del receipt["error"]
    receipt_bytes = (json.dumps(receipt) + "\n").encode()
    path.write_bytes(receipt_bytes)
    reference["behavior_proof_receipt"]["receipt_sha256"] = "sha256:" + hashlib.sha256(receipt_bytes).hexdigest()
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "behavior_proof" not in result["valid_evidence"]["AC-IMPL"]
    assert any("behavior-proof" in blocker for blocker in result["hard_blockers"])


def test_clean_behavior_receipt_with_error_is_refused(tmp_path: Path) -> None:
    reference = _behavior_receipt_reference(tmp_path, receipt_updates={"error": "runner failed"})
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "behavior_proof" not in result["valid_evidence"]["AC-IMPL"]


def test_forged_correct_without_receipt_finding_id_is_refused(tmp_path: Path) -> None:
    receipt = _approved_actionable_receipt()
    del receipt["findings"][1]["id"]
    receipt["reviewer_payload"]["finding_ids"] = ["F001", None]
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=receipt)
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "behavior_proof" not in result["valid_evidence"]["AC-IMPL"]


def test_closeout_cli_reconciles_original_actionable_receipt(
    tmp_path: Path, capsys: pytest.CaptureFixture,
) -> None:
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=_approved_actionable_receipt())
    receipt_path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    receipt_bytes = receipt_path.read_bytes()
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )
    state_file = tmp_path / "lifecycle.json"
    task_lifecycle.write_lifecycle(state_file, ledger)
    observation_file = tmp_path / "observation.json"
    observation_file.write_text(json.dumps(_observation(_body())), encoding="utf-8")

    code = task_closeout.main([
        "reconcile", "--state-file", str(state_file),
        "--observation-file", str(observation_file), "--now", NOW,
    ])

    assert code == 0
    output = json.loads(capsys.readouterr().out)
    assert output["receipt"]["state"] == "CI_PASSED"
    assert output["receipt"]["hard_blockers"] == []
    persisted = task_lifecycle.load_lifecycle(state_file)
    assert persisted["current_state"] == "CI_PASSED"
    assert persisted["ac_snapshot"] == ledger["ac_snapshot"]
    assert persisted["evidence"] == ledger["evidence"]
    assert receipt_path.read_bytes() == receipt_bytes


def test_actionable_behavior_receipt_changed_bytes_fail_digest_validation(tmp_path: Path) -> None:
    reference = _behavior_receipt_reference(tmp_path, receipt_updates=_approved_actionable_receipt())
    path = Path(reference["behavior_proof_receipt"]["receipt_path"])
    path.write_bytes(path.read_bytes() + b"\n")
    ledger = _add(
        _ready_evidence(_ledger(behavior_proof=True)),
        "AC-IMPL", "behavior_proof", details=reference,
    )

    result = task_lifecycle.evaluate(ledger, _observation(_body()))

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "digest" in " ".join(result["hard_blockers"])


def test_carrier_preserves_identity_ac_snapshot_and_remaining_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=30)
    ledger = _ledger()
    path = task_lifecycle.lifecycle_path(tmp_path, ledger["identity"])
    task_lifecycle.write_lifecycle(path, ledger)

    carrier = task_lifecycle.carrier_projection(ledger, state_file=str(path))

    assert carrier["identity"] == ledger["identity"]
    assert carrier["ac_snapshot"] == ledger["ac_snapshot"]
    assert carrier["remaining_scope"] == ledger["remaining_scope"]
    assert path.name == "issue-42.json"


def test_local_git_observation_cross_checks_exact_worktree_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True, timeout=30)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True, timeout=30)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
        check=True,
        timeout=30,
    )
    (repo / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, timeout=30)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True, timeout=30)
    worktree = repo / ".worktrees" / "dispatch" / "codex" / "42-closeout"
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "worktree",
            "add",
            "-qb",
            "codex/42-closeout",
            str(worktree),
        ],
        check=True,
        timeout=30,
    )

    observed = task_lifecycle.observe_local_git(
        repo,
        head_sha=None,
        branch="codex/42-closeout",
        worktree=str(worktree),
    )
    wrong = task_lifecycle.observe_local_git(
        repo,
        head_sha=None,
        branch="codex/wrong",
        worktree=str(worktree),
    )

    assert observed["worktree_present"] is True
    assert observed["dispatch_worktree_used"] is True
    assert observed["actual_worktree_branch"] == "codex/42-closeout"
    assert observed["worktree_branch_matches"] is True
    assert wrong["worktree_branch_matches"] is False


# Offline Git object pack from the public actions/hello-world-javascript-action
# merge below, signed by the pinned GitHub key. It retains the exact commits and
# trees needed by merge-tree; unchanged blobs are unnecessary. The base is a
# shallow boundary, so neither historical repository objects nor network access
# are required. Git index-pack checks the pack checksum and object identities.
SIGNED_PUBLISHER_MERGE = "47eaec9b0ef67e9ce32c6bac2bddb1f1223df554"
SIGNED_PUBLISHER_BASE = "7b5f22c2afb0b04bc23e02fac244ee8d6874961f"
SIGNED_PUBLISHER_PACK = (
    "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"
)


@pytest.fixture
def signed_publisher_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    repo = tmp_path / "signed-publisher"
    subprocess.run(["git", "init", "-q", str(repo)], check=True, capture_output=True, timeout=30)
    subprocess.run(
        ["git", "-C", str(repo), "index-pack", "--stdin"],
        input=base64.b64decode(SIGNED_PUBLISHER_PACK), capture_output=True, check=True, timeout=30,
    )
    (repo / ".git" / "shallow").write_text(SIGNED_PUBLISHER_BASE + "\n", encoding="utf-8")
    return repo


@pytest.mark.parametrize("format_override", ["openpgp", "ssh", "x509"])
def test_real_git_accepts_pinned_publisher_with_isolated_keyring(
    signed_publisher_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    format_override: str,
) -> None:
    repo = signed_publisher_repo
    # The caller's empty keyring cannot verify this commit. Its configured
    # verifier and signature format must also be ignored by the production path.
    caller_home = tmp_path / "caller keyring"
    caller_home.mkdir(mode=0o700)
    monkeypatch.setenv("GNUPGHOME", str(caller_home))
    caller_before = list(caller_home.iterdir())
    for key, value in (
        ("gpg.format", format_override),
        ("gpg.program", str(tmp_path / "unavailable-gpg")),
        ("gpg.openpgp.program", str(tmp_path / "unavailable-openpgp")),
    ):
        task_lifecycle._run_git(repo, ["config", key, value])
    parents = task_lifecycle._run_git(repo, ["show", "-s", "--format=%P", SIGNED_PUBLISHER_MERGE]).split()

    assert task_lifecycle._verified_publisher_merge(repo, SIGNED_PUBLISHER_MERGE, parents) is True
    assert list(caller_home.iterdir()) == caller_before


def test_vendored_publisher_file_contains_both_keys(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            "gpg", "--no-options", "--homedir", str(tmp_path), "--batch",
            "--with-colons", "--show-keys", str(task_lifecycle.GITHUB_WEB_FLOW_KEY_FILE),
        ],
        capture_output=True, text=True, check=True, timeout=30,
    )
    fingerprints = {
        line.split(":")[9] for line in result.stdout.splitlines() if line.startswith("fpr:")
    }
    assert fingerprints == {
        task_lifecycle.GITHUB_WEB_FLOW_FINGERPRINT,
        "5DE3E0509C47EA3CF04A42D34AEE18F83AFDEB23",
    }


@pytest.mark.parametrize("failure", ["no-gpg", "missing-key-file", "invalid-key-file"])
def test_real_publisher_verification_fails_closed_without_keyring(
    signed_publisher_repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str,
) -> None:
    if failure == "no-gpg":
        monkeypatch.setattr(task_lifecycle.shutil, "which", lambda _program: None)
    else:
        key_file = tmp_path / "unavailable-key.gpg"
        if failure == "invalid-key-file":
            key_file.write_text("invalid public key\n", encoding="utf-8")
        monkeypatch.setattr(task_lifecycle, "GITHUB_WEB_FLOW_KEY_FILE", key_file)
    parents = task_lifecycle._run_git(
        signed_publisher_repo, ["show", "-s", "--format=%P", SIGNED_PUBLISHER_MERGE],
    ).split()

    assert task_lifecycle._verified_publisher_merge(
        signed_publisher_repo, SIGNED_PUBLISHER_MERGE, parents,
    ) is False


def test_real_git_rejects_throwaway_signed_publisher_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    key_home = tmp_path / "throwaway-keyring"
    key_home.mkdir(mode=0o700)
    monkeypatch.setenv("GNUPGHOME", str(key_home))
    repo = tmp_path / "repo"
    repo.mkdir()
    gpg = shutil.which("gpg")
    assert gpg is not None

    def git(*args: str, message: str | None = None) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo, input=message, capture_output=True, text=True,
            check=True, timeout=30,
        ).stdout.strip()

    try:
        subprocess.run(
            [
                gpg, "--no-options", "--homedir", str(key_home), "--batch",
                "--pinentry-mode", "loopback", "--passphrase", "",
                "--quick-generate-key", "GitHub <noreply@github.com>", "ed25519", "sign", "0",
            ],
            check=True, capture_output=True, timeout=30,
        )
        keys = subprocess.run(
            [gpg, "--no-options", "--homedir", str(key_home), "--with-colons", "--list-keys"],
            check=True, capture_output=True, text=True, timeout=30,
        ).stdout
        fingerprint = next(line.split(":")[9] for line in keys.splitlines() if line.startswith("fpr:"))
        git("init", "-q", "-b", "main")
        for key, value in (
            ("user.name", "GitHub"), ("user.email", "noreply@github.com"),
            ("user.signingkey", fingerprint), ("gpg.format", "openpgp"),
            ("gpg.program", gpg), ("gpg.openpgp.program", gpg), ("commit.gpgsign", "false"),
        ):
            git("config", key, value)
        (repo / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
        git("add", ".gitignore")
        tree = git("write-tree")
        base = git("commit-tree", tree, message="base\n")
        git("update-ref", "refs/heads/main", base)
        main = git("commit-tree", tree, "-p", base, message="main update\n")
        git("update-ref", "refs/remotes/origin/main", main)
        topic = git("commit-tree", tree, "-p", base, message="implementation\n\nX-Agent: codex/42-closeout\n")
        head = git(
            "commit-tree", "-S", tree, "-p", topic, "-p", main,
            message="Merge branch 'main' into codex/42-closeout\n",
        )
        # Prove that this is a valid signature in the caller's trusted keyring,
        # and that the merge tree is clean. Rejection must be about publisher identity.
        assert git("show", "-s", "--format=%G?%x1f%GF", head) == f"G\x1f{fingerprint}"
        assert fingerprint != task_lifecycle.GITHUB_WEB_FLOW_FINGERPRINT
        assert git("merge-tree", "--write-tree", "--no-messages", topic, main) == tree
        git("reset", "--hard", base)
        worktree = repo / ".worktrees" / "dispatch" / "codex" / "42-closeout"
        git("worktree", "add", "-qb", "codex/42-closeout", str(worktree), head)

        observed = task_lifecycle.observe_local_git(
            worktree, head_sha=head, branch="codex/42-closeout", worktree=str(worktree),
        )

        observed_commit = next(item for item in observed["commits"] if item["sha"] == head)
        assert observed_commit["second_parent_on_main"] is True
        assert observed_commit["verified_publisher_merge"] is False
        assert task_lifecycle._local_readiness(observed) == [
            f"commit {head} lacks exactly one valid X-Agent trailer",
        ]
    finally:
        subprocess.run(
            ["gpgconf", "--homedir", str(key_home), "--kill", "gpg-agent"],
            check=True, capture_output=True, timeout=30,
        )


@pytest.mark.parametrize(
    ("shape", "trailers", "accepted"),
    [
        ("ordinary", "X-Agent: codex/42-closeout", True),
        ("publisher", "X-Agent: codex/42-closeout", True),
        ("ordinary", "", False),
        ("local-agent", "", False),
        ("name-only", "", False),
        ("header-only", "", False),
        ("extra-tree", "", False),
        ("wrong-branch", "", False),
        ("merge-unavailable", "", False),
        ("one-parent", "", False),
        ("off-main", "", False),
        ("ancestry-unavailable", "", False),
        ("other-subject", "", False),
        ("multiple-branches", "", False),
        ("no-branch", "", False),
        ("three-parents", "", False),
        ("publisher", "X-Agent:", False),
        ("publisher", "X-Agent: codex/42-closeout\nX-Agent: codex/other", False),
    ],
)
def test_local_git_commit_attribution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, shape: str, trailers: str, accepted: bool,
) -> None:
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        monkeypatch.delenv(name, raising=False)
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args: str, message: str | None = None) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo, input=message, capture_output=True, text=True,
            check=True, timeout=30,
        ).stdout.strip()

    git("init", "-q", "-b", "main")
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.com")
    git("config", "commit.gpgsign", "false")
    (repo / ".gitignore").write_text(".worktrees/\n", encoding="utf-8")
    git("add", ".gitignore")
    tree = git("write-tree")

    def commit(message: str, *parents: str) -> str:
        args = ["commit-tree", tree]
        for parent in parents:
            args.extend(["-p", parent])
        return git(*args, message=message + "\n")

    base = commit("base")
    git("update-ref", "refs/heads/main", base)
    main_parent = commit("main update", base)
    main_tip = commit("later main update", main_parent)
    git("update-ref", "refs/remotes/origin/main", main_tip)
    topic = commit("implementation\n\nX-Agent: codex/42-closeout", base)
    side = commit("side branch\n\nX-Agent: codex/side", base)
    subject = "Merge branch 'main' into codex/42-closeout"
    parents = [topic, main_parent]
    if shape == "ordinary":
        subject, parents = "implementation update", [topic]
    elif shape == "one-parent":
        parents = [topic]
    elif shape == "off-main":
        parents = [topic, side]
    elif shape == "other-subject":
        subject = "Merge branch 'topic' into codex/42-closeout"
    elif shape == "multiple-branches":
        subject += " another-branch"
    elif shape == "no-branch":
        subject = "Merge branch 'main' into "
    elif shape == "three-parents":
        parents = [topic, main_parent, side]
    elif shape == "wrong-branch":
        subject = "Merge branch 'main' into codex/other-task"
    elif shape == "extra-tree":
        (repo / "agent-added.txt").write_text("unattributed addition\n", encoding="utf-8")
        git("add", "agent-added.txt")
        tree = git("write-tree")
    elif shape == "name-only":
        git("config", "user.name", "GitHub")
        git("config", "user.email", "noreply@github.com")
    head = commit(subject + ("\n\n" + trailers if trailers else ""), *parents)
    if shape == "header-only":
        raw = git("cat-file", "commit", head)
        headers, _, body = raw.partition("\n\n")
        raw = headers + "\ngpgsig -----BEGIN PGP SIGNATURE-----\n invalid\n -----END PGP SIGNATURE-----\n\n" + body
        head = git("hash-object", "-w", "-t", "commit", "--stdin", message=raw + "\n")
    # Keep the fixture's primary checkout clean after constructing an extra tree.
    git("reset", "--hard", base)
    worktree = repo / ".worktrees" / "dispatch" / "codex" / "42-closeout"
    git("worktree", "add", "-qb", "codex/42-closeout", str(worktree), head)
    run_git = task_lifecycle._run_git

    def publisher_verification(root: Path, args: list[str]) -> str:
        if shape == "ancestry-unavailable" and args[:2] == ["merge-base", "--is-ancestor"]:
            raise task_lifecycle.LifecycleError("ancestry unavailable")
        if shape == "merge-unavailable" and args[0] == "merge-tree":
            raise task_lifecycle.LifecycleError("merge proof unavailable")
        if (
            shape in {"extra-tree", "merge-unavailable"}
            and args[-4:] == ["show", "-s", "--format=%G?%x1f%GF", head]
        ):
            # Simulate valid signatures only for rejected tree/proof cases.
            # The publisher accept path uses the real signed fixture above.
            return f"U\x1f{task_lifecycle.GITHUB_WEB_FLOW_FINGERPRINT}"
        return run_git(root, args)

    monkeypatch.setattr(task_lifecycle, "_run_git", publisher_verification)

    observed = task_lifecycle.observe_local_git(
        worktree, head_sha=head, branch="codex/42-closeout", worktree=str(worktree),
    )

    observed_commit = next(item for item in observed["commits"] if item["sha"] == head)
    assert observed_commit == {
        "sha": head,
        "subject": subject.rstrip(),
        "parents": parents,
        "second_parent_on_main": (
            len(parents) == 2 and parents[1] == main_parent and shape != "ancestry-unavailable"
        ),
        "verified_publisher_merge": False,
        "x_agent_trailers": trailers.splitlines(),
    }
    blockers = task_lifecycle._local_readiness(observed)
    if accepted:
        assert blockers == []
    else:
        assert blockers == [f"commit {head} lacks exactly one valid X-Agent trailer"]


@pytest.mark.parametrize(
    ("signature", "accepted"),
    [
        ("G\x1f5DE3E0509C47EA3CF04A42D34AEE18F83AFDEB23", False),
        ("U\x1f5DE3E0509C47EA3CF04A42D34AEE18F83AFDEB23", False),
        *[(f"{status}\x1f{task_lifecycle.GITHUB_WEB_FLOW_FINGERPRINT}", False) for status in "BXYREN"],
        ("G\x1f" + "a" * 40, False),
        ("G\x1f", False),
        ("GitHub", False),
    ],
)
def test_publisher_merge_requires_verified_pinned_signature(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, signature: str, accepted: bool,
) -> None:
    calls = []

    def run_git(root: Path, args: list[str]) -> str:
        calls.append(args)
        return signature if args[-4] == "show" and "%G?" in args[-2] else "tree"

    monkeypatch.setattr(task_lifecycle, "_run_git", run_git)
    assert task_lifecycle._verified_publisher_merge(tmp_path, HEAD, [HEAD, MERGE]) is accepted
    assert any(args[0] == "merge-tree" for args in calls) is accepted


@pytest.mark.parametrize("failure", ["signature", "merge-tree", "commit-tree", "parents"])
def test_publisher_merge_proof_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str,
) -> None:
    def run_git(root: Path, args: list[str]) -> str:
        if args[0] == "merge-tree":
            if failure == "merge-tree":
                raise task_lifecycle.LifecycleError("conflicting or unavailable merge")
            return "tree"
        if "%G?" in args[-2]:
            if failure == "signature":
                raise task_lifecycle.LifecycleError("verification unavailable")
            return f"U\x1f{task_lifecycle.GITHUB_WEB_FLOW_FINGERPRINT}"
        raise task_lifecycle.LifecycleError("commit tree unavailable")

    monkeypatch.setattr(task_lifecycle, "_run_git", run_git)
    parents = [HEAD] if failure == "parents" else [HEAD, MERGE]
    assert task_lifecycle._verified_publisher_merge(tmp_path, HEAD, parents) is False


def test_reconcile_accepts_publisher_merge_without_adding_evidence() -> None:
    ledger = _ready_evidence(_ledger())
    evidence = deepcopy(ledger["evidence"])
    observation = _observation(_body())
    observation["local"]["commits"].append({
        "sha": MERGE,
        "subject": "Merge branch 'main' into codex/42-closeout",
        "parents": [HEAD, "c" * 40],
        "second_parent_on_main": True,
        "verified_publisher_merge": True,
        "x_agent_trailers": [],
    })

    reconciled, receipt, _ = task_lifecycle.reconcile(ledger, observation, now=NOW)

    assert receipt["state"] == "CI_PASSED"
    assert receipt["hard_blockers"] == []
    assert reconciled["evidence"] == evidence


@pytest.mark.parametrize("missing_proof", ["branch", "signature-and-tree"])
def test_readiness_rejects_unproven_publisher_merge(missing_proof: str) -> None:
    local = _observation(_body())["local"]
    commit = {
        "sha": MERGE,
        "subject": "Merge branch 'main' into codex/42-closeout",
        "parents": [HEAD, "c" * 40],
        "second_parent_on_main": True,
        "verified_publisher_merge": True,
        "x_agent_trailers": [],
    }
    if missing_proof == "branch":
        commit["subject"] = "Merge branch 'main' into codex/another-task"
    else:
        del commit["verified_publisher_merge"]
    local["commits"].append(commit)
    assert task_lifecycle._local_readiness(local) == [
        f"commit {MERGE} lacks exactly one valid X-Agent trailer",
    ]


def test_legacy_migration_preserves_proof_lists() -> None:
    ledger = _ready_evidence(_ledger())
    legacy = {
        "schema_version": "task-lifecycle.legacy",
        "pr_number": 77,
        "evidence": deepcopy(ledger["evidence"]),
        "observation_receipts": [],
        "mutation_receipts": [],
    }

    migrated = task_lifecycle.migrate_legacy(
        legacy,
        identity=_identity(),
        policy=_policy(),
        issue_body=_body(),
        required_checks=["CI Gate"],
        author_family="codex",
        now=NOW,
    )

    assert migrated["migration"]["legacy"] is True
    assert migrated["evidence"] == legacy["evidence"]


def test_schema_round_trip_is_strict() -> None:
    ledger = _ledger()
    schema = json.loads(
        Path("agents_extensions/shared/schemas/task-lifecycle.v1.schema.json").read_text(encoding="utf-8")
    )
    assert schema["additionalProperties"] is False
    assert task_lifecycle.validate_lifecycle(ledger) == ledger


@pytest.mark.parametrize("state", task_lifecycle.STATES)
def test_every_lifecycle_boundary_survives_durable_resume(tmp_path: Path, state: str) -> None:
    ledger = _ledger()
    ledger["current_state"] = state
    path = tmp_path / f"{state.lower()}.json"

    task_lifecycle.write_lifecycle(path, ledger)
    resumed = task_lifecycle.load_lifecycle(path)

    assert resumed == task_lifecycle.validate_lifecycle(ledger)
    assert task_lifecycle.carrier_projection(resumed)["current_state"] == state


# --------------------------------------------------------------------------- #
# #6028 — resolve_membership: the ONE canonical native-or-unique-body proof
# shared by lifecycle initialization, reconciliation, and every mutation gate.
# --------------------------------------------------------------------------- #
def _fresh_report(now: float, index: dict) -> dict:
    return {
        "repository": "org/repo",
        "generated_at": now,
        "membership_complete": True,
        "incomplete_nodes": [],
        "effective_membership": index,
        "open_issue_numbers": [42, 10],
    }


def test_resolve_membership_native_success() -> None:
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=10,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10, 20],
        membership_report=None,
    )
    assert result == {
        "valid": True,
        "method": "native",
        "epic": 10,
        "generated_at": None,
        "digest": None,
        "reason": None,
    }


def test_resolve_membership_unique_body_success() -> None:
    import time

    now = time.time()
    report = _fresh_report(now, {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}})

    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10, 20],
        membership_report=report,
    )

    assert result["valid"] is True
    assert result["method"] == "body"
    assert result["epic"] == 10
    assert result["generated_at"] == now
    assert result["digest"].startswith("sha256:")


def test_resolve_membership_native_precedence_over_conflicting_body_evidence() -> None:
    """Native parentage decides the outcome outright — a native parent that
    disagrees with the identity's stream epic is rejected, never falls
    through to body evidence even when body evidence would say otherwise."""
    import time

    report = _fresh_report(
        time.time(),
        {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}},
    )

    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=20,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10, 20],
        membership_report=report,
    )

    assert result["valid"] is False
    assert result["method"] is None
    assert "native parent epic" in result["reason"]


def test_resolve_membership_rejects_missing_audit_evidence() -> None:
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10],
        membership_report=None,
    )
    assert result["valid"] is False
    assert result["method"] is None
    assert "missing" in result["reason"]


def test_resolve_membership_rejects_stale_audit_evidence() -> None:
    import time

    report = _fresh_report(
        time.time() - 10_000,
        {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}},
    )
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10],
        membership_report=report,
    )
    assert result["valid"] is False
    assert "stale" in result["reason"]


def test_resolve_membership_rejects_malformed_audit_evidence() -> None:
    import time

    report = _fresh_report(time.time(), {"42": {"epics": [10]}})  # missing required fields
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10],
        membership_report=report,
    )
    assert result["valid"] is False
    assert "malformed" in result["reason"]


def test_resolve_membership_rejects_orphan() -> None:
    """No native parent AND no entry at all in the fresh audit index — this is
    also the shape a CHILD-SIDE-ONLY ``Refs #10`` reference produces: the
    auditor's effective-membership index is built exclusively from what the
    epic body says, so a mention that lives only in the child issue's own
    prose never creates an entry here."""
    import time

    report = _fresh_report(time.time(), {})
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10],
        membership_report=report,
    )
    assert result["valid"] is False
    assert "orphan" in result["reason"]


def test_resolve_membership_rejects_wrong_epic() -> None:
    import time

    report = _fresh_report(
        time.time(),
        {"42": {"epics": [20], "streams": ["other"], "via": "body", "unique_stream": True}},
    )
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10, 20],
        membership_report=report,
    )
    assert result["valid"] is False
    assert "different epic" in result["reason"]


def test_resolve_membership_rejects_multi_home() -> None:
    import time

    report = _fresh_report(
        time.time(),
        {
            "42": {
                "epics": [10, 20],
                "streams": ["infra", "other"],
                "via": "body",
                "unique_stream": False,
            }
        },
    )
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10, 20],
        membership_report=report,
    )
    assert result["valid"] is False
    assert "ambiguously multi-homed" in result["reason"]


def test_resolve_membership_reviewer_case_fails_closed_on_incomplete_traversal() -> None:
    """Opus 5.5 review finding 1 (issue #8661): root #10 references #500,
    root #20 references #500, but #20's traversal was incomplete.
    Even though #500 is in effective_membership under #10 with unique_stream: True,
    resolve_membership must fail closed naming unread node #20."""
    import time

    incomplete_report = {
        "generated_at": time.time(),
        "membership_complete": False,
        "incomplete_nodes": [20],
        "warnings": [{"code": "traversal_incomplete", "issue": 20}],
        "effective_membership": {
            "500": {
                "epics": [10],
                "streams": ["stream10"],
                "via": "body",
                "unique_stream": True,
            }
        },
        "open_issue_numbers": [10, 500],
    }
    result = task_lifecycle.resolve_membership(
        issue_number=500,
        stream_epic=10,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10, 20],
        membership_report=incomplete_report,
    )
    assert result["valid"] is False
    assert "#20" in result["reason"]
    assert "incomplete" in result["reason"]


def test_resolve_membership_rejects_unflagged_or_mistyped_completeness() -> None:
    """A pre-flag cache, the string "false", or a non-list incomplete_nodes is unverified."""
    import time

    index = {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}}
    absent = _fresh_report(time.time(), index)
    del absent["membership_complete"]
    string_false = _fresh_report(time.time(), index)
    string_false["membership_complete"] = "false"
    non_list = _fresh_report(time.time(), index)
    non_list["incomplete_nodes"] = "false"
    for report in (absent, string_false, non_list):
        result = task_lifecycle.resolve_membership(
            issue_number=42,
            stream_epic=10,
            native_parent_epic=None,
            repository="org/repo",
            native_parent_repository="org/repo",
            registered_epics=[10],
            membership_report=report,
        )
        assert result["valid"] is False
        assert "incomplete" in result["reason"]


def test_resolve_membership_accepts_complete_traversal_report() -> None:
    import time

    complete_report = {
        "repository": "org/repo",
        "generated_at": time.time(),
        "membership_complete": True,
        "incomplete_nodes": [],
        "warnings": [],
        "effective_membership": {
            "500": {
                "epics": [10],
                "streams": ["stream10"],
                "via": "body",
                "unique_stream": True,
            }
        },
        "open_issue_numbers": [10, 500],
    }
    result = task_lifecycle.resolve_membership(
        issue_number=500,
        stream_epic=10,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10, 20],
        membership_report=complete_report,
    )
    assert result["valid"] is True
    assert result["method"] == "body"
    assert result["epic"] == 10


def test_resolve_membership_rejects_unregistered_stream_epic() -> None:
    result = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=10,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[99],
        membership_report=None,
    )
    assert result["valid"] is False
    assert "registered issue-stream" in result["reason"]


def test_resolve_membership_digest_is_deterministic_over_the_index() -> None:
    import time

    now = time.time()
    index = {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}}
    first = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10],
        membership_report=_fresh_report(now, index),
    )
    second = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10],
        membership_report=_fresh_report(now, dict(index)),
    )
    changed = task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=10,
        native_parent_epic=None,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10],
        membership_report=_fresh_report(
            now,
            {
                **index,
                "7": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True},
            },
        ),
    )
    assert first["digest"] == second["digest"]
    assert first["digest"] != changed["digest"]


# --------------------------------------------------------------------------- #
# #9783 — a native descendant reached through an unregistered sub-epic is
# accepted only on the audit's own fresh, complete native-chain resolution.
# --------------------------------------------------------------------------- #
def _native(*epics: int) -> dict:
    return {
        "epics": list(epics),
        "streams": ["infra"] if len(epics) == 1 else ["infra", "other"],
        "via": "native",
        "unique_stream": len(epics) == 1,
    }


def _chain(report: dict | None, *, stream_epic: int = 10, native_parent_epic: int = 30) -> dict:
    return task_lifecycle.resolve_membership(
        issue_number=42,
        stream_epic=stream_epic,
        native_parent_epic=native_parent_epic,
        repository="org/repo",
        native_parent_repository="org/repo",
        registered_epics=[10, 20],
        membership_report=report,
    )


def test_resolve_membership_accepts_native_grandchild_through_unregistered_sub_epic() -> None:
    import time

    now = time.time()
    index = {"42": _native(10), "30": _native(10)}
    result = _chain(_fresh_report(now, index))
    assert result == {
        "valid": True,
        "method": "native_chain",
        "epic": 10,
        "generated_at": now,
        "digest": task_lifecycle.digest(index),
        "reason": None,
    }


@pytest.mark.parametrize(
    "index,reason",
    [
        ({"42": _native(20), "30": _native(20)}, "reaches a different registered epic"),
        ({"42": _native(10, 20), "30": _native(10)}, "multi-homed"),
        ({"30": _native(10)}, "does not resolve the issue through a native sub-issue chain"),
        (
            {"42": {**_native(10), "via": "body"}, "30": _native(10)},
            "does not resolve the issue through a native sub-issue chain",
        ),
        ({"42": _native(10)}, "native parent is not itself a native descendant"),
        ({"42": _native(10), "30": _native(20)}, "native parent is not itself a native descendant"),
    ],
    ids=["different-epic", "multi-homed", "orphan", "body-only", "parent-absent", "parent-elsewhere"],
)
def test_resolve_membership_refuses_ambiguous_native_chain(index: dict, reason: str) -> None:
    import time

    now = time.time()
    result = _chain(_fresh_report(now, index))
    assert result["valid"] is False
    assert result["method"] is None
    assert result["reason"].startswith("native parent #30 is not a registered stream epic and ")
    assert reason in result["reason"]
    assert result["generated_at"] == now
    assert result["digest"] == task_lifecycle.digest(index)


def test_resolve_membership_refuses_native_chain_on_stale_missing_or_incomplete_audit() -> None:
    import time

    index = {"42": _native(10), "30": _native(10)}
    stale = _chain(_fresh_report(time.time() - 7200, index))
    missing = _chain(None)
    incomplete_report = {
        **_fresh_report(time.time(), index),
        "membership_complete": False,
        "incomplete_nodes": [30],
    }
    incomplete = _chain(incomplete_report)

    for result in (stale, missing):
        assert result["valid"] is False
        assert "missing, stale, or malformed" in result["reason"]
    assert incomplete["valid"] is False
    assert "incomplete (unread nodes: #30)" in incomplete["reason"]


def test_resolve_membership_registered_but_different_native_parent_ignores_chain_evidence() -> None:
    """Chain evidence never overrides a native parent that is itself a
    different registered stream epic."""
    import time

    report = _fresh_report(time.time(), {"42": _native(10), "20": _native(10)})
    result = _chain(report, native_parent_epic=20)
    assert result["valid"] is False
    assert result["epic"] == 20
    assert "native parent epic that differs" in result["reason"]


@pytest.mark.parametrize(
    "native_parent_epic,registered_epics,expected",
    [
        (None, [10, 20], True),
        (30, [10, 20], True),
        (10, [10, 20], False),
        (20, [10, 20], False),
    ],
    ids=["no-parent", "unregistered-parent", "matching-parent", "registered-different-parent"],
)
def test_membership_needs_audit(native_parent_epic: int | None, registered_epics: list[int], expected: bool) -> None:
    assert task_lifecycle.membership_needs_audit(native_parent_epic, registered_epics) is expected


# --------------------------------------------------------------------------- #
# #6028 — evaluate()/reconcile() wire resolve_membership in for the primary
# issue and drift is caught fresh on every subsequent reconcile.
# --------------------------------------------------------------------------- #
def test_evaluate_accepts_unique_body_membership_and_records_provenance() -> None:
    import time

    ledger = _ready_evidence(_ledger())
    observation = _observation(_body())
    observation["github"]["issue"]["parent_epic"] = None
    now = time.time()
    observation["github"]["membership_audit"] = _fresh_report(
        now, {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}}
    )

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] != "BLOCKED_WITH_RECEIPT"
    assert result["membership"] == {
        "valid": True,
        "method": "body",
        "epic": 10,
        "generated_at": now,
        "digest": result["membership"]["digest"],
        "reason": None,
    }
    assert result["membership"]["digest"].startswith("sha256:")


def test_evaluate_rejects_body_membership_without_fresh_audit() -> None:
    ledger = _ready_evidence(_ledger())
    observation = _observation(_body())
    observation["github"]["issue"]["parent_epic"] = None
    observation["github"]["membership_audit"] = None

    result = task_lifecycle.evaluate(ledger, observation)

    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert "issue membership" in " ".join(result["hard_blockers"])
    assert result["membership"]["valid"] is False


def test_reconcile_persists_membership_provenance_in_the_receipt() -> None:
    import time

    ledger = _ready_evidence(_ledger())
    observation = _observation(_body())
    observation["github"]["issue"]["parent_epic"] = None
    now = time.time()
    observation["github"]["membership_audit"] = _fresh_report(
        now, {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True}}
    )

    _updated, receipt, _ = task_lifecycle.reconcile(ledger, observation, now=NOW)

    projection = receipt["observation"]["projection"]
    assert projection["membership"]["method"] == "body"
    assert projection["membership"]["epic"] == 10


def test_membership_drift_blocks_a_later_reconcile() -> None:
    """Membership accepted on one reconcile is NOT cached — a later
    reconcile with an observation that no longer proves membership (native
    parent gone, no fresh body audit) must fail closed, even though the
    ledger previously reconciled cleanly."""
    ledger = _ready_evidence(_ledger())
    first_observation = _observation(_body())
    ledger, first_receipt, _ = task_lifecycle.reconcile(ledger, first_observation, now=NOW)
    assert first_receipt["state"] != "BLOCKED_WITH_RECEIPT"

    drifted_observation = _observation(_body())
    drifted_observation["github"]["issue"]["parent_epic"] = None
    drifted_observation["github"]["membership_audit"] = None

    ledger, second_receipt, replayed = task_lifecycle.reconcile(ledger, drifted_observation, now="2026-07-16T11:00:00Z")

    assert replayed is False
    assert second_receipt["state"] == "BLOCKED_WITH_RECEIPT"
    assert "issue membership" in " ".join(second_receipt["hard_blockers"])
    assert ledger["current_state"] == "BLOCKED_WITH_RECEIPT"


@pytest.mark.parametrize("line", [
    "- [X] **AC-01b** — Output is current.",
    "- [X] AC-01b: Output is current.",
    "- [X] AC-01b Output is current.",
])
def test_observed_checkbox_forms_initialize_and_verify_snapshot(line):
    parsed = task_lifecycle.parse_issue_acceptance_criteria(line)
    assert parsed == [{"id": "AC-01b", "text": "Output is current.", "checked": True}]
    policy = {"AC-01b": {"due_state": "IMPLEMENTATION_READY", "required_evidence": ["test"]}}
    snapshot = task_lifecycle.build_ac_snapshot(line, policy, finalized_at=NOW)
    ledger = task_lifecycle.build_lifecycle(
        _identity(), author_family="codex", ac_snapshot=snapshot,
        required_checks=["CI Gate"], now=NOW, pr_number=77,
    )
    ledger = _add(ledger, "AC-01b", "test")
    equivalent = "- [ ] **AC-01b** — Output is current."
    result = task_lifecycle.evaluate(ledger, _observation(equivalent))
    assert not any("drift" in blocker or "stable-ID" in blocker for blocker in result["hard_blockers"])
    drift = task_lifecycle.evaluate(ledger, _observation(equivalent.replace("current", "stale")))
    assert any("drift" in blocker for blocker in drift["hard_blockers"])


@pytest.mark.parametrize("mark,checked", [(" ", False), ("x", True), ("X", True)])
@pytest.mark.parametrize("form", ["**{id}** — {text}", "{id}: {text}", "{id} {text}"])
def test_checkbox_forms_preserve_original_id_text_and_checked(mark, checked, form):
    body = "- [ ] CI Gate green\n- [" + mark + "] " + form.format(id="AC-01", text="Output is current.")
    assert task_lifecycle.parse_issue_acceptance_criteria(body) == [
        {"id": "AC-01", "text": "Output is current.", "checked": checked},
    ]


@pytest.mark.parametrize("line", [
    "- [ ] AC-01:", "- [ ] AC-01 : ", "- [ ] AC-01", "- [ ] **AC-01** — ",
    "- [ ] AC-01. Missing separator", "- [ ] **AC-01**: Unsupported bold separator",
    "- [ ] AC-: Missing identifier", "- [ ] AC-01/b Bad identifier",
    "- [ ] AC-lowercase: Unsupported identifier",
    "- [ ] AC-" + "1" * 30 + ": Too long", "- [y] AC-01: Bad checked state",
    "- [ ] **AC-01 — Missing closing emphasis", "* [ ] AC-01: Unsupported bullet",
])
def test_malformed_ac_like_checkbox_cannot_disappear_from_mixed_snapshot(line):
    body = "- [ ] **AC-OK** — Valid criterion.\n" + line
    with pytest.raises(task_lifecycle.LifecycleError, match="malformed AC-like"):
        task_lifecycle.parse_issue_acceptance_criteria(body)
    result = task_lifecycle.evaluate(_ledger(), _observation(_body() + line))
    assert any("malformed AC-like" in blocker for blocker in result["hard_blockers"])


@pytest.mark.parametrize("second", ["- [x] AC-01: Same criterion.", "- [ ] AC-01 Same criterion."])
def test_duplicate_ids_across_forms_refuse_snapshot(second):
    with pytest.raises(task_lifecycle.LifecycleError, match=r"duplicate acceptance criterion ID.*AC-01"):
        task_lifecycle.parse_issue_acceptance_criteria("- [ ] **AC-01** — Same criterion.\n" + second)


def test_criterion_length_limits_and_legacy_bold_ids():
    assert task_lifecycle.parse_issue_acceptance_criteria("- [ ] **LEGACY** - Existing criterion.")[0]["id"] == "LEGACY"
    with pytest.raises(task_lifecycle.LifecycleError, match="ID exceeds 32"):
        task_lifecycle.parse_issue_acceptance_criteria("- [ ] **AC-" + "1" * 30 + "b** — Too long.")
    with pytest.raises(task_lifecycle.LifecycleError, match="exceeds 4000"):
        task_lifecycle.parse_issue_acceptance_criteria("- [ ] AC-01: " + "x" * 4001)
    with pytest.raises(task_lifecycle.LifecycleError, match="no stable-ID"):
        task_lifecycle.parse_issue_acceptance_criteria("- [ ] CI Gate green")


# --------------------------------------------------------------------------- #
# #10055 — check_ac_checkbox shares the parser's one line grammar: bold and
# plain IDs check off identically, exact IDs only, and indentation, checked
# state, and the trailing newline survive byte-for-byte.
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("form", ["**{id}** — {text}", "{id}: {text}", "{id} {text}"])
@pytest.mark.parametrize("indent", ["", "  "])
def test_check_ac_checkbox_marks_every_parser_form(form, indent):
    line = indent + "- [ ] " + form.format(id="AC-01", text="Output is current.")
    body = "Some intro prose.\n" + line + "\n"
    updated = task_lifecycle.check_ac_checkbox(body, "AC-01")
    assert updated == "Some intro prose.\n" + line.replace("- [ ]", "- [x]") + "\n"
    assert task_lifecycle.parse_issue_acceptance_criteria(updated) == [
        {"id": "AC-01", "text": "Output is current.", "checked": True},
    ]


@pytest.mark.parametrize("form", ["**{id}** — {text}", "{id}: {text}", "{id} {text}"])
def test_check_ac_checkbox_matches_the_exact_id_only(form):
    body = "\n".join(
        [
            "- [ ] " + form.format(id="AC-1", text="First criterion."),
            "- [ ] " + form.format(id="AC-10", text="Tenth criterion."),
            "",
        ]
    )
    first_only = task_lifecycle.check_ac_checkbox(body, "AC-1").splitlines()
    assert first_only[0].startswith("- [x]")
    assert first_only[1].startswith("- [ ]")
    tenth_only = task_lifecycle.check_ac_checkbox(body, "AC-10").splitlines()
    assert tenth_only[0].startswith("- [ ]")
    assert tenth_only[1].startswith("- [x]")


@pytest.mark.parametrize("form", ["**{id}** — {text}", "{id}: {text}"])
def test_check_ac_checkbox_ignores_ids_mentioned_in_other_criteria(form):
    other = "- [ ] " + form.format(id="AC-02", text="Depends on **AC-01** and AC-01 being done.")
    body = "- [ ] **AC-01** — First criterion.\n" + other + "\n"
    updated = task_lifecycle.check_ac_checkbox(body, "AC-01")
    assert updated.splitlines() == ["- [x] **AC-01** — First criterion.", other]


@pytest.mark.parametrize("mark", ["x", "X"])
@pytest.mark.parametrize("form", ["**{id}** — {text}", "{id}: {text}", "{id} {text}"])
def test_check_ac_checkbox_leaves_checked_lines_byte_identical(mark, form):
    body = "- [" + mark + "] " + form.format(id="AC-01", text="Output is current.") + "\n"
    assert task_lifecycle.check_ac_checkbox(body, "AC-01") == body


def test_check_ac_checkbox_preserves_a_missing_trailing_newline():
    body = "- [ ] AC-01: Output is current."
    assert task_lifecycle.check_ac_checkbox(body, "AC-01") == "- [x] AC-01: Output is current."


def test_check_ac_checkbox_without_a_matching_line_returns_the_body():
    body = "- [ ] **AC-01** — Output is current.\n"
    assert task_lifecycle.check_ac_checkbox(body, "AC-99") == body
    assert task_lifecycle.check_ac_checkbox("", "AC-01") == ""


@pytest.mark.parametrize("ac_id", ["AC-01", "AC-01b", "AC-01c"])
@pytest.mark.parametrize("form", ["**{id}** — {text}", "{id}: {text}", "{id} {text}"])
def test_actual_closeout_init_accepts_equivalent_checkbox_forms(tmp_path, monkeypatch, ac_id, form):
    line = "- [X] " + form.format(id=ac_id, text="Output is current.")
    identity_path = tmp_path / "identity.json"
    policy_path = tmp_path / "policy.json"
    state_path = tmp_path / "lifecycle.json"
    identity_path.write_text(json.dumps(_identity()))
    policy_path.write_text(json.dumps({
        ac_id: {"due_state": "IMPLEMENTATION_READY", "required_evidence": ["test"]},
    }))
    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "read_issue", lambda self, repo, number: {
        "body": line, "parent_epic": 10, "parent_repository": "org/repo",
    })
    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "registered_stream_epics", lambda self, repository: [10])
    monkeypatch.setattr(task_closeout.GhGitHubAdapter, "read_issue_parent",
                        lambda self, repo, number: {"number": 10, "repository": repo})
    args = task_closeout.build_parser().parse_args([
        "--repo-root", str(tmp_path), "init", "--identity-file", str(identity_path),
        "--ac-policy", str(policy_path), "--state-file", str(state_path),
        "--author-family", "codex", "--required-check", "CI Gate", "--pr", "77", "--now", NOW,
    ])
    assert task_closeout.cmd_init(args) == 0
    ledger = task_lifecycle.load_lifecycle(state_path)
    assert task_lifecycle.parse_issue_acceptance_criteria(line) == [
        {"id": ac_id, "text": "Output is current.", "checked": True},
    ]
    assert ledger["ac_snapshot"]["criteria"][0]["id"] == ac_id
    assert ledger["ac_snapshot"]["criteria"][0]["text"] == "Output is current."
    snapshot = deepcopy(ledger["ac_snapshot"])
    args = task_closeout.build_parser().parse_args([
        "--repo-root", str(tmp_path), "add-evidence", "--state-file", str(state_path),
        "--ac-id", ac_id, "--type", "test", "--summary", "Caller regression passed.",
        "--commit", HEAD, "--now", NOW,
    ])
    assert task_closeout.cmd_evidence(args) == 0
    ledger = task_lifecycle.load_lifecycle(state_path)
    assert ledger["ac_snapshot"] == snapshot
    assert ledger["evidence"][0]["ac_id"] == ac_id
    assert task_closeout.cmd_evidence(args) == 0
    assert task_lifecycle.load_lifecycle(state_path) == ledger
    before_refusal = state_path.read_bytes()
    for unknown_id in ["AC-99b", "AC-01/b", ac_id.lower()]:
        args.ac_id = unknown_id
        with pytest.raises(task_lifecycle.LifecycleError, match="unknown acceptance criterion"):
            task_closeout.cmd_evidence(args)
        assert state_path.read_bytes() == before_refusal
    result = task_lifecycle.evaluate(ledger, _observation(f"- [ ] {ac_id} Output is current."))
    assert not any("drift" in blocker for blocker in result["hard_blockers"])
    assert result["valid_evidence"][ac_id] == ["test"]
    drift = task_lifecycle.evaluate(ledger, _observation(f"- [x] {ac_id}: Output changed."))
    assert any("drift" in blocker for blocker in drift["hard_blockers"])


@pytest.mark.parametrize("ac_id", ["AZ", "AC-01", "A" + "Z" * 31, "AC-" + "1" * 28 + "b", "AC-01bC"])
def test_schema_id_bounds_preserve_parser_snapshot_and_evidence(ac_id):
    body = f"- [ ] **{ac_id}** — Output is current."
    snapshot = task_lifecycle.build_ac_snapshot(
        body, {ac_id: {"due_state": "IMPLEMENTATION_READY", "required_evidence": ["test"]}},
        finalized_at=NOW,
    )
    ledger = task_lifecycle.build_lifecycle(
        _identity(), author_family="codex", ac_snapshot=snapshot,
        required_checks=["CI Gate"], now=NOW, pr_number=77,
    )
    updated = _add(ledger, ac_id, "test")
    assert updated["ac_snapshot"] == snapshot
    assert updated["ac_snapshot"]["criteria"][0]["id"] == ac_id
    assert updated["evidence"][0]["ac_id"] == ac_id


@pytest.mark.parametrize("ac_id", [
    "", "A", "A" + "Z" * 32, "AC-" + "1" * 29 + "b", "ac-01b", "1C-01b",
    "AC-lowercase", "AC-01b1", "AC-01_b", "AC-01/b", "AC-01b\n", "AC-01\u0431",
])
@pytest.mark.parametrize("target", ["criterion", "evidence"])
def test_schema_refuses_invalid_ids_in_snapshot_and_evidence(ac_id, target):
    ledger = _add(_ledger(), "AC-IMPL", "test")
    if target == "criterion":
        ledger["ac_snapshot"]["criteria"][0]["id"] = ac_id
        ledger["ac_snapshot"]["content_hash"] = task_lifecycle.ac_content_hash(ledger["ac_snapshot"]["criteria"])
        location = r"ac_snapshot.criteria.0.id"
    else:
        record = ledger["evidence"][0]
        record["ac_id"] = ac_id
        record["id"] = task_lifecycle.digest({key: value for key, value in record.items() if key != "id"})
        location = r"evidence.0.ac_id"
    with pytest.raises(task_lifecycle.LifecycleError, match=f"schema violation at {location}"):
        task_lifecycle.validate_lifecycle(ledger)


def test_schema_suffix_references_remain_bound_and_unique():
    snapshot = task_lifecycle.build_ac_snapshot(
        "- [ ] AC-01b: Output is current.",
        {"AC-01b": {"due_state": "IMPLEMENTATION_READY", "required_evidence": ["test"]}},
        finalized_at=NOW,
    )
    ledger = task_lifecycle.build_lifecycle(
        _identity(), author_family="codex", ac_snapshot=snapshot,
        required_checks=["CI Gate"], now=NOW, pr_number=77,
    )
    ledger = _add(ledger, "AC-01b", "test")
    unbound = deepcopy(ledger)
    record = unbound["evidence"][0]
    record["ac_id"] = "AC-01c"
    record["id"] = task_lifecycle.digest({key: value for key, value in record.items() if key != "id"})
    with pytest.raises(task_lifecycle.LifecycleError, match="evidence targets unknown AC: AC-01c"):
        task_lifecycle.validate_lifecycle(unbound)
    duplicate_criteria = deepcopy(ledger)
    duplicate_criteria["ac_snapshot"]["criteria"].append(deepcopy(snapshot["criteria"][0]))
    duplicate_criteria["ac_snapshot"]["content_hash"] = task_lifecycle.ac_content_hash(
        duplicate_criteria["ac_snapshot"]["criteria"],
    )
    with pytest.raises(task_lifecycle.LifecycleError, match="duplicate stable IDs"):
        task_lifecycle.validate_lifecycle(duplicate_criteria)
    duplicate_evidence = deepcopy(ledger)
    duplicate_evidence["evidence"].append(deepcopy(ledger["evidence"][0]))
    with pytest.raises(task_lifecycle.LifecycleError, match="duplicate evidence record"):
        task_lifecycle.validate_lifecycle(duplicate_evidence)


@pytest.mark.parametrize("parent_number", [10, 20, 30])
@pytest.mark.parametrize("parent_repository", ["foreign/repo", None, [], "malformed"])
def test_9794_repository_refusal_precedes_every_native_membership_branch(parent_number, parent_repository):
    report = _fresh_report(time.time(), {"42": _native(10), "30": _native(10)})
    result = task_lifecycle.resolve_membership(
        issue_number=42, stream_epic=10, native_parent_epic=parent_number,
        repository="org/repo", native_parent_repository=parent_repository,
        registered_epics=[10, 20], membership_report=report,
    )
    assert result["valid"] is False
    assert "repository" in result["reason"]
    assert result["method"] is None


def test_9794_parent_repository_compare_is_case_insensitive():
    result = task_lifecycle.resolve_membership(
        issue_number=42, stream_epic=10, native_parent_epic=10,
        repository="org/repo", native_parent_repository="ORG/Repo",
        registered_epics=[10], membership_report=None,
    )
    assert result["valid"] is True


@pytest.mark.parametrize("parents,valid,reason,read_count", [
    ({42: (10, "ORG/Repo")}, True, None, 1),
    ({42: (10, "foreign/repo")}, False, "repository boundary", 1),
    ({42: (30, "org/repo"), 30: (40, "foreign/repo"), 40: (10, "org/repo")}, False, "repository boundary", 2),
    ({42: (31, "org/repo"), 31: (20, "org/repo")}, False, "different registered", 2),
    ({42: (30, "org/repo"), 30: (31, "org/repo"), 31: (20, "org/repo")}, False, "different registered", 3),
    ({42: (32, "org/repo"), 32: (10, "org/repo")}, True, None, 2),
    ({42: None}, False, "missing", 1),
    ({42: (30, "org/repo"), 30: (42, "org/repo")}, False, "cyclic", 2),
    ({n: (n + 1, "org/repo") for n in range(42, 51)}, False, "maximum sub-issue depth", 8),
    ({**{n: (n + 1, "org/repo") for n in range(42, 49)}, 49: (10, "org/repo")}, True, None, 8),
    ({42: (True, "org/repo")}, False, "number is malformed", 1),
    ({42: (10, None)}, False, "identity is malformed", 1),
], ids=["casefold", "foreign-number-collision", "returning-local-descendant",
        "intermediate-reparent", "unchanged-parent-ancestor-reparent", "same-epic-sibling",
        "missing", "cycle", "over-depth", "eight-reads-accepted", "boolean-number", "unqualified"])
def test_9794_live_ancestry(parents, valid, reason, read_count):
    reads = []

    def read_parent(repository, number):
        assert repository == "org/repo"
        reads.append(number)
        parent = parents[number]
        return None if parent is None else {"number": parent[0], "repository": parent[1]}

    result = task_lifecycle.resolve_live_ancestry(
        repository="org/repo", issue_number=42, stream_epic=10,
        registered_epics=[10, 20], read_parent=read_parent,
    )
    assert result["valid"] is valid
    assert len(reads) == read_count
    if reason:
        assert reason in result["reason"]
    else:
        assert result["epic"] == 10


@pytest.mark.parametrize("error", [task_lifecycle.LifecycleError("unread"), OSError("unread"), ValueError("bad JSON")])
def test_9794_live_unread_ancestry_returns_typed_refusal(error):
    def unread(repository, number):
        raise error

    result = task_lifecycle.resolve_live_ancestry(
        repository="org/repo", issue_number=42, stream_epic=10,
        registered_epics=[10], read_parent=unread,
    )
    assert result["valid"] is False
    assert "could not be read" in result["reason"]


@pytest.mark.parametrize("repository,epics,reason", [(None, [10], "malformed"), ("org/repo", None, "absent"), ("org/repo", [20], "absent")])
def test_9794_live_ancestry_requires_typed_repository_and_registry(repository, epics, reason):
    def unexpected(*args):
        pytest.fail("invalid identity must refuse before reading")

    result = task_lifecycle.resolve_live_ancestry(
        repository=repository, issue_number=42, stream_epic=10,
        registered_epics=epics, read_parent=unexpected,
    )
    assert result["valid"] is False
    assert reason in result["reason"]


def _9794_body_report():
    return {
        "repository": "org/repo",
        "generated_at": time.time(), "membership_complete": True,
        "incomplete_nodes": [], "warnings": [],
        "effective_membership": {
            "42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": True},
        },
    }


@pytest.mark.parametrize(
    "evidence_repository,valid,reason",
    [
        ("other/repo", False, "does not match"),
        (None, False, "missing or malformed"),
        ("", False, "missing or malformed"),
        ("repo", False, "missing or malformed"),
        (42, False, "missing or malformed"),
        ("ORG/Repo", True, None),
        ("org/repo", True, None),
    ],
)
def test_9852_body_evidence_requires_identity_repository(evidence_repository, valid, reason):
    report = _9794_body_report()
    if evidence_repository is not None:
        report["repository"] = evidence_repository
    else:
        report.pop("repository")
    result = task_lifecycle.resolve_live_ancestry(
        repository="org/repo", issue_number=42, stream_epic=10,
        registered_epics=[10], read_parent=lambda repo, number: None,
        membership_report=report,
    )
    assert result["valid"] is valid
    if valid:
        assert result["method"] == "body"
    else:
        assert reason in result["reason"]
        assert result["method"] is None


def test_9852_repository_evidence_refuses_malformed_task_identity():
    assert task_lifecycle.repository_evidence_refusal(
        "repo", "org/repo", source="audit"
    ) == "task repository identity is malformed"


@pytest.mark.parametrize("native_parent_epic", [None, 30], ids=["body", "native-chain"])
@pytest.mark.parametrize(
    "evidence_repository,valid,reason",
    [
        ("other/repo", False, "does not match"),
        (None, False, "missing or malformed"),
        ("", False, "missing or malformed"),
        ("repo", False, "missing or malformed"),
        (42, False, "missing or malformed"),
        ([], False, "missing or malformed"),
        (" org/repo", False, "missing or malformed"),
        ("ORG/Repo", True, None),
        ("org/repo", True, None),
    ],
)
def test_9866_read_only_audit_requires_identity_repository(native_parent_epic, evidence_repository, valid, reason):
    report = _9794_body_report()
    if native_parent_epic is not None:
        report["effective_membership"]["42"]["via"] = "native"
        report["effective_membership"]["30"] = {
            "epics": [10], "streams": ["infra"], "via": "native", "unique_stream": True,
        }
    if evidence_repository is None:
        report.pop("repository")
    else:
        report["repository"] = evidence_repository
    result = task_lifecycle.resolve_membership(
        repository="org/repo", issue_number=42, stream_epic=10,
        native_parent_epic=native_parent_epic, native_parent_repository="org/repo",
        registered_epics=[10], membership_report=report,
    )
    assert result["valid"] is valid
    if valid:
        assert result["method"] == ("body" if native_parent_epic is None else "native_chain")
        assert result["generated_at"] == report["generated_at"]
        assert result["digest"] == task_lifecycle.digest(report["effective_membership"])
    else:
        assert reason in result["reason"]
        assert result["method"] is None
        assert result["epic"] is None


def test_9866_evaluate_refuses_foreign_audit():
    observation = _observation(_body())
    observation["github"]["issue"]["parent_epic"] = None
    observation["github"]["membership_audit"] = {**_9794_body_report(), "repository": "other/repo"}
    result = task_lifecycle.evaluate(_ready_evidence(_ledger()), observation)
    assert result["state"] == "BLOCKED_WITH_RECEIPT"
    assert result["membership"]["valid"] is False
    assert "membership audit repository does not match the task identity" in " ".join(result["hard_blockers"])


def test_9794_live_null_target_accepts_exact_body_evidence():
    report = _9794_body_report()
    reads = []

    def read_parent(repository, number):
        reads.append((repository, number))
        return None  # Successful repository-qualified read returned parent: null.

    result = task_lifecycle.resolve_live_ancestry(
        repository="org/repo", issue_number=42, stream_epic=10,
        registered_epics=[10, 20], read_parent=read_parent, membership_report=report,
    )
    assert reads == [("org/repo", 42)]
    assert result == {
        "valid": True, "method": "body", "epic": 10,
        "generated_at": report["generated_at"],
        "digest": task_lifecycle.digest(report["effective_membership"]), "reason": None,
    }


@pytest.mark.parametrize("patch", [
    {"membership_complete": False},
    {"incomplete_nodes": [20]},
    {"warnings": [{"code": "traversal_incomplete", "issue": 20}]},
    {"warnings": [{"code": "truncated_depth", "frontier": [20]}]},
    {"warnings": [{"code": "unresolved_subissue", "issue": 20}]},
    {"warnings": [{"code": "unresolved_subissue"}]},
    {"generated_at": 0}, {"generated_at": "unread"},
    {"effective_membership": {}},
    {"effective_membership": {"42": {"epics": [20], "streams": ["infra"], "via": "body", "unique_stream": True}}},
    {"effective_membership": {"42": {"epics": [10, 20], "streams": ["infra", "other"], "via": "body", "unique_stream": False}}},
    {"effective_membership": {"42": {"epics": [10, 20], "streams": ["infra"], "via": "body", "unique_stream": False}}},
    {"effective_membership": {"42": {"epics": [10], "streams": ["infra"], "via": "native", "unique_stream": True}}},
    {"effective_membership": {"42": {"epics": [10], "streams": ["infra"], "via": [], "unique_stream": True}}},
    {"effective_membership": {"42": {"epics": [10], "streams": ["infra"], "via": {}, "unique_stream": True}}},
    {"effective_membership": {"42": {"epics": [10], "streams": ["infra"], "via": "body", "unique_stream": 1}}},
], ids=["failed", "incomplete-nodes", "timeout", "depth", "unresolved-root", "untyped-unresolved",
        "stale", "malformed-time", "missing-target", "wrong-epic", "two-streams", "two-epics-one-stream",
        "native-evidence", "list-via", "dict-via", "untyped-unique"])
def test_9794_live_body_refuses_incomplete_or_inexact_evidence(patch):
    report = {**_9794_body_report(), **patch}
    result = task_lifecycle.resolve_live_ancestry(
        repository="org/repo", issue_number=42, stream_epic=10,
        registered_epics=[10, 20], read_parent=lambda repo, number: None,
        membership_report=report,
    )
    assert result["valid"] is False
    assert result["method"] is None
    assert result["reason"]


@pytest.mark.parametrize("parents,reason", [
    ({42: (30, "org/repo"), 30: None}, "missing"),
    ({42: (10, "foreign/repo")}, "repository boundary"),
    ({42: (20, "org/repo")}, "different registered"),
    ({42: (10, None)}, "identity is malformed"),
])
def test_9794_body_evidence_never_overrides_native_refusal(parents, reason):
    def read_parent(repository, number):
        parent = parents[number]
        return None if parent is None else {"number": parent[0], "repository": parent[1]}

    result = task_lifecycle.resolve_live_ancestry(
        repository="org/repo", issue_number=42, stream_epic=10,
        registered_epics=[10, 20], read_parent=read_parent, membership_report=_9794_body_report(),
    )
    assert result["valid"] is False
    assert reason in result["reason"]


@pytest.mark.parametrize("error", [
    task_lifecycle.LifecycleError("partial or malformed identity"),
    subprocess.TimeoutExpired("parent", 1),
])
def test_9794_unread_target_cannot_use_valid_body_evidence(error):
    def unread(repository, number):
        raise error

    result = task_lifecycle.resolve_live_ancestry(
        repository="org/repo", issue_number=42, stream_epic=10,
        registered_epics=[10, 20], read_parent=unread, membership_report=_9794_body_report(),
    )
    assert result["valid"] is False
    assert "could not be read" in result["reason"]


def test_9794_native_precedence_does_not_consult_body_audit():
    result = task_lifecycle.resolve_live_ancestry(
        repository="org/repo", issue_number=42, stream_epic=10,
        registered_epics=[10, 20], read_parent=lambda repo, number: {"number": 10, "repository": repo},
        membership_report={"membership_complete": False},
    )
    assert result["valid"] is True
    assert result["method"] == "native_chain"


def test_9794_resolved_root_allows_unresolved_descendant_reporting():
    report = _9794_body_report()
    report["warnings"] = [{"code": "unresolved_subissue", "issue": 30}]
    result = task_lifecycle.resolve_live_ancestry(
        repository="org/repo", issue_number=42, stream_epic=10,
        registered_epics=[10, 20], read_parent=lambda repo, number: None, membership_report=report,
    )
    assert result["valid"] is True
    assert result["method"] == "body"

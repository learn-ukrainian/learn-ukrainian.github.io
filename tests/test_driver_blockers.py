"""Deterministic snapshots and exact posted receipts, with no live Fleet writes."""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import driver_blockers as blockers
from scripts import driver_state

REPO = Path(__file__).resolve().parents[1]
EPIC = "infra"


def item(key="blocked-build", **fields):
    return {"id": key, "state": "blocked", "owner": "monitor", "waits_on": "review", "action": "get approval", **fields}


def observation(*items, complete=True):
    return {"epic": EPIC, "complete": complete, "items": list(items)}


def receipt(body, *, key="message-1", stamp="2026-10-10T01:00:00Z", **fields):
    return {
        "recipient": "cto",
        "message_id": key,
        "created_at": stamp,
        "content_sha256": hashlib.sha256(body).hexdigest(),
        **fields,
    }


def posted(*items):
    return "\n".join(" | ".join(i.values()) for i in items).encode("utf-8")


def seed(path, current=None):
    current = current or observation(item())
    body = posted(*current["items"])
    return blockers.record(path, EPIC, current, receipt(body), body, 0)


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    state = tmp_path / ".claude/infra-epic/DRIVER-STATE.md"
    state.parent.mkdir(parents=True)
    monkeypatch.setenv("SESSION_EPIC", EPIC)
    monkeypatch.setenv(driver_state.STATE_ENV, str(state))
    return state.parent / blockers.LEDGER_NAME


def run_cli(ledger, *args):
    environment = {**os.environ, "SESSION_EPIC": EPIC, driver_state.STATE_ENV: str(ledger.parent / "DRIVER-STATE.md")}
    return subprocess.run(
        [sys.executable, "-m", "scripts.driver_blockers", *args],
        cwd=REPO,
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
    )


def record_files(tmp_path, current, body, received=None):
    paths = [tmp_path / "current.json", tmp_path / "receipt.json", tmp_path / "posted.md"]
    paths[0].write_text(json.dumps(current))
    paths[1].write_text(json.dumps(received or receipt(body, key="message-2", stamp="2026-10-10T02:00:00Z")))
    paths[2].write_bytes(body)
    return paths


def record_args(paths, generation="1"):
    current, received, body = paths
    return [
        "record",
        "--epic",
        EPIC,
        "--current",
        str(current),
        "--receipt",
        str(received),
        "--body-file",
        str(body),
        "--expect-generation",
        generation,
    ]


def test_held_out_mixed_post_set_and_reappearance(ledger):
    stable = item("stable")
    changed = item("changed", action="wait for CI")
    resolved = item("resolved")
    baseline = seed(ledger, observation(stable, changed, resolved))
    updated = {**changed, "action": "repair CI"}
    new = item("new")
    current = observation(stable, updated, new)
    delta = blockers.compute_delta(current, baseline)
    assert {i["id"]: i["class"] for i in delta["items"]} == {
        "stable": "UNCHANGED",
        "changed": "CHANGED",
        "new": "NEW",
        "resolved": "RESOLVED",
    }
    assert {i["id"] for i in delta["items"] if i["class"] != "UNCHANGED"} == {"changed", "new", "resolved"}
    body = posted(updated, new) + b"\nRESOLVED resolved"
    baseline = blockers.record(
        ledger, EPIC, current, receipt(body, key="message-2", stamp="2026-10-10T02:00:00Z"), body, 1
    )
    assert baseline["generation"] == 2
    assert "resolved" not in baseline["items"]
    assert blockers.compute_delta(current, baseline)["post_required"] is False
    recurrence = blockers.compute_delta(observation(stable, updated, new, resolved), baseline)
    assert recurrence["items"][-1]["class"] == "NEW"


@pytest.mark.parametrize("field", ["state", "owner", "waits_on", "action"])
def test_each_semantic_field_changes_fingerprint(ledger, field):
    baseline = seed(ledger)
    delta = blockers.compute_delta(observation(item(**{field: "different"})), baseline)
    assert delta["items"][0]["class"] == "CHANGED"
    assert delta["post_required"] is True


def test_fingerprint_sorted_utf8_without_unicode_normalization():
    value = item(owner="é")
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    assert blockers.fingerprint(value) == hashlib.sha256(raw).hexdigest()
    assert blockers.fingerprint(dict(reversed(list(value.items())))) == blockers.fingerprint(value)
    assert blockers.fingerprint(item(owner="e\u0301")) != blockers.fingerprint(value)


@pytest.mark.parametrize("complete", [False, True])
def test_unknown_empty_snapshot_never_authorizes_silence(complete):
    delta = blockers.compute_delta(observation(complete=complete))
    assert delta == {"epic": EPIC, "baseline": "unknown", "generation": 0, "items": [], "post_required": True}


@pytest.mark.parametrize("empty", [False, True])
def test_partial_snapshot_cannot_resolve_or_suppress(ledger, empty):
    baseline = seed(ledger)
    current = observation(complete=False) if empty else observation(item(), complete=False)
    delta = blockers.compute_delta(current, baseline)
    assert delta["baseline"] == "unknown"
    assert delta["generation"] == 1
    assert delta["post_required"] is True
    assert all(i["class"] == "NEW" for i in delta["items"])


def test_complete_empty_snapshot_resolves_then_becomes_silent(ledger):
    baseline = seed(ledger)
    delta = blockers.compute_delta(observation(), baseline)
    assert delta["items"] == [{"id": "blocked-build", "class": "RESOLVED"}]
    body = b"RESOLVED blocked-build"
    baseline = blockers.record(
        ledger, EPIC, observation(), receipt(body, key="message-2", stamp="2026-10-10T02:00:00Z"), body, 1
    )
    assert blockers.compute_delta(observation(), baseline)["post_required"] is False


@pytest.mark.parametrize(
    "corruption",
    [
        "absent",
        "malformed",
        "wrong_epic",
        "anchor_hash",
        "anchor_time",
        "anchor_missing",
        "anchor_extra",
        "generation",
        "map",
        "extra",
        "oversized",
    ],
)
def test_invalid_ledger_is_unknown(ledger, corruption):
    stored = seed(ledger)
    if corruption == "absent":
        ledger.unlink()
    elif corruption == "malformed":
        ledger.write_text("{")
    elif corruption == "oversized":
        ledger.write_bytes(b" " * (blockers.MAX_INPUT_BYTES + 1))
    else:
        if corruption == "wrong_epic":
            stored["epic"] = "atlas"
        elif corruption == "anchor_hash":
            stored["anchor"]["content_sha256"] = "bad"
        elif corruption == "anchor_time":
            stored["anchor"]["created_at"] = "2026-10-10"
        elif corruption == "anchor_missing":
            stored["anchor"].pop("message_id")
        elif corruption == "anchor_extra":
            stored["anchor"]["recipient"] = "other"
        elif corruption == "generation":
            stored["generation"] = 0
        elif corruption == "map":
            stored["items"]["blocked-build"] = "not a fingerprint"
        else:
            stored["unexpected"] = True
        ledger.write_text(json.dumps(stored))
    delta = blockers.compute_delta(observation(item()), blockers.load_ledger(ledger, EPIC))
    assert delta["baseline"] == "unknown"
    assert delta["items"][0]["class"] == "NEW"
    assert delta["post_required"] is True


@pytest.mark.parametrize(
    "current",
    [
        observation(item(id="")),
        observation(item(id="  ")),
        observation(item(), item()),
        observation(item(owner="")),
        observation(item(action=7)),
        observation(item(extra="unknown")),
        {**observation(item()), "probe": "output"},
        {**observation(item()), "complete": 1},
        {**observation(item()), "epic": "atlas"},
        {"epic": EPIC, "complete": True},
        [],
    ],
)
def test_invalid_observation_cli_prints_no_classes(ledger, tmp_path, current):
    path = tmp_path / "observation.json"
    path.write_text(json.dumps(current))
    result = run_cli(ledger, "delta", "--epic", EPIC, "--current", str(path))
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.startswith("driver_blockers:")
    assert not ledger.exists()


@pytest.mark.parametrize(
    "content",
    [
        b"{",
        b"\xff",
        b" " * (blockers.MAX_INPUT_BYTES + 1),
        b'{"epic":"infra","epic":"infra","complete":true,"items":[]}',
    ],
    ids=["malformed", "invalid-utf8", "oversized", "duplicate-json-keys"],
)
def test_unreadable_malformed_duplicate_json_and_oversized(ledger, tmp_path, content):
    path = tmp_path / "current.json"
    path.write_bytes(content)
    result = run_cli(ledger, "delta", "--epic", EPIC, "--current", str(path))
    assert result.returncode == 1
    assert result.stdout == ""
    path.unlink()
    result = run_cli(ledger, "delta", "--epic", EPIC, "--current", str(path))
    assert result.returncode == 1
    assert result.stdout == ""


@pytest.mark.parametrize(
    "failure",
    [
        "recipient",
        "missing_id",
        "time",
        "naive_time",
        "hash",
        "reused_id",
        "earlier",
        "equal_time",
        "missing_item",
        "missing_field",
        "partial",
        "stale",
    ],
)
def test_rejected_record_preserves_bytes_and_resurfaces(ledger, tmp_path, failure):
    seed(ledger)
    before = ledger.read_bytes()
    current = observation(item(action="repair CI"))
    body = posted(*current["items"])
    received = receipt(body, key="message-2", stamp="2026-10-10T02:00:00Z")
    generation = "1"
    if failure == "recipient":
        received["recipient"] = "operator"
    elif failure == "missing_id":
        received.pop("message_id")
    elif failure in {"time", "naive_time"}:
        received["created_at"] = "invalid" if failure == "time" else "2026-10-10T02:00:00"
    elif failure == "hash":
        received["content_sha256"] = "0" * 64
    elif failure == "reused_id":
        received["message_id"] = "message-1"
    elif failure in {"earlier", "equal_time"}:
        received["created_at"] = "2026-10-10T00:59:00Z" if failure == "earlier" else "2026-10-10T03:00:00+02:00"
    elif failure in {"missing_item", "missing_field"}:
        body = b"different blocker" if failure == "missing_item" else b"blocked-build"
        received["content_sha256"] = hashlib.sha256(body).hexdigest()
    elif failure == "partial":
        current["complete"] = False
    else:
        generation = "0"
    paths = record_files(tmp_path, current, body, received)
    result = run_cli(ledger, *record_args(paths, generation))
    assert result.returncode == 1
    assert result.stdout == ""
    assert ledger.read_bytes() == before
    assert (
        blockers.compute_delta(observation(item(action="repair CI")), blockers.load_ledger(ledger, EPIC))["items"][0][
            "class"
        ]
        == "CHANGED"
    )


@pytest.mark.parametrize("flag", ["--epic", "--current", "--receipt", "--body-file", "--expect-generation"])
def test_record_requires_every_flag(ledger, tmp_path, flag):
    seed(ledger)
    before = ledger.read_bytes()
    paths = record_files(tmp_path, observation(item()), posted(item()))
    args = record_args(paths)
    index = args.index(flag)
    del args[index : index + 2]
    result = run_cli(ledger, *args)
    assert result.returncode == 2
    assert result.stdout == ""
    assert ledger.read_bytes() == before


def test_record_requires_resolved_id_in_exact_body(ledger):
    seed(ledger)
    before = ledger.read_bytes()
    body = b"all clear"
    with pytest.raises(ValueError, match="RESOLVED"):
        blockers.record(
            ledger, EPIC, observation(), receipt(body, key="message-2", stamp="2026-10-10T02:00:00Z"), body, 1
        )
    assert ledger.read_bytes() == before


def test_record_rejects_partial_substring_token_matches(ledger):
    seed(ledger, observation(item("resolved")))
    before = ledger.read_bytes()
    # 1. "resolved" (RESOLVED) item id embedded in word "unresolved"
    body1 = b"Status is unresolved at this time"
    with pytest.raises(ValueError, match="posted body omits RESOLVED item id 'resolved' verbatim"):
        blockers.record(
            ledger,
            EPIC,
            observation(),
            receipt(body1, key="message-2", stamp="2026-10-10T02:00:00Z"),
            body1,
            1,
        )
    # 2. "ci" (NEW) item id embedded in word "ci-repair"
    body2 = b"blocked by ci-repair task | blocked | monitor | review | get approval\nRESOLVED resolved"
    with pytest.raises(ValueError, match="posted body omits NEW item id 'ci' verbatim"):
        blockers.record(
            ledger,
            EPIC,
            observation(item("ci")),
            receipt(body2, key="message-3", stamp="2026-10-10T03:00:00Z"),
            body2,
            1,
        )
    # 3. "blocked" (state) embedded in "blocked-build" without standalone token
    body3 = b"blocked-build | monitor | review | get approval\nRESOLVED resolved"
    with pytest.raises(
        ValueError, match="posted body omits required fields for NEW item 'blocked-build' on the same line"
    ):
        blockers.record(
            ledger,
            EPIC,
            observation(item("blocked-build")),
            receipt(body3, key="message-4", stamp="2026-10-10T04:00:00Z"),
            body3,
            1,
        )
    # 4. "open" embedded in "reopened"
    q_item = item("queue-lag", state="open", owner="ci", waits_on="none", action="fix")
    body4 = b"queue-lag | reopened | ci | none | fix\nRESOLVED resolved"
    with pytest.raises(ValueError, match="posted body omits required fields for NEW item 'queue-lag' on the same line"):
        blockers.record(
            ledger,
            EPIC,
            observation(q_item),
            receipt(body4, key="message-5", stamp="2026-10-10T05:00:00Z"),
            body4,
            1,
        )
    # 5. "ci" embedded in "recipient"
    body5 = b"queue-lag | open | recipient | none | fix\nRESOLVED resolved"
    with pytest.raises(ValueError, match="posted body omits required fields for NEW item 'queue-lag' on the same line"):
        blockers.record(
            ledger,
            EPIC,
            observation(q_item),
            receipt(body5, key="message-6", stamp="2026-10-10T06:00:00Z"),
            body5,
            1,
        )
    # 6. "fix" embedded in "prefix"
    body6 = b"queue-lag | open | ci | none | prefix\nRESOLVED resolved"
    with pytest.raises(ValueError, match="posted body omits required fields for NEW item 'queue-lag' on the same line"):
        blockers.record(
            ledger,
            EPIC,
            observation(q_item),
            receipt(body6, key="message-7", stamp="2026-10-10T07:00:00Z"),
            body6,
            1,
        )
    # 7. Fields scattered across paragraphs / separate lines
    body7 = (
        b"queue-lag was discussed with the recipient.\n"
        b"The service was reopened.\n"
        b"There are none left in the prefix queue.\n"
        b"RESOLVED resolved"
    )
    with pytest.raises(ValueError, match="posted body omits required fields for NEW item 'queue-lag' on the same line"):
        blockers.record(
            ledger,
            EPIC,
            observation(q_item),
            receipt(body7, key="message-8", stamp="2026-10-10T08:00:00Z"),
            body7,
            1,
        )
    assert ledger.read_bytes() == before


def test_resolved_id_requires_same_line_resolution_marker(ledger):
    cache = item("cache-warm")
    api = item("api-latency", waits_on="cache-warm")
    seed(ledger, observation(cache, api))
    before = ledger.read_bytes()

    # 1. cache-warm is RESOLVED, but appears only inside another item's field (no marker word)
    body_missing_marker = b"api-latency | blocked | monitor | cache-warm | repair CI"
    with pytest.raises(
        ValueError,
        match="posted body omits exact token RESOLVED cache-warm on its own non-active line",
    ):
        blockers.record(
            ledger,
            EPIC,
            observation(api),
            receipt(body_missing_marker, key="message-2", stamp="2026-10-10T02:00:00Z"),
            body_missing_marker,
            1,
        )
    assert ledger.read_bytes() == before

    # 2. cache-warm appears on an active observation line containing marker words (closed / done)
    body_active_line_marker = b"api-latency | closed | monitor | cache-warm | done"
    with pytest.raises(
        ValueError,
        match="posted body omits exact token RESOLVED cache-warm on its own non-active line",
    ):
        blockers.record(
            ledger,
            EPIC,
            observation(api),
            receipt(body_active_line_marker, key="message-3", stamp="2026-10-10T03:00:00Z"),
            body_active_line_marker,
            1,
        )
    assert ledger.read_bytes() == before

    # 3. cache-warm with non-standalone marker word (closed-pr)
    body_closed_pr = b"api-latency | blocked | monitor | cache-warm | repair CI\ncache-warm closed-pr"
    with pytest.raises(
        ValueError,
        match="posted body omits exact token RESOLVED cache-warm on its own non-active line",
    ):
        blockers.record(
            ledger,
            EPIC,
            observation(api),
            receipt(body_closed_pr, key="message-4", stamp="2026-10-10T04:00:00Z"),
            body_closed_pr,
            1,
        )
    assert ledger.read_bytes() == before

    # 4. cache-warm with hyphenated negation (not-resolved)
    body_not_resolved = b"api-latency | blocked | monitor | cache-warm | repair CI\ncache-warm not-resolved"
    with pytest.raises(
        ValueError,
        match="posted body omits exact token RESOLVED cache-warm on its own non-active line",
    ):
        blockers.record(
            ledger,
            EPIC,
            observation(api),
            receipt(body_not_resolved, key="message-5", stamp="2026-10-10T05:00:00Z"),
            body_not_resolved,
            1,
        )
    assert ledger.read_bytes() == before

    # 5. cache-warm with explicit negation (is not resolved)
    body_is_not_resolved = b"api-latency | blocked | monitor | cache-warm | repair CI\ncache-warm is not resolved"
    with pytest.raises(
        ValueError,
        match="posted body omits exact token RESOLVED cache-warm on its own non-active line",
    ):
        blockers.record(
            ledger,
            EPIC,
            observation(api),
            receipt(body_is_not_resolved, key="message-6", stamp="2026-10-10T06:00:00Z"),
            body_is_not_resolved,
            1,
        )
    assert ledger.read_bytes() == before

    # The review's prose can never establish an explicit resolution.
    for prose in (b"cache-warm is not yet resolved", b"cache-warm is not resolved. Follow-up closed"):
        body = posted(api) + b"\n" + prose
        with pytest.raises(ValueError, match="RESOLVED"):
            blockers.record(
                ledger,
                EPIC,
                observation(api),
                receipt(body, key="message-7", stamp="2026-10-10T07:00:00Z"),
                body,
                1,
            )
        assert ledger.read_bytes() == before

    # 6. cache-warm accompanied by explicit same-line resolution marker
    body_with_marker = b"api-latency | blocked | monitor | cache-warm | repair CI\nRESOLVED cache-warm"
    updated = blockers.record(
        ledger,
        EPIC,
        observation(api),
        receipt(body_with_marker, key="message-7", stamp="2026-10-10T07:00:00Z"),
        body_with_marker,
        1,
    )
    assert "cache-warm" not in updated["items"]
    assert updated["generation"] == 2


@pytest.mark.parametrize(
    "prose",
    [
        "cache-warm is not yet resolved",
        "cache-warm is not resolved. Follow-up closed",
        "cache-warm resolved",
        "cache-warm cleared",
        "cache-warm fixed",
        "cache-warm closed",
        "cache-warm done",
        "cache-warm unblocked",
        "resolved cache-warm",
        "Not RESOLVED cache-warm",
        "RESOLVED cache-warm later",
        "RESOLVED cache-warm | blocked | monitor | review | get approval",
    ],
)
def test_resolution_requires_exact_standalone_token(ledger, prose):
    seed(ledger, observation(item("cache-warm")))
    before = ledger.read_bytes()
    body = prose.encode()
    with pytest.raises(ValueError, match="RESOLVED"):
        blockers.record(
            ledger, EPIC, observation(), receipt(body, key="message-2", stamp="2026-10-10T02:00:00Z"), body, 1
        )
    assert ledger.read_bytes() == before


def test_standalone_resolution_is_independent_of_other_item_ids(ledger):
    active = item("RESOLVED")
    seed(ledger, observation(active, item("cache-warm")))
    body = b"RESOLVED cache-warm"
    stored = blockers.record(
        ledger, EPIC, observation(active), receipt(body, key="message-2", stamp="2026-10-10T02:00:00Z"), body, 1
    )
    assert stored["items"] == {"RESOLVED": blockers.fingerprint(active)}


@pytest.mark.parametrize("linked", ["ledger", "lock", "parent"])
def test_delta_refuses_symlinked_state(ledger, tmp_path, linked):
    seed(ledger)
    before = ledger.read_bytes()
    paths = record_files(tmp_path, observation(item()), posted(item()))
    if linked == "parent":
        moved = ledger.parent.with_name("moved-epic")
        ledger.parent.rename(moved)
        ledger.parent.symlink_to(moved, target_is_directory=True)
    else:
        target = tmp_path / "linked-target"
        target.write_bytes(before if linked == "ledger" else b"")
        link = ledger if linked == "ledger" else ledger.with_name(f"{ledger.name}.lock")
        link.unlink()
        link.symlink_to(target)
    result = run_cli(ledger, "delta", "--epic", EPIC, "--current", str(paths[0]))
    assert result.returncode != 0, result.stdout
    assert result.stdout == ""
    assert "driver_blockers:" in result.stderr
    assert ledger.read_bytes() == before


@pytest.mark.parametrize("replacement", ["symlink", "directory"])
def test_record_refuses_parent_swap_after_generation_read(ledger, tmp_path, monkeypatch, replacement):
    from scripts.common.safe_unit_install import InstallError

    seed(ledger)
    before = ledger.read_bytes()
    moved = ledger.parent.with_name("moved-epic")
    decoy = tmp_path / "decoy-epic"
    decoy.mkdir()
    (decoy / ledger.name).write_bytes(before)
    original = blockers.compute_delta

    def swap(observed, stored=None):
        result = original(observed, stored)
        ledger.parent.rename(moved)
        if replacement == "symlink":
            ledger.parent.symlink_to(decoy, target_is_directory=True)
        else:
            ledger.parent.mkdir()
            (ledger.parent / ledger.name).write_bytes(before)
        return result

    monkeypatch.setattr(blockers, "compute_delta", swap)
    changed = item(action="repair CI")
    body = posted(changed)
    with pytest.raises((ValueError, OSError, InstallError)):
        blockers.record(
            ledger, EPIC, observation(changed), receipt(body, key="message-2", stamp="2026-10-10T02:00:00Z"), body, 1
        )
    assert (moved / ledger.name).read_bytes() == before
    assert ledger.read_bytes() == before
    assert (decoy / ledger.name).read_bytes() == before


def test_record_creates_private_lock_even_with_permissive_umask(ledger):
    old_umask = os.umask(0)
    try:
        seed(ledger)
    finally:
        os.umask(old_umask)
    assert stat.S_IMODE(ledger.with_name(f"{ledger.name}.lock").stat().st_mode) == 0o600


@pytest.mark.parametrize("linked", ["ledger", "lock"])
def test_record_refuses_symlinked_state_without_changing_target(ledger, tmp_path, linked):
    seed(ledger)
    before = ledger.read_bytes()
    target = tmp_path / "target"
    target.write_bytes(before if linked == "ledger" else b"")
    link = ledger if linked == "ledger" else ledger.with_name(f"{ledger.name}.lock")
    link.unlink()
    link.symlink_to(target)
    paths = record_files(tmp_path, observation(item(action="repair CI")), posted(item(action="repair CI")))
    result = run_cli(ledger, *record_args(paths))
    assert result.returncode == 1
    assert result.stdout == ""
    assert link.is_symlink()
    assert target.read_bytes() == (before if linked == "ledger" else b"")
    assert ledger.read_bytes() == before


@pytest.mark.parametrize(
    "epic",
    [
        "infra",
        "7919",
        "a",
        "lit-war",
        "a--b",
        "",
        "../infra",
        "/infra",
        "UPPER",
        "bad_name",
        "bad.name",
        "-infra",
        "infra-",
        "infra\n",
        "інфра",
    ],
)
def test_epic_validation_matches_shell_rule(epic):
    result = subprocess.run(
        [
            "bash",
            "-c",
            'source "$1"; epic_name_valid "$2"',
            "selector-test",
            str(REPO / "scripts/lib/handoff_identity.sh"),
            epic,
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode == 0:
        blockers.validate_epic(epic)
    else:
        with pytest.raises(ValueError, match="selector"):
            blockers.validate_epic(epic)


def test_two_racing_records_have_one_winner(ledger, tmp_path):
    seed(ledger)
    current = observation(item(action="repair CI"))
    paths = record_files(tmp_path, current, posted(*current["items"]))
    command = [sys.executable, "-m", "scripts.driver_blockers", *record_args(paths)]
    environment = {**os.environ, "SESSION_EPIC": EPIC, driver_state.STATE_ENV: str(ledger.parent / "DRIVER-STATE.md")}
    with (ledger.parent / f"{blockers.LEDGER_NAME}.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        processes = [
            subprocess.Popen(
                command, cwd=REPO, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            for _ in range(2)
        ]
        fcntl.flock(lock, fcntl.LOCK_UN)
    try:
        outputs = [process.communicate(timeout=20) for process in processes]
        assert sorted(process.returncode for process in processes) == [0, 1]
        assert sum('"recorded": true' in out for out, _ in outputs) == 1
        assert blockers.load_ledger(ledger, EPIC)["generation"] == 2
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=20)


def test_killed_mid_temp_write_keeps_old_readable_ledger(ledger):
    seed(ledger)
    before = ledger.read_bytes()
    script = """import json, sys
from pathlib import Path
from scripts import driver_blockers as b
def hold(fd):
    print('temp-write-reached', flush=True)
    sys.stdin.read()
b.os.fsync = hold
b._atomic_write(Path(sys.argv[1]), json.loads(sys.argv[2]))
"""
    updated = json.loads(before)
    updated["generation"] = 2
    process = subprocess.Popen(
        [sys.executable, "-c", script, str(ledger), json.dumps(updated)],
        cwd=REPO,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        import selectors

        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            assert selector.select(timeout=20), "writer did not reach temp-write barrier"
        assert process.stdout.readline().strip() == "temp-write-reached"
        process.kill()
        process.communicate(timeout=20)
        assert ledger.read_bytes() == before
        assert blockers.load_ledger(ledger, EPIC)["generation"] == 1
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=20)


def test_atomic_write_private_same_directory_and_fsync_order(ledger, monkeypatch):
    stored = seed(ledger)
    events = []
    real_fsync, real_replace = os.fsync, os.replace

    def fsync(descriptor):
        events.append("directory-fsync" if stat.S_ISDIR(os.fstat(descriptor).st_mode) else "file-fsync")
        real_fsync(descriptor)

    def replace(source, destination, *, src_dir_fd, dst_dir_fd):
        assert src_dir_fd == dst_dir_fd
        assert os.fstat(src_dir_fd).st_ino == ledger.parent.stat().st_ino
        assert Path(source).name == source
        assert destination == ledger.name
        assert stat.S_IMODE(os.stat(source, dir_fd=src_dir_fd).st_mode) == 0o600
        assert json.loads((ledger.parent / source).read_bytes()) == stored
        events.append("replace")
        real_replace(source, destination, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)

    monkeypatch.setattr(blockers.os, "fsync", fsync)
    monkeypatch.setattr(blockers.os, "replace", replace)
    blockers._atomic_write(ledger, stored)
    assert events == ["file-fsync", "replace", "directory-fsync"]
    assert stat.S_IMODE(ledger.stat().st_mode) == 0o600
    assert list(ledger.parent.glob(f".{blockers.LEDGER_NAME}.*")) == []


def test_atomic_write_collision_preserves_existing_staging_and_ledger(ledger, monkeypatch):
    from scripts.common import safe_unit_install

    stored = seed(ledger)
    before = ledger.read_bytes()
    monkeypatch.setattr(safe_unit_install.secrets, "token_hex", lambda count: "occupied")
    staging = ledger.parent / f".{ledger.name}.occupied.tmp"
    staging.write_bytes(b"another writer's staging")
    with pytest.raises(FileExistsError):
        blockers._atomic_write(ledger, stored)
    assert staging.read_bytes() == b"another writer's staging"
    assert ledger.read_bytes() == before


def test_atomic_replace_failure_keeps_old_and_cleans_own_temp(ledger, monkeypatch):
    stored = seed(ledger)
    before = ledger.read_bytes()
    monkeypatch.setattr(
        blockers.os, "replace", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("synthetic rename failure"))
    )
    with pytest.raises(OSError, match="synthetic rename failure"):
        blockers._atomic_write(ledger, stored)
    assert ledger.read_bytes() == before
    assert list(ledger.parent.glob(f".{blockers.LEDGER_NAME}.*")) == []


def test_show_absent_present_empty_and_private_paths(ledger):
    result = run_cli(ledger, "show", "--epic", EPIC)
    assert result.returncode == 0
    assert result.stdout.strip() == blockers.UNKNOWN_SUMMARY
    seed(ledger)
    result = run_cli(ledger, "show", "--epic", EPIC)
    assert result.stdout.strip() == "CTO blockers: generation 1; 1 recorded blockers"
    ledger.write_text("")
    assert run_cli(ledger, "show", "--epic", EPIC).stdout.strip() == blockers.UNKNOWN_SUMMARY
    assert str(ledger.parent) not in result.stdout


def test_ledger_path_uses_matching_launcher_state_only(ledger, monkeypatch, tmp_path):
    assert blockers.ledger_path(EPIC) == ledger
    monkeypatch.setattr(driver_state, "_repo_root", lambda: tmp_path)
    assert blockers.ledger_path("atlas") == tmp_path / ".claude/atlas-epic" / blockers.LEDGER_NAME
    monkeypatch.delenv(driver_state.STATE_ENV)
    assert blockers.ledger_path(EPIC) == ledger
    for unsafe in ("../infra", "/infra", "infra\n", "infra\u202e"):
        with pytest.raises(ValueError, match="selector"):
            blockers.ledger_path(unsafe)


@pytest.mark.parametrize("command", [None, "delta", "record", "show"])
def test_plain_script_cli_help(tmp_path, command):
    environment = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/driver_blockers.py"), *([command] if command else []), "--help"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "usage:" in result.stdout
    assert "--help" in result.stdout


@pytest.mark.parametrize("command", [None, "delta", "record", "show"])
def test_cli_help_contract(ledger, command):
    result = run_cli(ledger, *([command] if command else []), "--help")
    assert result.returncode == 0
    for required in ("Examples:", "Outputs:", "Exit codes:", "Related:", "complete", "--expect-generation"):
        assert required in result.stdout


def test_successful_cli_record_and_delta(ledger, tmp_path):
    current = observation(item())
    paths = record_files(tmp_path, current, posted(item()))
    result = run_cli(ledger, *record_args(paths, "0"))
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"generation": 1, "recorded": True}
    result = run_cli(ledger, "delta", "--epic", EPIC, "--current", str(paths[0]))
    assert result.returncode == 0
    delta = json.loads(result.stdout)
    assert delta["baseline"] == "valid"
    assert delta["post_required"] is False
    assert delta["items"][0]["class"] == "UNCHANGED"


def test_boolean_generation_and_nonstring_anchor_cannot_validate(ledger):
    stored = seed(ledger)
    for mutate in (lambda d: d.update(generation=True), lambda d: d["anchor"].update(message_id=1)):
        corrupt = copy.deepcopy(stored)
        mutate(corrupt)
        assert blockers.validate_ledger(corrupt, EPIC) is None


def test_in_process_cli_round_trip_and_failure(ledger, tmp_path, capsys):
    current = observation(item())
    paths = record_files(tmp_path, current, posted(item()))
    assert blockers.main(record_args(paths, "0")) == 0
    assert json.loads(capsys.readouterr().out) == {"generation": 1, "recorded": True}
    assert blockers.main(["delta", "--epic", EPIC, "--current", str(paths[0])]) == 0
    assert json.loads(capsys.readouterr().out)["post_required"] is False
    assert blockers.main(["show", "--epic", EPIC]) == 0
    assert capsys.readouterr().out.strip() == "CTO blockers: generation 1; 1 recorded blockers"
    before = ledger.read_bytes()
    paths[0].write_text("bad JSON")
    assert blockers.main(["delta", "--epic", EPIC, "--current", str(paths[0])]) == 1
    result = capsys.readouterr()
    assert result.out == ""
    assert "not valid UTF-8 JSON" in result.err
    assert ledger.read_bytes() == before


@pytest.mark.parametrize("generation", [-1, True])
def test_invalid_generation_cannot_record(ledger, generation):
    seed(ledger)
    before = ledger.read_bytes()
    body = posted(item())
    with pytest.raises(ValueError, match="generation"):
        blockers.record(ledger, EPIC, observation(item()), receipt(body), body, generation)
    assert ledger.read_bytes() == before


def test_show_summary_is_bounded_even_for_large_valid_generation(ledger):
    stored = seed(ledger)
    stored["generation"] = 10**200
    ledger.write_text(json.dumps(stored))
    summary = blockers.show_summary(ledger, EPIC)
    assert summary == "CTO blockers: generation [large integer]; 1 recorded blockers"
    assert len(summary) < 100


@pytest.mark.parametrize("corruption", ["json", "anchor", "map", "epic"])
def test_record_cannot_overwrite_an_unverifiable_existing_generation_or_anchor(ledger, corruption):
    stored = seed(ledger)
    if corruption == "json":
        ledger.write_text("{")
    else:
        if corruption == "anchor":
            stored["anchor"]["created_at"] = "invalid"
        elif corruption == "map":
            stored["items"]["blocked-build"] = "invalid"
        else:
            stored["epic"] = "atlas"
        ledger.write_text(json.dumps(stored))
    before = ledger.read_bytes()
    body = posted(item(action="repair CI"))
    with pytest.raises(ValueError, match="generation and anchor"):
        blockers.record(
            ledger,
            EPIC,
            observation(item(action="repair CI")),
            receipt(body, key="message-2", stamp="2026-10-10T02:00:00Z"),
            body,
            0,
        )
    assert ledger.read_bytes() == before
    assert blockers.compute_delta(observation(item()), blockers.load_ledger(ledger, EPIC))["baseline"] == "unknown"


def test_invalid_timestamp_diagnostic_does_not_echo_receipt_data(ledger, tmp_path):
    body = posted(item())
    private = "synthetic-private-timestamp-value"
    paths = record_files(tmp_path, observation(item()), body, receipt(body, stamp=private))
    result = run_cli(ledger, *record_args(paths, "0"))
    assert result.returncode == 1
    assert private not in result.stderr
    assert "anchor created_at must be an ISO-8601 timestamp" in result.stderr
    assert not ledger.exists()

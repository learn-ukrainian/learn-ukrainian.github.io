"""Synthetic Fleet hour/export controls, not integrated delivery proof (#10154)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest

from scripts.fleet import router_report
from scripts.fleet.router_policy import RouterPolicyError, aggregate_hour, digest
from scripts.fleet.router_report import HourReaderReceipt, export_hour, main, read_hour
from scripts.fleet_comms.routing_reservations import RoutingReservationLedger
from scripts.orchestration.task_lifecycle import digest as lifecycle_digest

START = "2035-01-01T00:00:00Z"
END = "2035-01-01T01:00:00Z"
SENTINEL = "PRIVATE_EXPORT_SENTINEL"
_REAL_CLOCK = router_report._utc_now


@pytest.fixture(autouse=True)
def fixed_reader_clock(monkeypatch):
    monkeypatch.setattr(router_report, "_utc_now", lambda: datetime(2035, 1, 2, tzinfo=UTC))


@pytest.fixture
def root(tmp_path):
    root = tmp_path / "plane"
    with RoutingReservationLedger(root=root):
        pass
    return root


def event(root, event_id, *, kind="selected", at=START, state="reserved", task="task", nonce="nonce", metadata=None, source="routing"):
    metadata = {"task_id": task, "run_nonce": nonce, **(metadata or {})}
    # Immutable synthetic rows in disposable migrated Fleet authority storage.
    # No fake provider execution, delivery claim or production write.
    with sqlite3.connect(root / "comms.sqlite3") as connection:
        if source == "routing":
            connection.execute("INSERT INTO routing_reservation_decisions VALUES (?,?,?,?,?,?)",
                               (event_id, "synthetic-reservation", kind, state, json.dumps(metadata), at))
        else:
            connection.execute("INSERT INTO authority_job_events VALUES (?,?,?,?,?,?,?)",
                               (event_id, "synthetic-job", 1, kind, state, json.dumps(metadata), at))


def proof_reference(tmp_path, name, value):
    path = tmp_path / name
    raw = json.dumps(value).encode()
    path.write_bytes(raw)
    return {"receipt_path": str(path), "receipt_sha256": "sha256:" + hashlib.sha256(raw).hexdigest()}


def behavior_record(tmp_path, *, at=START):
    # Matches the existing canonical review/lifecycle contract exactly.
    input_digest, head = "a" * 64, "b" * 40
    proof = {
        "schema_version": "code-review-receipt.v1", "target": {"head_sha": head, "input_sha256": input_digest},
        "author": {"family": "openai"}, "reviewer": {"family": "anthropic"},
        "final_disposition": "clean", "exit_code": 0, "error": None,
        "behavior_proof": {"schema_version": "behavior-proof.v1", **{
            surface: {"status": "pass", "clauses": [{"target_input_sha256": input_digest}]}
            for surface in ("source_aware", "source_blind")}},
    }
    reference = {**proof_reference(tmp_path, "behavior.json", proof), "target_sha": head, "input_sha256": input_digest}
    record = {"type": "behavior_proof", "ac_id": "AC-1", "summary": "Synthetic proof",
              "url": None, "subject": {"repository": "example/repo", "issue": 1, "pr": 2, "commit": head},
              "details": {"behavior_proof_receipt": reference}, "recorded_at": at}
    return {**record, "id": lifecycle_digest(record)}


def forge_reference(tmp_path, *, at=START):
    return proof_reference(tmp_path, "forge.json", {
        "schema_version": "task-closeout-observation.v1", "observed_at": END,
        "github": {"repository": "example/repo", "error": None,
                   "pr": {"number": 2, "state": "MERGED", "merged_at": at, "merge_sha": "c" * 40}},
        "local": {},
    })


def test_complete_empty_and_full_pages_have_explicit_denominators(root):
    report = export_hour(root=root, start=START, end=END, page_size=1)
    assert report["status"] == "COMPLETE"
    assert report["denominator"]["events"] == report["denominator"]["unique_tasks"] == 0
    assert all(metric["count"] == 0 for metric in report["metrics"].values())
    event(root, "1", kind="reserved")
    event(root, "2", kind="admitted", task="other", source="job")
    report = export_hour(root=root, start=START, end=END, page_size=1)
    assert report["reader"]["exhausted"] is True
    assert report["reader"]["pages"] == 4
    assert report["metrics"]["selected"]["count"] == 1
    assert report["metrics"]["admitted"]["count"] == 2
    assert report["denominator"]["events"] == 2
    assert report["denominator"]["unique_tasks"] == 2


def test_half_open_utc_boundaries_and_replayed_transitions(root):
    event(root, "before", at="2034-12-31T23:59:59Z")
    event(root, "start", kind="reserved")
    event(root, "replay", kind="reserved")
    event(root, "other_nonce", kind="reserved", nonce="second")
    event(root, "end", at=END, task="other")
    report = export_hour(root=root, start=START, end=END)
    assert report["metrics"]["selected"]["count"] == 2
    assert report["metrics"]["admitted"]["count"] == 2
    assert report["denominator"]["events"] == 3
    assert report["denominator"]["unique_tasks"] == 1


def test_done_never_supplies_delivered_or_merged(root):
    event(root, "done", kind="settled", state="complete", metadata={"delivered": True, "merged": True})
    report = export_hour(root=root, start=START, end=END)
    assert report["status"] == "UNKNOWN"
    assert report["metrics"]["executed_done"]["count"] == 1
    for metric in ("delivered", "merged"):
        assert report["metrics"][metric] == {"status": "UNKNOWN", "count": None, "codes": ["PROOF_MISSING"]}


def test_canonical_proofs_count_by_their_own_times_and_dedupe_merge(root, tmp_path):
    metadata = {"behavior_proof_record": behavior_record(tmp_path), "forge_receipt": forge_reference(tmp_path)}
    # Creation and execution belong to a different hour from proof/merge.
    event(root, "done", kind="settled", state="complete", at="2034-12-31T23:30:00Z", metadata=metadata)
    event(root, "replay", kind="settled", state="complete", at="2034-12-31T23:30:01Z", metadata=metadata)
    event(root, "another_task_same_merge", kind="merged", at=END, task="other", metadata={"forge_receipt": metadata["forge_receipt"]})
    report = export_hour(root=root, start=START, end=END)
    assert report["status"] == "COMPLETE"
    assert report["metrics"]["executed_done"]["count"] == 0
    assert report["metrics"]["delivered"]["count"] == report["metrics"]["merged"]["count"] == 1
    assert report["denominator"]["events"] == 0
    assert report["denominator"]["unique_tasks"] == 2


@pytest.mark.parametrize("kind", ["digest", "family", "timestamp", "target", "surface", "bare_reference", "record_digest", "subject"])
def test_invalid_behavior_receipts_stay_unknown(root, tmp_path, kind):
    record = behavior_record(tmp_path)
    reference = record["details"]["behavior_proof_receipt"]
    if kind in {"family", "target", "surface"}:
        value = json.loads(Path(reference["receipt_path"]).read_text())
        if kind == "family":
            value["reviewer"]["family"] = "openai"
        elif kind == "target":
            value["target"]["head_sha"] = "d" * 40
        else:
            value["behavior_proof"]["source_blind"]["status"] = "fail"
        reference.update(proof_reference(tmp_path, "behavior.json", value))
    elif kind == "digest":
        reference["receipt_sha256"] = "sha256:" + "f" * 64
    elif kind == "timestamp":
        record["recorded_at"] = "invalid"
    elif kind == "subject":
        record["subject"]["commit"] = "d" * 40
    if kind != "record_digest":
        record["id"] = lifecycle_digest({key: value for key, value in record.items() if key != "id"})
    else:
        record["id"] = "bad"
    event(root, "delivery", kind="delivered", metadata={"behavior_proof_record": reference if kind == "bare_reference" else record})
    assert export_hour(root=root, start=START, end=END)["metrics"]["delivered"]["status"] == "UNKNOWN"


@pytest.mark.parametrize("kind", ["missing", "false_flag", "wrong_schema", "not_merged", "sha", "timestamp", "repository", "number", "error", "observation", "not_object"])
def test_invalid_forge_receipts_stay_unknown(root, tmp_path, kind):
    reference = forge_reference(tmp_path)
    value = json.loads(Path(reference["receipt_path"]).read_text())
    if kind == "missing":
        reference = None
    elif kind == "false_flag":
        reference = {"merged": True}
    else:
        if kind == "wrong_schema":
            value["schema_version"] = "wrong"
        elif kind == "not_merged":
            value["github"]["pr"]["state"] = "OPEN"
        elif kind == "sha":
            value["github"]["pr"]["merge_sha"] = SENTINEL
        elif kind == "timestamp":
            value["github"]["pr"]["merged_at"] = SENTINEL
        elif kind == "repository":
            value["github"]["repository"] = None
        elif kind == "number":
            value["github"]["pr"]["number"] = True
        elif kind == "error":
            value["github"]["error"] = SENTINEL
        elif kind == "observation":
            value["observed_at"] = "2034-01-01T00:00:00Z"
        elif kind == "not_object":
            value = []
        reference = proof_reference(tmp_path, "forge.json", value)
    event(root, "merge", kind="merged", metadata={"forge_receipt": reference})
    report = export_hour(root=root, start=START, end=END)
    assert report["metrics"]["merged"]["status"] == "UNKNOWN"
    assert SENTINEL not in json.dumps(report)


@pytest.mark.parametrize("kind", ["missing_db", "missing_table", "bad_json", "non_object", "duplicate_json", "bad_timestamp", "bad_nonce", "partial", "symlink", "corrupt_db"])
def test_gaps_caps_and_corrupt_sources_cannot_be_empty(root, tmp_path, kind):
    if kind == "missing_db":
        root = tmp_path / "missing"
    elif kind == "symlink":
        link = tmp_path / "linked"
        link.symlink_to(root, target_is_directory=True)
        root = link
    elif kind == "corrupt_db":
        (root / "comms.sqlite3").write_bytes(SENTINEL.encode())
    else:
        event(root, "one")
        with sqlite3.connect(root / "comms.sqlite3") as connection:
            if kind == "missing_table":
                connection.execute("ALTER TABLE authority_job_events RENAME TO missing_events")
            elif kind not in {"partial"}:
                # Update a synthetic job row (routing events are immutable).
                event(root, "bad", source="job")
                field = "created_at" if kind == "bad_timestamp" else "metadata_json"
                raw = {"bad_json": "{", "non_object": "[]", "duplicate_json": '{"a":1,"a":2}',
                       "bad_timestamp": SENTINEL, "bad_nonce": '{"run_nonce":null}'}[kind]
                connection.execute(f"UPDATE authority_job_events SET {field}=?", (raw,))
    report = export_hour(root=root, start=START, end=END, page_size=1, max_pages=1 if kind == "partial" else None)
    assert report["status"] == "UNKNOWN"
    assert report["denominator"]["events"] is None
    assert all(item["count"] is None for item in report["metrics"].values())


def test_receipt_binding_rejects_bool_json_hour_events_and_tampering(root):
    read = read_hour(root=root, start=START, end=END)
    for receipt in (True, False, read.receipt.private_dict(),
                    HourReaderReceipt(START, END, "a"*64, digest([]), 1, END, True, "COMPLETE"),
                    replace(read.receipt, source_sha256="f"*64)):
        assert aggregate_hour([], start=START, end=END, complete=receipt)["code"] == "READER_MISMATCH"
    assert aggregate_hour(read.events, start=END, end="2035-01-01T02:00:00Z", complete=read.receipt)["code"] == "READER_MISMATCH"
    changed = [{"secret": SENTINEL}]
    assert aggregate_hour(changed, start=START, end=END, complete=read.receipt)["code"] == "READER_MISMATCH"
    assert aggregate_hour(changed, start=START, end=END, complete=replace(read.receipt, events_sha256=digest(changed)))["code"] == "READER_MISMATCH"


@pytest.mark.parametrize("start,end", [("2035-01-01", END), ("2035-01-01T00:30:00Z", END), (START, START), (START, "2035-01-01T02:00:00Z"), ("2035-01-01T01:00:00+01:00", END)])
def test_invalid_hour_rejected(root, start, end):
    with pytest.raises(RouterPolicyError, match="HOUR_INVALID"):
        read_hour(root=root, start=start, end=end)


@pytest.mark.parametrize("page_size,max_pages", [(0, None), (True, None), (10001, None), (1, 0), (1, True)])
def test_invalid_page_options(root, page_size, max_pages):
    with pytest.raises(RouterPolicyError, match="EXPORT_INVALID"):
        read_hour(root=root, start=START, end=END, page_size=page_size, max_pages=max_pages)


def test_actual_cli_entrypoint_and_private_boundary(root):
    event(root, "private", metadata={"trace": {"reason": SENTINEL}})
    command = [sys.executable, "-m", "scripts.fleet.router_report", "--root", str(root), "--start", "2000-01-01T00:00:00Z", "--end", "2000-01-01T01:00:00Z"]
    public = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
    assert public.returncode == 0
    assert SENTINEL not in public.stdout + public.stderr
    assert "metrics" not in json.loads(public.stdout)
    private = subprocess.run([*command, "--visibility", "private", "--include-events"], capture_output=True, text=True, check=False, timeout=30)
    assert private.returncode == 0
    assert SENTINEL in json.loads(private.stdout)["private_events"][0]["metadata"]["trace"]["reason"]
    error = subprocess.run([*command, "--visibility", SENTINEL], capture_output=True, text=True, check=False, timeout=30)
    assert error.returncode == 2
    assert SENTINEL not in error.stdout + error.stderr
    assert json.loads(error.stdout)["code"] == "EXPORT_INVALID"
    help_result = subprocess.run([sys.executable, "-m", "scripts.fleet.router_report", "--help"], capture_output=True, text=True, check=False, timeout=30)
    assert help_result.returncode == 0
    assert all(label in help_result.stdout for label in ("Outputs:", "Exit codes:", "Related:"))


def test_cli_unknown_and_no_private_events_in_public(root, capsys):
    assert main(["--root", str(root / "missing"), "--start", START, "--end", END]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "unknown"
    assert main(["--start", START, "--end", END, "--include-events"]) == 2
    assert "private_events" not in capsys.readouterr().out


def test_snapshot_has_no_mutable_join_and_does_not_write(root):
    event(root, "one", kind="finished", state="complete", source="job")
    before = (root / "comms.sqlite3").read_bytes()
    read = read_hour(root=root, start=START, end=END)
    assert read.events[0]["finished_at"] is None
    report = aggregate_hour(read.events, start=START, end=END, complete=read.receipt)
    assert report["metrics"]["executed_done"]["status"] == "UNKNOWN"
    assert (root / "comms.sqlite3").read_bytes() == before
    # Reservation/job subjects here are intentionally absent. No mutable join
    # is needed, and full private metadata survives the export unchanged.
    assert read.receipt.exhausted


def test_job_done_counts_only_immutable_terminal_time(root):
    event(root, "known", kind="finished", state="complete", source="job", at=END,
          metadata={"finished_at": START})
    read = read_hour(root=root, start=START, end=END)
    report = aggregate_hour(read.events, start=START, end=END, complete=read.receipt)
    assert report["metrics"]["executed_done"]["count"] == 1
    assert report["denominator"]["events"] == 0


def test_source_connection_failure_is_typed_unknown(root, monkeypatch):
    from scripts.control_plane import storage

    def unavailable(*args, **kwargs):
        raise RuntimeError(SENTINEL)
    monkeypatch.setattr(storage, "connect", unavailable)
    report = export_hour(root=root, start=START, end=END)
    assert report["status"] == "UNKNOWN"
    assert SENTINEL not in json.dumps(report)


def test_open_hour_cannot_be_certified_complete(root, monkeypatch):
    monkeypatch.setattr(router_report, "_utc_now", lambda: datetime(2035, 1, 1, 0, 30, tzinfo=UTC))
    report = export_hour(root=root, start=START, end=END)
    assert report["status"] == "UNKNOWN"
    assert report["code"] == "READER_PARTIAL"


def test_empty_event_id_is_corruption_not_a_skipped_page(root):
    event(root, "")
    report = export_hour(root=root, start=START, end=END)
    assert report["status"] == "UNKNOWN"
    assert report["code"] == "READER_CORRUPT"


def test_private_export_and_cli_argument_errors(root, capsys):
    event(root, "private", metadata={"trace": {"reason": SENTINEL}})
    report = export_hour(root=root, start=START, end=END, include_events=True)
    assert report["private_events"][0]["metadata"]["trace"]["reason"] == SENTINEL
    assert main(["--start", START, "--end", END, "--visibility", SENTINEL]) == 2
    output = capsys.readouterr().out
    assert SENTINEL not in output
    assert json.loads(output)["code"] == "EXPORT_INVALID"
    assert _REAL_CLOCK().tzinfo == UTC


@pytest.mark.parametrize("variant", ["identical", "conflicting", "missing_identity", "not_mapping", "nonfinite"])
def test_aggregate_contract_handles_reader_injected_replay_and_corruption(root, monkeypatch, variant):
    # Immutable injected adapter fixtures exercise aggregate guards; this is
    # component contract proof, never claimed as an actual Fleet replay event.
    event(root, "first", kind="reserved")
    fixture = read_hour(root=root, start=START, end=END).events[0]
    event(root, "second", kind="reserved")
    def injected(row, source):
        output = dict(fixture)
        if variant == "conflicting":
            output["state"] = "failed" if row["decision_id"] == "second" else "reserved"
        elif variant == "missing_identity":
            output["task_id"] = ""
        elif variant == "not_mapping":
            return None
        elif variant == "nonfinite":
            output["metadata"] = {"nonfinite": float("nan")}
        return output
    monkeypatch.setattr(router_report, "_normalize_event", injected)
    if variant == "nonfinite":
        # A failed serialization cannot mint a valid complete receipt.
        report = export_hour(root=root, start=START, end=END)
        assert report["status"] == "UNKNOWN"
        assert report["code"] == "READER_CORRUPT"
    else:
        report = export_hour(root=root, start=START, end=END)
        if variant == "identical":
            assert report["metrics"]["selected"]["count"] == 1
            assert report["denominator"]["events"] == 1
        else:
            assert report["code"] == "READER_CORRUPT"


def test_missing_behavior_file_reference_is_unknown(root, tmp_path):
    record = behavior_record(tmp_path)
    record["details"]["behavior_proof_receipt"] = {}
    record["id"] = lifecycle_digest({key: value for key, value in record.items() if key != "id"})
    event(root, "missing", kind="delivered", metadata={"behavior_proof_record": record})
    report = export_hour(root=root, start=START, end=END)
    assert report["metrics"]["delivered"]["status"] == "UNKNOWN"

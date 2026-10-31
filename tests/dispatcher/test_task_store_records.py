"""Approved #12192 admission and mid-run record-damage defect classes."""

import json
import signal
from types import SimpleNamespace

import pytest

from scripts.dispatcher import store, worker
from scripts.dispatcher.types import TaskSpec
from scripts.orchestration.task_record_store import read_task_record
from scripts.review import budget_grant, review_lineage
from scripts.review import record_cf_verdict as recorder
from tests.dispatcher.test_core import run_git
from tests.dispatcher.test_core import sandbox as sandbox

HEAD = "a" * 40


def admission_readers(root):
    return [
        lambda: review_lineage.review_records(root, repository="org/repo"),
        lambda: budget_grant._grant_records(root),
        lambda: store.list_tasks(include_archive=True, strict=True),
        lambda: recorder.admitted_unknown_history(
            repository="org/repo", branch="topic", head_sha=HEAD, task_root=root, repo_root=root
        ),
        lambda: recorder.require_no_outside_review_in_flight(root, "org/repo", HEAD),
    ]


@pytest.mark.parametrize("archived", [False, True])
@pytest.mark.parametrize("foreign", [
    b"[curriculum_manifest_canary] Manifest written successfully: 3901 files\n",
    b'{"schema":"agy-read-only.v1","task_id":"worker"}',
    b'{"schema_version":"code-review-findings.v1","findings":[]}',
    b'["a proof list"]',
])
def test_foreign_sidecar_does_not_block_review_admission(tmp_path, monkeypatch, caplog, foreign, archived):
    """A foreign sidecar must not deny an unrelated review or spend its attempt."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    archive = tmp_path / "archive"
    archive.mkdir()
    valid = dict(task_id="unrelated", schema_version=2, repository="org/repo", status="done", review_profile="infra")
    (tmp_path / "unrelated.json").write_text(json.dumps(valid))
    sidecar = (archive if archived else tmp_path) / "worker.manifest-canary.json"
    sidecar.write_bytes(foreign)
    assert [record["task_id"] for _, record in admission_readers(tmp_path)[0]()] == ["unrelated"]
    assert admission_readers(tmp_path)[1]() == []
    assert [record["task_id"] for record in admission_readers(tmp_path)[2]()] == ["unrelated"]
    assert admission_readers(tmp_path)[3]() == ()
    assert admission_readers(tmp_path)[4]() is None
    store.check_review_attempt(dict(review_id="unused", attempt_id="unused", manifest_sha256="b" * 64))
    assert str(sidecar) in caplog.text


def test_receipt_marker_cannot_hide_legacy_review_claim(tmp_path, monkeypatch):
    """A receipt marker cannot remove a lifecycle claim from admission's inventory."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    record = dict(schema="agy-read-only.v1", task_id="legacy-review", agent="claude", status="done",
                  review_profile="infra", review_mode="cross_family", repository="org/repo", worktree_branch="topic")
    (tmp_path / "legacy-review.receipt.json").write_text(json.dumps(record))

    assert [row["task_id"] for _, row in review_lineage.review_records(tmp_path, repository="org/repo")] == [
        "legacy-review"
    ]
    assert [row["task_id"] for row in store.list_tasks(include_archive=True, strict=True)] == ["legacy-review"]


@pytest.mark.parametrize(("marker", "value"), [
    ("pr", 12192),
    ("review_attempt", {"review_id": "legacy"}),
    ("require_review_verdict", True),
    ("review_profile", "infra"),
    ("review_author_model", "gpt-6.1-sol"),
    ("review_risk", "high"),
    ("review_mode", "cross_family"),
    ("type", "review"),
])
def test_legacy_review_flags_remain_visible_to_lineage(tmp_path, marker, value):
    """Every established review flag retains a legacy row in lineage inventory."""
    (tmp_path / "legacy-review.json").write_text(json.dumps({"repository": "org/repo", marker: value}))

    assert [path.name for path, _ in review_lineage.review_records(tmp_path, repository="org/repo")] == [
        "legacy-review.json"
    ]


@pytest.mark.parametrize("damaged", [
    b'{"schema_version":2,"task_id":"damaged",',
    b'{"schema_version":3,"task_id":"damaged"}',
    b'{"schema_version":"2","task_id":"damaged"}',
    b'{"schema_version":2,"task_id":"forged"}',
    '{"schema_version":2,"task_id":"damaged"}'.encode("utf-16"),
    b'\xef\xbb\xbf{"schema_version":2,"task_id":"damaged"}',
    b'\xef\xbb\xbf\n{"schema_version":2,"task_id":"damaged"}',
    b'\xef\xbb\xbf\t  {"schema_version":2,"task_id":"damaged"}',
    '\ufeff\u00a0{"schema_version":2,"task_id":"damaged"}'.encode("utf-8"),
    b'\x00\x00{"schema_version":2,"task_id":"damaged"}',
])
def test_damaged_record_still_refuses_admission(tmp_path, monkeypatch, damaged):
    """Corruption or forged identity must not disappear from admission scans."""
    monkeypatch.setenv("LU_TASKS_DIR", str(tmp_path))
    archive = tmp_path / "archive"
    archive.mkdir()
    legacy = archive / "legacy.20261030T000000Z.1.archived.json"
    legacy.write_text(json.dumps(dict(task_id="legacy", status="done", review_profile="infra", repository="org/repo")))
    assert read_task_record(legacy)["task_id"] == "legacy"
    assert [record["task_id"] for _, record in admission_readers(tmp_path)[0]()] == ["legacy"]
    (tmp_path / "damaged.json").write_bytes(damaged)
    for reader in admission_readers(tmp_path):
        with pytest.raises((ValueError, recorder.RecordError)):
            reader()


@pytest.mark.parametrize("phase", ["provider_exit", "settlement_cutoff", "terminal_write"])
@pytest.mark.parametrize("damage", ["deleted", "truncated", "non_object", "missing_nonce", "replaced_nonce", "recursion"])
def test_mid_run_record_damage_publishes_typed_terminal_failure(sandbox, monkeypatch, phase, damage):
    """Record loss/corruption cannot strand a supervisor or overwrite a replacement run."""
    from tests.dispatcher import stub_provider

    monkeypatch.setenv("LU_TASKS_DIR", str(sandbox.tasks))
    monkeypatch.setattr(worker.providers, "load", lambda _agent: stub_provider)
    released = []
    hold = SimpleNamespace(environment=lambda: {}, release=lambda: released.append(True))
    monkeypatch.setattr(worker.admission, "hold_review_test_slots", lambda **_kwargs: (hold, None))
    spec = TaskSpec("damage-probe", "codex", "echo", None, "read-only", sandbox.repo,
                    sandbox.repo / "damage-probe.prompt", sandbox.tasks / "damage-probe.result")
    spec.prompt_file.write_bytes(b"literal final response")
    record = store.new_record(spec, {"key": "public", "github": str(sandbox.remote)}, "main",
                              run_git(sandbox.repo, "rev-parse", "HEAD"), {"research_owned_path": []})
    record["prompt_file"] = str(sandbox.tasks / "damage-probe.prompt")
    path = store.create(record, b"literal final response")
    (sandbox.tasks / "logs").mkdir()
    original = worker.communicate if phase == "provider_exit" else getattr(
        store, "begin_settlement" if phase == "settlement_cutoff" else "_write"
    )
    damaged = False

    def damage_record():
        nonlocal damaged
        if damaged:
            return
        damaged = True
        if damage == "deleted":
            path.unlink()
        elif damage == "truncated":
            path.write_text('{"schema_version":2,')
        elif damage == "non_object":
            path.write_text("[]")
        elif damage == "recursion":
            path.write_text("[" * 100000)
        elif damage == "missing_nonce":
            path.write_text("{}")
        else:
            path.write_text(json.dumps(dict(record, run_nonce="replacement")))

    def interrupted(*args, **kwargs):
        if phase == "terminal_write":
            if args[1].get("status") not in store.ACTIVE:
                damage_record()
            return original(*args, **kwargs)
        result = original(*args, **kwargs)
        damage_record()
        return result

    monkeypatch.setattr(worker if phase == "provider_exit" else store,
                        "communicate" if phase == "provider_exit" else (
                            "begin_settlement" if phase == "settlement_cutoff" else "_write"), interrupted)
    reaped = []
    monkeypatch.setattr(worker, "_reap_settled", lambda *_args, **_kwargs: reaped.append(True))
    previous_term, previous_int = signal.getsignal(signal.SIGTERM), signal.getsignal(signal.SIGINT)
    if damage == "replaced_nonce":
        with pytest.raises(store.TaskRecordError, match="TASK_RECORD_REPLACED"):
            worker.supervise(path, {}, 10)
        assert json.loads(path.read_text())["run_nonce"] == "replacement"
    else:
        worker.supervise(path, {}, 10)
        terminal = store.read("damage-probe", record["run_nonce"])
        assert terminal["status"] == "crashed"
        assert terminal["error"] == "TASK_RECORD_DAMAGED"
        assert terminal["finished_at"]
        assert terminal["worktree_disposition_reason"] == "task_record_damaged"
        assert worker._identity(terminal["provider_pgid"]) is None
    assert damaged
    assert released == [True]
    assert reaped == []
    assert signal.getsignal(signal.SIGTERM) is previous_term
    assert signal.getsignal(signal.SIGINT) is previous_int

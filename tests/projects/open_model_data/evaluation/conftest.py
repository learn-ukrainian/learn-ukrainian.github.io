"""Synthetic dispatch, cgroup, custody and committed-blob fixtures only."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.orchestration.dispatch_isolation import scope_cgroup, scope_unit_name
from scripts.projects.open_model_data.evaluation import custody
from scripts.projects.open_model_data.review_build import output
from scripts.review.model_catalog import load_model_catalog
from tests.projects.open_model_data.review_build.conftest import private_tmp_path as private_tmp_path


@pytest.fixture
def tmp_path(private_tmp_path):
    """Keep synthetic custody fixtures outside repository-contained basetemp."""
    return private_tmp_path


@pytest.fixture
def dispatched(tmp_path, monkeypatch):
    root = tmp_path / "SYNTHETIC-tasks"
    root.mkdir()
    task = "eval-steward-6321-synthetic-reader"
    nonce = "SYNTHETIC-nonce"
    model = load_model_catalog()["seats"]["openai_frontier"]["model_id"]
    record = dict(
        task_id=task,
        run_nonce=nonce,
        status="running",
        model=model,
        launch_mode="scope",
        launch_unit=scope_unit_name(task, nonce),
    )
    path = root / f"{task}.json"

    state = SimpleNamespace(root=root, record=record, path=path)

    def save():
        state.path.write_text(json.dumps(state.record))

    state.save = save
    save()
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", task)
    monkeypatch.setenv("LU_RUNTIME_RUN_NONCE", nonce)
    monkeypatch.delenv("LU_TASKS_DIR", raising=False)
    monkeypatch.setattr(custody, "tasks_dir", lambda: root)
    real_read = Path.read_text
    cgroup = scope_cgroup(record["launch_unit"], uid=custody.os.getuid())
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda p, *a, **kw: "0::" + cgroup + "\n" if str(p) == "/proc/self/cgroup" else real_read(p, *a, **kw),
    )
    state.cgroup = cgroup
    return state


@pytest.fixture
def sealed(dispatched, tmp_path, monkeypatch):
    monkeypatch.setattr(output, "filesystem", lambda p: "ext4")
    root = tmp_path / "SYNTHETIC-custody"
    ref = custody.ArtifactRef("C1", "final", "synthetic-v1")
    payload = "SYNTHETIC opaque membership АБВ".encode()
    sha = custody.seal(ref, payload, custody_root=root)
    issuer = dict(dispatched.record)
    issuer["status"] = "done"
    issuer_path = dispatched.path
    issuer_path.write_text(json.dumps(issuer))
    # A separate live synthetic dispatch consumes the finished writer's seal.
    reader_task = "eval-steward-6321-synthetic-active-reader"
    reader_nonce = "SYNTHETIC-reader-nonce"
    dispatched.record = {
        **issuer,
        "task_id": reader_task,
        "run_nonce": reader_nonce,
        "status": "running",
        "launch_unit": scope_unit_name(reader_task, reader_nonce),
    }
    dispatched.path = dispatched.root / (reader_task + ".json")
    dispatched.save()
    dispatched.cgroup = scope_cgroup(dispatched.record["launch_unit"], uid=custody.os.getuid())
    monkeypatch.setenv("LEARN_UKRAINIAN_DISPATCH_TASK_ID", reader_task)
    monkeypatch.setenv("LU_RUNTIME_RUN_NONCE", reader_nonce)
    real_read = Path.read_text
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda p, *a, **kw: (
            "0::" + dispatched.cgroup + "\n" if str(p) == "/proc/self/cgroup" else real_read(p, *a, **kw)
        ),
    )
    events = [json.loads(line) for line in (root / custody.LOG).read_bytes().split(b"\n") if line]
    entry = {
        **custody.asdict(ref),
        "sha256": sha,
        "bytes": len(payload),
        "sealed_by_task_id": issuer["task_id"],
        "custody_genesis_sha256": custody.digest(custody.canonical(events[0])),
    }
    manifest = {"schema": "omd-sealed-rulers.v1", "entries": [entry]}
    monkeypatch.setattr(
        custody, "run_git", lambda *a, **kw: SimpleNamespace(returncode=0, stdout=custody.canonical(manifest))
    )
    return SimpleNamespace(
        root=root,
        ref=ref,
        payload=payload,
        entry=entry,
        manifest=manifest,
        dispatched=dispatched,
        issuer=issuer,
        issuer_path=issuer_path,
    )

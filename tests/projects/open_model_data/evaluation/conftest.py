"""Synthetic dispatch, cgroup, custody and committed-blob fixtures only."""

import json
import subprocess
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.orchestration.dispatch_isolation import scope_cgroup, scope_unit_name
from scripts.orchestration.execution_safe_git import run_git
from scripts.projects.open_model_data.evaluation import custody
from scripts.projects.open_model_data.review_build import output
from scripts.review.model_catalog import CATALOG_PATH, load_model_catalog
from tests.projects.open_model_data.review_build.conftest import private_tmp_path as private_tmp_path


@pytest.fixture
def tmp_path(private_tmp_path):
    """Keep synthetic custody fixtures outside repository-contained basetemp."""
    return private_tmp_path


@pytest.fixture
def history(tmp_path, monkeypatch):
    """Real disposable Git witnesses; these catalog copies authorize no dispatch."""
    repo = tmp_path / "SYNTHETIC-repo"
    repo.mkdir()

    def git(*args):
        return subprocess.run(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "commit.gpgSign=false",
                "-c",
                "user.name=Synthetic",
                "-c",
                "user.email=synthetic@example.invalid",
                *args,
            ],
            cwd=repo,
            check=True,
            capture_output=True,
            timeout=30,
        )

    git("init", "-b", "synthetic")
    catalog_path = repo / custody.CATALOG_BLOB
    catalog_path.parent.mkdir(parents=True)
    data = yaml.safe_load(CATALOG_PATH.read_bytes())
    template = data["models"][data["seats"]["openai_frontier"]["model_id"]]
    for identity in ("SYNTHETIC-model-a", "SYNTHETIC-model-b"):
        data["models"][identity] = {**deepcopy(template), "aliases": [], "routing_wire_ids": {"native_codex": identity}}
        data["models"][identity].pop("runtime_model_ids", None)
    data["seats"]["openai_frontier"]["model_id"] = "SYNTHETIC-model-a"
    catalog_path.write_text(yaml.safe_dump(data), encoding="utf-8")

    def commit():
        git("add", ".")
        git("commit", "--allow-empty", "-m", "Synthetic custody witness")
        sha = git("rev-parse", "HEAD").stdout.decode().strip()
        git("update-ref", "refs/remotes/origin/main", sha)
        return sha

    def catalog(data):
        catalog_path.write_text(yaml.safe_dump(data), encoding="utf-8")
        # A new synthetic dispatch reloads its catalog; never authorize a model run.
        load_model_catalog.cache_clear()
        return commit()

    def manifest(data):
        path = repo / custody.MANIFEST_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(custody.canonical(data))
        return commit()

    initial = commit()
    monkeypatch.setattr(custody, "REPOSITORY", repo)
    monkeypatch.setattr(custody, "CATALOG_PATH", catalog_path)
    monkeypatch.setattr(custody, "load_model_catalog", lambda: load_model_catalog(catalog_path))
    monkeypatch.setattr(custody, "run_git", run_git)
    return SimpleNamespace(
        repo=repo,
        git=git,
        commit=commit,
        catalog=catalog,
        manifest=manifest,
        catalog_path=catalog_path,
        initial=initial,
    )


@pytest.fixture
def dispatched(tmp_path, monkeypatch, history):
    root = tmp_path / "SYNTHETIC-tasks"
    root.mkdir()
    task = "eval-steward-6321-synthetic-reader"
    nonce = "SYNTHETIC-nonce"
    model = custody.load_model_catalog()["seats"]["openai_frontier"]["model_id"]
    record = dict(
        task_id=task,
        run_nonce=nonce,
        status="running",
        model=model,
        launch_mode="scope",
        launch_unit=scope_unit_name(task, nonce),
    )
    path = root / f"{task}.json"

    state = SimpleNamespace(root=root, record=record, path=path, history=history)

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
def sealed(dispatched, tmp_path, monkeypatch, history):
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
        "sealed_event_sha256": custody.digest(custody.canonical(events[1])),
    }
    manifest = {"schema": "omd-sealed-rulers.v1", "entries": [entry]}
    history.manifest(manifest)
    return SimpleNamespace(
        root=root,
        ref=ref,
        payload=payload,
        entry=entry,
        manifest=manifest,
        dispatched=dispatched,
        issuer=issuer,
        issuer_path=issuer_path,
        history=history,
    )

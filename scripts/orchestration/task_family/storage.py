"""Atomic local persistence for task-family plans, events, and receipts."""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import Any

from .model import LifecycleEvent, LifecycleState, OperationReceipt, TaskFamilyManifest
from .planner import TaskFamilyPlan, canonical_json, sha256_digest


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomically publish JSON after flushing file and directory metadata."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (canonical_json(payload) + "\n").encode("utf-8")
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temp_name)
        raise


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temp_name)
        raise


@contextmanager
def advisory_lock(path: Path) -> Iterator[None]:
    """Cooperate with other planners; never alters or deletes Git lock files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class TaskFamilyStorage:
    """Stores runtime state at .agent/task-families/<family>/operations/<operation>/."""

    def __init__(self, repo_root: Path, family_id: str, operation_id: str) -> None:
        self.root = repo_root / ".agent" / "task-families" / family_id / "operations" / operation_id

    @property
    def plan_path(self) -> Path:
        return self.root / "plan.json"

    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.json"

    @property
    def state_path(self) -> Path:
        return self.root / "state.json"

    @property
    def receipt_path(self) -> Path:
        return self.root / "receipt.json"

    @property
    def receipt_text_path(self) -> Path:
        return self.root / "receipt.txt"

    @property
    def execution_path(self) -> Path:
        """Immutable CLI-to-executor adaptation inputs for this operation."""
        return self.root / "execution.json"

    @property
    def rename_plan_path(self) -> Path:
        """Immutable title-reconciliation authorization for one rename operation."""
        return self.root / "rename-plan.json"

    @property
    def rollover_plan_path(self) -> Path:
        """Immutable exact-ID plan for one native rollover transition."""
        return self.root / "rollover-plan.json"

    @property
    def rollover_binding_path(self) -> Path:
        """Immutable native-created replacement identity and typed relations."""
        return self.root / "rollover-binding.json"

    @property
    def rollover_archive_authorization_path(self) -> Path:
        """Immutable post-confirmation authorization for one predecessor archive."""
        return self.root / "rollover-archive-authorization.json"

    @property
    def lock_path(self) -> Path:
        return self.root / ".operation.lock"

    @property
    def snapshots_dir(self) -> Path:
        return self.root / "snapshots"

    @property
    def events_path(self) -> Path:
        return self.root / "events.jsonl"

    def write_manifest(self, manifest: TaskFamilyManifest) -> None:
        if self.manifest_path.exists():
            existing = self.read_json(self.manifest_path)
            if existing != manifest.to_dict():
                raise ValueError("immutable manifest mismatch; create a new operation instead of replacing this manifest")
            return
        atomic_write_json(self.manifest_path, manifest.to_dict())

    def load_manifest(self) -> TaskFamilyManifest:
        return TaskFamilyManifest.from_dict(self.read_json(self.manifest_path))

    def write_plan(self, plan: TaskFamilyPlan) -> None:
        if self.plan_path.exists():
            existing = self.read_json(self.plan_path)
            if existing.get("digest") != plan.digest:
                raise ValueError("immutable plan digest mismatch; create a new operation instead of replacing this plan")
            return
        atomic_write_json(self.plan_path, plan.to_dict())

    def write_immutable_json(self, path: Path, payload: dict[str, Any]) -> None:
        """Write a stable operation document once, rejecting replacement drift."""
        if path.exists():
            if self.read_json(path) != payload:
                raise ValueError(f"immutable operation document mismatch: {path.name}")
            return
        atomic_write_json(path, payload)

    def write_execution(self, payload: dict[str, Any]) -> None:
        self.write_immutable_json(self.execution_path, payload)

    def load_execution(self) -> dict[str, Any]:
        return self.read_json(self.execution_path)

    def load_plan(self) -> TaskFamilyPlan:
        return TaskFamilyPlan.from_dict(self.read_json(self.plan_path))

    def assert_plan_digest(self, digest: str) -> dict[str, Any]:
        payload = self.read_json(self.plan_path)
        immutable = dict(payload)
        immutable.pop("digest", None)
        immutable.pop("state", None)
        actual = sha256_digest(immutable)
        if digest != payload.get("digest") or actual != digest:
            raise ValueError("immutable plan digest does not match persisted plan")
        return payload

    def write_receipt(self, receipt: OperationReceipt) -> None:
        atomic_write_json(self.receipt_path, receipt.to_dict())
        atomic_write_text(self.receipt_text_path, receipt.render_human())

    def load_receipt(self) -> OperationReceipt:
        return OperationReceipt.from_dict(self.read_json(self.receipt_path))

    def write_state(self, state: LifecycleState, *, details: dict[str, Any] | None = None) -> None:
        """Atomically persist mutable execution state; plans remain immutable."""
        atomic_write_json(
            self.state_path,
            {"schema_version": 1, "state": state.value, "details": details or {}},
        )

    def load_state(self) -> dict[str, Any]:
        payload = self.read_json(self.state_path)
        if payload.get("schema_version") != 1:
            raise ValueError(f"unsupported operation state schema_version: {payload.get('schema_version')!r}")
        try:
            LifecycleState(payload.get("state"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"unknown lifecycle state: {payload.get('state')!r}") from exc
        if not isinstance(payload.get("details"), dict):
            raise ValueError("operation state details must be an object")
        return payload

    def write_snapshot(self, name: str, payload: dict[str, Any]) -> Path:
        if not name or Path(name).name != name or not name.endswith(".json"):
            raise ValueError("snapshot name must be a plain .json filename")
        path = self.snapshots_dir / name
        atomic_write_json(path, payload)
        return path

    def append_event(self, event: LifecycleEvent) -> None:
        """Append durable evidence while holding the per-operation advisory lock."""
        encoded = (canonical_json(event.to_dict()) + "\n").encode("utf-8")
        with advisory_lock(self.lock_path):
            self.root.mkdir(parents=True, exist_ok=True)
            with self.events_path.open("ab") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            directory_fd = os.open(self.root, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)

    def load_events(self) -> tuple[LifecycleEvent, ...]:
        if not self.events_path.exists():
            return ()
        with self.events_path.open(encoding="utf-8") as handle:
            return tuple(LifecycleEvent.from_dict(json.loads(line)) for line in handle if line.strip())

    @staticmethod
    def read_json(path: Path) -> dict[str, Any]:
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError(f"expected object JSON at {path}")
        return payload

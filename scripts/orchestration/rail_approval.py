#!/usr/bin/env python3
"""Human-issued, Monitor-served approval receipts for control-rail writes.

This module is deliberately an *issuance* boundary, not an agent helper.  It
has no import-time side effect and nothing in dispatch or the hook can invoke
``issue`` automatically.  An operator or advisor explicitly runs the CLI,
which writes an immutable runtime-store record.  Enforcement consumers never
read this file directly: they re-fetch its receipt through the Monitor API (or
an equivalently provisioned bridge) via ``rail_path_guard``.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import json
import os
import sys
import tempfile
import uuid
from collections.abc import Callable, Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

SOURCE_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(SOURCE_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_REPO_ROOT))

from scripts.common.repo_root import main_checkout_root

try:
    from .rail_path_guard import (
        APPROVED_ISSUERS,
        HEAD_SHA,
        OPAQUE_RECEIPT_ID,
        RailApprovalReceiptError,
        normalize_repository_path,
        validate_rail_approval_receipt_data,
    )
except ImportError:  # pragma: no cover - direct script invocation
    from rail_path_guard import (  # type: ignore
        APPROVED_ISSUERS,
        HEAD_SHA,
        OPAQUE_RECEIPT_ID,
        RailApprovalReceiptError,
        normalize_repository_path,
        validate_rail_approval_receipt_data,
    )

PROJECT_ROOT = main_checkout_root(SOURCE_REPO_ROOT)
DEFAULT_RAIL_APPROVAL_STORE_PATH = (
    PROJECT_ROOT / "batch_state" / "rail_approval_receipts.v1.json"
)
STORE_SCHEMA_VERSION = "rail-approval-store.v1"
MAX_TTL_HOURS = 168


class RailApprovalStoreError(ValueError):
    """The operator-controlled receipt store is unreadable or inconsistent."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _rfc3339(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _validate_store(payload: object) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, Mapping):
        raise RailApprovalStoreError("rail approval store root must be an object")
    if payload.get("schema_version") != STORE_SCHEMA_VERSION:
        raise RailApprovalStoreError("rail approval store schema version is invalid")
    receipts = payload.get("receipts")
    if not isinstance(receipts, Mapping):
        raise RailApprovalStoreError("rail approval store receipts must be an object")
    normalized: dict[str, dict[str, Any]] = {}
    for receipt_id, receipt in receipts.items():
        if not isinstance(receipt_id, str) or not OPAQUE_RECEIPT_ID.fullmatch(receipt_id):
            raise RailApprovalStoreError("rail approval store contains an invalid receipt ID")
        try:
            verified = validate_rail_approval_receipt_data(receipt)
        except RailApprovalReceiptError as exc:
            raise RailApprovalStoreError(f"rail approval store receipt {receipt_id!r} is invalid") from exc
        if verified["receipt_id"] != receipt_id:
            raise RailApprovalStoreError("rail approval store receipt key does not match its payload")
        normalized[receipt_id] = verified
    return normalized


@contextmanager
def _exclusive_store_lock(path: Path):
    """Serialize issuer writes without exposing an incomplete JSON projection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(path.suffix + ".lock")
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _read_store(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RailApprovalStoreError("rail approval store is unreadable") from exc
    return _validate_store(payload)


def _write_store(path: Path, receipts: Mapping[str, Mapping[str, Any]]) -> None:
    payload = {
        "schema_version": STORE_SCHEMA_VERSION,
        "receipts": {receipt_id: dict(receipt) for receipt_id, receipt in sorted(receipts.items())},
    }
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        directory_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            Path(temporary_name).unlink()
        raise


class RailApprovalReceiptRegistry:
    """Mutable only for human issuance; API clients expose immutable receipts."""

    def __init__(self, path: Path | str = DEFAULT_RAIL_APPROVAL_STORE_PATH) -> None:
        self.path = Path(path)

    def fetch(self, receipt_id: str) -> dict[str, Any]:
        if not OPAQUE_RECEIPT_ID.fullmatch(receipt_id):
            raise RailApprovalStoreError("rail approval receipt ID is invalid")
        receipt = _read_store(self.path).get(receipt_id)
        if receipt is None:
            raise KeyError(receipt_id)
        return dict(receipt)

    def issue(self, receipt: Mapping[str, Any]) -> dict[str, Any]:
        try:
            verified = validate_rail_approval_receipt_data(receipt)
        except RailApprovalReceiptError as exc:
            raise RailApprovalStoreError("refusing to issue an invalid rail approval receipt") from exc
        receipt_id = str(verified["receipt_id"])
        with _exclusive_store_lock(self.path):
            receipts = _read_store(self.path)
            if receipt_id in receipts:
                raise RailApprovalStoreError("rail approval receipt ID already exists")
            receipts[receipt_id] = verified
            _write_store(self.path, receipts)
        return dict(verified)


def create_rail_approval_receipt(
    *,
    task_id: str,
    head_sha: str,
    owned_paths: Sequence[str],
    issuer: str,
    ttl_hours: int,
    now: Callable[[], datetime] = _utc_now,
    receipt_id: str | None = None,
) -> dict[str, Any]:
    """Build one schema-valid, narrowly bound receipt for explicit issuance."""
    if issuer not in APPROVED_ISSUERS:
        raise RailApprovalStoreError("rail approval issuer must be operator or advisor")
    if not isinstance(task_id, str) or not task_id.strip():
        raise RailApprovalStoreError("rail approval task ID is required")
    if not isinstance(head_sha, str) or not HEAD_SHA.fullmatch(head_sha):
        raise RailApprovalStoreError("rail approval head SHA must be a 40-character lowercase SHA")
    if isinstance(ttl_hours, bool) or not isinstance(ttl_hours, int):
        raise RailApprovalStoreError("rail approval TTL must be an integer number of hours")
    if not 1 <= ttl_hours <= MAX_TTL_HOURS:
        raise RailApprovalStoreError(f"rail approval TTL must be between 1 and {MAX_TTL_HOURS} hours")
    try:
        normalized_paths = tuple(normalize_repository_path(path) for path in owned_paths)
    except RailApprovalReceiptError as exc:
        raise RailApprovalStoreError("rail approval owned paths must be exact normalized paths") from exc
    if not normalized_paths:
        raise RailApprovalStoreError("rail approval requires at least one owned path")
    if len(set(normalized_paths)) != len(normalized_paths):
        raise RailApprovalStoreError("rail approval owned paths must be unique")
    generated_id = receipt_id or f"rail-approval-{uuid.uuid4().hex}"
    if not OPAQUE_RECEIPT_ID.fullmatch(generated_id):
        raise RailApprovalStoreError("rail approval receipt ID is invalid")
    issued_at = now().astimezone(UTC)
    receipt = {
        "schema_version": "rail-approval-receipt.v1",
        "receipt_id": generated_id,
        "issuer": issuer,
        "issued_at": _rfc3339(issued_at),
        "expires_at": _rfc3339(issued_at + timedelta(hours=ttl_hours)),
        "action": "rail-path-mutation",
        "task_id": task_id,
        "head_sha": head_sha,
        "owned_paths": list(normalized_paths),
    }
    try:
        return validate_rail_approval_receipt_data(receipt)
    except RailApprovalReceiptError as exc:  # schema stays the final issuer contract
        raise RailApprovalStoreError("rail approval receipt failed schema validation") from exc


def issue_rail_approval_receipt(
    *,
    registry: RailApprovalReceiptRegistry,
    task_id: str,
    head_sha: str,
    owned_paths: Sequence[str],
    issuer: str,
    ttl_hours: int,
    now: Callable[[], datetime] = _utc_now,
) -> dict[str, Any]:
    """Create then atomically publish a receipt; never overwrite prior evidence."""
    receipt = create_rail_approval_receipt(
        task_id=task_id,
        head_sha=head_sha,
        owned_paths=owned_paths,
        issuer=issuer,
        ttl_hours=ttl_hours,
        now=now,
    )
    return registry.issue(receipt)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Human-only rail-approval issuance. This command is never called by dispatch "
            "or hook enforcement; it writes receipts for the Monitor API to serve."
        )
    )
    commands = parser.add_subparsers(dest="command", required=True)
    issue = commands.add_parser("issue", help="Issue one bounded operator/advisor rail receipt.")
    issue.add_argument("--task-id", required=True)
    issue.add_argument("--head-sha", required=True)
    issue.add_argument("--owned-path", action="append", required=True)
    issue.add_argument("--issuer", required=True, choices=sorted(APPROVED_ISSUERS))
    issue.add_argument("--ttl-hours", required=True, type=int)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "issue":  # pragma: no cover - argparse keeps this unreachable
        return 2
    try:
        receipt = issue_rail_approval_receipt(
            registry=RailApprovalReceiptRegistry(),
            task_id=args.task_id,
            head_sha=args.head_sha,
            owned_paths=args.owned_path,
            issuer=args.issuer,
            ttl_hours=args.ttl_hours,
        )
    except RailApprovalStoreError as exc:
        print(f"rail approval issuance refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - direct operator entry point
    raise SystemExit(main())

"""Operator-signed allowance for one ACP consult by a model the catalog otherwise refuses.

A parked or non-active catalog model (for example ``claude-fable-5-1`` with no
consult role, or ``gpt-6-astra`` after its red-team exception expired) may take
an ACP ask, consult or discussion seat only while an operator-signed allowance
names that exact model, the ``consult`` activity and the call's scope. Nothing
else changes: reviews, critiques and approvals of record, sealed reviews,
advisor roles, resolver, ladder and substitution selection, and execution,
writer and driver roles never read an allowance.

Trust model
-----------
Any agent running as the host user can write files in that user's directories,
so a plain local record would let an agent allow itself. The record is
therefore signed with OpenSSH (``ssh-keygen -Y sign``, namespace
``lu-allowance``) by a key the operator holds off this host, and verified with
``ssh-keygen -Y verify`` against the allowed-signers file at the one fixed path
``/etc/learn-ukrainian/operator-allowance-signers``. That file, every directory
above it and the ``ssh-keygen`` binary must be owned by root and not group- or
world-writable (a sticky directory excepted), and a symlink is refused. No
environment variable, CLI option, worktree file or caller argument selects the
signer file, the signer identity, the namespace or the binary. Residual: an
account with root can replace the signer file, the same boundary as any other
host secret. A task-scoped allowance binds to the task id the ACP entry
validates; it narrows a consult to that task, it does not authenticate the
caller.

The record file is canonical JSON (sorted keys, no spaces, one optional
trailing newline)::

    {"activity":"consult","expires_at":"2026-11-06T09:00:00Z",
     "issued_at":"2026-11-05T09:00:00Z","model":"gpt-6-astra",
     "order_ref":"chat-2026-11-05","schema":"lu-operator-allowance.v1",
     "scope":{"kind":"window"}}

``scope`` is exactly one of ``{"kind":"task","task_id":"<task id>"}`` or
``{"kind":"window"}``. ``model`` is the canonical catalog id (an alias is
refused). Every record is valid only while ``issued_at <= now < expires_at``; a
window scope may last at most 24 hours. The record and its signature live in
``$XDG_CONFIG_HOME/learn-ukrainian/operator-allowances/`` (default
``~/.config``) as ``<name>.json`` and ``<name>.json.sig``. A missing, unsigned,
badly signed, tampered or malformed record means no allowance.

Operator setup and grant steps: ``docs/guardrails/operator-allowance.md``.
"""

from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import os
import re
import stat
import subprocess
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

ALLOWANCE_SCHEMA = "lu-operator-allowance.v1"
SIGNATURE_NAMESPACE = "lu-allowance"
SIGNER_IDENTITY = "operator@learn-ukrainian"
CONSULT_ACTIVITY = "consult"
CONSULT_PURPOSE = "consult"
MAX_WINDOW = timedelta(hours=24)
RECORD_SUFFIX = ".json"
SIGNATURE_SUFFIX = ".json.sig"
MAX_RECORDS = 32
MAX_RECORD_BYTES = 4096
MAX_SIGNATURE_BYTES = 16384
VERIFY_TIMEOUT_S = 10

# Fixed trust anchors. Production code never takes these from the environment,
# a CLI option, a worktree file or a caller argument; only the test harness
# replaces the module attributes.
_SIGNERS_PATH = Path("/etc/learn-ukrainian/operator-allowance-signers")
_SSH_KEYGEN = Path("/usr/bin/ssh-keygen")
_TRUSTED_OWNER_UID = 0

_RECORD_KEYS = frozenset({"schema", "model", "activity", "scope", "order_ref", "issued_at", "expires_at"})
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}")
_SEAL = object()


class AllowanceRefused(ValueError):
    """One record was not a valid operator allowance; the caller treats it as absent."""


@dataclass(frozen=True)
class OperatorAllowance:
    """A verified allowance. Only this module constructs one, after signature verification."""

    model: str
    activity: str
    scope_kind: str
    task_id: str | None
    order_ref: str
    issued_at: datetime
    expires_at: datetime
    record_sha256: str
    _seal: object = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._seal is not _SEAL:
            raise TypeError("an OperatorAllowance is minted only by signature verification")

    def admits(
        self,
        model: Any,
        *,
        activity: str,
        task_id: str | None,
        now: datetime | None = None,
    ) -> bool:
        """True only for exactly this model text, the consult activity, this scope and the live window."""
        moment = now or datetime.now(UTC)
        if activity != CONSULT_ACTIVITY or self.activity != CONSULT_ACTIVITY:
            return False
        if str(model or "") != self.model:
            return False
        if not self.issued_at <= moment < self.expires_at:
            return False
        if self.scope_kind == "task":
            return task_id is not None and task_id == self.task_id
        return self.scope_kind == "window"

    def receipt(self) -> dict[str, Any]:
        """The typed, durable fields that name this allowance on every admitted call."""
        scope: dict[str, str] = {"kind": self.scope_kind}
        if self.task_id is not None:
            scope["task_id"] = self.task_id
        return {
            "schema": ALLOWANCE_SCHEMA,
            "model": self.model,
            "activity": self.activity,
            "scope": scope,
            "order_ref": self.order_ref,
            "issued_at": _format_time(self.issued_at),
            "expires_at": _format_time(self.expires_at),
            "record_sha256": self.record_sha256,
        }


def is_verified(value: Any) -> bool:
    """True when ``value`` is an allowance this module minted."""
    return isinstance(value, OperatorAllowance) and value._seal is _SEAL


_ACTIVE: contextvars.ContextVar[OperatorAllowance | None] = contextvars.ContextVar(
    "lu_operator_allowance", default=None
)


@contextlib.contextmanager
def activate(allowance: OperatorAllowance | None) -> Iterator[None]:
    """Install a verified allowance for one ACP consult call (``None`` installs nothing)."""
    if allowance is not None and not is_verified(allowance):
        raise TypeError("only a verified operator allowance can be activated")
    token = _ACTIVE.set(allowance)
    try:
        yield
    finally:
        _ACTIVE.reset(token)


def active_allowance() -> OperatorAllowance | None:
    """The allowance installed by the current ACP consult call, if any."""
    current = _ACTIVE.get()
    return current if is_verified(current) else None


def active_consult_allowance(model: Any, *, task_id: str | None) -> OperatorAllowance | None:
    """The installed allowance when it still admits a consult of ``model`` for ``task_id``."""
    current = active_allowance()
    if current is not None and current.admits(model, activity=CONSULT_ACTIVITY, task_id=task_id):
        return current
    return None


def allowance_dir(environ: Mapping[str, str] | None = None) -> Path:
    """The per-user directory holding signed allowance records (records only, never the signer)."""
    env = os.environ if environ is None else environ
    base = (env.get("XDG_CONFIG_HOME") or "").strip()
    root = Path(base) if base else Path(env.get("HOME") or Path.home()) / ".config"
    return root / "learn-ukrainian" / "operator-allowances"


def find_consult_allowance(
    model: Any,
    *,
    task_id: str,
    purpose: str | None,
    sealed_review: bool,
    now: datetime | None = None,
) -> OperatorAllowance | None:
    """Return a verified allowance admitting this ACP consult, or ``None`` (fail closed).

    Only an explicit non-authoritative consult purpose without sealed-review
    configuration may use an allowance. Each candidate record must verify
    against the fixed signer file before its fields are trusted.
    """
    if purpose != CONSULT_PURPOSE or sealed_review:
        return None
    moment = now or datetime.now(UTC)
    text = str(model or "")
    try:
        directory = allowance_dir()
        candidates = sorted(directory.glob(f"*{RECORD_SUFFIX}"))[:MAX_RECORDS]
    except OSError:
        return None
    for record_path in candidates:
        try:
            allowance = load_allowance(record_path, record_path.with_name(record_path.name + ".sig"))
        except AllowanceRefused:
            continue
        if allowance.admits(text, activity=CONSULT_ACTIVITY, task_id=task_id, now=moment):
            return allowance
    return None


def load_allowance(record_path: Path, signature_path: Path) -> OperatorAllowance:
    """Verify one record and its signature, then validate its fields; raise ``AllowanceRefused``."""
    record = _read_bounded(record_path, MAX_RECORD_BYTES, "record")
    if not signature_path.is_file():
        raise AllowanceRefused("unsigned allowance record")
    _read_bounded(signature_path, MAX_SIGNATURE_BYTES, "signature")
    _verify_signature(record, signature_path)
    return _parse_record(record)


def _read_bounded(path: Path, limit: int, label: str) -> bytes:
    try:
        with path.open("rb") as handle:
            data = handle.read(limit + 1)
    except OSError as exc:
        raise AllowanceRefused(f"allowance {label} is unreadable") from exc
    if len(data) > limit:
        raise AllowanceRefused(f"allowance {label} exceeds {limit} bytes")
    return data


def _require_trusted_path(path: Path, label: str, *, executable: bool = False) -> None:
    """Refuse a symlink, a non-regular file, an untrusted owner, or a writable path or ancestor."""
    trusted = {0, _TRUSTED_OWNER_UID}
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise AllowanceRefused(f"{label} is missing") from exc
    if stat.S_ISLNK(info.st_mode):
        raise AllowanceRefused(f"{label} is a symlink")
    if not stat.S_ISREG(info.st_mode):
        raise AllowanceRefused(f"{label} is not a regular file")
    if info.st_uid != _TRUSTED_OWNER_UID and not (executable and info.st_uid == 0):
        raise AllowanceRefused(f"{label} is not owned by root")
    if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise AllowanceRefused(f"{label} is group- or world-writable")
    for parent in Path(path).parents:
        try:
            parent_info = os.lstat(parent)
        except OSError as exc:
            raise AllowanceRefused(f"{label} has an unreadable parent directory") from exc
        if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
            raise AllowanceRefused(f"{label} has a parent that is not a real directory")
        if parent_info.st_uid not in trusted:
            raise AllowanceRefused(f"{label} has a parent directory not owned by root")
        writable = parent_info.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
        if writable and not parent_info.st_mode & stat.S_ISVTX:
            raise AllowanceRefused(f"{label} has a group- or world-writable parent directory")


def _verify_signature(record: bytes, signature_path: Path) -> None:
    signers = Path(_SIGNERS_PATH)
    keygen = Path(_SSH_KEYGEN)
    if not signers.is_absolute() or not keygen.is_absolute():
        raise AllowanceRefused("allowance trust anchors must be absolute paths")
    _require_trusted_path(signers, "allowance signer file")
    _require_trusted_path(keygen, "ssh-keygen", executable=True)
    command = [
        str(keygen),
        "-Y",
        "verify",
        "-f",
        str(signers),
        "-I",
        SIGNER_IDENTITY,
        "-n",
        SIGNATURE_NAMESPACE,
        "-s",
        str(signature_path),
    ]
    try:
        completed = subprocess.run(
            command,
            input=record,
            capture_output=True,
            timeout=VERIFY_TIMEOUT_S,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AllowanceRefused("allowance signature verification could not run") from exc
    if completed.returncode != 0:
        raise AllowanceRefused("allowance signature does not verify against the operator signer")


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise AllowanceRefused("allowance record repeats a key")
    return dict(pairs)


def _parse_time(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not _TIMESTAMP.fullmatch(value):
        raise AllowanceRefused(f"allowance {label} must be YYYY-MM-DDTHH:MM:SSZ")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError as exc:
        raise AllowanceRefused(f"allowance {label} is not a real time") from exc


def _format_time(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_record(record: bytes) -> OperatorAllowance:
    try:
        payload = json.loads(record.decode("utf-8"), object_pairs_hook=_reject_duplicates)
    except (UnicodeDecodeError, ValueError) as exc:
        if isinstance(exc, AllowanceRefused):
            raise
        raise AllowanceRefused("allowance record is not JSON") from exc
    if not isinstance(payload, dict) or set(payload) != _RECORD_KEYS:
        raise AllowanceRefused(f"allowance record must have exactly the keys {sorted(_RECORD_KEYS)}")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if record not in {canonical, canonical + b"\n"}:
        raise AllowanceRefused("allowance record is not canonical JSON")
    if payload["schema"] != ALLOWANCE_SCHEMA:
        raise AllowanceRefused("allowance record has an unsupported schema")
    if payload["activity"] != CONSULT_ACTIVITY:
        raise AllowanceRefused("an allowance admits only the consult activity")
    order_ref = payload["order_ref"]
    if not isinstance(order_ref, str) or not _IDENTIFIER.fullmatch(order_ref):
        raise AllowanceRefused("allowance order_ref must be a 1-200 character identifier")
    model = payload["model"]
    if not isinstance(model, str) or not _is_canonical_catalog_model(model):
        raise AllowanceRefused("allowance model must be a canonical catalog model id")
    issued_at = _parse_time(payload["issued_at"], "issued_at")
    expires_at = _parse_time(payload["expires_at"], "expires_at")
    if expires_at <= issued_at:
        raise AllowanceRefused("allowance expires_at must be after issued_at")
    scope = payload["scope"]
    if not isinstance(scope, dict):
        raise AllowanceRefused("allowance scope must be an object")
    task_id: str | None = None
    if scope == {"kind": "window"}:
        if expires_at - issued_at > MAX_WINDOW:
            raise AllowanceRefused("a window allowance lasts at most 24 hours")
    elif set(scope) == {"kind", "task_id"} and scope["kind"] == "task":
        task_id = scope["task_id"]
        if not isinstance(task_id, str) or not _IDENTIFIER.fullmatch(task_id):
            raise AllowanceRefused("allowance scope task_id must be a 1-200 character identifier")
    else:
        raise AllowanceRefused("allowance scope is exactly one task id or one window")
    return OperatorAllowance(
        model=model,
        activity=CONSULT_ACTIVITY,
        scope_kind=str(scope["kind"]),
        task_id=task_id,
        order_ref=order_ref,
        issued_at=issued_at,
        expires_at=expires_at,
        record_sha256=hashlib.sha256(record).hexdigest(),
        _seal=_SEAL,
    )


def _is_canonical_catalog_model(model: str) -> bool:
    from scripts.review.model_catalog import ModelCatalogError, load_model_catalog

    try:
        catalog = load_model_catalog()
    except (ModelCatalogError, OSError, ValueError):
        return False
    return model in catalog["models"]

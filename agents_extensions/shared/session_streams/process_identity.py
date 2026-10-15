"""Kernel-derived fingerprint of one lease-holder process incarnation (#10657).

A lease records ``holder.process_identity``: a typed, versioned public
identifier of the long-lived process that holds it. It is derived only from the
running kernel, never from the environment or from a value a caller nominates:

    v1:<sha256 of "lu-holder-process.v1", boot id, PID namespace, PID, start ticks>

joined by newlines. The boot id (``/proc/sys/kernel/random/boot_id``) differs
on every host and boot; the PID namespace separates containers sharing one
kernel; the start time in clock ticks since boot (``/proc/<pid>/stat`` field
22) separates a reused PID from its earlier owner.

Every input is world-readable, so the value is an identifier, not a secret or
a bearer credential: knowing it proves nothing. Holding is proven only by a
process that finds the fingerprinted process among its own kernel ancestors.
Machines without ``/proc`` cannot derive or prove an identity; both sides then
fail closed (no identity recorded, every proof refused).
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

PROCESS_IDENTITY_SCHEMA = "lu-holder-process.v1"
PROCESS_IDENTITY_RE = re.compile(r"^v1:[0-9a-f]{64}$")
_BOOT_ID = Path("/proc/sys/kernel/random/boot_id")
_BOOT_ID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_NAMESPACE_RE = re.compile(r"^pid:\[[0-9]+\]$")
_PROC_SELF = Path("/proc/self")


class ProcessIdentityUnavailable(ValueError):
    """The kernel facts an identity needs cannot be read or are inconsistent."""


def validate_process_identity(value: object) -> str:
    """Return ``value`` when it is a well-formed v1 identity; raise ``ValueError`` otherwise."""
    if not isinstance(value, str) or not PROCESS_IDENTITY_RE.fullmatch(value):
        raise ValueError("process_identity must be v1:<64 lowercase hex>")
    return value


def fingerprint(boot_id: str, namespace: str, pid: int, start_ticks: int) -> str:
    """The v1 identity of process ``pid`` started at ``start_ticks`` in ``namespace`` on boot ``boot_id``."""
    payload = "\n".join((PROCESS_IDENTITY_SCHEMA, boot_id, namespace, str(pid), str(start_ticks)))
    return "v1:" + hashlib.sha256(payload.encode("ascii")).hexdigest()


def _boot_id() -> str:
    value = _BOOT_ID.read_text(encoding="ascii").strip()
    if not _BOOT_ID_RE.fullmatch(value):
        raise ProcessIdentityUnavailable("kernel boot identity unavailable")
    return value


def _namespace() -> str:
    """This process's PID namespace; every ancestor visible through ``/proc`` shares it."""
    value = os.readlink(_PROC_SELF / "ns" / "pid")
    if not _NAMESPACE_RE.fullmatch(value):
        raise ProcessIdentityUnavailable("PID namespace identity unavailable")
    return value


def _stat(path: Path) -> tuple[int, int, int]:
    """``(pid, ppid, start_ticks)`` from a ``/proc/<pid>/stat`` file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    # comm is parenthesized and may contain spaces or ')'. The fields after the
    # final ')' start at state (field 3): ppid is field 4, starttime field 22.
    head, _, tail = text.rpartition(")")
    fields = tail.split()
    return int(head.split("(", 1)[0]), int(fields[1]), int(fields[19])


def _lineage() -> tuple[tuple[int, int], ...]:
    """``(pid, start_ticks)`` for this process and each visible ancestor, nearest first."""
    pid, ppid, start = _stat(_PROC_SELF / "stat")
    if pid != os.getpid():
        # /proc belongs to another PID namespace: its numbers are not ours.
        raise ProcessIdentityUnavailable("/proc does not describe this process")
    chain = [(pid, start)]
    seen = {pid}
    while ppid > 0 and ppid not in seen:
        found, parent, start = _stat(Path(f"/proc/{ppid}/stat"))
        if found != ppid:
            raise ProcessIdentityUnavailable("/proc returned another process")
        chain.append((ppid, start))
        seen.add(ppid)
        ppid = parent
    return tuple(chain)


def lineage_identity(pid: int) -> str:
    """The identity of ``pid`` if it is this process or one of its live kernel ancestors.

    The chain is read twice around the boot and namespace reads and must be
    identical: an ancestor that exits reparents its child, and a reused PID
    carries a later start time, so a stable chain proves every link held while
    the identity was computed. Raises ``ProcessIdentityUnavailable`` when the
    kernel facts are unreadable or moved, and ``LookupError`` when ``pid`` is
    not in the chain.
    """
    try:
        before = _lineage()
        boot, namespace = _boot_id(), _namespace()
        after = _lineage()
    except (OSError, ValueError, IndexError) as exc:
        if isinstance(exc, ProcessIdentityUnavailable):
            raise
        raise ProcessIdentityUnavailable("process ancestry or kernel identity unavailable") from None
    if before != after:
        raise ProcessIdentityUnavailable("process ancestry changed while it was read")
    starts = dict(after)
    if pid not in starts:
        raise LookupError("process is neither this process nor one of its ancestors")
    return fingerprint(boot, namespace, pid, starts[pid])


def parent_identity(pid: int) -> str | None:
    """The supervisor's derivation: the identity of ``pid`` only when it is this process's parent.

    The launcher runs the claim command directly, so the long-lived holder it
    names is the command's parent; the short-lived command itself is never
    fingerprinted. Any other PID, or any kernel fact that cannot be read, yields
    ``None``: the lease then records no identity and every proof against it
    refuses. Nothing here reads the environment.
    """
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 1 or os.getppid() != pid:
        return None
    try:
        identity = lineage_identity(pid)
    except (ProcessIdentityUnavailable, LookupError):
        return None
    # A parent that exited meanwhile would have reparented this process.
    return identity if os.getppid() == pid else None

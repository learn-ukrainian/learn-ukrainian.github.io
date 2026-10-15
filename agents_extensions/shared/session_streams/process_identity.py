"""Kernel-derived fingerprint of one lease-holder process incarnation (#10657).

A lease records ``holder.process_identity``: a typed, versioned public
identifier of the long-lived process that holds it. It is derived only from the
running kernel, never from the environment or from a value a caller nominates:

    v1:<sha256 of "lu-holder-process.v1", boot id, PID namespace, PID, start ticks>

joined by newlines. The boot id (``/proc/sys/kernel/random/boot_id``) differs
on every host and boot; the PID namespace separates containers sharing one
kernel; the start time in clock ticks since boot (``/proc/<pid>/stat`` field
22) separates a reused PID from its earlier owner.

Monitor derives the value itself when it accepts a claim
(``connected_peer_parent_identity``): from the kernel's view of the loopback
connection that carries the claim, it fingerprints the parent of the
connecting process, the launcher that runs the claim command. A claim that
carries the field is refused, so no client nominates it.

Every input is world-readable, so the value is an identifier, not a secret or
a bearer credential: knowing it proves nothing. Holding is proven only by a
process that finds the fingerprinted process among its own kernel ancestors.
Machines without ``/proc`` cannot derive or prove an identity; both sides then
fail closed (no identity recorded, every proof refused).
"""

from __future__ import annotations

import hashlib
import ipaddress
import os
import re
import struct
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


def _socket_inode(client: tuple[str, int], server: tuple[str, int]) -> int | None:
    """The inode of the connecting end of the established TCP connection ``client`` → ``server``.

    Read from this network namespace's kernel socket tables; IPv4-mapped
    addresses compare as IPv4. ``None`` unless exactly one socket matches.
    """
    want = (_address(client[0]), client[1], _address(server[0]), server[1])
    found = set()
    for table, width in ((_PROC_SELF / "net" / "tcp", 4), (_PROC_SELF / "net" / "tcp6", 16)):
        try:
            lines = table.read_text(encoding="ascii").splitlines()[1:]
        except OSError:
            continue
        for line in lines:
            fields = line.split()
            # Field 3 is the state; 01 is ESTABLISHED. Field 9 is the inode.
            if len(fields) < 10 or fields[3] != "01":
                continue
            local, remote = _endpoint(fields[1], width), _endpoint(fields[2], width)
            if (*local, *remote) == want and fields[9].isdigit() and int(fields[9]) > 0:
                found.add(int(fields[9]))
    return found.pop() if len(found) == 1 else None


def _address(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    address = ipaddress.ip_address(value)
    mapped = getattr(address, "ipv4_mapped", None)
    return mapped if mapped is not None else address


def _endpoint(text: str, width: int) -> tuple[ipaddress.IPv4Address | ipaddress.IPv6Address, int]:
    """``ADDR:PORT`` as the kernel prints it: 32-bit words in host byte order, port in hex."""
    address, port = text.split(":")
    if len(address) != width * 2:
        raise ValueError("socket table address width mismatch")
    raw = b"".join(struct.pack("=I", int(address[i : i + 8], 16)) for i in range(0, len(address), 8))
    return _address(str(ipaddress.ip_address(raw))), int(port, 16)


def _socket_owners(inode: int) -> set[int]:
    """Every process whose descriptor table this process can read and that holds socket ``inode``."""
    link = f"socket:[{inode}]"
    owners = set()
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            descriptors = os.listdir(f"/proc/{entry}/fd")
        except OSError:
            continue
        for descriptor in descriptors:
            try:
                if os.readlink(f"/proc/{entry}/fd/{descriptor}") == link:
                    owners.add(int(entry))
                    break
            except OSError:
                continue
    return owners


def connected_peer_parent_identity(client: tuple[str, int], server: tuple[str, int], parent_pid: int) -> str | None:
    """Monitor's derivation: the identity of the parent of the process at the far end of a connection.

    Monitor calls this for an accepted loopback connection (``client`` is the
    peer's address, ``server`` the address it connected to). The kernel names
    the connecting socket, the one process holding it and that process's
    parent. The identity is returned only when that parent is ``parent_pid``,
    the holder PID the claim records: the launcher runs the claim command as
    its direct child, so a lease records the launcher it names and nothing a
    caller nominates. ``None`` when anything is ambiguous or unreadable (a
    shared socket, a peer in another PID or network namespace, a proxy, a
    process this one may not inspect, or a parent other than ``parent_pid``):
    the lease then records no identity and every proof against it refuses.
    """
    if isinstance(parent_pid, bool) or not isinstance(parent_pid, int) or parent_pid <= 1:
        return None
    try:
        inode = _socket_inode(client, server)
        owners = _socket_owners(inode) if inode is not None else set()
        if len(owners) != 1:
            return None
        peer = owners.pop()
        if _stat(_PROC_SELF / "stat")[0] != os.getpid():
            return None  # /proc belongs to another PID namespace.
        before = _stat(Path(f"/proc/{peer}/stat"))
        if before[0] != peer or before[1] != parent_pid:
            return None
        found, _, start = _stat(Path(f"/proc/{parent_pid}/stat"))
        boot, namespace = _boot_id(), _namespace()
        # The parent exiting (or its PID being reused) meanwhile reparents the
        # peer; the peer exiting changes its start time or removes it.
        if found != parent_pid or _stat(Path(f"/proc/{peer}/stat")) != before:
            return None
    except (OSError, ValueError, IndexError):
        return None
    return fingerprint(boot, namespace, parent_pid, start)

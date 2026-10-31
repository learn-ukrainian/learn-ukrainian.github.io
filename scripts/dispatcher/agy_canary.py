"""Projected canary for the read-only AGY sandbox (C-3027).

The parent copies this file into the sandbox's read-only boundary directory and runs it as the
sandbox's first process, after bubblewrap has finished every mount. It tries each planned syscall,
reports the outcomes on an inherited descriptor and starts AGY only when the parent, having checked
the report itself, answers with the go byte. Its fixed read probe imports only the projected trusted store contracts and locality dependency.
"""

from __future__ import annotations

import errno
import json
import os
import socket
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class StoreReadResult:
    status: Literal["read", "refused"]
    store: str
    reason: str | None = None


def _read_store(store: str, repository: str) -> StoreReadResult:
    """One fixed contract probe; no caller-supplied code, SQL or import location."""
    if store not in {"sources", "vesum"}:
        return StoreReadResult("refused", store, "unsupported_read_store")
    sys.path.insert(0, str(Path(__file__).parent / "store_contract"))
    import sqlite3

    from scripts.lib.readonly_sqlite import open_readonly
    from scripts.storage.topology import StoreRefusal, resolve_store

    binding = resolve_store(store, Path(repository), env={})
    if isinstance(binding, StoreRefusal):
        return StoreReadResult("refused", store, binding.reason)
    try:
        connection = open_readonly(binding.path)
        try:
            connection.execute("SELECT count(*) FROM sqlite_master").fetchone()
        finally:
            connection.close()
    except sqlite3.Error as error:
        try:
            with binding.path.open("rb") as stream:
                header = stream.read(20)
            missing_shm = not binding.path.with_name(binding.path.name + "-shm").exists()
        except OSError:
            return StoreReadResult("refused", store, "store_unavailable")
        if (header.startswith(b"SQLite format 3\0") and header[18:20] == b"\x02\x02" and missing_shm
                and getattr(error, "sqlite_errorcode", 0) & 0xff in {sqlite3.SQLITE_READONLY, sqlite3.SQLITE_CANTOPEN}):
            return StoreReadResult("refused", store, "wal_sidecars_unavailable")
        return StoreReadResult("refused", store, "store_unavailable")
    except OSError:
        return StoreReadResult("refused", store, "store_unavailable")
    return StoreReadResult("read", store)


def _attempt(op: str, path: str, port: int | None, store: str | None = None) -> str | dict:
    """Run one probe; the errno name of its failure, or ``OK``."""
    try:
        if op == "store_read":
            return asdict(_read_store(store or "", path))
        if op == "write_open":
            os.close(os.open(path, os.O_WRONLY | os.O_CLOEXEC))
        elif op == "create":
            os.close(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o600))
        elif op == "mkdir":
            os.mkdir(path, 0o700)
        elif op == "rename":
            os.rename(path, path + ".moved")
        elif op == "unlink":
            os.unlink(path)
        elif op == "chmod":
            # The owner may always chmod, so re-applying the current mode fails only on a read-only mount.
            os.chmod(path, os.stat(path).st_mode & 0o7777)
        elif op == "stat":
            os.stat(path)
        elif op == "scratch_cycle":
            # Positive control: the private scratch must take a create, write, rename and delete.
            moved = path + ".moved"
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC, 0o600)
            try:
                os.write(descriptor, b"canary")
            finally:
                os.close(descriptor)
            os.rename(path, moved)
            os.unlink(moved)
        elif op in ("connect_tcp", "connect_abstract", "connect_unix"):
            family = socket.AF_INET if op == "connect_tcp" else socket.AF_UNIX
            with socket.socket(family, socket.SOCK_STREAM) as probe:
                probe.settimeout(2)
                probe.connect((path, port) if op == "connect_tcp" else ("\0" + path if op == "connect_abstract" else path))
        else:
            return "UNKNOWN_OP"
    except OSError as exc:
        return errno.errorcode.get(exc.errno, str(exc.errno)) if exc.errno else type(exc).__name__
    return "OK"


def main() -> int:
    plan_path, command = sys.argv[1], sys.argv[3:]
    if sys.argv[2] != "--" or not command:
        return 125
    with open(plan_path, encoding="utf-8") as handle:
        plan = json.load(handle)
    outcomes = [
        {**probe, "outcome": _attempt(probe["op"], probe["path"], probe.get("port"), probe.get("store"))}
        for probe in plan["probes"]
    ]
    with os.fdopen(plan["report_fd"], "w", encoding="utf-8") as report:
        report.write(json.dumps({"pid": os.getpid(), "probes": outcomes}))
    with os.fdopen(plan["go_fd"], "rb") as go:
        answer = go.read(1)
    if answer != b"1":
        return 125
    # Nothing the launcher held may reach AGY: only stdin, stdout and stderr stay open.
    os.closerange(3, os.sysconf("SC_OPEN_MAX"))
    os.execv(command[0], command)
    return 125  # unreachable: execv replaces this process or raises


if __name__ == "__main__":
    raise SystemExit(main())

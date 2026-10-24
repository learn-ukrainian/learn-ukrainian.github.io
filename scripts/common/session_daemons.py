"""Narrow exceptions for unreadable same-uid session daemons during holder scans."""

from __future__ import annotations

import os
from pathlib import Path

_ARGV0_ALLOWLIST = frozenset({b"/usr/bin/ssh-agent", b"/usr/bin/gpg-agent", b"(sd-pam)"})


def allowed_session_daemon(entry: Path) -> str | None:
    """Return the allowed argv[0], or None when identity is unknown or unlisted.

    Call only after holder inspection fails. UID comes from status because a
    non-dumpable process's proc directory may be root-owned. Matching argv[0]
    is intentionally spoofable by the same uid that already owns the trees.
    """
    try:
        status = (entry / "status").read_bytes().splitlines()
        uids = next((line.partition(b":")[2].split() for line in status if line.startswith(b"Uid:")), [])
        if uids[:3] != [str(os.getuid()).encode()] * 3:
            return None
        argv = (entry / "cmdline").read_bytes().split(b"\0")
    except OSError:
        return None
    argv0 = argv[0]
    if argv0 in _ARGV0_ALLOWLIST or argv0.startswith(b"sshd-session:"):
        return os.fsdecode(argv0)
    if argv0 == b"/usr/lib/systemd/systemd" and b"--user" in argv[1:]:
        return os.fsdecode(argv0)
    return None

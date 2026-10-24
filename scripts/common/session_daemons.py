"""Narrow exceptions for unreadable same-uid session daemons during holder scans."""

from __future__ import annotations

import os
from pathlib import Path

_AGENT_UNITS = {"ssh-agent.service": "ssh-agent", "gpg-agent.service": "gpg-agent"}


def _status(entry: Path) -> dict[str, str]:
    text = (entry / "status").read_text(encoding="utf-8", errors="replace")
    return {key: value.strip() for key, _, value in (line.partition(":") for line in text.splitlines()) if value}


def allowed_session_daemon(entry: Path) -> str | None:
    """Return a kernel-fact daemon identity, or None when it cannot be established.

    Call only after holder inspection fails. UID comes from status because a
    non-dumpable process's proc directory may be root-owned. Preserve the
    reaper's init.scope and root-sshd-parent exceptions. Agents additionally
    require their own exact unit cgroup and the user's systemd parent.
    No decision depends on the process-controlled command line.
    """
    try:
        uid = os.getuid()
        status = _status(entry)
        if status.get("Uid", "").split()[:3] != [str(uid)] * 3:
            return None
        cgroup = (entry / "cgroup").read_text(encoding="utf-8", errors="replace").splitlines()
        user_group = f"0::/user.slice/user-{uid}.slice/user@{uid}.service"
        manager_group = [f"{user_group}/init.scope"]
        if cgroup == manager_group:
            return status.get("Name") or "init.scope"
        sshd = {"sshd-session", "sshd"}
        agent = next((name for unit, name in _AGENT_UNITS.items() if cgroup == [f"{user_group}/app.slice/{unit}"]), None)
        if status.get("Name") not in sshd and status.get("Name") != agent:
            return None
        ppid = status.get("PPid", "")
        if not ppid.isascii() or not ppid.isdecimal():
            return None
        parent_entry = entry.parent / ppid
        parent = _status(parent_entry)
        if status.get("Name") in sshd:
            if parent.get("Name") in sshd and parent.get("Uid", "").split()[:1] == ["0"]:
                return status["Name"]
            return None
        if (agent is not None and parent.get("Name") == "systemd"
                and parent.get("Uid", "").split()[:3] == [str(uid)] * 3
                and (parent_entry / "cgroup").read_text(encoding="utf-8", errors="replace").splitlines() == manager_group):
            return agent
    except OSError:
        return None
    return None

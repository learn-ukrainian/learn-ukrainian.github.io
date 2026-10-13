#!/bin/sh
# ACP Claude seat launcher (#10500): the adapter reads this file only from the
# canonical primary checkout, pins its SHA-256, writes the verified bytes to a
# private per-launch copy that CLAUDE_CODE_EXECUTABLE names, and validates the
# pinned host Claude Code before every launch. It sources and execs no
# repository file; one it gains joins the adapter's digest closure and is
# copied beside it. Editing this file changes that digest.
# ACPX cannot pass a tool deny and --deny-all never covers
# tools that run without asking, so the headless background denies (#9690) are
# added here; the SDK's own --disallowedTools follows in "$@" and accumulates.
host=${LU_CLAUDE_ACP_HOST-}
identity=${LU_CLAUDE_ACP_HOST_IDENTITY-}
unset LU_CLAUDE_ACP_HOST LU_CLAUDE_ACP_HOST_IDENTITY
case $host in /*) ;; *) echo "claude_acp_exec: pinned Claude Code path is missing or relative" >&2; exit 126 ;; esac
case $identity in *:*:*:*:*) ;; *) echo "claude_acp_exec: pinned Claude Code identity is missing" >&2; exit 126 ;; esac
# Device, inode, size, and mtime and ctime in nanoseconds: an in-place edit after
# the version probe changes ctime. Only GNU stat prints exact nanoseconds; Ubuntu
# installs it as gnustat when stat is the uutils one, which rounds them.
stat=/usr/bin/gnustat
[ -x "$stat" ] || stat=/usr/bin/stat
[ "$("$stat" -c %d:%i:%s:%.9Y:%.9Z -- "$host" 2>/dev/null)" = "$identity" ] || { echo "claude_acp_exec: pinned Claude Code changed since its version probe, or this host lacks GNU stat" >&2; exit 126; }
exec "$host" --disallowedTools Monitor,ScheduleWakeup,CronCreate,Workflow "$@"

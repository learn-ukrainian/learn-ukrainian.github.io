#!/bin/sh
# ACP Claude seat launcher (#10500): the adapter points CLAUDE_CODE_EXECUTABLE
# here and validates this file, its parents and the pinned host Claude Code
# before every launch. ACPX cannot pass a tool deny and --deny-all never covers
# tools that run without asking, so the headless background denies (#9690) are
# added here; the SDK's own --disallowedTools follows in "$@" and accumulates.
host=${LU_CLAUDE_ACP_HOST-}
identity=${LU_CLAUDE_ACP_HOST_DEV_INO-}
unset LU_CLAUDE_ACP_HOST LU_CLAUDE_ACP_HOST_DEV_INO
case $host in /*) ;; *) echo "claude_acp_exec: pinned Claude Code path is missing or relative" >&2; exit 126 ;; esac
case $identity in *:*) ;; *) echo "claude_acp_exec: pinned Claude Code identity is missing" >&2; exit 126 ;; esac
[ "$(/usr/bin/stat -c %d:%i -- "$host" 2>/dev/null)" = "$identity" ] || { echo "claude_acp_exec: pinned Claude Code changed since its version probe" >&2; exit 126; }
exec "$host" --disallowedTools Monitor,ScheduleWakeup,CronCreate,Workflow "$@"

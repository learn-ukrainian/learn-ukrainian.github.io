#!/bin/bash
# Launch a Claude session as the INFRA / CODE driver — NOT the folk/seminar Claude and
# NOT a curriculum track-orchestrator.
#
# Handoff identity: `claude-infra` (exported as SESSION_HANDOFF_AGENT). The SessionStart
# hook (agents_extensions/shared/hooks/session-setup.sh) keys the cold-start thread handoff
# off this variable, so the infra lane reads/writes its OWN slot
# (.agent/claude-infra-thread-handoff.md) instead of the shared `claude` slot that the folk
# driver and the track-orchestrators (start-bio-driver.sh etc.) also land on. Without this,
# every Claude session defaults to agent `claude` and they clobber each other's handoff.
#
# Everything else (skills deploy, native-install launch, --chrome, bypassPermissions,
# Headroom routing, autocompact window) is inherited from start-claude.sh.
#
# See docs/session-state/current.claude-infra.md for the lane's role + cold-start.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SESSION_HANDOFF_AGENT=claude-infra
exec "$ROOT/start-claude.sh" "$@"

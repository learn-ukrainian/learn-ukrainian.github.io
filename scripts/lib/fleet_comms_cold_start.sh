#!/usr/bin/env bash
# fleet_comms_cold_start.sh — shared dual-aware fleet-comms cold-start helpers for launchers.
#
# Binding doctrine: agents_extensions/shared/rules/fleet-comms-coordination.md
# (also served at GET /api/rules). Launchers inject a short pointer; they must not
# invent a competing design or flip plane/stream/eligibility cutovers.
#
# Usage (from a start-*.sh after PROJECT_DIR is set):
#   # shellcheck source=scripts/lib/fleet_comms_cold_start.sh
#   source "$PROJECT_DIR/scripts/lib/fleet_comms_cold_start.sh"
#   export FLEET_COMMS_PLANE_MODE="$(fleet_comms_resolve_plane_mode)"
#   fleet_comms_print_banner_line   # optional compact operator line
#   _clause="$(fleet_comms_cold_clause)"  # append into cold-start prompts

# shellcheck disable=SC2034  # PROJECT_DIR is provided by the sourcing launcher

fleet_comms_rule_relpath() {
  printf '%s' "agents_extensions/shared/rules/fleet-comms-coordination.md"
}

# Resolve plane mode once (fail-open → off).
fleet_comms_resolve_plane_mode() {
  local mode="off"
  local root="${PROJECT_DIR:-.}"
  if [ -x "$root/.venv/bin/python" ] \
      && [ -f "$root/scripts/fleet_comms/message_plane.py" ]; then
    mode="$(
      "$root/.venv/bin/python" -c \
        'from scripts.fleet_comms.message_plane import resolve_plane_mode; print(resolve_plane_mode(None))' \
        2>/dev/null || true
    )"
    case "${mode}" in
      off|shadow|dual_write) ;;
      *) mode="off" ;;
    esac
  fi
  printf '%s' "$mode"
}

# Compact dual-aware clause for injected cold-start prompts.
fleet_comms_cold_clause() {
  local plane_mode="${FLEET_COMMS_PLANE_MODE:-off}"
  local rule
  rule="$(fleet_comms_rule_relpath)"
  printf '%s' \
    "Fleet-comms (#5512) mid-cutover — obey ${rule} (also in /api/rules). " \
    "Prefer message-plane + CF surfaces; fall back to file dual-write while plane mode is ${plane_mode} " \
    "(do not flip cutovers without operator/advisor GO; do not invent a competing design). " \
    "Topology: \`.venv/bin/python -m scripts.fleet_comms plane-status\` (+ metrics/backlog/dead-letters). " \
    "Formal CF: \`.venv/bin/python -m scripts.ai_agent_bridge review-pr <N>\` then publish-review-verdict " \
    "(cross-family; never self-seal). Continuity: stream lease already claimed; dual-write " \
    "\`.claude/<epic>-epic/*-DRIVER-HANDOFF.md\` remains authoritative until stream-authority cutover."
}

# One-line operator banner (stdout). Safe when FLEET_COMMS_PLANE_MODE unset (resolves off).
fleet_comms_print_banner_line() {
  local plane_mode="${FLEET_COMMS_PLANE_MODE:-}"
  if [ -z "$plane_mode" ]; then
    plane_mode="$(fleet_comms_resolve_plane_mode)"
  fi
  case "$plane_mode" in
    off)
      echo "  fleet-comms: plane=off → file dual-write fallback; CF via review-pr; rule=$(fleet_comms_rule_relpath)"
      ;;
    shadow|dual_write)
      echo "  fleet-comms: plane=${plane_mode} → prefer plane; keep diary dual-write until authority cutover; rule=$(fleet_comms_rule_relpath)"
      ;;
    *)
      echo "  fleet-comms: plane=${plane_mode} (unknown) → treat as off; rule=$(fleet_comms_rule_relpath)"
      ;;
  esac
}

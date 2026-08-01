#!/usr/bin/env bash
# fleet_comms_cold_start.sh — shared authority-aware fleet-comms cold-start helpers.
#
# Binding doctrine: agents_extensions/shared/rules/fleet-comms-coordination.md
# (also served at GET /api/rules). Method playbook: drive-epic skill (#5632).
# Authority cutover approved by the operator in #6159 on 2026-08-01.
#
# Usage (from a start-*.sh after PROJECT_DIR is set):
#   # shellcheck source=scripts/lib/fleet_comms_cold_start.sh
#   source "$PROJECT_DIR/scripts/lib/fleet_comms_cold_start.sh"
#   export FLEET_COMMS_PLANE_MODE="$(fleet_comms_resolve_plane_mode)"
#   fleet_comms_print_banner_line
#   _clause="$(fleet_comms_cold_clause)"

# shellcheck disable=SC2034  # PROJECT_DIR is provided by the sourcing launcher

# Select ACP for eligible `ab discuss` calls without starting any process.
export LU_AGENT_COMM_TRANSPORT="${LU_AGENT_COMM_TRANSPORT:-acp}"

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
      off|shadow|dual_write|authority) ;;
      *) mode="off" ;;
    esac
  fi
  printf '%s' "$mode"
}

# Compact authority-aware clause for injected cold-start prompts.
fleet_comms_cold_clause() {
  local plane_mode="${FLEET_COMMS_PLANE_MODE:-off}"
  local rule
  rule="$(fleet_comms_rule_relpath)"
  printf '%s' \
    "Fleet-comms (#6159) authority cutover — obey ${rule} (also in /api/rules). " \
    "Method playbook: load skill drive-epic (provider drivers inject the binding after lease + canary). " \
    "Use fleet-comms as communication authority when current mode=${plane_mode}; " \
    "legacy bridge/channel stores are read-only migration projections in authority mode. " \
    "Topology: \`.venv/bin/python -m scripts.fleet_comms plane-status\` (+ metrics/backlog/dead-letters). " \
    "Formal CF: \`.venv/bin/python -m scripts.ai_agent_bridge review-pr <PR_NUMBER> --reviewer <cross-family>\` " \
    "then publish-review-verdict (PR number required; never self-seal). " \
    "All normal inter-agent asks, 2–6 seat discussions, and sealed formal review provider calls use ACP; " \
    "never fall back to bridge/provider execution. ACP transports; fleet-comms owns durable state. " \
    "Continuity: stream lease already claimed; write durable receipts to fleet-comms."
}

# One-line operator banner (stdout).
fleet_comms_print_banner_line() {
  local plane_mode="${FLEET_COMMS_PLANE_MODE:-}"
  if [ -z "$plane_mode" ]; then
    plane_mode="$(fleet_comms_resolve_plane_mode)"
  fi
  case "$plane_mode" in
    off)
      echo "  fleet-comms: plane=off · diary authoritative · CF via review-pr · rule=$(fleet_comms_rule_relpath) · skill=drive-epic"
      ;;
    shadow|dual_write)
      echo "  fleet-comms: plane=${plane_mode} (compatibility soak) · rule=$(fleet_comms_rule_relpath) · skill=drive-epic"
      ;;
    authority)
      echo "  fleet-comms: plane=authority · ACP transport · legacy read-only · rule=$(fleet_comms_rule_relpath) · skill=drive-epic"
      ;;
    *)
      echo "  fleet-comms: plane=${plane_mode} (unknown→treat off) · rule=$(fleet_comms_rule_relpath)"
      ;;
  esac
}

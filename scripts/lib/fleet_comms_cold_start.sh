#!/usr/bin/env bash
# fleet_comms_cold_start.sh — shared dual-aware fleet-comms cold-start helpers for launchers.
#
# Binding doctrine: agents_extensions/shared/rules/fleet-comms-coordination.md
# (also served at GET /api/rules). Method playbook: drive-epic skill (#5632).
# Aligned with Sol CF on #5632: file handoffs stay authoritative in every plane mode;
# dual_write is not stream-authority cutover.
#
# Usage (from a start-*.sh after PROJECT_DIR is set):
#   # shellcheck source=scripts/lib/fleet_comms_cold_start.sh
#   source "$PROJECT_DIR/scripts/lib/fleet_comms_cold_start.sh"
#   export FLEET_COMMS_PLANE_MODE="$(fleet_comms_resolve_plane_mode)"
#   fleet_comms_print_banner_line
#   _clause="$(fleet_comms_cold_clause)"

# shellcheck disable=SC2034  # PROJECT_DIR is provided by the sourcing launcher

fleet_comms_rule_relpath() {
  printf '%s' "agents_extensions/shared/rules/fleet-comms-coordination.md"
}

# Resolve plane mode once (fail-open → off). Modes: off|shadow|dual_write only.
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

# Compact dual-aware clause for injected cold-start prompts (post-#5632 Sol-aligned).
fleet_comms_cold_clause() {
  local plane_mode="${FLEET_COMMS_PLANE_MODE:-off}"
  local rule
  rule="$(fleet_comms_rule_relpath)"
  printf '%s' \
    "Fleet-comms (#5512) mid-cutover — obey ${rule} (also in /api/rules). " \
    "Method playbook: load skill drive-epic (start-*-drive.sh does not auto-load it yet). " \
    "Prefer plane + CF surfaces; file dual-write diary stays authoritative in every plane mode " \
    "(current mode=${plane_mode}; dual_write is shadow/mirror, not authority cutover — " \
    "do not flip cutovers or invent a competing design). " \
    "Topology: \`.venv/bin/python -m scripts.fleet_comms plane-status\` (+ metrics/backlog/dead-letters). " \
    "Formal CF: \`.venv/bin/python -m scripts.ai_agent_bridge review-pr <PR_NUMBER> --reviewer <cross-family>\` " \
    "then publish-review-verdict (PR number required; never self-seal). " \
    "Continuity: stream lease already claimed; dual-write \`.claude/<epic>-epic/*-DRIVER-HANDOFF.md\`."
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
      echo "  fleet-comms: plane=${plane_mode} (shadow/mirror; diary still authoritative) · rule=$(fleet_comms_rule_relpath) · skill=drive-epic"
      ;;
    *)
      echo "  fleet-comms: plane=${plane_mode} (unknown→treat off) · rule=$(fleet_comms_rule_relpath)"
      ;;
  esac
}

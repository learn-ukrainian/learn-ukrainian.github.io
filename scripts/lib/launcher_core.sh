#!/usr/bin/env bash
# Shared lifecycle for the public launcher estate. Provider adapters own every
# route, credential, endpoint, and binary decision; this file owns only the
# uniform public CLI and driver lifecycle.

launcher_usage() {
  local name="start-${LC_PROVIDER}${LC_MODE:+-${LC_MODE}}.sh"
  local driver_mode provider_env example_three
  if [ "$LC_MODE" = "interactive" ]; then
    name="start-${LC_PROVIDER}.sh"
  fi
  case "$LC_PROVIDER" in
    kimi|glm)
      driver_mode="  driver       No certified ${LC_PROVIDER} driver entrypoint is available."
      ;;
    *)
      driver_mode="  driver       Validates a certified model and lane, claims its lease, runs the
               provider canary, then injects the drive-epic binding."
      ;;
  esac
  case "$LC_PROVIDER" in
    claude) provider_env='  CLAUDE_CODE_*            Claude Code session configuration (route-shaped values are cleared).' ;;
    codex) provider_env='  CODEX_CC_BASE_URL, CODEX_CC_AUTH_TOKEN
                             Approved local-proxy settings for --harness claude-code.' ;;
    gemini) provider_env='  AGY_*                    AGY-managed Gemini authentication and configuration.' ;;
    grok) provider_env='  GROK_*                   Grok CLI authentication and configuration.' ;;
    kimi) provider_env='  KIMICC_AUTH_TOKEN, MOONSHOT_API_KEY, KIMI_API_KEY
                             Explicit Kimi credentials for --harness claude-code.' ;;
    glm) provider_env='  GLMCC_AUTH_TOKEN, ZAI_API_KEY, ZHIPU_API_KEY, GLM_API_KEY
                             Explicit GLM credentials (preferred over the secret file).
  ~/.secret/zai.key        Owner-only fallback (mode 0600/0400) when env is unset.
  GLMCC_SECRET_FILE        Override path for the file-backed Z.AI key.' ;;
  esac
  case "$LC_PROVIDER:$LC_MODE" in
    kimi:interactive) example_three='./start-kimicc.sh --endpoint coding' ;;
    glm:interactive) example_three='./start-glmcc.sh --endpoint coding' ;;
    *:driver) example_three="./${name} --epic devops" ;;
    *) example_three="./start-${LC_PROVIDER}-driver.sh --epic devops" ;;
  esac
  cat <<EOF
Usage: ./${name} [OPTIONS] [PROMPT ...] [-- PROVIDER_ARGS ...]

Launch ${LC_PROVIDER} through the approved provider adapter. Use a -driver
entrypoint only for an epic-driving session; interactive launchers never claim leases.

Modes:
  interactive  Starts a provider session. --epic is rejected.
$driver_mode

Options:
  -h, --help                 Show this help and exit.
  --model MODEL              Provider model (default: ${LC_MODEL:-provider default}).
  --harness HARNESS          Provider harness (default: ${LC_HARNESS}).
  --epic SELECTOR            Driver lane only; for example: devops or atlas.
  --governor SELECTOR        Codex driver only; one lease-free Sol cycle (AUTO allowed).
  --endpoint NAME            Kimi/GLM route endpoint: coding or platform.
  --isolate-config           Kimi/GLM Claude-Code config isolation (default).
  --no-isolate-config        Use the existing Claude-Code config only when route-safe.
  --                         Pass all remaining arguments verbatim to the provider CLI.

Environment:
  LAUNCHER_DRY_RUN=1         Validate the route and print a redacted exact would-exec argv.
  LAUNCHER_MODEL             Default model when --model is omitted.
  LAUNCHER_HARNESS           Default harness when --harness is omitted.
$provider_env

EXIT CODES:
  0  Launch completed, help shown, or dry-run succeeded.
  1  Launch refused on a continuity precondition (rollover ambiguity or lease).
  2  Usage error (unknown flag, unsupported harness, or invalid selector).
  3  Required provider credential or executable is unavailable.
  4  Driver certification is missing or revoked.
  5  Provider transport is degraded; use the stated external-fleet disposition.

Examples:
  ./start-${LC_PROVIDER}.sh --help
  LAUNCHER_DRY_RUN=1 ./start-${LC_PROVIDER}.sh --model ${LC_MODEL:-MODEL}
  $example_three
EOF
  if [ "$LC_MODE" = "driver" ]; then
    cat <<'EOF'

Valid lane selectors:
  infra | harness | infra.fleet-comms
  devops | infra.devops
  atlas | practice | atlas.practice
  hramatka | hramatka.lessons
  folk | seminars-folk
  bio | seminars-bio
  corpus | corpus-channels
EOF
  fi
}

launcher_error() {
  printf 'Error: %s\n' "$*" >&2
}

launcher_require_binary() {
  local binary="$1"
  local error_message="$2"
  local exit_code="$3"

  if [ "$LC_DRY_RUN" = "1" ]; then
    printf 'LAUNCHER_DRY_RUN=1: would require binary %s\n' "$binary"
    return 0
  fi
  command -v "$binary" >/dev/null 2>&1 || {
    launcher_error "$error_message"
    return "$exit_code"
  }
}

launcher_clear_foreign_route_state() {
  # A route-shaped value inherited by a public launcher is foreign. Adapters set
  # their own process-scoped values only after this cleanup; credentials with
  # provider-specific names remain available for adapter selection.
  unset ANTHROPIC_BASE_URL ANTHROPIC_AUTH_TOKEN ANTHROPIC_API_KEY
  unset ANTHROPIC_MODEL ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_SONNET_MODEL
  unset ANTHROPIC_DEFAULT_HAIKU_MODEL ANTHROPIC_DEFAULT_FABLE_MODEL
  unset CLAUDE_CODE_SUBAGENT_MODEL CLAUDE_CODE_EFFORT_LEVEL
  unset CLAUDE_CODE_MAX_CONTEXT_TOKENS CLAUDE_CODE_AUTO_COMPACT_WINDOW
  unset CLAUDE_CODE_API_KEY_HELPER_TTL_MS API_TIMEOUT_MS
  # Provider-selector switches (Bedrock/Vertex/Foundry/Mantle/AWS) must not
  # survive into an alternate Claude-Code route — settings env can also pin
  # them, which the route guard refuses separately.
  unset CLAUDE_CODE_USE_BEDROCK CLAUDE_CODE_USE_VERTEX CLAUDE_CODE_USE_FOUNDRY
  unset CLAUDE_CODE_USE_MANTLE CLAUDE_CODE_USE_ANTHROPIC_AWS
  unset LEARN_UKRAINIAN_TRANSPORT LEARN_UKRAINIAN_REQUESTED_PROFILE_ID
  unset LEARN_UKRAINIAN_CLAUDEX_MANAGED_LAUNCH LEARN_UKRAINIAN_KIMICC_MANAGED_LAUNCH
  unset LEARN_UKRAINIAN_GLMCC_MANAGED_LAUNCH
}

launcher_defaults() {
  case "$LC_PROVIDER" in
    claude)
      LC_MODEL="${LAUNCHER_MODEL:-claude-fable-5}"
      LC_HARNESS="${LAUNCHER_HARNESS:-claude-code}"
      ;;
    codex)
      LC_MODEL="${LAUNCHER_MODEL:-gpt-5.6-terra}"
      LC_HARNESS="${LAUNCHER_HARNESS:-codex}"
      ;;
    gemini)
      LC_MODEL="${LAUNCHER_MODEL:-gemini-3.6-flash-high}"
      LC_HARNESS="${LAUNCHER_HARNESS:-agy}"
      ;;
    grok)
      LC_MODEL="${LAUNCHER_MODEL:-grok-4.5}"
      LC_HARNESS="${LAUNCHER_HARNESS:-grok}"
      ;;
    kimi)
      LC_MODEL="${LAUNCHER_MODEL:-k3}"
      LC_HARNESS="${LAUNCHER_HARNESS:-kimi-code}"
      ;;
    glm)
      LC_MODEL="${LAUNCHER_MODEL:-glm-5.2}"
      LC_HARNESS="${LAUNCHER_HARNESS:-claude-code}"
      ;;
    *) launcher_error "unknown provider '$LC_PROVIDER'"; exit 2 ;;
  esac
  LC_ENDPOINT="${LAUNCHER_ENDPOINT:-coding}"
  LC_ISOLATE_CONFIG="${LAUNCHER_ISOLATE_CONFIG:-1}"
  LC_DRY_RUN="${LAUNCHER_DRY_RUN:-0}"
  LC_EPIC=""
  LC_GOVERNOR="0"
  LC_FORWARD_ARGS=()
}

launcher_need_value() {
  if [ -z "${2:-}" ]; then
    launcher_error "$1 requires a value; run --help."
    exit 2
  fi
}

launcher_parse() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      -h|--help)
        launcher_usage
        exit 0
        ;;
      --)
        shift
        while [ "$#" -gt 0 ]; do
          LC_FORWARD_ARGS+=("$1")
          shift
        done
        ;;
      --model)
        launcher_need_value "$1" "${2:-}"
        LC_MODEL="$2"
        shift 2
        ;;
      --model=*) LC_MODEL="${1#*=}"; shift ;;
      --harness)
        launcher_need_value "$1" "${2:-}"
        LC_HARNESS="$2"
        shift 2
        ;;
      --harness=*) LC_HARNESS="${1#*=}"; shift ;;
      --epic)
        launcher_need_value "$1" "${2:-}"
        LC_EPIC="$2"
        shift 2
        ;;
      --epic=*) LC_EPIC="${1#*=}"; shift ;;
      --governor)
        # Preserve the historical `--governor --help` form: help is a launcher
        # request, not a selector named "--help".
        if [ "${2:-}" = "-h" ] || [ "${2:-}" = "--help" ]; then
          shift
          continue
        fi
        launcher_need_value "$1" "${2:-}"
        LC_GOVERNOR="1"
        LC_EPIC="$2"
        shift 2
        ;;
      --governor=*) LC_GOVERNOR="1"; LC_EPIC="${1#*=}"; shift ;;
      --endpoint)
        launcher_need_value "$1" "${2:-}"
        LC_ENDPOINT="$2"
        shift 2
        ;;
      --endpoint=*) LC_ENDPOINT="${1#*=}"; shift ;;
      --isolate-config) LC_ISOLATE_CONFIG=1; shift ;;
      --no-isolate-config) LC_ISOLATE_CONFIG=0; shift ;;
      -*)
        # A driver selector consumes the first positional argument. Preserve
        # the former driver's compatibility contract by forwarding subsequent
        # provider flags, while still rejecting unknown launcher flags before
        # a selector has been supplied.
        if [ "$LC_MODE" = "driver" ] && [ -n "$LC_EPIC" ]; then
          LC_FORWARD_ARGS+=("$1")
          shift
          continue
        fi
        launcher_error "unknown launcher flag '$1'; run --help."
        exit 2
        ;;
      *)
        if [ "$LC_MODE" = "driver" ] && [ -z "$LC_EPIC" ]; then
          LC_EPIC="$1"
        else
          LC_FORWARD_ARGS+=("$1")
        fi
        shift
        ;;
    esac
  done
}

launcher_normalize_model() {
  # D1 makes Fable the default and retains `--model sonnet` as the deliberate
  # alternate choice. Certify against the explicit roster identifiers.
  case "$LC_PROVIDER:$LC_MODEL" in
    claude:fable) LC_MODEL='claude-fable-5' ;;
    claude:sonnet) LC_MODEL='claude-sonnet-5' ;;
  esac
}

launcher_resolve_roots() {
  LC_SESSION_ROOT="$LC_ROOT"
  local common_dir
  common_dir="$(git -C "$LC_ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  if [ -n "$common_dir" ]; then
    LC_DURABLE_HELPER_ROOT="$(dirname "$common_dir")"
  else
    LC_DURABLE_HELPER_ROOT="$LC_ROOT"
  fi
  export LC_SESSION_ROOT LC_DURABLE_HELPER_ROOT
}

launcher_validate_mode() {
  if [ "$LC_MODE" = "interactive" ]; then
    if [ -n "$LC_EPIC" ]; then
      launcher_error "interactive launchers reject --epic; use start-${LC_PROVIDER}-driver.sh."
      exit 2
    fi
    if [ "$LC_GOVERNOR" = "1" ]; then
      launcher_error "--governor is available only on start-codex-driver.sh."
      exit 2
    fi
    return
  fi

  if [ "$LC_GOVERNOR" = "1" ]; then
    if [ "$LC_PROVIDER" != "codex" ]; then
      launcher_error "--governor is available only on start-codex-driver.sh."
      exit 2
    fi
    if [ -z "$LC_EPIC" ]; then
      launcher_error "--governor requires a selector or AUTO."
      exit 2
    fi
    if [ "$LC_EPIC" != "AUTO" ] && ! launcher_selector_resolve "$LC_EPIC" >/dev/null; then
      launcher_error "unknown lane selector '$LC_EPIC'."
      launcher_selector_help >&2
      exit 2
    fi
    LC_MODEL="gpt-5.6-sol"
    unset SESSION_EPIC
    LC_GOVERNOR_PROMPT="Follow agents_extensions/shared/prompts/dynamic-area-epic-fleet-governor.md for one bounded supervision cycle. TARGET=$LC_EPIC GOAL=AUTO"
    LC_FORWARD_ARGS=("$LC_GOVERNOR_PROMPT" "${LC_FORWARD_ARGS[@]}")
    return
  fi

  if [ -z "$LC_EPIC" ]; then
    launcher_error "driver launch requires --epic SELECTOR; run --help."
    exit 2
  fi
  if ! launcher_selector_resolve "$LC_EPIC" >/dev/null; then
    launcher_error "unknown lane selector '$LC_EPIC'."
    launcher_selector_help >&2
    exit 2
  fi
  LC_EPIC="$(launcher_selector_lane "$LC_EPIC")"
}

launcher_validate_driver_certification() {
  [ "$LC_MODE" = "driver" ] || return 0
  [ "$LC_GOVERNOR" = "0" ] || return 0
  case "$LC_PROVIDER:$LC_MODEL" in
    claude:claude-fable-5|claude:claude-sonnet-5|codex:gpt-5.6-terra|codex:gpt-5.6-sol|gemini:gemini-3.6-flash-high|gemini:gemini-3.1-pro-high|grok:grok-4.5)
      return 0
      ;;
    *)
      launcher_error "model '$LC_MODEL' is not certified for the $LC_PROVIDER driver."
      exit 4
      ;;
  esac
}

launcher_prepare_driver_identity() {
  local handoff harness
  case "$LC_PROVIDER" in
    claude) handoff="$(handoff_identity_for_epic "$LC_EPIC")"; harness="claude-code" ;;
    codex) handoff="$(handoff_identity_for_codex_epic "$LC_EPIC")"; harness="codex-cli" ;;
    gemini) handoff="$(handoff_identity_for_gemini_epic "$LC_EPIC")"; harness="agy" ;;
    grok) handoff="$(handoff_identity_for_grok_epic "$LC_EPIC")"; harness="grok-tui" ;;
  esac
  LC_DRIVER_HANDOFF="$handoff"
  LC_DRIVER_HARNESS="$harness"
  export SESSION_EPIC="$LC_EPIC"
  export SESSION_HANDOFF_AGENT="$LC_DRIVER_HANDOFF"
}

launcher_claim_driver_lease() {
  local stream task_id instance_id
  stream="$(launcher_selector_stream "$LC_EPIC")"
  launcher_prepare_driver_identity
  if [ "$LC_DRY_RUN" = "1" ]; then
    printf 'launcher: would claim lease stream=%s agent=%s harness=%s\n' "$stream" "$LC_PROVIDER" "$LC_DRIVER_HARNESS"
    return 0
  fi
  # shellcheck source=scripts/lib/session_supervisor.sh
  source "$LC_ROOT/scripts/lib/session_supervisor.sh"
  task_id="${SESSION_TASK_ID:-launcher-${LC_PROVIDER}-driver}"
  instance_id="${SESSION_INSTANCE_ID:-${LC_PROVIDER}-$$}"
  claim_session_supervisor_env "$stream" "$LC_PROVIDER" "$LC_DRIVER_HARNESS" "$task_id" "$instance_id" "$LC_SESSION_ROOT" "start-${LC_PROVIDER}-driver.sh" "$LC_EPIC"
}

launcher_close_failed_driver_lease() {
  # A provider canary runs after the lease claim. Close the exact exported
  # session-stream envelope before refusing the launch, so another certified
  # driver is not blocked behind this failed cold start until its TTL expires.
  if ! "$LC_SESSION_ROOT/.venv/bin/python" \
      -m agents_extensions.shared.session_streams hook close >/dev/null 2>&1; then
    launcher_error "failed to close the ${LC_PROVIDER} driver lease after provider canary failure."
  fi
}

launcher_bind_drive_epic() {
  local fleet_clause
  # shellcheck source=scripts/lib/fleet_comms_cold_start.sh
  source "$LC_ROOT/scripts/lib/fleet_comms_cold_start.sh"
  if command -v fleet_comms_cold_clause >/dev/null 2>&1; then
    fleet_clause="$(fleet_comms_cold_clause)"
  else
    fleet_clause='Fleet-comms: run plane-status and review-pr; file dual-write remains authoritative in every plane mode.'
  fi
  LC_DRIVER_PROMPT="Load agents_extensions/shared/skills/drive-epic/SKILL.md before acting. The launcher already claimed the ${LC_EPIC} lease and ran its provider canary; do not claim, renew, or reopen the lease. ${fleet_clause} Obtain independent cross-family review."
  LC_FORWARD_ARGS+=("$LC_DRIVER_PROMPT")
  if [ "$LC_DRY_RUN" = "1" ]; then
    printf 'launcher: would bind drive-epic after lease and provider canary\n'
  fi
}

launcher_main() {
  LC_PROVIDER="$1"
  LC_MODE="$2"
  shift 2
  LC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  # Every interactive and driver launcher exports the same routine ACP route;
  # sourcing the helper starts no process. Driver prompt binding later reuses
  # its functions and is intentionally idempotent.
  # shellcheck source=scripts/lib/fleet_comms_cold_start.sh
  source "$LC_ROOT/scripts/lib/fleet_comms_cold_start.sh"
  launcher_clear_foreign_route_state
  launcher_defaults
  launcher_parse "$@"
  launcher_normalize_model
  # Provider adapters are sourced dynamically and consume these values.
  export LC_ENDPOINT LC_ISOLATE_CONFIG
  launcher_resolve_roots
  # shellcheck source=scripts/lib/handoff_identity.sh
  source "$LC_ROOT/scripts/lib/handoff_identity.sh"
  launcher_validate_mode
  launcher_validate_driver_certification
  # shellcheck disable=SC1090
  source "$LC_ROOT/scripts/launchers/${LC_PROVIDER}.sh"
  launcher_adapter_validate
  launcher_adapter_preflight

  # Agent-extensions staleness gate (restored from the pre-cutover
  # start-claude.sh, now for EVERY provider): a session launched against stale
  # deployed hooks/rules runs retired definitions — refuse rather than launch.
  # Dry-run reports instead of deploying (hermetic probe surface).
  if [ "$LC_DRY_RUN" = "1" ]; then
    echo "LAUNCHER_DRY_RUN=1: would deploy agent extensions (agents:deploy)"
  else
    # shellcheck source=scripts/lib/deploy_extensions.sh
    source "$LC_ROOT/scripts/lib/deploy_extensions.sh"
    if ! deploy_agent_extensions "$LC_ROOT" agents:deploy; then
      launcher_error "refusing to launch ${LC_PROVIDER}: the agent-extensions deploy failed."
      exit 1
    fi
  fi

  if [ "$LC_MODE" = "driver" ] && [ "$LC_GOVERNOR" = "0" ]; then
    local canary_rc=0
    launcher_prepare_driver_identity
    if [ "$LC_DRY_RUN" != "1" ] && declare -F launcher_adapter_prelease >/dev/null 2>&1; then
      # Continuity refusal (rollover ambiguity / already-resumed packet) is the
      # legacy public exit 1 — NOT 5, which is reserved for transport
      # degradation (#5958 CI fix; e2e callers pin this contract).
      launcher_adapter_prelease || exit 1
    fi
    if [ "${LC_DRIVER_LEASE_ENABLED:-1}" != "1" ]; then
      printf 'Skipping stream lease and provider canary (untrusted %s route).\n' "$LC_PROVIDER" >&2
      launcher_adapter_exec
      return
    fi
    launcher_claim_driver_lease
    launcher_adapter_canary || canary_rc=$?
    if [ "$canary_rc" -ne 0 ]; then
      launcher_close_failed_driver_lease
      exit "$canary_rc"
    fi
    launcher_bind_drive_epic
  fi
  if [ "$LC_MODE" = "driver" ] && [ "$LC_GOVERNOR" = "1" ] && [ "$LC_DRY_RUN" = "1" ]; then
    printf 'launcher: governor SESSION_EPIC=%s\n' "${SESSION_EPIC:-<unset>}"
  fi
  launcher_adapter_exec
}

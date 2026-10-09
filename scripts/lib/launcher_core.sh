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
    cursor) provider_env='  CURSOR_API_KEY           Optional Cursor API key (otherwise CLI login / oauth).' ;;
    kimi) provider_env='  KIMICC_AUTH_TOKEN, MOONSHOT_API_KEY, KIMI_API_KEY
                             Explicit Kimi credentials for --harness claude-code.' ;;
    glm) provider_env='  GLMCC_AUTH_TOKEN, ZAI_API_KEY, ZHIPU_API_KEY, GLM_API_KEY
                             Explicit GLM credentials (preferred over the secret file).
  ~/.secret/zai.key        Owner-only fallback (mode 0600/0400) when env is unset.
  GLMCC_SECRET_FILE        Override path for the file-backed Z.AI key.' ;;
  esac
  case "$LC_PROVIDER:$LC_MODE" in
    gemini:interactive) example_three='./start-gemini.sh --model gemini-3.8-flash-high' ;;
    kimi:interactive) example_three='./start-kimicc.sh --endpoint coding' ;;
    glm:interactive) example_three='./start-glmcc.sh --endpoint coding' ;;
    *:driver) example_three="./${name} --epic devops"$'\n'"  ./${name} --epic infra --force" ;;
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
  --model MODEL              Provider model. Claude driver default: claude-opus-5-5[1m].
                             Cursor default (driver and interactive): grok-4.7-high;
                             it also accepts composer-2.5, never Auto, a Fast variant,
                             an empty model or a forwarded --model. Gemini driver
                             default: gemini-3.1-pro-high (gemini-3.8-flash-high is
                             also certified); Gemini interactive default:
                             gemini-3.8-flash-high. Claude
                             interactive / Grok: omit to keep last TUI/session model.
  --effort LEVEL             Session effort when supported (Claude Code --effort; Grok
                             --reasoning-effort). Claude driver default: high. Otherwise
                             omit to keep last session selection. Other providers ignore.
  --harness HARNESS          Provider harness (default: ${LC_HARNESS}).
  --epic SELECTOR            Driver lane only; for example: devops or atlas.
  --force                    Driver only. Attributed operator release of a live
                             predecessor lease, then claim. Use when the previous
                             driver did not hand off. Live drivers must not pass it.
  --governor SELECTOR        Codex driver only; one lease-free Sol cycle (AUTO allowed).
  --endpoint NAME            Kimi/GLM route endpoint: coding or platform.
  --isolate-config           Kimi/GLM Claude-Code config isolation (default).
  --no-isolate-config        Use the existing Claude-Code config only when route-safe.
  --                         Pass all remaining arguments verbatim to the provider CLI.

Environment:
  LAUNCHER_DRY_RUN=1         Validate the route and print a redacted exact would-exec argv.
  LAUNCHER_DRY_RUN_ARGV_FILE With dry-run, also write the exact NUL-separated argv here.
  LU_RULES_SEAT              Rules core seat: core or content (default: content for a
                             curriculum driver lane, else core). Exported to the session.
  LAUNCHER_MODEL             Default model when --model is omitted (Claude driver:
                             claude-opus-5-5[1m]; Cursor: grok-4.7-high; empty
                             for Claude interactive/Grok = last session).
  LAUNCHER_EFFORT            Default effort when --effort is omitted (Claude driver: high;
                             empty for Claude interactive/Grok = last session).
  LAUNCHER_HARNESS           Default harness when --harness is omitted.
$provider_env

EXIT CODES:
  0  Launch completed, help shown, or dry-run succeeded.
  1  Launch refused on a continuity precondition (rollover ambiguity or lease).
  2  Usage error (unknown flag, retired model, unsupported harness, or invalid selector).
  3  Required provider credential or executable is unavailable.
  4  Driver certification is missing or revoked.
  5  Provider transport is degraded; use the stated external-fleet disposition.
  6  Driver memory scope unavailable or unverifiable; no unbounded override.

Examples:
  ./${name} --help
  LAUNCHER_DRY_RUN=1 ./${name} --model ${LC_MODEL:-MODEL}
  $example_three
EOF
  if [ "$LC_PROVIDER" = grok ] || [ "$LC_PROVIDER" = codex ]; then
    cat <<'EOF'

Hermes (opt-in only):
  --harness hermes           Use the existing Hermes OAuth login; no paid fallback.
                             Grok pins grok-4.7 via xai-oauth; Codex pins
                             gpt-6.1-sol via openai-codex (interactive only).
                             --effort maps to the probed Hermes --reasoning flag.
                             Hermes accepts prompt text, not forwarded CLI flags.
                             Requires an installed CLI and an empty fallback chain,
                             including for dry-run. Help never probes or claims leases.
  Rollback: omit --harness hermes to use the native launcher again.
EOF
  fi
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

# Project interpreter for helper modules: the .venv of the helper root that
# launcher_resolve_roots validated (#9118, #9121), so an operator-named Codex
# primary serves the adapters too. Call after launcher_resolve_roots; callers
# exit 3.
launcher_project_python() {
  local python="${LC_DURABLE_HELPER_ROOT:-}/.venv/bin/python"
  if [ -z "${LC_DURABLE_HELPER_ROOT:-}" ] || [ ! -f "$python" ] || [ ! -x "$python" ]; then
    launcher_error "project interpreter not found: $python"
    return 1
  fi
  printf '%s\n' "$python"
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

launcher_hermes_validate() {
  if [ "$LC_HARNESS_EXPLICIT" != 1 ]; then
    launcher_error 'Hermes requires explicit --harness hermes; environment opt-in is refused.'
    exit 2
  fi
  local arg
  for arg in "${LC_FORWARD_ARGS[@]}"; do
    case "$arg" in
      -*)
        launcher_error 'Hermes accepts prompt text only; forwarded CLI flags are forbidden.'
        exit 2
        ;;
    esac
  done
}

launcher_hermes_preflight() {
  # Unlike native dry-run, Hermes must prove its CLI surface before emitting
  # an argv. Capture probe output: config/provider failures may contain secrets.
  command -v hermes >/dev/null 2>&1 || {
    launcher_error 'Hermes executable is unavailable.'
    exit 3
  }
  local help flag fallback reasoning_help
  help="$(hermes chat --help 2>/dev/null)" || {
    launcher_error 'Hermes CLI capability probe failed.'
    exit 3
  }
  for flag in --model --provider --query --in --cli; do
    if ! grep -Eq -- "(^|[[:space:],])${flag}([[:space:]=,]|$)" <<< "$help"; then
      launcher_error 'Hermes CLI lacks a required launcher option.'
      exit 2
    fi
  done
  if [ -n "$LC_EFFORT" ]; then
    reasoning_help="$(awk '
      /^  --reasoning / { found=1; print; next }
      found && /^  -/ { exit }
      found { print }
    ' <<< "$help")"
    if ! grep -Eq -- "(^|[[:space:],])${LC_EFFORT}([[:space:],.]|$)" <<< "$reasoning_help"; then
      launcher_error 'Hermes CLI does not advertise the requested reasoning effort.'
      exit 2
    fi
  fi
  fallback="$(hermes fallback list 2>/dev/null)" || {
    launcher_error 'Hermes fallback configuration could not be verified.'
    exit 3
  }
  # Fail closed on changed/unknown output, not merely absence of a paid label.
  if [ "$fallback" != $'\n  No fallback providers configured.\n\n  Add one with:  hermes fallback add' ]; then
    launcher_error 'Hermes requires an empty fallback chain; refusing unverified or configured fallback.'
    exit 2
  fi
  LC_AUTH_SOURCE="hermes-existing-oauth"
}

launcher_hermes_exec() {
  local cmd=(hermes chat --cli --provider "$LC_HERMES_PROVIDER" --model "$LC_MODEL" --in "$LC_SESSION_ROOT")
  local prompt="" arg
  if [ -n "$LC_EFFORT" ]; then cmd+=(--reasoning "$LC_EFFORT"); fi
  for arg in "${LC_FORWARD_ARGS[@]}"; do
    if [ -n "$prompt" ]; then prompt+=$'\n'; fi
    prompt+="$arg"
  done
  # Hermes has no system-prompt flag: the rules core leads the seeded query.
  if [ -n "${LC_RULES_CORE:-}" ]; then
    cmd+=(--query "$(rules_core_prefix "$prompt")")
  elif [ "${#LC_FORWARD_ARGS[@]}" -gt 0 ]; then
    cmd+=(--query "$prompt")
  fi
  if [ "$LC_DRY_RUN" = 1 ]; then
    printf 'LAUNCHER_DRY_RUN=1: credential_source=%s provider=%s model=%s requested_effort=%s harness=hermes\nwould exec ' \
      "$LC_AUTH_SOURCE" "$LC_HERMES_PROVIDER" "$LC_MODEL" "${LC_EFFORT:-default}"
    launcher_print_argv "${cmd[@]}"
    printf '\n'
    return 0
  fi
  launcher_exec_command "${cmd[@]}"
}

# Dry-run argv printer shared by every adapter. Stdout shows each argument with
# the rules core replaced by a size placeholder; LAUNCHER_DRY_RUN_ARGV_FILE, when
# set, receives the exact NUL-separated argv the launch would exec.
launcher_print_argv() {
  local arg placeholder
  placeholder="<rules-core seat=${LC_RULES_SEAT:-none} bytes=${LC_RULES_CORE_BYTES:-0}>"
  for arg in "$@"; do
    if [ -n "${LC_RULES_CORE:-}" ]; then
      arg="${arg//"$LC_RULES_CORE"/$placeholder}"
      if [ -n "${LC_RULES_CORE_TOML:-}" ]; then
        arg="${arg//"$LC_RULES_CORE_TOML"/$placeholder}"
      fi
    fi
    printf '%q ' "$arg"
  done
  if [ -n "${LAUNCHER_DRY_RUN_ARGV_FILE:-}" ]; then
    printf '%s\0' "$@" > "$LAUNCHER_DRY_RUN_ARGV_FILE"
  fi
}

# Every seat starts with the rules core (scripts/lib/rules_core.sh). A driver on
# a curriculum lane is a content seat and also gets the curriculum addendum. An
# absent or unreadable core refuses the launch (exit 1), naming the path.
launcher_load_rules_core() {
  local lane=""
  LC_RULES_CORE_TOML=""
  if [ ! -r "$LC_ROOT/scripts/lib/rules_core.sh" ]; then
    launcher_error "refusing to launch ${LC_PROVIDER}: rules core unavailable ($LC_ROOT/scripts/lib/rules_core.sh is missing)."
    exit 1
  fi
  # shellcheck source=scripts/lib/rules_core.sh
  source "$LC_ROOT/scripts/lib/rules_core.sh"
  if [ "$LC_MODE" = driver ] && [ "$LC_GOVERNOR" = 0 ]; then
    lane="$LC_EPIC"
  fi
  rules_core_load "$LC_DURABLE_HELPER_ROOT/.venv/bin/python" "$LC_ROOT" "$lane" "$LC_PROVIDER" || exit 1
  if [ -n "$LC_RULES_CORE" ] && [ "$LC_DRY_RUN" = 1 ]; then
    printf 'launcher: rules core seat=%s bytes=%s\n' "$LC_RULES_SEAT" "$LC_RULES_CORE_BYTES"
  fi
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

launcher_export_git_identity() {
  local py identity name email
  py="$(launcher_project_python)" || return 3
  identity="$("$py" "$LC_ROOT/scripts/lib/git_identity.py" "$LC_PROVIDER" "${LC_MODEL:-}")" || return 3
  IFS=$'\t' read -r name email <<< "$identity"
  export GIT_AUTHOR_NAME="$name" GIT_COMMITTER_NAME="$name"
  export GIT_AUTHOR_EMAIL="$email" GIT_COMMITTER_EMAIL="$email"
}

launcher_defaults() {
  case "$LC_PROVIDER" in
    claude)
      # Driver seats the orchestrator on Opus 5.5 with the 1M window (operator
      # 2026-09-22); effort defaults to high below. Interactive leaves model and
      # effort alone so Claude Code keeps the last TUI/session selection.
      if [ "$LC_MODE" = driver ]; then
        LC_MODEL="${LAUNCHER_MODEL:-claude-opus-5-5[1m]}"
      else
        LC_MODEL="${LAUNCHER_MODEL:-}"
      fi
      LC_HARNESS="${LAUNCHER_HARNESS:-claude-code}"
      ;;
    codex)
      LC_MODEL="${LAUNCHER_MODEL:-gpt-6.1-sol}"
      LC_HARNESS="${LAUNCHER_HARNESS:-codex}"
      ;;
    gemini)
      # The driver defaults to 3.1 Pro (2026-10-08 approval); interactive
      # sessions keep the 3.8 Flash default.
      if [ "$LC_MODE" = driver ]; then
        LC_MODEL="${LAUNCHER_MODEL:-gemini-3.1-pro-high}"
      else
        LC_MODEL="${LAUNCHER_MODEL:-gemini-3.8-flash-high}"
      fi
      LC_HARNESS="${LAUNCHER_HARNESS:-agy}"
      ;;
    grok)
      # Both interactive and driver leave model/effort alone unless the caller
      # sets --model / --effort or LAUNCHER_MODEL / LAUNCHER_EFFORT. Empty means
      # the Grok TUI keeps the last session selection.
      LC_MODEL="${LAUNCHER_MODEL:-}"
      LC_HARNESS="${LAUNCHER_HARNESS:-grok}"
      ;;
    cursor)
      # Driver and interactive sessions both pin the catalog seat. Omitting
      # --model lets cursor-agent use Auto, which only a typed implementation
      # dispatch may run (operator decision 2026-09-30, #9274). --model or
      # LAUNCHER_MODEL may choose another certified pin.
      LC_MODEL="${LAUNCHER_MODEL:-$LC_CURSOR_SEAT_PIN}"
      LC_HARNESS="${LAUNCHER_HARNESS:-cursor-agent}"
      ;;
    kimi)
      LC_MODEL="${LAUNCHER_MODEL:-k3-256k}"
      LC_HARNESS="${LAUNCHER_HARNESS:-kimi-code}"
      ;;
    glm)
      LC_MODEL="${LAUNCHER_MODEL:-glm-5.3}"
      LC_HARNESS="${LAUNCHER_HARNESS:-claude-code}"
      ;;
    *) launcher_error "unknown provider '$LC_PROVIDER'"; exit 2 ;;
  esac
  LC_EFFORT="${LAUNCHER_EFFORT:-}"
  if [ "$LC_PROVIDER" = codex ] && [ -z "$LC_EFFORT" ]; then
    # Operator 2026-09-22: Sol's seat is high, including the ordinary launcher.
    LC_EFFORT=high
  fi
  if [ "$LC_PROVIDER" = claude ] && [ "$LC_MODE" = driver ] && [ -z "$LC_EFFORT" ]; then
    # Opus 5.5 API default is medium; orchestrating seats run at high.
    LC_EFFORT=high
  fi
  LC_ENDPOINT="${LAUNCHER_ENDPOINT:-coding}"
  LC_ISOLATE_CONFIG="${LAUNCHER_ISOLATE_CONFIG:-1}"
  LC_DRY_RUN="${LAUNCHER_DRY_RUN:-0}"
  LC_EPIC=""
  LC_GOVERNOR="0"
  LC_DRIVER_FORCE=0
  LC_DRIVER_LEASE_CLAIMED=0
  LC_HARNESS_EXPLICIT=0
  LC_FORWARD_ARGS=()
}

launcher_need_value() {
  if [ -z "${2:-}" ]; then
    launcher_error "$1 requires a value; run --help."
    exit 2
  fi
}

launcher_drop_force_from_successor_args() {
  # --force is a one-shot operator takeover. Supervisory successor execs replay
  # LC_DRIVER_ORIGINAL_ARGS; leaving launcher --force there can evict a later
  # legitimate holder (#8229 CF). Provider args after `--` are forwarded
  # verbatim and must keep a literal --force.
  local arg past_dd=0
  local -a kept=()
  for arg in "${LC_DRIVER_ORIGINAL_ARGS[@]+"${LC_DRIVER_ORIGINAL_ARGS[@]}"}"; do
    if [ "$past_dd" = "1" ]; then
      kept+=("$arg")
      continue
    fi
    if [ "$arg" = "--" ]; then
      past_dd=1
      kept+=("$arg")
      continue
    fi
    [ "$arg" = "--force" ] && continue
    kept+=("$arg")
  done
  if [ "${#kept[@]}" -gt 0 ]; then
    LC_DRIVER_ORIGINAL_ARGS=("${kept[@]}")
  else
    LC_DRIVER_ORIGINAL_ARGS=()
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
      --effort)
        launcher_need_value "$1" "${2:-}"
        LC_EFFORT="$2"
        shift 2
        ;;
      --effort=*) LC_EFFORT="${1#*=}"; shift ;;
      --harness)
        launcher_need_value "$1" "${2:-}"
        LC_HARNESS_EXPLICIT=1
        LC_HARNESS="$2"
        shift 2
        ;;
      --harness=*) LC_HARNESS_EXPLICIT=1; LC_HARNESS="${1#*=}"; shift ;;
      --epic)
        launcher_need_value "$1" "${2:-}"
        LC_EPIC="$2"
        shift 2
        ;;
      --epic=*) LC_EPIC="${1#*=}"; shift ;;
      --force) LC_DRIVER_FORCE=1; shift ;;
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
  # Claude omits --model unless asked (interactive and driver). Short aliases
  # normalize to roster identifiers when a model is provided.
  case "$LC_PROVIDER:$LC_MODEL" in
    claude:fable) LC_MODEL='claude-fable-5-1' ;;
    claude:fable-5) LC_MODEL='claude-fable-5' ;;
    claude:sonnet) LC_MODEL='claude-sonnet-5-5' ;;
    claude:opus|claude:opus-5-5|claude:opus-5.5) LC_MODEL='claude-opus-5-5[1m]' ;;
    claude:opus-5) LC_MODEL='claude-opus-5' ;;
  esac
  if [ -n "$LC_MODEL" ]; then
    "$LC_DURABLE_HELPER_ROOT/.venv/bin/python" "$LC_ROOT/scripts/review/model_catalog.py" \
      --check-retired-model "$LC_MODEL" || exit 2
  fi
}

launcher_normalize_effort() {
  # Claude Code accepts low|medium|high|xhigh|max (and future levels). Empty
  # means "do not inject --effort" so the last session effort is kept.
  if [ -z "${LC_EFFORT:-}" ]; then
    return 0
  fi
  case "$LC_EFFORT" in
    low|medium|high|xhigh|max) return 0 ;;
    *)
      launcher_error "unknown --effort '$LC_EFFORT' (expected low|medium|high|xhigh|max)."
      exit 2
      ;;
  esac
}

# Git's repository-local environment (`git rev-parse --local-env-vars`): each
# one redirects which repository a git call, or a helper that asks git, sees.
LC_GIT_LOCAL_ENV_VARS=(
  GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_CONFIG GIT_CONFIG_PARAMETERS
  GIT_CONFIG_COUNT GIT_OBJECT_DIRECTORY GIT_DIR GIT_WORK_TREE
  GIT_IMPLICIT_WORK_TREE GIT_GRAFT_FILE GIT_INDEX_FILE GIT_NO_REPLACE_OBJECTS
  GIT_REPLACE_REF_BASE GIT_PREFIX GIT_SHALLOW_FILE GIT_COMMON_DIR
)

# LC_DURABLE_HELPER_ROOT is the primary checkout that every launcher helper
# interpreter and helper script runs from. It is resolved by the shared
# project_interpreter.sh check (gitfile shape + back-pointer, never git, never
# `commondir`), and an ambient value is overwritten. Untrusted git metadata
# refuses the launch rather than falling back to a worktree-local root (#9121).
#
# The one exception is CODEX_CANONICAL_REPO_ROOT on a Codex launch: an
# operator-set override (docs/SCRIPTS.md, #5438) and the only accepted way to
# name a primary that Git cannot prove from the worktree, such as a
# `--separate-git-dir` primary with no `<primary>/.git/worktrees/<name>`.
# When set, it replaces the gitfile check and must itself be the primary
# checkout of this worktree's Git common directory, on `main`; any mismatch
# refuses. Unset, nothing here falls back to it.
launcher_resolve_roots() {
  unset "${LC_GIT_LOCAL_ENV_VARS[@]}"
  LC_SESSION_ROOT="$LC_ROOT"
  LC_DURABLE_HELPER_ROOT=""
  # shellcheck source=scripts/lib/project_interpreter.sh
  source "$(dirname "${BASH_SOURCE[0]}")/project_interpreter.sh"
  if [ "${LC_PROVIDER:-}" = codex ] && [ -n "${CODEX_CANONICAL_REPO_ROOT:-}" ]; then
    LC_DURABLE_HELPER_ROOT="$(launcher_canonical_override_root "$CODEX_CANONICAL_REPO_ROOT")" || exit 1
  elif ! LC_DURABLE_HELPER_ROOT="$(project_primary_root_resolve "$LC_ROOT")"; then
    launcher_error "refusing to run launcher helpers from $LC_ROOT; its git metadata does not validate."
    exit 3
  fi
  export LC_SESSION_ROOT LC_DURABLE_HELPER_ROOT
}

# Prints the physical path of an operator-named primary checkout, or explains
# on stderr why it is not one: it must share this worktree's Git common
# directory, be that repository's primary (its git dir IS the common dir, so a
# linked worktree does not qualify; nor does a directory that reaches another
# checkout's `.git`) and have `main` checked out. When the common directory
# records `core.worktree`, the override must be that directory.
#
# Residual (#9121): a `--separate-git-dir` primary is a plain gitfile
# (`gitdir: <common>`) and Git records no back-pointer to it, so a second
# directory holding a copy of that gitfile is locally indistinguishable from
# the primary unless `core.worktree` is set (Git does not set it by default).
# This is the same class as the forged-fake-primary residual in
# project_interpreter.sh. The override is operator-set environment, like PATH:
# an operator who sets CODEX_CANONICAL_REPO_ROOT vouches for that directory.
# Pinned by test_override_copied_separate_git_dir_gitfile_residual.
launcher_canonical_override_root() {
  local root common own_common own_git recorded
  root="$(cd -P "$1" 2>/dev/null && pwd)" || {
    launcher_error "CODEX_CANONICAL_REPO_ROOT is not a directory: $1"
    return 1
  }
  common="$(git -C "$LC_ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" \
    && common="$(cd -P "$common" 2>/dev/null && pwd)" || common=""
  own_common="$(git -C "$root" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" \
    && own_common="$(cd -P "$own_common" 2>/dev/null && pwd)" || own_common=""
  if [ -n "$common" ] && [ "$own_common" = "$common" ] \
    && recorded="$(git --git-dir="$common" config --get core.worktree 2>/dev/null)"; then
    # A relative core.worktree is relative to the Git directory.
    case "$recorded" in
      /*) ;;
      *) recorded="$common/$recorded" ;;
    esac
    if [ "$(cd -P "$recorded" 2>/dev/null && pwd)" != "$root" ]; then
      launcher_error "CODEX_CANONICAL_REPO_ROOT is not the core.worktree Git records ($recorded): $root"
      return 1
    fi
  fi
  if [ -z "$common" ] || [ "$own_common" != "$common" ] \
    || [ "$(git -C "$root" rev-parse --show-toplevel 2>/dev/null)" != "$root" ]; then
    launcher_error "CODEX_CANONICAL_REPO_ROOT is not a checkout of this Git common directory."
    return 1
  fi
  own_git="$(git -C "$root" rev-parse --absolute-git-dir 2>/dev/null)" \
    && own_git="$(cd -P "$own_git" 2>/dev/null && pwd)" || own_git=""
  if [ "$own_git" != "$common" ]; then
    launcher_error "CODEX_CANONICAL_REPO_ROOT is a linked worktree, not the primary checkout: $root"
    return 1
  fi
  # A lookalike reaches the real `<primary>/.git` through a symlink or a
  # gitfile; Git can already name that primary, so only it qualifies.
  if [ -L "$root/.git" ] \
    || { [ "$(basename "$common")" = .git ] && [ "$(dirname "$common")" != "$root" ]; }; then
    launcher_error "CODEX_CANONICAL_REPO_ROOT borrows another checkout's .git: $root"
    return 1
  fi
  if [ "$(git -C "$root" branch --show-current 2>/dev/null)" != main ]; then
    launcher_error "canonical checkout must be on main: $root"
    return 1
  fi
  printf '%s\n' "$root"
}

launcher_validate_mode() {
  if [ "$LC_MODE" = "interactive" ]; then
    if [ -n "$LC_EPIC" ]; then
      launcher_error "interactive launchers reject --epic; use start-${LC_PROVIDER}-driver.sh."
      exit 2
    fi
    if [ "$LC_DRIVER_FORCE" = "1" ]; then
      launcher_error "interactive launchers reject --force; use start-${LC_PROVIDER}-driver.sh --epic SELECTOR --force."
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
    if [ "$LC_EPIC" != "AUTO" ]; then
      launcher_require_registered_slot "$LC_PROVIDER" "$LC_EPIC" || exit 2
    fi
    if [ "$LC_MODEL" = gpt-6-luna ]; then
      launcher_error "gpt-6-luna is a scouting model, not a governor model. Use gpt-6.1-sol."
      exit 4
    fi
    LC_MODEL="${LC_MODEL:-gpt-6.1-sol}"
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
  launcher_require_registered_slot "$LC_PROVIDER" "$LC_EPIC" || exit 2
  # Slot identity uses the resolved lane (launcher_require_registered_slot).
  # SESSION_EPIC keeps the selector when that lane is not the same stream, so
  # the file handoff directory does not follow the area slot.
  LC_EPIC="$(launcher_session_epic "$LC_EPIC")"
}

# Gemini drives epics only through start-gemini-driver.sh on the two certified
# AGY pins (2026-10-08 approval). Any other Gemini model id, and a Gemini model
# id on another provider's driver, is refused before scope entry or startup.
# A provider --model forwarded after `--` would put a second, uncertified model
# on the agy exec line, so the Gemini driver refuses it as well.
LC_GEMINI_DRIVER_MODELS='gemini-3.1-pro-high, gemini-3.8-flash-high'

launcher_refuse_uncertified_gemini_driver() {
  local arg
  [ "$LC_MODE" = driver ] || return 0
  if [ "$LC_PROVIDER" = gemini ]; then
    for arg in "${LC_FORWARD_ARGS[@]+"${LC_FORWARD_ARGS[@]}"}"; do
      case "$arg" in
        --model|--model=*)
          launcher_error "the gemini driver takes its model from the launcher --model, not from forwarded '$arg' (certified: $LC_GEMINI_DRIVER_MODELS)."
          exit 4
          ;;
      esac
    done
  fi
  case "$LC_PROVIDER:$LC_MODEL" in
    gemini:gemini-3.1-pro-high|gemini:gemini-3.8-flash-high)
      return 0
      ;;
    gemini:*)
      launcher_error "model '$LC_MODEL' is not certified for the gemini driver (certified: $LC_GEMINI_DRIVER_MODELS)."
      exit 4
      ;;
    *:gemini-*|*:gemini:*)
      launcher_error "model '$LC_MODEL' is a Gemini model; it drives only through start-gemini-driver.sh (certified: $LC_GEMINI_DRIVER_MODELS)."
      exit 4
      ;;
  esac
}

launcher_validate_driver_certification() {
  launcher_refuse_uncertified_gemini_driver
  # Interactive Grok: empty --model keeps the last TUI selection; an explicit
  # pin must be the certified native model (refuse retired grok-4.5, #6870).
  # Cursor pins a concrete model in every mode: an interactive session is not a
  # typed implementation dispatch, so it never runs Auto either (#9274).
  if [ "$LC_PROVIDER" = "cursor" ] && [ "$LC_GOVERNOR" = "0" ]; then
    launcher_validate_cursor_pin
    return 0
  fi
  if [ "$LC_MODE" = "interactive" ] && [ "$LC_PROVIDER" = "grok" ]; then
    if [ -z "${LC_MODEL:-}" ]; then
      return 0
    fi
    case "$LC_MODEL" in
      grok-4.7) return 0 ;;
      *)
        launcher_error "model '$LC_MODEL' is not certified for the grok launcher (use grok-4.7, or omit --model)."
        exit 4
        ;;
    esac
  fi
  [ "$LC_MODE" = "driver" ] || return 0
  [ "$LC_GOVERNOR" = "0" ] || return 0
  # Claude/Grok may omit --model so the CLI keeps its current selection.
  if { [ "$LC_PROVIDER" = "claude" ] || [ "$LC_PROVIDER" = "grok" ]; } && [ -z "${LC_MODEL:-}" ]; then
    return 0
  fi
  case "$LC_PROVIDER:$LC_MODEL" in
    claude:claude-opus-5-5|claude:claude-opus-5-5\[1m\]|claude:claude-fable-5-1|claude:claude-sonnet-5-5|codex:gpt-6.1-sol|gemini:gemini-3.1-pro-high|gemini:gemini-3.8-flash-high|grok:grok-4.7)
      return 0
      ;;
    *)
      launcher_error "model '$LC_MODEL' is not certified for the $LC_PROVIDER driver."
      exit 4
      ;;
  esac
}

# Catalog seat pin: orchestrator_seats.cursor model_id grok-4.7 at effort high
# (scripts/config/model_catalog.yaml; tests/test_start_cursor_launcher.py
# keeps the two in step).
LC_CURSOR_SEAT_PIN=grok-4.7-high

# Every launched Cursor session, driver or interactive, runs a concrete
# approved pin, never Auto (operator decision 2026-09-30, #9274): an empty
# model and a provider --model forwarded after `--` would let cursor-agent pick
# Auto or override the certified pin.
launcher_validate_cursor_pin() {
  local arg seat="cursor driver"
  [ "$LC_MODE" = driver ] || seat="cursor interactive session"
  for arg in "${LC_FORWARD_ARGS[@]+"${LC_FORWARD_ARGS[@]}"}"; do
    case "$arg" in
      --model|--model=*)
        launcher_error "the $seat takes its model from the launcher --model, not from forwarded '$arg' (pin $LC_CURSOR_SEAT_PIN or composer-2.5; never Auto)."
        exit 4
        ;;
    esac
  done
  if [ -z "${LC_MODEL:-}" ]; then
    launcher_error "the $seat requires a concrete model; an empty model runs Auto (pin $LC_CURSOR_SEAT_PIN or composer-2.5)."
    exit 4
  fi
  local normalized
  if ! normalized="$("$LC_DURABLE_HELPER_ROOT/.venv/bin/python" -c '
import sys
sys.path.insert(0, sys.argv[1])
from scripts.review.model_catalog import ModelCatalogError, apply_cursor_model_pins
try:
    print(apply_cursor_model_pins(sys.argv[2]) or "")
except ModelCatalogError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(4)
' "$LC_ROOT" "$LC_MODEL")"; then
    launcher_error "model '$LC_MODEL' is not certified for the $seat; pin $LC_CURSOR_SEAT_PIN or composer-2.5."
    exit 4
  fi
  LC_MODEL="$normalized"
  if ! launcher_cursor_model_certified "$LC_MODEL"; then
    launcher_error "CURSOR_MODEL_NOT_APPROVED: model '$LC_MODEL' is not certified for the $seat; pin $LC_CURSOR_SEAT_PIN or composer-2.5."
    exit 4
  fi
}

# Cursor CLI model ids: bare certified pins and bracket overrides such as
# composer-2.5[fast=false]. Auto, Fast variants and previous generations are not certified.
launcher_cursor_model_certified() {
  local model="$1"
  case "$model" in
    composer-2.5|composer-2.5\[fast=false\]|grok-4.7-high) return 0 ;;
  esac
  return 1
}

launcher_prepare_driver_identity() {
  local handoff harness
  case "$LC_PROVIDER" in
    claude) handoff="$(handoff_identity_for_epic "$LC_EPIC")"; harness="claude-code" ;;
    codex) handoff="$(handoff_identity_for_codex_epic "$LC_EPIC")"; harness="codex-cli" ;;
    gemini) handoff="$(handoff_identity_for_gemini_epic "$LC_EPIC")"; harness="agy" ;;
    grok) handoff="$(handoff_identity_for_grok_epic "$LC_EPIC")"; harness="grok-tui" ;;
    cursor) handoff="$(handoff_identity_for_cursor_epic "$LC_EPIC")"; harness="cursor-agent" ;;
  esac
  if [ "$LC_HARNESS" = hermes ]; then harness=hermes; fi
  LC_DRIVER_HANDOFF="$handoff"
  LC_DRIVER_HARNESS="$harness"
  export SESSION_EPIC="$LC_EPIC"
  export SESSION_HANDOFF_AGENT="$LC_DRIVER_HANDOFF"
}

launcher_import_rollover_bundle() {
  local stream helper_root py script output rc
  stream="$(launcher_selector_stream "$LC_EPIC" 2>/dev/null || true)"
  case "$stream" in
    epic:*) ;;
    *) return 0 ;;
  esac
  helper_root="$LC_DURABLE_HELPER_ROOT"
  py="$helper_root/.venv/bin/python"
  script="$helper_root/scripts/orchestration/thread_handoff.py"
  if [ ! -x "$py" ] || [ ! -f "$script" ]; then
    printf 'WARNING: rollover bundle pre-lease import unavailable; continuing fail-open (helper=%s).\n' "$helper_root" >&2
    return 0
  fi
  output=""
  rc=0
  output="$("$py" "$script" \
    --repo-root "$helper_root" \
    --monitor-base-url "${LU_MONITOR_LOOPBACK:-http://127.0.0.1:8765}" \
    import-bundle --from-api "$stream" --stream "$stream" 2>&1)" || rc=$?
  if [ "$rc" -ne 0 ] || [[ "$output" == *WARNING:* ]]; then
    printf 'WARNING: rollover bundle pre-lease import refused or failed (fail-open); launcher continues.\n%s\n' "$output" >&2
  fi
}

launcher_claim_driver_lease() {
  local stream task_id instance_id
  stream="$(launcher_selector_stream "$LC_EPIC")"
  launcher_prepare_driver_identity
  if [ "$LC_DRY_RUN" = "1" ]; then
    printf 'launcher: would claim lease stream=%s agent=%s harness=%s\n' "$stream" "$LC_PROVIDER" "$LC_DRIVER_HARNESS"
    printf 'launcher: session epic=%s slot=%s handoff=.claude/%s-epic/CLAUDE-DRIVER-HANDOFF.md\n' \
      "$SESSION_EPIC" "$LC_DRIVER_HANDOFF" "$SESSION_EPIC"
    if [ "${LC_DRIVER_FORCE:-0}" = "1" ]; then
      printf 'launcher: would force-release any live holder on %s then claim\n' "$stream"
    fi
    launcher_cursor_observer_presence
    return 0
  fi
  # shellcheck source=scripts/lib/session_supervisor.sh
  source "$LC_ROOT/scripts/lib/session_supervisor.sh"
  task_id="${SESSION_TASK_ID:-launcher-${LC_PROVIDER}-driver}"
  instance_id="${SESSION_INSTANCE_ID:-${LC_PROVIDER}-$$}"
  claim_session_supervisor_env "$stream" "$LC_PROVIDER" "$LC_DRIVER_HARNESS" "$task_id" "$instance_id" "$LC_SESSION_ROOT" "start-${LC_PROVIDER}-driver.sh" "$LC_EPIC" || return 1
  LC_DRIVER_LEASE_CLAIMED=1
  launcher_cursor_observer_presence
}

launcher_cursor_observer_presence() {
  # Occupancy cannot infer Cursor from a RAM lease or a live fleet-agents row.
  # Heartbeat the loopback observer store (#7075). Fail-open if Monitor is down.
  [ "$LC_PROVIDER" = "cursor" ] || return 0
  [ "$LC_MODE" = "driver" ] || return 0
  if [ "$LC_DRY_RUN" = "1" ]; then
    printf 'launcher: would heartbeat observer presence agent=cursor\n'
    printf 'launcher: would renew observer presence while the driver session runs\n'
    return 0
  fi
  local task_id
  task_id="${SESSION_TASK_ID:-${LC_EPIC:-cursor-driver}}"
  # Linked worktrees carry no venv; the validated durable helper root does.
  "$LC_DURABLE_HELPER_ROOT/.venv/bin/python" -m scripts.orchestration.observer_heartbeat \
    --agent cursor \
    --task-id "$task_id" \
    --epic "$LC_EPIC" \
    --status working \
    --summary "cursor driver occupancy heartbeat" \
    >/dev/null || true
}

launcher_cursor_observer_renew_loop() {
  [ "$LC_PROVIDER" = "cursor" ] || return 0
  [ "$LC_MODE" = "driver" ] || return 0
  [ "$LC_DRY_RUN" != "1" ] || return 0
  local child_pid="$1"
  (
    # Same orphan class as the driver renew loop (#7832): an untracked
    # `sleep 480` outlives a TERM'd subshell and holds the launcher's output
    # pipes open past any caller timeout. Wait on an anonymous FIFO instead.
    local observer_stop=""
    local slices=0
    local wait_fifo wait_fd=""
    trap 'observer_stop=1' INT TERM HUP
    if wait_fifo="$(mktemp -u)" && mkfifo "$wait_fifo"; then
      if { exec 215<>"$wait_fifo"; }; then
        wait_fd=215
      fi
      rm -f "$wait_fifo"
    fi
    while [ -z "$observer_stop" ] && kill -0 "$child_pid" 2>/dev/null; do
      # Short slices only: a long `read -t` resumes its full timeout after a
      # trapped signal instead of returning, which would stall teardown.
      slices=4800
      while [ "$slices" -gt 0 ] && [ -z "$observer_stop" ] && kill -0 "$child_pid" 2>/dev/null; do
        if [ -n "$wait_fd" ]; then
          read -r -t 0.1 -u "$wait_fd" _ 2>/dev/null || true
        else
          # FIFO setup failed: a stop can orphan at most one 0.1s sleep.
          sleep 0.1
        fi
        slices=$((slices - 1))
      done
      [ -n "$observer_stop" ] && break
      if ! kill -0 "$child_pid" 2>/dev/null; then
        break
      fi
      launcher_cursor_observer_presence
    done
  ) &
  LC_OBSERVER_HEARTBEAT_PID=$!
}

launcher_stop_cursor_observer_renew() {
  if [ -n "${LC_OBSERVER_HEARTBEAT_PID:-}" ]; then
    kill "$LC_OBSERVER_HEARTBEAT_PID" 2>/dev/null || true
    wait "$LC_OBSERVER_HEARTBEAT_PID" 2>/dev/null || true
    LC_OBSERVER_HEARTBEAT_PID=""
  fi
}

launcher_driver_renew_loop() {
  [ "$LC_MODE" = "driver" ] || return 0
  [ "${LC_DRIVER_LEASE_CLAIMED:-0}" = "1" ] || return 0
  [ "$LC_DRY_RUN" != "1" ] || return 0
  local child_pid="$1"
  local renew_started=$SECONDS
  local heartbeat_error
  local renew_interval="${SESSION_STREAM_RENEW_INTERVAL_SECONDS:-300}"
  local renew_jitter="${SESSION_STREAM_RENEW_JITTER_SECONDS:-30}"
  local launcher_pid="$$"
  (
    # A backgrounded interval sleep can be orphaned when TERM lands between its
    # spawn and the PID capture; the orphan keeps the launcher's output pipes
    # open past any caller timeout (#7832). Wait on an anonymous FIFO instead:
    # with no child process, nothing can outlive this subshell. These libraries
    # do not require Bash 4; reserve fd 214 instead of {var} FDs.
    local renew_stop=""
    local slices=0
    local wait_fifo wait_fd=""
    trap 'renew_stop=1' INT TERM HUP
    if wait_fifo="$(mktemp -u)" && mkfifo "$wait_fifo"; then
      if { exec 214<>"$wait_fifo"; }; then
        wait_fd=214
      fi
      rm -f "$wait_fifo"
    fi
    while [ -z "$renew_stop" ] && kill -0 "$launcher_pid" 2>/dev/null && kill -0 "$child_pid" 2>/dev/null; do
      # Five minutes with a bounded +/-30s jitter avoids synchronized renewals.
      # Short slices only: a long `read -t` resumes its full timeout after a
      # trapped signal instead of returning, which would stall teardown.
      slices=$(( (renew_interval - renew_jitter + RANDOM % (2 * renew_jitter + 1)) * 10 ))
      while [ "$slices" -gt 0 ] && [ -z "$renew_stop" ] && kill -0 "$launcher_pid" 2>/dev/null && kill -0 "$child_pid" 2>/dev/null; do
        if [ -n "$wait_fd" ]; then
          read -r -t 0.1 -u "$wait_fd" _ 2>/dev/null || true
        else
          # FIFO setup failed: a stop can orphan at most one 0.1s sleep.
          sleep 0.1
        fi
        slices=$((slices - 1))
      done
      [ -n "$renew_stop" ] && break
      if ! kill -0 "$launcher_pid" 2>/dev/null || ! kill -0 "$child_pid" 2>/dev/null; then
        break
      fi
      if heartbeat_error="$("$LC_DURABLE_HELPER_ROOT/.venv/bin/python" -m scripts.session_supervisor heartbeat --role driver 2>&1 >/dev/null)"; then
        renew_started=$SECONDS
        continue
      fi
      if printf '%s' "$heartbeat_error" | grep -q 'LEASE LOST'; then
        printf 'LEASE LOST — stopping driver after fenced heartbeat.\n' >&2
        kill -TERM "$child_pid" 2>/dev/null || true
        break
      fi
      # Transport errors are retryable until this lease could no longer be
      # alive.  A failed heartbeat is not permission to claim a new lease.
      if [ $((SECONDS - renew_started)) -ge "${SESSION_STREAM_TTL_SECONDS:-900}" ]; then
        printf 'LEASE LOST — Monitor heartbeat did not recover before TTL.\n' >&2
        kill -TERM "$child_pid" 2>/dev/null || true
        break
      fi
    done
  ) &
  LC_DRIVER_RENEW_PID=$!
}

launcher_stop_driver_renew() {
  if [ -n "${LC_DRIVER_RENEW_PID:-}" ]; then
    kill "$LC_DRIVER_RENEW_PID" 2>/dev/null || true
    wait "$LC_DRIVER_RENEW_PID" 2>/dev/null || true
    LC_DRIVER_RENEW_PID=""
  fi
}

launcher_classify_close_failure() {
  # Map known-safe marker substrings from scripts.session_supervisor's stderr
  # to a stable, privacy-safe class. The caller never echoes the raw text this
  # matches against — only the fixed code names below are safe to log, so this
  # function must never print anything but one of them, regardless of how
  # hostile the captured stderr is.
  local stderr_text="$1"
  case "$stderr_text" in
    *'missing required hook environment'*)
      printf 'missing-required-environment' ;;
    *'LEASE LOST'*|*'fenced the exact lease'*|*'not the current fenced lease'*|*'does not match the supplied historical lease'*|*'has no exact active lease'*)
      printf 'lease-fenced' ;;
    *'Monitor API unreachable'*)
      printf 'monitor-unreachable' ;;
    *'Monitor API'*|*'monitor URL must be an HTTP loopback URL'*)
      printf 'monitor-error' ;;
    *'session-supervisor:'*)
      printf 'store-error' ;;
    *)
      printf 'unknown' ;;
  esac
}

launcher_close_driver_lease() {
  # Close only the exact exported, fenced lease. The store operation is
  # idempotent, so a bounded retry is safe when the first client invocation is
  # interrupted after the transaction commits but before it returns.
  [ "${LC_DRIVER_LEASE_CLOSED:-0}" = "1" ] && return 0

  local attempt=0 delay=1 remaining
  local close_stderr="" close_failure_reason
  local retry_seconds="${LC_DRIVER_CLOSE_RETRY_SECONDS:-600}"
  case "$retry_seconds" in
    ''|*[!0-9]*) retry_seconds=600 ;;
  esac
  local deadline=$((SECONDS + 10#$retry_seconds))
  while :; do
    attempt=$((attempt + 1))
    # Linked worktrees carry no venv; the validated durable helper root does.
    # Capture stderr per attempt for classification only — it is never echoed.
    if close_stderr="$("$LC_DURABLE_HELPER_ROOT/.venv/bin/python" \
        -m scripts.session_supervisor close --role driver 2>&1 >/dev/null)"; then
      LC_DRIVER_LEASE_CLOSED=1
      return 0
    fi
    close_failure_reason="$(launcher_classify_close_failure "$close_stderr")"
    case "$close_failure_reason" in
      lease-fenced|missing-required-environment) break ;;
      monitor-unreachable|monitor-error)
        remaining=$((deadline - SECONDS))
        [ "$remaining" -gt 0 ] || break
        [ "$delay" -le "$remaining" ] || delay=$remaining
        echo "waiting for Monitor API to recover (close attempt $attempt)" >&2
        sleep "$delay"
        delay=$((delay * 2))
        [ "$delay" -le 30 ] || delay=30
        ;;
      *) [ "$attempt" -lt 2 ] || break ;;
    esac
  done
  launcher_error "failed to close the exact ${LC_PROVIDER} driver lease after $attempt attempts. close_failure_reason=${close_failure_reason}"
  return 1
}

launcher_close_failed_driver_lease() {
  # A provider canary runs after the lease claim. Close the exact exported
  # session-stream envelope before refusing the launch, so another certified
  # driver is not blocked behind this failed cold start until its TTL expires.
  launcher_close_driver_lease || true
}

launcher_forward_driver_signal() {
  local signal="$1"
  local exit_code="$2"
  trap - "$signal"
  if [ -n "${LC_DRIVER_CHILD_PID:-}" ] && kill -0 "$LC_DRIVER_CHILD_PID" 2>/dev/null; then
    kill -s "$signal" "$LC_DRIVER_CHILD_PID" 2>/dev/null || true
    wait "$LC_DRIVER_CHILD_PID" 2>/dev/null || true
  fi
  LC_DRIVER_CHILD_PID=""
  session_supervisor_stop_inbox_watch
  launcher_stop_driver_renew
  launcher_stop_cursor_observer_renew
  launcher_close_driver_lease || true
  trap - EXIT INT TERM HUP
  exit "$exit_code"
}

# Test seam: tests may widen the check-to-wait window; production leaves this a no-op.
launcher_driver_wait_hook() { :; }

launcher_exec_command() {
  # Interactive sessions retain the direct exec contract. A lease-owning
  # driver keeps this small supervisor shell alive so normal exit and
  # termination signals can atomically close the exact fenced session.
  if [ "$LC_MODE" != "driver" ] \
      || [ "${LC_DRIVER_LEASE_ENABLED:-1}" != "1" ] \
      || [ "${LC_DRIVER_LEASE_CLAIMED:-0}" != "1" ]; then
    exec "$@"
  fi

  local provider_rc=0
  local close_rc=0
  # Record the executable while the initial provider's PATH is still available.
  LC_DRIVER_PROVIDER_COMMAND="${1##*/}"
  LC_DRIVER_PROVIDER_EXECUTABLE="$(type -P -- "$1")" || LC_DRIVER_PROVIDER_EXECUTABLE=""
  if [ -n "$LC_DRIVER_PROVIDER_EXECUTABLE" ]; then
    LC_DRIVER_PROVIDER_EXECUTABLE="$(cd -- "$(dirname -- "$LC_DRIVER_PROVIDER_EXECUTABLE")" && pwd)/${LC_DRIVER_PROVIDER_EXECUTABLE##*/}"
  fi
  LC_DRIVER_CHILD_PID=""
  LC_DRIVER_LEASE_CLOSED=0
  LC_DRIVER_RENEW_PID=""
  LC_DRIVER_PENDING_SIGNAL=""
  LC_DRIVER_PENDING_EXIT=0
  LC_SUPERVISORY_FAILURE_REASON=""
  trap 'exec 213>&-; session_supervisor_stop_inbox_watch; launcher_close_driver_lease || true' EXIT
  # Bash may deliver a trap between an asynchronous spawn and its $! capture.
  # Defer shutdown until every child has an owned PID, or cleanup can orphan
  # the watcher/renewal process and leave inherited output pipes open.
  trap 'LC_DRIVER_PENDING_SIGNAL=INT; LC_DRIVER_PENDING_EXIT=130' INT
  trap 'LC_DRIVER_PENDING_SIGNAL=TERM; LC_DRIVER_PENDING_EXIT=143' TERM
  trap 'LC_DRIVER_PENDING_SIGNAL=HUP; LC_DRIVER_PENDING_EXIT=129' HUP

  # Explicitly duplicate stdin: Bash otherwise redirects asynchronous commands
  # from /dev/null when job control is disabled, which would break TUIs. Reset
  # the background subshell's inherited signal dispositions before exec so
  # forwarded INT/TERM/HUP reach the provider rather than being ignored.
  (
    trap - INT TERM HUP
    exec "$@"
  ) 0<&0 &
  LC_DRIVER_CHILD_PID=$!
  launcher_driver_renew_loop "$LC_DRIVER_CHILD_PID"
  launcher_cursor_observer_renew_loop "$LC_DRIVER_CHILD_PID"
  if ! session_supervisor_start_inbox_watch; then
    session_supervisor_stop_provider_for_wake
    provider_rc=1
  fi
  trap 'launcher_forward_driver_signal INT 130' INT
  trap 'launcher_forward_driver_signal TERM 143' TERM
  trap 'launcher_forward_driver_signal HUP 129' HUP
  if [ -n "$LC_DRIVER_PENDING_SIGNAL" ]; then
    launcher_forward_driver_signal "$LC_DRIVER_PENDING_SIGNAL" "$LC_DRIVER_PENDING_EXIT"
  fi
  if [ "$provider_rc" -eq 0 ]; then
    # A trapped USR1 must not interrupt a child wait: Bash can reap the exiting
    # watcher inside it and lose its status, leaving the later watcher wait
    # blocked in waitpid(-1) forever (#7824). Read bounded slices on an anonymous
    # FIFO instead: the trap runs, read -t finishes its timeout, then we re-check.
    # These libraries do not require Bash 4; reserve fd 213 instead of {var} FDs.
    local wait_fifo wait_fd=""
    if wait_fifo="$(mktemp -u)" && mkfifo "$wait_fifo"; then
      if { exec 213<>"$wait_fifo"; }; then
        wait_fd=213
      fi
      rm -f "$wait_fifo"
    fi
    # Cleanup that waits or exits inside a trapped read can abort Bash. Record
    # termination here and forward it only after the bounded slice returns.
    trap 'LC_DRIVER_PENDING_SIGNAL=INT; LC_DRIVER_PENDING_EXIT=130' INT
    trap 'LC_DRIVER_PENDING_SIGNAL=TERM; LC_DRIVER_PENDING_EXIT=143' TERM
    trap 'LC_DRIVER_PENDING_SIGNAL=HUP; LC_DRIVER_PENDING_EXIT=129' HUP
    local wake_rc watcher_finished=0
    while kill -0 "$LC_DRIVER_CHILD_PID" 2>/dev/null; do
      # Failure exits intentionally send no USR1. Observe child death as well
      # as notifications, and never wait on a still-running watcher after USR1.
      if [ -n "${LC_SUPERVISORY_WATCH_PID:-}" ] && ! kill -0 "$LC_SUPERVISORY_WATCH_PID" 2>/dev/null; then
        wake_rc=0
        session_supervisor_read_wake || wake_rc=$?
        if [ "$wake_rc" -eq 0 ] && ! session_supervisor_preflight_successor; then
          # A refused successor must leave the provider and lease alive. Resume
          # inbox supervision so a later wake can retry after the CLI is fixed.
          LC_SUPERVISORY_DELIVERY=""
          session_supervisor_stop_inbox_watch
          if session_supervisor_start_inbox_watch; then
            continue
          fi
          wake_rc=1
        fi
        if [ "$wake_rc" -ne 76 ]; then
          watcher_finished=1
          provider_rc=$wake_rc
          [ "$wake_rc" -eq 0 ] || LC_SUPERVISORY_DELIVERY=""
          break
        fi
      fi
      launcher_driver_wait_hook
      if [ -n "$wait_fd" ]; then
        read -r -t 0.1 -u "$wait_fd" _ 2>/dev/null || true
      else
        # FIFO setup failed: retain the old slice (and its race) rather than spin.
        sleep 0.1 & wait "$!" 2>/dev/null || true
      fi
      if [ -n "$LC_DRIVER_PENDING_SIGNAL" ]; then
        exec 213>&-
        launcher_forward_driver_signal "$LC_DRIVER_PENDING_SIGNAL" "$LC_DRIVER_PENDING_EXIT"
      fi
    done
    exec 213>&-
    trap 'launcher_forward_driver_signal INT 130' INT
    trap 'launcher_forward_driver_signal TERM 143' TERM
    trap 'launcher_forward_driver_signal HUP 129' HUP
    # Include a signal recorded between the last slice and restoring the traps.
    if [ -n "$LC_DRIVER_PENDING_SIGNAL" ]; then
      launcher_forward_driver_signal "$LC_DRIVER_PENDING_SIGNAL" "$LC_DRIVER_PENDING_EXIT"
    fi
    if [ "$watcher_finished" != 1 ]; then
      wait "$LC_DRIVER_CHILD_PID" || provider_rc=$?
    fi
  fi
  if [ "${watcher_finished:-0}" = 1 ]; then
    session_supervisor_stop_provider_for_wake
  fi
  LC_DRIVER_CHILD_PID=""
  session_supervisor_stop_inbox_watch
  launcher_stop_driver_renew
  launcher_stop_cursor_observer_renew
  launcher_close_driver_lease || close_rc=$?
  trap - EXIT INT TERM HUP

  if [ -n "${LC_SUPERVISORY_FAILURE_REASON:-}" ]; then
    session_supervisor_publish_start_failure "${SESSION_STREAM_ID:-}" \
      "${SESSION_STREAM_GENERATION:-}" "$LC_SUPERVISORY_FAILURE_REASON"
  fi
  if [ "$close_rc" -ne 0 ] && [ "$provider_rc" -eq 0 ]; then
    return "$close_rc"
  fi
  if [ "$close_rc" -eq 0 ] && [ -n "${LC_SUPERVISORY_DELIVERY:-}" ]; then
    session_supervisor_exec_successor
    return 1
  fi
  return "$provider_rc"
}

launcher_forward_args_have_agent() {
  local arg
  for arg in "${LC_FORWARD_ARGS[@]}"; do
    case "$arg" in
      --agent|--agent=*) return 0 ;;
    esac
  done
  return 1
}

launcher_inject_driver_agent() {
  # Claude Code selects its system prompt from --agent. The project default
  # (.claude/settings.json "agent") is the main orchestrator, which is the wrong
  # prompt for every non-curriculum driver lane, so resolve the lane's
  # driver_agent_type from scripts/config/area_assignments.yaml and inject it
  # unless the caller chose an agent explicitly.
  [ "$LC_PROVIDER" = "claude" ] || return 0
  [ -n "${LC_EPIC:-}" ] || return 0
  if launcher_forward_args_have_agent; then
    return 0
  fi
  # The validated durable helper root's interpreter only; a worktree-local
  # .venv is never tried (#9118, #9121).
  local py="$LC_DURABLE_HELPER_ROOT/.venv/bin/python"
  local agent_type=""
  [ -x "$py" ] || return 0
  agent_type="$(cd "$LC_SESSION_ROOT" && "$py" -m scripts.orchestration.driver_agent_type --lane "$LC_EPIC" 2>/dev/null || true)"
  if [ -z "$agent_type" ]; then
    printf 'launcher: no driver_agent_type for lane %s in area_assignments.yaml; keeping the settings default agent\n' "$LC_EPIC" >&2
    return 0
  fi
  LC_FORWARD_ARGS=(--agent "$agent_type" "${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = "1" ]; then
    printf 'launcher: would select agent %s for lane %s\n' "$agent_type" "$LC_EPIC"
  fi
}

launcher_bind_drive_epic() {
  local fleet_clause
  if [ -r "$LC_ROOT/scripts/lib/fleet_comms_cold_start.sh" ]; then
    # shellcheck source=scripts/lib/fleet_comms_cold_start.sh
    source "$LC_ROOT/scripts/lib/fleet_comms_cold_start.sh"
  fi
  if command -v fleet_comms_resolve_plane_mode >/dev/null 2>&1; then
    # shellcheck disable=SC2155  # export of resolved plane mode is intentional
    export FLEET_COMMS_PLANE_MODE="${FLEET_COMMS_PLANE_MODE:-$(fleet_comms_resolve_plane_mode)}"
  fi
  if command -v fleet_comms_cold_clause >/dev/null 2>&1; then
    fleet_clause="$(fleet_comms_cold_clause)"
  else
    fleet_clause='Fleet-comms: run plane-status; cross-family review is direct ask-<lane> per the skill (§6) — verdict posted on the PR, merge when CI green, sealed formal CF is retired; authority mode is durable state and ACP is provider transport.'
  fi
  LC_DRIVER_PROMPT="Load agents_extensions/shared/skills/drive-epic/SKILL.md before acting. The launcher already claimed the ${LC_EPIC} lease and ran its provider canary; do not claim, renew, or reopen the lease. ${fleet_clause} Consult the Work API projection (http://127.0.0.1:8765/api/work/v1/projection) for orientation and treat grok-bot QA-observer issues as a queue input — the skill covers both. Obtain independent cross-family review."
  launcher_inject_driver_agent
  LC_FORWARD_ARGS+=("$LC_DRIVER_PROMPT")
  if [ "$LC_DRY_RUN" = "1" ]; then
    printf 'launcher: would bind drive-epic after lease and provider canary\n'
  fi
}

launcher_publication_path() {
  local shim_path="$LC_ROOT/scripts/agent_runtime/shims" real_path="" entry
  if [[ -z "${AGENT_REAL_GH:-}" ]]; then
    IFS=':' read -r -a publication_paths <<< "${PATH:-}"
    for entry in "${publication_paths[@]}"; do
      [[ "$entry" == */scripts/agent_runtime/shims ]] && continue
      if [[ -x "$entry/gh" ]]; then
        real_path="$(cd "$entry" && pwd)/gh"
        break
      fi
    done
    export AGENT_REAL_GH="$real_path"
  fi
  export AGENT_ORIGINAL_PATH="${AGENT_ORIGINAL_PATH:-${PATH:-}}"
  export PATH="$shim_path:${PATH:-}"
  unset LU_OPSEC_OVERRIDE
}

launcher_main() {
  LC_PROVIDER="$1"
  LC_MODE="$2"
  shift 2
  # Consumed by session_supervisor_exec_successor in the sourced helper.
  # shellcheck disable=SC2034
  LC_DRIVER_ORIGINAL_ARGS=("$@")
  # Re-entry must retain --force for the first actual lease acquisition;
  # successor arguments intentionally drop it later in this same startup.
  LC_SCOPE_ORIGINAL_ARGS=("$@")
  LC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  # Keep route selection self-contained for minimal/synthetic launchers while
  # sourcing the richer cold-start clause whenever the full checkout is
  # present. Neither path starts an ACP process.
  export LU_AGENT_COMM_TRANSPORT="${LU_AGENT_COMM_TRANSPORT:-acp}"
  if [ -r "$LC_ROOT/scripts/lib/fleet_comms_cold_start.sh" ]; then
    # shellcheck source=scripts/lib/fleet_comms_cold_start.sh
    source "$LC_ROOT/scripts/lib/fleet_comms_cold_start.sh"
  fi
  launcher_clear_foreign_route_state
  launcher_defaults
  launcher_parse "$@"
  # Defaults and parsing set the model before this guard reads it. Reject an
  # uncertified Gemini driver model before scope entry, root resolution, adapter
  # preflight, deployment, or any continuity/lease/canary/provider work. Help
  # remains a read-only request.
  launcher_refuse_uncertified_gemini_driver
  launcher_drop_force_from_successor_args
  launcher_normalize_effort
  # Provider adapters are sourced dynamically and consume these values.
  export LC_ENDPOINT LC_ISOLATE_CONFIG
  launcher_resolve_roots
  launcher_publication_path
  launcher_normalize_model
  # shellcheck source=scripts/lib/handoff_identity.sh
  source "$LC_ROOT/scripts/lib/handoff_identity.sh"
  launcher_validate_mode
  launcher_validate_driver_certification
  # Every admitted driver path enters before expensive preparation, import and lease.
  if [ "$LC_MODE" = driver ]; then
    if [ "$LC_DRY_RUN" = 1 ]; then
      printf 'LAUNCHER_DRY_RUN=1: would enter a verified per-driver memory-limited scope in lu-driver.slice\n'
    else
      # shellcheck source=scripts/lib/driver_scope.sh
      source "$LC_ROOT/scripts/lib/driver_scope.sh" || exit 6
      launcher_enter_driver_scope || exit 6
    fi
  fi
  # Before any adapter check, plane probe or deploy: no core, no launch.
  launcher_load_rules_core
  launcher_export_git_identity || exit 3
  # shellcheck disable=SC1090
  source "$LC_ROOT/scripts/launchers/${LC_PROVIDER}.sh"
  launcher_adapter_validate
  # Native Grok drivers inspect deployed project hooks. Deploy first so a
  # first launch or changed profile is checked against its fresh deployment.
  if [ "$LC_PROVIDER:$LC_MODE:$LC_HARNESS" != grok:driver:grok ]; then
    launcher_adapter_preflight
  fi

  if [ "$LC_DRY_RUN" != "1" ]; then
    if declare -F fleet_comms_warn_if_plane_unreachable >/dev/null 2>&1; then
      fleet_comms_warn_if_plane_unreachable
    fi
  fi

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

  if [ "$LC_PROVIDER:$LC_MODE:$LC_HARNESS" = grok:driver:grok ]; then
    launcher_adapter_preflight || exit $?
  fi

  if [ "$LC_MODE" = "driver" ] && [ "$LC_GOVERNOR" = "0" ]; then
    local canary_rc=0
    launcher_prepare_driver_identity
    if [ "$LC_DRY_RUN" != "1" ]; then
      # This is deliberately before adapter prelease and before any provider
      # packet scan: every driver must see an imported packet at cold start.
      launcher_import_rollover_bundle
    fi
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
    launcher_claim_driver_lease || exit 1
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

#!/usr/bin/env bash

launcher_adapter_validate() {
  case "$LC_HARNESS" in kimi-code|claude-code) ;; *) launcher_error 'Kimi supports --harness kimi-code|claude-code.'; exit 2 ;; esac
  case "$LC_ENDPOINT" in coding|platform) ;; *) launcher_error 'Kimi endpoint must be coding or platform.'; exit 2 ;; esac
  if [ "$LC_HARNESS" = kimi-code ] && ! _kimi_forward_args_are_fresh_session; then
    launcher_error "Kimi Code starts fresh sessions only: $_KIMI_BAD_ARG is not an admitted fresh-session option and could restore a session or pick an agent without the rules core. Kimi seats take fresh web/UI/backend coding tasks; start a new session."
    exit 2
  fi
}
launcher_adapter_preflight() {
  if [ "$LC_HARNESS" = kimi-code ]; then
    LC_AUTH_SOURCE='kimi-code-oauth'
    launcher_require_binary kimi 'Kimi Code executable is unavailable.' 3 || exit $?
    # Catalog-backed alias resolution (review finding on #5958 r3): the native
    # kimi CLI rejects bare aliases like "k3" ("not configured in config.toml");
    # resolve every alias to the configured native model id before exec.
    local py
    py="$(launcher_project_python)" || exit 3
    if ! LC_MODEL="$("$py" "$LC_ROOT/scripts/review/model_catalog.py" \
        --resolve-kimi-model "$LC_MODEL" --format native)"; then
      launcher_error "unknown --model '$LC_MODEL' (use k3-256k, k3, k2.7, k2.7-highspeed)."
      exit 2
    fi
    return
  fi
  # shellcheck source=scripts/lib/kimicc_route.sh
  source "$LC_ROOT/scripts/lib/kimicc_route.sh"
  ENDPOINT="$LC_ENDPOINT" MODEL_ALIAS="$LC_MODEL" ISOLATE_CONFIG="$LC_ISOLATE_CONFIG"
  export ENDPOINT MODEL_ALIAS ISOLATE_CONFIG
  kimicc_configure_route "$LC_SESSION_ROOT" "$LC_SESSION_ROOT" "$LC_DURABLE_HELPER_ROOT" || exit $?
  LC_AUTH_SOURCE="$AUTH_SOURCE"
  launcher_require_binary claude 'Claude Code executable is unavailable for the Kimi harness.' 3 || exit $?
}
launcher_adapter_canary() {
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'kimi adapter: would run provider canary'; fi
  return 0
}
# Kimi Code binds an agent at session creation, and the rules core rides in on
# that agent (--agent-file). A resumed session restores its old agent and a custom
# agent replaces ours, so neither would carry the core. Rather than deny-list every
# spelling of resume/continue/session/agent (the CLI accepts many: -S<id>, -r<id>,
# clustered -yc, aliases), the launcher ALLOWS only the options of the installed
# CLI that cannot change the session or agent, and refuses everything else: unknown
# flags, subcommands (session, fork, ...), positionals, and a bare `--`.
#   boolean:     -y --yolo, --auto, --plan, -h --help, -V --version
#   value taking: -p --prompt, --output-format, --skills-dir, --add-dir
# --model/-m is refused too: the launcher already selects the catalog-resolved model.
_kimi_forward_args_are_fresh_session() {
  local args=("${LC_FORWARD_ARGS[@]+"${LC_FORWARD_ARGS[@]}"}") i=0 arg flag cluster ch
  _KIMI_BAD_ARG=""
  while [ "$i" -lt "${#args[@]}" ]; do
    arg="${args[$i]}"
    i=$((i + 1))
    case "$arg" in
      --yolo|--auto|--plan|--help|--version) ;;
      --prompt|--output-format|--skills-dir|--add-dir)
        # the value is the next argument; one that looks like an option is ambiguous, so refuse it
        if [ "$i" -ge "${#args[@]}" ] || [[ "${args[$i]}" == -* ]]; then _KIMI_BAD_ARG="$arg"; return 1; fi
        i=$((i + 1))
        ;;
      --prompt=?*|--output-format=?*|--skills-dir=?*|--add-dir=?*) ;;
      --*)
        flag="${arg%%=*}"
        _KIMI_BAD_ARG="$flag"
        return 1
        ;;
      -?*)
        # short cluster: boolean letters, optionally ending in -p with attached or next value
        cluster="${arg#-}"
        while [ -n "$cluster" ]; do
          ch="${cluster:0:1}"
          cluster="${cluster:1}"
          case "$ch" in
            y|h|V) ;;
            p)
              if [ -z "$cluster" ]; then
                if [ "$i" -ge "${#args[@]}" ] || [[ "${args[$i]}" == -* ]]; then _KIMI_BAD_ARG="$arg"; return 1; fi
                i=$((i + 1))
              elif [[ "$cluster" == -* ]]; then
                _KIMI_BAD_ARG="$arg"
                return 1
              fi
              cluster=""
              ;;
            *) _KIMI_BAD_ARG="$arg"; return 1 ;;
          esac
        done
        ;;
      *)
        _KIMI_BAD_ARG="$arg"
        return 1
        ;;
    esac
  done
  return 0
}
launcher_adapter_exec() {
  local cmd agent_file
  if [ "$LC_HARNESS" = kimi-code ]; then
    cmd=(kimi --model "$LC_MODEL")
    # The agent file renders Kimi's default prompt (${base_prompt}) and appends the core.
    if [ -n "${LC_RULES_CORE:-}" ]; then
      if agent_file="$(rules_core_kimi_agent_file "$LC_DURABLE_HELPER_ROOT/.venv/bin/python" "$LC_ROOT")"; then
        cmd+=(--agent-file "$agent_file")
      else
        rules_core_refuse "Kimi agent file could not be written"
        exit 1
      fi
    fi
  else
    cmd=(claude --model "$LEAD_MODEL")
    if [ -n "${LC_RULES_CORE:-}" ]; then
      cmd+=(--append-system-prompt "$LC_RULES_CORE")
    fi
  fi
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; launcher_print_argv "${cmd[@]}"; printf '\n'; return 0; fi
  exec "${cmd[@]}"
}

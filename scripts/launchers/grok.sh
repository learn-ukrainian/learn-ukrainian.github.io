#!/usr/bin/env bash

launcher_adapter_validate() {
  # shellcheck disable=SC2153 # LC_MODE is supplied by launcher_core.sh.
  if [ "$LC_MODE" = driver ] && [ "$LC_HARNESS" = grok ]; then
    local forwarded forwarded_name
    for forwarded in "${LC_FORWARD_ARGS[@]}"; do
      case "$forwarded" in
        # No value-taking flags, positional prompts, subcommands or aliases:
        # only presentation changes and tool removal preserve the inspected
        # project and the launcher-bound process tree. See the canary runbook.
        --debug|--fullscreen|--minimal|--no-alt-screen|--disable-web-search|--no-subagents)
          ;;
        *)
          # Name the option without reflecting values or positional prompt
          # text into diagnostics.
          case "$forwarded" in
            --*) forwarded_name="${forwarded%%=*}" ;;
            -?*) forwarded_name="${forwarded:0:2}" ;;
            *) forwarded_name='positional argument or subcommand' ;;
          esac
          launcher_error "Grok driver forwarded option '$forwarded_name' is not allowlisted: project root, tool execution site, session identity and leader mode are launcher-bound. Allowed flags: --debug, --fullscreen, --minimal, --no-alt-screen, --disable-web-search, --no-subagents."
          exit 2
          ;;
      esac
    done
  fi
  case "$LC_HARNESS" in
    grok) ;;
    hermes)
      launcher_hermes_validate
      LC_MODEL="${LC_MODEL:-grok-4.7}"
      # shellcheck disable=SC2034 # consumed by shared Hermes execution
      LC_HERMES_PROVIDER=xai-oauth
      case "$LC_EFFORT" in
        ""|low|medium|high|xhigh) ;;
        *) launcher_error 'Grok/Hermes supports only low|medium|high|xhigh effort.'; exit 2 ;;
      esac
      ;;
    *) launcher_error 'Grok supports only --harness grok or --harness hermes.'; exit 2 ;;
  esac
}
launcher_adapter_preflight() {
  if [ "$LC_HARNESS" = hermes ]; then launcher_hermes_preflight; return; fi
  LC_AUTH_SOURCE='grok-cli-oauth'
  launcher_require_binary grok 'Grok executable is unavailable.' 3 || exit $?
  if [ "$LC_MODE" = driver ]; then
    if [ "${LC_DRY_RUN:-0}" = 1 ]; then
      echo 'LAUNCHER_DRY_RUN=1: would require a trusted folder, a matching deployed Grok driver profile and both discovered pre_tool_use matchers'
      return 0
    fi
    local inspection project_python="$LC_DURABLE_HELPER_ROOT/.venv/bin/python"
    if ! inspection="$(cd "$LC_ROOT" && grok inspect --json)"; then
      launcher_error 'Grok driver preflight: grok inspect --json failed. Run grok inspect --json in this checkout and resolve its error, then retry.'
      return 2
    fi
    if [ ! -x "$project_python" ]; then
      launcher_error 'Grok driver preflight: project interpreter unavailable. Restore the shared project interpreter, then retry.'
      return 2
    fi
    "$project_python" "$LC_ROOT/scripts/agent_runtime/grok_hook_bridge.py" --driver-preflight "$LC_ROOT" <<< "$inspection" || return 2
  fi
}
launcher_adapter_canary() {
  if [ "$LC_DRY_RUN" = 1 ]; then echo 'grok adapter: would run provider canary'; fi
  return 0
}
launcher_adapter_exec() {
  # Clear an inherited parent binding even on an interactive/Hermes launch.
  unset LU_GROK_DRIVER_SESSION_ID LU_GROK_SOURCE_ROOT LU_GROK_PROJECT_PYTHON
  if [ "$LC_HARNESS" = hermes ]; then launcher_hermes_exec; return; fi
  local cmd=(grok)
  if [ "$LC_MODE" = driver ]; then
    export LU_GROK_SOURCE_ROOT="$LC_ROOT"
    export LU_GROK_PROJECT_PYTHON="$LC_DURABLE_HELPER_ROOT/.venv/bin/python"
    LU_GROK_DRIVER_SESSION_ID="$("$LU_GROK_PROJECT_PYTHON" -c 'import uuid; print(uuid.uuid4())')" || return 2
    export LU_GROK_DRIVER_SESSION_ID
    cmd+=(--session-id "$LU_GROK_DRIVER_SESSION_ID" --no-leader)
  fi
  # Only pin --model / --reasoning-effort when the caller asked for them;
  # otherwise the Grok TUI keeps whatever was selected last in the session.
  if [ -n "${LC_MODEL:-}" ]; then
    cmd+=(--model "$LC_MODEL")
  fi
  if [ -n "${LC_EFFORT:-}" ]; then
    cmd+=(--reasoning-effort "$LC_EFFORT")
  fi
  # --rules appends to Grok's system prompt; native AGENTS.md loading is unproven.
  if [ -n "${LC_RULES_CORE:-}" ]; then
    cmd+=(--rules "$LC_RULES_CORE")
  fi
  cmd+=("${LC_FORWARD_ARGS[@]}")
  if [ "$LC_DRY_RUN" = 1 ]; then printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"; launcher_print_argv "${cmd[@]}"; printf '\n'; return 0; fi
  launcher_exec_command "${cmd[@]}"
}

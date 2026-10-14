#!/usr/bin/env bash

launcher_muse_usage() {
  cat <<'EOF'
Usage: ./start-muse-driver.sh [OPTIONS] [PROMPT ...]

Start the supervised Muse DevOps or Harness/monitor driver through the shared launcher core.
Real sessions are refused until native forbidden-action guards are proven.
There is no interactive launcher and no guard bypass.

Options:
  -h, --help          Show help without starting Muse or claiming a lease.
  --epic SELECTOR    Required: devops or monitor, or their supported aliases.
                     devops: infra.devops; monitor: infra.monitor, ops-api,
                     ops.api, operator-api. infra/harness remain refused.
  --model MODEL      Single ordered trial pin: muse-wonder-full-1.0.
  --effort LEVEL     none|minimal|low|medium|high|xhigh|max|ultra; default high.
  --harness muse     Native CLI only.
  --dry-run          Validate admission and print the planned argv.
  --                Positional prompt text only; provider flags are refused.

Environment:
  LAUNCHER_MODEL, LAUNCHER_EFFORT, LAUNCHER_HARNESS  Defaults for these options.
  LAUNCHER_DRY_RUN=1             Same as --dry-run.
  LAUNCHER_DRY_RUN_ARGV_FILE     Write exact NUL-separated planned argv.

EXIT CODES:
  0  Help or dry run succeeded.
  1  Shared continuity or occupied-lease refusal.
  2  Invalid usage, effort, harness or forwarded provider flag.
  3  Required executable unavailable.
  4  Model, content, stream, repository or guard admission refused.
  6  Shared driver memory scope could not be verified.

Examples:
  ./start-muse-driver.sh --help
  ./start-muse-driver.sh --epic monitor --effort high --dry-run
  LAUNCHER_DRY_RUN=1 ./start-muse-driver.sh --epic infra.devops

Unproven guards: shell, credential, publish, destructive-command, filesystem.
Unproven lifecycle hooks: session start, before prompt, after compaction, session end.
Dry-run argv is a plan, not permission to execute it directly.
EOF
}

launcher_adapter_validate() {
  [ "$LC_MODE" = driver ] || { launcher_error 'MUSE_DRIVER_ONLY'; exit 4; }
  [ "$LC_HARNESS" = muse ] || { launcher_error 'MUSE_HARNESS_UNSUPPORTED'; exit 2; }
  [ "$LC_MODEL" = muse-wonder-full-1.0 ] || { launcher_error 'MUSE_MODEL_UNCERTIFIED'; exit 4; }
  [ "$LC_DRIVER_FORCE" = 0 ] || { launcher_error 'MUSE_FORCE_FORBIDDEN'; exit 4; }
  [ "${LC_DRIVER_LEASE_ENABLED:-1}" = 1 ] || { launcher_error 'MUSE_LEASE_REQUIRED'; exit 4; }
  local arg lane stream expected_stream py classification visibility
  for arg in "${LC_FORWARD_ARGS[@]+"${LC_FORWARD_ARGS[@]}"}"; do
    case "$arg" in
      -*) launcher_error 'MUSE_PROVIDER_FLAGS_FORBIDDEN'; exit 2 ;;
    esac
  done
  lane="$(launcher_selector_lane "$LC_EPIC")" || { launcher_error 'MUSE_STREAM_NOT_ADMITTED'; exit 4; }
  case "$lane" in
    folk|bio|hramatka|open-model-data)
      launcher_error 'MUSE_UKRAINIAN_CONTENT_FORBIDDEN'; exit 4 ;;
  esac
  py="$(launcher_project_python)" || exit 3
  classification="$("$py" "$LC_ROOT/scripts/orchestration/driver_agent_type.py" --lane "$lane" --provider muse)" || {
    launcher_error 'MUSE_LANE_CLASSIFICATION_UNKNOWN'; exit 4;
  }
  if [ "$classification" = curriculum-orchestrator ] || [ "${LU_RULES_SEAT:-core}" = content ]; then
    launcher_error 'MUSE_CURRICULUM_CONTENT_FORBIDDEN'; exit 4
  fi
  [ "$classification" = infra-orchestrator ] || { launcher_error 'MUSE_LANE_CLASSIFICATION_UNKNOWN'; exit 4; }
  stream="$(launcher_selector_stream "$LC_EPIC")" || { launcher_error 'MUSE_STREAM_NOT_ADMITTED'; exit 4; }
  case "$lane" in
    devops|monitor) ;;
    *) launcher_error 'MUSE_STREAM_NOT_ADMITTED'; exit 4 ;;
  esac
  expected_stream="$(launcher_selector_stream "$lane")" || { launcher_error 'MUSE_STREAM_NOT_ADMITTED'; exit 4; }
  [ "$stream" = "$expected_stream" ] || {
    launcher_error 'MUSE_STREAM_NOT_ADMITTED'; exit 4;
  }
  # gh resolves the checkout's repository. Missing/unknown visibility never
  # permits private source to reach the provider, including in dry runs.
  visibility="$(
    cd "$LC_ROOT" || exit 1
    unset GH_REPO GITHUB_REPOSITORY
    gh repo view --json visibility --jq .visibility 2>/dev/null
  )" || {
    launcher_error 'MUSE_REPOSITORY_VISIBILITY_UNKNOWN'; exit 4;
  }
  case "$visibility" in
    PUBLIC) ;;
    PRIVATE|INTERNAL) launcher_error 'MUSE_PRIVATE_REPOSITORY_FORBIDDEN'; exit 4 ;;
    *) launcher_error 'MUSE_REPOSITORY_VISIBILITY_UNKNOWN'; exit 4 ;;
  esac
}

launcher_adapter_preflight() {
  if [ "$LC_DRY_RUN" != 1 ]; then
    launcher_error 'MUSE_GUARD_PARITY_UNPROVEN: shell,credential,publish,destructive-command,filesystem; session-start,before-prompt,after-compaction,session-end hooks unproven'
    exit 4
  fi
  LC_AUTH_SOURCE=muse-cli-managed-auth
  echo 'muse adapter: MUSE_GUARD_PARITY_UNPROVEN: shell,credential,publish,destructive-command,filesystem; hooks unproven'
  launcher_require_binary muse 'Muse executable is unavailable.' 3 || exit $?
}

launcher_adapter_canary() {
  # Recall requires answers from a rollover session. No startup model probe.
  # shellcheck disable=SC2034 # Read by launcher_bind_drive_epic in the shared core.
  LC_PROVIDER_CANARY_RAN=0
  echo 'muse adapter: provider canary: not run; rollover uses scripts.session_canary.muse_lane mint and score'
}

launcher_adapter_exec() {
  # Repeat at the execution boundary: direct calls cannot bypass the gate.
  if [ "$LC_DRY_RUN" != 1 ]; then launcher_adapter_preflight; fi
  local cmd=(muse --provider meta --model "$LC_MODEL" --reasoning-effort "$LC_EFFORT"
    --workspace "$LC_SESSION_ROOT" --worktree off --disable-shell --disable-write)
  local prompt='' arg
  for arg in "${LC_FORWARD_ARGS[@]}"; do
    if [ -n "$prompt" ]; then prompt+=$'\n'; fi
    prompt+="$arg"
  done
  cmd+=("$(rules_core_prefix "$prompt")")
  if [ "$LC_DRY_RUN" = 1 ]; then
    printf 'LAUNCHER_DRY_RUN=1: credential_source=%s\nwould exec ' "$LC_AUTH_SOURCE"
    launcher_print_argv "${cmd[@]}"
    printf '\n'
    return 0
  fi
  launcher_exec_command "${cmd[@]}"
}

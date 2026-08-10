#!/bin/bash
# Hook: SessionStart — runs on new sessions AND resumed sessions
# Validates environment and reports project state.
# Skips in headless/pipeline mode to avoid adding latency.

SESSION_START_STARTED_SECONDS=$SECONDS

# 0. Pyenv-rehash stale-lock cleanup. Runs BEFORE the headless-skip
#    because every shell startup (including pipeline jobs) hits pyenv
#    init, and a stale lock costs 60s per Bash invocation.
#
#    Background: pyenv-rehash uses `noclobber` to write a 0-byte
#    sentinel at $PYENV_ROOT/shims/.pyenv-shim. If a rehash gets
#    killed mid-flight (laptop sleep, overnight session crash,
#    terminal closure), the sentinel survives and every subsequent
#    rehash blocks 60s waiting on the lock before giving up. Last
#    incident: stale sentinel from 2026-04-26 02:56 (overnight
#    session) made every Claude Bash tool call take 60+ seconds for
#    two days straight.
#
#    Diagnostic only: if the sentinel is older than 1 minute, report it and
#    leave removal to the explicit operator repair command. Session startup
#    must not delete machine state from an age heuristic.
#
#    Using `find -mmin +1` instead of `stat`: portable across BSD
#    (macOS) and GNU (Homebrew coreutils) without flag-flavor
#    detection. `stat -f %m` (BSD) and `stat -c %Y` (GNU) have
#    incompatible meanings — `find -mmin +1` is the same on both.
PYENV_SHIM_LOCK="${PYENV_ROOT:-$HOME/.pyenv}/shims/.pyenv-shim"
if [ -f "$PYENV_SHIM_LOCK" ] && \
   [ -n "$(find "$PYENV_SHIM_LOCK" -mmin +1 -type f 2>/dev/null)" ]; then
  echo "WARNING: pyenv rehash lock is older than one minute; inspect it, then remove it explicitly if stale: rm -f \"$PYENV_SHIM_LOCK\"" >&2
fi

# Repo-health canary: core.bare MUST be false on this working repo. A stray
# `git config core.bare true` silently breaks git status/add/commit/worktree for
# the main checkout AND every linked worktree at once (they share .git/config),
# and is never pushed so CI cannot catch it — only a local canary can. Auto-heal
# so no session inherits a broken tree. Runs BEFORE the headless-skip because
# pipeline jobs need a work tree too. See issue #2842.
_LU_REPO="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
if [ "$(git -C "$_LU_REPO" config --get core.bare 2>/dev/null)" = "true" ]; then
  git -C "$_LU_REPO" config --local core.bare false 2>/dev/null \
    && echo "⚠️  repo-health: reset core.bare true→false (git work tree was broken; see #2842)" >&2
fi

# Repo-health canary: a self-referential `node_modules` symlink (X -> X) is an
# infinite loop. `npm run <script>` builds its child PATH by walking the tree
# UPWARD and prepending every ancestor node_modules/.bin; resolving the loop
# makes `spawn` return ELOOP, so EVERY npm build dies instantly with exit 194
# and no output — looking like "Astro is broken" when it is not. Gitignored, so
# CI can't catch it; only a local canary can. Detect the exact absolute
# self-link here and leave repair to the explicit doctor command. See
# docs/bug-autopsies/node-modules-eloop-symlink.md.
for _nm in "$_LU_REPO/node_modules" "$_LU_REPO/site/node_modules"; do
  if [ -L "$_nm" ] && [ "$(readlink "$_nm" 2>/dev/null)" = "$_nm" ]; then
    echo "WARNING: self-referential symlink detected at $_nm (npm spawn ELOOP). Inspect it, then run: .venv/bin/python scripts/audit/check_self_symlinks.py --fix" >&2
  fi
done

# Skip in non-interactive (headless) mode
if [ -n "$CLAUDE_NON_INTERACTIVE" ] || [ -n "$LEARN_UKRAINIAN_PIPELINE" ] || [ -n "$GEMINI_SESSION" ]; then
  exit 0
fi

# Read hook stdin exactly once, then parse all official fields in one jq pass.
STDIN_JSON=""
if [ ! -t 0 ]; then
  STDIN_JSON=$(cat)
fi

HOOK_FIELDS=()
if [ -n "$STDIN_JSON" ]; then
  while IFS= read -r -d '' _hook_field; do
    HOOK_FIELDS+=("$_hook_field")
  done < <(printf '%s' "$STDIN_JSON" | jq -j '
    [
      (if (.session_id | type) == "string" then .session_id else "" end),
      (if (.transcript_path | type) == "string" then .transcript_path else "" end),
      (if (.source | type) == "string" then .source else "" end),
      (if (.model | type) == "string" then .model
       elif (.model | type) == "object" then (.model.id // "")
       else "" end),
      (if (.agent_type | type) == "string" then .agent_type else "" end)
    ] | .[] | tostring, ([0] | implode)
  ' 2>/dev/null)
fi
SESSION_ID="${HOOK_FIELDS[0]:-}"
TRANSCRIPT_PATH="${HOOK_FIELDS[1]:-}"
SOURCE="${HOOK_FIELDS[2]:-}"
OBSERVED_MODEL="${HOOK_FIELDS[3]:-}"
AGENT_TYPE="${HOOK_FIELDS[4]:-}"
unset HOOK_FIELDS _hook_field

if [ -z "$SESSION_ID" ]; then
  SESSION_ID="${CODEX_THREAD_ID:-${CODEX_SESSION_ID:-}}"
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
ISSUES=()
INFO=()

if [ -n "${CODEX_CANONICAL_REPO_ROOT:-}" ]; then
  CANONICAL_ROOT="$CODEX_CANONICAL_REPO_ROOT"
else
  GIT_COMMON_DIR=$(git -C "$PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
  if [ -n "$GIT_COMMON_DIR" ] && [ "$(basename "$GIT_COMMON_DIR")" = ".git" ]; then
    CANONICAL_ROOT=$(dirname "$GIT_COMMON_DIR")
  else
    CANONICAL_ROOT="$PROJECT_DIR"
  fi
fi

# Interpreter for bounded session-record calls: the CANONICAL checkout owns the
# shared venv — linked worktrees have none (formal CF r4 F001 on #5896: the
# PROJECT_DIR default 127s every worktree session). Hermetic tests inject
# CLAUDE_SESSION_RECORD_PYTHON explicitly instead.
BOUNDED_PYTHON="${CLAUDE_SESSION_RECORD_PYTHON:-$CANONICAL_ROOT/.venv/bin/python}"
BOUNDED_RUNNER="${SESSION_BOUNDED_RUNNER:-$PROJECT_DIR/scripts/agent_runtime/bounded_command.py}"
SESSION_START_BUDGET_SECONDS="${SESSION_START_BUDGET_SECONDS:-12}"
if ! [[ "$SESSION_START_BUDGET_SECONDS" =~ ^[1-9][0-9]*$ ]]; then
  SESSION_START_BUDGET_SECONDS=12
fi
clamp_bounded_timeout() {
  local requested_timeout="$1"
  local elapsed_seconds=$((SECONDS - SESSION_START_STARTED_SECONDS))
  local remaining_seconds=$((SESSION_START_BUDGET_SECONDS - elapsed_seconds))
  if [ "$remaining_seconds" -le 0 ]; then
    echo "SessionStart aggregate ${SESSION_START_BUDGET_SECONDS}s command budget exhausted." >&2
    return 124
  fi
  CLAMPED_BOUNDED_TIMEOUT_SECONDS="$requested_timeout"
  if [ "$CLAMPED_BOUNDED_TIMEOUT_SECONDS" -gt "$remaining_seconds" ]; then
    CLAMPED_BOUNDED_TIMEOUT_SECONDS="$remaining_seconds"
  fi
}
run_bounded() {
  local requested_timeout="$1"
  shift
  if [ ! -x "$BOUNDED_PYTHON" ] || [ ! -f "$BOUNDED_RUNNER" ]; then
    return 127
  fi
  clamp_bounded_timeout "$requested_timeout" || return $?
  "$BOUNDED_PYTHON" "$BOUNDED_RUNNER" \
    --timeout "$CLAMPED_BOUNDED_TIMEOUT_SECONDS" -- "$@"
}

# Hook-owned state uses the same bounded local-lock contract. fcntl releases
# locks when an owner dies; this deadline handles a live but wedged owner.
export LEARN_UKRAINIAN_LOCK_TIMEOUT_SECONDS=1
export THREAD_ROLLOVER_COMMAND_RUNNER="$BOUNDED_RUNNER"
export THREAD_ROLLOVER_COMMAND_TIMEOUT_SECONDS=3

if [ -n "${SESSION_HANDOFF_AGENT:-}" ]; then
  HANDOFF_AGENT="$SESSION_HANDOFF_AGENT"
elif [[ "${0:-}" == *"/.codex/"* ]]; then
  HANDOFF_AGENT="codex"
elif [[ "${0:-}" == *"/.gemini/"* ]]; then
  HANDOFF_AGENT="gemini"
elif [ -n "${CODEX_THREAD_ID:-}${CODEX_SESSION_ID:-}" ]; then
  HANDOFF_AGENT="codex"
else
  HANDOFF_AGENT="claude"
fi

IS_CODEX_SESSION=0
case "$HANDOFF_AGENT" in
  codex|codex-*) IS_CODEX_SESSION=1 ;;
esac

# An ordinary Codex App/CLI task is not a fleet driver. Native Codex owns its
# compaction lifecycle, so do not search every Codex rollover namespace or ask
# the operator to assign an epic. Exact launcher rollovers and explicit epic
# drivers retain the durable handoff path below.
CODEX_NORMAL_TASK=0
if [ "$IS_CODEX_SESSION" = "1" ] \
  && [ -z "${SESSION_HANDOFF_AGENT:-}" ] \
  && [ -z "${SESSION_EPIC:-}" ] \
  && [ -z "${CODEX_LAUNCHER_ROLLOVER_AGENT:-}${CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID:-}${CODEX_LAUNCHER_ROLLOVER_ID:-}" ]; then
  CODEX_NORMAL_TASK=1
fi

# Resolve the main-session route. Model mismatches are recorded as an untrusted
# compact fallback; they must not abort SessionStart or fabricate a 1M window.
REQUESTED_PROFILE_ID="${LEARN_UKRAINIAN_REQUESTED_PROFILE_ID:-}"
if [ "$IS_CODEX_SESSION" = "1" ] && [ -z "$REQUESTED_PROFILE_ID" ]; then
  REQUESTED_PROFILE_ID="native_codex"
fi
PROFILE_RESOLVER_SH="${CLAUDE_PROFILE_RESOLVER_SH:-$PROJECT_DIR/scripts/lib/profile_resolver.sh}"
if [ ! -f "$PROFILE_RESOLVER_SH" ]; then
  echo "Error: context-profile resolver not found." >&2
  exit 1
fi
# The resolver's own interpreter default is $PROJECT_DIR/.venv — absent in
# linked worktrees (F001 r5 class). Point it at the canonical venv here; an
# explicit CLAUDE_PROFILE_RESOLVER_PYTHON still wins.
export CLAUDE_PROFILE_RESOLVER_PYTHON="${CLAUDE_PROFILE_RESOLVER_PYTHON:-$CANONICAL_ROOT/.venv/bin/python}"
# shellcheck disable=SC1090
source "$PROFILE_RESOLVER_SH"
if ! resolve_context_profile "$REQUESTED_PROFILE_ID" "$OBSERVED_MODEL"; then
  echo "Error: main-session context-profile resolution failed." >&2
  exit 1
fi
if [ "$LEARN_UKRAINIAN_TRUSTED" != "1" ]; then
  ISSUES+=("CONTEXT PROFILE UNTRUSTED: $LEARN_UKRAINIAN_RESOLUTION_REASON. Compact startup is active without a trusted context denominator or forced auto-compaction.")
fi

# Session-record persistence, venv version check, primary-on-main assert,
# thread-lease claim, and rollover detect are consolidated into ONE python
# process (scripts/hooks/session_start_gate.py) further below — the serial
# per-check interpreter spawns dominated the measured ~950 ms cold-start
# (PR #6413). Only shell-cheap checks stay inline here.

# A supervised Claudex child inherits a random run id and generation. Bind those
# to Claude Code's official SessionStart id before any rollover can be requested.
if [ -n "${LEARN_UKRAINIAN_CLAUDEX_RUN_ID:-}" ]; then
  CLAUDEX_SUPERVISOR_SCRIPT="${CLAUDEX_SUPERVISOR_SCRIPT:-$PROJECT_DIR/scripts/orchestration/claudex_supervisor.py}"
  CLAUDEX_SUPERVISOR_PYTHON="${CLAUDEX_SUPERVISOR_PYTHON:-$PROJECT_DIR/.venv/bin/python}"
  if [ -z "$SESSION_ID" ] || [ ! -f "$CLAUDEX_SUPERVISOR_SCRIPT" ] || [ ! -x "$CLAUDEX_SUPERVISOR_PYTHON" ]; then
    ISSUES+=("CLAUDEX SUPERVISOR BIND FAILED: official session identity or runtime helper is unavailable.")
  else
    SUPERVISOR_BIND_CMD=(
      "$CLAUDEX_SUPERVISOR_PYTHON" "$CLAUDEX_SUPERVISOR_SCRIPT" bind-session
      --run-id "$LEARN_UKRAINIAN_CLAUDEX_RUN_ID"
      --launch-generation "${LEARN_UKRAINIAN_CLAUDEX_LAUNCH_GENERATION:-}"
      --session-id "$SESSION_ID"
      --handoff-agent "$HANDOFF_AGENT"
    )
    [ -n "$SOURCE" ] && SUPERVISOR_BIND_CMD+=(--source "$SOURCE")
    [ -n "$OBSERVED_MODEL" ] && SUPERVISOR_BIND_CMD+=(--model "$OBSERVED_MODEL")
    if ! run_bounded 3 "${SUPERVISOR_BIND_CMD[@]}" >/dev/null 2>&1; then
      ISSUES+=("CLAUDEX SUPERVISOR BIND FAILED: SessionStart did not match the owned child generation.")
    fi
    unset SUPERVISOR_BIND_CMD
  fi
fi

# 1. Venv-missing is checked in shell (the gate itself needs the venv python);
# the exact version pin comparison happens inside the gate, in-process.
if [ ! -x "$CANONICAL_ROOT/.venv/bin/python" ]; then
  ISSUES+=("VENV MISSING: canonical .venv/bin/python not found. Recreate it with the version in .python-version.")
fi

# 2. Claude-only environment diagnostics do not belong in Codex context.
if [ "$IS_CODEX_SESSION" = "0" ] && [ -z "$CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS" ]; then
  ISSUES+=("ENV MISSING: CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS not set. Add to .bashrc: export CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS=32000")
fi

# Broad curriculum scans, service probes, GitHub issue listings, and governance
# audits are deliberately absent here. They are optional orientation data and
# belong behind /api/orient, not on the synchronous session-availability path.

# Dispatch-lane self-test (#4879). Build the active lane's normal adapter
# invocation, then run only its resolved CLI's --version command. This catches
# a broken local binary or package shim without sending a model request. Keep
# it bounded and advisory: a failed probe must surface the unavailable lane,
# never prevent a SessionStart response from reaching the operator.
LANE_PROBE_SCRIPT="$PROJECT_DIR/scripts/agent_runtime/lane_probe.py"
if [ -f "$LANE_PROBE_SCRIPT" ]; then
  LANE_PROBE_RC=0
  LANE_PROBE_JSON=$(run_bounded 3 env "PYTHONPATH=$PROJECT_DIR" "$BOUNDED_PYTHON" \
    -m scripts.agent_runtime.lane_probe --agent "$HANDOFF_AGENT" --cwd "$PROJECT_DIR" --timeout 2 2>/dev/null) || LANE_PROBE_RC=$?
  if [ "$LANE_PROBE_RC" -ne 0 ]; then
    LANE_PROBE_REASON=$(printf '%s' "$LANE_PROBE_JSON" | jq -r '.probes[0].reason // "probe did not return a result"' 2>/dev/null || true)
    ISSUES+=("DISPATCH LANE SELF-TEST FAILED for $HANDOFF_AGENT: $LANE_PROBE_REASON")
  fi
  unset LANE_PROBE_RC LANE_PROBE_JSON LANE_PROBE_REASON
fi
unset LANE_PROBE_SCRIPT

# 6. Check MEMORY.md line count (truncated at 200 lines by system)
MEMORY_DIR="$HOME/.claude/projects/-Users-krisztiankoos-projects-learn-ukrainian/memory"
MEMORY_FILE="$MEMORY_DIR/MEMORY.md"
if [ "$IS_CODEX_SESSION" = "0" ] && [ -f "$MEMORY_FILE" ]; then
  MEMORY_LINES=$(wc -l < "$MEMORY_FILE" | tr -d ' ')
  if [ "$MEMORY_LINES" -gt 150 ]; then
    ISSUES+=("MEMORY.md is $MEMORY_LINES lines (limit: 200, budget: 150). Lines after 200 are INVISIBLE. Trim NOW before doing anything else. Move reference data to topic files in memory/.")
  elif [ "$MEMORY_LINES" -gt 120 ]; then
    INFO+=("MEMORY.md is $MEMORY_LINES/150 lines — approaching budget. Be selective about new entries.")
  fi
fi

# 7a. Report the LAUNCH-TIME predeploy verdict. The launcher prints a failure
# banner, but the agent CLI clears the terminal on start, so that banner never
# reaches the operator or the session. scripts/lib/deploy_extensions.sh leaves
# a durable breadcrumb; surface it here or the session boots against a stale
# .claude/ believing it is current (incident 2026-07-26).
PREDEPLOY_STATUS="$PROJECT_DIR/.agent/last-deploy-status"
if [ -f "$PREDEPLOY_STATUS" ] && head -1 "$PREDEPLOY_STATUS" 2>/dev/null | grep -q '^FAILED'; then
  PD_EXIT=$(grep '^exit_code=' "$PREDEPLOY_STATUS" 2>/dev/null | cut -d= -f2)
  PD_SCRIPT=$(grep '^script=' "$PREDEPLOY_STATUS" 2>/dev/null | cut -d= -f2)
  PD_REASON=$(grep -m1 -E '^(❌|  ⚠️)' "$PROJECT_DIR/.agent/last-deploy-failure.log" 2>/dev/null | sed 's/^[[:space:]]*//')
  [ -z "$PD_REASON" ] && PD_REASON="see .agent/last-deploy-failure.log"
  ISSUES+=("PREDEPLOY FAILED at launch (npm run ${PD_SCRIPT:-agents:deploy}, exit ${PD_EXIT:-?}) — deploy targets are STALE, this session may be running outdated hooks/skills/settings. Reason: $PD_REASON")
fi

# 7. Check agents_extensions/shared/ → .claude/ sync drift
if [ "$IS_CODEX_SESSION" = "0" ] \
  && [ -d "$PROJECT_DIR/agents_extensions/shared" ] \
  && [ -d "$PROJECT_DIR/.claude" ]; then
  DIFF_EXCLUDES=(".DS_Store")
  ORPHAN_PATHS_SH="$PROJECT_DIR/scripts/deploy_orphan_paths.sh"
  if [ -f "$ORPHAN_PATHS_SH" ]; then
    # shellcheck disable=SC1090
    source "$ORPHAN_PATHS_SH"
    set -f
    # shellcheck disable=SC2086
    for item in $ORPHAN_PATHS_CLAUDE; do
      DIFF_EXCLUDES+=("$item")
    done
    set +f
    for path in "${CLAUDE_RULE_AUTOLOAD_EXCLUDES[@]}"; do
      DIFF_EXCLUDES+=("$(basename "$path")")
    done
  else
    for item in settings.local.json scheduled_tasks.lock worktrees folk-epic bio-epic critical-rules.md non-negotiable-rules.md workflow.md delegate-must-use-worktree.md cli-help-standard.md model-assignment.md; do
      DIFF_EXCLUDES+=("$item")
    done
  fi

  diff_args=(-rq)
  for ex in "${DIFF_EXCLUDES[@]}"; do
    diff_args+=("--exclude=$ex")
  done

  DRIFT=$(run_bounded 2 diff "${diff_args[@]}" \
    "$PROJECT_DIR/agents_extensions/shared/" "$PROJECT_DIR/.claude/" 2>/dev/null | head -5)
  if [ -n "$DRIFT" ]; then
    DRIFT_COUNT=$(echo "$DRIFT" | wc -l | tr -d ' ')
    ISSUES+=("DEPLOY DRIFT: $DRIFT_COUNT file(s) differ between agents_extensions/shared/ and .claude/. Run: npm run agents:deploy")
  fi
fi

if [ "$CODEX_NORMAL_TASK" = "0" ]; then
  if [ "${LEARN_UKRAINIAN_COLD_START_PROFILE:-}" = "compact" ]; then
    INFO+=("Orientation diagnostics: http://localhost:8765/api/orient?lean=true&session=${SESSION_ID:-}")
  else
    INFO+=("Orientation diagnostics: http://localhost:8765/api/orient?session=${SESSION_ID:-}")
  fi
fi

# The local protected-branch diagnostic runs inside the consolidated gate below.

# 13. Session handoff. Claude uses the official SessionStart session id; Codex
# retains its documented environment fallback for non-Claude fixtures.
CURRENT_THREAD_ID="${SESSION_ID:-${CODEX_THREAD_ID:-${CODEX_SESSION_ID:-}}}"
ROLLOVER_PYTHON="${THREAD_ROLLOVER_PYTHON:-$CANONICAL_ROOT/.venv/bin/python}"  # canonical: worktrees carry no venv (F001 r5)
ROLLOVER_SCRIPT="${THREAD_ROLLOVER_SCRIPT:-$PROJECT_DIR/scripts/orchestration/thread_handoff.py}"
HANDOFF_CONTEXT=""
HANDOFF_WARNINGS=""

# A Codex driver launcher may select exactly one fresh, unbound CLI rollover
# before starting the TUI. SessionStart is the first boundary with the new
# task UUID, so bind and resume only that exported identity here. Re-run the
# lane-scoped preflight immediately before mutation to catch ambiguity or
# replacement drift that appeared while Codex was starting.
if [ "${CODEX_SESSION:-0}" = "1" ] \
  && [ -n "${CODEX_LAUNCHER_ROLLOVER_AGENT:-}${CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID:-}${CODEX_LAUNCHER_ROLLOVER_ID:-}" ]; then
  ROLLOVER_LINK_HELPER="$PROJECT_DIR/scripts/lib/thread_rollover_link.sh"
  if [ -z "${CODEX_LAUNCHER_ROLLOVER_AGENT:-}" ] \
    || [ -z "${CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID:-}" ] \
    || [ -z "${CODEX_LAUNCHER_ROLLOVER_ID:-}" ]; then
    HANDOFF_CONTEXT="ERROR: INCOMPLETE CODEX LAUNCHER ROLLOVER IDENTITY — stop; no rollover was mutated."
  elif [ -z "$CURRENT_THREAD_ID" ]; then
    HANDOFF_CONTEXT="ERROR: CODEX LAUNCHER ROLLOVER HAS NO SESSION ID — stop; no rollover was mutated."
  elif [ ! -f "$ROLLOVER_LINK_HELPER" ]; then
    HANDOFF_CONTEXT="ERROR: CODEX LAUNCHER ROLLOVER HELPER MISSING — stop; no rollover was mutated."
  else
    # shellcheck disable=SC1090
    source "$ROLLOVER_LINK_HELPER"
    VERIFY_OUTPUT=""
    if ! clamp_bounded_timeout 3; then
      HANDOFF_CONTEXT="ERROR: CODEX LAUNCHER ROLLOVER PREFLIGHT SKIPPED — SessionStart command budget exhausted; no rollover was mutated."
    elif ! VERIFY_OUTPUT=$(
      THREAD_ROLLOVER_COMMAND_TIMEOUT_SECONDS="$CLAMPED_BOUNDED_TIMEOUT_SECONDS" \
        verify_codex_pending_rollover \
          "$CANONICAL_ROOT" \
          "$HANDOFF_AGENT" \
          "$CODEX_LAUNCHER_ROLLOVER_AGENT" \
          "$CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID" \
          "$CODEX_LAUNCHER_ROLLOVER_ID" 2>&1
    ); then
      HANDOFF_CONTEXT="ERROR: CODEX LAUNCHER ROLLOVER PREFLIGHT CHANGED — stop; no rollover was mutated.
Output:
$VERIFY_OUTPUT"
    else
      EXACT_ROLLOVER_COMMON=(
        --agent "$CODEX_LAUNCHER_ROLLOVER_AGENT"
        --lineage-id "$CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID"
        --rollover-id "$CODEX_LAUNCHER_ROLLOVER_ID"
      )
      BIND_OUTPUT=""
      if ! BIND_OUTPUT=$(run_bounded 3 "$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" --repo-root "$CANONICAL_ROOT" \
        bind-replacement "${EXACT_ROLLOVER_COMMON[@]}" \
        --replacement-task-id "$CURRENT_THREAD_ID" \
        --evidence "Codex launcher SessionStart bound the exact fresh CLI task ID" 2>&1); then
        HANDOFF_CONTEXT="ERROR: CODEX LAUNCHER EXACT ROLLOVER BIND FAILED — stop.
Output:
$BIND_OUTPUT"
      else
        RESUME_OUTPUT=""
        if ! RESUME_OUTPUT=$(run_bounded 3 "$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" --repo-root "$CANONICAL_ROOT" \
          resume "${EXACT_ROLLOVER_COMMON[@]}" \
          --replacement-thread-id "$CURRENT_THREAD_ID" 2>&1); then
          HANDOFF_CONTEXT="ERROR: CODEX LAUNCHER EXACT ROLLOVER RESUME FAILED — stop.
Output:
$RESUME_OUTPUT"
        elif ! HANDOFF_CONTEXT=$(run_bounded 3 "$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" --repo-root "$CANONICAL_ROOT" \
          detect --agent "$CODEX_LAUNCHER_ROLLOVER_AGENT" \
          --current-thread-id "$CURRENT_THREAD_ID" --format session-start 2>&1); then
          HANDOFF_CONTEXT="ERROR: CODEX LAUNCHER EXACT ROLLOVER READBACK FAILED — stop.
Output:
$HANDOFF_CONTEXT"
        fi
        unset RESUME_OUTPUT
      fi
      unset BIND_OUTPUT EXACT_ROLLOVER_COMMON
    fi
    unset VERIFY_OUTPUT
  fi
  unset ROLLOVER_LINK_HELPER
fi

# Rollover packets are lineage-scoped and may legitimately coexist. A driver
# cold-start is different: only one live Claude session may own a handoff slot
# at a time. The lease claim (plus session-record, venv-pin, primary-on-main,
# and rollover detect) runs inside the consolidated one-process gate below —
# see GATE INVOCATION. Generation-sidecar rationale (formal CF F001 round 3 on
# #5896) and takeover-banner duty (#5759) are unchanged and live in the gate's
# result mapping.

build_handoff_pointer() {
  local brief_path="$1"
  cat <<EOF
PREVIOUS-SESSION HANDOFF — read this brief first, then orient via Monitor API.

Brief: $brief_path
Read with: Read tool. The target is the current agent handoff or a compact brief.
Cold-start protocol: agents_extensions/shared/rules/workflow.md § "Two-tier handoffs"

---
EOF
}

build_local_handoff_pointer() {
  local handoff_path="$1"
  cat <<EOF
PREVIOUS-SESSION HANDOFF — read the local thread rollover packet first.

Agent: $HANDOFF_AGENT
Thread handoff: $handoff_path
Bootstrap prompt: .agent/${HANDOFF_AGENT}-thread-bootstrap.md
Read with: Read tool. These files are gitignored local state and must not be committed.
Cold-start protocol: docs/best-practices/codex-thread-handoff.md

---
EOF
}

build_handoff_fallback() {
  local warning_text="$1"
  local prefix=""

  if [ -n "$warning_text" ]; then
    prefix="$warning_text

"
  fi

  cat <<EOF
${prefix}PREVIOUS-SESSION HANDOFF — legacy git router opt-in could not locate a compact handoff.

Do not dump or rewrite docs/session-state/current.md. For thread rollover, run:
.venv/bin/python scripts/orchestration/thread_handoff.py prepare --agent $HANDOFF_AGENT

---
EOF
}

# Validate SESSION_EPIC if set against fleet taxonomy selectors.
HANDOFF_IDENTITY_SH="${CLAUDE_HANDOFF_IDENTITY_SH:-$PROJECT_DIR/scripts/lib/handoff_identity.sh}"
if [ -f "$HANDOFF_IDENTITY_SH" ]; then
  # shellcheck disable=SC1090
  source "$HANDOFF_IDENTITY_SH"
fi

SESSION_EPIC_VALID=1
if [ -n "${SESSION_EPIC:-}" ]; then
  if declare -f launcher_selector_resolve >/dev/null 2>&1 \
     && ! launcher_selector_resolve "$SESSION_EPIC" >/dev/null 2>&1; then
    SESSION_EPIC_VALID=0
  fi
fi

# Optional task-family filter from launcher epic (#5398). SESSION_EPIC is the
# epic name (hramatka, atlas, harness); task_family on packets usually matches.
TASK_FAMILY_ARGS=()
if [ -n "${SESSION_EPIC:-}" ] && [ "$SESSION_EPIC_VALID" = "1" ]; then
  case "${SESSION_EPIC}" in
    harness|infra) : ;; # do not over-filter infra packets
    *) TASK_FAMILY_ARGS=(--task-family "$SESSION_EPIC") ;;
  esac
fi

# --- GATE INVOCATION: one python process for record/venv/primary/lease/detect.
# Crash honesty (issue #6411): a crashed helper maps to "could not determine",
# never to a business verdict such as a lease conflict.
# --session-id is the durable thread-lease/rollover identity (CURRENT_THREAD_ID,
# with the Codex env fallback); --record-session-id is the official hook
# session id that context-monitor.sh reads the session record back by. Keep
# these two args separate even though they usually coincide for Claude
# sessions (CF review on #6414 finding 1).
GATE_ARGS=(
  --repo-root "$CANONICAL_ROOT" --project-dir "$PROJECT_DIR"
  --agent "$HANDOFF_AGENT" --session-id "$CURRENT_THREAD_ID"
  --record-session-id "$SESSION_ID"
)
[ -n "$TRANSCRIPT_PATH" ] && GATE_ARGS+=(--transcript-path "$TRANSCRIPT_PATH")
[ -n "$SOURCE" ] && GATE_ARGS+=(--source "$SOURCE")
[ -n "$OBSERVED_MODEL" ] && GATE_ARGS+=(--observed-model "$OBSERVED_MODEL")
[ -n "$AGENT_TYPE" ] && GATE_ARGS+=(--agent-type "$AGENT_TYPE")
[ -n "$REQUESTED_PROFILE_ID" ] && GATE_ARGS+=(--profile-id "$REQUESTED_PROFILE_ID")
case "$HANDOFF_AGENT" in
  claude|claude-*) GATE_ARGS+=(--claim-lease) ;;
esac
if [ "$CODEX_NORMAL_TASK" = "0" ] && [ -z "$HANDOFF_CONTEXT" ]; then
  GATE_ARGS+=(--detect)
fi
if [ ${#TASK_FAMILY_ARGS[@]} -gt 0 ]; then
  GATE_ARGS+=(--task-family "$SESSION_EPIC")
fi

GATE_RC=0
GATE_JSON=$(run_bounded 9 env "PYTHONPATH=$PROJECT_DIR" "$BOUNDED_PYTHON" \
  -m scripts.hooks.session_start_gate "${GATE_ARGS[@]}" 2>/dev/null) || GATE_RC=$?
unset GATE_ARGS

GATE_FIELDS=()
if [ "$GATE_RC" -eq 0 ] && [ -n "$GATE_JSON" ]; then
  while IFS= read -r -d '' _gate_field; do
    GATE_FIELDS+=("$_gate_field")
  done < <(printf '%s' "$GATE_JSON" | jq -j '
    [ (.session_record.status // ""), (.session_record.verdict // .session_record.error // ""),
      (.python_version.status // ""), (.python_version.verdict // .python_version.error // ""),
      (.primary_main.status // ""), (.primary_main.verdict // .primary_main.error // ""),
      (.thread_lease.status // ""), (.thread_lease.context // ""),
      (.thread_lease.generation // ""), (.thread_lease.takeover_banner // ""),
      (.rollover_detect.status // ""), (.rollover_detect.context // ""),
      (.rollover_detect.detect_status // "")
    ] | .[] | tostring, ([0] | implode)' 2>/dev/null)
  unset _gate_field
fi

GATE_DETECT_STATUS=""
if [ "$GATE_RC" -ne 0 ] || [ ${#GATE_FIELDS[@]} -lt 13 ]; then
  ISSUES+=("SESSION GATE COULD NOT RUN (rc=$GATE_RC): session-record, venv-pin, and primary-on-main checks did not run.")
  case "$HANDOFF_AGENT" in
    claude|claude-*)
      if [ -z "$HANDOFF_CONTEXT" ]; then
        HANDOFF_CONTEXT="ERROR: SESSION GATE COULD NOT RUN (timeout/budget/runner missing) — stop; lease state UNKNOWN; do NOT force-release.
Output:
${GATE_JSON:-no output}"
      fi
      ;;
  esac
else
  case "${GATE_FIELDS[0]}" in
    ok|skipped) ;;
    issue) ISSUES+=("${GATE_FIELDS[1]}") ;;
    *) ISSUES+=("SESSION RECORD CHECK CRASHED (state unknown): ${GATE_FIELDS[1]:-unknown error}") ;;
  esac
  case "${GATE_FIELDS[2]}" in
    ok|skipped) ;;
    issue) ISSUES+=("${GATE_FIELDS[3]}") ;;
    *) ISSUES+=("VENV PIN CHECK CRASHED (state unknown): ${GATE_FIELDS[3]:-unknown error}") ;;
  esac
  case "${GATE_FIELDS[4]}" in
    ok|skipped) ;;
    issue) ISSUES+=("${GATE_FIELDS[5]}") ;;
    *) ISSUES+=("PRIMARY-ON-MAIN CHECK CRASHED (branch state unknown): ${GATE_FIELDS[5]:-unknown error}") ;;
  esac
  case "${GATE_FIELDS[6]}" in
    ok)
      # Generation reaches only the process-scoped env file (no session-keyed
      # sidecar — formal CF F001 round 3 on #5896). Takeover/heal is never
      # silent (#5759).
      if [ -n "${GATE_FIELDS[8]}" ] && [ -n "${CLAUDE_ENV_FILE:-}" ]; then
        printf 'export LEARN_UKRAINIAN_THREAD_LEASE_GENERATION=%s\n' "${GATE_FIELDS[8]}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
      fi
      [ -n "${GATE_FIELDS[9]}" ] && INFO+=("${GATE_FIELDS[9]}")
      ;;
    skipped) ;;
    *)
      if [ -z "$HANDOFF_CONTEXT" ]; then
        HANDOFF_CONTEXT="${GATE_FIELDS[7]:-ERROR: LEASE CLAIM HELPER CRASHED — stop; lease state UNKNOWN; do NOT force-release.}"
      fi
      ;;
  esac
  case "${GATE_FIELDS[10]}" in
    ok|skipped) GATE_DETECT_STATUS="${GATE_FIELDS[12]}" ;;
    *)
      if [ -z "$HANDOFF_CONTEXT" ]; then
        HANDOFF_CONTEXT="${GATE_FIELDS[11]:-ERROR: thread_handoff.py detect crashed. Stop.}"
      fi
      ;;
  esac
fi
unset GATE_JSON GATE_FIELDS GATE_RC

if [ -z "$HANDOFF_CONTEXT" ] && [ "$GATE_DETECT_STATUS" = "none" ]; then
  HANDOFF_FILE="$PROJECT_DIR/docs/session-state/current.md"

  if [ -f "$PROJECT_DIR/.agent/${HANDOFF_AGENT}-thread-handoff.md" ]; then
    HANDOFF_CONTEXT=$(build_local_handoff_pointer ".agent/${HANDOFF_AGENT}-thread-handoff.md")
  elif [ "${SESSION_HANDOFF_ALLOW_GIT_ROUTER:-0}" = "1" ] && [ -f "$HANDOFF_FILE" ]; then
    AGENT_HANDOFF=$(sed -n "s/^[[:space:]]*-[[:space:]]*${HANDOFF_AGENT}:[[:space:]]*//p" "$HANDOFF_FILE" 2>/dev/null | head -1 | sed 's/[[:space:]]*$//')

    if [ -n "$AGENT_HANDOFF" ]; then
      if [ -f "$PROJECT_DIR/$AGENT_HANDOFF" ]; then
        HANDOFF_CONTEXT=$(build_handoff_pointer "$AGENT_HANDOFF")
      else
        HANDOFF_WARNINGS="WARN: Agent-Handoff for $HANDOFF_AGENT pointed to $AGENT_HANDOFF but file missing on disk."
      fi
    fi

    MARKER_BRIEF=$(grep -m1 '^Latest-Brief:' "$HANDOFF_FILE" 2>/dev/null | sed 's/^Latest-Brief:[[:space:]]*//; s/[[:space:]]*$//')

    if [ -z "$HANDOFF_CONTEXT" ] && [ -n "$MARKER_BRIEF" ]; then
      if [ -f "$PROJECT_DIR/$MARKER_BRIEF" ]; then
        HANDOFF_CONTEXT=$(build_handoff_pointer "$MARKER_BRIEF")
      else
        HANDOFF_WARNINGS="WARN: Latest-Brief pointed to $MARKER_BRIEF but file missing on disk."
      fi
    fi

    if [ -z "$HANDOFF_CONTEXT" ]; then
      # shellcheck disable=SC2016
      TABLE_BRIEF=$(sed -n 's/.*\*\*Brief (read first):\*\* `\([^`]*\)`.*/\1/p' "$HANDOFF_FILE" 2>/dev/null | head -1)

      if [ -n "$TABLE_BRIEF" ]; then
        if [ -f "$PROJECT_DIR/$TABLE_BRIEF" ]; then
          if [ -z "$MARKER_BRIEF" ]; then
            HANDOFF_WARNINGS="${HANDOFF_WARNINGS:+$HANDOFF_WARNINGS
}WARN: Latest-Brief marker missing in current.md — fell back to table regex. Add the marker to fix."
          fi
          HANDOFF_CONTEXT="${HANDOFF_WARNINGS:+$HANDOFF_WARNINGS

}$(build_handoff_pointer "$TABLE_BRIEF")"
        else
          HANDOFF_WARNINGS="${HANDOFF_WARNINGS:+$HANDOFF_WARNINGS
}WARN: Latest-Brief pointed to $TABLE_BRIEF but file missing on disk."
        fi
      fi
    fi

    if [ -z "$HANDOFF_CONTEXT" ]; then
      HANDOFF_WARNINGS="${HANDOFF_WARNINGS:+$HANDOFF_WARNINGS
}WARN: Could not locate latest brief in current.md under legacy router opt-in. Not dumping git-tracked router contents."
      HANDOFF_CONTEXT=$(build_handoff_fallback "$HANDOFF_WARNINGS")
    fi
  fi

  if [ -z "$HANDOFF_CONTEXT" ]; then
    if ! HANDOFF_CONTEXT=$(run_bounded 3 "$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" \
      --repo-root "$CANONICAL_ROOT" detect --agent "$HANDOFF_AGENT" \
      --current-thread-id "$CURRENT_THREAD_ID" --format session-start 2>&1); then
      HANDOFF_CONTEXT="ERROR: thread_handoff.py detect failed. Stop.
Output:
$HANDOFF_CONTEXT"
    fi
  fi
fi

# Epic assignment banner
EPIC_BANNER=""
if [ -n "${SESSION_EPIC:-}" ] && [ "$SESSION_EPIC_VALID" = "1" ]; then
  EPIC_HANDOFF_PATH=".claude/${SESSION_EPIC}-epic/CLAUDE-DRIVER-HANDOFF.md"
  case "$HANDOFF_AGENT" in
    codex|codex-*)
      CODEX_EPIC_HANDOFF=".claude/${SESSION_EPIC}-epic/CODEX-DRIVER-HANDOFF.md"
      if [ -f "$PROJECT_DIR/$CODEX_EPIC_HANDOFF" ]; then
        EPIC_HANDOFF_PATH="$CODEX_EPIC_HANDOFF"
      fi
      unset CODEX_EPIC_HANDOFF
      ;;
  esac
  EPIC_BANNER="ASSIGNED EPIC: ${SESSION_EPIC}.epic (binding — from the launch command).
You are the ${SESSION_EPIC} lane, NOT the main orchestrator. Do not claim or work
other lanes' queues. Rollover namespace: ${HANDOFF_AGENT}.
Epic driver handoff (load AFTER the thread handoff below, it
is the lane SSOT): $EPIC_HANDOFF_PATH"
  if [ ! -f "$PROJECT_DIR/$EPIC_HANDOFF_PATH" ]; then
    EPIC_BANNER="$EPIC_BANNER
(No driver handoff exists yet for this epic — create it at first rollover.)"
  fi
  unset EPIC_HANDOFF_PATH
elif [ -n "${SESSION_EPIC:-}" ] && [ "$SESSION_EPIC_VALID" = "0" ]; then
  VALID_SELECTORS_HELP=""
  if declare -f launcher_selector_help >/dev/null 2>&1; then
    VALID_SELECTORS_HELP="$(launcher_selector_help)"
  fi
  EPIC_BANNER="ERROR: unknown SESSION_EPIC '${SESSION_EPIC}' — epic binding STOPPED.
${VALID_SELECTORS_HELP:+$VALID_SELECTORS_HELP
}NO EPIC ASSIGNED (unknown SESSION_EPIC fell back to unassigned mode).
Do NOT default to 'main orchestrator'. Resolve your lane in this order:
1. The user's first message names the epic → that binds.
2. .agent/lane-assignments.md maps this agent type to exactly ONE epic → that binds.
3. Otherwise ASK THE USER one question ('which epic is this session?') BEFORE
   claiming any lane, reading any thread handoff as your own, or touching queues."
elif [ "$IS_CODEX_SESSION" = "1" ]; then
  EPIC_BANNER=""
else
  EPIC_BANNER="NO EPIC ASSIGNED (launcher had no --epic flag).
Do NOT default to 'main orchestrator'. Resolve your lane in this order:
1. The user's first message names the epic → that binds.
2. .agent/lane-assignments.md maps this agent type to exactly ONE epic → that binds.
3. Otherwise ASK THE USER one question ('which epic is this session?') BEFORE
   claiming any lane, reading any thread handoff as your own, or touching queues."
fi

# The Codex driver board is generated only after the launcher owns its exact
# stream lease and has completed rollover preflight. Inject it into the actual
# SessionStart context so the operator never has to paste or re-request it.
CODEX_COLD_START_BOARD=""
case "$HANDOFF_AGENT" in
  codex|codex-*)
    if [ -n "${SESSION_EPIC:-}" ] && [ "$SESSION_EPIC_VALID" = "1" ]; then
      CODEX_COLD_START_PATH="$PROJECT_DIR/.claude/${SESSION_EPIC}-epic/CODEX-COLD-START.md"
      if [ -f "$CODEX_COLD_START_PATH" ]; then
        CODEX_COLD_START_BOARD=$(<"$CODEX_COLD_START_PATH")
      else
        ISSUES+=("CODEX COLD-START BOARD MISSING: launcher must bootstrap and inject $CODEX_COLD_START_PATH before driving.")
      fi
      unset CODEX_COLD_START_PATH
    fi
    ;;
esac

# Build Profile Capsule
CAPSULE_ORIENTATION_URL="http://localhost:8765/api/orient?session=${SESSION_ID:-}"
if [ "${LEARN_UKRAINIAN_COLD_START_PROFILE:-}" = "compact" ]; then
  CAPSULE_ORIENTATION_URL="http://localhost:8765/api/orient?lean=true&session=${SESSION_ID:-}"
fi

if [ "$IS_CODEX_SESSION" = "1" ]; then
  CAPSULE="CODEX SESSION: profile=${LEARN_UKRAINIAN_PROFILE_ID:-fallback}; model=${OBSERVED_MODEL:-${LEARN_UKRAINIAN_MAIN_MODEL_ID:-unknown}}; context=${LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS:-0}; trusted=${LEARN_UKRAINIAN_TRUSTED:-0}.
Native compaction is runtime-owned. Fleet hydration is ${SESSION_EPIC:+bound to ${SESSION_EPIC}; }${SESSION_EPIC:-unbound for this ordinary task}.
Orientation (on demand): ${CAPSULE_ORIENTATION_URL#http://localhost:8765}"
else
  CAPSULE="--- SESSION PROFILE CAPSULE ---
Profile: ${LEARN_UKRAINIAN_PROFILE_ID:-fallback}
Requested Profile: ${LEARN_UKRAINIAN_REQUESTED_PROFILE_ID:-None}
Declared Model: ${LEARN_UKRAINIAN_EXPECTED_MAIN_MODEL_ID:-${LEARN_UKRAINIAN_MAIN_MODEL_ID:-unknown}}
Declared Window: ${LEARN_UKRAINIAN_EXPECTED_MAIN_CONTEXT_WINDOW_TOKENS:-0}
Effective Window: ${LEARN_UKRAINIAN_MAIN_CONTEXT_WINDOW_TOKENS:-0}
Observed Model: ${OBSERVED_MODEL:-None}
Cold Start: ${LEARN_UKRAINIAN_COLD_START_PROFILE:-compact}
Budget: ${LEARN_UKRAINIAN_COLD_START_BUDGET_TOKENS:-0}
Auto-Compact Capacity: ${LEARN_UKRAINIAN_AUTO_COMPACT_CAPACITY_TOKENS:-None}
Trusted: ${LEARN_UKRAINIAN_TRUSTED:-0} (${LEARN_UKRAINIAN_RESOLUTION_REASON:-missing-profile})
Session ID: ${SESSION_ID:-None}
Orientation URL: $CAPSULE_ORIENTATION_URL
--------------------------------"
fi

# Build output
CONTEXT="$CAPSULE"
if [ -n "$EPIC_BANNER" ]; then
  CONTEXT="$CONTEXT

$EPIC_BANNER"
fi
if [ -n "$HANDOFF_CONTEXT" ]; then
  CONTEXT="$CONTEXT

$HANDOFF_CONTEXT"
fi
if [ -n "$CODEX_COLD_START_BOARD" ]; then
  CONTEXT="$CONTEXT

CODEX COLD-START BOARD (launcher-injected)
$CODEX_COLD_START_BOARD"
fi

if [ ${#ISSUES[@]} -gt 0 ]; then
  CONTEXT="$CONTEXT

SESSION SETUP CHECK:
ISSUES:"
  for issue in "${ISSUES[@]}"; do
    CONTEXT="$CONTEXT
  - $issue"
  done
fi

if [ ${#INFO[@]} -gt 0 ]; then
  if [ ${#ISSUES[@]} -eq 0 ]; then
    CONTEXT="$CONTEXT

SESSION SETUP CHECK:"
  fi
  CONTEXT="$CONTEXT
INFO:"
  for info in "${INFO[@]}"; do
    CONTEXT="$CONTEXT
  - $info"
  done
fi

jq -n --arg msg "$CONTEXT" \
  '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":$msg}}'
exit 0

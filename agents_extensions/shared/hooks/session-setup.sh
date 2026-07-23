#!/bin/bash
# Hook: SessionStart — runs on new sessions AND resumed sessions
# Validates environment and reports project state.
# Skips in headless/pipeline mode to avoid adding latency.

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
#    Defensive: if the sentinel is older than 1 minute, it is
#    definitely stale (real rehashes complete in <1s) — delete it.
#    The 1-minute threshold avoids racing against an active rehash.
#
#    Using `find -mmin +1` instead of `stat`: portable across BSD
#    (macOS) and GNU (Homebrew coreutils) without flag-flavor
#    detection. `stat -f %m` (BSD) and `stat -c %Y` (GNU) have
#    incompatible meanings — `find -mmin +1` is the same on both.
PYENV_SHIM_LOCK="${PYENV_ROOT:-$HOME/.pyenv}/shims/.pyenv-shim"
if [ -f "$PYENV_SHIM_LOCK" ] && \
   [ -n "$(find "$PYENV_SHIM_LOCK" -mmin +1 -type f 2>/dev/null)" ]; then
  rm -f "$PYENV_SHIM_LOCK"
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
# CI can't catch it; only a local canary can. Auto-heal the exact absolute
# self-link case here (the general loop case is healed by the API-orient Python
# canary in scripts/api/main.py). See docs/bug-autopsies/node-modules-eloop-symlink.md.
for _nm in "$_LU_REPO/node_modules" "$_LU_REPO/site/node_modules"; do
  if [ -L "$_nm" ] && [ "$(readlink "$_nm" 2>/dev/null)" = "$_nm" ]; then
    rm -f "$_nm" \
      && echo "⚠️  repo-health: removed self-referential symlink $_nm (was breaking npm with spawn ELOOP)" >&2
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

# Resolve the main-session route. Model mismatches are recorded as an untrusted
# compact fallback; they must not abort SessionStart or fabricate a 1M window.
REQUESTED_PROFILE_ID="${LEARN_UKRAINIAN_REQUESTED_PROFILE_ID:-}"
PROFILE_RESOLVER_SH="${CLAUDE_PROFILE_RESOLVER_SH:-$PROJECT_DIR/scripts/lib/profile_resolver.sh}"
if [ ! -f "$PROFILE_RESOLVER_SH" ]; then
  echo "Error: context-profile resolver not found." >&2
  exit 1
fi
# shellcheck disable=SC1090
source "$PROFILE_RESOLVER_SH"
if ! resolve_context_profile "$REQUESTED_PROFILE_ID" "$OBSERVED_MODEL"; then
  echo "Error: main-session context-profile resolution failed." >&2
  exit 1
fi
if [ "$LEARN_UKRAINIAN_TRUSTED" != "1" ]; then
  ISSUES+=("CONTEXT PROFILE UNTRUSTED: $LEARN_UKRAINIAN_RESOLUTION_REASON. Compact startup is active without a trusted context denominator or forced auto-compaction.")
fi

# Persist official SessionStart identity and the resolved route in the canonical
# checkout. Build argv as an array so exact transcript paths are never split.
SESSION_RECORD_SCRIPT="${CLAUDE_SESSION_RECORD_SCRIPT:-$PROJECT_DIR/scripts/lib/session_record.py}"
SESSION_RECORD_PYTHON="${CLAUDE_SESSION_RECORD_PYTHON:-$PROJECT_DIR/.venv/bin/python}"
if [ -n "$SESSION_ID" ] && [ -f "$SESSION_RECORD_SCRIPT" ] && [ -x "$SESSION_RECORD_PYTHON" ]; then
  SESSION_RECORD_CMD=(
    "$SESSION_RECORD_PYTHON" "$SESSION_RECORD_SCRIPT" --state-root "$CANONICAL_ROOT"
    update --session-id "$SESSION_ID" --provenance "SessionStart" --append-env
  )
  [ -n "$TRANSCRIPT_PATH" ] && SESSION_RECORD_CMD+=(--transcript-path "$TRANSCRIPT_PATH")
  [ -n "$SOURCE" ] && SESSION_RECORD_CMD+=(--source "$SOURCE")
  [ -n "$OBSERVED_MODEL" ] && SESSION_RECORD_CMD+=(--observed-model "$OBSERVED_MODEL")
  [ -n "$AGENT_TYPE" ] && SESSION_RECORD_CMD+=(--agent-type "$AGENT_TYPE")
  [ -n "$REQUESTED_PROFILE_ID" ] && SESSION_RECORD_CMD+=(--profile-id "$REQUESTED_PROFILE_ID")
  if ! "${SESSION_RECORD_CMD[@]}" >/dev/null; then
    ISSUES+=("SESSION RECORD FAILED: official SessionStart identity could not be persisted.")
  fi
  unset SESSION_RECORD_CMD
elif [ -n "$SESSION_ID" ]; then
  ISSUES+=("SESSION RECORD UNAVAILABLE: canonical runtime record helper is missing.")
fi

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
    if ! "${SUPERVISOR_BIND_CMD[@]}" >/dev/null 2>&1; then
      ISSUES+=("CLAUDEX SUPERVISOR BIND FAILED: SessionStart did not match the owned child generation.")
    fi
    unset SUPERVISOR_BIND_CMD
  fi
fi

# 1. Check .venv exists and has correct Python
if [ ! -f "$PROJECT_DIR/.venv/bin/python" ]; then
  ISSUES+=("VENV MISSING: .venv/bin/python not found. Recreate: rm -rf .venv && ~/.pyenv/versions/3.12.8/bin/python -m venv .venv")
else
  PY_VERSION=$("$PROJECT_DIR/.venv/bin/python" --version 2>/dev/null)
  if [[ "$PY_VERSION" != *"3.12"* ]]; then
    ISSUES+=("VENV WRONG PYTHON: Expected 3.12.x, got $PY_VERSION")
  fi
fi

# 2. Check CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS is set
if [ -z "$CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS" ]; then
  ISSUES+=("ENV MISSING: CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS not set. Add to .bashrc: export CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS=32000")
fi

if [ "${LEARN_UKRAINIAN_COLD_START_PROFILE:-}" != "compact" ]; then
  # 3. Check message broker DB exists
  MCP_DB="$PROJECT_DIR/.mcp/servers/message-broker/messages.db"
  if [ ! -f "$MCP_DB" ]; then
    INFO+=("Message broker DB not found at $MCP_DB — Gemini comms unavailable")
  fi

  # 4. Check for stale orchestration state (in-progress builds older than 24h)
  STALE_COUNT=0
  if [ -d "$PROJECT_DIR/curriculum" ]; then
    while IFS= read -r -d '' state_file; do
      if [ -f "$state_file" ]; then
        if grep -q '"in_progress"' "$state_file" 2>/dev/null; then
          MOD_TIME=$(stat -f %m "$state_file" 2>/dev/null || stat -c %Y "$state_file" 2>/dev/null)
          NOW=$(date +%s)
          AGE=$(( (NOW - MOD_TIME) / 3600 ))
          if [ "$AGE" -gt 24 ]; then
            STALE_COUNT=$((STALE_COUNT + 1))
          fi
        fi
      fi
    done < <(find "$PROJECT_DIR/curriculum" -name "state-v3.json" -print0 2>/dev/null)
  fi

  if [ "$STALE_COUNT" -gt 0 ]; then
    INFO+=("$STALE_COUNT stale orchestration state file(s) found (in_progress > 24h old). Consider cleanup.")
  fi

  # 5. Report in-progress module builds
  IN_PROGRESS_COUNT=0
  if [ -d "$PROJECT_DIR/curriculum" ]; then
    IN_PROGRESS_COUNT=$(find "$PROJECT_DIR/curriculum" -name "state-v3.json" -exec grep -l '"in_progress"' {} \; 2>/dev/null | wc -l | tr -d ' ')
  fi

  if [ "$IN_PROGRESS_COUNT" -gt 0 ]; then
    INFO+=("$IN_PROGRESS_COUNT module build(s) currently in progress")
  fi
fi

# 6. Check MEMORY.md line count (truncated at 200 lines by system)
MEMORY_DIR="$HOME/.claude/projects/-Users-krisztiankoos-projects-learn-ukrainian/memory"
MEMORY_FILE="$MEMORY_DIR/MEMORY.md"
if [ -f "$MEMORY_FILE" ]; then
  MEMORY_LINES=$(wc -l < "$MEMORY_FILE" | tr -d ' ')
  if [ "$MEMORY_LINES" -gt 150 ]; then
    ISSUES+=("MEMORY.md is $MEMORY_LINES lines (limit: 200, budget: 150). Lines after 200 are INVISIBLE. Trim NOW before doing anything else. Move reference data to topic files in memory/.")
  elif [ "$MEMORY_LINES" -gt 120 ]; then
    INFO+=("MEMORY.md is $MEMORY_LINES/150 lines — approaching budget. Be selective about new entries.")
  fi
fi

# 7. Check agents_extensions/shared/ → .claude/ sync drift
if [ -d "$PROJECT_DIR/agents_extensions/shared" ] && [ -d "$PROJECT_DIR/.claude" ]; then
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

  DRIFT=$(diff "${diff_args[@]}" "$PROJECT_DIR/agents_extensions/shared/" "$PROJECT_DIR/.claude/" 2>/dev/null | head -5)
  if [ -n "$DRIFT" ]; then
    DRIFT_COUNT=$(echo "$DRIFT" | wc -l | tr -d ' ')
    ISSUES+=("DEPLOY DRIFT: $DRIFT_COUNT file(s) differ between agents_extensions/shared/ and .claude/. Run: npm run agents:deploy")
  fi
fi

if [ "${LEARN_UKRAINIAN_COLD_START_PROFILE:-}" != "compact" ]; then
  # 8. Check MCP sources server health (historically called the RAG server)
  MCP_STATUS=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:8766/sse" 2>/dev/null)
  if [ "$MCP_STATUS" != "200" ] && [ "$MCP_STATUS" != "000" ]; then
    INFO+=("MCP sources server returned HTTP $MCP_STATUS — some tools may be unavailable")
  elif [ "$MCP_STATUS" = "000" ]; then
    ISSUES+=("MCP sources server unreachable at 127.0.0.1:8766 — VESUM + textbook + dictionary tools unavailable. Start with: ./services.sh start sources")
  fi

  # 10. Check for stale decisions
  if [ -f "$PROJECT_DIR/.venv/bin/python" ] && [ -f "$PROJECT_DIR/scripts/check_decisions.py" ]; then
    STALE_DECISIONS=$("$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/check_decisions.py" --quiet 2>/dev/null)
    if [ -n "$STALE_DECISIONS" ]; then
      INFO+=("$STALE_DECISIONS")
    fi
  fi

  # 10b. Check ADR hygiene
  if [ -f "$PROJECT_DIR/.venv/bin/python" ] && [ -f "$PROJECT_DIR/scripts/audit/check_adrs.py" ]; then
    ADR_REPORT=$("$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/audit/check_adrs.py" --quiet 2>/dev/null)
    ADR_EXIT=$?
    if [ "$ADR_EXIT" -ge 2 ] && [ -n "$ADR_REPORT" ]; then
      ISSUES+=("ADR hygiene: $ADR_REPORT — see docs/best-practices/adr-management.md")
    elif [ -n "$ADR_REPORT" ]; then
      INFO+=("ADR hygiene: $ADR_REPORT")
    fi
  fi

  # 10c. Check postmortem hygiene
  if [ -f "$PROJECT_DIR/.venv/bin/python" ] && [ -f "$PROJECT_DIR/scripts/audit/check_postmortems.py" ]; then
    POSTMORTEM_REPORT=$("$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/audit/check_postmortems.py" --quiet 2>/dev/null)
    if [ -n "$POSTMORTEM_REPORT" ]; then
      ISSUES+=("Postmortem hygiene: $POSTMORTEM_REPORT — see docs/best-practices/postmortem-management.md")
    fi
  fi

  # 11. Open GH issues summary
  if command -v gh >/dev/null 2>&1; then
    OPEN_ISSUES=$(gh issue list --state open --json number,title,labels --limit 10 2>/dev/null)
    if [ $? -eq 0 ] && [ -n "$OPEN_ISSUES" ] && [ "$OPEN_ISSUES" != "[]" ]; then
      ISSUE_COUNT=$(echo "$OPEN_ISSUES" | jq 'length')
      ISSUE_LIST=$(echo "$OPEN_ISSUES" | jq -r '.[] | "  #\(.number): \(.title)"' | head -5)
      INFO+=("$ISSUE_COUNT open issue(s):
  $ISSUE_LIST")
    fi
  fi

  # 11b. Issue-stream hygiene
  STREAM_AUDIT_CACHE="$PROJECT_DIR/batch_state/issue_stream_audit.json"
  if [ -f "$PROJECT_DIR/scripts/orchestration/issue_stream_audit.py" ]; then
    STREAM_FRESH=0
    if [ -f "$STREAM_AUDIT_CACHE" ]; then
      STREAM_AGE=$(( $(date +%s) - $(jq -r '.generated_at // 0' "$STREAM_AUDIT_CACHE" 2>/dev/null || echo 0) ))
      [ "$STREAM_AGE" -lt 3600 ] && STREAM_FRESH=1
    fi
    if [ "$STREAM_FRESH" -eq 1 ]; then
      ORPHAN_COUNT=$(jq -r '.orphans | length' "$STREAM_AUDIT_CACHE" 2>/dev/null || echo 0)
      if [ "$ORPHAN_COUNT" -gt 0 ]; then
        ORPHAN_LIST=$(jq -r '.orphans[:5][] | "  #\(.number): \(.title)"' "$STREAM_AUDIT_CACHE" 2>/dev/null)
        ISSUES+=("$ORPHAN_COUNT issue(s) in NO stream epic (link them — registry: scripts/config/issue_streams.yaml):
  $ORPHAN_LIST")
      fi
      MISSING_EPICS=$(jq -r '.closed_or_missing_epics | join(", ")' "$STREAM_AUDIT_CACHE" 2>/dev/null)
      [ -n "$MISSING_EPICS" ] && ISSUES+=("Stream epic(s) closed/missing: #$MISSING_EPICS — fix scripts/config/issue_streams.yaml or reopen")

      if [ -f "$PROJECT_DIR/scripts/audit/check_research_registry.py" ] && \
         [ -f "$PROJECT_DIR/docs/references/research-registry.yaml" ] && \
         [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
        STRICT_JSON=$(cd "$PROJECT_DIR" && "$PROJECT_DIR/.venv/bin/python" scripts/audit/check_research_registry.py --strict-adoption --json 2>/dev/null)
        STRICT_OK=$(echo "$STRICT_JSON" | jq -r '.ok' 2>/dev/null)
        if [ "$STRICT_OK" = "false" ]; then
          STRICT_ERRORS=$(echo "$STRICT_JSON" | jq -r '.errors[]? | "  - \(.)"' 2>/dev/null)
          ISSUES+=("Research registry strict-adoption gate FAILED (ADR-011 P4 — ownership/consumer drift vs live GitHub, scripts/audit/check_research_registry.py --strict-adoption):
  $STRICT_ERRORS")
        fi
      fi
    elif command -v gh >/dev/null 2>&1; then
      (cd "$PROJECT_DIR" && nohup "$PROJECT_DIR/.venv/bin/python" -m scripts.orchestration.issue_stream_audit --json >/dev/null 2>&1 &)
      INFO+=("issue-stream audit cache stale — background refresh started (#4708)")
    fi
  fi

  # 12. Git hygiene
  if command -v git >/dev/null 2>&1 && [ -d "$PROJECT_DIR/.git" ]; then
    HYGIENE_THRESHOLD_WARN=5
    HYGIENE_THRESHOLD_ISSUE=20

    DIRTY_NONEXEMPT=$(
      git -C "$PROJECT_DIR" status --short 2>/dev/null \
        | grep -vE ' (wiki/|data/corpus_audit/draft_tickets/)' \
        | wc -l | tr -d ' '
    )

    if [ "$DIRTY_NONEXEMPT" -gt "$HYGIENE_THRESHOLD_ISSUE" ]; then
      ISSUES+=("GIT HYGIENE: $DIRTY_NONEXEMPT dirty files outside exempt paths (threshold: $HYGIENE_THRESHOLD_ISSUE). Triage BEFORE starting work — see docs/best-practices/git-hygiene.md. Often these are stale-behind-main drift; \`git checkout HEAD -- <file>\` fixes each one.")
    elif [ "$DIRTY_NONEXEMPT" -gt "$HYGIENE_THRESHOLD_WARN" ]; then
      INFO+=("Git hygiene: $DIRTY_NONEXEMPT dirty files outside exempt paths. Under the issue threshold ($HYGIENE_THRESHOLD_ISSUE) but worth inspecting with \`git status --short | grep -vE ' (wiki/|data/corpus_audit/draft_tickets/)'\`. Policy: docs/best-practices/git-hygiene.md.")
    fi

    # 12b. Primary must stay attached to main (#4857) — auto-heal when possible.
    if [ -x "$PROJECT_DIR/.venv/bin/python" ] \
        && [ -f "$PROJECT_DIR/scripts/guardrails/assert_primary_on_main.py" ]; then
      if ! "$PROJECT_DIR/.venv/bin/python" \
          "$PROJECT_DIR/scripts/guardrails/assert_primary_on_main.py" \
          --cwd "$PROJECT_DIR" --quiet 2>/dev/null; then
        if "$PROJECT_DIR/.venv/bin/python" \
            "$PROJECT_DIR/scripts/guardrails/assert_primary_on_main.py" \
            --cwd "$PROJECT_DIR" --heal 2>/dev/null; then
          INFO+=("PRIMARY HEAD was off main/detached — auto-healed to main (#4857). Prefer worktrees for all branch work.")
        else
          ISSUES+=("PRIMARY HEAD is detached or not on main (#4857). Run: .venv/bin/python scripts/guardrails/assert_primary_on_main.py --heal. Never gh pr checkout / git checkout <sha> on primary.")
        fi
      fi
    fi
  fi
else
  # 9. Compact mode orientation link
  INFO+=("Lean orientation: http://localhost:8765/api/orient?lean=true&session=${SESSION_ID:-}")
fi

# 13. Session handoff. Claude uses the official SessionStart session id; Codex
# retains its documented environment fallback for non-Claude fixtures.
CURRENT_THREAD_ID="${SESSION_ID:-${CODEX_THREAD_ID:-${CODEX_SESSION_ID:-}}}"
ROLLOVER_PYTHON="${THREAD_ROLLOVER_PYTHON:-$PROJECT_DIR/.venv/bin/python}"
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
    if ! VERIFY_OUTPUT=$(verify_codex_pending_rollover \
      "$CANONICAL_ROOT" \
      "$HANDOFF_AGENT" \
      "$CODEX_LAUNCHER_ROLLOVER_AGENT" \
      "$CODEX_LAUNCHER_ROLLOVER_LINEAGE_ID" \
      "$CODEX_LAUNCHER_ROLLOVER_ID" 2>&1); then
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
      if ! BIND_OUTPUT=$("$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" --repo-root "$CANONICAL_ROOT" \
        bind-replacement "${EXACT_ROLLOVER_COMMON[@]}" \
        --replacement-task-id "$CURRENT_THREAD_ID" \
        --evidence "Codex launcher SessionStart bound the exact fresh CLI task ID" 2>&1); then
        HANDOFF_CONTEXT="ERROR: CODEX LAUNCHER EXACT ROLLOVER BIND FAILED — stop.
Output:
$BIND_OUTPUT"
      else
        RESUME_OUTPUT=""
        if ! RESUME_OUTPUT=$("$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" --repo-root "$CANONICAL_ROOT" \
          resume "${EXACT_ROLLOVER_COMMON[@]}" \
          --replacement-thread-id "$CURRENT_THREAD_ID" 2>&1); then
          HANDOFF_CONTEXT="ERROR: CODEX LAUNCHER EXACT ROLLOVER RESUME FAILED — stop.
Output:
$RESUME_OUTPUT"
        elif ! HANDOFF_CONTEXT=$("$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" --repo-root "$CANONICAL_ROOT" \
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
# at a time. Claim the flat durable lease before reading any queue guidance so
# a duplicate SessionStart stops before it can double-drive work.
case "$HANDOFF_AGENT" in
  claude|claude-*)
    if [ -z "$CURRENT_THREAD_ID" ]; then
      HANDOFF_CONTEXT="ERROR: Cannot acquire durable thread lease: SessionStart did not provide a current thread id. Stop; do not drive this queue."
    elif ! THREAD_LEASE_OUTPUT=$("$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" \
      --repo-root "$CANONICAL_ROOT" claim-thread-lease --agent "$HANDOFF_AGENT" \
      --current-thread-id "$CURRENT_THREAD_ID" 2>&1); then
      HANDOFF_CONTEXT="ERROR: DURABLE THREAD LEASE CONFLICT — stop; do not cold-start or drive this queue.
Output:
$THREAD_LEASE_OUTPUT"
    fi
    ;;
esac

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

# Optional task-family filter from launcher epic (#5398). SESSION_EPIC is the
# epic name (hramatka, atlas, harness); task_family on packets usually matches.
TASK_FAMILY_ARGS=()
if [ -n "${SESSION_EPIC:-}" ]; then
  case "${SESSION_EPIC}" in
    harness|infra) : ;; # do not over-filter infra packets
    *) TASK_FAMILY_ARGS=(--task-family "$SESSION_EPIC") ;;
  esac
fi

if [ -z "$HANDOFF_CONTEXT" ] && ! DETECT_OUTPUT=$("$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" \
  --repo-root "$CANONICAL_ROOT" detect --agent "$HANDOFF_AGENT" \
  --current-thread-id "$CURRENT_THREAD_ID" "${TASK_FAMILY_ARGS[@]}" --format json 2>&1); then
  # Exit 2 may be multi-packet ambiguity (#5398) — surface candidates, never cold-start.
  DETECT_ERR_CODE=$(printf '%s' "$DETECT_OUTPUT" | "$ROLLOVER_PYTHON" -c 'import json,sys
try:
  d=json.loads(sys.stdin.read()); print(d.get("error_code") or "")
except Exception:
  print("")' 2>/dev/null || true)
  if [ "$DETECT_ERR_CODE" = "MULTIPLE_LIVE_PENDING_ROLLOVERS" ]; then
    HANDOFF_CONTEXT="ERROR: MULTIPLE live pending rollovers — do not cold-start; bind one exact candidate.
$DETECT_OUTPUT"
  else
    HANDOFF_CONTEXT="ERROR: thread_handoff.py detect failed. Stop.
Output:
$DETECT_OUTPUT"
  fi
elif [ -n "$HANDOFF_CONTEXT" ]; then
  : # Lease failure above is authoritative; never replace it with detect output.
elif ! DETECT_STATUS=$(printf '%s' "$DETECT_OUTPUT" | "$ROLLOVER_PYTHON" -c 'import json,sys; print(json.loads(sys.stdin.read()).get("status", ""), end="")'); then
  HANDOFF_CONTEXT="ERROR: thread_handoff.py detect output could not be parsed. Stop.
Output:
$DETECT_OUTPUT"
elif [ "$DETECT_STATUS" = "ambiguous" ]; then
  HANDOFF_CONTEXT="ERROR: MULTIPLE live pending rollovers — do not cold-start; bind one exact candidate.
$DETECT_OUTPUT"
elif [ "$DETECT_STATUS" = "pending_start" ] || [ "$DETECT_STATUS" = "resumed" ]; then
  if ! HANDOFF_CONTEXT=$("$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" \
    --repo-root "$CANONICAL_ROOT" detect --agent "$HANDOFF_AGENT" \
    --current-thread-id "$CURRENT_THREAD_ID" "${TASK_FAMILY_ARGS[@]}" --format session-start 2>&1); then
    HANDOFF_CONTEXT="ERROR: thread_handoff.py detect failed. Stop.
Output:
$HANDOFF_CONTEXT"
  fi
elif [ "$DETECT_STATUS" = "none" ]; then
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
    if ! HANDOFF_CONTEXT=$("$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" \
      --repo-root "$CANONICAL_ROOT" detect --agent "$HANDOFF_AGENT" \
      --current-thread-id "$CURRENT_THREAD_ID" --format session-start 2>&1); then
      HANDOFF_CONTEXT="ERROR: thread_handoff.py detect failed. Stop.
Output:
$HANDOFF_CONTEXT"
    fi
  fi
elif [ -z "$HANDOFF_CONTEXT" ]; then
  HANDOFF_CONTEXT="ERROR: Unexpected detect status: $DETECT_STATUS"
fi

# Epic assignment banner
EPIC_BANNER=""
if [ -n "${SESSION_EPIC:-}" ]; then
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
    if [ -n "${SESSION_EPIC:-}" ]; then
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

CONTEXT="$CONTEXT

SESSION SETUP CHECK:"

if [ ${#ISSUES[@]} -gt 0 ]; then
  CONTEXT="$CONTEXT
ISSUES:"
  for issue in "${ISSUES[@]}"; do
    CONTEXT="$CONTEXT
  - $issue"
  done
fi

if [ ${#INFO[@]} -gt 0 ]; then
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

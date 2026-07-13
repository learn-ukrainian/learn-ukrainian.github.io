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

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
ISSUES=()
INFO=()

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
# Excludes must match scripts/deploy_prompts.sh, derived dynamically from
# scripts/deploy_orphan_paths.sh to avoid hand-maintained drift (issue #4610).
# Without these, every cold start flags a false-positive drift.
if [ -d "$PROJECT_DIR/agents_extensions/shared" ] && [ -d "$PROJECT_DIR/.claude" ]; then
  DIFF_EXCLUDES=(".DS_Store")
  ORPHAN_PATHS_SH="$PROJECT_DIR/scripts/deploy_orphan_paths.sh"
  if [ -f "$ORPHAN_PATHS_SH" ]; then
    # shellcheck disable=SC1090
    source "$ORPHAN_PATHS_SH"
    # set -f: ORPHAN_PATHS_CLAUDE carries glob patterns (*-epic) that must reach
    # diff --exclude LITERALLY; without noglob the unquoted expansion would match
    # against the hook's cwd if a *-epic entry ever appears there.
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
    # Fallback to the old static list if deploy_orphan_paths.sh is missing (graceful degradation)
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

# 8. Check MCP sources server health (historically called the RAG server)
MCP_STATUS=$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:8766/sse" 2>/dev/null)
if [ "$MCP_STATUS" != "200" ] && [ "$MCP_STATUS" != "000" ]; then
  # 000 means connection refused (server down), non-200 means server error
  INFO+=("MCP sources server returned HTTP $MCP_STATUS — some tools may be unavailable")
elif [ "$MCP_STATUS" = "000" ]; then
  ISSUES+=("MCP sources server unreachable at 127.0.0.1:8766 — VESUM + textbook + dictionary tools unavailable. Start with: ./services.sh start sources")
fi

# 9. Check gemini-cli auth
if command -v gemini >/dev/null 2>&1; then
  GEMINI_CHECK=$(gemini --version 2>&1)
  if [[ "$GEMINI_CHECK" == *"error"* ]] || [[ "$GEMINI_CHECK" == *"auth"* ]]; then
    INFO+=("gemini-cli may need re-authentication: gemini auth login")
  fi
else
  INFO+=("gemini-cli not found — Gemini builds unavailable")
fi

# 10. Check for stale decisions
if [ -f "$PROJECT_DIR/.venv/bin/python" ] && [ -f "$PROJECT_DIR/scripts/check_decisions.py" ]; then
  STALE_DECISIONS=$("$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/check_decisions.py" --quiet 2>/dev/null)
  if [ -n "$STALE_DECISIONS" ]; then
    INFO+=("$STALE_DECISIONS")
  fi
fi

# 10b. Check ADR hygiene (sister to check_decisions). Process + rationale:
# docs/best-practices/adr-management.md.
if [ -f "$PROJECT_DIR/.venv/bin/python" ] && [ -f "$PROJECT_DIR/scripts/audit/check_adrs.py" ]; then
  ADR_REPORT=$("$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/scripts/audit/check_adrs.py" --quiet 2>/dev/null)
  ADR_EXIT=$?
  if [ "$ADR_EXIT" -ge 2 ] && [ -n "$ADR_REPORT" ]; then
    # Errors (missing required fields, broken supersede chains, numbering
    # duplicates) should surface as blocking ISSUES.
    ISSUES+=("ADR hygiene: $ADR_REPORT — see docs/best-practices/adr-management.md")
  elif [ -n "$ADR_REPORT" ]; then
    INFO+=("ADR hygiene: $ADR_REPORT")
  fi
fi

# 10c. Check postmortem hygiene (sister to decisions + ADRs). Process:
# docs/best-practices/postmortem-management.md.
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

# 11b. Issue-stream hygiene (#4708) — cached, never blocks session start.
# Fresh cache (<1h): surface orphans as ISSUES so every cold-starting agent
# (Claude, Codex, agy, cursor) sees stream drift. Stale/no cache: kick a
# background refresh so the NEXT start is covered.
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

    # 11c. Research-registry strict adoption gate (ADR-011 P4, PR #4998 review):
    # the fresh cache just confirmed above is exactly the input
    # `--strict-adoption` needs — wire it in HERE so it is not a dead CLI.
    # Offline (reads only the cache we already have), non-blocking (an ISSUES
    # entry, never a session-start failure).
    if [ -f "$PROJECT_DIR/scripts/audit/check_research_registry.py" ] && \
       [ -f "$PROJECT_DIR/docs/references/research-registry.yaml" ] && \
       [ -x "$PROJECT_DIR/.venv/bin/python" ]; then
      STRICT_JSON=$(cd "$PROJECT_DIR" && "$PROJECT_DIR/.venv/bin/python" scripts/audit/check_research_registry.py --strict-adoption --json 2>/dev/null)
      # NOTE: jq's `//` treats `false` as falsy too, so `.ok // empty` would
      # silently discard a real `false` — read `.ok` directly instead.
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

# 12. Git hygiene — warn if too many dirty files accumulated.
# See docs/best-practices/git-hygiene.md for policy.
# Exempt paths (wiki/**, data/corpus_audit/draft_tickets/) can be legitimately
# dirty during parallel builds; everything else is drift.
if command -v git >/dev/null 2>&1 && [ -d "$PROJECT_DIR/.git" ]; then
  HYGIENE_THRESHOLD_WARN=5
  HYGIENE_THRESHOLD_ISSUE=20

  # Count dirty files NOT matched by any exemption pattern. Keep this
  # in sync with docs/best-practices/git-hygiene.md § "Exemption paths".
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
fi

# 13. Session handoff — prefer gitignored local thread rollover packets.
# Do not read/dump docs/session-state/current.md by default. That router is
# git-tracked and has repeatedly dirtied the shared main checkout. Rollover
# state belongs in .agent/<agent>-thread-handoff.md, produced by
# scripts/orchestration/thread_handoff.py prepare.
HANDOFF_FILE="$PROJECT_DIR/docs/session-state/current.md"
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
LOCAL_THREAD_HANDOFF="$PROJECT_DIR/.agent/${HANDOFF_AGENT}-thread-handoff.md"
HANDOFF_CONTEXT=""
HANDOFF_WARNINGS=""

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
  local bootstrap_path=".agent/${HANDOFF_AGENT}-thread-bootstrap.md"
  cat <<EOF
PREVIOUS-SESSION HANDOFF — read the local thread rollover packet first.

Agent: $HANDOFF_AGENT
Thread handoff: $handoff_path
Bootstrap prompt: $bootstrap_path
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

if [ -f "$LOCAL_THREAD_HANDOFF" ]; then
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

# Epic assignment banner — the FIRST thing the session reads. SESSION_EPIC is
# exported by start-claude.sh from its launcher-only `--epic` flag. With an
# epic: bind the session to that lane and point at the epic driver handoff.
# Without: forbid the old "standalone = main orchestrator" default that caused
# the 2026-07-13 atlas/hramatka/main lane collision — the session must resolve
# its lane from the user's first message / .agent/lane-assignments.md, or ASK.
EPIC_BANNER=""
if [ -n "${SESSION_EPIC:-}" ]; then
  EPIC_BANNER="ASSIGNED EPIC: ${SESSION_EPIC}.epic (binding — from the launch command).
You are the ${SESSION_EPIC} lane, NOT the main orchestrator. Do not claim or work
other lanes' queues. Epic driver handoff (load AFTER the thread handoff below, it
is the lane SSOT): .claude/${SESSION_EPIC}-epic/CLAUDE-DRIVER-HANDOFF.md"
  if [ ! -f "$PROJECT_DIR/.claude/${SESSION_EPIC}-epic/CLAUDE-DRIVER-HANDOFF.md" ]; then
    EPIC_BANNER="$EPIC_BANNER
(No driver handoff exists yet for this epic — create it at first rollover.)"
  fi
else
  EPIC_BANNER="NO EPIC ASSIGNED (launcher had no --epic flag).
Do NOT default to 'main orchestrator'. Resolve your lane in this order:
1. The user's first message names the epic → that binds.
2. .agent/lane-assignments.md maps this agent type to exactly ONE epic → that binds.
3. Otherwise ASK THE USER one question ('which epic is this session?') BEFORE
   claiming any lane, reading any thread handoff as your own, or touching queues."
fi

# Build output
if [ ${#ISSUES[@]} -eq 0 ] && [ ${#INFO[@]} -eq 0 ] && [ -z "$HANDOFF_CONTEXT" ] && [ -z "$EPIC_BANNER" ]; then
  exit 0
fi

CONTEXT=""
if [ -n "$EPIC_BANNER" ]; then
  CONTEXT="$EPIC_BANNER

"
fi
if [ -n "$HANDOFF_CONTEXT" ]; then
  CONTEXT="${CONTEXT}$HANDOFF_CONTEXT
"
fi
CONTEXT="${CONTEXT}SESSION SETUP CHECK:"

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

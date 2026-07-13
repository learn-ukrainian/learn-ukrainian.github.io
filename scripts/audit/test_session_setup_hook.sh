#!/usr/bin/env bash
set -euo pipefail

unset GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR GIT_DIR GIT_INDEX_FILE
unset GIT_OBJECT_DIRECTORY GIT_PREFIX GIT_WORK_TREE

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOK="$REPO_ROOT/agents_extensions/shared/hooks/session-setup.sh"
POST_COMPACT_HOOK="$REPO_ROOT/agents_extensions/shared/hooks/post-compact.sh"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local label="$3"

  if [[ "$haystack" != *"$needle"* ]]; then
    echo "OUTPUT WAS: $haystack"
    fail "$label: expected output to contain: $needle"
  fi
}

assert_not_contains() {
  local haystack="$1"
  local needle="$2"
  local label="$3"

  if [[ "$haystack" == *"$needle"* ]]; then
    echo "OUTPUT WAS: $haystack"
    fail "$label: expected output not to contain: $needle"
  fi
}

count_warns() {
  local haystack="$1"

  awk '{count += gsub(/WARN:/, "")} END {print count + 0}' <<< "$haystack"
}

setup_fixture() {
  local root="$1"

  rm -rf "$root"
  mkdir -p "$root/docs/session-state" "$root/.venv/bin" "$root/.mcp/servers/message-broker" "$TMP_ROOT/home"
  # Dispatching stub: most tests just need a python-version banner, but the
  # strict-adoption-gate fixtures (below) need a controllable
  # `check_research_registry.py --strict-adoption` response without a real
  # venv or registry.
  cat > "$root/.venv/bin/python" <<'PYEOF'
#!/usr/bin/env bash
if [[ "$*" == *"check_research_registry.py"* ]]; then
  printf '%s\n' "$STRICT_GATE_FAKE_JSON"
  exit "${STRICT_GATE_FAKE_EXIT:-0}"
fi
printf "Python 3.12.8\n"
PYEOF
  printf 'fixture db\n' > "$root/.mcp/servers/message-broker/messages.db"
  chmod +x "$root/.venv/bin/python"
  mkdir -p "$root/scripts/orchestration"
  touch "$root/scripts/orchestration/thread_handoff.py"
  git -C "$root" init -q
  git -C "$root" config user.email "session-setup@example.invalid"
  git -C "$root" config user.name "Session Setup Fixture"
  printf 'fixture\n' > "$root/.git-fixture"
  git -C "$root" add .git-fixture
  git -C "$root" -c commit.gpgsign=false commit -q -m "fixture"
  printf '*\n' > "$root/.git/info/exclude"
}

run_hook() {
  local root="$1"
  local allow_git_router="${2:-0}"
  local handoff_agent="${3:-claude}"
  local current_thread_id="${4:-}"

  HOME="$TMP_ROOT/home" XDG_CONFIG_HOME="$TMP_ROOT/xdg-config" XDG_CACHE_HOME="$TMP_ROOT/xdg-cache" XDG_DATA_HOME="$TMP_ROOT/xdg-data" XDG_STATE_HOME="$TMP_ROOT/xdg-state" GH_CONFIG_DIR="$TMP_ROOT/gh" PATH="/usr/bin:/bin" \
    CLAUDE_PROJECT_DIR="$root" \
    CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS=32000 \
    CODEX_THREAD_ID="$current_thread_id" \
    CODEX_CANONICAL_REPO_ROOT="$root" \
    THREAD_ROLLOVER_PYTHON="$REPO_ROOT/.venv/bin/python" \
    THREAD_ROLLOVER_SCRIPT="$REPO_ROOT/scripts/orchestration/thread_handoff.py" \
    SESSION_HANDOFF_AGENT="$handoff_agent" \
    SESSION_HANDOFF_ALLOW_GIT_ROUTER="$allow_git_router" \
    "$HOOK"
}

prepare_fixture() {
  local root="$1"
  local agent="$2"
  local thread_id="$3"

  HOME="$TMP_ROOT/home" XDG_CONFIG_HOME="$TMP_ROOT/xdg-config" XDG_CACHE_HOME="$TMP_ROOT/xdg-cache" XDG_DATA_HOME="$TMP_ROOT/xdg-data" XDG_STATE_HOME="$TMP_ROOT/xdg-state" GH_CONFIG_DIR="$TMP_ROOT/gh" \
    CODEX_CANONICAL_REPO_ROOT="$root" PATH="/usr/bin:/bin" \
    "$REPO_ROOT/.venv/bin/python" "$REPO_ROOT/scripts/orchestration/thread_handoff.py" \
    --repo-root "$root" --monitor-base-url http://127.0.0.1:1 prepare --agent "$agent" --active-thread-id "$thread_id" >/dev/null
}

find_rollover_lease() {
  local root="$1"
  local agent="$2"

  find "$root/.agent/thread-rollovers/$agent" -name lease.json -print -quit
}

resume_fixture() {
  local root="$1"
  local agent="$2"
  local state_file="$3"
  local replacement_thread_id="$4"
  local rollover_id

  rollover_id=$("$REPO_ROOT/.venv/bin/python" -c \
    'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["replacement"]["rollover_id"])' \
    "$state_file")

  HOME="$TMP_ROOT/home" XDG_CONFIG_HOME="$TMP_ROOT/xdg-config" XDG_CACHE_HOME="$TMP_ROOT/xdg-cache" XDG_DATA_HOME="$TMP_ROOT/xdg-data" XDG_STATE_HOME="$TMP_ROOT/xdg-state" GH_CONFIG_DIR="$TMP_ROOT/gh" PATH="/usr/bin:/bin" \
    "$REPO_ROOT/.venv/bin/python" "$REPO_ROOT/scripts/orchestration/thread_handoff.py" \
    --repo-root "$root" --monitor-base-url http://127.0.0.1:1 resume --agent "$agent" \
    --state-file "$state_file" --rollover-id "$rollover_id" \
    --replacement-thread-id "$replacement_thread_id" >/dev/null
}

run_post_compact() {
  local root="$1"
  HOME="$TMP_ROOT/home" XDG_CONFIG_HOME="$TMP_ROOT/xdg-config" XDG_CACHE_HOME="$TMP_ROOT/xdg-cache" XDG_DATA_HOME="$TMP_ROOT/xdg-data" XDG_STATE_HOME="$TMP_ROOT/xdg-state" GH_CONFIG_DIR="$TMP_ROOT/gh" \
    CLAUDE_PROJECT_DIR="$root" SESSION_HANDOFF_AGENT="codex" CODEX_CANONICAL_REPO_ROOT="$root" \
    THREAD_ROLLOVER_PYTHON="$REPO_ROOT/.venv/bin/python" \
    THREAD_ROLLOVER_SCRIPT="$REPO_ROOT/scripts/orchestration/thread_handoff.py" \
    "$POST_COMPACT_HOOK"
}

fixture_root="$TMP_ROOT/project"
fallback_warn_count=0
marker_bytes="0"

# 1. Local gitignored thread handoff wins when no v2 packet is live.
setup_fixture "$fixture_root"
mkdir -p "$fixture_root/.agent" "$fixture_root/docs/session-state"
printf '# local handoff\n' > "$fixture_root/.agent/claude-thread-handoff.md"
cat > "$fixture_root/docs/session-state/current.md" <<'EOF'
# Current

CURRENT BODY SHOULD NOT APPEAR
EOF
output="$(run_hook "$fixture_root")"
assert_contains "$output" "Thread handoff: .agent/claude-thread-handoff.md" "local handoff"
assert_contains "$output" "Bootstrap prompt: .agent/claude-thread-bootstrap.md" "local handoff"
assert_not_contains "$output" "CURRENT BODY SHOULD NOT APPEAR" "local handoff"
assert_not_contains "$output" "WARN:" "local handoff"

# 2. current.md is ignored by default when no local handoff exists.
setup_fixture "$fixture_root"
cat > "$fixture_root/docs/session-state/current.md" <<'EOF'
# Current

DEFAULT ROUTER BODY SHOULD NOT APPEAR
EOF
output="$(run_hook "$fixture_root")"
assert_not_contains "$output" "DEFAULT ROUTER BODY SHOULD NOT APPEAR" "router ignored by default"
assert_not_contains "$output" "WARN: Could not locate latest brief in current.md" "router ignored by default"

# 3. Marker path is used when legacy router is explicitly enabled.
setup_fixture "$fixture_root"
mkdir -p "$fixture_root/foo"
printf 'brief body\n' > "$fixture_root/foo/bar-brief.md"
cat > "$fixture_root/docs/session-state/current.md" <<'EOF'
# Current

Latest-Brief: foo/bar-brief.md

HEAD BODY SHOULD NOT APPEAR
EOF
output="$(run_hook "$fixture_root" 1)"
assert_contains "$output" "PREVIOUS-SESSION HANDOFF" "marker hit"
assert_contains "$output" "Brief: foo/bar-brief.md" "marker hit"
assert_not_contains "$output" "HEAD BODY SHOULD NOT APPEAR" "marker hit"
assert_not_contains "$output" "WARN:" "marker hit"
marker_bytes="$(printf '%s' "$output" | wc -c | tr -d ' ')"

# 4. Agent-Handoff mapping wins over Latest-Brief.
setup_fixture "$fixture_root"
mkdir -p "$fixture_root/docs/session-state"
printf 'orchestrator body\n' > "$fixture_root/docs/session-state/codex-orchestrator-handoff.md"
printf 'claude body\n' > "$fixture_root/docs/session-state/current.claude.md"
cat > "$fixture_root/docs/session-state/current.md" <<'EOF'
# Current Session Router

Latest-Brief: docs/session-state/codex-orchestrator-handoff.md

Agent-Handoff:
- orchestrator: docs/session-state/codex-orchestrator-handoff.md
- claude: docs/session-state/current.claude.md
EOF
output="$(run_hook "$fixture_root" 1)"
assert_contains "$output" "Brief: docs/session-state/current.claude.md" "agent handoff"
assert_not_contains "$output" "Brief: docs/session-state/codex-orchestrator-handoff.md" "agent handoff"
assert_not_contains "$output" "WARN:" "agent handoff"

# 5. Table regex fallback with missing marker.
setup_fixture "$fixture_root"
mkdir -p "$fixture_root/foo"
printf 'brief body\n' > "$fixture_root/foo/bar-brief.md"
cat > "$fixture_root/docs/session-state/current.md" <<'EOF'
# Current

| Thread | Handoff | Status |
|---|---|---|
| Test | **Brief (read first):** `foo/bar-brief.md`<br>**Detail (human-read):** `foo/bar.html` | ok |

TABLE FALLBACK BODY SHOULD NOT APPEAR
EOF
output="$(run_hook "$fixture_root" 1)"
assert_contains "$output" "Brief: foo/bar-brief.md" "table fallback"
assert_contains "$output" "WARN: Latest-Brief marker missing in current.md" "table fallback"
assert_not_contains "$output" "TABLE FALLBACK BODY SHOULD NOT APPEAR" "table fallback"
fallback_warn_count=$((fallback_warn_count + $(count_warns "$output")))

# 6. Missing-brief warning retains no-router fallback guidance.
setup_fixture "$fixture_root"
cat > "$fixture_root/docs/session-state/current.md" <<'EOF'
# Current

Latest-Brief: foo/missing-brief.md

MISSING MARKER FALLBACK BODY
EOF
output="$(run_hook "$fixture_root" 1)"
assert_contains "$output" "WARN: Latest-Brief pointed to foo/missing-brief.md but file missing on disk." "missing brief"
assert_contains "$output" "legacy git router opt-in could not locate a compact handoff" "missing brief"
assert_not_contains "$output" "MISSING MARKER FALLBACK BODY" "missing brief"
fallback_warn_count=$((fallback_warn_count + $(count_warns "$output")))

# 7. No table in legacy mode falls back to deterministic guidance.
setup_fixture "$fixture_root"
cat > "$fixture_root/docs/session-state/current.md" <<'EOF'
# Current

NO TABLE FALLBACK BODY
EOF
output="$(run_hook "$fixture_root" 1)"
assert_contains "$output" "WARN: Could not locate latest brief in current.md under legacy router opt-in." "no table"
assert_contains "$output" "thread_handoff.py prepare --agent claude" "no table"
assert_not_contains "$output" "NO TABLE FALLBACK BODY" "no table"
fallback_warn_count=$((fallback_warn_count + $(count_warns "$output")))

# 8. SESSION_HANDOFF_AGENT isolates local packet lanes.
setup_fixture "$fixture_root"
mkdir -p "$fixture_root/.agent"
printf '# infra handoff\n' > "$fixture_root/.agent/claude-infra-thread-handoff.md"
printf '# folk handoff\n' > "$fixture_root/.agent/claude-thread-handoff.md"
output="$(run_hook "$fixture_root" 0 claude-infra)"
assert_contains "$output" "Thread handoff: .agent/claude-infra-thread-handoff.md" "infra lane isolation"
assert_not_contains "$output" "Thread handoff: .agent/claude-thread-handoff.md" "infra lane isolation"
assert_not_contains "$output" "WARN:" "infra lane isolation"

# 9. Research-registry strict-adoption gate (ADR-011 P4, PR #4998 review):
#    a fresh stream-audit cache plus a failing gate must surface an ISSUES entry.
setup_fixture "$fixture_root"
mkdir -p "$fixture_root/scripts/audit" "$fixture_root/scripts/orchestration" "$fixture_root/docs/references" "$fixture_root/batch_state"
printf '# stub\n' > "$fixture_root/scripts/audit/check_research_registry.py"
printf '# stub\n' > "$fixture_root/scripts/orchestration/issue_stream_audit.py"
printf 'records: []\n' > "$fixture_root/docs/references/research-registry.yaml"
printf '{"generated_at": %s, "orphans": [], "closed_or_missing_epics": []}\n' \
  "$(date +%s)" > "$fixture_root/batch_state/issue_stream_audit.json"
export STRICT_GATE_FAKE_JSON='{"ok": false, "errors": ["demo-record: consumer issue 999 did not resolve"], "drift": [], "cache": "fresh"}'
export STRICT_GATE_FAKE_EXIT=2
output="$(run_hook "$fixture_root")"
unset STRICT_GATE_FAKE_JSON STRICT_GATE_FAKE_EXIT
assert_contains "$output" "Research registry strict-adoption gate FAILED" "strict gate wired"
assert_contains "$output" "demo-record: consumer issue 999 did not resolve" "strict gate wired"

# 10. A passing strict-adoption gate must remain silent on success.
setup_fixture "$fixture_root"
mkdir -p "$fixture_root/scripts/audit" "$fixture_root/scripts/orchestration" "$fixture_root/docs/references" "$fixture_root/batch_state"
printf '# stub\n' > "$fixture_root/scripts/audit/check_research_registry.py"
printf '# stub\n' > "$fixture_root/scripts/orchestration/issue_stream_audit.py"
printf 'records: []\n' > "$fixture_root/docs/references/research-registry.yaml"
printf '{"generated_at": %s, "orphans": [], "closed_or_missing_epics": []}\n' \
  "$(date +%s)" > "$fixture_root/batch_state/issue_stream_audit.json"
export STRICT_GATE_FAKE_JSON='{"ok": true, "errors": [], "drift": [], "cache": "fresh"}'
export STRICT_GATE_FAKE_EXIT=0
output="$(run_hook "$fixture_root")"
unset STRICT_GATE_FAKE_JSON STRICT_GATE_FAKE_EXIT
assert_not_contains "$output" "Research registry strict-adoption gate FAILED" "strict gate passing"
assert_not_contains "$output" "WARN:" "strict gate passing"

# 11. Engine-generated pending packet is authoritative.
setup_fixture "$fixture_root"
prepare_fixture "$fixture_root" claude old-thread
output="$(run_hook "$fixture_root")"
assert_contains "$output" "PENDING THREAD ROLLOVER DETECTED" "pending packet"
assert_contains "$output" "--agent claude" "pending packet"
assert_not_contains "$output" "COLD START: NO LIVE THREAD ROLLOVER" "pending packet"

# 12. No live packet + no legacy artifacts emits cold-start engine guidance.
setup_fixture "$fixture_root"
output="$(run_hook "$fixture_root")"
assert_contains "$output" "COLD START: NO LIVE THREAD ROLLOVER" "engine cold start"
assert_contains "$output" "Create exactly ten truthful legacy orientation facts" "engine cold start"

# 13. Engine lane isolation across local .agent paths.
setup_fixture "$fixture_root"
prepare_fixture "$fixture_root" claude old-claude
prepare_fixture "$fixture_root" claude-infra old-infra
output_claude="$(run_hook "$fixture_root" 0 claude)"
assert_contains "$output_claude" "--agent claude " "engine lane isolation"
output_infra="$(run_hook "$fixture_root" 0 claude-infra)"
assert_contains "$output_infra" "--agent claude-infra" "engine lane isolation"

# 14. Malformed and ambiguous v2 packets stop and do not fall back.
setup_fixture "$fixture_root"
prepare_fixture "$fixture_root" claude old-a
state_file="$(find_rollover_lease "$fixture_root" claude)"
cat > "$state_file" <<'EOF'
{ "schema_version": 2, "thread": "broken"
EOF
output="$(run_hook "$fixture_root" 0 claude)"
assert_contains "$output" "ERROR: thread_handoff.py detect failed. Stop." "malformed packet"

setup_fixture "$fixture_root"
prepare_fixture "$fixture_root" codex old-a
prepare_fixture "$fixture_root" codex old-b
output="$(run_hook "$fixture_root" 0 codex)"
assert_contains "$output" "Multiple live pending rollovers found for agent codex" "ambiguous packet"

# 15. Resumed packet for current thread allowed; mismatch blocks.
setup_fixture "$fixture_root"
prepare_fixture "$fixture_root" codex old-thread
state_file="$(find_rollover_lease "$fixture_root" codex)"
resume_fixture "$fixture_root" codex "$state_file" old-thread
output="$(run_hook "$fixture_root" 0 codex old-thread)"
assert_contains "$output" "RESUMED THREAD ROLLOVER DETECTED" "resumed same thread"
assert_not_contains "$output" "PENDING THREAD ROLLOVER DETECTED" "resumed same thread"

output="$(run_hook "$fixture_root" 0 codex other-thread)"
assert_contains "$output" "live rollover is already bound to a different replacement thread" "resumed bound other thread"
assert_contains "$output" "old-thread" "resumed bound other thread"

# 16. PostCompact remains read-only and surfaces packet health only.
setup_fixture "$fixture_root"
prepare_fixture "$fixture_root" codex old-thread
output="$(run_post_compact "$fixture_root")"
assert_contains "$output" "Thread rollover health (read-only)" "post compact health"
assert_contains "$output" '\"status\": \"pending_start\"' "post compact packet"
assert_not_contains "$output" "confirm-started" "post compact no confirmation"

printf 'marker_hit_stdout_bytes=%s\n' "$marker_bytes"
printf 'fallback_warn_count=%s\n' "$fallback_warn_count"
printf 'ok - session setup hook handoff fixtures passed\n'

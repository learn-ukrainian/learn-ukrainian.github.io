#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOK="$REPO_ROOT/agents_extensions/shared/hooks/session-setup.sh"
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
    fail "$label: expected output to contain: $needle"
  fi
}

assert_not_contains() {
  local haystack="$1"
  local needle="$2"
  local label="$3"

  if [[ "$haystack" == *"$needle"* ]]; then
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
}

run_hook() {
  local root="$1"
  local allow_git_router="${2:-0}"
  local handoff_agent="${3:-claude}"

  HOME="$TMP_ROOT/home" \
    CLAUDE_PROJECT_DIR="$root" \
    CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS=32000 \
    SESSION_HANDOFF_AGENT="$handoff_agent" \
    SESSION_HANDOFF_ALLOW_GIT_ROUTER="$allow_git_router" \
    "$HOOK"
}

fixture_root="$TMP_ROOT/project"
fallback_warn_count=0

# 1. Local gitignored thread handoff wins by default.
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

# 2. current.md is ignored by default when no local thread handoff exists.
setup_fixture "$fixture_root"
cat > "$fixture_root/docs/session-state/current.md" <<'EOF'
# Current

DEFAULT ROUTER BODY SHOULD NOT APPEAR
EOF
output="$(run_hook "$fixture_root")"
assert_not_contains "$output" "DEFAULT ROUTER BODY SHOULD NOT APPEAR" "router ignored by default"
assert_not_contains "$output" "WARN: Could not locate latest brief in current.md" "router ignored by default"

# 3. Legacy marker path hits only when explicitly enabled.
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

# 4. Agent-Handoff mapping wins over the compatibility Latest-Brief marker when legacy router is enabled.
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

# 5. Table regex fallback when legacy router is enabled.
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

# 6. Brief missing when legacy router is enabled.
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

# 7. No handoff table at all when legacy router is enabled.
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

# 8. SESSION_HANDOFF_AGENT routes each lane to its OWN thread handoff slot.
#    Regression guard for the infra/folk cold-start collision: with both handoff files
#    present, agent=claude-infra must select the infra slot, never the folk `claude` slot.
setup_fixture "$fixture_root"
mkdir -p "$fixture_root/.agent"
printf '# infra handoff\n' > "$fixture_root/.agent/claude-infra-thread-handoff.md"
printf '# folk handoff\n' > "$fixture_root/.agent/claude-thread-handoff.md"
output="$(run_hook "$fixture_root" 0 claude-infra)"
assert_contains "$output" "Thread handoff: .agent/claude-infra-thread-handoff.md" "infra lane isolation"
assert_contains "$output" "Bootstrap prompt: .agent/claude-infra-thread-bootstrap.md" "infra lane isolation"
assert_not_contains "$output" "Thread handoff: .agent/claude-thread-handoff.md" "infra lane isolation"
assert_not_contains "$output" "WARN:" "infra lane isolation"

# 9. Research-registry strict-adoption gate (ADR-011 P4, PR #4998 review): a
#    fresh stream-audit cache plus a failing gate must surface an ISSUES entry.
#    Proves the gate is wired into a real cold-start path, not a dead CLI.
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

# 10. A passing strict-adoption gate must NOT add an ISSUES entry (non-blocking,
#     silent on success).
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
assert_not_contains "$output" "strict-adoption gate FAILED" "strict gate passing"
assert_not_contains "$output" "WARN:" "strict gate passing"

printf 'marker_hit_stdout_bytes=%s\n' "$marker_bytes"
printf 'fallback_warn_count=%s\n' "$fallback_warn_count"
printf 'ok - session setup hook handoff fixtures passed\n'

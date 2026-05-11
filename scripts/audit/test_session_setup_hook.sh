#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOK="$REPO_ROOT/claude_extensions/hooks/session-setup.sh"
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
  printf '#!/usr/bin/env bash\nprintf "Python 3.12.8\\n"\n' > "$root/.venv/bin/python"
  printf 'fixture db\n' > "$root/.mcp/servers/message-broker/messages.db"
  chmod +x "$root/.venv/bin/python"
}

run_hook() {
  local root="$1"

  HOME="$TMP_ROOT/home" \
    CLAUDE_PROJECT_DIR="$root" \
    CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS=32000 \
    "$HOOK"
}

fixture_root="$TMP_ROOT/project"
fallback_warn_count=0

# 1. Marker path hits.
setup_fixture "$fixture_root"
mkdir -p "$fixture_root/foo"
printf 'brief body\n' > "$fixture_root/foo/bar-brief.md"
cat > "$fixture_root/docs/session-state/current.md" <<'EOF'
# Current

Latest-Brief: foo/bar-brief.md

HEAD BODY SHOULD NOT APPEAR
EOF
output="$(run_hook "$fixture_root")"
assert_contains "$output" "PREVIOUS-SESSION HANDOFF" "marker hit"
assert_contains "$output" "Brief: foo/bar-brief.md" "marker hit"
assert_not_contains "$output" "HEAD BODY SHOULD NOT APPEAR" "marker hit"
assert_not_contains "$output" "WARN:" "marker hit"
marker_bytes="$(printf '%s' "$output" | wc -c | tr -d ' ')"

# 2. Table regex fallback.
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
output="$(run_hook "$fixture_root")"
assert_contains "$output" "Brief: foo/bar-brief.md" "table fallback"
assert_contains "$output" "WARN: Latest-Brief marker missing in current.md" "table fallback"
assert_not_contains "$output" "TABLE FALLBACK BODY SHOULD NOT APPEAR" "table fallback"
fallback_warn_count=$((fallback_warn_count + $(count_warns "$output")))

# 3. Brief missing.
setup_fixture "$fixture_root"
cat > "$fixture_root/docs/session-state/current.md" <<'EOF'
# Current

Latest-Brief: foo/missing-brief.md

MISSING MARKER FALLBACK BODY
EOF
output="$(run_hook "$fixture_root")"
assert_contains "$output" "WARN: Latest-Brief pointed to foo/missing-brief.md but file missing on disk." "missing brief"
assert_contains "$output" "MISSING MARKER FALLBACK BODY" "missing brief"
fallback_warn_count=$((fallback_warn_count + $(count_warns "$output")))

# 4. No handoff table at all.
setup_fixture "$fixture_root"
cat > "$fixture_root/docs/session-state/current.md" <<'EOF'
# Current

NO TABLE FALLBACK BODY
EOF
output="$(run_hook "$fixture_root")"
assert_contains "$output" "WARN: Could not locate latest brief in current.md" "no table"
assert_contains "$output" "NO TABLE FALLBACK BODY" "no table"
fallback_warn_count=$((fallback_warn_count + $(count_warns "$output")))

printf 'marker_hit_stdout_bytes=%s\n' "$marker_bytes"
printf 'fallback_warn_count=%s\n' "$fallback_warn_count"
printf 'ok - session setup hook handoff fixtures passed\n'

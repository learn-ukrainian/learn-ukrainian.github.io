#!/usr/bin/env bash
# Fixtures for scripts/lib/deploy_extensions.sh — the fail-honest launcher
# deploy helper. Wired into the required pytest gate via
# tests/test_deploy_extensions.py so the deploy-failure banner (which replaced
# the fail-silent `|| true` in start-claude.sh / start-codex.sh) stays
# load-bearing: a regression back to silent success would fail these fixtures.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=scripts/lib/deploy_extensions.sh
source "$REPO_ROOT/scripts/lib/deploy_extensions.sh"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

contains() {
  # contains <haystack> <needle> <label>
  if [[ "$1" != *"$2"* ]]; then
    fail "$3: expected output to contain [$2], got: $1"
  fi
}

not_contains() {
  if [[ "$1" == *"$2"* ]]; then
    fail "$3: expected output NOT to contain [$2], got: $1"
  fi
}

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/deploy-ext-test.XXXXXX")"
trap 'rm -rf "$WORK_DIR"' EXIT

# Fake project with an agents:deploy script + a fake npm shim on PATH whose
# behaviour is driven by FAKE_NPM_EXIT / FAKE_NPM_OUTPUT.
mkdir -p "$WORK_DIR/project" "$WORK_DIR/bin"
printf '{"scripts": {"agents:deploy": "scripts/deploy_prompts.sh"}}\n' > "$WORK_DIR/project/package.json"
cat > "$WORK_DIR/bin/npm" <<'FAKE'
#!/usr/bin/env bash
printf '%s\n' "${FAKE_NPM_OUTPUT:-deploy output line}"
exit "${FAKE_NPM_EXIT:-0}"
FAKE
chmod +x "$WORK_DIR/bin/npm"
export PATH="$WORK_DIR/bin:$PATH"

# --- success: one confirmation line, no failure banner, exit 0 ---
out="$(FAKE_NPM_EXIT=0 deploy_agent_extensions "$WORK_DIR/project" agents:deploy)" \
  || fail "success case: expected exit 0, got $?"
contains "$out" "Agent extensions deployed" "success prints confirmation"
not_contains "$out" "DEPLOY FAILED" "success has no failure banner"

# --- failure: loud banner + real npm output surfaced + npm exit code returned ---
rc=0
out="$(FAKE_NPM_EXIT=3 FAKE_NPM_OUTPUT='rsync: permission denied somewhere' \
  deploy_agent_extensions "$WORK_DIR/project" agents:deploy)" || rc=$?
[[ "$rc" -eq 3 ]] || fail "failure case: expected exit 3, got $rc"
contains "$out" "AGENT-EXTENSIONS DEPLOY FAILED" "failure prints banner"
contains "$out" "exit 3" "failure banner includes exit code"
contains "$out" "rsync: permission denied somewhere" "failure surfaces real deploy output"
contains "$out" "may be STALE" "failure warns about stale targets"
not_contains "$out" "Agent extensions deployed" "failure never claims success"

# --- failure leaves a DURABLE breadcrumb for session-setup.sh ---
# The banner alone is not enough: the launcher hands the terminal to the agent
# CLI, which clears it, so the session boots blind against a stale target.
STATUS_FILE="$WORK_DIR/project/.agent/last-deploy-status"
FAILURE_LOG="$WORK_DIR/project/.agent/last-deploy-failure.log"
[[ -f "$STATUS_FILE" ]] || fail "failure did not persist $STATUS_FILE"
head -1 "$STATUS_FILE" | grep -q '^FAILED' \
  || fail "status file does not start with FAILED"
grep -q '^exit_code=3' "$STATUS_FILE" || fail "status file lost the exit code"
grep -q '^script=agents:deploy' "$STATUS_FILE" || fail "status file lost the script name"
[[ -f "$FAILURE_LOG" ]] || fail "failure did not persist $FAILURE_LOG"
grep -q 'rsync: permission denied somewhere' "$FAILURE_LOG" \
  || fail "persisted log lost the real deploy output"

# --- a later SUCCESS must clear the breadcrumb (no stale alarm next launch) ---
out="$(FAKE_NPM_EXIT=0 deploy_agent_extensions "$WORK_DIR/project" agents:deploy)" \
  || fail "post-failure success case: expected exit 0, got $?"
[[ ! -f "$STATUS_FILE" ]] || fail "success did not clear $STATUS_FILE"
[[ ! -f "$FAILURE_LOG" ]] || fail "success did not clear $FAILURE_LOG"

# --- session-setup.sh actually reads the breadcrumb back (wiring guard) ---
SESSION_SETUP="$REPO_ROOT/agents_extensions/shared/hooks/session-setup.sh"
grep -q 'last-deploy-status' "$SESSION_SETUP" \
  || fail "session-setup.sh no longer reads the predeploy status breadcrumb"
grep -q 'PREDEPLOY FAILED' "$SESSION_SETUP" \
  || fail "session-setup.sh no longer reports a failed predeploy"

# --- missing npm script: explicit skip warning, exit 0 ---
mkdir -p "$WORK_DIR/bare"
printf '{"scripts": {}}\n' > "$WORK_DIR/bare/package.json"
out="$(deploy_agent_extensions "$WORK_DIR/bare" agents:deploy)" \
  || fail "missing-script case: expected exit 0, got $?"
contains "$out" "not found" "missing script warns instead of failing"

# --- missing package.json: explicit skip warning, exit 0 ---
mkdir -p "$WORK_DIR/empty"
out="$(deploy_agent_extensions "$WORK_DIR/empty" agents:deploy)" \
  || fail "no-package-json case: expected exit 0, got $?"
contains "$out" "not found" "missing package.json warns instead of failing"

# --- launchers actually use the helper (regression guard on the wiring) ---
launcher=start-claude.sh
grep -q 'deploy_extensions.sh' "$REPO_ROOT/$launcher" \
  || fail "$launcher no longer sources deploy_extensions.sh"
grep -q 'deploy_agent_extensions' "$REPO_ROOT/$launcher" \
  || fail "$launcher no longer calls deploy_agent_extensions"
# ^[^#]* keeps the guard from false-positiving on comments that merely
# describe the old pattern (deepseek review recommendation, PR #4843).
if grep -E '^[^#]*npm run [a-z:]*deploy.*(\|\| true|2>/dev/null)' "$REPO_ROOT/$launcher" >/dev/null; then
  fail "$launcher reintroduced a fail-silent npm deploy"
fi

grep -q 'thread_rollover_link.sh' "$REPO_ROOT/start-codex.sh" \
  || fail "start-codex.sh no longer sources the Codex checkout bootstrap"
grep -q 'bootstrap_codex_checkout' "$REPO_ROOT/start-codex.sh" \
  || fail "start-codex.sh no longer bootstraps the target checkout"
grep -q -- '--git-common-dir' "$REPO_ROOT/start-codex.sh" \
  || fail "start-codex.sh no longer resolves the canonical checkout"
grep -q 'branch --show-current' "$REPO_ROOT/start-codex.sh" \
  || fail "start-codex.sh no longer requires canonical main"
grep -q 'GIT_OPTIONAL_LOCKS=0' "$REPO_ROOT/start-codex.sh" \
  || fail "start-codex.sh no longer suppresses optional primary-index locks"
if grep -Eq 'codex-interactive|git worktree add|checkout --detach' "$REPO_ROOT/start-codex.sh"; then
  fail "start-codex.sh reintroduced a detached interactive worktree"
fi

echo "ok - deploy extensions fixtures passed"

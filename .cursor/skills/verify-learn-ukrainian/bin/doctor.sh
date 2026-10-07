#!/usr/bin/env bash
# Read-only health check for a verify-learn-ukrainian instance.
# Exit 0 when the instance is worth driving; non-zero otherwise.
if [[ "${1:-}" == --help ]]; then
  cat <<'EOF'
Usage: bash .cursor/skills/verify-learn-ukrainian/bin/doctor.sh
Read-only health check before driving a local instance; not deployment proof.
First source the exact env.sh path printed by launch.sh.
Inputs: LU_VERIFY_HOST=localhost, LU_VERIFY_PORT=4321, Node 22;
        LU_VERIFY_PYTHON defaults to the checkout's .venv/bin/python.
Optional: LU_VERIFY_PID_FILE checks socket process-group ownership with ss;
          LU_VERIFY_EXPECTED_REV checks the checkout's HEAD.
Outputs: health diagnostics only. Exit: 0 healthy, 1 failed health check.
Related: launch.sh, drive-playwright.sh, ../SKILL.md.
EOF
  exit 0
fi
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"

PORT="${LU_VERIFY_PORT:-4321}"
# Default host matches site/playwright.config.ts (set LU_VERIFY_HOST to override).
HOST="${LU_VERIFY_HOST:-localhost}"
BASE_URL="http://${HOST}:${PORT}"
PID_FILE="${LU_VERIFY_PID_FILE:-}"
EXPECTED_REV="${LU_VERIFY_EXPECTED_REV:-}"

fail() { echo "doctor FAIL: $*" >&2; exit 1; }
ok() { echo "doctor OK: $*"; }

# Interpreter + Node (site package engines.node = 22.x)
PYTHON="${LU_VERIFY_PYTHON:-${ROOT}/.venv/bin/python}"
[[ -x "$PYTHON" ]] || fail "project interpreter missing — set LU_VERIFY_PYTHON to the shared interpreter in a worktree"
NODE_MAJOR="$(node -v 2>/dev/null | sed -E 's/^v([0-9]+).*/\1/' || true)"
[[ "$NODE_MAJOR" == "22" ]] || fail "need Node 22.x on PATH (got: $(node -v 2>/dev/null || echo none))"

# HTTP readiness
if ! curl -fsS --max-time 5 "${BASE_URL}/" >/dev/null; then
  fail "site not answering at ${BASE_URL}/"
fi
ok "site answering at ${BASE_URL}/"

# Learner route smoke (HTML, not SPA fallback alone)
for path in /a1/ /lexicon/ /practice/; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' --max-time 10 "${BASE_URL}${path}" || echo 000)"
  [[ "$code" == "200" ]] || fail "GET ${path} returned HTTP ${code}"
done
ok "learner routes /a1/ /lexicon/ /practice/ return 200"

# Optional: confirm we own the listening process
if [[ -n "$PID_FILE" ]]; then
  [[ -f "$PID_FILE" ]] || fail "PID file missing: $PID_FILE"
  pid="$(cat "$PID_FILE")"
  [[ "$pid" =~ ^[1-9][0-9]*$ && -d "/proc/$pid" ]] || fail "recorded PID $pid is not running"
  # setsid gives the launcher and its descendants an isolated process group.
  pgid="$(ps -o pgid= -p "$pid" | tr -d '[:space:]')"
  [[ "$pgid" == "$pid" ]] || fail "recorded PID $pid is not its process group leader"
  if command -v ss >/dev/null 2>&1; then
    listeners="$(ss -ltnp "sport = :${PORT}" 2>/dev/null || true)"
    owned=false
    while IFS= read -r listener_pid; do
      listener_pgid="$(ps -o pgid= -p "$listener_pid" 2>/dev/null | tr -d '[:space:]' || true)"
      if [[ "$listener_pgid" == "$pgid" ]]; then
        owned=true
        break
      fi
    done < <(grep -oE 'pid=[0-9]+,' <<<"$listeners" | sed -E 's/pid=([0-9]+),/\1/')
    [[ "$owned" == true ]] || fail "port ${PORT} not owned by process group ${pgid}"
    ok "port ${PORT} owned by process group ${pgid}"
  else
    echo "doctor SKIP: socket ownership unavailable (ss missing)"
  fi
fi

if [[ -n "$EXPECTED_REV" ]]; then
  head_rev="$(git -C "$ROOT" rev-parse HEAD)"
  [[ "$head_rev" == "$EXPECTED_REV" ]] || fail "HEAD ${head_rev} != expected ${EXPECTED_REV}"
  ok "git HEAD matches expected revision"
fi

ok "instance worth driving"
exit 0

#!/usr/bin/env bash
# Read-only health check for a verify-learn-ukrainian instance.
# Exit 0 when the instance is worth driving; non-zero otherwise.
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
[[ -x "$ROOT/.venv/bin/python" ]] || fail "missing .venv/bin/python — create the project venv first"
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
  [[ -n "$pid" && -d "/proc/$pid" ]] || fail "recorded PID $pid is not running"
  # Port must be owned by that PID or one of its children
  if command -v ss >/dev/null 2>&1; then
    listeners="$(ss -ltnp "sport = :${PORT}" 2>/dev/null || true)"
    echo "$listeners" | grep -q "pid=${pid}" || fail "port ${PORT} not owned by PID ${pid}"
  fi
  ok "port ${PORT} owned by PID ${pid}"
fi

if [[ -n "$EXPECTED_REV" ]]; then
  head_rev="$(git -C "$ROOT" rev-parse HEAD)"
  [[ "$head_rev" == "$EXPECTED_REV" ]] || fail "HEAD ${head_rev} != expected ${EXPECTED_REV}"
  ok "git HEAD matches expected revision"
fi

ok "instance worth driving"
exit 0

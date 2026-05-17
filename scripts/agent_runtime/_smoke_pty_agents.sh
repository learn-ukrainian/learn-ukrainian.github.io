#!/usr/bin/env bash
# Per-agent PTY smoke validation (#2071).
#
# Fires a small "say hello" probe via runner.invoke against each of the
# 5 supported agents and asserts:
#
#   1. response_chars > 0  — output was captured (the actual #2071 bug)
#   2. result.ok is True   — the call completed cleanly
#
# This is a MANUAL post-merge validation tool. It makes real LLM calls
# (small ones — "say hello"), so we don't run it automatically in CI;
# the user / orchestrator runs it once after PR merge, captures the
# per-agent output, and either confirms green or files a follow-up
# issue for any regression.
#
# Usage:
#     bash scripts/agent_runtime/_smoke_pty_agents.sh            # all 5
#     bash scripts/agent_runtime/_smoke_pty_agents.sh codex      # one
#     bash scripts/agent_runtime/_smoke_pty_agents.sh codex gemini
#
# Output: one JSON line per agent on stdout. On any failure (no
# response, regression, etc.) the script prints the failure and
# continues to the next agent. Final exit code = number of failed
# agents (0 = all green).
#
# Per-agent regression workaround: set DELEGATE_DISABLE_PTY=1 in the
# adapter's spawn path. Document the issue, file a follow-up, restore
# PTY mode once the agent-specific fix lands.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${ROOT}" || exit 1

VENV_PY="${ROOT}/.venv/bin/python"
if [[ ! -x "${VENV_PY}" ]]; then
    COMMON_DIR="$(git rev-parse --git-common-dir 2>/dev/null || true)"
    if [[ -n "${COMMON_DIR}" ]]; then
        CANDIDATE="$(cd "${COMMON_DIR}/.." 2>/dev/null && pwd)/.venv/bin/python"
        if [[ -x "${CANDIDATE}" ]]; then
            VENV_PY="${CANDIDATE}"
        fi
    fi
fi
if [[ ! -x "${VENV_PY}" ]]; then
    echo "ERROR: cannot locate .venv/bin/python (worktree or main checkout)" >&2
    exit 99
fi

# The Python smoke driver — written to a temp file so we can invoke it
# without heredoc-pipe parsing oddities.
DRIVER="$(mktemp -t pty-smoke-driver.XXXXXX.py)"
cat >"${DRIVER}" <<'PYDRIVER'
import json
import os
import sys
import time
from pathlib import Path

agent = sys.argv[1]
repo_root = Path(os.environ["LU_ROOT"])
sys.path.insert(0, str(repo_root / "scripts"))

MODEL_BY_AGENT = {
    "codex":    None,
    "gemini":   "gemini-3-flash-preview",
    "claude":   "claude-haiku-4-5-20251001",
    "deepseek": "deepseek-v4-flash",
    "grok":     None,
}

prompt = "Reply with exactly: SMOKE_OK"

start = time.monotonic()
result = None
err = None
try:
    from agent_runtime.runner import invoke
    result = invoke(
        agent_name=agent,
        prompt=prompt,
        mode="read-only",
        cwd=repo_root,
        model=MODEL_BY_AGENT.get(agent),
        entrypoint="runtime",
        hard_timeout=120,
    )
except Exception as exc:
    err = f"{type(exc).__name__}: {exc}"
elapsed = time.monotonic() - start

report = {
    "agent": agent,
    "elapsed_s": round(elapsed, 2),
    "ok": result.ok if result is not None else False,
    "response_chars": len(result.response) if result is not None else 0,
    "model": getattr(result, "model", None) if result is not None else None,
    "error": err,
}
print(json.dumps(report))

fail_reasons = []
if not report["ok"]:
    fail_reasons.append(f"result.ok=False (err={err})")
if report["response_chars"] == 0:
    fail_reasons.append("response_chars=0 — PTY may not be flowing")
if fail_reasons:
    print("REGRESSION:", "; ".join(fail_reasons), file=sys.stderr)
    sys.exit(2)
PYDRIVER

cleanup() {
    rm -f "${DRIVER}"
}
trap cleanup EXIT

AGENTS=("$@")
if [[ ${#AGENTS[@]} -eq 0 ]]; then
    AGENTS=(codex gemini claude deepseek grok)
fi

FAILED=0
export LU_ROOT="${ROOT}"

for AGENT in "${AGENTS[@]}"; do
    echo "=== smoke: ${AGENT} ==="
    if "${VENV_PY}" "${DRIVER}" "${AGENT}"; then
        echo "  OK"
    else
        echo "  AGENT FAILED (exit $?)"
        FAILED=$((FAILED + 1))
    fi
done

echo
echo "=== smoke summary: ${FAILED} failed of ${#AGENTS[@]} agents ==="
exit "${FAILED}"

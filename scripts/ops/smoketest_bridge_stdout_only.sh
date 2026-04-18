#!/usr/bin/env bash
# Smoketest: ai_agent_bridge `--stdout-only` writes Gemini's response to stdout.
#
# Why this exists: the wiki review pipeline (scripts/wiki/compile.py) captures
# subprocess stdout and parses it for `X/10` scores. A bridge regression in
# 2026-04-18 had `--stdout-only` suppress broker delivery WITHOUT writing the
# response to stdout — wiki reviews silently returned 0.0/10 across every
# dimension and the per-dim audit floor failed the article. Run this after any
# change to scripts/ai_agent_bridge/_gemini.py or _cli.py to catch a re-regression
# before it pollutes a wiki compile run.
#
# Pass criteria: a single non-empty line of output, no `[gemini] attempt N/M`
# preamble, exit 0. We deliberately don't check semantic correctness of the
# response — Gemini occasionally over-explains a one-shot reply — only that
# something parseable made it to stdout.
#
# Usage:
#     bash scripts/ops/smoketest_bridge_stdout_only.sh
#
# Exit 0 = pass. Exit 1 = bridge is leaking the preamble or eating the response.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

PROMPT='Reply with EXACTLY this single line and nothing else: PARSER_TEST_OK 9.5/10'
TASK_ID="bridge-stdout-only-smoketest-$(date +%s)"

OUT_FILE="$(mktemp -t bridge-smoke-out.XXXXXX)"
ERR_FILE="$(mktemp -t bridge-smoke-err.XXXXXX)"
trap 'rm -f "$OUT_FILE" "$ERR_FILE"' EXIT

# `unset` of GEMINI_API_KEY / GOOGLE_API_KEY forces the bridge through the
# subscription path (matches how production wiki compiles call it).
unset GEMINI_API_KEY GOOGLE_API_KEY

if ! printf '%s\n' "$PROMPT" | timeout 180 \
        .venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini - \
            --task-id "$TASK_ID" \
            --model gemini-3.1-pro-preview \
            --stdout-only \
            --from claude \
        > "$OUT_FILE" 2> "$ERR_FILE"; then
    echo "FAIL: ask-gemini --stdout-only exited non-zero." >&2
    echo "--- stderr ---" >&2
    head -40 "$ERR_FILE" >&2
    exit 1
fi

# Must contain something — empty stdout means the response was eaten.
if [[ ! -s "$OUT_FILE" ]]; then
    echo "FAIL: stdout was empty. Bridge is not writing Gemini's response." >&2
    echo "--- stderr ---" >&2
    head -40 "$ERR_FILE" >&2
    exit 1
fi

# Must NOT contain the bridge progress preamble — that line leaking into stdout
# is the exact regression Phase A canary 2026-04-18 surfaced (was masking real
# review scores under "0.0/10 across all dims").
if grep -q '\[gemini\] attempt' "$OUT_FILE"; then
    echo "FAIL: '[gemini] attempt N/M' bridge preamble leaked into stdout." >&2
    echo "      The --stdout-only guard in _run_gemini_attempt regressed." >&2
    echo "--- stdout ---" >&2
    head -10 "$OUT_FILE" >&2
    exit 1
fi

echo "PASS: bridge --stdout-only delivered $(wc -c < "$OUT_FILE" | tr -d ' ') bytes to stdout."
exit 0

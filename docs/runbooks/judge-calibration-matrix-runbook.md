# Judge Calibration Matrix Runbook

This runbook is for the Russianism judge calibration matrix implemented in
`scripts/audit/judge_calibration_matrix.py`.

## Pre-flight

Fetch the PR #2006 calibration cases if the local ref is missing:

```bash
git fetch origin 'refs/pull/2006/head:refs/remotes/origin/pr-2006'
```

Verify Hermes routes return non-empty output before spending matrix quota:

```bash
hermes -z "Reply PONG." -m gpt-5.5
hermes -z "Reply PONG." -m claude-opus-4-7
```

Until #2036 is resolved (`hermes auth add anthropic`), run the Anthropic
family with `--harnesses native_cli` only. The harness supports `hermes` for
Anthropic, but the auth is currently missing.
If `hermes auth status anthropic` reports logged in but the Claude PONG check
still returns empty stdout, keep the same `native_cli` fallback and update
#2036 with the fresh evidence.

If Claude via Hermes still returns empty output after auth is repaired, debug:

```bash
hermes -z "Reply PONG." -m claude-opus-4-7 --provider anthropic
hermes -z "Reply PONG." -m claude-opus-4-7 2>&1 | head -200
HERMES_DEBUG=1 hermes -z "Reply PONG." -m claude-opus-4-7
```

Then check `~/.hermes/logs/`, try `claude-opus-4-6`, and try
`claude-sonnet-4-6` to separate an opus-4-7 issue from a provider issue.

## Smoke

Run the dispatch smoke only, not the full matrix:

```bash
.venv/bin/python scripts/audit/judge_calibration_matrix.py \
  --smoke \
  --out-dir audit/2026-05-17-judge-calibration-matrix-smoke/
```

## Per-family Runs

Run families serially after smoke passes:

```bash
.venv/bin/python scripts/audit/judge_calibration_matrix.py \
  --families xai \
  --harnesses hermes \
  --out-dir audit/2026-05-17-judge-calibration-matrix/
```

```bash
.venv/bin/python scripts/audit/judge_calibration_matrix.py \
  --families anthropic \
  --harnesses native_cli \
  --resume \
  --out-dir audit/2026-05-17-judge-calibration-matrix/
```

After #2036 is resolved, include Hermes for Anthropic:

```bash
.venv/bin/python scripts/audit/judge_calibration_matrix.py \
  --families anthropic \
  --harnesses native_cli,hermes \
  --resume \
  --out-dir audit/2026-05-17-judge-calibration-matrix/
```

```bash
.venv/bin/python scripts/audit/judge_calibration_matrix.py \
  --families openai \
  --harnesses native_cli,hermes \
  --resume \
  --out-dir audit/2026-05-17-judge-calibration-matrix/
```

```bash
.venv/bin/python scripts/audit/judge_calibration_matrix.py \
  --families google \
  --harnesses native_cli \
  --resume \
  --out-dir audit/2026-05-17-judge-calibration-matrix/
```

Gemini via Hermes is excluded because Google ToS forbids that route.

## Report

Regenerate the consolidated leaderboard from existing cell JSON:

```bash
.venv/bin/python scripts/audit/judge_calibration_matrix.py \
  --build-report-only \
  --out-dir audit/2026-05-17-judge-calibration-matrix/
```

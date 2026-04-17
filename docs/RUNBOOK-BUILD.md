# Build Pipeline Runbook

Quick reference for running builds without Claude. Copy-paste ready.

## Prerequisites

### 1. MCP Sources Server (optional but recommended)

```bash
# Start in a separate terminal — stays running
.venv/bin/python .mcp/servers/sources/server.py
# Verify: curl http://127.0.0.1:8766/health
```

Without MCP: builds work fine (Gemini gets VESUM data injected into prompts), but live dictionary/textbook lookups are unavailable during write/review.

### 2. Verify Plans Exist

```bash
# Check plans are valid
.venv/bin/python scripts/validate_plan_config.py a1
.venv/bin/python scripts/validate_plan_config.py a2
.venv/bin/python scripts/validate_plan_config.py b1
.venv/bin/python scripts/validate_plan_config.py b2
```

### 3. Verify Wikis Are Compiled

```bash
.venv/bin/python scripts/wiki/compile.py --status
```

Core levels (A1-C2) are 100% compiled. If any are missing:

```bash
# Compile missing wikis for a level
.venv/bin/python scripts/wiki/compile.py --track a2 --all
# Single article
.venv/bin/python scripts/wiki/compile.py --track a2 --slug genitive-intro
```

---

## Build Commands

### Single Module

```bash
# Module numbers are 1-indexed, matching order in curriculum.yaml
.venv/bin/python scripts/build/v6_build.py a1 1
```

### Batch (Range)

```bash
# A1: 55 modules (1-55)
.venv/bin/python scripts/build/v6_build.py a1 1 --range 55

# A2: 69 modules (1-69)
.venv/bin/python scripts/build/v6_build.py a2 1 --range 69

# B1: 94 modules (1-94)
.venv/bin/python scripts/build/v6_build.py b1 1 --range 94

# B2: 93 modules (1-93)
.venv/bin/python scripts/build/v6_build.py b2 1 --range 93
```

### Writer / Reviewer

```bash
# Default: gemini-tools writes, cross-agent reviews
.venv/bin/python scripts/build/v6_build.py a1 1 --range 55

# Explicit Gemini writes + Gemini reviews (current setup)
.venv/bin/python scripts/build/v6_build.py a1 1 --range 55 \
  --writer gemini-tools --reviewer gemini-tools
```

### Gemini Auth Mode

```bash
# Auto (default): preserve current environment behavior
.venv/bin/python scripts/build/v6_build.py a1 1 --writer gemini-tools

# Subscription / OAuth: strip GEMINI_API_KEY and GOOGLE_API_KEY for this run
GEMINI_AUTH_MODE=subscription \
  .venv/bin/python scripts/build/v6_build.py a1 1 --writer gemini-tools

# API key: preserve key env vars explicitly
GEMINI_AUTH_MODE=api \
  GEMINI_API_KEY=... \
  .venv/bin/python scripts/build/v6_build.py a1 1 --writer gemini-tools
```

`GEMINI_AUTH_MODE=subscription|api|auto` only affects Gemini CLI launches.
Claude and Codex paths ignore it.

### Resume (continue from where it stopped)

```bash
# Resume all incomplete modules in range — skips completed phases
.venv/bin/python scripts/build/v6_build.py a1 1 --range 55 --resume

# Resume from a specific step (e.g., after first pass stops at review)
.venv/bin/python scripts/build/v6_build.py a1 1 --range 55 --step publish --resume
```

### Specific Steps Only

```bash
# Run only audit+heal+publish for modules that stopped at stress/review
.venv/bin/python scripts/build/v6_build.py a1 1 --range 55 --step publish --resume

# Run only review pass
.venv/bin/python scripts/build/v6_build.py a1 1 --range 55 --step review --resume
```

---

## Important Flags

| Flag | What it does |
|------|-------------|
| `--resume` | Skip completed phases (reads state.json) |
| `--step publish --resume` | Audit → heal → publish only (cheapest resume) |
| `--step review --resume` | Re-review only |
| `--step all` | Full pipeline from scratch (**expensive, rarely needed**) |
| `--force-publish` | Publish even if audit fails (not recommended) |
| `--no-chunk` | Single-call generation instead of section-by-section |

---

## ⚠️ Do NOT

- **`--step all --resume`** — this re-runs write+review from inside the heal block, costing 15-20 min/module. Use `--step publish --resume` instead.
- Run without checking plans first — invalid plans = wasted compute.
- Kill a running build mid-write — the state.json tracks progress, so `--resume` can recover.

---

## Monitoring

While builds run, check progress:

```bash
# Quick status of all modules with state.json
for f in curriculum/l2-uk-en/a1/orchestration/*/state.json; do
  slug=$(basename $(dirname $f))
  phase=$(.venv/bin/python -c "
import json; d=json.load(open('$f'))
phases=d.get('phases',{})
done=[p for p,v in phases.items() if v.get('status')=='complete']
print(done[-1] if done else 'none')
  " 2>/dev/null)
  echo "$slug: $phase"
done
```

---

## Module Counts (from curriculum.yaml)

| Level | Modules | Plans | Wikis |
|-------|---------|-------|-------|
| A1 | 55 | 55 | 55 ✅ |
| A2 | 69 | 69 | 69 ✅ |
| B1 | 94 | 100 | 100 ✅ |
| B2 | 93 | 89 | 89 ✅ |

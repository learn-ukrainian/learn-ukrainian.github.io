# Testbed — Pipeline Regression Testing

The testbed maintains a fixed set of modules across difficulty levels and rebuilds/audits them to detect pipeline quality regressions.

## Quick Start

```bash
# Audit existing modules and compare vs baseline (no builds, no API calls)
.venv/bin/python tests/testbed/run_testbed.py check

# Full rebuild + audit + compare
.venv/bin/python tests/testbed/run_testbed.py full

# Audit only (no builds)
.venv/bin/python tests/testbed/run_testbed.py audit

# Save current results as the new baseline
.venv/bin/python tests/testbed/run_testbed.py baseline

# View latest results
.venv/bin/python tests/testbed/run_testbed.py report
```

## Commands

| Command | API calls? | What it does |
|---------|-----------|--------------|
| `check` | No | Audit existing content, compare vs baseline, exit 1 on regression |
| `audit` | No | Audit all modules, save results, print report |
| `build` | Yes (Gemini) | Build all modules via pipeline v5 |
| `full` | Yes (Gemini) | Build + audit + compare |
| `baseline` | No | Audit + save results as the new baseline |
| `report` | No | Print latest results vs baseline |

## Module Selection

Modules are configured in `tests/testbed/config.yaml`. The current set covers:

- **A1** (4 modules): phonology, gender, adjectives, first verbs, first case, imperatives
- **A2** (1 module): past tense + aspect pairs
- **B1** (1 module): full grammar + aspect mastery
- **B2** (2 modules): passive voice checkpoint, literary register
- **C1** (1 module): logical connectors (highest complexity)

Each module was chosen to test a specific constraint boundary or difficulty level.

## Grading

Modules receive A/B/C/F grades based on:

| Grade | Criteria |
|-------|----------|
| **A** | Audit passed, ≤1 fix attempt, words ≥ 110% target |
| **B** | Audit passed, ≤2 fix attempts |
| **C** | Audit passed, >2 fix attempts |
| **F** | Audit failed (any gate) |

## Regression Detection

The `check` command compares current audit results against `baseline.json`:
- Grade **improvement** (e.g., F → B): reported but not a failure
- Grade **regression** (e.g., A → B): causes exit code 1
- Same grade: no action

## CI Integration

Run as a pytest test (marked `slow`):

```bash
# Include in CI with explicit selection
.venv/bin/python -m pytest tests/test_testbed_check.py -v

# Or via the testbed runner directly
.venv/bin/python tests/testbed/run_testbed.py check
```

## Files

```
tests/testbed/
├── config.yaml          # Module list (frozen)
├── run_testbed.py       # Runner (build/audit/check/baseline/report)
├── core/
│   ├── baseline.json    # Golden baseline for regression checks
│   ├── grades.csv       # Historical grade log
│   ├── plans/           # Frozen plans for testbed modules
│   └── results/         # Per-run JSON results
└── seminar/
    ├── plans/
    └── results/
```

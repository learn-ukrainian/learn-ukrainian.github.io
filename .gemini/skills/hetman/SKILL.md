---
name: hetman
description: "Activity enrichment + review. Wrapper around build_module_v5.py --restart-from activities."
---

# Hetman: Activity Enrichment

> Thin wrapper around `build_module_v5.py`. All orchestration happens in Python.

## Usage

```
/hetman {track} {num}              # Enrich content-complete module
/hetman {track} {num} --full       # Full E2E pipeline (all phases)
```

## Execution

**Enrich mode** (default — requires existing content):

```bash
.venv/bin/python scripts/build_module_v5.py {track} {num} --restart-from activities
```

**Full mode** (`--full` flag):

```bash
.venv/bin/python scripts/build_module_v5.py {track} {num}
```

## What It Does (enrich mode)

- Activities + vocabulary generation
- Validation (morphological + Russicism detection)
- MDX regeneration
- Review (adversarial, Claude-side)

## Logs

Check `logs/build-{slug}-*.log` for full output.

---
name: hetman
description: "Activity enrichment + final review (Phases 3, 7). Thin wrapper around build_module.py --enrich."
---

# Hetman: Activity Enrichment

> Thin wrapper around `build_module.py`. All orchestration happens in Python.

## Usage

```
/hetman {track} {num}              # Enrich content-complete module
/hetman {track} {num} --full       # Full E2E pipeline (content + activities + review)
```

## Execution

**Enrich mode** (default — requires existing content):

```bash
.venv/bin/python scripts/build_module.py {track} {num} --enrich
```

**Full mode** (`--full` flag):

```bash
.venv/bin/python scripts/build_module.py {track} {num}
```

## What It Does (enrich mode)

- Phase 3: Activities + vocabulary generation
- Phase 4: Full audit + fix loop
- Phase 5: MDX regeneration
- Phase 7: Final adversarial review

## Logs

Check `logs/build-{slug}-*.log` for full output.

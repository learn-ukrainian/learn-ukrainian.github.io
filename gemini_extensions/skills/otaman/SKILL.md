---
name: otaman
description: "Content sprint — prose only (Phases 0-6b). Thin wrapper around build_module.py --content-only."
---

# Otaman: Content Sprint

> Thin wrapper around `build_module.py`. All orchestration happens in Python.

## Usage

```
/otaman {track} {num}
```

## Execution

Run this command and report the result:

```bash
.venv/bin/python scripts/build_module.py {track} {num} --content-only
```

## What It Does

- Phase 0: Research
- Phase 1: Meta/outline rebuild
- Phase 2: Section-by-section content generation
- Phase 4: Content-only audit + fix loop
- Phase 5: MDX generation
- Phase 6: Prose review
- Phase 6b: Apply review fixes

## After Completion

Run `/hetman {track} {num}` to add activities and final review.

## Logs

Check `logs/build-{slug}-*.log` for full output.

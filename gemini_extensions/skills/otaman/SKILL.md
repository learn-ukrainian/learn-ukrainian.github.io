---
name: otaman
description: "Content sprint — prose only. Wrapper around build_module_v5.py --restart-from content."
---

# Otaman: Content Sprint

> Thin wrapper around `build_module_v5.py`. All orchestration happens in Python.

## Usage

```
/otaman {track} {num}
```

## Execution

Run this command and report the result:

```bash
.venv/bin/python scripts/build_module_v5.py {track} {num} --restart-from content
```

## What It Does

- Research (if not cached)
- Discover (lexical sandbox seeding)
- Sandbox (VESUM-validated word bank)
- Content generation (section-by-section prose)
- Validation (morphological + Russicism detection)
- MDX generation

## After Completion

Run `/hetman {track} {num}` to add activities and final review.

## Logs

Check `logs/build-{slug}-*.log` for full output.

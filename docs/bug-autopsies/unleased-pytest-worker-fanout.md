# Bug Autopsy: ungoverned local pytest could start workers above the cap

**Date:** 2026-11-03

**Issue:** #11179

## Symptom

A normal local `pytest -n N` with N above the existing cap of 2 started those xdist workers.
The dispatch clamp never applied, because it runs only when `LEARN_UKRAINIAN_DISPATCH_TASK_ID`
is set. Nothing refused the run, and nothing required the test-slot governor.

## Root cause

`ci.pytest_dispatch_cap` is loaded for ordinary repository pytest, but both the worker clamp
and the early `--tx` rejection were gated on the dispatch marker. `_shrink_tx` also runs only
on that path, and only after `pytest_cmdline_main` yields, which is after xdist has already
built its worker list. The count a local run would start was never compared with
`MAX_PROCESSES`.

The holder marker is a separate check. On this tree `inherited_hold` already returns the
count only after `_live_holder` has matched it to the locked ticket's `held` record and to
the locked slot files. A stale, unlocked, malformed, or overclaimed marker is not a hold.
The fan-out bug was that "not a hold" still meant "start as many workers as asked".

## Prevention

Before xdist's command hook runs, a local controller with no live hold is refused when the
worker count xdist would start is above 2. The error names
`.venv/bin/python -m scripts.common.test_slots run -- .venv/bin/python -m pytest ...`.
A live hold still clamps to the slots it holds. A dispatch run is still clamped to 2, not
refused. Serial runs, `-n 0`, counts at or under 2, collection-only runs, and CI are unchanged.
`LU_TEST_SLOTS=off` disables acquisition and does not authorize a larger fan-out; the error
says so, because the governor command under `off` would otherwise refuse again.

The check uses `workerinput` to recognize a real xdist worker. An inherited
`PYTEST_XDIST_WORKER` on a new pytest does not exempt it.

## Limits

This is one run's ceiling, not a sum across sibling processes. It does not stop a true `CI`
value, `-p no:xdist`, `--noconftest`, or an `addopts` override that drops the plugin. A
same-user copy of a live marker is still the existing descendant contract. No new cap, lease,
environment variable, or pool policy was added.

## Links

- Issue: https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/11179
- Dispatch clamp that did not cover a local run: 755a6882e51a
- Holder record bound to locked slots: ed326e8d4f65

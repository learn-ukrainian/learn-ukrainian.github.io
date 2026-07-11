# Wiring the P4 strict-adoption gate surfaced two latent bugs

**Date:** 2026-07-12
**Issue:** #4998
**Category:** silent-cli-crash / shell-boolean-gotcha

## Symptom

Wiring `check_research_registry.py --strict-adoption` into a real controlled
path (PR #4998 review, item 12) surfaced two independent bugs that unit tests
alone never caught:

1. **Bare-script CLI invocation crashed.** `.venv/bin/python
   scripts/audit/check_research_registry.py --strict-adoption --json` raised
   `ImportError: cannot import name 'get_immersion_range' from partially
   initialized module 'config'` — but `.venv/bin/python -m
   scripts.audit.check_research_registry --strict-adoption --json` (same
   file, `-m` form) worked fine. The bare-script form is exactly how a human,
   a cron job, or the session-setup cold-start hook invokes it.
2. **A failing gate looked identical to a passing one in the cold-start
   hook.** Wiring the gate into
   `agents_extensions/shared/hooks/session-setup.sh` via `STRICT_OK=$(echo
   "$STRICT_JSON" | jq -r '.ok // empty')` never surfaced a failure, even
   with a fabricated `{"ok": false, ...}` fixture in the new
   `scripts/audit/test_session_setup_hook.sh` cases.

## Root cause

1. Adding `from scripts.audit import atlas_intake_registry` (to wire the real
   corpus resolver) forced Python to run `scripts/audit/__init__.py` for the
   first time from *inside* a file that itself lives in `scripts/audit/`.
   That `__init__.py` imports `scripts/audit/config.py`, which does a bare
   `from config import get_immersion_range` — resolved against
   `sys.path[0]`. When a script is invoked as `python
   scripts/audit/check_research_registry.py` (not `-m`), Python sets
   `sys.path[0]` to the script's **own directory** (`scripts/audit/`) — so
   the bare `import config` finds `scripts/audit/config.py` itself (same
   file, mid-import) instead of the intended `scripts/config.py`, and
   crashes on a circular partial import. This is a **pre-existing landmine**
   in `scripts/audit/config.py`'s import style; it had simply never been
   triggered because nothing under `scripts/audit/` previously imported the
   `scripts.audit` package from within a bare-script invocation of one of
   its own files.
2. jq's `//` alternative operator treats **both** `null` and `false` as the
   "nothing here" case it falls back from — `false // empty` evaluates to
   `empty`, not `false`. `.ok // empty` is the right idiom when you want
   "missing key → default", but it silently discards a real `false` value.

## Fix

1. Load `atlas_intake_registry.py` directly by file path via
   `importlib.util.spec_from_file_location` (registering the module in
   `sys.modules` *before* `exec_module`, since `dataclasses`' introspection
   needs `sys.modules[cls.__module__]` while the class body executes). This
   sidesteps `scripts/audit/__init__.py` entirely and works under both
   bare-script and `-m`/import invocation —
   `scripts/audit/check_research_registry.py::_load_atlas_intake_registry`.
2. Read `.ok` directly (`jq -r '.ok'`) and compare the string result to
   `"false"`; a missing key resolves to jq's literal `"null"` string, which
   never matches, so the check stays safe either way.

**Prevention:** (1) any new cross-import of the `scripts.audit` *package*
(not a submodule reached some other way) from a file that itself lives inside
`scripts/audit/` should be treated as suspect — test the bare-script
invocation (`python path/to/file.py ...`), not just `-m`/pytest-imported
usage, before shipping. (2) never use `KEY // empty` / `KEY // default` in jq
when `KEY` is a boolean you need to branch on `false` — only use that idiom
for optional strings/arrays/objects where `null`/absent are the only
"nothing" states. Both caught by actually running the bare-script CLI and the
hook test harness end-to-end (not just pytest-imported unit tests) before
merging.

## Links

- PR #4998 (corrective pass, commit c46382bd74142961dda719ff5a5b6ad6204fcf86)
- `scripts/audit/check_research_registry.py::_load_atlas_intake_registry`
- `agents_extensions/shared/hooks/session-setup.sh` (§11c)
- `scripts/audit/test_session_setup_hook.sh` (fixtures 9–10)

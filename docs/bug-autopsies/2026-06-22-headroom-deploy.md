# Headroom deploy: two failure modes took the proxy down mid-upgrade

**Date:** 2026-06-22
**Issue:** #3725
**Category:** deploy-tooling / pipx-uv-clobber + launchd-bootout
**Tool:** `scripts/deploy_headroom.sh`
**Impact:** Fleet-wide Headroom proxy (`127.0.0.1:8787`) left **down** after a failed
0.26.0 → 0.27.0 upgrade. The deploy script stopped the proxy (step 2), then aborted at
the pipx upgrade (step 3), never reaching start/verify (steps 5–6).

## Symptom

```
== 3/6  Upgrade headroom-ai[proxy] -> 0.27.0 ==
Installing to existing venv 'headroom-ai'
error: Failed to create virtual environment
  Caused by: A virtual environment already exists at `.../pipx/venvs/headroom-ai`. Use `--clear` to replace it
⚠️  Not removing existing venv ... because it was not created in this session
'/opt/homebrew/bin/uv venv --python /opt/homebrew/opt/python@3.14/libexec/bin/python --quiet ...' failed
```

## Root cause

Two independent root causes, either of which alone leaves the proxy down:

### 1. `pipx install --force` + uv backend + Python major.minor drift

- The existing venv was built on **Python 3.13.13** (`pyvenv.cfg: home = .../python@3.13/bin`).
- Homebrew had since set `PIPX_DEFAULT_PYTHON=/opt/homebrew/opt/python@3.14/libexec/bin/python`.
- `pipx install --force` **recreates** the venv. Because the target interpreter (3.14)
  differed from the venv's (3.13), pipx asked uv to build a fresh venv over the existing dir.
- **uv 0.11.14 refuses to clobber a venv it did not create in-session** ("Not removing
  existing venv ... Use `--clear`"). So `--force` aborts — but only when the interpreter
  drifts. It worked for months while pipx's default stayed on 3.13.

The trigger is environmental (a Homebrew update flips the default Python), so it is latent
until the day it isn't, and it recurs on every machine as Python advances.

### 2. `headroom install stop` boots the job out; `start` only kickstarts

- Step 2 (`headroom install stop`) does `launchctl bootout` — the launchd job leaves the
  GUI domain entirely.
- Step 5 (`headroom install start`) uses `launchctl kickstart -k gui/<uid>/com.headroom.<profile>`,
  which **only works on an already-loaded job**. After a bootout it fails:
  `Could not find service "com.headroom.default" in domain for user gui: 501` (exit 113).
- This stop/start asymmetry means **every** stop→start cycle in 0.27.0 is broken, masked here
  only because cause #1 aborted before step 5 ran.

`headroom install apply` would re-bootstrap, but it **regenerates `manifest.json`** and would
drop the codex-applied proxy tuning (`concurrency=3`, `--disable-kompress`, `min_tokens=5000`,
`max_items=25`). The correct recovery is to re-bootstrap the **existing** plist
(`launchctl bootstrap gui/<uid> <plist>`), which preserves the manifest; `RunAtLoad=true`
starts it.

## Manual recovery performed

```bash
pipx uninstall headroom-ai
pipx install --python /opt/homebrew/opt/python@3.13/libexec/bin/python "headroom-ai[proxy]==0.27.0"
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.headroom.default.plist
curl -s http://127.0.0.1:8787/health   # -> version 0.27.0, status healthy, memory disabled (intended)
```

## Prevention

Landed in `scripts/deploy_headroom.sh` (#3725):

- **Step 3:** replaced `pipx install --force` with **uninstall-then-install**. Removing the
  venv dir first sidesteps the uv clobber guard entirely. The install is **pinned to the
  interpreter the venv already runs** (derived from `pyvenv.cfg` `home` + `version_info`),
  so a package upgrade never silently jumps Python major.minor; override via
  `HEADROOM_PYTHON=/path/to/python`.
- **Step 5:** if `headroom install start` fails (job booted out), the script now
  **re-bootstraps the existing plist** (preserving `manifest.json`), falling back to
  `headroom install restart`, and only then `die`s. It deliberately does **not** fall back to
  `apply` (would clobber tuning).

## Lessons

- `pipx install --force` is not idempotent across interpreter drift when uv is the backend.
  For a managed tool, prefer **uninstall + pinned install** and pin the interpreter explicitly.
- A `stop` that `bootout`s + a `start` that `kickstart`s is not a symmetric pair. After a stop,
  the job must be **bootstrapped**, not kickstarted.
- The service's real config lives in `~/.headroom/deploy/<profile>/manifest.json`, not in CLI
  flags. Recovery that regenerates the manifest silently drops hand-applied tuning — re-bootstrap
  the existing plist instead.

## Links

- PR #3725 — `fix(infra): harden deploy_headroom.sh against pipx/uv clobber + launchd bootout`;
  fix shipped in commit `04adadde6d`.
- Precursor PR #3721 (commit `0e6f397f9f`) — added `scripts/deploy_headroom.sh`.

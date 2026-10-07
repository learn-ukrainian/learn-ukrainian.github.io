---
name: verify-learn-ukrainian
description: "Drive the learn-ukrainian Astro learner site and reuse local CI Gate / data-contract checks to prove behavior. Use when verifying lessons, Atlas word cards, practice pages, site build, or local CI Gate equivalents."
---

# Verify learn-ukrainian

Project-local verification for the public learner site (`site/`, Astro) plus the CI Gate and data-contract commands developers already run. Read cold: launch an isolated preview, doctor it, drive a mapped feature with Playwright (existing `site/e2e` specs), capture evidence, clean up. Do not invent new product checks — call the repo's make/npm/pytest/scripts targets.

**Public-repo rule:** never write host paths, hostnames, IPs, internal topology, or secret values into evidence filenames, commits, or PR text. Evidence under `.cursor/skills/verify-learn-ukrainian/artifacts/` is gitignored except `.gitkeep`.

## Launch

Isolated preview (preferred for proof):

```bash
# Node 22.x required (site package engines + undici). Prefer nvm use 22 when available.
bash .cursor/skills/verify-learn-ukrainian/bin/launch.sh preview
source "$LU_VERIFY_STATE_DIR/env.sh"   # set LU_VERIFY_STATE_DIR to the exact path launch.sh printed
```

- Default build mode is `LU_VERIFY_BUILD_MODE=shell` → `npm run build:shell` in `site/` (committed Atlas artifacts + Astro). Set `LU_VERIFY_BUILD_MODE=full` for `npm run build` (hydrate from the public GitHub Release atlas-manifest asset, then Astro).
- Ready when `http://$LU_VERIFY_HOST:$LU_VERIFY_PORT/` answers (defaults: host `localhost`, port `4321`, same as `site/playwright.config.ts`).
- Launch refuses to start if that port already answers and is not this run's PID file — do not double-drive a shared instance.
- Dev alternative: `bash .cursor/skills/verify-learn-ukrainian/bin/launch.sh dev` (`npm run dev` in `site/`).
- Teardown: `bash .cursor/skills/verify-learn-ukrainian/bin/cleanup.sh` (after `source` of the run's `env.sh`).
- Scratch state defaults to `${TMPDIR:-/tmp}/lu-verify-<run-id>`. Custom `LU_VERIFY_STATE_DIR` must be a directory named `lu-verify-<run-id>` directly under that temporary root; cleanup rejects broad paths, traversal outside the root, and symlink directories.

Prerequisites outside Launch (once per machine):

```bash
# Python project env (primary checkout setup only; never create a worktree venv)
uv venv .venv --python 3.12
uv pip install --python .venv/bin/python -r requirements-lock.txt
# If you install from requirements.txt, pin ruff to the lockfile version before checks:
#   uv pip install --python .venv/bin/python 'ruff==0.15.21'
(cd site && npm ci)
```

In a dispatch worktree, set `LU_VERIFY_PYTHON` to the task-prescribed shared project interpreter before doctor or run-checks. Both default to the checkout's `.venv/bin/python` otherwise; the sense-lint child shell uses the same selected interpreter.

## Doctor

```bash
source "$LU_VERIFY_STATE_DIR/env.sh"   # from launch
bash .cursor/skills/verify-learn-ukrainian/bin/doctor.sh
```

Doctor checks: project `.venv` present, Node 22.x on PATH, site HTTP up, `/a1/`, `/lexicon/`, `/practice/` return 200, optional PID ownership of the port, optional `LU_VERIFY_EXPECTED_REV` matches `git rev-parse HEAD`. Run doctor before the first drive and after any failed drive.

## Drive

Feature recipes live in `features/`. Prefer stable routes and the existing Playwright specs over ad-hoc clicks.

```bash
source "$LU_VERIFY_STATE_DIR/env.sh"
# Green path on current main: HTTP route smoke + practice Playwright
bash .cursor/skills/verify-learn-ukrainian/bin/drive-routes.sh
bash .cursor/skills/verify-learn-ukrainian/bin/drive-playwright.sh practice
# Optional: atlas | lessons | all — see feature gotchas (some specs drift vs arc /a1/)
```

Harnesses:

| Feature | How to drive |
| --- | --- |
| A1 lessons (arc) | `bin/drive-routes.sh` — `/a1/`, module landings |
| A1 upgrade sidebar (legacy) | `bin/drive-playwright.sh lessons` → `e2e/a1-lesson-nav.spec.ts` (often red vs arc landing) |
| Atlas word cards | `e2e/atlas-practice.spec.ts` browse/lemma tests + `/lexicon/` routes |
| Practice | `drive-playwright.sh practice` — cloze + matching greps (green path) |

Stable handles: `[data-index-search]`, `.atlas-index-item`, `button[data-mode="cloze"]`, `[data-testid="practice-matching"]`, `[data-testid="practice-secondary-tools"]`, arc module hrefs under `/a1/<slug>/`.

## Evidence

- Directory: `$LU_VERIFY_EVIDENCE_DIR` (set by launch; under `.cursor/skills/verify-learn-ukrainian/artifacts/<run-id>/`).
- Playwright: `playwright-<feature>.log` plus copied `test-results/` on failure.
- Data/CI checks: stdout from `bin/run-checks.sh` (redirect into the evidence dir when proving).
- Proof standards: exercise real learner routes (not internal setters); capture action + resulting state (spec assertions + log); side effects for data checks are exit codes and lock/manifest equality, not UI alone.
- Cleanup must leave evidence in place — confirm the evidence path still exists after `cleanup.sh`.

## Cleanup

```bash
source "$LU_VERIFY_STATE_DIR/env.sh"
bash .cursor/skills/verify-learn-ukrainian/bin/cleanup.sh
test -d "$LU_VERIFY_EVIDENCE_DIR"   # must still exist
```

Kills only the PID recorded by launch (and its process group). Removes the scratch state dir. Never deletes evidence. Never `pkill` by process name.

## Helpers

All under `.cursor/skills/verify-learn-ukrainian/bin/` (executable):

| Script | Invocation |
| --- | --- |
| `launch.sh` | `bash .cursor/skills/verify-learn-ukrainian/bin/launch.sh preview` |
| `doctor.sh` | `bash .cursor/skills/verify-learn-ukrainian/bin/doctor.sh` |
| `drive-routes.sh` | `bash .cursor/skills/verify-learn-ukrainian/bin/drive-routes.sh` |
| `drive-playwright.sh` | `bash .cursor/skills/verify-learn-ukrainian/bin/drive-playwright.sh practice` |
| `run-checks.sh` | `bash .cursor/skills/verify-learn-ukrainian/bin/run-checks.sh` |
| `cleanup.sh` | `bash .cursor/skills/verify-learn-ukrainian/bin/cleanup.sh` |

### Local CI Gate commands (`run-checks.sh`)

These mirror what CI Gate runs locally — they are not a full 16-shard pytest matrix:

- `bash scripts/ci/checks.sh` — Ruff + content contracts (see `docs/runbooks/ci-gate.md`)
- `npm run build` / `npm run build:shell` + `npm test` in `site/` — Frontend job pieces (build via launch; unit tests: `(cd site && npm run test:unit && npm run test:built-output)` when proving frontend)
- Targeted pytest: `tests/validate/test_permissions_register.py`
- `.venv/bin/python -m scripts.atlas.word_card_foundation verify --manifest registry/atlas/pilot/pilot-v1.json --registry registry/atlas/identity/registry.json`
- `.venv/bin/python -m scripts.curriculum.evidence lessons-lock a1 sounds-letters-and-hello`
- `.venv/bin/python scripts/lexicon/check_manifest_freshness.py`

### Skip policy (never fail the suite for missing private env)

`run-checks.sh` prints `SKIP` with a reason and continues when:

| Check | Skip when |
| --- | --- |
| Evidence pack-verify | Sources MCP / sources service on the local monitor port is down |
| Practice linguistic gate | `data/vesum.db` absent |
| Curated-seed make targets | Private curated seed input absent |
| Word-card verify | Input/DB refuse that names missing private files |
| Lesson lock | Committed lock missing, or stderr reports unavailable sources/artifacts |
| `checks.sh` | `origin/main` not fetched |

Skips are successful for env gaps. Only an executed check that returns non-zero without an env-gap signal is `FAIL`.

## Feature map

See [`features/README.md`](features/README.md). Keep the map honest with `/maintain-verification-skill` as the site changes.

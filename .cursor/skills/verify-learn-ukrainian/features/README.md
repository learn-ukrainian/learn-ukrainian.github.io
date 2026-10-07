# learn-ukrainian verification map

This directory is the maintained source for verifying learner-facing behavior of the Astro site and the data contracts that gate those surfaces. Read this index before driving the app, then use the matching feature file as the recipe.

## Baseline preconditions

- Project `.venv` exists and is used for every Python command (never bare `python` / `python3`).
- Node 22.x is on `PATH` (`nvm use 22` when available).
- Site deps installed: `(cd site && npm ci)`.
- Launch an isolated preview with `bash .cursor/skills/verify-learn-ukrainian/bin/launch.sh preview`, then `source` the printed `env.sh`.
- Run `bash .cursor/skills/verify-learn-ukrainian/bin/doctor.sh` and require OK before the first drive.
- Never drive an instance that was not started by this verification run.
- Data-contract recipes do not need the preview server; CI Gate checks do not need it either.

## Driving conventions

- Start every UI recipe from a healthy doctor'd preview unless the feature file says otherwise.
- Prefer the existing Playwright specs and their selectors (`data-testid`, `data-mode`, `.lu-sidebar-*`, `[data-index-search]`) over coordinates.
- Treat every command as literal. Keep quoted names and flags unchanged.
- Run HTTP learner-route smokes through `bin/drive-routes.sh`.
- Run browser drives through `bin/drive-playwright.sh` (prefer `practice` as the green mapped feature on current main).
- Run data/CI checks through `bin/run-checks.sh` (or the underlying make/npm/pytest commands it wraps).
- Cleanup removes only the launched process and scratch state — never evidence under `$LU_VERIFY_EVIDENCE_DIR`.

## Proof and skip reporting

- Capture the user action and the resulting state (Playwright log + assertions), not only a final screenshot.
- Data-check proof is exit code `0` plus the command's OK line (lock identical, register schema valid, pin verify JSON).
- Record the feature ID and entry point with every artifact.
- Report an unreachable path with the unmet precondition (`SKIP` reason from `run-checks.sh`).
- Do not report a skipped private-env check as verified through a different path.

## Feature entry contract

Each feature file starts with an H1 title and one paragraph describing the user-visible behavior. It then uses exactly four H2 sections in this order.

1. `Sub-features` lists short IDs with one line for each behavior.
2. `How to get to it (user POV)` lists every user entry point.
3. `Driving it with <harness>` starts with `Preconditions:` and uses labeled bullets that pair each user action with an exact command and observable result.
4. `Gotchas` lists traps that can waste or invalidate a verification run.

## Features

- [A1 lessons](./lessons.md) — level landing, module landing, lesson pages, sidebar and prev/next.
- [Atlas word cards](./atlas-word-cards.md) — lexicon landing, browse, lemma word-card pages.
- [Practice](./practice.md) — `/practice/` modes, cloze/matching/flashcards, secondary tools fold.
- [Readings](./readings.md) — `/readings/` library, genre cards, one published text.
- [Site build](./site-build.md) — production shell/full build and preview readiness.
- [Data contracts & local CI Gate](./data-contracts.md) — lesson lock freshness, Atlas register pins/manifests, licence register, `checks.sh`.

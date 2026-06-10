# Dispatch brief — unify ALL track landings on the LevelLanding pattern (A2 is the reference)

## Problem (verified)
`a2/index.mdx` renders the correct landing design **through `LevelLanding`** (contained hero card + stat
row + numbered module list with play buttons, both light/dark). But **`a1/index.mdx` and `folk/index.mdx`
render an OLD layout** (full-width CourseLayout hero + a two-card "CORE LADDER" block) even though they
import `LevelLanding` — they were never migrated. Result: landings drift per track. **A2 is the reference
for "correct."**

## Scope — migrate every TRACK landing to the A2/LevelLanding pattern
1. **Enumerate** every track landing: `starlight/src/content/docs/{a1,a2,b1,b2,c1,c2,folk,hist,lit,istorio,oes,ruth,...}/index.mdx` (and any `pages/{track}/index.astro`). List which already render via `LevelLanding` like A2 vs which use old markup.
2. **Migrate the non-conforming ones** (a1, folk, and any others) to render through `LevelLanding` EXACTLY as `a2/index.mdx` does — contained hero card, stat row (module count + word target), numbered module list. Remove the old two-card / full-width-hero landing markup. Drive each from its existing per-track module data (e.g. a1 already imports `A1_UNITS`).
3. **Pass the full prop contract** every track: `title, subtitle, level, color (--lu-id-<track>), moduleCount, wordTarget, modules, progressTitle, progressDescription` (a1/folk currently omit `progressTitle`/`progressDescription`).
4. **Both modes** — the landing must be legible in light AND dark (use the merged `--lu-*` tokens; identity color from `--lu-id-<track>`). **Do NOT** force the lexicon page (`pages/lexicon/index.astro`) into this — it correctly follows the Word Atlas POC, leave it.

## Conformance gate (the anti-laziness teeth)
Add `tests/test_landings_use_levellanding.py`: for every `{track}/index.mdx` that exists, assert it renders via `LevelLanding` and passes the required props (no track left on the old layout). This is what stops regression.

## #M-4 verification (screenshots are MANDATORY — one per track)
- **A screenshot of EVERY migrated track landing in BOTH light and dark** (a1, folk, …), each showing the LevelLanding hero card + module list — proving none was skipped. (You cited "LLMs are lazy" — prove every track, not just one.)
- `npm run build:full --prefix starlight` final line raw (green); `npm test --prefix starlight` + `.venv/bin/python -m pytest tests/test_landings_use_levellanding.py -q` final lines raw.

## Numbered steps
1. Confirm `pwd` is the dispatch worktree (base origin/main).
2. Enumerate landings; identify non-conforming.
3. Migrate each to the A2/LevelLanding pattern (both modes, full props).
4. Add the conformance test.
5. Verify (per-track both-mode screenshots, build, tests).
6. Commit (conventional + `X-Agent` trailer): `fix(landings): unify all track landings on LevelLanding (A2 reference), both modes + conformance test`.
7. `git push -u origin <branch>`; `gh pr create` with the per-track screenshots. **DO NOT merge** — review.

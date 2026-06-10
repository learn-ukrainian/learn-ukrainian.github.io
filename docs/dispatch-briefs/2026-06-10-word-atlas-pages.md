# Dispatch brief — Word Atlas pages: implement against dual-mode tokens (3 views, landing, Ukrainian, filter) + activity token refactor

**Authorities (now on `main` — read them):**
- `docs/best-practices/dual-mode-design-tokens.md` — the semantic + section-identity tokens (already defined in `starlight/src/css/custom.css` for light + dark).
- `docs/poc/poc-word-atlas-design.html` — the **dual-mode mockup** (3 views, both themes) — this is the visual spec.

This is the **pages** step: make the **live** Word Atlas render the POC, in **both** modes, consuming the merged `--lu-*` tokens. No hardcoded hex/rgba in the pages you touch — use the tokens.

## Scope
1. **Landing** — `starlight/src/pages/lexicon/index.astro`: align to the POC landing view; **fully Ukrainian UI** (`Фільтр`/`Шукати`, Ukrainian badge + subtitle — not "Word Atlas"/"Filter"/"Course vocabulary…"); the filter button uses `--lu-on-accent` on `--lu-accent` (dark text on yellow, both modes); both themes legible.
2. **Detail** — `starlight/src/pages/lexicon/[lemma].astro`: align to the POC detail view; consume `--lu-*` tokens (surfaces/text/border + `--lu-id-lexicon` identity); Ukrainian section labels; both themes.
3. **3rd view** — the POC has **3 views**; the live site has only landing + detail. Identify the missing third (e.g. a category/grid/index view) from the POC and implement it.
4. **Activity token refactor** — refactor `starlight/src/components/Activities.module.css` state tints to the `--lu-state-*` / `--lu-match-right` tokens, **replacing** the `[data-theme='dark']` block added in #2900 with token references (same values, single source). Activities must still render correctly in both modes (regression-check MatchUp/Quiz/TrueFalse).

## #M-4 verification (final report = command + cwd + raw output, + screenshots)
- Playwright/both-mode screenshots of **landing + detail + 3rd view** in light AND dark; sample contrast ≥ WCAG AA (4.5:1); filter button readable in both.
- `grep` shows the touched pages use `--lu-*` tokens (no raw hex in the lexicon pages).
- `npm run build:full --prefix starlight` final line raw (green); `npm test --prefix starlight` final line raw (green).
- Activities regression: load an A1 module's activities in dark — MatchUp/Quiz still legible.

## Numbered steps
1. Confirm `pwd` is the dispatch worktree (base = origin/main, has the tokens + POC).
2. Implement landing (Ukrainian, filter, both modes) → detail → 3rd view, all token-backed.
3. Refactor `Activities.module.css` onto `--lu-state-*` tokens.
4. Run the #M-4 verification (both-mode screenshots, build, tests, activity regression).
5. Commit (conventional + `X-Agent` trailer): `feat(lexicon): Word Atlas pages on dual-mode tokens — 3 views, Ukrainian UI, filter fix; activities → state tokens`.
6. `git push -u origin <branch>`; `gh pr create` with the both-mode screenshots. **DO NOT merge** — goes to review.

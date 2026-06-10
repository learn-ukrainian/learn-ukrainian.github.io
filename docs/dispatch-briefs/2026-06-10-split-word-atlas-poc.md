# Dispatch brief — split the multi-view Word Atlas POC into one-design-per-HTML

## Why
`docs/poc/poc-word-atlas-design.html` packs **3 views** (landing / lemma-detail / 3rd view) into one
file. When a dispatch implements "the Word Atlas" from a 3-in-1 mockup, partial application is the
failure mode (the lazy path implements one view, skips the rest). One-design-per-HTML + an explicit
design→route map removes that ambiguity. (Single-view POCs — lesson, folk-lesson, lit, site — are
already fine; do NOT split those.)

## Scope
1. Split `docs/poc/poc-word-atlas-design.html` into 3 files, each a **standalone dual-mode** mockup
   (light + dark frame, using the `--lu-*` tokens already in `custom.css`):
   - `docs/poc/word-atlas/landing.html` → route `/lexicon/`
   - `docs/poc/word-atlas/detail.html` → route `/lexicon/{lemma}`
   - `docs/poc/word-atlas/<3rd-view>.html` → its route (name it from the actual 3rd view)
2. Preserve every view's content exactly — this is a mechanical split, not a redesign. Keep the
   shared CSS (extract to a sibling `word-atlas.css` the 3 files share, or inline per file — your call,
   but no visual change).
3. Add `docs/poc/word-atlas/README.md` — the **design→route map** (which html drives which route) +
   a note that each file is the single source for that one page.
4. Replace the old `poc-word-atlas-design.html` with a short stub pointing at the new directory (keep
   the path alive for existing links), OR `git mv` and update references — grep for `poc-word-atlas-design`
   and fix any references (docs/best-practices/*, dispatch briefs).

## #M-4 verification
- Open each of the 3 split files in a browser (or render) in BOTH themes — screenshot proof they match
  the original views, nothing dropped.
- `grep -rl poc-word-atlas-design docs/ | wc -l` → show remaining references are updated/intentional.

## Numbered steps
1. Confirm `pwd` is the dispatch worktree.
2. Split into the 3 dual-mode files + README design→route map.
3. Fix references to the old path.
4. Verify (both-theme screenshots of each of the 3, references grep).
5. Commit (conventional + `X-Agent` trailer): `refactor(poc): split Word Atlas design into one-html-per-view + design→route map`.
6. `git push -u origin <branch>`; `gh pr create`. **DO NOT merge** — review.

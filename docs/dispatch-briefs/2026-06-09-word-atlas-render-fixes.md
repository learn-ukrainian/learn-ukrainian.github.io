# Dispatch brief — Word Atlas + A1 render bug fixes (LIVE site)

The site is live at learn-ukrainian.github.io. Three render bugs, all mechanical.
Fix at the right layer, add tests, **no auto-merge** — the orchestrator reviews + redeploys.

## #M-4 verifiable-claims preamble
Every claim in your final report MUST be tool-backed (command + cwd + raw output). Quote raw, never "I checked":
- "manifest regenerated" → the regen command + `git diff --stat` raw.
- "gloss cleaned" → `python3 -c "import json; …print 11 flagged glosses"` raw, showing no internal tags.
- ":::info renders" → astro build line + a `grep ':::info' dist/a1/weather/index.html` returning **0** (proves it's processed, not raw).
- "tests pass" → `pytest` / `vitest` final line raw. "build green" → astro build final line raw.

## The three bugs (root causes already traced)

### Bug 1 — gloss carries internal classification (11 entries)
`starlight/src/data/lexicon-manifest.json` → `entries[].gloss` includes authoring tags after the `—`:
`"how are you — chunk"`, `"hi, informal — chunk"`, `"teacher, f — feminitive, VESUM-verified; mirror of вчитель / учитель m"`, `"Good morning — chunk, unstressed \`[о]\` stays clean"`, etc.
- Trace where the gloss is set (the manifest generator — likely `scripts/lexicon/enrich_manifest.py` or the vocab source it reads).
- Fix at the **generation layer**: produce a clean user-facing `gloss` (the translation only) by stripping a defined, maintainable set of internal-classification suffixes (`chunk`, `feminitive`, `VESUM-verified`, `mirror of …`, parenthetical stress/phonetic notes). Preserve the raw string in a separate field (e.g. `gloss_internal`) if any consumer needs it — do NOT silently drop data.
- Regenerate `lexicon-manifest.json`. Verify all 11 flagged lemmas now show a clean gloss.

### Bug 2 — HTML entities in enrichment text
Some `enrichment` text has `&amp;`, `&lt;` (e.g. lemmas `звук`, `книга`). Decode HTML entities at the generation layer so the rendered card shows `&`/`<`, not the entity. Audit the manifest for any other entity escapes.

### Bug 3 — `:::info` admonitions render raw in LIVE A1 lessons (migration regression)
Starlight processed `:::info` / `:::note` / `:::tip` / `:::caution` directives into styled boxes. The site dropped Starlight, so the Astro/MDX pipeline no longer handles `:::` → they render as raw text in published A1 lessons (`weather`, `how-many`, `my-day`, `reading-ukrainian`, `what-is-it-like`, `this-and-that`, `linking-ideas`, + folk/b1).
- Fix at the **pipeline/presentation layer** (parity-safe, NO per-MDX edits): add `remark-directive` + a small remark/rehype handler in the Astro config that maps `:::type` container directives to styled `<aside class="admonition admonition-{type}">` with a title, plus CSS. Restores admonition rendering site-wide.
- Verify: `grep -rl ':::info' starlight/src/content/docs/` lists the files; after build, `grep ':::info' dist/a1/weather/index.html` returns **0** and the built HTML contains the rendered `<aside>`.

## Numbered steps
1. Confirm `pwd` is the dispatch worktree (not main).
2. Bug 1: trace + fix the gloss generator; regenerate the manifest; verify 11 lemmas.
3. Bug 2: decode HTML entities at generation; regenerate; verify.
4. Bug 3: add remark-directive handling + CSS in Astro config; verify build + grep.
5. Tests: a generator test asserting glosses carry no internal tags + entities decoded; a vitest/DOM test (or build-grep assertion) that `:::info` renders an `<aside>`, not raw text.
6. `.venv/bin/ruff check <changed .py>`; `npm run build:full --prefix starlight` (must be green); run the relevant pytest + `npm test --prefix starlight`.
7. Commit (conventional + `X-Agent` trailer): `fix(lexicon,ui): clean Word Atlas glosses + decode entities + render ::: admonitions (live bugs)`.
8. `git push -u origin <branch>`; `gh pr create` describing the 3 root causes + fixes. **NO merge.**

## Out of scope (orchestrator handles separately)
- The 36,177 OCR-garbage etymology pages (`etymology-manifest.json`, `/etymology/[slug]`) — a data-quality/product decision (gate the routes off vs re-OCR), NOT part of this PR. Do not touch the etymology manifest or routes.

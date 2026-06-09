# Dispatch brief — A1 lesson POC redesign: framework + 1 reference module (LOCAL ONLY)

This is the **B-pilot, Step A**: build the POC lesson component framework and convert ONE
reference module to it, so the design can be verified locally before any writer-prompt change or
rollout. **DO NOT deploy. DO NOT change the V7 writer prompt. DO NOT touch other A1 modules' content.**

## Design spec (READ FIRST — it is the authority)
`docs/poc/poc-lesson-design.html` — open it; it has the complete CSS + exact component markup for
the core lesson (`#module-core`). Match its look. Core identity = **blue (#0057B8) + yellow (#FFD700)**.
Also read `docs/best-practices/v7-design-and-corpus.md` §1.2 (4-tab shape) so you don't break the contract.

## #M-4 verification (final report = command + cwd + raw output)
- "renders like POC" → `npm run build:full --prefix starlight` final line raw + a screenshot path or
  `grep -c 'class="dialogue"\|class="rule-box"\|class="exercise-badge"' dist/a1/things-have-gender/index.html` raw (>0).
- "other modules unbroken" → build green (38K pages) + load `/a1/weather/` still renders (admonitions intact).
- "tests pass" → vitest final line raw.

## What to build

### 1. Prose components (presentational `.astro`, no React needed)
Create components matching the POC markup/CSS:
- `Dialogue` → `.dialogue` (`.dialogue-title`, `.dialogue-line` with `.speaker` + UK + `.trans`)
- `RuleBox` → `.rule-box` (`.rule-box-header` + icon + table; gender spans `.gender-m`/`.gender-f`/`.gender-n`)
- `ObserveBox` → `.exercise` + `.observe-box` (`.observe-pairs`, `.observe-question`)
- `MythBox`, `SourceBox` (for seminar parity — build them; not used by this A1 module)
Make them usable in MDX the SAME way the existing islands (VocabCard, Quiz…) are made available
(find that registration; register the new components alongside).

### 2. POC CSS → `starlight/src/css/custom.css` (ADDITIVE — must not break plain-markdown modules)
Port the POC's design system + component CSS: dialogue, rule-box + gender colors, the `.exercise`
wrapper + `.exercise-badge` palette (all 30 badge types), and the per-activity styles
(quiz/matchup/fillin/truefalse/etc.) so the EXISTING activity islands get the POC card frame.
Scope under the lesson content area so other surfaces (lexicon, home) are unaffected.

### 3. Lesson header (the styled `.header.core`)
The POC has a blue/yellow header with a `.level-badge` ("A1 Module 08"), UK `<h1>`, English `.subtitle`.
Apply it to the A1 lesson page chrome (lesson layout / `[...slug].astro` hero region) WITHOUT breaking
folk/lexicon layouts — gate by track/core.

### 4. Frame the existing activity islands
Wrap the existing activity components (Quiz, FillIn, MatchUp, TrueFalse, Order, …) in the POC's
`.exercise` card + a type `.exercise-badge`. Prefer a small wrapper component or a CSS rule keyed on
the island container — do NOT rewrite the island internals.

### 5. Convert the ONE reference module
`starlight/src/content/docs/a1/things-have-gender.mdx` (title "Речі мають рід" = the POC's example):
- **Урок tab**: restructure the EXISTING prose into `<Dialogue>`, `<RuleBox>` (the gender table — м blue / ж pink / с green), and `<ObserveBox>` where the content fits — using the module's REAL content (do not invent or change meaning; just move it into the components).
- **Словник / Зошит / Ресурси**: keep content; they inherit the new CSS (FlashcardDeck/VocabCard, activity cards, admonition Resources).
- This is a hand-conversion of ONE module ONLY. Leave the other 54 modules' MDX untouched.

## Numbered steps
1. Confirm `pwd` is the dispatch worktree.
2. Build prose components + register them for MDX.
3. Port POC CSS into custom.css (additive, scoped).
4. Style lesson header (core gated).
5. Frame activity islands as exercise cards.
6. Convert `things-have-gender.mdx` Урок to the components (real content).
7. `npm run build:full --prefix starlight` (green) + verify `/a1/things-have-gender/` has dialogue/rule-box/exercise markup AND `/a1/weather/` still renders (no regression) + `npm test --prefix starlight`.
8. Commit (conventional + `X-Agent` trailer): `feat(ui): A1 POC lesson framework + things-have-gender reference module [B-pilot, local-only]`.
9. `git push -u origin <branch>`; `gh pr create` — body: what was built, how to review locally (`/a1/things-have-gender/`), screenshots/grep proof. **DO NOT merge. DO NOT deploy.**

## Hard constraints
- Local only. No Pages deploy. No writer-prompt edit. No other-module content edits.
- Additive CSS — the 54 not-yet-converted modules must still render fine (plain markdown).
- This is a design-fidelity pilot for human review; the writer-prompt automation is a SEPARATE later step.

# K3 Practice Redesign — Build Specification

Status: implementation specification for the owner-accepted K3 design

Design baseline: r7.1 content from `K3-final-merge` plus r8 layout from
`K3-layout-r8`

Design authority: frozen; implementation must not reinterpret the mockups

## 1. Delivery contract

This specification converts the accepted mockups into ordered engineering work
on the real practice site. The r7.1 content and r8 layout are normative. A PR may
ship only the subset assigned to its chunk; it must not substitute different
copy, interaction rules, layout, icons, colors, or content.

The following requirements are non-negotiable across all chunks:

- The setup dashboard is a two-column grid at widths of `1000px` and above.
  Its exact desktop row map is:

  ```css
  grid-template-rows: auto auto auto 1fr auto;
  grid-template-areas:
    "hero words"
    "stats words"
    "session words"
    ". words"
    "focus modes";
  ```

  The `"."` filler row is deliberate and must remain.
- At widths below `1000px`, the single DOM order is hero, stats, session CTA,
  words, focus, modes. CSS reflow must not produce a conflicting keyboard order.
- The primary start/resume CTA is visible without scrolling at `1366x768` in
  both Ukrainian and English chrome. Section 8 defines the two owner HARD tests.
- The daily set contains 20 unique lemmas. Its rows are ordered pending due,
  pending new, then completed. Completed rows remain visible and dim to `0.62`.
  Hover and focus restore a completed row to full opacity. State is always three
  channel: boxed glyph (`✦`, `↻`, `✓`), localized text, and the accepted
  yellow-dark/blue/green semantic color.
- The words disclosure is a native `<details>` element, closed on initial setup
  render. Its summary is at least 48 CSS pixels high and exposes the real open
  state through `aria-expanded`.
- Word rows and every interactive target in redesign scope have a 48 CSS pixel
  minimum hit area.
- The compact mode chooser always exposes all 11 accepted modes. It shows four
  columns on desktop and an auto-filling two-column layout on mobile. Each card
  contains only title and step label; one shared line shows the hovered or
  focused card's description. Cards have no mode icons.
- Flashcards use the site's real 3D `.flashcard` pattern. The card itself flips;
  ratings remain disabled before the flip; choosing a rating locks the result;
  the learner advances only through the explicit next control.
- No assessed interaction auto-advances. A submitted answer, final match, or
  flashcard rating must first enter a stable result state, expose feedback, and
  move focus to an explicit next control.
- The exercise stage retains home navigation, current mode, `n / total`
  progress, and one prompt plus descriptor per screen. Digits 1–4 answer where
  options exist; Enter activates the focused explicit next action after result.
- Every new interface string has a non-empty Ukrainian and English value and is
  rendered through the site's exclusive chrome-locale mechanism. Learning
  content remains Ukrainian. UI text must not explain or copy exercise rules.
- Every changed site component triggers lesson-schema regeneration in the same
  PR. The exact required commands are repeated in every applicable chunk.

## 2. Verified integration surface

The implementation must bind to the following existing files and exports. These
are source observations, not proposed names.

| Concern | Verified site surface |
| --- | --- |
| Route | `site/src/pages/words-of-the-day/practice.astro` is the practice page at `/words-of-the-day/practice/`; it renders `CourseLayout`, the mount, the current intro, and route-local practice CSS. |
| Hydration boundary | `site/src/lexicon/LexiconPracticeMount.astro` mounts `LexiconPractice` with `client:only="react"` and supplies the static hydration fallback. |
| State owner | `site/src/components/LexiconPractice.tsx` owns the idle, active, and summary states; level, mode, session budget, loaded shards, SRS review log, streak, daily-new count, due selection, and resumption are already coordinated there. |
| Modes | `MODE_CARD_ORDER` and `MODE_META` in `site/src/components/LexiconPractice.tsx` define the 11 existing modes: mixed, flashcards, matching, choice, cloze, stress, classify, paradigm, synonym, paronym, and heritage, with Ukrainian and English titles, descriptions, and step labels. |
| Published levels | `PUBLISHED_PRACTICE_LEVELS` in `site/src/lib/lexicon/srs.ts` is `A1` through `C1`. `site/src/components/LexiconPractice.tsx` already renders C2 as unavailable with a “soon” label. |
| Core deck | `PracticeIndexItem` and `PracticeLexeme` are declared in `site/src/lib/lexicon/srs.ts`. `site/src/components/LexiconPractice.tsx` loads `practice-index.<level>.json` for the idle state and progressively combines the selected level with lower, disjoint CEFR shards; `ensureDeck` loads the corresponding `practice-lexemes.<level>.json` core before lazy drill shards. |
| SRS state | `CardState`, `ReviewLogEntry`, `isPracticeNewCard`, `isDueReviewCard`, `countDueReviewCards`, `countAvailableNewCards`, `computeSessionScope`, `computeTodayRingDenominator`, and `nextDuePreviewTime` are in `site/src/lib/lexicon/srs.ts`. |
| Daily-new and streak persistence | `PRACTICE_NEW_CARDS_KEY`, `readNewCardsDailyState`, and `writeNewCardsDailyState` are in `site/src/lib/lexicon/srs.ts`. The practice streak is currently persisted under `STREAK_KEY` by helpers in `site/src/components/LexiconPractice.tsx`. |
| Weak areas | `weakCaseChips(reviewLog)` and the Ukrainian case-label map are in `site/src/lib/lexicon/weak-areas.ts`. The function derives up to four weak grammatical cases from `ReviewLogEntry.blankCase`; `translateWeaknessLabel` in `site/src/components/LexiconPractice.tsx` supplies their existing English labels. |
| Next-due copy | `formatNextDueLabel` is currently defined and consumed by the summary in `site/src/components/LexiconPractice.tsx`; its time source is `nextDuePreviewTime` from `site/src/lib/lexicon/srs.ts`. |
| Flashcard component | `site/src/components/PracticeFlashcard.tsx` already renders `.flashcard`, `.flashcard-inner`, `.flashcard-front`, and `.flashcard-back`, flips with pointer or keyboard input, and disables ratings until reveal. Its current parent callback completes immediately after rating. |
| Canonical flashcard CSS | `site/src/styles/lesson.css` defines the real perspective, 3D rotation, blue border/front, and blue back for `.flashcard`. `site/src/pages/words-of-the-day/practice.astro` currently overrides some front/back colors and borders. |
| Matching | `site/src/components/MatchUp.tsx` is the lesson-schema compatibility shim for `packages/activity-kit/src/components/MatchUp.tsx`. The package component reports individual pair ratings through `onMatch` and the final board through `onComplete`. `site/src/styles/match-up.css` is the shared match styling; route-local CSS in `site/src/pages/words-of-the-day/practice.astro` currently flattens matched tiles to one success color. |
| Locale and theme | `site/src/layouts/CourseLayout.astro` pre-paints `lu-theme` and `lu-chrome-locale` and defines exclusive `.lu-i18n`/`.lu-i18n-block` rendering. `ChromeText` and `ChromeDual` are exported by `site/src/lib/i18n/ChromeText.tsx`. Theme color tokens, including teal, orange, purple, and yellow families in both themes, are in `site/src/styles/course.css`. |
| Summary | `site/src/components/PracticeSessionSummary.tsx` already accepts counts, streak, a next-due label, deferred lemmas, and start/back actions. It does not yet render the accepted score ratio and closing proverb. |
| Atlas route | `site/src/pages/lexicon/[lemma].astro` is the lexicon detail route. Existing practice links in `site/src/components/LexiconPractice.tsx` already target `/lexicon/<lemmaId>/`. |
| Separate daily pool | `site/src/lexicon/DailyWords.astro` and `site/src/lib/lexicon/daily.ts` power a separate date-seeded Atlas daily selection from `/lexicon/daily-pool.json`. That random pool is not the source of the practice 20. |
| Existing tests | Practice coverage lives in `site/tests/unit/LexiconPractice.test.tsx`, `site/tests/unit/lexicon-srs.test.ts`, `site/tests/unit/weak-areas.test.ts`, `site/tests/unit/k3-chrome-locale.test.ts`, and `site/e2e/atlas-practice.spec.ts`. |

## 3. Daily-set and SRS data contract

### 3.1 Source of the 20 words

The practice 20 are selected from the existing generated practice-index shards,
not from `/lexicon/daily-pool.json`. The eligible pool is the chosen learner
level plus every published lower level, matching the cumulative behavior already
implemented by `levelsUpTo`, `mergeDecks`, and `ensureDeck` in
`site/src/components/LexiconPractice.tsx`. C2 remains “soon” because
`PUBLISHED_PRACTICE_LEVELS` in `site/src/lib/lexicon/srs.ts` ends at C1.

The setup path loads all eligible `practice-index.<level>.json` shards before it
materializes the daily snapshot. It does not need drill shards. After the 20 IDs
are known, fetch the `practice-lexemes.<level>.json` core only for levels
represented in that set so the dashboard has verified lemma, gloss, part of
speech, and paradigm data. Preserve the current progressive loading behavior for
the active exercise's drill shards in `site/src/components/LexiconPractice.tsx`.

Selection is deterministic for the local date, learner level, and deck version:

1. Collapse card candidates by `lemmaId`; one lemma can occupy only one daily
   slot even when its `PracticeIndexItem.modes` contains several SRS cards.
2. A lemma is due when at least one non-new card satisfies
   `isDueReviewCard(card, now)`. Sort due lemmas by earliest due timestamp, then
   CEFR, `newOrder`, and `lemmaId` for stable ties.
3. A lemma is new when every supported card is absent or satisfies
   `isPracticeNewCard`. Sort new lemmas by CEFR, `newOrder`, and `lemmaId`.
4. Take unique due lemmas first and then unique new lemmas until the set reaches
   20. If a synthetic/test deck contains fewer than 20 eligible unique lemmas,
   use the full eligible set and expose that actual denominator; production
   acceptance fixtures must contain at least 20.
5. A reviewed-but-not-due lemma that is neither due nor new does not displace a
   due or new candidate. Never use randomness to refill the set.

`deckVersion` comes from `PracticeShardMeta.deckVersion`, declared in
`site/src/lib/lexicon/srs.ts` and present on every generated index/lexeme shard.
All eligible index shards must agree on it; a disagreement is a load error, not a
mixed-version daily set.

### 3.2 Persisted snapshot

Add the following versioned contract to `site/src/lib/lexicon/srs.ts`:

```ts
import type { CefrLevel } from './levels';

export interface DailyPracticeDeckItem {
  lemmaId: string;
  origin: 'due' | 'new';
}

export interface DailyPracticeDeckSnapshot {
  version: 1;
  date: string;       // local YYYY-MM-DD
  level: CefrLevel;
  deckVersion: string;
  createdAt: number;
  items: DailyPracticeDeckItem[];
}
```

Export a dedicated storage key and pure/read/write/materialization helpers. The
snapshot is valid only when `version`, local date, selected level, and generated
deck version match. Reuse a valid snapshot so ratings cannot replace rows during
the day. When the generated deck changes, keep still-valid unique IDs in their
saved order and deterministically refill missing IDs with the selection algorithm
above. Invalid JSON or unavailable storage falls back to an in-memory snapshot;
it must not block practice.

Changing learner level intentionally materializes that level's daily snapshot.
Returning to a previously used level on the same local day restores its own
snapshot. The storage representation may therefore be a keyed map of snapshots;
the item contract above remains the serialized unit.

### 3.3 Consumed SRS fields and derived states

The dashboard consumes these existing fields from `CardState` in
`site/src/lib/lexicon/srs.ts`:

- `due`: candidate ordering and whether an existing card is currently due;
- `reps` and `state`: new-card classification through `isPracticeNewCard`;
- `last_review`: tie-breaking and reconciliation when review-log history is
  unavailable;
- `stability` and `difficulty`: not displayed, but preserved and passed through
  the existing scheduling path without modification.

It consumes `ReviewLogEntry.review` as the result timestamp,
`ReviewLogEntry.rating` as the latest outcome, and `ReviewLogEntry.lemmaId` for
daily deduplication. Those fields are declared in
`site/src/lib/lexicon/srs.ts`; do not infer completion from rendered counters.

The visible counters have these exact meanings:

- **Due**: snapshot items whose saved `origin` is `due`.
- **New**: snapshot items whose saved `origin` is `new`.
- **Done**: unique snapshot lemmas with a successful review recorded after the
  later of local midnight and `createdAt`. `hard`, `good`, and `easy` are
  successful; an `again` result returns the lemma to pending due.
- **Streak**: the existing practice streak read through the helpers currently
  owned by `site/src/components/LexiconPractice.tsx`. This redesign does not
  derive a second streak.

Rows are recomputed and ordered as pending due, pending new, then done, retaining
stable snapshot order inside each group. A review result changes state, not daily
membership. Session selection in `site/src/components/LexiconPractice.tsx` must
be constrained to snapshot IDs; a failed card may recur through the existing
closure behavior, but no 21st lemma enters the day's practice.

### 3.4 Atlas links

Every lemma row is one full-row same-tab link. The daily preview remains the
flip button from the frozen design and has a separate same-tab “Open in Atlas”
link. Every such link uses:

```text
/lexicon/${encodeURIComponent(lemmaId)}/
```

This binds the requested `/lexicon/<word>/` scheme to the `lemmaId` consumed by
the real dynamic route in `site/src/pages/lexicon/[lemma].astro`. Nested row
status labels are presentational and must not create competing nested controls.
Chunk 2 introduces one `atlasLemmaHref(lemmaId)` formatter in
`site/src/components/LexiconPractice.tsx`, migrates that component's existing
inline practice-feedback URLs to it, and passes computed URLs to child
components. No link is built from the display gloss or an unverified inflected
surface form.

### 3.5 Focus cue

The focus cue is data-derived, never a hard-coded mockup word. Prefer the first
pending daily lemma with a paradigm form for the highest-ranked weak case from
`weakCaseChips(reviewLog)` in `site/src/lib/lexicon/weak-areas.ts`. If that case
has no usable form in the set, scan the remaining pending rows. If no weak case
is available, use the first deterministic non-nominative paradigm form in the
existing generated lexeme data. If no verified form exists, render the accepted
reserved-height cue container without invented linguistic content. The source
lemma and form both link through the Atlas scheme in section 3.4.

## 4. Component map

| File | Disposition | Responsibility after the redesign |
| --- | --- | --- |
| `site/src/lib/lexicon/srs.ts` | CHANGE | Own the versioned daily-snapshot types, storage key, deterministic selection, validation, refill, and row-state derivation. |
| `site/src/lib/i18n/chrome.ts` | CHANGE | Add typed `practice.*` keys for static redesigned interface copy; preserve the existing English-key/Ukrainian-record compile-time parity contract. Dynamic numeric phrases use `ChromeDual` rather than dictionary keys. |
| `site/src/components/PracticeDailyDeck.tsx` | **NEW** | Render the 3D daily-card preview and the collapsed 20-row `<details>` disclosure, row markers, counters, Atlas links, voice slot, and open-state accessibility. It receives data; it does not select the set. |
| `site/src/components/PracticeFormRail.tsx` | **NEW** | Render the generalized source-to-actual-form rail and its idle/correct/wrong/calque verdict states for cloze, paradigm, paronym, and heritage only. |
| `site/src/components/PracticeStress.tsx` | **NEW** | Render arbitrary-length stress choices by iterating the generated `nuclei` positions. It owns no two-vowel special case. |
| `site/src/components/LexiconPractice.tsx` | CHANGE | Materialize/load the daily set; render the accepted home grid; constrain sessions to the 20 IDs; coordinate mode detail, focus cue, result dwell, explicit next, form rail, level changes, and summary data. |
| `site/src/components/PracticeFlashcard.tsx` | CHANGE | Keep the real `.flashcard`; add a locked rated state and explicit parent-controlled completion. Prevent flip/rating keyboard handlers after lock. |
| `site/src/components/PracticeSessionSummary.tsx` | CHANGE | Add the accepted completed/total ratio and closing proverb while retaining next-due formatting and existing actions. |
| `site/src/components/MatchUp.tsx` | CHANGE | Add the documented optional practice-only pair-coding prop to the lesson-schema shim. |
| `packages/activity-kit/src/components/MatchUp.tsx` | CHANGE | Implement the optional four-token semantic coding and visible pair tags while preserving the default behavior for all existing lesson consumers. |
| `site/src/pages/words-of-the-day/practice.astro` | CHANGE | Keep `CourseLayout` and `LexiconPracticeMount`; remove the superseded intro; implement the accepted grid, responsive, state, theme, and contrast styling; stop neutralizing the canonical flashcard front/back. |
| `site/src/styles/match-up.css` | CHANGE | Define opt-in semantic pair tokens and matched/focus states without changing default lesson matching. |
| `site/tests/unit/*.test.*`, `site/e2e/atlas-practice.spec.ts` | CHANGE/NEW CASES | Prove data selection, copy completeness, accessibility, dwell behavior, themes, rails, pair coding, and hard viewport requirements. |

## 5. Ordered PR-shaped build chunks

Each chunk is independently shippable and testable. Land them in this order.
Later chunks may depend only on already-landed public contracts from earlier
chunks.

### Chunk 1 — Daily-set domain and copy inventory

**Goal:** introduce the deterministic 20-lemma contract without changing the
current UI.

**Files**

- CHANGE `site/src/lib/lexicon/srs.ts`.
- CHANGE `site/src/lib/i18n/chrome.ts`.
- CHANGE `site/tests/unit/lexicon-srs.test.ts`.
- **NEW** `site/tests/unit/practice-chrome-copy.test.ts`.

**Build brief**

1. Add the types, keyed storage, pure selection, snapshot validation/refill, and
   visible row-state derivation from section 3.
2. Keep all scheduling and rating algorithms untouched. The new functions select
   lemmas; existing SRS functions still select/update cards.
3. Add the accepted static chrome strings to the English and Ukrainian records in
   `site/src/lib/i18n/chrome.ts` under typed `practice.*` keys. Include setup
   labels, words show/hide, status names, tap-to-flip, explicit next, rail
   labels/verdicts, score/next-due labels, voice-slot accessible text, and
   C2-soon text. Reuse existing `MODE_META` and rating pairs where they already
   exist, without rewriting them.
4. Add a test that rejects a missing or whitespace-only locale value for every
   `practice.*` key. Do not concatenate `uk / en` in the data layer.

**Acceptance**

- Exactly 20 unique lemmas are selected from a fixture containing enough data;
  due precedes new, and all deterministic tie-breakers are covered.
- Multiple due modes for one lemma consume one slot.
- A valid snapshot is stable after SRS mutations and page reload.
- Date, level, version, corrupt JSON, a missing ID, and a duplicate ID exercise
  their specified invalidation/refill paths.
- `again` moves a completed lemma back to pending due; a later successful rating
  moves it back to done without changing membership.
- Every new `practice.*` key contains non-empty `uk` and `en` values, and the key
  sets remain identical.
- `PUBLISHED_PRACTICE_LEVELS` remains A1 through C1 and C2 is not added to the
  eligible pool.

**Verification**

```bash
npm --prefix site exec -- vitest run \
  tests/unit/lexicon-srs.test.ts \
  tests/unit/practice-chrome-copy.test.ts
npm --prefix site exec -- tsc --noEmit
```

No site component changes in this chunk, so the lesson-schema regeneration rule
is not triggered.

### Chunk 2 — Accepted setup dashboard and daily words

**Goal:** ship the r8 home layout, daily card/list, counters, focus cue, level
selector, compact modes, and the two owner HARD tests.

**Files**

- **NEW** `site/src/components/PracticeDailyDeck.tsx`.
- CHANGE `site/src/components/LexiconPractice.tsx`.
- CHANGE `site/src/pages/words-of-the-day/practice.astro`.
- CHANGE `site/tests/unit/LexiconPractice.test.tsx`.
- CHANGE `site/tests/unit/k3-chrome-locale.test.ts`.
- CHANGE `site/e2e/atlas-practice.spec.ts`.

**Build brief**

1. Move the setup hero into the React idle dashboard so one grid owner controls
   the frozen desktop areas and mobile DOM order. Keep `CourseLayout` and
   `LexiconPracticeMount` unchanged as the route/hydration boundary.
2. Load all eligible index cores, materialize the snapshot, and fetch lexeme
   cores for its represented levels. Render loading/error states in the grid
   without shifting the CTA below the first viewport.
3. Render the real level control using the published-level gate already present
   in `site/src/components/LexiconPractice.tsx`; A1–C1 are enabled and C2 is
   disabled with paired “soon” copy.
4. Render due/new/done counters, existing streak, the mixed-session card, and the
   derived focus cue. Existing resumable mixed-session state takes precedence in
   the CTA label/action. Preserve existing stored mode sessions even though the
   frozen home card exposes only the primary mixed resume action.
5. Render `PracticeDailyDeck` with the canonical 3D classes from
   `site/src/styles/lesson.css`. The preview card is always visible; the list is
   collapsed initially. Keep its `n / total` position, previous/next buttons,
   lemma/IPA/part-of-speech/level front, gloss back, and separate “Open in
   Atlas” link. Make each list row a full Atlas link. The speaker is a
   non-functional but accessible voice slot, not a playback button.
6. Render all 11 `MODE_CARD_ORDER` entries. Use title and step only. Update one
   shared `aria-live="polite"` description line from pointer hover or keyboard
   focus; associate every card with it through `aria-describedby`. On pointer
   leave or blur, restore the accepted Mixed detail text. Relocate the exact
   existing `MODE_META` strings without rewriting them. Do not use icons.
7. Apply the exact desktop grid, including the `"."` row, and the frozen mobile
   DOM order. Preserve the canonical flashcard colors by deleting the route-local
   front/back overrides that neutralize `site/src/styles/lesson.css`.
8. Keep row opacity at `0.62`. Use a foreground token that passes the composited
   normal-text contrast threshold in both themes; do not lower the opacity or
   silently alter the accepted status colors. Restore opacity to `1` on hover and
   focus.
9. Preserve the accepted epigraph verbatim as Ukrainian learning content:
   `«Мова — це серце народу: гине мова — гине народ» — Іван Огієнко`. Keep the
   10/20/until-clear session-size controls and scope estimate in the session card.

**Acceptance**

- HARD-1 and HARD-2 in section 8 pass at exactly `1366x768` with no prior scroll.
- Desktop computed `grid-template-areas` contains the empty filler row. At
  `999px`, DOM/tab order is hero, stats, CTA, words, focus, modes.
- The disclosure begins closed, its 48px summary toggles with pointer and
  keyboard, and `aria-expanded` always equals its open state.
- The daily preview plus list represent the same unique snapshot IDs. Rows are
  due/new/done ordered; completing a row dims rather than removes it.
- Every row and the preview's separate Atlas link use the encoded URL from
  section 3.4; clicking the preview card flips rather than navigates.
- A1–C1 can be selected; C2 is disabled and labeled “soon” in the active locale.
- All 11 mode cards are present at every level, even when a mode has no current
  focus recommendation. Hover and focus update the same single detail line.
- Ukrainian and English chrome each show one locale, not slash-concatenated
  duplicates. The page passes in light, dark, and system theme settings.
- Automated contrast is at least 4.5:1 for normal row text and 3:1 for state
  markers/focus indicators after the done-row opacity is composited in both
  themes.

**Verification**

```bash
npm --prefix site exec -- vitest run \
  tests/unit/LexiconPractice.test.tsx \
  tests/unit/k3-chrome-locale.test.ts \
  tests/unit/lexicon-srs.test.ts \
  tests/unit/practice-chrome-copy.test.ts
npm --prefix site exec -- playwright test e2e/atlas-practice.spec.ts
npm --prefix site exec -- tsc --noEmit
```

**Lesson-schema regeneration — mandatory because site components change**

```bash
.venv/bin/python scripts/build/generate_lesson_schema.py
.venv/bin/pytest tests/test_lesson_schema.py tests/test_prompt_substitution.py -v
.venv/bin/ruff check scripts/build/generate_lesson_schema.py scripts/build/prompt_builder.py tests/test_lesson_schema.py tests/test_prompt_substitution.py
```

Commit `docs/lesson-schema.yaml` only if regeneration produces a real component
contract change. Never omit the regeneration step because the generated diff is
empty.

### Chunk 3 — Real flashcard dwell and accepted summary

**Goal:** finish the flashcard mode and session close without auto-advance.

**Files**

- CHANGE `site/src/components/PracticeFlashcard.tsx`.
- CHANGE `site/src/components/LexiconPractice.tsx`.
- CHANGE `site/src/components/PracticeSessionSummary.tsx`.
- CHANGE `site/src/pages/words-of-the-day/practice.astro`.
- CHANGE `site/tests/unit/LexiconPractice.test.tsx`.
- CHANGE `site/e2e/atlas-practice.spec.ts`.

**Build brief**

1. Extend `PracticeFlashcard` with an explicit locked/rated state. Before reveal,
   the four rating controls are visibly dimmed and semantically disabled. After
   reveal, one rating records through the existing SRS callback, disables
   further flip/rating input, and returns the rating to the parent without
   completing the selection.
2. In `LexiconPractice`, replace the flashcard `rateAndComplete` path with the
   existing parked-outcome pattern. Show the accepted result and explicit next
   control; focus it after rating. Only that control completes the selection.
3. Apply the same dwell boundary to final matching completion at the parent
   level: the completed board stays visible, the result is announced, and an
   explicit next control advances. Individual `onMatch` ratings remain attached
   to their original pairs.
4. Add the accepted completed/total score ratio and closing proverb to
   `PracticeSessionSummary`. The large score is the existing session
   `correct / (correct + lapsed)` result, matching the accepted 18/20 example;
   it is not the separate daily done ring. The outcome lists remain constrained
   to lemmas in the same daily snapshot. Render the Ukrainian learning-content
   proverb exactly as `«Терпи, козаче — отаманом будеш.»` with attribution
   `Українське прислів'я`. Keep the existing
   `formatNextDueLabel(nextDuePreviewTime())` pipeline in
   `site/src/components/LexiconPractice.tsx`.
5. Audit choice, cloze, stress, classify, paradigm, synonym, paronym, and heritage
   paths so every assessed submission uses the same submit → locked result →
   explicit next lifecycle. Do not use timeouts for progression.

**Acceptance**

- Enter/Space flips the card while unrated. Rating shortcuts do nothing before
  reveal. One pointer or keyboard rating records exactly once, locks the card,
  announces the result, and focuses next.
- Waiting after any result never changes the prompt. The next prompt appears only
  after activating the explicit control.
- The final matching pair does not leave the board; one result and one next
  control appear, and pair-level ratings are not duplicated.
- A unit-test matrix covers no-auto-advance for all 11 modes.
- Summary ratio equals correct over correct plus lapsed, retains the existing
  next-due label, and renders its paired interface labels in only the selected
  locale. Its two outcome lists contain only daily-snapshot lemmas.
- Canonical `.flashcard` perspective/front/back styling from
  `site/src/styles/lesson.css` remains effective in both themes.

**Verification**

```bash
npm --prefix site exec -- vitest run \
  tests/unit/LexiconPractice.test.tsx \
  tests/unit/k3-chrome-locale.test.ts
npm --prefix site exec -- playwright test e2e/atlas-practice.spec.ts
npm --prefix site exec -- tsc --noEmit
```

**Lesson-schema regeneration — mandatory because site components change**

```bash
.venv/bin/python scripts/build/generate_lesson_schema.py
.venv/bin/pytest tests/test_lesson_schema.py tests/test_prompt_substitution.py -v
.venv/bin/ruff check scripts/build/generate_lesson_schema.py scripts/build/prompt_builder.py tests/test_lesson_schema.py tests/test_prompt_substitution.py
```

Commit `docs/lesson-schema.yaml` only if regeneration produces a real component
contract change.

### Chunk 4 — Practice-only matching pair coding

**Goal:** reproduce r7.1 per-pair semantics without regressing lesson MatchUp.

**Files**

- CHANGE `site/src/components/MatchUp.tsx`.
- CHANGE `packages/activity-kit/src/components/MatchUp.tsx`.
- CHANGE `site/src/components/LexiconPractice.tsx`.
- CHANGE `site/src/styles/match-up.css`.
- CHANGE `site/src/pages/words-of-the-day/practice.astro`.
- CHANGE existing MatchUp unit tests and `site/tests/unit/LexiconPractice.test.tsx`.

**Build brief**

1. Add the optional documented prop
   `matchedPairCoding?: 'semantic-four'` to both the site shim and package
   component. Omitted means equivalent default DOM, rendering, and behavior for
   existing lessons.
2. In the opt-in practice mode, assign each original pair a stable token index
   `pairIndex % 4`. Use the existing teal, orange, purple, and yellow theme token
   families from `site/src/styles/course.css`; never infer identity from color
   alone.
3. After a match, render the same visible circled tag on both partners:
   `①`, `②`, `③`, `④`, then repeat the color cycle while incrementing the tag
   through the available board size. Include the tag and partner identity in the
   accessible name. Keep unmatched, selected, wrong, focus, and disabled states
   distinct in light and dark themes.
4. Have `LexiconPractice` opt in only for the practice matching mode. Remove the
   route-local single-green matched override for this mode. Preserve
   `onMatch(pairIndex, rating)` identity through the shuffled right column.
5. Update the localized prompt progress after each pair (`Доберіть пари · n з N`
   / `Match pairs · n of N`). Keep the accepted mismatch behavior: red border
   plus a 240ms shake when motion is allowed; omit the shake under reduced motion.

**Acceptance**

- A four-pair board produces four token families and four matching tag pairs.
  A board above four pairs cycles colors but keeps unique visible tags.
- Both members of a pair share token and tag after matching; different pairs do
  not become indistinguishable through color alone.
- Shuffle does not change original pair identity or rating attribution.
- Progress announces `n of N` after each match; mismatch clears after 240ms and
  never advances the board.
- Keyboard-only completion exposes selected, wrong, matched, and next focus in a
  sensible order. Accessible names communicate pair identity without requiring
  color perception.
- A MatchUp rendered without `matchedPairCoding` has unchanged DOM semantics,
  callbacks, and visual state classes.
- Light/dark contrast passes the thresholds in chunk 2.

**Verification**

```bash
npm --prefix site exec -- vitest run \
  tests/unit/LexiconPractice.test.tsx \
  tests/unit/MatchUp.test.tsx
npm --prefix site exec -- playwright test e2e/atlas-practice.spec.ts
npm --prefix site exec -- tsc --noEmit
```

**Lesson-schema regeneration — mandatory because site components change**

```bash
.venv/bin/python scripts/build/generate_lesson_schema.py
.venv/bin/pytest tests/test_lesson_schema.py tests/test_prompt_substitution.py -v
.venv/bin/ruff check scripts/build/generate_lesson_schema.py scripts/build/prompt_builder.py tests/test_lesson_schema.py tests/test_prompt_substitution.py
```

Commit `docs/lesson-schema.yaml` only if regeneration produces a real component
contract change.

### Chunk 5 — Generalized form rail and N-vowel stress

**Goal:** finish the accepted form feedback across the four relevant modes and
close the three carry-over fixes.

**Files**

- **NEW** `site/src/components/PracticeFormRail.tsx`.
- **NEW** `site/src/components/PracticeStress.tsx`.
- CHANGE `site/src/components/LexiconPractice.tsx`.
- CHANGE `site/src/pages/words-of-the-day/practice.astro`.
- CHANGE `site/tests/unit/LexiconPractice.test.tsx`.
- CHANGE `site/e2e/atlas-practice.spec.ts`.

**Build brief**

1. Give `PracticeFormRail` typed source entries, the actual selected/typed form,
   and verdict `'idle' | 'correct' | 'wrong' | 'calque'`. Render it only for
   cloze, paradigm, paronym, and heritage. Recognition modes do not receive an
   ornamental empty rail. Keep Atlas navigation in the existing feedback-link
   position; do not turn the frozen static rail cells into new controls.
2. Cloze and paradigm show dictionary lemma/source at left and the learner's
   actual answer at right. A non-empty check locks one honest outcome. Clicking a
   suggestion populates the input; only the check action commits it. Do not
   silently correct a wrong typed form before displaying the rail.
3. Paronym shows both candidate dictionary forms on the left and the actual
   selected inflected option on the right. `PracticeParonymItem.lemma`,
   `.confusable`, and `.answer` already provide this data in
   `site/src/lib/lexicon/srs.ts`; do not derive new linguistic claims in the UI.
4. Heritage uses `PracticeHeritageItem.nativeLemma` (falling back to `.lemma`)
   for the dictionary-form side and `.answer` for the form side, as generated by
   `scripts/audit/generate_practice_deck.py`. Preserve the accepted label touch:
   source is `день`; render the supplied `.answer` value `днями` in the rail even
   when the sentence option label is orthographically capitalized `Днями`.
   Preserve the option label's capitalization in sentence feedback. Do not
   lowercase arbitrary answers or derive a new form in the component.
5. A calque selection gets the distinct calque verdict; other wrong answers get
   wrong. Correct/wrong/calque color is always accompanied by visible text and an
   announced status.
6. `PracticeStress` must render the accepted word-shaped control by iterating
   `Array.from(item.unstressed)` and replacing every code-point position listed
   in `PracticeStressItem.nuclei` with a vowel button; all other code points are
   text spans. The generator's `_vowel_nuclei` in
   `scripts/audit/generate_practice_deck.py` supplies the complete position list
   and emits only payloads with at least two nuclei. No component branch may
   assume exactly two vowels or fixed word length. Compare the selected supplied
   nucleus index with `stressIndex`; do not recompute Ukrainian stress from
   spelling.
7. Apply the carry-over done-row AA check from chunk 2 again after final styling.
   The frozen `0.62` opacity remains; choose a compliant underlying text token or
   block the PR and record a designer note rather than weakening the threshold.

**Acceptance**

- Stress fixtures with two, three, and at least five vowel nuclei render exactly
  that many in-word buttons, preserve supplied code-point positions around
  consonants/apostrophes, and record the correct supplied `stressIndex`.
- Cloze suggestion click changes the input but does not submit. Check locks and
  shows exactly the typed/selected form plus an honest verdict.
- The rail appears for cloze, paradigm, paronym, and heritage, and is absent from
  mixed recognition-only prompts, flashcards, matching, choice, stress,
  classify, and synonym.
- Heritage rail tests cover source `день`, rail form `днями`, and a sentence
  answer beginning `Днями`; no lowercasing leaks into sentence feedback.
- Existing feedback Atlas links use encoded lemma IDs, not displayed inflected
  forms; the rail remains static.
- Correct, wrong, and calque remain distinguishable in forced light/dark themes,
  without relying on hue alone.
- Done-row text/markers still meet 4.5:1/3:1 after opacity compositing in both
  themes.
- No mode advances before the explicit next action.

**Verification**

```bash
npm --prefix site exec -- vitest run \
  tests/unit/LexiconPractice.test.tsx \
  tests/unit/k3-chrome-locale.test.ts
npm --prefix site exec -- playwright test e2e/atlas-practice.spec.ts
npm --prefix site exec -- tsc --noEmit
```

**Lesson-schema regeneration — mandatory because site components change**

```bash
.venv/bin/python scripts/build/generate_lesson_schema.py
.venv/bin/pytest tests/test_lesson_schema.py tests/test_prompt_substitution.py -v
.venv/bin/ruff check scripts/build/generate_lesson_schema.py scripts/build/prompt_builder.py tests/test_lesson_schema.py tests/test_prompt_substitution.py
```

Commit `docs/lesson-schema.yaml` only if regeneration produces a real component
contract change.

## 6. Interaction state contract

All 11 modes use the same parent-level state progression in
`site/src/components/LexiconPractice.tsx`:

```text
unanswered → submitted/locked → result visible → explicit next → next selection
```

- `unanswered`: relevant inputs are enabled; next is absent.
- `submitted/locked`: one result has been recorded; input, card, or completed
  board can no longer emit another result.
- `result visible`: verdict, explanation/form rail where applicable, and next are
  present in the DOM; next receives focus without scrolling the prompt away.
- `explicit next`: this is the only transition that calls the current selection
  completion function. No timer, animation end, SRS rating callback, or final
  `onMatch` callback may trigger it.

Matching mismatch feedback resets after the frozen 240ms interval. Its red state
is feedback within the unanswered board, not progression. The shake is disabled
under reduced motion and the reset must not move focus unpredictably.

## 7. Locale, theme, accessibility, and copy gates

### Locale-pair completeness

- Every new static chrome string is defined once under a typed `practice.*` key
  in both locale records in `site/src/lib/i18n/chrome.ts`.
- React renders static keys with `ChromeText` and interpolated pairs with
  `ChromeDual`, both from `site/src/lib/i18n/ChromeText.tsx`. Do not use the
  current `showEnglishSubtitles` slash-copy pattern for redesigned chrome.
- Existing Ukrainian lemmas, prompts, quotes, and inflected forms are learning
  content and remain visible in both chrome locales.
- Unit tests iterate every new copy key and render the dashboard, interaction
  result, and summary once in each locale. Each run rejects the inactive locale's
  chrome text in the accessibility tree.

### Theme and contrast

- Test explicit light and dark values of the real `lu-theme` mechanism from
  `site/src/layouts/CourseLayout.astro`, plus system mode with emulated light and
  dark preference.
- Test default, hover, focus-visible, selected, wrong, correct, calque, disabled,
  and done states. Normal text requires WCAG AA 4.5:1; large text and non-text
  state/focus boundaries require 3:1.
- The dimmed done row is measured after `opacity: 0.62` is composited over the
  actual theme background. A raw token-to-token calculation is insufficient.
- Reduced-motion mode removes unnecessary transitions while retaining the real
  front/back relationship and immediate state change.

### Zero rule-copy gate

No new visible string may narrate the implementation rules, for example how
colors pair tiles, how the queue is ordered, how a form rail is derived, or that
the learner must wait for next. Such rules belong in semantic markup, tests, and
this specification. The approved copy inventory is an allow-list: the unit test
renders every redesigned state and fails on visible chrome absent from
the `practice.*` dictionary, `MODE_META`, the existing rating labels, or
explicitly approved learning content.

### Accessibility details

- Native elements are preferred: `<details>/<summary>`, links for Atlas
  navigation, buttons for mode/start/next/rating actions.
- Hover behavior has an equivalent focus behavior. Focus indicators remain
  visible in both themes.
- State markers and pair identity use text/shape plus color. The matching tag is
  part of the accessible name.
- Result changes and the shared mode detail use polite live regions; do not
  announce the entire dashboard after each row-state change.
- The mobile visual order must match DOM and focus order.

## 8. Owner HARD tests and final acceptance matrix

### HARD-1 — English first viewport

In `site/e2e/atlas-practice.spec.ts`, set a deterministic 20-item fixture and a
resumable Mixed session, select English chrome and a desktop light theme, set the
viewport to exactly `1366x768`, open `/words-of-the-day/practice/`, wait for the
idle dashboard to settle, and make **no scroll call**. Assert:

- `window.scrollY === 0`;
- both start and resume controls are fully inside the viewport:
  `rect.top >= 0 && rect.bottom <= 768` for each;
- both controls are actionable and their English accessible names are visible;
- the words disclosure begins closed and the 3D preview remains visible.

### HARD-2 — Ukrainian first viewport

Repeat HARD-1 from a clean context with Ukrainian chrome and a desktop dark
theme. Assert the same start-and-resume geometry at exactly `1366x768`, the
Ukrainian accessible names, and absence of the English CTA chrome.

`1440x900` remains a secondary visual-regression viewport from the accepted r8
mockup, but it does not replace either `1366x768` HARD test.

### Cross-chunk release matrix

| Gate | Required proof |
| --- | --- |
| Frozen layout | Exact desktop grid including `"."`; mobile DOM/focus order; HARD-1 and HARD-2. |
| Daily 20 | Unique persisted IDs, due/new source counts, stable done state/order, actual denominator for undersized fixtures. |
| All modes | Exactly the 11 `MODE_CARD_ORDER` modes, compact titles/steps, one shared focus/hover detail line, no icons. |
| Real flashcard | Canonical `.flashcard` DOM/CSS, card flip, disabled pre-flip ratings, locked rated state, explicit next. |
| Honest feedback | Actual submitted value, distinct wrong/calque, relevant four-mode form rail only, heritage labeling touch. |
| Stress generality | N-vowel/code-point fixtures; no two-vowel assumption. |
| Pair coding | Four theme tokens plus visible/announced pair tags; default lesson MatchUp unchanged. |
| Locale | Every new string has uk/en; exclusive active chrome in setup, activity, and summary. |
| Theme/AA | Light, dark, system, focus/state contrast, composited done-row checks. |
| Progression | Submit/rate/final-match never auto-advances; explicit next is focused and solely advances. |
| Copy discipline | No rule narration and no redesigned chrome outside the approved pair inventories. |
| Schema | Every PR that changes a site component runs generator, schema tests, and generator/prompt-builder Ruff checks. |

## 9. Out of scope

The following mockup-adjacent work ships later and must not expand these chunks:

- Voice playback, audio generation, microphone input, speech recognition, and
  pronunciation scoring. This release reserves only the accepted voice slot.
- A new backend, account synchronization, or cross-device daily snapshot. The
  contract is local storage with the existing in-memory fallback.
- New SRS math, rating intervals, closure policy, streak policy, or a migration
  away from the existing scheduler in `site/src/lib/lexicon/srs.ts`.
- New lexical, paradigm, stress, heritage, paronym, or translation content. The
  UI consumes the generated practice fields; it does not invent missing facts.
- C2 practice data or enabling C2. It remains “soon.”
- Redesigning the separate daily-words pool in `site/src/lexicon/DailyWords.astro`
  or changing `site/src/lib/lexicon/daily.ts`.
- Bespoke new classify or synonym mechanics beyond placing their current
  behavior inside the accepted shared shell and dwell lifecycle.
- A global redesign of `CourseLayout`, the site header/footer, Atlas detail
  pages, or non-practice lesson activities.
- Changing default MatchUp visuals outside the explicit practice-only opt-in.
- Shipping the mockup's demo controls, viewport labels, annotations, or debug
  furniture.

## 10. Designer notes appendix

No design deviations are proposed.

Two implementation clarifications preserve the frozen design without fabricating
content:

1. The daily focus cue remains a reserved-height layout area when no generated
   pending lemma has a verified form. It does not substitute a hard-coded example.
2. The heritage `день`/`днями` touch reads the supplied dictionary and `.answer`
   fields for the rail while the sentence uses its supplied option label. No
   runtime morphological transformation or blanket lowercasing is introduced.

Any later discovery that requires changing frozen copy, layout, opacity, mode
count, progression, or semantic color mapping must be recorded as a new designer
note and returned to the owner for an explicit decision before implementation.

## 11. Review provenance

The 2026-07-18 pre-submit cross-family advisory review used Gemini 3.1 Pro High
through the approved AGY/Antigravity lane and returned `PASS` with no material
findings. This was a recorded lane substitution: the direct Gemini CLI OAuth
probe was unavailable, while CodexBar reported the Antigravity lane healthy.

A second native read-only cross-family pass used Claude Opus 4.8 and returned
`PASS`. Its three advisory accuracy notes (`levelsUpTo`, the `CefrLevel` import,
and introduction-versus-existence of the Atlas formatter) were applied before
PR creation. The isolated-review resolver found no eligible cross-family route;
the AGY sealed branch attempt failed closed because native instruction/hook/MCP
suppression could not be proven. These advisory passes are therefore recorded
as substitutions, not misrepresented as a formal isolated receipt.

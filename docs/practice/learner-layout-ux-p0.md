# Practice Learner Layout UX — P0/P1 (design of record)

Status: accepted design baseline for learner-facing layout fixes to the existing
K3 practice UI. **This is not a redesign.** The K3 layout (one centered column,
11 mode cards, daily deck of 12, explicit «Далі →» advance, no auto-advance)
stays frozen per `docs/practice/K3-BUILD-SPEC.md`. Every item below is a
targeted layout/affordance fix inside the current structure.

Audience: non-power-user learners. Consequences:

- **No onboarding tour.** Help must live inline, on the surface where it is
  needed, in the learner's chrome locale.
- **No required shortcuts.** Keyboard shortcuts (1–4, Enter, Space) may stay as
  redundant accelerators; nothing may be reachable only by keyboard.
- **Visible helpers only:** text labels (not icons alone), per-mode counts,
  empty states that name the next action, hit targets of at least 48 CSS px
  (K3-BUILD-SPEC §1: "every interactive target in redesign scope has a 48 CSS
  pixel minimum hit area").

Sources of truth for current behavior: `site/src/components/LexiconPractice.tsx`
and the components it mounts (`PracticeDailyDeck`, `PracticeFlashcard`,
`PracticeStress`, `PracticeSessionSummary`, `MatchUp`), styles in
`site/src/pages/words-of-the-day/practice.astro`, `site/src/styles/match-up.css`,
SRS logic in `site/src/lib/lexicon/srs.ts`. Line numbers below are as of this
writing and drift; the component/section names are the durable anchors.

Practice-type coverage note (not a layout item):

- **Antonym** exists as a polarity of the synonym shard
  (`PracticeSynonymItem.polarity: 'synonym' | 'antonym'`, srs.ts:228; prompt
  «Оберіть антонім до «X»», LexiconPractice.tsx:1180-1190). It shares the
  «Синоніми» mode card; there is no separate antonym count. Keep it this way —
  do not split the mode card.
- **Homonym** (омоніми) has no practice mode at all; it appears only in Word
  Atlas articles (`site/src/lexicon/WordAtlasArticle.tsx:648-663`). Building a
  homonym drill is out of scope for this document; when it lands it must follow
  the same layout rules below.

---

## P0 — blocks or misleads the learner on the primary path

### P0-1. Mode descriptions are hover-only; touch learners never see them

- **Problem:** The 11 mode cards show only title + step label. The description
  («Що це за режим») lives in one shared line `#mode-detail-line` that updates
  on hover/focus and defaults to Мікс. On touch there is no hover, and tapping a
  card starts the session immediately — a mobile learner picks a mode with zero
  explanation of what it drills. This contradicts "no onboarding tour; visible
  helpers".
- **Location:** `LexiconPractice.tsx:3565-3604` (mode grid, `onPointerEnter`/
  `onFocus` handlers), mode copy in `MODE_META` (`507-618`).
- **Concrete layout change:** Put the description text *on each card*, below
  the step label, at readable size (≥0.8rem, not uppercase), wrapped to two
  lines max. Keep the card a single `<button>`; description is part of the
  button's accessible name. Remove the shared hover line (or keep it as a
  desktop-only redundancy — but the card must be self-sufficient).
- **Do-not-change:** The 11-card grid, its order (`MODE_CARD_ORDER`), 4-col
  desktop / 2-col mobile layout, the single shared line *may* stay as
  decoration but must not be the only carrier of the description. No mode
  icons (spec §1).

### P0-2. Empty states are dead ends with no next action

- **Problem:** When the pool is empty the learner hits a text-only wall:
  «Усі картки на зараз повторено.» (`3723-3727`), «Поки що немає карток для
  практики.» (`3674-3678`), empty cloze/heritage/paronym shards
  («…ще готуються.», `3711-3722`), matching/choice option-build failures
  (`3999-4046`), and the focus-miss «Це слово ще не в тренажері.» (`3219-3226`).
  The cloze empty state even *names* alternatives («Спробуйте флешкартки, добір
  пар або вибір.») without linking them. Only «← Додому» escapes.
- **Location:** `LexiconPractice.tsx:3674-3727` (active-phase empties),
  `3999-4046` (option-build failures), `3219-3226` (focus miss).
- **Concrete layout change:** Every empty state gets the same three-part block:
  (1) what happened, one sentence; (2) the single best next action as a
  full-width primary button (e.g. «← Додому» becomes «Повернутись до режимів»;
  cloze-empty gets «Почати флешкартки» wired to `startFocusMode('flashcards')`);
  (3) where it *does* make sense, up to two secondary mode buttons with real
  counts («Флешкартки · 34»). Text-only suggestions are forbidden: any mode
  named in copy must be a button.
- **Do-not-change:** The copy's meaning and the shard-level guards
  (`hasLoadedDrillShards`); the "ще готуються" states for heritage/paronym must
  stay honest — the next action there is «Повернутись до режимів», not a fake
  start button. Session/isolation logic in srs.ts untouched.

### P0-3. Zero-count mode cards look playable; counts are aria-hidden

- **Problem:** A mode with 0 items (e.g. Спадщина before curated pairs land) is
  still a fully clickable card; the only signal is a dimmer badge via
  `data-mode-empty`. Tapping it starts a session that dies in P0-2's empty
  state. Worse, the count badge itself is `aria-hidden="true"`, so screen-reader
  users get no count at all.
- **Location:** `LexiconPractice.tsx:2066-2074` (`modeCounts`), `3597-3603`
  (badge, `aria-hidden`), `practice.astro:1656-1660` (`data-mode-empty`).
- **Concrete layout change:** (1) Drop `aria-hidden` from the badge and make the
  count part of the card's accessible name («Наголос, 12 вправ»). (2) For
  count-0 modes render an explicit text state on the card — «Немає вправ» (or
  «Скоро» where a shard is planned) — and disable the button (`disabled`, not
  just dimmed), so the learner never starts a guaranteed-empty session. Мікс is
  exempt (it aggregates other modes).
- **Do-not-change:** `modeCounts` computation; the badge position (top-right);
  mixed-mode behavior. Do not hide empty modes — the spec requires all 11 cards
  always visible.

### P0-4. Heritage status is color-only on flashcards

- **Problem:** The flashcard corner tag displays the CEFR text («B1») while its
  *background color* encodes heritage (teal native/inherited, purple
  borrowed/loanword, orange calque, red avoid — `HERITAGE_COLORS`).
  Color is the only channel, native vs inherited are indistinguishable, and
  calque/avoid — the decolonization-critical signal — reads as decoration.
- **Location:** `LexiconPractice.tsx:624-631` (`HERITAGE_COLORS`), `810-818`
  (`cardData` tag), `PracticeFlashcard.tsx:114-121` (render).
- **Concrete layout change:** Add a short text chip next to the CEFR tag on the
  card back (front stays clean) with the heritage word itself: «питоме»,
  «успадковане», «запозичене», «калька», «уникай». Keep the color as a
  secondary channel on that chip. Only render when `heritage` is non-null.
- **Do-not-change:** CEFR tag text and position; heritage *feedback* in the
  heritage drill itself («⚠️ калька; {rationale}», `4203-4308`) is already
  textual and stays as-is; color values in `HERITAGE_COLORS`.

### P0-5. Stress-mode vowel targets are ~35×42 px — the smallest in the app

- **Problem:** The core stress interaction is tapping one vowel inside a word.
  Vowel buttons are `min-width: 2.2rem; min-height: 2.6rem` (~35×42 px), under
  the 48 px minimum, and there is no keyboard alternative at all (digits are not
  mapped in stress mode).
- **Location:** `PracticeStress.tsx` (vowel buttons), styles at
  `practice.astro:1761-1763`.
- **Concrete layout change:** Raise vowel buttons to ≥48×48 px (font-size may
  grow to match; the word is the stage, let it be big). Add visible digit
  badges over vowels in reading order and map Digit-1..n to vowels left-to-right,
  matching the choice/classify pattern — as a redundant accelerator, never the
  only path.
- **Do-not-change:** The interaction model (consonants as text, vowels as
  buttons), the prompt «Де наголос у слові «…»? — Оберіть наголошену голосну»,
  stress-mark display rules (A1 shows marks, A2+ strips them, spec §1).

### P0-6. Flashcards have no visible instruction and cryptic rating UI

- **Problem:** A first-time learner sees a bare word. "Tap to flip" exists only
  as an `aria-label`; nothing on screen says the card flips or that you rate
  *after* flipping. The rating bar is always visible but disabled pre-flip with
  unexplained digit badges (1–4) and, post-flip, interval previews like `‹4d›`
  that no label decodes.
- **Location:** `PracticeFlashcard.tsx:108` (card, aria-only instruction),
  `129-154` (rating bar, digit hints, `previewRatingIntervals` render).
- **Concrete layout change:** (1) Add a visible one-line hint under the card
  pre-flip: «Торкніться картки, щоб побачити значення» (chrome-locale
  mechanism, both locales). Hide it after the first flip of the session. (2)
  Label the rating row pre-flip with its own dimmed hint: «Спочатку переверніть
  картку». (3) Give the interval preview a text prefix: «через 4 дн.» instead
  of bare `‹4d›`, pluralized via `uaPlural`. Digits 1–4 may stay as redundant
  hints but must have an aria-label explaining them («клавіша 1»).
- **Do-not-change:** Flip interaction, ratings-disabled-before-flip rule,
  rating locks result, explicit «Далі →» advance (spec §1); SRS rating logic
  (`rateCard`, interval computation) untouched.

### P0-7. Daily-deck collapsed counters are colored bare numbers

- **Problem:** The collapsed «Слова дня» `<details>` summary shows three bare
  numbers whose meaning (due / new / done) is carried only by green/blue/yellow
  color. A non-power user — or anyone color-blind — cannot read their own day
  at a glance.
- **Location:** `PracticeDailyDeck.tsx:224-237` (summary counters); expanded
  rows (`239-296`) already have glyphs + why-lines and are fine.
- **Concrete layout change:** In the collapsed summary, render each counter as
  glyph + number + short label, matching the expanded rows' three-channel rule:
  «↻ 5 до повторення · ✦ 4 нові · ✓ 3 вивчено» (labels through the chrome-locale
  mechanism). This restates spec §1's "state is always three channel" at the
  collapsed layer where it is currently violated.
- **Do-not-change:** The `<details>` element, closed-by-default, ≥48 px summary,
  row order (pending due, pending new, done), deck size 12, row content.

### P0-8. Hit targets below 48 px on secondary controls

- **Problem:** Several learner-facing controls fall under the 48 px floor:
  weak-area chips 40 px (`practice.astro:891-893`), «Скинути фокус ×» ~28 px
  (inline-styled, `LexiconPractice.tsx:3254-3262`), «🔀 Перемішати слова» ~30 px
  (`practice.astro:1380-1392`), deck-switch offer buttons 40 px
  (`practice.astro:1302-1305`), deck-filter chips `btn-sm` (`3284-3351`).
- **Location:** as listed; all idle-phase secondary controls.
- **Concrete layout change:** Bring every one to ≥48 px min-height (min-width
  where tapping is horizontal, e.g. «×» becomes a labeled text button «Скинути
  фокус»). No new elements, no layout reflow — this is padding/size only.
- **Do-not-change:** Placement, grouping, and behavior of these controls; the
  weak-chips focus-session trigger (`3540-3561`); re-roll semantics (#6132).

---

## P1 — degrades clarity or consistency; not path-blocking

### P1-1. Weak-area chips have no visible heading

- **Problem:** The orange chips (case names, etc.) appear with no explanation;
  only an `aria-label` «Слабкі місця» on the group. A sighted non-power user
  sees unlabeled orange pills between the session panel and the mode grid.
- **Location:** `LexiconPractice.tsx:3540-3561`.
- **Concrete layout change:** Add a visible group label «Тренуйте слабкі місця»
  (chrome mechanism) above the chips, same visual weight as «Режими».
- **Do-not-change:** Chip content (`weakCaseChips`), focus-session behavior
  (`focusModeForWeakness`), orange accent.

### P1-2. «Сьогодні» progress ring computed but never rendered

- **Problem:** `computeTodayRingDenominator`, `todayPct`, and `todayRingStyle`
  are computed (`LexiconPractice.tsx:3140-3153`) and no element consumes them.
  The learner has no visible "how much of today is done" denominator — exactly
  the kind of visible helper this audience needs.
- **Location:** `LexiconPractice.tsx:3140-3153` (dead computation), stats strip
  `3409-3426`.
- **Concrete layout change:** Either render it — a thin progress bar or «N з M
  сьогодні» line inside the stats strip — or delete the dead code. Prefer
  rendering: it is the cheapest visible-helper win in this document.
- **Do-not-change:** The four existing stats and their labels; denominator
  computation in srs.ts.

### P1-3. Storage-full warning offers no recovery action

- **Problem:** «Прогрес не зберігається — сховище переповнене» renders as
  `role="alert"` with no guidance. The learner is told progress is lost and
  nothing else.
- **Location:** `LexiconPractice.tsx:3210-3217`, copy in
  `translateStorageWarning` (`448-469`).
- **Concrete layout change:** Append a second sentence naming the action:
  «Звільніть місце в сховищі браузера або ввімкніть синхронізацію з
  Google Drive.» — with the Drive part linking to the existing sync button's
  handler when available.
- **Do-not-change:** Alert role, warning detection flags (`SrsFlags`), the
  Ukrainian-first wording; do not auto-open the Drive flow.

### P1-4. C2 «скоро» is hover-only and unreachable on touch

- **Problem:** The disabled C2 level button carries its only explanation in a
  `title` tooltip; the visible «скоро» label is 0.62rem. Touch users get
  nothing; everyone gets tiny text.
- **Location:** `LexiconPractice.tsx:3387-3406`, `practice.astro:1102`.
- **Concrete layout change:** Raise the «скоро» label to ≥0.75rem and move the
  explanation into an `aria-label` («C2 — скоро») on the disabled button.
  Tooltip may stay as a desktop extra.
- **Do-not-change:** C2 stays disabled until its deck ships
  (`PUBLISHED_PRACTICE_LEVELS`, srs.ts:33); level-selector layout and 44 px→48 px
  button sizing per P0-8.

### P1-5. Paronym and heritage options lack the digit badges other modes have

- **Problem:** Choice/classify/paradigm/synonym option buttons carry visible
  digit badges (1–4) and digit shortcuts; paronym and heritage options have
  neither. Inconsistent affordance trains the learner to expect digits that
  sometimes are not there.
- **Location:** paronym `4147-4160`, heritage `4245-4258`; contrast with
  `3966-3980` (shared option render) and `DigitChoiceShortcuts` (`1351-1375`).
- **Concrete layout change:** Render the same digit badge + shortcut wiring on
  paronym and heritage option buttons. Purely additive.
- **Do-not-change:** Option order/seeded answer placement
  (`seededAnswerIndex`), feedback blocks, auto-derived SRS rating
  (correct→good, wrong→again).

### P1-6. Strings hardcoded outside the chrome-locale mechanism

- **Problem:** Several UI strings are Ukrainian-only ternaries or literals that
  bypass `ChromeText`: the Drive sync button («☁️ Увійти та синхронізувати…»,
  `3278-3279`), deck-filter bar labels (`3288-3314`), the hero epigraph
  (`3377-3379`), the summary proverb (`PracticeSessionSummary.tsx:102-105`),
  and the session `document.title` (`2239`). EN-chrome learners (A1 scaffolding)
  get untranslated chrome; the K3 spec requires every UI string in both locales
  through the exclusive mechanism.
- **Location:** as listed.
- **Concrete layout change:** Move each string into `CHROME_STRINGS` with UK +
  EN values and render via `ChromeText`/`ChromeDual`. UA immersion is
  unaffected — UK chrome shows exactly what it shows today.
- **Do-not-change:** Learning content stays Ukrainian (spec §1); the epigraph
  and proverb *content* stays Ukrainian-only by design (they are content, not
  chrome) but should still route through the mechanism with an EN gloss or an
  explicit documented exemption. Chrome stays single-locale, never dual-visible.

### P1-7. Daily deck has no start CTA of its own

- **Problem:** The learner browses «Слова дня» (carousel, re-roll, Atlas links)
  and must discover that starting happens in a separate panel further down.
  The deck is the emotional entry point of the page; its only actions are
  navigation and re-roll.
- **Location:** `PracticeDailyDeck.tsx` (no CTA); session CTA at
  `LexiconPractice.tsx:3516-3523`.
- **Concrete layout change:** Add a secondary button under the carousel:
  «Почати заняття з цими словами» calling the same `startSession` path as the
  primary CTA. Keep it visually secondary — the session panel's CTA remains
  primary and above the fold (owner HARD test, spec §8).
- **Do-not-change:** Primary CTA placement and label («Почати заняття» /
  «Продовжити заняття»), deck composition, re-roll.

---

## Global do-not-change (applies to every item)

- **Layout:** K3 one-centered-column setup dashboard; DOM order hero → stats →
  words → session → focus/modes; 11 mode cards, order fixed; no desktop grid
  reordering; no mode icons.
- **Interaction rules:** no auto-advance anywhere; every assessed interaction
  enters a stable result state with feedback and focus moves to the explicit
  «Далі →»; flashcard ratings disabled pre-flip; matching auto-rates from
  misses.
- **SRS/content:** `srs.ts` selection, scheduling, session snapshots, daily-deck
  derivation, deck shards, and all item content are out of scope. This document
  changes presentation and affordances only.
- **i18n:** chrome stays single-locale via `html[data-chrome-locale]`; learning
  content stays Ukrainian; A1 English scaffolding is item-content glossing only
  (#5503), never dual chrome.
- **Shortcuts:** keep all existing shortcuts; they are accelerators. Nothing in
  this document may make a shortcut the only way to do something.
- **Pedagogy:** UA immersion and decolonized framing stay as built — heritage
  drill feedback («⚠️ калька…»), epigraph, and proverbs are content decisions
  this document does not reopen.

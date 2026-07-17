# UI Review — Practice hub + Atlas (dictionary) landing

Reviewer: Kimi K3 · Branch: `kimi/atlas-ui-improve` · Date: 2026-07-16

Scope reviewed (in-scope surfaces only; word-page article reviewed for findings only):

- `site/src/pages/words-of-the-day/practice.astro` (+ its global practice styles)
- `site/src/lexicon/LexiconPracticeMount.astro` → `site/src/components/LexiconPractice.tsx`,
  `PracticeFlashcard.tsx`, `PracticeSessionSummary.tsx` (everything the mount mounts)
- `site/src/pages/lexicon/index.astro` (atlas landing) → `site/src/lexicon/AtlasTypeahead.astro`,
  `AtlasRuntimeStatus.astro`
- `site/src/pages/lexicon/browse.astro` → `site/src/lexicon/AtlasFullIndex.astro` (browse UI)
- Live pages cross-checked: `/lexicon/` , `/lexicon/practice/` (astro.config redirect →
  `/words-of-the-day/practice/`), `/words-of-the-day/practice/`

Standing rules applied: UI copy stays Ukrainian (English scaffolding is A1-only by design —
`showEnglishSubtitles = learnerLevel === 'A1'` at `LexiconPractice.tsx:1136`); static hosting;
focused diffs; accessibility/mobile = functionality.

Legend: **[FIXED]** implemented in this PR · **[FILED]** finding only, not fixed here.

---

## HIGH

### 1. Window-level key handlers hijack Enter/Space from focused controls [FIXED]

- `site/src/components/PracticeFlashcard.tsx:44-70` — the window `keydown` flips the card on
  Space/Enter and rates on `1–4`/`a/h/g/e` **regardless of where focus is**. While a card is
  unflipped, pressing Enter/Space on the focused «← Додому» button (or any page control) flips the
  card instead of activating the control, and calls `preventDefault()`.
- `site/src/components/LexiconPractice.tsx:1431-1440` — during the wrong-answer dwell, a window
  Enter handler `preventDefault()`s and advances even when focus is on the «Відкрити в Атласі →»
  links (`:3047`, `:3132`, `:3273`) or «← Додому» (`:2612`). Keyboard-only learners cannot activate
  those controls while `pendingOutcome` is set.
- Minimal fix: bail when the event originates inside an interactive element
  (`target.closest('button, a, input, textarea, select, [role="button"]')`) and only
  `preventDefault()` when the handler actually acts.

### 2. Number badges on choice options promise shortcuts that don't exist [FIXED]

- `LexiconPractice.tsx:2869` (drill options) and `:2956` (choice options) render `.mc-key` badges
  `1/2/3/4` styled as key caps (`practice.astro:907-919`), but no keydown listener maps digits for
  these modes. Flashcards *do* support `1–4` (`PracticeFlashcard.tsx:54-63`), so learners trained
  there press digits in choice/drill and nothing happens.
- Minimal fix: window keydown listener in the drill/choice render paths mapping `1..n` →
  `onChoice(options[n-1])` while `!answerLocked`, with the same interactive-target guard as #1.

### 3. English leaks into the immersion UI for B1+ learners [FIXED]

The component design is Ukrainian-only past A1 (`showEnglishSubtitles = learnerLevel === 'A1'`),
but several strings bypass the gate:

- `LexiconPractice.tsx:1019-1026` — `BilingualPracticeMessage` renders the English half
  unconditionally; used for the load error (`:2587`) and pool-miss notice (`:2242`).
- `LexiconPractice.tsx:2589-2592` — retry button always shows "Try again".
- `LexiconPractice.tsx:3193` — `{cloze.clozeEn}` (English sentence translation) renders for every
  level. It is currently the *only* cue for which word goes in the blank, so gating it requires
  adding the Ukrainian lemma as the cue first.
- `LexiconPractice.tsx:3196` — attribution starts with English "Sentences from".
- `LexiconPractice.tsx:1442-1445` — `document.title` is always English
  (`"Cloze Practice - Words of the Day"`) and is never restored after leaving the session.
- `PracticeSessionSummary.tsx:45` — `<span lang="uk">З lapses</span>` (English word inside a
  Ukrainian-tagged span; a Ukrainian TTS voice mangles it); `:65` — `<span lang="uk">Перейшли до
  Review</span>`; `:88` — heading «повторимо наступного разу» starts lowercase, unlike siblings.
- Minimal fix: gate every English fragment behind `showEnglishSubtitles`; show the cloze target
  lemma in the Ukrainian task line («Поставте слово „валіза" у правильному відмінку») so the
  exercise no longer depends on the English gloss; «Речення з» for attribution; Ukrainian
  `document.title` restored on exit; «Помилки» / «Перейшли на повторення» / «Повторимо наступного
  разу» in the summary.

## MEDIUM

### 4. Flashcard flip auto-focuses the «Добре» rating — races the flipping keystroke [FIXED]

- `PracticeFlashcard.tsx:36-42` — on flip, focus is forced to `[data-rate="good"]`. Space activates
  buttons on **keyup**: flipping with Space moves focus between keydown and keyup, so the keyup
  lands on the just-focused «Добре» button and records an instant accidental rating. The hardcoded
  target also biases the SRS rating.
- Minimal fix: remove the auto-focus; ratings stay reachable via the documented `1–4`/`a/h/g/e`
  keys and Tab.

### 5. Focus lost when «Далі →» appears after a wrong answer [FIXED]

- `LexiconPractice.tsx:2675-2689` — after a wrong pick the clicked option becomes `disabled`, so
  focus drops to `<body>`; the «Далі →» button that appears is never focused. Keyboard/SR users
  lose their place (the window Enter handler was the only recovery — undiscoverable, and see #1).
- Minimal fix: focus the «Далі →» button when it renders (ref + effect on `pendingOutcome`).

### 6. Stale 650 ms auto-advance timer mutates state after the learner leaves [FIXED]

- `LexiconPractice.tsx:2055-2059` (choice) and `:2086-2090` (cloze) — the correct-answer
  auto-advance `setTimeout` is never stored or cleared. Tapping «← Додому» within 650 ms of a
  correct answer still lets `completeSelection` fire: it writes history, bumps counters, and can
  call `openSummary()` — flipping the just-exited session back to the summary screen.
- Minimal fix: keep the timer id in a ref; clear it in `finishPractice`, on unmount, and before
  scheduling a new one.

### 7. Cloze case-label phrasing is ungrammatical Ukrainian [FIXED]

- `LexiconPractice.tsx:3219` — aria-label `Відповідь у знахідний` (bare adjective after «у»);
  `:2101` — feedback «Тепер постав його у знахідний». `caseLabel` values are bare adjectives
  (`знахідний`, `родовий`, … — generated at `scripts/audit/generate_practice_deck.py:724` with
  `CASE_LABELS_UA` `:104-112`), so the two spots that use them with a preposition read wrong.
- Minimal fix (UI-side, data untouched): derive «у знахідному відмінку» (locative) for the
  aria-label and «у знахідний відмінок» (accusative) for the feedback from the bare label —
  all seven case labels are regular hard-stem `-ий` adjectives, so the transformation is uniform.

### 8. Next-due label lacks a unit; `uaPlural` imported but unused [FIXED]

- `LexiconPractice.tsx:2736-2746` — `formatNextDueLabel` produces «ще 3 о 14:00» ("3 more *what*?");
  `uaPlural` is imported (`:34`) and never used.
- Minimal fix: `uaPlural(remaining, { one: 'година', few: 'години', many: 'годин' })` →
  «ще 3 години о 14:00».

### 9. Browse overflow message uses English "more" [FIXED]

- `site/src/lexicon/AtlasFullIndex.astro:423` —
  `` `+${state.overflow} more — звузьте запит` `` — English inside the Ukrainian browse UI.
- Minimal fix: reuse the file's existing `atlasEntryCountLabel` → «ще 154 записи — звузьте запит».

### 10. Typeahead active option doesn't scroll into view [FIXED]

- `site/src/lexicon/AtlasTypeahead.astro:123-162` (`taRender`) — up to 12 results render in a
  `max-height: 340px` scrollable list (`word-atlas.css:201-202`); ArrowUp/ArrowDown move
  `aria-activedescendant` but the active option is never scrolled into view, so keyboard users
  navigate blind past the fold.
- Minimal fix: after render, `activeOption?.scrollIntoView({ block: 'nearest' })` when active ≥ 0.

## LOW

### 11. Small a11y/copy gaps in practice home & cloze [FIXED — batch]

- `LexiconPractice.tsx:2231` — storage warning renders with no live-region role (the adjacent
  pool-miss warning has `role="status"`). → `role="alert"`.
- `LexiconPractice.tsx:2370-2387` — session-budget buttons announce as bare "10" / "20". →
  Ukrainian `aria-label` («10 карток на сесію» / «20 карток на сесію»).
- `LexiconPractice.tsx:2389-2402` — «Почати сесію» not disabled while loading; double-click fires
  `startSession` twice. → `disabled={loading}`.
- `LexiconPractice.tsx:3213-3221` — cloze input lacks mobile typing hints; iOS/Android keyboards
  autocapitalize/autocorrect Ukrainian answers. → `autoCapitalize="off" autoCorrect="off"
  spellCheck={false} lang="uk"` (16 px font already prevents iOS zoom — good).

### 12. New-tab links don't say so [FILED]

- «Відкрити в Атласі →» (`LexiconPractice.tsx:3047`, `:3132`, `:3273`) uses `target="_blank"`
  with no indication to sighted or screen-reader users. Minimal fix: append «(нова вкладка)» to
  the link's `aria-label`. Not fixed here (copy churn across three feedback panels; folded into a
  later pass with the word-page work).

### 13. Typeahead Escape clears the whole query [FILED]

- `AtlasTypeahead.astro:310-315` — Escape wipes the input rather than just closing the listbox.
  Common combobox behavior is close-first, clear-second. Low severity; the clear is at least
  recoverable by retyping.

### 14. `AtlasRuntimeStatus` byte formatting uses English "MB" [FILED]

- `AtlasRuntimeStatus.astro:63` — `formatBytes` prints "MB"; Ukrainian convention is «МБ». Only
  shown in the non-hydrated fallback detail line.

### 15. `DailyWords` level group has an English aria-label [FILED — adjacent surface]

- `site/src/lexicon/DailyWords.astro:34` — `aria-label="Learner level"` announced in English.
  DailyWords is mounted only by the words-of-the-day hub (`pages/words-of-the-day.astro`), which
  is outside this PR's enumerated scope. Minimal fix when touched: `aria-label="Рівень учня"`.

### 16. Alphabet letter buttons are 36 px tap targets [FILED]

- `AtlasFullIndex.astro:616-619` — `.atlas-letter-link` is 2.25 rem (36 px); passes WCAG 2.5.8 AA
  (24 px) but below the 44 px platform guideline. Bumping to 2.5–2.75 rem keeps the sticky bar
  reasonable (33 letters wrap anyway). Polish, not a blocker.

---

## OUT-OF-SCOPE-FOR-THIS-PR — word page (`[lemma].astro` / `WordAtlasArticle.astro`)

These files are being reworked on another in-flight branch. Findings recorded for that branch's
author; **not** fixed here.

### W1 (high) — Etymology timeline stages are click-only

`WordAtlasArticle.astro:801-804` + `:1184-1194` — `ety-stage` divs swap the etymology note on click
but are plain `<div>`s: no `role="button"`, no `tabindex`, no keydown handler. Keyboard/switch
users cannot reach per-stage notes. Minimal fix: real `<button type="button">` stages +
`aria-live="polite"` on the note output.

### W2 (med) — English UI strings on a Ukrainian-only page

`WordAtlasArticle.astro:711` (`· keywords:`), `:1140` (`<h2>Wikipedia</h2>`), `:1169` (`manifest:`),
plus raw Latin track codes (`HIST M03`, `ISTORIO`, `OES`, `RUTH`) in the «У курсі» module IDs
(`:1114`, `:292-305`). Minimal fix: «ключові слова», «Вікіпедія», «маніфест»; map track codes to
Ukrainian labels.

### W3 (med) — `target="_blank"` links with no new-tab indication, inconsistent behavior

Source pills (`:754`), synonym/antonym/homonym/paronym source links (`:964`, `:974`, `:1001`,
`:1029`), literary attestation (`:1061`), wiki links (`:1147`, `:1154-1155`) open new tabs with no
indicator; idiom sources (`:1046`) and external-material links (`:1099`) are external but open
same-tab. Minimal fix: consistent «(нова вкладка) ↗» + aria-label; one behavior for external links.

### W4 (med) — Paradigm tables lack header semantics

`WordAtlasArticle.astro:821`, `:837`, `:851`, `:869`, `:888` — header rows are bare `<tr><th>`
directly under `<table>` (implicit `<tbody>`), no `scope="col"`, no `<caption>`; verb tense tables
are unidentifiable to screen readers. Minimal fix: `<thead>` + `scope="col"` + `<caption>`.

### W5 (med) — English translation terms not marked `lang="en"`

`WordAtlasArticle.astro:1130-1131` — `.en-side`/`.en-term` spans inherit the page's Ukrainian
`lang`; TTS reads English glosses with Ukrainian rules. Minimal fix: `lang="en"` on the container.

### W6 (low) — Heading levels skip `<h2>` → `<h4>`

`WordAtlasArticle.astro:1043`, `:1083`, `:1099`, `:1144`, `:1151` — card titles under `<h2>`
sections use `<h4>`. Minimal fix: `<h3>`.

### W7 (low) — Overview-card ready/pending state is color + cryptic glyph only

`WordAtlasArticle.astro:721-725` — `ready`/`pending` conveyed by color and an `aria-hidden`
`✓`/`·`; the `·` is meaningless, AT gets no explicit state. Minimal fix: visually-hidden
«готово»/«очікує» text + a real pending glyph.

### W8 (low) — Synonym glosses exposed only via `title`

`WordAtlasArticle.astro:936` — per-member gloss is hover-only (`title={member.gloss?.text}`),
invisible to keyboard/touch. Minimal fix: visible small text or an accessible disclosure.

Checked and intentionally not flagged: severity color boxes pair color with icons + text (not
color-only); the `form_of` info box; `[lemma].astro` route frontmatter/description generation.

---

## What this PR implements (8 focused changes)

| # | Change | Findings | Files |
|---|--------|----------|-------|
| 1 | Interactive-target guards on window key handlers | 1 | `PracticeFlashcard.tsx`, `LexiconPractice.tsx` |
| 2 | Remove post-flip auto-focus to «Добре» | 4 | `PracticeFlashcard.tsx` |
| 3 | Digit shortcuts (1–4) for drill/choice options | 2 | `LexiconPractice.tsx` |
| 4 | Focus «Далі →» on wrong-answer dwell | 5 | `LexiconPractice.tsx` |
| 5 | English-leak gating + Ukrainian copy (summary, title, attribution, cloze lemma cue) | 3 | `LexiconPractice.tsx`, `PracticeSessionSummary.tsx` |
| 6 | Clear auto-advance timer on exit/unmount | 6 | `LexiconPractice.tsx` |
| 7 | Cloze case-phrase grammar + next-due units + home/cloze a11y batch | 7, 8, 11 | `LexiconPractice.tsx` |
| 8 | Atlas browse «ще N записів» + typeahead scroll-into-view | 9, 10 | `AtlasFullIndex.astro`, `AtlasTypeahead.astro` |

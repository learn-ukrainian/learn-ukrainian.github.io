# Practice learner layout — UX critique (Opus)

Review date: 2026-08-03. Base commit: `2ac5fe6a32`.

Scope: the learner-facing layout of `/words-of-the-day/practice/` — the idle
setup dashboard and the in-session stage. This is a **critique, not a redesign**.
Every fix proposed here reuses an existing class, token, or component already in
the tree. No new design system, no new component family, no new copy dictionary.

Read: `site/src/components/LexiconPractice.tsx` (4,477 lines),
`site/src/lib/lexicon/srs.ts` (2,886 lines), plus the stylesheet that actually
renders them (`site/src/pages/words-of-the-day/practice.astro`), the four child
components on the critical path (`PracticeFlashcard`, `PracticeStress`,
`PracticeDailyDeck`, `PracticeSessionSummary`), the accepted spec
(`docs/practice/K3-BUILD-SPEC.md`), and the e2e gates in
`site/e2e/atlas-practice.spec.ts`.

**Verification status — read this before acting on any geometry claim.**
Findings are read from source. I did not render the page: this worktree is
sparse (no `curriculum/`, no `site/node_modules`), so an Astro build and the
Playwright suite cannot run here. Claims about *what the code does* are
code-backed and cited. The one claim about *pixels on screen* (P0-1) is a box-model
computation from the CSS, explicitly flagged, and must be settled by re-running
HARD-1/HARD-2 rather than by trusting this document.

---

## Who "non-power-user learner" means here

Someone who arrives from the Atlas or a bookmark, has not read a manual, is on a
laptop or a phone, does not know what FSRS is, and has roughly two minutes of
patience before deciding the page is broken. They will not hover to discover
things, will not press keys they were not shown, and will read the first
interactive control on the page as "the thing I am supposed to do".

That last sentence is where most of the P0 list comes from.

---

## Findings at a glance

| # | Finding | Theme |
| --- | --- | --- |
| P0-1 | The first two controls on the page are Google Drive sync and deck management | Obvious primary CTA |
| P0-2 | Custom-deck mode counts are inflated — every mode claims content it lacks | Honest empty modes |
| P0-3 | An empty mode is still tappable, dead-ends, and is invisible to screen readers | Honest empty modes |
| P0-4 | Words of the Day is decorative — the session does not draw from it | Obvious primary CTA |
| P0-5 | Flashcard self-grading ships with no visible instruction and no at-rest colour | Visible helpers |
| P0-6 | The cloze wrong-case loop has no exit and no "show me the answer" | Visible helpers |
| P0-7 | The four stat tiles mix two different denominators | Honest empty modes |
| P1-1 | The session time estimate is the one number allowed to truncate | Visible helpers |
| P1-2 | Mode descriptions are unreachable on touch | Visible helpers |
| P1-3 | Digit shortcuts exist on some option lists and not others | No required shortcuts |
| P1-4 | The two new bars bypass the locale contract; the Drive button is Ukrainian-only | Visible helpers |
| P1-5 | Two consequential controls sit at 40px against a 44px page floor | Large targets |
| P1-6 | Daily counters encode state in colour alone | Honest empty modes |
| P1-7 | The daily preview card announces "Tap to flip" instead of the word | Visible helpers |
| P1-8 | Pressing Start gives no in-place feedback; the loading card renders a bare `—` | Visible helpers |
| P1-9 | The summary Score silently drops every `hard` rating | Honest empty modes |
| P1-10 | The stress verdict is a bare ✓ / ✗ glyph with no words | Visible helpers |
| P1-11 | Dead progress code: the "today ring" is computed and never rendered | Visible helpers |

---

## P0

### P0-1 — The first two controls on the page are account sync and deck management

A learner opening the page meets, in this order: a blue button reading
«Увійти та синхронізувати з Google Drive», then a bar headed «Колоди та
добірки слів» with a «Менеджер колод / Імпорт» button and a row of deck chips.
Only after those does the hero, the stats, the words, and the actual
«Почати заняття» CTA appear.

Both bars are rendered *before* `.k3-practice-dashboard` and *outside* its grid
— `LexiconPractice.tsx:3270` (Drive) and `:3285` (deck filter), with the
dashboard opening at `:3373`. The desktop grid at `practice.astro:1023-1051`
therefore cannot place them; they simply push everything below.

Three things make this a P0 rather than a nitpick:

1. **It inverts the intended hierarchy.** The dashboard's own grid was tuned to
   pair the deck preview with the session panel specifically so the CTA clears
   the fold — the reasoning is documented in the stylesheet at
   `practice.astro:1006-1022`, citing a measured 932px CTA position at
   1366×768. Two unmeasured bars were then inserted above all of it.
2. **It is out of the accepted scope.** `K3-BUILD-SPEC.md` §9 lists "account
   synchronization" among the things that "ship later and must not expand these
   chunks". The first control on the learner's page is now account sync.
3. **It puts the binding gate at risk.** HARD-1 and HARD-2
   (`atlas-practice.spec.ts:211` and `:230`, helper at `:162`) assert
   `window.scrollY === 0` and `rect.bottom <= 768` for both Start and Resume at
   1366×768.

   Box-model estimate for what was added above them, using the 44px button floor
   from `practice.astro:106-115`: Drive bar ≈ 12 + 44 + 16 = **72px**; deck bar ≈
   16 + 12 + 44 + 8 + 44 + 12 + 16 = **152px**. Together ≈ **224px**. Whether
   that actually breaks the gate depends on the current hero and preview heights
   — **this is the one number in this document that must be measured, not
   reasoned about.** Run HARD-1/HARD-2 before and after any fix.

**Fix, no new design system.** Move both bars below the mode grid and collapse
them behind the disclosure pattern the page already owns —
`.k3-practice-sources` (`practice.astro:1307-1326`) is exactly this: a
`<details>` with a 44px summary, used for secondary material. Deck choice is a
returning-learner action; account sync is a power-user action. Neither is the
first thing a learner should be asked to decide.

### P0-2 — Custom-deck mode counts are inflated

`ensureDeckCustomSetCoverage` gives every unmatched custom-deck key the full
mode list:

```
modes: hasCloze
  ? ['flashcards', 'cloze', 'stress', 'classify', 'paradigm', 'synonym', 'paronym', 'heritage']
  : ['flashcards', 'stress', 'classify', 'paradigm', 'synonym', 'paronym', 'heritage'],
```

— `LexiconPractice.tsx:307-309`. That claim is made regardless of whether any
stress, classify, paradigm, synonym, paronym, or heritage item exists for the
word. `modeCounts` (`:2066-2074`) then counts `item.modes`, so the mode grid
prints those numbers as fact.

Concretely: a learner imports a five-word list, sees `5` on the Heritage card,
taps it, and lands in an active session whose only content is
«Усі картки повторено» (`practice.allCaughtUp`). The count promised five
exercises and delivered zero.

This is the exact failure mode the count badge was added to prevent — the
comment at `:2061-2065` says so: "instead of mixed silently collapsing toward
whichever modes happen to have content and leaving an empty tap as the only way
to discover a mode has nothing".

**Fix.** Derive the custom-deck mode list from resolved drill content the same
way the built shards do, or — cheaper and still honest — assign only
`['flashcards']` (plus `'cloze'` when `clozeIds` is non-empty) to keys with no
practice-core match, and let real modes appear once real content resolves.

### P0-3 — An empty mode is still tappable, dead-ends, and is invisible to screen readers

Three separate gaps on the same control:

- `data-mode-empty='true'` only sets `opacity: 0.55`
  (`practice.astro:1629-1631`). The button is not `disabled`, carries no
  explanation, and `onClick` still calls `startFocusMode`
  (`LexiconPractice.tsx:3593`).
- The learner who taps it gets an *active session phase* that renders a muted
  sentence — `practice.clozePreparing`, `practice.heritagePreparing`,
  `practice.paronymPreparing`, or the generic `practice.allCaughtUp`
  (`:3711-3727`). They must find «← Додому» to get out.
- The count badge is `aria-hidden="true"` (`:3599`). A screen-reader user gets
  no count, and dimming is not conveyed at all — so for them the mode grid has
  no emptiness signal whatsoever.

**Fix.** Set `disabled` and `aria-disabled` when `modeEmpty`; replace the
`.k3-mode-step` line for that card with a short "no exercises yet" string added
to `CHROME_STRINGS` in both locales; drop `aria-hidden` from the badge and give
it an accessible name. All four use existing structures.

### P0-4 — Words of the Day is decorative; the session does not draw from it

The daily zone is the visual anchor of the page: its own 340px column on desktop
(`grid-area: words`, spanning four grid rows, `practice.astro:1028-1033`), a
flippable preview card, a 12-row disclosure, per-row "why this word" lines.

The session ignores it. `beginSession` plans from
`filterIndexByDeckFilter(loadedDeck.index, …)` (`LexiconPractice.tsx:2686-2693`)
and `selectNextPracticeItem` runs against `selectionDeck` (`:2102-2135`), which
is the level index narrowed by the deck filter only. `dailySnapshot` never
enters the pool. The daily rows link out to Atlas
(`PracticeDailyDeck.tsx:280-291`); there is no "practise this word" affordance
anywhere in the zone.

The disconnect is already being papered over downstream: the summary filters
`advancedToReview` and `deferredLemmas` down to `dailySnapshotIds`
(`LexiconPractice.tsx:3169-3182`), so a learner who just advanced eight words
that happen not to be in today's twelve sees an empty "Advanced to review" list.

For a non-power learner the read is simple and wrong: "these are my words for
today → I press the big button → I get different words."

**Fix, pick one — both reuse existing machinery.** Either (a) add a "practise
these" action in `.daily-deck-header` that starts a session scoped to the
snapshot ids, using the deck-filter path that already exists; or (b) if the zone
is meant to stay a reading surface, retitle it so it stops implying it is the
session, and stop filtering the summary by snapshot membership. Option (b) is
one string and one deletion; option (a) is the honest one.

### P0-5 — Flashcard self-grading ships with no visible instruction and no at-rest colour

Flashcards are the default mode and the first thing a Mixed session is likely to
show. What the learner sees: a 300px card with a single Ukrainian word, and
below it four identical grey buttons at 45% opacity.

- The "tap to flip" hint exists **only** in the `aria-label`
  (`PracticeFlashcard.tsx:108`). Nothing visible tells a sighted learner the
  card flips.
- The rating buttons are rendered visible-but-`disabled` before flip
  (`:143`), styled `opacity: 0.45; cursor: not-allowed`
  (`practice.astro:926-930`).
- Their semantic colours are declared on `:hover` **only** —
  `.rate-btn[data-rate="again"]:hover` etc., `practice.astro:466-484`. On touch
  there is no hover. At rest on desktop there is no hover. So Again / Hard /
  Good / Easy are four visually identical boxes at the single highest-cognition
  moment in the app.
- The interval previews (`‹10 хв›`) that would make the choice meaningful only
  render after flip (`PracticeFlashcard.tsx:151`).

Spec §7 requires that "hover behavior has an equivalent focus behavior"; here
there is no focus equivalent and no rest state either.

**Fix.** Move the four `data-rate` colour rules onto the base selector (keep
hover as an intensity change) and add the matching `:focus-visible` rules. Add
the flip hint as visible text using the existing `.flashcard-subtitle` slot on
the front face, sourced from the `practice.tapToFlip` key that is already
defined in both locales.

### P0-6 — The cloze wrong-case loop has no exit

`submitCloze` (`LexiconPractice.tsx:3054-3116`) branches three ways. The
`caseMiss` branch clears the input, sets a corrective message, and **does not
lock**:

```js
if (caseMiss) {
  if (!clozeAttemptRecorded) { recordReview(selection, 'hard'); setClozeAttemptRecorded(true); }
  setClozeInput('');
  setClozeFeedback({ kind: 'case-miss', … });
  return;
}
```

`isWrongCaseAnswer` (`srs.ts:1904-1914`) returns true for the nominative and for
any form in `lemma.paradigm.cases`. So a learner who knows the word but not the
case can cycle through its paradigm indefinitely — each attempt clears the box
and re-asks. There is no attempt counter, no reveal, no skip.

The only escape is to type something *outside* the paradigm, which falls to the
`wrong-word` branch, locks, and scores as a miss. A learner has to guess wrong
in a specific way to get unstuck.

Two aggravating details in the same branch: `setClozeInput('')` silently wipes a
value the learner may have just placed by tapping a chip (chips only populate
the input and return — `:3057-3061`), and the corrective message is built by
`casePhraseAccusative` (`:1346-1348`), which hardcodes the accusative frame
«у {case} відмінок» for every case.

**Fix.** Cap case-misses at two, then lock and reveal `cloze.form` through
`PracticeFormRail`, which is already mounted for this mode on lock
(`:3881-3894`) and already has "Джерело / Ваша відповідь" rows. Stop clearing
the input on case-miss — select it instead, so a chip tap is not destroyed.

### P0-7 — The four stat tiles mix two different denominators

The stats row (`LexiconPractice.tsx:3409-3426`) reads: Due, New, Done, Streak.

- **Due** is `countDueReviewCards(indexForStats)` — and that function iterates
  *every mode of every index item* (`srs.ts:2110-2116`). One lemma with eight
  modes contributes up to eight. `indexForStats` is the whole cumulative level
  index (`LexiconPractice.tsx:2057`).
- **New** and **Done** are `dailyRows.pendingNew.length` and
  `dailyRows.done.length` — rows inside today's twelve-item snapshot
  (`:3133-3139`, capped by `DAILY_PRACTICE_DECK_SIZE = 12`).

So the first tile counts cards across the learner's entire level and the next
two count rows in a twelve-word set, side by side, in identical styling, with no
label distinguishing them. A B1 learner can plausibly see `Due 340 · New 4 ·
Done 2` and have no way to reconcile those numbers.

**Fix.** Put all four on the same basis. The cheapest honest version: scope the
Due tile to the same snapshot — `dailyRows.pendingDue.length` is already
computed and already shown inside the daily disclosure counters
(`PracticeDailyDeck.tsx:228`), so the tile would simply agree with it — and
surface the level-wide backlog, if it is wanted at all, in the session-scope
line where a bigger number reads as context rather than as a task list.

---

## P1

**P1-1 — The one honest time estimate is the one allowed to truncate.**
`.k3-session-scope` sets `white-space: nowrap; text-overflow: ellipsis`
(`practice.astro:1187-1197`) inside the 340px column. Its content is
«5 до повторення + 3 нових ≈ 3 хв» (`LexiconPractice.tsx:3504-3507`) — the
only "how long will this take" signal on the page. Allow two lines instead;
the card grows, which the layout already tolerates.

**P1-2 — Mode descriptions are unreachable on touch.** `.k3-mode-detail` updates
on `onMouseEnter`/`onFocus` (`:3589-3592`) and tapping a card starts the session
immediately (`:3593`). A phone learner can never read what a mode does before
committing to it. Render the description inside each card at small size, or
require a second tap to confirm — the `.k3-mode-step` slot is already there.

**P1-3 — Digit shortcuts are inconsistent.** Nothing is shortcut-only, which is
correct and worth keeping: every path has a visible control, digits are shown as
`.mc-key` badges, and «Далі →» exists alongside Enter. But `DigitChoiceShortcuts`
is mounted for choice and drill lists (`:3934`, `:4050`) and not for heritage or
paronym (`:4245-4258`, `:4147-4160`), whose options also render without the
number badge. Same interaction, two behaviours.

**P1-4 — The two new bars bypass the locale contract.** They use inline
`chromeLocale === 'uk' ? … : …` ternaries instead of `CHROME_STRINGS`
(`:3288`, `:3296`, `:3306`, `:3314`), and the Drive button label (`:3279`) plus
every `driveSyncMsg` value set in `handleGoogleDriveSync` (`:1490`, `:1493`,
`:1497`, `:1500`) are Ukrainian-only with no English form — «Авторизація через
Google...», «Синхронізація з Google Drive...», «Успішно! Синхронізовано колод:
N», «Помилка: …». Spec §7 "Locale-pair completeness" requires both records for
every chrome string. An English-chrome learner gets untranslated Ukrainian
system copy — which is different from Ukrainian *learning content* and is not
covered by the immersion policy.

**P1-5 — Two consequential controls sit below the page's own 44px floor.**
`.lexicon-practice button` sets `min-height: 44px`
(`practice.astro:106-115`) and nearly everything honours it. The exceptions are
`.k3-switch-offer-actions button` at 40px (`:1302-1305`) — the Yes/Keep decision
for discarding a session — and `.lexicon-weak-chip` at 40px (`:891-892`). Raise
both to 44px. (Target sizing is otherwise in good shape: options 56px, cloze
chips 48px, mode cards 48px, daily nav 44×48. The general problem on this page
is affordance, not hit area.)

**P1-6 — Daily counters encode state in colour alone.** The three counters in
the disclosure summary render bare numbers whose only differentiator is
`.counter.due` / `.new` / `.done` colour (`PracticeDailyDeck.tsx:226-236`,
`practice.astro:1470-1489`), with no text and no accessible name. Spec §7:
"State markers and pair identity use text/shape plus color."

**P1-7 — The daily preview card announces the wrong thing.** It is
`role="button"` with `aria-label={chromeString(chromeLocale, 'practice.tapToFlip')}`
(`PracticeDailyDeck.tsx:152-154`), so the accessible name is "Tap to flip" and
the word itself is suppressed. `PracticeFlashcard` gets this right —
`` `${card.front} — ${tapLabel}` `` (`PracticeFlashcard.tsx:108`). Copy that.

**P1-8 — Pressing Start gives no in-place feedback.** `{loading && …}` renders
after the entire dashboard (`LexiconPractice.tsx:3613-3617`), so on a slow
connection the only signal at the button is `cursor: wait` and 72% opacity
(`practice.astro:1248-1252`). Separately, the daily-deck loading placeholder
renders a card whose word is a literal `—` (`:3444-3450`), which reads as broken
content rather than as loading.

**P1-9 — The summary Score silently drops every `hard` rating.** `sessionCorrect`
increments on `good`/`easy`, `sessionLapsed` on `again`
(`LexiconPractice.tsx:2899-2904`), and the summary computes
`total = correct + lapsed` (`PracticeSessionSummary.tsx:31`). A learner who
rates a full session «Важко» sees `Score 0/0`.

**P1-10 — The stress verdict is a bare glyph.** On lock, `PracticeStress` renders
`✓` or `✗` and nothing else (`PracticeStress.tsx:74-84`). The correct vowel does
get a `.correct` class, so the information is on screen — but the verdict line
itself carries no words in either locale.

**P1-11 — Dead progress code.** `todayDenominator`, `todayPct`, and
`todayRingStyle` are computed (`LexiconPractice.tsx:3140-3153`) and never
rendered; the comment at `:1776-1781` still describes "the «До повторення» tile
+ today ring" as a live feature. Also note `completedToday` starts at `0` on
every page load (`:1455`) and is never rehydrated, so any ring restored from
this state would reset to zero on reload. Either restore the ring with a
persisted numerator or delete the three computations.

---

## What already works — do not regress this

Worth stating plainly, because several of these are unusual to get right and a
fix in the wrong place could undo them:

- **Explicit progression.** Nothing auto-advances. Every mode parks its outcome
  and waits for «Далі →» or Enter, and the double-advance race is closed via a
  ref rather than state (`LexiconPractice.tsx:3003-3012`). This matches spec §6
  exactly.
- **Focus is managed after an answer.** `useLayoutEffect` scrolls to top and
  focuses the advance button before paint (`:2230-2234`), so a keyboard learner
  never loses their place behind a tall prompt.
- **Wrong answers reveal the right one.** Choice, drill, heritage, and paronym
  all mark the correct option on lock (`:3970`, `:4249`, `:4151`).
- **No shortcut-only path.** Every keyboard affordance has a visible control.
- **Deck and level switches are guarded.** A tap during an active or resumable
  session parks the choice and asks inline rather than silently recomputing
  (`:2825-2870`), and the accepted value is threaded through as an explicit
  override rather than raced against state.
- **Resume fails closed.** A snapshot from a different level, deck, or day is
  never replayed (`srs.ts:2414-2436`), and sessions are isolated per mode.
- **Storage failure is surfaced, not swallowed** (`:3210-3217`).
- **Target sizes are broadly compliant** — the 44px floor is real and mostly
  honoured.

---

## Parallel Kimi K3 review — agreements and disagreements

**No such review is in hand.** I searched `reviews/`, `review/`, `docs/`, and
`briefs/` for a Kimi artifact covering this surface and found none. Everything
below is therefore stated as a **prediction with its assumption named**, so it
can be checked against the real review when it lands rather than mistaken for a
report of one.

Assumptions I am reasoning from:

1. "K3" refers to the accepted redesign spec `docs/practice/K3-BUILD-SPEC.md`,
   and the parallel review is a Kimi-family model reviewing the same two files
   against learner-UX criteria.
2. It reviewed the same base commit and the same two files named in the brief —
   which means, like me, it would have had to reach outside them for the
   stylesheet to say anything about geometry or colour.
3. It has no live render either.

### Where I expect to agree

- **The mode grid's empty-state handling is the clearest defect.** It is visible
  in `LexiconPractice.tsx` alone, without the stylesheet. Any competent review
  finds it. I would expect near-identical wording.
- **Self-graded flashcards are the wrong first experience for a beginner.** Also
  visible from the component alone.
- **The stat tiles are confusing.** Reachable from `srs.ts` by reading
  `countDueReviewCards` next to `DAILY_PRACTICE_DECK_SIZE`.
- **The file is too large.** 4,477 lines with the island, five sub-components,
  and a dozen pure helpers in one module. I agree, and I deliberately left it
  out of the findings table: it is a maintainability finding, not a learner-UX
  one, and this brief asked for the latter.

### Where I expect to disagree, and would hold

- **On target sizes.** I would expect a review working from JSX alone to flag
  the inline-styled buttons — the clear-focus button at `padding: '4px 8px',
  fontSize: '0.8rem'` (`:3251-3265`) and the deck-manager button at
  `padding: '0.25rem 0.6rem'` (`:3294`) — as sub-44px targets. **They are not.**
  `.lexicon-practice button { min-height: 44px }` (`practice.astro:106-115`)
  applies and inline `padding` does not override `min-height`. Their hit area is
  compliant; only their *visual weight* is small. The genuine sub-44px controls
  are the two named in P1-5, and neither is reachable without opening the
  stylesheet. I would hold this one firmly and ask for the computed box.

- **On "add hints / add a tutorial".** The likely recommendation for a beginner
  audience is more onboarding copy. I would push back: spec §7 has a **zero
  rule-copy gate** — "no new visible string may narrate the implementation
  rules" — with an allow-list test behind it. The fix for "the learner does not
  know what Again/Hard/Good/Easy mean" is the interval preview that already
  exists plus colour at rest, not a paragraph of instructions. I would trade
  every proposed explanatory sentence for a visible state.

- **On the Drive and deck bars.** A review reading only the two named files sees
  two ordinary-looking JSX blocks and is unlikely to weight them heavily. I rank
  the Drive bar as the single worst learner-facing decision on the page,
  because it is out of the accepted scope (§9), it is Ukrainian-only, and it
  sits above a fold position that was fixed by measurement and is now protected
  by a hard gate. If the parallel review ranks this below P1, I would contest
  it.

- **On the daily-deck disconnect (P0-4).** This one needs `beginSession`,
  `selectNextPracticeItem`, and `summaryStats` held in mind at once across both
  files. If the parallel review missed it, that is not a defect in the review —
  it is the cost of a 7,300-line reading surface. I would raise it rather than
  treat silence as disagreement.

### Where I would concede quickly

- Any concrete geometry claim, mine included, loses to a live measurement. P0-1
  is the case in point: my 224px is arithmetic on a stylesheet, and a rendered
  `boundingBox()` beats it.
- If the parallel review finds real learner-facing bugs inside the exercise
  components I only skimmed — `MatchUp`, `PracticeFormRail`,
  `LexiconCustomDeckManager` — I have no basis to argue and would fold those in.
- If Words of the Day was *designed* as a reading surface rather than as the
  session's source, then P0-4 is a copy fix, not an architecture fix, and I
  would drop it to P1.

---

## Suggested order of work

The P0s are not equally expensive. Rough sequencing, cheapest-first within
impact:

1. **P0-3** (disable empty modes) and **P0-7** (one denominator) — small,
   contained, immediately more honest.
2. **P0-1** (move the two bars behind the existing disclosure) — small diff,
   biggest single change to what a learner sees first. Gate on HARD-1/HARD-2.
3. **P0-5** (rating colours at rest + visible flip hint) — CSS plus one span.
4. **P0-6** (cloze reveal after two case-misses) — real logic, worth the care.
5. **P0-2** (stop over-claiming custom-deck modes) — touches deck resolution;
   needs its own tests.
6. **P0-4** (daily/session relationship) — decide the intent first; the fix
   follows from that decision, not the other way round.

The P1s are mostly one-line fixes and can ride along with whichever P0 touches
the same file.

# Atlas Practice Hub — production spec

> **IA UPDATE (2026-06-25, shipped #3811):** the practice surface was **re-homed from the Word Atlas to
> Words of the Day**. The Atlas (`/lexicon/`) is now the dictionary (search-first + the restored full А-Я
> browse at `/lexicon/browse/`); Words of the Day (`/words-of-the-day/`) is the daily learning surface; and
> practice lives at **`/words-of-the-day/practice/`** as WoD's drill arm. The interaction/answer model below
> is UNCHANGED — only the surface's home + branding moved. `practice-hub.html` here reflects the new IA
> (Atlas search · А–Я browse · Words of the Day · Practice views).

> The PoC `practice-hub.html` (this folder) is the **interaction source-of-truth**. The production React
> components must match the answer model + variety behaviours here. Design locked with the user 2026-06-24,
> then **revised against a 3-agent fleet review (codex / agy / cursor)** — their corrections are folded in
> and marked ⟦fleet⟧.

## 0. Headline requirement — the session must FEEL varied, WITHOUT fighting the scheduler

Learners must feel the tasks keep changing — never "the same kind repeating." BUT ⟦fleet: all 3⟧ variety is
**secondary to spaced-repetition scheduling**. The anti-monotony selector reorders and decorates; it must
never delay a due card or block re-showing a just-failed (lapsed) one. Precedence and the testable rules are
in §6.

## 1. Architecture — static, build-time, no backend

GitHub Pages is static; no server generates exercises at runtime, and we must not invent/template sentences
in the browser (quality bar). Pattern: **move generation to build time → static JSON; assemble client-side.**

- **One prebuilt practice pool, CEFR-level-segmented** (`practice-*.A1.json`, …), lazy-loaded.
- ⟦fleet codex/cursor⟧ **Shard the deck** so cloze content isn't paid for unless used:
  `practice-index.{lvl}.json` (ids + scheduling metadata), `practice-lexemes.{lvl}.json` (gloss/ipa/paradigm),
  `practice-cloze.{lvl}.json` (sentences). Load cloze only when cloze is enabled. **CI raw+gzip size budget
  per file per level.**
- **Scheduling state is client-side**: `ts-fsrs` (FSRS-6) + `localStorage`. ⟦fleet codex⟧ The **FSRS card unit
  is `lemmaId + mode`** (NOT per sentence/case) — compact deltas keyed by stable ids + `deckVersion`
  invalidation; move to **IndexedDB** if state can exceed a few MB.
- ⟦fleet codex⟧ **Deterministic build**: seeded RNG per `deckVersion`; deterministic ordering; snapshot tests
  for representative entries; schema validator. No unseeded randomness in deck generation.

## 2. Deck schema + field sourcing

| Field | Source |
|---|---|
| `lemmaId`, `lemma`, `lemmaPlain`, `ipa`, `gloss`, `pos`, `cefr`, `heritage`/`severity` | manifest enrichment |
| `paradigm.cases.<відмінок>.{singular,plural}` | manifest `enrichment.morphology.paradigm` |
| `cloze: [{ clozeId, sentenceFrameId, sentence, blankCase, form, caseRule, clozeEn }]` | sentence from **reviewed module vocab cards**; `form`+`blankCase` from paradigm; `caseRule` from a curated case→trigger map |

- **Eligibility**: `is_practice_eligible` (gloss + CEFR/course anchor, no derived forms, no surzhyk) —
  `scripts/audit/lexeme_filter.py`.
- ⟦fleet codex⟧ **Stable ids**: `clozeId` + `sentenceFrameId` assigned at build time. The variety selector
  tracks IDs, never sentence strings (text edits must not break "don't repeat a frame").
- ⟦fleet codex⟧ **Reviewed-source allowlist, fail-closed**: the generator only ingests a vocab card whose
  provenance is in an explicit reviewed-status/path allowlist; missing provenance → skip (never emit).
- ⟦fleet codex⟧ **VESUM ambiguity**: store morphology metadata; if a target `form` is valid for multiple
  cases/lemmas (non-discriminative), **skip that cloze item (fail-closed)** — for case-demanding cloze a non-discriminative target form is unusable (consistent with §7).
- ⟦fleet agy⟧ **CEFR-appropriate sentences (A1/A2)**: prototypical, transparent case triggers only.
  Accusative direct object («Я бачу брата»), Locative static position («Вона у школі»). **Avoid** partitive
  genitive / complex quantifiers («буханець хліба» = B1+) and **lexicalised chunks** (fixed greetings like
  «доброго ранку» — retrieved whole, not via grammar, so worthless as case practice). Sentence level ≤ word
  level.

## 3. Exercise modes + data needs

| Mode | Needs | Coverage |
|---|---|---|
| Flashcards | lemma + gloss + paradigm | every eligible word (free) |
| Matching | lemma + gloss | every eligible word (free) |
| Choice (meaning MC) | lemma + gloss | every eligible word (free) |
| **Cloze** | sentence + `blankCase` + `form` + `caseRule` | only words with a vetted sentence |

⟦fleet cursor⟧ **Cloze is scarce** (most words are recognition-only) → it has its own `clozeDue` sub-queue and
is **soft-capped at ~25% of a session** (a weighting guideline, not a hard ceiling — ⟦fleet codex⟧ **lapsed / urgent-due cloze is EXEMPT** so the scheduler is never starved; unless the learner opts into a "grammar focus"). Build emits
`clozeCoverage` per level; **CI warns if an A1 deck is <10% cloze-eligible.**

## 4. Cloze answer model (case-demanding, SCAFFOLDED) — revised ⟦fleet all 3⟧

The cloze still **demands the correct case form; the bare lemma is never the final accepted answer.** But it
is **not a flat "wrong"** — that demotivates A1/A2 learners (conflates *knowing the word* with *knowing the
morphology*) and, if unscored, is an SRS loophole. Three states:

| State | Visual | Scored? | Advance? | Copy |
|---|---|---|---|---|
| **Correct** (the `form`) | green | ✓ pass | yes | `✓ … (знахідний відмінок)` |
| **Wrong case** (the lemma, or any non-target case of the right word) | **amber** `role="status"` | **counts as a CASE-MISS in SRS** (card returns sooner / lower ease) — NOT a free retry | **no** — blank stays empty, chips re-enabled | `✓ Правильне слово! Тепер постав його у [місцевий]: …` + the §4a rule |
| **Wrong word** (a distractor) | red | fail (SRS) | after resolve (typed → retry; chip → reveal) | `✗ Не те слово` |

- ⟦fleet agy⟧ **Gate cloze behind recognition mastery**: a word enters cloze only after it reaches a baseline
  FSRS stability in flashcards/matching. No case-production on day-one vocab.
- **Typo/stress tolerant, case strict** (`czNorm`): forgive a missing stress mark or apostrophe variant; never
  forgive the case.
- ⟦fleet codex⟧ **One grade per presentation**: the SRS outcome is set by the **first** attempt. A wrong-case
  first attempt records the case-miss; the subsequent scaffolded correction advances the UI but does **not**
  also record a pass for that same presentation.

### 4a. Case-rule feedback — revised ⟦fleet agy⟧

Naming the case is not enough and can be wrong: «на/в» trigger **both** accusative (motion) **and** locative
(position). Feedback must **disambiguate the trigger and show the inflection**:
`на (напрямок) → знахідний (робот**а** → робот**у**)`. The curated case→trigger map supplies the
disambiguated trigger gloss + the lemma→form delta per item.

## 5. Cloze option generation (anti-gaming) — strengthened ⟦fleet codex/cursor⟧

Never let the option *shape* reveal the answer. The user's case-contrast requirement (show робота **and**
роботу so the learner discriminates the case) is kept — but hardened against tells:

- The lemma stays an option (the case contrast the user asked for); clicking it triggers the **scaffold**
  (§4), not a fail.
- ⟦fleet codex⟧ **≥2–3 oblique-looking forms per set** so "the oblique one is the answer" is not a tell.
- Modes (never exactly one same-root pair): ~two same-root pairs (answer's + a decoy word's, both declined =
  trap) / ~no pair (answer among mixed lemma|declined distractors). ⟦fleet cursor⟧ **CEFR-ramp the mix**:
  A1 ≈ 70% no-pair / 30% two-pair → 55/45 by B1.
- ⟦fleet codex⟧ **Randomise the answer's length/position** so neither betrays it.
- ⟦fleet codex⟧ **Build-time/test-time option-set VALIDATOR** for every generated set: unique normalised
  labels; answer present exactly once; no accepted alternate equals a distractor; ≥ min oblique distractors;
  no fixed answer position; option lengths within a bounded distribution; no homograph/answer-equivalent leak.
- ⟦fleet codex⟧ **Distractor buckets** (testable, not "near/far"): same POS; mixed semantic-bucket ratio;
  avoid sharing the answer's English gloss headword.

## 6. VARIETY — first-class, SRS-subordinate, testable — revised ⟦fleet all 3⟧

One **selector** produces the next item. **Precedence (merge order)** ⟦fleet codex/cursor⟧:

1. Build the **due/lapsed candidate set** from FSRS (lapsed items are highest urgency).
2. Drop only **hard** variety violations (e.g. the exact item just shown). ⟦fleet codex⟧ **Lapsed cards are
   EXEMPT** from this and from word-spacing drops — re-expose them immediately.
3. Rank remaining by **FSRS urgency**.
4. Apply soft anti-monotony as a **penalty score** (not a filter) to break ties / reorder near-equal-urgency
   candidates.
5. ⟦fleet codex/agy⟧ If too few candidates remain, **widen the due window / relax word-spacing BEFORE**
   pulling not-due cards; **lapsed items are EXEMPT from the word-anti-repeat** (re-expose immediately).

Soft variety levers (penalty score, never override scheduling):
- ⟦fleet cursor/codex⟧ **Mode**: a **penalty** (not a hard ban) discouraging the same mode within the last 3,
  **overridden by due/lapsed pressure**; **per-mode debt counters** so cloze/choice
  don't vanish behind flashcard due-volume; ⟦fleet cursor⟧ **session bootstrap** — first ~8–12 items include
  each available mode at least once.
- ⟦fleet agy⟧ **Sequence by mastery, not random rotation**: a word moves recognition→production by its own
  FSRS stability.
- **Case (cloze)**: ⟦fleet codex⟧ *conditional* invariant — *if* ≥3 cases are eligible in the candidate pool,
  the last 8 cloze items must cover ≥3; else assert max-available coverage.
- **Sentence / distractors**: rotate `sentenceFrameId`s and distractor sets; never repeat a frame back-to-back.
- ⟦fleet cursor⟧ **Perceptual variety**: track `recallDirection` (UK→meaning / meaning→UK) and choice polarity
  («що означає X?» / «яке слово означає Y?») so the *felt* shape changes, not just metadata.

**Tests**: drive ~50 selections and assert the **precedence** (due/lapsed never starved; lapsed exempt from
exact-item / word-spacing drops), and that the **soft** rules apply only when they do NOT starve
scheduling (mode-penalty respected absent due pressure; conditional case coverage; no frame immediate-repeat;
perceptual rotation), plus the §5 option-validator. Violations = build red.

## 6b. SESSION MODEL — bounded sessions, not an open faucet ⟦fable 2026-07-06, user-directed; GH #4658⟧

Practice must be a **well-defined session, not aimless practice** (user, 2026-07-06). The session layer
WRAPS the §6 selector: the selector remains the single source of "next item"; the session only counts a
budget down and stops. Session logic must never reorder or delay what the selector picks — the same
subordination §0 imposes on variety.

- **Session contract (primary CTA).** The home's primary action is one button — «Почати сесію» — with the
  scope visible before starting: «N до повторення + M нових ≈ X хв» (X from a fixed 20s/item estimate).
  Mode cards demote to a secondary "focus practice" row. Session sizes: quick 10 / standard 20 (default) /
  «до нуля» (until due-queue empty). ⟦agy 2026-07-06 F2⟧ **Interface boundary**: the session layer defines
  POOL CONSTRAINTS only (review budget, new-card allowance); the §6 selector retains total control over
  ordering within the constrained pool — the session never sequences items itself.
  ⟦agy 2026-07-06 F3⟧ **A1 scaffolding**: when the learner level is A1, session labels render with English
  subtitles («Почати сесію» / *Start session*) per the project's A1-exception design; from A2 the labels
  are Ukrainian-only — never raise English above A1.
- **New-card caps.** `newPerSession` default 8, `newPerDay` default 20 (localStorage settings; a later
  settings UI may expose them). The home separates the metrics: «До повторення: N» (reviews only) and
  «Нові сьогодні: m/20». The today-ring denominator becomes `dueReviews + min(remaining daily new
  allowance, available new)` — NEVER the whole deck (browser-verified defect: a fresh learner saw
  «0/1150 сьогодні»).
- **In-session progress + completion.** Stage bar shows «i/N». Completing the budget (or emptying the due
  queue in «до нуля») renders a **session summary**: correct/lapsed counts, words that advanced to Review
  state, streak effect, and a next-due preview («ще 12 о 18:00»), with «Ще одна сесія» / «Готово» CTAs.
  ⟦agy 2026-07-06 F1 — replaces the earlier "end-on-success extra item" idea⟧ **Failed-card closure rule**:
  a session does not close while an item rated `again` DURING this session remains unresolved — the item
  re-enters the active pool (the §6 lapsed-exemption already re-exposes it) and the budget extends past N
  by up to 5 items until each such item is answered successfully or the extension cap is reached (then the
  summary lists it under «повторимо наступного разу»). Sessions end on resolution, not on an unrelated
  success.
- **Resume.** A session snapshot `{sessionSeed, history, budget, completed, modeFilter, level, startedAt}`
  persists to `localStorage['lu-practice-session']` after every item. On mount, a snapshot younger than
  6h with budget remaining offers «Продовжити сесію (i/N)»; starting fresh discards it. This also repairs
  the variety/anti-repeat state loss on refresh (history was React-state only).
  ⟦agy 2026-07-06 F4, adjudicated⟧ Resume restores seed + history + budget counters ONLY; item selection
  recomputes against the LIVE FSRS store. The remaining queue is deliberately NOT persisted — ratings made
  before the refresh mutated card state, so a stored queue would replay stale scheduling; recomputation is
  correct-by-construction and keeps the selector the single source of "next item".
- **Reveal-gated rating + interval preview.** Flashcards: rating buttons are INERT until the card is
  flipped (browser-verified defect: rating an unseen answer is currently possible); keyboard rating keys
  likewise. ⟦agy 2026-07-06 F6⟧ Keys: `Space`/`Enter` reveal; `1`–`4` (and the existing `a/h/g/e`) rate,
  active only post-reveal; on flip, programmatic focus moves to the rating bar (screen-reader order
  follows the interaction). After reveal, each rating button shows its scheduling consequence from the
  FSRS preview («Ще раз ‹10 хв› · Добре ‹3 д› · Легко ‹7 д›») — the scheduler made visible is what makes
  SRS feel purposeful.
- **Stable stage.** The stage has a fixed min-height across item types (no interaction-zone jumping
  between tall flashcards and compact MC); in-session the page hero collapses to a compact bar
  (back · title · i/N) so controls stay above the fold at common laptop viewports.
- **Failure states.** The practice island renders an error fallback with a retry button on hydration or
  shard-fetch failure (browser-verified: a one-shot dynamic-import failure left the page permanently
  blank). Unpublished level buttons (C2 today) render disabled with «скоро».

**Tests**: session pool constraints (reviews before new within the pool; new ≤ newPerSession; daily
allowance decrements and gates) while §6 ordering tests keep passing unchanged; today-ring denominator
excludes uncapped new; completion fires at budget, with the failed-card closure extension (≤ +5, listed
in the summary when capped); snapshot round-trip restores seed/history/budget and recomputes selection
against live state; rating inert pre-flip (pointer AND keys); interval labels match `ts-fsrs` preview
output; A1 renders EN subtitles, A2+ does not; level buttons without published shards are disabled.
Violations = build red.

## 7. Quality / verification gates

- All forms **VESUM-verified at build time** (skip non-discriminative/ambiguous forms — §2).
- **Sentences from reviewed content only** (allowlist, fail-closed) — no invention, no runtime templating.
- **Option-set validator** (§5) + **seeded-RNG snapshot tests** (§1) + **`clozeCoverage` gate** (§3) + **deck
  size budgets** (§1).
- Reuse: `check_atlas_manifest_enrichment`, manifest freshness, render-verify.

## 8. What to change in PR #3777 artifacts

- `generate_practice_deck.py`: emit the §2 schema (sharded index/lexemes/cloze; stable `clozeId`/
  `sentenceFrameId`; reviewed-source allowlist fail-closed; VESUM-gate + ambiguity skip; CEFR-appropriate
  sentence selection); seeded RNG; size budgets; **replace the empty placeholder deck**.
- `srs.ts`: FSRS card = `lemmaId+mode`; add the §6 selector (precedence + lapse-exemption + per-mode debt +
  cloze ≤25% sub-queue) consuming the due-queue.
- `LexiconPractice.tsx` / cloze component: §4 three-state scaffolded model (correct / amber case-miss /
  red wrong-word; case-miss costs SRS, blank stays open, chips re-enabled); §4a disambiguated case-rule
  feedback; §5 anti-gaming + validator; recognition-mastery gate before a word enters cloze. All modes pull
  the next item from the §6 selector, not a raw shuffle.
- Counts use `uaPlural` (locked).

## 9. Drill-type expansion (v4 — GH #4383) — new modes fed by `data/atlas.db` (entry-model v1, #4378)

The 4 live modes drill recognition + one production skill (case cloze). The Atlas enrichment already
carries data for far more. Decks feed from **`data/atlas.db`** once entry-model SSG lands (plan roadmap
step 5 / #4385); until then, from the manifest export — the deck **schema** is DB-shaped either way.

**Base eligibility for every mode** (on top of per-mode gates): article `review_state = approved` AND
`visibility = public` AND `is_practice_eligible` (§2). ⟦codex v4⟧ `is_practice_eligible` (and every
`is_*_eligible` below) becomes a **deterministic DB-backed predicate** (view or builder-materialised
column on `data/atlas.db`) — prose-only predicates don't gate anything; missing/unknown ⇒ **false**
(fail-closed). Everything below inherits the locked invariants:
SRS-first precedence (§6), one grade per presentation (§4), fail-closed generation (§2/§5/§7),
seeded/deterministic build (§1), FSRS card unit = `lemmaId + mode` (§1).

| Mode (new) | Atlas data | Fill phase dep. | Eligibility gate | CEFR availability |
|---|---|---|---|---|
| `paradigm` — declension/conjugation | `enrichment.morphology.paradigm` (VESUM) | **Phase 1 (local)** | `is_paradigm_eligible` | A2 (chips) · B1+ (typed) |
| `stress` — stress placement | `enrichment.stress` | **Phase 1 (local)** | `is_stress_eligible` | A1+ |
| `synonym` — synonym/antonym match | `sections.synonyms` / `sections.antonyms` | **available NOW** ⟦v5 probe 2026-07-05: 796 prompts / 1,224 in-vocab pairs⟧ · slovnyk Phase 2 grows it | `is_synonym_eligible` | B1+ |
| `idiom` — idiom→meaning match | `sections.idioms` / phraseologism articles | Phase 1 + Phase 2 | `is_idiom_eligible` | B1+ (curated A2 exceptions) |
| `heritage` — decolonization pick | `heritage_status.curated_calque` + §6_note corrections | **Phase 1 (curated)** ⟦v5 probe: 5 pairs — ships thin, fail-closed, until calque curation⟧ | `is_heritage_eligible` | B1+ (curated A2 exceptions) |
| `classify` (v5, §9.8) — category sort | VESUM tags already in `enrichment.morphology` + `pos` | **available NOW** ⟦v5 probe: 2,214 nouns · 1,069 verbs · 598 adj⟧ | `is_classify_eligible` | A1+ (gender) · A2+ (aspect/declension) |
| `paronym` (v5, §9.9) — confusable-pair pick | curated `paronym_pair` records | **curated only** ⟦v5: ~6 module seed pairs; grows via curation⟧ | `is_paronym_eligible` | B1+ |
| `listening` — dictation | `enrichment.pronunciation.ipa` + audio | **DEFERRED** — needs an audio/TTS decision; IPA alone is not a drill. Placeholder only, NOT in v4 scope. | — | — |

> **v5 scope note (user-approved 2026-07-05):** ALL suggested modes are wanted; build order follows
> DATA-READINESS — Wave 1 decks = `stress` (4,467) · `classify` (3,881) · `paradigm` (2,180) ·
> `synonym` (1,224 pairs); `heritage` + `paronym` ship machinery fail-closed and fill as curated
> pairs land (curation lane: mine Antonenko/UA-GEC for calques, Гринчишин paronym dictionary +
> module `contrast_pair` activities for paronyms). Antonym polarity rides the `synonym` mode for
> free (43 in-vocab pairs today — thin, grows with intake). The mode union in `srs.ts` gains ALL
> six at once (§9.6) — ONE deckVersion bump; a known mode with no deck simply contributes no cards.

### 9.1 `paradigm` — slot production (declension / conjugation)

- **Item**: prompt = lemma + target slot named in Ukrainian («орудний відмінок, однина» / «2-га особа
  однини, теперішній час»); ⟦agy v4⟧ at A2 the UA term carries an EN abbreviation **subtitle gloss**
  («instr. sg») — UA-first stays hard (§4a already uses UA case names), the subtitle drops at B1.
  Answer = the slot form. A2 = chips (options are OTHER slots of the SAME
  paradigm — inherent same-root distractors; §5 validator applies: unique normalised labels, no
  answer-position/length tell). B1+ = typed with `czNorm` (stress/apostrophe tolerant, form strict).
- **Gate `is_paradigm_eligible`**: complete non-defective VESUM paradigm; a slot whose surface form is
  VESUM-ambiguous (non-discriminative across slots, e.g. syncretic gen.sg=acc.sg) is **skipped
  per-slot**; < 3 usable slots → word ineligible (fail-closed, consistent with §2).
- **SRS**: ONE card `lemmaId+paradigm` (not per slot). ⟦codex v4⟧ The card records **per-slot
  outcomes** (client-side history + §10.1 presentation metadata); rotation biases toward **missed and
  stale** slots, not plain least-recently-tested — one card must not over-promote on easy slots.
  Conditional coverage invariant like §6-case: if ≥3 slots eligible, last 8 presentations cover ≥3.
- **Mastery gate**: production mode → enters only after recognition baseline (generalises the §4 cloze
  gate to a single **production-gate** shared by `cloze` and `paradigm`).
- **Wrong-slot scaffold (§4 analog)**: right paradigm, wrong slot → amber case-miss (counts in SRS,
  first attempt grades); feedback names BOTH slots with the form delta («це давальний: брат**ові**;
  потрібен орудний: брат**ом**»).

### 9.2 `stress` — stress placement

- **Item**: word rendered unstressed, syllable nuclei tappable; learner taps the stressed vowel.
  Feedback shows the stressed form (audio later, with `listening`).
- **Gate `is_stress_eligible`**: ≥2 vowels; **exactly one attested stress position**. Variant-stress and
  stress-homograph lemmas (насипа́ти/наси́пати aspect pairs) are **excluded** in v1 — meaning-bearing
  stress is a future advanced drill, not a v1 edge case to guess at (fail-closed).
- ⟦agy v4⟧ **Light exposure gate** (not the full production-gate): a word enters `stress` only after
  ≥1 prior presentation in any recognition mode — day-one stress on a never-seen word is blind
  guessing, but stress is form-learning, so the bar stays minimal. Available from A1.
- Distractors are inherent (the other syllables) so §5 anti-gaming is trivially satisfied.
- **SRS**: `lemmaId+stress`.

### 9.3 `synonym` — synonym / antonym match

- **Item**: MC «Оберіть синонім до …» / «Оберіть антонім до …». Polarity (syn/ant) is tracked as §6
  perceptual variety (like `recallDirection`) — one mode, two felt shapes.
- **Gate `is_synonym_eligible`**: the target syn/antonym must ITSELF be an approved public atlas
  article at **≤ learner level** ⟦agy v4: level+1 targets = unlearned words as active answers — no⟧
  (so it is verified vocabulary, not an unvetted string); ≥3 valid
  distractors constructible under §5 buckets (same POS, no shared EN-gloss headword with prompt OR
  answer); pairs whose glosses are near-identical to a distractor's are skipped (validator).
- **Coverage honesty**: synonyms are slovnyk-sourced → deck grows with fill **Phase 2**; build reports
  coverage, never pads (§9.7).
- **SRS**: `lemmaId+synonym` on the PROMPT lemma.

### 9.4 `idiom` — idiom → meaning

- **Item**: MC: idiom prompt → pick the meaning. Meanings in **Ukrainian** (EN gloss as subtitle only —
  max-immersion rule is non-negotiable), CEFR-graded meaning text.
- **Gate `is_idiom_eligible`**: idiom carries a curated meaning gloss from Фразеологічний/slovnyk; under
  entry-model v1 idioms are their own `phraseologism` articles — the drill item links to that article
  (component-lemma backlink per the entry-model doc). B1+ default; A2 only for curator-flagged
  transparent idioms.
- **SRS**: card on the phraseologism article's own id (`idiomArticleId+idiom`).

### 9.5 `heritage` — decolonization drill (mission flagship)

- **Item**: «Оберіть питоме українське слово»: prompt = a reviewed **Ukrainian sentence frame** with
  the slot (EN meaning as subtitle gloss ONLY — ⟦agy v4⟧ an EN-primary prompt violates max-immersion);
  options = native form(s) + the russianism/calque + §5-valid distractors. Picking the calque is
  a scored miss with the **cited correction** as feedback (Антоненко-Давидович + heritage sources —
  the citation ships in the deck item, verbatim from `heritage_status.§6_note`).
- **Framing rule (pedagogy, hard)**: the russianism appears ONLY inside this mode, always ⚠️-marked in
  feedback, NEVER as a flashcard/matching/choice target anywhere else — we drill
  recognition-and-replacement, we do not teach the calque.
- **Gate `is_heritage_eligible`**: **curated pairs only, fail-closed** — a `curated_calque` correction
  with ≥1 citation AND the native alternative is an approved public article. Never generated from raw
  `russian_shadow` scores (the щитовидка/місцезнаходження rejects are drill items, not targets).
  ⟦codex v4⟧ "Curated" is a **validated contract, not a JSON convention**: the deck builder consumes a
  `heritage_pair` schema — `{nativeSlug, calqueLabel, corrections[], citations[] (≥1), sourceFamily}` —
  schema-validated at build; any pair failing validation is dropped and reported, never emitted.
- ⟦v5.1 — #4505 curation lane, agy-reviewed 2026-07-06⟧ **Schema extension + frames.** The curated
  store is `data/lexicon/heritage_pairs.yaml`. On top of the v4 five-field minimum each record adds:
  **`kind: lexical | sense_restricted`** — sense-restricted pairs (the неділя/задача class: the word
  is standard Ukrainian, ONE sense is the calque) additionally REQUIRE `calqueSense` +
  `authenticSense`; a bare lexical pair may not model them. **`frames[]` (optional per record,
  mirroring §9.9)** — `{sentence_with_slot, answer_form, calque_form, origin, disambiguated}`.
  **Item emission is fail-closed at the ITEM level**: a record without ≥1 frame validates as a
  RECORD but emits NO items (reported as frame-coverage debt, never a degraded word-level fallback
  item — sentence context is the pedagogy, not an optional garnish). For `sense_restricted` pairs
  the frame validator additionally requires `disambiguated: true` — the curator's explicit
  confirmation that the frame forces the calque sense (a frame where the authentic sense also fits
  would teach avoidance of a correct word). Every record carries a source-backed `rationale`
  (why the calque is wrong — shipped as feedback), and pairs are mined ONLY from attested evidence
  (UA-GEC annotations, Антоненко-Давидович, anti-surzhyk dictionaries, legacy curated records) —
  prevalence-gated so one-off idiosyncratic errors don't become drill targets.
- ⟦agy v4⟧ **Availability**: default **B1+** (calque exposure before core vocab is solid = lexical
  interference); **A2 only for curator-flagged high-frequency pairs whose native form is A-level
  vocabulary** — the mission-flagship pairs learners actually meet at A2, not the long tail.
  ⟦v5.1⟧ the mechanical A2 filter (native CEFR ≤ A2 + prevalence evidence) only NOMINATES;
  the record ships A2 only with the curator flag (`cefrAvailability: a2`).
- **SRS**: `nativeLemmaId+heritage` (the native word is what's being learned).

### 9.6 Selector + client integration (amends §6/§8)

- `PracticeMode` union + `PRACTICE_MODES` + `isPracticeMode` in `srs.ts` gain the new modes.
  ⚠️ Migration ⟦codex v4 — hardened⟧: the current `parseCardKey` remaps ANY unknown mode to
  `flashcards`; that silently corrupts state for old clients reading new-mode keys (and synced
  events). Change the contract: only **legacy no-`::` keys** map to `flashcards`; an **explicit
  unknown mode** is **quarantined** (state preserved untouched, card excluded from scheduling) —
  never remapped. Adding modes bumps `deckVersion`; ship the parser change BEFORE any new-mode deck.
- Per-mode debt counters (§6) extend to all modes; session bootstrap covers each AVAILABLE mode once.
- Sub-queue caps: cloze ~25% stays; `paradigm`+`stress` share a soft ~30% production guideline;
  `heritage`/`idiom`/`synonym` are scarce → own sub-queues like cloze, lapsed/urgent-due exempt.
- **Production-gate** (§9.1) is one shared predicate; `stress` and recognition modes bypass it.
- CEFR mode-availability matrix ships in the deck index per level (client never hardcodes it).

### 9.7 Deck architecture at 250k + coverage gates (amends §1/§3/§7)

- Per-drill shards following the existing split: `lexicon/practice-{mode}.{lvl}.json` (index/lexemes
  stay shared), lazy-loaded per enabled mode, **CI raw+gzip budget per shard per level**.
- Builder (`generate_practice_deck.py`, later `scripts/atlas/build_practice_decks.py` reading
  `data/atlas.db`) emits per (level × mode) coverage %, and the §3 `clozeCoverage` CI gate generalises:
  **warn on thin decks** for every scarce mode (cloze, synonym, idiom, heritage) with per-mode
  thresholds; a thin deck WARNS and ships small — it is never padded with unvetted items.
- ⟦codex v4⟧ **Per-mode option-set validators in CI** — §5's validator is cloze-form-specific; each MC
  mode gets its own (synonym: register/length balance, no semantic near-duplicate of the answer among
  distractors; idiom: meaning-text length balance; heritage: no source-label leakage marking the
  native form, calque never visually distinguishable pre-answer). Violations = build red, like §5.
- Acceptance (from GH #4383, amended v5): deck builder consumes `data/atlas.db`; **≥4 new drill
  types live with non-thin decks** (stress, classify, paradigm, synonym — the data-ready wave) plus
  heritage + paronym machinery fail-closed; FSRS extended across modes; coverage % reported per
  level; CI warns on thin decks.

### 9.8 `classify` — category sort (v5, user-approved 2026-07-05; ancestry: module `group-sort`, 249 instances)

- **Item**: MC «До якої групи належить …?» — one word, pick its category. Category sets (each a
  separate variety axis, §6): **gender** (чоловічий/жіночий/середній рід — nouns), **aspect**
  (доконаний/недоконаний вид — verbs), **declension group** (І–IV відміна — nouns, B1+), **POS**
  (частина мови — mixed decks, A2+). UA-first labels; EN subtitle gloss at A1–A2 only (§9.1 rule).
- **Data**: pure VESUM — the tags already ride `enrichment.morphology` + `pos`; ZERO curation.
  ⟦v5 probe⟧ 2,214 nouns (gender) · 1,069 verbs (aspect) · 598 adjectives in today's manifest.
- **Gate `is_classify_eligible`** (per category set, fail-closed): the VESUM tag exists and is
  UNAMBIGUOUS. Explicit per-set exclusions ⟦agy v5 review⟧: **gender** — pluralia tantum (двері,
  ножиці — no singular ⇒ no gender assignment) AND common-gender nouns (спільний рід, VESUM
  double-gender entries: сирота, колега, суддя); **aspect** — bi-aspectual verbs; **declension** —
  everything outside the І–IV відміна system: heteroclitic nouns, pluralia tantum, indeclinable
  nouns (незмінні: шосе, бюро), and substantivized adjectives that VESUM lemmatizes as nouns yet
  inflect adjectivally (минуле, майбутнє; черговий-type stay `adj` and self-exclude from noun
  pools). Gate at the LEMMA level, never the surface form — VESUM form→lemma collisions are real
  (verified: окуляри→окуляр, шахи→шах, таксі→такса). A word can be eligible in one set and
  excluded from another.
- **Anti-gaming (§5)**: options are the CLOSED category set (all genders / both aspects) — inherent
  balance; validator asserts the deck never lets one category exceed ~60% of a session's classify
  items (else learners meta-game the base rate).
- **SRS**: ONE card `lemmaId+classify` (not per category set); per-set outcomes recorded like §9.1
  slots; rotation biases missed sets.
- **Availability**: gender A1+ · aspect/POS A2+ · declension B1+.

### 9.9 `paronym` — confusable-pair pick (v5, user-approved 2026-07-05; ancestry: module `contrast_pair`; the тактовний≠тактичний class)

- **Item**: reviewed Ukrainian sentence frame with a slot (like §9.5); options = the correct
  paronym + its confusable(s). Feedback ALWAYS shows both words with their distinct meanings and
  one attested collocation each — the drill teaches the DISTINCTION, not just the answer.
- **Data contract**: curated `paronym_pair` records, schema-validated at build like §9.5's
  `heritage_pair`: `{slugA, slugB, frames[] (≥1 per direction), distinction_gloss_uk, citations[]
  (≥1 — Гринчишин «Словник паронімів», Антоненко, or СУМ senses)}`. Both slugs must be approved
  public articles. Any pair failing validation is dropped and reported — never emitted.
- **Option congruency (anti-gaming, §5)** ⟦agy v5 review⟧: every option in a frame MUST surface in
  the exact morphological form the slot requires (same case/gender/number for nominals; same
  person/number/tense for verbs). A form-mismatched distractor (fem-sg slot, target *тактовна*,
  distractor *тактичний*) lets agreement clues solve the item with zero semantic knowledge. The
  §5-style build validator rejects any frame whose options do not share the slot's agreement
  feature bundle (VESUM tags of the surface forms must match on case/gender/number/person/tense).
- **Sources for curation** (a curation-lane task, not build-time generation): Гринчишин paronym
  dictionary (check corpus availability), Антоненко-Давидович confusable entries, and the 6
  existing module `contrast_pair` activities as seeds. **Aspectual pairs are NOT paronyms**
  ⟦agy v5 review⟧ (видові пари — писати/написати, вирішувати/вирішити — one lexeme in two
  aspects): the curation lane excludes them; that contrast belongs to `classify`'s aspect axis.
- **Both directions drilled**: the pair generates a card per member (`lemmaId+paronym`), frames
  chosen so each member is the correct answer in its own frames (no "always-B" tell; §5 validator).
- **Availability**: B1+ (meaning-discrimination presupposes both words' recognition baseline —
  the §9.1 production-gate analog applies on BOTH members).

## 10. Practice Hub backend (v4 — GH #4384) — DESIGN ONLY, implementation gated

**Status: design.** Implementation starts only after this section passes fleet review + user go.
The static path (§1) stays authoritative forever: **no account = exactly today's offline behaviour.**
The backend is progressive enhancement for accounts + cross-device sync + analytics — never a fork.

### 10.1 Sync model — append-only review-event log (the core decision)

Do NOT sync FSRS state (two offline devices reviewing the same card would clobber each other — LWW on
scheduler state is wrong by construction). FSRS-6 state is a deterministic fold over the review
history, so **sync the log, derive the state**:

```
ReviewEvent {
  eventId ULID, lemmaId, mode, rating, reviewedAt, deckVersion, clientId,
  presentation? { slotId?, clozeId?, polarity?, optionSetId? }   // ⟦codex v4⟧ ignored by FSRS;
}                          // feeds slot rotation / frame no-repeat / coverage after a restore
```

- Client appends events locally (today: also start recording this log client-side even WITHOUT a
  backend — cheap, enables history backfill at first login; IndexedDB when > a few MB, per §1).
- Sync ⟦codex v4 — cursors defined⟧: **upload** = idempotent push, server ACKs per `eventId`
  (unACKed events re-push); **download** = a **server-assigned monotonic sequence number**
  (`serverSeq`, stamped at ingest) as the pull cursor — never a `reviewedAt` cursor, which loses
  late-arriving offline events. Replay through deterministic FSRS-6 → identical state on every
  device. Conflict-free by construction (append-only set union on `eventId`; idempotent upsert).
  Snapshots are a fast-restore cache, never authority.
- ⟦codex v4⟧ **Canonical replay order + clock policy** (determinism is a contract, not a vibe):
  server stamps `serverReceivedAt` + `serverSeq`; client clocks are validated — `reviewedAt` in the
  future of `serverReceivedAt` (+ skew window) or absurdly old is **clamped** to `serverReceivedAt`.
  Replay folds each card's events ordered by `(clampedReviewedAt, eventId)` — both synced fields, so
  every device folds identically; clamped time is also what FSRS uses for elapsed-interval input.
- ⟦codex v4⟧ **FSRS params are part of the contract**: scheduler params/settings live in an
  account-level record with an `fsrsParamsVersion`; replay pins the version. Devices never fold the
  same log under different parameters (that would fork state exactly like LWW would).
- `deckVersion` invalidation stays client-side (§1); events from older deck versions replay fine
  (card key = `lemmaId+mode` is version-stable).

### 10.2 Stack — PocketBase v1 (researched 2026-07-05)

**PocketBase**: single Go binary + SQLite (matches the `atlas.db` ethos), MIT-licensed, self-hostable
on the smallest VPS/free tier, built-in auth (email OTP/magic-link + OAuth), realtime, admin UI. The
needed API surface (auth + one append-only collection + one snapshot collection) maps 1:1 — smallest
possible ops burden for a permanently non-commercial project. **Alternative** if analytics outgrow
SQLite: Supabase (self-hostable Postgres multi-service stack). ⟦codex v4⟧ The **event log is
portable; auth/rules/admin are NOT** — so backend v1 ships a **backend-adapter + export contract**
(full per-user event-log export as JSON, documented restore path, scheduled backups) from day one;
"migration" means replaying exports into the next stack, and users can always take their data out.
**Rejected**: Firebase (proprietary, not self-hostable — violates project policy); custom FastAPI
service (needless bespoke surface for commodity auth+CRUD).

### 10.3 Data model + auth + analytics

- `users` — PocketBase-native. Auth = email OTP/magic-link (+ optional OAuth). Account deletion =
  hard-delete user + events — ⟦agy v4⟧ enforced at the DB layer (`ON DELETE CASCADE`), NOT via the
  append-only API rules (which would block it); the client, on deletion or auth-invalidation, purges
  local scheduling state + the IndexedDB event log.
- `review_events` — the §10.1 shape; unique `eventId`; indexed `(user, serverSeq)` (the pull cursor)
  + `(user, reviewedAt)` for analytics; append-only rules
  (no update/delete via API). ⟦agy v4⟧ Events carry NO userId client-side — the server scopes rows by
  the authenticated session at upload; pre-login local history uploads on first sync (backfill).
- `snapshots` — `(user, schemaVersion, blob, updatedAt)` — optional fast-restore.
- **Analytics** = server-side derivations of the event log ONLY (deck health, per-item difficulty,
  thin-mode detection feeding §9.7 curation). No third-party trackers; aggregate stats opt-in.
  ⟦agy v4⟧ PocketBase request logs anonymise/strip client IP + User-Agent (its defaults keep both).

### 10.4 Explicitly out of scope for backend v1 (named so they aren't re-litigated)

Search/data API at 250k entries; live slovnyk/Wikipedia enrichment proxy; server-side FSRS parameter
optimisation. Each is a v2 candidate behind its own design gate.

---
*Revision log: v1 (design locked with user) → v2 folds in the codex/agy/cursor fleet review of
2026-06-24. v3 applies the codex re-review (5 consistency fixes: hard rules → SRS-subordinate).
**v3.1 — FLEET RE-REVIEW PASSED** (the mandatory infra-orchestrator fleet-gate is satisfied): codex
"All 5 are resolved; blocker cleared" (bridge msg 1427, 2026-06-24); agy "v2 correctly resolves all
my prior findings… no blocker" (bridge msg 1424). Build kickoff AUTHORIZED by the user and dispatched
to codex as task `practice-hub-pr1b-build` (2026-06-24) — supersedes the empty-placeholder #3777.
**v4 (2026-07-05, GH #4383/#4384)** adds §9 drill-type expansion from `data/atlas.db` (paradigm /
stress / synonym / idiom / heritage; listening deferred) + §10 Practice Hub backend design
(event-log sync, PocketBase). §§0–8 are UNCHANGED — v4 extends, it does not reopen the locked
interaction model. **v4 FLEET REVIEW FOLDED (2026-07-05)**: codex (bridge msg 1831 — 6 blockers:
DB-backed eligibility predicates, heritage_pair validated contract, parseCardKey quarantine,
canonical replay order + clock clamps, presentation metadata in events, fsrsParamsVersion; + 3
non-blockers, 1 nit — ALL folded, marked ⟦codex v4⟧) and agy (bridge msg 1828 — 3 blockers:
stress exposure gate, A2 metalanguage subtitle, heritage UA-first prompt; + 5 non-blockers, 1 nit —
folded, marked ⟦agy v4⟧; heritage availability adjudicated to B1+ with curated A2 exceptions).*

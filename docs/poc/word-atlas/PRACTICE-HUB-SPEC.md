# Atlas Practice Hub — production spec (build target for PR #3777)

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
exact-item / word-spacing / mode drops), and that the **soft** rules apply only when they do NOT starve
scheduling (mode-penalty respected absent due pressure; conditional case coverage; no frame immediate-repeat;
perceptual rotation), plus the §5 option-validator. Violations = build red.

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

---
*Revision log: v1 (design locked with user) → v2 (this) folds in the codex/agy/cursor fleet review of
2026-06-24. v3 applies the codex re-review (5 consistency fixes: hard rules → SRS-subordinate). Must pass a fleet re-review before #3777 build kickoff (per infra-orchestrator
mandatory fleet-gate).*

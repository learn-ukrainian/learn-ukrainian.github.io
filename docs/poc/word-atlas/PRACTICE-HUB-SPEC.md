# Atlas Practice Hub — production spec (build target for PR #3777)

> The PoC `practice-hub.html` (this folder) is the **interaction source-of-truth**. The production
> React components must match the answer model + variety behaviours specified here. Verified design
> decisions from the user, 2026-06-24.

## 0. Headline requirement — the session must FEEL varied

The single most important UX property: **learners must feel the tasks keep changing — never "the same
kind repeating."** Every selection decision below (mode, word, case, sentence, options) routes through one
**anti-monotony selector** that biases AWAY from whatever was shown recently. Monotony is a bug, not a
polish item. Concrete, testable rules are in §6.

## 1. Architecture — static, build-time, no backend

GitHub Pages is static; there is no server to generate exercises at runtime, and we must **not** invent or
template sentences in the browser (quality bar: no unvetted content). The pattern: **move generation to
build time → static JSON; assemble exercises client-side.**

- **One prebuilt practice pool**, segmented by CEFR level (`practice-deck.A1.json`, `.A2.json`, …) for
  lazy-loading. Not per-user, not per-session — one pool per level.
- **Per-session variety + scheduling is client-side**: `ts-fsrs` (FSRS-6) over the pool + `localStorage`
  state. One pool → endless varied sessions, zero backend.
- Deck size: a bounded enriched subset (far smaller than the 39 MB manifest). Lazy-load the active level.

## 2. Deck schema (per entry) and where each field is sourced

| Field | Source |
|---|---|
| `lemma`, `lemmaPlain`, `ipa`, `gloss`, `pos`, `cefr`, `heritage`/`severity` | manifest enrichment |
| `paradigm.cases.<відмінок>.{singular,plural}` | manifest `enrichment.morphology.paradigm` |
| `cloze: [{ sentence, blankCase, form, caseRule, clozeEn }]` | `sentence`/`clozeEn` from **reviewed curriculum-module vocab cards**; `form` + `blankCase` from the paradigm; `caseRule` from a small curated case→trigger map |

- **Eligibility**: `is_practice_eligible` (gloss + CEFR/course anchor, no derived forms, no surzhyk) —
  already in `scripts/audit/lexeme_filter.py`.
- **Cloze is the only authored-content mode.** A word gets cloze items only if it has ≥1 **vetted** sentence
  from real content. The generator **skips** (never invents) when no vetted sentence exists.
- `form` is ALWAYS an oblique (declined) case form — the slot must never be answered by the bare lemma.

## 3. Exercise modes and their data needs

| Mode | Needs | Coverage |
|---|---|---|
| Flashcards | lemma + gloss + paradigm | every eligible word (free) |
| Matching | lemma + gloss | every eligible word (free) |
| Choice (meaning MC) | lemma + gloss | every eligible word (free) |
| **Cloze** | sentence + `blankCase` + `form` + `caseRule` | only words with a vetted sentence |

Recognition modes scale to the whole lexicon at zero authoring cost. Cloze is gated on sentence content.

## 4. Cloze answer model (case-demanding) — from the PoC, locked

1. **Demand the declined `form`.** The bare lemma is **never** accepted — typed OR clicked.
2. A wrong-case answer → **teaching message**, not a silent pass, and **not scored**:
   `«✕ Правильне слово, але інший відмінок — тут «роботу» (на → знахідний).»` (`caseRule` supplies the «(…)»).
3. **Typo / stress tolerant, case strict.** Normalise both sides: lowercase (uk), strip combining stress
   `́`, normalise apostrophes. The CASE is the learning target, so it is never forgiven.
4. Wrong *word* (a distractor) → retry on typed input; reveal + mark on chip click.
5. On resolve, fill the blank with the correct `form` and show the case name.

(Reference impl: PoC `czNorm` / `answerCloze`.)

## 5. Cloze option generation (anti-gaming) — from the PoC, locked

If the answer is always the only `lemma + declined` pair among the options, a learner games it by shape
(pick the oblique member of the single pair) without knowing the word or the case. **Never present exactly
one same-root pair.** Randomise composition:

- **~55% two-pair**: answer (`form`) + its own lemma (wrong-case distractor) + a **decoy word in BOTH forms**
  (lemma + a declined form). Two pairs → shape reveals nothing; the decoy's declined form is a trap.
- **~45% no-pair**: answer + 3 distinct distractor words, each shown as **either** its lemma **or** a
  declined form (random). Zero pairs.

Distractors are drawn from (a) the same word's other cases and (b) other words' mixed forms. (Reference
impl: PoC `nextCloze` option builder. Verified over 300 draws: answer always present; ~55/45; no lone pair.)

## 6. VARIETY — first-class, testable (the headline requirement)

All item selection flows through one **anti-monotony selector** that tracks a sliding window of the last
`K` items (`{mode, word, case, sentenceFrame}`) and biases selection away from recent values. Requirements:

- **a. Mode rotation.** Never serve the same exercise mode more than **twice consecutively**; interleave
  flashcards / matching / choice / cloze (+ future modes). Weighted by SRS need, but immediate-repeat-capped.
- **b. Word anti-repeat + SRS.** Never the same word within the last `K` items (`K ≥ 8`); `ts-fsrs`
  due-ordering over the full pool gives natural spacing; a large pool means words don't recycle fast.
- **c. Case variety (cloze).** Rotate the grammatical case tested (знах./род./дав./місц./оруд.). The last
  8 cloze items must cover **≥3 distinct cases**; prefer under-used cases for the current word.
- **d. Sentence variety.** Multiple sentence frames per case; if a word has >1 vetted sentence, rotate them;
  never show the same sentence frame back-to-back.
- **e. Option-composition variety (cloze).** The two-pair / no-pair modes (§5) also serve variety — they
  must alternate, not settle into one shape.
- **f. Distractor variety.** Vary which words are distractors across items; mix near (same semantic field)
  and far distractors so the wrong options aren't predictable.
- **g. Within-mode variety.** Flashcards alternate recall direction (UK→meaning / meaning→UK); Choice
  alternates «що означає X?» vs «яке слово означає Y?»; Matching varies set membership each round.

**Anti-monotony as a test**: a unit test drives ~50 selections and asserts (no mode 3× in a row; no word
within K; ≥3 cases per 8 cloze; sentence frame never immediately repeats). Monotony failing the test = build
red, same as any other gate.

## 7. Quality / verification gates

- **All forms VESUM-verified at build time.** The generator emits a `form` only if VESUM confirms it for the
  lemma+case; otherwise skip that cloze item.
- **Sentences from reviewed content only** — no invention, no runtime templating. Generator **fails closed**.
- Reuse the existing gates: `check_atlas_manifest_enrichment`, manifest freshness, render-verify.
- The deck generator (`scripts/audit/generate_practice_deck.py`) is the build-time owner of all of the above.

## 8. What to change in the current PR #3777 artifacts

- `generate_practice_deck.py`: emit the §2 schema incl. `cloze[]` (sentence+blankCase+form+caseRule) sourced
  from module vocab cards + paradigm; VESUM-gate every form; segment output per CEFR level; **replace the
  empty placeholder deck**.
- `srs.ts`: keep; it's the per-word scheduler. Add the §6 anti-monotony selector as a sibling that consumes
  the SRS due-queue but enforces mode/case/word/sentence spacing.
- `LexiconPractice.tsx`: cloze component implements §4 (case-strict, teaching feedback, typo-tolerant) and §5
  (anti-gaming options); all modes pull their next item from the anti-monotony selector, not a raw shuffle.
- `correctLabel`/count displays already use `uaPlural` — keep (locked principle).

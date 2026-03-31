# Cross-Level State Standard Reconciliation (B1 → B2 → C1 → C2)

**Date**: 2026-03-31

## Purpose

The individual gap analyses found gaps per level in isolation. This document cross-references them to catch:
- False gaps (covered at a lower level, so not actually missing)
- Misplacements (topic at wrong level)
- Real cross-level holes (topic falls between levels)

---

## 1. Cross-Level Corrections

### 1A. Prefixed Motion Verbs — B2 gap is FALSE

| Level | Coverage |
|-------|---------|
| **B1** | **7 dedicated modules**: `motion-prefixes-arrival`, `motion-prefixes-departure`, `motion-prefixes-in-out`, `motion-prefixes-transit`, `motion-prefixes-around`, `motion-flight-swim`, `figurative-motion` |
| **B2** | Gap analysis flagged as HIGH — "ZERO coverage" |

**Verdict**: B1 already covers this thoroughly. B2 does NOT need a new module.
The B2 gap analysis searched B2 plans only and missed B1's excellent coverage. B2 can assume motion verbs as prerequisite knowledge.

**Action**: ~~New module `prefixed-motion-verbs`~~ → REMOVE from B2 plan.

### 1B. Adjective/Adverb Comparison — B2 gap is REDUCED

| Level | Coverage |
|-------|---------|
| **B1** | **3 dedicated modules**: `adjectives-comparative`, `adjectives-superlative`, `adjectives-suppletive` + `adverbs-comparison-formation` |
| **B2** | Gap analysis flagged as HIGH — "no dedicated module" |

**Verdict**: B1 covers the grammar (formation, irregular forms, suppletive). B2 doesn't need a grammar module — it may need register-specific comparison usage (academic vs literary). But this can be folded into existing word-formation or stylistics modules.

**Action**: ~~New module `adjective-adverb-comparison`~~ → Expand existing B2 module (e.g., `word-formation-adjective-formation`) with a section on comparison in formal/academic registers. Much smaller fix.

### 1C. Pronouns — Gap at B2, C1, AND C2 (real progressive gap)

| Level | Coverage | What's covered |
|-------|---------|---------------|
| **B1** | `advanced-pronouns` (1 module) | Indefinite (хтось, дехто), negative (ніхто, ніщо), relative (який, що, хто) |
| **B2** | **NOTHING** | Reflexive себе, reciprocal один одного, definitive сам/самий/весь/кожний NOT covered |
| **C1** | Crammed into `morfolohichna-norma-c1` | Pronouns share 1000 words with adjectives — insufficient |
| **C2** | **NOTHING** | Stylistic/literary pronoun usage not explicitly taught |

**Verdict**: Real progressive gap. B1 covers one category. B2 should cover reflexive/reciprocal/definitive. C1 should deepen for academic use. C2 is OK to handle implicitly through style modules.

**Action**: Add 1 B2 module `pronoun-system-advanced` (reflexive, reciprocal, definitive). Expand C1's `morfolohichna-norma-c1` pronoun section. C2 — no action needed.

### 1D. Conditional Mood — C1 gap is REDUCED

| Level | Coverage |
|-------|---------|
| **B1** | **2 dedicated modules**: `conditionals-real`, `conditionals-unreal` |
| **B2** | `conditional-mood-particles` (1 dedicated module) |
| **C1** | Only `hedging-modality` touches this tangentially |

**Verdict**: B1+B2 cover the grammar solidly. C1 needs APPLIED conditional use in academic argumentation (counterfactual reasoning, hedging, irrealis in literary analysis) — but this is more of an expansion of `hedging-modality` than a new module.

**Action**: ~~New module `conditional-mastery-c1`~~ → Expand `hedging-modality` to explicitly cover conditional constructions in academic discourse. Rename if needed.

### 1E. Collective/Fractional Numerals — Verify B1 depth

| Level | Coverage |
|-------|---------|
| **B1** | `cases-with-quantity-expressions` — "explicitly covers collective numerals, fractions mentioned" |
| **B2** | `numeral-declension-compound-numbers`, `numeral-declension-time-dates` — compound/time but not collective/fractional |

**Verdict**: Need to verify B1's actual depth. If B1 covers basics of двоє/троє + одна друга, B2 just needs practice in complex contexts. If B1 only mentions them, B2 needs to teach them.

**Action**: Read B1's `cases-with-quantity-expressions` plan before deciding. Likely: expand B2's `numeral-declension-compound-numbers` to add a collective/fractional section.

### 1F. Aspect Pairs — C1 gap is real but SCOPED

| Level | Coverage |
|-------|---------|
| **B1** | Aspect basics throughout verb modules |
| **B2** | `aspect-nuances-secondary-imperfectivization`, `aspect-nuances-imperative-infinitive` (2 modules) |
| **C1** | **NOTHING** — no aspect module at all |

**Verdict**: Real gap. B2 teaches secondary imperfectivization and aspect in imperatives. C1 should teach PRODUCTIVE aspect mastery — using aspect strategically in academic/literary writing. Not grammar instruction, but register-aware aspect choice.

**Action**: Add 1 C1 module `aspect-pairs-mastery-c1` focused on productive aspect use in academic and literary discourse.

### 1G. Morphology & Cases at C2 — Real structural gap

| Level | Coverage |
|-------|---------|
| **B2** | `advanced-case-semantics` (1 module on case meanings) |
| **C1** | `morfolohichna-norma-c1` (1 module covering all morphology norms) |
| **C2** | `complete-grammar-review` (1 module trying to cover everything) |

**Verdict**: Real gap. C2 SS requires complete mastery of all morphological paradigms with archaic, dialectal, and literary forms. Currently compressed into one subsection of one module.

**Action**: Add 2-3 C2 modules for morphology/case mastery. The `complete-grammar-review` module should be restructured.

---

## 2. Revised Gap Summary (After Cross-Level Reconciliation)

### B1 (Issue #1120)
| # | Gap | Action | New modules |
|---|-----|--------|-------------|
| 1 | Possessive adjectives | Expand existing or new module | 0-1 |
| 2 | Homogeneous members | New module | 1 |
| 3 | Work theme | New module or expand | 0-1 |
| 4 | Restaurant/food | Verify A2, possibly expand | 0 |

**B1 total: +1 to +3 new modules (91 → 92-94)**

### B2 (Issue #1116)
| # | Gap | Action | New modules |
|---|-----|--------|-------------|
| ~~1~~ | ~~Prefixed motion verbs~~ | ~~REMOVED — B1 covers this~~ | 0 |
| ~~2~~ | ~~Adj/adv comparison~~ | ~~REDUCED — expand existing module~~ | 0 |
| 3 | Advanced pronouns | New module `pronoun-system-advanced` | 1 |
| 4 | Collective/fractional numerals | Expand `numeral-declension-compound-numbers` | 0 |
| 5 | Advanced noun declension | Expand `advanced-case-semantics` or new | 0-1 |
| 6 | Zero-suffix deverbals | Add section to `word-formation-abstract-nouns` | 0 |

**B2 total: +1 to +2 new modules (89 → 90-91)**
Down from the original estimate of +3 modules.

### C1 (Issue #1117)
| # | Gap | Action | New modules |
|---|-----|--------|-------------|
| 1 | Aspect pairs mastery | New module | 1 |
| ~~2~~ | ~~Conditional mood~~ | ~~REDUCED — expand `hedging-modality`~~ | 0 |
| 3 | Pronoun paradigm | Expand `morfolohichna-norma-c1` | 0 |
| 4 | Sport theme | New module or expand | 0-1 |

**C1 total: +1 to +2 new modules (111 → 112-113)**

### C2 (Issue #1118)
| # | Gap | Action | New modules |
|---|-----|--------|-------------|
| 1 | Morphology mastery (nouns, adj, numerals) | 2-3 new modules | 2-3 |
| 2 | Case semantics | 1 new module | 1 |
| 3 | One-member sentences as literary device | Expand `syntactic-stylistics` | 0 |
| P0 | word_target 4000→5000 | Script fix (91 files) | 0 |

**C2 total: +3 to +4 new modules (106 → 109-110)**

---

## 3. Systemic Issues (All Levels)

| Issue | B1 | B2 | C1 | C2 |
|-------|----|----|----|----|
| Missing `activity_hints` | ✅ 91/91 have them | ❌ 85/89 missing | ❌ 111/111 missing | ❌ 106/106 missing |
| Missing `references` | ✅ 91/91 have them | ❌ 86/89 missing | ✅ 111/111 have them | ❌ 106/106 missing |
| Wrong `word_target` | ✅ correct | ✅ correct (1 orphan exception) | ✅ correct | ❌ 91/106 wrong (4000→5000) |
| YAML errors | ✅ 0 | ❌ 4 files | ? not checked | ? not checked |
| English in headers | ✅ 0 | ❌ 7 sections | ? not checked | ? not checked |

**B1 is the gold standard** — all fields present, all correct. B2/C1/C2 need to be brought up to B1's quality.

---

## 4. Execution Order

1. **B2 first** (issue #1116) — fix mechanical issues → add missing fields group-by-group → add 1-2 new modules
2. **C1 second** (issue #1117) — add activity_hints → fix gaps → add 1-2 new modules
3. **C2 third** (issue #1118) — fix word_target (P0) → add references + activity_hints → add 3-4 new modules
4. **B1 last** (issue #1120) — already in good shape, just need 1-3 new modules for gaps

Each level gets the same treatment: mechanical fixes → field-by-field completeness → State Standard gap modules → adversarial review.

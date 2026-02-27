<!-- content-hash: fd86c9fa03fd -->
**Reviewed-By:** claude-opus-4-6

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | **Language Quality** | 7 | Grammar error on line 220 («говорить» instead of infinitive «говорити»); non-standard medical term on line 294 («серцевої системи» → should be «серцево-судинної системи»); semantically awkward construction on line 182 («їй дуже боляче плакати»). The bulk of the Ukrainian is clean and correct, but errors in a language-teaching module weigh heavily. |
| 2 | **LLM Fingerprint** | 6 | Extreme structural monotony: 15 identical **«Приклади вживання [X]:»** headers each followed by exactly 5 numbered examples. 6 identically formatted **«Міні-діалог:»** blocks. The intensifier «дуже» appears 37 times across the module, creating a padded, repetitive feel. Each subsection follows the exact same template: [prose] → [5 examples] → [optional mini-dialogue]. |
| 3 | **Lesson Quality** | 8 | Good PPP structure, warm tone, clear grammar explanations with English support. Dialogues are realistic and engaging. The "Would I Continue?" test passes 4/5 (learner wouldn't feel overwhelmed, instructions are clear, quick wins present, Ukrainian introduced gently). Minor: no explicit "You can now..." celebration at the end — the summary is functional but could be warmer. |
| 4 | **Factual Accuracy** | 8 | The malyna/salicylic acid claim (line 267) is supported by research notes. However, line 294 uses «серцева система» which is not a recognized medical term — the standard Ukrainian term is «серцево-судинна система» (cardiovascular system). Teaching incorrect medical terminology in a health module is a factual issue. |
| 5 | **Immersion** | 9 | 89.6% Ukrainian is at the high end of the 75-90% Band 3 target but within range. English is appropriately confined to [!note] grammar boxes. Grammar explanations in English are pedagogically justified at A2. |
| 6 | **Activity Quality** | 8 | 12 activities across 10 types (match-up, fill-in x2, quiz, unjumble, group-sort, error-correction, true-false, mark-the-words, select, translate, cloze) — excellent variety. The error-correction activity catching «кушати» and «самий кращий» Russicisms is superb. Minor: the quiz questions (activity 3) lean toward content recall rather than language comprehension (e.g., «Який традиційний український засіб найчастіше п'ють від високої температури?» is answerable from general knowledge). |
| 7 | **Warmth & Humanity** | 8 | Module has warm tone throughout, multiple realistic dialogues, cultural hooks. Direct address is frequent. However, the closing section (line 398-409) is functional rather than celebratory — it lists facts learned rather than affirming the learner's achievement. Missing a "You've got this!" moment. |
| 8 | **Richness** | 6 | Audit flags collocations: 0/20 and register_notes: 4/5. The vocabulary YAML places collocations as free text inside the `notes` field rather than in a dedicated `collocations` field, causing the audit to report zero. The prose itself contains rich collocations, but the structured data doesn't reflect this. This is a structural fix, not a content rewrite. |
| 9 | **Plan Compliance** | 8 | All 5 content sections present and all planned points covered. However, the H2 header for section 3 reads «Здоровий спосіб життя та ментальний баланс» (line 184) while the plan specifies «Здоровий спосіб життя та ментальне здоров'я» — a title mismatch. The section content does cover mental health as planned, so this is cosmetic but should match for traceability. |

---

## Critical Issues Found

### Issue 1: Grammar Error — Infinitive form (CRITICAL)

- **Location:** Line 220, section «Здоровий спосіб життя та ментальний баланс»
- **Type:** GRAMMAR_ERROR
- **Evidence:** «Вони вчаться відкрито говорить про проблеми.» — After «вчаться» (they learn), the infinitive «говорити» is mandatory. «Говорить» is the 3rd person singular present tense form. In a language-teaching module, this morphological error is critical — a learner might internalize the wrong form.
- **Fix:** Replace «говорить» with «говорити» on line 220.

### Issue 2: Extreme Structural Monotony (SIGNIFICANT)

- **Location:** Entire module — lines 18, 70, 111, 130, 140, 177, 189, 199, 222, 269, 279, 289, 354, 364, 374
- **Type:** LLM_FINGERPRINT
- **Evidence:** 15 section headers all named «Приклади вживання [variant]:» each followed by exactly 5 numbered examples. The pattern [prose paragraph] → [5 examples] → [Міні-діалог] repeats identically through every subsection without exception. Real textbooks vary their example formats — inline examples in prose, tables, dialogues, comparison pairs, fill-in-the-blanks — not the same template 15 times.
- **Fix:** Vary the example presentation. Convert some «Приклади вживання» blocks to inline examples within prose, comparison tables, or short scenarios. Reduce the count from exactly 5 to 3-4 in some sections. Rename headers to be context-specific rather than generic.

### Issue 3: Non-Standard Medical Terminology (SIGNIFICANT)

- **Location:** Line 294, section «Народна медицина та традиційні практики»
- **Type:** FACTUAL_ERROR
- **Evidence:** «Паритися в бані корисно для нашої серцевої системи та швидкого кровообігу.» — «Серцева система» is not a standard Ukrainian medical term. The established term is «серцево-судинна система» (cardiovascular system). In a health-vocabulary module that explicitly teaches medical terminology, using a fabricated medical term is misleading.
- **Fix:** Replace «серцевої системи» with «серцево-судинної системи» on line 294.

### Issue 4: Semantically Awkward Example (MINOR)

- **Location:** Line 182, section «Презентація: Моє тіло та самопочуття»
- **Type:** NATURALNESS
- **Evidence:** «Дитина впала з велосипеда, і зараз їй дуже боляче плакати.» — «Боляче плакати» (painful to cry) doesn't convey the intended meaning of "she's in pain." A native speaker would say «їй дуже боляче» (she's in a lot of pain) without the infinitive «плакати». The construction implies that the act of crying itself is painful, which is semantically odd.
- **Fix:** Replace with «і зараз їй дуже боляче» or «і зараз їй дуже боляче, тому вона плаче».

### Issue 5: H2 Title Mismatch with Plan (MINOR)

- **Location:** Line 184
- **Type:** PLAN_COMPLIANCE
- **Evidence:** Content H2 reads «Здоровий спосіб життя та ментальний баланс» while the plan specifies «Здоровий спосіб життя та ментальне здоров'я». The mental health content is present, but the title should match for pipeline traceability.
- **Fix:** Rename H2 on line 184 to «Здоровий спосіб життя та ментальне здоров'я».

### Issue 6: Richness Gap — Vocabulary YAML Structure (SIGNIFICANT)

- **Location:** `/curriculum/l2-uk-en/a2/vocabulary/health-wellness.yaml`
- **Type:** RICHNESS_GAP
- **Evidence:** Collocations are embedded as free text inside `notes:` fields (e.g., line 6: `notes: 'collocations: міцне здоров'я, піклуватися про здоров'я'`), but the audit expects a dedicated `collocations` field. This causes the richness gate to report 0/20 collocations despite rich collocation data being present in the prose. Additionally, register_notes is 4/5.
- **Fix:** Add a `collocations` list field to each relevant vocab entry. Add one more `register` note to bring register_notes to 5/5 (e.g., on «баня» — colloquial/informal register vs. «сауна» — more modern/neutral register).

### Issue 7: Excessive «дуже» Filler (MINOR)

- **Location:** Throughout the module (37 occurrences)
- **Type:** LLM_FILLER
- **Evidence:** The intensifier «дуже» appears 37 times across ~5100 words (once per ~138 words). Natural Ukrainian prose varies intensifiers — «надзвичайно», «вкрай», «неймовірно», «страшенно», «напрочуд», «на диво». Over-reliance on «дуже» is a hallmark of LLM-generated Ukrainian text.
- **Fix:** Replace ~15 instances of «дуже» with varied intensifiers or remove them where the intensification adds no meaning (e.g., «це дуже важливо» → «це важливо»; «дуже сильний біль» → «нестерпний біль»).

---

## Factual Verification

| Claim | Location | Verdict | Notes |
|-------|----------|---------|-------|
| «Здоров'я — найбільше багатство» is a traditional Ukrainian proverb | Line 16 | VERIFIED | Well-established Ukrainian proverb |
| Malyna contains natural salicylic acid | Line 267 | VERIFIED | Confirmed in research notes and widely accepted |
| Military greeting «Бажаю здоров'я!» | Line 36 | PLAUSIBLE | This is an established tradition in Ukrainian armed forces |
| Kalyna lowers blood pressure | Line 264 | PLAUSIBLE | Traditional claim; folk medicine rather than clinical evidence |
| «Серцева система» as medical term | Line 294 | INCORRECT | Standard term is «серцево-судинна система» |
| Ukrainian healthcare reform with «декларація» | Line 349 | VERIFIED | Post-2017 reform; matches research notes |
| Вуличні тренажери as cultural phenomenon | Line 207 | VERIFIED | Well-documented; matches cultural hooks in research |

---

## Verification Summary

| Check | Result | Details |
|-------|--------|---------|
| Russianisms (A2 list) | PASS | No instances of приймати участь, самий кращий, скучати, нравитися, відноситися, слідуючий in prose. The error-correction activity correctly teaches «кушати» → «їсти» and «самий кращий» → «найкращий». |
| Colonial framing | PASS | No "Unlike Russian..." patterns. No Russian language comparisons. The Soviet reference (line 362) is historical context, not colonial framing. |
| Grammar scope | PASS | Grammar taught (боліти construction, Dative states, треба/варто, більш/менш comparatives) aligns with plan and A2 level specifications (§3.12, §4.2.2.3, §4.3.1). |
| Anglicisms | PASS | No calques found (робити рішення, брати місце, робити сенс absent). |
| LLM fingerprint | PARTIAL FAIL | «це не просто» appears 2x (lines 16, 287) — at threshold but not over. However, the 15x identical example format and 37x «дуже» constitute a clear LLM batching pattern. |
| Plan compliance | PARTIAL FAIL | All 5 sections present and all content points covered. H2 title mismatch on section 3 (ментальний баланс vs ментальне здоров'я). Word count 170% over target is acceptable (minimums). |
| Activity correctness | PASS | All 12 activities have correct answers, appropriate distractors, and relevant explanations. Error-correction items are pedagogically excellent. |
| Beginner safety | PASS | "Would I Continue?" = 4/5. English grammar notes are appropriately scaffolded. Pacing is comfortable. Only gap: closing section lacks warm celebration. |

---

## Verdict

**CONDITIONAL PASS** — The module delivers strong pedagogical content with excellent activities and cultural depth. However, it requires targeted fixes before full approval:

**Must fix (blocks pass):**
1. Grammar error: «говорить» → «говорити» (line 220) — language error in a language module
2. Medical term: «серцевої системи» → «серцево-судинної системи» (line 294)
3. Richness gap: restructure vocabulary YAML to add dedicated `collocations` fields (moves from 0/20 to 20+/20)

**Should fix (quality improvement):**
4. Structural monotony: vary at least 5 of the 15 «Приклади вживання» blocks into different formats
5. H2 title: rename «ментальний баланс» → «ментальне здоров'я» (line 184) to match plan
6. Semantic fix: «боляче плакати» → «боляче» (line 182)
7. Reduce «дуже» count from 37 to ~20 by varying intensifiers

**Fix priority:** Items 1-3 are quick targeted fixes. Item 4 requires more structural work but significantly improves the LLM Fingerprint score. Items 5-7 are minor polish.
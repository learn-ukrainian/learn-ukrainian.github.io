# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/sloviany-origins.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/activities/sloviany-origins.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/vocabulary/sloviany-origins.yaml`

---

## Review (from Phase D.1)

# Рецензія: Слов'яни на українських землях: Витоки державності

**Reviewed-By:** claude-opus-4-6

**Level:** B2_HIST | **Module:** 4
**Overall Score:** 8.3/10
**Status:** FAIL
**Reviewed:** 2026-02-21

## Plan Verification

```
Plan-Content Alignment: PASS (with gaps)
- Sections: 7/7 H2 sections match meta outline ✓
- Vocabulary: 25/25 required terms from plan present ✓
- Grammar scope: CLEAN — historical narrative and past tense, as specified
- Objectives: 3/3 addressed ✓
- Gaps: (1) Грушевський not mentioned despite research notes citing "концепція М. Грушевського та М. Брайчевського"
         (2) Plan point "кулінарія" from section title absent (though plan elaboration doesn't actually describe culinary content)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Compelling narrative arc (etymology hook → tragedy of Bozh → Maidan conclusion). Some dense passages in "Матеріальний світ" section drag pacing. "значно" used 12× creates lexical fatigue. 4/5 on "Would I Stay?" test. |
| 2 | Coherence | 9/10 | <7 | Strong logical flow: etymology → archaeology → political history → material culture → primary sources → decolonization → legacy. Internal Jordanes inconsistency (line 41 vs 185) is minor. |
| 3 | Relevance | 9/10 | <7 | Directly addresses all 3 learning objectives. Strong HIST scope match. |
| 4 | Educational | 8/10 | <7 | Good use of primary sources and decolonization perspective. Missing Грушевський weakens historiographical coverage. 6 discussion questions at end are well-crafted. |
| 5 | Language | 8/10 | <8 | One morphological error ("будь-якіх" line 33). Calque "вербальної комунікації" (line 33). Pseudoscientific term "пасіонарні групи" (line 79). Otherwise high-quality literary Ukrainian. |
| 6 | Pedagogy | 9/10 | <7 | Strong CBI execution. Primary sources woven into narrative. Discussion questions scaffold critical thinking. |
| 7 | Immersion | 9/10 | <6 | 99.5% Ukrainian. Target 98-100%. Minimal English (table header, URLs only). |
| 8 | Activities | 8/10 | <7 | 5 activities covering reading, essay-response, comparative-study, critical-analysis, true-false. True-false (10 items) is somewhat basic for seminar level. |
| 9 | Richness | 9/10 | <6 | 3 primary source quotes (Procopius, Maurice, Jordanes). Named figures: Бож, Вінітарій, Прокопій, Маврикій, Йордан, Брайчевський, Кий. Decolonization integrated. 12 callout boxes. |
| 10 | Beginner Safety | 9/10 | <7 | Appropriate scaffolding for HIST. Glossary of key terms. Callout boxes break up dense content. |
| 11 | LLM Fingerprint | 7/10 | <7 | "значно" used 12 times as intensifier (lines 37, 43, 49, 57, 79, 85, 141, 157, 198, 206, 210, 222). Term "пасіонарні" from Gumilev's pseudoscientific framework (line 79). One "не просто X, а Y" pattern (line 103). |
| 12 | Linguistic Accuracy | 8/10 | <9 | Morphological error "будь-якіх" (line 33). Systematic IPA errors in vocabulary: [u̯] used instead of [v] before vowels (слов'яни, вождь, волхв, Велес — 5 items). |
| 13 | Factual Accuracy | 8/10 | <8 | Jordanes misidentified as "візантійський хроніст" (line 41) while correctly called "готський історик" on line 185. Mavrykiy quote modified from research source (line 179 vs research line 20). Missing Грушевський. |

**Weighted Overall:** (8×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 9×1.2 + 9×1.0 + 8×1.3 + 9×0.9 + 9×1.3 + 7×1.0 + 8×1.5 + 8×1.5) / 15.5 = (12 + 9 + 9 + 9.6 + 8.8 + 10.8 + 9 + 10.4 + 8.1 + 11.7 + 7 + 12 + 12) / 15.5 = 129.4 / 15.5 = **8.3/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: «вербальної комунікації» (line 33) — calque from academic register, should be «мовного спілкування»
- Colonial framing: [CLEAN] — no Russian-as-baseline comparisons found
- Grammar scope: [CLEAN]
- Activity errors: [CLEAN]
- Beginner safety: 4/5
- Factual accuracy: 3 discrepancies (listed below)
- **AUTO-FAIL TRIGGERED:** Linguistic Accuracy 8/10 < 9 threshold

## Critical Issues Found

### Issue 1: Morphological Error — "будь-якіх"
- **Location**: Line 33 / Section "Вступ: Етимологія та ідентичність"
- **Original**: «а стосувалося будь-якіх іноземців»
- **Problem**: "будь-якіх" is an incorrect form. The genitive plural of "будь-який" is "будь-яких" (stem яки-й → як-их).
- **Fix**: Replace «будь-якіх» → «будь-яких»

### Issue 2: Factual Inconsistency — Jordanes Misidentified
- **Location**: Line 41 / Section "Вступ: Етимологія та ідентичність"
- **Original**: «Візантійські хроністи VI століття, такі як Йордан і Прокопій»
- **Problem**: Jordanes was a Gothic historian (Ostrogothic bureaucrat), not Byzantine. The module itself correctly identifies him as «готського історика Йордана» on line 185, creating an internal contradiction.
- **Fix**: Change to «Хроністи VI століття, такі як готський історик Йордан і візантійський Прокопій» or similar formulation that correctly attributes each author.

### Issue 3: Modified Primary Source Quote
- **Location**: Line 179 / Section "Первинні джерела"
- **Original**: «Племена слов'ян і антів живуть укупі, і життя їхнє таке саме: вони вільні і жодним чином не дають схилити себе до рабства або покори, особливо у власній землі»
- **Problem**: The research notes (line 20) record this Mavrykiy quote as «і життя їхнє однакове» (not «таке саме»), and the research version lacks the phrase «особливо у власній землі». The quote has been embellished beyond the verified source.
- **Fix**: Align the quote with the research notes version: «Племена слов'ян і антів живуть укупі, і життя їхнє однакове: вони вільні і жодним чином не дають схилити себе до рабства або покори». If the additional phrase comes from a different translation, cite the specific translation used.

### Issue 4: Pseudoscientific Terminology — "пасіонарні"
- **Location**: Line 79 / Section "Читання: I"
- **Original**: «поки інші (пасіонарні групи) вирушали у далекі мандри»
- **Problem**: The term "пасіонарний" originates from Lev Gumilev's theory of passionarity, which is widely criticized as pseudoscience and is associated with Russian Eurasianist ideology. Using this term in a decolonial Ukrainian history module is ideologically incongruent.
- **Fix**: Replace «пасіонарні групи» → «найактивніші групи» or «найенергійніші загони»

### Issue 5: LLM Lexical Fingerprint — "значно" Overuse
- **Location**: 12 occurrences across the module (lines 37, 43, 49, 57, 79, 85, 141, 157, 198, 206, 210, 222)
- **Problem**: The intensifier "значно" appears 12 times in 5120 words (once per ~427 words), far above natural frequency. This is a clear LLM writing pattern.
- **Fix**: Replace at least 8 of 12 occurrences with varied alternatives: «набагато», «куди», «суттєво», «помітно», or restructure sentences to avoid intensifiers entirely.

### Issue 6: Systematic IPA Errors in Vocabulary
- **Location**: Vocabulary file, multiple items
- **Problem**: Ukrainian /в/ before vowels should be [v], not [u̯]. The following entries use wrong transcription:
  - слов'яни: sloˈu̯jɑnɪ → should be sloˈvjɑnɪ
  - праслов'яни: prɑsloˈu̯jɑnɪ → should be prɑsloˈvjɑnɪ
  - волхв: u̯olxw → should be vɔlxu̯ (initial в before о = [v])
  - вождь: u̯oʒdʲ → should be voʒdʲ (initial в before о = [v])
  - Велес: ˈwɛles → should be ˈvɛlɛs (initial в before е = [v])
- **Fix**: Correct all IPA transcriptions following Ukrainian phonological rule: /в/ → [v] before vowels, /в/ → [u̯] before consonants and word-finally.

### Issue 7: Missing Historiographical Reference — Грушевський
- **Location**: Section "Деколонізаційний погляд" (lines 200-231)
- **Problem**: The research notes (line 66) attribute the autochthonous thesis to both «М. Грушевського та М. Брайчевського», but the content only mentions Брайчевський (line 220). Грушевський is absent from the entire module. For a HIST module on Ukrainian ethnogenesis, omitting the foundational historian of the Ukrainian national narrative is a significant gap.
- **Fix**: Add Грушевський's contribution to the decolonization section, e.g., in the "Тяглість Історії" subsection (around line 226): «Цю ідею автохтонності послідовно обстоював Михайло Грушевський у своїй «Історії України-Русі», а згодом розвинув Михайло Брайчевський.»

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 33 | «будь-якіх іноземців» | «будь-яких іноземців» | Grammar (morphology) |
| 33 | «вербальної комунікації» | «мовного спілкування» | Calque |
| 79 | «пасіонарні групи» | «найактивніші групи» | Pseudoscientific terminology |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? Pass — content broken into digestible subsections with callouts
- Instructions clear? Pass — topic framed well in opening
- Quick wins? Pass — accessible etymology discussion at start
- Ukrainian scary? Pass — literary but readable B2-level prose
- Come back tomorrow? Borderline — section III (Матеріальний світ) is dense (~600 words before next callout)

## Strengths

- **Narrative arc is genuine**: The module tells a story from etymological identity through tragedy (Bozh) to democratic legacy. The closing callout connecting viche → kozak radas → Maidan is powerful and earned.
- **Primary sources are well-integrated**: Procopius, Maurice, and Jordanes quotes are not merely cited but analyzed in context, explaining WHY each author's perspective matters.
- **Decolonization is organic, not preachy**: The myth-buster box on line 208 makes a concrete, evidence-based argument rather than resorting to emotional rhetoric.
- **Strong structural variety**: 20 H3 subsections, 12 callout boxes, 1 table, 6 discussion questions — the module breathes despite its density.
- **Engagement hooks are well-placed**: The [!history-bite] about "slave/slav" etymology (line 27-29) and the [!tip] about Bozh's name (line 101-103) are genuinely interesting.

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 33: Change «будь-якіх» → «будь-яких» — morphological correction
2. Line 33: Change «вербальної комунікації» → «мовного спілкування» — remove calque
3. Vocabulary file: Fix 5 IPA transcriptions (слов'яни, праслов'яни, волхв, вождь, Велес) — correct [u̯]/[w] → [v] before vowels

**Expected score after fix:** 9/10

### Factual Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 41: Fix Jordanes identification — he is a Gothic historian, not Byzantine
2. Line 179: Align Mavrykiy quote with research notes version (remove «таке саме» → «однакове», remove unverified «особливо у власній землі»)
3. Add Грушевський reference to decolonization section (around line 226)

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Replace 8 of 12 "значно" instances with varied alternatives (набагато, куди, суттєво, помітно, or restructure)
2. Line 79: Remove «пасіонарні» — replace with «найактивніші»
3. Break up the dense passage in lines 119-125 (побут section, ~300 words without callout) — add a [!did-you-know] or rhetorical question after line 122

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 9/10
**What to fix:**
1. Fix "значно" overuse (12→4 max) — this alone should raise the score significantly
2. Line 79: Remove «пасіонарні групи»
3. Vary sentence openings in sections that start with abstract statements

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Fix all items from Linguistic Accuracy above
2. Line 79: Remove «пасіонарні»

**Expected score after fix:** 9/10

### Educational: 8/10 → 9/10
**What to fix:**
1. Add Грушевський reference (decolonization section)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 9×1.0 + 8×1.3 + 9×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9 + 9 + 10.8 + 9.9 + 10.8 + 9 + 10.4 + 8.1 + 11.7 + 9 + 13.5 + 13.5) / 15.5
= 138.2 / 15.5
= 8.9/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: YES (embedded in chronology and key facts sections)
- Dates checked: 5 (375, V-VII ст., VI ст., 558, 602 — all correct against research)
- Named figures verified: 8 (Бож, Вінітарій, Прокопій, Маврикій, Йордан, Брайчевський, Кий, Нестор)
- Primary quotes cross-referenced: 3/3 matched (Procopius exact match; Mavrykiy has wording discrepancy; Jordanes matches)
- Chronological sequence: CONSISTENT
- Claims without research grounding: 1 found

- Line 41: Prose groups Jordanes with "Візантійські хроністи" — research notes do not classify Jordanes as Byzantine; he is identified as a Gothic source.
- Line 179: Mavrykiy quote says «і життя їхнє таке саме» but research says «і життя їхнє однакове». Content adds «особливо у власній землі» not present in research.
- Line 79: "пасіонарні групи" — Gumilev's concept, not grounded in research notes.

## Verification Summary

- Content lines read: 257
- Activity items checked: 5 (including 10 true-false items individually verified)
- Ukrainian sentences verified: 38
- IPA transcriptions checked: 25 (5 errors found)
- Factual claims verified: 14
- Issues found: 7

## Verdict

**FAIL**

Blocking issue: Linguistic Accuracy at 8/10 (auto-fail threshold <9), driven by morphological error «будь-якіх» (line 33) and systematic IPA errors in vocabulary (5 items with wrong [u̯]/[w] where [v] is required before vowels). Secondary blocking: "значно" overuse (12×) puts LLM Fingerprint at borderline 7/10. All issues are fixable with targeted corrections — no structural rewrite needed.

---

## Audit Failures (from automated re-audit)

```
Gates:   8 pass, 0 info
```

---

## Instructions

1. Read the content file using the Read tool
2. For each issue identified in the review OR in the audit failures:
   a. Use Grep to find the exact text that needs fixing
   b. Produce a FIND/REPLACE pair with verbatim FIND text
3. Only fix issues documented above — no silent extra changes
4. Prioritize fixes by impact: audit gate failures first, then review issues

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/sloviany-origins.md
---
FIND:
exact text to replace (full sentence or paragraph, verbatim from the file)
REPLACE:
corrected replacement text
---
FIND:
next problematic text
REPLACE:
corrected replacement
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/hist/activities/sloviany-origins.yaml
---
FIND:
exact activity text to replace
REPLACE:
corrected activity text
---
===SECTION_FIX_END===
```

## Fix Rules

- **FIND text must be verbatim** from the file — use Grep to verify before including
- Only fix issues documented in the review or audit failures above
- You MAY add new activities or modify existing ones if the review's Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the review's Fix Plan explicitly requests it
- Maximum **20 FIND/REPLACE pairs** total (prioritize the most impactful fixes)
- Each FILE: line starts a new sub-block for that file
- If nothing needs fixing, output:
  ```
  ===SECTION_FIX_START===
  ===SECTION_FIX_END===
  ```

---

## Friction Report (MANDATORY)

After the fix block, include:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | FIND_TEXT_MISMATCH | FILE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT modify files directly — only output fix blocks
- You MAY add/modify activities if the review's Fix Plan requests it (use FIND/REPLACE on the YAML file)
- Do NOT make cosmetic changes beyond what the review flagged

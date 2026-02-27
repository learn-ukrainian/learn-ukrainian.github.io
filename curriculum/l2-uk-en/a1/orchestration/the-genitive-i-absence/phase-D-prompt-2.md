# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-genitive-i-absence.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-genitive-i-absence.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-genitive-i-absence.yaml`

---

## Review (from Phase D.1)

# Рецензія: The Genitive I: Absence

**Reviewed-By:** claude-opus-4-6

**Level:** A1 | **Module:** 16
**Overall Score:** 8.1/10
**Status:** FAIL
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: All 4 plan sections present as H2 headers (Вступ, Граматика, Практика, Культурний контекст) — PASS
- Vocabulary: 8/8 required present (немає, без, час, гроші, молоко, цукор, вода, хліб), 5/5 recommended present (проблема, квиток, ключ, телефон, газ) — PASS
- Grammar scope: Genitive case for absence, без + genitive, немає + genitive all covered. No scope creep to later modules — PASS
- Objectives: All 4 plan objectives addressed — PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good structure with clear progression through 4 sections. Tables and callout boxes break density well. Missing warm greeting at opening (no "Привіт!" or "Today you'll learn...") and zero explicit encouragement phrases ("Great!", "Well done!"). "Would I Continue?" test: 4/5. |
| 2 | Coherence | 8/10 | <7 | Logical flow from introduction → grammar → practice → culture. Minor redundancy: line 131 repeats the -а → -и rule already established at lines 118-123 ("Feminine nouns ending in -а after a hard consonant follow the same -а → -и rule"). |
| 3 | Relevance | 9/10 | <7 | All plan vocabulary and objectives covered. Cultural hooks (Немає проблем, proverb, market culture, polite refusals) are practical and directly serve the grammar goal. |
| 4 | Educational | 8/10 | <7 | Clear grammar explanations with the -а vs -у distinction well-handled. Excellent common mistakes table at lines 191-197. But "День" and "Батько" are listed under "### Genitive Endings: Masculine Hard Nouns (-а)" heading (line 71) despite being soft-stem and vowel-final respectively — could teach wrong categorization patterns. |
| 5 | Language | 8/10 | <8 | Ukrainian grammar is correct throughout. English is mostly clear. One awkward English translation at line 47: "Here is no water" should be "There is no water here." Three untranslated complex Ukrainian paragraphs at A1 level (addressed under Beginner Safety). |
| 6 | Pedagogy | 8/10 | <7 | PPP structure followed. Grammar section (lines 58-204, ~150 lines) is dense before the Practice section begins. No mini-exercise between Introduction and end of Grammar — long stretch of passive reading. Self-check game at line 272 is good but comes late. |
| 7 | Immersion | 8/10 | <6 | 28.8% vs target 25-40% — within range. Ukrainian exposure is well-distributed through examples, dialogues, and cultural sections. Callout box titles appropriately in Ukrainian. |
| 8 | Activities | 7/10 | <7 | 10 activities with good variety (group-sort, match-up, fill-in, unjumble, quiz). Three specific errors found: (1) distractor «води немає» is valid Ukrainian, (2) unjumble answers missing commas, (3) quiz grammar mismatch. Details in Critical Issues. |
| 9 | Richness | 8/10 | <6 | Strong cultural content: proverb «Немає диму без вогню», hospitality culture «Чим багаті, тим і раді», market interaction patterns, polite refusal conventions. Three realistic dialogues (café, service, shop). No named Ukrainian cultural figures beyond generic cultural practices. |
| 10 | Beginner Safety | 7/10 | <7 | "Would I Continue?" 4/5 (fails on quick wins — 150 lines of grammar before practice). Three paragraphs of complex untranslated Ukrainian at A1: lines 247, 302, 335-337 use vocabulary like «пряме», «різко», «фактична», «пом'якшує» without English support. Zero explicit encouragement phrases found. |
| 11 | LLM Fingerprint | 9/10 | <7 | No structural monotony — all H2 sections open differently. No clichéd metaphors. No "це не просто" rhetoric. No AI opener patterns. Example sentences are natural and varied. Dialogues feel authentic. |
| 12 | Linguistic Accuracy | 8/10 | <9 | IPA stress error on «мене»: transcribed as (first-syllable stress) at lines 33 and 68, but standard Ukrainian is мене́ (second-syllable stress). «День» (soft-stem) and «Батько» (-о ending) listed under hard-noun heading. IPA vowel quality issue in «інтернету» at line 67: [e] should be [ɛ]. |
| 13 | Factual Accuracy | 9/10 | <8 | Grammar rules are correctly explained. Proverb «Немає диму без вогню» is authentic. Gen.Pl. «проблем» correctly identified. «Гроші» as plural-only noun is accurate. Cultural claims about polite refusals and «Немає проблем» usage are plausible and accurate. No fabricated facts in callout boxes. |

**Weighted Overall:** (8×1.5 + 8×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 8×1.0 + 7×1.3 + 8×0.9 + 7×1.3 + 9×1.0 + 8×1.5 + 9×1.5) / 15.5 = (12 + 8 + 9 + 9.6 + 8.8 + 9.6 + 8 + 9.1 + 7.2 + 9.1 + 9 + 12 + 13.5) / 15.5 = 124.9 / 15.5 = **8.1/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Colonial framing: [CLEAN] — no Russian comparisons found
- Grammar scope: [CLEAN] — stays within genitive for absence/без
- Activity errors: [3 ISSUES] — bad distractor, missing commas, grammar mismatch
- Beginner safety: 4/5
- Factual accuracy: [CLEAN]
- LLM fingerprint: [CLEAN] — no monotony patterns detected

## Critical Issues Found

### Issue 1: IPA Stress Error on «мене» (Linguistic Accuracy)
- **Location**: Lines 33, 68 / Section «Вступ: Ситуація відсутності» and Section «Граматика: Конструкція «Немає» та «Без»»
- **Original**: «У мене немає квитка.» (line 33) and «У мене немає паспорта.» (line 68)
- **Problem**: The IPA transcription places stress on the first syllable. Standard Ukrainian pronunciation is мене́ with stress on the second syllable. This error appears twice, teaching incorrect pronunciation to beginners.
- **Fix**: Change to in both occurrences.

### Issue 2: Activity Distractor «води немає» Is Valid Ukrainian (Activities)
- **Location**: Activities file line 314 / Activity "Заповніть діалоги", item 6
- **Original**: sentence: «— Це вода? — Тут ... (немає вода).» with distractor option «води немає»
- **Problem**: «води немає» is perfectly valid Ukrainian with inverted word order. "Тут води немає" is a correct sentence. A learner selecting this would be marked wrong despite giving a correct answer.
- **Fix**: Replace distractor «води немає» with «немає воду» (incorrect accusative form) to create a genuinely wrong option.

### Issue 3: Untranslated Complex Ukrainian at A1 Level (Beginner Safety)
- **Location**: Lines 247, 302, 335-337 / Sections «Практика: Родовий відмінок у дії» and «Культурний контекст: «Немає проблем»»
- **Original**: «В українській культурі пряме «Ні» може звучати різко. Використовуйте **немає**. Це ввічливо. Це звучить як факт, а не відмова.» (line 247)
- **Problem**: Three paragraphs use vocabulary far beyond A1 level (пряме, різко, використовуйте, фактична, пом'якшує, фольклор, структуру відсутності) with zero English translation. An A1 learner at module 16 cannot parse these sentences.
- **Fix**: Add English translations after each untranslated paragraph, or rewrite these framing sentences in English with key Ukrainian phrases embedded.

### Issue 4: Unjumble Activity Missing Commas (Activities)
- **Location**: Activities file lines 126-131, 143-149 / Activity "Складіть речення"
- **Original**: «Кава без цукру будь ласка» (line 126) and «Вибачте у мене немає грошей» (line 143)
- **Problem**: Expected answers are missing required commas. Correct Ukrainian punctuation: «Кава без цукру, будь ласка» and «Вибачте, у мене немає грошей». Teaching incorrect punctuation to A1 learners builds bad habits.
- **Fix**: Add commas to expected answers.

### Issue 5: Quiz Activity Grammar Mismatch (Activities)
- **Location**: Activities file line 215 / Activity "Перевірка знань", item 6
- **Original**: Question asks «це ввічливо чи грубо?» but correct answer option reads «Ввічливі (Polite)»
- **Problem**: The question uses the predicative/adverb form "ввічливо" but the answer option uses the plural adjective form "Ввічливі" — grammatical inconsistency in the activity itself.
- **Fix**: Change answer text from «Ввічливі (Polite)» to «Ввічливо (Polite)».

### Issue 6: Zero Encouragement Phrases (Beginner Safety / Experience Quality)
- **Location**: Throughout all sections
- **Problem**: No explicit encouragement phrases found ("Great!", "Well done!", "You've got this!", "Excellent!"). The module maintains an informative tone throughout but lacks the warmth markers critical for A1 learners. Minimum requirement is ≥3 encouragement phrases.
- **Fix**: Add encouragement phrases after key examples and practice sections. E.g., after the Є vs Немає contrast (line 48): "Great — you can already see the pattern!" After the visual mapping table (line 223): "Well done getting this far!" Before the self-check game (line 272): "You've learned a lot — let's see it in action!"

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 33 | «» | «» | IPA stress |
| 47 | «(Here is no water.)» | «(There is no water here.)» | English grammar |
| 67 | «» | «» | IPA vowel quality |
| 68 | «» | «» | IPA stress |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — content is dense but well-organized with tables and callout boxes
- Instructions clear? **Pass** — English explanations present for all grammar concepts
- Quick wins? **Fail** — ~150 lines of grammar content (lines 58-204) before Practice section; no mini-exercise in the grammar section
- Ukrainian scary? **Pass** — Ukrainian is introduced with translations in most places
- Come back tomorrow? **Pass** — the cultural context section is engaging and the proverb gives a memorable takeaway

**Warmth markers:**
- Direct address (you/ви): ≥15 ✅
- Encouragement phrases: 0 ❌ (minimum: ≥3)
- "Don't worry" moments: 1 (line 189: "It is easy to mix up endings when you are learning")
- "You can now" validation: 1 (line 360: "You are now ready to navigate...")

## Strengths

- **Excellent common mistakes table** (lines 191-197): The side-by-side wrong/right/why format in section «Граматика: Конструкція «Немає» та «Без»» is exactly what beginners need — clear, visual, and preventative.
- **Strong cultural integration**: Section «Культурний контекст: «Немає проблем»» naturally reinforces grammar through authentic cultural practices (polite refusals, market interactions, the proverb «Немає диму без вогню»). This makes abstract grammar feel purposeful.
- **Well-designed dialogues**: Three distinct scenarios (café, key exchange, shop) in section «Практика: Родовий відмінок у дії» show the grammar in realistic contexts with natural Ukrainian phrasing like «Вибачте, круасанів немає» and «На жаль, хліба вже немає».
- **Clear -а vs -у distinction**: The concrete/abstract categorization at lines 98-112 is well-explained with memorable examples, addressing one of the most common genitive case errors.

## Fix Plan to Reach 9/10 (REQUIRED — score 8.1)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 33: Change IPA «» → «» — correct stress on мене
2. Line 68: Change IPA «» → «» — same fix
3. Line 67: Change IPA «» → «» — correct vowel quality
4. Lines 83-85: Move "День" and "Батько" out of the "### Genitive Endings: Masculine Hard Nouns (-а)" subsection into a separate "### Special Cases" subsection, or add explicit note that these are exceptions to the hard-noun pattern.

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Activities line 314: Replace distractor «води немає» with «немає воду» — eliminate valid-answer distractor
2. Activities line 126: Change answer to «Кава без цукру, будь ласка» — add comma
3. Activities line 143: Change answer to «Вибачте, у мене немає грошей» — add comma
4. Activities line 215: Change «Ввічливі (Polite)» to «Ввічливо (Polite)» — fix grammar mismatch

**Expected score after fix:** 9/10

### Beginner Safety: 7/10 → 9/10
**What to fix:**
1. Lines 247, 302, 335-337: Add English translations for all untranslated Ukrainian paragraphs
2. Add ≥3 explicit encouragement phrases at key transition points (after line 48, before line 209, before line 272)
3. Add warm opening to section «Вступ: Ситуація відсутності» — e.g., "You've made great progress! Today's lesson unlocks a powerful new tool."

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add warm greeting at module opening (before line 11 blockquote, or integrate into it)
2. Add "Today you'll learn to..." preview list after the opening blockquote
3. Add encouragement phrases (covered in Beginner Safety fixes above)

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 47: Change «(Here is no water.)» to «(There is no water here.)» — fix English grammar
2. Untranslated paragraphs (covered in Beginner Safety fixes)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 8×1.0 + 9×1.0 + 8×1.2 + 9×1.1 + 8×1.2 + 8×1.0 + 9×1.3 + 8×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 8 + 9 + 9.6 + 9.9 + 9.6 + 8 + 11.7 + 7.2 + 11.7 + 9 + 13.5 + 13.5) / 15.5
= 134.2 / 15.5
= 8.7/10
```

## Factual Verification

- Research notes consulted: YES (A1 core track — research notes exist and were read)
- Key Facts Ledger present: NO (not applicable for core grammar track)
- Dates checked: 0 (no dates in content)
- Named figures verified: 0 (no historical figures referenced)
- Primary quotes cross-referenced: 1 (proverb «Немає диму без вогню» — confirmed in research notes line 20)
- Chronological sequence: N/A
- Claims without research grounding: 0

Grammar rules verified:
- Genitive endings -а/-я for concrete masculine: CORRECT
- Genitive endings -у/-ю for abstract/substance masculine: CORRECT
- Feminine -а → -и, -я → -і: CORRECT
- Neuter -о → -а, -е → -я: CORRECT
- Гроші → грошей (Gen.Pl.): CORRECT
- Проблема → проблем (Gen.Pl.): CORRECT

## Verification Summary

- Content lines read: 361
- Activity items checked: 65 (across 10 activities)
- Ukrainian sentences verified: 48
- IPA transcriptions checked: 14
- Factual claims verified: 8
- Issues found: 6

## Verdict

**FAIL**

The module fails on **Linguistic Accuracy** (8/10, auto-fail threshold <9). The IPA stress error on «мене» appears twice (lines 33, 68), teaching incorrect pronunciation of a high-frequency pronoun. Additionally, three activity errors (bad distractor, missing commas, grammar mismatch) and missing beginner warmth markers need fixing. The content quality, grammar explanations, and cultural integration are strong — the fixes are targeted and achievable in one revision pass.

---

## Audit Failures (from automated re-audit)

```
Gates:   7 pass, 1 info
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-genitive-i-absence.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-genitive-i-absence.yaml
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

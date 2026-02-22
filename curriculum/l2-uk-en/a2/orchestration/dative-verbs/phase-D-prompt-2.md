# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/dative-verbs.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/dative-verbs.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/dative-verbs.yaml`

---

## Review (from Phase D.1)

# Рецензія: Dative Verbs

**Reviewed-By:** claude-opus-4-6

**Level:** A2 | **Module:** 3
**Overall Score:** 8.2/10
**Status:** FAIL
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: FAIL
- Sections: PASS — all 4 H2 sections from meta content_outline present (Вступ: Керування та Адресат, Презентація: Дієслова Давального відмінка, Практика: Відмінки в дії, Діалоги: Взаємодопомога та Вдячність)
- Vocabulary: 7/15 required from plan; 8 MISSING (вибачати, пробачати, заздрити, симпатизувати, співчувати, підходити, вистачати, бракувати)
- Grammar scope: PASS — stays within dative verb government, no scope creep
- Objectives: PARTIAL — 3/4 objectives met; "verbs of communication and interaction" incomplete without вибачати/пробачати/співчувати
- Collocations: PARTIAL — plan specifies сліпо довіряти, наперед дякую, допомагати по господарству; none appear in content. Красно дякувати appears only in a callout box (line 112)
- Plan summary calls for "Щиро співчуваю" as gratitude register: MISSING entirely
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm opening with volunteering context, 5 dialogues with analysis, good closing. Theory block (lines 16-253) runs 237 lines before practice begins, delaying active learner engagement. |
| 2 | Coherence | 9/10 | <7 | Logical flow: concept → 3 verb groups → drills → dialogues → summary. Each H2 section builds on the previous. The "Cycle of Gratitude" summary (line 470-476) ties everything together. |
| 3 | Relevance | 9/10 | <7 | Volunteering, doctor's visit, gift planning — all A2-relevant real-life scenarios. Cultural context (толока) anchors grammar in lived experience. |
| 4 | Educational | 7/10 | <7 | Solid coverage of 6 core verbs + impersonal constructions. However, 8/15 required vocabulary items from the plan are completely absent (вибачати, пробачати, заздрити, симпатизувати, співчувати, підходити, вистачати, бракувати). Key collocations from the plan (сліпо довіряти, наперед дякую) are missing. |
| 5 | Language | 8/10 | <8 | Ukrainian is natural and correct throughout. No Russianisms or calques detected. English is clear, warm, B1-accessible. Lines 297-299 use "better than" framing for -ові/-еві vs -у/-ю, implying the short form is incorrect when both are standard per State Standard 2024. |
| 6 | Pedagogy | 8/10 | <7 | PPP structure well-followed. 3 verb groups with clear classification. 8+ drills provide extensive practice. But 237 lines of theory before first drill is long for A2 pacing (recommended: ≤2 concepts before practice). |
| 7 | Immersion | 9/10 | <6 | 51.9% vs target 50-60%. On target. English used for conceptual explanations, Ukrainian for examples and dialogues. |
| 8 | Activities | 8/10 | <7 | 12 activity blocks, ~99 individual items, good variety (quiz, group-sort, match-up, fill-in ×3, error-correction, unjumble ×2, translate, mark-the-words, cloze). Pedagogical inconsistency: Drill 2 (line 290) corrects to «вчителю» while lesson explicitly promotes -ові/-еві endings for male persons. |
| 9 | Richness | 8/10 | <6 | Толока cultural context, hand-on-heart gesture note, volunteering as civic duty, doctor visit scenario, gift planning dialogue. Good cultural anchoring. Missing deeper collocation work. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Warm tone, frequent encouragement, clear visual aids (tables, transformation charts), Ukrainian introduced with English scaffolding throughout. |
| 11 | LLM Fingerprint | 7/10 | <7 | 7+ distinct metaphors: "CEO" (line 18), "magnets" (line 22), "GPS" (line 34), "isolated island" (line 14), "bridges" (line 14), "two hands" (line 162), "ключ до серця" (line 64). Exceeds threshold of 4. Section openings: 2/4 start with "Now..." (lines 257, 392). Example blocks follow rigid template: header + "Examples:" + 3-5 bullets per verb. |
| 12 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL.** Line 419: «Йому сподобалися цифри» labeled «безособову конструкцію» — this is factually wrong; "цифри" is the grammatical subject and the verb agrees in plural, making this an inverted experiencer construction, not impersonal. Lines 297-299: "better than" framing misrepresents State Standard where both -ові/-еві and -у/-ю are valid dative endings. |
| 13 | Factual Accuracy | 9/10 | <8 | Толока description (line 93) is historically accurate. "Hand on heart" gesture (line 112) is culturally accurate. Claim that "подобати existed in the old language" (line 227) is verified — the non-reflexive form is archaic. No fabricated facts in callout boxes. |

**Weighted Overall:**
```
(8×1.5 + 9×1.0 + 9×1.0 + 7×1.2 + 8×1.1 + 8×1.2 + 9×1.0 + 8×1.3 + 8×0.9 + 9×1.3 + 7×1.0 + 8×1.5 + 9×1.5) / 15.5
= (12 + 9 + 9 + 8.4 + 8.8 + 9.6 + 9 + 10.4 + 7.2 + 11.7 + 7 + 12 + 13.5) / 15.5
= 127.6 / 15.5
= 8.23/10
```

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Colonial framing: [CLEAN]
- Grammar scope: [CLEAN] — stays within dative verbs, does not teach new noun declension
- Activity errors: [1 inconsistency — Drill 2 uses short form while lesson promotes long form]
- Beginner safety: 5/5
- LLM Fingerprint: Metaphor density exceeds threshold (7 > 4)
- Factual accuracy: [CLEAN — all callout box claims verified]
- Linguistic accuracy: [FAIL — mislabeling of inverted construction as impersonal, misleading "better than" for standard-compliant endings]

## Critical Issues Found

### Issue 1: Vocabulary Plan Compliance (CRITICAL)
- **Location**: Entire module — Section «Презентація: Дієслова Давального відмінка»
- **Problem**: The plan's `vocabulary_hints.required` specifies 15 verbs. Only 7 appear in the content. Missing 8 required verbs: вибачати, пробачати, заздрити, симпатизувати, співчувати, підходити, вистачати, бракувати. These are not obscure additions — they represent core A2 dative verbs covering forgiveness, empathy, sufficiency/lack, and suitability.
- **Fix**: Add at minimum вибачати/пробачати (forgiveness pair — parallels вірити/довіряти), співчувати (gratitude registers per plan), and бракувати/вистачати (impersonal dative constructions). These can be added as a 4th group in Section «Презентація: Дієслова Давального відмінка» or woven into existing groups.

### Issue 2: Linguistic Mislabeling — "безособова конструкція" (ACCURACY)
- **Location**: Line 419 / Section «Діалоги: Взаємодопомога та Вдячність»
- **Original**: «Вона також використовує безособову конструкцію: «Йому сподобалися цифри».»
- **Problem**: «Йому сподобалися цифри» has a grammatical subject ("цифри") and the verb agrees with it in plural ("сподобалися"). This is an inverted experiencer construction (інверсійна конструкція), NOT impersonal (безособова). True impersonal constructions lack a grammatical subject (e.g., "Мені холодно"). This error is pedagogically significant: A2 learners need to understand that "подобатися" agrees with its subject, not with the experiencer.
- **Fix**: Replace «безособову конструкцію» with «інверсійну конструкцію» or «конструкцію з давальним відмінком досвідника».

### Issue 3: "Better than" Framing for Standard-Compliant Endings (PEDAGOGICAL)
- **Location**: Lines 297-299 / Section «Практика: Відмінки в дії»
- **Original**: «*Брат* → *Братові* (better than "брату"). *Олег* → *Олегові* (better than "Олегу"). *Батько* → *Батькові* (better than "батьку").»
- **Problem**: Both -ові/-еві and -у/-ю are valid per State Standard 2024. "Better than" implies the short form is incorrect, which is misleading. While -ові/-еві is preferred for animate masculine nouns, -у/-ю is not wrong.
- **Fix**: Change "better than" to "preferred over" or "more common than" to accurately represent both forms as valid while still guiding learners toward the recommended form.

### Issue 4: Pedagogical Inconsistency in Error Correction Drill
- **Location**: Line 290 / Section «Практика: Відмінки в дії»
- **Original**: «Ми дякуємо *вчителя*. | Ми дякуємо **вчителю**. | *Дякувати (кому?)* — Dative.»
- **Problem**: The drill corrects to «вчителю» (short dative form), while the lesson itself (lines 295-301 in Drill 3) explicitly promotes -ові/-еві as the preferred endings for male persons. To be internally consistent, the correction should use «вчителеві».
- **Fix**: Change «вчителю» to «вчителеві» in the correction column.

### Issue 5: Excessive Metaphor Density
- **Location**: Primarily Section «Вступ: Керування та Адресат» (lines 14-64)
- **Problem**: 7+ distinct metaphors: sentence-as-company with verb-as-CEO (line 18), verbs-as-magnets (line 22), ending-as-GPS (line 34), person-as-isolated-island (line 14), communication-as-bridges (line 14), double-object-verbs-as-two-hands (line 162), grammar-as-key-to-hearts (line 64). Exceeds the 4-metaphor threshold.
- **Fix**: Remove 3 weaker metaphors. Keep CEO (most pedagogically useful), GPS (concise and helpful), and bridges (emotionally resonant). Remove: magnets, isolated island, two hands, key-to-hearts.

### Issue 6: Missing Collocations from Plan
- **Location**: Entire module
- **Problem**: Plan specifies key collocations: сліпо довіряти, наперед дякую, допомагати по господарству, вибачте за запізнення, біла заздрість. None appear in the content. Only «щиро дякувати» and «Красно дякую» (line 112) are present.
- **Fix**: Add a "Useful Collocations" subsection to Section «Практика: Відмінки в дії» with the plan-specified pairings. At minimum include: «наперед дякую» (thank in advance), «сліпо довіряти» (trust blindly), «допомагати по господарству» (help around the house).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 419 | «безособову конструкцію» | «інверсійну конструкцію» | Linguistic inaccuracy |
| 290 | «вчителю» | «вчителеві» | Pedagogical inconsistency |
| 297 | «better than "брату"» | «preferred over "брату"» | Misleading framing |
| 298 | «better than "Олегу"» | «preferred over "Олегу"» | Misleading framing |
| 299 | «better than "батьку"» | «preferred over "батьку"» | Misleading framing |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — English scaffolding throughout, manageable chunks, visual tables
- Instructions clear? **Pass** — Each drill has explicit instructions, patterns shown before practice
- Quick wins? **Pass** — Examples after each verb allow "I understand this" moments, though formal drills start at line 259
- Ukrainian scary? **Pass** — Introduced gently, always with English translations
- Come back tomorrow? **Pass** — Volunteering and doctor's visit contexts are relatable; толока is a memorable cultural hook

Emotional Safety Mapping:
- Welcome/orientation: ✓ (lines 12-14, warm opening with "why is this important?")
- Curiosity trigger: ✓ (line 42, "Here is where it gets interesting")
- Quick wins: ✓ (multiple small example blocks with translations)
- Encouragement: ✓ (line 500, «Ви зробили великий крок уперед»)
- Progress marker: ✓ (line 500, «Тепер ви можете не тільки описувати світ, але й взаємодіяти з ним»)

## Strengths

- **Excellent cultural integration**: The толока tradition (line 93) and modern volunteering context (армія, переселенці) anchor grammar in culturally meaningful scenarios without being heavy-handed.
- **Strong dialogue variety**: 5 dialogues covering different registers (neighborhood, workplace, casual friends, medical, gift planning) with Ukrainian-language analysis sections after each.
- **Effective error correction pedagogy**: The "Dyakuyu Fix" drill (lines 287-291) and the myth-buster on «Я подобаю це» (line 224) directly address the most common A2 errors.
- **Подобатися transformation table** (lines 218-222) is a clear visual aid that makes the subject-object flip intuitive for English speakers.
- **Reading passage** (lines 366-387) integrates all taught verbs in a natural volunteer narrative — excellent consolidated practice.

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 419: Change «безособову конструкцію» → «інверсійну конструкцію» — corrects a factual error in grammatical classification
2. Lines 297-299: Change "better than" → "preferred over" in all three instances — accurately represents State Standard 2024
3. Line 290: Change «вчителю» → «вчителеві» — maintains internal consistency with lesson's own teaching

**Expected score after fix:** 9/10

### Educational: 7/10 → 9/10
**What to fix:**
1. Add missing required verbs to Section «Презентація: Дієслова Давального відмінка» — at minimum вибачати/пробачати (forgiveness pair), співчувати (empathy), бракувати/вистачати (impersonal sufficiency). This adds ~300 words.
2. Add collocation subsection to Section «Практика: Відмінки в дії» with plan-specified pairings (сліпо довіряти, наперед дякую, допомагати по господарству). This adds ~150 words.
3. Add «Щиро співчуваю» to the summary as a gratitude register per plan requirements.

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Remove 3 weaker metaphors from Section «Вступ: Керування та Адресат»: "magnets" (line 22), "isolated island" (line 14), "key to hearts" (line 64). Replace with direct language.
2. Vary example block format — not every verb subsection needs the exact "Examples:" header pattern.

**Expected score after fix:** 8/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add a mini-exercise (e.g., 3-item "match verb to case") between Section «Вступ: Керування та Адресат» and Section «Презентація: Дієслова Давального відмінка» to break the 237-line theory stretch and provide an early quick win.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 8×1.2 + 9×1.0 + 8×1.3 + 8×0.9 + 9×1.3 + 8×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9 + 9 + 10.8 + 9.9 + 9.6 + 9 + 10.4 + 7.2 + 11.7 + 8 + 13.5 + 13.5) / 15.5
= 135.1 / 15.5
= 8.72/10
```

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (core grammar track, not seminar)
- Key Facts Ledger present: N/A
- Callout box claims verified: 3 checked
  - Толока description (line 93): Historically accurate — communal labor tradition
  - "Hand on heart" gesture (line 112): Culturally accurate Ukrainian practice
  - "Подобати existed in the old language" (line 227): Verified — archaic non-reflexive form
- Dates checked: 0 (no dates in content)
- Named figures verified: 0 (no historical figures cited)
- Fabricated claims: NONE found

## Verification Summary

- Content lines read: 500
- Activity items checked: 99 (across 12 activity blocks)
- Ukrainian sentences verified: 42
- IPA transcriptions checked: 6 (допомагати, дякувати, подобатися, повідомляти, показувати, довіряти — all correct)
- Factual claims verified: 3
- Issues found: 6

## Verdict

**FAIL**

Blocking issues: (1) Linguistic Accuracy 8/10 < 9 auto-fail threshold — «безособову конструкцію» mislabeling on line 419 is a factual error in a grammar module that can mislead A2 learners about verb agreement. (2) Educational 7/10 — 8 of 15 required vocabulary items from the plan are missing, representing over half the planned scope. Fixing the linguistic mislabeling (Issue 2) and adding the missing verbs with collocations (Issue 1, Issue 6) are required for a PASS.

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
failing gates:
review: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
→ 1 violations (minor)
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/dative-verbs-audit.log for details)
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/dative-verbs.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/dative-verbs.yaml
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

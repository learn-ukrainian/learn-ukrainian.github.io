# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/description-adverbs.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/description-adverbs.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/description-adverbs.yaml`

---

## Review (from Phase D.1)

# Рецензія: Description: Adverbs

**Reviewed-By:** claude-opus-4-6

**Level:** A1 | **Module:** 28
**Overall Score:** 8.0/10
**Status:** FAIL
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: 5/5 H2 sections present and match meta outline
- Vocabulary: 20/20 items present; 4 recommended items missing (тут, там, сьогодні, завтра)
- Grammar scope: VIOLATION — comparative adverb form "тихіше" introduced despite SCOPE excluding it
- Objectives: 4/4 objectives addressed
- Persona: MISSING — plan specifies "Food Critic" roleplay but no food critic content exists
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Well-structured lesson arc with warm opening, stories, dialogues, and self-check. Missing Food Critic persona from plan. Closing self-check questions lack a "You can now..." celebration. |
| 2 | Coherence | 8/10 | <7 | Good flow: adj vs adv distinction → formation → frequency → intensity → practice. Marred by word order inconsistency: teaches "after verb" rule (line 130) but own examples use "before verb" for «добре» (lines 64, 117, 364, 381). |
| 3 | Relevance | 9/10 | <7 | Daily habits, lifestyle, station dialogue — all highly relevant to A1 learner needs. Strong practical orientation. |
| 4 | Educational | 7/10 | <7 | Solid grammar explanations and formation rule. Scope violation with comparative «тихіше». Word order teaching contradicts own examples. The "Ніколи не..." activity (8 identical-answer items) drills one point excessively without progressive complexity. |
| 5 | Language | 8/10 | <8 | Clean of Russianisms and colonial framing. One unnatural sentence: «Я роблю фінал» (line 250). English explanations are clear and B1-accessible. |
| 6 | Pedagogy | 7/10 | <7 | PPP structure executed well. Missing Food Critic persona entirely — plan explicitly requires "Roleplay as a 'Food Critic' describing how someone cooks or eats." Word order rule taught at line 130 is contradicted by own examples at lines 64, 117, 381. |
| 7 | Immersion | 7/10 | <6 | 35.2% vs target 35-55% — technically within range but at absolute floor. For an A1.3 Consolidation module, this is low. |
| 8 | Activities | 8/10 | <7 | 10 activities with good variety (group-sort, fill-in, match-up, quiz, unjumble). Unjumble line 170-171 expects "Я добре розумію" (adverb before verb) contradicting the lesson's stated rule. "Ніколи не..." fill-in: all 8 items have identical answer "не" — excessive repetition. |
| 9 | Richness | 8/10 | <6 | Strong cultural elements: «Добре» as agreement marker, proverb «Тихіше їдеш — далі будеш», multiple named characters (Іван, Олена, Ігор, Максим, Олег, Андрій, Марія). Missing food/cooking cultural angle from plan. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Clear English scaffolding, encouraging tip boxes, manageable chunks. Module is long (2915 words, 145% target) but well-structured. Minor: no explicit "You can now..." celebration at end. |
| 11 | LLM Fingerprint | 8/10 | <7 | "Here are some examples:" appears 3× (lines 26, 41, 89) — structural monotony. "Let's" appears 8× as section openers. Voice is otherwise warm and natural tutoring tone, no purple prose or "це не просто" patterns. |
| 12 | Linguistic Accuracy | 8/10 | <9 | IPA stress error: «зовсім» transcribed as [ˈzɔu̯sʲim] (line 223) — stress should be on second syllable [zɔu̯ˈsʲim]. Unnatural sentence «Я роблю фінал» (line 250). Word order examples contradicting stated rules. |
| 13 | Factual Accuracy | 9/10 | <8 | [!culture] box on «добре» (line 120-126): accurate. [!myth-buster] on "very much" placement (line 271-275): accurate. Proverb «Тихіше їдеш — далі будеш» (line 336): real proverb, correctly cited. Grammar rules are accurate. |

**Weighted Overall:**
```
(8×1.5) + (8×1.0) + (9×1.0) + (7×1.2) + (8×1.1) + (7×1.2) + (7×1.0) + (8×1.3) + (8×0.9) + (9×1.3) + (8×1.0) + (8×1.5) + (9×1.5)
= 12 + 8 + 9 + 8.4 + 8.8 + 8.4 + 7 + 10.4 + 7.2 + 11.7 + 8 + 12 + 13.5
= 124.4 / 15.5 = **8.0/10**
```

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: «Я роблю фінал» (line 250) — possible English calque of "I'm doing the final"
- Colonial framing: [CLEAN] — no Russian comparisons found
- Grammar scope: [VIOLATION] — comparative form «тихіше» (line 336-340) introduced and explained despite SCOPE comment (line 3) explicitly excluding "Comparative/Superlative degrees of adverbs (B1 topic)"
- Activity errors: Unjumble answer "Я добре розумію" (activity line 171) contradicts lesson's stated word order rule
- Beginner safety: 5/5
- Factual accuracy: [CLEAN]

## Critical Issues Found

### Issue 1: IPA Stress Error on «зовсім»
- **Location**: Line 223 / Section «Презентація 3: Ступені та Інтенсивність»
- **Original**: «**зовсім** [ˈzɔu̯sʲim] — at all / completely / quite»
- **Problem**: Stress mark placed on first syllable [ˈzɔu̯sʲim]. The correct stress for зовсім is on the second syllable: зовСІМ.
- **Fix**: Change IPA to `[zɔu̯ˈsʲim]`

### Issue 2: Unnatural Ukrainian «Я роблю фінал»
- **Location**: Line 250 / Section «Презентація 3: Ступені та Інтенсивність»
- **Original**: «Я знаю. Я вже **майже** готовий. Я роблю фінал.»
- **Problem**: «Робити фінал» is not natural Ukrainian. This appears to be a calque from English "I'm doing the final." A native speaker would say «Я закінчую» or «Я завершую».
- **Fix**: Replace with «Я знаю. Я вже **майже** готовий. Я закінчую.»

### Issue 3: Grammar Scope Violation — Comparative Form «тихіше»
- **Location**: Lines 336-340 / Section «Практика: Звички та Стиль Життя»
- **Original**: «**тихіше** (quieter/slower) acts as an adverb describing the manner of movement»
- **Problem**: The SCOPE comment (line 3) explicitly states "Not covered: Comparative/Superlative degrees of adverbs (B1 topic)." Yet the content introduces and explains the comparative form «тихіше». The plan used «Повільно їдеш — далі будеш» (basic adverb form) rather than «Тихіше їдеш — далі будеш» (comparative form), presumably to avoid this scope violation.
- **Fix**: Either (a) replace the proverb with «Повільно їдеш — далі будеш» as the plan intended and remove the comparative grammar explanation, or (b) keep the authentic proverb but remove the grammar explanation of «тихіше» and simply gloss it as "slower" without morphological analysis.

### Issue 4: Missing Food Critic Persona
- **Location**: Entire module / All sections
- **Original**: N/A — content does not exist
- **Problem**: The plan (line 51-52) specifies `role: Food Critic` with direction to include "Roleplay as a 'Food Critic' (persona) describing how someone cooks or eats (добре, погано, дуже смачно)." The meta also lists persona role as "Food Critic." This is completely absent from the module.
- **Fix**: Add a Food Critic roleplay subsection to section «Практика: Звички та Стиль Життя», e.g., a dialogue where the learner plays a food critic evaluating how a chef cooks (швидко, повільно, смачно, добре, погано).

### Issue 5: Word Order Inconsistency Between Rule and Examples
- **Location**: Lines 64, 117, 381 vs. line 130 / Sections «Розминка: Як чи Який?» and «Презентація: Утворення та Винятки»
- **Original**: Rule at line 130: "the most neutral position is **after the verb**" / Examples: «Він **добре** знає Київ» (line 64), «Я **добре** розумію» (line 117)
- **Problem**: The lesson teaches that manner adverbs go after the verb (line 130) and advises learners to "stick to after the verb" (line 138). But the module's own examples repeatedly place «добре» before the verb. This confuses A1 learners who are trying to internalize the rule.
- **Fix**: Either (a) change the examples to match the rule: «Він знає Київ **добре**», «Я розумію **добре**»; or (b) explicitly note that «добре» is commonly used before the verb as a natural exception to the general pattern. Option (b) is linguistically more honest. Also fix unjumble activity (activity line 170-171) to match whichever approach is chosen.

### Issue 6: Repetitive Activity — "Ніколи не..." Fill-in
- **Location**: Activity lines 196-224 / Activity #7
- **Original**: 8 items all with identical answer "не" and identical structure "X ніколи {{answer}} Y"
- **Problem**: All 8 items test the exact same point with zero progressive difficulty. After item 2, the learner is clicking "не" mechanically. This doesn't develop competence — it tests short-term memory of a single word.
- **Fix**: Reduce to 4 items and add 4 items that mix "ніколи не" with other frequency adverb patterns (e.g., "Я _____ снідаю вдома" where the answer is "зазвичай" or "часто"), creating a discriminative exercise rather than a repetition drill.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 223 | «зовсім [ˈzɔu̯sʲim]» | «зовсім [zɔu̯ˈsʲim]» | IPA stress error |
| 250 | «Я роблю фінал» | «Я закінчую» | Unnatural/calque |
| 336 | «Тихіше їдеш — далі будеш» (with grammar explanation of comparative) | Remove comparative grammar analysis or use «Повільно їдеш — далі будеш» | Scope violation |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — Good chunking despite 2915 words. Clear section breaks and visual tables.
- Instructions clear? **Pass** — English explanations are concise and B1-accessible. Grammar rules use clear formulas.
- Quick wins? **Pass** — First section (adj vs adv distinction) builds on known adjective knowledge. Pairs table at line 50-53 gives immediate understanding.
- Ukrainian scary? **Pass** — Ukrainian introduced with English translations throughout. IPA provided for key words. Tip boxes in Ukrainian are simple and encouraging.
- Come back tomorrow? **Pass** — Engaging stories (Ivan, Maksym, Oleh), realistic dialogues (station, friends), and a motivational closing tip box.

## Strengths
- Clear conceptual distinction between adjectives and adverbs through the Який?/Як? framework with visual table (section «Розминка: Як чи Який?»)
- Multiple named characters with distinct lifestyles (Іван the student, Максим the musician, Олег the office worker) make practice sections engaging
- Strong cultural grounding with the «Добре» usage insight (line 120-126) and the proverb (line 336)
- Good activity variety: 6 distinct activity types across 10 exercises
- Double negation rule (section «Презентація 2: Як часто?», lines 185-203) is clearly explained with formula and correct/incorrect examples

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 223: Change IPA `[ˈzɔu̯sʲim]` → `[zɔu̯ˈsʲim]` — wrong stress placement
2. Line 250: Change «Я роблю фінал» → «Я закінчую» — unnatural Ukrainian
3. Lines 64, 117, 381: Either move «добре» after the verb in examples OR add an explicit note that «добре» commonly precedes the verb — resolves contradiction with rule at line 130

**Expected score after fix:** 9/10

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Add Food Critic roleplay subsection to section «Практика: Звички та Стиль Життя» — plan mandates this persona
2. Resolve word order rule/example conflict (see Linguistic Accuracy fix #3)
3. Lines 336-340: Remove comparative grammar explanation of «тихіше» — keep the proverb as cultural exposure only, or replace with plan's version «Повільно їдеш — далі будеш»

**Expected score after fix:** 9/10

### Educational: 7/10 → 9/10
**What to fix:**
1. Activity lines 196-224: Reduce "Ніколи не..." to 4 items, add 4 discriminative items mixing different frequency adverbs
2. Activity line 170-171: Fix unjumble answer to match the taught word order rule
3. Resolve scope violation (comparative form)

**Expected score after fix:** 9/10

### Coherence: 8/10 → 9/10
**What to fix:**
1. Resolve the word order contradiction (fixes #3 from Linguistic Accuracy above)
2. Add transitional sentence before section «Практика: Звички та Стиль Життя» that sets up the Food Critic angle

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Lines 26, 41, 89: Vary the "Here are some examples:" transitions — use different phrasings (e.g., "Try these:", "Look at how this works:", "See the pattern:")
2. Reduce "Let's" openers — at least 3 of the 8 instances should use different transitions

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5) + (9×1.0) + (9×1.0) + (9×1.2) + (8×1.1) + (9×1.2) + (7×1.0) + (8×1.3) + (8×0.9) + (9×1.3) + (9×1.0) + (9×1.5) + (9×1.5)
= 13.5 + 9 + 9 + 10.8 + 8.8 + 10.8 + 7 + 10.4 + 7.2 + 11.7 + 9 + 13.5 + 13.5
= 134.2 / 15.5 = 8.7/10
```

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (core grammar track, not seminar)
- Key Facts Ledger present: NO
- Dates checked: 0 (no historical dates in module)
- Named figures verified: 0 (characters are fictional — Ivan, Maksym, Oleh, etc.)
- Primary quotes cross-referenced: 1 — proverb «Тихіше їдеш — далі будеш» is a real Ukrainian proverb, correctly cited
- Chronological sequence: NOT_APPLICABLE
- Claims without research grounding: 0

**Callout box verification:**
- [!culture] (line 120): «Добре» as universal agreement word — VERIFIED, culturally accurate
- [!myth-buster] (line 271): "very much" placement difference English vs Ukrainian — VERIFIED, linguistically accurate
- [!quote] (line 335): Proverb and meaning — VERIFIED (though comparative form is scope concern, not factual error)

## Verification Summary

- Content lines read: 419
- Activity items checked: 80+ (across 10 activities)
- Ukrainian sentences verified: 45+
- IPA transcriptions checked: 12 (1 error found: зовсім)
- Factual claims verified: 3 callout boxes
- Issues found: 6

## Verdict

**FAIL**

Blocking issues: (1) Linguistic Accuracy 8/10 triggers auto-fail threshold (<9). IPA stress error on «зовсім» and unnatural «Я роблю фінал» must be fixed. (2) Grammar scope violation — comparative form «тихіше» explained despite explicit SCOPE exclusion. (3) Missing Food Critic persona required by plan and meta. (4) Word order rule contradicted by own examples creates pedagogical confusion for A1 learners.

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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/description-adverbs.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/description-adverbs.yaml
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

# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/the-dative-ii-nouns.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/the-dative-ii-nouns.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/vocabulary/the-dative-ii-nouns.yaml`

---

## Review (from Phase D.1)

# Рецензія: The Dative II — Nouns

**Reviewed-By:** claude-opus-4-6

**Level:** A2 | **Module:** 2
**Overall Score:** 7.7/10
**Status:** FAIL
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: 7/7 H2 present (plan's 4 sections split into 7 — acceptable granularity)
- Vocabulary: 13/15 required vocab in YAML; 8/15 actually appear in content prose.
  личити, заважати, вистачати, бракувати completely absent from content.
  дозволяти, шкодити absent from vocabulary YAML entirely.
- Grammar scope: CLEAN — no grammar from later modules
- Objectives: 4/4 objectives met in content (form M/F/N/Pl endings, use with verbs)
- Missing plan-required elements:
  1. «Дідусеві 80 років» age example (plan §1 explicit requirement)
  2. «личити» practice with clothing contexts (plan §4 explicit requirement)
  3. «давати відповідь» collocation (plan vocabulary_hints.required)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Well-structured arc from concept→endings→practice→culture→dialogue. Cultural content (flowers, taboo gifts, Name Day) keeps learner engaged. Dense in some sections (Section «Чоловічий та середній рід: -ові/-у» covers euphony, neuter, AND disambiguation) |
| 2 | Coherence | 8/10 | <7 | Logical progression. Minor inconsistency: summary at line 212 says «Дочка → Дочці» but section examples use «Донька → Доньці» (lines 179, 203) |
| 3 | Relevance | 7/10 | <7 | 5 plan-required verbs (личити, заважати, вистачати, бракувати + давати відповідь collocation) absent from content despite appearing in vocabulary YAML |
| 4 | Educational | 7/10 | <7 | Grammar explanations are clear with good tables. But vocab gap means learners encounter 5+ words in vocab list they never saw in context. Missing «Дідусеві 80 років» from age section |
| 5 | Language | 7/10 | **<8 ❌** | Line 65 factual error claiming -ові is unique to Ukrainian. Line 206 «Палаталізацію задньоязикових» is C1+ terminology. Line 20 «бенефіціаром» is C1+ register. Line 343 «моветон» is C1+. Line 281 misuses `[!decolonization]` for a simple grammar contrast |
| 6 | Pedagogy | 7/10 | <7 | Good PPP flow with present→practice→produce. But vocab-content disconnect undermines PPP: vocabulary items личити, заважати, вистачати, бракувати taught in vocab file but never presented or practiced in prose |
| 7 | Immersion | 9/10 | <6 | 56.9% vs target 50-60%. English used for grammar logic, Ukrainian for examples. Appropriate for A2 M01-20 band |
| 8 | Activities | 7/10 | <7 | 12 activities with good variety (8 types). Cloze blank 7 «людям» and blank 10 «колегам» contextually implausible. Fill-in «Ми йдемо назустріч (муха)» semantically absurd. No activities for личити/заважати/вистачати/бракувати |
| 9 | Richness | 8/10 | <6 | Strong cultural hooks: flower number etiquette, taboo gifts with coin workaround, Name Day celebration. 4 dialogue scenes. 8 callout boxes. |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 3.5/5 — warm tone throughout, but Ukrainian prose contains C1+ vocabulary (бенефіціаром, палаталізація задньоязикових, моветон) without glossing |
| 11 | LLM Fingerprint | 8/10 | <7 | Section openings are varied (no structural monotony). Line 67 has staccato dramatic pattern: «It sounds melodious. It is purely Ukrainian. It adds respect.» 1 metaphor flagged (line 267 "magnet"). Below threshold |
| 12 | Linguistic Accuracy | 8/10 | **<9 ❌** | Line 185 sentence fragments. Line 212 summary mismatch. Line 100 confusing «Accusative/Genitive» label. Line 343 «дві квіти» should be «дві квітки» |
| 13 | Factual Accuracy | 8/10 | <8 | Line 65: Claims -ові "distinguishing it from neighboring Slavic languages" — Polish has -owi, Czech has -ovi. Inaccurate superlative/uniqueness claim |

**Weighted Overall:**
```
(8×1.5 + 8×1.0 + 7×1.0 + 7×1.2 + 7×1.1 + 7×1.2 + 9×1.0 + 7×1.3 + 8×0.9 + 8×1.3 + 8×1.0 + 8×1.5 + 8×1.5) / 15.5
= (12.0 + 8.0 + 7.0 + 8.4 + 7.7 + 8.4 + 9.0 + 9.1 + 7.2 + 10.4 + 8.0 + 12.0 + 12.0) / 15.5
= 119.2 / 15.5
= 7.7/10
```

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no помагати, кушати, or similar detected
- Calques: [CLEAN] — no structural calques detected
- Colonial framing: Line 65 «distinguishing it from neighboring Slavic languages» — defines Ukrainian feature via contrast with others (borderline, not Russian-specific)
- Grammar scope: [CLEAN] — stays within Dative noun scope
- Activity errors: 3 implausible items (fill-in муха, cloze blanks 7/10)
- Beginner safety: 3.5/5
- Factual accuracy: 1 inaccurate uniqueness claim (line 65)

## Critical Issues Found

### Issue 1: Plan-Required Verb «личити» Completely Absent
- **Location**: Entire content file / Section «Ключові дієслова та керування»
- **Problem**: The plan explicitly requires: "Practice the verb «личити» (Medium frequency) in descriptive contexts — use clothing and style examples: «ця сукня тобі личить»." The verb appears in vocabulary/the-dative-ii-nouns.yaml (line 51-55) but is never introduced, explained, or practiced anywhere in the content prose or activities.
- **Fix**: Add a subsection in Section «Ключові дієслова та керування» covering «личити» with clothing examples. Add 2-3 activity items practicing this verb.

### Issue 2: Factual Inaccuracy — Uniqueness Claim
- **Location**: Line 65 / Section «Чоловічий та середній рід: -ові/-у»
- **Original**: «This flexibility is a unique feature of Ukrainian, distinguishing it from neighboring Slavic languages.»
- **Problem**: Polish Dative uses -owi (bratu / bratowi), Czech uses -ovi. The -ові ending is NOT unique to Ukrainian. This is a fabricated superlative claim.
- **Fix**: Replace with: "This flexibility is a characteristic feature of Ukrainian. The choice between -ові and -у gives speakers stylistic control over their tone."

### Issue 3: C1+ Vocabulary in A2 Ukrainian Prose
- **Location**: Line 20 / Section «Вступ: Концепція адресата»
- **Original**: «Хто є бенефіціаром вашої дії?»
- **Problem**: «бенефіціаром» is C1+ academic vocabulary. An A2 learner reading this Ukrainian sentence would not understand this word.
- **Fix**: Replace with «Хто отримує результат вашої дії?» — uses A2-accessible vocabulary.

### Issue 4: C1+ Terminology «Палаталізацію задньоязикових»
- **Location**: Line 206 / Section «Жіночий рід та чергування приголосних»
- **Original**: «Ця таблиця підсумовує "Палаталізацію задньоязикових".»
- **Problem**: University-level phonology terminology (palatalization of velars) in A2 content. Completely opaque to target audience.
- **Fix**: Replace with «Ця таблиця підсумовує зміни звуків Г, К, Х перед закінченням -і.»

### Issue 5: Sentence Fragments
- **Location**: Line 185 / Section «Жіночий рід та чергування приголосних»
- **Original**: «Якщо ви даруєте квіти **доньці**. Якщо ви адресуєте посилку **аптеці**.»
- **Problem**: Two incomplete conditional sentences with no main clause. These are grammatically incorrect fragments.
- **Fix**: Convert to statements: «Ви даруєте квіти **доньці**. Ви адресуєте посилку **аптеці**.»

### Issue 6: Summary Inconsistency
- **Location**: Line 212 / Section «Жіночий рід та чергування приголосних»
- **Original**: «Приклади: Мама → Мамі, Ольга → Ользі, Дочка → Дочці.»
- **Problem**: Summary uses «Дочка → Дочці» but the section examples teach «Донь**к**а — Донь**ц**і» (lines 179, 203). While both words mean "daughter" and both undergo К→Ц, using a different lexeme in the summary than in the examples creates confusion.
- **Fix**: Change to «Донька → Доньці» to match the examples taught above.

### Issue 7: Implausible Activity Item
- **Location**: Activities file line 191-194
- **Original**: «Ми йдемо назустріч (муха).» → answer: «мусі»
- **Problem**: "We go towards a fly" is semantically absurd. No one walks towards a fly intentionally.
- **Fix**: Replace with «Я приношу їжу (муха).» → answer: «мусі» — or a sentence about a child being scared of a fly.

### Issue 8: Missing Plan-Required Age Example
- **Location**: Lines 48-60 / Section «Вступ: Концепція адресата»
- **Problem**: Plan §1 explicitly requires «Дідусеві вісімдесят років» as an example. The age section uses «Студентові», «Батькові», «Сестрі» but NOT «Дідусеві». This also means the -еві ending for soft stems is not demonstrated in the age context.
- **Fix**: Add «**Дідусеві** вісімдесят років. — To grandfather is 80 years.» as an example.

### Issue 9: Misused `[!decolonization]` Callout
- **Location**: Line 281 / Section «Ключові дієслова та керування»
- **Original**: `[!decolonization]` with title «Мовний суверенітет» explaining that «допомагати» takes Dative unlike English "help" (Accusative)
- **Problem**: This is a standard English-Ukrainian grammar contrast, not a decolonization topic. The `[!decolonization]` callout type is meant for Russification, language bans, resistance — not verb government differences from English.
- **Fix**: Change to `[!warning]` with title «Поширена помилка» (Common Mistake).

### Issue 10: Cloze Passage — Implausible Answers
- **Location**: Activities file lines 393-410
- **Original**: Blank 7 «Ми пропонуємо {{7}} чай і торт» → answer «людям»; Blank 10 «Брат показує свої подарунки {{10}}» → answer «колегам»
- **Problem**: The cloze describes a family birthday party. Offering tea to generic «людям» (people) rather than «гостям» (guests) is unnatural. A brother showing birthday presents to «колегам» (colleagues) at a home party is implausible.
- **Fix**: Blank 7 → «гостям»; Blank 10 → «друзям» or «родичам».

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 185 | «Якщо ви даруєте квіти **доньці**. Якщо ви адресуєте посилку **аптеці**.» | «Ви даруєте квіти **доньці**. Ви адресуєте посилку **аптеці**.» | Grammar (fragments) |
| 206 | «Палаталізацію задньоязикових» | «зміни звуків Г, К, Х перед закінченням -і» | Register (C1+ → A2) |
| 20 | «Хто є бенефіціаром вашої дії?» | «Хто отримує результат вашої дії?» | Register (C1+ → A2) |
| 343 | «це моветон і поганий знак» | «це погана ознака і грубість» | Register (C1+ → A2) |
| 212 | «Дочка → Дочці» | «Донька → Доньці» | Consistency |
| 100 | «Accusative/Genitive» | «Accusative» | Terminology (confusing for A2) |
| 343 | «дві квіти» | «дві квітки» | Grammar (numeral+noun agreement) |

## Beginner Safety Audit

"Would I Continue?" Test: 3.5/5

- Overwhelmed? **BORDERLINE FAIL** — Ukrainian prose contains 3 instances of C1+ vocabulary (бенефіціаром, палаталізація задньоязикових, моветон) without glossing or translation. A2 learner would hit a wall.
- Instructions clear? **PASS** — English explanations are clear throughout. Grammar tables are well-organized.
- Quick wins? **PASS** — Examples appear early and frequently. First callout box provides a quick win with pronoun review.
- Ukrainian scary? **BORDERLINE PASS** — Generally introduced gently with English support, but the 3 C1+ terms break the safety net.
- Come back tomorrow? **PASS** — Cultural content about flowers, taboo gifts, and Name Day is genuinely engaging and motivating.

## Strengths

- **Rich cultural content**: Section «Практика: Етикет подарунків» is genuinely engaging with flower etiquette, taboo gifts, and the coin workaround tradition. This is memorable, practical knowledge.
- **Dialogue quality**: Section «Діалоги: День Ангела» provides 4 distinct scenarios (greeting, shopping, party, hospitality) that naturally showcase Dative in social contexts.
- **Euphony teaching**: Section «Чоловічий та середній рід: -ові/-у» subsection "Милозвучність" clearly explains why -ові/-у alternation exists with concrete examples like «панові директору».
- **Error prevention**: The `[!warning]` box at line 97-102 and the "Help Trap" at line 279-287 proactively address high-frequency learner errors.
- **Activity variety**: 8 different activity types across 12 activities. Good progression from receptive (group-sort, mark-the-words) to productive (unjumble, cloze).

## Fix Plan to Reach 9.0/10 (REQUIRED — score is 7.7)

### Language: 7/10 → 9/10
**What to fix:**
1. Line 65: Remove factual claim «distinguishing it from neighboring Slavic languages» → Replace with «This gives speakers stylistic flexibility.»
2. Line 20: Change «бенефіціаром» → «отримувачем» (A2-accessible)
3. Line 206: Change «Палаталізацію задньоязикових» → «зміни звуків Г, К, Х перед -і»
4. Line 343: Change «моветон» → «погана ознака»
5. Line 281: Change `[!decolonization]` → `[!warning]`; retitle «Поширена помилка»

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 185: Fix sentence fragments — remove «Якщо» or add main clauses
2. Line 212: Change «Дочка → Дочці» → «Донька → Доньці»
3. Line 343: Change «дві квіти» → «дві квітки»
4. Line 100: Change «Accusative/Genitive» → «Accusative»

**Expected score after fix:** 9/10

### Factual Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 65: Remove or correct the uniqueness claim about -ові ending

**Expected score after fix:** 9/10

### Relevance: 7/10 → 8/10
**What to fix:**
1. Add subsection in Section «Ключові дієслова та керування» for verbs «личити», «заважати», «вистачати», «бракувати» with 2-3 examples each
2. Add «давати відповідь» collocation to the давати examples

**Expected score after fix:** 8/10 (still not 9 — would need structural reorganization)

### Educational: 7/10 → 8/10
**What to fix:**
1. Add «Дідусеві вісімдесят років» to age expression section (lines 55-59)
2. Add practice activities for личити, заважати

**Expected score after fix:** 8/10

### Pedagogy: 7/10 → 8/10
**What to fix:**
1. Ensure all vocab YAML items have at least one content appearance
2. Add mini-exercise for personal/personal verb grouping

**Expected score after fix:** 8/10

### Activities: 7/10 → 8/10
**What to fix:**
1. Replace «Ми йдемо назустріч (муха)» with a plausible sentence
2. Fix cloze blanks 7 (людям → гостям) and 10 (колегам → друзям)
3. Add 2-3 items for личити/заважати

**Expected score after fix:** 8/10

### Projected Overall After Fixes
```
(8×1.5 + 8×1.0 + 8×1.0 + 8×1.2 + 9×1.1 + 8×1.2 + 9×1.0 + 8×1.3 + 8×0.9 + 8×1.3 + 8×1.0 + 9×1.5 + 9×1.5) / 15.5
= (12.0 + 8.0 + 8.0 + 9.6 + 9.9 + 9.6 + 9.0 + 10.4 + 7.2 + 10.4 + 8.0 + 13.5 + 13.5) / 15.5
= 129.1 / 15.5
= 8.3/10
```

Note: Reaching 9.0 overall would require deeper structural changes (adding full personal/заважати/вистачати sections, restructuring the PPP flow to integrate missing verbs). The fixes above resolve auto-fail gates and bring the module to a solid 8.3.

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (A2 core grammar track — no research file with Key Facts Ledger)
- Key Facts Ledger present: NO
- Dates checked: 0 (no historical dates in content)
- Named figures verified: 0 (no historical figures)
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: 1 (line 65 uniqueness claim about -ові)
- Callout box claims verified: 8 boxes checked, 1 factual issue found (line 65)

## Verification Summary

- Content lines read: 437
- Activity items checked: 98 (across 12 activities)
- Ukrainian sentences verified: 34
- IPA transcriptions checked: 0 (none in content; IPA in vocab YAML appears correct)
- Factual claims verified: 4 (uniqueness claim, cultural rules, euphony rule, age construction)
- Issues found: 10

## Verdict

**FAIL**

Two auto-fail gates triggered: **Language** (7/10, threshold <8) due to factual inaccuracy on line 65 and three instances of C1+ vocabulary in A2 Ukrainian prose; **Linguistic Accuracy** (8/10, threshold <9) due to sentence fragments at line 185 and summary inconsistency at line 212. Additionally, five plan-required vocabulary items (личити, заважати, вистачати, бракувати, давати відповідь) are absent from content despite appearing in the vocabulary file. The cultural content and dialogue sections are strong, but the language-level and plan-alignment issues require targeted fixes before pass.

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
failing gates:
review: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-dative-ii-nouns-audit.log for details)
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/the-dative-ii-nouns.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/the-dative-ii-nouns.yaml
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

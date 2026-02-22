# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-cyrillic-code-ii.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-cyrillic-code-ii.yaml`

---

## Review (from Phase D.1)

# Рецензія: The Cyrillic Code II

**Reviewed-By:** claude-opus-4-6

**Level:** A1 | **Module:** 02
**Overall Score:** 8.2/10
**Status:** FAIL
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PASS (with minor discrepancies)
- Sections: All 5 H2 sections present and match plan (Вступ, Унікальні приголосні, Йотовані голосні та М'який знак, Голосні та напівголосні, Практика та вимова)
- Vocabulary: 8/8 required from plan (центр, чай, школа, гарний, жити, день, Європа, яблуко); recommended words also present (ще, ґанок, їжа, юнак, сіль, сім'я in vocab file). Note: сім'я appears in vocabulary YAML and activities but is NEVER introduced in the lesson content.
- Grammar scope: CLEAN — stays within alphabet/phonetics scope
- Objectives: All 4 objectives addressed (unique consonants, iotated vowels, soft sign, И/І distinction)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong lesson arc with welcome, preview, practice, celebration. "Would I Continue?" 5/5. Slightly flowery abstract language in intro reduces accessibility for nervous beginners. |
| 2 | Language | 8/10 | <8 | Two English grammar errors: sentence fragment at line 143, broken predicate at line 71. Ukrainian sentences embedded in text are all correct. No Russianisms or calques detected. |
| 3 | Pedagogy | 8/10 | <7 | Strong PPP structure. Two misplaced example words (хлопець in Ч section, читати in Й section) undermine the "one letter at a time" presentation. Word сім'я quizzed but never taught. |
| 4 | Activities | 8/10 | <7 | 8 activities with good variety (match-up, group-sort, quiz, fill-in, anagram, true-false). Г/Ґ and И/І fill-in drills are pedagogically excellent. сім'я tested in quiz but absent from lesson body. |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5 — strong English scaffolding, predictable structure, regular encouragement. One-letter-at-a-time pacing is ideal. Minor: some abstract language in section «Вступ» could be simplified. |
| 6 | LLM Fingerprint | 7/10 | <7 | 3+ instances of abstract noun stacking across sections (lines 12, 18, 139). "In this lesson, we will" pattern at line 18. Content is substantive and pedagogically sound underneath — the fingerprint is rhetorical, not structural. |
| 7 | Linguistic Accuracy | 8/10 | <9 | є́нот (line 149) has wrong stress — standard is єно́т. я́сь glossed as "clear - root word" (line 277) but is a proper name, not "clear." хлопець placed in Ч section despite containing no Ч. читати placed in Й section despite containing no Й. |

**Weighted Overall:** (9×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 9×1.3 + 7×1.0 + 8×1.5) / 8.9
= (13.5 + 8.8 + 9.6 + 10.4 + 11.7 + 7.0 + 12.0) / 8.9
= 73.0 / 8.9 = **8.2/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN] — stays within alphabet/phonetics
- Activity errors: [1 found — сім'я quizzed but never taught in lesson]
- Beginner safety: 5/5
- Factual accuracy: [2 discrepancies — letter count 14 vs 15, є́нот stress]
- Colonial framing: [CLEAN] — no "Unlike Russian" patterns; Ї identity claim at line 158 is factual, not comparative
- LLM Fingerprint: [BORDERLINE] — abstract noun stacking triggers ≤7

## Critical Issues Found

### Issue 1: Misplaced Example — хлопець in Ч Section
- **Location**: Line 120 / Section «Унікальні приголосні» (subsection Ч)
- **Original**: «**хло́пець** (boy/guy)»
- **Problem**: The word хлопець (х-л-о-п-е-ц-ь) does NOT contain the letter Ч. It contains Ц and Х but not Ч. Placing it in the Ч section implicitly teaches a false phonological claim.
- **Fix**: Replace with a word that actually contains Ч, e.g., **чо́рний** (black), **чоловік** (man), or **чотири** (four).

### Issue 2: Misplaced Example — читати in Й Section
- **Location**: Line 248 / Section «Голосні та напівголосні» (subsection Й)
- **Original**: «**чита́ти** (to read)»
- **Problem**: The word читати (ч-и-т-а-т-и) does NOT contain the letter Й. It only contains И, which is a different letter. This directly undermines the lesson's core objective of distinguishing letters.
- **Fix**: Replace with a word containing Й, e.g., **гайда** (let's go), **дайте** (give), or **край** (land/edge).

### Issue 3: Incorrect Stress on єнот
- **Location**: Line 149 / Section «Йотовані голосні та М'який знак» (subsection Є)
- **Original**: «**є́нот** (raccoon)»
- **Problem**: Standard Ukrainian stress is єно́т (second syllable), not є́нот (first syllable). This teaches incorrect pronunciation.
- **Fix**: Change to «**єно́т** (raccoon)» or replace with a more common A1-appropriate word like **єдність** (unity).

### Issue 4: Incorrect Gloss for ясь
- **Location**: Line 277 / Section «Практика та вимова»
- **Original**: «**я́сь** (clear - root word)»
- **Problem**: "Ясь" is a proper name (traditional diminutive of Ярослав), not a standalone word meaning "clear." The adjective root is "ясний." Using a fabricated meaning in a pronunciation drill teaches false vocabulary.
- **Fix**: Replace with a real soft-С word: «**о́сінь** (autumn)» or «**гу́сь** (goose)» — both clearly demonstrate the palatalized С.

### Issue 5: English Sentence Fragment
- **Location**: Line 143 / Section «Йотовані голосні та М'який знак» (subsection Є)
- **Original**: «As an "iotated" vowel, meaning it starts with a "y" sound.»
- **Problem**: This is a sentence fragment — no main clause. The subject ("it") is missing and "as" creates a dangling modifier.
- **Fix**: «It is an "iotated" vowel, meaning it starts with a "y" sound.»

### Issue 6: Broken English Predicate
- **Location**: Line 71 / Section «Унікальні приголосні» (subsection Ж)
- **Original**: «The resulting sound is rich and warm that appears in some of the most fundamental Ukrainian words.»
- **Problem**: "is rich and warm that appears" is grammatically broken — "that appears" has no valid antecedent in this construction.
- **Fix**: «The resulting sound is rich and warm, appearing in some of the most fundamental Ukrainian words.»

### Issue 7: Letter Count Discrepancy (14 vs 15)
- **Location**: Lines 8, 12, 18 / Section «Вступ» and H1 title
- **Original**: «The Final 14 Letters» / «final fourteen letters»
- **Problem**: The lesson actually covers 15 letters: Г, Ґ, Ж, Ш, Щ, Ч, Ц (7) + Є, Ї, Ю, Я, Ь (5) + И, І, Й (3) = 15. The "14" count is incorrect.
- **Fix**: Change to "The Final 15 Letters" throughout, or verify with Module 1 scope whether one letter was already covered.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 149 | «є́нот» | «єно́т» | Stress error |
| 277 | «я́сь (clear - root word)» | «о́сінь (autumn)» or «гу́сь (goose)» | Fabricated gloss |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — one letter at a time, clear pacing, English scaffolding throughout
- Instructions clear? **Pass** — each section explains what to do, physical pronunciation mechanics are precise
- Quick wins? **Pass** — opening diagnostic with familiar words (мама, тато, брат, кіт) provides immediate confidence; each letter section is a small win
- Ukrainian scary? **Pass** — Ukrainian introduced gently within English explanations; «Зверніть увагу:» and «Давайте практикувати!» are scaffolded with translations
- Come back tomorrow? **Pass** — encouraging tone throughout, «Чудова робота!» at line 279, celebratory ending with «Сла́ва Украї́ні!»

## Strengths

- **Excellent Г/Ґ treatment**: The cultural hook about the repressed letter Ґ (section «Унікальні приголосні», lines 64-65) is historically accurate, emotionally resonant, and pedagogically sound — it gives learners a memorable reason to distinguish the two sounds.
- **"Smile vs Grin" technique** (section «Голосні та напівголосні»): Naming the И/І distinction with body-based mnemonics is genuinely clever pedagogy that learners will remember. The minimal pair кіт/кит reinforces it perfectly.
- **Contrast drills** (section «Практика та вимова»): The И/І, Г/Ґ, and С/СЬ contrast drills at lines 264-278 directly address documented learner errors from the research notes. This is evidence-based curriculum design.
- **Activity variety and quality**: The Г/Ґ fill-in activity is particularly well-designed — 8 items with a 6:2 Г:Ґ ratio reflecting real frequency, natural sentence frames, and clear explanations. The И/І fill-in is equally strong.
- **Cultural hooks are authentic**: The Ї/Mariupol resistance story (line 165-166) and Ґ restoration (line 64-65) both come from documented sources in the research notes.

## Fix Plan to Reach 9.0/10 (REQUIRED — score 8.2)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 120: Replace «**хло́пець** (boy/guy)» with a Ч-containing word like «**чо́рний** (black)» — fixes misplaced example
2. Line 248: Replace «**чита́ти** (to read)» with a Й-containing word like «**край** (land/edge)» — fixes misplaced example
3. Line 149: Change «**є́нот**» to «**єно́т**» — fixes stress error
4. Line 277: Replace «**я́сь** (clear - root word)» with «**о́сінь** (autumn)» — fixes fabricated gloss

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 143: Change «As an "iotated" vowel, meaning it starts with a "y" sound.» to «It is an "iotated" vowel, meaning it starts with a "y" sound.»
2. Line 71: Change «The resulting sound is rich and warm that appears» to «The resulting sound is rich and warm, appearing in some of the most fundamental Ukrainian words.»

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Line 12: Simplify «your key to unlocking the true sound and soul of the language» — reduce abstract noun stacking. E.g., «your key to reading and speaking Ukrainian naturally»
2. Line 18: Simplify «They are the phonetic fingerprint of the culture» and «the unique acoustic heritage of Ukraine» — e.g., «These letters give Ukrainian its distinctive sound» and «the way Ukrainian really sounds»
3. Line 139: Simplify «the secret to Ukrainian euphony—the natural musicality and smoothness of the language» — e.g., «what makes Ukrainian sound so smooth and musical»

**Expected score after fix:** 8/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add сім'я to the lesson content (section «Йотовані голосні та М'який знак», subsection Я) — the word is quizzed in activities but never taught
2. Fix or verify the "14 vs 15 letters" count — either correct the title or confirm one letter belongs in Module 1

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
Experience: 9 × 1.5 = 13.5
Language: 9 × 1.1 = 9.9
Pedagogy: 9 × 1.2 = 10.8
Activities: 9 × 1.3 = 11.7  (fixes сім'я gap)
Beginner Safety: 9 × 1.3 = 11.7
LLM Fingerprint: 8 × 1.0 = 8.0
Linguistic Accuracy: 9 × 1.5 = 13.5
Total: 79.1 / 8.9 = 8.9/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not applicable — A1 core)
- Dates checked: 2 (Ґ banned 1933, restored 1990 — matches research notes)
- Named figures verified: 0 (no named historical figures in content)
- Primary quotes cross-referenced: NOT_APPLICABLE
- Chronological sequence: CONSISTENT
- Claims without research grounding: 1 (Mariupol 2022 Ї graffiti — confirmed in research notes)
- Stress/pronunciation claims verified: 1 error found (є́нот should be єно́т)
- Letter count claim: DISCREPANCY (title says 14, content covers 15)

## Verification Summary

- Content lines read: 322
- Activity items checked: 76 (across 8 activities)
- Ukrainian sentences verified: 12 embedded Ukrainian phrases
- IPA transcriptions checked: 20 (vocabulary file)
- Factual claims verified: 5 (Ґ history, Ї Mariupol, letter count, єнот stress, ясь gloss)
- Issues found: 7

## Verdict

**FAIL**

Linguistic Accuracy scores 8/10, below the <9 auto-fail threshold. Four errors drive this: хлопець placed as a Ч example despite containing no Ч (line 120), читати placed as a Й example despite containing no Й (line 248), incorrect stress on є́нот (line 149), and fabricated gloss for я́сь (line 277). All four are straightforward fixes requiring word replacements. After repair, the module should comfortably pass — the pedagogical design, activity quality, and cultural content are genuinely strong.

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
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-ii-audit.log for details)
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-cyrillic-code-ii.yaml
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

# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/questions-and-negation.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/questions-and-negation.yaml`

---

## Review (from Phase D.1)

# Рецензія: Questions & Negation

**Reviewed-By:** claude-opus-4-6

**Level:** A1 | **Module:** 7
**Overall Score:** 8.2/10
**Status:** FAIL
**Reviewed:** 2026-02-21

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: 5/5 H2 sections from meta content_outline present (names match meta, not plan — acceptable)
- Vocabulary: 8/8 required from plan, 7/7 recommended, 9 extra (total 24)
- Grammar scope: CLEAN — yes/no with чи, question words, negation with не, frequency adverbs
- Objectives: 4/4 addressed (чи questions, question words, negation, frequency adverbs)
```

**Note:** The plan defines a "Investigative Journalist" persona for roleplay, but the content only implicitly uses it in the "Social Curiosity" scenario (line 288). No explicit roleplay activity named as such. Minor gap.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm tone with creative ALF hook, but summary (lines 367-381) is entirely Ukrainian — could overwhelm at end of long lesson |
| 2 | Coherence | 9/10 | <7 | Logical flow: intro → grammar → practice → application → culture. "Що vs Шо" and "Frequency words" subsections slightly tangential but justified |
| 3 | Relevance | 9/10 | <7 | All content directly serves stated objectives; cultural hook is relevant |
| 4 | Educational | 8/10 | <7 | "Do Trap" is excellent pedagogy; but activities undercut learning (see Activities dimension) |
| 5 | Language | 8/10 | <8 | «освіжаюче проста» calque (line 369); "Шо = Surzhyk / lazy pronunciation" is linguistically inaccurate (line 160); «Це швидше і більш розмовно» slightly awkward (line 98) |
| 6 | Pedagogy | 8/10 | <7 | Solid PPP structure; well-scaffolded English→Ukrainian; but activities don't challenge enough (repetitive fill-ins) |
| 7 | Immersion | 9/10 | <6 | 31.5% Ukrainian; A1.1 target is 20-40% — squarely in range |
| 8 | Activities | 7/10 | <7 | Anagram items not actually scrambled; 2 fill-in activities have zero discrimination (same answer for all items); see Critical Issues |
| 9 | Richness | 8/10 | <6 | ALF cultural hook, Lviv café scenario, intonation visualization with arrows, animacy distinction with pets |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5; warm scaffolding throughout; minor concern with all-Ukrainian summary |
| 11 | LLM Fingerprint | 7/10 | <7 | "Важливо знати:" used 7 times (lines 77,97,124,153,166,182,238); 6+ distinct metaphors; 3× "not just" pattern (lines 13,18,249) |
| 12 | Linguistic Accuracy | 9/10 | <9 | IPA correct throughout; grammar correct; one calque «освіжаюче» |
| 13 | Factual Accuracy | 8/10 | <8 | «Він сформував почуття гумору цілого покоління» (line 345) is unverifiable superlative; «Шо» mischaracterized as Surzhyk (line 160) |

**Weighted Overall:**
```
(8×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 9×1.0 + 7×1.3 + 8×0.9 + 9×1.3 + 7×1.0 + 9×1.5 + 8×1.5) / 15.5
= (12 + 9 + 9 + 9.6 + 8.8 + 9.6 + 9 + 9.1 + 7.2 + 11.7 + 7 + 13.5 + 12) / 15.5
= 127.5 / 15.5
= 8.2/10
```

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: «освіжаюче проста» (line 369) — English calque "refreshingly simple"
- Colonial framing: CLEAN — no Russian-as-baseline comparisons
- Grammar scope: CLEAN — no grammar from later modules
- Activity errors: Anagram items not scrambled (lines 219-238); repetitive fill-ins (lines 161-196, 240-275)
- Beginner safety: 5/5
- Factual accuracy: 2 issues — ALF superlative claim (line 345), "Шо = Surzhyk" mischaracterization (line 160)

## Critical Issues Found

### Issue 1: Anagram Activity Items Not Scrambled (ACTIVITIES — CRITICAL)
- **Location**: Lines 219-238 / Activity "Розшифруйте слова"
- **Original**: `scrambled: "т а м"` → `answer: "там"`, `scrambled: "х т о"` → `answer: "хто"`, etc. (all 8 items)
- **Problem**: Every "scrambled" word has letters in the correct order with spaces between them. "т а м" is not an anagram of "там" — it IS "там" with spaces. There is zero scrambling, making the activity educationally worthless.
- **Fix**: Actually scramble the letters, e.g., `scrambled: "м а т"` → `answer: "там"`, `scrambled: "о т х"` → `answer: "хто"`.

### Issue 2: "Шо" Mischaracterized as Surzhyk (LANGUAGE + FACTUAL)
- **Location**: Line 160
- **Original**: «**Шо** = Very casual, spoken, sometimes considered "Surzhyk" (mixed language) or just lazy pronunciation.»
- **Problem**: "Шо" is a dialectal/colloquial variant with deep roots in Ukrainian dialects, predating Russian contact. It is NOT Surzhyk. Labeling it "lazy pronunciation" is a value judgment and factually incorrect. This perpetuates a harmful misconception.
- **Fix**: Replace with: «**Шо** = Very casual, spoken variant found across many Ukrainian dialects. Completely natural in informal conversation, but not standard written Ukrainian.»

### Issue 3: "Освіжаюче проста" — English Calque (LANGUAGE)
- **Location**: Line 369
- **Original**: «Ви дізналися: українська мова освіжаюче проста.»
- **Problem**: «Освіжаюче» as an adverb modifying an adjective is a calque from English "refreshingly". This construction is not standard Ukrainian.
- **Fix**: «Ви дізналися: українська мова приємно проста.» or «...вражаюче проста.»

### Issue 4: "Важливо знати:" Repeated 7 Times (LLM FINGERPRINT)
- **Location**: Lines 77, 97, 124, 153, 166, 182, 238
- **Problem**: The same heading «Важливо знати:» is used identically 7 times across 7 subsections. This is a clear LLM generation pattern — no real textbook repeats the same callout heading this many times.
- **Fix**: Vary the headings: «Зверніть увагу:», «Порада:», «Пам'ятайте:», «Корисно знати:», «На замітку:», etc.

### Issue 5: Repetitive Fill-In Activities (ACTIVITIES)
- **Location**: Lines 161-196 ("Скажіть «ні»") and Lines 240-275 ("Ввічливі запитання")
- **Problem**: In "Скажіть «ні»", all 8 items have the same answer ("не") with identical explanations copy-pasted. In "Ввічливі запитання", all 8 items have the same answer ("Чи") with identical explanations. Zero discrimination is required from the learner.
- **Fix**: For "Скажіть «ні»": reduce to 4 items with "не" and add 4 items where "ні" is the correct answer (testing the не/ні distinction). For "Ввічливі запитання": mix in items where the correct start is a question word (Хто, Де, etc.) rather than always "Чи".

### Issue 6: ALF Superlative Claim (FACTUAL)
- **Location**: Line 345
- **Original**: «Він сформував почуття гумору цілого покоління.»
- **Problem**: While the ALF Ukrainian dub is culturally significant, claiming it "shaped the sense of humor of an entire generation" is an unverifiable superlative. Multiple media influenced 90s Ukrainian culture.
- **Fix**: «Він залишив яскравий слід у поп-культурі 90-х.» (It left a vivid mark on 90s pop culture.)

### Issue 7: Excessive Metaphor Density (LLM FINGERPRINT)
- **Location**: Throughout the module
- **Problem**: 6+ distinct metaphors: "flag" for чи (line 63), "guard" for не (line 40), "wall" for ні (line 58), "shield" for не (line 58), "tossing a ball" for intonation (line 254), "ping-pong" for conversation (line 301), "politeness dial" (line 328), "slamming a door" for ні (line 338). This exceeds the 4-metaphor threshold.
- **Fix**: Remove or merge at least 3 metaphors. The wall/shield pair at line 58 and the guard at line 40 all describe the same concept — pick one. The door metaphor at line 338 is redundant with the wall metaphor.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 369 | «освіжаюче проста» | «приємно проста» | Calque |
| 98 | «Це швидше і більш розмовно» | «Це швидший і більш розмовний варіант» or «Так швидше й розмовніше» | Awkward phrasing |
| 160 | «sometimes considered "Surzhyk" (mixed language) or just lazy pronunciation» | «a widespread colloquial variant found across Ukrainian dialects» | Factual inaccuracy |
| 367 | «Ви робили заяви» | «Ви лише стверджували» | Stilted word choice — «заяви» implies official declarations |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — Concepts introduced one at a time, English scaffolding consistent
- Instructions clear? **Pass** — Always knew what was being taught; "Do Trap" addressed immediately
- Quick wins? **Pass** — The revelation "you don't need 'do'" is an early win at line 23
- Ukrainian scary? **Pass** — Gentle introduction with translations throughout
- Come back tomorrow? **Pass** — ALF hook is memorable; conversational scenarios feel useful

**Note:** The summary section (lines 367-381) is entirely in Ukrainian with 7 self-check questions in Ukrainian. For an A1.1 module, this could feel overwhelming as a final impression. Consider adding English translations for the self-check questions.

## Strengths

- **"Do Trap" pedagogy** (lines 22-35): Excellent proactive error prevention. The warning box with the ridiculous "Робиш ти знати?" example is memorable and effective.
- **Ні/Не distinction** (lines 49-58): The wall/shield metaphor, while contributing to metaphor density, is genuinely helpful for beginners who confuse these two words.
- **ALF cultural hook** (lines 344-361): Creative and authentic Ukrainian cultural reference that doubles as grammar reinforcement. The breakdown at lines 357-359 is excellent applied analysis.
- **Intonation visualization** (lines 248-265): The arrow notation (↘/↗) and the physical analogy of drawing lines with fingers is practical and kinesthetic.
- **Register awareness** (lines 327-333): The "politeness dial" concept is age-appropriate and immediately actionable.

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Activities: 7/10 → 9/10
**What to fix:**
1. Lines 219-238: Actually scramble the anagram letters (e.g., "м а т" → "там", "т о х" → "хто")
2. Lines 161-196: Replace 4 of 8 "не" items with items where "ні" is the correct answer, testing the не/ні distinction
3. Lines 240-275: Replace 4 of 8 "Чи" items with items where question words (Хто, Де, Коли) are the correct answer
4. Diversify explanations — don't copy-paste identical text for all items

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 9/10
**What to fix:**
1. Lines 77,97,124,153,166,182,238: Replace 5 of 7 «Важливо знати:» with varied headings (Зверніть увагу, Порада, Пам'ятайте, Корисно знати, На замітку)
2. Remove at least 3 metaphors: consolidate wall/shield/guard into one at lines 40,58; remove door metaphor at 338 (redundant with wall)
3. Line 249: Rephrase "Intonation is not just decoration" — the "not just X; it is Y" pattern appears 3 times

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 369: Change «освіжаюче проста» → «приємно проста»
2. Line 160: Remove "Surzhyk" and "lazy pronunciation" characterization; replace with accurate dialectal description
3. Line 98: Rephrase «Це швидше і більш розмовно» → «Так швидше й розмовніше»

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Lines 373-381: Add English translations for the 7 self-check questions (currently all Ukrainian for A1.1 learners)
2. Add a brief English encouragement before the summary to frame it as a celebration

**Expected score after fix:** 9/10

### Factual Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 345: Replace «Він сформував почуття гумору цілого покоління» with «Він залишив яскравий слід у поп-культурі 90-х»
2. Line 160: Fix "Шо = Surzhyk" mischaracterization (same as Language fix)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 9×1.1 + 8×1.2 + 9×1.0 + 9×1.3 + 8×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9 + 9 + 9.6 + 9.9 + 9.6 + 9 + 11.7 + 7.2 + 11.7 + 9 + 13.5 + 13.5) / 15.5
= 136.2 / 15.5
= 8.8/10
```

To reach 9.0+, Educational (8→9) and Pedagogy (8→9) would also need improvement — likely through the activity fixes propagating quality improvements and adding the explicit "Investigative Journalist" roleplay activity from the plan.

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (A1 core track — no research file exists)
- Key Facts Ledger present: NO
- Dates checked: 1 ("1990-х" for ALF dub — plausible)
- Named figures verified: 1 (ALF/Oksana in scenarios — fictional/illustrative, acceptable)
- Primary quotes cross-referenced: 1 («Ти не любиш котів? Ти просто не вмієш їх готувати!» — recognized cultural reference)
- Chronological sequence: N/A
- Claims without research grounding: 2 — ALF superlative (line 345), "Шо = Surzhyk" (line 160)

## Verification Summary

- Content lines read: 381
- Activity items checked: 68 (8+8+12+8+8+8+8+8)
- Ukrainian sentences verified: 34
- IPA transcriptions checked: 27 (3 inline + 24 vocabulary)
- Factual claims verified: 4
- Issues found: 7

## Verdict

**FAIL**

Three blocking issues: (1) Anagram activity items are not scrambled — letters appear in correct order, rendering the activity educationally worthless. (2) "Шо" mischaracterized as "Surzhyk" and "lazy pronunciation" — factually inaccurate and potentially harmful framing of a legitimate dialectal form. (3) LLM fingerprint: "Важливо знати:" repeated 7 times identically plus excessive metaphor density exceeding the 4-metaphor threshold. All three require fixes before the module can pass.

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
failing gates:
→ 1 violations (minor)
❌ [REVIEW_LOW_SECTION_COVERAGE] Review only covers 0/5 (0%) content sections. Missed: Вступ: Мистецтво ставити питання, Граматика: Як будувати питання, Практика: Інтонація та конструктор, Застосування: Розмова в реальному житті, Культурний контекст: Ввічливість і гумор. A thorough review must address each major section of the content.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/questions-and-negation-audit.log for details)
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/questions-and-negation.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/questions-and-negation.yaml
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

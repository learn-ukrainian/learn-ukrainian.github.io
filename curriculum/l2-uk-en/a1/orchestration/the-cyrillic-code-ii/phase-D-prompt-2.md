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
**Overall Score:** 7.3/10
**Status:** FAIL
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PASS (with notes)
- Sections: PASS — all 5 planned H2 sections present (Вступ, Унікальні приголосні, Йотовані голосні та М'який знак, Голосні та напівголосні, Практика та вимова)
- Vocabulary: 8/8 required present, 5/6 recommended present (ніч missing from vocab YAML despite plan recommendation and content usage)
- Grammar scope: CLEAN — no scope creep detected
- Objectives: PASS — all 4 objectives addressed
- Word count: 4562 / 2000 target (228%) — extreme overshoot; content is substantive but padded
- Activities: Plan specified 4 activities (75 items); actual is 8 activities (68+ items) — different structure but comparable coverage
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | 228% word overshoot creates wall-of-text; 8+ stacked metaphors overwhelm rather than guide; first practice sentences appear only after ~600 words of English prose |
| 2 | Language | 8/10 | <8 | Russicism «красивий» (line 88) directly contradicts module's own гарний vocabulary; inverted word order «Швидко йде час» (line 64) unnatural for A1 |
| 3 | Pedagogy | 7/10 | <7 | Misleading ніч placement in Soft Sign section (line 145) — ніч has no Ь; cognitive overload from 4500+ words violates "≤2 concepts before practice" pacing standard |
| 4 | Activities | 8/10 | <7 | 8 activities with good type variety (match-up, group-sort, fill-in, quiz, anagram, true-false); Г/Ґ and И/І get dedicated drills; some items per activity below plan targets |
| 5 | Beginner Safety | 7/10 | <7 | "Would I Continue?" 3/5 — overwhelming length and verbose prose will discourage nervous beginners |
| 6 | LLM Fingerprint | 6/10 | <7 | 8+ metaphors (4 threshold); 7 sections with identical 8-10 bullet example batching; "much more than just" + "far, far beyond" rhetoric; 4+ purple prose sentences with stacked abstractions |
| 7 | Linguistic Accuracy | 8/10 | <9 | «красивий» Russicism on line 88; «прекрасне» contested form on line 59; IPA fully correct across 20 vocab items |

**Weighted Overall:**
```
(7 × 1.5) + (8 × 1.1) + (7 × 1.2) + (8 × 1.3) + (7 × 1.3) + (6 × 1.0) + (8 × 1.5)
= 10.5 + 8.8 + 8.4 + 10.4 + 9.1 + 6.0 + 12.0 = 65.2
65.2 / 8.9 = 7.3/10
```

## Auto-Fail Checklist Results

- Russianisms: **FLAG** — «красивий» (line 88), «прекрасне» (line 59, contested)
- Calques: CLEAN
- Colonial framing: CLEAN — Russian references appear only in legitimate [!history-bite] and [!decolonization] blocks
- Grammar scope: CLEAN
- Activity errors: CLEAN — all items verified correct
- Beginner safety: 3/5
- Factual accuracy: CLEAN — Ґ ban dates (1933-1990) match research, Mariupol 2022 reference appropriate

## Critical Issues Found

### Issue 1: Russicism «красивий» Contradicting Module Vocabulary
- **Location**: Line 88 / Section «Унікальні приголосні»
- **Original**: «Центр міста красивий.»
- **Problem**: The word красивий is a contested lexical Russicism. More critically, this module explicitly teaches **гарний** as "beautiful/good" — using a different, Russian-influenced word for the same concept two sections earlier creates direct learner confusion at A1.
- **Fix**: Replace with «Центр міста гарний.» — reinforces the module's own vocabulary.

### Issue 2: Severe LLM Fingerprint — Metaphor Overdose & Example Batching
- **Location**: Throughout all sections
- **Problem**: 8+ distinct metaphors in a single A1 module: "heart and soul" (line 12), "soul, history, and heartbeat" (line 24), "snowflake or a spider" (line 54), "pitchfork" (line 56), "bumblebee" (line 71), "wind rustling through leaves" (line 71), "balloon on a string" (line 100), "master keys" (line 201). The threshold is 4. Additionally, 7 subsections each have exactly 8-10 consecutive bullet-point example sentences in identical «**Ukrainian.** (English.)» format — this is unmistakable LLM batching.
- **Fix**: Reduce metaphors to ≤3 most effective ones (Smile/Grin, snowflake/pitchfork are the best — drop the rest). Vary example presentation: inline some, table some, interleave with explanatory text. Break the uniform 10-sentence blocks.

### Issue 3: Misleading ніч Placement in Soft Sign Section
- **Location**: Line 145 / Section «Йотовані голосні та М'який знак»
- **Original**: «Another excellent example is the word **ні́ч** (night), which contrasts nicely with hard consonant endings you will learn later.»
- **Problem**: The word ніч appears in the Soft Sign (Ь) subsection introduced by "Another excellent example" — implying it exemplifies the soft sign's effect. But ніч contains NO soft sign. The phrasing is ambiguous about whether ніч is presented as a soft-sign example or a contrast to it. This will confuse A1 learners about when Ь is needed.
- **Fix**: Move ніч to a separate, clearly labeled contrast paragraph: "Compare this to words WITHOUT the soft sign, like **ніч** (night), where the final consonant stays hard." Or remove entirely and add a dedicated soft/hard contrast exercise.

### Issue 4: Excessive Verbosity — 228% of Word Target
- **Location**: All sections, especially section «Вступ» (lines 14-24)
- **Problem**: 4562 words vs 2000 target. The section «Вступ» alone is approximately 500 words of motivational prose before any teaching begins. Lines 16-20 spend 250 words on "welcome back" and "trust the process" encouragement. While warm, this volume is cognitively exhausting for A1 beginners — the module reads more like an essay than a lesson. Plan allocates 300 words for «Вступ»; actual is ~500.
- **Fix**: Cut «Вступ» to 200-250 words. For each subsequent section, reduce English explanation by ~40%, retaining the best pedagogical explanations (Smile/Grin technique, tongue-position instructions) while removing motivational filler. Target: 2200-2500 total words.

### Issue 5: Contested Russicism «прекрасне»
- **Location**: Line 59 / Section «Унікальні приголосні»
- **Original**: «Життя прекрасне.»
- **Problem**: While «прекрасне» appears in SUM, it is frequently flagged as Russian-influenced. In a decolonization-focused curriculum, prefer unambiguously Ukrainian alternatives.
- **Fix**: Replace with «Життя чудове.»

### Issue 6: Purple Prose / Stacked Abstract Nouns
- **Location**: Lines 12, 22, 24, 121
- **Original** (line 24): "you are connecting directly with the soul, history, and heartbeat of Ukraine"
- **Original** (line 121): "a profound, recognizable symbol of national identity, resilience, and strength"
- **Problem**: Multiple sentences stack 3+ abstract nouns, which is a strong LLM fingerprint marker and inappropriate register for A1 beginner tutoring. A patient tutor speaks simply.
- **Fix**: Replace with concrete, actionable language. E.g., line 24 → "you're building real reading skills that will work on Ukrainian streets, menus, and signs."

### Issue 7: Unnatural Sentence Word Order
- **Location**: Line 64 / Section «Унікальні приголосні»
- **Original**: «Швидко йде час.»
- **Problem**: Inverted word order (adverb-verb-subject) is literary/poetic, not natural conversational Ukrainian. For A1, standard SVO order is expected.
- **Fix**: Replace with «Час йде швидко.» or simply «Час минає швидко.»

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 88 | «Центр міста красивий.» | «Центр міста гарний.» | Russicism |
| 59 | «Життя прекрасне.» | «Життя чудове.» | Contested Russicism |
| 64 | «Швидко йде час.» | «Час йде швидко.» | Unnatural word order |
| 84 | «Щире слово допомагає.» | Consider replacing — abstract for A1 | Register too high |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? **FAIL** — 4562 words is double the target. Sections of dense English prose (lines 16-24, ~500 words) before any Ukrainian practice. Seven blocks of 8-10 example sentences each add visual weight.
- Instructions clear? **PASS** — The lesson structure is logical: present letter → explain sound → give examples. The Smile/Grin technique for И/І is particularly clear.
- Quick wins? **MARGINAL PASS** — Example sentences start at line 37, but these are passive reading rather than interactive practice. The first activity is external to the prose. No inline mini-exercises.
- Ukrainian scary? **PASS** — Ukrainian is introduced gently with full English explanations and translations for every sentence.
- Come back tomorrow? **FAIL** — The essay-length prose would discourage a nervous beginner. The repetitive example blocks (10 sentences × 7 sections = 70+ sentences to read) feel like homework, not a guided lesson.

## Strengths

- **Г/Ґ distinction is excellently taught** — the "breath vs block" framing (lines 30-34) is physiologically precise and memorable. The [!history-bite] about the 1933 ban (line 49-50) is factually grounded and emotionally resonant.
- **Smile vs Grin technique for И/І** (lines 167-171) is a genuinely creative, body-based mnemonic that A1 learners can physically execute. This is the module's best pedagogical innovation.
- **Decolonization framing is handled correctly** — the [!decolonization] block about Ї in Mariupol (line 123-124) and the Kyiv spelling section (lines 211-216) use legitimate decolonization framing without colonial comparison patterns.
- **Activity variety is strong** — 8 activities spanning 6 different types (match-up, group-sort, quiz, fill-in, anagram, true-false) with dedicated drills for the two hardest distinctions (Г/Ґ and И/І).
- **IPA is fully correct** across all 20 vocabulary items. Stress placement verified accurate.

## Fix Plan to Reach 9/10 (REQUIRED)

### LLM Fingerprint: 6/10 → 9/10
**What to fix:**
1. Reduce metaphors from 8+ to ≤3. Keep: Smile/Grin (И/І), snowflake/pitchfork (Ж/Ш). Remove: "heart and soul," "soul, history, and heartbeat," "bumblebee," "balloon on a string," "master keys to the Cyrillic code," "wind rustling through leaves."
2. Break the uniform 10-sentence example blocks. Vary formats: inline 2-3 sentences within explanatory paragraphs, use a comparison table for minimal pairs, group 3-4 short sentences in a callout box, and save longer practice sets for the final section «Практика та вимова».
3. Rewrite lines 12, 22, 24, 121 to remove stacked abstractions. Replace with concrete, specific language appropriate for A1 tutor voice.
4. Eliminate "much more than just" (line 24) and "far, far beyond" (line 121) rhetoric patterns.

**Expected score after fix:** 9/10

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Cut total word count from 4562 to ~2200-2500. Section «Вступ»: 500→250 words. Each subsequent section: reduce English prose by ~40%.
2. Section «Вступ» (lines 16-24): condense the three-paragraph warmup into one short paragraph. Remove the "mental diagnostic check" concept (line 20) — it's padding.
3. Add inline mini-exercises after each letter group (e.g., "Try reading this word: **чай**. Did you hear the 'ch'?") before the full example blocks.

**Expected score after fix:** 9/10

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Line 145: Either remove ніч from the Soft Sign section or restructure as an explicit contrast: "Notice: **день** ends with a soft sign, but **ніч** does not need one — can you hear the difference?"
2. Add ніч to the vocabulary YAML file (plan recommends it, content uses it).
3. Reduce cognitive load by cutting prose between concepts. Currently, sections «Унікальні приголосні» and «Йотовані голосні та М'який знак» each have 700+ words before the next section — split the practice more evenly.

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 88: «Центр міста красивий.» → «Центр міста гарний.»
2. Line 59: «Життя прекрасне.» → «Життя чудове.»
3. Line 64: «Швидко йде час.» → «Час йде швидко.»

**Expected score after fix:** 9/10

### Beginner Safety: 7/10 → 9/10
**What to fix:**
1. Achieving the word count reduction (above) is the primary fix — 2200 words instead of 4562 dramatically improves approachability.
2. Add 2-3 inline "Try it!" moments before the full example blocks so learners get quick wins earlier.
3. Add a celebration moment at the midpoint (after consonants, before vowels): "You've already learned 7 new letters — that's half of today's lesson!"

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Fix the three Ukrainian issues listed above (красивий, прекрасне, Швидко йде час).
2. Review remaining example sentences for A1 appropriateness — «Щире слово допомагає» (line 84) uses abstract vocabulary ("sincere word helps") that may be above A1 register.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
Experience:  9 × 1.5 = 13.5
Language:    9 × 1.1 = 9.9
Pedagogy:    9 × 1.2 = 10.8
Activities:  8 × 1.3 = 10.4
Beginner:    9 × 1.3 = 11.7
LLM:         9 × 1.0 = 9.0
Linguistic:  9 × 1.5 = 13.5
Total = 78.8 / 8.9 = 8.9/10
```

## Verification Summary

- Content lines read: 235
- Activity items checked: 74 (12 match-up pairs + 14 group-sort items + 8 quiz + 8+8 fill-in + 8 anagram + 8 true-false + 8 quiz)
- Ukrainian sentences verified: 71 (content example sentences) + 16 (activity sentences)
- IPA transcriptions checked: 20/20 (all correct)
- Factual claims verified: 3 (Ґ ban 1933-1990 ✓, Mariupol 2022 ✓, Kyiv transliteration ✓)
- Issues found: 7

## Verdict

**FAIL**

Blocking issues: (1) LLM Fingerprint 6/10 < 7 auto-fail — 8+ metaphors, uniform example batching across 7 sections, and purple prose with stacked abstractions produce unmistakable AI-generated texture. (2) Linguistic Accuracy 8/10 < 9 auto-fail — Russicism «красивий» on line 88 directly contradicts the module's own vocabulary. The module's pedagogical core (Г/Ґ distinction, Smile/Grin technique, decolonization framing) is genuinely strong — the primary repair needed is aggressive prose reduction (~45% cut) and metaphor pruning to let the good teaching shine through.

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

# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/holidays-and-traditions.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/holidays-and-traditions.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/holidays-and-traditions.yaml`

---

## Review (from Phase D.1)

**Reviewed-By:** claude-opus-4-6

# Рецензія: Holidays & Traditions

**Level:** A1 | **Module:** 33
**Overall Score:** 8.2/10
**Status:** PASS
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PASS (with minor gaps)
- Sections: 7/7 present (Warm-up, Presentation, Presentation 2, Presentation 3, Practice, Practice 2, Practice 3)
- Vocabulary: 8/8 required present in content; 5/7 recommended used (торт, свічка absent from prose; Кутя mentioned but not as a vocab item)
- Grammar scope: CLEAN — З + Instrumental and Бажаю + Genitive treated as lexicalized chunks per plan
- Objectives: 4/4 addressed (name holidays ✓, give greetings ✓, talk about birthdays ✓, express wishes ✓)
- Missing: Plan requires explicit "Common Error Alert" for Accusative vs Genitive with бажаю — no [!warning] box exists for this
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm persona as Folklore Keeper maintained throughout; good model answers and real-world templates (Viber, email); but 3 consecutive Presentation sections before first Practice creates a long stretch without interaction |
| 2 | Coherence | 9/10 | <7 | Logical progression: holidays → greetings → wishes → birthdays → greeting cards → gifts → creative task; Summary ties back cleanly |
| 3 | Relevance | 9/10 | <7 | Highly practical — learner exits with greeting card templates, gift etiquette, and digital message patterns usable immediately |
| 4 | Educational | 8/10 | <7 | Excellent treatment of З + Instrumental (with [!warning] box); missing the equivalent error alert for Бажаю + Genitive that the plan explicitly requires |
| 5 | Language | 8/10 | <8 | Ukrainian prose clean of Russianisms/calques; IPA transcriptions use Russian-style vowel reduction [ɐ] instead of standard Ukrainian [ɑ]; false uniqueness claim on line 185 |
| 6 | Pedagogy | 8/10 | <7 | PPP structure followed; but three consecutive Presentation sections (lines 48–196) before first Practice is too much content before active engagement; no "try it yourself" scaffolding between presentations |
| 7 | Immersion | 8/10 | <6 | 45.7% vs target 35-55% — within range; English used appropriately for grammar explanations; Ukrainian used for all dialogues and examples |
| 8 | Activities | 7/10 | <7 | 10 activities with good variety; but "День знань", "День матері" (match-up activity), and "перемогою" (fill-in activity) appear in activities without being taught in content — scope mismatch |
| 9 | Richness | 9/10 | <6 | 5 engagement boxes; cultural hooks (12 dishes, Shchedryk, ear-pulling); mini-dialogues; real-world templates (Viber, email, paper card) |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5; warm welcome and clear instructions but long stretch before first active practice (lines 15–198) |
| 11 | LLM Fingerprint | 8/10 | <7 | Section openings vary (no 3+ identical patterns); but extreme choppy-sentence padding on line 185 («Батьки роблять це. Друзі роблять це. Дитина сміється.») and line 258 feels mechanical |
| 12 | Linguistic Accuracy | 9/10 | <9 | Ukrainian grammar correct throughout; IPA uses [ɐ] for unstressed final -а (debatable but not standard Ukrainian phonology); all case forms verified correct |
| 13 | Factual Accuracy | 8/10 | <8 | False uniqueness claim: «Ця традиція унікальна. Інші країни її не мають.» (line 185) — ear-pulling birthday traditions exist in Hungary, Brazil, and other cultures; all other facts verified (Різдво 25.12, 12 страв, Щедрик by Леонтович, Свт. Миколай 6.12) |

**Weighted Overall:**
```
(8×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 8×1.0 + 7×1.3 + 9×0.9 + 8×1.3 + 8×1.0 + 9×1.5 + 8×1.5) / 15.5
= (12.0 + 9.0 + 9.0 + 9.6 + 8.8 + 9.6 + 8.0 + 9.1 + 8.1 + 10.4 + 8.0 + 13.5 + 12.0) / 15.5
= 127.1 / 15.5
= 8.2/10
```

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: CLEAN
- Colonial framing: CLEAN — no Ukrainian-via-Russian comparisons found
- Grammar scope: CLEAN — Instrumental and Genitive treated as frozen chunks per plan
- Activity errors: 3 items reference untaught content (День знань, День матері, перемога)
- Beginner safety: 4/5
- Factual accuracy: 1 false uniqueness claim (line 185)

## Critical Issues Found

### Issue 1: False Uniqueness Claim (Factual)
- **Location**: Line 185 / Section «Practice 3» (subsection «Традиція: Тягнути за вуха» in Section «Presentation 3»)
- **Original**: «Ця традиція унікальна. Інші країни її не мають. Вона особлива для України.»
- **Problem**: Ear-pulling birthday traditions exist in Hungary (füle húzás), Brazil, Italy, and other cultures. Claiming uniqueness is a fabricated superlative.
- **Fix**: Remove the uniqueness claim. Replace with: «Ця традиція дуже популярна в Україні.» — states the cultural importance without false exclusivity.

### Issue 2: Activities Reference Untaught Content
- **Location**: Activities file, match-up activity 1 (lines 17-20) and fill-in activity 4 (lines 168-171)
- **Original**: Activity pairs include "День знань" → "1 вересня", "День матері" → "травень", and "Вітаю з перемогою!" — none of these holidays/words appear anywhere in the lesson content
- **Problem**: Activities should test what was taught. Introducing new vocabulary in exercises without prior presentation violates PPP pedagogy.
- **Fix**: Either (a) add День знань and День матері to the Section «Warm-up» seasonality table, and перемога to the greetings list, or (b) replace these activity items with holidays already taught (e.g., День Святого Миколая, День Незалежності which ARE in the content table)

### Issue 3: Missing Common Error Alert for Бажаю + Genitive
- **Location**: Section «Presentation 2» (lines 98–145)
- **Original**: No [!warning] box for the case mismatch with бажаю, unlike the excellent warning in Section «Presentation» for З + Instrumental (line 72)
- **Problem**: The plan explicitly requires: "Типова помилка: використання знахідного відмінка замість родового (напр., «Бажаю успіх» замість «Бажаю успіху»)". This pedagogical element is missing.
- **Fix**: Add a [!warning] box after line 104, parallel to the one in Presentation:
  ```
  > [!warning] **Stop: Accusative vs. Genitive**
  > ❌ **Incorrect:** «Бажаю успіх!» (I wish success [object])
  > ✅ **Correct:** «Бажаю успіху!» (I wish of-success [genitive])
  ```

### Issue 4: IPA Uses Russian-Style Vowel Reduction
- **Location**: Lines 108, 111 / Section «Presentation 2»
- **Original**: «Щастя —» and «Здоров'я —»
- **Problem**: The symbol [ɐ] (near-open central vowel) represents the Russian-style reduction of unstressed /а/. Standard Ukrainian phonology does not reduce unstressed vowels — final -я should be transcribed with [ɑ].
- **Fix**: Change to and respectively.

### Issue 5: Choppy-Sentence Padding
- **Location**: Line 185 / Section «Presentation 3»
- **Original**: «Ця традиція стара. Вона дуже весела. Батьки роблять це. Друзі роблять це. Дитина сміється. Всі рахують: "Один, два, три...". Це щасливий момент. Не бійтеся. Це не боляче. Це добра традиція. Це побажання росту!»
- **Problem**: 11 consecutive sentences of 2-5 words each. While short sentences suit A1, this density feels mechanical and padded. The repetitive "Це X" structure (5 times) is an LLM fingerprint.
- **Fix**: Consolidate into fewer, slightly longer sentences: «Ця весела традиція стара. Батьки і друзі роблять це, а дитина сміється. Всі рахують: "Один, два, три...". Не бійтеся — це не боляче, а побажання росту!»

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 108 | «Щастя —» | «Щастя —» | IPA — non-standard vowel reduction |
| 111 | «Здоров'я —» | «Здоров'я —» | IPA — non-standard vowel reduction |
| 185 | «Ця традиція унікальна. Інші країни її не мають.» | «Ця традиція дуже популярна в Україні.» | Fabricated superlative |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — pacing within each section is comfortable; English scaffolding present throughout
- Instructions clear? **Pass** — formulas clearly explained; checklist provided for writing task in Section «Practice 3»
- Quick wins? **Fail** — First three sections (Section «Warm-up», Section «Presentation», Section «Presentation 2») are pure presentation. No "try this now" micro-exercise until Section «Practice» (line 198). That's ~180 lines of content before active engagement.
- Ukrainian scary? **Pass** — Ukrainian introduced gently with translations; grammar treated as frozen chunks
- Come back tomorrow? **Pass** — cultural hooks (Shchedryk story, ear-pulling tradition, 12 dishes) are engaging and memorable

## Strengths

- **Excellent З + Instrumental treatment**: The [!warning] box on line 72 with ❌/✅ comparison and the "magnet" metaphor is outstanding beginner pedagogy
- **Real-world templates**: Section «Practice 3» provides both informal (Viber) and formal (email) greeting templates — immediately practical
- **Cultural richness**: Shchedryk as Carol of the Bells (Section «Warm-up», line 33), 12 dishes tradition (line 29), flower etiquette (line 284) — genuinely useful cultural knowledge
- **Greeting card structure**: The 4-part formula (Address → Holiday → Wishes → Signature) in Section «Practice» is a clear, actionable framework
- **Euphony explanation**: The зі/з distinction (line 84-85) is elegantly explained with pronunciation logic

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Factual Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 185: Remove «Ця традиція унікальна. Інші країни її не мають. Вона особлива для України.» → Replace with «Ця традиція дуже популярна в Україні.» — removes false uniqueness claim

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Activities match-up 1 (lines 17-20): Replace "День знань → 1 вересня" and "День матері → травень" with holidays from the content (e.g., "День Святого Миколая → 6 грудня" is already there; add "Святвечір → вечір перед Різдвом" or keep existing pair)
2. Activities fill-in 4 (line 168-171): Replace "перемогою" item with a holiday greeting from the content (e.g., "Вітаю з Днем Незалежності!" which IS in the content table on line 45)

**Expected score after fix:** 9/10

### Educational: 8/10 → 9/10
**What to fix:**
1. After line 104 in Section «Presentation 2»: Add [!warning] box for Accusative vs Genitive error with бажаю, mirroring the structure of the Instrumental warning in Section «Presentation»

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add a micro-exercise (2-3 item matching or "translate this greeting") between Section «Presentation» and Section «Presentation 2» to break up the presentation marathon
2. Add another micro-exercise between Section «Presentation 2» and Section «Presentation 3»

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 108: IPA →
2. Line 111: IPA →
3. Line 185: Remove false uniqueness claim (see Factual Accuracy above)

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Break the 3-Presentation marathon with micro-exercises (see Pedagogy above) — this also improves experience

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Line 185: Consolidate the 11 choppy sentences into 4-5 natural sentences (see Issue 5 fix above)
2. Line 258: Merge «Подарунки важливі. Вони показують любов. Вони показують повагу.» into «Подарунки показують любов і повагу.»

**Expected score after fix:** 9/10

### Beginner Safety: 8/10 → 9/10
**What to fix:**
1. Add quick-win micro-exercises between presentations (addresses the "Quick wins?" fail in the "Would I Continue?" test)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 8×1.0 + 9×1.3 + 9×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 10.8 + 9.9 + 10.8 + 8.0 + 11.7 + 8.1 + 11.7 + 9.0 + 13.5 + 13.5) / 15.5
= 138.5 / 15.5
= 8.9/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (research notes provide vocabulary frequencies, cultural hooks, and cross-references)
- Dates checked: 4 (Різдво 25.12 ✓, Новий рік 31.12/1.01 ✓, Дeнь Святого Миколая 6.12 ✓, День Незалежності 24.08 ✓)
- Named figures verified: 1 (Микола Леонтович — Щедрик ✓)
- Primary quotes cross-referenced: N/A — core track
- Chronological sequence: CONSISTENT
- Claims without research grounding: 1 found
  - Line 185: Prose claims «Ця традиція унікальна. Інші країни її не мають.» — no research note supports this uniqueness claim, and it is factually inaccurate (ear-pulling traditions exist in Hungary, Brazil, and other cultures)

## Verification Summary

- Content lines read: 349
- Activity items checked: 66 (across 10 activities)
- Ukrainian sentences verified: 28
- IPA transcriptions checked: 4 (щастя, здоров'я, успіху, любові)
- Factual claims verified: 8
- Issues found: 5

## Verdict

**PASS**

Solid A1 cultural module with warm persona, practical templates, and accurate cultural content. Five issues require fixes before production: (1) false uniqueness claim about ear-pulling tradition, (2) activities referencing untaught content (День знань, День матері, перемога), (3) missing [!warning] box for бажаю + Genitive error per plan, (4) IPA vowel reduction symbols, (5) choppy-sentence padding. All fixable without restructuring.

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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/holidays-and-traditions.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/holidays-and-traditions.yaml
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

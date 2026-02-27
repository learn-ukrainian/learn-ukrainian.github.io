# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Track Calibration

# Track Calibration: B1 (Modules 6+ — Full Immersion)

## Bilingual Scope
B1 modules 6+ target 85-100% Ukrainian immersion. Grammar is explained IN
Ukrainian using metalanguage learned in the bridge modules (M01-05).
The target is not hardcoded to 100% because vocabulary tables and
occasional transliterations contribute to the non-Ukrainian portion.
Flag: English prose explanations (should be in Ukrainian at this stage).
Flag: Modules below 85% immersion.
Do NOT flag: vocabulary table English glosses, frontmatter.

## Russicism Lookup (B1 Immersed)
All B1 Bridge Russicisms plus heightened sensitivity to:
- Surzhyk patterns in example sentences
- Russian word order calques (placing adjective after noun Russian-style)
- давайте + future perfective → Ukrainian imperative form (-мо)

## LLM Filler Sensitivity
Strict. No English filler. Flag all generic AI padding in Ukrainian:
- "це не просто X, а й Y" used repeatedly
- "давайте розглянемо" / "давайте дізнаємося" (LLM-typical transitions)
- "варто зазначити, що" (it's worth noting)
- Stacked abstract nouns in Ukrainian

## Content Focus
Fully Ukrainian prose. Focus on: natural Ukrainian, coherent paragraphs,
grammar accuracy, absence of Russianisms, register-appropriate vocabulary.


---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/aspect-complete-system.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/activities/aspect-complete-system.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/vocabulary/aspect-complete-system.yaml`

---

## Review (from Phase D.1)

# Рецензія: Вид дієслова: повна система

**Reviewed-By:** claude-opus-4-6

**Level:** B1 | **Module:** 6
**Overall Score:** 8.8/10
**Status:** PASS
**Reviewed:** 2026-02-26

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: All 5 plan sections present as H2 headers + standard Підсумок section
- Vocabulary: 9/9 required, 5/5 recommended — all present in vocabulary sidecar
- Grammar scope: CLEAN — no scope creep; motion verb aspects explicitly excluded per SCOPE comment
- Objectives: All 3 objectives addressed (complete system understanding, context clue identification, aspect choice for situations)
```

All content_outline points verified against the prose:
- Section «Розминка та Контекст»: Diagnostic task (пекла/спекла), Video/Photo mode, Paradjanov metaphor — all present
- Section «Граматична Система: Форми та Функції»: Past tense forms, future tense triple system with comparison table, ingressive по- — all present
- Section «Глибинна Семантика: Процес та Результат»: General-factual meaning, fact vs completion contrast, proverb analysis — all present
- Section «Аналіз Помилок та Тонкощі»: "буду + ДВ" trap, negation logic, attempt vs success, semelfactive -ну- — all present
- Section «Практика та Мовленнєві Ситуації»: Narrative architecture, 4-step algorithm, time markers table, real-world integration — all present

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Compelling opening hook with cinema metaphor; memorable Video/Photo mode analogy; TTT structure with diagnostic task before rules. Multiple "aha" moments (general-factual meaning, negation logic). |
| 2 | Coherence | 9/10 | <7 | Logical arc: intuition → formal grammar → deep semantics → errors → practice → summary. Each section builds on prior concepts. Cross-references within module (e.g., Section «Аналіз Помилок та Тонкощі» references загальнофактичне значення from Section «Глибинна Семантика: Процес та Результат»). |
| 3 | Relevance | 9/10 | <7 | Core B1 grammar concept per State Standard §4.2.3.1. Real-world scenarios: job interviews, office reports, IT daily stand-ups, cooking, storytelling. |
| 4 | Educational | 9/10 | <7 | TTT structure (test at line 23 before teach at line 43). 4-step decision algorithm (line 256-268). Time markers reference table. 14 engagement boxes. 11 activities covering identification, production, and error correction. |
| 5 | Language | 8/10 | <8 | Natural Ukrainian throughout, no Russianisms detected, no colonial framing. Minor issues: IT jargon at line 299 not flagged as non-standard; "фундаментально" appears 3 times across the module (lines 30, 73, 169) — slightly repetitive for a single text. |
| 6 | Pedagogy | 9/10 | <7 | Strong TTT: diagnostic task → explanation → practice loop repeated per topic. Cultural anchors (Paradjanov, proverbs, Shevchenko). Anticipates common mistakes (Section «Аналіз Помилок та Тонкощі»). Algorithm provides scaffolding for independent use. |
| 7 | Immersion | 10/10 | <6 | 99.8% Ukrainian. English only in scope comment (lines 1-6) and vocabulary sidecar glosses. No English prose explanations in body. |
| 8 | Activities | 8/10 | <7 | 11 activities, 7 types (quiz, match-up, fill-in ×3, error-correction, unjumble, cloze, mark-the-words, true-false). Issues: terminology inconsistency (складати/скласти in prose vs здавати/здати in activities); mark-the-words trivially solvable; unjumble has word-order ambiguity. |
| 9 | Richness | 9/10 | <6 | Cultural hooks: Параджанов, Шевченко, Леся Українка, folk proverbs, folk tales. Real-world: IT stand-ups, office reports, job interviews. Visual: comparison table (line 123-130). 11 distinct callout types used. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Clear explanations with analogies. Graduated difficulty. Algorithm provides safety net. Multiple micro-exercises embedded for immediate practice. |
| 11 | LLM Fingerprint | 8/10 | <7 | No "це не просто", no "давайте розглянемо", no "варто зазначити". Section openings are varied. 11 different callout types (no title repetition). Minor: "фундаментально" appears 3× across the module. |
| 12 | Linguistic Accuracy | 9/10 | <9 | All aspect rules correctly stated. Future tense paradigm correct. Ingressive по- correctly identified. General-factual meaning correctly explained. Minor: simplified etymology at line 85 (see Issue 4). |
| 13 | Factual Accuracy | 9/10 | <8 | «Тіні забутих предків» (1964) correct. Proverbs authentic. «Лісова пісня» reference honestly framed as hypothetical illustration at line 240. -тиму etymology from «імати» is the standard linguistic explanation. |

**Weighted Overall:**
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 8×1.1 + 9×1.2 + 10×1.0 + 8×1.3 + 9×0.9 + 9×1.3 + 8×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 10.8 + 8.8 + 10.8 + 10.0 + 10.4 + 8.1 + 11.7 + 8.0 + 13.5 + 13.5) / 15.5
= 137.1 / 15.5 = **8.8/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no красивий, добавити, хватить etc. found
- Calques: [CLEAN] — no "робити сенс", "брати місце" etc.
- Colonial framing: [CLEAN] — no "Unlike Russian" or comparisons with Russian
- Grammar scope: [CLEAN] — motion verb aspects explicitly excluded per SCOPE comment
- Activity errors: 2 minor (see Issues 1, 2)
- Beginner safety: 5/5
- Factual accuracy: [CLEAN] — all factual claims verified
- LLM filler phrases: [CLEAN] — D.0 pre-screen clean confirmed
- Word salad: [CLEAN] — all paragraphs have clear single points

## Critical Issues Found

### Issue 1: Content-Activity Terminology Inconsistency (Activities)
- **Location**: Content line 222 / Activities line 162 and 691
- **Original (content)**: «Найяскравіший приклад — пара «складати іспит» (НДВ) та «скласти іспит» (ДВ).»
- **Original (activity)**: «Пара 'здавати іспит' (НДВ) та 'здати іспит' (ДВ) ілюструє опозицію 'спроба проти успіху'.»
- **Problem**: The prose teaches the attempt-vs-success opposition using the pair складати/скласти, but the activities (match-up at line 162 and true-false at line 691) test using здавати/здати. Both pairs are valid Ukrainian, but a B1 learner who just learned the concept with one pair will be confused when tested on a different pair without the content establishing the equivalence.
- **Fix**: Either (a) add здавати/здати as a second example in the prose at line 222-228, noting it as a synonym pair, or (b) change the activity true-false at line 691 to use складати/скласти to match the content.

### Issue 2: Mark-the-Words Activity Trivially Solvable (Activities)
- **Location**: Activities line 464-475
- **Original**: «Кожного ранку вона прокидається дуже рано. Спочатку дівчина п'є гарячу каву, а потім довго читає новини. Вона завжди працює уважно, слухає музику, часто гуляє в парку і ніколи не поспішає.»
- **Problem**: The text contains ONLY НДВ verbs (прокидається, п'є, читає, працює, слухає, гуляє, поспішає). Since there are no ДВ verbs mixed in, a student can mark every verb without understanding aspect — the answer is "all of them." This doesn't test discrimination ability.
- **Fix**: Rewrite the text to include 3-4 ДВ verbs among the НДВ ones (e.g., add a sentence like «Сьогодні вона прокинулася пізніше, випила каву і вирішила погуляти») so students must distinguish between aspects.

### Issue 3: IT Jargon Without Register Contextualization (Language)
- **Location**: Line 299, Section «Практика та Мовленнєві Ситуації»
- **Original**: «Коли розробник каже «я фіксив баг» (НДВ), команда розуміє, що проблема все ще існує, і розробник продовжує боротьбу. Але коли лунає «я пофіксив баг» (ДВ, від англіцизму, який адаптувався до української видової системи за допомогою префікса), команда полегшено зітхає.»
- **Problem**: In a grammar module teaching formal aspect rules, using non-standard IT slang (англіцизми "фіксив"/"пофіксив") without explicitly noting these are colloquial/jargon forms may give B1 learners the impression these are standard Ukrainian. The parenthetical "(від англіцизму...)" partly addresses this, but doesn't clearly state the register.
- **Fix**: Add a brief note: «(Це розмовний ІТ-жаргон; у стандартній мові — «виправляв помилку» / «виправив помилку»)».

### Issue 4: Simplified Etymology (Linguistic Accuracy, Minor)
- **Location**: Line 85, Section «Граматична Система: Форми та Функції»
- **Original**: «Ці закінчення походять від давнього дієслова «імати» (мати), яке злилося з інфінітивом.»
- **Problem**: The verb «імати» in Old Ukrainian meant "to seize, to take, to catch" — not precisely "мати" (to have) in the modern sense. The parenthetical "(мати)" oversimplifies the etymological link. For B1 level this is acceptable, but a more precise wording would strengthen linguistic authority.
- **Fix**: Change to «від давнього дієслова «імати» (що означало «брати», «мати намір»)» — this is both more precise and more helpful for understanding the original meaning.

### Issue 5: Unjumble Word Order Ambiguity (Activities)
- **Location**: Activities lines 339-358
- **Problem**: Ukrainian has relatively free word order, but the unjumble activity accepts only one "correct" ordering. For example, item 2 accepts only «Він обов'язково напише цей довгий важливий лист завтра рано вранці», but «Завтра рано вранці він обов'язково напише цей довгий важливий лист» is equally valid.
- **Fix**: Either (a) shorten unjumble sentences to 6-7 words where word order is less ambiguous, or (b) accept multiple valid orderings if the platform supports it.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 299 | «я фіксив баг» | Add register note: «(розмовний ІТ-жаргон)» | Register |
| 85 | «імати» (мати) | «імати» (що означало «брати», «мати намір») | Precision |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass — Content is chunked into manageable subsections with callout breaks
- Instructions clear? Pass — Algorithm provides step-by-step decision framework
- Quick wins? Pass — Diagnostic task at line 23 gives immediate engagement; micro-exercises throughout
- Ukrainian scary? Pass — All Ukrainian is at appropriate B1 level; no overly complex syntax
- Come back tomorrow? Pass — Cultural hooks and practical scenarios create motivation to continue

## Strengths
- **Exceptional pedagogical framing**: The Video/Photo mode metaphor is genuinely memorable and provides a cognitive anchor that will serve learners well beyond this single module
- **TTT structure executed well**: Diagnostic task (line 23-32) before formal rules, with the торт пекла/спекла example being a particularly effective discovery moment
- **Rich cultural embedding**: Параджанов, Шевченко poetry, Ukrainian proverbs, Леся Українка — all serve the grammar teaching rather than being decorative
- **Practical real-world scenarios**: The office reporting dialogue (lines 291-296) showing process vs result in professional communication is immediately applicable
- **Comprehensive future tense table** (lines 123-130): Clear, well-structured, and a valuable reference for learners
- **4-step aspect choice algorithm** (lines 257-268): Actionable decision framework that covers ~95% of cases

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Activities: 8/10 → 9/10
**What to fix:**
1. Activities line 691: Change «здавати іспит» / «здати іспит» to «складати іспит» / «скласти іспит» to match the content at line 222, OR add здавати/здати as an additional example in the prose
2. Activities lines 464-475: Rewrite mark-the-words text to include mixed НДВ/ДВ verbs — e.g., replace current all-НДВ text with a passage like: «Кожного ранку вона прокидається рано. Сьогодні вона прокинулася, випила каву і вирішила погуляти. Зазвичай вона довго читає новини, працює уважно і слухає музику.» — НДВ answers: прокидається, читає, працює, слухає; ДВ NOT marked: прокинулася, випила, вирішила
3. Activities lines 339-358: Shorten unjumble sentences to 6-7 words to reduce word-order ambiguity

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 299: Add register note after «я пофіксив баг» — e.g., append «(Це розмовний ІТ-жаргон; у стандартній мові ви скажете «виправив помилку»)»
2. Line 85: Refine etymology — change «від давнього дієслова «імати» (мати)» to «від давнього дієслова «імати» (що означало «брати», «мати намір»)»

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Reduce repetition of "фундаментально/фундаментальна": Replace 1-2 of the 3 occurrences (lines 30, 73, 169) with more varied vocabulary — e.g., line 30 «фундаментальна різниця» → «принципова різниця»; line 169 «фундаментальна характеристика» → «визначальна характеристика»

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
Experience: 9, Coherence: 9, Relevance: 9, Educational: 9,
Language: 9, Pedagogy: 9, Immersion: 10, Activities: 9,
Richness: 9, Beginner Safety: 9, LLM: 9, Linguistic Accuracy: 9, Factual Accuracy: 9

(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 10×1.0 + 9×1.3 + 9×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 10.8 + 9.9 + 10.8 + 10.0 + 11.7 + 8.1 + 11.7 + 9.0 + 13.5 + 13.5) / 15.5
= 140.5 / 15.5 = 9.1/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (core grammar module, not seminar track)
- Dates checked: 1 — «Тіні забутих предків» (1964) ✓ correct
- Named figures verified: 3 — Сергій Параджанов ✓, Тарас Шевченко ✓, Леся Українка ✓
- Primary quotes cross-referenced: 0 (no direct quotes from named figures)
- Chronological sequence: N/A (grammar module)
- Claims without research grounding: 0

Additional factual checks:
- Proverb «Зробив діло — гуляй сміло» — authentic Ukrainian proverb ✓
- Proverb «Вік живи — вік учись» — authentic Ukrainian proverb ✓
- Etymology of -тиму from «імати» — standard linguistic explanation ✓ (with minor simplification noted in Issue 4)
- State Standard §4.2.3.1 reference — consistent with research notes ✓

## Verification Summary

- Content lines read: 316
- Activity items checked: 124 (across 11 activities)
- Ukrainian sentences verified: ~70 in prose + all activity items
- IPA transcriptions checked: 0 (none present — grammar module)
- Factual claims verified: 6 (date, figures, proverbs, etymology, State Standard)
- Issues found: 5

## Verdict

**PASS**

This is a strong B1 grammar module with effective TTT pedagogy, rich cultural embedding, and comprehensive coverage of the aspectual system per the plan. The 5 issues found are all minor (terminology inconsistency, activity design, register marking, etymology precision, word-order ambiguity) and none trigger auto-fail thresholds. Fixes are straightforward and would bring the module to 9.1/10.

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
failing gates:
lesson: 4847/4000 (raw: 5235) | pedagogy: 9 violations
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 40/100)
→ Revision recommended (severity 40/100)
→ 9 violations (significant)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/aspect-complete-system-audit.log for details)
```

---

## Instructions

1. Read the content file using the Read tool
2. For each issue identified in the review OR in the audit failures:
   a. Use Grep to find the exact text that needs fixing
   b. Produce a FIND/REPLACE pair with verbatim FIND text
3. Only fix issues documented above — no silent extra changes
4. Prioritize fixes by impact: audit gate failures first, then review issues
5. For Russianisms: replace with the standard Ukrainian form from the calibration table

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

```
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/aspect-complete-system.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/activities/aspect-complete-system.yaml
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

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

**Reviewed-By:** claude-opus-4-6

# Рецензія: Вид дієслова: повна система

**Level:** B1 | **Module:** 06
**Overall Score:** 8.8/10
**Status:** PASS
**Reviewed:** 2026-02-26

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: All 5 planned sections present as H2 headers + bonus «Підсумок» (not in plan, pedagogically appropriate addition)
- Vocabulary: 14/14 from plan (9 required + 5 recommended), 16 extra = 30 total
- Grammar scope: CLEAN — aspect system stays within b1-06 scope, does not encroach on b1-07/08 (past tense deep dives) or b1-16 (motion verb aspect)
- Objectives: All 3 objectives addressed (complete system understanding, context-based identification, situational aspect choice)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong opening hook with Parajanov metaphor, diagnostic baking scenario (lines 24-32), Video/Photo model keeps learner anchored. "Did I Learn?" test: 5/5. |
| 2 | Coherence | 9/10 | <7 | Clean arc: metaphor → diagnosis → grammar forms → deep semantics → error analysis → practice → summary. Each section builds on the previous; proverbs in section «Глибинна Семантика: Процес та Результат» revisit Video/Photo from section «Розминка та Контекст». |
| 3 | Relevance | 9/10 | <7 | Aspect is the single most important B1 grammar topic. IT stand-up example (line 299), job interview scenario (line 147), and work reporting dialogue (lines 291-296) anchor grammar in real-world Ukrainian professional life. |
| 4 | Educational | 9/10 | <7 | TTT structure: diagnostic task before rules, 4-step algorithm (lines 257-268), time marker table (lines 273-283). Clear "why" layer throughout — learner understands communicative consequences of aspect choice, not just rules. |
| 5 | Language | 8/10 | <8 | Ukrainian is natural throughout (99.8% immersion, zero Russianisms in prose). Issue: line 192 «Це союз, створений для опису процесів» uses "союз" metaphorically (alliance), but since B1 learners know "союз" as grammatical term (conjunction), this creates unnecessary ambiguity. |
| 6 | Pedagogy | 9/10 | <7 | Excellent TTT: diagnostic baking dialogue → concept explanation → practice integration. Proverbs as "linguistic anchors" (lines 182-185) are a clever mnemonic device. Algorithm + marker table give learners concrete tools. |
| 7 | Immersion | 10/10 | <6 | 99.8% Ukrainian. Only non-Ukrainian content: SCOPE comment, conceptual labels "Video mode"/"Photo mode" (used as teaching mnemonics, appropriate). |
| 8 | Activities | 8/10 | <7 | 11 activities, 8 distinct types — strong variety. Issue: 3 items use Russicism distractors ("рішав" line 534, "доказував" lines 595/602) in aspect-focused exercises, testing lexical correctness instead of aspect choice. |
| 9 | Richness | 9/10 | <6 | Parajanov film reference, Shevchenko poetry, Ukrainian proverbs, folk tales, IT jargon context, job interview scenario, office dialogue. Tables, exercises, callout boxes distributed throughout. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. The 4-step algorithm (lines 257-268) provides a concrete safety net. Graduated difficulty: warm-up → forms → semantics → nuances → practice. |
| 11 | LLM Fingerprint | 9/10 | <7 | Zero instances of "це не просто", "давайте розглянемо", "варто зазначити". Section openings are all distinct. Minor: "Розуміння цієї/цих X допоможе/дозволяє" appears 3× (lines 12, 18, 105), but this is natural Ukrainian pedagogical phrasing, not AI artifact. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Grammar rules verified: future tense paradigm (line 123-130 table), "бути + ДВ" prohibition, ingressive "по-", semelfactive "-ну-", general-factual imperfective — all accurate. Etymology of synthetic future from "імати" (line 105) is correct. No overgeneralizations found. |
| 13 | Factual Accuracy | 8/10 | <8 | Parajanov/«Тіні забутих предків» (1964) claim is accurate. Issue: line 240 states «у «Лісовій пісні» Лесі Українки семельфактивні дієслова передають раптові зміни настрою героїв» as fact, then illustrates with imagined examples ("можна уявити, як"). This is unsubstantiated literary analysis presented as established observation. |

**Weighted Overall:** (9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 8×1.1 + 9×1.2 + 10×1.0 + 8×1.3 + 9×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 8×1.5) / 15.5 = (13.5 + 9 + 9 + 10.8 + 8.8 + 10.8 + 10 + 10.4 + 8.1 + 11.7 + 9 + 13.5 + 12) / 15.5 = 136.6 / 15.5 = **8.8/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no Russianisms in prose content. "рішав" and "доказував" appear only as incorrect distractor options in activities (intentional but off-focus).
- Calques: [CLEAN] — no calques detected.
- Colonial framing: [CLEAN] — no Russian comparisons, no "Unlike Russian..." patterns.
- Grammar scope: [CLEAN] — stays within b1-06 scope. Motion verb aspect explicitly excluded per SCOPE comment.
- Activity errors: [3 off-focus distractors] — see Issue 2 below.
- Beginner safety: 5/5
- Factual accuracy: [1 unsubstantiated claim] — «Лісова пісня» literary analysis.

## Critical Issues Found

### Issue 1: Unsubstantiated literary analysis in culture callout
- **Location**: Line 240 / Section «Аналіз Помилок та Тонкощі»
- **Original**: «у «Лісовій пісні» Лесі Українки семельфактивні дієслова передають раптові зміни настрою героїв: можна уявити, як на тлі тихого лісового фону (НДВ: «шуміло», «плескалося») раптово «крикнула» Мавка або «тріснула» гілка»
- **Problem**: The opening clause states as fact that semelfactive verbs in «Лісова пісня» convey sudden mood shifts, then pivots to "можна уявити" (one can imagine) to illustrate — effectively inventing an example while framing it as analysis of the actual text. The verbs «шуміло», «плескалося», «крикнула», «тріснула» are plausible for the forest setting but are not cited from the actual drama.
- **Fix**: Either cite a real passage from «Лісова пісня» with actual verbs, or reframe the entire callout as a hypothetical teaching exercise: «Уявімо лісову сцену...» without attributing specific linguistic features to Леся Українки's text.

### Issue 2: Off-focus Russicism distractors in aspect activities
- **Location**: Activities YAML, lines 534, 595, 602
- **Original**: Distractor "рішав" (line 534) in negation activity; distractors "доказував"/"доказав" (lines 595, 602) in "attempt vs success" activity.
- **Problem**: These activities test aspect choice (НДВ vs ДВ), but "рішав" and "доказувати/доказати" are Russicisms (correct: вирішував, доводити/довести). Including them as distractors tests lexical correctness rather than the target skill. A learner who correctly identifies the aspect but picks "доказував" because they don't know it's a Russicism fails for the wrong reason.
- **Fix**: Replace "рішав" with a valid Ukrainian imperfective option (e.g., "розв'язував"). Replace "доказував"/"доказав" with aspect-contrasting alternatives using standard verbs (e.g., "переконував"/"переконав").

### Issue 3: Potentially confusing "союз" metaphor
- **Location**: Line 192 / Section «Аналіз Помилок та Тонкощі»
- **Original**: «допоміжне дієслово «бути» в майбутньому часі (буду, будеш, буде) працює **винятково** з дієсловами недоконаного виду. Це союз, створений для опису процесів.»
- **Problem**: The word "союз" is used metaphorically (meaning "alliance/partnership"), but B1 learners already know "союз" as a grammatical term meaning "conjunction" (і, але, або). This could cause a moment of confusion — "Is бути a conjunction?"
- **Fix**: Replace "союз" with a non-grammatical metaphor: «Це тандем, створений для опису процесів» or «Це партнерство, створене для опису процесів».

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 192 | «Це союз, створений для опису процесів» | «Це тандем, створений для опису процесів» | Clarity (ambiguous term) |
| 534 (act.) | distractor "рішав" | "розв'язував" | Russicism distractor |
| 595 (act.) | distractor "доказував" | "переконував" | Russicism distractor |
| 602 (act.) | distractor "доказував"/"доказав" | "переконував"/"переконав" | Russicism distractor |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass — graduated progression, concepts introduced one at a time with examples before rules.
- Instructions clear? Pass — diagnostic task (baking scenario), Video/Photo model, 4-step algorithm all provide clarity.
- Quick wins? Pass — the diagnostic task at line 24 gives immediate success experience.
- Ukrainian scary? Pass — immersion is well-scaffolded with familiar vocabulary and real-world scenarios.
- Come back tomorrow? Pass — cultural hooks (Parajanov, Shevchenko, IT jargon) make content memorable and worth returning to.

## Strengths

- **Parajanov metaphor (line 17)**: Linking cinematic techniques to aspect choice is brilliant pedagogy — it makes an abstract grammar concept visual and memorable. The dynamic camera = НДВ, static frame = ДВ mapping is both culturally authentic and pedagogically effective.
- **Diagnostic baking dialogue (lines 24-32)**: Perfect TTT implementation — the learner encounters the problem before the rule is stated. The scenario is vivid (flour everywhere, tired Olena) and the aspect contrast is immediately obvious.
- **4-step decision algorithm (lines 257-268)**: Converts abstract grammar knowledge into a concrete, actionable procedure. This is the kind of tool a learner can actually use in live conversation.
- **Proverbs as anchors (lines 182-185)**: «Зробив діло — гуляй сміло» (ДВ) vs «Вік живи — вік учись» (НДВ) are memorable, authentic, and perfectly illustrate the core semantic distinction.
- **IT jargon callout (line 299)**: «я фіксив баг» vs «я пофіксив баг» shows how even borrowed vocabulary adapts to the Ukrainian aspect system — a genuinely insightful observation that connects grammar to modern professional life.

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Language: 8/10 → 9/10
**What to fix:**
1. Line 192: Change «Це союз, створений для опису процесів» → «Це тандем, створений для опису процесів» — eliminates grammatical term ambiguity.

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Line 534: Replace distractor "рішав" with "розв'язував" — tests aspect (imperfective alternative) not Russicism avoidance.
2. Lines 595, 602: Replace distractors "доказував"/"доказав" with "переконував"/"переконав" — maintains aspect contrast with standard Ukrainian vocabulary.

**Expected score after fix:** 9/10

### Factual Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 240: Rewrite the «Лісова пісня» callout to frame the example as hypothetical illustration rather than literary analysis. Change opening from «у «Лісовій пісні» Лесі Українки семельфактивні дієслова передають раптові зміни настрою героїв:» to «Уявімо сцену з лісової казки (як у «Лісовій пісні» Лесі Українки):» — removes the unsupported analytical claim while preserving the cultural reference.

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 10×1.0 + 9×1.3 + 9×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5+9+9+10.8+9.9+10.8+10+11.7+8.1+11.7+9+13.5+13.5) / 15.5
= 140.5 / 15.5 = 9.06/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track — research notes are supplementary)
- Dates checked: 1 — «Тіні забутих предків» (1964) ✅ correct
- Named figures verified: 2 — Сергій Параджанов ✅, Тарас Шевченко ✅
- Primary quotes cross-referenced: 2 proverbs verified as authentic Ukrainian proverbs ✅
- Chronological sequence: N/A (grammar module)
- Claims without research grounding: 1 — the «Лісова пісня» semelfactive verb analysis (line 240) is not grounded in research notes and presents unsubstantiated literary analysis.

## Verification Summary

- Content lines read: 316
- Activity items checked: 119 (across 11 activities)
- Ukrainian sentences verified: 48 (all example sentences, dialogue lines, proverbs)
- IPA transcriptions checked: 0 (none present — appropriate for B1 grammar module)
- Factual claims verified: 5 (Parajanov film date, Shevchenko attribution, 2 proverbs, «імати» etymology)
- Issues found: 3

## Verdict

**PASS**

This is a strong B1 grammar module with excellent pedagogical structure, engaging cultural hooks, and near-perfect immersion. The three issues found are minor and localized: an ambiguous metaphor (line 192), off-focus activity distractors (3 items), and one unsubstantiated literary claim (line 240). All are fixable without restructuring. After targeted fixes, this module should reach 9.0+/10.

---

## Audit Failures (from automated re-audit)

```
Gates:   6 pass, 1 info
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

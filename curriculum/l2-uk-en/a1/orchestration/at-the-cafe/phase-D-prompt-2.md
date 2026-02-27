# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-cafe.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/at-the-cafe.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/at-the-cafe.yaml`

---

## Review (from Phase D.1)

**Reviewed-By:** claude-opus-4-6

# Рецензія: At the Café

**Level:** A1 | **Module:** 19
**Overall Score:** 8.1/10
**Status:** PASS
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: 7/7 from meta outline present as H2 ✓
- Vocabulary: 8/8 required present, 5/6 recommended present (чайові missing from vocab file)
- Grammar scope: Accusative ✓, Genitive chunks ✓, Instrumental chunks ✓. Plan lists «візьміть» imperative — NOT taught. Plan requires «Мені, будь ласка...» — NOT taught in prose.
- Objectives: 4/4 learning objectives addressed ✓
```

**Key gap:** The plan (plans/a1/at-the-cafe.yaml) explicitly lists `'Ввічливе замовлення: корекція помилки «Я хочу» на більш природні та ввічливі форми «Мені, будь ласка...» або «Я буду...»'`. The content teaches «Я буду...» and «Я візьму...» but never introduces «Мені, будь ласка...» in the prose, despite it being arguably the most common Ukrainian ordering pattern. The unjumble activity (line 235-236) tests this pattern, creating an activity-content disconnect.

The plan also lists `Polite imperatives (принесіть, візьміть)` — the content teaches «принесіть» and «дайте» but omits «візьміть».

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good café scenario arc (greet→order→pay); lacks warmth markers — zero "Great!", "Well done!", "You've got this!" phrases found; only 1 "Don't worry" (line 50) and 1 "practice makes perfect" (line 202) |
| 2 | Coherence | 9/10 | <7 | Logical 7-section progression; each section builds on the previous; Kulchytsky legend in final section matches meta outline |
| 3 | Relevance | 9/10 | <7 | Directly practical — café ordering is high-frequency A1 need; vocabulary is immediately usable |
| 4 | Educational | 8/10 | <7 | Clear accusative rule + table (line 181-192); missing «Мені, будь ласка» pattern is a real pedagogical gap; good рахунок/чек distinction (line 294-298) |
| 5 | Language | 8/10 | <8 | Line 286: «каву з молоком» used in non-accusative English context (should be citation form «кава з молоком»); IPA inconsistency: stressed а = [a] in «кава» but [ɑ] elsewhere |
| 6 | Pedagogy | 8/10 | <7 | PPP structure present; good scaffolding from chunks to rules to practice; missing key ordering pattern and insufficient encouragement per beginner safety requirements |
| 7 | Immersion | 8/10 | <6 | 25.4% Ukrainian (target 25-40%); at the very bottom of the range; multiple dialogues and Ukrainian phrases embedded well |
| 8 | Activities | 7/10 | <7 | 9 activities with good variety; implausible «Дайте смачну воду» (line 214-215); unjumble tests «Мені будь ласка каву» (line 235-236) which prose never teaches |
| 9 | Richness | 8/10 | <6 | Kulchytsky legend, Lviv café culture, tipping customs, menu simulation, 4 dialogues; good range of cultural touchpoints |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 5/5; pacing good with small vocabulary chunks; but only 1 "don't worry" moment (requires ≥2) and ≤2 encouragement phrases (requires ≥3) |
| 11 | LLM Fingerprint | 8/10 | <7 | Section openings are varied (no monotony); no "це не просто" patterns; but "golden ticket" (line 13), "The Magic of Change" (line 41), "The Magic Word" (line 94) — slightly generic AI-friendly headers; "dressing up for dinner" metaphor (line 50) is cute but borderline cliché |
| 12 | Linguistic Accuracy | 9/10 | <9 | Ukrainian grammar is clean throughout prose; accusative rules correctly stated; only issue is line 286 case form in English context |
| 13 | Factual Accuracy | 8/10 | <8 | Line 403 «Він навчив Європу пити каву» presents disputed legend as fact in Ukrainian summary, though English framing (line 399) correctly says "legend" and "according to the story"; tipping norms and etiquette are accurate |

**Weighted Overall:**
(8×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 8×1.0 + 7×1.3 + 8×0.9 + 8×1.3 + 8×1.0 + 9×1.5 + 8×1.5) / 15.5
= (12.0 + 9.0 + 9.0 + 9.6 + 8.8 + 9.6 + 8.0 + 9.1 + 7.2 + 10.4 + 8.0 + 13.5 + 12.0) / 15.5
= 126.2 / 15.5 = **8.1/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no кушать, приймати участь, etc.
- Calques: [CLEAN] — no робити сенс, брати місце, etc.
- Colonial framing: [CLEAN] — no "Unlike Russian" comparisons
- Grammar scope: [MINOR] — «без цукру» and «з молоком» correctly presented as chunks; no over-explanation of Genitive/Instrumental rules
- Activity errors: [ISSUES] — implausible «Дайте смачну воду»; activity-content disconnect for «Мені, будь ласка»
- Beginner safety: 5/5 on "Would I Continue?" test
- Factual accuracy: [MINOR] — Kulchytsky legend framing inconsistency between English and Ukrainian
- LLM fingerprint: [CLEAN] — no structural monotony, no "це не просто" rhetoric

## Critical Issues Found

### Issue 1: MISSING_PATTERN — «Мені, будь ласка...» never taught
- **Location**: Entire prose content / Section «Замовлення: Знахідний відмінок» and Section «Презентація: Привітання та ввічливість»
- **Problem**: The plan explicitly requires teaching «Мені, будь ласка...» as a core polite ordering form alongside «Я буду...». This is arguably the MOST commonly used ordering pattern in real Ukrainian cafés. The content teaches «Я буду...» (line 161-167) and «Я візьму...» (line 169-173) but completely skips «Мені, будь ласка...». Meanwhile, the unjumble activity (line 235-236) tests exactly this pattern — asking students to assemble «Мені будь ласка каву» — which the prose never taught. The quiz explanation on line 348 also says "Use «Я буду» or «Мені, будь ласка»" — referencing a pattern that was never presented.
- **Fix**: Add a third ordering structure in Section «Замовлення: Знахідний відмінок» after the «Я візьму...» block (around line 173):
```
**3. Мені...**
Literally: "For me..."
This is the most natural way to order in casual settings.
- **Мені каву, будь ласка.** (Coffee for me, please.)
- **Мені чай з лимоном.** (Tea with lemon for me.)
```

### Issue 2: CASE_FORM_MISUSE — «каву з молоком» in non-accusative context
- **Location**: Line 286 / Section «Рахунок та оплата»
- **Original**: «каву з молоком»
- **Problem**: The sentence reads "You have finished your delicious **каву з молоком**." Here the Ukrainian phrase is embedded in English prose as a descriptive reference to the drink, not as a direct object in a Ukrainian sentence. Using the accusative form «каву» here is pedagogically confusing for a beginner who is actively learning that words change form depending on context. The citation/reference form should be nominative.
- **Fix**: Change to «кава з молоком» (nominative/citation form): "You have finished your delicious **кава з молоком**."

### Issue 3: IMPLAUSIBLE_ACTIVITY — «Дайте смачну воду»
- **Location**: Activities file, fill-in item (line 214-215)
- **Original**: «Дайте смачну воду»
- **Problem**: "Give [me] tasty water" is not a plausible café order. Nobody describes water as "tasty" when ordering. This exercise exists purely to drill feminine adjective accusative agreement, but the sentence feels artificial and would confuse a learner about real usage.
- **Fix**: Replace with «Дайте холодну воду» (Give cold water) — realistic and drills the same grammar point. Update answer to "холодну" and options to ["холодну", "холодна", "холодний", "холодне"].

### Issue 4: FACTUAL_OVERSTATEMENT — Kulchytsky legend stated as fact
- **Location**: Line 403 / Section «Культурний контекст: Українські кав'ярні»
- **Original**: «Він навчив Європу пити каву.»
- **Problem**: The English text (line 399) correctly frames this as "a beloved Ukrainian legend" and uses "according to the story" — appropriate hedging for a disputed claim. But the Ukrainian summary on line 403 drops all qualifiers and states «Він навчив Європу пити каву» as unqualified fact. This is misleading. Historians dispute Kulchytsky's role; many attribute the first Viennese coffeehouse to Johannes Diodato.
- **Fix**: Add qualifier: «За легендою, він навчив Європу пити каву.» (According to legend, he taught Europe to drink coffee.)

### Issue 5: VOCABULARY_GAP — чайові missing from vocabulary file
- **Location**: Vocabulary file (vocabulary/at-the-cafe.yaml)
- **Original**: N/A (absent)
- **Problem**: «чайові» (tip) is taught in the prose (line 322) and listed as a recommended vocabulary item in the plan, but it's missing from the vocabulary YAML file. Students who rely on the vocabulary list for review will not find this term.
- **Fix**: Add entry to vocabulary file:
```yaml
- lemma: "чайові"
  translation: "tip"
  pos: "noun"
  gender: "pl"
  example: "Залиште чайові, будь ласка."
```

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 286 | «каву з молоком» (in English context) | «кава з молоком» | Case form / pedagogical clarity |
| 403 | «Він навчив Європу пити каву.» | «За легендою, він навчив Європу пити каву.» | Factual qualifier |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — vocabulary introduced in small chunks (3-4 items), pacing comfortable
- Instructions clear? **Pass** — clear English explanations throughout, step-by-step ordering guide (line 381-386)
- Quick wins? **Pass** — early match of basic drinks (кава, чай, вода), immediate practice in simple dialogue (lines 104-106)
- Ukrainian scary? **Pass** — introduced gently with English translations; grammar previewed metaphorically ("dressing up for dinner")
- Come back tomorrow? **Pass** — engaging café scenario, multiple dialogues, cultural hooks

**Warmth Deficit:** Despite 5/5 on the structural test, emotional safety markers fall short:
- Welcome/orientation: ✓ (line 17-19, «Ласкаво просимо!»)
- Curiosity trigger: ✓ (line 42-50, grammar preview as mystery)
- Quick wins: ✓ (lines 104-106, simple dialogue)
- Encouragement phrases: Only 2 found — «Do not worry about the rules just yet» (line 50), «Remember, practice makes perfect!» (line 202). Target is ≥3.
- "Don't worry" moments: Only 1 found (line 50). Target is ≥2.
- Progress markers: 1 found — «You are now equipped to caffeinate yourself across Ukraine» (line 434). Could use mid-lesson progress markers.

## Strengths

- **Excellent dialogue variety**: 4 distinct dialogues (simple greeting lines 104-106, latte order lines 268-274, payment lines 315-319, full interaction lines 356-369) progressively increase in complexity — strong scaffolding.
- **Clear accusative table**: The comparison table on lines 181-192 is a model of visual grammar presentation — clean columns, consistent examples, covers all three genders. A beginner can reference this repeatedly.
- **Practical cultural content**: The рахунок/чек distinction (lines 294-298), tipping etiquette (lines 321-326), and Ви/ти guidance (lines 62-67) are genuinely useful — these are real pitfalls for tourists and language learners.
- **Menu simulation**: The visual menu (lines 340-349) is a creative immersion element that mimics real-world reading practice.
- **Lexical chunk approach**: Teaching «з молоком» and «без цукру» as fixed phrases (lines 227-239, 242-243) is pedagogically sound for A1 — avoids overloading with Instrumental/Genitive rules.

## Fix Plan to Reach 9/10 (REQUIRED — score is 8.1)

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. After the accusative table (line 192), add: "You just learned one of the biggest grammar patterns in Ukrainian — well done! The Accusative case is yours now."
2. After the payment dialogue (line 319), add: "Excellent! You can now handle the entire café visit from start to finish."
3. In Section «Розминка: Кава — це культура» (around line 28), after introducing the Big Three drinks, add: "Don't worry if these words feel new — by the end of this lesson, you'll be ordering them like a regular."

**Expected score after fix:** 9/10

### Educational: 8/10 → 9/10
**What to fix:**
1. Section «Замовлення: Знахідний відмінок» (after line 173): Add «Мені, будь ласка...» as a third ordering pattern with 2-3 examples, matching the plan requirement.
2. Section «Презентація: Привітання та ввічливість» (around line 92): Add «Візьміть» as a third polite imperative alongside «Дайте» and «Принесіть», matching the plan grammar specification.

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 286: Change «каву з молоком» → «кава з молоком» in the English prose context.
2. Standardize IPA for stressed а — use [ɑ] consistently (line 30 «кава» →; line 21 «каву» →).

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add 2 more encouragement moments (see Experience Quality fixes above).
2. Add 1 more "don't worry" moment in Section «Уточнення: Яку каву ви бажаєте?» (around line 243): "Don't worry about memorizing all these forms right now — they'll become second nature with practice."

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Fill-in line 214-215: Replace «Дайте смачну воду» → «Дайте холодну воду» with corresponding option updates.
2. Ensure «Мені, будь ласка...» is taught in the prose before the unjumble activity tests it (see Educational fix above — this resolves the disconnect).

**Expected score after fix:** 9/10

### Factual Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 403: Change «Він навчив Європу пити каву.» → «За легендою, він навчив Європу пити каву.»

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Line 41: Consider renaming "The Magic of Change" → something more specific, e.g., "Grammar Preview: Words That Transform" or simply "Grammar Preview: -а becomes -у"
2. Line 94: "The Magic Word" → "The Power of «Будь ласка»"

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 8×1.0 + 9×1.3 + 8×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9.0 + 9.0 + 10.8 + 9.9 + 10.8 + 8.0 + 11.7 + 7.2 + 11.7 + 9.0 + 13.5 + 13.5) / 15.5
= 137.6 / 15.5 = 8.9/10
```

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (A1 core track — no research file exists)
- Key Facts Ledger present: NO
- Dates checked: 1 (1683 — Battle of Vienna, historically accurate)
- Named figures verified: 1 (Юрій Кульчицький — real historical figure, legend correctly hedged in English but not in Ukrainian summary)
- Primary quotes cross-referenced: N/A
- Chronological sequence: CONSISTENT
- Claims without research grounding: 1 — Line 403 overstates Kulchytsky's role without qualifier in Ukrainian

## Verification Summary

- Content lines read: 436
- Activity items checked: 109 (across 9 activities)
- Ukrainian sentences verified: 48 (all dialogue lines + example sentences)
- IPA transcriptions checked: 12
- Factual claims verified: 5 (Kulchytsky legend, tipping norms, рахунок/чек distinction, Ви etiquette, café culture)
- Issues found: 5 critical/significant

## Verdict

**PASS**

Solid A1 café module with good structure, accurate grammar teaching, and engaging dialogues. The most impactful fix needed is adding the «Мені, будь ласка...» ordering pattern to the prose — this is a plan requirement, the most natural Ukrainian ordering form, and already tested by activities. Secondary fixes: correct the accusative form misuse on line 286, replace the implausible «Дайте смачну воду» activity item, add warmth/encouragement markers, and qualify the Kulchytsky claim in the Ukrainian summary.

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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-cafe.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/at-the-cafe.yaml
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

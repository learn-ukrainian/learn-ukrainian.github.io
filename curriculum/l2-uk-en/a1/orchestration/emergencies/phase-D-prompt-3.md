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

# Track Calibration: A1

## Bilingual Scope
A1 uses PROGRESSIVE immersion — targets increase per module:
- Modules 1-2: 5-15% Ukrainian (Cyrillic intro, mostly English)
- Modules 3-5: 10-25% Ukrainian (early vocab building)
- Modules 6-10: 15-35% Ukrainian (growing immersion)
- Modules 11-20: 25-40% Ukrainian (foundation established)
- Modules 21+: 35-55% Ukrainian (consolidation)

Mixing English explanations with Ukrainian examples is CORRECT pedagogy.
Do NOT flag bilingual content as LANGUAGE_BLENDER.
Flag: Full Ukrainian paragraphs that exceed the module's immersion band.
Flag: Modules that are below their minimum immersion target.

## Russicism Lookup (A1-specific)
These appear frequently in A1 content. Flag as HIGH:
- здача → решта (change/money)
- тапочки → капці (slippers)
- кушати → їсти (to eat)
- давайте попрактикуємо → попрактикуймо (let's practice — Russian imperative calque)
- давайте повторимо → повторімо (let's repeat — Russian imperative calque)
- давайте подивимося → подивімося (let's look — Russian imperative calque)
- чоловіче → пане (sir — register mismatch in service contexts)
- надіятися → сподіватися (to hope)
- піднімається → підводиться (gets up)
- получати → отримувати (to receive)
- вообще → взагалі (in general)

## Anglicism Lookup (A1-specific)
- "Що ви хочете?" → "Що бажаєте?" (register in service/hospitality contexts)
- "роблять каву" → "готують каву" (make coffee — English calque)
- "робити добру каву" → "готувати смачну каву" (make good coffee)

## LLM Filler Sensitivity
At A1, some motivational content is ACCEPTABLE when woven into teaching.
Flag ONLY: pure cheerleading with zero educational content, generic padding
("Numbers are everywhere", "Language is not just about labeling things",
"As you continue your Ukrainian journey").
Do NOT flag: warm encouragement that includes a teaching point.

## Content Focus
Simple sentences are expected. Don't flag short paragraphs.
Focus on: Russianisms, factual errors in callouts, and fluff replacing actual teaching.
Do NOT penalize: friendly tone, bilingual explanations, basic vocabulary presentation.


---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/emergencies.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/emergencies.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/emergencies.yaml`

---

## Review (from Phase D.1)

# Рецензія: Emergencies

**Reviewed-By:** claude-opus-4-6

**Level:** A1 | **Module:** 42
**Overall Score:** 8.5/10
**Status:** PASS
**Reviewed:** 2026-02-26

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: 4/4 present (Вступ, Презентація, Практика, Виробництво та підсумок)
- Vocabulary: 8/8 required present (допомога, швидка, поліція, пожежна, небезпека, аварія, лікарня, документи), 6/6 recommended present (загубити, вкрасти, травма, адреса, свідок, заява), 4 extra (дзвонити, викликати, лікар, офіцер, гаманець, метро)
- Grammar scope: PASS — Vocative case, imperative mood, location expressions all within A1 scope per plan
- Objectives: 4/4 addressed (call for help, describe problems, give location, understand instructions)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good PPP arc with warm opening and summary celebration. Some English prose is overly elaborate (lines 119-129), dragging the flow. Dialogues and rapid-fire drill at end are effective. |
| 2 | Language | 8/10 | <8 | Ukrainian generally correct; one semantic error «розділяє ці концепції» (line 95). English prose sometimes too verbose for A1 tutor voice ("Let us" x2, emphatic phrasing). No Russianisms found. |
| 3 | Pedagogy | 8/10 | <7 | Solid PPP structure with scaffolded progression. Vocative "Поліціє!" (line 75) is grammatically correct but practically unused by native speakers — misleading for A1 learners. Good contrast between дзвонити/викликати. |
| 4 | Activities | 9/10 | <7 | 10 activities across 6 types (match-up, fill-in, quiz, unjumble, group-sort). Exceeds plan's 4 activity types. Items test Ukrainian language skills appropriately for A1. |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Clear English scaffolding, warm tone, quick wins with vocabulary matching. Ukrainian introduced gently. One minor concern: Vocative terminology (Кличний відмінок) may feel heavy for A1. |
| 6 | LLM Fingerprint | 8/10 | <7 | No "це не просто"/"це не лише" patterns. No generic AI clichés. "Let us" (lines 179, 190) instead of "Let's" — overly formal. Some emphatic prose: "universally understood and preferred... across every single region of Ukraine without exception" (line 129). |
| 7 | Linguistic Accuracy | 9/10 | <9 | Generally accurate Ukrainian. One clear semantic error: «розділяє» (divides) should be «розрізняє» (distinguishes) at line 95. Vocative paradigm table correct. Stress marks present on key terms. |

**Weighted Overall:** (8×1.5 + 8×1.1 + 8×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9 = (12.0 + 8.8 + 9.6 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9 = 75.3 / 8.9 = **8.5/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN — no items from A1 calibration list found; «визивати» correctly flagged by content itself
- Calques: CLEAN — no "робити сенс" or similar patterns
- Colonial framing: CLEAN — no "Unlike Russian" patterns; Russicism section frames decolonization positively
- Grammar scope: CLEAN — Vocative case and imperative are within A1 plan scope
- Activity errors: CLEAN — all items checked, grammar correct in activity text
- Beginner safety: 5/5
- Factual accuracy: 2 concerns flagged (see Issues 3 and 4 below)

## Critical Issues Found

### Issue 1: Semantic Error — «розділяє» vs «розрізняє»
- **Location**: Line 95 / Section «Презентація»
- **Original**: «Українська мова розділяє ці концепції.»
- **Problem**: «Розділяти» means "to divide/separate" — the correct verb for "distinguishes between" is «розрізняти». Also, «концепції» is valid but «поняття» is more natural in this pedagogical context.
- **Fix**: Change to «Українська мова розрізняє ці поняття.»

### Issue 2: Pragmatically Misleading Vocative «Поліціє!»
- **Location**: Lines 74-75, 86 / Section «Презентація»
- **Original**: «Поліціє, зупиніть його!»
- **Problem**: While the vocative "Поліціє" is grammatically derivable from the paradigm, native Ukrainian speakers do not use this form in practice. When shouting for police help, Ukrainians use the nominative "Поліція!" as an exclamation, or address individual officers with "Офіцере!" or "Пане офіцере!". Teaching A1 learners a form they would never hear in real life is pedagogically counterproductive.
- **Fix**: Replace the "поліція → поліціє" row in the table with a note: "For «поліція» (an institution), Ukrainians use the nominative «Поліція!» as an exclamation. For individual officers, use «Офіцере!» or «Пане!»" Keep the paradigm note as a footnote for completeness.

### Issue 3: Unqualified Factual Claim — 112 Operators Speaking English
- **Location**: Line 39 / Section «Вступ»
- **Original**: «Оператори 112 також говорять англійською мовою.»
- **Problem**: This is an unqualified blanket statement. Not all 112 operators across Ukraine are guaranteed to speak English. This could give A1 learners false confidence in a crisis.
- **Fix**: Qualify to «Деякі оператори 112 говорять англійською мовою.» or «Система 112 підтримує англійську мову.»

### Issue 4: Imprecise 112 Launch Date
- **Location**: Line 35 / Section «Вступ»
- **Original**: «У 2023 році міністерство запустило єдиний номер служби 112.»
- **Problem**: Ukraine's 112 system has been under phased implementation since approximately 2012-2014. Saying it was "launched" in 2023 is an oversimplification. The research notes say "2023-2024" but the actual rollout was gradual.
- **Fix**: Change to «Україна поступово впроваджує єдиний номер 112.» or «З 2023 року система 112 активно працює по всій Україні.» — removing the word "запустило" (launched) which implies a single launch event.

### Issue 5: Richness Gap — Missing [!culture] Callout for «Дія»
- **Location**: Lines 253-261 / Section «Виробництво та підсумок»
- **Original**: Plain text subsection about Дія and єДопомога
- **Problem**: The plan meta specifies a [!cultural] box for this content. The richness audit shows cultural: 1/3 — wrapping this section in a [!culture] callout would address the gap.
- **Fix**: Wrap lines 256-261 in a `> [!culture]` callout box.

### Issue 6: Confusing Wording — «Це формальний наказ»
- **Location**: Line 18 / Section «Вступ»
- **Original**: «Це формальний наказ. Це дієслово означає "допомагати".»
- **Problem**: «Наказ» means "order/command" (a noun denoting a specific speech act), but «допоможіть» is an imperative VERB FORM (наказовий спосіб). The two sentences together confuse verb form with speech act, and then confuse it further by saying "this verb means 'to help'" — the learner doesn't know if "цe" refers to the imperative form or to the verb root.
- **Fix**: Rewrite to: «Це формальна форма дієслова "допомагати" (to help). Ви використовуєте її як команду.»

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 95 | «Українська мова розділяє ці концепції.» | «Українська мова розрізняє ці поняття.» | Semantic error (verb + noun) |
| 18 | «Це формальний наказ.» | «Це формальна форма дієслова "допомагати".» | Unclear wording |
| 39 | «Оператори 112 також говорять англійською мовою.» | «Деякі оператори 112 говорять англійською мовою.» | Factual overstatement |
| 37 | «викликати швидку та поліцію на адресу» | «викликати швидку та поліцію за адресою» | Prepositional usage |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? PASS — Good pacing, English scaffolding throughout
- Instructions clear? PASS — Structure is predictable, each subsection has clear purpose
- Quick wins? PASS — Early match-up activity, vocabulary examples with translations
- Ukrainian scary? PASS — Introduced gently with English explanations
- Come back tomorrow? PASS — Encouraging tone, practical scenarios feel useful

## Strengths
- Excellent decolonization framing: the «визивати» Russicism section (lines 117-129) correctly identifies and corrects a genuine colonial linguistic artifact without using Russian as a comparison baseline
- Strong practical scenarios: the 112 call dialogue (lines 181-188) and police document dialogue (lines 200-204) are realistic and useful for A1 learners
- Good verb contrast: the дзвонити/викликати distinction (lines 93-115) with table and warning box is excellent A1 teaching
- Effective rapid-fire drill (lines 263-278) in section «Виробництво та підсумок» builds reflex responses
- Well-constructed vocabulary with 20 items covering all plan requirements

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Line 95: Change «Українська мова розділяє ці концепції.» → «Українська мова розрізняє ці поняття.» — removes confusion
2. Lines 179, 190: Change "Let us" → "Let's" — warmer tutor voice
3. Lines 253-261: Wrap Дія content in `> [!culture]` callout — improves formatting and visual engagement
4. Line 129: Trim "universally understood and preferred by emergency dispatchers across every single region of Ukraine without exception" → "universally understood by dispatchers across Ukraine" — less overwrought

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 95: Fix «розділяє ці концепції» → «розрізняє ці поняття» — semantic correction
2. Line 18: Rewrite «Це формальний наказ.» → «Це формальна форма дієслова "допомагати".» — clearer
3. Line 37: Change «на адресу» → «за адресою» — more standard prepositional usage
4. Line 39: Qualify «Оператори 112 також говорять англійською мовою.» → «Деякі оператори 112 говорять англійською мовою.»

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Lines 74-75, 86: Add pedagogical note that "Поліціє!" is grammatically valid but in practice Ukrainians use «Поліція!» (exclamation) or «Пане офіцере!» (personal address). Keep the paradigm row for reference but mark it as theoretical.
2. Line 35: Nuance the 112 claim — change «У 2023 році міністерство запустило» → «З 2023 року система 112 активно працює по всій Україні.»

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Lines 179, 190: "Let us" → "Let's" (2 occurrences)
2. Line 129: Reduce emphatic prose (see Experience fix above)
3. Line 255: Rewrite «Україна — це дуже сучасна країна.» — generic and flat. Replace with a specific claim: «Україна активно впроваджує цифрові технології у державні послуги.»

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 9.0 + 13.5) / 8.9
= 80.1 / 8.9 = 9.0/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track — no ledger expected)
- Dates checked: 1 (112 launch date — flagged as imprecise, see Issue 4)
- Named figures verified: N/A (no historical figures referenced)
- Primary quotes cross-referenced: N/A
- Chronological sequence: CONSISTENT
- Claims without research grounding: 2 found
  - Line 39: "Оператори 112 також говорять англійською мовою" — research notes do not mention English-speaking operators
  - Line 39: "Система працює навіть з укриття" — research notes do not verify this shelter connectivity claim

## Verification Summary

- Content lines read: 293
- Activity items checked: 72 (across 10 activities)
- Ukrainian sentences verified: 38
- Factual claims verified: 5 (3 confirmed, 2 flagged)
- Issues found: 6

## Verdict

**PASS**

The module is a solid A1 emergency vocabulary lesson with good structure, effective dialogues, and correct decolonization framing. Six issues were found, none triggering auto-fail: one semantic error (розділяє→розрізняє), one pragmatic concern (Поліціє! vocative), two unverified factual claims (English operators, shelter connectivity), one missing [!culture] callout, and some overly formal English prose. All are fixable in a single D.2 pass.

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
failing gates:
lesson: 3051/2000 (raw: 3304) | pedagogy: 1 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 1 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/emergencies-audit.log for details)
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/emergencies.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/emergencies.yaml
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

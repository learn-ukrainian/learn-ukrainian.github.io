# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> **You have file system access.** Use Read and Grep to verify every fix against the actual file content.

---

## Context

A review identified issues in this module. Your job is to produce **exact FIND/REPLACE fix pairs** that resolve the issues. You are NOT writing a review — that was already done. Focus only on producing correct, targeted fixes.

---

## Files You Can Read (use Read tool)

1. **Content**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-and-shopping.md`
2. **Activities**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/food-and-shopping.yaml`
3. **Vocabulary**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/food-and-shopping.yaml`

---

## Review (from Phase D.1)

# Рецензія: Food, Drinks & Shopping

**Reviewed-By:** claude-opus-4-6

**Level:** A1 | **Module:** 18
**Overall Score:** 8.0/10
**Status:** PASS
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PASS (with minor deviations)
- Sections: 4/4 plan sections covered; plan's "Одиниці виміру та граматика" folded into Section «Основні продукти та напої» rather than standalone — acceptable reorganization
- Vocabulary: 6/6 required (хліб, вода, молоко, купувати, їсти, кілограм); 4/6 recommended (missing паляниця, сіль from vocabulary file; both appear in content but not vocab YAML)
- Grammar scope: CLEAN — Accusative (review) + Genitive (formulaic) + Price expressions all within plan scope
- Objectives: 4/4 addressed (order food with Acc, request quantities with Gen, ask prices, distinguish food/drink categories)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm opening with «Вітаємо!» and kitchen imagery; culturally engaging food topic. But no explicit "Today you'll learn..." preview in Ukrainian, and the closing "Congratulations!" is generic rather than listing specific competencies gained. |
| 2 | Coherence | 8/10 | <7 | Logical progression: verbs → Accusative → vocabulary by category → Genitive quantities → shopping dialogues → cultural traditions. Section «Основні продукти та напої» absorbs both product vocabulary AND units/grammar from the plan, making it disproportionately long (~180 lines vs ~40 lines for Section «Українські традиції: хліб і гостинність»). |
| 3 | Relevance | 9/10 | <7 | Food and shopping vocabulary is universally applicable for A1 learners. Direct connection to daily life in Ukraine. Prerequisites (a1-17 Numbers and Money) are properly leveraged for price expressions. |
| 4 | Educational | 8/10 | <7 | Accusative and Genitive rules are presented with clear visual patterns. The "Golden Rule" approach simplifies case learning well. However, introducing TWO grammatical cases plus three full verb paradigms in one module creates high cognitive load for A1. |
| 5 | Language | 8/10 | <8 | Ukrainian is grammatically correct throughout. English explanations are clear and warm. One colonial framing concern in the паляниця [!myth-buster] (line 175: "in Russian, ц is always hard, never palatalized") — mitigated by being in an identity/shibboleth context, but still defines Ukrainian phonology via Russian contrast. |
| 6 | Pedagogy | 8/10 | <7 | PPP structure followed: Present verbs → Present Accusative → Practice with "Я люблю..." → Present vocabulary → Practice dialogues → Produce shopping lists. However, the gap between presentation and first practice opportunity is long — verbs + Accusative + categories before the first interactive exercise. |
| 7 | Immersion | 7/10 | <6 | Pre-computed 25.1%. For A1.2 [Navigation] phase, the tier rubric targets 40-60%. The heavy grammar explanation sections are almost entirely English. Ukrainian appears mostly in examples and vocabulary items rather than in instructional prose. |
| 8 | Activities | 7/10 | <7 | 9 activities with good variety (group-sort, match-up, quiz, fill-in, unjumble). Critical error: Activity 5 "Кількості та продукти" has duplicate right-side item "соку" (paired with both "склянка" and "літр"), making unique matching impossible. Activity 3 quiz items use untaught vocabulary (вранці, зазвичай, міцну, гарячу). |
| 9 | Richness | 8/10 | <6 | Strong cultural hooks: хліб-сіль tradition, паляниця shibboleth, сало as national symbol, борщ UNESCO heritage, коровай and паска. Named Ukrainian dishes and practices give authenticity. Missing richer visual descriptions (the plan mentions "handwritten style visual shopping list" but content just uses a bullet list). |
| 10 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5. Opening «Вітаємо!» with kitchen imagery is welcoming. Grammar is dense but scaffolded with "don't worry" reassurance (line 221). Quick wins via "Я люблю..." sentences. Only concern: high concept density before practice opportunities. |
| 11 | LLM Fingerprint | 7/10 | <7 | «Подивіться на приклади:» appears at lines 60, 109, and 144 — identical example-batching pattern in three consecutive subsections. Section openings «Ми йдемо в магазин» (line 83) and «Ми йдемо за покупками» (line 227) are near-identical. No purple prose or cliché metaphors. |
| 12 | Linguistic Accuracy | 9/10 | <9 | All Ukrainian grammar rules (Accusative: -а→-у, -я→-ю; Genitive: -а→-и, -о→-а) are correct. Verb conjugations for їсти, пити, купувати are accurate. IPA inconsistency: content has «Сік» [sik] (line 155) but vocabulary file has [sʲik]. |
| 13 | Factual Accuracy | 9/10 | <8 | «Хліб — усьому голова» is a genuine proverb. Борщ UNESCO heritage claim is accurate (2022 inscription). Паляниця shibboleth is well-documented. Хліб-сіль tradition accurately described. Сало description is correct. No fabricated claims found. |

**Weighted Overall:**
(8×1.5 + 8×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 7×1.0 + 7×1.3 + 8×0.9 + 8×1.3 + 7×1.0 + 9×1.5 + 9×1.5) / 15.5
= (12 + 8 + 9 + 9.6 + 8.8 + 9.6 + 7 + 9.1 + 7.2 + 10.4 + 7 + 13.5 + 13.5) / 15.5
= 124.7 / 15.5
= **8.0/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN in content. Activity distractors "сока" (activities line 481) and "чая" (activities line 530) are Russian Genitive forms used as intentionally wrong answers — pedagogically questionable for EN→UK direction but not content errors.
- Calques: CLEAN
- Colonial framing: BORDERLINE — Line 175 паляниця [!myth-buster] defines Ukrainian ц via Russian contrast. Falls within the legitimate exception for identity/shibboleth context, but the comparison with Russian is the framing mechanism rather than debunking propaganda.
- Grammar scope: CLEAN — Accusative (review) and Genitive (formulaic) both within plan scope.
- Activity errors: FOUND — duplicate "соку" in match-up Activity 5 (lines 243, 249).
- Beginner safety: 4/5
- Factual accuracy: CLEAN

## Critical Issues Found

### Issue 1: Duplicate Match-Up Target (ACTIVITY_ERROR)
- **Location**: Activities file lines 243 and 249 / Activity "Кількості та продукти"
- **Original**: Both «склянка → соку» and «літр → соку» map to the same right-side value
- **Problem**: In a match-up activity, each right-side item must be unique for the learner to determine a unique correct pairing. Two items mapping to "соку" makes the exercise ambiguous — the learner cannot know which container pairs with which "соку."
- **Fix**: Replace one pair. Change «літр → соку» to «літр → молока» or add a different product (e.g., «літр → води»).

### Issue 2: Structural Monotony — Triple "Подивіться на приклади:" (LLM_FINGERPRINT)
- **Location**: Lines 60, 109, 144 in Section «Вступ: Улюблена їжа та напої» and Section «Основні продукти та напої»
- **Original**: «Подивіться на приклади:» used identically three times as a transition to examples
- **Problem**: Identical example-batching trigger phrase in three consecutive subsections creates robotic monotony. This is a classic LLM structural pattern.
- **Fix**: Vary the transition phrases. Line 60: keep «Подивіться на приклади:». Line 109: change to «Ось кілька прикладів:» (Here are some examples). Line 144: change to «Спробуймо з цими словами:» (Let's try with these words).

### Issue 3: English-Only H3 Header (CONSISTENCY)
- **Location**: Line 289 / Section «У магазині: діалоги та покупки»
- **Original**: «### Ordering with Precision»
- **Problem**: Every other H3 header in the module has a Ukrainian title with English in parentheses (e.g., «### Овочі та Фрукти (Vegetables and Fruits)»). This one breaks the pattern and reduces immersion.
- **Fix**: Change to «### Замовлення з точністю (Ordering with Precision)»

### Issue 4: H1 Heading for Summary (FORMATTING)
- **Location**: Line 338
- **Original**: «# Підсумок»
- **Problem**: Uses H1 heading level, same as the module title. All content sections use H2. This breaks the heading hierarchy.
- **Fix**: Change to «## Підсумок»

### Issue 5: Untaught Vocabulary in Quiz Activity (PEDAGOGY)
- **Location**: Activities file lines 74, 96 / Activity "Дієслова: їсти, пити, купувати"
- **Original**: «Вранці ти зазвичай _____ міцну гарячу каву» (line 74) and «Моя сестра зараз _____ зелений чай з лимоном» (line 96)
- **Problem**: The quiz tests verb conjugation but wraps it in sentences with untaught vocabulary: "вранці" (in the morning), "зазвичай" (usually), "міцну" (strong), "гарячу" (hot), "зелений" (green). A1 learners may be confused by the unknown words and fail to focus on the grammatical point.
- **Fix**: Simplify sentences to use only taught vocabulary. E.g., «Ти _____ каву» or «Ти _____ каву і чай.»

### Issue 6: Ambiguous "кухні" Double-Meaning (BEGINNER_CLARITY)
- **Location**: Line 9 / Section «Вступ: Улюблена їжа та напої»
- **Original**: «Сьогодні ми відкриваємо смачний світ української кухні. Ви на українській кухні.»
- **Problem**: "кухні" appears twice in adjacent sentences with different cases and meanings — first as Genitive ("of cuisine"), then as Locative ("in the kitchen"). At A1, learners haven't mastered case distinctions and may think the same word means two different things without understanding why.
- **Fix**: Rewrite second sentence to avoid repetition: «Ви на кухні.» (You are in the kitchen.) — dropping "українській" to differentiate from the first use.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 155 | «Сік» [sik] | «Сік» [sʲik] | IPA inconsistency (content vs vocabulary file) |
| 289 | «Ordering with Precision» | «Замовлення з точністю (Ordering with Precision)» | Missing Ukrainian header |
| 338 | «# Підсумок» | «## Підсумок» | Heading level error |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — Two grammatical cases is ambitious but the Accusative is review; Genitive is presented formulaically with explicit "don't worry!" reassurance on line 221.
- Instructions clear? **Pass** — English explanations are consistently clear, grammar rules use visual tables, examples follow every rule.
- Quick wins? **Pass** — Section «Вступ: Улюблена їжа та напої» provides «Я люблю суп/борщ/воду/каву» sentences that feel immediately achievable.
- Ukrainian scary? **Pass** — Ukrainian introduced with immediate English translations; glossed vocabulary throughout; familiar international words (банан, лимон, піца) reduce fear.
- Come back tomorrow? **Fail (borderline)** — Food is an engaging topic, but the density of grammar (Accusative + Genitive + 3 verb paradigms + units of measure + dialogues) may leave learners feeling they haven't mastered anything before moving on.

## Strengths
- **Excellent cultural integration**: The bread traditions (хліб-сіль, паляниця, sacred bread) weave culture authentically into vocabulary learning rather than as disconnected sidebars.
- **Clear grammar visualization**: The Accusative "Golden Rule" (masculine/neuter don't change, feminine changes) is an effective simplification for A1.
- **Practical dialogue patterns**: The shopping dialogues in Section «У магазині: діалоги та покупки» provide realistic, reusable templates (Дайте, будь ласка... / Скільки коштує?).
- **Well-targeted callout boxes**: The [!warning] boxes for common errors (Potato Problem, Soup Verb Trap, Politeness Check) preempt real learner mistakes.
- **Strong activity variety**: 5 different activity types across 9 activities, covering receptive (matching, sorting) and productive (fill-in, unjumble) skills.

## Fix Plan to Reach 9/10 (REQUIRED if score < 9.0)

### Activities: 7/10 → 9/10
**What to fix:**
1. Activities line 249: Change «літр → соку» to «літр → води» to eliminate duplicate match-up target
2. Activities lines 63-96: Simplify quiz sentences to use only vocabulary from this module and prerequisites. Remove вранці, зазвичай, міцну, гарячу, зелений from verb conjugation items.

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Line 109: Change «Подивіться на приклади:» to «Ось кілька прикладів:»
2. Line 144: Change «Подивіться на приклади:» to «Спробуймо з цими словами:»

**Expected score after fix:** 8/10

### Immersion: 7/10 → 8/10
**What to fix:**
1. Add Ukrainian transitions between subsections (e.g., before Section «М'ясо та Риба», line 114: add «Тепер поговоримо про м'ясо та рибу.»)
2. Convert some English instructional sentences to bilingual format where the Ukrainian is simple enough for A1.2 (e.g., line 85 "let's fill your virtual shopping basket" → «Наповнімо ваш кошик! — Let's fill your basket!»)

**Expected score after fix:** 8/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Line 338: Change «# Підсумок» to «## Підсумок»
2. Line 289: Change «### Ordering with Precision» to «### Замовлення з точністю (Ordering with Precision)»
3. Add an explicit "Після цього уроку ви зможете..." (After this lesson you'll be able to...) preview after the opening paragraph

**Expected score after fix:** 9/10

### Beginner Safety: 8/10 → 9/10
**What to fix:**
1. Add a brief "checkpoint" encouragement between the Accusative and Genitive sections (around line 176): «Чудово! Ви вже знаєте Знахідний відмінок. Тепер один маленький крок далі...» (Great! You already know the Accusative. Now one small step further...)
2. Add "You can now..." bullets to the Підсумок listing specific competencies

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
Experience: 9, Coherence: 8, Relevance: 9, Educational: 8,
Language: 8, Pedagogy: 8, Immersion: 8, Activities: 9,
Richness: 8, Beginner Safety: 9, LLM: 8, Linguistic: 9, Factual: 9

(9×1.5 + 8×1.0 + 9×1.0 + 8×1.2 + 8×1.1 + 8×1.2 + 8×1.0 + 9×1.3 + 8×0.9 + 9×1.3 + 8×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 8 + 9 + 9.6 + 8.8 + 9.6 + 8 + 11.7 + 7.2 + 11.7 + 8 + 13.5 + 13.5) / 15.5
= 132.1 / 15.5
= 8.5/10
```

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (core A1 track, no research file exists)
- Key Facts Ledger present: NO
- Dates checked: 0 (no dates in content)
- Named figures verified: 0 (no named figures)
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: 0

Callout box verification (all tracks):
- «Хліб — усьому голова» (line 13): Genuine Ukrainian proverb ✓
- Borsch UNESCO heritage (line 329): Verified — inscribed 2022 on Intangible Cultural Heritage list ✓
- Паляниця as shibboleth (line 174-175): Widely documented in media from 2022 ✓
- Salo description (line 131): Accurate cultural description ✓
- Bread-and-salt tradition (lines 311-316): Genuine pan-Slavic tradition, accurately described ✓
- Коровай as wedding bread, паска as Easter bread (line 332): Correct ✓

## Verification Summary

- Content lines read: 350
- Activity items checked: 108 (across 9 activities)
- Ukrainian sentences verified: 45+
- IPA transcriptions checked: 30 (1 inconsistency found: сік [sik] vs [sʲik])
- Factual claims verified: 6
- Issues found: 6

## Verdict

**PASS**

This is a solid A1 food-and-shopping module with strong cultural integration and accurate grammar. The blocking issue is the duplicate "соку" in the match-up activity (Activity 5), which must be fixed for the activity to function. The LLM fingerprint from triple «Подивіться на приклади:» repetition and the untaught vocabulary in quiz items should also be addressed. After these fixes, the module comfortably passes all thresholds.

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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/food-and-shopping.md
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
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/food-and-shopping.yaml
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

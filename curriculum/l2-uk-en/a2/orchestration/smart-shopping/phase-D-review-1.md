**Reviewed-By:** claude-opus-4-6

---

# Phase D.1 Review: smart-shopping (A2-24)

**Module:** Smart Shopping — Comparisons and Choices
**Level:** A2, Sequence 24, Band 2 (60-75% immersion)
**Persona:** Encouraging Cultural Guide / Personal Shopper
**Word count:** 3850 / 3000 (128.3%)
**Activities:** 12 | **Vocabulary:** 25 | **Engagement boxes:** 8

---

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | Language Quality | 8/10 | Ukrainian prose is natural and largely error-free; English grammar explanations are clear. Minor formatting artifacts on lines 214 and 225; "більш хороший" on line 203 is technically valid but highly unnatural. No Russianisms or calques found. |
| 2 | Factual Accuracy | 7/10 | Critical mislabeling of suffix -іш- on line 96 when the first example (солодший) uses -ш-. Superlative claim about Ukrainian e-commerce on line 67 is unverifiable. Grammar rules otherwise correct. |
| 3 | Lesson Quality | 8/10 | "Would I Continue?" 3/5 pass — no warm opening, ~1600 words before first practice opportunity. Structure is solid PPP. Grammar explanations in English are accessible. Market/online scenarios in section «Продукція» are engaging. |
| 4 | Activity Quality | 7/10 | 12 activities with good type variety. Critical bug: activity error-correction item (YAML line 286) contains uncorrected "ближший" which contradicts the stem-change lesson. Internal inconsistency between content (-іш- label) and activities (-ш- label) for солодший. |
| 5 | Richness | 8/10 | Strong cultural hooks ("свій продавець", freshness hierarchy, "бабусі"). Two realistic scenarios (market negotiation + online order). Polite refusal strategies are excellent. Named reference (Нова Пошта). 8 varied callout boxes. |
| 6 | Immersion Balance | 9/10 | 68.7% within Band 2 target (60-75%). English correctly reserved for abstract grammar rules (comparative/superlative formation). Ukrainian used for cultural content, dialogues, and instructions. Good scaffolding. |
| 7 | LLM Fingerprint | 8/10 | Two instances of "це не тільки/лише" pattern (lines 13, 35) — at threshold. Section openings are varied. No structural monotony. Summary opening «У цьому великому та важливому модулі ми вивчили багато нового» (line 306) is slightly generic. Example formatting varies well across sections. |
| 8 | Humanity & Warmth | 7/10 | No warm greeting (no "Привіт!"). Encouragement concentrated at the very end (line 324: «Ви чудово впоралися»). Missing "don't worry" moments in the grammar sections. The [!warning] boxes function more as technical alerts than emotional support. A2 learners need warmth distributed throughout, not back-loaded. |
| 9 | Plan Compliance | 8/10 | All planned sections present. Vocabulary and grammar scope fully covered. Missing: the plan's Підсумок section calls for a "quick recap table of adjective degrees" and a "final checklist for polite shopping interactions" — neither is present. Section «Підсумок» uses H1 instead of H2, breaking document structure. |

---

## Critical Issues Found

### Issue 1: Suffix -іш- vs -ш- Mislabeling (CRITICAL — Factual/Pedagogical Error)

**Location:** Content file, line 96-97

The text on line 96 states: "Let's look at how this works with the suffix **-іш-**, which is the most common and regular pattern:" and then the **first example** is:

Line 97: `соло́дкий — sweet → солодший — sweeter`

**Problem:** `солодший` is formed with the suffix **-ш-** (stem "солод-" + suffix "-ш-" + ending "-ий"), NOT with -іш-. The remaining four examples (важливіший, тепліший, смачніший, новіший) correctly demonstrate -іш-, but the first example contradicts the stated pattern.

The activities file itself correctly identifies this on YAML line 344: «'Солодший' та 'дешевший' утворені за допомогою суфікса -ш-.»

This creates an internal contradiction between the lesson and its own activities. An A2 learner will be confused about which suffix солодший actually uses.

**Fix:** Either (a) move солодкий→солодший to a separate subsection introducing the -ш- suffix first, then proceed to -іш- examples; or (b) remove it from the -іш- list and add a true -іш- example like "корисний → корисніший" instead.

---

### Issue 2: Uncorrected Double Error in Activity (CRITICAL — Activity Bug)

**Location:** Activities YAML, line 286

The error-correction activity contains:
```
sentence: Центральний ринок ближший як наш супермаркет.
error: як
answer: ніж
```

**Problem:** The sentence contains TWO errors: (1) «як» should be «ніж» or «за», AND (2) «ближший» should be «ближчий» per the stem-change rule taught on content line 175 (`близький + ш → ближчий`). The activity only catches «як» and presents «ближший» as correct — directly contradicting the lesson's own stem-change teaching. A learner completing this exercise will internalize «ближший» as correct.

**Fix:** Change the sentence to «Центральний ринок ближчий як наш супермаркет» so that only one error (як) remains, or restructure as two separate items.

---

### Issue 3: Підсумок Uses H1 Instead of H2 (MODERATE — Structural)

**Location:** Content file, line 303

All main sections use `##` (H2): `## Вступ`, `## Презентація`, `## Практика`, `## Продукція`. But section «Підсумок» uses `#` (H1): `# Підсумок`. This breaks the document hierarchy and likely causes parsing/rendering issues in the pipeline.

**Fix:** Change `# Підсумок` to `## Підсумок` on line 303.

---

### Issue 4: Broken Formatting Artifacts in Grammar Explanations (MODERATE — Language Quality)

**Location:** Content file, lines 214 and 225

Line 214: «...remains in its original Nominative case — Nominative case. It does not change its ending.»
Line 225: «...followed by the object of comparison in the Accusative case — Accusative case.»

The "— Nominative case" and "— Accusative case" appear to be broken tooltip/annotation artifacts where the case name is duplicated with a dash separator. This reads as stuttering text to a learner.

**Fix:** Remove the duplicated phrases. Should read: "...remains in the Nominative case" and "...takes the Accusative case".

---

### Issue 5: "більш хороший" Presented as Standard Correct Form (MODERATE — Naturalness)

**Location:** Content file, line 203

The double-comparison table presents «Цей варіант **більш хороший**» as "Правильно (Складена форма)". While technically not a grammar error, "більш хороший" is extremely unnatural in any register of Ukrainian. Native speakers use "кращий" universally. No Ukrainian textbook recommends "більш хороший" as a standard form. Presenting it as a correct alternative will confuse A2 learners who may start producing this awkward construction.

**Fix:** Add a note to the table indicating that for suppletive forms (хороший, поганий, великий, малий), the analytical form with "більш/менш" is strongly avoided in practice. The simple suppletive form is always preferred.

---

### Issue 6: Missing Recap Table and Checklist in Section «Підсумок» (MODERATE — Plan Compliance)

**Location:** Content file, section «Підсумок» (lines 303-324)

The plan explicitly requires:
- "Provide a quick recap table of adjective degrees (comparative and superlative)"
- "Include a final checklist for polite shopping interactions in both physical (bazar) and digital contexts, completely in Ukrainian"

The actual section «Підсумок» has prose summary and self-check questions (lines 305-323) but contains neither a table nor a checklist. The prose summary covers the content well, but the plan-mandated table format would serve as a much better quick reference for learners.

**Fix:** Add a compact table summarizing the degree paradigm (Base → Comparative → Superlative) for 5-6 key adjectives, and a bulleted checklist of shopping phrases for both market and online contexts.

---

### Issue 7: Vocabulary IPA Double Stress (MINOR — Vocabulary)

**Location:** Vocabulary YAML, line 115

The IPA for `важливіший` is `[ʋɑˈʒlɪˈʋʲiʃɪj]` — this contains two primary stress marks (ˈ before ж and before ʋʲ). A single word can only have one primary stress. The correct IPA should be `[ʋɑʒlɪˈʋʲiʃɪj]` with stress on the penultimate syllable.

**Fix:** Remove the first stress mark: `[ʋɑʒlɪˈʋʲiʃɪj]`.

---

### Issue 8: Missing Warm Opening for A2 Learner (MINOR — Humanity/Warmth)

**Location:** Content file, lines 9-13

The module opens with a blockquote philosophical question «Чому це важливо?» followed by dense Ukrainian prose about "складна система соціальної комунікації, культурних традицій та щоденних рішень". There is no personal greeting, no "Привіт!", no "Today you'll learn..." preview.

For A2 Band 2, the learner should feel welcomed before being immersed in abstract cultural discussion. The persona is "Encouraging Cultural Guide" but the opening reads more like a textbook introduction.

**Fix:** Add a warm greeting before the blockquote: "Привіт! Сьогодні ми разом підемо на шопінг — shopping trip! 🛒" (or similar short welcome in Ukrainian with minimal English support), then transition into the philosophical hook.

---

### Issue 9: Unverifiable Superlative Claim (MINOR — Factual Accuracy)

**Location:** Content file, line 67

«Українська система електронної комерції та доставки є однією з найшвидших та найзручніших в Європі.»

While Ukraine's Nova Poshta network is genuinely impressive, claiming it's "one of the fastest and most convenient in Europe" is a superlative claim without sourcing. For A2 learners who may take this at face value, this should either be softened or attributed.

**Fix:** Soften to «Українська система доставки дуже швидка та зручна» or add a qualifying phrase.

---

## Verification Summary

| Check | Result | Notes |
|-------|--------|-------|
| Russianisms | PASS | No Russianisms found. «здачу» correctly flagged as Russicism in error-correction activity (YAML line 318). |
| Colonial framing | PASS | No references to Russian language as baseline. Content presents Ukrainian grammar on its own terms. |
| Grammar scope | PASS | Comparative and superlative degrees (§4.3.1) within A2-24 scope. No scope creep. |
| Word salad | PASS | All paragraphs have clear single points, logical flow. |
| Factual accuracy | PARTIAL FAIL | Suffix -іш- mislabeling (Issue 1). Unverifiable e-commerce claim (Issue 9). |
| Activity correctness | FAIL | Double error in error-correction item (Issue 2). Content/activity inconsistency on suffix labeling. |
| Plan compliance | PARTIAL FAIL | All sections present but missing table/checklist in section «Підсумок» (Issue 6). H1/H2 mismatch (Issue 3). |
| Immersion balance | PASS | 68.7% within Band 2 target range. |
| LLM fingerprint | PASS (borderline) | 2x "це не тільки/лише" at threshold; section openings varied; no monotony. |
| Beginner safety | PARTIAL FAIL | No warm opening. Encouragement back-loaded. ~1600 words before first practice. |

### Section Coverage

| Section | Referenced | Key Finding |
|---------|-----------|-------------|
| Section «Вступ» | Yes | Dense cultural content, missing warm welcome. Good hooks (свій продавець, freshness hierarchy). |
| Section «Презентація» | Yes | Suffix mislabeling issue. Grammar explanations clear in English. Transaction vocabulary well-presented. |
| Section «Практика» | Yes | Stem-change drills solid. Double-comparison table effective but has "більш хороший" issue. Broken formatting on lines 214, 225. |
| Section «Продукція» | Yes | Market dialogue is the module's strongest section — natural, engaging, culturally rich. Online scenario provides good contrast. Polite refusal section excellent. |
| Section «Підсумок» | Yes | H1 structural error. Missing recap table and checklist per plan. Self-check questions are good but prose-heavy. |

---

## Verdict

**REVISE** — Two critical issues (suffix mislabeling in grammar teaching, double error in error-correction activity) directly compromise the pedagogical integrity of the module. Both can be fixed with targeted edits without requiring a rewrite.

**Required fixes before pass:**
1. Fix suffix -іш- vs -ш- categorization for солодкий (content line 96-97)
2. Fix "ближший" to "ближчий" in error-correction activity (YAML line 286)
3. Change `# Підсумок` to `## Підсумок` (content line 303)
4. Fix broken "case — case" formatting (content lines 214, 225)
5. Add note about "більш хороший" being impractical for suppletive forms (content line 203)
6. Fix double stress in важливіший IPA (vocab line 115)

**Recommended fixes (not blocking):**
7. Add recap table and checklist to section «Підсумок»
8. Add warm greeting at module opening
9. Soften e-commerce superlative claim (content line 67)
**Reviewed-By:** claude-opus-4-6

## Scores

| # | Dimension | Score | Evidence Summary |
|---|-----------|-------|------------------|
| 1 | Plan Compliance | 7/10 | Missing "Automation Rhythms / Tiers" subsection from plan; missing 5 required vocabulary pairs; quiz item count far below plan target |
| 2 | Language Quality | 7/10 | Ukrainian grammar generally correct but dialogues severely degraded by excessive A2-inappropriate adverb padding; no Russianisms; no colonial framing |
| 3 | Lesson Quality | 7/10 | Good structure (welcome→present→practice→produce) but bloated dialogues would confuse A2 learners; grammar teaching error at line 263 |
| 4 | Activity Quality | 7/10 | 12 activities with good variety and correct answers; quiz count (8) far below plan requirement (25+); match-up (18) below target (20+) |
| 5 | Immersion | 8/10 | 50.0% measured, target 50-60%; at lower boundary but acceptable for A2 M16 Band 1 |
| 6 | Richness | 8/10 | Two strong cultural hooks (UNESCO borscht, Toloka); decision tree diagram; diverse example contexts; good callout variety |
| 7 | Humanity & Warmth | 7/10 | Direct address and encouragement present; but artificial adverb-stuffed dialogues create stilted LLM feel rather than genuine warmth |
| 8 | LLM Fingerprint | 6/10 | «двигун будь-якої мови» AI cliché; extreme adverb padding in dialogues (амбітно, завбачливо, неймовірно, надзвичайно); structural monotony across dialogue subsections (each uses Definition/How it works/Examples) |
| 9 | Factual Accuracy | 8/10 | UNESCO borscht claim correct (2022); Toloka tradition accurate; but "Я напишу зараз" incorrectly marked as grammatically wrong — it is valid Ukrainian perfective future |
| 10 | Vocabulary Coverage | 6/10 | 19 vocab items but "платити" entry truncated (missing fields); "заплатити" absent; 5 plan-required pairs missing entirely from vocab file |

---

## Critical Issues Found

### Issue 1: Grammar Teaching Error — "Я напишу зараз" Falsely Marked Incorrect (CRITICAL)

**Location:** Line 263 of section «Підсумок»

**Evidence:** The content states:
> «❌ Я напишу зараз. (Incorrect! This means "I will have written right now," which makes no sense.)»

This is **wrong**. «Я напишу зараз» is perfectly valid Ukrainian meaning "I will write it right now" — the perfective future expressing immediate intention. "Зараз" has two meanings: (1) at this moment, (2) right away/shortly. Meaning (2) is fully compatible with perfective future. Additionally, the English translation "I will have written right now" is Present Perfect, not simple future — the correct translation is "I will write (and finish) right now."

**Impact:** This teaches learners that a correct, high-frequency Ukrainian construction is grammatically impossible. An A2 learner who says «Я зараз напишу» to a native speaker will be told it's perfectly fine — destroying trust in the course material.

**Fix:** Replace the ❌ example. Instead of marking «Я напишу зараз» as incorrect, explain the ambiguity: if the learner intends "I am writing right now" (present process), use imperfective «Я пишу зараз»; if the learner intends "I will write it right now" (immediate future result), perfective «Я напишу зараз» is correct. Use a clearly impossible construction like «❌ *Я зараз напишу цю книгу» (implying an ongoing present process that is clearly not instantaneous) or simply focus the trap on the tense label: "If you conjugate напишу, that's FUTURE, not present."

### Issue 2: Vocabulary File Truncated — "платити" Incomplete, "заплатити" Missing

**Location:** Vocabulary file lines 92-93

**Evidence:** The last vocabulary entry is:
```yaml
- lemma: "платити"
  ipa: ''
```
Missing fields: `translation`, `pos`, `aspect`. The perfective pair «заплатити» is completely absent. The file has 19 lemmas but the 10th pair is broken.

**Impact:** Vocabulary file fails schema validation. Learners won't get the complete pair for this high-frequency financial verb.

**Fix:** Complete the "платити" entry and add "заплатити" with all required fields.

### Issue 3: IPA Double Stress on "відповісти"

**Location:** Vocabulary file line 88

**Evidence:** IPA is `''` with two primary stress marks (ˈ). Ukrainian words have exactly one primary stress. The correct IPA is `` with stress on the final syllable.

**Impact:** Incorrect pronunciation guidance. An A2 learner following this IPA would stress two syllables.

**Fix:** Change to `''`.

### Issue 4: Section «Підсумок» Uses H1 Instead of H2

**Location:** Line 252

**Evidence:** `# Підсумок` — all other content sections use H2 (`## Вступ`, `## Презентація`, `## Практика`, `## Діалоги`). The summary section breaks hierarchy by using H1.

**Impact:** Structural inconsistency; may break automated section parsing.

**Fix:** Change `# Підсумок` to `## Підсумок`.

### Issue 5: Mermaid Diagram Not Fenced

**Location:** Lines 39-52 in section «Вступ»

**Evidence:** The decision tree starts directly with `graph TD` without a ````mermaid` code fence. It will render as raw text like:
> graph TD
>     A[What is the nature of the action?] --> B(Happening right now?)

**Impact:** The plan specifically requires a "Visual Decision Tree (Mermaid diagram)" — it won't render as a visual.

**Fix:** Wrap lines 39-52 in ````mermaid` ... ```` fences.

### Issue 6: Severe LLM Adverb Padding in Section «Діалоги» — Unnatural A2 Language

**Location:** Lines 220-249 across all dialogue subsections

**Evidence (verbatim):**
- Line 233: «Коли ви амбітно плануєте повністю побудувати міцні стіни?» — No Ukrainian speaker says "амбітно плануєте"
- Line 235: «Я завбачливо принесу свої професійні інструменти.» — "завбачливо" (foresightedly) is B2+ vocabulary and bizarre in casual neighbor conversation
- Line 235: «Разом ви неймовірно швидко зможете успішно побудувати ваш новий дім.» — Triple adverb chain (неймовірно, швидко, успішно)
- Line 247: «Я дуже часто забуваю такі надзвичайно важливі речі, коли я так багато і важко працюю.» — Over-padded with intensifiers
- Line 248: «Вона постійно і завжди чекає на твій теплий дзвінок.» — "постійно і завжди" is redundant; "теплий дзвінок" is unnatural

The word "дуже" appears **18 times** across the content — nearly once per 200 words.

**Impact:** A2 dialogues should model natural, simple Ukrainian. These read like LLM output inflated to hit word count. Words like «завбачливо», «амбітно», «надзвичайно» are inappropriate for A2 level and would overwhelm learners.

**Fix:** Strip all unnecessary adverbs from dialogues. Example fix for line 233: «Коли ви плануєте побудувати стіни?» Example fix for line 235: «Я принесу свої інструменти.» Target simple, natural speech appropriate for A2 comprehension.

### Issue 7: Missing "Automation Rhythms / Tiers" From Plan

**Location:** Section «Презентація» (lines 56-134)

**Evidence:** The plan's Презентація section requires: *"Automation Rhythms: Grouping pairs by Tiers (1-3) to create auditory anchors and melodic patterns that facilitate faster recall during speech."* This subsection is entirely absent. The content organizes by formation category (prefix/suffix/suppletive) but never groups by frequency tiers.

**Impact:** Plan compliance gap. The tier-based grouping was designed to help learners prioritize which pairs to memorize first.

**Fix:** Add a subsection in «Презентація» grouping pairs into Tier 1 (most frequent: купувати/купити, робити/зробити), Tier 2 (frequent: дзвонити/подзвонити, забувати/забути), Tier 3 (less frequent: ловити/спіймати, вирішувати/вирішити) with a note that Tier 1 pairs should be drilled until automatic.

### Issue 8: Quiz Activity Count Far Below Plan Target

**Location:** Activities file, quiz activity (lines 168-262)

**Evidence:** Plan requires: quiz (15+ items) + quiz (10+ items) = 25+ quiz items total. Actual: 8 quiz items in a single quiz activity. This is 32% of the target.

**Impact:** Insufficient practice for aspect selection speed drills, which is a core objective of the module.

**Fix:** Add a second quiz activity focused on "Identify aspect pair relationship" (10+ items as per plan) and expand the existing quiz to 15+ items.

### Issue 9: Five Required Vocabulary Pairs Missing From File

**Location:** Vocabulary file (entire)

**Evidence:** Plan's `vocabulary_hints.required` specifies 15 pairs. The vocabulary file has 9.5 pairs (19 lemmas, with платити truncated). Missing required pairs:
- продавати/продати
- губити/загубити
- пам'ятати/запам'ятати
- малювати/намалювати
- прибирати/прибрати

**Impact:** Learners won't get structured vocabulary entries (IPA, POS, aspect tags) for 5 plan-required pairs.

**Fix:** Add all 5 missing pairs with complete fields (lemma, ipa, translation, pos, aspect).

---

## Factual Verification

| Claim | Location | Verdict | Notes |
|-------|----------|---------|-------|
| «У 2022 році культура приготування українського борщу була внесена до списку ЮНЕСКО.» | Line 188, section «Практика» | **Correct** | UNESCO inscribed "Culture of Ukrainian borscht cooking" on Intangible Heritage list, July 2022 |
| «Існує понад 100 різних регіональних варіантів.» | Line 188, section «Практика» | **Plausible** | Commonly cited figure in Ukrainian food culture sources |
| Toloka as communal labor tradition for building | Line 207-209, section «Діалоги» | **Correct** | Well-documented Ukrainian tradition of collective voluntary work |
| Grain overnight ritual to test building site | Line 222, section «Діалоги» | **Plausible** | Traditional folk practice, presented appropriately as cultural context |
| «❌ Я напишу зараз.» marked as incorrect | Line 263, section «Підсумок» | **INCORRECT** | This is valid Ukrainian (perfective future with "зараз" = "right away") — see Critical Issue 1 |
| Prefix overgeneralization with "з-" | Lines 77-80, section «Презентація» | **Correct** | Well-documented learner error pattern |
| «буду + perfective = impossible» | Line 130, section «Презентація» | **Correct** | Compound future requires imperfective infinitive |

---

## Verification Summary

### Section Coverage

| Section | Reviewed | Key Findings |
|---------|----------|--------------|
| «Вступ» (lines 14-54) | Yes | Mermaid diagram unfenced; good conceptual framing; adequate English scaffolding |
| «Презентація» (lines 56-134) | Yes | Three formation categories well-presented; missing Automation Rhythms/Tiers subsection; prefix warning box effective |
| «Практика» (lines 135-200) | Yes | Temporal markers well-organized; borscht cultural hook natural and effective; Process/Result correction box good |
| «Діалоги» (lines 202-250) | Yes | Toloka cultural hook good concept; severely degraded by LLM adverb padding; dialogue language unnaturally bloated for A2 |
| «Підсумок» (lines 252-297) | Yes | Grammar teaching error on "Я напишу зараз"; H1/H2 inconsistency; mastery checklist and three rules are effective |

### Auto-Fail Checklist

| Check | Result |
|-------|--------|
| Russianisms | None found |
| Colonial framing | None found |
| Grammar scope violations | None found (stays within aspect pairs scope) |
| Activity errors | None in answers; activity type/count mismatch with plan |
| "Would I Continue?" test | 3/5 — pacing comfortable (pass), instructions clear (pass), quick wins present (pass), Ukrainian introduced gently (FAIL — A2-unfriendly words like завбачливо/амбітно), would come back (borderline — dialogues feel artificial) |
| LLM fingerprint patterns | "двигун будь-якої мови" (AI cliché); structural monotony in dialogue subsections; extreme adverb padding |

### Engagement Box Inventory

| Type | Title/Theme | Quality |
|------|------------|---------|
| [!reflection] | Canvas painting metaphor | Good — accessible analogy |
| [!warning] | Prefix overgeneralization | Good — addresses common error |
| [!tip] | буду + perfective trap | Good — clear rule with examples |
| [!fact] | Process/Result confusion | Good — concrete error correction |
| [!culture] | Ukrainian borscht / UNESCO | Good — authentic cultural hook |
| [!context] | Толока tradition | Good — meaningful cultural context |

No title repetition detected. 6 boxes — adequate variety.

---

## Verdict

**FAIL — Requires D.2 targeted repair.**

**Blocking issues (must fix):**
1. Grammar teaching error: «Я напишу зараз» is valid Ukrainian, not incorrect (line 263)
2. Vocabulary file truncated: "платити" incomplete, "заплатити" missing
3. IPA double stress on "відповісти" in vocabulary
4. Section «Підсумок» H1→H2 fix
5. Mermaid diagram unfenced

**High-priority issues (should fix):**
6. Strip LLM adverb padding from section «Діалоги» — simplify to natural A2 speech
7. Add missing 5 required vocabulary pairs
8. Add quiz items to reach plan target (25+ total)
9. Add "Automation Rhythms / Tiers" subsection to «Презентація»

The module has a solid pedagogical skeleton — the formation taxonomy, temporal marker drills, cultural hooks, and error correction patterns are well-designed. The critical problems are: (a) a factual grammar teaching error that would mislead learners, (b) a severely truncated vocabulary file, and (c) LLM-generated adverb inflation that makes the dialogues unnatural and inappropriate for A2 level. With targeted repairs to these specific areas, this module can reach passing quality.
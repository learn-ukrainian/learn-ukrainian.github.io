# Рецензія: Медична українська: спілкування у сфері охорони здоров'я

**Reviewed-By:** claude-opus-4-6

**Level:** B2 | **Module:** b2-20
**Overall Score:** 8.7/10
**Status:** FAIL
**Reviewed:** 2026-02-25
**Review Type:** D.3 Re-Review (post-D.2 repair, cycle 2)

## D.1 Issue Fix Verification

| # | D.1 Issue | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Incorrect verb «здатися» (original line 222) | FIXED | Grep confirms «здатися» absent from file. Line 232 now reads «звернутися до досвідченого невролога» |
| 2 | IPA stress error «натщесерце» | **NOT FIXED** | Vocab line 145: still `` — correct: ``. This is the second failed attempt to fix this. |
| 3 | Untaught «Біль віддає» in match-up | FIXED | Content line 113 teaches concept with examples; activity match-up at line 711 is now supported |
| 4 | Hyperbolic Amosov prose (stacked epithets) | FIXED | Line 185 reads «видатний український кардіохірург, науковець і письменник» — clean |
| 5 | Missing plan point (complaint form practice) | FIXED | New subsection at line 257 «Практика: як скласти коротку скаргу для цифрової системи» |
| 6 | Superlative doubling at line 41 | FIXED | Grep confirms «наймасштабніших» absent. Line 41 now reads «Одним із найяскравіших прикладів цієї трансформації» |

**D.2 Regressions:** None detected. All 5 successful repairs integrate cleanly without orphaned references or formatting damage.

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: 6/6 present. Minor title variations (unchanged from D.1):
  - Plan: "Медична документація та цифровізація" → Content: "Медична документація та цифровізація суспільства"
  - Plan: "Культура мовлення та корекція русизмів" → Content: "Культура мовлення: корекція суржику та русизмів"
- Vocabulary: 20/20 required covered, 10/10 recommended covered, 0 extra
- Grammar scope: CLEAN — all grammar (noun gender, transitivity, reflexive verbs) is within B2 scope
- Objectives: PASS — both objectives addressed
- Missing plan point: RESOLVED — complaint form practice present at lines 257-273
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong opening hook (lines 10-12) establishes urgency and relevance. Pharmacy culture section (lines 20-37) provides genuinely compelling cultural insight. Amosov section reads naturally after D.2 de-hagiographying. Complaint form template (lines 261-271) adds a practical "quick win". |
| 2 | Coherence | 9/10 | <7 | Logical arc: pharmacy → symptoms → consultation → instructions → documentation → correction. Each section builds on previous vocabulary. D.2 additions (line 113 «Біль віддає», lines 257-273 complaint practice) integrate seamlessly without disrupting flow. |
| 3 | Relevance | 9/10 | <7 | Directly practical for B2 learners living in Ukraine — Helsi.me interface, e-prescription workflow, pharmacist interactions, complaint forms are all real-world needs. Cultural anchors (Amosov, pharmacy culture) are authentic. |
| 4 | Educational | 8/10 | <7 | Section «Опис симптомів та відчуттів» is concept-dense: 5 pain types (lines 86-99), intensity/dynamics vocabulary (lines 107-113), and collocations with «скарга» (lines 115-125) — totaling ~75 lines of content with only [!note] at line 52, [!tip] at line 93, and [!tip] at line 102 as processing breaks. A fourth practice prompt between the pain type definitions (e.g., after line 92 «пульсуючий біль») would improve pacing. Section «Медичні інструкції та філософія Амосова» runs ~600 words of Amosov content (lines 178-199) before the [!tip] at line 201. |
| 5 | Language | 9/10 | <8 | No grammatical errors in teacher prose. Line 61 uses euphemistic «інших слов'янських мов» with explicit Russian mention only in [!decolonization] block (lines 63-64) — acceptable pattern. Euphony rules (у/в alternation) respected throughout. No russianisms in authorial voice. |
| 6 | Pedagogy | 8/10 | <7 | Good TTT for «біль» gender: incorrect examples shown alongside correct ones (lines 68-69) before the rule. TTT for лікувати/лікуватися (lines 142-160) uses contrastive pairs with clear examples before the warning box. However, section «Медичні інструкції та філософія Амосова» is more presentation-heavy: the Amosov biography (lines 185-189) and philosophy (lines 187-197) run ~500 words before the first student prompt at line 191 and [!tip] at line 201. |
| 7 | Immersion | 10/10 | <6 | 98.7% Ukrainian. English appears only in parenthetical translations (e.g., "Transitive verb", "sick leave certificate"). Fully appropriate for B2. |
| 8 | Activities | 9/10 | <7 | 14 activities, 93+ items across 12 types (quiz, fill-in, unjumble, error-correction, true-false, translate, select, match-up, reading ×3, essay-response, group-sort, cloze). D.1 issue with untaught «Біль віддає» resolved. All items checked — distractors are pedagogically targeted (e.g., gender errors, russianisms, collocation violations). Minor: match-up «Гострий біль» (line 709) described as «Дуже сильний та раптовий дискомфорт, який важко терпіти» partially overlaps with ріжучий біль but is not blocking. |
| 9 | Richness | 9/10 | <6 | 11 callout boxes ([!culture] ×2, [!decolonization] ×1, [!warning] ×3, [!tip] ×3, [!note] ×1, [!quote] ×1). Comparison table (lines 302-309). Clinical examples throughout. Helsi.me and Amosov as cultural anchors. Complaint form template (lines 261-271). Varied formatting: dialogues, bullet lists, tables, blockquotes. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Content appropriately challenging for B2 — medical register is inherently complex but explanations are clear. Quick wins: pharmacy dialogue (lines 28-32) is immediately relatable. Warning boxes anticipate confusion (e.g., line 72 on «біль» gender, line 160 on лікувати/лікуватися). Complaint form template gives concrete tool for immediate use. |
| 11 | LLM Fingerprint | 8/10 | <7 | Superlative doubling at line 41 fixed. Section openings are all varied and distinct (verified: lines 16, 55, 129, 178, 224, 277 — no structural monotony). No "це не просто" patterns. Remaining: line 185 «стала беззаперечним бестселером» — «беззаперечним» is an unnecessary intensifier typical of LLM prose. Line 189 «щоденна, дуже інтенсивна, виснажлива розминка» — triple adjective stacking. Both are minor. No callout title repetition. |
| 12 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL.** IPA stress error in vocabulary persists after two repair cycles: «натщесерце» at vocab line 145 still marked ``. Correct Ukrainian stress is натщесе́рце → ``. The stress marker ˈ must be moved from before t͡ʃt͡ʃ to before sɛr. No other IPA errors found across remaining 29 vocabulary items (spot-checked: діа́гноз `` ✓, обсте́ження `` ✓, тупи́й `` ✓, фармаце́вт `` ✓). |
| 13 | Factual Accuracy | 9/10 | <8 | Amosov facts verified against research notes: кардіохірург ✓, Київ ✓, «Роздуми про здоров'я» ✓, «1000 рухів» ✓, «система обмежень і навантажень» ✓. Helsi.me description accurate (e-prescriptions via SMS, electronic declarations). E-prescription workflow matches current Ukrainian practice. [!culture] box at line 183 claims Amosov institute named after him — Національний інститут серцево-судинної хірургії імені М. М. Амосова exists ✓. No fabricated claims found in any callout box. |

**Weighted Overall:** (9×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 9×1.1 + 8×1.2 + 10×1.0 + 9×1.3 + 9×0.9 + 9×1.3 + 8×1.0 + 8×1.5 + 9×1.5) / 15.5 = (13.5 + 9.0 + 9.0 + 9.6 + 9.9 + 9.6 + 10.0 + 11.7 + 8.1 + 11.7 + 8.0 + 12.0 + 13.5) / 15.5 = 135.6 / 15.5 = **8.7/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — Content actively teaches against russianisms (приймати участь, осмотр). No accidental russianisms in teacher prose.
- Calques: [CLEAN] — No calques found in teacher language.
- Grammar scope: [CLEAN] — All grammar (noun gender, transitivity, reflexive verbs) is within B2 scope.
- Activity errors: [CLEAN] — Previously untaught «Біль віддає» now taught in content at line 113.
- Beginner safety: 5/5
- Factual accuracy: [CLEAN] — All factual claims verified against research notes.
- Colonial framing: [CLEAN] — Line 61 uses euphemistic «інших слов'янських мов» with explicit Russian mention only in [!decolonization] block (line 64). Acceptable pattern.
- **Linguistic Accuracy: [FAIL]** — IPA stress error in vocabulary persists (unfixed after two D.2 cycles).

## Critical Issues Found

### Issue 1: Unfixed IPA Stress Error — «натщесерце» (Linguistic Accuracy — AUTO-FAIL)
- **Location**: Vocabulary file, line 145
- **Original**: `ipa: ''`
- **Problem**: Stress marker ˈ placed before t͡ʃt͡ʃ (first consonant cluster). The correct Ukrainian stress is натщесе́рце — stress on the penultimate syllable «сер». This was flagged in the original D.1 review and again in the D.3 re-review, but D.2 has failed to apply this fix in both repair cycles. The fix is trivial: move the ˈ character from before t͡ʃt͡ʃ to before sɛr.
- **Fix**: Change `ipa: ''` to `ipa: ''`

### Issue 2: LLM-Typical Hyperbolic Qualifier in Section «Медичні інструкції та філософія Амосова» (LLM Fingerprint — Minor)
- **Location**: Line 185 / Section «Медичні інструкції та філософія Амосова»
- **Original**: «стала беззаперечним бестселером»
- **Problem**: The qualifier «беззаперечним» (indisputable) is an unnecessary intensifier. A real Ukrainian teacher would simply say the book was a bestseller. Stacking «мільйонними тиражами» + «беззаперечним бестселером» in the same clause is characteristic of LLM writing.
- **Fix**: Change «видана мільйонними тиражами, стала беззаперечним бестселером» to «видана мільйонними тиражами і стала бестселером».

### Issue 3: Triple Adjective Stacking in Section «Медичні інструкції та філософія Амосова» (LLM Fingerprint — Minor)
- **Location**: Line 189 / Section «Медичні інструкції та філософія Амосова»
- **Original**: «щоденна, дуже інтенсивна, виснажлива розминка»
- **Problem**: Three adjectives stacked before one noun. Natural Ukrainian would use fewer modifiers or restructure.
- **Fix**: Simplify to «щоденна інтенсивна розминка» — removing «дуже» and «виснажлива» which add little meaning beyond what «інтенсивна» already conveys.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| vocab:145 | `` | `` | IPA stress |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass — Medical register is complex but explanations break it down with clinical examples
- Instructions clear? Pass — Each concept explained with context and examples before rules
- Quick wins? Pass — Pharmacy dialogue (lines 28-32) and complaint form template (lines 261-271) provide immediate practical tools
- Ukrainian scary? Pass — Callout boxes and practice prompts ([!tip] boxes) guide without overwhelming
- Come back tomorrow? Pass — Content is engaging with cultural hooks (pharmacy culture, Amosov philosophy, Helsi.me)

## Strengths

- **Pharmacy culture section** (lines 20-37): Genuinely insightful cultural content about the unique role of Ukrainian pharmacists as primary consultants — this is practical knowledge that textbooks rarely cover.
- **Complaint form template** (lines 261-271): A concrete, immediately usable tool added in D.2 that transforms abstract lesson content into practical skill.
- **Contrastive analysis of лікувати vs лікуватися** (lines 140-160): Excellent pedagogical structure with clear subject/object analysis and practical examples, followed by a warning box at line 160 that anticipates the most common mistake.
- **Decolonization handling** (lines 61-64): Presents «біль» gender as an inherent Ukrainian feature with the Russian contrast appropriately contained in a [!decolonization] callout.
- **відділ vs відділення** section (lines 234-247): The «хірургічний відділ» analogy at line 247 is memorable and pedagogically effective.

## Fix Plan to Reach 9.0/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Vocabulary file line 145: Change `ipa: ''` → `ipa: ''` — Move stress marker to correct syllable.

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Line 185: Change «видана мільйонними тиражами, стала беззаперечним бестселером» → «видана мільйонними тиражами і стала бестселером» — Remove unnecessary intensifier.
2. Line 189: Change «щоденна, дуже інтенсивна, виснажлива розминка» → «щоденна інтенсивна розминка» — Reduce adjective stacking.

**Expected score after fix:** 9/10

### Educational: 8/10 → 9/10
**What to fix:**
1. After line 92 (end of «пульсуючий біль» clinical example) in section «Опис симптомів та відчуттів»: Add one [!tip] practice prompt asking the learner to describe a specific pain scenario using the three types just learned. This breaks up the 5 pain types into two groups of 3+2 with practice between them.

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. In section «Медичні інструкції та філософія Амосова», between the Amosov biography (line 185) and the «система обмежень і навантажень» explanation (line 187): The think-first prompt at line 191 is good, but comes ~400 words into the Amosov narrative. Consider moving or duplicating a brief reflection prompt earlier (e.g., after line 186 "популяризував цілу цілісну, струнку філософську систему") to encourage active processing.

**Expected score after fix:** 8.5/10 (marginal improvement; 9/10 would require restructuring)

### Projected Overall After Fixes
```
Experience: 9 × 1.5 = 13.5
Coherence: 9 × 1.0 = 9.0
Relevance: 9 × 1.0 = 9.0
Educational: 9 × 1.2 = 10.8
Language: 9 × 1.1 = 9.9
Pedagogy: 8.5 × 1.2 = 10.2
Immersion: 10 × 1.0 = 10.0
Activities: 9 × 1.3 = 11.7
Richness: 9 × 0.9 = 8.1
Beginner Safety: 9 × 1.3 = 11.7
LLM Fingerprint: 9 × 1.0 = 9.0
Linguistic Accuracy: 9 × 1.5 = 13.5
Factual Accuracy: 9 × 1.5 = 13.5

Projected = 139.9 / 15.5 = 9.0/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (research notes are structured as vocabulary/cultural hooks/errors)
- Dates checked: 0 (no specific historical dates in content)
- Named figures verified: 1 (Микола Амосов — кардіохірург, Київ, «Роздуми про здоров'я», «1000 рухів», «система обмежень і навантажень» — all match research notes)
- Primary quotes cross-referenced: 1/1 matched (Амосов quote at line 194 matches research cultural hooks section)
- Chronological sequence: N/A (no historical narrative)
- Claims without research grounding: 0 found
- Callout box verification: All 11 callout boxes checked — no fabricated claims. [!culture] at line 183 claims Національний інститут серцево-судинної хірургії named after Amosov — verified.

## Verification Summary

- Content lines read: 332
- Activity items checked: 93+ (across 14 activities)
- Ukrainian sentences verified: 40+
- IPA transcriptions checked: 30/30 (all vocabulary items)
- Factual claims verified: 8 (Amosov facts, Helsi.me, e-prescription workflow, [!culture] boxes)
- Issues found: 3 (1 critical — IPA stress; 2 minor — LLM fingerprint)

## Verdict

**FAIL**

Single blocking issue: IPA stress error on «натщесерце» in vocabulary file (line 145) persists after two D.2 repair cycles. The fix is trivial — move stress marker from `` to `` — but it triggers the Linguistic Accuracy auto-fail gate (<9). All other D.1 issues (5 of 6) were successfully repaired with no regressions detected. Content quality is high; once the IPA fix lands, the module should pass.
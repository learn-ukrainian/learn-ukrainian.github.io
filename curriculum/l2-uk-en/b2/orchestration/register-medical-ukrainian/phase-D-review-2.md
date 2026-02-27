# Рецензія: Медична українська: спілкування у сфері охорони здоров'я

**Reviewed-By:** claude-opus-4-6

**Level:** B2 | **Module:** b2-20
**Overall Score:** 8.7/10
**Status:** FAIL
**Reviewed:** 2026-02-25
**Review Type:** D.3 Re-Review (post-D.2 repair)

## D.1 Issue Fix Verification

| # | D.1 Issue | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Incorrect verb «здатися» (line 222) | FIXED | Line 226 now reads «звернутися до досвідченого невролога» — Grep confirms «здатися» absent from file |
| 2 | IPA stress error «натщесерце» | **NOT FIXED** | Vocab line 145: still `` — correct: `` |
| 3 | Untaught «Біль віддає» in match-up | FIXED | Concept added to content at line 109 under Section «Опис симптомів та відчуттів» |
| 4 | Hyperbolic Amosov prose (stacked epithets) | FIXED | Line 181 simplified to «видатний український кардіохірург, науковець і письменник» |
| 5 | Missing plan point (complaint form practice) | FIXED | New subsection at line 251 «Практика: як скласти коротку скаргу для цифрової системи» |

**D.2 Regressions:** None detected. All repairs are clean and well-integrated.

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: 6/6 present. Minor title variations (unchanged from D.1):
  - Plan: "Медична документація та цифровізація" → Content: "Медична документація та цифровізація суспільства"
  - Plan: "Культура мовлення та корекція русизмів" → Content: "Культура мовлення: корекція суржику та русизмів"
- Vocabulary: 20/20 required covered, 10/10 recommended covered, 0 extra
- Grammar scope: CLEAN — no grammar from later modules
- Objectives: PASS — both objectives addressed
- Missing plan point: NOW RESOLVED — complaint form practice added at lines 251-267
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong opening hook (lines 10-12) establishes urgency. Pharmacy culture section is culturally compelling. Amosov section (now de-hagiographied) reads naturally. |
| 2 | Coherence | 9/10 | <7 | Logical progression: pharmacy→symptoms→consultation→instructions→documentation→correction. New additions (line 109 «Біль віддає», lines 251-267 complaint practice) integrate seamlessly without disrupting flow. |
| 3 | Relevance | 9/10 | <7 | Highly practical for B2 learners in Ukraine — Helsi.me, e-prescriptions, pharmacist interactions are real-world needs. Complaint form practice (new) adds direct applicability. |
| 4 | Educational | 8/10 | <7 | Excellent grammar focus (біль gender, лікувати/лікуватися). Section «Опис симптомів та відчуттів» remains content-heavy: 5 pain types + intensity/dynamics + collocations (lines 82-119) with only one [!tip] practice box at line 98 breaking the flow. Could benefit from one more integrated practice checkpoint after the pain types (line 96). |
| 5 | Language | 9/10 | <8 | D.1 verb error fixed. No new grammatical errors detected. Line 61 uses «інших слов'янських мов» as euphemism — acceptable with the explicit [!decolonization] block at line 63-64. Euphony respected throughout. |
| 6 | Pedagogy | 8/10 | <7 | Good TTT elements for біль (rule after examples) and лікувати/лікуватися (contrastive analysis). Section «Медичні інструкції та філософія Амосова» improved but still ~600 words of Amosov biography/philosophy (lines 174-193) before the [!tip] at line 195. The new complaint practice section (lines 251-267) improves pedagogy for Section «Медична документація та цифровізація суспільства». |
| 7 | Immersion | 10/10 | <6 | 98.7% Ukrainian. English appears only in parenthetical translations. Fully appropriate for B2. |
| 8 | Activities | 9/10 | <7 | 14 activity types, 93+ items. D.1 issue with untaught «Біль віддає» resolved — concept now taught at line 109. Minor: match-up item «Гострий біль» (activity line 709) described as «Дуже сильний та раптовий дискомфорт, який важко терпіти» somewhat overlaps with ріжучий біль description in content. Not blocking. |
| 9 | Richness | 9/10 | <6 | 11 callout boxes (culture ×2, decolonization ×1, warning ×3, tip ×3, note ×1, quote ×1), comparison table (lines 296-303), clinical examples throughout, Helsi.me and Amosov as cultural anchors. Complaint form template (lines 255-265) adds practical variety. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5 — Content is appropriately challenging for B2. Clear explanations with practical examples. Well-signposted with callouts. New complaint form practice gives quick win. |
| 11 | LLM Fingerprint | 8/10 | <7 | D.1 stacked epithets fixed (line 181). Remaining: line 41 «найяскравіших, наймасштабніших прикладів» — superlative doubling. No "це не просто" patterns. Section openings are all varied and distinct. No structural monotony. |
| 12 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL.** IPA stress error in vocabulary: «натщесерце» at line 145 still marked as `` — correct stress is натщесе́рце → ``. D.2 failed to apply this fix. No other IPA errors found across 30 vocabulary items. |
| 13 | Factual Accuracy | 9/10 | <8 | Amosov facts verified: кардіохірург, Київ, "Роздуми про здоров'я", "1000 рухів", "система обмежень і навантажень" — all consistent with research notes. Helsi.me description accurate. E-prescription system description matches current Ukrainian practice. All callout boxes verified for plausibility — no fabrications. |

**Weighted Overall:** (9×1.5 + 9×1.0 + 9×1.0 + 8×1.2 + 9×1.1 + 8×1.2 + 10×1.0 + 9×1.3 + 9×0.9 + 9×1.3 + 8×1.0 + 8×1.5 + 9×1.5) / 15.5 = (13.5 + 9 + 9 + 9.6 + 9.9 + 9.6 + 10 + 11.7 + 8.1 + 11.7 + 8 + 12 + 13.5) / 15.5 = 135.6 / 15.5 = **8.7/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — Content actively teaches against russianisms (приймати участь, осмотр). No accidental russianisms in teacher prose.
- Calques: [CLEAN] — No calques found in teacher language.
- Grammar scope: [CLEAN] — All grammar (noun gender, transitivity, reflexive verbs) is within B2 scope.
- Activity errors: [CLEAN] — Previously untaught «Біль віддає» now taught in content.
- Beginner safety: 5/5
- Factual accuracy: [CLEAN] — All factual claims verified against research notes.
- Colonial framing: [CLEAN] — Line 61 uses euphemistic «інших слов'янських мов» in main prose, with explicit Russian mention only in [!decolonization] block (line 64). Acceptable pattern.
- **Linguistic Accuracy: [FAIL]** — IPA stress error in vocabulary persists (unfixed from D.1).

## Critical Issues Found

### Issue 1: Unfixed IPA Stress Error — «натщесерце» (Linguistic Accuracy — AUTO-FAIL)
- **Location**: Vocabulary file, line 145
- **Original**: `ipa: ''`
- **Problem**: Stress marker ˈ placed before t͡ʃt͡ʃ (second syllable). The correct Ukrainian stress is натщесе́рце — stress on the penultimate syllable «сер». This was flagged in D.1 review but D.2 failed to apply the fix.
- **Fix**: Change to `ipa: ''`

### Issue 2: Superlative Doubling (LLM Fingerprint — Minor)
- **Location**: Line 41 / Section «Вступ: Медичний регістр та культура аптеки»
- **Original**: «Одним із найяскравіших, наймасштабніших прикладів цієї трансформації»
- **Problem**: Two superlative adjectives stacked together — a common LLM-generated pattern. Natural Ukrainian would typically use one superlative or rephrase.
- **Fix**: Simplify to «Одним із найяскравіших прикладів цієї трансформації» (remove «наймасштабніших»).

### Issue 3: Content-Heavy Section Without Practice Break (Pedagogy)
- **Location**: Lines 82-96 / Section «Опис симптомів та відчуттів»
- **Original**: Five pain types (ниючий, ріжучий, пульсуючий, розпираючий, тупий) presented sequentially over ~500 words with clinical examples, before a single [!tip] at line 98.
- **Problem**: Learner processes 5 new concept clusters without any practice checkpoint. The [!tip] at line 98 comes after all five types, not between them.
- **Fix**: Insert a brief practice prompt after the first 2-3 pain types (e.g., after line 91: «Спробуйте: Який тип болю ви б відчули після удару об двері — ниючий, ріжучий чи пульсуючий?»).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| vocab:145 | `` | `` | IPA stress |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass — Content is dense but well-signposted with 11 callout boxes.
- Instructions clear? Pass — All grammar explanations include explicit rules and examples.
- Quick wins? Pass — Pharmacy culture opening is engaging and immediately applicable.
- Ukrainian scary? Pass — New complaint form practice (lines 251-267) gives concrete template to follow.
- Come back tomorrow? Pass — Teacher voice is warm, practical, and encouraging throughout.

## Strengths

- **D.2 repairs are clean**: Verb fix at line 226, Amosov prose simplification at line 181, and «Біль віддає» addition at line 109 all integrate seamlessly with surrounding text. No orphaned references or formatting damage.
- **New complaint form practice section** (lines 251-267) is practical, well-templated, and directly addresses the plan requirement. The template/example format is pedagogically effective.
- **Strong cultural grounding**: The pharmacy culture section (Section «Вступ: Медичний регістр та культура аптеки») and Amosov section (Section «Медичні інструкції та філософія Амосова») provide authentic Ukrainian context that goes beyond generic medical vocabulary.
- **Excellent activity suite**: 14 activity types with comprehensive coverage. The cloze passage (activity lines 798-914) is particularly strong — it tells a coherent medical journey story.
- **Effective decolonization handling**: Ukrainian medical terminology presented on its own terms in main prose, with Russian contrast limited to [!decolonization] callout (line 63-64).

## Fix Plan to Reach 9.0/10 (REQUIRED — current score 8.7)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Vocabulary line 145: Change `ipa: ''` → `ipa: ''` — corrects stress placement to натщесе́рце.

**Expected score after fix:** 9/10 (single remaining fix, no other IPA or linguistic errors)

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Line 41: Change «Одним із найяскравіших, наймасштабніших прикладів» → «Одним із найяскравіших прикладів» — eliminates superlative doubling.

**Expected score after fix:** 9/10

### Educational: 8/10 → 9/10
**What to fix:**
1. After line 91 (end of пульсуючий біль section): Insert a mini-practice prompt to break up the 5 pain types, e.g., «Спробуйте: Уявіть, що у вас болить зуб — який тип болю ви б описали лікареві?»

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. In Section «Медичні інструкції та філософія Амосова», after line 186 (end of навантаження description) and before the [!quote]: Insert a brief comprehension check, e.g., «Як ви думаєте: чому Амосов вважав, що сучасний комфорт робить нас слабшими? Подумайте про це перед тим, як прочитаєте його відповідь.»

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.0 + 9×1.0 + 9×1.2 + 9×1.1 + 9×1.2 + 10×1.0 + 9×1.3 + 9×0.9 + 9×1.3 + 9×1.0 + 9×1.5 + 9×1.5) / 15.5
= (13.5 + 9 + 9 + 10.8 + 9.9 + 10.8 + 10 + 11.7 + 8.1 + 11.7 + 9 + 13.5 + 13.5) / 15.5
= 140.5 / 15.5
= 9.1/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track — research notes have vocabulary frequency, cultural hooks, common errors)
- Dates checked: N/A — no historical dates in content
- Named figures verified: 1 (Микола Амосов) — facts match research notes (кардіохірург, Київ, "Роздуми про здоров'я", "1000 рухів", "система обмежень і навантажень")
- Primary quotes cross-referenced: 1/1 matched — Amosov quote at line 188 matches research notes
- Chronological sequence: N/A
- Claims without research grounding: 0 found
- Callout boxes checked: 11/11 — all factually plausible, no fabrications

## Verification Summary

- Content lines read: 326
- Activity items checked: 93+ (across 14 activity types)
- Ukrainian sentences verified: 40+
- IPA transcriptions checked: 30/30 (1 error: натщесерце)
- Factual claims verified: 8
- D.1 issues verified: 5/5 (4 fixed, 1 unfixed)
- D.2 regressions found: 0
- Issues found: 3 (1 critical — IPA unfixed, 2 minor)

## Verdict

**FAIL**

The module remains in FAIL status due to a single blocking issue: the IPA stress error for «натщесерце» (vocab line 145) was flagged in D.1 but not fixed by D.2, triggering the Linguistic Accuracy auto-fail gate (<9). This is a trivial one-character fix (`ˈ` position shift). The other four D.1 issues were properly resolved with no regressions. Once the IPA stress is corrected, the module should comfortably pass.
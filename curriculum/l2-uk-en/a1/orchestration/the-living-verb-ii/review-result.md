**Reviewed-By:** claude-opus-4-6

# Рецензія: The Living Verb II

**Level:** A1 | **Module:** 16
**Overall Score:** 7.1/10
**Status:** FAIL
**Reviewed:** 2026-03-19

## Plan Verification

```
Plan-Content Alignment: PASS (with minor gaps)
- Sections: 4/4 present (Вступ, Презентація, Практика, Продукування)
- Vocabulary: 8/8 required present in prose, 4/4 recommended present
- Grammar scope: PASS — no scope creep detected
- Objectives: 4/4 addressed
```

**Plan Adherence Checklist (content_outline.points):**

**Section "Вступ: Тріада гостинності (Introduction: The Triad of Hospitality)":**
- Introduction to Second Conjugation as second pillar: COVERED — Line 3: 「Today, we are exploring the second pillar of Ukrainian verbal action: the Second Conjugation.」
- Cultural Motivator — Hospitality Triad (їсти, пити, говорити): COVERED — Line 5: 「їсти (to eat), пити (to drink), and говорити (to speak)」
- Concept check (imperfective review): COVERED — Line 7 discusses "doing" vs "completing" and anchors to prior knowledge.

**Section "Презентація: Моделі та мутації (Presentation: Paradigms and Mutations)":**
- Systematic endings + side-by-side comparison: COVERED — Lines 17-24 table shows читати vs говорити.
- State Standard §4.2.4.1 сидіти model: COVERED — Line 31: 「сидіти (to sit)」 with mutation pattern.
- Labial L phonetic framing: COVERED — Lines 38-42 explain physical rationale.
- Irregularity of їсти: COVERED — Lines 44-56 with dedicated table and error examples.
- бачити vs дивитися distinction: COVERED — Lines 58-64.

**Section "Практика: Помилки та автоматизація (Practice: Errors and Automation)":**
- Contrastive drills (conjugation mixing): COVERED — Line 73: 「For example, a learner might say *ти робеш*. This is entirely incorrect!」
- Mutation mastery drills: COVERED — Lines 84-87.
- Sorting exercises: COVERED — Lines 89-93.

**Section "Продукування та культурний контекст (Production and Cultural Context)":**
- Contextual production collocations: COVERED — Lines 109-112.
- Etymology of любити: COVERED — Line 115: 「It comes from the ancient Proto-Indo-European root *\*lewdh-*」
- Social ethics of hospitality: COVERED — Lines 119-122.

**Activity hints:**
- fill-in (conjugation): COVERED — activity 1 (8 items) + activity 3 (6 items)
- match-up (verb sorting): COVERED — activity 2 (10 pairs)
- fill-in (mutated forms): COVERED — activity 3 specifically targets я-forms with mutations

**Vocabulary required:** All 8 required verbs (говорити, робити, бачити, любити, їсти, пити, ходити, просити) appear in prose AND at least one activity. ✅

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Warm hospitality framing but NO callout boxes, no encouragement markers, abrupt Підсумок. Missing "You can now..." celebration beats. |
| 2 | Language | 8/10 | <8 | Ukrainian grammar is correct throughout. Collocations at lines 110-112 use untaught cases (instrumental/accusative) but as fixed phrases — acceptable. No Russianisms. |
| 3 | Pedagogy | 8/10 | <7 | Strong PPP structure, excellent error-correction approach. Missing explicit warning that пити is NOT 2nd conjugation despite -ити ending. |
| 4 | Activities | 8/10 | <7 | 6 activities, good variety (fill-in, match-up, group-sort, quiz, true-false). All items verified correct. Missing activity that produces full sentences. |
| 5 | Beginner Safety | 7/10 | <7 | "Would I Continue?" 3/5 — no quick wins before dense grammar, no encouragement phrases, no "don't worry" moments. Content is warm but lacks explicit emotional safety markers. |
| 6 | LLM Fingerprint | 8/10 | <7 | No structural monotony. Sections open differently. No "це не просто" patterns. One minor flag: "Let's" opener used 4x (lines 13, 31, 75, 115) but varied enough. |
| 7 | Linguistic Accuracy | 8/10 | <9 | Missing critical note that пити is 1st conjugation (п'ю, п'єш), not 2nd — a learner following this module would reasonably assume it's 2nd conjugation. Error examples (їджу, робеш, etc.) correctly marked as incorrect. |

**Weighted Overall:** (7×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 7×1.3 + 8×1.0 + 8×1.5) / 8.9 = (10.5 + 8.8 + 9.6 + 10.4 + 9.1 + 8.0 + 12.0) / 8.9 = 68.4 / 8.9 = **7.7/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no instances found
- Calques: [CLEAN]
- Colonial framing: [CLEAN] — no "unlike Russian" comparisons
- Grammar scope: [MINOR] — accusative/instrumental in collocations (lines 110-112) pre-date their teaching module, but presented as fixed chunks
- Activity errors: [CLEAN] — all forms verified against VESUM
- Beginner safety: 3/5 (see below)
- Factual accuracy: [ISSUE] — пити misclassified by omission (see Critical Issue 3)

## Critical Issues Found

### Issue 1: Zero Engagement Boxes (AUDIT GATE FAILURE)
- **Location**: Whole module
- **Problem**: The module contains zero `> [!tip]`, `> [!example]`, `> [!cultural-note]`, `> [!did-you-know]` or similar callout boxes. The audit requires minimum 1 for A1. Richness is 57% (threshold 60%) — engagement boxes are the missing dimension. The blockquotes at lines 33-35 and 40-42 are plain `>` blockquotes, not Obsidian-style callouts.
- **Fix**: Add at least 2 callout boxes: one `> [!tip]` for the "golden rule" about и vowels (near line 26), and one `> [!cultural-note]` for the hospitality triad (near line 5 or lines 119-122). Also add one `> [!example]` with a mini-dialogue using the hospitality verbs.

### Issue 2: Підсумок Uses H1 Instead of H2
- **Location**: Line 124: 「# Підсумок」
- **Problem**: All other sections use `##` (H2). The summary uses `#` (H1), breaking the document structure hierarchy. The plan doesn't list Підсумок as a separate section, and it shouldn't outrank the main H2 sections.
- **Fix**: Change `# Підсумок` to `## Підсумок`.

### Issue 3: пити Silently Grouped with 2nd Conjugation
- **Location**: Section "Вступ: Тріада гостинності (Introduction: The Triad of Hospitality)", line 5, and section "Продукування та культурний контекст (Production and Cultural Context)", line 112
- **Problem**: The module introduces пити as part of the Hospitality Triad alongside 2nd conjugation verbs (їсти, говорити) but never warns that пити is actually 1st conjugation (п'ю, п'єш, п'є — uses є, not и). VESUM confirms: п'ю, п'єш, п'є, п'ємо, п'єте, п'ють — all 1st conjugation forms. A learner following this module would reasonably try to conjugate *я пию, *ти пиїш — nonexistent forms. The builder notes identify this friction but the content doesn't address it.
- **Fix**: Add an explicit warning box near line 112 or in section "Презентація: Моделі та мутації (Presentation: Paradigms and Mutations)": "Despite ending in -ити, пити is actually a First Conjugation verb: п'ю, п'єш, п'є. Don't be fooled by the infinitive ending!"

### Issue 4: No Encouragement or Emotional Safety Markers
- **Location**: Whole module
- **Problem**: Zero explicit encouragement phrases ("Great!", "You've got this!", "Don't worry"), zero "don't worry" moments, and zero "You can now..." validation markers. The Beginner Safety rubric requires ≥3 encouragement phrases, ≥2 "don't worry" moments, and ≥2 validation markers. The closest the module gets is "Are you ready to join the table?" (line 9), which is inviting but not encouraging.
- **Fix**: Add at minimum: (1) one encouragement phrase after the first table (line 25-26), (2) one "don't worry" moment near the mutation section (line 29), (3) "You can now..." celebration in Підсумок.

### Issue 5: Immersion Below Target Band
- **Location**: Whole module
- **Problem**: Audit shows 8.3% immersion. Module 16 falls in the "Modules 11-20: 25-45% Ukrainian" band. At 8.3%, the module is far below the minimum 25% target. Most Ukrainian appears only in bold vocabulary words and tables, with almost all prose in English.
- **Fix**: Add Ukrainian mini-dialogues or Reading Practice blocks after sections "Презентація: Моделі та мутації (Presentation: Paradigms and Mutations)" and "Продукування та культурний контекст (Production and Cultural Context)". Example: a short dialogue of a guest arriving at a Ukrainian home using the hospitality triad verbs. This would boost immersion while reinforcing the cultural theme.

### Issue 6: D.0 Morphological Violations — Collocations with Untaught Cases
- **Location**: Lines 110-112 in section "Продукування та культурний контекст (Production and Cultural Context)"
- **Original**: 「говорити українською」(instrumental), 「любити природу」(accusative), 「пити каву」(accusative)
- **Problem**: D.0 flags instrumental and accusative forms not taught until M25. These are standard collocations presented as fixed phrases, which is pedagogically defensible at A1. However, the module doesn't signal these as "learn as a chunk" — a learner might try to analyze the case ending.
- **Fix**: PARTIALLY DISMISS. Add a brief note: "Learn these as fixed phrases for now — we'll explore the grammar behind the word endings in a later module." This addresses the D.0 flag without removing essential collocations.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 56 | 「*я їджу* or *я їстю*」 | N/A — correctly marked as errors | Error example (OK) |
| 73 | 「*ти робеш*」 | N/A — correctly marked as error | Error example (OK) |
| 77-79 | 「*ти бачеш*」「*він ходе*」「*ми просемо*」 | N/A — correctly marked as errors | Error examples (OK) |
| 112 | пити treated as 2nd conjugation by context | Add explicit 1st conjugation warning | Misclassification by omission |

All error examples are correctly marked with italics (*) as incorrect forms — this is good pedagogy. No Russianisms detected. No calques detected.

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? **Pass** — pacing is reasonable, grammar is introduced in manageable chunks with tables
- Instructions clear? **Pass** — always clear what to learn, tables are well-organized
- Quick wins? **Fail** — 500+ words of content before first activity reference; no inline mini-exercises
- Ukrainian scary? **Pass** — Ukrainian introduced gently with translations throughout
- Come back tomorrow? **Fail** — no encouragement phrases, no celebration, abrupt ending without warmth

## Strengths
- **Excellent error pedagogy**: The module explicitly shows common errors (їджу, робеш, просемо) and corrects them — this is exactly what real Ukrainian teachers do (contrastive drilling).
- **Strong cultural framing**: The Hospitality Triad is an engaging, memorable hook that gives vocabulary emotional resonance.
- **Correct linguistics**: All conjugation tables are accurate. The mutation explanations (д→дж, labial+л, с→ш, т→ч) are correct and well-sequenced.
- **Activity variety**: 6 activities across 5 types (fill-in ×2, match-up, group-sort, quiz, true-false) — good variety for reinforcement.
- **Etymology of любити**: The PIE root connection to люди is factually grounded and pedagogically memorable.

## Fix Plan to Reach 9/10 (REQUIRED — score is 7.7)

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Add 2-3 `> [!tip]`, `> [!cultural-note]`, `> [!example]` callout boxes — solves engagement=0 audit gate
2. Line 124: Change `# Підсумок` to `## Підсумок`
3. Add "You can now..." celebration in Підсумок
4. Add a mini-dialogue in Ukrainian using hospitality verbs (boosts immersion + engagement + experience)

**Expected score after fix:** 9/10

### Beginner Safety: 7/10 → 9/10
**What to fix:**
1. Add ≥3 encouragement phrases (after table at line 25, after mutation section ~line 42, after practice section ~line 87)
2. Add ≥1 "don't worry" moment near mutations (~line 29: "Don't worry — this pattern is very consistent once you see it a few times")
3. Add "You can now..." validation in Підсумок

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Add explicit пити warning — this verb is 1st conjugation (п'ю, п'єш), not 2nd, despite -ити ending. Place near the Hospitality Triad introduction or as a `> [!tip]` callout.
2. Add "learn as fixed phrases" note for collocations at lines 109-112

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 8.8 + 9.6 + 10.4 + 11.7 + 8.0 + 13.5) / 8.9
= 75.5 / 8.9 = 8.5/10
```

To reach 9.0+, Pedagogy and Activities would also need polish (add inline practice earlier, add a sentence-building activity), but the immediate priority is the 3 failing dimensions above.

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track)
- Dates checked: N/A
- Named figures verified: N/A
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: 0
- Etymology of любити (PIE *lewdh-): Consistent with research notes line 13. ✅
- пити as 1st conjugation: Confirmed by VESUM (п'ю, п'єш, п'є). Research notes line 15 say "Regular -ити verb" which is misleading — it's regular but 1st conjugation.

## Verification Summary

- Content lines read: 135
- Activity items checked: 46 (8 fill-in + 10 match-up + 6 fill-in + 12 group-sort + 6 quiz + 8 true-false — minus 4 duplicate quiz items = 46 unique checks)
- Ukrainian sentences verified: 24 (all table entries + blockquote examples + error examples)
- Citations in bank: 25
- Issues found: 6

## Verdict

**FAIL**

Three blocking issues: (1) **Zero engagement boxes** — audit gate failure requiring at minimum 1 callout box. (2) **пити misclassification by omission** — learners will assume it's 2nd conjugation, producing nonexistent forms. (3) **Immersion at 8.3%** vs 25% minimum for M16 — module needs Ukrainian dialogues or reading practice blocks. Fix plan is concrete and achievable in one rebuild pass.
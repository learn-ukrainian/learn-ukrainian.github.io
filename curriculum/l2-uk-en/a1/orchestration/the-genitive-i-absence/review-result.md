# Рецензія: The Genitive I: Absence

**Level:** A1 | **Module:** 31
**Overall Score:** 7.4/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-6

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: ALL 5 sections present as H2 ✅
- Vocabulary: 13/13 required+recommended words present in prose ✅
- Grammar scope: CLEAN — no scope creep ✅
- Objectives: ALL 4 objectives addressed ✅
- Activity items: FAIL — 24/51 items delivered (plan: 25+20+6=51, actual: 10+8+6=24)
```

### Plan Adherence Checklist

**Section "Вступ (Introduction)":**
- Contrast є vs немає: COVERED — Lines 3, 11-14 contrast existence vs absence with examples 「У ме́не нема́є квитка́.」
- Learner Error не vs немає: COVERED — Lines 5-9 explicitly explain the distinction with examples

**Section "Презентація (Presentation)":**
- немає + genitive set phrases: COVERED — Lines 22-24 with 「У ме́не нема́є ча́су.」 and 「У ме́не нема́є гроше́й.」
- без + genitive collocations: COVERED — Lines 28-31 with кава без цукру, вода без газу, їхати без квитка
- Masculine ending systematization -а/-я vs -у/-ю: COVERED — Lines 33-48 with clear split and 「нема́є телефо́на」 semantic example

**Section "Практика (Practice)":**
- Case Neglect minimal pairs: COVERED — Lines 55-59 with 「Є квито́к. — Нема́є квитка́.」
- Nom → Gen transformations for feminine: COVERED — Lines 61-63 with вода → води, проблема → проблеми
- Roleplay at restaurant: COVERED — Lines 65-73 with full dialogue including 「На жаль, хлі́ба нема́є.」

**Section "Культурний контекст (Cultural Context)":**
- Немає проблем + polite refusal: COVERED — Lines 77-82 with 「Нема́є пробле́м!」 and 「На жаль, квиткі́в нема́є.」
- Proverb: COVERED — Line 85 with 「Нема́є ди́му без вогню́.」

**Section "Займенники у родовому (Pronouns in Genitive)":**
- Personal pronouns in genitive: COVERED — Line 93 lists all forms
- н- rule after prepositions: COVERED — Lines 97-100 with examples 「У ньо́го нема́є ча́су.」

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good lesson arc (welcome→present→practice→celebrate) but no callout boxes, and the Підсумок is an H1 not H2 breaking formatting |
| 2 | Language | 7/10 | <8 | Wrong stress on ме́не (should be мене́, appears 5 times); register issue in café dialogue — 「Що ви хо́чете?」 should be 「Що бажа́єте?」 in service context |
| 3 | Pedagogy | 8/10 | <7 | Clear PPP structure, good minimal pairs; but pacing dumps all masculine endings at once (lines 35-48) before practice |
| 4 | Activities | 6/10 | <7 | Only 24/51 items vs plan (10/25, 8/20, 6/6); all 3 activities are fill-in — no type variety; цукра is a VESUM-failed distractor |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5 — warm tone throughout, but no callout boxes for encouragement or tips |
| 6 | LLM Fingerprint | 8/10 | <7 | Minor structural monotony — several sections open with "Let us..." pattern; otherwise good variety |
| 7 | Linguistic Accuracy | 8/10 | <9 | Wrong stress ме́не (×5), VESUM-failed цукра in activities, register mismatch in dialogue |

**Weighted Overall:** (8×1.5 + 7×1.1 + 8×1.2 + 6×1.3 + 8×1.3 + 8×1.0 + 8×1.5) / 8.9 = (12 + 7.7 + 9.6 + 7.8 + 10.4 + 8.0 + 12.0) / 8.9 = 67.5 / 8.9 = **7.6/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN — no Russian ghost words detected
- Calques: MEDIUM — 「Що ви хо́чете?」 (line 67) is an Anglicism/register mismatch in café context. Natural Ukrainian service: 「Що бажа́єте?」
- Grammar scope: CLEAN — all grammar stays within A1 genitive scope
- Activity errors: FAIL — цукра (activity distractor) is NOT a valid Ukrainian word form per VESUM. Used as wrong distractor in 3 activity items (lines 19, 56, 89 of activities YAML)
- Beginner safety: 4/5
- Factual accuracy: CLEAN — proverb 「Нема́є ди́му без вогню́.」 is genuine; cultural claims about Немає проблем are accurate

## Critical Issues Found

### Issue 1: Wrong Stress on мене (HIGH — Linguistic Accuracy)
- **Location**: Lines 14, 23, 24, 93, 94 / Sections "Вступ (Introduction)", "Презентація (Presentation)", "Займенники у родовому (Pronouns in Genitive)"
- **Original**: 「ме́не」 (5 occurrences)
- **Problem**: The stress dictionary confirms мене́ (stress on second syllable) is the correct form. ме́не with stress on first syllable is wrong. This is a pronoun learners will use constantly — teaching wrong stress is critical.
- **Fix**: Replace all occurrences of ме́не with мене́

### Issue 2: VESUM-Failed Distractor цукра in Activities (HIGH — Activities)
- **Location**: Activities YAML lines 19, 56, 89
- **Original**: `options: ["цукор", "цукру", "цукром", "цукра"]`
- **Problem**: цукра is NOT a valid Ukrainian word form (confirmed by VESUM: NOT FOUND). Students should not practice choosing between options where one distractor is a non-existent form. This fails the ACTIVITY_VESUM_FAIL gate.
- **Fix**: Replace цукра with цукрі (locative, valid form) or цукру (duplicate — better: цукрові as dative alternative)

### Issue 3: Activity Item Shortfall vs Plan (HIGH — Activities)
- **Location**: Activities YAML, all three activities
- **Original**: Activity 1 has 10 items (plan: 25), Activity 2 has 8 items (plan: 20)
- **Problem**: Only 24 of 51 planned activity items were delivered (47%). This is a massive shortfall that undermines the drilling purpose of the module. The plan specifies high item counts precisely because genitive endings require extensive drilling.
- **Fix**: Rebuild activities with full item counts per plan specification (25, 20, 6)

### Issue 4: Zero Engagement Boxes (MEDIUM — Experience Quality)
- **Location**: Entire module — all sections
- **Problem**: The module has 0 callout boxes (`[!tip]`, `[!example]`, `[!cultural-note]`, etc.). Audit requires minimum 1 for A1. Callout boxes provide visual variety, quick wins, and encouragement moments crucial for beginners.
- **Fix**: Add at minimum: 1× `[!tip]` in section "Презентація (Presentation)" about the -а/-у semantic split, 1× `[!cultural-note]` in section "Культурний контекст (Cultural Context)" around the proverb

### Issue 5: Register Mismatch in Café Dialogue (MEDIUM — Language)
- **Location**: Line 67 / Section "Практика (Practice)"
- **Original**: 「До́брий день! Що ви хо́чете?」
- **Problem**: In Ukrainian service contexts (café, restaurant), a server would naturally say 「Що бажа́єте?」 not 「Що ви хо́чете?」. The A1 calibration explicitly flags this as an Anglicism. "Що ви хочете?" sounds blunt/rude from a server in Ukrainian culture.
- **Fix**: Change to 「Що бажа́єте?」 with a brief note that this is the polite service form

### Issue 6: Підсумок Uses H1 Instead of H2 (LOW — Experience Quality)
- **Location**: Line 102
- **Original**: `# Підсумок`
- **Problem**: All other sections use H2 (`##`). The summary uses H1, breaking the heading hierarchy. This will cause rendering issues in the Starlight site.
- **Fix**: Change to `## Підсумок`

### Issue 7: Low Immersion (11.5% vs 30-55% target) (MEDIUM — Pedagogy)
- **Location**: Entire module
- **Problem**: Module 31 falls in the A1 band 21+ which targets 30-55% Ukrainian immersion. At 11.5%, the module is far under. The English prose is clear and warm, but there are opportunities for more Ukrainian text — additional example sentences, a reading practice block, or Ukrainian-only mini-dialogues.
- **Fix**: Add a Reading Practice block (5-8 Ukrainian sentences) after section "Практика (Practice)" and expand Ukrainian examples in sections "Презентація (Presentation)" and "Займенники у родовому (Pronouns in Genitive)"

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 14 | 「У ме́не нема́є квитка́.」 | 「У мене́ нема́є квитка́.」 | Stress error |
| 23 | 「У ме́не нема́є ча́су.」 | 「У мене́ нема́є ча́су.」 | Stress error |
| 24 | 「У ме́не нема́є гроше́й.」 | 「У мене́ нема́є гроше́й.」 | Stress error |
| 93 | 「ме́не」 | 「мене́」 | Stress error |
| 94 | 「Без ме́не.」 | 「Без мене́.」 | Stress error |
| 67 | 「Що ви хо́чете?」 | 「Що бажа́єте?」 | Register/Anglicism |

### D.0 Pre-Screen Disposition

1. **[STRESS_MISMATCH] ме́не → мене́**: CONFIRMED — wrong stress, 5 occurrences
2. **[STRESS_UNKNOWN] гроше́й**: DISMISSED — VESUM confirms грошей is valid gen.pl. of гроші; stress on е́й is standard
3. **[STRESS_UNKNOWN] гро́ші**: DISMISSED — standard nominative plural stress
4. **[STRESS_UNKNOWN] телефо́на**: DISMISSED — VESUM confirms телефона is valid gen.sg.; stress on о́ is standard
5. **[STRESS_MISMATCH] його́ → йо́го**: DISMISSED — його́ (stress on second syllable) is the standard genitive of він per SUM and VESUM. The suggestion йо́го appears incorrect.
6. **[STRESS_UNKNOWN] ньо́го**: DISMISSED — valid prepositional variant of його, stress is standard
7. **[STRESS_UNKNOWN] її́**: DISMISSED — valid genitive of вона, stress is standard
8. **[LOW_ENGAGEMENT]**: CONFIRMED — 0 engagement boxes, minimum 1 required
9. **[ACTIVITY_VESUM_FAIL] цукра**: CONFIRMED — цукра is NOT a valid Ukrainian word form

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — pacing is comfortable, concepts introduced gradually
- Instructions clear? **Pass** — always clear what to do, English scaffolding present
- Quick wins? **Pass** — minimal pairs on line 56 give immediate "I can do this" feeling
- Ukrainian scary? **Pass** — introduced gently with translations throughout
- Come back tomorrow? **Fail** — no callout boxes for encouragement, no celebratory moments until very end; the closing (line 111 "Keep up the fantastic work!") is warm but section "Практика (Practice)" and "Займенники у родовому (Pronouns in Genitive)" feel dry without visual breaks

## Strengths
- **Excellent semantic split explanation** (lines 45-48): The телефо́на vs телефо́ну distinction is a gem — clear, memorable, immediately useful
- **Strong minimal pairs drill** (lines 55-59): 「Є квито́к. — Нема́є квитка́.」 — exactly what the plan calls for, effective pedagogy
- **Natural dialogue** (lines 67-72): The café ordering scene feels authentic and provides real-world context
- **Well-structured proverb integration** (line 85): 「Нема́є ди́му без вогню́.」 elegantly demonstrates both немає and без in one sentence
- **Warm, encouraging tone** throughout — the tutor voice is consistent and supportive

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Activities: 6/10 → 8/10
**What to fix:**
1. Rebuild Activity 1 to have 25 items per plan (currently 10)
2. Rebuild Activity 2 to have 20 items per plan (currently 8)
3. Replace цукра distractor with valid form (цукрові or цукрів) in all 3 activity files
4. Consider adding a match-up or quiz activity type for variety (plan only specifies fill-in, but variety aids learning)

**Expected score after fix:** 8/10

### Language: 7/10 → 9/10
**What to fix:**
1. Fix all 5 occurrences of ме́не → мене́ (lines 14, 23, 24, 93, 94)
2. Change 「Що ви хо́чете?」 → 「Що бажа́єте?」 on line 67

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Same stress fixes as Language above
2. Fix цукра distractor in activities

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add 2 callout boxes: `[!tip]` in section "Презентація (Presentation)" and `[!cultural-note]` in section "Культурний контекст (Cultural Context)"
2. Fix `# Підсумок` → `## Підсумок` on line 102

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add a Reading Practice block (5-8 Ukrainian sentences) after section "Практика (Practice)" to boost immersion from 11.5% toward 30%
2. Add more Ukrainian examples in section "Займенники у родовому (Pronouns in Genitive)" (currently only 3 examples for 8 pronoun forms)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 8×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 10.4 + 10.4 + 8.0 + 13.5) / 8.9
= 76.5 / 8.9 = 8.6/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not applicable — core track)
- Dates checked: N/A (no historical dates)
- Named figures verified: N/A
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: 0
- Proverb verified: 「Нема́є ди́му без вогню́.」 confirmed in research notes as genuine Ukrainian proverb ✅
- Cultural claim "Немає проблем!" as hospitality marker: confirmed in research notes ✅
- Grammar rules (masculine -а/-у split): cross-referenced with RAG textbook search — Grade 6 Avramenko p.100 confirms the rule ✅

## Verification Summary

- Content lines read: 111
- Activity items checked: 24 (all items in all 3 activities)
- Ukrainian sentences verified: 28
- Citations in bank: 17
- Issues found: 7

## Verdict

**FAIL**

Blocking issues: (1) Wrong stress on мене́ appears 5 times — teaching incorrect pronunciation of a core pronoun is a critical linguistic accuracy failure. (2) Activity item count is 47% of plan target (24/51) — massive shortfall undermines the drilling purpose. (3) VESUM-failed distractor цукра appears in 3 activity items. (4) Zero engagement boxes fails the audit gate. Issues 1, 3, and 4 are fixable with targeted edits; issue 2 requires activity rebuild.
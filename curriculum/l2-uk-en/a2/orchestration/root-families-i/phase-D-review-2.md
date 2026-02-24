# Рецензія: Root Families I: The DNA of Vocabulary

**Reviewed-By:** claude-opus-4-6

**Level:** A2 | **Module:** 41
**Overall Score:** 8.1/10
**Status:** FAIL
**Reviewed:** 2026-02-23

## D.3 Re-Review: D.1 Fix Verification

| D.1 Issue | Status | Evidence |
|-----------|--------|----------|
| IPA [ʍxʲid] for вхід | **NOT FIXED** | Vocab line 9 still reads `ipa: '[ʍxʲid]'` |
| Plokhy described as novelist | **FIXED** | Line 204 now reads «новий роман Сергія Жадана» — real fiction writer |
| Broken comma syntax line 44 | **FIXED** | Line 49 now reads «регулярний рух пішки, який повторюється» — comma removed |
| Untaught обачний tested in 3 activities | **FIXED** | Line 117 now introduces обачний with etymology and example |
| Orphaned English filler paragraphs (4 blocks) | **PARTIALLY FIXED** | 3 of 4 remain — lines 89, 128, 235 |
| Off-scope розклад quiz item | **FIXED** | розклад now only a distractor (incorrect option) |
| "Це не просто" x2 LLM fingerprint | **FIXED** | Pattern no longer found in content |
| Cold opening, no greeting | **FIXED** | Line 10: "Привіт! Welcome to your first word-building module." |

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: 5/5 present (Вступ, Родини ход- та пис-, Родини чит- та бач-, Фонетика та префікси, Практичне застосування)
- Vocabulary: 29 items in vocabulary file; Big Four roots covered; розклад included as conceptual expansion
- Grammar scope: PASS — stays within root families, prefixes, aspectual pairs, euphony rule
- Objectives: 4/4 addressed (identify roots, guess derivatives, build words, recognize professional roots)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm opening with "Привіт!" at line 10; excellent Quick Win box at line 23; strong bookstore dialogue at line 202; 3 orphaned English paragraphs (lines 89, 128, 235) still break lesson flow; `# Підсумок` uses H1 instead of H2 (line 240) |
| 2 | Language | 8/10 | <8 | Clean Ukrainian throughout; minor tautology at line 49 «регулярний рух пішки, який повторюється» — "регулярний" already implies repetition; orphaned English blocks at lines 89, 128, 235 disconnect from Ukrainian flow but are individually correct |
| 3 | Pedagogy | 8/10 | <7 | обачний now properly taught at line 117 before testing — D.1 fix verified; slight theory frontloading in section «Вступ» offset by Quick Win at line 23; PPP structure intact across all sections |
| 4 | Activities | 9/10 | <7 | 12 varied activity types — excellent range; all items align with taught content; розклад fixed to distractor-only; cloze library passage (line 349) is outstanding contextual practice |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5; warm greeting ✓, quick wins ✓, clear instructions ✓, Ukrainian not scary ✓; come back tomorrow 4/5 (orphaned English blocks at lines 89, 128 are jarring mid-lesson) |
| 6 | LLM Fingerprint | 8/10 | <7 | "Це не просто" and "In this module, we will explore" removed ✓; section openings vary ✓; residual formulaic phrasing: «Це слово чудово показує, як логічна лінгвістична структура може створювати дуже емоційну та романтичну лексику.» (line 125); callout box types varied (tip, warning, culture, observe, fact, myth-buster) |
| 7 | Linguistic Accuracy | 8/10 | <9 | **IPA error unfixed**: вхід transcribed as [ʍxʲid] using non-Ukrainian phoneme ʍ (vocab line 9); IPA stress missing on сходити [sxɔdɪtɪ] (vocab line 116); IPA stress misplaced on передбачити [pɛrɛˈdbɑt͡ʃɪtɪ] (vocab line 93) — mark before [d] instead of before [b] |

**Weighted Overall:**
```
(8×1.5 + 8×1.1 + 8×1.2 + 9×1.3 + 8×1.3 + 8×1.0 + 8×1.5) / 8.9
= (12.0 + 8.8 + 9.6 + 11.7 + 10.4 + 8.0 + 12.0) / 8.9
= 72.5 / 8.9
= 8.1/10
```

**AUTO-FAIL TRIGGER**: Linguistic Accuracy 8/10 < 9 threshold

## Auto-Fail Checklist Results

- Russianisms: CLEAN — no Russian calques detected
- Calques: CLEAN
- Colonial framing: CLEAN — no Russian comparisons found
- Grammar scope: CLEAN — stays within root families and aspect
- Activity errors: CLEAN — all items properly aligned after D.2 fixes
- Beginner safety: 4/5
- Factual accuracy: CLEAN — Plokhy removed; Zhadan is a real Ukrainian fiction writer
- **AUTO-FAIL TRIGGER**: Linguistic Accuracy 8/10 < 9 threshold (IPA [ʍxʲid] unfixed)

## Critical Issues Found

### Issue 1: UNFIXED — IPA Error on вхід Using Non-Ukrainian Phoneme
- **Location**: Vocabulary file line 9
- **Original**: `ipa: '[ʍxʲid]'` for lemma "вхід"
- **Problem**: This is the same error flagged in D.1 that D.2 failed to repair. The symbol ʍ represents a voiceless labial-velar approximant (found in some Scottish English dialects for "wh"). This phoneme does not exist in the Ukrainian phonological inventory. The в in вхід before voiceless х is realized as labiodental [ʋ] or approximant [w], never as [ʍ].
- **Fix**: Change to `ipa: '[ʋxʲid]'`

### Issue 2: IPA Missing Stress Mark on сходити
- **Location**: Vocabulary file line 116
- **Original**: `ipa: '[sxɔdɪtɪ]'`
- **Problem**: No stress mark present. Every polysyllabic vocabulary entry should have stress marked. The correct stress is on the second syllable: схо-ДИ-ти.
- **Fix**: Change to `ipa: '[sxɔˈdɪtɪ]'`

### Issue 3: IPA Stress Misplacement on передбачити
- **Location**: Vocabulary file line 93
- **Original**: `ipa: '[pɛrɛˈdbɑt͡ʃɪtɪ]'`
- **Problem**: The stress marker ˈ is positioned before [d], placing it at an impossible syllable boundary. The syllabification is пе-ред-БА-чи-ти, with stress on the third syllable [bɑ].
- **Fix**: Change to `ipa: '[pɛrɛdˈbɑt͡ʃɪtɪ]'`

### Issue 4: Three Orphaned English Paragraphs Remain
- **Location**: Lines 89, 128, 235
- **Original (line 89)**: "Beyond physical movement, the **-ход-** root extends into abstract language. The word **підхід** literally means "approach"..." — appears after the entire пис- family discussion, abruptly returning to ход- content
- **Original (line 128)**: "The root **-бач-** also underlies words about mutual understanding..." — mixes бач- and чит- commentary in one orphaned block after the full Ukrainian section «Родини чит- та бач-»
- **Original (line 235)**: "When you meet a familiar root with an unfamiliar prefix, read the whole sentence for clues..." — orphaned at end of section «Практичне застосування»
- **Problem**: These English blocks are disconnected from their surrounding Ukrainian context. They break lesson flow and were flagged in D.1 but only partially addressed.
- **Fix**: Line 89 → move into the ход- H3 subsection (after line 46). Line 128 → split: бач- sentence into the бач- H3, чит- sentence into the чит- H3. Line 235 → integrate into the "Створення власних мереж слів" subsection at line 231.

### Issue 5: H1 Header for Summary Section
- **Location**: Line 240
- **Original**: `# Підсумок`
- **Problem**: All content sections use H2 (`## Вступ`, `## Родини ход- та пис-`, etc.), but the closing summary uses H1. This creates a structural inconsistency — the summary appears as a peer to the module title rather than a content section.
- **Fix**: Change to `## Підсумок`

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 49 | «регулярний рух пішки, який повторюється» | «регулярний рух пішки» | Tautology — "регулярний" already implies repetition |
| 125 | «Це слово чудово показує, як логічна лінгвістична структура може створювати дуже емоційну та романтичну лексику.» | «Це слово показує, як логіка мови створює романтичну лексику.» | Verbose/formulaic for A2 |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — comfortable pacing, English scaffolding for theory
- Instructions clear? **Pass** — "Today you'll learn" preview, clear section headers
- Quick wins? **Pass** — excellent [!tip] Quick Win box at line 23
- Ukrainian scary? **Pass** — introduced gently with translations throughout
- Come back tomorrow? **Borderline** — orphaned English blocks at lines 89 and 128 mid-lesson create awkward discontinuity that may confuse a beginner about lesson structure

## Strengths

- **Excellent activity quality**: 12 activities across 10 different types with strong contextual integration; the cloze library passage (activity line 349) is pedagogically outstanding
- **обачний fix well-executed**: Line 117 introduces the word with clear etymology and a natural example «Будь обачним на дорозі!» before it appears in activities
- **Zhadan replacement appropriate**: Line 204 now correctly names a real Ukrainian fiction writer
- **Strong cultural hooks**: писанка etymology (line 65), побачення as "mutual seeing" (lines 119-125), and читацький квиток cultural note (line 109-110) are authentic and engaging
- **Bookstore dialogue** (lines 204-209): Natural, contextual, uses 5 target vocabulary items organically

## Fix Plan to Reach 9/10 (REQUIRED — score is 8.1)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Vocabulary line 9: Change `ipa: '[ʍxʲid]'` → `ipa: '[ʋxʲid]'` — removes non-Ukrainian phoneme
2. Vocabulary line 116: Change `ipa: '[sxɔdɪtɪ]'` → `ipa: '[sxɔˈdɪtɪ]'` — adds missing stress mark
3. Vocabulary line 93: Change `ipa: '[pɛrɛˈdbɑt͡ʃɪtɪ]'` → `ipa: '[pɛrɛdˈbɑt͡ʃɪtɪ]'` — corrects stress placement

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Line 89: Move English paragraph about підхід into the ход- H3 subsection after line 46
2. Line 128: Split бач-/чит- English paragraph — integrate each part into its respective H3
3. Line 235: Integrate practical English tip into the word network subsection at line 231
4. Line 240: Change `# Підсумок` → `## Підсумок`

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 49: Remove tautological «який повторюється» — the word "регулярний" already conveys this
2. Line 125: Simplify «Це слово чудово показує, як логічна лінгвістична структура може створювати дуже емоційну та романтичну лексику.»

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 8×1.2 + 9×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 9.6 + 11.7 + 10.4 + 8.0 + 13.5) / 8.9
= 76.6 / 8.9
= 8.6/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track)
- Dates checked: N/A (no specific historical dates claimed)
- Named figures verified: 1 — Сергій Жадан (line 204) is a real Ukrainian fiction writer ✓
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: 0
- Etymology claims: 3 verified (Proto-Slavic *pьsati* line 65, *čisti* line 95, Greek *hodos* line 44) — all consistent with research notes

## Verification Summary

- Content lines read: 254
- Activity items checked: 78 (across 12 activities)
- Ukrainian sentences verified: 45+
- IPA transcriptions checked: 29 (all vocabulary items)
- Factual claims verified: 6
- Issues found: 5 (1 unfixed from D.1, 2 new IPA issues, 1 structural, 1 flow)

## Verdict

**FAIL**

Single blocking issue: IPA error on вхід (vocabulary line 9) using non-Ukrainian phoneme [ʍ] was not repaired by D.2 despite being explicitly flagged as Critical Issue #1 in D.1. This triggers the Linguistic Accuracy < 9 auto-fail. Additionally, two new IPA issues (missing stress on сходити, misplaced stress on передбачити) and three orphaned English paragraphs remain unresolved. All five issues are straightforward FIND/REPLACE fixes — a single D.2 pass should clear them.
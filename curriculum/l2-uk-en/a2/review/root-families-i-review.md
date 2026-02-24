<!-- content-hash: 41b99b985552 -->
# Рецензія: Root Families I: The DNA of Vocabulary

**Reviewed-By:** claude-opus-4-6

**Level:** A2 | **Module:** 41
**Overall Score:** 8.2/10
**Status:** FAIL
**Reviewed:** 2026-02-23

## D.3 Re-Review: D.1 Fix Verification

| D.1 Issue | Status | Evidence |
|-----------|--------|----------|
| IPA [ʍxʲid] for вхід | **NOT FIXED** | Vocab line 9 still reads `ipa: '[ʍxʲid]'` — non-Ukrainian phoneme ʍ persists |
| IPA missing stress on сходити | **NOT FIXED** | Vocab line 116 still reads `ipa: '[sxɔdɪtɪ]'` — no stress mark |
| IPA stress misplaced on передбачити | **NOT FIXED** | Vocab line 93 still reads `ipa: '[pɛrɛˈdbɑt͡ʃɪtɪ]'` — mark before [d] not [b] |
| Orphaned English paragraphs | **NOT FIXED** | 4 standalone English paragraphs remain at content lines 48, 110, 119, 233 |
| H1 Підсумок heading | **FIXED** | Line 238: `## Підсумок` (H2) |
| Plokhy described as novelist | **FIXED** | Line 202: «новий роман Сергія Жадана» — real Ukrainian author |
| обачний tested before teaching | **FIXED** | Line 117 teaches обачний with etymology before activities test it |
| Off-scope розклад quiz item | **FIXED** | розклад only appears as incorrect option/distractor in activities |
| "Це не просто" LLM fingerprint | **FIXED** | Pattern not found in current content |
| Cold opening, no greeting | **FIXED** | Line 10: «Привіт! Welcome to your first word-building module.» |
| Tautology "регулярний рух пішки, який повторюється" | **FIXED** | Line 51 now reads «регулярний рух пішки, а не рух в один кінець у цей момент» — tautology removed, replaced with meaningful contrast |

**Summary: 3 of 11 D.1 issues remain unfixed. All 3 are IPA errors in the vocabulary file — D.2 appears to have failed to apply vocabulary file fixes.**

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: 6/6 present (Вступ, Родини ход- та пис-, Родини чит- та бач-, Фонетика та префікси, Практичне застосування, Підсумок)
- Vocabulary: 29 items in vocabulary file; Big Four roots covered (ход-, пис-, чит-, бач-); розклад included as conceptual expansion
- Grammar scope: PASS — stays within root families, prefixes, aspectual pairs, euphony rule; no scope creep
- Objectives: 4/4 addressed (identify roots ✓ [section «Практичне застосування» line 191], guess derivatives ✓ [Guessing Machine in «Фонетика та префікси» line 181], build words ✓ [throughout], recognize professional roots ✓ [line 69 письменник])
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm "Привіт!" opening at line 10; excellent Quick Win box at line 23; strong bookstore dialogue at lines 200–207 in section «Практичне застосування»; 7 varied callout boxes (tip, warning, culture, observe, fact, myth-buster); 4 standalone English paragraphs (lines 48, 110, 119, 233) break Ukrainian flow mid-section without callout framing |
| 2 | Language | 8/10 | <8 | Ukrainian prose is clean throughout; no Russianisms; no calques; minor English translation issue at line 97 «Я люблю **читати** детективи. (I love reading detectives.)» — "detectives" should be "detective stories"; line 166 glosses «**В**писати» as "(to type in)" when "to write in/inscribe" is more accurate; line 240 in section «Підсумок» uses «дивовижну архітектуру української мови» — slightly florid for a summary |
| 3 | Pedagogy | 9/10 | <7 | обачний properly taught at line 117 before testing — D.1 fix verified; PPP structure intact: Present (sections «Вступ» through «Родини чит- та бач-») → Practice (section «Фонетика та префікси» Guessing Machine) → Produce (section «Практичне застосування» dialogue and aspect practice); Quick Win at line 23 provides early dopamine hit; conjugation table at lines 54–59 in section «Родини ход- та пис-» is visual and clear |
| 4 | Activities | 9/10 | <7 | 12 activities across 10 unique types — excellent variety; all items align with taught content; розклад fixed to distractor-only; cloze library passage (activity line 349) is outstanding contextual practice; error-correction items (activity lines 211–250) test meaningful distinctions (aspect, euphony, бачити/дивитися); minor: activity line 245 «Мені потрібно прочитати листа весь вечір» uses genitive "листа" — acceptable but less standard than accusative "лист" |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5; warm greeting ✓, quick wins ✓, clear instructions ✓, Ukrainian not scary ✓, come back tomorrow ✓; section «Підсумок» provides progress celebration with self-check questions (lines 244–251); callout boxes provide emotional safety throughout; standalone English paragraphs (lines 48, 119) are not jarring enough to fail |
| 6 | LLM Fingerprint | 8/10 | <7 | "Це не просто" pattern removed ✓; section openings vary (English intro in «Вступ», Ukrainian «Корінь...» in «Родини ход- та пис-» and «Родини чит- та бач-», English in «Фонетика та префікси», Ukrainian in «Практичне застосування», Ukrainian in «Підсумок»); callout box types: 6 different types across 7 boxes; residual generic phrasing: line 127 «Це слово показує, як логіка мови створює романтичну лексику.» and line 240 «дивовижну архітектуру української мови»; example format somewhat uniform (Ukrainian + English parenthetical) across sections but this is standard pedagogical format |
| 7 | Linguistic Accuracy | 7/10 | <9 | **4 IPA errors**: (1) вхід `[ʍxʲid]` uses non-Ukrainian phoneme ʍ (vocab line 9); (2) сходити `[sxɔdɪtɪ]` missing stress mark (vocab line 116); (3) передбачити `[pɛrɛˈdbɑt͡ʃɪtɪ]` stress before [d] not [b] (vocab line 93); (4) NEW: префікс `[prɛfʲiks]` missing stress mark (vocab line 128); grammar explanations accurate; word formation logic correct throughout |

**Weighted Overall:**
```
(8×1.5 + 8×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 7×1.5) / 8.9
= (12.0 + 8.8 + 10.8 + 11.7 + 11.7 + 8.0 + 10.5) / 8.9
= 73.5 / 8.9
= 8.3/10
```

**AUTO-FAIL TRIGGER**: Linguistic Accuracy 7/10 < 9 threshold

## Auto-Fail Checklist Results

- Russianisms: CLEAN — no Russian calques detected
- Calques: CLEAN — no calque patterns found
- Colonial framing: CLEAN — no Russian comparisons found; Ukrainian word formation presented on its own terms
- Grammar scope: CLEAN — stays within root families, prefixes, aspect, euphony rule
- Activity errors: CLEAN — all items properly aligned after earlier D.2 fixes
- Beginner safety: 5/5
- Factual accuracy: CLEAN — etymological claims (Proto-Slavic *pьsati*, *čisti*, Greek *hodos* connection) are established; Zhadan is a real Ukrainian fiction writer
- **AUTO-FAIL TRIGGER**: Linguistic Accuracy 7/10 < 9 threshold (3 unfixed D.1 IPA errors + 1 new IPA error)

## Critical Issues Found

### Issue 1: UNFIXED — IPA Error on вхід Using Non-Ukrainian Phoneme [ʍ]
- **Location**: Vocabulary file line 9
- **Original**: `ipa: '[ʍxʲid]'` for lemma "вхід"
- **Problem**: This error was flagged in D.1 and D.2 failed to repair it. The symbol ʍ represents a voiceless labial-velar approximant (found in some Scottish English dialects). This phoneme does not exist in the Ukrainian phonological inventory. The в in вхід before voiceless х is realized as labiodental [ʋ] or drops entirely, never as [ʍ].
- **Fix**: Change to `ipa: '[ʋxʲid]'`

### Issue 2: UNFIXED — IPA Missing Stress Mark on сходити
- **Location**: Vocabulary file line 116
- **Original**: `ipa: '[sxɔdɪtɪ]'`
- **Problem**: Flagged in D.1, unfixed. Every polysyllabic vocabulary entry must have stress marked. The stress falls on the second syllable: схо́дити.
- **Fix**: Change to `ipa: '[sxɔˈdɪtɪ]'`

### Issue 3: UNFIXED — IPA Stress Misplacement on передбачити
- **Location**: Vocabulary file line 93
- **Original**: `ipa: '[pɛrɛˈdbɑt͡ʃɪtɪ]'`
- **Problem**: Flagged in D.1, unfixed. The stress mark is placed between [ɛ] and [d], implying stress on the syllable "дба" which doesn't exist. The correct stress is передба́чити — on the syllable [bɑ].
- **Fix**: Change to `ipa: '[pɛrɛdˈbɑt͡ʃɪtɪ]'`

### Issue 4: NEW — IPA Missing Stress Mark on префікс
- **Location**: Vocabulary file line 128
- **Original**: `ipa: '[prɛfʲiks]'`
- **Problem**: Missing stress mark. The stress falls on the second syllable: префі́кс.
- **Fix**: Change to `ipa: '[prɛˈfʲiks]'`

### Issue 5: English Translation Inaccuracy — "reading detectives"
- **Location**: Content line 97, section «Родини чит- та бач-»
- **Original**: «Я люблю **читати** детективи. (I love reading detectives.)»
- **Problem**: "Детективи" in Ukrainian colloquially means "detective stories/novels" (the genre), but the English gloss "reading detectives" is misleading — it sounds like reading about detective people. The translation should reflect the genre meaning.
- **Fix**: Change English gloss to "(I love reading detective stories.)"

### Issue 6: English Translation Inaccuracy — "to type in" for вписати
- **Location**: Content line 166, section «Фонетика та префікси»
- **Original**: «**В**писати (to type in, to insert text — рух тексту всередину документа)»
- **Problem**: "Вписати" means "to write in, to inscribe, to enter" — not "to type in." The gloss "to type in" implies keyboard input, which would be "набрати" or "ввести." "To insert text" is acceptable; "to type in" is not.
- **Fix**: Change to "(to write in, to insert text — рух тексту всередину документа)"

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 97 (content) | «(I love reading detectives.)» | «(I love reading detective stories.)» | Translation |
| 166 (content) | «to type in, to insert text» | «to write in, to insert text» | Translation |
| 9 (vocab) | `ipa: '[ʍxʲid]'` | `ipa: '[ʋxʲid]'` | IPA phoneme |
| 93 (vocab) | `ipa: '[pɛrɛˈdbɑt͡ʃɪtɪ]'` | `ipa: '[pɛrɛdˈbɑt͡ʃɪtɪ]'` | IPA stress |
| 116 (vocab) | `ipa: '[sxɔdɪtɪ]'` | `ipa: '[sxɔˈdɪtɪ]'` | IPA stress |
| 128 (vocab) | `ipa: '[prɛfʲiks]'` | `ipa: '[prɛˈfʲiks]'` | IPA stress |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — Content is well-paced with small conceptual chunks; each root family gets its own section with practice
- Instructions clear? **Pass** — Learning objectives set in section «Вступ» at line 12; each section has clear purpose
- Quick wins? **Pass** — Quick Win at line 23 (guess вхід meaning); conjugation table at lines 54–59; bookstore dialogue at lines 200–207
- Ukrainian scary? **Pass** — Introduced gently with English scaffolding; the Lego metaphor in «Вступ» makes word formation approachable
- Come back tomorrow? **Pass** — Encouraging closing in section «Підсумок» with self-check questions; varied callout boxes maintain engagement

## Strengths

- **Excellent activity variety**: 12 activities across 10 unique types (match-up, quiz, fill-in, group-sort, unjumble, true-false, error-correction, mark-the-words, select, cloze, translate) — outstanding for A2
- **Strong cultural hooks**: писанка connection to *пис-* root (line 67 in «Родини ход- та пис-»), побачення etymology as "mutual seeing" (line 122 in «Родини чит- та бач-»)
- **Practical dialogue**: The bookstore conversation (lines 200–207 in «Практичне застосування») uses 5 target vocabulary items naturally and is contextually authentic
- **Effective mnemonic**: "Кафе Птах" euphony rule presentation in section «Фонетика та префікси» (lines 143–149) is clear, memorable, and pedagogically sound
- **Well-designed error-correction activities**: Items target precisely the errors the lesson addresses (зходити→сходити, бачили→дивилися, надпис→підпис)
- **obачний D.1 fix verified**: Line 117 in section «Родини чит- та бач-» now properly teaches обачний with prefix analysis and example before activities test it

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Vocab line 9: Change `ipa: '[ʍxʲid]'` → `ipa: '[ʋxʲid]'` — removes non-Ukrainian phoneme
2. Vocab line 116: Change `ipa: '[sxɔdɪtɪ]'` → `ipa: '[sxɔˈdɪtɪ]'` — adds missing stress
3. Vocab line 93: Change `ipa: '[pɛrɛˈdbɑt͡ʃɪtɪ]'` → `ipa: '[pɛrɛdˈbɑt͡ʃɪtɪ]'` — corrects stress placement
4. Vocab line 128: Change `ipa: '[prɛfʲiks]'` → `ipa: '[prɛˈfʲiks]'` — adds missing stress

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Lines 48, 110, 119, 233: Wrap standalone English paragraphs in `[!tip]` or `[!observe]` callout boxes, or integrate them into the preceding Ukrainian text as bilingual explanations — this resolves the "orphaned" feeling

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Content line 97: Change "(I love reading detectives.)" → "(I love reading detective stories.)"
2. Content line 166: Change "(to type in, to insert text" → "(to write in, to insert text"

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Content line 127: Rephrase «Це слово показує, як логіка мови створює романтичну лексику.» to something more natural, e.g., «Так простий корінь бач- став основою для одного з найромантичніших слів.»
2. Content line 240 in section «Підсумок»: Replace «дивовижну архітектуру української мови» with a less florid phrase, e.g., «систему українського словотворення»

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 9.0 + 13.5) / 8.9
= 80.1 / 8.9
= 9.0/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track)
- Dates checked: 0 (no specific historical dates claimed)
- Named figures verified: 1 (Сергій Жадан — confirmed real Ukrainian author, line 202)
- Primary quotes cross-referenced: N/A
- Chronological sequence: N/A
- Claims without research grounding: 0
- Etymology claims verified: 3 (Proto-Slavic *pьsati* at line 67, *čisti* at line 93, Greek *hodos* at line 44 — all established in research notes)
- Callout box claims verified: 7/7 — all factual claims in callout boxes are accurate (писанка etymology, бачити/дивитися distinction, записати dual meaning, Кафе Птах rule, aspect pair logic, обачний etymology, aspect myth-busting)

## Verification Summary

- Content lines read: 252
- Activity items checked: 62 (across 12 activities)
- Ukrainian sentences verified: 47
- IPA transcriptions checked: 29
- Factual claims verified: 11
- Issues found: 6

## Verdict

**FAIL**

Three IPA errors from D.1 remain unfixed in the vocabulary file (вхід [ʍxʲid], сходити missing stress, передбачити misplaced stress), plus one new IPA error (префікс missing stress). These are trivial single-character fixes but trigger the Linguistic Accuracy < 9 auto-fail gate. D.2 appears to have never applied the vocabulary file repairs from the previous cycle.
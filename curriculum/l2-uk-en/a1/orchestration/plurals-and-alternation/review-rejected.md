# Рецензія: Plurals and Alternation

**Level:** A1 | **Module:** 13
**Overall Score:** 7.2/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-opus-4-6

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: 5/5 plan sections present + bonus Підсумок — PASS
- Vocabulary: 8/8 required present in prose, 4/4 recommended present — PASS
- Grammar scope: PASS (Nominative plural only, consonant alternation correctly labeled as preview)
- Objectives: 4/4 addressed — PASS
- Persona: FAIL — Plan specifies "Market Vendor" role but content has ZERO market context
- Activity hints: 4/4 types present with correct item counts — PASS
```

### Plan Content Outline Point-by-Point

**Section "Множина іменників":**
- Masculine plural endings -и/-і: COVERED (line 6, студент→студенти, хлопець→хлопці)
- Feminine plural endings replacing -а/-я: COVERED (line 13, книга→книги, земля→землі)
- Neuter plural endings replacing -о/-е: COVERED (line 20, місто→міста, море→моря)
- Irregular plurals (діти, люди, очі): COVERED (line 27)

**Section "Чергування":**
- Vowel alternation і→о/е: COVERED (line 33, кіт→коти, піч→печі, ніж→ножі)
- Why alternation happens (fleeting і): COVERED (line 35)
- Consonant alternation preview (к→ц, г→з, х→с): COVERED (line 43)
- Pattern recognition strategy: COVERED (line 45)

**Section "Множина прикметників":**
- Simplification to single -і/-ї: COVERED (line 51-53)
- Soft-stem adjectives: COVERED (line 60, синій→сині)
- Agreement with plural nouns: COVERED (line 62)
- Practice forming noun phrases: COVERED (lines 73-76)

**Section "Винятки та особливості":**
- Uncountable nouns: COVERED (line 82, молоко, цукор, вода, повітря)
- Plural-only nouns: COVERED (line 88, гроші, двері, ножиці, окуляри)
- Stress shifts in plural: COVERED (line 95, рука→руки, сестра→сестри, нога→ноги)

**Section "Практика":**
- Plural formation drills: COVERED (lines 101-108)
- Matching singulars to plurals: COVERED (lines 112-115)
- Reading plural phrases: COVERED (lines 119-127)

**CRITICAL MISS — Market Vendor Persona:** The plan specifies `persona.role: Market Vendor` and the research notes design an entire market scenario with яблука, огірки, помідори on market stalls. The content has ZERO market references. No ринок, no vendor interaction, no shopping scenario. This is a significant plan adherence failure since the persona was designed to contextualize plurals in a real-world setting.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Missing persona context; no callout boxes; overlong paragraphs (line 35 is a wall of text about historical linguistics) |
| 2 | Language | 7/10 | <8 | Multiple stress mark errors confirmed (see Linguistic Accuracy); LLM superlatives ("fascinating", "fantastic", "incredibly") |
| 3 | Pedagogy | 7/10 | <7 | Plan's Market Vendor persona completely unused; no discovery exercise despite research designing one; explanation-heavy with few interactive moments before section "Практика" |
| 4 | Activities | 7/10 | <7 | Non-existent forms as distractors (дитин, ніжа, окна fail VESUM) contradicting builder's claim of "real dictionary words"; otherwise solid variety |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5 — warm tone throughout, clear explanations, quick wins via simple bullet lists; dock for wall-of-text in section "Чергування" (line 35 paragraph on historical linguistics overwhelming for A1) |
| 6 | LLM Fingerprint | 7/10 | <7 | Structural monotony: 4/6 sections open with "You [already know/have learned]..." backward reference; uniform example format (identical `**word** (translation) → **word** (translation)` bullets across all sections); superlative stacking ("fascinating", "fantastic", "incredibly") |
| 7 | Linguistic Accuracy | 7/10 | <9 | At least 3 confirmed stress errors (землі́→зе́млі, міста́→мі́ста, со́ки→соки́); likely more pending manual verification (печі́, моря́); non-existent distractor forms |

**Weighted Overall:**
```
(7×1.5 + 7×1.1 + 7×1.2 + 7×1.3 + 8×1.3 + 7×1.0 + 7×1.5) / 8.9
= (10.5 + 7.7 + 8.4 + 9.1 + 10.4 + 7.0 + 10.5) / 8.9
= 63.6 / 8.9
= 7.1/10
```

## Auto-Fail Checklist Results

- Russianisms: CLEAN — no Russian ghost words detected
- Calques: CLEAN
- Colonial framing: CLEAN — no "unlike Russian" comparisons
- Grammar scope: CLEAN — stays in Nominative, consonant alternation correctly marked as preview
- Activity errors: FAIL — дитин, ніжа, окна are non-existent Ukrainian forms used as distractors
- Beginner safety: 4/5
- Factual accuracy: Grammar rules are accurate; stress marks have errors

## Critical Issues Found

### Issue 1: Multiple Stress Mark Errors (Linguistic Accuracy — HIGH)
- **Location**: Lines 13, 20, 22, 25, 33, 39 across sections "Множина іменників" and "Чергування"
- **Original (line 13)**: 「The word **земля́** (land, earth) replaces its final **-я** with **-і**, becoming **землі́** (lands).」
- **Problem**: Pre-screen flags землі́ as wrong stress; nom.pl. of земля́ is зе́млі (stress shifts to first syllable)
- **Fix**: Replace **землі́** with **зе́млі** on line 13

- **Original (line 20)**: 「The word **мі́сто** (city) drops its **-о** and adds an **-а** to become **міста́** (cities).」
- **Problem**: Nom.pl. of мі́сто is мі́ста (stress stays on first syllable), not міста́
- **Fix**: Replace **міста́** with **мі́ста** on lines 20, 22, 66, 104, 120, 135

- **Original (line 33)**: 「the word **піч** (oven) becomes **печі́** (ovens)」
- **Problem**: Pre-screen flags печі́; nom.pl. of піч is пе́чі (stress on first syllable)
- **Fix**: Replace **печі́** with **пе́чі**

- **Original (line 39)**: 「**сік** (juice) → **со́ки** (juices)」
- **Problem**: Pre-screen flags со́ки; nom.pl. of сік is соки́ (stress on last syllable)
- **Fix**: Replace **со́ки** with **соки́**

**Note on dismissed pre-screen items:**
- Lines 53-60 AGREEMENT_ERROR flags: All FALSE POSITIVES — these are adjective paradigm tables showing masculine/feminine/neuter→plural forms. Not agreement errors.
- брати́ (line 9): Likely correct for nom.pl. of брат; stress checker confuses with verb бра́ти (to take). DISMISS but verify manually.
- се́стри (line 17): Correct; pre-screen suggesting сестри́ appears wrong. DISMISS.
- ма́ми (line 16): Correct; pre-screen suggesting ма́ми́ is nonsensical. DISMISS.

### Issue 2: Non-Existent Activity Distractors (Activities — HIGH)
- **Location**: Activities file, lines 115, 161, 181
- **Problem**: Three distractors fail VESUM verification:
  - `дитин` (line 115) — not a real Ukrainian word form
  - `ніжа` (line 161) — not a real Ukrainian word form
  - `окна` (line 181) — this is the RUSSIAN plural of окно; not a valid Ukrainian form
- **Builder contradiction**: Builder notes claim "Safely used real dictionary words from the cumulative vocabulary list as activity distractors to guarantee VESUM validation" — this is false for these three items.
- **Fix**: Replace дитин→дітям, ніжа→ножа, окна→ока (real Ukrainian forms that are wrong answers in context)

### Issue 3: Market Vendor Persona Completely Missing (Pedagogy — MEDIUM)
- **Location**: Entire module
- **Problem**: Plan specifies `persona.role: Market Vendor`. Research notes design an elaborate market scenario: "At a Ukrainian market (ринок), vendors display quantity labels: «яблука», «огірки», «помідори»". The content has zero market context. The entire contextual frame designed to make plurals feel real-world is absent.
- **Fix**: Weave a market vendor frame into section "Множина іменників" opening and section "Практика". Add a market scenario with food plurals (яблука, огірки, помідори) as the discovery exercise the research designed.

### Issue 4: Zero Engagement Boxes (Experience — MEDIUM)
- **Location**: Entire module (0 callout boxes)
- **Problem**: Audit requires ≥1 engagement box for A1. Module has zero `[!tip]`, `[!example]`, `[!cultural-note]`, `[!did-you-know]` callouts. Richness gaps confirm: `engagement: 0/2`.
- **Fix**: Add at minimum:
  1. A `[!tip]` box in section "Чергування" with a mnemonic for the fleeting і pattern
  2. A `[!cultural-note]` box in section "Винятки та особливості" about гроші being plural-only (culturally interesting)

### Issue 5: Wall-of-Text Historical Linguistics (Beginner Safety — MEDIUM)
- **Location**: Line 35, section "Чергування"
- **Original**: 「Why does this alternation happen? It goes back to historical vowel changes and what linguists call the "fleeting **і**".」 — followed by a dense paragraph about closed/open syllables, historical vowel changes, and syllable structure.
- **Problem**: This is university-level phonological explanation dropped on an A1 learner. "A closed syllable is a syllable that ends in a consonant" — this meta-linguistic terminology is overwhelming. The learner just needs to know that і changes to о/е in certain words.
- **Fix**: Simplify to 2-3 sentences max. Move detailed explanation to a collapsible `[!tip]` box for curious learners.

### Issue 6: LLM Superlative Stacking (LLM Fingerprint — LOW)
- **Location**: Lines 31, 49, 133
- **Original (line 49)**: 「But here is some fantastic news that will make your life much easier: when you use adjectives in the plural, things get incredibly simple!」
- **Problem**: "fascinating" (lines 31, 133), "fantastic" (line 49), "incredibly" (lines 49, 135) — five superlatives. Real tutors don't talk this way. This is LLM enthusiasm inflation.
- **Fix**: Replace with natural tutor language: "Here's good news:" instead of "fantastic news"; "quite simple" instead of "incredibly simple".

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 13 | 「землі́」 | 「зе́млі」 | Stress |
| 20 | 「міста́」 | 「мі́ста」 | Stress |
| 33 | 「печі́」 | 「пе́чі」 | Stress |
| 39 | 「со́ки」 | 「соки́」 | Stress |
| Act. 115 | дитин | дітям | Non-existent form |
| Act. 161 | ніжа | ножа | Non-existent form |
| Act. 181 | окна | ока | Non-existent / Russicism |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — pacing is reasonable, bullet examples break up text
- Instructions clear? **Pass** — always clear what to observe
- Quick wins? **Pass** — simple bullet-list examples provide immediate success moments
- Ukrainian scary? **Pass** — introduced gently with translations throughout
- Come back tomorrow? **Fail** — line 35 paragraph on historical phonology would make a nervous beginner doubt they belong here; also no persona/context to keep them emotionally invested

## Strengths
- Grammar explanations are accurate and well-structured (correct endings for all three genders, correct alternation patterns)
- Example sentences are natural and use high-frequency vocabulary appropriate for A1
- Good variety of activity types (fill-in, match-up, quiz, group-sort) matching plan hints exactly
- Irregular plurals (діти, люди, очі) are well-presented as "memorize these" rather than explained with complex rules
- Vocabulary file is clean and well-organized with 20 items, all verified against VESUM

## Fix Plan to Reach 9/10 (REQUIRED since score < 9.0)

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Lines 13, 20, 22, 25, 33, 39, 66, 104, 108, 120, 135: Correct all stress marks (землі́→зе́млі, міста́→мі́ста, печі́→пе́чі, со́ки→соки́) — systematically across all occurrences
2. Activities lines 115, 161, 181: Replace non-existent distractors with real Ukrainian forms

**Expected score after fix:** 9/10

### Language: 7/10 → 9/10
**What to fix:**
1. Replace LLM superlatives with natural tutor language (5 instances)
2. Stress mark corrections (same as Linguistic Accuracy)

**Expected score after fix:** 9/10

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Add ≥2 engagement callout boxes (tip + cultural-note)
2. Weave market vendor persona into opening and practice sections
3. Break up line 35 wall-of-text into simplified explanation + collapsible detail

**Expected score after fix:** 9/10

### Pedagogy: 7/10 → 9/10
**What to fix:**
1. Add market scenario discovery exercise (from research notes) to section "Множина іменників"
2. Add the two-column однина/множина table from the textbook model (Vashulenko Grade 3 p.116)

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Replace 3 non-existent distractors with VESUM-verified forms

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Vary section openings (not all "You [already know/have learned]...")
2. Mix example formats (add a table, a mini-dialogue, not just identical bullet lists)
3. Reduce superlatives to ≤1

**Expected score after fix:** 8/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 10.4 + 8.0 + 13.5) / 8.9
= 77.8 / 8.9
= 8.7/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track)
- Grammar rules verified: All plural formation rules are accurate per textbook RAG (Grade 3, p.114; Grade 4, p.38)
- Stress marks: Multiple errors flagged (see Critical Issues)
- Cultural claims: No callout boxes to verify (none present)
- Textbook alignment: Content matches Vashulenko Grade 3 p.114 однина/множина approach, but fails to use the p.116 discovery exercise for pluralia tantum as research recommended

## Verification Summary

- Content lines read: 141
- Activity items checked: 44 (12 fill-in + 12 match-up + 10 quiz + 10 group-sort)
- Ukrainian sentences verified: 38 (all inline examples and practice sentences)
- Citations in bank: 15
- Issues found: 6 (2 HIGH, 3 MEDIUM, 1 LOW)

## Verdict

**FAIL**

Blocking issues: (1) Multiple confirmed stress mark errors violate linguistic accuracy gate (Linguistic Accuracy 7/10, auto-fail threshold <9); (2) Non-existent activity distractors (дитин, ніжа, окна) fail VESUM audit gate; (3) Zero engagement boxes fail richness gate. Secondary: Market Vendor persona from plan is completely absent.
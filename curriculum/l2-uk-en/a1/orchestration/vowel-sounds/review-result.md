# Рецензія: Vowel Sounds

**Level:** A1 | **Module:** 2
**Overall Score:** 7.9/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-6

## Plan Verification

```
Plan-Content Alignment: PASS (with minor gaps)
- Sections: All 6 sections present as H2 headers ✅
- Vocabulary: 18/18 required+recommended words present in prose ✅
- Grammar scope: ISSUE — verb 'каже' violates pre-verb constraint
- Objectives: All 5 objectives addressed ✅
- Pronunciation videos: All 10 videos embedded ✅
```

### Plan Adherence Checklist

**Section "Вступ — Introduction":**
- "Review: M1 gave you the alphabet map and 10 practice letters" — COVERED (line 3: references first lesson)
- "Why vowels matter: every syllable has exactly one vowel" — COVERED (line 5)

**Section "Шість основних голосних — Six Base Vowels":**
- "А — open, like 'a' in 'father'. Words: мама, каша, сало" — COVERED (line 11)
- "О — rounded. Stays О even when unstressed. Words: око, молоко, село" — COVERED (line 16)
- "У — like 'oo' in 'moon'. Words: тут, вухо, суп" — COVERED (line 21)
- "Е — like 'e' in 'set'. Words: небо, село, день" — COVERED (line 26)
- "И — uniquely Ukrainian. Words: риба, сир, син" — COVERED (line 31)
- "І — like 'ee' in 'see'. Words: ліс, кіт, сік" — COVERED (line 36)
- "И vs І distinction with minimal pairs: кит vs кіт" — COVERED (line 41)

**Section "Наголос — Word Stress":**
- "Every Ukrainian word has one stressed syllable" — COVERED (line 45)
- "Golden Rule: Ukrainian vowels stay pure" — COVERED (line 47)
- "Example: молоко — stress on last syllable, all three О's the same" — COVERED (line 49)

**Section "Йотовані голосні — Iotated Vowels":**
- "Я = й+а. At start: яблуко. After vowel: моя. After consonant: дядько" — COVERED (line 55)
- "Ю = й+у. At start: юнак, юшка. After consonant: люди" — COVERED (line 60)
- "Є = й+е. At start: Європа. After vowel: моє" — COVERED (line 65)
- "Ї = ALWAYS two sounds. Words: їжак, їжа, Україна. Cultural note: Ї as symbol" — COVERED (line 70)
- "Й — semi-vowel. Words: край, йогурт. Never forms syllable alone" — COVERED (line 75)

**Section "Голосні в словах — Vowels in Words":**
- "Short sentences: Це яблуко. Це моє село. Мама каже 'так'. Де мій кіт?" — COVERED (lines 81-84)
- "Count-the-vowels exercise: молоко, Україна, кіт" — COVERED (lines 87-92)

**Section "Підсумок — Summary":**
- "10 vowel letters: 6 base + 4 iotated + semi-vowel Й" — COVERED (line 98)
- "Golden Rule reinforced" — COVERED (line 100)
- "Self-check questions" — COVERED (line 102)
- "Next: M3 consonant system" — COVERED (line 104)

**Activity hints adherence:**
- watch-and-repeat (10 items) — COVERED ✅
- classify (10 items) — COVERED ✅
- image-to-letter (8 items) — COVERED ✅
- quiz (10 items) — COVERED ✅ (has 10 items)
- group-sort (8+ items) — COVERED ✅ (10 items)
- fill-in (8 items) — COVERED ✅

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Warm tutor voice throughout. Opens with encouragement, ends with celebration. Minor: no callout boxes anywhere. |
| 2 | Language | 7/10 | <8 | Colonial framing on line 16: 「This is completely unlike Russian, where unstressed 'o' turns into an 'a' sound.」 defines Ukrainian vowel purity via Russian comparison. |
| 3 | Pedagogy | 8/10 | <7 | Strong PPP structure. Vowel-counting exercises excellent. But verb 'каже' on line 83 violates grammar scope (verbs start at M15). |
| 4 | Activities | 7/10 | <7 | кот (Russicism, not in VESUM) appears as quiz distractor line 182. Otherwise well-designed and varied. |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Pacing is excellent, encouragement throughout, no overwhelm. |
| 6 | LLM Fingerprint | 8/10 | <7 | Line 75: 「It is very important to note that」 is classic LLM formality. Otherwise natural tutor voice. No structural monotony. |
| 7 | Linguistic Accuracy | 8/10 | <9 | Verb 'каже' in pre-verb module (grammar scope violation). Line 70 claim about Ї not existing in any other Cyrillic alphabet needs verification (Bosnian uses it in limited contexts). |

**Weighted Overall:** (9×1.5 + 7×1.1 + 8×1.2 + 7×1.3 + 9×1.3 + 8×1.0 + 8×1.5) / 8.9 = (13.5 + 7.7 + 9.6 + 9.1 + 11.7 + 8.0 + 12.0) / 8.9 = 71.6 / 8.9 = **8.0/10**

## Auto-Fail Checklist Results

- Russianisms: **FOUND** — `кот` in activities (line 182). This is the Russian word for cat; Ukrainian is `кіт`.
- Calques: CLEAN
- Colonial framing: **FOUND** — line 16: 「This is completely unlike Russian, where unstressed 'o' turns into an 'a' sound.」
- Grammar scope: **VIOLATION** — verb `каже` (казати, imperf:pres:s:3) on line 83. Verbs are forbidden before M15.
- Activity errors: `кот` is not a valid Ukrainian word form (VESUM-verified: NOT FOUND).
- Beginner safety: 5/5
- Factual accuracy: Line 70 claim 「It does not exist in any other Cyrillic alphabet」 — slightly overstated. Ї is overwhelmingly associated with Ukrainian and is a legitimate cultural symbol, but the absolute "no other Cyrillic alphabet" claim should be softened to "unique to the Ukrainian alphabet among major Cyrillic scripts" or similar.

## Critical Issues Found

### Issue 1: Russicism in Activity Distractor (HIGH)
- **Location**: Activities file, line 182 / quiz item "Which word means 'cat'?"
- **Original**: 「кот」
- **Problem**: `кот` is NOT a valid Ukrainian word (confirmed: VESUM NOT FOUND). It is the Russian word for cat. Including it as a distractor teaches students a Russian word form. This is a Russicism and an audit gate failure.
- **Fix**: Replace `кот` with a valid Ukrainian distractor like `кут` (corner) which is already used in the same quiz, or `кін` (another valid monosyllable). Since `кут` is already option D, replace `кот` with `кат` (executioner — valid VESUM word, same consonant frame).

### Issue 2: Verb in Pre-Verb Module (HIGH)
- **Location**: Line 83, Section "Голосні в словах — Vowels in Words"
- **Original**: 「Мама каже 'так'.」
- **Problem**: `каже` is a conjugated verb (казати, 3rd person singular present). This module is M2 — verbs are forbidden until M15. The builder acknowledged this deviation, noting the plan includes this exact sentence. However, the plan itself may need revision; at minimum, the sentence exposes learners to a grammatical form they won't study for 13 more modules.
- **Fix**: Replace with a verb-free sentence: «Мама — так.» or «Мама тут.» (uses only the word `тут` from M1). Alternatively: «Це мама.»

### Issue 3: Colonial Framing (MEDIUM)
- **Location**: Line 16, Section "Шість основних голосних — Six Base Vowels"
- **Original**: 「This is completely unlike Russian, where unstressed 'o' turns into an 'a' sound.」
- **Problem**: Defines Ukrainian vowel purity by contrasting with Russian. This is colonial framing — Ukrainian features should be presented on their own terms. A1 learners don't need Russian as a reference point.
- **Fix**: Rewrite to present the Ukrainian feature positively: "The single most important thing to remember here is that it stays a pure, full **О** even when it is unstressed. In Ukrainian, every О is always a clear О — it never reduces to a weaker sound. This vowel purity is a beautiful feature of Ukrainian pronunciation."

### Issue 4: Zero Engagement Boxes (MEDIUM)
- **Location**: Whole module
- **Problem**: The module contains 0 callout boxes (`[!tip]`, `[!example]`, `[!cultural-note]`, `[!did-you-know]`, etc.). The audit requires minimum 1 for A1. The Ї cultural identity note on line 70 is excellent content but is buried in prose rather than highlighted in a callout box. The richness audit shows engagement: 0/2.
- **Fix**: Convert the Ї cultural note (line 70) into a `> [!did-you-know]` callout. Add at least one `> [!tip]` for the И vs І jaw position technique (line 41).

### Issue 5: LLM Formality Pattern (LOW)
- **Location**: Line 75, Section "Йотовані голосні — Iotated Vowels"
- **Original**: 「It is very important to note that **Й** never forms a syllable all on its own.」
- **Problem**: "It is very important to note" is a classic LLM formal pattern. A patient tutor would say this more naturally.
- **Fix**: "Here's a key rule: **Й** never forms a syllable all on its own."

### Issue 6: Factual Overstatement — Ї Uniqueness (LOW)
- **Location**: Line 70, Section "Йотовані голосні — Iotated Vowels"
- **Original**: 「It does not exist in any other Cyrillic alphabet」
- **Problem**: While Ї is overwhelmingly a Ukrainian symbol and the claim is nearly correct, it appears in limited historical/regional Cyrillic usage (Rusyn). The absolute claim is slightly overstated.
- **Fix**: Soften to: "It is unique to the Ukrainian Cyrillic alphabet and found in no other major Slavic writing system."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 83 | 「Мама каже 'так'.」 | «Це мама.» or «Мама тут.» | Scope (verb in pre-verb module) |
| 182 (acts) | 「кот」 | кат | Russicism (not valid Ukrainian) |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — pacing is comfortable, new words introduced 3-5 at a time per vowel
- Instructions clear? **Pass** — always know what to do, English explanations are clear
- Quick wins? **Pass** — vowels are presented individually with familiar words (мама, тут from M1)
- Ukrainian scary? **Pass** — introduced gently with English support, video links for each sound
- Come back tomorrow? **Pass** — encouraging throughout, ends with celebration and clear next step

## Strengths

- **Excellent plan adherence**: Every single content_outline point is covered, all 18 vocabulary words appear naturally in prose.
- **Strong pedagogical metaphor**: 「In Ukrainian, a vowel is a promise—it always sounds like itself, no matter what.」 (line 49) — this is memorable and pedagogically effective.
- **Well-designed activities**: 6 diverse activity types, well-matched to objectives. The syllable-counting fill-in directly reinforces the core skill. The И/І quiz is thorough with 10 items.
- **Warm tutor voice**: The module genuinely feels like a patient, encouraging tutor. Line 3 opens with 「Welcome to the beating heart of the Ukrainian language!」 and the closing celebrates progress.
- **Video integration**: All 10 pronunciation videos properly embedded with Anna Ohoiko credit.

## Fix Plan to Reach 9.0/10 (REQUIRED — score is 8.0)

### Language: 7/10 → 9/10
**What to fix:**
1. Line 16: Remove Russian comparison. Change to present vowel purity as an inherent Ukrainian feature.
2. No other colonial framing found — single fix resolves this.

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Activities line 182: Replace `кот` with `кат` (valid VESUM word, same consonant frame as кіт/кит).

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Line 83: Replace 「Мама каже 'так'.」 with a verb-free alternative like «Це мама.» or «Мама тут.»

**Expected score after fix:** 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 83: Remove verb (same fix as Pedagogy).
2. Line 70: Soften Ї uniqueness claim.
3. Activities line 182: Remove Russicism `кот`.

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Line 75: Replace "It is very important to note" with natural tutor phrasing.

**Expected score after fix:** 9/10

### Add Engagement Boxes (Richness fix):
1. Convert Ї cultural note (line 70) into a `> [!did-you-know]` callout.
2. Add `> [!tip]` for И vs І jaw position technique near line 41.

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 9.0 + 13.5) / 8.9
= 80.1 / 8.9 = 9.0/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track)
- Dates checked: N/A
- Named figures verified: N/A
- Primary quotes cross-referenced: N/A
- Grammar rules verified: Vowel purity rule confirmed by Grade 2 textbook p.34 (6 голосних звуків, 10 букв). Syllable counting rule confirmed by Grade 2 p.34 (поділи їх на склади).
- Callout box claims: Line 70 Ї uniqueness claim slightly overstated (see Issue 6).

## Verification Summary

- Content lines read: 106
- Activity items checked: 54 (across 6 activities)
- Ukrainian sentences verified: 12
- Citations in bank: 16
- Issues found: 6

## Verdict

**FAIL**

Blocking issues: (1) `кот` Russicism in activity distractor — not a valid Ukrainian word, fails VESUM gate. (2) Verb `каже` in pre-verb module M2 — grammar scope violation. (3) Colonial framing comparing Ukrainian to Russian on line 16. (4) Zero engagement callout boxes (audit gate failure). All four are fixable with targeted edits.
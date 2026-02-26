# Рецензія: The Cyrillic Code II

**Reviewed-By:** claude-opus-4-6

**Level:** A1 | **Module:** 02
**Overall Score:** 8.4/10
**Status:** PASS
**Reviewed:** 2026-02-25

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: PASS — all 5 H2 sections from content_outline present
- Vocabulary: 8/8 required present, 5/6 recommended present (ніч in content but missing from vocab YAML; тінь in vocab YAML but missing from content)
- Grammar scope: PASS — no grammar scope violations
- Objectives: PASS — all 4 objectives addressed
- Letter count: MISMATCH — plan subtitle says "The Final 14 Letters", content title says "The Final 15 Letters"
  (Module 1 SCOPE says "19 letters" with "remaining 14 for module 2"; 19+15=34 > 33 alphabet letters)
- Activity items: BELOW PLAN — plan specifies 20-item quizzes and 15-20 item match-ups; actual items per activity are 8-12
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm structure with welcome/preview/celebrate arc, but 47% richness (0 dialogues, 1/2 tables, 0 proverbs) significantly limits engagement variety |
| 2 | Language | 9/10 | <8 | Ukrainian grammatically correct throughout; no Russianisms; no colonial framing; minor forced injections on lines 41, 229 |
| 3 | Pedagogy | 8/10 | <7 | Excellent "Smile vs Grin" technique and contrast drills; however, 7 consonants presented in section «Унікальні приголосні» without interleaved mini-exercises before section «Практика та вимова» |
| 4 | Activities | 8/10 | <7 | Good variety (8 types, 74 total items); Й classified as "Consonant" in group-sort contradicts content's "semivowel" teaching; item counts below plan targets |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5; warm opening, scaffolded English support, diagnostic checkpoint, celebration ending |
| 6 | LLM Fingerprint | 8/10 | <7 | Repetitive "You will find/hear/use this letter..." formula across 7 subsections (lines 41, 68, 107, 120, 157, 163, 229); section openings otherwise varied |
| 7 | Linguistic Accuracy | 9/10 | <9 | All pronunciation descriptions accurate; IPA correct in vocabulary; Ґ history verified; vocab sidecar mismatch (тінь in YAML but not content) |

**Weighted Overall:** (8×1.5 + 9×1.1 + 8×1.2 + 8×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9 = (12 + 9.9 + 9.6 + 10.4 + 11.7 + 8 + 13.5) / 8.9 = 75.1 / 8.9 = **8.4/10**

## Auto-Fail Checklist Results

- Russianisms: CLEAN — no instances of давайте + perfective, кушати, получати, etc.
- Calques: CLEAN — no English or Russian calques detected
- Colonial framing: CLEAN — no "Unlike Russian" or comparative framing; `[!decolonization]` block is legitimate
- Grammar scope: CLEAN — module stays within phonetics/alphabet scope
- Activity errors: Й classified as consonant contradicts content (see Issue 2)
- Beginner safety: 5/5
- Factual accuracy: Letter count inconsistency (15 vs 14); Ґ history and Ї Mariupol claims verified correct
- LLM filler: «Це дуже важливо.» (line 41) and «Запам'ятайте це правило.» (line 229) are forced injections

## Critical Issues Found

### Issue 1: Letter Count Inconsistency (Factual)
- **Location**: Line 8 (title), Line 2 (SCOPE), Line 16, Line 18 / Section «Вступ»
- **Original**: «The Cyrillic Code II: The Final 15 Letters» (line 8) and «you have already conquered the first nineteen letters» (line 16)
- **Problem**: The plan subtitle says "The Final 14 Letters." Module 1's SCOPE says it covers 19 letters with "the remaining 14" for module 2. But this module claims 15 letters. 19 + 15 = 34, exceeding the 33-letter Ukrainian alphabet. Either this module covers 14 (plan) or module 1 covers 18 (not 19). The content and plan are inconsistent.
- **Fix**: Change title to "The Final 14 Letters" and line 16 to "the first nineteen letters" if Й was already in module 1 (verify against a1-01 content). Alternatively, if this module genuinely adds Й, change line 16 to "the first eighteen letters" and update module 1's SCOPE to "18 letters."

### Issue 2: Й Classification Contradiction Between Content and Activity
- **Location**: Activity "Consonants vs. Vowels" (activities YAML line 29-49) vs Content line 219, Section «Голосні та напівголосні»
- **Original**: Content line 219: «This hat transforms the letter from a full vowel into a "semivowel."» — Activity YAML places Й under group `Consonants (Приголосні)` at line 38.
- **Problem**: The content explicitly teaches Й as a "semivowel" in the section «Голосні та напівголосні» (Vowels and Semivowels). The group-sort activity then asks learners to classify it as a "Consonant." A learner who paid attention to the lesson would get this "wrong" by placing Й under Vowels. This directly undermines the lesson.
- **Fix**: Either (a) add a third group "Semivowels (Напівголосні)" containing only Й, or (b) move Й to the Vowels group with a note, or (c) change the activity instruction to "Sort into Consonants, Vowels, or Semivowels."

### Issue 3: Vocabulary Sidecar Mismatch
- **Location**: Vocabulary YAML line 70 (тінь) vs Content line 210 (ні́ч)
- **Original**: Vocabulary YAML includes `тінь` (shadow) with IPA `[tʲinʲ]` (line 69-72). Content line 210 uses «ні́ч» (night) as an example under І but never mentions тінь.
- **Problem**: The vocabulary sidecar should reflect words actually taught in the content. тінь never appears in the lesson; ні́ч appears on line 210 but has no vocabulary entry. This breaks the content-vocabulary alignment that learners (and downstream tools) rely on.
- **Fix**: Replace тінь with ніч in the vocabulary YAML: `lemma: ніч`, `translation: night`, `ipa: [nʲit͡ʃ]`, `pos: noun`.

### Issue 4: Forced Ukrainian Injections Without Pedagogical Purpose
- **Location**: Line 41 / Section «Унікальні приголосні» and Line 229 / Section «Голосні та напівголосні»
- **Original**: Line 41: «Це дуже важливо. (This is very important.)» tacked onto end of a paragraph listing Г example words. Line 229: «Запам'ятайте це правило. (Remember this rule.)» appended to a paragraph about Й usage contexts.
- **Problem**: «Це дуже важливо» on line 41 doesn't relate to the example words — it just says "this is very important" without specifying what. «Запам'ятайте це правило» on line 229 says "remember this rule" but no specific rule was stated — the paragraph describes usage contexts, not a rule. These feel like token Ukrainian injections to boost immersion percentage without serving any teaching purpose.
- **Fix**: Line 41: Remove the injection or replace with something meaningful tied to the content, e.g., «Буква Г — дуже часта.» (The letter Г is very common.) Line 229: Remove or replace with a concrete rule statement before the Ukrainian, e.g., explain that Й never starts a syllable alone, then use «Запам'ятайте: Й не починає склад.»

### Issue 5: Richness Severely Below Threshold
- **Location**: Entire module / All sections
- **Original**: Richness audit: 47% (threshold: 95%). Gaps: engagement 2/5, cultural 1/3, examples 4/24, dialogues 0/4, proverbs 0/1, tables 1/2
- **Problem**: The module is primarily expository prose with individual vocabulary examples. It lacks dialogues, has only one comparison table (Ш vs Щ in section «Унікальні приголосні»), zero proverbs, and insufficient structured example blocks and cultural callouts.
- **Fix**: See Fix Plan below for specific additions per gap dimension.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 41 | «Це дуже важливо.» | «Буква Г — дуже часта.» or remove | Forced injection |
| 229 | «Запам'ятайте це правило.» | Remove or precede with actual rule | Forced injection |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? **Pass** — Letters introduced one at a time with H3 subsections; clear English scaffolding declared upfront
- Instructions clear? **Pass** — Learner always knows what to do; diagnostic check at start, reading practice at end
- Quick wins? **Pass** — Familiar words from module 1 used as diagnostic; example words build incrementally
- Ukrainian scary? **Pass** — Heavy English scaffolding with Ukrainian examples translated inline
- Come back tomorrow? **Pass** — Encouraging tone throughout; celebration at end ("You have officially unlocked the entire Cyrillic code")

## Strengths

- **"Smile vs Grin" technique** (Section «Голосні та напівголосні», lines 196-215): Brilliant pedagogical metaphor for the И/І distinction. Physiologically grounded (jaw tension mapping), memorable naming, and immediately applied via minimal pairs (кі́т/ки́т, Ри́м/Рі́вне). This is A+ teaching.
- **Decolonization hook for Ґ** (Section «Унікальні приголосні», lines 54-55): Historically accurate, emotionally resonant, and immediately relevant to letter recognition. Learner understands *why* the distinction matters, not just *how* to pronounce it.
- **Ї as resistance symbol** (Section «Йотовані голосні та М'який знак», lines 150-151): Powerful cultural hook that gives the letter emotional weight beyond its phonetic value. Well-sourced and pedagogically appropriate for A1 (simple narrative, clear significance).
- **Contrast drills** (Section «Практика та вимова», lines 237-255): Well-designed pairs covering the three most common learner errors (І/И, Г/Ґ, С/СЬ). Clear instructions, exaggeration guidance, and progressive difficulty.
- **Activity variety**: 8 distinct activity types (match-up, group-sort, quiz, fill-in ×2, anagram, true-false, quiz) with good explanations for each item. The Г/Ґ fill-in (activity 4) is particularly well-designed.

## Fix Plan to Reach 9/10 (REQUIRED — score 8.4 < 9.0)

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Section «Унікальні приголосні»: Add 1 comparison table for Г vs Ґ (parallel to existing Ш/Щ table on lines 91-94) showing shape, sound, example words, and frequency.
2. Section «Практика та вимова»: Add 2 short dialogues (3-4 lines each) using the new letters. E.g., a café dialogue using Ч (чай), Ц (цукор), and a city navigation dialogue using Ш (школа), Ц (центр).
3. Section «Вступ» or «Практика та вимова»: Add 1 Ukrainian proverb using the new letters — e.g., «Що маєш — бережи» (What you have — treasure it) which uses Щ and Ж.
4. Add 2 `[!engagement]` or `[!did-you-know]` callouts — e.g., one about the frequency of Ч in hospitality language, one about how Ukrainian children learn И/І.
5. Add 1 `[!culture]` callout — e.g., about Lviv (Львів uses Ь) or about the tradition of offering tea (чай).

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Section «Унікальні приголосні»: After the first 3-4 consonants (around line 70), insert a brief "Quick Check" mini-exercise (similar to the one on line 188) asking learners to read aloud 3-4 words using only the consonants covered so far. This breaks up the 90-line block.
2. Section «Практика та вимова»: Add 1-2 guided mini-dialogues where the learner reads both parts, applying multiple letter groups together.

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Fix Й classification in group-sort activity (YAML lines 29-49): Add a third group "Semivowels (Напівголосні)" or move Й to Vowels group with explanatory note.
2. Consider increasing quiz item counts closer to plan targets (8 → 12-15 items) if richness gap demands more practice.

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 9/10
**What to fix:**
1. Vary the "You will find/hear/use this letter..." formula across subsections in «Унікальні приголосні» and «Йотовані голосні та М'який знак». Use different transitions: rhetorical questions, example sentences, cultural context, or frequency statistics instead of the same connector pattern.

**Expected score after fix:** 9/10

### Linguistic Accuracy: 9/10 → 9/10 (maintain)
**What to fix:**
1. Resolve letter count: verify against a1-01 whether 14 or 15 is correct, then update title (line 8) and prose (line 16) accordingly.
2. Replace тінь with ніч in vocabulary YAML.

**Expected score after fix:** 9/10 (already at threshold)

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 9×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 9 + 13.5) / 8.9
= 80.1 / 8.9
= 9.0/10
```

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (A1 core level — no research file)
- Key Facts Ledger present: NO
- Dates checked: 2 (Ґ ban 1933: correct; Ґ restoration 1990: correct)
- Named figures verified: 0 (no named historical figures)
- Primary quotes cross-referenced: N/A
- Chronological sequence: CONSISTENT
- Claims without research grounding: 1 — Mariupol Ї graffiti 2022 (well-documented cultural phenomenon, no research file needed at A1)
- Callout factual accuracy: All 5 callouts verified correct

## Verification Summary

- Content lines read: 299
- Activity items checked: 74 (across 8 activities)
- Ukrainian sentences verified: 12
- IPA transcriptions checked: 20 (all vocabulary items)
- Factual claims verified: 5 (Ґ ban/restoration, Ї uniqueness, Ї Mariupol, Ь palatalization mechanics)
- Issues found: 5 (1 letter count inconsistency, 1 Й classification conflict, 1 vocab mismatch, 1 forced injections, 1 richness gap)

## Verdict

**PASS**

The module delivers solid phonetics instruction with excellent pedagogical techniques ("Smile vs Grin," decolonization hooks, contrast drills) and passes all auto-fail thresholds. The five issues identified are fixable in D.2: the letter count inconsistency needs alignment with module 1, the Й group-sort classification must match the "semivowel" teaching, the тінь/ніч vocab mismatch needs correction, and richness additions (dialogues, tables, proverbs) will close the 47% → 95% gap. No blocking issues prevent a targeted repair pass.
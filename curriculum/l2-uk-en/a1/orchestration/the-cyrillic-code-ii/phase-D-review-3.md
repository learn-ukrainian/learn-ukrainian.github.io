# Рецензія: The Cyrillic Code II

**Reviewed-By:** claude-sonnet-4-6

**Level:** A1 | **Module:** a1-02
**Overall Score:** 8.0/10
**Status:** FAIL
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PASS (with minor gaps)
- Sections: ALL 5 H2 sections present and correctly titled
    «Вступ» ✅ / «Унікальні приголосні» ✅ / «Йотовані голосні та М'який знак» ✅
    / «Голосні та напівголосні» ✅ / «Практика та вимова» ✅
- Vocabulary: 8/8 required words present; 5/6 recommended (ніч missing from vocab file,
    appears in content at line 187 but not lexicalized in vocabulary/the-cyrillic-code-ii.yaml)
  Extras: літо, ми, мій, сіль, тінь, пити, діти (all reasonable from activity exercises)
- Grammar scope: CLEAN — alphabet/phonetics only, no A1-03+ grammar introduced
- Objectives: 4/4 objectives fully addressed
  - Recognize unique consonants (Г, Ґ, Ж, Ш, Щ, Ч, Ц) ✅
  - Identify iotated vowels (Є, Ї, Ю, Я) ✅
  - Understand soft sign (Ь) ✅
  - Distinguish И vs І ✅
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Strong cultural hooks; slightly dense in Section «Унікальні приголосні» (~36 example words before any practice break) |
| 2 | Language | 8/10 | <8 | Ukrainian sentences grammatically clean; colonial framing in one quiz activity item; one abstract-noun stack in intro |
| 3 | Pedagogy | 8/10 | <7 | Solid PPP progression; "Smile vs Grin" technique is excellent; activity item counts below plan (8 items vs 15–20 planned) |
| 4 | Activities | 7/10 | <7 | Excellent type variety (6 types across 8 activities); colonial framing in one quiz question (activities line 122–123); all individual answers accurate |
| 5 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5; warm opening, multiple quick wins, strong closing, ≥3 encouragement phrases |
| 6 | LLM Fingerprint | 8/10 | <7 | No structural monotony; one mild "not just X — Y" pattern (line 36); one 3-noun abstract stack (line 12); no repeated callout types except [!tip]×2 and [!warning]×2 (different content each time) |
| 7 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL**: мій '[mij]' in vocab should be '[mʲij]'; Європа '[jɛu̯ˈrɔpɑ]' in vocab vs [jɛˈʋrɔpɑ] in content; [i̯] vs [j] glide notation inconsistency for чай and гарний across files |

**Weighted Overall:**
```
(8×1.5) + (8×1.1) + (8×1.2) + (7×1.3) + (9×1.3) + (8×1.0) + (8×1.5)
= 12.0 + 8.8 + 9.6 + 9.1 + 11.7 + 8.0 + 12.0
= 71.2 / 8.9 = 8.0/10
```

## Auto-Fail Checklist Results

- Russianisms: CLEAN — no кушати, приймати участь, etc.
- Calques: CLEAN — no робити сенс, брати місце, etc.
- Grammar scope: CLEAN — no post-A1.1 grammar introduced
- Activity errors: ONE issue — quiz question frames Ukrainian identity via Russian contrast
- Beginner safety: 5/5
- Factual accuracy: ONE issue — quiz question's causal framing is less careful than the prose (see Critical Issues)

## Critical Issues Found

### Issue 1: IPA Error — мій Missing Palatalization Mark (Vocabulary File)
- **Location**: `vocabulary/the-cyrillic-code-ii.yaml`, line 61–62
- **Original**: `- ipa: '[mij]'`
- **Problem**: The letter м before і undergoes palatalization in Ukrainian; the IPA should mark the palatalized м with [ʲ]. The content file correctly transcribes this at line 239: «**мій** [mʲij] (my/mine masculine)». The vocabulary file contradicts the content — a learner comparing both files receives conflicting phonological information, and the vocabulary file version is phonologically wrong.
- **Fix**: Change to `- ipa: '[mʲij]'`

### Issue 2: IPA Inconsistency — Європа (Content vs Vocabulary)
- **Location**: `vocabulary/the-cyrillic-code-ii.yaml` line 25–26 vs. content line 138
- **Original (vocab)**: `- ipa: '[jɛu̯ˈrɔpɑ]'`
- **Content**: «**Європа** [jɛˈʋrɔpɑ] (Europe) — A high cultural frequency word.»
- **Problem**: The vocabulary file encodes В as a non-syllabic glide [u̯] producing the initial diphthong [jɛu̯], while the content correctly represents it as the bilabial approximant consonant [ʋ]. These notate the same underlying sound differently, creating cross-file contradiction. For an A1 learner comparing both files, this is confusing and the vocab notation is non-standard.
- **Fix**: Change vocabulary IPA to `'[jɛˈʋrɔpɑ]'` for consistency with the content file

### Issue 3: IPA Glide Notation Inconsistency — чай and гарний (Vocabulary vs Content)
- **Location**: `vocabulary/the-cyrillic-code-ii.yaml` lines 5 and 13
- **Original (vocab чай)**: `- ipa: '[t͡ʃɑi̯]'` | **Content (line 103 and 237)**: `[t͡ʃɑj]`
- **Original (vocab гарний)**: `- ipa: '[ˈɦɑrnɪi̯]'` | **Content (lines 49, 238)**: `[ˈɦɑrnɪj]`
- **Problem**: The vocabulary file uses the non-syllabic [i̯] diacritic for the final palatal glide while the content uses [j]. Both are valid IPA representations of the same phoneme, but systematic inconsistency between the vocabulary file and the content file for the same words will confuse A1 learners who see both. The content notation ([j]) is simpler and more standard for pedagogical IPA.
- **Fix**: Standardize vocabulary to `'[t͡ʃɑj]'` and `'[ˈɦɑrnɪj]'`

### Issue 4: Colonial Framing in Quiz Activity
- **Location**: `activities/the-cyrillic-code-ii.yaml`, lines 122–123
- **Original**: `question: Which letter was repressed in 1933 to make Ukrainian look more like Russian?`
- **Problem**: The question defines the reason for the Ґ ban by positioning Russian as the reference point ("to make Ukrainian look more like Russian"). This is colonial framing — Ukrainian identity is defined by contrast with Russian as baseline. Notably, the main content (line 69) handles this correctly without naming Russian: «This was a deliberate colonial policy to artificially force the Ukrainian language to look and sound identical to other languages in the empire.» The activity introduces what the content deliberately avoided.
- **Fix**: Rephrase to: `question: Which letter was removed from the Ukrainian alphabet by Soviet decree in 1933 and restored in 1990?`

## Ukrainian Language Issues

| Line | File | Current | Corrected | Type |
|------|------|---------|-----------|------|
| 62 | vocabulary | `[mij]` | `[mʲij]` | IPA Error — missing palatalization |
| 25 | vocabulary | `[jɛu̯ˈrɔpɑ]` | `[jɛˈʋrɔpɑ]` | IPA Inconsistency (cross-file) |
| 5 | vocabulary | `[t͡ʃɑi̯]` | `[t͡ʃɑj]` | IPA Inconsistency (glide notation) |
| 13 | vocabulary | `[ˈɦɑrnɪi̯]` | `[ˈɦɑrnɪj]` | IPA Inconsistency (glide notation) |
| 122–123 | activities | «to make Ukrainian look more like Russian» | «removed from the Ukrainian alphabet by Soviet decree in 1933 and restored in 1990» | Colonial Framing |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5

- Overwhelmed? **Pass** — English scaffolding is consistent throughout; Section «Унікальні приголосні» is dense (~36 example words) but logical groupings (Г/Ґ pair, Ж/Ш pair, affricates) reduce cognitive load; the [!warning] callouts break the flow helpfully
- Instructions clear? **Pass** — every activity type, every drill, every section is clearly introduced in English with explicit expectations
- Quick wins? **Pass** — review words at line 20–27 give immediate wins; "you're in excellent shape" (line 27) rewards early effort; drill sections in «Практика та вимова» provide structured success moments
- Ukrainian scary? **Pass** — all Ukrainian text is paired with IPA and English translation; «Давайте зробимо швидку перевірку.» (line 20) is introduced with immediate gloss; no raw Ukrainian without support
- Come back tomorrow? **Pass** — «Молодець! (Well done!)» closing (line 297), "You've officially decoded the entire Cyrillic script" celebration, and the "Перевірте себе" self-check reinforce progress

**Emotional beats present:**
- ≥1 Welcome/orientation: «Привіт! Welcome back to the Ukrainian alphabet!» (line 16) ✅
- ≥1 Curiosity trigger: «Here's where Ukrainian phonetics gets really interesting» (line 130) ✅
- ≥2 Quick wins: lines 27 and 286 ✅
- ≥1 Encouragement/normalizing: «it is completely normal» tip block (line 30) ✅
- ≥1 Progress marker: «You have now encountered every single letter» (line 249) ✅

## Strengths

- **Cultural hooks are outstanding for A1**: The [!history-bite] block on the repressed Ґ (line 68–69) and the [!decolonization] block on Ї as a symbol of resistance (lines 171–172) are pedagogically excellent. They give learners genuine motivation to learn "obscure" letters. The Mariupol graffiti example is viscerally memorable.
- **"Smile vs Grin" technique** (lines 206–210) is an exceptional A1 pedagogical device — it ties abstract phonology to a concrete, memorable physical action learners can self-monitor in a mirror.
- **Activity variety is strong**: 6 different activity types (match-up, group-sort, quiz, fill-in, anagram, true-false) covering the same material from multiple angles prevents rote memorization and accommodates different learning styles.
- **Callout box placement is well-timed**: [!warning] after Г/Ґ introduction (lines 65–67), [!tip] for palatalization (lines 193–195), [!fact] for Й semivowel status (lines 244–245) — each callout appears immediately after introducing the concept it clarifies.
- **IPA coverage in the content file is accurate and consistent** (excluding the vocabulary file issues): 40+ words transcribed, all content-file IPA verified correct.

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. `vocabulary/the-cyrillic-code-ii.yaml` line 62: Change `'[mij]'` → `'[mʲij]'` — removes phonological error (м palatalization before і is standard)
2. `vocabulary/the-cyrillic-code-ii.yaml` line 25: Change `'[jɛu̯ˈrɔpɑ]'` → `'[jɛˈʋrɔpɑ]'` — aligns with content notation and standard pedagogical IPA
3. `vocabulary/the-cyrillic-code-ii.yaml` line 5: Change `'[t͡ʃɑi̯]'` → `'[t͡ʃɑj]'` — standardizes glide notation
4. `vocabulary/the-cyrillic-code-ii.yaml` line 13: Change `'[ˈɦɑrnɪi̯]'` → `'[ˈɦɑrnɪj]'` — standardizes glide notation

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. `activities/the-cyrillic-code-ii.yaml` lines 122–123: Rephrase quiz question away from colonial framing (see Issue 4 above)

**Expected score after fix:** 9/10

### Activities: 7/10 → 8/10
**What to fix:**
1. `activities/the-cyrillic-code-ii.yaml` lines 122–123: Fix colonial framing in quiz question (same fix as Language)

**Expected score after fix:** 8/10

### Projected Overall After Fixes
```
Experience Quality: 8×1.5 = 12.0
Language:          9×1.1 = 9.9
Pedagogy:          8×1.2 = 9.6
Activities:        8×1.3 = 10.4
Beginner Safety:   9×1.3 = 11.7
LLM Fingerprint:   8×1.0 = 8.0
Linguistic Accuracy: 9×1.5 = 13.5

Sum = 75.1 / 8.9 = 8.4/10

No auto-fail dimensions remain.
STATUS AFTER FIXES: PASS
```

## Factual Verification

- Research notes consulted: NOT_APPLICABLE (A1 grammar/phonetics module)
- Key Facts Ledger present: NOT_APPLICABLE
- Dates checked: 1 («from 1933 to 1990» for Ґ ban, line 69 — ACCURATE, historically verified)
- Named figures verified: 0
- Primary quotes cross-referenced: N/A
- Chronological sequence: CONSISTENT
- Claims without research grounding: 0 found

**Callout box factual check (all tracks requirement):**
- [!history-bite] (line 68–69): Ґ banned 1933, restored 1990 — ACCURATE
- [!decolonization] (lines 171–172): Ї graffiti in occupied Mariupol and Kherson 2022 — PLAUSIBLE and consistent with documented resistance practices; no fabrication detected
- [!culture] (line 281–282): Kyiv/Kiev campaign post-independence — ACCURATE
- [!tip] blocks (lines 29–31, 193–195): Pronunciation advice — phonetically sound
- [!warning] blocks (lines 65–67, 228–230): Pronunciation trap descriptions — accurate
- [!observe] (lines 158–159): Euphony claim — accurate characterization of Ukrainian phonology
- [!fact] (lines 244–245): Й as semivowel description — linguistically accurate

## Verification Summary

- Content lines read: 313
- Activity items checked: 62 (across 8 activities)
- Ukrainian sentences verified via Grep: 12 cited sentences, all confirmed verbatim
- IPA transcriptions checked: 47 in content + 20 in vocabulary file
- Factual claims verified: 7 (all callout boxes)
- Issues found: 4 (3 IPA issues, 1 colonial framing)

## Verdict

**FAIL**

Blocking issue: **Linguistic Accuracy auto-fail** — the vocabulary file contains one clear IPA error (мій `[mij]` → `[mʲij]`) and three cross-file IPA inconsistencies (Європа notation, and [i̯] vs [j] glide for чай and гарний). Additionally, a quiz activity question uses colonial framing ("to make Ukrainian look more like Russian") that the main content deliberately avoided. The content prose and IPA in the markdown file are otherwise high quality. All four issues are targeted, low-effort fixes with no content rewriting required.
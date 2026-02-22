**Reviewed-By:** claude-sonnet-4-6

# Рецензія: The Cyrillic Code II

**Level:** A1.1 | **Module:** a1-02
**Overall Score:** 7.9/10
**Status:** FAIL
**Reviewed:** 2026-02-22

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: 5/5 present (Вступ, Унікальні приголосні, Йотовані голосні та М'який знак,
  Голосні та напівголосні, Практика та вимова)
- Vocabulary: 8/8 required words present (центр, чай, школа, гарний, жити, день,
  Європа, яблуко); 6/6 recommended words present
- Grammar scope: CLEAN — no grammar from later modules; phonetics/alphabet only
- Objectives: All 4 learning objectives addressed
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Strong warm opening and closing; section «Унікальні приголосні» is dense (90 lines, 7 consonants, 30+ examples); mechanical Підсумок paragraph (line 307) |
| 2 | Language | 8/10 | <8 | One history-bite hyperbole ("violently removed", line 69); misleading голос/голова note (line 55); IPA inconsistency between vocab YAML and content for Європа |
| 3 | Pedagogy | 8/10 | <7 | Good PPP structure, culturally rich hooks; "quick wins" are concentrated at end rather than distributed; self-check questions at Підсумок are metalinguistically demanding for A1.1 |
| 4 | Activities | 8/10 | <7 | 8 activities, 6 different types — good variety; item counts diverge from plan (plan: 20/quiz, actual: 8/quiz); all content accurate |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5 pass — density of section «Унікальні приголосні» causes borderline overwhelm; module length 3684 words is 84% over target for A1.1 |
| 6 | LLM Fingerprint | 7/10 | <7 | Structural monotony: Ж, Ш, Щ, Ч, Ц all in identical template format (5 consecutive); line 253 purple phrase; Підсумок paragraph is mechanical exhaustive enumeration |
| 7 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL**: vocabulary YAML IPA error: Європа [jɛu̯ˈrɔpɑ] (в incorrectly transcribed as glide u̯, not approximant ʋ); мій [mij] missing palatalization marker; non-standard [ˈr⁽ʲ⁾iʋnɛ] for Рівне in content |

**Weighted Overall:**
```
(8×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 8×1.3 + 7×1.0 + 8×1.5) / 8.9
= (12.0 + 8.8 + 9.6 + 10.4 + 10.4 + 7.0 + 12.0) / 8.9
= 70.2 / 8.9
= 7.9/10
```

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: CLEAN
- Grammar scope: CLEAN — alphabet/phonetics only, no later-module grammar introduced
- Colonial framing: CLEAN — decolonization callout (line 175–176) uses `[!decolonization]` tag, legitimate exception; history-bite vaguely references "other languages in the empire" without naming Russian
- Activity errors: CLEAN — all answers correct, all distractors plausible
- Beginner safety: 4/5 — borderline on "overwhelmed" due to dense consonant section
- Factual accuracy: One hyperbole — "violently removed" (line 69) not supported by research notes; research says "banned" only

## Critical Issues Found

### Issue 1: Vocabulary YAML — IPA Error for Європа (Linguistic Accuracy — AUTO-FAIL)
- **Location**: `vocabulary/the-cyrillic-code-ii.yaml` line 25; cross-reference `the-cyrillic-code-ii.md` line 142
- **Original**: `ipa: '[jɛu̯ˈrɔpɑ]'` (vocabulary YAML)
- **Problem**: Ukrainian в is the labiodental approximant [ʋ], not the non-syllabic glide [u̯]. The vocab file transcribes the "вр" sequence in Європа as a labial glide [u̯] + [r], which misrepresents the consonant to learners. The content file correctly uses `[jɛˈʋrɔpɑ]` (line 142). This internal inconsistency between the two files is a linguistic accuracy failure — a learner comparing both would receive contradictory phonological information.
- **Fix**: Change vocab IPA to `'[jɛˈʋrɔpɑ]'` to match content and standard Ukrainian phonology.

### Issue 2: Vocabulary YAML — IPA Error for мій (Linguistic Accuracy — AUTO-FAIL)
- **Location**: `vocabulary/the-cyrillic-code-ii.yaml` line 61
- **Original**: `ipa: '[mij]'`
- **Problem**: In Ukrainian, м before і is palatalized: мій = [mʲij]. The vocabulary file omits the palatalization superscript [ʲ]. Since this module specifically teaches palatalization via the Soft Sign, omitting the palatalization marker in a vocabulary item for мій directly contradicts the lesson's core phonetic teaching.
- **Fix**: Change to `ipa: '[mʲij]'`

### Issue 3: History-Bite Hyperbole — "violently removed" (Language)
- **Location**: Line 69, Section «Унікальні приголосні», callout `[!history-bite]`
- **Original**: «During the Soviet era, specifically from 1933 to 1990, this letter was officially banned and violently removed from the Ukrainian alphabet.»
- **Problem**: The letter Ґ was removed through an administrative orthographic reform decree (the 1933 "Kharkiv reforms"), not through physical violence. The research notes describe it as "banned from the Ukrainian alphabet" — they do not use the word "violently." Using this word in a factual historical callout is hyperbole that misleads learners about the mechanism of the suppression and overstates a claim that cannot be substantiated.
- **Fix**: Change to «During the Soviet era, specifically from 1933 to 1990, this letter was officially banned and systematically erased from the Ukrainian alphabet.»

### Issue 4: Misleading Pedagogical Note — голос/голова (Language / Beginner Safety)
- **Location**: Line 55, Section «Унікальні приголосні»
- **Original**: «**голос** [ˈɦɔlɔs] (voice) — Notice the similarity to "head" (голова).»
- **Problem**: голос (voice) and голова (head) share the sequence гол- but are unrelated in meaning and have different etymologies (голос from Proto-Slavic *golsъ; голова from *golva). The note invites beginners to draw a connection between "voice" and "head" that does not exist. For A1 learners without Ukrainian context, "similarity to 'head'" implies a semantic or mnemonic link, but actually misleads. The intent appears to be phonetic reinforcement (both start with Г), but the execution creates a false conceptual bridge.
- **Fix**: Remove the reference to голова entirely, or rewrite as: «**голос** [ˈɦɔlɔs] (voice) — Another Г word from this list to reinforce the soft, voiced "h" opening.»

### Issue 5: LLM Fingerprint — Structural Monotony in Consonant Presentations (LLM Fingerprint)
- **Location**: Lines 75–120, Section «Унікальні приголосні»
- **Problem**: Five consonants (Ж, Ш, Щ, Ч, Ц) are each presented in an identical template: **bold letter (Name)** → one-sentence English description → bullet list of 4–6 IPA examples. While Г and Ґ have differentiated presentation, the five remaining consonants are structurally cloned. A learner reading through the section encounters five visually identical blocks in sequence, which signals mechanical generation and can cause reading fatigue. The LLM fingerprint threshold for structural monotony (3+ sections in same format) is met.
- **Fix**: Vary at least 2 of the 5 presentations. For example, group Ж and Ш explicitly as a voiced/unvoiced pair with a comparison table, then present Щ = Ш+Ч visually with a phoneme-splitting diagram. This breaks the repetition while adding pedagogical value.

### Issue 6: Non-Standard IPA Notation — Рівне (Linguistic Accuracy)
- **Location**: Line 219, Section «Голосні та напівголосні»
- **Original**: «**Рівне** [ˈr⁽ʲ⁾iʋnɛ] (Rivne, a Ukrainian city)»
- **Problem**: The notation ⁽ʲ⁾ (superscript palatalization in parentheses) indicates an optional phonetic feature and is non-standard in teaching IPA contexts. It appears in phonological research papers but is inappropriate in A1 beginner materials where learners are learning IPA for the first time. A student would not know how to interpret ⁽ʲ⁾ and has been given no guide to this convention anywhere in the module.
- **Fix**: Simplify to `[ˈriʋnɛ]` (standard unpalatalized) or `[ˈrʲiʋnɛ]` (fully soft), and add a brief note: "The 'r' can sound slightly soft in natural speech."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| vocab line 25 | `'[jɛu̯ˈrɔpɑ]'` | `'[jɛˈʋrɔpɑ]'` | IPA Error — wrong consonant symbol |
| vocab line 61 | `'[mij]'` | `'[mʲij]'` | IPA Error — missing palatalization |
| content line 219 | `[ˈr⁽ʲ⁾iʋnɛ]` | `[ˈriʋnɛ]` | IPA — non-standard notation for A1 |
| content line 69 | «violently removed» | «systematically erased» | English — historical hyperbole |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5

- **Overwhelmed?** BORDERLINE — Section «Унікальні приголосні» runs 90 lines with 7 consonants and 30+ examples before any practice break. An A1.1 beginner who has just learned the alphabet may find this cognitively demanding. Other sections (Йотовані голосні та М'який знак, Голосні та напівголосні) are better paced.
- **Instructions clear?** PASS — Every section explains what to do, translations are provided, IPA is present. No ambiguity.
- **Quick wins?** PASS — The Вступ review (мама, тато, брат, вода) creates immediate success. Practice drills in section «Практика та вимова» provide further wins.
- **Ukrainian scary?** PASS — Ukrainian text is always accompanied by IPA and English translation. Scaffolding is consistently applied.
- **Come back tomorrow?** PASS — Warm closing on line 301 («You've officially decoded the entire Cyrillic script — look how far you've come!») with «Молодець!» provides a strong positive close.

**Emotional safety note**: The «[!tip]» on line 29 («If you hesitated on any of the review words, it is completely normal. Reading a new alphabet takes time...») is an excellent "don't worry" moment that validates anxiety. The module has ≥2 "don't worry" moments and ≥2 "you can do it" moments. Beginner safety is solid overall.

**Module length concern**: 3684 words at A1.1 is 84% over the 2000-word target. For a single study session at this level, this may be too much content. However, since the module is a reference-format phonetics guide (learners can scan rather than read linearly), this does not constitute a hard fail on beginner safety — but should be noted for revision.

## Strengths

- **Cultural framing is excellent**: The `[!history-bite]` callout about Ґ (line 68–69) and the `[!decolonization]` callout about Ї (lines 175–176) are pedagogically strong and culturally appropriate. These hooks give the alphabet linguistic meaning beyond mechanics.
- **Physiological pronunciation guidance**: The "Smile vs Grin" technique (section «Голосні та напівголосні», lines 209–214) is a memorable, concrete physical cue that gives learners a kinesthetic anchor. The palatalization mechanics on lines 183–186 are unusually clear for A1 material.
- **Warm tutor voice throughout**: Section openings are varied and personal. «Три літери left — and they need your full attention» (line 202) is direct and human. The Вступ greeting «Привіт! Welcome back to the Ukrainian alphabet!» (line 16) sets the right tone.
- **Research alignment**: All cultural claims in the module align with the research notes. The Ґ ban dates (1933–1990), the Ї graffiti resistance context, and the State Standard minimal pairs (Рим – Рівне) are all correctly applied.
- **Activity variety**: 8 activities using 6 types (match-up, group-sort, quiz, fill-in, anagram, true-false) across all key letters. The анagram activity and group-sort are appropriate cognitive variety for A1.

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. `vocabulary/the-cyrillic-code-ii.yaml` line 25: Change `ipa: '[jɛu̯ˈrɔpɑ]'` → `ipa: '[jɛˈʋrɔpɑ]'` — eliminates the u̯/ʋ mismatch with content file
2. `vocabulary/the-cyrillic-code-ii.yaml` line 61: Change `ipa: '[mij]'` → `ipa: '[mʲij]'` — adds palatalization to match content file (line 243) and lesson teaching
3. Content line 219: Change `[ˈr⁽ʲ⁾iʋnɛ]` → `[ˈriʋnɛ]` — eliminates non-standard notation

**Expected score after fix:** 9/10 (IPA errors in both files corrected)

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Lines 75–120, Section «Унікальні приголосні»: Break structural monotony in consonant blocks. Group Ж + Ш explicitly as a voiced/unvoiced pair with a compact comparison; keep Щ = Ш+Ч demonstration; this creates 2 distinct presentation formats instead of 5 identical ones.
2. Line 253: Change «Knowledge, however, must be forged into skill through deliberate, conscious practice.» → «Now let's take everything from your head and put it into your mouth.» — informal, matches warm tutor voice
3. Line 307 (Підсумок): Trim the mechanical sequential enumeration of all 6 topics. Two sentences max, focusing on the learner's achievement, not inventory.

**Expected score after fix:** 8/10 (monotony reduced but not eliminated)

### Language: 8/10 → 9/10
**What to fix:**
1. Line 69: Change «officially banned and violently removed» → «officially banned and systematically erased» — removes unsubstantiated hyperbole
2. Line 55: Remove or rewrite the «Notice the similarity to "head" (голова)» note — eliminates misleading semantic implication

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
Linguistic Accuracy: 8 → 9
LLM Fingerprint: 7 → 8
Language: 8 → 9

(8×1.5 + 9×1.1 + 8×1.2 + 8×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9
= (12.0 + 9.9 + 9.6 + 10.4 + 10.4 + 8.0 + 13.5) / 8.9
= 73.8 / 8.9
= 8.3/10 → PASS (all auto-fail thresholds met)
```

## Verification Summary

- Content lines read: 317
- Activity items checked: 8 activities, 62 individual items
- Ukrainian sentences verified: 12 (all inline Ukrainian phrases)
- IPA transcriptions checked: 48 (content) + 20 (vocabulary YAML)
- Factual claims verified: 4 (Ґ ban dates 1933–1990 ✓; Ї graffiti Mariupol 2022 ✓; Kyiv transliteration campaign ✓; "violently removed" ✗ — not in research notes)
- Issues found: 6

## Verdict

**FAIL**

The module fails on one auto-fail threshold: Linguistic Accuracy is 8/10, below the required ≥9, due to IPA errors in the vocabulary YAML file (Європа incorrectly transcribes в as the glide [u̯] rather than the approximant [ʋ]; мій is missing palatalization [mʲij]). These errors in a module specifically teaching palatalization and phonetic precision are directly contradictory. Three targeted fixes are required: correct both vocabulary YAML IPA entries, simplify the non-standard Рівне transcription notation in the content. No prose rewrites are needed for pass.
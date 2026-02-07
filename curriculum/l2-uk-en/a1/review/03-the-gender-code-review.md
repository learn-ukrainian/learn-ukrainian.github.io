# Review: The Gender Code

**Level:** A1 | **Module:** 03
**Overall Score:** 9.6/10
**Status:** PASS
**Reviewed:** 2026-02-07
**Review Prompt:** review-content-core-a v1.0

## Scores Breakdown

| Dimension | Score | Notes |
|-----------|-------|-------|
| Lesson Quality | 10/10 | Warm "secret code" metaphor. "Would I Continue?" 5/5. Caring tutor voice throughout. |
| Coherence | 10/10 | Logical flow: gender rules → why it matters → declension families → practice → culture. |
| Relevance | 10/10 | All 5 plan sections present. Covers 3 genders, 4 declension families, gender prediction rules. |
| Educational | 9/10 | Clear tables, useful examples. One factual error fixed (овочі/фрукти "plural only" claim). |
| Language | 9/10 | Ukrainian correct and natural. English B1-readable and warm. Mini-dialogues feel authentic. |
| Pedagogy | 10/10 | PPP well-executed. Present (gender table) → Practice (families, patterns, dialogues) → Produce (categorization tasks). |
| L1/L2 Balance | 10/10 | 14.5% Ukrainian immersion — within 10-25% target for M03. |
| Activities | 9/10 | 8 activities, 6 types, 113 total items. Schema-valid after YAML wrapper fix. Fill-in sentences in English (acceptable at A1 M03). |
| Richness | 10/10 | 6 engagement callouts (Did You Know, Pop Culture Moment, Real World, Myth Buster, Pro Tip, Folklore Corner). Excellent cultural depth. |
| Beginner Safety | 10/10 | 5/5 "Would I Continue?" test. All emotional beats present. Builds confidence progressively. |
| LLM Fingerprint | 9/10 | Natural tutor voice. "Think of it like a secret code" is engaging and personal. No AI patterns detected. |
| Linguistic Accuracy | 9/10 | State Standard §4.2.1-4.2.3 compliance. Овочі/фрукти error corrected. IPA stress marks fixed in vocabulary. |

## L1/L2 Balance Analysis

- **Target immersion:** 10-25% Ukrainian (M03)
- **Actual immersion:** ~14.5% Ukrainian
- **Assessment:** On target. English scaffolding appropriate for third module. Ukrainian in tables, example words, dialogues, and practice exercises.

## IPA Verification

- Transcriptions checked: 37 (vocabulary file)
- Errors found: 2 (Прип'ять missing stress, Таня stress placement)
- All corrected: Yes

## State Standard Check

- Grammar point: Three-gender system, four declension families
- Standard reference: §4.2.1 (noun gender), §4.2.2 (declension system), §4.2.3 (gender agreement)
- Compliance: Fully compliant after овочі/фрукти correction.

## Beginner Safety Audit

"Would I Continue?" Test:
- Overwhelmed? Pass — gender rules presented as simple pattern recognition
- Instructions clear? Pass — tables, examples, clear categories
- Quick wins? Pass — 95% predictability stat is immediately reassuring
- Ukrainian scary? Pass — introduced through familiar concepts (table, bread, book)
- Come back tomorrow? Pass — "secret code" framing makes it fun
- **Result:** 5/5

Emotional beats found: 6+
- Welcome: Yes ("Have you ever wondered...")
- Curiosity: Yes ("Think of it like a secret code")
- Quick wins: 3+ (95% predictability, S.T.A.L.K.E.R. reference, mini-dialogue)
- Encouragement: 2+ ("Excellent! You've just analyzed 6 nouns like a linguist")
- Progress marker: Yes ("You've unlocked the Ukrainian Gender Code!")

## Issues Found and Fixed

### Issue 1: YAML Activities Wrapper
**Location:** activities/03-the-gender-code.yaml
**Original:** Had frontmatter + `activities:` dictionary wrapper
**Problem:** Schema requires bare list at root
**Fix:** Removed frontmatter and wrapper, made bare list
**Status:** Fixed

### Issue 2: Овочі/Фрукти Described as "Plural Only"
**Location:** Line 122-124 (Pro Tip callout)
**Original:** "Exception: Овочі (vegetables, plural only), фрукти (fruits, plural only)."
**Problem:** Both овоч and фрукт have singular forms. They are NOT pluralia tantum like двері.
**Fix:** Changed to "Watch out: **овоч** (vegetable) and **фрукт** (fruit) are masculine — they end in consonants!"
**Status:** Fixed

### Issue 3: Vocabulary Lemma вина → вино
**Location:** vocabulary/03-the-gender-code.yaml
**Original:** вина (guilt, fault) — feminine
**Problem:** Lesson uses вино (wine, neuter) in Pro Tip but vocabulary had вина (different word, different meaning)
**Fix:** Changed to вино /vɪˈnɔ/ (wine, neuter)
**Status:** Fixed

### Issue 4: Vocabulary Capitalization
**Location:** vocabulary/03-the-gender-code.yaml
**Original:** таня /tˈanja/ — lowercase
**Problem:** Proper name should be capitalized; stress mark placement non-standard
**Fix:** Changed to Таня /ˈtanja/
**Status:** Fixed

### Issue 5: Missing Gender Field
**Location:** vocabulary/03-the-gender-code.yaml
**Original:** фрукт — no gender field
**Problem:** Missing required gender annotation
**Fix:** Added gender: m
**Status:** Fixed

### Issue 6: Missing IPA Stress
**Location:** vocabulary/03-the-gender-code.yaml
**Original:** прип'ять /prɪpjatʲ/
**Problem:** Missing stress mark
**Fix:** Changed to /prɪˈpjatʲ/
**Status:** Fixed

## Verification Summary

- Lines read: 210 (full .md)
- Activity items checked: 113 (8 activities)
- Ukrainian sentences verified: ~25
- English sentences verified: ~80
- IPA transcriptions verified: 37
- Issues found: 6
- Issues fixed: 6

## Recommendation

**PASS** — Strong third module introducing the Ukrainian gender system. Excellent "secret code" framing connecting to previous modules. The 4 declension families overview gives learners a roadmap for future grammar. Six issues fixed (YAML wrapper, factual error about plural-only nouns, vocabulary lemma, capitalization, missing gender, IPA stress). All gates pass.

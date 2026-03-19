# Phase D.2: Targeted Repair

> **You are an expert Ukrainian language editor applying targeted fixes based on a review.**
> The review already applied some fixes. You handle what's still failing.
> You have **Edit** and **Grep** tools — fix files directly.

---

## Ukrainian Alphabet Reference (use when editing letter/sound content)

When fixing content about the Ukrainian alphabet, vowels, or consonants, use these EXACT classifications:
- **10 vowel letters (голосні)**: А, О, У, Е, И, І, Я, Ю, Є, Ї (6 base + 4 iotated)
- **22 consonant letters (приголосні)**: Б, В, Г, Ґ, Д, Ж, З, Й, К, Л, М, Н, П, Р, С, Т, Ф, Х, Ц, Ч, Ш, Щ
- **1 modifier**: Ь (soft sign)
- Common confusions: В is a CONSONANT, І is a VOWEL, Й is a CONSONANT

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original, not less.
- **PRESERVE the author's intent.** If a paragraph explains something poorly, rewrite it to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your rewrite should read like the original author wrote it on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information that cannot be salvaged). This should be rare.

---

## Fix Plan (from Phase D.1 review)



**NOTE: 6 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] MISSING_STRUCTURAL_ELEMENT** in `Голосні та приголосні — Vowels and Consonants`
  - Expected: Plan point requires visual element: Preview chart organized by category (COPY EXACTLY): Голосні (Base): А, О, У, Е, И, І Голосні (Iotate
  - Actual: Section contains only prose — no table or bulleted list found
  - Fix: Add a markdown table or bulleted list to section 'Голосні та приголосні — Vowels and Consonants'

- **[HIGH] MISSING_STRUCTURAL_ELEMENT** in `Перші 10 літер — First 10 Letters`
  - Expected: Plan point requires visual element: Decodable words (use ONLY these 10 letters): мама (mom), тато (dad), кіт (cat), молоко (milk), масло
  - Actual: Section contains only prose — no table or bulleted list found
  - Fix: Add a markdown table or bulleted list to section 'Перші 10 літер — First 10 Letters'

- **[HIGH] MISSING_STRUCTURAL_ELEMENT** in `Підсумок — Summary`
  - Expected: Plan point requires visual element: Self-check: Can you find all 10 vowel letters on the chart? Can you read мама and кіт? What is the d
  - Actual: Section contains only prose — no table or bulleted list found
  - Fix: Add a markdown table or bulleted list to section 'Підсумок — Summary'


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Section "Вступ — Introduction", Throughout, concentrated in sections "Вступ — Introduction", "Голосні та приголосні — Vowels and Consonants", and "Перші 10 літер — First 10 Letters", Whole module, Whole module — all 6 sections, activities/the-ukrainian-alphabet.yaml, fill-in items (lines 127-154), activities/the-ukrainian-alphabet.yaml, line 203

### Finding 1: Zero Engagement Boxes (MEDIUM — audit gate failure)
**Location**: Whole module — all 6 sections
**Problem**: The module has 0 engagement callout boxes (`> [!tip]`, `> [!example]`, `> [!cultural-note]`, `> [!did-you-know]`, etc.). The audit requires minimum 1 for A1, and richness gate needs at least 2. The content is pure prose with no visual breakpoints. This directly causes the richness gate failure (52% < 60%).
**Required Fix**: Add at least 2 callout boxes:
**Severity**: HIGH

### Finding 2: VESUM-Failing Syllable Fragments in Activities (LOW — confirmed false positive)
**Location**: activities/the-ukrainian-alphabet.yaml, fill-in items (lines 127-154)
**Problem**: D.0 pre-scan flagged КІ, ЛО, ЛІ, СЛО, СО as VESUM failures. These are **syllable fragments** in letter-blending exercises (e.g., "К + І → КІ. КІ + Т → ___"), not standalone word answers. The actual answers (мама, кіт, тато, молоко, ліс, сон, мак, місто) are all valid VESUM words.
**Required Fix**: Change explanation on line 203 from "масло = МА+СЛО" to "масло = МАС+ЛО" for correct syllabification.
**Severity**: HIGH

### Finding 3: Adverb/Adjective Stuffing (MEDIUM — LLM fingerprint)
**Location**: Throughout, concentrated in sections "Вступ — Introduction", "Голосні та приголосні — Vowels and Consonants", and "Перші 10 літер — First 10 Letters"
**Problem**: Real tutors use warm, encouraging language but don't stack superlatives in every paragraph. This pattern makes the prose feel AI-generated rather than human-authored.
**Required Fix**: Reduce ~50% of intensifiers. Keep warmth, remove hyperbole. E.g., "One of the best things about Ukrainian..." (drop "absolute"), "organized into two main categories" (drop "elegantly"), etc.
**Severity**: HIGH

### Finding 4: Missing Poster Video from Plan (LOW)
**Location**: Section "Вступ — Introduction"
**Problem**: Plan specifies `poster: https://www.youtube.com/watch?v=grL2s5e2AGI` but this video is not embedded in the content. The overview and playlist links are present (lines 15-16) but the poster video is missing.
**Required Fix**: Add the poster video link alongside the overview and playlist links in section "Вступ — Introduction".
**Severity**: HIGH

### Finding 5: No Inline Examples Formatted as Callouts (MEDIUM — richness gap)
**Location**: Whole module
**Problem**: The richness audit shows `examples: 0/8`. While the module has many inline examples (bold words, blending walkthroughs), none are formatted as `> [!example]` callout blocks that the audit system can detect. The blending walkthrough on lines 95-97 and the micro-dialogues on lines 111-115 would benefit from being in `> [!example]` blocks for visual clarity AND audit compliance.
**Required Fix**: Wrap at least 2 key teaching moments in `> [!example]` callout blocks — the blending walkthrough (lines 95-97) and the micro-dialogues (lines 111-115).
**Severity**: HIGH

### Finding 6: Syllabification Error in Activity Explanation
**Location**: activities/the-ukrainian-alphabet.yaml, line 203
**Problem**: Ukrainian syllabification rules place consonant clusters at syllable boundaries differently. МАС-ЛО is the correct syllabification (consonant С closes the first syllable before Л). While this is a fill-in activity about letter-blending (not syllabification per se), presenting СЛО as a syllable teaches incorrect phonetic intuition.
**Required Fix**: Change to "масло = МА+С+ЛО. It means butter." or simply "масло means butter."
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Zero Engagement Boxes (MEDIUM — audit gate failure)
- **Location**: Whole module — all 6 sections
- **Problem**: The module has 0 engagement callout boxes (`> [!tip]`, `> [!example]`, `> [!cultural-note]`, `> [!did-you-know]`, etc.). The audit requires minimum 1 for A1, and richness gate needs at least 2. The content is pure prose with no visual breakpoints. This directly causes the richness gate failure (52% < 60%).
- **Fix**: Add at least 2 callout boxes:
  1. A `> [!tip]` in section "Перші 10 літер — First 10 Letters" about the Н/H visual trap (currently buried in prose at line 68)
  2. A `> [!did-you-know]` in section "Вступ — Introduction" about Cyrillic's Greek origins (line 5 content could be elevated)

### Issue 2: VESUM-Failing Syllable Fragments in Activities (LOW — confirmed false positive)
- **Location**: activities/the-ukrainian-alphabet.yaml, fill-in items (lines 127-154)
- **Problem**: D.0 pre-scan flagged КІ, ЛО, ЛІ, СЛО, СО as VESUM failures. These are **syllable fragments** in letter-blending exercises (e.g., "К + І → КІ. КІ + Т → ___"), not standalone word answers. The actual answers (мама, кіт, тато, молоко, ліс, сон, мак, місто) are all valid VESUM words.
- **Verdict**: DISMISS — these are intentional pedagogical syllable-building steps, not vocabulary items. The audit flag is a false positive for this activity type. However, the `explanation` field on line 203 uses "МА+СЛО" for масло, which implies СЛО is a syllable — but Ukrainian syllabification would actually be МАС+ЛО. This is a minor phonetic inaccuracy.
- **Fix**: Change explanation on line 203 from "масло = МА+СЛО" to "масло = МАС+ЛО" for correct syllabification.

### Issue 3: Adverb/Adjective Stuffing (MEDIUM — LLM fingerprint)
- **Location**: Throughout, concentrated in sections "Вступ — Introduction", "Голосні та приголосні — Vowels and Consonants", and "Перші 10 літер — First 10 Letters"
- **Original examples**:
  - Line 5: 「The Cyrillic alphabet was originally created way back in the 9th century by the dedicated students of Saints Cyril and Methodius.」 — "way back", "dedicated" are filler
  - Line 7: 「One of the absolute best things about learning Ukrainian is that its spelling system is highly phonetic.」 — "absolute best things" is hyperbolic
  - Line 34: 「The Ukrainian alphabet is elegantly organized into two main, functional categories: vowels and consonants.」 — "elegantly organized" is unnecessarily florid
  - Line 95: 「Now, let us practice blending these letters together to build syllables and eventually full words.」 — fine on its own, but combined with "incredibly powerful tools" (line 51), "incredibly smooth and enjoyable" (line 26), "seamlessly becomes" (line 97), "magically becomes" (line 95) — the hyperbole accumulates
- **Problem**: Real tutors use warm, encouraging language but don't stack superlatives in every paragraph. This pattern makes the prose feel AI-generated rather than human-authored.
- **Fix**: Reduce ~50% of intensifiers. Keep warmth, remove hyperbole. E.g., "One of the best things about Ukrainian..." (drop "absolute"), "organized into two main categories" (drop "elegantly"), etc.

### Issue 4: Missing Poster Video from Plan (LOW)
- **Location**: Section "Вступ — Introduction"
- **Problem**: Plan specifies `poster: https://www.youtube.com/watch?v=grL2s5e2AGI` but this video is not embedded in the content. The overview and playlist links are present (lines 15-16) but the poster video is missing.
- **Fix**: Add the poster video link alongside the overview and playlist links in section "Вступ — Introduction".

### Issue 5: No Inline Examples Formatted as Callouts (MEDIUM — richness gap)
- **Location**: Whole module
- **Problem**: The richness audit shows `examples: 0/8`. While the module has many inline examples (bold words, blending walkthroughs), none are formatted as `> [!example]` callout blocks that the audit system can detect. The blending walkthrough on lines 95-97 and the micro-dialogues on lines 111-115 would benefit from being in `> [!example]` blocks for visual clarity AND audit compliance.
- **Fix**: Wrap at least 2 key teaching moments in `> [!example]` callout blocks — the blending walkthrough (lines 95-97) and the micro-dialogues (lines 111-115).

### Issue 6: Syllabification Error in Activity Explanation
- **Location**: activities/the-ukrainian-alphabet.yaml, line 203
- **Original**: "масло = МА+СЛО. It means butter."
- **Problem**: Ukrainian syllabification rules place consonant clusters at syllable boundaries differently. МАС-ЛО is the correct syllabification (consonant С closes the first syllable before Л). While this is a fill-in activity about letter-blending (not syllabification per se), presenting СЛО as a syllable teaches incorrect phonetic intuition.
- **Fix**: Change to "масло = МА+С+ЛО. It means butter." or simply "масло means butter."

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| — | No Ukrainian language errors found | — | — |

All Ukrainian words (мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні, сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно) verified against VESUM. Sight words (привіт, дякую, це) are correct. Sentence structures (「Це кіт?」, 「Мама тут.」, 「Кіт там.」) are grammatically valid A1 patterns (Це+noun, Noun+тут/там).

---

## Fix Plan to Reach 9.0/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add a `> [!tip]` callout in section "Перші 10 літер — First 10 Letters" about the Н/H false friend (extract from line 68 prose)
2. Add a `> [!did-you-know]` callout in section "Вступ — Introduction" about the 'ough' comparison or Cyrillic origin
3. Add a `> [!example]` block around the blending walkthrough (lines 95-97) for visual breakpoint

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 5: Remove "way back" and "dedicated" — "Cyrillic was created in the 9th century by students of Saints Cyril and Methodius"
2. Line 7: "One of the best things about learning Ukrainian" (drop "absolute")
3. Line 34: "organized into two main categories" (drop "elegantly")
4. Line 51: "These 10 high-frequency letters are powerful tools" (drop "incredibly")
5. Line 95: Remove "magically" from "МА + МА magically becomes мама"
6. Line 97: Remove "seamlessly" from "К + І + Т seamlessly becomes кіт"

**Expected score after fix:** 9/10

### Activities: 7/10 → 8/10
**What to fix:**
1. Line 203 in activities YAML: Fix syllabification in explanation ("МА+СЛО" → "МА+С+ЛО" or remove syllable breakdown)

**Expected score after fix:** 8/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
Same as Language fixes above — reducing intensifier stuffing will address the AI voice pattern.

**Expected score after fix:** 8/10

### Projected Overall After Fixes
(9×1.5 + 9×1.1 + 9×1.2 + 8×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9 = (13.5 + 9.9 + 10.8 + 10.4 + 11.7 + 8.0 + 13.5) / 8.9 = 77.8 / 8.9 = **8.7/10**

---

## Audit Failures (from automated re-audit)

```
✨ Purity violations found: 4
❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (100% overlap): "### Літера Т
❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (100% overlap): "### Літера К
❌ [CONTENT_REDUNDANCY] Redundant information detected in lesson (100% overlap): "### Літера С
❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with '[anna ohoiko...'.
--- STRICT GATES (Level A1) ---
📚 PEDAGOGICAL VIOLATIONS FOUND:
[ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with '[anna ohoiko...'.
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 15/100)
→ 4 violations (moderate)
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/the-ukrainian-alphabet-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `КІ` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-ukrainian-alphabet.md`

```markdown
## Вступ — Introduction

Welcome to your very first step in reading Ukrainian! Are you ready to unlock a whole new world of reading and communication? Ukrainian uses the Cyrillic script, which might look completely unfamiliar at first glance. If you have ever looked at a word like **молоко** (milk) and wondered how on earth to read it, you are in exactly the right place. 

The Cyrillic alphabet was created in the 9th century by students of Saints Cyril and Methodius. It is an adaptation of the Greek alphabet, created specifically to capture the sounds of Slavic languages via the First Bulgarian Empire. This means that Cyrillic is NOT derived from the Latin alphabet you are used to reading in English; instead, it descends directly from the Greek alphabet!

> [!did-you-know]
> Unlike English, where the letters 'ough' can sound five different ways ("though", "through", "tough", "cough", "thought"), Ukrainian is wonderfully consistent — each letter usually maps to just one sound. This predictability will be your greatest asset!

One of the best things about learning Ukrainian is that its spelling system is highly phonetic. Each letter usually maps to just one sound. This predictability will be your greatest asset.

Here is the complete map of the 33-letter Ukrainian alphabet:
А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я

Please do not try to memorize all of these letters right now! We are going to master them step by step. You will master each specific group across our next few modules.

For an overview of everything we are going to cover, watch this introductory video and explore the full playlist:
*   [Anna Ohoiko — Ukrainian Lessons — Poster](https://www.youtube.com/watch?v=grL2s5e2AGI)
*   [Anna Ohoiko — Ukrainian Lessons — Overview](https://www.youtube.com/watch?v=ksXIXj7CXwc)
*   [Anna Ohoiko — Ukrainian Lessons — Playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)

<!-- adapted from: Bolshakova, Grade 1 -->

## Букви і звуки — Letters and Sounds

Before we jump right in and start reading our very first words like **мама** and **тато**, we need to take a moment to understand a crucial linguistic concept. What exactly is the difference between letters and sounds? In the Ukrainian language, letters (**букви**) are simply the written symbols that you see printed on a page or displayed on a screen. Sounds (**звуки**), on the other hand, are the actual acoustic vibrations you hear with your ears and pronounce with your mouth when speaking.

While letters and sounds work together very closely, they are not exactly the same thing. In fact, Ukrainian has 38 unique phonemes (distinct sounds), but there are only 33 letters in its alphabet to represent them all.

This brings us to a key insight: Ukrainian spelling is highly phonetic. One letter almost always represents one specific sound. This makes Ukrainian far easier to read than English could ever hope to be. Once you learn the consistent sounds of the 33 letters, you can reliably sound out practically any word you encounter. If you see a word like **кіт**, you just read the letters one by one, left to right.

There are just a few special exceptions to keep in mind for our future lessons. Some letters do double duty. The iotated vowels (Я, Ю, Є, Ї) can sometimes represent two sounds at the exact same time. Additionally, the soft sign (Ь) is a special modifier that has no sound of its own; it simply changes the pronunciation of the consonant right before it. We will explore those details when we study special signs!

<!-- adapted from: Kravtsova, Grade 3 -->

## Голосні та приголосні — Vowels and Consonants

The Ukrainian alphabet is organized into two main categories: vowels and consonants. Understanding this division right from the start is your first big step toward confident reading.

Let us start with the vowels. Ukrainian has exactly 10 vowel letters. These are clearly divided into 6 base vowels (А, О, У, Е, И, І) and 4 iotated vowels (Я, Ю, Є, Ї). When you pronounce a vowel, you use your voice only. The air flows freely from your lungs and out of your mouth without any obstruction from your lips, your tongue, or your teeth. Here is a golden rule to remember as you practice: every single Ukrainian syllable has exactly one vowel. If a long word has three vowels, like **молоко**, it automatically has three syllables. It is truly that simple!

Next, we have the consonants. There are 22 consonant letters in total, plus the special soft sign (Ь). The soft sign acts purely as a modifier and has absolutely no sound of its own. When you pronounce a consonant, the airflow from your lungs is partially or fully obstructed by your lips, your tongue, or your teeth, creating a distinct, sharp sound.

Here is your preview chart, organized by category:

- **Голосні (Base):** А, О, У, Е, И, І
- **Голосні (Iotated):** Я, Ю, Є, Ї
- **Приголосні:** Б, В, Г, Ґ, Д, Ж, З, Й, К, Л, М, Н, П, Р, С, Т, Ф, Х, Ц, Ч, Ш, Щ
- **Modifier:** Ь

Please remember, you do not need to master vowels, consonants, and special signs today. We will tackle them step by step soon!

## Перші 10 літер — First 10 Letters

Today you start reading in a new language! We are going to focus on our first practice set: just 10 letters. This manageable set includes 4 vowels (А, О, У, І) and 6 consonants (М, Н, Т, К, С, Л). These 10 high-frequency letters will let you read real Ukrainian words immediately.

Let us introduce each letter one by one with some simple pronunciation guidance to help you along. Please watch the short video for each letter to hear exactly how it sounds!

### Літера А
Pronounce this as a clear, open 'a', just like in the English word 'father'.
[Anna Ohoiko — Ukrainian Lessons — А](https://www.youtube.com/watch?v=hvB3VpcR3ZE)

### Літера М
This sounds exactly like the English M. You will use it constantly.
[Anna Ohoiko — Ukrainian Lessons — М](https://www.youtube.com/watch?v=Ez95H4ibuJo)

### Літера О
This is a nicely rounded 'o', similar to the sound in the word 'more'.
[Anna Ohoiko — Ukrainian Lessons — О](https://www.youtube.com/watch?v=gJFxRIPRZbI)

### Літера Н
This sounds like the English N. Warning: it looks like an English H, but it is NOT an H! This is a very common visual trap for beginners.

> [!tip]
> **Visual trap alert!** The Ukrainian letter **Н** looks identical to the English letter H — but it makes the /n/ sound! Similarly, **С** looks like English C but sounds like S. When you see these letters, pause and remember: you are reading Ukrainian now, not English.
[Anna Ohoiko — Ukrainian Lessons — Н](https://www.youtube.com/watch?v=vNUfiKHPYaU)

### Літера У
Pronounce this as an 'oo' sound, just like in the English word 'moon'.
[Anna Ohoiko — Ukrainian Lessons — У](https://www.youtube.com/watch?v=VB1O6PmtYRU)

### Літера Т
This sounds exactly like the English T.
[Anna Ohoiko — Ukrainian Lessons — Т](https://www.youtube.com/watch?v=m-jcLR_gK0k)

### Літера І
Pronounce this as an 'ee' sound, just like in 'see'.
[Anna Ohoiko — Ukrainian Lessons — І](https://www.youtube.com/watch?v=Z9TH0H4ShGo)

### Літера К
This sounds exactly like the English K.
[Anna Ohoiko — Ukrainian Lessons — К](https://www.youtube.com/watch?v=J7sGEI4-xJo)

### Літера С
This sounds exactly like the English S. Try not to confuse it with the English letter C.
[Anna Ohoiko — Ukrainian Lessons — С](https://www.youtube.com/watch?v=7UsFBgSL91E)

### Літера Л
This sounds like the English L, though your tongue position differs slightly.
[Anna Ohoiko — Ukrainian Lessons — Л](https://www.youtube.com/watch?v=v6-3Xg52Buk)

Now, let us practice blending these letters together to build syllables and then full words.

> [!example]
> Take the consonant letter **М** and the vowel letter **А**. Blend them together: you get the syllable **МА**. Now put two of those syllables together: **МА** + **МА** → **мама** (mom).
>
> Try another: take **К** and add **І** → you get **КІ**. Add **Т** at the end: **К** + **І** + **Т** → **кіт** (cat). You are building from letters to syllables to complete words!

Because you know these 10 letters, you can already decode and read all of these words:

- **мама** (mom), **тато** (dad), **кіт** (cat)
- **молоко** (milk), **масло** (butter), **сік** (juice), **сало** (lard)
- **око** (eye), **ніс** (nose)
- **місто** (city), **ліс** (forest), **кіно** (cinema)
- **сон** (dream), **сом** (catfish), **мак** (poppy)
- **стіл** (table), **тут** (here), **там** (there)

## Перші слова — First Words in Context

Now that you can confidently decode words like **місто** and **ліс**, it is time to put them into context. We are going to use a few special words to help us build short, natural sentences. Reading words in isolation is great practice, but reading them in real sentences is where language learning really begins.

First, let us look at some handy decodable survival words. Using only our 10 practice letters, you can easily read **так** (yes) and **ні** (no). These are essential for basic communication.
We also have a few important sight words. These contain untaught letters, so you should recognize them as whole shapes for now without worrying about sounding them out perfectly: **привіт** (hello), **дякую** (thank you), and **це** (this is).

Let us combine these tools into some helpful micro-dialogues. Read these short conversations aloud:

> [!example]
> — Це кіт?
> — Так, це кіт.
>
> — Це місто?
> — Ні, це ліс.

Notice how the word **це** works perfectly to point things out in your environment. Let us try a bit more reading practice with short sentences that mix your fully decodable words and your new sight words. Read slowly and carefully:

*   Мама тут.
*   Кіт там.
*   Це молоко.
*   Це масло.
*   Тато тут.
*   Це сік.

You are officially reading Ukrainian sentences! By starting with these simple structures, you are training your brain to recognize authentic patterns. Whether you are pointing at a **кіт** or asking about a glass of **молоко**, these first words give you a solid foundation for everything that comes next.

## Підсумок — Summary

Let us take a moment to review everything we have learned today. The Ukrainian alphabet contains exactly 33 letters: 10 vowels, 22 consonants, and 1 modifier (Ь). It is a highly phonetic system where each letter reliably maps to one sound.

You learned 10 letters today! You can now confidently read: **мама**, **тато**, **кіт**, **молоко**, **місто**, and **ліс**.

Take a moment for a quick self-check:

- Can you find all 10 vowel letters on the alphabet chart?
- Can you read the words **мама** and **кіт** aloud without hesitation?
- What is the difference between letters (**букви**) and sounds (**звуки**)?

Next up, we will explore the Ukrainian vowel system, covering all 10 vowel letters in detail. Keep going — you are off to a great start!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-ukrainian-alphabet.yaml`

```yaml
- type: watch-and-repeat
  title: "Listen and Repeat the 10 Practice Letters"
  instruction: "Watch each short video, listen carefully to the sound, and repeat it aloud. Pay special attention to letters that look like English letters but sound different!"
  items:
    - letter: "А"
      word: "мама"
      video: "https://www.youtube.com/watch?v=hvB3VpcR3ZE"
      note: "Open 'a' as in 'father'"
    - letter: "М"
      word: "мама"
      video: "https://www.youtube.com/watch?v=Ez95H4ibuJo"
      note: "Like English M"
    - letter: "О"
      word: "око"
      video: "https://www.youtube.com/watch?v=gJFxRIPRZbI"
      note: "Rounded 'o' as in 'more'"
    - letter: "Н"
      word: "ніс"
      video: "https://www.youtube.com/watch?v=vNUfiKHPYaU"
      note: "Looks like English H but sounds like N — a visual trap!"
    - letter: "У"
      word: "тут"
      video: "https://www.youtube.com/watch?v=VB1O6PmtYRU"
      note: "'oo' as in 'moon'"
    - letter: "Т"
      word: "тато"
      video: "https://www.youtube.com/watch?v=m-jcLR_gK0k"
      note: "Like English T"
    - letter: "І"
      word: "кіт"
      video: "https://www.youtube.com/watch?v=Z9TH0H4ShGo"
      note: "'ee' as in 'see'"
    - letter: "К"
      word: "кіт"
      video: "https://www.youtube.com/watch?v=J7sGEI4-xJo"
      note: "Like English K"
    - letter: "С"
      word: "сон"
      video: "https://www.youtube.com/watch?v=7UsFBgSL91E"
      note: "Like English S — looks like English C but sounds like S!"
    - letter: "Л"
      word: "ліс"
      video: "https://www.youtube.com/watch?v=v6-3Xg52Buk"
      note: "Like English L, tongue position differs slightly"

- type: image-to-letter
  title: "What Letter Does the Word Start With?"
  instruction: "Look at the picture. Think of the Ukrainian word for it, then choose the letter it starts with."
  items:
    - emoji: "🐱"
      answer: "К"
      distractors: ["М", "С", "Т"]
      note: "кіт (cat) starts with К"
    - emoji: "🌲"
      answer: "Л"
      distractors: ["Н", "К", "М"]
      note: "ліс (forest) starts with Л"
    - emoji: "👁️"
      answer: "О"
      distractors: ["А", "І", "У"]
      note: "око (eye) starts with О"
    - emoji: "🏙️"
      answer: "М"
      distractors: ["Н", "Т", "С"]
      note: "місто (city) starts with М"
    - emoji: "💤"
      answer: "С"
      distractors: ["Т", "К", "Л"]
      note: "сон (dream) starts with С"
    - emoji: "👨"
      answer: "Т"
      distractors: ["М", "К", "Н"]
      note: "тато (dad) starts with Т"
    - emoji: "👃"
      answer: "Н"
      distractors: ["М", "Л", "С"]
      note: "ніс (nose) starts with Н"
    - emoji: "🥛"
      answer: "М"
      distractors: ["С", "К", "Л"]
      note: "молоко (milk) starts with М"

- type: classify
  title: "Sort the Letters"
  instruction: "Drag each of the 10 practice letters into the correct category. Remember: vowels use your voice only with no obstruction, consonants obstruct the airflow."
  categories:
    - label: "Vowels"
      symbol_hint: "vowel"
      items: ["А", "О", "У", "І"]
    - label: "Consonants"
      symbol_hint: "consonant"
      items: ["М", "Н", "Т", "К", "С", "Л"]

- type: match-up
  title: "Match Each Letter to Its Sound"
  instruction: "Match each Ukrainian letter to the sound it makes. Watch out for visual traps — some letters look like English letters but sound completely different!"
  pairs:
    - left: "А"
      right: "'a' as in father"
    - left: "О"
      right: "'o' as in more"
    - left: "У"
      right: "'oo' as in moon"
    - left: "І"
      right: "'ee' as in see"
    - left: "М"
      right: "/m/ sound (same as English M)"
    - left: "Н"
      right: "/n/ sound (looks like H but is NOT H!)"
    - left: "Т"
      right: "/t/ sound (same as English T)"
    - left: "К"
      right: "/k/ sound (same as English K)"
    - left: "С"
      right: "/s/ sound (looks like C but sounds like S!)"
    - left: "Л"
      right: "/l/ sound (similar to English L)"

- type: fill-in
  title: "Build Words from Letters and Syllables"
  instruction: "Use what you know about blending letters to complete each word-building exercise. Choose the correct result."
  items:
    - sentence: "М + А → МА. МА + МА → ___"
      answer: "мама"
      options: ["мама", "масло", "молоко", "мак"]
      explanation: "Blending М+А gives МА. Two МА syllables make мама (mom)."
    - sentence: "К + І → КІ. КІ + Т → ___"
      answer: "кіт"
      options: ["кіт", "кіно", "там", "тут"]
      explanation: "Blending К+І gives КІ. Adding Т makes кіт (cat)."
    - sentence: "Т + А → ТА. ТА + ТО → ___"
      answer: "тато"
      options: ["тато", "там", "так", "тут"]
      explanation: "Blending Т+А gives ТА. Adding ТО makes тато (dad)."
    - sentence: "М + О → МО. МО + ЛО + КО → ___"
      answer: "молоко"
      options: ["молоко", "масло", "місто", "мама"]
      explanation: "Three syllables МО+ЛО+КО blend into молоко (milk)."
    - sentence: "Л + І → ЛІ. ЛІ + С → ___"
      answer: "ліс"
      options: ["ліс", "ніс", "сік", "стіл"]
      explanation: "Blending Л+І gives ЛІ. Adding С makes ліс (forest)."
    - sentence: "С + О → СО. СО + Н → ___"
      answer: "сон"
      options: ["сон", "сом", "сік", "сало"]
      explanation: "Blending С+О gives СО. Adding Н makes сон (dream)."
    - sentence: "М + А → МА. МА + К → ___"
      answer: "мак"
      options: ["мак", "мама", "масло", "місто"]
      explanation: "Blending М+А gives МА. Adding К makes мак (poppy)."
    - sentence: "М + І → МІ. МІ + С + ТО → ___"
      answer: "місто"
      options: ["місто", "масло", "молоко", "мак"]
      explanation: "Blending М+І gives МІ. Adding СТО makes місто (city)."

- type: quiz
  title: "Read and Identify"
  instruction: "Read the Ukrainian word and choose what it means. Use your knowledge of the 10 practice letters to sound out each word!"
  items:
    - question: "What does the word кіт mean?"
      options:
        - text: "cat"
          correct: true
        - text: "milk"
          correct: false
        - text: "table"
          correct: false
        - text: "forest"
          correct: false
      explanation: "кіт = К+І+Т. It means cat."
    - question: "What does the word молоко mean?"
      options:
        - text: "butter"
          correct: false
        - text: "milk"
          correct: true
        - text: "juice"
          correct: false
        - text: "lard"
          correct: false
      explanation: "молоко = МО+ЛО+КО. It means milk."
    - question: "What does the word ліс mean?"
      options:
        - text: "nose"
          correct: false
        - text: "dream"
          correct: false
        - text: "forest"
          correct: true
        - text: "city"
          correct: false
      explanation: "ліс = Л+І+С. It means forest."
    - question: "What does the word масло mean?"
      options:
        - text: "poppy"
          correct: false
        - text: "city"
          correct: false
        - text: "catfish"
          correct: false
        - text: "butter"
          correct: true
      explanation: "масло = МАС+ЛО. It means butter."
    - question: "Which Ukrainian letter looks like English H but sounds like N?"
      options:
        - text: "Н"
          correct: true
        - text: "М"
          correct: false
        - text: "К"
          correct: false
        - text: "Т"
          correct: false
      explanation: "Н is the biggest visual trap for beginners — it looks like H but makes the /n/ sound."
    - question: "Which Ukrainian letter looks like English C but sounds like S?"
      options:
        - text: "К"
          correct: false
        - text: "Л"
          correct: false
        - text: "С"
          correct: true
        - text: "Т"
          correct: false
      explanation: "С looks like English C but makes the /s/ sound."
    - question: "What does the word стіл mean?"
      options:
        - text: "juice"
          correct: false
        - text: "table"
          correct: true
        - text: "dream"
          correct: false
        - text: "here"
          correct: false
      explanation: "стіл = С+Т+І+Л. It means table."
    - question: "What does the word сік mean?"
      options:
        - text: "lard"
          correct: false
        - text: "poppy"
          correct: false
        - text: "eye"
          correct: false
        - text: "juice"
          correct: true
      explanation: "сік = С+І+К. It means juice."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-ukrainian-alphabet.yaml`

```yaml
items:
  - lemma: "мама"
    translation: "mom"
    pos: "noun"
    gender: "f"
    notes: "Decodable with 10 practice letters. Universal first word."
    usage: "Мама тут."
  - lemma: "тато"
    translation: "dad"
    pos: "noun"
    gender: "m"
    notes: "Decodable with 10 practice letters. High-frequency family word."
    usage: "Тато тут."
  - lemma: "кіт"
    translation: "cat"
    pos: "noun"
    gender: "m"
    notes: "Decodable. Demonstrates blending К+І+Т."
    usage: "Це кіт."
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    gender: "n"
    notes: "Decodable. Three-syllable word showing the one-vowel-per-syllable rule."
    usage: "Це молоко."
  - lemma: "масло"
    translation: "butter"
    pos: "noun"
    gender: "n"
    notes: "Decodable with 10 practice letters."
    usage: "Це масло."
  - lemma: "ліс"
    translation: "forest"
    pos: "noun"
    gender: "m"
    notes: "Decodable. High-frequency word."
    usage: "Це ліс."
  - lemma: "місто"
    translation: "city"
    pos: "noun"
    gender: "n"
    notes: "Decodable. High-frequency word."
    usage: "Це місто."
  - lemma: "око"
    translation: "eye"
    pos: "noun"
    gender: "n"
    notes: "Decodable. Vowel-only start (О+К+О)."
    usage: "Це око."
  - lemma: "так"
    translation: "yes"
    pos: "adverb"
    notes: "Decodable survival word."
    usage: "Так, це кіт."
  - lemma: "ні"
    translation: "no"
    pos: "particle"
    notes: "Decodable survival word."
    usage: "Ні, це не кіт."
  - lemma: "сон"
    translation: "dream, sleep"
    pos: "noun"
    gender: "m"
    notes: "Decodable. Minimal pair with сом."
    usage: "Це сон."
  - lemma: "сом"
    translation: "catfish"
    pos: "noun"
    gender: "m"
    notes: "Decodable. Minimal pair with сон."
  - lemma: "ніс"
    translation: "nose"
    pos: "noun"
    gender: "m"
    notes: "Decodable. Body vocabulary."
  - lemma: "мак"
    translation: "poppy"
    pos: "noun"
    gender: "m"
    notes: "Decodable. Common Ukrainian cultural word."
  - lemma: "сік"
    translation: "juice"
    pos: "noun"
    gender: "m"
    notes: "Decodable. Everyday food word."
  - lemma: "стіл"
    translation: "table"
    pos: "noun"
    gender: "m"
    notes: "Decodable. Everyday object."
  - lemma: "тут"
    translation: "here"
    pos: "adverb"
    notes: "Decodable. High-frequency adverb."
    usage: "Мама тут."
  - lemma: "там"
    translation: "there"
    pos: "adverb"
    notes: "Decodable. High-frequency adverb."
    usage: "Кіт там."
  - lemma: "сало"
    translation: "lard"
    pos: "noun"
    gender: "n"
    notes: "Decodable. Everyday food word."
  - lemma: "кіно"
    translation: "cinema"
    pos: "noun"
    gender: "n"
    notes: "Decodable. Everyday word."
```

---

## Instructions

1. For each issue in the Fix Plan or audit failures, use **Grep** to verify the exact text exists in the file
2. Use the **Edit** tool to fix each issue directly in the file
3. Only fix issues documented above — no silent extra changes
4. Prioritize: audit gate failures first, then review issues

---

## How to Fix

Use the Edit tool for each fix. The workflow for each issue:

1. **Grep** the file to confirm the text exists and is unique
2. **Edit** the file: provide `old_string` (exact text from file) and `new_string` (corrected text)
3. Move to next issue

File paths:
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-ukrainian-alphabet.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-ukrainian-alphabet.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-ukrainian-alphabet.yaml`

## Fix Rules

- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- Do NOT add new prose sections or vocabulary items unless the Fix Plan explicitly requests it
- Maximum **20 edits** total (prioritize the most impactful fixes)
- If nothing needs fixing, state that clearly

---

## Friction Report (MANDATORY)

After all fixes, output:

```
===FRICTION_START===
**Phase**: Phase D.2: Targeted Repair
**Step**: {what you were doing when friction occurred, or "Full Phase D.2"}
**Friction Type**: NONE | EDIT_FAILED | TEXT_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done in Phase D.1
- Do NOT output ===REVIEW_START=== blocks
- Do NOT output FIND/REPLACE blocks — use the Edit tool instead
- You MAY add/modify activities if the Fix Plan requests it
- Do NOT make cosmetic changes beyond what the review flagged

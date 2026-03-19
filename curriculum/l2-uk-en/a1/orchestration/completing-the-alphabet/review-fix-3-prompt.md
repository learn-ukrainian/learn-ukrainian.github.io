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



**NOTE: 10 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] MISSING_STRUCTURAL_ELEMENT** in `Вступ — Introduction`
  - Expected: Plan point requires visual element: Review: M1 gave you the map, M2 mastered vowels, M3 mastered consonants. Today: the final pieces — m
  - Actual: Section contains only prose — no table or bulleted list found
  - Fix: Add a markdown table or bulleted list to section 'Вступ — Introduction'


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Activities file, line 217 (classify activity, Ц category), All H2 sections — lines 19-25, 46-50, 67-68, 76-78, 86-88, 96-97, 104-105, 108-109, Entire module, Entire module — all sections, Lines 7, 18, 45, 54, 121, 136, Vocabulary file — missing entry

### Finding 1: ZERO Engagement Boxes (Audit Gate FAIL)
**Location**: Entire module — all sections
**Problem**: The module contains 0 engagement boxes (`[!tip]`, `[!culture]`, `[!did-you-know]`, `[!example]`). The richness gate requires engagement ≥ 2. This is an audit gate failure.
**Required Fix**: Add at least 2 callout boxes. Suggestions:
**Severity**: HIGH

### Finding 2: "Let us" Formality (×6 occurrences)
**Location**: Lines 7, 18, 45, 54, 121, 136
**Problem**: "Let us" ×6 is formal and robotic. A patient, supportive tutor would say "Let's" — contractions are explicitly permitted in the tier guidance ("Contractions allowed"). This is an LLM fingerprint pattern.
**Required Fix**: Replace all 6 instances of "Let us" with "Let's".
**Severity**: HIGH

### Finding 3: місяць in Activity Without Prose Introduction
**Location**: Activities file, line 217 (classify activity, Ц category)
**Problem**: The word місяць appears in the classify activity under the Ц category but is never mentioned in the prose content and is not in the plan's vocabulary_hints. Students encounter an untaught word in practice.
**Required Fix**: Replace місяць with a word that IS taught in the prose and demonstrates Ц. The prose mentions цукор and цибуля — both already in the activity. Replace місяць with a Ц-word from the content, or add місяць to the prose in section "Африкати, Щ та Ф — Affricates, Щ, and Ф".
**Severity**: HIGH

### Finding 4: Low Immersion (4.4% vs 10-25% target)
**Location**: Entire module
**Problem**: Module 4 falls in the M3-5 band (target 10-25% Ukrainian). Current immersion is 4.4%. The only Ukrainian-language reading passage is the single-line challenge on line 123. The survival phrases on lines 126-130 are isolated words with English translations.
**Required Fix**: Add more Ukrainian reading opportunities: expand the reading challenge, add a second mini-reading passage in section "Апостроф — The Apostrophe", and consider adding short Ukrainian sentences after each example cluster rather than only English explanations.
**Severity**: HIGH

### Finding 5: Identical Example Formatting Across All Sections
**Location**: All H2 sections — lines 19-25, 46-50, 67-68, 76-78, 86-88, 96-97, 104-105, 108-109
**Problem**: Every single section presents examples in the exact same format: `*   **word** (translation) — explanation`. No variation (no tables, no inline examples, no dialogues, no comparison boxes). This is a clear LLM structural monotony pattern.
**Required Fix**: Vary example presentation: use a comparison table for the кін/кінь minimal pair, use inline examples for some words, present the apostrophe words in a formatted box or table with columns for "Without apostrophe" vs "With apostrophe".
**Severity**: HIGH

### Finding 6: фото Missing from Vocabulary File
**Location**: Vocabulary file — missing entry
**Problem**: фото (photo) appears in the prose at line 97 as a vocabulary example for Ф but has no entry in the vocabulary YAML file. It is listed in the plan as a recommended word.
**Required Fix**: Add фото to the vocabulary file.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: ZERO Engagement Boxes (Audit Gate FAIL)
- **Location**: Entire module — all sections
- **Problem**: The module contains 0 engagement boxes (`[!tip]`, `[!culture]`, `[!did-you-know]`, `[!example]`). The richness gate requires engagement ≥ 2. This is an audit gate failure.
- **Fix**: Add at least 2 callout boxes. Suggestions:
  - Section "М'який знак — The Soft Sign": Add `[!tip]` after the minimal pair about кін/кінь — e.g., a tip about listening for soft consonants.
  - Section "Диграфи ДЖ, ДЗ — Digraphs": Add `[!culture]` about the uniqueness of ДЗ to Ukrainian.

### Issue 2: "Let us" Formality (×6 occurrences)
- **Location**: Lines 7, 18, 45, 54, 121, 136
- **Original**: 「Let us look at some everyday examples where the soft sign does its work:」 (line 18), 「Let us look at some very common, everyday words that use this symbol:」 (line 45), 「Let us compare the sounds closely.」 (line 54), 「Let us briefly review the final, crucial pieces of the alphabet puzzle you have just mastered:」 (line 136)
- **Problem**: "Let us" ×6 is formal and robotic. A patient, supportive tutor would say "Let's" — contractions are explicitly permitted in the tier guidance ("Contractions allowed"). This is an LLM fingerprint pattern.
- **Fix**: Replace all 6 instances of "Let us" with "Let's".

### Issue 3: місяць in Activity Without Prose Introduction
- **Location**: Activities file, line 217 (classify activity, Ц category)
- **Problem**: The word місяць appears in the classify activity under the Ц category but is never mentioned in the prose content and is not in the plan's vocabulary_hints. Students encounter an untaught word in practice.
- **Fix**: Replace місяць with a word that IS taught in the prose and demonstrates Ц. The prose mentions цукор and цибуля — both already in the activity. Replace місяць with a Ц-word from the content, or add місяць to the prose in section "Африкати, Щ та Ф — Affricates, Щ, and Ф".

### Issue 4: Low Immersion (4.4% vs 10-25% target)
- **Location**: Entire module
- **Problem**: Module 4 falls in the M3-5 band (target 10-25% Ukrainian). Current immersion is 4.4%. The only Ukrainian-language reading passage is the single-line challenge on line 123. The survival phrases on lines 126-130 are isolated words with English translations.
- **Fix**: Add more Ukrainian reading opportunities: expand the reading challenge, add a second mini-reading passage in section "Апостроф — The Apostrophe", and consider adding short Ukrainian sentences after each example cluster rather than only English explanations.

### Issue 5: Identical Example Formatting Across All Sections
- **Location**: All H2 sections — lines 19-25, 46-50, 67-68, 76-78, 86-88, 96-97, 104-105, 108-109
- **Problem**: Every single section presents examples in the exact same format: `*   **word** (translation) — explanation`. No variation (no tables, no inline examples, no dialogues, no comparison boxes). This is a clear LLM structural monotony pattern.
- **Fix**: Vary example presentation: use a comparison table for the кін/кінь minimal pair, use inline examples for some words, present the apostrophe words in a formatted box or table with columns for "Without apostrophe" vs "With apostrophe".

### Issue 6: фото Missing from Vocabulary File
- **Location**: Vocabulary file — missing entry
- **Problem**: фото (photo) appears in the prose at line 97 as a vocabulary example for Ф but has no entry in the vocabulary YAML file. It is listed in the plan as a recommended word.
- **Fix**: Add фото to the vocabulary file.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 128 | 「**Дякую!** (Thank you!)」 | Acceptable as formulaic phrase — not verb instruction | Scope (mitigated) |
| 129 | 「**Будь ласка!** (Please!)」 | Acceptable as formulaic phrase — not verb instruction | Scope (mitigated) |

Note: D.0 flagged Дякую and Будь as MORPHOLOGICAL_VIOLATION (verbs in pre-verb module). These are confirmed verbs in VESUM (дякувати verb:imperf:pres:s:1, бути verb:imperf:impr:s:2). However, the plan explicitly requires these as survival phrases in section "Весь алфавіт!". They are presented as fixed expressions, not as grammar instruction. The morphological validator correctly identifies the verb forms; the pedagogical context makes them acceptable as formulaic chunks. **Recommendation**: Add a brief English note like "(This is a set phrase — we'll learn verb forms later!)" to preempt learner confusion.

---

## Fix Plan to Reach 9/10 (REQUIRED)

### Experience Quality: 7/10 → 9/10
**What to fix:**
1. Add ≥2 engagement boxes to close the richness gate:
   - After line 33 (кін/кінь section): Add `> [!tip]` about listening for soft vs hard consonants
   - After line 110 (digraphs section): Add `> [!culture]` about ДЗ being uniquely Ukrainian
2. Add a `> [!did-you-know]` in section "Африкати, Щ та Ф" about Ц being one of the most characteristic sounds of Ukrainian

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Lines 7, 18, 45, 54, 121, 136: Replace all "Let us" → "Let's" (6 instances)

**Expected score after fix:** 9/10

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Replace "Let us" ×6 with "Let's" (removes robotic formality pattern)
2. Vary example formatting: convert at least one bullet-list example cluster into a table (e.g., the кін/кінь minimal pair as a comparison table, or apostrophe words as a before/after table)

**Expected score after fix:** 8/10

### Projected Overall After Fixes
```
Experience: 9×1.5=13.5 | Language: 9×1.1=9.9 | Pedagogy: 8×1.2=9.6 |
Activities: 8.5×1.3=11.05 | Safety: 9×1.3=11.7 | LLM: 8×1.0=8.0 | Accuracy: 9×1.5=13.5
Total: 77.25 / 8.9 = 8.7/10
```

---

## Audit Failures (from automated re-audit)

```
⚠️  Outline compliance: 0 errors, 1 warnings
⚠️ [EXTRA_SECTION_IN_MARKDOWN] Section 'Підсумок — Summary' found in markdown but not in outline.
--- STRICT GATES (Level A1) ---
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 1 violations (minor)
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
⚠️  [PRAISE_ONLY_CITATIONS] Review cites 25 Ukrainian passages but ALL are used positively — none highlight problems. A credible review uses citations to show both strengths AND weaknesses. REDO: DELETE the existing review file and regenerate from scratch. Run build_module_v5.py review phase (tier-1-beginner) using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence and stress mark, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/completing-the-alphabet-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `ДЖ` (source: prose)
  ❌ `ДЗ` (source: prose)
  ❌ `ець` (source: prose)
  ❌ `иця` (source: prose)
  ❌ `М'Я` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/completing-the-alphabet.md`

```markdown
## Вступ — Introduction

Welcome back! You have made absolutely incredible progress so far. Here is your journey so far:

- **Module 1** — the big picture and the map of the Ukrainian language
- **Module 2** — mastered the six fundamental vowels
- **Module 3** — conquered the vast landscape of consonants
- **Module 4 (today!)** — the final, exciting pieces of the puzzle

Today, we are putting it all together. We are looking at the special phonetic modifiers like the soft sign (**Ь**) and the apostrophe (**'**), the unique affricate consonants (**Ц**, **Ч**, **Щ**), the dynamic digraphs (**ДЖ**, **ДЗ**), and the somewhat rare letter **Ф**.

These are the final tools you need to unlock the Ukrainian language. Once you finish this module, you will be able to read absolutely any Ukrainian word you see. That is a massive milestone for any language learner! You will be able to sound out street signs in Kyiv, read menus in Lviv, and pronounce the names of new friends perfectly.

Learning a new alphabet can feel like climbing a mountain, but you are now standing right near the peak. You have trained your brain to recognize Cyrillic letters, and you have trained your mouth to produce new sounds. The elements we cover today are the polish—the little details that make your Ukrainian sound authentic and natural. Let's dive in and complete your alphabet journey with confidence!

## М'який знак — The Soft Sign

### Літера Ь
[Anna Ohoiko — Ukrainian Lessons — Ь](https://www.youtube.com/watch?v=cJlal8XKBxo)

Meet the soft sign, written as **Ь**. This letter is entirely unique in the Ukrainian alphabet because it makes absolutely no sound of its own. You cannot pronounce a soft sign by itself in isolation. Instead, it acts purely as a phonetic modifier. Its entire job is to soften, or palatalize, the consonant that comes right before it.

To understand softening, we need to think about where your tongue is inside your mouth. When you pronounce a hard consonant, your tongue is generally relaxed. But for a soft consonant, you press the middle part of your tongue closer to the roof of your mouth, right behind your upper teeth. This physical shift gives the consonant a slightly "lighter," "sweeter," or more delicate quality.

Let's look at some everyday examples where the soft sign does its work. The word **сіль** (salt) has a soft **Л** — you will find it in any Ukrainian kitchen. The word **день** (day) has a soft **Н**, and you will use it in the standard greeting **Добрий день!** (Good day!). And **осінь** (autumn) also has a soft **Н** — a beautiful season in Ukraine, famous for golden leaves and warm colours.

Now try reading these short sentences aloud. Focus on pronouncing the soft consonants:

> Це **сіль**. Добрий **день**! Це **осінь**.

Do you notice a visual pattern here? The **Ь** often appears at the very end of a word, right after a consonant, as we see in **сіль** and **день**. However, it can also appear right in the middle of a word, tucked between two different consonants, to show that the first consonant is soft. In the city name **Львів** (Lviv), the first **Л** is soft — this is the famous, historic western Ukrainian city. In **мідь** (copper), the **Д** is soft.

There is a very strict rule for the soft sign: it will never appear at the beginning of a word, and it will never appear after a vowel. It only ever follows consonants.

To truly appreciate why the soft sign is so critically important, let's look at a minimal pair. A minimal pair is a set of two words that are completely identical except for one single sound.

| Word | Sound | Meaning |
|------|-------|---------|
| **кін** | hard **Н** | a stake in a game |
| **кінь** | soft **Н** (because of **Ь**) | horse |

That one little silent sign changes the physical quality of the preceding consonant, creating an entirely different word! If you drop the soft sign, you might accidentally talk about a wooden stake instead of a beautiful animal.

> [!tip]
> **Listening for softness:** When you hear a Ukrainian word ending in a consonant, ask yourself — does it sound "light" and "sweet," or "firm" and "plain"? That difference is the soft sign at work. Train your ear with pairs like **кін** / **кінь** and **кон** / **конь**!

## Апостроф — The Apostrophe

We have another very special symbol in written Ukrainian: the apostrophe (**'**). While the soft sign softens a consonant, the apostrophe does the exact opposite job. It keeps a consonant hard when it is followed by an iotated vowel (**Я**, **Ю**, **Є**, **Ї**).

In English, an apostrophe usually shows possession (like "John's book") or a contraction (like "don't"). But in Ukrainian, the apostrophe is purely phonetic. It tells your mouth exactly how to behave.

Think back to the iotated vowels. They have a dual function. Normally, when they follow a consonant, they automatically soften that consonant and lose their initial "Y" sound.

But what if we *want* to keep the consonant hard and we also *want* to keep the full "Y" sound of the vowel? That is exactly what the apostrophe is designed for. It acts like a tiny, invisible wall separating the consonant from the vowel.

Let's look at some very common, everyday words that use this symbol:

| Word | Meaning | Apostrophe after | Before vowel |
|------|---------|-----------------|--------------|
| **м'ясо** | meat | М (labial) | Я |
| **п'ять** | five | П (labial) | Я |
| **сім'я** | family | М (labial) | Я |
| **м'яч** | ball | М (labial) | Я |
| **об'єкт** | object | Б (labial) | Є |

There is a strict spelling rule for when the apostrophe appears. It typically shows up after the labial consonants—these are consonants made with your lips, specifically **Б**, **П**, **В**, **М**, and **Ф**—and also after the consonant **Р**, right before the vowels **Я**, **Ю**, **Є**, or **Ї**.

Let's compare the sounds closely. If we were to write the letters **МЯ** without an apostrophe, the **М** would become soft, and the **Я** would just sound like "A". It would sound like "mya" blended smoothly together into one sound.
But with the apostrophe in place, **М'Я** means we pronounce a distinctly hard **М**, followed immediately by the full "Y+A" sound of the vowel **Я**. The apostrophe forces you to pronounce both parts clearly and separately.

What happens without the apostrophe? Compare these pairs:

| Without apostrophe | With apostrophe | Difference |
|---|---|---|
| МЯ → soft М, vowel "A" | **М'Я** → hard М, full "Y+A" | The apostrophe preserves both sounds |
| ПЯ → soft П, vowel "A" | **П'Я** → hard П, full "Y+A" | Without it, the Y-sound disappears |

Remember, the apostrophe is absolutely not optional. It is a mandatory part of spelling these words, and forgetting it changes the pronunciation and the rhythm of the word completely!

Try reading this short passage aloud — every bold word contains an apostrophe:

> Це **сім'я**. Тут **м'ясо** і **п'ять** **м'ячів**. Це **об'єкт**.

Now try a longer passage. Read it slowly and pay attention to the apostrophes:

> Це моя **сім'я**. Тут **м'ясо** і **цибуля**. **П'ять** — це число. Ось **м'яч**. А це **об'єкт**.

## Африкати, Щ та Ф — Affricates, Щ, and Ф

Now let's look at some special consonant sounds that add real texture to the language. First, we will examine the affricates. An affricate is a complex sound made by very quickly combining two separate consonants into one single, explosive sound.

### Літера Ц
[Anna Ohoiko — Ukrainian Lessons — Ц](https://www.youtube.com/watch?v=u44eCjR2Oz8)

The letter **Ц** is a true affricate. It is the perfect, seamless combination of the **Т** sound and the **С** sound, fused together into one sharp burst. It sounds exactly like the "ts" at the end of the English words "cats" or "boots". You will hear it in everyday words like **цукор** (sugar) and **цибуля** (onion).

This letter is incredibly common in Ukrainian, especially in word endings like **-ець** (often marking a person or agent, as in *хлопець*) or **-иця** (as in *вулиця*). It gives the language a crisp, rhythmic quality. Try this sentence: «Тут **цукор** і **цибуля**.» (Here is sugar and onion.)

> [!did-you-know]
> The sound **Ц** is one of the most characteristic sounds of Ukrainian. You will hear it everywhere — in names like **Франко** → **франківець**, in everyday words like **вулиця** (street), and in dozens of common suffixes. It gives Ukrainian its distinctive crisp rhythm.

### Літера Ч
[Anna Ohoiko — Ukrainian Lessons — Ч](https://www.youtube.com/watch?v=UsJkbdsY2RA)

Next is the letter **Ч**, which is another true affricate. It sounds exactly like the "ch" in the English words "church", "cheese", or "catch". This is a very frequent and important sound in spoken Ukrainian. You will hear it in **час** (time/hour), **черепаха** (turtle), and **чай** (tea).

You will use this letter constantly. Try reading this mini-dialogue:

> — **Що** це? (What is this?)
> — Це **чай**. (This is tea.)
> — А це? (And this?)
> — Це **черепаха**! (This is a turtle!)

### Літера Щ
[Anna Ohoiko — Ukrainian Lessons — Щ](https://www.youtube.com/watch?v=QmBLieIuf6Q)

The letter **Щ** looks a bit like the letter **Ц** because of that little tail on the bottom right, but it behaves very differently. **Щ** is not an affricate. Instead, it is a consonant cluster. It represents two completely separate sounds written efficiently as one single letter: **Ш** plus **Ч** (sh + ch). When you say it, you must pronounce both sounds clearly, one right after the other. Listen for it in **що** (what), **ще** (still/more), and **щастя** (happiness).

The little word **що** is a powerhouse. It appears in almost every single Ukrainian conversation you will ever have! Mastering the crisp "sh-ch" sound will instantly make your Ukrainian sound more authentic. Try: «**Що** це? Це **щастя**!» (What is this? This is happiness!)

### Літера Ф
[Anna Ohoiko — Ukrainian Lessons — Ф](https://www.youtube.com/watch?v=haHRsFFZRQI)

Finally in this group, let's look at the letter **Ф**. This letter sounds exactly like the English "f" in "fun" or "family". Interestingly, **Ф** is quite rare in native, historical Ukrainian words. You will mostly see it in words borrowed from other languages or in internationalisms that are recognized worldwide. It serves as the voiceless partner of the letter **В**. Two common examples: **факт** (fact) and **фото** (photo) — both are internationalisms you will recognize instantly.

## Диграфи ДЖ, ДЗ — Digraphs

Ukrainian has two specific sounds that do not have their own single dedicated letters in the alphabet. Instead, they are written using two letters grouped together. These combinations are called digraphs. A digraph is simply two letters that represent one single phoneme, or sound. English uses digraphs all the time, like the "sh" in "shoe" or the "th" in "think".

The first Ukrainian digraph is **ДЖ**. It sounds just like the "j" in the English word "jungle" or the "g" in the word "gem". It is the voiced, vibrating partner of the letter **Ч**. You can hear it in **джерело** (spring, source) and **бджола** (bee) — try saying "jungle" and then saying **джерело** to feel how similar the initial sound is.

The second digraph is **ДЗ**. There is actually no perfect, single-letter English equivalent for this sound. It is a fusion of the **Д** sound and the **З** sound, creating a buzzing "dz" noise. You can hear something similar if you say the "ds" in the English word "kids" or "adds", but in Ukrainian, it is sharper and more unified. It is the voiced partner of the letter **Ц**. This specific sound is uniquely Ukrainian and adds a beautiful buzz to the language. Listen for it in **дзвін** (bell) and **дзеркало** (mirror).

When you see these letters printed together in a word, you must remember to pronounce them as one smooth, continuous sound, not as two separate distinct letters!

Read this passage aloud and listen for the digraphs:

> Тут **джерело**. Там **бджола**. Це **дзвін**. А це **дзеркало**.

> [!culture]
> The sound **ДЗ** is uniquely Ukrainian — you will not find it in most other Slavic languages. Words like **дзвін** (bell) and **дзеркало** (mirror) have a distinctive buzzing quality that is one of the hallmarks of authentic Ukrainian pronunciation.

## Весь алфавіт! — The Full Alphabet Mastered

### Літера Ґ
[Anna Ohoiko — Ukrainian Lessons — Ґ](https://www.youtube.com/watch?v=gNjHqjTW9WQ)

You have truly done it! You now know the complete, 33-letter Ukrainian alphabet from start to finish:
**А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я**

Plus, you know the powerful digraphs **ДЖ** and **ДЗ**, and the rule-enforcing apostrophe (**'**). You have trained your eyes and your voice. Let's celebrate with a comprehensive reading challenge. Read each passage aloud — they use all the special letters, affricates, modifiers, and digraphs you have learned:

> Це **осінь**. Це **факт**. Там **цукор**, **чай**, **м'ясо**, **цибуля**. Тут **джерело**. Це **Львів**. **Що** це? Це **щастя**.

Now try this second passage — it combines apostrophe words with digraphs and affricates:

> Це **сіль** і **цукор**. Тут **м'яч** і **фото**. Там **дзвін** і **дзеркало**. **Що** це? Це **бджола**! А це **черепаха**. Ось **кінь**. Це **осінь** у **Львові**.

Now try a short conversation. Read both parts aloud:

> — **Добрий день!** Як справи?
> — **Дякую**, добре! Що це?
> — Це **чай** і **цукор**. **Будь ласка!**
> — **Дякую!** До побачення!

These are set phrases — we will learn verb forms later! For now, practise them as fixed expressions:
*   **Добрий день!** (Good day!)
*   **Як справи?** (How are you?)
*   **Дякую!** (Thank you!)
*   **Будь ласка!** (Please!)
*   **До побачення!** (Goodbye!)

You have officially unlocked the ability to decode any Ukrainian word you encounter. The reading skills and phonetic awareness you have built from these first four modules are your unshakeable foundation. Everything you learn from here on out—the grammar, the vocabulary, the conversations—will build on this massive, impressive achievement.

## Підсумок — Summary

Let's briefly review the final, crucial pieces of the alphabet puzzle you have just mastered:
*   The soft sign (**Ь**) softens the consonant immediately before it. It has no actual sound of its own.
*   The apostrophe (**'**) acts as a phonetic barrier. It preserves the "Y" sound of iotated vowels and keeps the preceding consonant hard.
*   The letters **Ц** and **Ч** are true affricates, blending two consonant sounds smoothly into one single burst.
*   The letter **Щ** is a unique consonant cluster, representing two separate, distinct sounds: **Ш** plus **Ч**.
*   The pairs **ДЖ** and **ДЗ** are digraphs: two separate letters working together to make one single voiced sound.
*   The letter **Ф** is relatively rare and mostly used in borrowed, international words.

Self-check questions to test your understanding:
1. What exactly does the **Ь** do to the letter that comes right before it?
2. When and why do you use an apostrophe in written Ukrainian?
3. What two specific sounds does the letter **Щ** represent?
4. Can you confidently read any Ukrainian word you see now?

Next up is Module 5, where we will take your reading skills to the next level by exploring syllables and word division!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/completing-the-alphabet.yaml`

```yaml
- type: watch-and-repeat
  title: "Pronunciation Practice"
  instruction: "Watch the video for each letter, then repeat the sound and example word out loud. Focus on the unique sound each letter or combination makes."
  items:
    - letter: "Ь"
      word: "сіль"
      video: "https://www.youtube.com/watch?v=cJlal8XKBxo"
      note: "The soft sign has no sound of its own — it softens the consonant before it. Listen for the soft Л in сіль."
    - letter: "Ц"
      word: "цукор"
      video: "https://www.youtube.com/watch?v=u44eCjR2Oz8"
      note: "Ц is an affricate — Т+С fused into one sharp sound, like 'ts' in 'cats'."
    - letter: "Ч"
      word: "чай"
      video: "https://www.youtube.com/watch?v=UsJkbdsY2RA"
      note: "Ч sounds like 'ch' in 'church'. Very common in Ukrainian."
    - letter: "Щ"
      word: "що"
      video: "https://www.youtube.com/watch?v=QmBLieIuf6Q"
      note: "Щ is two sounds: Ш+Ч (sh+ch). Pronounce both clearly, one after the other."
    - letter: "Ф"
      word: "факт"
      video: "https://www.youtube.com/watch?v=haHRsFFZRQI"
      note: "Ф sounds like English 'f'. Rare in native Ukrainian words — mostly in borrowings."
    - letter: "Ґ"
      word: "Ґ"
      video: "https://www.youtube.com/watch?v=gNjHqjTW9WQ"
      note: "Ґ is a unique Ukrainian letter — a hard G sound, distinct from Г."
    - letter: "ДЖ"
      word: "джерело"
      video: "https://www.youtube.com/watch?v=ksXIXj7CXwc"
      note: "ДЖ is a digraph — two letters, one sound. Like 'j' in 'jungle'."
    - letter: "ДЗ"
      word: "дзвін"
      video: "https://www.youtube.com/watch?v=ksXIXj7CXwc"
      note: "ДЗ is a digraph — two letters, one buzzing sound. Uniquely Ukrainian."
    - letter: "Ь"
      word: "кінь"
      video: "https://www.youtube.com/watch?v=cJlal8XKBxo"
      note: "Compare кінь (horse, soft Н) with кін (stake, hard Н). The soft sign changes the word completely."
    - letter: "Щ"
      word: "щастя"
      video: "https://www.youtube.com/watch?v=QmBLieIuf6Q"
      note: "Practice the Ш+Ч cluster in щастя (happiness). Both sounds must be clear."

- type: classify
  title: "Which Consonant Is Softened?"
  instruction: "Sort these words by which consonant the soft sign (Ь) softens. Some words have no soft sign at all."
  categories:
    - label: "Soft Л"
      items: ["сіль", "Львів"]
    - label: "Soft Н"
      items: ["день", "осінь", "кінь"]
    - label: "Soft Д"
      items: ["мідь"]
    - label: "No Ь"
      items: ["чай", "цукор", "час", "факт"]

- type: image-to-letter
  title: "Which Special Letter?"
  instruction: "Look at the picture and think of the Ukrainian word. Which special letter or digraph does the word contain?"
  items:
    - emoji: "🍬"
      answer: "Ц"
      distractors: ["Ч", "Щ"]
      note: "цукор (sugar) contains the affricate Ц"
    - emoji: "⏰"
      answer: "Ч"
      distractors: ["Ц", "Щ"]
      note: "час (time) contains the affricate Ч"
    - emoji: "🫖"
      answer: "Ч"
      distractors: ["Ц", "Ф"]
      note: "чай (tea) contains the affricate Ч"
    - emoji: "💧"
      answer: "ДЖ"
      distractors: ["ДЗ", "Щ"]
      note: "джерело (spring/source) contains the digraph ДЖ"
    - emoji: "🔔"
      answer: "ДЗ"
      distractors: ["ДЖ", "Ц"]
      note: "дзвін (bell) contains the digraph ДЗ"
    - emoji: "🪞"
      answer: "ДЗ"
      distractors: ["ДЖ", "Ч"]
      note: "дзеркало (mirror) contains the digraph ДЗ"
    - emoji: "🐝"
      answer: "ДЖ"
      distractors: ["ДЗ", "Ц"]
      note: "бджола (bee) contains the digraph ДЖ"
    - emoji: "📷"
      answer: "Ф"
      distractors: ["Х", "В"]
      note: "фото (photo) contains the rare letter Ф"

- type: quiz
  title: "Apostrophe Rules"
  instruction: "Test your understanding of when and why the apostrophe is used in Ukrainian spelling."
  vesum_exempt: true
  items:
    - question: "Which spelling is correct for the word meaning 'meat'?"
      options:
        - text: "м'ясо"
          correct: true
        - text: "мясо"
          correct: false
        - text: "мьясо"
          correct: false
        - text: "м'асо"
          correct: false
      explanation: "The apostrophe separates the labial consonant М from the iotated vowel Я, keeping М hard and preserving the Y+A sound."
    - question: "Which spelling is correct for the word meaning 'five'?"
      options:
        - text: "пять"
          correct: false
        - text: "п'ять"
          correct: true
        - text: "пьять"
          correct: false
        - text: "п'ать"
          correct: false
      explanation: "П is a labial consonant followed by Я, so the apostrophe is required to keep П hard and preserve the full Y+A sound."
    - question: "Which spelling is correct for the word meaning 'family'?"
      options:
        - text: "сімья"
          correct: false
        - text: "сімя"
          correct: false
        - text: "сім'я"
          correct: true
        - text: "сім'а"
          correct: false
      explanation: "The apostrophe appears after М (a labial consonant) before Я. Ukrainian never uses Ь before iotated vowels the way Russian does."
    - question: "Which spelling is correct for the word meaning 'ball'?"
      options:
        - text: "м'яч"
          correct: true
        - text: "мяч"
          correct: false
        - text: "мьяч"
          correct: false
        - text: "м'ач"
          correct: false
      explanation: "М is a labial consonant, and the following vowel is Я — the apostrophe is mandatory."
    - question: "Which spelling is correct for the word meaning 'object'?"
      options:
        - text: "обєкт"
          correct: false
        - text: "об'ект"
          correct: false
        - text: "обьєкт"
          correct: false
        - text: "об'єкт"
          correct: true
      explanation: "The apostrophe appears after Б (a labial consonant) before Є (an iotated vowel)."
    - question: "After which consonants does the apostrophe typically appear?"
      options:
        - text: "Б, П, В, М, Ф, and Р"
          correct: true
        - text: "All consonants"
          correct: false
        - text: "Only Б and П"
          correct: false
        - text: "Only М and В"
          correct: false
      explanation: "The apostrophe appears after labial consonants (Б, П, В, М, Ф) and also after Р, before iotated vowels."
    - question: "What does the apostrophe do in Ukrainian?"
      options:
        - text: "It softens the consonant before it"
          correct: false
        - text: "It keeps the consonant hard and preserves the Y-sound of the vowel"
          correct: true
        - text: "It shows possession, like in English"
          correct: false
        - text: "It doubles the consonant sound"
          correct: false
      explanation: "The apostrophe acts as a barrier — it keeps the preceding consonant hard and lets the iotated vowel keep its full Y-sound."
    - question: "Before which vowels does the apostrophe appear?"
      options:
        - text: "А, О, У, І"
          correct: false
        - text: "Е, И, І, О"
          correct: false
        - text: "Я, Ю, Є, Ї"
          correct: true
        - text: "All vowels"
          correct: false
      explanation: "The apostrophe appears only before iotated vowels — Я, Ю, Є, Ї — which have a Y-sound that would otherwise be absorbed."
    - question: "Which word does NOT need an apostrophe?"
      options:
        - text: "цукор"
          correct: true
        - text: "м'ясо"
          correct: false
        - text: "п'ять"
          correct: false
        - text: "сім'я"
          correct: false
      explanation: "Цукор has no labial consonant followed by an iotated vowel, so no apostrophe is needed."
    - question: "In the word м'ясо, the apostrophe tells you to..."
      options:
        - text: "Soften the М"
          correct: false
        - text: "Pronounce a hard М, then the full Y+A sound of Я"
          correct: true
        - text: "Skip the Я sound entirely"
          correct: false
        - text: "Pronounce М twice"
          correct: false
      explanation: "Without the apostrophe, М+Я would blend into a soft M+A. The apostrophe forces a clear separation: hard М, then full Я (Y+A)."

- type: classify
  title: "Which Affricate or Cluster?"
  instruction: "Sort each word by the special consonant it contains: the affricate Ц, the affricate Ч, or the consonant cluster Щ."
  categories:
    - label: "Ц"
      items: ["цукор", "цибуля"]
    - label: "Ч"
      items: ["час", "чай", "черепаха"]
    - label: "Щ"
      items: ["що", "ще", "щастя"]

- type: fill-in
  title: "Complete the Phrase"
  instruction: "Fill in the missing word to complete each Ukrainian survival phrase."
  items:
    - sentence: "Complete the greeting meaning 'Good day!': Добрий ___!"
      answer: "день"
      options: ["день", "ніч", "ранок", "час"]
      explanation: "Добрий день! is the standard daytime greeting in Ukrainian."
    - sentence: "Complete the question meaning 'How are you?': Як ___?"
      answer: "справи"
      options: ["справи", "день", "тут", "там"]
      explanation: "Як справи? literally means 'How are things?' — the standard way to ask how someone is."
    - sentence: "Complete the phrase meaning 'Please!': Будь ___!"
      answer: "ласка"
      options: ["ласка", "день", "добре", "тут"]
      explanation: "Будь ласка! literally means 'Be kind!' — the standard way to say 'please'."
    - sentence: "Complete the phrase meaning 'Goodbye!': До ___!"
      answer: "побачення"
      options: ["побачення", "день", "ранок", "ніч"]
      explanation: "До побачення! literally means 'Until the seeing!' — the standard farewell."
    - sentence: "Complete the question meaning 'What is this?': ___ це?"
      answer: "Що"
      options: ["Що", "Як", "Де", "Хто"]
      explanation: "Що це? means 'What is this?' — one of the most common questions in Ukrainian."
    - sentence: "Complete the answer meaning 'This is tea.': Це ___."
      answer: "чай"
      options: ["чай", "час", "що", "ще"]
      explanation: "Це чай. — a simple Це + noun statement using the word for tea."

- type: match-up
  title: "Match the Survival Phrase"
  instruction: "Match each Ukrainian phrase to its English meaning."
  pairs:
    - left: "Добрий день!"
      right: "Good day!"
    - left: "Як справи?"
      right: "How are you?"
    - left: "Дякую!"
      right: "Thank you!"
    - left: "Будь ласка!"
      right: "Please!"
    - left: "До побачення!"
      right: "Goodbye!"
    - left: "Що це?"
      right: "What is this?"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/completing-the-alphabet.yaml`

```yaml
items:
  - lemma: "сіль"
    translation: "salt"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ь softening the Л. Everyday kitchen word."
  - lemma: "день"
    translation: "day"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Ь softening the Н. Top 50 word."
    usage: "Добрий день!"
  - lemma: "Львів"
    translation: "Lviv"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Ь before a consonant (soft Л). Historic western Ukrainian city."
  - lemma: "м'ясо"
    translation: "meat"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates the apostrophe after labial М before Я."
  - lemma: "п'ять"
    translation: "five"
    pos: "numeral"
    notes: "Demonstrates the apostrophe after labial П before Я."
  - lemma: "сім'я"
    translation: "family"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates the apostrophe after labial М before Я. High-frequency word."
  - lemma: "цукор"
    translation: "sugar"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates the affricate Ц. Everyday kitchen word."
  - lemma: "час"
    translation: "time; hour"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates the affricate Ч. Top 100 word."
  - lemma: "що"
    translation: "what"
    pos: "pronoun"
    notes: "Demonstrates the consonant cluster Щ. Top 10 word. Used in Що це?"
  - lemma: "джерело"
    translation: "spring; source"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates the ДЖ digraph."
  - lemma: "дзвін"
    translation: "bell"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates the ДЗ digraph. Culturally significant (church bells)."
  - lemma: "осінь"
    translation: "autumn"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ь softening the Н. Seasonal vocabulary."
  - lemma: "м'яч"
    translation: "ball"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates the apostrophe after labial М before Я."
  - lemma: "щастя"
    translation: "happiness"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates the consonant cluster Щ. High-frequency word."
  - lemma: "факт"
    translation: "fact"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates the rare letter Ф. An internationalism."
  - lemma: "бджола"
    translation: "bee"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates the ДЖ digraph. Nature vocabulary."
  - lemma: "дзеркало"
    translation: "mirror"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates the ДЗ digraph. Everyday object."
  - lemma: "черепаха"
    translation: "turtle"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates the affricate Ч. Common in children's literature."
  - lemma: "чай"
    translation: "tea"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates the affricate Ч. High-frequency word."
  - lemma: "фото"
    translation: "photo"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates the rare letter Ф. An internationalism. Indeclinable."
  - lemma: "кінь"
    translation: "horse"
    pos: "noun"
    gender: "m"
    notes: "Minimal pair with кін (stake). Demonstrates how Ь changes word meaning."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/completing-the-alphabet.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/completing-the-alphabet.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/completing-the-alphabet.yaml`

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

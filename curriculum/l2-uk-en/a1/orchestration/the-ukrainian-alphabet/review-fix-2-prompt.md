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



**NOTE: 7 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] MISSING_STRUCTURAL_ELEMENT** in `Вступ — Introduction`
  - Expected: Plan point requires visual element: Show the full 33-letter alphabet chart (COPY EXACTLY): А Б В Г Ґ Д Е Є Ж З И І Ї Й К Л М Н О П Р С Т
  - Actual: Section contains only prose — no table or bulleted list found
  - Fix: Add a markdown table or bulleted list to section 'Вступ — Introduction'


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Line 1, Section "Вступ — Introduction", Line 177, Section "Підсумок — Summary", Line 4, Section "Вступ — Introduction", Lines 27-28, Section "Букви і звуки — Letters and Sounds", Lines 38, 42, 168 — Sections "Голосні та приголосні — Vowels and Consonants" and "Підсумок — Summary", Lines 64-102, Section "Перші 10 літер — First 10 Letters", Section "Вступ — Introduction" — not present

### Finding 1: System Artifact on Line 1 (CRITICAL)
**Location**: Line 1, Section "Вступ — Introduction"
**Problem**: Build system artifact left in the content file. Renders as visible text. Also triggered IPA_BANNED pre-screen flag.
**Required Fix**: Delete the entire line.
**Severity**: HIGH

### Finding 2: Wrong Stress on приголосні (HIGH — 3 occurrences)
**Location**: Lines 38, 42, 168 — Sections "Голосні та приголосні — Vowels and Consonants" and "Підсумок — Summary"
**Problem**: Stress is on the wrong syllable. Correct stress is при́голосні (stress on при-). Confirmed by pre-screen STRESS_MISMATCH. This is a critical linguistic error in a module teaching letter fundamentals — wrong stress from lesson 1 will fossilize.
**Required Fix**: Replace all 3 instances of приголо́сні with при́голосні.
**Severity**: HIGH

### Finding 3: IPA Notation on Lines 27-28 (HIGH)
**Location**: Lines 27-28, Section "Букви і звуки — Letters and Sounds"
**Problem**: Uses IPA-style forward-slash notation /m/ and /a/, which is banned per project rules. The rest of the module correctly uses «» (e.g., line 64: 「The letter А makes an open «a» sound」). Inconsistent.
**Required Fix**: Change `/m/` to `«m»` and `/a/` to `«a»` to match the convention used in section "Перші 10 літер — First 10 Letters".
**Severity**: HIGH

### Finding 4: LLM Filler in Opening (MEDIUM)
**Location**: Line 4, Section "Вступ — Introduction"
**Problem**: "We are so incredibly excited" is generic AI enthusiasm. "In this module, we will explore" is formulaic LLM opener (confirmed by D.0 pre-screen). A real tutor would say something more direct and personal.
**Required Fix**: Rewrite opening to be warm but direct: "Welcome to your very first step in learning Ukrainian! Today, you'll meet the Ukrainian alphabet."
**Severity**: HIGH

### Finding 5: Missing Poster Video (MEDIUM)
**Location**: Section "Вступ — Introduction" — not present
**Problem**: Plan specifies `pronunciation_videos.poster: https://www.youtube.com/watch?v=grL2s5e2AGI` but this video is not embedded in the content. The overview video is present (line 12) but the poster video is missing.
**Required Fix**: Add poster video embed after the overview video or in section "Перші 10 літер — First 10 Letters".
**Severity**: HIGH

### Finding 6: Structural Monotony in Letter Introductions (MEDIUM)
**Location**: Lines 64-102, Section "Перші 10 літер — First 10 Letters"
**Problem**: Uniform structure across 8 entries creates LLM fingerprint. Only Н and С break the pattern with `[!warning]` callouts. Real tutors vary their presentation.
**Required Fix**: Vary 2-3 letter introductions — e.g., lead with the word example for some ("Listen to the word **ма́ма** — hear that first sound? That's М!"), or group similar-to-English letters together in a quick list rather than individual entries.
**Severity**: HIGH

### Finding 7: Overpromising Closing (LOW)
**Location**: Line 177, Section "Підсумок — Summary"
**Problem**: Module 1 of 64 — claiming "well on your way to fluency" is misleading and could set false expectations that lead to discouragement later.
**Required Fix**: Replace with something honest: "You've taken your first step — and it's a big one!"
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: System Artifact on Line 1 (CRITICAL)
- **Location**: Line 1, Section "Вступ — Introduction"
- **Original**: 「[watchdog] Output resumed after 219s stall」
- **Problem**: Build system artifact left in the content file. Renders as visible text. Also triggered IPA_BANNED pre-screen flag.
- **Fix**: Delete the entire line.

### Issue 2: Wrong Stress on приголосні (HIGH — 3 occurrences)
- **Location**: Lines 38, 42, 168 — Sections "Голосні та приголосні — Vowels and Consonants" and "Підсумок — Summary"
- **Original**: 「**приголо́сні**」
- **Problem**: Stress is on the wrong syllable. Correct stress is при́голосні (stress on при-). Confirmed by pre-screen STRESS_MISMATCH. This is a critical linguistic error in a module teaching letter fundamentals — wrong stress from lesson 1 will fossilize.
- **Fix**: Replace all 3 instances of приголо́сні with при́голосні.

### Issue 3: IPA Notation on Lines 27-28 (HIGH)
- **Location**: Lines 27-28, Section "Букви і звуки — Letters and Sounds"
- **Original**: 「The letter **м** makes the sound /m/」 and 「The letter **а** makes the sound /a/」
- **Problem**: Uses IPA-style forward-slash notation /m/ and /a/, which is banned per project rules. The rest of the module correctly uses «» (e.g., line 64: 「The letter А makes an open «a» sound」). Inconsistent.
- **Fix**: Change `/m/` to `«m»` and `/a/` to `«a»` to match the convention used in section "Перші 10 літер — First 10 Letters".

### Issue 4: LLM Filler in Opening (MEDIUM)
- **Location**: Line 4, Section "Вступ — Introduction"
- **Original**: 「We are so incredibly excited to have you here to start this journey. In this module, we will explore the Ukrainian alphabet.」
- **Problem**: "We are so incredibly excited" is generic AI enthusiasm. "In this module, we will explore" is formulaic LLM opener (confirmed by D.0 pre-screen). A real tutor would say something more direct and personal.
- **Fix**: Rewrite opening to be warm but direct: "Welcome to your very first step in learning Ukrainian! Today, you'll meet the Ukrainian alphabet."

### Issue 5: Missing Poster Video (MEDIUM)
- **Location**: Section "Вступ — Introduction" — not present
- **Problem**: Plan specifies `pronunciation_videos.poster: https://www.youtube.com/watch?v=grL2s5e2AGI` but this video is not embedded in the content. The overview video is present (line 12) but the poster video is missing.
- **Fix**: Add poster video embed after the overview video or in section "Перші 10 літер — First 10 Letters".

### Issue 6: Structural Monotony in Letter Introductions (MEDIUM)
- **Location**: Lines 64-102, Section "Перші 10 літер — First 10 Letters"
- **Original**: 8 of 10 letters follow identical pattern "The letter X [makes/sounds/looks] like..." 
- **Problem**: Uniform structure across 8 entries creates LLM fingerprint. Only Н and С break the pattern with `[!warning]` callouts. Real tutors vary their presentation.
- **Fix**: Vary 2-3 letter introductions — e.g., lead with the word example for some ("Listen to the word **ма́ма** — hear that first sound? That's М!"), or group similar-to-English letters together in a quick list rather than individual entries.

### Issue 7: Overpromising Closing (LOW)
- **Location**: Line 177, Section "Підсумок — Summary"
- **Original**: 「You are well on your way to fluency!」
- **Problem**: Module 1 of 64 — claiming "well on your way to fluency" is misleading and could set false expectations that lead to discouragement later.
- **Fix**: Replace with something honest: "You've taken your first step — and it's a big one!"

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 38 | 「приголо́сні」 | при́голосні | Stress error |
| 42 | 「приголо́сні」 | при́голосні | Stress error |
| 168 | 「приголо́сні」 | при́голосні | Stress error |
| 27 | /m/ | «m» | IPA banned |
| 28 | /a/ | «a» | IPA banned |

---

## Fix Plan to Reach 9/10 (REQUIRED — score < 9.0)

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Lines 38, 42, 168: Change 「приголо́сні」 → при́голосні — wrong stress fossilizes bad pronunciation from lesson 1
2. Lines 27-28: Change /m/ and /a/ to «m» and «a» — IPA banned, inconsistent with rest of module
3. Line 1: Remove 「[watchdog] Output resumed after 219s stall」 — system artifact

**Expected score after fix:** 9/10

### Language: 7/10 → 9/10
**What to fix:**
1. Fix the 3 stress errors (same as Linguistic Accuracy above — primary blocker)
2. Fix IPA notation (same as above)

**Expected score after fix:** 9/10 (stress and IPA were the only issues)

### LLM Fingerprint: 7/10 → 8/10
**What to fix:**
1. Line 4: Rewrite opening to remove 「We are so incredibly excited to have you here」 and 「In this module, we will explore」
2. Lines 64-102: Vary 2-3 letter introductions in section "Перші 10 літер — First 10 Letters" to break the uniform "The letter X..." pattern
3. Line 177: Replace 「You are well on your way to fluency!」 with honest encouragement

**Expected score after fix:** 8/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add poster video from plan
2. Add 2 more engagement callouts (currently 3/5 per richness gaps) — e.g., a `[!did-you-know]` about why Ukrainian has both І and И, and a `[!culture]` about the word мама being universal
3. Add 1 table (richness gap: tables 0/2) — e.g., a comparison table of the 10 practice letters showing letter, sound, and example word

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 8×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 10.4 + 11.7 + 8.0 + 13.5) / 8.9
= 77.8 / 8.9
= 8.7/10
```

---

## Audit Failures (from automated re-audit)

```
--- STRICT GATES (Level A1) ---
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

Welcome to your very first step in learning the Ukrainian language! Today, you'll meet the Ukrainian alphabet. Ukrainian uses the Cyrillic script, a writing system with a fascinating and rich history. It descended directly from the Greek alphabet and was created by students of Saints Cyril and Methodius during the First Bulgarian Empire. This means it is NOT derived from Latin, and it is also not the Russian alphabet. Ukrainian has its own beautiful, complete set of 33 letters.

> [!culture] Cyrillic Origins
> Cyrillic was created by students of Saints Cyril and Methodius. It is NOT derived from Latin — it descends directly from the Greek alphabet.

The great news for you as a beginner? This 33-letter system is highly phonetic. Unlike English, where a combination like 'ough' can be pronounced five different ways, in Ukrainian, each letter usually maps to just one sound.

Watch this quick overview to hear the sounds of the alphabet:
[Anna Ohoiko — Ukrainian Lessons — Overview](https://www.youtube.com/watch?v=ksXIXj7CXwc)

And here is a beautiful alphabet poster video to see all the letters together:
[Ukrainian Alphabet Poster](https://www.youtube.com/watch?v=grL2s5e2AGI)

Here is your map to reading Ukrainian—the full 33-letter alphabet:

| | | | | | | | | | | |
|---|---|---|---|---|---|---|---|---|---|---|
| А | Б | В | Г | Ґ | Д | Е | Є | Ж | З | И |
| І | Ї | Й | К | Л | М | Н | О | П | Р | С |
| Т | У | Ф | Х | Ц | Ч | Ш | Щ | Ь | Ю | Я |

Please do not worry about memorizing all of these today! We will master each group of letters step by step in the coming modules. For now, just take a look and get familiar with the shapes. Let's get started!

## Букви і звуки — Letters and Sounds

When learning to read a new language, it is very important to clearly understand the difference between letters and sounds. In Ukrainian, letters (**бу́кви**) are the written symbols you see printed on the page. Sounds (**зву́ки**) are what you hear when someone speaks and what you pronounce aloud. They are not exactly the same thing. In fact, while the Ukrainian alphabet has 33 letters, the spoken language has 38 distinct phonemes.

However, you will find a key insight that makes your journey much easier: Ukrainian spelling is incredibly phonetic. One letter almost always represents exactly one sound. This makes Ukrainian far easier to read than English! Once you learn how these 33 letters sound, you will be able to sound out almost any word you encounter. You will not have to guess if a letter is silent or if it suddenly changes its sound.

Here is how simple it is in practice:
*   The letter **м** makes the sound «m»
*   The letter **а** makes the sound «a»
*   Together they always read as **ма**

> [!tip] Phonetic Reading
> Once you know the sounds of the letters, you can pronounce words even if you don't know what they mean yet!

There are a few special cases to keep in mind for later. Some letters do double duty. The iotated vowels (Я, Ю, Є, Ї) can sometimes represent two sounds at once. Also, the soft sign (Ь) is a special modifier letter that has no sound of its own; instead, it modifies the consonant right before it. We will cover those details in module 2 and module 4. Today, your only job is to understand that **бу́кви** and **зву́ки** work together to create a beautifully logical reading system.

## Голосні та приголосні — Vowels and Consonants

To understand the 33 letters better, we need to divide them into helpful categories. Just like in English, Ukrainian letters are grouped into vowels (**голосні́**) and consonants (**при́голосні**).

When you pronounce vowels (**голосні́**), your voice flows freely without any obstruction from your lips, teeth, or tongue. Ukrainian has 10 vowel letters. These are divided into 6 base vowels (А, О, У, Е, И, І) and 4 iotated vowels (Я, Ю, Є, Ї). Remember this golden rule of reading Ukrainian: every single Ukrainian syllable must have exactly one vowel. This simple rule makes breaking words down into syllables very straightforward.

When you pronounce consonants (**при́голосні**), the air is obstructed by your lips, tongue, or teeth. Ukrainian has 22 consonant letters. Additionally, there is one special modifier letter, the soft sign (Ь), which has no sound of its own but changes how we pronounce the consonant before it.

Let's look at how vowels and consonants work in real words:
*   **ма́ма** (mom) — 2 consonants (м, м) + 2 vowels (а, а) = 2 syllables
*   **кіт** (cat) — 2 consonants (к, т) + 1 vowel (і) = 1 syllable
*   **молоко́** (milk) — 3 consonants (м, л, к) + 3 vowels (о, о, о) = 3 syllables

Let's look at the preview chart organized by category:

Голосні (Base): А, О, У, Е, И, І
Голосні (Iotated): Я, Ю, Є, Ї
Приголосні: Б, В, Г, Ґ, Д, Ж, З, Й, К, Л, М, Н, П, Р, С, Т, Ф, Х, Ц, Ч, Ш, Щ
Modifier: Ь

Do not feel overwhelmed! You do not need to memorize this chart right now. In module 2 we will master the vowels, in module 3 the consonants, and in module 4 the special signs.

## Перші 10 літер — First 10 Letters

Today, you are going to learn your first 10 letters. Yes, you will be reading real Ukrainian words by the end of this section! Our practice set includes 4 vowels (А, О, У, І) and 6 consonants (М, Н, Т, К, С, Л). These are high-frequency letters that let you read real Ukrainian words immediately. Let's look at them one by one.

Here is a quick-reference table for all 10 practice letters:

| Letter | Sound | Like English... | Example Word |
|--------|-------|-----------------|--------------|
| А | «a» | «a» in «father» | **ма́ма** (mom) |
| О | «o» | «o» in «more» | **молоко́** (milk) |
| У | «u» | «oo» in «moon» | **тут** (here) |
| І | «i» | «ee» in «see» | **кіт** (cat) |
| М | «m» | M | **ма́ма** (mom) |
| Н | «n» | ⚠️ Looks like H! | **ніс** (nose) |
| Т | «t» | T | **та́то** (dad) |
| К | «k» | K | **кіт** (cat) |
| С | «s» | ⚠️ Looks like C! | **сон** (dream) |
| Л | «l» | L (tongue differs) | **ліс** (forest) |

Now let's meet each letter up close. First, the four vowels — the heart of every syllable:

**Літера А**
[Anna Ohoiko — Ukrainian Lessons — А](https://www.youtube.com/watch?v=hvB3VpcR3ZE)
The letter А makes an open «a» sound, just like the «a» in the English word «father».

**Літера О**
[Anna Ohoiko — Ukrainian Lessons — О](https://www.youtube.com/watch?v=gJFxRIPRZbI)
The letter О makes a rounded «o» sound, similar to «more».

**Літера У**
[Anna Ohoiko — Ukrainian Lessons — У](https://www.youtube.com/watch?v=VB1O6PmtYRU)
The letter У sounds like the «oo» in «moon».

**Літера І**
[Anna Ohoiko — Ukrainian Lessons — І](https://www.youtube.com/watch?v=Z9TH0H4ShGo)
The letter І sounds like the «ee» in «see».

> [!did-you-know] І and И — Two Different Letters!
> Ukrainian has both **І** (sounds like «ee») and **И** (a sound between «i» and «e» that doesn't exist in English). They are completely different letters with different sounds. You'll meet И in module 2!

Now the six consonants. Some look like their English twins — but watch out for the false friends!

**Літера М**
[Anna Ohoiko — Ukrainian Lessons — М](https://www.youtube.com/watch?v=Ez95H4ibuJo)
Listen to the word **ма́ма** — hear that first sound? That's М! It looks and sounds just like the English M.

**Літера Н**
[Anna Ohoiko — Ukrainian Lessons — Н](https://www.youtube.com/watch?v=vNUfiKHPYaU)
> [!warning] False Friend
> The letter Н looks exactly like an English H, but it is NOT an H! It makes an «n» sound, like in «no».

**Літера Т** and **Літера К** — two easy wins:
[Anna Ohoiko — Ukrainian Lessons — Т](https://www.youtube.com/watch?v=m-jcLR_gK0k) | [Anna Ohoiko — Ukrainian Lessons — К](https://www.youtube.com/watch?v=J7sGEI4-xJo)
These two are your friends — Т sounds like T, and К sounds like K. No surprises here!

**Літера С**
[Anna Ohoiko — Ukrainian Lessons — С](https://www.youtube.com/watch?v=7UsFBgSL91E)
> [!warning] False Friend
> The letter С looks like an English C, but it sounds like the English S. Think **с**он (dream) — that's an «s», not a «k»!

**Літера Л**
[Anna Ohoiko — Ukrainian Lessons — Л](https://www.youtube.com/watch?v=v6-3Xg52Buk)
The letter Л is similar to the English L, though your tongue position differs slightly.

> [!culture] Мама — A Universal Word
> The word **ма́ма** sounds almost the same in dozens of languages around the world. Linguists believe this is because «m» and «a» are among the very first sounds babies produce. Your first Ukrainian word connects you to something truly universal!

Now, let's build syllables. Take М and А. Together they make МА. If you put two of these together, МА + МА, you get **ма́ма** (mom). You just read your first word! Let's try another. К + І makes КІ. Add Т, and you get **кіт** (cat). You build from letters to syllables, and from syllables to words.

Using ONLY these 10 letters, you can already read all of these wonderful decodable words:
*   **ма́ма** (mom)
*   **та́то** (dad)
*   **кіт** (cat)
*   **молоко́** (milk)
*   **ма́сло** (butter)
*   **о́ко** (eye)
*   **ніс** (nose)
*   **мі́сто** (city)
*   **ліс** (forest)
*   **сон** (dream)
*   **сом** (catfish)
*   **мак** (poppy)
*   **сік** (juice)
*   **са́ло** (lard)
*   **стіл** (table)
*   **тут** (here)
*   **там** (there)
*   **кіно́** (cinema)

Great job! Take your time to sound out each letter, build the syllable, and then read the whole word. You are doing wonderfully.

## Перші слова — First Words in Context

Now that you can read your first words, let's put them into context. To help you build full sentences immediately, we are going to introduce three common sight words. These words contain untaught letters, so please recognize them as whole shapes for now:

*   **приві́т** (hello)
*   **дя́кую** (thank you)
*   **це** (this is)

In addition to these sight words, you also have two very important decodable survival words that use the 10 practice letters perfectly: **так** (yes) and **ні** (no).

Let's read some short dialogues using your new decodable words and sight words. Read them aloud and listen to how the words flow together naturally.

> **(Вдома / At home)**
> — Приві́т! Це кіт?
> — Так, це кіт.

> **(На кухні / In the kitchen)**
> — Це молоко́?
> — Ні, це ма́сло.

> **(На вулиці / Outside)**
> — Це ліс?
> — Ні, це мі́сто.

> **(У кімнаті / In the room)**
> — Ма́ма тут?
> — Так, ма́ма тут. А та́то там.

You are making incredible progress! Let's try a little reading practice with short sentences mixing your decodable words and sight words:

*   Ма́ма тут.
*   Кіт там.
*   Це молоко́.
*   Це ма́сло.
*   Дя́кую!

Reading these sentences means you are truly reading Ukrainian right now. Be proud of yourself and keep practicing these patterns!

## Підсумок — Summary

Let's quickly review what you have accomplished in this first step. The Ukrainian alphabet has 33 letters: 10 vowels (**голосні́**), 22 consonants (**при́голосні**), and 1 modifier (Ь). It is a highly phonetic system, which makes your reading journey very rewarding.

You successfully mastered 10 letters today. Just think about that! With those 10 letters alone, you can already read essential words like: **ма́ма**, **та́то**, **кіт**, **молоко́**, **мі́сто**, and **ліс**.

Self-check time! Can you answer these questions confidently?
*   Can you find all 10 vowel letters on the chart?
*   Can you read **ма́ма** and **кіт** confidently?
*   What is the difference between **бу́кви** and **зву́ки**?

Next up: we will dive deep into the vowel system and explore all 10 vowel letters. You've taken your first real step — and it's a big one!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-ukrainian-alphabet.yaml`

```yaml
- type: watch-and-repeat
  title: 'Listen and Repeat: First 10 Letters'
  instruction: 'Watch the video for each letter, listen carefully to Anna, and repeat the sound aloud.'
  items:
    - letter: 'А'
      word: 'мама'
      video: 'https://www.youtube.com/watch?v=hvB3VpcR3ZE'
      note: 'Open "a" sound'
    - letter: 'О'
      word: 'молоко'
      video: 'https://www.youtube.com/watch?v=gJFxRIPRZbI'
      note: 'Rounded "o" sound'
    - letter: 'У'
      word: 'тут'
      video: 'https://www.youtube.com/watch?v=VB1O6PmtYRU'
      note: '"oo" sound'
    - letter: 'І'
      word: 'кіт'
      video: 'https://www.youtube.com/watch?v=Z9TH0H4ShGo'
      note: '"ee" sound'
    - letter: 'М'
      word: 'мама'
      video: 'https://www.youtube.com/watch?v=Ez95H4ibuJo'
      note: 'Like English M'
    - letter: 'Н'
      word: 'ніс'
      video: 'https://www.youtube.com/watch?v=vNUfiKHPYaU'
      note: 'Looks like H, sounds like N'
    - letter: 'Т'
      word: 'тато'
      video: 'https://www.youtube.com/watch?v=m-jcLR_gK0k'
      note: 'Like English T'
    - letter: 'К'
      word: 'кіт'
      video: 'https://www.youtube.com/watch?v=J7sGEI4-xJo'
      note: 'Like English K'
    - letter: 'С'
      word: 'сон'
      video: 'https://www.youtube.com/watch?v=7UsFBgSL91E'
      note: 'Looks like C, sounds like S'
    - letter: 'Л'
      word: 'ліс'
      video: 'https://www.youtube.com/watch?v=v6-3Xg52Buk'
      note: 'Like English L'

- type: image-to-letter
  title: 'Match Picture to Starting Letter'
  instruction: 'Look at the emoji and select the letter the Ukrainian word starts with.'
  items:
    - emoji: '👩'
      answer: 'М'
      distractors: ['Н', 'Т', 'К']
      note: 'мама (mom)'
    - emoji: '🐈'
      answer: 'К'
      distractors: ['М', 'С', 'Л']
      note: 'кіт (cat)'
    - emoji: '🥛'
      answer: 'М'
      distractors: ['О', 'С', 'Н']
      note: 'молоко (milk)'
    - emoji: '👁️'
      answer: 'О'
      distractors: ['А', 'У', 'І']
      note: 'око (eye)'
    - emoji: '🌲'
      answer: 'Л'
      distractors: ['Т', 'С', 'М']
      note: 'ліс (forest)'
    - emoji: '🏙️'
      answer: 'М'
      distractors: ['Н', 'Л', 'С']
      note: 'місто (city)'
    - emoji: '👨'
      answer: 'Т'
      distractors: ['К', 'С', 'М']
      note: 'тато (dad)'
    - emoji: '💤'
      answer: 'С'
      distractors: ['О', 'М', 'Н']
      note: 'сон (dream)'

- type: classify
  title: 'Vowels vs Consonants'
  instruction: 'Sort the 10 practice letters into vowels (голосні) and consonants (приголосні).'
  categories:
    - label: 'Голосні (Vowels)'
      symbol_hint: 'vowel'
      items: ['А', 'О', 'У', 'І']
    - label: 'Приголосні (Consonants)'
      symbol_hint: 'consonant'
      items: ['М', 'Н', 'Т', 'К', 'С', 'Л']

- type: match-up
  title: 'Match Letter to Sound'
  instruction: 'Match each Ukrainian letter to its correct sound description.'
  pairs:
    - left: 'А'
      right: 'open "a" sound'
    - left: 'О'
      right: 'rounded "o" sound'
    - left: 'У'
      right: '"oo" sound'
    - left: 'І'
      right: '"ee" sound'
    - left: 'М'
      right: '"m" sound'
    - left: 'Н'
      right: '"n" sound (not H!)'
    - left: 'Т'
      right: '"t" sound'
    - left: 'К'
      right: '"k" sound'
    - left: 'С'
      right: '"s" sound (not C!)'
    - left: 'Л'
      right: '"l" sound'

- type: fill-in
  title: 'Build Syllables and Words'
  instruction: 'Choose the correct syllable or word built from the letters.'
  items:
    - sentence: 'М + А = ___'
      answer: 'МА'
      options: ['МА', 'АМ', 'МО', 'ОМ']
    - sentence: 'МА + МА = ___'
      answer: 'мама'
      options: ['мама', 'тато', 'масло', 'сало']
    - sentence: 'Т + А = ___'
      answer: 'ТА'
      options: ['ТА', 'АТ', 'ТО', 'ОТ']
    - sentence: 'ТА + ТО = ___'
      answer: 'тато'
      options: ['тато', 'мама', 'місто', 'молоко']
    - sentence: 'К + І = ___'
      answer: 'КІ'
      options: ['КІ', 'ІК', 'КО', 'ОК']
    - sentence: 'КІ + Т = ___'
      answer: 'кіт'
      options: ['кіт', 'сон', 'ліс', 'ніс']
    - sentence: 'С + О = ___'
      answer: 'СО'
      options: ['СО', 'СА', 'СУ', 'СІ']
    - sentence: 'СО + М = ___'
      answer: 'сом'
      options: ['сом', 'сон', 'мак', 'сік']

- type: quiz
  title: 'Read and Identify'
  instruction: 'Read the Ukrainian word and choose the correct meaning.'
  items:
    - question: 'What does the word "мама" mean?'
      options:
        - text: 'mom'
          correct: true
        - text: 'dad'
          correct: false
        - text: 'cat'
          correct: false
        - text: 'milk'
          correct: false
      explanation: 'МАМА means mom in Ukrainian.'
    - question: 'What does the word "кіт" mean?'
      options:
        - text: 'cat'
          correct: true
        - text: 'dog'
          correct: false
        - text: 'eye'
          correct: false
        - text: 'nose'
          correct: false
      explanation: 'КІТ means cat in Ukrainian.'
    - question: 'What does the word "молоко" mean?'
      options:
        - text: 'milk'
          correct: true
        - text: 'butter'
          correct: false
        - text: 'juice'
          correct: false
        - text: 'water'
          correct: false
      explanation: 'МОЛОКО means milk in Ukrainian.'
    - question: 'What does the word "місто" mean?'
      options:
        - text: 'city'
          correct: true
        - text: 'forest'
          correct: false
        - text: 'table'
          correct: false
        - text: 'cinema'
          correct: false
      explanation: 'МІСТО means city in Ukrainian.'
    - question: 'What does the word "ліс" mean?'
      options:
        - text: 'forest'
          correct: true
        - text: 'city'
          correct: false
        - text: 'table'
          correct: false
        - text: 'lard'
          correct: false
      explanation: 'ЛІС means forest in Ukrainian.'
    - question: 'What does the word "око" mean?'
      options:
        - text: 'eye'
          correct: true
        - text: 'nose'
          correct: false
        - text: 'dream'
          correct: false
        - text: 'dad'
          correct: false
      explanation: 'ОКО means eye in Ukrainian.'
    - question: 'What does the word "ніс" mean?'
      options:
        - text: 'nose'
          correct: true
        - text: 'eye'
          correct: false
        - text: 'cat'
          correct: false
        - text: 'yes'
          correct: false
      explanation: 'НІС means nose in Ukrainian.'
    - question: 'What does the word "тато" mean?'
      options:
        - text: 'dad'
          correct: true
        - text: 'mom'
          correct: false
        - text: 'dream'
          correct: false
        - text: 'there'
          correct: false
      explanation: 'ТАТО means dad in Ukrainian.'
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-ukrainian-alphabet.yaml`

```yaml
items:
  - lemma: 'мама'
    translation: 'mom'
    pos: 'noun'
  - lemma: 'тато'
    translation: 'dad'
    pos: 'noun'
  - lemma: 'кіт'
    translation: 'cat'
    pos: 'noun'
  - lemma: 'молоко'
    translation: 'milk'
    pos: 'noun'
  - lemma: 'масло'
    translation: 'butter'
    pos: 'noun'
  - lemma: 'ліс'
    translation: 'forest'
    pos: 'noun'
  - lemma: 'місто'
    translation: 'city'
    pos: 'noun'
  - lemma: 'око'
    translation: 'eye'
    pos: 'noun'
  - lemma: 'ніс'
    translation: 'nose'
    pos: 'noun'
  - lemma: 'сон'
    translation: 'dream / sleep'
    pos: 'noun'
  - lemma: 'сік'
    translation: 'juice'
    pos: 'noun'
  - lemma: 'стіл'
    translation: 'table'
    pos: 'noun'
  - lemma: 'кіно'
    translation: 'cinema'
    pos: 'noun'
  - lemma: 'тут'
    translation: 'here'
    pos: 'adverb'
  - lemma: 'там'
    translation: 'there'
    pos: 'adverb'
  - lemma: 'так'
    translation: 'yes'
    pos: 'particle'
  - lemma: 'ні'
    translation: 'no'
    pos: 'particle'
  - lemma: 'привіт'
    translation: 'hello'
    pos: 'interjection'
  - lemma: 'дякую'
    translation: 'thank you'
    pos: 'interjection'
  - lemma: 'це'
    translation: 'this is'
    pos: 'pronoun'
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

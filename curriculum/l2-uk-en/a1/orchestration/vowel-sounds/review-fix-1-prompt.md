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



**NOTE: 3 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] MISSING_STRUCTURAL_ELEMENT** in `Вступ — Introduction`
  - Expected: Plan point requires visual element: Review: M1 gave you the alphabet map and 10 practice letters. Today: the vowel system — 10 letters t
  - Actual: Section contains only prose — no table or bulleted list found
  - Fix: Add a markdown table or bulleted list to section 'Вступ — Introduction'


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Line 171 / Section "Голосні в словах — Vowels in Words", Line 25 / Section "Шість основних голосних — Six Base Vowels", Line 3 / Section "Вступ — Introduction", Whole module

### Finding 1: Verb scope violation — просимо (HIGH)
**Location**: Line 3 / Section "Вступ — Introduction"
**Problem**: The verb "просимо" (imperf:pres:p:1, VESUM-confirmed) appears in Module 2, which is pre-verb (verbs introduced at M15). D.0 pre-screen confirmed this.
**Required Fix**: Replace with an English greeting or a noun phrase. "Ласкаво просимо" is a fixed expression, but for strict scope compliance, use "Welcome back!" in English only, or treat it as a fixed phrase with explicit annotation.
**Severity**: HIGH

### Finding 2: Verb scope violation — каже (HIGH)
**Location**: Line 171 / Section "Голосні в словах — Vowels in Words"
**Problem**: The verb "каже" (imperf:pres:s:3, VESUM-confirmed) is used in a reading practice sentence. Verbs are forbidden before M15.
**Required Fix**: Replace with a verbless sentence: "Ма́ма — так!" or restructure: "Ма́ма: «Так!»"
**Severity**: HIGH

### Finding 3: Russian/English comparison as baseline (MEDIUM)
**Location**: Line 25 / Section "Шість основних голосних — Six Base Vowels"
**Problem**: Defines Ukrainian vowel purity by contrast with Russian. While the English comparison is pedagogically useful (English speakers DO reduce vowels), the Russian mention is colonial framing — Ukrainian should be presented on its own terms. The Ї culture note on line 137 is acceptable because it's a `[!culture]` block discussing identity.
**Required Fix**: Remove the Russian mention, keep the English comparison: "This is a massive difference from English, where unstressed vowels often turn into a lazy, mumbled «uh» sound. In Ukrainian, every О stays a crisp О!"
**Severity**: HIGH

### Finding 4: Richness gap — engagement boxes (LOW)
**Location**: Whole module
**Problem**: Audit metrics show 2 engagement boxes, but richness gate shows `engagement: 1/2`. Only `[!challenge]` (line 73) and `[!tip]` (line 86) qualify — the `[!practice]` and `[!culture]` may not count as "engagement" for the richness gate. Adding one more engagement callout (e.g., a `[!did-you-know]`) would close this gap.
**Required Fix**: Add one `[!did-you-know]` callout in section "Наголос — Word Stress" about an interesting stress fact.
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Verb scope violation — просимо (HIGH)
- **Location**: Line 3 / Section "Вступ — Introduction"
- **Original**: 「Ласкаво просимо! Welcome back to your Ukrainian journey.」
- **Problem**: The verb "просимо" (imperf:pres:p:1, VESUM-confirmed) appears in Module 2, which is pre-verb (verbs introduced at M15). D.0 pre-screen confirmed this.
- **Fix**: Replace with an English greeting or a noun phrase. "Ласкаво просимо" is a fixed expression, but for strict scope compliance, use "Welcome back!" in English only, or treat it as a fixed phrase with explicit annotation.

### Issue 2: Verb scope violation — каже (HIGH)
- **Location**: Line 171 / Section "Голосні в словах — Vowels in Words"
- **Original**: 「Ма́ма ка́же «так». (Mom says «yes».)」
- **Problem**: The verb "каже" (imperf:pres:s:3, VESUM-confirmed) is used in a reading practice sentence. Verbs are forbidden before M15.
- **Fix**: Replace with a verbless sentence: "Ма́ма — так!" or restructure: "Ма́ма: «Так!»"

### Issue 3: Russian/English comparison as baseline (MEDIUM)
- **Location**: Line 25 / Section "Шість основних голосних — Six Base Vowels"
- **Original**: 「This is a massive difference from Russian or English, where unstressed vowels often turn into a lazy, mumbled «uh» sound.」
- **Problem**: Defines Ukrainian vowel purity by contrast with Russian. While the English comparison is pedagogically useful (English speakers DO reduce vowels), the Russian mention is colonial framing — Ukrainian should be presented on its own terms. The Ї culture note on line 137 is acceptable because it's a `[!culture]` block discussing identity.
- **Fix**: Remove the Russian mention, keep the English comparison: "This is a massive difference from English, where unstressed vowels often turn into a lazy, mumbled «uh» sound. In Ukrainian, every О stays a crisp О!"

### Issue 4: Richness gap — engagement boxes (LOW)
- **Location**: Whole module
- **Problem**: Audit metrics show 2 engagement boxes, but richness gate shows `engagement: 1/2`. Only `[!challenge]` (line 73) and `[!tip]` (line 86) qualify — the `[!practice]` and `[!culture]` may not count as "engagement" for the richness gate. Adding one more engagement callout (e.g., a `[!did-you-know]`) would close this gap.
- **Fix**: Add one `[!did-you-know]` callout in section "Наголос — Word Stress" about an interesting stress fact.

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 3 | 「Ласкаво просимо!」 | "Welcome back!" (English only) or annotate as fixed phrase | Scope (verb in pre-verb module) |
| 171 | 「Ма́ма ка́же «так».」 | 「Ма́ма: «Так!»」 | Scope (verb in pre-verb module) |
| 25 | 「...from Russian or English, where...」 | "...from English, where..." | Colonial framing |

---

## Fix Plan to Reach 9.0/10

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 3: Replace 「Ласкаво просимо!」 with English-only greeting or annotate as fixed phrase — removes verb scope violation
2. Line 171: Change 「Ма́ма ка́же «так».」 → 「Ма́ма: «Так!»」 — removes second verb scope violation

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 25: Remove "Russian or" from the comparison — present Ukrainian vowel purity on its own terms with English-only contrast

**Expected score after fix:** 9/10

### LLM Fingerprint: 8/10 → 8/10
**Note:** The structural monotony in base vowel subsections (description → 3 bullets → video × 6) is inherent to a phonetics module covering letters one by one. Not worth restructuring — the format serves pedagogy. Score stays 8.

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9
= 79.1 / 8.9 = 8.9/10
```

---

## Audit Failures (from automated re-audit)

```
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 1 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 1 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/vowel-sounds-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `Європа` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vowel-sounds.md`

```markdown
## Вступ — Introduction

Welcome back to your Ukrainian journey! In our first module, you explored the alphabet map and practiced your first ten letters. You learned the difference between letters and sounds, and how basic syllables blend together. You did absolutely great! Today, we are focusing on the true heartbeat of the language: the vowel system. 

In Ukrainian, vowels are everything. There are ten vowel letters that carry every single syllable in the language. Why do vowels matter so much? Because the rule is simple and absolute: every syllable has exactly one vowel. If you count the vowels in a Ukrainian word, you instantly know how many syllables it has. It is that straightforward! When you see a long word, you do not need to panic. You just find the vowels, and you will know exactly how to break it down. 

Take your time as we walk through these new sounds. You are building the foundation for beautiful, natural, and authentic Ukrainian pronunciation. Ready? Let's dive in!

## Шість основних голосних — Six Base Vowels

Let's start with the six base vowels. These are the core sounds that you will hear in almost every single Ukrainian sentence. They are the building blocks of the language, and mastering them early will make everything else much easier.

### Літера А

The letter **А** is an open, wide sound, very much like the «a» in the English word «father». The key rule here is that it never reduces or changes its quality, no matter where it is in the word or whether it is stressed or not. Open your mouth wide and let the sound out clearly!
*   **ма́ма** (mom) — You remember this from Module 1!
*   **ка́ша** (porridge) — A staple of Ukrainian cuisine.
*   **са́ло** (lard) — Another famous traditional food.

> [!video] Літера А
> [Anna Ohoiko — Ukrainian Lessons — А](https://www.youtube.com/watch?v=hvB3VpcR3ZE)

### Літера О

The letter **О** is beautifully rounded, similar to the «o» in «more» or «door». Push your lips forward to make a perfect circle. The most important thing to remember is that it stays a crisp, clear **О** even when it is unstressed. This is a massive difference from English, where unstressed vowels often turn into a lazy, mumbled «uh» sound. In Ukrainian, every О stays a crisp О!
*   **о́ко** (eye) — A simple, two-syllable word.
*   **молоко́** (milk) — Three pure «o» sounds!
*   **село́** (village) — The «o» stays pure at the end.

> [!video] Літера О
> [Anna Ohoiko — Ukrainian Lessons — О](https://www.youtube.com/watch?v=gJFxRIPRZbI)

### Літера У

The letter **У** sounds like the «oo» in «moon» or «boot». Push your lips even further forward than for **О** to make it sound authentic. It is a deep, resonant sound that never wavers.
*   **тут** (here) — A very useful little word.
*   **ву́хо** (ear) — Notice how the «u» anchors the word.
*   **суп** (soup) — Easy to remember!

> [!video] Літера У
> [Anna Ohoiko — Ukrainian Lessons — У](https://www.youtube.com/watch?v=VB1O6PmtYRU)

### Літера Е

The letter **Е** sounds like the «e» in «set» or «pet». Be extremely careful here: it is NOT like the English «ee». It is a short, crisp, and flat sound. Notice how it sounds in these words, paying attention to the vowel itself even as you see some new consonants like Д, В, and Р. Do not let those new letters distract you from the **Е**!
*   **не́бо** (sky) — A beautiful, poetic word.
*   **село́** (village) — Notice the crisp «e» at the start.
*   **день** (day) — A word you will use all the time.

> [!video] Літера Е
> [Anna Ohoiko — Ukrainian Lessons — Е](https://www.youtube.com/watch?v=KFlsroBW0dk)

### Літера И

Now we meet a sound that is uniquely Ukrainian! The letter **И** has no exact English equivalent, which makes it fun to practice. To pronounce it, keep your jaw relaxed and your tongue slightly lower than when you say the English «ee». It sounds a bit like the «i» in «sit», but much deeper, almost coming from the back of your throat. Do not push your lips forward!
*   **ри́ба** (fish) — A great word to practice this sound.
*   **сир** (cheese) — Feel the vibration in your jaw.
*   **син** (son) — Another everyday family word.

> [!video] Літера И
> [Anna Ohoiko — Ukrainian Lessons — И](https://www.youtube.com/watch?v=W-1rCu0indE)

### Літера І

The letter **І** is much brighter and higher than **И**. It sounds just like the English «ee» in «see» or «tree». Give a little smile when you say it to help place the sound right at the front of your mouth.
*   **ліс** (forest) — From your previous lesson.
*   **кіт** (cat) — Everyone loves a cat!
*   **сік** (juice) — Perfect for breakfast.

> [!video] Літера І
> [Anna Ohoiko — Ukrainian Lessons — І](https://www.youtube.com/watch?v=Z9TH0H4ShGo)

> [!challenge] The Hardest Contrast
> The difference between **И** and **І** is often the hardest vowel contrast for English speakers to master. Let's drill it with a minimal pair. Try to feel your jaw position change as you say these two words!
> *   **кит** (whale) — keep your jaw relaxed, and make a deeper, lower sound.
> *   **кіт** (cat) — make a tight smile, producing a high and bright sound.

## Наголос — Word Stress

Let's talk about word stress, or **на́голос**. Every Ukrainian word has exactly one stressed syllable. The stressed vowel is pronounced a little louder, slightly longer, and with a bit more energy than the other vowels in the word. However, there is a Golden Rule you must remember and apply every single time you speak: **Ukrainian vowels stay pure in any position**, whether they are stressed or unstressed. The essential quality of the sound does NOT change. 

English speakers naturally tend to swallow unstressed vowels, turning them into a lazy «uh» sound, which linguists call a schwa. For example, think about the English word «photograph»—the vowels shift completely depending on where the stress lands. You must actively fight this instinct in Ukrainian! 

Let's look at the word **молоко́** (milk). The stress is on the last syllable: мо-ло-КО. But all three **О** letters sound exactly the same. They are all pure, rounded **О** sounds. Keep them crisp and clear, and your Ukrainian will instantly sound much more authentic and beautiful. Do not let your mouth get lazy!

> [!tip] Golden Rule Reminder
> Say it with me slowly: мо-ло-КО. Do not let those first two vowels lose their shape and become a lazy English mumble! You have to keep every single **О** perfectly pure.

## Йотовані голосні — Iotated Vowels

Now we meet a fascinating and elegant group of letters: the iotated vowels **Я**, **Ю**, **Є**, and **Ї**. Think of these letters as clever «double-duty» vowels. When they appear at the start of a word, or immediately after another vowel, they actually represent TWO distinct sounds pushed together: the semi-vowel **Й** (which sounds like the English consonant «y» in «yes» or «yellow») plus one of the base vowels we just learned. 

### Літера Я

When the letter **Я** is at the start of a word, it blends the consonant sound «y» (as in «yes») directly into the open «a» sound.
*   **я́блуко** (apple) — A crisp, sweet word.
*   **яйце́** (egg) — Another common food item.

When it comes after another vowel, it also keeps its two sounds, gliding easily from the previous vowel:
*   **моя́** (my, used with feminine nouns)

When it comes after a consonant, it does something very special: it softens the consonant right before it. For example, in the word **дя́дько** (uncle), the **Д** becomes soft before the **Я**, and you just hear the pure «a» sound immediately afterward.

> [!video] Літера Я
> [Anna Ohoiko — Ukrainian Lessons — Я](https://www.youtube.com/watch?v=yhSAf41LX8I)

### Літера Ю

At the start of a word, the letter **Ю** blends the «y» sound directly into the deep «oo» sound, making it sound very much like the English word «you».
*   **юна́к** (young man) — Notice the strong «y» sound.
*   **ю́шка** (broth or fish soup) — A traditional dish.

After a consonant, it softens that consonant, just like **Я** does. Think of the word **лю́ди** (people), where the **Л** becomes soft before the vowel.

> [!video] Літера Ю
> [Anna Ohoiko — Ukrainian Lessons — Ю](https://www.youtube.com/watch?v=9JdIBYCTWGw)

### Літера Є

At the start of a word, the letter **Є** blends the «y» sound with the crisp «e» sound. It sounds similar to the beginning of the English word «yellow».
*   **Євро́па** (Europe) — Very easy to recognize!

After another vowel, it gracefully maintains its two sounds:
*   **моє́** (my, used with neuter nouns)

> [!video] Літера Є
> [Anna Ohoiko — Ukrainian Lessons — Є](https://www.youtube.com/watch?v=O0bwRyyBQSc)

### Літера Ї

The letter **Ї** is incredibly special. Unlike the other iotated vowels, it ALWAYS makes two sounds (the semi-vowel plus the bright «ee» sound), no matter where it is located in the word! It never, ever softens a preceding consonant. It sounds similar to the beginning of the English word «yield».
*   **їжа́к** (hedgehog) — A favorite animal in Ukrainian fairy tales.
*   **ї́жа** (food) — A very important word to know!
*   **Украї́на** (Ukraine) — The most beautiful word of all.

> [!culture] A Symbol of Identity
> The letter **Ї** is completely unique to the Ukrainian alphabet. You will not find it in Russian or Belarusian. Because of this exclusivity, the letter **Ї** has become a powerful, modern symbol of Ukrainian identity, resistance, and cultural pride.

> [!video] Літера Ї
> [Anna Ohoiko — Ukrainian Lessons — Ї](https://www.youtube.com/watch?v=UcjdjQXhAY8)

### The Semi-Vowel Й

We have been talking a lot about the «y» sound hiding inside these iotated letters. That sound is actually represented by its very own letter: the semi-vowel **Й**. It is a short, sharp, consonant-like sound that you will often see at the end of words or syllables. It never forms a syllable on its own.
*   **край** (edge or land) — A poetic word for homeland.
*   **йо́гурт** (yogurt) — Tastes exactly like it sounds!

## Голосні в словах — Vowels in Words

You are doing wonderfully! You have absorbed a lot of phonetic rules, and now it is time to put these vowels into real practice. Read these short dialogues and sentences out loud. Do not worry about the consonants you haven't formally learned yet—we will cover the entire consonant system in Module 3. Right now, I just want you to focus all your energy on making your vowels clear, bright, and pure. Read slowly and deliberately.

> **(Вдома / At home)**
> — Це я́блуко.
> — Так, це моє́ я́блуко.

> **(У місті / In the city)**
> — Це село́?
> — Ні, це мі́сто. Це мій край.

> **(За столом / At the table)**
> — Де мій сир?
> — Сир тут! А ка́ша там.

Let's try a quick, fun exercise together. Do you remember our rule from the introduction? The number of vowels in a word equals the exact number of syllables. Let's count them together and see how the rhythm of the language works!
*   **кіт** (cat) — There is only 1 vowel, so it is 1 syllable.
*   **молоко́** (milk) — There are 3 vowels (**О**, **О**, **О**), so it is exactly 3 syllables: мо-ло-ко.
*   **Украї́на** (Ukraine) — There are 4 vowels (**У**, **А**, **Ї**, **А**), making it 4 syllables: У-кра-ї-на.

> [!practice] Reading Practice
> Read these sentences out loud to yourself. Focus intensely on keeping every single vowel pure and preventing any lazy English schwa sounds from sneaking in!
> *   Ма́ма: «Так!» (Mom: «Yes!»)
> *   Це моє́ село́. (This is my village.)
> *   Де мій кіт? (Where is my cat?)

## Підсумок — Summary

Congratulations! You have just learned the entire foundation of Ukrainian pronunciation. Let's take a moment to review everything we've covered today:

*   You now know the 10 vowel letters: the 6 base vowels (**А О У Е И І**) and the 4 iotated vowels (**Я Ю Є Ї**), plus the important semi-vowel **Й**.
*   You fully understand the Golden Rule: Ukrainian vowels stay pure! Never swallow or reduce them, even when they are unstressed.
*   You know that counting the number of vowels in a word tells you exactly how many syllables it has.

Let's do a quick self-check before you move on to the next lesson:
1.  Can you pronounce all 6 base vowels? Try saying them out loud right now, feeling the shape of your mouth.
2.  What two sounds does the letter **Я** make when it appears at the very beginning of a word?
3.  Can you feel the physical difference in your jaw position between the deep **И** and the bright **І**?

You are building a fantastic foundation. Next up, in Module 3, we will master the consonant system—including voiced and voiceless pairs, sonorants, and the crucial difference between hard and soft consonants. Keep up the great work, and I will see you there!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/vowel-sounds.yaml`

```yaml
- type: watch-and-repeat
  title: "Vowel Pronunciation Drill"
  instruction: "Watch each video by Anna Ohoiko, then repeat the vowel sound out loud. Focus on mouth shape and jaw position."
  items:
    - letter: "А"
      word: "мама"
      video: "https://www.youtube.com/watch?v=hvB3VpcR3ZE"
      note: "Open wide, like 'a' in 'father'. Never reduces."
    - letter: "О"
      word: "око"
      video: "https://www.youtube.com/watch?v=gJFxRIPRZbI"
      note: "Round your lips into a circle. Stays pure even when unstressed."
    - letter: "У"
      word: "суп"
      video: "https://www.youtube.com/watch?v=VB1O6PmtYRU"
      note: "Push lips forward, like 'oo' in 'moon'."
    - letter: "Е"
      word: "небо"
      video: "https://www.youtube.com/watch?v=KFlsroBW0dk"
      note: "Short and crisp, like 'e' in 'set'. NOT like English 'ee'."
    - letter: "И"
      word: "риба"
      video: "https://www.youtube.com/watch?v=W-1rCu0indE"
      note: "Relax your jaw, tongue lower than for І. Uniquely Ukrainian!"
    - letter: "І"
      word: "кіт"
      video: "https://www.youtube.com/watch?v=Z9TH0H4ShGo"
      note: "Bright and high, like 'ee' in 'see'. Smile when you say it."
    - letter: "Я"
      word: "яблуко"
      video: "https://www.youtube.com/watch?v=yhSAf41LX8I"
      note: "At word start: Й + А. Two sounds blended together."
    - letter: "Ю"
      word: "юшка"
      video: "https://www.youtube.com/watch?v=9JdIBYCTWGw"
      note: "At word start: Й + У. Sounds like English 'you'."
    - letter: "Є"
      word: "Європа"
      video: "https://www.youtube.com/watch?v=O0bwRyyBQSc"
      note: "At word start: Й + Е. Like the start of 'yellow'."
    - letter: "Ї"
      word: "їжак"
      video: "https://www.youtube.com/watch?v=UcjdjQXhAY8"
      note: "ALWAYS two sounds: Й + І. Unique to Ukrainian!"

- type: classify
  title: "Sort the Vowel Letters"
  instruction: "Drag each letter into the correct category. Base vowels represent one sound. Iotated vowels can represent two sounds."
  categories:
    - label: "Base Vowels"
      symbol_hint: "vowel"
      items: ["А", "О", "У", "Е", "И", "І"]
    - label: "Iotated Vowels"
      symbol_hint: "iotated"
      items: ["Я", "Ю", "Є", "Ї"]

- type: image-to-letter
  title: "Which Vowel Does It Start With?"
  instruction: "Look at the picture. What vowel letter does the Ukrainian word for this picture start with?"
  items:
    - emoji: "🍎"
      answer: "Я"
      distractors: ["А", "О"]
      note: "яблуко (apple)"
    - emoji: "🦔"
      answer: "Ї"
      distractors: ["І", "Й"]
      note: "їжак (hedgehog)"
    - emoji: "👁️"
      answer: "О"
      distractors: ["А", "У"]
      note: "око (eye)"
    - emoji: "🌍"
      answer: "Є"
      distractors: ["Е", "Ю"]
      note: "Європа (Europe)"
    - emoji: "🧑"
      answer: "Ю"
      distractors: ["У", "Є"]
      note: "юнак (young man)"
    - emoji: "🇺🇦"
      answer: "У"
      distractors: ["А", "О"]
      note: "Україна (Ukraine)"
    - emoji: "🥚"
      answer: "Я"
      distractors: ["Є", "І"]
      note: "яйце (egg)"
    - emoji: "🍲"
      answer: "Ю"
      distractors: ["У", "Я"]
      note: "юшка (broth)"

- type: quiz
  title: "И vs І — Spot the Difference"
  instruction: "Test your knowledge of the two trickiest Ukrainian vowels."
  items:
    - question: "Which vowel is in the word сир (cheese)?"
      options:
        - text: "И"
          correct: true
        - text: "І"
          correct: false
        - text: "Е"
          correct: false
        - text: "А"
          correct: false
      explanation: "Сир contains И — the deeper vowel with a relaxed jaw."
    - question: "Which vowel is in the word кіт (cat)?"
      options:
        - text: "І"
          correct: true
        - text: "И"
          correct: false
        - text: "О"
          correct: false
        - text: "У"
          correct: false
      explanation: "Кіт contains І — the bright, high vowel, like 'ee' in 'see'."
    - question: "Which word contains the letter И?"
      options:
        - text: "син"
          correct: true
        - text: "кіт"
          correct: false
        - text: "ліс"
          correct: false
        - text: "сік"
          correct: false
      explanation: "Син (son) has И. The others all contain І."
    - question: "Which word contains the letter І?"
      options:
        - text: "ліс"
          correct: true
        - text: "сир"
          correct: false
        - text: "риба"
          correct: false
        - text: "кит"
          correct: false
      explanation: "Ліс (forest) has І. The others all contain И."
    - question: "The letter И sounds closest to which English sound?"
      options:
        - text: "'i' in 'sit' (but deeper)"
          correct: true
        - text: "'ee' in 'see'"
          correct: false
        - text: "'a' in 'father'"
          correct: false
        - text: "'o' in 'more'"
          correct: false
      explanation: "И is similar to the 'i' in 'sit', but deeper and more relaxed. It has no exact English equivalent."
    - question: "The letter І sounds closest to which English sound?"
      options:
        - text: "'ee' in 'see'"
          correct: true
        - text: "'i' in 'sit'"
          correct: false
        - text: "'e' in 'set'"
          correct: false
        - text: "'oo' in 'moon'"
          correct: false
      explanation: "І is bright and high, just like 'ee' in 'see'. Smile when you say it!"
    - question: "In the minimal pair кит / кіт, which word means 'cat'?"
      options:
        - text: "кіт"
          correct: true
        - text: "кит"
          correct: false
        - text: "Both mean cat"
          correct: false
        - text: "Neither means cat"
          correct: false
      explanation: "Кіт (with І) means cat. Кит (with И) means whale. One vowel changes everything!"
    - question: "In the minimal pair кит / кіт, which word means 'whale'?"
      options:
        - text: "кит"
          correct: true
        - text: "кіт"
          correct: false
        - text: "Both mean whale"
          correct: false
        - text: "Neither means whale"
          correct: false
      explanation: "Кит (with И) means whale. The deeper, more relaxed vowel for the bigger animal!"
    - question: "When pronouncing И, what should your jaw do?"
      options:
        - text: "Stay relaxed and low"
          correct: true
        - text: "Tighten into a smile"
          correct: false
        - text: "Open as wide as possible"
          correct: false
        - text: "Push lips forward"
          correct: false
      explanation: "For И, keep your jaw relaxed with your tongue low. Save the smile for І!"
    - question: "Which vowel is higher and brighter — like making a small smile?"
      options:
        - text: "І"
          correct: true
        - text: "И"
          correct: false
        - text: "Е"
          correct: false
        - text: "У"
          correct: false
      explanation: "І is the bright, high vowel. Smile to place the sound at the front of your mouth."

- type: group-sort
  title: "Iotated Vowels — One Sound or Two?"
  instruction: "Sort these words by how the highlighted iotated vowel works. At the start of a word or after another vowel, it makes TWO sounds. After a consonant, it makes ONE sound and softens the consonant."
  groups:
    - name: "Two sounds (Й + vowel)"
      items:
        - "яблуко (Я at start)"
        - "юнак (Ю at start)"
        - "Європа (Є at start)"
        - "їжак (Ї — always two)"
        - "моя (Я after vowel)"
        - "моє (Є after vowel)"
        - "їжа (Ї — always two)"
        - "юшка (Ю at start)"
    - name: "One sound (softens consonant)"
      items:
        - "дядько (Я after Д)"
        - "люди (Ю after Л)"

- type: fill-in
  title: "Count the Syllables"
  instruction: "Remember the rule — every vowel letter = one syllable. Count the vowels and pick the correct number of syllables."
  items:
    - sentence: "The word молоко has ___ syllables."
      answer: "3"
      options: ["1", "2", "3", "4"]
      explanation: "Мо-ло-ко: three О vowels = three syllables."
    - sentence: "The word кіт has ___ syllable(s)."
      answer: "1"
      options: ["1", "2", "3", "4"]
      explanation: "Кіт has only one vowel (І), so it is one syllable."
    - sentence: "The word Україна has ___ syllables."
      answer: "4"
      options: ["2", "3", "4", "5"]
      explanation: "У-кра-ї-на: four vowels (У, а, ї, а) = four syllables."
    - sentence: "The word мама has ___ syllables."
      answer: "2"
      options: ["1", "2", "3", "4"]
      explanation: "Ма-ма: two А vowels = two syllables."
    - sentence: "The word яблуко has ___ syllables."
      answer: "3"
      options: ["1", "2", "3", "4"]
      explanation: "Я-блу-ко: three vowels (я, у, о) = three syllables."
    - sentence: "The word село has ___ syllables."
      answer: "2"
      options: ["1", "2", "3", "4"]
      explanation: "Се-ло: two vowels (е, о) = two syllables."
    - sentence: "The word їжак has ___ syllables."
      answer: "2"
      options: ["1", "2", "3", "4"]
      explanation: "Ї-жак: two vowels (ї, а) = two syllables."
    - sentence: "The word небо has ___ syllables."
      answer: "2"
      options: ["1", "2", "3", "4"]
      explanation: "Не-бо: two vowels (е, о) = two syllables."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/vowel-sounds.yaml`

```yaml
items:
  - lemma: "яблуко"
    translation: "apple"
    pos: "noun"
    gender: "n"
    notes: "Key word for letter Я at word start. Two syllables: я-блу-ко."
    usage: "Це яблуко."
  - lemma: "риба"
    translation: "fish"
    pos: "noun"
    gender: "f"
    notes: "Key word for letter И. Feel the relaxed jaw on the first vowel."
    usage: "Це риба."
  - lemma: "село"
    translation: "village"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates unstressed Е staying pure — never reduces to a schwa."
    usage: "Це село."
  - lemma: "Україна"
    translation: "Ukraine"
    pos: "noun"
    gender: "f"
    notes: "Key word for letter Ї. Four syllables: У-кра-ї-на."
    usage: "Це Україна."
  - lemma: "їжак"
    translation: "hedgehog"
    pos: "noun"
    gender: "m"
    notes: "Key word for Ї at word start. A favorite animal in Ukrainian fairy tales."
    usage: "Це їжак."
  - lemma: "юнак"
    translation: "young man"
    pos: "noun"
    gender: "m"
    notes: "Key word for Ю at word start. State Standard vocabulary."
    usage: "Це юнак."
  - lemma: "край"
    translation: "edge; land; homeland"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Й (semi-vowel) at word end. A poetic word for homeland."
    usage: "Це мій край."
  - lemma: "день"
    translation: "day"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Е. Top 50 frequency word in Ukrainian."
    usage: "Це день."
  - lemma: "син"
    translation: "son"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates И. High-frequency family word."
    usage: "Це мій син."
  - lemma: "мій"
    translation: "my; mine"
    pos: "adj"
    notes: "Possessive. Feminine form моя demonstrates Я after vowel. Neuter form моє demonstrates Є after vowel."
    usage: "Це мій кіт. Це моя мама. Це моє село."
  - lemma: "вухо"
    translation: "ear"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates У. Body vocabulary."
    usage: "Це вухо."
  - lemma: "їжа"
    translation: "food"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ї at word start. Everyday vocabulary."
    usage: "Це їжа."
  - lemma: "яйце"
    translation: "egg"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates Я at word start. Notice both Я and Е vowels."
    usage: "Це яйце."
  - lemma: "юшка"
    translation: "broth; fish soup"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ю at word start. A traditional Ukrainian dish."
    usage: "Це юшка."
  - lemma: "каша"
    translation: "porridge"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates А. A staple of Ukrainian cuisine."
    usage: "Це каша."
  - lemma: "небо"
    translation: "sky"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates Е. A beautiful, poetic word."
    usage: "Це небо."
  - lemma: "сир"
    translation: "cheese"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates И. Feel the deeper vowel compared to І."
    usage: "Де мій сир?"
  - lemma: "мама"
    translation: "mom"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates А. Review from Module 1."
    usage: "Це мама."
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    gender: "n"
    notes: "Three pure О sounds: мо-ло-ко. All stay crisp even unstressed."
    usage: "Це молоко."
  - lemma: "око"
    translation: "eye"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates О. A simple two-syllable word: о-ко."
    usage: "Це око."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vowel-sounds.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/vowel-sounds.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/vowel-sounds.yaml`

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

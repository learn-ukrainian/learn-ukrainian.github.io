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
- Only modify these sections: Activities file, line 182 / quiz item "Which word means 'cat'?", Line 16, Section "Шість основних голосних — Six Base Vowels", Line 70, Section "Йотовані голосні — Iotated Vowels", Line 75, Section "Йотовані голосні — Iotated Vowels", Line 83, Section "Голосні в словах — Vowels in Words", Whole module

### Finding 1: Russicism in Activity Distractor (HIGH)
**Location**: Activities file, line 182 / quiz item "Which word means 'cat'?"
**Problem**: `кот` is NOT a valid Ukrainian word (confirmed: VESUM NOT FOUND). It is the Russian word for cat. Including it as a distractor teaches students a Russian word form. This is a Russicism and an audit gate failure.
**Required Fix**: Replace `кот` with a valid Ukrainian distractor like `кут` (corner) which is already used in the same quiz, or `кін` (another valid monosyllable). Since `кут` is already option D, replace `кот` with `кат` (executioner — valid VESUM word, same consonant frame).
**Severity**: HIGH

### Finding 2: Verb in Pre-Verb Module (HIGH)
**Location**: Line 83, Section "Голосні в словах — Vowels in Words"
**Problem**: `каже` is a conjugated verb (казати, 3rd person singular present). This module is M2 — verbs are forbidden until M15. The builder acknowledged this deviation, noting the plan includes this exact sentence. However, the plan itself may need revision; at minimum, the sentence exposes learners to a grammatical form they won't study for 13 more modules.
**Required Fix**: Replace with a verb-free sentence: «Мама — так.» or «Мама тут.» (uses only the word `тут` from M1). Alternatively: «Це мама.»
**Severity**: HIGH

### Finding 3: Colonial Framing (MEDIUM)
**Location**: Line 16, Section "Шість основних голосних — Six Base Vowels"
**Problem**: Defines Ukrainian vowel purity by contrasting with Russian. This is colonial framing — Ukrainian features should be presented on their own terms. A1 learners don't need Russian as a reference point.
**Required Fix**: Rewrite to present the Ukrainian feature positively: "The single most important thing to remember here is that it stays a pure, full **О** even when it is unstressed. In Ukrainian, every О is always a clear О — it never reduces to a weaker sound. This vowel purity is a beautiful feature of Ukrainian pronunciation."
**Severity**: HIGH

### Finding 4: Zero Engagement Boxes (MEDIUM)
**Location**: Whole module
**Problem**: The module contains 0 callout boxes (`[!tip]`, `[!example]`, `[!cultural-note]`, `[!did-you-know]`, etc.). The audit requires minimum 1 for A1. The Ї cultural identity note on line 70 is excellent content but is buried in prose rather than highlighted in a callout box. The richness audit shows engagement: 0/2.
**Required Fix**: Convert the Ї cultural note (line 70) into a `> [!did-you-know]` callout. Add at least one `> [!tip]` for the И vs І jaw position technique (line 41).
**Severity**: HIGH

### Finding 5: LLM Formality Pattern (LOW)
**Location**: Line 75, Section "Йотовані голосні — Iotated Vowels"
**Problem**: "It is very important to note" is a classic LLM formal pattern. A patient tutor would say this more naturally.
**Required Fix**: "Here's a key rule: **Й** never forms a syllable all on its own."
**Severity**: HIGH

### Finding 6: Factual Overstatement — Ї Uniqueness (LOW)
**Location**: Line 70, Section "Йотовані голосні — Iotated Vowels"
**Problem**: While Ї is overwhelmingly a Ukrainian symbol and the claim is nearly correct, it appears in limited historical/regional Cyrillic usage (Rusyn). The absolute claim is slightly overstated.
**Required Fix**: Soften to: "It is unique to the Ukrainian Cyrillic alphabet and found in no other major Slavic writing system."
**Severity**: HIGH

---

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

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 83 | 「Мама каже 'так'.」 | «Це мама.» or «Мама тут.» | Scope (verb in pre-verb module) |
| 182 (acts) | 「кот」 | кат | Russicism (not valid Ukrainian) |

---

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

---

## Audit Failures (from automated re-audit)

```
--- STRICT GATES (Level A1) ---
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/vowel-sounds-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `Кравцова` (source: prose)
  ❌ `Європа` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vowel-sounds.md`

```markdown
## Вступ — Introduction

Welcome to the beating heart of the Ukrainian language! In our very first lesson, we mapped out the entire Cyrillic alphabet and started practicing our first ten letters. You did an amazing job making that crucial first contact. Today, we are zooming in on the absolute foundation of Ukrainian pronunciation: the vowel system. 

There are exactly ten vowel letters in Ukrainian, and they are incredibly important because they carry the weight and rhythm of every single syllable in the language. Why do vowels matter so much? The answer is beautifully simple: every syllable in Ukrainian has exactly one vowel. This is a brilliant, built-in shortcut for you as a learner. If you simply count the vowels in any given word, you will instantly know exactly how many syllables that word has. It makes reading long, intimidating words suddenly feel easy and manageable. Once you understand these ten vowel letters, you will have the rhythmic keys to the language unlocked and ready for your conversational journey. Let's dive in!

## Шість основних голосних — Six Base Vowels

We will begin our journey with the six foundational vowel sounds. These are the basic building blocks of Ukrainian pronunciation. Think of them as the steady, reliable anchors of the language.

The letter **А** is a bright, open sound, very similar to the 'a' in the English word 'father'. It never reduces or changes its sound, no matter where it appears. You already know the word **мама**, but you will also hear this wonderful, open vowel in everyday foods like **каша** (porridge) and the traditional **сало** (lard).

### Літера А
[Anna Ohoiko — Ukrainian Lessons — А](https://www.youtube.com/watch?v=hvB3VpcR3ZE)

The letter **О** is beautifully rounded, much like the 'o' in the English word 'more'. The single most important thing to remember here is that it stays a pure, full **О** even when it is unstressed. In Ukrainian, every О is always a clear, pure О — it never weakens or reduces to another sound. This vowel purity is one of the most beautiful features of Ukrainian pronunciation. You can hear it clearly in words you know like **око** and **молоко**, as well as the new word **село** (village).

### Літера О
[Anna Ohoiko — Ukrainian Lessons — О](https://www.youtube.com/watch?v=gJFxRIPRZbI)

The letter **У** sounds just like the 'oo' in the English word 'moon'. It is a deep, resonant sound that vibrates. You will practice it in the word **тут** from our last lesson, as well as in **вухо** (ear) and **суп** (soup).

### Літера У
[Anna Ohoiko — Ukrainian Lessons — У](https://www.youtube.com/watch?v=VB1O6PmtYRU)

Next is **Е**, which sounds closely like the 'e' in 'set'. Be careful: it is NOT like the English 'ee' sound. You will start seeing some new consonants like **Д**, **В**, and **Р** in these examples, but I want you to focus purely on the vowel sound. Listen to the crisp **Е** in **небо** (sky), **село** (village), and **день** (day).

### Літера Е
[Anna Ohoiko — Ukrainian Lessons — Е](https://www.youtube.com/watch?v=KFlsroBW0dk)

Now for **И** — this vowel is uniquely Ukrainian! There is no exact English equivalent, which makes it a fun challenge. Keep your jaw very relaxed, and place your tongue lower than when you make an 'ee' sound. Try it with **риба** (fish), **сир** (cheese), and **син** (son).

### Літера И
[Anna Ohoiko — Ukrainian Lessons — И](https://www.youtube.com/watch?v=W-1rCu0indE)

Finally, we have **І**, which sounds sharply like the 'ee' in the English word 'see'. It is much brighter and higher in the mouth than **И**. You already know this sound from **ліс**, **кіт**, and **сік**.

### Літера І
[Anna Ohoiko — Ukrainian Lessons — І](https://www.youtube.com/watch?v=Z9TH0H4ShGo)

The distinction between **И** and **І** is often the hardest vowel contrast for English speakers to master. We must drill this carefully with minimal pairs (words that differ by only one sound). Let's compare **кит** (whale) and **кіт** (cat). You really need to feel the jaw position: it drops slightly for the relaxed **И** in **кит**, but stays high and tense for the bright **І** in **кіт**.

> [!tip] **И vs І — Feel the Difference**
> Place your hand under your chin. Say **кіт** — your jaw barely moves. Now say **кит** — your jaw drops just a little. That tiny shift is the whole difference! Practice switching back and forth until you can feel it every time.

## Наголос — Word Stress

Every single Ukrainian word containing more than one syllable has exactly one stressed syllable. This concept is called наголос. The stressed vowel is pronounced slightly louder and a bit longer than the surrounding vowels. However, and this is absolutely crucial to sounding natural, the quality of the vowel itself does NOT change.

This brings us to the Golden Rule of Ukrainian pronunciation: Ukrainian vowels stay pure in any position, whether they are stressed or unstressed. As English speakers, we naturally want to swallow unstressed vowels and turn them into a lazy, muted "uh" sound (linguists call this a schwa). You must actively fight this habit when speaking Ukrainian!

For example, look closely at the word **молоко**. The word stress falls on the very last syllable, making it **молокО**. But all three **О**'s must sound exactly the same: pure, rounded, and clear. Compare this to the English word 'photograph', where the vowel sounds constantly shift and muddy depending on which syllable gets the stress. In Ukrainian, a vowel is a promise—it always sounds like itself, no matter what. Maintaining this purity is the quickest way to sound less like a foreigner and more like a local.

## Йотовані голосні — Iotated Vowels

Now we get to meet the four 'double-duty' vowels: **Я**, **Ю**, **Є**, and **Ї**. These are called iotated vowels. The term sounds technical, but the concept is very straightforward. At the start of a word, or immediately after another vowel, these letters actually represent TWO sounds combined into one letter: the semi-vowel **Й** (which sounds like an English 'y') plus a base vowel.

The letter **Я** represents the combination of **й**+**а**. At the start of a word, it clearly makes two sounds, as in the delicious word **яблуко** (apple) and **яйце** (egg). When it comes after another vowel, it also makes two distinct sounds, just like in the feminine possessive word **моя** (my). However, when **Я** comes after a consonant, it has a special job: it softens that consonant. For example, in the word **дядько**, the **Д** becomes a soft consonant right before the **Я** sound.

### Літера Я
[Anna Ohoiko — Ukrainian Lessons — Я](https://www.youtube.com/watch?v=yhSAf41LX8I)

The letter **Ю** represents the sounds **й**+**у**. Just like with **Я**, at the start of a word it makes two sounds: you can hear this in **юнак** (young man) and the tasty traditional soup **юшка** (broth). After a consonant, it serves to soften that preceding letter, exactly like in the word **люди**, where the **Л** becomes soft.

### Літера Ю
[Anna Ohoiko — Ukrainian Lessons — Ю](https://www.youtube.com/watch?v=9JdIBYCTWGw)

The letter **Є** represents **й**+**е**. At the start of a word, you get the double sound, as in the name **Європа** (Europe). After another vowel, it also gives two sounds: you can hear it perfectly in the neuter possessive word **моє** (my).

### Літера Є
[Anna Ohoiko — Ukrainian Lessons — Є](https://www.youtube.com/watch?v=O0bwRyyBQSc)

The letter **Ї** is truly special. Unlike the other three iotated vowels, it ALWAYS represents two sounds, **й**+**і**. It never, ever softens a preceding consonant. You will see and hear it in words like **їжак** (hedgehog), everyday **їжа** (food), and most importantly, **Україна**. Let's add a quick cultural note here: the letter **Ї** stands as a powerful symbol of Ukrainian identity. It is unique to the Ukrainian Cyrillic alphabet — no other major Slavic writing system uses it — and Ukrainians are fiercely proud of it.

> [!did-you-know] **Ї — A Symbol of Identity**
> During difficult times, drawing the letter **Ї** has served as a symbol of resistance and national pride. It belongs to Ukrainian and Ukrainian alone.

### Літера Ї
[Anna Ohoiko — Ukrainian Lessons — Ї](https://www.youtube.com/watch?v=UcjdjQXhAY8)

Finally, let's look at the letter **Й** itself. This is the semi-vowel, a very short, crisp, consonant-like sound. You hear it at the end of words like **край** (edge or land) and inside modern words like **йогурт**. Here is a key rule: **Й** never forms a syllable all on its own. It must always be attached to a true vowel.

## Голосні в словах — Vowels in Words

Let's put all this phonetic theory into practice with some reading exercises. Do not worry about perfectly pronouncing all the consonants just yet; your only job right now is to focus on the vowels. Pay attention to how pure they sound.

«Це яблуко.»
«Це моє село.»
«Мама тут.»
«Де мій кіт?»

Now, let's try a vital vowel-counting exercise. Remember our rule from the introduction: the number of vowels in a word equals the number of syllables in that word. This is a skill you will use every day.

Take the word **молоко**. We can quickly spot and count three **О**'s. Since there are three vowels, that means there are exactly 3 syllables.
What about the name of the country itself, **Україна**? Let's count them: we see **У**, **а**, **ї**, and **а**. That is a total of four vowels, which gives us exactly 4 syllables: У-кра-ї-на. It has a beautiful rhythm to it!
And what about the word **кіт**? There is only 1 vowel here, the letter **і**, meaning the word has exactly 1 syllable.
Let's try another one. How many syllables does the word **юнак** have? We can see two vowels (**ю** and **а**), so it has exactly two syllables.
What about the word **край**? Remember our lesson on the semi-vowel: the letter **й** does not count as a full vowel! There is only one **а**, so the word has just one syllable!

Practicing this simple visual exercise will train your eyes to scan Ukrainian text correctly, letting you confidently break down long, intimidating new words into manageable, rhythmic chunks.

## Підсумок — Summary

You have done a fantastic job today. We have now covered the complete set of ten Ukrainian vowel letters. You know that there are six base vowels (**А**, **О**, **У**, **Е**, **И**, **І**) and four special iotated vowels (**Я**, **Ю**, **Є**, **Ї**), plus the helpful semi-vowel **Й**.

Always remember the Golden Rule reinforced today: Ukrainian vowels stay absolutely pure. You must never swallow them or reduce them to lazy sounds, regardless of where the word stress falls. Every vowel deserves to be heard clearly.

Self-check questions before you move on: Can you confidently pronounce all 6 base vowels without making them sound like English sounds? What two distinct sounds does the letter **Я** make when it appears at the very start of a word? What is the physical difference in your jaw and tongue position between making an **И** sound and an **І** sound?

In our next module, we will step over to the other side of the alphabet to master the consonant system. You will learn about voiced and voiceless pairs, special sonorants, and the vital difference between hard and soft sounds. See you there!

<!-- adapted from: Кравцова, Grade 3 -->
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/vowel-sounds.yaml`

```yaml
- type: watch-and-repeat
  title: "Vowel Pronunciation Drill"
  instruction: "Watch each video by Anna Ohoiko. Listen carefully to the vowel sound, then repeat it aloud several times. Focus on mouth shape and jaw position."
  items:
    - letter: "А"
      word: "мама"
      video: "https://www.youtube.com/watch?v=hvB3VpcR3ZE"
      note: "Open sound, like 'a' in 'father'. Keep it bright and clear."
    - letter: "О"
      word: "око"
      video: "https://www.youtube.com/watch?v=gJFxRIPRZbI"
      note: "Rounded, like 'o' in 'more'. Stays pure even when unstressed."
    - letter: "У"
      word: "суп"
      video: "https://www.youtube.com/watch?v=VB1O6PmtYRU"
      note: "Deep sound, like 'oo' in 'moon'."
    - letter: "Е"
      word: "небо"
      video: "https://www.youtube.com/watch?v=KFlsroBW0dk"
      note: "Like 'e' in 'set'. NOT like English 'ee'."
    - letter: "И"
      word: "риба"
      video: "https://www.youtube.com/watch?v=W-1rCu0indE"
      note: "Uniquely Ukrainian. Relax your jaw, tongue lower than for І."
    - letter: "І"
      word: "кіт"
      video: "https://www.youtube.com/watch?v=Z9TH0H4ShGo"
      note: "Like 'ee' in 'see'. Brighter and higher than И."
    - letter: "Я"
      word: "яблуко"
      video: "https://www.youtube.com/watch?v=yhSAf41LX8I"
      note: "At word start, sounds like 'y' + 'a'. Two sounds in one letter."
    - letter: "Ю"
      word: "юнак"
      video: "https://www.youtube.com/watch?v=9JdIBYCTWGw"
      note: "At word start, sounds like 'y' + 'oo'. Two sounds in one letter."
    - letter: "Є"
      word: "Європа"
      video: "https://www.youtube.com/watch?v=O0bwRyyBQSc"
      note: "At word start, sounds like 'y' + 'e'. Two sounds in one letter."
    - letter: "Ї"
      word: "їжак"
      video: "https://www.youtube.com/watch?v=UcjdjQXhAY8"
      note: "ALWAYS two sounds: 'y' + 'ee'. A uniquely Ukrainian letter."

- type: classify
  title: "Sort the Vowel Letters"
  instruction: "Drag each Ukrainian vowel letter into the correct category: base vowels or iotated (double-duty) vowels."
  categories:
    - label: "Base Vowels"
      symbol_hint: "vowel"
      items: ["А", "О", "У", "Е", "И", "І"]
    - label: "Iotated Vowels"
      symbol_hint: "vowel"
      items: ["Я", "Ю", "Є", "Ї"]

- type: image-to-letter
  title: "Which Vowel Does It Start With?"
  instruction: "Look at the picture. Which Ukrainian vowel letter does the word for this picture start with?"
  items:
    - emoji: "🍎"
      answer: "Я"
      distractors: ["А", "Ю", "Є"]
      note: "яблуко (apple) starts with Я"
    - emoji: "🦔"
      answer: "Ї"
      distractors: ["І", "И", "Є"]
      note: "їжак (hedgehog) starts with Ї"
    - emoji: "👁️"
      answer: "О"
      distractors: ["А", "У", "Е"]
      note: "око (eye) starts with О"
    - emoji: "🇺🇦"
      answer: "У"
      distractors: ["Ю", "О", "А"]
      note: "Україна starts with У"
    - emoji: "🥚"
      answer: "Я"
      distractors: ["Є", "Ї", "І"]
      note: "яйце (egg) starts with Я"
    - emoji: "🌍"
      answer: "Є"
      distractors: ["Е", "Я", "Ї"]
      note: "Європа (Europe) starts with Є"
    - emoji: "🍲"
      answer: "Ю"
      distractors: ["У", "Я", "Є"]
      note: "юшка (broth) starts with Ю"
    - emoji: "🍽️"
      answer: "Ї"
      distractors: ["І", "Є", "Я"]
      note: "їжа (food) starts with Ї"

- type: quiz
  title: "И vs І — Can You Tell Them Apart?"
  instruction: "Choose the correct answer for each question about the two trickiest Ukrainian vowels."
  items:
    - question: "Which vowel is in the word кіт (cat)?"
      explanation: "Кіт has the letter І — bright and high, like 'ee' in 'see'."
      options:
        - text: "І"
          correct: true
        - text: "И"
          correct: false
        - text: "Е"
          correct: false
        - text: "Ї"
          correct: false
    - question: "Which vowel is in the word кит (whale)?"
      explanation: "Кит has the letter И — uniquely Ukrainian, with a relaxed jaw."
      options:
        - text: "И"
          correct: true
        - text: "І"
          correct: false
        - text: "У"
          correct: false
        - text: "Е"
          correct: false
    - question: "Which vowel sounds like 'ee' in the English word 'see'?"
      explanation: "І is bright and high in the mouth, very close to English 'ee'."
      options:
        - text: "І"
          correct: true
        - text: "И"
          correct: false
        - text: "Е"
          correct: false
        - text: "А"
          correct: false
    - question: "Which vowel is uniquely Ukrainian with no exact English equivalent?"
      explanation: "И has no exact match in English. You relax your jaw and lower your tongue."
      options:
        - text: "И"
          correct: true
        - text: "І"
          correct: false
        - text: "О"
          correct: false
        - text: "У"
          correct: false
    - question: "To pronounce И correctly, what should you do with your jaw?"
      explanation: "For И, your jaw drops slightly and relaxes — lower than for І."
      options:
        - text: "Relax it and drop it slightly"
          correct: true
        - text: "Clench it tightly"
          correct: false
        - text: "Open it as wide as possible"
          correct: false
        - text: "Push it forward"
          correct: false
    - question: "Which vowel appears in the word риба (fish)?"
      explanation: "Риба contains the uniquely Ukrainian vowel И."
      options:
        - text: "И"
          correct: true
        - text: "І"
          correct: false
        - text: "Е"
          correct: false
        - text: "Ї"
          correct: false
    - question: "Which vowel appears in the word ліс (forest)?"
      explanation: "Ліс contains І — bright and high, like 'ee' in 'see'."
      options:
        - text: "І"
          correct: true
        - text: "И"
          correct: false
        - text: "Е"
          correct: false
        - text: "А"
          correct: false
    - question: "Which word means 'cat' in Ukrainian?"
      explanation: "Кіт (with І) means cat. Кит (with И) means whale."
      options:
        - text: "кіт"
          correct: true
        - text: "кит"
          correct: false
        - text: "кат"
          correct: false
        - text: "кут"
          correct: false
    - question: "Which vowel is brighter and higher in the mouth?"
      explanation: "І is brighter and higher, while И is more relaxed and lower."
      options:
        - text: "І"
          correct: true
        - text: "И"
          correct: false
        - text: "Е"
          correct: false
        - text: "У"
          correct: false
    - question: "Which word means 'cheese' in Ukrainian?"
      explanation: "Сир (with И) means cheese. The relaxed Ukrainian И vowel is key."
      options:
        - text: "сир"
          correct: true
        - text: "сір"
          correct: false
        - text: "сер"
          correct: false
        - text: "сур"
          correct: false

- type: group-sort
  title: "How Many Sounds Does the Iotated Vowel Make?"
  instruction: "In each word below, the highlighted iotated vowel (Я, Ю, Є, or Ї) makes either ONE sound or TWO sounds. Sort each word into the correct group."
  groups:
    - name: "TWO sounds (at word start or after a vowel)"
      items: ["яблуко", "моя", "юнак", "Європа", "їжак", "моє", "їжа", "юшка"]
    - name: "ONE sound (after a consonant — softens it)"
      items: ["дядько", "люди"]

- type: fill-in
  title: "Count the Syllables"
  instruction: "Remember the rule: the number of vowels in a word equals the number of syllables. Count the vowels and choose the correct number."
  items:
    - sentence: "The word молоко has ___ syllables."
      answer: "3"
      options: ["1", "2", "3", "4"]
      explanation: "Молоко has three vowels (о, о, о), so it has 3 syllables."
    - sentence: "The word Україна has ___ syllables."
      answer: "4"
      options: ["2", "3", "4", "5"]
      explanation: "Україна has four vowels (У, а, ї, а), so it has 4 syllables."
    - sentence: "The word кіт has ___ syllable(s)."
      answer: "1"
      options: ["1", "2", "3", "4"]
      explanation: "Кіт has one vowel (і), so it has 1 syllable."
    - sentence: "The word юнак has ___ syllables."
      answer: "2"
      options: ["1", "2", "3", "4"]
      explanation: "Юнак has two vowels (ю, а), so it has 2 syllables."
    - sentence: "The word край has ___ syllable(s)."
      answer: "1"
      options: ["1", "2", "3", "4"]
      explanation: "Край has one vowel (а). Remember, Й is a semi-vowel and does not count!"
    - sentence: "The word яблуко has ___ syllables."
      answer: "3"
      options: ["1", "2", "3", "4"]
      explanation: "Яблуко has three vowels (я, у, о), so it has 3 syllables."
    - sentence: "The word мама has ___ syllables."
      answer: "2"
      options: ["1", "2", "3", "4"]
      explanation: "Мама has two vowels (а, а), so it has 2 syllables."
    - sentence: "The word село has ___ syllables."
      answer: "2"
      options: ["1", "2", "3", "4"]
      explanation: "Село has two vowels (е, о), so it has 2 syllables."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/vowel-sounds.yaml`

```yaml
items:
  - lemma: "яблуко"
    translation: "apple"
    pos: "noun"
    gender: "n"
    notes: "Key word for Я; starts with iotated vowel (й+а)"
    usage: "Це яблуко."
  - lemma: "риба"
    translation: "fish"
    pos: "noun"
    gender: "f"
    notes: "Key word for И; high-frequency food word"
    usage: "Це риба."
  - lemma: "село"
    translation: "village"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates unstressed Е staying pure"
    usage: "Це моє село."
  - lemma: "Україна"
    translation: "Ukraine"
    pos: "noun"
    gender: "f"
    notes: "Key word for Ї; 4 syllables (У-кра-ї-на)"
    usage: "Це Україна."
  - lemma: "їжак"
    translation: "hedgehog"
    pos: "noun"
    gender: "m"
    notes: "Key word for Ї; starts with iotated vowel (always й+і)"
  - lemma: "юнак"
    translation: "young man"
    pos: "noun"
    gender: "m"
    notes: "Key word for Ю; starts with iotated vowel (й+у)"
  - lemma: "край"
    translation: "edge, land"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Й at word end; Й does not count as a vowel for syllable counting"
  - lemma: "день"
    translation: "day"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Е; top 50 most frequent Ukrainian word"
  - lemma: "син"
    translation: "son"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates И; high-frequency family word"
  - lemma: "мій"
    translation: "my (masculine)"
    pos: "adj"
    notes: "Possessive; forms моя (f), моє (n) — iotated vowels after vowel"
    usage: "Де мій кіт?"
  - lemma: "вухо"
    translation: "ear"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates У; body vocabulary"
  - lemma: "їжа"
    translation: "food"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ї; everyday vocabulary"
  - lemma: "яйце"
    translation: "egg"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates Я at word start (й+а)"
    usage: "Це яйце."
  - lemma: "юшка"
    translation: "broth, soup"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ю; traditional Ukrainian food"
  - lemma: "каша"
    translation: "porridge"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates А; everyday food word"
  - lemma: "небо"
    translation: "sky"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates Е; high-frequency word"
  - lemma: "сир"
    translation: "cheese"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates И; everyday food word"
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    gender: "n"
    notes: "Three О vowels, all stay pure even unstressed (Golden Rule)"
    usage: "Це молоко."
  - lemma: "кіт"
    translation: "cat"
    pos: "noun"
    gender: "m"
    notes: "Minimal pair with кит (whale) — І vs И contrast"
    usage: "Де мій кіт?"
  - lemma: "Європа"
    translation: "Europe"
    pos: "noun"
    gender: "f"
    notes: "Key word for Є at word start (й+е)"
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

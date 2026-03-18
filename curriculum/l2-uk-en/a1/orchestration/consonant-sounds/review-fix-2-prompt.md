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



**NOTE: 2 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Across sections "Сонорні — Sonorant Consonants" and "Тверді та м'які — Hard and Soft Consonants", Activities file / All 6 activities, Line 10 / Section "Сонорні — Sonorant Consonants"

### Finding 1: Russicism — луна used for "moon" (HIGH)
**Location**: Line 10 / Section "Сонорні — Sonorant Consonants"
**Problem**: In Ukrainian, луна́ (stress on last syllable) means "echo," NOT "moon." The word for "moon" is **місяць**. Using луна for "moon" is a Russian calque (Russian луна́ = moon). This is also a stress error: лу́на → луна́. Both the meaning and the stress are wrong. A Russicism in an A1 phonetics module is a critical error — learners will internalize the wrong word.
**Required Fix**: Replace with **ла́мпа** (lamp) — demonstrates hard Л, high-frequency A1 word: 「**Л** flows through **ла́мпа** (lamp) and **ліс** (forest).」
**Severity**: HIGH

### Finding 2: Required vocabulary missing from activities (MEDIUM)
**Location**: Activities file / All 6 activities
**Problem**: Plan requires **небо** as required vocabulary. It should appear in at least one activity for practice reinforcement. Currently only mentioned once in passing.
**Required Fix**: Add **небо** to the image-to-letter activity with emoji 🌌 or ☁️, answer "Н", distractors ["М", "Л", "В"].
**Severity**: HIGH

### Finding 3: Richness gap — examples below threshold (LOW)
**Location**: Across sections "Сонорні — Sonorant Consonants" and "Тверді та м'які — Hard and Soft Consonants"
**Problem**: The module could benefit from additional example contexts, particularly in section "Тверді та м'які" where only 3 examples are given (ліс, день, кінь) before the minimal pair.
**Required Fix**: Add 2-3 more hard/soft examples in section "Тверді та м'які" after the existing examples. E.g., **ніс** (nose, soft Н before І) vs **нос** (not a standard form — skip). Better: **кіт** (cat, soft К before І), **мій** (my, soft М before І).
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Russicism — луна used for "moon" (HIGH)
- **Location**: Line 10 / Section "Сонорні — Sonorant Consonants"
- **Original**: 「**лу́на** (moon)」
- **Problem**: In Ukrainian, луна́ (stress on last syllable) means "echo," NOT "moon." The word for "moon" is **місяць**. Using луна for "moon" is a Russian calque (Russian луна́ = moon). This is also a stress error: лу́на → луна́. Both the meaning and the stress are wrong. A Russicism in an A1 phonetics module is a critical error — learners will internalize the wrong word.
- **Fix**: Replace with **ла́мпа** (lamp) — demonstrates hard Л, high-frequency A1 word: 「**Л** flows through **ла́мпа** (lamp) and **ліс** (forest).」

### Issue 2: Required vocabulary missing from activities (MEDIUM)
- **Location**: Activities file / All 6 activities
- **Original**: **небо** (sky) appears only in prose (line 10) but is absent from every activity
- **Problem**: Plan requires **небо** as required vocabulary. It should appear in at least one activity for practice reinforcement. Currently only mentioned once in passing.
- **Fix**: Add **небо** to the image-to-letter activity with emoji 🌌 or ☁️, answer "Н", distractors ["М", "Л", "В"].

### Issue 3: Richness gap — examples below threshold (LOW)
- **Location**: Across sections "Сонорні — Sonorant Consonants" and "Тверді та м'які — Hard and Soft Consonants"
- **Original**: Audit shows examples: 4/8
- **Problem**: The module could benefit from additional example contexts, particularly in section "Тверді та м'які" where only 3 examples are given (ліс, день, кінь) before the minimal pair.
- **Fix**: Add 2-3 more hard/soft examples in section "Тверді та м'які" after the existing examples. E.g., **ніс** (nose, soft Н before І) vs **нос** (not a standard form — skip). Better: **кіт** (cat, soft К before І), **мій** (my, soft М before І).

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 10 | 「**лу́на** (moon)」 | 「**ла́мпа** (lamp)」 | Russicism + wrong stress |

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 8.3)

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. Line 10: Change 「**лу́на** (moon)」 → 「**ла́мпа** (lamp)」 — eliminates the Russicism and stress error. лампа demonstrates hard Л, is high-frequency, and is a real A1 word.

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Same fix as Linguistic Accuracy — the луна Russicism is the only language issue.

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Add **небо** to image-to-letter activity — ensures all required vocab appears in at least one activity.

**Expected score after fix:** 9/10

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
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
⚠️  [PRAISE_ONLY_CITATIONS] Review cites 15 Ukrainian passages but ALL are used positively — none highlight problems. A credible review uses citations to show both strengths AND weaknesses. REDO: DELETE the existing review file and regenerate from scratch. Run build_module_v5.py review phase (tier-1-beginner) using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence and stress mark, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.
⚠️  [UNIFORM_HIGH_SCORES] All 7 dimension scores are uniformly high (mean=8.3, stdev=0.49). Each dimension should be evaluated independently — genuinely different aspects rarely score identically.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/consonant-sounds-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `ДЖ` (source: prose)
  ❌ `ДЗ` (source: prose)
  ❌ `зу` (source: prose)
  ❌ `хлі` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/consonant-sounds.md`

```markdown
## Вступ — Introduction
Welcome back! You are doing incredibly well. In our first module, we explored the entire Ukrainian alphabet together, and in the second module, you successfully mastered all ten vowels. Now that you have those beautiful, clear vowel sounds down perfectly, it is time to build the strong framework around them.

Today, we are going to focus entirely on the twenty-two consonant letters of the Ukrainian language. We will look closely at how they are organized by the way you produce the sound using your mouth, tongue, and throat. All the vowels you have already learned are now available and ready to be paired with these exciting new consonant sounds. Our primary goal today is not just to recognize these letters on the page, but to classify them and pronounce them exactly like a native speaker. Let's dive in!

## Сонорні — Sonorant Consonants
Are you ready to start? We will begin with the most musical sounds in the Ukrainian language: the sonorant consonants. These are sounds where your voice completely dominates over any breath noise. You use your vocal cords heavily to produce them, making them hum beautifully. There are exactly five sonorant consonants in Ukrainian: **Л**, **М**, **Н**, **Р**, and **В**.

### Літери Л, М і Н
You already know the letters **Л**, **М**, and **Н** from our very first alphabet module. These sounds are very similar to their English equivalents, but remember to keep them clear and crisp. **М** hums beautifully in words like **ма́ма** (mom) and **мо́ре** (sea). **Н** rings clearly in **не́бо** (sky) and **ніч** (night). **Л** flows through **ла́мпа** (lamp) and **ліс** (forest).
> **Літера М**
> [Anna Ohoiko — Ukrainian Lessons — М](https://www.youtube.com/watch?v=Ez95H4ibuJo)
>
> **Літера Н**
> [Anna Ohoiko — Ukrainian Lessons — Н](https://www.youtube.com/watch?v=vNUfiKHPYaU)
>
> **Літера Л**
> [Anna Ohoiko — Ukrainian Lessons — Л](https://www.youtube.com/watch?v=v6-3Xg52Buk)

### Літера Р
Let's focus on the letter **Р**. It looks exactly like an English letter P, but it sounds completely different! This is the famous rolled or trilled R. To make this unique sound, you need to practice a quick tongue-tip trill against the roof of your mouth, just behind your front teeth. Try saying **ри́ба** (fish) and **рука́** (hand). Take your time practicing this motion. It might take a little while to master, but it is a very satisfying sound to make once you get the hang of it!
> **Літера Р**
> [Anna Ohoiko — Ukrainian Lessons — Р](https://www.youtube.com/watch?v=fMGsQ5KPQgg)

### Літера В
Next up is the letter **В**. In the Ukrainian language, this letter is classified as a sonorant, and its pronunciation is actually closer to the English W than the English V. When you say it, your lips should be slightly rounded together. Do NOT put your top teeth on your bottom lip like you do when making the V sound in English! Try saying **вода́** (water) and **вовк** (wolf). Notice how your lips naturally come together? It almost sounds like English words starting with W. Great job!
> **Літера В**
> [Anna Ohoiko — Ukrainian Lessons — В](https://www.youtube.com/watch?v=aFcvYfvQ2X4)

## Дзвінкі та глухі пари — Voiced and Voiceless Pairs
In Ukrainian, consonants very often come in identical twins, which we call voiced and voiceless pairs. What does this mean? It means your mouth, lips, and tongue are in the exact same physical position for both letters, but one uses your vocal cords to make a sound, and the other uses only air.

> [!practice] Test Your Voice
> Cover your ears tightly with your hands. Now say the English sound «z» and hold it. You will hear a strong, rumbling buzz inside your head! That is a voiced consonant. Now say the English sound «s» and hold it. You will only hear air moving — no buzz at all. That is a voiceless consonant. This hands-on-ears test is the best way to feel the difference!

Let's look at the six main pairs of consonants. Practice the hands-on-ears test with each pair to really feel the contrast!

### Літери Б і П
The letter **Б** is voiced, and its partner **П** is voiceless. Your lips press together exactly the same way for both. Try saying **бабу́ся** (grandma) to feel the voiced **Б**. Then, say **паву́к** (spider) to feel the airy, voiceless **П**.
> **Літера Б**
> [Anna Ohoiko — Ukrainian Lessons — Б](https://www.youtube.com/watch?v=V1hxBE_JbGg)
>
> **Літера П**
> [Anna Ohoiko — Ukrainian Lessons — П](https://www.youtube.com/watch?v=JksSjjxyW5Y)

### Літери Д і Т
The letter **Д** is voiced, while the letter **Т** is voiceless. Feel the difference when you say the high-frequency word **дім** (house) with a strong **Д**, and compare it to **та́то** with a voiceless **Т**.
> **Літера Д**
> [Anna Ohoiko — Ukrainian Lessons — Д](https://www.youtube.com/watch?v=g4Bh-lqzd48)
>
> **Літера Т**
> [Anna Ohoiko — Ukrainian Lessons — Т](https://www.youtube.com/watch?v=m-jcLR_gK0k)

### Літери З і С
Voiced **З** and voiceless **С** make a perfect contrast pair. Try saying **зуб** (tooth) for the voiced sound, and **суп** (soup) for the voiceless sound. These are everyday words you will use constantly!
> [Anna Ohoiko — Ukrainian Lessons — З](https://www.youtube.com/watch?v=BhASNxitC1A)
>
> [Anna Ohoiko — Ukrainian Lessons — С](https://www.youtube.com/watch?v=7UsFBgSL91E)

### Літери Ж і Ш
Now meet the sibilant pair: voiced **Ж** and voiceless **Ш**. **Ж** sounds exactly like the «s» in the English word «measure», while **Ш** makes the exact sound you use when asking someone to be quiet. Compare the child-friendly word **жук** (beetle) with the everyday clothing item **ша́пка** (hat).
> [Anna Ohoiko — Ukrainian Lessons — Ж](https://www.youtube.com/watch?v=dIrGVcqPwqM)
>
> [Anna Ohoiko — Ukrainian Lessons — Ш](https://www.youtube.com/watch?v=1D-6MIw3OXY)

### Літери Г і Х
Our next pair brings us deep into the throat: voiced **Г** and voiceless **Х**. **Г** is a soft, throaty sound known as a voiced glottal fricative — it is absolutely NOT a hard «g» sound. **Х** sounds like the raspy sound in the Scottish word «loch». Feel the difference between **гора́** (mountain) and the cultural staple **хліб** (bread).
> [Anna Ohoiko — Ukrainian Lessons — Г](https://www.youtube.com/watch?v=gVnclpSI0DU)
>
> [Anna Ohoiko — Ukrainian Lessons — Х](https://www.youtube.com/watch?v=vpr58zJSJKc)

### Літери Ґ і К
The letter **Ґ** is voiced, and **К** is voiceless. The letter **Ґ** IS the hard «g» sound, exactly like the «g» in the English word «go». It is very rare and is found in only about 400 native words, like **ґа́нок** (porch). Interestingly, it was removed from the alphabet in 1933 and successfully restored in 1990! The letter **К** is its common voiceless partner, which you know from **кіт**.
> **Літера К**
> [Anna Ohoiko — Ukrainian Lessons — К](https://www.youtube.com/watch?v=J7sGEI4-xJo)

> [!warning] CRITICAL RULE: No Final Devoicing
> This is one of the most important rules for a beautiful and natural Ukrainian accent: voiced consonants stay completely voiced at the end of a word! Many other languages naturally turn final voiced consonants into voiceless ones. Ukrainian does NOT do this.
> When you say the word **зуб**, you must clearly pronounce the **б** at the end — **зуб**, NOT **зуп**. When you say **хліб**, it must end with a clear, voiced consonant: **хліб**, NOT **хліп**. This distinction takes conscious practice, but you can absolutely do it!

## Тверді та м'які — Hard and Soft Consonants
Now that we have covered how consonant sounds are made and paired together, let's look at another essential linguistic feature. Most Ukrainian consonants come in two distinct variants: hard and soft.

A consonant becomes soft (or palatalized) when it comes directly before the vowels **І**, **Я**, **Ю**, or **Є**, or when it is followed by the special soft sign letter **Ь** (which we will cover in depth in Module 4). When you make a soft consonant, the middle portion of your tongue raises upward toward the roof of your mouth, giving the sound a lighter, wetter quality.

Let's look closely at some examples you already know:
- **ліс** (forest) — the vowel **І** makes the preceding **Л** soft.
- **день** (day) — the **Д** here is hard because it comes before **Е**, which is not one of the softening vowels. The soft sign **Ь** at the end makes the **Н** soft.
- **кінь** (horse) — the **І** makes the **К** soft, and the **Ь** makes the **Н** soft. It is crucial to hear the softness here, as it changes the meaning completely from the word **кін** (end/limit)!
- **кіт** (cat) — the vowel **І** makes the **К** soft, just like in **кінь** above.
- **ніс** (nose) — the **І** makes the **Н** soft. Compare this to the hard **Н** in **на́ша** (our), where **Н** comes before **А**.
- **мій** (my) — the **І** makes the **М** soft. You will use this word constantly!

> [!tip] It's the Consonant That Changes
> Let's look at the minimal pair **лук** (bow, the weapon) and **люк** (hatch). In English, we might naturally think the vowel sound changed from an «oo» sound to a «yoo» sound. In Ukrainian, the vowel is the exact same «oo» sound in both words! It is the consonant **Л** that changes from a hard **Л** to a soft **Л**. Always focus your attention on changing the consonant, not the vowel.

There are a few important exceptions you should remember as you practice. The letters **Ж** and **Ш** are always hard, no matter what follows them. Conversely, the letter **Й** is always soft by its very nature. We will discuss the soft sign **Ь**, which explicitly forces the softening of consonants, in much more detail in our next lesson.
> **Літера Й**
> [Anna Ohoiko — Ukrainian Lessons — Й](https://www.youtube.com/watch?v=aq0cjB90s3w)

## Читання — Reading Practice
Let's practice reading all these fantastic new sounds together. Remember to read slowly and pay close attention to whether each consonant is voiced or voiceless, and whether it is hard or soft.

Let's try these voiced and voiceless pair drills. Try reading them aloud, pausing to feel the difference in your throat and mouth:
- **зуб** — **суп**
- **жук** — **ша́пка**
- **гора́** — **хор**

Now, try these minimal pairs to test your mastery of hard and soft consonants, as well as the important vowel distinctions we covered in the last module:
- **лук** — **люк** (practicing the hard **Л** versus the soft **Л**)
- **дим** (smoke) — **дім** (house) (practicing the hard **Д** versus the soft **Д**, and the difference between **И** and **І**)

Let's look at some short phrases using the vocabulary we have learned today. Look for our new target words!

> **(Вдома / At Home)**
> — Приві́т! Це дім?
> — Так, це дім.
>
> **(На кухні / In the Kitchen)**
> — Це хліб?
> — Ні, це суп. А там хліб.
> — О, до́бре!
>
> **(На вулиці / Outside)**
> — Хто це?
> — Це бабу́ся. А там лю́ди.
>
> **(У лісі / In the Forest)**
> — Це вовк?
> — Так, це вовк!
> — А там?
> — А там жук.

Excellent work! You are reading perfectly and putting all the pieces together. Keep up the wonderful progress!

## Підсумок — Summary
You have done a truly fantastic job today! We covered a vast amount of ground, and your pronunciation is getting better and more confident with every single word.

Let's quickly review the major concepts you have learned:
- We explored the 5 sonorant consonants (**Л**, **М**, **Н**, **Р**, **В**) and their musical qualities.
- We practiced the 6 voiced and voiceless pairs, testing them carefully using the hands-on-ears method.
- We discovered the hard and soft consonant system and how vowels change the consonants before them.

Before we finish this module, try answering these self-check questions:
1. What are the 5 sonorant consonants?
2. What is the voiceless partner of the letter **Б**?
3. Is **Г** a hard «g» sound or a soft, throaty sound?
4. Do voiced consonants turn voiceless at the end of a word in Ukrainian?

Next time, in Module 4, we will finally complete the entire alphabet by learning about the soft sign (**Ь**), the apostrophe, the affricates (**Ц**, **Ч**, **Щ**), the digraphs (дж, дз), and the rare letter **Ф**. See you there!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/consonant-sounds.yaml`

```yaml
- type: watch-and-repeat
  title: "Consonant Pronunciation Practice"
  instruction: "Watch each video by Anna Ohoiko, then repeat the consonant sound and example word aloud. Focus on how your mouth, lips, and tongue move."
  items:
    - letter: "Р"
      word: "риба"
      video: "https://www.youtube.com/watch?v=fMGsQ5KPQgg"
      note: "Rolled/trilled R — tongue-tip trill against the roof of your mouth"
    - letter: "В"
      word: "вода"
      video: "https://www.youtube.com/watch?v=aFcvYfvQ2X4"
      note: "Closer to English W than V — lips rounded, no teeth on lip"
    - letter: "Б"
      word: "бабуся"
      video: "https://www.youtube.com/watch?v=V1hxBE_JbGg"
      note: "Voiced — feel the buzz in your throat"
    - letter: "П"
      word: "павук"
      video: "https://www.youtube.com/watch?v=JksSjjxyW5Y"
      note: "Voiceless partner of Б — same lip position, only air"
    - letter: "Д"
      word: "дім"
      video: "https://www.youtube.com/watch?v=g4Bh-lqzd48"
      note: "Voiced — tongue touches the same spot as Т"
    - letter: "Т"
      word: "тато"
      video: "https://www.youtube.com/watch?v=m-jcLR_gK0k"
      note: "Voiceless partner of Д — same tongue position, only air"
    - letter: "З"
      word: "зуб"
      video: "https://www.youtube.com/watch?v=BhASNxitC1A"
      note: "Voiced — feel the buzz when you say it"
    - letter: "С"
      word: "суп"
      video: "https://www.youtube.com/watch?v=7UsFBgSL91E"
      note: "Voiceless partner of З — only air, no buzz"
    - letter: "Ж"
      word: "жук"
      video: "https://www.youtube.com/watch?v=dIrGVcqPwqM"
      note: "Voiced — like the s in English measure"
    - letter: "Ш"
      word: "шапка"
      video: "https://www.youtube.com/watch?v=1D-6MIw3OXY"
      note: "Voiceless partner of Ж — like English sh"
    - letter: "Г"
      word: "гора"
      video: "https://www.youtube.com/watch?v=gVnclpSI0DU"
      note: "Soft throaty sound (voiced glottal fricative) — NOT a hard g"
    - letter: "Х"
      word: "хліб"
      video: "https://www.youtube.com/watch?v=vpr58zJSJKc"
      note: "Voiceless partner of Г — like ch in Scottish loch"

- type: classify
  title: "Sort the Consonants"
  instruction: "Drag each consonant letter into the correct category based on how it is produced."
  categories:
    - label: "Sonorant (musical, voice dominates)"
      symbol_hint: "sonorant"
      items: ["Л", "М", "Н", "Р", "В"]
    - label: "Voiced (buzz in throat)"
      symbol_hint: "voiced"
      items: ["Б", "Д", "З", "Ж", "Г"]
    - label: "Voiceless (air only, no buzz)"
      symbol_hint: "voiceless"
      items: ["П", "Т", "С", "Ш", "Х"]

- type: image-to-letter
  title: "What Letter Does It Start With?"
  instruction: "Look at the picture and tap the Ukrainian consonant letter that the word starts with."
  items:
    - emoji: "🪲"
      answer: "Ж"
      distractors: ["З", "Ш", "Г"]
      note: "жук (beetle)"
    - emoji: "🧢"
      answer: "Ш"
      distractors: ["Ж", "С", "Щ"]
      note: "шапка (hat)"
    - emoji: "🤚"
      answer: "Р"
      distractors: ["Л", "Н", "М"]
      note: "рука (hand)"
    - emoji: "🐺"
      answer: "В"
      distractors: ["Б", "Г", "Д"]
      note: "вовк (wolf)"
    - emoji: "🏔️"
      answer: "Г"
      distractors: ["Ґ", "Х", "К"]
      note: "гора (mountain)"
    - emoji: "🍞"
      answer: "Х"
      distractors: ["Г", "К", "Ш"]
      note: "хліб (bread)"
    - emoji: "🐱"
      answer: "К"
      distractors: ["Ґ", "Х", "Г"]
      note: "кіт (cat)"
    - emoji: "🕷️"
      answer: "П"
      distractors: ["Б", "Т", "В"]
      note: "павук (spider)"
    - emoji: "🌌"
      answer: "Н"
      distractors: ["М", "Л", "В"]
      note: "небо (sky)"

- type: match-up
  title: "Match Voiced to Voiceless Partner"
  instruction: "Each voiced consonant has a voiceless partner. Match them together."
  pairs:
    - left: "Б (voiced)"
      right: "П (voiceless)"
    - left: "Д (voiced)"
      right: "Т (voiceless)"
    - left: "З (voiced)"
      right: "С (voiceless)"
    - left: "Ж (voiced)"
      right: "Ш (voiceless)"
    - left: "Г (voiced)"
      right: "Х (voiceless)"
    - left: "Ґ (voiced)"
      right: "К (voiceless)"

- type: quiz
  title: "Voiced or Voiceless? The Hands-on-Ears Test"
  instruction: "Imagine covering your ears and saying each sound. Would you hear a buzz (voiced) or only air (voiceless)?"
  items:
    - question: "You cover your ears and say the Б sound. What do you hear?"
      options:
        - text: "A strong buzz — it is voiced"
          correct: true
        - text: "Only air — it is voiceless"
          correct: false
        - text: "Nothing at all"
          correct: false
        - text: "A whistle sound"
          correct: false
      explanation: "Б is a voiced consonant. When you cover your ears, you hear a clear buzz because your vocal cords vibrate."
    - question: "You cover your ears and say the П sound. What do you hear?"
      options:
        - text: "Only air — it is voiceless"
          correct: true
        - text: "A strong buzz — it is voiced"
          correct: false
        - text: "A humming sound"
          correct: false
        - text: "A clicking sound"
          correct: false
      explanation: "П is the voiceless partner of Б. Your lips are in the same position, but your vocal cords do not vibrate."
    - question: "Which consonant in the pair З/С is voiceless?"
      options:
        - text: "С"
          correct: true
        - text: "З"
          correct: false
        - text: "Both are voiceless"
          correct: false
        - text: "Neither is voiceless"
          correct: false
      explanation: "С is voiceless (only air). З is its voiced partner (you hear a buzz)."
    - question: "You cover your ears and say the Ж sound. What do you hear?"
      options:
        - text: "A buzz — it is voiced"
          correct: true
        - text: "Only air — it is voiceless"
          correct: false
        - text: "A high-pitched ring"
          correct: false
        - text: "Silence"
          correct: false
      explanation: "Ж is voiced, like the s in English measure. Its voiceless partner is Ш."
    - question: "Which of these consonants is voiceless?"
      options:
        - text: "Т"
          correct: true
        - text: "Д"
          correct: false
        - text: "Б"
          correct: false
        - text: "Ж"
          correct: false
      explanation: "Т is voiceless. Д, Б, and Ж are all voiced consonants."
    - question: "You cover your ears and say the М sound. What do you hear?"
      options:
        - text: "A strong buzz — it is a sonorant"
          correct: true
        - text: "Only air — it is voiceless"
          correct: false
        - text: "A quiet hiss"
          correct: false
        - text: "A sharp click"
          correct: false
      explanation: "М is a sonorant consonant. Sonorants are the most musical sounds — your voice completely dominates."
    - question: "Which consonant is the voiceless partner of Г?"
      options:
        - text: "Х"
          correct: true
        - text: "К"
          correct: false
        - text: "Ґ"
          correct: false
        - text: "Ш"
          correct: false
      explanation: "Х is the voiceless partner of Г. Remember, К is the voiceless partner of Ґ (not Г)."
    - question: "You cover your ears and say the Ш sound. What do you hear?"
      options:
        - text: "Only air — it is voiceless"
          correct: true
        - text: "A strong buzz — it is voiced"
          correct: false
        - text: "A deep hum"
          correct: false
        - text: "A musical tone"
          correct: false
      explanation: "Ш is voiceless (like English sh). Its voiced partner is Ж."
    - question: "In Ukrainian, what happens to the Б sound at the end of the word зуб?"
      options:
        - text: "It stays voiced — you say зуб"
          correct: true
        - text: "It becomes voiceless — you say зуп"
          correct: false
        - text: "It disappears completely"
          correct: false
        - text: "It becomes soft"
          correct: false
      explanation: "Ukrainian voiced consonants stay voiced at the end of a word. Many other languages devoice them — Ukrainian doesn't!"
    - question: "Which of these is NOT a sonorant consonant?"
      options:
        - text: "Б"
          correct: true
        - text: "Л"
          correct: false
        - text: "М"
          correct: false
        - text: "Р"
          correct: false
      explanation: "Б is a voiced consonant (not a sonorant). The 5 sonorants are Л, М, Н, Р, and В."

- type: classify
  title: "Hard or Soft Consonant?"
  instruction: "Look at the underlined consonant in each word. Is it hard or soft? Remember, consonants become soft before І, Я, Ю, Є, or the soft sign Ь."
  categories:
    - label: "Hard consonant"
      symbol_hint: "hard"
      items:
        - "лук (Л before У)"
        - "дим (Д before И)"
        - "вовк (В before О)"
        - "зуб (З before У)"
        - "суп (С before У)"
        - "жук (Ж — always hard)"
        - "шапка (Ш — always hard)"
        - "гора (Г before О)"
    - label: "Soft consonant"
      symbol_hint: "soft"
      items:
        - "ліс (Л before І)"
        - "люк (Л before Ю)"
        - "дім (Д before І)"
        - "кінь (Н before Ь)"
        - "ніч (Н before І)"
        - "кіт (К before І)"
        - "день (Н before Ь)"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/consonant-sounds.yaml`

```yaml
items:
  - lemma: "хліб"
    translation: "bread"
    pos: "noun"
    gender: "m"
    notes: "Cultural staple; demonstrates Х; no-devoicing rule — say хліб, not хліп"
    usage: "Це хліб."
  - lemma: "зуб"
    translation: "tooth"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates З; no-devoicing drill — say зуб, not зуп"
    usage: "Це зуб."
  - lemma: "дім"
    translation: "house"
    pos: "noun"
    gender: "m"
    notes: "High-frequency; demonstrates soft Д before І; minimal pair with дим"
    usage: "Це дім."
  - lemma: "вовк"
    translation: "wolf"
    pos: "noun"
    gender: "m"
    notes: "Tale vocabulary; demonstrates В as sonorant (closer to English W)"
    usage: "Це вовк."
  - lemma: "жук"
    translation: "beetle"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates voiced Ж; textbook word (Bolshakova)"
    usage: "Це жук."
  - lemma: "шапка"
    translation: "hat"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates voiceless Ш; everyday clothing"
    usage: "Це шапка."
  - lemma: "гора"
    translation: "mountain"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Г (voiced glottal fricative, NOT a hard g)"
    usage: "Це гора."
  - lemma: "небо"
    translation: "sky"
    pos: "noun"
    gender: "n"
    notes: "High-frequency; demonstrates Н"
    usage: "Це небо."
  - lemma: "рука"
    translation: "hand"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Р (rolled/trilled R); body vocabulary"
    usage: "Це рука."
  - lemma: "бабуся"
    translation: "grandma"
    pos: "noun"
    gender: "f"
    notes: "High-frequency family word; demonstrates voiced Б"
    usage: "Це бабуся."
  - lemma: "павук"
    translation: "spider"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates voiceless П; textbook word (Bolshakova)"
    usage: "Це павук."
  - lemma: "ґанок"
    translation: "porch"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates rare Ґ (hard g); one of ~400 native Ґ words"
    usage: "Це ґанок."
  - lemma: "кінь"
    translation: "horse"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates soft Н before Ь; minimal pair with кін (end/limit)"
    usage: "Це кінь."
  - lemma: "людина"
    translation: "person, people (люди)"
    pos: "noun"
    gender: "f"
    notes: "High-frequency; demonstrates soft Л before Ю; plural люди used in content"
    usage: "Це люди."
  - lemma: "суп"
    translation: "soup"
    pos: "noun"
    gender: "m"
    notes: "Voiceless pair drill with зуб; everyday food word"
    usage: "Це суп."
  - lemma: "вода"
    translation: "water"
    pos: "noun"
    gender: "f"
    notes: "High-frequency; demonstrates В as sonorant"
    usage: "Це вода."
  - lemma: "дим"
    translation: "smoke"
    pos: "noun"
    gender: "m"
    notes: "Hard Д before И; minimal pair with дім (house)"
    usage: "Це дим."
  - lemma: "люк"
    translation: "hatch"
    pos: "noun"
    gender: "m"
    notes: "Soft Л before Ю; minimal pair with лук (bow)"
    usage: "Це люк."
  - lemma: "риба"
    translation: "fish"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Р (rolled/trilled); pronunciation practice word"
    usage: "Це риба."
  - lemma: "ліс"
    translation: "forest"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates soft Л before І; high-frequency nature word"
    usage: "Це ліс."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/consonant-sounds.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/consonant-sounds.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/consonant-sounds.yaml`

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

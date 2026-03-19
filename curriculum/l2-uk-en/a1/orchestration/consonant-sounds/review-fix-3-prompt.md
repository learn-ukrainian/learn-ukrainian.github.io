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

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:classify`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 14 items
  - Fix: Add 1 more items to 'classify' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Entire module — all sections, Line 98 / Section "Тверді та м'які — Hard and Soft Consonants", Lines 39 and 125 / Sections "Дзвінкі та глухі пари — Voiced and Voiceless Pairs" and "Читання — Reading Practice", Lines 85 and 88 / Section "Дзвінкі та глухі пари — Voiced and Voiceless Pairs", Lines 86-87 / Section "Дзвінкі та глухі пари — Voiced and Voiceless Pairs"

### Finding 1: Linguistic Error — "день" consonant analysis (CRITICAL)
**Location**: Line 98 / Section "Тверді та м'які — Hard and Soft Consonants"
**Problem**: Е does NOT soften consonants in Ukrainian. Line 94 of the SAME module correctly lists only І, Я, Ю, Є as softening vowels — Е is absent. Bolshakova Grade 2 (p. 43) confirms: "На письмі м'які приголосні позначають буквами і, я, ю, є та знаком м'якшення ь." In "день" [den′], the Д is HARD before Е. Only the Н is soft (before Ь). This directly contradicts the module's own rule and teaches a wrong phonological fact.
**Required Fix**: Change to `- **день** (hard **Д** before **Е**, soft **Н** because of **Ь**)` — or better, replace "день" with a word that demonstrates soft Д unambiguously, such as **дія** (action — soft **Д** because of **І**) or **діти** (children — soft **Д** because of **І**). Given this is A1.1 with limited vocabulary, the simplest fix is correcting the analysis of "день" and noting that Д here is hard.
**Severity**: HIGH

### Finding 2: IPA Brackets Banned (HIGH — D.0 confirmed)
**Location**: Lines 86-87 / Section "Дзвінкі та глухі пари — Voiced and Voiceless Pairs"
**Problem**: Square-bracket phonetic notation [б], [п] is banned in the curriculum. Only stress marks (´) are allowed for pronunciation guidance.
**Required Fix**: Rewrite without brackets: "**зуб** is always pronounced with a clear voiced **б** at the end, NOT as a **п**." Same pattern for хліб.
**Severity**: HIGH

### Finding 3: Imperative "закрий" — morphological scope violation (HIGH — D.0 confirmed)
**Location**: Lines 39 and 125 / Sections "Дзвінкі та глухі пари — Voiced and Voiceless Pairs" and "Читання — Reading Practice"
**Problem**: "закрий" is a perfective imperative (verb:perf:impr:s:2 per VESUM). Imperatives are not taught until M47. While this is a quoted textbook instruction (Bolshakova Grade 2 uses "закрий долонями вуха"), using Ukrainian imperatives in A1.1 content where learners have ZERO verb knowledge creates confusion.
**Required Fix**: Replace with English instruction: "Cover your ears with your hands" (the hands-on-ears test). Remove the bold Ukrainian imperative phrase.
**Severity**: HIGH

### Finding 4: Zero Engagement Boxes — Audit Gate FAIL (HIGH)
**Location**: Entire module — all sections
**Problem**: Audit shows engagement: 0/2. The only callout is a `[!practice]` on line 29 (「> [!practice] Let's Review M, N, L」). No `[!did-you-know]`, `[!culture-note]`, or `[!fun-fact]` boxes exist. The research notes explicitly provide cultural hooks: (1) хліб і сіль hospitality tradition, (2) скоромовка tongue twister for Ж, (3) вовк in folk tales. None were used.
**Required Fix**: Add at least 2 engagement callouts. Suggested placements:
**Severity**: HIGH

### Finding 5: Colonial Framing (MEDIUM)
**Location**: Lines 85 and 88 / Section "Дзвінкі та глухі пари — Voiced and Voiceless Pairs"
**Problem**: Defines Ukrainian phonology by contrast with Russian. While the devoicing contrast IS pedagogically important for English speakers who also know German or Russian, the framing should present the Ukrainian rule first, then add a warning for learners who know those languages. Currently, the Russian/German rule is stated FIRST, which makes Ukrainian sound like the exception rather than the norm.
**Required Fix**: Reframe: Lead with the Ukrainian rule ("In Ukrainian, voiced consonants ALWAYS stay voiced at the end of a word. **зуб** always ends with a clear **б**. **хліб** always ends with a clear **б**."). Then add a `[!tip]` for learners who know German or other languages: "If you speak German or another language where final consonants become voiceless, be careful — Ukrainian keeps them voiced!"
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Linguistic Error — "день" consonant analysis (CRITICAL)
- **Location**: Line 98 / Section "Тверді та м'які — Hard and Soft Consonants"
- **Original**: 「- **день** (soft **Д** because of **Е**, soft **Н** because of **Ь**)」
- **Problem**: Е does NOT soften consonants in Ukrainian. Line 94 of the SAME module correctly lists only І, Я, Ю, Є as softening vowels — Е is absent. Bolshakova Grade 2 (p. 43) confirms: "На письмі м'які приголосні позначають буквами і, я, ю, є та знаком м'якшення ь." In "день" [den′], the Д is HARD before Е. Only the Н is soft (before Ь). This directly contradicts the module's own rule and teaches a wrong phonological fact.
- **Fix**: Change to `- **день** (hard **Д** before **Е**, soft **Н** because of **Ь**)` — or better, replace "день" with a word that demonstrates soft Д unambiguously, such as **дія** (action — soft **Д** because of **І**) or **діти** (children — soft **Д** because of **І**). Given this is A1.1 with limited vocabulary, the simplest fix is correcting the analysis of "день" and noting that Д here is hard.

### Issue 2: IPA Brackets Banned (HIGH — D.0 confirmed)
- **Location**: Lines 86-87 / Section "Дзвінкі та глухі пари — Voiced and Voiceless Pairs"
- **Original**: 「- **зуб** is pronounced зу[б], NOT зу[п].」 and 「- **хліб** is pronounced хлі[б], NOT хлі[п].」
- **Problem**: Square-bracket phonetic notation [б], [п] is banned in the curriculum. Only stress marks (´) are allowed for pronunciation guidance.
- **Fix**: Rewrite without brackets: "**зуб** is always pronounced with a clear voiced **б** at the end, NOT as a **п**." Same pattern for хліб.

### Issue 3: Imperative "закрий" — morphological scope violation (HIGH — D.0 confirmed)
- **Location**: Lines 39 and 125 / Sections "Дзвінкі та глухі пари — Voiced and Voiceless Pairs" and "Читання — Reading Practice"
- **Original**: 「закрий долонями вуха」 (lines 39, 125)
- **Problem**: "закрий" is a perfective imperative (verb:perf:impr:s:2 per VESUM). Imperatives are not taught until M47. While this is a quoted textbook instruction (Bolshakova Grade 2 uses "закрий долонями вуха"), using Ukrainian imperatives in A1.1 content where learners have ZERO verb knowledge creates confusion.
- **Fix**: Replace with English instruction: "Cover your ears with your hands" (the hands-on-ears test). Remove the bold Ukrainian imperative phrase.

### Issue 4: Zero Engagement Boxes — Audit Gate FAIL (HIGH)
- **Location**: Entire module — all sections
- **Problem**: Audit shows engagement: 0/2. The only callout is a `[!practice]` on line 29 (「> [!practice] Let's Review M, N, L」). No `[!did-you-know]`, `[!culture-note]`, or `[!fun-fact]` boxes exist. The research notes explicitly provide cultural hooks: (1) хліб і сіль hospitality tradition, (2) скоромовка tongue twister for Ж, (3) вовк in folk tales. None were used.
- **Fix**: Add at least 2 engagement callouts. Suggested placements:
  - After line 27 (section "Сонорні — Sonorant Consonants"): `[!did-you-know]` about вовк in Ukrainian folk tales (сірий вовк)
  - After line 74 or 76 (section "Дзвінкі та глухі пари — Voiced and Voiceless Pairs"): `[!culture-note]` about хліб і сіль (bread and salt) hospitality tradition — both words appear in this module

### Issue 5: Colonial Framing (MEDIUM)
- **Location**: Lines 85 and 88 / Section "Дзвінкі та глухі пари — Voiced and Voiceless Pairs"
- **Original**: 「In languages like German or Russian, voiced consonants at the end of a word become voiceless. Ukrainian does NOT do this!」 (line 85) and 「This is different from Russian and German.」 (line 88)
- **Problem**: Defines Ukrainian phonology by contrast with Russian. While the devoicing contrast IS pedagogically important for English speakers who also know German or Russian, the framing should present the Ukrainian rule first, then add a warning for learners who know those languages. Currently, the Russian/German rule is stated FIRST, which makes Ukrainian sound like the exception rather than the norm.
- **Fix**: Reframe: Lead with the Ukrainian rule ("In Ukrainian, voiced consonants ALWAYS stay voiced at the end of a word. **зуб** always ends with a clear **б**. **хліб** always ends with a clear **б**."). Then add a `[!tip]` for learners who know German or other languages: "If you speak German or another language where final consonants become voiceless, be careful — Ukrainian keeps them voiced!"

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 98 | 「soft **Д** because of **Е**」 | hard **Д** before **Е** | Grammar error |
| 86 | 「зу[б], NOT зу[п]」 | with a clear voiced **б**, NOT as **п** | IPA banned |
| 87 | 「хлі[б], NOT хлі[п]」 | with a clear voiced **б**, NOT as **п** | IPA banned |
| 39 | 「закрий долонями вуха」 | English instruction | Scope violation |
| 125 | 「закрий долонями вуха」 | English instruction | Scope violation |

---

## Fix Plan to Reach 9/10 (REQUIRED — score is 8.0)

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Line 98: Change 「soft **Д** because of **Е**」 → "hard **Д** before **Е**" — eliminates the contradition with line 94's correct rule
2. Lines 86-87: Remove [б]/[п] brackets, use bold letter names instead — eliminates IPA violations
3. Lines 39, 125: Replace 「закрий долонями вуха」 with English "cover your ears with your hands" — eliminates imperative scope violation

**Expected score after fix:** 9/10

### Language: 7/10 → 9/10
**What to fix:**
1. Lines 84-88: Reframe the no-devoicing section to lead with the Ukrainian rule, then add a tip for speakers of other languages — eliminates colonial framing
2. Line 88: Remove "This is different from Russian and German" — redundant after reframe

**Expected score after fix:** 9/10

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add `[!did-you-know]` about вовк in Ukrainian folk tales after line 27 in section "Сонорні — Sonorant Consonants"
2. Add `[!culture-note]` about хліб і сіль tradition after line 76 in section "Дзвінкі та глухі пари — Voiced and Voiceless Pairs"

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 8.5×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.2 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9
= 78.5 / 8.9 = 8.8/10
```

---

## Audit Failures (from automated re-audit)

```
--- STRICT GATES (Level A1) ---
❌ [REVIEW_VERDICT_FAIL] Review concludes with **Status:** FAIL — the reviewer identified issues that need to be fixed before the module can pass. Run Phase D.2 repair or rebuild the module.
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

Welcome back! In our first module, we gave you a complete overview of the 33-letter Ukrainian alphabet. Then, in Module 2, you mastered all ten vowels and discovered the beauty of pure vowel sounds. Today, we focus on the remaining 22 letters — the consonant sounds.

We are going to organize them not by alphabetical order, but by how your mouth produces them. You will learn about sonorant consonants (the "musical" sounds), voiced and voiceless pairs, and the crucial distinction between hard and soft consonants. All ten vowels you already know from Module 2 are available for us to practice with. By the end of this module, you will have a solid grasp of consonant pronunciation and classification, unlocking your ability to read many more Ukrainian words. Let's begin!

## Сонорні — Sonorant Consonants

In Ukrainian, sonorant consonants — **сонорні приголосні** — are the "musical" sounds. When you pronounce them, your voice dominates over the noise. There are exactly five sonorants in the language: **Л**, **М**, **Н**, **Р**, and **В**. You already know **Л**, **М**, and **Н** from Module 1. Think of the soft, flowing sound in a word like **небо** (sky).

Now, let's look at the two new sonorants that often trick English speakers.

First is **Р**. This is the rolled or trilled R! It looks exactly like the English P, but it sounds completely different. To pronounce it, you need to practice the tongue-tip trill. Relax your tongue and let the tip vibrate against the roof of your mouth right behind your upper teeth. Listen to the video below and try it yourself.

[Anna Ohoiko — Ukrainian Lessons — Р](https://www.youtube.com/watch?v=fMGsQ5KPQgg)

Here are two great words to practice the trilled R:
- **риба** (fish)
- **рука** (hand)

Next is **В**. This letter is also a sonorant in Ukrainian. It is much closer to the English W than the English V. When you say it, keep your lips rounded. Do NOT put your teeth on your lower lip! Feel the air flow freely.

[Anna Ohoiko — Ukrainian Lessons — В](https://www.youtube.com/watch?v=aFcvYfvQ2X4)

Try saying these words with rounded lips:
- **вода** (water)
- **вовк** (wolf)

> [!did-you-know] Вовк in Ukrainian Folk Tales
> The grey wolf — **сірий вовк** — is one of the most beloved characters in Ukrainian folk tales (**казки**). He appears in nearly every classic story! Now you can say his name with the correct Ukrainian **В** sound.

> [!practice] Let's Review M, N, L
> Let's listen to the other sonorants you met earlier. Try to hear the "musical" quality in all five of these letters!
> [Anna Ohoiko — Ukrainian Lessons — М](https://www.youtube.com/watch?v=Ez95H4ibuJo)
> [Anna Ohoiko — Ukrainian Lessons — Н](https://www.youtube.com/watch?v=vNUfiKHPYaU)
> [Anna Ohoiko — Ukrainian Lessons — Л](https://www.youtube.com/watch?v=v6-3Xg52Buk)

## Дзвінкі та глухі пари — Voiced and Voiceless Pairs

Now we move to consonants that rely more on noise. Many of these come in matched pairs. They share the exact same mouth position, but one uses your vocal cords and the other does not.

To tell the difference, we will use the hands-on-ears test. Cover your ears tightly with your hands. Now say "zzzzz" and then "sssss". When you say a voiced consonant (**дзвінкий**), you will hear a loud buzz inside your head. When you say a voiceless consonant (**глухий**), you will only hear the rush of air. Each pair is identical in mouth position, just with different voicing.

Let's explore the six main pairs. Try the hands-on-ears test with each one!

### Б and П
**Б** is voiced, **П** is voiceless.
- **бабуся** (grandma)
- **павук** (spider)
[Anna Ohoiko — Ukrainian Lessons — Б](https://www.youtube.com/watch?v=V1hxBE_JbGg)
[Anna Ohoiko — Ukrainian Lessons — П](https://www.youtube.com/watch?v=JksSjjxyW5Y)

### Д and Т
**Д** is voiced, **Т** is voiceless.
- **дім** (house)
- **тато** (M1 review)
[Anna Ohoiko — Ukrainian Lessons — Д](https://www.youtube.com/watch?v=g4Bh-lqzd48)
[Anna Ohoiko — Ukrainian Lessons — Т](https://www.youtube.com/watch?v=m-jcLR_gK0k)

### З and С
**З** is voiced, **С** is voiceless.
- **зуб** (tooth)
- **суп** (soup)
[Anna Ohoiko — Ukrainian Lessons — З](https://www.youtube.com/watch?v=BhASNxitC1A)
[Anna Ohoiko — Ukrainian Lessons — С](https://www.youtube.com/watch?v=7UsFBgSL91E)

### Ж and Ш
**Ж** is a voiced sibilant, sounding like the 'zh' in 'measure'. **Ш** is voiceless, sounding like the English 'sh'.
- **жук** (beetle)
- **шапка** (hat)
[Anna Ohoiko — Ukrainian Lessons — Ж](https://www.youtube.com/watch?v=dIrGVcqPwqM)
[Anna Ohoiko — Ukrainian Lessons — Ш](https://www.youtube.com/watch?v=1D-6MIw3OXY)

### Г and Х
This pair is uniquely Ukrainian. **Г** is a soft, throaty sound — a voiced glottal fricative. It is NOT a hard 'g' like the English 'go'. It sounds more like a heavy, voiced 'h'. **Х** is its voiceless partner, sounding like the heavy 'ch' in the German word 'ach' or the Scottish 'loch'.
- **гора** (mountain)
- **хліб** (bread)
[Anna Ohoiko — Ukrainian Lessons — Г](https://www.youtube.com/watch?v=gVnclpSI0DU)
[Anna Ohoiko — Ukrainian Lessons — Х](https://www.youtube.com/watch?v=vpr58zJSJKc)

> [!culture-note] Хліб і сіль — Bread and Salt
> In Ukrainian tradition, welcoming guests with **хліб і сіль** (bread and salt) is the highest symbol of hospitality. Both **Х** (from **хліб**) and **С** (from **сіль**) are consonant sounds you are learning in this module!

### Ґ and К
**Ґ** IS the hard 'g' (like in 'go'), and **К** is voiceless. The letter **Ґ** is extremely rare, found in only about 400 native words. It was actually removed from the alphabet in 1933 and restored in 1990!
- **ґанок** (porch)
- **кіт** (M1 review)
[Anna Ohoiko — Ukrainian Lessons — К](https://www.youtube.com/watch?v=J7sGEI4-xJo)

**CRITICAL RULE: No Final Devoicing!**
In Ukrainian, voiced consonants ALWAYS stay voiced at the end of a word. You must pronounce the final consonant clearly — no swallowing it into a voiceless sound!
- **зуб** always ends with a clear, voiced **б** — never as **п**.
- **хліб** keeps its voiced **б** at the end too. Say it: хліб, not "хліп"!

> [!tip] Learner Warning
> If you speak German or another language where final consonants become voiceless, pay extra attention here. Ukrainian keeps them voiced — always!

## Тверді та м'які — Hard and Soft Consonants

The final major concept in Ukrainian phonetics is the difference between hard and soft consonants. Most Ukrainian consonants come in hard (**твердий**) and soft (**м'який**) variants.

A consonant becomes soft (palatalized) when you push the middle of your tongue up toward the roof of your mouth. How do you know when to do this? A consonant becomes soft when it is placed before the vowels **І**, **Я**, **Ю**, or **Є**, or when it is followed by the soft sign **Ь** (which is covered in Module 4).

Look at these examples of soft consonants:
- **ліс** (soft **Л** because of **І**)
- **день** (hard **Д** before **Е**, soft **Н** because of **Ь**)
- **кінь** (horse — soft **К** because of **І**, soft **Н** because of **Ь**)
- **люди** (people — soft **Л** because of **Ю**)

Let's compare a minimal pair where the soft consonant changes the entire meaning. Remember, the consonant changes, not the vowel!
- **лук** (hard **Л** — bow (weapon))
- **люк** (soft **Л** — hatch)

There are a few important exceptions to the hard and soft system:
- **Ж** and **Ш** are always hard.
- **Й** is always soft.
[Anna Ohoiko — Ukrainian Lessons — Й](https://www.youtube.com/watch?v=aq0cjB90s3w)

We will dive into the specific details of the soft sign (**Ь**) — the letter that exists solely to force softening — in Module 4!

## Читання — Reading Practice

Now let's practice reading words using the full consonant inventory alongside the vowels you mastered in Module 2.

We are focusing entirely on pronunciation. Here are some basic noun phrases. Practice reading them aloud, paying close attention to your sonorants and voiced/voiceless pairs.

> **Це дім.**
> **Це хліб.**
> **Ось бабуся.**
> **Тут вода.**
> **Це небо.**

Next, try these voiced/voiceless pair drills. Do the hands-on-ears test if you need to feel the buzz!
- **зуб** — **суп**
- **жук** — **шапка**
- **гора** — **хор**

Finally, practice these minimal pairs. Notice how a single phonetic change alters the word completely:
- Hard vs. Soft: **лук** (hard **Л**) vs. **люк** (soft **Л**)
- Vowel shift (**И** vs **І**): **дим** (smoke, voiced **Д**) vs. **дім** (house, soft voiced **Д**)

Remember to keep your lips rounded for **В**, roll your **Р**, and never devoice those final consonants!

## Підсумок — Summary

Let's review what we learned today.

You now know the 5 sonorants (**Л**, **М**, **Н**, **Р**, **В**) and the 6 voiced/voiceless consonant pairs. You have also been introduced to the hard/soft consonant system, driven by softening vowels.

**Self-check:**
- What are the 5 sonorants?
- What is the voiceless partner of **Б**?
- Is **Г** a hard 'g' or a soft throaty sound?
- Do voiced consonants devoice at the word end?

Next time, in Module 4, we will complete the alphabet! We will cover the soft sign (**Ь**), the apostrophe, the affricates (**Ц**, **Ч**, **Щ**), digraphs (**ДЖ**, **ДЗ**), and the rare **Ф**. Keep practicing your new sounds!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/consonant-sounds.yaml`

```yaml
- type: watch-and-repeat
  title: "Consonant Pronunciation Practice"
  instruction: "Watch each video, then repeat the sound and example word aloud. Focus on how each consonant is produced."
  items:
    - letter: "Р"
      word: "риба"
      video: "https://www.youtube.com/watch?v=fMGsQ5KPQgg"
      note: "Rolled/trilled R — let your tongue tip vibrate"
    - letter: "В"
      word: "вода"
      video: "https://www.youtube.com/watch?v=aFcvYfvQ2X4"
      note: "Closer to English W — keep lips rounded, no teeth on lip"
    - letter: "Б"
      word: "бабуся"
      video: "https://www.youtube.com/watch?v=V1hxBE_JbGg"
      note: "Voiced — feel the buzz in your throat"
    - letter: "П"
      word: "павук"
      video: "https://www.youtube.com/watch?v=JksSjjxyW5Y"
      note: "Voiceless partner of Б — same mouth position, no buzz"
    - letter: "Д"
      word: "дім"
      video: "https://www.youtube.com/watch?v=g4Bh-lqzd48"
      note: "Voiced — tongue touches upper teeth"
    - letter: "Т"
      word: "тато"
      video: "https://www.youtube.com/watch?v=m-jcLR_gK0k"
      note: "Voiceless partner of Д"
    - letter: "З"
      word: "зуб"
      video: "https://www.youtube.com/watch?v=BhASNxitC1A"
      note: "Voiced — like English Z"
    - letter: "С"
      word: "суп"
      video: "https://www.youtube.com/watch?v=7UsFBgSL91E"
      note: "Voiceless partner of З — like English S"
    - letter: "Ж"
      word: "жук"
      video: "https://www.youtube.com/watch?v=dIrGVcqPwqM"
      note: "Voiced — like ZH in measure"
    - letter: "Ш"
      word: "шапка"
      video: "https://www.youtube.com/watch?v=1D-6MIw3OXY"
      note: "Voiceless partner of Ж — like English SH"
    - letter: "Г"
      word: "гора"
      video: "https://www.youtube.com/watch?v=gVnclpSI0DU"
      note: "Soft throaty sound — NOT a hard G"
    - letter: "Х"
      word: "хліб"
      video: "https://www.youtube.com/watch?v=vpr58zJSJKc"
      note: "Voiceless partner of Г — like CH in Scottish loch"

- type: classify
  title: "Sort the Consonants"
  instruction: "Drag each consonant into the correct category based on how it is produced."
  categories:
    - label: "Sonorant (musical, voice dominates)"
      symbol_hint: "sonorant"
      items: ["Л", "М", "Н", "Р", "В"]
    - label: "Voiced (buzz with vocal cords)"
      symbol_hint: "voiced"
      items: ["Б", "Д", "З", "Ж", "Г", "Ґ"]
    - label: "Voiceless (air only, no buzz)"
      symbol_hint: "voiceless"
      items: ["П", "Т", "С", "Ш", "Х", "К"]

- type: image-to-letter
  title: "What Letter Does It Start With?"
  instruction: "Look at the picture. Which Ukrainian consonant does this word start with?"
  items:
    - emoji: "🐛"
      answer: "Ж"
      distractors: ["Ш", "З"]
      note: "жук (beetle)"
    - emoji: "🧢"
      answer: "Ш"
      distractors: ["Ж", "С"]
      note: "шапка (hat)"
    - emoji: "✋"
      answer: "Р"
      distractors: ["Л", "Н"]
      note: "рука (hand)"
    - emoji: "🐟"
      answer: "Р"
      distractors: ["Л", "В"]
      note: "риба (fish)"
    - emoji: "🏔️"
      answer: "Г"
      distractors: ["Х", "К"]
      note: "гора (mountain)"
    - emoji: "🐺"
      answer: "В"
      distractors: ["Б", "Г"]
      note: "вовк (wolf)"
    - emoji: "🍞"
      answer: "Х"
      distractors: ["Г", "К"]
      note: "хліб (bread)"
    - emoji: "🕷️"
      answer: "П"
      distractors: ["Б", "В"]
      note: "павук (spider)"

- type: match-up
  title: "Voiced and Voiceless Partners"
  instruction: "Match each voiced consonant on the left to its voiceless partner on the right."
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
  title: "Hands-on-Ears Test"
  instruction: "Imagine covering your ears and saying each consonant. Would you hear a buzz (voiced) or just air (voiceless)?"
  items:
    - question: "You say the sound for Б. Do you feel a buzz or just air?"
      explanation: "Б is voiced — you would feel a strong buzz when you cover your ears and say it."
      options:
        - text: "Buzz (voiced)"
          correct: true
        - text: "Air only (voiceless)"
          correct: false
        - text: "It is a sonorant"
          correct: false
        - text: "No sound at all"
          correct: false
    - question: "You say the sound for С. Do you feel a buzz or just air?"
      explanation: "С is voiceless — you only hear the rush of air, no buzz."
      options:
        - text: "Buzz (voiced)"
          correct: false
        - text: "Air only (voiceless)"
          correct: true
        - text: "It is a sonorant"
          correct: false
        - text: "No sound at all"
          correct: false
    - question: "You say the sound for Ж. Do you feel a buzz or just air?"
      explanation: "Ж is voiced — like the ZH in English measure. You feel a buzz."
      options:
        - text: "Buzz (voiced)"
          correct: true
        - text: "Air only (voiceless)"
          correct: false
        - text: "It is a sonorant"
          correct: false
        - text: "No sound at all"
          correct: false
    - question: "You say the sound for Х. Do you feel a buzz or just air?"
      explanation: "Х is voiceless — like the CH in Scottish loch. Air only, no buzz."
      options:
        - text: "Buzz (voiced)"
          correct: false
        - text: "Air only (voiceless)"
          correct: true
        - text: "It is a sonorant"
          correct: false
        - text: "No sound at all"
          correct: false
    - question: "You say the sound for Д. Do you feel a buzz or just air?"
      explanation: "Д is voiced — its voiceless partner is Т."
      options:
        - text: "Buzz (voiced)"
          correct: true
        - text: "Air only (voiceless)"
          correct: false
        - text: "It is a sonorant"
          correct: false
        - text: "No sound at all"
          correct: false
    - question: "You say the sound for П. Do you feel a buzz or just air?"
      explanation: "П is voiceless — its voiced partner is Б."
      options:
        - text: "Buzz (voiced)"
          correct: false
        - text: "Air only (voiceless)"
          correct: true
        - text: "It is a sonorant"
          correct: false
        - text: "No sound at all"
          correct: false
    - question: "What type of consonant is Р?"
      explanation: "Р is a sonorant — one of the 5 musical consonants where voice dominates over noise."
      options:
        - text: "Sonorant"
          correct: true
        - text: "Voiced (non-sonorant)"
          correct: false
        - text: "Voiceless"
          correct: false
        - text: "Always soft"
          correct: false
    - question: "What type of consonant is В?"
      explanation: "В is a sonorant in Ukrainian — one of the 5 musical consonants (Л М Н Р В)."
      options:
        - text: "Sonorant"
          correct: true
        - text: "Voiced (non-sonorant)"
          correct: false
        - text: "Voiceless"
          correct: false
        - text: "Always hard"
          correct: false
    - question: "The Ukrainian letter Г sounds like the English hard G in go. True or false?"
      explanation: "Г is a soft, throaty sound (voiced glottal fricative), NOT a hard G. The hard G sound is Ґ."
      options:
        - text: "True — Г is like English G"
          correct: false
        - text: "False — Г is a soft throaty sound"
          correct: true
        - text: "False — Г is voiceless"
          correct: false
        - text: "True — Г and Ґ sound the same"
          correct: false
    - question: "In Ukrainian, voiced consonants become voiceless at the end of a word (like in Russian or German). True or false?"
      explanation: "Ukrainian does NOT devoice final consonants! зуб always ends with a clear voiced б, never as п."
      options:
        - text: "True — they become voiceless"
          correct: false
        - text: "False — they stay voiced"
          correct: true
        - text: "Only sometimes"
          correct: false
        - text: "Only sonorants stay voiced"
          correct: false

- type: classify
  title: "Hard or Soft?"
  instruction: "Look at the underlined consonant in each word. Is it hard or soft? Remember: consonants become soft before І, Я, Ю, Є or the soft sign Ь."
  categories:
    - label: "Hard consonant"
      symbol_hint: "hard"
      items: ["Л in лук", "Д in дим", "Ж in жук", "Ш in шапка", "Н in небо", "Р in рука", "Г in гора"]
    - label: "Soft consonant"
      symbol_hint: "soft"
      items: ["Л in люк", "Л in ліс", "Д in дім", "Н in день", "Н in кінь", "Л in люди", "К in кінь", "К in кіт"]
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/consonant-sounds.yaml`

```yaml
items:
  - lemma: "хліб"
    translation: "bread"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Х; no-devoicing rule (voiced б at end, never п)"
    usage: "Це хліб."
  - lemma: "зуб"
    translation: "tooth"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates З; no-devoicing drill (voiced б at end, never п)"
    usage: "Це зуб."
  - lemma: "дім"
    translation: "house"
    pos: "noun"
    gender: "m"
    notes: "High-frequency; demonstrates soft Д before І"
    usage: "Це дім."
  - lemma: "вовк"
    translation: "wolf"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates В (sonorant); tale vocabulary"
    usage: "Це вовк."
  - lemma: "жук"
    translation: "beetle"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Ж (voiced sibilant)"
  - lemma: "шапка"
    translation: "hat"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ш (voiceless sibilant); everyday clothing"
  - lemma: "гора"
    translation: "mountain"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Г (throaty fricative, NOT hard G)"
  - lemma: "небо"
    translation: "sky"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates Н; high-frequency"
    usage: "Це небо."
  - lemma: "рука"
    translation: "hand"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Р (rolled/trilled); body vocabulary"
  - lemma: "бабуся"
    translation: "grandma"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Б; high-frequency family word"
    usage: "Ось бабуся."
  - lemma: "павук"
    translation: "spider"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates П (voiceless partner of Б)"
  - lemma: "ґанок"
    translation: "porch"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates rare Ґ (hard G); classic textbook word"
  - lemma: "кінь"
    translation: "horse"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates soft Н (before Ь) and soft К (before І)"
  - lemma: "люди"
    translation: "people"
    pos: "noun"
    notes: "Demonstrates soft Л (before Ю); high-frequency; plural of людина"
  - lemma: "суп"
    translation: "soup"
    pos: "noun"
    gender: "m"
    notes: "Voiceless pair drill with зуб; everyday food"
  - lemma: "вода"
    translation: "water"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates В (sonorant); high-frequency"
    usage: "Тут вода."
  - lemma: "дим"
    translation: "smoke"
    pos: "noun"
    gender: "m"
    notes: "Minimal pair with дім (hard Д vs soft Д)"
  - lemma: "люк"
    translation: "hatch"
    pos: "noun"
    gender: "m"
    notes: "Minimal pair with лук (soft Л vs hard Л)"
  - lemma: "риба"
    translation: "fish"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Р (rolled/trilled R)"
  - lemma: "кіт"
    translation: "cat"
    pos: "noun"
    gender: "m"
    notes: "M1 review; demonstrates К; soft К before І"
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

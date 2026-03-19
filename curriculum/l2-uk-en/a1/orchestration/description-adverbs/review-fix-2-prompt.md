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



**NOTE: 4 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 8 items
  - Fix: Add 17 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 8 items
  - Fix: Add 17 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥25 items
  - Actual: Activity has 6 items
  - Fix: Add 19 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 8 items
  - Fix: Add 12 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥20 items
  - Actual: Activity has 6 items
  - Fix: Add 14 more items to 'fill-in' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:quiz`
  - Expected: Plan requires ≥10 items
  - Actual: Activity has 8 items
  - Fix: Add 2 more items to 'quiz' activity

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:fill-in`
  - Expected: Plan requires ≥8 items
  - Actual: Activity has 6 items
  - Fix: Add 2 more items to 'fill-in' activity


---

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Entire module — only 1 `[!culture]` box at line 149, Section "Вступ (Introduction)", top of module, Whole module, `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/description-adverbs.yaml`

### Finding 1: Richness Gate — Missing Engagement Boxes (HIGH)
**Location**: Entire module — only 1 `[!culture]` box at line 149
**Problem**: Audit requires engagement: 2, current: 0/2 (the `[!culture]` box may not count as engagement type). This causes the richness gate to FAIL and the overall audit to FAIL.
**Required Fix**: Add a `[!did-you-know]` or `[!tip]` callout box. Best location: after the formation rule in section "Основи та Формування" (after line 60), and/or after the double negation drill in section "Час та Частота" (after line 101).
**Severity**: HIGH

### Finding 2: Missing Vocabulary Items (MEDIUM)
**Location**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/description-adverbs.yaml`
**Problem**: Four words are explicitly taught in the content and/or used in activities but absent from the vocabulary file:
**Required Fix**: Add all 4 to vocabulary file.
**Severity**: HIGH

### Finding 3: Immersion Below Target (MEDIUM)
**Location**: Whole module
**Problem**: Immersion at 18.5% vs target 20-35%. Module 42 falls in the "Modules 21+" band (target 30-55% per calibration). The prose is heavily English with Ukrainian appearing only in bolded examples. While English scaffolding is appropriate for grammar explanation, more Ukrainian reading practice blocks would help.
**Required Fix**: Add a short Ukrainian reading practice block (4-6 sentences) in section "Час та Частота" or "Синтаксис та Інтенсивність" to boost immersion. Example: a mini-dialogue or paragraph describing a daily routine using the taught adverbs.
**Severity**: HIGH

### Finding 4: No Learning Objectives Preview (LOW)
**Location**: Section "Вступ (Introduction)", top of module
**Problem**: The module jumps into content without a "Today you'll learn..." preview. Per Beginner Lesson Arc, a PREVIEW element is expected ("Today you'll learn to...") to set expectations.
**Required Fix**: Add 2-3 bullet points at the start: "In this module, you'll learn to: form adverbs from adjectives, use frequency adverbs, describe how actions happen."
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Richness Gate — Missing Engagement Boxes (HIGH)
- **Location**: Entire module — only 1 `[!culture]` box at line 149
- **Problem**: Audit requires engagement: 2, current: 0/2 (the `[!culture]` box may not count as engagement type). This causes the richness gate to FAIL and the overall audit to FAIL.
- **Fix**: Add a `[!did-you-know]` or `[!tip]` callout box. Best location: after the formation rule in section "Основи та Формування" (after line 60), and/or after the double negation drill in section "Час та Частота" (after line 101).

### Issue 2: Missing Vocabulary Items (MEDIUM)
- **Location**: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/description-adverbs.yaml`
- **Problem**: Four words are explicitly taught in the content and/or used in activities but absent from the vocabulary file:
  - **смачно** — used in content line 153 「Ця людина готує дуже смачно!」 and in activity "Food Critic" (line 173). Verified in VESUM: `adv:compb:predic`.
  - **трохи** — taught as intensity marker at line 117. Verified in VESUM: `adv`.
  - **майже** — taught as intensity marker at line 118. Verified in VESUM: `adv`.
  - **зовсім** — taught as intensity marker at line 119. Verified in VESUM: `adv`.
- **Fix**: Add all 4 to vocabulary file.

### Issue 3: Immersion Below Target (MEDIUM)
- **Location**: Whole module
- **Problem**: Immersion at 18.5% vs target 20-35%. Module 42 falls in the "Modules 21+" band (target 30-55% per calibration). The prose is heavily English with Ukrainian appearing only in bolded examples. While English scaffolding is appropriate for grammar explanation, more Ukrainian reading practice blocks would help.
- **Fix**: Add a short Ukrainian reading practice block (4-6 sentences) in section "Час та Частота" or "Синтаксис та Інтенсивність" to boost immersion. Example: a mini-dialogue or paragraph describing a daily routine using the taught adverbs.

### Issue 4: No Learning Objectives Preview (LOW)
- **Location**: Section "Вступ (Introduction)", top of module
- **Problem**: The module jumps into content without a "Today you'll learn..." preview. Per Beginner Lesson Arc, a PREVIEW element is expected ("Today you'll learn to...") to set expectations.
- **Fix**: Add 2-3 bullet points at the start: "In this module, you'll learn to: form adverbs from adjectives, use frequency adverbs, describe how actions happen."

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| — | No Ukrainian grammar errors found | — | — |

All Ukrainian sentences verified. Grammar is correct throughout. No Russianisms, no calques, no scope violations.

---

## Fix Plan to Reach 9.0/10 (REQUIRED — score is 8.4)

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Section "Вступ (Introduction)": Add learning objectives preview after the frontmatter (before line 26) — "In this module, you'll learn to..."
2. Section "Основи та Формування": Add a `[!tip]` callout after line 60 about the opposite-pairs memory trick (швидко↔повільно, голосно↔тихо)
3. Section "Час та Частота": Add a `[!did-you-know]` callout after line 101 about double negation being common across many languages (not just Ukrainian)

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Section "Синтаксис та Інтенсивність": After the 4 intensity markers list (line 119), add a mini-practice prompt before the dialogues — e.g., "Try combining дуже with adverbs you already know before reading on."
2. Section "Час та Частота" or "Синтаксис та Інтенсивність": Add a 4-6 sentence Ukrainian reading practice block (daily routine paragraph using taught adverbs) to boost immersion.

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Add смачно, трохи, майже, зовсім to vocabulary file
2. Consider adding 2-3 more items to the Food Critic fill-in (currently 6, plan says 8)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 8.0 + 13.5) / 8.9
= 79.1 / 8.9 = 8.9/10
```

With engagement boxes added (closing richness gap), audit gate should also pass.

---

## Audit Failures (from automated re-audit)

```
⚠️  Template violations: 1 critical, 0 warnings, 0 info
🔴 [MISSING_REQUIRED_SECTION] Missing required section 'Presentation' per template 'a1-module-template.md'
--- STRICT GATES (Level A1) ---
📋 TEMPLATE COMPLIANCE VIOLATIONS FOUND:
🔴 [MISSING_REQUIRED_SECTION] Missing required section 'Presentation' per template 'a1-module-template.md'
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 1 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• 1 Critical Template Violations
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/description-adverbs-audit.log for details)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: 1 Critical Template Violations
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `ий` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/description-adverbs.md`

```markdown
---
module: a1-042
level: A1
sequence: 42
slug: description-adverbs
version: "2.0"
title: "Description: Adverbs"
subtitle: How We Do Things
focus: grammar
pedagogy: PPP
phase: A1.4 [Tenses & Daily Life]
word_target: 1200
duration: 45
transliteration: false
tags: [adverbs, grammar, frequency]
grammar:
  - Adverbs of manner
  - Adverbs of frequency
objectives:
  - Learner can form adverbs from adjectives
  - Learner can use adverbs to describe how actions are done
  - Learner can use frequency adverbs correctly
  - Learner can distinguish adverbs from adjectives
---

## Вступ (Introduction)

**In this module, you will learn to:**
- Form adverbs from adjectives (the -ий → -о rule)
- Use frequency adverbs (завжди, часто, іноді, ніколи)
- Add intensity with words like дуже and трохи
- Describe how actions happen — like a food critic!

When we describe things or people around us, we typically ask the question **Який?** (Which? / What kind?). For example, if you see a new item, you might ask **який це стіл?** (what kind of table is this?). We naturally answer this question with an adjective, such as **великий стіл** (a big table) or **новий стіл** (a new table). 

But what happens when we want to describe an action instead of an object? How do we talk about the way someone does something? For this purpose, we use a completely different question: **Як?** (How?).

- **Як ти працюєш?** (How do you work?)
- **Як вона говорить?** (How does she speak?)
- **Як вони читають?** (How do they read?)

To answer the question **Як?**, we must use adverbs. Adverbs are the words that tell us exactly *how* an action happens. If someone speaks well, we say **вона говорить добре** (she speaks well). We cannot say ~~вона говорить гарна~~ because **гарна** is an adjective meant for describing nouns, not verbs.

A very common mistake English speakers make is using an adjective instead of an adverb. In English, you might say "He runs fast" where the word "fast" looks exactly like an adjective. Because of this English interference, a learner might try to say ~~Він говорить хороший~~ (He speaks good). But in Ukrainian, actions always require adverbs: **Він говорить добре** (He speaks well). 

Think of it as a clear visual contrast in your mind:
- **Який?** (Adjective) describes a noun (a person, place, or object). 
- **Як?** (Adverb) describes a verb (an action or state). 

By mastering adverbs, your Ukrainian will immediately sound much more natural and dynamic. Let's look at how we build these words and start using them right away!

## Основи та Формування (Basics and Formation)

Forming adverbs from adjectives in Ukrainian is wonderfully straightforward and logical. If you already know the adjective, you almost certainly know the adverb! 

Here is the basic derivation rule: you simply take the adjective stem (drop the **-ий**, **-а**, **-е**, **-і** endings) and add **-о**. That's it! 

Look at this visual mapping of ending changes. Notice how we create pairs of opposites:
- **швидкий** (quick) → **швидко** (quickly)
- **повільний** (slow) → **повільно** (slowly)
- **гарний** (beautiful/good) → **гарно** (beautifully/nicely)
- **поганий** (bad) → **погано** (badly)
- **тихий** (quiet) → **тихо** (quietly)
- **голосний** (loud) → **голосно** (loudly)
- **легкий** (easy) → **легко** (easily)
- **важкий** (difficult) → **важко** (with difficulty)

> [!tip] Memory Trick: Opposite Pairs
> Learn adverbs in opposite pairs — it doubles your vocabulary instantly! **швидко ↔ повільно** (quickly ↔ slowly), **голосно ↔ тихо** (loudly ↔ quietly), **добре ↔ погано** (well ↔ badly), **легко ↔ важко** (easily ↔ with difficulty).

There is one extremely important exception you must memorize immediately: the adjective **добрий** (good) becomes the adverb **добре** (well). The word **добре** is one of the Top 100 high-frequency words in the Ukrainian language. Beyond just meaning "well," it serves as a universal response for "OK," "agreed," or "good." You will hear it constantly in daily life.

> - **Ми йдемо в кафе?** (Are we going to the cafe?)
> - **Добре!** (OK! / Agreed!)
> - **Я працюю завтра.** (I work tomorrow.)
> - **Добре, я розумію.** (OK, I understand.)

What about standard word order in a sentence? In Ukrainian, the adverb typically follows the verb it describes. This keeps the action and its description tightly linked together.

- **Він працює добре.** (He works well.)
- **Я читаю швидко.** (I read quickly.)
- **Вони слухають тихо.** (They listen quietly.)

<!-- adapted from: Заболотний, Grade 7 -->

## Час та Частота (Time and Frequency)

Now that we know how to describe *how* we do things, let's talk about *how often* we do them. Adverbs of frequency are essential for describing our daily routines and habits. 

Here is the frequency scale, going all the way from 100% down to 0%:
- **завжди** (always) 
- **зазвичай** (usually) 
- **часто** (often) 
- **іноді** (sometimes) 
- **рідко** (rarely) 
- **ніколи** (never)

Let's see these frequency words in action with some common verbs:
- **Я завжди снідаю.** (I always eat breakfast.)
- **Він зазвичай читає тут.** (He usually reads here.)
- **Ми часто гуляємо в парку.** (We often walk in the park.)
- **Вона іноді спить тут.** (She sometimes sleeps here.)
- **Вони рідко відпочивають там.** (They rarely rest there.)

There is a critical learner error you must avoid when using **ніколи** (never). In English, you would say "I never work," using only one negative word in the sentence. Ukrainian, however, requires double negation. When you use the word **ніколи**, you MUST also use the negative particle **не** right before the verb. 

Drill this pattern into your memory: **Я ніколи не** (+ verb).
- **Я ніколи не працюю.** (I never work.)
- **Він ніколи не п'є каву.** (He never drinks coffee.)
- **Ми ніколи не їмо м'ясо.** (We never eat meat.)

> [!did-you-know] Double Negation Is Normal!
> Many learners worry that double negation sounds "wrong" because English avoids it. But in Ukrainian, double negation is the ONLY correct way to use **ніколи**. In fact, many European languages work this way — French (*ne ... jamais*), Spanish (*nunca ... no*). You are learning a very natural grammatical pattern!

We also use simple spatial and temporal markers to set the scene for our actions. These are very common adverbs:
- **тут** (here)
- **там** (there)
- **сьогодні** (today)
- **завтра** (tomorrow)

You can mix these beautifully to create rich, descriptive sentences: **Сьогодні я працюю тут, а завтра я відпочиваю там** (Today I work here, and tomorrow I rest there).

### 📖 Читання (Reading Practice)

Read this short paragraph about Оксана's daily routine. Try to understand it without translating word by word!

> **Оксана завжди снідає швидко. Вона часто працює добре, але іноді працює повільно. Оксана зазвичай читає тихо, а її брат завжди читає голосно. Вона рідко відпочиває тут. Сьогодні Оксана працює добре, а завтра вона відпочиває там.**

How much did you understand? Here is a quick comprehension check:
- How does Оксана eat breakfast? → **швидко** (quickly)
- How often does she rest here? → **рідко** (rarely)
- How does her brother read? → **голосно** (loudly)

## Синтаксис та Інтенсивність (Syntax and Intensity)

Sometimes, simply doing something "well" or "quickly" isn't quite enough to express what you mean. We often want to add intensity to our descriptions. We do this by using intensity markers before our adverbs. 

Here are the most common intensity markers you will need:
- **дуже** (very)
- **трохи** (a bit / a little)
- **майже** (almost)
- **зовсім** (completely / at all)

A common learner error is the wrong placement of the word **дуже**. Because English allows flexible placement in some contexts (like "I like it very much"), a learner might try to say ~~Це добре дуже~~. This is completely incorrect in Ukrainian. 

Instruction: The word **дуже** MUST precede the modified adverb or adjective. It acts like a magnifying glass pointing directly at the word that immediately follows it.

Let's see their usage in combination with other adverbs:
- **дуже добре** (very well)
- **дуже швидко** (very quickly)
- **дуже важко** (very difficult)
- **майже завжди** (almost always)
- **майже ніколи не** (almost never)
- **трохи повільно** (a bit slowly)

Let's look at some short dialogues to see how this works in conversation:
> - **Як вона працює?** (How does she work?)
> - **Вона працює дуже швидко.** (She works very quickly.)

> - **Ви часто гуляєте тут?** (Do you often walk here?)
> - **Ми гуляємо тут майже завжди.** (We walk here almost always.)

Notice how the intensity marker **дуже** sits right in front of **швидко**. This makes your Ukrainian sound natural, expressive, and accurate. 

## Підсумок та Культура (Summary and Culture)

You now have a rich and powerful toolkit for describing your personal habits, daily routines, and actions. Try describing your morning routine using these new words:
- **Я зазвичай снідаю дуже швидко.** (I usually eat breakfast very quickly.)
- **Я ніколи не п'ю каву повільно.** (I never drink coffee slowly.)
- **Сьогодні я працюю дуже добре.** (Today I am working very well.)

> [!culture] Did You Know?
> In Ukrainian culture, there is a famous and wise proverb that highlights the value of caution over rushing: **«Повільно їдеш — далі будеш»**. This literally translates to "You drive slowly — you will be further." It is the Ukrainian equivalent of the English proverb "Slow and steady wins the race" or "Haste makes waste." It reminds us that doing things **швидко** (quickly) isn't always **добре** (well)! Quality takes time.

To practice your new skills, imagine you are a Food Critic reviewing a new restaurant. Describe how someone cooks, eats, or serves food:
- **Ця людина готує дуже смачно!** (This person cooks very deliciously!)
- **Він працює швидко і добре.** (He works quickly and well.)
- **Офіціант розуміє нас погано, але він говорить дуже тихо.** (The waiter understands us badly, but he speaks very quietly.)
- **Я іноді їм тут.** (I sometimes eat here.)

Keep practicing these adverbs every day. **Ви працюєте дуже добре!** (You are working very well!)
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/description-adverbs.yaml`

```yaml
- type: fill-in
  title: Form Adverbs from Adjectives
  instruction: 'Each sentence shows an adjective. Choose the correct adverb form (ending in -о or -е).'
  items:
    - sentence: "швидкий → ___"
      answer: "швидко"
      options: ["швидко", "швидка", "швидку", "швидкий"]
      explanation: "Drop -ий from швидкий and add -о to get швидко (quickly)."
    - sentence: "повільний → ___"
      answer: "повільно"
      options: ["повільно", "повільна", "повільну", "повільний"]
      explanation: "Drop -ий from повільний and add -о to get повільно (slowly)."
    - sentence: "гарний → ___"
      answer: "гарно"
      options: ["гарно", "гарна", "гарну", "гарний"]
      explanation: "Drop -ий from гарний and add -о to get гарно (beautifully/nicely)."
    - sentence: "поганий → ___"
      answer: "погано"
      options: ["погано", "погана", "погану", "поганий"]
      explanation: "Drop -ий from поганий and add -о to get погано (badly)."
    - sentence: "тихий → ___"
      answer: "тихо"
      options: ["тихо", "тиха", "тиху", "тихий"]
      explanation: "Drop -ий from тихий and add -о to get тихо (quietly)."
    - sentence: "голосний → ___"
      answer: "голосно"
      options: ["голосно", "голосна", "голосну", "голосний"]
      explanation: "Drop -ий from голосний and add -о to get голосно (loudly)."
    - sentence: "легкий → ___"
      answer: "легко"
      options: ["легко", "легка", "легку", "легкий"]
      explanation: "Drop -ий from легкий and add -о to get легко (easily)."
    - sentence: "важкий → ___"
      answer: "важко"
      options: ["важко", "важка", "важку", "важкий"]
      explanation: "Drop -ий from важкий and add -о to get важко (with difficulty)."
    - sentence: "добрий → ___"
      answer: "добре"
      options: ["добре", "добро", "добра", "добрий"]
      explanation: "Добрий is an exception — the adverb is добре, not добро."
    - sentence: "смачний → ___"
      answer: "смачно"
      options: ["смачно", "смачна", "смачну", "смачний"]
      explanation: "Drop -ий from смачний and add -о to get смачно (deliciously)."
    - sentence: "Він працює ___. (добрий)"
      answer: "добре"
      options: ["добре", "добро", "добрий", "добра"]
      explanation: "Actions require adverbs. Добрий → добре (exception to the -о rule)."
    - sentence: "Вона читає ___. (швидкий)"
      answer: "швидко"
      options: ["швидко", "швидка", "швидкий", "швидку"]
      explanation: "The adjective швидкий becomes the adverb швидко to describe how she reads."
    - sentence: "Вони слухають ___. (тихий)"
      answer: "тихо"
      options: ["тихо", "тиха", "тихий", "тиху"]
      explanation: "The adjective тихий becomes the adverb тихо to describe how they listen."
    - sentence: "Він говорить ___. (голосний)"
      answer: "голосно"
      options: ["голосно", "голосна", "голосний", "голосну"]
      explanation: "The adjective голосний becomes the adverb голосно to describe how he speaks."

- type: fill-in
  title: Choose the Right Adverb
  instruction: Pick the adverb that best completes each sentence.
  items:
    - sentence: "Він працює ___."
      answer: "добре"
      options: ["добре", "погано", "швидко", "тихо"]
      explanation: "Він працює добре means He works well."
    - sentence: "Я читаю ___."
      answer: "швидко"
      options: ["швидко", "повільно", "голосно", "важко"]
      explanation: "Я читаю швидко means I read quickly."
    - sentence: "Вони слухають ___."
      answer: "тихо"
      options: ["тихо", "голосно", "швидко", "добре"]
      explanation: "Вони слухають тихо means They listen quietly."
    - sentence: "Вона говорить ___."
      answer: "голосно"
      options: ["голосно", "тихо", "легко", "погано"]
      explanation: "Вона говорить голосно means She speaks loudly."
    - sentence: "Я ___ снідаю."
      answer: "завжди"
      options: ["завжди", "ніколи", "іноді", "рідко"]
      explanation: "Я завжди снідаю means I always eat breakfast."
    - sentence: "Він ___ читає тут."
      answer: "зазвичай"
      options: ["зазвичай", "ніколи", "рідко", "завжди"]
      explanation: "Він зазвичай читає тут means He usually reads here."
    - sentence: "Ми ___ гуляємо в парку."
      answer: "часто"
      options: ["часто", "ніколи", "рідко", "завжди"]
      explanation: "Ми часто гуляємо в парку means We often walk in the park."
    - sentence: "Вона ___ спить тут."
      answer: "іноді"
      options: ["іноді", "завжди", "часто", "ніколи"]
      explanation: "Вона іноді спить тут means She sometimes sleeps here."
    - sentence: "Вони ___ відпочивають там."
      answer: "рідко"
      options: ["рідко", "завжди", "часто", "дуже"]
      explanation: "Вони рідко відпочивають там means They rarely rest there."
    - sentence: "Він працює дуже ___."
      answer: "добре"
      options: ["добре", "завжди", "іноді", "ніколи"]
      explanation: "Він працює дуже добре means He works very well. Дуже modifies the adverb добре."
    - sentence: "Я ___ не їм м'ясо."
      answer: "ніколи"
      options: ["ніколи", "завжди", "часто", "дуже"]
      explanation: "Я ніколи не їм м'ясо means I never eat meat. Remember: ніколи requires не before the verb."
    - sentence: "Вона говорить дуже ___."
      answer: "тихо"
      options: ["тихо", "завжди", "іноді", "рідко"]
      explanation: "Вона говорить дуже тихо means She speaks very quietly."
    - sentence: "Ми ___ гуляємо тут."
      answer: "майже завжди"
      options: ["майже завжди", "ніколи не", "дуже добре", "трохи погано"]
      explanation: "Ми майже завжди гуляємо тут means We almost always walk here."
    - sentence: "Сьогодні він читає ___."
      answer: "повільно"
      options: ["повільно", "завжди", "ніколи", "іноді"]
      explanation: "Сьогодні він читає повільно means Today he reads slowly."

- type: quiz
  title: Frequency Adverbs
  instruction: Choose the correct answer about how frequency adverbs work in Ukrainian.
  items:
    - question: "Which adverb means 'always' in Ukrainian?"
      options:
        - text: "завжди"
          correct: true
        - text: "ніколи"
          correct: false
        - text: "іноді"
          correct: false
        - text: "рідко"
          correct: false
      explanation: "Завжди means always — it is at the top of the frequency scale (100%)."
    - question: "Which adverb is the opposite of завжди (always)?"
      options:
        - text: "ніколи"
          correct: true
        - text: "часто"
          correct: false
        - text: "зазвичай"
          correct: false
        - text: "іноді"
          correct: false
      explanation: "Ніколи (never) is the opposite of завжди (always) — 0% vs 100%."
    - question: "How do you correctly say 'I never work' in Ukrainian?"
      options:
        - text: "Я ніколи не працюю"
          correct: true
        - text: "Я ніколи працюю"
          correct: false
        - text: "Я не працюю ніколи"
          correct: false
        - text: "Ніколи я працюю"
          correct: false
      explanation: "Ukrainian requires double negation with ніколи. The pattern is: Я ніколи НЕ + verb."
    - question: "Put these in order from most frequent to least frequent: часто, завжди, іноді"
      options:
        - text: "завжди → часто → іноді"
          correct: true
        - text: "часто → завжди → іноді"
          correct: false
        - text: "іноді → часто → завжди"
          correct: false
        - text: "завжди → іноді → часто"
          correct: false
      explanation: "Завжди (always, 100%) → часто (often) → іноді (sometimes)."
    - question: "Where does the word дуже go in a Ukrainian sentence?"
      options:
        - text: "Before the adverb or adjective it modifies"
          correct: true
        - text: "After the adverb or adjective it modifies"
          correct: false
        - text: "At the end of the sentence"
          correct: false
        - text: "At the beginning of the sentence"
          correct: false
      explanation: "Дуже always precedes the word it modifies: дуже добре (very well), дуже швидко (very quickly)."
    - question: "What is the adverb form of the adjective добрий (good)?"
      options:
        - text: "добре"
          correct: true
        - text: "добро"
          correct: false
        - text: "добра"
          correct: false
        - text: "добру"
          correct: false
      explanation: "Добрий is an exception — the adverb is добре (not добро). It means well and also serves as OK/agreed."
    - question: "Which question word do you use to ask about HOW an action is done?"
      options:
        - text: "Як?"
          correct: true
        - text: "Який?"
          correct: false
        - text: "Що?"
          correct: false
        - text: "Де?"
          correct: false
      explanation: "Як? (How?) asks about the manner of an action. Який? (Which/What kind?) asks about a noun."
    - question: "Which word means 'almost' in Ukrainian?"
      options:
        - text: "майже"
          correct: true
        - text: "трохи"
          correct: false
        - text: "зовсім"
          correct: false
        - text: "дуже"
          correct: false
      explanation: "Майже means almost. Трохи = a bit, зовсім = completely, дуже = very."
    - question: "What does Ukrainian double negation with ніколи require?"
      options:
        - text: "Adding не before the verb"
          correct: true
        - text: "Adding не after the verb"
          correct: false
        - text: "Nothing — ніколи alone is enough"
          correct: false
        - text: "Using два before the verb"
          correct: false
      explanation: "Ukrainian requires ніколи НЕ + verb. The не must come directly before the verb."
    - question: "Which word means 'rarely' in Ukrainian?"
      options:
        - text: "рідко"
          correct: true
        - text: "часто"
          correct: false
        - text: "завжди"
          correct: false
        - text: "іноді"
          correct: false
      explanation: "Рідко means rarely — near the bottom of the frequency scale, just above ніколи (never)."

- type: fill-in
  title: 'Food Critic: Describe How Things Are Done'
  instruction: 'You are a food critic reviewing a restaurant. Complete each sentence with the best adverb.'
  items:
    - sentence: "Ця людина готує дуже ___!"
      answer: "смачно"
      options: ["смачно", "погано", "тихо", "важко"]
      explanation: "Готує дуже смачно means cooks very deliciously — a great food critic compliment!"
    - sentence: "Він працює ___ і добре."
      answer: "швидко"
      options: ["швидко", "повільно", "погано", "тихо"]
      explanation: "Працює швидко і добре means works quickly and well."
    - sentence: "Офіціант говорить дуже ___."
      answer: "тихо"
      options: ["тихо", "голосно", "швидко", "добре"]
      explanation: "Говорить дуже тихо means speaks very quietly."
    - sentence: "Я ___ їм тут."
      answer: "іноді"
      options: ["іноді", "ніколи", "завжди", "дуже"]
      explanation: "Я іноді їм тут means I sometimes eat here."
    - sentence: "Офіціант розуміє нас ___."
      answer: "погано"
      options: ["погано", "добре", "швидко", "голосно"]
      explanation: "Розуміє нас погано means understands us badly."
    - sentence: "Вони готують дуже ___."
      answer: "добре"
      options: ["добре", "погано", "тихо", "важко"]
      explanation: "Готують дуже добре means they cook very well."
    - sentence: "Вона ___ їсть тут."
      answer: "завжди"
      options: ["завжди", "дуже", "добре", "швидко"]
      explanation: "Вона завжди їсть тут means She always eats here."
    - sentence: "Він готує трохи ___."
      answer: "повільно"
      options: ["повільно", "голосно", "добре", "завжди"]
      explanation: "Готує трохи повільно means cooks a bit slowly — the intensity marker трохи softens the adverb."

- type: match-up
  title: Adjective to Adverb
  instruction: Match each adjective with its adverb form.
  pairs:
    - left: "швидкий"
      right: "швидко"
    - left: "повільний"
      right: "повільно"
    - left: "гарний"
      right: "гарно"
    - left: "поганий"
      right: "погано"
    - left: "тихий"
      right: "тихо"
    - left: "голосний"
      right: "голосно"
    - left: "легкий"
      right: "легко"
    - left: "добрий"
      right: "добре"

- type: group-sort
  title: Sort the Words
  instruction: Sort these words into the correct category.
  groups:
    - name: "Adverbs (answer Як?)"
      items: ["добре", "швидко", "повільно", "тихо", "голосно"]
    - name: "Adjectives (answer Який?)"
      items: ["добрий", "швидкий", "повільний", "тихий", "голосний"]

- type: true-false
  title: True or False?
  instruction: Decide whether each statement about Ukrainian adverbs is correct.
  items:
    - statement: "To form an adverb from an adjective, you replace -ий with -о."
      correct: true
      explanation: "That is the basic rule. швидкий → швидко, тихий → тихо."
    - statement: "The adverb form of добрий is добро."
      correct: false
      explanation: "Добрий is an exception — the adverb is добре, not добро."
    - statement: "In Ukrainian, you can say Я ніколи працюю without the word не."
      correct: false
      explanation: "Ukrainian requires double negation. The correct form is Я ніколи НЕ працюю."
    - statement: "The word дуже must come before the adverb it modifies."
      correct: true
      explanation: "Дуже always precedes its target word: дуже добре (very well), never добре дуже."
    - statement: "Завжди means sometimes in Ukrainian."
      correct: false
      explanation: "Завжди means always. Sometimes is іноді."
    - statement: "Adverbs in Ukrainian typically follow the verb they describe."
      correct: true
      explanation: "Standard word order places the adverb after the verb: Він працює добре."

- type: unjumble
  title: Put the Words in Order
  instruction: Arrange the words to form a correct Ukrainian sentence.
  items:
    - words: ["добре", "Він", "працює"]
      answer: "Він працює добре"
    - words: ["швидко", "читаю", "Я"]
      answer: "Я читаю швидко"
    - words: ["снідаю", "завжди", "Я"]
      answer: "Я завжди снідаю"
    - words: ["не", "ніколи", "працюю", "Я"]
      answer: "Я ніколи не працюю"
    - words: ["дуже", "працює", "Вона", "швидко"]
      answer: "Вона працює дуже швидко"
    - words: ["часто", "парку", "в", "гуляємо", "Ми"]
      answer: "Ми часто гуляємо в парку"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/description-adverbs.yaml`

```yaml
items:
  - lemma: "добре"
    translation: "well; OK, agreed"
    pos: "adverb"
    notes: "Top 100 high-frequency word. Exception from добрий (not добро). Also used as a universal response meaning OK/agreed."
    usage: "Він працює добре."
  - lemma: "швидко"
    translation: "quickly"
    pos: "adverb"
    notes: "From швидкий. Regular -ий → -о formation."
    usage: "Я читаю швидко."
  - lemma: "часто"
    translation: "often"
    pos: "adverb"
    usage: "Ми часто гуляємо в парку."
  - lemma: "ніколи"
    translation: "never"
    pos: "adverb"
    notes: "Requires double negation: ніколи НЕ + verb."
    usage: "Я ніколи не працюю."
  - lemma: "зазвичай"
    translation: "usually"
    pos: "adverb"
    usage: "Він зазвичай читає тут."
  - lemma: "завжди"
    translation: "always"
    pos: "adverb"
    usage: "Я завжди снідаю."
  - lemma: "погано"
    translation: "badly"
    pos: "adverb"
    notes: "From поганий. Regular -ий → -о formation."
    usage: "Він розуміє погано."
  - lemma: "повільно"
    translation: "slowly"
    pos: "adverb"
    notes: "From повільний. Cultural link to proverb: Повільно їдеш — далі будеш."
    usage: "Я ніколи не п'ю каву повільно."
  - lemma: "дуже"
    translation: "very"
    pos: "adverb"
    notes: "Must always precede the word it modifies. Never at the end."
    usage: "Вона працює дуже швидко."
  - lemma: "іноді"
    translation: "sometimes"
    pos: "adverb"
    usage: "Вона іноді спить тут."
  - lemma: "рідко"
    translation: "rarely"
    pos: "adverb"
    usage: "Вони рідко відпочивають там."
  - lemma: "голосно"
    translation: "loudly"
    pos: "adverb"
    notes: "From голосний. Regular -ий → -о formation."
    usage: "Вона говорить голосно."
  - lemma: "тихо"
    translation: "quietly"
    pos: "adverb"
    notes: "From тихий. Regular -ий → -о formation."
    usage: "Вони слухають тихо."
  - lemma: "тут"
    translation: "here"
    pos: "adverb"
    notes: "State Standard Catalog A spatial marker."
    usage: "Він зазвичай читає тут."
  - lemma: "там"
    translation: "there"
    pos: "adverb"
    notes: "State Standard Catalog A spatial marker."
    usage: "Вони рідко відпочивають там."
  - lemma: "сьогодні"
    translation: "today"
    pos: "adverb"
    notes: "State Standard Catalog A time marker."
    usage: "Сьогодні я працюю тут."
  - lemma: "завтра"
    translation: "tomorrow"
    pos: "adverb"
    notes: "State Standard Catalog A time marker."
    usage: "Завтра я відпочиваю там."
  - lemma: "легко"
    translation: "easily"
    pos: "adverb"
    notes: "From легкий. Regular -ий → -о formation."
    usage: "Це легко зробити."
  - lemma: "важко"
    translation: "with difficulty; hard"
    pos: "adverb"
    notes: "From важкий. Regular -ий → -о formation."
    usage: "Це дуже важко."
  - lemma: "гарно"
    translation: "beautifully, nicely"
    pos: "adverb"
    notes: "From гарний. Regular -ий → -о formation."
    usage: "Вона говорить дуже гарно."
  - lemma: "смачно"
    translation: "deliciously, tastily"
    pos: "adverb"
    notes: "From смачний. Regular -ий → -о formation. Common in food/restaurant contexts."
    usage: "Ця людина готує дуже смачно!"
  - lemma: "трохи"
    translation: "a bit, a little"
    pos: "adverb"
    notes: "Intensity marker. Softens the adverb that follows: трохи повільно (a bit slowly)."
    usage: "Він читає трохи повільно."
  - lemma: "майже"
    translation: "almost"
    pos: "adverb"
    notes: "Intensity marker. Placed before adverbs: майже завжди (almost always), майже ніколи не (almost never)."
    usage: "Ми гуляємо тут майже завжди."
  - lemma: "зовсім"
    translation: "completely, at all"
    pos: "adverb"
    notes: "Intensity marker. With negation means 'not at all': зовсім не розумію."
    usage: "Він зовсім не розуміє."
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/description-adverbs.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/description-adverbs.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/description-adverbs.yaml`

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

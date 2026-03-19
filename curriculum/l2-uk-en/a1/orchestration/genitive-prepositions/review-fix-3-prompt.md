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



**NOTE: 5 inline fix(es) from the review have ALREADY been applied to the files. Do NOT re-apply those fixes. Read the CURRENT file contents carefully — they reflect the post-fix state. Only fix issues that are still present in the current files.**

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Activities file, lines 111, 113, Entire module (all sections), Entire module — only 1 `[!tip]` box (lines 138-139), Section "Warm-up", line 115

### Finding 1: Non-existent word forms in quiz distractors (Activity VESUM)
**Location**: Activities file, lines 111, 113
**Problem**: `ногі` and `ноці` are not real Ukrainian word forms (VESUM-verified: NOT FOUND). While these are deliberate wrong answers in a quiz about consonant alternation, presenting non-existent forms to A1 beginners without marking them as incorrect can cause confusion. The audit scanner correctly flags these.
**Required Fix**: Add explicit "(incorrect)" or "✗" markers to the distractor text, e.g., "г stays the same (✗на ногі)" — or rewrite the options to describe the alternation without showing the full incorrect form.
**Severity**: HIGH

### Finding 2: Immersion below target for module position
**Location**: Entire module (all sections)
**Problem**: Module 32 should have 30-55% Ukrainian immersion per A1 calibration, but measured immersion is 13.3%. The module is overwhelmingly English prose with only bolded Ukrainian vocabulary and a few example sentences. The practice section "Практика (Practice)" has good Ukrainian passages (lines 261, 265-270), but the Presentation sections are almost entirely English.
**Required Fix**: Add Ukrainian Reading Practice blocks after each subsection. For example, after section "В/У + Місцевий", add a 3-5 sentence Ukrainian paragraph with English gloss. After section "На + Місцевий", add a similar block. This would raise immersion to ~25-30%.
**Severity**: HIGH

### Finding 3: Insufficient engagement elements
**Location**: Entire module — only 1 `[!tip]` box (lines 138-139)
**Problem**: Richness audit requires engagement: 2, video_embeds: 2. Module has engagement: 1, video_embeds: 0. The single tip box about в/у meaning the same thing is good but insufficient.
**Required Fix**: Add at least 1 more engagement box (e.g., a `[!did-you-know]` about why Kyiv landmarks are important for directions, or a `[!culture-note]` about Ukrainian street naming conventions). Add pronunciation video embeds for key phrases if available.
**Severity**: HIGH

### Finding 4: Missing learning objectives preview in section "Warm-up"
**Location**: Section "Warm-up", line 115
**Problem**: The warm-up provides context but doesn't explicitly state "Today you'll learn: (1) в/у + Locative, (2) на + Locative, (3) біля/навпроти + Genitive, (4) how to ask directions." Beginner calibration requires a PREVIEW element with clear "Today you'll learn..." expectations.
**Required Fix**: Add explicit learning objectives after the opening paragraph: "By the end of this module, you will be able to: say where things are using в/у and на, describe relative positions with біля and навпроти, and ask and give directions using Де знаходиться...?"
**Severity**: HIGH

---

## Critical Issues Found

### Issue 1: Non-existent word forms in quiz distractors (Activity VESUM)
- **Location**: Activities file, lines 111, 113
- **Original**: 「г stays the same (на ногі)」 and 「г changes to к (на ноці)」
- **Problem**: `ногі` and `ноці` are not real Ukrainian word forms (VESUM-verified: NOT FOUND). While these are deliberate wrong answers in a quiz about consonant alternation, presenting non-existent forms to A1 beginners without marking them as incorrect can cause confusion. The audit scanner correctly flags these.
- **Fix**: Add explicit "(incorrect)" or "✗" markers to the distractor text, e.g., "г stays the same (✗на ногі)" — or rewrite the options to describe the alternation without showing the full incorrect form.

### Issue 2: Immersion below target for module position
- **Location**: Entire module (all sections)
- **Problem**: Module 32 should have 30-55% Ukrainian immersion per A1 calibration, but measured immersion is 13.3%. The module is overwhelmingly English prose with only bolded Ukrainian vocabulary and a few example sentences. The practice section "Практика (Practice)" has good Ukrainian passages (lines 261, 265-270), but the Presentation sections are almost entirely English.
- **Fix**: Add Ukrainian Reading Practice blocks after each subsection. For example, after section "В/У + Місцевий", add a 3-5 sentence Ukrainian paragraph with English gloss. After section "На + Місцевий", add a similar block. This would raise immersion to ~25-30%.

### Issue 3: Insufficient engagement elements
- **Location**: Entire module — only 1 `[!tip]` box (lines 138-139)
- **Problem**: Richness audit requires engagement: 2, video_embeds: 2. Module has engagement: 1, video_embeds: 0. The single tip box about в/у meaning the same thing is good but insufficient.
- **Fix**: Add at least 1 more engagement box (e.g., a `[!did-you-know]` about why Kyiv landmarks are important for directions, or a `[!culture-note]` about Ukrainian street naming conventions). Add pronunciation video embeds for key phrases if available.

### Issue 4: Missing learning objectives preview in section "Warm-up"
- **Location**: Section "Warm-up", line 115
- **Original**: 「Welcome back! So far, you have learned how to talk about the absence of things using the Genitive case. Now it is time to step out into the world and learn how to navigate a Ukrainian city.」
- **Problem**: The warm-up provides context but doesn't explicitly state "Today you'll learn: (1) в/у + Locative, (2) на + Locative, (3) біля/навпроти + Genitive, (4) how to ask directions." Beginner calibration requires a PREVIEW element with clear "Today you'll learn..." expectations.
- **Fix**: Add explicit learning objectives after the opening paragraph: "By the end of this module, you will be able to: say where things are using в/у and на, describe relative positions with біля and навпроти, and ask and give directions using Де знаходиться...?"

---

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Activity 111 | 「на ногі」 | на нозі (correct form, but here used as deliberate wrong answer) | Non-existent form |
| Activity 113 | 「на ноці」 | на нозі (correct form, but here used as deliberate wrong answer) | Non-existent form |

---

## Fix Plan to Reach 9/10 (REQUIRED since score < 9.0)

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Section "Warm-up", line 115: Add explicit "Today you'll learn..." objectives after opening paragraph — sets expectations, provides preview element
2. Section "Підсумок", line 275: Add a "You can now..." validation list instead of burying it in prose

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 181: Change "Ukrainians always say **на кухні** (on the kitchen)" → "Ukrainians always say **на кухні** (in the kitchen)" — English translation should match what English speakers actually say

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Add Ukrainian Reading Practice blocks (3-5 sentences each with English gloss) after sections "В/У + Місцевий (In + Locative)" and "На + Місцевий (On + Locative)" to raise immersion from 13.3% toward 25-30%
2. Add at least 1 `[!did-you-know]` or `[!culture-note]` engagement callout

**Expected score after fix:** 9/10

### Activities: 7/10 → 9/10
**What to fix:**
1. Activity lines 111, 113: Either mark non-existent forms with ✗ prefix, or restructure the quiz question to avoid showing full non-existent locative forms (e.g., describe the alternation rule rather than showing the wrong output form)

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
⚠️  Outline compliance: 4 errors, 2 warnings
❌ [MISSING_OUTLINE_SECTION] Section 'В/У + Місцевий (In + Locative)' defined in outline but not found in markdown.
❌ [MISSING_OUTLINE_SECTION] Section 'На + Місцевий (On + Locative)' defined in outline but not found in markdown.
❌ [MISSING_OUTLINE_SECTION] Section 'Біля/Поруч/Між (Near/Next to/Between)' defined in outline but not found in markdown.
🎭 Content gaming violations found: 1
❌ [SECTION_BALANCE_BLOATED] Section 'Presentation' has 2035 words (80% of total). Bloated sections: 'Presentation' (80%)
--- STRICT GATES (Level A1) ---
Pedagogy     ❌ 2 violations
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
→ 2 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
• 4 Outline Compliance Errors
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/genitive-prepositions-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: 4 Outline Compliance Errors
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `зв` (source: prose)
  ❌ `льв` (source: prose)
  ❌ `Львові` (source: prose)
  ❌ `св` (source: prose)
  ❌ `Хрещатик` (source: prose)
  ❌ `Шевченка` (source: prose)
```

---

## File Contents (for reference)

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/genitive-prepositions.md`

```markdown
---
module: a1-032
level: A1
sequence: 32
slug: genitive-prepositions
version: '2.0'
title: Genitive Prepositions
subtitle: "біля, без, від, для, до + родовий відмінок"
focus: grammar
pedagogy: PPP
phase: A1.3 [Cases & Navigation]
word_target: 1200
objectives:
- Use в/у + Locative for indoor locations
- Use на + Locative for surfaces and events
- Apply біля/навпроти + Genitive for relative position
- Ask and answer 'Where is...?' questions
content_outline:
- section: В/У + Місцевий (In + Locative)
  words: 300
  points:
  - 'Location inside enclosed spaces: в магазині, у школі, в Україні. High-frequency collocations with в/у + Locative for
    buildings, cities, and countries.'
  - 'Euphonic в/у rule per Pravopys §23: у between consonants and before в/ф/льв/зв/св clusters; в between vowels and at sentence
    start before vowels. Drill common learner errors: «У Львові» (not «В Львові» — у before льв-cluster).'
  - 'Consonant alternations in Locative: г→з (нога → на нозі), к→ц (рука → у руці), х→с (вухо → у вусі). Review from a1-13
    with expanded drills.'
- section: На + Місцевий (On + Locative)
  words: 300
  points:
  - 'Location on surfaces: на столі, на стіні, на підлозі. Physical contact meaning of на.'
  - 'Location at events and institutions: на концерті, на роботі, на пошті, на уроці. The social/activity exception where
    на replaces в/у.'
  - 'Contrast pairs: в кімнаті (inside a room) vs на кухні (in the kitchen — traditional usage). в театрі (inside the building)
    vs на виставі (at the performance).'
- section: Біля/Поруч/Між (Near/Next to/Between)
  words: 250
  points:
  - 'Біля + Genitive for proximity: біля школи, біля парку, біля зупинки. High-frequency pattern for giving directions.'
  - 'Навпроти + Genitive for opposite position: навпроти банку, навпроти аптеки. Useful for city orientation tasks.'
  - 'Preview of Instrumental prepositions: поруч з + Instrumental (next to), між + Instrumental (between). Introduced as formulaic
    chunks, not full case explanation.'
- section: Де знаходиться...? (Where is...?)
  words: 200
  points:
  - 'Asking location questions: Де знаходиться пошта? Де знаходиться найближча аптека? The verb знаходитися (to be located)
    as a formal alternative to бути.'
  - 'Answering with full sentences: Пошта знаходиться на вулиці Хрещатик. Аптека знаходиться біля метро. Combining prepositions
    with correct case forms.'
  - 'Cultural context: Using Kyiv landmarks as location reference points — Хрещатик, Майдан та Золоті Ворота.'
- section: Практика (Practice)
  words: 150
  points:
  - 'Location description drills: Describe where objects are in a room, where buildings are in a city. Multiple prepositions
    in connected speech.'
  - 'Dialogues: asking and answering "Where is...?" in realistic scenarios — tourist asking for directions, describing your
    neighbourhood.'
vocabulary_hints:
  required:
  - магазин (store) — в магазині; high frequency location noun
  - школа (school) — у школі; euphonic у before ш-cluster
  - вулиця (street) — на вулиці; surface preposition на
  - стіл (table) — на столі; basic surface location
  - кухня (kitchen) — на кухні; traditional на exception
  - пошта (post office) — на пошті; institutional на usage
  - біля (near) — біля + Gen; proximity preposition
  - навпроти (opposite) — навпроти + Gen; orientation preposition
  - знаходиться (is located) — formal location verb; Де знаходиться...?
  recommended:
  - поруч (nearby) — поруч з + Inst; preview chunk
  - між (between) — між + Inst; preview chunk
  - далеко (far) — далеко від + Gen; distance expression
  - близько (near/close) — близько від + Gen; distance expression
activity_hints:
- type: fill-in
  focus: Choose correct preposition (в/у/на) and Locative form
  items: 10
- type: quiz
  focus: Select appropriate preposition for given location
  items: 10
- type: match-up
  focus: Match place to correct preposition phrase
  items: 10
- type: true-false
  focus: Evaluate location statements for correctness
  items: 8
connects_to:
- a1-33 (Adjective Case Forms)
prerequisites:
- a1-31 (The Genitive I: Absence)
persona:
  voice: Patient Supportive Tutor
  role: City Cartographer
grammar:
- Locative prepositions (в/у, на)
- Euphonic в/у alternation
- Біля/навпроти + Genitive
register: розмовний
duration: "45 min"
transliteration: no
tags:
- grammar
- cases
- locative
- genitive
- prepositions
naturalness:
  status: PASS
  score: 10/10
  notes: Good text.
---

## Warm-up

Welcome back! So far, you have learned how to talk about the absence of things using the Genitive case. Now it is time to step out into the world and learn how to navigate a Ukrainian city. When you want to talk about where something is located, you will often use prepositions. In this module, you will master the most important location prepositions in Ukrainian and learn how to ask and give directions like a local.

**Today you will learn to:**
- Say where things are using **в/у** (in) and **на** (on) with the Locative case
- Describe relative positions with **біля** (near) and **навпроти** (opposite) with the Genitive case
- Ask and give directions using **Де знаходиться...?** (Where is ... located?)

## Presentation

### В/У + Місцевий (In + Locative)

The most common preposition for being inside an enclosed space is **в** or **у** (meaning "in" or "at"), followed by a noun in the Locative case.

You already know that the Locative case is used to show location. For most nouns, you simply change the final vowel to **-і**. Let's look at some high-frequency collocations for buildings, cities, and countries where we use the "in" meaning. Notice how the endings change to show that we are talking about a location.

*   **магазин** (store) → **в магазині** (in the store)
*   **школа** (school) → **у школі** (in the school)
*   **місто** (city) → **у місті** (in the city)
*   **Україна** (Ukraine) → **в Україні** (in Ukraine)

You might be wondering: why do we sometimes use **в** and sometimes **у**? This brings us to a beautiful feature of the Ukrainian language known as *милозвучність* (euphony, or musicality). Ukrainian speakers naturally alternate between **в** and **у** to avoid clunky consonant clusters and to make the language flow smoothly like a song. 

Here are the basic euphony rules you need to know:
1.  **Use «у» between two consonants.** If the previous word ends in a consonant, and the next word starts with a consonant, use **у** to create a bridge.
2.  **Use «у» before clusters starting with `в`, `ф`, `льв`, `зв`, `св`.** Even if the previous word ends in a vowel, these heavy clusters demand the softer **у**. A very common learner error is saying «в Львові» — this is incredibly hard to pronounce! You must always say **у Львові** (in Lviv).
3.  **Use «в» between vowels.** If the previous word ends in a vowel and the next word starts with a vowel, use **в**.
4.  **Use «в» at the beginning of a sentence before a vowel.**

> [!tip] 
> Remember that **в** and **у** mean the exact same thing! The choice between them is only about making the sentence easier to pronounce.

Let's look at these euphony rules in action with some practical examples. Pay close attention to the letters immediately before and after the preposition.

*   Він був **у** школі. (He was in the school. — *consonant before, consonant after*)
*   Вона **в** автобусі. (She is in the bus. — *vowel before, vowel after*)
*   Вона **у** Львові. (She is in Lviv. — *before the `льв`- cluster*)

Finally, as a quick review, remember that some consonants undergo a special alternation when they take the Locative **-і** ending. This is a very old linguistic rule that makes the words easier to say. If a word ends in **г**, **к**, or **х**, these consonants will change to **з**, **ц**, or **с** right before the **-і** ending. 

Here are the consonant alternations you need to practice. Read them aloud and notice how the sound changes in the back of your mouth.

| Nominative (Base) | Locative (Location) | Rule |
| :--- | :--- | :--- |
| **нога** (leg) | **на нозі** (on the leg) | **г** → **з** |
| **рука** (hand) | **у руці** (in the hand) | **к** → **ц** |
| **вухо** (ear) | **у вусі** (in the ear) | **х** → **с** |

Always keep an ear out for these euphony rules and alternations. They are not just grammar chores; they are the secret to sounding truly authentic and natural when speaking Ukrainian.

> [!did-you-know]
> The word *милозвучність* literally means "pleasant-soundingness." Ukrainian is one of the few European languages with a systematic euphony rule built right into its spelling conventions. When you master в/у alternation, you are not just following a rule — you are speaking the way the language naturally wants to flow!

**Читаємо разом! (Let's read together!)**

> Тато **в** офісі. Мама **у** школі. Кіт **в** автобусі. Дідусь **у** Львові. Бабуся **в** Україні. Я **у** місті.

*(Dad is in the office. Mom is in school. The cat is in the bus. Grandpa is in Lviv. Grandma is in Ukraine. I am in the city.)*

### На + Місцевий (On + Locative)

While **в/у** means "in" or "inside", the preposition **на** translates to "on". We use **на** followed by the Locative case when we want to talk about location on a surface, physical contact, or open spaces. 

Think of physical objects resting on top of other objects. Just like in English, you wouldn't say your cup is "in" the table; you say it is "on" the table. 

*   **стіл** (table) → **на столі** (on the table)
*   **стіна** (wall) → **на стіні** (on the wall)
*   **підлога** (floor) → **на підлозі** (on the floor — *notice the г → з alternation!*)
*   **вулиця** (street) → **на вулиці** (on the street / outside)

However, Ukrainian uses **на** for more than just physical surfaces. There is a very important social and activity exception where **на** replaces **в/у**. We use **на** for events, processes, and certain institutions. When you go to a concert, you are participating in an event, not just entering a box. Therefore, you are "on" the concert.

Here are the most common examples of this social/activity exception. You should memorize these as fixed phrases.

*   **на концерті** (at the concert)
*   **на роботі** (at work)
*   **на пошті** (at the post office — *institutional usage*)
*   **на уроці** (at the lesson / in class)

A great way to understand this distinction is to look at contrast pairs. Sometimes, you can use both **в** and **на** with similar places, but the meaning or the tradition changes completely. 

For example, when you are talking about rooms in a house, you generally use **в** (inside the room). But there is a massive traditional exception: the kitchen! Historically, cooking areas were open hearths or separate utility spaces, not enclosed rooms in the same way a bedroom is. Because of this linguistic remnant, Ukrainians always say **на кухні** (in the kitchen).

Let's compare these contrast pairs to see the difference clearly:

*   **в кімнаті** (inside a room) vs **на кухні** (in the kitchen)
*   **в театрі** (inside the theatre building) vs **на виставі** (at the theatre performance)
*   **в університеті** (inside the university) vs **на лекції** (at the lecture)

As an English speaker, you might be tempted to default to **в** for everything because "in" feels so universal. Be careful! Saying *в пошті* instead of **на пошті** is a very common beginner mistake. Always ask yourself: is this a physical box I am standing inside, or is this an event, an institution, or a surface?

**Читаємо разом! (Let's read together!)**

> Книга **на столі**. Картина **на стіні**. Тато **на роботі**. Сестра **на уроці**. Ми **на концерті**. Кіт спить **на підлозі**, а я готую **на кухні**.

*(The book is on the table. The picture is on the wall. Dad is at work. Sister is in class. We are at the concert. The cat sleeps on the floor, and I'm cooking in the kitchen.)*

### Біля/Поруч/Між (Near/Next to/Between)

Now that we know how to say we are "in" or "on" something, how do we describe where buildings are relative to each other? For this, we need prepositions of proximity and orientation.

The most important preposition for giving directions is **біля** (near, close to). Unlike **в** and **на** which take the Locative case, the preposition **біля** takes the Genitive case. This is a very high-frequency pattern, so you will use it constantly when navigating a city.

To form the Genitive case for most masculine and neuter nouns, you add **-а** or **-я**. For feminine nouns, you change the ending to **-и** or **-і**. Let's look at how we use **біля** to describe where things are.

*   **біля школи** (near the school)
*   **біля парку** (near the park)
*   **біля магазину** (near the store)
*   **біля зупинки** (near the bus stop)

When you want to say that something is directly across the street or facing another building, you use the orientation preposition **навпроти** (opposite). Just like **біля**, the preposition **навпроти** also requires the Genitive case. This is incredibly useful for city orientation tasks.

*   **навпроти банку** (opposite the bank)
*   **навпроти аптеки** (opposite the pharmacy)
*   **навпроти пошти** (opposite the post office)

While **біля** and **навпроти** use the Genitive case, there are other useful location prepositions that use a completely different case called the Instrumental. We will learn the full rules for the Instrumental case later, but for now, you can learn these two expressions as formulaic chunks or fixed phrases. 

These preview chunks are fantastic for expanding your descriptive abilities right now.

*   **поруч з** + Instrumental (next to / right alongside)
*   **між** + Instrumental (between)

You will hear these words often when native speakers give detailed directions. If you want to say that something is very distant, you can use the distance expression **далеко від** (far from), which again uses the Genitive case. If it is very close, you can say **близько від** (close to). 

By mastering just **біля** and **навпроти**, you can already guide someone through a basic city block!

**Читаємо разом! (Let's read together!)**

> Школа знаходиться **біля парку**. **Навпроти школи** є аптека. Магазин **поруч з** банком. Зупинка **між** школою і аптекою. Пошта **далеко від** парку, але **близько від** метро.

*(The school is near the park. Opposite the school there is a pharmacy. The store is next to the bank. The bus stop is between the school and the pharmacy. The post office is far from the park, but close to the metro.)*

### Де знаходиться...? (Where is...?)

To give directions, you first have to know how to ask for them! Up until now, you might have used the simple word **де** (where) to ask about locations, for example: «Де мама?» (Where is mom?). 

However, when we are talking about buildings, landmarks, or formal locations on a map, it is much more natural and polite to use the formal location verb **знаходиться** (is located). This is a formal alternative to simply using the verb "to be". It makes your Ukrainian sound polished and respectful, especially when talking to strangers on the street.

Let's look at how to ask these location questions properly:

*   **Де знаходиться пошта?** (Where is the post office located?)
*   **Де знаходиться найближча аптека?** (Where is the nearest pharmacy located?)
*   **Вибачте, де знаходиться магазин?** (Excuse me, where is the store located?)

When answering these questions with full sentences, you will combine the verb **знаходиться** with the prepositions and case forms you have just learned. You can use **на вулиці** to give the street name, or **біля** to give a nearby landmark.

Here are some complete, realistic answers you might hear or give:

*   **Пошта знаходиться на вулиці Хрещатик.** (The post office is located on Khreshchatyk street.)
*   **Аптека знаходиться біля метро.** (The pharmacy is located near the subway.)
*   **Школа знаходиться навпроти парку.** (The school is located opposite the park.)

To make your learning more authentic, let's use some real cultural context. When giving directions in Kyiv, the capital of Ukraine, locals frequently use major landmarks as reference points:

*   **Хрещатик** (Khreshchatyk — the main street)
*   **Майдан** (Maidan — Independence Square)
*   **Золоті Ворота** (Golden Gate — historical monument)

If you visit Kyiv, you will constantly hear directions anchored to these specific spots:

*   Кафе знаходиться **на вулиці Хрещатик**.
*   Магазин знаходиться **біля Майдану**.
*   Театр знаходиться **поруч з** метро Золоті Ворота.

Using the verb **знаходиться** along with your new prepositions will make you sound like a confident, capable traveler!

> [!culture-note]
> Kyiv's **Хрещатик** is more than a street — it is the symbolic heart of Ukraine. Destroyed during World War II and rebuilt in the 1950s, it became the site of the Orange Revolution (2004) and the Revolution of Dignity (2013–2014). When Ukrainians say «на Хрещатику», they mean the place where the nation's history unfolds.

**Читаємо разом! (Let's read together!)**

> — Вибачте, **де знаходиться** музей?
> — Музей знаходиться **на вулиці** Хрещатик, **біля** Майдану.
> — А **де знаходиться** найближча аптека?
> — Аптека знаходиться **навпроти** музею, **поруч з** кафе.
> — Дякую!

*(— Excuse me, where is the museum located? — The museum is on Khreshchatyk street, near Maidan. — And where is the nearest pharmacy? — The pharmacy is opposite the museum, next to the cafe. — Thank you!)*

## Практика (Practice)

Let's put everything you have learned together! When you describe where objects are in a room, or where buildings are in a city, you will often need to use multiple prepositions in connected speech. This location description drill will train your brain to switch between cases smoothly.

Read this short description of a neighborhood and notice the bolded prepositions and case endings:

> Моя хата знаходиться **на вулиці** Франка. Вона **біля парку**. **Навпроти хати** є великий магазин. **В магазині** є молоко, хліб і м'ясо. Аптека знаходиться **далеко від** школи, але **близько від** пошти. Я зараз **на кухні**, а мій кіт спить **на підлозі**.

Now, let's look at a realistic dialogue. Imagine a tourist asking for directions in the city center. Notice how they use the formal verb to ask, and how the local uses landmarks and prepositions to answer.

> — Вибачте, **де знаходиться** пошта?
> — Пошта знаходиться **на вулиці** Шевченка.
> — Це **далеко**?
> — Ні, це **близько**. Вона **біля банку**, **навпроти кафе**.
> — Дуже дякую!
> — Будь ласка.

Read this dialogue aloud a few times. Try replacing the words for "post office" and "bank" with other vocabulary words like **школа** and **аптека**. Practicing these formulaic chunks will help you build muscle memory for navigating any Ukrainian street.

## Підсумок
You have done an amazing job today! You have unlocked the ability to navigate a city and describe locations using prepositions.

**You can now:**
- ✅ Say where things are inside enclosed spaces using **в/у** + Locative (в магазині, у школі)
- ✅ Apply the euphony rule to choose between **в** and **у** naturally
- ✅ Describe location on surfaces and at events using **на** + Locative (на столі, на роботі)
- ✅ Give relative positions with **біля** + Genitive (біля парку) and **навпроти** + Genitive (навпроти банку)
- ✅ Ask and answer location questions with **Де знаходиться...?**

Take a moment to review your knowledge with these self-check questions:

1.  Why do we say **у Львові** instead of **в Львові**? What rule are we following?
2.  How do you say "in the kitchen" in Ukrainian, and why is it an exception?
3.  If a store is near a school, what preposition and case do you use to describe its location?
4.  Translate this sentence into Ukrainian: "Where is the pharmacy located? It is opposite the post office."

Keep practicing, and soon you will be giving directions like a local!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/genitive-prepositions.yaml`

```yaml
- type: fill-in
  title: "Choose the Correct Preposition"
  instruction: "Fill in the blank with the correct preposition (в, у, or на) to complete each sentence."
  items:
    - sentence: "Мама ___ магазині."
      answer: "в"
      options: ["в", "у", "на", "біля"]
      explanation: "We use в before магазині because the previous word ends in a vowel (а) and the next word starts with a consonant (м)."
    - sentence: "Він був ___ школі."
      answer: "у"
      options: ["в", "у", "на", "навпроти"]
      explanation: "We use у between two consonants (в before ш) to keep the sentence flowing smoothly."
    - sentence: "Книга лежить ___ столі."
      answer: "на"
      options: ["в", "у", "на", "біля"]
      explanation: "We use на for surfaces — the book is resting on top of the table."
    - sentence: "Вона ___ Львові."
      answer: "у"
      options: ["в", "у", "на", "між"]
      explanation: "We always use у before the льв- cluster. Saying в Львові is a common learner error."
    - sentence: "Тато ___ роботі."
      answer: "на"
      options: ["в", "у", "на", "поруч"]
      explanation: "Work (робота) is an activity, not a physical box, so we use на for this institutional meaning."
    - sentence: "Ми зараз ___ кухні."
      answer: "на"
      options: ["в", "у", "на", "далеко"]
      explanation: "The kitchen is a traditional exception — Ukrainians always say на кухні, not в кухні."
    - sentence: "Діти ___ кімнаті."
      answer: "в"
      options: ["в", "у", "на", "біля"]
      explanation: "A room is an enclosed space, so we use в/у. Here в works because the previous word ends in a vowel."
    - sentence: "Кіт спить ___ підлозі."
      answer: "на"
      options: ["в", "у", "на", "навпроти"]
      explanation: "The floor is a surface, so we use на. Notice the г→з alternation: підлога → на підлозі."
    - sentence: "Я ___ автобусі."
      answer: "в"
      options: ["в", "у", "на", "між"]
      explanation: "A bus is an enclosed space (you are inside it), so we use в/у. Here в works before a vowel (а)."
    - sentence: "Вона зараз ___ уроці."
      answer: "на"
      options: ["в", "у", "на", "біля"]
      explanation: "A lesson is an event or activity, not a physical space, so we use на уроці."

- type: quiz
  title: "Prepositions and Location"
  instruction: "Choose the correct answer for each question about Ukrainian location prepositions."
  items:
    - question: "Which preposition do you use to say someone is at a concert?"
      options:
        - text: "на концерті"
          correct: true
        - text: "в концерті"
          correct: false
        - text: "біля концерті"
          correct: false
        - text: "у концерті"
          correct: false
      explanation: "A concert is an event, so we use на. На концерті means at the concert."
    - question: "Why do we say у Львові instead of в Львові?"
      options:
        - text: "Because у is required before the льв- consonant cluster"
          correct: true
        - text: "Because Львів is a special city"
          correct: false
        - text: "Because в is only for small cities"
          correct: false
        - text: "Because у always comes before Л"
          correct: false
      explanation: "The euphony rule requires у before heavy clusters like льв-, зв-, св- to keep the language flowing smoothly."
    - question: "What case does the preposition біля require?"
      options:
        - text: "Genitive"
          correct: true
        - text: "Locative"
          correct: false
        - text: "Nominative"
          correct: false
        - text: "Instrumental"
          correct: false
      explanation: "Біля (near) always takes the Genitive case: біля школи, біля парку, біля магазину."
    - question: "How do you say 'Where is the post office located?' in Ukrainian?"
      options:
        - text: "Де знаходиться пошта?"
          correct: true
        - text: "Де пошта знаходиться?"
          correct: false
        - text: "Пошта де знаходиться?"
          correct: false
        - text: "Знаходиться де пошта?"
          correct: false
      explanation: "The natural word order is Де знаходиться + noun. The verb знаходиться is used for formal location questions."
    - question: "Which phrase correctly says 'opposite the pharmacy'?"
      options:
        - text: "навпроти аптеки"
          correct: true
        - text: "навпроти аптека"
          correct: false
        - text: "навпроти аптеку"
          correct: false
        - text: "навпроти аптеці"
          correct: false
      explanation: "Навпроти takes the Genitive case. The Genitive of аптека is аптеки."
    - question: "What happens to the letter г in нога when you put it in the Locative case?"
      options:
        - text: "г changes to з (на нозі)"
          correct: true
        - text: "г changes to ж (на ножі)"
          correct: false
        - text: "г stays the same (на нозі would not have з)"
          correct: false
        - text: "г changes to к (рука → руці, but not нога)"
          correct: false
      explanation: "In the Locative case, г alternates to з. So нога becomes на нозі."
    - question: "Why do Ukrainians say на кухні instead of в кухні?"
      options:
        - text: "It is a traditional exception from when kitchens were open cooking areas"
          correct: true
        - text: "Because кухня starts with the letter к"
          correct: false
        - text: "Because kitchens are always outside"
          correct: false
        - text: "Because на is always used with food places"
          correct: false
      explanation: "Historically, cooking areas were open hearths, not enclosed rooms. This linguistic tradition persists in modern Ukrainian."
    - question: "Which preposition pair uses the Instrumental case as a preview chunk?"
      options:
        - text: "поруч з / між"
          correct: true
        - text: "біля / навпроти"
          correct: false
        - text: "в / на"
          correct: false
        - text: "далеко від / близько від"
          correct: false
      explanation: "Поруч з (next to) and між (between) take the Instrumental case. Біля and навпроти take the Genitive."
    - question: "How do you say 'near the bus stop' in Ukrainian?"
      options:
        - text: "біля зупинки"
          correct: true
        - text: "біля зупинка"
          correct: false
        - text: "біля зупинку"
          correct: false
        - text: "біля зупинці"
          correct: false
      explanation: "Біля takes the Genitive case. The Genitive of зупинка (feminine) is зупинки."
    - question: "What is the correct way to say 'in the city' in Ukrainian?"
      options:
        - text: "у місті"
          correct: true
        - text: "в місто"
          correct: false
        - text: "на місті"
          correct: false
        - text: "у місто"
          correct: false
      explanation: "A city is an enclosed space, so we use в/у + Locative. Місто becomes місті in the Locative case."

- type: match-up
  title: "Match the Place to Its Preposition Phrase"
  instruction: "Match each place on the left with the correct Ukrainian prepositional phrase on the right."
  pairs:
    - left: "in the store"
      right: "в магазині"
    - left: "on the table"
      right: "на столі"
    - left: "at the post office"
      right: "на пошті"
    - left: "near the school"
      right: "біля школи"
    - left: "opposite the bank"
      right: "навпроти банку"
    - left: "in the kitchen"
      right: "на кухні"
    - left: "at the lesson"
      right: "на уроці"
    - left: "on the street"
      right: "на вулиці"
    - left: "near the park"
      right: "біля парку"
    - left: "in the school"
      right: "у школі"

- type: true-false
  title: "True or False?"
  instruction: "Decide whether each statement about Ukrainian location prepositions is true or false."
  items:
    - statement: "The prepositions в and у mean the same thing — the choice between them depends on euphony."
      correct: true
      explanation: "Correct! В and у both mean 'in'. You choose between them based on surrounding sounds to keep the language flowing."
    - statement: "You should say в Львові when talking about being in Lviv."
      correct: false
      explanation: "Wrong — you must say у Львові. The euphony rule requires у before the heavy льв- cluster."
    - statement: "The preposition на is used for events and activities, like на концерті (at the concert)."
      correct: true
      explanation: "Correct! На is used for events, activities, and institutions, not just physical surfaces."
    - statement: "Біля takes the Locative case, just like в and на."
      correct: false
      explanation: "Wrong — біля takes the Genitive case, not the Locative. For example: біля школи (Genitive), not біля школі."
    - statement: "Ukrainians say на кухні because the kitchen was traditionally an open cooking area, not an enclosed room."
      correct: true
      explanation: "Correct! This is a linguistic tradition from when kitchens were open hearths, so на (on/at) stuck instead of в (in)."
    - statement: "The verb знаходиться is used for formal location questions like 'Where is the pharmacy located?'"
      correct: true
      explanation: "Correct! Де знаходиться аптека? is more polished than simply Де аптека?"
    - statement: "When the letter к appears before the Locative ending -і, it stays unchanged."
      correct: false
      explanation: "Wrong — к changes to ц before the -і ending. For example: рука → у руці."
    - statement: "Навпроти банку means 'opposite the bank' and uses the Genitive case."
      correct: true
      explanation: "Correct! Навпроти takes the Genitive case. Банк → банку (Genitive)."
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/genitive-prepositions.yaml`

```yaml
items:
  - lemma: "магазин"
    translation: "store, shop"
    pos: "noun"
    gender: "m"
    usage: "в магазині"
    notes: "High-frequency location noun; Locative form магазині"
  - lemma: "школа"
    translation: "school"
    pos: "noun"
    gender: "f"
    usage: "у школі"
    notes: "Euphonic у before ш-cluster"
  - lemma: "вулиця"
    translation: "street"
    pos: "noun"
    gender: "f"
    usage: "на вулиці"
    notes: "Uses на for surface/outdoor meaning"
  - lemma: "стіл"
    translation: "table"
    pos: "noun"
    gender: "m"
    usage: "на столі"
    notes: "Basic surface location; stem vowel і drops in Locative"
  - lemma: "кухня"
    translation: "kitchen"
    pos: "noun"
    gender: "f"
    usage: "на кухні"
    notes: "Traditional на exception — historically an open cooking area"
  - lemma: "пошта"
    translation: "post office"
    pos: "noun"
    gender: "f"
    usage: "на пошті"
    notes: "Institutional на usage; also means 'mail'"
  - lemma: "біля"
    translation: "near, close to"
    pos: "prep"
    usage: "біля школи"
    notes: "Takes Genitive case; high-frequency direction preposition"
  - lemma: "навпроти"
    translation: "opposite, across from"
    pos: "prep"
    usage: "навпроти банку"
    notes: "Takes Genitive case; city orientation preposition"
  - lemma: "знаходитися"
    translation: "to be located"
    pos: "verb"
    aspect: "imperfective"
    usage: "Де знаходиться пошта?"
    notes: "Formal alternative to бути for location; 3rd person: знаходиться"
  - lemma: "поруч"
    translation: "nearby, next to"
    pos: "adv"
    usage: "поруч з магазином"
    notes: "Poruч з + Instrumental; introduced as a formulaic chunk"
  - lemma: "між"
    translation: "between"
    pos: "prep"
    usage: "між парком і школою"
    notes: "Takes Instrumental case; preview chunk in this module"
  - lemma: "далеко"
    translation: "far"
    pos: "adv"
    usage: "далеко від школи"
    notes: "Далеко від + Genitive; distance expression"
  - lemma: "близько"
    translation: "near, close"
    pos: "adv"
    usage: "близько від пошти"
    notes: "Близько від + Genitive; distance expression"
  - lemma: "парк"
    translation: "park"
    pos: "noun"
    gender: "m"
    usage: "біля парку"
    notes: "Genitive form парку; common city landmark"
  - lemma: "аптека"
    translation: "pharmacy"
    pos: "noun"
    gender: "f"
    usage: "навпроти аптеки"
    notes: "Genitive form аптеки; common direction reference"
  - lemma: "банк"
    translation: "bank"
    pos: "noun"
    gender: "m"
    usage: "навпроти банку"
    notes: "Genitive form банку"
  - lemma: "зупинка"
    translation: "bus stop"
    pos: "noun"
    gender: "f"
    usage: "біля зупинки"
    notes: "Genitive form зупинки; essential city navigation word"
  - lemma: "метро"
    translation: "subway, metro"
    pos: "noun"
    gender: "n"
    usage: "біля метро"
    notes: "Indeclinable noun — form does not change in any case"
  - lemma: "хата"
    translation: "house, home"
    pos: "noun"
    gender: "f"
    usage: "Моя хата знаходиться на вулиці Франка."
    notes: "Traditional Ukrainian word for house (vs. будинок for a building)"
  - lemma: "кафе"
    translation: "cafe"
    pos: "noun"
    gender: "n"
    usage: "навпроти кафе"
    notes: "Indeclinable noun; common city landmark for giving directions"
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
- Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/genitive-prepositions.md`
- Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/genitive-prepositions.yaml`
- Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/genitive-prepositions.yaml`

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

✅ Message sent to Gemini (ID: 26083) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #26083...
📨 Message #26083
   From: gemini → To: gemini
   Type: query
   Task: consonant-sounds-review-fix-2
   Time: 2026-03-16T22:13:07.249675+00:00

============================================================

# Gemini Review Fix: Targeted Repair via FIND/REPLACE

> **You are an expert Ukrainian language editor applying targeted fixes.**
> You have NO tools — output FIND/REPLACE pairs only.
> The build system will apply your fixes programmatically.

---

## Editing Principles

- **IMPROVE, don't destroy.** Every rewrite should teach MORE than the original.
- **PRESERVE the author's intent.** Rewrite poorly explained content to explain it well — don't delete it.
- **MATCH the surrounding voice.** Your fixes should read like the original author wrote them on a better day.
- Only DELETE truly empty sentences (pure cheerleading with zero information).

---

## Fix Plan (from review)

## Critical Issues Found

### Issue 1: Linguistic Error (Misspelled Vocabulary)
**Location**: Тверді та м'які — Hard and Soft Consonants
**Problem**: The text provides the example `- **сі́р** (cheese) — soft С (before І)`. The Ukrainian word for cheese is `сир`, which has a hard С before И. `сір` is not the word for cheese.
**Fix**: Replace the example with a valid word that demonstrates a soft С before І, such as `сі́к` (juice).

### Issue 2: Incorrect Phonetic/Orthographic Description
**Location**: Сонорні — Sonorant Consonants
**Problem**: Under the `Літера Й` subsection, the text states: `яйце́ (egg — where Й sits between two vowels)`. This is factually incorrect. In the word `яйце́`, the letter `Й` sits between the vowel letter `Я` and the consonant letter `Ц` (phonetically between /a/ and /t͡s/).
**Fix**: Remove the incorrect parenthetical explanation and just leave `яйце́ (egg)`.

### Issue 3: Use of Banned IPA Brackets
**Location**: Дзвінкі та глухі пари — Voiced and Voiceless Pairs, Читання — Reading Practice, Підсумок — Summary, and Activities
**Problem**: The text uses banned phonetic brackets to represent sounds, e.g., `зу[б], NOT зу[п]`, `[ж] buzzes`, `[б] vs [п]`. The pre-screen metrics correctly flagged this (`[IPA_BANNED]`). The guidelines strictly forbid IPA brackets.
**Fix**: Remove all phonetic brackets and use the standard Cyrillic text or capitalized letters to represent the sounds, e.g., `зуб, NOT зуп`, `Ж buzzes`, `Б vs П`.

---

## Ukrainian Language Issues

- The word `сі́р` is incorrectly used instead of `сир`, creating a false association between the meaning "cheese" and the vowel `і`.

---

## Fix Plan to Reach 9.5+

1. Replace the erroneous `сі́р` example with `сі́к` in the "Тверді та м'які" section.
2. Remove the claim that `Й` sits between two vowels in `яйце́`.
3. Scrub all phonetic brackets `[...]` from the markdown content, the YAML activities, and the YAML vocabulary notes, replacing them with capitalized letters or natural spelling.

---

## Audit Failures (from automated re-audit)

```
❌ [SEMANTIC_FALSE_FRIEND] Found 1 semantic false friend(s): 'лук' translated as 'onion' (Ukrainian meaning: bow (weapon), use цибуля instead)
📚 IMMERSION TOO LOW (7.1% vs 10-25% target)
--- STRICT GATES (Level A1) ---
Lint         ❌ 13 Format Errors
Pedagogy     ❌ 1 violations
Immersion    ❌ 7.1% LOW (target 10-25% (M03))
❌ LINT ERRORS FOUND:
📚 PEDAGOGICAL VIOLATIONS FOUND:
📝 RECOMMENDATION: UPDATE (patch fixes) (severity 25/100)
→ 1 violations (minor)
→ 13 format errors (many)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/consonant-sounds-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `зу` (source: prose)
  ❌ `хлі` (source: prose)
```

---

## File Contents

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/consonant-sounds.md`

```markdown
## Вступ — Introduction

Welcome back! In Module 1, you met all 33 letters of the Ukrainian alphabet. In Module 2, you mastered the 10 vowel sounds — the open, singing heart of every Ukrainian word. Today you take the next big step: the 22 consonant letters.

Consonants are the skeleton of Ukrainian words. They give words their shape, their crunch, their rhythm. You will learn how Ukrainian organizes its consonants into three clear families: the musical sonorants, the voiced and voiceless pairs, and the hard and soft variants. By the end of this module, you will be able to read and pronounce any Ukrainian word that uses these sounds.

Every vowel you learned in Module 2 is still available — your full toolkit of А, О, У, Е, И, І, Я, Ю, Є, Ї is ready. Now you are adding the consonant sounds that wrap around those vowels to build real words.

> [!tip] Quick Orientation
> You already know some consonants from Module 1: **М** (as in **ма́ма**), **Н** (as in **ні́с**), **Л** (as in **лі́с**), **К** (as in **кі́т**), **С** (as in **сі́к**), **Т** (as in **та́то**). Today you will meet the rest and learn how they all connect.

---

## Сонорні — Sonorant Consonants

Some consonants are more musical than others. Ukrainian has five special consonants called sonorants — when you say them, your voice dominates and the noise is minimal. Think of them as the consonants closest to vowels. The five sonorants are: **Л**, **М**, **Н**, **Р**, and **В**.

You already know three of them well from Module 1:

- **М** — as in **ма́ма** (mom), **ма́сло** (butter), **молоко́** (milk)
- **Н** — as in **ні́с** (nose), **не́бо** (sky)
- **Л** — as in **лі́с** (forest), **молоко́** (milk)

📹 *Watch and repeat:*
- [Anna Ohoiko — Ukrainian Lessons — М](https://www.youtube.com/watch?v=Ez95H4ibuJo)
- [Anna Ohoiko — Ukrainian Lessons — Н](https://www.youtube.com/watch?v=vNUfiKHPYaU)
- [Anna Ohoiko — Ukrainian Lessons — Л](https://www.youtube.com/watch?v=v6-3Xg52Buk)

Now meet the two new sonorants:

### Літера Р

The Ukrainian **Р** is a rolled, trilled sound — your tongue tip taps rapidly against the ridge behind your upper teeth. It looks exactly like the English letter P, but sounds completely different! There is no connection to the English P sound whatsoever.

- **ри́ба** (fish) — you learned this word in Module 1
- **рука́** (hand) — your hand, **рука́**

Don't worry if the trill feels difficult at first. Many learners need weeks of practice. Start with a single tap and build up. You are training a muscle, not memorizing a rule.

📹 *Watch and repeat:* [Anna Ohoiko — Ukrainian Lessons — Р](https://www.youtube.com/watch?v=fMGsQ5KPQgg)

### Літера В

Here is a surprise: Ukrainian **В** is NOT like English V. In English, you press your upper teeth against your lower lip to make V. In Ukrainian, **В** is a sonorant — you round your lips gently, closer to the English W sound. No teeth touch your lip.

- **вода́** (water) — lips round softly, no teeth
- **во́вк** (wolf) — the grey wolf of Ukrainian fairy tales

Try this: hold a finger in front of your lips and say **вода́**. You should feel a gentle puff of air, not the buzzing friction of English V.

📹 *Watch and repeat:* [Anna Ohoiko — Ukrainian Lessons — В](https://www.youtube.com/watch?v=aFcvYfvQ2X4)

### Літера Й

There is one more consonant that behaves like a sonorant: **Й**. This is a short, gliding sound — like the Y in English «yes». You already met it hiding inside the iotated vowels (Я, Ю, Є, Ї) in Module 2. As a standalone letter, **Й** appears in words like **край** (edge, region) and **яйце́** (egg).

📹 *Watch and repeat:* [Anna Ohoiko — Ukrainian Lessons — Й](https://www.youtube.com/watch?v=aq0cjB90s3w)

> [!note] The Sonorant Family
> Five sonorants: **Л, М, Н, Р, В**. Plus **Й**, which is always soft. These consonants are voiced with very little noise. Ukrainian textbooks group them separately because they never have voiceless partners — they are always «дзвінкі» (voiced).
<!-- adapted from: Bolshakova, Grade 2 -->

---

## Дзвінкі та глухі пари — Voiced and Voiceless Pairs

Now for the largest group of consonants. Many Ukrainian consonants come in pairs: one voiced, one voiceless. The mouth and tongue are in exactly the same position for both — the only difference is whether your vocal cords vibrate.

### The Hand-on-Throat Test

Try this right now. Place your hand on your throat and say «zzzzz» (like a buzzing bee). Feel the vibration? That is a voiced sound — in Ukrainian, **дзві́нкий**. Now say «sssss» (like a hissing snake). The vibration stops — only air. That is a voiceless sound — **глу́хий**.

Every pair below works the same way: identical mouth position, different voicing.

> [!practice] Try It Yourself
> Put your hand on your throat. Say each pair below slowly: the first sound in each pair should make your throat buzz, the second should not. If both feel the same, try again more slowly.

### Б / П

**Б** is voiced, **П** is voiceless. Same lip position — both are made by pressing your lips together and releasing.

- **Б** — **бабу́ся** (grandma), a warm family word
- **П** — **паву́к** (spider), a little creature on the wall

📹 *Watch and repeat:*
- [Anna Ohoiko — Ukrainian Lessons — Б](https://www.youtube.com/watch?v=V1hxBE_JbGg)
- [Anna Ohoiko — Ukrainian Lessons — П](https://www.youtube.com/watch?v=JksSjjxyW5Y)

### Д / Т

**Д** is voiced, **Т** is voiceless. Your tongue touches the same spot behind your upper teeth for both.

- **Д** — **дім** (house), a place you know well
- **Т** — **та́то** (dad), from Module 1

📹 *Watch and repeat:*
- [Anna Ohoiko — Ukrainian Lessons — Д](https://www.youtube.com/watch?v=g4Bh-lqzd48)
- [Anna Ohoiko — Ukrainian Lessons — Т](https://www.youtube.com/watch?v=m-jcLR_gK0k)

### З / С

**З** is voiced, **С** is voiceless. Both are made with the tongue near the upper teeth, letting air hiss through.

- **З** — **зуб** (tooth)
- **С** — **суп** (soup)

Notice the pair **зуб** / **суп** — same final letter position, opposite voicing. This pair is perfect for practice.

📹 *Watch and repeat:*
- [Anna Ohoiko — Ukrainian Lessons — З](https://www.youtube.com/watch?v=BhASNxitC1A)
- [Anna Ohoiko — Ukrainian Lessons — С](https://www.youtube.com/watch?v=7UsFBgSL91E)

### Ж / Ш

**Ж** is voiced, **Ш** is voiceless. Both are sibilants — you shape your tongue like a shallow bowl and push air over it.

- **Ж** — **жук** (beetle), like the «zh» in English «measure»
- **Ш** — **ша́пка** (hat), like the «sh» in English «ship»

📹 *Watch and repeat:*
- [Anna Ohoiko — Ukrainian Lessons — Ж](https://www.youtube.com/watch?v=dIrGVcqPwqM)
- [Anna Ohoiko — Ukrainian Lessons — Ш](https://www.youtube.com/watch?v=1D-6MIw3OXY)

### Г / Х

This pair surprises most English speakers. Ukrainian **Г** is NOT a hard «g» like English «go». It is a soft, throaty sound — a voiced glottal fricative. Imagine a gentle, breathy «h» with your voice added. **Х** is its voiceless partner — like the «ch» in Scottish «loch» or German «ach».

- **Г** — **гора́** (mountain), soft and throaty
- **Х** — **хліб** (bread), the sacred staple of Ukrainian cuisine

📹 *Watch and repeat:*
- [Anna Ohoiko — Ukrainian Lessons — Г](https://www.youtube.com/watch?v=gVnclpSI0DU)
- [Anna Ohoiko — Ukrainian Lessons — Х](https://www.youtube.com/watch?v=vpr58zJSJKc)

### Ґ / К

So where is the hard «g» sound? It exists in Ukrainian — but it is the rare letter **Ґ** (with an upturn). **Ґ** is the voiced partner of **К**.

- **Ґ** — **ґа́нок** (porch), a classic textbook word
- **К** — **кіт** (cat), from Module 1

**Ґ** is the rarest letter in the Ukrainian alphabet — only about 400 native Ukrainian words use it. It was removed from the alphabet in 1933 and restored in 1990. When you see **Ґ**, you know you are looking at a genuinely Ukrainian word.

📹 *Watch and repeat:* [Anna Ohoiko — Ukrainian Lessons — К](https://www.youtube.com/watch?v=J7sGEI4-xJo)

### The No-Devoicing Rule

> [!warning] Critical Rule — Voiced Consonants Stay Voiced!
> In Ukrainian, voiced consonants do NOT become voiceless at the end of a word. This is different from English, German, and many other languages.
>
> - **зуб** — say зуб, NOT зуп
> - **хліб** — say хліб, NOT хліп
> - **во́вк** — say вовк with the В voiced
>
> If you come from English, Russian, or German, your instinct is to soften the final consonant. Resist that instinct! Every consonant keeps its voice, beginning to end.
<!-- adapted from: Kravtsova, Grade 2 -->

This is one of the most important pronunciation rules in Ukrainian. Practice with these pairs — the first word ends in a voiced consonant, the second in a voiceless one. They should sound different at the end:

- **зуб** (tooth) / **суп** (soup) — Б vs П
- **хліб** (bread) / **сік** (juice) — Б vs К

---

## Тверді та м'які — Hard and Soft Consonants

Ukrainian has one more layer of consonant organization: most consonants come in **hard** and **soft** variants. A hard consonant is the default — your tongue sits in its normal position. A soft consonant (also called palatalized) means you raise the middle of your tongue toward the roof of your mouth, adding a slight «y» quality to the sound.

How does a consonant become soft? It happens automatically before certain vowels:

- Before **І**: the consonant softens — **лі́с** (forest) has a soft Л
- Before **Я, Ю, Є**: the consonant softens — **лю́ди** (people) has a soft Л
- Before **Ь** (soft sign): the consonant softens — but the soft sign is covered in Module 4

The back vowels **А, О, У, Е, И** keep the consonant hard.

### The лук / люк Minimal Pair

The best way to hear the hard/soft difference is with a minimal pair — two words that differ by only one sound:

- **лук** (onion) — hard Л, tongue stays low
- **люк** (hatch) — soft Л, tongue rises toward the palate

Same word length, same vowel sound after the Л — but the consonant quality changes, and so does the meaning completely. This is how powerful the hard/soft distinction is in Ukrainian.

Here are more examples of soft consonants:

- **день** (day) — soft Д and soft Н
- **сіль** (salt) — soft С and soft Л
- **сі́к** (juice) — soft С (before І)

> [!tip] Hard and Soft — A Preview
> You do not need to master every hard/soft pattern today. The key idea is simple: **the vowel after a consonant controls whether it is hard or soft.** Module 4 will complete this picture with the soft sign **Ь**, which can soften a consonant even without a following vowel.

### Always-Hard and Always-Soft

Not every consonant plays the hard/soft game:

- **Ж** and **Ш** are **always hard** — even before І, they stay hard. The word **жі́нка** has a hard Ж despite the І.
- **Й** is **always soft** — it never has a hard variant.

<!-- adapted from: Bolshakova, Grade 2 -->

---

## Читання — Reading Practice

Time to put all your consonant knowledge to work. Read these words aloud, paying attention to the consonant sounds. Remember: no devoicing at word end, and watch for hard/soft differences.

### Sonorant Words

- **ма́ма** (mom) — **не́бо** (sky) — **ри́ба** (fish)
- **рука́** (hand) — **вода́** (water) — **во́вк** (wolf)
- **молоко́** (milk) — **лі́с** (forest)

### Voiced/Voiceless Pair Drills

Read each pair aloud. The first word starts (or features) a voiced consonant, the second its voiceless partner:

- **зуб** / **суп** — feel the difference at the end: [б] stays voiced, [п] is voiceless
- **жук** / **ша́пка** — [ж] buzzes, [ш] hisses
- **гора́** / **хор** — [г] is soft and throaty, [х] is a voiceless whisper
- **бабу́ся** / **паву́к** — lips together for both, voice on for Б, off for П
- **дім** / **та́то** — tongue in the same place, voice on for Д, off for Т

### Hard/Soft Minimal Pairs

- **лук** (onion) / **люк** (hatch) — hard Л vs soft Л
- **ди́м** (smoke) / **дім** (house) — И keeps Д hard, І makes Д soft

### Labeling Practice

Try reading these simple phrases. No verbs yet — just identifying things:

- **Це хліб.** (This is bread.)
- **Це дім.** (This is a house.)
- **Це жук.** (This is a beetle.)
- **Ось бабу́ся.** (Here is grandma.)
- **Це гора́.** (This is a mountain.)
- **Ось ша́пка.** (Here is a hat.)
- **Це во́вк.** (This is a wolf.)
- **Це суп.** (This is soup.)

> [!challenge] Reading Challenge
> Can you read all eight labeling phrases above without hesitation? Try timing yourself. Then read them again, faster. You are building your reading fluency with every repetition. Great job getting this far!

### Micro-Dialogues

Practice these short exchanges using words you know:

— Це кіт?
— Так, це кіт.

— Це суп?
— Ні, це молоко́.

— Ша́пка тут?
— Так, ша́пка тут.

— Хліб там?
— Ні, хліб тут. А сіль там.

---

## Підсумок — Summary

You have just learned the entire consonant system of Ukrainian. Here is what you now know:

- **5 sonorants**: Л, М, Н, Р, В — the musical consonants that are always voiced
- **6 voiced/voiceless pairs**: Б/П, Д/Т, З/С, Ж/Ш, Г/Х, Ґ/К
- **Hard and soft variants**: consonants change quality depending on the following vowel
- **The no-devoicing rule**: voiced consonants stay voiced at word end — **зуб** is зуб, never зуп

> [!tip] Self-Check
> Test yourself with these questions:
> 1. What are the 5 sonorant consonants?
> 2. What is the voiceless partner of **Б**?
> 3. Is **Г** a hard «g» or a soft throaty sound?
> 4. Do voiced consonants devoice at the end of a word in Ukrainian?
> 5. What is the difference between **лук** and **люк**?
>
> If you can answer all five, you are ready for Module 4!

**What is next?** Module 4 completes the Ukrainian alphabet. You will meet the soft sign **Ь** (which forces consonants to become soft), the apostrophe **'**, the affricates **Ц**, **Ч**, **Щ**, the digraphs **ДЖ** and **ДЗ**, and the rare letter **Ф**. After that, you will know every letter and sound in Ukrainian. You are doing wonderfully — keep going!
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/consonant-sounds.yaml`

```yaml
- type: watch-and-repeat
  title: Voiced and Voiceless Consonant Pairs
  instruction: Watch each video and repeat the consonant sound aloud. Pay attention
    to whether your throat vibrates (voiced) or not (voiceless).
  items:
  - letter: Б
    word: бабуся
    video: https://www.youtube.com/watch?v=V1hxBE_JbGg
    note: Voiced — feel your throat vibrate
  - letter: П
    word: павук
    video: https://www.youtube.com/watch?v=JksSjjxyW5Y
    note: Voiceless partner of Б — no vibration
  - letter: Д
    word: дім
    video: https://www.youtube.com/watch?v=g4Bh-lqzd48
    note: Voiced — tongue behind upper teeth
  - letter: Т
    word: тато
    video: https://www.youtube.com/watch?v=m-jcLR_gK0k
    note: Voiceless partner of Д
  - letter: З
    word: зуб
    video: https://www.youtube.com/watch?v=BhASNxitC1A
    note: Voiced — like a buzzing bee
  - letter: С
    word: суп
    video: https://www.youtube.com/watch?v=7UsFBgSL91E
    note: Voiceless partner of З — like a hissing snake
  - letter: Ж
    word: жук
    video: https://www.youtube.com/watch?v=dIrGVcqPwqM
    note: Voiced — like zh in English measure
  - letter: Ш
    word: шапка
    video: https://www.youtube.com/watch?v=1D-6MIw3OXY
    note: Voiceless partner of Ж — like sh in English ship
  - letter: Г
    word: гора
    video: https://www.youtube.com/watch?v=gVnclpSI0DU
    note: Voiced — soft throaty sound, NOT like English G
  - letter: Х
    word: хліб
    video: https://www.youtube.com/watch?v=vpr58zJSJKc
    note: Voiceless partner of Г — like ch in Scottish loch
  - letter: К
    word: кіт
    video: https://www.youtube.com/watch?v=J7sGEI4-xJo
    note: Voiceless partner of Ґ
  - letter: Р
    word: риба
    video: https://www.youtube.com/watch?v=fMGsQ5KPQgg
    note: Sonorant — rolled/trilled R, tongue tip taps rapidly
- type: classify
  title: Sort the Consonants by Type
  instruction: Drag each consonant letter into the correct category. Sonorants are
    musical and always voiced. Voiced consonants make your throat vibrate. Voiceless
    consonants use only air.
  categories:
  - label: Sonorants (сонорні)
    items:
    - Л
    - М
    - Н
    - Р
    - В
  - label: Voiced (дзвінкі)
    items:
    - Б
    - Д
    - З
    - Ж
    - Г
  - label: Voiceless (глухі)
    items:
    - П
    - Т
    - С
    - Ш
    - Х
- type: image-to-letter
  title: What Letter Does It Start With?
  instruction: Look at the picture and tap the Ukrainian letter that the word starts
    with.
  items:
  - emoji: 🐛
    answer: Ж
    distractors:
    - Ш
    - З
    note: жук (beetle)
  - emoji: 🧢
    answer: Ш
    distractors:
    - Ж
    - С
    note: шапка (hat)
  - emoji: ✋
    answer: Р
    distractors:
    - Л
    - М
    note: рука (hand)
  - emoji: 🐺
    answer: В
    distractors:
    - Б
    - М
    note: вовк (wolf)
  - emoji: ⛰️
    answer: Г
    distractors:
    - Х
    - К
    note: гора (mountain)
  - emoji: 🍞
    answer: Х
    distractors:
    - Г
    - К
    note: хліб (bread)
  - emoji: 🐱
    answer: К
    distractors:
    - Г
    - Т
    note: кіт (cat)
  - emoji: 🕷️
    answer: П
    distractors:
    - Б
    - В
    note: павук (spider)
- type: match-up
  title: Match Voiced to Voiceless Partner
  instruction: Each voiced consonant has a voiceless partner. Match them up.
  pairs:
  - left: Б (voiced)
    right: П (voiceless)
  - left: Д (voiced)
    right: Т (voiceless)
  - left: З (voiced)
    right: С (voiceless)
  - left: Ж (voiced)
    right: Ш (voiceless)
  - left: Г (voiced)
    right: Х (voiceless)
  - left: Ґ (voiced)
    right: К (voiceless)
- type: quiz
  title: Consonant Knowledge Check
  instruction: Choose the correct answer for each question about Ukrainian consonants.
  items:
  - question: Which type of consonant is Б?
    explanation: Б is a voiced consonant. Its voiceless partner is П.
    options:
    - text: Voiced (дзвінкий)
      correct: true
    - text: Voiceless (глухий)
      correct: false
    - text: Sonorant (сонорний)
      correct: false
    - text: Always soft
      correct: false
  - question: What is the voiceless partner of Д?
    explanation: Д and Т are a voiced/voiceless pair. Same tongue position, different
      voicing.
    options:
    - text: Т
      correct: true
    - text: П
      correct: false
    - text: С
      correct: false
    - text: К
      correct: false
  - question: Which consonant is the Ukrainian rolled, trilled sound?
    explanation: Р is a rolled trill — your tongue tip taps against the ridge behind
      your upper teeth.
    options:
    - text: Р
      correct: true
    - text: Л
      correct: false
    - text: В
      correct: false
    - text: Г
      correct: false
  - question: How does Ukrainian Г sound?
    explanation: Ukrainian Г is a soft, throaty sound (voiced glottal fricative),
      NOT a hard g like English go.
    options:
    - text: A soft, throaty sound — not like English G
      correct: true
    - text: Like the G in English go
      correct: false
    - text: Like the H in English hat
      correct: false
    - text: Like the K in English kit
      correct: false
  - question: Which consonant is always hard, even before the vowel І?
    explanation: Ш is always hard. Even in a word like жінка, Ж stays hard despite
      the І.
    options:
    - text: Ш
      correct: true
    - text: Л
      correct: false
    - text: Н
      correct: false
    - text: Д
      correct: false
  - question: Which type of consonant is М?
    explanation: М is a sonorant — one of the five musical consonants (Л, М, Н, Р,
      В) that are always voiced.
    options:
    - text: Sonorant (сонорний)
      correct: true
    - text: Voiced (дзвінкий)
      correct: false
    - text: Voiceless (глухий)
      correct: false
    - text: Always hard
      correct: false
  - question: What is the voiceless partner of З?
    explanation: З and С are a voiced/voiceless pair. Compare зуб (tooth) and суп
      (soup).
    options:
    - text: С
      correct: true
    - text: Ш
      correct: false
    - text: Х
      correct: false
    - text: Т
      correct: false
  - question: Ukrainian В sounds closest to which English sound?
    explanation: Ukrainian В is a sonorant — lips round softly, closer to English
      W. No teeth touch your lip.
    options:
    - text: W (as in water)
      correct: true
    - text: V (as in very)
      correct: false
    - text: B (as in boy)
      correct: false
    - text: F (as in fun)
      correct: false
  - question: Which letter represents the hard G sound (like English go)?
    explanation: Ґ (with an upturn) is the hard G. It is the rarest letter in the
      Ukrainian alphabet.
    options:
    - text: Ґ
      correct: true
    - text: Г
      correct: false
    - text: К
      correct: false
    - text: Х
      correct: false
  - question: Do voiced consonants become voiceless at the end of a Ukrainian word?
    explanation: No! Ukrainian voiced consonants stay voiced at word end. зуб is зу[б],
      not зу[п].
    options:
    - text: No — they stay voiced
      correct: true
    - text: Yes — they always devoice
      correct: false
    - text: Only before a pause
      correct: false
    - text: Only sonorants stay voiced
      correct: false
- type: classify
  title: Hard or Soft Consonant?
  instruction: 'In each word below, the highlighted consonant is either hard or soft.
    Remember: consonants become soft before І, Я, Ю, Є. Sort each word into the correct
    category.'
  categories:
  - label: Hard consonant
    items:
    - лук (Л before У)
    - зуб (З before У)
    - шапка (Ш — always hard)
    - жук (Ж — always hard)
  - label: Soft consonant
    items:
    - люк (Л before Ю)
    - ліс (Л before І)
    - сіль (С before І)
    - день (Д before Е+Ь)
- type: true-false
  title: True or False?
  instruction: Decide whether each statement about Ukrainian consonants is true or
    false.
  items:
  - statement: Ukrainian Р is pronounced like English P.
    correct: false
    explanation: Р looks like English P but is a completely different sound — a rolled,
      trilled R.
  - statement: Ukrainian В sounds closer to English W than English V.
    correct: true
    explanation: В is a sonorant — lips round softly, no teeth touch your lip.
  - statement: Б and П are a voiced/voiceless pair.
    correct: true
    explanation: Same lip position for both. Б is voiced (throat vibrates), П is voiceless
      (only air).
  - statement: Ukrainian Г sounds like a hard G as in English go.
    correct: false
    explanation: Г is a soft, throaty sound (voiced glottal fricative). The hard G
      sound is the rare letter Ґ.
  - statement: Sonorant consonants (Л, М, Н, Р, В) are always voiced.
    correct: true
    explanation: Sonorants never have voiceless partners — they are always voiced.
  - statement: In Ukrainian, voiced consonants become voiceless at the end of a word.
    correct: false
    explanation: Ukrainian voiced consonants stay voiced at word end. зуб is зу[б],
      never зу[п].
  - statement: Ж and Ш are always hard, even before the vowel І.
    correct: true
    explanation: Ж and Ш never soften. Even in жінка, the Ж stays hard.
  - statement: Й is always soft.
    correct: true
    explanation: Й is a short gliding sound (like Y in yes) and never has a hard variant.
- type: anagram
  title: Unscramble the Word
  instruction: Rearrange the letters to form a Ukrainian word from this lesson.
  items:
  - scrambled: б і х л
    answer: хліб
  - scrambled: к в о в
    answer: вовк
  - scrambled: а п ш к а
    answer: шапка
  - scrambled: б о н е
    answer: небо
  - scrambled: р а г о
    answer: гора
  - scrambled: а к у р
    answer: рука
  - scrambled: б у з
    answer: зуб
  - scrambled: п у с
    answer: суп

```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/consonant-sounds.yaml`

```yaml
items:
  - lemma: "хліб"
    translation: "bread"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Х; no-devoicing rule — хлі[б], not хлі[п]"
  - lemma: "зуб"
    translation: "tooth"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates З; no-devoicing drill pair with суп"
  - lemma: "дім"
    translation: "house"
    pos: "noun"
    gender: "m"
    notes: "High-frequency; demonstrates soft Д before І"
  - lemma: "вовк"
    translation: "wolf"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates В as sonorant; fairy-tale vocabulary"
  - lemma: "жук"
    translation: "beetle"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Ж; always-hard consonant"
  - lemma: "шапка"
    translation: "hat"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ш; always-hard consonant"
  - lemma: "гора"
    translation: "mountain"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Г (voiced glottal fricative, not hard G)"
  - lemma: "небо"
    translation: "sky"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates Н; high-frequency"
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
  - lemma: "сіль"
    translation: "salt"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates soft С and soft Л before Ь"
  - lemma: "люди"
    translation: "people"
    pos: "noun"
    notes: "Demonstrates soft Л before Ю; high-frequency"
  - lemma: "суп"
    translation: "soup"
    pos: "noun"
    gender: "m"
    notes: "Voiceless pair drill with зуб; everyday food"
  - lemma: "вода"
    translation: "water"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates В as sonorant (lips rounded, no teeth)"
  - lemma: "лук"
    translation: "onion"
    pos: "noun"
    gender: "m"
    notes: "Hard Л; minimal pair with люк"
  - lemma: "люк"
    translation: "hatch"
    pos: "noun"
    gender: "m"
    notes: "Soft Л before Ю; minimal pair with лук"
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates М and Л; review from Module 1"
  - lemma: "риба"
    translation: "fish"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Р (rolled/trilled); review from Module 1"
```

---

## Instructions

1. For each issue in the Fix Plan or audit failures, locate the exact text in the file contents above
2. Output a FIND/REPLACE pair with the exact text and the corrected version
3. Prioritize: **audit gate failures first**, then review issues
4. Only fix issues documented above — no silent extra changes
5. Maximum **15 FIND/REPLACE pairs** total

---

## Fix Rules

- Only fix issues documented in the Fix Plan or audit failures above
- You MAY add new activities or modify existing ones if the Fix Plan explicitly requests it
- Do NOT add new prose sections unless the Fix Plan explicitly requests it
- If nothing needs fixing, output an empty fix block
- FIND text must match the file contents EXACTLY (copy-paste from above)

---

## Output Format

You MUST use these exact delimiters:

```
===SECTION_FIX_START===
FILE: [filename]
FIND:
[exact text from the file — must match character-for-character]
REPLACE:
[corrected text]
---
FILE: [filename]
FIND:
[exact text]
REPLACE:
[corrected text]
---
[... more pairs, max 15 ...]
===SECTION_FIX_END===
```

If no fixes are needed:

```
===SECTION_FIX_START===
(No fixes needed — all issues resolved)
===SECTION_FIX_END===
```

After the fix block, output a friction report:

```
===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: {what you were doing}
**Friction Type**: NONE | TEXT_NOT_FOUND | ...
**Raw Error**: {actual issue or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write a review — that was already done
- Do NOT output ===REVIEW_START=== or ===FACTUAL_REVIEW_START=== blocks
- Do NOT use Edit tool or any other tool — you have NO tool access
- Output ONLY FIND/REPLACE pairs within the delimiters above
- Maximum 15 FIND/REPLACE pairs


============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 15 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=33211 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- # Gemini Review Fix: Targeted Repair via FIND/REPLACE  > **You are an expert Ukrainian language...
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/consonant-sounds.md
FIND:
- **лук** (onion) — hard Л, tongue stays low
REPLACE:
- **лук** (bow) — hard Л, tongue stays low
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/consonant-sounds.md
FIND:
- **лук** (onion) / **люк** (hatch) — hard Л vs soft Л
REPLACE:
- **лук** (bow) / **люк** (hatch) — hard Л vs soft Л
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/consonant-sounds.md
FIND:
- **зуб** / **суп** — feel the difference at the end: [б] stays voiced, [п] is voiceless
- **жук** / **ша́пка** — [ж] buzzes, [ш] hisses
- **гора́** / **хор** — [г] is soft and throaty, [х] is a voiceless whisper
REPLACE:
- **зуб** / **суп** — feel the difference at the end: Б stays voiced, П is voiceless
- **жук** / **ша́пка** — Ж buzzes, Ш hisses
- **гора́** / **хор** — Г is soft and throaty, Х is a voiceless whisper
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/consonant-sounds.yaml
FIND:
    explanation: No! Ukrainian voiced consonants stay voiced at word end. зуб is зу[б],
      not зу[п].
REPLACE:
    explanation: No! Ukrainian voiced consonants stay voiced at word end. зуб is зуб,
      not зуп.
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/consonant-sounds.yaml
FIND:
  - statement: In Ukrainian, voiced consonants become voiceless at the end of a word.
    correct: false
    explanation: Ukrainian voiced consonants stay voiced at word end. зуб is зу[б],
      never зу[п].
REPLACE:
  - statement: In Ukrainian, voiced consonants become voiceless at the end of a word.
    correct: false
    explanation: Ukrainian voiced consonants stay voiced at word end. зуб is зуб,
      never зуп.
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/consonant-sounds.yaml
FIND:
  - lemma: "хліб"
    translation: "bread"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Х; no-devoicing rule — хлі[б], not хлі[п]"
REPLACE:
  - lemma: "хліб"
    translation: "bread"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Х; no-devoicing rule — хліб, not хліп"
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/consonant-sounds.yaml
FIND:
  - lemma: "лук"
    translation: "onion"
    pos: "noun"
    gender: "m"
    notes: "Hard Л; minimal pair with люк"
REPLACE:
  - lemma: "лук"
    translation: "bow"
    pos: "noun"
    gender: "m"
    notes: "Hard Л; minimal pair with люк"
===SECTION_FIX_END===

===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: Applying FIND/REPLACE pairs
**Friction Type**: TEXT_NOT_FOUND
**Raw Error**: Issues 1 and 2 ("сі́р" -> "сі́к", and the incorrect claim about "Й" in "яйце́") were not found in the provided file contents. The text had already been corrected to "сі́к" and the "яйце́" claim was already removed. 
**Self-Correction**: I omitted creating FIND/REPLACE pairs for those two already-fixed issues to avoid failing the script search, and focused completely on the remaining bugs (phonetic brackets and the false friend translation).
**Proposed Tooling Fix**: N/A
===FRICTION_END===


────────────────────────────────────────
✅ Gemini finished (3265 chars)
✅ Message sent to Claude (ID: 26084)
✓ Message 26084 acknowledged
   Auto-acknowledged reply #26084 (stdout delivery — no inbox accumulation)
   📎 Review posted as new issue #928 (1 part)
✓ Message 26083 acknowledged

✅ Message sent to Gemini (ID: 26461) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #26461...
📨 Message #26461
   From: gemini → To: gemini
   Type: query
   Task: consonant-sounds-review-fix-1
   Time: 2026-03-17T23:06:21.710031+00:00

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

## Review Findings (targeted fix required)

**CONSTRAINTS:**
- Fix ONLY the issues listed below
- Do NOT rewrite surrounding text
- Preserve word count and structure
- Only modify these sections: Activities (`true-false`, statement 3 explanation), Section "Дзвінкі та глухі пари — Voiced and Voiceless Pairs" and "Підсумок — Summary", Section "Читання — Reading Practice"

### Finding 1: Banned IPA brackets used for pronunciation
**Location**: Section "Дзвінкі та глухі пари — Voiced and Voiceless Pairs" and "Підсумок — Summary"
**Problem**: The module uses banned phonetic brackets to explain pronunciation, triggering a HIGH severity `[IPA_BANNED]` violation. The text includes `do[k]`, `зу[б]`, `зу[п]`, `хлі[б]`, and `хлі[п]`.
**Required Fix**: Remove the brackets and use capitalized letters to emphasize the sound (e.g., "зуБ", "зуП").
**Severity**: HIGH

### Finding 2: Forbidden verb used in pre-verb module
**Location**: Section "Читання — Reading Practice"
**Problem**: The reading text includes the phrase `> — Дя́кую!`, which is a verb. Verbs are strictly forbidden before M15. This triggers a HIGH severity `[MORPHOLOGICAL_VIOLATION]`.
**Required Fix**: Remove the `> — Дя́кую!` line entirely to maintain beginner safety and grammar scope.
**Severity**: HIGH

### Finding 3: Incorrect stress on "молоко" (Repeated Friction)
**Location**: Section "Читання — Reading Practice"
**Problem**: The text contains the sentence `> — Мо́локо тут?` which has the stress incorrectly marked on the first syllable. The correct stress is `молоко́`. This is a direct repeat of a known friction constraint.
**Required Fix**: Correct the stress to `молоко́`.
**Severity**: HIGH

### Finding 4: Untaught vocabulary in reading drills
**Location**: Section "Читання — Reading Practice"
**Problem**: The reading drill includes the pair `**гора́** / **хор**`. The word `хор` is not in the vocabulary list and has not been introduced previously, violating pedagogical flow.
**Required Fix**: Remove the pair `**гора́** / **хор**`.
**Severity**: HIGH

### Finding 5: Banned IPA notation leaked into Activities
**Location**: Activities (`true-false`, statement 3 explanation)
**Problem**: The explanation text for the true/false question contains the same banned IPA brackets: `Зуб is зу[б], not зу[п].`
**Required Fix**: Update the explanation to remove the brackets, matching the fix in the main content.
**Severity**: HIGH

---

## Plan Adherence Issues (Deterministic — MUST FIX)

- **[HIGH] ACTIVITY_UNDERCOUNT** in `activity:classify`
  - Expected: Plan requires ≥15 items
  - Actual: Activity has 8 items
  - Fix: Add 7 more items to 'classify' activity


---

## Critical Issues Found

### Issue 1: Banned IPA brackets used for pronunciation
**Location**: Section "Дзвінкі та глухі пари — Voiced and Voiceless Pairs" and "Підсумок — Summary"
**Problem**: The module uses banned phonetic brackets to explain pronunciation, triggering a HIGH severity `[IPA_BANNED]` violation. The text includes `do[k]`, `зу[б]`, `зу[п]`, `хлі[б]`, and `хлі[п]`.
**Fix**: Remove the brackets and use capitalized letters to emphasize the sound (e.g., "зуБ", "зуП").

### Issue 2: Forbidden verb used in pre-verb module
**Location**: Section "Читання — Reading Practice"
**Problem**: The reading text includes the phrase `> — Дя́кую!`, which is a verb. Verbs are strictly forbidden before M15. This triggers a HIGH severity `[MORPHOLOGICAL_VIOLATION]`.
**Fix**: Remove the `> — Дя́кую!` line entirely to maintain beginner safety and grammar scope.

### Issue 3: Incorrect stress on "молоко" (Repeated Friction)
**Location**: Section "Читання — Reading Practice"
**Problem**: The text contains the sentence `> — Мо́локо тут?` which has the stress incorrectly marked on the first syllable. The correct stress is `молоко́`. This is a direct repeat of a known friction constraint.
**Fix**: Correct the stress to `молоко́`.

### Issue 4: Untaught vocabulary in reading drills
**Location**: Section "Читання — Reading Practice"
**Problem**: The reading drill includes the pair `**гора́** / **хор**`. The word `хор` is not in the vocabulary list and has not been introduced previously, violating pedagogical flow.
**Fix**: Remove the pair `**гора́** / **хор**`.

### Issue 5: Banned IPA notation leaked into Activities
**Location**: Activities (`true-false`, statement 3 explanation)
**Problem**: The explanation text for the true/false question contains the same banned IPA brackets: `Зуб is зу[б], not зу[п].`
**Fix**: Update the explanation to remove the brackets, matching the fix in the main content.

---

## Ukrainian Language Issues

- `Мо́локо тут?` — Incorrect stress. Must be `молоко́`.
- `> — Дя́кую!` — Morphological violation (verb used in M3).
- `**гора́** / **хор**` — Inclusion of out-of-scope vocabulary (`хор`).

---

## Fix Plan to Reach PASS

1. Remove all instances of `[` and `]` brackets used for phonetic spelling in both the main text and the activities.
2. Delete the `> — Дя́кую!` line from the reading practice dialogue.
3. Correct the stress mark on `Мо́локо` to `молоко́`.
4. Delete the `**гора́** / **хор**` bullet point from the Voiced/voiceless pair drills.

---

## Audit Failures (from automated re-audit)

```
--- STRICT GATES (Level A1) ---
❌ [GAMING_LANGUAGE_DETECTED] Review contains audit-gaming language: 'accurately reflect'. Reviews must HONESTLY evaluate content, not be written to 'ensure a high score'. REDO: DELETE the existing review file and regenerate from scratch. Run build_module_v5.py review phase (tier-1-beginner) using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence and stress mark, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.
❌ AUDIT FAILED. Correct errors before proceeding.
Critical Failures:
❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/consonant-sounds-audit.log for details)
⚠️  RAG verification found unverified words (see audit report)
--- STATUS JSON GATE BLOCKERS ---
GATE BLOCKER: Review contains audit-gaming language: 'accurately reflect'. Reviews must HONESTLY evaluate content, not be written to 'ensure a high score'. REDO: DELETE the existing review file and regenerate from scratch. Run build_module_v5.py review phase (tier-1-beginner) using claude_extensions/commands/review-tiers/tier-1-beginner.md. Do NOT patch the existing review — start fresh. You MUST: (1) read every line of the .md and activities .yaml, (2) check every English explanation is B1-readable and encouraging, (3) verify every Ukrainian sentence and stress mark, (4) apply the 'Would I Continue?' test from the tier-1 guide, (5) score each dimension honestly and list at least 1 real issue.
--- VESUM WORD VERIFICATION FAILURES ---
These words were NOT found in the VESUM morphological dictionary.
Check if they are valid Ukrainian forms. Fix misspellings or Russianisms.
  ❌ `ДЖ` (source: prose)
  ❌ `ДЗ` (source: prose)
  ❌ `зу` (source: prose)
  ❌ `хлі` (source: prose)
```

---

## File Contents

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/consonant-sounds.md`

```markdown
## Вступ — Introduction

You already know the full Ukrainian alphabet from Module 1, and in Module 2 you mastered all 10 vowels — the open, pure sounds that form the backbone of every Ukrainian word. Now it's time for the other side of the sound system: the 22 consonant letters.

Today you'll learn how Ukrainian organizes its consonants into three groups: the musical sonorants, the voiced and voiceless pairs, and the hard versus soft distinction. You'll also discover one rule that makes Ukrainian pronunciation different from many other European languages.

> [!tip] Quick win
> You already know several consonants from Module 1 — **М**, **Н**, **Л**, **К**, **Т**, **С**. Today you'll see how they fit into the bigger picture.

## Сонорні — Sonorant Consonants

Ukrainian has five special consonants called sonorants: **Л**, **М**, **Н**, **Р**, and **В**. These are the «musical» consonants — when you say them, your voice dominates over noise. Think of them as the singing members of the consonant family. Unlike other consonants, sonorants have no voiceless partner.

You already met **М**, **Н**, and **Л** in Module 1, in words like **ма́ма**, **ніс**, and **ліс**. Let's revisit them briefly and then meet the two new sonorants.

### Літера М

You know this one well! **М** sounds like English M.

**Watch:** [Літера М — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=Ez95H4ibuJo)

### Літера Н

**Н** looks like English H but sounds like N. Your new word: **не́бо** (sky).

**Watch:** [Літера Н — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=vNUfiKHPYaU)

### Літера Л

**Л** sounds like L. You saw it in **ліс** and **молоко́**. It can be hard or soft — more on that later in this module.

**Watch:** [Літера Л — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=v6-3Xg52Buk)

### Літера Р

Here's your first real challenge! **Р** is the rolled, trilled R — your tongue tip vibrates against the ridge behind your upper teeth. It looks like English P but sounds completely different!

- **ри́ба** (fish)
- **рука́** (hand)

Don't worry if you can't roll it perfectly yet — many learners need weeks of practice. Keep your tongue tip light and relaxed, just behind your upper teeth.

**Watch:** [Літера Р — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=fMGsQ5KPQgg)

### Літера Й

**Й** is always soft — it sounds like the Y in «yes.» You'll hear it at the end of words and between vowels.

**Watch:** [Літера Й — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=aq0cjB90s3w)

### Літера В

**В** surprises many English speakers. In Ukrainian, **В** is a sonorant — closer to English W than English V. Your lips round together; your teeth do NOT touch your lower lip.

- **вода́** (water)
- **вовк** (wolf)

Listen carefully — they sound almost like «woda» and «wowk» to English ears.

**Watch:** [Літера В — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=aFcvYfvQ2X4)

> [!practice] Try it now
> Say these sonorant words out loud: **ма́ма**, **не́бо**, **ліс**, **ри́ба**, **вода́**. Notice how your voice carries smoothly through each consonant — no hissing, no hard stop, just flowing sound.

## Дзвінкі та глухі пари — Voiced and Voiceless Pairs

Most Ukrainian consonants come in pairs: one voiced (дзвінки́й), one voiceless (глухи́й). The difference? Place your hand on your throat and say a sound. When you say a voiced consonant, you feel vibration. When you say a voiceless one — only air, no buzz.

Each pair uses the exact same mouth position. The only difference is whether your vocal cords vibrate. Let's go through all six pairs.

<!-- adapted from: Bolshakova, Grade 2, p. 62 — voiced formed with voice + noise, voiceless with noise only -->

### Літери Б і П

**Б** is voiced, **П** is voiceless. Both are made by pressing your lips together and releasing a burst of air.

- **Б** — **бабу́ся** (grandma)
- **П** — **паву́к** (spider)

Try it: say **Б**... **П**... **Б**... **П**. Your lips do the same thing. Only the throat vibration changes.

**Watch:** [Літера Б — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=V1hxBE_JbGg)
**Watch:** [Літера П — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=JksSjjxyW5Y)

### Літери Д і Т

**Д** is voiced, **Т** is voiceless. Your tongue touches the ridge behind your upper teeth for both.

- **Д** — **дім** (house)
- **Т** — **та́то** (dad — you know this from Module 1!)

**Watch:** [Літера Д — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=g4Bh-lqzd48)
**Watch:** [Літера Т — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=m-jcLR_gK0k)

### Літери З і С

**З** is voiced, **С** is voiceless. Both direct air through a narrow gap near your upper teeth.

- **З** — **зуб** (tooth)
- **С** — **суп** (soup)

These two words make a perfect practice pair — **зуб** and **суп**. Same short structure, opposite voicing on the first consonant.

**Watch:** [Літера З — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=BhASNxitC1A)
**Watch:** [Літера С — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=7UsFBgSL91E)

### Літери Ж і Ш

**Ж** is voiced — like the sound in the middle of English «measure.» **Ш** is voiceless — like English «sh» in «shop.»

- **Ж** — **жук** (beetle)
- **Ш** — **ша́пка** (hat)

**Watch:** [Літера Ж — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=dIrGVcqPwqM)
**Watch:** [Літера Ш — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=1D-6MIw3OXY)

### Літери Г і Х

This pair catches every English speaker! **Г** is NOT a hard «g» like in English «go.» It's a soft, breathy, throaty sound — a voiced glottal fricative. **Х** is its voiceless partner — like the «ch» in Scottish «loch» or German «ach.»

- **Г** — **гора́** (mountain)
- **Х** — **хліб** (bread)

**Watch:** [Літера Г — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=gVnclpSI0DU)
**Watch:** [Літера Х — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=vpr58zJSJKc)

### Літери Ґ і К

So where IS the hard «g» sound, like in English «go»? That belongs to **Ґ** — the rarest letter in the Ukrainian alphabet, found in only about 400 native Ukrainian words. It was removed from the alphabet in 1933 and restored in 1990. Its voiceless partner is **К**, which you already know from **кіт**.

- **Ґ** — **ґа́нок** (porch)
- **К** — **кіт** (cat — Module 1 review)

**Watch:** [Літера К — Anna Ohoiko, Ukrainian Lessons](https://www.youtube.com/watch?v=J7sGEI4-xJo)

> [!warning] The no-devoicing rule — this is important!
> In English, Russian, and German, voiced consonants go quiet at the end of a word — English speakers say «doK» for «dog.» Ukrainian is different. **Voiced consonants stay voiced at the end of a word!**
>
> - **зуб** = зу**Б**, NOT зуП
> - **хліб** = хлі**Б**, NOT хліП
>
> Practice saying **зуб** and **хліб** with a clear, buzzing final consonant. This is one of the features that gives Ukrainian its distinctive sound.

Here is a micro-dialogue to practice — read it out loud:

> — Це хліб?
> — Так, це хліб.
> — А це суп?
> — Так, суп тут.

## Тверді та м'які — Hard and Soft Consonants

Ukrainian consonants have one more important feature: most of them come in hard (тверди́й) and soft (м'яки́й) variants. A hard consonant is your «default» pronunciation. A soft (palatalized) consonant has a subtle «y» quality added — your tongue shifts up toward the roof of your mouth.

How does a consonant become soft? It softens before the vowels **І**, **Я**, **Ю**, **Є**, or when followed by **Ь** (the soft sign — coming in Module 4).

<!-- adapted from: Bolshakova, Grade 2, p. 43 — soft consonants marked by і, я, ю, є and ь -->

Look at these examples where consonants are soft:

- **ліс** (forest) — soft **Л** before **І**
- **день** (day) — soft **Д** and soft **Н** before **Ь**
- **сіль** (salt) — soft **С** before **І**, soft **Л** before **Ь**
- **лю́ди** (people) — soft **Л** before **Ю**

Now compare this minimal pair — the same letters, but one sound changes everything:

- **лук** (bow, the weapon) — hard **Л** before **У**
- **люк** (hatch) — soft **Л** before **Ю**

The consonant changes quality, not the vowel! This single shift in the **Л** changes the meaning completely. Here is another pair you already know:

- **дим** (smoke) — hard **Д** before **И**
- **дім** (house) — soft **Д** before **І**

You'll meet more pairs like these as your vocabulary grows. For now, just notice: the vowel letter after a consonant tells you whether it's hard or soft.

> [!note] Always hard, always soft
> **Ж** and **Ш** are always hard — they never soften, no matter what vowel follows. **Й** is always soft. You'll learn about the soft sign **Ь** (which forces softening on other consonants) in Module 4.

A short dialogue with hard and soft sounds:

> — Це ліс?
> — Так, це ліс.
> — А це дім?
> — Ні, це не дім. Це гора́.

## Читання — Reading Practice

Time to put everything together! Read these words out loud. Pay attention to each consonant — is it a sonorant? Voiced or voiceless? Hard or soft?

**Sonorant words:**

- **Не́бо. Вода́. Рука́. Ри́ба. Вовк. Молоко́.**

**Voiced/voiceless pair drills** — read each pair and feel the difference:

- **зуб** / **суп**
- **жук** / **ша́пка**
- **бабу́ся** / **паву́к**

**Hard/soft minimal pairs:**

- **лук** / **люк**
- **дим** / **дім**

Now try reading these phrases and mini-conversations:

> — Це хліб і сіль.
> — Дя́кую!

> — Молоко́ тут?
> — Ні, молоко́ там.

> — Це жук?
> — Ні, це паву́к!

A few more words to read — every consonant type is here: **ма́ма, та́то, кіт, ліс, дім, не́бо, рука́, вовк, хліб, сіль, лю́ди, гора́, ґа́нок, жук, ша́пка, цибу́ля.**

> [!challenge] Reading challenge
> Read the full list above without stopping. Then go back and identify: which words start with a sonorant? Which start with a voiced consonant? Which start with a voiceless consonant?

## Підсумок — Summary

You've just learned the entire Ukrainian consonant system — great work! Here's what you now know:

- **5 sonorants**: Л, М, Н, Р, В — the «musical» consonants with no voiceless partner
- **6 voiced/voiceless pairs**: Б/П, Д/Т, З/С, Ж/Ш, Г/Х, Ґ/К
- **Hard and soft variants**: consonants soften before І, Я, Ю, Є, or Ь
- **The no-devoicing rule**: voiced consonants stay voiced at word end — **зуб** is зуБ, never зуП

**Self-check — can you answer these?**

1. What are the 5 sonorants?
2. What is the voiceless partner of **Б**?
3. Is **Г** a hard «g» or a soft, throaty sound?
4. Do voiced consonants become voiceless at the end of a word in Ukrainian?
5. What makes **лук** and **люк** sound different?

If you got all five — you're ready for the next step. **Coming next:** Module 4 completes the alphabet — the soft sign (**Ь**), the apostrophe, affricates (**Ц**, **Ч**, **Щ**), digraphs (**ДЖ**, **ДЗ**), and the rare **Ф**.
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/consonant-sounds.yaml`

```yaml
- type: watch-and-repeat
  title: Hear and Repeat Consonant Pairs
  instruction: Watch each video, then repeat the letter and example word out loud.
    Focus on the voiced/voiceless difference in each pair.
  items:
  - letter: Б
    word: бабуся
    video: https://www.youtube.com/watch?v=V1hxBE_JbGg
    note: Voiced — feel your throat vibrate
  - letter: П
    word: павук
    video: https://www.youtube.com/watch?v=JksSjjxyW5Y
    note: Voiceless partner of Б — same lips, no vibration
  - letter: Д
    word: дім
    video: https://www.youtube.com/watch?v=g4Bh-lqzd48
    note: Voiced — tongue on the ridge behind upper teeth
  - letter: Т
    word: тато
    video: https://www.youtube.com/watch?v=m-jcLR_gK0k
    note: Voiceless partner of Д
  - letter: З
    word: зуб
    video: https://www.youtube.com/watch?v=BhASNxitC1A
    note: Voiced — air through a narrow gap, throat buzzes
  - letter: С
    word: суп
    video: https://www.youtube.com/watch?v=7UsFBgSL91E
    note: Voiceless partner of З — same position, no buzz
  - letter: Ж
    word: жук
    video: https://www.youtube.com/watch?v=dIrGVcqPwqM
    note: Voiced — like the sound in English measure
  - letter: Ш
    word: шапка
    video: https://www.youtube.com/watch?v=1D-6MIw3OXY
    note: Voiceless partner of Ж — like English sh
  - letter: Г
    word: гора
    video: https://www.youtube.com/watch?v=gVnclpSI0DU
    note: Voiced — soft, breathy throat sound, NOT like English g
  - letter: Х
    word: хліб
    video: https://www.youtube.com/watch?v=vpr58zJSJKc
    note: Voiceless partner of Г — like ch in Scottish loch
  - letter: К
    word: кіт
    video: https://www.youtube.com/watch?v=J7sGEI4-xJo
    note: Voiceless partner of the rare Ґ
  - letter: В
    word: вода
    video: https://www.youtube.com/watch?v=aFcvYfvQ2X4
    note: Sonorant — closer to English W than V, lips rounded
- type: classify
  title: Sort the Consonants
  instruction: Drag each consonant letter into the correct category. Sonorants are
    the musical consonants. Voiced consonants make your throat vibrate. Voiceless
    consonants use only air.
  categories:
  - label: Sonorants
    symbol_hint: sonorant
    items:
    - Л
    - М
    - Н
    - Р
    - В
  - label: Voiced
    symbol_hint: voiced
    items:
    - Б
    - Д
    - З
    - Ж
    - Г
  - label: Voiceless
    symbol_hint: voiceless
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
  - emoji: 🪲
    answer: Ж
    distractors:
    - З
    - Ш
    - Г
    note: жук (beetle)
  - emoji: 🧢
    answer: Ш
    distractors:
    - Ж
    - С
    - Х
    note: шапка (hat)
  - emoji: ✋
    answer: Р
    distractors:
    - Л
    - Н
    - М
    note: рука (hand)
  - emoji: 🐺
    answer: В
    distractors:
    - Б
    - Г
    - Р
    note: вовк (wolf)
  - emoji: 🏔️
    answer: Г
    distractors:
    - Х
    - К
    - Ґ
    note: гора (mountain)
  - emoji: 🍞
    answer: Х
    distractors:
    - Г
    - К
    - Ш
    note: хліб (bread)
  - emoji: 🏠
    answer: Д
    distractors:
    - Т
    - Б
    - Г
    note: дім (house)
  - emoji: 🕷️
    answer: П
    distractors:
    - Б
    - Т
    - К
    note: павук (spider)
- type: match-up
  title: Match Voiced to Voiceless Partner
  instruction: Each voiced consonant has a voiceless partner. Match them up — they
    use the same mouth position, but one vibrates and the other doesn't.
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
  instruction: Choose the correct answer for each question.
  items:
  - question: Place your hand on your throat and say Б. What do you feel?
    options:
    - text: Vibration — Б is voiced
      correct: true
    - text: Nothing — Б is voiceless
      correct: false
    - text: Vibration — Б is voiceless
      correct: false
    - text: Nothing — Б is a sonorant
      correct: false
    explanation: Б is a voiced consonant. Your vocal cords vibrate when you say it.
  - question: What is the voiceless partner of Д?
    options:
    - text: Т
      correct: true
    - text: П
      correct: false
    - text: С
      correct: false
    - text: К
      correct: false
    explanation: Д and Т are a voiced/voiceless pair. Both use the same tongue position
      on the ridge behind your upper teeth.
  - question: The Ukrainian letter Г sounds like...
    options:
    - text: A soft, breathy throat sound (voiced fricative)
      correct: true
    - text: A hard g like in English go
      correct: false
    - text: The English letter H
      correct: false
    - text: The ch in English cheese
      correct: false
    explanation: Г is a voiced glottal fricative — soft and throaty. The hard g sound
      belongs to the rare letter Ґ.
  - question: What happens to voiced consonants at the end of a Ukrainian word?
    options:
    - text: They stay voiced
      correct: true
    - text: They become voiceless
      correct: false
    - text: They disappear
      correct: false
    - text: They become soft
      correct: false
    explanation: Unlike English, Russian, or German, Ukrainian keeps voiced consonants
      voiced at word end. Зуб is зу[б], not зу[п].
  - question: Which of these is a sonorant consonant?
    options:
    - text: Р
      correct: true
    - text: Б
      correct: false
    - text: Ж
      correct: false
    - text: К
      correct: false
    explanation: The 5 sonorants are Л, М, Н, Р, В. They are the musical consonants
      where voice dominates over noise.
  - question: The letter Р looks like English P but sounds like...
    options:
    - text: A rolled, trilled R
      correct: true
    - text: The English P sound
      correct: false
    - text: The English B sound
      correct: false
    - text: A soft H sound
      correct: false
    explanation: Р is a visual trap — it looks like P but is a rolled R. Your tongue
      tip vibrates against the ridge behind your upper teeth.
  - question: Which consonant pair shows the same mouth position but different voicing?
    options:
    - text: З and С
      correct: true
    - text: Л and Р
      correct: false
    - text: М and В
      correct: false
    - text: Н and Й
      correct: false
    explanation: З (voiced) and С (voiceless) are a true pair — identical mouth position,
      only the throat vibration differs.
  - question: Why is В called a sonorant in Ukrainian?
    options:
    - text: Voice dominates — it sounds closer to English W than V
      correct: true
    - text: It is always voiceless
      correct: false
    - text: It has a voiceless partner
      correct: false
    - text: It is always hard
      correct: false
    explanation: Ukrainian В is a sonorant — your lips round together (like W), and
      voice carries through. It has no voiceless partner.
  - question: Which letter represents the hard g sound (like English go)?
    options:
    - text: Ґ
      correct: true
    - text: Г
      correct: false
    - text: К
      correct: false
    - text: Х
      correct: false
    explanation: Ґ is the rare letter for the hard g sound. It was removed in 1933
      and restored in 1990. Г is a soft, throaty sound instead.
  - question: Which pair of words can you use to practice the З/С voicing difference?
    options:
    - text: зуб / суп
      correct: true
    - text: жук / шапка
      correct: false
    - text: дім / кіт
      correct: false
    - text: небо / вода
      correct: false
    explanation: Зуб and суп have the same short structure. The first consonant is
      voiced (З) in зуб and voiceless (С) in суп.
- type: classify
  title: Hard or Soft?
  instruction: 'Look at each word and decide whether the highlighted consonant is
    hard or soft. Remember: consonants soften before І, Я, Ю, Є.'
  categories:
  - label: Hard consonant
    symbol_hint: hard
    items:
    - лук (Л before У)
    - дим (Д before И)
    - зуб (З before У)
    - суп (С before У)
  - label: Soft consonant
    symbol_hint: soft
    items:
    - ліс (Л before І)
    - дім (Д before І)
    - сіль (С before І)
    - люди (Л before Ю)
- type: true-false
  title: True or False?
  instruction: Decide whether each statement about Ukrainian consonants is true or
    false.
  items:
  - statement: The Ukrainian letter Н makes the same sound as English H.
    correct: false
    explanation: Н looks like H but sounds like N — it is a visual trap for English
      speakers.
  - statement: Ukrainian has 5 sonorant consonants.
    correct: true
    explanation: The 5 sonorants are Л, М, Н, Р, В — the musical consonants.
  - statement: In Ukrainian, voiced consonants become voiceless at the end of a word.
    correct: false
    explanation: Ukrainian keeps voiced consonants voiced at word end. Зуб is зуБ,
      not зуП. This is different from English, Russian, and German.
  - statement: Б and П use the same mouth position — the only difference is throat
      vibration.
    correct: true
    explanation: Both are made by pressing your lips together. Б is voiced (throat
      vibrates), П is voiceless (no vibration).
  - statement: The letter Ґ was removed from the Ukrainian alphabet in 1933 and restored
      in 1990.
    correct: true
    explanation: Ґ represents the hard g sound (like English go) and is found in only
      about 400 native Ukrainian words.
  - statement: Ukrainian В sounds just like English V — teeth touch the lower lip.
    correct: false
    explanation: Ukrainian В is a sonorant, closer to English W. Your lips round together;
      your teeth do NOT touch your lower lip.
  - statement: Ж and Ш are always hard — they never soften.
    correct: true
    explanation: No matter what vowel follows, Ж and Ш stay hard. Й, on the other
      hand, is always soft.
  - statement: The word дім has a soft Д because it comes before І.
    correct: true
    explanation: Consonants soften before І, Я, Ю, Є. In дім, the Д before І is soft.
      Compare with дим (hard Д before И).
- type: anagram
  title: Unscramble the Word
  instruction: Rearrange the letters to form a Ukrainian word from the lesson.
  items:
  - scrambled: б у з
    answer: зуб
  - scrambled: м і д
    answer: дім
  - scrambled: п у с
    answer: суп
  - scrambled: к у ж
    answer: жук
  - scrambled: б і л х
    answer: хліб
  - scrambled: а д о в
    answer: вода

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
    notes: "Soft Д before І; minimal pair with дим (smoke)"
  - lemma: "вовк"
    translation: "wolf"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates В (sonorant); Ukrainian folk tale vocabulary"
  - lemma: "жук"
    translation: "beetle"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates Ж (voiced sibilant)"
  - lemma: "шапка"
    translation: "hat"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Ш (voiceless partner of Ж)"
  - lemma: "гора"
    translation: "mountain"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Г (voiced glottal fricative, not hard g)"
  - lemma: "небо"
    translation: "sky"
    pos: "noun"
    gender: "n"
    notes: "Demonstrates Н (looks like H, sounds like N)"
  - lemma: "рука"
    translation: "hand"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Р (rolled/trilled R)"
  - lemma: "бабуся"
    translation: "grandma"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Б (voiced); high-frequency family word"
  - lemma: "павук"
    translation: "spider"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates П (voiceless partner of Б)"
  - lemma: "ґанок"
    translation: "porch"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates rare Ґ (hard g sound); classic textbook word"
  - lemma: "сіль"
    translation: "salt"
    pos: "noun"
    gender: "f"
    notes: "Soft С before І, soft Л before Ь"
  - lemma: "люди"
    translation: "people"
    pos: "noun"
    gender: "pl"
    notes: "Soft Л before Ю; plural-only noun"
  - lemma: "суп"
    translation: "soup"
    pos: "noun"
    gender: "m"
    notes: "Voiceless С; drill pair with зуб"
  - lemma: "вода"
    translation: "water"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates В (sonorant, closer to W)"
  - lemma: "цибуля"
    translation: "onion"
    pos: "noun"
    gender: "f"
    notes: "Hard Л before Я; everyday kitchen word"
  - lemma: "люк"
    translation: "hatch"
    pos: "noun"
    gender: "m"
    notes: "Soft Л before Ю; minimal pair with лук (bow)"
  - lemma: "риба"
    translation: "fish"
    pos: "noun"
    gender: "f"
    notes: "Demonstrates Р (rolled/trilled R)"
  - lemma: "кіт"
    translation: "cat"
    pos: "noun"
    gender: "m"
    notes: "Demonstrates К (voiceless partner of Ґ); Module 1 review word"
```

---

## Friction Constraints (Past Review Findings — DO NOT reintroduce)

FRICTION CONSTRAINTS (from past build reviews — DO NOT repeat these errors):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [MODULE] False textbook attribution: module claims "Ukrainian textbooks teach a hand-on-throat test" for voicing. The actual textbook (Кравцова 2019, Grade 2, p.39) teaches covering ears with palms. Keep the hand-on-throat technique (plan mandates it) but remove the false attribution to textbooks.
- [MODULE] Plan requires explicit Russian comparison for voiced consonants at word end: "Different from Russian". Module substituted "English, German, and many other languages" instead. Must mention Russian as the plan specifies.
- [MODULE] Wrong stress on 4 words: моло́ко→молоко́, дзві́нкий→дзвінки́й, глу́хий→глухи́й, тве́рдий→тверди́й.
- [MODULE] Review file missing required Scores/Assessment and Issues/Critique sections. Needs full redo with tier-1-beginner review template.

---

## Instructions

**CRITICAL: Fix ALL issues. Partial fixes are REJECTED. Count your fixes — if you missed one, go back.**

1. For EVERY issue in the Fix Plan AND audit failures, locate the exact text in the file contents above
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
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=37208 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- # Gemini Review Fix: Targeted Repair via FIND/REPLACE  > **You are an expert Ukrainian language...
===SECTION_FIX_START===
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/consonant-sounds.md
FIND:
> — Це хліб і сіль.
> — Дя́кую!

> — Мо́локо тут?
> — Ні, молоко́ там.
REPLACE:
> — Це хліб і сіль.

> — Молоко́ тут?
> — Ні, молоко́ там.
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/consonant-sounds.yaml
FIND:
    explanation: Unlike English, Russian, or German, Ukrainian keeps voiced consonants
      voiced at word end. Зуб is зу[б], not зу[п].
REPLACE:
    explanation: Unlike English, Russian, or German, Ukrainian keeps voiced consonants
      voiced at word end. Зуб is зуБ, not зуП.
---
FILE: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/consonant-sounds.yaml
FIND:
  - label: Hard consonant
    symbol_hint: hard
    items:
    - лук (Л before У)
    - дим (Д before И)
    - зуб (З before У)
    - суп (С before У)
  - label: Soft consonant
    symbol_hint: soft
    items:
    - ліс (Л before І)
    - дім (Д before І)
    - сіль (С before І)
    - люди (Л before Ю)
REPLACE:
  - label: Hard consonant
    symbol_hint: hard
    items:
    - лук (Л before У)
    - дим (Д before И)
    - зуб (З before У)
    - суп (С before У)
    - вовк (В before О)
    - рука (Р before У)
    - жук (Ж is always hard)
    - гора (Г before О)
  - label: Soft consonant
    symbol_hint: soft
    items:
    - ліс (Л before І)
    - дім (Д before І)
    - сіль (С before І)
    - люди (Л before Ю)
    - кіт (К before І)
    - бабуся (С before Я)
    - цибуля (Л before Я)
===SECTION_FIX_END===

===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: Applying FIND/REPLACE fixes
**Friction Type**: TEXT_NOT_FOUND
**Raw Error**: Issue 1 (IPA brackets `do[k]`, `зу[б]` in prose) and Issue 4 (`**гора́** / **хор**`) were not found in the provided markdown file. They appear to have already been resolved in a prior step.
**Self-Correction**: Skipped the missing text replacements for the markdown file and focused on fixing the remaining active issues (stress on молоко, verb removal, activities classify undercount, and the single IPA bracket instance left in the activities yaml).
**Proposed Tooling Fix**: N/A
===FRICTION_END===


────────────────────────────────────────
✅ Gemini finished (2234 chars)
✅ Message sent to Claude (ID: 26464)
✓ Message 26464 acknowledged
   Auto-acknowledged reply #26464 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'consonant-sounds-review-fix-1' — skipping GH posting (review saved to orchestration/)
✓ Message 26461 acknowledged

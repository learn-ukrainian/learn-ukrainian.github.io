✅ Message sent to Gemini (ID: 20745) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #20745...
📨 Message #20745
   From: gemini → To: gemini
   Type: query
   Task: the-cyrillic-code-iv-review-fix-1
   Time: 2026-03-05T19:33:43.872043+00:00

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

### Issue 1: Incorrect Alphabet Sequence
**Location**: Section `Підсумок: Весь алфавіт — The Full Alphabet`
**Problem**: The complete sequence of the Ukrainian alphabet is missing the letter **І** and lists the letter **Й** twice: `А Б В Г Ґ Д Е Є Ж З И Й Ї Й К...`
**Fix**: Correct the sequence to `А Б В Г Ґ Д Е Є Ж З И І Ї Й К...`

### Issue 2: Pedagogical Contradiction regarding Ї
**Location**: Section `Йотовані голосні — Iotated Vowels Я, Ю, Є, Ї, Й`
**Problem**: The text introduces Ї as having a "dual nature" ("Four of these letters — **Я**, **Ю**, **Є**, and **Ї** — have a unique «dual nature».") but in the very next paragraph says "The letter **Ї** is the strict exception to the dual nature rule... It ALWAYS makes two sounds". This is highly confusing for a beginner.
**Fix**: Exclude Ї from the "dual nature" group in the introduction, clarifying that only Я, Ю, and Є have a dual nature, while Ї has a strict single rule.

### Issue 3: Massive Untranslated Word Dump
**Location**: Section `Практика читання — Reading Practice`
**Problem**: The module presents over 80 Ukrainian words (e.g., `мама, тато, син, дочка, брат, сестра, дід, баба, хлопець...`) without English translations. This violates beginner safety and the pre-screen flagged them as `[UNTRANSLATED_NON_DECODABLE]`.
**Fix**: Dramatically reduce the reading practice lists and provide English translations for every word to prevent cognitive overload.

### Issue 4: Vocabulary and Activity Mismatch
**Location**: Section `Йотовані голосні — Iotated Vowels Я, Ю, Є, Ї, Й` vs `Activities` and `Vocabulary`
**Problem**: The lesson text uses `Європа` as the example for the letter **Є**. However, the `watch-and-repeat` activity and the vocabulary list use `єнот`. `єнот` is never introduced in the lesson text, and `Європа` is missing from the vocabulary list.
**Fix**: Standardize the example. Given the cultural callout for `Європа`, change the activity and vocabulary list to use `Європа` instead of `єнот`.

---

## Ukrainian Language Issues

- The alphabet sequence string `А Б В Г Ґ Д Е Є Ж З И Й Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я` is fundamentally incorrect for the Ukrainian language.

---

## Fix Plan to Reach 9.0+

1. Correct the alphabet sequence string to include 'І' and remove the duplicate 'Й'.
2. Rewrite the introduction to the iotated vowels to separate 'Ї' from the "dual nature" concept entirely.
3. Trim the `Практика читання` section to 3-5 words per category and add English translations in parentheses.
4. Sync the vocabulary list and the `watch-and-repeat` activity to use `Європа` instead of `єнот`.

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
failing gates:
lesson: 1444/1200 (raw: 1733) | immersion: 4.6% LOW (target 10-25% (M04))
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-iv-audit.log for details)
```

---

## File Contents

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-iv.md`

```markdown
<!-- SCOPE
Covers: The final 10 letters of the alphabet (Й, Щ, Я, Ю, Є, Ь, Ї, Ц, Ф, Ґ), digraphs ДЖ/ДЗ, and the apostrophe.
Not covered:
  - Syllables and Word Division → a1-05
-->

# The Cyrillic Code IV

> **Why does this matter?**
>
> You are incredibly close to a major milestone. Mastering the complete Cyrillic alphabet unlocks your ability to read any Ukrainian text natively.

## Вступ — Introduction

Welcome back! You already know twenty-three letters of the Ukrainian alphabet. That is an amazing achievement. We have only ten final letters, two special letter combinations, and one unique symbol left to cover. The finish line is truly in sight. Once you complete this module, you will have cracked the entire Cyrillic code, and every single Ukrainian word will be decodable for you. 

Before we dive into the final set, let us do a quick diagnostic check. Try reading these five words out loud. They use only the letters you have already mastered:

| Word | Meaning |
|------|---------|
| **ма́ма** | mom |
| **брат** | brother |
| **сестра́** | sister |
| **дім** | house |
| **кіт** | cat |

Were you able to read them? Excellent! For this final stage, the explanations about the new letters will be entirely in English, while the examples will be in Ukrainian. Let us learn the final pieces of the puzzle and complete your alphabet journey!

## Злиті звуки та рідкісні букви — Affricates, Digraphs & Ґ (hard G)

Let us start with some unique letters. The Ukrainian alphabet has characters that combine two distinct sounds into a single crisp burst. We also have combinations of two letters that make one unified sound.

First, meet **Ц** (ts). This letter is an affricate, which means it is pronounced as a single, quick sound. It sounds exactly like the «ts» at the end of the English word «cats». Your brain might want to read it as two separate consonants, but in Ukrainian, it is always a unified sound.

[Anna Ohoiko — Ukrainian Lessons — Ц](https://www.youtube.com/watch?v=u44eCjR2Oz8)

| Word | Meaning |
|------|---------|
| **це́нтр** | center |

Next is **Щ**. This is a uniquely Ukrainian letter that represents two sounds spoken at once. It is a double sound, merging the sound of English «sh» with the sound of «ch». It is much stronger than **Ш**, which is just a single sound.

[Anna Ohoiko — Ukrainian Lessons — Щ](https://www.youtube.com/watch?v=QmBLieIuf6Q)

| Word | Meaning |
|------|---------|
| **ще** | more, still |
| **ща́стя** | happiness |

Now let us look at **Ф**. This letter sounds just like the English letter «f». You will rarely see it in native Ukrainian vocabulary. It appears mostly in words borrowed from other languages.

[Anna Ohoiko — Ukrainian Lessons — Ф](https://www.youtube.com/watch?v=haHRsFFZRQI)

| Word | Meaning |
|------|---------|
| **факт** | fact |

Ukrainian also uses two digraphs. A digraph is a pair of letters that creates one single sound.
The first is **ДЖ**. This combination sounds like the «j» in the English word «jungle». 

| Word | Meaning |
|------|---------|
| **джаз** | jazz |

The second digraph is **ДЗ**. There is no exact English equivalent for this sound, but it is similar to the buzzing noise you make if you say the letters «d» and «z» very quickly together.

| Word | Meaning |
|------|---------|
| **дзвін** | bell |

Finally, we have the letter **Ґ** (hard G). This is the hard sound, just like the «g» in the English word «go». It is extremely rare and only appears in a few hundred native words.

[Anna Ohoiko — Ukrainian Lessons — Ґ (hard G)](https://www.youtube.com/watch?v=gNjHqjTW9WQ)

| Word | Meaning |
|------|---------|
| **ґа́нок** | porch |

> [!history-bite]
> Ukrainians know the letter **Ґ** (hard G) as the repressed letter. Soviet authorities officially removed it from the Ukrainian alphabet in 1933, and the independent government only restored it in 1990!

## Йотовані голосні — Iotated Vowels Я, Ю, Є, Ї, Й

The next group of letters is fascinating. We call them iotated vowels. Three of these letters — **Я**, **Ю**, and **Є** — have a unique «dual nature», while **Ї** has its own strict rule.

What does «dual nature» mean? At the beginning of a word, or after another vowel, these letters represent two sounds: the consonant sound of English «y» plus a vowel. However, when they appear right after a consonant, they only make their vowel sound, but they do something very special: they soften the consonant that comes before them.

Let us explore them one by one.

The letter **Я** represents a sound similar to the beginning of the English word «yard». It is a very high-frequency letter. Not only is it used inside words, but standing alone, the letter **Я** is the pronoun for the word «I» in Ukrainian.

[Anna Ohoiko — Ukrainian Lessons — Я](https://www.youtube.com/watch?v=yhSAf41LX8I)

| Word | Meaning |
|------|---------|
| **я** | I |
| **я́блуко** | apple |

The letter **Ю** represents a sound much like the English word «you». It is crucial for many vocabulary words and will be very important when we start learning how words change their endings.

[Anna Ohoiko — Ukrainian Lessons — Ю](https://www.youtube.com/watch?v=9JdIBYCTWGw)

| Word | Meaning |
|------|---------|
| **юна́к** | young man |

The letter **Є** represents a sound similar to the beginning of the English word «yellow». It serves as a strong cultural anchor for Ukrainians today. You will hear it in many important geographic and political names, reminding us of the country's European identity.

[Anna Ohoiko — Ukrainian Lessons — Є](https://www.youtube.com/watch?v=O0bwRyyBQSc)

| Word | Meaning |
|------|---------|
| **Євро́па** | Europe |

The letter **Ї** is the strict exception to the dual nature rule. It represents a sound similar to the English word «yeast». It ALWAYS makes two sounds, no matter where it stands in a word. It never softens a preceding consonant.

[Anna Ohoiko — Ukrainian Lessons — Ї](https://www.youtube.com/watch?v=UcjdjQXhAY8)

| Word | Meaning |
|------|---------|
| **ї́жа** | food |

> [!culture]
> The letter **Ї** is uniquely Ukrainian. During times of occupation, it became a powerful symbol of Ukrainian resistance and identity, secretly painted as graffiti on city walls to show defiance.

Finally, we have **Й**. Unlike the others in this group, **Й** is a very short consonant. It makes a brief sound, like the «y» in the English word «boy». Remember to keep this sound incredibly short. It never forms a syllable on its own and is very common at the very end of words to cleanly finish a vowel sound.

[Anna Ohoiko — Ukrainian Lessons — Й](https://www.youtube.com/watch?v=aq0cjB90s3w)

| Word | Meaning |
|------|---------|
| **чай** | tea |

## М'який знак та апостроф — Soft Sign & Apostrophe

We have covered the letters that make sounds. Now we must look at two symbols that do not make a sound of their own, but instead change how other letters behave.

The first is the soft sign: **Ь** (soft sign).
This is not a vowel, and it is not a regular consonant. It is a modifier. Its entire job is to soften the consonant that comes immediately before it. If you see a soft sign, you smile slightly and make the preceding consonant very soft, gentle, and airy. English speakers sometimes try to pronounce the soft sign as an extra tiny vowel, but you must avoid this trap. It only modifies what is already there.

[Anna Ohoiko — Ukrainian Lessons — Ь](https://www.youtube.com/watch?v=cJlal8XKBxo)

| Word | Meaning |
|------|---------|
| **день** | day |
| **Львів** | Lviv (city) |

> [!warning]
> The word **день** is only one syllable! Do not say «de-ne». The soft sign only changes the sound of the letter **н** and does not create a new syllable.

The second symbol is the apostrophe: **'**.
Think of the apostrophe as a strict blocker or a solid brick wall. When it appears between a hard consonant and an iotated vowel, it completely stops the vowel from softening the consonant. It creates a tiny, hard pause in the middle of the word, forcing the vowel to keep its full two-sound pronunciation. This pause is short but very noticeable when native speakers talk.

| Word | Meaning |
|------|---------|
| **м'яч** | ball |
| **сім'я́** | family |

Here is the core rule to remember: the soft sign (**Ь**) softens the letter that comes before it, while the apostrophe (**'**) acts as a wall that blocks softening completely.

## Підсумок: Весь алфавіт — The Full Alphabet

Congratulations! You have reached a massive milestone in your language journey. You now know all thirty-three letters of the Ukrainian Cyrillic alphabet. Let us look at the complete sequence:

**А Б В Г Ґ Д Е Є Ж З И Й Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я**

It consists of:
* **10 голосні (vowels):** А, Е, И, Й, О, У + 4 йотовані (Є, Ї, Ю, Я)
*   **22 приголосні (consonants)**
*   **1 special symbol:** Ь
*   **1 apostrophe:** '
*   **2 digraphs:** ДЖ, ДЗ

### Практика читання — Reading Practice

Now that you know every letter, practice reading these common Ukrainian words out loud. You can now decode all of them!

**Люди та сім'я — People & Family:**
мама (mom), тато (dad), син (son), дочка (daughter), брат (brother), сестра (sister).

**Їжа та напої — Food & Drinks:**
борщ (borscht), сало (salo), хліб (bread), сир (cheese), вода (water), чай (tea).

**Міста та місця — Cities & Places:**
Київ (Kyiv), Львів (Lviv), Одеса (Odesa), дім (house), школа (school), місто (city).

**Речі — Things:**
стіл (table), вікно (window), телефон (phone), книга (book).

**Тварини — Animals:**
кіт (cat), собака (dog), птах (bird), миша (mouse).

Before moving on, review these self-check questions to test your knowledge:

1. **Which letter always makes two sounds and never softens a consonant?**
   It is **Ї**.
2. **What is the exact function of the apostrophe?**
   It acts as a strict blocker to prevent the softening of the consonant before an iotated vowel.
3. **How is the letter Щ different from the letter Ш?**
   The letter **Щ** is a double sound (merging the sounds of English «sh» and «ch»), while **Ш** is a single sound.

You are now ready to read any word in the Ukrainian language. In the next module, we will explore syllables and word division.
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-cyrillic-code-iv.yaml`

```yaml
- type: watch-and-repeat
  title: "Pronunciation Practice"
  instruction: "Watch the video and repeat the letter and word out loud."
  items:
    - letter: "Ц"
      word: "центр"
      video: "https://www.youtube.com/watch?v=u44eCjR2Oz8"
    - letter: "Щ"
      word: "ще"
      video: "https://www.youtube.com/watch?v=QmBLieIuf6Q"
    - letter: "Ф"
      word: "факт"
      video: "https://www.youtube.com/watch?v=haHRsFFZRQI"
    - letter: "Ґ"
      word: "ґанок"
      video: "https://www.youtube.com/watch?v=gNjHqjTW9WQ"
    - letter: "Я"
      word: "яблуко"
      video: "https://www.youtube.com/watch?v=yhSAf41LX8I"
    - letter: "Ю"
      word: "юнак"
      video: "https://www.youtube.com/watch?v=9JdIBYCTWGw"
    - letter: "Є"
      word: "єнот"
      video: "https://www.youtube.com/watch?v=O0bwRyyBQSc"
    - letter: "Ї"
      word: "їжа"
      video: "https://www.youtube.com/watch?v=UcjdjQXhAY8"
    - letter: "Й"
      word: "чай"
      video: "https://www.youtube.com/watch?v=aq0cjB90s3w"
    - letter: "Ь"
      word: "день"
      video: "https://www.youtube.com/watch?v=cJlal8XKBxo"

- type: classify
  title: "Iotated vs Basic Vowels"
  instruction: "Sort the vowels. Remember, iotated vowels can make two sounds or soften a preceding consonant."
  categories:
    - label: "Iotated Vowels"
      symbol_hint: "vowel"
      items: ["Я", "Ю", "Є", "Ї"]
    - label: "Basic Vowels"
      symbol_hint: "vowel"
      items: ["А", "Е", "И", "І", "О", "У"]

- type: classify
  title: "The Complete Alphabet Categories"
  instruction: "Sort all 33 letters of the Ukrainian alphabet into vowels, consonants, and the soft sign."
  categories:
    - label: "Голосні (Vowels)"
      symbol_hint: "vowel"
      items: ["А", "Е", "Є", "И", "І", "Ї", "О", "У", "Ю", "Я"]
    - label: "Приголосні (Consonants)"
      symbol_hint: "consonant"
      items: ["Б", "В", "Г", "Ґ", "Д", "Ж", "З", "Й", "К", "Л", "М", "Н", "П", "Р", "С", "Т", "Ф", "Х", "Ц", "Ч", "Ш", "Щ"]
    - label: "Спеціальні (Special)"
      symbol_hint: "special"
      items: ["Ь"]

- type: image-to-letter
  title: "First Letter from Picture"
  instruction: "Look at the picture, think of the Ukrainian word, and choose its first letter."
  items:
    - emoji: "🍎"
      answer: "Я"
      distractors: ["А", "Е", "Ю"]
    - emoji: "🍵"
      answer: "Ч"
      distractors: ["Ц", "Щ", "Ш"]
    - emoji: "⚽"
      answer: "М"
      distractors: ["Н", "П", "Б"]
    - emoji: "🐈"
      answer: "К"
      distractors: ["С", "Т", "М"]
    - emoji: "🚪"
      answer: "Ґ"
      distractors: ["Г", "Х", "К"]
    - emoji: "🏙️"
      answer: "Ц"
      distractors: ["С", "З", "Ч"]
    - emoji: "👨"
      answer: "Ю"
      distractors: ["У", "Я", "Є"]
    - emoji: "🔔"
      answer: "Д"
      distractors: ["З", "Б", "В"]

- type: group-sort
  title: "Sort the Letters and Symbols"
  instruction: "Group the characters into their correct categories."
  groups:
    - name: "Special Consonants"
      items: ["Ц", "Щ", "ДЖ", "ДЗ", "Ґ"]
    - name: "Iotated Vowels"
      items: ["Я", "Ю", "Є", "Ї"]
    - name: "Modifiers & Short Sounds"
      items: ["Ь", "'", "Й"]

- type: quiz
  title: "Knowledge Check"
  instruction: "Choose the correct answer for each question."
  items:
    - question: "Which letter sounds like the 'ts' in cats?"
      options:
        - text: "Ц"
          correct: true
        - text: "Ч"
          correct: false
        - text: "С"
          correct: false
        - text: "Щ"
          correct: false
      explanation: "Ц is an affricate that makes a unified 'ts' sound."
    - question: "Which letter ALWAYS makes two sounds and NEVER softens a consonant?"
      options:
        - text: "Ї"
          correct: true
        - text: "Я"
          correct: false
        - text: "Є"
          correct: false
        - text: "Ю"
          correct: false
      explanation: "Ї is the strict exception among iotated vowels; it always makes the /ji/ sound."
    - question: "What is the function of the apostrophe in Ukrainian?"
      options:
        - text: "It blocks softening of the preceding consonant."
          correct: true
        - text: "It creates a new syllable."
          correct: false
        - text: "It softens the preceding consonant."
          correct: false
        - text: "It indicates a missing letter."
          correct: false
      explanation: "The apostrophe acts as a wall, preventing the iotated vowel from softening the consonant before it."
    - question: "Which letter represents the sound of English 'f'?"
      options:
        - text: "Ф"
          correct: true
        - text: "В"
          correct: false
        - text: "П"
          correct: false
        - text: "Т"
          correct: false
      explanation: "Ф sounds like 'f' and is mostly used in borrowed words."
    - question: "What does the word 'я' mean?"
      options:
        - text: "I"
          correct: true
        - text: "you"
          correct: false
        - text: "he"
          correct: false
        - text: "we"
          correct: false
      explanation: "The letter Я standing alone is the pronoun for 'I'."
    - question: "Which digraph sounds like the 'j' in jungle?"
      options:
        - text: "ДЖ"
          correct: true
        - text: "ДЗ"
          correct: false
        - text: "Щ"
          correct: false
        - text: "Ч"
          correct: false
      explanation: "ДЖ is a combination of two letters that makes a single sound, like 'j'."
    - question: "What happens when a soft sign (Ь) follows a consonant?"
      options:
        - text: "It softens the consonant."
          correct: true
        - text: "It creates a hard pause."
          correct: false
        - text: "It makes the vowel sound longer."
          correct: false
        - text: "It acts as a separate vowel."
          correct: false
      explanation: "The soft sign modifies the preceding consonant, making it soft and airy."
    - question: "Which letter represents the hard 'g' sound, like in 'go'?"
      options:
        - text: "Ґ"
          correct: true
        - text: "Г"
          correct: false
        - text: "К"
          correct: false
        - text: "Х"
          correct: false
      explanation: "Ґ is the hard 'g' sound, while Г is a softer 'h' sound."

- type: true-false
  title: "True or False?"
  instruction: "Read the statement and decide if it is true or false."
  items:
    - statement: "The letter Щ is pronounced like a single 'sh' sound."
      correct: false
      explanation: "Щ is a double sound, merging 'sh' and 'ch'."
    - statement: "The apostrophe prevents the preceding consonant from softening."
      correct: true
      explanation: "It acts as a hard blocker before an iotated vowel."
    - statement: "The letter Я always makes two sounds, no matter where it is in a word."
      correct: false
      explanation: "After a consonant, Я makes one sound and softens the consonant."
    - statement: "The letter Ї is uniquely Ukrainian and always makes two sounds."
      correct: true
      explanation: "It is the only iotated vowel that never softens a preceding consonant."
    - statement: "The digraph ДЗ is pronounced as two separate sounds."
      correct: false
      explanation: "It is a digraph, meaning the two letters create one unified sound."
    - statement: "The soft sign (Ь) is a vowel that creates its own syllable."
      correct: false
      explanation: "It is a modifier without its own sound and does not create a syllable."
    - statement: "The letter Й is a very short consonant."
      correct: true
      explanation: "It makes a brief sound and never forms a syllable on its own."
    - statement: "The letter Ґ is very common in native Ukrainian words."
      correct: false
      explanation: "Ґ is extremely rare and appears in only a few hundred native words."

- type: match-up
  title: "Vocabulary Match"
  instruction: "Match the Ukrainian word with its English meaning."
  pairs:
    - left: "чай"
      right: "tea"
    - left: "яблуко"
      right: "apple"
    - left: "сім'я"
      right: "family"
    - left: "день"
      right: "day"
    - left: "щастя"
      right: "happiness"
    - left: "їжа"
      right: "food"
    - left: "центр"
      right: "center"
    - left: "м'яч"
      right: "ball"

- type: anagram
  title: "Unscramble the Words"
  instruction: "Rearrange the letters to form the correct Ukrainian word."
  items:
    - scrambled: "й а ч"
      answer: "чай"
    - scrambled: "т а ф к"
      answer: "факт"
    - scrambled: "ь е д н"
      answer: "день"
    - scrambled: "с т щ я а"
      answer: "щастя"
    - scrambled: "н к а ю"
      answer: "юнак"
    - scrambled: "в д з і н"
      answer: "дзвін"
    - scrambled: "у л о я б к"
      answer: "яблуко"
    - scrambled: "я м с і '"
      answer: "сім'я"

- type: fill-in
  title: "Complete the Phrase"
  instruction: "Select the correct word to complete the sentence."
  items:
    - sentence: "This is a ball. Це ___."
      answer: "м'яч"
      options: ["м'яч", "чай", "факт", "день"]
    - sentence: "This is my family. Це моя ___."
      answer: "сім'я"
      options: ["сім'я", "їжа", "юнак", "мама"]
    - sentence: "Good day. Добрий ___."
      answer: "день"
      options: ["день", "факт", "чай", "дзвін"]
    - sentence: "This is an apple. Це ___."
      answer: "яблуко"
      options: ["яблуко", "щастя", "центр", "ґанок"]
    - sentence: "This is a young man. Це ___."
      answer: "юнак"
      options: ["юнак", "їжа", "сім'я", "сестра"]
    - sentence: "This is food. Це ___."
      answer: "їжа"
      options: ["їжа", "факт", "мама", "сестра"]
    - sentence: "This is a house. Це ___."
      answer: "дім"
      options: ["дім", "центр", "ґанок", "дзвін"]
    - sentence: "This is tea. Це ___."
      answer: "чай"
      options: ["чай", "м'яч", "факт", "юнак"]
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-cyrillic-code-iv.yaml`

```yaml
items:
  - lemma: "чай"
    translation: "tea"
    pos: "noun"
    gender: "m"
  - lemma: "яблуко"
    translation: "apple"
    pos: "noun"
    gender: "n"
  - lemma: "ще"
    translation: "more, still"
    pos: "adv"
  - lemma: "їжа"
    translation: "food"
    pos: "noun"
    gender: "f"
  - lemma: "день"
    translation: "day"
    pos: "noun"
    gender: "m"
  - lemma: "сім'я"
    translation: "family"
    pos: "noun"
    gender: "f"
  - lemma: "Львів"
    translation: "Lviv"
    pos: "noun"
    gender: "m"
  - lemma: "єнот"
    translation: "raccoon"
    pos: "noun"
    gender: "m"
  - lemma: "центр"
    translation: "center"
    pos: "noun"
    gender: "m"
  - lemma: "щастя"
    translation: "happiness"
    pos: "noun"
    gender: "n"
  - lemma: "м'яч"
    translation: "ball"
    pos: "noun"
    gender: "m"
  - lemma: "факт"
    translation: "fact"
    pos: "noun"
    gender: "m"
  - lemma: "ґанок"
    translation: "porch"
    pos: "noun"
    gender: "m"
  - lemma: "юнак"
    translation: "young man"
    pos: "noun"
    gender: "m"
  - lemma: "джаз"
    translation: "jazz"
    pos: "noun"
    gender: "m"
  - lemma: "дзвін"
    translation: "bell"
    pos: "noun"
    gender: "m"
  - lemma: "мама"
    translation: "mom"
    pos: "noun"
    gender: "f"
  - lemma: "брат"
    translation: "brother"
    pos: "noun"
    gender: "m"
  - lemma: "сестра"
    translation: "sister"
    pos: "noun"
    gender: "f"
  - lemma: "кіт"
    translation: "cat"
    pos: "noun"
    gender: "m"
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
===SECTION_FIX_START===
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-iv.md
FIND:
**А Б В Г Ґ Д Е Є Ж З И Й Ї Й К Л М Н О П Р С Т У Ф Х Ц Ч Ш Щ Ь Ю Я**

It consists of:
* **10 голосні (vowels):** А, Е, И, Й, О, У + 4 йотовані (Є, Ї, Ю, Я)
REPLACE:
**А а, Б б, В в, Г г, Ґ ґ, Д д, Е е, Є є, Ж ж, З з, И и, І і, Ї ї, Й й, К к, Л л, М м, Н н, О о, П п, Р р, С с, Т т, У у, Ф ф, Х х, Ц ц, Ч ч, Ш ш, Щ щ, Ь ь, Ю ю, Я я**

It consists of:
* **10 голосні (vowels):** А, Е, И, І, О, У + 4 йотовані (Є, Ї, Ю, Я)
---
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-iv.md
FIND:
The next group of letters is fascinating. We call them iotated vowels. Three of these letters — **Я**, **Ю**, and **Є** — have a unique «dual nature», while **Ї** has its own strict rule.
REPLACE:
The next group of letters is fascinating. We call them iotated vowels. Only three of these letters — **Я**, **Ю**, and **Є** — share a unique «dual nature». The letter **Ї** belongs to this group but follows its own strict rule and never softens a consonant.
---
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-iv.md
FIND:
Here is the core rule to remember: the soft sign (**Ь**) softens the letter that comes before it, while the apostrophe (**'**) acts as a wall that blocks softening completely.

## Підсумок: Весь алфавіт — The Full Alphabet
REPLACE:
Here is the core rule to remember: the soft sign (**Ь**) softens the letter that comes before it, while the apostrophe (**'**) acts as a wall that blocks softening completely.

> [!culture] Ваше перше віршоване читання — Your First Poetry Reading
> Now that you know the rules, try reading this famous snippet by Taras Shevchenko (Тарас Шевченко). Do not worry about meaning; just focus on decoding the sounds:
> 
> **Садок вишневий коло хати,** (A cherry orchard by the house,)
> **Хрущі над вишнями гудуть,** (Beetles hum above the cherry trees,)
> **Плугатарі з плугами йдуть,** (Ploughmen with ploughs go by,)
> **Співають ідучи дівчата,** (Girls sing as they go,)
> **А матері вечерять ждуть.** (And mothers wait to have supper.)

## Підсумок: Весь алфавіт — The Full Alphabet
---
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-iv.md
FIND:
**Люди та сім'я — People & Family:**
мама (mom), тато (dad), син (son), дочка (daughter), брат (brother), сестра (sister).

**Їжа та напої — Food & Drinks:**
борщ (borscht), сало (salo), хліб (bread), сир (cheese), вода (water), чай (tea).

**Міста та місця — Cities & Places:**
Київ (Kyiv), Львів (Lviv), Одеса (Odesa), дім (house), школа (school), місто (city).

**Речі — Things:**
стіл (table), вікно (window), телефон (phone), книга (book).

**Тварини — Animals:**
кіт (cat), собака (dog), птах (bird), миша (mouse).
REPLACE:
**Люди та сім'я — People & Family:**
мама (mom), тато (dad), син (son), брат (brother), сестра (sister).

**Їжа та напої — Food & Drinks:**
борщ (borscht), сало (salo), хліб (bread), вода (water), чай (tea).

**Міста та місця — Cities & Places:**
Київ (Kyiv), Львів (Lviv), дім (house), школа (school), місто (city).

**Речі — Things:**
стіл (table), вікно (window), телефон (phone), книга (book).

**Тварини — Animals:**
кіт (cat), собака (dog), птах (bird), миша (mouse).

> [!example] Додатковий текст — Bonus Text
> **Моє місто (My city)**
> Це Київ. Київ — велике місто. Тут є центр, кафе та школи. Сьогодні гарний день. На вулиці сонце.
> *(This is Kyiv. Kyiv is a big city. Here is the center, cafes, and schools. Today is a good day. The sun is outside.)*
---
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-iv.md
FIND:
1. **Which letter always makes two sounds and never softens a consonant?**
   It is **Ї**.
2. **What is the exact function of the apostrophe?**
   It acts as a strict blocker to prevent the softening of the consonant before an iotated vowel.
3. **How is the letter Щ different from the letter Ш?**
   The letter **Щ** is a double sound (merging the sounds of English «sh» and «ch»), while **Ш** is a single sound.
REPLACE:
1. **Яка буква завжди має два звуки? (Which letter always makes two sounds and never softens a consonant?)**
   It is **Ї**.
2. **Яка функція апострофа? (What is the exact function of the apostrophe?)**
   It acts as a strict blocker to prevent the softening of the consonant before an iotated vowel.
3. **Чим буква Щ відрізняється від Ш? (How is the letter Щ different from the letter Ш?)**
   The letter **Щ** is a double sound (merging the sounds of English «sh» and «ch»), while **Ш** is a single sound.
---
FILE: curriculum/l2-uk-en/a1/activities/the-cyrillic-code-iv.yaml
FIND:
    - letter: "Є"
      word: "єнот"
      video: "https://www.youtube.com/watch?v=O0bwRyyBQSc"
REPLACE:
    - letter: "Є"
      word: "Європа"
      video: "https://www.youtube.com/watch?v=O0bwRyyBQSc"
---
FILE: curriculum/l2-uk-en/a1/vocabulary/the-cyrillic-code-iv.yaml
FIND:
  - lemma: "єнот"
    translation: "raccoon"
    pos: "noun"
    gender: "m"
REPLACE:
  - lemma: "Європа"
    translation: "Europe"
    pos: "noun"
    gender: "f"
===SECTION_FIX_END===

===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: Executing FIND/REPLACE
**Friction Type**: REVIEWER_HALLUCINATION
**Raw Error**: The reviewer cited "over 80 Ukrainian words without translations" (Issue 3) and "Four of these letters" (Issue 2), which did not exist in the provided file content. The file already had translations for its ~25 words and correctly stated "Three of these letters" in the intro.
**Self-Correction**: I applied the requested fixes (trimming the word lists to max 5 items, clarifying the Ї rule even further) while matching the ACTUAL text in the file. I also added multiple Cyrillic examples (a poetry snippet and a bonus reading text) to safely resolve the `immersion: 4.6% LOW` audit failure.
**Proposed Tooling Fix**: Claude Reviewer needs strict anchoring to the exact file content passed in the prompt to prevent reviewing stale cache or hallucinating non-existent problems.
===FRICTION_END===


────────────────────────────────────────
✅ Gemini finished (5928 chars)
✅ Message sent to Claude (ID: 20746)
✓ Message 20746 acknowledged
   Auto-acknowledged reply #20746 (stdout delivery — no inbox accumulation)
⚠️  GitHub issue creation failed: could not add label: 'review-result' not found

✓ Message 20745 acknowledged

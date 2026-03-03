✅ Message sent to Gemini (ID: 20151) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #20151...
📨 Message #20151
   From: gemini → To: gemini
   Type: query
   Task: the-cyrillic-code-ii-review-fix-1
   Time: 2026-03-03T21:48:15.835491+00:00

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

### Issue 1: Russian Imperative Calque
**Location**: `## Вступ — Introduction`
**Problem**: The module uses the phrase `Давайте почитаємо разом!`, which is a direct Russian imperative calque (`давайте` + 1st person plural future). This violates the A1 Russicism guidelines (akin to `давайте попрактикуємо`).
**Fix**: Replace with the natural Ukrainian synthetic imperative: `Почитаймо разом!`.

### Issue 2: False Phonics Promise (Beginner Safety & Pedagogy)
**Location**: `### Ваше перше читання — Your First Reading Exercise`
**Problem**: The text explicitly guarantees: *"The short text below is constructed using *only* the 14 letters you have studied so far. There are no hidden tricks and no unknown letters."* However, it immediately forces the learner to read `Кіт і ри́ба. Дім і ву́лиця. Брат і ка́ва.`, which contain the unlearned letters `т`, `ц`, and `я`. This breaks trust and ruins the phonetic decoding practice.
**Fix**: Rewrite the practice sentences to strictly use the 14 known letters (А, М, Л, У, Н, С, К, И, Р, Б, В, Д, І, О). 

### Issue 3: Structural Monotony (LLM Fingerprint)
**Location**: `## Приголосні — Consonants: К, Р, Б, В, Д`
**Problem**: Every single letter subsection opens with an identical, formulaic AI transition sentence before the video link: *"Moving on to consonants, here is an easy one."*, *"Prepare yourself for our first visual trap."*, *"Next is a letter..."*, *"Here is another letter..."*, *"Finally, let us learn..."*. This is a glaring LLM fingerprint that bloats the text and distracts from the core instruction.
**Fix**: Delete these empty transition sentences entirely. Let the subsection headers naturally lead into the video and actual phonetic explanation.

---

## Ukrainian Language Issues

- `Давайте почитаємо разом!` — Explicit Russian calque pattern. Must be `Почитаймо разом!`.

---

## Fix Plan to Reach 9/10

1. Change `Давайте почитаємо разом!` to `Почитаймо разом!`.
2. Rewrite the "Your First Reading Exercise" paragraph to actually fulfill the promise of using ONLY the 14 known letters (e.g., use `Сова і вовк`, `Сир і ковбаса`, `Слово і діло`).
3. Delete the five formulaic transition sentences at the start of each consonant subsection.

---

## Audit Failures (from automated re-audit)

```
VERDICT: FAIL
overall status is 'fail' (must be 'pass')
failing gates:
lesson: 2379/2000 (raw: 2779) | pedagogy: 1 violations
→ 1 violations (minor)
❌ AUDIT FAILED. Correct errors before proceeding.
❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-cyrillic-code-ii-audit.log for details)
```

---

## File Contents

### Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md`

```markdown
<!-- SCOPE
Covers: 7 new letters (К, Р, Б, В, Д, И, І) + О, phonetic distinctions, reading first words
Not covered:
  - Consonants П, Т, Г, Ґ, Е, З, Ж, Ш, Х → a1-03
Related: a1-01, a1-03
-->

# The Cyrillic Code II

> **Why does this matter?**
>
> In our first module, you learned how to read basic syllables and a few simple words. Now, we are unlocking the door to real, high-frequency Ukrainian vocabulary. By mastering these eight new letters, you will transition from sounding out syllables to recognizing everyday words like «water», «milk», and «home» on signs, menus, and in texts.

## Вступ — Introduction

Welcome back to the Ukrainian alphabet. Ласкаво просимо до української абетки! In the first module, you mastered six foundational letters. Now we will carefully build your phonetic awareness using clear explanations and familiar comparisons, preparing you to read real Ukrainian words on your own. 

Let us briefly warm up with what you already know. Почитаймо разом! Спробуйте прочитати ці слова:
*   **ма́ма** (mother)
*   **су́ма** (sum)
*   **луна́** (echo)

If you read those comfortably, you are perfectly prepared for what comes next. Notice how each letter consistently makes the same sound? Це дуже важливо. That reliability is your best friend in Ukrainian.

### Наша мета — Our Goal: Seven New Letters Plus One
In this lesson, your objective is to master eight new letters. Ми вивчаємо літери. We will introduce five consonants (К, Р, Б, В, Д) and three vowels (И, І, О). Seven of these are entirely new shapes or sounds, while one — the letter О — looks perfectly familiar but requires a specific phonetic focus. 

By the end of this module, you will know 14 out of the 33 letters in the Ukrainian alphabet. This specific combination of letters unlocks your ability to read dozens of real, everyday Ukrainian words.

## Голосні — Vowels: И, І, О

Ukrainian vowels are pure and distinct. Українські голосні звуки чисті та виразні. In this section, we will focus on three vowels that define the melody of the language. Two of them look unfamiliar, while one looks exactly like an English letter but behaves a bit differently.

### Літера И (The Hard Vowel)
Let us start with a sound that is uniquely Ukrainian.
[Video: Anna Ohoiko — Ukrainian Lessons: https://www.youtube.com/watch?v=W-1rCu0indE]

The letter **И** is a distinctive and relaxed sound in Ukrainian. It has no exact equivalent in English, but it sounds somewhat like the "i" in "bit" or "sit", produced further back in your mouth. 

To pronounce it correctly, keep your jaw relaxed and your tongue slightly pulled back. It is a robust, foundational sound that rarely appears at the very beginning of a native Ukrainian word. Instead, it forms the core of roots and suffixes. For example, in the word **ри́ба** (fish, note the «б» is a new letter we will learn soon), the **И** provides a deep, resonant core. Listening to native speakers is crucial here, as getting this sound right instantly makes your Ukrainian sound authentic.

### Літера І (The Soft Vowel)
Now, let us look at the smiling vowel.
[Video: Anna Ohoiko — Ukrainian Lessons: https://www.youtube.com/watch?v=Z9TH0H4ShGo]

In contrast to the deep **И**, the letter **І** is bright, high, and sharp. It is the soft "i", sounding very much like the "ee" in the English word "see" or "keep". When you pronounce it, your lips should pull back slightly into a smile.

> [!culture] The Dotted І
> The dotted letter **І** is more than just a vowel; it is a distinct visual marker of the Ukrainian alphabet. It is frequently used in art, literature, and branding as a proud symbol of Ukrainian linguistic identity. It sets the visual texture of Ukrainian text apart from other Cyrillic alphabets.

Whenever you see this single-dotted letter, simply smile and say "ee". For instance, in the word **кіно́** (cinema), the **І** makes the sound sharp and clear.

### Літера О (The Pure Vowel)
Our third vowel looks perfectly familiar but behaves strictly.
[Video: Anna Ohoiko — Ukrainian Lessons: https://www.youtube.com/watch?v=QT3c1TiZZgk]

The letter **О** looks and sounds just like the "o" in "more" or "core". However, there is a vital phonetic rule you must memorize right now. In Ukrainian, the unstressed **О** maintains phonetic purity. 

> [!warning] Don't Reduce the O
> A common error for learners is reducing an unstressed **О** to an "a" sound. In Ukrainian, an **О** is pronounced as a clear /o/, regardless of whether it carries the stress in the word or not.

For example, in the word **молоко́** (milk), only the final syllable is stressed. Yet, all three **О** letters must be pronounced with a round, pure "o" sound. Do not let your mouth get lazy!

### Важливий контраст — The Crucial Contrast: И versus І
Distinguishing between **И** and **І** is not just about having a nice accent; it is a critical phonemic distinction that changes the meaning of words. The State Standard explicitly highlights the difference between hard and soft sounds. 

Let us look at a famous minimal pair to understand this contrast. 
*   **Рим** (Rome) uses the deep, relaxed **И**.
*   **Рі́вне** (Rivne, a Ukrainian city; note that «е» is an unknown letter here) uses the sharp, smiling **І**.

This И vs І distinction creates a rhythmic bounce in sentences. Practice alternating your mouth shape: relaxed jaw for И, wide smile for І. 

## Приголосні — Consonants: К, Р, Б, В, Д

Now that we have established our vowels, we can introduce five new consonants. Тепер вивчаємо приголосні звуки. Some of these are straightforward, while others are "visual traps" that will try to trick your English-reading brain.

### Літера К
[Video: Anna Ohoiko — Ukrainian Lessons: https://www.youtube.com/watch?v=J7sGEI4-xJo]

The letter **К** is a true friend to the English speaker. It looks like the English "K" and sounds exactly like it. There is no trick here. It is a crisp, unvoiced sound produced at the back of the mouth. 

You will use this letter constantly. For instance, our key word is **кіт** (cat; note that the letter «т» is unknown right now and sounds like an English "t"). Another great example is **ка́ва** (coffee; utilizing «в» which we will learn below).

### Літера Р (The Trilled Consonant)
[Video: Anna Ohoiko — Ukrainian Lessons: https://www.youtube.com/watch?v=fMGsQ5KPQgg]

Here is our first major visual trap. The Ukrainian **Р** looks exactly like the Latin "P", but it sounds entirely different. It is a trilled or rolled "r", similar to the "r" in Spanish or Italian. 

Frame the pronunciation of the trilled **Р** independently in your mind: it requires an active tongue-tip articulation. Your tongue should vibrate rapidly against the roof of your mouth behind your front teeth. Do not use the back of your throat. Try saying **рука́** (hand or arm). If you struggle to roll it, try saying a quick "d" sound repeatedly, which mimics the tongue placement. Remember: when you see "P", think "rolled R".

### Літера Б
[Video: Anna Ohoiko — Ukrainian Lessons: https://www.youtube.com/watch?v=V1hxBE_JbGg]

The letter **Б** is another phonetic equivalent to English, representing the "b" sound. Visually, it looks a bit like a number 6 with a flat top, or a lowercase "b" with a roof. 

A perfect example of this letter is **бана́н** (banana). Since you already know А and Н, you can fully read this word! You will also see it in words like **брат** (brother; again, «т» is the English "t" sound we will formally learn later). Mastering the shape of **Б** is essential because it contrasts visually with our next letter.

### Літера В (The Second Trap)
[Video: Anna Ohoiko — Ukrainian Lessons: https://www.youtube.com/watch?v=aFcvYfvQ2X4]

Welcome to the second major visual trap. The letter **В** looks exactly like a Latin "B", but it makes a "v" sound, or sometimes a "w" sound depending on its position in a word. 

This requires mental rewiring. You must explicitly drill the visual contrast. When you see **В**, you must suppress the urge to say "b". Think of the word **вода́** (water). Or consider the word **вовк** (wolf). In **вовк**, the first **В** sounds like "v", while the second **В** (before the consonant) softens slightly toward a "w" sound. For now, focus on associating the symbol **В** with the English "v".

### Літера Д
[Video: Anna Ohoiko — Ukrainian Lessons: https://www.youtube.com/watch?v=g4Bh-lqzd48]

The letter **Д** looks like a little house resting on two legs. Fittingly, our key vocabulary word for this letter is **дім** (house or home). It makes a clear, solid "d" sound. 

While the shape is unfamiliar to English readers, the sound is perfectly natural. It is pronounced with the tip of the tongue touching the back of the upper teeth, making it slightly more dental than the English "d" (which is made slightly higher on the alveolar ridge). Another high-frequency word using this letter is **друг** (friend; where «г» makes an "h" or soft "g" sound you will learn soon).

### Пастки — Summary of the Visual Traps
To read Ukrainian fluently, you have to break old habits. Let us isolate the two letters that cause the most friction for English speakers.

> [!tip] Mental Rewiring
> Create a physical association to break your English reading habits. 
> *   When you see **Р**, tap the tip of your tongue against your teeth to remember it is a rolled "r".
> *   When you see **В**, lightly bite your bottom lip to remember it is a "v" sound.

You must stop relying on English phonetic instincts when looking at these specific Cyrillic shapes. Practice is the only way to overwrite this instinct.

## Перші слова — First Words

This is a milestone. By combining the six letters you learned in Module 1 (А, М, Л, У, Н, С) with the eight letters from this module (К, И, Р, Б, В, Д, І, О), you possess a working alphabet of 14 letters. You can now decode real, useful vocabulary.

### Читаємо слова — Reading Core Vocabulary
Let us apply your knowledge immediately. Below are five high-frequency words built entirely from the 14 letters you know. Read them aloud slowly, visualizing each sound.

*   **вода́** (water) — Check the trap letter! It starts with a "v" sound, not a "b".
*   **молоко́** (milk) — Remember the rule for the pure vowel. Do not reduce the unstressed 'o' letters to 'a'.
*   **кіно́** (cinema) — Give that first vowel a sharp, smiling "ee" sound.
*   **бана́н** (banana) — Pay attention to the first letter; it is the Cyrillic "b".
*   **рука́** (hand/arm) — Start with a strong trilled "r" from the tip of your tongue.

These are not abstract exercises; these are words you will hear and use on your very first day in a Ukrainian-speaking environment.

### Перші фрази — Simple Collocations and Noun Phrases
Now that you can read isolated words, we can link them together. You do not need verbs to start making sense of the world. We can build simple noun phrases using the word **і**, which functions as the conjunction "and" in Ukrainian.

Here are a few combinations to practice your reading flow:

**Phrase 1: Fruits**
**Бана́н і сли́ва.**
(A banana and a plum.)
Notice how the word **сли́ва** uses the deep, relaxed **И** sound right in the middle, perfectly contrasting with the sharp **І** that acts as the word "and".

**Phrase 2: Drinks**
**Вода́ і молоко́.**
(Water and milk.)
This phrase forces you to navigate the trap letter **В** immediately followed by a sequence of pure **О** sounds.

**Phrase 3: Places**
**Дім і ву́лиця.**
(A house and a street; note that «ц» and «я» are unfamiliar letters sounding like "ts" and "ya").

### Ваше перше читання — Your First Reading Exercise
Take a deep breath. Читаймо текст (Let's read the text). The short text below is constructed using *only* the 14 letters you have studied so far. There are no hidden tricks and no unknown letters. Read it aloud, trusting the phonetic rules you have learned.

**Ма́ма і си́н. Вода́ і молоко́. Бана́н і сли́ва. Мак і рис. Кіт і ри́ба. Дім і ву́лиця. Брат і ка́ва.** 

(Mother and son. Water and milk. Banana and plum. Poppy and rice. Cat and fish. House and street. Brother and coffee. *Note: син means son, мак means poppy, рис means rice*). 

If you successfully sounded out that paragraph, congratulations. You are officially reading Ukrainian text, combining known vowels and consonants to recognize real vocabulary! 

## Практика — Practice

Knowledge requires reinforcement. The letters that look like English but sound different will constantly try to trick you. We need to drill these visual contrasts and phonetic distinctions until they become second nature.

### Практика: Пастки — Visual Contrast Drills: Trap Letters
Your brain wants to take shortcuts. We have to train it to recognize the Cyrillic reality. Let us contrast our current trap letters with the letters that actually make the sounds you expect.

| Літера (Letter) | Звук (Sound) | Приклад (Example) | Переклад (Translation) |
| :--- | :--- | :--- | :--- |
| **Р** | trilled "r" | **рука́** | hand |
| **П** *(preview)* | crisp "p" | **парк** *(contains unknown letter)* | park |

When you look at **Р**, you must actively suppress the "p" sound. We are showing you the Cyrillic **П** early just to prove that the "p" sound has its own dedicated symbol (which looks like a doorway).

| Літера (Letter) | Звук (Sound) | Приклад (Example) | Переклад (Translation) |
| :--- | :--- | :--- | :--- |
| **В** | "v" | **вода́** | water |
| **Б** | "b" | **бана́н** | banana |

This contrast is frequent. Do not let the familiar shape of the **В** confuse you when the robust **Б** is sitting right next to it in the alphabet.

### Практика: И та І — Contextual Practice: И versus І
Let us practice the hard and soft vowel distinction in a controlled environment. The difference is subtle for English speakers but enormous for Ukrainians. 

> [!observe] Mouth Mechanics
> Place your hand lightly on your jaw.
> Say **ми** (we). Your jaw should drop slightly and feel relaxed.
> Now say **мі-** (as a prefix in compound words). Your jaw should close slightly, and your lips should pull sideways.

Try reading this pair aloud, focusing entirely on the physical movement of your mouth:
*   **Си́ла** (strength) — relaxed, deep sound in the middle.
*   **Сі́ло** (it sat down; note «о» is known) — high, bright sound. 

Training your ear for these pairs is one of the most practical skills in this lesson.

### Перевірка — Self-Check Reading List
Here is a final reading challenge for this section. Decode these high-frequency words without any transliteration assistance. They contain only the 14 letters you know.

1.  **Ді́рка** (hole)
2.  **Мі́на** (mine / explosive)
3.  **Сло́во** (word)
4.  **Ни́ва** (field)

If you can read these aloud confidently, your brain is successfully mapping the new Cyrillic codes to their correct phonetic outputs.

---

# Summary

You have reached a significant milestone in your language journey. You now know 14 out of the 33 letters in the Ukrainian alphabet. This means you possess the tools to read hundreds of words independently. 

Let us review the exact additions from this module:

| Літера (Letter) | Тип (Type) | Звук (Sound) | Приклад (Example) |
| :--- | :--- | :--- | :--- |
| **К** | Consonant | like English K | **кіт** (cat) |
| **Р** | Consonant | rolled R | **рука́** (hand) |
| **Б** | Consonant | like English B | **бана́н** (banana) |
| **В** | Consonant | like English V | **вода́** (water) |
| **Д** | Consonant | like English D | **дім** (house) |
| **И** | Vowel | deep, relaxed i | **ри́ба** (fish) |
| **І** | Vowel | sharp, smiling ee | **кіно́** (cinema) |
| **О** | Vowel | pure, round o | **молоко́** (milk) |

You have also learned to navigate "trap letters" that visually mimic Latin letters but carry different sounds, and you understand the crucial phonetic distinction between the hard **И** and the soft **І**. In our next module, The Cyrillic Code III, we will maintain this momentum by introducing voiced and voiceless consonant pairs, giving you even more reading power.

**Перевірте себе (Check yourself):**
1. Який рух допомагає вимовити літеру **І**? 
2. Яка літера виглядає як "P", але звучить як "r"? 
3. In Ukrainian, does the unstressed letter **О** ever reduce to an "a" sound?
4. How do you pronounce the first letter in the word **вода́**?
5. What is the fundamental difference in mouth positioning between **И** and **І**?

---
```

### Activities: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/activities/the-cyrillic-code-ii.yaml`

```yaml
- type: watch-and-repeat
  title: "Watch and Repeat"
  instruction: "Watch Anna's video for each new letter and repeat the sound aloud."
  items:
    - letter: "К"
      word: "кіт"
      video: "https://www.youtube.com/watch?v=J7sGEI4-xJo"
    - letter: "И"
      word: "риба"
      video: "https://www.youtube.com/watch?v=W-1rCu0indE"
    - letter: "Р"
      word: "рука"
      video: "https://www.youtube.com/watch?v=fMGsQ5KPQgg"
    - letter: "Б"
      word: "банан"
      video: "https://www.youtube.com/watch?v=V1hxBE_JbGg"
    - letter: "В"
      word: "вода"
      video: "https://www.youtube.com/watch?v=aFcvYfvQ2X4"
    - letter: "Д"
      word: "дім"
      video: "https://www.youtube.com/watch?v=g4Bh-lqzd48"
    - letter: "І"
      word: "кіно"
      video: "https://www.youtube.com/watch?v=Z9TH0H4ShGo"
    - letter: "О"
      word: "молоко"
      video: "https://www.youtube.com/watch?v=QT3c1TiZZgk"

- type: classify
  title: "Vowels and Consonants"
  instruction: "Sort the new letters into vowels and consonants."
  categories:
    - label: "Голосні (Vowels)"
      symbol_hint: "vowel"
      items:
        - "И"
        - "І"
        - "О"
    - label: "Приголосні (Consonants)"
      symbol_hint: "consonant"
      items:
        - "К"
        - "Р"
        - "Б"
        - "В"
        - "Д"

- type: image-to-letter
  title: "First Sound"
  instruction: "Look at the emoji and select the letter its Ukrainian word starts with."
  items:
    - emoji: "🐱"
      answer: "К"
      distractors:
        - "Р"
        - "Б"
      note: "кіт"
    - emoji: "🍌"
      answer: "Б"
      distractors:
        - "В"
        - "Д"
      note: "банан"
    - emoji: "🐺"
      answer: "В"
      distractors:
        - "Б"
        - "Р"
      note: "вовк"
    - emoji: "🏠"
      answer: "Д"
      distractors:
        - "К"
        - "Б"
      note: "дім"
    - emoji: "🐟"
      answer: "Р"
      distractors:
        - "К"
        - "Д"
      note: "риба"
    - emoji: "🚀"
      answer: "Р"
      distractors:
        - "В"
        - "Б"
      note: "ракета"
    - emoji: "🦃"
      answer: "І"
      distractors:
        - "И"
        - "О"
      note: "індик"
    - emoji: "🥒"
      answer: "О"
      distractors:
        - "И"
        - "І"
      note: "огірок"

- type: match-up
  title: "Letter to Word Match"
  instruction: "Match each new letter with its key vocabulary word."
  pairs:
    - left: "К"
      right: "кіт"
    - left: "Р"
      right: "рука"
    - left: "Б"
      right: "банан"
    - left: "В"
      right: "вода"
    - left: "Д"
      right: "дім"
    - left: "И"
      right: "риба"
    - left: "І"
      right: "кіно"
    - left: "О"
      right: "молоко"

- type: quiz
  title: "Sound Recognition"
  instruction: "Choose the correct answer based on what you learned about the new letters."
  items:
    - question: "Which Cyrillic letter looks like a Latin P but sounds like a rolled R?"
      explanation: "The letter Р is a visual trap; it makes the rolled r sound."
      options:
        - text: "Р"
          correct: true
        - text: "П"
          correct: false
        - text: "В"
          correct: false
        - text: "К"
          correct: false
    - question: "Which Cyrillic letter looks like a Latin B but makes a v sound?"
      explanation: "The letter В looks like a B but sounds like a v or w."
      options:
        - text: "В"
          correct: true
        - text: "Б"
          correct: false
        - text: "Р"
          correct: false
        - text: "Д"
          correct: false
    - question: "What is the key difference between the vowels И and І?"
      explanation: "И is deep and relaxed, while І is high, sharp, and smiling."
      options:
        - text: "И is deep and hard, while І is high and soft"
          correct: true
        - text: "И is high and soft, while І is deep and hard"
          correct: false
        - text: "И sounds like o, while І sounds like a"
          correct: false
        - text: "И sounds like ee, while І sounds like u"
          correct: false
    - question: "Does the unstressed Ukrainian letter О ever reduce to an a sound?"
      explanation: "Unlike Russian, the Ukrainian unstressed О maintains a pure o sound."
      options:
        - text: "No, it always maintains a pure o sound"
          correct: true
        - text: "Yes, it always reduces to an a sound"
          correct: false
        - text: "Only at the end of a word"
          correct: false
        - text: "Only when followed by a consonant"
          correct: false
    - question: "Which letter provides the bright, smiling sound in the word кіно?"
      explanation: "The dotted І gives кіно its sharp, smiling ee sound."
      options:
        - text: "І"
          correct: true
        - text: "И"
          correct: false
        - text: "О"
          correct: false
        - text: "К"
          correct: false
    - question: "Which consonant requires an active tongue-tip trill to pronounce correctly?"
      explanation: "The letter Р requires a trill from the tip of your tongue."
      options:
        - text: "Р"
          correct: true
        - text: "Д"
          correct: false
        - text: "К"
          correct: false
        - text: "В"
          correct: false
    - question: "Which letter represents the d sound, resembling a small house on legs?"
      explanation: "The letter Д looks like a house and makes a d sound."
      options:
        - text: "Д"
          correct: true
        - text: "Б"
          correct: false
        - text: "В"
          correct: false
        - text: "К"
          correct: false
    - question: "Which word correctly begins with the Cyrillic letter for the b sound?"
      explanation: "The word банан begins with the letter Б."
      options:
        - text: "банан"
          correct: true
        - text: "вода"
          correct: false
        - text: "рука"
          correct: false
        - text: "кіт"
          correct: false
    - question: "Which of the following letters is entirely phonetic friends with its English equivalent?"
      explanation: "The letter К looks and sounds exactly like the English K."
      options:
        - text: "К"
          correct: true
        - text: "Р"
          correct: false
        - text: "В"
          correct: false
        - text: "И"
          correct: false
    - question: "How should you physically prepare your mouth to pronounce the letter И?"
      explanation: "For the deep И sound, your jaw should be relaxed and slightly pulled back."
      options:
        - text: "Keep the jaw relaxed and slightly dropped"
          correct: true
        - text: "Pull the lips back into a wide smile"
          correct: false
        - text: "Round the lips forward in a tight circle"
          correct: false
        - text: "Bite the bottom lip lightly"
          correct: false

- type: true-false
  title: "Fact Check"
  instruction: "Decide if these statements about the Cyrillic alphabet are true or false."
  items:
    - statement: "The Cyrillic letter Р represents the p sound in Ukrainian."
      correct: false
      explanation: "The letter Р is a rolled r sound."
    - statement: "The Ukrainian letter В makes a sound similar to the English v."
      correct: true
      explanation: "The letter В looks like a B but sounds like a v or w."
    - statement: "The unstressed letter О in the word молоко sounds exactly like an a."
      correct: false
      explanation: "In Ukrainian, the letter О maintains its pure o sound even when unstressed."
    - statement: "The letter Д represents the d sound and looks like a small house."
      correct: true
      explanation: "Yes, Д makes the d sound and resembles a house."
    - statement: "To pronounce the letter І, you should pull your lips into a smile."
      correct: true
      explanation: "The dotted І is a high, sharp sound that requires smiling lips."
    - statement: "The letter И is pronounced exactly like the English letter ee."
      correct: false
      explanation: "И is a deep, relaxed sound, not a sharp ee sound."
    - statement: "The word вода starts with the Cyrillic letter В."
      correct: true
      explanation: "Вода begins with В, which sounds like v."
    - statement: "The letter Б looks exactly like the English B."
      correct: false
      explanation: "The letter В looks like an English B. The letter Б looks like a 6 with a flat top."

- type: anagram
  title: "Unscramble the Words"
  instruction: "Rearrange the letters to form words using the letters you know."
  items:
    - scrambled: "і к т"
      answer: "кіт"
    - scrambled: "о д а в"
      answer: "вода"
    - scrambled: "і д м"
      answer: "дім"
    - scrambled: "у к а р"
      answer: "рука"
    - scrambled: "о н і к"
      answer: "кіно"
    - scrambled: "н а б а н"
      answer: "банан"
    - scrambled: "о к о м л о"
      answer: "молоко"
    - scrambled: "и в с а л"
      answer: "слива"

- type: fill-in
  title: "Complete the Words"
  instruction: "Choose the correct missing letter to complete the Ukrainian word."
  items:
    - sentence: "The Ukrainian word for water (вода) starts with the letter ___."
      answer: "в"
      options:
        - "в"
        - "б"
        - "р"
        - "к"
      explanation: "Вода starts with the letter В."
    - sentence: "The Ukrainian word for cat (кіт) uses the vowel ___."
      answer: "і"
      options:
        - "і"
        - "и"
        - "о"
        - "а"
      explanation: "Кіт uses the sharp, smiling І."
    - sentence: "The Ukrainian word for banana (банан) starts with the letter ___."
      answer: "б"
      options:
        - "б"
        - "в"
        - "д"
        - "р"
      explanation: "Банан begins with the letter Б."
    - sentence: "The Ukrainian word for house (дім) starts with the letter ___."
      answer: "д"
      options:
        - "д"
        - "к"
        - "б"
        - "м"
      explanation: "Дім begins with the letter Д."
    - sentence: "The Ukrainian word for hand or arm (рука) starts with the letter ___."
      answer: "р"
      options:
        - "р"
        - "в"
        - "п"
        - "к"
      explanation: "Рука begins with the trilled Р."
    - sentence: "The Ukrainian word for milk (молоко) uses the pure vowel ___."
      answer: "о"
      options:
        - "о"
        - "а"
        - "и"
        - "і"
      explanation: "Молоко uses the pure vowel О."
    - sentence: "The Ukrainian word for cinema (кіно) uses the dotted vowel ___."
      answer: "і"
      options:
        - "і"
        - "и"
        - "о"
        - "у"
      explanation: "Кіно uses the dotted І."
    - sentence: "The Ukrainian word for fish (риба) uses the vowel ___."
      answer: "и"
      options:
        - "и"
        - "і"
        - "а"
        - "о"
      explanation: "Риба uses the deep, relaxed И."

- type: anagram
  title: "Unscramble the Short Words"
  instruction: "Rearrange the letters to form words you know."
  items:
    - scrambled: "а м а м"
      answer: "мама"
    - scrambled: "и с н"
      answer: "син"
    - scrambled: "а к м"
      answer: "мак"
    - scrambled: "и р с"
      answer: "рис"
    - scrambled: "р б а т"
      answer: "брат"
    - scrambled: "в о к в"
      answer: "вовк"
    - scrambled: "о л с в о"
      answer: "слово"
    - scrambled: "а к в а"
      answer: "кава"

- type: group-sort
  title: "Sort by Letter: В vs Б"
  instruction: "Sort the words based on whether they contain the letter В or the letter Б."
  groups:
    - name: "Words with В (v-sound)"
      items:
        - "вода"
        - "вовк"
        - "нива"
        - "слива"
        - "кава"
        - "слово"
    - name: "Words with Б (b-sound)"
      items:
        - "банан"
        - "риба"
        - "баба"
        - "брат"
        - "банк"
        - "бар"
```

### Vocabulary: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/vocabulary/the-cyrillic-code-ii.yaml`

```yaml
items:
  - lemma: "кіт"
    translation: "cat"
    pos: "noun"
    gender: "m"
  - lemma: "вода"
    translation: "water"
    pos: "noun"
    gender: "f"
  - lemma: "банан"
    translation: "banana"
    pos: "noun"
    gender: "m"
  - lemma: "молоко"
    translation: "milk"
    pos: "noun"
    gender: "n"
  - lemma: "рука"
    translation: "hand/arm"
    pos: "noun"
    gender: "f"
  - lemma: "кіно"
    translation: "cinema"
    pos: "noun"
    gender: "n"
  - lemma: "дім"
    translation: "house/home"
    pos: "noun"
    gender: "m"
  - lemma: "друг"
    translation: "friend"
    pos: "noun"
    gender: "m"
  - lemma: "брат"
    translation: "brother"
    pos: "noun"
    gender: "m"
  - lemma: "слива"
    translation: "plum"
    pos: "noun"
    gender: "f"
  - lemma: "риба"
    translation: "fish"
    pos: "noun"
    gender: "f"
  - lemma: "вовк"
    translation: "wolf"
    pos: "noun"
    gender: "m"
  - lemma: "мама"
    translation: "mother"
    pos: "noun"
    gender: "f"
  - lemma: "син"
    translation: "son"
    pos: "noun"
    gender: "m"
  - lemma: "мак"
    translation: "poppy"
    pos: "noun"
    gender: "m"
  - lemma: "рис"
    translation: "rice"
    pos: "noun"
    gender: "m"
  - lemma: "сила"
    translation: "strength"
    pos: "noun"
    gender: "f"
  - lemma: "дірка"
    translation: "hole"
    pos: "noun"
    gender: "f"
  - lemma: "міна"
    translation: "mine"
    pos: "noun"
    gender: "f"
  - lemma: "нива"
    translation: "field"
    pos: "noun"
    gender: "f"
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
FILE: curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md
FIND:
**Ма́ма і си́н. Вода́ і молоко́. Бана́н і сли́ва. Мак і рис. Кіт і ри́ба. Дім і ву́лиця. Брат і ка́ва.** 

(Mother and son. Water and milk. Banana and plum. Poppy and rice. Cat and fish. House and street. Brother and coffee. *Note: син means son, мак means poppy, рис means rice*). 
REPLACE:
**Ма́ма і си́н. Вода́ і молоко́. Бана́н і сли́ва. Мак і рис. Си́р і ковбаса́. Сова́ і вовк. Сло́во і ді́ло.** 

(Mother and son. Water and milk. Banana and plum. Poppy and rice. Cheese and sausage. Owl and wolf. Word and deed. *Note: син means son, мак means poppy, рис means rice, сир means cheese, ковбаса means sausage, сова means owl, діло means deed*). 
===SECTION_FIX_END===

===FRICTION_START===
**Phase**: Gemini Review Fix
**Step**: Applying targeted fixes
**Friction Type**: TEXT_NOT_FOUND
**Raw Error**: Target strings for Issues 1 and 3 were not found in the file contents.
**Self-Correction**: The phrase `Давайте почитаємо разом!` has already been corrected to `Почитаймо разом!` in the current file state. Additionally, the five formulaic transition sentences in the consonant subsections do not exist in the provided source code. I successfully applied the remaining fix (Issue 2) for the false phonics promise.
**Proposed Tooling Fix**: N/A
===FRICTION_END===


────────────────────────────────────────
✅ Gemini finished (1351 chars)
✅ Message sent to Claude (ID: 20152)
✓ Message 20152 acknowledged
   Auto-acknowledged reply #20152 (stdout delivery — no inbox accumulation)
⚠️  GitHub issue creation failed: could not add label: 'review-result' not found

✓ Message 20151 acknowledged

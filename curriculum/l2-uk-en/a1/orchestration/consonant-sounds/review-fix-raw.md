  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=34039 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
===REVIEW_START===

  [watchdog] Output resumed after 195s stall
**Content Quality Review**
- **Language & Tone**: The tone is extremely encouraging and supportive, perfectly matching the "Patient Supportive Tutor" persona. The explanations of phonetic concepts (voiced/voiceless, hard/soft) are simplified well for the A1 level. 
- **Plan Adherence**: The module follows the `content_outline` strictly. All required vocabulary words (хліб, зуб, дім, вовк, жук, шапка, гора, небо, рука, бабуся) are well integrated into the content and examples. I have also corrected two minor translation typos in the Reading Practice section ("там" instead of "there").
- **Pedagogy & Structure**: The progression from sonorants to voiced/voiceless pairs, and finally to hard/soft consonants is logical and well-paced. The "Golden Rule" (no devoicing) is highlighted clearly.
- **Activities**: The current activities YAML was truncated and had schema errors. I have fixed the schema for the `quiz` options (changing them from simple strings to proper objects with `text` keys) and added the missing 8th activity to meet the minimum density requirement of 8 activities. 

**Audit Fixes Applied**:
1. Fixed YAML Schema Violation: Updated the `quiz` activity (Hand-on-Throat Test) to use an array of objects for `options` instead of strings, resolving the "not of type 'object'" schema error. 
2. Fixed Missing Activity Types: Changed `multiple-choice` to `quiz` to correctly satisfy the `quiz` requirement from `meta.yaml`.
3. Fixed Activity Density: Restored the truncated items for the first quiz to reach 10 items, added a 6th activity (`Hard or Soft Consonants?` classify), a 7th activity (`Ukrainian Consonant Rules` quiz), and an 8th activity (`Vocabulary Matching` match-up) to fulfill the expected 8 activities minimum requirement (previously 7/8). 
===REVIEW_END===

===CONTENT_START===
## Вступ — Introduction

Welcome to Module 3! Hello and welcome back! You are doing an absolutely amazing job so far. You have already learned the beautiful, melodic Ukrainian vowels, and now it is time to explore the rest of the alphabet. In this lesson, your goal is to master the Ukrainian consonants. By the end of this module, you will be able to read and pronounce almost any basic Ukrainian word with confidence.

You might be wondering, what exactly is the difference between a vowel and a consonant? When you speak a vowel, your breath flows freely out of your mouth without any obstruction. But when you pronounce a consonant, the airflow is partially or completely blocked by your lips, your teeth, or your tongue. Think of vowels as the flesh and emotion of a word, while consonants provide the skeleton and structure. 

Don't worry if this seems like a lot of letters at first glance. You already know many of them because they look and sound exactly like their English counterparts. Others might look a bit different on the page, but your mouth already knows how to make the sounds. We will break them down into easy, manageable groups so you will never feel overwhelmed. Take your time, listen closely to the examples, and practice aloud as often as you can. You are building a very strong foundation, and your dedication is truly paying off!

## Сонорні — Sonorant Consonants

Let's start your journey with the sonorant consonants. In Ukrainian, sonorant consonants are special and incredibly important. They are always voiced, meaning you use your vocal cords to produce them. They ring out clearly, using much more voice than noise. Because they are so strong, you do not have to worry about them ever losing their voice, no matter where they appear in a word. 

Let's look at the letters in this powerful group:

### Літера М
[Anna Ohoiko — Ukrainian Lessons — М](https://www.youtube.com/watch?v=Ez95H4ibuJo)
The letter **М** makes the «m» sound, just like it does in English. Press your lips together and let your voice hum.
* **ма́ма** (mom)
* **мі́сто** (city)
* **молоко́** (milk)
* **мак** (poppy)

### Літера Н
[Anna Ohoiko — Ukrainian Lessons — Н](https://www.youtube.com/watch?v=vNUfiKHPYaU)
The letter **Н** looks exactly like an English «H», but it actually makes the «n» sound. This is a very common letter in Ukrainian, so you will see it everywhere. Press the tip of your tongue against your upper teeth.
* **не́бо** (sky)
* **ніс** (nose)
* **ні** (no)
* **сон** (dream)

### Літера Л
[Anna Ohoiko — Ukrainian Lessons — Л](https://www.youtube.com/watch?v=v6-3Xg52Buk)
The letter **Л** makes the «l» sound. It can look a bit like a little tent. When you say the Ukrainian hard **Л**, make sure the back of your tongue is slightly lowered, giving it a rich, deep sound.
* **ліс** (forest)
* **са́ло** (pork fat)

### Літера Р
[Anna Ohoiko — Ukrainian Lessons — Р](https://www.youtube.com/watch?v=fMGsQ5KPQgg)
The letter **Р** looks like an English «P», but it represents the rolled «r» sound. You need to flutter or roll your tongue against the roof of your mouth, right behind your front teeth. If you cannot roll your «r» yet, don't worry! Keep practicing, and it will come with time.
* **рука́** (hand)
* **ри́ба** (fish)
* **сир** (cheese)

### Літера В
[Anna Ohoiko — Ukrainian Lessons — В](https://www.youtube.com/watch?v=aFcvYfvQ2X4)
The letter **В** looks like an English «B», but it makes a «v» or sometimes a soft «w» sound. When it comes at the end of a word or before another consonant, it softens into a sound similar to the English «w».
* **вода́** (water)
* **вовк** (wolf)
* **ву́хо** (ear)

### Літера Й
[Anna Ohoiko — Ukrainian Lessons — Й](https://www.youtube.com/watch?v=aq0cjB90s3w)
The letter **Й** is the short «y» sound, exactly like the «y» at the end of the English word «boy». It is always short and brisk.
* **край** (edge/region)
* **мій** (my)

> [!tip]
> **Keep your voice strong!**
> When you say these words, let your voice resonate in your chest and throat. Ukrainian sonorants are very melodic and they give the language its musical quality. Speak proudly and loudly!

Let's practice your new words in a short dialogue. Read aloud and focus on your pronunciation. Remember to stress the vowels with the accent mark.

> **(Вдо́ма / At home)**
> — Ма́ма тут?
> — Так, ма́ма тут.
> — А вовк там?
> — Ні, вовк у лі́сі!

## Дзвінкі та глухі пари — Voiced and Voiceless Pairs

Now, let's look at the consonant pairs. In Ukrainian, many consonants come in pairs: one is voiced, and the other is voiceless. What does this mean for you? 
To feel a voiced consonant, place two fingers gently on your throat and say the «z» sound: zzzzz. You will feel a vibration. That is your vocal cords working! Now say the «s» sound: sssss. The vibration stops, and you only hear the air rushing out. That is a voiceless consonant.

> [!warning]
> **The Golden Rule of Ukrainian Consonants**
> In many languages, including Russian and German, voiced consonants become voiceless at the end of a word. In Ukrainian, **voiced consonants never lose their voice**. If a word ends in a voiced consonant, you must pronounce it loudly and clearly, keeping your vocal cords vibrating until the very end. For example, the word **зуб** (tooth) must end with a strong, vibrating «b» sound, never a «p».

Let's explore your consonant pairs.

### Літери Б та П
[Anna Ohoiko — Ukrainian Lessons — Б](https://www.youtube.com/watch?v=V1hxBE_JbGg)
[Anna Ohoiko — Ukrainian Lessons — П](https://www.youtube.com/watch?v=JksSjjxyW5Y)
The letter **Б** produces a strong vocalized labial sound, whereas **П** is entirely unvoiced. Both require identical lip positioning to produce, yet they yield completely different acoustic results.
* **бабу́ся** (grandma)
* **паву́к** (spider)
* **зуб** (tooth)
* **суп** (soup)

Notice the massive difference between **зуб** and **суп**. You must keep the vocal cords vibrating strongly in **зуб**. Do not let it turn into a whisper!

### Літери Д та Т
[Anna Ohoiko — Ukrainian Lessons — Д](https://www.youtube.com/watch?v=g4Bh-lqzd48)
[Anna Ohoiko — Ukrainian Lessons — Т](https://www.youtube.com/watch?v=m-jcLR_gK0k)
The letter **Д** represents a vibrating dental stop, while **Т** acts as its silent counterpart. When pronouncing these, press your tongue flat against the back of your upper teeth, deliberately avoiding the upper gum ridge (alveolar ridge) used in English.
* **дім** (house)
* **та́то** (dad)
* **вода́** (water)
* **стіл** (table)

### Літери З та С
[Anna Ohoiko — Ukrainian Lessons — З](https://www.youtube.com/watch?v=BhASNxitC1A)
[Anna Ohoiko — Ukrainian Lessons — С](https://www.youtube.com/watch?v=7UsFBgSL91E)
With **З**, your vocal cords create a noticeable buzzing effect, which is completely absent in the breathy **С**. Remember to maintain the buzz of **З** fully through to the absolute end of any word!
* **зуб** (tooth)
* **село́** (village)
* **сон** (dream)
* **сік** (juice)

### Літери Ж та Ш
[Anna Ohoiko — Ukrainian Lessons — Ж](https://www.youtube.com/watch?v=dIrGVcqPwqM)
[Anna Ohoiko — Ukrainian Lessons — Ш](https://www.youtube.com/watch?v=1D-6MIw3OXY)
Resembling a small insect visually, **Ж** delivers a rich, buzzing fricative similar to the 's' in "measure". Its purely unvoiced equivalent is **Ш**, matching the English 'sh' sound perfectly.
* **жук** (beetle)
* **ша́пка** (hat)
* **ка́ша** (porridge)

### Літери Г, Ґ, К, та Х
[Anna Ohoiko — Ukrainian Lessons — Г](https://www.youtube.com/watch?v=gVnclpSI0DU)
[Anna Ohoiko — Ukrainian Lessons — К](https://www.youtube.com/watch?v=J7sGEI4-xJo)
[Anna Ohoiko — Ukrainian Lessons — Х](https://www.youtube.com/watch?v=vpr58zJSJKc)
This group is very interesting. **Г** is a soft, throaty «h» sound, but it is voiced! You engage your vocal cords. **К** is the familiar voiceless «k» sound. **Х** is a strong, breathy, voiceless «ch» sound, like in the Scottish word «loch» or the German name «Bach». Finally, **Ґ** is the hard English «g» sound, though it is quite rare in Ukrainian.
* **гора́** (mountain)
* **хліб** (bread)
* **мак** (poppy)
* **ґа́нок** (porch)
* **кіт** (cat)

> [!culture]
> **Bread is Life**
> The word **хліб** (bread) is absolutely central to Ukrainian culture. It represents hospitality, survival, and life itself. Notice how it ends with the voiced consonant **Б**. Make sure you say the «b» clearly: **хліб**. It is a word that deserves a strong voice!

Let's read a short dialogue using your new pairs. Read it twice to build your confidence.

> **(На ку́хні / In the kitchen)**
> — Це суп?
> — Так, це суп.
> — А де хліб?
> — Хліб там.
> — А вода́ тут?
> — Так, вода́ тут.

You are doing great! Let's move on to the next exciting concept.

## Тверді та м'які — Hard and Soft Consonants

You have learned about voiced and voiceless consonants. Now, we will introduce a very important feature of Ukrainian pronunciation: consonants can be hard (тверді́) or soft (м'які́).

What does this actually mean for your mouth? When you pronounce a hard consonant, your tongue is in its normal, relaxed position. But when you pronounce a soft consonant, the middle of your tongue raises actively toward the roof of your mouth, adding a slight, almost hidden «y» sound right as you say the consonant. It is a smooth, gliding motion.

> [!note]
> **How do you know if a consonant is soft?**
> Look directly at the vowel that comes immediately after it! You have already learned the beautiful vowels **І**, **Я**, **Ю**, and **Є**. These are your special "softening" vowels. Whenever a consonant is followed by one of these, you must pronounce the consonant softly. If it is followed by **А**, **О**, **У**, **Е**, or **И**, the consonant remains hard.

Let's compare hard and soft sounds using words you are learning. Pay close attention to how your tongue moves.

* **Hard Л**: **са́ло** (pork fat) — The «l» is hard because it is followed by the neutral vowel «o». Your tongue stays flat.
* **Soft Л**: **лю́ди** (people) — The «l» is soft because it is followed by the softening vowel «ю». Your tongue lifts up to the roof of your mouth. Notice the difference in the feeling.
* **Soft Л**: **люк** (hatch) — Another excellent example of the soft «l» caused by the vowel «ю».

Let's look at more examples from your vocabulary list:
* **Hard З**: **зуб** (tooth) — The «u» keeps the consonant hard.
* **Soft С**: **сіль** (salt) — The «s» is soft because of the powerful «і». (And the «l» at the end is also soft, which we will learn more about in the future!).
* **Hard Ц**: We have **цибу́ля** (onion). The «ц» is hard because of the vowel «и». But look at the end of the word! The «л» is soft because it is followed by the «я».

Let's practice reading some more words where you must pay close attention to the vowels.
* **дім** (house) — You must make a soft «d» because of the «і».
* **не́бо** (sky) — You make a hard «n» because «е» does not soften the consonant before it.
* **бабу́ся** (grandma) — You must make a soft «s» because of the «я» at the end.

> [!practice]
> **Feel the profound difference**
> Say the word **са́ло** and then immediately say **лю́ди**. Can you feel exactly how your tongue moves up for the «l» in **лю́ди**? Take your time and practice this motion back and forth. It will make your Ukrainian sound incredibly natural and authentic!

## Читання — Reading Practice

You have learned so much vital information in this module! Let's put your excellent new skills to the test. Read the following sentences aloud. Pay very close attention to your voiced consonants at the ends of words, and watch out for your soft consonants. Read slowly at first, then try to read a little faster.

* **Це мій дім.** (This is my house.)
* **Там гора́ і ліс.** (There is a mountain and a forest there.)
* **Тут вовк і жук.** (Here is a wolf and a beetle.)
* **Це моя́ рука́.** (This is my hand.)
* **Бабу́ся там.** (Grandma is there.)
* **Де моя́ ша́пка?** (Where is my hat?)
* **Тут є хліб і вода́.** (Here is bread and water.)
* **Це сіль, а це цибу́ля.** (This is salt, and this is an onion.)
* **Це паву́к.** (This is a spider.)
* **Там є ґа́нок і люк.** (There is a porch and a hatch there.)

You are making wonderful, steady progress. Your reading is getting smoother and more confident with every single sentence. 

## Підсумок — Summary

Congratulations on completing this challenging and essential module! You have taken a huge step forward in your Ukrainian language journey. You should feel very proud of your incredible progress today. Don't worry if you still need to practice some of the new sounds. They will become easier and more natural the more you use them.

**Checklist — What you can do now:**
* You can easily identify and pronounce the beautiful sonorant consonants.
* You know the Golden Rule: voiced consonants like **Б**, **Д**, and **З** always keep their strong voice at the ends of words (like in **хліб** and **зуб**).
* You can recognize the distinct difference between voiceless and voiced consonant pairs.
* You understand the vital concept of hard and soft consonants, and you know exactly which vowels make a consonant soft.

Great job! In the next module, you will learn a few final special symbols to complete your alphabet knowledge. Keep up the fantastic work, you are doing brilliantly!
===CONTENT_END===

===ACTIVITIES_START===
- type: watch-and-repeat
  title: Pronunciation Practice
  items:
  - letter: М
    word: мама
    video: https://www.youtube.com/watch?v=Ez95H4ibuJo
    note: Press your lips together and let your voice hum.
  - letter: Н
    word: небо
    video: https://www.youtube.com/watch?v=vNUfiKHPYaU
    note: Press the tip of your tongue against your upper teeth.
  - letter: Л
    word: ліс
    video: https://www.youtube.com/watch?v=v6-3Xg52Buk
    note: Make sure the back of your tongue is slightly lowered for the hard Л.
  - letter: Р
    word: рука
    video: https://www.youtube.com/watch?v=fMGsQ5KPQgg
    note: Flutter or roll your tongue against the roof of your mouth.
  - letter: В
    word: вода
    video: https://www.youtube.com/watch?v=aFcvYfvQ2X4
    note: Makes a 'v' or sometimes a soft 'w' sound.
  - letter: Й
    word: мій
    video: https://www.youtube.com/watch?v=aq0cjB90s3w
    note: Always a short and brisk 'y' sound.
  - letter: Б
    word: бабуся
    video: https://www.youtube.com/watch?v=V1hxBE_JbGg
    note: Voiced 'b' sound. Keep it vibrating!
  - letter: П
    word: павук
    video: https://www.youtube.com/watch?v=JksSjjxyW5Y
    note: Voiceless 'p' sound.
  - letter: Д
    word: дім
    video: https://www.youtube.com/watch?v=g4Bh-lqzd48
    note: Voiced 'd'. Tongue touches the back of upper teeth.
  - letter: Т
    word: тато
    video: https://www.youtube.com/watch?v=m-jcLR_gK0k
    note: Voiceless 't'. Tongue touches the back of upper teeth.
  - letter: З
    word: зуб
    video: https://www.youtube.com/watch?v=BhASNxitC1A
    note: Voiced 'z'. Keep it buzzing to the end.
  - letter: С
    word: село
    video: https://www.youtube.com/watch?v=7UsFBgSL91E
    note: Voiceless 's' sound.
- type: classify
  title: Sort Consonant Types
  instruction: Розподіліть елементи за групами.
  categories:
  - label: Сонорні (Sonorant)
    items:
    - М
    - Н
    - Л
    - Р
    - В
  - label: Дзвінкі (Voiced)
    items:
    - Б
    - Д
    - З
    - Ж
    - Г
  - label: Глухі (Voiceless)
    items:
    - П
    - Т
    - С
    - Ш
    - К
- type: image-to-letter
  title: Match Picture to Starting Letter
  items:
  - emoji: 🪲
    answer: Ж
    distractors:
    - Ш
    - З
    note: жук starts with Ж
  - emoji: 🧢
    answer: Ш
    distractors:
    - Ж
    - С
    note: шапка starts with Ш
  - emoji: 🖐️
    answer: Р
    distractors:
    - П
    - В
    note: рука starts with Р
  - emoji: 👵
    answer: Б
    distractors:
    - П
    - В
    note: бабуся starts with Б
  - emoji: 🕷️
    answer: П
    distractors:
    - Б
    - Т
    note: павук starts with П
  - emoji: ⛰️
    answer: Г
    distractors:
    - Х
    - К
    note: гора starts with Г
  - emoji: 🍞
    answer: Х
    distractors:
    - Г
    - К
    note: хліб starts with Х
  - emoji: 🐺
    answer: В
    distractors:
    - Б
    - Ф
    note: вовк starts with В
- type: match-up
  title: Match Voiced and Voiceless Partners
  instruction: З'єднайте відповідні елементи.
  pairs:
  - left: Б
    right: П
  - left: Д
    right: Т
  - left: З
    right: С
  - left: Ж
    right: Ш
  - left: Г
    right: Х
  - left: Ґ
    right: К
- type: quiz
  title: Hand-on-Throat Test
  instruction: Виберіть правильний варіант.
  items:
  - question: Is the first sound in 'зуб' (З) voiced, voiceless, or sonorant?
    options:
    - text: Voiced (Дзвінкий)
    - text: Voiceless (Глухий)
    - text: Sonorant (Сонорний)
    answer: Voiced (Дзвінкий)
    explanation: З is a voiced consonant. Your vocal cords vibrate.
  - question: Is the first sound in 'суп' (С) voiced, voiceless, or sonorant?
    options:
    - text: Voiced (Дзвінкий)
    - text: Voiceless (Глухий)
    - text: Sonorant (Сонорний)
    answer: Voiceless (Глухий)
    explanation: С is a voiceless consonant. Only air rushes out.
  - question: Is the first sound in 'бабуся' (Б) voiced, voiceless, or sonorant?
    options:
    - text: Voiced (Дзвінкий)
    - text: Voiceless (Глухий)
    - text: Sonorant (Сонорний)
    answer: Voiced (Дзвінкий)
    explanation: Б is a voiced consonant.
  - question: Is the first sound in 'павук' (П) voiced, voiceless, or sonorant?
    options:
    - text: Voiced (Дзвінкий)
    - text: Voiceless (Глухий)
    - text: Sonorant (Сонорний)
    answer: Voiceless (Глухий)
    explanation: П is the voiceless partner to Б.
  - question: Is the first sound in 'дім' (Д) voiced, voiceless, or sonorant?
    options:
    - text: Voiced (Дзвінкий)
    - text: Voiceless (Глухий)
    - text: Sonorant (Сонорний)
    answer: Voiced (Дзвінкий)
    explanation: Д is a voiced consonant.
  - question: Is the first sound in 'тато' (Т) voiced, voiceless, or sonorant?
    options:
    - text: Voiced (Дзвінкий)
    - text: Voiceless (Глухий)
    - text: Sonorant (Сонорний)
    answer: Voiceless (Глухий)
    explanation: Т is the voiceless partner to Д.
  - question: Is the first sound in 'жук' (Ж) voiced, voiceless, or sonorant?
    options:
    - text: Voiced (Дзвінкий)
    - text: Voiceless (Глухий)
    - text: Sonorant (Сонорний)
    answer: Voiced (Дзвінкий)
    explanation: Ж is a voiced consonant.
  - question: Is the first sound in 'шапка' (Ш) voiced, voiceless, or sonorant?
    options:
    - text: Voiced (Дзвінкий)
    - text: Voiceless (Глухий)
    - text: Sonorant (Сонорний)
    answer: Voiceless (Глухий)
    explanation: Ш is a voiceless consonant.
  - question: Is the first sound in 'гора' (Г) voiced, voiceless, or sonorant?
    options:
    - text: Voiced (Дзвінкий)
    - text: Voiceless (Глухий)
    - text: Sonorant (Сонорний)
    answer: Voiced (Дзвінкий)
    explanation: Г is a voiced consonant.
  - question: Is the first sound in 'рука' (Р) voiced, voiceless, or sonorant?
    options:
    - text: Voiced (Дзвінкий)
    - text: Voiceless (Глухий)
    - text: Sonorant (Сонорний)
    answer: Sonorant (Сонорний)
    explanation: Р is a sonorant consonant.
- type: classify
  title: Hard or Soft Consonants?
  instruction: Розподіліть слова за типом приголосного.
  categories:
  - label: Твердий (Hard)
    items:
    - лук
    - зуб
    - сало
    - мама
  - label: М'який (Soft)
    items:
    - люк
    - сіль
    - люди
    - дім
- type: quiz
  title: Ukrainian Consonant Rules
  instruction: Виберіть правильну відповідь.
  items:
  - question: What happens to voiced consonants at the end of a word in Ukrainian?
    options:
    - text: They stay voiced
    - text: They become voiceless
    - text: They disappear
    answer: They stay voiced
    explanation: Voiced consonants never lose their voice at the end of a word.
  - question: How do you know if a consonant is soft?
    options:
    - text: Look at the vowel immediately after it
    - text: Look at the vowel before it
    - text: It's always marked with an apostrophe
    answer: Look at the vowel immediately after it
    explanation: Vowels like І, Я, Ю, Є make the preceding consonant soft.
  - question: Which of these vowels makes a consonant hard?
    options:
    - text: О
    - text: І
    - text: Ю
    answer: О
    explanation: А, О, У, Е, И keep the consonant hard.
  - question: Which letter represents a rolled or trilled 'r' sound?
    options:
    - text: Р
    - text: Л
    - text: Г
    answer: Р
    explanation: The letter Р makes a rolled 'r' sound.
  - question: Is the letter В always pronounced exactly like the English 'v'?
    options:
    - text: No, it can sound like a soft 'w'
    - text: Yes, always
    - text: No, it sounds like 'b'
    answer: No, it can sound like a soft 'w'
    explanation: At the end of words or before consonants, it softens.
  - question: How is the letter Х pronounced?
    options:
    - text: Like a breathy 'ch' (as in 'loch')
    - text: Like a hard 'k'
    - text: Like an English 'x'
    answer: Like a breathy 'ch' (as in 'loch')
    explanation: Х is a strong, voiceless 'ch' sound.
  - question: Which of these words contains a soft 'л'?
    options:
    - text: люди
    - text: сало
    - text: лук
    answer: люди
    explanation: The 'ю' makes the 'л' soft.
  - question: Which is the voiceless partner of Ж?
    options:
    - text: Ш
    - text: С
    - text: Х
    answer: Ш
    explanation: Ж and Ш form a voiced/voiceless pair.
- type: match-up
  title: Vocabulary Matching
  instruction: З'єднайте слово з перекладом.
  pairs:
  - left: бабуся
    right: grandma
  - left: хліб
    right: bread
  - left: вода
    right: water
  - left: гора
    right: mountain
  - left: жук
    right: beetle
  - left: павук
    right: spider
  - left: зуб
    right: tooth
  - left: дім
    right: house
===ACTIVITIES_END===

===VOCABULARY_START===
- word: мама
  translation: mom
  pos: noun
  example: Мама тут.
- word: місто
  translation: city
  pos: noun
  example: Це гарне місто.
- word: молоко
  translation: milk
  pos: noun
  example: Де молоко?
- word: мак
  translation: poppy
  pos: noun
  example: Це червоний мак.
- word: небо
  translation: sky
  pos: noun
  example: Небо блакитне.
- word: ніс
  translation: nose
  pos: noun
  example: Це мій ніс.
- word: ні
  translation: no
  pos: particle
  example: Ні, вовк у лісі!
- word: сон
  translation: dream
  pos: noun
  example: Це гарний сон.
- word: ліс
  translation: forest
  pos: noun
  example: Там гора і ліс.
- word: сало
  translation: pork fat
  pos: noun
  example: Це смачне сало.
- word: рука
  translation: hand
  pos: noun
  example: Це моя рука.
- word: риба
  translation: fish
  pos: noun
  example: Тут є риба.
- word: сир
  translation: cheese
  pos: noun
  example: Де сир?
- word: вода
  translation: water
  pos: noun
  example: Вода тут.
- word: вовк
  translation: wolf
  pos: noun
  example: Тут вовк і жук.
- word: вухо
  translation: ear
  pos: noun
  example: Це моє вухо.
- word: край
  translation: edge/region
  pos: noun
  example: Це мій рідний край.
- word: мій
  translation: my
  pos: pronoun
  example: Це мій дім.
- word: бабуся
  translation: grandma
  pos: noun
  example: Бабуся там.
- word: павук
  translation: spider
  pos: noun
  example: Це великий павук.
- word: зуб
  translation: tooth
  pos: noun
  example: Це мій зуб.
- word: суп
  translation: soup
  pos: noun
  example: Це гарячий суп.
- word: дім
  translation: house
  pos: noun
  example: Це мій дім.
- word: тато
  translation: dad
  pos: noun
  example: Тато тут.
- word: стіл
  translation: table
  pos: noun
  example: Де стіл?
- word: село
  translation: village
  pos: noun
  example: Це моє село.
- word: сік
  translation: juice
  pos: noun
  example: Де мій сік?
- word: жук
  translation: beetle
  pos: noun
  example: Тут вовк і жук.
- word: шапка
  translation: hat
  pos: noun
  example: Де моя шапка?
- word: каша
  translation: porridge
  pos: noun
  example: Це смачна каша.
- word: гора
  translation: mountain
  pos: noun
  example: Там гора і ліс.
- word: хліб
  translation: bread
  pos: noun
  example: Тут є хліб і вода.
- word: ґанок
  translation: porch
  pos: noun
  example: Там є ґанок і люк.
- word: кіт
  translation: cat
  pos: noun
  example: Це мій кіт.
- word: люди
  translation: people
  pos: noun
  example: Тут люди.
- word: люк
  translation: hatch
  pos: noun
  example: Там є ґанок і люк.
- word: сіль
  translation: salt
  pos: noun
  example: Це сіль, а це цибуля.
- word: цибуля
  translation: onion
  pos: noun
  example: Це цибуля.
===VOCABULARY_END===

# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 1: Sounds, Letters, and Hello (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Claude Opus
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-001
level: A1
sequence: 1
slug: sounds-letters-and-hello
version: '1.0'
title: Sounds, Letters, and Hello
subtitle: "33 літери, 38 звуків, Привіт!"
focus: phonetics
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Understand the difference between sounds (звуки) and letters (літери)
- Recognize the two families of sounds — vowels (голосні) and consonants (приголосні)
- Read your first Ukrainian words using Cyrillic letters
- Say hello and respond to a greeting
content_outline:
- section: "Звуки і літери (Sounds and Letters)"
  words: 250
  points:
  - "Golden rule from Большакова Grade 1 p.24 and Заболотний Grade 5 p.73:
    'Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери.'
    33 letters (літери), 38 sounds (звуки). Letters are symbols on paper.
    Sounds are what we hear and pronounce."
  - "Two families of sounds:
    Голосні (vowels) — made with voice only, mouth open, no obstruction.
    Большакова teaches with a poem: 'Голосні почуєш в пісні.'
    6 vowel sounds: [а], [о], [у], [е], [и], [і].
    10 vowel letters: А, О, У, Е, И, І, Я, Ю, Є, Ї."
  - "Приголосні (consonants) — made with voice + noise or noise only.
    Lips, teeth, tongue create obstruction. 32 consonant sounds.
    Большакова: 'Приголосні деренчать, і тихенько шелестять.'"
- section: "Перші слова (First Words)"
  words: 300
  points:
  - "Some Cyrillic letters look like Latin but may sound different.
    Start with letters that look AND sound familiar: А, О, К, М, Т.
    Read immediately: мама, тато, кома, атом, мак, око.
    Important: Ukrainian Т is dental (tongue touches teeth, not gum ridge)
    and К/Т are unaspirated (no puff of air). Close enough for now."
  - "False friend letters — the biggest trap for English speakers:
    В sounds [в] (not 'b'), Н sounds [н] (not 'h'),
    Р sounds [р] rolled (not 'p'), С sounds [с] (not 'c/k'),
    У sounds [у] (not 'y'), Х sounds [х] (not 'x').
    Practice: вода (water), рука (hand), сон (dream), ніс (nose), хата (house)."
  - "New shapes — letters with no Latin equivalent:
    Б, Г, Ґ, Д, Ж, З, И, Й, Л, П, Ф, Ц, Ч, Ш, Щ.
    Through words: банк, дім, зима, книга, школа.
    Щ always makes TWO sounds [шч]. Ь has NO sound (softens the consonant before it)."
  - "Special: Ї always = [йі], never softens. Unique to Ukrainian.
    Я, Ю, Є can be two sounds OR soften a consonant.
    Full exploration in M02 — for now, just recognize them."
- section: "Привіт! (Hello!)"
  words: 250
  points:
  - "Following Anna Ohoiko ULP Episode 1 — your first conversation.
    Привіт! — Hi! (informal, use with friends, family, peers).
    Як справи? — How are you? Answers: Добре. Чудово. Нормально.
    А у тебе? — And you?"
  - "Рада тебе бачити! (female) / Радий тебе бачити! (male) — Glad to see you!
    Note: Ukrainian has gendered forms. Women say рада, men say радий.
    This is your first encounter with gender in Ukrainian — it will become
    a major topic starting M08."
  - "Reading practice with the greeting:
    Read each letter, blend into syllables: При-віт!
    This word uses letters from all groups:
    П (new), р (false friend!), и (new vowel), в (false friend!), і (vowel), т (familiar)."
- section: "Читаємо (Reading Practice)"
  words: 250
  points:
  - "Environmental reading — signs you see in Ukraine:
    Аптека (pharmacy), Банк (bank), Кафе (cafe), Метро (metro),
    Пошта (post office), Школа (school), Зупинка (bus stop).
    Sound out each letter, blend into syllables, read the whole word."
  - "Ukrainian city names:
    Київ, Львів, Одеса, Харків, Дніпро, Полтава."
  - "First sentences with Це (this is):
    Це мама. Це банк. Це Київ. Що це? Хто це?"
- section: "Підсумок — Summary"
  words: 150
  points:
  - "Self-check: How many letters? How many sounds? Why are they different?
    What are голосні? What are приголосні?
    What does Привіт mean? How do you respond to Як справи?"
vocabulary_hints:
  required:
  - мама (mother)
  - тато (father)
  - вода (water)
  - рука (hand)
  - книга (book)
  - школа (school)
  - привіт (hi, informal)
  - як справи (how are you)
  - добре (fine, good)
  - чудово (great, wonderful)
  recommended:
  - банк (bank)
  - аптека (pharmacy)
  - метро (metro)
  - пошта (post office)
  - зупинка (bus stop)
  - нормально (okay)
activity_hints:
- type: quiz
  focus: "Sound or letter? (звук чи літера?)"
  items: 6
- type: match-up
  focus: "Match false friend letters to their REAL sounds"
  items: 6
- type: fill-in
  focus: "Complete the greeting dialogue"
  items: 4
- type: group-sort
  focus: "Sort into голосні vs приголосні"
  items: 8
connects_to:
- a1-002 (Reading Ukrainian)
prerequisites: []
grammar:
- "Звуки vs літери — 33 letters, 38 sounds"
- "Голосні (6 sounds, 10 letters) vs приголосні (32 sounds)"
- "Cyrillic letter-sound mapping (familiar, false friends, new shapes)"
- "Привіт greeting as first spoken Ukrainian"
register: розмовний
references:
- title: "Большакова Grade 1 буквар, p.24"
  notes: "Голосні/приголосні taught through poems. 'Голосні почуєш в пісні.'"
- title: "Захарійчук Grade 1 буквар (NUS 2025), p.13"
  notes: "Sound notation: [•] for vowels, [–] for consonants."
- title: "Заболотний Grade 5, p.73"
  notes: "38 звуків: 6 голосних + 32 приголосні."
- title: "ULP Season 1, Episode 1 — Informal Greetings"
  url: https://www.ukrainianlessons.com/episode1/
  notes: "Привіт, Як справи?, response patterns."
pronunciation_videos:
  overview: https://www.youtube.com/watch?v=ksXIXj7CXwc
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

</plan_content>

## Generated Content

<generated_module_content>
<!-- TAB:Урок -->

## Зву́ки і лі́тери (Sounds and Letters)

Look at the text on this page. What you see are letters — symbols printed on a screen. Now say a word out loud. Anything. What you just produced are sounds — vibrations in the air. This distinction is the absolute foundation of how Ukrainian teaches its own language. Every Ukrainian first-grader learns a golden rule:

> **Ми чу́ємо і вимовля́ємо звуки, а ба́чимо і пи́шемо літери.**

We hear and pronounce sounds. We see and write letters. Sounds and letters are not the same thing. The Ukrainian alphabet has 33 letters (**літери**), but the language uses 38 sounds (**звуки**). Why the mismatch? Because some letters represent more than one sound, and one special letter — **Ь** — represents no sound at all. It only softens the consonant before it.

Ukrainian sounds split into two families. The first family is **голосні́** — vowels. These are sounds made with voice alone. Your mouth stays open, nothing blocks the air. A poem from Ukrainian first-grade textbooks captures it perfectly: «Голосні почу́єш в пісні́» — you hear vowels in a song. There are 6 vowel sounds, but 10 vowel letters. The six sounds are the pure ones: the sounds behind **А**, **О**, **У**, **Е**, **И**, **І**. The four extra letters — **Я**, **Ю**, **Є**, **Ї** — are special. They can represent two sounds at once or soften a preceding consonant. More on those in Module 2.

The second family is **при́голосні** — consonants. These sounds are made when something in your mouth — lips, teeth, tongue — creates an obstruction. Air hits a barrier. Another textbook poem: «Приголосні деренча́ть, і тихе́нько шелестя́ть» — consonants rattle and quietly rustle. There are 32 consonant sounds in Ukrainian.

:::quiz
title: "Звук чи лі́тера?"
---
- q: "What do we hear and pronounce?"
  o: ["звуки (sounds)", "літери (letters)", "слова́ (words)"]
  a: 0
- q: "What do we see and write?"
  o: ["літери (letters)", "звуки (sounds)", "речення (sentences)"]
  a: 0
- q: "How many letters does Ukrainian have?"
  o: ["33", "38", "26"]
  a: 0
- q: "How many vowel sounds are there?"
  o: ["6", "10", "8"]
  a: 0
- q: "Which family of sounds is made with voice alone, mouth open?"
  o: ["голосні", "приголосні", "літери"]
  a: 0
- q: "Why does Ukrainian have more sounds than letters?"
  o: ["Some letters represent more than one sound", "Some sounds have no letters", "Ukrainian borrowed extra sounds"]
  a: 0
:::

## Пе́рші слова (First Words)

Some Cyrillic letters look identical to Latin ones — and some of those even sound similar. Start with the friendliest group: **А**, **О**, **К**, **М**, **Т**. These look familiar and sound close enough to what you expect. With just these five letters, you can already read real Ukrainian words:

> **Ма́ма.** **Та́то.** **Мак.** **Око́.** **А́том.**

**Мама** — mother. **Тато** — father. **Мак** — poppy (the national flower you see on Ukrainian embroidery). **Око** — eye (a poetic word). **Атом** — atom. You are reading Ukrainian.

One small detail: Ukrainian **Т** is dental — your tongue touches the back of your teeth, not the gum ridge behind them. And **К** and **Т** have no puff of air after them, unlike English. Close enough for now. You will refine this naturally.

### False Friends — The Biggest Trap

Now for the letters that will trick you. These look like Latin letters but make completely different sounds:

| Letter | Looks like | Actually sounds like |
|--------|-----------|---------------------|
| **В** | B | **В** as in "vest" |
| **Н** | H | **Н** as in "no" |
| **Р** | P | **Р** — a rolled "r" |
| **С** | C | **С** as in "sun" |
| **У** | Y | **У** as in "moon" |
| **Х** | X | **Х** like "ch" in Scottish "loch" |

Read these words carefully, fighting every instinct to use English sounds:

> **Вода́.** **Рука́.** **Сон.** **Ніс.** **Ха́та.**

**Вода** — water (not "boda"). **Рука** — hand (not "pyka"). **Сон** — dream. **Ніс** — nose. **Хата** — a traditional Ukrainian house.

:::match-up
title: "Match false friend letters to their real sounds"
---
- left: "В"
  right: "sounds like V in 'vest'"
- left: "Н"
  right: "sounds like N in 'no'"
- left: "Р"
  right: "a rolled R sound"
- left: "С"
  right: "sounds like S in 'sun'"
- left: "У"
  right: "sounds like OO in 'moon'"
- left: "Х"
  right: "sounds like CH in Scottish 'loch'"
:::

### New Shapes

Finally, there are letters with no Latin look-alike at all: **Б**, **Г**, **Ґ**, **Д**, **Ж**, **З**, **И**, **Й**, **Л**, **П**, **Ф**, **Ц**, **Ч**, **Ш**, **Щ**. Do not try to memorize them in a list. Learn them through words:

> **Банк.** **Дім.** **Зима́.** **Кни́га.** **Шко́ла.**

**Банк** — bank. **Дім** — home, house. **Зима** — winter. **Книга** — book. **Школа** — school. Notice how **Щ** always makes two sounds together — like "shch" blended quickly. And remember **Ь** — the soft sign — has no sound of its own. It only tells you to soften the consonant before it, as in **дім** (the **Ь** is hiding inside the letter **і** here, but you will meet it clearly in words like **день** — day).

One more special letter: **Ї** always represents two sounds blended together. It is unique to Ukrainian — no other Slavic language has it. The letters **Я**, **Ю**, **Є** can also represent two sounds or soften a consonant, but that is a story for Module 2.

:::group-sort
title: "Sort these letters: голосні чи приголосні?"
---
groups:
  - name: "Голосні (vowels)"
    items: ["А", "О", "У", "І"]
  - name: "Приголосні (consonants)"
    items: ["М", "К", "Б", "Ш"]
:::

## Приві́т! (Hello!)

Time for your first Ukrainian conversation. Two friends meet on the street:

> — **Привіт!**
> — **Привіт! Як спра́ви?**
> — **До́бре. А у тебе́?**
> — **Чудо́во!**

**Привіт** — hi. This is informal, used with friends, family, people your age. **Як справи?** — how are you? (literally: how are things?). The answers:

| Ukrainian | English |
|-----------|---------|
| **Добре.** | Fine. Good. |
| **Чудово!** | Great! Wonderful! |
| **Норма́льно.** | Okay. Not bad. |

After answering, bounce the question back: **А у тебе?** — and you?

:::tip
Ukrainian has gendered speech. A woman says **ра́да тебе ба́чити** (glad to see you), a man says **ра́дий тебе бачити**. This is your very first encounter with grammatical gender — it will become a major topic starting in Module 8. For now, just notice that the endings are different.
:::

Now, look at the word **привіт** letter by letter. It uses letters from every group you have learned:

- **П** — new shape (no Latin equivalent)
- **Р** — false friend (not "P"!)
- **И** — new vowel (no English match — between "i" and "e")
- **В** — false friend (not "B"!)
- **І** — vowel (like "ee" in "see")
- **Т** — familiar (dental, remember?)

Reading this one word is a workout through the entire alphabet system.

:::fill-in
title: "Complete the greeting"
---
- sentence: "— Привіт! Як ___?"
  answer: "справи"
- sentence: "— Добре. А у ___?"
  answer: "тебе"
- sentence: "— ___! Рада тебе бачити!"
  answer: "Привіт"
- sentence: "— Як справи? — ___."
  answer: "Чудово"
:::

## Чита́ємо (Reading Practice)

You are now walking through a Ukrainian city. Signs surround you. Sound out each letter, blend them into syllables, read the whole word:

> **Апте́ка.** **Банк.** **Кафе́.** **Метро́.** **По́шта.** **Школа.** **Зупи́нка.**

**Аптека** — pharmacy. **Банк** — bank. **Кафе** — cafe. **Метро** — metro. **Пошта** — post office. **Школа** — school. **Зупинка** — bus stop. These are the signs you will see every day in Ukraine. Notice that some words look nearly identical to English (**банк**, **метро**, **кафе**) — these are international words that Ukrainian absorbed and adapted.

### Ukrainian Cities

Now read the names of real Ukrainian cities:

> **Ки́їв.** **Львів.** **Оде́са.** **Харків.** **Дніпро́.** **Полта́ва.**

**Київ** — Kyiv, the capital. **Львів** — Lviv, the cultural heart of western Ukraine. **Одеса** — Odesa, the Black Sea port. **Харків** — Kharkiv, the eastern metropolis. **Дніпро** — Dnipro, named after the great river. **Полтава** — Poltava, famous for its history and its Ukrainian dialect considered the "purest."

### First Sentences

Ukrainian has a powerful little word: **це** — "this is." With it, you can make your first sentences:

> **Це мама.** **Це банк.** **Це Київ.**

To ask questions: **Що це?** — what is this? **Хто це?** — who is this? **Що** is for things, **хто** is for people.

> — **Що це?**
> — **Це школа.**
> — **Хто це?**
> — **Це мама.**

:::true-false
title: "True or false?"
---
- statement: "The Ukrainian alphabet has 33 letters."
  answer: true
- statement: "There are more vowel sounds than consonant sounds in Ukrainian."
  answer: false
- statement: "The letter В sounds like B in English."
  answer: false
- statement: "Привіт is a formal greeting."
  answer: false
- statement: "Що це? means 'What is this?'"
  answer: true
:::


### Відео — Video

<YouTubeVideo client:only="react" url="https://www.youtube.com/watch?v=ksXIXj7CXwc" label="Overview — Ukrainian Lessons" />

[Повний плейлист / Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)


## Підсумок — Summary

You have learned the foundation of the Ukrainian sound system. 33 **літери** on paper, 38 **звуки** in the air. Letters are what you see and write. Sounds are what you hear and pronounce. **Голосні** — vowels — are made with voice alone: six sounds, ten letters. **Приголосні** — consonants — are made when your mouth creates an obstruction: 32 sounds.

You can now read Ukrainian words using three groups of letters: familiar ones (**А**, **О**, **К**, **М**, **Т**), false friends that look Latin but sound different (**В**, **Н**, **Р**, **С**, **У**, **Х**), and new shapes with no Latin equivalent (**Б**, **Д**, **Ж**, **З**, **Ш**, **Щ**).

You know your first greeting: **Привіт! Як справи? — Добре!** You can read city signs: **аптека**, **банк**, **школа**, **метро**. You can build simple sentences with **це**: **Це Київ. Що це? Хто це?**


<!-- TAB:Словник -->

### Обов'язкові слова — Required words

| Слово | Translation |
|-------|-------------|
| **мама** | mother |
| **тато** | father |
| **вода** | water |
| **рука** | hand |
| **книга** | book |
| **школа** | school |
| **привіт** | hi, informal |
| **як справи** | how are you |
| **добре** | fine, good |
| **чудово** | great, wonderful |

### Рекомендовані слова — Recommended words

| Слово | Translation |
|-------|-------------|
| **банк** | bank |
| **аптека** | pharmacy |
| **метро** | metro |
| **пошта** | post office |
| **зупинка** | bus stop |
| **нормально** | okay |


<!-- TAB:Зошит -->

:::note
Розширені вправи для цього уроку ще в розробці.

Advanced exercises for this module are in development. Check back soon!
:::


<!-- TAB:Ресурси -->

- Большакова Grade 1 буквар, p.24
  _Голосні/приголосні taught through poems. 'Голосні почуєш в пісні.'_
- Захарійчук Grade 1 буквар (NUS 2025), p.13
  _Sound notation: [•] for vowels, [–] for consonants._
- Заболотний Grade 5, p.73
  _38 звуків: 6 голосних + 32 приголосні._
- [ULP Season 1, Episode 1 — Informal Greetings](https://www.ukrainianlessons.com/episode1/)
  _Привіт, Як справи?, response patterns._
</generated_module_content>

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

Check for:
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Russianisms (кот→кіт, хорошо→добре, конечно→звичайно)
- Surzhyk (шо→що, чо→чому)
- Calques (приймати душ→брати душ)
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture
  - If you suspect a factual or phonetic error but are not 100% certain, flag it as `[NEEDS RAG VERIFICATION]` rather than marking it as critical/major

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

List every exercise block (`:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, `:::true-false`). These are filled exercises — a deterministic tool converted placeholders to real content.

For each exercise, check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?
- Are there enough items per exercise? (check against plan's `activity_hints`)

Also check: Are there enough exercises total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercises are generated by a deterministic tool from the writer's placeholders. If the exercise LOGIC is wrong (e.g., matching unrelated items), flag it — the tool's input data needs fixing. If the exercise FORMAT looks unusual, that is expected (the tool uses a specific DSL syntax).

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | Every content_outline point covered? Section word budgets respected (±10%)? All plan references used? |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | PPP (Present→Practice→Produce) applied? Textbook pedagogy used (Большакова, Захарійчук)? Grammar scope respected (no A2 in A1)? |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | Placeholders specific enough? Test the right skills? Placed after relevant teaching? Match plan's activity_hints? Sufficient items? |
| 6 | **Engagement & tone** | 10% | Interesting for teens/adults? Authoritative but warm (like a skilled teacher)? No LLM filler ("Good news!", "Don't panic!", "Fun fact!")? Cultural hooks? |
| 7 | **Structural integrity** | 5% | All H2 headings from plan present? Word count in range? No duplicate sections? No meta-commentary? Clean markdown? |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | Dialogues natural and culturally appropriate? Real situations, real responses? Speaker roles clear? Not stilted or textbook-robotic? |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence.

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Critical = module cannot ship. Major = quality below standard. Minor = polish item.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero critical findings, at most minor issues |
| **REVISE** | Has major findings but no criticals — fixable without rewrite |
| **REJECT** | Has any critical finding — fundamental problems requiring rewrite |

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]
```

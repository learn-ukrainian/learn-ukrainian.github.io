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

Look at the text on this page. What you see are marks on a screen — symbols, shapes, ink. Now say a word out loud — any word. What you just produced are sounds: vibrations of air shaped by your mouth, tongue, and throat. This distinction between what we see and what we hear is the absolute foundation of the Ukrainian language.

Every Ukrainian child learns a golden rule in first grade. It comes from Большако́ва's Grade 1 primer, page 24, and it goes like this: **Ми чу́ємо і вимовля́ємо звуки, а ба́чимо і пи́шемо літери.** We hear and pronounce sounds, but we see and write letters. Sounds and letters are not the same thing. Ukrainian has 33 letters in its alphabet, but 38 distinct sounds. The mismatch matters — some letters represent more than one sound, and some sounds have no letter of their own. That gap between 33 and 38 will become clearer as you progress, but for now, hold onto this: letters live on paper, sounds live in the air.

Ukrainian sounds split into two families. The first family is **голосні́** — vowels. These are sounds made with voice alone. Your mouth stays open, the air flows freely, nothing blocks it. A poem from Grade 1 captures this perfectly: **Голосні почу́єш в пісні́** — "You hear vowels in a song." Ukrainian has 6 vowel sounds but 10 vowel letters. The six sounds are **а**, **о**, **у**, **е**, **и**, **і**. The ten letters that represent them are **А**, **О**, **У**, **Е**, **И**, **І**, **Я**, **Ю**, **Є**, **Ї**. Why ten letters for six sounds? Because **Я**, **Ю**, **Є**, and **Ї** do double duty — they can represent two sounds at once, or soften the consonant before them. That is a story for Module 2. For now, just recognize all ten.

The second family is **при́голосні** — consonants. These sounds are made when something in your mouth creates an obstacle: your lips press together, your tongue touches your teeth, or air squeezes through a narrow gap. Voice may or may not be involved — some consonants buzz with voice, others are just a whisper of noise. Another line from the same poem describes them: **Приголосні деренча́ть і тихе́нько шелестя́ть** — "Consonants rattle and quietly rustle." Ukrainian has 32 consonant sounds. One special letter, **Ь** (the soft sign), makes no sound at all — it only tells you to soften the consonant before it. Think of it as a silent instruction to the reader's tongue.

:::quiz
title: "Звук чи лі́тера?"
---
- q: "What do we hear and pronounce?"
  o: ["звуки (sounds)", "літери (letters)", "слова́ (words)"]
  a: 0
- q: "What do we see and write?"
  o: ["літери (letters)", "звуки (sounds)", "речення (sentences)"]
  a: 0
- q: "How many letters are in the Ukrainian alphabet?"
  o: ["33", "38", "26"]
  a: 0
- q: "How many distinct sounds does Ukrainian have?"
  o: ["38", "33", "32"]
  a: 0
- q: "What does the soft sign Ь do?"
  o: ["Softens the consonant before it", "Makes a vowel sound", "Adds a pause between words"]
  a: 0
- q: "How many vowel sounds are there in Ukrainian?"
  o: ["6", "10", "8"]
  a: 0
:::

:::group-sort
title: "Голосні чи приголосні? (Vowels or consonants?)"
---
groups:
  - name: "Голосні (vowels)"
    items: ["А", "О", "У", "І"]
  - name: "Приголосні (consonants)"
    items: ["М", "К", "Б", "Ш"]
:::

## Пе́рші слова (First Words)

Some Cyrillic letters look exactly like Latin ones — and luckily, a few of them even sound similar. These friendly letters are your starting point: **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words right now.

Look at the word **ма́ма**. It means "mother," and you already know every letter in it. Now look at **та́то** — "father." Two letters, repeated, and the word is yours. Here are more words you can already read: **ко́ма** (comma), **а́том** (atom), **мак** (poppy), **о́ко** (eye), **там** (there), **тут** (here). Read each one out loud. Notice something important: Ukrainian **Т** is pronounced with your tongue touching the back of your upper teeth — not the gum ridge as in English. And both **К** and **Т** have no puff of air after them. Hold your hand in front of your mouth and say the English word "top" — you feel a burst of air. The Ukrainian **тато** has none. This is close enough for now, but worth noticing early.

### False friends — the biggest trap

Now the dangerous part. Several Cyrillic letters look identical to Latin letters but make completely different sounds. These are false friends, and they will trip you up if you read them the English way.

**В** looks like B, but sounds like "v" in "vest." The word **вода́** means "water" — say it as "voda," not "boda."

**Н** looks like H, but sounds like "n" in "no." The word **ніс** means "nose."

**Р** looks like P, but is a rolled "r." The word **рука́** means "hand."

**С** looks like C, but always sounds like "s" in "sun." The word **сон** means "dream."

**У** looks like Y, but sounds like "oo" in "moon."

**Х** has no exact English match — it sounds like "ch" in Scottish "loch." The word **ха́та** means "house" or "cottage."

### New shapes

Finally, some letters have shapes you have never seen: **Б**, **Г**, **Ґ**, **Д**, **Ж**, **З**, **И**, **Й**, **Л**, **П**, **Ф**, **Ц**, **Ч**, **Ш**, **Щ**. No Latin lookalikes, no confusion — just new shapes to learn. Meet a few through words: **банк** (bank), **дім** (home), **зима́** (winter), **кни́га** (book), **шко́ла** (school). Notice that **Щ** always makes two sounds blended together — "shch." And remember **Ь**, the soft sign — it has no sound of its own but changes how the consonant before it is pronounced.

One letter is uniquely Ukrainian: **Ї**. No other Slavic language has it. It always makes two sounds together. The letters **Я**, **Ю**, and **Є** can also represent two sounds, or they can soften a consonant before them — but that full story belongs to Module 2. For now, simply recognize these letters when you see them.

:::match-up
title: "False friend letters — match to their REAL sounds"
---
- left: "В"
  right: "sounds like «v» in vest"
- left: "Н"
  right: "sounds like «n» in no"
- left: "Р"
  right: "a rolled «r»"
- left: "С"
  right: "sounds like «s» in sun"
- left: "У"
  right: "sounds like «oo» in moon"
- left: "Х"
  right: "sounds like «ch» in loch"
:::

## Приві́т! (Hello!)

Time for your first Ukrainian conversation. Imagine you are meeting a friend on the street in Kyiv. What do you say?

> — **Привіт!**
> — **Привіт! Як спра́ви?**
> — **До́бре! А у тебе́?**
> — **Чудо́во!**

That is a complete greeting in Ukrainian. Let's break it apart.

**Привіт** means "hi" — informal, warm, for friends, family, and people your age. You would not say it to your professor or a stranger much older than you. For those situations, Ukrainian has formal greetings — but those come later, in Module 4.

**Як справи?** means "how are you?" — literally "how are things?" The most common answers are: **Добре** (fine, good), **Чудово** (wonderful, great), and **Норма́льно** (okay, all right). After you answer, you bounce the question back: **А у тебе?** — "And you?"

There is one more phrase worth learning now: **Ра́да тебе ба́чити!** means "glad to see you!" — but only if the speaker is a woman. A man says **Ра́дий тебе бачити!** This is your very first encounter with something that runs through the entire Ukrainian language: grammatical gender. A woman uses the ending **-а** (рад**а**), a man uses **-ий** (рад**ий**). Gender will become a major topic starting in Module 8, but notice it now — it is everywhere.

Now go back and read the word **Привіт** letter by letter. This one word uses letters from all three groups you just learned. **П** is a new shape. **р** is a false friend — remember, it is a rolled "r," not "p." **и** is a vowel unique to Ukrainian. **в** is another false friend — "v," not "b." **і** is a vowel. **т** is familiar from **тато**. Six letters, three groups, one word. You are already reading Ukrainian.

:::fill-in
title: "Complete the greeting"
---
- sentence: "___! Як справи?"
  answer: "Привіт"
- sentence: "Як справи? — ___, дякую."
  answer: "Добре"
- sentence: "А у ___?"
  answer: "тебе"
- sentence: "Як справи? — ___!"
  answer: "Чудово"
:::

## Чита́ємо (Reading Practice)

You know enough letters now to read real Ukrainian words — words you would see on signs, buildings, and maps across Ukraine. This is environmental reading: learning to decode the world around you.

### Signs you see everywhere

Walk down any Ukrainian street and you will find these words on signs and storefronts. Sound out each letter, blend them into syllables, then read the whole word:

| Ukrainian | English | Syllables |
|-----------|---------|-----------|
| **Апте́ка** | pharmacy | Ап-те-ка |
| **Банк** | bank | Банк |
| **Кафе́** | café | Ка-фе |
| **Метро́** | metro | Мет-ро |
| **По́шта** | post office | Пош-та |
| **Школа** | school | Шко-ла |
| **Зупи́нка** | bus stop | Зу-пин-ка |

Notice how many of these words are international — **банк**, **метро**, **кафе** — the Cyrillic spelling is different, but the words themselves are recognizable. That is your shortcut: dozens of Ukrainian words are already familiar from English or other European languages. Others, like **зупинка** and **пошта**, are purely Ukrainian — you learn them fresh.

### Ukrainian cities

Every Ukrainian knows these city names. Practice reading them — they are on maps, road signs, train tickets, and the news:

**Ки́їв** (Kyiv), **Львів** (Lviv), **Оде́са** (Odesa), **Харків** (Kharkiv), **Дніпро́** (Dnipro), **Полта́ва** (Poltava).

Try sounding out **Київ**: **К** (familiar) + **и** (Ukrainian vowel) + **ї** (unique letter, two sounds) + **в** (false friend — "v"). Four letters, and you have just read the name of the capital.

### First sentences

Now put words together. Ukrainian has a wonderfully simple structure for pointing at things and naming them:

> **Це мама.** — This is mom.
> **Це банк.** — This is a bank.
> **Це Київ.** — This is Kyiv.

**Це** means "this is." To ask what something is, you say **Що це?** (What is this?). To ask who someone is: **Хто це?** (Who is this?). And to answer: **Це тато.** **Це школа.** **Це книга.** You now have a complete structure for identifying anything in the world around you. Point, name, done.

:::tip
When sounding out an unfamiliar word, go letter by letter from left to right. Find the vowels first — they are the peaks of each syllable. Then attach the consonants before and after each vowel. **Ап-те-ка**: three vowels, three syllables.
:::


### Відео — Video

<YouTubeVideo client:only="react" url="https://www.youtube.com/watch?v=ksXIXj7CXwc" label="Overview — Ukrainian Lessons" />

[Повний плейлист / Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)


## Підсумок — Summary

You have covered an enormous amount of ground in this first module. Here is what you now know:

**Sounds and letters** are different things. Ukrainian has 33 **літери** (letters) and 38 **зву́ків** (sounds). The golden rule: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери.**

Sounds split into two families: **голосні** (vowels) — 6 sounds, 10 letters, made with voice alone — and **приголосні** (consonants) — 32 sounds, made when something in the mouth blocks the air.

You learned three groups of Cyrillic letters: **familiar** ones (А, О, К, М, Т), **false friends** (В, Н, Р, С, У, Х — they look like Latin letters but sound completely different), and **new shapes** (Б, Г, Д, Ж, Ш, and more).

You had your first Ukrainian conversation: **Привіт! Як справи? — Добре!** You noticed that Ukrainian has gendered forms: **рада** (female) vs. **радий** (male).

And you started reading real Ukrainian words — signs like **аптека** and **школа**, cities like **Київ** and **Львів**, and simple sentences with **Це**.

**Self-check:** How many letters? (33.) How many sounds? (38.) Why are they different? What are **голосні**? What are **приголосні**? What does **Привіт** mean? How do you answer **Як справи?**


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

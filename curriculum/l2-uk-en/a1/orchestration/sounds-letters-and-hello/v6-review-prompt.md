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
## Зву́ки і лі́тери (Sounds and Letters)

Look at the text on this page. What you see are letters — symbols printed on a screen. Now say a word out loud. What you just produced are sounds — vibrations in the air. This distinction is the absolute foundation of Ukrainian, and every Ukrainian first-grader learns a golden rule:

> **Ми чу́ємо і вимовля́ємо звуки, а ба́чимо і пи́шемо літери.**

We hear and pronounce sounds, but we see and write letters. In Ukrainian, the word for a sound is **звук** (plural: **звуки**), and the word for a letter is **лі́тера** (plural: **літери**). Ukrainian has 33 letters but 38 sounds. Why the mismatch? Because some letters can represent more than one sound, and some sounds have no letter of their own. You will discover these surprises gradually.

Sounds split into two families. The first family is **голосні́** — vowels. These are made with your voice alone: your mouth is open, air flows freely, nothing blocks it. A poem from Ukrainian first-grade textbooks captures this perfectly: *«Голосні почу́єш в пісні́»* — you hear vowels in a song. There are 6 vowel sounds in Ukrainian, but 10 vowel letters:

| Vowel sounds (6) | Vowel letters (10) |
|---|---|
| **а**, **о**, **у**, **е**, **и**, **і** | А, О, У, Е, И, І, Я, Ю, Є, Ї |

Why 10 letters for 6 sounds? The letters **Я**, **Ю**, **Є**, and **Ї** are special — they can represent two sounds at once or soften the consonant before them. That is a story for Module 2. For now, just know they exist.

The second family is **при́голосні** — consonants. These are made when something in your mouth — your lips, teeth, or tongue — blocks the airflow. Another first-grade poem says: *«Приголосні деренча́ть і тихе́нько шелестя́ть»* — consonants clatter and softly rustle. Ukrainian has 32 consonant sounds.

:::quiz
title: "Звук чи літера?"
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
- q: "How many sounds does Ukrainian have?"
  o: ["38", "33", "32"]
  a: 0
- q: "Which family of sounds is made with voice alone, mouth open?"
  o: ["голосні (vowels)", "приголосні (consonants)"]
  a: 0
- q: "Which poem line describes vowels?"
  o: ["«Голосні почуєш в пісні»", "«Приголосні деренчать»"]
  a: 0
:::

## Пе́рші слова (First Words)

### Familiar Faces

Some Ukrainian letters look exactly like Latin letters and make similar sounds. These are your friends: **А**, **О**, **К**, **М**, and **Т**. With just these five, you can already read real Ukrainian words:

| Word | Meaning |
|---|---|
| **ма́ма** | mother |
| **та́то** | father |
| **мак** | poppy |
| **о́ко** | eye |
| **а́том** | atom |
| **ко́ма** | comma |
| **том** | volume (of a book) |

Try it. Look at **мама**. You know every letter. М — like "m." А — like "a" in "father." Read it: *мама*. Now **тато**: Т-А-Т-О. Father. You are reading Ukrainian.

One small detail: Ukrainian **Т** is pronounced with your tongue touching your teeth, not the gum ridge behind them as in English. And Ukrainian **К** and **Т** have no puff of air after them — hold your hand in front of your mouth and try to say them without feeling breath on your palm. These differences are subtle. Close enough for now.

### False Friends

Here is where English speakers stumble. Several Ukrainian letters look like Latin letters but make completely different sounds:

| Letter | Looks like... | But sounds like... | Example |
|---|---|---|---|
| **В** | English B | "v" in "van" | **вода́** — water |
| **Н** | English H | "n" in "no" | **ніс** — nose |
| **Р** | English P | a rolled "r" (like in Spanish) | **рука́** — hand |
| **С** | English C | "s" in "sun" | **сон** — dream |
| **У** | English Y | "oo" in "boot" | **рука** — hand |
| **Х** | English X | "ch" in Scottish "loch" | **ха́та** — house |

**В** is the most dangerous false friend. When you see **вода**, your English brain screams "boda." Fight it. This is **вода** — "voda" — water. Similarly, **Р** in **рука** is not "p" — it is a rolled "r," like a cat purring. **Рука** means hand.

:::match-up
title: "Match false friend letters to their real sounds"
---
- left: "В"
  right: "sounds like «в» in вода, not like English B"
- left: "Н"
  right: "sounds like «н» in ніс, not like English H"
- left: "Р"
  right: "a rolled R (like in Spanish), not English P"
- left: "С"
  right: "sounds like «с» in сон, not like English C"
- left: "У"
  right: "sounds like «у» in рука, «oo» in boot"
- left: "Х"
  right: "sounds like «ch» in Scottish «loch», not English X"
:::

### New Shapes

Finally, some letters have no Latin equivalent at all. They are entirely new shapes: **Б**, **Г**, **Ґ**, **Д**, **Ж**, **З**, **И**, **Й**, **Л**, **П**, **Ф**, **Ц**, **Ч**, **Ш**, **Щ**. Do not panic — you will learn these through words, not by memorizing a chart.

Here are a few to start:

| Word | Meaning | New letters in it |
|---|---|---|
| **банк** | bank | **Б** |
| **дім** | house, home | **Д**, **І** |
| **зима́** | winter | **З**, **И** |
| **кни́га** | book | **Б** is not new, but **Г** is |
| **шко́ла** | school | **Ш** |

Two special cases. The letter **Щ** always makes two sounds together — like "sh" immediately followed by "ch." And the letter **Ь** (the soft sign) has no sound of its own — it simply softens the consonant before it. The letter **Ї** is unique to Ukrainian and always represents two sounds together. The letters **Я**, **Ю**, **Є** can behave in two different ways depending on their position. Full details come in Module 2 — for now, just recognize them when you see them.

## Приві́т! (Hello!)

Time for your first Ukrainian conversation. Imagine you meet a friend on the street in Kyiv:

> — **Привіт!**
> — **Привіт! Як спра́ви?**
> — **До́бре. А у тебе́?**
> — **Чудо́во!**

**Привіт** means "hi" — it is informal, for friends, family, and peers. **Як справи?** means "how are you?" Here are the most common responses:

| Response | Meaning |
|---|---|
| **Добре.** | Fine. / Good. |
| **Чудово!** | Great! / Wonderful! |
| **Норма́льно.** | Okay. / So-so. |

After answering, you bounce the question back: **А у тебе?** — "And you?"

:::tip
Ukrainian has gendered forms. A woman says **Ра́да тебе ба́чити!** (Glad to see you!), while a man says **Ра́дий тебе бачити!** This is your very first encounter with grammatical gender in Ukrainian — it will become a major topic starting in Module 8.
:::

Now look at the word **Привіт** letter by letter. It uses letters from every group you have learned:

| Letter | Group |
|---|---|
| **П** | new shape |
| **р** | false friend (rolled "r," not "p"!) |
| **и** | new vowel |
| **в** | false friend ("v," not "b"!) |
| **і** | vowel (similar to English "ee") |
| **т** | familiar friend |

This one word is a perfect test of everything in this module.

:::fill-in
title: "Complete the greeting dialogue"
---
- sentence: "— ___! Як справи?"
  answer: "Привіт"
- sentence: "— Добре. А у ___?"
  answer: "тебе"
- sentence: "— ___! Рада тебе бачити!"
  answer: "Чудово"
- sentence: "— Привіт! Як ___?"
  answer: "справи"
:::

## Чита́ємо (Reading Practice)

### Signs in Ukraine

Walk down any street in a Ukrainian city and you will see these signs. Sound out each letter, blend them into syllables, then read the whole word:

| Sign | Meaning |
|---|---|
| **Апте́ка** | pharmacy |
| **Банк** | bank |
| **Кафе́** | cafe |
| **Метро́** | metro |
| **По́шта** | post office |
| **Школа** | school |
| **Зупи́нка** | bus stop |

Notice how many of these are close to English or other European languages. **Банк**, **метро**, **кафе** — these are international words. But pay attention to the letters: the **Б** in **Банк** is not a Latin B, and the **К** at the end has no puff of air.

### Ukrainian Cities

Now try some city names. These are words every Ukrainian knows by heart:

**Ки́їв** · **Львів** · **Оде́са** · **Харків** · **Дніпро́** · **Полта́ва**

**Київ** — the capital. Notice the false friend **В** at the end: it sounds like "v," giving you "Kyiv," not "Kyib." **Львів** has two **В** letters! Both sound like "v."

### First Sentences

Ukrainian has a wonderfully useful word: **Це** — "this is." With it, you can make your first sentences:

> **Це мама.** — This is mother.
> **Це банк.** — This is a bank.
> **Це Київ.** — This is Kyiv.

And your first questions:

> **Що це?** — What is this?
> **Хто це?** — Who is this?

**Що** means "what" and **Хто** means "who." These two words open the door to asking about everything around you.

:::group-sort
title: "Classify these Ukrainian letters"
---
groups:
  - name: "Голосні (vowels)"
    items: ["А", "О", "У", "І"]
  - name: "Приголосні (consonants)"
    items: ["М", "К", "Б", "Ш"]
:::


## Video Resources

<YouTubeVideo client:only="react" url="https://www.youtube.com/watch?v=ksXIXj7CXwc" label="Overview — Ukrainian Lessons" />

📋 [Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)

## Словник — Vocabulary

### Required words

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

### Recommended words

| Слово | Translation |
|-------|-------------|
| **банк** | bank |
| **аптека** | pharmacy |
| **метро** | metro |
| **пошта** | post office |
| **зупинка** | bus stop |
| **нормально** | okay |

## Resources

- Большакова Grade 1 буквар, p.24
  _Голосні/приголосні taught through poems. 'Голосні почуєш в пісні.'_
- Захарійчук Grade 1 буквар (NUS 2025), p.13
  _Sound notation: [•] for vowels, [–] for consonants._
- Заболотний Grade 5, p.73
  _38 звуків: 6 голосних + 32 приголосні._
- [ULP Season 1, Episode 1 — Informal Greetings](https://www.ukrainianlessons.com/episode1/)
  _Привіт, Як справи?, response patterns._

## Підсумок — Summary

Test yourself. Can you answer these questions?

**How many letters?** 33. **How many sounds?** 38. **Why different?** Some letters represent more than one sound.

**What are голосні?** Vowels — sounds made with voice alone, no obstruction. Six sounds, ten letters.

**What are приголосні?** Consonants — sounds made when lips, teeth, or tongue create a barrier. Thirty-two sounds.

**What are false friend letters?** Letters that look like Latin but sound different: **В** (not "b"), **Н** (not "h"), **Р** (not "p"), **С** (not "c"), **У** (not "y"), **Х** (not "x").

**What does Привіт mean?** Hi — informal greeting. **Як справи?** — How are you? Responses: **Добре**, **Чудово**, **Нормально**.

:::true-false
title: "True or false?"
---
- statement: "Ukrainian has 33 letters."
  answer: true
- statement: "Ukrainian has 33 sounds."
  answer: false
- statement: "Голосні sounds are made with voice and noise."
  answer: false
- statement: "The letter В sounds like English B."
  answer: false
- statement: "Привіт is an informal greeting."
  answer: true
:::

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

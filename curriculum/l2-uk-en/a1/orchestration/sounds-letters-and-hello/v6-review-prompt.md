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

Look at the text on this page. What you see are letters — symbols printed on a screen. Now say a word out loud. Anything. What you just produced are sounds — vibrations in the air that carry meaning. This distinction is the absolute foundation of the Ukrainian language, and every Ukrainian child learns it in the first grade. There is a golden rule:

> **Ми чу́ємо і вимовля́ємо звуки, а ба́чимо і пи́шемо літери.**

We hear and pronounce sounds. We see and write letters. Sounds and letters are not the same thing. Ukrainian has **33 літери** (letters) but **38 зву́ків** (sounds). Why the mismatch? Because some letters represent more than one sound, and some sounds share a letter. You will discover exactly how as you move through the curriculum — for now, hold onto that number: 33 letters, 38 sounds.

Ukrainian sounds split into two families. The first family is **голосні́** — vowels. These are sounds made with your voice alone, mouth open, air flowing freely with no obstruction from your lips, teeth, or tongue. Ukrainian schoolchildren learn them through a poem: **Голосні почу́єш в пісні́** — "You'll hear vowels in a song." There are **6 голосни́х звуків** (vowel sounds), but **10 голосних лі́тер** (vowel letters): **А, О, У, Е, И, І, Я, Ю, Є, Ї**. The extra four letters (Я, Ю, Є, Ї) have a special trick — they can represent two sounds at once. More on that in Module 2.

The second family is **при́голосні** — consonants. These sounds are made when something in your mouth — lips, teeth, tongue — creates an obstruction. Air pushes through or around that obstruction, producing noise. Some consonants use voice and noise together; others use noise alone. Ukrainian has **32 при́голосних звуки** (consonant sounds). A schoolroom rhyme captures the difference: **Приголосні деренча́ть і тихе́нько шелестя́ть** — "Consonants rattle and softly rustle."

One more character: the letter **Ь** (soft sign). It has no sound of its own. It tells you to soften the consonant before it. Think of it as an instruction mark, not a sound.

:::quiz
title: "Звук чи лі́тера?"
---
- q: "What do we hear and pronounce?"
  o: ["звуки (sounds)", "літери (letters)", "слова́ (words)"]
  a: 0
- q: "What do we see and write?"
  o: ["літери (letters)", "звуки (sounds)", "речення (sentences)"]
  a: 0
- q: "How many letters does the Ukrainian alphabet have?"
  o: ["33", "38", "26"]
  a: 0
- q: "How many vowel sounds are there in Ukrainian?"
  o: ["6", "10", "8"]
  a: 0
- q: "What are голосні?"
  o: ["Vowels", "Consonants", "Letters"]
  a: 0
- q: "What are приголосні?"
  o: ["Consonants", "Vowels", "Syllables"]
  a: 0
:::

:::group-sort
title: "Голосні чи приголосні? (Vowel or consonant letters?)"
---
groups:
  - name: "Голосні"
    items: ["А", "О", "У", "І"]
  - name: "Приголосні"
    items: ["М", "К", "Б", "Ш"]
:::

## Пе́рші слова (First Words)

Some Ukrainian letters will feel like old friends. **А** looks like A and sounds like the "a" in "father." **О** looks like O and sounds like a clear, round "o" — never a lazy "uh." **К** looks like K and sounds like K. **М** looks like M and sounds like M. **Т** looks like T and sounds like T.

With just these five letters, you can already read real Ukrainian words:

| Word | Meaning |
|------|---------|
| **ма́ма** | mother |
| **та́то** | father |
| **ко́ма** | comma |
| **а́том** | atom |
| **мак** | poppy |
| **о́ко** | eye |
| **там** | there |
| **тут** | here |

Try it. Look at **мама**: М-А-М-А. You already know every letter. Now **тато**: Т-А-Т-О. You just read your first Ukrainian words.

:::tip
Ukrainian **Т** is dental — your tongue touches the back of your upper teeth, not the gum ridge behind them. And Ukrainian **К** and **Т** have no puff of air after them, unlike their English cousins. These are small differences. Close enough for now — awareness is the first step.
:::

### False Friends — The Biggest Trap

Now for the letters that will betray you. These look like Latin letters but make completely different sounds:

| Letter | Looks like | Actually sounds like |
|--------|-----------|---------------------|
| **В** | B | "v" as in "van" |
| **Н** | H | "n" as in "no" |
| **Р** | P | a rolled "r" (tongue taps the roof of your mouth) |
| **С** | C | "s" as in "sun" |
| **У** | Y | "oo" as in "moon" |
| **Х** | X | like "ch" in Scottish "loch" |

These false friends are responsible for more reading errors than anything else in early Ukrainian. Burn this table into your memory. When you see **В**, your brain will scream "B!" — override it. It is "v."

Practice with real words:

| Word | Meaning | Watch out for |
|------|---------|--------------|
| **вода́** | water | В = "v", not "b" |
| **рука́** | hand | Р = rolled "r", not "p" |
| **сон** | dream | С = "s", not "k" |
| **ніс** | nose | Н = "n", not "h" |
| **ха́та** | house | Х = "ch" in "loch", not "ks" |

### New Shapes

Finally, some letters have no Latin lookalike at all. They are entirely new shapes: **Б, Г, Ґ, Д, Ж, З, И, Й, Л, П, Ф, Ц, Ч, Ш, Щ**. No false friends here — your brain has nothing to confuse them with, so they are actually easier to learn.

Meet a few through words:

| Word | Meaning |
|------|---------|
| **банк** | bank |
| **дім** | home, house |
| **зима́** | winter |
| **кни́га** | book |
| **шко́ла** | school |

One letter deserves special attention: **Щ** always makes two sounds together — "sh" followed immediately by "ch." And **Ї** is unique to Ukrainian — no other Slavic language has it. It always represents two sounds: a "y" glide followed by "ee."

:::match-up
title: "Match false friend letters to their REAL sounds"
---
- left: "В"
  right: "v (as in «van»)"
- left: "Н"
  right: "n (as in «no»)"
- left: "Р"
  right: "rolled r"
- left: "С"
  right: "s (as in «sun»)"
- left: "У"
  right: "oo (as in «moon»)"
- left: "Х"
  right: "ch (as in Scottish «loch»)"
:::

## Приві́т! (Hello!)

Time for your first Ukrainian conversation. Two friends meet on the street:

> — **Привіт!**
> — **Привіт! Як спра́ви?**
> — **До́бре. А у тебе́?**
> — **Чудо́во!**

That is a complete, natural greeting in Ukrainian. Let's break it apart.

**Привіт!** means "Hi!" — informal, used with friends, family, peers, anyone you would address with "ти" (you, singular informal). This is the word you will use most in your first weeks.

**Як справи?** means "How are you?" — literally "How are things?" Common responses:

| Response | Meaning |
|----------|---------|
| **Добре.** | Fine. / Good. |
| **Чудово!** | Great! / Wonderful! |
| **Норма́льно.** | Okay. / All right. |

**А у тебе?** means "And you?" — a natural way to return the question.

:::caution
Ukrainian has gendered forms. A woman says **Ра́да тебе ба́чити!** ("Glad to see you!"). A man says **Ра́дий тебе бачити!** The ending changes: **рада** (feminine) versus **радий** (masculine). This is your very first encounter with gender in Ukrainian — a topic that becomes central starting in Module 8.
:::

Now try reading **Привіт** letter by letter. This single word uses letters from every category you just learned: **П** (new shape), **р** (false friend — rolled "r," not "p"!), **и** (new vowel), **в** (false friend — "v," not "b"!), **і** (vowel), **т** (familiar). If you can read **Привіт**, you have already practiced all three letter groups.

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

Imagine you just landed at Бори́спіль airport and you are taking a bus into Ки́їв. Signs are everywhere. You can read them.

### Signs You See in Ukraine

Sound out each letter. Blend them into syllables. Read the whole word.

| Sign | Meaning |
|------|---------|
| **Апте́ка** | pharmacy |
| **Банк** | bank |
| **Кафе́** | cafe |
| **Метро́** | metro |
| **По́шта** | post office |
| **Школа** | school |
| **Зупи́нка** | bus stop |

Notice how many of these are recognizable from English or other European languages — **банк**, **метро**, **кафе**. Ukrainian has absorbed international words, just like every other language. But they are written in Cyrillic and follow Ukrainian pronunciation rules.

### Ukrainian Cities

Now try city names. These are words you will hear in news, weather forecasts, and everyday conversation:

**Київ** · **Львів** · **Оде́са** · **Харків** · **Дніпро́** · **Полта́ва**

Start with **Київ**: К-и-ї-в. The **Ї** makes a "yi" sound, and the **в** at the end sounds like "v." **Львів** is trickier — two consonant clusters and that unique **Ї** again.

### First Sentences

Ukrainian has a powerful little word: **Це** — "This is." With **Це** and a noun, you can make your first Ukrainian sentences:

> **Це мама.** — This is mom.
> **Це банк.** — This is a bank.
> **Це Київ.** — This is Kyiv.

And your first questions:

> **Що це?** — What is this?
> **Хто це?** — Who is this?

**Що** means "what." **Хто** means "who." With these two question words, **Це**, and the vocabulary you already know, you can point at anything in Ukraine and start a conversation.

> — **Що це?**
> — **Це аптека.**
> — **А це?**
> — **Це пошта.**

:::true-false
title: "Так чи ні? (True or false?)"
---
- statement: "The Ukrainian alphabet has 33 letters."
  answer: true
- statement: "Ukrainian has more vowel sounds than consonant sounds."
  answer: false
- statement: "The letter В sounds like «b» in English."
  answer: false
- statement: "Щ represents two sounds together."
  answer: true
- statement: "Ї is a letter found in many Slavic languages."
  answer: false
:::


### Відео — Video

<YouTubeVideo client:only="react" url="https://www.youtube.com/watch?v=ksXIXj7CXwc" label="Overview — Ukrainian Lessons" />

[Повний плейлист / Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)


## Підсумок — Summary

Here is what you now know. The Ukrainian alphabet has **33 літери** and **38 звуків**. Letters and sounds are not the same: **ми чуємо звуки, а бачимо літери**. Sounds split into two families: **голосні** (vowels — 6 sounds, 10 letters) and **приголосні** (consonants — 32 sounds). Some Cyrillic letters look like Latin but sound completely different — these false friends (**В, Н, Р, С, У, Х**) require constant vigilance.

You learned your first greeting: **Привіт! Як справи? — Добре.** You learned to read signs (**Аптека, Банк, Метро**), city names (**Київ, Львів, Одеса**), and to make simple sentences with **Це**: **Це школа. Що це? Хто це?**

You can now read and pronounce basic Ukrainian words. You can greet someone and respond to a greeting. And you understand the most fundamental concept in Ukrainian phonetics — the difference between **звуки** and **літери**.


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

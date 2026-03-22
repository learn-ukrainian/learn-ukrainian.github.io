# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 2: Reading Ukrainian (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Claude Opus
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-002
level: A1
sequence: 2
slug: reading-ukrainian
version: '1.0'
title: Reading Ukrainian
subtitle: "From letters to words to sentences"
focus: phonetics
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Read any Ukrainian word by sounding out letters and blending syllables
- Apply the syllable rule — count vowels to count syllables
- Read multisyllable words confidently (not letter by letter)
- Understand how the 10 vowel letters map to 6 vowel sounds
content_outline:
- section: "Склади (Syllables)"
  words: 250
  points:
  - "Большакова Grade 1 p.25: 'У слові стільки складів, скільки голосних звуків.'
    Count the vowels, count the syllables. This rule never breaks.
    ма-ма (2 vowels = 2 syllables), мо-ло-ко (3 vowels = 3 syllables),
    банк (1 vowel = 1 syllable)."
  - "How to read a new word:
    1. Find the vowels (they're the syllable cores)
    2. Split at syllable boundaries (consonants prefer starting new syllables)
    3. Sound out each syllable
    4. Blend into the full word at natural speed
    Practice: а-пте-ка, у-ні-вер-си-тет, шо-ко-лад.
    Note: Ukrainian phonetic syllable division (складоподіл) follows the
    open-syllable principle — consonants prefer starting new syllables."
  - "Following Большакова p.29 звуковий аналіз method: identify vowels,
    divide into syllables, then read. This is how Ukrainian children learn."
- section: "Голосні літери (Vowel Letters)"
  words: 300
  points:
  - "Review from M01: 6 sounds, 10 letters. Now learn all 10 individually.
    Simple vowels (one sound each): А [а], О [о], У [у], Е [е], И [и], І [і].
    Each makes ONE consistent sound — no surprises."
  - "Iotated vowels (two sounds or softening):
    Я = [йа] at word start (яблуко) or after vowel (моя).
    After consonant: softens it + [а] (пісня — Н is softened).
    Ю = [йу] or softening + [у]. Є = [йе] or softening + [е].
    Ї = ALWAYS [йі] — never softens. Only at word start, after vowel,
    or after apostrophe. Unique to Ukrainian."
  - "Critical minimal pairs:
    И vs І: кит (whale) vs кіт (cat), дим (smoke) vs дім (house).
    Listen to Anna's pronunciation videos for each — the difference
    is subtle but changes meaning."
- section: "Читання слів (Reading Words)"
  words: 300
  points:
  - "Apply M01 letter knowledge to read real words fluently.
    Strategy: don't read letter-by-letter. Read syllable-by-syllable.
    Start with the vowels (find them first), then build outward.
    Example: книга — find vowels И, А → кни-га → read."
  - "Common word patterns for reading practice:
    CVCV: мама, тато, каша, вода, рука, хата, коза, нога
    CVCCV: школа, книга, банда, парта
    CVC: дім, сон, ліс, дуб, хліб, банк
    The more patterns you see, the faster you read."
  - "Special letter combinations to watch for:
    Щ is always [шч] — що, ще, щастя.
    Ь has no sound — it softens: день, сіль, кінь.
    ' (apostrophe) separates: сім'я, м'ясо, п'ять.
    These will be explored fully in M03."
- section: "Читаємо разом (Reading Together)"
  words: 200
  points:
  - "Progressive reading practice — start simple, build up:
    Level 1 (2 syllables): мама, тато, вода, рука, хата, каша
    Level 2 (3 syllables): аптека, молоко, людина, вулиця
    Level 3 (4+ syllables): університет, бібліотека, фотографія"
  - "Reading a simple text (all Це + noun, no verbs):
    Це Київ. Це столиця. Тут аптека і банк. Там школа.
    Що це? Це кафе. А це пошта."
- section: "Підсумок — Summary"
  words: 150
  points:
  - "Self-check: How do you count syllables in a Ukrainian word?
    What are the 6 vowel sounds? Name the 4 iotated vowel letters.
    What does Ь do? What does the apostrophe do?
    Read this word: бібліотека — how many syllables?"
vocabulary_hints:
  required:
  - яблуко (apple) — Я at word start = [йа]
  - молоко (milk) — 3 syllables, all simple vowels
  - людина (person) — Л + Ю combination
  - вулиця (street) — Ц sound practice
  - столиця (capital) — Київ — столиця України
  - каша (porridge) — Ш sound practice
  - пісня (song) — softening by Я after consonant
  recommended:
  - університет (university) — long word practice
  - бібліотека (library) — 5 syllables
  - фотографія (photography) — long word with Ф
  - шоколад (chocolate) — Ш + О + К combination
activity_hints:
- type: fill-in
  focus: "Divide words into syllables: мо-ло-ко, ап-те-ка"
  items: 8
- type: quiz
  focus: "How many syllables? Count the vowels."
  items: 8
- type: match-up
  focus: "Match iotated vowels to their sound components: Я=[й]+[а]"
  items: 4
- type: quiz
  focus: "Read the word and choose its meaning"
  items: 6
connects_to:
- a1-003 (Special Signs)
prerequisites:
- a1-001 (Sounds, Letters, and Hello)
grammar:
- "Syllable rule: count vowels = count syllables (складоподіл)"
- "10 vowel letters → 6 vowel sounds mapping"
- "Iotated vowels (Я, Ю, Є as two sounds or softening; Ї always [йі])"
- "Reading fluency: syllable-by-syllable word reading"
- "Ь, apostrophe, voiced/voiceless (preview — detailed in M03)"
register: розмовний
references:
- title: "Большакова Grade 1 буквар, p.25"
  notes: "Syllable rule: 'У слові стільки складів, скільки голосних звуків.'"
- title: "Большакова Grade 1 буквар, p.29"
  notes: "Звуковий аналіз слова method — how to analyze word sounds."
- title: "Захарійчук Grade 1 (NUS 2025), p.13-15"
  notes: "Sound notation: [•] for vowels, [–] for consonants, [=] for soft."
pronunciation_videos:
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

</plan_content>

## Generated Content

<generated_module_content>
<!-- TAB:Урок -->

## Склади (Syllables)

How many syllables does the word **молоко́** have? A first-grade student in Ukraine knows the answer instantly — and not because they memorized it. They know a rule that never fails.

Every Ukrainian child learns this principle from their very first буква́р: **У сло́ві сті́льки складів, скі́льки голосни́х зву́ків** — a word has as many syllables as it has vowel sounds. Find the vowels, and you have found the syllables. This rule works for every single Ukrainian word, no exceptions.

Let's try it. The word **ма́ма** has two vowels: **а** and **а**. Two vowels means two syllables: **ма-ма**. The word **молоко** has three vowels: **о**, **о**, **о**. Three vowels, three syllables: **мо-ло-ко**. What about **банк**? Only one vowel: **а**. One syllable. What about **університе́т**? Five vowels: **у**, **і**, **е**, **и**, **е**. Five syllables: **у-ні-вер-си-тет**.

This is the method Ukrainian textbooks teach, following Большако́ва's звукови́й ана́ліз approach from Grade 1. Here is how to read any new Ukrainian word:

1. **Find the vowels** — they are the core of every syllable
2. **Split at syllable boundaries** — consonants prefer to start new syllables (the open-syllable principle)
3. **Sound out each syllable** separately
4. **Blend them together** at natural speed

Try this method with **апте́ка**. The vowels are **а**, **е**, **а** — three syllables: **ап-те-ка**. Now try **ка́ша**: vowels **а**, **а** — two syllables: **ка-ша**. And **ву́лиця**: vowels **у**, **и**, **а** — three syllables: **ву-ли-ця**.

Notice something important: consonants in Ukrainian prefer to begin a new syllable rather than close the previous one. That's why it's **мо-ло-ко**, not **мол-ок-о**. This open-syllable principle (складопо́діл) is a fundamental feature of Ukrainian phonetics.

:::quiz
title: "Скільки складів? (How many syllables?)"
---
- q: "How many syllables in «мама»?"
  o: ["1", "2", "3"]
  a: 1
- q: "How many syllables in «молоко»?"
  o: ["2", "3", "4"]
  a: 1
- q: "How many syllables in «банк»?"
  o: ["1", "2", "3"]
  a: 0
- q: "How many syllables in «аптека»?"
  o: ["2", "3", "4"]
  a: 1
- q: "How many syllables in «університет»?"
  o: ["3", "4", "5"]
  a: 2
- q: "How many syllables in «каша»?"
  o: ["1", "2", "3"]
  a: 1
- q: "How many syllables in «вулиця»?"
  o: ["2", "3", "4"]
  a: 1
- q: "How many syllables in «хліб»?"
  o: ["1", "2", "3"]
  a: 0
:::

## Голосні́ лі́тери (Vowel Letters)

In Module 1 you learned that Ukrainian has 6 vowel sounds but 10 vowel letters. Now it's time to meet all ten individually and understand why the numbers don't match.

### Simple vowels — one letter, one sound

Six vowel letters each represent exactly one sound. No surprises, no variations:

| Letter | Sound | Example |
|--------|-------|---------|
| **А** | "a" as in "father" | **мама** |
| **О** | "o" as in "port" | **молоко** |
| **У** | "oo" as in "moon" | **рука́** |
| **Е** | "e" as in "pen" | **не́бо** |
| **И** | between "i" in "bit" and "e" in "bet" | **дим** |
| **І** | "ee" as in "meet" | **дім** |

Pay special attention to the pair **И** and **І**. They look similar but represent different sounds — and swapping them changes meaning completely. **Дим** means smoke, but **дім** means house. **Кит** is a whale, but **кіт** is a cat. These minimal pairs show why precision with Ukrainian vowels matters from day one.

### Iotated vowels — the double agents

Four vowel letters can represent two sounds at once. They are **Я**, **Ю**, **Є**, and **Ї**.

**Я**, **Ю**, and **Є** have a dual nature. At the beginning of a word or after another vowel, they produce two sounds — a "y" glide followed by a vowel:

- **Я** = "y" + "a": **я́блуко** (apple) — the **Я** at the start gives two sounds
- **Ю** = "y" + "u": **юна́к** (young man) — again, two sounds at the start
- **Є** = "y" + "e": **Євро́па** (Europe) — two sounds at the start

After a consonant, these same letters do something different: they soften the preceding consonant and contribute just the vowel sound. In **пі́сня** (song), the **Я** softens the **Н** and sounds like "a" — no "y" glide.

Then there is **Ї** — uniquely Ukrainian and wonderfully simple. **Ї** always represents two sounds: "y" + "i". It never softens a consonant. You will find it at the beginning of words (**їжа́к** — hedgehog), after vowels (**мої́** — my/mine), or after an apostrophe (**з'ї́сти**). No other Slavic language has this letter.

:::match-up
title: "Iotated vowels — what sounds do they make?"
---
- left: "Я (at word start)"
  right: "«й» + «а»"
- left: "Ю (at word start)"
  right: "«й» + «у»"
- left: "Є (at word start)"
  right: "«й» + «е»"
- left: "Ї (always)"
  right: "«й» + «і»"
:::

## Чита́ння слів (Reading Words)

You know the letters. You know the syllable rule. Now it's time to read real Ukrainian words — not letter by letter, but syllable by syllable, the way Ukrainian students are taught.

Here is the strategy: don't start at the first letter and inch forward. Instead, scan the whole word first. Find the vowels, mark the syllables mentally, then read each syllable as a unit. Let's apply this to **кни́га** (book). Find the vowels: **и** and **а**. That's two syllables: **кни-га**. Now say it smoothly: **книга**.

### Common word patterns

Certain letter patterns appear again and again in Ukrainian. Recognizing them speeds up your reading dramatically.

**Two-syllable words** (CVCV pattern): **мама**, **та́то**, **каша**, **вода́**, **рука**, **ха́та**, **коза́**, **нога́**. These are the easiest to read — two consonants, two vowels, perfectly regular.

**Two-syllable words with clusters** (CVCCV): **шко́ла**, **книга**, **па́рта**. Here a consonant cluster starts the second syllable. Ukrainian consonants love clustering together at syllable beginnings.

**One-syllable words** (CVC): **дім**, **сон**, **ліс**, **дуб**, **хліб**, **банк**. Short, punchy words — one vowel, one syllable, done.

**Three-syllable words**: **люди́на** (person), **столи́ця** (capital), **вулиця** (street). Find the three vowels, split, read.

### Special combinations to watch for

Three letter features deserve a brief preview here. They will be covered fully in Module 3, but you should recognize them now:

**Щ** always represents the sound combination "shch": **що** (what), **ще** (still/yet), **ща́стя** (happiness).

**Ь** (soft sign) has no sound of its own. Its job is to soften the consonant before it: **день** (day), **сіль** (salt), **кінь** (horse). The word **день** has one syllable — **ь** is not a vowel.

The **apostrophe** ( **'** ) separates a consonant from an iotated vowel, preventing softening: **сім'я́** (family), **м'я́со** (meat), **п'ять** (five). Without the apostrophe, the consonant would be softened instead.

:::fill-in
title: "Поді́ли на склади (Divide into syllables)"
---
- sentence: "мо-ло-___"
  answer: "ко"
- sentence: "ап-те-___"
  answer: "ка"
- sentence: "ка-___"
  answer: "ша"
- sentence: "лю-ди-___"
  answer: "на"
- sentence: "ву-ли-___"
  answer: "ця"
- sentence: "сто-ли-___"
  answer: "ця"
- sentence: "у-ні-вер-си-___"
  answer: "тет"
- sentence: "біб-лі-о-те-___"
  answer: "ка"
:::

## Чита́ємо ра́зом (Reading Together)

Time to put everything together. Below is a reading ladder — words organized from short to long. Read each word by finding its vowels, splitting into syllables, and blending.

**Level 1 — Two syllables:** **мама**, **тато**, **вода**, **рука**, **хата**, **каша**, **небо**, **книга**

**Level 2 — Three syllables:** **аптека**, **молоко**, **людина**, **вулиця**, **столиця**, **шокола́д**

**Level 3 — Four or more syllables:** **університет**, **бібліоте́ка**, **фотогра́фія**

Verify your reading: **бібліотека** has five vowels (**і**, **і**, **о**, **е**, **а**) — five syllables. **Фотографія** has five vowels (**о**, **о**, **а**, **і**, **а**) — also five syllables.

Now try reading connected text. Every sentence below uses structures from Module 1 — **Це** (this is), **тут** (here), **там** (there), question words.

> **Це Ки́їв. Це столиця. Тут аптека і банк. Там школа. Що це? Це кафе́. А це по́шта.**

Read it again, faster. You are reading Ukrainian.

:::quiz
title: "Що це? (What is it?)"
---
- q: "What does «яблуко» mean?"
  o: ["milk", "apple", "porridge"]
  a: 1
- q: "What does «молоко» mean?"
  o: ["person", "street", "milk"]
  a: 2
- q: "What does «столиця» mean?"
  o: ["capital", "library", "street"]
  a: 0
- q: "What does «пісня» mean?"
  o: ["chocolate", "song", "porridge"]
  a: 1
- q: "What does «людина» mean?"
  o: ["university", "apple", "person"]
  a: 2
- q: "What does «каша» mean?"
  o: ["porridge", "song", "house"]
  a: 0
:::


### Відео — Video

[Повний плейлист / Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)


## Підсумок — Summary

You now have the tools to read any Ukrainian word. Before moving to Module 3, check yourself with these questions:

**How do you count syllables in a Ukrainian word?** Count the vowel sounds. The number of vowels equals the number of syllables — always.

**What are the 6 vowel sounds?** А, О, У, Е, И, І. Six sounds, each represented by one letter.

**Name the 4 iotated vowel letters.** Я, Ю, Є, Ї. The first three can represent either two sounds (at word start or after a vowel) or soften a preceding consonant. Ї always represents two sounds.

**What does Ь do?** It softens the consonant before it. It makes no sound of its own and is not a vowel — it does not create a syllable.

**What does the apostrophe do?** It separates a consonant from an iotated vowel, blocking softening: **сім'я**, **м'ясо**.

**Final challenge — read this word: бібліотека.** Find the vowels: **і**, **і**, **о**, **е**, **а** — five vowels, five syllables: **біб-лі-о-те-ка**. If you read that without hesitation, you are ready for Module 3.


<!-- TAB:Словник -->

### Обов'язкові слова — Required words

| Слово | Translation |
|-------|-------------|
| **яблуко** | apple |
| **молоко** | milk |
| **людина** | person |
| **вулиця** | street |
| **столиця** | capital |
| **каша** | porridge |
| **пісня** | song |

### Рекомендовані слова — Recommended words

| Слово | Translation |
|-------|-------------|
| **університет** | university |
| **бібліотека** | library |
| **фотографія** | photography |
| **шоколад** | chocolate |

### Додаткові слова з уроку — Additional words from the lesson

| Слово | Translation |
|-------|-------------|
| **банк** |  |
| **мама** |  |
| **дим** |  |
| **дім** |  |
| **Кит** |  |
| **кіт** |  |
| **книга** |  |
| **рука** |  |
| **сон** |  |
| **ліс** |  |
| **дуб** |  |
| **хліб** |  |
| **що** |  |
| **ще** |  |
| **день** |  |
| **сіль** |  |
| **кінь** |  |
| **п'ять** |  |
| **тато** |  |
| **вода** |  |
| **хата** |  |
| **небо** |  |
| **Це** |  |
| **тут** |  |
| **там** |  |
| **сім'я** |  |
| **м'ясо** |  |


<!-- TAB:Зошит -->

:::note
Розширені вправи для цього уроку ще в розробці.

Advanced exercises for this module are in development. Check back soon!
:::


<!-- TAB:Ресурси -->

- Большакова Grade 1 буквар, p.25
  _Syllable rule: 'У слові стільки складів, скільки голосних звуків.'_
- Большакова Grade 1 буквар, p.29
  _Звуковий аналіз слова method — how to analyze word sounds._
- Захарійчук Grade 1 (NUS 2025), p.13-15
  _Sound notation: [•] for vowels, [–] for consonants, [=] for soft._
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

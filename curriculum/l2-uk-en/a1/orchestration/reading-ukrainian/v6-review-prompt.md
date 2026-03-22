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

How many syllables does the word **молоко́** have? A first-grader in Ukraine answers instantly: three. The reason is simple — **молоко** has three vowels. Every Ukrainian child learns this rule on page 25 of the букvar: **«У сло́ві сті́льки складів, скі́льки голосни́х зву́ків.»** A word has as many syllables as it has vowel sounds. This rule never breaks. Not once. Not in any Ukrainian word.

Try it. The word **ма́ма** has two vowels — **а** and **а** — so it has two syllables: **ма-ма**. The word **банк** has one vowel — **а** — so it is one syllable. The word **шокола́д** has three vowels — **о**, **о**, **а** — so three syllables: **шо-ко-лад**.

Here is how to read any new Ukrainian word, step by step. This is the звукови́й ана́ліз method from Большако́ва's Grade 1 textbook:

1. **Find the vowels** — they are the core of every syllable.
2. **Split at syllable boundaries** — consonants prefer to start a new syllable, not end one. This is the open-syllable principle.
3. **Sound out each syllable** slowly.
4. **Blend** the syllables together at natural speed.

The open-syllable principle is important. In Ukrainian phonetic syllable division (складопо́діл), consonants travel forward to begin the next syllable rather than closing the previous one. So **апте́ка** divides as **а-пте-ка** — the cluster «пт» starts the second syllable. The word **ву́лиця** divides as **ву-ли-ця**. The word **люди́на** divides as **лю-ди-на**.

:::quiz
title: "Скільки складів?"
---
- q: "How many syllables does «молоко» have?"
  o: ["2", "3", "4"]
  a: 1
- q: "How many syllables does «банк» have?"
  o: ["1", "2", "3"]
  a: 0
- q: "How many syllables does «аптека» have?"
  o: ["2", "3", "4"]
  a: 1
- q: "How many syllables does «університе́т» have?"
  o: ["4", "5", "6"]
  a: 1
- q: "How many syllables does «ха́та» have?"
  o: ["1", "2", "3"]
  a: 1
- q: "How many syllables does «кіт» have?"
  o: ["1", "2", "3"]
  a: 0
- q: "How many syllables does «бібліоте́ка» have?"
  o: ["3", "4", "5"]
  a: 2
- q: "How many syllables does «ка́ша» have?"
  o: ["1", "2", "3"]
  a: 1
:::

:::fill-in
title: "Divide into syllables"
---
- sentence: "мо-ло-___"
  answer: "ко"
- sentence: "а-пте-___"
  answer: "ка"
- sentence: "пі-___"
  answer: "сня"
- sentence: "я-блу-___"
  answer: "ко"
- sentence: "ву-ли-___"
  answer: "ця"
- sentence: "ка-___"
  answer: "ша"
- sentence: "лю-ди-___"
  answer: "на"
- sentence: "шо-ко-___"
  answer: "лад"
:::

## Голосні́ лі́тери (Vowel Letters)

Ukrainian has six vowel sounds but ten vowel letters. In Module 1, you met this fact briefly. Now it is time to learn every vowel letter and understand why ten letters exist for only six sounds.

### Simple Vowels

Six letters each make one clean, consistent sound:

| Letter | Sound | Example |
|--------|-------|---------|
| **А** | like "a" in "father" | **мама** |
| **О** | like "o" in "more" | **молоко** |
| **У** | like "oo" in "moon" | **вулиця** |
| **Е** | like "e" in "met" | **метро́** |
| **И** | between "i" in "bit" and "e" in "roses" | **дим** |
| **І** | like "ee" in "see" | **дім** |

No surprises here. Each letter, one sound, every time. Ukrainian vowels do not change based on stress the way English vowels do — the letter **О** always sounds the same whether it is stressed or not.

### Iotated Vowels

Four more letters carry a hidden sound — a short «й» before the vowel:

**Я** = «й» + «а» at the start of a word or after another vowel. So **я́блуко** starts with two sounds: «й» then «а». After a consonant, **Я** softens that consonant instead: in **пі́сня**, the **Н** becomes soft before **Я**.

**Ю** works the same way: «й» + «у» at the start (**юна́к**), but softening after a consonant (**лю́ди** — soft **Л**).

**Є** = «й» + «е» at the start (**єно́т**), softening after a consonant.

**Ї** is uniquely Ukrainian. It always carries both sounds — «й» + «і» — no matter where it appears. It never softens a consonant. You find it at the start of words (**їжа́к**), after vowels (**мої́**), or after an apostrophe (**сім'я́** — but here the **Я** follows the apostrophe, not **Ї**). The letter **Ї** does not exist in Russian. It is distinctly Ukrainian.

:::tip
The difference between **И** and **І** changes meaning. **Кит** means "whale." **Кіт** means "cat." **Дим** means "smoke." **Дім** means "house." Small letter, big difference.
:::

:::match-up
title: "Iotated vowels — what sounds do they carry?"
---
- left: "Я (word start)"
  right: "«й» + «а»"
- left: "Ю (word start)"
  right: "«й» + «у»"
- left: "Є (word start)"
  right: "«й» + «е»"
- left: "Ї (always)"
  right: "«й» + «і»"
:::

## Чита́ння слів (Reading Words)

You know all the letters from Module 1. You know how syllables work. Now put it all together: read real Ukrainian words, not letter by letter, but syllable by syllable.

The key shift is this: stop looking at individual letters. Instead, find the vowels first, then group the consonants around them. Your eyes should land on syllables, not single characters.

Take the word **кни́га**. Find the vowels: **И** and **А**. That means two syllables. The division: **кни-га**. Now read each syllable, then blend: **книга**. It means "book."

Try **столи́ця**. Vowels: **О**, **И**, **А** — three syllables. Division: **сто-ли-ця**. This word means "capital city." **Ки́їв** — **столиця**.

### Common Word Patterns

Recognizing patterns makes reading faster. Here are the most common shapes of Ukrainian words:

**Two-syllable (CVCV):** **мама**, **та́то**, **каша**, **вода́**, **рука́**, **хата**, **нога́**, **коза́**

**Two-syllable (CVCCV):** **шко́ла**, **книга**, **па́рта**

**One-syllable (CVC):** **дім**, **сон**, **ліс**, **дуб**, **банк**

The more patterns your eye recognizes, the less you need to sound out. After a few dozen words, you will start reading **мама** as a whole unit, not as **ма** + **ма**.

### Special Combinations — A Preview

Three letter features deserve a quick mention now. Module 3 will cover them fully, but you should know they exist:

**Щ** always sounds like «шч» together — quick and merged. **Що це?** — "What is this?"

**Ь** (soft sign) has no sound of its own. It softens the consonant before it: **день** — "day," **сіль** — "salt."

The apostrophe **'** separates a consonant from an iotated vowel, keeping both sounds distinct: **сім'я** — "family," **м'я́со** — "meat."

:::quiz
title: "Read and choose the meaning"
---
- q: "What does «книга» mean?"
  o: ["school", "book", "table"]
  a: 1
- q: "What does «вулиця» mean?"
  o: ["street", "window", "village"]
  a: 0
- q: "What does «столиця» mean?"
  o: ["table", "capital city", "chair"]
  a: 1
- q: "What does «пісня» mean?"
  o: ["letter", "song", "forest"]
  a: 1
- q: "What does «яблуко» mean?"
  o: ["apple", "egg", "yard"]
  a: 0
- q: "What does «людина» mean?"
  o: ["mirror", "person", "flower"]
  a: 1
:::

## Чита́ємо ра́зом (Reading Together)

Time to practice. Read the words below out loud. Start with the short ones and work your way up. For each word, find the vowels first, split into syllables, then blend.

**Level 1 — Two syllables:** **мама**, **тато**, **вода**, **рука**, **хата**, **каша**, **коза**, **нога**

**Level 2 — Three syllables:** **аптека**, **молоко**, **людина**, **вулиця**, **столиця**, **пісня** <!-- two syllables but included for iotated vowel practice -->

**Level 3 — Four or more syllables:** **університет**, **бібліотека**, **фотогра́фія**, **шоколад**

Now try reading connected text. Every sentence below uses only **Це** + noun or simple location words — no verbs, no grammar yet. Just reading practice:

> **Це Київ. Це столиця. Тут аптека. Там школа. Що це? Це кафе́. А це по́шта. Тут банк. Там бібліотека.**

Read it again, faster. Do not stop between words — let the syllables flow. If a word trips you up, go back to the method: vowels → syllables → blend.

One more passage with new vocabulary:

> **Це парк. Тут фотографія. Що це? Це фонта́н. А там каша? Ні, це шоколад.**

:::group-sort
title: "Sort by syllable count"
---
groups:
  - name: "1 склад"
    items: ["дім", "банк", "сон", "ліс"]
  - name: "2 склади"
    items: ["мама", "каша", "книга", "хата"]
  - name: "3+ склади"
    items: ["молоко", "аптека", "столиця", "університет"]
:::


### Відео — Video

[Повний плейлист / Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)


## Підсумок — Summary

You now have a reliable method for reading any Ukrainian word, no matter how long. The core steps: find the vowels, count the syllables, split the word at syllable boundaries (remembering that consonants prefer to start a new syllable), sound out each syllable, and blend.

You know all ten vowel letters: six simple ones — **А**, **О**, **У**, **Е**, **И**, **І** — and four iotated ones — **Я**, **Ю**, **Є**, **Ї**. You know that **Ї** is uniquely Ukrainian and always carries two sounds.

You have seen how **И** and **І** change meaning: **кит** versus **кіт**, **дим** versus **дім**. You have practiced reading words from one syllable to five, and you have read your first connected Ukrainian texts.

:::caution
The soft sign **Ь** and the apostrophe **'** will be covered fully in Module 3 — Special Signs. For now, just recognize that **Ь** softens and the apostrophe separates.
:::

Test yourself: how many syllables does **бібліотека** have? Find the vowels — **І**, **І**, **О**, **Е**, **А** — five vowels, five syllables: **бі-блі-о-те-ка**. If you got that right, you are ready for Module 3.


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
| **дим** |  |
| **дім** |  |
| **Кит** |  |
| **Кіт** |  |
| **хата** |  |
| **сон** |  |
| **ліс** |  |
| **дуб** |  |
| **ма** |  |
| **день** |  |
| **сіль** |  |
| **сім'я** |  |
| **коза** |  |
| **нога** |  |
| **Це** |  |


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

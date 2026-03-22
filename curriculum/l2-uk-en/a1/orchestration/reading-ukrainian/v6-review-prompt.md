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

There is a golden rule taught to every Ukrainian first-grader, straight from the pages of Большако́ва's буква́р on page 25: **«У сло́ві сті́льки складів, скі́льки голосни́х зву́ків»** — a word has as many syllables as it has vowel sounds. This rule never breaks. Look at the word **ма́ма** — it has two vowels, **А** and **А**, so it splits into two syllables: **ма-ма**. The word **молоко́** has three vowels, all **О**: **мо-ло-ко** — three syllables. What about **банк**? One vowel, **А** — one syllable. No splitting needed. And **сон**? One vowel, **О** — also one syllable. This rule is absolute. No exceptions exist in the entire Ukrainian language. If you can find the vowels, you can count the syllables.

Now for the method. Большакова's page 29 outlines the **звукови́й ана́ліз** — the sound analysis method that Ukrainian children use to read any unfamiliar word. It works in four steps. First, find all the vowels — they are the cores of each syllable. Second, split the word at syllable boundaries. Ukrainian follows the **складопо́діл** (open-syllable principle), which means consonants prefer to start new syllables rather than end old ones. Third, sound out each syllable slowly and clearly. Fourth, blend the syllables together at natural speed until the word flows. Walk through it with **апте́ка**: the vowels are **А**, **Е**, **А** — three syllables. Split: **а-пте-ка**. Sound each syllable, then blend: **аптека**. A pharmacy — and you just read it.

Practice the method on progressively harder words. **Оса́** — two vowels, **О** and **А** — two syllables: **о-са**. **Шко́ла** — vowels **О**, **А** — two syllables: **шко-ла**. **Молоко** — three О's, three syllables. Now try **університе́т** — five vowels: **У**, **І**, **Е**, **И**, **Е** — five syllables: **у-ні-вер-си-тет**. Single-vowel words like **ліс**, **дуб**, and **хліб** are one syllable each — no splitting needed, just read them whole. This is exactly how Большакова's classroom exercise works: *«Ви́знач, скільки складів у ко́жному слові»* — determine how many syllables each word has. You are now doing what Ukrainian first-graders do.

:::quiz
title: "Скільки складів? (How many syllables?)"
---
- q: "сон"
  o: ["1", "2", "3"]
  a: 0
- q: "оса"
  o: ["1", "2", "3"]
  a: 1
- q: "ка́ша"
  o: ["1", "2", "3"]
  a: 1
- q: "молоко"
  o: ["2", "3", "4"]
  a: 1
- q: "анана́с"
  o: ["2", "3", "4"]
  a: 1
- q: "кни́га"
  o: ["1", "2", "3"]
  a: 1
- q: "бібліоте́ка"
  o: ["3", "4", "5"]
  a: 2
- q: "університет"
  o: ["4", "5", "6"]
  a: 1
:::

## Голосні́ лі́тери (Vowel Letters)

You learned in M01 that Ukrainian has 6 vowel sounds but 10 vowel letters. Now it is time to meet each one individually. The six simple vowels each produce one consistent sound — no surprises, no variations. **А** sounds like the "a" in "father" (**мама**). **О** is a pure, rounded "o" (**молоко**). **У** sounds like the "oo" in "moon" (**ву́лиця**). **Е** is an open "e" as in "bed" (**день**). **И** is lower and more central, without an exact English match (**кит**). **І** is higher and fronter, closer to "ee" in "see" (**кіт**). Each letter maps to exactly one sound, every time. These six are the syllable-building sounds you just learned to count.

Now meet the iotated vowels — the four letters that can represent two sounds at once. **Я** equals [й] + [а] at the start of a word (**я́блуко** — apple) or after another vowel (**моя́**). But after a consonant, **Я** softens that consonant and adds [а]: in **пі́сня** (song), the **Н** before **Я** becomes soft. **Ю** works the same way: [й] + [у] at a word start (**юна́к** — young man) or after a vowel; after a consonant, it softens + [у] (**люблю́**). **Є** follows the pattern too: [й] + [е] at word start (**єно́т** — raccoon) or after a vowel (**си́нє**); after a consonant, softening + [е]. Then there is **Ї** — the uniquely Ukrainian letter. **Ї** always represents [й] + [і], without exception. It never softens a consonant. It appears only at a word start (**їжа́к** — hedgehog), after a vowel (**мої́**), or after an apostrophe (**з'їв**). No other Slavic language has **Ї**.

Why does precision with vowels matter so much? Because one vowel letter can change the entire meaning of a word. Consider these critical minimal pairs: **кит** (whale) vs **кіт** (cat), **дим** (smoke) vs **дім** (house), **лис** (fox) vs **ліс** (forest), **бик** (bull) vs **бік** (side). The **И** vs **І** distinction does not exist in English — both sound "ee"-adjacent, but they differ in tongue position. **И** is lower and more central; **І** is higher and fronter. Listen to Anna's pronunciation videos for audio examples of each pair. Also compare **би́ти** (to hit) vs **бі́ти** (beats) — the vowel alone changes the meaning. This is why reading each vowel carefully matters from day one.

:::match-up
title: "Iotated vowels — match to sound components"
---
- left: "Я"
  right: "[й] + [а]"
- left: "Ю"
  right: "[й] + [у]"
- left: "Є"
  right: "[й] + [е]"
- left: "Ї"
  right: "[й] + [і]"
:::

## Чита́ння слів (Reading Words)

The single most important reading habit to build right now: never read letter-by-letter — read syllable-by-syllable. Apply the method from Section 1 to real words immediately. Take **книга**: find the vowels **И** and **А** — two syllables. Split: **кни-га**. Blend: **книга** — a book. Now **школа**: vowels **О** and **А** — split **шко-ла** — blend **школа** — a school. Try **столи́ця**: vowels **О**, **И**, **А** — three syllables, **сто-ли-ця**. **Ки́їв** — **столиця**. The faster your eye spots vowels, the faster you read. And here is welcome news: Ukrainian spelling is highly regular. Once you know the letters, reading is predictable. There are no silent letters, no surprise pronunciations. Unlike English, where "though," "through," and "thought" all sound different, Ukrainian letters behave consistently.

Building reading fluency depends on recognizing common word patterns. Start with the easiest: CVCV words (consonant-vowel-consonant-vowel), where every syllable ends in a vowel. These are open syllables, and they flow naturally: **мама**, **та́то**, **каша**, **вода́**, **рука́**, **ха́та**, **коза́**, **нога́**. Read each one — they practically read themselves. Next, CVCCV words with a consonant cluster: **школа**, **книга**, **па́рта** — the cluster stays together at the start of the second syllable. Then CVC words — closed, single-syllable: **дім**, **сон**, **ліс**, **дуб**, **хліб**, **банк**. No splitting needed at all. Practice reading each group aloud, starting slow, then faster. The more patterns your eye recognizes, the less you need to consciously split syllables.

Three special letter combinations appear in many common words. Full treatment comes in M03, but here is a preview. **Щ** always sounds like [шч] — as in **що** (what), **ще** (more), **ща́стя** (happiness). Do not try to pronounce it as a single sound; it is always the two-sound combination [шч]. **Ь** (the soft sign) has no sound of its own — it softens the consonant that comes before it: **день** — the **Н** becomes soft; **сіль** — the **Л** becomes soft; **кінь** — again, a soft **Н**. Then the apostrophe (**'**) separates a consonant from an iotated vowel, preserving the [й] sound: **сім'я́** (family) — without the apostrophe, the **Я** would soften **М** instead of keeping its full [йа] sound. Same with **м'я́со** (meat) and **п'ять** (five). Think of the apostrophe as a wall — the consonant stays hard on one side, and the vowel keeps both of its sounds on the other.

:::fill-in
title: "Ро́зділи на склади (Divide into syllables)"
---
- sentence: "молоко → ___"
  answer: "мо-ло-ко"
- sentence: "аптека → ___"
  answer: "а-пте-ка"
- sentence: "вулиця → ___"
  answer: "ву-ли-ця"
- sentence: "шокола́д → ___"
  answer: "шо-ко-лад"
- sentence: "люди́на → ___"
  answer: "лю-ди-на"
- sentence: "яблуко → ___"
  answer: "я-блу-ко"
- sentence: "столиця → ___"
  answer: "сто-ли-ця"
- sentence: "бібліотека → ___"
  answer: "бі-блі-о-те-ка"
:::

## Чита́ємо ра́зом (Reading Together)

Time to put everything together with a progressive reading ladder — from simple to ambitious. **Level 1** (2 syllables): **мама**, **тато**, **вода**, **рука**, **хата**, **каша**. All CVCV, all open syllables — the gentlest entry point. **Level 2** (3 syllables): **аптека**, **молоко**, **людина**, **вулиця**. Longer, but every word follows the same regular patterns. **Level 3** (4+ syllables): **університет**, **бібліотека**, **фотогра́фія**, **шоколад**. These look intimidating at first glance, but they follow the same rules as every word before them. Find the vowels, split into syllables, sound out, blend. Try reading each word three times: once slowly, once at medium speed, once at natural conversational pace.

Now read a connected text — all using the **Це** + noun pattern, no conjugated verbs required yet.

> **Це Київ. Це столиця. Тут аптека і банк. Там школа. Що це? Це кафе́. А це по́шта. Ось бібліотека. Там кни́ги.**

Every word in this text uses letters and patterns from M01 and this module. Read it once slowly, syllable by syllable, then again at natural speed. Notice how Ukrainian sentences are short and direct — noun after noun, no articles. There is no "a" or "the" in Ukrainian. **Це кафе** means "This is a café" — three words instead of four. If you can read this entire paragraph aloud without stopping to decode any word, you are reading Ukrainian. Not letter-by-letter, not guessing — actually reading.

:::quiz
title: "Що це сло́во означа́є? (What does this word mean?)"
---
- q: "молоко"
  o: ["apple", "milk", "bread", "water"]
  a: 1
- q: "яблуко"
  o: ["street", "song", "apple", "house"]
  a: 2
- q: "людина"
  o: ["person", "library", "porridge", "capital"]
  a: 0
- q: "столиця"
  o: ["school", "capital", "pharmacy", "book"]
  a: 1
- q: "книга"
  o: ["cat", "street", "book", "whale"]
  a: 2
- q: "вулиця"
  o: ["milk", "university", "person", "street"]
  a: 3
:::


### Відео — Video

[Повний плейлист / Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)


## Підсумок — Summary

Four key skills now belong to you. First, **syllable counting** — **«У слові стільки складів, скільки голосних звуків»** — a rule that works for every Ukrainian word without exception. Count the vowels and you know the syllables. Second, the **vowel letter system** — 6 simple vowels (**А**, **О**, **У**, **Е**, **И**, **І**), each making one consistent sound; 4 iotated vowels (**Я**, **Ю**, **Є**, **Ї**), which can produce two sounds or soften a preceding consonant. **Ї** always stays [йі] — uniquely Ukrainian, never softening. Third, a **reading strategy** that works on any word: find vowels → split into syllables → sound out → blend. Never read letter-by-letter. Fourth, a **preview of special signs** — **Щ** always equals [шч], **Ь** softens the consonant before it, and the apostrophe separates consonant from iotated vowel. These will be explored fully in M03.

Self-check: read **бібліотека** aloud. How many syllables? Five: **бі-блі-о-те-ка**. Now spot the vowels in **університет**: **У**, **І**, **Е**, **И**, **Е** — five vowels, five syllables. If you can do this quickly and confidently, you are ready for the next module: **Special Signs** — where **Ь**, the apostrophe, and the full consonant system take center stage.


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

| Слово | Частина мови | Рід |
|-------|-------------|-----|
| **сон** | ім. | ч. |
| **ліс** | ім. | ч. |
| **дуб** | ім. | ч. |
| **хліб** | ім. | ч. |
| **день** | ім. | ч. |
| **кит** | ім. | ч. |
| **кіт** | ім. | ч. |
| **з'їв** | дієсл. |  |
| **дим** | ім. | ч. |
| **дім** | ім. | ч. |
| **лис** | ім. | ч. |
| **бик** | ім. | ч. |
| **бік** | ім. | ч. |
| **сіль** | ім. | ж. |
| **кінь** | ім. | ч. |
| **п'ять** | числ. |  |
| **хата** | ім. | ж. |
| **Це кафе** |  |  |


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

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

Look at this word: **університе́т**. Five consonants, five vowels, twelve letters total. How would you even start reading it? Here is the golden rule, taught on page 25 of every Ukrainian буква́р: **«У сло́ві сті́льки складів, скі́льки голосни́х зву́ків»** — a word has as many syllables as it has vowel sounds. Count the vowels, count the syllables. This rule never breaks. Take **ма́ма**: two vowels (А, А) = two syllables, **ма-ма**. Take **молоко́**: three vowels (О, О, О) = three syllables, **мо-ло-ко**. Take **банк**: one vowel (А) = one syllable. Simple and absolute.

Now for the method. Ukrainian children learn to read using звукови́й ана́ліз — sound analysis — from the Большако́ва буквар. Here is how it works for any new word. Step one: find the vowels — circle them mentally, because they are the skeleton of the word. Step two: split at syllable boundaries. Ukrainian follows the open-syllable principle — consonants prefer to start new syllables rather than close old ones. Step three: sound out each syllable slowly. Step four: blend them together at natural speed. Watch this in action with **апте́ка**: find the vowels А, Е, А → split **а-пте-ка** → say each syllable → blend into **аптека**. Three vowels, three syllables, every time.

Practice the method on progressively longer words. **Оса́**: vowels О, А → **о-са** (2 syllables). **Шко́ла**: vowels О, А → **шко-ла** (2 syllables). **Молоко**: vowels О, О, О → **мо-ло-ко** (3 syllables). **Університет**: vowels У, І, Е, И, Е → **у-ні-вер-си-тет** (5 syllables). Every Ukrainian word, no matter how long, follows the same rule. Find the vowels first — they are the skeleton.

:::fill-in
title: "Поді́ли на склади (Divide into syllables)"
---
- sentence: "шо-ко-___"
  answer: "лад"
- sentence: "бі-блі-о-те-___"
  answer: "ка"
- sentence: "ву-ли-___"
  answer: "ця"
- sentence: "лю-ди-___"
  answer: "на"
- sentence: "сто-ли-___"
  answer: "ця"
- sentence: "ка-___"
  answer: "ша"
- sentence: "пі-___"
  answer: "сня"
- sentence: "я-блу-___"
  answer: "ко"
:::

Now try counting without splitting. How many syllables? Count the vowels: **бібліоте́ка** — І, І, О, Е, А — five. **Фотогра́фія** — О, О, А, І, А — five. **Люди́на** — Ю, И, А — three. **Ву́лиця** — У, И, А — three. **Ка́ша** — А, А — two. **Дім** — І — one. **Сон** — О — one. **Хліб** — І — one. Knowing the syllable count helps you predict a word's rhythm and prepares you for finding the stressed syllable — **на́голос** — coming in M03.

## Голосні́ лі́тери (Vowel Letters)

Recall from M01: Ukrainian has 6 vowel sounds but 10 vowel letters. Now it is time to learn each one. Start with the simple vowels — six letters that each make exactly one sound: **А**, **О**, **У**, **Е**, **И**, **І**. No surprises, no variations. One letter = one sound, always. These are the straightforward ones.

The four remaining vowels are called iotated — they can represent TWO sounds. **Я** = [й] + [а] at word start: **я́блуко**, **я́ма**, **я́сен**. The same happens after a vowel: **моя́**, **мрі́я** — the **Я** starts a new syllable, so it keeps both sounds. After a consonant, **Я** softens that consonant and contributes only [а]: **пі́сня** — the **Н** becomes soft. The same pattern applies to **Ю** = [й] + [у] at word start (**ю́рта**) but softening after a consonant (**люблю́**). And **Є** = [й] + [е] at word start (**єно́т**) or after a vowel (**си́нє**). The textbook example makes it clear: **мая́к** → **ма-як** — the **Я** starts a new syllable, so it sounds as [йа].

**Ї** stands alone. It ALWAYS represents two sounds, [й] + [і], and never softens a consonant. It appears only at word start (**їжа́к**), after a vowel (**мої́**, **твої́**, **лі́лії**), or after an apostrophe (**з'ї́ла**). This letter exists only in Ukrainian — not in Russian, not in any other Slavic language. From the textbook: **«Колюче їжаченя́ з'ї́ло слимака́»** — even in a full sentence, **Ї** keeps its two sounds.

:::match-up
title: "У́твори па́ру — iotated vowels and their sounds"
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

Now for the hardest pair: **И** vs **І**. These two vowels trouble English speakers most, because English has nothing quite like either one. But in Ukrainian, confusing them changes meaning completely. **Кит** (whale) vs **кіт** (cat). **Дим** (smoke) vs **дім** (house). **Лис** (fox) vs **ліс** (forest). **И** sits deeper in the mouth — a back vowel. **І** is brighter, more forward. Anna's pronunciation videos in the playlist cover this pair in detail — listen to them for ear training.

:::quiz
title: "Скільки складів? (How many syllables?)"
---
- q: "бібліотека"
  o: ["3", "4", "5"]
  a: 2
- q: "їжак"
  o: ["1", "2", "3"]
  a: 1
- q: "яблуко"
  o: ["2", "3", "4"]
  a: 1
- q: "університет"
  o: ["4", "5", "6"]
  a: 1
- q: "дім"
  o: ["1", "2", "3"]
  a: 0
- q: "молоко"
  o: ["2", "3", "4"]
  a: 1
- q: "фотографія"
  o: ["4", "5", "6"]
  a: 1
- q: "каша"
  o: ["1", "2", "3"]
  a: 1
:::

Here is the full picture. The 10 vowel letters organize neatly into two rows: simple (**А О У Е И І**) and iotated (**Я Ю Є Ї**). Notice the pairing: А↔Я, У↔Ю, Е↔Є, І↔Ї. Each iotated letter adds [й] before its paired vowel sound. This visual pattern makes all ten easy to remember.

## Чита́ння слів (Reading Words)

Time to move from individual letters to fluent word reading. The key principle: do not read letter-by-letter — read syllable-by-syllable. The syllable is the natural reading unit in Ukrainian, and this is exactly how Ukrainian children learn with the Большакова method. Letter-by-letter reading is slow and loses meaning. Watch the method in action. Take **кни́га**: find the vowels И, А → split **кни-га** → read each syllable → blend the word. Now **школа**: vowels О, А → **шко-ла** → blend. Two syllables, two clean steps, one word.

Common word patterns help build speed. Start with **CVCV** (consonant-vowel-consonant-vowel) — the easiest pattern, two open syllables: **мама**, **та́то**, **каша**, **вода́**, **рука́**, **ха́та**, **коза́**, **нога́**. Next, **CVC** — one closed syllable, very common in short words: **дім**, **сон**, **ліс**, **дуб**, **хліб**. Then **CVCCV** — a consonant cluster in the middle, where you split before the cluster: **школа**, **книга**, **па́рта**. Practice reading each group aloud. Start slow, then build speed with each pass.

Watch for three special letter combinations. **Щ** always sounds like [шч] — **що**, **ще**, **ща́стя** — never just [ш]. **Ь** (the soft sign) has no sound of its own; it softens the preceding consonant: **день**, **сіль**, **кінь**. The apostrophe (**'**) separates a consonant from an iotated vowel: **сім'я́**, **м'я́со**, **п'ять**. These three will be explored fully in M03 — for now, just recognize them when you encounter them while reading.

:::quiz
title: "Що це сло́во? (Read the word, choose the meaning)"
---
- q: "яблуко"
  o: ["milk", "apple", "street"]
  a: 1
- q: "молоко"
  o: ["person", "milk", "porridge"]
  a: 1
- q: "людина"
  o: ["person", "capital", "library"]
  a: 0
- q: "столи́ця"
  o: ["street", "chocolate", "capital"]
  a: 2
- q: "вулиця"
  o: ["song", "street", "apple"]
  a: 1
- q: "шокола́д"
  o: ["school", "porridge", "chocolate"]
  a: 2
:::

A reading tip from Ukrainian classrooms: when you encounter a new word, use finger tracking. Point to each syllable as you say it, then remove your finger and say the whole word smoothly. This physical technique bridges syllable-by-syllable reading to fluent whole-word recognition. Ukrainian teachers use this method throughout Grades 1 and 2 — it works for adult learners too.

Now combine both skills — syllable splitting and iotated vowels — in one reading pass. **Яблуко**: **я-блу-ко**, where **Я** is at word start = [йа]. **Пісня**: **пі-сня**, where **Я** follows a consonant = softening. **Моя**: **мо-я**, where **Я** follows a vowel = [йа]. Each position of the iotated vowel changes its role. Recognizing this pattern is the key to reading any word with **Я**, **Ю**, **Є**, or **Ї**.

## Чита́ємо ра́зом (Reading Together)

A progressive reading ladder — start with the easiest words and build confidence. Level 1, two syllables: **мама**, **тато**, **вода**, **рука**, **хата**, **каша**. Level 2, three syllables: **аптека**, **молоко**, **людина**, **вулиця**. Level 3, four or more syllables: **університет**, **бібліотека**, **фотографія**. Read each level until comfortable, then move up. Speed is not the goal — accuracy is.

Now try connected reading. These sentences use only the **Це** + noun structure — no verb conjugation needed:

> Це Ки́їв. Це столиця. Тут аптека і банк. Там школа. Що це? Це кафе́. А це по́шта. Це вулиця. Тут людина. Це мама і тато.

Read the passage slowly first, syllable by syllable. Then read it again faster, blending words. Notice how much you can already read after just two modules — real Ukrainian sentences about a real Ukrainian city. Every word in that passage follows the rules you learned today.

Final self-assessment — try reading these six words without any help, then check your syllable count. **Бібліотека** (5 syllables — all simple vowels). **Їжаченя** (4 syllables — **Ї** at word start). **Яблуко** (3 syllables — **Я** at word start). **Сім'я** (2 syllables — apostrophe separating). **Столиця** (3 syllables — **ЦЯ** combination). **Щастя** (2 syllables — **Щ** + softened **ТЬ**). If you can read all six, you are ready for M03.


### Відео — Video

[Повний плейлист / Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)


## Підсумок — Summary

Three core skills from this module. First: the syllable rule — count vowels to count syllables, and it works every time. **«У слові стільки складів, скільки голосних звуків.»** Second: the 10 vowel letters — 6 simple (**А О У Е И І**) and 4 iotated (**Я Ю Є Ї**). Iotated vowels represent two sounds at word or syllable start but soften the preceding consonant elsewhere. The exception is **Ї**, which always keeps both sounds. Third: the reading strategy — find vowels, split into syllables, blend. You now have a method to read any Ukrainian word, no matter how long.

Self-check questions for review. How do you count syllables in a Ukrainian word? What are the 6 vowel sounds? Name the 4 iotated vowel letters. What does **Ь** do? What does the apostrophe do? How many syllables in **бібліотека**? The answer: 5 — count the vowels І, І, О, Е, А. Next module — M03, Special Signs — a deep dive into **Ь**, the apostrophe, and consonant features.


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
| **Дім** |  |
| **Сон** |  |
| **Хліб** |  |
| **Кит** |  |
| **кіт** |  |
| **Дим** |  |
| **Лис** |  |
| **ліс** |  |
| **А О У Е И І** |  |
| **Я Ю Є Ї** |  |
| **дуб** |  |
| **що** |  |
| **ще** |  |
| **день** |  |
| **сіль** |  |
| **кінь** |  |
| **п'ять** |  |
| **Моя** |  |
| **хата** |  |
| **Це** |  |
| **Їжаченя** |  |
| **Сім'я** |  |
| **ЦЯ** |  |
| **Щастя** |  |
| **ТЬ** |  |


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

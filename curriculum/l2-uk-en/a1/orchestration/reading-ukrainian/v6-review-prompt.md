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
version: '1.1'
title: Reading Ukrainian
subtitle: From letters to words to sentences
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
- section: Склади (Syllables)
  words: 250
  points:
  - 'Большакова Grade 1 p.25: ''У слові стільки складів, скільки голосних звуків.'' Count the vowels, count the syllables.
    This rule never breaks. ма-ма (2 vowels = 2 syllables), мо-ло-ко (3 vowels = 3 syllables), банк (1 vowel = 1 syllable).'
  - 'How to read a new word: 1. Find the vowels (they''re the syllable cores) 2. Split at syllable boundaries (consonants
    prefer starting new syllables) 3. Sound out each syllable 4. Blend into the full word at natural speed Practice: а-пте-ка,
    у-ні-вер-си-тет, шо-ко-лад. Note: Ukrainian phonetic syllable division (складоподіл) follows the open-syllable principle
    — consonants prefer starting new syllables.'
  - 'Following Большакова p.29 звуковий аналіз method: identify vowels, divide into syllables, then read. This is how Ukrainian
    children learn.'
- section: Голосні літери (Vowel Letters)
  words: 300
  points:
  - 'Review from M01: 6 sounds, 10 letters. Now learn all 10 individually. Simple vowels (one sound each): А [а], О [о], У
    [у], Е [е], И [и], І [і]. Each makes ONE consistent sound — no surprises.'
  - 'Iotated vowels (two sounds or softening): Я = [йа] at word start (яблуко) or after vowel (моя). After consonant: softens
    it + [а] (пісня — Н is softened). Ю = [йу] or softening + [у]. Є = [йе] or softening + [е]. Ї = ALWAYS [йі] — never softens.
    Only at word start, after vowel, or after apostrophe. Unique to Ukrainian.'
  - 'Critical minimal pairs: И vs І: кит (whale) vs кіт (cat), дим (smoke) vs дім (house). Listen to Anna''s pronunciation
    videos for each — the difference is subtle but changes meaning.'
- section: Читання слів (Reading Words)
  words: 300
  points:
  - 'Apply M01 letter knowledge to read real words fluently. Strategy: don''t read letter-by-letter. Read syllable-by-syllable.
    Start with the vowels (find them first), then build outward. Example: книга — find vowels И, А → кни-га → read.'
  - 'Common word patterns for reading practice: CVCV: мама, тато, каша, вода, рука, хата, коза, нога CVCCV: школа, книга,
    банда, парта CVC: дім, сон, ліс, дуб, хліб, банк The more patterns you see, the faster you read.'
  - 'Special letter combinations to watch for: Щ is always [шч] — що, ще, щастя. Ь has no sound — it softens: день, сіль,
    кінь. '' (apostrophe) separates: сім''я, м''ясо, п''ять. These will be explored fully in M03.'
- section: Читаємо разом (Reading Together)
  words: 200
  points:
  - 'Progressive reading practice — start simple, build up: Level 1 (2 syllables): мама, тато, вода, рука, хата, каша Level
    2 (3 syllables): аптека, молоко, людина, вулиця Level 3 (4+ syllables): університет, бібліотека, фотографія'
  - 'Reading a simple text (all Це + noun, no verbs): Це Київ. Це столиця. Тут аптека і банк. Там школа. Що це? Це кафе. А
    це пошта.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'Self-check: How do you count syllables in a Ukrainian word? What are the 6 vowel sounds? Name the 4 iotated vowel letters.
    What does Ь do? What does the apostrophe do? Read this word: бібліотека — how many syllables?'
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
  focus: 'Divide words into syllables: мо-ло-ко, ап-те-ка'
  items: 8
- type: quiz
  focus: How many syllables? Count the vowels.
  items: 8
- type: match-up
  focus: 'Match iotated vowels to their sound components: Я=[й]+[а]'
  items: 4
- type: quiz
  focus: Read the word and choose its meaning
  items: 6
connects_to:
- a1-003 (Special Signs)
prerequisites:
- a1-001 (Sounds, Letters, and Hello)
grammar:
- 'Syllable rule: count vowels = count syllables (складоподіл)'
- 10 vowel letters → 6 vowel sounds mapping
- Iotated vowels (Я, Ю, Є as two sounds or softening; Ї always [йі])
- 'Reading fluency: syllable-by-syllable word reading'
- Ь, apostrophe, voiced/voiceless (preview — detailed in M03)
register: розмовний
references:
- title: Большакова Grade 1 буквар, p.25
  notes: 'Syllable rule: ''У слові стільки складів, скільки голосних звуків.'''
- title: Большакова Grade 1 буквар, p.29
  notes: Звуковий аналіз слова method — how to analyze word sounds.
- title: Захарійчук Grade 1 (NUS 2025), p.13-15
  notes: 'Sound notation: [•] for vowels, [–] for consonants, [=] for soft.'
pronunciation_videos:
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

</plan_content>

## Generated Content

<generated_module_content>
<!-- TAB:Урок -->

## Склади (Syllables)

How many syllables does the word **молоко** (milk) have? Before you answer, here is a rule that every Ukrainian first-grader learns on page 25 of their textbook:

:::tip
**У слові стільки складів, скільки голосних звуків.** — A word has as many syllables as it has vowel sounds.
:::

This rule never breaks. Find the vowels, and you have found the syllables. The word **молоко** has three vowels — О, О, О — so it has three syllables: **мо-ло-ко**. The word **мама** (mother) has two vowels — А, А — so two syllables: **ма-ма**. The word **банк** (bank) has one vowel — А — so it is one syllable: **банк**.

This is not a guideline. It is an absolute rule of Ukrainian phonetics.

### How to Read a New Word

Ukrainian children learn to read through a method called **звуковий аналіз** (sound analysis), described in Большакова's Grade 1 textbook on page 29. Here is the process adapted for you:

1. **Find the vowels** — they are the core of every syllable.
2. **Split at syllable boundaries** — in Ukrainian, consonants prefer to start new syllables rather than end old ones. This is the open-syllable principle.
3. **Sound out each syllable** — pronounce them one at a time.
4. **Blend into the full word** — say the syllables together at natural speed.

Try it with **аптека** (pharmacy): vowels are А, Е, А → three syllables → **а-пте-ка**. Now **університет** (university): vowels У, І, Е, И, Е → five syllables → **у-ні-вер-си-тет**. And **шоколад** (chocolate): vowels О, О, А → three syllables → **шо-ко-лад**.

Notice how consonants attach to the following vowel whenever possible. In **аптека**, the П and Т stay with the Е, not with the А before them: **а-пте-ка**, not **ап-те-ка**. This open-syllable pattern is consistent throughout Ukrainian.

:::fill-in
title: "Поділи на склади (Divide into syllables)"
---
- sentence: "мо-ло-___"
  answer: "ко"
- sentence: "а-пте-___"
  answer: "ка"
- sentence: "ка-___"
  answer: "ша"
- sentence: "шо-ко-___"
  answer: "лад"
- sentence: "ву-ли-___"
  answer: "ця"
- sentence: "лю-ди-___"
  answer: "на"
- sentence: "сто-ли-___"
  answer: "ця"
- sentence: "пі-___-я"
  answer: "сн"
:::

## Голосні літери (Vowel Letters)

In Module 1 you learned that Ukrainian has six vowel sounds but ten vowel letters. Now it is time to meet all ten individually and understand why the numbers do not match.

### Simple Vowels — One Letter, One Sound

Six vowel letters each produce exactly one sound, with no surprises:

| Letter | Sound | Example |
|--------|-------|---------|
| **А** | like "a" in "father" | **каша** (porridge) |
| **О** | like "o" in "more" | **молоко** (milk) |
| **У** | like "oo" in "moon" | **вулиця** (street) |
| **Е** | like "e" in "met" | **центр** (centre) |
| **И** | between "i" in "bit" and "e" in "roses" | **дим** (smoke) |
| **І** | like "ee" in "meet" | **дім** (house) |

These six letters are straightforward. Each one maps to a single, consistent sound.

### Iotated Vowels — Two Sounds or Softening

The remaining four vowel letters are called iotated vowels. They behave differently depending on their position in the word.

**Я** — at the beginning of a word or after another vowel, it produces two sounds: a "y"-glide followed by the "a" sound. The word **яблуко** (apple) starts with that "y" + "a" combination. In **моя** (my, feminine), the Я comes after a vowel, so again two sounds. But after a consonant, Я softens that consonant and produces only the "a" sound: in **пісня** (song), the Н becomes soft before Я.

**Ю** works the same way: two sounds at a word start or after a vowel, softening after a consonant. **Є** follows the same pattern with the "e" sound.

**Ї** is unique — and uniquely Ukrainian. It always produces two sounds, no matter where it appears. **Ї** never softens a consonant. It only appears at the beginning of a word, after another vowel, or after an apostrophe. No other Slavic language has this letter.

### Minimal Pairs: И vs І

These two letters look similar and sound close to each other, but they change meaning completely:

- **кит** (whale) vs **кіт** (cat)
- **дим** (smoke) vs **дім** (house)

The difference is subtle but critical. Listen carefully to the pronunciation videos for each pair — your ear will tune in with practice.

:::match-up
title: "Йотовані голосні (Iotated vowels)"
---
- left: "Я"
  right: "[й] + [а]"
- left: "Ю"
  right: "[й] + [у]"
- left: "Є"
  right: "[й] + [е]"
- left: "Ї"
  right: "[й] + [і] — always two sounds"
:::

:::quiz
title: "Скільки складів? (How many syllables?)"
---
- q: "яблуко"
  o: ["2", "3", "4"]
  a: 1
- q: "молоко"
  o: ["2", "3", "4"]
  a: 1
- q: "банк"
  o: ["1", "2", "3"]
  a: 0
- q: "університет"
  o: ["4", "5", "6"]
  a: 1
- q: "каша"
  o: ["1", "2", "3"]
  a: 1
- q: "бібліотека"
  o: ["4", "5", "6"]
  a: 1
- q: "дім"
  o: ["1", "2", "3"]
  a: 0
- q: "людина"
  o: ["2", "3", "4"]
  a: 1
:::

## Читання слів (Reading Words)

You know all 33 letters. You know how syllables work. Now the goal shifts from individual letters to fluid reading. The key: do not read letter by letter. Read syllable by syllable.

### The Strategy

When you see a new word, resist the urge to spell it out one letter at a time. Instead:

1. Spot the vowels first — they tell you the structure.
2. Build outward from each vowel, attaching consonants.
3. Say each syllable, then blend.

Take **книга** (book). Find the vowels: И and А. That gives you two syllables. The consonants К and Н cluster at the start, and Г attaches to the second syllable: **кни-га**. Now say it at natural speed.

### Common Word Patterns

The more patterns you recognize, the faster you read. Here are three common shapes:

**Two-syllable words (CVCV pattern):** **мама** (mother), **тато** (father), **каша** (porridge), **вода** (water), **рука** (hand), **хата** (house), **коза** (goat), **нога** (leg).

**Words with consonant clusters (CVCCV):** **школа** (school), **книга** (book), **парта** (desk).

**One-syllable words (CVC):** **дім** (house), **сон** (dream), **ліс** (forest), **дуб** (oak), **хліб** (bread), **банк** (bank).

Practice reading each group aloud. Start slowly, then increase speed. The goal is to hear syllables, not individual letters.

### Special Combinations — A Preview

Three things will appear in words you read, even before Module 3 explains them fully:

**Щ** always sounds like "sh" followed quickly by "ch" — as in **що** (what) and **ще** (still, more).

**Ь** (soft sign) has no sound of its own. It softens the consonant before it: **день** (day), **сіль** (salt), **кінь** (horse).

**Апостроф** (apostrophe) separates a consonant from an iotated vowel, preventing softening: **сім'я** (family), **м'ясо** (meat), **п'ять** (five). These will be explored in detail in Module 3.

:::quiz
title: "Що це за слово? (What is this word?)"
---
- q: "хліб"
  o: ["bread", "house", "forest"]
  a: 0
- q: "книга"
  o: ["school", "book", "desk"]
  a: 1
- q: "вулиця"
  o: ["capital", "street", "pharmacy"]
  a: 1
- q: "столиця"
  o: ["capital", "library", "university"]
  a: 0
- q: "яблуко"
  o: ["porridge", "milk", "apple"]
  a: 2
- q: "людина"
  o: ["street", "person", "song"]
  a: 1
:::

## Читаємо разом (Reading Together)

Time to put everything together. Read through each level below, applying the syllable strategy. Start slowly, then push for natural speed.

**Level 1 — Two syllables:** **мама**, **тато**, **вода**, **рука**, **хата**, **каша**.

**Level 2 — Three syllables:** **аптека** (pharmacy), **молоко** (milk), **людина** (person), **вулиця** (street).

**Level 3 — Four or more syllables:** **університет** (university), **бібліотека** (library), **фотографія** (photography).

For each word, find the vowels first, split into syllables, then blend. If a word feels difficult, slow down to syllable speed and try again.

### A Short Reading Passage

Now read this short text. Every sentence uses structures you already know — **Це** (this is), **тут** (here), **там** (there), and question words.

> **Це Київ. Це столиця. Тут аптека і банк. Там школа. Що це? Це кафе. А це пошта.**

Read it again. This time, try to read each sentence without pausing between syllables. You are reading Ukrainian.

:::caution
If you struggled with any word above, go back and apply the four-step method: find vowels → split syllables → sound out → blend. Speed comes from repeating this process, not from skipping it.
:::


### Відео — Video

[Повний плейлист / Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)


## Підсумок — Summary

You now have the tools to read any Ukrainian word, no matter how long or unfamiliar. Here is what you learned:

**The syllable rule** — count the vowels, count the syllables. **Молоко** has three vowels and three syllables. **Банк** has one vowel and one syllable. This rule never fails.

**Six vowel sounds, ten vowel letters.** The simple vowels — А, О, У, Е, И, І — each make one sound. The iotated vowels — Я, Ю, Є — make two sounds at the start of a word or after a vowel, but soften a preceding consonant otherwise. **Ї** always makes two sounds and is unique to Ukrainian.

**The four-step reading method:** find vowels, split into syllables, sound out each one, blend at natural speed.

**Special characters previewed:** Щ (two sounds blended), Ь (softens the consonant before it), apostrophe (separates consonant from iotated vowel). Module 3 explores these in full.

Test yourself: how many syllables in **бібліотека**? Find the vowels — І, І, О, Е, А — five vowels, five syllables: **бі-блі-о-те-ка**. If you got that right, you are ready for Module 3.


<!-- TAB:Словник -->

### Обов'язкові та рекомендовані слова

| Слово | Переклад | Частина мови | Рід |
|-------|----------|-------------|-----|
| **склад** | syllable | ім. | ч. |
| **молоко** | milk | ім. | с. |
| **університет** | university | ім. | ч. |
| **шоколад** | chocolate | ім. | ч. |
| **каша** | porridge | ім. | ж. |
| **вулиця** | street | ім. | ж. |
| **людина** | person | ім. | ж. |
| **столиця** | capital | ім. | ж. |
| **пісня** | song | ім. | ж. |
| **центр** | centre | ім. | ч. |
| **дим** | smoke | ім. | ч. |
| **яблуко** | apple | ім. | с. |
| **моя** | my (feminine) | прикм. |  |
| **кит** | whale | ім. | ч. |
| **кіт** | cat | ім. | ч. |
| **коза** | goat | ім. | ж. |
| **нога** | leg | ім. | ж. |
| **парта** | desk | ім. | ж. |
| **ліс** | forest | ім. | ч. |
| **дуб** | oak | ім. | ч. |
| **хліб** | bread | ім. | ч. |
| **ще** | still; more | присл. |  |
| **день** | day | ім. | ч. |
| **сіль** | salt | ім. | ж. |
| **кінь** | horse | ім. | ч. |
| **сім'я** | family | ім. | ж. |
| **м'ясо** | meat | ім. | с. |
| **п'ять** | five | числ. |  |
| **бібліотека** | library | ім. | ж. |
| **фотографія** | photography | ім. | ж. |
| **тут** | here | присл. |  |
| **там** | there | присл. |  |
| **і** | and | спол. |  |
| **а** | and; but (contrast) | спол. |  |
| **йотований** | iotated (vowel type) | прикм. |  |
| **апостроф** | apostrophe | ім. | ч. |

### Вирази

| Вираз | Переклад |
|-------|----------|
| **звуковий аналіз** | sound analysis |


<!-- TAB:Зошит -->

:::note
Розширені вправи для цього уроку ще в розробці.

Advanced exercises for this module are in development. Check back soon!
:::


<!-- TAB:Ресурси -->

**Джерела — References**

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

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

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

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

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


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 102 words | Not found: 11 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Большакова — NOT IN VESUM
  ✗ Большакова' — NOT IN VESUM
  ✗ Захарійчук — NOT IN VESUM
  ✗ блі — NOT IN VESUM
  ✗ вер — NOT IN VESUM
  ✗ кни — NOT IN VESUM
  ✗ прикм — NOT IN VESUM
  ✗ присл — NOT IN VESUM
  ✗ пте — NOT IN VESUM
  ✗ спол — NOT IN VESUM
  ✗ числ — NOT IN VESUM

Sample of verified words (all confirmed to exist in Ukrainian):
  ✓ Апостроф → lemma: апостроф, POS: noun
  ✓ Банк → lemma: банк, POS: noun
  ✓ Вираз → lemma: вираз, POS: noun
  ✓ Вирази → lemma: вираз, POS: noun
  ✓ Відео → lemma: відео, POS: noun
  ✓ Голосні → lemma: голосний, POS: adj
  ✓ Джерела → lemma: джерело, POS: noun
  ✓ Зошит → lemma: зошит, POS: noun
  ✓ Йотовані → lemma: йотований, POS: adj
  ✓ Київ → lemma: кий, POS: noun
  ✓ Молоко → lemma: молоко, POS: noun
  ✓ Обов'язкові → lemma: обов'язковий, POS: adj
  ✓ Переклад → lemma: переклад, POS: noun
  ✓ Повний → lemma: повний, POS: adj
  ✓ Поділи → lemma: поділ, POS: noun
  ✓ Підсумок → lemma: підсумок, POS: noun
  ✓ Ресурси → lemma: ресурс, POS: noun
  ✓ Розширені → lemma: розширений, POS: adj
  ✓ Рід → lemma: рід, POS: noun
  ✓ Склади → lemma: склад, POS: noun
  ✓ Скільки → lemma: скільки, POS: adv
  ✓ Словник → lemma: словник, POS: noun
  ✓ Слово → lemma: слово, POS: noun
  ✓ Там → lemma: там, POS: adv
  ✓ Тут → lemma: тут, POS: adv
  ✓ Урок → lemma: урка, POS: noun
  ✓ Частина → lemma: частина, POS: noun
  ✓ Читання → lemma: читання, POS: noun
  ✓ Читаємо → lemma: читати, POS: verb
  ✓ аналіз → lemma: аналіз, POS: noun
  ✓ апостроф → lemma: апостроф, POS: noun
  ✓ аптека → lemma: аптека, POS: noun
  ✓ банк → lemma: банк, POS: noun
  ✓ буквар → lemma: буквар, POS: noun
  ✓ бібліотека → lemma: бібліотека, POS: noun
  ✓ вода → lemma: вода, POS: noun
  ✓ вправи → lemma: вправа, POS: noun
  ✓ вулиця → lemma: вулиця, POS: noun
  ✓ голосних → lemma: голосний, POS: adj
  ✓ голосні → lemma: голосний, POS: adj
  ✓ день → lemma: день, POS: noun
  ✓ дим → lemma: дим, POS: noun
  ✓ для → lemma: для, POS: prep
  ✓ дуб → lemma: дуб, POS: noun
  ✓ дім → lemma: дім, POS: noun
  ✓ звуковий → lemma: звуковий, POS: adj
  ✓ звуків → lemma: звук, POS: noun
  ✓ йотований → lemma: йотований, POS: adj
  ✓ кафе → lemma: кафе, POS: noun
  ✓ каша → lemma: каша, POS: noun

</vesum_verification>
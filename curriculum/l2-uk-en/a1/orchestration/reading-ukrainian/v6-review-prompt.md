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

How many syllables does the word **молоко** (milk) have? A Ukrainian first-grader can answer this instantly, because every child in Ukraine learns one unbreakable rule from the very first page of their буквар:

:::tip
**У слові стільки складів, скільки голосних звуків.**
A word has as many syllables as it has vowel sounds.
:::

Count the vowels — count the syllables. It never fails. Look at **молоко**: three vowels (**о**, **о**, **о**), so three syllables: **мо-ло-ко**. The word **мама** (mother) has two vowels (**а**, **а**) — two syllables: **ма-ма**. And **банк** (bank)? One vowel (**а**), one syllable. That's it. No exceptions.

This rule is your key to reading any Ukrainian word, no matter how long. Here is how to approach a word you have never seen before:

1. **Find the vowels** — they are the cores of each syllable.
2. **Split at syllable boundaries** — in Ukrainian, consonants prefer to start new syllables rather than close old ones. This is called the open-syllable principle.
3. **Sound out each syllable** separately.
4. **Blend them together** at natural speed.

Try it with **аптека** (pharmacy): vowels are **а**, **е**, **а** — three syllables. Split: **а-пте-ка**. Notice how the **п** joins the next syllable rather than staying with **а**? That is the open-syllable principle at work. Now try **університет** (university): five vowels, five syllables — **у-ні-вер-си-тет**. And **шоколад** (chocolate): three vowels — **шо-ко-лад**.

This is exactly how Ukrainian children learn to read, following the звуковий аналіз (sound analysis) method from Большакова's Grade 1 буквар. Find the vowels first, then build outward.

Why is this open-syllable principle so important? Because it gives spoken Ukrainian its characteristic flowing, melodic rhythm. When consonants attach to the following vowel rather than the preceding one, words string together smoothly. A word like **добре** (good) is split **до-бре**, not **доб-ре**. A word like **сестра** (sister) is **се-стра**. By practicing this division now, you are training your brain to produce a native-sounding rhythm right from your very first words.

:::fill-in
title: "Поділи на склади (Divide into syllables)"
---
- sentence: "мо-ло-___"
  answer: "ко"
- sentence: "а-пте-___"
  answer: "ка"
- sentence: "ма-___"
  answer: "ма"
- sentence: "шо-ко-___"
  answer: "лад"
- sentence: "ка-___"
  answer: "ша"
- sentence: "во-___"
  answer: "да"
- sentence: "у-ні-вер-си-___"
  answer: "тет"
- sentence: "бі-блі-о-те-___"
  answer: "ка"
:::

## Голосні літери (Vowel Letters)

In Module 1 you learned that Ukrainian has six vowel sounds but ten vowel letters. Now it is time to meet all ten individually and understand why the numbers do not match.

### Simple vowels

Six letters each make one consistent sound, with no surprises:

| Letter | Sound | Example |
|--------|-------|---------|
| **А** | like "a" in "father" | **каша** (porridge) |
| **О** | like "o" in "or" | **молоко** (milk) |
| **У** | like "oo" in "moon" | **вулиця** (street) |
| **Е** | like "e" in "bet" | **аптека** (pharmacy) |
| **И** | no English match — between "i" in "bit" and "y" in "myth" | **дим** (smoke) |
| **І** | like "ee" in "see" | **дім** (house) |

Pay special attention to **И** and **І**. These two letters distinguish words that otherwise look almost identical: **кит** (whale) vs **кіт** (cat), **дим** (smoke) vs **дім** (house). The difference is subtle but it changes meaning completely. To pronounce **І**, smile widely and push your tongue forward — it is a sharp, clear sound. To pronounce **И**, relax your lips, pull your tongue back slightly, and drop your jaw just a bit. If you struggle with **И**, try saying the English word "myth" or "bit" and holding the vowel sound. Listen to Anna's pronunciation videos in the playlist below to train your ear to hear this critical distinction before you practice speaking.



### Звуковий запис (Sound Notation)

In many Ukrainian textbooks, such as Захарійчук's Grade 1 *буквар*, you will see a special visual notation used to analyze sounds. A vowel sound is always marked with a solid dot **[•]**. A hard consonant is marked with a single dash **[–]**, and a soft consonant with a double dash **[=]**. For example, the word **дім** (house) would be diagrammed as **[= • –]**, showing a soft consonant (**д** is softened by **і**), a vowel (**і**), and a hard consonant (**м**). This visual system helps young learners map sounds in their head before they fully master reading letters.

### Iotated vowels

The remaining four vowel letters are called iotated because they can represent two sounds at once:

**Я** — at the start of a word or after another vowel, it sounds like «й» + «а». The word **яблуко** (apple) begins with these two sounds blended together. But after a consonant, **Я** softens that consonant and sounds only as «а»: in **пісня** (song), the **Н** before **Я** becomes soft.

**Ю** works the same way: «й» + «у» at a word start, or softening + «у» after a consonant. **Є** follows the same pattern: «й» + «е», or softening + «е».

**Ї** is special — unique to Ukrainian. It always represents two sounds: «й» + «і». Always. It never softens a consonant because it never appears directly after one. You will only find **Ї** at the start of a word, after a vowel, or after an apostrophe.

:::match-up
title: "Йотовані голосні (Iotated vowels and their sounds)"
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

## Читання слів (Reading Words)

You know all the letters from Module 1. You know the syllable rule. Now put them together to read real words — not letter by letter, but syllable by syllable.

Here is the strategy: do not start at the first letter and crawl forward. Instead, scan the word for vowels first. Those vowels are your anchors. Build the syllables around them, then blend.

Take the word **книга** (book). Find the vowels: **и** and **а**. Two syllables: **кни-га**. Read each syllable, then say the whole word at natural speed. Done.

### Common word patterns

The more patterns you recognize, the faster you read. Here are three types you will see constantly:

**Two-syllable words (CVCV pattern):** **мама** (mother), **тато** (father), **каша** (porridge), **вода** (water), **рука** (hand), **хата** (house), **нога** (foot)

**Words with consonant clusters:** **школа** (school), **книга** (book), **парта** (school desk)

**One-syllable words:** **дім** (house), **сон** (sleep/dream), **ліс** (forest), **дуб** (oak), **хліб** (bread), **банк** (bank)

### Special letter combinations

Three things to watch for as you read. These will be explored fully in Module 3, but knowing them now will prevent confusion:

**Щ** always sounds like «ш» + «ч» blended together. You will meet it in common words like **що** (what) and **ще** (more/still).

**Ь** (the soft sign) has no sound of its own. Its job is to soften the consonant before it: **день** (day), **сіль** (salt), **кінь** (horse).

**The apostrophe** (') separates a consonant from an iotated vowel, preventing softening. Without it, the meaning changes. Compare: in the word **м'ясо** (meat), the apostrophe tells you the **м** stays hard and the **я** keeps its full «й» + «а» sound. Without the apostrophe, you would try to soften the **м**, which is physically difficult and sounds completely different to a native speaker. Think of the apostrophe as a tiny speed bump — a micro-pause that keeps the consonant and the vowel strictly separated.

As you practice reading these patterns, do not worry about speed. Speed is a byproduct of accuracy. Your goal right now is to look at a word, identify its vowels, mentally divide it into syllables, and produce the sounds correctly. In the beginning, this will feel like solving a puzzle. That is completely normal. With a few days of practice, your brain will start recognizing common syllables instantly, and the puzzle-solving phase will vanish.

 As you progress, you will naturally stop looking at individual letters and start recognizing entire syllable blocks instantly. The open-syllable principle you practiced earlier means that these blocks are highly predictable and consistent. Your eyes will jump from vowel to vowel, and the surrounding consonants will simply fall into place. This is the ultimate secret to reading Ukrainian fluently: trust the vowels to lead the way.

:::quiz
title: "Скільки складів? (How many syllables?)"
---
- q: "молоко"
  o: ["2", "3", "4"]
  a: 1
- q: "мама"
  o: ["1", "2", "3"]
  a: 1
- q: "банк"
  o: ["1", "2", "3"]
  a: 0
- q: "університет"
  o: ["3", "4", "5"]
  a: 2
- q: "бібліотека"
  o: ["4", "5", "6"]
  a: 1
- q: "каша"
  o: ["1", "2", "3"]
  a: 1
- q: "шоколад"
  o: ["2", "3", "4"]
  a: 1
- q: "людина"
  o: ["2", "3", "4"]
  a: 1
:::

## Читаємо разом (Reading Together)

Time to read. Start with short words and build up. Say each word out loud — reading Ukrainian is a physical skill, and your mouth needs practice.

**Level 1 — two syllables:** **мама**, **тато**, **вода** (water), **рука** (hand), **хата** (house), **каша** (porridge)

**Level 2 — three syllables:** **аптека** (pharmacy), **молоко** (milk), **людина** (person), **вулиця** (street), **столиця** (capital)

**Level 3 — four or more syllables:** **університет** (university), **бібліотека** (library), **фотографія** (photography)

Now read a simple text. Every sentence here uses only the structure «Це» (this is) + a noun — no verbs, no grammar tricks. Just reading practice:

> Це Київ. Це столиця. Тут аптека і банк. Там школа. Що це? Це кафе. А це пошта.

*(This is Kyiv. This is the capital. Here is a pharmacy and a bank. There is a school. What is this? This is a café. And this is the post office.)*

Notice how you can read every word by finding the vowels and building syllables. The word **столиця** has three vowels — **о**, **и**, **я** — so three syllables: **сто-ли-ця**. **Київ** — столиця України.

Let's try one more short text, slightly longer. Remember to breathe and look for the vowels:

> Там ліс і вода. Це мама і тато. А це дім. Тут школа, а там університет. Що там? Там бібліотека.

*(There is a forest and water. This is mom and dad. And this is a house. Here is a school, and there is a university. What is there? There is a library.)*

Read both of these short texts out loud at least three times. The first time, you will decode the syllables. The second time, you will recognize the words. The third time, you will actually be reading fluently in Ukrainian.

:::quiz
title: "Що це означає? (What does it mean?)"
---
- q: "яблуко"
  o: ["milk", "apple", "street"]
  a: 1
- q: "молоко"
  o: ["person", "porridge", "milk"]
  a: 2
- q: "людина"
  o: ["person", "street", "song"]
  a: 0
- q: "столиця"
  o: ["school", "pharmacy", "capital"]
  a: 2
- q: "пісня"
  o: ["book", "song", "house"]
  a: 1
- q: "бібліотека"
  o: ["university", "library", "photography"]
  a: 1
:::




### Відео — Video

[Повний плейлист / Full playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)


## Підсумок — Summary

You now have everything you need to read any Ukrainian word. Here is what you learned:

**The syllable rule** — count the vowels, count the syllables. This rule never breaks. **Молоко** has three vowels, so three syllables. **Банк** has one vowel, so one syllable.

**Ten vowel letters, six vowel sounds.** The simple six — **А**, **О**, **У**, **Е**, **И**, **І** — each make one sound. The iotated four — **Я**, **Ю**, **Є**, **Ї** — can represent two sounds or soften a consonant. **Ї** always has two sounds and is unique to Ukrainian.

**Reading strategy** — find the vowels first, split into syllables, sound out each syllable, then blend. Never read letter by letter.

**Special signs** — **Ь** softens a consonant. The apostrophe prevents softening. **Щ** is always two sounds blended. All three will be covered in depth in Module 3.

Self-check: take the word **бібліотека** (library). How many vowels? Five — **і**, **і**, **о**, **е**, **а**. How many syllables? Five: **бі-блі-о-те-ка**. If you can do that, you can read Ukrainian.


<!-- TAB:Словник -->

### Обов'язкові та рекомендовані слова

| Слово | Переклад | Частина мови | Рід |
|-------|----------|-------------|-----|
| **молоко** | milk | ім. | с. |
| **каша** | porridge | ім. | ж. |
| **вулиця** | street | ім. | ж. |
| **столиця** | capital | ім. | ж. |
| **яблуко** | apple | ім. | с. |
| **пісня** | song | ім. | ж. |
| **людина** | person | ім. | ж. |
| **університет** | university | ім. | ч. |
| **бібліотека** | library | ім. | ж. |
| **фотографія** | photography | ім. | ж. |
| **шоколад** | chocolate | ім. | ч. |
| **склад** | syllable | ім. | ч. |
| **дим** | smoke | ім. | ч. |
| **кит** | whale | ім. | ч. |
| **кіт** | cat | ім. | ч. |
| **нога** | foot | ім. | ж. |
| **парта** | school desk | ім. | ж. |
| **ліс** | forest | ім. | ч. |
| **дуб** | oak | ім. | ч. |
| **хліб** | bread | ім. | ч. |
| **ще** | more; still | присл. |  |
| **день** | day | ім. | ч. |
| **сіль** | salt | ім. | ж. |
| **кінь** | horse | ім. | ч. |
| **м'ясо** | meat | ім. | с. |
| **тут** | here | присл. |  |
| **там** | there | присл. |  |

### Вирази

| Вираз | Переклад |
|-------|----------|
| **звуковий аналіз** | sound analysis |
| **Поділи на склади** | Divide into syllables |


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

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string must be an EXACT substring of the module content — copy-paste it
- Keep fixes minimal — change only what's wrong, preserve surrounding text
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

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

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 100 words | Not found: 11 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Большакова — NOT IN VESUM
  ✗ Большакова' — NOT IN VESUM
  ✗ Захарійчук — NOT IN VESUM
  ✗ Захарійчук' — NOT IN VESUM
  ✗ блі — NOT IN VESUM
  ✗ вер — NOT IN VESUM
  ✗ доб — NOT IN VESUM
  ✗ кни — NOT IN VESUM
  ✗ присл — NOT IN VESUM
  ✗ пте — NOT IN VESUM
  ✗ стра — NOT IN VESUM

All 100 other words are confirmed to exist in VESUM.

</vesum_verification>
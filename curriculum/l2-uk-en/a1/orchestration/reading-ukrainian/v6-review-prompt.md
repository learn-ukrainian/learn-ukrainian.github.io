<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 2: Reading Ukrainian (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Gemini Pro
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-002
level: A1
sequence: 2
slug: reading-ukrainian
version: '1.2'
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
  - 'Большакова Grade 1 p.25: ''У слові стільки складів, скільки голосних звуків.''
    Count the vowels, count the syllables. This rule never breaks. ма-ма (2 vowels
    = 2 syllables), мо-ло-ко (3 vowels = 3 syllables), банк (1 vowel = 1 syllable).'
  - 'How Ukrainian children learn to read — складові ланцюжки (syllable chains):
    Start with a consonant + vowel pair: М → ма, мо, му, ми. Then reverse: ам, ом, ум.
    Then build words: ма-ма, мо-ло-ко. This is bottom-up: sound → syllable → word.
    (Захарійчук Grade 1, p.46; Большакова Grade 1, p.25)'
  - 'Звуковий аналіз слова (Большакова p.29): 1) Визначаю голосні звуки 2) Ділю
    слово на склади 3) Ставлю наголос 4) Позначаю приголосні звуки.
    Chin-test for syllable counting (Кравцова Grade 2, p.13): put your palm under
    your chin, say the word — each chin touch = one syllable.'
  - 'Ukrainian sound notation system (Захарійчук p.15): [●] голосний, [—] твердий
    приголосний, [=] м''який приголосний. Every Ukrainian child learns this in Grade 1.'
- section: Голосні літери (Vowel Letters)
  words: 300
  points:
  - 'Review from M01: 6 sounds, 10 letters. Now learn all 10 individually. Simple
    vowels (one sound each): А [а], О [о], У [у], Е [е], И [и], І [і]. Each makes
    ONE consistent sound — no surprises.'
  - 'Iotated vowels (two sounds or softening): Я = [йа] at word start (яблуко) or
    after vowel (моя). After consonant: softens it + [а] (пісня — Н is softened).
    Ю = [йу] or softening + [у]. Є = [йе] or softening + [е]. Ї = ALWAYS [йі] — never
    softens. Only at word start, after vowel, or after apostrophe. Unique to Ukrainian.'
  - 'Critical minimal pairs: И vs І: кит (whale) vs кіт (cat), дим (smoke) vs дім
    (house). Listen to Anna''s pronunciation videos for each — the difference is subtle
    but changes meaning.'
- section: Читання слів (Reading Words)
  words: 500
  points:
  - 'Apply складові ланцюжки to real words. Don''t read letter-by-letter — read
    syllable-by-syllable. Use звуковий аналіз: find vowels first, split into склади,
    then blend. Example: книга — find vowels И, А → кни-га → read.'
  - 'Progressive difficulty using Ukrainian classification (односкладові → багатоскладові):
    односкладові (1 syllable): дім, сон, ліс, дуб, хліб.
    двоскладові (2 syllables): ма-ма, та-то, во-да, ру-ка, ха-та, ка-ша.
    трискладові (3 syllables): ап-те-ка, мо-ло-ко, лю-ди-на, ву-ли-ця.
    багатоскладові (4+ syllables): у-ні-вер-си-тет, біб-лі-о-те-ка, фо-то-гра-фі-я.'
  - 'Ukrainian city names as reading practice: Ки-їв, Льві-в, О-де-са, Хар-ків,
    Дні-про, Пол-та-ва. Note the different syllable counts and structures.'
  - 'Special letter combinations to watch for (preview for M03): Щ is always [шч] — що, ще.
    Ь has no sound — it softens: день, сіль, кінь. Apostrophe separates: сім''я,
    м''ясо, п''ять. These will be explored fully in M03.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'Self-check: How do you count syllables in a Ukrainian word? What are the 6 vowel
    sounds? Name the 4 iotated vowel letters. What does Ь do? What does the apostrophe
    do? Read this word: бібліотека — how many syllables?'
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
- type: divide-words
  focus: 'Поділи слова на склади: мо-ло-ко, ап-те-ка, у-ні-вер-си-тет'
  items: 8
- type: count-syllables
  focus: 'Порахуй склади — скільки голосних, стільки й складів'
  items: 8
- type: match-up
  focus: 'Match iotated vowels to their sound components: Я=[й]+[а]'
  items: 6
- type: quiz
  focus: Read the word and choose its meaning
  items: 6
- type: odd-one-out
  focus: 'Яке слово зайве? — by syllable count (односкладове серед двоскладових)'
  items: 6
connects_to:
- a1-003 (Special Signs)
prerequisites:
- a1-001 (Sounds, Letters, and Hello)
grammar:
- 'Правило складоподілу: у слові стільки складів, скільки голосних звуків'
- 'Звуковий аналіз слова: визначити голосні → поділити на склади → наголос → приголосні'
- 'Складові ланцюжки: приголосний + голосний = склад (ма, мо, му)'
- 'Ukrainian sound notation: [●] голосний, [—] твердий приголосний, [=] м''який приголосний'
- 10 vowel letters → 6 vowel sounds mapping
- Iotated vowels (Я, Ю, Є as two sounds or softening; Ї always [йі])
- 'Word classification: односкладові, двоскладові, трискладові, багатоскладові'
- Ь, apostrophe (preview — detailed in M03)
register: розмовний
references:
- title: Большакова Grade 1 буквар, p.25
  notes: 'Syllable rule: ''У слові стільки складів, скільки голосних звуків.'''
- title: Большакова Grade 1 буквар, p.29
  notes: Звуковий аналіз слова method — how to analyze word sounds.
- title: Захарійчук Grade 1 (NUS 2025), p.13-15
  notes: 'Sound notation: [•] for vowels, [–] for consonants, [=] for soft.'

</plan_content>

## Generated Content

<generated_module_content>
## Склади (Syllables)

Every Ukrainian first-grader learns one golden rule before reading a single word. The textbook states it plainly: **«У слові стільки складів, скільки голосних звуків»** — a word has as many syllables as it has vowel sounds. This rule never breaks. Look at **мама** (mother): two vowels, А and А, so two syllables — **ма-ма**. Now **молоко** (milk): three vowels, О, О, О — three syllables, **мо-ло-ко**. And **банк** (bank): one vowel, А — one syllable, just **банк**. Count the vowels, count the syllables. Every time.

> **Марко:** Скільки складів у слові "молоко"? *(How many syllables in the word "moloko"?)*
> **Аня:** Три голосні — О, О, О. Отже, три склади: мо-ло-ко! *(Three vowels — O, O, O. So, three syllables: mo-lo-ko!)*
> **Марко:** Правильно! А "банк"? *(Correct! And "bank"?)*
> **Аня:** Тільки один! *(Only one!)*

With that rule in hand, Ukrainian textbooks teach a four-step method called **звуковий аналіз слова** (sound analysis of a word). Большакова's Grade 1 textbook (p.29) lays it out: (1) **Визначаю голосні звуки** — find all the vowels in the word. (2) **Ділю слово на склади** — split the word into syllables, one vowel per syllable. Ukrainian syllables tend to be open (ending in a vowel) — this process is called **складоподіл** (syllable division). (3) **Ставлю наголос** — mark which syllable carries the stress. (4) **Позначаю приголосні звуки** — identify consonants as hard or soft. Walk through it with **мама** (mother): vowels А, А → two syllables **ма-ма** → stress on the first syllable → both М sounds are hard. Now **аптека** (pharmacy): vowels А, Е, А → three syllables **а-пте-ка** → stress on the second syllable → consonants П, Т, К are hard.

For reading, apply звуковий аналіз as a practical strategy: (1) spot the vowels, (2) split into syllables, (3) read each syllable aloud slowly, (4) blend the syllables together at natural speed. Try it: **а-пте-ка** → а... пте... ка → **аптека**. Done.

Here is a physical trick from Кравцова's Grade 2 textbook (p.13): place your palm under your chin and say the word aloud. Each time your chin touches your hand, that is one syllable. Try it with **мо-ло-ко** — you should feel three touches.

Ukrainian Grade 1 textbooks (Захарійчук, p.15) use a simple notation for sound analysis: **[●]** marks a vowel sound, **[—]** marks a hard consonant, and **[=]** marks a soft consonant. For **мама**: [— ● | — ●] — two hard consonants, two vowels, two syllables. For **пісня**: [— ● | — = ●] — the Н before Я is soft. Every Ukrainian child learns these symbols in first grade.

Ukrainian children build reading skill through **складові ланцюжки** (syllable chains). Start with one consonant and cycle through vowels: **М → ма, мо, му, ми, мі, ме**. Then reverse: **ам, ом, ум**. Then build words from the chains: **ма-ма**, **мо-ло-ко**. Add a second consonant: **Т → та, то, ту, ти, ті, те**. Now combine: **та-то**, **мо-ло-то**. This is bottom-up reading: sound → syllable → word.

This method conquers even intimidating long words. Take **шоколад** (chocolate): three vowels О, О, А give **шо-ко-лад** — three syllables. **Університет** (university): five vowels У, І, Е, И, Е give **у-ні-вер-си-тет** — five syllables. **Бібліотека** (library): five vowels І, І, О, Е, А give **бі-блі-о-те-ка** — five syllables. A word that looked impossible becomes five manageable pieces. The rule never fails: count the vowels, and the word opens up.

<!-- INJECT_ACTIVITY: count-syllables -->

## Голосні літери (Vowel Letters)

You already know from M01 that Ukrainian has six vowel sounds but ten vowel letters. The first six are the simple vowels — each letter makes exactly one sound, every time, no surprises. **А** sounds like the "a" in "father" — **аптека** (pharmacy). **О** as in "or" — **молоко** (milk). **У** as in "moon" — **рука** (hand). **Е** is between English "e" in "met" and "a" in "cat" — **вечір** (evening). **И** is a sound English does not have, deeper and more central than "i" — **кит** (whale). **І** is a high front sound, close to "ee" in "see" — **кіт** (cat). These six are completely reliable: what you see is what you say.

The remaining four vowel letters are called iotated vowels: **Я**, **Ю**, **Є**, **Ї**. They follow a two-sound rule. When **Я** appears at the start of a word or after another vowel, it produces two sounds — [й] + [а]. Say **яблуко** (apple): the Я at the beginning gives [йа], so you hear [йа]-блу-ко. The same happens in **моя** (my, feminine): мо-[йа]. But when **Я** comes after a consonant, it does something different — it softens that consonant and adds only [а]. In **пісня** (song), the Н before Я becomes soft. The same pattern applies to **Ю** ([йу] at word start, softening + [у] after consonant) and **Є** ([йе] at word start, softening + [е] after consonant). Look at **людина** (person): Л is softened by Ю. In **вечірнє** (evening, neuter adjective), Н is softened by Є.

<!-- INJECT_ACTIVITY: match-up -->

**Ї** stands apart. It always produces two sounds — [й] + [і] — with zero exceptions. **Ї** never appears directly after a consonant, so it never softens anything. You find it at the start of a word (**їжак** — hedgehog), after a vowel (**країна** — country), or after an apostrophe. **Ї** is distinctly Ukrainian — Russian has no equivalent letter.

Now, the critical minimal pairs: **И** vs **І**. These two sounds distinguish meaning. **Кит** (whale) vs **кіт** (cat). **Дим** (smoke) vs **дім** (house). The difference between [и] (more central, deeper) and [і] (high, front) changes the word entirely. They are two separate phonemes — never interchangeable. Listen carefully to model pronunciations and practice hearing the contrast before you drill.

<!-- INJECT_ACTIVITY: divide-words -->

## Читання слів (Reading Words)

The syllable method is a scaffold, not a permanent crutch. The goal is to internalize the rhythm so you stop reading letter-by-letter and start reading syllable-by-syllable, then word-by-word. Here is the reading strategy in order: (1) spot the vowels — they are the cores of each syllable. (2) Build the consonant clusters around them. (3) Read syllable-by-syllable. (4) Repeat until the word flows at natural speed. Try it with **книга** (book): vowels И and А give two syllables — **кни-га**. Read each piece, then blend: **книга**.

Ukrainian words follow recognizable patterns. The easiest pattern alternates consonant-vowel: **мама** (mother), **тато** (father), **каша** (porridge), **вода** (water), **рука** (hand), **хата** (house), **коза** (goat). These words practically read themselves — each syllable is open, ending on a vowel. Slightly harder are words with consonant clusters before a vowel: **школа** (school), **книга** (book). And then closed-syllable words, where a syllable ends on a consonant: **дім** (house), **сон** (dream), **ліс** (forest), **дуб** (oak), **хліб** (bread), **банк** (bank). Practice each group separately before mixing them. Most Ukrainian syllables are open — ending in a vowel — which makes blending easier than you might expect.

<!-- INJECT_ACTIVITY: quiz -->

Time to read. Start with two-syllable words. Read each one twice — first split, then blended:

**ма-ма** → **мама** (mother). **та-то** → **тато** (father). **во-да** → **вода** (water). **ру-ка** → **рука** (hand). **ха-та** → **хата** (house). **ка-ша** → **каша** (porridge).

Now three-syllable words. Split first, then blend:

**а-пте-ка** → **аптека** (pharmacy). **мо-ло-ко** → **молоко** (milk). **лю-ди-на** → **людина** (person). **ву-ли-ця** → **вулиця** (street). **сто-ли-ця** → **столиця** (capital) — **Київ** (Kyiv) is **столиця** України.

Now the long words. Count the vowels, split, and conquer:

**у-ні-вер-си-тет** → **університет** (university) — five syllables. **бі-блі-о-те-ка** → **бібліотека** (library) — five syllables. **фо-то-гра-фі-я** → **фотографія** (photography) — five syllables. These look intimidating, but the vowel-counting method handles them completely. Finish with Ukrainian city names as a confidence-builder: **Ки-їв** (Kyiv — note the Ї), **О-де-са** (Odesa), **Хар-ків** (Kharkiv), **Дні-про** (Dnipro), **Пол-та-ва** (Poltava).

Three special combinations appear in Ukrainian words that you should recognize now. They will be drilled thoroughly in M03 — today, just notice them when they appear.

First: **Щ** always reads as [шч] — one letter, two sounds. **Що** means "what," **ще** means "still" or "more." Never read Щ as [ш] alone.

Second: **Ь** (the soft sign, **м'який знак**) has no sound of its own. It only softens the consonant before it. **День** (day) — the Н is soft. **Сіль** (salt) — the Л is soft. **Кінь** (horse) — the Н is soft. Think of Ь as a silent softener.

Third: the apostrophe (**'**) separates — it prevents the iotated vowel from softening the preceding consonant. **Сім'я** (family) — the М stays hard, then Я gives [йа]. **М'ясо** (meat) — same pattern. **П'ять** (five) — П stays hard. These three features will be explored fully in M03; for now, recognize them when you see them.

> **Аня:** Бі-блі-о-те-ка... **бібліотека**! *(Library!)*
> **Марко:** Так! А це? *(Yes! And this?)*
> **Аня:** Яб-лу-ко... **яблуко**! *(Apple!)*
> **Марко:** А це — **шоколад**! *(And this is chocolate!)*

Аня uses the syllable method — splitting each word, then blending. Марко confirms and adds a new word. This is exactly how the method works in practice: slow and careful at first, then faster with each repetition.

<!-- INJECT_ACTIVITY: odd-one-out -->

## Підсумок — Summary

Self-check — answer each question before reading the answer:

- **How do you count syllables in a Ukrainian word?** → Count the vowels. Each vowel = one syllable. The rule never breaks.
- **What are the 6 vowel sounds?** → [а], [о], [у], [е], [и], [і].
- **Name the 4 iotated vowel letters.** → **Я**, **Ю**, **Є**, **Ї**.
- **What do Я, Ю, Є do at the start of a word?** → They produce two sounds: Я = [й] + [а], Ю = [й] + [у], Є = [й] + [е].
- **What does Ї always produce?** → Always [й] + [і] — two sounds, no exceptions.
- **What does Ь do?** → It softens the consonant before it but has no sound of its own.
- **What does the apostrophe do?** → It separates the consonant from a following iotated vowel, preventing softening.
- **Read this word and count syllables: бібліотека.** → **Бі-блі-о-те-ка**. Five syllables — five vowels: І, І, О, Е, А.

**Deterministic word count: 1675 words** (calculated by pipeline, do NOT estimate manually)

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

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

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

Verified: 91 words | Not found: 11 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Аня — NOT IN VESUM
  ✗ Большакова' — NOT IN VESUM
  ✗ Захарійчук — NOT IN VESUM
  ✗ Кравцова' — NOT IN VESUM
  ✗ Пол — NOT IN VESUM
  ✗ блу — NOT IN VESUM
  ✗ блі — NOT IN VESUM
  ✗ вер — NOT IN VESUM
  ✗ кни — NOT IN VESUM
  ✗ ків — NOT IN VESUM
  ✗ пте — NOT IN VESUM

All 91 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp__rag__verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp__rag__verify_lemma` — full declension/conjugation for a lemma
- `mcp__rag__search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp__rag__query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp__rag__query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp__rag__search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp__rag__search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp__rag__search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp__rag__search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp__rag__query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp__rag__search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp__rag__search_literary` — verify literary references against primary sources
- `mcp__rag__query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.

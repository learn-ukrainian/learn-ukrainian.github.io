<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 2: Reading Ukrainian (A1, A1.1 [Sounds, Letters, and First Contact])
**Writer:** Gemini
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
## Склади — Syllables

> **Олена:** Що там? *(What is there?)*
> **Максим:** Тут каша. *(Porridge is here.)*
> **Олена:** А там молоко. *(And milk is there.)*

English syllable division is complicated. In contrast, Ukrainian has one ironclad rule: **У слові стільки складів, скільки голосних звуків.** There are as many syllables as there are vowel sounds. You never have to guess. The word **мама** (mother) has two vowels, making two syllables: **ма-ма**. The word **молоко** (milk) has three vowels, breaking into three syllables: **мо-ло-ко**. Conversely, the word **банк** (bank) forms exactly one syllable: **банк**.

To make counting syllables a physical habit, Ukrainian teachers use the "Chin-test." Place your open palm flat under your chin. Say a word out loud. Every time your chin drops and touches your hand, you have produced one syllable. Try this with the word **тато** (father). Your chin drops twice, confirming two syllables: **та-то**. 

:::tip
Always rely on the vowels. A word like **університет** (university) might look intimidating, but your chin will rhythmically drop exactly five times as you say it. That proves **у-ні-вер-си-тет** has exactly five syllables.
:::

Before children learn to write letters, they are taught to visualize sounds using a simple notation system. A solid dot **[●]** represents a vowel sound. A single dash **[—]** stands for a hard consonant, and a double dash **[=]** marks a soft consonant. For example, the visual model for **мама** (mother) is **[— ● | — ●]**. This visual coding builds a strong mental model of how words are structured.

When it is time to read, Ukrainian pedagogy uses "Syllable Chains" (**складові ланцюжки**). This is a bottom-up method focused entirely on blending sounds. You start with a single consonant sound, like **М**, and attach different vowels to it: **ма**, **мо**, **му**, **ми**. Then, you reverse the order: **ам**, **ом**, **ум**. Once you can fluidly blend these small units, reading words becomes effortless. You take one chunk, **ма**, add another chunk, **ма**, and you read **мама**.

<!-- INJECT_ACTIVITY: count-syllables-practice -->

<!-- INJECT_ACTIVITY: divide-words-practice -->

## Голосні літери — Vowel Letters

> **Тарас:** Хто там? *(Who is there?)*
> **Ігор:** Там кіт. *(A cat is there.)*
> **Тарас:** Ні, це не кіт. *(No, this is not a cat.)*

The Ukrainian vowel system is built on a specific mathematical relationship: ten vowel letters map down to only six core vowel sounds. The foundation starts with the six "simple" vowel letters: **А**, **О**, **У**, **Е**, **И**, and **І**. Each of these letters represents exactly one consistent sound. Unlike English, where the letter "A" shifts its sound heavily depending on the surrounding letters, a Ukrainian **А** will always make the identical sound in every single word you encounter.

The most critical distinction for any new learner is the difference between the letters **И** and **І**. The letter **І** is pronounced at the front of your mouth, while the sound for **И** is pulled further back into your throat. Mixing these up completely changes your sentence. 

:::caution
Pay close attention to vowel placement. The word **кит** means a whale. If you bring the vowel forward and say **кіт**, you are now talking about a cat. The word **дим** means smoke, but change the vowel, and **дім** means a house.
:::

The remaining four vowel letters are the "iotated" vowels: **Я**, **Ю**, **Є**, and **Ї**. Their pronunciation depends on where they sit. Their primary role is to represent two sounds simultaneously: a quick [й] glide attached to a basic vowel. You hear this clearly at the beginning of words or after another vowel. The letter **Я** represents two sounds in **яблуко** (apple) and **моя** (my). The letter **Є** does the same in **єнот** (raccoon). The letter **Ї** is a special exception. It is completely rigid and ALWAYS represents two sounds [йі]. You hear this in **їжак** (hedgehog) and **Україна** (Ukraine).

The letters **Я**, **Ю**, and **Є** have a second, very different function. When placed directly after a consonant, they lose their two-sound glide. Instead, they represent a single vowel sound while softening the consonant right before them. This creates a distinct contrast. The combination **ЛА** sounds firm and hard, but **ЛЯ** sounds soft. The chunk **ЛУ** is hard, while **ЛЮ** is soft. This happens in the word **пісня** (song). The letter **Я** softens the consonant **Н** and then produces the sound of the letter **А**. These vowels carry a hidden [й] sound that melts into the preceding consonant.

<!-- INJECT_ACTIVITY: iotated-vowels-components -->

## Читання слів — Reading Words

> **Богдан:** Де аптека? *(Where is the pharmacy?)*
> **Марія:** Аптека там. *(The pharmacy is there.)*
> **Богдан:** Дякую! *(Thank you!)*

To read properly, you need to apply the five-step Sound Analysis method (**звуковий аналіз слова**). First, pronounce the word aloud. Second, identify all vowel sounds. Third, use those vowels to divide the word into syllables. Fourth, locate the stressed syllable (**наголос**). Fifth, categorize the consonants as hard or soft. While a complex word with soft sounds might be mapped as **[— ● = ●]**, we can analyze the word **книга** (book). We identify the vowels **И** and **А**, dividing it into **кни-га**. The stress falls on the first syllable. The hard consonants make its true model **[— — ● | — ●]**. 

We can classify words by length, starting with one-syllable words (**односкладові**). You should read them as a single burst of sound. Practice this quick blending with **дім** (house). Now try **сон** (dream), **ліс** (forest), **дуб** (oak), and **хліб** (bread). Then you can progress to two-syllable words (**двоскладові**). Because you already know how to identify vowels, these will break cleanly into balanced halves. Try reading **та-то** (father), **во-да** (water), and **ру-ка** (hand). Keep a steady rhythm as you read **ка-ша** (porridge) and **ха-та** (house). The goal is to blend the chunks smoothly into a single breath.

Once you establish that rhythm, three-syllable words (**трискладові**) are completely manageable. You simply apply the syllable rule. The word **аптека** (pharmacy) naturally breaks into **ап-те-ка**. The word **молоко** (milk) becomes the rhythmic sequence **мо-ло-ко**. You can apply the same rhythm to **шоколад** (chocolate), reading it as **шо-ко-лад**. You can effortlessly read **людина** (person) as **лю-ди-на** and **вулиця** (street) as **ву-ли-ця**. Knowing how to spot these chunks opens up massive vocabulary. Look at the word **столиця** (capital). Break it into **сто-ли-ця** and read it fluidly. Now you can read a complete geographic fact: **Київ — столиця України** (Kyiv is the capital of Ukraine).

Take the word **університет** (university). By counting the five vowels, you instantly know there are exactly five syllables: **у-ні-вер-си-тет**. Read each chunk aloud. The same logic applies to the word **бібліотека** (library), which organizes neatly into **біб-лі-о-те-ка**. 

:::note
These international words serve as excellent confidence boosters. The word **фотографія** (photography) breaks down exactly the same way into **фо-то-гра-фі-я**. While these multisyllable words (**багатоскладові**) look massive, they are constructed using the exact same unbreakable syllable rules as the simple word **мама**.
:::

We can use major Ukrainian cities as excellent reading practice. Sounding out **Київ** (Kyiv) forces you to contrast the deep vowel **И** right next to the two-sound vowel **Ї**. The city name **Львів** (Lviv) gives you a preview of a softening sign. The name **Одеса** (Odesa) is a perfectly simple, three-syllable rhythmic word. The name **Харків** (Kharkiv) shows how the letter **І** naturally softens the sound before it. The name **Дніпро** (Dnipro) forces you to blend a tight cluster of consonants. Finally, the name **Полтава** (Poltava) provides a perfectly even and rhythmic flow.

As you practice reading, you will inevitably encounter three special signs. We will cover them deeply in the next module, but knowing them now provides a safety net. The letter **Щ** is entirely unique because it always produces a heavy, double sound: [шч]. You will see this in words like **що** (what) and **ще** (more). The Soft Sign **Ь** makes absolutely no sound of its own; it exists only to soften the letter before it, as seen in **день** (day), **сіль** (salt), and **кінь** (horse). Finally, the apostrophe acts as a hard barrier. It forces the letters apart, preventing softening, as you can see clearly in the words **м'ясо** (meat), **сім'я** (family), and **п'ять** (five).

<!-- INJECT_ACTIVITY: syllable-odd-one-out -->

<!-- INJECT_ACTIVITY: reading-meaning-quiz -->

## Підсумок — Summary

> **Анна:** Це все? *(Is this all?)*
> **Павло:** Так, це все! *(Yes, this is all!)*

We have established the foundational rules for reading the Ukrainian language. Before you move on to the next module, use this self-check to test your new knowledge.

*   How do you count syllables in a Ukrainian word? You simply count the vowels! There are as many syllables as there are vowel sounds.
*   What are the six basic vowel sounds? The foundation is built upon **А**, **О**, **У**, **Е**, **И**, and **І**.
*   Name the four iotated vowel letters. They are **Я**, **Ю**, **Є**, and **Ї**.
*   Which letter is always two sounds [йі]? The unique letter **Ї** always retains its two sounds.
*   What is the difference between **кит** and **кіт**? The deep **И** versus the front **І** sound completely changes the meaning from a whale to a cat.
*   What does the letter **Ь** do? It makes no sound of its own, but softens the consonant right before it.
*   What does the apostrophe do? It acts as a hard barrier, separating a consonant from an iotated vowel.
*   Count the syllables in the word **бібліотека**. It has five vowels, which means exactly five syllables.

You can now sound out any Ukrainian word!
</generated_module_content>

**PIPELINE NOTE — Word count: 1453 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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
| 6 | **Engagement & tone** | 10% | The writer's persona is an encouraging teacher — natural teacher phrasing like "Let us look at..." or "Have you noticed..." is FINE and should NOT be penalized. DEDUCT ONLY for: self-congratulatory openers ("Welcome to A2! Congratulations on completing..."), gamified/corporate language ("You have unlocked...", "You now possess...", "Your journey begins..."), empty filler that adds words but zero information ("This is a very important concept that you will use frequently in your daily life"), generic enthusiasm not specific to Ukrainian ("incredibly beautiful language", "wonderfully consistent system"). REWARD for: teacher warmth with substance, specific cultural details, humor, concrete Ukrainian examples, natural classroom energy. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count BELOW 1200 (more content is always welcome — never penalize for exceeding the target), dangling/incomplete sentences, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count at or above target. |
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
- The `find` string MUST be an EXACT copy-paste from the module content. DO NOT change quotes (« » to " "), dashes (— to -), or spacing. If you change a single character in the `find` string, the automated replacement will fail.
- Keep fixes minimal — change only what's wrong, preserve surrounding text. Provide enough context (e.g. 5-7 words) to make the match unique.
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

Verified: 73 words | Not found: 13 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Анна — NOT IN VESUM
  ✗ Богдан — NOT IN VESUM
  ✗ Дніпро — NOT IN VESUM
  ✗ Львів — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Одеса — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Павло — NOT IN VESUM
  ✗ Полтава — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Харків — NOT IN VESUM
  ✗ вер — NOT IN VESUM
  ✗ кни — NOT IN VESUM

All 73 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp_rag_verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp_rag_verify_lemma` — full declension/conjugation for a lemma
- `mcp_rag_search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp_rag_query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp_rag_query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp_rag_search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp_rag_search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp_rag_search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp_rag_search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp_rag_query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp_rag_search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp_rag_search_literary` — verify literary references against primary sources
- `mcp_rag_query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.

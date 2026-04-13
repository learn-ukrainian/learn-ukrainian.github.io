<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 42: Hey, Friend! (A1, A1.7 [Communication])
**Writer:** Gemini
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-042
level: A1
sequence: 42
slug: hey-friend
version: '1.2'
title: Hey, Friend!
subtitle: Олено! Тарасе! Друже! Мамо! — calling people by name
focus: grammar
pedagogy: PPP
phase: A1.7 [Communication]
word_target: 1200
objectives:
- Form vocative case for common names and family words (Олено! Тарасе! Мамо!)
- Use vocative in greetings and direct address (Привіт, Андрію!)
- Recognize vocative endings for masculine (-е, -у/-ю) and feminine (-о, -ю, -є) nouns
- Address people naturally using vocative in everyday situations
dialogue_situations:
- setting: 'At a busy birthday party — calling people across the room by name: Олено!
    Тарасе! Друже! Мамо! Бабусю! Дідусю! Each person is doing something different
    (dancing, eating, talking).'
  speakers:
  - Іменинник (birthday person)
  - Друзі
  motivation: 'Vocative: Олена→Олено, Тарас→Тарасе, мама→мамо, бабуся→бабусю'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Meeting a friend: — Олено, привіт! Як справи? — Добре, дякую, Тарасе!
    А в тебе? — Теж добре. Олено, ти знаєш мого брата? — Ні. — Андрію, ходи сюди!
    Це Олена. Олено, це Андрій. Vocative forms: Олено (Олена), Тарасе (Тарас), Андрію
    (Андрій).'
  - 'Dialogue 2 — At home: — Мамо, де мій телефон? — На столі, синку. — Тату, а де
    ключі? — У кишені, дочко. — Бабусю, ми йдемо! — Добре, будьте обережні! Family
    vocatives: мамо, тату, синку, дочко, бабусю.'
- section: Кличний відмінок (The Vocative Case)
  words: 300
  points:
  - 'Ukrainian has a special case for calling someone — кличний відмінок. In English
    you just say the name: ''Olena, come here!'' In Ukrainian the name CHANGES: Олена
    → Олено, ходи сюди! This is not optional — Ukrainians always use vocative when
    addressing someone. Grade 4 helper word: Кл. (!) — the exclamation mark reminds
    you: you''re calling someone, so the ending changes.'
  - 'Why vocative matters: Олена прийшла. (Olena came.) — nominative, talking ABOUT
    her. Олено, ходи сюди! (Olena, come here!) — vocative, talking TO her. Using nominative
    to address someone sounds unnatural in Ukrainian. It''s like saying ''Hey, him!''
    instead of ''Hey, you!'' in English.'
- section: Закінчення кличного (Vocative Endings)
  words: 300
  points:
  - 'Feminine names and nouns (-а → -о): Олена → Олено, мама → мамо, сестра → сестро,
    Оксана → Оксано, подруга → подруго, бабуся → бабусю (-ся → -сю). Names on -ка:
    Наталка → Наталко, Ірка → Ірко. Names on -ія: Марія → Маріє (not Маріо!). Names
    on -а (long): Катерина → Катерино, Тетяна → Тетяно.'
  - 'Masculine names and nouns: Hard consonant → -е: Тарас → Тарасе, Іван → Іване,
    брат → брате, пан → пане. Soft consonant / -й → -ю: Андрій → Андрію, дідусь →
    дідусю, вчитель → вчителю. Special: друг → друже (г → ж), козак → козаче (к →
    ч). Тато → тату (exceptional -у ending, memorize).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Vocative quick reference: | Pattern | Nominative → Vocative | Example | | Feminine
    -а | -а → -о | Олена → Олено, мама → мамо | | Feminine -ія | -ія → -іє | Марія
    → Маріє | | Feminine -ся | -ся → -сю | бабуся → бабусю | | Masculine hard | +
    -е | Тарас → Тарасе, брат → брате | | Masculine -й/soft | + -ю | Андрій → Андрію,
    вчитель → вчителю | | Special (г, к) | г→ж, к→ч + -е | друг → друже | Self-check:
    How do you call your family? мама → ? тато → ? брат → ?'
vocabulary_hints:
  required:
  - друг (friend, m)
  - подруга (friend, f)
  - брат (brother, m)
  - сестра (sister, f)
  - пан (Mr., m)
  - пані (Mrs./Ms., f)
  recommended:
  - синку (son — vocative, from син)
  - дочко (daughter — vocative, from дочка)
  - козак (Cossack, m)
  - вчитель (teacher, m)
  - бабуся (grandmother, f)
  - дідусь (grandfather, m)
activity_hints:
- type: fill-in
  focus: 'Write vocative: Олена → Олено, Тарас → Тарасе, мама → мамо'
  items:
  - Олена → {Олено}
  - Тарас → {Тарасе}
  - мама → {мамо}
  - Іван → {Іване}
  - сестра → {сестро}
  - Андрій → {Андрію}
  - подруга → {подруго}
  - брат → {брате}
  - Марія → {Маріє}
  - бабуся → {бабусю}
- type: quiz
  focus: 'Choose correct vocative: (Олена / Олено / Оленю), привіт!'
  items:
  - question: ___, привіт!
    options:
    - Олено
    - Олена
    - Оленю
  - question: Як справи, ___?
    options:
    - Тарасе
    - Тарас
    - Тарасу
  - question: Дякую, ___!
    options:
    - мамо
    - мама
    - маме
  - question: Ходи сюди, ___!
    options:
    - Іване
    - Іван
    - Івану
  - question: Будь обережний, ___!
    options:
    - синку
    - синок
    - синке
  - question: Що ти робиш, ___?
    options:
    - брате
    - брат
    - брату
  - question: Добрий день, ___!
    options:
    - пане
    - пан
    - пану
  - question: Привіт, ___!
    options:
    - Андрію
    - Андрій
    - Андріє
- type: group-sort
  focus: 'Sort vocative endings: -о (feminine) vs -е (masculine hard) vs -ю (masculine
    soft)'
  groups:
  - name: -о (feminine)
    items:
    - Олено
    - мамо
    - сестро
  - name: -е (masculine hard)
    items:
    - Тарасе
    - Іване
    - брате
    - пане
  - name: -ю (masculine soft)
    items:
    - Андрію
    - дідусю
    - вчителю
- type: fill-in
  focus: 'Complete dialogue: ___, привіт! Як справи? (name → vocative)'
  items:
  - — {Олено|Олена}, привіт! Як справи?
  - — Добре, дякую, {Тарасе|Тарас}!
  - — {Мамо|Мама}, де мій телефон?
  - — На столі, {синку|синок}.
  - — {Бабусю|Бабуся}, ми йдемо!
  - — Добре, до побачення, {Андрію|Андрій}!
connects_to:
- a1-043 (Please Do This)
prerequisites:
- a1-041 (Checkpoint — Food and Shopping)
grammar:
- 'Vocative case (кличний відмінок): special endings for direct address'
- Feminine -а → -о (Олена → Олено), -ія → -іє (Марія → Маріє)
- Masculine hard → -е (Тарас → Тарасе), soft/-й → -ю (Андрій → Андрію)
- 'Consonant alternation: друг → друже (г → ж)'
register: розмовний
references:
- title: State Standard 2024, §4.2.3.4
  notes: 'Vocative case — address forms. A1 scope: common patterns only.'
- title: 'Grade 4 textbook: Кличний відмінок (Заболотний)'
  notes: Helper word Кл. (!). Feminine -а→-о, masculine hard→-е, soft→-ю.

</plan_content>

## Generated Content

<generated_module_content>
## Діалоги (Dialogues)

At a birthday party, you often need to call someone across the room: **Олено! Тарасе! Мамо! Бабусю!** In Ukrainian, direct address usually changes the ending of the name or family word. Listen for these forms in the dialogues below.

> **Тарас:** Олено, привіт! Як справи? *(Olena, hi! How are things?)*
> **Олена:** Добре, дякую, Тарасе! А в тебе? *(Good, thanks, Taras! And with you?)*
> **Тарас:** Теж добре. Олено, ти знаєш мого брата? *(Also good. Olena, do you know my brother?)*
> **Олена:** Ні, не знаю. *(No, I do not know.)*
> **Тарас:** Андрію, ходи сюди! Це Олена. Олено, це Андрій. *(Andriy, come here! This is Olena. Olena, this is Andriy.)*
> **Андрій:** Привіт, Олено! *(Hi, Olena!)*
> **Олена:** Привіт, Андрію! *(Hi, Andriy!)*

> **Олег:** Мамо, де мій телефон? *(Mom, where is my phone?)*
> **Мама:** На столі, **синку** (son). А де твій рюкзак? *(On the table, son. And where is your backpack?)*
> **Олег:** Там. *(There.)*
> **Ірина:** Тату, а де ключі? *(Dad, and where are the keys?)*
> **Тато:** У кишені, **дочко** (daughter). *(In the pocket, daughter.)*
> **Олег:** Бабусю, ми йдемо! *(Grandma, we are going!)*
> **Бабуся:** Добре, будьте обережні! *(Good, be careful!)*

Point out the pattern you see in these conversations. Notice how the names and family words change their final letters when the person is addressed directly. The basic name is **Олена** (Olena), but to call her, Taras says **Олено**. The basic name is **Тарас** (Taras), but Olena addresses him as **Тарасе**. The **брат** (brother, m) is **Андрій** (Andriy), but Taras calls him **Андрію** across the room. The exact same transformation happens with family words: **мама** (mom) becomes **мамо**, **тато** (dad) becomes **тату**, and **бабуся** (grandmother, f) becomes **бабусю**. When the parents reply, they use **синку** and **дочко**. These changed endings show that you are talking directly to the person. They act as an auditory signal that says "I am speaking to you now."

:::note
In modern Ukrainian, using these special endings is a sign of good education and politeness. While some people might occasionally mix it up in very fast, informal speech, using the proper endings like **мамо** or **Тарасе** shows that you respect the language and the person you are speaking to.
:::

<!-- INJECT_ACTIVITY: fill-in-dialogue-completion -->

## Кличний відмінок (The Vocative Case)

Ukrainian has a special grammatical case for calling someone or getting their attention: the **кличний відмінок** (vocative case). In standard Ukrainian, direct address normally uses this form: **Олено, ходи сюди!** In school grammar, this case is often remembered with the helper **Кл. (!)** — the exclamation mark signals that you are calling someone, so the ending changes.

:::tip
If you ever forget how to form the vocative case, try to visualize the Ukrainian abbreviation **Кл. (!)**. Imagine you are shouting across a noisy street. You would naturally stretch the end of the name. The vocative endings (**-о**, **-е**, **-ю**) are perfect vowel sounds for calling out loudly!
:::

Why does the vocative case matter so much in daily conversation? It creates a very clear, grammatical distinction between talking ABOUT a person and talking TO a person. When you use the nominative case, you are answering the question "Who is this?" (Хто це?). But when you use the vocative case, you are not answering a question; you are initiating contact. Look at this important difference in structure:

*   **Олена читає.** *(Olena is reading.)* — This uses the nominative case. You are stating a fact about her.
*   **Олено, ходи сюди!** *(Olena, come here!)* — This uses the vocative case. You are addressing her directly.

Using the nominative case to address someone sounds extremely unnatural to a Ukrainian ear. It feels distant, abrupt, and slightly rude, somewhat similar to saying "Hey, him!" instead of "Hey, you!" in English. The vocative case makes your speech sound warm, natural, and polite. It stands apart from the main grammar of the sentence, often separated by a comma.

The vocative case is equally important in formal and professional situations. When you speak to a teacher, a doctor, a manager, or any adult you do not know well, you must use formal titles alongside their name. In Ukrainian, the words **пан** (Mr., m) and **пані** (Mrs./Ms., f) are used to show respect. The word **пані** is a special feminine noun that does not change its ending, but the masculine noun **пан** changes to **пане** in the vocative case.

*   **Добрий день, пане Іване!** *(Good day, Mr. Ivan!)*
*   **Добрий день, пані Оксано!** *(Good day, Ms. Oksana!)*

Use the vocative form in the name. With **пан**, the title also changes (**пане Іване**), but **пані** stays unchanged (**пані Оксано**).

<!-- INJECT_ACTIVITY: quiz-vocative-choice -->

## Закінчення кличного (Vocative Endings)

Let us look at how to form the vocative case endings for different types of words. For most feminine names and feminine nouns that end in the vowel **-а**, the ending changes to **-о**. This is a very consistent and reliable pattern that you will hear constantly.

*   **Олена** → **Олено**
*   **мама** → **мамо**
*   **сестра** (sister, f) → **сестро**
*   **подруга** (friend, f) → **подруго**
*   **Оксана** → **Оксано**

This rule also applies to informal or diminutive names that end in **-ка**:

*   **Наталка** → **Наталко**
*   **Ірка** → **Ірко**

Whenever you see a feminine word ending in a standard **-а**, you can confidently swap it for an **-о** to call that person.

Feminine nouns have two other common patterns depending on their final letters. If a feminine name or noun ends in **-ія**, it changes to **-іє**. Be careful not to say "Маріо" — that sounds like an Italian name!

*   **Марія** → **Маріє**
*   **Юлія** → **Юліє**

If a feminine noun ends in **-ся**, especially affectionate family words, the ending softens and changes to **-сю**.

*   **бабуся** → **бабусю**
*   **Леся** → **Лесю**

Masculine names and nouns work a little differently. If a masculine noun ends in a hard consonant, you simply add the vowel **-е** to the end of the word.

*   **Тарас** → **Тарасе**
*   **Іван** → **Іване**
*   **брат** → **брате**
*   **пан** → **пане**

:::caution
Do not confuse the masculine ending **-е** with English pronunciation rules. The letter **е** in Ukrainian is always pronounced clearly. When you say **Тарасе**, make sure you pronounce the final vowel. It is never a silent letter!
:::

Sometimes, the final consonant of the masculine word changes to make the word easier to pronounce. The hard sound **г** changes to the softer **ж**, and the sound **к** changes to **ч**. This consonant shift is a very old feature of the language and sounds very poetic.

*   **друг** (friend, m) → **друже**
*   **козак** (Cossack, m) → **козаче**

For masculine names and nouns that end in a soft consonant or the letter **-й**, you add or change the ending to the vowel **-ю**.

*   **Андрій** → **Андрію**
*   **дідусь** (grandfather, m) → **дідусю**
*   **вчитель** (teacher, m) → **вчителю**

There is one very important exception that you simply must memorize right now. The common word for dad, **тато**, does not follow the standard feminine **-о** or masculine **-е** rules. It takes a special, unique ending **-у**.

*   **тато** → **тату**

<!-- INJECT_ACTIVITY: group-sort-endings -->
<!-- INJECT_ACTIVITY: fill-in-vocative-forms -->

## Підсумок — Summary

You now know how to address people correctly and naturally in Ukrainian. The vocative case is a beautiful and essential feature of the language that instantly connects you to the person you are speaking with. Here is a quick reference summary table to help you remember the main patterns we covered today:

| Pattern | Nominative → Vocative | Example |
| :--- | :--- | :--- |
| Feminine **-а** | **-а** → **-о** | **Олена** → **Олено**, **мама** → **мамо** |
| Feminine **-ія** | **-ія** → **-іє** | **Марія** → **Маріє** |
| Feminine **-ся** | **-ся** → **-сю** | **бабуся** → **бабусю** |
| Masculine hard | + **-е** | **Тарас** → **Тарасе**, **брат** → **брате** |
| Masculine **-й** / soft | + **-ю** | **Андрій** → **Андрію**, **вчитель** → **вчителю** |
| Special (**г**, **к**) | **г**→**ж**, **к**→**ч** + **-е** | **друг** → **друже**, **козак** → **козаче** |

To truly master the vocative case, you need to practice it out loud with the people you talk to most often. Use these self-check questions to test your memory and build your reflexes. Imagine these people are standing in the next room and you need to call them loudly:

*   How do you call your mom? — **Мамо!**
*   How do you call your dad? — **Тату!**
*   How do you call your brother? — **Брате!**
*   How do you call your friend Taras? — **Тарасе!**
*   How do you call your grandmother? — **Бабусю!**
*   How do you call your friend Andriy? — **Андрію!**
*   How do you call your sister? — **Сестро!**
*   How do you formally address Mr. Ivan? — **Пане Іване!**

By actively using these forms in your daily life, you show that you deeply understand the rhythm, grammar, and respect built into Ukrainian communication.
</generated_module_content>

**PIPELINE NOTE — Word count: 1368 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 70 words | Not found: 23 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іван — NOT IN VESUM
  ✗ Іване — NOT IN VESUM
  ✗ Ірина — NOT IN VESUM
  ✗ Ірка — NOT IN VESUM
  ✗ Ірко — NOT IN VESUM
  ✗ Андрій — NOT IN VESUM
  ✗ Андрію — NOT IN VESUM
  ✗ Лесю — NOT IN VESUM
  ✗ Леся — NOT IN VESUM
  ✗ Маріо — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Маріє — NOT IN VESUM
  ✗ Наталка — NOT IN VESUM
  ✗ Наталко — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Оксано — NOT IN VESUM
  ✗ Олег — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олено — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тарасе — NOT IN VESUM
  ✗ Юлія — NOT IN VESUM
  ✗ Юліє — NOT IN VESUM

All 70 other words are confirmed to exist in VESUM.

</vesum_verification>

---

## Verification Tools (Shell Commands)

You have access to verification tools via shell commands. Use these to verify
Ukrainian vocabulary, check grammar, and search textbook content **as you write**.

**IMPORTANT:** Run verification commands BEFORE finalizing any Ukrainian text.
Batch multiple verifications together to minimize round-trips.

### 1. Batch-verify Ukrainian words exist in VESUM (preferred — one call for many words)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_words
results = verify_words(['слово1', 'слово2', 'слово3'])
for w, matches in results.items():
    if matches:
        print(f'{w}: FOUND — lemma={matches[0][\"lemma\"]}, pos={matches[0][\"pos\"]}')
    else:
        print(f'{w}: NOT FOUND — may not exist in standard Ukrainian')
"
```

### 2. Verify a single Ukrainian word in VESUM (with full morphological tags)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_word
results = verify_word('WORD_HERE')
if results:
    for m in results:
        print(f'lemma={m[\"lemma\"]}, pos={m[\"pos\"]}, tags={m[\"tags\"]}')
else:
    print('NOT FOUND in VESUM')
"
```

### 3. Get all inflected forms of a lemma (declension/conjugation)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from rag.query import verify_lemma
forms = verify_lemma('LEMMA_HERE')
for f in forms[:20]:
    print(f'{f[\"word_form\"]:20s} {f[\"pos\"]:8s} {f[\"tags\"]}')
print(f'... {len(forms)} forms total')
"
```

### 4. Check CEFR level of a word (is it level-appropriate?)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import query_cefr_level
results = query_cefr_level('WORD_HERE')
for r in results:
    print(f'{r[\"word\"]}: {r[\"level\"]} ({r[\"pos\"]})')
if not results:
    print('Not in CEFR database')
"
```

### 5. Search textbook content (Ukrainian school textbooks, Grades 1-11)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_textbooks
keywords = {'keyword1', 'keyword2'}
results = search_textbooks(keywords, 5)
for r in results:
    title = r.get('section_title', r.get('title', ''))
    grade = r.get('grade', '?')
    text = r.get('text', '')[:200]
    print(f'Grade {grade} | {title}')
    print(f'  {text}')
    print()
"
```

### 6. Search style guide for calques/Russianisms (Антоненко-Давидович, 279 entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_style_guide
results = search_style_guide('TOPIC_HERE', 3)
for r in results:
    print(f'--- {r.get(\"word\", \"\")} [{r.get(\"section\", \"\")}]')
    print(r.get('text', '')[:300])
    print()
if not results:
    print('No style guide entries found')
"
```

### 7. Look up word definition in СУМ-11 (Ukrainian explanatory dictionary, 127K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_definitions
results = search_definitions('WORD_HERE', 3)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

### 8. Search idioms (Фразеологічний словник, 25K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import search_idioms
results = search_idioms('WORD_HERE', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"text\", r.get(\"definition\", \"\")))[:200]}')
"
```

### 9. English-to-Ukrainian translation (Балла, 79K entries)

```bash
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from wiki.sources_db import translate_en_uk
results = translate_en_uk('ENGLISH_WORD', 5)
for r in results:
    print(f'{r.get(\"word\", \"\")}: {str(r.get(\"definition\", r.get(\"text\", \"\")))[:200]}')
"
```

---

**WHEN to use these tools:**

1. **Before writing any Ukrainian text** — batch-verify all key vocabulary with
   `verify_words` (tool 1). Any word that returns NOT FOUND must be replaced.
2. **When you suspect a Russicism or calque** — search the style guide (tool 6)
   and verify the correct Ukrainian form with `verify_word` (tool 2).
3. **When writing for A1/A2** — check CEFR levels (tool 4) to ensure vocabulary
   is level-appropriate.
4. **When unsure about a case ending or conjugation** — use `verify_lemma` (tool 3)
   to see the full paradigm.
5. **When covering a grammar topic** — search textbooks (tool 5) to see how
   Ukrainian school textbooks teach it.
6. **When you need the precise Ukrainian meaning** — use СУМ-11 (tool 7).
7. **When looking for natural Ukrainian expressions** — search idioms (tool 8).

**Batching rule:** Collect all words you want to verify, then run ONE `verify_words`
call instead of multiple `verify_word` calls. This is faster and uses fewer tokens.

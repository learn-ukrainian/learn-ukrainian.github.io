# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 42: Hey, Friend! (A1, A1.7 [Communication])
**Writer:** Gemini Pro
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

Have you ever noticed how people's names seem to magically change when you travel to Ukraine? You might meet a man introduced as **Тарас** (Taras), but when his friends call out to him across the street, they shout **Тарасе!** (Tarase!). You might read about a woman named **Олена** (Olena), but her text messages from friends begin with **Олено!** (Oleno!). 

This is not a mistake or a series of complex nicknames. It is a fundamental grammatical rule of Ukrainian communication. Let us look at a typical conversation when two friends meet.

<div class="dialogue">


**Олена:** Привіт! Як справи? *(Hi! How are you?)*


**Тарас:** Добре, дякую, Олено! А в тебе? *(Good, thanks, Olena! And you?)*


**Олена:** Теж добре. Тарасе, ти знаєш мого брата? *(Also good. Taras, do you know my brother?)*


**Тарас:** Ні. *(No.)*


**Олена:** Андрію, ходи сюди! Це Тарас. *(Andriy, come here! This is Taras.)*


**Тарас:** Привіт, Андрію! *(Hi, Andriy!)*


**Андрій:** Привіт! *(Hi!)*


</div>


Let us discuss this interaction. This is a very typical scene when friends meet. They use casual greetings like **Привіт** (Hi). Notice how they constantly use each other's names. In Ukrainian culture, addressing a friend by name is a sign of warmth and closeness. But they do not use the names exactly as you might see them on a passport or an ID card. 

When we talk about these people, their names are **Олена** (Olena), **Тарас** (Taras), and **Андрій** (Andriy). But when we talk directly to them, their names transform into **Олено** (Oleno), **Тарасе** (Tarase), and **Андрію** (Andriyu). This transformation is the secret to sounding truly natural in Ukrainian.

:::fill-in
title: "Знайди місце (Complete the dialogue)"
---
- sentence: "— ___, привіт! Як справи?"
  answer: "Олено"
- sentence: "— Добре, дякую, ___!"
  answer: "Тарасе"
- sentence: "— ___, ходи сюди!"
  answer: "Андрію"
:::

Now, let us look at another scenario. This time, we are at home with a family, getting ready to leave the house.

<div class="dialogue">


**Син:** Мамо, де мій телефон? *(Mom, where is my phone?)*


**Мама:** На столі, синку. *(On the table, son.)*


**Донька:** Тату, а де ключі? *(Dad, and where are the keys?)*


**Тато:** У кишені, дочко. *(In the pocket, daughter.)*


**Син:** Бабусю, ми йдемо! *(Grandma, we are going!)*


**Бабуся:** Добре, будьте обережні! *(Good, be careful!)*


</div>


Here, we see the exact same grammatical principle applied to family relationships. The transformation happens with everyday family members just as it does with names. We say **мама** (mom) when talking about her, but we call out **мамо** (mom!) when asking her a question. We say **тато** (dad), but we call out **тату** (dad!). 

We also see some very warm, affectionate terms used by parents and grandparents. A parent might call their son **синку** (son!), which is the affectionate vocative form of **синок** (sonny). The base word is **син** (son), but Ukrainians use the diminutive **синок** in address — and its vocative is **синку**. A parent might call their daughter **дочко** (daughter!), derived from the word **дочка** (daughter). And a grandmother, **бабуся** (grandma), is lovingly addressed as **бабусю** (grandma!). 

By using these forms, you immediately sound more natural and engaged in the conversation. You are no longer just an observer; you are an active participant.

:::fill-in
title: "Знайди місце (Complete the dialogue)"
---
- sentence: "— ___, де мій телефон?"
  answer: "Мамо"
- sentence: "— На столі, ___."
  answer: "синку"
- sentence: "— ___, ми йдемо!"
  answer: "Бабусю"
:::

## Кличний відмінок (The Vocative Case)

Ukrainian has a special grammatical case purely for calling someone or addressing them directly. This is called **кличний відмінок** (the vocative case). 

When you address someone in English, you simply use their name: "Olena, come here!" or "Taras, look at this." In Ukrainian, the name actually changes its ending. You cannot simply use the base name to call someone. The transformation from **Олена** to **Олено** is mandatory. This is not an optional stylistic choice or a slang expression. Ukrainians always use the vocative case when addressing someone directly. It is a core rule of how the language works.

:::tip
In the 4th grade, Ukrainian schoolchildren learn a specific helper word to remember this case. The helper word is **Кл. (!)** (an abbreviation for *vocative*). The exclamation mark serves as a strong, permanent visual reminder: you are calling someone, getting their attention, and therefore, the ending of the word must change. Whenever you want to speak *to* someone, imagine that exclamation mark appearing next to their name.
:::

Let us look at why the vocative case matters so much. Let us compare two simple sentences to see the difference.

*   **Олена прийшла.** *(Olena came.)*
*   **Олено, ходи сюди!** *(Olena, come here!)*

In the first sentence, we use the nominative case. We are talking about Olena. She is the subject of the action. She is the one who came. We are simply stating a fact about her, describing an event that happened. 

In the second sentence, we use the vocative case. We are talking directly to Olena. We want her attention. We are giving her an instruction. 

Using the nominative case to address someone sounds extremely unnatural in Ukrainian. To a native speaker's ear, it sounds as strange and jarring as saying "Hey, him!" instead of "Hey, you!" in English. It feels broken and slightly rude. The vocative case is the polite, natural, and grammatically correct way to establish a connection with another person. It shows that you recognize them as the recipient of your words.

You will hear this everywhere. Imagine walking through a bustling market in Kyiv or Lviv. You will constantly hear the vocative case around you. Vendors calling out to customers, and friends trying to find each other in the crowd.

*   **Пане, дайте яблука!** *(Sir, give [me] apples!)*
*   **Пані, де молоко?** *(Ma'am, where is the milk?)*
*   **Друже, ходи сюди!** *(Friend, come here!)*

Every time a conversation is initiated, the vocative case is the spark that starts it. It is a beautiful feature of the language that brings people closer together. We use **пан** (Mr. / sir) and **пані** (Mrs. / Ms.) to be polite with strangers, and **друг** (friend) with people we know well. Notice that **пані** is a special word that never changes its ending, but the others do.

:::quiz
title: "Обери правильне слово (Choose the right word)"
---
- q: "___, привіт!"
  o: ["Олено", "Олена", "Оленю"]
  a: 0
- q: "Як справи, ___?"
  o: ["Тарасе", "Тарас", "Тарасу"]
  a: 0
- q: "Дякую, ___!"
  o: ["мамо", "мама", "маме"]
  a: 0
- q: "Ходи сюди, ___!"
  o: ["Іване", "Іван", "Івану"]
  a: 0
- q: "Будь обережний, ___!"
  o: ["синку", "синок", "синке"]
  a: 0
- q: "Що ти робиш, ___?"
  o: ["брате", "брат", "брату"]
  a: 0
- q: "Добрий день, ___!"
  o: ["пане", "пан", "пану"]
  a: 0
- q: "Привіт, ___!"
  o: ["Андрію", "Андрій", "Андріє"]
  a: 0
:::

## Закінчення кличного (Vocative Endings)

Now that we know why we use the vocative case, let us explore how to form it. The rules depend on the gender of the noun and the final sound of the word. While there are a few exceptions, the patterns are highly predictable and logical.

### Feminine Names and Nouns

For feminine names and nouns, the most common transformation is from the ending **-а** to the ending **-о**. This is very consistent and easy to remember. Most traditional Ukrainian female names follow this exact pattern.

*   **Олена** → **Олено** *(Olena)*
*   **мама** → **мамо** *(mom)*
*   **сестра** → **сестро** *(sister)*
*   **Оксана** → **Оксано** *(Oksana)*
*   **подруга** → **подруго** *(female friend)*

This rule also applies to names that end in **-ка**. These are often diminutive or casual forms of names, but they still follow the strict grammar rule. Longer feminine names ending in **-а** also follow this pattern perfectly.

*   **Наталка** → **Наталко** *(Natalka)*
*   **Ірка** → **Ірко** *(Irka)*
*   **Катерина** → **Катерино** *(Kateryna)*
*   **Тетяна** → **Тетяно** *(Tetiana)*

However, not all feminine names end in **-а**. If a feminine name ends in **-ія**, the ending changes to **-іє**. Be very careful not to use "-іо" — that is a common mistake for beginners trying to guess the rule!

*   **Марія** → **Маріє** *(Mariia)*
*   **Юлія** → **Юліє** *(Yuliia)*
*   **Вікторія** → **Вікторіє** *(Viktoriia)*

If a feminine noun ends in **-ся**, the ending changes to **-сю**. This makes the word sound soft and affectionate, which is perfect for family members.

*   **бабуся** → **бабусю** *(grandma)*
*   **Маруся** → **Марусю** *(Marusia)*

### Masculine Names and Nouns

For masculine names and nouns, the rules depend on whether the word ends in a hard consonant, a soft consonant, or the letter **-й**.

If the masculine word ends in a hard consonant, we simply add the ending **-е**. This is the standard rule for most masculine names and titles. Here we see **Іван** (Ivan) and **брат** (brother) following the rule.

*   **Тарас** → **Тарасе** *(Taras)*
*   **Іван** → **Іване** *(Ivan)*
*   **брат** → **брате** *(brother)*
*   **пан** → **пане** *(Mr. / sir)*

If the masculine word ends in a soft consonant (like **-ль**, **-сь**) or the letter **-й**, we replace the soft sign (**-ь**) or the letter **-й** with the ending **-ю**. The letter **-й** is always treated as a soft sound in Ukrainian. This makes the pronunciation smooth.

*   **Андрій** → **Андрію** *(Andriy)*
*   **дідусь** → **дідусю** *(grandpa)*
*   **вчитель** → **вчителю** *(teacher)*
*   **Олексій** → **Олексію** *(Oleksiy)*

There are also a few special consonant alternations you must memorize. Sometimes, the final consonant of the root changes before taking the **-е** ending. This happens to make the word easier and more natural to pronounce rapidly. 

When a masculine word ends in the letter **-г**, the **г** changes to **ж**.

*   **друг** → **друже** *(friend)*

When a masculine word ends in the letter **-к**, the **к** changes to **ч**. The word **козак** (Cossack) is historically very important in Ukrainian culture. Even today, you might hear someone affectionately called a Cossack if they are brave or strong. The transformation sounds very traditional and proud.

*   **козак** → **козаче** *(Cossack)*

Finally, there is one very important exception to memorize. The word **тато** (dad) is masculine, even though it ends in **-о** (which is unusual for masculine nouns). In the vocative case, it takes a special **-у** ending: **тато** → **тату**. This is a historic exception — simply memorize it.

*   **тато** → **тату** *(dad)*

:::group-sort
title: "Розподіли (Sort vocative endings)"
---
groups:
  - name: "-о (feminine)"
    items: ["Олено", "мамо", "сестро"]
  - name: "-е (masculine hard)"
    items: ["Тарасе", "Іване", "брате", "пане"]
  - name: "-ю (masculine soft)"
    items: ["Андрію", "дідусю", "вчителю"]
:::

## Підсумок — Summary

You now know how to correctly call people by their names and family titles. The **кличний відмінок** (vocative case) is the key to sounding polite, respectful, and completely natural in Ukrainian. 

Remember the helper word **Кл. (!)** — whenever you address someone directly, you must change the ending of their name to match the grammatical rule. If you forget to use the vocative case, people will still understand you, but your Ukrainian will sound slightly awkward and foreign. Mastering this small change makes a massive difference in how native speakers perceive your language skills.

Here is a quick reference table for the vocative patterns we learned in this module. You can use this table to check your endings when you write messages to your Ukrainian friends.

| Pattern | Nominative → Vocative | Example |
| :--- | :--- | :--- |
| Feminine **-а** | **-а** → **-о** | **Олена** → **Олено**, **мама** → **мамо** |
| Feminine **-ія** | **-ія** → **-іє** | **Марія** → **Маріє** |
| Feminine **-ся** | **-ся** → **-сю** | **бабуся** → **бабусю** |
| Masculine hard | + **-е** | **Тарас** → **Тарасе**, **брат** → **брате** |
| Masculine **-й** / soft | + **-ю** | **Андрій** → **Андрію**, **вчитель** → **вчителю** |
| Special (**г**, **к**) | **г**→**ж**, **к**→**ч** + **-е** | **друг** → **друже** |

Self-check: How do you call your family? Try to remember the rules without looking at the table.

*   **мама** → **мамо**
*   **тато** → **тату**
*   **брат** → **брате**
*   **сестра** → **сестро**
*   **бабуся** → **бабусю**
*   **дідусь** → **дідусю**

You are now fully ready to greet your Ukrainian friends with confidence and respect! Go ahead and start using these forms in your daily practice.

:::fill-in
title: "Утвори пару (Write vocative)"
---
- sentence: "Олена → ___"
  answer: "Олено"
- sentence: "Тарас → ___"
  answer: "Тарасе"
- sentence: "мама → ___"
  answer: "мамо"
- sentence: "Іван → ___"
  answer: "Іване"
- sentence: "сестра → ___"
  answer: "сестро"
- sentence: "Андрій → ___"
  answer: "Андрію"
- sentence: "подруга → ___"
  answer: "подруго"
- sentence: "брат → ___"
  answer: "брате"
- sentence: "Марія → ___"
  answer: "Маріє"
- sentence: "бабуся → ___"
  answer: "бабусю"
:::

**Deterministic word count: 1777 words** (calculated by pipeline, do NOT estimate manually)

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

Verified: 91 words | Not found: 31 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іван — NOT IN VESUM
  ✗ Іване — NOT IN VESUM
  ✗ Івану — NOT IN VESUM
  ✗ Ірка — NOT IN VESUM
  ✗ Ірко — NOT IN VESUM
  ✗ Андрій — NOT IN VESUM
  ✗ Андрію — NOT IN VESUM
  ✗ Андріє — NOT IN VESUM
  ✗ Катерина — NOT IN VESUM
  ✗ Катерино — NOT IN VESUM
  ✗ Марусю — NOT IN VESUM
  ✗ Маруся — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Маріє — NOT IN VESUM
  ✗ Наталка — NOT IN VESUM
  ✗ Наталко — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Оксано — NOT IN VESUM
  ✗ Олексій — NOT IN VESUM
  ✗ Олексію — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олено — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тарасе — NOT IN VESUM
  ✗ Тарасу — NOT IN VESUM
  ✗ Тетяна — NOT IN VESUM
  ✗ Тетяно — NOT IN VESUM
  ✗ Юлія — NOT IN VESUM
  ✗ Юліє — NOT IN VESUM
  ✗ маме — NOT IN VESUM
  ✗ синке — NOT IN VESUM

All 91 other words are confirmed to exist in VESUM.

</vesum_verification>
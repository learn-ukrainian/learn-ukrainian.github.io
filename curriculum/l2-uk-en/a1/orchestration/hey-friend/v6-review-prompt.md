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
## Діало́ги (Dialogues)

Imagine you are at a lively birthday party in Ukraine. The traditional music is playing loudly, people are talking in groups, and you need to get your friend's attention across the crowded room. In English, you would simply shout their name exactly as it is written. In Ukrainian, calling out to someone or addressing them directly requires a specific grammatical shift. You cannot just use their regular, dictionary-form name; you must change its ending to show that you are talking to them, rather than about them. 

Let us look at a typical interaction as guests arrive at the party. The birthday person is greeting friends as they walk through the door. Notice how the names change when they speak directly to each other. Pay special attention to how **Оле́на** (Olena), **Тара́с** (Taras), and **Андрі́й** (Andriy) are addressed.

> **Імени́нник:** **Оле́но, приві́т! Як спра́ви?** *(Olena, hi! How are you?)*
> **Олена:** **До́бре, дякую, Тара́се! А в тебе́?** *(Good, thanks, Taras! And you?)*
> **Іменинник:** **Теж добре. Олено, ти зна́єш мого бра́та?** *(Also good. Olena, do you know my brother?)*
> **Олена:** **Ні.** *(No.)*
> **Іменинник:** **Андрію, хо́ди сюди́! Це Олена.** *(Andriy, come here! This is Olena.)*
> **Іменинник:** **Олено, це Андрій.** *(Olena, this is Andriy.)*

Later at the same party, the birthday person interacts with different family members in the kitchen. Family words also change their endings when you address them directly. Pay attention to how the words for mom, dad, son, daughter, and grandma transform in conversation when someone is asking a question or giving an instruction.

> **Син:** **Ма́мо, де мій телефо́н?** *(Mom, where is my phone?)*
> **Ма́ма:** **На столі́, синку́.** *(On the table, son.)*
> **Дочка́:** **Тату́, а де ключі́?** *(Dad, and where are the keys?)*
> **Та́то:** **У кише́ні, до́чко.** *(In the pocket, daughter.)*
> **Син:** **Бабу́сю, ми йдемо́!** *(Grandma, we are going!)*
> **Бабу́ся:** **Добре, бу́дьте обере́жні!** *(Good, be careful!)*
> **Бабуся:** **До поба́чення, Андрію!** *(Goodbye, Andriy!)*

Did you notice the consistent pattern of direct address in those two dialogues? When the speaker talked about someone, they used the regular name, like saying **Це Олена** (This is Olena) or **Це Андрій** (This is Andriy). But when they spoke directly to them, **Олена** (Olena) became **Олено** (Olena), **Тарас** (Taras) became **Тарасе** (Taras), and **мама** (mom) became **мамо** (mom). This shift is not an optional stylistic choice; it is a fundamental rule of natural Ukrainian communication.

*   **До́брий ра́нок, па́не Іва́не!** *(Good morning, Mr. Ivan!)*
*   **Добрий ве́чір, па́ні Окса́но!** *(Good evening, Ms. Oksana!)*
*   **До побачення, вчи́телю!** *(Goodbye, teacher!)*
*   **На добра́ніч, синку!** *(Good night, son!)*
*   **Смачно́го, дру́зі!** *(Bon appetit, friends!)*

<!-- INJECT_ACTIVITY: dialogue-flow-practice -->

## Кли́чний відмі́нок (The Vocative Case)

Ukrainian grammar features seven cases, and one of them is used exclusively for calling, addressing, or getting someone's attention. This is called the **кличний відмінок** (Vocative Case). As you already know, Ukrainian relies on changing word endings to show grammatical relationships within a sentence. While the other six cases indicate who is doing an action or where an object is located, the vocative case serves a purely communicative function. In English you just say the name: "Olena, come here!". In Ukrainian the name CHANGES: **Олено, ходи сюди!** (Olena, come here!). When you address a person, you must alter their name or title to match this specific grammatical role. This is not optional — Ukrainians always use the vocative when addressing someone.

In Ukrainian elementary schools, fourth-grade students learn a simple but effective trick to remember when to use this form. Teachers introduce the vocative case with a Grade 4 helper word and punctuation mark: **Кл. (!)** (Voc. (!)). The exclamation mark acts as a visual reminder that you are "shouting," calling out, or directly addressing someone. This punctuation mark triggers the ending change. Whenever you use a person's name with an exclamation mark or a comma in direct speech, you must apply the vocative ending. This mental trigger ensures that the name correctly reflects the social interaction taking place.

:::note
The vocative case is entirely independent of the other cases. It does not answer any questions (like "who?" or "what?"), because its only job is to get someone's attention.
:::

Understanding the difference between talking about someone and talking to someone is critical for your fluency. The nominative case is the dictionary form, used when someone is the subject of a sentence. Why the vocative matters: **Олена прийшла́.** (Olena came.) is in the nominative, because you are talking ABOUT her. However, if you want to address her, you must use the vocative: **Олено, ходи сюди!** (Olena, come here!), because you are talking TO her. Using the nominative to address a person sounds incredibly unnatural to native speakers. It feels as awkward as saying "Hey, him!" instead of "Hey, you!" in English. Let us compare these two states:

**Називни́й відмінок** (Nominative):
*   **Це мій тато.** *(This is my dad.)*
*   **Тут працю́є вчи́тель.** *(A teacher works here.)*
*   **Там стої́ть Олена.** *(Olena is standing there.)*
*   **Мій брат чита́є.** *(My brother is reading.)*

**Кличний відмінок** (Vocative):
*   **Тату, я тебе ба́чу!** *(Dad, I see you!)*
*   **Вчителю, добрий ранок!** *(Teacher, good morning!)*
*   **Олено, йди туди́!** *(Olena, go there!)*
*   **Бра́те, що ти чита́єш?** *(Brother, what are you reading?)*

The vocative case is much more than just a grammatical rule; it is a living marker of Ukrainian linguistic identity. While this grammatical feature has mostly disappeared from standard Russian, surviving only in a few archaic religious terms, it remains vibrant and absolutely necessary in everyday Ukrainian conversation. By using the vocative case correctly, you are not just following a textbook rule. You are actively speaking authentic, decolonized Ukrainian and showing deep respect for the natural structure and historical continuity of the language. When you use the vocative case, native speakers instantly recognize that you are making a genuine effort to understand the rhythm of their language, rather than just translating English words directly into Ukrainian.

## Закі́нчення кли́чного (Vocative Endings)

Let us break down the specific rules for forming the vocative case, starting with feminine names and nouns that end in the letter **-а**. This is the most common feminine pattern you will encounter. To create the vocative form, you simply replace the final **-а** with the letter **-о**. 

*   **Олена** → **Олено** (Olena)
*   **мама** → **мамо** (mom)
*   **сестра́** → **се́стро** (sister)
*   **Окса́на** → **Оксано** (Oksana)
*   **по́друга** → **по́друго** (friend, f)

This rule also applies to informal or diminutive names ending in **-ка**, such as **Ната́лка** → **Ната́лко** (Natalka) and **Ірка** → **Ірко** (Irka). Furthermore, longer names ending in **-а** follow this exactly: **Катери́на** → **Катери́но** (Kateryna), **Тетя́на** → **Тетя́но** (Tetiana). Note that the polite title **пані** (Mrs. / Ms.) is an exception and does not change its form when used to address someone.

*   **Олено, де мій зо́шит?** *(Olena, where is my notebook?)*
*   **Мамо, я хо́чу ї́сти.** *(Mom, I want to eat.)*
*   **Сестро, ти йдеш у кіно́?** *(Sister, are you going to the cinema?)*
*   **Подруго, це твоя́ кни́га?** *(Friend, is this your book?)*
*   **Катерино, добрий день!** *(Kateryna, good day!)*

Feminine names that end in **-і́я** or the soft letter **-я** follow a slightly different but closely related pattern. If a name ends in **-ія**, the ending shifts to **-і́є**. For example, **Марі́я** (Mariia) becomes **Марі́є** (Mariia — vocative, never "Маріо!"). If a feminine word or name ends in a soft **-ся** or is a diminutive form ending in **-я**, the ending changes to **-ю**. 

*   **Марія** → **Маріє** (Mariia)
*   **Ю́лія** → **Ю́ліє** (Yuliia)
*   **бабуся** → **бабусю** (grandma)
*   **Га́ля** → **Галю** (Halia)
*   **Ната́ля** → **Ната́лю** (Natalia)

Notice how the soft quality of the final consonant is preserved by using the soft vowel **-ю** or **-є**. 

*   **Маріє, як справи?** *(Mariia, how are things?)*
*   **Юліє, ходи сюди!** *(Yuliia, come here!)*
*   **Бабусю, ти ду́же до́бра.** *(Grandma, you are very kind.)*
*   **Наталю, де ти живе́ш?** *(Natalia, where do you live?)*

:::caution
Do not confuse the feminine ending **-ю** (like in **бабусю**) with the masculine soft ending **-ю** (like in **Андрію**). While they look identical, they come from different spelling patterns.
:::

Now let us look at masculine names and nouns. Most standard masculine words end in a hard consonant. To form the vocative for these words, you do not replace anything; you simply add the letter **-е** directly to the end of the hard consonant. This makes the word slightly longer and easier to call out across a room.

*   **Тарас** → **Тарасе** (Taras)
*   **Іва́н** → **Іване** (Ivan)
*   **брат** → **брате** (brother)
*   **пан** → **пане** (Mr. / sir)
*   **Богдан** → **Богдане** (Bohdan)

Whenever you use the formal title **пан**, it must also take this ending, as in **Добрий день, пане!** (Good day, sir!).

*   **Тарасе, що ти ро́биш?** *(Taras, what are you doing?)*
*   **Іване, це твій телефон?** *(Ivan, is this your phone?)*
*   **Брате, йди сюди!** *(Brother, come here!)*
*   **Пане, де тут апте́ка?** *(Sir, where is the pharmacy here?)*
*   **Богдане, ти студе́нт?** *(Bohdan, are you a student?)*

If a masculine word ends in a soft consonant or the letter **-й**, the added vowel changes to match the softness. Instead of adding **-е**, you must add the letter **-ю** to the end of the word. This maintains the softness of the final sound and creates a smooth, natural flow when speaking.

*   **Андрій** → **Андрію** (Andriy)
*   **Сергі́й** → **Сергі́ю** (Serhiy)
*   **діду́сь** → **діду́сю** (grandpa)
*   **вчитель** → **вчителю** (teacher, m)

Replacing the **-й** with **-ю** is one of the most frequent transformations you will make when addressing Ukrainian men.

*   **Андрію, ти ма́єш брата?** *(Andriy, do you have a brother?)*
*   **Сергію, це твоя маши́на?** *(Serhiy, is this your car?)*
*   **Дідусю, чита́й ка́зку!** *(Grandpa, read a fairy tale!)*
*   **Вчителю, я маю пита́ння.** *(Teacher, I have a question.)*

There are a few special cases and consonant alternations that you should memorize because they occur in very common words. The word for dad takes an exceptional **-у** ending: **тато** → **тату** (dad). You must memorize this. The word for son also takes an **-у** ending: **син** → **си́ну** (son). The affectionate form is **сино́к** → **синку**. Additionally, some masculine consonants change their sound entirely to make pronunciation easier. For example, the consonant **г** changes to **ж** in **друг** → **дру́же** (friend, m), and the consonant **к** changes to **ч** in **коза́к** → **коза́че** (Cossack).

*   **Тату, я йду додо́му.** *(Dad, I am going home.)*
*   **Синку, будь обере́жний!** *(Son, be careful!)*
*   **Друже, ти маєш ра́цію.** *(Friend, you are right.)*
*   **Козаче, куди́ ти йдеш?** *(Cossack, where are you going?)*

<!-- INJECT_ACTIVITY: vocative-form-practice -->
<!-- INJECT_ACTIVITY: vocative-choice-quiz -->
<!-- INJECT_ACTIVITY: ending-sorting-activity -->

## Підсумок — Summary

Mastering the vocative case is a crucial step in sounding like a natural, fluent Ukrainian speaker. Remember that you must always change the ending of a name or title when you are addressing someone directly. The core patterns are very consistent across the language: feminine words ending in **-а** shift to **-о**, masculine words ending in hard consonants add **-е**, and masculine words ending in soft consonants or **-й** add **-ю**. By applying these simple vowel shifts, you ensure that your greetings, questions, and daily interactions flow smoothly and respect the traditional rules of Ukrainian communication. You will quickly find that these vowel shifts become automatic as your brain learns to associate the act of calling someone with adding these specific soft or hard sounds.

Keep this vocative quick reference guide handy as you practice forming the vocative case. It covers the most frequent patterns you will encounter in everyday conversation.

| Pattern | Nominative → Vocative | Example |
| :--- | :--- | :--- |
| Feminine **-а** | **-а** → **-о** | **Олена** → **Олено**, **мама** → **мамо** |
| Feminine **-ія** | **-ія** → **-іє** | **Марія** → **Маріє** |
| Feminine **-ся** | **-ся** → **-сю** | **бабуся** → **бабусю** |
| Masculine hard | + **-е** | **Тарас** → **Тарасе**, **брат** → **брате** |
| Masculine **-й** / soft | + **-ю** | **Андрій** → **Андрію**, **вчитель** → **вчителю** |
| Special (**г**, **к**) | **г**→**ж**, **к**→**ч** + **-е** | **друг** → **друже** |
| Special (**-у**) | irregular | **тато** → **тату**, **син** → **сину** |

:::tip
Whenever you say **Привіт!** (Hi!), **Добрий день!** (Good day!), or ask **Як справи?** (How are you?), immediately follow it with the vocative form of the person's name or title!
:::

Before moving on to the next module, take a moment to self-check your understanding of these rules. How do you call your family? **мама** (mom) → ? **тато** (dad) → ? **брат** (brother) → ? How do you correctly greet your friend Taras? Most importantly, do you clearly feel the functional difference between the sentence **Марія прийшла** (Mariia came) and the direct command **Маріє, ходи сюди!** (Mariia, come here!)? If you can confidently answer these questions and apply the correct endings,
</generated_module_content>

**PIPELINE NOTE — Word count: 2076 words** (calculated deterministically by the pipeline, NOT by the writer. This number is CORRECT. Do NOT estimate your own word count — use this number for the Structural integrity dimension.)

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

Verified: 98 words | Not found: 71 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Іва — NOT IN VESUM
  ✗ Іване — NOT IN VESUM
  ✗ Ірка — NOT IN VESUM
  ✗ Ірко — NOT IN VESUM
  ✗ Андрі — NOT IN VESUM
  ✗ Андрій — NOT IN VESUM
  ✗ Андрію — NOT IN VESUM
  ✗ Богдан — NOT IN VESUM
  ✗ Богдане — NOT IN VESUM
  ✗ Галю — NOT IN VESUM
  ✗ Діало — NOT IN VESUM
  ✗ Закі — NOT IN VESUM
  ✗ Катерино — NOT IN VESUM
  ✗ Кли — NOT IN VESUM
  ✗ Маріо — NOT IN VESUM
  ✗ Марія — NOT IN VESUM
  ✗ Маріє — NOT IN VESUM
  ✗ Називни — NOT IN VESUM
  ✗ Ната — NOT IN VESUM
  ✗ Наталю — NOT IN VESUM
  ✗ Окса — NOT IN VESUM
  ✗ Оксано — NOT IN VESUM
  ✗ Оле — NOT IN VESUM
  ✗ Олена — NOT IN VESUM
  ✗ Олено — NOT IN VESUM
  ✗ Сергі — NOT IN VESUM
  ✗ Сергію — NOT IN VESUM
  ✗ Тарас — NOT IN VESUM
  ✗ Тарасе — NOT IN VESUM
  ✗ Тетя — NOT IN VESUM
  ✗ Юліє — NOT IN VESUM
  ✗ апте — NOT IN VESUM
  ✗ биш — NOT IN VESUM
  ✗ відмі — NOT IN VESUM
  ✗ додо — NOT IN VESUM
  ✗ дру — NOT IN VESUM
  ✗ друго — NOT IN VESUM
  ✗ дьте — NOT IN VESUM
  ✗ жний — NOT IN VESUM
  ✗ жні — NOT IN VESUM
  ✗ зку — NOT IN VESUM
  ✗ кише — NOT IN VESUM
  ✗ кли — NOT IN VESUM
  ✗ кни — NOT IN VESUM
  ✗ лка — NOT IN VESUM
  ✗ лко — NOT IN VESUM
  ✗ лія — NOT IN VESUM
  ✗ ліє — NOT IN VESUM
  ✗ маши — NOT IN VESUM
  ✗ нник — NOT IN VESUM

All 98 other words are confirmed to exist in VESUM.

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

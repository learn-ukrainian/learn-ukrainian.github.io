        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
          📊 Section Word Analysis:
     Вступ та культурний контекст (Introduction & Cultural Context)                     175 /  200  ⚠️ (-25)
     Кольори та узгодження (Colors & Grammar of Agreement)                              415 /  300  ✅ (+115)
     Лексика одягу (Clothing Vocabulary)                                                254 /  300  ⚠️ (-46)
     Практика: Дієслово «носити» та покупки (Practice: The Verb 'To Wear' & Shopping)   295 /  250  ✅ (+45)
     Підсумок (Summary)                                                                 184 /  150  ✅ (+34)
     ─────────────────────────────────────────────────────────────────────────────────────────────────────────
     TOTAL                                                                             1323 / 1200  ✅ (+123)
  📋 Found YAML activities file (8 activities)
  > Match the Colors: 8 items (min 8)
  > Match the Clothing: 8 items (min 8)
  > Choose the Correct Form: 8 items (min 8)
  > Complete with the Correct Color Ending: 8 items (min 8)
  > Sort the Words: 14 items (min 6)
  > True or False: 8 items (min 8)
  > Using the Verb To Wear: 8 items (min 8)
  > Shopping for Clothes: 8 items (min 8)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 1283/1200 (raw: 1442)
Activities   ✅ 8/8
Density      ✅ All > 6
Unique_types ✅ 5/4 types
Priority     ✅ Priority types used
Engagement   ✅ 3/3
Audio        ℹ️ No audio
Vocab        ✅ 23/1
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ✅ Level-appropriate
Content_heavy ℹ️ N/A (standard module)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ℹ️ Quality validation N/A (A1/A2)
Research     ✅ Content aligned with research
Immersion    🇺🇦 35.6% (target 25-40% (M12))

Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/colors-and-clothing-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/colors-and-clothing.json

✅ AUDIT PASSED.

✅ AUDIT PASSED

Running RAG word verification...
Verifying: colors-and-clothing.md
  VESUM misses: 3 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 20337.66it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 188 | VESUM: 185 (98.4%) | RAG: 3 | Not found: 0
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/colors-and-clothing-rag-audit.md
✅ RAG verification: all words verified

VESUM: 185/188 (98%) verified
⚠️ VESUM not found (3): ий, ю, ій
        ```

        ## Current Content of Affected Section(s)


Це нова тема.
The topic is new.

Це мій новий одяг.
My new clothing is here.

Ось одяг.
Here is the clothing.

Що це?
What is this?

Це мій одяг.
My clothing is here.

| Word | Meaning |
|------|---------|
| **соро́чка** | shirt |
| **све́тр** | sweater |
| **ку́ртка** | jacket |
| **су́кня** | dress (elegant) |
| **пла́ття** | dress (casual) |

> [!culture]
> Слово «су́кня» — це елегантний одяг. Слово «пла́ття» — це щоденний одяг.
> The word "су́кня" is elegant clothing. The word "пла́ття" is everyday clothing.

Це нові фрази.
These are new phrases.

Ось мій нови́й си́ній све́тр.
Here is my new blue sweater.

Ось гарна черво́на су́кня.
Here is a beautiful red dress.

Там те́пла ку́ртка.
There is a warm jacket.

Ось магазин.
Here is a store.

Це гарний одяг.
This clothing is beautiful.

Тепер поговоримо про спеціальну групу слів.
Now let's talk about a special group of words.

Це спеціальні слова.
These are special words.

Ці слова — завжди множина.
These words are always plural.

| Word | Meaning |
|------|---------|
| **штани́** | pants |
| **джи́нси** | jeans |
| **окуля́ри** | glasses |

Because these words are always plural, any adjective describing them must also be in the plural form.

Це мої нові́ джи́нси.
These are my new jeans.

Ось мої чо́рні окуля́ри.
Here are my black glasses.

Там одні́ си́ні штани́.
There is one pair of beautiful blue pants.

## Практика: Дієслово «носити» та покупки (Practice: The Verb 'To Wear' & Shopping)

Now we thoroughly know the undeniably correct names of clothes and the vibrant descriptive colors.

Дієслово «носити».
The verb 'to wear'.

Я часто ношу́ бі́лу соро́чку.
I often wear a white shirt.

Подивімося на правило.
Let us look at the rule.

Дієслово «носити» змінює жіночий рід.
The verb 'to wear' changes feminine gender.

Закінчення «-а» змінюється на «-у».
The ending '-a' changes to '-у'.

Закінчення «-я» змінюється на «-ю».
The ending '-я' changes to '-ю'.

Слово також змінює закінчення!
The adjective also changes its ending!

Я ношу́ черво́ну су́кню.
I wear a red dress.

Ви бачите, як два слова змінюються?
Do you see how two words change?

Це не «черво́на су́кня».
It is not 'черво́на су́кня'.

Це «черво́ну су́кню».
It is 'черво́ну су́кню'.

Я ношу́ си́ні джи́нси.
I wear blue jeans.
(Слова у множині не змінюють закінчення — це дуже легко! Plural words do not change their endings — it is very easy!)

Практикуймо!
Let's practice.

Ось короткий діалог.
Here is a short dialogue.

Ви зараз у магазині одягу.
Imagine you are in a store.

Ми в магазині одягу.
We are in a clothing store.

— Добрий день. Де бі́ла соро́чка?
— Good afternoon. Where is the white shirt?
— Ось бі́ла соро́чка. Це ваш розмір.
— Here is the white shirt. Your size is right here.
— Так, це мій розмір. Це гарний колір.
— Yes, it fits. The color is beautiful.
— Це чудова бі́ла соро́чка.
— The white shirt is wonderful.

When shopping for clothes, you can use these helpful phrases to express what you like or if something fits well.

Ці штани́ гарні.
These pants are beautiful.

Ця чо́рна ку́ртка дуже гарна.
This black jacket is very beautiful.

## Підсумок (Summary)

Ось нові слова.
Here are the new words.

Кольори і граматика.
Colors and grammar.

Ось мій одяг.
Look at my clothing.

Я ношу чорні штани.
I wear black pants.

Я ношу білу сорочку.
I wear a white shirt.

Ось гарна червона сукня.
Here is a beautiful red dress.

Там мій новий синій светр.
There is my new blue sweater.

Чоловічий рід: закінчення -ий (чорний светр).
Masculine adjectives end in -ий.

Жіночий рід: закінчення -а (чорна сорочка).
Feminine adjectives end in -а.

Середній рід: закінчення -е (чорне плаття).
Neuter adjectives end in -е.

Ці слова — завжди множина (штани́, окуля́ри).
These words are always plural.

Дієслово «носити» змінює закінчення.
The verb 'to wear' changes endings.

Я ношу́ бі́лу ку́ртку.
I wear a white jacket.

Ось мій розмір.
Here is my size.

Це дуже важливо.
It is very important.

Тест.
Quiz.

Take a moment to answer these review questions:
1. How do you say «red dress» in Ukrainian?
2. Translate the phrase «I wear a white shirt».
3. What is the grammatical gender of «све́тр»?
4. Which colors symbolize life and earth?

Практика важлива!
Practice is important!

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/colors-and-clothing.md`

        ## Instructions

        1. Fix ONLY the violations listed above
        2. For euphony (в/у, і/й): apply Ukrainian euphony rules strictly
        3. Do NOT add or remove content — only fix the specific violations
        4. Preserve all markdown formatting, headers, and structure

        ## Output Format (MANDATORY)

        Output ONLY the fixed section(s) between delimiters:

        ```
        ===SECTION_FIX_START===
        ## {section title}
        {fixed section content}
        ===SECTION_FIX_END===
        ```

        If multiple sections need fixing, output each in its own delimiter block.
        Do NOT output anything else — no explanations, no commentary.

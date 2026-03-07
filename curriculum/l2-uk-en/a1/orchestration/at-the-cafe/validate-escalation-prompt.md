        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
          > Cafe Vocabulary: 8 items (min 8)
  > Cafe Phrases: 8 items (min 8)
  > Cafe Etiquette and Vocabulary: 9 items (min 8)
  > Ordering Rules in a Cafe: 8 items (min 8)
  > Complete the Cafe Order: 8 items (min 8)
  > Customer and Waiter Conversation: 8 items (min 8)
  > Put the Words in Order: 8 items (min 6)
  > Drinks vs Other Items: 11 items (min 6)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 1494/1200 (raw: 1684)
Activities   ✅ 8/8
Density      ✅ All > 6
Unique_types ✅ 6/4 types
Priority     ✅ Priority types used
Engagement   ✅ 4/3
Audio        ℹ️ No audio
Vocab        ✅ 20/1
Structure    ✅ Valid Structure
Lint         ✅ Clean Format
Pedagogy     ❌ 1 violations
Content_heavy ℹ️ N/A (standard module)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ℹ️ Quality validation N/A (A1/A2)
Research     ✅ Content aligned with research
Immersion    🇺🇦 45.0% (target 35-55% (M41))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [HEADING_LEVEL] Main section 'Summary' uses H2 (##) but spec requires H1 (#)
     → FIX: Change '## Summary' to '# Summary' for top-level TOC compliance


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 1 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/at-the-cafe-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/at-the-cafe.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/a1/audit/at-the-cafe-audit.log for details)

Running RAG word verification...
Verifying: at-the-cafe.md
  VESUM misses: 6 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 18225.54it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 302 | VESUM: 296 (98.0%) | RAG: 4 | Not found: 2
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/at-the-cafe-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

VESUM: 296/302 (98%) verified
⚠️ VESUM not found (6): Відень, Львові, Львів, Марія, сіку, Юрія
        ```

        ## Current Content of Affected Section(s)

        ## Вступ (Introduction)

Українська кав'ярня — це особливе місце. Це не просто швидкий напій. Ви відпочиваєте. Ви говорите з друзями. Ви насолоджуєтеся атмосферою.
(A Ukrainian café is a special place. It is not just a quick drink. You rest. You talk with friends. You enjoy the atmosphere.)

У таких містах, як Львів, кава всюди. Традиція «піти на каву» (going for a coffee) — це важливий соціальний ритуал. Український друг запрошує вас на каву. Це гарна ідея провести час разом. Це справжній символ дружби.
(In cities like Lviv, coffee is everywhere. The tradition of "going for a coffee" is an important social ritual. A Ukrainian friend invites you for coffee. It is a good idea to spend time together. It is a true symbol of friendship.)

Є відома легенда про українця Юрія Кульчицького. Він врятував місто Відень. Потім він відкрив там кав'ярню. Сьогодні у Львові є пам'ятник на його честь.
(There is a famous legend about the Ukrainian Yuriy Kulchytsky. He saved the city of Vienna. Then he opened a coffeehouse there. Today in Lviv there is a monument in his honor.)

Before we start practicing how to order, let us learn the essential vocabulary words you will need at any café.

| Word | Meaning |
|------|---------|
| **ка́ва** | coffee |
| **чай** | tea |
| **вода́** | water |
| **меню́** | menu |
| **раху́нок** | bill |
| **офіціа́нт** | waiter |
| **замовля́ти** | to order |
| **будь ла́ска** | please |

> [!culture]
> Західна Україна дуже любить каву. Львів — це місто кави. В інших регіонах чай також популярний. Але кожне місто має затишну кав'ярню.
> (Western Ukraine loves coffee very much. Lviv is the city of coffee. In other regions, tea is also popular. But every city has a cozy coffee shop.)

## Презентація (Presentation)

Ви заходите в кафе. Офіціант вітає вас. Офіціанти використовують форму «Ви». Це повага.
(You enter a café. The waiter greets you. Waiters use the "You" form. This is respect.)

Офіціант питає:
- «До́брий день! Що бажа́єте?» (Good afternoon! What would you like?)
- «Що ви замо́вите?» (What will you order?)

Англійська мова має фразу "I want". Але українська фраза «Я хо́чу» звучить не дуже ввічливо.
(The English language has the phrase "I want". But the Ukrainian phrase "I want" sounds not very polite.)

Українці використовують інші фрази. Це фрази для замовлення:
(Ukrainians use other phrases. These are phrases for ordering:)

- «Я бу́ду...» (I will have...)
- «Ка́ву, будь ла́ска.» (Coffee, please.)

> [!warning]
> Фраза «Я хо́чу ка́ву» — це граматично правильно, але досить грубо. Важливо завжди говорити «Я бу́ду...».
> (The phrase "I want coffee" is grammatically correct, but quite rude. It is important to always say "I will have...".)

### Як замовляти напої (How to Order Drinks)

Ви замовляєте щось. Тоді слово змінює свою форму. Це називається Знахідний відмінок. Він працює для прямого об'єкта.
(You order something. Then the word changes its form. This is called the Accusative case. It works for the direct object.)

Слова жіночого роду:
Закінчення **-а** стає **-у**.
Закінчення **-я** стає **-ю**.
(The -a ending becomes -y. The -ya ending becomes -yu.)

### «вода́» → «во́ду»

Слово «вода́» має закінчення **-а**. Ми змінюємо літеру на **-у**.
(The word for water has an -a ending. We change the letter to -y.)

- «Я бу́ду во́ду.» (I will have water.)
- «Во́ду, будь ла́ска.» (Water, please.)

### «ка́ва» → «ка́ву»

Слово «ка́ва» має закінчення **-а**. Ми змінюємо літеру на **-у**.
(The word for coffee has an -a ending. We change the letter to -y.)

- «Я бу́ду ка́ву.» (I will have coffee.)
- «Ка́ву, будь ла́ска.» (Coffee, please.)

### «сік» → «сік»

Чоловічі слова не змінюють форму. Слово «сік» — це чоловічий рід. Воно не має закінчення **-а**. Це неживий предмет.
(Masculine words do not change form. The word for juice is masculine. It does not have an -a ending. It is an inanimate object.)

- «Я бу́ду сік.» (I will have juice.)
- «Сік, будь ла́ска.» (Juice, please.)

> [!tip]
> Слова «чай» і «сік» — чоловічого роду. Ви замовляєте ці напої. Форма слова не змінюється.
> (Words like tea and juice are masculine. You order these drinks. The form of the word does not change.)

### Деталі замовлення (Order Details)

Ви хочете додати інгредієнти до напою. Ось дві важливі фрази:
(You want to add ingredients to the drink. Here are two important phrases:)

- «з молоко́м» (with milk)
- «без цу́кру» (without sugar)

Ви додаєте ці фрази після напою:
(You add these phrases after the drink:)

- «Я бу́ду ка́ву з молоко́м.» (I will have coffee with milk.)
- «Чай без цу́кру, будь ла́ска.» (Tea without sugar, please.)
- «Я бу́ду ка́ву з молоко́м і без цу́кру.» (I will have coffee with milk and without sugar.)

## Практика (Practice)

Ви хочете попросити меню. Найкращий варіант — це фраза «чи можна».
(You want to ask for the menu. The best option is the phrase "chy mozhna" - may I / is it possible.)

- «Чи можна, будь ла́ска, меню́?» (May I have the menu, please?)
- «Чи можна, будь ла́ска, во́ду?» (May I have water, please?)

Фраза «чи можна» працює зі Знахідним відмінком. Форма «вода́» стає «во́ду».
(The phrase "chy mozhna" works with the Accusative case. The form "voda" becomes "vodu".)

### Просити рахунок (Asking for the Bill)

Ви п'єте напій. Ви просите рахунок. В Україні є два різні слова:
(You drink the beverage. You ask for the bill. In Ukraine, there are two different words:)

- **раху́нок**: Цей документ показує суму. (This document shows the amount.)
- **чек**: Ви отримуєте цей папір після оплати. (You get this paper after paying.)

Ви хочете заплатити. Ви просите «раху́нок».
(You want to pay. You ask for the "rakhunok".)

- «Чи можна, будь ла́ска, раху́нок?» (May I have the bill, please?)

> [!warning]
> Правильно просити «раху́нок» перед оплатою, а не «чек». Офіціант приносить чек пізніше.
> (It is correct to ask for the "rakhunok" before paying, not the "chek". The waiter brings the receipt later.)

### Як платити (How to Pay)

Офіціант питає про оплату. Ось дві корисні фрази:
(The waiter asks about payment. Here are two useful phrases:)

- «ка́рткою» (by card)
- «готі́вкою» (in cash)

Ви говорите коротко:
(You speak shortly:)

- «Опла́та ка́рткою.» (Payment by card.)
- «Я заплачу́ готі́вкою.» (I will pay in cash.)

### Коротка розмова (A Short Conversation)

Let us look at a realistic conversation in a café. Notice how the customer uses polite forms.

**Бариста:** До́брий день! Що ви замо́вите? (Good afternoon! What will you order?)
**Клієнт:** До́брий день. Я бу́ду ка́ву. (Good afternoon. I will have coffee.)
**Бариста:** А яку ка́ву? (And which coffee?)
**Клієнт:** Ка́ву з молоко́м, будь ла́ска. (Coffee with milk, please.)
**Бариста:** Добре. (Good.)
*(later)*
**Клієнт:** Чи можна, будь ла́ска, раху́нок? (May I have the bill, please?)
**Бариста:** Так, звича́йно. (Yes, of course.)

## Продукція та Підсумок (Production and Summary)

Read this short story about a visit to a café in Ukraine.

> Марі́я в кафе́. Офіціа́нт пита́є: «До́брий день! Що бажа́єте?»
> (Mariia is in a café. The waiter asks: "Good afternoon! What would you like?")
> Марі́я відповіда́є: «До́брий день. Я бу́ду чай з лимо́ном і без цу́кру.»
> (Mariia answers: "Good afternoon. I will have tea with lemon and without sugar.")
> Офіціа́нт прино́сить чай. Марі́я п'є чай. Це ду́же смачни́й чай!
> (The waiter brings the tea. Mariia drinks the tea. It is very tasty tea!)
> По́тім Марі́я ка́же: «Мо́жна, будь ла́ска, раху́нок? Опла́та ка́рткою.»
> (Then Mariia says: "May I have the bill, please? Payment by card.")
> Офіціа́нт прино́сить раху́нок. Марі́я пла́тить і залиша́є чайові́.
> (The waiter brings the bill. Mariia pays and leaves a tip.)

Слово «чайові́» (tip) походить від слова «чай». В Україні прийнято залишати близько 10% на чай за гарне обслуговування.
(The word "chayovi" (tip) comes from the word for "tea". In Ukraine, it is customary to leave about 10% as a tip for good service.)

### Граматика (Grammar Recap)

Here is a quick summary of how feminine words completely change when you order them. Remember, masculine words (like сік, чай) and neuter words (like меню) never change!

| Dictionary Form (Nominative) | When Ordering (Accusative) |
|------------------------------|----------------------------|
| **вода́** (water) | Я бу́ду **во́ду** |
| **ка́ва** (coffee) | Я бу́ду **ка́ву** |
| **пі́ца** (pizza) | Я бу́ду **пі́цу** |

## Summary

Тепер українською мовою ви готові замовити популярний напій! Важливо знати одне правило. Правильна фраза — це «Я бу́ду...» замість «Я хо́чу...». Також треба змінювати закінчення **-а** на **-у** для жіночого роду.
(Now you are ready to order a popular drink in the Ukrainian language! It is important to know one rule. The correct phrase is "I will have..." instead of "I want...". It is also necessary to change the -a ending to -y for the feminine gender.)

1. Як сказати правильно? (How to say correctly?) — Я буду каву. / Я буду кава.
Відповідь (Answer): Я буду каву.
2. Ви хочете заплатити. Що ви просите? (You want to pay. What do you ask for?) — чек / рахунок
Відповідь (Answer): рахунок.
3. Як сказати «with milk»? (How to say "with milk"?) — без молока / з молоком
Відповідь (Answer): з молоком.
4. Яка форма правильна? (Which form is correct?) — Я буду сіку. / Я буду сік.
Відповідь (Answer): Я буду сік.


        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-cafe.md`

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

        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
          > Understand Café Dialogue: 8 items (min 8)
  > Customer and Waiter: 8 items (min 8)
  > Accusative Case Endings: 8 items (min 8)
  > Café Etiquette and Vocabulary: 8 items (min 8)
  > Vocabulary Match: 8 items (min 8)
  > Accusative Case Endings: 10 items (min 6)
  > Build the Sentence: 6 items (min 6)
  > Adjectives and Details: 8 items (min 8)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 1656/1200 (raw: 2049)
Activities   ✅ 8/8
Density      ✅ All > 6
Unique_types ✅ 6/4 types
Priority     ✅ Priority types used
Engagement   ✅ 3/3
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
Immersion    🇺🇦 38.1% (target 35-55% (M41))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [HEADING_LEVEL] Main section 'Summary' uses H2 (##) but spec requires H1 (#)
     → FIX: Change '## Summary' to '# Summary' for top-level TOC compliance


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 1 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/at-the-cafe-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/at-the-cafe.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/at-the-cafe-audit.log for details)

Running RAG word verification...
Verifying: at-the-cafe.md
  VESUM misses: 3 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 59493.67it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 251 | VESUM: 248 (98.8%) | RAG: 3 | Not found: 0
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/at-the-cafe-rag-audit.md
✅ RAG verification: all words verified

VESUM: 248/251 (99%) verified
⚠️ VESUM not found (3): Анна, Анни, Львів
        ```

        ## Current Content of Affected Section(s)


The word «чай» does not change. We say «чай». The word «сік» also does not change. 

Слова́ — неісто́ти. (Inanimate words.)
Сло́во не змі́нюється. (The word does not change.)
Це ду́же ле́гко. (This is very easy.)
Ви ка́жете словнико́ву фо́рму. (You say the dictionary form.)

Compare:

| Noun Form (Subject) | Object Form (Accusative) | Example |
|---------------------|----------------------------|---------|
| **чай** (tea) | **чай** | Я бу́ду чай. (I will have tea.) |
| **сік** (juice) | **сік** | Мо́жна, будь ла́ска, сік? (May I have juice, please?) |

> [!warning]
> A very common learner mistake is to say «Я бу́ду ка́ва». Always remember to change that final -а to a -у when ordering feminine items!

### Ваші напої (Customizing Your Drink)

Іноді́ ми хо́чемо ка́ву з молоко́м. Або́ чай без цу́кру. Це гото́ві фра́зи.

Sometimes we want coffee with milk. Or tea without sugar. These are ready phrases. 

Ви хо́чете ка́ву з молоко́м? (Do you want coffee with milk?)
Або́ чай без цу́кру? (Or tea without sugar?)
Це популя́рні фра́зи. (These are popular phrases.)
Ми їх ча́сто ка́жемо. (We say them often.)

Ось ще при́клади: (Here are more examples:)
Я лю́блю ка́ву з молоко́м. (I love coffee with milk.)
Він лю́бить чай без цу́кру. (He loves tea without sugar.)
Вона́ не лю́бить молоко́. (She does not love milk.)
Ми п'ємо́ во́ду. (We drink water.)
Вода́ ду́же ко́рисна. (Water is very healthy.)
Я п'ю ка́ву. (I drink coffee.)
Ти п'єш сік. (You drink juice.)
Він п'є чай. (He drinks tea.)
Вона́ п'є во́ду. (She drinks water.)
Ми п'ємо́ ка́ву з молоко́м. (We drink coffee with milk.)

Наприклад:

| Phrase | Meaning | Example |
|--------|---------|---------|
| **з молоко́м** | with milk | ка́ва з молоко́м (coffee with milk) |
| **без цу́кру** | without sugar | чай без цу́кру (tea without sugar) |

Я бу́ду ка́ву з молоко́м, будь ла́ска.
I will have coffee with milk, please.

## Практика (Practice)

Тепе́р ми бу́демо проси́ти ре́чі. Ми не ка́жемо кома́нди. Ми пита́ємо «мо́жна».

Now we will ask for things. We do not say commands. We ask "is it possible." 

Мале́нький діало́г: (A little dialogue:)
— До́брий день! (Good afternoon!)
— До́брий день! (Good afternoon!)
— Мо́жна меню́, будь ла́ска? (May I have the menu, please?)
— Так, ось меню́. (Yes, here is the menu.)
— Дя́кую. (Thank you.)
— Будь ла́ска. (You are welcome.)

### Непрямі прохання (Indirect Requests)

Instead of using a command like "Give me" or "Bring me," we ask a question: "Is it possible to have...?" We do this using the highly versatile word «Мо́жна» (is it possible / may I).

Мо́жна меню́, будь ла́ска?
May I have the menu, please?

Мо́жна во́ду, будь ла́ска?
May I have water, please?

Ще кі́лька ситуа́цій: (A few more situations:)
Ви в рестора́ні. (You are in a restaurant.)
Мо́жна меню́, будь ла́ска? (May I have the menu, please?)
Офіціа́нт дає́ меню́. (The waiter gives the menu.)
Ви чита́єте меню́. (You read the menu.)
Ви замовля́єте ї́жу. (You order food.)
Мо́жна пі́цу, будь ла́ска? (May I have pizza, please?)
Мо́жна суп, будь ла́ска? (May I have soup, please?)
Мо́жна сала́т, будь ла́ска? (May I have salad, please?)
Мо́жна хліб, будь ла́ска? (May I have bread, please?)
Мо́жна борщ, будь ла́ска? (May I have borscht, please?)

Notice that we still use the Accusative case here because you are asking for an object. «Вода́» becomes «во́ду». The word «меню́» is a foreign loanword, so it never changes its form. 

Ви та́кож мо́жете замо́вити ті́стечко. Сло́во «ті́стечко» не змі́нюється.

You can also order a pastry. The word «ті́стечко» does not change. 

### Оплата (Paying the Bill): Раху́нок vs Чек

Час плати́ти. Ви про́сите раху́нок. Ви ніко́ли не про́сите чек.

It is time to pay. You ask for the bill. You never ask for the receipt.

> [!tip]
> In Ukrainian, the piece of paper the waiter (офіціа́нт) brings you with the total amount to pay is called «раху́нок». The word «чек» is the printed, official receipt you receive *after* you have paid.

Мо́жна раху́нок, будь ла́ска?
May I have the bill, please?

### Деталі замовлення (Clarifying Your Order)

Бари́ста мо́же ста́вити пита́ння. Яка́ ка́ва? Вели́ка чи мала́? Холо́дна чи гаря́ча?

The barista can ask questions. Which coffee? Large or small? Cold or hot?

Бари́ста ста́вить пита́ння. (The barista asks questions.) Він пита́є про ка́ву. (He asks about the coffee.) 

Наприклад:

| Adjective / Phrase | Meaning |
|--------------------|---------|
| **вели́кий** | large |
| **мали́й** | small |
| **холо́дний** | cold |
| **гаря́чий** | hot |
| **з га́зом** | sparkling (with gas) |
| **без га́зу** | still (without gas) |

Во́ду з га́зом, будь ла́ска. Мо́жна, будь ла́ска, гаря́чу ка́ву?

Sparkling water, please. May I have hot coffee, please?

## Продукція та Підсумок (Production and Summary)

Ви гото́ві йти в кав'я́рню. Ви зна́єте слова́. Ви мо́жете замовля́ти.

You are ready to go to a café. You know the words. You can order. 

Я заплачу́ ка́рткою. Я заплачу́ готі́вкою. Я залишу́ чайові́.

I will pay by card. I will pay in cash. I will leave a tip.

Істо́рія А́нни: (Anna's story:)
А́нна хо́че пи́ти. (Anna wants to drink.)
Вона́ замовля́є во́ду. (She orders water.)
Вона́ ка́же: «Я бу́ду во́ду, будь ла́ска». (She says: "I will have water, please.")
Бари́ста дає́ во́ду. (The barista gives the water.)
А́нна пла́тить ка́рткою. (Anna pays by card.)
Вона́ ка́же: «Дя́кую!». (She says: "Thank you!")
Це бу́ла смачна́ вода́. (This was tasty water.)
А́нна йде додо́му. (Anna goes home.)
А́нна щасли́ва. (Anna is happy.)
За́втра вона́ зно́ву при́йде сюди́. (Tomorrow she will come here again.)

### Діалог у кав'ярні (Café Roleplay)

Let us put everything together in a short, realistic café dialogue (діало́г). 

— До́брий день! Мо́жна меню́, будь ла́ска?
— До́брий день! Так, ось меню́. Що ви замо́вите?
— Я бу́ду ка́ву й шокола́дне ті́стечко.
— Яку́ ка́ву? З молоко́м чи без цу́кру?
— Мо́жна, будь ла́ска, вели́ку ка́ву з молоко́м?
— До́бре.

*(Later, after enjoying the food...)*

— Мо́жна раху́нок, будь ла́ска? Я заплачу́ ка́рткою.
— Звича́йно.

**English Translation:**
— Good afternoon! May I have the menu, please?
— Good afternoon! Yes, here is the menu. What will you order?
— I will have coffee and a chocolate pastry.
— Which coffee? With milk or without sugar?
— May I have a large coffee with milk, please?
— Good.
— May I have the bill, please? I will pay by card.
— Of course.

### Граматика (Grammar Recap): Accusative Endings

Remember this simple rule when ordering objects:

| Gender | Dictionary Ending | Ordering Ending (Accusative) | Example |
|--------|-------------------|------------------------------|---------|
| Feminine | -а | **-у** | вода́ → во́ду |
| Masculine | consonant | **no change** | чай → чай |
| Neuter | -о, -е, -ю | **no change** | меню́ → меню́ |

### Перевірка (Self-Check Questions)

Це ціка́во! (It is interesting!) Ви зна́єте ці слова́. (You know these words.)

1. You want to order water. How do you correctly say "I will have water" using the Accusative case?
2. You want to ask for the menu politely. What magic question word should you use instead of "give me"?
3. You are ready to leave and need to pay. Should you ask the waiter (офіціа́нт) for a «чек» or a «раху́нок»?
4. What does the phrase «ка́ва без цу́кру» mean in English?

## Summary

Ви ви́вчили нові́ слова́. Ви зна́єте знахі́дний відмі́нок. Ви мо́жете замовля́ти напо́ї. Тепе́р ви гото́ві йти в кав'я́рню в Украї́ні!

You learned how to politely order drinks and food in a café, including using the Accusative case for objects, making indirect requests, and paying the bill. Now you are ready to visit a café in Ukraine!

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

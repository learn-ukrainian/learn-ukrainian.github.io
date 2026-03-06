        # Escalation Fix — validate

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
          > True or False?: 8 items (min 8)
  > Match the Ending: 8 items (min 8)
  > Complete the Sentence: 8 items (min 8)
  > Check Your Understanding: 8 items (min 8)
  > Sort by Person: 15 items (min 6)
  > Build the Sentence: 6 items (min 6)
  > Match the Meaning: 8 items (min 8)
  > Natural Speech: 8 items (min 8)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 1833/1200 (raw: 1993)
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
Immersion    🇺🇦 37.7% (target 25-40% (M15))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [HEADING_LEVEL] Main section 'Summary' uses H2 (##) but spec requires H1 (#)
     → FIX: Change '## Summary' to '# Summary' for top-level TOC compliance


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
   → 1 violations (minor)


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-living-verb-i-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/the-living-verb-i.json

❌ AUDIT FAILED. Correct errors before proceeding.

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/the-living-verb-i-audit.log for details)

Running RAG word verification...
Verifying: the-living-verb-i.md
  VESUM misses: 8 — querying RAG...
[embed] Loading BGE-M3 from BAAI/bge-m3...

Fetching 30 files:   0%|          | 0/30 [00:00<?, ?it/s]
Fetching 30 files: 100%|██████████| 30/30 [00:00<00:00, 13292.74it/s]
[embed] BGE-M3 loaded.
You're using a XLMRobertaTokenizerFast tokenizer. Please note that with a fast tokenizer, using the `__call__` method is faster than using a method to encode the text followed by a call to the `pad` method to get a padded encoding.
  Words: 282 | VESUM: 274 (97.2%) | RAG: 3 | Not found: 5
  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/the-living-verb-i-rag-audit.md
⚠️  RAG verification found unverified words (see audit report)

VESUM: 274/282 (97%) verified
⚠️ VESUM not found (8): ати, ду, ю, ють, ємо, єте, єш, Іван
        ```

        ## Current Content of Affected Section(s)

        (We have the same rule for the verb **знати** (to know). We have the stem of the word: **зна-**. Then we add our new endings.)

Я зна́ю цю правду.
(I know this truth.)

Ти зна́єш усе.
(You know everything.)

Вона зна́є правило.
(She knows the rule.)

Правило просте і надійне.
(The rule is simple and reliable.)
Ви вивчаєте ці шість закінчень і знаєте сотні нових слів.
(You learn these six endings and you know hundreds of new words.)

## Практика (Practice)

Ви розумієте нове правило.
(You understand the new rule.)
Ми працюємо і будуємо речення.
(We work and build sentences.)
Ми також знаємо часті помилки.
(We also know frequent mistakes.)

Дуже велика помилка — це використовувати словникову форму. В англійській мові це нормально. В українській мові ми завжди маємо нове закінчення для кожної особи.
(A very big mistake is using the dictionary form. In English it is normal. In Ukrainian we always have a new ending for each person.)

> [!warning]
> Never say «Я читати» or «Я працювати». This literally sounds like "I to read" or "I to work" to a native speaker. Це дуже часта помилка.
(This is a very common mistake.)
Always remember to drop the **-ти** and add the correct personal ending.

Ми працюємо разом.
(We work together.)
Ми маємо прості об'єкти.
(We have simple objects.)

Наприклад:

Я читаю новий журнал.
(I am reading a new magazine.)

Я слухаю цікаве радіо.
(I am listening to interesting radio.)

Я пишу довгий лист.
(I am writing a long letter.)

Ми вивчаємо українську мову.
(We are studying the Ukrainian language.)

Ви знаєте це слово.
(You know this word.)

У цих прикладах ми маємо прості об'єкти: журнал, радіо чи лист. Ви бачите, як красиво працює структура.
(In these examples, we use inanimate objects like a magazine, a radio, or a letter. Notice how the structure flows beautifully.)
The sentence goes straight from the actor, to the action, to the object.

Дуже часта звичка — це використовувати слово «я» в кожному реченні. Це не помилка, але це звучить неприродно. Закінчення слова вже означає «я».
(Another common habit for English speakers is using the pronoun **я** (I) in every single sentence. While it is not grammatically wrong, it sounds unnatural in Ukrainian. Since the verb ending **-ю** already means "I", repeating the pronoun constantly feels heavy.)

Українці говорять про щоденні дії інакше. Ми часто не говоримо слово «я».
(Native speakers usually talk about their daily routine differently. They drop the pronouns to create a smooth flow.)

Compare:

Працюю багато щодня.
(I work a lot every day.)

Слухаю нову музику.
(I listen to new music.)

Пишу повідомлення зараз.
(I write a message now.)

Відпочиваю вдома.
(I am resting at home.)

Це робить мову дуже природною. Практика для вечора. Ви бачите: слова роблять усю роботу.
(This makes the language very natural. Evening routine practice. Notice how the verbs do all the work.)

Я вдома.
(I am at home.)

Слухаю радіо.
(I am listening to the radio.)

Читаю новини.
(I am reading the news.)

Думаю про це.
(I am thinking about it.)

Ви практикуєте ці короткі речення і маєте гарний результат. Пам'ятаємо нове правило.
(You practice these short sentences and have a good result. We remember the new rule.)
Слово робить усю роботу. Закінчення показує особу.
(The verb does all the work. The ending shows the person.)

### Діалог (Dialogue)

Reading practice:

— Привіт! Ти працюєш вдома зараз?
(Hi! Are you working at home now?)
— Привіт. Так, працюю.
(Hi. Yes, I am working.)
— Ти слухаєш радіо?
(Are you listening to the radio?)
— Ні, я читаю новий журнал.
(No, I am reading a new magazine.)
— Я розумію. Ти знаєш, де Іван?
(I understand. Do you know where Ivan is?)
— Він відпочиває. Він слухає музику.
(He is resting. He is listening to music.)
— А ви? Ви чекаєте на автобус?
(And you plural? Are you waiting for a bus?)
— Так, ми чекаємо на автобус.
(Yes, we are waiting for a bus.)
— Добре. Ми також чекаємо.
(Good. We are also waiting.)

### Мій день (My day)

Я працюю дуже багато.
(I work a lot.)
Слухаю радіо вранці.
(I listen to the radio in the morning.)
Вдень я читаю листи.
(During the day I read letters.)
Пишу повідомлення.
(I write messages.)
Увечері я відпочиваю вдома.
(In the evening I rest at home.)
Слухаю нову музику.
(I listen to new music.)
Думаю про це багато.
(I think about this a lot.)
Я знаю, що це важливо.
(I know that this is important.)
Ми працюємо і ми вивчаємо українську мову.
(We work and we study the Ukrainian language.)
Ви знаєте, як це працює.
(You know how this works.)
Вони також знають.
(They also know.)
Ми розуміємо все.
(We understand everything.)

## Культурний аспект та підсумок (Cultural Insight and Summary)

You have just unlocked a massive and essential part of the Ukrainian language. The **-ати** pattern is truly your master key. By learning just one set of endings, you now have the power to use a huge number of action words in your daily conversations.

> [!culture]
> В Україні ми маємо прислів'я.
(In Ukraine we have a proverb.)
«Птиця — це її пір'я, а людина — це її мова»
(A bird is its feathers, and a person is their speech.)
Speaking accurately and using the correct verb endings shows care and respect for the rich Ukrainian language! Ukrainians appreciate when learners try to use the correct grammar.

Ось нові правила.
(Here are the new rules.)
Перше правило: ми маємо основу слова без **-ти**. Друге правило: ми додаємо нові закінчення: **-ю, -єш, -є, -ємо, -єте, -ють**.
(First rule: we have the word stem without **-ти**. Second rule: we attach personal endings: **-ю, -єш, -є, -ємо, -єте, -ють**.)

Наприклад:

Ми розуміємо все.
(We understand everything.)

Ви чекаєте на автобус.
(You are waiting for a bus.)

Вони грають на гітарі.
(They play the guitar.)

Ти знаєш багато слів.
(You know many words.)

Third, always remember the pro-drop rule. The verb ending alone tells us who is performing the action, so you do not need to repeat the pronoun every single time. Це дуже природно.
(This is very natural.)

Here are a few quick questions to check your understanding before we finish:

1. Що ми використовуємо для «ми»?
(What ending do we use for **ми**?)
2. Чи завжди ми говоримо «я»?
(Do we always say the pronoun **я**?)
3. Як ми маємо основу слова «читати»?
(How do we find the stem for the verb **читати**?)
4. Як ми кажемо «I am reading» українською?
(How do we say "I am reading" in Ukrainian?)

Ми робимо фантастичний прогрес сьогодні!
(We make fantastic progress today!)
You are no longer just describing static things—you are finally talking about life in motion!

## Summary

Congratulations on mastering the first conjugation! You have learned the basic structure of the present tense and how to make simple action sentences without always using pronouns.

        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-living-verb-i.md`

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

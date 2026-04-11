<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG — drop textbook search -->
# V6 Pre-Write Verification — Linguistic Fact Checking

You MUST verify linguistic facts using the tools below BEFORE writing begins. This is a verification-only step — do NOT write any module content.

The wiki article already contains curated textbook content — your job here is to verify VOCABULARY, GRAMMAR RULES, CALQUES, and CEFR LEVELS using linguistic tools.

## Module

**Module:** 57: Кличний відмінок (офіційний) (B1, B1.5 [Case Nuances & Prepositions])

## Plan vocabulary to verify

- кличний відмінок (vocative case)
- звертання (address/salutation)
- по батькові (patronymic)
- пан/пані (Mr./Ms. — formal address)
- добродій/добродійка (Sir/Madam — very formal)
- шановний/шановна (respected/dear — formal letter opening)
- вельмишановний (most respected — very formal)
- колега (colleague — common address in workplace)
- прізвище (surname)
- посада (position/title)
- офіційний (official/formal)
- діловий (business-related)
- листування (correspondence)
- панове (gentlemen — plural formal address)

## Sections to research

- **Повторення: кличний відмінок**: Quick review of vocative formation from A2 (Авраменко Grade 6 p.106): І відміна тверда: -о (мамо, Миколо, Галино) І відміна м'яка: -е, -є (Надіє, Анастасіє, подрузе) ІІ відміна тверда: -е (Іване, Денисе, Олександре) ІІ відміна м'яка: -ю (Ігорю, Сергію, Андрію) Чоловічі імена на -а: -о (Микито, Сашо, Ілько); Important patterns learners may have missed: -ко ending: Тарасику, братику (diminutive) Nouns in -ець: -цю (хлопцю, молодцю) Names ending in -ій: -ію (Василію, Дмитрію) or -іє (Василіє — archaic); ІІІ відміна: -е (радосте, любове, молоде) Plural vocative = plural nominative for most nouns (друзі!, колеги!, студенти!). Practice: form vocative for 15 names covering all declension classes.
- **Офіційні звертання**: From Литвінова Grade 6 p.141: пан + ім'я: пане Євгене, пане Миколо пані + ім'я: пані Оксано (but also: пані Оксана — Н.в. tolerated) добродій → добродію, добродійка → добродійко These are the standard Ukrainian formal address forms.; Ім'я + по батькові — both words in Кл.в. (Заболотний Grade 11 p.98): Іване Вікторовичу, Маріє Степанівно, Олексію Миколайовичу. Masculine по батькові: -овичу (Петровичу, Івановичу) Feminine по батькові: -івно (Петрівно, Іванівно); Загальна назва + прізвище — ONLY first word in Кл.в. (Заболотний Grade 11 p.98): кореспонденте Левчук (not *кореспонденте Левчуку) професоре Ковальчук, лікарю Петренко But: друже Іване (both vocative when both are common or given names)
- **Кличний відмінок у діловому листуванні**: Business letter opening: Шановний пане Директоре! Шановна пані Головою! Шановні колеги! (plural — Н.в. and Кл.в. coincide) Вельмишановний добродію! (very formal); Email format: Добрий день, Олександре Миколайовичу! Вітаю, пане Петре! Шановна Маріє Степанівно, пишу з приводу... The vocative is MANDATORY in Ukrainian formal address — using Н.в. (*Олександр Миколайович!) sounds unnatural.; Closing formulas with vocative echo: 'З повагою, Олександр Петренко' (formal close — no vocative). But: 'Чекаю на Вашу відповідь, Іване Олексійовичу.' (vocative in the closing sentence — direct address). Also: 'Дякую Вам, шановна Маріє Степанівно, за допомогу.'
- **Звертання до груп і титулів**: Plural address: Шановні депутати! Дорогі друзі! Панове! Plural vocative = plural nominative for most nouns. Exception: панове (vocative of пани in address context).; Religious and military titles: отче (отець), владико (владика), генерале (генерал). Historical: козаче (козак), гетьмане (гетьман). Modern: пане Президенте, пані Міністре (or: пані Міністерко).; Cultural note: Ukrainian vocative is ALIVE and productive, unlike many European languages. Using it correctly signals respect and cultural competence. NOT using it (substituting Н.в.) sounds foreign or rude in formal contexts.
- **Практика в контексті**: Role play: formal meeting. Learners address each other using full formal address: ім'я + по батькові in vocative. 'Шановний Андрію Олексійовичу, дозвольте представити вам нашу колегу, Олену Вікторівну. Олено Вікторівно, це Андрій Олексійович.'; Letter writing: write a formal complaint to a company, a thank-you letter to a teacher, or an invitation to an event. Each must begin with correct vocative address.; Error analysis: common mistakes by L2 speakers: *Шановний Іван Петрович! (should be Іване Петровичу) *Пані Оксано Петрівно! (correct — both in vocative) *Докторе Ковальчуку! (should be Ковальчук — прізвище stays Н.в.)
- **Підсумок**: Vocative decision tree: Informal: Оксано! Андрію! Neutral: пане/пані + ім'я в Кл.в. Formal: Шановний(-а) + пане/пані + посада/ім'я + по батькові в Кл.в. Title + прізвище: тільки перше слово в Кл.в.; Punctuation with vocative (Авраменко Grade 8 p.133): Vocative address is separated by comma(s): Оксано, підійди сюди. Шановний Іване Петровичу, дозвольте звернутися до Вас. If the address is at the beginning with exclamation — capitalize next word: Друзі! Сьогодні важливий день. If address is emphatic with О: О Україно! О рідний краю!; Preview: next modules — часові прийменники, причина і мета.

## Instructions

Complete ALL of the following verification tasks. Each task MUST include at least one tool call.

### Task 1: Verify ALL vocabulary words exist in VESUM

Call `verify_words` with EVERY word from the plan vocabulary above. Batch them (10-15 per call).

Report:
- ✅ Words confirmed in VESUM
- ❌ Words NOT in VESUM (these must not be used in the module)

### Task 2: Verify grammar rules

For any grammar rules mentioned in the plan, call `query_pravopys` to confirm the official 2019 rule.

Report the Правопис section number and key rule text.

### Task 3: Check for calques

Call `search_style_guide` for any phrases in the plan that might be calques. Check at least 3 phrases.

Report any calques found with the correct Ukrainian alternative.

### Task 4: Verify CEFR appropriateness

Call `query_cefr_level` on 5-10 key vocabulary words to confirm they match the target level (B1).

Report any words above the target level.

## Output format

Output your findings in this exact format:

<verification>
## VESUM Verification
- Confirmed: [list of verified words]
- Not found: [list of words to avoid]

## Grammar Rules
- [rule]: Правопис §[number] — [key text]

## Calque Warnings
- [phrase]: [calque or OK] — [correct form if calque]

## CEFR Check
- [word]: [level] — [OK or above target]
</verification>

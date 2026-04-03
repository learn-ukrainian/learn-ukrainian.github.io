## Linguistic Scan
Errors found:
- **Russianism/Calque**: "вражаючий масштаб" is a calque of "впечатляющий" (active participles on -учий/-ючий are discouraged; "разючий масштаб" is correct).
- **Syntactic Surzhyk**: "мається на увазі" is an artificial passive construction discouraged by standard style guides (a calque of "имеется в виду"). It should be active: "ми маємо на увазі".
- **Factual morphology error**: The text states "А дієслово отримує специфічне закінчення -ся." In Ukrainian morphology, -ся is a postfix/affix, not an ending (закінчення). This is a critical factual error.
- **Instrumental agent with impersonal passive**: "відкрито для вільного огляду відвідувачами" incorrectly places an agent ("відвідувачами" in instrumental case) alongside an impersonal form on -но/-то, violating the exact grammatical rule taught later in the module.

## Exercise Check
- `INJECT_ACTIVITY: quiz` — placed correctly, matches plan.
- `INJECT_ACTIVITY: fill-in` — placed correctly, matches plan.
- `INJECT_ACTIVITY: match-up` — placed correctly, matches plan.
- `INJECT_ACTIVITY: error-correction` — placed correctly, matches plan.
- `INJECT_ACTIVITY: sentence-builder` — placed correctly, matches plan.
- `INJECT_ACTIVITY: fill-in` — **DUPLICATE**. There are 6 markers instead of the plan's 5. This will duplicate the activity and cause a pipeline failure.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | Missing required plan points: the proverb comparison ("Добре слово дім будує"), the active-to-passive transformation examples ("Учні написали..."), and the explicit comprehension questions in the practice section. Word count (4833) exceeds the 4000 target by >20%. |
| 2. Linguistic accuracy | 6/10 | Uses calques ("вражаючий"), awkward passives ("мається на увазі"), morphological mislabeling ("закінчення -ся"), and violates its own rule about instrumental agents with impersonal passives ("відкрито... відвідувачами"). |
| 3. Pedagogical quality | 6/10 | Failed to include the required comprehension questions after the reading passage, and duplicated an activity marker which ruins the activity pacing and density limits. |
| 4. Vocabulary coverage | 7/10 | Missing the required vocabulary term "неперехідне дієслово" from the text. Other vocabulary successfully integrated. |
| 5. Exercise quality | 6/10 | Duplicate `fill-in` marker inserted at the end of the file. |
| 6. Engagement & tone | 9/10 | Good use of realistic examples (Palace of Culture, window washing) and avoiding overly gamified language. |
| 7. Structural integrity | 7/10 | Missing exact H2 match ("Підсумок та перехід" instead of "Підсумок та перехід до M24"). Word count exceeds target by 20%. |
| 8. Cultural accuracy | 10/10 | Excellent explanation of the difference between Ukrainian active preference and bureaucratic "канцелярит". |
| 9. Dialogue & conversation quality | 8/10 | Good contextual use of formal language, but hampered by the "відвідувачами" instrumental case error in the text. |

## Findings
[1. Plan adherence] [critical]
Location: Section "Пасив через зворотні дієслова"
Issue: Missing the proverb example required by the plan ("Добре слово дім будує...").
Fix: Add the proverb example to the end of the first paragraph.

[1. Plan adherence] [critical]
Location: Section "Форми на -но/-то: українська спеціальність"
Issue: Missing the transformation practice required by the plan ("Учні написали диктант...").
Fix: Add the transformation examples explicitly to the text.

[1. Plan adherence] [major]
Location: Section "Практика: пасив у контексті"
Issue: Missing the required comprehension questions after the reading passage.
Fix: Add the comprehension questions explicitly to the text.

[2. Linguistic accuracy] [major]
Location: `Щоб підкреслити вражаючий масштаб виконаних...`
Issue: "Вражаючий" is a calque of "впечатляющий" (active participle).
Fix: Replace with "разючий".

[2. Linguistic accuracy] [critical]
Location: `А дієслово отримує специфічне закінчення -ся.`
Issue: -ся is a postfix/affix, not an ending. Calling it "закінчення" is factually incorrect in grammar.
Fix: Change to "формотворчий афікс -ся".

[2. Linguistic accuracy] [major]
Location: `Це трапляється, коли державна установа чи велика організація мається на увазі як колективний виконавець.`
Issue: "мається на увазі" is an artificial passive construction criticized by style guides.
Fix: Rewrite in active voice: "ми маємо на увазі... як колективного виконавця".

[2. Linguistic accuracy] [critical]
Location: Dialogue: `вільного огляду відвідувачами. *(` and translation.
Issue: Using "відвідувачами" (instrumental) with "відкрито" (-но/-то) violates the Ukrainian grammatical rule taught in the very same module.
Fix: Remove "відвідувачами" and its translation.

[3. Pedagogical quality] [critical]
Location: End of "Практика: пасив у контексті"
Issue: A duplicate `INJECT_ACTIVITY: fill-in` marker was added.
Fix: Remove the duplicate marker.

[4. Vocabulary coverage] [major]
Location: Section "Пасив через зворотні дієслова"
Issue: Required vocabulary "неперехідне дієслово" is missing.
Fix: Insert definition of intransitive verb as contrast to transitive.

[7. Structural integrity] [major]
Location: `## Підсумок та перехід`
Issue: H2 header does not match the plan's exact `content_outline`.
Fix: Rename to `## Підсумок та перехід до M24`.

## Verdict: REVISE
The module has several linguistic and factual errors (calling an affix an "ending", putting an instrumental agent on an impersonal passive, and using an active-participle calque), as well as structural defects (missing required vocabulary, missing plan examples, missing questions, and a duplicated activity marker). It must be revised to meet B1 curriculum standards.

<fixes>
- find: "Щоб підкреслити вражаючий масштаб виконаних"
  replace: "Щоб підкреслити разючий масштаб виконаних"
- find: "без жодного прийменника. Давайте уважно"
  replace: "без жодного прийменника. Натомість **неперехідне дієслово** *(intransitive verb)* такої здатності не має, тому від нього пасив утворити неможливо. Давайте уважно"
- find: "на сам об'єкт будівництва.\n\nАле що робити,"
  replace: "на сам об'єкт будівництва. Наприклад, порівняйте: «Добре слово дім будує» (активний стан, слово виконує дію) та варіант із тим самим змістом «Поганим словом усе руйнується» (пасивний стан на -ся, дія спрямована на об'єкт).\n\nАле що робити,"
- find: "А дієслово отримує специфічне закінчення -ся."
  replace: "А дієслово отримує специфічний формотворчий афікс -ся."
- find: "Це трапляється, коли державна установа чи велика організація мається на увазі як колективний виконавець."
  replace: "Це трапляється, коли ми маємо на увазі державну установу чи велику організацію як колективного виконавця."
- find: "вільного огляду відвідувачами. *("
  replace: "вільного огляду. *("
- find: "for free viewing by visitors.)*"
  replace: "for free viewing.)*"
- find: "певний завершений робочий процес.\n\nОднак під час використання"
  replace: "певний завершений робочий процес. Спробуйте утворити такі речення самостійно: «Учні написали диктант» стає «Диктант написано», а «Архітектор спроєктував будівлю» перетворюється на «Будівлю спроєктовано». Зверніть увагу, як виконавець дії повністю зникає — у цьому і полягає головний сенс таких форм.\n\nОднак під час використання"
- find: "про імена виконавців."
  replace: "про імена виконавців. Дайте відповіді на запитання: Знайдіть усі конструкції на -но/-то у тексті. Спробуйте перетворити їх на активні речення. Чому автор обрав пасив у цих випадках?"
- find: "<!-- INJECT_ACTIVITY: fill-in, Complete sentences with the correct -но/-то form of the given verb, 8 items -->\n\nНаостанок нам варто"
  replace: "Наостанок нам варто"
- find: "## Підсумок та перехід\n\nЧас підбити підсумки"
  replace: "## Підсумок та перехід до M24\n\nЧас підбити підсумки"
</fixes>

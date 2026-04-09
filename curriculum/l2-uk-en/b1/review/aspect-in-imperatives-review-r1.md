## Linguistic Scan
Two linguistic errors found:
1. `«Заспокойся і говоріть повільніше»` — Grammatical mismatch. The text incorrectly mixes the second-person singular (`Заспокойся`) with the second-person plural/formal (`говоріть`) in the same sentence. 
2. `Авторизація тривалого процесу` — An English calque. In Ukrainian, "авторизація" strictly refers to IT authentication or copyright, not granting "permission/authorization" for an action. The natural phrase is "Дозвіл на тривалий процес".

(Note: VESUM incorrectly flagged "прийом" and "поліцейського" as not found; both are valid, standard Ukrainian forms and were not penalized.)

## Exercise Check
All 6 planned activity markers are present, logically placed after the relevant teaching units, and matched perfectly in pedagogical focus to the plan's `activity_hints`:
1. `<!-- INJECT_ACTIVITY: diagnostic-aspect-quiz -->` (Type: quiz, placed at the start as a diagnostic).
2. `<!-- INJECT_ACTIVITY: positive-imperative-choice -->` (Type: fill-in).
3. `<!-- INJECT_ACTIVITY: imperative-category-sort -->` (Type: group-sort).
4. `<!-- INJECT_ACTIVITY: match-up -->` (Type: match-up).
5. `<!-- INJECT_ACTIVITY: error-correction-pragmatics -->` (Type: error-correction).
6. `<!-- INJECT_ACTIVITY: guest-rules-writing -->` (Type: open-writing).

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | DEDUCT for missed dialogue contrasts. The plan explicitly specified that the dialogues must contrast pf commands with impf rules (`наріж` vs `не додавай`; `візьми` vs `не запізнюйся`). The writer ignored this and made the first dialogue entirely pf and the second entirely impf. REWARD for covering all `content_outline` sections and maintaining correct structure. |
| 2. Linguistic accuracy | 8/10 | DEDUCT for the critical singular/plural grammatical mismatch (`Заспокойся і говоріть`) and the calque (`Авторизація`). REWARD for excellent general language flow and accurate explanation of semantic boundaries. |
| 3. Pedagogical quality | 10/10 | REWARD for an outstanding explanation of the pragmatics behind aspect. Framing imperfective positive imperatives as "invitations/permissions" rather than arbitrary exceptions is excellent pedagogy. |
| 4. Vocabulary coverage | 9/10 | DEDUCT slightly for missing the explicit introduction of the perfective `почати/почніть` as contrasted with the imperfective `починайте`. All other required vocabulary items are woven naturally into the text. |
| 5. Exercise quality | 10/10 | REWARD for perfect placement of markers exactly where the conceptual teaching requires them. |
| 6. Engagement & tone | 10/10 | REWARD for the strong decolonial framing regarding the "Давай(те)" calque and replacing it with synthetic Ukrainian imperative forms (`Поговорімо`, `Ходімо`). |
| 7. Structural integrity | 10/10 | REWARD for exceeding the word count (4231 words) and perfectly matching all H2 headers required by the `content_outline`. |
| 8. Cultural accuracy | 10/10 | REWARD for culturally authentic framing of hospitality (the difference between `Сядь!` and `Сідайте!`). |
| 9. Dialogue & conversation quality | 7/10 | DEDUCT for failing to provide the specific dialogue mechanics requested by the plan. The pedagogical value of the dialogues is severely diminished because they lack the pf/impf contrast in a single situation. |

## Findings
[2] [CRITICAL]
Location: `Або якщо ваш стурбований співрозмовник занадто сильно поспішає і ковтає слова під час важливого виступу, ви тихо скажете йому: «Заспокойся і говоріть повільніше (speak slower)».`
Issue: Grammatical mismatch mixing singular "ти" (заспокойся) and plural/formal "ви" (говоріть) in the same command.
Fix: Change `Заспокойся` to `Заспокойтеся`.

[2] [MAJOR]
Location: `Авторизація тривалого процесу — це унікальна територія недоконаного виду`
Issue: The word "Авторизація" is an English calque (authorization) when used to mean "permission" for an action.
Fix: Replace with `Дозвіл на тривалий процес`.

[9] [MAJOR]
Location: `> — **Інструктор:** Чудово. Тепер трохи підсмаж до золотистого кольору, а **врешті посоли** *(finally salt)* і негайно зніми з вогню.`
Issue: The cooking dialogue completely missed the contrast with imperfective general rules (e.g., "не додавай") that the plan specifically requested.
Fix: Append the missing imperfective command to the instructor's final dialogue line.

[9] [MAJOR]
Location: `> — **Мама:** Сину, будь ласка, **не запізнюйся** *(don't be late)* сьогодні на свої перші уроки...`
Issue: The parent dialogue completely missed the contrast with perfective commands (e.g., "візьми парасольку, не забудь ключі") requested by the plan.
Fix: Integrate the perfective commands into the mother's speech and adjust the son's reply to sound natural.

## Verdict: REVISE
The module features brilliant pedagogical explanations but contains a critical grammatical mismatch, a calque, and misses the pedagogical contrast in the dialogues specifically requested by the plan. The fixes will inject the missing dialogue contrasts and correct the grammar.

<fixes>
- find: "«Заспокойся і говоріть повільніше (speak slower)»."
  replace: "«Заспокойтеся і говоріть повільніше (speak slower)»."
- find: "Авторизація тривалого процесу — це унікальна територія недоконаного виду"
  replace: "Дозвіл на тривалий процес — це унікальна територія недоконаного виду"
- find: "Тепер трохи підсмаж до золотистого кольору, а **врешті посоли** *(finally salt)* і негайно зніми з вогню."
  replace: "Тепер трохи підсмаж до золотистого кольору, а **врешті посоли** *(finally salt)* і негайно зніми з вогню. Але **не додавай** *(don't add - impf)* забагато солі."
- find: "> — **Мама:** Сину, будь ласка, **не запізнюйся** *(don't be late)* сьогодні на свої перші уроки. Взагалі, намагайся ніколи не **запізнюватися** *(to be late)*. І після завершення школи ніколи **не розмовляй** *(don't talk)* з підозрілими незнайомцями на вулиці."
  replace: "> — **Мама:** Сину, **візьми** *(take - pf)* парасольку — обіцяють дощ. І **не забудь** *(don't forget - pf)* ключі! Також, будь ласка, **не запізнюйся** *(don't be late - impf)* сьогодні на уроки і ніколи **не розмовляй** *(don't talk - impf)* з незнайомцями."
- find: "> — **Син:** Добре, мамо, я все чудово зрозумів. Я обіцяю, що не буду цього робити."
  replace: "> — **Син:** Добре, мамо. Ключі я взяв, і обіцяю, що буду уважним і не буду цього робити."
</fixes>

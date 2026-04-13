## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym misuse, or forbidden Russian letters found in the Ukrainian examples I checked.

Factual grammar problems found:
- `§ Два питання — два види`: `You just take the infinitive, remove the «-ти», and add the standard past tense endings.` This teaches an overgeneralized past-tense formation rule; it is only safe for the regular pairs shown here.
- `§ Практика вибору виду`: `Using the imperfective form sounds like you gave up halfway.` and `Студенти часто кажуть: «Я вчора писав листа». Це звучить так, ніби процес не закінчився.` This misteaches imperfective past. In this context it is ambiguous without further context; it does not inherently mean “unfinished” or “gave up.”

## Exercise Check
- Prose markers present: `quiz...` after section 1, `match-up...` after section 3, `fill-in-aspect-choice` and `error-correction-aspect` after section 4.
- Matching inline YAML IDs exist for `quiz...`, `match-up...`, and `fill-in-aspect-choice`.
- `error-correction-aspect` does not have a matching inline YAML ID. The YAML defines `error-correction-aspect-practice`, so the planned error-correction activity will not inject.
- The inline quiz has 8 items as planned, but all 8 answers use `correct: 0`.
- The match-up activity covers signal words, but it does not include example sentences, even though the plan explicitly asks for “the correct aspect and example sentence.”

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All four planned sections are present and the main outline points are covered, but the planned error-correction activity will not inject (`<!-- INJECT_ACTIVITY: error-correction-aspect -->` vs YAML `id: error-correction-aspect-practice`), and the match-up activity omits the example sentences promised by the plan. |
| 2. Linguistic accuracy | 7/10 | No Russianisms/Surzhyk/calques found, but the lesson states `You just take the infinitive, remove the «-ти»...` and later says imperfective `sounds like you gave up halfway`, both of which are misleading grammar claims. |
| 3. Pedagogical quality | 6/10 | The module has many examples and a clear presentation-to-practice flow, but it overstates aspect choice in `If you want to say that you finished a task...` and turns the plan’s `ambiguous` example (`Я писав листа вчора`) into a false “unfinished” rule. |
| 4. Vocabulary coverage | 9/10 | Required plan vocabulary is well represented in context: `минулий час`, `процес`, `результат`, `довго`, `раптом`, and all five required verb pairs appear repeatedly in prose. |
| 5. Exercise quality | 4/10 | One inline marker cannot resolve to YAML, all eight quiz answers are in slot 0, and the match-up activity tests metalinguistic labels rather than the plan’s requested signal word + example sentence pairing. |
| 6. Engagement & tone | 7/10 | The teacher voice is generally clear, but `This isn't just a grammar trick; it is a core difference in how Ukrainians categorize the world` and `Українці завжди...` drift into inflated claims instead of concrete instruction. |
| 7. Structural integrity | 8/10 | The module has all required H2 headings and exceeds the 2000-word minimum (pipeline count: 2855), but the unresolved `error-correction-aspect` marker creates a publish-time structural break. |
| 8. Cultural accuracy | 7/10 | The module avoids Russian-centric framing, but `a core difference in how Ukrainians categorize the world` and `Українці завжди розрізняють...` essentialize speakers instead of describing a grammatical contrast. |
| 9. Dialogue & conversation quality | 8/10 | The dialogue has named speakers and a plausible Sunday context, but it is short and mostly demonstrative rather than a fuller natural exchange. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Два питання — два види` — `You just take the infinitive, remove the «-ти», and add the standard past tense endings.`  
Issue: This states a universal past-tense formation rule, which is false outside the regular verbs shown here.  
Fix: Limit the claim to the regular verbs in this lesson.

[PEDAGOGICAL QUALITY] [SEVERITY: critical]  
Location: `Практика вибору виду` — `If you want to say that you finished a task, always choose the perfective verb. Using the imperfective form sounds like you gave up halfway.`  
Issue: This teaches a false inference about imperfective past. Imperfective here signals process/non-result focus or ambiguity, not “gave up halfway.”  
Fix: Rephrase the tip so it contrasts result-focus vs process-focus without claiming failure.

[PEDAGOGICAL QUALITY] [SEVERITY: critical]  
Location: `Практика вибору виду` — `Студенти часто кажуть: «Я вчора писав листа». Це звучить так, ніби процес не закінчився. Українці чекають продовження...`  
Issue: This contradicts the plan’s own `ambiguous` treatment and teaches an overly rigid rule.  
Fix: Rewrite it to say the sentence is ambiguous without extra context; use perfective when the finished result is what matters.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: prose marker `<!-- INJECT_ACTIVITY: error-correction-aspect -->` and activities YAML `id: error-correction-aspect-practice`  
Issue: The marker ID and YAML ID do not match, so the planned error-correction exercise will not inject into the module.  
Fix: Rename the YAML ID to exactly `error-correction-aspect`.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: activities YAML quiz block — all eight items use `correct: 0`  
Issue: The answer key has a visible pattern, making the quiz easier by position rather than language knowledge.  
Fix: Reorder options and vary the correct index positions.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: activities YAML match-up block — e.g. `щодня -> Вказує на регулярну дію (недоконаний вид)`  
Issue: The plan asks learners to match signal words with the correct aspect and an example sentence, but the generated exercise only matches signal words to explanations.  
Fix: Replace the right-hand sides with short example sentences that include the aspect cue.

[CULTURAL ACCURACY] [SEVERITY: major]  
Location: `Два питання — два види` — `This isn't just a grammar trick; it is a core difference in how Ukrainians categorize the world.` and `Українці завжди розрізняють дію як процес і дію як результат.`  
Issue: This essentializes Ukrainian speakers and overstates a grammar point as a national worldview claim.  
Fix: Reframe both sentences as descriptions of Ukrainian grammar, not of what Ukrainians “always” do.

## Verdict: REVISE
The module has multiple fixable but real problems: two critical grammar-teaching overstatements, one publish-breaking activity ID mismatch, and two substantial exercise-design issues. It is not a rewrite case, but it should not ship unchanged.

<fixes>
- find: |
    This isn't just a grammar trick; it is a core difference in how Ukrainians categorize the world.
  replace: |
    This is not just a grammar trick; it is a central contrast in Ukrainian grammar.
- find: |
    Українці завжди розрізняють дію як процес і дію як результат.
  replace: |
    В українській мові часто розрізняють дію як процес і дію як результат.
- find: |
    You just take the infinitive, remove the «-ти», and add the standard past tense endings.
  replace: |
    For the regular verbs shown here, you remove the infinitive ending and add the usual past tense forms; some Ukrainian verbs form the past tense less regularly.
- find: |
    If you want to say that you finished a task, always choose the perfective verb. Using the imperfective form sounds like you gave up halfway.
  replace: |
    If you want to emphasize that a task is finished, choose the perfective verb. The imperfective form does not mean you gave up; without context, it simply focuses on the process rather than the result.
- find: |
    Студенти часто кажуть: «Я вчора писав листа». Це звучить так, ніби процес не закінчився. Українці чекають продовження: «...але не закінчив». Якщо лист готовий, треба казати: «Я вчора написав листа». Інша помилка — це слова типу «щодня». Не можна казати: «Він щодня зробив вправи». Якщо дія повторюється, ми повинні використовувати дієслово «робив».
  replace: |
    Студенти часто кажуть: «Я вчора писав листа». Без додаткового контексту це двозначно: ми розуміємо процес, але не знаємо, чи лист уже готовий. Якщо ви хочете підкреслити готовий результат, треба казати: «Я вчора написав листа». Інша помилка — це слова типу «щодня». Не можна казати: «Він щодня зробив вправи». Якщо дія повторюється, ми повинні використовувати дієслово «робив».
- find: |
    It sounds as if the process did not finish. Ukrainians expect a continuation: "...but did not finish." If the letter is ready, you must say: "Yesterday I wrote a letter."
  replace: |
    Without extra context, this is ambiguous: we understand the process, but we do not know whether the letter is already finished. If you want to emphasize the finished result, you should say: "Yesterday I wrote the letter."
- find: |
    - id: error-correction-aspect-practice
  replace: |
    - id: error-correction-aspect
- find: |
    - id: quiz-given-a-sentence-identify-whether-the-verb-is-imperfective-or-perfective-and-explain-why
      type: quiz
      instruction: Визначте вид дієслова та причину його використання
      items:
      - question: Я довго читав цю книгу.
        options:
        - Недоконаний (процес, тривалість)
        - Доконаний (результат)
        - Недоконаний (раптова дія)
        - Доконаний (повторювана дія)
        correct: 0
      - question: Він нарешті написав листа.
        options:
        - Доконаний (результат)
        - Недоконаний (процес)
        - Доконаний (повторювана дія)
        - Недоконаний (раптова дія)
        correct: 0
      - question: Ми щодня готували сніданок.
        options:
        - Недоконаний (регулярна дія)
        - Доконаний (результат)
        - Недоконаний (раптова дія)
        - Доконаний (послідовність)
        correct: 0
      - question: Вона раптом відкрила двері.
        options:
        - Доконаний (раптова дія)
        - Недоконаний (процес)
        - Доконаний (регулярна дія)
        - Недоконаний (довга тривалість)
        correct: 0
      - question: Студенти вчили нові слова весь вечір.
        options:
        - Недоконаний (процес)
        - Доконаний (результат)
        - Недоконаний (раптова дія)
        - Доконаний (послідовність)
        correct: 0
      - question: Брат швидко зробив домашнє завдання.
        options:
        - Доконаний (результат)
        - Недоконаний (процес)
        - Недоконаний (регулярна дія)
        - Доконаний (довга тривалість)
        correct: 0
      - question: Одного разу я побачив ведмедя в лісі.
        options:
        - Доконаний (одноразова дія)
        - Недоконаний (процес)
        - Доконаний (регулярна дія)
        - Недоконаний (раптова дія)
        correct: 0
      - question: Він часто читав новини в інтернеті.
        options:
        - Недоконаний (регулярна дія)
        - Доконаний (результат)
        - Доконаний (раптова дія)
        - Недоконаний (одноразова дія)
        correct: 0
      title: Визначте вид дієслова та причину його використання
  replace: |
    - id: quiz-given-a-sentence-identify-whether-the-verb-is-imperfective-or-perfective-and-explain-why
      type: quiz
      instruction: Визначте вид дієслова та причину його використання
      items:
      - question: Я довго читав цю книгу.
        options:
        - Доконаний (результат)
        - Недоконаний (раптова дія)
        - Недоконаний (процес, тривалість)
        - Доконаний (повторювана дія)
        correct: 2
      - question: Він нарешті написав листа.
        options:
        - Недоконаний (процес)
        - Доконаний (результат)
        - Доконаний (повторювана дія)
        - Недоконаний (раптова дія)
        correct: 1
      - question: Ми щодня готували сніданок.
        options:
        - Доконаний (результат)
        - Недоконаний (раптова дія)
        - Доконаний (послідовність)
        - Недоконаний (регулярна дія)
        correct: 3
      - question: Вона раптом відкрила двері.
        options:
        - Недоконаний (процес)
        - Доконаний (регулярна дія)
        - Доконаний (раптова дія)
        - Недоконаний (довга тривалість)
        correct: 2
      - question: Студенти вчили нові слова весь вечір.
        options:
        - Недоконаний (процес)
        - Доконаний (результат)
        - Недоконаний (раптова дія)
        - Доконаний (послідовність)
        correct: 0
      - question: Брат швидко зробив домашнє завдання.
        options:
        - Недоконаний (процес)
        - Недоконаний (регулярна дія)
        - Доконаний (довга тривалість)
        - Доконаний (результат)
        correct: 3
      - question: Одного разу я побачив ведмедя в лісі.
        options:
        - Недоконаний (процес)
        - Доконаний (одноразова дія)
        - Доконаний (регулярна дія)
        - Недоконаний (раптова дія)
        correct: 1
      - question: Він часто читав новини в інтернеті.
        options:
        - Доконаний (результат)
        - Доконаний (раптова дія)
        - Недоконаний (регулярна дія)
        - Недоконаний (одноразова дія)
        correct: 2
      title: Визначте вид дієслова та причину його використання
- find: |
    - id: match-up-match-signal-words-with-the-correct-aspect-and-example-sentence
      type: match-up
      instruction: З'єднайте сигнальне слово з його значенням та видом дієслова
      pairs:
      - left: щодня
        right: Вказує на регулярну дію (недоконаний вид)
      - left: нарешті
        right: Вказує на досягнутий результат (доконаний вид)
      - left: довго
        right: Вказує на тривалий процес (недоконаний вид)
      - left: раптом
        right: Вказує на несподівану, коротку дію (доконаний вид)
      - left: завжди
        right: Вказує на постійну звичку (недоконаний вид)
      - left: одного разу
        right: Вказує на конкретну подію в минулому (доконаний вид)
      - left: часто
        right: Вказує на дію, яка повторюється (недоконаний вид)
      - left: вже
        right: Вказує, що дія успішно завершена (доконаний вид)
      title: З'єднайте сигнальне слово з його значенням та видом дієслова
  replace: |
    - id: match-up-match-signal-words-with-the-correct-aspect-and-example-sentence
      type: match-up
      instruction: З'єднайте сигнальне слово з прикладом речення та видом дієслова
      pairs:
      - left: щодня
        right: Щодня вона готувала сніданок (недоконаний вид)
      - left: нарешті
        right: Нарешті він написав листа (доконаний вид)
      - left: довго
        right: Він довго готував вечерю (недоконаний вид)
      - left: раптом
        right: Раптом хтось постукав у двері (доконаний вид)
      - left: завжди
        right: У дитинстві ми завжди читали перед сном (недоконаний вид)
      - left: одного разу
        right: Одного разу ми поїхали в гори (доконаний вид)
      - left: часто
        right: Вона часто вчила нові слова ввечері (недоконаний вид)
      - left: вже
        right: Я вже вивчив ці слова (доконаний вид)
      title: З'єднайте сигнальне слово з прикладом речення та видом дієслова
</fixes>
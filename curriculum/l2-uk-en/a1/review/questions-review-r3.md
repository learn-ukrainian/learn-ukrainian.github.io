## Linguistic Scan
- [CRITICAL] `## Запере́чення` / `## Підсумок`: the module says `You must never separate them with other words.` and later `The particle **не** always stands directly before the verb.` That is a false absolute rule. Standard Ukrainian allows intervening words, e.g. textbook corpus has `не надто зациклюйтеся`.

## Exercise Check
- Marker inventory is correct: `quiz-question-word-choice`, `match-question-answer`, `fill-in-negation-transform`, `quiz-double-negation`.
- Marker placement is correct: the two question-word markers come after `## Пита́льні слова́`, and the two negation markers come after `## Запере́чення`.
- Issues:
- `quiz-question-word-choice` has 6 items, but the plan requires 8.
- `fill-in-negation-transform` has 6 items, but the plan requires 8.
- Both quiz blocks are patternable because every item uses `correct: 0`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All four planned H2 sections are present, and the required vocabulary is covered. But the navigation dialogue explanation says the tourist uses only `**де**`, `**куди**`, and `**як**`, while the plan’s dialogue motivation explicitly calls for `Де? Куди? Як? Коли? in real navigation`. Also, `rg` finds no `Варзацька`, `Ukrainian Lessons`, or `Episode 35` in the module. |
| 2. Linguistic accuracy | 8/10 | The Ukrainian examples are mostly solid, but the grammar explanation contains a factual error: `You must never separate them with other words.` / `The particle **не** always stands directly before the verb.` |
| 3. Pedagogical quality | 7/10 | The module broadly follows PPP, but the negation section teaches an overgeneralized rule that will mislead learners beyond the listed examples. |
| 4. Vocabulary coverage | 9/10 | All required items appear in prose or examples, and recommended items such as `ніхто`, `нічого`, `ніколи`, `жити`, `розуміти`, and `тому що` are introduced in context. |
| 5. Exercise quality | 5/10 | Placement is good, but `quiz-question-word-choice` and `fill-in-negation-transform` are both 2 items short of plan, and both quiz blocks keep the correct answer in slot `0` for every item. |
| 6. Engagement & tone | 7/10 | The tone is teacherly and clear, but several English opener lines are generic rather than sharply tied to Ukrainian usage. |
| 7. Structural integrity | 10/10 | All planned sections are present and ordered correctly; markdown is clean; pipeline word count is 1588, which is above target. |
| 8. Cultural accuracy | 9/10 | No Russia-centered framing or cultural inaccuracies found. |
| 9. Dialogue & conversation quality | 7/10 | Named speakers help, but the tourist exchange is thin and transactional (`Ви́бачте, де центр?` / `Центр там.`) and also misses the planned navigation use of `коли`. |

## Findings
[2. Linguistic accuracy] [SEVERITY: critical]  
Location: `## Запере́чення` / `## Підсумок` — `You must never separate them with other words.` / `The particle **не** always stands directly before the verb.`  
Issue: This teaches a false absolute rule about Ukrainian negation.  
Fix: Rephrase it as the core A1 pattern `не + verb`, not an exceptionless rule.

[1. Plan adherence] [SEVERITY: major]  
Location: first dialogue explanation — `The tourist uses **де** (where) ... **куди** (where to) ... and **як** (how)`  
Issue: The plan’s navigation dialogue explicitly calls for `Де? Куди? Як? Коли?`, but the published dialogue never models `коли` in that real navigation scene.  
Fix: Add one `коли` exchange to the tourist dialogue and update the explanation sentence.

[1. Plan adherence] [SEVERITY: major]  
Location: whole module — no matches for `Варзацька`, `Ukrainian Lessons`, or `Episode 35` in `questions.md`  
Issue: The plan includes two references, but the module never integrates or cites them.  
Fix: Add one brief sentence in the teaching prose tying the explanation to the Grade 4 textbook pattern and ULP Season 1, Episode 35.

[5. Exercise quality] [SEVERITY: major]  
Location: `activities/questions.yaml`, `quiz-question-word-choice` block  
Issue: The plan requires 8 items; the quiz has 6.  
Fix: Expand it to 8 items.

[5. Exercise quality] [SEVERITY: major]  
Location: `activities/questions.yaml`, `fill-in-negation-transform` block  
Issue: The plan requires 8 items; the fill-in has 6.  
Fix: Expand it to 8 items.

[5. Exercise quality] [SEVERITY: major]  
Location: `activities/questions.yaml`, both quiz blocks  
Issue: Every quiz item uses `correct: 0`, so answer positions are mechanically predictable.  
Fix: Reorder options so the correct answer varies by item.

## Verdict: REVISE
REVISE. There is a critical factual grammar error in the negation explanation, and there are multiple major plan/exercise defects: one planned dialogue point is missing, the planned references are uncited, and two activities are underbuilt and patternable.

<fixes>
- find: |
    To gather information effectively, you need a core set of linguistic tools. Ukrainian relies on seven essential question words: **хто** (who), **що** (what), **де** (where), **куди** (where to), **коли** (when), **чому** (why), and **як** (how). In neutral questions, these words usually come first.
  replace: |
    To gather information effectively, you need a core set of linguistic tools. Ukrainian relies on seven essential question words: **хто** (who), **що** (what), **де** (where), **куди** (where to), **коли** (when), **чому** (why), and **як** (how). In neutral questions, these words usually come first. This matches the basic school-textbook treatment of question words in Grade 4 materials such as Варзацька and the word-order and intonation focus in Ukrainian Lessons Podcast Season 1, Episode 35.

- find: |
    > **Тури́ст:** Ви́бачте, де центр? *(Excuse me, where is the center?)*
    > **Перехо́жий:** Центр там. *(The center is there.)*
    > **Турист:** Дякую! Куди́ іде́ цей авто́бус? *(Thanks! Where does this bus go?)*
    > **Перехожий:** Цей автобус іде в парк. *(This bus goes to the park.)*
    > **Турист:** До́бре. Як пройти́ до парку? *(Good. How to get to the park?)*
    > **Перехожий:** Пря́мо і напра́во. *(Straight and to the right.)*

    When arriving in a new city, finding your way relies heavily on your ability to use question words. The tourist uses **де** (where) to locate a static place, **куди** (where to) to ask about the direction of the bus, and **як** (how) to request instructions for reaching a destination.
  replace: |
    > **Тури́ст:** Ви́бачте, де центр? *(Excuse me, where is the center?)*
    > **Перехо́жий:** Центр там. *(The center is there.)*
    > **Турист:** Дякую! Куди́ іде́ цей авто́бус? *(Thanks! Where does this bus go?)*
    > **Перехожий:** Цей автобус іде в парк. *(This bus goes to the park.)*
    > **Турист:** Коли́ він іде? *(When does it go?)*
    > **Перехожий:** Зараз. *(Now.)*
    > **Турист:** До́бре. Як пройти́ до парку? *(Good. How to get to the park?)*
    > **Перехожий:** Пря́мо і напра́во. *(Straight and to the right.)*

    When arriving in a new city, finding your way relies heavily on your ability to use question words. The tourist uses **де** (where) to locate a static place, **куди** (where to) to ask about the direction of the bus, **коли** (when) to ask about timing, and **як** (how) to request instructions for reaching a destination.

- find: |
    The particle **не** forms a very tight unit with the verb that immediately follows it. You must never separate them with other words.
  replace: |
    In the basic A1 pattern, **не** usually goes before the verb: **Я не знаю. Він не працює.** At higher levels, other words can appear between **не** and the verb, but beginners should first master the simple pattern **не + verb**.

- find: |
    Negation in Ukrainian follows strict but simple patterns. The particle **не** always stands directly before the verb. When expressing absolute absence, Ukrainian demands double negation.
  replace: |
    Negation in Ukrainian follows simple beginner patterns. In the core A1 pattern, **не** goes before the verb: **Я не знаю.** When expressing absolute absence, Ukrainian demands double negation.

- find: |
    - id: quiz-question-word-choice
      type: quiz
      instruction: Оберіть правильне питальне слово (Choose the correct question word)
      items:
      - question: _____ ти живеш?
        options:
        - Де
        - Куди
        - Що
        - Хто
        correct: 0
      - question: _____ це? — Це стіл.
        options:
        - Що
        - Хто
        - Де
        - Коли
        correct: 0
      - question: _____ це? — Це мій студент.
        options:
        - Хто
        - Що
        - Де
        - Коли
        correct: 0
      - question: _____ ти йдеш?
        options:
        - Куди
        - Де
        - Як
        - Хто
        correct: 0
      - question: _____ ти працюєш? — Вранці.
        options:
        - Коли
        - Хто
        - Що
        - Де
        correct: 0
      - question: _____ справи? — Добре, дякую.
        options:
        - Як
        - Що
        - Хто
        - Чому
        correct: 0
  replace: |
    - id: quiz-question-word-choice
      type: quiz
      instruction: Оберіть правильне питальне слово (Choose the correct question word)
      items:
      - question: _____ ти живеш?
        options:
        - Де
        - Куди
        - Що
        - Хто
        correct: 0
      - question: _____ це? — Це стіл.
        options:
        - Хто
        - Що
        - Де
        - Коли
        correct: 1
      - question: _____ це? — Це мій студент.
        options:
        - Що
        - Де
        - Хто
        - Коли
        correct: 2
      - question: _____ ти йдеш?
        options:
        - Де
        - Як
        - Куди
        - Хто
        correct: 2
      - question: _____ ти працюєш? — Вранці.
        options:
        - Хто
        - Де
        - Коли
        - Що
        correct: 2
      - question: _____ справи? — Добре, дякую.
        options:
        - Що
        - Як
        - Хто
        - Чому
        correct: 1
      - question: _____ ти не працюєш? — Тому що я хочу спати.
        options:
        - Як
        - Коли
        - Де
        - Чому
        correct: 3
      - question: _____ це? — Це в парку.
        options:
        - Куди
        - Коли
        - Де
        - Хто
        correct: 2

- find: |
    - id: fill-in-negation-transform
      type: fill-in
      instruction: Зробіть речення заперечним (Make the sentence negative)
      items:
      - sentence: Я знаю. → Я ____ знаю.
        answer: не
        options:
        - ні
        - не
        - нічого
      - sentence: Хтось (Someone) знає. → ____ не знає.
        answer: Ніхто
        options:
        - Ніхто
        - Нічого
        - Не
      - sentence: Я бачу все (everything). → Я ____ не бачу.
        answer: нічого
        options:
        - ніхто
        - нічого
        - ні
      - sentence: Вона працює. → Вона ____ працює.
        answer: не
        options:
        - не
        - ніколи
        - ні
      - sentence: Він завжди (always) спить. → Він ____ не спить.
        answer: ніколи
        options:
        - ніколи
        - ніхто
        - не
      - sentence: Ми розуміємо. → Ми ____ розуміємо.
        answer: не
        options:
        - не
        - ні
        - нічого
  replace: |
    - id: fill-in-negation-transform
      type: fill-in
      instruction: Зробіть речення заперечним (Make the sentence negative)
      items:
      - sentence: Я знаю. → Я ____ знаю.
        answer: не
        options:
        - ні
        - не
        - нічого
      - sentence: Хтось (Someone) знає. → ____ не знає.
        answer: Ніхто
        options:
        - Ніхто
        - Нічого
        - Не
      - sentence: Я бачу все (everything). → Я ____ не бачу.
        answer: нічого
        options:
        - ніхто
        - нічого
        - ні
      - sentence: Вона працює. → Вона ____ працює.
        answer: не
        options:
        - не
        - ніколи
        - ні
      - sentence: Він завжди (always) спить. → Він ____ не спить.
        answer: ніколи
        options:
        - ніколи
        - ніхто
        - не
      - sentence: Ми розуміємо. → Ми ____ розуміємо.
        answer: не
        options:
        - не
        - ні
        - нічого
      - sentence: Хтось говорить. → ____ не говорить.
        answer: Ніхто
        options:
        - Нічого
        - Ніхто
        - Не
      - sentence: Вони щось бачать. → Вони ____ не бачать.
        answer: нічого
        options:
        - ні
        - нічого
        - ніхто

- find: |
    - id: quiz-double-negation
      type: quiz
      instruction: Оберіть правильне українське речення (Choose the correct Ukrainian
        sentence)
      items:
      - question: I know nothing.
        options:
        - Я нічого не знаю.
        - Я нічого знаю.
        - Я знаю нічого.
        - Я не знаю щось.
        correct: 0
      - question: Nobody works.
        options:
        - Ніхто не працює.
        - Ніхто працює.
        - Не працює хтось.
        - Хтось не працює.
        correct: 0
      - question: We never rest.
        options:
        - Ми ніколи не відпочиваємо.
        - Ми ніколи відпочиваємо.
        - Ми не відпочиваємо ніколи.
        - Ми завжди не відпочиваємо.
        correct: 0
      - question: He understands nothing.
        options:
        - Він нічого не розуміє.
        - Він нічого розуміє.
        - Він розуміє нічого.
        - Він не розуміє ніхто.
        correct: 0
      - question: Nobody speaks.
        options:
        - Ніхто не говорить.
        - Ніхто говорить.
        - Не говорить нічого.
        - Ніхто не знає.
        correct: 0
      - question: Nobody came.
        options:
        - Ніхто не прийшов.
        - Ніхто прийшов.
        - Нічого не прийшов.
        - Хтось не прийшов.
        correct: 0
  replace: |
    - id: quiz-double-negation
      type: quiz
      instruction: Оберіть правильне українське речення (Choose the correct Ukrainian
        sentence)
      items:
      - question: I know nothing.
        options:
        - Я не знаю щось.
        - Я знаю нічого.
        - Я нічого не знаю.
        - Я нічого знаю.
        correct: 2
      - question: Nobody works.
        options:
        - Хтось не працює.
        - Ніхто не працює.
        - Ніхто працює.
        - Не працює хтось.
        correct: 1
      - question: We never rest.
        options:
        - Ми завжди не відпочиваємо.
        - Ми ніколи не відпочиваємо.
        - Ми ніколи відпочиваємо.
        - Ми не відпочиваємо.
        correct: 1
      - question: He understands nothing.
        options:
        - Він нічого розуміє.
        - Він не розуміє ніхто.
        - Він нічого не розуміє.
        - Він розуміє нічого.
        correct: 2
      - question: Nobody speaks.
        options:
        - Ніхто не знає.
        - Не говорить нічого.
        - Ніхто не говорить.
        - Ніхто говорить.
        correct: 2
      - question: Nobody came.
        options:
        - Хтось не прийшов.
        - Нічого не прийшов.
        - Ніхто прийшов.
        - Ніхто не прийшов.
        correct: 3
</fixes>
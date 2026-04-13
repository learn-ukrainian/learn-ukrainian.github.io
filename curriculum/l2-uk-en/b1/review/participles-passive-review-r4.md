## Linguistic Scan
Errors found:
- "сяючий" is flagged as NOT IN VESUM and is an active participle with the suffix "-ючий", which is often discouraged in standard Ukrainian in favor of more natural adjectives or alternative participles. The plan suggests "квітучий".
- Phrasing error: "Крок перший: знайдіть форму інфінітива і дієслово «запросити»." is logically confusing as written.

## Exercise Check
- The `fill-in`, `match-up`, `error-correction`, and `reading` markers match the plan.
- The marker `<!-- INJECT_ACTIVITY: quiz-participle-vs-adjective -->` has an unexpected suffix. The plan hint is just `quiz`.
- The marker `<!-- INJECT_ACTIVITY: essay-response-5 -->` has an unexpected suffix. The plan hint is just `essay-response`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The text misses explicit pedagogical citations mentioned in the plan (e.g., Литвінова). |
| 2. Linguistic accuracy | 8/10 | The word "сяючий" is not in VESUM and is best avoided. The phrasing "знайдіть форму інфінітива і дієслово «запросити»" is logically tangled. |
| 3. Pedagogical quality | 10/10 | Excellent PPP flow. Concepts are introduced with clear examples before the rules are given. |
| 4. Vocabulary coverage | 8/10 | Required words "ношений" and "закручений" are completely missing from the text. |
| 5. Exercise quality | 8/10 | Marker IDs (`quiz-participle-vs-adjective`, `essay-response-5`) do not perfectly match the plan's exact activity_hints types. |
| 6. Engagement & tone | 10/10 | Encouraging and professional teacher tone without corporate gamification. |
| 7. Structural integrity | 8/10 | The module's word count is 3120, which is significantly below the 4000-word target. |
| 8. Cultural accuracy | 10/10 | Great use of culturally relevant contexts like Mariinskyi Palace and vyshyvanka. |
| 9. Dialogue & conversation quality | 10/10 | The dialogue is natural, multi-turn, and effectively demonstrates the grammar in use. |

## Findings

[Dimension 1] [minor]
Location: section "Пасивні дієприкметники: значення"
Issue: Plan references not cited (Литвінова Grade 7 p.88 is mentioned in the plan but absent from the prose).
Fix: Add a brief attribution to the definition.

[Dimension 2] [major]
Location: section "Творення пасивних дієприкметників" — "Крок перший: знайдіть форму інфінітива і дієслово «запросити»."
Issue: Awkward/incorrect phrasing that makes the instruction confusing.
Fix: Change to "Крок перший: візьміть форму інфінітива, наприклад, дієслово «запросити»."

[Dimension 2] [minor]
Location: section "Підсумок" — "the active **сяючий** (shining)"
Issue: The active participle "сяючий" is not in the VESUM dictionary and is often considered a Russianism/calque by stylists. The plan explicitly suggests "квітучий".
Fix: Replace "сяючий" with "квітучий" (and update the English translation).

[Dimension 4] [critical]
Location: section "Творення пасивних дієприкметників"
Issue: Required vocabulary words "ношений" and "закручений" are completely missing from the text.
Fix: Integrate these words into the consonant alternation explanations and the summary table.

[Dimension 5] [major]
Location: Exercise markers `<!-- INJECT_ACTIVITY: quiz-participle-vs-adjective -->` and `<!-- INJECT_ACTIVITY: essay-response-5 -->`
Issue: Marker IDs do not perfectly match the plan's `activity_hints` types, which can cause the pipeline injection to fail.
Fix: Simplify the marker IDs to exactly match the plan types (`quiz` and `essay-response`).

[Dimension 7] [major]
Location: Entire module
Issue: The word count (3120 words) is well below the target budget (4000 words).
Fix: Add an `insert_after` block with an additional paragraph about the usage of passive participles in official-business style to increase depth and word count.

## Verdict: REVISE
The module is fundamentally strong with excellent pedagogy and clear explanations, but it requires revision to fix missing required vocabulary, mismatched exercise markers, a problematic active participle, and to add some volume to get closer to the word count target.

<fixes>
- find: "В українській мові ми називаємо таку ознаку пасивним дієприкметником. Пасивні дієприкметники виражають ознаку предмета за дією, якої він зазнає від іншого виконавця."
  replace: "В українській мові ми називаємо таку ознаку пасивним дієприкметником. Як зазначається у шкільних підручниках (наприклад, О. Литвінової), пасивні дієприкметники виражають ознаку предмета за дією, якої він зазнає від іншого виконавця."
- find: "Крок перший: знайдіть форму інфінітива і дієслово «запросити»."
  replace: "Крок перший: візьміть форму інфінітива, наприклад, дієслово «запросити»."
- find: "the active **сяючий** (shining) and the passive **пофарбований** (painted)."
  replace: "the active **квітучий** (blooming) and the passive **пофарбований** (painted)."
- find: "Звук **[т]** переходить у **[ч]**: слово «сплатити» дає форму «сплачений» (рахунок уже сплачений). Ці чергування є природними"
  replace: "Звук **[т]** переходить у **[ч]**: слово «сплатити» дає форму «сплачений» (рахунок уже сплачений), а «закрутити» стає «закручений» (закручений дріт). Ці чергування є природними"
- find: "Звук **[с]** переходить у **[ш]**: дієслово «скосити» стає дієприкметником «скошений»."
  replace: "Звук **[с]** переходить у **[ш]**: дієслово «скосити» стає дієприкметником «скошений» (так само «носити» утворює «ношений»)."
- find: |
    *   **т → ч**: сплатити → сплачений
    *   **з → ж**: вразити → вражений
    *   **с → ш**: скосити → скошений
  replace: |
    *   **т → ч**: сплатити → сплачений, закрутити → закручений
    *   **з → ж**: вразити → вражений
    *   **с → ш**: скосити → скошений, носити → ношений
- find: "<!-- INJECT_ACTIVITY: quiz-participle-vs-adjective -->"
  replace: "<!-- INJECT_ACTIVITY: quiz -->"
- find: "<!-- INJECT_ACTIVITY: essay-response-5 -->"
  replace: "<!-- INJECT_ACTIVITY: essay-response -->"
- insert_after: "Це робить ваше мовлення грамотним.\n:::"
  content: "\n\nУ науково-навчальному та офіційно-діловому стилях пасивні дієприкметники зустрічаються на кожному кроці. Вони дозволяють формулювати думки чітко, об'єктивно та без зайвих емоцій. Наприклад, у новинах ви часто почуєте фрази на кшталт «прийнятий закон», «схвалене рішення» або «підписаний документ». У таких випадках увага суспільства зосереджена саме на результаті (закон, рішення, документ), а не на тому, хто саме це зробив. Тому вміння правильно утворювати та відмінювати ці форми є критично важливим для розуміння українського інформаційного простору.\n\n> *In scientific-educational and official-business styles, passive participles are found at every step. They allow you to formulate thoughts clearly, objectively, and without unnecessary emotions. For example, in the news, you will often hear phrases like «прийнятий закон» (adopted law), «схвалене рішення» (approved decision), or «підписаний документ» (signed document). In such cases, society's attention is focused precisely on the result (the law, the decision, the document), and not on who exactly did it. Therefore, the ability to correctly form and decline these forms is critically important for understanding the Ukrainian information space.*"
</fixes>
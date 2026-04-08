## Linguistic Scan
Errors found:
- The perfective verb for `відповідати` is spelled incorrectly in the summary table as `відповідісти` instead of `відповісти`. VESUM confirms `відповідісти` does not exist.

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-find-partner -->` - Correctly placed after Section 2. Matches plan.
- `<!-- INJECT_ACTIVITY: fill-in-categorize-by-formation-type -->` - Correctly placed after Section 3. Matches plan.
- `<!-- INJECT_ACTIVITY: match-up-fill-in-the-blanks-with-the-correct-pair -->` - Placed at the end to review the summary. Matches plan.
- `<!-- INJECT_ACTIVITY: fill-in-choose-the-correct-aspect-partner -->` - Placed at the end. Matches plan.
No exercise issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The plan required "готувати / приготувати" as a core example in Section 2, but it was skipped and only included in the table. The plan required "класти / покласти" in Section 4, but it was completely missing from the text. The summary table only lists 15 pairs, but the plan required 20 pairs ("Present a list of the 20 most important aspectual pairs"). |
| 2. Linguistic accuracy | 8/10 | The perfective verb for "відповідати" is spelled as "відповідісти" in the summary table. This is a critical grammatical error. The correct form is "відповісти". All other forms and explanations are accurate. |
| 3. Pedagogical quality | 9/10 | Excellent explanation of the difference between process and result. The "Кафе Птах" mnemonic is taught brilliantly and contextually. Minor deduction for wordy English explanations of prefixes (~90 words of pure theory before providing practical examples of the `по-` prefix). |
| 4. Vocabulary coverage | 8/10 | Required vocabulary words `префікс`, `суфікс`, and `корінь` are only used in Ukrainian within section headings or table formatting. They are never explicitly introduced to the learner as vocabulary terms (e.g., `* **префікс** — prefix`) the way `пара` was. Recommended words are absent. |
| 5. Exercise quality | 10/10 | All 4 activity markers are present, mapped exactly to the plan's requirements, and correctly placed after the relevant grammatical concepts are taught. |
| 6. Engagement & tone | 10/10 | The tone is warm, encouraging, and highly instructional. The shoe store analogy effectively illustrates the concept of aspectual pairs. |
| 7. Structural integrity | 10/10 | Word count is a robust 3027 words (exceeding the 2000 target). Markdown formatting is clean, and all requested sections are present in order. |
| 8. Cultural accuracy | 10/10 | The module appropriately integrates real Ukrainian pedagogical tools (Кафе Птах) and authentic cultural practices (making varenyky with grandmother) into the grammar instruction. |
| 9. Dialogue & conversation quality | 10/10 | The dialogue between the grandmother and granddaughter making varenyky perfectly demonstrates the functional difference between imperfective and perfective commands in real life. |

## Findings
[1. Plan adherence] [major]
Location: Section 2 (Спосіб 1: Додавання префікса)
Issue: The plan required `готувати / приготувати` to be featured as a core example, but it was skipped in the prose and only added to the table.
Fix: Insert `* **Готувати / приготувати** — to cook / to finish cooking.` into the bulleted list of examples.

[1. Plan adherence] [major]
Location: Section 4 (Спосіб 3: Зовсім інші слова) and Summary Table
Issue: The plan explicitly required teaching `класти / покласти` and presenting a summary table of 20 essential aspect pairs. The generated text missed `класти / покласти` entirely and the table only has 15 pairs.
Fix: Add `класти / покласти` to Section 4 and expand the summary table with 5 additional verbs taught in the lesson (пити, вчити, платити, чути, класти) to hit exactly 20 pairs.

[2. Linguistic accuracy] [critical]
Location: Summary Table under "Корінь" (`| | відповід**а**ти | відповід**іс**ти | to answer |`)
Issue: The perfective form of "відповідати" is "відповісти", not "відповідісти". This is a non-existent word.
Fix: Replace `відповід**іс**ти` with `відпов**іс**ти` in the table row.

[4. Vocabulary coverage] [major]
Location: Throughout the module
Issue: The plan's required vocabulary words `префікс`, `суфікс`, and `корінь` are only used in Ukrainian in headings. They must be explicitly introduced as terms.
Fix: Add bulleted definitions for `Префікс`, `Суфікс`, and `Корінь` at the beginning of their respective sections.

## Verdict: REVISE
The module contains a critical linguistic error (`відповідісти` does not exist) and failed to satisfy several explicit plan requirements (missing the 20-pair count, missing the core `готувати` example, and missing explicit vocabulary definitions). The fixes below structurally align the text with the plan and correct the grammatical error.

<fixes>
- find: |
    ## Спосіб 1: Додавання префікса (Method 1: Adding a Prefix)

    In the Ukrainian language,
  replace: |
    ## Спосіб 1: Додавання префікса (Method 1: Adding a Prefix)

    * **Префікс** — prefix.

    In the Ukrainian language,
- find: |
    * **Бачити / побачити** — to see / to catch sight of.
    * **Чути / почути** — to hear / to catch a sound of.
  replace: |
    * **Бачити / побачити** — to see / to catch sight of.
    * **Готувати / приготувати** — to cook / to finish cooking.
    * **Чути / почути** — to hear / to catch a sound of.
- find: |
    ## Спосіб 2: Зміна в корені або суфіксі

    У попередньому розділі
  replace: |
    ## Спосіб 2: Зміна в корені або суфіксі

    * **Корінь** — root.
    * **Суфікс** — suffix.

    У попередньому розділі
- find: |
    Similarly, we have the pair **ловити / піймати** (to catch). You spend time trying to catch something («ловити»), but the moment of capture is instantaneous («піймати»).
  replace: |
    Similarly, we have the pair **ловити / піймати** (to catch). You spend time trying to catch something («ловити»), but the moment of capture is instantaneous («піймати»). Finally, you must memorize the pair for putting or laying things down: **класти / покласти** (to put).
- find: |
    | Форма (Formation) | Недоконаний (Process) | Доконаний (Result) | Переклад (Translation) |
    | :--- | :--- | :--- | :--- |
    | **Префікс** | читати | **про**читати | to read |
    | | писати | **на**писати | to write |
    | | робити | **з**робити | to do |
    | | бачити | **по**бачити | to see |
    | | готувати | **при**готувати | to cook |
    | **Суфікс** | відчин**я**ти | відчин**и**ти | to open |
    | | куп**ува**ти | куп**и**ти | to buy |
    | | виріш**ува**ти | виріш**и**ти | to decide |
    | | запит**ува**ти | запит**а**ти | to ask |
    | **Корінь** | допом**ага**ти | допом**ог**ти | to help |
    | | відповід**а**ти | відповід**іс**ти | to answer |
    | **Інші слова** | брати | взяти | to take |
    | | говорити | сказати | to speak / to say |
    | | ловити | піймати | to catch |
    | | шукати | знайти* | to search / to find |
  replace: |
    | Форма (Formation) | Недоконаний (Process) | Доконаний (Result) | Переклад (Translation) |
    | :--- | :--- | :--- | :--- |
    | **Префікс** | читати | **про**читати | to read |
    | | писати | **на**писати | to write |
    | | робити | **з**робити | to do |
    | | бачити | **по**бачити | to see |
    | | готувати | **при**готувати | to cook |
    | | пити | **ви**пити | to drink |
    | | вчити | **ви**вчити | to study |
    | | платити | **за**платити | to pay |
    | | класти | **по**класти | to put |
    | | чути | **по**чути | to hear |
    | **Суфікс** | відчин**я**ти | відчин**и**ти | to open |
    | | куп**ува**ти | куп**и**ти | to buy |
    | | виріш**ува**ти | виріш**и**ти | to decide |
    | | запит**ува**ти | запит**а**ти | to ask |
    | **Корінь** | допом**ага**ти | допом**ог**ти | to help |
    | | відповід**а**ти | відпов**іс**ти | to answer |
    | **Інші слова** | брати | взяти | to take |
    | | говорити | сказати | to speak / to say |
    | | ловити | піймати | to catch |
    | | шукати | знайти* | to search / to find |
</fixes>

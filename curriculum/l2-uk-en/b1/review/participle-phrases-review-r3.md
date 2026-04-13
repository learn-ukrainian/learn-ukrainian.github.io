## Linguistic Scan
Linguistic errors found:
- **достовірним**: Often considered a Russianism/calque (достоверный). The more natural Ukrainian equivalent in this context is "вірогідним" або "певним".
- **безцінний**: A calque of Russian "бесценный". The correct Ukrainian word for "invaluable" is "неоціненний".
- The examples of Surzhyk and Russianisms (бачивший, заснувший, прочитавша, etc.) are correctly identified as errors to avoid.

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-focus-on-identifying-the-and-the-in-12-sentences -->` (Present after section 1, matches plan)
- `<!-- INJECT_ACTIVITY: match-up-definitions-connect-terms-like-and-with-their-comma-rules-and-examples -->` (Present after section 2, matches plan)
- `<!-- INJECT_ACTIVITY: fill-in-form-insert-the-correctly-inflected-participle-into-a-phrase-based-on-the-noun-provided -->` (Present after section 2, matches plan)
- `<!-- INJECT_ACTIVITY: essay-response-sentences -->` (Present after section 3, matches plan)
- `<!-- INJECT_ACTIVITY: error-correction-punctuation -->` (Present after section 4, matches plan)
- `<!-- INJECT_ACTIVITY: reading-comprehension -->` (Present after section 5, matches plan)
**Issue:** While the activity markers are present and correct, the plan explicitly required an *inline prose passage* with deliberate errors ("Error-correction passage: a text with deliberate punctuation errors in participle phrases. Learners fix all errors and explain the rules."). This is completely missing from the prose.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missing the required "Error-correction passage" in section 5. The text provides the news report and the encyclopedic text, but skipped the text with deliberate punctuation errors. Also, word count targets were left in two H2 headings. |
| 2. Linguistic accuracy | 9/10 | Excellent grammar and morphology overall, but used a couple of words that border on Russianisms or calques, such as "достовірним" instead of "вірогідним", and "безцінний" instead of "неоціненний". |
| 3. Pedagogical quality | 10/10 | Perfect PPP flow. Introduces concepts clearly with realistic examples ("Фільм, знятий в Україні"), explains the "why" behind the grammar, and accurately addresses common Russianisms ("склавший", "прочитавша") to teach linguistic purity. |
| 4. Vocabulary coverage | 9/10 | Most required and recommended vocabulary is included naturally. However, the recommended word "пунктограма" is missing entirely from the prose. |
| 5. Exercise quality | 10/10 | All 6 `activity_hints` have corresponding `<!-- INJECT_ACTIVITY: ... -->` markers placed logically after the relevant sections. |
| 6. Engagement & tone | 10/10 | Natural teacher persona. Encouraging ("Ви щойно уважно прочитали..."), explains nuances without resorting to corporate or overly enthusiastic fluff. |
| 7. Structural integrity | 8/10 | The text length is excellent (4761 words). However, there are LLM generation artifacts in two H2 headings: `(~880 words total)` and `(~770 words total)`. |
| 8. Cultural accuracy | 10/10 | Mentions Zakarpattia floods and Saint Sophia Cathedral (Yaroslav the Wise, Mosaics, Oranta), providing great authentic cultural and historical context. |
| 9. Dialogue & conversation quality | 10/10 | The initial news report dialogue between the journalist and rescuer is highly natural, relevant, and uses the grammar target perfectly in context. |

## Findings

[Structural integrity] [major]
Location: `## Правила відокремлення (~880 words total)`
Issue: H2 heading contains AI generation artifacts (word count targets) instead of just the heading text.
Fix: Remove the word count target from the heading.

[Structural integrity] [major]
Location: `## Трансформація: зворот ↔ підрядне речення (~770 words total)`
Issue: H2 heading contains AI generation artifacts (word count targets) instead of just the heading text.
Fix: Remove the word count target from the heading.

[Plan adherence] [major]
Location: `## Читання та практика`
Issue: The plan explicitly required an "Error-correction passage: a text with deliberate punctuation errors in participle phrases". This passage is missing.
Fix: Insert a short error-correction reading passage with deliberate punctuation errors right before the writing task in the final section.

[Vocabulary coverage] [minor]
Location: `Головне пунктуаційне правило для дієприкметникових зворотів є напрочуд логічним.`
Issue: The recommended vocabulary word `пунктограма` is missing from the prose.
Fix: Insert `(пунктограма)` next to "пунктуаційне правило".

[Linguistic accuracy] [minor]
Location: `...стали достовірним джерелом наших сучасних об'єктивних знань...`
Issue: "Достовірний" is often considered a Russianism or calque (достоверный); "вірогідний" or "певний" is preferred for sources/information.
Fix: Change "достовірним" to "вірогідним".

[Linguistic accuracy] [minor]
Location: `...створили тут справжній безцінний шедевр сакрального мистецтва...`
Issue: "Безцінний" is a calque of "бесценный"; "неоціненний" is the more natural Ukrainian equivalent for something invaluable.
Fix: Change "безцінний" to "неоціненний".

## Verdict: REVISE
While the linguistic explanations and pedagogical flows are phenomenal, the module contains structural artifacts in headings and misses a required text passage from the plan. It requires targeted automated revision.

<fixes>
- find: "## Правила відокремлення (~880 words total)"
  replace: "## Правила відокремлення"
- find: "## Трансформація: зворот ↔ підрядне речення (~770 words total)"
  replace: "## Трансформація: зворот ↔ підрядне речення"
- find: "Головне пунктуаційне правило для дієприкметникових зворотів є напрочуд логічним."
  replace: "Головне пунктуаційне правило (пунктограма) для дієприкметникових зворотів є напрочуд логічним."
- find: "Настав час для вашого власного самостійного та творчого **завдання** *(task)*."
  replace: "Окрім читання правильних текстів, корисно вміти знаходити чужі помилки. Прочитайте цей короткий текст із навмисними пунктуаційними помилками у дієприкметникових зворотах. Спробуйте знайти їх усі та пояснити, чому тут потрібні коми:\n\n> **Текст для виправлення помилок**\n> Туристи стомлені довгою екскурсією нарешті дісталися до музею. Збудована у минулому столітті, будівля вражала своєю архітектурою. Картини написані відомими майстрами висіли на кожній стіні. Ми, вражені цією красою довго не хотіли йти геть.\n\nНастав час для вашого власного самостійного та творчого **завдання** *(task)*."
- find: "стали достовірним джерелом наших сучасних об'єктивних знань"
  replace: "стали вірогідним джерелом наших сучасних об'єктивних знань"
- find: "справжній безцінний шедевр сакрального мистецтва"
  replace: "справжній неоціненний шедевр сакрального мистецтва"
</fixes>
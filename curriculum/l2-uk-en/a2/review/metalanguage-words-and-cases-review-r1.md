## Linguistic Scan
Errors found:
1. Calque: `задати питання` (should be `поставити питання`).
2. Calque: `іде мова` (should be `йдеться`).
3. Calque/Surzhyk: `мають роль` (should be `відіграють роль`).
4. Grammatical reflexivity error / Calque: `у моїй кімнаті` (should be `у своїй кімнаті`).

## Exercise Check
- Marker IDs do not precisely match the standard slugified plan's activity hints (the writer hallucinated descriptive slugs like `sort-a-list-of-24-words-into-five-buckets` instead of directly mapping the plan text).
- There are 5 markers in the text, but the plan only calls for 4 activities. The `match-up` activity is erroneously duplicated at the very end of the module.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The module successfully covers all plan points but hallucinates a 5th duplicate `match-up` activity at the end: `<!-- INJECT_ACTIVITY: match-up-match-ukrainian-grammar-terms-to-their-english-equivalents -->`. |
| 2. Linguistic accuracy | 6/10 | Contains several classic calques: "задати питання" instead of "поставити питання", "мова йде" instead of "йдеться", "мають роль" instead of "відіграють роль", and fails to use the reflexive pronoun in "у моїй кімнаті". |
| 3. Pedagogical quality | 9/10 | Excellent use of primary school textbook excerpts (Вашуленко, Большакова) to build reading confidence. Simplifies complex case questions into actionable, digestible rules. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary terms are naturally integrated into the prose and thoroughly explained. |
| 5. Exercise quality | 7/10 | Mismatched activity marker IDs (e.g. `group-sort-sort-a-list-of-24-words-into-five-buckets`) and an extraneous duplicate marker injected right before the summary. |
| 6. Engagement & tone | 10/10 | The tone is highly encouraging and uses a solid classroom framework ("Уявіть урок української мови. A student is asking...") to contextualize metalanguage naturally. |
| 7. Structural integrity | 10/10 | All H2 headings from the plan are present, no stray formatting artifacts, and word count is extremely robust (3180 words, well over the 2000 target). |
| 8. Cultural accuracy | 10/10 | Authentic Ukrainian mnemonic included ("Нашого Ромчика Дивує Зебра..."). Grammar explanations mirror how Ukrainian children actually learn these concepts. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue between Marko and Anna identifying cases is natural and pedagogically focused. Named speakers are used effectively without feeling overly robotic. |

## Findings
[2. Linguistic accuracy] [Critical]
Location: "Треба задати питання від дієслова." and "Спочатку треба навчитися задати питання... Ми завжди задаємо питання"
Issue: "Задати питання" is a Russian calque (задавать вопрос). The correct Ukrainian form is "поставити питання".
Fix: Replace with "поставити питання" and "ставимо питання".

[2. Linguistic accuracy] [Critical]
Location: "Про який саме відмінок іде мова у правилі? *(Exactly which case is being discussed in the rule?)* Мова йде про знахідний відмінок."
Issue: "Мова йде" is a classic Russian calque (речь идет). The correct Ukrainian form is "йдеться".
Fix: Replace with "ідеться у правилі?" and "Йдеться про знахідний відмінок."

[2. Linguistic accuracy] [Critical]
Location: "Іменники мають дуже важливу роль у реченні."
Issue: "Мати роль" is a mixed calque/Surzhyk derived from Russian "иметь роль/значение". The correct idiom is "відіграють роль".
Fix: Replace "мають" with "відіграють".

[2. Linguistic accuracy] [Minor]
Location: "Чи можу я назвати свою професію та три предмети у моїй кімнаті, використовуючи українські терміни"
Issue: When the subject is "я", natural Ukrainian prefers the reflexive pronoun "свій" over "мій".
Fix: Replace "у моїй кімнаті" with "у своїй кімнаті".

[5. Exercise quality] [Major]
Location: Throughout the prose at `<!-- INJECT_ACTIVITY: ... -->` locations.
Issue: Marker IDs are hallucinated (e.g. `sort-a-list-of-24-words-into-five-buckets`) and do not reliably map to standard slugs from the plan. There is also a 5th duplicate marker.
Fix: Standardize the 4 marker IDs to match the plan focuses and remove the 5th duplicate marker.

## Verdict: REVISE
The module is pedagogically excellent and culturally authentic, but contains four specific linguistic errors (calques like "задати питання", "мають роль", and "мова йде") and hallucinated/duplicate activity markers. These specific structural and linguistic issues must be resolved before publishing.

<fixes>
- find: "Треба задати питання від дієслова."
  replace: "Треба поставити питання від дієслова."
- find: "Спочатку треба навчитися **задати питання** *(to ask a question)*. *(First, you need to learn to ask a question.)* Ми завжди задаємо питання від дієслова до іменника."
  replace: "Спочатку треба навчитися **ставити питання** *(to ask a question)*. *(First, you need to learn to ask a question.)* Ми завжди ставимо питання від дієслова до іменника."
- find: "Про який саме відмінок іде мова у правилі? *(Exactly which case is being discussed in the rule?)* Мова йде про знахідний відмінок. *(The accusative case is being discussed.)*"
  replace: "Про який саме відмінок ідеться у правилі? *(Exactly which case is being discussed in the rule?)* Йдеться про знахідний відмінок. *(The accusative case is being discussed.)*"
- find: "Іменники мають дуже важливу роль у реченні."
  replace: "Іменники відіграють дуже важливу роль у реченні."
- find: "у моїй кімнаті, використовуючи українські терміни"
  replace: "у своїй кімнаті, використовуючи українські терміни"
- find: "<!-- INJECT_ACTIVITY: match-up-match-ukrainian-grammar-terms-etc-to-english-equivalents -->"
  replace: "<!-- INJECT_ACTIVITY: match-up-match-ukrainian-grammar-terms-to-their-english-equivalents -->"
- find: "<!-- INJECT_ACTIVITY: group-sort-sort-a-list-of-24-words-into-five-buckets -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort-sort-words-into-parts-of-speech-imennyk-prykmetnyk-diieslovo-etc -->"
- find: "<!-- INJECT_ACTIVITY: fill-in-complete-the-case-name-and-its-question-pair-e-g -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in-complete-case-questions-rodovyi -->"
- find: "<!-- INJECT_ACTIVITY: quiz-identify-the-part-of-speech-and-case-of-underlined-words-in-simple-sentences -->"
  replace: "<!-- INJECT_ACTIVITY: quiz-identify-the-part-of-speech-of-underlined-words-in-ukrainian-sentences -->"
- find: "Ви знаєте всі необхідні терміни. *(You know all the necessary terms.)*\n\n<!-- INJECT_ACTIVITY: match-up-match-ukrainian-grammar-terms-to-their-english-equivalents -->\n\n## Підсумок"
  replace: "Ви знаєте всі необхідні терміни. *(You know all the necessary terms.)*\n\n## Підсумок"
</fixes>

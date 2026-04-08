## Linguistic Scan
Errors found. The text contains a few Russian calques/Russianisms:
- **відкрив вікно** (Calque from Russian "открыть окно"). The correct verb for windows/doors is "відчиняти".
- **закрив книгу** (Calque from Russian "закрыть книгу"). The correct verb for books is "згортати" (або "загортати").
- **чисту правду** (Russianism "чистая правда"). The idiomatic Ukrainian expression is "щира правда".

All other text, including phonetic rules (Кафе «Птах») and aspect pairings, is linguistically accurate. No Surzhyk or paronym errors were found. The VESUM verification is clean.

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-aspect-id -->` is correctly placed after the introductory theory section "Два питання — два види".
- `<!-- INJECT_ACTIVITY: match-signal-words -->` is correctly placed after "Коли вживати недоконаний вид", testing the signal words just introduced.
- `<!-- INJECT_ACTIVITY: fill-in-aspect-choice -->` is correctly placed after "Коли вживати доконаний вид".
- `<!-- INJECT_ACTIVITY: error-correction-aspect -->` is correctly placed after "Практика вибору виду", matching the error correction focus in the plan.
All 4 markers match the plan's `activity_hints` exactly and are spread evenly throughout the module.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | The text faithfully executes every plan point, including the specific signal words ("довго", "раптом") and the overarching concept of "camera rolling vs taking a photo" ("shooting a video and taking a photo"). The decision flowchart is successfully integrated into the summary. |
| 2. Linguistic accuracy | 8/10 | Generally excellent, but contains three notable calques from Russian: "відкрив вікно" (instead of відчинив), "закрив книгу" (instead of згорнув), and "чисту правду" (instead of щиру). |
| 3. Pedagogical quality | 10/10 | Exceptional pedagogical flow. The use of contrastive examples in the past tense ("Я робив це завдання дві години, але не зробив його") perfectly illustrates the concept to an English speaker. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary items from the plan are integrated naturally into the prose (e.g., минулий час, робити/зробити, раптом, щодня). |
| 5. Exercise quality | 10/10 | The exercise markers correspond exactly to the plan's activity hints and are logically placed immediately after the relevant pedagogical explanations. |
| 6. Engagement & tone | 10/10 | Very natural and encouraging teacher tone. The analogies used to explain the aspectual differences are vivid and directly helpful for learners. |
| 7. Structural integrity | 10/10 | All H2 headings match the plan exactly. The word count (2831 words) successfully meets and exceeds the 2000-word target without feeling bloated. |
| 8. Cultural accuracy | 10/10 | Factually correct presentation of how Ukrainian morphology handles verbs. Decolonized approach that explains Ukrainian on its own terms. |
| 9. Dialogue & conversation quality | 10/10 | The opening dialogue between Olya and Taras is highly functional and natural, contrasting process ("готував обід дві години") with result ("швидко приготувала... вечерю"). |

## Findings
[2. Linguistic accuracy] [critical]
Location: Section "Коли вживати доконаний вид", paragraph about sequence of actions: "Він прийшов (came) додому, відкрив (opened) вікно і сів (sat down) за стіл."
Issue: "відкрити вікно" is a calque from Russian "открыть окно". In Ukrainian, the correct verb for opening doors and windows is "відчиняти" (verified via `mcp_rag_query_r2u`).
Fix: Change "відкрив" to "відчинив".

[2. Linguistic accuracy] [critical]
Location: Section "Практика вибору виду", the sentences: "Я швидко прочитав (finished reading) її і закрив (closed) книгу." AND "Він побачив кінець, прочитав текст і закрив книгу."
Issue: "закрити книгу" is a calque from Russian "закрыть книгу". In Ukrainian, books are closed using the verb "згортати" (verified via `mcp_rag_query_r2u`).
Fix: Change both instances of "закрив" to "згорнув".

[2. Linguistic accuracy] [major]
Location: Section "Практика вибору виду", the sentence: "Ми можемо радісно сказати: «Він нарешті сказав (said) усім чисту правду»."
Issue: "чиста правда" is a literal translation/Russianism of "чистая правда". The idiomatic Ukrainian expression is "щира правда" (verified via `mcp_rag_query_r2u`).
Fix: Change "чисту правду" to "щиру правду".

## Verdict: REVISE
The module is structurally and pedagogically outstanding, fulfilling the plan with excellent examples and natural flow. However, it contains a few documented Russian calques ("відкрив вікно", "закрив книгу", "чисту правду") that are classified as critical/major linguistic errors. These must be corrected before the module can be published. 

<fixes>
- find: "**відкрив** *(opened)* вікно"
  replace: "**відчинив** *(opened)* вікно"
- find: "її і **закрив** *(closed)* книгу."
  replace: "її і **згорнув** *(closed)* книгу."
- find: "прочитав текст і закрив книгу."
  replace: "прочитав текст і згорнув книгу."
- find: "усім чисту правду»."
  replace: "усім щиру правду»."
</fixes>

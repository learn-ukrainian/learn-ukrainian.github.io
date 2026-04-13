## Linguistic Scan
Linguistic scan revealed several Russianisms and calques used as primary teaching examples. Specifically:
- **"читаюча дівчина"** and **"сяючі очі"** (Section 1) are presented as "classic examples" of active present participles in contrast with gerunds. However, active present participles on **-учий/-ячий** are considered unnatural/Russicisms in modern Ukrainian (Antonenko-Davydovych, *Як ми говоримо*). VESUM correctly flags `читаюча` and `сяючі` as not found. These should be replaced with natural Ukrainian constructions ("дівчина, що читає", "сяйливі очі").
- **"включаючи"** (Section 5) is listed as a lexicalized form. While found in dictionaries (tagged as `advp:imperf` in VESUM), many linguists (e.g., Avramenko, Ponomariv) recommend avoiding it in favor of **"зокрема"**, **"серед них"**, or **"враховуючи"** as it is often a calque of Russian *включая*.
- **"свіжі новини"** (Sections 1, 3) is a literal translation of *свежие новости*. Standard Ukrainian prefers **"останні новини"** (confirmed by `r2u` results).

No other linguistic errors (Surzhyk, orthography, etc.) found.

## Exercise Check
The module contains 6 activity markers, which matches the plan:
1. `reading-identifying-gerunds` (After Section 1): Appropriate for identifying gerunds vs. participles.
2. `fill-in-gerund-formation` (After Section 2): Appropriate for testing the formation algorithm.
3. `match-gerund-conjugations` (After Section 2): Appropriate for distinguishing I and II conjugation suffixes.
4. `essay-gerund-situations` (After Section 3): Appropriate for testing different types of adverbial modifiers (manner, time, etc.).
5. `error-correction` (After Section 4): Appropriate for the "dangling gerund" and aspect mistakes.
6. `quiz` (After Section 6): Appropriate for final synthesis.

Logic and placement are correct.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | Covers all 7 sections. Follows the morning jog situation, suffix rules, logical subject, styles, and reading passage. Cites Lytvynova, Zabolotnyi, and Avramenko naturally. |
| 2. Linguistic accuracy | 7/10 | Critical issue: teaching Russicisms (**"читаюча дівчина"**, **"сяючі очі"**) as "classic" participle examples without noting their non-standard status. Use of **"свіжі новини"** instead of **"останні новини"**. |
| 3. Pedagogical quality | 10/10 | Excellent PPP flow. Clear distinction between -учи/-ючи and -ачи/-ячи. Deep explanation of the logical subject rule with clear "wrong" examples. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary (дієприслівник, недоконаний вид, читаючи, слухаючи, пишучи, говорячи, обставина, додаткова дія, одночасність, логічний підмет) and recommended vocabulary (усміхаючись, дивлячись, стоячи, біжучи, сидячи, хвилюючись) are integrated. |
| 5. Exercise quality | 10/10 | 6 markers spread evenly. Types (fill-in, match, error-correction, essay) match the plan exactly. |
| 6. Engagement & tone | 10/10 | Encouraging teacher tone ("Уявіть типовий літній ранок...", "Розгляньмо кожен із цих..."). Natural multi-turn dialogue. |
| 7. Structural integrity | 10/10 | Word count (4637) is well above the 4000 target. H2 headings match the plan exactly. |
| 8. Cultural accuracy | 10/10 | References Kyiv (Embankment, Dnipro Bridge), the Carpathians (Hoverla, Smereky), and decolonized pedagogical terms. |
| 9. Dialogue & conversation quality | 10/10 | The opening dialogue between "Бігун" and "Друг" is natural and effectively models the grammar point in a real-life situation. |

## Findings
[LINGUISTIC] [SEVERITY: critical]
Location: Section 1 (Paragraphs 11-12)
Issue: Using **"читаюча дівчина"** and **"сяючі очі"** as model participles. These are Russicisms.
Fix: Replace with natural Ukrainian constructions and explain that active present participles are rarely used in standard Ukrainian.

[LINGUISTIC] [SEVERITY: major]
Location: Section 1, 3
Issue: **"свіжі новини"** is a calque of *свежие новости*.
Fix: Replace with **"останні новини"**.

[LINGUISTIC] [SEVERITY: minor]
Location: Section 5
Issue: **"включаючи"** is a frequent calque, better to use **"зокрема"**.
Fix: Replace example with a more natural Ukrainian phrasing.

## Verdict: REVISE
The module is pedagogically strong and well-structured, but it inadvertently teaches several Russicisms/calques (**"читаюча дівчина"**, **"сяючі очі"**, **"свіжі новини"**) as standard forms. Given the B1 level and decolonized mission, these must be corrected before publication.

<fixes>
- find: "я завжди уважно слухаю свіжі новини"
  replace: "я завжди уважно слухаю останні новини"
- find: "я не помічаю втоми. А **дихаючи** *(breathing)* свіжим ранковим повітрям"
  replace: "я не помічаю втоми. А **дихаючи** *(breathing)* чистим ранковим повітрям"
- find: "Розгляньмо приклад: «**читаюча дівчина**» *(the reading girl)*. Тут слово «читаюча» описує саму дівчину і змінюється разом з іменником."
  replace: "Розгляньмо приклад: «**усміхнена дівчина**» *(the smiling girl)*. Тут слово «усміхнена» описує саму дівчину і змінюється разом з іменником. Варто зауважити, що в українській мові активні дієприкметники теперішнього часу (як-от «читаюча») вживаються вкрай рідко; зазвичай ми використовуємо конструкцію «дівчина, що читає»."
- find: "ми скажемо «**сяючі очі**» *(shining eyes)*. Це дієприкметник, який узгоджується з іменником у називному відмінку множини. Але якщо ми описуємо дію людини, ми скажемо: «Вона йшла, **сяючи** *(shining / while shining)* від щастя»."
  replace: "ми скажемо «**сяйливі очі**» *(shining eyes)*. Це прикметник, який описує ознаку. Але якщо ми описуємо дію людини, ми скажемо: «Вона йшла, **сяючи** *(shining / while shining)* від щастя». Тут незмінюваний дієприслівник пояснює, як саме вона йшла."
- find: "я завжди уважно слухаю свіжі новини"
  replace: "я завжди уважно слухаю останні новини"
- find: "«**Аналізуючи** *(while analyzing)* ці статистичні дані, науковці помітили дуже цікаву тенденцію»."
  replace: "«**Аналізуючи** *(while analyzing)* ці дані, дослідники помітили цікаву тенденцію»."
- find: "Квитки на концерт купили всі, **включаючи** *(including)* мене»."
  replace: "Квитки на концерт купили всі, **зокрема й** *(including)* я»."
- find: "я завжди уважно слухаю останні новини"
  replace: "я завжди уважно слухаю останні новини"
- find: "Готуючи сніданок, я слухаю ранкові новини."
  replace: "Готуючи сніданок, я слухаю останні новини."
</fixes>
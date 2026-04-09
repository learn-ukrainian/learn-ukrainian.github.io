## Linguistic Scan
Found errors:
- "на найбли कूलзу зупинку" — Critical artifact; foreign characters (Bengali/Hindi) injected into the text instead of a Ukrainian word.
- "ти їзздиш" — Typo in the conjugation paradigm.
- "знаходиться зовсім близько" — Calque of Russian "находится"; should be "перебуває" when describing physical presence.
- "приймаєте рішення" — Calque of Russian "принимать решение"; should be "вирішуєте" or "ухвалюєте рішення".
- "відправиться" — Russicism for departing transport; normative Ukrainian uses "вирушить".
- "парковці" — Colloquialism/Russicism; should be "автостоянці".

## Exercise Check
The generated text contains 13 exercise placeholders, whereas the plan only outlines 6 in `activity_hints`. While all requested activity types are present (quiz, fill-in, match-up, error-correction, group-sort, free-write), the excessive fragmentation of markers clutters the file structure. However, the inline reading comprehension questions and dialogues are well-formed and placed correctly after their respective theory blocks. 

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The text missed the `dialogue_situations` meta-requirement for an Oral Exam setting with an Examiner and Student, writing only the train station dialogue. It also missed the explicit contrast `літак летить (literal)` requested in Block 5. |
| 2. Linguistic accuracy | 7/10 | Contains a critical gibberish artifact ("найбли कूलзу"), a conjugation typo ("їзздиш"), and several common calques/Russicisms ("приймаєте рішення", "знаходиться", "відправиться"). |
| 3. Pedagogical quality | 10/10 | Excellent pedagogical flow. It breaks down the prefixes into logical groups (arrival vs departure, crossing vs passing) and clearly explains the difficult rules for case government. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary words (контрольна робота, різноспрямований, маршрут, самооцінка, etc.) are present and naturally integrated. |
| 5. Exercise quality | 9/10 | Over-fragmented with 13 markers instead of the 6 planned, but the markers logically follow the taught sections. |
| 6. Engagement & tone | 10/10 | Very supportive, natural teacher persona. Uses great examples to make spatial rules concrete. |
| 7. Structural integrity | 9/10 | Meets the 4000-word target perfectly (4305). However, a broken unicode string artifact slipped into the prose. |
| 8. Cultural accuracy | 10/10 | Accurate geography and authentic examples from Ukrainian realia (Lviv, Carpathians, Yaremche, Boryspil). |
| 9. Dialogue & conversation quality | 9/10 | The train station dialogue is natural and useful, but the planned Oral Exam dialogue was completely absent. |

## Findings
[2. Linguistic accuracy] [Critical]
Location: `[3. __________] на найбли कूलзу зупинку.`
Issue: Gibberish/foreign character artifact instead of a Ukrainian word.
Fix: Replace `на найбли कूलзу зупинку.` with `на найближчу зупинку.`

[2. Linguistic accuracy] [Critical]
Location: `«Їздити»: я їжджу, ти їзздиш, вона їздить,`
Issue: Typo in the conjugation paradigm for "їздити".
Fix: Replace `ти їзздиш,` with `ти їздиш,`

[2. Linguistic accuracy] [Major]
Location: `Якщо ж ви хочете підкреслити, що хтось знаходиться зовсім близько,`
Issue: Use of "знаходитися" to indicate physical presence is a calque of Russian "находиться".
Fix: Replace `що хтось знаходиться зовсім близько,` with `що хтось перебуває зовсім близько,`

[2. Linguistic accuracy] [Major]
Location: `Ви сідаєте в таксі і приймаєте рішення швидко поїхати на вокзал`
Issue: "приймати рішення" is a direct calque from Russian "принимать решение".
Fix: Replace `і приймаєте рішення швидко поїхати на вокзал` with `і вирішуєте швидко поїхати на вокзал`

[2. Linguistic accuracy] [Major]
Location: `Зрозумів. А о котрій годині він відправиться (will depart) далі?`
Issue: "відправлятися" is a Russicism when used for departing transport. Normative Ukrainian uses "вирушати".
Fix: Replace `о котрій годині він відправиться (will depart) далі?` with `о котрій годині він вирушить (will depart) далі?`

[2. Linguistic accuracy] [Minor]
Location: `Ми залишили нашу машину на безпечній парковці навпроти готелю`
Issue: "парковка" is colloquial; the standard term is "автостоянка".
Fix: Replace `на безпечній парковці навпроти готелю` with `на безпечній автостоянці навпроти готелю`

[1. Plan adherence] [Major]
Location: `Це був ідеальний маршрут для нашої відпустки, який я запам'ятаю назавжди!` (End of Block 6 narrative).
Issue: The generator followed the `content_outline` dialogue but ignored the explicit `dialogue_situations` meta requirement for an "Oral exam — the student describes a journey" setting.
Fix: Inject a short oral exam exchange by adding it to the end of the paragraph: `який я запам'ятаю назавжди!\n\nА тепер уявіть, що ви складаєте усний іспит. Вам потрібно описати свій щоденний маршрут, використовуючи всі групи префіксів.\n\n> — **Екзаменатор:** Розкажіть, як ви провели вчорашній день?\n> — **Студент:** Я вийшов з дому, пішов до зупинки, доїхав до вокзалу, приїхав до Львова, обійшов центр і зайшов у кав'ярню.`

[1. Plan adherence] [Minor]
Location: `і не помічаєте, як швидко минають години, ідеальною фразою буде «час летить (time flies)».`
Issue: The content outline explicitly requests contrasting `Час летить (figurative)` with `Літак летить (literal)`, but the literal counter-example is missing from the explanation block.
Fix: Replace `швидко минають години, ідеальною фразою буде «час летить (time flies)».` with `швидко минають години, ідеальною фразою буде «час летить (time flies)». Це переносне значення, адже в прямому значенні ми кажемо «літак летить (literal)».`

## Verdict: REVISE
The module covers the massive topic of motion verbs exceptionally well, delivering high-quality pedagogical explanations and a very positive tone. However, the presence of a critical character artifact ("найбли कूलзу"), a conjugation typo ("їзздиш"), several calques ("приймати рішення", "знаходиться"), and a missing planned dialogue sequence require a revision before publishing.

<fixes>
- find: "на найбли कूलзу зупинку."
  replace: "на найближчу зупинку."
- find: "ти їзздиш,"
  replace: "ти їздиш,"
- find: "що хтось знаходиться зовсім близько,"
  replace: "що хтось перебуває зовсім близько,"
- find: "і приймаєте рішення швидко поїхати на вокзал"
  replace: "і вирішуєте швидко поїхати на вокзал"
- find: "о котрій годині він відправиться (will depart) далі?"
  replace: "о котрій годині він вирушить (will depart) далі?"
- find: "на безпечній парковці навпроти готелю"
  replace: "на безпечній автостоянці навпроти готелю"
- find: "який я запам'ятаю назавжди!"
  replace: "який я запам'ятаю назавжди!\n\nА тепер уявіть, що ви складаєте усний іспит. Вам потрібно описати свій щоденний маршрут, використовуючи всі групи префіксів.\n\n> — **Екзаменатор:** Розкажіть, як ви провели вчорашній день?\n> — **Студент:** Я вийшов з дому, пішов до зупинки, доїхав до вокзалу, приїхав до Львова, обійшов центр і зайшов у кав'ярню."
- find: "швидко минають години, ідеальною фразою буде «час летить (time flies)»."
  replace: "швидко минають години, ідеальною фразою буде «час летить (time flies)». Це переносне значення, адже в прямому значенні ми кажемо «літак летить (literal)»."
</fixes>

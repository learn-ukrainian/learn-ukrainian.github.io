## Linguistic Scan
Found 2 linguistic errors:
- "Давайте" + verb (4 instances: "Давайте подивимося", "Давайте спочатку подивимося", "Давайте попрактикуємо") is a common calque from the Russian imperative "давайте посмотрим". The proper Ukrainian form is the synthetic imperative ("Подивімося", "Попрактикуймо").
- "Значить" used as an introductory word ("Значить, це друга група") is colloquial/Surzhyk; the correct literary form is "Отже".

## Exercise Check
The plan provided 4 `activity_hints`. However, the writer injected 6 `<!-- INJECT_ACTIVITY: {id} -->` markers. The first two markers (`fill-in-ordinals` and `match-up-numeral-meanings`) are extra, do not map to the plan, and will result in either dangling markers or duplicate/invalid activities in the downstream pipeline.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The text misses recommended vocabulary "обидва/обидві" and "десяток". The reading practice section completely omits the required "ages of historical figures" and "distances between cities", focusing solely on dates. The generated dialogue is a generic market exchange that ignored the specific "school sports day" setting and mandated phrases ("Перша команда", "Другий забіг", "Одного м'яча не вистачає"). |
| 2. Linguistic accuracy | 8/10 | Good overall syntax and declension tables, but contains Russian calques for imperative verbs ("Давайте подивимося", "Давайте попрактикуємо") and Surzhyk introductory words ("Значить" instead of "Отже"). |
| 3. Pedagogical quality | 9/10 | Excellent grammar progression. The explanation of the "1-2-5" rule is clear and logical. However, modeling the "Давайте" imperative teaches learners bad habits. |
| 4. Vocabulary coverage | 8/10 | All required vocabulary is used in clear context, but recommended words "обидва/обидві" and "десяток" are omitted entirely. |
| 5. Exercise quality | 8/10 | The writer injected 6 markers instead of the 4 requested by the plan, disrupting the pipeline's 1:1 mapping for `activity_hints`. |
| 6. Engagement & tone | 9/10 | The tone is warm and encouraging ("Це дуже красива граматична особливість"). |
| 7. Structural integrity | 10/10 | All required H2 sections are present in order. Word count is reported as 2528, safely above the 2000 target. |
| 8. Cultural accuracy | 10/10 | Appropriately references Ukrainian holidays (Independence Day, Constitution Day) and acknowledges the modern December 25th date for Christmas. |
| 9. Dialogue & conversation quality | 7/10 | The generated dialogue missed the planned motivational context ("Organizing a school sports day"), resulting in a generic transaction that didn't showcase the required ordinal expressions. |

## Findings
[1. Plan adherence] [critical]
Location: `## Скільки чого? Числівник + іменник (How Many? Numeral + Noun Agreement)`
Issue: The plan explicitly requires teaching "обидва/обидві" alongside "два/дві" and including the word "десяток". Neither is present in the text.
Fix: Add "обидва/обидві" to the paragraph explaining "два/дві", and "десяток" to the paragraph discussing "кілька/багато".

[1. Plan adherence] [critical]
Location: `## Числа навколо нас (Numbers Around Us)`
Issue: The dialogue missed the specific "school sports day" setting and phrases ("Перша команда", "Другий забіг", "Одного м'яча не вистачає", "П'ять медалей").
Fix: Rewrite the dialogue to incorporate both the market buying aspect and the sports day phrasing requested by the plan.

[1. Plan adherence] [critical]
Location: `## Числа навколо нас (Numbers Around Us)` (paragraph about reading practice)
Issue: The reading practice paragraph omits "ages of historical figures" and "distances between cities", focusing only on dates.
Fix: Append sentences about distances (e.g., Kyiv to Lviv) and ages of historical figures (e.g., Shevchenko, Franko).

[2. Linguistic accuracy] [critical]
Location: Multiple locations ("Давайте подивимося", "Давайте спочатку подивимося", "Давайте попрактикуємо")
Issue: "Давайте" + verb is a Russian calque for the imperative mood. The correct Ukrainian form is the synthetic imperative ("Подивімося", "Попрактикуймо").
Fix: Replace all instances with the proper synthetic imperative forms.

[2. Linguistic accuracy] [critical]
Location: `## Скільки чого? Числівник + іменник`
Issue: The word "Значить" is used as an introductory word ("Значить, це друга група"). This is colloquial/Surzhyk; the correct written form is "Отже".
Fix: Replace "Значить" with "Отже".

[5. Exercise quality] [major]
Location: End of `## Порядкові числівники` and `## Один/одна/одне у відмінках`
Issue: Extra `<!-- INJECT_ACTIVITY: ... -->` markers were injected beyond the 4 requested by the plan, breaking the pipeline's 1:1 injection mapping.
Fix: Remove the two excess markers (`fill-in-ordinals` and `match-up-numeral-meanings`).

## Verdict: REVISE
The module covers a complex grammar topic excellently, but has critical issues with plan adherence (missing required dialogue contexts, missing examples, missing recommended vocabulary) and linguistic accuracy (Russian calques like "Давайте" and "Значить"). Applying the deterministic fixes below will resolve all issues.

<fixes>
- find: "Давайте подивимося, як змінюється числівник"
  replace: "Подивімося, як змінюється числівник"
- find: "Давайте спочатку подивимося на чоловічий та середній рід (masculine and neuter)."
  replace: "Подивімося спочатку на чоловічий та середній рід (masculine and neuter)."
- find: "Давайте подивимося на другу групу уважніше."
  replace: "Подивімося на другу групу уважніше."
- find: "Давайте попрактикуємо читання дат."
  replace: "Попрактикуймо читання дат."
- find: "Значить, це друга група."
  replace: "Отже, це друга група."
- find: "Ми кажемо **дві сестри** (two sisters) або **дві стіни** (two walls). Це дуже красива граматична особливість."
  replace: "Ми кажемо **дві сестри** (two sisters) або **дві стіни** (two walls). Так само працює слово **обидва** (both). Ми кажемо **обидва брати** (both brothers), але **обидві сестри** (both sisters). Це дуже красива граматична особливість."
- find: "Або ми скажемо **кілька днів** (several days) та **декілька друзів** (several friends). Коли ми йдемо на базар чи в магазин, ці слова стають нашими найкращими помічниками."
  replace: "Або ми скажемо **кілька днів** (several days) та **декілька друзів** (several friends). Також ми часто використовуємо слово **десяток** (a ten / a dozen), наприклад, **десяток яєць** (ten eggs). Коли ми йдемо на базар чи в магазин, ці слова стають нашими найкращими помічниками."
- find: "Уявіть ситуацію на ринку. Вчитель та учні організовують спортивне свято і купують інвентар.\n> — **Вчитель:** Добрий день! Скільки **коштують** *(cost)* ці **три м'ячі** *(three balls)*?\n> — **Продавець:** Доброго дня! Вони коштують **п'ятсот гривень** *(five hundred hryvnias)*.\n> — **Учень:** Це дуже дорого! А скільки коштує **один м'яч** *(one ball)*?\n> — **Продавець:** Один м'яч коштує **двісті гривень** *(two hundred hryvnias)*. Якщо берете три, буде дешевше.\n> — **Вчитель:** Добре. Дайте, будь ласка, **п'ять м'ячів** *(five balls)* і **два насоси** *(two pumps)*.\n> — **Продавець:** З вас **тисяча двісті гривень** *(one thousand two hundred hryvnias)*.\n> — **Вчитель:** Ось, тримайте. Дякую!\n\nЗверніть увагу, як змінюється слово «м'яч». Ми кажемо «один м'яч» у Називному відмінку однини. Потім ми кажемо «три м'ячі» у Називному відмінку множини. Нарешті, ми кажемо «п'ять м'ячів» у Родовому відмінку множини. Слово «гривня» також змінюється: «двісті гривень», «п'ятсот гривень». Це правило узгодження в дії."
  replace: "Уявіть ситуацію на спортивному ринку. Вчитель фізкультури та учні купують інвентар і планують свято.\n> — **Вчитель фізкультури:** Добрий день! Скільки **коштують** *(cost)* ці м'ячі? Нам **одного м'яча** *(one ball)* не вистачає для гри.\n> — **Продавець:** Доброго дня! Один коштує **двісті гривень** *(two hundred hryvnias)*. А якщо візьмете **три кілограми** *(three kilograms)* крейди для поля, зроблю знижку.\n> — **Учень:** А ще нам потрібні призи! У нас **перша команда** *(first team)* — це десять учнів.\n> — **Вчитель фізкультури:** Добре, дайте, будь ласка, ще **п'ять медалей** *(five medals)*. **Другий забіг** *(second race)* вже о десятій, треба поспішати.\n> — **Продавець:** З вас **тисяча двісті гривень** *(one thousand two hundred hryvnias)*.\n> — **Вчитель фізкультури:** Ось, тримайте. Дякую!\n\nЗверніть увагу на фрази: «одного м'яча» (Родовий відмінок), «три кілограми» (Називний відмінок множини), «перша команда» та «другий забіг» (узгодження порядкових числівників), «п'ять медалей» (Родовий відмінок множини після «п'ять»). Це правило узгодження в дії."
- find: "Зверніть увагу, що всі дати закінчуються на «-го»: першого, двадцять п'ятого. Це вказує на день, коли щось відбувається. Назва місяця також стоїть у Родовому відмінку: серпня, червня, січня, грудня."
  replace: "Зверніть увагу, що всі дати закінчуються на «-го»: першого, двадцять п'ятого. Це вказує на день, коли щось відбувається. Назва місяця також стоїть у Родовому відмінку: серпня, червня, січня, грудня. Також у текстах ви часто зустрінете відстані та вік. Наприклад: «Відстань між Києвом та Львовом — близько п'ятисот кілометрів (about five hundred kilometers)». Або про історичних осіб: «Тарас Шевченко прожив сорок сім років (forty-seven years), а Іван Франко — сорок один рік (forty-one years)»."
- find: "Воно допоможе вам правильно планувати зустрічі.\n\n<!-- INJECT_ACTIVITY: fill-in-ordinals -->"
  replace: "Воно допоможе вам правильно планувати зустрічі."
- find: "Ви будете чути ці фрази постійно.\n\n<!-- INJECT_ACTIVITY: match-up-numeral-meanings -->"
  replace: "Ви будете чути ці фрази постійно."
</fixes>

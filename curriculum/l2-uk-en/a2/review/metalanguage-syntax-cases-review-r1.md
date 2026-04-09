## Linguistic Scan
- "Давайте" is used 6 times as an imperative particle (a calque from the Russian "давайте + глагол" construction).
- "Задаємо логічне питання" is a calque from the Russian "задавать вопрос" (the correct Ukrainian phrase is "ставимо питання").
- All other linguistic claims, terminology, and phonetics are factually correct.

## Exercise Check
- `<!-- INJECT_ACTIVITY: mark-the-words-combinations -->` was hallucinated by the writer and does not correspond to the plan's `activity_hints`.
- The plan required a `fill-in` activity for determining cases, which is MISSING from the "Відмінки" section.
- The remaining markers correctly match the `activity_hints` plan points.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The text misses the "Complete metalanguage glossary" in the "Підсумок" section. It omitted "сполучні слова" from the "Складне речення" section. It also omitted the required examples ("Тарасе! Маріє! Друже!") and abbreviations (Н.в., Р.в.) for cases in the "Відмінки" section. |
| 2. Linguistic accuracy | 7/10 | Pervasive use of Russian calques: "Давайте" + verb (6 instances) and "Задаємо питання". |
| 3. Pedagogical quality | 9/10 | Strong PPP flow and excellent analogies (commander/subordinate for словосполучення). Good use of visual mnemonics. |
| 4. Vocabulary coverage | 9/10 | All required and recommended vocabulary items were included naturally, except for "сполучне слово" which was skipped. |
| 5. Exercise quality | 8/10 | Hallucinated a `mark-the-words-combinations` exercise and forgot the required `fill-in` activity for determining cases. |
| 6. Engagement & tone | 10/10 | Very supportive, natural teacher tone. Good analogies (building a house, energetic centers) that do not feel gamified. |
| 7. Structural integrity | 10/10 | Clean markdown, high word count, and well-paced sections. All H2 headings perfectly match the plan. |
| 8. Cultural accuracy | 10/10 | Accurately reflects Ukrainian Grade 5 pedagogical approaches and syntactic traditions (e.g., underline styles, structural parsing). |
| 9. Dialogue & conversation quality | 5/10 | The dialogue completely ignored the plan's strict requirement to use "підмет, присудок, додаток, означення, обставина", and to parse a newspaper sentence. Instead, it only redundantly repeated the explanation of "словосполучення". |

## Findings

[1. Plan adherence] [Major]
Location: Section "Складне речення", paragraph on subordinating conjunctions ("Третя важлива група — це підрядні сполучники...")
Issue: The plan explicitly requires teaching "Сполучні слова: хто, що, який, чий, котрий, де, коли, як, куди." The generated text omits this.
Fix: Add the connective words to the paragraph on subordinating conjunctions.

[1. Plan adherence] [Major]
Location: Section "Відмінки: система і питання"
Issue: The plan requires examples for the Vocative case ("Тарасе! Маріє! Друже!") and abbreviations for cases (Н.в., Р.в., etc.). The text misses both.
Fix: Add the abbreviations directly into the case descriptions and append the examples to the Vocative case.

[1. Plan adherence] [Major]
Location: Section "Підсумок: ваш синтаксичний словник"
Issue: The plan explicitly requires a "Complete metalanguage glossary — all terms from this module collected". The text just provides a paragraph summary instead of listing the words.
Fix: Add the glossary list immediately before the self-check questions.

[2. Linguistic accuracy] [Major]
Location: Throughout the module ("Давайте дуже детально познайомимося...", "Давайте спочатку зробимо...", etc.)
Issue: Using "давайте + дієслово" is a widespread Russian calque. Synthetic imperatives ("познайомимося", "зробімо") should be used instead.
Fix: Replace all "Давайте" constructions with proper Ukrainian imperatives.

[2. Linguistic accuracy] [Major]
Location: Section "Граматична основа: підмет і присудок" ("Задаємо логічне питання: хто або що фізично виконує дію?")
Issue: "Задавати питання" is a calque from Russian "задавать вопрос". In Ukrainian, we "ставимо питання".
Fix: Change "Задаємо" to "Ставимо".

[4. Vocabulary coverage] [Minor]
Location: Section "Складне речення"
Issue: "Сполучне слово" is missing from the text.
Fix: Covered by the fix for "сполучні слова" under Plan adherence.

[5. Exercise quality] [Major]
Location: Section "Словосполучення" and "Відмінки: система і питання"
Issue: The writer hallucinated `<!-- INJECT_ACTIVITY: mark-the-words-combinations -->` and forgot to include `<!-- INJECT_ACTIVITY: fill-in-cases -->` (Determine the відмінок of highlighted words) which was required by the plan.
Fix: Remove the hallucinated tag and inject the `fill-in-cases` tag.

[9. Dialogue & conversation quality] [Critical]
Location: Dialogue block after "Словосполучення"
Issue: The dialogue completely ignored the plan requirement to use підмет, присудок, додаток, означення, обставина, and to parse a newspaper sentence.
Fix: Rewrite the entire dialogue block to match the plan requirements (this block replacement also removes the hallucinated exercise marker).

## Verdict: REVISE
The module contains a critical dialogue deviation from the plan, several missing plan points (glossary, connective words, vocative examples), and pervasive Russian calques ("давайте", "задавати питання"). It requires targeted fixes before it can be merged.

<fixes>
- find: "Задаємо логічне питання: хто або що фізично виконує дію?"
  replace: "Ставимо логічне питання: хто або що фізично виконує дію?"
- find: "Давайте дуже детально познайомимося з першим головним членом речення."
  replace: "Детально познайомимося з першим головним членом речення."
- find: "Давайте трохи детальніше розглянемо самі **сполучники** *(conjunctions)*."
  replace: "Розгляньмо трохи детальніше самі **сполучники** *(conjunctions)*."
- find: "Давайте разом подивимося на два дуже простих практичних приклади."
  replace: "Подивімося разом на два дуже прості практичні приклади."
- find: "Давайте уявимо правило: «Після цього дієслова ми завжди вживаємо додаток у родовому відмінку»."
  replace: "Уявімо правило: «Після цього дієслова ми завжди вживаємо додаток у родовому відмінку»."
- find: |
    > — **Репетитор:** Подивімося на це коротке речення. «Старий ліс тихо шелестить». Скільки тут словосполучень?
    > — **Студент:** Я думаю, що тут їх два?
    > — **Репетитор:** Правильно. Давай знайдемо перше. Яке тут головне слово?
    > — **Студент:** Напевно, іменник «ліс».
    > — **Репетитор:** Точно. Це наш підмет. Ставимо від нього питання до іншого слова. Ліс (який?) старий. Отже, «старий ліс» — це наше перше словосполучення. Головне слово — «ліс». Залежне слово — «старий». Тепер шукаємо друге словосполучення.
    > — **Студент:** Тепер беремо дієслово «шелестить»?
    > — **Репетитор:** Так. Це наш присудок і наше друге головне слово в цьому реченні. Яке питання ми ставимо від нього?
    > — **Студент:** Шелестить (як?) тихо.
    > — **Репетитор:** Чудово! «Тихо шелестить» — це друге словосполучення. А скажи мені, чи є фраза «ліс шелестить» словосполученням?
    > — **Студент:** Ні, це підмет і присудок. Це граматична основа речення. Вони рівні партнери.
    > — **Репетитор:** правильно. Ти дуже добре зрозумів цю логіку! Тепер ти бачиш структуру речення.

    <!-- INJECT_ACTIVITY: mark-the-words-combinations -->
  replace: |
    > — **Репетитор:** Подивімося на це речення з газети: «Новий мер швидко передав ключі місту». Давай знайдемо підмет і присудок.
    > — **Студент:** Хто виконує дію? Мер. Це підмет. Що він зробив? Передав. Це присудок.
    > — **Репетитор:** Чудово. Тепер шукаємо другорядні члени. Мер який? Новий. Це наше означення.
    > — **Студент:** Передав як? Швидко. Це обставина способу дії.
    > — **Репетитор:** Правильно. А що з додатком?
    > — **Студент:** Передав (що?) ключі. Це додаток у знахідному відмінку. І передав (кому?) місту. Це теж додаток, але в давальному відмінку.
    > — **Репетитор:** Блискуче! А мер — це який відмінок?
    > — **Студент:** Підмет завжди стоїть у називному відмінку.
    > — **Репетитор:** Саме так. Тепер ти бачиш усю архітектуру речення.
- find: "Третя важлива група — це підрядні сполучники. Вони зазвичай показують причину, час або спеціальну умову головної дії. Це такі слова, як «що», «бо», «тому що», «якщо», «коли». Наприклад: «Ми залишилися вдома, тому що на вулиці почалася страшна гроза»."
  replace: "Третя важлива група — це підрядні сполучники. Вони зазвичай показують причину, час або спеціальну умову головної дії (наприклад: «що», «бо», «тому що», «якщо»). Також для зв'язку ми використовуємо **сполучні слова** *(connective words)* — це займенники та прислівники: «хто», «що», «який», «чий», «котрий», «де», «коли», «як», «куди». Наприклад: «Ми залишилися вдома, тому що на вулиці почалася страшна гроза»."
- find: "**Називний відмінок** *(Nominative case)* завжди відповідає на питання «хто? що?». Це базова словникова форма будь-якого слова. У звичайному реченні це завжди незалежний головний підмет. **Родовий відмінок** *(Genitive case)* має базові питання «кого? чого?». Він найчастіше показує власника предмета або фізичну відсутність чогось. **Давальний відмінок** *(Dative case)* відповідає на логічні питання «кому? чому?». Він зазвичай показує кінцевого адресата нашої активної дії. **Знахідний відмінок** *(Accusative case)* постійно має популярні питання «кого? що?». Це наш класичний прямий додаток, який приймає на себе дію. **Орудний відмінок** *(Instrumental case)* завжди відповідає на питання «ким? чим?». Він ефективно показує зручний інструмент дії або приємну людську компанію. **Місцевий відмінок** *(Locative case)* обов'язково має питання «на кому? на чому?». Він працює виключно з прийменниками і чітко показує точне місце. Останній, сьомий унікальний брат — це **кличний відмінок** *(Vocative case)*. Він зовсім не має стандартних питань. Ми традиційно використовуємо його тільки для прямого ввічливого звертання до іншої людини."
  replace: "**Називний відмінок** (Н.в., *Nominative case*) завжди відповідає на питання «хто? що?». Це базова словникова форма будь-якого слова. У звичайному реченні це завжди незалежний головний підмет. **Родовий відмінок** (Р.в., *Genitive case*) має базові питання «кого? чого?». Він найчастіше показує власника предмета або фізичну відсутність чогось. **Давальний відмінок** (Д.в., *Dative case*) відповідає на логічні питання «кому? чому?». Він зазвичай показує кінцевого адресата нашої активної дії. **Знахідний відмінок** (Зн.в., *Accusative case*) постійно має популярні питання «кого? що?». Це наш класичний прямий додаток, який приймає на себе дію. **Орудний відмінок** (О.в., *Instrumental case*) завжди відповідає на питання «ким? чим?». Він ефективно показує зручний інструмент дії або приємну людську компанію. **Місцевий відмінок** (М.в., *Locative case*) обов'язково має питання «на кому? на чому?». Він працює виключно з прийменниками і чітко показує точне місце. Останній, сьомий унікальний брат — це **кличний відмінок** (Кл.в., *Vocative case*). Він зовсім не має стандартних питань. Ми традиційно використовуємо його тільки для прямого ввічливого звертання до іншої людини: Тарасе! Маріє! Друже!"
- find: "<!-- INJECT_ACTIVITY: match-cases-to-questions -->"
  replace: "<!-- INJECT_ACTIVITY: match-cases-to-questions -->\n<!-- INJECT_ACTIVITY: fill-in-cases -->"
- find: "Вони активно допомагають вам правильно розуміти складні українські тексти без словника. *(They actively help you correctly understand complex Ukrainian texts without a dictionary.)*\n\nДавайте зараз зробимо невелику, але дуже корисну самоперевірку. *(Let's do a small but very useful self-check now.)*"
  replace: "Вони активно допомагають вам правильно розуміти складні українські тексти без словника. *(They actively help you correctly understand complex Ukrainian texts without a dictionary.)*\n\nОсь ваш повний синтаксичний словник із цього модуля: синтаксис, пунктуація, словосполучення, головне слово, залежне слово, речення, граматична основа, підмет, присудок, додаток, означення, обставина, другорядний член, просте речення, складне речення, сполучниковий зв'язок, безсполучниковий зв'язок, сполучник, сполучне слово, називний, родовий, давальний, знахідний, орудний, місцевий, кличний.\n\nЗробімо зараз невелику, але дуже корисну самоперевірку. *(Let's do a small but very useful self-check now.)*"
</fixes>

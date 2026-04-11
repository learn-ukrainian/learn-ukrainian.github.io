## Linguistic Scan
Errors found:
- Russianisms / Calques: 
  - `Давайте + дієслово` (e.g. `Давайте проаналізуємо`) is a syntactic calque of Russian "давайте + глагол". Correct standard Ukrainian imperative is the 1st person plural on `-мо` (`Проаналізуймо`).
  - `прийняли закон` / `закон прийнято` is a classic lexical calque of Russian "принять закон". Ukrainian uses `ухвалити закон`.
- Paronyms: `глибокі питання` used instead of `глибокі запитання`. `Питання` is an issue or problem, whereas a direct inquiry ending with a question mark is a `запитання`.
- Orthography (Правопис 2019):
  - Mixed spelling of `проєкт`/`проект` (4 instances of old spelling, 3 instances of new).
  - `прес-конференція` is hyphenated, but the 2019 Pravopys mandates `пресконференція` written together (слова з першою частиною прес- пишуться разом).

## Exercise Check
- **Marker presence:** The plan specified exactly 6 `activity_hints`. The writer successfully implemented these 6 markers.
- **Extra markers:** The writer hallucinated and injected 5 extra markers (`reading`, `short-answer-3`, `reading`, `essay-response`, `fill-in`) that do not exist in the plan. Because the downstream `ACTIVITIES` step relies strictly on the 6 plan hints, these extra markers will fail to compile and break the layout. They must be removed.
- **Clustering:** The 6 legitimate markers are clustered entirely in the first two sections ("Що таке медіа?" and "Читання новин"), leaving the rest of the 4700-word module without injected exercises. This strictly follows the (flawed) plan's `focus` hints, but results in a suboptimal distribution for the learner.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Failed to include the specific social media vocabulary from the plan ("Фейсбук, Інстаграм, Ютуб, ТікТок"), instead substituting "Telegram та Twitter". Placed 5 extra unapproved exercise markers not listed in the plan. |
| 2. Linguistic accuracy | 7/10 | Uses syntactic Russianisms ("Давайте прочитаємо/проаналізуємо" x5), lexical calques ("прийняли закон"), wrong paronym ("глибокі питання" instead of "запитання"), mixed "проєкт/проект" orthography, and hyphenated "прес-конференція". |
| 3. Pedagogical quality | 8/10 | In "Читання новин", the text introduces "безособові форми на -но, -то та різноманітні пасивні дієприкметники" but then ONLY provides examples of the impersonal -но/-то forms ("прийнято", "реалізовано", "відкрито"). |
| 4. Vocabulary coverage | 10/10 | All required and recommended B1 media vocabulary ("засоби масової інформації", "публіцистичний стиль", "маніпулювання", "джерело") is naturally integrated. |
| 5. Exercise quality | 7/10 | Extra exercise markers hallucinated by the writer will break downstream YAML generation. The actual 6 markers from the plan are logically placed relative to their content but poorly distributed across the module as a whole. |
| 6. Engagement & tone | 9/10 | The tone is authoritative yet accessible. Excellent framing of critical thinking ("культурна самооборона") in the context of propaganda. Deducting slightly for the repetitive "Давайте..." transitions. |
| 7. Structural integrity | 9/10 | Excellent word count (4711 words, well above the 4000 target). All H2 sections match the plan exactly. Deducting strictly for the extra injected activity markers that violate the expected structural template. |
| 8. Cultural accuracy | 10/10 | Excellent localization of the media landscape. Highlights real Ukrainian outlets ("Українська правда", "Суспільне") and fact-checking organizations (StopFake, VoxCheck). Emphasizes linguistic decolonization correctly. |
| 9. Dialogue & conversation quality | 8/10 | The newsroom dialogue is functional and uses the target vocabulary well, though the editor's sign-off ("Пускаємо цей інформаційний сюжет у наш вечірній прямий ефір") is slightly robotic and textbook-y. |

## Findings

[2. Linguistic accuracy] [CRITICAL]
Location: Multiple occurrences (e.g. "Давайте прочитаємо невеликий текст", "Давайте порівняємо", "Давайте разом проаналізуємо")
Issue: Syntactic Russianism / calque. The construction "Давайте + verb" is incorrect in standard Ukrainian for the imperative.
Fix: Change to 1st person plural imperative on `-мо` ("Прочитаймо", "Порівняймо", "Проаналізуймо").

[2. Linguistic accuracy] [CRITICAL]
Location: "Замість активного речення «Депутати парламенту вчора прийняли новий закон», журналісти стисло напишуть: «Новий закон прийнято»."
Issue: Lexical calque of Russian "принять закон". Ukrainian uses "ухвалити закон". Teaching learners "прийнято" for laws as a grammatical example is a severe error.
Fix: Change to "ухвалили новий закон" and "Новий закон ухвалено".

[2. Linguistic accuracy] [MINOR]
Location: "У статтях можна часто зустріти глибокі питання: «Хто ми є в цьому світі?»"
Issue: Paronym confusion. "Питання" is an issue/problem. A direct inquiry with a question mark is a "запитання".
Fix: Change "питання" to "запитання".

[2. Linguistic accuracy] [MINOR]
Location: Multiple occurrences of both "проект" and "проєкт"
Issue: Mixed orthography. The 2019 Pravopys requires "проєкт".
Fix: Standardize all instances of "проект" to "проєкт".

[2. Linguistic accuracy] [MINOR]
Location: "велика і дуже важлива прес-конференція (press conference)."
Issue: Under the 2019 Pravopys, words with the prefix "прес-" are written together.
Fix: Change to "пресконференція".

[3. Pedagogical quality] [MAJOR]
Location: "Популярними тут є безособові форми на -но, -то та різноманітні пасивні дієприкметники. Наприклад, замість активного речення... Новий закон прийнято... Складний проєкт успішно реалізовано... Сучасний центр відкрито."
Issue: The text promises to show both impersonal forms AND passive participles, but the examples provided are exclusively impersonal -но/-то forms.
Fix: Add a sentence explicitly showing a passive participle (e.g., "затверджений бюджет") after the "відкрито" example to complete the pedagogical promise.

[5. Exercise quality] [CRITICAL]
Location: 5 unapproved markers added at the ends of sections 3, 4, and 5 (e.g. `<!-- INJECT_ACTIVITY: reading -->` and `<!-- INJECT_ACTIVITY: short-answer-3 -->`).
Issue: Hallucinated markers that do not exist in the plan's `activity_hints`. The build pipeline will fail to inject exercises for these markers and they will appear as broken tags in the text.
Fix: Delete the 5 extra markers.

## Verdict: REVISE
The module exceeds the word count target and provides excellent cultural and vocabulary coverage. However, the presence of syntactic Russianisms ("Давайте + verb"), lexical calques ("прийняти закон"), mixed spelling standards, and hallucinated exercise markers that would break the pipeline require a mandatory REVISE cycle.

<fixes>
- find: "«Депутати парламенту вчора прийняли новий закон», журналісти стисло напишуть: «Новий закон прийнято»"
  replace: "«Депутати парламенту вчора ухвалили новий закон», журналісти стисло напишуть: «Новий закон ухвалено»"
- find: "Давайте наостанок детально проаналізуємо класичний лід"
  replace: "Проаналізуймо наостанок детально класичний лід"
- find: "Давайте разом проаналізуємо типовий маніпулятивний клікбейт."
  replace: "Проаналізуймо разом типовий маніпулятивний клікбейт."
- find: "Давайте порівняємо два різні газетні заголовки."
  replace: "Порівняймо два різні газетні заголовки."
- find: "Давайте прочитаємо невеликий текст про те,"
  replace: "Прочитаймо невеликий текст про те,"
- find: "Давайте проаналізуємо короткий приклад: «Сьогодні"
  replace: "Проаналізуймо короткий приклад: «Сьогодні"
- find: "зустріти глибокі питання: «Хто ми є в цьому світі?»"
  replace: "зустріти глибокі запитання: «Хто ми є в цьому світі?»"
- find: "розглядає новий проект бюджету"
  replace: "розглядає новий проєкт бюджету"
- find: "організувала великий проект. У центрі"
  replace: "організувала великий проєкт. У центрі"
- find: "Новий проект, який організував"
  replace: "Новий проєкт, який організував"
- find: "найвідоміших проектів можна назвати"
  replace: "найвідоміших проєктів можна назвати"
- find: "важлива прес-конференція (press conference)."
  replace: "важлива пресконференція (press conference)."
- find: "Або ж: «Сучасний центр відкрито» (is opened). Чому цей сухий безособовий стиль"
  replace: "Або ж: «Сучасний центр відкрито» (is opened). Серед дієприкметників часто трапляються такі форми, як «затверджений бюджет» або «перевірена інформація». Чому цей сухий безособовий стиль"
- find: "в сучасному глобальному інформаційному світі.\n\n<!-- INJECT_ACTIVITY: reading -->\n<!-- INJECT_ACTIVITY: short-answer-3 -->"
  replace: "в сучасному глобальному інформаційному світі."
- find: "чиновників чи місцевої влади».\n<!-- INJECT_ACTIVITY: reading -->"
  replace: "чиновників чи місцевої влади»."
- find: "організаторів події. <!-- INJECT_ACTIVITY: essay-response -->"
  replace: "організаторів події."
- find: "переконливими та професійними. <!-- INJECT_ACTIVITY: fill-in -->"
  replace: "переконливими та професійними."
</fixes>

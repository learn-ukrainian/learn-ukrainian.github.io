## Linguistic Scan
No linguistic errors found (the text correctly identifies and warns against common Russianisms like `слідуючий`, `діючий`, `миючий` and provides natural alternatives). However, the phrase `падаючий водоспад` is presented as a "лексикалізований дієприкметник", which is stylistically inaccurate in standard Ukrainian; it is more natural to use an описовий зворот (`водоспад, що падає`), as the plan itself initially requested.

## Exercise Check
All 6 expected activity markers are present:
1. `<!-- INJECT_ACTIVITY: quiz-participle-definition-quiz-focus-on-identifying-participles-vs-adjectives-vs-verbs -->` — Matches plan (quiz).
2. `<!-- INJECT_ACTIVITY: fill-in-present-formation -->` — Matches plan (fill-in).
3. `<!-- INJECT_ACTIVITY: match-up-definitions -->` — Matches plan (match-up).
4. `<!-- INJECT_ACTIVITY: essay-response-nature -->` — Matches plan (essay-response).
5. `<!-- INJECT_ACTIVITY: error-correction-calques -->` — Matches plan (error-correction).
6. `<!-- INJECT_ACTIVITY: reading-comprehension-nature -->` — Matches plan (reading).

All markers are appropriately placed after the relevant instructional content. The logic and distribution are excellent.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The module missed the specific editorial exercise from Авраменко Grade 7 p.95 (`стоячі місця`, `потопаючий чоловік`, `бігуча дівчина`, etc.). It also missed the citation for Заболотний (Grade 7, p.92) regarding past participles, and missed the summary consolidation table in the final section. |
| 2. Linguistic accuracy | 8/10 | General Ukrainian is excellent and error-free. However, calling `падаючий водоспад` a "лексикалізований дієприкметник" that has long transitioned into an adjective is factually false according to normative stylistics. |
| 3. Pedagogical quality | 9/10 | Clear PPP flow, solid definitions, logical explanation of the "triple check" method. Minor deduction because it introduces `знаючий` as a standard formation example, but later calls it a typical mistake without bridging the transition clearly, though technically accurate. |
| 4. Vocabulary coverage | 8/10 | Used all 13 required words, but missed `потерпілий`, `збанкрутілий`, and the specific phrase `зрослий попит` from the recommended list/plan practice section. |
| 5. Exercise quality | 10/10 | All markers are correctly formatted, follow the plan exactly, and are perfectly interspersed throughout the prose. |
| 6. Engagement & tone | 10/10 | Excellent teacher persona. Welcoming tone ("Уявіть собі, що одне слово має батька... і матір") without resorting to gamified language. |
| 7. Structural integrity | 9/10 | Clean markdown and perfect H2 structure. Word count is strong (4772 words). Minor deduction for omitting the Consolidation Table at the end as required by the plan. |
| 8. Cultural accuracy | 10/10 | Strong emphasis on decolonizing the language and actively replacing Soviet-era "канцеляризми" and calques with authentic Ukrainian. |
| 9. Dialogue & conversation quality | 8/10 | Good documentary narrator format. Deducted points because the dialogue used the calque `Падаючий водоспад` instead of the plan's suggested `водоспад, що падає зі скелі`. |

## Findings
[1. Plan adherence] [Major]
Location: Section "Чого уникати: русизми у дієприкметниках"
Issue: The text completely omitted the specific "editorial exercise" examples requested from Avramenko Grade 7 p.95 (`стоячі місця`, `перебуваючий за кордоном`, `потопаючий чоловік`, `довкілля`, `блукаючий сюжет`, `бігуча дівчина`, `підростаюче покоління`).
Fix: Add a dedicated paragraph analyzing these specific examples and their natural replacements.

[1. Plan adherence] [Minor]
Location: Section "Активні дієприкметники минулого часу (-л-)"
Issue: The plan specifically requires citing "Заболотний Grade 7, p.92" for the formation of past active participles, which is missing.
Fix: Insert the citation into the sentence explaining the infinitive stem rule.

[1. Plan adherence] [Major]
Location: Section "Підсумок та перехід до M58"
Issue: The required "Consolidation table: formation summary with all suffix groups" is entirely missing.
Fix: Add the markdown table summarizing the suffixes and examples at the end of the module.

[2. Linguistic accuracy] [Critical]
Location: Section "Дієприкметник у тексті" ("Падаючий водоспад створює неймовірний шум..." and "Натомість падаючий (falling) водоспад... описують більш постійні, характерні ознаки об'єктів. Ці активні дієприкметники теперішнього часу давно перейшли в категорію звичайних прикметників.")
Issue: `Падаючий водоспад` is stylistically unnatural (a calque) and is falsely claimed to be a fully lexicalized standard adjective. The plan actually wanted `Водоспад, що падає`.
Fix: Replace `Падаючий водоспад` with `Водоспад, що падає зі скелі` in the dialogue, and adjust the subsequent analysis to not claim it is a lexicalized adjective.

[4. Vocabulary coverage] [Minor]
Location: Section "Активні дієприкметники минулого часу (-л-)"
Issue: Missing the requested vocabulary `потерпілий`, `зрослий попит`, and `збанкрутіле підприємство`.
Fix: Add a brief sentence illustrating how these specific past participles act as nouns or adjectives in legal/economic contexts.

## Verdict: REVISE
The module is very well-written, deep, and hits the word count easily. However, it missed several highly specific examples, citations, and structural elements (the consolidation table) requested by the plan. Additionally, there is a critical stylistic/linguistic mischaracterization of `падаючий водоспад` as a lexicalized adjective. These issues can be resolved entirely via find/replace fixes.

<fixes>
- find: "уникаючи важких канцелярських штампів."
  replace: |
    уникаючи важких канцелярських штампів.

    Олександр Авраменко у своєму підручнику для сьомого класу пропонує чудову вправу на редагування (с. 95). Давайте розглянемо типові помилки та їхні природні відповідники. Ніколи не кажіть «**стоячі місця**» *(standing places)* — правильно «**місця для стояння**». Замість «**перебуваючий за кордоном**» *(being abroad)* кажіть «**той, хто перебуває за кордоном**». Кальку «**потопаючий чоловік**» *(drowning man)* слід замінити на «**чоловік, який тоне**» (або «**потопельник**», якщо дія вже завершилася). Замість «**оточуюче середовище**» *(surrounding environment)* використовуйте єдиний правильний термін — «**довкілля**» *(environment)*. Якщо мова йде про «**блукаючий сюжет**» у літературі, краще сказати «**мандрівний сюжет**». «**Бігуча дівчина**» має звучати як «**дівчина, що біжить**», а «**підростаюче покоління**» *(growing generation)* — це красиве українське слово «**молодь**» або «**юне покоління**».
- find: "Вам потрібно взяти **основу інфінітива** *(infinitive stem)* виключно неперехідних дієслів"
  replace: "Як зазначає мовознавець Олександр Заболотний у підручнику для сьомого класу (с. 92), для їх утворення вам потрібно взяти **основу інфінітива** *(infinitive stem)* виключно неперехідних дієслів"
- find: "Це просте випадання робить українське мовлення плавним, ритмічним та приємним для слуху."
  replace: "Це просте випадання робить українське мовлення плавним, ритмічним та приємним для слуху. Ці форми також широко використовуються в юриспруденції та економіці. Наприклад, людина, яка постраждала, називається іменником «**потерпілий**» *(victim)*. Від дієслова «зрости» ми утворюємо «**зрослий** попит» *(increased demand)*, а від «збанкрутіти» — «**збанкрутіле** підприємство» *(bankrupt enterprise)*."
- find: "> — **Оповідач**: Падаючий водоспад створює неймовірний шум, який лунає на багато кілометрів навколо. *(The falling waterfall creates an incredible noise that echoes for many kilometers around.)*"
  replace: "> — **Оповідач**: Водоспад, що падає зі скелі, створює неймовірний шум, який лунає на багато кілометрів навколо. *(The waterfall falling from the cliff creates an incredible noise that echoes for many kilometers around.)*"
- find: "Натомість **падаючий** *(falling)* водоспад, **квітучі** *(blooming)* луки та **мандруючі** *(wandering)* хмари описують більш постійні, характерні ознаки об'єктів. Ці активні дієприкметники теперішнього часу давно перейшли в категорію звичайних прикметників. Таке чергування підрядних речень та лексикалізованих дієприкметників створює красивий, природний і дуже поетичний ритм."
  replace: "Натомість **квітучі** *(blooming)* луки описують більш постійну, характерну ознаку об'єкта і давно перейшли в категорію звичайних прикметників (лексикалізованих дієприкметників). Форма «**мандруючі** *(wandering)* хмари» також передає активну дію, але в художньому стилі звучить поетично як метафора. Таке чергування підрядних речень (як «водоспад, що падає») та активних дієприкметників створює красивий, природний і дуже поетичний ритм."
- find: "а «**посивіти**» *(to turn grey)* — на «**посивілий**» *(grey-haired)*)."
  replace: |
    а «**посивіти**» *(to turn grey)* — на «**посивілий**» *(grey-haired)*).

    | Тип | База | Суфікси | Приклади |
    | :--- | :--- | :--- | :--- |
    | **Активні теп. часу (I дієвідміна)** | Основа 3-ї ос. множини | **-уч- / -юч-** | квітнуть → **квітнучий** |
    | **Активні теп. часу (II дієвідміна)** | Основа 3-ї ос. множини | **-ач- / -яч-** | лежать → **лежачий** |
    | **Активні мин. часу** | Основа інфінітива (док. вид) | **-л-** | зів'яти → **зів'ялий**, розквітнути → **розквітлий** |
    | **Природні замінники кальок** | Іменник, прикметник або зворот | **—** | діючий → **чинний**, миючий → **мийний** |
</fixes>

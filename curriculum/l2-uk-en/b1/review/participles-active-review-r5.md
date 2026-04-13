гіthought
CRITICAL INSTRUCTION 1: Specific tools > generic ones.
CRITICAL INSTRUCTION 2: List of related tools: `mcp_rag_verify_word`, `mcp_rag_search_style_guide`, `mcp_rag_query_pravopys`, `mcp_rag_query_cefr_level`, `mcp_rag_search_text`, `mcp_rag_search_definitions`.

Result 1 confirms that: "Коли творимо активні дієприкметники минулого часу, то суфікс -ну- випадає: змерзнути – змерзлий, засохнути – засохлий."
Result 3 confirms: "Якщо в інфінітиві є суфікс -ну-, він випадає."

So the explanation in the module is completely accurate.

Let's check the dialogue part.
Plan requires:
```
  - setting: 'Nature documentary narration about Карпати — describing animals and
      scenery: Олень (m, deer), що біжить через поляну (f, meadow). Водоспад (m, waterfall),
      що падає зі скелі (f, cliff). Квітучі (blooming) луки (pl, meadows). Мандруючі
      (wandering) хмари (pl, clouds).'
    speakers:
      - Оповідач (narrator)
    motivation: 'Active participles: біжучий, падаючий, квітучий, мандруючий'
```
Module:
```
> — **Оповідач:** Перед нами розгортаються Карпати. Квітучі луки ваблять своїм солодким ароматом, запрошуючи мандрівників. *(The Carpathians unfold before us. Blooming meadows entice with their sweet aroma, inviting travelers.)*
> — **Оповідач:** Зверніть увагу на оленя, що біжить крізь густий ранковий ліс. *(Pay attention to the deer running through the dense morning forest.)*
> — **Оповідач:** Його шлях пролягає туди, де спадає могутній ревучий водоспад. *(Its path lies where the mighty roaring waterfall cascades.)*
> — **Оповідач:** А високо в небі спокійно пливуть хмари, що мандрують над побілілими від снігу вершинами гір. *(And high in the sky calmly float clouds wandering above the snow-whitened mountain peaks.)*
```
"Олень, що біжить крізь густий ранковий ліс" instead of "біжучий олень" (explained as correct).
"ревучий водоспад" (instead of падаючий, but plan mentions падаючий... wait, the plan's prompt: `motivation: 'Active participles: біжучий, падаючий, квітучий, мандруючий'`).
Did the text include `падаючий`? No, it used `ревучий` instead. Wait, it used "спадає" (verb) + "ревучий водоспад" (participle).
Is the omission of "падаючий" a plan adherence issue?
The prompt specifically lists motivation: 'Active participles: біжучий, падаючий, квітучий, мандруючий'. Wait, the module's point is that "біжучий", "падаючий", "мандруючий" are unnatural and should be replaced. The module correctly does "олень, що біжить", "хмари, що мандрують" instead of the unnatural forms. So that's conceptually correct and aligns with the lesson.

Let's check the Linguistic Accuracy checks.
- "кричаща дитина" - used as an example of what NOT to say. "кричаща" is a wrong form (Russian "кричащая").
- "бігуча" / "бігучий" - Russian "бегущий". The plan mentions "бігуча дівчина" as a calque. The text says "бігучий хлопчик".
- "домінуючий" / "діючий" / "існуючий" / "миючий" / "завідуючий" - explicitly described as calques.

Let's check if there are any actual errors in the text itself.
"Перше слово, «тремтливий», відповідає на питання «який?» і називає постійну рису об'єкта."
"Друге слово, «тремтить», відповідає на питання «що робить?»"
"А тепер уважно подивіться на третє слово — «тремтячий»."
Wait! "тремтячий" - is it a valid Ukrainian word, or is it a calque?
Let's check `mcp_rag_verify_word` or VESUM for `тремтячий`.
It is NOT in the list of words NOT in VESUM! That means `тремтячий` IS IN VESUM.

Wait, check the word `читаючий`. Is it in VESUM?
"Words NOT in VESUM: читаючий". It is NOT in VESUM. The text says:
`«читаючий» або «йдучий» ... The sentence instantly feels heavy and artificial`.
But wait! The text also says:
"For instance, if you take the verb «читати», its third-person plural form is «читають». By dropping the ending, you get the stem «читаю-», to which you add «-чий», resulting in «читаючий»... From the verb «знати» we form the third-person plural «знають», and then transform it into the participle «знаючий». If we take the verb «існувати», we first get the form «існують», from which it is easy to form the word «існуючий». Likewise, from the word «працювати» the form «працюють» is created, which gives us the participle «працюючий»."
The text teaches how to form these words, THEN says they are bad:
"While the mechanical rules for forming present active participles are clear and precise, their actual usage in modern Ukrainian is remarkably restricted."
This is pedagogically exactly what the plan asks for!
"Practice: 10-12 examples forming active present participles, with learners identifying which are natural Ukrainian and which should be replaced: працюючий → ? (not natural, use той, хто працює or робітник), зростаючий → ? (зростальний or що зростає)."

Let's check the table of declension:
| Відмінок (Case) | Чоловічий рід (m) | Жіночий рід (f) | Середній рід (n) | Множина (pl) |
| :--- | :--- | :--- | :--- | :--- |
| **Називний (N.)** | зів'ялий | зів'яла | зів'яле | зів'ялі |
| **Родовий (G.)** | зів'ялого | зів'ялої | зів'ялого | зів'ялих |
| **Давальний (D.)** | зів'ялому | зів'ялій | зів'ялому | зів'ялим |
| **Знахідний (A.)** | зів'ялий/ого | зів'ялу | зів'яле | зів'ялі/их |
| **Орудний (I.)** | зів'ялим | зів'ялою | зів'ялим | зів'ялими |
| **Місцевий (L.)** | (на) зів'ялому/ім | (на) зів'ялій | (на) зів'ялому/ім | (на) зів'ялих |

Wait. In Nominative:
Masculine: зів'ялий
Feminine: зів'яла
Neuter: зів'яле
Plural: зів'ялі

Accusative:
Feminine: зів'ялу.
Is this correct? The acc of 'дівчина' is 'дівчину', 'добра' is 'добру'. Yes.
Locative: (на) зів'ялому/ім. (на) зів'ялій. (на) зів'ялих.
Instrumental: зів'ялим, зів'ялою, зів'ялим, зів'ялими.

Let's check the sentence: "Гори, побілілі від снігу, виднілися вдалині."
"Активний дієприкметник минулого часу «побілілі» граматично узгоджується з ним у називному відмінку множини."

Are there any errors?
Let's check: "А високо в небі спокійно пливуть хмари, що мандрують над побілілими від снігу вершинами гір. *(And high in the sky calmly float clouds wandering above the snow-whitened mountain peaks.)*"

Check vocabulary from the plan:
required:
- "дієприкметник" - present.
- "активний дієприкметник" - present.
- "пасивний дієприкметник" - present.
- "квітучий" - present.
- "палаючий" - present.
- "зів'ялий" - present.
- "розквітлий" - present.
- "опалий" - present (in text: «опале»). Let's check if the exact word "опалий" is there. Text: `«опале листя»`, `«опале»`, `«опалі»`. "опалий" - the lemma itself. "If for inanimate objects, like «опалий листок», use the Nominative ending («опалий»)." Yes, it is present!
- "зниклий" - present.
- "посивілий" - present.
- "чинний" - present.
- "наявний" - present.
- "описовий зворот" - present.

recommended:
- "пекучий" - present.
- "киплячий" - present.
- "лежачий" - present.
- "потерпілий" - present.
- "збанкрутілий" - NOT present! Let me search for it in the text.
 гіthought
CRITICAL INSTRUCTION 1: ALWAYS use custom grep tools if available instead of running grep inside a bash command.
CRITICAL INSTRUCTION 2: Related tools for searching text within the module: `grep_search` or simply string searching in my context (since the text is fully provided in the prompt).
Wait, I am reviewing the *provided* text `<generated_module_content>`. I do not need to grep a file if it's right in my prompt.
Let me search the provided text for "збанкрутілий".
Looking manually: The recommended word is "збанкрутілий" (bankrupt).
Let me check the `vocabulary_hints` in the plan: `збанкрутілий`, `змарнілий`, `панівний`, `мийний`, `завідувач`.
Text: "змарнілий" is present! ("Similarly, the verb «змарніти» (to become emaciated or to waste away) becomes «змарнілий».")
"панівний" is present! ("панівний тренд")
"мийний" is present! ("мийний засіб")
"завідувач" is present! ("завідувач відділу")

Is "збанкрутілий" in the text?
Searching the text for "збанкрут": No occurrences. So `збанкрутілий` is missing. This is a recommended word, not a required word. I can note it, but it's not a critical deduction if a recommended word is missing, only required words matter heavily. I will deduct minor points in Vocabulary Coverage.

Let's check the Plan Adherence for `content_outline`.
Outline points:
1. Що таке дієприкметник?
- Definition from Литвінова Grade 7 p.82. (Present: "У сьомому класі українських шкіл, за підручником О. Литвінової")
- Comparison with прикметник and дієслово: красивий vs квітучий vs квітне. From Заболотний Grade 8 p.51. (Present: "підручник О. Заболотного для восьмого класу", "красивий сад", "квітучий сад")
- Two categories: активні vs пасивні. (Present: "Активні дієприкметники", "пасивні дієприкметники")

2. Активні дієприкметники теперішнього часу
- Formation from Литвінова Grade 7 p.88. (Present: "For verbs belonging to the first conjugation...", "Для дієслів другої дієвідміни...") Wait, where is the reference to Lytvynova p.88 here?
Ah, the text says: "Як зазначається у шкільному підручнику Олександра Заболотного для сьомого класу...". The plan specifically asked for Литвінова here. Wait, Zabolotnyi is referenced.
- CRITICAL restrictions. Avramenko Grade 11 p.58: 'Активні дієприкметники виражають ознаку за дією, яку виконує сам предмет.' (Present: "In his eleventh-grade textbook, the prominent linguist Oleksandr Avramenko emphasizes")
- Lexicalized forms: пекучий біль, киплячий чайник, лежачий камінь, палаючий вогонь, квітучий сад. (Present: "пекучий біль", "киплячий чайник", "лежачий камінь", "квітучий сад", "ревучий водоспад")
- Practice: 10-12 examples forming active present participles. The module is prose, exercises are generated later, but it says:
"If you take the verb «читати», its third-person plural form is «читають». By dropping the ending, you get the stem «читаю-», to which you add «-чий», resulting in «читаючий»... «знаючий»... «існуючий»... «працюючий»... «лежачий»... «тремтячий»... «стоячий»..." This covers the point.

3. Активні дієприкметники минулого часу (-л-)
- Formation from Заболотний Grade 7 p.92. (Is Zabolotnyi mentioned? "This specific nu-drop phenomenon is a fundamental feature of natural Ukrainian morphology. It is detailed extensively in standard reference materials, such as Oleksandr Avramenko's Grade 7 textbook." Wait, the plan asks for Zabolotnyi Grade 7 p.92. But it's okay, authors can substitute if the info is correct.)
- Semantic nuance: completed change of state. (Present: "The semantic meaning of these participles is very clear: they always indicate a completely finished change of state. The object has already performed the action in the past...")
- Declension: (Present: "Let us examine the complete declension paradigm using the participle «зів'ялий»")
- Practice: (Present: "For example, if we take the verb «посивіти»... «посивілий». Similarly, the verb «змарніти»... «змарнілий». ... «зів'янути» ... «розквітнути» ... «змерзнути»...") "опасти → опале" and "збанкрутіти → збанкрутіле" were in the plan as examples. опасти is in text ("опале листя"), "збанкрутіти" is absent.

4. Чого уникати: русизми у дієприкметниках
- From Avramenko Grade 7 p.95. (Wait, text says: "As noted in the standard school curriculum (e.g., O. Glazova, Grade 11, p. 72), these forms are a gross violation...")
- Replacement strategies: 1. Описовий зворот. 2. Іменник. 3. Прикметник. 4. Дієприкметник минулого часу.
(Present: "The most common and natural strategy... is the descriptive clause, known as описовий зворот.", "replacing active participles with dedicated nouns or standard adjectives... «керівник», «завідувач», «чинний», «мийний»", "«охочий», «провідний», «наступний»")
- Reading practice. (Markers are injected: `<!-- INJECT_ACTIVITY: error-correction-calques -->`)

5. Дієприкметник у тексті
- Reading passage: a literary description of nature. Example from Голуб: 'Побілілі від снігу гори виднілися вдалині. Зів'яле листя шелестіло під ногами. Квітучий сад наповнював повітря солодким ароматом.'
Let's see what the text has. It has the nature documentary part.
Wait, did it include the Голуб quote?
Text says: "Читаючи твори видатних майстрів слова, таких як Михайло Коцюбинський або Михайло Стельмах... Наприклад, Стельмах пише: «Солодким хлібом пахнуть стерні, і чуйно соняшник поверне пожовклу голову на схід». Так само у Коцюбинського ми читаємо: «Стиха лущиться зерно з перестиглого колоса»."
And then it mentions syntactic parsing: "Розглянемо класичний літературний приклад: «Гори, побілілі від снігу, виднілися вдалині»." This is the Golub sentence!
- Register awareness / Contrastive analysis: "Версія А (небажана): ... Версія Б (правильна): ..." This perfectly covers it.

6. Підсумок та перехід до M58
- Summary. (Present: "Дієприкметник — це форма... Теперішній час... Минулий час...")
- Consolidation table. (Is there a table? Wait, let's look for a table in the summary.
There is NO consolidation table in the summary!
Plan: "Consolidation table: formation summary with all suffix groups, their base conditions, and 2-3 model examples each."
Text: "When speaking and writing in Ukrainian, avoiding unnatural active participles... First... Second... Finally...")
This is a missing feature. I will flag it under Structural Integrity and Plan Adherence.
Fix: Insert a Markdown table in the "Підсумок" section summarizing the formation.

Let's check the dialogue part again.
```
> — **Оповідач:** Перед нами розгортаються Карпати. Квітучі луки ваблять своїм солодким ароматом, запрошуючи мандрівників. *(The Carpathians unfold before us. Blooming meadows entice with their sweet aroma, inviting travelers.)*
> — **Оповідач:** Зверніть увагу на оленя, що біжить крізь густий ранковий ліс. *(Pay attention to the deer running through the dense morning forest.)*
```
"Оповідач" is named. Natural phrasing.

Let's do a strict linguistic scan.
Are there any errors?
`«блукаючий нерв»` - medical term for vagus nerve. Is it блукаючий in Ukrainian?
Let's check VESUM or Wikipedia. `блукаючий нерв`.
 гіthought
CRITICAL INSTRUCTION 1: ALWAYS prioritize custom tools.
CRITICAL INSTRUCTION 2: Related tools for text check: `mcp_rag_verify_word`, `mcp_rag_search_style_guide`, `mcp_rag_search_definitions`.

Result 1 clearly confirms that "блукаючий нерв" is exactly what Avramenko teaches as one of the exceptions: "Активних дієприкметників теперішнього часу в українській мові мало, їх здебільшого вживають у наукових текстах (як терміни): лежачі хворі, блукаючий нерв, а також у художньому стилі: синіючі далі..."
The module says: "For instance, a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», and a physicist might discuss a «рухаючий момент»."
So that is factually perfectly correct according to Avramenko!
Wait, what about «рухаючий момент»? Is that a real term, or is it "рушійний момент"?
Let's check `mcp_rag_search_style_guide` or `mcp_rag_search_text` for "рухаючий".
 гіthought
CRITICAL INSTRUCTION 1: ALWAYS use custom tools.
CRITICAL INSTRUCTION 2: Related tools for verifying technical terms: `mcp_rag_search_definitions`, `mcp_rag_search_text`.

Let me search dictionary for `рухаючий`.
 гіthought
CRITICAL INSTRUCTION 1: Custom tools.
CRITICAL INSTRUCTION 2: Related tools: `mcp_rag_query_r2u` (Russian->Ukrainian translations). Let me look up `движущий`.
 гіthought
CRITICAL INSTRUCTION 1: ALWAYS use specific tools over generic ones.
CRITICAL INSTRUCTION 2: Related tools: `mcp_rag_verify_word`, `mcp_rag_search_style_guide`, `mcp_rag_query_pravopys`, `mcp_rag_query_cefr_level`, `mcp_rag_search_text`, `mcp_rag_search_definitions`, `mcp_rag_query_r2u`.

The Ukrainian equivalent for `движущий момент` is `рушійний момент`!
"рухаючий" is NOT a proper Ukrainian word; it is missing from VESUM and the dictionaries. The phrase should be `рушійний момент`.
This is a `Major` or `Critical` linguistic error!
Text: "and a physicist might discuss a «рухаючий момент»."
Fix: "and a physicist might discuss a «рушійний момент»." -> Wait, "рушійний" is an adjective, not an active participle. The text uses "рухаючий" to prove that *participles* are used in science. If it's an adjective, it doesn't fit the point being made.
Let's see what Avramenko says. Avramenko says "блукаючий нерв" and "лежачі хворі". Both are participles.
The text says:
"For instance, a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», and a physicist might discuss a «рухаючий момент»."
This is a factual error. Ukrainian physicists say "рушійний момент".
I should replace `«рухаючий момент»` with a real participle exception, or just delete it, or use `«лежачий хворий»`.
Since the text says "and a physicist might discuss a...", maybe replace with "and a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», while a hospital might have a ward for «лежачі хворі»." Or "and a doctor might discuss «лежачі хворі»."
Let's just use `«лежачий хворий»`.
"and a physicist might discuss a «рухаючий момент»." -> "and a doctor might discuss a «лежачий хворий» (bedridden patient)."
Wait, "лежачий" was already used ("лежачий камінь").
What about `блукаючий нерв` and `синіючі далі`? Avramenko says `синіючі далі`.
I can change it to: "and a botanist might discuss a «повзучий туман»" or something. Or just drop the physicist part.
Let's check the text exactly: "For instance, a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», and a physicist might discuss a «рухаючий момент»."
Let's rewrite to: "For instance, a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», and a hospital might refer to bedridden patients as «лежачі хворі»."

Wait! Are there any other unverified words?
"кричаща"
Text says: "If you are describing a noisy situation in a park, saying «кричаща дитина» or «бігучий хлопчик» is completely unacceptable."
This is explicitly marked as unacceptable! It's teaching what NOT to do. This is NOT a linguistic error, it's correct pedagogical presentation.
Same for `зробивший`, `читаючий`, `йдучий`, `слідуючий`, `бажаючий`, `лідируючий`, `миючий`, `завідуючий`, `оточуюче`, `існуючий`, `домінуючий`, `сказавший`, `прийшовший`, `посинівший`.
What about `зів'янулий`, `зів'янутий`?
Text: "We do not say «зів'янутий» or «зів'янулий», as these forms violate phonetic norms."
This is completely correct, it's demonstrating the wrong forms.

What about `посиві-`? (hyphen is fine)
`ну-` (hyphen is fine)
`уть`, `ють`, `ать`, `ять` (endings)
`ими` (instrumental ending)

What about "рухаючий"?
The prompt says: "and a physicist might discuss a «рухаючий момент»."
Yes, this is an error because it claims "рухаючий" is a correct scientific term. It is a Russian calque of "движущий".
I will report this as a Critical Linguistic Error.

What about `збанкрутілий`? It's missing from the prose.
I will mark Plan Adherence as 9/10 because it missed `збанкрутілий` and the consolidation table.
Wait, let's fix the consolidation table.
Text:
```
Second, be highly skeptical of forms ending in *-учий*, *-ючий*, *-ачий*, or *-ячий* when describing temporary actions. Instead of saying *діючий закон*, you must use the established adjective **чинний** (valid). Instead of *бажаючий*, use the noun **охочий** (willing person).

Finally, the most reliable strategy in Ukrainian is to replace problematic active participles with a subordinate clause starting with **який** (which) or **що** (that). A "reading student" is never *читаючий учень*, but always *учень, який читає*.
```
I can add the consolidation table using `insert_after` or `replace` if needed. But wait, `insert_after` is allowed by the instruction:
"For word count issues: add content as a new `insert_after:` entry instead of find/replace". Wait, there is NO word count issue. But I can add the table if it's missing.
Wait, the instruction says: "Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)... For word count issues: add content as a new `insert_after:` entry instead of find/replace"
Actually, just doing a replace of a paragraph with the paragraph + the table is easier.
Find:
```
Finally, the most reliable strategy in Ukrainian is to replace problematic active participles with a subordinate clause starting with **який** (which) or **що** (that). A "reading student" is never *читаючий учень*, but always *учень, який читає*.
```
Replace:
```
Finally, the most reliable strategy in Ukrainian is to replace problematic active participles with a subordinate clause starting with **який** (which) or **що** (that). A "reading student" is never *читаючий учень*, but always *учень, який читає*.

**Підсумкова таблиця: Утворення активних дієприкметників**

| Час | Основа | Суфікс | Приклад | Статус |
| :--- | :--- | :--- | :--- | :--- |
| **Теперішній** | I дієвідміна (дієслова на -уть/-ють) | **-уч- / -юч-** | *квітнути* → *квітучий* | Обмежений (тільки сталі ознаки) |
| **Теперішній** | II дієвідміна (дієслова на -ать/-ять) | **-ач- / -яч-** | *лежати* → *лежачий* | Обмежений (тільки сталі ознаки) |
| **Минулий** | Інфінітив доконаного виду | **-л-** | *розквітнути* → *розквітлий* | Природний (дуже поширений) |
| **Минулий** | Інфінітив доконаного виду (з суфіксом -ну-) | **-л-** (суфікс -ну- випадає) | *зів'янути* → *зів'ялий* | Природний (дуже поширений) |
```

What about `збанкрутілий`? The plan says: `збанкрутіти → збанкрутіле підприємство`.
I can add it where it gives examples of past active participles.
Text:
```
Let us look at the verb «зів'янути» (to wilt). We do not say «зів'янутий» or «зів'янулий», as these forms violate phonetic norms. Instead, we drop the «-ну-» to get the simplified stem «зів'я-», add the suffix «-л-», and arrive at the elegant and correct form «зів'ялий». The exact same rule applies to verbs like «розквітнути» (to blossom) and «змерзнути» (to freeze). Dropping the «-ну-» gives us «розквітлий» and «змерзлий». This specific nu-drop phenomenon is a fundamental feature of natural Ukrainian morphology.
```
I can add:
```
Dropping the «-ну-» gives us «розквітлий» and «змерзлий». For verbs without the «-ну-» suffix, the process is even simpler. For example, «збанкрутіти» (to go bankrupt) simply becomes «збанкрутілий» (bankrupt), as in «збанкрутіле підприємство» (a bankrupt enterprise). This specific nu-drop phenomenon...
```

Let's check the dialogue part again.
Is it exactly what was required?
Yes.

Let's check Exercises check.
`activity_hints` from plan:
1. reading: "Прочитайте текст про що таке дієприкметник? і дайте відповіді на запитання."
2. essay-response: "Напишіть 5 речень, використовуючи нову лексику з розділу «Активні дієприкметники теперішнього часу (-уч-/-юч-, -ач-/-яч-)»."
3. fill-in: "Вставте правильну граматичну форму у реченнях на тему що таке дієприкметник?."
4. error-correction: "Знайдіть і виправте помилки у реченнях на тему активні дієприкметники теперішнього часу (-уч-/-юч-, -ач-/-яч-)."
5. quiz: "Оберіть правильний варіант: лексика та граматика з розділу «Що таке дієприкметник?»."
6. match-up: "З'єднайте терміни з розділу «Активні дієприкметники теперішнього часу (-уч-/-юч-, -ач-/-яч-)» з їхніми визначеннями."

Injected markers in text:
- `<!-- INJECT_ACTIVITY: quiz-participle-definition -->` (matches quiz/reading)
- `<!-- INJECT_ACTIVITY: fill-in-present-formation -->` (matches fill-in)
- `<!-- INJECT_ACTIVITY: match-up-definitions -->` (matches match-up)
- `<!-- INJECT_ACTIVITY: essay-response-nature -->` (matches essay-response)
- `<!-- INJECT_ACTIVITY: error-correction-calques -->` (matches error-correction)
- `<!-- INJECT_ACTIVITY: reading-comprehension-nature -->` (matches reading)
- `<!-- INJECT_ACTIVITY: match-up-term-definitions -->` (matches match-up)
- `<!-- INJECT_ACTIVITY: quiz-active-participles-review -->` (matches quiz)

The plan has 6 hints, the text has 8 markers. That's perfectly fine (more exercises is okay, and the markers align with the hints).

Let's check translation of "дієприкметник". The text says:
"To better understand this dual nature, compare the regular verb "квітнути" and the participle "квітучий" formed from it."
Participle is correct.

Let's check if the text explains things in Ukrainian or English.
Mostly English for grammar explanations, but with deep Ukrainian examples.
"This mechanical transformation clearly shows how the verb's present tense stem merges with an adjectival ending..."
Is this acceptable for B1? Yes, grammar modules are often taught in English at B1, transitioning. But let's check the global context: "transitioning away from English instructions to full Ukrainian immersion... B1+ grammar modules; Narrative arcs".
Actually, B1 grammar is taught with TTT and extensive English explanations.

Wait! The text says: "The word «слідуючий» is never used to indicate order in a queue or a sequence of events; the only correct option is the adjective «наступний»." (This is perfect).

Let's double check "рухаючий момент".
"For instance, a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», and a physicist might discuss a «рухаючий момент»."
Fix: "For instance, a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», and biologists might classify a certain plant as «повзучий» (creeping)."
Wait, "повзучий" is a valid lexicalized participle (повзуча рослина).
Let's find Avramenko's examples of scientific terms.
Avramenko: "лежачі хворі, блукаючий нерв, а також у художньому стилі: синіючі далі".
I will replace:
```
For instance, a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», and a physicist might discuss a «рухаючий момент».
```
with:
```
For instance, a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», and clinical records might describe «лежачі хворі» (bedridden patients).
```

Let's check if there are other scientific terms.
"and a physicist might discuss a «рухаючий момент»." -> `find` text.
```yaml
- find: "«блукаючий нерв», and a physicist might discuss a «рухаючий момент»."
  replace: "«блукаючий нерв», and medical records might mention «лежачі хворі» (bedridden patients)."
```

Is there any other Russianism or Surzhyk?
"Версія А (небажана): «Існуючий план показує, що домінуючий тренд на ринку вимагає термінових змін. Завідуючий відділом підкреслив, що оточуюче середовище є вкрай нестабільним»."
This is perfect, it explicitly marks it as undesirable and provides Version B.

Let's check `описовий зворот` -> The descriptive clause. Perfect.

Let's check the word `ревучий водоспад`. Is it acceptable?
Text says: "Наприклад, коли ми кажемо «ревучий водоспад», ми чітко розуміємо, що водоспад сам виконує дію — він реве."
And later: "«ревучий водоспад» as natural adjective-like participles."
Let's check VESUM or dictionaries for `ревучий`.
 гіthought
CRITICAL INSTRUCTION 1: Specific tools > generic tools.
CRITICAL INSTRUCTION 2: Related tools: `mcp_rag_verify_word`.

Yes, `ревучий` is a valid adjective in Ukrainian.

What about `бігуча` in `бігуча дівчина`?
Text says: "saying «кричаща дитина» or «бігучий хлопчик» is completely unacceptable."
This is perfectly aligned with the lesson.

Wait, "Олень, що біжить крізь густий ранковий ліс"
"Його шлях пролягає туди, де спадає могутній ревучий водоспад."
"А високо в небі спокійно пливуть хмари, що мандрують над побілілими від снігу вершинами гір."
The translation logic is perfect.

Wait! The `activity_hints` in the Plan:
`- type: essay-response
  focus: "Напишіть 5 речень, використовуючи нову лексику з розділу «Активні дієприкметники теперішнього часу (-уч-/-юч-, -ач-/-яч-)»."`

The generated injected markers:
`<!-- INJECT_ACTIVITY: quiz-participle-definition -->`
`<!-- INJECT_ACTIVITY: fill-in-present-formation -->`
`<!-- INJECT_ACTIVITY: match-up-definitions -->`
`<!-- INJECT_ACTIVITY: essay-response-nature -->`
`<!-- INJECT_ACTIVITY: error-correction-calques -->`
`<!-- INJECT_ACTIVITY: reading-comprehension-nature -->`
`<!-- INJECT_ACTIVITY: match-up-term-definitions -->`
`<!-- INJECT_ACTIVITY: quiz-active-participles-review -->`

So `essay-response-nature` is for the past active participles section?
Wait, the hint specifically said "з розділу Активні дієприкметники теперішнього часу". But `essay-response` is injected at the end of the MINULYI CHAS section. "<!-- INJECT_ACTIVITY: essay-response-nature -->".
This is perfectly fine since the prompt asks me to check if the logic is correct and exercises match what was just taught. Since it's essay response about nature description using new vocabulary, it fits.

Let's review the Scoring Dimensions.
1. **Plan adherence** - 9/10
   - Missing consolidation table in the summary.
   - Missing vocabulary word `збанкрутілий`.
   - Covered all textbook references and all main conceptual points.
2. **Linguistic accuracy** - 8/10
   - Claim that `рухаючий момент` is a valid technical term used by physicists is factually wrong (`рухаючий` is a calque of `движущий`, Ukrainian physicists use `рушійний момент`).
3. **Pedagogical quality** - 10/10
   - Explanations are crystal clear.
   - Contrasts and exceptions are explained well.
4. **Vocabulary coverage** - 9/10
   - `збанкрутілий` missing. The rest are seamlessly woven into the text.
5. **Exercise quality** - 10/10
   - Markers match hints and are placed logically after concepts.
6. **Engagement & tone** - 10/10
   - Excellent, academic yet engaging tone.
7. **Structural integrity** - 10/10
   - 5478 words (target 4000). All sections present and properly ordered.
8. **Cultural accuracy** - 10/10
   - Specifically decolonized the language, actively combating Surzhyk. Quotes Ukrainian authors accurately.
9. **Dialogue & conversation quality** - 10/10
   - Natural documentary voice-over format fits the requirements perfectly.

Wait, let's look at the wording around `рухаючий момент`.
```
For instance, a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», and a physicist might discuss a «рухаючий момент». In these highly formalized contexts, the need for a concise, single-word term overrides the general stylistic preference for descriptive clauses.
```
I will supply a fix to correct it to:
```
For instance, a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», and a hospital might refer to bedridden patients as «лежачі хворі». In these highly formalized contexts, the need for a concise, single-word term overrides the general stylistic preference for descriptive clauses.
```

Let's find the exact text for the fix:
```yaml
- find: "«блукаючий нерв», and a physicist might discuss a «рухаючий момент»."
  replace: "«блукаючий нерв», and a hospital might have a ward for «лежачі хворі» (bedridden patients)."
```

Wait, `збанкрутілий` fix:
```yaml
- find: "«розквітлий» and «змерзлий». This specific nu-drop phenomenon"
  replace: "«розквітлий» and «змерзлий». For verbs without the «-ну-» suffix, the process is even simpler. For example, «збанкрутіти» (to go bankrupt) becomes «збанкрутілий», as in «збанкрутіле підприємство» (a bankrupt enterprise). This specific nu-drop phenomenon"
```
Wait, the actual text is:
```
Dropping the «-ну-» gives us «розквітлий» and «змерзлий». This specific nu-drop phenomenon is a fundamental feature of natural Ukrainian morphology.
```
So:
```yaml
- find: "Dropping the «-ну-» gives us «розквітлий» and «змерзлий». This specific nu-drop phenomenon"
  replace: "Dropping the «-ну-» gives us «розквітлий» and «змерзлий». For verbs without this suffix, the process is even simpler. For example, «збанкрутіти» (to go bankrupt) becomes «збанкрутілий», as in «збанкрутіле підприємство» (a bankrupt enterprise). This specific nu-drop phenomenon"
```

Let's do the Consolidation table fix:
```yaml
- find: "A \"reading student\" is never *читаючий учень*, but always *учень, який читає*."
  replace: "A \"reading student\" is never *читаючий учень*, but always *учень, який читає*.\n\n**Підсумкова таблиця: Утворення активних дієприкметників**\n\n| Час | Основа | Суфікс | Приклад | Статус |\n| :--- | :--- | :--- | :--- | :--- |\n| **Теперішній** | I дієвідміна | **-уч- / -юч-** | *квітнути* → *квітучий* | Обмежений |\n| **Теперішній** | II дієвідміна | **-ач- / -яч-** | *лежати* → *лежачий* | Обмежений |\n| **Минулий** | Інфінітив | **-л-** | *зникнути* → *зниклий* | Природний |"
```

Wait, I should make sure the exact `find` string is matched:
```
Finally, the most reliable strategy in Ukrainian is to replace problematic active participles with a subordinate clause starting with **який** (which) or **що** (that). A "reading student" is never *читаючий учень*, but always *учень, який читає*.
```
I will use the exact string.

Are there any other errors?
What about the `А. У якому реченні вжито неприродні для української мови слова?` that Avramenko's Grade 11 has? (Not required to include exactly everything).
I should double check if "зникнути -> зниклий" has nu-drop. Yes, зникнути -> зниклий.

Let's check the markdown for `Consolidation table`:
```markdown
| Час | Основа | Суфікс | Приклад | Статус |
| :--- | :--- | :--- | :--- | :--- |
| **Теперішній** | I дієвідміна | **-уч- / -юч-** | *квітнути* → *квітучий* | Обмежений (тільки сталі ознаки) |
| **Теперішній** | II дієвідміна | **-ач- / -яч-** | *лежати* → *лежачий* | Обмежений (тільки сталі ознаки) |
| **Минулий** | Інфінітив доконаного виду | **-л-** | *розквітнути* → *розквітлий* | Природний |
| **Минулий** | Інфінітив із суфіксом -ну- | **-л-** (суфікс -ну- випадає) | *зів'янути* → *зів'ялий* | Природний |
```

Wait, in the output, it should be in the `<fixes>` block.

Let me structure the review:
```markdown
## Linguistic Scan
- [Linguistic Accuracy] Issue with `рухаючий момент`. This is a direct calque of the Russian "движущий момент". Ukrainian uses the adjective "рушійний" (рушійний момент). Claiming it is a valid active participle used in science is factually wrong and teaches Surzhyk.

## Exercise Check
- All requested `activity_hints` from the plan are covered by the 8 `INJECT_ACTIVITY` markers.
- Placement of the markers follows the logical presentation of topics (e.g. `fill-in-present-formation` and `match-up-definitions` placed right after the formation rules for present active participles).
- `essay-response-nature` tests vocabulary correctly in the context of describing completed natural phenomena (past participles).

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Covers all requested sections and textbook references. However, it is missing the Consolidation Table from the summary section ("Consolidation table: formation summary with all suffix groups..."), and missed the recommended word `збанкрутілий`. |
| 2. Linguistic accuracy | 8/10 | The module incorrectly claims that «рухаючий момент» is a valid technical term for physicists. This is a calque of "движущий момент"; the correct scientific term is "рушійний момент" (adjective, not participle). All other decolonization points and explanations are perfect. |
| 3. Pedagogical quality | 10/10 | Exceptional pedagogy. The distinction between "квітнути" vs "квітучий" (ongoing vs permanent) is brilliant. The logical explanation of nu-dropping is very helpful. |
| 4. Vocabulary coverage | 9/10 | Covers 12/13 required words smoothly in context. Missed the recommended word "збанкрутілий". |
| 5. Exercise quality | 10/10 | Markers perfectly track the flow of information. Appropriate diversity of tasks. |
| 6. Engagement & tone | 10/10 | Authoritative, scholarly, but engaging (e.g., using "Imagine a word that combines..."). Excellent tone. |
| 7. Structural integrity | 10/10 | 5478 words easily clears the 4000 target. Sections are well-balanced. |
| 8. Cultural accuracy | 10/10 | High standard of decolonized language and direct instruction on avoiding Soviet-era calques. |
| 9. Dialogue & conversation quality | 10/10 | The "Nature documentary narration" meets the specific prompt completely. |

## Findings
[1. Plan adherence] [major]
Location: Section "Підсумок" (The entire final summary section)
Issue: The plan explicitly requires a "Consolidation table: formation summary with all suffix groups, their base conditions, and 2-3 model examples each." It was omitted.
Fix: Add the missing summary table at the end of the section.

[2. Linguistic accuracy] [critical]
Location: Section "Активні дієприкметники теперішнього часу..." (Paragraph starting "Understanding when and where...")
Issue: The module incorrectly claims `рухаючий момент` is a valid scientific term for a physicist. This is a calque of "движущий момент". The correct Ukrainian term is `рушійний момент` (which is an adjective, not a participle). 
Fix: Replace the physicist example with another correct Avramenko example of a medical participle, such as `лежачі хворі`.

[4. Vocabulary coverage] [minor]
Location: Section "Активні дієприкметники минулого часу (-л-)" (Paragraph starting "There is one important phonetic rule...")
Issue: The recommended vocabulary word `збанкрутілий` (past active participle) was not included in the text, despite being explicitly listed in the plan.
Fix: Add an example demonstrating the formation of `збанкрутілий` alongside `розквітлий` and `змерзлий`.

## Verdict: REVISE
The module is incredibly well-written and pedagogically sound. However, the factual error claiming `рухаючий` is a correct scientific term is critical, and the missing consolidation table from the plan requires a revision.

<fixes>
- find: "«блукаючий нерв», and a physicist might discuss a «рухаючий момент»."
  replace: "«блукаючий нерв», and clinical records might describe «лежачі хворі» (bedridden patients)."
- find: "Dropping the «-ну-» gives us «розквітлий» and «змерзлий». This specific nu-drop phenomenon"
  replace: "Dropping the «-ну-» gives us «розквітлий» and «змерзлий». For verbs without this suffix, the process is even simpler. For example, «збанкрутіти» (to go bankrupt) becomes «збанкрутілий», as in «збанкрутіле підприємство» (a bankrupt enterprise). This specific nu-drop phenomenon"
- find: "A \"reading student\" is never *читаючий учень*, but always *учень, який читає*."
  replace: "A \"reading student\" is never *читаючий учень*, but always *учень, який читає*.\n\n**Підсумкова таблиця: Утворення активних дієприкметників**\n\n| Час | Основа | Суфікс | Приклад | Статус |\n| :--- | :--- | :--- | :--- | :--- |\n| **Теперішній** | I дієвідміна | **-уч- / -юч-** | *квітнути* → *квітучий* | Обмежений (переважно сталі ознаки) |\n| **Теперішній** | II дієвідміна | **-ач- / -яч-** | *лежати* → *лежачий* | Обмежений (переважно сталі ознаки) |\n| **Минулий** | Інфінітив доконаного виду | **-л-** | *зникнути* → *зниклий* | Природний (поширений) |\n| **Минулий** | Інфінітив із суфіксом -ну- | **-л-** (суфікс -ну- випадає) | *зів'янути* → *зів'ялий* | Природний (поширений) |"
</fixes>
```

Let me double check the `find` text exactness.
Module text:
1) `"«блукаючий нерв», and a physicist might discuss a «рухаючий момент»."` - Wait, text says:
`For instance, a medical professional will correctly refer to the vagus nerve as the «блукаючий нерв», and a physicist might discuss a «рухаючий момент».` - Yes, EXACT.

2) `"Dropping the «-ну-» gives us «розквітлий» and «змерзлий». This specific nu-drop phenomenon"`
Text:
`Dropping the «-ну-» gives us «розквітлий» and «змерзлий». This specific nu-drop phenomenon is a fundamental feature of natural Ukrainian morphology.` - Yes, EXACT.

3) `"A "reading student" is never *читаючий учень*, but always *учень, який читає*."`
Text:
`A "reading student" is never *читаючий учень*, but always *учень, який читає*.` - Yes, EXACT.

Is the English quote "A "reading student" is never *читаючий учень*," EXACT?
Text says:
`A "reading student" is never *читаючий учень*, but always *учень, який читає*.`
Yes.

Let's do a quick final check of the generated content to ensure there are no other stray Russian characters or mistakes.
`«-уть»` or `«-ють»`, `«-ать»` or `«-ять»`
All look fine. No Russian characters detected.
"Суб'єкт" (apostrophe ok)
"в'янучий" (apostrophe ok)

Are there any missing H2 headings?
Plan:
- Що таке дієприкметник?
- Активні дієприкметники теперішнього часу (-уч-/-юч-, -ач-/-яч-)
- Активні дієприкметники минулого часу (-л-)
- Чого уникати: русизми у дієприкметниках
- Дієприкметник у тексті
- Підсумок та перехід до M58

Module H2s:
`## Що таке дієприкметник?`
`## Активні дієприкметники теперішнього часу (-уч-/-юч-, -ач-/-яч-)`
`## Активні дієприкметники минулого часу (-л-)`
`## Чого уникати: русизми у дієприкметниках`
`## Дієприкметник у тексті`
`## Підсумок`
The last heading in module is `## Підсумок` instead of `## Підсумок та перехід до M58`.
Wait, the plan outline specifies the name: `- section: "Підсумок та перехід до M58"`.
Module used `## Підсумок`.
Should I replace it to exact text? Yes.

```yaml
- find: "## Підсумок\n\nДієприкметник — це форма"
  replace: "## Підсумок та перехід до M58\n\nДієприкметник — це форма"
```
Wait, the text is:
```
## Підсумок

Дієприкметник — це форма, яка поєднує властивості дієслова та прикметника,
```
Let me write the fix simpler:
```yaml
- find: "## Підсумок\n\nДієприкметник — це форма"
  replace: "## Підсумок та перехід до M58\n\nДієприкметник — це форма"
```
But Markdown text can sometimes have variable newlines. Let me just replace the heading itself.

```yaml
- find: "## Підсумок\n"
  replace: "## Підсумок та перехід до M58\n"
```
Wait, if there are multiple newlines, it could fail if it doesn't match perfectly. I'll include the next word to make it unique.
```yaml
- find: "## Підсумок\n\nДієприкметник — це форма"
  replace: "## Підсумок та перехід до M58\n\nДієприкметник — це форма"
```

Let's check the text exactly:
```
<!-- INJECT_ACTIVITY: reading-comprehension-nature -->

## Підсумок

Дієприкметник — це форма, яка поєднує властивості
```

```yaml
- find: "## Підсумок\n\nДієприкметник — це форма"
  replace: "## Підсумок та перехід до M58\n\nДієприкметник — це форма"
```
This is a `minor` Plan Adherence issue.

Everything is well accounted for. I'm ready to construct the final response.## Linguistic Scan
- [Linguistic Accuracy] Issue with `рухаючий момент`. The text incorrectly claims this is a valid scientific term for physicists. This is a direct calque of the Russian "движущий момент". In Ukrainian physics, the correct term is the adjective "рушійний" (рушійний момент). Claiming "рухаючий" is a valid active participle used in Ukrainian science is factually wrong and teaches Surzhyk.

## Exercise Check
- All 6 requested `activity_hints` from the plan are covered by the 8 `INJECT_ACTIVITY` markers. 
- Placement of the markers perfectly follows the logical presentation of topics (e.g. `fill-in-present-formation` and `match-up-definitions` placed right after the formation rules for present active participles).
- `essay-response-nature` tests vocabulary correctly in the context of describing completed natural phenomena (past participles).
- The DSL formatting for exercises is deferred to the pipeline, but the logic requested by the hints is sound.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Covers all requested sections and textbook references smoothly. However, it omitted the explicit Consolidation Table from the summary section ("Consolidation table: formation summary with all suffix groups..."), missed the recommended word `збанкрутілий`, and slightly altered the final H2 heading from "Підсумок та перехід до M58" to just "Підсумок". |
| 2. Linguistic accuracy | 8/10 | The module incorrectly claims that «рухаючий момент» is a valid technical term for physicists. This is a Russian calque; the correct scientific term is "рушійний момент" (adjective, not participle). All other decolonization points, grammar rules, and explanations of calques (e.g. "бігуча", "миючий") are perfectly correct. |
| 3. Pedagogical quality | 10/10 | Exceptional pedagogy. The distinction between "квітнути" vs "квітучий" (ongoing vs permanent) is brilliant. The logical explanation of nu-dropping is very helpful. |
| 4. Vocabulary coverage | 9/10 | Covers all required words seamlessly in context. Missed the recommended word "збанкрутілий". |
| 5. Exercise quality | 10/10 | Markers perfectly track the flow of information. Appropriate diversity of tasks matching the plan. |
| 6. Engagement & tone | 10/10 | Authoritative, scholarly, yet engaging (e.g., "Imagine a word that combines..."). Excellent tone for B1 learners. |
| 7. Structural integrity | 10/10 | At 5478 words, it safely clears the 4000 target. Sections are well-balanced and properly sequenced. |
| 8. Cultural accuracy | 10/10 | High standard of decolonized language and direct instruction on avoiding Soviet-era calques. Use of Ukrainian literary examples (Stelmakh, Kotsiubynsky) is excellent. |
| 9. Dialogue & conversation quality | 10/10 | The "Nature documentary narration" meets the specific prompt completely, utilizing natural descriptive clauses ("олень, що біжить"). |

## Findings
[1. Plan adherence] [major]
Location: Section "Підсумок" (The entire final summary section)
Issue: The plan explicitly requires a "Consolidation table: formation summary with all suffix groups, their base conditions, and 2-3 model examples each." It was omitted.
Fix: Add the missing summary table at the end of the section.

[2. Linguistic accuracy] [critical]
Location: Section "Активні дієприкметники теперішнього часу..." (Paragraph starting "Understanding when and where...")
Issue: The module incorrectly claims `рухаючий момент` is a valid scientific term for a physicist. This is a calque of "движущий момент". The correct Ukrainian term is `рушійний момент` (which is an adjective, not a participle). 
Fix: Replace the physicist example with another correct Avramenko example of a medical participle, such as `лежачі хворі` (bedridden patients).

[4. Vocabulary coverage] [minor]
Location: Section "Активні дієприкметники минулого часу (-л-)" (Paragraph starting "There is one important phonetic rule...")
Issue: The recommended vocabulary word `збанкрутілий` (past active participle) was not included in the text, despite being explicitly listed in the plan's examples.
Fix: Add an example demonstrating the formation of `збанкрутілий` alongside `розквітлий` and `змерзлий`.

[1. Plan adherence] [minor]
Location: Final H2 Heading ("## Підсумок")
Issue: The final heading does not perfectly match the explicit plan string `## Підсумок та перехід до M58`.
Fix: Rename the heading.

## Verdict: REVISE
The module is incredibly well-written, thoroughly engaging, and pedagogically sound. The deep-dive into decolonized forms and nuanced translations is stellar. However, the factual error claiming `рухаючий` is a correct scientific term is critical, and the missing consolidation table from the plan requires a revision.

<fixes>
- find: "«блукаючий нерв», and a physicist might discuss a «рухаючий момент»."
  replace: "«блукаючий нерв», and clinical records might describe «лежачі хворі» (bedridden patients)."
- find: "Dropping the «-ну-» gives us «розквітлий» and «змерзлий». This specific nu-drop phenomenon"
  replace: "Dropping the «-ну-» gives us «розквітлий» and «змерзлий». For verbs without this suffix, the process is even simpler. For example, «збанкрутіти» (to go bankrupt) becomes «збанкрутілий», as in «збанкрутіле підприємство» (a bankrupt enterprise). This specific nu-drop phenomenon"
- find: "A \"reading student\" is never *читаючий учень*, but always *учень, який читає*."
  replace: "A \"reading student\" is never *читаючий учень*, but always *учень, який читає*.\n\n**Підсумкова таблиця: Утворення активних дієприкметників**\n\n| Час | Основа | Суфікс | Приклад | Статус |\n| :--- | :--- | :--- | :--- | :--- |\n| **Теперішній** | I дієвідміна | **-уч- / -юч-** | *квітнути* → *квітучий* | Обмежений (переважно сталі ознаки) |\n| **Теперішній** | II дієвідміна | **-ач- / -яч-** | *лежати* → *лежачий* | Обмежений (переважно сталі ознаки) |\n| **Минулий** | Інфінітив доконаного виду | **-л-** | *зникнути* → *зниклий* | Природний (поширений) |\n| **Минулий** | Інфінітив із суфіксом -ну- | **-л-** (суфікс -ну- випадає) | *зів'янути* → *зів'ялий* | Природний (поширений) |"
- find: "## Підсумок\n\nДієприкметник — це форма"
  replace: "## Підсумок та перехід до M58\n\nДієприкметник — це форма"
</fixes>
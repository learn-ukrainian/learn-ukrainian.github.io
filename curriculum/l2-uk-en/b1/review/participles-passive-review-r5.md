## Linguistic Scan
Linguistic errors found:
1. "Слово «варений» — це прикметник недоконаного виду" — Grammatical contradiction; adjectives do not have the category of aspect (вид) in Ukrainian grammar.
2. "приймає дію на себе" — Calque from Russian "принимает действие на себя".

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in -->` - OK
- `<!-- INJECT_ACTIVITY: match-up -->` - OK
- `<!-- INJECT_ACTIVITY: error-correction -->` - OK
- `<!-- INJECT_ACTIVITY: quiz -->` - Misplaced based on plan. Plan focus is "значення", but injected in Section 4.
- `<!-- INJECT_ACTIVITY: reading -->` - Misplaced based on plan. Plan focus is "значення", but injected in Section 5.
- `<!-- INJECT_ACTIVITY: essay-response -->` - OK

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The module missed the transformation exercises (передати → переданий) from Section 5, missed the consolidation table from Section 6, and previewed M23 instead of M59 in the summary. |
| 2. Linguistic accuracy | 7/10 | CRITICAL: The text falsely claimed an adjective has aspect ("Слово «варений» — це прикметник недоконаного виду"). It also contained the calque "приймає дію на себе". |
| 3. Pedagogical quality | 8/10 | The grammatical contradiction about adjective aspect causes pedagogical confusion, but the rest of the module has an excellent flow and uses good contextual examples. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary was used well in context, but the recommended word "побачений" was missed in the examples. |
| 5. Exercise quality | 8/10 | The activity markers deviate from the exact plan focuses (e.g., placing the `quiz` about "значення" in Section 4), though spreading them out is pedagogically sound. |
| 6. Engagement & tone | 10/10 | The tone is engaging, natural, and avoids corporate phrasing. |
| 7. Structural integrity | 7/10 | The word count (3139 words) is significantly below the target of 4000 words. |
| 8. Cultural accuracy | 10/10 | Excellent cultural context with the Mariinskyi Palace dialogue and accurate differentiation between Ukrainian syntax and Russian short forms. |
| 9. Dialogue & conversation quality | 10/10 | The dialogue is natural and demonstrates the grammar perfectly in context. |

## Findings
[1. Plan adherence] [major]
Location: Section "Підсумок", last paragraph: "In the upcoming modules, you will use these exact words to build impersonal **-но** and **-то** forms..."
Issue: The plan explicitly required a preview of M59 (Дієприкметниковий зворот), not a preview of -но/-то forms.
Fix: Replace with "In the next module (M59), you will learn how to combine these participles with dependent words to form a **дієприкметниковий зворот** (participle phrase), which has its own specific punctuation rules."

[2. Linguistic accuracy] [critical]
Location: Section "Дієприкметник чи прикметник?", paragraph 3: "Слово «варений» — це прикметник недоконаного виду."
Issue: Factual grammatical error. Adjectives do not have the category of aspect (вид) in Ukrainian grammar. Calling "варений" an adjective of imperfective aspect contradicts both itself and basic grammar.
Fix: Replace with "Слово «варений» — це звичайний прикметник, який не має виду. Але якщо додати префікс і утворити слово «зварений», це вже справжній пасивний дієприкметник доконаного виду."

[3. Linguistic accuracy] [major]
Location: Section "Пасивні дієприкметники: значення", paragraph 1: "Предмет тут не є активним учасником процесу, він лише приймає дію на себе."
Issue: Calque from Russian "принимает действие на себя". Natural Ukrainian uses "зазнає дії" or "дія спрямована на нього".
Fix: Replace with "Предмет тут не є активним учасником процесу, дія просто спрямована на нього."

[4. Plan adherence] [major]
Location: Section "Підсумок", first paragraph.
Issue: The plan required a "Consolidation table: complete formation algorithm with suffix selection tree" and a "Quick-reference alternation chart", but the text provides only prose.
Fix: Replace the prose summary of formation rules with a markdown table and bullet points matching the plan requirements.

[5. Plan adherence] [major]
Location: Section "Практика: пасивні дієприкметники у тексті", between the dialogue and the transformation explanation.
Issue: The transformation exercises requested by the plan (передати → переданий, одягнути → одягнутий, etc.) are missing from the text.
Fix: Inject the transformation list before the transformation paragraph.

## Verdict: REVISE
The module contains a critical grammatical error regarding adjectives and aspect, a calque, and misses several specific elements explicitly requested in the plan (table, transformation exercises, M59 preview). Fixes are provided below to correct the errors and inject the missing content.

<fixes>
- find: "Предмет тут не є активним учасником процесу, він лише приймає дію на себе."
  replace: "Предмет тут не є активним учасником процесу, дія просто спрямована на нього."
- find: "Слово «варений» — це прикметник недоконаного виду. Але якщо додати префікс і утворити слово «зварений», це вже стовідсотковий пасивний дієприкметник доконаного виду."
  replace: "Слово «варений» — це звичайний прикметник, який не має виду. Але якщо додати префікс і утворити слово «зварений», це вже справжній пасивний дієприкметник доконаного виду."
- find: "Розглянемо приклад трансформації активного стану на пасивний. Активне речення: «Італійські майстри зробили цю ліпнину»."
  replace: "Щоб закріпити навички, спробуйте утворити пасивні дієприкметники від таких дієслів: передати (переданий), одягнути (одягнутий), заплести (заплетений), зварити (зварений), помити (помитий), замести (заметений), пофарбувати (пофарбований).\n\nРозглянемо приклад трансформації активного стану на пасивний. Активне речення: «Італійські майстри зробили цю ліпнину»."
- find: "Ось зведений алгоритм творення пасивних дієприкметників. Спочатку знайдіть основу інфінітива. Якщо основа закінчується на голосний «а», використовуйте суфікс «-н-». Наприклад, від слова «прочитати» утворюється «прочитаний». Якщо основа закінчується на приголосний, «и» або «і», додавайте суфікс «-ен-» та обов'язково перевіряйте чергування приголосних. Від слова «сплатити» утворюється «сплачений», де «т» змінюється на «ч». Якщо основа односкладова, використовуйте суфікс «-т-», як у слові «митий». Пам'ятайте, що готові дієприкметники відмінюються за родами, числами та відмінками точно так само, як звичайні прикметники твердої групи.\n\n> *Here is the summary algorithm for forming passive participles. First, find the infinitive stem. If the stem ends in the vowel \"а\", use the suffix \"-н-\". For example, from the word \"прочитати\" we form \"прочитаний\". If the stem ends in a consonant, \"и\", or \"і\", add the suffix \"-ен-\" and always check for consonant alternations. From the word \"сплатити\" we form \"сплачений\", where \"т\" changes to \"ч\". If the stem is monosyllabic, use the suffix \"-т-\", as in the word \"митий\". Remember that the finished participles decline by gender, number, and case exactly like regular adjectives of the hard group.*"
  replace: "Ось зведений алгоритм творення пасивних дієприкметників:\n\n| Кінцевий звук основи | Суфікс | Приклад творення |\n| :--- | :--- | :--- |\n| Голосний **-а-** | **-н-** | прочитати → прочитаний |\n| Приголосний, **-и-**, **-і-** | **-ен-** | побачити → побачений |\n| Односкладова основа | **-т-** | мити → митий |\n\n*Швидка довідка чергувань перед -ен-: д→дж, т→ч, з→ж, с→ш, б→бл.*\nГотові дієприкметники відмінюються як звичайні прикметники твердої групи.\n\n> *Here is the summary algorithm for forming passive participles:\n> - Stem ending in **-а-** gets the **-н-** suffix (прочитати → прочитаний).\n> - Stem ending in a consonant, **-и-**, or **-і-** gets the **-ен-** suffix (побачити → побачений).\n> - Monosyllabic stems get the **-т-** suffix (мити → митий).\n> \n> Quick-reference alternations before -ен-: д→дж, т→ч, з→ж, с→ш, б→бл.*"
- find: "In the upcoming modules, you will use these exact words to build impersonal **-но** and **-то** forms (like **відчинено** or **зроблено**), which are extremely common and natural in everyday communication."
  replace: "In the next module (M59), you will learn how to combine these participles with dependent words to form a **дієприкметниковий зворот** (participle phrase), which has its own specific punctuation rules."
</fixes>
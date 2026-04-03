## Linguistic Scan
Found 1 critical linguistic error (contradiction with a grammatical rule taught later in the same text). No Surzhyk, Russian characters, or Calques detected.
- **Critical grammatical error**: «Новий важливий закон ухвалено Верховною Радою». As the text correctly explains in Section 3, forms ending in -но/-то (like *ухвалено*) cannot be used with an instrumental agent (*Верховною Радою*).

## Exercise Check
All 5 required exercises are present, logically sequenced, and match the plan's `activity_hints`.
1. `<!-- INJECT_ACTIVITY: fill-in... -->` (Placed after section 3 "Форми на -но/-то"). Tests the just-taught morphology.
2. `<!-- INJECT_ACTIVITY: match-up... -->` (Placed after section 4 "Порівняння"). 
3. `<!-- INJECT_ACTIVITY: error-correction... -->` (Placed after section 4). Perfect placement for stylistic revision.
4. `<!-- INJECT_ACTIVITY: quiz... -->` (Placed after section 4). Tests general comprehension.
5. `<!-- INJECT_ACTIVITY: sentence-builder... -->` (Placed in section 5 "Практика"). Follows reading passage to practice transformations.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The text follows the plan structure perfectly. However, it copies a flawed example from the plan's prompt ("Закон ухвалено Верховною Радою") which contradicts the rules taught in the module. |
| 2. Linguistic accuracy | 8/10 | The text contains a critical grammatical error in Section 1: «Новий важливий закон ухвалено Верховною Радою». The -но/-то forms NEVER take the instrumental case for the agent. |
| 3. Pedagogical quality | 8/10 | The error above creates massive pedagogical confusion. Section 1 shows an example of using the instrumental case with -но/-то, while Section 3 explicitly forbids it: "ми ніколи не використовуємо орудний відмінок для прямого позначення виконавця дії разом із цими формами на -но або -то". |
| 4. Vocabulary coverage | 10/10 | All required vocabulary is smoothly integrated and contextualized (пасивний стан, активний стан, будуватися, називатися, знаходитися, використовуватися, збудовано, виконано, прочитано, ухвалено, канцелярит, перехідне/неперехідне дієслово, орудний відмінок). |
| 5. Exercise quality | 10/10 | All 5 markers are present, appropriately placed after the relevant sections, and precisely match the types and focus specified in the plan. |
| 6. Engagement & tone | 8/10 | Deducting points for meta-commentary ("Зробімо зараз значно глибший порівняльний аналіз") and generic enthusiasm that tells instead of shows ("Вона максимально точно передає найтонші відтінки... Це гарантовано буде неймовірно цікава та корисна подорож..."). |
| 7. Structural integrity | 10/10 | Clean Markdown formatting. Headings precisely match the plan. |
| 8. Cultural accuracy | 10/10 | Excellent points about Ukrainian's structural preference for the active voice and the organic nature of -но/-то compared to bureaucratic -ся passives. |
| 9. Dialogue & conversation quality | 8/10 | The dialogue in the Palace of Culture is stilted and robotic ("Добрий день! Це виглядає неймовірно сучасно і дуже вражає!", "Це справді чудово видно голим оком навіть зараз"). Needs more natural phrasing. |

## Findings
[2. Linguistic accuracy] [CRITICAL]
Location: Section "Активний і пасивний стан", paragraph 3: «Це трапляється, коли ми маємо на увазі державну установу чи велику організацію як колективного виконавця. Наприклад: «Новий важливий закон **ухвалено** *(has been adopted)* Верховною Радою вчора ввечері».»
Issue: Grammatical error that contradicts the module's own teaching. -Но/-то forms cannot be used with an agent in the instrumental case (*Верховною Радою*).
Fix: Rewrite the explanation to show how official documents use passive to omit the agent and state the action as an objective fact.

[9. Dialogue & conversation quality] [MAJOR]
Location: Section "Активний і пасивний стан", dialogue: «> — **Журналіст:** Добрий день! Це виглядає неймовірно сучасно і дуже вражає!... Це справді чудово видно голим оком навіть зараз.»
Issue: The dialogue sounds like a robotic textbook translation rather than a natural conversation between an architect and a journalist.
Fix: Smooth out the journalist's phrasing to sound more organic ("Зал справді виглядає...", "Масштаб робіт справді вражає").

[6. Engagement & tone] [MINOR]
Location: Section "Порівняння трьох конструкцій", paragraph 2: «Зробімо зараз значно глибший **порівняльний аналіз** *(contrastive analysis)* на прикладі однієї дуже простої, типової побутової ситуації.»
Issue: Heavy meta-commentary breaking the fourth wall. 
Fix: Simplify to a more direct transition: "Для кращого розуміння проаналізуємо ці конструкції..."

[6. Engagement & tone] [MINOR]
Location: Section "Підсумок та перехід до M24", paragraph 3: «Вона максимально точно передає найтонші відтінки змісту лише за допомогою хитрого словотворення. Це гарантовано буде неймовірно цікава та корисна подорож у найглибшу структуру українського дієслова!»
Issue: Generic enthusiasm and telling instead of showing at the end of the module.
Fix: Condense to a more professional, grounded summary of the upcoming module.

## Verdict: REVISE
The text is generally excellent, but the inclusion of a flawed example with the instrumental case on a -но/-то form in the first section creates a critical pedagogical contradiction with the rules taught in the third section.

<fixes>
- find: "По-четверте, офіційні юридичні документи часто використовують пасив. Це трапляється, коли ми маємо на увазі державну установу чи велику організацію як колективного виконавця. Наприклад: «Новий важливий закон **ухвалено** *(has been adopted)* Верховною Радою вчора ввечері». У таких специфічних випадках пасивні конструкції чудово виконують свою функцію."
  replace: "По-четверте, офіційні юридичні документи часто використовують пасив. Це трапляється, коли подіям надається статус офіційного факту, а не особистої ініціативи. Наприклад, замість активного стану застосовують безособову констатацію: «Новий важливий закон **ухвалено** *(has been adopted)* вчора ввечері». У таких специфічних випадках пасивні конструкції чудово виконують свою функцію."
- find: "> — **Журналіст:** Добрий день! Це виглядає неймовірно сучасно і дуже вражає! *(Good day! This looks incredibly modern and very impressive!)*\n> — **Архітектор:** Дякую! Усі ці високі стіни були пофарбовані лише минулого місяця, а вхід буде відкрито для широкої публіки вже завтра вранці. *(Thank you! All these high walls were painted just last month, and the entrance will be opened for the general public already tomorrow morning.)*\n> — **Журналіст:** Це справді чудово видно голим оком навіть зараз. Дуже вам дякую за цікаву екскурсію! *(That is truly perfectly visible to the naked eye even now. Thank you very much for the interesting tour!)*"
  replace: "> — **Журналіст:** Добрий день! Зал справді виглядає неймовірно сучасно. *(Good day! The hall truly looks incredibly modern.)*\n> — **Архітектор:** Дякую! Усі ці високі стіни були пофарбовані лише минулого місяця, а вхід буде відкрито для широкої публіки вже завтра вранці. *(Thank you! All these high walls were painted just last month, and the entrance will be opened for the general public already tomorrow morning.)*\n> — **Журналіст:** Масштаб робіт справді вражає. Дуже вам дякую за цікаву екскурсію! *(The scale of the work is truly impressive. Thank you very much for the interesting tour!)*"
- find: "Зробімо зараз значно глибший **порівняльний аналіз** *(contrastive analysis)* на прикладі однієї дуже простої, типової побутової ситуації. Уявіть собі звичайнісіньке коротке речення: «Мама зараз миє вікно»."
  replace: "Для кращого розуміння проаналізуємо ці конструкції на прикладі простої типової побутової ситуації. Уявіть собі звичайнісіньке коротке речення: «Мама зараз миє вікно»."
- find: "Вона максимально точно передає найтонші відтінки змісту лише за допомогою хитрого словотворення. Це гарантовано буде неймовірно цікава та корисна подорож у найглибшу структуру українського дієслова!"
  replace: "Саме завдяки цьому ми можемо точно передавати найтонші відтінки змісту. Від розуміння станів та видів дієслова ми перейдемо до механіки його творення."
</fixes>

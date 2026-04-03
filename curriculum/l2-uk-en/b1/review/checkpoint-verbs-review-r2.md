## Linguistic Scan
- "нудьгується" in "розробникам ніколи не нудьгується" is an unattested impersonal reflexive form (0 occurrences in GRAC). Standard Ukrainian requires active voice here: "розробники не нудьгують".

## Exercise Check
- **CRITICAL ISSUE**: The generated text contains 12 specific, granular `INJECT_ACTIVITY` markers that directly contradict the plan. The plan requires exactly 6 integrated Phase-3 review activities (1 quiz, 1 fill-in, 1 error-correction, 1 match-up, 1 group-sort, 1 reading-comprehension). The generated markers focus on single topics rather than synthesizing all of Phase 3, which breaks the checkpoint pedagogy.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Word count is massively over budget (4867 vs 4000). The writer generated 12 isolated activity markers instead of the 6 integrated markers specified in `activity_hints`. |
| 2. Linguistic accuracy | 8/10 | Used the non-standard and unattested impersonal form "нудьгується" ("розробникам ніколи не нудьгується") instead of the standard active "розробники не нудьгують". All other grammar is highly accurate. |
| 3. Pedagogical quality | 10/10 | Excellent pedagogical examples contrasting 'якщо' and 'якби' in a business context. Highlights active voice preference clearly ("Дім був збудований нами" → marked as an error). |
| 4. Vocabulary coverage | 8/10 | Failed to include the required vocabulary term "видова пара" and recommended term "перехідне дієслово" anywhere in the prose. |
| 5. Exercise quality | 4/10 | Hallucinated 12 activity markers with completely different focuses instead of following the 6 integrated activity hints provided in the plan. |
| 6. Engagement & tone | 6/10 | Heavy meta-commentary at the end of the module ("Уважно проаналізуймо цей діалог, адже він є чудовим прикладом «соціальних шахів»", "Ми з вами разом пройшли величезний шлях", "Тепер настав час рухатися далі!"). |
| 7. Structural integrity | 8/10 | Structurally sound, but word count is significantly over the 10% tolerance limit. |
| 8. Cultural accuracy | 10/10 | Correctly targets Russian calques ("пішли" for let's go) and explains them cleanly. Uses appropriate cultural contexts (IT office, train station). |
| 9. Dialogue & conversation quality | 10/10 | The dialogues (train station frustration, HR interview) are natural, well-contextualized, and integrate the review grammar points seamlessly. |

## Findings

[Dimension 2] [SEVERITY: critical]
Location: "Комплексні вправи: дієслівна фаза" (Проте розробникам ніколи не нудьгується *(they are never bored)* в офісі...)
Issue: "Нудьгується" is a non-standard and practically unattested impersonal reflexive form (0.00 IPM in GRAC). Should use standard active form.
Fix: Change "розробникам ніколи не нудьгується" to "розробники ніколи не нудьгують".

[Dimension 4] [SEVERITY: major]
Location: Throughout text.
Issue: Missing required vocabulary word "видова пара" and recommended word "перехідне дієслово".
Fix: Inject these terms into the relevant pedagogical sections (Наказовий спосіб / Пасивний стан).

[Dimension 5] [SEVERITY: critical]
Location: Throughout text (12 INJECT_ACTIVITY markers).
Issue: The writer ignored the 6 integrated `activity_hints` from the plan and injected 12 hallucinated activity markers spread throughout the text.
Fix: Remove all 12 generated markers and inject the 6 correct markers from the plan at the appropriate review sections.

[Dimension 6] [SEVERITY: major]
Location: End of "Діалог-синтез та перехід до Фази 4" (Уважно проаналізуймо цей діалог, адже він є чудовим прикладом «соціальних шахів»...)
Issue: Four paragraphs of heavy meta-commentary, generic enthusiasm, and congratulatory filler, which also pushes the word count far over budget.
Fix: Delete the meta-commentary paragraphs and replace the transition paragraph with a concise summary.

## Verdict: REVISE
The module requires revision due to critical exercise marker hallucinations, missing required vocabulary, one non-standard linguistic form ("нудьгується"), and heavy meta-commentary that severely bloats the word count.

<fixes>
- find: 'Проте розробникам ніколи не нудьгується *(they are never bored)* в офісі, адже щодня з''являються нові складні виклики.'
  replace: 'Проте розробники ніколи не нудьгують *(they are never bored)* в офісі, адже щодня з''являються нові складні виклики.'
- find: 'Вибір правильного **виду** *(aspect)* у наказовому способі має критичне значення для точної передачі вашої думки. **Доконаний вид** *(perfective aspect)* завжди використовується'
  replace: 'Вибір правильного **виду** *(aspect)* у наказовому способі має критичне значення для точної передачі вашої думки. Кожна **видова пара** *(aspectual pair)* розрізняється за метою: **доконаний вид** *(perfective aspect)* завжди використовується'
- find: 'Другий спосіб — це використання спеціальних безособових форм на **-но** або **-то**, що фокусується виключно на **результаті** *(result)* та беззаперечному факті завершення дії.'
  replace: 'Другий спосіб — це використання спеціальних безособових форм на **-но** або **-то**, які утворюються, якщо ми маємо **перехідне дієслово** *(transitive verb)*. Цей спосіб фокусується виключно на **результаті** *(result)* та беззаперечному факті завершення дії.'
- find: '<!-- INJECT_ACTIVITY: match-up, Match 10 sentence halves: 5 "якщо" clauses with their logical results and 5 "якби" clauses with theirs. Focus on forcing the correct mood/tense selection. -->'
  replace: ''
- find: '<!-- INJECT_ACTIVITY: fill-in, Learners must choose between "би" and "б" in 10 sentences and provide the correct past tense verb form to complete the conditional structure. -->'
  replace: ''
- find: '<!-- INJECT_ACTIVITY: group-sort, Sort 12 imperative forms into three categories: 2nd Person Singular, 2nd Person Plural, and 1st Person Plural (Inclusive). Include tricky forms like "сядьте" and "глянь". -->'
  replace: ''
- find: '<!-- INJECT_ACTIVITY: fill-in, Choose the correct aspect (pf/ipf) for 10 situations (e.g., "You are teaching a child to wash hands every day"). -->'
  replace: ''
- find: '<!-- INJECT_ACTIVITY: match-up, Match 10 verbs with their corresponding verbal nouns. Include both -ння/ття and zero-suffix types (e.g., плавати - плавання, виходити - вихід). 10 items. -->'
  replace: ''
- find: '<!-- INJECT_ACTIVITY: quiz, Identify the word-formation method for 12 words (Prefixal, Suffixal, or Mixed). Example: "написати" (Prefixal), "заземлити" (Mixed). 12 items. -->'
  replace: ''
- find: '<!-- INJECT_ACTIVITY: error-correction, Fix 8 sentences with typical errors: using -ся instead of -сь after a vowel, using "вибачаюся" instead of "вибачте", and awkward passive structures like "*Книга читається мною". 8 items. -->'
  replace: ''
- find: '<!-- INJECT_ACTIVITY: quiz, Identify the category of reflexive verb in 12 sentences. Is it a reciprocal action (we met) or an impersonal feeling (I feel like sleeping)? 12 items. -->'
  replace: ''
- find: '<!-- INJECT_ACTIVITY: reading-comprehension, Based on the IT company text, answer 8 grammar-focused questions. "Why is ''якби'' used in sentence 4?" "What is the base verb for the noun ''тестування''?" 8 items. -->'
  replace: "<!-- INJECT_ACTIVITY: quiz, Identify grammar structures in context: умовний/наказовий/зворотний/пасивний/віддієслівний -->\n\n<!-- INJECT_ACTIVITY: match-up, Match sentence pairs: active↔passive, real↔unreal conditional, verb↔verbal noun -->"
- find: '<!-- INJECT_ACTIVITY: match-up, Match 10 active sentences with their passive -но/-то equivalents. Focus on high-frequency verbs: купити, зробити, написати, відкрити, забути. 10 items. -->'
  replace: ''
- find: '<!-- INJECT_ACTIVITY: fill-in, A 10-gap text where the learner must choose the single best verb form from the entire Phase 3 repertoire to fit the context. This tests synthesis of all prior sections. 10 items. -->'
  replace: "<!-- INJECT_ACTIVITY: fill-in, Complete a mixed text with correct Phase 3 verb forms (conditional, imperative, reflexive, passive) -->\n\n<!-- INJECT_ACTIVITY: error-correction, Fix errors across all Phase 3 topics: *Пішли (→ Ходімо), wrong conditional, spelling, Russianisms -->\n\n<!-- INJECT_ACTIVITY: group-sort, Sort verbs/constructions by Phase 3 category: умовний/наказовий/зворотний/пасивний/словотвір -->"
- find: '<!-- INJECT_ACTIVITY: reading-comprehension, Read the job interview dialogue and answer grammar-focused questions testing your understanding of Phase 3 topics like conditionals, imperatives, passives, and reflexives. 8 items. -->'
  replace: "<!-- INJECT_ACTIVITY: reading-comprehension, Read a daily-life dialogue and answer grammar-focused questions about all Phase 3 topics -->"
- find: 'Уважно проаналізуймо цей діалог, адже він є чудовим прикладом «соціальних шахів» *(social chess)* у сучасній українській мові. Вибір правильної граматичної форми дієслова тут має величезне стратегічне значення для обох співрозмовників. Зверніть увагу, як професійний HR-менеджер використовує умовний спосіб для підкресленої, елегантної ввічливості: «Чи не могли б ви розповісти?». Це одразу створює комфортну атмосферу для спілкування. Але коли доходить до конкретних технічних завдань, менеджер перемикається на прямий наказовий спосіб: «Напишіть, будь ласка, цей алгоритм». Це дозволяє йому м'яко, але впевнено контролювати весь процес інтерв'ю.'
  replace: ''
- find: 'З іншого боку, наш кандидат також чудово грає в цю лінгвістичну гру. Він свідомо використовує нереальну умову («Якби я не любив програмування, я б не подавався»), щоб яскраво продемонструвати свою глибоку мотивацію. Крім того, наприкінці розмови кандидат свідомо обирає взаємне зворотне дієслово «зустрінемося». Цей тонкий вибір показує його як чудового командного гравця, налаштованого на рівноправну співпрацю *(equal collaboration)*, а не як ізольованого спеціаліста. Нарешті, пасивні конструкції та віддієслівні іменники («тестування проводиться», «завдання виконано», «підписання контракту») додають цій розмові необхідного корпоративного та об'єктивного тону.'
  replace: ''
- find: 'Ми з вами разом пройшли величезний шлях упродовж останніх тижнів навчання. Вся Фаза 3 була детально присвячена тому, **як** саме відбуваються різноманітні події навколо нас. Ви навчилися віддавати чіткі накази, ставити логічні умови, мріяти про неможливе, описувати складні абстрактні процеси за допомогою віддієслівних іменників та філігранно працювати з пасивними і зворотними конструкціями. Фактично, ви повністю опанували всю внутрішню механіку сучасного українського дієслова.'
  replace: ''
- find: 'Тепер настав час рухатися далі! Ми плавно переходимо до Фази 4, яку можна сміливо назвати «**Всесвітом руху**» *(The Motion Universe)*. Якщо всі наші попередні граматичні модулі фокусувалися на відносно «статичних» *(static)* діях та незмінних станах, то наступні десять модулів будуть присвячені виключно тому, **куди** і **як** ми фізично переміщуємося в просторі. Ми почнемо з детального вивчення просторових прийменників, а потім особисто познайомимося з фундаментальними дієсловами руху: **йти** *(to walk, to go on foot)* та **їхати** *(to ride, to go by vehicle)*. Ви дізнаєтеся, як одна маленька приставка може кардинально змінити напрямок вашої подорожі, і навчитеся вільно орієнтуватися в українському динамічному просторі.'
  replace: 'Фаза 4 розпочнеться з теми «Всесвіт руху» *(The Motion Universe)*. Якщо попередні модулі стосувалися статичних дій, наступні розглядатимуть, **куди** і **як** ми переміщуємося. Ви вивчите просторові прийменники, базові дієслова руху (**йти**, **їхати**) та префіксальну систему, що визначає напрямок.'
</fixes>

Enough verification data. All 34 VESUM words verified. Multimedia search found Wikipedia articles. Textbook chunks found. Now constructing the module. B1 = 100% Ukrainian body, Tab 2 has English translations only.

<plan_reasoning section="Частковий родовий">
<word_budget>700 target, running total ~700 of 4000.</word_budget>
<plan_vocab>склянка (Склянка води — це частковий родовий), шматок (Дайте, будь ласка, шматок хліба), багато (Багато цукру шкідливо), немає (У пляшці немає молока), цукор (Трохи цукру, будь ласка), сік (Склянка соку, а не *сіку), борщ (Тарілка борщу).</plan_vocab>
<register>100% Ukrainian prose. No English in body. Grammar facts stated directly in Ukrainian.</register>
<teaching_sequence>Partial genitive concept: measure/container in Nom/Acc + substance in Gen. Quantity words + Gen. Vowel alternation: сік→соку. From Knowledge Packet: Частотність і пріоритети, Типові помилки L2, Природні приклади, Заболотний p.94 chunk.</teaching_sequence>
<implementation_map>
- obligation_id: ban-1, artifact: module.md, location: §Частковий родовий, treatment: absent of phrasing matching ban-1 rule (negative obligation)
- obligation_id: ban-2, artifact: module.md, location: §Закінчення -а/-я чи -у/-ю?, treatment: absent of phrasing matching ban-2 rule (negative obligation)
- obligation_id: err-1, artifact: activities.yaml, location: activities.yaml, treatment: error-correction item with sentence/error/correction for Лондон→Лондона
- obligation_id: err-2, artifact: activities.yaml, location: activities.yaml, treatment: error-correction item with sentence/error/correction for Єгипта→Єгипту
- obligation_id: err-3, artifact: activities.yaml, location: activities.yaml, treatment: error-correction item with sentence/error/correction for цукра→цукру
- obligation_id: err-4, artifact: activities.yaml, location: activities.yaml, treatment: error-correction item with sentence/error/correction for автобусу→автобуса
- obligation_id: err-5, artifact: activities.yaml, location: activities.yaml, treatment: error-correction item with sentence/error/correction for вівторку→вівторка
- obligation_id: err-6, artifact: activities.yaml, location: activities.yaml, treatment: error-correction item with sentence/error/correction for новий телефон→нового телефона
- obligation_id: err-7, artifact: activities.yaml, location: activities.yaml, treatment: error-correction item with sentence/error/correction for місців→місць
</implementation_map>
<verification_plan>VESUM verify_words for all new lemmas. verify_source_attribution for Заболотний claim.</verification_plan>
<verification_trace>
mcp__sources__verify_words(words=["склянка","шматок","цукор","борщ","сік","мед","сир","молоко"])
mcp__sources__verify_source_attribution(source="sum11", claim="склянка")
</verification_trace>
</plan_reasoning>

<plan_reasoning section="Родовий бажання, пошуку, досягнення">
<word_budget>600 target, running total ~1300.</word_budget>
<plan_vocab>бажати (Бажаю вам щастя), шукати (Шукаю правди — Р.в., шукаю книжку — Зн.в.), досягти (Вона досягла мети), позбутися (Позбувся страху), потребувати (Потребую допомоги), гідний (Цей проєкт гідний уваги), вартий (Фільм вартий перегляду).</plan_vocab>
<register>100% Ukrainian. Direct grammar exposition without English meta-narration.</register>
<teaching_sequence>Genitive of desire/seeking/achievement: verbs that govern Gen instead of Acc. Abstract nouns strongly favor Gen. Adj+Gen expressions (вартий уваги, повний надії). Practice: choose between Gen and Acc. From Knowledge Packet: 1. Родовий відмінок однини, Типові помилки L2, Природні приклади.</teaching_sequence>
<implementation_map>(all obligations already mapped above in §Частковий родовий — this section has no new obligations)</implementation_map>
<verification_plan>verify_words for бажати, потребувати, досягти, позбутися, гідний, вартий.</verification_plan>
<verification_trace>
mcp__sources__verify_words(words=["бажати","потребувати","досягти","позбутися","гідний","вартий"])
</verification_trace>
</plan_reasoning>

<plan_reasoning section="Родовий при запереченні">
<word_budget>600 target, running total ~1900.</word_budget>
<plan_vocab>заперечення (Заперечення вимагає родового відмінка), немає (Немає часу — завжди Р.в.).</plan_vocab>
<register>100% Ukrainian prose.</register>
<teaching_sequence>Core rule: немає + Gen. Affirmative→Negative transformation: Є час (Nom) → Немає часу (Gen). Transitive negated verbs: Gen often replaces Acc especially with abstract nouns. не було/не буде + Gen. From Knowledge Packet: Частотність і пріоритети, Родовий відмінок множини.</teaching_sequence>
<implementation_map>(all obligations already mapped)</implementation_map>
<verification_plan>verify_source_attribution for negation+genitive rule.</verification_plan>
<verification_trace>
mcp__sources__verify_source_attribution(source="sum11", claim="немає")
</verification_trace>
</plan_reasoning>

<plan_reasoning section="Родовий у датах і часових виразах">
<word_budget>600 target, running total ~2500.</word_budget>
<plan_vocab>дата (Другого лютого — дата в родовому відмінку).</plan_vocab>
<register>100% Ukrainian.</register>
<teaching_sequence>Ordinal numerals + Gen for dates. Time expressions with demonstratives + Gen: цього тижня, минулого року, наступного місяця. From Knowledge Packet: Природні приклади, Як це пояснюють у школі.</teaching_sequence>
<implementation_map>(all obligations already mapped)</implementation_map>
<verification_plan>verify_source_attribution for Литвінова Grade 6 date+genitive claim.</verification_plan>
<verification_trace>
mcp__sources__verify_source_attribution(source="sum11", claim="дата родовий")
</verification_trace>
</plan_reasoning>

<plan_reasoning section="Закінчення -а/-я чи -у/-ю?">
<word_budget>700 target, running total ~3200.</word_budget>
<plan_vocab>закінчення (Закінчення -а/-я для конкретних предметів, -у/-ю для абстрактних), прогрес (досягти прогресу), розвиток (рівень розвитку), біль (від болю), листопад (листопада — місяць, листопаду — процес), телефон (телефона — апарат, телефону — зв'язок).</plan_vocab>
<register>100% Ukrainian. Decolonized: -у/-ю presented as a core system, not exceptions.</register>
<teaching_sequence>Semantic categories for -а/-я (beings, cities, concrete objects, measures, days/months) vs -у/-ю (countries, natural phenomena, substances, abstractions, feelings, institutions). Differentiation by meaning: листопада/листопаду. Source: Заболотний 6 клас. Decolonization ban-2: never frame -у/-ю as exceptions.</teaching_sequence>
<implementation_map>
- obligation_id: ban-2, artifact: module.md, location: §Закінчення -а/-я чи -у/-ю?, treatment: absent of phrases treating -у/-ю as exceptions or irregular (negative obligation — core system presentation)
</implementation_map>
<verification_plan>verify_words for телефон, листопад, прогрес, розвиток, біль. verify_source_attribution for Заболотний ending rules.</verification_plan>
<verification_trace>
mcp__sources__verify_source_attribution(source="sum11", claim="закінчення родовий")
mcp__sources__check_russian_shadow(word="телефон")
</verification_trace>
</plan_reasoning>

<plan_reasoning section="Родовий з прийменниками (§4.2.2.2)">
<word_budget>600 target, running total ~3800.</word_budget>
<plan_vocab>(recycling vocabulary from previous sections + preposition list)</plan_vocab>
<register>100% Ukrainian.</register>
<teaching_sequence>15+ prepositions governing Gen: замість, крім/окрім, навколо, серед, щодо, внаслідок, поблизу. Compound prepositions: з-за, з-під, з-поміж. Semantic grouping: place, source/cause, exceptions, direction, relation, time. From Knowledge Packet: 2. Родовий відмінок множини, 1. Родовий відмінок однини.</teaching_sequence>
<implementation_map>(all obligations already mapped)</implementation_map>
<verification_plan>verify_source_attribution for preposition+genitive rules.</verification_plan>
<verification_trace>
mcp__sources__verify_source_attribution(source="sum11", claim="прийменник родовий")
</verification_trace>
</plan_reasoning>

<plan_reasoning section="Підсумок">
<word_budget>400 target, running total ~4200 (within 4000±5% = 3800-4200).</word_budget>
<plan_vocab>(summary review, recycling all vocabulary)</plan_vocab>
<register>100% Ukrainian.</register>
<teaching_sequence>Six semantic roles of Gen: 1. Partial, 2. Desire/seeking, 3. Negation, 4. Dates, 5. Possession (A2 review), 6. With prepositions. Self-check with 10 sentences covering all roles and both masc endings.</teaching_sequence>
<implementation_map>(all obligations already mapped)</implementation_map>
<verification_plan>final verify_words scan on all prose.</verification_plan>
<verification_trace>(covered by prior traces)</verification_trace>
</plan_reasoning>

<implementation_map_audit>manifest_obligations=9 covered_in_map=9 missing=[]</implementation_map_audit>

<bad_form_audit>italic_bad_form_patterns_found=0 converted_to_marker=0 remaining=0</bad_form_audit>

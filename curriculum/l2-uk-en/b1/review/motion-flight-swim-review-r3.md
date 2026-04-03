## Linguistic Scan
Errors found:
- "по гучномовцю" (calque from Russian "по громкоговорителю", should be "через гучномовець")
- "приймає власних рішень" (calque from Russian "принимать решение", should be "ухвалює власні рішення")
- "виключно сама відстань" (artificial/calque usage of "виключно" as a limiting particle, should be "лише")

## Exercise Check
- The `quiz` marker is placed before water verbs are taught, effectively missing half the required topic. It needs to be moved after the "Пливти / плавати" section to be a combined exercise.
- The `fill-in` marker was narrowed to only maritime sentences, ignoring the plan's requirement for airport sentences.
- The `error-correction` marker was overly specific instead of following the broad scope from the plan.
- The total count is 6, which matches the plan, but their placement and scope need adjustment.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The text has 5291 words, which is >30% over the 4000-word target. The writer padded the text with extra paragraphs (e.g., detailing airplane parts like "крило", "хвіст", "кабіна пілота", which were not in the plan). Exercise markers deviated from plan intents. |
| 2. Linguistic accuracy | 7/10 | Contains calques: "по гучномовцю" instead of "через гучномовець", "приймає рішення" instead of "ухвалює рішення", and the artificial use of "виключно" as a limiting particle ("виключно сама відстань" instead of "лише сама відстань"). |
| 3. Pedagogical quality | 8/10 | Explanations of unidirectional vs multidirectional verbs are very thorough. However, placing a combined quiz marker before the second half of the content was taught showed a lack of pedagogical foresight. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary items (аеропорт, рейс, пором, etc.) are included and well-contextualized. |
| 5. Exercise quality | 7/10 | The injected markers were artificially narrowed from the plan. A combined air/water quiz was placed after only the air section, testing only air verbs. The fill-in was reduced to just maritime. |
| 6. Engagement & tone | 6/10 | The tone is often overly meta and instructional ("Ми вже дослідили велику частину всесвіту дієслів руху", "Тепер настав час логічно завершити", "Ви, напевно, помітили, як автор вміло використовує..."). Shows a tendency to tell rather than show. |
| 7. Structural integrity | 9/10 | All H2 headers match the plan precisely. Markdown is clean and correctly formatted. |
| 8. Cultural accuracy | 10/10 | Excellent context using real-world Ukrainian routes (Boryspil to Istanbul, Dnipro river) and natural settings. |
| 9. Dialogue & conversation quality | 5/10 | The dialogues in the airport and seaport are purely transactional and robotic ("У вас є багаж? Так, одна валіза.", "А скільки коштує квиток в один бік?"). They lack natural conversational flow. |

## Findings

[2. Linguistic accuracy] [Critical]
Location: "по гучномовцю оголосили **посадку**"
Issue: "по гучномовцю" is a calque of the Russian "по громкоговорителю". The correct Ukrainian form requires the preposition "через".
Fix: Change to "через гучномовець оголосили **посадку**"

[2. Linguistic accuracy] [Critical]
Location: "не приймає власних рішень і не бореться"
Issue: "приймати рішення" is a widespread calque of the Russian "принимать решение" (confirmed by Antonenko-Davydovych). The correct collocation is "ухвалювати рішення".
Fix: Change to "не ухвалює власних рішень і не бореться"

[2. Linguistic accuracy] [Critical]
Location: "виключно сама відстань, яку успішно подолав"
Issue: "виключно" used as a limiting particle is a calque/artificial construction (Antonenko-Davydovych). It should be replaced with "лише" or "тільки".
Fix: Change to "лише сама відстань, яку успішно подолав"

[9. Dialogue & conversation quality] [Major]
Location: "В аеропорту (At the airport): Працівниця: Доброго дня..."
Issue: Dialogues are purely transactional and robotic. They read like an old phrasebook without any natural conversational flow or personality.
Fix: Rewrite the transactional exchanges to include more natural greetings and phrasing.

[1. Plan adherence] [Major]
Location: "Кожен сучасний потужний літак має надзвичайно складну і дуже цікаву будову..."
Issue: The text is bloated (5291 words vs 4000 target) and includes an entire paragraph detailing airplane parts (хвіст, крило, кабіна) that were not requested in the plan, artificially inflating the word count.
Fix: Remove the redundant paragraph about airplane parts and update the corresponding activity hint that referenced "ілюмінатор".

[5. Exercise quality] [Major]
Location: `<!-- INJECT_ACTIVITY: quiz...` and `<!-- INJECT_ACTIVITY: fill-in...`
Issue: The writer split the combined exercises required by the plan. The plan asked for a quiz choosing between ALL FOUR air/water base verbs and their prefixes, but the generated marker only tests the "летіти/літати" pair because it was placed prematurely in the text.
Fix: Move the quiz marker to after the water section, and update the marker hints to match the plan's combined scope exactly.

## Verdict: REVISE
The module contains critical linguistic errors (Russian calques like "приймати рішення" and "по гучномовцю"), fails the word count target by >30%, and suffers from poorly placed exercise markers that break the pedagogical logic of the plan.

<fixes>
- find: "по гучномовцю оголосили **посадку**"
  replace: "через гучномовець оголосили **посадку**"
- find: "не приймає власних рішень і не бореться"
  replace: "не ухвалює власних рішень і не бореться"
- find: "виключно сама відстань, яку успішно подолав"
  replace: "лише сама відстань, яку успішно подолав"
- find: "**Працівниця:** Доброго дня. Ваш паспорт і квиток, будь ласка. *(Good afternoon. Your passport and ticket, please.)*\n**Марко:** Доброго дня. Ось мої документи. *(Good afternoon. Here are my documents.)*\n**Працівниця:** У вас є багаж? *(Do you have luggage?)*"
  replace: "**Працівниця:** Доброго дня! Паспорт і квиток, будь ласка. *(Good afternoon! Passport and ticket, please.)*\n**Марко:** Вітаю. Тримайте, ось мої документи. *(Greetings. Here you go, these are my documents.)*\n**Працівниця:** Дякую. Чи будете здавати багаж? *(Thank you. Will you be checking in any luggage?)*"
- find: "**Олена:** Перепрошую, о котрій годині пором відпливає на острів? *(Excuse me, what time does the ferry sail to the island?)*\n**Касир:** Наступний пором відпливає о 14:30 від третього причалу. *(The next ferry departs at 2:30 PM from pier three.)*"
  replace: "**Олена:** Перепрошую, підкажіть, о котрій відпливає найближчий пором на острів? *(Excuse me, could you tell me what time the next ferry sails to the island?)*\n**Касир:** О 14:30. Відправлення від третього причалу. *(At 2:30 PM. Departure is from pier three.)*"
- find: "Кожен сучасний потужний літак має надзвичайно складну і дуже цікаву будову, з якою завжди корисно бути добре знайомим. З обох боків довгого металевого корпусу розташоване величезне і міцне **крило** *(wing)*, яке допомагає важкому літаку дуже впевнено триматися високо в повітрі під час руху. Задня частина літака традиційно і цілком логічно називається **хвіст** *(tail)*. Під час довгого багаточасового польоту пасажири дуже люблять дивитися у маленьке кругле віконечко, яке в авіації має спеціальну професійну назву — **ілюмінатор** *(porthole/window)*. Керують цим неймовірно великим і технологічним повітряним судном надзвичайно досвідчені пілоти. Їхнє головне робоче місце — це закрита **кабіна пілота** *(cockpit)*, куди звичайним пасажирам вхід завжди суворо і категорично заборонено правилами безпеки. Перед самим початком польоту ви обов'язково почуєте дуже важливу ввічливу команду від старшої стюардеси: «Шановні пасажири, будь ласка, **пристебніть паски безпеки** *(fasten your seatbelts)*». Це найголовніше і непорушне правило чудово гарантує ваш абсолютний спокій та надійний захист під час дуже швидкого руху.\n\n"
  replace: ""
- find: "Match aviation/maritime vocabulary (рейс, пором, причал, ілюмінатор)"
  replace: "Match aviation/maritime vocabulary (рейс, пором, причал, палуба)"
- find: "майбутні подорожі.\n\n<!-- INJECT_ACTIVITY: quiz, Focus on choosing летіти/літати or the correct prefix, 8 items -->\n<!-- INJECT_ACTIVITY: group-sort, Sort prefixed forms of летіти (прилетіти, залетіти, облетіти, etc.) by meaning category (Arrival, Direction, Limit), 12 items -->\n\n## Пливти / плавати"
  replace: "майбутні подорожі.\n\n<!-- INJECT_ACTIVITY: group-sort, Sort prefixed forms of летіти (прилетіти, залетіти, облетіти, etc.) by meaning category (Arrival, Direction, Limit), 12 items -->\n\n## Пливти / плавати"
- find: "відпочинку на морі чи річці.\n\n<!-- INJECT_ACTIVITY: fill-in, Complete maritime sentences with correct prefixed verbs (припливти, переплисти, відпливти), 8 items -->\n<!-- INJECT_ACTIVITY: error-correction, Fix incorrect air/water motion verb forms like *перепливти or *літати instead of летіти in specific contexts, 6 items -->\n\n## Авіаційна та морська"
  replace: "відпочинку на морі чи річці.\n\n<!-- INJECT_ACTIVITY: quiz, Focus on choosing летіти/літати or пливти/плавати and correct prefix based on context, 8 items -->\n<!-- INJECT_ACTIVITY: fill-in, Complete airport and maritime sentences with correct prefixed motion verbs, 8 items -->\n<!-- INJECT_ACTIVITY: error-correction, Fix incorrect air/water motion verb forms (wrong prefix, wrong base verb), 6 items -->\n\n## Авіаційна та морська"
</fixes>

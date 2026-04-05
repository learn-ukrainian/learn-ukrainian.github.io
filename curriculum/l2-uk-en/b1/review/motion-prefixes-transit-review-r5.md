Now I have enough evidence to compile the full review. Let me write it up.

## Linguistic Scan

**Russianisms:** None found. The module actively identifies and corrects one (перевести ≠ перекласти for "translate") — excellent decolonized teaching.

**Surzhyk:** None found.

**Calques:** None found. All verb-preposition pairings verified: через + Зн.в., повз + Зн.в., по + Д.в. — all correct.

**Paronyms:** None misused.

**Russian characters (ы, э, ё, ъ):** None found.

**Gender/case verification:**
- "переїхати через Замковий міст" — міст (m.), Зн.в. = "міст" (inanimate=Nom.) ✓
- "перейти через дорогу" — дорога (f.), Зн.в. = "дорогу" ✓
- "повз будинок" — будинок (m.), Зн.в. = "будинок" (inanimate=Nom.) ✓
- "по Хрещатику" — Хрещатик (m.), Д.в. = "Хрещатику" ✓
- "по розміченому пішохідному переходу" — перехід (m.), Д.в. = "переходу" ✓

**Conjugation tables verified against VESUM:**
- перейти: перейду/перейдеш/перейде/перейдемо/перейдете/перейдуть ✓
- Past: перейшов/перейшла/перейшло/перейшли ✓
- переїхати: переїду/переїдеш/переїде/переїдемо/переїдете/переїдуть ✓
- пройти: пройду/пройдеш/пройде/пройдемо/пройдете/пройдуть ✓
- Past: пройшов/пройшла/пройшло/пройшли ✓
- проїхати: проїду/проїдеш/проїде/проїдемо/проїдете/проїдуть ✓
- Past: проїхав/проїхала/проїхало/проїхали ✓

All verified via `verify_words`. Zero conjugation errors.

**VESUM not-found words:** All 14 are proper nouns (Київ, Дніпро, Авраменко, etc.) or tokenization artifacts (Кам← from Кам'янець-Подільський, янця← from Кам'янця). No real errors.

**Notable positive:** The module corrects the plan's "перевести (to translate)" to "перекласти" and explicitly warns learners that using "перевести" for "translate" is a Russicism from Russian "перевести." This is linguistically accurate and a strong decolonization move. GRAC concordance confirms "перевести текст" appears only in informal/internet sources, while "перекласти" is the standard literary form.

**No linguistic errors found.**

## Exercise Check

All 6 activity markers present, matching plan's `activity_hints`:

| # | Marker type | Plan match | Placement | After teaching? |
|---|------------|------------|-----------|----------------|
| 1 | match-up | ✓ "Match пере- verbs with про- counterparts" | End of пере- section | ✓ After both prefix groups introduced conceptually |
| 2 | fill-in | ✓ "Complete direction-giving sentences with про- verbs" | End of про- section | ✓ After про- taught |
| 3 | quiz | ✓ "Choose пере- or про-" | In comparison section | ✓ After contrastive pairs explained |
| 4 | error-correction | ✓ "Fix incorrect transit prefix choices" | In comparison section | ✓ After common errors discussed |
| 5 | group-sort | ✓ "Sort all prefix groups" | In integration section | ✓ After 8-prefix table |
| 6 | free-write | ✓ "Write travel directions" | End of integration section | ✓ After full system presented |

Markers spread across 4 different sections (not clustered). Focus descriptions match plan's `activity_hints`. Item counts specified in markers match plan (8, 8, 8, 6, 14, 6).

**No exercise issues found.**

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All 6 content_outline sections covered. Textbook references cited: Голуб Grade 6 p.31 ("рух «з одного боку на інший»"), Авраменко Grade 5 p.63 ("рух через перешкоду"), Заболотний Grade 5 p.55 (prefix diagram with бігти) — all verified via RAG. All required vocabulary present. Two justified deviations: section title "Шість→Вісім" correctly fixes plan's arithmetic error (plan lists 8 prefixes but titles section "Шість"); "перевести (to translate)" correctly replaced by "перекласти" with Russicism warning. Minor: Підсумок lacks the "Complete table" the plan envisions — presents content as flowing text with two category lists rather than a two-column verb table. |
| 2. Linguistic accuracy | 10/10 | Zero Russianisms, zero Surzhyk, zero calques. All conjugation tables verified against VESUM (перейти, переїхати, пройти, проїхати — all 28 forms correct). Case governance correct throughout: через+Зн.в. ("через дорогу"), повз+Зн.в. ("повз музей"), по+Д.в. ("по вулиці"). Actively teaches decolonized Ukrainian: identifies "перевести=translate" as Russicism, teaches "перекласти" instead. |
| 3. Pedagogical quality | 9/10 | Strong PPP flow: Presentation (road trip narrative introduces both prefixes in context) → Pattern (systematic analysis of пере- then про- with 10+ examples each) → Practice (contrastive scenarios, then integration exercises). 3+ examples per grammar point consistently (перейти alone has 5+ sentence examples). Conjugation paradigms with full person/number/tense forms. Extended meanings taught through spatial metaphor ("time as a river passing through life"). Aspect pairs (переходити/перейти, проходити/пройти) explicitly contrasted with process vs. result framing. |
| 4. Vocabulary coverage | 10/10 | All 12 required vocabulary items from plan used naturally in prose: перейти ("Перейдіть вулицю на зелене світло"), переїхати ("Переїхали міст через Дніпро"), перебігти ("Дитина перебігла дорогу"), перенести ("Переніс дитину через калюжу"), перевести ("Перевела бабусю через дорогу"), пройти ("Пройшли повз музей"), проїхати ("Проїхали свою зупинку!"), пробігти ("Пробіг повз мене"), переходити ("Переходьте обережно!"), проходити ("проходили повз цей будинок"), пішохідний перехід, перехрестя. All 11 recommended items also covered: перевезти, провести, провезти, перелетіти, переплисти, пролетіти, проплисти, повз, наскрізь, кордон, пронести. |
| 5. Exercise quality | 9/10 | All 6 plan activity_hints have corresponding markers with matching types and focus descriptions. Placement is pedagogically sound — match-up after пере- (tests pattern recognition), fill-in after про- (tests production), quiz and error-correction in comparison section (tests discrimination), group-sort and free-write in integration section (tests synthesis). Item counts match plan. Cannot evaluate generated YAML content, only markers. |
| 6. Engagement & tone | 8/10 | **Strengths:** Кам'янець-Подільський bridge story is vivid and culturally specific. Cat-crossing-road scenario is memorable and humorous. "Foreigner who walked along the highway" example is genuinely funny ("мужньо крокувала гарячим асфальтом п'ять кілометрів"). Two natural dialogues with named speakers. Road trip narrative draws the reader in. **Weaknesses:** Recurring verbal padding: "надзвичайно важливим," "абсолютно стандартною," "кардинально змінюють," "максимально точно" — these intensifiers add no meaning. Generic motivational language: "Тепер настав час стати справжнім архітектором власних унікальних маршрутів" could apply to any course. "Не бійтеся сміливо та креативно комбінувати різні лексичні варіанти, адже саме так щодня звучить багата, жива та абсолютно природна українська мова" — fully generic. Gamified framing: "Ваша просторова навігація стає все точнішою" and "Тепер ви можете описати будь-який міський маршрут" — "You now possess" register. |
| 7. Structural integrity | 10/10 | All H2 headings present and ordered correctly. No duplicate summaries. No stray tags or formatting artifacts. Clean markdown with proper table formatting. Word count 5151 > 4000 target. Section title "Вісім" correctly fixes plan's "Шість." |
| 8. Cultural accuracy | 10/10 | Fully decolonized — Ukrainian taught on its own terms, never "like Russian." Actively corrects a Russian influence (перевести≠перекласти). Cultural references authentic: Кам'янець-Подільський Замковий міст, Хрещатик, Золоті ворота, Шевченко monument, Ukrainian wedding tradition (carrying bride over threshold). Geographic references (Київ→Житомир road trip, Харків driving lesson) are realistic. |
| 9. Dialogue quality | 9/10 | Two multi-turn dialogues with named speakers. Driving lesson (Інструктор/Учень): natural instruction flow, matches plan's dialogue_situation exactly, uses transit verbs organically during navigation. City directions (Турист/Місцевий): 5-turn exchange, realistic scenario in Kyiv center, integrates multiple prefix groups naturally (пройдіть, перейдіть, дійдіть, зайдіть). Road trip narrative functions as a third quasi-dialogue. All dialogues grounded in real situations learners would encounter. |

## Findings

[ENGAGEMENT] [MAJOR]
Location: Section "Вісім префіксів разом" — "Тепер настав час стати справжнім архітектором власних унікальних маршрутів. Спробуйте максимально впевнено застосувати свій новий мовний арсенал дієслів руху на практиці."
Issue: Generic motivational language — "become a true architect of your own unique routes" and "new linguistic arsenal" are flowery and could apply to any language course.
Fix: Replace with direct instruction that demonstrates rather than motivates.

[ENGAGEMENT] [MAJOR]
Location: Section "Вісім префіксів разом" — "Не бійтеся сміливо та креативно комбінувати різні лексичні варіанти, адже саме так щодня звучить багата, жива та абсолютно природна українська мова. Тепер ви можете описати будь-який міський маршрут із точними просторовими деталями — від перетинання мостів до проходження повз визначні місця."
Issue: Two consecutive sentences of generic motivation. "Don't be afraid to boldly and creatively combine" is filler. "Now you can describe any city route" is "You have unlocked" register.
Fix: Remove the motivational filler and end the section on the concrete production task.

[ENGAGEMENT] [MINOR]
Location: Section "Підсумок" — "Ваша просторова навігація стає все точнішою."
Issue: Gamified progress-tracking language ("Your spatial navigation is becoming more precise"). Tells rather than shows.
Fix: Remove — the preceding content demonstrates the learner's progress through the self-check questions.

[ENGAGEMENT] [MINOR]
Location: Section "Префікс про-" — "Другим надзвичайно важливим префіксом для дієслів руху є префікс про-."
Issue: "Надзвичайно важливим" is a generic intensifier that adds no pedagogical value.
Fix: Simplify the opening.

[ENGAGEMENT] [MINOR]
Location: Section "Пере- чи про-?" — "Один маленький префікс дійсно повністю змінює геометрію нашого руху в українській мові."
Issue: Meta-commentary about how amazing prefixes are. Telling, not showing — the preceding content already demonstrates this effectively.
Fix: Remove the sentence; the Заболотний reference and examples carry the point.

[PLAN ADHERENCE] [MINOR]
Location: Section "Підсумок: пере- і про-"
Issue: Plan specifies "Complete table: пере- and про- with all base verbs" but module presents the summary as flowing prose with two category lists rather than a structured comparison table. A table format would be more useful for reference.
Fix: Not critical — the information is all present. Could be improved in a future pass by adding a reference table.

## Verdict: REVISE

The module is linguistically impeccable (10/10) with excellent pedagogical structure, full vocabulary coverage, and correct cultural framing. The only dimension below 9 is Engagement (8/10) due to recurring verbal padding and generic motivational language scattered across the module. These are fixable with surgical edits — no structural rewrite needed. Zero linguistic errors to fix; all fixes target engagement/tone.

<fixes>
- find: "Тепер настав час стати справжнім архітектором власних унікальних маршрутів. Спробуйте максимально впевнено застосувати свій новий мовний арсенал дієслів руху на практиці."
  replace: "Спробуйте застосувати всі вивчені дієслова руху на практиці."
- find: "Не бійтеся сміливо та креативно комбінувати різні лексичні варіанти, адже саме так щодня звучить багата, жива та абсолютно природна українська мова. Тепер ви можете описати будь-який міський маршрут із точними просторовими деталями — від перетинання мостів до проходження повз визначні місця."
  replace: "Комбінуйте різні префікси, адже саме так звучить природна українська мова."
- find: "Ваша просторова навігація стає все точнішою. У наступному модулі"
  replace: "У наступному модулі"
- find: "Другим надзвичайно важливим префіксом для дієслів руху є префікс **про-**."
  replace: "Другий ключовий транзитний префікс — **про-**."
- find: "Один маленький префікс дійсно повністю змінює геометрію нашого руху в українській мові."
  replace: "Один префікс змінює геометрію руху."
</fixes>

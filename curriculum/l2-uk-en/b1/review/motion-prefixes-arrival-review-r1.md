## Linguistic Scan
Errors found:
1. **Calques / Russianisms**:
   - `місцезнаходження` (calque from местонахождение, should be `місце перебування`).
   - `благополучно` (Russianism/calque, should be `щасливо` або `успішно`).
   - `брати/взяти таксі` (calque from брать такси, should be `сісти в таксі` or `їхати на таксі`).
   - `доставка` (Russianism, should be `доставляння`).
   - `парковку` (informal Russianism, should be `стоянку` or `майданчик для паркування`).
2. **Surzhyk Syntax**:
   - `Давайте розглянемо` (Surzhyk imperative, should be `Розгляньмо`).
3. **Stylistic awkwardness**:
   - `лімітованої точки` (unnatural use of a borrowed word, should be `конкретної точки`).

## Exercise Check
- Marker logic issue: The `group-sort` marker's focus deviated completely from the plan. The plan asked to sort by prefix meaning (arrival vs. reaching), but the marker asks to sort by vehicle vs. on foot. 
- Marker formatting issue: The `free-write` marker is missing the `items: 6` parameter requested by the plan.
- All other exercises correctly match the taught material and are distributed well.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missing the full conjugation of `доїхати` (the writer provided conjugation for `дійти` instead). Missing the imperfective example for `прибігати` (used perfective twice for the kitten example). Missing the specific example for `доплисти` in Section 3. |
| 2. Linguistic accuracy | 8/10 | Several calques and Russianisms present: "взяв таксі", "брати таксі", "благополучно", "місцезнаходження", "доставка", "парковка". Surzhyk syntax in "Давайте розглянемо". |
| 3. Pedagogical quality | 9/10 | Very strong contextual explanations of grammar. The distinction between "при-" (being there) and "до-" (making it there) is explained clearly with contrasting examples like "Я прийшов до тебе" vs "Я ледве дійшов до тебе". |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary items from the plan are integrated naturally into the prose. |
| 5. Exercise quality | 8/10 | The `group-sort` activity asks students to sort verbs by vehicle vs on foot, entirely missing the point of the module (при- vs до-), contrary to the plan's exact instruction. |
| 6. Engagement & tone | 8/10 | Good use of culturally relevant examples (Zakarpattia, Boryspil, Dovbush Rocks). However, minor meta-commentary slightly disrupts the tone: "Почнемо наш детальний огляд...", "Давайте розглянемо...". |
| 7. Structural integrity | 10/10 | All sections are present, properly ordered, and well within the target word count bounds (4742 words against a 4000 target). |
| 8. Cultural accuracy | 10/10 | Accurate references to Ukrainian geography, rural estates, and travel patterns. |
| 9. Dialogue & conversation quality | 10/10 | The dialogue is a realistic exchange about travel logistics featuring named speakers ("Олена", "Максим") and effectively incorporates the target grammar. |

## Findings
[Plan adherence] [Critical]
Location: Section 3 "Префікс до-: досягнення мети"
Issue: The plan explicitly required the full conjugation of `доїхати`. The writer omitted this entirely, conjugating `дійти` instead.
Fix: Add the future and past tense conjugations of `доїхати` directly after introducing it.

[Plan adherence] [Major]
Location: Section 2 "Префікс при-: прибуття" and Section 3 "Префікс до-: досягнення мети"
Issue: The plan required an example for the imperfective `прибігати` ("Кіт прибігає, коли чує їжу") and perfective `доплисти` ("Він доплив до берега"). The text uses perfective `прибіг` for the cat and omits `доплисти` entirely outside the summary table.
Fix: Update the cat example to imperfective `прибігати` and add a sentence with `доплисти` for a swimmer.

[Linguistic accuracy] [Critical]
Location: Section 2 ("він вирішив не брати швидке таксі", "я одразу взяв таксі до вас"), Section 4 ("благополучно доїхали"), Section 5 ("машина вже приїхала на парковку"), Section 6 ("місцезнаходження")
Issue: Text relies on direct Russian calques ("брати таксі", "благополучно", "місцезнаходження", "парковку").
Fix: Replace with natural Ukrainian equivalents: "сісти в таксі/їхати таксі", "щасливо/успішно", "місце перебування", "стоянку".

[Linguistic accuracy] [Major]
Location: Section 3 ("Коли ж швидка доставка людей або комерційних вантажів")
Issue: "Доставка" is a known Russianism; the standard Ukrainian verbal noun is "доставляння" (neuter).
Fix: Change to "швидке доставляння".

[Linguistic accuracy] [Minor]
Location: Section 4 ("Давайте розглянемо цю тонку лінгвістичну різницю")
Issue: "Давайте + verb" is a Surzhyk construction mimicking Russian "давайте рассмотрим".
Fix: Change to the proper imperative "Розгляньмо".

[Exercise quality] [Major]
Location: `<!-- INJECT_ACTIVITY: group-sort ... -->` and `<!-- INJECT_ACTIVITY: free-write ... -->`
Issue: The `group-sort` activity tests the wrong concept (vehicle vs foot) instead of the plan's requirement (arrival vs reaching). The `free-write` tag is missing the item count.
Fix: Correct the marker instructions to match the plan exactly.

[Engagement & tone] [Minor]
Location: Section 3 ("Почнемо наш детальний огляд з базового руху пішки.")
Issue: Meta-commentary detracts from the immersive flow of the module.
Fix: Simplify to "Найбільш базовим є рух пішки."

## Verdict: REVISE
The writer did an excellent job explaining the semantic differences between the prefixes, but missed several explicit structural requirements from the plan (conjugations, specific examples) and allowed multiple Russian calques to slip through. The exercise marker for `group-sort` must also be corrected to ensure the generated activity matches the learning objective.

<fixes>
- find: "він вирішив не брати швидке таксі."
  replace: "він вирішив не їхати на швидкому таксі."
- find: "А вже звідти я одразу взяв таксі до вас"
  replace: "А вже звідти я одразу сів у таксі до вас"
- find: "Ближче до вечора ми благополучно"
  replace: "Ближче до вечора ми щасливо"
- find: "хтось покидає своє місцезнаходження і рухається геть"
  replace: "хтось покидає своє місце перебування і рухається геть"
- find: "його машина вже приїхала на парковку"
  replace: "його машина вже приїхала на стоянку"
- find: "Коли ж швидка доставка людей або комерційних вантажів"
  replace: "Коли ж швидке доставляння людей або комерційних вантажів"
- find: "Давайте розглянемо цю тонку лінгвістичну різницю"
  replace: "Розгляньмо цю тонку лінгвістичну різницю"
- find: "до певної лімітованої точки у просторі."
  replace: "до певної конкретної точки у просторі."
- find: "Почнемо наш детальний огляд з базового руху пішки."
  replace: "Найбільш базовим є рух пішки."
- find: "Для далеких подорожей на будь-якому транспорті ми обов'язково маємо використовувати дієслово **доїхати** *(to reach by vehicle, perfective)*. Воно є абсолютно необхідним"
  replace: "Для далеких подорожей на будь-якому транспорті ми обов'язково маємо використовувати дієслово **доїхати** *(to reach by vehicle, perfective)*. Його майбутній час відмінюється так: я **доїду**, ти **доїдеш**, він/вона **доїде**, ми **доїдемо**, ви **доїдете**, вони **доїдуть**. Минулий час: **доїхав**, **доїхала**, **доїхало**, **доїхали**. Воно є абсолютно необхідним"
- find: "стрибнути в останній вечірній трамвай»."
  replace: "стрибнути в останній вечірній трамвай». Якщо ми говоримо про подолання дистанції по воді, ми використовуємо дієслово **доплисти** *(to swim all the way to, perfective)*. Наприклад: «Втомлений плавець успішно доплив до берега»."
- find: "Або ж у побутовій ситуації: «Мій пухнастий кіт миттєво прибіг на кухню, коли почув звук відкритої консерви»."
  replace: "Його недоконаною парою є дієслово **прибігати** *(to come running repeatedly)*. Або ж у побутовій ситуації: «Мій пухнастий кіт щоразу швидко прибігає на кухню, коли чує звук відкритої консерви»."
- find: "<!-- INJECT_ACTIVITY: group-sort, Sort prefixed motion verbs into those involving a vehicle vs. those on foot, 10 items -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort, Sort prefixed motion verbs into при- (arrival) / до- (reaching) groups, 10 items -->"
- find: "<!-- INJECT_ACTIVITY: free-write, Write a short travel narrative describing a recent trip using at least 4 при- and 3 до- verbs. -->"
  replace: "<!-- INJECT_ACTIVITY: free-write, Write a short travel narrative using at least 4 при- and 3 до- verbs, 6 items -->"
</fixes>

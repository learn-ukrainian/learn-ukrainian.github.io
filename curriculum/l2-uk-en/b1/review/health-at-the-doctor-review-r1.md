## Linguistic Scan
- **Russianisms / Calques:**
  - `подразнюючий`, `пульсуючий`, `ріжучий` are active participles ending in -учий/-юючий, which are heavily discouraged in modern Ukrainian as morphological calques from Russian. They should be replaced with natural adjectives (`подразливий`, `пульсівний`, `гострий` або `різкий`).
  - `лікарняний лист` is a direct calque from Russian "больничный лист". The standard Ukrainian term is `листок непрацездатності`.
  - `щитовидна залоза` is a deprecated Russian-influenced term. The modern medical standard is `щитоподібна залоза`.

## Exercise Check
- `<!-- INJECT_ACTIVITY: match-medical-word-families -->` is injected after Section 1. However, the plan states this activity tests the "лікар-лікувати-ліки" word family, which is not taught until Section 4. This violates the rule that exercises must test what was just taught.
- `<!-- INJECT_ACTIVITY: sentence-builder-medical-actions -->` is injected after Section 4. It should be swapped with the match-up activity.
- The remaining three markers (`fill-in-doctor-patient-dialogue`, `quiz-symptoms-specialist`, `error-correction-case-government`) are correctly placed after their respective teaching sections.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The text misses explicit explanation of the case government `одужати від + Р.` in the Section 2 verb list. It also omits the `хвороба → хворіти → хворий` morphological family from the Section 4 word families explanation. |
| 2. Linguistic accuracy | 7/10 | Multiple active participle calques (`подразнюючий`, `пульсуючий`, `ріжучий`), plus `лікарняний лист` and `щитовидна залоза`. |
| 3. Pedagogical quality | 10/10 | Excellent PPP flow. Grammar and phonetics (alternations, pluralia tantum) are contextualized flawlessly with clear, vivid examples. |
| 4. Vocabulary coverage | 9/10 | All required vocabulary is present. `хвороба` is used in passing but not explicitly taught as a word family as the plan requested. |
| 5. Exercise quality | 7/10 | The `match-medical-word-families` activity is placed prematurely after Section 1, before its target concepts (`лікар-лікувати-ліки`) are introduced in Section 4. |
| 6. Engagement & tone | 10/10 | Tone is professional, culturally grounded (Vocative case usage, clinic vs. hospital distinction), and avoids generic corporate-speak or meta-commentary. |
| 7. Structural integrity | 9/10 | Clean Markdown. All sections are present. The word count is 5869, which is ~46% over the 4000-word target. Deducting a point for being verbose. |
| 8. Cultural accuracy | 10/10 | Accurately describes the modern Ukrainian medical system (e-prescriptions, polyclinics, 'лікар' vs 'доктор' distinction). |
| 9. Dialogue & conversation quality | 10/10 | The doctor-patient and dentist dialogues are natural, realistic, and use correct medical registry and case government. |

## Findings
[Linguistic Accuracy] [Critical]
Location: `сухий, подразнюючий кашель без мокротиння`
Issue: "Подразнюючий" is an active participle calque from Russian.
Fix: Replace with "подразливий".

[Linguistic Accuracy] [Critical]
Location: `сильний, пульсуючий головний біль`, `сильний, тупий, пульсуючий головний біль`
Issue: "Пульсуючий" is an active participle calque.
Fix: Replace with "пульсівний".

[Linguistic Accuracy] [Critical]
Location: `різкий ріжучий біль у горлі`
Issue: "Ріжучий" is an active participle calque, and "різкий ріжучий" is tautological.
Fix: Replace with "різкий біль у горлі".

[Linguistic Accuracy] [Critical]
Location: `лікарняний лист (документ для роботи)`
Issue: Direct calque from Russian "больничный лист".
Fix: Replace with "листок непрацездатності".

[Linguistic Accuracy] [Critical]
Location: `ліки для щитовидної залози`
Issue: "Щитовидна" is a Russianism in modern Ukrainian medicine.
Fix: Replace with "щитоподібної".

[Plan Adherence] [Major]
Location: Section "У лікаря: діалог" verb list (items 1-5).
Issue: The plan requires teaching the case government for "одужати від + Р." here, but it was skipped.
Fix: Add a new bullet point "6. Дієслово одужати від..." to the list.

[Plan Adherence] [Major]
Location: Section "В аптеці" (`У всіх цих словах базовий спільний корінь «лік-» залишається абсолютно стабільним і є вашим ключем до розуміння всієї родини медичних слів.`)
Issue: The plan explicitly requires teaching the `хвороба → хворіти → хворий` morphological family.
Fix: Add a sentence explicitly connecting this word family.

[Exercise Quality] [Major]
Location: `<!-- INJECT_ACTIVITY: match-medical-word-families -->` after Section 1.
Issue: This activity tests the `лікар-лікувати-ліки` family, which isn't taught until Section 4.
Fix: Swap the marker with `<!-- INJECT_ACTIVITY: sentence-builder-medical-actions -->` (which is currently after Section 4).

## Verdict: REVISE
The module has a very strong pedagogical foundation and excellent cultural contextualization, but it contains critical linguistic calques (active participles, "лікарняний лист", "щитовидна") and misses two specific plan points. The exercise marker for word families is also placed prematurely. These require deterministic fixes before the module can pass.

<fixes>
- find: "Також мене постійно турбує сильний, пульсуючий **головний біль** *(headache)*."
  replace: "Також мене постійно турбує сильний, пульсівний **головний біль** *(headache)*."
- find: "**Скарги під час надходження:** сильний, тупий, пульсуючий головний біль переважно у ділянці скронь; загальна м'язова слабкість тіла; сухий, подразнюючий кашель без мокротиння; стабільно висока температура тіла 38,2 градуси за Цельсієм; різкий ріжучий біль у горлі, який значно посилюється під час ковтання твердої їжі та гарячої рідини."
  replace: "**Скарги під час надходження:** сильний, тупий, пульсівний головний біль переважно у ділянці скронь; загальна м'язова слабкість тіла; сухий, подразливий кашель без мокротиння; стабільно висока температура тіла 38,2 градуси за Цельсієм; різкий біль у горлі, який значно посилюється під час ковтання твердої їжі та гарячої рідини."
- find: "Це і є той самий офіційний медичний діагноз, який лікарі юридично записують у вашу медичну картку та лікарняний лист (документ для роботи), коли в звичайній, повсякденній розмовній мові ми кажемо просто «у мене застуда» або «я підхопив якийсь вірус»."
  replace: "Це і є той самий офіційний медичний діагноз, який лікарі юридично записують у вашу медичну картку та листок непрацездатності (документ для роботи), коли в звичайній, повсякденній розмовній мові ми кажемо просто «у мене застуда» або «я підхопив якийсь вірус»."
- find: "Наприклад, деякі специфічні ліки для щитовидної залози потрібно **приймати натщесерце** *(to take on an empty stomach)* — це медичний термін означає"
  replace: "Наприклад, деякі специфічні ліки для щитоподібної залози потрібно **приймати натщесерце** *(to take on an empty stomach)* — це медичний термін означає"
- find: "5. Дієслово **оглянути** *(to examine)* — це класичне перехідне дієслово. Воно вимагає знахідного відмінка *(Accusative)* прямого об'єкта: **«Черговий лікар дуже уважно оглянув хворого пацієнта»** *(The doctor on duty carefully examined the sick patient)*.\n\n<!-- INJECT_ACTIVITY: fill-in-doctor-patient-dialogue -->"
  replace: "5. Дієслово **оглянути** *(to examine)* — це класичне перехідне дієслово. Воно вимагає знахідного відмінка *(Accusative)* прямого об'єкта: **«Черговий лікар дуже уважно оглянув хворого пацієнта»** *(The doctor on duty carefully examined the sick patient)*.\n6. Дієслово **одужати від** *(to recover from)* вимагає родового відмінка *(Genitive)*: **«Він нарешті одужав від тривалої хвороби»** *(He finally recovered from a long illness)*.\n\n<!-- INJECT_ACTIVITY: fill-in-doctor-patient-dialogue -->"
- find: "І, зрештою, сам фізичний засіб для лікування ми називаємо словом у множині **ліки**. У всіх цих словах базовий спільний корінь «лік-» залишається абсолютно стабільним і є вашим ключем до розуміння всієї родини медичних слів."
  replace: "І, зрештою, сам фізичний засіб для лікування ми називаємо словом у множині **ліки**. У всіх цих словах базовий спільний корінь «лік-» залишається абсолютно стабільним і є вашим ключем до розуміння всієї родини медичних слів. Так само прозоро працює родина слова **хвороба**: від іменника утворюється дієслово **хворіти** та прикметник **хворий**."
- find: "* Називний відмінок — **око**. Місцевий відмінок — **в оці** *(in the eye)*. Наприклад: **«У мене відчуття, ніби порошинка в оці»** *(I have a feeling like there is a speck of dust in the eye)*.\n\n<!-- INJECT_ACTIVITY: match-medical-word-families -->"
  replace: "* Називний відмінок — **око**. Місцевий відмінок — **в оці** *(in the eye)*. Наприклад: **«У мене відчуття, ніби порошинка в оці»** *(I have a feeling like there is a speck of dust in the eye)*.\n\n<!-- INJECT_ACTIVITY: sentence-builder-medical-actions -->"
- find: "На металевих тюбиках із мазями часто можна побачити яскравий напис-попередження: **тільки для зовнішнього застосування** *(for external use only)* — це сувора заборона, що означає: такі препарати наносять лише на шкіру поверхнево, їх категорично не можна брати до рота чи ковтати.\n\n<!-- INJECT_ACTIVITY: sentence-builder-medical-actions -->"
  replace: "На металевих тюбиках із мазями часто можна побачити яскравий напис-попередження: **тільки для зовнішнього застосування** *(for external use only)* — це сувора заборона, що означає: такі препарати наносять лише на шкіру поверхнево, їх категорично не можна брати до рота чи ковтати.\n\n<!-- INJECT_ACTIVITY: match-medical-word-families -->"
</fixes>

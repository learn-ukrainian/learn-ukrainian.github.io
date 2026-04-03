## Linguistic Scan
1 error found:
- Russianism/Typo: "зльот" instead of "зліт" (take-off). VESUM confirms "зльот" does not exist in standard Ukrainian.

## Exercise Check
- The `group-sort` activity is correctly placed after the verbs of air motion prefix section.
- The `quiz` activity is correctly placed.
- The `error-correction` activity is correctly placed.
- The `match-up` activity is correctly placed.
- The `free-write` activity is correctly placed.
- **ERROR:** The `fill-in` activity (Complete airport and maritime sentences) is injected *before* the "Авіаційна та морська лексика" section where the airport and maritime terminology is actually taught. It tests concepts before they are introduced.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The text misses several specific points from the plan: 1) The main reading passage fails to mention "аеропорт Боріспіль" as requested. 2) The mandatory dialogue setting at the Black Sea with parents and children is completely missing. 3) The required example for `обплисти` ("Обпливли острів за день") is omitted entirely. 4) The required example for `проплисти` ("Проплили повз острів") is missing in favor of a different context. |
| 2. Linguistic accuracy | 7/10 | Contains a critical Russianism/typo: "стрімкий **зльот**" instead of the correct Ukrainian "стрімкий **зліт**". |
| 3. Pedagogical quality | 8/10 | Good use of PPP flow and textbook references. However, the `fill-in` activity testing specific maritime and aviation vocabulary is placed before that vocabulary is introduced, breaking the pedagogical sequence. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary items from the plan are naturally integrated into the text. |
| 5. Exercise quality | 8/10 | Activity counts and topics align with `activity_hints`. Deduction for placing the vocabulary `fill-in` activity in the wrong section, which would require learners to guess words they haven't been taught yet. |
| 6. Engagement & tone | 8/10 | Generally engaging and descriptive, but contains some minor instances of teacherly meta-commentary that tell rather than show (e.g., "Глибоке знання всіх цих корисних префіксів дозволить вам неймовірно точно і красиво описувати..."). |
| 7. Structural integrity | 6/10 | The word count is 5147 words, which is massively over the target of 4000 words (>28% off target). |
| 8. Cultural accuracy | 10/10 | Accurate references to Ukrainian educational materials (Авраменко, Вашуленко). Natural geographical references (Босфор). |
| 9. Dialogue & conversation quality | 6/10 | Deducted because the core conversational requirement ("At the Чорне море near Одеса") was entirely ignored. The substitute transactional airport/seaport dialogues are fine, but failing to include the planned interactive family scene weakens the conversational quality. |

## Findings
[Linguistic accuracy] [Critical]
Location: `починається найемоційніший момент — стрімкий **зльот** *(take-off)* літака`
Issue: "Зльот" is a Russianism or typo (derived from Russian "взлёт"). The correct Ukrainian noun for "take-off" is "зліт".
Fix: Change "зльот" to "зліт".

[Plan adherence] [Major]
Location: `Я приїхав у головний міжнародний **аеропорт** *(airport)* нашої столиці. Я знав,`
Issue: The plan explicitly requires mentioning "аеропорт Боріспіль" in the introductory reading passage, but it is missing.
Fix: Add "Бориспіль" to the airport description.

[Plan adherence] [Major]
Location: `За таким самим принципом утворюються й інші важливі форми: **доплисти** *(to swim all the way to)*, **обплисти** *(to sail/swim around)*, **проплисти** *(to sail/swim past or cover a distance)*.`
Issue: The plan requires an example for the prefix "об-": "Обпливли острів за день". The text lists the verb "обплисти" but gives no example sentence for it.
Fix: Add the required example sentence after the verb "обплисти".

[Plan adherence] [Major]
Location: `сміливо використовуйте префікс про- і дієслово **проплисти** *(to sail/swim past or cover distance)*. Наприклад, ви можете гордо розповісти друзям: «Під час учорашніх міських змагань ми дуже швидко **проплили** цілих п'ять кілометрів»`
Issue: The plan requires the specific example "Проплили повз острів" for the verb "проплисти", but the text only gives an example about swimming 5 kilometers in a competition.
Fix: Add the missing "sail past an island" example.

[Exercise quality] [Major]
Location: Just before `## Авіаційна та морська лексика`
Issue: The `fill-in` activity tests airport and maritime sentences, but is placed BEFORE the "Авіаційна та морська лексика" section where these terms are taught.
Fix: Move the `fill-in` activity marker to below the vocabulary section.

[Dialogue & conversation quality] [Major]
Location: End of section "Авіаційна та морська лексика"
Issue: The text completely ignores the mandatory `dialogue_situations` plan point (setting at the Black Sea, parents and kids talking about swimming to a buoy and a boat sailing to an island).
Fix: Add the mandatory dialogue scene at the end of the dialogues section.

[Structural integrity] [Major]
Location: Deterministic word count check at the bottom.
Issue: The module word count is 5147 words, which is massively over the target of 4000 words.
Fix: None for the fix block, but heavily penalized in scoring.

## Verdict: REVISE
The module contains a critical linguistic error ("зльот"), fails to incorporate a mandatory dialogue setting, misses several required examples, and places an exercise out of logical sequence. These issues can be corrected deterministically.

<fixes>
- find: "починається найемоційніший момент — стрімкий **зльот** *(take-off)* літака"
  replace: "починається найемоційніший момент — стрімкий **зліт** *(take-off)* літака"
- find: "Я приїхав у головний міжнародний **аеропорт** *(airport)* нашої столиці. Я знав,"
  replace: "Я приїхав у міжнародний **аеропорт Бориспіль** *(Boryspil airport)* поблизу нашої столиці. Я знав,"
- find: "За таким самим принципом утворюються й інші важливі форми: **доплисти** *(to swim all the way to)*, **обплисти** *(to sail/swim around)*, **проплисти** *(to sail/swim past or cover a distance)*. Щоб набагато краще зрозуміти"
  replace: "За таким самим принципом утворюються й інші важливі форми: **доплисти** *(to swim all the way to)*, **обплисти** *(to sail/swim around)*, **проплисти** *(to sail/swim past or cover a distance)*. Наприклад: «Ми швидко **обпливли** цей острів за один день» *(We sailed around this island in one day)*. Щоб набагато краще зрозуміти"
- find: "сміливо використовуйте префікс про- і дієслово **проплисти** *(to sail/swim past or cover distance)*. Наприклад, ви можете гордо розповісти друзям: «Під час учорашніх міських змагань ми дуже швидко **проплили** цілих п'ять кілометрів» *(During yesterday's city competition we very quickly swam a whole five kilometers)*."
  replace: "сміливо використовуйте префікс про- і дієслово **проплисти** *(to sail/swim past or cover distance)*. Наприклад: «Ми швидко **проплили** повз зелений острів» *(We quickly sailed past the green island)*. Або ж про відстань: «На змаганнях ми дуже швидко **проплили** цілих п'ять кілометрів» *(At the competition we very quickly swam a whole five kilometers)*."
- find: "<!-- INJECT_ACTIVITY: quiz, Focus on choosing летіти/літати or пливти/плавати and correct prefix based on context, 8 items -->\n<!-- INJECT_ACTIVITY: fill-in, Complete airport and maritime sentences with correct prefixed motion verbs, 8 items -->\n<!-- INJECT_ACTIVITY: error-correction, Fix incorrect air/water motion verb forms (wrong prefix, wrong base verb), 6 items -->\n\n## Авіаційна та морська лексика"
  replace: "<!-- INJECT_ACTIVITY: quiz, Focus on choosing летіти/літати or пливти/плавати and correct prefix based on context, 8 items -->\n<!-- INJECT_ACTIVITY: error-correction, Fix incorrect air/water motion verb forms (wrong prefix, wrong base verb), 6 items -->\n\n## Авіаційна та морська лексика"
- find: "<!-- INJECT_ACTIVITY: match-up, Match aviation/maritime vocabulary (рейс, пором, причал, палуба) with definitions in Ukrainian, 8 items -->\n<!-- INJECT_ACTIVITY: free-write, Write a travel story involving both a flight and a ferry trip using 6+ prefixed verbs from the module, 6 items -->\n\n## Переносні значення: час летить, думки пливуть"
  replace: "<!-- INJECT_ACTIVITY: fill-in, Complete airport and maritime sentences with correct prefixed motion verbs, 8 items -->\n<!-- INJECT_ACTIVITY: match-up, Match aviation/maritime vocabulary (рейс, пором, причал, палуба) with definitions in Ukrainian, 8 items -->\n<!-- INJECT_ACTIVITY: free-write, Write a travel story involving both a flight and a ferry trip using 6+ prefixed verbs from the module, 6 items -->\n\n## Переносні значення: час летить, думки пливуть"
- find: "**Олена:** На верхню палубу, будь ласка. *(To the upper deck, please.)*\n\n<!-- INJECT_ACTIVITY:"
  replace: "**Олена:** На верхню палубу, будь ласка. *(To the upper deck, please.)*\n\n**На Чорному морі (At the Black Sea):**\n**Батьки:** Дивіться, як красиво! Чайки летять над морем, а он там, дуже високо, літак пролетів над нами. *(Look how beautiful! Seagulls are flying over the sea, and over there, very high up, a plane flew above us.)*\n**Діти:** Ми хочемо плавати! Можна ми попливемо до того великого жовтого буйка? *(We want to swim! Can we swim to that big yellow buoy?)*\n**Батьки:** Так, але не запливайте за нього. А завтра ми купимо квитки, і наш човен попливе на той зелений острів. *(Yes, but don't swim past it. And tomorrow we will buy tickets, and our boat will sail to that green island.)*\n**Діти:** Ура! Ми дуже любимо плавати в морі! *(Hooray! We really love swimming in the sea!)*\n\n<!-- INJECT_ACTIVITY:"
</fixes>

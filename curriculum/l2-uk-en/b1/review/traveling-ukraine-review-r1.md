## Linguistic Scan
- `включіть постіль у вартість` — Calque/literal translation of "include bedding in the price". Natural Ukrainian uses "додайте постіль" or simply "з постіллю".
- `знаходяться` — Common stylistic calque from Russian "находиться". Better: "розташовані" або "містяться".
- `на відому гору Говерла` — Grammatical declension error. Appositions with common nouns (гора, річка) decline: "на гору Говерлу".
- No Russianisms found. `відправлятися` vs `відходити` is explicitly and correctly taught as a decolonization point.

## Exercise Check
- `<!-- INJECT_ACTIVITY: group-sort-transport-categories -->` — Correctly placed after Section 1.
- `<!-- INJECT_ACTIVITY: error-correction-travel-calques -->` — Correctly placed after Section 2.
- `<!-- INJECT_ACTIVITY: quiz-motion-prefixes-context -->` — **Issue:** Placed at the end of Section 2, BEFORE the actual prefix meanings (`ви-`, `від-`, `про-`, `пере-`, etc.) are systematically taught in Section 3 and 5. Must be moved after Section 3.
- `<!-- INJECT_ACTIVITY: match-up-focus-matching-landmarks-with-their-respective-cities-and-regions -->` — Correctly placed after Section 3.
- `<!-- INJECT_ACTIVITY: fill-in-focus-completing-navigation-dialogues-with-motion-verbs-and-spatial-prepositions -->` — Correctly placed after Section 4.
- `<!-- INJECT_ACTIVITY: free-write-trip-report -->` — Correctly placed after Section 5.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 5/10 | The text completely omitted the "Planning a two-week road trip" dialogue with the traveling couple ("Спочатку поїдемо до Львова..."). It also missed specific landmarks (`Софійський собор`, `Чернігів`, `Ужгород`) and the specific model narrative sequence in Section 3 ("Зайшли до готелю", "Обійшли центр", "Підійшли до водоспаду Пробій"). |
| 2. Linguistic accuracy | 7/10 | Found a grammatical apposition error: "на відому гору Говерла". Found stylistic calques: "знаходяться" (розташовані) and "включіть постіль у вартість" (додайте постіль). |
| 3. Pedagogical quality | 9/10 | Good PPP flow. Explanations of "орудний відмінок без прийменника" for geography are excellent and naturally integrated. |
| 4. Vocabulary coverage | 7/10 | Required word `зворотний квиток` missing (used `туди й назад` instead). Recommended words `хостел`, `провулок`, `навпроти` are missing. |
| 5. Exercise quality | 7/10 | The `quiz-motion-prefixes-context` is placed at the end of Section 2, which breaks pedagogical sequencing because it tests prefixes before they are taught in Section 3. |
| 6. Engagement & tone | 9/10 | The tone is warm and encouraging. Good use of conversational transitions ("Давайте детально подивимося..."). |
| 7. Structural integrity | 10/10 | Clean markdown. Word count is 5253 words, well above the 4000-word target. |
| 8. Cultural accuracy | 10/10 | Excellent decolonization notes on transport vocabulary (`відходити/виїжджати` instead of `відправлятися`). Authentic geographical routing. |
| 9. Dialogue & conversation quality | 8/10 | The ticket purchase and airport dialogues are natural and communicative, though the absence of the required planning dialogue impacts the score. |

## Findings
[1. Plan adherence] [Critical]
Location: Section 1 (or anywhere in the text)
Issue: The mandatory dialogue situation "Planning a two-week road trip across Ukraine" featuring a traveling couple ("Спочатку поїдемо до Львова...") is completely missing.
Fix: Insert the full planning dialogue at the end of Section 1.

[1. Plan adherence] [Major]
Location: Section 3 (Маршрут: від Києва до Карпат)
Issue: Missing the specific narrative sequence ("Зайшли до готелю", "Обійшли центр", "Підійшли до водоспаду Пробій") and specific landmarks (`Софійський собор`, `Чернігів`, `Кам'янець-Подільський`, `Ужгород`).
Fix: Integrate the missing landmarks into the geographical descriptions and append the missing narrative actions to the arrival in Yaremche.

[4. Vocabulary coverage] [Major]
Location: Section 2 & 4
Issue: Missing plan vocabulary: `зворотний квиток`, `хостел`, `провулок`, `навпроти`.
Fix: Replace `туди й назад` with `зворотний квиток`, add `хостел` to the booking sentence, and add `провулок`/`навпроти` to the city navigation vocabulary.

[2. Linguistic accuracy] [Major]
Location: Section 2 (На вокзалі та в аеропорту)
Issue: Literal translation calque: "обов'язково включіть постіль у вартість".
Fix: Change to "обов'язково додайте постіль".

[2. Linguistic accuracy] [Major]
Location: Section 3 (Маршрут: від Києва до Карпат)
Issue: Stylistic calque: "Також там знаходяться легендарні та популярні Потьомкінські сходи."
Fix: Change "знаходяться" to "розташовані".

[2. Linguistic accuracy] [Critical]
Location: Section 3 (Маршрут: від Києва до Карпат)
Issue: Grammatical declension error in apposition: "на відому гору Говерла". Common nouns require proper nouns to decline in this structure.
Fix: Change to "на відому гору Говерлу".

[5. Exercise quality] [Major]
Location: End of Section 2
Issue: `quiz-motion-prefixes-context` is placed prematurely, testing material taught in Section 3.
Fix: Relocate the injection marker to the end of Section 3.

## Verdict: REVISE
The text is well-written and exceeds the word target, but it fails to include a mandated dialogue and several specific narrative sequences from the plan. It also contains a grammatical error (`гору Говерла`) and a premature exercise placement. Fixes are provided below to restore the missing plan requirements and correct the linguistic flaws.

<fixes>
- find: "значно легшою та набагато приємнішою."
  replace: |
    значно легшою та набагато приємнішою.
    
    Давайте послухаємо, як пара мандрівників планує свою велику двотижневу подорож Україною:
    
    > — **Олена:** У нас є цілих два тижні! Який у нас буде точний маршрут?
    > — **Максим:** **Спочатку поїдемо до Львова** *(First we will go to Lviv)*. Ми давно хотіли там погуляти.
    > — **Олена:** Чудова ідея. **Потім заїдемо в Карпати** *(Then we will drop by the Carpathians)* на кілька днів. Я хочу в гори.
    > — **Максим:** Добре. З Карпат ми **доїдемо до Одеси за два дні** *(will reach Odesa in two days)*, щоб побачити море.
    > — **Олена:** А як ми повернемося додому?
    > — **Максим:** З Одеси ми **перелетимо до Харкова** *(will fly over to Kharkiv)*, а звідти вже поїдемо назад.
    > — **Олена:** Ідеальний план! Я вже зараз почну бронювати готелі.
- find: "бронювати *(to book)* необхідні квитки та затишне житло через інтернет."
  replace: "бронювати *(to book)* необхідні квитки, дорогий готель або молодіжний **хостел** *(hostel)* через інтернет."
- find: "чи ви хочете одразу купити туди й назад *(round trip)*?"
  replace: "чи ви хочете одразу купити **зворотний квиток** *(return ticket)*?"
- find: "обов'язково включіть постіль у вартість. Скільки коштує"
  replace: "обов'язково додайте постіль. Скільки коштує"
- find: "<!-- INJECT_ACTIVITY: error-correction-travel-calques -->\n<!-- INJECT_ACTIVITY: quiz-motion-prefixes-context -->"
  replace: "<!-- INJECT_ACTIVITY: error-correction-travel-calques -->"
- find: "<!-- INJECT_ACTIVITY: match-up-focus-matching-landmarks-with-their-respective-cities-and-regions -->"
  replace: "<!-- INJECT_ACTIVITY: match-up-focus-matching-landmarks-with-their-respective-cities-and-regions -->\n<!-- INJECT_ACTIVITY: quiz-motion-prefixes-context -->"
- find: "Звідси ми вже пішки з великою радістю пішли прямо до нашого дерев'яного готелю. Наша довга транзитна подорож завершилася успішно."
  replace: "Ми швидко **зайшли до готелю** *(went into the hotel)*, щоб залишити речі, і відразу **вийшли на прогулянку** *(went out for a walk)*. Ми із задоволенням **обійшли центр містечка** *(walked around the town center)* та зблизька **підійшли до водоспаду Пробій** *(walked up to the Probiy waterfall)*. Наша довга подорож завершилася успішно."
- find: "А дуже відома Києво-Печерська Лавра яскраво сяє своїми золотими куполами на зелених схилах могутнього Дніпра."
  replace: "А дуже відома Києво-Печерська Лавра яскраво сяє своїми золотими куполами на зелених схилах Дніпра. Не менш вражаючим є і величний **Софійський собор**."
- find: "Також там знаходяться легендарні та популярні Потьомкінські сходи."
  replace: "Також там розташовані легендарні та популярні Потьомкінські сходи."
- find: "найвищу точку України — відому гору Говерла."
  replace: "найвищу точку України — відому гору Говерлу. Ви також можете поїхати до інших історичних міст, таких як стародавній **Чернігів**, середньовічний **Кам'янець-Подільський** з його фортецею або європейський **Ужгород** на Закарпатті."
- find: "це місце традиційно називається **на перехресті** *(at the intersection)*. Для"
  replace: "це місце традиційно називається **на перехресті** *(at the intersection)*. Якщо вам потрібна дуже маленька вулиця, ви шукаєте **провулок** *(lane / alley)*. А якщо ваш готель стоїть через дорогу від парку, ви скажете, що він розташований **навпроти** *(opposite)*. Для"
</fixes>

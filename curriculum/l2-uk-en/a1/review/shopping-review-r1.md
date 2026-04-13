## Linguistic Scan
- `:::tip` note: “You might sometimes hear the word «буханка» used for a loaf of bread, but this is an incorrect Russian calque.” This is a factual error. Local verification shows `буханка` exists in VESUM, and СУМ-11 defines it as a Ukrainian word for a loaf of bread.

## Exercise Check
- 4/4 planned markers are present: `fill-in-prices`, `quiz-currency`, `match-up-locations`, `fill-in-quantities`.
- Marker placement is mostly correct: price exercises follow the price section, the locations exercise follows the locations section, and quantities come after quantity teaching.
- Issue: the generated locations exercise includes `кава: кафе` and `борщ: ресторан`, but the prose before `<!-- INJECT_ACTIVITY: match-up-locations -->` teaches only `магазин`, `супермаркет`, `ринок`, `аптека`, `крамниця`, `м'ясний відділ`, and `молочний відділ`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The supermarket dialogue covers `хліб`, `молоко`, and `сир`, but misses the planned price-comparison items `ковбаса` and `масло`; the module also rejects `буханка`, which the plan’s quantity activity expects. |
| 2. Linguistic accuracy | 6/10 | The tip says `«буханка» ... is an incorrect Russian calque`, but local dictionary verification attests `буханка` as Ukrainian. |
| 3. Pedagogical quality | 6/10 | The lesson opens with a long English paragraph (“Shopping in Ukraine blends modern convenience with traditional culture...”) before any Ukrainian, then adds more English meta-explanation after short dialogues, weakening PPP and A1 practice density. |
| 4. Vocabulary coverage | 8/10 | Required/recommended vocabulary is broadly present (`коштувати`, `скільки`, `гривня`, `ціна`, `ринок`, `знижка`, `гроші`, `готівка`), but the loaf-of-bread vocabulary becomes confusing because `буханка` is later mislabelled as wrong. |
| 5. Exercise quality | 7/10 | All four markers are present and sensibly placed, but the locations exercise tests `кафе` and `ресторан` before those place words are taught. |
| 6. Engagement & tone | 7/10 | The tone is teacherly, but filler like “This makes the local market the perfect place to practice your Ukrainian communication skills” adds words without adding much lesson value. |
| 7. Structural integrity | 9/10 | All planned H2 headings are present and in order; pipeline word count is 1641, so the module is comfortably above the 1200-word target. |
| 8. Cultural accuracy | 7/10 | The market/supermarket framing is fine, but the categorical claim that `буханка` is a Russian calque misrepresents Ukrainian usage. |
| 9. Dialogue & conversation quality | 6/10 | The market dialogue is usable, but the supermarket dialogue stays thin and misses the planned comparison set `ковбаса`/`масло`. |

## Findings
- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `You might sometimes hear the word «буханка» used for a loaf of bread, but this is an incorrect Russian calque.`  
Issue: This teaches false Ukrainian. `буханка` is attested in VESUM and СУМ-11.  
Fix: Replace the categorical warning with a neutral note that `буханка`, `буханець`, and `хлібина` all exist, while `буханець`/`хлібина` can be presented as good everyday options.

- [PLAN ADHERENCE] [SEVERITY: major]  
Location: supermarket dialogue: `Мама: Вибачте, де тут хліб?... Дочка: Мамо, скільки коштує цей сир?...`  
Issue: The plan’s supermarket comparison explicitly includes `хліб`, `молоко`, `сир`, `ковбаса`, and `масло`, but the written dialogue never adds `ковбаса` or `масло`.  
Fix: Extend the supermarket dialogue with short price-comparison lines for `ковбаса` and `масло`.

- [EXERCISE QUALITY] [SEVERITY: major]  
Location: section before `<!-- INJECT_ACTIVITY: match-up-locations -->`  
Issue: The generated locations exercise includes `кава: кафе` and `борщ: ресторан`, but those locations are not taught before the marker.  
Fix: Add one brief sentence introducing `кафе` and `ресторан` before the marker.

- [PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: opening paragraph `Shopping in Ukraine blends modern convenience with traditional culture...`; post-dialogue paragraphs `Let's look at the key phrases used in this conversation...` and `In a large store, navigating is your first priority...`  
Issue: Too much English meta-explanation inflates sections and reduces A1 teaching density. The lesson spends many words describing shopping in English instead of moving quickly from situation to Ukrainian pattern to practice.  
Fix: Compress these English paragraphs to short signposting sentences and keep the focus on the Ukrainian chunks.

## Verdict: REVISE
REVISE. There is one critical factual language error (`буханка`), plus multiple major issues in plan adherence, exercise alignment, and pedagogy.

<fixes>
- find: |-
    Shopping in Ukraine blends modern convenience with traditional culture. A large **супермаркет** (supermarket) offers everything under one roof, with clear price tags and self-checkout counters. However, if you want the freshest vegetables, seasonal fruit, or a chance to speak directly with the people who grow your food, you must visit a **ринок** (market). At the market, there are rarely printed price tags on every item; you must ask the seller directly. This makes the local market the perfect place to practice your Ukrainian communication skills. Let's see how a typical interaction unfolds when buying fresh produce.
  replace: |-
    In Ukraine, you can shop in a **супермаркет** (supermarket) or at a **ринок** (market). At the market, you often ask the seller directly about prices, so it is a useful place to practice shopping phrases.

- find: |-
    Let's look at the key phrases used in this conversation. To ask for an item politely, the shopper uses the phrase **Дайте, будь ласка...** (Give me, please...). This is the standard, most natural way to request something from a seller in Ukraine. Notice how the shopper states both the quantity and the item clearly together: **кілограм яблук** (a kilogram of apples) and **два кілограми помідорів** (two kilograms of tomatoes). The prices are spoken directly as numbers followed by the currency. There is no need for complex sentences; short, clear, and direct phrases are exactly how native speakers handle transactions.
  replace: |-
    Key phrases here are **Дайте, будь ласка...**, **кілограм яблук**, and **два кілограми помідорів**. At A1, learn them as short shopping chunks.

- find: |-
    > **(У супермаркеті / At the supermarket)**
    > **Мама:** Вибачте, де тут хліб? *(Excuse me, where is the bread here?)*
    > **Працівник:** Хліб у третьому ряду. *(The bread is in the third aisle.)*
    > **Мама:** А молоко? *(And the milk?)*
    > **Працівник:** Молоко в холодильнику, там. *(The milk is in the fridge, there.)*
    > **Дочка:** Мамо, скільки коштує цей сир? *(Mom, how much does this cheese cost?)*
    > **Мама:** Сто двадцять гривень. *(One hundred twenty hryvnias.)*
    > **Дочка:** Дорого! А є дешевший? *(Expensive! Is there a cheaper one?)*
    > **Мама:** Так, ось цей — вісімдесят. *(Yes, this one — eighty.)*
  replace: |-
    > **(У супермаркеті / At the supermarket)**
    > **Мама:** Вибачте, де тут хліб? *(Excuse me, where is the bread here?)*
    > **Працівник:** Хліб у третьому ряду. *(The bread is in the third aisle.)*
    > **Мама:** А молоко? *(And the milk?)*
    > **Працівник:** Молоко в холодильнику, там. *(The milk is in the fridge, there.)*
    > **Дочка:** Мамо, скільки коштує цей сир? *(Mom, how much does this cheese cost?)*
    > **Мама:** Сто двадцять гривень. *(One hundred twenty hryvnias.)*
    > **Дочка:** Дорого! А є дешевший? *(Expensive! Is there a cheaper one?)*
    > **Мама:** Так, ось цей — вісімдесят. *(Yes, this one — eighty.)*
    > **Дочка:** А скільки коштує ковбаса? *(And how much does the sausage cost?)*
    > **Працівник:** Ковбаса — сто двадцять гривень. *(The sausage is one hundred twenty hryvnias.)*
    > **Мама:** А масло? *(And the butter?)*
    > **Працівник:** Шістдесят п'ять гривень. *(Sixty-five hryvnias.)*

- find: |-
    In a large store, navigating is your first priority. You ask for directions using **де тут...** (where is... here). You can also naturally react to prices using adjectives: if a product costs too much money, you can exclaim **Дорого!** (Expensive!), or you can ask a worker for something **дешевший** (cheaper).
  replace: |-
    In a large store, **де тут...?**, **Дорого!**, and **А є дешевший?** are useful short phrases.

- find: |-
    *   **Вибачте, де молочний відділ?** *(Excuse me, where is the dairy section?)*
    *   **М'ясний відділ там, у другому ряду.** *(The meat section is there, in the second aisle.)*

    <!-- INJECT_ACTIVITY: match-up-locations -->
  replace: |-
    *   **Вибачте, де молочний відділ?** *(Excuse me, where is the dairy section?)*
    *   **М'ясний відділ там, у другому ряду.** *(The meat section is there, in the second aisle.)*

    For drinks or prepared food, you might also go to a **кафе** (cafe) or a **ресторан** (restaurant).

    <!-- INJECT_ACTIVITY: match-up-locations -->

- find: |-
    You might sometimes hear the word «буханка» used for a loaf of bread, but this is an incorrect Russian calque. The natural, authentic Ukrainian word is **буханець** or **хлібина**.
  replace: |-
    You might sometimes hear the words «буханка», «буханець», or «хлібина» for a loaf of bread. **Буханець** and **хлібина** are good everyday Ukrainian options, and **буханка** also exists in Ukrainian.
</fixes>
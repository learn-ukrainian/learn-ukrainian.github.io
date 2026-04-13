## Linguistic Scan
- Incorrect grammar claim in **Скільки коштує?**: “**Notice how the last digit entirely determines the currency's form.**” This is false. `11–14` take `гривень`, so the last digit alone does not determine the form.

## Exercise Check
Markers present and correctly distributed: `fill-in-prices`, `quiz-currency`, `match-up-locations`, `fill-in-quantities`.

All four markers appear after the relevant teaching sections and align with the four `activity_hints` in the plan. No inline DSL exercise logic was present to audit beyond these markers.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All planned H2 sections are present, but the middle sections overshoot the 300-word plan budgets substantially: `Скільки коштує?` and `Де купити?` are roughly 436 and 440 words, driven by long English exposition such as “**This is a fundamental rule of noun-number agreement in Ukrainian.**” and side material like the loaf-variant tip block. |
| 2. Linguistic accuracy | 7/10 | “**Notice how the last digit entirely determines the currency's form.**” teaches an incorrect rule; `11–14` require `гривень`. |
| 3. Pedagogical quality | 7/10 | The module often explains grammar abstractly in English instead of keeping A1 patterning tight, e.g. “**It takes a form called the genitive case, which indicates "of something"**...”. The summary also expands the payment pattern to “**Можна карткою чи потрібна готівка?**”, although the taught chunk is just `Можна карткою?`. |
| 4. Vocabulary coverage | 9/10 | Required and recommended vocabulary are well represented in prose: `знижка`, `гроші`, `готівка`, `кілограм`, `літр`, `пляшка`, `пачка`, `супермаркет`, `ринок`. |
| 5. Exercise quality | 9/10 | All four planned exercise markers appear once each and follow the relevant teaching content. Marker coverage and placement are strong. |
| 6. Engagement & tone | 8/10 | Tone is teacherly and not gamified, but some filler/meta phrasing adds words without much extra learner value, e.g. “**The most important question in your shopping toolkit...**” and “**This is a fundamental rule...**”. |
| 7. Structural integrity | 9/10 | All required H2 headings are present and in order, and the pipeline word count is 1525, above target. The main weakness is section sprawl in the middle. |
| 8. Cultural accuracy | 9/10 | The module stays in Ukrainian shopping contexts (`ринок`, `супермаркет`, `аптека`) and avoids Russian-centric framing. |
| 9. Dialogue & conversation quality | 9/10 | The market dialogue is natural, multi-turn, and usable. The supermarket dialogue is functional and anchored in a real shopping situation. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: **Скільки коштує?** — “**Let's apply numbers directly to prices. Notice how the last digit entirely determines the currency's form.**”  
Issue: This teaches a wrong grammar rule. Ukrainian currency forms are not determined entirely by the last digit; `11–14` take `гривень`.  
Fix: Change the sentence to state the exception explicitly.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: **Скільки коштує?** — from “**The most important question in your shopping toolkit...**” through the pricing/reaction paragraphs  
Issue: This section is far above the plan’s 300-word budget and spends too many words on English meta-explanation instead of concise A1 patterning.  
Fix: Condense the English exposition so the section focuses on the core patterns and examples.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: **Де купити?** — from “**Where exactly do you go to купувати...**” through the grocery-trip example and `:::tip` loaf note  
Issue: This section is also far above the 300-word budget because of side notes and extra explanation not essential to the plan’s A1 scope.  
Fix: Trim the side material and keep only the core shopping-location and quantity chunks.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: **Підсумок — Summary** — “**Можна карткою чи потрібна готівка?**”  
Issue: The self-check answer introduces a new structure (`чи потрібна...`) instead of rehearsing the taught target chunk from the plan (`Можна карткою?`).  
Fix: Replace it with the taught phrase `Можна карткою?`.

## Verdict: REVISE
REVISE. The module is structurally sound and exercise placement is good, but it contains one critical factual grammar error and multiple major pacing/pedagogy issues that should be fixed before shipping.

<fixes>
- find: |
    Let's apply numbers directly to prices. Notice how the last digit entirely determines the currency's form.
  replace: |
    Let's apply numbers directly to prices. Notice how the final number usually determines the currency's form, except 11-14, which take **гривень**.
- find: |
    The most important question in your shopping toolkit is **Скільки коштує...?** (How much does it cost?). You must pay close attention to the item you are asking about, as the verb must agree with the noun. If you are buying a single or uncountable item, use the singular verb form **коштує**. If you are pointing to a plural item, the verb must take the plural form **коштують**.
  replace: |
    The key shopping question is **Скільки коштує...?** (How much does it cost?). For one item or something uncountable, use **коштує**. For plural items, use **коштують**.
- find: |
    The official currency of Ukraine is the **гривня** (hryvnia). When stating a **ціна** (price), the ending of the word changes depending on the specific number before it. This is a fundamental rule of noun-number agreement in Ukrainian.
  replace: |
    The official currency of Ukraine is the **гривня** (hryvnia). Its form changes after numbers: **гривня** after 1 (except 11), **гривні** after 2-4 (except 12-14), and **гривень** after 5-9, 0, and 11-19.
- find: |
    The smaller unit of currency is the **копійка** (kopeck), representing one hundredth of a hryvnia. The grammar rules for its endings are identical: **одна копійка**, **дві копійки**, **п'ять копійок**. However, physical kopecks are less common today. Prices are frequently rounded to the nearest ten kopecks or whole hryvnia, so you will hear **гривня** much more often than **копійка**.
  replace: |
    The smaller unit of currency is the **копійка** (kopeck). The pattern is the same: **одна копійка**, **дві копійки**, **п'ять копійок**.
- find: |
    Before handing over your **гроші** (money), you might react to the final total. If you feel it is too high, exclaim **Дорого!** (Expensive!). If it is a fantastic deal, happily say **Дешево!** (Cheap!) or **Нормальна ціна.** (Fair price.). To ask for the final sum, use **Скільки за все?** (How much for everything?). You might also politely ask **Є знижка?** (Is there a discount?).
  replace: |
    Before paying, you can react to the price with **Дорого!**, **Дешево!**, or **Нормальна ціна.** To ask for the total, say **Скільки за все?** To ask about a discount, say **Є знижка?**
- find: |
    Where exactly do you go to **купувати** (to buy) what you need? A standard shop is called a **магазин** (shop), while a very large one is a **супермаркет** (supermarket). A smaller, local shop is often called a **крамниця** (store — an authentic Ukrainian synonym for магазин). For fresh produce or homemade goods, you visit the **ринок** (market). Finally, for medicine or vitamins, you go to an **аптека** (pharmacy).
  replace: |
    You can buy things in a **магазин** (shop), **супермаркет** (supermarket), or **крамниця** (store). For fresh produce, go to the **ринок** (market). For medicine, go to an **аптека** (pharmacy).
- find: |
    For drinks or prepared food, you might also go to a **кафе** (cafe) or a **ресторан** (restaurant).
  replace: ""

- find: |
    When asking for a product, you rarely ask for just "water" or "apples"; you specify an exact quantity. In Ukrainian grammar, the item following a quantity word changes its ending. It takes a form called the genitive case, which indicates "of something" (like a liter *of* milk). At this introductory level, simply learn these combinations as fixed chunks.
  replace: |
    After quantity words, learn the noun as a chunk: **кілограм яблук**, **літр молока**, **пляшка води**. At A1, memorizing these combinations is enough.
- find: |
    Here is how you might describe a quick trip to the grocery store:

    > **Я йду в супермаркет. Я купую літр молока і два кілограми яблук. Вони дуже свіжі.**
    > *(I am going to the supermarket. I am buying a liter of milk and two kilograms of apples. They are very fresh.)*
  replace: ""

- find: |
    :::tip
    You might sometimes hear the words «буханка», «буханець», or «хлібина» for a loaf of bread. **Буханець** and **хлібина** are good everyday Ukrainian options, and **буханка** also exists in Ukrainian.
    :::
  replace: ""

- find: |
        *   **Можна карткою чи потрібна готівка?** *(Can I pay by card or is cash needed?)*
  replace: |
        *   **Можна карткою?** *(Can I pay by card?)*
</fixes>
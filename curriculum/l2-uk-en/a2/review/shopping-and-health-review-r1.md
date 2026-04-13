## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym errors, or Russian-only letters were found in the Ukrainian examples.

One factual grammar error was found in the explanation:
- `Any number from five onwards takes the Genitive Plural.` This is false. Repo textbook data states that with compound numerals, the noun follows the last component: `двадцять три дні`, but `двадцять п'ять днів`.

## Exercise Check
All 4 activity markers are present exactly once, and each comes after the relevant teaching section:
- `fill-in-complete-market-dialogue-lines-with-correct-quantity-genitive-forms` after the market section
- `quiz-choose-the-correct-genitive-phrase-for-health-complaints-and-remedies` after the doctor section
- `match-up-match-health-problems-to-their-remedies` after the pharmacy/remedies section
- `true-false-judge-whether-shopping-and-health-phrases-use-the-genitive-correctly` after the final consolidation

Marker IDs match the plan’s `activity_hints`. No inline DSL exercises were present to audit for answer logic.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The three planned sections are present and the target vocab is embedded in prose (`кілограм яблук`, `немає температури`, `ліки від кашлю`). But the market section never teaches the explicit plan point `по скільки? — дорого/дешево/нормально`, and the vendor never offers a taste or alternative although the plan calls for that. |
| 2. Linguistic accuracy | 7/10 | The Ukrainian examples are clean, but the rule `Any number from five onwards takes the Genitive Plural` is factually wrong; textbook evidence in the repo gives `двадцять три дні` vs. `двадцять п'ять днів`. |
| 3. Pedagogical quality | 7/10 | The module has strong contextual examples (`У мене болить...`, `немає температури`, `краплі від нежиті`), but it muddies the target pattern by teaching `немає + Genitive` and then switching to `Але я зовсім не маю апетиту.` without explanation. |
| 4. Vocabulary coverage | 10/10 | All required plan words appear naturally (`ринок`, `здоров'я`, `температура`, `аптека`, `ліки`, `кашель`, `апетит`), and recommended words also appear in context (`помідорів`, `нежиті`, `алергія`, `таблетки`, `шматок`). |
| 5. Exercise quality | 10/10 | All four markers appear once and after the relevant teaching block; the sequence matches the plan cleanly. |
| 6. Engagement & tone | 7/10 | The teacher voice is serviceable (`Let us look at...`, `Notice how...`), but the closing summary slips into filler: `The Genitive case is the ultimate connector in everyday Ukrainian life` and `Це дуже корисна і важлива граматика.` |
| 7. Structural integrity | 10/10 | All H2 headings from the plan are present and in order, the markdown is clean, and the pipeline word count is 2848, well above the 2000 target. |
| 8. Cultural accuracy | 9/10 | The module stays in Ukrainian contexts (`ринок`, `аптека`, `поліклініка`) and does not define Ukrainian through Russian. |
| 9. Dialogue & conversation quality | 7/10 | Speaker labels are clear, but the market dialogue stays mostly request-price-payment (`Дайте...`, `З вас дев'яносто гривень`) instead of the richer market interaction promised in the plan. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `The Genitive case is strictly required after numbers five and above. This "five plus" rule is essential for handling money and quantities. Any number from five onwards takes the Genitive Plural.`  
Issue: This teaches a false rule. Compound numerals follow the last component, so `двадцять три яблука` is not Genitive Plural, while `двадцять п'ять яблук` is.  
Fix: Replace the rule with a formulation that distinguishes plain `5+` numerals from compound numerals whose last word controls the noun form.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `When buying, pay attention to whether the item is singular or plural. You ask "Скільки коштує?" for singular, but "Скільки коштують?" for plural. Vendors often use diminutives to sound friendly.`  
Issue: The explicit plan point `по скільки? — дорого/дешево/нормально` is missing. I searched the content for `по скільки`, `дорого`, `дешево`, and `нормально`; all occur 0 times.  
Fix: Expand this paragraph with the missing price-question pattern and evaluation phrases.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `> — **Продавець:** Які красиві яблука! Вони дуже солодкі і соковиті. Яблука з мого саду.`  
Issue: The plan explicitly says the vendor should offer a taste and suggest alternatives, but the market dialogue never does. I searched for `спробуйте`, `скуштуйте`, and `альтерн`; all occur 0 times.  
Fix: Add a vendor line that offers a taste and mentions an alternative variety.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `> — **Пацієнт:** Ні, температури немає. Але я зовсім не маю апетиту. *(No, there is no fever. But I have absolutely no appetite.)*`  
Issue: The section explicitly teaches `немає + Genitive`, then immediately switches to another structure without explanation. That weakens focused practice of the target pattern.  
Fix: Keep the dialogue on-pattern with `У мене зовсім немає апетиту.`

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `The Genitive case is the ultimate connector in everyday Ukrainian life...` / `Це дуже корисна і важлива граматика.`  
Issue: The ending is generic filler rather than a concrete recap of the three Genitive uses taught in the module.  
Fix: Replace the closing with a compact comparison of the actual patterns: quantity, absence, and remedy/cause.

## Verdict: REVISE
REVISE. The module is structurally solid and the exercise markers are well placed, but it contains one critical grammar error plus several major plan/pedagogy misses.

<fixes>
- find: |
    The Genitive case is strictly required after numbers five and above. This "five plus" rule is essential for handling money and quantities. Any number from five onwards takes the Genitive Plural.
  replace: |
    The Genitive Plural is required after numbers like five, six, ten, or thirty: п'ять кілограмів, десять гривень, тридцять яблук. But compound numerals follow the last component: двадцять три яблука, but twenty five apples = двадцять п'ять яблук.

- find: |
    When buying, pay attention to whether the item is singular or plural. You ask "Скільки коштує?" for singular, but "Скільки коштують?" for plural. Vendors often use diminutives to sound friendly.
  replace: |
    When buying, pay attention to whether the item is singular or plural. You ask "Скільки коштує?" for singular, but "Скільки коштують?" for plural. You will also hear "По скільки помідори?" at the market, and people often react with words like "дорого", "дешево", or "нормально". Vendors often use diminutives to sound friendly.

- find: |
    > — **Продавець:** Які красиві яблука! Вони дуже солодкі і соковиті. Яблука з мого саду.
  replace: |
    > — **Продавець:** Які красиві яблука! Вони дуже солодкі і соковиті. Яблука з мого саду. Спробуйте одне. Якщо хочете кисліші, є ще інший сорт.

- find: |
    > — **Пацієнт:** Ні, температури немає. Але я зовсім не маю апетиту. *(No, there is no fever. But I have absolutely no appetite.)*
  replace: |
    > — **Пацієнт:** Ні, температури немає. У мене зовсім немає апетиту. *(No, there is no fever. I have absolutely no appetite.)*

- find: |
    The Genitive case is the ultimate connector in everyday Ukrainian life. It is essential for navigating daily situations smoothly. You use it to specify a quantity when shopping, to state that you lack a **температура** (temperature), or to say you have no **апетит** (appetite). Mastering these practical patterns will make you confident in both the market and the clinic.

    Родовий відмінок допомагає нам у багатьох життєвих ситуаціях. Ми часто просимо кілограм яблук або купуємо таблетки від болю. Також ми кажемо лікареві, що у нас немає температури. Це дуже корисна і важлива граматика.
  replace: |
    The same Genitive patterns connect both topics in this module: quantity at the market, absence of symptoms, and remedies **від** a condition. Compare these pairs: кілограм яблук, немає температури, ліки від кашлю. This is the practical overlap you should notice and practice.

    Родовий відмінок поєднує обидві теми цього модуля: кілограм яблук, немає температури, ліки від кашлю. Ті самі моделі працюють у магазині, у лікаря й в аптеці.
</fixes>
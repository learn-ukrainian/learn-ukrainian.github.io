## Linguistic Scan
- `Після цифри п'ять і більше ми завжди використовуємо родовий відмінок множини.`  
  Issue: `цифра` is the wrong term here; the rule is about `числівники`, not digits.

- `Ніколи не кажіть «да», а завжди кажіть «так».`  
  Issue: false absolute. Local dictionary data attests `да` in Ukrainian as a dialectal/conjunction form, so the module should teach standard preference for `так`, not “never”.

- `This creates a deep sense of **милозвучність**...` in the diminutives block.  
  Issue: factual misuse of `милозвучність`; diminutive suffixes are not the same concept as phonetic euphony.

## Exercise Check
4 activity markers are present, matching the 4 `activity_hints` in the plan:

- `quiz-role-play-planning-a-party-aspect-in-future-tense` after Section 1
- `fill-in-shopping-groceries` after Section 2
- `match-up-story-aspect` after Section 3
- `match-up-narrative-questions` after Section 3

Placement is mostly correct: each marker appears after the relevant teaching block, and the two Section 3 markers come after the past-aspect explanation plus reading practice. No inline DSL exercise logic is visible here, so there is no answer-key logic to audit.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All three planned sections are present and the reference is cited: `This recap follows the review logic noted in «Заболотний Grade 5-6»`. However, Section 2 spends a full block on diminutives/`да` instead of the planned market-genitive dialogue work, and Section 3 dialogue drifts into future planning: `ми будемо купувати необхідні продукти`. |
| 2. Linguistic accuracy | 6/10 | Most Ukrainian forms are clean, but the module teaches `Після цифри п'ять і більше...` (wrong grammatical term) and `Ніколи не кажіть «да»...` (false absolute). It also equates diminutives with `милозвучність`, which is inaccurate. |
| 3. Pedagogical quality | 7/10 | The module gives multiple examples for aspect and Genitive, but Section 2 burns valuable space on an off-plan diminutives lecture, and Section 3 weakens the `Що ти робив?/Що ти зробив?` target by switching back to future party logistics. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is well covered in context: `планувати`, `купувати/купити`, `готувати/приготувати`, `ринок`, `коштує`, `кілограм`, `вечірка`, `день`. `замовити` and `запланувати` also appear in the prose. |
| 5. Exercise quality | 9/10 | The module has 4 markers for 4 planned activities, and each marker comes after the material it is supposed to test. No inline exercise content is present here, so placement is the main thing to audit, and that is acceptable. |
| 6. Engagement & tone | 6/10 | The teacher voice is consistent, but the Section 2 digression becomes inflated and slogan-like, especially `Diminutives are the DNA of the Ukrainian language`, which adds heat more than instruction. |
| 7. Structural integrity | 10/10 | All H2 scenario sections are present and ordered correctly, markdown is clean, all 4 markers are intact, and the pipeline word count is 2885, which is above the 2000 target. |
| 8. Cultural accuracy | 5/10 | `Ніколи не кажіть «да»...` and the claim that diminutives create `милозвучність` both oversimplify or misstate Ukrainian usage and linguistic culture. |
| 9. Dialogue & conversation quality | 7/10 | Named speakers and real situations help, but Section 3 stops sounding like a past-events catch-up and starts sounding like future planning: `ми будемо купувати необхідні продукти`, `планую замовити смачну піцу`. |

## Findings
- [LINGUISTIC ACCURACY] [SEVERITY: critical]  
  Location: `Після цифри п'ять і більше ми завжди використовуємо родовий відмінок множини.`  
  Issue: `цифра` is the wrong grammatical term; this rule is about numerals (`числівники`), not digits.  
  Fix: Change `Після цифри` to `Після числівників`.

- [LINGUISTIC ACCURACY / CULTURAL ACCURACY / PEDAGOGICAL QUALITY] [SEVERITY: critical]  
  Location: the block beginning `A defining characteristic of spoken Ukrainian...` and including `Ніколи не кажіть «да», а завжди кажіть «так».`  
  Issue: this block is off-plan for a Genitive/market section, misdefines `милозвучність`, and teaches a false absolute about `да`.  
  Fix: Replace the whole block with a short market-dialogue follow-up that recycles `немає`, alternative requests, and Genitive forms.

- [PLAN ADHERENCE / DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
  Location: `Ви вже почали готувати якісь цікаві страви?... ми будемо купувати необхідні продукти... Я теж хочу допомогти і планую замовити смачну піцу...`  
  Issue: Section 3 is supposed to practice past narration and the `Що ти робив?/Що ти зробив?` contrast, but these turns switch back to future planning.  
  Fix: Replace these turns with a past-focused mini-dialogue using one imperfective background action and one perfective result.

## Verdict: REVISE
Critical findings are present, and multiple dimensions are below 9. The module is structurally complete and mostly usable, but it cannot ship as-is because it teaches at least two incorrect linguistic/cultural points and wastes target-section space on an off-plan digression.

<fixes>
- find: "Після цифри п'ять і більше ми завжди використовуємо родовий відмінок множини."
  replace: "Після числівників п'ять і більше ми завжди використовуємо родовий відмінок множини."
- find: |
    A defining characteristic of spoken Ukrainian, especially in hospitable settings like a neighborhood market, is the extensive use of diminutive suffixes. Vendors use these special forms not because they are talking to small children, but to sound friendly, polite, and welcoming to their customers. This creates a deep sense of **милозвучність** (euphony or sweet-sounding language) that is central to traditional Ukrainian culture.

    Ви часто почуєте на ринку такі приємні слова: солодкі мандаринки, свіжий борщик, зелена цибулька або гострий часничок. Продавці щиро пропонують вам свої найкращі продукти. Це робить їхню щоденну мову дуже живою та емоційною. Важливо також завжди пам'ятати про правильні слова для згоди. Ніколи не кажіть «да», а завжди кажіть «так».

    > *You will often hear such pleasant words at the market: sweet little mandarins, fresh little borsch, green little onions, or spicy little garlic. The vendors sincerely offer you their best products. This makes their daily language very lively and emotional. It is also important to always remember the correct words for agreement. Never say "да" (a Russian calque), but always say "так" (yes).*

    :::tip
    **Did you know?**
    Diminutives are the DNA of the Ukrainian language. Forms like мандаринки or цибулька are not just "baby talk"; they are a fully realized emotional register that adults use daily to express warmth and care.
    :::
  replace: |
    A useful market dialogue does not stop when one item is unavailable. The learner should practice short follow-up questions and alternative requests so the conversation keeps moving while recycling the Genitive case after **немає**.

    Покупець може сказати: «Шкода. Тоді дайте, будь ласка, ягоди». Продавець може відповісти: «Сиру сьогодні немає, але є свіжий мед». Такі короткі репліки тренують родовий відмінок і роблять діалог природним.

    > *A useful market dialogue does not stop when one item is unavailable. Short follow-up questions and alternative requests keep the conversation moving while recycling the Genitive case after "немає".*

    :::tip
    **Did you know?**
    At the market, short follow-up lines like «Тоді дайте, будь ласка, ягоди» or «А сир у вас є?» sound natural and keep the dialogue moving.
    :::
- find: |
    > — **Тарас:** Ви вже почали готувати якісь цікаві страви? Це буде дуже крута вечірка! *(Have you already started cooking some interesting dishes? It will be a very cool party!)*
    > — **Оксана:** Ні, спочатку ми будемо купувати необхідні продукти, а потім я зможу приготувати салати. *(No, first we will be buying necessary groceries, and then I will be able to prepare salads.)*
    > — **Тарас:** Я теж хочу допомогти і планую замовити смачну піцу для нас усіх. *(I also want to help and plan to order a delicious pizza for all of us.)*
    > — **Оксана:** Чудова ідея! Якраз вчора я змогла знайти гарний італійський ресторан неподалік. *(Great idea! Just yesterday I managed to find a nice Italian restaurant nearby.)*
  replace: |
    > — **Тарас:** А що ти робила ввечері? *(And what were you doing in the evening?)*
    > — **Оксана:** Я довго обговорювала наш план на вихідні з друзями, а потім приготувала вечерю. *(I was discussing our weekend plan with friends for a long time, and then I prepared dinner.)*
    > — **Тарас:** А що ти ще зробила? *(And what else did you get done?)*
    > — **Оксана:** Я ще замовила піцу і знайшла гарний італійський ресторан неподалік. *(I also ordered pizza and found a nice Italian restaurant nearby.)*
</fixes>
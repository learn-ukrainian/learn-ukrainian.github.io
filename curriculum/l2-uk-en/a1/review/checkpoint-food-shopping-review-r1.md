## Linguistic Scan
No linguistic errors found.

Checked against the supplied VESUM data and local verification: the core Ukrainian forms used in the prose are valid, the accusative examples are correct, and the forbidden Russian characters `ы, э, ё, ъ` do not appear.

## Exercise Check
The prose contains 4 planned exercise markers, and their placement is pedagogically sensible: 2 after `## Граматика` and 2 after `## Діалог`.

The generated exercise logic is mostly solid:
- `quiz-accusative-forms` tests exactly the accusative contrasts just taught, with varied correct-answer positions.
- `fill-in-dialogue` matches the connected-scenario language from the module.
- `quiz-situational-phrases` tests communicative function, not trivia.

Issue found:
- The module ships a marker `<!-- INJECT_ACTIVITY: group-sort-accusative -->`, but the current `activities/checkpoint-food-shopping.yaml` does not define a matching `group-sort-accusative` activity. As shipped, that planned exercise cannot inject.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 5/10 | The plan’s anchor scenario is `Hosting a вечеря ... продукти ... вареники ... тарілки ... склянки`, but none of `вареники`, `тарілки`, `склянки`, `вечеря`, `продукти` appear in the prose. The opening self-check is also broken instead of fully covering the planned M36-M40 review prompts. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, or case-ending mistakes found in the Ukrainian text. Local checks confirmed forms such as `звичайно`, `рахунок`, `карткою`, `лікаря`; banned Russian letters are absent. |
| 3. Pedagogical quality | 6/10 | The module explains the grammar correctly, but the first review tool learners see is a broken questionnaire, and the “Connected Dialogue” functions more like stitched examples than a stable model conversation. |
| 4. Vocabulary coverage | 5/10 | Core cafe/market review words appear (`борщ`, `кава з молоком`, `рахунок`, `карткою`), but the plan’s anchor consolidation vocabulary is missing from prose: `продукти`, `вечеря`, `вареники`, `тарілки`, `склянки`. |
| 5. Exercise quality | 7/10 | The visible exercises are logically correct and well placed, but `<!-- INJECT_ACTIVITY: group-sort-accusative -->` has no matching generated activity definition, so one planned exercise is missing in the shipped package. |
| 6. Engagement & tone | 6/10 | The opener and summary use generic milestone language: `Welcome to the A1.6 Checkpoint! You have reached a major milestone...` and `Congratulations on reaching the end...`, which adds little instructional value. |
| 7. Structural integrity | 6/10 | All planned H2 headings are present and the pipeline word count is 1111, but the self-check section contains a visible formatting break: `If you can answer "yes" to these questions, ** (I eat porridge.))?`. |
| 8. Cultural accuracy | 9/10 | No false cultural claims or Russian-centered framing appear. Everyday Ukrainian situations like `ринок`, `кафе`, `Рахунок, будь ласка`, and `Можна карткою?` are appropriate. |
| 9. Dialogue & conversation quality | 5/10 | The dialogue is not role-stable: `Олег` says `Потім іду на ринок`, then `Дайте кілограм`, while `Марія` suddenly jumps to `Мені борщ і воду...`. It reads like pasted example lines, not a believable interaction. |

## Findings
[STRUCTURAL INTEGRITY] [SEVERITY: major]  
Location: `## Що ми знаємо?` — `If you can answer "yes" to these questions, ** (I eat porridge.))?`  
Issue: The opening questionnaire is malformed and learner-facing text is visibly broken.  
Fix: Replace the corrupted paragraph and bullet block with a clean self-check that covers the planned review points.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: Whole module; plan anchor scenario is `Hosting a вечеря ... shopping for продукти ... cooking вареники and салат ... тарілки ... склянки`, but those words are absent from the prose.  
Issue: The module drops the plan’s declared dinner-party consolidation scenario and its anchor vocabulary.  
Fix: Revise the connected dialogue so it naturally includes `продукти`, `вечеря`, `вареники`, `тарілки`, `склянки`, and `гості` while still reviewing market/cafe language.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `## Граматика` marker `<!-- INJECT_ACTIVITY: group-sort-accusative -->`; verified absent from `activities/checkpoint-food-shopping.yaml`  
Issue: One planned exercise has no matching generated definition, so the module cannot render that activity as shipped.  
Fix: Add a real group-sort exercise or replace the dead marker with an inline sorting task.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `## Діалог` — `**Олег:** Потім іду на ринок...`, `**Олег:** Дайте кілограм...`, `**Марія:** Мені борщ і воду...`  
Issue: Speaker roles are inconsistent and transitions are abrupt, so the exchange does not model natural conversation.  
Fix: Rewrite the dialogue with stable roles and clear scene transitions.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: opening paragraph `Welcome to the A1.6 Checkpoint! You have reached a major milestone...` and summary opener `Congratulations on reaching the end...`  
Issue: The framing relies on generic pep talk instead of concrete teaching.  
Fix: Replace the congratulatory filler with direct instructional framing.

## Verdict: REVISE
REVISE. The Ukrainian itself is sound, but there are multiple major issues: broken opening structure, dropped plan-anchor vocabulary/scenario, one missing exercise in the shipped package, and an incoherent model dialogue. Several dimensions are below 9, so this cannot PASS.

<fixes>
- find: |
    Welcome to the A1.6 Checkpoint! You have reached a major milestone in your Ukrainian language journey. In this module, we are bringing together everything you learned in the last five modules. We will combine your food vocabulary, practical shopping phrases, and the accusative case for both things and people in realistic, everyday scenarios.
  replace: |
    This checkpoint brings together the key material from A1.6. In this module, you review food vocabulary, practical shopping phrases, and the accusative case for both things and people in realistic, everyday scenarios.

- find: |
    This is your opportunity to step back and reflect on how much you can already understand and communicate. Look at the self-check questionnaire below. If you can answer "yes" to these questions, ** (I eat porridge.))?
    *   **Кафе (Cafe):** Can you order a meal at a cafe (for example, **Мені борщ, будь ласка.** (Borscht for me, please.))?
    *   **Ринок (Market):** Can you ask for prices and buy things at the market (for example, **Скільки коштує? Дайте кілограм...** (How much does it cost? Give me a kilogram...))?
    *   **Люди (People):** Can you use the accusative case to talk about people (for example, **Я бачу брата.** (I see a brother.), **Я знаю Олену.** (I know Olena.))?
  replace: |
    This is your opportunity to step back and check what you can already do. Look at the self-check questionnaire below.

    *   **Їжа й напої (Food and Drink):** Can you name 10 foods and 5 drinks?
    *   **Знахідний відмінок (Accusative):** Can you say what you eat or drink (for example, **Я їм кашу. Я п'ю воду.**)?
    *   **Кафе (Cafe):** Can you order a meal at a cafe (for example, **Мені борщ, будь ласка.**)?
    *   **Ринок (Market):** Can you ask for prices and buy things at the market (for example, **Скільки коштують помідори? Дайте кілограм яблук, будь ласка.**)?
    *   **Люди (People):** Can you use the accusative case to talk about people (for example, **Я бачу брата. Я знаю Олену.**)?

- find: |
    <!-- INJECT_ACTIVITY: group-sort-accusative -->
  replace: |
    ### Швидке сортування (Quick Sort)

    Sort these forms into two groups.

    *   **Inanimate (що?):** борщ, хліб, сік, чай, сир
    *   **Animate (кого?):** брата, лікаря, сусіда, друга, вчителя

- find: |
    > **Олег:** Що ти їш на сніданок?
    > *(What do you eat for breakfast?)*
    > **Марія:** Я їм кашу і п'ю каву з молоком.
    > *(I eat porridge and drink coffee with milk.)*
    > **Олег:** Потім іду на ринок. Скільки коштують помідори?
    > *(Then I go to the market. How much do tomatoes cost?)*
    > **Марія:** Тридцять гривень.
    > *(Thirty hryvnias.)*
    > **Олег:** Дайте кілограм, будь ласка.
    > *(Give me a kilogram, please.)*
    > **Марія:** Мені борщ і воду, будь ласка. Рахунок, будь ласка. Можна карткою?
    > *(Borscht and water for me, please. The bill, please. Can I pay by card?)*
    > **Олег:** О, я бачу Олену! Олено, привіт! Ти знаєш мого брата?
    > *(Oh, I see Olena! Olena, hi! Do you know my brother?)*
  replace: |
    > **Олег:** Що ти їси на сніданок?
    > *(What do you eat for breakfast?)*
    > **Марія:** Я їм кашу і п'ю каву з молоком. Потім іду на ринок купувати продукти на вечерю.
    > *(I eat porridge and drink coffee with milk. Then I go to the market to buy groceries for dinner.)*
    > **Продавчиня:** Що вам?
    > *(What would you like?)*
    > **Марія:** Скільки коштують помідори?
    > *(How much do the tomatoes cost?)*
    > **Продавчиня:** Тридцять гривень.
    > *(Thirty hryvnias.)*
    > **Марія:** Добре. Дайте кілограм помідорів, будь ласка. Я готую вареники і салат.
    > *(Good. Give me a kilogram of tomatoes, please. I am making varenyky and salad.)*
    > **Олег:** А вдома все готово?
    > *(Is everything ready at home?)*
    > **Марія:** Так. Я ставлю тарілки і склянки на стіл для гостей.
    > *(Yes. I am putting plates and glasses on the table for the guests.)*
    > **Марія:** Після ринку я заходжу в кафе: Мені борщ і воду, будь ласка. Рахунок, будь ласка. Можна карткою?
    > *(After the market I stop at a cafe: Borscht and water for me, please. The bill, please. Can I pay by card?)*
    > **Марія:** А потім я бачу Олену. Олено, привіт! Ти знаєш мого брата?
    > *(And then I see Olena. Olena, hi! Do you know my brother?)*

- find: |
    Congratulations on reaching the end of the A1.6 Checkpoint!  Here is a summary of what you can now do in Ukrainian:
  replace: |
    Here is a summary of what you can now do in Ukrainian:
</fixes>
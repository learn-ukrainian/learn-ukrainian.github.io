## Linguistic Scan
- Grammar-teaching error in [services-and-communication.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/services-and-communication.md:63): `Слова «допоможіть» та «підкажіть» вимагають після себе займенника.` This is false. These verbs govern a dative complement, not specifically a pronoun.

## Exercise Check
- Marker inventory is complete: `fill-in`, `group-sort`, `match-up`, `quiz` all appear, and each marker is placed after the relevant teaching section.
- Marker count matches all 4 `activity_hints` from the plan.
- The generated exercise logic is weaker than the marker placement: [services-and-communication.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/services-and-communication.yaml:76) has a `match-up` that drifts from “service requests → responses” into glossary Q&A, and one quiz item tests the wrong construction.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All four planned H2 sections are present, but Dialogue 1 never reaches the plan’s “giving the address, paying” step; lines 34-39 stop before payment. The required action `підписати` is also absent from the prose. |
| 2. Linguistic accuracy | 7/10 | Critical rule error in the grammar explanation: `Слова «допоможіть» та «підкажіть» вимагають після себе займенника.` |
| 3. Pedagogical quality | 6/10 | The address section overstates the rule: `Ми пишемо ім'я людини тільки у давальному відмінку.` It does not clearly separate address layout from dative addressee phrases. |
| 4. Vocabulary coverage | 8/10 | Required/recommended lexis is mostly covered naturally (`пошта`, `лист`, `конверт`, `марка`, `посилка`, `бандероль`, `квитанція`, `одержувач`, `відправник`, `індекс`), but `підписати` is missing. |
| 5. Exercise quality | 5/10 | Marker placement is good, but [activities/services-and-communication.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/services-and-communication.yaml:76) includes a bad response pair (`Допоможіть мені заповнити бланк.` → `Звичайно, що писати тут?`) and a wrong quiz stem (`Я пишу адресу ____`). |
| 6. Engagement & tone | 7/10 | The voice is teacherly, but filler like `Це дуже важливе правило.` adds emphasis without adding information. |
| 7. Structural integrity | 10/10 | All planned sections are present and ordered correctly; the pipeline word count is 2889, well above the 2000 target; no stray structural artifacts beyond expected inject markers. |
| 8. Cultural accuracy | 9/10 | Укрпошта is named and the module stays Ukrainian-centered; no obvious cultural inaccuracies surfaced. |
| 9. Dialogue & conversation quality | 7/10 | Named speakers help, but the first dialogue is still thin and task-incomplete relative to the postal workflow in the plan. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: [services-and-communication.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/services-and-communication.md:63) — `Слова «допоможіть» та «підкажіть» вимагають після себе займенника.`  
Issue: This teaches the wrong rule. The verbs require a dative complement, not specifically a pronoun.  
Fix: Change the explanation to `вимагають після себе форми давального відмінка` and note that it may be a pronoun or noun.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: [services-and-communication.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/services-and-communication.md:34) — Dialogue 1 ends with `Заповніть бланк...` / `...кинути її в поштову скриньку біля входу.`  
Issue: The plan explicitly requires “giving the address, paying,” but the dialogue never shows either step.  
Fix: Rewrite the dialogue so the customer gives the address and asks how much to pay.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: [services-and-communication.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/services-and-communication.md:1) — repo search confirms `підписати: 0` in the module prose.  
Issue: A planned core action vocabulary item is missing.  
Fix: Add `підписати` naturally in the postal-form dialogue.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: [services-and-communication.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/services-and-communication.md:153) — `When you write the recipient's name on an envelope or at the top of a personal letter, you must use the Dative case.` / `Ми пишемо ім'я людини тільки у давальному відмінку.`  
Issue: The explanation is too absolute and blurs postal address formatting with dative addressee phrases.  
Fix: Narrow the claim to salutation / `Кому?` addressee phrases and show those as the target pattern.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: [services-and-communication.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/services-and-communication.yaml:76) — `Допоможіть мені заповнити бланк.` → `Звичайно, що писати тут?`  
Issue: This is not a clean request-to-response match, and the whole exercise drifts away from the plan’s stated focus (`service requests → appropriate responses`).  
Fix: Replace the block with actual service-request / service-response pairs.

[EXERCISE QUALITY] [SEVERITY: critical]  
Location: [services-and-communication.yaml](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/activities/services-and-communication.yaml:149) — `Я пишу адресу ____`  
Issue: The stem itself is wrong for the intended dative answer. This tests the wrong construction.  
Fix: Replace the stem with a verb that actually licenses the dative phrase, such as `Я пишу листа ____`.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: [services-and-communication.md](/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a2/services-and-communication.md:103) — `Це дуже важливе правило.`  
Issue: This is filler emphasis, not instruction.  
Fix: Replace it with a brief functional reminder about `дякувати + Dav.`.

## Verdict: REVISE
There is a critical grammar-teaching error, a critical exercise-stem error, and multiple major plan/pedagogy issues. Several dimensions are below 9, so this cannot pass.

<fixes>
- find: |
    > — **Клієнт:** Добрий день! Дайте мені, будь ласка, два конверти і марки. Я хочу надіслати листа. *(Good day! Please give me two envelopes and stamps. I want to send a letter.)*
    > — **Працівник пошти:** Добрий день. Ось ваші конверти. Куди ви надсилаєте листи? *(Good day. Here are your envelopes. Where are you sending the letters?)*
    > — **Клієнт:** Один лист — у Київ, а другий — за кордон, у Польщу. *(One letter is to Kyiv, and the second is abroad, to Poland.)*
    > — **Працівник пошти:** Тоді вам потрібні різні марки. Заповніть бланк, будь ласка, для міжнародного листа. *(Then you need different stamps. Please fill out the form for the international letter.)*
    > — **Клієнт:** Дякую. Підкажіть мені, де можна надіслати листівку? *(Thank you. Tell me where I can send a postcard?)*
    > — **Працівник пошти:** Ви можете просто кинути її в поштову скриньку біля входу. *(You can just drop it in the postbox near the entrance.)*
  replace: |
    > — **Клієнт:** Добрий день! Дайте мені, будь ласка, два конверти і марки. Я хочу надіслати листа. *(Good day! Please give me two envelopes and stamps. I want to send a letter.)*
    > — **Працівник пошти:** Добрий день. Ось ваші конверти. Куди ви надсилаєте листи? *(Good day. Here are your envelopes. Where are you sending the letters?)*
    > — **Клієнт:** Один лист — у Київ, а другий — за кордон, у Польщу. Ось адреса для міжнародного листа. *(One letter is to Kyiv, and the second is abroad, to Poland. Here is the address for the international letter.)*
    > — **Працівник пошти:** Тоді вам потрібні різні марки. Заповніть бланк, будь ласка, для міжнародного листа. *(Then you need different stamps. Please fill out the form for the international letter.)*
    > — **Клієнт:** Дякую. Скільки я маю заплатити? *(Thank you. How much do I have to pay?)*
    > — **Працівник пошти:** Двадцять п’ять гривень. Ви можете просто кинути листівку в поштову скриньку біля входу. *(Twenty-five hryvnias. You can just drop the postcard in the postbox near the entrance.)*
- find: |
    > — **Працівник пошти:** Добре. Давайте її сюди. Вам треба заповнити спеціальну форму. *(Okay. Give it here. You need to fill out a special form.)*
  replace: |
    > — **Працівник пошти:** Добре. Давайте її сюди. Вам треба заповнити і підписати спеціальну форму. *(Okay. Give it here. You need to fill out and sign a special form.)*
- find: |
    Коли ми просимо про допомогу, ми часто використовуємо давальний відмінок. Слова «допоможіть» та «підкажіть» вимагають після себе займенника. Цей займенник відповідає на питання «кому?». Клієнт каже: «Допоможіть мені, будь ласка». Тут слово «мені» — це давальний відмінок від займенника «я».
  replace: |
    Коли ми просимо про допомогу, ми часто використовуємо давальний відмінок. Слова «допоможіть» та «підкажіть» вимагають після себе форми давального відмінка. Це може бути займенник або іменник. Клієнт каже: «Допоможіть мені, будь ласка». Тут слово «мені» — це давальний відмінок від займенника «я».
- find: |
    When you write the recipient's name on an envelope or at the top of a personal letter, you must use the Dative case. The Dative case answers the important question **кому?** (to whom?). This grammatical rule applies to formal letters, casual postcards, and all types of packages. If you want someone to successfully receive your mail, you change their name and any adjectives describing them into the appropriate Dative case forms. This shows respect and clearly indicates the intended receiver of your message or gift.

    На конверті завжди є детальна інформація про одержувача. Ми пишемо ім'я людини тільки у давальному відмінку. Наприклад, ви пишете довгий лист дорогому другові Андрію. Або ви хочете відправити теплий подарунок любій бабусі Олені. В офіційних листах ми часто пишемо шановному професорові Петренку. Коли людина має отримати ваш лист, її ім'я стоїть у формі давального відмінка.
  replace: |
    When you write a salutation or the **Кому?** line on a form, you use the Dative case. The Dative case answers the important question **кому?** (to whom?). In this module, the key pattern is the addressee phrase: **дорогому другові Андрію**, **любій бабусі Олені**, **шановному професорові Петренку**. This marks the recipient of the letter or parcel clearly and politely.

    У цьому модулі ми тренуємо давальний відмінок у фразах на позначення адресата: **кому?** Ви можете написати: «дорогому другові Андрію», «любій бабусі Олені», «шановному професорові Петренку». У таких словосполученнях ім'я людини та слова перед ним стоять у давальному відмінку. Так ми чітко показуємо, кому призначений лист або подарунок.
- find: |
    - id: match-up-requests-responses
      type: match-up
      instruction: З'єднайте запит із відповіддю
      pairs:
      - left: Я хочу надіслати листа.
        right: Ось конверт і марка.
      - left: Де можна надіслати листівку?
        right: Киньте її в поштову скриньку.
      - left: Скільки коштує відправити бандероль?
        right: Триста гривень.
      - left: Допоможіть мені заповнити бланк.
        right: Звичайно, що писати тут?
      - left: Куди ви надсилаєте листи?
        right: Один у Київ, а другий за кордон.
      - left: Що таке індекс?
        right: Це цифри для вашої адреси.
      - left: Хто такий одержувач?
        right: Це людина, яка чекає на посилку.
      - left: Я хочу забрати посилку.
        right: Дайте мені вашу квитанцію.
  replace: |
    - id: match-up-requests-responses
      type: match-up
      instruction: З'єднайте запит із відповіддю
      pairs:
      - left: Дайте мені, будь ласка, два конверти і марки.
        right: Ось ваші конверти і марки.
      - left: Де можна надіслати листівку?
        right: Киньте її в поштову скриньку.
      - left: Скільки коштує відправити бандероль?
        right: Триста гривень.
      - left: Допоможіть мені заповнити бланк.
        right: Звичайно, що вам потрібно?
      - left: Підкажіть мені, де купити марку.
        right: Марки можна купити у цьому віконці.
      - left: Я хочу забрати посилку.
        right: Дайте мені вашу квитанцію.
      - left: Покажіть мені бланк, будь ласка.
        right: Ось бланк для міжнародного відправлення.
      - left: Скажіть, будь ласка, хто такий одержувач.
        right: Це людина, яка отримує посилку.
- find: |
      - question: Я пишу адресу ____
  replace: |
      - question: Я пишу листа ____
- find: |
    Після того, як ви отримали допомогу, ви повинні подякувати людині. Якщо листоноша приніс вам лист, ви кажете: «Дякую листоноші за допомогу». Це дуже важливе правило.
  replace: |
    Після того, як ви отримали допомогу, ви повинні подякувати людині. Якщо листоноша приніс вам лист, ви кажете: «Дякую листоноші за допомогу». Зверніть увагу: після «дякую» ми ставимо форму давального відмінка.
</fixes>
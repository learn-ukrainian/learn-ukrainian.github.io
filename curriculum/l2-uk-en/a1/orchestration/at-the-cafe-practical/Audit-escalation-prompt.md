        # Escalation Fix — Audit

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        ============================================================
  OTAMAN VERIFY: at-the-cafe-practical
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  at-the-cafe-practical
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 2520/2000 (raw: 3027) | pedagogy: 1 violations | immersion: 33.3% LOW (target 35-55% (M35))

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📚 PEDAGOGICAL VIOLATIONS FOUND:
    [EUPHONY] Line 290: «з собою?**» — з перед з/с/ш/ч; має бути «із собою?**»
       → FIX: Replace «з» with «із» (before sibilant)


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 1 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/at-the-cafe-practical-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/at-the-cafe-practical.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/at-the-cafe-practical-audit.log for details)
        ```

        ## Current Content of Affected Section(s)


---
## Практика: Діалоги в кав'ярні

Let's see these phrases in action. Read these dialogues aloud to practice the flow.

### Діалог 1: Класичне замовлення

In this scenario, you are in a cozy Lviv café ordering a classic set. Note the use of **філіжанка**.

**Офіціант:** Добрий день! Що будете замовляти? (Good day! What will you order?)
**Клієнт:** Добрий день! **Я буду філіжанку** кави і круасан, будь ласка. (Good day! I will [have] a cup of coffee and a croissant, please.)
**Офіціант:** Кава з молоком чи без? (Coffee with milk or without?)
**Клієнт:** З молоком, але **без цукру**, будь ласка. (With milk, but without sugar, please.)
**Офіціант:** Який круасан: **із шоколадом** чи з джемом? (Which croissant: with chocolate or with jam?)
**Клієнт:** **Із шоколадом**, будь ласка. Я люблю шоколад. (With chocolate, please. I love chocolate.)
**Офіціант:** Зрозумів. Це все? (Understood. Is that all?)
**Клієнт:** Так, дякую. А, і склянку води, будь ласка. (Yes, thank you. Ah, and a glass of water, please.)
**Офіціант:** Звичайно. (Of course.)

> [!observe]
> Look at the endings: «Я буду... філіжанк**у**». The base word is *філіжанка*, but because you are ordering it (it is the object), it becomes *філіжанку*. Also notice «склянк**у** води» (a glass of water).

### Діалог 2: Комфорт і робота

Often, you need more than just coffee—you need a place to work or browse.

**Клієнт:** Привіт! Скажіть, будь ласка, у вас є Wi-Fi? (Hi! Tell [me], please, do you have Wi-Fi?)
**Бариста:** Так, звичайно. (Yes, of course.)
**Клієнт:** А який пароль? (And what is the password?)
**Бариста:** Пароль на чеку. Ось ваш чек. (The password is on the receipt. Here is your receipt.)
**Клієнт:** Дякую. І ще одне питання: де тут можна зарядити телефон? (Thank you. And one more question: where can [one] charge a phone here?)
**Бариста:** Біля вікна є розетка. Там вільно. (There is a socket near the window. It is free there.)
**Клієнт:** Супер, дякую! Я буду працювати тут годину. (Super, thanks! I will work here for an hour.)
**Бариста:** Без проблем. Гарної роботи! (No problem. Have a nice work!)

### Діалог 3: Тут чи з собою?

Sometimes you are in a rush. You need coffee "to go".

**Бариста:** Добрий день! Що для вас? (Good day! What for you?)
**Клієнт:** Добрий день. Можна лате, будь ласка? (Good day. Can I have a latte, please?)
**Бариста:** **Кава тут чи з собою?** (Coffee here or to go?)
**Клієнт:** **З собою**, будь ласка. (To go, please.)
**Бариста:** Середнє чи велике? (Medium or large?)
**Клієнт:** Велике. (Large.)
**Бариста:** Ваше ім'я? (Your name?)
**Клієнт:** Андрій. (Andriy.)
**Бариста:** Дякую, Андрій. Чекайте дві хвилини. (Thank you, Andriy. Wait two minutes.)

### Діалог 4: Оплата рахунку

Finishing the visit clearly and politely.

**Клієнт:** Офіціанте! Можна рахунок, будь ласка? (Waiter! Can [I have] the bill, please?)
**Офіціант:** Так, звичайно. Ви платите **готівкою** чи **карткою**? (Yes, of course. Are you paying by cash or by card?)
**Клієнт:** **Карткою**, будь ласка. У мене Apple Pay. (By card, please. I have Apple Pay.)
**Офіціант:** *[готує термінал]* Прошу, прикладайте телефон. (Here you go, please tap the phone.)
**Клієнт:** *[платить]* Дякую, кава була дуже смачна! А сирник — просто фантастика. (Thank you, the coffee was very tasty! And the cheesecake was just fantastic.)
**Офіціант:** Ми раді! Приходьте ще! (We are glad! Come again!)
**Клієнт:** До побачення! Гарного дня! (Goodbye! Have a nice day!)
**Офіціант:** До побачення! (Goodbye!)


        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/at-the-cafe-practical.md`

        ## Instructions

        1. Fix ONLY the violations listed above
        2. For euphony (в/у, і/й): apply Ukrainian euphony rules strictly
        3. Do NOT add or remove content — only fix the specific violations
        4. Preserve all markdown formatting, headers, and structure

        ## Output Format (MANDATORY)

        Output ONLY the fixed section(s) between delimiters:

        ```
        ===SECTION_FIX_START===
        ## {section title}
        {fixed section content}
        ===SECTION_FIX_END===
        ```

        If multiple sections need fixing, output each in its own delimiter block.
        Do NOT output anything else — no explanations, no commentary.

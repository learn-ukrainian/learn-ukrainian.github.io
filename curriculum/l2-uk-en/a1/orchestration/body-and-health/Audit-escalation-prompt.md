        # Escalation Fix — Audit

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        ============================================================
  OTAMAN VERIFY: body-and-health
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  body-and-health
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 2304/2000 (raw: 2472) | pedagogy: 1 violations

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📚 PEDAGOGICAL VIOLATIONS FOUND:
    [EUPHONY] Line 319: «голова і є» — і між голосними; має бути «й є»
       → FIX: Replace «і» with «й» (between vowels)


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 1 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/body-and-health-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/body-and-health.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/body-and-health-audit.log for details)
        ```

        ## Current Content of Affected Section(s)


---
## Практикум: Діалоги про здоров'я

**Читайте діалоги.** (Read the dialogues.) **Це практика.** (This is practice.)

### Сценарій 1: Друзі (Casual)
**Олег:** Привіт, Ірино! Як ти? (Hi, Iryna! How are you?)
**Ірина:** Привіт. Я почуваю себе погано. (Hi. I feel bad.)
**Олег:** Що сталося? (What happened?)
**Ірина:** У мене болить голова і є температура. (I have a headache and a fever.)
**Олег:** Треба відпочивати. Пий чай і їж малину. (You need to rest. Drink tea and eat raspberry.)
**Ірина:** Дякую, так і зроблю. (Thank you, I will do so.)

### Сценарій 2: У лікаря (Formal)
**Лікар:** Доброго дня. Що вас турбує? (Good day. What bothers you?)
**Пацієнт:** Доброго дня, лікарю. У мене сильний кашель і болить горло. (Good day, doctor. I have a strong cough and a sore throat.)
**Лікар:** У вас є температура? (Do you have a fever?)
**Пацієнт:** Так, трохи висока. (Yes, a little high.)
**Лікар:** Відкрийте рот, будь ласка. (Open your mouth, please.)
**Пацієнт:** А-а-а.
**Лікар:** Так, горло червоне. Це грип. (Yes, the throat is red. It is the flu.)
**Пацієнт:** Що робити? (What should I do?)
**Лікар:** Ось рецепт. Купіть ці ліки в аптеці. Пийте багато води і відпочивайте. (Here is a prescription. Buy this medicine at the pharmacy. Drink a lot of water and rest.)
**Пацієнт:** Дякую, до побачення. (Thank you, goodbye.)

### Сценарій 3: В аптеці (Pharmacy)
**Аптекар:** Слухаю вас. (I am listening to you / Can I help you?)
**Клієнт:** Добрий день. Дайте, будь ласка, щось від кашлю. (Good day. Give [me], please, something for a cough.)
**Аптекар:** У вас сухий кашель? (Do you have a dry cough?)
**Клієнт:** Так. (Yes.)
**Аптекар:** Візьміть цей сироп. Він дуже добрий. (Take this syrup. It is very good.)
**Клієнт:** Скільки коштує? (How much does it cost?)
**Аптекар:** Двісті гривень. (200 hryvnias.)
**Клієнт:** Добре, ось гроші. Дякую. (Okay, here is the money. Thank you.)

### Сценарій 4: Вдома (At Home)
**Мама:** Ти хворий? (Are you sick?)
**Син:** Так, у мене температура. (Yes, I have a fever.)
**Мама:** Тобі треба лежати. (You need to lie down.)
**Син:** Я замерз. (I am cold.)
**Мама:** Ось ковдра і чай. Відпочивай. (Here is a blanket and tea. Rest.)
**Син:** Добре. (Okay.)

---

# Підсумок

Today we mastered essential health vocabulary. You know body parts, how to say "У мене болить...", and how to speak with a doctor. Remember: **Я почуваю себе погано** (I feel bad) describes your state, and **У мене болить голова** describes specific pain.

Take care of your health! As Ukrainians say: **Бережіть себе!** (Take care of yourself!).

**Перевірте себе:**

1.  How do you say "My leg hurts" in Ukrainian?
2.  What is the plural of **око**?
3.  How do you say "I feel bad" using the reflexive verb?
4.  What preposition do you use to ask for medicine "for" something?
5.  What is the traditional Ukrainian tea ingredient for a cold?
6.  How do you say "I need to go to the doctor" (using "треба")?


        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/body-and-health.md`

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

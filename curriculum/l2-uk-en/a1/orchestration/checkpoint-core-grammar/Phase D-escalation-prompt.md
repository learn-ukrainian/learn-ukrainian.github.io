        # Escalation Fix — Phase D

        You are an expert Ukrainian language editor. The previous agent could not fix
        these audit violations. Fix them precisely.

        ## Audit Errors

        ```
        ============================================================
  HETMAN VERIFY: checkpoint-core-grammar
============================================================

[1/4] Running full audit...
[2/4] Checking sidecar files...
[3/4] Reading status JSON...
[4/4] Checking overall status...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  checkpoint-core-grammar
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  overall status is 'fail' (must be 'pass')
  failing gates:
    lesson: 2432/1500 (raw: 2684) | pedagogy: 1 violations

  Hetman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
  📚 PEDAGOGICAL VIOLATIONS FOUND:
    [YAML_SCHEMA_VIOLATION] Schema error in checkpoint-core-grammar.yaml: Schema validation error at key '0': {'text': 'гарна кава', 'correct': True} is not of type 'string'
       → FIX: Fix the activity YAML to match the schema in schemas/activities-base.schema.json


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 5/100)
     → 1 violations (minor)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/checkpoint-core-grammar-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/checkpoint-core-grammar.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/checkpoint-core-grammar-audit.log for details)
        ```

        ## Current Content of Affected Section(s)

        **Try right now:**
Look around and name three objects using "мій/моя/моє". For example: "Це мій стіл. Це моя ручка. Це моє вікно". This is a simple but very effective exercise.

### Self-Check

What ending will the adjective "гарний" have with the word "місто"?
Since "місто" ends in -о (Neuter), the adjective must be **гарне**.

## Навичка 3: Система дієслів

The verb is the engine of the sentence. Without it, nothing happens. In Ukrainian, the tense system is simpler than in English (no Continuous or Perfect), but word forms change more. We will look at three tenses: present, past, and future.

### Model: Verb Tenses

**Present Tense**
In the present tense, verbs change their ending depending on WHO performs the action (я, ти, він, ми...). We divide them into two large groups (conjugations):
1.  **Group -ати (читати, знати):**
    *   Я зна**ю**, Ти зна**єш**, Він зна**є**
    *   Ми зна**ємо**, Ви зна**єте**, Вони зна**ють**
2.  **Group -ити (робити, говорити):**
    *   Я робл**ю**, Ти роб**иш**, Він роб**ить**
    *   Ми роб**имо**, Ви роб**ите**, Вони роб**лять**

Remember "Ви" (formal you). In Ukrainian culture, this is a marker of respect. You always address strangers, older people, and service staff as "Ви" (**-єте**, **-ите**).

**Past Tense**
The past tense is students' favorite time because it is the simplest. Here the verb changes not by person (я/ти/він), but by **gender**. It's like an adjective!
*   He (Man): чита**в** (added **-в**)
*   She (Woman): чита**ла** (added **-ла**)
*   It (Sun): чита**ло** (added **-ло**)
*   They (People): чита**ли** (added **-ли**)

**Future Tense**
For the future tense, we have a simple formula that works for most verbs denoting a process (imperfective aspect):
**БУДУ + Infinitive**
It is very similar to the English "will be doing".
*   Я **буду читати**.
*   Ти **будеш робити**.
*   Ми **будемо йти**.

### Practice: Conjugation Drills

**Trap: The Extra "є" (The "To Be" Trap)**
This is a classic mistake of English-speaking students. In English, you always say "I am a student". In the Ukrainian present tense, the verb "to be" (є) is often omitted. But in the past tense, it is MANDATORY!

| Time | English | Ukrainian (Mistake) | Ukrainian (Correct) |
|------|---------|---------------------|---------------------|
| Present | I am a student | *Я є студент* | **Я студент** (without "є") |
| Past | I was a student | *Я студент* | **Я був студентом** (need "був") |

**Conjugate "читати" in your head.**
Я читаю, Ти читаєш... Now try "робити": Я роблю, Ти робиш...

### Self-Check

**Translate: "I was at home".**
If you are a man: "Я був вдома".
If you are a woman: "Я була вдома".
Did you remember to change the verb ending?

## Навичка 4: Система відмінків

Cases (Відмінки) are what makes the Ukrainian language flexible. A case shows the role of a word in a sentence. We do not rely on word order like in English, we change the ending. At this stage, you should confidently operate with four main cases.

### Model: The Four Cases

**Nominative Case (Називний)**
This is the basic form of the word you see in the dictionary. It answers the questions **Хто? Що?** (Who? What?).
It is the subject of the sentence — the one performing the action.
*   **Студент** читає.
*   **Книга** лежить.

**Accusative Case (Знахідний) — Direction**
We use this case when talking about movement SOMEWHERE (Where to?).
Question: **Куди?**
*   Я йду **в банк**. (Банк — unchanged, because inanimate, masc. gender)
*   Я йду **в школу**. (Школа → Школ**у**, because fem. gender)

> [!tip]
> **Life Hack for Accusative:**
> If it is masculine and not a person (стіл, парк, магазин) — the word DOES NOT change!
> Я бачу стіл. Я йду в парк.
> Only feminine gender changes: -а turns into -у.
> Я бачу мам**у**. Я йду в бібліотек**у**.

**Locative Case (Місцевий) — Place**
This case tells us WHERE something is located (Where at?).
Question: **Де?**
There is always a preposition **в/у** or **на**.
*   Я **в банку**. (Банк → Банк**у**)
*   Я **в школі**. (Школа → Школ**і**)

**Genitive Case (Родовий) — Absence**
At level A1, we learn this case in the context of "no" (absence/negation).
Questions: **Кого? Чого?**
When something is missing, the ending changes:
*   У мене немає **часу** (час → час**у**).
*   У мене немає **машини** (машина → машин**и**).
*   Я не хочу **кави** (кава → кав**и**).

This is the case of negation. If you say "ні" or "немає", get ready to change the ending.

### Practice: Direction vs Location

**Critical Difference: Куди vs Де**
This is the most frequent mistake. Confusing "Where I am going" (Direction) and "Where I am" (Location).
*   *Я йду в парку* (Mistake! You are walking inside the park).
*   **Я йду в парк** (Correct. You are moving towards the park).
*   **Я гуляю в парку** (Correct. You are already there).

### Self-Check

**Translate: "I do not have water".**
"У мене немає води". (Вода -> Води in Genitive).
Did you change the ending?

## Навичка 5: Практичні ситуації

Now that we have sorted out the theory, let's see how it works in life. Here are three scenarios waiting for you in the next modules. Try to analyze the grammar in each phrase.

### Model: Real-Life Contexts

**Scenario 1: Ordering at a Cafe**
You want to eat. You use the verb "хотіти" + Accusative case (for food) or Genitive (if you want a little of something).
*   **Клієнт:** Добрий день! Я буду **каву** і **салат**.
    *   *Analysis:* Кава (she) → Кав**у** (Accusative). Салат (he, inanimate) → Салат (Accusative, no change).
*   **Офіціант:** Ви хочете десерт?
*   **Клієнт:** Ні, я не хочу **десерту**, дякую.
    *   *Analysis:* Не хочу (negation) → Десерт**у** (Genitive).

**Scenario 2: Navigation in the City**
You are lost and asking for directions. Motion verbs and cases of place/direction work here.
*   **Турист:** Вибачте, ви знаєте, де **метро**?
    *   *Analysis:* Метро (it, invariable word).
*   **Перехожий:** Так, ідіть прямо, там буде парк. Метро **в парку**.
    *   *Analysis:* В парку (Locative — де?).
*   **Турист:** Дякую! Я йду **в центр**.
    *   *Analysis:* В центр (Accusative — куди?).

**Scenario 3: Describing Impressions**
You are telling friends about your trip. The main thing here is adjective agreement and past tense.
*   **Я:** Львів — це дуже **гарне місто**.
    *   *Analysis:* Місто (it) → Гарн**е** (Neut).
*   **Я:** Я **був** там учора. Ми **робили** багато фото.
    *   *Analysis:* Був indicates Masculine past. Робили indicates Plural past.
*   **Я:** Це **була** чудова поїздка!
    *   *Analysis:* Поїздка (she) → Бул**а** indicates Feminine past.

### Practice: Myth Buster

> [!myth-buster]
> **Myth: "I will understand everything from context"**
> Many students think that endings are not important if you know the root of the word. This is a dangerous myth. In Ukrainian, "Мама любить доньку" and "Маму любить донька" are two completely different sentences, although the word order can be the same. Who loves whom? Only the endings (Nominative vs Accusative) give the answer. Grammar is not decor, it is the code of meaning.

### Self-Check

**Why do we say "Він знає", but "Вони знають"?**
Because the verb changes ending depending on the person. "Він" (he) takes -є, "Вони" (they) takes -ють.

## Інтеграційне завдання

Are you ready for the final test? This task combines everything we reviewed today. Imagine a situation: you met a friend on the street.

**Task:** Read the dialogue and find in it:
1.  A verb in the past tense.
2.  A noun in the Locative case (Where?).
3.  A noun in the Accusative case (Where to?).
4.  An adjective agreed with a feminine noun.

**Dialogue:**
— Привіт, Олено! Де ти **була**?
— Привіт! Я була **в магазині**.
— Що ти там робила?
— Я купувала **нову сукню**. Завтра я йду **в театр**.
— О, це чудова ідея! А я зараз йду **додому**. Я не маю **часу**.

*   *Hint:*
    *   *Була* — past tense.
    *   *В магазині* — Locative case.
    *   *В театр* — Accusative case.
    *   *Нову сукню* — Accusative case + agreement (сукня — she).
    *   *Часу* — Genitive case (do not have).

If you could take this dialogue apart — you are ready. You possess the tools to build your world in Ukrainian.

---

## Підсумок

Today we did a great job. We stopped, looked back, and made sure that our backpack of knowledge is packed correctly. You reviewed how to read without mistakes, how to agree words, how to manage time (past, present, future), and how to indicate direction and location.

This is the base of level A1. Next, it will only get more interesting — more words, more live situations, more culture. But the grammatical frame will remain the same. If you feel unsure about any of these topics, return to the relevant module (1-33) and go through it again. Do not be afraid to repeat. Repetition is the mother of learning.

You are ready to move on! Next stop — the coffee shop. Prepare your taste buds and vocabulary!

## Vocabulary

This module uses standard vocabulary from A1. Review the terms below if needed.
(See vocabulary sidecar for details)


        ## File Path

        `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-core-grammar.md`

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

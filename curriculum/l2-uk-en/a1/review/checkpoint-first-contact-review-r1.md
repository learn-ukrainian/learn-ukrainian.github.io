## Linguistic Scan
- Factually wrong phonetics claim in `Що ми знаємо?`: `the soft **Г** (H) versus the hard **Ґ** (G)`. Ukrainian **Г** is not a “soft” consonant; it is the voiced fricative [ɦ].

## Exercise Check
- Marker inventory is correct: `quiz-comprehensive-review`, `match-up-questions-answers`, `fill-in-self-introduction`.
- Marker IDs match the plan’s three `activity_hints`.
- Marker placement is acceptable: quiz after self-check, match-up after grammar, fill-in after the capstone dialogue.
- No inline DSL exercise blocks appear in the prose, so there is no inline exercise logic to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 5/10 | The plan requires review of letters/sounds and stress, but the module never asks `How many letters/sounds` and never mentions `наголос`; the capstone also omits the plan’s goodbye and compresses the required graduation speech to `Мене звати Богдан. Я з Дніпра. Я інженер. Це моя сім'я.` |
| 2. Linguistic accuracy | 7/10 | `such as the soft **Г** (H) versus the hard **Ґ** (G)` teaches a wrong phonetic description. |
| 3. Pedagogical quality | 5/10 | The checkpoint introduces later-scope material instead of consolidating A1.1: `Я живу в Києві.` adds deferred locative/conjugation material, and the dialogue explicitly teaches `Кличний відмінок` although the plan says `No new grammar — consolidation only`. |
| 4. Vocabulary coverage | 8/10 | Recommended checkpoint vocabulary is present and natural: `ім'я`, `прізвище`; however the reading section’s `Я живу в Києві.` pulls in later-scope material. |
| 5. Exercise quality | 9/10 | All three planned activity types are represented by correctly named markers placed after relevant teaching sections. |
| 6. Engagement & tone | 9/10 | The prose keeps a teacherly tone and uses concrete situations such as the conference coffee break with named speakers. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly, and the pipeline word count is above target at 1230. |
| 8. Cultural accuracy | 10/10 | The module uses Ukrainian names and places (`Богдан`, `Соломія`, `Дніпро`, `Тернопіль`) without Russian-centered framing. |
| 9. Dialogue & conversation quality | 6/10 | The capstone exchange ends abruptly at `У вас гарна сім'я.` with no goodbye, despite the plan requiring a full-cycle first meeting. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Що ми знаємо?` — `such as the soft **Г** (H) versus the hard **Ґ** (G)`  
Issue: `Г` is described incorrectly as “soft.” In Ukrainian phonetics, `Г` is not a soft consonant; it is a voiced fricative [ɦ].  
Fix: Replace `soft **Г**` with an accurate beginner-safe description such as `breathy **Г** (close to H)`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Читання` — `* **Я живу в Києві.** (I live in Kyiv.)`  
Issue: This imports later material the source plan explicitly deferred; the checkpoint stops being pure A1.1 review.  
Fix: Replace the sentence with an already-reviewed A1.1 pattern such as `* **Я з Києва.** (I am from Kyiv.)`.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Діалог` — `Crucially, they use the **Кличний відмінок** (Vocative case) for direct address.` and the following tip block  
Issue: The checkpoint teaches new grammar even though the plan says `No new grammar — consolidation only`. Vocative belongs to a later module, not this A1.1 checkpoint.  
Fix: Remove the vocative explanation and keep the dialogue analysis focused on formal `ви/вас`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Діалог` — the conversation ends with `> **Соломія:** Дуже гарно! У вас гарна сім'я.`  
Issue: The plan requires a full cycle `greeting → name → origin → profession → family → showing photos → goodbye`, but the goodbye is missing.  
Fix: Add a short closing exchange, e.g. `Дякую! До побачення!` / `До побачення!`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Діалог` — `You might say: **Мене звати Богдан. Я з Дніпра. Я інженер. Це моя сім'я.**`  
Issue: The plan’s graduation-speech model requires a fuller connected monologue with nationality, parents, and `У мене є...`; the current version is too thin.  
Fix: Replace it with a fuller A1.1 monologue that includes nationality, parents’ professions, and one family sentence.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Підсумок — Summary` — checklist begins `* Can you read Ukrainian Cyrillic words fluently...`  
Issue: The final self-check omits two plan-mandated review points: `How many letters/sounds in Ukrainian?` and stress review from M04.  
Fix: Add checklist items for `33 letters / 38 sounds`, stress placement, and the explicit `introduce yourself in 5 sentences` check.

## Verdict: REVISE
One critical phonetics error and multiple major plan/scope violations block PASS. The module is structurally clean, but it cannot ship while it teaches wrong phonetics, introduces later grammar, and omits required checkpoint content.

<fixes>
- find: |
    such as the soft **Г** (H) versus the hard **Ґ** (G), and the deep **И** (Y) versus the sharp **І** (I).
  replace: |
    such as the breathy **Г** (close to H) versus the hard **Ґ** (G), and the deep **И** (Y) versus the sharp **І** (I).
- find: |
    * **Я живу в Києві.** (I live in Kyiv.)
  replace: |
    * **Я з Києва.** (I am from Kyiv.)
- find: |
    > **Соломія:** Дуже приємно. Моє **ім'я** (first name) — Соломія. Моє **прізвище** (surname) — Коваль. Звідки ви, Богдане? *(Very nice to meet you. My first name is Solomiya. My surname is Koval. Where are you from, Bohdan?)*
    > **Богдан:** Я з Дніпра. Я інженер. Звідки ви, Соломіє? *(I am from Dnipro. I am an engineer. Where are you from, Solomiya?)*
  replace: |
    > **Соломія:** Дуже приємно. Моє **ім'я** (first name) — Соломія. Моє **прізвище** (surname) — Коваль. Звідки ви? *(Very nice to meet you. My first name is Solomiya. My surname is Koval. Where are you from?)*
    > **Богдан:** Я з Дніпра. Я інженер. А ви звідки? *(I am from Dnipro. I am an engineer. And where are you from?)*
- find: |
    Analyze the natural features of this dialogue. Because they are meeting in a professional setting, they use the polite, formal address with the pronouns **ви** (you) and **вас** (you, accusative). Crucially, they use the **Кличний відмінок** (Vocative case) for direct address. Notice how Solomiya says **Богдане** (Bohdan) — the masculine consonant adds an **-е** ending. Bohdan replies with **Соломіє** (Solomiya). This shows authentic Ukrainian politeness. 

    :::tip
    The Vocative case (**Кличний відмінок**) is mandatory in Ukrainian when addressing someone directly. It instantly elevates your spoken language from beginner translation to authentic phrasing, showing that you understand the cultural importance of proper address.
    :::
  replace: |
    Analyze the natural features of this dialogue. Because they are meeting in a professional setting, they use the polite, formal address with the pronouns **ви** (you) and **вас** (you, accusative). This keeps the exchange respectful and matches the conference setting.

    :::tip
    For a first professional meeting, stay with **ви** and **вас**. These are the key A1.1 forms you need for a polite introduction.
    :::
- find: |
    > **Соломія:** Дуже гарно! У вас гарна сім'я. *(Very nice! You have a nice family.)*
  replace: |
    > **Соломія:** Дуже гарно! У вас гарна сім'я. *(Very nice! You have a nice family.)*
    > **Богдан:** Дякую! До побачення! *(Thank you! Goodbye!)*
    > **Соломія:** До побачення! *(Goodbye!)*
- find: |
    You might say: **Мене звати Богдан. Я з Дніпра. Я інженер. Це моя сім'я.** (My name is Bohdan. I am from Dnipro. I am an engineer. This is my family.)
  replace: |
    You might say: **Привіт! Мене звати Богдан. Я з Дніпра. Я українець. Я — інженер. Моя мама — вчителька. Мій тато — інженер. У мене є брат.** (Hi! My name is Bohdan. I am from Dnipro. I am Ukrainian. I am an engineer. My mother is a teacher. My father is an engineer. I have a brother.)
- find: |
    * Can you read Ukrainian Cyrillic words fluently, including those utilizing the **Ь** and the apostrophe?
    * Can you say hello informally with **Привіт** (Hi) and formally with **Добрий день** (Good afternoon)?
  replace: |
    * Can you say how many letters and how many sounds Ukrainian has?
    * Can you place the stress correctly in common words such as **кава** and **вода**?
    * Can you read Ukrainian Cyrillic words fluently, including those utilizing the **Ь** and the apostrophe?
    * Can you say hello informally with **Привіт** (Hi) and formally with **Добрий день** (Good afternoon)?
    * Can you introduce yourself in 5 sentences?
</fixes>
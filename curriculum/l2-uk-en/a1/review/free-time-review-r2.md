## Linguistic Scan
No Russianisms, Surzhyk, paronym errors, or forbidden Russian letters found. The critical language-teaching issue is the `у/в` explanation: the module presents euphony as a hard consonant/vowel rule, then the linked preposition exercise treats `у` and `в` as single-correct answers in contexts where both forms are acceptable.

## Exercise Check
Three markers are present, and the count matches the plan’s 3 `activity_hints`.

`match-hobbies-verbs` appears after **Хобі і спорт**.  
`fill-in-prepositions-activities` appears after **Хобі і спорт**.  
`fill-in-invitations-frequency` appears after **Як часто?**

Placement is correct and not clustered at the end. The problems are in the linked activity logic: the preposition fill-in uses unsafe single-answer keys for `у/в`, and the invitations/frequency fill-in has a valid distractor plus a first-option answer pattern throughout.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | All four planned H2 sections are present and ordered correctly; the module covers hobbies/sports, invitations, frequency, and A1.4 integration with weather in `Сьогодні тепло...` / `Сьогодні холодно...`. |
| 2. Linguistic accuracy | 6/10 | The prose says: `If the previous word ends in a consonant and the next word starts with a consonant, we use «у»... If there are vowels around, we prefer «в».` That overstates `у/в` milozvuchnist as a hard rule, and the linked exercise then marks alternants as single-correct. |
| 3. Pedagogical quality | 7/10 | The overall PPP flow is there, but the module leaves chunk-based A1 teaching and turns `у/в` into a rigid phonetics rule instead of keeping `грати у / в...`, `ходити у / в...` as safe chunks. |
| 4. Vocabulary coverage | 10/10 | All required plan vocabulary appears naturally in prose/dialogue: `вихідні`, `спорт`, `футбол`, `кіно`, `часто`, `іноді`, `рідко`, `ходімо`. Recommended vocabulary is also present: `завжди`, `зазвичай`, `ніколи`, `театр`, `концерт`, `музей`, `давай`, `раз`. |
| 5. Exercise quality | 4/10 | Marker placement is good, but `Ми граємо ____ футбол.` offers `у/на/в`, `Вони ходять ____ театр...` offers `у/на/в`, and `____ в кіно у суботу!` uses valid `Ідемо` as a distractor. Both visible fill-in activities also put every correct answer in the first option slot. |
| 6. Engagement & tone | 9/10 | The tone is teacherly and useful, with a concrete cultural note on `Будинок культури` rather than generic hype. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present; the module is clean markdown; pipeline word count is 1403, safely above the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module frames Ukrainian culture on its own terms and avoids Russian-centered comparisons. |
| 9. Dialogue & conversation quality | 9/10 | Named speakers, a real free-time scenario, and usable lines like `Ходімо в кіно...` and `Двічі на тиждень...` make the dialogues serviceable for A1 conversation practice. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: **Хобі і спорт** tip — `If the previous word ends in a consonant and the next word starts with a consonant, we use «у»... If there are vowels around, we prefer «в».`  
Issue: This teaches `у/в` as a hard rule. For A1 this should stay a chunk-based milozvuchnist note, not an absolute consonant/vowel algorithm.  
Fix: Replace the tip with wording that says Ukrainian alternates `у/в` for euphony and that both forms can be correct in context.

[EXERCISE QUALITY] [SEVERITY: critical]  
Location: `fill-in-prepositions-activities` — `Ми граємо ____ футбол.` / `Вони ходять ____ театр раз на місяць.`  
Issue: The answer key treats `у` as uniquely correct while also offering `в`, even though these are acceptable alternants in such contexts. That makes the exercise logically unsafe.  
Fix: Change these items so the correct answer is `у/в`, and remove the false single-correct setup.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `fill-in-invitations-frequency` — `____ в кіно у суботу! — Добре!` with options `Ходімо / Давай / Ідемо`  
Issue: `Ідемо` is a valid invitation here, so the item does not have one clean correct answer. The whole visible fill-in block also puts every correct answer in the first option slot, making the pattern guessable.  
Fix: Replace the valid distractor with a clearly wrong option and reorder the options across the block so correct answers are not always first.

## Verdict: REVISE
REVISE. The module is structurally solid and mostly clean Ukrainian, but it has ship-blocking exercise logic problems and one misleading grammar-teaching claim. Dimensions 2, 3, and 5 are below 9, and the `у/в` issues are fixable with targeted replacements rather than a rebuild.

<fixes>
- find: |
    :::tip
    How do you know whether to use «у» or «в»? Ukrainian loves harmony and flow! If the previous word ends in a consonant and the next word starts with a consonant, we use «у» to break them up to make pronunciation easier. If there are vowels around, we prefer «в». This rule is called euphony, or "beautiful sounding."
    :::
  replace: |
    :::tip
    With sports and places, Ukrainian alternates between «у» and «в» for euphony. At A1, learn the chunk first: «грати у / в футбол», «ходити у / в театр». The exact choice depends on the surrounding sounds, so both forms can be correct in context.
    :::

- find: |
    - id: fill-in-prepositions-activities
      type: fill-in
      instruction: Оберіть правильний прийменник (Choose the correct preposition)
      items:
      - sentence: Він грає ____ піаніно.
        answer: на
        options:
        - на
        - у
        - в
      - sentence: Ми граємо ____ футбол.
        answer: у
        options:
        - у
        - на
        - в
      - sentence: Я хочу ходити ____ концерт.
        answer: на
        options:
        - на
        - в
        - у
      - sentence: Вони ходять ____ театр раз на місяць.
        answer: у
        options:
        - у
        - на
        - в
      - sentence: Вона грає ____ гітарі.
        answer: на
        options:
        - на
        - у
        - в
      - sentence: Ти граєш ____ теніс?
        answer: у
        options:
        - у
        - на
        - в
    - id: fill-in-invitations-frequency
  replace: |
    - id: fill-in-prepositions-activities
      type: fill-in
      instruction: Оберіть правильний прийменник (Choose the correct preposition)
      items:
      - sentence: Він грає ____ піаніно.
        answer: на
        options:
        - у
        - на
        - до
      - sentence: Ми граємо ____ футбол.
        answer: у/в
        options:
        - до
        - на
        - у/в
      - sentence: Я хочу ходити ____ концерт.
        answer: на
        options:
        - в
        - на
        - у
      - sentence: Вони ходять ____ театр раз на місяць.
        answer: у/в
        options:
        - на
        - у/в
        - до
      - sentence: Вона грає ____ гітарі.
        answer: на
        options:
        - у
        - до
        - на
      - sentence: Ти граєш ____ теніс?
        answer: у/в
        options:
        - на
        - у/в
        - до
    - id: fill-in-invitations-frequency

- find: |
    - id: fill-in-invitations-frequency
      type: fill-in
      instruction: Вставте правильне слово (Fill in the correct word)
      items:
      - sentence: Я ____ працюю у неділю.
        answer: ніколи не
        options:
        - ніколи не
        - завжди
        - часто
      - sentence: Вона грає у теніс двічі ____.
        answer: на тиждень
        options:
        - на тиждень
        - у тиждень
        - в тиждень
      - sentence: ____ в кіно у суботу! — Добре!
        answer: Ходімо
        options:
        - Ходімо
        - Давай
        - Ідемо
      - sentence: Я люблю спорт, тому ____ граю у баскетбол.
        answer: часто
        options:
        - часто
        - ніколи
        - рідко
      - sentence: Я не маю часу, тому ____ читаю книги.
        answer: рідко
        options:
        - рідко
        - часто
        - завжди
      - sentence: — Що ти робиш у ____? — Відпочиваю.
        answer: вихідні
        options:
        - вихідні
        - театр
        - музей
    - id: quiz-frequency
  replace: |
    - id: fill-in-invitations-frequency
      type: fill-in
      instruction: Вставте правильне слово (Fill in the correct word)
      items:
      - sentence: Я ____ працюю у неділю.
        answer: ніколи не
        options:
        - часто
        - ніколи не
        - завжди
      - sentence: Вона грає у теніс двічі ____.
        answer: на тиждень
        options:
        - в тиждень
        - на тиждень
        - у тиждень
      - sentence: ____ в кіно у суботу! — Добре!
        answer: Ходімо
        options:
        - Читаю
        - Ходімо
        - Працюю
      - sentence: Я люблю спорт, тому ____ граю у баскетбол.
        answer: часто
        options:
        - ніколи
        - часто
        - рідко
      - sentence: Я не маю часу, тому ____ читаю книги.
        answer: рідко
        options:
        - часто
        - завжди
        - рідко
      - sentence: — Що ти робиш у ____? — Відпочиваю.
        answer: вихідні
        options:
        - театр
        - вихідні
        - музей
    - id: quiz-frequency
</fixes>
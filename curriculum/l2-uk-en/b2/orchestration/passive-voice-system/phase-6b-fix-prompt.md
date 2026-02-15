Activate skill full-rebuild-core-b.

The Green Team review identified CRITICAL pedagogical errors in `curriculum/l2-uk-en/b2/activities/passive-voice-system.yaml`.

1. **Broken Fill-in Activity**:
   The activity "Трансформація: Дієприкметник → Безособова форма" is technically impossible because the noun case must change (Nominative -> Accusative), but `fill-in` only changes the verb.
   **Action**: Replace this entire activity with a `quiz` type activity titled "Трансформація: Дієприкметник → Безособова форма".
   - Instruction: "Оберіть правильний варіант трансформації речення у безособову форму (на -но/-то). Зверніть увагу на зміну відмінка!"
   - Create 10 items.
   - Example item:
     Question: "Трансформуйте: 'Ця робота була зроблена вчасно.'"
     Options:
       - text: "Цю роботу було зроблено вчасно." (Correct)
       - text: "Ця робота було зроблено вчасно." (Incorrect - wrong case)
       - text: "Цю роботу була зроблена вчасно." (Incorrect - agreements)
       - text: "Цієї роботи було зроблено вчасно." (Incorrect - Genitive)

2. **Contradictory Unjumble Items**:
   Items in "Конструювання пасивних речень" force students to use agents ("нами", "поліцією"), contradicting the module's theory.
   **Action**: Edit `curriculum/l2-uk-en/b2/activities/passive-voice-system.yaml`.
   - Item 2: Remove "нами" from `words` and `answer`. (Target: "Це питання зараз уважно розглядається").
   - Item 8: Remove "поліцією" from `words` and `answer`. (Target: "Цей злочин було швидко розкрито").
   - **Check**: Ensure the remaining words still meet the 6-word minimum!
     - "Це питання зараз уважно розглядається" (5 words). -> Expand to "Це важливе питання зараз уважно розглядається" (6 words).
     - "Цей злочин було швидко розкрито" (5 words). -> Expand to "Цей жахливий злочин було швидко розкрито" (6 words).

Use `read_file` to read the yaml, then `write_file` (or `replace` if precise) to apply fixes.

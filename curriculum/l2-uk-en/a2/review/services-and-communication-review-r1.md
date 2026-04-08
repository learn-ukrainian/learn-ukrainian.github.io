## Linguistic Scan
One major linguistic error found: the use of the verb "знаходитися" for physical location/contents (`Що знаходиться всередині?`), which is a known calque of the Russian "находиться". Natural Ukrainian uses "Що всередині?" or "Що там міститься?".
No other Russianisms, Surzhyk, or paronyms were found. The Dative noun endings (ові/еві/і) and imperative constructions are flawless.

## Exercise Check
All 4 activity markers are present, logically placed after the concepts they test, and correctly map to the `activity_hints` in the plan:
1. `<!-- INJECT_ACTIVITY: fill-in-complete-post-office-dialogue-lines-with-correct-dative-forms -->` (Placed after Dialogue section).
2. `<!-- INJECT_ACTIVITY: match-up-service-requests -->` (Placed after Requesting/Thanking section).
3. `<!-- INJECT_ACTIVITY: group-sort-dative-functions -->` (Placed after Requesting/Thanking section).
4. `<!-- INJECT_ACTIVITY: quiz-address-agreement -->` (Placed after Address section).

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The text misses the plan requirement for Dialogue 2: "asking about delivery time". The client only asks `«Де треба писати номер телефону одержувача?»` without inquiring about delivery duration. All other points are strictly covered. |
| 2. Linguistic accuracy | 9/10 | Contains a textbook calque: `«Що знаходиться всередині?»` instead of the natural `«Що всередині?»`. Otherwise, the language is highly accurate. |
| 3. Pedagogical quality | 10/10 | Excellent pedagogical breakdown of the Dative case answering "Кому?". The distinction between `дати листоноші` and `заповнити бланк` is well contextualized. |
| 4. Vocabulary coverage | 10/10 | All required and recommended words (`пошта`, `відправник`, `одержувач`, `індекс`, `бандероль`) are naturally embedded in the narrative. |
| 5. Exercise quality | 10/10 | The 4 injected activity markers correspond exactly to the plan's focus areas and are spaced appropriately. |
| 6. Engagement & tone | 9/10 | Generally excellent teacher persona, though some phrasing is overly robotic, e.g., `«купіть інший предмет. Це листівка»`. |
| 7. Structural integrity | 9/10 | Formatting artifact present where the Genitive case English translation was replaced by a duplicate in backticks: `родовий відмінок (\`родовий відмінок\`)`. The 2556 word count easily hits the target. |
| 8. Cultural accuracy | 10/10 | Authentic mention of `Укрпошта` services, yellow postboxes, and addressing protocols perfectly reflects Ukrainian postal culture. |
| 9. Dialogue & conversation quality | 10/10 | The dialogues are polite, natural, and accurately capture service interactions (e.g., `«Дайте мені, будь ласка, два конверти...»`). |

## Findings
[Linguistic accuracy] [major]
Location: `> — **Оператор:** Добрий день! Що знаходиться всередині? Це важливо знати.`
Issue: The verb "знаходитися" used for location/contents is a calque from the Russian "находиться". Natural Ukrainian simply uses "що всередині".
Fix: Remove "знаходиться" and simplify to "Що всередині?".

[Plan adherence] [minor]
Location: `> — **Оператор:** Пишіть номер телефону ось тут, унизу спеціального бланка.\n\nУ цій ситуації клієнт чітко пояснює, кому він надсилає свої речі.`
Issue: The plan specified that Dialogue 2 should include "asking about delivery time", which is completely omitted from the exchange.
Fix: Add two lines at the end of Dialogue 2 asking about delivery time and providing the answer.

[Engagement & tone] [minor]
Location: `Якщо ви хочете надіслати гарне фото з коротким текстом, купіть інший предмет. Це **листівка** *(postcard)*.`
Issue: "Купіть інший предмет" (buy another object) is extremely unnatural phrasing.
Fix: Simplify the phrasing to "вам потрібна листівка".

[Structural integrity] [minor]
Location: `Тут ми завжди використовуємо родовий відмінок (\`родовий відмінок\`).`
Issue: There is an AI formatting artifact where the Ukrainian term is duplicated inside backticks instead of the proper English translation "Genitive case".
Fix: Replace with "родовий відмінок *(Genitive case)*."

## Verdict: REVISE
The module is high-quality, pedagogical, and accurate, but it contains a known Russian calque ("знаходиться") and misses a specific dialogue requirement from the master plan. These require targeted determinist fixes before the module is approved.

<fixes>
- find: "Що знаходиться всередині? Це важливо знати."
  replace: "Що всередині? Це важливо знати."
- find: "> — **Оператор:** Пишіть номер телефону ось тут, унизу спеціального бланка.\n\nУ цій ситуації клієнт чітко пояснює, кому він надсилає свої речі."
  replace: "> — **Оператор:** Пишіть номер телефону ось тут, унизу спеціального бланка.\n> — **Клієнт:** Дякую. Підкажіть мені, скільки часу йде посилка до Львова?\n> — **Оператор:** Зазвичай посилка їде два або три дні.\n\nУ цій ситуації клієнт чітко пояснює, кому він надсилає свої речі, та дізнається про час доставки."
- find: "Якщо ви хочете надіслати гарне фото з коротким текстом, купіть інший предмет. Це **листівка** *(postcard)*."
  replace: "Якщо ви хочете надіслати гарне фото з коротким текстом, вам потрібна **листівка** *(postcard)*."
- find: "Тут ми завжди використовуємо родовий відмінок (`родовий відмінок`)."
  replace: "Тут ми завжди використовуємо родовий відмінок *(Genitive case)*."
</fixes>

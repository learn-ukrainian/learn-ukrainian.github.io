## Linguistic Scan
Errors found:
1. `сервісами доставки` — "Сервіс доставки" is a common borrowing/calque. The natural Ukrainian phrase is "службами доставки".
2. `Давайте подивимося` — Syntactic calque from Russian "давайте посмотрим". The standard Ukrainian first-person plural imperative is "Подивімося".
3. `такі дієслова як` — Orthography error. Missing comma before "як" when introducing explanatory examples. 

## Exercise Check
All activity markers (`quiz-dative-recognition`, `fill-in-dative-endings`, `match-verbs-to-case`, `error-correction-dative`) are present, correctly formatted, and match the plan's `activity_hints`. They are placed logically after their corresponding instructional sections. 

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missing the required post office dialogue from Part 2 ("Fill in correct forms in post office and service dialogues from М19"). Only a single sentence was provided. |
| 2. Linguistic accuracy | 7/10 | Found a syntactic calque ("Давайте подивимося"), a lexical calque ("сервісами доставки"), and a missing comma with "такі дієслова, як". |
| 3. Pedagogical quality | 9/10 | Excellent pedagogical notes (e.g., explaining why "подобатися" agrees with the object). However, the "подобатися" grammar was moved to Part 1 instead of Part 3 where the plan requested it. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary hints are used naturally in context. |
| 5. Exercise quality | 10/10 | Markers match the plan exactly and test the recently taught material. |
| 6. Engagement & tone | 9/10 | Tone is encouraging and appropriate. The Secret Santa scenario is culturally relevant. |
| 7. Structural integrity | 10/10 | All headers present, word count (1648 words) exceeds the 1500 target, clean Markdown. |
| 8. Cultural accuracy | 10/10 | "Таємний Санта" is an authentic representation of modern Ukrainian office culture. Phonetic rules like parallel endings are explained accurately. |
| 9. Dialogue & conversation quality | 8/10 | The Secret Santa dialogue feels slightly transactional and textbook-like ("А що потрібно купити новому колезі?"), though it effectively drills the dative forms. |

## Findings
[2. Linguistic accuracy] [Critical]
Location: `Це особливо важливо, коли ви приходите на пошту або користуєтеся сервісами доставки.`
Issue: "Сервіс доставки" is a lexical borrowing/calque. The standard natural Ukrainian phrasing is "служба доставки" (delivery service).
Fix: Change `сервісами доставки` to `службами доставки`.

[2. Linguistic accuracy] [Critical]
Location: `Давайте подивимося, як давальний відмінок працює в реальному житті.`
Issue: "Давайте подивимося" is a syntactic calque of the Russian "давайте посмотрим". The correct Ukrainian imperative is "Подивімося".
Fix: Change `Давайте подивимося, як` to `Подивімося, як`.

[2. Linguistic accuracy] [Critical]
Location: `Розуміння того, що такі дієслова як дякувати та допомагати завжди вимагають давального відмінка, допоможе вам звучати природно`
Issue: Missing comma. According to Ukrainian orthography rules, the phrase "такі дієслова, як..." requires a comma to set off the examples.
Fix: Change `що такі дієслова як дякувати та допомагати завжди` to `що такі дієслова, як дякувати та допомагати, завжди`.

[1. Plan adherence] [Major]
Location: `Частина 2: Вибір форми`
Issue: The plan explicitly required: "Fill in correct forms in post office and service dialogues from М19." However, the text only provides a single sentence about the post office ("Я хочу надіслати посилку...") before moving on to the Secret Santa dialogue.
Fix: Insert a short post office dialogue immediately after the sentence about sending a package.

## Verdict: REVISE
The module is high quality and pedagogically sound, but contains linguistic calques ("Давайте подивимося", "сервісами доставки"), a punctuation error, and misses the required post office dialogue from the plan. These must be corrected before publishing.

<fixes>
- find: "або користуєтеся сервісами доставки."
  replace: "або користуєтеся службами доставки."
- find: "Давайте подивимося, як давальний відмінок"
  replace: "Подивімося, як давальний відмінок"
- find: "що такі дієслова як дякувати та допомагати завжди"
  replace: "що такі дієслова, як дякувати та допомагати, завжди"
- find: "* **Я хочу надіслати посилку моєму старому другові.** (I want to send a package to my old friend.)\n\nAdjectives and possessives"
  replace: "* **Я хочу надіслати посилку моєму старому другові.** (I want to send a package to my old friend.)\n\n> **Працівник пошти:** Кому ви хочете надіслати цю посилку?\n> **Клієнт:** **Моєму старому другові**.\n> **Працівник пошти:** Добре. А цей лист **новій колезі**?\n> **Клієнт:** Так.\n\nAdjectives and possessives"
</fixes>

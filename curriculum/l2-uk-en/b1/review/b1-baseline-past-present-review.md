## Linguistic Scan
Found a few linguistic and stylistic errors:
- **Calque:** `перевірочне запитання` is a calque from Russian "проверочный". The correct standard Ukrainian term is `перевірне запитання`.
- **Colloquialism / Calque:** `співбесідою на роботу` is a colloquial calque from "собеседование на работу". Standard Ukrainian is simply `співбесідою` or `співбесідою щодо працевлаштування`.
- **Pleonasm:** `Англомовні мовці` is slightly redundant ("English-speaking speakers"). Better to use `Англомовні студенти`.
- **Anglicism:** Using `гендерну ідентичність` to describe the grammatical gender of a subject in a sentence is an English-centric concept transfer. In grammar, we refer strictly to `рід` (grammatical gender) or `стать` (biological sex).

*(Note: The text contains manual stress marks throughout the prose. Per the guidelines, this is ignored for scoring, but typically the pipeline handles prose stress automatically.)*

## Exercise Check
- `<!-- INJECT_ACTIVITY: group-sort -->` — matches `group-sort` (I vs II дієвідміна). Placed correctly after Section 1.
- `<!-- INJECT_ACTIVITY: fill-in-tense-forms -->` — matches `fill-in` (tense forms). Placed correctly after Section 2.
- `<!-- INJECT_ACTIVITY: quiz-aspect-id -->` — matches `quiz` (aspect identification). Placed correctly after Section 3.
- `<!-- INJECT_ACTIVITY: match-up-aspect-pairs -->` — matches `match-up` (aspectual pairs). Placed correctly after Section 3.
- `<!-- INJECT_ACTIVITY: error-correction-aspect -->` — matches `error-correction`. Placed correctly after Section 4.
- `<!-- INJECT_ACTIVITY: open-writing-yesterday -->` — matches `open-writing`. Placed correctly after Section 4.
All 6 plan activities are represented, logically spaced, and properly placed after their respective teaching concepts.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | Every point covered. Ex: the distinction of 1st vs 2nd conjugation, the past tense suffixes, the aspectual pairs (префіксальний, суфіксальний, суплетивні) are all present exactly as planned. |
| 2. Linguistic accuracy | 9/10 | Generally excellent, but deducted slightly for a few calques and pleonasms ("перевірочне", "співбесідою на роботу", "Англомовні мовці"). |
| 3. Pedagogical quality | 10/10 | Outstanding PPP flow. The writer expertly links the dialogue back to the grammar concepts: "Згадайте, як Олексій описував своє літо: «Я працював...» Оскільки Олексій — чоловік..." This is textbook-perfect pedagogy. |
| 4. Vocabulary coverage | 10/10 | All required metalanguage terms from the plan are introduced naturally, bolded, and translated (напр., *дієвідмінювання (conjugation)*, *доконаний вид (perfective aspect)*). |
| 5. Exercise quality | 10/10 | All 6 injected markers exactly match the plan's type and focus. Placements perfectly follow the conceptual explanations. |
| 6. Engagement & tone | 10/10 | Natural and encouraging without sounding corporate. The "narrative transformation" example in Section 4 is a brilliant, engaging way to demonstrate aspect. |
| 7. Structural integrity | 10/10 | The module is well-structured with all H2 headers matching the plan. Word count is 4687, safely exceeding the 4000 target. |
| 8. Cultural accuracy | 10/10 | Excellent decolonized note: "Відпадіння цього кінцевого приголосного звука є ключовою історичною та морфологічною відмінністю від російської мови, де ця літера неухильно зберігається." |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are highly natural, context-rich, and perfectly illustrate the grammar points (e.g., the coffee shop catch-up and the exam worry scenario). |

## Findings
[2. Linguistic accuracy] [Critical]
Location: "поста́вте переві́рочне запитання" and "Перевірочне запитання тут звучить так:"
Issue: "Перевірочне" is a Russian calque (проверочное). The correct pedagogical term in Ukrainian is "перевірне".
Fix: Replace "перевірочне" with "перевірне".

[2. Linguistic accuracy] [Major]
Location: "перед важливим і́спитом або складною співбе́сідою на роботу."
Issue: "Співбесіда на роботу" is a colloquial calque from Russian. Standard phrasing is just "співбесідою" or "співбесідою щодо роботи".
Fix: Replace "співбе́сідою на роботу" with "співбе́сідою".

[2. Linguistic accuracy] [Minor]
Location: "Англомо́вні мо́вці часто намага́ються механі́чно перенести́"
Issue: "Англомовні мовці" is a pleonasm (English-speaking speakers).
Fix: Replace "Англомо́вні мо́вці" with "Англомо́вні студе́нти".

[2. Linguistic accuracy] [Minor]
Location: "дієслово в минулому часі — це своєрі́дне дзе́ркало суб'єкта, яке́ відобража́є його ге́ндерну іденти́чність."
Issue: Using "gender identity" to explain grammatical gender agreement is an unnatural anglicism. The Ukrainian term is "рід".
Fix: Replace "ге́ндерну іденти́чність" with "рід".

## Verdict: REVISE
The text is exceptionally strong, rich, and pedagogically sound. However, the presence of a few calques (like "перевірочне") constitutes a critical linguistic error in a curriculum, requiring a REVISE verdict to apply deterministic fixes.

<fixes>
- find: "поста́вте переві́рочне запитання:"
  replace: "поста́вте переві́рне запитання:"
- find: "Перевірочне запитання тут звучить так:"
  replace: "Переві́рне запитання тут звучить так:"
- find: "Англомо́вні мо́вці часто намага́ються"
  replace: "Англомо́вні студе́нти часто намага́ються"
- find: "яке́ відобража́є його ге́ндерну іденти́чність."
  replace: "яке́ відобража́є його рід."
- find: "або складною співбе́сідою на роботу."
  replace: "або складною співбе́сідою."
</fixes>

## Linguistic Scan
Errors found:
1. "Це сама активна дія" — "сама" used as a superlative is a Russianism/calque. Ukrainian requires the "най-" prefix ("найактивніша").
2. "що саме мало трапитися (to happen)" — "мало трапитися" means "was supposed to happen". The correct translation for a past event "what happened" is "що саме трапилося" or "відбулося".
3. "Я отримав багато вражень" — Calque from Russian "получил впечатления". Natural Ukrainian uses phrasing like "у мене залишилося багато вражень". 
4. "дає ідеальний старт" — Unnatural phrasing/calque from sports jargon in the context of narrative storytelling. "Є ідеальним початком" is much more natural.

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->`: Placed correctly after Scenario 1. Matches plan hint (quiz on past trip description/aspect).
- `<!-- INJECT_ACTIVITY: match-up-travel-verbs -->`: Placed correctly after Scenario 2. Matches plan hint (match-up of motion verb + prep). 
- `<!-- INJECT_ACTIVITY: fill-in-travel-narrative -->`: Placed correctly after Scenario 3. Matches plan hint (fill-in).
- `<!-- INJECT_ACTIVITY: error-correction-travel -->`: Placed correctly after the Speaking Task. Matches plan hint (error-correction).
Inventory is complete (4/4) and placed logically after their corresponding topics.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Deductions for missing required questions from the plan in the dialogues. Scenario 2 is missing "Як доберемося? Поїдемо потягом чи полетимо?" and "Що будемо робити?". Scenario 3 is missing "Що найбільше сподобалось?". Otherwise, all grammatical and structural points are covered well. |
| 2. Linguistic accuracy | 7/10 | Found several critical errors: a Russianism superlative ("сама активна"), a mistranslation of intent vs reality ("мало трапитися"), and a phraseological calque ("отримав багато вражень"). |
| 3. Pedagogical quality | 9/10 | Excellent breakdown of "Stage vs. Action" principle for imperfective/perfective. Good examples of future tense formation and gender agreement in past tense. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary are used smoothly and contextually throughout the text. |
| 5. Exercise quality | 10/10 | Exact match with the 4 `activity_hints` provided in the plan. Logical placement. |
| 6. Engagement & tone | 10/10 | Positive, encouraging tone. Very clear and natural phrasing without relying on gamified corporate language. |
| 7. Structural integrity | 10/10 | All headers and sections are perfectly ordered. The word count is 2794, well above the 2000 target. |
| 8. Cultural accuracy | 10/10 | Superb emphasis on authentic Ukrainian city names (Київ, Львів) and transportation terminology ("подорож", "двірець", warning against "білет" and "путешествіє"). |
| 9. Dialogue & conversation quality | 8/10 | The dialogues are realistic and contextualize the grammar well, but docked points due to missing the questions defined in the plan outline. |

## Findings
[2. Linguistic accuracy] [Critical]
Location: Сценарій 1, "Це сама активна дія."
Issue: "Сама активна" is a Russianism/calque for forming superlatives. Ukrainian uses the "най-" prefix.
Fix: Change to "Це найактивніша дія."

[2. Linguistic accuracy] [Critical]
Location: Сценарій 1, "щоб зрозуміти, що саме мало трапитися (to happen)."
Issue: "Мало трапитися" means "was supposed to happen". The correct meaning for a completed past event is "що саме трапилося".
Fix: Change to "що саме трапилося (what happened)."

[2. Linguistic accuracy] [Critical]
Location: Сценарій 3, "Також Марко може емоційно сказати: «Я отримав багато вражень» (I got many impressions)."
Issue: "Отримати враження" is a calque of Russian "получить впечатления". A natural Ukrainian phrasing is "у мене залишилося багато вражень".
Fix: Change to "«У мене залишилося багато вражень» (I got many impressions)."

[2. Linguistic accuracy] [Major]
Location: Сценарій 1, "Слово «спочатку» дає ідеальний старт вашій історії."
Issue: "Давати старт" is unnatural for a story context, sounding like a calque from sports or business jargon.
Fix: Change to "є ідеальним початком вашої історії."

[1. Plan adherence] [Major]
Location: Сценарій 2, Dialogue between Taras and Oksana
Issue: The plan specifically requires the questions: "Як доберемося? Поїдемо потягом чи полетимо?" and "Що будемо робити?". These are missing from the dialogue.
Fix: Add these questions and corresponding responses to the dialogue.

[1. Plan adherence] [Major]
Location: Сценарій 3, Dialogue between Marko and Olena
Issue: The plan specifically requires the question: "Що найбільше сподобалось?". This is missing from the dialogue.
Fix: Add this question and Marko's response to the end of the dialogue.

## Verdict: REVISE
The module exceeds the word count and has a fantastic pedagogical structure, but it contains critical linguistic errors (a superlative Russianism and a mistranslated verbal phrase) and missed a few explicit requirements in the dialogues from the plan. It requires a deterministic find/replace pass.

<fixes>
- find: "Це сама активна дія."
  replace: "Це найактивніша дія."
- find: "щоб зрозуміти, що саме мало трапитися (to happen)."
  replace: "щоб зрозуміти, що саме трапилося (what happened)."
- find: "«Я отримав багато вражень» (I got many impressions)."
  replace: "«У мене залишилося багато вражень» (I got many impressions)."
- find: "дає ідеальний старт вашій історії."
  replace: "є ідеальним початком вашої історії."
- find: "Коли ми виїдемо з міста? *(That's a great idea! When will we depart from the city?)*"
  replace: "Коли ми виїдемо з міста і як доберемося? Поїдемо потягом чи полетимо? *(That's a great idea! When will we depart from the city and how will we get there? Will we go by train or fly?)*"
- find: "Ми виїдемо в п'ятницю ввечері. *(We will depart on Friday evening.)*"
  replace: "Ми виїдемо в п'ятницю ввечері і поїдемо нічним потягом. *(We will depart on Friday evening and go by night train.)*"
- find: "> — **Оксана:** Супер! Я впевнена, що наша подорож буде цікавою. *(Super! I am sure our trip will be interesting.)*"
  replace: "> — **Оксана:** Супер! А що ми будемо там робити? *(Super! And what will we do there?)*\n> — **Тарас:** Ми будемо гуляти лісом і насолоджуватися природою. *(We will walk in the forest and enjoy nature.)*\n> — **Оксана:** Я впевнена, що наша подорож буде цікавою. *(I am sure our trip will be interesting.)*"
- find: "> — **Марко:** Ми багато ходили на **пляж** (beach) і просто дивилися на **море** (sea). Це був чудовий відпочинок! *(We went to the beach a lot and just looked at the sea. It was a wonderful vacation!)*"
  replace: "> — **Марко:** Ми багато ходили на **пляж** (beach) і просто дивилися на **море** (sea). Це був чудовий відпочинок! *(We went to the beach a lot and just looked at the sea. It was a wonderful vacation!)*\n> — **Олена:** А що тобі найбільше сподобалося? *(And what did you like the most?)*\n> — **Марко:** Найбільше мені сподобалася місцева природа. *(I liked the local nature the most.)*"
</fixes>

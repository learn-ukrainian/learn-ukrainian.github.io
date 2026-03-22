  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=51256 chars: ROLE: You are a TEXT GENERATOR executing a specific task. You produce text output. That's it.  ABSOLUTE RULES — VIOLATION OF ANY RULE MEANS TASK FAILURE:  1. OUTPUT ONLY TEXT. Your ONLY job is to read...
## Linguistic Scan

- **Factual Phonetic Error:** The text claims the consonant `[р]` is "завжди твердий" (always hard / has no soft pair). This is factually incorrect in Ukrainian; `[р]` has a soft pair `[р']` (e.g., *рік, ряд, буря*). The AI directly contradicts itself, having correctly transcribed `[р']` earlier in the word `школярі́ [школ'ар'і]`.
- **Hallucinated Minimal Pair:** `кон (an older form) vs кінь (horse)`. "Кон" is not a valid Ukrainian word meaning "older form of horse" (this is a Russicism/invention). The word `кін` exists (meaning stake/scene, genitive `кону`), but it's not a valid minimal pair for `[н]` vs `[н']` in this context. 
- **Lexical Error:** `на листках клині́в` — "клин" means wedge (genitive plural: клинів). The text meant "кленів" (maple trees).
- **Unusual Name:** `Мале́нька Бори́вка` — "Боривка" is not a standard Ukrainian name and sounds like a typo or hallucination.
- **English Calque / Translation Error:** `great letters have no place` — Calquing "великі літери" directly into English as "great letters" instead of "capital letters" or "uppercase letters".

## Exercise Check

1. **`:::quiz` "Звук, літера чи фонема?" (8 items)**
   - *Issue:* Deviates from plan. The plan requested: `focus: "Classify sounds: голосний чи приголосний? дзвінкий чи глухий?"`. The generated quiz tests meta-knowledge and definitions (фонетика vs графіка) instead of practical sound classification.
2. **`:::match-up` "З'єднай термін із визначенням" (8 items)**
   - *Issue:* Matches plan hint. Logic is sound.
3. **`:::group-sort` "Розподіли приголосні на три групи" (16 items total)**
   - *Issue:* Plan requested 10 items. Generated 16 items. Otherwise, the logic is correct.
4. **`:::fill-in` "Запишіть фонетичну транскрипцію" (6 items)**
   - *Issue:* Matches plan hint. Correct logic.
5. **`:::true-false` "Правда чи неправда?" (6 items)**
   - *Issue:* Not requested in the plan's `activity_hints`.
6. **Prose / Missing Exercise (`<!-- mark-the-words exercise... -->`)**
   - *Issue:* The AI failed to use the DSL and left an internal comment: `<!-- mark-the-words exercise: the DSL doesn't have a mark-the-words type in the approved list, so using the closest equivalent -->`. It then wrote the exercise as plain prose, failing the interactive requirement.
7. **`:::quiz` "Знайди і виправ помилку в транскрипції" (6 items)**
   - *Issue:* Replaced the requested `error-correction` type with a `quiz` type.

## Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 2/10 | Severe word count shortfall (~1500-2000 words vs 4000 target). Missed/altered specific `activity_hints` (e.g., changed the focus of the first quiz). |
| 2. Linguistic accuracy | 4/10 | Major phonetic factual error (`[р]` is not always hard). Hallucinated "кон". Lexical errors ("клинів"). |
| 3. Pedagogical quality | 4/10 | Left "thinking traces" in the text which confuses the learner. English explanation uses bizarre calques ("great letters"). |
| 4. Vocabulary coverage | 9/10 | Integrates almost all required and recommended vocabulary terms naturally into the explanations and final glossary. |
| 5. Exercise quality | 5/10 | Failed to implement `mark-the-words`, deviating to prose. Changed the objective of the initial quiz. |
| 6. Engagement & tone | 3/10 | AI's internal monologue ("wait, let us use a clearer example") destroys the authoritative tone and immersion. |
| 7. Structural integrity | 1/10 | Critical failure: The text contains raw LLM artifacts, meta-commentary, and HTML comments visible to the user. |
| 8. Cultural accuracy | 7/10 | Explains Ukrainian phonetics independently of Russian, but invents a strange name ("Боривка"). |
| 9. Dialogue & conversation quality | 6/10 | The short reading passage contains a bizarre name and a blatant typo ("клинів" vs "кленів"). |

## Findings

[Structural integrity] [critical]
Location: `## Наголос (Stress)` -> "...вікóн (windows, genitive plural) — wait, let us use a clearer example" AND `## Приголосні звуки: тверді та м'які` -> "...[р] vs [р']: wait, «р» is always hard in Ukrainian. Let us use a better pair:"
Issue: Raw LLM artifacts, self-correction, and internal monologue were printed directly into the student-facing text.
Fix: Remove all meta-commentary. Present only the final, correct examples cleanly.

[Linguistic accuracy] [critical]
Location: `### Класифікація: які́ приголосні — за́вжди́ тверді?` -> "Завжди тверді (always hard — no soft pair): [б], [п], [в], [м], [ф], [г], [ґ], [к], [х], [ж], [ч], [ш], [дж], [р]."
Issue: Factual phonetic error. The consonant `[р]` is NOT always hard in Ukrainian; it has a valid soft pair `[р']` (e.g., *рік*, *буря*, *школярі*). The AI even used `[р']` correctly in a previous section, creating a direct contradiction.
Fix: Remove `[р]` from the "Завжди тверді" list. Move it to the list of consonants that have a soft pair, or add a specific note about its unique phonetic rules.

[Plan adherence] [critical]
Location: Entire document.
Issue: The module falls drastically short of the 4000-word target (estimated at <2000 words).
Fix: Expand the content significantly with more detailed explanations, longer reading passages, more phonetic examples, and deeper cultural context regarding Ukrainian pronunciation.

[Exercise quality] [critical]
Location: `<!-- mark-the-words exercise: the DSL doesn't have a mark-the-words type in the approved list, so using the closest equivalent -->`
Issue: AI left an HTML comment breaking the fourth wall regarding DSL limitations, and failed to generate an interactive exercise, relying on prose instead.
Fix: Remove the HTML comment and format the exercise using a valid DSL type that achieves the same pedagogical goal (e.g., another `group-sort` or a `quiz`).

[Linguistic accuracy] [major]
Location: `## Приголосні звуки: тверді та м'які` -> "кон (an older form) vs кінь (horse) — [н] vs [н']"
Issue: Hallucination. "кон" is not a standard Ukrainian word meaning an older form of horse.
Fix: Replace with a genuine minimal pair, such as "лан" (field) vs "лань" (doe), or "син" (son) vs "синь" (deep blue).

[Engagement & tone] [major]
Location: `### Правила транскри́пції` -> "3. НЕ використо́вуємо... вели́кі букви. ... great letters have no place because sounds do not have uppercase."
Issue: Unnatural English translation. Calquing "великі літери" to "great letters" will confuse L2 learners.
Fix: Change "great letters" to "capital letters" or "uppercase letters".

[Linguistic accuracy] [major]
Location: `### Чита́ння: знайді́ть дзвінкі, глухі та сонорні` -> "на листках клині́в."
Issue: Lexical error. "клинів" is the genitive plural of "клин" (wedge). It should be "кленів" (maple trees).
Fix: Change "клинів" to "кленів". (Also recommend changing the hallucinated name "Боривка" to a real name like "Богданка" or "Борислава").

[Exercise quality] [major]
Location: `:::quiz` "Звук, літера чи фонема?"
Issue: Deviates from the plan's exact instructions. Plan requested a quiz focusing on classifying sounds ("голосний чи приголосний? дзвінкий чи глухий?"), but the AI generated a quiz on metalanguage definitions.
Fix: Rewrite the first quiz to focus on classifying actual sounds as specified in the `activity_hints`.

## Verdict: REJECT
The module contains critical LLM artifacts ("wait, let us use a clearer example") published directly into the text, a massive factual error regarding Ukrainian phonetics (`[р]` labeled as always hard), and falls drastically short of the word count target. It requires a complete rewrite to remove AI fingerprints, fix the phonetic logic, and meet the required depth.

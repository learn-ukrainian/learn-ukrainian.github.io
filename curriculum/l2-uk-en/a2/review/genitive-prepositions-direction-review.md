## Linguistic Scan
1 error found:
- "знаходиться" in the sense of physical location ("Вона знаходиться біля старого парку") is a calque from Russian "находится". It should be replaced with "розташована" or omitted (e.g., "Вона біля старого парку").

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-genitive-forms -->` is correctly placed after the Genitive Forms grammar explanation. Matches the plan's `fill-in` hint.
- `<!-- INJECT_ACTIVITY: match-up-functions -->` is correctly placed after the time ranges section. Matches the plan's `match-up` hint.
- `<!-- INJECT_ACTIVITY: group-sort-categories -->` is correctly placed after the purpose and readiness section. Matches the plan's `group-sort` hint.
- `<!-- INJECT_ACTIVITY: quiz-meaning-choice -->` is correctly placed after the summary comparison. Matches the plan's `quiz` hint.
All 4 markers are present, appropriately placed, and exactly match the required types in the plan.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | DEDUCT: The outline specifically required teaching neuter nouns ("до моря (soft neuter)"), but this was completely omitted from the text's grammar notes. Additionally, the English translations for two H2 headings from the plan ("Where Are You Going?..." and "Other Meanings and Summary") were dropped. |
| 2. Linguistic accuracy | 8/10 | DEDUCT: Contains a known Russian calque for physical location ("Вона знаходиться біля старого парку"). This must be fixed to ensure learners do not pick up conversational Surzhyk/calques. The rest of the Ukrainian grammar forms and rules are flawless. |
| 3. Pedagogical quality | 9/10 | REWARD: Excellent explanation of `до` vs `в/на` for people vs places, and a brilliant summary comparing `від`, `до`, and `після`. DEDUCT (minor): The English translation in the dialogue "I have very much work" is slightly awkward ("a lot of work" is better). |
| 4. Vocabulary coverage | 9/10 | DEDUCT: The required word "мета" (purpose) was only included in the final summary table. It should be introduced naturally in the running prose when the concept of purpose is first taught. |
| 5. Exercise quality | 10/10 | REWARD: All 4 injected markers are present, perfectly match the `activity_hints` from the plan, and are placed logically after the relevant instructional content. |
| 6. Engagement & tone | 10/10 | REWARD: The tone is natural, encouraging, and structured clearly. It addresses common learner pitfalls (like using 'в лікар') gracefully and explains concepts gently. |
| 7. Structural integrity | 9/10 | DEDUCT: The missing English text in the H2 headings slightly violates the plan's exact structural requirement for these sections. Word count is healthy (2259 words). |
| 8. Cultural accuracy | 10/10 | REWARD: Accurately explains why the Russian "к" + Dative is incorrect in Ukrainian, explicitly reinforcing a decolonized perspective on the language and teaching authentic sentence structures. |
| 9. Dialogue & conversation quality | 9/10 | REWARD: Dialogues feature named speakers and highly contextual, natural phrasing ("Мені дуже треба купити ліки", "Чудово! Передавай вітання!"). |

## Findings
[1. Linguistic accuracy] [critical]
Location: `— **Таксист:** Добре, я знаю, де є аптека. Вона знаходиться біля старого парку.`
Issue: Using "знаходиться" to describe physical location is a well-known calque from Russian "находится". In Ukrainian, things are "розташовані" or simply "є" / omitted entirely.
Fix: Simplify to "Вона біля старого парку."

[2. Plan adherence] [major]
Location: `**Жіночий рід (Feminine):**\nшкола *(school)* → до школи...`
Issue: The plan explicitly required teaching neuter nouns ("до моря (soft neuter)") under the stem rules, but this was entirely left out of the prose and examples block.
Fix: Add a "**Середній рід (Neuter):**" section with the example "море *(sea)* → до моря" to the Genitive forms note.

[3. Structural integrity] [minor]
Location: `## Куди ти йдеш? До + родовий для напрямку` and `## До + родовий: решта значень та узагальнення`
Issue: The English translations specified in the plan's H2 headings were dropped.
Fix: Append the exact English translations from the plan to the headers.

[4. Vocabulary coverage] [major]
Location: `Beyond physical movement and time, the preposition **до** *(to/for/until)* frequently expresses purpose, readiness, and abstract goals.`
Issue: The required vocabulary word "мета" is only shown in the summary table and is missing from the prose context.
Fix: Add "*(мета)*" immediately after the word "purpose" to introduce the vocabulary item natively.

[5. Pedagogical quality] [minor]
Location: `I know. But I have very much work.`
Issue: "Very much work" is awkward literal English. "A lot of work" is the natural phrasing.
Fix: Replace "very much" with "a lot of".

## Verdict: REVISE
The module is incredibly well-written and pedagogically sound, providing clear and robust grammar guidance. However, it contains a critical Russian calque ("знаходиться") and misses a few specific structural elements from the plan (neuter noun examples, English headers, prose integration of "мета"). Fixing these will ensure it meets the highest standards.

<fixes>
- find: "Вона знаходиться біля старого парку."
  replace: "Вона біля старого парку."
- find: |
    **Жіночий рід (Feminine):**
    школа *(school)* → до школи
    станція *(station)* → до станції
    площа *(square)* → до площі
    :::
  replace: |
    **Жіночий рід (Feminine):**
    школа *(school)* → до школи
    станція *(station)* → до станції
    площа *(square)* → до площі

    **Середній рід (Neuter):**
    море *(sea)* → до моря
    :::
- find: "## Куди ти йдеш? До + родовий для напрямку"
  replace: "## Куди ти йдеш? До + родовий для напрямку (Where Are You Going? До + Genitive for Direction)"
- find: "## До + родовий: решта значень та узагальнення"
  replace: "## До + родовий: решта значень та узагальнення (До + Genitive: Other Meanings and Summary)"
- find: "frequently expresses purpose, readiness, and abstract goals."
  replace: "frequently expresses purpose *(мета)*, readiness, and abstract goals."
- find: "I know. But I have very much work."
  replace: "I know. But I have a lot of work."
</fixes>

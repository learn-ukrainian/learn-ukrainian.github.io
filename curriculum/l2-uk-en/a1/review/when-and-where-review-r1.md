## Linguistic Scan
Errors and minor stylistic issues found:
- **Factual grammatical error:** Stating that there are "no exceptions" to the comma before *що/де/коли* is wrong (e.g., elliptical single-word clauses like "Я не знаю де." do not take a comma).
- **Style/Calque:** "добрий час" is a slight calque for "good time" instead of the more idiomatic "гарний час" or "зручний час".
- **Usage/Idiom:** "Де побачиш фонтан" is slightly awkward for temporal/spatial directions; "Коли побачиш" is more standard.
- **Pedagogical clarity:** Grouping the perfective imperative "Скажи" directly under the imperfective lemma "казати" without noting the pair may cause morphological confusion later.

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-comma-placement -->` (Matches hint 4: Where is the comma?)
- `<!-- INJECT_ACTIVITY: quiz-question-or-conjunction -->` (Matches hint 2: Question word or conjunction?)
- `<!-- INJECT_ACTIVITY: fill-in-conjunction-choice -->` (Matches hint 1: Complete with що/де/коли)
- `<!-- INJECT_ACTIVITY: fill-in-build-sentences -->` (Matches hint 3: Build complex sentences)
All 4 requested activity markers are present, logically placed after their respective teaching sections, and appropriately test the material just taught.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Covered all sections and dialog structures from the plan. Minor deduction for skipping some recommended vocabulary (`чути`, `розуміти`, `головне`). |
| 2. Linguistic accuracy | 8/10 | Included a factually incorrect absolute rule (`Ukrainian ALWAYS places a comma before що, де, коли when they serve as conjunctions — no exceptions.`). Used a slightly unnatural calque (`добрий час`) and spatial phrasing (`Де побачиш фонтан`). |
| 3. Pedagogical quality | 9/10 | Excellent breakdown of the difference between question words and conjunctions, with very clear examples. Minor deduction for grouping "Скажи" under "Казати" without noting it's a perfective pair, which could cause morphological confusion for learners trying to construct it. |
| 4. Vocabulary coverage | 9/10 | All required vocabulary (`що, де, коли, знати, думати, казати`) used naturally and repeatedly in context. |
| 5. Exercise quality | 10/10 | Markers perfectly match the plan's `activity_hints` and are placed correctly after the relevant explanations. |
| 6. Engagement & tone | 10/10 | The dialogues are highly engaging, featuring named speakers in realistic, highly communicative situations. The tone is encouraging but focused. |
| 7. Structural integrity | 9/10 | Clean structure, but leaked a generated AI artifact at the bottom of the file (`**Deterministic word count...`). |
| 8. Cultural accuracy | 10/10 | Culturally neutral and accurate. |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are expanded beyond the plan beautifully, creating very natural multi-turn conversations that seamlessly integrate the target grammar. |

## Findings
[2. Linguistic accuracy] [Major]
Location: `Ukrainian ALWAYS places a comma before **що**, **де**, **коли** when they serve as conjunctions — no exceptions.`
Issue: The "no exceptions" claim is factually incorrect. In Ukrainian, a comma is NOT placed if the subordinate clause consists of a single relative word/conjunction (e.g., "Я не знаю де."). While the comma is almost always used in A1 contexts, teaching an absolute "no exceptions" rule is dangerous and creates unlearning debt.
Fix: Soften the rule to state it applies when connecting two parts of a sentence.

[2. Linguistic accuracy] [Major]
Location: `Write this rule in your notebook: comma + conjunction = always paired in Ukrainian.`
Issue: Same as above. The absolutism "always paired" is grammatically incorrect.
Fix: Change to "the standard pair".

[2. Linguistic accuracy] [Minor]
Location: `Я теж думаю, що о шостій — добрий час.`
Issue: "Добрий час" is a slight calque of "good time". In Ukrainian, "зручний час", "вдалий час", or "гарний час" (as written in the original plan) is more natural in this context.
Fix: Change "добрий час" to "гарний час".

[2. Linguistic accuracy] [Minor]
Location: `Де побачиш фонтан — поверни ліворуч.`
Issue: While understandable, "Де побачиш" (Where you see) is slightly awkward for temporal/spatial directions compared to "Коли побачиш" (When you see). The original plan separated these more cleanly.
Fix: Change "Де" to "Коли".

[3. Pedagogical quality] [Minor]
Location: `«Казати» works with all three conjunctions: «Він каже, що вона в Києві», «Вона казала, де магазин», «Скажи, коли прийдеш».`
Issue: Grouping "Скажи" directly under the imperfective "казати" without mentioning it is a different verb ("сказати") can cause morphological confusion, as learners might assume "скажи" is formed directly from the "каз-" stem.
Fix: Add a brief parenthetical mention of its perfective pair.

[7. Structural integrity] [Minor]
Location: `**Deterministic word count: 1946 words** (calculated by pipeline, do NOT estimate manually)`
Issue: AI artifact/meta-commentary leaked into the final text.
Fix: Remove the artifact.

## Verdict: REVISE
The module is extremely well-written with great dialogues and clear explanations, but it requires revision to fix the factual error regarding the "no exceptions" comma rule, a minor calque, and the AI artifact at the bottom of the file.

<fixes>
- find: "Ukrainian ALWAYS places a comma before **що**, **де**, **коли** when they serve as conjunctions — no exceptions."
  replace: "Ukrainian ALWAYS places a comma before **що**, **де**, **коли** when they connect two parts of a sentence."
- find: "Write this rule in your notebook: comma + conjunction = always paired in Ukrainian."
  replace: "Write this rule in your notebook: comma + conjunction = the standard pair in Ukrainian."
- find: "Я теж думаю, що о шостій — добрий час."
  replace: "Я теж думаю, що о шостій — гарний час."
- find: "Де побачиш фонтан — поверни ліворуч."
  replace: "Коли побачиш фонтан — поверни ліворуч."
- find: "«Казати» works with all three conjunctions: «Він каже, що вона в Києві», «Вона казала, де магазин», «Скажи, коли прийдеш»."
  replace: "«Казати» (and its pair **сказати**) works with all three conjunctions: «Він каже, що вона в Києві», «Вона казала, де магазин», «Скажи, коли прийдеш»."
- find: "**Deterministic word count: 1946 words** (calculated by pipeline, do NOT estimate manually)"
  replace: " "
</fixes>

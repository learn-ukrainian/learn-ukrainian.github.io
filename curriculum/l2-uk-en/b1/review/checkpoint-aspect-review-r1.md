## Linguistic Scan
Errors found:
1. `Олено:` and `Марку:` - Speaker tags must be in Nominative case (`Олена:`, `Марко:`), not Vocative.
2. `стан природи` - Grammatical case error. After the noun `опису`, the dependent nouns must be in the genitive case. It should be `стану природи` (опису атмосфери, стану природи або звичних занять).
3. `відкриєте комп'ютер` - Unnatural phrasing (calque). In Ukrainian, you don't "open" a desktop computer unless you are fixing the hardware. It should be `увімкнете комп'ютер` (turn on) or `відкриєте ноутбук`.

## Exercise Check
- Marker logic and placement are excellent. Each marker directly follows the relevant instruction, testing exactly what was just taught.
- **Issue**: Marker IDs include custom suffixes (`group-sort-future-imperative`, `error-correction-imperative`, etc.) rather than strictly matching the plan's expected types (`group-sort`, `error-correction`). This mismatch can cause the downstream injection script to fail to link the plan's `activity_hints` to the markers.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module follows the structure perfectly but completely misses the explicit teaching of the required vocabulary term "**видова пара**", even though it explains prefixation. Furthermore, textbook references (Литвінова, Заболотний, Авраменко) are vaguely generalized as "з підручника" rather than explicitly cited. |
| 2. Linguistic accuracy | 7/10 | 1) Case error: "опису атмосфери, стан природи" (should be `стану`). 2) Vocative case in speaker tags: "> — **Олено:**" instead of Nominative `Олена:`. 3) Unnatural phrasing: "відкриєте комп'ютер" instead of `увімкнете комп'ютер`. |
| 3. Pedagogical quality | 10/10 | Superb "movie director" analogy for aspect. The contextual breakdown of negative imperatives ("не падай" vs "не впади" for rules vs warnings) is an exceptional, high-level explanation. |
| 4. Vocabulary coverage | 9/10 | All required vocabulary is present except the term `видова пара`. |
| 5. Exercise quality | 9/10 | Exercises test what was just taught, but marker IDs deviate from the exact plan types (e.g., `<!-- INJECT_ACTIVITY: open-writing-aspect-check -->` instead of `open-writing`). |
| 6. Engagement & tone | 10/10 | Excellent teacher persona. Tone is firm, encouraging, and avoids corporate/gamified filler. |
| 7. Structural integrity | 8/10 | A stray prompt artifact made its way into an H2 header: `## Вид у майбутньому та наказовому (~1000 words total)`. Word count is safely over the 4000-word target. |
| 8. Cultural accuracy | 10/10 | Authentic situations and natural Ukrainian framing without relying on English-centric tenses. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are perfectly crafted to illustrate aspect differences, though formatting requires fixing (the vocative speaker tags). |

## Findings
[1. Plan adherence] [Major]
Location: Section "Вид в умовному способі та підсумок", paragraph 3 ("Коли ви додаєте префікс до дієслова...")
Issue: The required vocabulary term "видова пара" is missing from the prose, despite the concept being explained.
Fix: Add the term when explaining prefixation.

[2. Linguistic accuracy] [Critical]
Location: Section "Вид і заперечення", first dialogue ("> — **Олено:** Ти знаєш...", "> — **Марку:** Ні, я не читав...")
Issue: Speaker labels in written dialogue must use the Nominative case (Хто говорить? - Олена, Марко), not the Vocative case. 
Fix: Change `Олено:` to `Олена:` and `Марку:` to `Марко:`.

[2. Linguistic accuracy] [Critical]
Location: Section "Вид у минулому: тло і послідовність", paragraph 4 ("Тому завжди обирайте недоконаний вид для опису атмосфери, стан природи або звичних занять...")
Issue: Grammatical case error. The noun "стан" must be in the genitive case ("стану") because it is part of a list governed by the noun "опису" (опису атмосфери, опису стану природи).
Fix: Change "стан природи" to "стану природи".

[2. Linguistic accuracy] [Major]
Location: Section "Вид у майбутньому та наказовому", paragraph 3 ("Ви сядете за свій робочий стіл, відкриєте комп'ютер, і ви не зупинитеся...")
Issue: Unnatural phrasing (calque of "open your computer"). In Ukrainian, you turn on a computer or open a laptop. 
Fix: Change "відкриєте комп'ютер" to "увімкнете комп'ютер".

[5. Exercise quality] [Minor]
Location: End of sections (e.g., `<!-- INJECT_ACTIVITY: group-sort-future-imperative -->`)
Issue: Activity marker IDs include extra suffixes, which may cause the pipeline to fail to match the plan's `activity_hints`.
Fix: Simplify the markers to match the exact types specified in the plan.

[7. Structural integrity] [Major]
Location: H2 Header before paragraph 7 ("## Вид у майбутньому та наказовому (~1000 words total)")
Issue: The header contains a stray word-count instruction artifact from the prompt.
Fix: Remove the artifact from the header.

## Verdict: REVISE
The module is pedagogically brilliant but contains critical linguistic errors (speaker tag cases, grammatical case error) and structural artifacts (header word count, mismatched marker IDs, missing required term) that require deterministic correction before it can pass. 

<fixes>
- find: "> — **Олено:** Ти знаєш, чим закінчився цей детектив?"
  replace: "> — **Олена:** Ти знаєш, чим закінчився цей детектив?"
- find: "> — **Марку:** Ні, я не читав цю книгу взагалі."
  replace: "> — **Марко:** Ні, я не читав цю книгу взагалі."
- find: "> — **Олено:** А я почала, але не прочитала до кінця,"
  replace: "> — **Олена:** А я почала, але не прочитала до кінця,"
- find: "для опису атмосфери, стан природи або звичних занять"
  replace: "для опису атмосфери, стану природи або звичних занять"
- find: "## Вид у майбутньому та наказовому (~1000 words total)"
  replace: "## Вид у майбутньому та наказовому"
- find: "Ви сядете за свій робочий стіл, відкриєте комп'ютер, і ви не зупинитеся"
  replace: "Ви сядете за свій робочий стіл, увімкнете комп'ютер, і ви не зупинитеся"
- find: "Коли ви додаєте префікс до дієслова (наприклад, «робити» → «зробити»,"
  replace: "Коли ви додаєте префікс до дієслова, створюючи **видову пару** *(aspectual pair)* (наприклад, «робити» → «зробити»,"
- find: "<!-- INJECT_ACTIVITY: group-sort-future-imperative -->"
  replace: "<!-- INJECT_ACTIVITY: group-sort -->"
- find: "<!-- INJECT_ACTIVITY: error-correction-imperative -->"
  replace: "<!-- INJECT_ACTIVITY: error-correction -->"
- find: "<!-- INJECT_ACTIVITY: match-up-negation-meaning -->"
  replace: "<!-- INJECT_ACTIVITY: match-up -->"
- find: "<!-- INJECT_ACTIVITY: open-writing-aspect-check -->"
  replace: "<!-- INJECT_ACTIVITY: open-writing -->"
</fixes>

## Linguistic Scan
No linguistic errors found.

## Exercise Check
- `<!-- INJECT_ACTIVITY: quiz-gender-agreement -->`: Present and correctly placed after the knowledge check section.
- `<!-- INJECT_ACTIVITY: fill-in-shopping-dialogue -->`: **Misplaced.** Present, but placed *before* the Connected Dialogue section it is meant to practice, breaking the pedagogical flow.
- `<!-- INJECT_ACTIVITY: group-sort-vocabulary -->`: Present and correctly placed.
- `<!-- INJECT_ACTIVITY: quiz-singular-plural -->`: Present and correctly placed at the end for review.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Covers all requested topics thoroughly, but deterministic word count (1578) is significantly above the target (1200). |
| 2. Linguistic accuracy | 10/10 | Excellent. Gender agreement, plurals, and number usage are all flawlessly executed. |
| 3. Pedagogical quality | 7/10 | Introduces untaught Locative ("На столі") and Instrumental ("За вікном") cases in the reading practice, which violates A1 sequencing. The shopping dialogue activity is also presented before the dialogue itself. |
| 4. Vocabulary coverage | 10/10 | Effectively integrates target cultural vocabulary (вишиванка, глечик, намисто, писанки) and reviews colors/adjectives perfectly. |
| 5. Exercise quality | 8/10 | All markers are present and match plan IDs, but the fill-in dialogue activity is misplaced before the dialogue. |
| 6. Engagement & tone | 7/10 | Contains meta-commentary ("Work through each self-check question honestly") and motivational fluff ("Ukrainian is not built in one day", "now they start to move") that should be trimmed. |
| 7. Structural integrity | 8/10 | Headers match the plan well, but the overall length exceeds limits. |
| 8. Cultural accuracy | 10/10 | Great authentic context with the ярмарок setting and culturally specific items seamlessly integrated. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue is highly practical, reviews the grammar points naturally, and features clear speaker voices. |

## Findings
[Pedagogical quality] [major]
Location: Чита́ння (Reading Practice) - "> **На столі́ є три книги.**" and "> **За вікно́м є парк.**"
Issue: The reading text introduces nouns in the Locative ("на столі") and Instrumental ("за вікном") cases, which are forward-references that have not been taught yet in A1. The plan specifies using ONLY vocabulary from M08-M13.
Fix: Replace with phrases that do not require untaught cases, such as "У мене є" or "Там".

[Exercise quality] [major]
Location: Грама́тика (Grammar Summary) / Діало́г (Connected Dialogue)
Issue: The `<!-- INJECT_ACTIVITY: fill-in-shopping-dialogue -->` marker is placed before the Connected Dialogue section. It asks learners to practice a dialogue before they have even seen the primary example, breaking the PPP sequence.
Fix: Move the marker to appear immediately after the Connected Dialogue section.

[Engagement & tone] [minor]
Location: Що ми зна́ємо? and Підсумок — Summary
Issue: The text includes meta-commentary ("Work through each self-check question honestly") and motivational fluff ("The building blocks are ready — now they start to move", "Ukrainian is not built in one day").
Fix: Trim the meta-commentary and focus purely on language review.

[Structural integrity] [minor]
Location: Entire document
Issue: The module exceeds the 1200-word target by over 30% (1578 words).
Fix: The tone fixes will trim some length, but the module is slightly verbose overall.

## Verdict: REVISE
The module is very strong linguistically and culturally, but requires a revision to fix pedagogical sequencing (untaught case endings) and structural flow (misplaced activity marker and excessive meta-commentary).

<fixes>
- find: "> **На столі́ є три книги.** *(On the table there are three books.)*"
  replace: "> **У мене́ є три книги.** *(I have three books.)*"
- find: "> **За вікно́м є парк.** *(Beyond the window there is a park.)*"
  replace: "> **Там є парк.** *(There is a park there.)*"
- find: "- **Скі́льки книг на столі?** (How many books on the table?) → **три** (three)"
  replace: "- **Скі́льки є книг?** (How many books are there?) → **три** (three)"
- find: |
    Memorize the forms you have seen rather than trying to derive them.

    <!-- INJECT_ACTIVITY: fill-in-shopping-dialogue -->

    ## Діало́г (Connected Dialogue)
  replace: |
    Memorize the forms you have seen rather than trying to derive them.

    ## Діало́г (Connected Dialogue)
- find: |
    Every price uses the number vocabulary from M11. This single dialogue puts all of A1.2 into action.

    <!-- INJECT_ACTIVITY: group-sort-vocabulary -->
  replace: |
    Every price uses the number vocabulary from M11. This single dialogue puts all of A1.2 into action.

    <!-- INJECT_ACTIVITY: fill-in-shopping-dialogue -->

    <!-- INJECT_ACTIVITY: group-sort-vocabulary -->
- find: |
    You have completed A1.2 — six modules covering the building blocks of describing your world in Ukrainian. Before moving forward, take a moment to check whether the skills from M08–M13 have stuck. Work through each self-check question honestly. If any answer feels uncertain, the grammar summary and reading practice below will help you solidify it.
  replace: |
    You have completed A1.2 — six modules covering the building blocks of describing your world in Ukrainian. Before moving forward, check your understanding of the skills from M08–M13. If any answer feels uncertain, review the grammar summary and reading practice below.
- find: |
    What comes next? In A1.3 — *Actions* — you will meet Ukrainian verbs for the first time. What do you do? What do you like? The nouns and adjectives from A1.2 will combine with verbs to make real sentences about real life. The building blocks are ready — now they start to move.

    Ukrainian is not built in one day. It is built in six modules at a time, then six more. You just finished the second set. The language is already yours to describe the world around you. **Молоде́ць! Продо́вжуємо.** *(Well done! We continue.)*
  replace: |
    What comes next? In A1.3 — *Actions* — you will meet Ukrainian verbs for the first time. What do you do? What do you like? The nouns and adjectives from A1.2 will combine with verbs to make new sentences.

    You can now describe the world around you in Ukrainian. **Молоде́ць! Продо́вжуємо.** *(Well done! We continue.)*
</fixes>

## Linguistic Scan
No linguistic errors found.

## Exercise Check
- 4 activity markers are present: `fill-in-directions`, `quiz-locative-accusative`, `fill-in-transport-route`, `match-up-navigation-responses`.
- All 4 marker IDs match the plan’s `activity_hints`.
- Placement is correct: each marker comes after the concept it is meant to test.
- Markers are distributed evenly across the module, not clustered at the end.
- No inline DSL exercise blocks are present, so there are no inline logic issues to audit here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All planned sections are present, and the core content is covered, but fidelity slips in specifics: the plan’s Lviv route is introduced as `Площа Ринок ... Оперний театр ... Високий замок`, while the actual dialogue reduces this to `В театр.` / `З замку.`; the plan/example focus on `на метро` becomes `Їдьте трамваєм до центру.`; section pacing is far from the planned 300/300/300/300 split (measured: 455 / 434 / 396 / 173). |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym errors, or wrong case/gender claims found. Checked suspect forms such as `направо`, `наліво`, `пішки`, `розі`, `дістатися`, `трамваєм`; all are attested. |
| 3. Pedagogical quality | 7/10 | The module does teach with examples (`Я зараз у парку.`, `Я йду в магазин.`, `Магазин на вулиці Шевченка.`), but too much space goes to English meta-explanation instead of learner-usable Ukrainian modeling, especially `These descriptors provide practical context...` and `A neighborhood is defined by what is accessible from your front door.` |
| 4. Vocabulary coverage | 10/10 | All required plan words appear naturally in prose: `пішки`, `хвилина`, `район`, `центр`, `Вибачте`. All recommended items also appear: `дістатися`, `ідіть`, `їдьте`, `поруч`. |
| 5. Exercise quality | 10/10 | The exercise inventory matches the plan exactly, and the markers follow the relevant teaching sections: `fill-in-directions` after directions, `quiz-locative-accusative` after `Де/Куди`, `fill-in-transport-route` after transport/neighborhood, `match-up-navigation-responses` after the summary. |
| 6. Engagement & tone | 8/10 | The tone is mostly teacherly and grounded, but several lines drift into generic filler, e.g. `Measuring distance through the required mode of transport is the most natural way to explain city geography.` |
| 7. Structural integrity | 10/10 | All H2 headings from the plan are present and ordered correctly; the markdown is clean; the deterministic word count is 1581, so the module is safely above target. |
| 8. Cultural accuracy | 10/10 | The module is anchored in Ukrainian context (`Lviv`, `Площа Ринок`, `Оперний театр`, `Високий замок`) and does not frame Ukrainian through Russian comparison. |
| 9. Dialogue & conversation quality | 8/10 | The commute dialogue is functional and natural (`Спочатку йду на зупинку... Потім іду пішки...`), but the first walking-tour dialogue is still a short prompt chain rather than a fuller exchange with distinct voices. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `> **Туристи:** **В театр.** *(To the theater.)*` / `> **Туристи:** **З замку.** *(From the castle.)*`  
Issue: The plan’s walking-tour dialogue is supposed to surface the actual Lviv landmarks, but the spoken exchange downgrades them to generic nouns. That weakens plan fidelity and the sense of place.  
Fix: Replace the generic replies with named landmarks in the dialogue itself, e.g. `В Оперний театр.` and `З Високого замку.`

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `> **Гід:** **Музей далеко. Їдьте трамваєм до центру.** *(The museum is far. Go by tram to the center.)*`  
Issue: The plan and later grammar/activity focus use `на метро`; switching to `трамваєм` breaks internal cohesion between dialogue, explanation, and exercise focus.  
Fix: Change the line to `Їдьте на метро до центру.`

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `These descriptors provide practical context for anyone trying to navigate an unfamiliar area. Measuring distance through the required mode of transport is the most natural way to explain city geography.`  
Issue: This is filler where the learner needs one more usable model. Right after teaching distance/transport, the module should reinforce with a short Ukrainian pattern, not abstract English commentary.  
Fix: Replace the paragraph with a compact model such as `Парк близько. Ми йдемо пішки.` / `Музей далеко. Їдемо на метро.`

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `This simple model description establishes a home base and identifies the immediate surroundings. The phrase **біля мого дому** (near my home) is a high-frequency chunk for describing a residential area. A neighborhood is defined by what is accessible from your front door.`  
Issue: This section is already over budget, but it spends three sentences on obvious English meta-commentary instead of another reusable pattern. The plan’s section pacing is substantially off balance: `Діалоги` 455 words, `Де і куди разом` 434, `Мій район` 396, `Підсумок` 173, against a planned 300 each.  
Fix: Compress this paragraph into a template-oriented teaching sentence, and add one worked route model to the summary.

## Verdict: REVISE
REVISE — no linguistic errors were found, but there are multiple major plan/pedagogical issues: the landmark dialogue is under-specified, the metro/tram example breaks internal cohesion, and section pacing is badly misbalanced against the 300-word plan.

<fixes>
- find: |-
    > **Гід:** **Де ми зараз?** *(Where are we now?)*
    > **Туристи:** **Ми на площі Ринок.** *(We are at Rynok Square.)*
    > **Гід:** **Куди йдемо далі?** *(Where are we going next?)*
    > **Туристи:** **В театр.** *(To the theater.)*
    > **Гід:** **Звідки ми прийшли?** *(Where did we come from?)*
    > **Туристи:** **З замку.** *(From the castle.)*
  replace: |-
    > **Гід:** **Де ми зараз?** *(Where are we now?)*
    > **Туристка:** **Ми на площі Ринок.** *(We are at Rynok Square.)*
    > **Турист:** **Куди йдемо далі?** *(Where are we going next?)*
    > **Гід:** **В Оперний театр.** *(To the Opera House.)*
    > **Туристка:** **Звідки ми прийшли?** *(Where did we come from?)*
    > **Гід:** **З Високого замку.** *(From the High Castle.)*
- find: |-
    > **Гід:** **Музей далеко. Їдьте трамваєм до центру.** *(The museum is far. Go by tram to the center.)*
  replace: |-
    > **Гід:** **Музей далеко. Їдьте на метро до центру.** *(The museum is far. Go by metro to the center.)*
- find: |-
    These descriptors provide practical context for anyone trying to navigate an unfamiliar area. Measuring distance through the required mode of transport is the most natural way to explain city geography.
  replace: |-
    Use these as short answers first, then add transport if needed: **Парк близько. Ми йдемо пішки.** / **Музей далеко. Їдемо на метро.**
- find: |-
    This simple model description establishes a home base and identifies the immediate surroundings. The phrase **біля мого дому** (near my home) is a high-frequency chunk for describing a residential area. A neighborhood is defined by what is accessible from your front door.
  replace: |-
    This gives you a simple neighborhood template: home base first, then nearby places. The chunk **біля мого дому** helps you add local landmarks immediately.
- insert_after: |-
    Grammatical navigation structures depend on a strict distinction between location and movement. The prepositions **в** and **на** act differently based on context. Pairing them with the locative case answers the static question **Де?** (Where?), while pairing them with the accusative case answers the directional question **Куди?** (Where to?). Transport methods further refine the description, distinguishing between walking (**пішки**), taking a non-declining transport (**на метро**), or riding a standard vehicle (**автобусом**). These patterns let you describe simple routes in Ukrainian.
  content: |-
    Use one full model to connect the patterns:

    *   **Я живу на вулиці Франка.** *(I live on Franko Street.)*
    *   **Біля мого дому є парк.** *(There is a park near my home.)*
    *   **На роботу я їду автобусом до центру, а потім іду пішки п'ять хвилин.** *(I go by bus to the center for work, and then I walk for five minutes.)*
    *   **Мій офіс у центрі міста.** *(My office is in the city center.)*
</fixes>
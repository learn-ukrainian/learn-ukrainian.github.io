## Linguistic Scan
No linguistic errors found.

## Exercise Check
Three exercise markers are present, and they match the three `activity_hints` in the plan:

- `matching-pronoun-ending`
- `fill-in-core-verbs`
- `fill-in-choose-gender`

Placement is mostly correct:
- `matching-pronoun-ending` appears after the grammar explanation it should test.
- The two fill-in markers appear after the Practice section content they should test.

Issue:
- `<!-- INJECT_ACTIVITY: fill-in-core-verbs -->` and `<!-- INJECT_ACTIVITY: fill-in-choose-gender -->` are adjacent immediately before `## Summary`, so practice is back-loaded rather than spread through the module.

No inline DSL exercise blocks were present.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | All four planned sections are present, but the module never cites the plan references `State Standard 2024` or `ULP Season 1, Episodes 26-27`, and the prose expands beyond the plan’s tight A1 framing. |
| 2. Linguistic accuracy | 10/10 | VESUM spot-checks confirmed key forms such as `робив`, `читала`, `дивилися`, `провів`, `провела`, `провели`; no Russian characters (`ы`, `э`, `ё`, `ъ`) were found; no clear Russianisms, Surzhyk, calques, or wrong Ukrainian forms found. |
| 3. Pedagogical quality | 7/10 | The module has a PPP shape, but long English setup delays input: “Monday morning at the office is a universal experience...” and the table row `1st / 2nd / 3rd | він працював | вона працювала | ...` does not actually demonstrate the cross-person point it explains. |
| 4. Vocabulary coverage | 9/10 | Required/recommended items are integrated naturally: `учора`, `вихідні`, `суботу`, `неділю`, `разом`, `фільм`, `провести`; `робити` is covered through the taught forms `робив/робила`. |
| 5. Exercise quality | 8/10 | All 3 planned markers are present and follow relevant teaching, but `fill-in-core-verbs` and `fill-in-choose-gender` are clustered together immediately before Summary instead of being distributed more evenly. |
| 6. Engagement & tone | 7/10 | The teacher voice is steady, but filler like “universal experience” and “highly predictable and mechanical pattern” adds explanation without much instructional value. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly; word count is 1637, above the 1200 target; markdown is clean. |
| 8. Cultural accuracy | 9/10 | No Russia-centric framing or cultural inaccuracies; workplace/weekend situations are plausible and neutral. |
| 9. Dialogue & conversation quality | 8/10 | Named speakers and a real weekend-sharing situation work well, but the section loses conversational momentum because English exposition surrounds the dialogues instead of letting them carry more of the teaching load. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `The Ukrainian past tense, known as **минулий** час (past tense), follows a highly predictable and mechanical pattern. Grade 3 and Grade 4 school textbooks in Ukraine teach this concept by focusing on the base form of the verb.`  
Issue: The module mentions Grade 3/4 textbooks, but it does not cite the plan’s other required references (`State Standard 2024` and `ULP Season 1, Episodes 26-27`).  
Fix: Revise this paragraph so it naturally references the State Standard and Ukrainian Lessons Podcast alongside the textbook framing.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Monday morning at the office is a universal experience. Coworkers gather around the coffee machine and share stories about their time away from work. To participate in these everyday conversations, you must be able to talk about completed actions. You need to use the past tense.`  
Issue: The section spends too long on generic English setup before giving the learner Ukrainian input. That weakens the PPP flow and pads the section with low-value exposition.  
Fix: Compress this opening to 1-2 sentences that set the scene and point the learner straight to the dialogue.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `| 1st / 2nd / 3rd | **він працював** | **вона працювала** | **воно працювало** | **вони працювали** |`  
Issue: The row label says `1st / 2nd / 3rd`, but every example in the row is third person. That muddles the lesson’s key point that past tense does not change by person.  
Fix: Replace the row with examples that explicitly show the same form across persons, e.g. `я / ти / він працював`, `я / ти / вона працювала`, `ми / ви / вони працювали`.

[EXERCISE QUALITY] [SEVERITY: minor]  
Location: `<!-- INJECT_ACTIVITY: fill-in-core-verbs -->` and `<!-- INJECT_ACTIVITY: fill-in-choose-gender -->`  
Issue: The last two exercise markers are adjacent immediately before the Summary, so practice is back-loaded instead of being spaced through the Practice section.  
Fix: Move `fill-in-core-verbs` earlier, right after the core verb examples, and leave `fill-in-choose-gender` later.

## Verdict: REVISE
The module is linguistically clean, but it has clear fixable quality issues: missing plan-reference integration, padded English exposition, a misleading person/gender table, and back-loaded exercise placement. That fails the PASS gate because there are identified issues and multiple dimensions fall below 9.

<fixes>
- find: |
    Monday morning at the office is a universal experience. Coworkers gather around the coffee machine and share stories about their time away from work. To participate in these everyday conversations, you must be able to talk about completed actions. You need to use the past tense. When Ukrainians discuss their weekend activities, the endings of their action words reveal important grammatical information. The speakers in the conversation below are Ivan and Mariia.
  replace: |
    Monday morning at work is a common time to talk about the weekend. Listen for the past-tense endings in the dialogue below. The speakers are Ivan and Mariia.

- find: |
    The Ukrainian past tense, known as **минулий** час (past tense), follows a highly predictable and mechanical pattern. Grade 3 and Grade 4 school textbooks in Ukraine teach this concept by focusing on the base form of the verb. To form the past tense, you start with the infinitive form of the verb. The infinitive is the dictionary form that always ends in **-ти**, such as **читати** (to read) or **працювати** (to work). For many common verbs at this level, you can remove this **-ти** ending to find the stem and then add a past-tense ending. This is a useful beginner pattern, but not every Ukrainian verb forms the past tense this way.
  replace: |
    In Ukrainian, the past tense is **минулий** час (past tense). Grade 3 and Grade 4 school textbooks teach a clear beginner pattern: for many common verbs at this level, you remove **-ти** and add a past-tense ending. This matches the State Standard 2024 focus on gender agreement in past-tense forms, and you can hear the same pattern in Ukrainian Lessons Podcast Season 1, Episodes 26-27. The infinitive is the dictionary form, such as **читати** (to read) or **працювати** (to work). This is a useful beginner pattern, but not every Ukrainian verb forms the past tense this way.

- find: |
    | Особа (Person) | Чоловічий рід (Masculine) | Жіночий рід (Feminine) | Середній рід (Neuter) | Множина (Plural) |
    | --- | --- | --- | --- | --- |
    | 1st / 2nd / 3rd | **він працював** | **вона працювала** | **воно працювало** | **вони працювали** |
  replace: |
    | Особа (Person) | Чоловічий рід (Masculine) | Жіночий рід (Feminine) | Середній рід (Neuter) | Множина (Plural) |
    | --- | --- | --- | --- | --- |
    | 1st / 2nd / 3rd | **я / ти / він працював** | **я / ти / вона працювала** | **воно працювало** | **ми / ви / вони працювали** |

- find: |
    *   **Учора я читав цікаву книжку.** (Yesterday I read an interesting book.)
    *   **Вона працювала в офісі.** (She worked in the office.)
    *   **Ми гуляли в парку.** (We walked in the park.)
    *   **Вони готували вечерю разом.** (They cooked dinner together.)
    *   **Тарас дивився фільм минулого тижня.** (Taras watched a film last week.)

    Notice how the plural form **-ли** is used for **ми** (we) and **вони** (they), regardless of the gender mix of the group.
  replace: |
    *   **Учора я читав цікаву книжку.** (Yesterday I read an interesting book.)
    *   **Вона працювала в офісі.** (She worked in the office.)
    *   **Ми гуляли в парку.** (We walked in the park.)
    *   **Вони готували вечерю разом.** (They cooked dinner together.)
    *   **Тарас дивився фільм минулого тижня.** (Taras watched a film last week.)

    <!-- INJECT_ACTIVITY: fill-in-core-verbs -->

    Notice how the plural form **-ли** is used for **ми** (we) and **вони** (they), regardless of the gender mix of the group.

- find: |
    <!-- INJECT_ACTIVITY: fill-in-core-verbs -->
    <!-- INJECT_ACTIVITY: fill-in-choose-gender -->
  replace: |
    <!-- INJECT_ACTIVITY: fill-in-choose-gender -->
</fixes>
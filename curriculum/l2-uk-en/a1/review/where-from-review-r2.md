## Linguistic Scan
- Factually wrong grammar explanation in `## Звідки? (Where From?)`: “The variant **із** helps with pronunciation before certain letters, like **із Торонто**.” This teaches a false letter-based rule. [Правопис 2019 §25](https://2019.pravopys.net/sections/25/) treats `із/зі` as milozvuchnist variants used around harder consonant combinations, not a simple “before certain letters” rule.

## Exercise Check
4/4 planned activity markers are present: `fill-in-where-from`, `group-sort-location-trio`, `fill-in-contrast-location-origin`, `quiz-preposition-choice`.

All markers appear after the relevant teaching:
- `fill-in-where-from` and `group-sort-location-trio` come after `## Звідки?`
- `fill-in-contrast-location-origin` comes after `## Країни і міста`
- `quiz-preposition-choice` comes after `## Підсумок — Summary`

No inline DSL exercises are shown here, so I cannot audit distractor logic or answer-key balance. Marker placement is sound. The only upstream gap is content coverage: I searched the prose and `З якого міста` appears 0 times, even though the plan explicitly called for that question pattern.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module covers the location trio, countries/cities, nationality, and current-location-vs-origin contrast, but the plan explicitly included `Also: З якого міста? З Торонто, з Токіо, з Берліна.` The prose never models `З якого міста`. |
| 2. Linguistic accuracy | 7/10 | Ukrainian examples are mostly clean, but the rule paragraph says: “The variant **із** helps with pronunciation before certain letters, like **із Торонто**.” That is an inaccurate grammar explanation. |
| 3. Pedagogical quality | 8/10 | The flow is broadly PPP: dialogue first, then pattern explanation, then practice markers. But the euphony explanation is overconfident and teaches a shaky rule instead of safe A1 chunk-memorization. |
| 4. Vocabulary coverage | 10/10 | All required plan vocabulary appears naturally in prose: `звідки`, `з/із/зі`, `Україна`, `Київ`, `Львів`, `Канада`; recommended items like `Одеса`, `Харків`, `США`, `Англія`, `Німеччина`, `Польща`, `додому` are also included. |
| 5. Exercise quality | 9/10 | All four planned activities have matching markers and are placed after the relevant teaching sections. With marker-only output, exercise logic itself is not visible, so full distractor auditing is not possible. |
| 6. Engagement & tone | 9/10 | The teacher voice is warm and classroom-appropriate: “Let us listen...”, “You have likely noticed...”. It avoids gamified/corporate language. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and in order. The pipeline word count is 1406, which is above the 1200 target. No stray tags beyond expected activity markers. |
| 8. Cultural accuracy | 9/10 | The module stays Ukrainian-centered, uses Kyiv and Ukrainian city examples, and avoids Russian-centric comparison framing. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues use named speakers and plausible situations. Dialogue 2 in particular cleanly contrasts `звідки` and `куди` in a natural exchange. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## Звідки? (Where From?)` — “The variant **із** helps with pronunciation before certain letters, like **із Торонто**.”  
Issue: This teaches a false rule. `із/зі` are not selected by a simple “certain letters” rule; [Правопис 2019 §25](https://2019.pravopys.net/sections/25/) frames them as milozvuchnist variants used around harder consonant combinations and for smoother pronunciation.  
Fix: Replace the paragraph with a safer A1 explanation that tells learners to memorize natural chunks instead of inferring a wrong letter-based rule.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Діалоги (Dialogues)` — first dialogue models `Звідки ти?` and answers with city names, but `З якого міста` does not appear anywhere in the module.  
Issue: The plan’s dialogue situation explicitly required the city-origin question pattern: `З якого міста? З Торонто, з Токіо, з Берліна.` The content answers with cities but never teaches the question itself.  
Fix: Add `З якого міста?` directly into Dialogue 1 so the city-question pattern is explicitly modeled before practice.

## Verdict: REVISE
The module is structurally solid and covers most of the plan well, but it has one critical grammar-teaching error and one clear missed plan point. That fails both the severity gate and the score gate for PASS.

<fixes>
- find: |-
    You have likely noticed that the preposition changes its shape. Ukrainian uses euphony rules to make speech flow smoothly and avoid awkward clusters of sounds. The basic form **з** is used before most vowels and simple consonants, as in **з Канади** or **з України**. The variant **із** helps with pronunciation before certain letters, like **із Торонто**. Finally, we use **зі** before difficult consonant clusters or specific tricky sounds, such as **зі Львова**, **зі школи**, and **зі США**.
  replace: |-
    You have likely noticed that the preposition changes its shape. Ukrainian uses euphony rules to make speech flow smoothly and avoid awkward clusters of sounds. The basic form **з** is common before vowels and many consonants, as in **з Канади** or **з України**. The variants **із** and **зі** are chosen for smoother pronunciation around harder consonant combinations. In this module, memorize the natural chunks **із Торонто**, **зі Львова**, **зі школи**, and **зі США**.
- find: |-
    > **Олег:** Дуже приємно, Марк. **Звідки ти?** *(Very nice to meet you, Mark. Where are you from?)*
    > **Марк:** Я **з Канади** (from Canada), **із Торонто**. А ти? *(I am from Canada, from Toronto. And you?)*
  replace: |-
    > **Олег:** Дуже приємно, Марк. **Звідки ти? З якого міста?** *(Very nice to meet you, Mark. Where are you from? Which city are you from?)*
    > **Марк:** Я **з Канади** (from Canada), **із Торонто**. А ти? *(I am from Canada, from Toronto. And you?)*
</fixes>
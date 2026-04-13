## Linguistic Scan
No linguistic errors found. Local verification also found no forbidden Russian characters (`ы`, `э`, `ё`, `ъ`) in the Ukrainian text.

## Exercise Check
The module has 4 exercise markers, which matches the 4 `activity_hints` in the plan. The markers are placed after the relevant teaching blocks: `fill-in-directions` after directions language, `quiz-locative-accusative` after the `де/куди` contrast, `fill-in-transport-route` after transport/neighborhood language, and `match-up-navigation-responses` after the summary. No placement/alignment problems found from the markers themselves.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned H2 sections are present and ordered correctly, and the module covers neighborhood/daily-route content. The main miss is the plan’s specific walking-tour dialogue with speakers `Гід` and `Туристи`; the opening gives narration plus fragments like `**Де ми?** ... **Куди далі?** ... **Звідки прийшли?**` instead of a fuller named exchange. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, paronym errors, or forbidden Russian characters substantiated. Verified forms such as `направо`, `наліво`, `пішки`, `дістатися`, `їдьте`, `ідіть`, `на розі`, `у центрі міста`, `на околиці` check out in the local tools. |
| 3. Pedagogical quality | 7/10 | The lesson has a workable dialogue → pattern → practice flow, but it spends too much A1 space on abstract English metalanguage, e.g. `Mastering these distinct grammatical cases transforms random city streets into a clear, navigable map.` and `These patterns are the foundation of practical city survival.` Those lines add rhetoric more than usable learner support. |
| 4. Vocabulary coverage | 10/10 | Required plan words all appear in prose: `пішки`, `хвилина`, `район`, `центр`, `вибачте`; recommended `дістатися`, `ідіть`, `їдьте`, `поруч` also appear naturally. |
| 5. Exercise quality | 10/10 | The 4 markers match the 4 planned activity types/foci and are distributed through the module rather than clustered at the end. |
| 6. Engagement & tone | 8/10 | The Lviv / neighborhood framing is concrete, but some phrasing is inflated rather than teacherly, e.g. `safe, accurate guidance` and `practical city survival.` |
| 7. Structural integrity | 10/10 | All planned headings are present, markdown is clean, markers are not dangling, and the pipeline word count is 1574, which is above the 1200 target. |
| 8. Cultural accuracy | 7/10 | The module usefully anchors the lesson in Lviv, but the same section says `Музей далеко. Їдьте на метро до центру.` after setting the scene in Lviv old town. Lviv public transport is tram/trolleybus/bus-based, not metro. Source: [Lviv Public Transport Guide](https://lviv.travel/en/news/gaid-lvivskim-gromadskim-transportom). |
| 9. Dialogue & conversation quality | 8/10 | The street-help and commute dialogues are functional and named, but the signature Lviv tour scene is mostly narrated instead of being played out as a guide/tourist conversation. |

## Findings
[PLAN ADHERENCE / DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: `## Діалоги` opening — `The core navigation questions form a simple cycle. **Де ми?** (Where are we?) — **На площі.** ... **Звідки прийшли?** ...`  
Issue: The plan calls for a walking-tour dialogue with `Гід` and `Туристи` around Lviv landmarks. The module reduces that plan point to narration plus fragments instead of a realized guide/tourist exchange.  
Fix: Replace the fragment block with a short named dialogue.

[PEDAGOGICAL QUALITY / ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `## Діалоги` — `Mastering these distinct grammatical cases transforms random city streets into a clear, navigable map.`; `## Підсумок` — `Combining these elements allows you to give and receive safe, accurate guidance.` / `These patterns are the foundation of practical city survival.`  
Issue: These English lines are abstract and rhetorical; they do not teach a form, chunk, or contrast that helps an A1 learner complete the tasks.  
Fix: Replace them with direct learner-facing wording about asking for/giving simple directions and describing simple routes.

[CULTURAL ACCURACY] [SEVERITY: critical]  
Location: first street-help dialogue — `> **Гід:** **Музей далеко. Їдьте на метро до центру.** *(The museum is far. Go by metro to the center.)*`  
Issue: The lesson frames the setting as Lviv old town, but Lviv has no metro. This is a factual mismatch inside the module’s own cultural frame. Source: [Lviv Public Transport Guide](https://lviv.travel/en/news/gaid-lvivskim-gromadskim-transportom).  
Fix: Change the transport example to `трамваєм`.

## Verdict: REVISE
REVISE because the module contains one critical factual/cultural error (`Lviv` + `metro`) and multiple major quality issues in pedagogy/dialogue realization. The language itself is clean, but the module should not ship unchanged.

<fixes>
- find: |
    The core navigation questions form a simple cycle. **Де ми?** (Where are we?) — **На площі.** (On the square). **Куди далі?** (Where to next?) — **В театр.** (To the theater). **Звідки прийшли?** (Where did we come from?) — **З замку.** (From the castle). Mastering these distinct grammatical cases transforms random city streets into a clear, navigable map.
  replace: |
    A guide can turn that route into a short real exchange:

    > **Гід:** **Де ми зараз?** *(Where are we now?)*
    > **Туристи:** **Ми на площі Ринок.** *(We are at Rynok Square.)*
    > **Гід:** **Куди йдемо далі?** *(Where are we going next?)*
    > **Туристи:** **В театр.** *(To the theater.)*
    > **Гід:** **Звідки ми прийшли?** *(Where did we come from?)*
    > **Туристи:** **З замку.** *(From the castle.)*
- find: |
    > **Гід:** **Музей далеко. Їдьте на метро до центру.** *(The museum is far. Go by metro to the center.)*
  replace: |
    > **Гід:** **Музей далеко. Їдьте трамваєм до центру.** *(The museum is far. Go by tram to the center.)*
- find: |
    Combining these elements allows you to give and receive safe, accurate guidance.
  replace: |
    Combining these elements allows you to ask for and give simple directions.
- find: |
    These patterns are the foundation of practical city survival.
  replace: |
    These patterns let you describe simple routes in Ukrainian.
</fixes>
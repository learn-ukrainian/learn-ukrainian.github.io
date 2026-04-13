## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym errors, or forbidden Russian characters found in the provided Ukrainian text.

Factual grammar error:
- `## В чи на?` — “Countries, regions, and cities ALWAYS take the preposition **в/у**.” This is too absolute. Ukrainian regional names can take `на`; the textbook corpus attests `на Волині`.

## Exercise Check
Markers present: `match-up-nominative-locative`, `fill-in-answer-where`, `quiz-v-or-na`, `quiz-where-is-it`.

Placement is mostly correct:
- `match-up-nominative-locative` and `fill-in-answer-where` come after the locative-form teaching.
- `quiz-v-or-na` and `quiz-where-is-it` come after the `В чи на?` section.
- Marker count matches the four `activity_hints` in the plan.

No exercise-logic error is visible in the module itself because the actual YAML items are not shown here.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The H2 structure matches the plan, but the planned newcomer-neighbor situation “asking a neighbor where to find: аптека, банк, пошта, кафе, лікарня, парк” is not realized in dialogue form; the opening exchange is “Де Олена?... А Тарас?... А діти?... А кішка?” instead. |
| 2. Linguistic accuracy | 6/10 | Most forms are correct, but “Countries, regions, and cities ALWAYS take the preposition **в/у**” is factually wrong; corpus evidence includes `на Волині`. |
| 3. Pedagogical quality | 7/10 | The helper question and core chunks are explained clearly, but the presentation phase spends its first dialogue on family-member locations instead of the module’s target place-finding scenario, reducing immediate practice with the planned place vocabulary. |
| 4. Vocabulary coverage | 9/10 | All required vocabulary appears in prose: “в школі,” “на роботі,” “у банку,” “у/в магазині,” “на вулиці,” “у місті”; recommended items also appear, including “у лікарні,” “у/в кафе,” “на площі,” “на вокзалі,” and “на пошті.” |
| 5. Exercise quality | 9/10 | All four planned activity types have matching markers, and each marker appears after the relevant teaching block. |
| 6. Engagement & tone | 9/10 | The teacher voice is clear and useful, especially in “Can you answer these simple questions in Ukrainian?” The tone stays instructional rather than gimmicky. |
| 7. Structural integrity | 5/10 | Section order is clean, but the pipeline word count is 1124, below the 1200-word target. |
| 8. Cultural accuracy | 8/10 | The module correctly insists on `в Україні` and avoids Russian-centered framing, but the overgeneralization about all “regions” taking `в/у` is culturally and grammatically inaccurate. |
| 9. Dialogue & conversation quality | 7/10 | Named speakers help, but the first exchange is a drill-like Q/A chain rather than a fuller newcomer-neighbor interaction. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## В чи на?` — “Countries, regions, and cities ALWAYS take the preposition **в/у**.”  
Issue: This teaches a false absolute rule. Ukrainian regional names can take `на`; textbook corpus evidence includes `на Волині`.  
Fix: Limit the rule to countries and cities, and add a note that some regional/historical names use `на`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Діалоги (Dialogues)` — “Де Олена?... А Тарас?... А діти?... А кішка?”  
Issue: The plan’s stated newcomer-neighbor situation about finding `аптека, банк, пошта, кафе, лікарня, парк` is missing from the dialogue section, so the target place vocabulary is underused in the presentation phase.  
Fix: Insert a short newcomer-neighbor exchange that answers real `де?` questions with `в аптеці`, `у банку`, `на пошті`, `в парку`, `у лікарні`, and `в кафе`.

[STRUCTURAL INTEGRITY] [SEVERITY: major]  
Location: Pipeline note — `Word count: 1124 words`  
Issue: The module is 76 words below the 1200-word target.  
Fix: Add a short dialogue block in the dialogues section; this also repairs the missing planned scenario.

## Verdict: REVISE
REVISE. The module has a critical factual grammar error, misses a planned dialogue situation, and is below the required word target. Multiple dimensions are below 9, so it does not meet the PASS gate.

<fixes>
- find: |-
    There is a strict rule regarding geographical locations. Countries, regions, and cities ALWAYS take the preposition **в/у**. You say **в Україні** (in Ukraine), **у Києві** (in Kyiv), **у Львові** (in Lviv), and **в Одесі** (in Odesa). Contrast this geographical rule with smaller local spaces like streets and squares, which typically take **на**. You say **на площі** (on the square) or **на Хрещатику** (on Khreshchatyk). The logic is that cities are seen as large, bounded territories (using **в**), while streets are viewed as open pathways or surfaces (using **на**).
  replace: |-
    There is a strong rule regarding countries and cities. Countries and cities normally take the preposition **в/у**. You say **в Україні** (in Ukraine), **у Києві** (in Kyiv), **у Львові** (in Lviv), and **в Одесі** (in Odesa). Contrast this with smaller local spaces like streets and squares, which typically take **на**. You say **на площі** (on the square) or **на Хрещатику** (on Khreshchatyk). Do not extend the **в/у** rule to every geographical name: some regional and historical names use **на**. For this A1 pattern, remember: countries and cities usually use **в/у**, while streets and squares often use **на**.
- insert_after: |-
    The preposition tells us the spatial relationship, and the ending confirms it.
  content: |-

    Here is one more neighborhood exchange that uses the module's target place words as real answers to **де?** questions:

    > **Новий мешканець:** Де я можу купити ліки? *(Where can I buy medicine?)*
    > **Сусід:** В аптеці. Аптека в центрі. *(At the pharmacy. The pharmacy is in the center.)*
    > **Новий мешканець:** А де я можу зняти гроші і відправити лист? *(And where can I withdraw money and send a letter?)*
    > **Сусід:** У банку і на пошті. Банк у центрі, а пошта на площі. *(At the bank and at the post office. The bank is in the center, and the post office is on the square.)*
    > **Новий мешканець:** А де кафе і лікарня? *(And where are the café and hospital?)*
    > **Сусід:** Кафе в парку, а лікарня теж у центрі. *(The café is in the park, and the hospital is also in the center.)*
</fixes>
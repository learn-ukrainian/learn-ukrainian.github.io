## Linguistic Scan
No linguistic errors found.

## Exercise Check
All 4 planned activities have corresponding markers:
- `quiz-question-choice` after `## Що ми знаємо?`
- `group-sort-case-function` and `quiz-euphony-rules` after `## Граматика`
- `fill-in-dialogue-forms` after `## Діалог`

The marker types match the plan’s `activity_hints`, and each appears after the relevant teaching section. No exercise-logic errors are visible from the markers alone. The only placement weakness is slight clustering: two markers sit back-to-back after `## Граматика`, but both still test material just taught there.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | The plan says the reading should show “a tourist navigates Kyiv — asks for directions, takes metro, finds a museum...”; the reading block contains no question/request at all (`?` x0, `Вибачте` x0, `Де` x0 in the quoted reading). Section pacing also drifts far from the plan budgets: approx. 258/200, 205/250, 439/200, 418/300, 74/250. |
| 2. Linguistic accuracy | 10/10 | No confirmed Russianisms, Surzhyk, calques, paronym errors, or Russian letters. Suspect forms such as `направо`, `наліво`, `відеодзвінку`, `метро`, and `дістатися` check out. |
| 3. Pedagogical quality | 6/10 | The module repeatedly uses abstract English framing instead of tight A1 teaching cues: “Real navigation happens in continuous conversation... bustling, vibrant streets of Kyiv” and “The core spatial patterns form the absolute foundation of your navigation skills.” The Ukrainian examples are good, but the exposition is too theory-heavy for a checkpoint review. |
| 4. Vocabulary coverage | 9/10 | Plan vocabulary is covered in prose: `Дерибасівській вулиці`, `Потьомкінські сходи`, `порт`, `пляж`, `музей`, `метро`, `вокзал`, `площа`, transport, and direction words all appear naturally. |
| 5. Exercise quality | 9/10 | Marker count matches the 4 planned activities, marker order is pedagogically sensible, and each marker tests the preceding section’s skill. No visible logic flaw can be confirmed without the downstream generated YAML. |
| 6. Engagement & tone | 6/10 | The voice slips into generic AI filler: “absolute foundation of your navigation skills,” “complete, natural, and highly functional thoughts,” and “urgently need some assistance.” This weakens the teacher persona and adds words without adding learning value. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and in order; markdown is clean; marker count is correct; pipeline word count is 1468, which is above the 1200 target. |
| 8. Cultural accuracy | 10/10 | The module stays grounded in Ukrainian cities and Ukrainian usage, with no colonial framing or factual cultural problems. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue has named speakers, a realistic city-navigation task, and a plausible follow-up destination (`у Львів`, `до станції Вокзальна`). It is functional and usable for A1 review. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Читання` — plan requires “a tourist navigates Kyiv — asks for directions...” but the reading block has no request for directions (`?` x0; `Вибачте` x0; `Де` x0 in the reading text).  
Issue: The reading does not fully cover the planned scenario because the tourist never actually asks for directions.  
Fix: Replace the middle of the reading with a short direction request and reply, e.g. add `Вибачте, де музей?` and a response directing the tourist to the metro/station.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Що ми знаємо?`, `## Читання`, `## Граматика`, `## Діалог`, `## Підсумок`  
Issue: Section budgets drift heavily from the plan: approx. 258/200, 205/250, 439/200, 418/300, 74/250. Grammar and dialogue overrun; the summary is far too short and drops the planned euphony recap.  
Fix: Cut the English lead-ins in Reading/Grammar/Dialogue and expand the summary to restate euphony plus the A1.5 achievement points.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `## Читання` — “Real navigation happens in continuous conversation, not in isolated textbook sentences...” and `## Граматика` — “The core spatial patterns form the absolute foundation of your navigation skills.”  
Issue: The module spends too many words on abstract English framing instead of concise form-meaning-use teaching. For an A1 checkpoint, this is padding rather than instruction.  
Fix: Replace these paragraphs with short prompts that point directly to the target pattern and examples.

[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `## Читання`, `## Граматика`, `## Діалог` — “bustling, vibrant streets of Kyiv,” “absolute foundation of your navigation skills,” “complete, natural, and highly functional thoughts,” “urgently need some assistance.”  
Issue: The tone is inflated and generic instead of sounding like a concrete, helpful teacher.  
Fix: Replace inflated setup language with specific classroom-style prompts and simpler scenario framing.

## Verdict: REVISE
REVISE because there are major findings in plan adherence, pedagogy, and tone, and dimensions 1, 3, and 6 are below 9. The module is structurally sound and linguistically clean, but it needs targeted tightening before shipping.

<fixes>
- find: |-
    Real navigation happens in continuous conversation, not in isolated textbook sentences. Imagine a tourist navigating the bustling, vibrant streets of Kyiv. They need to ask locals for accurate directions, understand the public transit system, locate a specific cultural site, and clearly explain their travel plans. This requires combining all your spatial skills.

    Read the following narrative about a tourist in the city. It combines all the spatial patterns you have learned so far.
  replace: |-
    Read this short route story. Notice how the tourist says where they are from, asks for directions, uses the metro, and finds the museum.

- find: |-
    > **Я дуже хочу їхати в музей.**
    > *(I really want to go to the museum.)*
    >
    > **Але музей стоїть далеко.**
    > *(But the museum stands far away.)*
    >
    > **Тому я йду на метро.**
    > *(Therefore I am walking to the metro.)*
    >
    > **Я їду на станцію Хрещатик.**
    > *(I travel to the Khreshchatyk station.)*
  replace: |-
    > **Я хочу поїхати до музею, тому питаю: «Вибачте, де музей?»**
    > *(I want to go to the museum, so I ask: “Excuse me, where is the museum?”)*
    >
    > **Мені кажуть: «Музей далеко. Ідіть до метро».**
    > *(They tell me: “The museum is far away. Go to the metro.”)*
    >
    > **Тому я йду до метро.**
    > *(So I go to the metro.)*
    >
    > **Я їду до станції Хрещатик.**
    > *(I travel to Khreshchatyk station.)*

- find: |-
    The core spatial patterns form the absolute foundation of your navigation skills. The question **Де?** (Where?) requires the prepositions **в** or **на** followed by the Locative case. You use this exclusively for static locations, telling people exactly where an object or person currently rests.
  replace: |-
    Use **Де?** (Where?) with **в / у** or **на** plus the Locative case for a static location.

- find: |-
    The question **Куди?** (To where?) requires the prepositions **в** or **на** followed by the Accusative case. You use this strictly for movement toward a destination, indicating the endpoint of a physical journey.
  replace: |-
    Use **Куди?** (To where?) with **в / у** or **на** plus the Accusative case for movement toward a destination.

- find: |-
    The question **Звідки?** (From where?) requires the prepositions **з**, **із**, or **зі** followed by the Genitive case. You use this to express the starting point of a movement or a person's geographic origin.
  replace: |-
    Use **Звідки?** (From where?) with **з / із / зі** plus the Genitive case for origin or the starting point of movement.

- find: |-
    Ukrainian speech requires a smooth flow of sounds. The euphony rules ensure that words connect naturally without awkward consonant clusters. You alternate between vowels and consonants using specific sets of prepositions and conjunctions.
  replace: |-
    For euphony, choose the form that sounds smoother in context: **у / в**, **і / й**, **з / із / зі**.

- find: |-
    When discussing your daily commute and transport, you use specific grammatical forms. You use the Instrumental case for the vehicle itself, or you use the preposition **на** with the Locative case for public transit systems.
  replace: |-
    For transport, use the Instrumental for the vehicle itself, or fixed beginner phrases such as **на метро**.

- find: |-
    You also use fixed, unchanging adverbs for simple directions on the street.
  replace: |-
    Use simple adverbs for street directions.

- find: |-
    All these individual elements combine to form complete, natural, and highly functional thoughts.
  replace: |-
    These patterns combine in simple route descriptions.

- find: |-
    Imagine you are visiting Kyiv and you urgently need some assistance. You stop a local resident on the street to ask for clear directions to a famous museum. After you find out about the museum, you also need to figure out how to reach the main train station for your onward journey to the city of Lviv.
  replace: |-
    You are visiting Kyiv. In this dialogue, you ask a local how to get to a museum and then how to reach the train station for Lviv.

- find: |-
    You can now combine the main Places patterns in one situation: say where you are, where you are going, where you are from, how you are traveling, and how to follow simple directions.

    Before moving on, check that you can answer **Де?** with the locative, **Куди?** with the accusative, and **Звідки?** with genitive chunks. In A1.6 you will keep using the accusative, but this time for direct objects in food and shopping situations.
  replace: |-
    You can now navigate simple city situations in Ukrainian: say where you are, where you are going, where you are from, how you are traveling, and how to follow simple directions.

    Before moving on, check that you can answer **Де?** with the locative, **Куди?** with the accusative, and **Звідки?** with genitive chunks. Check your euphony too: can you choose **у / в**, **і / й**, and **з / із / зі** so the phrase sounds smooth?

    In A1.6 you will keep using the accusative, but this time for direct objects in food and shopping situations.
</fixes>
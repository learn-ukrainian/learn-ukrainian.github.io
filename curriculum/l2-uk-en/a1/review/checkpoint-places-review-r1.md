## Linguistic Scan
- [CRITICAL] Factually wrong grammar note: `standard Ukrainian style guides often recommend simply using the word **метро** on its own ... or **в метро** to sound more authentic.` Local textbook search teaches transport as `метро — на метро`; `в метро` is locative “in the metro,” not the preferred beginner transport phrase here.
- No Russianisms, Surzhyk, paronym errors, or forbidden Russian letters were confirmed in the Ukrainian example sentences.

## Exercise Check
4/4 planned markers are present. `quiz-question-choice` follows the self-check section, `group-sort-case-function` and `quiz-euphony-rules` follow the grammar review, and `fill-in-dialogue-forms` follows the dialogue. Marker type/focus alignment is good, and nothing suggests an exercise-logic failure in the inline content.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 5/10 | All planned H2 sections are present, but the plan’s Odesa checkpoint setup is missing: no `Дерибасівська`, `Потьомкінські`, `порт`, `пляж`, or `сходи`, while the prose instead centers on `Kyiv`. Section pacing is also far off the plan’s compact review budgets: Grammar is 435 words vs planned 200, Dialogue 434 vs 300, Intro 298 vs 200. |
| 2. Linguistic accuracy | 7/10 | Most Ukrainian examples are clean (`Вона живе у Львові.`, `Я родом з України.`), but the note claiming `в метро` is more authentic than `на метро` teaches the wrong usage distinction. |
| 3. Pedagogical quality | 6/10 | There are many examples, but the checkpoint keeps slipping into long English lecture prose: `Notice how this narrative effortlessly switches...` and `You already possess all the grammatical tools needed...` add explanation without much new learning value. |
| 4. Vocabulary coverage | 5/10 | Core city/navigation words are present (`музей`, `вокзал`, `метро`, `площа`), but the plan’s motivating checkpoint vocabulary tied to Odesa landmarks is not used in the prose. |
| 5. Exercise quality | 9/10 | Marker count matches the 4 `activity_hints`, and placement is sensible: question-choice after the review triad, case sort and euphony quiz after grammar, fill-in after dialogue. |
| 6. Engagement & tone | 5/10 | Tone drifts into inflated, generic phrasing: `You already possess all the grammatical tools needed`, `You have acquired several powerful technical tools`, `You have the momentum...`. That reads like AI filler, not a focused teacher voice. |
| 7. Structural integrity | 7/10 | The module has all required H2 headings and exceeds the 1200-word minimum, but it ends with a stray code fence: ````` after the final paragraph. |
| 8. Cultural accuracy | 8/10 | Nothing is overtly inaccurate or Russocentric, but the planned Odesa local-color checkpoint is largely absent despite being the module’s stated motivating situation. |
| 9. Dialogue & conversation quality | 9/10 | The dialogue is speaker-labeled, multi-turn, and based on a real navigation task (`Де тут музей? ... Де вокзал?`). It is functional and usable. |

## Findings
[PLAN ADHERENCE / VOCABULARY COVERAGE] [SEVERITY: major]  
Location: `To prove you are ready, read this short introduction out loud:` block with `Мене звати Анна... Я живу в Києві...`  
Issue: The module skips the plan’s motivating checkpoint scene: a video-call walk through Odesa with `Дерибасівська вулиця`, `Потьомкінські сходи`, `порт`, and `пляж`. Those landmark words never appear in the prose.  
Fix: Replace the read-aloud mini-scene with a short Odesa/video-call vignette that uses the missing landmark vocabulary.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `You might hear people say **на метро** ... or **в метро** to sound more authentic.`  
Issue: This teaches the wrong distinction. For transport, `на метро` is standard/common and explicitly taught that way in textbook material; `в метро` normally means physical location inside the metro.  
Fix: Rewrite the note so it presents `на метро` as the normal learner phrase and explains that `в метро` means “in the metro.”

[PEDAGOGICAL QUALITY + ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `You have reached the final stage...`, `Notice how this narrative effortlessly switches...`, `You already possess all the grammatical tools needed...`, `You have acquired several powerful technical tools...`  
Issue: The checkpoint is padded with generic English meta-commentary and AI-sounding encouragement instead of compact review teaching. That weakens PPP pacing and pushes sections far beyond their planned budgets.  
Fix: Trim the English exposition and replace it with shorter teacher-facing summaries tied directly to the target patterns.

[STRUCTURAL INTEGRITY] [SEVERITY: minor]  
Location: end of module after `You have the momentum, and you are ready for the next step.`  
Issue: A stray closing code fence ````` remains in the content.  
Fix: Remove the stray code fence.

## Verdict: REVISE
REVISE. The module has one critical factual/linguistic error (`в метро` note), plus major plan and pedagogy problems: the Odesa checkpoint vocabulary/setup is missing, the prose is over-expanded with generic English filler, and there is a formatting artifact at the end.

<fixes>
- find: |
    You have reached the final stage of the Places phase. Navigating a Ukrainian city requires you to combine several different skills into one smooth conversation. You must know how to state your current location, your destination, your point of origin, and your mode of transport. This checkpoint brings all those pieces together.

    The Ukrainian spatial system relies on a solid triad of questions. Understanding these three questions unlocks basic urban mobility. The static location answers the question **Де?** (Where?). The dynamic destination answers the question **Куди?** (To where?). Finally, the point of origin answers the question **Звідки?** (From where?). Ukrainians naturally categorize every movement into one of these three buckets.
  replace: |
    This checkpoint reviews the key Places patterns from M28-M34. Keep three questions active as you read: **Де?** for location, **Куди?** for direction, and **Звідки?** for origin.

    You will combine euphony, city vocabulary, transport, directions, and the locative / accusative / genitive chunks you already know.
- find: |
    > **Мене звати Анна.**
    > *(My name is Anna.)*
    >
    > **Я живу в Києві.**
    > *(I live in Kyiv.)*
    >
    > **Я щодня їду на роботу.**
    > *(I travel to work every day.)*
    >
    > **Я їду на метро.**
    > *(I travel by metro.)*
  replace: |
    > **Привіт! Я зараз в Одесі, на Дерибасівській вулиці.**
    > *(Hi! I am in Odesa now, on Deribasivska Street.)*
    >
    > **Я на відеодзвінку з другом.**
    > *(I am on a video call with a friend.)*
    >
    > **Потьомкінські сходи недалеко, а порт унизу.**
    > *(The Potemkin Stairs are nearby, and the port is below.)*
    >
    > **Потім я йду на пляж.**
    > *(Then I am going to the beach.)*
- find: |
    Notice how this narrative effortlessly switches between different spatial concepts to tell a complete story. The tourist starts by answering the question of origin with **з Канади** (from Canada). Then, they state their current static location using **у центрі Києва** (in the center of Kyiv). Next, they switch to a dynamic destination with **в музей** (to the museum). They describe their route using transport vocabulary and basic directions like **прямо** (straight) and **направо** (to the right). Finally, they confirm the static location of their destination with **на великій площі** (on the large square). You already possess all the grammatical tools needed to understand and construct a detailed story exactly like this one.
  replace: |
    This reading brings the checkpoint patterns together in one route: **з Канади** shows origin, **у центрі Києва** shows location, **в музей** shows direction, and **на метро / прямо / направо** describe the way.
- find: |
    :::note
    You might hear people say **на метро** (by metro) very often in casual speech. While this is widely understood, standard Ukrainian style guides often recommend simply using the word **метро** on its own (as an instrumental form) or **в метро** to sound more authentic. However, **на метро** remains extremely common in everyday city navigation.
    :::
  replace: |
    :::note
    For transport, **на метро** is a normal and widely taught beginner phrase. You may also hear bare **метро** in context because the noun is indeclinable, but **в метро** usually means “in the metro,” not “by metro.”
    :::
- find: |
    You can now successfully navigate the bustling streets of a Ukrainian city. You have built a solid grammatical foundation for basic urban survival. You know exactly how to ask locals for directions, understand the specific routes people give you, and explain your own daily movements. You can confidently state where you are originally from and where you currently intend to go. This means you can handle the most crucial interactions required of any traveler or new resident.

    You have acquired several powerful technical tools during this phase. You know the euphony rules that make your pronunciation sound natural, fluid, and connected. You know how to use the Locative case to answer the question **Де?** (Where?) for static locations. You know how to use the Accusative case to answer the question **Куди?** (To where?) for dynamic movement toward a target. You also know how to use Genitive chunks to answer the question **Звідки?** (From where?). These tools allow you to form precise, accurate sentences without second-guessing your preposition choices.

    The next phase of your learning journey will build directly on these exact skills. In the upcoming Food and Shopping modules, you will take the Accusative case, which you currently use only for physical destinations, and dramatically expand its function. You will learn to use the Accusative case for direct objects, allowing you to successfully order a coffee, buy a train ticket, or purchase fresh groceries at the market. Understanding how to direct your movement was the first step; soon, you will direct your actions toward objects. You have the momentum, and you are ready for the next step.
    ```
  replace: |
    You can now combine the main Places patterns in one situation: say where you are, where you are going, where you are from, how you are traveling, and how to follow simple directions.

    Before moving on, check that you can answer **Де?** with the locative, **Куди?** with the accusative, and **Звідки?** with genitive chunks. In A1.6 you will keep using the accusative, but this time for direct objects in food and shopping situations.
</fixes>
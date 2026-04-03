## Linguistic Scan
Errors found:
1. "де покласти їх" — uses the location question word "де" instead of the directional "куди" for the verb "покласти". Additionally, placing the pronoun "їх" at the absolute end of the sentence is unnatural phrasing in Ukrainian.

## Exercise Check
- `activity-1` is placed correctly after the Imperative verbs explanation.
- `activity-2` and `activity-3` are placed back-to-back with no intervening text. This is a structural error.
- `activity-4` is placed correctly after Holiday greetings.
- The activity focuses match the plan's `activity_hints`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The module uses the school fair scenario from `dialogue_situations` for the `Діалог` section instead of the specific holiday gathering dialogue in the `content_outline`. However, it successfully covers all required pedagogical points. |
| 2. Linguistic accuracy | 7/10 | Uses the colloquial/Surzhyk "де покласти їх" instead of "куди їх покласти" or a natural "де" phrasing. The rest of the Ukrainian text is very accurate and natural. |
| 3. Pedagogical quality | 7/10 | CRITICAL ERROR: The grammar section incorrectly classifies "**бо**" and "**тому́ що**" as coordinating conjunctions. In Ukrainian grammar, they are subordinating conjunctions of cause (підрядні сполучники причини). |
| 4. Vocabulary coverage | 10/10 | All required A1.7 vocabulary elements (holidays, greetings, conjunctions) are integrated naturally. |
| 5. Exercise quality | 8/10 | Markers `activity-2` and `activity-3` are placed back-to-back without intervening text. |
| 6. Engagement & tone | 8/10 | Contains gamified meta-commentary ("You have five communication tools now", "That is what A1.7 communication looks like.", "You have worked hard through this checkpoint phase"). |
| 7. Structural integrity | 9/10 | Clean markdown structure. Note: The prose contains hardcoded stress marks which are usually handled by a downstream deterministic tool (not penalized per instructions, but noted). |
| 8. Cultural accuracy | 10/10 | Natural representation of holiday greetings (кутя, колядки) and school fair volunteering. |
| 9. Dialogue & conversation quality | 9/10 | The dialogues are realistic, multi-turn, and effectively demonstrate the target grammar in action. |

## Findings
[2. Linguistic accuracy] [Major]
Location: `— Олена: Добре, принесу! Скажи, де покласти їх.`
Issue: Uses location "де" instead of directional "куди" for the verb "покласти". Placing the pronoun "їх" at the end is also unnatural.
Fix: Change to "Скажи, де вони мають бути." This maintains the "де" subordinating clause practice while being grammatically natural.

[3. Pedagogical quality] [Critical]
Location: `Conjunctions connect your thoughts. Coordinating conjunctions link equal parts: ... - **бо** (because: Принеси кутю, бо я не вмію варити.) - **тому що** ...`
Issue: Incorrectly classifies "бо" and "тому що" as coordinating conjunctions. They are subordinating conjunctions of cause.
Fix: Move "бо" and "тому що" into the subordinating conjunctions section and update the transition text to properly separate `activity-2` and `activity-3`.

[5. Exercise quality] [Major]
Location: `<!-- INJECT_ACTIVITY: activity-2 -->\n\n<!-- INJECT_ACTIVITY: activity-3 -->`
Issue: Exercise markers are placed back-to-back.
Fix: Restructure the grammar section to separate the subordinating conjunctions block into two parts, placing `activity-2` before the "що/де/коли" group, and `activity-3` after it.

[6. Engagement & tone] [Minor]
Location: `You have five communication tools now — let's see how well they work together.` and `That is what A1.7 communication looks like.`
Issue: Gamified language and meta-commentary breaking immersion.
Fix: Replace with natural transitions ("Let's see how these skills work together", "This is how these skills work in real conversations").

[2. Linguistic accuracy] [Major]
Location: `three coordinating conjunctions, and three subordinating clauses.`
Issue: Because the original text incorrectly classified "бо" as coordinating, the instruction asks the student to find 3 subordinating clauses. With the grammar corrected, there are actually 5 subordinating clauses in the dialogue ("бо" x2, "де" x2, "що").
Fix: Update the target count to "five subordinating clauses" to match the corrected grammatical reality of the text.

## Verdict: REVISE
The module contains a critical grammatical classification error regarding conjunctions, a linguistic calque, and back-to-back exercise markers. Applying the exact fixes below will resolve these issues and make the module ready for publishing.

<fixes>
- find: |
    Conjunctions connect your thoughts. Coordinating conjunctions link equal parts:
    - **і** / **та** (and — adds)
    - **а** (and/but — contrasts: **Олена йде, а Тарас залиша́ється.** - Olena goes, but Taras stays.)
    - **але** (but — contradicts: **Я хо́чу прийти́, але я хво́рий.** - I want to come, but I am sick.)
    - **бо** (because: **Принеси кутю, бо я не вмі́ю вари́ти.** - Bring kutia, because I don't know how to cook.)
    - **тому́ що** (because: **Я йду, тому́ що вже пі́зно.** - I am going, because it is already late.)

    Subordinating conjunctions link a dependent clause to a main clause, and always require a comma before them:
    - **що** (**Я знаю, що ти тут.** - I know that you are here.)
    - **де** (**Скажи, де ти.** - Tell me where you are.)
    - **коли** (**Я не знаю, коли ти вільний.** - I don't know when you are free.)

    <!-- INJECT_ACTIVITY: activity-2 -->

    <!-- INJECT_ACTIVITY: activity-3 -->
  replace: |
    Conjunctions connect your thoughts. Coordinating conjunctions link equal parts:
    - **і** / **та** (and — adds)
    - **а** (and/but — contrasts: **Олена йде, а Тарас залиша́ється.** - Olena goes, but Taras stays.)
    - **але** (but — contradicts: **Я хо́чу прийти́, але я хво́рий.** - I want to come, but I am sick.)

    Subordinating conjunctions link a dependent clause to a main clause, and always require a comma before them:
    - **бо** (because: **Принеси кутю, бо я не вмі́ю вари́ти.** - Bring kutia, because I don't know how to cook.)
    - **тому́ що** (because: **Я йду, тому́ що вже пі́зно.** - I am going, because it is already late.)

    <!-- INJECT_ACTIVITY: activity-2 -->

    Other subordinating conjunctions help build complex sentences:
    - **що** (**Я знаю, що ти тут.** - I know that you are here.)
    - **де** (**Скажи, де ти.** - Tell me where you are.)
    - **коли** (**Я не знаю, коли ти вільний.** - I don't know when you are free.)

    <!-- INJECT_ACTIVITY: activity-3 -->
- find: "— Олена: Добре, принесу! Скажи, де покласти їх."
  replace: "— Олена: Добре, принесу! Скажи, де вони мають бути."
- find: "You have five communication tools now — let's see how well they work together. Here are five questions to check your knowledge from this phase:"
  replace: "Let's see how these skills work together. Here are five questions to check your knowledge from this phase:"
- find: "These five skills work together. In the reading passage below, you will see Olena use all of them in one short phone call — she addresses Taras by name, asks him to bring something, explains why, links her thoughts into longer sentences, and wishes him a happy holiday. That is what A1.7 communication looks like."
  replace: "These five skills work together. In the reading passage below, you will see Olena use all of them in one short phone call — she addresses Taras by name, asks him to bring something, explains why, links her thoughts into longer sentences, and wishes him a happy holiday. This is how these skills work in real conversations."
- find: "You have worked hard through this checkpoint phase. Here are the concrete communication skills you have practised:"
  replace: "Here are the communication skills you have practised in this module:"
- find: "You should find at least two vocatives, three imperatives, three coordinating conjunctions, and three subordinating clauses. This is exactly what natural A1.7 Ukrainian looks like in action."
  replace: "You should find at least two vocatives, three imperatives, three coordinating conjunctions, and five subordinating clauses. This is how natural Ukrainian looks in action."
</fixes>

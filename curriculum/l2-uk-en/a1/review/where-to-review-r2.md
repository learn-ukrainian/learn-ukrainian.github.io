## Linguistic Scan
- Factually wrong grammar claim in the Dialogue 2 explanation: `When traveling to a city, you must use the verb **їхати** (to go by transport) combined with the preposition **в** or **у** and the name of the city.` This is too absolute. `їхати` is specifically movement by transport, but city destinations are not restricted to that verb.

## Exercise Check
- 4 exercise markers are present, matching the 4 `activity_hints` in the plan.
- Placement is correct: `fill-in-accusative` follows the accusative explanation; `quiz-de-or-kudy` and `group-sort-de-kudy` follow the `Де?` vs `Куди?` contrast; `quiz-yty-or-ikhaty` follows the `йти` vs `їхати` explanation.
- The markers are distributed through the teaching sequence rather than dumped into the summary.
- No inline DSL exercise blocks appear here, so there is no answer logic to audit in the prose itself.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All planned H2 sections are present and in order. The prose covers the required contrasts `Де? — Я в банку.` / `Куди? — Я йду в банк.`, the accusative endings `школа → у школу`, `робота → на роботу`, and the motion-verb contrast `Я йду в магазин.` / `Я їду на вокзал.` The ULP Episode 18 reference is integrated in the opening. |
| 2. Linguistic accuracy | 8/10 | The Ukrainian examples are clean, but the explanation `When traveling to a city, you must use the verb **їхати**...` teaches an overgeneralized rule about Ukrainian motion verbs. |
| 3. Pedagogical quality | 7/10 | The module has a solid PPP skeleton, but some explanations are too theory-heavy before examples, especially `In Ukrainian primary schools, Grade 4 students learn...` and `To navigate the Ukrainian language successfully, you must clearly map out...` Both delay the learner-facing rule with long English exposition. |
| 4. Vocabulary coverage | 10/10 | Required vocabulary appears naturally in context: `куди`, `йти`, `їхати`, `у школу`, `на роботу`, `у банк`. Recommended words also appear in prose: `магазин`, `бібліотека`, `ресторан`, `Одеса`, `повертатися додому`. |
| 5. Exercise quality | 10/10 | The marker set matches the plan exactly, and each marker comes after the concept it is supposed to test. The sequence from form explanation to `de/kudy` contrast to motion verbs is coherent. |
| 6. Engagement & tone | 7/10 | Several lines are padded with inflated wording instead of teaching content, for example `This is a highly visible, high-frequency grammatical signal that native speakers expect to hear in daily conversation.` That adds length without adding usable A1 knowledge. |
| 7. Structural integrity | 10/10 | The structure is clean, all planned H2 headings are present, the marker comments are intact, and the deterministic pipeline word count is 1450, which is above the 1200 target. |
| 8. Cultural accuracy | 9/10 | The module stays Ukrainian-centered and avoids Russian-comparison framing. The errands/public-transport note is plausible and non-exoticizing, though broad. |
| 9. Dialogue & conversation quality | 9/10 | The dialogues use named speakers, clear real-life settings, and multi-turn exchanges such as the Saturday errand split-up and weekend travel planning. They read naturally enough for A1 input. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `This second conversation focuses on cities as destinations. When traveling to a city, you must use the verb **їхати** (to go by transport) combined with the preposition **в** or **у** and the name of the city.`  
Issue: This teaches an absolute rule that is not true. `їхати` is a transport verb, but city destinations are not limited to `їхати`.  
Fix: Rephrase it so the statement is about this dialogue’s example, not a universal rule.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `In Ukrainian primary schools, Grade 4 students learn to identify cases using specific helper words and questions... This grammatical structure perfectly answers the question **Куди?**.`  
Issue: The explanation spends too long in English meta-theory before giving the learner a concise operational rule.  
Fix: Compress the paragraph and move the usable rule to the front.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `To navigate the Ukrainian language successfully, you must clearly map out the key question pair in your mind before speaking... The table below illustrates this crucial split.`  
Issue: This is another overlong English setup for a very simple A1 contrast.  
Fix: Replace it with a short rule-first introduction directly tied to the table.

[ENGAGEMENT & TONE] [SEVERITY: major]  
Location: `This is a highly visible, high-frequency grammatical signal that native speakers expect to hear in daily conversation.`  
Issue: Inflated filler increases word count without teaching anything new.  
Fix: Replace it with plain learner-facing language.

## Verdict: REVISE
REVISE because the module contains one critical factual overstatement about Ukrainian motion verbs and two major prose-quality problems that weaken clarity. Structure, vocabulary coverage, and exercise placement are strong, but the explanation needs tightening before release.

<fixes>
- find: 'This second conversation focuses on cities as destinations. When traveling to a city, you must use the verb **їхати** (to go by transport) combined with the preposition **в** or **у** and the name of the city. Notice the subtle morphological change for Odesa: the nominative **Одеса** becomes the accusative **в Одесу** (to Odesa). However, Lviv experiences no change at all: **Львів** remains **у Львів**. This illustrates how the accusative case affects different types of nouns differently.'
  replace: 'This second conversation focuses on cities as destinations. In this dialogue, the speakers use the verb **їхати** (to go by transport) with the preposition **в** or **у** and the name of the city. Notice the morphological change for Odesa: the nominative **Одеса** becomes the accusative **в Одесу** (to Odesa). However, **Львів** shows no visible change in form: **у Львів**. This illustrates how the accusative case affects different types of nouns differently.'
- find: 'In Ukrainian primary schools, Grade 4 students learn to identify cases using specific helper words and questions. For the accusative case (**Знахідний відмінок**), the mental helper phrase is **бачу** (I see), and the core questions are **кого?** (whom?) and **що?** (what?). This helps native speakers remember that the accusative case typically marks the direct object of an action. However, when dealing with geography and movement, the accusative case takes on an entirely new role. To express direction—specifically, physical motion toward a destination—we use the prepositions **в/у** or **на** followed directly by a noun in the accusative case. This grammatical structure perfectly answers the question **Куди?**.'
  replace: 'In Ukrainian primary schools, Grade 4 students learn to identify cases with helper words and questions. For the accusative case (**Знахідний відмінок**), the helper is **бачу** (I see), and the core questions are **кого?** (whom?) and **що?** (what?). For direction, Ukrainian also uses **в/у** or **на** plus the accusative to answer **Куди?**.'
- find: 'To navigate the Ukrainian language successfully, you must clearly map out the key question pair in your mind before speaking. If you want to know "Where are you?" in a static sense, you ask **Де ти?**, and this question absolutely requires an answer using **в**, **у**, or **на** plus the LOCATIVE case. If you want to know "Where are you going?" in a dynamic sense, you ask **Куди ти йдеш?**, and this requires an answer using **в**, **у**, or **на** plus the ACCUSATIVE case. The table below illustrates this crucial split.'
  replace: 'Keep this question pair simple. **Де ти?** asks about a static location, so the answer uses **в**, **у**, or **на** plus the LOCATIVE case. **Куди ти йдеш?** asks about direction, so the answer uses **в**, **у**, or **на** plus the ACCUSATIVE case. The table below shows the contrast.'
- find: 'This is a highly visible, high-frequency grammatical signal that native speakers expect to hear in daily conversation.'
  replace: 'This is the main ending change learners need at this stage.'
</fixes>
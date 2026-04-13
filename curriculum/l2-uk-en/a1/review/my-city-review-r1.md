## Linguistic Scan
No linguistic errors found.

## Exercise Check
Markers present: `quiz-v-or-na`, `match-up-place-activity`, `fill-in-describe-city`, `quiz-where-to-go`. Count matches the 4 plan hints, and each marker comes after relevant teaching content. Placement issue: the last two markers are adjacent at the end of `Де це?`, so practice is not distributed as evenly as it should be.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The plan requires a Kyiv-neighborhood map dialogue using `бібліотека, музей, площа, озеро, зупинка, церква` plus `біля, поруч з, далеко від`, but Dialogue 2 is only `“Що є біля твого дому? … Біля дому є магазин і кафе.”` |
| 2. Linguistic accuracy | 10/10 | No confirmed Ukrainian-form or grammar errors in examples such as `“Вибачте, де тут аптека?”`, `“Біля дому є магазин і кафе.”`, `“на пошті / на вокзалі / на площі.”` |
| 3. Pedagogical quality | 6/10 | The module opens with two dense English theory paragraphs: `“Navigating a new city is a highly practical skill...”` and `“Imagine arriving in a new town...”` before the first Ukrainian example. Similar filler appears in `“To navigate effectively, a robust vocabulary...”` |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is covered naturally across the module: `аптека, бібліотека, магазин, ресторан, готель, вокзал, тут, там`; recommended items like `лікарня, пошта, музей, церква, далеко, близько, біля` also appear. |
| 5. Exercise quality | 8/10 | All 4 planned activity markers are present, but `<!-- INJECT_ACTIVITY: fill-in-describe-city -->` and `<!-- INJECT_ACTIVITY: quiz-where-to-go -->` are clustered together at the end of one section. |
| 6. Engagement & tone | 5/10 | Filler-heavy lines like `“This conversation demonstrates a highly efficient pattern”` and `“To navigate effectively, a robust vocabulary of city landmarks is essential”` add length more than teaching value. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and in order; markdown is clean; pipeline word count is 1627, which is above the 1200 target. |
| 8. Cultural accuracy | 9/10 | No Russian-centric framing or cultural inaccuracies; examples stay in ordinary Ukrainian urban context such as `“на вулиці Шевченка”` and `“У моєму місті є великий парк...”` |
| 9. Dialogue & conversation quality | 6/10 | Dialogue 2 is a thin Q/A sequence: `“Що є біля твого дому? ... А школа?”` It feels like an interrogation rather than a concrete shared task with richer turns. |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: Dialogue section — `“The second dialogue shifts the focus...”` / `“Що є біля твого дому? ... Біля дому є магазин і кафе.”`  
Issue: The plan’s specific dialogue situation is missing. I confirmed no occurrences of `Київ`, `поруч з`, `далеко від`, `озеро`, or `зупинка` in the module, so the planned map task and key chunks were not implemented.  
Fix: Replace Dialogue 2 with a Kyiv-neighborhood map exchange that includes `музей, площа, озеро, зупинка, церква` and the chunks `біля, поруч з, далеко від`.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: Dialogue 2 — `“Що є біля твого дому? ... А школа?”`  
Issue: The exchange is one-sided and overly transactional. It does not give the speakers a concrete shared purpose or distinct conversational turns.  
Fix: Rewrite it as a collaborative map-description dialogue instead of a short interrogation.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: Opening of `Діалоги` — `“Navigating a new city is a highly practical skill...”` / `“Imagine arriving in a new town...”`  
Issue: The module spends too long on abstract English explanation before giving learners Ukrainian input. For A1 PPP, the presentation should move to the model dialogue faster.  
Fix: Replace the two opening paragraphs with a brief preview that states the task and points directly to the dialogue.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: Opening of `Місця в місті` — `“To navigate effectively, a robust vocabulary of city landmarks is essential...”`  
Issue: This is generic meta prose rather than direct teaching. It inflates the section without adding much usable language.  
Fix: Replace it with a short instruction that introduces the word set and leads straight into examples.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Де це?` — `“Additionally, the established locative phrases **у центрі** ... **на розі** ...”`  
Issue: The plan explicitly calls for `поруч з` and `далеко від`, but this section never teaches them.  
Fix: Expand this paragraph with short chunk-based examples of `поруч з` and `далеко від`.

[EXERCISE QUALITY] [SEVERITY: minor]  
Location: End of `Де це?` — `<!-- INJECT_ACTIVITY: fill-in-describe-city -->` followed immediately by `<!-- INJECT_ACTIVITY: quiz-where-to-go -->`  
Issue: The activity count and types are correct, but the last two markers are clustered instead of spaced through the module.  
Fix: Move `quiz-where-to-go` up to follow the place/action practice.

## Verdict: REVISE
REVISE. There are no confirmed linguistic errors, but several dimensions score below 9 and there are multiple major quality findings: the plan-specific Kyiv map dialogue is missing, the teaching prose is overpadded with English filler, and the second dialogue plus exercise distribution need targeted fixes.

<fixes>
- find: |
    Navigating a new city is a highly practical skill. Knowing how to identify buildings, ask for directions, and locate specific places transforms a confusing map into a readable environment. The ability to describe your surroundings is fundamental to daily communication. Understanding core urban vocabulary is essential for functioning in a Ukrainian city. Two natural conversations illustrate how people ask for and provide location information. Pay close attention to how the speakers locate places using simple vocabulary rather than complex sentences.

    Imagine arriving in a new town and needing to locate basic services. The most direct approach is to ask a passerby. In Ukrainian, these exchanges are brief and rely on simple spatial vocabulary rather than complex verb structures. Observe how the question is framed and how the response pinpoints the street without unnecessary elaboration. This directness is polite and highly efficient.
  replace: |
    These dialogues teach you to ask where a place is and to describe a neighborhood on a simple map. Alina and Ihor use city vocabulary to mark places in a Kyiv neighborhood and say what is near, next to, or far from each landmark.

- find: |
    The second dialogue shifts the focus from finding a specific destination to describing a local area. Two people are discussing the immediate surroundings of a home. This is a common topic of conversation when getting to know someone, understanding their daily routine, and learning about the infrastructure of their neighborhood.

    > **Ігор:** Що є біля твого дому? *(What is near your home?)*
    > **Аліна:** Біля дому є магазин і кафе. *(Near the home there is a shop and a cafe.)*
    > **Ігор:** А школа? *(And the school?)*
    > **Аліна:** Школа далеко, у центрі міста. *(The school is far away, in the city center.)*

    This brief exchange reviews the location patterns essential for describing an environment. The phrase **у центрі** (in the center) combines the preposition **у** with the locative case. Furthermore, the word **є** functions as "there is," allowing the speaker to list the establishments that exist in the neighborhood.
  replace: |
    The second dialogue follows the planned map task: two friends are drawing a Kyiv neighborhood for a pen pal and naming the places on it.

    > **Ігор:** Що є на твоїй карті? *(What is on your map?)*
    > **Аліна:** Тут є бібліотека, музей і площа. *(There is a library, a museum, and a square here.)*
    > **Ігор:** А де озеро? *(And where is the lake?)*
    > **Аліна:** Озеро біля музею, а зупинка поруч з площею. *(The lake is near the museum, and the bus stop is next to the square.)*
    > **Ігор:** А церква? *(And the church?)*
    > **Аліна:** Церква далеко від озера, але біля бібліотеки. *(The church is far from the lake, but near the library.)*

    This brief exchange reviews the location patterns essential for describing an environment. It also gives the learner ready-made chunks with **є**, **біля**, **поруч з**, and **далеко від**.

- find: |
    To navigate effectively, a robust vocabulary of city landmarks is essential. A typical urban environment consists of various public and commercial spaces. Building this foundational vocabulary allows you to identify your surroundings and plan your activities confidently. Here are the core nouns for common public places:
  replace: |
    Start with the core names of places you see on a city map. Read the words first, then connect them to the locative patterns and actions below.

- find: |
    Additionally, the established locative phrases **у центрі** (in the center) and **на розі** (on the corner) are vital for describing key intersections and central areas in any city.
  replace: |
    Additionally, the chunks **поруч з** (next to) and **далеко від** (far from) help you describe distance more precisely. Learn them as ready-made patterns: **поруч з музеєм**, **поруч з площею**, **далеко від озера**, **далеко від вокзалу**. The established locative phrases **у центрі** (in the center) and **на розі** (on the corner) are vital for describing key intersections and central areas in any city.

- find: |
    <!-- INJECT_ACTIVITY: match-up-place-activity -->
  replace: |
    <!-- INJECT_ACTIVITY: match-up-place-activity -->
    <!-- INJECT_ACTIVITY: quiz-where-to-go -->

- find: |
    <!-- INJECT_ACTIVITY: fill-in-describe-city -->
    <!-- INJECT_ACTIVITY: quiz-where-to-go -->
  replace: |
    <!-- INJECT_ACTIVITY: fill-in-describe-city -->
</fixes>
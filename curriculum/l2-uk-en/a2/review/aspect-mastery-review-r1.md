## Linguistic Scan
- The module repeatedly teaches `говорити / сказати` as a **видова пара**: `The most crucial examples ... are **брати / взяти** ... and **говорити / сказати**`, `**говорити / сказати** — *to speak, to say*`, and `Verbs involving communication, such as **говорити / сказати** ...`. VESUM marks `говорити` and `казати` as imperfective, `сказати` as perfective; the clean aspect pair here is `казати / сказати`, not `говорити / сказати`.
- The suffix-pattern explanation is factually wrong in two places. `A great example is the pair **допомагати / допомогти**` mislabels a stem-changing pair as the suffix model, and `you will see many verbs that change their **суфікс** (suffix) to form the perfective aspect` reverses the rule. In the module’s own examples, the longer suffixed forms are imperfective: `записувати`, `розповідати`, `пояснювати`.

## Exercise Check
Four markers are present: `group-sort-formation`, `match-up-pairs`, `fill-in-context`, and `quiz-read-a-mini-situation-and-choose-the-correct-aspect-form-with-justification`. They match the four `activity_hints`, appear after the relevant teaching sections, and are spread evenly through the module. No inline DSL exercise logic is present to audit.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All four planned sections and all 4 activity markers are present, but section pacing is far off plan: 693/500, 864/600, 727/500, 619/400 words. Recommended vocabulary item `морфологія` has 0 matches in the module. |
| 2. Linguistic accuracy | 5/10 | Critical teaching errors: the text presents `говорити / сказати` as an aspect pair, uses `допомагати / допомогти` as the suffix-pattern example, and later says suffix changes “form the perfective aspect.” |
| 3. Pedagogical quality | 6/10 | There is a PPP skeleton and many examples, but the first section opens with a long English theory block before the first Ukrainian example, and later sections spend too much space on meta-explanation instead of tighter contrasts and practice. |
| 4. Vocabulary coverage | 8/10 | Required plan vocabulary is present in prose, and recommended `утворення`, `тільки що`, and `вже` appear; `морфологія` is missing. |
| 5. Exercise quality | 9/10 | Marker placement is strong: each activity comes after the target teaching section, and the marker inventory matches the plan exactly. |
| 6. Engagement & tone | 8/10 | The voice is teacherly rather than gamified, but repeated lines like “You will use these pairs constantly” and “absolute key to fluency” add filler more than teaching value. |
| 7. Structural integrity | 10/10 | All planned H2 headings are present and ordered correctly, formatting is clean, and the pipeline count is 2925 words, safely above target. |
| 8. Cultural accuracy | 10/10 | No Russian-centric framing or cultural inaccuracies surfaced. |
| 9. Dialogue & conversation quality | 8/10 | The dialogues are named and scenario-based, but the dialogue section spends substantial space explaining the dialogues instead of giving more actual turns. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `The most crucial examples for daily communication are **брати / взяти** ... and **говорити / сказати**`, `**говорити / сказати** — *to speak, to say*`, `Verbs involving communication, such as **говорити / сказати** ...`  
Issue: The module teaches `говорити / сказати` as a clean aspect pair. VESUM/dictionary evidence supports `казати` = imperfective and `сказати` = perfective; `говорити` is a separate imperfective verb with broader meaning.  
Fix: Replace `говорити / сказати` with `казати / сказати` everywhere it is presented as an aspect pair, and adjust the explanatory prose accordingly.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `A great example is the pair **допомагати / допомогти** (to help — impf./pf.).` and `you will see many verbs that change their **суфікс** (suffix) to form the perfective aspect.`  
Issue: The suffix-formation pattern is taught incorrectly. `допомагати / допомогти` is not the module’s own type-2 suffix example, and the Group B intro reverses the direction by claiming suffixes form the perfective.  
Fix: Use a real suffixal example such as `записувати / записати`, and rewrite the Group B intro so it says the longer suffixed form is usually imperfective.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: The prose has 0 matches for `морфологія`; section counts are 693/864/727/619 words against plan budgets 500/600/500/400.  
Issue: A recommended plan term is missing, and the module overshoots every section budget by a wide margin.  
Fix: Add `морфологія` in the opening explanation and compress the long English framing paragraphs in sections 1-4.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `In English, we use different tenses...`, `Now that you know the four formation patterns...`, `In everyday conversation, choosing the right **видова пара**...` through `Our first dialogue takes place...`  
Issue: Too much of the module tells the learner what will happen instead of teaching the contrast directly. This delays Ukrainian examples and weakens the explanation-to-practice ratio.  
Fix: Replace the long English setup paragraphs with short lead-ins and keep the saved space for direct contrasts, examples, or dialogue turns.

## Verdict: REVISE
REVISE — the module has solid structure and exercise placement, but the critical grammar-teaching errors around aspect pairing and suffix formation make it unsafe to ship as-is.

<fixes>
- find: |-
    In English, we use different tenses to show if an action is ongoing or completed. For example, "I was doing" describes a process, while "I did it" describes a finished result. In Ukrainian, we use a completely different approach. We change the verb itself to create an **видова пара** (aspect pair). The imperfective form describes a process, a habit, or a repeated action. The perfective form focuses on the result, completion, or a single successful event. You will use these pairs constantly in everyday conversations.
  replace: |-
    In Ukrainian, aspect is part of verb **морфологія**. We create a **видова пара** (aspect pair) by changing the verb itself: the imperfective form shows process, habit, or repetition, while the perfective form highlights completion or a single result.

- find: |-
    The most common way to form the perfective aspect is by adding a **префікс** (prefix) to the imperfective verb. This prefix adds the meaning of completion but does not change the core meaning of the action. Let's look at how this works in practice.
  replace: |-
    The most common way to form the perfective aspect is by adding a **префікс** (prefix) to the imperfective verb. Let us look at how this works in practice.

- find: |-
    > *This is a very popular method of formation. We say "to write" when the action is ongoing. But we say "to have written" when the text is ready. Other pairs work the same way. The word "to read" becomes "to have read". The word "to do" becomes "to have done". Also, "to eat" becomes "to have eaten", and "to cook" becomes "to have cooked". Before the letters "k", "p", "t", "f", and "kh" we use the prefix "s-". Therefore we say "to have photographed", "to have said", and "to have baked".*
  replace: |-
    > *This pattern usually marks completion: писати → написати, читати → прочитати, робити → зробити.*

- find: |-
    A great example is the pair **допомагати / допомогти** (to help — impf./pf.).
  replace: |-
    A great example is the pair **записувати / записати** (to write down — impf./pf.).

- find: |-
    Finally, the fourth pattern includes verbs that use completely different roots for their imperfective and perfective forms. These are called suppletive verbs. Because they lack a shared root, you cannot rely on prefixes or suffixes, and you simply have to memorize them as distinct pairs. The most crucial examples for daily communication are **брати / взяти** (to take — impf./pf.) and **говорити / сказати** (to say — impf./pf.).
  replace: |-
    Finally, the fourth pattern includes verbs that use different roots in the imperfective and perfective. These suppletive pairs must be memorized. The most crucial examples for daily communication are **брати / взяти** (to take — impf./pf.) and **казати / сказати** (to say — impf./pf.).

- find: |-
    Now that you know the four formation patterns, it is time to build your core vocabulary. We have selected the thirty most essential aspect pairs for everyday communication. They are divided into three thematic groups: daily actions, communication, and movement. Learning them as linked pairs is the absolute key to fluency in Ukrainian. Whenever you learn a new verb, you should immediately memorize its partner. Every **видова пара** (aspect pair) gives you the tools to express both the journey and the destination of an action.
  replace: |-
    Below are thirty high-frequency aspect pairs grouped by topic. Learn each verb together with its partner, not as an isolated word.

- find: |-
    The first group covers the most common actions you perform at home, in the kitchen, or during your daily chores. Most of these verbs form their perfective partner by simply adding a **префікс** (prefix) to the front of the word. This short addition acts like a seal of completion. When you use the imperfective form, you invite the listener to imagine the ongoing process of the work. When you use the perfective form, you present them with the final, ready product.
  replace: |-
    The first group covers everyday actions at home and in the kitchen. Most pairs here are prefix-based: the imperfective shows the process, and the perfective shows the finished result.

- find: |-
    The second group contains verbs related to communication, studying, and processing new information. In this category, you will see many verbs that change their **суфікс** (suffix) to form the perfective aspect. Pay close attention to the pair **говорити / сказати** (to say — impf./pf.), which uses completely different roots. This is incredibly common in spoken Ukrainian when reporting what someone said versus describing a long conversation.
  replace: |-
    The second group contains verbs related to communication, studying, and processing new information. In this category, you will see many pairs where the imperfective verb has a longer suffix, while the perfective partner is shorter. Pay close attention to the pair **казати / сказати** (to say — impf./pf.), which is a true aspect pair used constantly in everyday speech.

- find: |-
    **говорити / сказати** — *to speak, to say*
  replace: |-
    **казати / сказати** — *to say, to tell*

- find: |-
    To truly master these essential verbs, you need to practice them actively in context. Do not just read the lists and hope to remember them. Try writing your own personal sentences for each aspect pair. Describe what you were doing yesterday as an ongoing process, and contrast it with what you actually finished successfully.
  replace: ""

- find: |-
    Now that you know how to form an **видова пара** (aspect pair), it is time to look at how we use them in real life. The basic rule of "process versus result" is a great starting point for beginners. However, real conversations are rarely that simple. We often combine different actions in a single sentence, paragraph, or story. To speak naturally and understand native speakers, you need to see how perfective and imperfective verbs interact with each other in context. Let us explore four common scenarios where choosing the right aspect is absolutely crucial for conveying your true meaning.
  replace: |-
    Now let us see how aspect works in real context. The four key situations below show when Ukrainian chooses process and when it chooses result.

- find: |-
    The second scenario is the classic interruption pattern. This happens when there is a long, ongoing background action which is suddenly interrupted by a short, completed event. The background action is always imperfective, because it describes a process happening over time. The interrupting event is perfective, because it is a sudden result that breaks into that ongoing process. Verbs involving communication, such as **говорити / сказати** (to say — impf./pf.), often appear in these interruptions.
  replace: |-
    The second scenario is interruption: a long background action is imperfective, and the sudden interrupting event is perfective. Verbs of speech, such as **казати / сказати** (to say — impf./pf.), often appear in this contrast.

- find: |-
    The third scenario contrasts habitual actions with a single result. If you do something regularly or repeatedly, you must always use the imperfective aspect. This remains true even if the action finishes completely every single time it happens. However, if you are focusing on a specific, one-time achievement on a particular day, you must switch to the perfective aspect to highlight that unique result. We can see this clearly with the verbs **допомагати / допомогти** (to help — impf./pf.) and **давати / дати** (to give — impf./pf.).
  replace: |-
    The third scenario contrasts habit with a single result: repeated actions take the imperfective, while one specific achievement takes the perfective. This is clear with **допомагати / допомогти** (to help — impf./pf.) and **давати / дати** (to give — impf./pf.).

- find: |-
    The final scenario involves the subtle nuances of negation. Adding the word «не» (not) before a verb changes the meaning of the aspect significantly. Negating an imperfective verb simply means the action did not happen at all, or it is just a general fact about your life. On the other hand, negating a perfective verb often implies that you attempted the action, but you failed or did not achieve the final result. You might also see this nuance with verbs involving placement, like **класти / покласти** (to put — impf./pf.), or taking items, like **брати / взяти** (to take — impf./pf.).
  replace: |-
    The final scenario is negation. With the imperfective, «не» usually means the action did not happen at all or is true in general; with the perfective, it often means the speaker did not reach the result.

- find: |-
    In everyday conversation, choosing the right **видова пара** (aspect pair) often depends on whether you are asking about a general activity or checking off a task list. This applies to all verbs, whether they change aspect using a **префікс** (prefix) or a **суфікс** (suffix). We frequently use conversational trigger phrases to emphasize results. 
    
    Before we look at the dialogues, let's review some key verbs you will see. It is important to know when to use **брати / взяти** (to take — impf./pf.) and **давати / дати** (to give — impf./pf.) in conversation. You will also notice verbs related to communication, like **говорити / сказати** (to say — impf./pf.).
    
    You might also need verbs for placement, like **класти / покласти** (to put — impf./pf.). Finally, pay attention to how speakers use **починати / почати** (to begin — impf./pf.) and **закінчувати / закінчити** (to finish — impf./pf.) to manage their time.
    
    Do not forget about **допомагати / допомогти** (to help — impf./pf.) when someone needs assistance. The word «вже» (already) is often paired with a perfective verb to confirm a completed task, while «тільки що» (just now) highlights a perfective action that ended a moment ago.
    
    Our first dialogue takes place between a parent and a child doing homework. This everyday scenario perfectly demonstrates the emotional difference between checking completed tasks and describing an ongoing, frustrating process.
  replace: |-
    In conversation, speakers switch aspect depending on whether they ask about a process or check a result. Watch the contrast between **брати / взяти**, **давати / дати**, **казати / сказати**, **класти / покласти**, **починати / почати**, **закінчувати / закінчити**, and **допомагати / допомогти** in the dialogues below.

- find: |-
    Notice how the parent uses perfective verbs because they want to see final results and move on to the next task. Meanwhile, the student uses imperfective verbs to emphasize the long, exhausting process they are currently experiencing.
  replace: |-
    The parent asks about the result, while the student emphasizes the unfinished process.

- find: |-
    Нарешті, зверніть увагу на використання видових пар у майбутньому часі. Якщо ваш керівник запитує про загальні плани на завтра, він використовує недоконаний вид, щоб дізнатися про вашу рутину. Але коли його цікавить кінцевий результат до п'ятниці, він обирає доконаний вид.
    
    > *Finally, pay attention to the use of aspect pairs in the future tense. If your manager asks about general plans for tomorrow, he uses the imperfective aspect to find out about your routine. But when he is interested in the final result by Friday, he chooses the perfective aspect.*
  replace: |-
    Нарешті, зверніть увагу на майбутній час: недоконаний вид описує запланований процес, а доконаний — очікуваний результат.
    
    > *In the future, the imperfective describes the planned process, while the perfective highlights the expected result.*
</fixes>
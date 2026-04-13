## Linguistic Scan
No Russianisms, Surzhyk, calques, or paronym errors found in the Ukrainian examples.

Factual grammar issues found:
- `## Я люблю...` says: “This structure is strictly used for actions, not for physical objects or abstract concepts.” That is false. `любити` also takes noun objects; СУМ-11 defines it as transitive `кого-, чого-небудь`, and textbook data includes `Я люблю музику.`
- `## Я люблю...` says: “an infinitive ... always ends in ... **-ти**.” That is false as a general claim; textbook data gives `-ти`, rarer `-ть`.
- `## Мені подобається...`, the `:::tip`, and the summary repeat the false rule that actions take `люблю` and things take `подобається` as if this were the only Ukrainian option.

## Exercise Check
4/4 planned exercise markers are present:
- `match-infinitives` and `fill-in-activities` appear after `## Я люблю...`
- `quiz-like-structure` and `fill-in-negative` appear after `## Мені подобається...`

Placement is correct, the markers are spread sensibly, and each one matches a plan activity type/focus. No marker-level issues found. The actual downstream YAML exercise logic is not visible here, so it cannot be audited from this artifact alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All planned H2 sections and target vocabulary are present, but the teaching blocks run long because of added exposition; `Я люблю...` and especially `Мені подобається...` are padded well beyond the plan’s lean 300-word teaching shape. |
| 2. Linguistic accuracy | 4/10 | The module teaches false rules: “This structure is strictly used for actions...”, “actions take **люблю**, while objects and things take **подобається**”, and “an infinitive ... always ends in ... **-ти**.” |
| 3. Pedagogical quality | 6/10 | The PPP flow exists, but it is weakened by categorical rules that are not actually true and by long English theory blocks like “The grammatical concept that makes this structure work so smoothly...” instead of tighter example-led explanation. |
| 4. Vocabulary coverage | 10/10 | All required verbs appear in prose/examples, and recommended `малювати`, `подорожувати`, `співати`, `музика`, `фільм`, `книга` are also used in context. |
| 5. Exercise quality | 9/10 | All four planned markers are present and placed after the relevant teaching sections; the visible marker design matches the plan well. |
| 6. Engagement & tone | 6/10 | The Kyiv/tea/tandem setting helps, but lines like “It is a fantastic opportunity...” and “cement the absolute foundation...” add word count without adding teaching value. |
| 7. Structural integrity | 9/10 | All H2 headings are present and ordered correctly, and the pipeline word count is 1495, above the 1200 target. |
| 8. Cultural accuracy | 9/10 | The module is grounded in Kyiv and everyday Ukrainian context, with no Russian-centric framing. |
| 9. Dialogue & conversation quality | 9/10 | Dialogue 1 is a plausible first-meeting exchange with named speakers and a natural follow-up question; Dialogue 2 is simple but coherent. |

## Findings
[Linguistic accuracy] [SEVERITY: critical]  
Location: `## Я люблю...` — “This structure is strictly used for actions, not for physical objects or abstract concepts.”  
Issue: False grammar rule. Ukrainian `любити` also takes noun objects; this teaches an exclusive contrast that is not true.  
Fix: Reframe it as a module-specific beginner pattern, not a universal rule.

[Linguistic accuracy] [SEVERITY: critical]  
Location: `## Я люблю...` — “In Ukrainian, you can easily spot an infinitive because it always ends in the distinct suffix **-ти**.”  
Issue: Factually wrong. School-textbook data gives infinitives in `-ти`, more rarely `-ть`.  
Fix: Limit the claim to the examples in this module or say the beginner examples here use `-ти`.

[Linguistic accuracy] [SEVERITY: critical]  
Location: `## Мені подобається...`, `:::tip`, `## Підсумок — Summary` — “However, you must use **мені подобається**...”, “actions take **люблю**...”, “You must use...”  
Issue: The same false exclusive contrast is repeated three more times, so the learner is likely to memorize it as a hard grammar law.  
Fix: Reframe all three spots as a teaching contrast used in this module, not the only possible Ukrainian phrasing.

[Plan adherence] [SEVERITY: major]  
Location: `## Я люблю...` and `## Мені подобається...`  
Issue: The prose is inflated with explanatory filler, so the module drifts away from the plan’s tight 300-word teaching blocks.  
Fix: Trim generic exposition and keep the explanation anchored to the examples.

[Engagement & tone] [SEVERITY: major]  
Location: `## Діалоги` — “It is a fantastic opportunity to practice speaking in a relaxed and friendly environment.”; `## Підсумок — Summary` — “cement the absolute foundation...”  
Issue: Empty booster language adds volume but not substance.  
Fix: Replace with direct teacher voice that points back to the pattern being learned.

## Verdict: REVISE
REVISE. The module cannot PASS because it contains critical linguistic inaccuracies that teach false grammar rules about `любити`/`подобатися` and about infinitive endings. Structure, vocabulary coverage, and marker placement are solid, so this is a repair job, not a full rebuild.

<fixes>
- find: "The best way to break the ice and find common ground is by sharing your hobbies and talking about the activities you enjoy doing in your free time. It is a fantastic opportunity to practice speaking in a relaxed and friendly environment."
  replace: "Sharing hobbies is a natural way to break the ice and practice simple Ukrainian."

- find: "Whenever you want to talk about your own favorite pastimes, you will rely on this exact same combination of words to get your point across to a native speaker."
  replace: "You can use this same pattern to talk about your own hobbies."

- find: "This structure is strictly used for actions, not for physical objects or abstract concepts."
  replace: "In this module, we use this structure for activities and hobbies."

- find: "The grammatical concept that makes this structure work so smoothly is the **інфінітив** (infinitive) form. The infinitive is simply the basic, dictionary form of a verb. It is the raw, unconjugated version of an action before it has been altered to match a specific person or a specific point in time. In Ukrainian, you can easily spot an infinitive because it always ends in the distinct suffix **-ти**. This fixed **-ти** form is exactly what immediately follows **я люблю**. You do not need to worry about conjugating the second verb at all; it stays in its pure, dictionary state, making it very easy to build these sentences."
  replace: "The form after **я люблю** is the **інфінітив** (infinitive), the basic dictionary form of the verb. In the examples in this module, these infinitives end in **-ти**: **читати, гуляти, готувати**. After **я люблю**, the second verb stays in this dictionary form."

- find: "While you now know exactly how to talk about the activities you love doing, you also need a reliable way to express that you simply like a specific thing, object, or place. For this, Ukrainian introduces a second, highly common way to say 'I like': the phrase **мені подобається**. It is crucial to contrast its usage directly with **я люблю** to avoid confusion. You use **я люблю** plus an infinitive action to express that you enjoy *doing* something. However, you must use **мені подобається** plus a noun to express that a static thing, physical object, or geographic location appeals to you."
  replace: "You also need a second common pattern for likes: **мені подобається**. In this module, use **я люблю** + infinitive for activities and **мені подобається** + noun for things or places. This keeps the two beginner patterns clear without adding extra grammar yet."

- find: "Always remember the golden rule: actions take **люблю**, while objects and things take **подобається**. Keeping these two categories separate in your mind will immediately make your Ukrainian sound much more natural."
  replace: "For this module, keep the two patterns separate: use **люблю** with activities and **мені подобається** with things. This helps you practice the contrast clearly."

- find: "A quick recap of the core distinction taught in this module will cement the absolute foundation of expressing your personal preferences in Ukrainian. You now have two distinct grammatical tools at your disposal. You must use the structure **я люблю** followed by an infinitive verb ending in **-ти** specifically for activities and actions that you actively enjoy doing. In sharp contrast, you must use the fixed chunk **мені подобається** followed directly by a noun for static things, objects, and places that appeal to you. This separation between liking an action and liking an object is a fundamental part of thinking in Ukrainian, rather than simply translating directly from English."
  replace: "Here is a quick recap of the two beginner patterns from this module. Use **я люблю** + infinitive to talk about activities you enjoy doing, and use **мені подобається** + noun to talk about things or places you like. This contrast helps you practice two common sentence patterns clearly."
</fixes>
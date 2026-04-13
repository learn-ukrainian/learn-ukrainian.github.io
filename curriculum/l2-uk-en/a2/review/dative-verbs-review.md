## Linguistic Scan
No linguistic errors found.

## Exercise Check
4 activity markers are present: `fill-in-dative-verbs`, `match-up-podobatysia`, `true-false-age`, `quiz-dative-vs-accusative`.
Each marker appears after the relevant teaching section, the IDs match the plan’s `activity_hints`, and the markers are distributed section-by-section rather than clustered at the end.
No inline DSL exercises are present, so there is no exercise-logic error to audit in the prose itself.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All four planned H2 sections are present and in the planned order; required plan vocabulary appears in prose (`допомагати`, `дякувати`, `дзвонити`, `радити`, `заважати`, `подобатися`, `відповідати`, `рік/роки/років`); all four planned activity markers are present. |
| 2. Linguistic accuracy | 10/10 | No Russian characters found (`ы/э/ё/ъ` all 0 occurrences). Spot checks via VESUM confirmed forms such as `подобався`, `подобалися`, `дитині`, `гратися`; no Russianisms, surzhyk, calques, or wrong Ukrainian case forms were found in the Ukrainian text. |
| 3. Pedagogical quality | 7/10 | The module has solid PPP sequencing, but several English glosses are misleading: “This noise on the street bothers mom from reading a book”, “The father answers the teacher to all his questions about school”, and the accusative explanation says “we only use the accusative case” after noting `чекати` can pattern differently. The age note “years have been given to me” is also an invented metaphor rather than a clean grammar explanation. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary from the plan is used naturally in prose and examples rather than dumped in a bare list. |
| 5. Exercise quality | 10/10 | Marker count matches the 4 plan hints exactly, and each marker follows the section whose skill it is supposed to test. |
| 6. Engagement & tone | 8/10 | Tone is mostly teacherly and functional, but filler like “Це дуже важливе правило в українській мові” adds words without adding instruction. |
| 7. Structural integrity | 10/10 | Clean markdown structure, all planned H2 headings present, no dangling sections, and deterministic pipeline word count is 3066, which is above target. |
| 8. Cultural accuracy | 10/10 | No Russia-centric framing, no cultural inaccuracies, and examples stay within ordinary Ukrainian contexts. |
| 9. Dialogue & conversation quality | 8/10 | The age dialogue is natural enough, but the preferences dialogue has an abrupt stitched transition: “А мені подобається спорт. Чи подобається їм Київ?” |

## Findings
[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: first section gloss — “This noise on the street bothers mom from reading a book. The father answers the teacher to all his questions about school.”  
Issue: The English gloss is misleading and unidiomatic for `заважати` and `відповідати`, which weakens the grammar explanation for learners using the translation as support.  
Fix: Change the gloss to “This noise on the street keeps mom from reading a book. The father answers the teacher’s questions about school.”

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: fourth section gloss — “For example, the verbs "to see", "to know", "to love", and "to wait" take a direct object. ... in these situations, the action is directed straight at the person, so we only use the accusative case.”  
Issue: This overstates the rule in English and clashes with the Ukrainian prose in the same paragraph, which already says `чекати` can use other government patterns.  
Fix: Reword the English gloss so it presents accusative as the pattern used in these examples, not as the only possible pattern.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: age note — “In Ukrainian, age is not an attribute you possess, but a state of being assigned to you. Think of it as "years have been given to me".”  
Issue: This is an invented metaphor, not a precise grammar explanation, and it risks teaching a pseudo-rule instead of the actual pattern.  
Fix: Replace it with a neutral memory aid that states the real pattern: Dative person + number + `рік/роки/років`.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: age section — “Це дуже важливе правило в українській мові.”  
Issue: This is filler; it adds emphasis but no new information.  
Fix: Remove the sentence and keep the concise structural explanation.

[DIALOGUE & CONVERSATION QUALITY] [SEVERITY: major]  
Location: preferences dialogue — “А мені подобається спорт. Чи подобається їм Київ?”  
Issue: The topic jump is abrupt, so the exchange reads like stitched example lines rather than a natural conversation.  
Fix: Add a transition such as “До речі” to make the shift conversational.

## Verdict: REVISE
The Ukrainian itself is clean, so this is not a reject. It still needs revision because dimensions 3, 6, and 9 fall below 9, and the identified issues are real pedagogical/dialogue problems that should be fixed before shipping.

<fixes>
- find: |
    > *Every week I call my friend to discuss the latest news. We always sincerely thank our female friend for her support. The doctor advises my brother to rest more in the fresh air. This noise on the street bothers mom from reading a book. The father answers the teacher to all his questions about school.*
  replace: |
    > *Every week I call my friend to discuss the latest news. We always sincerely thank our female friend for her support. The doctor advises my brother to rest more in the fresh air. This noise on the street keeps mom from reading a book. The father answers the teacher's questions about school.*
- find: |
    > *Many common verbs in Ukrainian always require the accusative case. These are verbs that denote a direct action on a certain object. To check, we ask the questions "whom?" or "what?". For example, the verbs "to see", "to know", "to love", and "to wait" take a direct object. If you say "I see mom", the word "mom" is in the accusative case. Let's look at other typical examples. "He really loves his older brother." "We are waiting for the sister near the school." "She knows this doctor well." In these situations, the action is directed straight at the person, so we only use the accusative case.*
  replace: |
    > *Many common verbs in Ukrainian use the accusative case in ordinary direct-object patterns. These are verbs that denote a direct action on a certain object. To check, we ask the questions "whom?" or "what?". For example, the verbs "to see", "to know", and "to love" take a direct object, and "чекати" is also often used with the accusative in examples like these. If you say "I see mom", the word "mom" is in the accusative case. Let's look at other typical examples. "He really loves his older brother." "We are waiting for the sister near the school." "She knows this doctor well." In these examples, the action is directed straight at the person, so the accusative is the relevant case.*
- find: |
    :::note
    **A matter of being** — In Ukrainian, age is not an attribute you possess, but a state of being assigned to you. Think of it as "years have been given to me".
    :::
  replace: |
    :::note
    **Memory tip** — A practical way to remember this pattern is: Dative person + number + рік/роки/років, for example, Мені двадцять п'ять років.
    :::
- find: |
    Коли ми говоримо про вік, ми завжди використовуємо давальний відмінок. Це дуже важливе правило в українській мові. Ми ставимо особу в давальний відмінок, потім додаємо число, а потім кажемо слово «рік» у правильній формі.
  replace: |
    Коли ми говоримо про вік, ми використовуємо давальний відмінок. Ми ставимо особу в давальний відмінок, потім додаємо число, а потім кажемо слово «рік» у правильній формі.
- find: |
    > — **Оксана:** А мені подобається спорт. Чи подобається їм Київ? *(And I like sports. Do they like Kyiv?)*
  replace: |
    > — **Оксана:** А мені подобається спорт. До речі, їм подобається Київ? *(And I like sports. By the way, do they like Kyiv?)*
</fixes>
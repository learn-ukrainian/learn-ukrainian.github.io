## Linguistic Scan
No Russianisms, Surzhyk, calques, paronym errors, or forbidden Russian characters were found in the Ukrainian examples.

One factual grammar issue was found:
- In `## Могти і мусити (Can and Must)`, the claim `This verb strictly denotes physical capability, availability, or receiving permission.` is too narrow. `могти` also expresses possibility; the module itself later says `ability or possibility`, so the explanation is internally inconsistent.

## Exercise Check
Markers found: 4 total, in the planned order: `fill-in`, `quiz`, `fill-in`, `quiz`.

Placement check:
- `<!-- INJECT_ACTIVITY: fill-in -->` appears after `## Хотіти (To Want)` and matches the planned conjugation focus.
- `<!-- INJECT_ACTIVITY: quiz -->` and `<!-- INJECT_ACTIVITY: fill-in -->` appear after `## Могти і мусити (Can and Must)` and fit modal-choice / sentence-completion practice.
- `<!-- INJECT_ACTIVITY: quiz -->` appears after `## Підсумок — Summary` and is a sensible place for a final pattern check.

No exercise-marker count mismatch or obvious marker-placement logic errors found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The module covers the contract’s core beats well, including both dialogues, `хотіти + noun` vs `хотіти + infinitive`, and the `могти/мусити` contrast. However, the summary section is far below its 270-330 section budget, and the pipeline note fixes the total module length at 1186, below the 1200 target. |
| 2. Linguistic accuracy | 8/10 | The Ukrainian examples themselves are clean, but the explanation `This verb strictly denotes physical capability, availability, or receiving permission` is factually too narrow for `могти`, which also covers possibility. |
| 3. Pedagogical quality | 8/10 | The module mostly follows dialogue -> explanation -> examples, but the summary spends too much space on generic English coaching (`Active practice is required...`, `Building these sentences out loud...`) instead of giving more Ukrainian production models. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is well integrated in context: `хочеш`, `робити`, `гуляти`, `можу`, `мушу`, `працювати`, `каву`, `борщ`, `їсти`. |
| 5. Exercise quality | 9/10 | All 4 planned markers are present, in the right type order, and placed after relevant teaching content. No visible logic defects can be established from the markers themselves. |
| 6. Engagement & tone | 8/10 | The actual examples are useful, but some prose sounds generated and expository, especially `Olya and Denys are planning a weekend — negotiating what to do` and the abstract summary coaching. |
| 7. Structural integrity | 6/10 | Headings are clean and ordered, but the pipeline note gives a total of 1186 words, below target, and the summary section is notably thinner than the other three sections. |
| 8. Cultural accuracy | 9/10 | No Russia-centered framing or dubious cultural claims. Situations are ordinary and appropriate: weekend plans and a café order. |
| 9. Dialogue & conversation quality | 9/10 | The dialogues are named, multi-turn, and functional. `Що ти хочеш робити сьогодні? ... Я не можу, я мушу працювати.` is a natural A1 planning exchange. |

## Findings
[2. Linguistic accuracy] [SEVERITY: critical]  
Location: `## Могти і мусити (Can and Must)` — `This verb strictly denotes physical capability, availability, or receiving permission.`  
Issue: This teaches an overly narrow meaning for `могти`. Standard dictionary evidence includes possibility as well, and the summary later says `ability or possibility`, so the module contradicts itself.  
Fix: Replace that sentence with wording that includes possibility.

[1. Plan adherence] [SEVERITY: major]  
Location: `## Підсумок — Summary`  
Issue: The summary is substantially under its 270-330 section budget, and the pipeline note shows the whole module at 1186 words, below the 1200-word target.  
Fix: Add more concrete summary practice with additional Ukrainian model sentences, especially noun vs infinitive contrast and all three modals in guided production.

[3. Pedagogical quality] [SEVERITY: major]  
Location: `## Діалоги (Dialogues)` — `Olya and Denys are planning a weekend — negotiating what to do. Read their exchange to see how desires, availability, and obligations function in practice.`  
Location: `## Підсумок — Summary` — `Active practice is required to internalize these verb forms...` / `Building these sentences out loud bridges the gap...`  
Issue: These lines are meta-narrative/generic filler. They add English exposition where the module should give tighter teacher framing and more Ukrainian output models.  
Fix: Replace them with concise teacher prompts and additional Ukrainian practice lines.

## Verdict: REVISE
REVISE, not PASS. There is one critical factual grammar explanation to fix, and the module also misses the target length while underdelivering in the summary section. The problems are localized and can be corrected with surface edits; this does not require a full rebuild.

<fixes>
- find: "Olya and Denys are planning a weekend — negotiating what to do. Read their exchange to see how desires, availability, and obligations function in practice."
  replace: "Read this short weekend-planning dialogue. It shows **хочу**, **можу**, and **мушу** in a natural exchange."
- find: "This verb strictly denotes physical capability, availability, or receiving permission. You pair it with an infinitive to describe exactly what you are able to accomplish."
  replace: "This verb can express ability, possibility, availability, or permission. In this module, you will mostly pair it with an infinitive to describe what you are able to do."
- find: "Active practice is required to internalize these verb forms and bring them out of the textbook into daily life. Apply these grammatical structures to an actual daily routine. Ask yourself these practical self-check questions to measure your progress:"
  replace: "Now turn the pattern into your own sentences. First say one sentence with **хочу + infinitive**, then one with **можу + infinitive**, and then one with **мушу + infinitive**. After that, answer these self-check questions:"
- insert_after: "* Say what you must do tomorrow. Do you have a strict obligation to work all day, or to help a close friend?"
  text: " Practice once more with concrete Ukrainian. Say: **Я хочу каву**, but **я хочу їсти**. Then build a three-part sentence: **Я хочу гуляти, але не можу — мушу працювати.** Ask a partner: **Що ти хочеш робити сьогодні? Що ти можеш робити сьогодні? Що ти мусиш робити завтра?** Finally, change only the infinitive: **Хочу** читати. **Можу** допомогти. **Мушу** вчити слова. **Сьогодні я можу читати українською, а завтра я мушу працювати.**"
</fixes>
## Linguistic Scan
- `Могти і мусити (Can and Must)`: “After shifting to **ж** for most forms, the consonant reverts to the original **г** in the "they" form.” This is false. The standard present-tense paradigm is `можу, можеш, може, можемо, можете, можуть`; `вони можуть` still has `ж`.
- `Підсумок — Summary`: “The verb **могти** changes **г** to **ж** for most forms, but returns to **г** in the "they" form (**вони можуть**).” This repeats the same false grammar claim.

## Exercise Check
4 markers are present: `fill-in` after `Хотіти`, then `quiz`, `fill-in`, `quiz` after `Могти і мусити`. The count and type order match the four activity obligations, but the placement is uneven: `Діалоги` gets no immediate practice, while three markers are clustered right before `Підсумок`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All required H2 sections are present and the section budgets are on target (`Діалоги` 294, `Хотіти` 325, `Могти і мусити` 289, `Підсумок` 313), but the module breaks the contract’s irregular-pattern teaching point by claiming `вони можуть` “returns to г.” |
| 2. Linguistic accuracy | 6/10 | `Могти і мусити` and `Підсумок` both teach the wrong stem behavior for `могти`: the text says `вони можуть` returns to `г`, but the taught present-tense form is still `мож-`. |
| 3. Pedagogical quality | 7/10 | The opening of `Діалоги` spends too long in abstract English theory (`People constantly negotiate their time and actions...`) before giving learners the target Ukrainian, and the wrong `могти` explanation teaches a false rule. |
| 4. Vocabulary coverage | 9/10 | Core contract vocabulary is used naturally in prose and examples: `хочеш`, `робити`, `хочу`, `гуляти`, `можу`, `мушу`, `працювати`, `Шкода`, `каву`, `їсти`. |
| 5. Exercise quality | 7/10 | The module has the required four markers in the correct type order, but three are stacked after `Могти і мусити` and none follows `Діалоги`, so practice is not distributed well across the lesson. |
| 6. Engagement & tone | 6/10 | Several sentences are generic filler rather than substantive teacher talk, e.g. `People constantly negotiate their time and actions` and `Another practical application occurs every time you visit a restaurant.` |
| 7. Structural integrity | 9/10 | All four required H2 headings are present, in order, with clean markdown, and the pipeline word count is 1350, above the 1200 target. |
| 8. Cultural accuracy | 9/10 | The module stays in ordinary Ukrainian everyday contexts and avoids Russia-centered framing. |
| 9. Dialogue & conversation quality | 7/10 | The first dialogue is functional, but the section is padded with exposition and the café exchange is stiff (`І ще я хочу їсти. Що ви можете порекомендувати?`) instead of sounding like a natural A1 interaction. |

## Findings
- [LINGUISTIC ACCURACY] [SEVERITY: critical]
Location: `Могти і мусити (Can and Must)` — “Pay attention to the final form, **вони можуть**. After shifting to **ж** for most forms, the consonant reverts to the original **г** in the "they" form.”
Issue: This teaches the wrong present-tense pattern for `могти`. `вони можуть` keeps the `ж` stem.
Fix: Replace the sentence with an explanation that the present-tense stem is `мож-` throughout: `можу, можеш, може, можемо, можете, можуть`.

- [LINGUISTIC ACCURACY] [SEVERITY: critical]
Location: `Підсумок — Summary` — “The verb **могти** changes **г** to **ж** for most forms, but returns to **г** in the "they" form (**вони можуть**).”
Issue: The summary repeats the same false rule, reinforcing the error.
Fix: Replace it with a correct summary stating that the present-tense forms use `мож-`, including `вони можуть`.

- [PEDAGOGICAL QUALITY] [SEVERITY: major]
Location: `Діалоги (Dialogues)` — “People constantly negotiate their time and actions. Expressing wants, needs, and capabilities is essential.” / “Another practical application occurs every time you visit a restaurant.”
Issue: The section front-loads generic English exposition instead of moving quickly into the required Ukrainian dialogues and pattern extraction.
Fix: Rewrite the section to open directly with the two contract dialogues, then add a shorter explanation of `хотіти + infinitive` and `хотіти + noun`.

- [EXERCISE QUALITY] [SEVERITY: major]
Location: Marker sequence — one `<!-- INJECT_ACTIVITY: fill-in -->` after `Хотіти`, then `<!-- INJECT_ACTIVITY: quiz -->`, `<!-- INJECT_ACTIVITY: fill-in -->`, `<!-- INJECT_ACTIVITY: quiz -->` all after `Могти і мусити`.
Issue: Activity placement is bunched too late. `Діалоги` introduces all three target modals but gets no immediate retrieval practice.
Fix: Move the first `quiz` marker to the end of `Діалоги (Dialogues)` and leave two markers after `Могти і мусити`.

- [PEDAGOGICAL QUALITY] [SEVERITY: minor]
Location: `Підсумок — Summary` — “Can you list three things you can do? (**Я можу читати**, **я можу писати**).”
Issue: The prompt asks for three examples but models only two.
Fix: Add a third example.

## Verdict: REVISE
The module cannot pass because it contains a critical grammar error taught twice (`вони можуть` incorrectly described as reverting to `г`). It also has major pedagogical and exercise-placement issues, and several dimensions fall below 9.

<fixes>
- find: "Pay attention to the final form, **вони можуть**. After shifting to **ж** for most forms, the consonant reverts to the original **г** in the \"they\" form."
  replace: "Pay attention to the final form, **вони можуть**. The present-tense stem still uses **ж** here: **мож-** appears in **можу, можеш, може, можемо, можете, можуть**."
- find: "The verb **могти** changes **г** to **ж** for most forms, but returns to **г** in the \"they\" form (**вони можуть**)."
  replace: "The verb **могти** changes **г** to **ж** in the present tense, including the \"they\" form (**вони можуть**)."
- find: "The dictionary form is **кава** (coffee), but it changes its ending to **-у** because it is the direct object, showing the Accusative case.\n\n## Хотіти (To Want)"
  replace: "The dictionary form is **кава** (coffee), but it changes its ending to **-у** because it is the direct object, showing the Accusative case.\n\n<!-- INJECT_ACTIVITY: quiz -->\n\n## Хотіти (To Want)"
- find: "<!-- INJECT_ACTIVITY: quiz -->\n<!-- INJECT_ACTIVITY: fill-in -->\n<!-- INJECT_ACTIVITY: quiz -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in -->\n<!-- INJECT_ACTIVITY: quiz -->"
- find: "* Can you list three things you can do? (**Я можу читати**, **я можу писати**)."
  replace: "* Can you list three things you can do? (**Я можу читати**, **я можу писати**, **я можу говорити українською**)."
</fixes>

<rewrite-block section="Діалоги (Dialogues)">
Rewrite only this section. Keep the exact H2 heading. Open directly with the two required dialogues instead of generic English exposition. Preserve both contract scenarios: weekend planning with Оля and Денис, and the café exchange with хотіти + noun. Keep the required terms `хочеш`, `робити`, `хочу`, `гуляти`, `можу`, `мушу`, `працювати`, and `Шкода`. After the dialogues, add a short, concrete explanation of the two target patterns: `хотіти + infinitive` and `хотіти + noun` with `я хочу каву`.
</rewrite-block>
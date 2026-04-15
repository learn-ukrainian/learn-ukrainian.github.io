## Linguistic Scan
No linguistic errors found.

## Exercise Check
Inventory: 4 markers total.

Placement in prose:
- `<!-- INJECT_ACTIVITY: fill-in -->` after `## Хотіти (To Want)`
- `<!-- INJECT_ACTIVITY: quiz -->` and `<!-- INJECT_ACTIVITY: fill-in -->` after `## Могти і мусити (Can and Must)`
- `<!-- INJECT_ACTIVITY: quiz -->` after `## Підсумок — Summary`

The marker count and type sequence match the contract’s four activity obligations (`fill-in`, `quiz`, `fill-in`, `quiz`). No inline exercise-logic errors are visible from the prose-only markers.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 10/10 | All four required H2 sections are present and ordered correctly, both required dialogues are covered, and the section word counts are within budget: Dialogues `293`, Хотіти `321`, Могти і мусити `294`, Summary `312`. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, calques, bad case forms, or wrong conjugation claims found. The core paradigms used in the module match VESUM-verified forms: `хочу/хочеш/хоче`, `можу/можеш/може`, `мушу/мусиш/мусить`. |
| 3. Pedagogical quality | 8/10 | The module generally follows a good dialogue → pattern → practice flow, but the explanation `placing **кава** (coffee) in the accusative case` blurs the actual surface form `каву`, and the long Summary prompt beginning `Say what you must do tomorrow...` overloads too many tasks into one block. |
| 4. Vocabulary coverage | 10/10 | The required vocabulary appears naturally in prose and examples: `хочу`, `робити`, `гуляти`, `можу`, `мушу`, `працювати`, `каву`, `їсти`, `борщ`. |
| 5. Exercise quality | 9/10 | All four required markers are present in the required type sequence, and each appears after material that can support it: conjugation after `Хотіти`, modal-choice/fill-in after `Могти і мусити`, recap quiz after `Підсумок`. |
| 6. Engagement & tone | 9/10 | The teacher voice stays mostly concrete and classroom-usable, especially in prompts like `Now turn the pattern into your own sentences.` It avoids gamified fluff. |
| 7. Structural integrity | 8/10 | The structure is complete and the pipeline word count is safely above target at `1297`, but the Summary contains a stray indented bullet: ` * Build two more model sentences aloud...`, which is a formatting artifact. |
| 8. Cultural accuracy | 10/10 | The module presents Ukrainian on its own terms, with no Russia-centered framing and no dubious cultural claims. |
| 9. Dialogue & conversation quality | 9/10 | The weekend-planning dialogue is natural and multi-turn (`Що ти хочеш робити сьогодні?... Я не можу, я мушу працювати.`). The café dialogue is useful and serviceable, if slightly more functional than vivid. |

## Findings
[Pedagogical quality] [SEVERITY: major]  
Location: `## Діалоги (Dialogues)` — `Second, **я хочу каву** attaches the desire directly to a noun, placing **кава** (coffee) in the accusative case.`  
Issue: The explanation names the lemma `кава` at the exact point where the learner should see the surface accusative form `каву`. That weakens the case-teaching moment.  
Fix: Rewrite the sentence so it explicitly shows `кава → каву`.

[Pedagogical quality] [SEVERITY: major]  
Location: `## Підсумок — Summary` — `* Say what you must do tomorrow... Then add one noun pattern too... Say the full chain aloud... Then ask a partner...`  
Issue: One prompt bundles too many different tasks into a single A1 practice block: obligation, noun-vs-infinitive contrast, repetition, partner questions, and extra production. That reduces clarity and progression.  
Fix: Split the block into shorter bullets with one task per bullet.

[Structural integrity] [SEVERITY: minor]  
Location: `## Підсумок — Summary` — ` * Build two more model sentences aloud...`  
Issue: The leading space creates an unintended nested bullet / formatting artifact.  
Fix: Remove the leading space and keep it as a normal top-level bullet while splitting the long practice block.

## Verdict: REVISE
The module is linguistically clean and contract-compliant, but it still has fixable pedagogical/structural issues. The score gate also fails because not all dimensions are `≥9`.

<fixes>
- find: "Second, **я хочу каву** attaches the desire directly to a noun, placing **кава** (coffee) in the accusative case."
  replace: "Second, **я хочу каву** attaches the desire directly to a noun, putting the noun **кава** into the accusative as **каву**."

- find: |-
    * Say what you must do tomorrow. Do you have a strict obligation to work all day, or to help a close friend? Then add one noun pattern too: **Я хочу каву.** Contrast it with **Я хочу їсти.** Say the full chain aloud: **Я хочу гуляти, але не можу — мушу працювати.** Then ask a partner: **Що ти хочеш робити сьогодні? Що ти можеш робити сьогодні? Що ти мусиш робити завтра?**
     * Build two more model sentences aloud: **Я хочу каву, але не можу пити зараз — мушу працювати.** **Ми хочемо гуляти, але не можемо — мусимо вчити слова.** Then switch the subject each time: **я**, **ти**, **ми**. This keeps the three patterns together and reinforces the contrast between **хочу**, **можу**, and **мушу** before you move on.
  replace: |-
    * Say what you must do tomorrow. Do you have a strict obligation to work all day, or to help a close friend?
    * Add one noun pattern too: **Я хочу каву.** Contrast it with **Я хочу їсти.**
    * Say the full chain aloud: **Я хочу гуляти, але не можу — мушу працювати.** Then ask a partner: **Що ти хочеш робити сьогодні? Що ти можеш робити сьогодні? Що ти мусиш робити завтра?**
    * Build two more model sentences aloud: **Я хочу каву, але не можу пити зараз — мушу працювати.** **Ми хочемо гуляти, але не можемо — мусимо вчити слова.** Then switch the subject each time: **я**, **ти**, **ми**. This keeps the three patterns together and reinforces the contrast between **хочу**, **можу**, and **мушу** before you move on.
</fixes>
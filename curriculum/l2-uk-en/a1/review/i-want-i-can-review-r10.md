## Linguistic Scan
No linguistic errors found.

VESUM spot-checks confirm the finite forms used for `хотіти` (`хочу, хочеш, хоче, хочемо, хочете, хочуть`) and `мусити` (`мушу, мусиш, мусить, мусимо, мусите, мусять`). I found no Russianisms, Surzhyk, calques, paronym mistakes, or forbidden Russian characters in the Ukrainian prose.

## Exercise Check
Markers found: 4 total, in the required order: `fill-in`, `quiz`, `fill-in`, `quiz`.

Placement is logically acceptable:
- `<!-- INJECT_ACTIVITY: fill-in -->` appears after `## Хотіти (To Want)`, matching the conjugation focus.
- `<!-- INJECT_ACTIVITY: quiz -->` and `<!-- INJECT_ACTIVITY: fill-in -->` appear after `## Могти і мусити (Can and Must)`, which is the first point where all three modals are available for contrast and mixed-sentence completion.
- `<!-- INJECT_ACTIVITY: quiz -->` appears after `## Підсумок — Summary`, fitting the final pattern review.

No exercise logic issues are visible in the prose, and there are no inline DSL exercises to audit.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | The module covers the contract’s core beats with both dialogues, the `хочу + noun` vs `хочу + infinitive` contrast, and the anchor sentence `Я хочу гуляти, але не можу — мушу працювати.` The miss is structural: `## Підсумок — Summary` is 255 words, below the 270-word minimum. |
| 2. Linguistic accuracy | 10/10 | Ukrainian forms and grammar claims are clean: `я хочу / ти хочеш / вони хочуть`, `я можу / ти можеш / вони можуть`, `я мушу / ти мусиш / вони мусять`; accusative example `кава → каву` is correct. |
| 3. Pedagogical quality | 9/10 | The flow is sound: dialogue first, then `Хотіти`, then `Могти і мусити`, then recap. Each grammar point gets multiple examples such as `Я хочу читати`, `Я можу говорити українською`, `Я мушу працювати`. |
| 4. Vocabulary coverage | 10/10 | Required vocabulary is integrated naturally in prose and dialogue: `хочеш`, `робити`, `гуляти`, `можу`, `мушу`, `працювати`, `каву`, `їсти`, `можете`, `можуть`. |
| 5. Exercise quality | 9/10 | All four required markers are present in the correct type order `fill-in, quiz, fill-in, quiz`, and each sits after the material it is meant to test. |
| 6. Engagement & tone | 9/10 | The tone stays teacherly and concrete, with useful prompts like `Then ask a partner: Що ти хочеш робити сьогодні?` and no gamified or congratulatory filler. |
| 7. Structural integrity | 8/10 | Headings are correct and ordered, marker syntax is clean, and total word count is above target at 1233. The issue is that `## Підсумок — Summary` falls short of its section minimum. |
| 8. Cultural accuracy | 10/10 | The module presents Ukrainian on its own terms, uses Ukrainian grammatical terminology (`складений дієслівний присудок`), and avoids Russian-centric framing. |
| 9. Dialogue & conversation quality | 9/10 | The first dialogue is natural and multi-turn: `Що ти хочеш робити сьогодні? ... Я не можу, я мушу працювати. ... Завтра я вільна.` The café exchange is functional and aligned with the plan. |

## Findings
[Plan adherence / Structural integrity] [SEVERITY: major]  
Location: `## Підсумок — Summary` — the section ends after `Building these sentences out loud bridges the gap between recognizing a written word and actively speaking it. Consistent daily practice of these specific connections makes navigating everyday conversational plans a very straightforward process.`  
Issue: The summary section is 255 words, below the contract minimum of 270 words.  
Fix: Add one short guided-practice paragraph before the final quiz marker that recycles `хочу`, `можу`, `мушу`, and the noun-vs-infinitive contrast.

## Verdict: REVISE
REVISE. The module is linguistically clean and pedagogically solid, but PASS is blocked by a concrete contract violation: the summary section is under its required word budget, which drops both plan adherence and structural integrity below 9.

<fixes>
- insert_after: "Building these sentences out loud bridges the gap between recognizing a written word and actively speaking it. Consistent daily practice of these specific connections makes navigating everyday conversational plans a very straightforward process."
  insert: "One more quick check: say **Я хочу каву**, **Я можу говорити українською**, and **Я мушу працювати сьогодні** aloud. Then change each sentence to **ти**: **Ти хочеш каву?**, **Ти можеш говорити українською?**, **Ти мусиш працювати сьогодні?** This keeps the three modal patterns active while you compare noun and infinitive use."
</fixes>
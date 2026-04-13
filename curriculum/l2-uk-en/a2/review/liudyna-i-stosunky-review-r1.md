## Linguistic Scan
No Russianisms, Surzhyk, paronym errors, or Russian characters were confirmed.

Critical factual/usage error found:
- In the `:::tip` under `## Зовнішність: як виглядає людина?`, the module says `«Вона виглядає гарно»` is wrong and implies looking with the eyes. That is false. `виглядати` is a valid Ukrainian verb with the dictionary sense `мати певний зовнішній вигляд`, so this note teaches incorrect usage.

## Exercise Check
Marker inventory in the prose: 6 markers total.

- `fill-in-complete-sentences-describing-people-with-the-correct-adjective-form-agreement-for-gender` appears after the appearance section and matches the taught content.
- `group-sort-traits` and `match-up-definitions` appear after the character section and fit the plan.
- `quiz-aspect-choice` appears after the aspect box, but the plan’s quiz hint is adjective choice, not aspect choice.
- `fill-in-sentence-completion-with-adjectives` appears twice late in the module, so the marker set overweights fill-ins and no longer matches the four `activity_hints` cleanly.
- Markers are not evenly distributed because two extra fill-in markers are clustered in the second half.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All four planned H2 sections are present, but one planned exemplar pair is only half-covered (`блакитноокий` has 0 occurrences), and the quiz marker is `quiz-aspect-choice` instead of the planned adjective-choice quiz. |
| 2. Linguistic accuracy | 6/10 | Most Ukrainian is clean, but the tip claiming `«Вона виглядає гарно»` is wrong teaches false usage. |
| 3. Pedagogical quality | 6/10 | There are good contextual examples, but `Моя сестра завжди каже правду, тому вона мені довіряє.` is logically backwards for the point being taught, and `Моя нова колега дуже працьовитий спеціаліст` introduces agreement noise right after a simple agreement explanation. |
| 4. Vocabulary coverage | 8/10 | Required vocabulary is used repeatedly (`людина`, `характер`, `зовнішність`, `привітний`, `щирий`, `працьовитий`, `терплячий`, `сусід`, `описувати`), and recommended items like `впертий`, `чуйний`, `наполегливий`, `знайомий` appear, but the planned `блакитноокий` exemplar is not taught. |
| 5. Exercise quality | 5/10 | Markers usually follow teaching, but `quiz-aspect-choice` does not match the plan’s quiz focus, and duplicated fill-in markers distort the activity mix. |
| 6. Engagement & tone | 8/10 | The teacher voice is warm and specific; notes on `впертий` and `добра людина` add useful cultural color without gamified filler. |
| 7. Structural integrity | 8/10 | The module has all main sections and exceeds the target word count (pipeline: 2878), but duplicate fill-in markers leave the structure uneven. |
| 8. Cultural accuracy | 8/10 | The module is generally Ukrainian-centered, but the `виглядає гарно` note turns a culture/usage tip into misinformation. |
| 9. Dialogue & conversation quality | 8/10 | Dialogues are named and multi-turn, but the `довіряє` example reads forced to serve grammar rather than natural meaning. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `## Зовнішність: як виглядає людина?` tip — `When translating "She looks beautiful", do not use the literal «Вона виглядає гарно». In Ukrainian, this implies she is actively looking at something beautifully with her eyes!`  
Issue: This is factually wrong. `виглядати` is standard Ukrainian for “to look/appear” in the sense of outward appearance, so the module forbids a valid pattern and gives a false explanation.  
Fix: Replace the note so it presents `Вона гарно виглядає / Вона виглядає гарно` as natural options, alongside `Вона гарна` and `Вона має гарний вигляд`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## Зовнішність: як виглядає людина?` — `У неї сині очі, отже, вона синьоока.`  
Issue: The plan explicitly calls for the exemplar pair `кароокий/блакитноокий`; the module teaches `кароока` but never teaches `блакитноокий`.  
Fix: Replace the example with `У неї блакитні очі, отже, вона блакитноока.`

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: quiz-aspect-choice -->`  
Issue: The plan’s quiz hint is adjective completion (`Він завжди допомагає — він дуже ___`), but this marker requests an aspect-choice quiz.  
Fix: Replace the marker with an adjective-choice quiz marker.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: fill-in-sentence-completion-with-adjectives -->` appears twice, once after `## Люди навколо нас...` and again at the very end.  
Issue: The plan has one fill-in activity hint, but the module adds two extra late fill-in markers, skewing the exercise mix and clustering activities.  
Fix: Remove both duplicated `fill-in-sentence-completion-with-adjectives` markers and keep the earlier fill-in marker that already covers adjective agreement.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Моя сестра завжди каже правду, тому вона мені довіряє.`  
Issue: The grammar is fine, but the logic is backwards: telling the truth usually supports `я їй довіряю`, not `вона мені довіряє`. That weakens the case-pattern example.  
Fix: Replace it with a semantically natural dative example, e.g. `Моя сестра добре мене знає, тому вона мені довіряє.`

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `Моя нова колега дуже працьовитий спеціаліст, вона працює в нашому відділі.`  
Issue: This is not the right example immediately after teaching simple adjective agreement. The feminine referent plus masculine adjective/noun pattern adds unnecessary noise for A2 learners.  
Fix: Replace it with a straightforward feminine agreement example, e.g. `Моя нова колега — дуже працьовита спеціалістка, вона працює в нашому відділі.`

## Verdict: REVISE
`REVISE` because the module contains one critical linguistic/usage error that teaches false Ukrainian, plus multiple major plan/exercise/pedagogy issues. Several dimensions are below 9, and the errors are fixable with deterministic replacements.

<fixes>
- find: |
    When translating "She looks beautiful", do not use the literal «Вона виглядає гарно». In Ukrainian, this implies she is actively looking at something beautifully with her eyes! Instead, use «Вона гарна» (She is beautiful) or «Вона має гарний вигляд» (She has a good look). Also, avoid the Russian calque «самий високий» for "the tallest". The correct Ukrainian superlative uses the prefix **най-**, making it «найвищий».
  replace: |
    When translating "She looks beautiful", you can naturally say «Вона гарно виглядає», «Вона виглядає гарно», «Вона гарна», or «Вона має гарний вигляд», depending on the nuance you want. Also, avoid the Russian calque «самий високий» for "the tallest". The correct Ukrainian superlative uses the prefix **най-**, making it «найвищий».
- find: |
    У нього темне волосся, тому він темноволосий. У неї сині очі, отже, вона синьоока. Її брат має світле волосся, він світловолосий. Якщо людина має карі очі, ми кажемо, що вона кароока.
  replace: |
    У нього темне волосся, тому він темноволосий. У неї блакитні очі, отже, вона блакитноока. Її брат має світле волосся, він світловолосий. Якщо людина має карі очі, ми кажемо, що вона кароока.
- find: |
    <!-- INJECT_ACTIVITY: quiz-aspect-choice -->
  replace: |
    <!-- INJECT_ACTIVITY: quiz-choose-the-correct-adjective-to-complete-a-description -->
- find: |
    <!-- INJECT_ACTIVITY: fill-in-sentence-completion-with-adjectives -->
  replace: ""

- find: |
    <!-- INJECT_ACTIVITY: fill-in-sentence-completion-with-adjectives -->
  replace: ""

- find: |
    Моя сестра завжди каже правду, тому вона мені довіряє.
  replace: |
    Моя сестра добре мене знає, тому вона мені довіряє.
- find: |
    Моя нова колега дуже працьовитий спеціаліст, вона працює в нашому відділі.
  replace: |
    Моя нова колега — дуже працьовита спеціалістка, вона працює в нашому відділі.
</fixes>
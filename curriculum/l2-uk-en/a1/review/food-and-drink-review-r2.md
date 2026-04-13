## Linguistic Scan
- No Russianisms, Surzhyk, calques, paronym mistakes, or banned Russian letters (`ы э ё ъ`) found in the Ukrainian examples.
- Factually misleading lexicon note: `There is no separate word for quark.` This is too absolute. The repo’s ULP notes include `дома́шній сир` = `cottage cheese`, so the note should be softened.

## Exercise Check
- Found 4 markers: `match-up-food-drink`, `group-sort-food-drinks`, `fill-in-chunks`, `quiz-meals-dishes`.
- The marker set matches the 4 planned activity types semantically: match-up, group-sort, fill-in, quiz.
- `match-up-food-drink` is placed too early. Before that marker, `вода` occurs 0 times and `сік` occurs 0 times in the prose, but both are in the planned match-up.
- The other three markers are placed after the relevant teaching and are spread reasonably well.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The core outline is covered: meals, food categories, drinks, `з + noun` chunks, and iconic dishes all appear. But the plan references are not integrated into the prose: `ULP`, `Episodes 11-13`, and `State Standard 2024` occur 0 times in the module text. |
| 2. Linguistic accuracy | 8/10 | Ukrainian forms are clean and VESUM-backed, with no Russian letters. The weak point is the lexicon note: `There is no separate word for quark.` is too absolute and can misteach learners. |
| 3. Pedagogical quality | 8/10 | The module broadly follows PPP: dialogues first, then vocabulary, then chunk practice, then summary. But the first exercise marker appears before some of its target vocabulary is taught, which breaks teach-then-test sequencing. |
| 4. Vocabulary coverage | 9/10 | All required plan vocabulary appears in prose, including `їжа`, `напій`, `хліб`, `кава`, `чай`, `вода`, `молоко`, `сік`, `м'ясо`, `риба`, `суп`, `сніданок`, `обід`, `вечеря`. Recommended cultural items like `борщ`, `вареники`, `сало`, `сметана`, `компот` are also included. |
| 5. Exercise quality | 7/10 | There are 4 markers and the planned exercise types are represented, but `match-up-food-drink` is misordered: `вода` and `сік` are not taught before the learner reaches it. |
| 6. Engagement & tone | 9/10 | Tone is teacherly and concrete, with useful cultural detail around `борщ`, `вареники`, `сало`, and family meals. |
| 7. Structural integrity | 10/10 | All planned H2 sections are present and ordered correctly. Markdown is clean, and the deterministic word count `1658` is above the `1200` target. |
| 8. Cultural accuracy | 8/10 | The module stays Ukrainian-centered and avoids Russian comparison framing. The main cultural/lexical problem is the overgeneralized claim about `quark`/`сир`. |
| 9. Dialogue & conversation quality | 9/10 | Named speakers and plausible situations are present: breakfast with `Бабуся`/`Онучка`, meal talk, and cafe ordering. |

## Findings
[LINGUISTIC ACCURACY / CULTURAL ACCURACY] [SEVERITY: critical]  
Location: `Note that the word **сир** is uniquely used for both yellow hard cheese and soft quark (cottage cheese) in Ukrainian. There is no separate word for quark.`  
Issue: The second sentence is too absolute and can teach a misleading lexical fact. The repo’s local ULP notes use `дома́шній сир` for `cottage cheese`, so “no separate word” overstates the situation.  
Fix: Replace the note with a softer explanation that `сир` is broad and that learners may also hear `домашній сир` for cottage cheese.

[EXERCISE QUALITY / PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: match-up-food-drink -->` immediately after the Dialogues section.  
Issue: The planned match-up includes items such as `вода` and `сік`, but both occur 0 times before this marker. The exercise is testing vocabulary before it is taught.  
Fix: Move this marker to the Drinks section, after the core drinks vocabulary has been introduced.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: module-wide; the prose never cites the plan references.  
Issue: The plan explicitly lists `ULP Season 1, Episodes 11-13` and `State Standard 2024, Topic 3 (ресторан)`, but the module text never integrates or mentions them.  
Fix: Add one natural sentence in the cafe-ordering subsection that ties the dialogue to the State Standard restaurant situation and ULP episodes.

## Verdict: REVISE
REVISE — there is one critical factual lexicon issue and two major quality issues. Dimensions 1, 2, 3, 5, and 8 are below 9, so this cannot pass as-is.

<fixes>
- find: "Note that the word **сир** is uniquely used for both yellow hard cheese and soft quark (cottage cheese) in Ukrainian. There is no separate word for quark."
  replace: "Note that the word **сир** covers cheese broadly in Ukrainian, and cottage cheese may also be specified as **домашній сир**. Do not assume a one-to-one match with English cheese labels."

- find: |
    <!-- INJECT_ACTIVITY: match-up-food-drink -->

    ## Їжа (Food)
  replace: |
    ## Їжа (Food)

- find: "Dairy drinks are also very common. You already know молоко, but you should also recognize **кефір** (kefir)."
  replace: "<!-- INJECT_ACTIVITY: match-up-food-drink -->\n\nDairy drinks are also very common. You already know молоко, but you should also recognize **кефір** (kefir)."

- find: "Here is a short dialogue about ordering drinks in a cafe:"
  replace: "Here is a short dialogue about ordering drinks in a cafe, matching the restaurant situation in the State Standard 2024 and the cafe-ordering material in ULP Season 1, Episodes 11-13:"
</fixes>
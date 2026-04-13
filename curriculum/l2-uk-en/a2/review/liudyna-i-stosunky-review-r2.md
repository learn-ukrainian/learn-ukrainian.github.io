## Linguistic Scan
- Critical terminology error in the grammar box: `**Імперфектив (Imperfective):** ...` / `**Перфектив (Perfective):** ...` teaches nonstandard labels here; the standard learner-facing terms are `недоконаний вид` / `доконаний вид`.
- Critical translation error: `Моя сестра добре мене знає, тому вона мені довіряє.` is glossed as `My sister always tells the truth, so she trusts me.` The Ukrainian means “My sister knows me well, so she trusts me.”

## Exercise Check
- Marker inventory in the module prose is 4/4: `fill-in-complete-sentences-describing-people-with-the-correct-adjective-form-agreement-for-gender`, `group-sort-traits`, `match-up-definitions`, `quiz-choose-the-correct-adjective-to-complete-a-description`.
- Placement is mostly correct: the fill-in follows appearance/agreement teaching; the group-sort and match-up follow the character-adjective teaching.
- Major mapping problem: the module uses `<!-- INJECT_ACTIVITY: quiz-choose-the-correct-adjective-to-complete-a-description -->`, but the activity YAML does not define that ID. It defines `quiz-aspect-choice` and `fill-in-sentence-completion-with-adjectives` instead. As written, that exercise will not inject correctly.
- The existing adjective-completion activity in YAML matches the plan focus better than the broken marker target, so the fix is to retarget the marker to that existing exercise.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | The plan’s relationship vocabulary explicitly includes `родич`, but the prose says `Люди навколо нас — це наші рідні, колеги по роботі...` and never actually uses `родич` in the module body. |
| 2. Linguistic accuracy | 6/10 | The grammar box uses `Імперфектив / Перфектив`, and the gloss `My sister always tells the truth...` mistranslates `Моя сестра добре мене знає, тому вона мені довіряє.` |
| 3. Pedagogical quality | 7/10 | The module has good example density, but a grammar box that labels aspect as `Імперфектив / Перфектив` and a wrong English gloss both risk teaching the wrong thing. |
| 4. Vocabulary coverage | 8/10 | Required items like `людина`, `характер`, `зовнішність`, `привітний`, `щирий`, `працьовитий`, `терплячий`, `сусід`, `описувати` are used naturally, but `родич` from the plan’s relationship set is absent from the prose. |
| 5. Exercise quality | 5/10 | The marker `<!-- INJECT_ACTIVITY: quiz-choose-the-correct-adjective-to-complete-a-description -->` has no matching inline activity ID; YAML defines `quiz-aspect-choice` and `fill-in-sentence-completion-with-adjectives` instead. |
| 6. Engagement & tone | 8/10 | Teacher voice is warm and mostly substantive: `Let's look at a conversation...`, `Did you know?`, and the cultural note on `добра людина` work well without corporate/gamified fluff. |
| 7. Structural integrity | 9/10 | All four planned H2 sections are present and ordered correctly, and the pipeline word count is above target. |
| 8. Cultural accuracy | 9/10 | The module treats Ukrainian on its own terms and includes useful culture-facing framing such as `Calling someone a «добра людина»... is one of the highest compliments`. |
| 9. Dialogue & conversation quality | 9/10 | Dialogues are named-speaker, multi-turn, and tied to real situations: photos, workplace introductions, family descriptions. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Grammar box — `**Імперфектив (Imperfective):** Вона завжди підказує.` / `**Перфектив (Perfective):** Вона підказала мені вчора.`  
Issue: The module introduces aspect with nonstandard labels here. For A2 learners, the standard Ukrainian terms are `недоконаний вид` and `доконаний вид`.  
Fix: Replace `Імперфектив` with `Недоконаний вид` and `Перфектив` with `Доконаний вид`.

[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Relationship-pronoun paragraph — `Моя сестра добре мене знає, тому вона мені довіряє.` / `My sister always tells the truth, so she trusts me.`  
Issue: The English gloss is wrong and teaches the wrong meaning of `добре мене знає`.  
Fix: Change the translation to `My sister knows me well, so she trusts me.`

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `Люди навколо нас — це наші рідні, колеги по роботі та просто випадкові перехожі.`  
Issue: The plan’s relationship vocabulary includes `родич`, but the prose never actually uses that target word.  
Fix: Revise the sentence so `родичі` appears naturally in the prose.

[EXERCISE QUALITY] [SEVERITY: major]  
Location: Marker — `<!-- INJECT_ACTIVITY: quiz-choose-the-correct-adjective-to-complete-a-description -->`  
Issue: This ID does not exist in `activities/liudyna-i-stosunky.yaml`, so the exercise will not inject as written.  
Fix: Point the marker to the existing adjective-completion activity ID: `fill-in-sentence-completion-with-adjectives`.

## Verdict: REVISE
REVISE. There are critical teaching errors in the aspect terminology and one English gloss, plus a broken exercise marker that will prevent correct injection. The module is structurally sound and mostly salvageable, so this is not a full reject.

<fixes>
- find: |
    **Імперфектив (Imperfective):** Вона завжди підказує. *(She always helps/suggests — a habitual trait that makes her a helpful person).*
    **Перфектив (Perfective):** Вона підказала мені вчора. *(She helped/suggested yesterday — a one-time action showing her good character).*
  replace: |
    **Недоконаний вид (Imperfective):** Вона завжди підказує. *(She always helps/suggests — a habitual trait that makes her a helpful person).*
    **Доконаний вид (Perfective):** Вона підказала мені вчора. *(She helped/suggested yesterday — a one-time action showing her good character).*
- find: "> *My sister always tells the truth, so she trusts me. My manager is very serious, but he respects me as a professional. My parents live far away, however, they help us.*"
  replace: "> *My sister knows me well, so she trusts me. My manager is very serious, but he respects me as a professional. My parents live far away, however, they help us.*"
- find: |
    Кожна людина будує унікальні стосунки з іншими. Люди навколо нас — це наші рідні, колеги по роботі та просто випадкові перехожі. Ми часто описуємо цих людей, коли розповідаємо про свій день.
  replace: |
    Кожна людина будує унікальні стосунки з іншими. Люди навколо нас — це наші родичі, рідні, колеги по роботі та знайомі. Ми часто описуємо цих людей, коли розповідаємо про свій день.
- find: "<!-- INJECT_ACTIVITY: quiz-choose-the-correct-adjective-to-complete-a-description -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in-sentence-completion-with-adjectives -->"
</fixes>
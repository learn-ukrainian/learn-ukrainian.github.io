## Linguistic Scan
- Factual grammar error in the aspect section: `There is a strict rule for negative imperatives...` and the grammar box `Perfective negative commands are only for accidental dangers...` overstate the rule. Local textbook search in the repo returns `Не/забудьте принести книги`, a perfective negative imperative used as a reminder, not an accidental-danger warning.

## Exercise Check
- Marker inventory: 5 markers found.
- `fill-in-form-the-correct-imperative-3rd-person-with-or-1st-plural-with-from-given-infinitives` appears after the 3rd-person section, but its own ID says it tests 1st-plural `-мо` too, which is taught only in the next section.
- The module therefore has 5 markers for 4 planned `activity_hints`; the extra custom marker is `fill-in-1st-plural-imperative-mo`.
- `match-up-vocative-wishes`, `quiz-aspect-choice`, and `unjumble-imperative-sentences` are placed after relevant teaching.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | All four planned sections are present and the required/recommended vocabulary is covered, but the activity plan is over-implemented: there are 5 markers for 4 `activity_hints`, and the combined fill-in marker appears before the 1st-plural section. |
| 2. Linguistic accuracy | 6/10 | The Ukrainian forms themselves are solid and VESUM-safe, but the aspect section incorrectly claims `There is a strict rule for negative imperatives...` and `Perfective negative commands are only for accidental dangers...`. |
| 3. Pedagogical quality | 6/10 | Example density is good, but the `-мо` explanation is internally inconsistent: it says `ends in a consonant` and then illustrates with `роби`, `скажи`; the negative-imperative rule is also oversimplified. |
| 4. Vocabulary coverage | 10/10 | All required plan vocabulary appears in prose, and all recommended items are also used naturally: `спокійний`, `уважний`, `живи`, `здійснитися`, `мрія`. |
| 5. Exercise quality | 6/10 | Marker spread is mostly good, but the first fill-in tests future content by ID, and the module contains one extra fill-in marker beyond the 4 planned activities. |
| 6. Engagement & tone | 7/10 | The cooking-class framing and wishes/toasts material help, but there is filler such as `This is a very simple and logical rule` and `Such words make our life much brighter and warmer.` |
| 7. Structural integrity | 9/10 | Clean H2 structure, correct section order, no dangling fragments, and pipeline word count is 2998, above target. |
| 8. Cultural accuracy | 9/10 | The wishes/toasts section grounds the grammar in Ukrainian usage and does not center Russian comparisons. |
| 9. Dialogue & conversation quality | 7/10 | Named speakers and a concrete setting help, but the dialogue is brief and mostly functional rather than vivid or conversationally rich. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: Aspect section — `There is a strict rule for negative imperatives: negative commands almost exclusively use the imperfective aspect.` and `Perfective negative commands are only for accidental dangers: «Не впади!»`  
Issue: This teaches a false rule. Ukrainian also uses perfective negative imperatives for one-time reminders/prevention, not only danger warnings; local textbook search returned `Не/забудьте принести книги`.  
Fix: Rephrase this as a tendency: imperfective is common for prohibitions, but perfective is also possible for warnings and one-time reminders.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: 1st-plural section — `If the base imperative form for "you" ends in a consonant...` followed by examples `роби`, `скажи`.  
Issue: The stated condition does not match the examples, so the formation rule is confusing.  
Fix: Replace it with an example-based explanation: some verbs insert `-і-` before `-мо` (`роби → робімо`, `скажи → скажімо`), while forms ending in `-ь` keep it (`сядь → сядьмо`, `поїдь → поїдьмо`).

[EXERCISE QUALITY] [SEVERITY: major]  
Location: `<!-- INJECT_ACTIVITY: fill-in-form-the-correct-imperative-3rd-person-with-or-1st-plural-with-from-given-infinitives -->` after the first section.  
Issue: By its own ID, this activity tests 1st-plural `-мо` before that pattern is taught.  
Fix: Move the combined fill-in marker to after the 1st-plural section.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: Marker inventory — both `fill-in-form-the-correct-imperative-3rd-person-with-or-1st-plural-with-from-given-infinitives` and `fill-in-1st-plural-imperative-mo`.  
Issue: The plan has 4 `activity_hints`, but the module has 5 markers because the fill-in activity has been duplicated/split.  
Fix: Remove the early marker and reuse the planned combined fill-in marker after section 2 in place of the extra custom marker.

[PEDAGOGICAL QUALITY] [SEVERITY: minor]  
Location: Aspect section opening — `You know to say **ходімо** ... rather than the borrowed **давайте**...`  
Issue: This contradicts the earlier section, which correctly presents `давайте` as a common softer suggestion, and it needlessly devalues a form the module itself teaches.  
Fix: Rephrase it to contrast compact synthetic `ходімо` with `давайте` as a common softer alternative.

## Verdict: REVISE
Critical grammar inaccuracy plus major exercise-placement and explanation problems. This fails the severity gate for PASS.

<fixes>
- find: "<!-- INJECT_ACTIVITY: fill-in-form-the-correct-imperative-3rd-person-with-or-1st-plural-with-from-given-infinitives -->"
  replace: ""
- find: "<!-- INJECT_ACTIVITY: fill-in-1st-plural-imperative-mo -->"
  replace: "<!-- INJECT_ACTIVITY: fill-in-form-the-correct-imperative-3rd-person-with-or-1st-plural-with-from-given-infinitives -->"
- find: "If the base imperative form for \"you\" ends in a consonant instead of a vowel, the transformation process is just as straightforward. When the basic command ends in a hard consonant, the connecting vowel **-і-** naturally appears before the **-мо** suffix to make the word easier to pronounce. If the command form ends in a soft consonant, indicated by a soft sign, you keep that soft sign and attach the **-мо** ending directly after it."
  replace: "Some common verbs change slightly before **-мо**, so it is best to learn this pattern through real examples. Some forms insert **-і-** before **-мо**: «роби → робімо», «скажи → скажімо». If the imperative already ends in **-ь**, you keep that soft sign and add **-мо**: «сядь → сядьмо», «поїдь → поїдьмо»."
- find: "You know to say **ходімо** (let's go) for joint actions, rather than the borrowed **давайте** (let's — suggestion particle). We will see that aspect also affects how we suggest doing things together."
  replace: "You know the compact synthetic form **ходімо** (let's go) for joint actions, while **давайте** (let's — suggestion particle) remains a common softer alternative. We will see that aspect also affects how we suggest doing things together."
- find: "There is a strict rule for negative imperatives: negative commands almost exclusively use the imperfective aspect. Telling someone NOT to do something implies an ongoing prohibition or stopping a process that is currently happening."
  replace: "Negative commands often use the imperfective aspect, especially for general prohibitions or for stopping a process that is already in progress. However, perfective negative imperatives are also possible for one-time warnings or reminders, for example «Не впади!» and «Не забудьте принести книги!». "
- find: "В українській мові негативні накази майже завжди мають недоконаний вид. Коли ми хочемо зупинити дію, ми кажемо: «Не читай це!». Ми також кажемо: «Не відкривайте вікно!». Навіть якщо дія разова, правило залишається суворим. Ми ніби кажемо людині не починати або не продовжувати цей процес. Це звучить природно і правильно для будь-якої заборони."
  replace: "В українській мові негативні накази часто мають недоконаний вид: «Не читай це!», «Не відкривайте вікно!». Але доконаний вид теж вживається для застереження або разового нагадування: «Не впади!», «Не забудьте принести книги!». Тому це не суворе правило, а загальна тенденція."
- find: "Perfective negative commands are only for accidental dangers: «Не впади!» (Don't fall — careful!)."
  replace: "Perfective negative commands can also appear in one-time warnings or reminders: «Не впади!» (Don't fall — careful!), «Не забудьте принести книги!» (Don't forget to bring the books!)."
</fixes>
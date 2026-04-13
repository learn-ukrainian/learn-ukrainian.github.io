## Linguistic Scan
No linguistic errors found.

VESUM spot checks confirm the core forms I was unsure about, including `стільці`, `крісла`, `дзеркала`, `підручники`, `столах`, and `вікон`. I found no verified Russianisms, Surzhyk, calques, paronym errors, or false grammar claims in the Ukrainian itself.

## Exercise Check
All 4 planned exercise markers are present.

- `group-sort-singular-plural`
- `fill-in-make-it-plural`
- `quiz-choose-correct-plural`
- `fill-in-adjective-agreement`

They appear after the relevant teaching sections, and each marker matches a plan `activity_hints` type/focus. No marker-level logic problems are visible from the prose alone.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 7/10 | Strong coverage of `стіл → столи`, `книга → книги`, `вікно → вікна`, adjective plural, and `ці / ті / мої`, but on reread the planned classroom model `дошка → дошки` never appears; the only related form is singular `бі́ля до́шки`. The pipeline word count is also 989, below the 1200 target. |
| 2. Linguistic accuracy | 10/10 | No verified Russianisms/Surzhyk/calques/paronym errors. Spot-checked Ukrainian forms are valid. |
| 3. Pedagogical quality | 6/10 | The explanation is clear, but the follow-up classroom dialogue jumps to untaught oblique plural cases: `а крі́сла — біля столі́в`, `Підручники на стола́х`, `А карти біля ві́кон`. That muddies a nominative-plural lesson. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary appears in prose: `столи`, `книги`, `вікна`, `стільці`, `ці`, `ті`, `мої`, `які`. Recommended items like `ручки`, `сумки`, `лампи`, `зошити`, `дзеркала`, `крісла`, `речі` also appear. |
| 5. Exercise quality | 9/10 | All planned markers are present and placed after the relevant teaching: three plural-noun markers after `Один → багато`, then adjective agreement after `Прикметники у множині`. |
| 6. Engagement & tone | 7/10 | Teacherly tone is mostly solid, but author-side scaffolding leaks into learner-facing text: `To make the classroom situation match the plan more closely, add a short follow-up exchange:` and `Keep the summary practical.` |
| 7. Structural integrity | 4/10 | The H2 structure is complete and ordered correctly, but the module is only 989 words, below target, and it contains meta-commentary rather than clean lesson prose. |
| 8. Cultural accuracy | 10/10 | No Russian-centric framing or cultural inaccuracies. Ukrainian is presented on its own terms. |
| 9. Dialogue & conversation quality | 8/10 | Two named-speaker dialogues in plausible settings do embed the target grammar in context, especially `Які ручки? Черво́ні чи си́ні?` and `Столи вели́кі й нові́.` |

## Findings
[PLAN ADHERENCE] [SEVERITY: major]  
Location: `> **Вчитель:** Добре, працю́ємо да́лі. Оди́н стілець тут, а два стільці там. Одне́ крі́сло бі́ля до́шки, а крі́сла — біля столі́в. Де підру́чники і ка́рти?`  
Issue: This follow-up never actually gives the planned `дошка → дошки` model. On reread, the module uses only singular `до́шки` in `бі́ля до́шки`, not nominative plural `дошки`.  
Fix: Rewrite the follow-up so it explicitly models `дошка → дошки`.

[PEDAGOGICAL QUALITY] [SEVERITY: major]  
Location: `а крі́сла — біля столі́в`, `Підручники на стола́х.`, `А карти біля ві́кон.`  
Issue: The lesson objective is nominative plural, but this dialogue introduces locative/genitive plural forms before they are taught. That expands scope and risks confusing A1 learners.  
Fix: Replace those lines with nominative-only singular/plural contrasts and simple location-free inventory sentences.

[STRUCTURAL INTEGRITY] [SEVERITY: major]  
Location: `PIPELINE NOTE — Word count: 989 words`  
Issue: The module is 211 words below the required 1200-word target.  
Fix: Add another guided practice paragraph in the summary section with extra plural drills using `ці`, `ті`, `мої`, and the core noun patterns.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `To make the classroom situation match the plan more closely, add a short follow-up exchange:`  
Issue: This is author/editor scaffolding, not learner-facing lesson prose.  
Fix: Replace it with a normal introduction to the follow-up dialogue.

[ENGAGEMENT & TONE] [SEVERITY: minor]  
Location: `Keep the summary practical.`  
Issue: This is another author note leaking into the published lesson voice.  
Fix: Replace it with a learner-facing summary lead-in.

## Verdict: REVISE
No verified Ukrainian language errors, but there are still ship-blocking quality issues: the module is under target length, and the classroom follow-up goes out of scope by teaching oblique plural cases while still missing the planned `дошка → дошки` model. The meta-authorial sentences should also be cleaned up.

<fixes>
- find: "To make the classroom situation match the plan more closely, add a short follow-up exchange:"
  replace: "Here is a short follow-up exchange with more classroom objects:"

- find: "> **Вчитель:** Добре, працю́ємо да́лі. Оди́н стілець тут, а два стільці там. Одне́ крі́сло бі́ля до́шки, а крі́сла — біля столі́в. Де підру́чники і ка́рти?\n> **У́чень 1:** Підручники на стола́х.\n> **Учень 2:** А карти біля ві́кон.\n> **Вчитель:** Чудо́во. Тепе́р у нас є столи, стільці, крісла, підручники і карти."
  replace: "> **Вчитель:** Добре, працюємо далі. Тут один стіл, а тут столи. Тут одна дошка, а там дошки. Тут одне крісло, а там крісла.\n> **Учень 1:** А де підручники і карти?\n> **Учень 2:** Підручники тут. Карти теж тут.\n> **Вчитель:** Чудово. Тепер у нас є столи, стільці, дошки, крісла, підручники і карти."

- find: "Keep the summary practical. First say the noun pair out loud: **стіл → столи**, **книга → книги**, **вікно → вікна**, **крісло → крісла**."
  replace: "For a practical review, first say each noun pair out loud: **стіл → столи**, **книга → книги**, **вікно → вікна**, **крісло → крісла**."

- insert_after: "Say each model once slowly and once at normal speed so the plural ending becomes automatic."
  content: "\n\nOne more short practice round can help lock in the pattern. Imagine you open the door of a classroom and describe what you see in short plural sentences: **Ці столи великі. Ті стільці старі. Ці книги нові. Ті вікна чисті. Мої зошити сині. Мої ручки червоні.** Then go back to the singular and say the pair again: **стіл — столи, книга — книги, вікно — вікна, дошка — дошки, крісло — крісла**. This is a useful habit because Ukrainian noun plurals do not all use one ending. Some common words follow **-и**: **столи, книги, ручки, сумки, лампи**. Some follow **-і**: **стільці, речі**. Many neuter nouns in **-о** form plurals in **-а**: **вікна, крісла, дзеркала**. Now turn the same vocabulary into questions and answers: **Які столи? — Великі й нові. Які стільці? — Старі. Які вікна? — Чисті.** You can also do a quick sorting drill aloud. Put singular words in one group: **стіл, книга, вікно, дошка, крісло**. Put plural words in another: **столи, книги, вікна, дошки, крісла**. Then add adjectives to the plural group only: **великі столи, нові книги, чисті вікна, старі дошки, нові крісла**. This final step matters because it reminds you that noun endings can change in different ways, but the plural adjective ending stays regular."
</fixes>
## Linguistic Scan
No linguistic errors found.

## Exercise Check
- `<!-- INJECT_ACTIVITY: fill-in-invitations -->`: Placed immediately after `Діалоги`. This tests frequency items ("Я ніколи не", "двічі на тиждень") BEFORE they are taught in the `Як часто?` section.
- `<!-- INJECT_ACTIVITY: match-up-hobbies -->`: Correctly placed after `Хобі і спорт`.
- `<!-- INJECT_ACTIVITY: preposition-check -->`: Correctly placed after `Хобі і спорт`.
- `<!-- INJECT_ACTIVITY: fill-in-frequency -->`: Correctly placed after `Як часто?`.
- **Issue**: The plan only specifies 3 activity hints. The writer injected 4 markers. The first marker is premature and redundant.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missed the required vocabulary chunk `дивитися фільми / серіали (to watch movies/series)` replacing it with `готувати`. Failed to combine "weather" in the final synthesized examples. |
| 2. Linguistic accuracy | 10/10 | All Ukrainian text is grammatically correct. Zero Russianisms, Surzhyk, or Calques. `у/в` and `на` rules are correctly applied. |
| 3. Pedagogical quality | 10/10 | Excellent breakdown of `в` (buildings) vs `на` (events), and `грати у` (sports) vs `грати на` (instruments). Clear explanation of the double negative rule for `ніколи`. |
| 4. Vocabulary coverage | 10/10 | All required words (`вихідні`, `спорт`, `футбол`, `кіно`, `часто`, `іноді`, `рідко`, `ходімо`) and recommended words (`завжди`, `зазвичай`, `ніколи`, `театр`, `концерт`, `музей`, `давай`, `раз`) are used naturally in context. |
| 5. Exercise quality | 7/10 | Four markers were injected for three plan hints. The `fill-in-invitations` marker was placed prematurely before frequency adverbs were taught. |
| 6. Engagement & tone | 8/10 | Used the forbidden gamified phrase "You now possess..." in the summary section. Otherwise, tone is encouraging and clear. |
| 7. Structural integrity | 10/10 | Word count is exactly 1257 words (exceeds 1200 target). All H2 sections match the plan outline. Clean Markdown formatting. |
| 8. Cultural accuracy | 10/10 | Decolonized approach. Accurate presentation of standard Ukrainian structures (`Ходімо`) vs informal (`Давай`). |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are natural, use names, and model real communicative situations effectively ("Що ти робиш у вихідні?"). |

## Findings
[Plan adherence] [Major]
Location: `Хобі і спорт — Що ти любиш?` section, bulleted list of activities.
Issue: The plan required introducing `дивитися фільми / серіали (to watch movies/series)`, but the writer substituted it with `готувати (to cook)`.
Fix: Replace `готувати` with `дивитися фільми / серіали`.

[Plan adherence] [Major]
Location: `Як часто? — Прислівники частоти` section, final bulleted examples.
Issue: The plan requested to "Combine all A1.4 skills: time + day + weather + activities". The examples successfully combine time, day, and activities, but omit weather entirely.
Fix: Update the bulleted examples to include time ("о п'ятій") and a weather condition ("Коли у п'ятницю йде дощ").

[Exercise quality] [Major]
Location: After the `Діалоги` section.
Issue: The `<!-- INJECT_ACTIVITY: fill-in-invitations -->` marker is placed before the `Як часто?` section. The corresponding plan activity tests frequency adverbs ("ніколи", "двічі на тиждень"), meaning the learner would be tested on untaught concepts. Additionally, the plan only specifies 3 activities, but 4 markers were injected.
Fix: Remove the premature `fill-in-invitations` marker. The remaining 3 markers perfectly match the 3 plan hints.

[Engagement & tone] [Minor]
Location: First sentence of the `Підсумок — Summary` section.
Issue: The phrase "You now possess the essential tools..." uses corporate/gamified language explicitly forbidden by the review rubric.
Fix: Replace with "You are now ready to discuss...".

## Verdict: REVISE
The module is linguistically flawless and features excellent pedagogical explanations for verbs of motion and prepositions. However, it requires minor revisions to align perfectly with the plan (adding missing vocabulary, integrating weather into examples, and removing a premature exercise marker) and fixing a single tone violation.

<fixes>
- find: "*(Sometimes I listen to music and draw.)*\n\n<!-- INJECT_ACTIVITY: fill-in-invitations -->\n\n## Хобі і спорт — Що ти любиш?"
  replace: "*(Sometimes I listen to music and draw.)*\n\n## Хобі і спорт — Що ти любиш?"
- find: "* **читати книги** (to read books)\n* **малювати вдома** (to draw at home)\n* **фотографувати** (to take photos)\n* **готувати** (to cook)"
  replace: "* **читати книги** (to read books)\n* **малювати вдома** (to draw at home)\n* **фотографувати** (to take photos)\n* **дивитися фільми / серіали** (to watch movies/series)"
- find: "* **У понеділок я завжди займаюся спортом.** (On Monday I always practice sports.)\n* **У п'ятницю ми часто ходимо в театр.** (On Friday we often go to the theater.)"
  replace: "* **У понеділок о п'ятій я завжди займаюся спортом.** (On Monday at five I always practice sports.)\n* **Коли у п'ятницю йде дощ, ми часто ходимо в театр.** (When it rains on Friday, we often go to the theater.)"
- find: "You now possess the essential tools to discuss your free time, hobbies, and weekend plans in Ukrainian."
  replace: "You are now ready to discuss your free time, hobbies, and weekend plans in Ukrainian."
</fixes>

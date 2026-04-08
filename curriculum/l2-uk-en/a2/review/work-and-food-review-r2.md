## Linguistic Scan
Linguistic errors found:
1. **Calque (Syntactic)**: 4 uses of "Давайте" + verb in the imperative sense (e.g., "Давайте прочитаємо"). This is a recognized Russianism/calque. The correct Ukrainian form is the 1st person plural imperative ("Прочитаймо", "Поговорімо").
2. **Calque (Lexical)**: 1 use of "знаходиться" to mean "is located" ("Мій офіс знаходиться між..."). In Ukrainian, "знаходитися" primarily means "to be found" after being lost. For spatial location, "розташований" or just "є/стоїть" is the correct form.

## Exercise Check
All exercise markers are present and correctly mapped to the plan:
- `<!-- INJECT_ACTIVITY: match-professions -->` matches `match-up` (Match profession questions).
- `<!-- INJECT_ACTIVITY: recipe-fill-in -->` matches `fill-in` (Complete a recipe description).
- `<!-- INJECT_ACTIVITY: true-false-workday -->` matches `true-false` (Workday Instrumental forms).
- `<!-- INJECT_ACTIVITY: review-instrumental -->` matches `quiz` (Identify function).
They are evenly distributed and placed perfectly after their respective teaching sections.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The text misses 3 specific phrases requested in the `content_outline`: "поливати олією", "між нарадами", "за розкладом". However, it does a great job with all the other requirements. |
| 2. Linguistic accuracy | 8/10 | The text contains 4 instances of the Russian syntactic calque "Давайте + [verb]" instead of the proper Ukrainian imperative. It also contains one instance of "знаходиться" for physical location instead of "розташований". |
| 3. Pedagogical quality | 10/10 | Superb step-by-step TBL/PPP flow. Grammar rules are effectively explained with immediate, practical examples (e.g., the explanation of the feminine noun "сіль" with a soft consonant is clear and helpful). |
| 4. Vocabulary coverage | 10/10 | All required vocabulary is naturally integrated into the text (готувати, різати, мішати, посипати, подавати, вареники, картопля, помідор, огірок, сіль, олія, виделка). |
| 5. Exercise quality | 10/10 | Markers perfectly correspond to the plan's `activity_hints` and are placed logically after the concept has been taught. |
| 6. Engagement & tone | 10/10 | Natural teacher persona ("Уявіть ситуацію...", "Разом подивімося..."). Not corporate and not patronizing. |
| 7. Structural integrity | 10/10 | Clean markdown, precise headers, no stray formatting. Word count (2653) easily exceeds the target of 2000. |
| 8. Cultural accuracy | 10/10 | Strongly emphasizes avoiding Russian calques for professions ("кухар", not "повар") and correctly distinguishes "олія" vs "масло" and the broad use of "сир". |
| 9. Dialogue & conversation quality | 10/10 | The dialogues are realistic and incorporate appropriate communicative reactions ("Справді?", "Я теж!"). |

## Findings

[1. Plan adherence] [minor]
Location: Section "На кухні: Готуємо разом"
Issue: The plan explicitly required teaching "поливати олією" alongside "посипати сіллю", but it was omitted.
Fix: Add "або «поливати олією» (to drizzle with oil)" to the end of the sentence about salt.

[1. Plan adherence] [minor]
Location: Section "Мій робочий день"
Issue: The plan explicitly required combining prepositions "між нарадами" and "за розкладом" in the workday description, but they were omitted.
Fix: Insert these phrases into the Manager's vlog dialogue.

[2. Linguistic accuracy] [major]
Location: Section "На кухні", Section "Мій робочий день", Section "Практика"
Issue: Four instances of the Russian syntactic calque "Давайте" + verb (e.g., "Давайте уважно прочитаємо", "Давайте разом подивимося"). This is an unnatural construction in educational Ukrainian material.
Fix: Replace with the Ukrainian 1st person plural imperative ("Уважно прочитаймо", "Разом подивімося", etc.).

[2. Linguistic accuracy] [major]
Location: Section "Практика", Dialogue
Issue: Use of "знаходиться" to mean "is located" ("Мій офіс знаходиться між..."). This is a widely recognized lexical calque from Russian.
Fix: Replace with "розташований".

## Verdict: REVISE
The module is overall excellent, with deep cultural notes and solid grammar instruction. However, the presence of grammatical and lexical calques ("давайте", "знаходиться") and a few missing plan phrases require a revision.

<fixes>
- find: "Давайте уважно прочитаємо діалог двох хороших друзів. *(Let's carefully read a dialogue of two good friends.)*"
  replace: "Уважно прочитаймо діалог двох хороших друзів. *(Let's carefully read a dialogue of two good friends.)*"
- find: "Тепер давайте детально поговоримо про наш типовий **робочий день** (workday)."
  replace: "Тепер детально поговорімо про наш типовий **робочий день** (workday)."
- find: "Давайте разом подивимося короткий відеоблог про типовий день менеджера. *(Let's watch a short vlog about a manager's typical day together.)*"
  replace: "Разом подивімося короткий відеоблог про типовий день менеджера. *(Let's watch a short vlog about a manager's typical day together.)*"
- find: "А тепер давайте попрактикуємо ці конструкції в реальній розмові. *(And now let's practice these constructions in a real conversation.)*"
  replace: "А тепер попрактикуймо ці конструкції в реальній розмові. *(And now let's practice these constructions in a real conversation.)*"
- find: "В орудному відмінку ми кажемо **«посипати сіллю»** (to sprinkle with salt)."
  replace: "В орудному відмінку ми кажемо **«посипати сіллю»** (to sprinkle with salt) або **«поливати олією»** (to drizzle with oil)."
- find: "> — **Менеджер:** Ввечері я повертаюся додому машиною. *(In the evening I return home by car.)*"
  replace: "> — **Менеджер:** Я завжди працюю **за розкладом** (according to schedule), а **між нарадами** (between meetings) п'ю каву.\n> — **Менеджер:** Ввечері я повертаюся додому машиною. *(In the evening I return home by car.)*"
- find: "Мій офіс знаходиться **між** (between) банком і парком."
  replace: "Мій офіс розташований **між** (between) банком і парком."
</fixes>

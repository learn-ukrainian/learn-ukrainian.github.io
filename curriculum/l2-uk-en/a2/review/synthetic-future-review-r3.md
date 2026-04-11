## Linguistic Scan
No linguistic errors found. The text uses accurate terminology, correct verb conjugations, and natural Ukrainian phrasing.

## Exercise Check
All 4 plan-specified exercise markers are present. However, three of them (`fill-in-future-forms`, `quiz-aspect-choice`, `unjumble-future-sentences`) are heavily clustered at the very end of the content right before the summary section. These must be spread out evenly to test concepts directly after they are taught.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The text replaced `здасть іспит` with `складе свій іспит` in the first dialogue. While `скласти іспит` is standard formal Ukrainian, the plan explicitly required `здати→здам` in its motivation section to demonstrate the irregular conjugation of `дати` in the perfective future. |
| 2. Linguistic accuracy | 10/10 | No Russianisms, Surzhyk, or calques found. Good, clear explanations of grammar and aspect. |
| 3. Pedagogical quality | 10/10 | Excellent breakdown of the difference between simple and compound future. The explicit warning about the "я буду написати" mistake is brilliant and extremely helpful for learners. |
| 4. Vocabulary coverage | 10/10 | All required and recommended words from the plan are included naturally in context. |
| 5. Exercise quality | 7/10 | The module includes all required exercise markers, but three of them are clustered sequentially at the very end without any intervening content, disrupting the pacing. |
| 6. Engagement & tone | 10/10 | The tone is highly encouraging and uses clear, practical examples. The instructional bilingual structure works well here. |
| 7. Structural integrity | 10/10 | Word count is 2995 words (well above the 2000 minimum). All required headers are present. |
| 8. Cultural accuracy | 10/10 | Authentic examples and dialogue situations (New Year resolutions, making weekend plans). |
| 9. Dialogue & conversation quality | 10/10 | The dialogues are natural, appropriately contextualized, and provide clear examples of aspect usage. |

## Findings

[1. Plan adherence] [major]
Location: Dialogue in "Простий майбутній час" section — "А Олена **складе** свій іспит. *(He will read fifty books! And Olena will pass her exam.)*"
Issue: The generator replaced the plan's requested "здасть іспит" with "складе свій іспит". While stylistically preferred for writing, it completely missed the plan's explicit pedagogical motivation to demonstrate the irregular conjugation `здати→здам` in the future tense.
Fix: Change `складе` back to `здасть` to fulfill the plan's objective.

[5. Exercise quality] [major]
Location: End of the module, right before `## Підсумок`
Issue: Three exercise markers (`fill-in-future-forms`, `quiz-aspect-choice`, `unjumble-future-sentences`) are clustered sequentially at the very end of the module.
Fix: Distribute `fill-in-future-forms` and `quiz-aspect-choice` earlier in the "Як обрати вид для майбутнього" section to improve pacing.

## Verdict: REVISE
The content is excellent linguistically and pedagogically, but the exercise clustering and the deviation from the plan's specific morphological target ("здати->здам") require fixes.

<fixes>
- find: "— **Анна:** Він **прочитає** п'ятдесят книг! А Олена **складе** свій іспит. *(He will read fifty books! And Olena will pass her exam.)*"
  replace: "— **Анна:** Він **прочитає** п'ятдесят книг! А Олена **здасть** свій іспит. *(He will read fifty books! And Olena will pass her exam.)*"
- find: |
    Для регулярних дій допомагають слова **часто** *(often)* та **завжди** *(always)*. *(For regular actions the words often and always help.)*

    There is a very important difference between English and Ukrainian grammar in conditional sentences.
  replace: |
    Для регулярних дій допомагають слова **часто** *(often)* та **завжди** *(always)*. *(For regular actions the words often and always help.)*

    <!-- INJECT_ACTIVITY: fill-in-future-forms -->

    There is a very important difference between English and Ukrainian grammar in conditional sentences.
- find: |
    Ніколи не використовуйте теперішній час після слова «якщо» для майбутнього! *(Never use the present tense after the word "if" for the future!)*

    Давайте подивимося, як друзі планують свої вихідні. *(Let's see how friends plan their weekend.)*
  replace: |
    Ніколи не використовуйте теперішній час після слова «якщо» для майбутнього! *(Never use the present tense after the word "if" for the future!)*

    <!-- INJECT_ACTIVITY: quiz-aspect-choice -->

    Давайте подивимося, як друзі планують свої вихідні. *(Let's see how friends plan their weekend.)*
- find: |
    > — **Марко:** Добре, якщо ти **купиш** квитки, я **куплю** попкорн. *(Good, if you buy the tickets, I will buy the popcorn.)*

    <!-- INJECT_ACTIVITY: fill-in-future-forms -->
    <!-- INJECT_ACTIVITY: quiz-aspect-choice -->
    <!-- INJECT_ACTIVITY: unjumble-future-sentences -->

    ## Підсумок
  replace: |
    > — **Марко:** Добре, якщо ти **купиш** квитки, я **куплю** попкорн. *(Good, if you buy the tickets, I will buy the popcorn.)*

    <!-- INJECT_ACTIVITY: unjumble-future-sentences -->

    ## Підсумок
</fixes>

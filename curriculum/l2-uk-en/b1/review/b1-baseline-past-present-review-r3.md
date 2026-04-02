## Linguistic Scan
- "гра́ти ... роль" -> This is a Russian calque ("играть роль"). In Ukrainian, the correct phrasing for figurative significance is "відіграва́ти роль".
- "допомі́жне́ слово" -> Typographical error: double acute accent on the letter 'е'.
- "Бі́льшість українських дієслів існують" -> Stylistic flaw: "більшість" referring to inanimate nouns typically requires a singular verb ("існує"), not plural.

## Exercise Check
- All `<!-- INJECT_ACTIVITY -->` markers are properly placed at the end of the relevant theoretical sections.
- The six injected markers correctly match the types and focus specified in the plan's `activity_hints`.
- No issues identified with exercise layout or flow.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | Missed the "Змішаний спосіб: кидати → кинути" point from section 3. The "Самоперевірка" in the conclusion substituted the plan's practical tasks (e.g., "Провідміняйте дієслово бачити", "Утворіть форми минулого часу дієслова нести") with theoretical recall questions. |
| 2. Linguistic accuracy | 8/10 | Used the calque "гра́ти ... роль" instead of "відіграва́ти роль". Typographical error with a double acute "допомі́жне́". Grammatical mismatch in "Бі́льшість українських дієслів існують" (should be singular 'існує'). |
| 3. Pedagogical quality | 9/10 | Excellent pedagogical flow for aspect (process vs result). Provides clear context and breaks down complex morphophonemic rules. |
| 4. Vocabulary coverage | 10/10 | All required vocabulary is present. The terms are correctly bolded, given context, and translated. |
| 5. Exercise quality | 10/10 | Exercise markers are placed strategically after concepts, testing what was just taught. All 6 planned activities are present. |
| 6. Engagement & tone | 8/10 | Contains some "telling instead of showing" and generic enthusiasm, e.g., "Саме тут вид українського дієслова розкрива́є свою спра́вжню стилісти́чну ма́гію." |
| 7. Structural integrity | 10/10 | Clean markdown, precise section headers, and the word count is aligned with the target. |
| 8. Cultural accuracy | 10/10 | Contexts and examples feel authentic to Ukraine (e.g., Kyiv cafe, university exams). |
| 9. Dialogue & conversation quality | 10/10 | Dialogues are natural, effectively demonstrating tense/aspect switching without sounding robotic. |

## Findings
[2. Linguistic accuracy] [Critical]
Location: "Ваш стари́й знайо́мий, вид дієслова, знову буде гра́ти свою найголовні́шу, виріша́льну роль."
Issue: "грати роль" is a calque of Russian "играть роль" in this figurative context.
Fix: Change to "відігравати роль".

[2. Linguistic accuracy] [Major]
Location: "допомі́жне́ слово"
Issue: Double acute accent typo on the word "допоміжне".
Fix: Remove the second acute accent.

[2. Linguistic accuracy] [Minor]
Location: "Бі́льшість українських дієслів існують па́рами."
Issue: "Більшість" with inanimate subjects should take a singular verb ("існує").
Fix: Change "існують" to "існує".

[1. Plan adherence] [Major]
Location: "Спро́буйте абсолютно самостійно дати правильні та то́чні ві́дповіді на ці чоти́ри ключові́ запитання, перш ніж читати наші підка́зки. По-пе́рше: як дуже швидко відрізни́ти пе́ршу дієвідмі́ну..."
Issue: The writer ignored the practical tasks for the self-check specified in the plan (e.g., "Провідміняйте дієслово бачити") and replaced them with theoretical recall questions.
Fix: Replace the theoretical questions with the practical tasks from the plan.

[1. Plan adherence] [Major]
Location: "Слово «да́ти» стає «дава́ти» *(to give/to be giving)*. І́ноді видові пари утворюються від абсолютно різних ко́ренів."
Issue: The plan point "Змішаний: кидати → кинути (суфікс + зміна кореня)." was completely skipped.
Fix: Insert the mixed method example into the text.

[6. Engagement & tone] [Minor]
Location: "Саме тут вид українського дієслова розкрива́є свою спра́вжню стилісти́чну ма́гію."
Issue: Use of generic "magic of" phrasing, which violates the tone guidelines.
Fix: Change to a more academic phrasing like "демонструє свої стилістичні можливості".

## Verdict: REVISE
The module is excellently structured but has a critical calque ("грати роль") and misses two major plan points (the mixed aspectual pair formation and the practical self-check exercises). The tone and typos also need minor polish. A REVISE is necessary to apply the fixes.

<fixes>
- find: "буде гра́ти свою найголовні́шу, виріша́льну роль."
  replace: "буде відіграва́ти свою найголовні́шу, виріша́льну роль."
- find: "допомі́жне́ слово"
  replace: "допомі́жне слово"
- find: "Бі́льшість українських дієслів існують па́рами."
  replace: "Бі́льшість українських дієслів існує па́рами."
- find: "Слово «да́ти» стає «дава́ти» *(to give/to be giving)*. І́ноді видові пари утворюються від абсолютно різних ко́ренів."
  replace: "Слово «да́ти» стає «дава́ти» *(to give/to be giving)*. Існує також змішаний спосіб, де поєднуються суфікс і зміна кореня: «кидати» перетворюється на «кинути». І́ноді видові пари утворюються від абсолютно різних ко́ренів."
- find: "По-пе́рше: як дуже швидко відрізни́ти пе́ршу **дієвідмі́ну** *(conjugation)* від другої? Ві́дповідь надзвичайно проста: завжди уважно диві́ться на **тематичний голосний** *(thematic vowel)* у самих закінченнях. Перша дієвідміна активно використо́вує літери «е» або «є» («пиш**е**ш», «чита́**є**ш»), а друга дієвідміна завжди жо́рстко вимагає «и» або «ї» («роб**и**ш», «сто**ї**ш»). По-дру́ге: як саме граматично утво́рюється минулий час виключно для чоловічого роду? Вам потрібно взяти чисту **основу інфінітива** *(infinitive stem)* і просто додати до неї один специфічний **суфікс** *(suffix)* «-в» (наприклад: «чита-ти» миттєво стає «чита-в»). По-тре́тє: чому відо́ме дієслово «зробити» абсолютно ніколи не має теперішнього часу? Тому що це конкре́тне слово належить до доконаного виду, який фокусу́ється виключно на фіна́льному, фіксо́ваному результаті. Ви фізично ніяк не можете мати повністю завершений результат прямо зараз, перебува́ючи всередині самого процесу дії. І по-четве́рте: коли ми обов'язково використовуємо закінчення «-ться», а коли пишемо «-шся»? Завжди орієнту́йтеся на шкільне́ запитання: якщо ви пита́єте «що роби**ть**?», то смі́ли́во пиші́ть «усміхає**ться**» з м'яким знаком. Якщо ваше пряме питання звучить як «що роби**ш**?», тоді пишіть «усміхає**шся**» повністю без нього."
  replace: "1. Провідміняйте дієслово «бачити» в теперішньому часі (я бачу, ти бачиш, він бачить, ми бачимо, ви бачите, вони бачать). 2. Утворіть форми минулого часу дієслова «нести» для всіх родів (ніс, несла, несло, несли). 3. Визначте вид дієслів: гуляв (недок.), побачив (док.), шукала (недок.), знайшла (док.), працювали (недок.). 4. Перекажіть свій вчорашній день, свідомо чергуючи доконаний і недоконаний вид, щоб показати тло і послідовні події."
- find: "Саме тут вид українського дієслова розкрива́є свою спра́вжню стилісти́чну ма́гію."
  replace: "Саме тут вид українського дієслова демонструє свої стилістичні можливості."
</fixes>

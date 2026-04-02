## Linguistic Scan
Found 2 linguistic errors.
1. "заводить друзів" is a Russian calque ("заводить друзей"). Correct form is "знаходить друзів".
2. "стає для вас невістка" is a case agreement error. The verb "ставати" requires the Instrumental case ("невісткою").

## Exercise Check
All 6 expected `<!-- INJECT_ACTIVITY: {id} -->` markers are present in the text. They are evenly distributed and placed logically at the end of their respective sections. Their focus effectively matches the plan's `activity_hints`.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 8/10 | The text covers the content outline but alters the plan for the final section. Instead of presenting the "Self-check in Ukrainian" as learner-driven production tasks ("Опишіть зовнішність вашого друга...", "Представте свого друга..."), it replaces them with pre-answered theoretical Q&A blocks. |
| 2. Linguistic accuracy | 7/10 | The text contains a case agreement error ("стає для вас невістка" instead of "невісткою") and a Russian calque ("заводить нових цікавих друзів"). |
| 3. Pedagogical quality | 8/10 | Follows an excellent PPP flow with contextual grammar and vocabulary introduction. However, the replacement of the active production self-check with passive Q&A limits productive practice. |
| 4. Vocabulary coverage | 10/10 | All required and recommended vocabulary words from the plan are naturally integrated, correctly contextualized, and properly bolded throughout the text. |
| 5. Exercise quality | 9/10 | All activity injection markers are present, matching the count from the plan's `activity_hints`, and are placed after the relevant teaching sections. |
| 6. Engagement & tone | 7/10 | DEDUCT for "telling instead of showing" and corporate-sounding meta-commentary (e.g., "українська мова люб'язно пропонує", "дивовижна лінгвістична точність", "найкращий і найприродніший спосіб", "Це фундаментальна та дуже корисна навичка"). |
| 7. Structural integrity | 8/10 | The markdown structure is clean and correctly implements the plan's sections. However, the final deterministic word count is 4943 words, which exceeds the 4000-word target by more than 10%. |
| 8. Cultural accuracy | 10/10 | Excellent! The text respects Ukrainian culture, deeply explains kinship terms that lack English equivalents (свекруха, теща, невістка), and correctly utilizes cultural idioms and literary references (Котляревський). |
| 9. Dialogue & conversation quality | 9/10 | The wedding reception dialogue effectively contextualizes the vocabulary and the vocative case. It is slightly theatrical ("Раді вітати вас у сонячній Вінниці!"), but fits the formal setting nicely. |

## Findings
[Linguistic accuracy] [CRITICAL]
Location: Section "Характер людини: риси і оцінка", paragraph 1: "Вона дуже легко заводить нових цікавих друзів і майже завжди із задоволенням перебуває в самому центрі уваги будь-якої великої компанії."
Issue: The phrase "заводить друзів" is a calque of the Russian "заводить друзей". In Ukrainian, one "знаходить друзів" or "здобуває друзів".
Fix:
find: "Вона дуже легко заводить нових цікавих друзів"
replace: "Вона дуже легко знаходить нових цікавих друзів"

[Linguistic accuracy] [CRITICAL]
Location: Section "Родина і родичі", paragraph 2: "Якщо ваш улюблений син нарешті одружується, то його молода дружина назавжди стає для вас невістка."
Issue: Case agreement error. The verb "ставати" requires the instrumental case (стає ким/чим?), so "невістка" must be "невісткою".
Fix:
find: "стає для вас невістка."
replace: "стає для вас невісткою."

[Plan adherence] [MAJOR]
Location: Section "Підсумок: людина у словах", paragraph 1: "> — **Питання:** Яка суттє́ва різни́ця між прикметниками **«кремезний»** *(stocky / sturdy)* та **«тенді́тний»** *(slender / delicate)*?..."
Issue: The plan explicitly called for an active "Self-check in Ukrainian" with production tasks (e.g., "Опишіть зовнішність вашого друга...", "Представте свого друга колезі..."). The writer replaced these learner-driven tasks with passive, pre-answered Q&A blocks testing theory rather than skill application.
Fix:
find: "> — **Питання:** Яка суттє́ва різни́ця між прикметниками **«кремезний»** *(stocky / sturdy)* та **«тенді́тний»** *(slender / delicate)*?\n> — **Відповідь:** Слово «кремезний» завжди означає людину дуже міцно́ї статури, з широ́кими плечи́ма та великою фізи́чною си́лою. Натомість прикметник «тендітний» описує когось тонко́го, надзвичайно ви́тонченого, легко́го та дещо слабко́го на зо́внішній вигляд.\n> — **Питання:** Коли в українській мові правильно вжива́ти слово **«відносини»** *(relations)*, а коли треба каза́ти **«стосунки»** *(relationships)*?\n> — **Відповідь:** Іме́нник «відносини» традиційно використовують виключно для офіці́йних, економі́чних, правови́х або дипломати́чних зв'язків. Слово «стосунки» ми обов'язково вжива́ємо тоді, коли говоримо про особисті, теплі дружні, романтичні або родинні контакти між звича́йними людьми.\n> — **Питання:** Як граматично правильно зверну́тися до хло́пця на ім'я Андрій, використо́вуючи **кличний відмінок** *(vocative case)*?\n> — **Відповідь:** На́ша мова вимагає використання спеціальної граматичної форми для будь-якого прямо́го звертання. Правильно і красиво казати: «Андрію!»\n> — **Питання:** Назві́ть три обов'язко́ві структу́рні частини класичного шкільно́го **тво́ру-опису** *(composition-description)* людини.\n> — **Відповідь:** Будь-який правильно структурований словесний портрет повинен місти́ти коро́ткий **зачин** *(introduction)*, розгорнуту **основну частину** *(main body)* з дета́лями та логі́чну **кінці́вку** *(conclusion)*, яка підсумо́вує враження."
replace: "1. **Опишіть зовнішність** вашого найкращого друга або подруги (5–7 речень).\n2. **Назвіть 5 позитивних і 3 негативних риси** характеру, які ви найчастіше помічаєте в людях.\n3. **Поясніть різницю** між словами *стосунки*, *ставлення* та *відносини* своїми словами.\n4. **Представте свого друга колезі** (формально) та іншому другу (неформально)."

## Verdict: REVISE
The module demonstrates excellent cultural grounding and vocabulary integration, but contains two critical linguistic errors (a case agreement mistake and a Russian calque) which cannot ship to learners. Furthermore, the self-check section violates the plan's pedagogical goal by providing a pre-answered Q&A instead of open production tasks. Fixing these issues with the targeted replacements provided below will bring the module to an excellent standard.

<fixes>
- find: "Вона дуже легко заводить нових цікавих друзів"
  replace: "Вона дуже легко знаходить нових цікавих друзів"
- find: "стає для вас невістка."
  replace: "стає для вас невісткою."
- find: "> — **Питання:** Яка суттє́ва різни́ця між прикметниками **«кремезний»** *(stocky / sturdy)* та **«тенді́тний»** *(slender / delicate)*?\n> — **Відповідь:** Слово «кремезний» завжди означає людину дуже міцно́ї статури, з широ́кими плечи́ма та великою фізи́чною си́лою. Натомість прикметник «тендітний» описує когось тонко́го, надзвичайно ви́тонченого, легко́го та дещо слабко́го на зо́внішній вигляд.\n> — **Питання:** Коли в українській мові правильно вжива́ти слово **«відносини»** *(relations)*, а коли треба каза́ти **«стосунки»** *(relationships)*?\n> — **Відповідь:** Іме́нник «відносини» традиційно використовують виключно для офіці́йних, економі́чних, правови́х або дипломати́чних зв'язків. Слово «стосунки» ми обов'язково вжива́ємо тоді, коли говоримо про особисті, теплі дружні, романтичні або родинні контакти між звича́йними людьми.\n> — **Питання:** Як граматично правильно зверну́тися до хло́пця на ім'я Андрій, використо́вуючи **кличний відмінок** *(vocative case)*?\n> — **Відповідь:** На́ша мова вимагає використання спеціальної граматичної форми для будь-якого прямо́го звертання. Правильно і красиво казати: «Андрію!»\n> — **Питання:** Назві́ть три обов'язко́ві структу́рні частини класичного шкільно́го **тво́ру-опису** *(composition-description)* людини.\n> — **Відповідь:** Будь-який правильно структурований словесний портрет повинен місти́ти коро́ткий **зачин** *(introduction)*, розгорнуту **основну частину** *(main body)* з дета́лями та логі́чну **кінці́вку** *(conclusion)*, яка підсумо́вує враження."
  replace: "1. **Опишіть зовнішність** вашого найкращого друга або подруги (5–7 речень).\n2. **Назвіть 5 позитивних і 3 негативних риси** характеру, які ви найчастіше помічаєте в людях.\n3. **Поясніть різницю** між словами *стосунки*, *ставлення* та *відносини* своїми словами.\n4. **Представте свого друга колезі** (формально) та іншому другу (неформально)."
</fixes>

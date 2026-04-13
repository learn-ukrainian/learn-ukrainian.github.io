## Linguistic Scan
- Critical: `Це традиційне місце, де ви можете спокійно випити філянку ароматної кави.` The form `філянка` is unsupported by the provided local VESUM/SUM lookup; the standard dictionary form is `філіжанка` / `філіжанку` ([Горох](https://www.goroh.pp.ua/%D0%A2%D0%BB%D1%83%D0%BC%D0%B0%D1%87%D0%B5%D0%BD%D0%BD%D1%8F/%D1%84%D1%96%D0%BB%D1%96%D0%B6%D0%B0%D0%BD%D0%BA%D0%B0), [СУМ-20](https://slovnyk.me/dict/newsum/%D1%84%D1%96%D0%BB%D1%96%D0%B6%D0%B0%D0%BD%D0%BA%D0%B0)).

## Exercise Check
6 markers found: `fill-in-shopping-dialogues`, `quiz-transaction-phrases`, `sentence-builder-comparison`, `match-up-agent-workplace`, `dialogue-completion-complaint`, `free-write-service-review`.

They match the 6 `activity_hints`, appear after the relevant teaching sections, and are distributed through the module. No exercise-placement or marker-ID issues found.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 6/10 | All planned H2 sections are present, but the specific dialogue situation “Shopping at a Львівський ТРЦ...” never appears: searches for `Львів` and `ТРЦ` returned 0 hits. The cross-module refs `b1-038`, `b1-039`, `b1-043`, `b1-045` and the exact phrase `Контрольна робота 5` also return 0 hits. Section pacing is also far off plan: `На ринку` is about 1436 words vs planned 750. |
| 2. Linguistic accuracy | 8/10 | Mostly clean Ukrainian, but `"...випити філянку ароматної кави"` uses a nonstandard/unsupported form instead of standard `філіжанку`. |
| 3. Pedagogical quality | 7/10 | There are many examples and usable dialogues, but explanation is often buried under padding, especially in the long market opening and `Цей живий і багатий текст чудово допоможе...`. The final summary also drifts to `від складних дієслів руху`, which is outside this module’s taught scope. |
| 4. Vocabulary coverage | 9/10 | Required vocabulary is covered naturally in prose: `знижка`, `готівка`, `картка`, `чек`, `повернення`, `гарантія`, `розмір`, `примірочна`, `посилка`, `обмін валют`, `курс`, `ремонт`, `бракований`. Recommended items like `переказ`, `рахунок`, `стрижка`, `ательє`, `кав'ярня`, `обслуговування` also appear. |
| 5. Exercise quality | 9/10 | All 6 expected markers are present, match the plan’s types/focuses, and come after the relevant teaching blocks. The only slight clustering is the last two markers in `Скарга і відгук`, but that section does teach both complaint and review writing. |
| 6. Engagement & tone | 5/10 | The module has energy and detail, but it is overloaded with filler and stacked intensifiers, e.g. `дуже багатий і особливий сенсорний досвід` and repeated chains of `дуже` / `надзвичайно` in the market opening. |
| 7. Structural integrity | 9/10 | All required H2 headings are present and ordered correctly. Markdown is clean, markers are intact, and the pipeline word count of 5487 is safely above the 4000 target. |
| 8. Cultural accuracy | 6/10 | The market material is culturally strong, but the supermarket checkout dialogue teaches `Решти не треба. Залиште це собі` to a cashier and then recommends that phrase `на касі`, which is culturally off for large supermarket checkouts. |
| 9. Dialogue & conversation quality | 7/10 | Several dialogues are multi-turn and contextual, but the supermarket exchange becomes stilted at `Залиште це собі`, and some dialogue turns are doing explanation work instead of sounding like real speech. |

## Findings
[LINGUISTIC ACCURACY] [SEVERITY: critical]  
Location: `Це традиційне місце, де ви можете спокійно випити філянку ароматної кави.`  
Issue: `філянку` is not supported by the provided VESUM/SUM verification path; the standard form is `філіжанку`.  
Fix: Replace `філянку` with `філіжанку`.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## У магазині` opening paragraph beginning `Коли ви повільно гуляєте центральними вулицями...`  
Issue: The plan’s specific dialogue situation is “Shopping at a Львівський ТРЦ ...” with comparison language, but the prose never mentions `Львів` or `ТРЦ` and opens generically instead.  
Fix: Replace the opening paragraph with one anchored in a Lviv shopping-center scenario that includes the planned comparison phrases and still introduces shop-name word formation.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: `## На ринку` opening paragraph beginning `Український **ринок**...`  
Issue: This section is massively over budget relative to plan pacing: about 1436 words vs planned 750, and the opening paragraph is especially inflated with descriptive filler.  
Fix: Compress the opening paragraph so the section gets to the market language and comparisons faster.

[CULTURAL ACCURACY] [SEVERITY: major]  
Location: supermarket checkout dialogue and the follow-up note: `Ви знаєте, решти не треба. Залиште це собі...` and `Також вона ідеально підходить... на касі.`  
Issue: This teaches a culturally implausible scenario for a large supermarket cashier; chain cashiers do not normally accept personal tips, so the example models the wrong real-world interaction.  
Fix: Change the checkout line to a normal request for change/receipt, and move `Решти не треба` to a small-cash, informal context such as a café or kiosk.

[PLAN ADHERENCE] [SEVERITY: major]  
Location: final summary paragraph: `Наступним нашим серйозним кроком буде Модуль 45: Контрольна робота... Ви повторите все: від складних дієслів руху...`  
Issue: The summary omits the planned cross-module references (`b1-038`, `b1-039`, `b1-043`, `b1-045` / `Контрольна робота 5`) and incorrectly claims the learner will review `складних дієслів руху`, which this module did not teach.  
Fix: Replace that ending with an explicit reference to `Контрольна робота 5 (B1-045)` and the relevant prerequisite grammar modules only.

## Verdict: REVISE
There is a critical linguistic correction (`філянку`) plus multiple major plan-fit and cultural issues. The module is usable, but it does not meet PASS because the review found teachable inaccuracies and several places where the prose diverges from the plan.

<fixes>
- find: "філянку ароматної кави"
  replace: "філіжанку ароматної кави"
- find: |-
    Український **ринок** *(market)*, або **базар** *(bazaar)*, — це значно більше, ніж просто зручне місце для щотижневої купівлі свіжих продуктів. Це справжній соціальний, культурний та економічний центр сучасного міста, де завжди бурхливо вирує життя, лунають найсвіжіші новини та щодня укладаються важливі усні угоди. Майже кожне велике місто України обов'язково має свій власний легендарний і впізнаваний ринок. У Києві це славетний історичний Бессарабський ринок, зручно розташований у самому центрі столиці. Він широко відомий своєю вишуканою архітектурою та традиційно високими цінами, які повністю відповідають його престижному статусу. В Одесі ж гордо височіє знаменитий Привоз — надзвичайно колоритний, страшенно галасливий і напрочуд живий базар, де можна легко знайти абсолютно все: від щойно виловленої свіжої риби до дотепних і яскравих місцевих жартів. Відвідування ринку — це завжди дуже багатий і особливий сенсорний досвід. З усіх можливих боків вас щільно оточують яскраві барви сезонних стиглих овочів, неповторні аромати домашньої ковбаси та різноманітних східних спецій. Для багатьох українців критично і життєво важливо мати на базарі **своїх продавців** *(personal sellers)*. Це ті самі надійні люди, у яких ви постійно роками купуєте свіже домашнє молоко, м'ясо чи зелень. Вони завжди дуже дбайливо залишать для вас найкращий і найсвіжіший шматок, і ніколи не продадуть вам неякісний чи зіпсований товар. Адже особиста бездоганна репутація та багаторічні довірчі людські стосунки на базарі важать для них значно більше, ніж будь-яка дорога телевізійна реклама.
  replace: |-
    Український **ринок** *(market)*, або **базар** *(bazaar)*, — це не лише місце для купівлі свіжих продуктів, а й простір живого щоденного спілкування. У Києві таким символом є Бессарабський ринок, в Одесі — Привоз. Для багатьох українців важливо мати на базарі **свого продавця** *(a trusted seller)*: людину, у якої роками купують молоко, м'ясо чи зелень і якій довіряють якість товару. Саме тому ринок у цій темі важливий не лише як культурний фон, а і як природне місце для порівнянь, торгу та ввічливих побутових діалогів.
- find: |-
    Коли ви повільно гуляєте центральними вулицями великого українського міста, ви обов'язково бачите безліч різноманітних яскравих вивісок. Як саме українці зазвичай називають свої улюблені торгові точки? Дуже часто ми активно використовуємо спеціальний продуктивний словотвірний суфікс **-арня** *(suffix for a place or workshop)* або **-ня** для створення абсолютно нових назв. Цей зручний суфікс надзвичайно легко і цілком логічно додається до базової основи слова. Наприклад, там, де досвідчені майстри щоранку печуть свіжий гарячий хліб і смачні булки, працює чудова **пекарня** *(bakery)*. Корінь цього слова прямо походить від відомого дієслова «пекти». А де продаються найцікавіші нові романи? Звісно, це завжди затишна **книгарня** *(bookstore)*. Давайте дуже уважно подивимося на два неймовірно популярні українські слова: **кав'ярня** *(coffee shop)* та **цукерня** *(confectionery)*. Слово «кав'ярня» утворюється від основи «кава» плюс суфікс «-ярня». Це традиційне місце, де ви можете спокійно випити філянку ароматної кави. А «цукерня» походить від солодкого слова «цукерка». Інший дуже популярний спосіб — це використання звичайного прикметника разом із загальним іменником «магазин» або гарним українським словом **крамниця** *(shop)*. Ми часто говоримо **продуктова крамниця** *(grocery store)*, якщо там продаються різноманітні продукти харчування. Якщо ж вам терміново потрібно купити нові зручні зимові чоботи або легкі туфлі, ви шукаєте великий **взуттєвий магазин** *(shoe store)*. Розуміння цієї простої логіки словотвору допоможе вам швидко орієнтуватися.
  replace: |-
    Уявіть, що ви зайшли до львівського ТРЦ і відразу порівнюєте варіанти: «Ця сукня гарніша, але дорожча. Чи є дешевша?», «Ця крамниця більша за ту», «Який варіант найкращий зі знижкою?». Саме в такому середовищі добре працює словотвірна логіка назв місць і крамниць. Там, де печуть хліб, працює **пекарня** *(bakery)*, де продають книжки — **книгарня** *(bookstore)*, а де стрижуть волосся — **перукарня** *(hair salon/barbershop)*. Поруч можуть бути **кав'ярня** *(coffee shop)*, **цукерня** *(confectionery)*, **хімчистка** *(dry cleaner's)* або великий **взуттєвий магазин** *(shoe store)*. Розуміння цієї словотвірної логіки допомагає швидко орієнтуватися в місті й одразу ставити природні запитання продавцеві.
- find: "> — **Покупець:** Ви знаєте, решти не треба. Залиште це собі, гарного і спокійного вам дня! *(You know, keep the change. Keep it for yourself, have a good and peaceful day!)*"
  replace: "> — **Покупець:** Дякую, будь ласка, дайте мені решту і чек. Гарного вам дня! *(Thank you, please give me the change and the receipt. Have a good day!)*"
- find: |-
    Коротка фраза «Решти не треба» є надзвичайно корисною і ввічливою, якщо ви бажаєте залишити дрібні чайові у вашій улюбленій кав'ярні. Також вона ідеально підходить, якщо ви просто не хочете довго чекати і брати зайві дрібні металеві монети на касі.
  replace: |-
    Коротка фраза «Решти не треба» природніше звучить у невеликій кав'ярні, кіоску або іншій неформальній готівковій ситуації. У великому супермаркеті на касі краще сказати: «Дайте, будь ласка, решту і чек».
- find: |-
    Наступним нашим серйозним кроком буде Модуль 45: Контрольна робота. Це велике тестування допоможе вам надійно закріпити абсолютно всі знання, які ви активно здобували у цьому важливому блоці. Ви повторите все: від складних дієслів руху до утворення ступенів порівняння та засвоєння нової професійної лексики. Готуйтеся сумлінно, регулярно повторюйте пройдений матеріал, і ви обов'язково покажете просто чудовий фінальний результат!
  replace: |-
    Наступним нашим серйозним кроком буде Контрольна робота 5 (B1-045). Перед нею варто ще раз повторити модулі B1-038 і B1-039 про ступені порівняння, а також B1-043 про творення іменників, бо саме ці теми ми щойно застосували в ситуаціях покупок і послуг.
</fixes>
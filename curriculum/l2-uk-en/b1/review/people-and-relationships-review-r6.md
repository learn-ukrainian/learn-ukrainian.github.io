## Linguistic Scan
Found a grammatical case error: the Nominative case is incorrectly used instead of the Instrumental after the verb "стає" ("стає для вас невістка"). Found a syntactic error where an adjective is used without quoting or syntactic linking ("кажемо про когось лагідний"). No Russianisms, Surzhyk, or calques found. 

## Exercise Check
- `<!-- INJECT_ACTIVITY: body-categories-match -->` is present and matches the plan correctly.
- `<!-- INJECT_ACTIVITY: character-traits-quiz -->` is present and matches the plan correctly.
- `<!-- INJECT_ACTIVITY: fill-in-portrait-family -->` is present and matches the plan correctly.
- `<!-- INJECT_ACTIVITY: vocab-categories -->` is present and matches the plan correctly.
- `<!-- INJECT_ACTIVITY: introductions-and-vocative-quiz -->` is present, but the marker ID implies a `quiz`. The plan explicitly specifies a `role-play` for this section.
- `<!-- INJECT_ACTIVITY: write-portrait-essay -->` is present and matches the plan correctly.

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | 9/10 | Covered almost all points, but missed `повний`, `худорляве`, `широкоплечий`, and `наполегливий` from the `content_outline`. |
| 2. Linguistic accuracy | 8/10 | Grammatical case error: "його молода дружина назавжди стає для вас невістка" (requires Instrumental: "невісткою"). Syntactic awkwardness: "кажемо про когось лагідний" (should be "називаємо когось лагідним"). |
| 3. Pedagogical quality | 9/10 | Clear PPP structure, numerous examples for grammar points (e.g., three examples for Genitive family relationships). Minor deduction due to meta-commentary blending into the pedagogy. |
| 4. Vocabulary coverage | 9/10 | All required and recommended vocab hints are successfully included. Missing a few section-specific outline words. |
| 5. Exercise quality | 8/10 | Most markers match the plan, but `introductions-and-vocative-quiz` contradicts the plan's specific instruction for a `role-play` activity in Section 5. |
| 6. Engagement & tone | 5/10 | Heavy use of meta-commentary and generic enthusiasm ("Розглянемо уважно такий чудовий приклад", "Щоб краще зрозуміти ці правила, детально розгляньмо", "Найбільша лексична точність і неймовірна краса..."). |
| 7. Structural integrity | 7/10 | All sections are present, but the calculated word count is 5006 words, exceeding the 4000-word target by >25%. |
| 8. Cultural accuracy | 10/10 | Excellent integration of Ukrainian kinship concepts, idioms ("кров із молоком"), and societal norms around introductions. |
| 9. Dialogue & conversation quality | 6/10 | The dialogue is stilted and textbook-robotic ("Пані Катерино, дозвольте відрекомендуватися. Я — Антон, і я обіцяю завжди любити і поважати вашу чудову онуку"). Features a robotic chorus of "Родичі" speaking in perfect unison. |

## Findings

[DIMENSION 6. Engagement & tone] [SEVERITY: major]
Location: Section 1 ("Розглянемо уважно такий чудовий приклад: У втомлених та сумних очах..."), Section 2 ("Візьмемо для нашого детального прикладу два популярні слова: щирий та чесний."), Section 6 ("Щоб краще зрозуміти ці правила, детально розгляньмо приклад структурованого портрета."), Section 7 ("У цьому модулі ми дуже детально та всебічно розглянули українську лексику... давайте ще раз повторимо найголовніші концепції нашого уроку"), Section 3 ("Найбільша лексична точність і неймовірна краса української мови проявляється саме тоді...")
Issue: The text contains excessive meta-commentary and generic enthusiasm, which violates the tone guidelines.
Fix: Remove the meta-commentary phrases and transition naturally to the examples.

[DIMENSION 9. Dialogue & conversation quality] [SEVERITY: major]
Location: Section 5 (Dialogue starting with "> — **Нарече́на:** Дорогі́ го́сті! Дозвольте представити вам мою́ нову роди́ну.")
Issue: Stilted and textbook-robotic phrasing ("Пані Катерино, дозвольте відрекомендуватися"). The dialogue features a collective "Родичі" chorus speaking in perfect unison.
Fix: Rewrite the dialogue to sound like a natural family introduction, replacing the robotic chorus with specific relatives (Дядько, Бабуся) and using natural greetings.

[DIMENSION 5. Exercise quality] [SEVERITY: major]
Location: Section 5 (`<!-- INJECT_ACTIVITY: introductions-and-vocative-quiz -->`)
Issue: The marker ID implies a quiz, but the plan's `activity_hints` explicitly specifies a `role-play` for introductions.
Fix: Change the marker ID to `<!-- INJECT_ACTIVITY: introductions-role-play -->`.

[DIMENSION 2. Linguistic accuracy] [SEVERITY: major]
Location: Section 3 ("його молода дружина назавжди стає для вас **неві́стка**")
Issue: Grammatical case error. The verb "стає" requires the Instrumental case, not Nominative.
Fix: Change "неві́стка" to "неві́сткою".

[DIMENSION 2. Linguistic accuracy] [SEVERITY: minor]
Location: Section 2 ("Коли ми впевнено кажемо про когось **лагідний**, ми зазвичай маємо на увазі його загальну зовнішню манеру поведінки.")
Issue: Syntactic awkwardness. "Кажемо про когось лагідний" lacks proper quoting or syntactic linking.
Fix: Change to "називаємо когось **ла́гідним**".

[DIMENSION 1. Plan adherence] [SEVERITY: minor]
Location: Section 1 ("Наприклад, чоловік може бути кремезний..."), Section 2 ("Один персонаж може бути неймовірно працьовитим...")
Issue: The text misses the words `повний`, `худорляве`, `широкоплечий`, and `наполегливий` from the plan's `content_outline`.
Fix: Integrate the missing words into the descriptions.

## Verdict: REVISE
The module covers the complex B1 vocabulary and pedagogy exceptionally well, but requires a REVISE due to a grammatical case error ("стає невістка"), robotic dialogue phrasing, a mismatched exercise marker, and excessive meta-commentary.

<fixes>
- find: "Розгля́немо уважно такий чудо́вий приклад: У вто́млених та сумни́х оча́х"
  replace: "Наприклад: У вто́млених та сумни́х оча́х"
- find: "Ві́зьмемо для нашого детального при́кладу два популя́рні слова: **щирий** *(sincere)* та **че́сний** *(honest)*."
  replace: "Порівняймо два популя́рні слова: **щирий** *(sincere)* та **че́сний** *(honest)*."
- find: "Щоб краще зрозуміти ці правила, детально розгля́ньмо приклад структуро́ваного портрета. (1) Мій"
  replace: "Ось приклад структуро́ваного портрета: (1) Мій"
- find: "У цьому мо́дулі ми дуже детально та всебі́чно розгля́нули украї́нську ле́ксику, необхі́дну для точного опису зовнішності, характеру, родинних зв'язків та спілкування. Щоб остато́чно закріпи́ти ці важливі знання, дава́йте ще раз повто́римо найголовні́ші конце́пції нашого уро́ку за допомогою кілько́х ключови́х практи́чних запита́нь."
  replace: "Закріпімо найголовніші конце́пції мо́дуля за допомогою кілько́х практи́чних запита́нь."
- find: "Найбі́льша лекси́чна то́чність і неймовірна краса́ украї́нської мови проявля́ється саме тоді́, коли ми починаємо детально описувати складні роди́нні зв'я́зки після весі́лля."
  replace: "Українська мова має дуже точну лексику для опису складних роди́нних зв'язкі́в після весі́лля."
- find: "його молода дружи́на назавжди стає для вас **неві́стка** *(daughter-in-law)*."
  replace: "його молода дружи́на назавжди стає для вас **неві́сткою** *(daughter-in-law)*."
- find: "Коли ми впевнено ка́жемо про когось **ла́гідний**, ми зазвичай ма́ємо на ува́зі"
  replace: "Коли ми впевнено називаємо когось **ла́гідним**, ми зазвичай ма́ємо на ува́зі"
- find: "<!-- INJECT_ACTIVITY: introductions-and-vocative-quiz -->"
  replace: "<!-- INJECT_ACTIVITY: introductions-role-play -->"
- find: "Напри́клад, чолові́к мо́же бу́ти **креме́зни́й** *(stocky/sturdy)*, що за́вжди́ означа́є фізи́чно си́льну, дуже міцну́ та широ́ку статуру."
  replace: "Напри́клад, чолові́к мо́же бу́ти **креме́зни́й** *(stocky/sturdy)* або **широкопле́чий** *(broad-shouldered)*, що означа́є фізи́чно си́льну статуру, а також **по́вний** *(plump/full)* або **худи́й** *(thin)*."
- find: "Обличчя буває дуже **смагля́ве** *(swarthy/dark-skinned)* від до́вгого перебува́ння"
  replace: "Обличчя буває **по́вне** *(full)* чи **худорля́ве** *(thin/lean)*, а також дуже **смагля́ве** *(swarthy/dark-skinned)* від до́вгого перебува́ння"
- find: "Оди́н персона́ж може бути неймовірно **працьови́тим** *(hardworking)*, ніколи не зна́ючи"
  replace: "Оди́н персона́ж може бути неймовірно **працьови́тим** *(hardworking)* та **наполегливим** *(persistent)*, ніколи не зна́ючи"
- find: |
    > — **Нарече́на:** Дорогі́ го́сті! Дозвольте представити вам мою́ нову роди́ну. Це мій **старший** *(older / elder)* брат Миха́йло — він дуже розу́мний і наді́йний чоловік.
    > — **Нарече́ний:** Дуже приємно познайомитися, Миха́йле! А це моя **моло́дша** *(younger)* сестра Оле́на — вона завжди найвеселі́ша ді́вчи́на в нашій сім'ї́.
    > — **Родичі:** Ра́ді віта́ти вас у со́нячній Ві́нниці! Ми так до́вго чека́ли на це прекрасне весілля.
    > — **Наречена:** Познайомтеся, будь ласка, з на́шою бабу́сею Катери́ною. Вона — **найдобрі́ша** *(kindest)* жінка у всьо́му світі і чудово готу́є украї́нські стра́ви.
    > — **Наречений:** Пані Катери́но, дозвольте відрекомендуватися. Я — Анто́н, і я обіця́ю завжди люби́ти і поважа́ти вашу чудо́ву ону́ку.
    > — **Родичі:** Щиро віта́ємо тебе́, Анто́не! Тепе́р ти також частина нашого великого роду, тому почу́вайся тут як удо́ма.
  replace: |
    > — **Нарече́на:** Антоне, познайомся з моєю родиною. Це мій **старший** *(older / elder)* брат Миха́йло — він дуже розу́мний і наді́йний.
    > — **Нарече́ний:** Дуже приємно познайомитися, Миха́йле! А це моя **моло́дша** *(younger)* сестра Оле́на — вона завжди найвеселі́ша ді́вчи́на в нашій сім'ї́.
    > — **Дядько:** Ра́ді віта́ти вас у со́нячній Ві́нниці! Ми так до́вго чека́ли на це прекрасне весілля.
    > — **Наречена:** Познайомтеся, будь ласка, з на́шою бабу́сею Катери́ною. Вона — **найдобрі́ша** *(kindest)* жінка у всьо́му світі і чудово готу́є украї́нські стра́ви.
    > — **Наречений:** Доброго дня, пані Катери́но! Я — Анто́н, дуже радий нарешті з вами познайомитися.
    > — **Бабуся:** Щиро віта́ємо тебе́, Анто́не! Тепе́р ти також частина нашого великого роду, тому почу́вайся як удо́ма.
</fixes>

<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/all-cases-practice.yaml` file for module **37: Все разом** (a2).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = 2-3 quick checks after key teaching points. Workbook = 4-8 deeper practice exercises covering the full topic.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

- `<!-- INJECT_ACTIVITY: quiz-identify-case-of-highlighted-nouns-in-the-birthday-dialogue-and-explain-the-trigger -->`
- `<!-- INJECT_ACTIVITY: fill-in-rewrite-dialogue-sentences-changing-singular-to-plural-e-g -->`
- `<!-- INJECT_ACTIVITY: match-up-match-sentence-halves-ensuring-case-agreement-with-prepositions-verbs -->`
- `<!-- INJECT_ACTIVITY: error-correction-all-cases -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete gaps in a dialogue with the correct case form — all 7 cases represented,
    both singular and plural
  items: 8
  type: fill-in
- focus: Identify which case a highlighted noun is in and explain why (verb or preposition
    trigger)
  items: 8
  type: quiz
- focus: Match sentence halves so that the case form in the first half agrees with
    the preposition/verb in the second half
  items: 8
  type: match-up
- focus: Find and fix wrong case endings across all 7 cases (e.g., *допомагаю сестру
    → сестрі, *багато студенти → студентів)
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- рецепт (prescription, recipe)
- температура (temperature)
- Карпати (Carpathians)
- милуватися (to admire)
- частувати (to treat (with food))
required:
- вечірка (party)
- подарунок (gift, present)
- лікар (doctor)
- пацієнт (patient)
- здоров'я (health)
- ліки (medicine)
- подорож (trip, journey)
- потяг (train)
- визначне місце (landmark, sight)
- запрошувати (to invite)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Діалог 1: Організовуємо день народження

Сьогодні ми слухаємо цікаву розмову двох друзів. **Оксана** *(Oksana)* та **Андрій** *(Andrii)* телефонують одне одному. Вони хочуть організувати чудову **вечірку** *(party)* для своєї подруги. Її звати **Олена** *(Olena)*. Це буде великий **сюрприз** *(surprise)* на її **день народження** *(birthday)*. У цьому діалозі вони природно використовують усі сім відмінків української мови. Це чудова можливість уважно послухати та побачити, як працює українська граматика в реальному житті.

> — **Оксана:** Привіт, Андрію! Ти пам'ятаєш, що завтра в Олени день народження? *(Hi, Andrii! Do you remember that tomorrow is Olena's birthday?)*
> — **Андрій:** Привіт, Оксано! Так, пам'ятаю. Хто саме **прийде** *(will come)* на свято? *(Hi, Oksana! Yes, I remember. Who exactly will come to the holiday?)*
> — **Оксана:** Прийдуть усі наші найкращі **друзі** *(friends)*. Але у нас є проблема: ще **немає торта** *(there is no cake)*. *(All our best friends will come. But we have a problem: there is no cake yet.)*
> — **Андрій:** Я можу **купити торт** *(to buy a cake)*. А що ще нам треба? *(I can buy a cake. And what else do we need?)*
> — **Оксана:** У нас буде **багато гостей** *(many guests)*, але зовсім **немає соку** *(there is no juice)*. *(We will have many guests, but there is absolutely no juice.)*
> — **Андрій:** Добре, я куплю сік. А ти можеш **запросити друзів** *(to invite friends)*? *(Okay, I will buy juice. And can you invite the friends?)*

Let's pause and look at the "birthday triggers" we just heard in the conversation. Notice how verbs and words of quantity change the endings of the nouns that follow them. 

When Andrii says he will buy a cake, he uses the Accusative case for the direct object of his action: «купити торт». Because the word «торт» is an inanimate noun, it does not change its ending here. 

However, when Oksana talks about what they specifically do not have, she must use the Genitive case of absence: «немає торта», «немає соку». Words that express quantity also trigger the Genitive case, which is exactly why she says «багато гостей» instead of the Nominative plural form «багато гості».

> — **Оксана:** Я вже почала **дзвонити друзям** *(to call friends)*. Вони дуже раді. *(I already started to call friends. They are very glad.)*
> — **Андрій:** Супер. А що ми подаруємо Олені? Нам потрібен гарний **подарунок** *(gift)*. *(Super. And what will we give Olena? We need a beautiful gift.)*
> — **Оксана:** Я думаю, ми можемо подарувати **Олені** *(to Olena)* нову книгу. *(I think we can give Olena a new book.)*
> — **Андрій:** Це чудова ідея. Ми прийдемо **з великою компанією** *(with a large company)*. *(That is a wonderful idea. We will come with a large company.)*
> — **Оксана:** Так, ми будемо **з друзями** *(with friends)*. Ми також можемо **прикрасити** *(to decorate)* кімнату **кульками** *(with balloons)*. *(Yes, we will be with friends. We can also decorate the room with balloons.)*

Now we clearly see both the Dative and Instrumental cases in action. 

The Dative case identifies the "recipient" of an action. When Oksana gives a gift, she gives it directly «Олені» (to Olena). Similarly, when she makes a phone call, she speaks «друзям» (to the friends).

The Instrumental case shows accompaniment or the physical means of doing something. It answers the question "with who?" or "with what?". They plan to arrive «з великою компанією» and celebrate «з друзями». Notice the difference between the singular ending in «з компанією» and the plural ending in «з друзями». They also decorate the room using balloons: «кульками».

> — **Андрій:** Де саме ми зробимо цю вечірку? **У ресторані** *(in a restaurant)* «Дніпро»? *(Where exactly will we do this party? In the restaurant "Dnipro"?)*
> — **Оксана:** Так, там завжди дуже гарно. Ми будемо зручно сидіти **на терасі** *(on the terrace)*. *(Yes, it is always very beautiful there. We will sit comfortably on the terrace.)*
> — **Андрій:** Домовилися, **Оксано** *(Oksana)*! Усе буде ідеально. *(Agreed, Oksana! Everything will be perfect.)*
> — **Оксана:** Дуже дякую за допомогу, **Андрію** *(Andrii)*! До завтра! *(Thank you very much for the help, Andrii! Until tomorrow!)*

В Україні є дуже цікава традиція. Зазвичай **іменинник** *(birthday person)* сам організовує свято і щедро **частує** *(treats)* своїх гостей. Гості просто приносять подарунки, але вони не платять за ресторан. Оскільки Оксана та Андрій роблять таємний сюрприз, це приємний виняток із правил! *(In Ukraine there is a very interesting tradition. Usually the birthday person themselves organizes the holiday and generously treats their guests. Guests simply bring gifts, but they do not pay for the restaurant. Since Oksana and Andrii are making a secret surprise, this is a pleasant exception to the rules!)*

<!-- INJECT_ACTIVITY: quiz-identify-case-of-highlighted-nouns-in-the-birthday-dialogue-and-explain-the-trigger -->


## Діалог 2: У лікарні

Сьогодні Петро йде до **лікарні** *(hospital)*. Він дуже погано почувається ще з самого ранку. У лікарні завжди багато хворих людей, тому Петро спочатку підходить до **реєстратури** *(reception)*. Йому потрібно точно дізнатися, де приймає його **лікар** *(doctor)*. Петро має **запис** *(appointment)* на десяту годину ранку. Він сподівається, що лікар швидко допоможе йому.

> — **Петро:** Добрий день! Я маю запис до лікаря Коваленка.
> — **Адміністраторка:** Добрий день! Ваше прізвище, будь ласка?
> — **Петро:** Моє прізвище — Бойко. Я записаний на десяту годину.
> — **Адміністраторка:** Хвилинку, я перевірю. Так, бачу. Але лікар зараз зайнятий. У нього інший **пацієнт** *(patient)*.
> — **Петро:** Зрозуміло. А де мені чекати? Мені потрібно сидіти в черзі?
> — **Адміністраторка:** Ні, ви можете почекати біля кабінету. Кабінет лікаря Коваленка знаходиться на другому поверсі.
> — **Петро:** А до лікарки Іванової зараз можна? Може, до неї немає черги?
> — **Адміністраторка:** На жаль, без неї ми не можемо вас прийняти. Вона сьогодні не працює. Зачекайте біля кабінету Коваленка.

When we use personal pronouns like «він» (he), «вона» (she), or «вони» (they) after a preposition, we must add the letter «н» at the beginning of the pronoun. The receptionist says «у нього» instead of «у його». This rule applies to all indirect cases when a preposition is present. For example, if Petro asks about a female doctor, he says «до неї» (to her). If the doctor is not there, we say «без неї» (without her). If Petro talks about the doctors in plural, he might ask: «Чи є ліки для них?» (Are there medicines for them?). Without a preposition, the letter «н» is simply dropped: «Я бачу його» (I see him).

Петро піднімається на другий поверх і заходить до кабінету.

> — **Лікар:** Добрий день, пане Петре. Сідайте, будь ласка. Що вас сьогодні турбує?
> — **Петро:** Добрий день, лікарю. Мені дуже погано.
> — **Лікар:** Розкажіть детальніше. Що саме у вас болить?
> — **Петро:** У мене болить голова і горло. Також я прийшов з високою температурою і страшним кашлем.
> — **Лікар:** Яка у вас **температура** *(temperature)* зараз?
> — **Петро:** Тридцять вісім і п'ять. Я відчуваю сильну слабкість у всьому тілі.
> — **Лікар:** Зрозуміло. Мені потрібно вас уважно оглянути. Відкрийте рот і скажіть "А-а-а".
> — **Петро:** А-а-а. Це дуже неприємно.
> — **Лікар:** Так, ваше горло дуже червоне. Ви маєте класичну застуду, пане Петре. Ваші легені чисті, це добре.

Notice how Petro describes his health. In English, you say "I have a headache". In Ukrainian, the body part is the subject in the Nominative case, and it performs the action of hurting. The verb is «боліти» (to hurt). Petro says «у мене болить голова» (literally: "at me the head hurts"). If multiple things hurt, the verb changes to plural: «у мене болять очі» (my eyes hurt). When describing a general state, we use the Dative case with an adverb: «мені погано» (to me it is bad) or the reflexive verb «почуватися» (to feel). You can simply say «я погано почуваюся».

> — **Лікар:** Я випишу вам **рецепт** *(prescription)*. Вам потрібно **приймати ліки** *(to take medicine)* тричі на день після їжі. Це дуже важливо.
> — **Петро:** Дякую. А що ще мені потрібно робити вдома?
> — **Лікар:** Я раджу вам багато спати. Пийте гарячий чай з лимоном і медом. Ваш організм потребує відпочинку.
> — **Петро:** Добре. Коли мені прийти на наступний **огляд** *(examination)*?
> — **Лікар:** Приходьте до мене через п'ять днів. Якщо вам раптом стане гірше, телефонуйте одразу. Бажаю вам міцного **здоров'я** *(health)*!
> — **Петро:** Дуже дякую вам за допомогу, пане докторе! До побачення.

<!-- INJECT_ACTIVITY: fill-in-rewrite-dialogue-sentences-changing-singular-to-plural-e-g -->


## Діалог 3: Подорож Україною

Україна — дуже велика і красива країна. Тарас та Ірина планують велику **подорож** *(trip)*. Вони хочуть побачити нове **місто** *(city)* і високі **гори** *(mountains)*. Також вони мріють поїхати на південь, де тече широка **річка** *(river)*. Їхній маршрут дуже довгий. Він іде через усю країну, майже від одного **кордону** *(border)* до іншого. Давайте послухаємо їхню розмову.

> — **Тарас:** Ірино, куди ми поїдемо у відпустку цього літа?
> — **Ірина:** Я дуже хочу поїхати до **Львова** *(Lviv)*. Я так люблю старі вулиці цього прекрасного міста.
> — **Тарас:** Це чудова ідея! Але може спочатку ми маємо відвідати **Одесу** *(Odesa)*? Ми дуже давно там не були.
> — **Ірина:** Добре, я згодна. А після Одеси ми поїдемо на захід країни?
> — **Тарас:** Саме так. З Одеси ми поїдемо просто до Львова. А потім я дуже хочу відпочивати в **Карпатах** *(Carpathians)*.
> — **Ірина:** О, я теж мрію про Карпати! Ми можемо знайти тихий будиночок біля гірської річки.
> — **Тарас:** Ідеальний план. Ми точно побачимо дуже багато гарних місць під час подорожі.

In this dialogue, Taras and Iryna use different cases for destinations. When they talk about moving towards a city, they use the Genitive case with the preposition «до». For masculine cities, the ending is usually «-а» or «-у». For example, they say «до Львова» and «до Києва» (to Kyiv). When they talk about the city as a direct object, they use the Accusative case: «відвідати Одесу» (to visit Odesa). The mountains «Карпати» only exist in the plural form. When Taras talks about being inside the mountains, he uses the Locative plural with the preposition «в»: «в Карпатах». If they wanted to go *to* the mountains, they would say «в Карпати» using the Accusative case for direction.

> — **Ірина:** Як саме ми будемо туди їхати? Будемо подорожувати **потягами** *(trains)* чи **машинами** *(cars)*?
> — **Тарас:** Я думаю, що набагато краще їхати нашою власною машиною. Так ми матимемо більше свободи під час подорожі.
> — **Ірина:** Повністю згодна. Ми зможемо зупинятися там, де тільки захочемо.
> — **Тарас:** Так, адже по дорозі є дуже багато **визначних місць** *(landmarks)*. Ми обов'язково відвідаємо кілька старовинних замків.
> — **Ірина:** Чудово! А ми запросимо когось із собою? Ми ж можемо поїхати з нашими **друзями** *(friends)*.
> — **Тарас:** Звісно! Я сьогодні запитаю Олега та Марію. З ними завжди надзвичайно весело подорожувати.
> — **Ірина:** Прекрасно. Тільки нам треба взяти з собою достатньо **грошей** *(money)* на пальне та їжу.
> — **Тарас:** Не хвилюйся про це, я вже все детально порахував.

Notice the Instrumental case in the plural. When Iryna asks about the method of transport, she says «потягами» or «машинами». The endings «-ами» and «-ями» are standard for the Instrumental plural. They also use this case to say *with whom* they are traveling: «з друзями». The word «гроші» is another noun that only exists in the plural. In the Genitive case, it becomes «грошей» (of money). If you need to use it in the Instrumental case (for example, to pay *with money*), you can use a unique, older ending «-ми» and say «грішми». You can also use the standard form «грошима». Both are correct and natural.

> — **Ірина:** Отже, ми їдемо до Львова. Але там часто йде дощ.
> — **Тарас:** Нічого страшного. Львову дуже пасує дощ. Це навіть романтично.
> — **Ірина:** Можливо, ти маєш рацію. А що ми будемо там робити?
> — **Тарас:** Ми будемо багато гуляти по **Хрещатику** *(Khreshchatyk)*... Ой, я переплутав! Хрещатик у Києві.
> — **Ірина:** Смішно! Ми будемо гуляти по старих площах Львова, а потім підемо гуляти по горах.
> — **Тарас:** Домовилися. Це буде найкраща відпустка у нашому житті!

<!-- INJECT_ACTIVITY: match-up-match-sentence-halves-ensuring-case-agreement-with-prepositions-verbs -->


## Самоперевірка: Знайди помилку

Часто ми робимо помилки, коли перекладаємо фрази з англійської мови слово в слово. English speakers often use direct translation for common phrases. In Ukrainian, we use a completely different structure. Ми кажемо: «У мене болить голова». Інша типова помилка — це прийменник «по». In Ukrainian, when we talk about moving across a surface, we must use the Locative case. Тому ми кажемо: «Ми гуляли по горах». Ми не використовуємо давальний відмінок у цій ситуації.

Ось коротка **шпаргалка** *(cheat sheet)*, яка допоможе вам швидко перевірити себе:

1. **Називний** *(Nominative)*: Хто? Що? Це головне слово в реченні. The person or thing doing the action.
2. **Родовий** *(Genitive)*: Кого? Чого? Ми використовуємо його, коли чогось немає («немає часу») або коли ми щось маємо («у мене є»). Також він потрібен для кількості («багато друзів») або після прийменників «з», «від», «для», «без».
3. **Давальний** *(Dative)*: Кому? Чому? Він показує напрямок дії («дати другові») або фізичний стан («мені тепло», «мені подобається»).
4. **Знахідний** *(Accusative)*: Кого? Що? Ми вживаємо його для об'єкта дії («бачу машину»). Також він показує напрямок руху з прийменниками «в» чи «на» («їду в місто»).
5. **Орудний** *(Instrumental)*: Ким? Чим? Використовуйте його для інструмента дії («писати ручкою») або коли робите щось разом («з друзями»).
6. **Місцевий** *(Locative)*: На/У кому? чому? Цей відмінок завжди потребує прийменника («в», «на», «по», «при»). Він показує місце («жити в Києві») або рух по поверхні («йти по вулиці»).
7. **Кличний** *(Vocative)*: Ми вживаємо цей відмінок, коли звертаємося до людини («Олеже!», «Маріє!»).

Давайте розглянемо три типові помилки та виправимо їх. Look at these buggy sentences and how to fix them:

* *«Я допомагаю мою сестру.»* Дієслово «допомагати» завжди вимагає давального відмінка, а не знахідного. The correct version is different. Ми маємо сказати: «Я допомагаю моїй сестрі».
* *«Ми їхали по потягу.»* Прийменник «по» з місцевим відмінком означає рух по поверхні. If you want to say by train, you need the Instrumental case without a preposition. Правильний варіант: «Ми їхали потягом». You could also use the Locative case if you mean inside the train. Тоді ми скажемо: «Ми їхали в потязі».
* *«У театрі було багато студенти.»* Після слова «багато» ми завжди маємо використовувати родовий відмінок множини. The correct sentence is different. Правильно буде: «У театрі було багато студентів».

The best strategy for self-correction is the check we learned before. Завжди перевіряйте дієслово або прийменник перед іменником. They dictate the rules. Вони вирішують, який відмінок треба використати в реченні.

<!-- INJECT_ACTIVITY: error-correction-all-cases -->

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: all-cases-practice
level: a2

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "Оберіть правильний варіант"
    items:
      - question: "_____ стіл"
        options: ["мій", "моя", "моє"]
        correct: 0             # 0-based index

  - id: another-marker-id
    type: fill-in
    instruction: "Вставте правильне слово"
    items:
      - sentence: "Це ____ кімната."
        answer: "моя"
        options: ["мій", "моя", "моє"]

workbook:
  - type: match-up
    instruction: "З'єднайте пари"
    pairs:
      - left: "стіл"
        right: "він"
      - left: "книга"
        right: "вона"
      - left: "вікно"
        right: "воно"

  - type: group-sort
    instruction: "Розподіліть слова за категоріями"
    groups:
      - label: "Category A"
        items: ["word1", "word2"]
      - label: "Category B"
        items: ["word3", "word4"]

  - type: true-false
    instruction: "Правда чи ні?"
    items:
      - statement: "Statement here"
        correct: true
        explanation: "Why it's true"

  - type: error-correction
    instruction: "Виправте помилку"
    items:
      - sentence: "Sentence with error"
        error: "wrong word"
        correction: "correct word"
        error_type: "word"
        options: ["option1", "option2", "option3"]
        explanation: "Why it's wrong"

  - type: observe
    examples:
      - "example sentence 1"
      - "example sentence 2"
    prompt: "What pattern do you notice?"

  - type: translate
    instruction: "Оберіть правильний переклад"
    items:
      - source: "English phrase"
        options:
          - text: "correct Ukrainian"
            correct: true
          - text: "wrong Ukrainian"
            correct: false

  - type: anagram
    instruction: "Складіть слово з літер"
    items:
      - letters: ["к", "н", "и", "г", "а"]
        answer: "книга"
        hint: "book"

  - type: order
    instruction: "Розставте речення в правильному порядку"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— Служба порятунку, слухаю вас."
      - "— Допоможіть! Тут пожежа!"
      - "— Де ви?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "Складіть правильне речення зі слів"
    items:
      - words: ["швидку!", "Викличте"]            # Jumbled words
        correct_order: ["Викличте", "швидку!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["потрібен", "Мені", "лікар."]
        correct_order: ["Мені", "потрібен", "лікар."]
        hint: "Dative + потрібен + noun"

  - type: error-correction
    instruction: "Знайдіть і виправте помилку"
    items:
      - sentence: "Мені потрібна лікар."
        error: "потрібна"
        correction: "потрібен"
        error_type: "word"           # MUST be one of: "word", "phrase", "register", "construction"
        options: ["потрібен", "потрібне", "потрібно"]
        explanation: "Лікар is masculine, so потрібен."
```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Optional: hint. Example: word: "молоко", answer: "мо-ло-ко"
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "яблуко", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["ка", "май", "ре"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["кіт", "пес", "молоко"], correct: 2, explanation: "молоко — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH):
- **critical-analysis**: Required: id, prompt. Optional: evaluation_criteria[]
- **essay-response**: Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Required: id, passage, questions[]
- **source-evaluation**: Required: id, source_text, criteria[], guiding_questions[]

---

## Learner Level Context

**Level: A2 (Module 37/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-cases [§4.2.3.1, §4.2.3.2, §4.2.3.3]
**Відмінки іменників** (Noun cases)
- **fill-in** — Який відмінок?: Вставити іменник у правильній відмінковій формі / Fill in the correct case ending for a noun in context
  - Instruction: *Вставте іменник у правильній формі*
- **quiz** — Визнач відмінок: Визначити, у якому відмінку стоїть виділений іменник / Identify which case a highlighted noun is in
- **group-sort** — Розподіли за відмінками: Розподілити форми іменників за відмінками / Sort noun forms by their case
- **error-correction** — Знайди помилку у відмінку: Знайти неправильне відмінкове закінчення та виправити / Find wrong case ending and correct it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Учні мають ПРОДУКУВАТИ форми, а не тільки розпізнавати. Обов'язково fill-in
- ❌ translate: Англійська не має відмінків — переклад не тестує відмінювання

### Pattern: grammar-pronouns [§4.2.1.4, §4.2.2]
**Особові займенники** (Personal pronouns)
- **match-up** — Займенник → дієслово: Зіставити особовий займенник із правильною формою дієслова — зв'язок займенника з дієвідмінюванням / Match personal pronoun with correct verb form — linking pronouns to conjugation
  - Instruction: *З'єднайте займенник із дієсловом*
- **fill-in** — Вставте займенник: Обрати правильний займенник за контекстом речення / Choose the correct pronoun based on sentence context
  - Instruction: *Вставте правильний займенник*
- **group-sort** — Однина чи множина?: Розподілити займенники на однину та множину / Sort pronouns into singular and plural
  - Instruction: *Розподіліть*
- **quiz** — Ти чи Ви?: Обрати правильну форму звертання — неформальне (ти) чи ввічливе (Ви) / Choose correct address form — informal (ти) vs polite (Ви)
**Anti-patterns (DO NOT generate):**
- ❌ translate: Займенники — про зв'язок з дієсловом, а не переклад

### Pattern: grammar-pluralization [§4.2.1.1]
**Множина іменників** (Noun plurals)
- **fill-in** — Утвори множину: Утворити множину іменника — закінчення -и vs -і залежно від приголосного / Form noun plural — -и vs -і endings depending on consonant
  - Instruction: *Напишіть множину*
- **group-sort** — Закінчення -и чи -і?: Розподілити іменники за типом закінчення множини / Sort nouns by plural ending type
  - Instruction: *Розподіліть*
- **match-up** — Однина → множина: Зіставити форму однини з формою множини / Match singular form to plural form
  - Instruction: *З'єднайте*
- **error-correction** — Виправ множину: Знайти неправильну форму множини та виправити / Find incorrect plural form and fix it
**Anti-patterns (DO NOT generate):**
- ❌ quiz-only: Множина — це словотворення. Учні мають продукувати форми, а не тільки вибирати
- ❌ fill-in-no-options: На A1 завжди давати варіанти — учень ще не знає всіх закінчень

### Pattern: general-reading [§1 (Speech activities — reading)]
**Розуміння тексту** (Reading comprehension)
- **true-false** — Правда чи ні?: Перевірити розуміння тексту або діалогу / Check comprehension of a passage or dialogue
- **quiz** — Відповідь на запитання: Відповісти на запитання за текстом / Answer questions about a text passage


**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ITEM COUNT MINIMUMS (non-negotiable):**
- **Default minimum: 6 items per activity.** Quiz = 6+, fill-in = 6+, match-up = 6+ pairs, true-false = 6+, anagram = 6+, error-correction = 6+, translate = 6+, divide-words = 6+, count-syllables = 6+, odd-one-out = 6+.
- **Lower minimums for specific types:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items.
- If you can't think of enough items, add more examples from the module's vocabulary and content.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

**Instructions match learner level:**
1. **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
2. **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
3. **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
4. **A2+:** Instructions in Ukrainian.
5. **B1+:** Full Ukrainian, no English.

**Other rules:**
6. **No duplicate options** — each option in a quiz item must be unique
7. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
8. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
9. **Min 6 pairs for match-up** — to prevent trivial elimination
10. **Explanations for true-false and error-correction** — help the learner understand WHY
11. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:



---

## Live Verification Tools (MCP)

You have access to RAG-powered MCP tools to verify Ukrainian language constructs **live as you write**. The research phase is already complete; use these tools strictly for targeted verification to ensure zero Russianisms, accurate grammar, and authentic usage.

**Core Tools:**
- `mcp_rag_verify_words` / `mcp_rag_verify_word` / `mcp_rag_verify_lemma` — VESUM morphological dictionary (409K lemmas, 6.7M forms). Returns full declension/conjugation.
- `mcp_rag_search_text` — Ukrainian school textbooks (Grades 1-11, 23K chunks).
- `mcp_rag_search_literary` — Primary literary sources (chronicles, poetry, legal texts).
- `mcp_rag_query_pravopys` — Official Ukrainian orthography rules (Правопис 2019).
- `mcp_rag_query_wikipedia` — Ukrainian Wikipedia.

**Dictionary Tools (NEW — use these for quality):**
- `mcp_rag_search_style_guide` — **Антоненко-Давидович (279 entries). HIGH PRIORITY.** Identifies calques and Russianisms. Use when unsure if a phrase is natural Ukrainian.
- `mcp_rag_query_cefr_level` — PULS CEFR vocabulary (5.9K words). Check if a word is level-appropriate (A1/A2/B1 etc.).
- `mcp_rag_search_definitions` — СУМ-11 (127K entries). Look up exact Ukrainian definitions.
- `mcp_rag_search_etymology` — Грінченко (67K entries). Historical forms, etymology.
- `mcp_rag_search_idioms` — Фразеологічний (25K entries). Find natural Ukrainian idioms.
- `mcp_rag_search_synonyms` — Ukrajinet WordNet (122K synsets). Synonyms, antonyms.
- `mcp_rag_translate_en_uk` — Балла EN→UK (79K entries). English→Ukrainian translations.
- `mcp_rag_query_grac` — GRAC corpus (2B tokens). Check word frequency, collocations, concordance. Use when unsure if a collocation is natural.
- `mcp_rag_query_ulif` — ULIF morphological paradigms. Full declension/conjugation tables. Use when verify_lemma isn't enough.
- `mcp_rag_query_r2u` — Russian→Ukrainian equivalents. Use when you suspect a word might be a Russicism — finds the proper Ukrainian alternative.

**WHEN to use tools (Specific Triggers):**

1. **Suspected Russianisms or Surzhyk (HIGH PRIORITY):**
   - *Trigger:* You are about to use a word that sounds similar to Russian, a calque, or you are unsure of its exact Ukrainian equivalent.
   - *Action:* Use `mcp_rag_search_style_guide` first (it knows calques). Then `mcp_rag_query_r2u` for the proper Ukrainian equivalent. Then verify with `mcp_rag_verify_words`.
   - *Example:* Checking *приймати участь* (calque) → *брати участь* (correct).

2. **Vocabulary Level Check:**
   - *Trigger:* You are writing for A1/A2 and want to ensure words are level-appropriate.
   - *Action:* Use `mcp_rag_query_cefr_level` to verify the word's CEFR level.

3. **Grammar & Morphology Doubts:**
   - *Trigger:* You are unsure about a case ending, irregular plural, or conjugation.
   - *Action:* Use `mcp_rag_verify_lemma` to pull the complete declension/conjugation.

4. **Natural Expressions:**
   - *Trigger:* You need a natural idiom or collocation for a dialogue.
   - *Action:* Use `mcp_rag_search_idioms` for Ukrainian expressions, `mcp_rag_search_synonyms` for word variety.

5. **Drafting Grammar Rules:**
   - *Trigger:* You are explaining a spelling or phonetic rule.
   - *Action:* Use `mcp_rag_query_pravopys` to confirm the exact 2019 standard.

6. **Checking Collocations & Frequency:**
   - *Trigger:* You want to confirm a word combination is actually used by native speakers.
   - *Action:* Use `mcp_rag_query_grac` with mode='collocations' to see real-world usage.

**MANDATORY Verification (these are NOT optional):**

7. **Letter/Sound Decomposition (ALWAYS VERIFY):**
   - *Trigger:* You are listing the letters, sounds, or syllables of ANY Ukrainian word.
   - *Action:* BEFORE writing the decomposition, call `mcp_rag_verify_word` on that word. The response shows the exact letter forms. Use ONLY what the tool returns. NEVER decompose a word from memory — your pre-training has wrong letter mappings (e.g., confusing и/і, я/а in specific words). This is the #1 source of errors.
   - *Example:* Before writing 'вулиця has letters В, У, Л...', call `mcp_rag_verify_word("вулиця")` and copy the letters from the result.

8. **Phonetic Claims (ALWAYS VERIFY):**
   - *Trigger:* You are stating how a letter sounds in a specific word, how many syllables a word has, or where stress falls.
   - *Action:* Call `mcp_rag_verify_word` to confirm. Ukrainian letters like є, ї, я, ю change sound value depending on position (after consonant vs word-initial). Do NOT guess — verify each claim.

9. **ANY Factual Claim About Ukrainian (VERIFY WHEN POSSIBLE):**
   - *Trigger:* You are stating a grammar rule, exception, or linguistic fact.
   - *Action:* Use `mcp_rag_query_pravopys` or `mcp_rag_search_text` to confirm. If you can't verify it, flag with `<!-- VERIFY: claim -->`.

**Efficiency Rules:**
- **Batch your checks:** Use `mcp_rag_verify_words` with 5-15 words at once.
- **Do NOT verify basic words:** *мама*, *стіл*, *робити* don't need checking.
- **Zero invention:** If VESUM doesn't know a word, don't use it.
- **Target: 10-20 tool calls per module** (was 8-15; mandatory checks added).

IMPORTANT: After using tools, output your COMPLETE module content as plain text. Do NOT narrate your tool usage. Just output the final module content.


**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be a2-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.

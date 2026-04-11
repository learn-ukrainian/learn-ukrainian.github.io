<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/preferences-and-choices.yaml` file for module **59: Я обираю, я вважаю** (a2).

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

- `<!-- INJECT_ACTIVITY: quiz-choose-the-appropriate-preference-choice-verb -->`
- `<!-- INJECT_ACTIVITY: fill-in-focus-complete-opinion-sentences-with-correct-connectors-and-instrumental-case-endings -->`
- `<!-- INJECT_ACTIVITY: match-up-focus-match-agreement-disagreement-phrases-to-various-social-debate-situations -->`
- `<!-- INJECT_ACTIVITY: error-correction-opinions -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Choose the appropriate opinion phrase for formal vs informal contexts
  items: 8
  type: quiz
- focus: Complete opinion sentences with correct connectors and comparatives
  items: 8
  type: fill-in
- focus: Match agreement/disagreement phrases to situations
  items: 8
  type: match-up
- focus: Find and correct grammar errors in sentences
  items: 6
  type: error-correction


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- безумовно (absolutely)
- інакше (differently)
- дозволити (to allow, to permit)
- погоджуватися (to agree)
- по-перше (firstly)
required:
- вважати (to think, to consider)
- воліти (to prefer)
- обирати (to choose)
- думка (opinion, thought)
- згоден (agree, m.)
- згодна (agree, f.)
- рація (rightness — in мати рацію)
- тому що (because)
- навпаки (on the contrary)
- переконаний (convinced, m.)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Що тобі більше подобається?

Ми часто говоримо про те, що ми любимо. Для цього ми використовуємо дієслово **подобатися** *(to like)*. Це дієслово завжди працює з **давальним відмінком** *(Dative case)*. Ми кажемо: **«Мені подобається це місто»** *(I like this city)*. Якщо ми запитуємо когось, ми кажемо: **«Тобі подобається ця кава?»** *(Do you like this coffee?)*. Або: **«Їй подобається українська музика»** *(She likes Ukrainian music)*. Це базова конструкція для нашого щоденного спілкування з друзями та родиною.

Але що робити, коли ми маємо дві або більше речей? Тоді ми порівнюємо. Для цього ми використовуємо фразу **більше подобається ... ніж ...** *(like more ... than ...)*. Ми можемо легко порівнювати різні **іменники** *(nouns)*. Наприклад: **«Мені більше подобається кава, ніж чай»** *(I like coffee more than tea)*. Ми також можемо порівнювати наші дії. Для цього ми беремо **інфінітив** *(infinitive)*. Наприклад: **«Йому більше подобається гуляти в парку, ніж дивитися телевізор»** *(He likes walking in the park more than watching TV)*. Зверніть увагу на кому перед словом **«ніж»** *(than)*. Ми завжди обов'язково ставимо кому перед цим словом в українській мові. Це дуже корисна та часта структура для дискусій.

В українській мові є ще одне чудове дієслово. Це дієслово **воліти** *(to prefer)*. Воно показує більш активний вибір, ніж слово «подобатися». Зазвичай після слова «воліти» ми ставимо дієслово в інфінітиві. Наприклад: **«Я волію читати книги ввечері»** *(I prefer to read books in the evening)*. Або: **«Вона воліє пити воду, а не сік»** *(She prefers to drink water, not juice)*. Ми також порівнюємо дії: **«Ми воліємо йти пішки, ніж їхати автобусом»** *(We prefer walking to taking a bus)*. Це дієслово звучить дуже природно та красиво.

Процес вибору — це важлива частина нашого життя. Для цього ми маємо дієслова **обирати** *(to choose - imperfective)* та **обрати** *(to choose - perfective)*. Дієслово «обирати» належить до першої дієвідміни. Його форми: я обираю, ти обираєш, він обирає, ми обираємо, ви обираєте, вони обирають. Ми кажемо: **«Я обираю цей фах»** *(I choose this profession)*. Або: **«Вона обирає нову сукню»** *(She is choosing a new dress)*. Будьте дуже обережні з англійською калькою "to choose to do something". В українській мові ми так не говоримо. Ми ніколи не кажемо *«я обираю залишитися вдома»*. Замість цього ми використовуємо дієслово **вирішити** *(to decide)*. Правильно буде сказати: **«Я вирішив залишитися вдома»** *(I decided to stay home)*. Це звучить набагато краще та природніше.

Давайте подивимося, як ці слова працюють у реальній розмові. Двоє друзів планують свої вихідні.
> — **Марко:** Привіт! Що ми будемо робити в суботу? *(Hi! What are we going to do on Saturday?)*
> — **Олена:** Привіт! Ми можемо піти в кіно або погуляти в парку. *(Hi! We can go to the cinema or walk in the park.)*
> — **Марко:** Мені більше подобається гуляти в парку, ніж сидіти в темному залі. *(I like walking in the park more than sitting in a dark hall.)*
> — **Олена:** А я волію подивитися новий фільм. *(And I prefer to watch a new movie.)*
> — **Марко:** Добре, тоді я обираю кіно. *(Okay, then I choose the cinema.)*
> — **Олена:** Чудово! Я вирішила купити квитки онлайн. *(Great! I decided to buy tickets online.)*

<!-- INJECT_ACTIVITY: quiz-choose-the-appropriate-preference-choice-verb -->

## На мою думку...

Коли ми хочемо сказати, що ми думаємо, ми використовуємо спеціальні фрази. Найчастіше ми говоримо **«Я вважаю, що...»** *(I think that...)* або **«На мою думку...»** *(In my opinion...)*. Це дуже корисні конструкції для будь-якої розмови. Вони допомагають нам показати нашу позицію. Наприклад: **«На мою думку, українська мова дуже милозвучна»** *(In my opinion, the Ukrainian language is very melodic)*. Зверніть увагу на важливу різницю між словами в українській мові. Дієслово **думати** *(to think)* є нейтральним. Ми використовуємо його щодня, коли говоримо про повсякденні речі. А от дієслово **вважати** *(to consider, to think)* звучить більш формально. Воно показує вашу серйозну, зважену та обдуману позицію. Це слово часто звучить у новинах або під час серйозних дискусій.

Іноді ми не зовсім впевнені у своїх словах. Тоді ми використовуємо чудову фразу **«Мені здається, що...»** *(It seems to me that...)*. Ця фраза робить нашу думку дуже м'якою. Наприклад: **«Мені здається, що завтра буде дощ»** *(It seems to me that it will rain tomorrow)*. Але якщо ми впевнені, ми говоримо інакше. Ми використовуємо прикметник **переконаний** *(convinced)*. Зверніть увагу на закінчення. Чоловік скаже: **«Я переконаний, що...»** *(I am convinced that...)*. Жінка обов'язково скаже: **«Я переконана, що...»** *(I am convinced that...)*. Наприклад: **«Я переконана, що цей фільм дуже цікавий»** *(I am convinced that this movie is very interesting)*. Це дуже сильна позиція. Використовуйте цю фразу, коли ви готові захищати свою думку.

Коли ми висловлюємо думку, ми завжди маємо пояснити причину. Для цього ми використовуємо спеціальні слова-зв'язки. Найпопулярніше слово — це **тому що** *(because)*. Воно ідеально підходить для будь-якої життєвої ситуації. Наприклад: **«Я вважаю, що це важливо, тому що це впливає на наше майбутнє»** *(I think this is important because it affects our future)*. У неформальній розмовній мові ми часто використовуємо коротке слово **бо** *(because)*. Воно звучить швидко і природно. Наприклад: **«Я обираю зелений чай, бо він гарячий»** *(I choose green tea because it is hot)*. Також є чудове слово **адже** *(since, after all)*. Воно додає більше емоцій у ваше речення. Якщо ситуація дуже офіційна, ми кажемо **оскільки** *(since, as)*. Усі ці слова з'єднують дві частини складного речення. Пам'ятайте, що перед цими словами ми завжди ставимо кому.

Дієслово «вважати» має ще одну дуже цікаву граматичну конструкцію. Вона допомагає нам давати оцінку або характеристику іншим людям чи речам. Ми кажемо: **вважати когось або щось** *(to consider someone or something)* **ким або чим** *(as someone or something)*. Після дієслова ми ставимо об'єкт у **Знахідний відмінок** *(Accusative case)*. А характеристику ми ставимо в **Орудний відмінок** *(Instrumental case)*. Наприклад: **«Я вважаю його своїм найкращим другом»** *(I consider him my best friend)*. Або: **«Ми вважаємо цей проєкт успішним»** *(We consider this project successful)*. Зверніть увагу на відмінність від англійської мови. В англійській мові ми часто не використовуємо спеціальні форми слів для такої конструкції. В українській мові зміна закінчення є обов'язковою. Ми завжди використовуємо Орудний відмінок для характеристики об'єкта. Це робить ваше речення правильним і дуже природним.

Ця ж сама граматична конструкція допомагає нам говорити про себе. Ми можемо описувати свій характер, свою національність або професію. Ми використовуємо фразу **вважати себе** *(to consider oneself)* і додаємо потрібне слово в Орудному відмінку. Наприклад: **«Я вважаю себе оптимістом»** *(I consider myself an optimist)*. Або інший приклад: **«Вона вважає себе українкою»** *(She considers herself a Ukrainian)*. Зверніть увагу на ще один дуже важливий момент. В українській мові ми використовуємо тільки дієслово «вважати». Слово «считаю» — це типовий **суржик** *(surzhyk, mixed language)*. Це слово походить з російської мови. Завжди правильно говорити: «Я вважаю», а не «Я считаю». Це правило допомагає вашій українській мові бути чистою, правильною та красивою.

<!-- INJECT_ACTIVITY: fill-in-focus-complete-opinion-sentences-with-correct-connectors-and-instrumental-case-endings -->

## Згоден чи ні?

У житті ми часто дискутуємо з іншими людьми. Коли наша думка збігається з думкою співрозмовника, ми висловлюємо згоду. Найпростіший спосіб сказати про це — використати слово **згоден** *(agree)*. Пам'ятайте про різницю в родах. Чоловік скаже: **«Я згоден»** *(I agree)*. Жінка скаже: **«Я згодна»** *(I agree)*. Ще одна дуже популярна і ввічлива фраза — **«Ви маєте рацію»** *(You are right)*. Вона ідеально підходить для формальних ситуацій та поважного спілкування. З друзями можна сказати коротше: **«Ти маєш рацію»** *(You are right)*. Якщо ви підтримуєте ідею, використовуйте емоційні слова. Можна сказати: **«Безумовно!»** *(Absolutely!)* або **«Саме так!»** *(Exactly!)*. Для офіційної дискусії чудово підходить фраза: **«Цілком погоджуюся»** *(I completely agree)*. Ці вислови роблять вашу мову багатою та впевненою.

Але що робити, коли ваші погляди різні? В українській культурі пряме слово «Ні!» іноді звучить занадто різко. Для культурної та спокійної дискусії ми використовуємо ввічливу незгоду. Найкращий помічник тут — сполучник **але** *(but)*. Він допомагає пом'якшити вашу відповідь. Ви можете почати так: **«Я не зовсім згоден»** *(I don't quite agree)*, якщо ви чоловік, або **«Я не зовсім згодна»** *(I don't quite agree)*, якщо ви жінка. Інший гарний варіант: **«Можливо, але...»** *(Maybe, but...)*. Ця фраза показує, що ви почули людину, але маєте інший погляд. Також можна сказати прямо: **«Я думаю інакше»** *(I think differently)*. А для дуже офіційних зустрічей чи конференцій існує елегантна конструкція: **«Дозвольте не погодитися»** *(Allow me to disagree)*. Вона показує високий рівень поваги до опонента.

Іноді ситуація вимагає сильної незгоди. Це буває, коли співрозмовник помиляється, і ви хочете виправити цю помилку. У таких випадках ми використовуємо чудове слово **навпаки** *(on the contrary)*. Воно повністю розвертає напрямок розмови. Ми часто додаємо до нього дієслово «вважати». Наприклад, хтось каже, що вивчати мови нудно. Ви можете відповісти: **«Навпаки, я вважаю, що це дуже цікаво»** *(On the contrary, I think it is very interesting)*. Це сильний аргумент. Інший приклад: «Це завдання складне? Ні, **навпаки, я вважаю, що це дуже легко»** *(On the contrary, I think that this is very easy)*. Використовуйте цю фразу, щоб впевнено захищати свою позицію.

Часто в житті немає правильних або неправильних речей. Ми можемо погоджуватися лише частково. Для таких складних ситуацій українська мова має ідеальну парну конструкцію. Ми кажемо: **«З одного боку... З іншого боку...»** *(On one hand... on the other hand...)*. Це допомагає показати баланс аргументів. Ми демонструємо, що бачимо всі плюси та мінуси ситуації. Наприклад: **«З одного боку, це швидко, але з іншого боку — це дорого»** *(On one hand, it is fast, but on the other hand, it is expensive)*. Або: **«З одного боку, місто велике, з іншого боку — тут багато шуму»** *(On one hand, the city is big, on the other hand, there is a lot of noise)*. Ще одна корисна фраза для компромісу: **«Це правда, але...»** *(That's true, but...)*.

Давайте подивимося, як ці фрази працюють у реальному житті. Уявіть зустріч книжкового клубу. Друзі обговорюють два літературні твори: великий **роман** *(novel)* і коротку **повість** *(novella)*.

> — **Оксана:** Мені більше подобається цей роман. На мою думку, він дуже глибокий. *(I like this novel more. In my opinion, it is very deep.)*
> — **Степан:** Я не зовсім згоден. Я вважаю, що там занадто багато деталей. *(I don't quite agree. I think there are too many details there.)*
> — **Оксана:** Можливо, але авторка чудово описує характер героїв. *(Maybe, but the author wonderfully describes the characters' personalities.)*
> — **Степан:** Тут ти маєш рацію. Вона пише добре. Але ця нова повість набагато динамічніша! *(Here you are right. She writes well. But this new novella is much more dynamic!)*
> — **Оксана:** Це правда, але вона занадто коротка. З одного боку, читати швидко, а з іншого — хочеться більше. *(That's true, but it is too short. On one hand, it's fast to read, and on the other, you want more.)*

<!-- INJECT_ACTIVITY: match-up-focus-match-agreement-disagreement-phrases-to-various-social-debate-situations -->

## Обговорення: що краще?

Іноді наша думка складна. Коли ми хочемо пояснити її детально, нам потрібні спеціальні слова. Вони допомагають структурувати наші аргументи. Для початку ми використовуємо вступне слово **по-перше** *(firstly)*. Потім ми додаємо наступний логічний аргумент за допомогою слова **по-друге** *(secondly)*. Якщо у нас є ще одна важлива деталь, ми кажемо **крім того** *(moreover)*. І щоб зробити гарний підсумок, ми використовуємо фразу **на завершення** *(in conclusion)*. Наприклад: «Я вважаю, що цей телефон чудовий. По-перше, він працює швидко. По-друге, у нього якісна камера. Крім того, він має красивий дизайн. На завершення скажу, що це найкращий вибір». Спробуйте завжди використовувати ці слова, коли ви пояснюєте свій вибір!

Давайте прочитаємо цікаву дискусію. Уявіть інтернет-форум, де українці обговорюють важливу тему: що краще — життя в місті чи в селі? Зверніть увагу, як люди використовують різні фрази.
> — **Олена:** На мою думку, жити в місті краще. По-перше, тут є хороша робота. По-друге, тут багато цікавих місць. *(In my opinion, living in the city is better. Firstly, there is good work here. Secondly, there are many interesting places here.)*
> — **Тарас:** Я не зовсім згоден. Мені здається, що в селі жити спокійніше. Я волію жити там, бо там красива природа. *(I don't quite agree. It seems to me that living in the village is calmer. I prefer to live there because there is beautiful nature there.)*
> — **Марія:** З одного боку, Тарас має рацію. Але, з іншого боку, в місті краща медицина. Крім того, там зручно. *(On one hand, Taras is right. But, on the other hand, there is better medicine in the city. Moreover, it is convenient there.)*
> — **Ігор:** Безумовно. Але я переконаний, що кожен обирає своє. На завершення скажу: головне — бути щасливим там, де ти живеш! *(Absolutely. But I am convinced that everyone chooses their own. In conclusion I will say: the main thing is to be happy where you live!)*

Ви бачите, що ця дискусія дуже ввічлива. Кожен учасник поважає думку іншого, але має власні аргументи.

Тепер ваша черга активно практикувати! Ваша тема — це кулінарні вподобання. Що краще: готувати вечерю вдома чи їсти в ресторані? Уявіть, що ви розмовляєте з друзями. Використовуйте корисні інструменти з модуля. Скажіть: «Мені більше подобається готувати вдома, ніж ходити в ресторан». Або: «Я волію їсти в кафе, бо це економить час». Додайте логічні аргументи: «На мою думку, домашня їжа здоровіша. По-перше, ви знаєте всі інгредієнти». Якщо партнер каже: «Але в ресторані смачніше!», відповідайте: «Можливо, але це дорого». Або скажіть: «Навпаки, я вважаю, що я готую краще!». Не бійтеся відкрито висловлювати свою власну думку і захищати свій свідомий вибір.

<!-- INJECT_ACTIVITY: error-correction-opinions -->

## Підсумок

Вітаємо! Ви успішно закінчили цей важливий модуль. Тепер ви знаєте, як висловлювати власну думку та робити свідомий вибір.

Зробіть коротку перевірку. Чи можете ви сказати «так» на ці запитання?

- Чи можу я порівнювати дві речі, використовуючи конструкцію **мені більше подобається ... ніж ...** *(I like ... more than ...)*? Наприклад: «Мені більше подобається кава, ніж чай».
- Чи вмію я правильно використовувати дієслово **вважати** *(to consider)* з Орудним відмінком? Наприклад: «Я вважаю його **другом** *(friend)*» або «Я вважаю себе лідером».
- Чи можу я ввічливо погоджуватися або не погоджуватися під час дискусії? Наприклад: «Ви **маєте рацію** *(are right)*» або «Я **не зовсім згоден** *(not quite agree)*».
- Чи розумію я різницю між дієсловами **обирати** *(to choose)* та **вирішити** *(to decide)*?

Збережіть ці ключові фрази для ваших майбутніх розмов:

- **На мою думку...** *(In my opinion...)*
- **Я вважаю, що...** *(I think that...)*
- **Я згоден / Я згодна** *(I agree, m./f.)*
- **Безумовно!** *(Absolutely!)*
- **Навпаки** *(On the contrary)*

Практикуйте ці слова кожного дня. Ваша думка дуже важлива. До зустрічі в наступному модулі!

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: preferences-and-choices
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

**Level: A2 (Module 59/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: grammar-adjectives [§4.2.1.2]
**Прикметники та узгодження** (Adjectives and agreement)
- **fill-in** — Який? Яка? Яке?: Обрати правильне закінчення прикметника за родом іменника / Choose adjective ending to match noun gender
  - Instruction: *Вставте правильну форму*
- **error-correction** — Знайди помилку в узгодженні: Знайти помилку в узгодженні прикметника й іменника за родом/числом / Find gender/number agreement errors between adjective and noun
- **match-up** — Іменник + прикметник: Зіставити іменники з правильними формами прикметників / Match nouns to correct adjective forms
**Anti-patterns (DO NOT generate):**
- ❌ translate: Узгодження — це граматика, а не лексика. Переклад не тестує закінчення

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

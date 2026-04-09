<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/purpose-clauses.yaml` file for module **48: Щоб зрозуміти...** (a2).

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

- `<!-- INJECT_ACTIVITY: fill-in-purpose-clauses-with-correct-form-after -->`
- `<!-- INJECT_ACTIVITY: quiz-distinguish-cause-from-purpose-using-or -->`
- `<!-- INJECT_ACTIVITY: match-up-transform-direct-speech-into-reported-speech-match-the-original-quote-to-its-indirect-version -->`
- `<!-- INJECT_ACTIVITY: unjumble-purpose-clauses -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Complete purpose clauses with the correct form after щоб (infinitive vs.
    past tense form depending on subject)
  items: 8
  type: fill-in
- focus: Choose тому що or щоб to complete sentences — distinguish cause from purpose
  items: 8
  type: quiz
- focus: Transform direct speech into reported speech — match the original quote to
    its indirect version
  items: 8
  type: match-up
- focus: Reorder words to form correct щоб purpose clauses (both infinitive and different-subject
    constructions)
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- навіщо (what for, why)
- передати (to pass on, to relay)
- попросити (to ask, to request)
- пряма мова (direct speech)
required:
- щоб (in order to, so that)
- мета (goal, purpose)
- сказати (to say, to tell)
- відповісти (to answer, to reply)
- пояснити (to explain)
- запитати (to ask)
- повідомлення (message)
- зрозуміти (to understand)
- непряма мова (indirect/reported speech)
- додати (to add)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Щоб + інфінітив: для чого?

Кожного дня ми щось робимо і завжди маємо певну мету. *(Every day we do something and always have a certain goal.)* У нашому житті є багато причин і багато результатів. Коли ми запитуємо **«Чому?»** *(Why?)*, ми шукаємо причину в минулому. Ми хочемо знати, що сталося до нашої дії. Але коли ми запитуємо **«Для чого?»** *(For what?)* або **«Навіщо?»** *(What for?)*, ми дивимося в майбутнє. Ми шукаємо нашу мету. Ми хочемо знати результат.

In English, you often use the infinitive "to" or the phrase "in order to" to express a goal or an intention. В українській мові ми маємо для цього спеціальний інструмент. Ми використовуємо маленьке, але дуже важливе слово — **щоб** *(in order to / so that)*. Це слово допомагає нам пояснити, навіщо ми робимо певну дію. Ми використовуємо його кожного дня.

Найпростіша і найпопулярніша конструкція — це слово **щоб** плюс **інфінітив** *(infinitive)*. Ми використовуємо цю форму, коли тільки одна людина робить дію і має мету. The person performing the main action and the person who wants to achieve the goal are the exact same subject. There is no change in actor between the two parts of the sentence.

Подивіться на цей короткий діалог:
> — **Анна:** Навіщо ти так часто читаєш новини? *(Why do you read the news so often?)*
> — **Марк:** Я читаю новини, **щоб** знати ситуацію у світі. *(I read the news in order to know the situation in the world.)*

У цьому реченні Марк читає новини, і саме Марк хоче знати ситуацію. Суб'єкт один — це «я». Ми просто додаємо «щоб» і дієслово в початковій формі. Ось ще кілька корисних прикладів з одним суб'єктом:
* Мій брат прийшов, **щоб** допомогти мені з ремонтом. *(My brother came to help me with the renovation.)*
* Влітку ми поїхали в Київ, **щоб** побачити це чудове місто. *(In summer we went to Kyiv to see this wonderful city.)*
* Треба багато працювати кожного дня, **щоб** жити добре і комфортно. *(One needs to work a lot every day in order to live well and comfortably.)*
* Я купив новий словник, **щоб** вивчати нові слова швидше. *(I bought a new dictionary to learn new words faster.)*

Але що робити, коли суб'єкти різні? What if one person does the main action, but the goal or intention involves someone else doing something? In this case, we cannot use the infinitive anymore. Ми використовуємо слово **щоб** і дієслово у формі **минулого часу** *(past tense)*.

This rule might seem very strange at first. However, after the word "щоб", the past tense form does not actually mean the action happened in the past. Here, it functions as a subjunctive mood. It expresses a wish, a request, or an instruction for someone else. The verb must strictly agree in gender and number with the new subject of the second part of the sentence.

If I do something so that my friend can do something else, we have two different actors. The first actor does the action. The second actor is the focus of the goal. Подивіться на цей діалог між друзями:
> — **Ірина:** Навіщо ти купив два квитки в кіно? *(Why did you buy two tickets to the cinema?)*
> — **Антон:** Я купив їх, **щоб** ти пішла зі мною. *(I bought them so that you would go with me.)*

У цьому діалозі Антон купує квитки. Це його дія. Але він має мету для Ірини. Він хоче, щоб Ірина пішла з ним. Суб'єкти різні. Тому він використовує слово «щоб» і дієслово «пішла» у формі минулого часу. Це жіночий рід, тому що суб'єкт тут — Ірина.

Зверніть увагу на ці приклади з різними суб'єктами:
* Я зателефонував вчора, **щоб** вона знала про нашу зустріч. *(I called yesterday so that she would know about our meeting.)*
* Вчитель довго пояснював нове правило, **щоб** учні зрозуміли граматику. *(The teacher explained the new rule for a long time so that the students would understand the grammar.)*
* Мама дала синові гроші, **щоб** він купив свіжий хліб. *(Mom gave her son money so that he would buy fresh bread.)*
* Ми відкрили вікно, **щоб** кіт міг вийти на вулицю. *(We opened the window so that the cat could go outside.)*

Ця конструкція з минулим часом дуже часто використовується з дієсловом **хотіти** *(to want)*. Ми використовуємо її, коли говоримо про наші бажання щодо інших людей. In English, you comfortably use the structure "I want you to do something". В українській мові ми так ніколи не говоримо. Ми не можемо просто перекласти слова і сказати «Я хочу тебе допомогти». Це буде велика граматична помилка!

Замість цього ми завжди використовуємо слово **щоб** і форму минулого часу. Literally, you say "I want that you did something". Це звучить незвично для англомовних людей, але це природна українська граматика. Let's look at a typical conversation between a mother and her son:
> — **Мама:** Олег, я хочу, **щоб** ти зробив домашнє завдання. *(Oleh, I want you to do your homework.)*
> — **Олег:** Але я хочу, **щоб** ми пішли в парк! *(But I want us to go to the park!)*
> — **Мама:** Спочатку уроки. Вчителька хоче, **щоб** усі діти добре знали математику. *(Lessons first. The teacher wants all children to know math well.)*

У цьому тексті мама говорить про свої бажання. Вона використовує слово «щоб» і дієслово «зробив». Це чоловічий рід, тому що суб'єкт — її син Олег.

* Я дуже хочу, **щоб** ти був щасливий кожного дня. *(I really want you to be happy every day.)* (Speaking to a male).
* Ми всі хочемо, **щоб** війна в Україні закінчилася якнайшвидше. *(We all want the war in Ukraine to end as soon as possible.)*
* Мій тато хоче, **щоб** я прибрала свою кімнату сьогодні. *(My dad wants me to clean my room today.)* (The speaker is female).
* Вона хоче, **щоб** ми прийшли в гості на вихідних. *(She wants us to come visit on the weekend.)*
* Керівник хоче, **щоб** ви зробили цей проєкт завтра. *(The manager wants you to do this project tomorrow.)*

Пам'ятайте це важливе правило: після конструкції «хочу, щоб» ніколи не буває теперішнього або майбутнього часу. Там завжди стоїть тільки дієслово у формі минулого часу.

Дуже важливо розуміти різницю між словами **тому що / бо** *(because)* та словом **щоб** *(in order to / so that)*. Вони відповідають на абсолютно різні запитання і мають різну логіку в реченні.

Слово «бо» або «тому що» показує нам причину. It explains why something is already happening based on a fact, a feeling, or a past event. Слово «щоб» показує нам мету або результат. It looks forward to what you want to achieve or what you want someone else to do.

Порівняйте ці два дуже схожі речення:
* Я зараз вчу українську мову, **бо** мені дуже цікаво. *(I am studying the Ukrainian language now because it is very interesting to me.)* Це ваша причина. Ви маєте інтерес.
* Я зараз вчу українську мову, **щоб** добре знати її. *(I am studying the Ukrainian language now in order to know it well.)* Це ваша мета на майбутнє.

Подивіться на інші приклади з життя:
* Він зараз п'є воду, **тому що** він хоче пити. *(He is drinking water now because he is thirsty.)* Це факт і причина дії.
* Він взяв пляшку води, **щоб** пити її в дорозі. *(He took a bottle of water to drink it on the way.)* Це його план і мета.
* Вона не пішла гуляти, **бо** на вулиці йде дощ. *(She didn't go for a walk because it is raining outside.)*
* Вона взяла велику парасольку, **щоб** не бути мокрою. *(She took a large umbrella so as not to be wet.)*

<!-- INJECT_ACTIVITY: fill-in-purpose-clauses-with-correct-form-after -->
<!-- INJECT_ACTIVITY: quiz-distinguish-cause-from-purpose-using-or -->


## Базова непряма мова: він сказав, що...

У житті ми дуже часто передаємо інформацію іншим людям. *(In life, we very often pass information to other people.)* Це працює як естафета. Хтось сказав вам цікаву новину, а ви говорите її своєму другу або колезі. Це називається **непряма мова** *(indirect speech)*. Нам обов'язково потрібно знати, як правильно сказати слова іншої людини. We use indirect speech to relay messages from friends, report news from television, or tell a story about a conversation you had yesterday. At this level, we will focus on the most basic and common pattern: reporting what someone said using the connector **що** *(that)*. Це дуже корисна граматична структура для щоденного спілкування. *(This is a very useful grammatical structure for daily communication.)* Ви будете використовувати її майже кожного дня на роботі або вдома. *(You will use it almost every day at work or at home.)*

Коли ми передаємо факт або звичайну новину, ми використовуємо дієслово **сказати** *(to say / to tell)* і слово «що». The most important rule in Ukrainian reported speech is that we always keep the original tense of the verb. There is absolutely no "backshifting" of tenses like there is in English grammar. Якщо людина зараз говорить у майбутньому часі, ми також використовуємо майбутній час. *(If a person speaks in the future tense now, we also use the future tense.)* Ми змінюємо тільки особу і займенники. Let's look at exactly how to transform **пряма мова** *(direct speech)* into indirect speech.
*   Пряма мова: «Я прийду завтра на роботу». *(Direct speech: "I will come to work tomorrow.")*
*   Непряма мова: Він сказав, **що** прийде завтра на роботу. *(Indirect speech: He said that he would come to work tomorrow.)*

Notice how the pronoun «я» logically changes to «він». However, the verb «прийду» (future) simply becomes «прийде» (future) to match the new pronoun. The time remains the future.
*   «Ми тут у ресторані». -> Вони сказали, **що** вони тут у ресторані. *("We are here in the restaurant." -> They said that they were here in the restaurant.)*
*   «Я дуже хочу їсти». -> Вона сказала, **що** дуже хоче їсти. *("I really want to eat." -> She said that she really wanted to eat.)*
*   «Я не знаю цю людину». -> Він сказав, **що** він не знає цю людину. *("I don't know this person." -> He said that he didn't know this person.)*

Звісно, ми можемо використовувати багато інших дієслів, а не тільки слово «сказати». У звичайній розмові ми часто використовуємо дієслова **відповісти** *(to answer / to reply)*, **пояснити** *(to explain)* та **додати** *(to add)*. Ці слова роблять нашу мову значно багатшою і цікавішою. *(These words make our language significantly richer and more interesting.)* They all follow the exact same grammatical structure. We put the reporting verb, then a comma, then the word «що», and finally the reported clause.
*   Вона **пояснила**, що не може прийти на зустріч. *(She explained that she could not come to the meeting.)*
*   Він **додав**, що буде пізно ввечері. *(He added that he would be late in the evening.)*
*   Я **відповів**, що все чудово розумію. *(I answered that I understood everything perfectly.)*
*   Новий вчитель **пояснив**, що це нове граматичне правило. *(The new teacher explained that this was a new grammatical rule.)*
*   Директор **додав**, що цей проєкт дуже важливий для нас. *(The director added that this project was very important for us.)*
*   Ми **відповіли**, що вже готові працювати. *(We replied that we were already ready to work.)*

Ці нові дієслова допомагають нам точно передати ситуацію та емоції. *(These new verbs help us accurately convey the situation and emotions.)*

Але як правильно передати питання від іншої людини? *(But how do we correctly convey a question from another person?)* Якщо питання не має спеціального питального слова (як-от хто, що, де, коли), ми використовуємо цікаве слово **чи** *(if / whether)*. Це звичайне питання, на яке ви можете відповісти тільки «так» або «ні». *(This is a normal question to which you can answer only "yes" or "no".)* When reporting a yes/no question to someone else, we must use the verb **запитати** *(to ask)*. Then we introduce the reported question using the word «чи». Ми ніколи не ставимо знак питання в кінці такого речення. *(We never put a question mark at the end of such a sentence.)*
*   Пряма мова: «Ти будеш пити каву?» *(Direct speech: "Will you drink coffee?")*
*   Непряма мова: Він запитав, **чи** я буду пити каву. *(Indirect speech: He asked if I would drink coffee.)*

Зверніть увагу на структуру. *(Pay attention to the structure.)* Ми просто додаємо слово «чи» перед фактом.
*   «Ви знаєте це гарне місто?» -> Вона запитала, **чи** ми знаємо це гарне місто. *("Do you know this beautiful city?" -> She asked if we knew this beautiful city.)*
*   «Ти маєш вільний час?» -> Мій брат запитав, **чи** я маю вільний час. *("Do you have free time?" -> My brother asked if I had free time.)*
*   «Він працює сьогодні в офісі?» -> Я запитав, **чи** він працює сьогодні в офісі. *("Is he working in the office today?" -> I asked whether he was working in the office today.)*

Тепер ми підходимо до дуже важливого і складного моменту. *(Now we come to a very important and difficult point.)* Ми маємо чітко розуміти різницю між фактами та проханнями або наказами. *(We must clearly understand the difference between facts and requests or orders.)* This is a tricky area where many students make a mistake because the English language uses completely different structures for these two things. В українській мові ми використовуємо слово «що» тільки для фактів, новин та інформації. Але ми обов'язково використовуємо слово «щоб» для наказів, прохань або строгих інструкцій. One small letter totally changes the entire meaning of your sentence from "He said that..." to "He said to...".

Подивіться дуже уважно на ці два речення. Вони дуже схожі, але вони мають абсолютно різний зміст:
1.  Він сказав, **що** я прийшов. *(He said that I came.)*
Це просто факт. *(This is simply a fact.)* Він розповів комусь про мій прихід додому. He is reporting the objective news of my arrival.
2.  Він сказав, **щоб** я прийшов. *(He told me to come.)*
Це прохання або строгий наказ. *(This is a request or a strict order.)* Він хоче бачити мене зараз. He is giving an instruction for me to arrive.

Пам'ятайте важливе правило з попередньої частини нашого уроку. Після слова «щоб» ми завжди ставимо дієслово у формі минулого часу.
*   Мама сказала, **що** вона купила свіжий хліб. *(Mom said that she bought fresh bread.)* - Fact.
*   Мама сказала, **щоб** я купив свіжий хліб. *(Mom said to buy fresh bread.)* - Instruction.
*   Мій колега написав, **що** ми маємо важливу зустріч. *(My colleague wrote that we have an important meeting.)* - Fact.
*   Мій колега написав, **щоб** я підготував усі документи. *(My colleague wrote that I should prepare all the documents.)* - Instruction.
*   Лікар сказав, **що** я п'ю мало води. *(The doctor said that I drink little water.)* - Fact.
*   Лікар сказав, **щоб** я пив більше води кожного дня. *(The doctor told me to drink more water every day.)* - Instruction.

Будьте дуже уважні з цими маленькими словами. *(Be very careful with these small words.)* Вони роблять ваше щоденне спілкування правильним і точним. *(They make your daily communication correct and accurate.)*

<!-- INJECT_ACTIVITY: match-up-transform-direct-speech-into-reported-speech-match-the-original-quote-to-its-indirect-version -->


## Мета і повідомлення в житті

> — **Син:** Мама, тато телефонував десять хвилин тому. *(Mom, dad called ten minutes ago.)* Він сказав, щоб ти зателефонувала бабусі. *(He said that you should call grandma.)*
> — **Мама:** Добре, я зателефоную їй трохи пізніше. *(Okay, I will call her a bit later.)* Я хочу зателефонувати, щоб запитати про її здоров'я. *(I want to call to ask about her health.)* Бабуся була в лікарні минулого тижня. *(Grandma was in the hospital last week.)*
> — **Син:** Тато також сказав, що він сьогодні затримається на роботі. *(Dad also said that he will be late at work today.)* У них там важлива зустріч. *(They have an important meeting there.)*
> — **Мама:** Я **зрозуміла** *(understood)*. Я приготую вечерю зараз, щоб він міг поїсти гаряче вдома. *(I will prepare dinner now so that he can eat hot food at home.)*
> — **Син:** А тато ще просив, щоб я прибрав у своїй кімнаті. *(And dad also asked that I clean in my room.)*
> — **Мама:** Тоді йди прибирати, щоб у нас було чисто. *(Then go clean so that it is clean here.)* Бабуся вчора говорила, що хоче приїхати в гості на вихідних. *(Grandma said yesterday that she wants to come visit on the weekend.)*
> — **Син:** Ура! *(Hooray!)* Я швидко приберу всі іграшки, щоб вона дуже зраділа. *(I will quickly clean all the toys so that she is very happy.)*

У реальному житті ми постійно передаємо інформацію. *(In real life, we constantly pass on information.)* Ми пишемо короткі **повідомлення** *(messages)* у месенджерах або просто залишаємо записки на холодильнику. *(We write short messages in messengers or simply leave notes on the fridge.)* У таких текстах дуже часто використовуються слова «що» та «щоб». *(In such texts, the words "that" and "so that" are used very often.)* Коли ви залишаєте записку, ви можете написати факт або пряму інструкцію. *(When you leave a note, you can write a fact or a direct instruction.)* Наприклад, ви можете написати сусіду: «Зателефонуй мамі, вона сказала, що чекає дзвінка». *("Call mom, she said that she is waiting for a call.")* Тут ми бачимо факт через **непряму мову** *(indirect speech)*. Або ви можете залишити таку записку: «Купи молоко, щоб ми могли випити кави вранці». *("Buy milk so that we could drink coffee in the morning.")* Це вже чітка **мета** *(purpose)* нашої дії. *(This is already a clear purpose of our action.)* Також ми часто пишемо про плани: «Він написав, що прийде пізніше після роботи». *("He wrote that he will come later after work.")* Такі прості речення роблять наше щоденне спілкування ефективним і зрозумілим. *(Such simple sentences make our daily communication effective and understandable.)* Звертайте увагу на ці важливі слова, коли читаєте українські тексти. *(Pay attention to these important words when you read Ukrainian texts.)*

Ці конструкції — це ідеальні фрази для початку розмови. *(These constructions are ideal phrases to start a conversation.)* Коли ми хочемо обговорити новини з друзями, ми часто використовуємо стандартні формули. *(When we want to discuss news with friends, we often use standard formulas.)* Наприклад, ви можете почати діалог так: «Мені сказали, що завтра буде сильний дощ». *("I was told that there will be heavy rain tomorrow.")* Це дуже природний спосіб поділитися інформацією, яку ви отримали від когось іншого. *(This is a very natural way to share information that you received from someone else.)* Інша дуже популярна фраза: «Я чув, що в центрі відкрився новий ресторан». *("I heard that a new restaurant opened in the center.")* Жінки зазвичай кажуть: «Я чула, що...». *("I heard that...")* Це чудова базова фраза, щоб почати обговорювати цікаві події навколо вас. *(This is a wonderful basic phrase to start discussing interesting events around you.)* А якщо ви хочете передати прохання, ви скажете: «Вони попросили, щоб ми прийшли трохи раніше». *("They asked that we come a bit earlier.")* Використовуйте ці готові фрази з дієсловами мовлення: **сказати** *(to say)*, **відповісти** *(to answer)*, **пояснити** *(to explain)*, **запитати** *(to ask)*, та **додати** *(to add)*. Вони допоможуть вам звучати впевнено як справжній носій мови. *(They will help you sound confidently like a true native speaker.)*

Тепер ви знаєте три головні слова для поєднання ваших думок. *(Now you know three main words for combining your thoughts.)* Давайте подивимося на них ще раз, щоб ви ніколи їх не плутали. *(Let's look at them once more so that you never confuse them.)*

First, we use «що» strictly for facts and objective statements. It directly answers the question "What did they say?". Наприклад: «Я знаю, що він сьогодні працює в офісі». *(For example: "I know that he is working in the office today.")* 

Second, we use «щоб» to express a specific purpose, wishes, or direct commands. It answers the question "What for?" or "To do what?". Наприклад: «Я працюю, щоб мати гроші на подорожі». *(For example: "I work to have money for travels.")* Або коли це різні люди: «Він хоче, щоб я працював швидше». *(Or when these are different people: "He wants me to work faster.")*

Third, we use «тому що» or «бо» to explain the cause or reason of an action. It answers the simple question "Why?". Наприклад: «Я працюю, тому що мені потрібні гроші». *(For example: "I work because I need money.")* 

Notice the crucial logical difference: «тому що» always looks back at the reason, while «щоб» always looks forward to the future goal. Якщо ви розумієте цю різницю, ви можете вільно будувати дуже гарні українські речення. *(If you understand this difference, you can freely build very beautiful Ukrainian sentences.)*

<!-- INJECT_ACTIVITY: unjumble-purpose-clauses -->


## Підсумок

Давайте згадаємо головні правила цього модуля. *(Let's recall the main rules of this module.)*

Використовуйте **щоб** *(in order to)* плюс інфінітив, якщо суб'єкт один: «Я йду, щоб купити хліб». *(Use "щоб" plus infinitive if the subject is the same: "I am going to buy bread.")*

Використовуйте **щоб** плюс минулий час, якщо суб'єкти різні: «Я хочу, щоб ти купив хліб». *(Use "щоб" plus past tense if the subjects are different: "I want you to buy bread.")*

**Непряма мова** *(indirect speech)* зі словом **що** *(that)* передає факти: «Він сказав, що прийде». *(Indirect speech with "що" conveys facts: "He said that he will come.")*

Непряма мова зі словом **щоб** передає **прохання** *(request)*: «Він сказав, щоб я прийшов». *(Indirect speech with "щоб" conveys a request: "He said that I should come.")*

Питання в непрямій мові використовують слово **чи** *(if/whether)*: «Він запитав, чи я буду там». *(Questions in indirect speech use "чи": "He asked if I will be there.")*

Ці правила роблять ваші українські речення дуже природними. *(These rules make your Ukrainian sentences very natural.)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: purpose-clauses
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

**Level: A2 (Module 48/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: grammar-verbs-present [§4.2.4.1]
**Дієвідмінювання в теперішньому часі** (Present tense conjugation)
- **fill-in** — Відмінюй дієслово: Вставити правильну форму дієслова за особою та числом / Fill in correct verb conjugation for given person/number
  - Instruction: *Вставте правильну форму дієслова*
- **group-sort** — І чи ІІ дієвідміна?: Розподілити дієслова за типом дієвідміни / Sort verbs by conjugation class (I vs II)
- **match-up** — Особа → форма: Зіставити особові займенники з формами дієслова / Match personal pronouns to verb conjugation forms
  - Instruction: *З'єднайте*
- **error-correction** — Виправ дієслово: Знайти неправильно відмінене дієслово та виправити / Find incorrectly conjugated verb and fix it
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує відмінювання. Англійські дієслова не змінюються за особами

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

### Pattern: general-vocabulary [§3 (Thematic catalogue)]
**Тематична лексика** (Thematic vocabulary)
- **match-up** — Слово → переклад: Зіставити українські слова з англійськими перекладами / Match Ukrainian words to English translations
- **fill-in** — Вставте слово: Вставити пропущене слово за контекстом / Fill in the missing word from context
- **anagram** — Склади слово: Переставити літери, щоб утворити правильне слово / Rearrange letters to form the target word
- **odd-one-out** — Четверте зайве: Обрати слово, що не належить до семантичної групи / Pick the word that doesn't belong to the semantic group
- **translate** — Оберіть переклад: Обрати правильний переклад із варіантів / Choose correct translation from options


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

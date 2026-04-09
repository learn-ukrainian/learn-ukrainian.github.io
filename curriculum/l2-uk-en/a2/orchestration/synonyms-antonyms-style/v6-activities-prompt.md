<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/synonyms-antonyms-style.yaml` file for module **58: Слова мають друзів** (a2).

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

- `<!-- INJECT_ACTIVITY: match-up-match-synonyms-e-g-and-antonyms-e-g-in-pairs -->`
- `<!-- INJECT_ACTIVITY: quiz-identify-the-literary-device-epithet-metaphor-personification-in-short-phrases -->`
- `<!-- INJECT_ACTIVITY: fill-in-form-diminutives-from-base-words-e-g-using-correct-suffixes -->`
- `<!-- INJECT_ACTIVITY: group-sort-sort-examples-into-syntactic-stylistic-categories-ellipsis-vs-repetition -->`

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Match synonyms and antonyms in pairs
  items: 8
  type: match-up
- focus: Identify the literary device (epithet, metaphor, ellipsis, repetition)
  items: 8
  type: quiz
- focus: Form diminutives from base words using correct suffixes
  items: 8
  type: fill-in
- focus: Sort examples into syntactic stylistic categories (еліпсис vs повтор)
  items: 8
  type: group-sort


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- стилістика (stylistics)
- порівняння (comparison, simile)
- відтінок (shade, nuance)
- прислів'я (proverb)
- виразність (expressiveness)
required:
- синонім (synonym)
- антонім (antonym)
- епітет (epithet)
- метафора (metaphor)
- зменшувальний (diminutive)
- суфікс (suffix)
- еліпсис (ellipsis)
- повтор (repetition)
- образний (figurative, expressive)
- ласкавий (tender, affectionate)


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Синоніми та антоніми: збагачуємо мовлення (~550 words total)

> — **Викладач:** Сьогодні ми редагуємо наш текст. *(Today we are editing our text.)* Як зробити його кращим? *(How to make it better?)*
> — **Студентка:** У мене є фраза «великий будинок». *(I have the phrase "big house".)* Це звучить нудно. *(It sounds boring.)*
> — **Викладач:** Правильно. *(Right.)* Яке слово ми можемо використати замість слова «великий»? *(What word can we use instead of the word "big"?)*
> — **Студент:** Можемо сказати «величезний палац». *(We can say "huge palace".)*
> — **Викладач:** Чудово! *(Excellent!)* А як щодо фрази «маленька дівчинка»? *(And what about the phrase "little girl"?)*
> — **Студентка:** Краще звучить «крихітна дівчинка». *(“Tiny girl” sounds better.)*
> — **Викладач:** Так, текст стає цікавішим. *(Yes, the text becomes more interesting.)* А тепер знайдемо протилежні слова. *(And now let's find opposite words.)* Замість «холодний вітер» напишемо «теплий вечір». *(Instead of "cold wind" we will write "warm evening".)*

В українській мові слова мають справжніх друзів. *(In the Ukrainian language, words have real friends.)* Це **синоніми** *(synonyms)* — слова, які мають схоже значення. *(words that have a similar meaning.)* Вони роблять наше мовлення багатим і точним. *(They make our speech rich and precise.)* Наприклад, ми дуже часто використовуємо дієслово «говорити» *(to speak)*. Але ми маємо багато інших цікавих варіантів. *(But we have many other interesting options.)* Якщо ми ділимося важливою інформацією, ми можемо **казати** *(to say)* або **розповідати** *(to tell)*. Якщо ми спілкуємося з нашими друзями неформально, ми можемо просто **балакати** *(to chat)*. Кожне нове слово має свій унікальний відтінок. *(Every new word has its unique shade.)* Синоніми допомагають нам точно передати наші думки та емоції. *(Synonyms help us accurately convey our thoughts and emotions.)* Ми завжди вибираємо слово залежно від конкретної ситуації. *(We always choose a word depending on the specific situation.)*

Дуже часто ми використовуємо базові прикметники. *(Very often we use basic adjectives.)* Наприклад, звичайні слова «гарний» *(nice)* або «хороший» *(good)*. Але українська мова пропонує набагато більше кольорів. *(But the Ukrainian language offers much more colors.)* Коли ми говоримо про зовнішність людини, краще сказати **вродливий** *(handsome/beautiful)*. Коли ми описуємо якийсь предмет або пейзаж, ідеально підходить слово **красивий** *(beautiful)*. А якщо ми маємо приємний досвід або сильну емоцію, ми кажемо **чудовий** *(wonderful)*. Чому це так важливо? *(Why is this so important?)* Бо постійне повторення одного слова — це **тавтологія** *(tautology)*. Тавтологія робить ваш текст бідним і нецікавим. *(Tautology makes your text poor and uninteresting.)* Якщо ви уникаєте повторів, ваша українська мова звучить набагато природніше та професійніше. *(If you avoid repetitions, your Ukrainian language sounds much more natural and professional.)* Коли ви пишете лист або розповідаєте цікаву історію, шукайте нові варіанти. *(When you write a letter or tell an interesting story, look for new options.)* Використовуйте різні синоніми, щоб малювати словами. *(Use different synonyms to paint with words.)* Це показує ваш високий рівень володіння мовою. *(This shows your high level of language proficiency.)*

Слова мають не лише друзів, але й ворогів. *(Words have not only friends, but also enemies.)* Це **антоніми** *(antonyms)* — слова з абсолютно протилежним значенням. *(words with an absolutely opposite meaning.)* Вони створюють дуже сильний контраст у вашому реченні. *(They create a very strong contrast in your sentence.)* Ми постійно використовуємо їх у нашому повсякденному житті. *(We constantly use them in our everyday life.)* Наприклад: «день» *(day)* і «ніч» *(night)*, «гарячий» *(hot)* і «холодний» *(cold)*, «початок» *(beginning)* і «кінець» *(end)*. Антоніми також є дуже важливими для українського фольклору. *(Antonyms are also very important for Ukrainian folklore.)* Вони часто є основою для багатьох українських прислів'їв. *(They are often the foundation for many Ukrainian proverbs.)* Одне популярне українське прислів'я мудро каже: «Не знаючи лиха, не пізнаєш і добра» *(Without knowing trouble, you won't know good either)*. Тут слова «лихо» *(trouble)* і «добро» *(good)* стоять поруч, щоб показати нам важливий життєвий урок. *(Here the words "trouble" and "good" stand next to each other to show us an important life lesson.)* Антоніми роблять наші думки глибокими та виразними. *(Antonyms make our thoughts deep and expressive.)*

<!-- INJECT_ACTIVITY: match-up-match-synonyms-e-g-and-antonyms-e-g-in-pairs -->

Ваше головне завдання — постійно розширювати свій словниковий запас. *(Your main task is to constantly expand your vocabulary.)* Завжди використовуйте **словник синонімів** *(dictionary of synonyms)* під час навчання. *(Always use a dictionary of synonyms during your studies.)* Він швидко допоможе вам знайти ідеальне слово для будь-якого контексту. *(It will quickly help you find the perfect word for any context.)* Ці слова-друзі завжди готові зробити вашу мову яскравішою! *(These word-friends are always ready to make your language brighter!)*


## Епітети та метафори: мова, що малює

Ми бачимо, як слова збагачують текст. *(We see how words enrich a text.)* Кожне слово має **пряме значення** *(literal meaning)*. *(Every word has a literal meaning.)* Наприклад, «золотий годинник» *(gold watch)* означає просто матеріал. *(For example, "gold watch" simply means the material.)* Це звичайний факт. *(This is an ordinary fact.)* Але слова мають також **переносне значення** *(figurative meaning)*. *(But words also have a figurative meaning.)* Ми переносимо ознаку одного предмета на інший. *(We transfer the characteristic of one object to another.)* Наприклад, ми часто кажемо «золота осінь» *(golden autumn)*. *(For example, we often say "golden autumn".)* Листя має жовтий колір, як золото. *(The leaves have a yellow color, like gold.)* Майстер має «золоті руки» *(skilful hands)*. *(A craftsman has "skilful hands".)* Це означає, що він усе робить ідеально. *(This means that he does everything perfectly.)* Переносне значення — це основа української **образності** *(expressiveness)*. *(Figurative meaning is the foundation of Ukrainian expressiveness.)* Воно допомагає нам малювати словами. *(It helps us paint with words.)*

Один із найпопулярніших засобів образності — це **епітет** *(epithet)*. *(One of the most popular devices of expressiveness is the epithet.)* Епітет — це дуже емоційний і яскравий прикметник. *(An epithet is a very emotional and bright adjective.)* Він не просто констатує факт, а малює картину. *(It does not just state a fact, but paints a picture.)* Епітети впливають на наші почуття. *(Epithets affect our feelings.)* Українська література дуже любить цей художній засіб. *(Ukrainian literature loves this artistic device very much.)* Замість звичайного дощу ми можемо побачити «срібний дощ» *(silvery rain)*. *(Instead of ordinary rain, we can see "silvery rain".)* Рідна мова часто називається «калинова мова» *(guelder-rose language)*. *(The native language is often called "guelder-rose language".)* Вона красива, як червона калина. *(It is beautiful like a red guelder-rose.)* Людина, яка щиро любить, має «палке серце» *(passionate heart)*. *(A person who loves sincerely has a "passionate heart".)* Епітети роблять текст живим і кольоровим. *(Epithets make the text alive and colorful.)* Вони часто звертаються до наших емоцій. *(They often appeal to our emotions.)*

Інший важливий стилістичний прийом — це **метафора** *(metaphor)*. *(Another important stylistic device is the metaphor.)* Метафора — це приховане порівняння. *(A metaphor is a hidden comparison.)* Ми порівнюємо дві речі, але не використовуємо слово «як» *(like)*. *(We compare two things, but we do not use the word "like".)* Ми просто називаємо один предмет іменем іншого. *(We simply name one object with the name of another.)* Наприклад, ми кажемо «море квітів» *(a sea of flowers)*. *(For example, we say "a sea of flowers".)* Це означає, що квітів дуже багато. *(This means there are very many flowers.)* Ми можемо мати «крила мрії» *(wings of a dream)* або бачити «зорю надії» *(star of hope)*. *(We can have "wings of a dream" or see a "star of hope".)* Метафори дозволяють нам коротко і влучно передавати складні емоції. *(Metaphors allow us to convey complex emotions briefly and aptly.)* Вони роблять нашу мову глибокою та поетичною. *(They make our language deep and poetic.)*

Особливий тип метафори — це **персоніфікація** *(personification)*. *(A special type of metaphor is personification.)* Вона наділяє неживі предмети людськими рисами. *(It endows inanimate objects with human traits.)* Це характерна ознака української народної творчості. *(This is a characteristic feature of Ukrainian folk creativity.)* В українських піснях природа завжди жива. *(In Ukrainian songs, nature is always alive.)* Вона думає, плаче і радіє разом із людиною. *(It thinks, cries, and rejoices together with a person.)* Навесні ми кажемо, що «сонце сміється» *(the sun laughs)*. *(In spring we say that "the sun laughs".)* Під час бурі ми чуємо, як «вітер співає» *(the wind sings)*. *(During a storm, we hear how "the wind sings".)* А вночі здається, що «ліси дивляться» *(forests watch)* на нас. *(And at night it seems that "forests watch" us.)* Персоніфікація допомагає нам відчути єдність із природою. *(Personification helps us feel unity with nature.)* Вона створює магічну атмосферу в тексті. *(It creates a magical atmosphere in the text.)*

<!-- INJECT_ACTIVITY: quiz-identify-the-literary-device-epithet-metaphor-personification-in-short-phrases -->


## Зменшувальні суфікси: ласкаві слова

Українська мова дуже ніжна та емоційна. *(The Ukrainian language is very tender and emotional.)* Ми часто використовуємо **зменшувально-пестливі суфікси** *(diminutive-affectionate suffixes)*. Вони показують не лише малий розмір предмета. *(They show not only the small size of an object.)* Головна їхня функція — це емоції. *(Their main function is emotions.)* Вони виражають любов, ніжність та близькість. *(They express love, tenderness, and closeness.)* Це не тільки слова для дітей. *(These are not only words for children.)* Дорослі люди постійно використовують їх у розмові. *(Adult people constantly use them in conversation.)* Наприклад, звичайний **кіт** *(cat)* стає милим словом **котик** *(kitty)*. *(For example, an ordinary cat becomes the cute word kitty.)* Слово **бабуся** *(grandmother)* перетворюється на тепле слово **бабусенька** *(dear grandmother)*. *(The word grandmother turns into the warm word dear grandmother.)* Ці суфікси роблять мову теплішою. *(These suffixes make the language warmer.)* Українці дуже люблять **ласкаві слова** *(words of endearment)*. *(Ukrainians love words of endearment very much.)* 

Для слів чоловічого роду ми часто використовуємо суфікси **-ик** та **-ок**. *(For masculine words we often use the suffixes -yk and -ok.)* Суфікс «-ик» зазвичай означає невеликий розмір предмета. *(The suffix "-yk" usually means a small size of an object.)* Великий **стіл** *(table)* стає маленьким словом **столик** *(little table)*. *(A big table becomes the small word little table.)* Звичайний **стілець** *(chair)* перетворюється на **стільчик** *(little chair)*. *(An ordinary chair turns into a little chair.)* Але цей суфікс також додає симпатії. *(But this suffix also adds sympathy.)* Ми кажемо **хлопчик** *(little boy)* замість «хлопець» *(boy)*. *(We say little boy instead of boy.)* Суфікс «-ок» частіше показує любов та родинний зв'язок. *(The suffix "-ok" more often shows love and family connection.)* Наприклад, слово «син» *(son)* стає ніжним словом **синок** *(dear son)*. *(For example, the word son becomes the tender word dear son.)* А суворе слово **батько** *(father)* може стати дуже теплим словом **батечко** *(dear father)*. *(And the strict word father can become the very warm word dear father.)* 

Для слів жіночого та середнього роду є свої красиві суфікси. *(For feminine and neuter words there are their own beautiful suffixes.)* Це суфікси **-ечк-**, **-очк-** та **-еньк-**. *(These are the suffixes -echk-, -ochk-, and -enk-.)* Наприклад, слово **квітка** *(flower)* перетворюється на миле слово **квіточка** *(little flower)*. *(For example, the word flower turns into the cute word little flower.)* Яскрава **зірка** *(star)* на небі стає словом **зірочка** *(little star)*. *(A bright star in the sky becomes the word little star.)* А слово **річка** *(river)* може стати ніжною формою **річечка** *(little river)*. *(And the word river can become the tender form little river.)* Ми також часто використовуємо суфікс «-еньк-» для прикметників. *(We also often use the suffix "-enk-" for adjectives.)* Це допомагає пом'якшити опис. *(This helps soften the description.)* Замість слова **малий** *(small)* ми говоримо **маленький** *(very small/cute)*. *(Instead of the word small we say very small/cute.)* А замість слова **гарний** *(pretty)* ми кажемо **гарненький** *(very pretty/cute)*. *(And instead of the word pretty we say very pretty/cute.)* Навіть **ніч** *(night)* може стати словом **ніченька** *(dear night)*. *(Even night can become the word dear night.)* Вони несуть багато позитивної енергії. *(They carry a lot of positive energy.)* 

В Україні ми дуже часто змінюємо імена людей. *(In Ukraine we very often change people's names.)* Зменшувальні форми імен показують нашу любов. *(Diminutive forms of names show our love.)* Наприклад, ім'я **Оксана** стає ласкавим іменем **Оксаночка**. *(For example, the name Oksana becomes the affectionate name Oksanochka.)* Ім'я **Іван** перетворюється на тепле ім'я **Іванко**. *(The name Ivan turns into the warm name Ivanko.)* А **Марія** часто стає формою **Марійка**. *(And Mariia often becomes the form Mariyka.)* Цікаво, що іноді ці суфікси повністю змінюють значення слова. *(Interestingly, sometimes these suffixes completely change the meaning of the word.)* Наприклад, слово **рука** *(arm/hand)* — це частина тіла. *(For example, the word arm/hand is a body part.)* Але форма **ручка** *(pen/handle)* може означати предмет, яким ми пишемо. *(But the form pen/handle can mean the object we write with.)* Слово **голова** *(head)* — це частина тіла людини. *(The word head is a body part of a person.)* А слово **головка** *(garlic head)* часто означає частину рослини. *(And the word garlic head often means a part of a plant.)* Контекст завжди дуже важливий. *(Context is always very important.)* 

<!-- INJECT_ACTIVITY: fill-in-form-diminutives-from-base-words-e-g-using-correct-suffixes -->


## Синтаксична стилістика: еліпсис і повтор

Іноді слова у реченні можуть зникати. *(Sometimes words in a sentence can disappear.)* Цей стилістичний прийом називається **еліпсис** *(ellipsis)*. *(This stylistic device is called ellipsis.)* Еліпсис — це пропуск слова, яке легко зрозуміти. *(Ellipsis is the omission of a word that is easy to understand.)* Українська мова часто пропускає дієслово «бути». *(The Ukrainian language often omits the verb "to be".)* Але в розмові ми пропускаємо й інші дієслова. *(But in conversation we omit other verbs too.)* Це робить мовлення дуже динамічним. *(This makes speech very dynamic.)* Наприклад, ви вибираєте напої в кафе. *(For example, you are choosing drinks in a cafe.)* Ви можете сказати довго: «Я буду пити каву, а ти?». *(You can say it long: "I will drink coffee, and you?".)* Але українці скажуть коротко: «**Я — каву, а ти?**» *(I [will have] coffee, and you?)*. *(But Ukrainians will say it shortly: "I [will have] coffee, and you?".)* Дієслово тут не потрібне. *(The verb is not needed here.)* Або ваш колега пішов з роботи. *(Or your colleague left work.)* Хтось запитує: «Де зараз Іван?». *(Someone asks: "Where is Ivan now?".)* Ви відповідаєте: «**Він — додому**» *(He [went] home)*. *(You answer: "He [went] home".)* Еліпсис створює відчуття швидкості та фокусує увагу. *(Ellipsis creates a sense of speed and focuses attention.)*

Еліпсис також дуже популярний у відомих гаслах. *(Ellipsis is also very popular in famous slogans.)* Коли ми прибираємо дієслово, фраза стає енергійною. *(When we remove the verb, the phrase becomes energetic.)* Подивіться на гасло: «**Усе найкраще — дітям!**» *(All the best [belongs] to children!)*. *(Look at the slogan: "All the best [belongs] to children!".)* Тут немає дієслова «належить» або «дається». *(There is no verb "belongs" or "is given" here.)* У письмовому тексті на місці пропущеного слова ми ставимо **тире** *(dash)*. *(In a written text, in the place of the omitted word we put a dash.)* Тире показує нам, де стояло дієслово. *(The dash shows us where the verb stood.)* Ще один приклад: «**Кожному — своє**» *(To each [his] own)*. *(Another example: "To each [his] own".)* Еліпсис робить такі фрази легкими для запам'ятовування. *(Ellipsis makes such phrases easy to remember.)*

В українській мові є ще один важливий прийом. *(In the Ukrainian language there is another important device.)* Це **повтор** *(repetition)*. *(This is repetition.)* Іноді ми навмисне повторюємо одне слово. *(Sometimes we intentionally repeat one word.)* Це свідомий вибір, щоб показати інтенсивність дії. *(This is a conscious choice to show the intensity of an action.)* Наприклад, ви довго шукали рішення. *(For example, you looked for a solution for a long time.)* Ви кажете: «Ми **думали-думали**, і знайшли» *(We thought and thought, and found it)*. *(You say: "We thought and thought, and found it".)* Повтор показує, що процес був довгим. *(Repetition shows that the process was long.)* Якщо місце знаходиться неблизько, ми кажемо: «Вони живуть **далеко-далеко**» *(They live very far away)*. *(If a place is located not close, we say: "They live very far away".)* А якщо люди йшли багато годин, вони **ходили-ходили** *(walked and walked)*. *(And if people walked for many hours, they walked and walked.)*

Повтор часто зустрічається в українському фольклорі. *(Repetition is often found in Ukrainian folklore.)* Він створює особливий ритм мовлення. *(It creates a special rhythm of speech.)* Відоме прислів'я каже: «Тихше їдеш — далі будеш» *(The quieter you go, the further you will be)*. *(A famous proverb says: "The quieter you go, the further you will be".)* Українці також люблять парні вирази. *(Ukrainians also love paired expressions.)* Наприклад, традиційний вираз **хліб-сіль** *(bread and salt)*. *(For example, the traditional expression bread and salt.)* Він означає гостинність і дружбу. *(It means hospitality and friendship.)* У народних казках герой довго подорожує. *(In folk tales the hero travels for a long time.)* Ми читаємо: «Ішов, ішов та й прийшов» *(He walked, walked, and finally arrived)*. *(We read: "He walked, walked, and finally arrived".)* Цей повтор підкреслює успішне завершення його великої подорожі. *(This repetition emphasizes the successful completion of his great journey.)* Такі фрази передають народну мудрість. *(Such phrases pass on folk wisdom.)*

Усі ці стилістичні інструменти роблять нашу мову багатою. *(All these stylistic tools make our language rich.)* Синоніми, зменшувальні суфікси, еліпсис і повтор — це друзі слів. *(Synonyms, diminutive suffixes, ellipsis, and repetition are friends of words.)* Використовуйте їх, і ваша українська буде красивою! *(Use them, and your Ukrainian will be beautiful!)*

<!-- INJECT_ACTIVITY: group-sort-sort-examples-into-syntactic-stylistic-categories-ellipsis-vs-repetition -->


## Підсумок

Сьогодні ми вивчили, як зробити мову багатою. *(Today we learned how to make our language rich.)* Слова мають друзів та ворогів. *(Words have friends and enemies.)* Синоніми допомагають уникати нудьги. *(Synonyms help avoid boredom.)* Антоніми створюють драму та контраст. *(Antonyms create drama and contrast.)* Зменшувальні суфікси додають серця у розмову. *(Diminutive suffixes add heart to a conversation.)* А такі прийоми, як еліпсис, роблять мову живою. *(And devices, like ellipsis, make the language alive.)*

Тепер час перевірити себе. *(Now it is time to check yourself.)* Дайте відповідь на ці запитання: *(Answer these questions:)*

1. Яка різниця між синонімами «говорити» та «балакати»? *(What is the difference between the synonyms "to speak" and "to chat"?)*
2. Чому ми кажемо «золоті руки», а не просто «вмілі руки»? *(Why do we say "golden hands", and not just "skillful hands"?)*
3. Який суфікс ви використаєте для слова «кіт», щоб він став ласкавим? *(What suffix will you use for the word "cat" to make it affectionate?)*
4. Що означає речення «Я — в парк»? *(What does the sentence "I am [going] to the park" mean?)*

Якщо ви знаєте відповіді, ви готові йти далі! *(If you know the answers, you are ready to go further!)* Використовуйте ці нові інструменти щодня. *(Use these new tools every day.)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: synonyms-antonyms-style
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

**Level: A2 (Module 58/60) — ELEMENTARY**

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

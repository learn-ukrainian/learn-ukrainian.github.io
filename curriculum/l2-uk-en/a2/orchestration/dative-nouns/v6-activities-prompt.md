<!-- version: 1.1.0 | updated: 2026-03-31 -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/dative-nouns.yaml` file for module **18: Студентові, сестрі, дитині** (a2).

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

(No injection markers found in prose. All activities will go to workbook.)

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

- focus: Put the noun in brackets into the dative case (e.g., подарувати [брат] →
    братові)
  items: 8
  type: fill-in
- focus: Sort dative nouns by gender (masculine -ові/-у, feminine -і, neuter -у/-ю)
  items: 8
  type: group-sort
- focus: Choose the correct dative ending for nouns with consonant alternation (подруга→подрузі
    vs. *подругі)
  items: 8
  type: quiz
- focus: Match verb + dative noun phrases to their English meanings
  items: 8
  type: match-up
- focus: Reorder words to form correct dative constructions with indirect objects
    (e.g., подарувати братові книгу)
  items: 6
  type: unjumble


You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

recommended:
- відміна (declension)
- чергування (alternation (grammar))
- одержувач (recipient)
- немовля (baby, infant)
required:
- студентові (to the student (dat.))
- сестрі (to the sister (dat.))
- другові (to the friend (dat.))
- подарувати (to give as a gift)
- показати (to show)
- написати (to write)
- розповісти (to tell, to narrate)
- пояснити (to explain)
- відповісти (to answer, to reply)
- закінчення (ending (grammar))


**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

---

## Module Content (the prose the learner reads before exercises)

<module_content>
## Давальний відмінок іменників чоловічого роду (Dative of Masculine Nouns)

The Dative case in Ukrainian is primarily the case of the recipient. It answers the questions **Кому?** *(To whom?)* and **Чому?** *(To what?)*. We use the Dative case when an action is directed toward a person or an object. This is often triggered by verbs of giving, communicating, or assisting, such as **дати** *(to give)*, **написати** *(to write)*, and **допомагати** *(to help)*. When you give a gift, write a letter, or help someone, that person is the recipient and must be in the Dative case. For example, the phrase «допомагати **студентові**» *(to help the student)* clearly shows the action directed at the student.

«Читаємо українською»:
Я хочу дати цей зошит **студентові**. *(I want to give this notebook to the student.)*
Марія завжди допомагає своєму **братові**. *(Mariia always helps her brother.)*
Кому ти хочеш написати повідомлення? *(To whom do you want to write a message?)*
Ми часто допомагаємо **дідусеві** в саду. *(We often help grandpa in the garden.)*

Most masculine nouns in Ukrainian belong to the second declension. For hard stems — nouns ending in a hard consonant — there are two parallel Dative endings: **-ові** and **-у**. These endings are completely interchangeable. You can choose either one, and both are grammatically perfect. However, in modern Ukrainian, the ending **-ові** is highly preferred for people, animals, and other living beings. It sounds distinctly Ukrainian and clearly marks the Dative case, preventing confusion with the Genitive case. The ending **-у** is shorter and is also very common in everyday speech.

«Читаємо українською»:
Я маю віддати книгу **братові**. *(I have to give the book back to the brother.)*
Я маю віддати книгу **брату**. *(I have to give the book back to the brother.)*
Олена купила подарунок **директорові**. *(Olena bought a gift for the director.)*
Олена купила подарунок **директору**. *(Olena bought a gift for the director.)*
Сьогодні я телефоную своєму **другові**. *(Today I am calling my friend.)*
Сьогодні я телефоную своєму **другу**. *(Today I am calling my friend.)*

If a masculine noun ends in a soft consonant (like **вчитель** — *teacher*) or a sibilant sound (like **товариш** — *comrade/friend*), the primary ending shifts from **-ові** to **-еві**. This happens because Ukrainian phonetics naturally soften the vowel after these specific consonants. Just like with hard stems, there is a shorter parallel ending. For soft and sibilant stems, the alternative ending is **-ю**. Both options are correct, but **-еві** is strongly encouraged for people to maintain the melodic rhythm and clear structure of the language.

«Читаємо українською»:
Студент поставив запитання **вчителеві**. *(The student asked the teacher a question.)*
Студент поставив запитання **вчителю**. *(The student asked the teacher a question.)*
Максим розповів цю історію **товаришеві**. *(Maksym told this story to the friend.)*
Максим розповів цю історію **товаришу**. *(Maksym told this story to the friend.)*
Дівчина усміхнулася молодому **лікареві**. *(The girl smiled at the young doctor.)*
Дівчина усміхнулася молодому **лікарю**. *(The girl smiled at the young doctor.)*

> — **Анна:** Ти вже написав **вчителеві**? *(Have you already written to the teacher?)*
> — **Марк:** Так, я відправив лист **вчителю** вранці. *(Yes, I sent the letter to the teacher in the morning.)*
> — **Анна:** А що ти подаруєш **товаришеві**? *(And what will you gift to the friend?)*
> — **Марк:** Я купив **товаришу** нову книгу. *(I bought a new book for the friend.)*

For masculine nouns that end in the vowel **-й** (which is considered a soft stem), the ending transforms into **-єві**. This preserves the "yotated" «й» sound when adding the ending. Common examples include words like **герой** *(hero)*, **водій** *(driver)*, and names like **Сергій** or **Андрій**. The short alternative for these nouns is also **-ю**. When speaking, **-єві** sounds very elegant and is widely used in both formal and everyday contexts to emphasize respect.

«Читаємо українською»:
Місто поставило пам'ятник **героєві**. *(The city put up a monument to the hero.)*
Місто поставило пам'ятник **герою**. *(The city put up a monument to the hero.)*
Ми заплатили гроші **водієві** автобуса. *(We paid money to the bus driver.)*
Ми заплатили гроші **водію** автобуса. *(We paid money to the bus driver.)*
Марія хоче зробити сюрприз **Андрієві**. *(Mariia wants to make a surprise for Andrii.)*
Марія хоче зробити сюрприз **Андрію**. *(Mariia wants to make a surprise for Andrii.)*

Because masculine nouns have two valid Dative endings, you might wonder how to choose between them. Ukrainian grammarians emphasize a "Style Rule" to avoid monotony. When two masculine Dative nouns appear next to each other — usually a title or profession followed by a first name — you should alternate the endings. The standard practice is to give the title the longer ending (**-ові**, **-еві**, **-єві**) and the name the shorter ending (**-у**, **-ю**). This creates a beautiful, rhythmic flow and prevents repetitive sounds.

«Читаємо українською»:
Треба подякувати **сусідові Данилу**. *(We need to thank neighbor Danylo.)*
Я віддав документи **директорові Івану**. *(I gave the documents to director Ivan.)*
Ми довіряємо **лікареві Олександру**. *(We trust doctor Oleksandr.)*
Лист адресований **панові Петру**. *(The letter is addressed to Mr. Petro.)*
Вони допомагають **братові Михайлу**. *(They are helping brother Mykhailo.)*

> — **Катерина:** Кому ти передав ключі? *(To whom did you pass the keys?)*
> — **Віктор:** Я дав їх **охоронцеві Богдану**. *(I gave them to security guard Bohdan.)*
> — **Катерина:** А хто телефонував **директорові Івану**? *(And who called director Ivan?)*
> — **Віктор:** Це був його секретар. *(It was his secretary.)*

Finally, there is a specific group of masculine nouns that end in **-о** in the nominative case. This includes family terms and names like **тато** *(dad)*, **батько** *(father)*, **дядько** *(uncle)*, and **Дмитро**. Although they have a different ending in their dictionary form compared to standard masculine nouns, they follow the exact same declension pattern in the Dative case. They take the standard hard stem endings **-ові** or **-у**.

«Читаємо українською»:
Я хочу зателефонувати **татові**. *(I want to call dad.)*
Я хочу зателефонувати **тату**. *(I want to call dad.)*
Діти приготували сніданок **батькові**. *(The children prepared breakfast for father.)*
Діти приготували сніданок **батьку**. *(The children prepared breakfast for father.)*
Ми купили подарунок **дядькові**. *(We bought a gift for uncle.)*
Ми купили подарунок **дядьку**. *(We bought a gift for uncle.)*
Олена написала повідомлення **Дмитрові**. *(Olena wrote a message to Dmytro.)*
Олена написала повідомлення **Дмитру**. *(Olena wrote a message to Dmytro.)*

<!-- INJECT_ACTIVITY: fill-in, Put the masculine noun in brackets into the dative case (e.g., написати [брат] → братові) -->
<!-- INJECT_ACTIVITY: group-sort, Sort dative nouns by gender (masculine -ові/-у vs. others introduced later) -->


## Давальний відмінок іменників жіночого роду (Dative of Feminine Nouns)

I declension feminine nouns (those ending in **-а** or **-я** in the dictionary form) are straightforward in the Dative case. Most of these nouns take the ending **-і**, replacing the final vowel. This applies to both hard stems (like **мама** *(mom)*) and soft stems (like **земля** *(earth)*). If the noun ends in a vowel followed by **-я** (like **-ія** in **Марія**), the ending becomes **-ї**. Unlike masculine nouns, feminine nouns have a single predictable ending for each type.

«Читаємо українською»:
Я купив подарунок **мамі**. *(I bought a gift for mom.)*
Він допомагає своїй старшій **сестрі**. *(He is helping his older sister.)*
Вони віддали документи **Марії**. *(They gave the documents to Mariia.)*
Діти подарували квіти **вчительці**. *(The children gifted flowers to the teacher.)*

There is one crucial rule when forming the Dative case for some feminine nouns: consonant alternation (чергування). When the stem of a noun ends in a velar consonant — **-г**, **-к**, or **-х** — this consonant changes before the **-і** ending. This historical shift makes pronunciation smoother. Specifically, **-г** changes to **-з**, **-к** changes to **-ц**, and **-х** changes to **-с**. Therefore, **книга** *(book)* becomes **книзі**, **подруга** *(female friend)* becomes **подрузі**, and **муха** *(fly)* becomes **мусі**.

«Читаємо українською»:
Ми подарували нову сукню **подрузі**. *(We gifted a new dress to a female friend.)*
Хлопець написав повідомлення **доньці**. *(The boy wrote a message to the daughter.)*
Турист подякував **Ользі** за допомогу. *(The tourist thanked Olha for the help.)*
Кіт не дає спокою **мусі**. *(The cat gives no peace to the fly.)*

> — **Анна:** Ти вже телефонував **подрузі**? *(Have you already called the friend?)*
> — **Марко:** Ще ні, я напишу **Ользі** ввечері. *(Not yet, I will write to Olha in the evening.)*
> — **Анна:** А що ти подарував **доньці** на свято? *(And what did you gift to the daughter for the holiday?)*
> — **Марко:** Я купив іграшку для неї, а квіти — **дружині**. *(I bought a toy for her, and flowers for the wife.)*

Feminine nouns of the III declension (those ending in a consonant or a soft sign) also take the **-і** ending in the Dative case. Words like **ніч** *(night)* become **ночі**, **любов** *(love)* becomes **любові**, and **радість** *(joy)* becomes **радості**. A special note should be made for the word **мати** *(mother)*: its stem changes in all indirect cases, so in the Dative it becomes **матері**.

«Читаємо українською»:
Ми радіємо кожній новій **речі**. *(We rejoice at every new thing.)*
Вона завжди допомагає своїй **матері**. *(She always helps her mother.)*
Юнак присвятив вірш **любові**. *(The young man dedicated a poem to love.)*
Немає меж моїй **радості**. *(There are no limits to my joy.)*

The Dative case indicates the indirect object — the person or thing to whom or for whom an action is performed. This pattern involves verbs of giving, communicating, or showing. The structure is: Subject + Verb + Dative (recipient) + Accusative (thing). With verbs like **подарувати** *(to give as a gift)*, **показати** *(to show)*, **розповісти** *(to tell)*, and **написати** *(to write)*, the recipient is always in the Dative case.

«Читаємо українською»:
Я дарую квіти коханій **дівчині**. *(I am giving flowers to the beloved girl.)*
Він розповідає історію **подрузі**. *(He is telling a story to the friend.)*
Ми пишемо довгого листа **сестрі**. *(We are writing a long letter to the sister.)*
Вчитель пояснив нову тему **студентці**. *(The teacher explained the new topic to the student.)*

<!-- INJECT_ACTIVITY: quiz, Choose the correct dative ending for nouns with consonant alternation (e.g., подруга → подрузі vs. подругі) -->


## Давальний відмінок іменників середнього роду (Dative of Neuter Nouns)

Neuter nouns of the II declension share their Dative endings with masculine nouns, taking either **-у** or **-ю**. Unlike masculine nouns, they never take the **-ові** or **-еві** endings. Hard stems take **-у**: **місто** *(city)* becomes **місту**, and **село** *(village)* becomes **селу**. Soft stems take **-ю**: **море** *(sea)* becomes **морю**, **серце** *(heart)* becomes **серцю**, and **знання** *(knowledge)* becomes **знанню**. 

«Читаємо українською»:
Ми даємо нову назву цьому **місту**. *(We are giving a new name to this city.)*
Мир потрібен кожному **селу** і **місту**. *(Peace is needed for every village and city.)*
Моряки радіють теплому і спокійному **морю**. *(The sailors rejoice at the warm and calm sea.)*
Хлопець завжди вірить своєму **серцю**. *(The boy always believes his heart.)*
Студенти приділяють багато часу **знанню**. *(Students dedicate a lot of time to knowledge.)*

> — **Іван:** Ти вже дав нову назву **селу**? *(Have you already given a new name to the village?)*
> — **Петро:** Ще ні. А ти дав назву **місту**? *(Not yet. And did you give a name to the city?)*
> — **Іван:** Так, я також додав великий порт. *(Yes, I also added a large port.)*
> — **Петро:** Це добре, люди завжди радіють **морю**. *(That is good, people always rejoice at the sea.)*

The IV declension contains a unique group of neuter nouns that denote young animals or infants. These words end in **-я** or **-а** and have special suffixes (**-ат-** or **-ят-**) in most cases. In the Dative case, they take the ending **-аті** or **-яті**. For example, **немовля** *(infant)* becomes **немовляті**, **курча** *(chick)* becomes **курчаті**, **хлоп'я** *(little boy)* becomes **хлоп'яті**, and **теля** *(calf)* becomes **теляті**.

«Читаємо українською»:
Мати дає тепле молоко **немовляті**. *(The mother gives warm milk to the infant.)*
Дівчинка кидає зерно малому **курчаті**. *(The girl throws grain to the small chick.)*
Дідусь читає казку **хлоп'яті**. *(The grandfather reads a fairy tale to the little boy.)*
Фермер приніс свіжу воду **теляті**. *(The farmer brought fresh water to the calf.)*
Вона купила нову іграшку малому **хлоп'яті**. *(She bought a new toy for the little boy.)*

> — **Оксана:** Що ти даєш **немовляті**? *(What are you giving to the infant?)*
> — **Марко:** Я даю йому тепле молоко. *(I am giving him warm milk.)*
> — **Оксана:** А хто дав їжу **курчаті**? *(And who gave food to the chick?)*
> — **Марко:** Бабуся вже дала зерно всім птахам. *(Grandma already gave grain to all the birds.)*

Neuter Dative nouns frequently follow verbs expressing an emotional reaction or a directed action, such as **радіти** *(to rejoice)*, **співчувати** *(to sympathize)*, or **дати** *(to give)*. You can rejoice at the sun (**радіти сонцю**), give a name to a city (**дати назву місту**), or sympathize with grief (**співчувати горю**). The recipient or the object of the emotion takes the Dative case.

«Читаємо українською»:
Діти завжди радіють яскравому **сонцю**. *(Children always rejoice at the bright sun.)*
Вони вирішили дати нову назву своєму **місту**. *(They decided to give a new name to their city.)*
Ми щиро співчуваємо вашому **горю**. *(We sincerely sympathize with your grief.)*
Люди радіють весняному **теплу**. *(People rejoice at the spring warmth.)*
Ми завжди радіємо новому **знайомству**. *(We always rejoice at a new acquaintance.)*

> — **Тарас:** Чому ти так радієш **сонцю**? *(Why do you rejoice at the sun so much?)*
> — **Олена:** Бо я дуже люблю весну! *(Because I love spring very much!)*
> — **Тарас:** А я радію нашому **знайомству**. *(And I rejoice at our acquaintance.)*
> — **Олена:** Я теж! *(Me too!)*

<!-- INJECT_ACTIVITY: match-up, Match verb + dative noun phrases (mixed genders) to their English meanings, 8 items -->


## Давальний відмінок у реченні (Dative Nouns in Sentences)

The most common use of the Dative case is to indicate the indirect object of a sentence. This is the person, animal, or entity that receives something, benefits from an action, or is the target of a communication. The standard sentence pattern is Subject + Verb + Dative (Recipient) + Accusative (Direct Object). While Ukrainian word order is very flexible and you can move words for emphasis, the recipient usually comes right after the verb in a neutral sentence. When analyzing a sentence, always ask «Кому?» *(To whom?)* to find the Dative noun.

«Читаємо українською»:
Тетяна вчора подарувала **братові** нову цікаву книгу. *(Tetiana gave a new interesting book to her brother yesterday.)*
Вчитель показав **студентам** велику карту України. *(The teacher showed a large map of Ukraine to the students.)*
Мама щовечора читає **дитині** гарну казку. *(Mom reads a beautiful fairy tale to the child every evening.)*
Дідусь купив своєму **онукові** новий велосипед. *(Grandpa bought a new bicycle for his grandson.)*
Я зараз готую **другові** дуже смачну вечерю. *(I am preparing a very tasty dinner for my friend right now.)*
Батько часто дарує квіти **мамі**. *(Father often gives flowers to mom.)*

> — **Відправник:** Доброго дня. Я хочу відправити ці посилки. *(Good afternoon. I want to send these packages.)*
> — **Працівник пошти:** Доброго дня. Кому перша посилка? *(Good afternoon. To whom is the first package?)*
> — **Відправник:** Це — **студентові** Петренку. *(This is for the student Petrenko.)*
> — **Працівник пошти:** Добре. А ця велика коробка? *(Good. And this big box?)*
> — **Відправник:** Це — моїй **сестрі** Олені. *(This is to my sister Olena.)*
> — **Працівник пошти:** Зрозуміло. І маленький пакунок? *(Understood. And the small parcel?)*
> — **Відправник:** Це — маленькій **дитині**, моїй племінниці. *(This is for a small child, my niece.)*
> — **Працівник пошти:** Чудово, зараз усе оформимо. *(Great, we will process everything now.)*

Many verbs of communication, giving, and transaction naturally trigger the Dative case. In English, you often use the preposition "to" (to give to, to show to, to explain to) to show this relationship. In Ukrainian, this preposition completely disappears, and the direction of the action is built entirely into the Dative case ending. You never use prepositions like «до» or «на» when giving something to someone. Common verbs include: **дати** *(to give)*, **подарувати** *(to give as a gift)*, **показати** *(to show)*, **розповісти** *(to tell)*, **написати** *(to write)*, **пояснити** *(to explain)*, and **відповісти** *(to answer)*. When you see these verbs, expect a Dative noun to follow.

«Читаємо українською»:
Викладач має ще раз пояснити нове правило **студентові**. *(The instructor has to explain the new rule to the student one more time.)*
Учень швидко і правильно відповів **вчителеві**. *(The pupil answered the teacher quickly and correctly.)*
Ти вже написав довгого листа **бабусі**? *(Have you already written a long letter to grandma?)*
Вона дуже хоче розповісти цю цікаву історію **подрузі**. *(She really wants to tell this interesting story to her friend.)*
Місцевий житель показав коротку дорогу **туристу**. *(The local resident showed the short road to the tourist.)*
Директор вранці дав нове завдання **менеджерові**. *(The director gave a new task to the manager in the morning.)*

Because the Genitive and Dative cases can sometimes look similar—especially for feminine nouns where both cases often use the ending **-і**—it is critical to remember their core functions. The Dative case is the "to/for" case, indicating a recipient, a beneficiary, or a direction of action (**дати братові** — *to give to the brother*). The Genitive case is the "from/of/absence" case, indicating possession, origin, or that someone is missing (**немає брата** — *there is no brother*). The Dative case always moves toward the person, while the Genitive case often shows distance, ownership, or absence.

«Читаємо українською»:
Я хочу сьогодні зателефонувати своєму старшому **братові**. *(I want to call my older brother today. — Dative)*
Сьогодні вдома немає мого старшого **брата**. *(There is no older brother of mine at home today. — Genitive)*
Ми активно допомагаємо **сестрі** робити великий ремонт. *(We are actively helping our sister do major renovations. — Dative)*
У моєї молодшої **сестри** є новий гарний автомобіль. *(My younger sister has a new beautiful car. — Genitive)*
Студент поставив складне питання **професорові**. *(The student asked the professor a difficult question. — Dative)*
Це нова цікава книга відомого **професора**. *(This is a new interesting book of the famous professor. — Genitive)*

<!-- INJECT_ACTIVITY: unjumble, Reorder words to form correct dative constructions with indirect objects (e.g., подарувати / братові / книгу / Тетяна), 6 items -->


## Підсумок

The Dative case (**давальний відмінок**) helps you express who is receiving something. Let's review the key endings:

*   **Чоловічий рід** *(Masculine)*: Nouns take **-ові**/**-еві**/**-єві** or **-у**/**-ю**. Endings like **-ові** are best for people (**студентові**, **братові**). When listing multiple names or titles together, alternate the endings: **панові Івану**.
*   **Жіночий рід** *(Feminine)*: Nouns take **-і** or **-ї** (**сестрі**, **Марії**). Always watch out for the consonant alternations **к→ц**, **г→з**, **х→с** before the ending **-і** (**подруга** → **подрузі**).
*   **Середній рід** *(Neuter)*: Nouns take **-у** or **-ю** (**місту**, **морю**). Words for babies and young animals take **-аті** or **-яті** (**дитя** → **дитяті**).

«Читаємо українською»:
Я хочу подякувати лікарю і медсестрі. *(I want to thank the doctor and the nurse.)*
Він розповів цікаву історію своєму другові. *(He told an interesting story to his friend.)*
Ми купили гарний подарунок маленькій дитині. *(We bought a nice gift for the small child.)*

**Перевірте себе** *(Self-check)*:
1. Яке закінчення ми оберемо для слова «вчитель» у давальному відмінку? *(Вчителеві / вчителю)*
2. Як зміниться слово «подруга», якщо ми хочемо їй щось подарувати? *(Подрузі)*
3. Коли краще вживати закінчення **-у**, а коли **-ові** для чоловічих імен? *(Чергування при переліку: панові Івану)*

</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: dative-nouns
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

### Seminar types (use for HIST, BIO, LIT, ISTORIO, OES, RUTH, FOLK):

**Core seminar types (use for ALL seminar tracks):**
- **critical-analysis**: Analyze a claim, argument, or source. Required: id, prompt. Optional: target_text, questions[], model_answers[], evaluation_criteria[]
- **essay-response**: Extended written response. Required: id, prompt. Optional: min_words (MUST be >= 50), model_answer, evaluation_criteria[], rubric[{criteria, description}]
- **reading**: Passage with comprehension questions. Required: id, passage, questions[]. Optional: source
- **source-evaluation**: Evaluate a primary/secondary source. Required: id, source_text, criteria[], guiding_questions[]. Optional: source_metadata, model_evaluation
- **comparative-study**: Compare 2+ items/perspectives. Required: id, items_to_compare[], criteria[], prompt. Optional: model_answer
- **authorial-intent**: Analyze author's purpose/perspective. Required: id, excerpt, questions[]. Optional: model_answer
- **debate**: Structured debate exercise. Required: id, debate_question, positions[{label, arguments[]}]. Optional: analysis_tasks[]

**Linguistics types (OES, RUTH, and linguistic analysis in any track):**
- **etymology-trace**: Trace word evolution across periods. Required: id, instruction, stages[{period, form}]
- **translation-critique**: Evaluate translations. Required: id, original, translations[{text}]. Optional: focus_points[]
- **transcription**: Transcribe historical text. Required: id, original, answer. Optional: hints[]
- **paleography-analysis**: Analyze historical script. Required: id, instruction, image_url, hotspots[{x, y, label}]
- **dialect-comparison**: Compare dialect features. Required: id, text_a, text_b, features[{feature, variant_a, variant_b}]

**Also allowed in seminars (for testing language comprehension):**
- **quiz**: Multiple choice comprehension check. Required: id, instruction, items[{question, options[], correct}]. Use for testing understanding of debates, source arguments, not factual recall.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct, explanation}]. Good for testing understanding of historiographic positions.

**FORBIDDEN in seminar tracks** (these test mechanics, not comprehension):
match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words, error-correction, translate, order

### Seminar activity rules

1. **3-9 activities per seminar module.** Not more.
2. **Required types:** Every seminar module MUST have at least one `reading` + one `essay-response` + one `critical-analysis`.
3. **The golden rule:** Can the learner answer without reading the Ukrainian text? If YES → rewrite the activity. Activities test COMPREHENSION and CRITICAL THINKING, never factual recall.
4. **All instructions in Ukrainian.** Seminar learners are B2+.
5. **Follow the plan's activity_hints.** They specify exactly what to generate.

---

## Learner Level Context

**Level: A2 (Module 18/60) — ELEMENTARY**

The learner knows ~1200 words, understands basic grammar.

**Instructions in Ukrainian.** No English needed.

**All core activity types are appropriate.** Include error-correction, cloze, unjumble for deeper practice.


## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

### Pattern: phonetics-sounds-letters [§4.1.1, §4.1.4]
**Звуки і літери** (Sounds and letters)
- **quiz** — Звук чи літера?: Розрізнити звук і літеру — основа української фонетики / Distinguish звук from літера — fundamental Ukrainian phonetics distinction
  - Instruction: *Оберіть правильну відповідь*
- **match-up** — Літера → Звук: Зіставити літери зі звуковими значеннями, особливо багатозвучні (я, ю, є, ї) / Match letters to their sound values, especially multi-sound letters (я, ю, є, ї)
  - Instruction: *З'єднайте літеру зі звуком*
- **group-sort** — Голосні й приголосні: Розподілити звуки на голосні та приголосні / Sort letters/sounds into голосні (vowel) vs приголосні (consonant)
  - Instruction: *Розподіліть звуки*
- **image-to-letter** — Знайди літеру: Побачити зображення, визначити українську літеру / See image, identify the Ukrainian letter it starts with
**Anti-patterns (DO NOT generate):**
- ❌ translate: Переклад не тестує фонетичні знання
- ❌ fill-in-no-options: Занадто складно для A1 — початківці потребують варіантів відповідей

### Pattern: phonetics-soft-hard [§4.1.2, §4.1.3]
**М'який знак і апостроф** (Soft sign and apostrophe)
- **group-sort** — М'який чи твердий?: Розподілити приголосні/слова за м'якістю чи твердістю вимови / Sort consonants/words by soft vs hard pronunciation
  - Instruction: *Розподіліть*
- **quiz** — Де потрібен ь?: Обрати слово, де потрібен м'який знак / Choose which word needs м'який знак
- **error-correction** — Виправ помилку: Знайти, де м'який знак або апостроф пропущено або вжито неправильно / Find where м'який знак or апостроф is missing/wrong
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: Занадто складно для A1 без варіантів

### Pattern: phonetics-stress [§4.1.5]
**Наголос** (Word stress)
- **quiz** — Де наголос?: Обрати правильне місце наголосу — критично для української вимови / Choose the correct stress position — critical for Ukrainian pronunciation
  - Instruction: *Оберіть слово з правильним наголосом*
- **odd-one-out** — Четверте зайве за наголосом: Обрати слово з іншою моделлю наголосу / Pick the word with different stress pattern
**Anti-patterns (DO NOT generate):**
- ❌ fill-in: Наголос — це вимова, не написання. Тестувати через вибір, не вписування

### Pattern: grammar-gender [§4.2.1.1, §4.2.2]
**Рід іменників** (Noun gender)
- **group-sort** — Він, вона чи воно?: Розподілити іменники за граматичним родом за закінченням / Sort nouns by grammatical gender using ending rules
  - Instruction: *Розподіліть слова за родами*
- **quiz** — Який рід?: Визначити рід за закінченням: приголосний=чол., -а/-я=жін., -о/-е=серед. / Determine gender from ending — consonant=masc, -а/-я=fem, -о/-е=neut
- **fill-in** — Мій, моя чи моє?: Обрати присвійний займенник, що узгоджується з родом іменника / Choose possessive that matches noun gender
  - Instruction: *Вставте правильне слово*
- **match-up** — Іменник + займенник: Зіставити іменники з він/вона/воно / Match nouns to він/вона/воно
**Anti-patterns (DO NOT generate):**
- ❌ fill-in-no-options: На рівні A1 завжди давати варіанти для вибору

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

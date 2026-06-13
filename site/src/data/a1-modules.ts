/**
 * A1 curriculum manifest — bilingual (Ukrainian + English).
 *
 * Source of truth for the A1 landing page module list. Order matches
 * `curriculum/l2-uk-en/curriculum.yaml`. Each item carries both Ukrainian
 * and English title + sub so the landing page can present both languages
 * without a separate i18n layer.
 *
 * Status is NOT stored here — it is derived at build time in
 * `src/content/docs/a1/index.mdx` from filesystem detection of the
 * deployed `.mdx` siblings.
 */

export type A1ModuleEntry = {
  num: number;
  slug: string;
  title: string;       // Ukrainian (primary)
  titleEn: string;     // English (secondary)
  sub: string;         // Ukrainian description
  subEn: string;       // English description
};

export type A1UnitGroup = {
  unit: string;        // Bilingual section header: "A1.X [Ukrainian · English]"
  items: A1ModuleEntry[];
};

export const A1_UNITS: A1UnitGroup[] = [
  {
    unit: "A1.1 [Звуки, літери та перший контакт · Sounds, Letters, and First Contact]",
    items: [
      { num: 1, slug: "sounds-letters-and-hello", title: "Звуки, літери та привіт", titleEn: "Sounds, Letters & Hello", sub: "33 літери, 38 звуків, Привіт!", subEn: "33 letters, 38 sounds, Hello!" },
      { num: 2, slug: "reading-ukrainian", title: "Читаємо українською", titleEn: "Reading Ukrainian", sub: "Від літер до слів та речень", subEn: "From letters to words and sentences" },
      { num: 3, slug: "special-signs", title: "Особливі знаки", titleEn: "Special Signs", sub: "Ь, апостроф і три ключові контрасти — день, сім'я, буряк/бур'ян", subEn: "Soft sign, apostrophe, and three key contrasts" },
      { num: 4, slug: "stress-and-melody", title: "Наголос і мелодика", titleEn: "Stress & Melody", sub: "Наголос змінює значення, інтонація змінює намір", subEn: "Stress changes meaning, intonation changes intent" },
      { num: 5, slug: "who-am-i", title: "Хто я?", titleEn: "Who Am I?", sub: "Мене звати… — ваша перша справжня розмова", subEn: "My name is… — your first real conversation" },
      { num: 6, slug: "my-family", title: "Моя сім'я", titleEn: "My Family", sub: "У мене є брат — показуємо фотографії", subEn: "I have a brother — sharing photos" },
      { num: 7, slug: "checkpoint-first-contact", title: "Підсумок: Перший контакт", titleEn: "Checkpoint: First Contact", sub: "Чи вмієте ви читати, вітатися та розповідати про себе?", subEn: "Can you read, greet, and introduce yourself?" },
    ],
  },
  {
    unit: "A1.2 [Мій світ · My World]",
    items: [
      { num: 8, slug: "things-have-gender", title: "Речі мають рід", titleEn: "Things Have Gender", sub: "Він, вона, воно — кожен іменник має рід", subEn: "He, she, it — every noun has a gender" },
      { num: 9, slug: "what-is-it-like", title: "Який він?", titleEn: "What Is It Like?", sub: "Великий стіл, нова книга — опис предметів", subEn: "Big table, new book — describing objects" },
      { num: 10, slug: "colors", title: "Кольори", titleEn: "Colors", sub: "Синій, жовтий — кольори України та вашого світу", subEn: "Blue, yellow — colors of Ukraine and your world" },
      { num: 11, slug: "how-many", title: "Скільки?", titleEn: "How Many?", sub: "Один, два, три — числа через ціни, вік та номери телефонів", subEn: "One, two, three — numbers via prices, age, phones" },
      { num: 12, slug: "this-and-that", title: "Це і те", titleEn: "This and That", sub: "Цей стіл, та книга — вказуємо на предмети", subEn: "This table, that book — pointing at things" },
      { num: 13, slug: "many-things", title: "Багато речей", titleEn: "Many Things", sub: "Столи, книги, вікна — від однини до множини", subEn: "Tables, books, windows — from singular to plural" },
      { num: 14, slug: "checkpoint-my-world", title: "Підсумок: Мій світ", titleEn: "Checkpoint: My World", sub: "Чи вмієте ви описувати речі, рахувати та вказувати на них?", subEn: "Can you describe, count, and point at things?" },
    ],
  },
  {
    unit: "A1.3 [Дії · Actions]",
    items: [
      { num: 15, slug: "what-i-like", title: "Що я люблю", titleEn: "What I Like", sub: "Я люблю читати — ваші перші дієслова", subEn: "I like to read — your first verbs" },
      { num: 16, slug: "verbs-group-one", title: "Дієслова першої групи", titleEn: "First-Group Verbs", sub: "Читаю, читаєш, читає — ваша перша дієвідміна", subEn: "I read, you read, she reads — your first conjugation" },
      { num: 17, slug: "verbs-group-two", title: "Дієслова другої групи", titleEn: "Second-Group Verbs", sub: "Говорю, говориш, говорить — друга модель", subEn: "I speak, you speak, she speaks — the second pattern" },
      { num: 18, slug: "i-want-i-can", title: "Я хочу, я можу", titleEn: "I Want, I Can", sub: "Хочу, можу, мушу — як висловити бажання та можливості", subEn: "Want, can, must — wishes and abilities" },
      { num: 19, slug: "questions", title: "Питання", titleEn: "Questions", sub: "Хто? Що? Де? — як запитувати про світ", subEn: "Who? What? Where? — how to ask about the world" },
      { num: 20, slug: "my-morning", title: "Мій ранок", titleEn: "My Morning", sub: "Прокидаюся, вмиваюся — зворотні дієслова та ранкова рутина", subEn: "Waking up, washing — reflexive verbs and morning routine" },
      { num: 21, slug: "checkpoint-actions", title: "Перевірка: Дії", titleEn: "Checkpoint: Actions", sub: "Чи можете ви сказати, що ви робите, хочете, та ставити запитання?", subEn: "Can you say what you do, want, and ask questions?" },
    ],
  },
  {
    unit: "A1.4 [Час і природа · Time & Nature]",
    items: [
      { num: 22, slug: "what-time", title: "Котра година?", titleEn: "What Time?", sub: "Котра година? О котрій? — позначення часу", subEn: "What time is it? At what time? — telling time" },
      { num: 23, slug: "days-and-months", title: "Дні та місяці", titleEn: "Days & Months", sub: "У понеділок, у січні — календар українською", subEn: "On Monday, in January — calendar in Ukrainian" },
      { num: 24, slug: "weather", title: "Погода", titleEn: "Weather", sub: "Сьогодні холодно — розмовляємо про погоду", subEn: "It's cold today — talking about the weather" },
      { num: 25, slug: "my-day", title: "Мій день", titleEn: "My Day", sub: "Спочатку, потім, нарешті — як розповісти про свій день", subEn: "First, then, finally — describing your day" },
      { num: 26, slug: "free-time", title: "Вільний час", titleEn: "Free Time", sub: "Хобі, спорт, музика — що ви робите для задоволення", subEn: "Hobbies, sports, music — what you do for fun" },
      { num: 27, slug: "checkpoint-time-nature", title: "Підсумок: Час і природа", titleEn: "Checkpoint: Time & Nature", sub: "Чи вмієте ви називати час, планувати тиждень та описувати погоду?", subEn: "Can you tell time, plan the week, and describe the weather?" },
    ],
  },
  {
    unit: "A1.5 [Місця · Places]",
    items: [
      { num: 28, slug: "euphony", title: "Милозвучність", titleEn: "Euphony", sub: "У/в, і/й, з/із/зі — українська звучить красиво", subEn: "U/v, i/y, z/iz/zi — Ukrainian sounds beautiful" },
      { num: 29, slug: "where-is-it", title: "Де це?", titleEn: "Where Is It?", sub: "В школі, на роботі — місцевий відмінок", subEn: "At school, at work — the locative case" },
      { num: 30, slug: "my-city", title: "Моє місто", titleEn: "My City", sub: "Бібліотека, аптека, ресторан — лексика міста", subEn: "Library, pharmacy, restaurant — city vocabulary" },
      { num: 31, slug: "where-to", title: "Куди?", titleEn: "Where To?", sub: "Іду в банк, на роботу — знахідний відмінок для напрямку", subEn: "Going to the bank, to work — accusative for direction" },
      { num: 32, slug: "transport", title: "Транспорт", titleEn: "Transport", sub: "Автобус, метро, таксі — як пересуватися", subEn: "Bus, metro, taxi — how to get around" },
      { num: 33, slug: "around-the-city", title: "У місті", titleEn: "Around the City", sub: "Де/куди + напрямки — орієнтування містом українською", subEn: "Where / where to + directions — navigating the city" },
      { num: 34, slug: "where-from", title: "Звідки?", titleEn: "Where From?", sub: "Звідки ти? Я з України — походження та напрямки", subEn: "Where are you from? I'm from Ukraine — origin and direction" },
      { num: 35, slug: "checkpoint-places", title: "Підсумок: Місця", titleEn: "Checkpoint: Places", sub: "Чи вмієте ви орієнтуватися в українському місті?", subEn: "Can you navigate a Ukrainian city?" },
    ],
  },
  {
    unit: "A1.6 [Їжа та покупки · Food & Shopping]",
    items: [
      { num: 36, slug: "food-and-drink", title: "Їжа та напої", titleEn: "Food & Drink", sub: "Їжа і напої — що українці їдять і п'ють", subEn: "Food and drinks — what Ukrainians eat and drink" },
      { num: 37, slug: "i-eat-i-drink", title: "Я їм, я п'ю", titleEn: "I Eat, I Drink", sub: "Я їм хліб, п'ю каву — знахідний відмінок для того, що ви їсте та п'єте", subEn: "I eat bread, I drink coffee — accusative for what you eat and drink" },
      { num: 38, slug: "at-the-cafe", title: "У кафе", titleEn: "At the Café", sub: "У кафе — замовлення, оплата та культура кафе", subEn: "At the café — ordering, paying, café culture" },
      { num: 39, slug: "shopping", title: "Покупки", titleEn: "Shopping", sub: "Скільки коштує? — ціни, кількості та покупки", subEn: "How much does it cost? — prices, quantities, shopping" },
      { num: 40, slug: "people-around-me", title: "Люди навколо мене", titleEn: "People Around Me", sub: "Я бачу маму, знаю Олену — знахідний відмінок для істот", subEn: "I see Mum, I know Olena — accusative for animates" },
      { num: 41, slug: "checkpoint-food-shopping", title: "Підсумок: Їжа та покупки", titleEn: "Checkpoint: Food & Shopping", sub: "Чи вмієте ви замовляти їжу та купувати речі українською?", subEn: "Can you order food and shop in Ukrainian?" },
    ],
  },
  {
    unit: "A1.7 [Спілкування · Communication]",
    items: [
      { num: 42, slug: "hey-friend", title: "Гей, друже!", titleEn: "Hey, Friend!", sub: "Олено! Тарасе! Друже! Мамо! — звертання на ім'я", subEn: "Olena! Taras! Friend! Mum! — the vocative case" },
      { num: 43, slug: "please-do-this", title: "Будь ласка, зроби це", titleEn: "Please, Do This", sub: "Читай! Скажіть! Дайте! — як просити людей щось зробити", subEn: "Read! Say! Give! — asking people to do things" },
      { num: 44, slug: "linking-ideas", title: "Зв'язок думок", titleEn: "Linking Ideas", sub: "І, а, але, бо — як поєднувати свої думки", subEn: "And, but, because — connecting your thoughts" },
      { num: 45, slug: "when-and-where", title: "Коли і де", titleEn: "When & Where", sub: "Що, де, коли — будуємо перші складні речення", subEn: "What, where, when — building first complex sentences" },
      { num: 46, slug: "holidays", title: "Свята", titleEn: "Holidays", sub: "Привітання, родинні традиції та державні свята України", subEn: "Greetings, family traditions, Ukraine's state holidays" },
      { num: 47, slug: "checkpoint-communication", title: "Перевірка: Спілкування", titleEn: "Checkpoint: Communication", sub: "Чи вмієте ви звертатися до людей, давати вказівки та поєднувати думки?", subEn: "Can you address people, give instructions, and connect ideas?" },
    ],
  },
  {
    unit: "A1.8 [Минуле, майбутнє, випускний · Past, Future, Graduation]",
    items: [
      { num: 48, slug: "what-happened", title: "Що сталося?", titleEn: "What Happened?", sub: "Він читав, вона читала — минулий час і рід", subEn: "He read, she read — past tense and gender" },
      { num: 49, slug: "yesterday", title: "Учора", titleEn: "Yesterday", sub: "Учора я прокинувся, поснідав і пішов — розповідь про свій день", subEn: "Yesterday I woke up, ate, and left — telling your day" },
      { num: 50, slug: "what-will-happen", title: "Що буде?", titleEn: "What Will Happen?", sub: "Я буду читати — ваш перший майбутній час", subEn: "I will read — your first future tense" },
      { num: 51, slug: "my-plans", title: "Мої плани", titleEn: "My Plans", sub: "У суботу я буду… — розклад та плани на вихідні", subEn: "On Saturday I'll… — schedules and weekend plans" },
      { num: 52, slug: "my-story", title: "Моя історія", titleEn: "My Story", sub: "Я народився, я живу, я буду… — твоє життя у трьох часах", subEn: "I was born, I live, I will be… — your life across three tenses" },
      { num: 53, slug: "health", title: "Здоров'я", titleEn: "Health", sub: "У мене болить голова — частини тіла та симптоми", subEn: "I have a headache — body parts and symptoms" },
      { num: 54, slug: "emergencies", title: "Екстрені ситуації", titleEn: "Emergencies", sub: "Допоможіть! Викличте швидку! — українська для виживання", subEn: "Help! Call an ambulance! — survival Ukrainian" },
      { num: 55, slug: "a1-finale", title: "Фінал А1", titleEn: "A1 Finale", sub: "Один повний день в українському місті — усе, що ви вивчили", subEn: "A full day in a Ukrainian city — everything you've learned" },
    ],
  },
];

/**
 * Slugs that exist under `starlight/src/content/docs/a1/` but are NOT
 * curriculum modules — exclude them when deriving deployment status.
 */
export const A1_NON_MODULE_SLUGS = new Set<string>([
  "index",
  "review-clears-needs-human",
]);

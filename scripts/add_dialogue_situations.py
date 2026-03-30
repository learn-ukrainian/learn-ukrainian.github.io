"""Add dialogue_situations to plans that have Діалоги sections.

Generates unique, grammar-motivated dialogue settings for each module.
Human reviews output before committing.

Usage:
    .venv/bin/python scripts/add_dialogue_situations.py --track a1 [--dry-run]
    .venv/bin/python scripts/add_dialogue_situations.py --track a1 --apply

Issue: #1102
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLANS_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en" / "plans"

# ────────────────────────────────────────────────
# A1 dialogue situations — hand-curated per module
# Each module gets 1-2 unique settings that MOTIVATE the grammar taught.
# NO MODULE may share a setting with another.
# ────────────────────────────────────────────────

A1_SITUATIONS: dict[str, list[dict]] = {
    "who-am-i": [
        {"setting": "Hostel common room — two backpackers meet for the first time",
         "speakers": ["Марко (Canadian student)", "Олена (from Kyiv)"],
         "motivation": "Мене звати, Звідки ти? — real first-meeting context"},
        {"setting": "University orientation day — students introduce themselves to the group",
         "speakers": ["Тарас (new student)", "Софія (second-year volunteer)"],
         "motivation": "Formal vs informal register, professions with Я — студент"},
    ],
    "my-family": [
        {"setting": "Video call showing phone photos to a new friend",
         "speakers": ["Оля", "Марк"],
         "motivation": "У мене є + family members, possessives мій/моя with photos"},
        {"setting": "Filling out a visa application together — helping each other with family questions",
         "speakers": ["Даша (applicant)", "Андрій (friend helping)"],
         "motivation": "Family vocabulary, У тебе є брати? in practical context"},
    ],
    "checkpoint-first-contact": [
        {"setting": "Conference coffee break — two professionals meet between sessions",
         "speakers": ["Богдан (engineer from Dnipro)", "Соломія (teacher from Ternopil)"],
         "motivation": "Consolidation: name, origin, profession, family — full introduction"},
    ],
    "things-have-gender": [
        {"setting": "At a pet shop — looking at animals and their accessories. "
         "A кіт (m) sleeps in a кошик (m, basket), a рибка (f) swims in an акваріум (m), "
         "a черепаха (f, turtle) sits near a дзеркало (n, mirror). "
         "Use animals and pet items to demonstrate він/вона/воно — not room furniture.",
         "speakers": ["Марія", "Оленка"],
         "motivation": "Він/вона/воно with кіт(m), рибка(f), кошеня(n), акваріум(m), черепаха(f)"},
    ],
    "what-is-it-like": [
        {"setting": "At a weekend book fair — browsing books, maps, and posters. "
         "Describe items: новий атлас (m), цікава книга (f), старе фото (n), "
         "великий плакат (m), маленька листівка (f, postcard). NOT bags or furniture.",
         "speakers": ["Тарас", "Софія"],
         "motivation": "Який/яка/яке? with книга(f), атлас(m), фото(n), плакат(m), листівка(f)"},
    ],
    "colors": [
        {"setting": "At an outdoor flower market — choosing bouquets for different occasions. "
         "Describe: червоні троянди (roses), білі лілії (lilies), жовті соняшники (sunflowers), "
         "синя ваза (f), зелене листя (n, leaves). Use flowers, plants, and wrapping.",
         "speakers": ["Наталка", "Продавець (flower seller)"],
         "motivation": "Color adjectives: червоний/а/е with троянда(f), соняшник(m), листя(n)"},
        {"setting": "Choosing an outfit for a party from a friend's wardrobe. "
         "Describe: чорна сукня (f, dress), білий светр (m, sweater), сіре пальто (n, coat), "
         "коричневі черевики (pl, shoes). Use clothing items, NOT bags.",
         "speakers": ["Дмитро", "Ліза"],
         "motivation": "Color + gender: сукня(f), светр(m), пальто(n), черевики(pl)"},
    ],
    "how-many": [
        {"setting": "At a bakery — ordering bread, pastries, and cakes for a family gathering. "
         "Count: хліб (m, bread), булочка (f, bun), тістечко (n, pastry). "
         "Prices in гривні. Ask: Скільки коштує торт? А три булочки?",
         "speakers": ["Покупець", "Пекар (baker)"],
         "motivation": "Скільки коштує? with торт(m), булочка(f), тістечко(n), хліб(m)"},
        {"setting": "Counting items in a school backpack before class — "
         "ручка (f, pen), олівець (m, pencil), зошит (m, notebook), підручник (m, textbook).",
         "speakers": ["Учень (student)", "Мама"],
         "motivation": "Numbers with school supplies: один олівець, дві ручки, п'ять зошитів"},
    ],
    "this-and-that": [
        {"setting": "At an electronics store — comparing phones, laptops, and headphones "
         "on different shelves. Цей телефон (m, this phone near you) vs той ноутбук (m, "
         "that laptop over there). Ця камера (f) vs та. Це радіо (n) vs те.",
         "speakers": ["Ірина", "Консультант (shop assistant)"],
         "motivation": "Цей/ця/це vs той/та/те with телефон(m), камера(f), радіо(n)"},
    ],
    "many-things": [
        {"setting": "Setting up a classroom for a Ukrainian lesson — counting and arranging items. "
         "Singular → plural: один стілець → стільці, одна дошка → дошки, "
         "одне крісло → крісла. Also: олівці, ручки, підручники, карти.",
         "speakers": ["Вчитель (teacher)", "Учні (students)"],
         "motivation": "Plurals with classroom items: стілець→стільці, дошка→дошки, крісло→крісла"},
    ],
    "checkpoint-my-world": [
        {"setting": "Walking through a Ukrainian street market (ярмарок) — "
         "pointing at handmade crafts: вишиванка (f, embroidered shirt), глечик (m, jug), "
         "намисто (n, necklace), писанки (pl, decorated eggs). Describe, count, point, buy.",
         "speakers": ["Ваня (tourist)", "Катя (local friend)"],
         "motivation": "Consolidation with Ukrainian cultural objects: вишиванка, глечик, писанка"},
    ],
    "what-i-like": [
        {"setting": "First day at a language exchange — sharing hobbies over tea",
         "speakers": ["Анна (learner)", "Віктор (tandem partner)"],
         "motivation": "Люблю + infinitive: Люблю читати, Люблю малювати"},
    ],
    "verbs-group-one": [
        {"setting": "In a shared kitchen — one person cooking, other asking what they're doing",
         "speakers": ["Юля (cooking)", "Сашко (curious)"],
         "motivation": "Group I verbs in action: читаєш, працюєш, готуєш"},
    ],
    "verbs-group-two": [
        {"setting": "At a gym — two friends doing different exercises, describing actions",
         "speakers": ["Тарас", "Микола"],
         "motivation": "Group II verbs: бачиш, говориш, робиш in physical context"},
    ],
    "i-want-i-can": [
        {"setting": "Planning a weekend — negotiating what to do",
         "speakers": ["Оля", "Денис"],
         "motivation": "Хочу/можу/мушу + infinitive: Хочу піти в кіно, Не можу, мушу працювати"},
    ],
    "questions": [
        {"setting": "A tourist asking a local for help navigating the city center",
         "speakers": ["Турист", "Перехожий (passerby)"],
         "motivation": "Question words: Де? Куди? Як? Коли? in real navigation"},
    ],
    "my-morning": [
        {"setting": "Two roommates comparing their morning routines before leaving for work",
         "speakers": ["Ліна", "Настя"],
         "motivation": "Reflexive verbs: прокидаюся, вмиваюся, одягаюся in sequence"},
    ],
    "checkpoint-actions": [
        {"setting": "Job interview — describing your typical day, skills, and schedule",
         "speakers": ["Кандидат (applicant)", "Менеджер"],
         "motivation": "Consolidation: verbs, modals, questions, reflexives"},
    ],
    "what-time": [
        {"setting": "Coordinating a meeting time over the phone — both checking schedules",
         "speakers": ["Марина", "Олексій"],
         "motivation": "О котрій годині? time expressions in scheduling"},
    ],
    "days-and-months": [
        {"setting": "At a doctor's reception — booking an appointment",
         "speakers": ["Пацієнт", "Реєстратор"],
         "motivation": "Days and months: У понеділок? Ні, у середу. В якому місяці?"},
    ],
    "weather": [
        {"setting": "Two friends deciding whether to go hiking — checking weather together",
         "speakers": ["Іванко", "Галя"],
         "motivation": "Impersonal: Сьогодні холодно, Завтра буде тепло, Іде дощ"},
    ],
    "my-day": [
        {"setting": "Writing a blog post / diary entry about your day — reading it to a friend",
         "speakers": ["Автор (narrator)", "Друг (listener, reacting)"],
         "motivation": "Sequence words: спочатку, потім, нарешті in narration"},
    ],
    "free-time": [
        {"setting": "At a community center bulletin board — discussing activity sign-ups",
         "speakers": ["Вітя", "Лєна"],
         "motivation": "Frequency adverbs: Часто ходиш? Іноді. Ходімо разом!"},
    ],
    "checkpoint-time-nature": [
        {"setting": "Planning a road trip together — dates, weather, schedule",
         "speakers": ["Організатор", "Друзі"],
         "motivation": "Consolidation: time, calendar, weather, daily routine"},
    ],
    "euphony": [
        {"setting": "Proofreading a friend's Ukrainian essay about their город (garden) — "
         "spotting у/в and і/й errors. Text mentions: у городі/в городі, і яблука/й яблука, "
         "у школі/в школі. Read sentences aloud to hear the difference.",
         "speakers": ["Студент (writing)", "Друг (correcting)"],
         "motivation": "У/в, і/й alternation with город(m), школа(f), яблуко(n)"},
    ],
    "where-is-it": [
        {"setting": "First week in a new city — asking a neighbor where to find: "
         "аптека (f, pharmacy), банк (m, bank), пошта (f, post office), кафе (n, café), "
         "лікарня (f, hospital), парк (m, park). В аптеці, на пошті, у банку.",
         "speakers": ["Новий мешканець (newcomer)", "Сусід (neighbor)"],
         "motivation": "В/на + locative with аптека(f), банк(m), пошта(f), кафе(n)"},
    ],
    "my-city": [
        {"setting": "Drawing a map of your Kyiv neighborhood for a pen pal — "
         "marking: бібліотека (f), музей (m, museum), площа (f, square), "
         "озеро (n, lake), зупинка (f, bus stop), церква (f, church). "
         "Use біля, поруч з, далеко від for distances.",
         "speakers": ["Аліна (describing)", "Ігор (asking questions)"],
         "motivation": "City vocab with бібліотека(f), музей(m), площа(f), озеро(n)"},
    ],
    "where-to": [
        {"setting": "Running Saturday errands together — splitting up: "
         "Я іду в банк (m), а ти — на пошту (f). Потім зустрінемося в кафе (n). "
         "Also: в аптеку, на зупинку, в бібліотеку.",
         "speakers": ["Оксана", "Степан"],
         "motivation": "Куди? + accusative: банк(m), пошта(f), кафе(n), аптека(f)"},
    ],
    "transport": [
        {"setting": "Explaining how to get from Kyiv airport (Бориспіль) to the hotel — "
         "автобус (m), потяг (m, train), таксі (n), метро (n). "
         "Їхати автобусом, потягом. Їхати на метро, на таксі.",
         "speakers": ["Приїжджий (visitor)", "Друг (local)"],
         "motivation": "Transport: автобус(m), потяг(m), таксі(n), метро(n)"},
    ],
    "around-the-city": [
        {"setting": "Walking tour of Lviv old town — going from Площа Ринок (f, main square) "
         "to Оперний театр (m, Opera house) to Високий замок (m, High Castle). "
         "Де ми? На площі. Куди далі? В театр. Звідки прийшли? З замку.",
         "speakers": ["Гід (guide)", "Туристи"],
         "motivation": "Де/Куди/Звідки with площа(f), театр(m), замок(m), парк(m)"},
    ],
    "where-from": [
        {"setting": "International student mixer at a Kyiv university — "
         "sharing origins: Я з Канади, Вона з Японії, Він з Німеччини. "
         "Also: З якого міста? З Торонто, з Токіо, з Берліна.",
         "speakers": ["Кілька студентів (group)"],
         "motivation": "Звідки? + з: Канада(f), Японія(f), Німеччина(f), Торонто(n)"},
    ],
    "checkpoint-places": [
        {"setting": "Video-calling a friend while walking through Одеса (Odesa) — "
         "showing: Дерибасівська вулиця (f), Потьомкінські сходи (pl, Potemkin Stairs), "
         "порт (m, port), пляж (m, beach). Describing where you are, where you're going.",
         "speakers": ["Мешканець (filming)", "Онлайн-друг (watching)"],
         "motivation": "Consolidation with вулиця(f), сходи(pl), порт(m), пляж(m)"},
    ],
    "food-and-drink": [
        {"setting": "Cooking борщ (m, borshch) with grandma — listing ingredients: "
         "буряк (m, beetroot), картопля (f, potato), капуста (f, cabbage), "
         "м'ясо (n, meat), морква (f, carrot), цибуля (f, onion), сметана (f, sour cream).",
         "speakers": ["Бабуся (teaching)", "Онучка (learning)"],
         "motivation": "Food with буряк(m), картопля(f), капуста(f), м'ясо(n), сметана(f)"},
    ],
    "i-eat-i-drink": [
        {"setting": "Lunch break at work — unpacking lunch boxes: "
         "Я їм бутерброд (m, sandwich) і п'ю чай (m, tea). "
         "А ти? Я їм салат (m) і п'ю каву (f, coffee). "
         "Also: яблуко (n), банан (m), вода (f), сік (m, juice).",
         "speakers": ["Колега 1", "Колега 2"],
         "motivation": "Accusative: бутерброд(m), салат(m), каву(f→acc), яблуко(n), чай(m)"},
    ],
    "at-the-cafe": [
        {"setting": "A date at a cozy Lviv café — ordering from the menu: "
         "кава (f, coffee), чай (m, tea), тістечко (n, pastry), "
         "круасан (m, croissant), вода (f, water), сік (m, juice). "
         "Мені каву, будь ласка. А мені — чай і тістечко.",
         "speakers": ["Ростик", "Іванка"],
         "motivation": "Ordering with кава(f), чай(m), тістечко(n), круасан(m)"},
    ],
    "shopping": [
        {"setting": "At a Ukrainian supermarket — comparing prices of: "
         "хліб (m, bread) — 25 грн, молоко (n, milk) — 42 грн, "
         "сир (m, cheese) — 89 грн, ковбаса (f, sausage) — 120 грн, "
         "масло (n, butter) — 65 грн. Скільки коштує сир? А молоко?",
         "speakers": ["Мама", "Дочка"],
         "motivation": "Prices with хліб(m), молоко(n), сир(m), ковбаса(f), масло(n)"},
    ],
    "people-around-me": [
        {"setting": "Showing wedding photos — identifying people: "
         "Бачиш маму (f→acc)? А тата (m→acc)? Знаєш Олену (f→acc)? "
         "Це мій дядько (m), а це тітка (f). Ось наречена (f) і наречений (m).",
         "speakers": ["Наречена", "Друг"],
         "motivation": "Accusative animate: маму(f), тата(m), Олену(f), дядька(m)"},
    ],
    "checkpoint-food-shopping": [
        {"setting": "Hosting a вечеря (f, dinner party) — full flow: "
         "shopping for продукти (pl) at the ринок (m, market), "
         "cooking вареники (pl) and салат (m), "
         "setting the table with тарілки (pl, plates) and склянки (pl, glasses), "
         "serving guests.",
         "speakers": ["Господиня (host)", "Гості (guests)"],
         "motivation": "Consolidation: продукти(pl), вареники(pl), тарілка(f), склянка(f)"},
    ],
    "hey-friend": [
        {"setting": "At a busy birthday party — calling people across the room by name: "
         "Олено! Тарасе! Друже! Мамо! Бабусю! Дідусю! "
         "Each person is doing something different (dancing, eating, talking).",
         "speakers": ["Іменинник (birthday person)", "Друзі"],
         "motivation": "Vocative: Олена→Олено, Тарас→Тарасе, мама→мамо, бабуся→бабусю"},
    ],
    "please-do-this": [
        {"setting": "Rearranging a classroom before an event — giving instructions: "
         "Постав стілець (m) тут! Перенеси дошку (f)! Відкрий вікно (n)! "
         "Принеси маркер (m)! Поклади книги (pl) на стіл!",
         "speakers": ["Вчитель (teacher)", "Учні (students)"],
         "motivation": "Imperative with стілець(m), дошка(f), вікно(n), маркер(m), книги(pl)"},
    ],
    "linking-ideas": [
        {"setting": "Debating where to go on vacation — comparing Карпати (pl, Carpathians) "
         "vs море (n, sea). Гори гарні, але далеко. Море тепле, бо літо. "
         "Я хочу в гори, а ти — на море. Поїдемо в Карпати, бо там дешевше.",
         "speakers": ["Подружжя (couple)"],
         "motivation": "І, а, але, бо with Карпати(pl), море(n), гори(pl)"},
    ],
    "when-and-where": [
        {"setting": "Explaining to a lost friend how to find your apartment: "
         "Коли побачиш аптеку (f), поверни ліворуч. Де побачиш парк (m), "
         "зупинись. Будинок (m), що стоїть біля дерева (n).",
         "speakers": ["Господар (on phone)", "Гість (lost outside)"],
         "motivation": "Complex sentences: що, де, коли with аптека(f), парк(m), будинок(m)"},
    ],
    "holidays": [
        {"setting": "Ukrainian Святвечір (m, Christmas Eve) dinner — explaining 12 dishes: "
         "кутя (f, kutia), борщ (m), вареники (pl), риба (f, fish), "
         "узвар (m, dried fruit compote). З Різдвом! З Новим роком!",
         "speakers": ["Українська родина", "Іноземний гість"],
         "motivation": "Holiday food: кутя(f), борщ(m), вареники(pl), узвар(m) + greetings"},
    ],
    "checkpoint-communication": [
        {"setting": "Organizing a шкільний ярмарок (m, school fair) — "
         "delegating: Олено, принеси плакати (pl)! Тарасе, постав столи (pl)! "
         "Ми маємо квитки (pl) і напої (pl). Нам потрібні стільці, бо людей багато.",
         "speakers": ["Організатор", "Волонтери"],
         "motivation": "Vocative + imperative + conjunctions with плакат(m), квиток(m), напій(m)"},
    ],
    "what-happened": [
        {"setting": "Monday morning at work — sharing weekend: "
         "Я ходив на концерт (m). Я читала роман (m). Ми гуляли в парку (m). "
         "Він дивився фільм (m). Вона готувала вечерю (f).",
         "speakers": ["Колеги (coworkers)"],
         "motivation": "Past tense with концерт(m), роман(m), парк(m), фільм(m), вечеря(f)"},
    ],
    "yesterday": [
        {"setting": "Police report — describing a stolen велосипед (m, bicycle): "
         "Я припаркував велосипед біля магазину (m). Потім зайшов у кав'ярню (f). "
         "Коли вийшов, велосипед зник. Бачив чоловіка (m) в синій куртці (f).",
         "speakers": ["Свідок (witness)", "Поліцейський"],
         "motivation": "Past narration with велосипед(m), магазин(m), кав'ярня(f), куртка(f)"},
    ],
    "what-will-happen": [
        {"setting": "Fortune teller at a fun fair — predicting the future: "
         "Ти будеш подорожувати. Знайдеш нову роботу (f). "
         "Зустрінеш друга (m). Отримаєш подарунок (m, gift). Будеш щасливий/щаслива!",
         "speakers": ["Ворожка (fortune teller)", "Клієнт"],
         "motivation": "Future with робота(f), друг(m), подарунок(m)"},
    ],
    "my-plans": [
        {"setting": "Group chat planning the weekend — "
         "У суботу буду прибирати квартиру (f). А я буду бігати в парку (m). "
         "Може, ввечері підемо в кіно (n)? Ходімо! О котрій?",
         "speakers": ["Група друзів (3 people)"],
         "motivation": "Future + scheduling with квартира(f), парк(m), кіно(n)"},
    ],
    "my-story": [
        {"setting": "Grandparent telling their life story — "
         "Я народився в селі (n, village). Ходив у школу (f). "
         "Зараз живу в місті (n, city). Працюю в лікарні (f, hospital). "
         "Буду відпочивати на дачі (f, dacha).",
         "speakers": ["Дідусь/Бабуся", "Онуки"],
         "motivation": "Three tenses with село(n), школа(f), місто(n), лікарня(f), дача(f)"},
    ],
    "health": [
        {"setting": "At the doctor's office — describing symptoms: "
         "У мене болить голова (f, head). Болить горло (n, throat). "
         "Болить живіт (m, stomach). Нежить (m, runny nose). Кашель (m, cough). "
         "Температура (f, fever).",
         "speakers": ["Пацієнт", "Лікар"],
         "motivation": "Body parts: голова(f), горло(n), живіт(m), температура(f)"},
    ],
    "emergencies": [
        {"setting": "A minor car accident on вулиця Хрещатик (f) — "
         "calling 103: Допоможіть! Аварія (f, accident) на Хрещатику! "
         "Потрібна швидка (f, ambulance)! Є постраждалий (m, injured person). "
         "Машина (f, car) пошкоджена.",
         "speakers": ["Водій (driver)", "Оператор 103"],
         "motivation": "Emergency with аварія(f), швидка(f), машина(f), вулиця(f)"},
    ],
    "a1-finale": [
        {"setting": "Full day in Kyiv — from hotel checkout to evening train departure",
         "speakers": ["Турист (spending final day)", "Various locals"],
         "motivation": "Everything: greetings, directions, ordering, shopping, past/future tense"},
    ],
}


A2_SITUATIONS = {
    "a2-bridge": [
        {"setting": "Arrival at a Kyiv language school on the first day of A2 — "
         "reviewing what you know: Я з Канади (genitive). Мені 25 (dative). "
         "Я вивчаю українську мову (accusative). Я живу в Києві (locative).",
         "speakers": ["Новий студент", "Викладач (teacher)"],
         "motivation": "Review all A1 cases in a natural intro conversation"},
    ],
    "aspect-in-vocabulary": [
        {"setting": "Cooking varenyky together — one person reads the recipe step by step: "
         "Ліпи (impf, keep forming) вареники. Зліпи (pf, form one). "
         "Вари (impf) 10 хвилин. Звари (pf) до готовності.",
         "speakers": ["Бабуся (teaching recipe)", "Онучка (cooking)"],
         "motivation": "Aspect pairs in cooking: ліпити/зліпити, варити/зварити"},
    ],
    "genitive-intro": [
        {"setting": "Moving into a new apartment — discovering what's missing: "
         "Немає холодильника (m, fridge)! Немає плити (f, stove)! "
         "Немає дзеркала (n, mirror)! Є багато коробок (pl, boxes) але мало меблів (pl, furniture).",
         "speakers": ["Сусідка (neighbor)", "Нова мешканка (new tenant)"],
         "motivation": "Genitive with немає: холодильник→холодильника, плита→плити, дзеркало→дзеркала"},
    ],
    "genitive-dates-numbers": [
        {"setting": "Booking a hotel room over the phone — dates and prices: "
         "З якого числа? З п'ятого березня. До якого? До десятого. "
         "Скільки номерів? Два номери. Скільки гостей? П'ять гостей.",
         "speakers": ["Гість", "Адміністратор готелю"],
         "motivation": "Genitive with dates: п'ятого березня, and counting: два номери, п'ять гостей"},
    ],
    "foundations-practice": [
        {"setting": "Scenario 1: Planning a housewarming party — buying торт (m, cake), "
         "напої (pl, drinks), серветки (pl, napkins). Скільки гостей? Десять. "
         "Scenario 2: At a Kyiv farmers market — buying мед (m, honey), сир (m, cheese), "
         "ягоди (pl, berries). Скільки коштує кілограм меду?",
         "speakers": ["Друзі (friends)", "Продавець (vendor)"],
         "motivation": "Genitive in real life: counting, prices, absence"},
    ],
    "genitive-prepositions-purpose": [
        {"setting": "Packing for a camping trip — deciding what's needed: "
         "Для кого ця ковдра (f, blanket)? Для Олени. Без ліхтарика (m, flashlight) — ніяк! "
         "Біля річки (f, river) поставимо намет (m, tent).",
         "speakers": ["Ігор", "Марта"],
         "motivation": "Для/без/біля + genitive: ковдра(f), ліхтарик(m), річка(f), намет(m)"},
    ],
    "genitive-adjectives-pronouns": [
        {"setting": "At a lost-and-found office — describing lost items with full adjective phrases: "
         "Це сумка мого старшого брата (m). Ви не бачили цієї червоної парасольки (f, umbrella)? "
         "Тут немає нашого великого чемодану (m, suitcase)?",
         "speakers": ["Власник (owner)", "Працівник бюро знахідок"],
         "motivation": "Genitive adj+noun: мого брата, цієї парасольки, нашого чемодану"},
    ],
    "genitive-plural": [
        {"setting": "Inventory check at a small village shop — counting what's left: "
         "Скільки пляшок (f, bottles) води? П'ять. Скільки банок (f, jars) меду? "
         "Три. А булок (f, buns)? Немає булок!",
         "speakers": ["Продавець", "Помічник (assistant)"],
         "motivation": "Genitive plural: пляшок, банок, булок — feminine zero ending"},
    ],
    "shopping-and-health": [
        {"setting": "At a Kyiv ринок (m, market) — buying produce: "
         "Дайте мені кілограм помідорів (m, tomatoes) і півкіло огірків (m, cucumbers). "
         "Then at the лікар (m, doctor): У мене болить горло (n, throat). "
         "Then at the аптека (f, pharmacy): Мені потрібні краплі (pl, drops).",
         "speakers": ["Покупець/Пацієнт", "Продавець/Лікар/Фармацевт"],
         "motivation": "Three real situations: помідор(m), огірок(m), горло(n), краплі(pl)"},
    ],
    "dative-pronouns": [
        {"setting": "Distributing birthday gifts at a family gathering — who gets what: "
         "Мені — книгу. Тобі — шоколад. Йому — шарф (m, scarf). "
         "Їй — квіти (pl, flowers). Нам — торт!",
         "speakers": ["Іменинник", "Родина"],
         "motivation": "Dative pronouns: мені, тобі, йому, їй with подарунок(m), книга(f)"},
    ],
    "dative-nouns": [
        {"setting": "At a post office — addressing packages to different people: "
         "Студентові Петренку — підручник (m, textbook). "
         "Сестрі Олені — листівка (f, postcard). Дитині — іграшка (f, toy).",
         "speakers": ["Відправник (sender)", "Працівник пошти"],
         "motivation": "Dative nouns: студент→студентові, сестра→сестрі, дитина→дитині"},
    ],
    "dative-adjectives-pronouns": [
        {"setting": "Teacher handing back graded essays — giving to specific students: "
         "Моєму найкращому студентові — десятка! Нашій новій студентці — дев'ятка. "
         "Цьому хлопцю треба більше працювати.",
         "speakers": ["Вчитель", "Студенти"],
         "motivation": "Full dative phrases: моєму студентові, нашій студентці, цьому хлопцю"},
    ],
    "dative-verbs": [
        {"setting": "Community volunteer day — helping different people: "
         "Допомагаю бабусі (f, grandma) нести сумки. Дзвоню другові (m, friend). "
         "Раджу сусідці (f, neighbor) нового лікаря. Мені подобається допомагати!",
         "speakers": ["Волонтер", "Різні люди"],
         "motivation": "Dative verbs: допомагати бабусі, дзвонити другові, радити сусідці"},
    ],
    "services-and-communication": [
        {"setting": "At Укрпошта (Ukrainian postal service) — sending a parcel to relatives: "
         "Бандероль (f, parcel) для сестри в Канаду. Скільки коштує? "
         "Заповніть бланк (m, form). Адреса одержувача (m, recipient)?",
         "speakers": ["Відправник", "Працівник пошти"],
         "motivation": "Post office: бандероль(f), бланк(m), адреса(f), одержувач(m)"},
    ],
    "instrumental-accompaniment": [
        {"setting": "Planning a picnic — who's coming with whom and bringing what: "
         "Я іду з Олегом (m). Вона прийде з подругою (f, girlfriend). "
         "Візьмемо каву з молоком (n, milk). Бутерброди з шинкою (f, ham).",
         "speakers": ["Організатор пікніку", "Друзі"],
         "motivation": "З + instrumental: з Олегом, з подругою, з молоком, з шинкою"},
    ],
    "instrumental-means": [
        {"setting": "Art class — discussing tools and methods: "
         "Малюю олівцем (m, pencil). Фарбую пензлем (m, brush). "
         "Різаю ножицями (pl, scissors). Їду на виставку автобусом (m, bus).",
         "speakers": ["Вчитель мистецтва", "Учні"],
         "motivation": "Instrumental of means: олівець→олівцем, пензель→пензлем, ножиці→ножицями"},
    ],
    "instrumental-profession": [
        {"setting": "High school reunion — catching up on careers: "
         "Я стала лікаркою (f). Він працює інженером (m). "
         "Вона хоче бути журналісткою (f). А ти?",
         "speakers": ["Колишні однокласники (former classmates)"],
         "motivation": "Бути + instrumental: лікарка→лікаркою, інженер→інженером"},
    ],
    "instrumental-prepositions": [
        {"setting": "Giving directions inside a museum — spatial prepositions: "
         "Картина (f, painting) над каміном (m, fireplace). Скульптура (f) між вікнами (pl). "
         "Лавка (f, bench) під деревом (n, tree). Кафе за музеєм (m).",
         "speakers": ["Гід музею", "Відвідувачі"],
         "motivation": "Над/під/між/за + instrumental: камін→каміном, вікно→вікнами, дерево→деревом"},
    ],
    "instrumental-adjectives-pronouns": [
        {"setting": "Writing a diary entry about your perfect day — full instrumental phrases: "
         "Гуляла з моїм найкращим другом (m). Обідала зі своєю старшою сестрою (f). "
         "Пила каву з тим новим колегою (m).",
         "speakers": ["Автор щоденника (diary writer, narrating)"],
         "motivation": "Full instrumental: з моїм другом, зі своєю сестрою, з тим колегою"},
    ],
    "work-and-food": [
        {"setting": "Job interview at a restaurant — talking about experience and cooking a test dish: "
         "Ким ви працювали? Кухарем (m, cook). Що ви вмієте готувати? "
         "Борщ з яловичиною (f, beef), вареники з картоплею (f, potato).",
         "speakers": ["Шеф-кухар (head chef)", "Кандидат"],
         "motivation": "Professions + cooking: кухар→кухарем, з яловичиною, з картоплею"},
    ],
    "plural-nominative-accusative": [
        {"setting": "At a zoo — identifying animals and their groups: "
         "Дивись — леви (m, lions)! Бачиш тих жирафів (m, giraffes)? "
         "А ось мавпи (f, monkeys)! Діти люблять пінгвінів (m, penguins).",
         "speakers": ["Батько/Мати", "Діти"],
         "motivation": "Nom plural: лев→леви. Acc animate plural: жираф→жирафів, пінгвін→пінгвінів"},
    ],
    "plural-genitive": [
        {"setting": "School cafeteria inventory — counting remaining items: "
         "Скільки тарілок (f, plates)? Двадцять. Виделок (f, forks)? П'ятнадцять. "
         "Ложок (f, spoons)? Десять. Склянок (f, glasses)? Немає склянок!",
         "speakers": ["Завідувач їдальні (cafeteria manager)", "Помічник"],
         "motivation": "Genitive plural: тарілка→тарілок, виделка→виделок, склянка→склянок"},
    ],
    "plural-other-cases": [
        {"setting": "Organizing a school trip — all cases in plural: "
         "Розкажіть дітям (dat pl) план. Їдемо автобусами (inst pl). "
         "Зупинимося в готелях (loc pl). Купимо подарунки для батьків (gen pl).",
         "speakers": ["Вчитель", "Учні"],
         "motivation": "All plural cases: дітям, автобусами, готелях, батьків"},
    ],
    "all-cases-practice": [
        {"setting": "Dialogue 1: Organizing a surprise birthday party at a ресторан (m) — "
         "calling, ordering торт (m), buying подарунок (m) для подруги (f). "
         "Dialogue 2: At a лікарня (f) — describing symptoms to лікар (m). "
         "Dialogue 3: Planning a trip across Ukraine — Львів, Одеса, Карпати.",
         "speakers": ["Various speakers per dialogue"],
         "motivation": "All cases in real scenarios: restaurant, hospital, travel"},
    ],
    "home-and-daily-life": [
        {"setting": "Scenario 1: Video tour of your помешкання (n, apartment) — "
         "кухня (f, kitchen), вітальня (f, living room), спальня (f, bedroom). "
         "Scenario 2: Describing your розпорядок дня (m, daily routine). "
         "Scenario 3: Visiting Ukrainian friends — bringing гостинці (pl, gifts).",
         "speakers": ["Мешканець", "Онлайн-друг / Господарі"],
         "motivation": "Home + daily life: кухня(f), вітальня(f), спальня(f), гостинці(pl)"},
    ],
    "synthetic-future": [
        {"setting": "Making New Year's resolutions with friends — "
         "Я напишу книгу (f)! Я вивчу іспанську (f)! "
         "Він прочитає 50 книг! Вона здасть іспит (m, exam)!",
         "speakers": ["Група друзів на Новий рік"],
         "motivation": "Perfective future: написати→напишу, вивчити→вивчу, здати→здам"},
    ],
    "aspect-mastery": [
        {"setting": "Parent and child doing homework — choosing the right aspect: "
         "Ти написав (pf) домашнє завдання? Ні, я ще пишу (impf). "
         "Прочитай (pf) цей абзац. Я читаю (impf) вже годину!",
         "speakers": ["Мама/Тато", "Школяр (student)"],
         "motivation": "30 aspect pairs in homework context: писати/написати, читати/прочитати"},
    ],
    "motion-verbs": [
        {"setting": "Airport chaos — everyone going in different directions: "
         "Я іду (on foot) до виходу (m, gate). Він їде (by vehicle) в місто. "
         "Літак (m, plane) летить до Парижа. Ми пішли (left) о третій.",
         "speakers": ["Пасажири", "Друг (on phone)"],
         "motivation": "Motion verbs: іти/їхати/летіти with real travel situations"},
    ],
    "imperative-complete": [
        {"setting": "Ukrainian cooking class — the chef gives commands to students: "
         "Наріжте цибулю (f, onion)! Хай вода (f) закипить! "
         "Помішаймо разом! Нехай соус (m) настоїться!",
         "speakers": ["Шеф-кухар", "Учасники класу"],
         "motivation": "All imperative forms: наріжте (2pl), хай закипить (3sg), помішаймо (1pl)"},
    ],
    "telling-stories-and-travel": [
        {"setting": "Scenario 1: A funny thing happened at the вокзал (m, train station) yesterday. "
         "Scenario 2: Planning a trip to Карпати (pl) — booking хатинка (f, cabin). "
         "Scenario 3: Showing vacation photos from Одеса — пляж (m), море (n), ресторан (m).",
         "speakers": ["Друзі (sharing stories)"],
         "motivation": "Past + future + travel: вокзал(m), хатинка(f), пляж(m), море(n)"},
    ],
    "preferences-and-choices": [
        {"setting": "Debate at a book club — comparing two novels: "
         "Мені більше подобається цей роман (m, novel). На мою думку, авторка (f) пише краще. "
         "Я не згоден — ця повість (f, novella) цікавіша!",
         "speakers": ["Члени книжкового клубу"],
         "motivation": "Opinions: подобається, на мою думку, згоден/не згоден with роман(m), повість(f)"},
    ],
    "nature-and-traditions": [
        {"setting": "Ukrainian family preparing for Івана Купала — "
         "weaving вінок (m, wreath), jumping over вогнище (n, bonfire), "
         "searching for цвіт папороті (m, fern flower). "
         "Also: Різдво (n) — колядки (pl, carols), Великдень (m) — писанки (pl, Easter eggs).",
         "speakers": ["Родина", "Іноземний гість"],
         "motivation": "Traditions: вінок(m), вогнище(n), колядки(pl), писанки(pl)"},
    ],
    "education-and-work": [
        {"setting": "Career counseling session at a university — "
         "Що ви вивчаєте? Право (n, law). Ким хочете стати? Адвокатом (m, lawyer). "
         "Де хочете працювати? В юридичній фірмі (f, law firm).",
         "speakers": ["Консультант", "Студент"],
         "motivation": "Education + career: право(n), адвокат(m), фірма(f)"},
    ],
    "a2-finale": [
        {"setting": "Full day in Lviv — morning: arriving at вокзал (m), "
         "checking into готель (m, hotel). Day: Площа Ринок (f, main square), "
         "кав'ярня (f), книгарня (f, bookshop). Evening: зустріч з друзями (meeting friends), "
         "вечеря (f, dinner), обговорення планів на майбутнє.",
         "speakers": ["Турист", "Різні мешканці Львова"],
         "motivation": "Full A2 capstone: all cases, aspects, tenses in one day trip"},
    ],
}



def add_situations_to_plan(plan_path: Path, situations: list[dict], dry_run: bool = True) -> bool:
    """Add dialogue_situations to a plan file."""
    text = plan_path.read_text("utf-8")

    # Check if already has dialogue_situations
    if "dialogue_situations:" in text:
        print("  ⏭️  Already has dialogue_situations")
        return False

    # Check if plan has dialogue/conversation/scenario sections
    plan = yaml.safe_load(text)
    plan_text_lower = yaml.dump(plan).lower()
    has_dialogue = any(
        kw in plan_text_lower for kw in [
            "діалог", "dialogue", "розмов", "conversation",
            "сценарій", "scenario",
        ]
    )
    if not has_dialogue:
        print("  ⏭️  No dialogue/scenario section")
        return False

    # Build YAML block
    sits_yaml = yaml.dump(
        {"dialogue_situations": situations},
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).strip()

    # Insert before content_outline
    insert_point = text.find("content_outline:")
    if insert_point == -1:
        insert_point = text.find("activity_hints:")
    if insert_point == -1:
        print("  ❌ Can't find insertion point")
        return False

    new_text = text[:insert_point] + sits_yaml + "\n" + text[insert_point:]

    if dry_run:
        print(f"  📝 Would add {len(situations)} situation(s)")
        for s in situations:
            print(f"     → {s['setting']}")
    else:
        plan_path.write_text(new_text, "utf-8")
        print(f"  ✅ Added {len(situations)} situation(s)")

    return True


def main():
    parser = argparse.ArgumentParser(description="Add dialogue_situations to plans")
    parser.add_argument("--track", required=True, help="Track (e.g., a1)")
    parser.add_argument("--apply", action="store_true", help="Actually write to files (default: dry-run)")
    args = parser.parse_args()

    situations_map = {"a1": A1_SITUATIONS, "a2": A2_SITUATIONS}
    sits = situations_map.get(args.track)
    if not sits:
        print(f"No situations defined for {args.track} yet")
        return

    dry_run = not args.apply
    if dry_run:
        print("DRY RUN — use --apply to write changes\n")

    curr = yaml.safe_load((PROJECT_ROOT / "curriculum" / "l2-uk-en" / "curriculum.yaml").read_text())
    modules = curr["levels"][args.track]["modules"]
    plan_dir = PLANS_ROOT / args.track

    added = 0
    skipped = 0
    for i, slug in enumerate(modules, 1):
        plan_path = plan_dir / f"{slug}.yaml"
        if not plan_path.exists():
            continue
        print(f"M{i:02d} {slug}:")
        if slug in sits:
            if add_situations_to_plan(plan_path, sits[slug], dry_run):
                added += 1
            else:
                skipped += 1
        else:
            print("  ⏭️  No situations defined")
            skipped += 1

    print(f"\n{'DRY RUN — ' if dry_run else ''}Done: {added} added, {skipped} skipped")


if __name__ == "__main__":
    main()

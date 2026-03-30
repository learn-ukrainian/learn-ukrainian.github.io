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
        {"setting": "Moving into a dorm room — unpacking boxes and deciding where things go",
         "speakers": ["Марія (new roommate)", "Оленка (showing the room)"],
         "motivation": "Він/вона/воно test with real objects: стіл, лампа, ліжко"},
    ],
    "what-is-it-like": [
        {"setting": "Shopping for a birthday gift in a department store",
         "speakers": ["Оленка", "Тарас"],
         "motivation": "Який/яка/яке? to describe items, adjective agreement with real products"},
    ],
    "colors": [
        {"setting": "Choosing paint colors for redecorating a friend's apartment",
         "speakers": ["Наталка", "Дмитро"],
         "motivation": "Color adjectives + gender agreement: синя стіна, жовте вікно, білий стіл"},
        {"setting": "At an outdoor market choosing flowers for a gift",
         "speakers": ["Покупець (buyer)", "Продавець (seller)"],
         "motivation": "Colors in real shopping: червоні троянди, білі лілії"},
    ],
    "how-many": [
        {"setting": "At a farmers market — checking prices and counting change",
         "speakers": ["Покупець", "Продавець"],
         "motivation": "Скільки коштує? Numbers with гривень, counting items"},
        {"setting": "Planning a birthday party — counting guests, plates, chairs",
         "speakers": ["Ліза", "Максим"],
         "motivation": "Numbers 1-100 in practical planning context"},
    ],
    "this-and-that": [
        {"setting": "At a flea market — pointing at items on different tables",
         "speakers": ["Ірина", "Олег"],
         "motivation": "Цей/ця/це (close) vs той/та/те (far) with real distance"},
    ],
    "many-things": [
        {"setting": "Packing a suitcase for a school trip — listing what to bring",
         "speakers": ["Мама", "Петрик"],
         "motivation": "Singular → plural: одна книга → три книги, один зошит → зошити"},
    ],
    "checkpoint-my-world": [
        {"setting": "Showing a friend around your neighborhood on a walk",
         "speakers": ["Ваня", "Катя"],
         "motivation": "Consolidation: gender, adjectives, colors, numbers, demonstratives"},
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
        {"setting": "Proofreading a friend's Ukrainian essay — spotting у/в and і/й errors",
         "speakers": ["Студент (writing)", "Друг (correcting)"],
         "motivation": "У/в, і/й alternation in real written context"},
    ],
    "where-is-it": [
        {"setting": "First week in a new city — asking where everything is",
         "speakers": ["Новий мешканець (newcomer)", "Сусід (neighbor)"],
         "motivation": "В/на + locative: Де аптека? В аптеці. Де пошта? На пошті."},
    ],
    "my-city": [
        {"setting": "Drawing a map of your neighborhood for a pen pal letter",
         "speakers": ["Аліна (describing)", "Ігор (asking questions)"],
         "motivation": "City vocabulary + location: бібліотека тут, аптека там, біля парку"},
    ],
    "where-to": [
        {"setting": "Running errands together — splitting up and meeting later",
         "speakers": ["Оксана", "Степан"],
         "motivation": "Куди? + accusative: Я іду в банк, А я — на пошту"},
    ],
    "transport": [
        {"setting": "Explaining how to get from the airport to the hotel",
         "speakers": ["Приїжджий (visitor)", "Друг (local, giving directions)"],
         "motivation": "Transport: автобусом, потягом, на метро in real route"},
    ],
    "around-the-city": [
        {"setting": "A walking tour guide showing a small group around the old town",
         "speakers": ["Гід (guide)", "Туристи"],
         "motivation": "Де?/Куди? combined: Ми зараз на площі, Далі підемо в музей"},
    ],
    "where-from": [
        {"setting": "International student mixer — everyone sharing where they're from",
         "speakers": ["Кілька студентів (group)"],
         "motivation": "Звідки? + з + genitive: Я з Канади, Вона з Японії"},
    ],
    "checkpoint-places": [
        {"setting": "Giving a video tour of your city to an online friend",
         "speakers": ["Мешканець (resident, filming)", "Онлайн-друг (watching, asking)"],
         "motivation": "Consolidation: where/where-to/where-from + city vocab + transport"},
    ],
    "food-and-drink": [
        {"setting": "Cooking traditional borshch together — listing ingredients",
         "speakers": ["Бабуся (teaching)", "Онук/Онучка (learning)"],
         "motivation": "Food vocabulary in recipe context: буряк, картопля, м'ясо"},
    ],
    "i-eat-i-drink": [
        {"setting": "Lunch break at work — sharing food and talking about what you eat",
         "speakers": ["Колега 1", "Колега 2"],
         "motivation": "Accusative: Я їм хліб, п'ю каву — real mealtime exchange"},
    ],
    "at-the-cafe": [
        {"setting": "A date at a cozy Lviv café — ordering and chatting",
         "speakers": ["Ростик", "Іванка"],
         "motivation": "Мені, будь ласка + ordering vocabulary in romantic context"},
    ],
    "shopping": [
        {"setting": "At a Ukrainian supermarket — comparing prices and reading labels",
         "speakers": ["Мама", "Дочка/Син"],
         "motivation": "Скільки коштує? Гривень in real grocery shopping"},
    ],
    "people-around-me": [
        {"setting": "Showing wedding photos — identifying people in each picture",
         "speakers": ["Наречена/Наречений", "Друг"],
         "motivation": "Accusative animate: Бачиш маму? Знаєш Олену? Це мій дядько."},
    ],
    "checkpoint-food-shopping": [
        {"setting": "Hosting a dinner party — shopping, cooking, and serving guests",
         "speakers": ["Господар/Господиня (host)", "Гості (guests)"],
         "motivation": "Consolidation: food, ordering, prices, accusative"},
    ],
    "hey-friend": [
        {"setting": "At a busy birthday party — calling people across the room",
         "speakers": ["Іменинник (birthday person)", "Друзі"],
         "motivation": "Vocative: Олено! Тарасе! Друже! Мамо! in noisy social setting"},
    ],
    "please-do-this": [
        {"setting": "Moving furniture in a new apartment — giving each other instructions",
         "speakers": ["Олег", "Наталя"],
         "motivation": "Imperative: Постав тут! Підніми! Поклади туди! in physical task"},
    ],
    "linking-ideas": [
        {"setting": "Debating where to go on vacation — comparing options",
         "speakers": ["Подружжя (couple)"],
         "motivation": "І, а, але, бо: Гори гарні, але далеко. Море тепле, бо літо."},
    ],
    "when-and-where": [
        {"setting": "Explaining to a friend how to find your apartment building",
         "speakers": ["Господар (host, on phone)", "Гість (lost outside)"],
         "motivation": "Complex sentences: Коли побачиш аптеку, поверни ліворуч"},
    ],
    "holidays": [
        {"setting": "Ukrainian Christmas Eve dinner — explaining traditions to a foreign guest",
         "speakers": ["Українська родина", "Іноземний гість"],
         "motivation": "Holiday vocabulary + З Різдвом! greetings in cultural context"},
    ],
    "checkpoint-communication": [
        {"setting": "Organizing a charity event — delegating tasks and coordinating",
         "speakers": ["Організатор", "Волонтери"],
         "motivation": "Consolidation: vocative, imperative, conjunctions, complex sentences"},
    ],
    "what-happened": [
        {"setting": "Monday morning at work — colleagues sharing weekend stories",
         "speakers": ["Колеги (coworkers)"],
         "motivation": "Past tense: Що ти робив? Я ходив у кіно. А ти? Я читала."},
    ],
    "yesterday": [
        {"setting": "Police report — describing what happened step by step",
         "speakers": ["Свідок (witness)", "Поліцейський"],
         "motivation": "Past tense narration: Спочатку я побачив, потім почув, нарешті зателефонував"},
    ],
    "what-will-happen": [
        {"setting": "Fortune teller at a fun fair — predicting the future playfully",
         "speakers": ["Ворожка (fortune teller)", "Клієнт"],
         "motivation": "Future tense: Ти будеш подорожувати, Будеш жити довго"},
    ],
    "my-plans": [
        {"setting": "Friends coordinating schedules for the coming week via messaging",
         "speakers": ["Група друзів (3 people)"],
         "motivation": "Future + days: У суботу буду... Може, зустрінемося? Ходімо!"},
    ],
    "my-story": [
        {"setting": "Grandparent telling their life story to grandchildren",
         "speakers": ["Дідусь/Бабуся", "Онуки"],
         "motivation": "Three tenses: Я народився в селі, Зараз живу в місті, Буду відпочивати"},
    ],
    "health": [
        {"setting": "At the doctor's office — describing symptoms",
         "speakers": ["Пацієнт", "Лікар"],
         "motivation": "У мене болить голова / горло / живіт — body parts in medical context"},
    ],
    "emergencies": [
        {"setting": "A minor car accident — calling for help and explaining the situation",
         "speakers": ["Водій (driver)", "Оператор 103 (emergency)"],
         "motivation": "Emergency imperatives: Допоможіть! Викличте швидку! Location phrases"},
    ],
    "a1-finale": [
        {"setting": "Full day in Kyiv — from hotel checkout to evening train departure",
         "speakers": ["Турист (spending final day)", "Various locals"],
         "motivation": "Everything: greetings, directions, ordering, shopping, past/future tense"},
    ],
}


def add_situations_to_plan(plan_path: Path, situations: list[dict], dry_run: bool = True) -> bool:
    """Add dialogue_situations to a plan file."""
    text = plan_path.read_text("utf-8")

    # Check if already has dialogue_situations
    if "dialogue_situations:" in text:
        print("  ⏭️  Already has dialogue_situations")
        return False

    # Check if plan has a Діалоги section
    plan = yaml.safe_load(text)
    has_dialogue = any(
        "Діалоги" in s.get("section", "") or "Dialogue" in s.get("section", "")
        for s in plan.get("content_outline", [])
    )
    if not has_dialogue:
        print("  ⏭️  No Діалоги section")
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

    situations_map = {"a1": A1_SITUATIONS}
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

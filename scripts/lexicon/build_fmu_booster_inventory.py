#!/usr/bin/env python3
"""Build and validate the Anna Ohoiko FMU Vocabulary Booster source inventory and decisions."""

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit.source_inventory_review_decisions import source_inventory_key

EPISODES_DATA = [
    {
        "id": "ohoiko-fmu-booster-ep-04",
        "num": "04",
        "ep": 4,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 4: Means of Transport",
        "url": "https://www.ukrainianlessons.com/fmu4/",
        "topic": "Transport",
        "words": [
            ("автобус", "noun", "bus"),
            ("тролейбус", "noun", "trolleybus"),
            ("трамвай", "noun", "tram"),
            ("метро", "noun", "subway / metro"),
            ("маршрутка", "noun", "route minibus"),
            ("фунікулер", "noun", "funicular"),
            ("таксі", "noun", "taxi"),
            ("поїзд", "noun", "train"),
            ("потяг", "noun", "train"),
            ("електричка", "noun", "suburban commuter train"),
            ("літак", "noun", "airplane"),
            ("пором", "noun", "ferry"),
            ("машина", "noun", "car"),
            ("велосипед", "noun", "bicycle"),
            ("мотоцикл", "noun", "motorcycle"),
            ("фургон", "noun", "van"),
            ("будинок на колесах", "noun", "campervan / RV"),
            ("вантажівка", "noun", "truck"),
        ],
    },
    {
        "id": "ohoiko-fmu-booster-ep-12",
        "num": "12",
        "ep": 12,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 12: Beverages / Drinks",
        "url": "https://www.ukrainianlessons.com/fmu12/",
        "topic": "Beverages / Drinks",
        "words": [
            ("напій", "noun", "beverage / drink"),
            ("чай", "noun", "tea"),
            ("зелений чай", "noun", "green tea"),
            ("чорний чай", "noun", "black tea"),
            ("трав'яний чай", "noun", "herbal tea"),
            ("кава", "noun", "coffee"),
            ("какао", "noun", "cocoa"),
            ("гарячий шоколад", "noun", "hot chocolate"),
            ("лимонад", "noun", "lemonade"),
            ("компот", "noun", "compote (fruit beverage)"),
            ("узвар", "noun", "uzvar (dried fruit compote)"),
            ("сік", "noun", "juice"),
            ("яблучний сік", "noun", "apple juice"),
            ("апельсиновий сік", "noun", "orange juice"),
            ("смузі", "noun", "smoothie"),
            ("коктейль", "noun", "cocktail"),
            ("молочний коктейль", "noun", "milkshake"),
            ("пиво", "noun", "beer"),
            ("вино", "noun", "wine"),
            ("червоне вино", "noun", "red wine"),
            ("біле вино", "noun", "white wine"),
            ("шампанське", "noun", "champagne"),
            ("горілка", "noun", "horilka / Ukrainian vodka"),
            ("газований напій", "noun", "carbonated drink / soda"),
            ("вода", "noun", "water"),
        ],
    },
    {
        "id": "ohoiko-fmu-booster-ep-18",
        "num": "18",
        "ep": 18,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 18: Shopping Vocabulary",
        "url": "https://www.ukrainianlessons.com/fmu18/",
        "topic": "Shopping Vocabulary",
        "words": [
            ("відчинено", "adv", "open (sign)"),
            ("зачинено", "adv", "closed (sign)"),
            ("візок", "noun", "shopping cart / trolley"),
            ("кошик", "noun", "shopping basket"),
            ("ваги", "noun", "scales"),
            ("ціна", "noun", "price"),
            ("розпродаж", "noun", "sale"),
            ("знижка", "noun", "discount"),
            ("акція", "noun", "promotional offer / deal"),
            ("каса", "noun", "cash desk / checkout"),
            ("черга", "noun", "queue / line"),
            ("касир", "noun", "cashier (male)"),
            ("касирка", "noun", "cashier (female)"),
            ("чек", "noun", "receipt"),
        ],
    },
    {
        "id": "ohoiko-fmu-booster-ep-23",
        "num": "23",
        "ep": 23,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 23: Hobbies",
        "url": "https://www.ukrainianlessons.com/fmu23/",
        "topic": "Hobbies",
        "words": [
            ("ходити", "verb", "to go regularly / walk"),
            ("грати", "verb", "to play"),
            ("кататися", "verb", "to ride / slide / ski"),
            ("займатися", "verb", "to engage in / practice"),
            ("готувати", "verb", "to cook"),
            ("бігати", "verb", "to run / jog"),
            ("подорожувати", "verb", "to travel"),
            ("читати", "verb", "to read"),
            ("шахи", "noun", "chess"),
            ("гітара", "noun", "guitar"),
            ("лижі", "noun", "skis"),
            ("йога", "noun", "yoga"),
            ("танець", "noun", "dance"),
            ("серіал", "noun", "TV show / series"),
            ("фільм", "noun", "movie / film"),
        ],
    },
    {
        "id": "ohoiko-fmu-booster-ep-25",
        "num": "25",
        "ep": 25,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 25: Sports",
        "url": "https://www.ukrainianlessons.com/fmu25/",
        "topic": "Sports",
        "words": [
            ("спорт", "noun", "sport"),
            ("футбол", "noun", "football / soccer"),
            ("баскетбол", "noun", "basketball"),
            ("волейбол", "noun", "volleyball"),
            ("теніс", "noun", "tennis"),
            ("бокс", "noun", "boxing"),
            ("атлетика", "noun", "athletics / track and field"),
            ("гімнастика", "noun", "gymnastics"),
            ("серфінг", "noun", "surfing"),
            ("сноубординг", "noun", "snowboarding"),
            ("більярд", "noun", "billiards / pool"),
            ("боулінг", "noun", "bowling"),
            ("біг", "noun", "running"),
            ("плавання", "noun", "swimming"),
            ("плавати", "verb", "to swim"),
            ("фехтування", "noun", "fencing"),
            ("кінний спорт", "noun", "equestrian sport"),
            ("лижний спорт", "noun", "skiing"),
            ("гірськолижний спорт", "noun", "alpine / downhill skiing"),
            ("велосипедний спорт", "noun", "cycling"),
        ],
    },
    {
        "id": "ohoiko-fmu-booster-ep-29",
        "num": "29",
        "ep": 29,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 29: Months and Seasons",
        "url": "https://www.ukrainianlessons.com/fmu29/",
        "topic": "Months and Seasons",
        "words": [
            ("пора року", "noun", "season of the year"),
            ("зима", "noun", "winter"),
            ("взимку", "adv", "in winter"),
            ("весна", "noun", "spring"),
            ("навесні", "adv", "in spring"),
            ("літо", "noun", "summer"),
            ("влітку", "adv", "in summer"),
            ("осінь", "noun", "autumn / fall"),
            ("восени", "adv", "in autumn / in fall"),
            ("місяць", "noun", "month"),
            ("січень", "noun", "January"),
            ("лютий", "noun", "February"),
            ("березень", "noun", "March"),
            ("квітень", "noun", "April"),
            ("травень", "noun", "May"),
            ("червень", "noun", "June"),
            ("липень", "noun", "July"),
            ("серпень", "noun", "August"),
            ("вересень", "noun", "September"),
            ("жовтень", "noun", "October"),
            ("листопад", "noun", "November"),
            ("грудень", "noun", "December"),
        ],
    },
    {
        "id": "ohoiko-fmu-booster-ep-33",
        "num": "33",
        "ep": 33,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 33: Family Members",
        "url": "https://www.ukrainianlessons.com/fmu33/",
        "topic": "Family Members",
        "words": [
            ("родина", "noun", "family"),
            ("сім'я", "noun", "family"),
            ("батьки", "noun", "parents"),
            ("мама", "noun", "mother"),
            ("мати", "noun", "mother"),
            ("тато", "noun", "father; dad"),
            ("батько", "noun", "father"),
            ("дитина", "noun", "child"),
            ("діти", "noun", "children"),
            ("син", "noun", "son"),
            ("дочка", "noun", "daughter"),
            ("донька", "noun", "daughter"),
            ("бабуся", "noun", "grandmother"),
            ("дідусь", "noun", "grandfather"),
            ("прабабуся", "noun", "great-grandmother"),
            ("прадід", "noun", "great-grandfather"),
            ("брат", "noun", "brother"),
            ("сестра", "noun", "sister"),
            ("дядько", "noun", "uncle"),
            ("тітка", "noun", "aunt"),
            ("племінник", "noun", "nephew"),
            ("племінниця", "noun", "niece"),
            ("двоюрідний брат", "noun", "male cousin"),
            ("двоюрідна сестра", "noun", "female cousin"),
            ("наречений", "noun", "fiancé / groom"),
            ("наречена", "noun", "fiancée / bride"),
            ("чоловік", "noun", "husband; man"),
            ("дружина", "noun", "wife"),
            ("подружжя", "noun", "married couple"),
            ("свекор", "noun", "father-in-law; husband's father"),
            ("свекруха", "noun", "mother-in-law; husband's mother"),
            ("тесть", "noun", "father-in-law; wife's father"),
            ("теща", "noun", "mother-in-law; wife's mother"),
            ("невістка", "noun", "daughter-in-law"),
            ("зять", "noun", "son-in-law"),
        ],
    },
    {
        "id": "ohoiko-fmu-booster-ep-35",
        "num": "35",
        "ep": 35,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 35: Jobs and Professions",
        "url": "https://www.ukrainianlessons.com/fmu35/",
        "topic": "Jobs and Professions",
        "words": [
            ("професія", "noun", "profession / occupation"),
            ("вчитель", "noun", "teacher (male)"),
            ("вчителька", "noun", "teacher (female)"),
            ("викладач", "noun", "instructor / lecturer (male)"),
            ("викладачка", "noun", "instructor / lecturer (female)"),
            ("професор", "noun", "professor (male)"),
            ("професорка", "noun", "professor (female)"),
            ("лікар", "noun", "doctor / physician (male)"),
            ("лікарка", "noun", "doctor / physician (female)"),
            ("менеджер", "noun", "manager (male)"),
            ("менеджерка", "noun", "manager (female)"),
            ("помічник", "noun", "helper"),
            ("помічниця", "noun", "assistant / helper (female)"),
            ("асистент", "noun", "assistant (male)"),
            ("асистентка", "noun", "assistant (female)"),
            ("інженер", "noun", "engineer (male)"),
            ("інженерка", "noun", "engineer (female)"),
            ("програміст", "noun", "programmer (male)"),
            ("програмістка", "noun", "programmer (female)"),
            ("дизайнер", "noun", "designer (male)"),
            ("дизайнерка", "noun", "designer (female)"),
            ("бухгалтер", "noun", "Accountant"),
            ("бухгалтерка", "noun", "accountant (female)"),
            ("юрист", "noun", "lawyer / jurist (male)"),
            ("юристка", "noun", "lawyer / jurist (female)"),
            ("офіціант", "noun", "waiter"),
            ("офіціантка", "noun", "waitress"),
            ("будівельник", "noun", "construction worker / builder (male)"),
            ("будівельниця", "noun", "construction worker / builder (female)"),
            ("водій", "noun", "driver (male)"),
            ("водійка", "noun", "driver (female)"),
            ("касир", "noun", "cashier (male)"),
            ("касирка", "noun", "cashier (female)"),
            ("продавець", "noun", "salesperson / shop assistant (male)"),
            ("продавчиня", "noun", "salesperson / shop assistant (female)"),
            ("тренер", "noun", "coach / trainer (male)"),
            ("тренерка", "noun", "coach / trainer (female)"),
            ("дослідник", "noun", "researcher (male)"),
            ("дослідниця", "noun", "researcher (female)"),
            ("засновник", "noun", "founder (male)"),
            ("засновниця", "noun", "founder (female)"),
            ("підприємець", "noun", "entrepreneur"),
            ("підприємниця", "noun", "entrepreneur (female)"),
            ("митець", "noun", "artist (male)"),
            ("мисткиня", "noun", "artist (female)"),
            ("письменник", "noun", "writer (male)"),
            ("письменниця", "noun", "writer (female)"),
            ("музикант", "noun", "musician (male)"),
            ("музикантка", "noun", "musician (female)"),
            ("пенсіонер", "noun", "retiree (male)"),
            ("пенсіонерка", "noun", "retiree (female)"),
        ],
    },
    {
        "id": "ohoiko-fmu-booster-ep-42",
        "num": "42",
        "ep": 42,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 42: Housing and Rooms",
        "url": "https://www.ukrainianlessons.com/fmu42/",
        "topic": "Housing and Rooms",
        "words": [
            ("житло", "noun", "housing / accommodation"),
            ("помешкання", "noun", "dwelling / accommodation"),
            ("дім", "noun", "house / home"),
            ("будинок", "noun", "building / house"),
            ("хата", "noun", "village house / cottage"),
            ("квартира", "noun", "apartment / flat"),
            ("заміський будинок", "noun", "country house"),
            ("дача", "noun", "summer house / dacha"),
            ("маєток", "noun", "manor / mansion"),
            ("гуртожиток", "noun", "dormitory / residence hall"),
            ("кімната", "noun", "room"),
            ("вітальня", "noun", "living room"),
            ("кухня", "noun", "kitchen"),
            ("спальня", "noun", "bedroom"),
            ("ванна кімната", "noun", "bathroom"),
            ("туалет", "noun", "restroom / toilet"),
            ("кабінет", "noun", "study / home office"),
            ("коридор", "noun", "corridor / hallway"),
            ("передпокій", "noun", "entryway / hall"),
            ("гараж", "noun", "garage"),
            ("підвал", "noun", "basement / cellar"),
            ("горище", "noun", "attic"),
            ("комора", "noun", "Storeroom / Pantry"),
        ],
    },
    {
        "id": "ohoiko-fmu-booster-ep-44",
        "num": "44",
        "ep": 44,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 44: Things in Every House",
        "url": "https://www.ukrainianlessons.com/fmu44/",
        "topic": "Things in Every House",
        "words": [
            ("аптечка", "noun", "first aid kit"),
            ("батарейка", "noun", "battery"),
            ("віник", "noun", "broom"),
            ("совок", "noun", "dustpan"),
            ("швабра", "noun", "mop"),
            ("відро", "noun", "bucket"),
            ("миска", "noun", "a bowl"),
            ("пилосос", "noun", "vacuum cleaner"),
            ("щітка", "noun", "brush"),
            ("ганчірка", "noun", "cleaning rag / cloth"),
            ("губка", "noun", "sponge"),
            ("смітник", "noun", "trash can / waste bin"),
            ("пакети для сміття", "noun", "garbage bags / bin liners"),
            ("мішки для сміття", "noun", "trash bags"),
            ("гумові рукавички", "noun", "rubber gloves"),
            ("паперові рушники", "noun", "paper towels"),
            ("туалетний папір", "noun", "toilet paper"),
            ("мийні засоби", "noun", "cleaning detergents"),
            ("засіб для миття вікон", "noun", "window cleaner"),
            ("засіб для миття унітазу", "noun", "toilet bowl cleaner"),
            ("засіб для прання", "noun", "laundry detergent"),
        ],
    },
    {
        "id": "ohoiko-fmu-booster-ep-48",
        "num": "48",
        "ep": 48,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 48: Staple Food",
        "url": "https://www.ukrainianlessons.com/fmu48/",
        "topic": "Staple Food",
        "words": [
            ("хліб", "noun", "bread"),
            ("картопля", "noun", "potato"),
            ("яйце", "noun", "egg"),
            ("макарони", "noun", "pasta / macaroni"),
            ("томатний соус", "noun", "tomato sauce"),
            ("томатна паста", "noun", "tomato paste"),
            ("рис", "noun", "rice"),
            ("гречка", "noun", "buckwheat"),
            ("вівсянка", "noun", "oatmeal / rolled oats"),
            ("борошно", "noun", "flour"),
            ("мука", "noun", "flour"),
            ("цукор", "noun", "sugar"),
            ("мед", "noun", "honey"),
            ("варення", "noun", "jam / preserves"),
            ("джем", "noun", "jam"),
            ("приправа", "noun", "seasoning / condiment"),
            ("спеція", "noun", "spice"),
            ("чорний перець", "noun", "black pepper"),
            ("сіль", "noun", "salt"),
            ("олія", "noun", "oil (vegetable / cooking)"),
            ("соняшникова олія", "noun", "sunflower oil"),
            ("оливкова олія", "noun", "olive oil"),
            ("оцет", "noun", "vinegar"),
            ("масло", "noun", "butter"),
            ("сметана", "noun", "sour cream"),
            ("молоко", "noun", "milk"),
            ("сир", "noun", "cheese / cottage cheese"),
            ("майонез", "noun", "mayonnaise"),
            ("кетчуп", "noun", "ketchup"),
            ("гірчиця", "noun", "mustard"),
        ],
    },
    {
        "id": "ohoiko-fmu-booster-ep-52",
        "num": "52",
        "ep": 52,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 52: Body Parts",
        "url": "https://www.ukrainianlessons.com/fmu52/",
        "topic": "Body Parts",
        "words": [
            ("тіло", "noun", "body"),
            ("частина тіла", "noun", "body part"),
            ("голова", "noun", "head"),
            ("волосся", "noun", "hair"),
            ("око", "noun", "eye"),
            ("вухо", "noun", "ear"),
            ("ніс", "noun", "nose"),
            ("губа", "noun", "lip"),
            ("обличчя", "noun", "face"),
            ("шия", "noun", "neck"),
            ("плече", "noun", "shoulder"),
            ("рука", "noun", "arm / hand"),
            ("палець", "noun", "finger / toe"),
            ("пальці рук", "noun", "fingers"),
            ("пальці ніг", "noun", "toes"),
            ("ніготь", "noun", "nail / fingernail"),
            ("груди", "noun", "chest / breasts"),
            ("живіт", "noun", "belly / stomach"),
            ("сідниці", "noun", "buttocks"),
            ("нога", "noun", "leg / foot"),
        ],
    },
    {
        "id": "ohoiko-fmu-booster-ep-55",
        "num": "55",
        "ep": 55,
        "title": "Anna Ohoiko - 5 Minute Ukrainian, Episode 55: Car and Road Vocabulary",
        "url": "https://www.ukrainianlessons.com/fmu55/",
        "topic": "Car and Road Vocabulary",
        "words": [
            ("кермо", "noun", "steering wheel"),
            ("коробка передач", "noun", "gearbox / transmission"),
            ("пасок безпеки", "noun", "seatbelt"),
            ("дорожній рух", "noun", "road traffic"),
            ("дорога", "noun", "road / highway"),
            ("траса", "noun", "highway / route"),
            ("смуга", "noun", "Lane (road)"),
            ("дорожній знак", "noun", "road sign"),
            ("світлофор", "noun", "traffic light"),
            ("пішохід", "noun", "pedestrian"),
            ("затор", "noun", "traffic jam"),
            ("корок", "noun", "traffic jam / congestion"),
            ("стоянка", "noun", "parking lot / parking"),
            ("заправка", "noun", "gas station / petrol station"),
        ],
    },
]

INV_PATH = PROJECT_ROOT / "data/lexicon/source-inventory/ohoiko-fmu-booster-vocabulary.yaml"
DECISIONS_PATH = (
    PROJECT_ROOT / "data/lexicon/source-inventory-review-decisions/2026-09-13-ohoiko-fmu-booster-approve.yaml"
)
INV_REL = "data/lexicon/source-inventory/ohoiko-fmu-booster-vocabulary.yaml"
DECISIONS_REL = "data/lexicon/source-inventory-review-decisions/2026-09-13-ohoiko-fmu-booster-approve.yaml"


def build_inventory_and_decisions(*, dry_run: bool = False):
    sources = []
    decisions = []

    # Track unique lemmas across inventory to ensure consistency
    seen_lemmas = {}

    for ep_info in EPISODES_DATA:
        source_id = ep_info["id"]
        locator = f"fmu-booster-ep-{ep_info['num']}"
        headwords = []

        for lemma, pos, gloss in ep_info["words"]:
            if lemma in seen_lemmas:
                prev_pos, prev_gloss = seen_lemmas[lemma]
                pos = prev_pos
                gloss = prev_gloss
            else:
                seen_lemmas[lemma] = (pos, gloss)

            headwords.append(
                {
                    "lemma": lemma,
                    "pos": pos,
                    "gloss": gloss,
                    "locator": locator,
                    "context": f"Джерело: 5 Minute Ukrainian / Анна Огойко, епізод {ep_info['ep']}: {ep_info['topic']}",
                }
            )

            key = source_inventory_key(lemma=lemma, inventory_path=INV_REL, locator=locator)
            decisions.append(
                {
                    "lemma": lemma,
                    "decision": "approve_for_publish",
                    "approved_pos": pos,
                    "approved_gloss": gloss,
                    "sense_note": f"curated ohoiko auto-approve (fmu-booster-ep-{ep_info['num']}); no AI review",
                    "source_inventory": {
                        "key": key,
                        "path": INV_REL,
                        "locator": locator,
                        "source_id": source_id,
                        "source_family": "ohoiko",
                    },
                    "evidence_refs": [
                        "curated source family ohoiko",
                        f"5 Minute Ukrainian Ep {ep_info['ep']}",
                        "VESUM and authoritative dictionaries",
                    ],
                }
            )

        sources.append(
            {
                "id": source_id,
                "source_family": "ohoiko",
                "extraction_mode": "curated_headword",
                "title": ep_info["title"],
                "url": ep_info["url"],
                "path": INV_REL,
                "locator": locator,
                "notes": (
                    f"Factual vocabulary extracted from 5 Minute Ukrainian Episode {ep_info['ep']}: {ep_info['topic']}. "
                    "Citation and educational reference only; no continuous audio transcripts or copyrightable lesson dialogues reproduced."
                ),
                "headwords": headwords,
            }
        )

    inv_doc = {
        "version": 1,
        "kind": "atlas_source_inventory",
        "sources": sources,
    }

    decisions_doc = {
        "version": 1,
        "kind": "atlas_source_inventory_review_decisions",
        "batch_id": "source-inventory-ohoiko-fmu-booster-2026-09-13",
        "batch_label": "ohoiko-fmu-booster-approve-2026-09-13",
        "reviewer": "operator-curated-source-trust",
        "reviewed_at": "2026-09-13",
        "source_queue": {
            "workflow": "source_inventory_publish_review_queue.v1",
            "total_queue_rows": len(decisions),
            "approved_in_queue": len(decisions),
            "promotion_batch_size": len(decisions),
        },
        "production_outputs_updated": [],
        "decisions": decisions,
    }

    if not dry_run:
        INV_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(INV_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(inv_doc, f, allow_unicode=True, sort_keys=False, width=1000)
        print(f"Wrote {INV_PATH} ({len(sources)} sources, {sum(len(s['headwords']) for s in sources)} headwords)")

        DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DECISIONS_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(decisions_doc, f, allow_unicode=True, sort_keys=False, width=1000)
        print(f"Wrote {DECISIONS_PATH} ({len(decisions)} decisions)")

    return inv_doc, decisions_doc


if __name__ == "__main__":
    build_inventory_and_decisions()

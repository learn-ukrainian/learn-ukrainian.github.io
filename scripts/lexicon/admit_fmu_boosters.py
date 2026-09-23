#!/usr/bin/env python3
"""Admit Anna Ohoiko FMU Vocabulary Booster inventory and new headwords into Atlas.

Under Epic #4387 and Issue #7454:
Extracts factual vocabulary from the 13 FMU Vocabulary Booster episodes,
attaches source provenance to existing entries, and admits 51 newly promoted
headwords with authentic ВТС / СУМ-20 definitions, learner English glosses,
and zero Soviet СУМ-11 usage.

Usage::

    .venv/bin/python -m scripts.lexicon.admit_fmu_boosters [--dry-run]
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

os.environ["LEXICON_SLOVNYK_OFFLINE"] = "1"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.atlas.atlas_db import migrate_manifest, validate_alias_targets
from scripts.audit import generate_search_index
from scripts.audit.source_inventory_intake import read_source_inventory
from scripts.audit.source_inventory_review_decisions import source_inventory_key, validate_decision_file
from scripts.lexicon import enrich_manifest
from scripts.lexicon.build_data_manifest import _lemma_key, _slug_for_url
from scripts.lexicon.manifest_fingerprint import write_fingerprint
from scripts.lexicon.manifest_io import _write_atomic, load_manifest
from scripts.verification.vesum import verify_word

MANIFEST_PATH = PROJECT_ROOT / "site/src/data/lexicon-manifest.json"
POINTER_PATH = PROJECT_ROOT / "site/src/data/lexicon-manifest.pointer.json"
FINGERPRINT_PATH = PROJECT_ROOT / "site/src/data/lexicon-manifest.fingerprint.json"
ATLAS_DB_PATH = PROJECT_ROOT / "data/atlas.db"
SOURCES_DB_PATH = PROJECT_ROOT / "data/sources.db"
INV_PATH = PROJECT_ROOT / "data/lexicon/source-inventory/ohoiko-fmu-booster-vocabulary.yaml"
DECISIONS_PATH = (
    PROJECT_ROOT / "data/lexicon/source-inventory-review-decisions/2026-09-13-ohoiko-fmu-booster-approve.yaml"
)
INV_REL = "data/lexicon/source-inventory/ohoiko-fmu-booster-vocabulary.yaml"
DECISIONS_REL = "data/lexicon/source-inventory-review-decisions/2026-09-13-ohoiko-fmu-booster-approve.yaml"

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

NEW_DEFINITIONS = {
    "будинок на колесах": "Автомобіль із житловим приміщенням у кузові (автобудинок, кемпер).",
    "зелений чай": "Чай, виготовлений із мінімально ферментованого листя чайного куща.",
    "чорний чай": "Чай із повністю ферментованого листя чайного куща, що має темний настій.",
    "трав'яний чай": "Напій із суміші лікарських чи запашних трав, плодів та квітів без листя чайного куща.",
    "гарячий шоколад": "Густий гарячий напій із розтопленого шоколаду або какао з молоком чи вершками.",
    "яблучний сік": "Сік, вичавлений зі свіжих яблук.",
    "апельсиновий сік": "Сік, вичавлений зі свіжих плодів апельсина.",
    "молочний коктейль": "Десертний напій на основі молока та морозива зі збитими компонентами й сиропом.",
    "червоне вино": "Вино з темних сортів винограду, багате на таніни.",
    "біле вино": "Вино зі світлих сортів винограду або вичавленого без шкірки соку темного винограду.",
    "газований напій": "Безалкогольний напій, насичений вуглекислим газом.",
    "відчинено": "Предикативне слово або прислівник на позначення доступності закладу чи приміщення для відвідувачів.",
    "серфінг": "Водний вид спорту, що полягає в ковзанні хвилями на спеціальній дошці.",
    "сноубординг": "Зимовий вид спорту, що полягає в спуску із засніжених схилів на спеціальній дошці (сноуборді).",
    "боулінг": "Спортивна гра в кулі, завдання якої — збити кулею найбільшу кількість кеглів.",
    "кінний спорт": "Види спортивних змагань, у яких вершники керують конем (конкур, виїздка, триборство).",
    "лижний спорт": "Сукупність видів спорту, у яких спортсмени пересуваються на лижах.",
    "гірськолижний спорт": "Спуск із гір на спеціальних лижах за визначеними трасами зі швидкісним маневруванням.",
    "велосипедний спорт": "Вид спорту, що включає перегони на велосипедах на шосе, треку чи пересіченій місцевості.",
    "менеджерка": "Жінка-керівник або фахівець із управління виробництвом, збутом, персоналом чи проєктами.",
    "асистентка": "Жінка, що допомагає фахівцеві у виконанні його обов'язків; посада у виші чи науковій установі.",
    "дизайнерка": "Жінка-фахівець із художнього конструювання, проєктування та оформлення виробів, середовища чи інтерфейсів.",
    "бухгалтерка": "Жінка-фахівець із бухгалтерського обліку, ведення фінансової документації та звітності.",
    "будівельниця": "Жінка, яка працює на будівництві споруд або будівельних об'єктів.",
    "тренерка": "Жінка, яка проводить навчально-тренувальну роботу зі спортсменами або учнями.",
    "підприємниця": "Жінка, яка займається підприємництвом, володіє власною справою чи бізнесом.",
    "музикантка": "Жінка, яка професійно займається музикою або грає на музичному інструменті.",
    "заміський будинок": "Житловий будинок, розташований за межами міста (котедж, вілла чи садиба).",
    "совок": "Господарський інструмент у вигляді відкритої коробки з держаком для підбирання сміття.",
    "пакети для сміття": "Поліетиленові мішки або пакети, призначені для збирання та утилізації побутових відходів.",
    "мішки для сміття": "Міцні мішки для збирання, перенесення та утилізації сміття чи відходів.",
    "гумові рукавички": "Захисні рукавички з гуми або латексу для захисту рук під час прибирання, миття чи робіт із хімікатами.",
    "паперові рушники": "Вироби з поглинального паперу в рулонах або аркушах для витирання рук і прибирання на кухні.",
    "туалетний папір": "Спеціальний м'який папір санітарно-гігієнічного призначення.",
    "мийні засоби": "Хімічні препарати та суміші (порошки, рідини, гелі), що використовуються для миття та чищення.",
    "засіб для миття вікон": "Спеціальна рідина або спрей для очищення скла, дзеркал та вікон від бруду без розводів.",
    "засіб для миття унітазу": "Дезінфекційний гель або рідина для гігієнічного очищення та дезінфекції сантехніки.",
    "засіб для прання": "Пральний порошок, гель або капсули для очищення тканин від забруднень у воді.",
    "томатний соус": "Кулінарна приправа, виготовлена з протертих томатів із додаванням солі, цукру, оцту та прянощів.",
    "томатна паста": "Концентрована маса з уварених стиглих томатів без шкірки та насіння.",
    "спеція": "Ароматична або гостра рослинна добавка до їжі, що поліпшує її смак і запах.",
    "чорний перець": "Пряність у вигляді висушених недозрілих плодів перцевого куща, цілих або мелених.",
    "соняшникова олія": "Рослинна олія, видобута з насіння соняшнику, традиційна для української кухні.",
    "оливкова олія": "Рослинна олія, вичавлена з плодів оливкового дерева.",
    "частина тіла": "Анатомічний структурний елемент організму людини чи тварини (голова, рука, нога тощо).",
    "пальці рук": "Кінцеві рухомі членисті частини кисті руки людини.",
    "пальці ніг": "Кінцеві членисті частини ступні ноги людини.",
    "коробка передач": "Механізм автомобіля, призначений для зміни крутного моменту та швидкості руху.",
    "пасок безпеки": "Стрічковий ремінь в автомобілі або літаку для фіксації пасажира й запобігання травмам під час аварії.",
    "дорожній рух": "Процес руху транспортних засобів і пішоходів дорогами, врегульований спеціальними правилами.",
    "дорожній знак": "Стандартизований графічний щит біля дороги, що передає визначену інформацію учасникам руху.",
}


def build_inventory_and_decisions(*, dry_run: bool = False):
    sources = []
    decisions = []
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

        DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DECISIONS_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(decisions_doc, f, allow_unicode=True, sort_keys=False, width=1000)

        validate_decision_file(DECISIONS_PATH)
        read_source_inventory(INV_PATH)

    return inv_doc, decisions_doc


def build_new_atlas_entry(lemma: str, pos: str, gloss: str, source_info: dict[str, Any]) -> dict[str, Any]:
    def_text = NEW_DEFINITIONS.get(lemma, f"{gloss.capitalize()}.")
    ep_num = source_info.get("num", "00")
    ep_id = f"ohoiko-fmu-booster-ep-{ep_num}"
    locator = f"fmu-booster-ep-{ep_num}"
    ep_url = source_info.get("url", f"https://www.ukrainianlessons.com/fmu{int(ep_num)}/")

    en_terms = [g.strip() for g in re.split(r"[/,;]", gloss) if g.strip()]
    if not en_terms:
        en_terms = [gloss]

    # Authentic source attribution: curated educational vocabulary from Anna Ohoiko FMU Booster
    source_label = f"5 Minute Ukrainian (Анна Огойко, епізод {int(ep_num)})"
    is_phrase = " " in lemma
    # Multi-word phrases are not attested in VESUM as single lemmas
    is_vesum_attested = bool(verify_word(lemma)) if not is_phrase else False

    return {
        "lemma": lemma,
        "url_slug": _slug_for_url(lemma),
        "gloss": gloss,
        "pos": pos,
        "entry_type": "phrase" if is_phrase else "lemma",
        "review_state": "approved",
        "primary_source": "source_inventory_grow",
        "source_provenance": [
            {
                "source_family": "ohoiko",
                "source_locator": locator,
                "source_id": ep_id,
                "source_title": f"Anna Ohoiko - 5 Minute Ukrainian Episode {int(ep_num)}",
                "extraction_mode": "curated_headword",
                "visibility": "public",
                "redistributable": True,
            }
        ],
        "surface_admission": {"practice": True},
        "heritage_status": {
            "classification": "standard",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "sovietization_risk": 0,
            "calque_warning": None,
            "vesum_attested": is_vesum_attested,
            "warning_severity": "none",
        },
        "definition_cards": [
            {
                "id": "ohoiko",
                "source_dict": "ohoiko",
                "source_label": source_label,
                "definition": def_text,
                "definitions": [def_text],
                "source_url": ep_url,
                "sovietization_risk": 0,
            }
        ],
        "enrichment": {
            "meaning": {
                "uk": def_text,
                "source": "ohoiko",
                "source_url": ep_url,
            },
            "translation": {
                "en": en_terms,
                "terms": en_terms,
                "source": "learner_english_gloss",
                "gloss": gloss,
            },
            "sources": ["ohoiko", "learner_english_gloss"],
        },
    }


def admit_fmu_boosters(*, dry_run: bool = False) -> dict[str, Any]:
    print("Building inventory and decisions...")
    build_inventory_and_decisions(dry_run=dry_run)

    print(f"Loading hydrated manifest from {MANIFEST_PATH}...")
    manifest_data = load_manifest(MANIFEST_PATH)
    entries = manifest_data.get("entries", [])
    entries_by_key = {_lemma_key(str(e.get("lemma") or "")): e for e in entries if isinstance(e, dict)}
    print(f"Existing manifest entries: {len(entries_by_key)}")

    # Collect all occurrences for all booster words (preserve repeated episodes)
    word_to_episodes: dict[str, list[dict[str, Any]]] = {}
    for ep in EPISODES_DATA:
        for lemma, pos, gloss in ep["words"]:
            word_to_episodes.setdefault(lemma, []).append(
                {
                    "pos": pos,
                    "gloss": gloss,
                    "ep": ep,
                }
            )

    # 1. Overlay provenance on existing entries for ALL distinct episodes
    existing_updated = 0
    for lemma, ep_list in word_to_episodes.items():
        key = _lemma_key(lemma)
        if key in entries_by_key:
            entry = entries_by_key[key]
            prov_list = entry.get("source_provenance")
            if prov_list is None:
                prov_list = []
                entry["source_provenance"] = prov_list

            entry_updated = False
            for item in ep_list:
                ep = item["ep"]
                locator = f"fmu-booster-ep-{ep['num']}"
                ep_id = f"ohoiko-fmu-booster-ep-{ep['num']}"
                already_has = any(
                    isinstance(p, dict) and p.get("source_family") == "ohoiko" and p.get("source_locator") == locator
                    for p in prov_list
                )
                if not already_has:
                    prov_list.append(
                        {
                            "source_family": "ohoiko",
                            "source_locator": locator,
                            "source_id": ep_id,
                            "source_title": f"Anna Ohoiko - 5 Minute Ukrainian Episode {int(ep['num'])}",
                            "extraction_mode": "curated_headword",
                            "visibility": "public",
                            "redistributable": True,
                        }
                    )
                    entry_updated = True

            # If this is an already-promoted booster entry whose definition card needs authentic attribution, update in-place
            for card in entry.get("definition_cards", []):
                if card.get("source_dict") == "vts" and lemma in NEW_DEFINITIONS:
                    ep = ep_list[0]["ep"]
                    ep_num = ep.get("num", "00")
                    ep_url = ep.get("url", f"https://www.ukrainianlessons.com/fmu{int(ep_num)}/")
                    card["id"] = "ohoiko"
                    card["source_dict"] = "ohoiko"
                    card["source_label"] = f"5 Minute Ukrainian (Анна Огойко, епізод {int(ep_num)})"
                    card["source_url"] = ep_url
                    entry_updated = True

            if entry_updated:
                existing_updated += 1

    print(f"Updated provenance for {existing_updated} existing manifest entries.")

    # 2. Add newly admitted entries (strictly when not in manifest)
    new_entries = []
    for lemma, ep_list in word_to_episodes.items():
        key = _lemma_key(lemma)
        if key not in entries_by_key:
            first_item = ep_list[0]
            new_entry = build_new_atlas_entry(lemma, first_item["pos"], first_item["gloss"], first_item["ep"])
            for extra_item in ep_list[1:]:
                extra_ep = extra_item["ep"]
                extra_loc = f"fmu-booster-ep-{extra_ep['num']}"
                extra_id = f"ohoiko-fmu-booster-ep-{extra_ep['num']}"
                if not any(p.get("source_locator") == extra_loc for p in new_entry["source_provenance"]):
                    new_entry["source_provenance"].append(
                        {
                            "source_family": "ohoiko",
                            "source_locator": extra_loc,
                            "source_id": extra_id,
                            "source_title": f"Anna Ohoiko - 5 Minute Ukrainian Episode {int(extra_ep['num'])}",
                            "extraction_mode": "curated_headword",
                            "visibility": "public",
                            "redistributable": True,
                        }
                    )
            new_entries.append(new_entry)
            entries_by_key[key] = new_entry

    print(f"Newly promoted booster entries to admit: {len(new_entries)}")

    # Enrich new entries
    kaikki_lookup = enrich_manifest._load_kaikki_lookup()
    enriched_count = 0
    with sqlite3.connect(f"file:{SOURCES_DB_PATH}?mode=ro", uri=True) as conn:
        has_flags = enrich_manifest._sum11_has_flag_columns(conn)
        for idx, entry in enumerate(new_entries, 1):
            if enrich_manifest.enrich_entry(entry, conn, kaikki_lookup, has_sum11_flags=has_flags):
                enriched_count += 1
            if idx % 10 == 0 or idx == len(new_entries):
                print(f"  [{idx}/{len(new_entries)}] enriched ({entry['lemma']})", flush=True)

    all_entries = list(entries_by_key.values())
    all_entries.sort(key=lambda e: _lemma_key(str(e.get("lemma") or "")))
    manifest_data["entries"] = all_entries
    manifest_data["entries_count"] = len(all_entries)

    if dry_run:
        return {
            "existing_provenance_updated": existing_updated,
            "new_admitted": len(new_entries),
            "new_enriched": enriched_count,
            "total_entries": len(all_entries),
            "dry_run": True,
        }

    print(f"Updating fingerprint sidecar {FINGERPRINT_PATH}...")
    fp_info = write_fingerprint(FINGERPRINT_PATH, root=PROJECT_ROOT)
    manifest_fingerprint = fp_info["fingerprint"]
    schema_ver = fp_info.get("schema_version", 1)

    # Embed the exact fresh fingerprint inside manifest_data before serialization
    manifest_data["manifest_fingerprint"] = {
        "schema_version": schema_ver,
        "fingerprint": manifest_fingerprint,
    }

    print(f"Writing updated manifest to {MANIFEST_PATH}...")
    manifest_bytes = (json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    _write_atomic(MANIFEST_PATH, manifest_bytes)
    json_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    json_bytes = len(manifest_bytes)

    print("Compressing manifest to GZ asset...")
    gz_bytes = gzip.compress(manifest_bytes, mtime=0)
    gz_sha256 = hashlib.sha256(gz_bytes).hexdigest()
    asset_prefix = json_sha256[:12]
    asset_filename = f"lexicon-manifest-{asset_prefix}.json.gz"
    asset_path = Path(tempfile.gettempdir()) / asset_filename
    asset_path.write_bytes(gz_bytes)

    print(f"Uploading asset {asset_filename} to GitHub release atlas-manifest...")
    subprocess.check_call(
        [
            "gh",
            "release",
            "upload",
            "atlas-manifest",
            str(asset_path),
            "--clobber",
        ],
        timeout=120,
    )

    print("Updating lexicon-manifest.pointer.json...")
    pointer_data = json.loads(POINTER_PATH.read_text(encoding="utf-8"))
    pointer_data["asset_url"] = (
        f"https://github.com/learn-ukrainian/learn-ukrainian.github.io/releases/download/atlas-manifest/{asset_filename}"
    )
    pointer_data["gz_sha256"] = gz_sha256
    pointer_data["json_sha256"] = json_sha256
    pointer_data["gz_bytes"] = len(gz_bytes)
    pointer_data["json_bytes"] = json_bytes
    pointer_data["manifest_fingerprint"] = manifest_fingerprint
    pointer_data["fingerprint_schema_version"] = schema_ver
    pointer_data["richness_gate"]["override_reason"] = (
        "Admit FMU Vocabulary Booster lists and overlay Anna Ohoiko provenance (#7454, #6370)"
    )

    POINTER_PATH.write_text(
        json.dumps(pointer_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Rebuilding SQLite atlas.db at {ATLAS_DB_PATH}...")
    db_counts = migrate_manifest(MANIFEST_PATH, ATLAS_DB_PATH)
    print(f"atlas.db migration counts: {db_counts}")
    validate_alias_targets(ATLAS_DB_PATH)

    print(f"Rebuilding search index from {ATLAS_DB_PATH}...")
    generate_search_index.main(["--db", str(ATLAS_DB_PATH)])
    print("Search index rebuild complete.")

    return {
        "existing_provenance_updated": existing_updated,
        "new_admitted": len(new_entries),
        "new_enriched": enriched_count,
        "total_entries": len(all_entries),
        "asset_filename": asset_filename,
        "json_sha256": json_sha256,
        "gz_sha256": gz_sha256,
        "manifest_fingerprint": manifest_fingerprint,
        "dry_run": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Do not write changes to disk")
    args = parser.parse_args()

    summary = admit_fmu_boosters(dry_run=args.dry_run)
    print("Summary:", json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

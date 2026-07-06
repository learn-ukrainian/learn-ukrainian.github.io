"""Canonical subject slugs for rows in the ``textbooks`` corpus table."""

from __future__ import annotations

from pathlib import Path

CANONICAL_TEXTBOOK_SUBJECTS: tuple[str, ...] = (
    "ukrmova",
    "ukrlit",
    "istoriya",
    "bukvar",
    "lexicon",
    "informatyka",
    "matematyka",
    "algebra",
    "heometriya",
    "fizyka",
    "khimiya",
    "biolohiya",
    "heohrafiya",
    "astronomiya",
    "ekonomika",
    "pravoznavstvo",
    "hromadianska",
    "zakhyst",
    "mystetstvo",
    "vsesvitnia",
    "zarlit",
    "pryroda",
    "zdorovia",
    "etyka",
    "finansova",
)


KNOWN_SOURCE_FILE_SUBJECTS: dict[str, str] = {
    "1-klas-bukvar-bolshakova-2018-1": "bukvar",
    "1-klas-bukvar-bolshakova-2018-2": "bukvar",
    "1-klas-bukvar-zaharijchuk-2025-1": "bukvar",
    "1-klas-bukvar-zaharijchuk-2025-2": "bukvar",
    "10-klas-istorija-ukrajiny-gisem-2018": "istoriya",
    "10-klas-ukrajinska-literatura-avramenko-2018": "ukrlit",
    "10-klas-ukrajinska-mova-avramenko-2018": "ukrmova",
    "10-klas-ukrajinska-mova-zabolotnij-2018": "ukrmova",
    "10-klas-ukrlit-borzenko-2018-prof": "ukrlit",
    "10-klas-ukrmova-glazova-2018": "ukrmova",
    "10-klas-ukrmova-karaman-2018": "ukrmova",
    "10-klas-ukrmova-zabolotnyi-2018": "ukrmova",
    "11-klas-istoriya-ukr-galimov-2024": "istoriya",
    "11-klas-istoriya-ukr-gisem-2024": "istoriya",
    "11-klas-istoriya-ukr-hlibovska-2024": "istoriya",
    "11-klas-ukrajinska-literatura-avramenko-2019": "ukrlit",
    "11-klas-ukrajinska-mova-avramenko-2019": "ukrmova",
    "11-klas-ukrajinska-mova-glazova-2019": "ukrmova",
    "11-klas-ukrajinska-mova-voron-2019": "ukrmova",
    "11-klas-ukrlit-borzenko-2019-prof": "ukrlit",
    "11-klas-ukrmova-zabolotnyi-2019": "ukrmova",
    "2-klas-ukrmova-bolshakova-2019-1": "ukrmova",
    "2-klas-ukrmova-bolshakova-2019-2": "ukrmova",
    "2-klas-ukrmova-kravcova-2019-1": "ukrmova",
    "2-klas-ukrmova-kravcova-2019-2": "ukrmova",
    "2-klas-ukrmova-vashulenko-2019-1": "ukrmova",
    "2-klas-ukrmova-vashulenko-2019-2": "ukrmova",
    "3-klas-ukrainska-mova-kravtsova-2020-1": "ukrmova",
    "3-klas-ukrainska-mova-ponomarova-2020-1": "ukrmova",
    "3-klas-ukrainska-mova-savchenko-2020-2": "ukrmova",
    "3-klas-ukrainska-mova-savchuk-2020-2": "ukrmova",
    "3-klas-ukrainska-mova-vashulenko-2020-1": "ukrmova",
    "3-klas-ukrainska-mova-vashulenko-2020-2": "ukrmova",
    "4-klas-ukrayinska-mova-kravtsova-2021-1": "ukrmova",
    "4-klas-ukrayinska-mova-ponomarova-2021-1": "ukrmova",
    "4-klas-ukrayinska-mova-savchenko-2021-2": "ukrmova",
    "4-klas-ukrayinska-mova-varzatska-2021-1": "ukrmova",
    "4-klas-ukrayinska-mova-zaharijchuk-2021-1": "ukrmova",
    "4-klas-ukrmova-zaharijchuk": "ukrmova",
    "5-klas-istoriya-schupak-2022": "istoriya",
    "5-klas-ukrlit-avramenko-2022": "ukrlit",
    "5-klas-ukrlit-zabolotnyi-2022": "ukrlit",
    "5-klas-ukrmova-avramenko-2022": "ukrmova",
    "5-klas-ukrmova-golub-2022": "ukrmova",
    "5-klas-ukrmova-litvinova-2022": "ukrmova",
    "5-klas-ukrmova-zabolotnyi-2023": "ukrmova",
    "6-klas-istoriia-shchupak-2023": "istoriya",
    "6-klas-istoriya-gisem-2023": "istoriya",
    "6-klas-ukrlit-avramenko-2023": "ukrlit",
    "6-klas-ukrlit-kovalenko-2023": "ukrlit",
    "6-klas-ukrlit-zabolotnyi-2023": "ukrlit",
    "6-klas-ukrmova-avramenko-2023": "ukrmova",
    "6-klas-ukrmova-golub-2023": "ukrmova",
    "6-klas-ukrmova-litvinova-2023": "ukrmova",
    "6-klas-ukrmova-zabolotnyi-2020": "ukrmova",
    "7-klas-istoria-ukr-galimov-2024": "istoriya",
    "7-klas-istoria-ukr-hlibovska-2024": "istoriya",
    "7-klas-istoria-ukr-pometun-2024": "istoriya",
    "7-klas-ukrlit-avramenko-2024": "ukrlit",
    "7-klas-ukrlit-mishhenko-2015": "ukrlit",
    "7-klas-ukrlit-zabolotnyi-2024": "ukrlit",
    "7-klas-ukrmova-avramenko-2024": "ukrmova",
    "7-klas-ukrmova-litvinova-2024": "ukrmova",
    "7-klas-ukrmova-zabolotnyi-2024": "ukrmova",
    "8-klas-istoria-ukr-galimov-2025": "istoriya",
    "8-klas-istoria-ukr-hlibovska-2025": "istoriya",
    "8-klas-istoria-ukr-schupak-2025": "istoriya",
    "8-klas-istoriya-ukr-gisem-2021": "istoriya",
    "8-klas-ukrlit-avramenko-2025": "ukrlit",
    "8-klas-ukrlit-zabolotnyi-2025": "ukrlit",
    "8-klas-ukrmova-avramenko-2025": "ukrmova",
    "8-klas-ukrmova-onatiy-2025": "ukrmova",
    "8-klas-ukrmova-zabolotnyi-2025": "ukrmova",
    "9-klas-istorija-ukrajini-burnejko-2017": "istoriya",
    "9-klas-istorija-ukrajini-gisem-2017": "istoriya",
    "9-klas-ukrajinska-literatura-avramenko-2017": "ukrlit",
    "9-klas-ukrajinska-literatura-mishhenko-2017": "ukrlit",
    "9-klas-ukrajinska-mova-avramenko-2017": "ukrmova",
    "9-klas-ukrajinska-mova-voron-2017": "ukrmova",
    "9-klas-ukrajinska-mova-zabolotnij-2017": "ukrmova",
    "9-klas-ukrmova-zabolotnyi-2017": "ukrmova",
    "anna-ohoiko-1000-words-2nd-ed": "lexicon",
    "anna-ohoiko-500-verbs": "lexicon",
    "antonenko-davydovych-yak-my-hovorymo": "lexicon",
    "pohribnyi-ukrainska-literaturna-vymova-1992": "lexicon",
    "ulp-1-00-lesson-notes": "lexicon",
    "ulp-2-00-lesson-notes": "lexicon",
    "ulp-3-00-lesson-notes": "lexicon",
    "ulp-4-00-lesson-notes": "lexicon",
    "ulp-5-00-lesson-notes": "lexicon",
    "ulp-6-00-lesson-notes": "lexicon",
}


_SUBJECT_ALIASES: dict[str, str] = {
    "ukrainska-mova": "ukrmova",
    "ukrajinska-mova": "ukrmova",
    "ukrayinska-mova": "ukrmova",
    "ukr-mova": "ukrmova",
    "mova": "ukrmova",
    "ukrainska-literatura": "ukrlit",
    "ukrajinska-literatura": "ukrlit",
    "ukrayinska-literatura": "ukrlit",
    "literatura": "ukrlit",
    "history": "istoriya",
    "istorija": "istoriya",
    "istoria": "istoriya",
    "istoriia": "istoriya",
    "istoriya-ukr": "istoriya",
    "istoria-ukr": "istoriya",
    "vocab": "lexicon",
    "vocabulary": "lexicon",
    "wordlist": "lexicon",
    "lesson-notes": "lexicon",
    "geometriya": "heometriya",
    "geometry": "heometriya",
    "geografiya": "heohrafiya",
    "geohrafiya": "heohrafiya",
    "heohrafiia": "heohrafiya",
    "geography": "heohrafiya",
    "biolohiia": "biolohiya",
    "biologia": "biolohiya",
    "biology": "biolohiya",
    "chemistry": "khimiya",
    "physics": "fizyka",
}


_SUBJECT_TOKEN_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    # fizyka MUST precede astronomiya: integrated «Фізика і астрономія» course
    # stems (e.g. 11-klas-fizika-astronomiia-zasekina-2019-standart) contain both
    # tokens and are physics-primary — labelling them astronomiya would leave the
    # fizyka-11 gap-audit cell falsely at 0 chunks (#4593 batch 3). Pure astronomy
    # stems carry no fizyk/fizik token and still resolve to astronomiya.
    ("fizyka", ("fizyk", "fizik", "physics")),
    ("astronomiya", ("astronomiya", "astronomiia", "astronomija")),
    ("ekonomika", ("ekonomika", "ekonomka")),
    ("pravoznavstvo", ("pravoznavstvo",)),
    ("hromadianska", ("hromadianska", "gromadianska", "gromadjanska")),
    ("zakhyst", ("zakhyst", "zahyst", "zakhist")),
    ("mystetstvo", ("mystetstvo", "mystectvo", "mistectvo")),
    (
        "lexicon",
        (
            "anna-ohoiko",
            "1000-words",
            "500-verbs",
            "antonenko-davydovych",
            "yak-my-hovorymo",
            "pohribnyi",
            "literaturna-vymova",
            "lesson-notes",
            "ulp-",
        ),
    ),
    ("bukvar", ("bukvar",)),
    (
        "zarlit",
        (
            "zarubizhna",
            "zarubzhna",
            "zarlit",
        ),
    ),
    (
        "ukrlit",
        (
            "ukrlit",
            "ukr-lit",
            "ukrajinska-literatura",
            "ukrayinska-literatura",
            "ukrainska-literatura",
            "ukrayinska-lit",
        ),
    ),
    (
        "ukrmova",
        (
            "ukrmova",
            "ukr-mova",
            "ukrajinska-mova",
            "ukrayinska-mova",
            "ukrainska-mova",
        ),
    ),
    (
        "vsesvitnia",
        (
            "vsesvit",
        ),
    ),
    (
        "istoriya",
        (
            "istoriya",
            "istoriia",
            "istorija",
            "istoria",
        ),
    ),
    ("informatyka", ("informatyk", "informatik")),
    ("matematyka", ("matematyk", "matematik")),
    ("algebra", ("algebra",)),
    ("heometriya", ("heometri", "geometri", "geometry")),
    ("khimiya", ("khimi", "himi", "chemistry")),
    ("biolohiya", ("biolohi", "biologi", "biology")),
    (
        "heohrafiya",
        ("heohrafi", "geografi", "geohrafi", "geography"),
    ),
    ("pryroda", ("pryrod", "piznaiemo", "piznaemo", "prirod")),
    ("zdorovia", ("zdorov",)),
    ("etyka", ("etyka", "etika")),
    ("finansova", ("finans", "pidpryiemn")),
)


def _source_key(value: str) -> str:
    stem = Path(str(value).strip()).name
    for suffix in (".jsonl", ".pdf", ".txt"):
        stem = stem.removesuffix(suffix)
    return stem.casefold().replace("_", "-")


def normalize_subject_slug(subject: str | None) -> str | None:
    """Return a canonical subject slug for user/API input."""
    if subject is None:
        return None
    key = _source_key(subject)
    if not key:
        return None
    if key in CANONICAL_TEXTBOOK_SUBJECTS:
        return key
    return _SUBJECT_ALIASES.get(key)


def subject_for_source_file(source_file: str) -> str | None:
    """Infer a canonical subject slug from a ``textbooks.source_file`` value."""
    key = _source_key(source_file)
    if not key:
        return None
    if key in KNOWN_SOURCE_FILE_SUBJECTS:
        return KNOWN_SOURCE_FILE_SUBJECTS[key]
    for subject, tokens in _SUBJECT_TOKEN_PATTERNS:
        if any(token in key for token in tokens):
            return subject
    return None

# Canonical Cyrillic author forms keyed by the Latin transliteration used
# in source_file slugs. SINGLE SOURCE OF TRUTH (PR #4650 refactor): the
# 2026-05-15 author_uk migration and scripts/ingest/incremental_textbook_ingest.py
# both import THIS map — never grow a parallel copy again (the dual-map drift
# bit the batch-2 ingest: 'gisem' existed here-adjacent but not in the tool's
# local dict). Every value must be title-probed or front-matter-verified.
AUTHOR_UK_BY_TRANSLIT: dict[str, str] = {
    # Core mova/lit textbook authors (originally in TRANSLITS)
    "karaman": "Караман",
    "zakhariychuk": "Захарійчук",
    "zaharijchuk": "Захарійчук",
    "zahariichuk": "Захарійчук",
    "kravcova": "Кравцова",
    "kravtsova": "Кравцова",
    "avramenko": "Авраменко",
    "glazova": "Глазова",
    "hlazova": "Глазова",
    "zabolotnyi": "Заболотний",
    "zabolotnij": "Заболотний",
    "zakharchuk": "Захарчук",
    "vashulenko": "Вашуленко",
    "bolshakova": "Большакова",
    "mishhenko": "Міщенко",
    "mishchenko": "Міщенко",
    "litvinova": "Літвінова",
    "golub": "Голуб",
    "varzatska": "Варзацька",
    "ponomarova": "Пономарова",
    # Additional textbook authors present in the corpus
    "borzenko": "Борзенко",
    "burnejko": "Бурнейко",
    "galimov": "Галімов",
    "gisem": "Гісем",
    # Хлібовська: front-matter of 7-klas/8-klas/11-klas history textbooks
    # confirms Х (Kh), not Г — the Latin transliteration here is unusual
    # (h→Х instead of the more common h→Г). Verified via in-corpus
    # textbook front-matter (2026-05-15 audit).
    "hlibovska": "Хлібовська",
    "kovalenko": "Коваленко",
    "onatiy": "Онатій",
    "pometun": "Пометун",
    "savchenko": "Савченко",
    "savchuk": "Савчук",
    "schupak": "Щупак",
    "shchupak": "Щупак",
    "voron": "Ворон",
    # #4593 wave-1 STEM authors (title-probed from source pages 2026-07-06)
    "ryvkind": "Ривкінд",
    "ister": "Істер",
    "merzliak": "Мерзляк",
    "zadorozhnyi": "Задорожний",
    "bariakhtar": "Бар'яхтар",
    "hryhorovych": "Григорович",
    "popel": "Попель",
    "anderson": "Андерсон",
    "pryshliak": "Пришляк",
    "krupska": "Крупська",
    "lukianchykov": "Лук'янчиков",
    "narovlianskyi": "Наровлянський",
    "fuka": "Фука",
    "komarovska": "Комаровська",
    "masol": "Масол",
    "zapotockyi": "Запотоцький",
    "hilberh": "Гільберг",
    # Non-textbook author-name strings already stored in Latin/English on
    # ingestion (literary works, podcast, style-guide author). Map them
    # to Cyrillic so author_uk is uniformly Cyrillic when populated.
    "Anna Ohoiko": "Анна Огоїко",
    "Borys Antonenko-Davydovych": "Борис Антоненко-Давидович",
    "Mykola Pohribnyi": "Микола Погрібний",
    "Ukrainian Lessons Podcast": "Ukrainian Lessons Podcast",
    # #4593 batch-3 authors (title-probed 2026-07-06)
    "voloshchuk": "Волощук",
    "voloschuk": "Волощук",
    "voloshhuk": "Волощук",
    "ladychenko": "Ладиченко",
    "korshevniuk": "Коршевнюк",
    "korshevnuk": "Коршевнюк",
    "meleshchenko": "Мелещенко",
    "meleschenko": "Мелещенко",
    "rublia": "Рубля",
    "rublya": "Рубля",
    "davydiuk": "Давидюк",
    "mandrenko": "Мандренко",
    "hushchyna": "Гущина",
    "gushchyna": "Гущина",
    "guschyna": "Гущина",
    "plastun": "Пластун",
    "remekh": "Ремех",
    "gilberg": "Гільберг",
    "vasylkiv": "Васильків",
    "nelin": "Нелін",
    "shalamov": "Шаламов",
    "zasekina": "Засєкіна",
    "zasiekina": "Засєкіна",
    "pestushko": "Пестушко",
    "homiak": "Криховець-Хом'як",
    "krihovec-homyak": "Криховець-Хом'як",
    "gudyma": "Гудима",
    "hudyma": "Гудима",
    "gudima": "Гудима",
    "nazarenko": "Назаренко",
    "rudenko": "Руденко",
    "vorontsova": "Воронцова",
    "voroncova": "Воронцова",
    "boiko": "Бойко",
    "boyko": "Бойко",
    "bojko": "Бойко",
    "kovbasenko": "Ковбасенко",
    "merzlyak": "Мерзляк",
    "merzljak": "Мерзляк",
    "grygorovych": "Григорович",
    "zadorozhnyj": "Задорожний",
    "zadorozhnij": "Задорожний",
    # #4593 batch-3 scan-fallback edition switches (title-probed 2026-07-07):
    # Воронцова/Гущина/Шиян zdorovia-8 scans → Василенко digital; Давидюк/
    # Данилевська/Мелещенко etyka-6 scans → Мартинюк digital.
    "vasylenko": "Василенко",
    "martyniuk": "Мартинюк",
}

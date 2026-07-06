from __future__ import annotations

from collections import Counter

from scripts.wiki.textbook_subjects import (
    KNOWN_SOURCE_FILE_SUBJECTS,
    normalize_subject_slug,
    subject_for_source_file,
)

# Quoted from the required read-only probe:
# sqlite3 'file:/Users/krisztiankoos/projects/learn-ukrainian/data/sources.db?mode=ro' \
#   "SELECT DISTINCT source_file FROM textbooks ORDER BY source_file;"
CURRENT_TEXTBOOK_SOURCE_FILES = (
    "1-klas-bukvar-bolshakova-2018-1",
    "1-klas-bukvar-bolshakova-2018-2",
    "1-klas-bukvar-zaharijchuk-2025-1",
    "1-klas-bukvar-zaharijchuk-2025-2",
    "10-klas-istorija-ukrajiny-gisem-2018",
    "10-klas-ukrajinska-literatura-avramenko-2018",
    "10-klas-ukrajinska-mova-avramenko-2018",
    "10-klas-ukrajinska-mova-zabolotnij-2018",
    "10-klas-ukrlit-borzenko-2018-prof",
    "10-klas-ukrmova-glazova-2018",
    "10-klas-ukrmova-karaman-2018",
    "10-klas-ukrmova-zabolotnyi-2018",
    "11-klas-istoriya-ukr-galimov-2024",
    "11-klas-istoriya-ukr-gisem-2024",
    "11-klas-istoriya-ukr-hlibovska-2024",
    "11-klas-ukrajinska-literatura-avramenko-2019",
    "11-klas-ukrajinska-mova-avramenko-2019",
    "11-klas-ukrajinska-mova-glazova-2019",
    "11-klas-ukrajinska-mova-voron-2019",
    "11-klas-ukrlit-borzenko-2019-prof",
    "11-klas-ukrmova-zabolotnyi-2019",
    "2-klas-ukrmova-bolshakova-2019-1",
    "2-klas-ukrmova-bolshakova-2019-2",
    "2-klas-ukrmova-kravcova-2019-1",
    "2-klas-ukrmova-kravcova-2019-2",
    "2-klas-ukrmova-vashulenko-2019-1",
    "2-klas-ukrmova-vashulenko-2019-2",
    "3-klas-ukrainska-mova-kravtsova-2020-1",
    "3-klas-ukrainska-mova-ponomarova-2020-1",
    "3-klas-ukrainska-mova-savchenko-2020-2",
    "3-klas-ukrainska-mova-savchuk-2020-2",
    "3-klas-ukrainska-mova-vashulenko-2020-1",
    "3-klas-ukrainska-mova-vashulenko-2020-2",
    "4-klas-ukrayinska-mova-kravtsova-2021-1",
    "4-klas-ukrayinska-mova-ponomarova-2021-1",
    "4-klas-ukrayinska-mova-savchenko-2021-2",
    "4-klas-ukrayinska-mova-varzatska-2021-1",
    "4-klas-ukrayinska-mova-zaharijchuk-2021-1",
    "4-klas-ukrmova-zaharijchuk",
    "5-klas-istoriya-schupak-2022",
    "5-klas-ukrlit-avramenko-2022",
    "5-klas-ukrlit-zabolotnyi-2022",
    "5-klas-ukrmova-avramenko-2022",
    "5-klas-ukrmova-golub-2022",
    "5-klas-ukrmova-litvinova-2022",
    "5-klas-ukrmova-zabolotnyi-2023",
    "6-klas-istoriia-shchupak-2023",
    "6-klas-istoriya-gisem-2023",
    "6-klas-ukrlit-avramenko-2023",
    "6-klas-ukrlit-kovalenko-2023",
    "6-klas-ukrlit-zabolotnyi-2023",
    "6-klas-ukrmova-avramenko-2023",
    "6-klas-ukrmova-golub-2023",
    "6-klas-ukrmova-litvinova-2023",
    "6-klas-ukrmova-zabolotnyi-2020",
    "7-klas-istoria-ukr-galimov-2024",
    "7-klas-istoria-ukr-hlibovska-2024",
    "7-klas-istoria-ukr-pometun-2024",
    "7-klas-ukrlit-avramenko-2024",
    "7-klas-ukrlit-mishhenko-2015",
    "7-klas-ukrlit-zabolotnyi-2024",
    "7-klas-ukrmova-avramenko-2024",
    "7-klas-ukrmova-litvinova-2024",
    "7-klas-ukrmova-zabolotnyi-2024",
    "8-klas-istoria-ukr-galimov-2025",
    "8-klas-istoria-ukr-hlibovska-2025",
    "8-klas-istoria-ukr-schupak-2025",
    "8-klas-istoriya-ukr-gisem-2021",
    "8-klas-ukrlit-avramenko-2025",
    "8-klas-ukrlit-zabolotnyi-2025",
    "8-klas-ukrmova-avramenko-2025",
    "8-klas-ukrmova-onatiy-2025",
    "8-klas-ukrmova-zabolotnyi-2025",
    "9-klas-istorija-ukrajini-burnejko-2017",
    "9-klas-istorija-ukrajini-gisem-2017",
    "9-klas-ukrajinska-literatura-avramenko-2017",
    "9-klas-ukrajinska-literatura-mishhenko-2017",
    "9-klas-ukrajinska-mova-avramenko-2017",
    "9-klas-ukrajinska-mova-voron-2017",
    "9-klas-ukrajinska-mova-zabolotnij-2017",
    "9-klas-ukrmova-zabolotnyi-2017",
    "anna-ohoiko-1000-words-2nd-ed",
    "anna-ohoiko-500-verbs",
    "antonenko-davydovych-yak-my-hovorymo",
    "pohribnyi-ukrainska-literaturna-vymova-1992",
    "ulp-1-00-lesson-notes",
    "ulp-2-00-lesson-notes",
    "ulp-3-00-lesson-notes",
    "ulp-4-00-lesson-notes",
    "ulp-5-00-lesson-notes",
    "ulp-6-00-lesson-notes",
)


def test_current_textbook_source_files_all_map_to_canonical_subjects() -> None:
    assert len(CURRENT_TEXTBOOK_SOURCE_FILES) == 91
    subjects = [subject_for_source_file(source) for source in CURRENT_TEXTBOOK_SOURCE_FILES]

    assert None not in subjects
    assert Counter(subjects) == {
        "ukrmova": 45,
        "ukrlit": 16,
        "istoriya": 16,
        "bukvar": 4,
        "lexicon": 10,
    }
    assert set(CURRENT_TEXTBOOK_SOURCE_FILES) == set(KNOWN_SOURCE_FILE_SUBJECTS)


def test_subject_aliases_normalize_to_canonical_slugs() -> None:
    assert normalize_subject_slug("ukrainska-mova") == "ukrmova"
    assert normalize_subject_slug("ukrajinska-literatura") == "ukrlit"
    assert normalize_subject_slug("istoriia") == "istoriya"
    assert normalize_subject_slug("vocabulary") == "lexicon"
    assert normalize_subject_slug("unknown") is None


def test_future_stem_source_files_map_by_token() -> None:
    assert subject_for_source_file("5-klas-informatyka-example-2026") == "informatyka"
    assert subject_for_source_file("7-klas-geometriya-example-2026") == "heometriya"
    assert subject_for_source_file("8-klas-biolohiia-example-2026") == "biolohiya"

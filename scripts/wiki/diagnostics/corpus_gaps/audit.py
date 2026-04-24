#!/usr/bin/env python3
"""Audit corpus coverage gaps and draft a Ukrainian-only ingestion roadmap."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from wiki.config import TRACK_WRITE_DOMAIN
from wiki.diagnostics.retrieval_playback import normalize_text
from wiki.sources_db import SOURCES_DB_PATH

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
OUTPUT_DIR = PROJECT_ROOT / "data" / "corpus_audit"
ARTICLE_CONCEPTS_PATH = OUTPUT_DIR / "article_concepts.json"
COVERAGE_MAP_PATH = OUTPUT_DIR / "coverage_map.json"
GAP_CATEGORIES_PATH = OUTPUT_DIR / "gap_categories.md"
INGESTION_ROADMAP_PATH = OUTPUT_DIR / "ingestion_roadmap.md"
DRAFT_TICKETS_DIR = OUTPUT_DIR / "draft_tickets"
A1_REPORT_PATH = PROJECT_ROOT / "docs" / "architecture" / "corpus-coverage-map-a1.md"

DEFAULT_TRACKS = ("a1", "a2", "b1")
DEFAULT_MODEL = "gpt-5.5"
DEFAULT_CHUNKS_PER_PAGE = 1.4
MAX_CONCEPTS_PER_ARTICLE = 15
MIN_CONCEPTS_PER_ARTICLE = 8

NORMALIZED_SQL = (
    "replace("
    "replace("
    "replace("
    "replace("
    "replace(text, '’', char(39)), "
    "'ʼ', char(39)), "
    "'ʹ', char(39)), "
    "'`', char(39)), "
    "'´', char(39))"
)

SEVERITY_ORDER = {"BLOCKER": 0, "MAJOR": 1, "MINOR": 2}
TRACK_SEVERITY = {
    "a1": "BLOCKER",
    "a2": "BLOCKER",
    "b1": "MAJOR",
    "b2": "MAJOR",
    "c1": "MINOR",
    "c2": "MINOR",
}

OBJECTIVE_PREFIXES = (
    "Learner can ",
    "Understand ",
    "Recognize ",
    "Use ",
    "Distinguish ",
    "Form ",
    "Explain ",
    "Introduce ",
    "Practice ",
    "Build ",
    "Read ",
    "Write ",
)

STOPWORDS = {
    "або",
    "але",
    "вона",
    "вони",
    "воних",
    "де",
    "для",
    "до",
    "з",
    "за",
    "й",
    "і",
    "із",
    "їх",
    "коли",
    "на",
    "не",
    "про",
    "та",
    "те",
    "ти",
    "у",
    "це",
    "цей",
    "ця",
    "що",
    "як",
}

CATEGORY_RULES: tuple[dict[str, Any], ...] = (
    {
        "slug": "orthography-and-language-policy",
        "label": "Правопис і мовна політика",
        "keywords": {
            "1933",
            "1928",
            "ґ",
            "правопис",
            "реформа",
            "русифікац",
            "скрипників",
            "мовна політика",
            "сталінськ",
            "деколонізац",
        },
        "source_tags": ("orthography", "language-policy", "decolonization"),
    },
    {
        "slug": "phonetics-and-orthoepy",
        "label": "Фонетика й орфоепія",
        "keywords": {
            "звук",
            "букв",
            "голосн",
            "приголосн",
            "наголос",
            "склад",
            "орфоеп",
            "фонет",
            "фонолог",
            "милозвуч",
            "йотован",
            "м'якіст",
            "вимов",
            "артикуляц",
            "дзвінк",
            "глух",
        },
        "source_tags": ("phonetics", "pronunciation", "orthoepy"),
    },
    {
        "slug": "literacy-pedagogy",
        "label": "Початкова методика читання й письма",
        "keywords": {
            "читан",
            "грамот",
            "буквар",
            "звукобукв",
            "звукобуквений",
            "складов",
            "звуковий аналіз",
            "методика",
            "добуквар",
            "письм",
        },
        "source_tags": ("pedagogy", "literacy", "methodology"),
    },
    {
        "slug": "cases-and-declension",
        "label": "Відмінки й відмінювання",
        "keywords": {
            "відмінок",
            "в чи на",
            "в/у чи на",
            "родов",
            "давальн",
            "знахідн",
            "орудн",
            "місцев",
            "кличн",
            "відмінюван",
            "прийменник",
            "закінчен",
        },
        "source_tags": ("morphology", "cases", "grammar"),
    },
    {
        "slug": "verbs-aspect-and-tense",
        "label": "Дієслово: вид, час, спосіб",
        "keywords": {
            "дієслов",
            "вчора",
            "вчорашн",
            "додати -й",
            "додати -іть",
            "доконан",
            "недоконан",
            "вид",
            "минулий",
            "майбутн",
            "на -й",
            "на -іть",
            "наказов",
            "теперішн",
            "умовн",
            "рух",
            "інфінітив",
        },
        "source_tags": ("verbs", "aspect", "tense", "grammar"),
    },
    {
        "slug": "plural-and-agreement",
        "label": "Множина й узгодження",
        "keywords": {
            "жіночого роду",
            "інженерка",
            "множин",
            "назвах осіб",
            "програмістка",
            "узгоджен",
            "прикметник",
            "займенник",
            "числівник",
            "чоловічого роду",
            "plural",
        },
        "source_tags": ("morphology", "agreement", "grammar"),
    },
    {
        "slug": "word-formation-and-morphophonemics",
        "label": "Словотвір і морфонологія",
        "keywords": {
            "словотв",
            "морфем",
            "морфолог",
            "чергуван",
            "суфікс",
            "префікс",
            "корінь",
            "морфонолог",
        },
        "source_tags": ("word-formation", "morphology", "grammar"),
    },
    {
        "slug": "syntax-and-word-order",
        "label": "Синтаксис і порядок слів",
        "keywords": {
            "синтакс",
            "реченн",
            "порядок слів",
            "сполучник",
            "підрядн",
            "відносн",
            "умовн",
            "причин",
        },
        "source_tags": ("syntax",),
    },
    {
        "slug": "speech-formulas-and-etiquette",
        "label": "Мовленнєві формули й етикет",
        "keywords": {
            "будь ласка",
            "вітан",
            "діалог",
            "кличн",
            "по батькові",
            "перепрошую",
            "офіціант",
            "звертан",
            "етикет",
            "прохання",
            "запрошенн",
            "представлен",
            "ти-форма",
            "форми «ти» та «ви»",
            "форма «ти»",
            "форма «ви»",
            "ви-форма",
        },
        "source_tags": ("pedagogy", "etiquette", "usage"),
    },
    {
        "slug": "everyday-scenarios-and-lexical-formulas",
        "label": "Побутові сценарії та лексичні формули",
        "keywords": {
            "адрес",
            "блакитн",
            "готівк",
            "дорогу",
            "гостре",
            "годин",
            "замовлен",
            "картк",
            "колір",
            "квартир",
            "ліворуч",
            "меню",
            "напою",
            "праворуч",
            "прямо",
            "район",
            "рахунок",
            "синій",
            "страви",
        },
        "source_tags": ("a1-scenarios", "pedagogy"),
    },
)

CATEGORY_PRIORITY = {
    "orthography-and-language-policy": 5,
    "literacy-pedagogy": 4,
    "word-formation-and-morphophonemics": 4,
    "everyday-scenarios-and-lexical-formulas": 4,
    "cases-and-declension": 3,
    "verbs-aspect-and-tense": 3,
    "syntax-and-word-order": 3,
    "speech-formulas-and-etiquette": 3,
    "phonetics-and-orthoepy": 2,
    "plural-and-agreement": 1,
}


@dataclass(frozen=True)
class SourceProposal:
    slug: str
    title: str
    author: str
    publisher: str
    year: str
    edition: str
    provenance: str
    acquisition_url: str
    acquisition_method: str
    format: str
    license: str
    estimated_pages: int
    schema_target: str
    schema_mapping: str
    ingestion_script: str
    tags: tuple[str, ...]


SOURCE_CATALOG: tuple[SourceProposal, ...] = (
    SourceProposal(
        slug="ukrainian-pravopys-2019",
        title="Український правопис",
        author="Українська національна комісія з питань правопису",
        publisher="Наукова думка / МОН України",
        year="2019",
        edition="нова редакція, офіційний PDF",
        provenance="Офіційне державне видання, затверджене Кабміном і поширене МОН України.",
        acquisition_url="https://mon.gov.ua/npa/pro-vprovadzhennya-novoyi-redakciyi-ukrayinskogo-pravopisu",
        acquisition_method="Direct PDF download from the official MON page; no OCR expected.",
        format="pdf",
        license="official public PDF",
        estimated_pages=300,
        schema_target="textbooks",
        schema_mapping="Map as a reference grammar volume in `textbooks` with blank grade and author/publisher metadata preserved in `source_file`.",
        ingestion_script="new PDF ingest wrapper or adapted `scripts/rag/scrape_diasporiana.py` text-layer path",
        tags=("orthography", "language-policy", "phonetics", "grammar"),
    ),
    SourceProposal(
        slug="shevelov-ukrainska-mova-1900-1941",
        title="Українська мова в першій половині двадцятого століття (1900-1941). Стан і статус",
        author="Юрій Шевельов",
        publisher="Видавництво «Сучасність»",
        year="1987",
        edition="Бібліотека «Прологу» і «Сучасности», ч. 173",
        provenance="Diasporiana preservation page for a canonical Ukrainian-language linguistic study.",
        acquisition_url="https://diasporiana.org.ua/movoznavstvo/15218-shevelov-yu-ukrayinska-mova-v-pershiy-polovini-dvadtsyatogo-stolittya-1900-1941-stan-i-status/",
        acquisition_method="Download the preserved PDF from Diasporiana; probe text layer first, OCR only if extraction quality is poor.",
        format="pdf",
        license="preservation scan / archive PDF",
        estimated_pages=295,
        schema_target="textbooks",
        schema_mapping="Store as a scholarly monograph in `textbooks`; keep author/title in metadata and leave `grade` empty.",
        ingestion_script="scripts/rag/scrape_diasporiana.py",
        tags=("orthography", "language-policy", "decolonization"),
    ),
    SourceProposal(
        slug="antonenko-davydovych-yak-my-hovorymo",
        title="Як ми говоримо",
        author="Борис Антоненко-Давидович",
        publisher="Об’єднання Українських Письменників «Слово» / Українське видавництво «Смолоскип» ім. В. Симоненка",
        year="1979",
        edition="Балтиморське видання Diasporiana",
        provenance="Diasporiana preservation page for a Ukrainian usage and style classic.",
        acquisition_url="https://diasporiana.org.ua/movoznavstvo/17347-antonenko-davidovich-b-yak-mi-govorimo/",
        acquisition_method="Download the preserved PDF from Diasporiana; ingest as a style/usage book with OCR fallback only if needed.",
        format="pdf",
        license="preservation scan / archive PDF",
        estimated_pages=271,
        schema_target="textbooks",
        schema_mapping="Store as a reference usage book in `textbooks`; preserve publisher/author metadata and leave `grade` empty.",
        ingestion_script="scripts/rag/scrape_diasporiana.py",
        tags=("orthography", "usage", "decolonization", "style"),
    ),
    SourceProposal(
        slug="mosenkis-leksykolohiia-fonetyka",
        title="Сучасна українська літературна мова: Лексикологія. Фонетика",
        author="Анатолій Мойсієнко та ін.",
        publisher="Знання",
        year="2010",
        edition="підручник",
        provenance="Chtyvo preservation page with full bibliographic description and downloadable PDF.",
        acquisition_url="https://chtyvo.org.ua/authors/Mosenkis_Yurii/Suchasna_ukrainska_literaturna_mova_Leksykolohiia_Fonetyka/",
        acquisition_method="Download the PDF from Chtyvo; ingest directly if the text layer is intact.",
        format="pdf",
        license="preservation copy / educational PDF",
        estimated_pages=270,
        schema_target="textbooks",
        schema_mapping="Store as a phonetics/lexicology textbook in `textbooks`; keep multi-author metadata in title/author fields.",
        ingestion_script="new PDF ingest wrapper or adapted `scripts/rag/scrape_diasporiana.py` text-layer path",
        tags=("phonetics", "pronunciation", "orthoepy"),
    ),
    SourceProposal(
        slug="lavrynets-morfemika-slovotvir-morfolohiia",
        title="Сучасна українська літературна мова. Морфеміка. Словотвір. Морфологія",
        author="Олена Лавринець, Катерина Симонова, І. Ярошевич",
        publisher="Києво-Могилянська академія",
        year="2019",
        edition="серія «Могилянський підручник»",
        provenance="Ukrainian university press textbook with stable commercial acquisition page and full bibliography.",
        acquisition_url="https://www.yakaboo.ua/ua/suchasna-ukrains-ka-literaturna-mova-morfemika-slovotvir-morfologija.html",
        acquisition_method="Purchase or library acquisition of the paper textbook, then scan/OCR with manual QA for grammatical paradigms.",
        format="print",
        license="commercial / purchasable",
        estimated_pages=524,
        schema_target="textbooks",
        schema_mapping="Store as a university grammar textbook in `textbooks`; keep the publisher and author metadata, blank `grade`.",
        ingestion_script="new print-PDF ingest path with OCR QA",
        tags=("morphology", "word-formation", "grammar"),
    ),
    SourceProposal(
        slug="leonova-morfolohiia",
        title="Сучасна українська літературна мова. Морфологія",
        author="Марія Леонова",
        publisher="Вища школа",
        year="1983",
        edition="навчальний посібник",
        provenance="Chtyvo preservation page with a downloadable DjVu and bibliographic record.",
        acquisition_url="https://chtyvo.org.ua/authors/Leonova_Mariia/Suchasna_ukrainska_literaturna_mova_Morfolohiia/",
        acquisition_method="Download the DjVu from Chtyvo and convert/OCR to text before chunking.",
        format="djvu",
        license="preservation copy / educational scan",
        estimated_pages=264,
        schema_target="textbooks",
        schema_mapping="Store as a morphology reference in `textbooks`; preserve source type in `source_file` and leave `grade` empty.",
        ingestion_script="new DjVu→PDF/OCR ingest wrapper",
        tags=("morphology", "cases", "verbs", "grammar"),
    ),
    SourceProposal(
        slug="ponomariv-suchasna-ukrainska-mova",
        title="Сучасна українська мова",
        author="Олександр Пономарів",
        publisher="Либідь",
        year="2008",
        edition="4-те видання",
        provenance="Ukrainian university textbook with stable commercial metadata and broad grammar/phonetics coverage.",
        acquisition_url="https://www.yakaboo.ua/ua/suchasna-ukrains-ka-mova-1229246.html",
        acquisition_method="Purchase or library acquisition of the paper edition; scan with OCR and verify tables/examples manually.",
        format="print",
        license="commercial / purchasable",
        estimated_pages=448,
        schema_target="textbooks",
        schema_mapping="Store as a broad university grammar reference in `textbooks`; preserve the edition in metadata and keep `grade` blank.",
        ingestion_script="new print-PDF ingest path with OCR QA",
        tags=("phonetics", "syntax", "grammar", "usage"),
    ),
    SourceProposal(
        slug="tsilyna-syntaksys-skladnoho-rechennia",
        title="Сучасна українська літературна мова. Синтаксис складного речення",
        author="Марина Цілина",
        publisher='Університет "Україна"',
        year="n.d.",
        edition="навчальний посібник",
        provenance="Ukrainian syntax workbook with stable current metadata and focus on complex sentence structures.",
        acquisition_url="https://www.yakaboo.ua/ua/suchasna-ukrains-ka-literaturna-mova-sintaksis-skladnogo-rechennja.html",
        acquisition_method="Purchase the print edition or source from a university library; scan/OCR and keep module headings for conjunction and clause types.",
        format="print",
        license="commercial / purchasable",
        estimated_pages=228,
        schema_target="textbooks",
        schema_mapping="Store as a syntax-focused higher-ed manual in `textbooks`; preserve chapter names in `source_file` and leave `grade` blank.",
        ingestion_script="new print-PDF ingest path with OCR QA",
        tags=("syntax", "grammar"),
    ),
    SourceProposal(
        slug="doroz-metodyka-navchannia-ukrainskoi-movy",
        title="Методика навчання української мови в загальноосвітніх закладах",
        author="Вікторія Дороз",
        publisher="Центр учбової літератури",
        year="2008",
        edition="навчальний посібник",
        provenance="Ukrainian pedagogical manual surfaced via current book metadata and library references.",
        acquisition_url="https://www.yakaboo.ua/ua/metodika-navchannja-ukrains-koi-movi-v-zagal-noosvitnih-zakladah-3350949.html",
        acquisition_method="Purchase the print edition or source from a library, then scan/OCR with manual cleanup for tabular course outlines.",
        format="print",
        license="commercial / purchasable",
        estimated_pages=386,
        schema_target="textbooks",
        schema_mapping="Store as a pedagogy-methodology book in `textbooks`; use author/title metadata and keep `grade` blank.",
        ingestion_script="new print-PDF ingest path with OCR QA",
        tags=("pedagogy", "literacy", "methodology"),
    ),
    SourceProposal(
        slug="palinska-turkevych-krok-1",
        title="Крок 1. Українська мова як іноземна. Книга для студента",
        author="Олеся Палінська, Оксана Туркевич",
        publisher="Видавництво Львівської політехніки / МІОК",
        year="2014",
        edition="2-ге видання, рівень A1-A2",
        provenance="Ukrainian-for-foreigners textbook series from МІОК / Львівська політехніка with stable current acquisition pages.",
        acquisition_url="https://www.yakaboo.ua/ua/krok-1-ukrains-ka-mova-jak-inozemna-kniga-dlja-studenta-cd-rom.html",
        acquisition_method="Purchase the current student book or source it from a university library; scan/OCR the print pages and preserve lesson/dialogue metadata.",
        format="print",
        license="commercial / purchasable",
        estimated_pages=104,
        schema_target="textbooks",
        schema_mapping="Store as a Ukrainian-as-a-foreign-language coursebook in `textbooks`; preserve lesson titles in `source_file` and leave `grade` blank.",
        ingestion_script="new print-PDF ingest path with OCR QA",
        tags=("a1-scenarios", "pedagogy", "usage"),
    ),
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def looks_like_objective(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if isinstance(yaml.safe_load(stripped), dict):
        return True
    return stripped.startswith(OBJECTIVE_PREFIXES) or (len(stripped.split()) >= 8 and any(ch in stripped for ch in ".:"))


def normalize_slug_key(track: str, slug: str) -> str:
    return f"{track}/{slug}"


def parse_discovery_signals(discovery: dict[str, Any]) -> tuple[list[str], list[str]]:
    query_keywords = discovery.get("query_keywords", [])
    if not isinstance(query_keywords, list):
        query_keywords = []

    keywords: list[str] = []
    objectives: list[str] = []

    explicit_objectives = discovery.get("objectives", [])
    if isinstance(explicit_objectives, list):
        objectives.extend(str(item).strip() for item in explicit_objectives if str(item).strip())

    for raw_item in query_keywords:
        item = str(raw_item).strip()
        if not item:
            continue
        if looks_like_objective(item):
            objectives.append(item)
        else:
            keywords.append(item)

    deduped_keywords = list(dict.fromkeys(keywords))
    deduped_objectives = list(dict.fromkeys(objectives))
    return deduped_keywords, deduped_objectives


def iter_discovery_articles(tracks: list[str], allowed_slugs: set[str] | None = None) -> list[dict[str, str]]:
    articles: list[dict[str, str]] = []
    for track in tracks:
        discovery_dir = CURRICULUM_ROOT / track / "discovery"
        if not discovery_dir.exists():
            continue
        write_domain = TRACK_WRITE_DOMAIN.get(track)
        if write_domain is None:
            continue
        for path in sorted(discovery_dir.glob("*.yaml")):
            if allowed_slugs is not None and path.stem not in allowed_slugs:
                continue
            articles.append(
                {
                    "track": track,
                    "slug": path.stem,
                    "domain": write_domain,
                    "discovery_path": str(path),
                }
            )
    return articles


def build_concept_prompt(track: str, slug: str, query_keywords: list[str], objectives: list[str]) -> str:
    keyword_block = "\n".join(f"- {item}" for item in query_keywords) or "- (none)"
    objective_block = "\n".join(f"- {item}" for item in objectives) or "- (none)"
    return (
        "You are deriving corpus-audit concepts for a Ukrainian-learning wiki article.\n"
        "Return only JSON that matches the provided schema.\n\n"
        f"Track: {track}\n"
        f"Slug: {slug}\n\n"
        "Task:\n"
        "1. Derive 8-15 load-bearing, testable Ukrainian concepts that the article would need to ground.\n"
        "2. Keep concepts specific enough for corpus presence checks, not generic syllabus labels.\n"
        "3. For each concept, provide 2-4 short Ukrainian surface forms likely to appear verbatim in educational or reference prose.\n"
        "4. Use Ukrainian only. No English, no commentary, no citations, no explanations.\n"
        "5. Avoid single bare nouns unless that noun is itself the actual concept.\n"
        "6. Prefer phrases a human auditor could search for in a corpus.\n\n"
        "Query keywords:\n"
        f"{keyword_block}\n\n"
        "Objectives / objective-like lines:\n"
        f"{objective_block}\n"
    )


def run_codex_concept_extraction(prompt: str, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    schema = {
        "type": "object",
        "properties": {
            "concepts": {
                "type": "array",
                "minItems": MIN_CONCEPTS_PER_ARTICLE,
                "maxItems": MAX_CONCEPTS_PER_ARTICLE,
                "items": {
                    "type": "object",
                    "properties": {
                        "concept": {"type": "string", "minLength": 4},
                        "variants": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 4,
                            "items": {"type": "string", "minLength": 2},
                        },
                    },
                    "required": ["concept", "variants"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["concepts"],
        "additionalProperties": False,
    }

    with tempfile.TemporaryDirectory(prefix="corpus-gap-codex-") as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        schema_path = tmpdir / "schema.json"
        output_path = tmpdir / "last_message.json"
        schema_path.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")

        command = [
            "codex",
            "exec",
            "-m",
            model,
            "-s",
            "read-only",
            "--ephemeral",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            "-C",
            str(PROJECT_ROOT),
            "-",
        ]
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "Codex concept extraction failed: "
                f"returncode={completed.returncode}, stderr={completed.stderr.strip()}"
            )
        if not output_path.exists():
            raise RuntimeError("Codex concept extraction did not write the expected output file.")
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError("Codex concept extraction returned a non-object payload.")
        return payload


def sanitize_concepts(raw_concepts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sanitized: list[dict[str, Any]] = []
    seen: set[str] = set()

    for entry in raw_concepts:
        concept = str(entry.get("concept", "")).strip()
        if not concept:
            continue
        normalized_concept = normalize_text(concept)
        if not normalized_concept or normalized_concept in seen:
            continue

        variants = [concept]
        for variant in entry.get("variants", []):
            text = str(variant).strip()
            if text:
                variants.append(text)

        deduped_variants: list[str] = []
        seen_variants: set[str] = set()
        for variant in variants:
            normalized_variant = normalize_text(variant)
            if normalized_variant and normalized_variant not in seen_variants:
                deduped_variants.append(variant)
                seen_variants.add(normalized_variant)

        sanitized.append({"concept": concept, "variants": deduped_variants[:4]})
        seen.add(normalized_concept)

    return sanitized[:MAX_CONCEPTS_PER_ARTICLE]


def derive_article_concepts(
    *,
    track: str,
    slug: str,
    discovery_path: Path,
    model: str = DEFAULT_MODEL,
    cache: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cache = cache or {}
    key = normalize_slug_key(track, slug)
    cached_articles = cache.setdefault("articles", {})
    cached = cached_articles.get(key)
    if isinstance(cached, dict):
        return cached

    discovery = load_yaml(discovery_path)
    query_keywords, objectives = parse_discovery_signals(discovery)
    prompt = build_concept_prompt(track, slug, query_keywords, objectives)
    response = run_codex_concept_extraction(prompt, model=model)
    concepts = sanitize_concepts(response.get("concepts", []))

    if not (MIN_CONCEPTS_PER_ARTICLE <= len(concepts) <= MAX_CONCEPTS_PER_ARTICLE):
        raise RuntimeError(
            f"{key}: expected {MIN_CONCEPTS_PER_ARTICLE}-{MAX_CONCEPTS_PER_ARTICLE} concepts, got {len(concepts)}"
        )

    try:
        discovery_path_text = str(discovery_path.relative_to(PROJECT_ROOT))
    except ValueError:
        discovery_path_text = str(discovery_path)

    article_payload = {
        "track": track,
        "slug": slug,
        "domain": TRACK_WRITE_DOMAIN.get(track, ""),
        "discovery_path": discovery_path_text,
        "query_keywords": query_keywords,
        "objectives": objectives,
        "llm_model": model,
        "llm_prompt": prompt,
        "concepts": concepts,
    }
    cached_articles[key] = article_payload
    return article_payload


def build_candidate_forms(variants: list[str]) -> list[str]:
    candidate_forms: list[str] = []
    for variant in variants:
        normalized_variant = normalize_text(variant)
        if not normalized_variant:
            continue
        for form in {
            normalized_variant,
            normalized_variant.capitalize(),
            normalized_variant.upper(),
        }:
            for apostrophe in ("'", "’", "ʼ", "ʹ"):
                candidate_forms.append(form.replace("'", apostrophe))
    return list(dict.fromkeys(candidate_forms))


def query_table_for_concept(
    conn: sqlite3.Connection,
    *,
    table: str,
    variants: list[str],
) -> dict[str, Any]:
    conn.row_factory = sqlite3.Row
    candidate_forms = build_candidate_forms(variants)
    if not candidate_forms:
        return {"present": False, "match_count": 0, "sample_chunk_ids": []}

    where = " OR ".join(f"{NORMALIZED_SQL} LIKE '%' || ? || '%'" for _ in candidate_forms)
    rows = conn.execute(
        f"""
        SELECT chunk_id, text
        FROM {table}
        WHERE {where}
        """,
        tuple(candidate_forms),
    ).fetchall()
    normalized_variants = {normalize_text(variant) for variant in variants if normalize_text(variant)}
    deduped_rows: dict[str, sqlite3.Row] = {}
    for row in rows:
        normalized_text = normalize_text(row["text"])
        if any(variant in normalized_text for variant in normalized_variants):
            deduped_rows[row["chunk_id"]] = row

    ordered_rows = list(deduped_rows.values())
    return {
        "present": bool(ordered_rows),
        "match_count": len(ordered_rows),
        "sample_chunk_ids": [row["chunk_id"] for row in ordered_rows[:5]],
    }


def check_concept_coverage(conn: sqlite3.Connection, concept_entry: dict[str, Any]) -> dict[str, Any]:
    variants = [str(item) for item in concept_entry.get("variants", []) if str(item).strip()]
    textbooks = query_table_for_concept(conn, table="textbooks", variants=variants)
    external = query_table_for_concept(conn, table="external_articles", variants=variants)
    return {
        "concept": concept_entry["concept"],
        "variants": variants,
        "in_textbooks": textbooks["present"],
        "in_external": external["present"],
        "textbooks_match_count": textbooks["match_count"],
        "external_match_count": external["match_count"],
        "textbooks_sample_chunk_ids": textbooks["sample_chunk_ids"],
        "external_sample_chunk_ids": external["sample_chunk_ids"],
        "absent_from_corpus": not textbooks["present"] and not external["present"],
    }


def article_severity(track: str) -> str:
    return TRACK_SEVERITY.get(track, "MINOR")


def tokenize_ukrainian(text: str) -> list[str]:
    tokens = []
    for raw in normalize_text(text).replace("/", " ").replace("-", " ").split():
        token = raw.strip(".,;:!?\"'()[]{}")
        if len(token) < 3 or token in STOPWORDS:
            continue
        if not any("\u0400" <= ch <= "\u04FF" or ch == "ґ" for ch in token):
            continue
        tokens.append(token)
    return tokens


def classify_gap_entry(concept_text: str, variants: list[str]) -> dict[str, Any]:
    haystack = " ".join([concept_text, *variants]).lower()
    best_rule: dict[str, Any] | None = None
    best_score = 0
    best_priority = -1
    for rule in CATEGORY_RULES:
        score = sum(len(keyword) for keyword in rule["keywords"] if keyword in haystack)
        priority = CATEGORY_PRIORITY.get(rule["slug"], 0)
        if score > best_score or (score > 0 and score == best_score and priority > best_priority):
            best_score = score
            best_priority = priority
            best_rule = rule

    if best_rule is not None:
        return best_rule

    tokens = tokenize_ukrainian(haystack)
    if not tokens:
        return {
            "slug": "miscellaneous-gaps",
            "label": "Інші прогалини",
            "keywords": set(),
            "source_tags": tuple(),
        }

    top_token = Counter(tokens).most_common(1)[0][0]
    return {
        "slug": "miscellaneous-gaps",
        "label": "Інші прогалини",
        "keywords": {top_token},
        "source_tags": tuple(),
    }


def classify_gap_categories(coverage_map: dict[str, Any]) -> list[dict[str, Any]]:
    by_category: dict[str, dict[str, Any]] = {}
    for article in coverage_map.get("articles", []):
        for concept in article.get("concepts", []):
            if not concept.get("absent_from_corpus"):
                continue
            category_info = classify_gap_entry(concept["concept"], concept.get("variants", []))
            category = by_category.setdefault(
                category_info["slug"],
                {
                    "slug": category_info["slug"],
                    "label": category_info["label"],
                    "source_tags": list(category_info.get("source_tags", ())),
                    "affected_articles": set(),
                    "affected_concepts": [],
                    "severity_tier": "MINOR",
                },
            )
            category["affected_articles"].add(normalize_slug_key(article["track"], article["slug"]))
            category["affected_concepts"].append(
                {
                    "track": article["track"],
                    "slug": article["slug"],
                    "concept": concept["concept"],
                }
            )
            article_tier = article["severity_tier"]
            if SEVERITY_ORDER[article_tier] < SEVERITY_ORDER[category["severity_tier"]]:
                category["severity_tier"] = article_tier

    categories: list[dict[str, Any]] = []
    for category in by_category.values():
        categories.append(
            {
                "slug": category["slug"],
                "label": category["label"],
                "source_tags": category["source_tags"],
                "affected_article_count": len(category["affected_articles"]),
                "affected_articles": sorted(category["affected_articles"]),
                "affected_concept_count": len(category["affected_concepts"]),
                "affected_concepts": sorted(
                    category["affected_concepts"],
                    key=lambda item: (item["track"], item["slug"], item["concept"]),
                ),
                "severity_tier": category["severity_tier"],
            }
        )

    categories.sort(
        key=lambda item: (
            SEVERITY_ORDER[item["severity_tier"]],
            -item["affected_article_count"],
            -item["affected_concept_count"],
            item["label"],
        )
    )
    return categories


def render_gap_categories_markdown(coverage_map: dict[str, Any], categories: list[dict[str, Any]]) -> str:
    lines = [
        "# Corpus Gap Categories",
        "",
        f"- Generated: {coverage_map['metadata']['generated_at']}",
        f"- Tracks: {', '.join(coverage_map['metadata']['tracks'])}",
        f"- Articles audited: {coverage_map['metadata']['article_count']}",
        f"- Concepts checked: {coverage_map['metadata']['concept_count']}",
        f"- Absent-from-corpus concepts: {coverage_map['metadata']['absent_concept_count']}",
        "",
    ]
    for category in categories:
        lines.extend(
            [
                f"## {category['severity_tier']} — {category['label']}",
                "",
                f"- Affected concepts: {category['affected_concept_count']}",
                f"- Affected articles: {category['affected_article_count']}",
                f"- Article scope: {', '.join(category['affected_articles'])}",
                "- Representative concepts:",
            ]
        )
        for concept in category["affected_concepts"][:8]:
            lines.append(f"  - {concept['track']}/{concept['slug']}: {concept['concept']}")
        lines.append("")
    return "\n".join(lines).replace("\n  - ", "\n- ").rstrip() + "\n"


def select_sources_for_category(category: dict[str, Any]) -> list[SourceProposal]:
    selected = [
        proposal
        for proposal in SOURCE_CATALOG
        if any(tag in proposal.tags for tag in category.get("source_tags", []))
    ]
    if selected:
        return selected[:2]

    if category["severity_tier"] in {"BLOCKER", "MAJOR"}:
        return []

    return [SOURCE_CATALOG[0]]


def roadmap_title(category: dict[str, Any], proposal: SourceProposal) -> str:
    prefix = {
        "BLOCKER": "Ingest",
        "MAJOR": "Ingest",
        "MINOR": "Consider ingesting",
    }[category["severity_tier"]]
    return f"{prefix} {proposal.title} for {category['label'].lower()}"


def build_roadmap(categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for category in categories:
        proposals = select_sources_for_category(category)
        if not proposals:
            rows.append(
                {
                    "priority": category["severity_tier"],
                    "gap_category": category["label"],
                    "source": "unfillable_strict",
                    "format": "—",
                    "license": "—",
                    "estimated_chunks": 0,
                    "ingestion_ticket_title": "unfillable_strict",
                    "source_slug": "unfillable_strict",
                    "source_notes": (
                        "No strictly Ukrainian source in the deterministic catalog matched this category. "
                        "Leave the gap flagged rather than backfilling it with non-Ukrainian material."
                    ),
                }
            )
            continue

        for proposal in proposals:
            estimated_chunks = round(proposal.estimated_pages * DEFAULT_CHUNKS_PER_PAGE)
            rows.append(
                {
                    "priority": category["severity_tier"],
                    "gap_category": category["label"],
                    "source": f"{proposal.author} — {proposal.title}",
                    "format": proposal.format,
                    "license": proposal.license,
                    "estimated_chunks": estimated_chunks,
                    "ingestion_ticket_title": roadmap_title(category, proposal),
                    "source_slug": proposal.slug,
                    "source_notes": proposal.provenance,
                }
            )

    rows.sort(
        key=lambda item: (
            SEVERITY_ORDER[item["priority"]],
            item["gap_category"],
            item["source"],
        )
    )
    return rows


def render_roadmap_markdown(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Ukrainian-Source Ingestion Roadmap",
        "",
        "| Priority | Gap category | Source | Format | License | Estimated chunks | Ingestion ticket title |",
        "|---|---|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['priority']} | "
            f"{row['gap_category']} | "
            f"{row['source']} | "
            f"{row['format']} | "
            f"{row['license']} | "
            f"{row['estimated_chunks']} | "
            f"{row['ingestion_ticket_title']} |"
        )
    lines.append("")
    return "\n".join(lines)


def draft_ticket_slug(priority: str, category: str, source_slug: str) -> str:
    safe_category = category.lower()
    safe_category = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in safe_category)
    safe_category = "-".join(part for part in safe_category.split("-") if part)
    return f"{priority.lower()}-{safe_category}-{source_slug}"


def build_ticket_body(category: dict[str, Any], proposal: SourceProposal) -> str:
    estimated_chunks = round(proposal.estimated_pages * DEFAULT_CHUNKS_PER_PAGE)
    lines = [
        f"# Draft — {roadmap_title(category, proposal)}",
        "",
        "## Why",
        (
            f"`{category['label']}` affects {category['affected_article_count']} audited article(s) "
            f"and {category['affected_concept_count']} absent-from-corpus concept(s). "
            "This draft is for human review only and must not be auto-filed without approval."
        ),
        "",
        "## Source provenance",
        f"- Author: {proposal.author}",
        f"- Title: {proposal.title}",
        f"- Publisher / edition: {proposal.publisher}; {proposal.edition}; {proposal.year}",
        f"- Provenance: {proposal.provenance}",
        f"- License / access: {proposal.license}",
        "",
        "## Acquisition method",
        f"- Source URL: {proposal.acquisition_url}",
        f"- Method: {proposal.acquisition_method}",
        "",
        "## Estimated ingestion size",
        (
            f"- Estimated chunk count: ~{estimated_chunks} "
            f"(≈ {proposal.estimated_pages} page(s) × {DEFAULT_CHUNKS_PER_PAGE:.1f} chunks/page)"
        ),
        "",
        "## Schema mapping",
        f"- Target table: `{proposal.schema_target}`",
        f"- Mapping: {proposal.schema_mapping}",
        "",
        "## Suggested script reuse",
        f"- Starting point: `{proposal.ingestion_script}`",
        "",
        "## Acceptance criteria",
        "- The source is acquired from the listed Ukrainian-only provenance and stored with traceable metadata.",
        "- Text extraction is reproducible and chunked without writing new ad hoc DB tables.",
        "- A smoke query over the ingested chunks surfaces at least one currently missing concept from the target gap category.",
        "- The resulting chunks are added through the existing source-ingest pipeline and appear in `data/sources.db` after rebuild.",
    ]
    return "\n".join(lines) + "\n"


def write_draft_tickets(categories: list[dict[str, Any]], rows: list[dict[str, Any]]) -> list[Path]:
    DRAFT_TICKETS_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    categories_by_label = {category["label"]: category for category in categories}
    proposals_by_slug = {proposal.slug: proposal for proposal in SOURCE_CATALOG}

    for row in rows:
        if row["priority"] not in {"BLOCKER", "MAJOR"} or row["source_slug"] == "unfillable_strict":
            continue
        category = categories_by_label[row["gap_category"]]
        proposal = proposals_by_slug[row["source_slug"]]
        slug = draft_ticket_slug(row["priority"], category["slug"], row["source_slug"])
        path = DRAFT_TICKETS_DIR / f"{slug}.md"
        path.write_text(build_ticket_body(category, proposal), encoding="utf-8")
        written.append(path)

    return sorted(written)


def summarize_gap_categories(categories: list[dict[str, Any]], limit: int = 5) -> list[str]:
    return [
        f"{category['label']} ({category['affected_article_count']} article(s))"
        for category in categories[:limit]
    ]


def render_ratio_bar(numerator: int, denominator: int, width: int = 20) -> str:
    if denominator <= 0:
        return "." * width
    filled = round((numerator / denominator) * width)
    filled = max(0, min(width, filled))
    return "#" * filled + "." * (width - filled)


def build_article_coverage_rows(coverage_map: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for article in coverage_map.get("articles", []):
        concept_count = int(article.get("concept_count", 0))
        absent_count = int(article.get("absent_concept_count", 0))
        covered_count = max(0, concept_count - absent_count)
        coverage_pct = round((covered_count / concept_count) * 100, 1) if concept_count else 0.0
        missing_concepts = [
            concept["concept"]
            for concept in article.get("concepts", [])
            if concept.get("absent_from_corpus")
        ]
        rows.append(
            {
                "track": article["track"],
                "slug": article["slug"],
                "concept_count": concept_count,
                "absent_concept_count": absent_count,
                "covered_concept_count": covered_count,
                "coverage_pct": coverage_pct,
                "coverage_bar": render_ratio_bar(covered_count, concept_count),
                "missing_concepts": missing_concepts,
            }
        )
    rows.sort(
        key=lambda item: (
            -item["absent_concept_count"],
            item["coverage_pct"],
            item["slug"],
        )
    )
    return rows


def build_presence_breakdown(coverage_map: dict[str, Any]) -> dict[str, int]:
    counts = {
        "textbooks_and_external": 0,
        "textbooks_only": 0,
        "external_only": 0,
        "absent_from_both": 0,
    }
    for article in coverage_map.get("articles", []):
        for concept in article.get("concepts", []):
            in_textbooks = bool(concept.get("in_textbooks"))
            in_external = bool(concept.get("in_external"))
            if in_textbooks and in_external:
                counts["textbooks_and_external"] += 1
            elif in_textbooks:
                counts["textbooks_only"] += 1
            elif in_external:
                counts["external_only"] += 1
            else:
                counts["absent_from_both"] += 1
    return counts


def build_report_source_rows(categories: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for category in categories:
        for proposal in select_sources_for_category(category):
            rows.append(
                {
                    "priority": category["severity_tier"],
                    "gap_category": category["label"],
                    "affected_article_count": category["affected_article_count"],
                    "affected_concept_count": category["affected_concept_count"],
                    "source": f"{proposal.author} — {proposal.title}",
                    "format": proposal.format,
                    "license": proposal.license,
                    "estimated_chunks": round(proposal.estimated_pages * DEFAULT_CHUNKS_PER_PAGE),
                }
            )
    rows.sort(
        key=lambda item: (
            SEVERITY_ORDER[item["priority"]],
            -item["affected_article_count"],
            -item["affected_concept_count"],
            item["gap_category"],
            item["source"],
        )
    )
    return rows[:limit]


def render_a1_report_markdown(
    article_concepts: dict[str, Any],
    coverage_map: dict[str, Any],
    categories: list[dict[str, Any]],
) -> str:
    metadata = coverage_map.get("metadata", {})
    article_rows = build_article_coverage_rows(coverage_map)
    presence = build_presence_breakdown(coverage_map)
    total_concepts = int(metadata.get("concept_count", 0))
    absent_concepts = int(metadata.get("absent_concept_count", 0))
    covered_concepts = max(0, total_concepts - absent_concepts)
    coverage_pct = round((covered_concepts / total_concepts) * 100, 1) if total_concepts else 0.0
    cached_a1_concepts = sum(
        1 for key in article_concepts.get("articles", {}) if key.startswith("a1/")
    )
    source_rows = build_report_source_rows(categories)

    lines = [
        "# Corpus Coverage Map — A1 Smoke Test",
        "",
        "## Scope",
        (
            "This report summarizes the `#1333` A1 smoke-test slice only: the 23 already-audited A1 articles, "
            "with seminar tracks excluded."
        ),
        (
            f"`article_concepts.json` currently caches concept derivation for {cached_a1_concepts} A1 discovery files, "
            f"but the audited coverage slice in `coverage_map.json` remains {metadata.get('article_count', 0)} articles."
        ),
        "",
        "## Method",
        "- Concept derivation uses Codex judgment only; the prompt and model are recorded in `data/corpus_audit/article_concepts.json` for reproducibility.",
        "- Corpus presence checks are deterministic: normalized exact-substring matching against `textbooks` and `external_articles`, reusing `normalize_text` from `#1330` for apostrophes and OCR cleanup.",
        "- No LLM fuzzy matching is used for presence checks.",
        "",
        "## Summary",
        f"- Generated from data timestamp: {metadata.get('generated_at', 'unknown')}",
        f"- Articles audited: {metadata.get('article_count', 0)}",
        f"- Concepts checked: {total_concepts}",
        f"- Concepts grounded in at least one corpus: {covered_concepts} / {total_concepts} ({coverage_pct}%)",
        f"- Concepts absent from both corpora: {absent_concepts} / {total_concepts}",
        "",
        "## Corpus Presence Mix",
        "",
        "| Presence bucket | Concepts |",
        "|---|---:|",
        f"| In `textbooks` and `external_articles` | {presence['textbooks_and_external']} |",
        f"| In `textbooks` only | {presence['textbooks_only']} |",
        f"| In `external_articles` only | {presence['external_only']} |",
        f"| In neither corpus | {presence['absent_from_both']} |",
        "",
        "## Lowest-Coverage Articles",
        "",
        "| Article | Covered | Missing | Coverage |",
        "|---|---:|---:|---|",
    ]

    for row in article_rows[:10]:
        lines.append(
            f"| `{row['track']}/{row['slug']}` | "
            f"{row['covered_concept_count']} / {row['concept_count']} | "
            f"{row['absent_concept_count']} | "
            f"`{row['coverage_bar']}` {row['coverage_pct']}% |"
        )

    lines.extend(
        [
            "",
            "## Top Gap Categories",
            "",
            "| Severity | Category | Affected articles | Absent concepts | Representative gaps |",
            "|---|---|---:|---:|---|",
        ]
    )

    for category in categories[:5]:
        examples = ", ".join(
            concept["concept"] for concept in category["affected_concepts"][:3]
        )
        lines.append(
            f"| {category['severity_tier']} | {category['label']} | "
            f"{category['affected_article_count']} | "
            f"{category['affected_concept_count']} | "
            f"{examples} |"
        )

    lines.extend(
        [
            "",
            "## Priority Ukrainian Sources",
            "",
            "Strictly Ukrainian sources only; no Russian-language or translated-from-Russian works are proposed here.",
            "",
            "| Priority | Gap category | Affected articles | Source | Format | License | Est. chunks |",
            "|---|---|---:|---|---|---|---:|",
        ]
    )

    for row in source_rows:
        lines.append(
            f"| {row['priority']} | {row['gap_category']} | {row['affected_article_count']} | "
            f"{row['source']} | {row['format']} | {row['license']} | {row['estimated_chunks']} |"
        )

    lines.extend(
        [
            "",
            "## Findings",
            (
                "The weakest article by far is `a1/at-the-cafe`, where service-interaction language "
                "(menu requests, recommendations, bill/payment talk, dietary clarifications) is missing much more often "
                "than core school-grammar concepts."
            ),
            (
                "Most remaining A1 misses cluster around situational learner language: route-giving formulas, etiquette "
                "distinctions such as `ти`/`ви`, precise clock-time answers, and a few imperative/morphology teaching phrases."
            ),
            (
                "This points to a structural corpus mix problem rather than a broad grammar deficit: the school-textbook corpus "
                "covers phonetics and formal grammar better than adult beginner interactional Ukrainian."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def build_coverage_map(
    article_concepts: dict[str, Any],
    tracks: list[str],
    allowed_keys: set[str] | None = None,
) -> dict[str, Any]:
    articles: list[dict[str, Any]] = []
    total_concepts = 0
    absent_concepts = 0

    with sqlite3.connect(str(SOURCES_DB_PATH)) as conn:
        for key in sorted(article_concepts.get("articles", {})):
            if allowed_keys is not None and key not in allowed_keys:
                continue
            article = article_concepts["articles"][key]
            concept_results: list[dict[str, Any]] = []
            for concept_entry in article.get("concepts", []):
                concept_result = check_concept_coverage(conn, concept_entry)
                concept_results.append(concept_result)
                total_concepts += 1
                absent_concepts += int(concept_result["absent_from_corpus"])

            articles.append(
                {
                    "track": article["track"],
                    "slug": article["slug"],
                    "domain": article["domain"],
                    "severity_tier": article_severity(article["track"]),
                    "concept_count": len(concept_results),
                    "absent_concept_count": sum(1 for item in concept_results if item["absent_from_corpus"]),
                    "concepts": concept_results,
                }
            )

    return {
        "metadata": {
            "generated_at": utc_now(),
            "tracks": tracks,
            "article_count": len(articles),
            "concept_count": total_concepts,
            "absent_concept_count": absent_concepts,
        },
        "articles": articles,
    }


def run_audit(
    tracks: list[str],
    model: str = DEFAULT_MODEL,
    allowed_slugs: set[str] | None = None,
) -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cached_concepts = load_json(ARTICLE_CONCEPTS_PATH)
    cached_concepts.setdefault("metadata", {})
    cached_concepts.setdefault("articles", {})
    cached_concepts["metadata"].update(
        {
            "generated_at": utc_now(),
            "tracks": tracks,
            "llm_model": model,
        }
    )

    articles = iter_discovery_articles(tracks, allowed_slugs=allowed_slugs)
    for article in articles:
        derive_article_concepts(
            track=article["track"],
            slug=article["slug"],
            discovery_path=Path(article["discovery_path"]),
            model=model,
            cache=cached_concepts,
        )
        write_json(ARTICLE_CONCEPTS_PATH, cached_concepts)

    allowed_keys = {normalize_slug_key(article["track"], article["slug"]) for article in articles}
    coverage_map = build_coverage_map(cached_concepts, tracks, allowed_keys=allowed_keys)
    categories = classify_gap_categories(coverage_map)
    roadmap = build_roadmap(categories)
    ticket_paths = write_draft_tickets(categories, roadmap)

    write_json(COVERAGE_MAP_PATH, coverage_map)
    GAP_CATEGORIES_PATH.write_text(render_gap_categories_markdown(coverage_map, categories), encoding="utf-8")
    INGESTION_ROADMAP_PATH.write_text(render_roadmap_markdown(roadmap), encoding="utf-8")

    return {
        "article_concepts": cached_concepts,
        "coverage_map": coverage_map,
        "categories": categories,
        "roadmap": roadmap,
        "draft_ticket_paths": [str(path.relative_to(PROJECT_ROOT)) for path in ticket_paths],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tracks",
        default=",".join(DEFAULT_TRACKS),
        help="Comma-separated core tracks to audit (default: a1,a2,b1)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Codex model for concept extraction (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--slugs",
        default="",
        help="Optional comma-separated slug filter within the selected tracks.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    tracks = [track.strip() for track in args.tracks.split(",") if track.strip()]
    allowed_slugs = {slug.strip() for slug in args.slugs.split(",") if slug.strip()} or None
    result = run_audit(tracks=tracks, model=args.model, allowed_slugs=allowed_slugs)
    coverage = result["coverage_map"]
    categories = result["categories"]
    print(
        "Wrote "
        f"{COVERAGE_MAP_PATH.relative_to(PROJECT_ROOT)}, "
        f"{GAP_CATEGORIES_PATH.relative_to(PROJECT_ROOT)}, "
        f"{INGESTION_ROADMAP_PATH.relative_to(PROJECT_ROOT)} "
        f"for {coverage['metadata']['article_count']} article(s), "
        f"{coverage['metadata']['concept_count']} concept(s), "
        f"{len(result['draft_ticket_paths'])} draft ticket(s)."
    )
    if categories:
        print("Top categories:")
        for summary in summarize_gap_categories(categories):
            print(f"- {summary}")


if __name__ == "__main__":
    main()

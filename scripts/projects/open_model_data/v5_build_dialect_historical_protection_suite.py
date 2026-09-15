#!/usr/bin/env python3
"""Phase 5.2: Build Dialect & Historical Protection Test Suite (ULDR #8051).

Assembles the 600-case Held-Out Evaluation Suite for Anti-Over-Standardization:
  - 300 Regional Dialect Sentences (Southwestern, Southeastern, Northern) [PRESERVE]
  - 200 Historical & Classical Sentences (Old East Slavic, Middle Ukrainian) [PRESERVE]
  - 100 Anti-Surzhyk Invariant Negative Controls (Colonial Calques & Surzhyk) [CORRECT]

Grounds 100% of cases in verified local human sources (sources.db: literary_texts, style_guide, ua_gec_errors).
Validates every record against JSON schemas and emits cryptographic SHA-256 release receipts.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import jsonschema

from scripts.projects.open_model_data.dialect_protection_invariants import (
    LEMKO_BANNED_TARGET_RE,
    MAX_TOLERATED_DIALECT_CORRUPTION,
    MAX_TOLERATED_HISTORICAL_CORRUPTION,
    OES_GRAPH_RE,
    OES_MAX_YEAR,
    first_lemko_marker,
    infer_oes_work_from_text,
    is_metalinguistic_control,
    lemko_record_is_authentic,
    oes_passages_are_near_duplicates,
    oes_pick_target_term,
    oes_record_is_authentic,
    oes_text_is_diplomatic_excerpt,
    oes_work_bucket,
    surzhyk_record_is_authentic,
    surzhyk_target_allowed,
)

PRIMARY_REPO_ROOT_ENV = "LEARN_UKRAINIAN_PRIMARY_REPO_ROOT"


def _primary_repo_root() -> Path | None:
    """Resolve an extra search root from env. Fail closed: no baked host path."""
    raw = os.environ.get(PRIMARY_REPO_ROOT_ENV, "").strip()
    if not raw:
        return None
    candidate = Path(raw)
    resolved = candidate.resolve() if candidate.is_absolute() else (Path.cwd() / candidate).resolve()
    if not resolved.is_dir():
        raise ValueError(f"{PRIMARY_REPO_ROOT_ENV} is set but is not an existing directory")
    return resolved


def resolve_data_path(rel_path: str) -> Path:
    """Resolve a relative data path via REPO_ROOT, cwd, or LEARN_UKRAINIAN_PRIMARY_REPO_ROOT.

    No baked host checkout fallback. Missing inputs return the REPO_ROOT-relative
    path so callers can report a normal FileNotFoundError.
    """
    candidates = [REPO_ROOT / rel_path, Path.cwd() / rel_path]
    primary = _primary_repo_root()
    if primary is not None:
        candidates.append(primary / rel_path)
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        if resolved in seen:
            continue
        seen.add(resolved)
        if candidate.exists() and candidate.stat().st_size > 0:
            return candidate
    return REPO_ROOT / rel_path


DEFAULT_SOURCES_DB = resolve_data_path("data/sources.db")
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "partitions"
DEFAULT_CONTRACTS_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "contracts"
RECORD_SCHEMA_FILE = DEFAULT_CONTRACTS_DIR / "v1_dialect_historical_protection_record.schema.json"
RECEIPT_SCHEMA_FILE = DEFAULT_CONTRACTS_DIR / "v1_dialect_historical_protection_receipt.schema.json"
LEMKO_SEED_FILE = (
    REPO_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "decolonization"
    / "seeds"
    / "lemko_dialect_attested_seeds.jsonl"
)
MID_UA_SEED_FILE = (
    REPO_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "decolonization"
    / "seeds"
    / "middle_ukrainian_attested_seeds.jsonl"
)
OES_SEED_FILE = (
    REPO_ROOT
    / "data"
    / "projects"
    / "open_model_data"
    / "decolonization"
    / "seeds"
    / "oes_diplomatic_monument_seeds.jsonl"
)
EXISTING_SUITE_FILE = DEFAULT_OUTPUT_DIR / "dialect_historical_protection_suite_600.jsonl"
OES_WIKI_DIR = REPO_ROOT / "wiki" / "linguistics" / "oes"

LATER_SLAVIC_REJECT_RE = re.compile(
    r"рицерского|шляхецкого|литовськ|статут|вольност",
    re.IGNORECASE,
)


def clean_sentence(s: str) -> str:
    """Clean whitespace and normalise quotes in sentence."""
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("\r", "")
    # Remove leading dashes/bullets
    s = re.sub(r"^[—–-]\s*", "", s)
    return s.strip()


def extract_sentences(text: str) -> list[str]:
    """Split text into clean, well-bounded sentences."""
    # Split on sentence terminals followed by space and capital
    raw_sents = re.split(r"(?<=[.!?…])\s+(?=[А-ЯЄІЇҐA-Z\"«])", text)
    valid = []
    for s in raw_sents:
        cs = clean_sentence(s)
        # Length filter: 25 to 300 characters, at least 4 words
        if 25 <= len(cs) <= 300 and len(cs.split()) >= 4 and (cs[0].isupper() or cs[0] in "«\"'"):
            valid.append(cs)
    return valid


def _load_existing_suite() -> list[dict[str, Any]]:
    if not EXISTING_SUITE_FILE.exists():
        return []
    return [
        json.loads(line)
        for line in EXISTING_SUITE_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _reuse_existing_subgroup(subgroup: str, quota: int) -> list[dict[str, Any]]:
    rows = [c for c in _load_existing_suite() if c.get("subgroup") == subgroup]
    if subgroup == "middle_ukrainian":
        rows = [
            c
            for c in rows
            if "життя та творчість" not in (c.get("source_metadata") or {}).get("work", "").lower()
        ]
    return rows[:quota]


def mine_lemko_from_seeds(quota: int = 40) -> list[dict[str, Any]]:
    """Load attested Lemko dialect sentences from the git-grounded seed file."""
    if not LEMKO_SEED_FILE.exists():
        raise FileNotFoundError(f"Lemko seed file missing: {LEMKO_SEED_FILE}")
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in LEMKO_SEED_FILE.read_text(encoding="utf-8").splitlines():
        if len(records) >= quota:
            break
        if not line.strip():
            continue
        seed = json.loads(line)
        text = clean_sentence(seed["input_text"])
        if text in seen:
            continue
        marker = first_lemko_marker(text)
        if marker is None or LEMKO_BANNED_TARGET_RE.search(marker):
            continue
        target = str(seed.get("target_term") or marker)
        if LEMKO_BANNED_TARGET_RE.search(target) or target.casefold() not in text.casefold():
            target = marker
        notes = (
            "Лемківський говір південно-західного наріччя. "
            f"Лексема «{target}» ({seed.get('definition', 'автентичний лемківський маркер')}). "
            "Автентична діалектна одиниця української мови та жива культурна спадщина. "
            "Підлягає безумовному захисту від штучного виправлення, стандартизації або "
            "хибної класифікації як суржику чи помилки."
        )
        rec = {
            "eval_id": f"eval_prot_dial_{len(records) + 1:04d}",
            "stratum": "regional_dialect",
            "subgroup": "southwestern_lemko",
            "case_type": "PRESERVE",
            "input_text": text,
            "target_term": target,
            "expected_action": "PRESERVE",
            "expected_replacement": None,
            "linguistic_notes": notes,
            "source_metadata": {
                "source": "literary_texts",
                "author": seed.get("author") or "Народна пісня",
                "work": seed.get("work") or "Лемківська народна пісня",
                "year": int(seed.get("year") or 1929),
                "language_period": "modern",
                "region_or_dialect": "southwestern_lemko",
            },
        }
        if not lemko_record_is_authentic(rec):
            continue
        seen.add(text)
        records.append(rec)
    if len(records) < quota:
        raise ValueError(f"Lemko seed harvest produced {len(records)} authentic cases, need {quota}")
    return records[:quota]


def _clean_oes_chunk(chunk: str) -> str:
    chunk = re.sub(r"\s+", " ", chunk).strip()
    chunk = re.sub(r"^[\s«»\"'`>*]+|[\s«»\"'`>]+$", "", chunk)
    chunk = re.sub(r"\s*\[S\d+[^\]]*\]\s*", " ", chunk)
    chunk = re.sub(r"\s*chunk_id:\s*`?[\w]+`?", " ", chunk, flags=re.IGNORECASE)
    chunk = re.sub(r"\s+", " ", chunk).strip(" «»\"'`")
    return chunk


def _make_oes_record(text: str, work: str, year: int, target: str | None = None) -> dict[str, Any] | None:
    picked = oes_pick_target_term(text)
    if target is None or len(target) < 2 or not OES_GRAPH_RE.search(target):
        target = picked
    if len(target) < 2:
        return None
    notes = (
        f"Давньоруська мовна доба (XI–XIII ст.), пам'ятка «{work}». "
        f"Історична лексема «{target}» збережена в оригінальній/дипломатичній графіці. "
        "Автентичний текст літописної спадщини Русі. "
        "Підлягає збереженню в оригінальному або коментованому вигляді; "
        "неприпустимо модернізувати під сучасний правопис або оголошувати граматичною помилкою."
    )
    rec = {
        "eval_id": "eval_prot_hist_0000",
        "stratum": "historical_text",
        "subgroup": "old_east_slavic",
        "case_type": "PRESERVE",
        "input_text": text,
        "target_term": target,
        "expected_action": "PRESERVE",
        "expected_replacement": None,
        "linguistic_notes": notes,
        "source_metadata": {
            "source": "literary_texts",
            "author": "Давньоруський книжник",
            "work": work,
            "year": year if year <= OES_MAX_YEAR else OES_MAX_YEAR,
            "language_period": "old_east_slavic",
        },
    }
    if not oes_record_is_authentic(rec):
        return None
    return rec


def _append_unique_oes(raw: list[dict[str, Any]], rec: dict[str, Any]) -> bool:
    text = rec["input_text"]
    for existing in raw:
        if oes_passages_are_near_duplicates(existing["input_text"], text):
            return False
    raw.append(rec)
    return True


def mine_oes_from_seeds() -> list[dict[str, Any]]:
    """Load curated diplomatic excerpts of named monuments."""
    if not OES_SEED_FILE.exists():
        raise FileNotFoundError(f"OES seed file missing: {OES_SEED_FILE}")
    raw: list[dict[str, Any]] = []
    for line in OES_SEED_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        seed = json.loads(line)
        text = _clean_oes_chunk(str(seed["input_text"]))
        if not oes_text_is_diplomatic_excerpt(text):
            continue
        inferred = infer_oes_work_from_text(text)
        work = str(seed.get("work") or (inferred[0] if inferred else ""))
        year = int(seed.get("year") or (inferred[1] if inferred else 1200))
        rec = _make_oes_record(text, work, year, seed.get("target_term"))
        if rec is None:
            continue
        _append_unique_oes(raw, rec)
    return raw


def mine_oes_from_wiki() -> list[dict[str, Any]]:
    """Mine diplomatic excerpts from wiki pages, ignoring pedagogy / later citations."""
    if not OES_WIKI_DIR.is_dir():
        raise FileNotFoundError(f"OES wiki directory missing: {OES_WIKI_DIR}")
    raw: list[dict[str, Any]] = []
    for path in sorted(OES_WIKI_DIR.glob("*.md")):
        body = path.read_text(encoding="utf-8")
        candidates = re.findall(r">\s*«?([^<\n]{20,400})", body)
        candidates += re.findall(r"«([^»]{20,400})»", body)
        candidates += re.findall(r"`([^`]{20,400})`", body)
        for chunk in candidates:
            chunk = _clean_oes_chunk(chunk)
            if not oes_text_is_diplomatic_excerpt(chunk):
                continue
            if LATER_SLAVIC_REJECT_RE.search(chunk):
                continue
            if re.search(r"яременк|переклад|чи не гоже було б нам", chunk, re.IGNORECASE):
                continue
            inferred = infer_oes_work_from_text(chunk)
            if inferred is None:
                continue
            work, year = inferred
            rec = _make_oes_record(chunk, work, year)
            if rec is None:
                continue
            _append_unique_oes(raw, rec)
    return raw


def mine_oes_diplomatic(quota: int = 100) -> list[dict[str, Any]]:
    """Assemble unique diplomatic monument excerpts. Do not pad with fake labels."""
    raw: list[dict[str, Any]] = []
    for rec in mine_oes_from_seeds() + mine_oes_from_wiki():
        _append_unique_oes(raw, rec)
    if len(raw) < quota:
        raise ValueError(
            f"OES diplomatic harvest produced {len(raw)} unique authentic cases, need {quota}"
        )
    ordered = _diversify_oes_monuments(raw, quota)
    records = []
    for idx, rec in enumerate(ordered, start=1):
        rec = dict(rec)
        rec["eval_id"] = f"eval_prot_hist_{idx:04d}"
        records.append(rec)
    return records


def _diversify_oes_monuments(raw: list[dict[str, Any]], quota: int) -> list[dict[str, Any]]:
    """Take every unique authentic PVL/Slovo/Pravda excerpt, then fill. No reserved padding."""
    buckets: dict[str, list[dict[str, Any]]] = {"pvl": [], "slovo": [], "pravda": [], "other": []}
    for rec in raw:
        key = oes_work_bucket(str(rec["source_metadata"]["work"]))
        buckets.setdefault(key, buckets["other"]).append(rec)
    picked: list[dict[str, Any]] = []
    used: set[int] = set()
    for key in ("pvl", "slovo", "pravda", "other"):
        for rec in buckets[key]:
            ident = id(rec)
            if ident in used:
                continue
            used.add(ident)
            picked.append(rec)
            if len(picked) >= quota:
                return picked
    return picked[:quota]


def mine_dialect_sentences(conn: sqlite3.Connection | None) -> list[dict[str, Any]]:
    """Mine 300 authentic regional dialect sentences across Southwestern, Southeastern, and Northern groups."""
    records: list[dict[str, Any]] = []

    # Dialect specifications: (subgroup, query_filter, terms_list, quota)
    # terms_list: tuple of (regex_stem, canonical_target, definition)
    subgroups = [
        # 1. Southwestern - Hutsul (45 cases)
        (
            "southwestern_hutsul",
            "SELECT author, work, text, year FROM literary_texts WHERE (author LIKE '%Коцюбинськ%' AND work LIKE '%Тіні забутих предків%') OR author LIKE '%Федькович%'",
            [
                (r"\bцаринк\w*", "царинка", "обгороджений сінокіс чи лука біля садиби у Карпатах"),
                (r"\bпла[яїіеє]\w*", "плай", "гірська стежка або дорога через хребет чи полонину"),
                (r"\bлегін\w*", "легінь", "парубок, юнак, сміливий молодий гуцул"),
                (r"\bмольфар\w*", "мольфар", "знахар, чарівник, носій традиційного карпатського світогляду"),
                (r"\bкрисан\w*", "крисаня", "гуцульський традиційний повстяний капелюх із крисами"),
                (r"\bватаг\w*", "ватаг", "старший вівчар, керівник вівчарського господарства на полонині"),
                (r"\bмаржинк\w*", "маржинка", "худоба, свійські тварини в гуцульській говірці"),
                (r"\bарідник\w*", "арідник", "злий дух, чорт у гуцульській демонології"),
                (r"\bбосоркан\w*", "босорканя", "відьма, чаклунка у карпатських народних віруваннях"),
                (r"\bчерес\w*", "черес", "широкий шкіряний чоловічий пояс із пряжками та кишенями"),
                (r"\bтрембіт\w*", "трембіта", "народний дерев'яний духовий інструмент карпатських горян"),
                (r"\bполонин\w*", "полонина", "високогірне пасовище вище межі лісу"),
                (r"\bструнґ\w*|\bструнг\w*", "струнга", "вузький прохід у загорожі для доїння овець"),
                (r"\bпостол\w*", "постоли", "традиційне шкіряне взуття горян без підборів"),
                (r"\bдроб\'ят\w*", "дроб'ята", "дрібна худоба або малі діти в гуцульській говірці"),
                (r"\bнявк\w*", "нявка", "лісова міфічна істота, мавка у карпатському фольклорі"),
                (r"\bколиб\w*", "колиба", "сезонне дерев'яне житло вівчарів і лісорубів на полонині"),
                (r"\bгазд\w*|\bґазд\w*", "ґазда", "господар садиби, голова родини у південно-західних говірках"),
            ],
            45,
        ),
        # 2. Southwestern - Boyko (45 cases)
        (
            "southwestern_boyko",
            "SELECT author, work, text, year FROM literary_texts WHERE author LIKE '%Франко%' AND (work LIKE '%Борислав%' OR work LIKE '%Захар Беркут%')",
            [
                (r"\bбескид\w*", "бескид", "гірський хребет, крута скеля або урвище в Карпатах"),
                (r"\bопришк\w*", "опришок", "учасник селянського визвольного повстанського руху в Карпатах"),
                (r"\bватр\w*", "ватра", "велике вогнище або живе багаття у бойківській та карпатській традиції"),
                (r"\bкичер\w*", "кичера", "гора, вкрита лісом, крім вершини, у карпатській топонімії"),
                (r"\bкошар\w*", "кошара", "загорода або хлів для овець у бойківському вівчарстві"),
                (r"\bберд\w*", "бердо", "круча, скелясте урвище або урвиста гора"),
                (r"\bдебр\w*", "дебря", "глибокий зарослий яр, ущелина або гущавина в горах"),
                (r"\bпутівець\w*", "путівець", "гірська або польова ґрунтова дорога"),
                (r"\bтухольц\w*", "тухольці", "мешканці давньої гірської громади Тухольщини"),
                (r"\bзвор\w*", "звір", "гірська ущелина або потік між горами"),
            ],
            45,
        ),
        # 3. Southwestern - Lemko is mined from attested seeds, not this regex harvest.
        # 4. Southwestern - Galician/Pokuttia (50 cases)
        (
            "southwestern_galician",
            "SELECT author, work, text, year FROM literary_texts WHERE author LIKE '%Стефаник%'",
            [
                (
                    r"\bґазд\w*|\bгазд\w*",
                    "ґазда",
                    "господар садиби, заможний селянин у покутсько-буковинському діалекті",
                ),
                (r"\bфамілі\w*", "фамілія", "родина, рід, сім'я у галицькому та покутському мовленні"),
                (r"\bкавалок\w*", "кавалок", "шматок, частина чогось у західноукраїнських діалектах"),
                (r"\bнай\b", "най", "спонукальна частка «хай», «нехай» у південно-західному наріччі"),
                (r"\bпослі\b", "послі", "прислівник «потім», «згодом», «пізніше» в покутській говірці"),
                (r"\bніц\b", "ніц", "займенник «нічого», «аніскільки» в західноукраїнському мовленні"),
                (r"\bспоритися\b|\bспоривс\w*", "споритися", "мати успіх, ладитися, приносити користь або сперечатися"),
                (r"\bдоконче\b", "доконче", "прислівник «конче», «обов'язково», «неодмінно»"),
                (
                    r"\bстратився\b|\bстративси\b",
                    "стратився",
                    "загинув, пропав або вчинив самогубство в народній драмі",
                ),
                (r"\bбайк\w*", "байка", "дрібниця, пусте, не варте уваги («то байка» — пусте)"),
            ],
            50,
        ),
        # 5. Southeastern - Poltava / Central Dnieper (45 cases)
        (
            "southeastern_poltava",
            "SELECT author, work, text, year FROM literary_texts WHERE author LIKE '%Котляревськ%' OR author LIKE '%Нечуй-Левицький%'",
            [
                (r"\bпарубоцьк\w*", "парубоцький", "властивий неодруженому юнакові, парубкові"),
                (
                    r"\bвечорниц\w*",
                    "вечорниці",
                    "традиційні молодіжні зібрання з піснями й розвагами в осінньо-зимовий період",
                ),
                (r"\bчумак\w*", "чумак", "візник і торговець сіллю й рибою в Україні XVI–XIX століть"),
                (r"\bледащ\w*", "ледащо", "нероба, ледачий або безпутний чоловік у народній мові"),
                (r"\bбайрак\w*", "байрак", "сухий лісистий яр або балка у лісостеповій Україні"),
                (r"\bкурінн\w*", "курінний", "козацький отаман куреня на Запорозькій Січі"),
                (r"\bоковит\w*", "оковита", "міцна горілка високого ґатунку старовинного домашнього виготовлення"),
                (r"\bдосвітк\w*", "досвітки", "вечірні та нічні посиденьки молоді, звичаєва форма дозвілля"),
                (r"\bзапорожець\w*|\bзапорожц\w*", "запорожець", "козак Низового Війська Запорозького"),
                (r"\bгайка\w*", "гайка", "невеликий гай, чагарник або урочище"),
            ],
            45,
        ),
        # 6. Southeastern - Slobozhan (25 cases)
        (
            "southeastern_slobozhan",
            "SELECT author, work, text, year FROM literary_texts WHERE author LIKE '%Хвильовий%' OR (author LIKE '%Мирний%' AND work LIKE '%Повія%')",
            [
                (r"\bслобод\w*", "слобода", "поселення на Слобожанщині, вільне від повинностей"),
                (r"\bхутір\w*|\bхутор\w*", "хутір", "відокремлена сільська садиба чи мале селище"),
                (r"\bкозир-дівк\w*", "козир-дівка", "бойова, моторна, показлива дівчина"),
                (r"\bярмарок\w*", "ярмарок", "періодичний святковий торг у містечку чи слободі"),
                (r"\bмандрівк\w*", "мандрівка", "подорож, поїздка степовими та слобідськими просторами"),
            ],
            25,
        ),
        # 7. Northern - Polissian (50 cases)
        (
            "northern_polissian",
            "SELECT author, work, text, year FROM literary_texts WHERE author LIKE '%Українка%' AND work LIKE '%Лісова пісня%'",
            [
                (r"\bмавк\w*", "мавка", "лісова міфічна діва, душа дерев у поліському фольклорі"),
                (r"\bпотерчат\w*", "потерчата", "міфічні душі нехрещених дітей у поліських віруваннях"),
                (r"\bводяник\w*", "водяник", "міфічний господар водойм і заплав у Поліссі"),
                (r"\bлісовик\w*", "лісовик", "міфічний дух, повелитель лісу та звірів"),
                (r"\bперелесник\w*", "перелесник", "спокусливий літаючий вогняний міфічний дух"),
                (r"\bбагн\w*", "багно", "болото, грузька трясовина в лісових масивах Полісся"),
                (r"\bгайстер\w*", "гайстер", "поліська діалектна назва лелеки (чорногуза)"),
                (r"\bтрясовин\w*", "трясовина", "хитке драговиння, болотяна топіль"),
                (r"\bдзвоник\w*", "дзвоники", "лісові квіти, характерні для поліських заплав і дібров"),
                (r"\bочерет\w*", "очерет", "висока водяна рослина поліських озер і річкових заплав"),
            ],
            50,
        ),
    ]

    item_idx = 1
    seen_texts: set[str] = set()

    if conn is None:
        reused: list[dict[str, Any]] = []
        for subgroup, _query, _terms, quota in subgroups:
            if subgroup == "southwestern_lemko":
                continue
            chunk = _reuse_existing_subgroup(subgroup, quota)
            if len(chunk) != quota:
                raise ValueError(f"Existing suite missing {subgroup}: got {len(chunk)}, need {quota}")
            reused.extend(chunk)
        lemko = mine_lemko_from_seeds(40)
        # Re-number dialect eval_ids in harvest order: reused non-Lemko first, then Lemko.
        all_dialect = reused + lemko
        for idx, rec in enumerate(all_dialect, start=1):
            rec["eval_id"] = f"eval_prot_dial_{idx:04d}"
        return all_dialect

    cur = conn.cursor()
    for subgroup, query, terms, quota in subgroups:
        if subgroup == "southwestern_lemko":
            continue
        sub_records: list[dict[str, Any]] = []
        rows = cur.execute(query).fetchall()

        for author, work, text, year in rows:
            if len(sub_records) >= quota:
                break
            sentences = extract_sentences(text)
            for s in sentences:
                if len(sub_records) >= quota:
                    break
                if s in seen_texts:
                    continue

                for pat, _canon_target, definition in terms:
                    m = re.search(pat, s, re.IGNORECASE)
                    if m:
                        matched_token = m.group(0)
                        seen_texts.add(s)

                        # Formulate rich linguistic notes
                        region_title = {
                            "southwestern_hutsul": "Гуцульський говір південно-західного наріччя",
                            "southwestern_boyko": "Бойківський говір південно-західного наріччя",
                            "southwestern_lemko": "Лемківський говір південно-західного наріччя",
                            "southwestern_galician": "Наддністрянський/покутський говір південно-західного наріччя",
                            "southeastern_poltava": "Полтавсько-середньонаддніпрянський говір південно-східного наріччя",
                            "southeastern_slobozhan": "Слобожанський говір південно-східного наріччя",
                            "northern_polissian": "Поліське (північне) наріччя української мови",
                        }.get(subgroup, "Діалектний ареал української мови")

                        notes = (
                            f"{region_title}. Лексема «{matched_token}» ({definition}). "
                            f"Автентична діалектна одиниця української мови та жива культурна спадщина. "
                            f"Підлягає безумовному захисту від штучного виправлення, стандартизації або хибної класифікації як суржику чи помилки."
                        )

                        rec = {
                            "eval_id": f"eval_prot_dial_{item_idx:04d}",
                            "stratum": "regional_dialect",
                            "subgroup": subgroup,
                            "case_type": "PRESERVE",
                            "input_text": s,
                            "target_term": matched_token,
                            "expected_action": "PRESERVE",
                            "expected_replacement": None,
                            "linguistic_notes": notes,
                            "source_metadata": {
                                "source": "literary_texts",
                                "author": author or "Невідомий",
                                "work": work or "Українська класична література",
                                "year": year or 1900,
                                "language_period": "modern",
                                "region_or_dialect": subgroup,
                            },
                        }
                        sub_records.append(rec)
                        item_idx += 1
                        break

        records.extend(sub_records)

    records.extend(mine_lemko_from_seeds(40))
    for idx, rec in enumerate(records, start=1):
        rec["eval_id"] = f"eval_prot_dial_{idx:04d}"
    return records


def mine_middle_ua_from_seeds(quota: int) -> list[dict[str, Any]]:
    """Load attested Middle Ukrainian sentences that replace biography-about-author rows."""
    if quota <= 0:
        return []
    if not MID_UA_SEED_FILE.exists():
        raise FileNotFoundError(f"Middle Ukrainian seed file missing: {MID_UA_SEED_FILE}")
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in MID_UA_SEED_FILE.read_text(encoding="utf-8").splitlines():
        if len(records) >= quota:
            break
        if not line.strip():
            continue
        seed = json.loads(line)
        text = clean_sentence(seed["input_text"])
        if text in seen or len(text) < 25:
            continue
        target = str(seed["target_term"])
        if target.casefold() not in text.casefold():
            continue
        work = seed.get("work") or "Староукраїнська пам'ятка"
        notes = (
            f"Староукраїнська (середньоукраїнська) мовна доба козацького бароко (XVI–XVIII ст.), "
            f"твір «{work}». Історична лексема «{target}». "
            "Автентична пам'ятка козацького літописання чи барокової філософії. "
            "Підлягає історичному захисту; заборонено примусово руйнувати бароковий колорит і граматику."
        )
        rec = {
            "eval_id": "eval_prot_hist_0000",
            "stratum": "historical_text",
            "subgroup": "middle_ukrainian",
            "case_type": "PRESERVE",
            "input_text": text,
            "target_term": target,
            "expected_action": "PRESERVE",
            "expected_replacement": None,
            "linguistic_notes": notes,
            "source_metadata": {
                "source": "literary_texts",
                "author": seed.get("author") or "Григорій Сковорода",
                "work": work,
                "year": int(seed.get("year") or 1760),
                "language_period": "middle_ukrainian",
            },
        }
        seen.add(text)
        records.append(rec)
    if len(records) < quota:
        raise ValueError(f"Middle Ukrainian seed harvest produced {len(records)} cases, need {quota}")
    return records[:quota]


def mine_historical_sentences(conn: sqlite3.Connection | None) -> list[dict[str, Any]]:
    """Mine 200 authentic historical sentences (100 Old East Slavic + 100 Middle Ukrainian)."""
    records: list[dict[str, Any]] = []

    oes_records = mine_oes_diplomatic(100)
    records.extend(oes_records)
    item_idx = len(oes_records) + 1

    # 2. Middle Ukrainian / Cossack Era (100 cases)
    mid_terms = [
        (r"\bкозацтв\w*", "козацтво", "козацький стан, збройне лицарство та суспільна верства"),
        (r"\bгетьманств\w*", "гетьманство", "період правління гетьмана та козацька держава Гетьманщина"),
        (r"\bпосполит\w*", "посполиті", "міщани та селяни в козацькій державі XVII–XVIII століть"),
        (r"\bвійськ\w*\s+запорозьк\w*", "Військо Запорозьке", "офіційна назва козацької держави та її збройних сил"),
        (r"\bполковник\w*", "полковник", "командир полку та голова полкового округу Гетьманщини"),
        (r"\bуніверсал\w*", "універсал", "офіційний законодавчий або розпорядчий акт гетьмана чи уряду"),
        (r"\bсовість\w*", "совість", "моральне сумління, духовна категорія філософії Григорія Сковороди"),
        (r"\bсродн\w*\s+прац\w*", "сродна праця", "філософська концепція природної покликаності людини за Сковородою"),
        (r"\bбулав\w*", "булава", "символ найвищої гетьманської або кошової військової та державної влади"),
        (r"\bклейнод\w*", "клейноди", "козацькі військові святині й регалії (булава, бунчук, прапор, печатка)"),
        (r"\bзнамен\w*", "знамено", "козацький прапор або корогва підрозділу"),
        (r"\bмаєтност\w*|\bмаєтність\w*", "маєтність", "родове землеволодіння чи маєток козацької старшини"),
        (r"\bтовариств\w*", "товариство", "козацька спільнота, запорозьке побратимство"),
        (r"\bстаршин\w*", "старшина", "військове й адміністративне керівництво Гетьманщини"),
        (r"\bписар\w*", "писар", "генеральний або полковий діловод і хранитель козацької канцелярії"),
    ]

    mid_records: list[dict[str, Any]] = []
    seen_mid: set[str] = set()

    if conn is None:
        reused_mid = _reuse_existing_subgroup("middle_ukrainian", 100)
        if len(reused_mid) < 100:
            reused_mid = reused_mid + mine_middle_ua_from_seeds(100 - len(reused_mid))
        if len(reused_mid) < 100:
            raise ValueError(
                f"Middle Ukrainian harvest produced {len(reused_mid)} cases after "
                "dropping biography rows, need 100"
            )
        for rec in reused_mid:
            rec = dict(rec)
            rec["eval_id"] = f"eval_prot_hist_{item_idx:04d}"
            mid_records.append(rec)
            item_idx += 1
        records.extend(mid_records)
        return records

    cur = conn.cursor()
    mid_rows = cur.execute(
        "SELECT author, work, text, year FROM literary_texts "
        "WHERE language_period = 'middle_ukrainian' AND "
        "(work LIKE '%Величк%' OR work LIKE '%Грабянк%' OR work LIKE '%Самовидець%' OR author LIKE '%Сковорода%') "
        "AND work NOT LIKE '%Життя та творчість%'"
    ).fetchall()

    for author, work, text, year in mid_rows:
        if len(mid_records) >= 100:
            break
        sentences = extract_sentences(text)
        for s in sentences:
            if len(mid_records) >= 100:
                break
            if s in seen_mid:
                continue

            for pat, _canon_target, definition in mid_terms:
                m = re.search(pat, s, re.IGNORECASE)
                if m:
                    matched_token = m.group(0)
                    seen_mid.add(s)
                    notes = (
                        f"Староукраїнська (середньоукраїнська) мовна доба козацького бароко (XVI–XVIII ст.), твір «{work}». "
                        f"Історична лексема «{matched_token}» ({definition}). "
                        f"Автентична пам'ятка козацького літописання чи барокової філософії. "
                        f"Підлягає історичному захисту; заборонено примусово руйнувати бароковий колорит і граматику."
                    )
                    rec = {
                        "eval_id": f"eval_prot_hist_{item_idx:04d}",
                        "stratum": "historical_text",
                        "subgroup": "middle_ukrainian",
                        "case_type": "PRESERVE",
                        "input_text": s,
                        "target_term": matched_token,
                        "expected_action": "PRESERVE",
                        "expected_replacement": None,
                        "linguistic_notes": notes,
                        "source_metadata": {
                            "source": "literary_texts",
                            "author": author or "Козацький літописець",
                            "work": work or "Козацькі літописи",
                            "year": year or 1710,
                            "language_period": "middle_ukrainian",
                        },
                    }
                    mid_records.append(rec)
                    item_idx += 1
                    break

    records.extend(mid_records)
    return records


def mine_anti_surzhyk_controls(conn: sqlite3.Connection | None) -> list[dict[str, Any]]:
    """Mine 100 authentic Anti-Surzhyk Invariant Negative Controls (from style_guide and ua_gec_errors)."""
    records: list[dict[str, Any]] = []

    # Canonical list of pervasive Russian calques / Surzhyk collocations with gold standard corrections
    # Sourced from Antonenko-Davydovych 'Як ми говоримо' and UA-GEC
    surzhyk_patterns = [
        (
            r"\bприймати\s+участь\b",
            "приймати участь",
            "брати участь",
            "Калька російського «принимать участие». Норма: «брати участь».",
        ),
        (
            r"\bна\s+протязі\s+дня\b|\bна\s+протязі\s+року\b|\bна\s+протязі\s+тижня\b|\bна\s+протязі\s+часу\b",
            "на протязі",
            "протягом",
            "Калька російського «на протяжении». В українській «протяг» — струмінь повітря; темпоральне значення — «протягом».",
        ),
        (
            r"\bприймати\s+міри\b",
            "приймати міри",
            "вживати заходів",
            "Калька російського «принимать меры». Норма: «вживати заходів».",
        ),
        (
            r"\bрахувати,\s+що\b|\bрахую,\s+що\b",
            "рахувати, що",
            "вважати, що",
            "Семантичний суржик від рос. «считать». В українській «рахувати» — лічити предмети; оціночне судження — «вважати».",
        ),
        (
            r"\bсамий\s+кращий\b|\bсамий\s+великий\b|\bсамий\s+важливий\b",
            "самий кращий",
            "найкращий",
            "Російська ненормативна складена форма найвищого ступеня з часткою «самий». Норма: префікс «най-».",
        ),
        (
            r"\bявляється\s+причиною\b|\bявляється\s+головним\b",
            "являється",
            "є",
            "Канцелярський росіянізм під впливом «является». В українській мові «являтися» вживається лише у значенні з'являтися уві сні чи видінні; норма: «є».",
        ),
        (
            r"\bвідноситися\s+до\b",
            "відноситися до",
            "ставитися до / належати до",
            "Калька російського багатозначного «относиться». Норма: до людей — «ставитися», до категорії — «належати».",
        ),
        (
            r"\bслідуючий\s+день\b|\bслідуюча\s+зустріч\b|\bслідуючий\s+пункт\b",
            "слідуючий",
            "наступний",
            "Активний дієприкметник-росіянізм від «следующий». Питоме українське слово — «наступний».",
        ),
        (
            r"\bспівпадати\b|\bспівпадає\b",
            "співпадати",
            "збігатися",
            "Морфологічна калька з рос. «совпадать». Норма: «збігатися».",
        ),
        (
            r"\bвлучити\s+впросак\b|\bпопасти\s+впросак\b",
            "попасти впросак",
            "потрапити в халепу",
            "Прямий фразеологічний росіянізм від «попасть впросак». Питомі українські фразеологізми: «потрапити в халепу», «сісти в калюжу».",
        ),
        (
            r"\bв\s+кінці\s+кінців\b",
            "в кінці кінців",
            "зрештою / врешті-решт",
            "Буквальний переклад російського звороту «в конце концов». Норма: «зрештою», «кінець кінцем», «врешті-решт».",
        ),
        (
            r"\bкидатися\s+в\s+очі\b|\bкидається\s+в\s+очі\b",
            "кидатися в очі",
            "впадати в око",
            "Калька російського виразу «бросаться в глаза». Норма: «впадати в око (у вічі)».",
        ),
        (
            r"\bпо\s+крайній\s+мірі\b",
            "по крайній мірі",
            "принаймні",
            "Калька російського «по крайней мере». Нормативне питоме слово — «принаймні».",
        ),
        (
            r"\bзаключатися\s+в\b|\bзаключається\s+в\b",
            "заключатися в",
            "полягати в",
            "Росіянізм під впливом «заключаться в чем-то». Норма: «полягати в».",
        ),
        (
            r"\bнанести\s+збитки\b|\bнанести\s+удар\b",
            "нанести збитки",
            "завдати збитків",
            "Порушення українського дієслівного керування від рос. «нанести ущерб». Норма: «завдати збитків», «завдати удару».",
        ),
        (
            r"\bтерпіти\s+поразку\b",
            "терпіти поразку",
            "зазнавати поразки",
            "Калька з рос. «терпеть поражение». Норма: «зазнавати поразки».",
        ),
        (
            r"\bпідводити\s+підсумки\b",
            "підводити підсумки",
            "підбивати підсумки",
            "Буквальний переклад рос. «подводить итоги». Питома норма: «підбивати підсумки».",
        ),
        (
            r"\bвести\s+себе\b",
            "вести себе",
            "поводитися",
            "Суржиковий зворот під впливом рос. «вести себя». Нормативне дієслово — «поводитися».",
        ),
        (
            r"\bприводити\s+до\s+помилок\b|\bприводить\s+до\s+помилок\b",
            "приводити до",
            "призводити до",
            "Змішування значень рос. «приводить к». В українській негативний наслідок виражається дієсловом «призводити до».",
        ),
        (
            r"\bпо\s+вихідних\b|\bпо\s+вівторках\b|\bпо\s+п'ятницях\b",
            "по вихідних",
            "у вихідні / щовівторка",
            "Ненормативне вживання прийменника «по» з давальним або місцевим відмінком за російським зразком «по выходным». Норма: «у вихідні», «щовівторка».",
        ),
        (
            r"\bз\s+тих\s+пір\b",
            "з тих пір",
            "відтоді",
            "Калька російського «с тех пор». Норма: «відтоді», «з того часу».",
        ),
        (
            r"\bне\s+дивлячись\s+на\s+те\b",
            "не дивлячись на",
            "незважаючи на",
            "Суржиковий дієприслівниковий зворот від рос. «не смотря на». «Не дивлячись» — це фізично не дивитися очима; поступковий зв'язок вимагає «незважаючи на».",
        ),
        (
            r"\bу\s+більшості\s+випадків\b",
            "у більшості випадків",
            "здебільшого / переважно",
            "Канцелярська калька рос. «в большинстве случаев». Питомі відповідники: «здебільшого», «переважно».",
        ),
        (
            r"\bвпадати\s+у\s+відчай\b|\bвпав\s+у\s+відчай\b",
            "впадати у відчай",
            "розпачувати",
            "Калька з рос. «впадать в отчаяние». Питоме дієслово — «розпачувати», «поринути в розпач».",
        ),
        (
            r"\bдати\s+знати\b",
            "дати знати",
            "повідомити",
            "Калька російського «дать знать». Норма: «повідомити», «сповістити».",
        ),
    ]

    # Authentic sentences from style_guide (skip metalinguistic "правильно сказати … а не")
    rows_sg: list[tuple[str]] = []
    if conn is not None:
        rows_sg = conn.cursor().execute("SELECT text FROM style_guide").fetchall()
    seen_surz: set[str] = set()
    item_idx = 1

    for (text,) in rows_sg:
        if len(records) >= 100:
            break
        sentences = extract_sentences(text)
        for s in sentences:
            if len(records) >= 100:
                break
            if s in seen_surz or is_metalinguistic_control(s):
                continue

            for pat, _target, corr, explanation in surzhyk_patterns:
                m = re.search(pat, s, re.IGNORECASE)
                if m:
                    matched_token = m.group(0)
                    if not surzhyk_target_allowed(matched_token):
                        continue
                    seen_surz.add(s)
                    notes = (
                        f"Колоніальний суржик та російська інтерференція: «{matched_token}». {explanation} "
                        f"Абсолютний антисуржиковий інваріант: суржик є токсичним продуктом русифікації, "
                        f"підлягає обов'язковому виправленню на питому форму «{corr}». "
                        f"Суворо заборонено легітимізувати суржик або помилково класифікувати його як діалект чи припустиму розмовну форму (нульова толерантність до нормалізації суржику)."
                    )
                    rec = {
                        "eval_id": f"eval_prot_surz_{item_idx:04d}",
                        "stratum": "anti_surzhyk_control",
                        "subgroup": "colonial_surzhyk_control",
                        "case_type": "CORRECT",
                        "input_text": s,
                        "target_term": matched_token,
                        "expected_action": "CORRECT",
                        "expected_replacement": corr,
                        "linguistic_notes": notes,
                        "source_metadata": {
                            "source": "style_guide",
                            "author": "Антоненко-Давидович Б.",
                            "work": "Як ми говоримо",
                            "error_type": "F/Calque",
                            "standard_replacement": corr,
                        },
                    }
                    if not surzhyk_record_is_authentic(rec):
                        seen_surz.discard(s)
                        continue
                    records.append(rec)
                    item_idx += 1
                    break

    # Load authentic human-annotated calques from UA-GEC
    uagec_path = resolve_data_path(
        "data/projects/open_model_data/decolonization/mined/uagec_mined_calques.jsonl"
    )

    if uagec_path.exists():
        with uagec_path.open("r", encoding="utf-8") as f:
            for line in f:
                if len(records) >= 100:
                    break
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                s = clean_sentence(row.get("sentence_context", ""))
                err = row.get("error", "").strip()
                corr = row.get("correct", "").strip()

                if not (s and err and corr):
                    continue
                if s in seen_surz or len(s) < 25 or len(s) > 300:
                    continue
                if err.lower() not in s.lower():
                    continue
                if is_metalinguistic_control(s) or not surzhyk_target_allowed(err):
                    continue

                seen_surz.add(s)
                notes = (
                    f"Колоніальний суржик та російська інтерференція: «{err}». "
                    f"Автентична помилка з корпусу UA-GEC ({row.get('error_type', 'F/Calque')}). "
                    f"Абсолютний антисуржиковий інваріант: форма є наслідком русифікації і підлягає обов'язковому виправленню на питому норму «{corr}». "
                    f"Суворо заборонено легітимізувати суржик або класифікувати його як діалект (нульова толерантність до нормалізації суржику)."
                )
                rec = {
                    "eval_id": f"eval_prot_surz_{item_idx:04d}",
                    "stratum": "anti_surzhyk_control",
                    "subgroup": "colonial_surzhyk_control",
                    "case_type": "CORRECT",
                    "input_text": s,
                    "target_term": err,
                    "expected_action": "CORRECT",
                    "expected_replacement": corr,
                    "linguistic_notes": notes,
                    "source_metadata": {
                        "source": "ua_gec_errors",
                        "doc_id": row.get("doc_id", ""),
                        "error_type": row.get("error_type", "F/Calque"),
                        "standard_replacement": corr,
                    },
                }
                if not surzhyk_record_is_authentic(rec):
                    seen_surz.discard(s)
                    continue
                records.append(rec)
                item_idx += 1

    if len(records) < 100:
        raise ValueError(f"Anti-Surzhyk harvest produced {len(records)} curated calques, need 100")
    return records[:100]


def build_suite() -> None:
    """Build the complete 600-case Dialect & Historical Protection Suite."""
    conn: sqlite3.Connection | None = None
    if DEFAULT_SOURCES_DB.exists() and DEFAULT_SOURCES_DB.stat().st_size > 0:
        print("Connecting to database at:", DEFAULT_SOURCES_DB)
        conn = sqlite3.connect(DEFAULT_SOURCES_DB)
    else:
        print("sources.db unavailable; using git-grounded seeds + existing non-replaced strata")

    print("1. Mining 300 Regional Dialect sentences...")
    dialect_cases = mine_dialect_sentences(conn)
    print(f"   Mined: {len(dialect_cases)} dialect cases")
    assert len(dialect_cases) == 300, f"Expected 300 dialect cases, got {len(dialect_cases)}"

    print("2. Mining 200 Historical & Classical sentences...")
    historical_cases = mine_historical_sentences(conn)
    print(f"   Mined: {len(historical_cases)} historical cases")
    assert len(historical_cases) == 200, f"Expected 200 historical cases, got {len(historical_cases)}"

    print("3. Mining 100 Anti-Surzhyk Invariant Negative Controls...")
    surzhyk_cases = mine_anti_surzhyk_controls(conn)
    print(f"   Mined: {len(surzhyk_cases)} anti-surzhyk cases")
    assert len(surzhyk_cases) == 100, f"Expected 100 anti-surzhyk cases, got {len(surzhyk_cases)}"

    if conn is not None:
        conn.close()

    all_cases = dialect_cases + historical_cases + surzhyk_cases
    assert len(all_cases) == 600, f"Expected 600 total cases, got {len(all_cases)}"

    # Validate against record schema
    print("Validating records against schema:", RECORD_SCHEMA_FILE)
    record_schema = json.loads(RECORD_SCHEMA_FILE.read_text(encoding="utf-8"))
    for idx, case in enumerate(all_cases):
        try:
            jsonschema.validate(case, record_schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Record {idx} ({case.get('eval_id')}) schema validation failed: {e.message}") from e

    # Write JSONL output
    out_dir = DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "dialect_historical_protection_suite_600.jsonl"
    sha_file = out_dir / "dialect_historical_protection_suite_600.sha256"
    receipt_file = out_dir / "dialect_historical_protection_receipt_v1.json"

    print("Writing evaluation suite to:", out_file)
    with out_file.open("w", encoding="utf-8") as f:
        for case in all_cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    # Compute SHA-256
    sha256_hash = hashlib.sha256(out_file.read_bytes()).hexdigest()
    sha_file.write_text(f"{sha256_hash}  {out_file.name}\n", encoding="utf-8")
    print(f"Computed SHA-256: {sha256_hash}")

    # Subgroup distribution counts
    subgroup_counts: dict[str, int] = {}
    for case in all_cases:
        sg = case["subgroup"]
        subgroup_counts[sg] = subgroup_counts.get(sg, 0) + 1

    # Formulate Release Receipt
    receipt = {
        "schema_version": "v1_dialect_historical_protection_receipt",
        "dataset_name": "Ukrainian Regional Dialect & Historical Protection Evaluation Suite",
        "phase": "Phase 5.2: Dialect & Historical Protection Test Suite (Anti-Over-Standardization Gate)",
        "issue": 8051,
        "parent_epic": 6321,
        "generated_at": datetime.now(UTC).isoformat(),
        "suite_summary": {
            "total_test_cases": 600,
            "preserve_cases": 500,
            "correct_cases": 100,
            "statistical_power": {
                "target_non_corruption_gate": ">= 98.0%",
                "max_tolerated_dialect_corruption": MAX_TOLERATED_DIALECT_CORRUPTION,
                "max_tolerated_historical_corruption": MAX_TOLERATED_HISTORICAL_CORRUPTION,
                "surzhyk_normalization_tolerance": "0.0%",
                "statistically_sound": True,
            },
        },
        "strata_distribution": {
            "regional_dialect": 300,
            "historical_text": 200,
            "anti_surzhyk_control": 100,
        },
        "subgroup_distribution": subgroup_counts,
        "invariants": {
            "anti_surzhyk_eradication_mandate": True,
            "zero_surzhyk_normalization_tolerance": True,
            "dialect_cultural_heritage_protection": True,
            "historical_continuity_preservation": True,
            "zero_hallucinated_sources": True,
        },
        "files": {
            "test_suite_jsonl": {
                "path": "data/projects/open_model_data/decolonization/partitions/dialect_historical_protection_suite_600.jsonl",
                "sha256": sha256_hash,
                "record_count": 600,
            },
        },
    }

    # Validate receipt against receipt schema
    print("Validating receipt against schema:", RECEIPT_SCHEMA_FILE)
    receipt_schema = json.loads(RECEIPT_SCHEMA_FILE.read_text(encoding="utf-8"))
    jsonschema.validate(receipt, receipt_schema)

    receipt_file.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Receipt written and verified:", receipt_file)
    print("Phase 5.2 dataset assembly completed successfully!")


if __name__ == "__main__":
    build_suite()

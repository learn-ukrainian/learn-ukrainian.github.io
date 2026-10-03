#!/usr/bin/env python3
"""Per-component holdings manifest for the open-model-data plan (#9609, PA2).

For every source the plan's components C1–C9 and its rulers draw on, record what
is held: the store and the exact row selection, the row count, a SHA-256 over the
rows used, and provenance (origin, edition, the origin-file hash where one was
recorded, the ingest code).  No source text is written, only counts and hashes.

Row hash: SHA-256 over the selected rows in primary-key order, one line per row,
each line ``json.dumps(list(row), ensure_ascii=False, separators=(",", ":"))``
followed by ``\\n``.  File hash (UA-GEC): SHA-256 over sorted lines
``<path relative to the clone>\\t<sha256 of the file>\\n``.

Databases are opened read-only.  Write the manifest:

    .venv/bin/python -m scripts.projects.open_model_data.holdings_manifest \\
        --sources-db PATH --vesum-db PATH --ua-gec PATH [--output PATH]

``--check`` recomputes and exits non-zero when any count or hash differs from the
committed manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / "registry" / "projects" / "open_model_data" / "sources" / "holdings_manifest.yaml"
ROW_HASH_SCHEME = "sha256(jsonl rows in primary-key order; compact separators; ensure_ascii=False)"
FILE_HASH_SCHEME = "sha256(sorted '<relative path>\\t<file sha256>\\n' lines)"
COMPONENTS = ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "rulers")


@dataclass(frozen=True)
class Holding:
    id: str
    components: tuple[str, ...]
    role: str
    store: str  # "sources.db" | "vesum.db" | "ua-gec"
    selection: str  # SQL for databases; a glob relative to the clone for "ua-gec"
    origin: str
    edition: str
    provenance: dict[str, Any] = field(default_factory=dict)
    register_id: str = ""
    notes: tuple[str, ...] = ()


_ULIF_PROVENANCE = {
    "origin_url": "https://lcorp.ulif.org.ua/dictua/",
    "ingest_code": [
        "scripts/wiki/sources_db.py (store_ulif_dictua_entry)",
        "scripts/lexicon/tools/import_ulif_dump.py",
    ],
    "per_row_hash": "ulif_dictua_entries.response_sha256 / content_sha256",
}
_ULIF_EDITION = "Словники України online (УМІФ НАН України), retrieved 2026-09; parser ulif-dictua-v2"
_UA_GEC_PROVENANCE = {
    "origin_url": "https://github.com/grammarly/ua-gec",
    "clone_commit": "4757f72f192c4a41e4c8fb1d9690a948f87cf6d6",
    "licence": "CC BY 4.0",
    "citation": "UA-GEC (Syvokon, Nahorna, Kuchmiichuk, Osidach, UNLP 2023)",
}
_UA_GEC_EDITION = "UA-GEC 2.0 (clone commit 4757f72f, 2024-02-11)"

HOLDINGS: tuple[Holding, ...] = (
    Holding(
        id="ua_gec_gec_only_train",
        components=("C1",),
        role="human corrections (training pool; dev is carved from it by E9)",
        store="ua-gec",
        selection="data/gec-only/train/annotated/*.ann",
        origin="UA-GEC corpus, gec-only layer, official train partition",
        edition=_UA_GEC_EDITION,
        provenance=_UA_GEC_PROVENANCE,
        register_id="ua_gec",
    ),
    Holding(
        id="ua_gec_gec_fluency_train",
        components=("C6",),
        role="F/Calque human correction edits (training pool); F/* tags exist only in this layer",
        store="ua-gec",
        selection="data/gec-fluency/train/annotated/*.ann",
        origin="UA-GEC corpus, gec-fluency layer, official train partition",
        edition=_UA_GEC_EDITION,
        provenance=_UA_GEC_PROVENANCE,
        register_id="ua_gec",
    ),
    Holding(
        id="ua_gec_test_ruler",
        components=("rulers",),
        role="UA-GEC test split (C1 ruler; C6 F/Calque ruler); never training",
        store="ua-gec",
        selection="data/*/test/annotated/*.ann",
        origin="UA-GEC corpus, both layers, official test partition",
        edition=_UA_GEC_EDITION,
        provenance=_UA_GEC_PROVENANCE,
        register_id="ua_gec",
    ),
    Holding(
        id="ua_gec_errors_table",
        components=("C1", "C6"),
        role="sources.db extraction of UA-GEC edits used by the miners; partition column carries the split",
        store="sources.db",
        selection="SELECT * FROM ua_gec_errors ORDER BY id",
        origin="derived from the UA-GEC clone by scripts/ingest/ua_gec_ingest.py",
        edition=_UA_GEC_EDITION,
        provenance={**_UA_GEC_PROVENANCE, "ingest_code": "scripts/ingest/ua_gec_ingest.py"},
        register_id="ua_gec",
    ),
    Holding(
        id="vesum_forms_all",
        components=("C2", "C7"),
        role="forms backbone (VESUM side of the P3 agreement); Russification contrast",
        store="vesum.db",
        selection="SELECT * FROM forms_all ORDER BY id",
        origin="brown-uk/dict_uk release asset dict_corp_vis.txt.bz2",
        edition="VESUM v6.8.0 (upstream commit bcb5ccd9585a79dbbbb7c8c5e241adcd8a64f824)",
        provenance={
            "origin_url": "https://github.com/brown-uk/dict_uk/releases/download/v6.8.0/dict_corp_vis.txt.bz2",
            "origin_file_sha256": "e33803783ac138e6f3af2cf0e9428ba146c0ecfda7f5c41fe83ae00c7af24be9",
            "canonical_jsonl_sha256": "53923150073b4fc7bee419fe7b071acbe17b6a9aba76cfb2d0336c95f5188680",
            "lock": "scripts/config/vesum_source.lock.json",
            "ingest_code": "scripts/rag/vesum_reingest.py",
            "licence": "CC BY-NC-SA 4.0",
        },
        register_id="vesum",
    ),
    Holding(
        id="ulif_paradigm_sections",
        components=("C2",),
        role="forms backbone (ULIF side of the P3 agreement)",
        store="sources.db",
        selection="SELECT * FROM ulif_dictua_sections WHERE kind = 'paradigm' ORDER BY id",
        origin="ULIF «Словники України» online, paradigm sections",
        edition=_ULIF_EDITION,
        provenance=_ULIF_PROVENANCE,
        register_id="ulif",
    ),
    Holding(
        id="ulif_register_entries_ok",
        components=("C2", "C3", "C4", "C7"),
        role="ULIF register (headword, homonym, gloss) behind every ULIF section",
        store="sources.db",
        selection="SELECT * FROM ulif_dictua_entries WHERE status = 'ok' ORDER BY id",
        origin="ULIF «Словники України» online, register entries",
        edition=_ULIF_EDITION,
        provenance=_ULIF_PROVENANCE,
        register_id="ulif",
    ),
    Holding(
        id="ulif_forms",
        components=("C2",),
        role="stressed forms (stress facet)",
        store="sources.db",
        selection="SELECT * FROM ulif_forms ORDER BY id",
        origin="derived from ULIF paradigm sections by scripts/lexicon/runner/ulif_forms.py",
        edition="build ulif-forms-v4 (ulif_forms_build.source_fingerprint "
        "d1d1a93417fe55ec1be950956138089d98d3604c9a85b22603ff577cc594bf12; 59 failed entries)",
        provenance={**_ULIF_PROVENANCE, "ingest_code": "scripts/lexicon/runner/ulif_forms.py"},
        register_id="ulif",
    ),
    Holding(
        id="ulif_synonym_sections",
        components=("C3",),
        role="synonym groups",
        store="sources.db",
        selection="SELECT * FROM ulif_dictua_sections WHERE kind = 'synonyms' ORDER BY id",
        origin="ULIF «Словники України» online, synonym sections",
        edition=_ULIF_EDITION,
        provenance=_ULIF_PROVENANCE,
        register_id="ulif",
    ),
    Holding(
        id="ulif_antonym_sections",
        components=("C3",),
        role="antonym groups",
        store="sources.db",
        selection="SELECT * FROM ulif_dictua_sections WHERE kind = 'antonyms' ORDER BY id",
        origin="ULIF «Словники України» online, antonym sections",
        edition=_ULIF_EDITION,
        provenance=_ULIF_PROVENANCE,
        register_id="ulif",
    ),
    Holding(
        id="ulif_phraseology_sections",
        components=("C4",),
        role="idioms with definitions",
        store="sources.db",
        selection="SELECT * FROM ulif_dictua_sections WHERE kind = 'phraseology' ORDER BY id",
        origin="ULIF «Словники України» online, phraseology sections",
        edition=_ULIF_EDITION,
        provenance=_ULIF_PROVENANCE,
        register_id="ulif",
    ),
    Holding(
        id="frazeolohichnyi",
        components=("C4",),
        role="idioms with definitions and citations",
        store="sources.db",
        selection="SELECT id, word, definition, text, source FROM frazeolohichnyi ORDER BY id",
        origin="electronic export «Український Фразелогічний Словник» (MS Access XML generated 2008-07-11), "
        "redistributed in github.com/bakustarver/ukr-dictionaries-list-opensource as fl.frasesUkUk.json",
        edition="Словник фразеологізмів української мови / уклад. В. М. Білоноженко, І. С. Гнатюк, В. В. Дятчук, "
        "Н. М. Неровня, Т. О. Федоренко; відп. ред. В. О. Винник. Київ: Наукова думка, 2003. ISBN 966-00-0797-3 "
        "(one volume; verified, see frazeolohichnyi_edition.yaml)",
        provenance={
            "origin_url": "https://github.com/bakustarver/ukr-dictionaries-list-opensource",
            "origin_files_sha256": {
                "frazeolohichnyi.zip": "ac27911e87f13f8aa60f35f5e70d2903f728d19193c29bfd17856db0cba4a023",
                "fl.frasesUkUk.json": "2622a86c158cc696007ac8489a9a0c9c6dc3ab2df557d7e0968b662083c161d1",
                "chunks.jsonl": "3ed99de6f462e293ad79db835ad499978d5b696ec8151f883ef729b989a48d84",
            },
            "ingest_code": [
                "scripts/rag/convert_dictionaries.py --frazeolohichnyi",
                "scripts/wiki/build_sources_db.py",
            ],
            "edition_evidence": "registry/projects/open_model_data/sources/frazeolohichnyi_edition.yaml",
        },
        register_id="frazeolohichnyi",
    ),
    Holding(
        id="pravopys_2019_paragraphs",
        components=("C5",),
        role="spelling rules with their printed examples (§ locator)",
        store="sources.db",
        selection="SELECT * FROM pravopys_paragraphs ORDER BY source_id, number",
        origin="official PDF published by УМІФ НАН України (ulif.org.ua)",
        edition="Український правопис. Авторизоване видання 2019 р. Київ: Наукова думка, 2019. 392 с. "
        "ISBN 978-966-00-1728-3",
        provenance={
            "origin_url": "https://www.ulif.org.ua/system/files/pravopus-new.pdf",
            "origin_file_sha256": "0d2fd75a2e9b2a412d4c8e072f6a8cac06d075a297a770fd037312054b0e501a",
            "retrieved": "2026-10-03T15:53:24Z",
            "ingest_code": "scripts/ingest/pravopys_2019_ingest.py (parser pravopys_2019_pdf_v3)",
            "source_note": "docs/sources/pravopys-2019-official-source.md",
        },
        register_id="pending:pravopys_2019",
    ),
    Holding(
        id="pohribnyi_1992_ocr_pages",
        components=("C8",),
        role="literary pronunciation; current rows are Tesseract OCR, superseded by the E3c transcription",
        store="sources.db",
        selection="SELECT * FROM textbooks WHERE source_file = 'pohribnyi-ukrainska-literaturna-vymova-1992' "
        "ORDER BY id",
        origin="scan of the printed booklet (28 pp.) held in the private data mirror",
        edition="Погрібний М. І. Українська літературна вимова. Дніпропетровськ: агентство «TRANSFORM», 1992. 28 с.",
        provenance={
            "origin_file_sha256": "5ea396063526800ebe095d0e8dc99477caf56964bf0ecbe13f14995c750e1555",
            "ingest_code": ["scripts/ingest/pohribnyi_pronunciation_ingest.py", "scripts/ingest/pohribnyi_tooling.py"],
        },
        register_id="pending:pohribnyi_1992",
        notes=("Not a record source until E3c replaces the OCR rows with the adjudicated transcription.",),
    ),
    Holding(
        id="antonenko_book_chunks",
        components=("C6",),
        role="calque pairs named by the book itself (row locator)",
        store="sources.db",
        selection="SELECT * FROM textbooks WHERE source_file = 'antonenko-davydovych-yak-my-hovorymo' ORDER BY id",
        origin="full text of «Як ми говоримо», chunked",
        edition="unverified: the edition of «Як ми говоримо» is recorded neither by the ingest code nor the register",
        provenance={"ingest_code": "scripts/ingest/antonenko_full_book_ingest.py"},
        register_id="antonenko_style_guide",
    ),
    Holding(
        id="antonenko_style_guide_index",
        components=("C6",),
        role="structured index of the same book (word, section, page)",
        store="sources.db",
        selection="SELECT * FROM style_guide ORDER BY id",
        origin="structured index over «Як ми говоримо»",
        edition="unverified: the edition of «Як ми говоримо» is recorded neither by the ingest code nor the register",
        register_id="antonenko_style_guide",
    ),
    Holding(
        id="sum11_contrast",
        components=("C7",),
        role="Russification evidence only (opt-in subset); never a norm",
        store="sources.db",
        selection="SELECT * FROM sum11 ORDER BY id",
        origin="СУМ-11 digitisation (see register entry sum11)",
        edition="Словник української мови в 11 томах. Київ: Наукова думка, 1970–1980",
        register_id="sum11",
    ),
    Holding(
        id="textbook_sections",
        components=("C9",),
        role="verbatim textbook sections (school grades 1–11 and university)",
        store="sources.db",
        selection="SELECT * FROM textbook_sections ORDER BY section_id",
        origin="school and university textbooks (per-file provenance in register entry textbooks)",
        edition="per source_file; see register entry textbooks",
        provenance={
            "ingest_code": ["scripts/wiki/extract_sections.py", "scripts/ingest/incremental_textbook_ingest.py"]
        },
        register_id="textbooks",
    ),
    Holding(
        id="sum20_live_articles",
        components=("C3", "C4"),
        role="meaning facet (checking); quarantined rows excluded",
        store="sources.db",
        selection="SELECT * FROM sum20_articles WHERE quarantine_reason = '' ORDER BY id",
        origin="sum20ua.com official article pages, crawled by wordid",
        edition="Словник української мови у 20 томах (УМІФ НАН України; Інститут мовознавства ім. О. О. Потебні)",
        provenance={"ingest_code": "scripts/ingest/sum20_official_ingest.py (parser sum20_official_v1)"},
        register_id="sum20",
    ),
    Holding(
        id="sum20_quarantined_articles",
        components=(),
        role="quarantined: unestablished provenance (#9609); never a source",
        store="sources.db",
        selection="SELECT * FROM sum20_articles WHERE quarantine_reason != '' ORDER BY id",
        origin="unknown: parser v1-official-codification has no ingest code in the repository history",
        edition="unverifiable",
        provenance={"quarantine_code": "scripts/ingest/sum20_quarantine_unverified.py"},
        register_id="sum20",
    ),
    Holding(
        id="vts_entries",
        components=("C3", "C4"),
        role="meaning facet, checking only (unofficial copy)",
        store="sources.db",
        selection="SELECT * FROM slovnyk_me_entries WHERE dictionary_slug = 'vts' ORDER BY id",
        origin="slovnyk.me copy of ВТС",
        edition="unverified: the slovnyk.me copy of ВТС does not state its print edition (checking role only)",
        provenance={"ingest_code": "scripts/ingest/slovnyk_me_ingest.py"},
        register_id="slovnyk_me",
    ),
    Holding(
        id="esum_etymology",
        components=("C7",),
        role="etymology facet",
        store="sources.db",
        selection="SELECT rowid, lemma, etymology_text, cognates, vol, page FROM esum_etymology ORDER BY rowid",
        origin="ЕСУМ digitisation (see register entry esum)",
        edition="Етимологічний словник української мови, vols 1–6 (1982–2012), OCR of archive.org items etslukrmov1–6",
        provenance={"ingest_code": ["scripts/ingest/esum_ingest.py", "scripts/ingest/esum_load.py"]},
        register_id="esum",
    ),
    Holding(
        id="zno_keyed_tasks",
        components=("rulers",),
        role="1,616 keyed exam tasks (own-statement essay tasks excluded); never training",
        store="sources.db",
        selection="SELECT * FROM zno_tasks WHERE task_format != 'own-statement' ORDER BY id",
        origin="zno.osvita.ua online test pages (one per session), linked to the official booklet metadata",
        edition="ЗНО 2010–2021 and НМТ 2022–2025 Ukrainian-language tests (УЦОЯО), 33 sessions",
        provenance={
            "origin_url_pattern": "https://zno.osvita.ua/{ukrainian|ukrmova}/{test_id}/",
            "ingest_code": "scripts/ingest/zno_ingest.py (ONLINE_TEST_MAPPING)",
            "origin_file_sha256": None,
        },
        register_id="pending:zno_nmt",
        notes=(
            "No origin hash: zno_documents.sha256 is empty for all 33 booklets and the fetched test pages "
            "(tmp/zno_cache) were not retained; the row hash is the only fixity.",
            "61 tasks belong to a booklet marked fetch_status 'dead' and 61 to one marked 'wrong-content'; "
            "their tasks come from the online test pages, not the booklet PDF.",
        ),
    ),
    Holding(
        id="zno_documents",
        components=("rulers",),
        role="booklet metadata behind the exam tasks",
        store="sources.db",
        selection="SELECT * FROM zno_documents ORDER BY id",
        origin="osvita.ua / zno.osvita.ua / testportal.gov.ua booklet URLs",
        edition="33 booklets, 2010–2025",
        provenance={"ingest_code": "scripts/ingest/zno_ingest.py (BOOKLETS)"},
        register_id="pending:zno_nmt",
    ),
)

# Rulers the plan names that are not built yet: recorded so the denominator is complete.
NOT_YET_BUILT: tuple[dict[str, str], ...] = (
    {
        "id": "protection_cases",
        "components": "rulers",
        "status": "not built; protection cases from authentic literary/regional text are sealed by E9",
    },
)


def _row_digest(rows: Iterable[tuple[Any, ...]]) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    for row in rows:
        digest.update(json.dumps(list(row), ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
        count += 1
    return count, digest.hexdigest()


def measure_rows(conn: sqlite3.Connection, selection: str) -> dict[str, Any]:
    cursor = conn.execute(selection)
    columns = [description[0] for description in cursor.description]
    count, digest = _row_digest(iter(cursor.fetchone, None))
    return {"rows": count, "rows_sha256": digest, "columns": columns}


_CALQUE_TAG = re.compile(r":::error_type=F/Calque(?=[}:])")


def measure_files(root: Path, pattern: str) -> dict[str, Any]:
    files = sorted(root.glob(pattern))
    lines = []
    calque_edits = 0
    documents: set[str] = set()  # UA-GEC file names are <doc id>.<annotator>.ann
    for path in files:
        data = path.read_bytes()
        lines.append(f"{path.relative_to(root).as_posix()}\t{hashlib.sha256(data).hexdigest()}\n")
        calque_edits += len(_CALQUE_TAG.findall(data.decode("utf-8")))
        documents.add(path.name.split(".")[0])
    return {
        "files": len(files),
        "documents": len(documents),
        "f_calque_edits": calque_edits,
        "files_sha256": hashlib.sha256("".join(lines).encode("utf-8")).hexdigest(),
    }


def _open_read_only(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)


def build_manifest(sources_db: Path, vesum_db: Path, ua_gec: Path, *, measured_at: str) -> dict[str, Any]:
    connections = {"sources.db": _open_read_only(sources_db), "vesum.db": _open_read_only(vesum_db)}
    try:
        holdings = []
        for holding in HOLDINGS:
            if holding.store == "ua-gec":
                measured = measure_files(ua_gec, holding.selection)
            else:
                measured = measure_rows(connections[holding.store], holding.selection)
            holdings.append(
                {
                    "id": holding.id,
                    "components": list(holding.components),
                    "role": holding.role,
                    "store": holding.store,
                    "selection": holding.selection,
                    **measured,
                    "origin": holding.origin,
                    "edition": holding.edition,
                    "provenance": holding.provenance,
                    "register_id": holding.register_id,
                    "notes": list(holding.notes),
                }
            )
    finally:
        for conn in connections.values():
            conn.close()
    return {
        "schema_version": 1,
        "issue": "#9609",
        "plan": "docs/projects/open-model-data/PLAN.md v3.4.4 (P2, PA2)",
        "measured_at": measured_at,
        "row_hash_scheme": ROW_HASH_SCHEME,
        "file_hash_scheme": FILE_HASH_SCHEME,
        "components": list(COMPONENTS),
        "holdings": holdings,
        "not_yet_built": list(NOT_YET_BUILT),
    }


_MEASURED_KEYS = ("rows", "rows_sha256", "files", "documents", "f_calque_edits", "files_sha256")


def drift(committed: dict[str, Any], fresh: dict[str, Any]) -> list[str]:
    """Holdings whose counts or hashes differ between two manifests."""
    old = {holding["id"]: holding for holding in committed["holdings"]}
    problems = []
    for holding in fresh["holdings"]:
        before = old.get(holding["id"])
        if before is None:
            problems.append(f"{holding['id']}: not in the committed manifest")
            continue
        for key in _MEASURED_KEYS:
            if before.get(key) != holding.get(key):
                problems.append(f"{holding['id']}: {key} {before.get(key)!r} -> {holding.get(key)!r}")
    problems += [f"{key}: missing from the fresh manifest" for key in old.keys() - {h["id"] for h in fresh["holdings"]}]
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sources-db", type=Path, required=True, help="sources.db (opened read-only)")
    parser.add_argument("--vesum-db", type=Path, required=True, help="vesum.db (opened read-only)")
    parser.add_argument("--ua-gec", type=Path, required=True, help="UA-GEC clone root")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="manifest path")
    parser.add_argument("--measured-at", required=True, help="UTC timestamp to record (from `date -u`)")
    parser.add_argument("--check", action="store_true", help="compare with the committed manifest; write nothing")
    args = parser.parse_args(argv)
    fresh = build_manifest(args.sources_db, args.vesum_db, args.ua_gec, measured_at=args.measured_at)
    if args.check:
        problems = drift(yaml.safe_load(args.output.read_text(encoding="utf-8")), fresh)
        for problem in problems:
            print(problem, file=sys.stderr)
        print("OK: holdings match the manifest" if not problems else f"DRIFT: {len(problems)} holdings changed")
        return 1 if problems else 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "# Generated by scripts/projects/open_model_data/holdings_manifest.py (#9609). Counts and hashes only.\n"
        + yaml.safe_dump(fresh, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    print(f"wrote {len(fresh['holdings'])} holdings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

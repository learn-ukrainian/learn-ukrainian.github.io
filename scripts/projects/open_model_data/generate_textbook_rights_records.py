#!/usr/bin/env python3
"""generate_textbook_rights_records.py - Generate textbook rights and copyright registry.

Part of Sovereign Ukrainian NLP Dataset Roadmap (Epic #6321, Issue #8341).
Governs rights, licensing terms, and pedagogical synthesis mandates for all
195 MOES-approved school textbooks in data/sources.db.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.projects.open_model_data.paths import REGISTRY_TEXTBOOKS_DIR


def resolve_data_path(rel_path: str) -> Path:
    """Resolve a relative data path, falling back to git common dir for gitignored files."""
    local_p = PROJECT_ROOT / rel_path
    if local_p.exists() and (local_p.is_dir() or local_p.stat().st_size > 0):
        return local_p
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).strip()
        git_dir = Path(common)
        root = git_dir.parent if git_dir.name == ".git" else git_dir.parent.parent
        candidate = root / rel_path
        if candidate.exists():
            return candidate
    except Exception:
        pass
    return local_p


DEFAULT_SOURCES_DB = resolve_data_path("data/sources.db")
DEFAULT_YAML_OUT = REGISTRY_TEXTBOOKS_DIR / "textbook_rights_records.yaml"
DEFAULT_JSON_OUT = REGISTRY_TEXTBOOKS_DIR / "textbook_rights_records.json"

KNOWN_PUBLISHERS = [
    "Генеза", "Ранок", "Оріон", "Освіта", "Грамота", "Астон", "Богдан",
    "Літера", "Педагогічна думка", "Алатон", "Сиція", "Школяр", "Перун",
    "Гімназія", "Академія", "Світ", "Букрек", "Картографія", "Майстер-клас",
]
PUB_REGEX = re.compile(r"\b(" + "|".join(KNOWN_PUBLISHERS) + r")\b", re.IGNORECASE)


def detect_publisher(cur: sqlite3.Cursor, source_file: str) -> str:
    """Detect publisher from imprint chunk texts."""
    texts = cur.execute(
        "SELECT text FROM textbooks WHERE source_file = ? LIMIT 6",
        (source_file,),
    ).fetchall()
    for (t,) in texts:
        m = PUB_REGEX.search(t)
        if m:
            val = m.group(1).capitalize()
            # Normalize casing
            for kp in KNOWN_PUBLISHERS:
                if kp.lower() == val.lower():
                    return kp
    return "Видавництво МОН України"


def build_rights_registry(db_path: Path = DEFAULT_SOURCES_DB) -> dict[str, Any]:
    """Build the comprehensive rights registry for all textbooks in the database."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT source_file, coalesce(author_uk, author, '') as author, subject, grade, count(*) as chunk_count
        FROM textbooks
        GROUP BY source_file
        ORDER BY subject, grade, source_file
    """).fetchall()

    records: list[dict[str, Any]] = []
    for src_file, author, subject, grade, chunk_count in rows:
        pub = detect_publisher(cur, src_file)
        author_clean = (author or "").strip()
        if not author_clean or author_clean == "private_teacher_lesson":
            author_clean = "Невідомий автор / МОН України"

        rec: dict[str, Any] = {
            "source_file": src_file,
            "author": author_clean,
            "subject": subject if subject else "загальний",
            "grade": str(grade) if grade else "",
            "chunk_count": chunk_count,
            "publisher": pub,
            "copyright_status": "in_copyright",
            "verbatim_reproduction_allowed": False,
            "explanation_synthesis_allowed": True,
            "attribution_required": True,
            "legal_basis": (
                "Law of Ukraine 'On Copyright and Related Rights' (No. 2811-IX) Arts. 22, 28 "
                "(educational fair use and conceptual synthesis; verbatim bulk copying prohibited)"
            ),
            "pedagogical_mandate": (
                "Dataset examples must explain concepts in original words, synthesize reasoning, "
                "and avoid verbatim copying of textbook passages."
            ),
        }
        records.append(rec)

    conn.close()

    registry_data: dict[str, Any] = {
        "schema_version": "textbook_rights_records_v1",
        "governing_issue": 8341,
        "parent_epic": 6321,
        "legal_framework": "Law of Ukraine 'On Copyright and Related Rights' (No. 2811-IX) Arts. 22, 28",
        "default_policy": {
            "copyright_status": "in_copyright",
            "verbatim_reproduction_allowed": False,
            "explanation_synthesis_allowed": True,
            "attribution_required": True,
            "pedagogical_mandate": (
                "Dataset examples must explain concepts in original words, synthesize reasoning, "
                "and avoid verbatim copying of textbook passages."
            ),
        },
        "total_textbooks": len(records),
        "textbooks": records,
    }
    return registry_data


def write_rights_registry(
    data: dict[str, Any],
    yaml_path: Path = DEFAULT_YAML_OUT,
    json_path: Path = DEFAULT_JSON_OUT,
) -> None:
    """Write the rights registry data to YAML and JSON destinations."""
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    with yaml_path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    logger.info("Wrote rights registry YAML to %s", yaml_path)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    logger.info("Wrote rights registry JSON to %s", json_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate textbook rights records.")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--yaml-out", type=Path, default=DEFAULT_YAML_OUT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_OUT)
    args = parser.parse_args()

    data = build_rights_registry(args.db_path)
    write_rights_registry(data, args.yaml_out, args.json_out)
    print(f"Successfully generated rights records for {data['total_textbooks']} textbooks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

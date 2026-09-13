#!/usr/bin/env python3
"""ULDR Phase 3.1: Textbook & ZNO Contrast Miner (Issue #8006).

Extracts authentic, human-authored contrastive tables and exam distractors from
local Ukrainian textbook chunks and official ZNO/NMT exam tasks in sources.db.
Enforces 100% human source custody and partition firewall boundaries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.projects.open_model_data.phase3_decolonization_partition import extract_root_family


def resolve_data_path(rel_path: str) -> Path:
    """Resolve a relative data path, falling back to git common dir for gitignored files."""
    local_p = REPO_ROOT / rel_path
    if local_p.exists() and local_p.stat().st_size > 0:
        return local_p
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).strip()
        main_p = Path(common).resolve().parent / rel_path
        if main_p.exists() and main_p.stat().st_size > 0:
            return main_p
    except Exception:
        pass
    return local_p


DEFAULT_SOURCES_DB = resolve_data_path("data/sources.db")
DEFAULT_VESUM_DB = resolve_data_path("data/vesum.db")
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "mined"
DEFAULT_CUSTODY_FILE = (
    REPO_ROOT / "data" / "projects" / "open_model_data" / "decolonization" / "partitions" / "train_source_custody.json"
)

TITLE_EXEMPTIONS = {
    "ім",
    "вул",
    "просп",
    "пров",
    "пл",
    "м",
    "с",
    "смт",
    "оз",
    "проф",
    "акад",
    "доц",
    "ген",
    "св",
    "д-р",
    "р",
    "рр",
    "ст",
    "тис",
    "млн",
    "грн",
    "див",
    "напр",
    "т",
    "о",
}


def _get_stem(w: str) -> str:
    clean = re.sub(r"[^а-яіїєґ']", "", w.lower())
    if len(clean) <= 3:
        return clean
    return clean[:4]


def parse_textbook_contrast_tables(
    sources_db: Path,
    vesum_db: Path,
    train_only_author_hashes: bool = True,
) -> list[dict[str, Any]]:
    """Extract explicit contrast pairs (НЕПРАВИЛЬНО -> ПРАВИЛЬНО, ❌ -> ✅) from textbook chunks."""
    s_conn = sqlite3.connect(f"file:{sources_db}?mode=ro", uri=True)
    v_conn = sqlite3.connect(f"file:{vesum_db}?mode=ro", uri=True)
    sc = s_conn.cursor()
    vc = v_conn.cursor()

    def get_lemma(word: str) -> str:
        clean = re.sub(r"[^а-яіїєґ']", "", word.strip().lower())
        if not clean:
            return ""
        res = vc.execute("SELECT lemma FROM forms_all WHERE word_form = ? LIMIT 1", (clean,)).fetchone()
        return res[0] if res else clean

    rows = sc.execute(
        "SELECT id, chunk_id, title, author_uk, grade, subject, text FROM textbooks "
        "WHERE text LIKE '%НЕПРАВИЛЬНО%ПРАВИЛЬНО%' "
        "   OR text LIKE '%ПРАВИЛЬНО%НЕПРАВИЛЬНО%' "
        "   OR text LIKE '%❌%' "
        "   OR text LIKE '%Культура мовлення%' "
        "   OR text LIKE '%Культура слова%'"
    ).fetchall()

    contrast_records = []
    seen_pairs = set()

    for r in rows:
        _tid, cid, title, author, grade, subj, text = r
        author_key = author or "unknown"
        if train_only_author_hashes:
            h = int(hashlib.sha256(f"tb_author:{author_key}:{title}".encode()).hexdigest()[:8], 16)
            if h % 10 >= 8:
                # Strictly respect Phase 3.0 custody: skip held-out chunks for training miner
                continue

        lines = text.split("\n")
        table_mode: str | None = None
        pair_idx = 1

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # Header detection
            if re.search(r"НЕПРАВИЛЬНО\s+ПРАВИЛЬНО", line_str, re.IGNORECASE):
                table_mode = "incorrect_first"
                continue
            elif re.search(r"ПРАВИЛЬНО\s+НЕПРАВИЛЬНО", line_str, re.IGNORECASE):
                table_mode = "correct_first"
                continue
            elif "❌" in line_str and "✅" in line_str:
                m = re.search(r"❌\s*([^✅\n]+)\s*✅\s*([^\n]+)", line_str)
                if m:
                    inc, cor = m.group(1).strip(), m.group(2).strip()
                    if len(inc) >= 2 and len(cor) >= 2 and inc.lower() != cor.lower():
                        pair_key = (inc.lower(), cor.lower())
                        if pair_key not in seen_pairs:
                            seen_pairs.add(pair_key)
                            first_word = cor.split()[0].strip(",.:;!?")
                            corr_lemma = get_lemma(first_word)
                            root_fam = (
                                extract_root_family(corr_lemma) or extract_root_family(first_word) or first_word[:3]
                            )
                            contrast_records.append(
                                {
                                    "item_id": f"contrast.textbook.{cid}.{pair_idx}",
                                    "chunk_id": cid,
                                    "source": f"textbook:{cid}",
                                    "author": author_key,
                                    "grade": grade,
                                    "subject": subj or "ukrmova",
                                    "incorrect": inc,
                                    "correct": cor,
                                    "derivational_family": root_fam,
                                    "context": line_str,
                                }
                            )
                            pair_idx += 1
                continue

            if table_mode:
                if line_str.isdigit() or len(line_str) < 3:
                    table_mode = None
                    continue
                # Stop on narrative, instructions, exercise numbers, citations, URLs
                if re.match(
                    r"^(\d+[\.\)]|\d+\s|[А-Я]\.|\bПрочитайте\b|\bСкладіть\b|\bПерепишіть\b|\bПерегляньте\b|\bРозрізняймо\b|\bДО РЕЧІ\b|\bЗАУВАЖТЕ\b|\bПоясніть\b|\bВправа\b|\bРозділ\b|\bТема\b)",
                    line_str,
                ):
                    table_mode = None
                    continue
                if re.match(r"^[А-Г]\s+", line_str) or re.search(r"https?://|cutt\.ly|[a-zA-Z\?«»–—\(\)]", line_str):
                    table_mode = None
                    continue
                if len(line_str.split()) > 10:
                    table_mode = None
                    continue

                words = line_str.split()
                if len(words) < 2:
                    continue

                pair = None
                if "," in line_str:
                    first_comma = line_str.index(",")
                    left_part = line_str[:first_comma].split()
                    if len(left_part) == 2:
                        pair = (left_part[0], left_part[1] + line_str[first_comma:])

                if not pair and words[0].lower() in ("самий", "сама", "саме", "самі") and len(words) >= 3:
                    pair = (" ".join(words[:2]), " ".join(words[2:]))

                if not pair:
                    for i in range(1, len(words)):
                        if words[i].lower() == words[0].lower():
                            pair = (" ".join(words[:i]), " ".join(words[i:]))
                            break

                if not pair:
                    best_split = None
                    best_score = -999
                    for i in range(1, len(words)):
                        p1 = words[:i]
                        p2 = words[i:]
                        stems1 = {_get_stem(w) for w in p1 if len(_get_stem(w)) >= 3}
                        stems2 = {_get_stem(w) for w in p2 if len(_get_stem(w)) >= 3}
                        overlap = len(stems1.intersection(stems2))
                        diff = abs(len(p1) - len(p2))
                        score = overlap * 10 - diff
                        if score > best_score:
                            best_score = score
                            best_split = (" ".join(p1), " ".join(p2))
                    if best_split and best_score > 0:
                        pair = best_split

                if not pair and len(words) == 2:
                    # Single-word contrast pairs side-by-side
                    pair = (words[0], words[1])

                if not pair:
                    # Reject ambiguous multi-word lines lacking structural split evidence
                    continue

                w1 = pair[0].strip(",.:;!?")
                w2 = pair[1].strip(",.:;!?")
                if table_mode == "incorrect_first":
                    inc, cor = w1, w2
                else:
                    inc, cor = w2, w1

                if len(inc) < 2 or len(cor) < 2 or inc.lower() == cor.lower():
                    continue

                pair_key = (inc.lower(), cor.lower())
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    first_word = cor.split()[0].strip(",.:;!?")
                    corr_lemma = get_lemma(first_word)
                    root_fam = extract_root_family(corr_lemma) or extract_root_family(first_word) or first_word[:3]
                    contrast_records.append(
                        {
                            "item_id": f"contrast.textbook.{cid}.{pair_idx}",
                            "chunk_id": cid,
                            "source": f"textbook:{cid}",
                            "author": author_key,
                            "grade": grade,
                            "subject": subj or "ukrmova",
                            "incorrect": inc,
                            "correct": cor,
                            "derivational_family": root_fam,
                            "context": line_str,
                        }
                    )
                    pair_idx += 1

    s_conn.close()
    v_conn.close()
    return contrast_records


def parse_zno_exam_tasks(sources_db: Path) -> list[dict[str, Any]]:
    """Extract all official ZNO/NMT exam tasks with distractors and keys."""
    s_conn = sqlite3.connect(f"file:{sources_db}?mode=ro", uri=True)
    sc = s_conn.cursor()

    rows = sc.execute(
        "SELECT id, year, exam, session, task_no, subject, task_format, stem, options_json, correct_json, topic_norm "
        "FROM zno_tasks ORDER BY id"
    ).fetchall()

    tasks = []
    for r in rows:
        tid, year, exam, session, task_no, subject, tformat, stem, opt_json, corr_json, topic = r
        try:
            options = json.loads(opt_json) if opt_json else []
        except Exception:
            options = opt_json

        try:
            correct_key = json.loads(corr_json) if corr_json else corr_json
        except Exception:
            correct_key = corr_json

        distractors = []
        correct_choice = None

        if isinstance(options, list) and isinstance(correct_key, str):
            key_map = {"А": 0, "Б": 1, "В": 2, "Г": 3, "Д": 4}
            corr_idx = key_map.get(correct_key.strip())
            for idx, opt in enumerate(options):
                if idx == corr_idx:
                    correct_choice = opt
                else:
                    distractors.append(opt)
        elif isinstance(options, dict) and "left" in options:
            distractors = options.get("left", [])
            correct_choice = options.get("right", [])

        stem_str = (stem or "").strip()
        if len(stem_str) > 150:
            lines = [l.strip() for l in stem_str.split("\n") if l.strip()]
            tail = lines[-2:] if len(lines) >= 2 else lines
            prompt = " ".join(tail)
            stem_str = lines[0][:80] + " ... [скорочено] ... " + prompt

        tasks.append(
            {
                "task_id": f"zno.{tid}",
                "exam": exam,
                "year": year,
                "session": session,
                "task_no": task_no,
                "subject": subject,
                "task_format": tformat,
                "topic_norm": topic or "general",
                "stem": stem_str,
                "options": options,
                "correct_key": correct_key,
                "distractors": distractors,
                "correct_choice": correct_choice,
            }
        )

    s_conn.close()
    return tasks


def mine_corpus_calques(
    sources_db: Path,
    vesum_db: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Run extraction for textbook contrast tables and ZNO distractor tasks."""
    output_dir.mkdir(parents=True, exist_ok=True)
    contrast_file = output_dir / "corpus_contrast_tables.jsonl"
    zno_file = output_dir / "zno_distractor_tasks.jsonl"

    contrast_records = parse_textbook_contrast_tables(sources_db, vesum_db)
    with contrast_file.open("w", encoding="utf-8") as f:
        for rec in contrast_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    zno_records = parse_zno_exam_tasks(sources_db)
    with zno_file.open("w", encoding="utf-8") as f:
        for rec in zno_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    author_counts: dict[str, int] = {}
    unique_chunks = set()
    for rec in contrast_records:
        author_counts[rec["author"]] = author_counts.get(rec["author"], 0) + 1
        unique_chunks.add(rec["chunk_id"])

    topic_counts: dict[str, int] = {}
    for rec in zno_records:
        t = rec["topic_norm"]
        topic_counts[t] = topic_counts.get(t, 0) + 1

    return {
        "contrast_records_count": len(contrast_records),
        "unique_chunks_count": len(unique_chunks),
        "contrast_sha256": hashlib.sha256(contrast_file.read_bytes()).hexdigest(),
        "zno_records_count": len(zno_records),
        "zno_sha256": hashlib.sha256(zno_file.read_bytes()).hexdigest(),
        "top_authors": dict(sorted(author_counts.items(), key=lambda x: -x[1])[:10]),
        "topic_distribution": topic_counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine textbook contrast tables and ZNO tasks.")
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--verify-only", action="store_true", help="Verify existing output files.")
    args = parser.parse_args()

    if args.verify_only:
        contrast_file = args.output_dir / "corpus_contrast_tables.jsonl"
        zno_file = args.output_dir / "zno_distractor_tasks.jsonl"
        if not contrast_file.is_file() or not zno_file.is_file():
            print("Missing output files for verification.")
            sys.exit(1)
        c_count = sum(1 for _ in contrast_file.open(encoding="utf-8"))
        z_count = sum(1 for _ in zno_file.open(encoding="utf-8"))
        print(f"Verified files: {c_count} contrast tables, {z_count} ZNO tasks.")
        sys.exit(0)

    summary = mine_corpus_calques(args.sources_db, args.vesum_db, args.output_dir)
    print("Mined textbook contrast pairs:", summary["contrast_records_count"])
    print("Mined ZNO tasks:", summary["zno_records_count"])


if __name__ == "__main__":
    main()

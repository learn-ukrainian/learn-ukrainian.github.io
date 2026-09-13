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

    def test_alignment(seq1: list[str], seq2: list[str]) -> int:
        if len(seq1) != len(seq2) or not seq1:
            return 0
        matches = 0
        for s1, s2 in zip(seq1, seq2, strict=True):
            w1 = set(re.findall(r"[а-яіїєґ']+", s1.lower()))
            w2 = set(re.findall(r"[а-яіїєґ']+", s2.lower()))
            lemmas1 = {get_lemma(w) for w in w1 if len(w) >= 3}
            lemmas2 = {get_lemma(w) for w in w2 if len(w) >= 3}
            stems1 = {_get_stem(w) for w in w1 if len(_get_stem(w)) >= 3}
            stems2 = {_get_stem(w) for w in w2 if len(_get_stem(w)) >= 3}
            if (
                len(w1.intersection(w2)) > 0
                or len(lemmas1.intersection(lemmas2)) > 0
                or len(stems1.intersection(stems2)) > 0
            ):
                matches += 1
        return matches

    def check_side_by_side_line(line_str: str) -> tuple[str, str] | None:
        words = line_str.split()
        if len(words) < 2:
            return None
        # 1. Comma in line with 2-word left part
        if "," in line_str:
            first_comma = line_str.index(",")
            left_part = line_str[:first_comma].split()
            if len(left_part) == 2:
                return (left_part[0], left_part[1] + line_str[first_comma:])
        # 2. Superlative constructions
        if words[0].lower() in ("самий", "сама", "саме", "самі") and len(words) >= 3:
            return (" ".join(words[:2]), " ".join(words[2:]))
        # 3. Repeated anchor word
        for i in range(1, len(words)):
            if words[i].lower() == words[0].lower():
                return (" ".join(words[:i]), " ".join(words[i:]))
        # 4. Shared stem / lemma morphological split
        best_split = None
        best_score = -999
        for i in range(1, len(words)):
            p1 = words[:i]
            p2 = words[i:]
            lemmas1 = {get_lemma(w) for w in p1 if len(w) >= 3}
            lemmas2 = {get_lemma(w) for w in p2 if len(w) >= 3}
            stems1 = {_get_stem(w) for w in p1 if len(_get_stem(w)) >= 3}
            stems2 = {_get_stem(w) for w in p2 if len(_get_stem(w)) >= 3}
            overlap = len(lemmas1.intersection(lemmas2).union(stems1.intersection(stems2)))
            diff = abs(len(p1) - len(p2))
            score = overlap * 10 - diff
            if score > best_score:
                best_score = score
                best_split = (" ".join(p1), " ".join(p2))
        if best_split and best_score > 0:
            return best_split
        # Reject unevidenced lines: no blind 2-word bisection fallback
        return None

    rows = sc.execute(
        "SELECT id, chunk_id, title, author_uk, grade, subject, text FROM textbooks "
        "WHERE text LIKE '%НЕПРАВИЛЬНО%' "
        "   OR text LIKE '%ПРАВИЛЬНО%' "
        "   OR text LIKE '%Правильно%' "
        "   OR text LIKE '%❌%' "
        "   OR text LIKE '%Культура мовлення%' "
        "   OR text LIKE '%Культура слова%' "
        "   OR text LIKE '%Антисуржик%'"
    ).fetchall()

    contrast_records = []
    seen_pairs = set()

    def add_pair(
        cid: str,
        author_key: str,
        grade: Any,
        subj: Any,
        inc: str,
        cor: str,
        ctx: str,
        pidx: int,
    ) -> bool:
        inc = re.sub(r"^[/\\–—\-\s]+|[/\\–—\-\s]+$", "", inc).strip(",.:;!? ")
        cor = re.sub(r"^[/\\–—\-\s]+|[/\\–—\-\s]+$", "", cor).strip(",.:;!? ")
        if len(inc) < 2 or len(cor) < 2 or inc.lower() == cor.lower():
            return False
        cor_words = re.findall(r"[а-яіїєґ']+", cor.lower())
        if not cor_words:
            return False
        first_word = cor_words[0]
        corr_lemma = get_lemma(first_word)
        root_fam = extract_root_family(corr_lemma) or extract_root_family(first_word) or first_word[:3]
        if not root_fam:
            return False
        pair_key = (inc.lower(), cor.lower())
        if pair_key in seen_pairs:
            return False
        seen_pairs.add(pair_key)
        contrast_records.append(
            {
                "item_id": f"contrast.textbook.{cid}.{pidx}",
                "chunk_id": cid,
                "source": f"textbook:{cid}",
                "author": author_key,
                "grade": grade,
                "subject": subj or "ukrmova",
                "incorrect": inc,
                "correct": cor,
                "derivational_family": root_fam,
                "context": ctx,
            }
        )
        return True

    for r in rows:
        _tid, cid, title, author, grade, subj, text = r
        author_key = author or "unknown"
        if train_only_author_hashes:
            h = int(hashlib.sha256(f"tb_author:{author_key}:{title}".encode()).hexdigest()[:8], 16)
            if h % 10 >= 8:
                # Strictly respect Phase 3.0 custody: skip held-out chunks for training miner
                continue

        lines = text.split("\n")
        pair_idx = 1
        i = 0

        while i < len(lines):
            line_str = lines[i].strip()
            if not line_str:
                i += 1
                continue

            # Inline emoji contrast: ❌ ... ✅ ...
            if "❌" in line_str and "✅" in line_str:
                m = re.search(r"❌\s*([^✅\n]+)\s*✅\s*([^\n]+)", line_str)
                if m and add_pair(
                    cid,
                    author_key,
                    grade,
                    subj,
                    m.group(1).strip(),
                    m.group(2).strip(),
                    line_str,
                    pair_idx,
                ):
                    pair_idx += 1
                i += 1
                continue

            # Header detection (case-insensitive word boundary)
            m_inc = re.search(r"\bНЕПРАВИЛЬНО\b", line_str, re.IGNORECASE)
            m_cor = re.search(r"\bПРАВИЛЬНО\b", line_str, re.IGNORECASE)
            if not (m_inc and m_cor):
                i += 1
                continue

            mode = "incorrect_first" if m_inc.start() < m_cor.start() else "correct_first"

            candidate_lines = []
            j = i + 1
            while j < len(lines):
                l = lines[j].strip()
                if l.isdigit() or len(l) < 2:
                    break
                # Stop on narrative, instructions, exercise numbers, citations, headings
                if re.match(
                    r"^(\d+[\.\)]|\d+\s|[А-Я]\.|\bПрочитайте\b|\bСкладіть\b|\bПерепишіть\b|\bПерегляньте\b|\bРозрізняймо\b|\bДО РЕЧІ\b|\bЗАУВАЖТЕ\b|\bПоясніть\b|\bВправа\b|\bРозділ\b|\bТема\b|\bКорисно знати\b)",
                    l,
                ):
                    break
                if re.match(r"^[А-Г]\s+", l) or re.search(r"https?://|cutt\.ly|[a-zA-Z\?«»–—\(\)]", l):
                    break
                if len(l.split()) > 10:
                    break
                candidate_lines.append(l)
                j += 1

            i = j
            if not candidate_lines:
                continue

            # 1. Check for two-column (or multi-column) block layout
            offset = 0
            is_two_col = False
            while offset < len(candidate_lines):
                rem = len(candidate_lines) - offset
                best_k = None
                best_matches = 0
                for k in range(2, rem // 2 + 1):
                    col1 = candidate_lines[offset : offset + k]
                    col2 = candidate_lines[offset + k : offset + 2 * k]
                    m = test_alignment(col1, col2)
                    min_m = 2 if k >= 3 else 1
                    if (
                        m >= min_m
                        and (m / k) >= 0.5
                        and (m > best_matches or (m == best_matches and (best_k is None or k > best_k)))
                    ):
                        best_matches = m
                        best_k = k

                if best_k:
                    is_two_col = True
                    c1 = candidate_lines[offset : offset + best_k]
                    c2 = candidate_lines[offset + best_k : offset + 2 * best_k]
                    for w1, w2 in zip(c1, c2, strict=True):
                        inc, cor = (w1, w2) if mode == "incorrect_first" else (w2, w1)
                        p1 = text.find(w1)
                        p2 = text.find(w2)
                        if p1 != -1 and p2 != -1:
                            start_p = min(p1, p2)
                            end_p = max(p1 + len(w1), p2 + len(w2))
                            ctx = text[start_p:end_p]
                        else:
                            ctx = f"{w1} -> {w2}"

                        if add_pair(cid, author_key, grade, subj, inc, cor, ctx, pair_idx):
                            pair_idx += 1
                    offset += 2 * best_k
                else:
                    break

            # 2. Check Alternating Rows if not half-and-half
            if not is_two_col and len(candidate_lines) >= 4 and len(candidate_lines) % 2 == 0:
                alt_matches = sum(
                    1
                    for idx in range(len(candidate_lines) // 2)
                    if test_alignment([candidate_lines[2 * idx]], [candidate_lines[2 * idx + 1]])
                )
                if alt_matches >= 2 and (alt_matches / (len(candidate_lines) // 2)) >= 0.6:
                    is_two_col = True
                    for idx in range(len(candidate_lines) // 2):
                        w1 = candidate_lines[2 * idx]
                        w2 = candidate_lines[2 * idx + 1]
                        inc, cor = (w1, w2) if mode == "incorrect_first" else (w2, w1)
                        p1 = text.find(w1)
                        p2 = text.find(w2)
                        if p1 != -1 and p2 != -1:
                            start_p = min(p1, p2)
                            end_p = max(p1 + len(w1), p2 + len(w2))
                            ctx = text[start_p:end_p]
                        else:
                            ctx = f"{w1} -> {w2}"

                        if add_pair(cid, author_key, grade, subj, inc, cor, ctx, pair_idx):
                            pair_idx += 1

            # 3. Check Side-by-Side if not column-based
            if not is_two_col:
                for l in candidate_lines:
                    p = check_side_by_side_line(l)
                    if p:
                        inc, cor = (p[0], p[1]) if mode == "incorrect_first" else (p[1], p[0])
                        if add_pair(cid, author_key, grade, subj, inc, cor, l, pair_idx):
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

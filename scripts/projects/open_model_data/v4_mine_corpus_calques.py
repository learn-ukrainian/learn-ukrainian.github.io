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

from scripts.projects.open_model_data.phase3_decolonization_partition import (
    extract_root_family,
    is_phase30_textbook_heldout,
)
from scripts.projects.open_model_data.phase3_mined_candidate_guards import (
    INVENTED_ZNO_CONNECTOR_RE,
    INVENTED_ZNO_ELLIPSIS_RE,
    INVENTED_ZNO_SPLICE_RE,
    contains_invented_zno_ellipsis,
    is_inverted_do_po_date_range,
    verify_mined_manifest,
)


def strip_invented_zno_ellipsis(stem: str) -> str:
    """Remove miner-invented ``[скорочено]`` connectors and leftover `` ... ... `` splices."""
    if not stem:
        return ""
    cleaned = INVENTED_ZNO_CONNECTOR_RE.sub(" ", stem)
    cleaned = INVENTED_ZNO_ELLIPSIS_RE.sub(" ", cleaned)
    cleaned = INVENTED_ZNO_SPLICE_RE.sub(" ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def official_zno_stem(stem: str) -> str:
    """Keep official exam bytes; strip only an invented ``[скорочено]`` connector if present."""
    text = (stem or "").strip()
    if not text:
        return ""
    if INVENTED_ZNO_ELLIPSIS_RE.search(text):
        return strip_invented_zno_ellipsis(text)
    return text


def _stems_from_zno_html(html: str) -> dict[int, str]:
    """Parse official stems from a zno.osvita.ua booklet page (same extraction as ingest)."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    stems: dict[int, str] = {}
    for card in soup.find_all(class_="task-card"):
        task_no_match = re.search(r"\d+", card.get("id", "") or "")
        if not task_no_match:
            continue
        q_div = card.find(class_="question")
        stem = q_div.get_text(separator="\n", strip=True) if q_div else ""
        stems[int(task_no_match.group(0))] = official_zno_stem(stem)
    return stems


def load_official_zno_stems_from_sources(sources_db: Path) -> dict[int, str]:
    """Map ``zno_tasks.id`` → official ``stem``."""
    conn = sqlite3.connect(f"file:{sources_db}?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT id, stem FROM zno_tasks ORDER BY id").fetchall()
    finally:
        conn.close()
    return {int(tid): official_zno_stem(stem) for tid, stem in rows}


def load_official_zno_stems_from_html(cache_dir: Path) -> dict[tuple[int, str, int], str]:
    """Map ``(year, session, task_no)`` → official stem from published exam pages."""
    from scripts.ingest.zno_ingest import ONLINE_TEST_MAPPING, fetch_page_with_rate_limit

    stems: dict[tuple[int, str, int], str] = {}
    for (year, session, subject_scope), (catalogue, test_id) in ONLINE_TEST_MAPPING.items():
        cache_path = cache_dir / f"{catalogue}_{test_id}.html"
        url = f"https://zno.osvita.ua/{catalogue}/{test_id}/"
        html = fetch_page_with_rate_limit(url, cache_path)
        for task_no, stem in _stems_from_zno_html(html).items():
            key = (int(year), str(session), int(task_no))
            if key in stems and stems[key] != stem:
                raise ValueError(f"Conflicting official stems for {key} ({subject_scope})")
            stems[key] = stem
    return stems


def restore_zno_stems_from_official_exam_text(
    records: list[dict[str, Any]],
    sources_db: Path | None = None,
    cache_dir: Path | None = None,
) -> dict[str, int]:
    """Replace mined stems with official exam text. Prefer ``zno_tasks.stem`` when present."""
    restored = 0
    longer = 0
    missing = 0
    by_id: dict[int, str] = {}
    by_key: dict[tuple[int, str, int], str] = {}
    db_path = sources_db if sources_db is not None and sources_db.is_file() and sources_db.stat().st_size > 0 else None
    if db_path is not None:
        by_id = load_official_zno_stems_from_sources(db_path)
    else:
        cache = cache_dir if cache_dir is not None else Path("/tmp/zno_cache")
        by_key = load_official_zno_stems_from_html(cache)

    for rec in records:
        previous = rec.get("stem") or ""
        official = ""
        if by_id:
            try:
                tid = int(str(rec.get("task_id", "")).split(".", 1)[1])
            except (IndexError, ValueError):
                tid = -1
            official = by_id.get(tid, "")
        else:
            try:
                key = (int(rec["year"]), str(rec["session"]), int(rec["task_no"]))
            except (KeyError, TypeError, ValueError):
                key = None
            official = by_key.get(key, "") if key is not None else ""
        if not official:
            missing += 1
            continue
        rec["stem"] = official
        restored += 1
        if len(official) > len(previous):
            longer += 1
    return {"restored": restored, "longer": longer, "missing": missing}


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


UKRAINIAN_STOPWORDS = {
    "і",
    "й",
    "та",
    "а",
    "але",
    "чи",
    "або",
    "в",
    "у",
    "на",
    "з",
    "із",
    "зі",
    "до",
    "по",
    "за",
    "про",
    "при",
    "під",
    "над",
    "перед",
    "для",
    "від",
    "без",
    "через",
    "після",
    "не",
    "ні",
    "як",
    "що",
    "щоб",
    "це",
    "той",
    "такий",
    "який",
    "яка",
    "яке",
    "які",
    "хто",
    "ми",
    "ви",
    "він",
    "вона",
    "воно",
    "вони",
    "його",
    "її",
    "їх",
    "їм",
    "нам",
    "вам",
}


def get_content_words(s: str) -> list[str]:
    s_clean = s.replace("’", "'").replace("`", "'")
    words = re.findall(r"[а-яіїєґ']+", s_clean.lower())
    return [w for w in words if len(w) >= 3 and w not in UKRAINIAN_STOPWORDS]


def _get_stem(w: str) -> str:
    clean = re.sub(r"[^а-яіїєґ']", "", w.replace("’", "'").lower())
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
        clean = re.sub(r"[^а-яіїєґ']", "", word.replace("’", "'").strip().lower())
        if not clean:
            return ""
        res = vc.execute("SELECT lemma FROM forms_all WHERE word_form = ? LIMIT 1", (clean,)).fetchone()
        return res[0] if res else clean

    def test_pair_alignment(s1: str, s2: str) -> bool:
        if s1.strip().lower() == s2.strip().lower():
            return False
        cw1 = set(get_content_words(s1))
        cw2 = set(get_content_words(s2))
        if not cw1 or not cw2:
            return False
        if cw1.intersection(cw2):
            return True
        lemmas1 = {get_lemma(w) for w in cw1}
        lemmas2 = {get_lemma(w) for w in cw2}
        if lemmas1.intersection(lemmas2):
            return True
        stems1 = {_get_stem(w) for w in cw1}
        stems2 = {_get_stem(w) for w in cw2}
        return bool(stems1.intersection(stems2))

    def test_alignment(seq1: list[str], seq2: list[str]) -> int:
        if len(seq1) != len(seq2) or not seq1:
            return 0
        matches = 0
        for s1, s2 in zip(seq1, seq2, strict=True):
            if test_pair_alignment(s1, s2):
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
        # 3. Repeated anchor word (non-stopword)
        for i in range(1, len(words)):
            w0 = words[0].replace("’", "'").lower()
            wi = words[i].replace("’", "'").lower()
            if wi == w0 and w0 not in UKRAINIAN_STOPWORDS:
                return (" ".join(words[:i]), " ".join(words[i:]))
        # 4. Shared stem / lemma morphological split on content words
        best_split = None
        best_score = -999
        for i in range(1, len(words)):
            p1 = words[:i]
            p2 = words[i:]
            cw1 = set(get_content_words(" ".join(p1)))
            cw2 = set(get_content_words(" ".join(p2)))
            if not cw1 or not cw2:
                continue
            lemmas1 = {get_lemma(w) for w in cw1}
            lemmas2 = {get_lemma(w) for w in cw2}
            stems1 = {_get_stem(w) for w in cw1}
            stems2 = {_get_stem(w) for w in cw2}
            overlap = len(cw1.intersection(cw2).union(lemmas1.intersection(lemmas2)).union(stems1.intersection(stems2)))
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
        inc = re.sub(r"\s+", " ", inc).strip()
        cor = re.sub(r"\s+", " ", cor).strip()
        if len(inc) < 2 or len(cor) < 2 or inc.lower() == cor.lower():
            return False
        # Reject inverted date range expressions where "по" is incorrectly marked as correct instead of "до"
        if is_inverted_do_po_date_range(inc, cor):
            return False
        cor_words = get_content_words(cor)
        if not cor_words:
            cor_words = re.findall(r"[а-яіїєґ']+", cor.replace("’", "'").lower())
        if not cor_words:
            return False
        first_word = cor_words[0]
        corr_lemma = get_lemma(first_word)
        root_fam = extract_root_family(corr_lemma) or extract_root_family(first_word) or first_word[:3]
        if not root_fam or len(root_fam) < 2:
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
        if train_only_author_hashes and is_phase30_textbook_heldout(author_key, title):
            # Same Phase 3.0 function as the partition firewall — not the count-only custody JSON.
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
            if re.search(r"(\[|URL|http|с\.\s*[–—\-]|ДонНУ|монографія|видавництво|редакція)", line_str, re.IGNORECASE):
                i += 1
                continue

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
                if not l or l.isdigit() or len(l) < 2:
                    break
                # Stop on narrative, instructions, exercise numbers, citations, headings
                if re.match(
                    r"^(\d+[\.\)]|\d+\s|[А-Я]\.|\bПрочитайте\b|\bСкладіть\b|\bВизначте\b|\bЯкі\b|\bПерепишіть\b|\bПерегляньте\b|\bРозрізняймо\b|\bДО РЕЧІ\b|\bЗАУВАЖТЕ\b|\bПоясніть\b|\bВправа\b|\bРозділ\b|\bТема\b|\bКорисно знати\b)",
                    l,
                ):
                    break
                # Reject wrapped lines ending with hyphens
                if l.endswith("-") or l.endswith("–") or l.endswith("—"):
                    break
                l_clean = re.sub(r"\([^)]*\)", "", l).strip()
                l_clean = re.sub(r"\s+", " ", l_clean)
                if re.match(r"^[А-Г]\s+", l_clean) or re.search(r"https?://|cutt\.ly|[a-zA-Z\?«»–—]", l_clean):
                    break
                l_words = l_clean.split()
                if len(l_words) > 6:
                    break
                if l_clean.endswith(".") and len(l_words) > 3:
                    break
                candidate_lines.append((l, l_clean))
                j += 1

            i = j
            if not candidate_lines:
                continue

            raw_lines = [item[0] for item in candidate_lines]
            clean_lines = [item[1] for item in candidate_lines]

            # 1. Check for two-column (or multi-column) block layout
            offset = 0
            is_two_col = False
            while offset < len(candidate_lines):
                rem = len(candidate_lines) - offset
                best_k = None
                best_matches = 0
                for k in range(2, rem // 2 + 1):
                    col1 = clean_lines[offset : offset + k]
                    col2 = clean_lines[offset + k : offset + 2 * k]
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
                    c1_clean = clean_lines[offset : offset + best_k]
                    c2_clean = clean_lines[offset + best_k : offset + 2 * best_k]
                    c1_raw = raw_lines[offset : offset + best_k]
                    c2_raw = raw_lines[offset + best_k : offset + 2 * best_k]
                    for (w1_raw, w1_clean), (w2_raw, w2_clean) in zip(
                        zip(c1_raw, c1_clean, strict=True),
                        zip(c2_raw, c2_clean, strict=True),
                        strict=True,
                    ):
                        inc_clean, cor_clean = (
                            (w1_clean, w2_clean) if mode == "incorrect_first" else (w2_clean, w1_clean)
                        )
                        p1 = text.find(w1_raw)
                        p2 = text.find(w2_raw)
                        if p1 != -1 and p2 != -1:
                            start_p = min(p1, p2)
                            end_p = max(p1 + len(w1_raw), p2 + len(w2_raw))
                            ctx = text[start_p:end_p]
                        else:
                            continue

                        if add_pair(cid, author_key, grade, subj, inc_clean, cor_clean, ctx, pair_idx):
                            pair_idx += 1
                    offset += 2 * best_k
                else:
                    break

            # 2. Check Alternating Rows if not half-and-half
            if not is_two_col and len(candidate_lines) >= 4 and len(candidate_lines) % 2 == 0:
                alt_matches = sum(
                    1
                    for idx in range(len(candidate_lines) // 2)
                    if test_pair_alignment(clean_lines[2 * idx], clean_lines[2 * idx + 1])
                )
                if alt_matches >= 2 and (alt_matches / (len(candidate_lines) // 2)) >= 0.6:
                    is_two_col = True
                    for idx in range(len(candidate_lines) // 2):
                        w1_raw, w1_clean = candidate_lines[2 * idx]
                        w2_raw, w2_clean = candidate_lines[2 * idx + 1]
                        inc_clean, cor_clean = (
                            (w1_clean, w2_clean) if mode == "incorrect_first" else (w2_clean, w1_clean)
                        )
                        p1 = text.find(w1_raw)
                        p2 = text.find(w2_raw)
                        if p1 != -1 and p2 != -1:
                            start_p = min(p1, p2)
                            end_p = max(p1 + len(w1_raw), p2 + len(w2_raw))
                            ctx = text[start_p:end_p]
                        else:
                            continue

                        if add_pair(cid, author_key, grade, subj, inc_clean, cor_clean, ctx, pair_idx):
                            pair_idx += 1

            # 3. Check Side-by-Side if not column-based
            if not is_two_col:
                for raw_l, clean_l in candidate_lines:
                    p = check_side_by_side_line(clean_l)
                    if p:
                        inc, cor = (p[0], p[1]) if mode == "incorrect_first" else (p[1], p[0])
                        if add_pair(cid, author_key, grade, subj, inc, cor, raw_l, pair_idx):
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

        # Official exam text must stay byte-faithful. Never invent a «[скорочено]» ellipsis.
        stem_str = official_zno_stem(stem)

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
    parser.add_argument(
        "--restore-zno-stems",
        action="store_true",
        help="Rewrite committed ZNO stems from official zno_tasks.stem or published exam HTML.",
    )
    parser.add_argument(
        "--zno-html-cache",
        type=Path,
        default=Path("/tmp/zno_cache"),
        help="Cache directory for official zno.osvita.ua booklet HTML.",
    )
    args = parser.parse_args()

    if args.verify_only:
        schema_path = (
            REPO_ROOT
            / "data"
            / "projects"
            / "open_model_data"
            / "contracts"
            / "v1_decolonization_mined_candidates.schema.json"
        )
        try:
            verify_mined_manifest(args.output_dir, schema_path)
        except ValueError as exc:
            print(f"Verification failed: {exc}")
            sys.exit(1)
        print("Mined artifacts verified (schema, SHA-256, F1–F3 guards).")
        sys.exit(0)

    if args.restore_zno_stems:
        zno_path = args.output_dir / "zno_distractor_tasks.jsonl"
        if not zno_path.is_file():
            print(f"Missing ZNO artifact: {zno_path.name}")
            sys.exit(1)
        records = []
        with zno_path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(json.loads(line))
        stats = restore_zno_stems_from_official_exam_text(
            records,
            sources_db=args.sources_db,
            cache_dir=args.zno_html_cache,
        )
        remaining = [rec.get("task_id") for rec in records if contains_invented_zno_ellipsis(rec.get("stem", ""))]
        if stats["missing"] or remaining:
            print(f"ZNO stem restore incomplete: missing={stats['missing']} spliced={len(remaining)}")
            sys.exit(1)
        with zno_path.open("w", encoding="utf-8") as handle:
            for rec in records:
                handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
        manifest_path = args.output_dir / "decolonization_mined_manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"]["zno_distractor_tasks"]["sha256"] = hashlib.sha256(zno_path.read_bytes()).hexdigest()
            manifest["files"]["zno_distractor_tasks"]["record_count"] = len(records)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        print(f"Restored official ZNO stems: {stats['restored']} ({stats['longer']} longer than the prior splice).")
        sys.exit(0)

    summary = mine_corpus_calques(args.sources_db, args.vesum_db, args.output_dir)
    print("Mined textbook contrast pairs:", summary["contrast_records_count"])
    print("Mined ZNO tasks:", summary["zno_records_count"])


if __name__ == "__main__":
    main()

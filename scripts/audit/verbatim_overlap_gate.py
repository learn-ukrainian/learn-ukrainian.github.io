#!/usr/bin/env python3
"""
Deterministic verbatim/near-verbatim overlap gate (advisory).

Screens generated learner content (module prose + dialogues + activities) against
the source corpus using a persisted word-shingle inverted index in SQLite.

- No LLM. Pure deterministic.
- LEFT: UA learner content extracted from module.md (fenced examples, prose, turns)
  + activities.yaml (inline + workbook) + INJECT targets (via yaml).
- RIGHT: textbooks, literary_texts, external_articles full strength.
  ukrainian_wiki reported separately as self-overlap.
- Normalization (identical sides): NFC + lower + strip combining stress (U+030x) +
  apostrophe fold + collapse punct/ws.
- Shingles: word k-grams (default k=8, configurable).
- Metrics:
  * max_contiguous_run (words) on raw normalized token seq via chained shingles
    (NEVER DF-suppressed); reported with and without DF-allowlist.
  * overlap_ratio (tokens covered / total) with DF + verify_quote allowlist.
  * On hits: fetch chunk + LCS alignment for true longest exact run.
- Allowlist:
  (a) Attributed quotes passing verify_quote(author, text) >= 0.85 (ratio only).
  (b) High-DF shingles (df >= N distinct chunks) for ratio only.
- Index keyed by corpus content-hash for auto-invalidation.
- Extraction is versioned + golden-tested.

CLI is advisory; no thresholds, no CI enforcement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import yaml

# Version the extraction contract so golden tests + index can invalidate together.
EXTRACTION_SPEC_VERSION: str = "2026-07-v1-ua-learner-activities"

K_DEFAULT: int = 8
DF_N_DEFAULT: int = 5  # tuned post-baseline with user; report the value used

SCOPED_CORPUS_WARNING: str = (
    "WARNING: DF counts and the verify_quote allowlist are computed over the scoped corpus only. "
    "Ratios are NOT comparable to full-index runs and MUST NOT set enforcement thresholds without a full-index delta check."
)

# Corpus tables we index at full strength (RIGHT side). Order matters for fingerprints.
FULL_CORPORA: list[tuple[str, str, str, str]] = [
    ("textbooks", "chunk_id", "text", "textbooks"),
    ("literary_texts", "chunk_id", "text", "literary"),
    ("external_articles", "chunk_id", "text", "external"),
]
# Self-overlap (our compiled content) — distinguishable in reports.
SELF_CORPORA: list[tuple[str, str, str, str]] = [
    ("ukrainian_wiki", "passage_id", "text", "ukrainian_wiki"),
]
# wikipedia optional (not indexed by default).
OPTIONAL_CORPORA: list[tuple[str, str, str, str]] = [
    ("wikipedia", "title", "text", "wikipedia"),
]

ALL_POSSIBLE_CORPORA: dict[str, tuple[str, str, str, str]] = {
    "textbooks": ("textbooks", "chunk_id", "text", "textbooks"),
    "literary": ("literary_texts", "chunk_id", "text", "literary"),
    "external": ("external_articles", "chunk_id", "text", "external"),
    "ukrainian_wiki": ("ukrainian_wiki", "passage_id", "text", "ukrainian_wiki"),
    "wikipedia": ("wikipedia", "title", "text", "wikipedia"),
}


def get_default_index_db_path(
    sources_db: Path | str,
    k: int,
    corpora: list[tuple[str, str, str, str]] | None = None,
) -> Path:
    sources_db = Path(sources_db)
    parent_dir = Path(".") if str(sources_db) == ":memory:" else sources_db.parent

    default_corpora = FULL_CORPORA + SELF_CORPORA
    is_default = False
    if corpora is None:
        is_default = True
    else:
        default_labels = {c[3] for c in default_corpora}
        current_labels = {c[3] for c in corpora}
        if default_labels == current_labels:
            is_default = True

    if is_default:
        return parent_dir / f"verbatim_shingle_k{k}.db"
    else:
        labels = sorted([c[3] for c in corpora])
        slug = "-".join(labels)
        return parent_dir / f"verbatim_shingle_k{k}_{slug}.db"


def parse_corpora_labels(raw_labels: list[str] | None) -> list[tuple[str, str, str, str]] | None:
    if raw_labels is None:
        return None
    labels = []
    for rl in raw_labels:
        for lbl in rl.split(","):
            lbl = lbl.strip()
            if lbl:
                labels.append(lbl)

    valid_labels = sorted(list(ALL_POSSIBLE_CORPORA.keys()))
    invalid = [l for l in labels if l not in ALL_POSSIBLE_CORPORA]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"Invalid corpus label(s): {', '.join(invalid)}. Valid labels are: {', '.join(valid_labels)}"
        )

    unique_labels = list(dict.fromkeys(labels))
    return [ALL_POSSIBLE_CORPORA[lbl] for lbl in unique_labels]


def normalize_text(text: str) -> str:
    """Ukrainian-aware normalization for shingling (must be identical on both sides).

    Strips ONLY stress combining marks (U+0301 acute, U+0300 grave). Other combining
    marks (e.g. diaeresis U+0308 on ї, breve U+0306 on й) are preserved so that
    distinct UA letters are not collapsed (ї≠і, й≠и). Always round-trips via NFC.
    """
    if not text:
        return ""
    # NFC first for canonical
    text = unicodedata.normalize("NFC", text)
    # lower
    text = text.lower()
    # NFD to separate marks, then drop ONLY stress codepoints (keep diaeresis/breve etc.)
    text = unicodedata.normalize("NFD", text)
    STRESS_MARKS = {0x0300, 0x0301}
    text = "".join(ch for ch in text if not (unicodedata.combining(ch) and ord(ch) in STRESS_MARKS))
    # restore NFC so precomposed letters are canonical (ї, й etc. recompose)
    text = unicodedata.normalize("NFC", text)
    # apostrophe variant fold (’ ' ` ′ ‘ ’ etc. -> ')
    text = re.sub(r"['’ʼ`′‘’]", "'", text)
    # collapse punctuation + runs of ws/hyphen to single space (keep ' inside words)
    text = re.sub(r"[^\w\s'-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(norm_text: str) -> list[str]:
    """Tokenize normalized text into words (apostrophes kept inside tokens)."""
    if not norm_text:
        return []
    return re.findall(r"[\w']+", norm_text)


def make_shingles(tokens: list[str], k: int = K_DEFAULT) -> list[str]:
    """Return list of shingle keys (space-joined word k-grams)."""
    if len(tokens) < k:
        return []
    return [" ".join(tokens[i : i + k]) for i in range(len(tokens) - k + 1)]


def has_cyrillic(s: str) -> bool:
    return bool(re.search(r"[\u0400-\u04FF]", s))


def is_mostly_ukrainian(s: str, threshold: float = 0.25) -> bool:
    """Heuristic: enough Cyrillic to treat as UA learner content."""
    if not s or len(s) < 3:
        return False
    cyr = len(re.findall(r"[\u0400-\u04FF]", s))
    letters = len(re.findall(r"\w", s))
    if letters == 0:
        return False
    return (cyr / letters) >= threshold


def strip_md_inline(line: str) -> str:
    """Remove common inline markdown while keeping UA text."""
    line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
    line = re.sub(r"\*([^*]+)\*", r"\1", line)
    line = re.sub(r"`([^`]+)`", r"\1", line)
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
    return line.strip()


def _find_offsets(haystack: str, needle: str) -> tuple[int, int]:
    """Return (start, end) char offsets for first occurrence or (-1, -1)."""
    if not needle:
        return (-1, -1)
    i = haystack.find(needle)
    if i == -1:
        return (-1, -1)
    return (i, i + len(needle))


@dataclass
class ExtractedSpan:
    """One extracted UA content span with audit provenance."""

    text: str
    norm: str
    tokens: list[str]
    source: str  # e.g. "curriculum/.../module.md:1234-1456" or yaml#act-...
    kind: str
    char_start: int = -1
    char_end: int = -1


def extract_from_module_md(md_path: Path) -> list[ExtractedSpan]:
    """Extract UA learner content from module.md.

    Includes: fenced UA example blocks (```text etc), UA prose paragraphs (B1+),
    dialogue turns inside fences. Strips frontmatter, headings, English gloss tables,
    UI scaffolding, markup.
    """
    raw = md_path.read_text(encoding="utf-8")
    spans: list[ExtractedSpan] = []

    # Strip YAML frontmatter
    content = re.sub(r"^---\s*\n[\s\S]*?\n---\s*\n?", "", raw, count=1)
    # Strip HTML comments document-wide with a newline-aware pattern.  A per-line
    # `<!--.*?-->` (the previous approach in strip_md_inline) silently leaked
    # MULTI-LINE comments — including multi-line `<!-- INJECT_ACTIVITY: ... -->`
    # markers — into the extracted prose, skewing overlap results.
    # (CodeQL py/bad-tag-filter, high severity: "does not match comments with newlines".)
    content = re.sub(r"<!--[\s\S]*?-->", "", content)

    # Fenced UA example blocks (dialogues, examples)
    fence_re = re.compile(r"```(?:text|uk|ua|)\s*\n([\s\S]*?)\n```", re.IGNORECASE)
    for m in fence_re.finditer(content):
        block = m.group(1).strip()
        if is_mostly_ukrainian(block) or has_cyrillic(block):
            abs_start = m.start(1)
            abs_end = m.end(1)
            norm = normalize_text(block)
            toks = tokenize(norm)
            spans.append(
                ExtractedSpan(
                    text=block,
                    norm=norm,
                    tokens=toks,
                    source=f"{md_path}:{abs_start}-{abs_end}",
                    kind="fenced-ua",
                    char_start=abs_start,
                    char_end=abs_end,
                )
            )

    # UA-heavy prose lines / paragraphs (B1+ teaching prose is UA; A1 filters out)
    # Walk lines, skip obvious non-content.
    lines = content.splitlines(keepends=True)
    offset = 0
    for line in lines:
        stripped = line.strip()
        # Skip structural / English / tables
        if not stripped:
            offset += len(line)
            continue
        if stripped.startswith(("#", "<!--", "import ", "export ", "| ---")):
            offset += len(line)
            continue
        if stripped.startswith("|") and (
            re.search(r"\b(English|Meaning|Gloss|Support|Translation|Vitia|Olenka|Good|Let's)\b", stripped, re.I)
            or ("|" in stripped and re.search(r"[A-Za-z]{4,}", stripped))
        ):
            # Skip any table row that mixes UA with English gloss/support
            offset += len(line)
            continue
        if re.match(r"^\s*\|?\s*(English|Meaning|Gloss|Support)\b", stripped, re.I):
            offset += len(line)
            continue

        clean = strip_md_inline(stripped)
        if has_cyrillic(clean) and is_mostly_ukrainian(clean, 0.15) and len(clean) >= 8:
            # Only keep substantial phrases (avoid single words in English scaffolding)
            s, e = _find_offsets(raw, clean)  # best effort in raw
            if s == -1:
                s, e = offset, offset + len(line)
            norm = normalize_text(clean)
            toks = tokenize(norm)
            spans.append(
                ExtractedSpan(
                    text=clean,
                    norm=norm,
                    tokens=toks,
                    source=f"{md_path}:{s}-{e}",
                    kind="prose-ua",
                    char_start=s,
                    char_end=e,
                )
            )
        offset += len(line)

    # Dedup by normalized text (same content may appear in table + fence)
    seen = set()
    unique: list[ExtractedSpan] = []
    for sp in spans:
        key = sp.norm
        if key and key not in seen:
            seen.add(key)
            unique.append(sp)
    return unique


def flatten_activities(raw: Any) -> list[dict]:
    """Normalize activities YAML shapes to flat list of dicts (V1 list / V2 inline+workbook)."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        collected: list[dict] = []
        for bucket in ("inline", "workbook"):
            b = raw.get(bucket)
            if isinstance(b, list):
                collected.extend(item for item in b if isinstance(item, dict))
        if not collected:
            wrapped = raw.get("activities")
            if isinstance(wrapped, list):
                collected.extend(item for item in wrapped if isinstance(item, dict))
        return collected
    return []


def _get_str(d: dict | Any, key: str, default: str = "") -> str:
    v = d.get(key, default) if isinstance(d, dict) else getattr(d, key, default)
    return str(v) if v is not None else default


def _get_list(d: dict | Any, key: str) -> list[Any]:
    v = d.get(key, []) or [] if isinstance(d, dict) else getattr(d, key, []) or []
    return v if isinstance(v, list) else []


def extract_from_activities_yaml(yaml_path: Path) -> list[ExtractedSpan]:
    """Extract UA learner-facing strings from activities YAML (prompts, items, pairs, etc.)."""
    raw_text = yaml_path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw_text) or {}
    except Exception:
        data = {}
    acts = flatten_activities(data)
    spans: list[ExtractedSpan] = []

    for act in acts:
        act_id = _get_str(act, "id", "act")
        for fld in ("title", "instruction", "question", "passage", "text", "prompt"):
            val = _get_str(act, fld)
            if val and has_cyrillic(val) and len(val) >= 4:
                s, e = _find_offsets(raw_text, val)
                norm = normalize_text(val)
                spans.append(
                    ExtractedSpan(
                        text=val,
                        norm=norm,
                        tokens=tokenize(norm),
                        source=f"{yaml_path}#act:{act_id}:{fld}@{s}",
                        kind=f"activity-{fld}",
                        char_start=s,
                        char_end=e,
                    )
                )

        for item in _get_list(act, "items"):
            if not isinstance(item, dict):
                continue
            for fld in ("sentence", "question", "text", "passage", "explanation", "prompt"):
                val = _get_str(item, fld)
                if val and has_cyrillic(val) and len(val) >= 4:
                    s, e = _find_offsets(raw_text, val)
                    norm = normalize_text(val)
                    spans.append(
                        ExtractedSpan(
                            text=val,
                            norm=norm,
                            tokens=tokenize(norm),
                            source=f"{yaml_path}#act:{act_id}:item:{fld}@{s}",
                            kind=f"activity-item-{fld}",
                            char_start=s,
                            char_end=e,
                        )
                    )
            for opt in _get_list(item, "options"):
                val = _get_str(opt, "text") if isinstance(opt, dict) else str(opt)
                if val and has_cyrillic(val) and len(val) >= 3:
                    s, e = _find_offsets(raw_text, val)
                    norm = normalize_text(val)
                    spans.append(
                        ExtractedSpan(
                            text=val,
                            norm=norm,
                            tokens=tokenize(norm),
                            source=f"{yaml_path}#act:{act_id}:opt@{s}",
                            kind="activity-option",
                            char_start=s,
                            char_end=e,
                        )
                    )

        for pair in _get_list(act, "pairs"):
            if isinstance(pair, dict):
                for side in ("left", "right"):
                    val = _get_str(pair, side)
                    if val and has_cyrillic(val) and len(val) >= 3:
                        s, e = _find_offsets(raw_text, val)
                        norm = normalize_text(val)
                        spans.append(
                            ExtractedSpan(
                                text=val,
                                norm=norm,
                                tokens=tokenize(norm),
                                source=f"{yaml_path}#act:{act_id}:pair:{side}@{s}",
                                kind=f"activity-pair-{side}",
                                char_start=s,
                                char_end=e,
                            )
                        )
            elif isinstance(pair, (list, tuple)) and len(pair) >= 2:
                for _i, v in enumerate(pair[:2]):
                    val = str(v)
                    if val and has_cyrillic(val) and len(val) >= 3:
                        s, e = _find_offsets(raw_text, val)
                        norm = normalize_text(val)
                        spans.append(
                            ExtractedSpan(
                                text=val,
                                norm=norm,
                                tokens=tokenize(norm),
                                source=f"{yaml_path}#act:{act_id}:pair@{s}",
                                kind="activity-pair",
                                char_start=s,
                                char_end=e,
                            )
                        )

    # Dedup
    seen = set()
    unique: list[ExtractedSpan] = []
    for sp in spans:
        if sp.norm and sp.norm not in seen:
            seen.add(sp.norm)
            unique.append(sp)
    return unique


def extract_module_content(
    level_or_path: str | Path, slug: str | None = None
) -> tuple[list[ExtractedSpan], dict[str, Any]]:
    """High level extractor for a module.

    Accepts either a path to module.md / module dir, or level+slug.
    Returns (spans, meta)
    """
    if isinstance(level_or_path, (str, Path)) and Path(level_or_path).exists():
        p = Path(level_or_path)
        if p.is_file() and p.name == "module.md":
            md_path = p
            mod_dir = p.parent
        elif p.is_dir():
            md_path = p / "module.md"
            mod_dir = p
        else:
            md_path = p
            mod_dir = p.parent
    else:
        # level + slug
        root = Path("curriculum/l2-uk-en")
        if slug is None:
            raise ValueError("slug required when passing level")
        level = str(level_or_path)
        mod_dir = root / level / slug
        md_path = mod_dir / "module.md"

    if not md_path.exists():
        raise FileNotFoundError(f"No module.md at {md_path}")

    spans = extract_from_module_md(md_path)

    # activities.yaml candidates (flat + subdir per brief)
    act_candidates = [
        mod_dir / "activities.yaml",
        mod_dir / "activities" / (md_path.stem + ".yaml"),
        md_path.with_suffix(".activities.yaml"),
    ]
    for yml in act_candidates:
        if yml.exists():
            spans.extend(extract_from_activities_yaml(yml))
            break

    # Also support legacy discovery? No — only the checked-in module content.

    meta = {
        "module_path": str(md_path),
        "extraction_spec": EXTRACTION_SPEC_VERSION,
        "num_spans": len(spans),
    }
    return spans, meta


def module_tokens_from_spans(spans: list[ExtractedSpan]) -> list[str]:
    """Build single normalized token sequence for the whole module (order of appearance)."""
    all_tokens: list[str] = []
    seen_norm = set()
    for sp in spans:
        # Avoid re-adding exact duplicate blocks
        if sp.norm in seen_norm:
            continue
        seen_norm.add(sp.norm)
        all_tokens.extend(sp.tokens)
    return all_tokens


# ----------------------------- Index + metrics -----------------------------


@dataclass
class VerbatimReport:
    module: str
    extraction_spec: str
    k: int
    df_n: int
    total_prose_tokens: int
    max_contiguous_run: int  # raw (never DF suppressed)
    max_contiguous_run_df_filtered: int
    overlap_ratio: float
    top_offense: dict[str, Any] | None = None
    df_excluded_count: int = 0
    verified_quote_excludes: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    corpus_hash: str = ""
    indexed_corpora: list[str] = field(default_factory=list)
    scope_note: str | None = None


class ShingleIndex:
    """Persisted inverted shingle index + DF + corpus hash guard."""

    def __init__(self, db_path: Path | str, k: int = K_DEFAULT):
        self.db_path = Path(db_path) if db_path != ":memory:" else db_path
        self.k = k
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS postings (
                shingle_key TEXT NOT NULL,
                corpus TEXT NOT NULL,
                chunk_id TEXT NOT NULL,
                char_offset INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_post_shingle ON postings(shingle_key);
            CREATE TABLE IF NOT EXISTS shingle_df (
                shingle_key TEXT PRIMARY KEY,
                df INTEGER NOT NULL
            );
            """
        )
        self.conn.commit()

    def get_meta(self, key: str, default: str | None = None) -> str | None:
        row = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row[0] if row else default

    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def corpus_hash_matches(self, fp: str, corpora: list[tuple[str, str, str, str]]) -> bool:
        stored = self.get_meta("corpus_hash")
        k_stored = self.get_meta("k")
        spec = self.get_meta("extraction_spec")
        stored_corpora_json = self.get_meta("indexed_corpora")

        requested_labels = [c[3] for c in corpora]
        try:
            stored_corpora = json.loads(stored_corpora_json) if stored_corpora_json else []
        except Exception:
            stored_corpora = []

        return (
            stored == fp
            and k_stored == str(self.k)
            and spec == EXTRACTION_SPEC_VERSION
            and stored_corpora == requested_labels
        )

    def close(self) -> None:
        self.conn.close()

    def build(
        self,
        sources_conn: sqlite3.Connection,
        corpora: list[tuple[str, str, str, str]] | None = None,
        progress: bool = False,
    ) -> str:
        """Build (or rebuild) from sources_conn. Returns the computed corpus fingerprint."""
        if corpora is None:
            corpora = FULL_CORPORA + SELF_CORPORA

        # Compute fingerprint (content sensitive but cheap)
        fp = self._compute_fingerprint(sources_conn, corpora)
        if self.corpus_hash_matches(fp, corpora):
            if progress:
                print("Index up-to-date for corpus hash; skipping rebuild.")
            return fp

        # Rebuild
        self.conn.executescript("DELETE FROM postings; DELETE FROM shingle_df; DELETE FROM meta;")
        self.conn.commit()

        shingle_to_chunks: dict[str, set[tuple[str, str]]] = defaultdict(set)
        total_shingles = 0  # post-deduplication count (number of actual postings inserted)
        total_shingles_pre_dedup = 0  # pre-deduplication raw occurrence count

        for table, id_col, text_col, corpus_label in corpora:
            try:
                rows = sources_conn.execute(
                    f"SELECT {id_col} AS cid, {text_col} AS txt FROM {table} ORDER BY {id_col}"
                ).fetchall()
            except sqlite3.OperationalError:
                continue
            for row in rows:
                cid = str(row["cid"] or "")
                txt = row["txt"] or ""
                norm = normalize_text(txt)
                toks = tokenize(norm)
                shs = make_shingles(toks, self.k)
                for sh in shs:
                    shingle_to_chunks[sh].add((corpus_label, cid))
                total_shingles_pre_dedup += len(shs)
                # insert postings (char_offset 0 is sufficient; LCS recovers exact)
                # deduplicate postings to unique (shingle_key, corpus, chunk_id) before insert
                if shs:
                    unique_shs = list(dict.fromkeys(shs))
                    total_shingles += len(unique_shs)
                    self.conn.executemany(
                        "INSERT INTO postings (shingle_key, corpus, chunk_id, char_offset) VALUES (?, ?, ?, 0)",
                        [(sh, corpus_label, cid) for sh in unique_shs],
                    )
            if progress:
                print(f"  indexed {len(rows)} from {corpus_label} ({table})")

        # DF table
        df_rows = [(sh, len(chs)) for sh, chs in shingle_to_chunks.items()]
        if df_rows:
            self.conn.executemany("INSERT OR REPLACE INTO shingle_df (shingle_key, df) VALUES (?, ?)", df_rows)

        self.set_meta("corpus_hash", fp)
        self.set_meta("k", str(self.k))
        self.set_meta("extraction_spec", EXTRACTION_SPEC_VERSION)
        self.set_meta("total_shingles", str(total_shingles))
        self.set_meta("total_shingles_pre_dedup", str(total_shingles_pre_dedup))
        self.set_meta("indexed_corpora", json.dumps([c[3] for c in corpora]))
        self.conn.commit()

        if progress:
            print(
                f"Index built. fingerprint={fp} shingles~{total_shingles} (pre-dedup~{total_shingles_pre_dedup})"
            )
        return fp

    def _compute_fingerprint(self, conn: sqlite3.Connection, corpora: list) -> str:
        """Content-based fingerprint: hash (label, id, norm(text)) per row in deterministic ID order.
        Ensures text mutations (same ID) cause rebuild. Uses full rows, not just count+sample IDs.
        """
        h = hashlib.sha256()
        h.update(EXTRACTION_SPEC_VERSION.encode())
        h.update(f"k={self.k}".encode())
        for table, id_col, text_col, label in corpora:
            try:
                # ORDER BY guarantees stable order for hashing across runs/insert orders
                rows = conn.execute(
                    f"SELECT {id_col} AS cid, {text_col} AS txt FROM {table} ORDER BY {id_col}"
                ).fetchall()
                h.update(f"{label}:{table}:n={len(rows)}".encode())
                for r in rows:
                    cid = str(r["cid"] or "")
                    txt = r["txt"] or ""
                    ntxt = normalize_text(txt)
                    # hash the actual content too
                    h.update(f"{label}|{cid}|{ntxt}".encode())
            except Exception:
                h.update(f"missing:{label}".encode())
        return h.hexdigest()[:28]

    def df_for(self, shingle_key: str) -> int:
        row = self.conn.execute("SELECT df FROM shingle_df WHERE shingle_key = ?", (shingle_key,)).fetchone()
        return int(row[0]) if row else 0

    def postings_for(self, shingle_key: str) -> list[tuple[str, str]]:
        # Deterministic order so reports and [0] picks are stable regardless of insert history
        rows = self.conn.execute(
            "SELECT corpus, chunk_id FROM postings WHERE shingle_key = ? ORDER BY corpus, chunk_id LIMIT 50",
            (shingle_key,),
        ).fetchall()
        return [(r["corpus"], r["chunk_id"]) for r in rows]

    def get_chunk_text(self, sources_conn: sqlite3.Connection, corpus: str, chunk_id: str) -> str:
        table_map = {
            "textbooks": ("textbooks", "chunk_id"),
            "literary": ("literary_texts", "chunk_id"),
            "external": ("external_articles", "chunk_id"),
            "ukrainian_wiki": ("ukrainian_wiki", "passage_id"),
            "wikipedia": ("wikipedia", "title"),
        }
        tinfo = table_map.get(corpus)
        if not tinfo:
            return ""
        table, idc = tinfo
        try:
            row = sources_conn.execute(f"SELECT text FROM {table} WHERE {idc} = ? LIMIT 1", (chunk_id,)).fetchone()
            return row[0] if row else ""
        except Exception:
            return ""


def longest_common_substring_tokens(a: list[str], b: list[str]) -> int:
    """Length of longest contiguous token run (uses difflib for speed)."""
    if not a or not b:
        return 0
    sm = SequenceMatcher(None, a, b, autojunk=False)
    m = sm.find_longest_match(0, len(a), 0, len(b))
    return m.size


def compute_metrics(
    module_tokens: list[str],
    index: ShingleIndex,
    sources_conn: sqlite3.Connection,
    df_n: int = DF_N_DEFAULT,
    verify_quote_fn: Callable[[str, str], float] | None = None,
) -> VerbatimReport:
    """Core deterministic computation. Returns full report (no side effects)."""
    indexed_corpora_meta = index.get_meta("indexed_corpora")
    if indexed_corpora_meta is None:
        raise ValueError("Missing indexed_corpora in index metadata")
    try:
        indexed_corpora = json.loads(indexed_corpora_meta)
    except Exception:
        indexed_corpora = []

    corpus_hash = index.get_meta("corpus_hash", "")

    # Check if scope is non-default
    default_corpora = FULL_CORPORA + SELF_CORPORA
    default_labels = {c[3] for c in default_corpora}
    scope_note = None
    if set(indexed_corpora) != default_labels:
        scope_note = SCOPED_CORPUS_WARNING

    if verify_quote_fn is None:

        def _no_verify(author: str, txt: str) -> float:
            return 0.0

        verify_quote_fn = _no_verify

    total = len(module_tokens)
    if total == 0:
        return VerbatimReport(
            module="",
            extraction_spec=index.get_meta("extraction_spec") or EXTRACTION_SPEC_VERSION,
            k=index.k,
            df_n=df_n,
            total_prose_tokens=0,
            max_contiguous_run=0,
            max_contiguous_run_df_filtered=0,
            overlap_ratio=0.0,
            corpus_hash=corpus_hash,
            indexed_corpora=indexed_corpora,
            scope_note=scope_note,
        )

    mod_shingles = make_shingles(module_tokens, index.k)
    sh_to_pos: dict[str, list[int]] = defaultdict(list)
    for pos, sh in enumerate(mod_shingles):
        sh_to_pos[sh].append(pos)

    # Collect hits — now with per-source tracking for correct max_run and verify exclusion
    hit_shingles: set[str] = set()
    df_excluded: set[str] = set()
    verified_excludes: list[dict] = []
    candidate_sources: list[tuple[str, str, str]] = []  # (corpus, chunk, sh)

    # (corpus, chunk_id) -> set of module shingle-start positions matched from *that* source chunk
    source_positions: dict[tuple[str, str], set[int]] = defaultdict(set)
    # token positions to exclude from ratio due to verified attributed quote
    verified_token_positions: set[int] = set()

    for sh in mod_shingles:
        df = index.df_for(sh)
        if df >= df_n:
            df_excluded.add(sh)
            # DF excluded still participate in per-source max_run (retain high-DF for genuine runs)
        posts = index.postings_for(sh)
        if posts:
            hit_shingles.add(sh)
            modposs = sh_to_pos[sh]
            # pick first (now stable due to ORDER BY in postings) for legacy LCS
            c, cid = posts[0]
            candidate_sources.append((c, cid, sh))
            for c2, cid2 in posts:
                source_positions[(c2, cid2)].update(modposs)
            # verify using real source author (not empty) + shingle text for attribution
            # require matched source author for a real attribution
            for c2, cid2 in posts:
                author = ""
                try:
                    tbl = "textbooks" if c2 == "textbooks" else ("literary_texts" if c2 == "literary" else None)
                    idc = "chunk_id"
                    if tbl:
                        row = sources_conn.execute(
                            f"SELECT author FROM {tbl} WHERE {idc} = ? LIMIT 1", (cid2,)
                        ).fetchone()
                        author = str(row[0] or "") if row else ""
                except Exception:
                    author = ""
                conf = verify_quote_fn(author or "", sh)
                if conf >= 0.85 and author:
                    # mark the k-tokens of this sh for exclusion from ratio only
                    for p in modposs:
                        for t in range(p, min(p + index.k, total)):
                            verified_token_positions.add(t)
                    verified_excludes.append(
                        {
                            "text": sh,
                            "author": author,
                            "corpus": c2,
                            "chunk_id": cid2,
                            "conf": conf,
                            "excluded_from_ratio": True,
                        }
                    )
                    # do not break: allow all matching shingles of the quote to be recorded/excluded

    # raw max run: per source chunk (bug7), high-DF retained via source_positions
    max_raw = 0
    for (_c, _cid), posset in source_positions.items():
        run = _chained_run_len(module_tokens, posset, index.k)
        if run > max_raw:
            max_raw = run
    if not source_positions:
        max_raw = _chained_run_len(module_tokens, set(), index.k)

    # DF-filtered max run: per source chunk (bug7, same as max_raw) and MATCHED only, with
    # high-DF shingle positions removed so the run breaks on high-DF connectors.  It must NOT
    # count non-matched or cross-chunk positions — doing so fabricated a run (incl. a full run
    # on zero-match prose).  Empty source_positions (no matches) => 0.
    df_excluded_positions: set[int] = set()
    for sh in df_excluded:
        for p in sh_to_pos.get(sh, ()):
            df_excluded_positions.add(p)
    max_df_filt = 0
    for (_c, _cid), posset in source_positions.items():
        run = _chained_run_len(module_tokens, posset - df_excluded_positions, index.k)
        if run > max_df_filt:
            max_df_filt = run

    # overlap tokens for ratio: ONLY shingles that actually matched postings (bug1), minus DF, minus verified (bug2)
    covered: set[int] = set()
    for sh in hit_shingles - df_excluded:
        for p in sh_to_pos[sh]:
            for t in range(p, min(p + index.k, total)):
                if t not in verified_token_positions:
                    covered.add(t)
    covered -= verified_token_positions

    overlap_count = len(covered)
    ratio = overlap_count / total if total else 0.0

    # LCS for true longest on offending sources
    lcs_max = 0
    top: dict[str, Any] | None = None
    seen_chunks: set[tuple[str, str]] = set()
    for c, cid, sh in candidate_sources:
        if (c, cid) in seen_chunks:
            continue
        seen_chunks.add((c, cid))
        src_text = index.get_chunk_text(sources_conn, c, cid)
        if not src_text:
            continue
        src_norm = normalize_text(src_text)
        src_toks = tokenize(src_norm)
        l = longest_common_substring_tokens(module_tokens, src_toks)
        if l > lcs_max:
            lcs_max = l
            # recover example matched text (first hit sh)
            top = {
                "corpus": c,
                "chunk_id": cid,
                "lcs_run": l,
                "matched_shingle": sh,
            }

    # If a long LCS > max_raw, prefer it (shingle broke on high-DF connectors)
    effective_max = max(max_raw, lcs_max)
    if top:
        top["effective_run"] = effective_max

    # Note: verified excludes for ratio are populated during hit collection (with real author + provenance).
    # The legacy top-offense verify (empty author) is intentionally not used to mutate ratio here;
    # max_contiguous_run is left unchanged by design (even for verified quotes).

    report = VerbatimReport(
        module="",
        extraction_spec=index.get_meta("extraction_spec") or EXTRACTION_SPEC_VERSION,
        k=index.k,
        df_n=df_n,
        total_prose_tokens=total,
        max_contiguous_run=effective_max,
        max_contiguous_run_df_filtered=max_df_filt,
        overlap_ratio=round(ratio, 6),
        top_offense=top,
        df_excluded_count=len(df_excluded),
        verified_quote_excludes=verified_excludes,
        notes=[f"DF allowlist N={df_n} (ratio only)", "LCS used for true max run"],
        corpus_hash=corpus_hash,
        indexed_corpora=indexed_corpora,
        scope_note=scope_note,
    )
    return report


def _chained_run_len(tokens: list[str], hit_start_positions: set[int], k: int) -> int:
    """Compute longest contiguous word run from set of matching shingle start positions."""
    if not tokens or not hit_start_positions:
        return 0
    n = len(tokens)
    max_run = 0
    i = 0
    while i <= n - k:
        if i in hit_start_positions:
            run = k
            j = i
            while j + 1 <= n - k and (j + 1) in hit_start_positions:
                run += 1
                j += 1
            max_run = max(max_run, run)
            i = j + 1
        else:
            i += 1
    return max_run


# ----------------------------- CLI + sweep ---------------------------------


def open_sources(db_path: Path | str) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def make_default_verify_fn(sources_db: Path | str) -> Callable[[str, str], float]:
    """Best-effort verify_quote using direct SQL + difflib (no rapidfuzz dep)."""

    def _fn(author: str, text: str) -> float:
        if not text or len(text) < 6:
            return 0.0
        try:
            conn = open_sources(sources_db)
            # Prefer literary
            q = normalize_text(text)
            rows = conn.execute(
                "SELECT text, author, chunk_id FROM literary_texts WHERE text LIKE ? LIMIT 5",
                (f"%{text[:40]}%",),
            ).fetchall()
            best = 0.0
            for r in rows:
                if author:
                    a = str(r["author"] or "").lower()
                    if author.lower() not in a:
                        continue
                sm = SequenceMatcher(None, q, normalize_text(r["text"] or ""))
                best = max(best, sm.ratio())
            conn.close()
            return best
        except Exception:
            return 0.0

    return _fn


def analyze_module(
    module_path: Path | str,
    sources_db: Path | str,
    index_db: Path | str | None = None,
    k: int = K_DEFAULT,
    df_n: int = DF_N_DEFAULT,
    verify_fn: Callable[[str, str], float] | None = None,
    corpora: list[tuple[str, str, str, str]] | None = None,
) -> VerbatimReport:
    """End-to-end for one module (used by CLI and tests)."""
    spans, _meta = extract_module_content(module_path)
    mod_tokens = module_tokens_from_spans(spans)
    mod_label = str(Path(module_path).parent.name) if isinstance(module_path, (str, Path)) else "unknown"

    sources_conn = open_sources(sources_db)
    if index_db is None:
        index_db = get_default_index_db_path(sources_db, k, corpora)
    idx = ShingleIndex(index_db, k=k)

    fp = idx.build(sources_conn, corpora=corpora, progress=False)
    # ensure matches
    _ = fp

    if verify_fn is None:
        verify_fn = make_default_verify_fn(sources_db)

    report = compute_metrics(mod_tokens, idx, sources_conn, df_n=df_n, verify_quote_fn=verify_fn)
    report.module = mod_label
    # enrich top with module source offset if possible
    if report.top_offense:
        report.top_offense["module"] = mod_label

    sources_conn.close()
    idx.close()
    return report


def cmd_analyze(args: argparse.Namespace) -> int:
    rpt = analyze_module(
        args.module,
        args.sources_db,
        index_db=args.index_db,
        k=args.k,
        df_n=args.df_n,
        corpora=args.corpora_resolved,
    )
    out = {
        "module": rpt.module,
        "k": rpt.k,
        "df_n": rpt.df_n,
        "total_prose_tokens": rpt.total_prose_tokens,
        "max_contiguous_run": rpt.max_contiguous_run,
        "max_contiguous_run_df_filtered": rpt.max_contiguous_run_df_filtered,
        "overlap_ratio": rpt.overlap_ratio,
        "top_offense": rpt.top_offense,
        "df_excluded_count": rpt.df_excluded_count,
        "verified_quote_excludes": rpt.verified_quote_excludes,
        "notes": rpt.notes,
        "extraction_spec": rpt.extraction_spec,
        "corpus_hash": rpt.corpus_hash,
        "indexed_corpora": rpt.indexed_corpora,
    }
    if rpt.scope_note is not None:
        out["scope_note"] = rpt.scope_note
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def cmd_build_index(args: argparse.Namespace) -> int:
    sources_conn = open_sources(args.sources_db)
    idx_path = args.index_db or get_default_index_db_path(args.sources_db, args.k, args.corpora_resolved)
    idx = ShingleIndex(idx_path, k=args.k)
    fp = idx.build(sources_conn, corpora=args.corpora_resolved, progress=True)
    print(f"OK corpus_hash={fp} index={idx_path}")
    sources_conn.close()
    idx.close()
    return 0


def cmd_baseline_sweep(args: argparse.Namespace) -> int:
    """Mode for orchestrator to invoke on real corpus after merge. Not executed in PR tests."""
    root = Path("curriculum/l2-uk-en")
    modules = []
    for md in root.glob("*/*/module.md"):
        if "/audit/" in str(md) or "/meta/" in str(md):
            continue
        modules.append(md)
    modules = sorted(modules)[: args.limit or 9999]

    sources_conn = open_sources(args.sources_db)
    idx_path = args.index_db or get_default_index_db_path(args.sources_db, args.k, args.corpora_resolved)
    idx = ShingleIndex(idx_path, k=args.k)
    _ = idx.build(sources_conn, corpora=args.corpora_resolved, progress=args.verbose)

    results = []
    for md in modules:
        spans, _ = extract_module_content(md)
        toks = module_tokens_from_spans(spans)
        rpt = compute_metrics(toks, idx, sources_conn, df_n=args.df_n)
        rpt.module = f"{md.parent.parent.name}/{md.parent.name}"
        results.append(
            {
                "module": rpt.module,
                "tokens": rpt.total_prose_tokens,
                "max_run": rpt.max_contiguous_run,
                "ratio": rpt.overlap_ratio,
            }
        )
        if args.verbose:
            print(rpt.module, rpt.max_contiguous_run, rpt.overlap_ratio)

    corpus_hash = idx.get_meta("corpus_hash", "")
    indexed_corpora_json = idx.get_meta("indexed_corpora")
    if indexed_corpora_json is None:
        raise ValueError("Missing indexed_corpora in index metadata")
    try:
        indexed_corpora = json.loads(indexed_corpora_json)
    except Exception:
        indexed_corpora = []

    out = {
        "count": len(results),
        "results": results[:50],
        "corpus_hash": corpus_hash,
        "indexed_corpora": indexed_corpora,
        "extraction_spec": EXTRACTION_SPEC_VERSION,
    }

    default_corpora = FULL_CORPORA + SELF_CORPORA
    default_labels = {c[3] for c in default_corpora}
    if set(indexed_corpora) != default_labels:
        out["scope_note"] = SCOPED_CORPUS_WARNING

    print(json.dumps(out, indent=2, ensure_ascii=False))
    sources_conn.close()
    idx.close()
    return 0


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Deterministic verbatim overlap gate (advisory)")
    p.add_argument("--sources-db", default="data/sources.db", help="Path to sources.db (or :memory: for tests)")
    p.add_argument("--index-db", default=None, help="Explicit index sqlite path")
    p.add_argument("--k", type=int, default=K_DEFAULT, help="Shingle size (words)")
    p.add_argument("--df-n", type=int, default=DF_N_DEFAULT, help="DF threshold for ratio allowlist")
    p.add_argument(
        "--corpus",
        action="append",
        default=None,
        help="Corpus to index/analyze (repeatable or comma-separated list of: textbooks, literary, external, ukrainian_wiki, wikipedia)",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="Analyze one module")
    a.add_argument("module", help="Path to module.md or module directory")
    a.set_defaults(func=cmd_analyze)

    b = sub.add_parser("build-index", help="Force (re)build the shingle index")
    b.set_defaults(func=cmd_build_index)

    s = sub.add_parser("baseline-sweep", help="Sweep many/all modules (orchestrator use)")
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--verbose", action="store_true")
    s.set_defaults(func=cmd_baseline_sweep)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_argparser()
    args = parser.parse_args(argv)

    try:
        args.corpora_resolved = parse_corpora_labels(args.corpus)
    except argparse.ArgumentTypeError as e:
        parser.error(str(e))

    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

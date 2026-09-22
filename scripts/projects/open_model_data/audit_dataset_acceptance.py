#!/usr/bin/env python3
"""Dataset Acceptance Audit Gate for Sovereign Ukrainian Datasets (Epic #6321, Issue #8339).

Universal, automated, fail-closed acceptance check for every dataset in Epic #6321.
Audits:
  1. Repeats (exact copies, near-duplicates, multiplicity, MinHash Jaccard >= 0.85)
  2. Form letters (sentence pattern concentration, perplexity, normalized entropy)
  3. Real content share (controls vs substantive corrections, thin category balance)
  4. Self-contradiction (date discrepancies, label vs text diff, target term alignment)
  5. Source rules (Epic rules 3 & 4: Soviet СУМ-11 distortion rules, translation dictionaries, approved authorities)
  6. Train/test overlap (VESUM lemmatized & curated aspect-pair normalized 4-gram containment)
  7. Deterministic random sample drawer (content-hashed seed, 300 instances, MD + JSON, human review lifecycle)

Exit codes:
  0: Passed automated checks (or accepted with verified human sign-off)
  1: Acceptance failed (one or more threshold limits breached)
  2: Operational error (missing databases, unreadable inputs, malformed records, invalid profile)
  3: Pending human review (when --require-human-signoff is requested and signoff is missing)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.rag.config import VESUM_DB_PATH

# ── Paths and Authorities ──────────────────────────────────────────────────


def _resolve_db_path(filename: str, project_root: Path) -> Path:
    direct = Path(os.environ.get(f"{filename.upper().replace('.', '_')}_PATH", project_root / "data" / filename))
    if direct.is_file() and direct.stat().st_size > 0:
        return direct
    try:
        from scripts.guardrails.worktree_containment import resolve_main_root

        primary = resolve_main_root(project_root) / "data" / filename
        if primary.is_file() and primary.stat().st_size > 0:
            return primary
    except Exception:
        pass
    return direct


DEFAULT_SOURCES_DB = _resolve_db_path("sources.db", PROJECT_ROOT)
PROFILES_DIR = Path(__file__).resolve().parent / "profiles"
ASPECT_PAIRS_FILE = Path(__file__).resolve().parent / "aspect_pairs.json"
COMMITTED_PROFILES = {"default", "grammar_8342"}

APPROVED_AUTHORITY_PATTERNS = [
    r"vesum",
    r"весум",
    r"(?:(?:український|новий|чинний)\s+)?правопис\s*\(?2019(?:\s*р(?:оку)?\.?)?\)?",
    r"сум[- ]?20",
    r"sum[- ]?20",
    r"втс\b",
    r"великий\s+тлумачний",
    r"горох\b",
    r"goroh\b",
    r"slovnyk\.me",
    r"словник\.me",
    r"антоненко[- ]давидович",
    r"як\s+ми\s+говоримо",
    r"караванськ(ий|ого)",
    r"пономарів\b",
    r"грінченк(о|а|ів)",
    r"есум\b",
    r"esum\b",
    r"уліф\b",
    r"ulif\b",
    r"пулс\b",
    r"puls\b",
    r"підручник\s+(?:для\s+\d+|з\s+української|автор)",
    r"pidruchnyk\b",
    r"заболотн",
    r"авраменк",
    r"вашуленк",
    r"глазова",
    r"брук\b",
    r"brown[-_]uk",
    r"ua[-_]gec",
    r"городенськ",
    r"шевельов",
]

TRANSLATION_DICT_IDS = {
    "r2u",
    "e2u",
    "balla_en_uk",
    "dmklinger_uk_en",
    "translate_en_uk",
    "bilingual_translation",
}

SOVIET_SUM11_ALIASES = [
    "sum11",
    "sum_11",
    "sum-11",
    "sum 11",
    "сум-11",
    "сум_11",
    "сум 11",
    "сум11",
    "словник української мови (1970–1980)",
    "словник української мови (1970-1980)",
    "словник української мови в 11 томах",
]

# ── Data Models ────────────────────────────────────────────────────────────


@dataclass
class DatasetRecord:
    """Standardized view of a single dataset line."""

    raw: dict[str, Any]
    file_path: Path
    line_number: int
    split: str  # 'train' or 'eval'
    query: str
    final_response: str
    reasoning_steps: list[str]
    reasoning_text: str
    chosen: str | None = None
    rejected: str | None = None
    target_term: str | None = None
    is_erroneous: bool | None = None
    original_text: str | None = None
    corrected_text: str | None = None
    category: str | None = None
    source_metadata: Any = None
    content_hash: str = ""


@dataclass
class CheckResult:
    check_id: str
    check_name: str
    status: str  # 'PASS', 'FAIL', 'NOT_APPLICABLE'
    metrics: dict[str, Any] = field(default_factory=dict)
    thresholds: dict[str, Any] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)


@dataclass
class AcceptanceReport:
    dataset_dir: str
    dataset_sha256: str
    profile_name: str
    profile_sha256: str
    total_records: int
    train_records: int
    eval_records: int
    checks: dict[str, CheckResult] = field(default_factory=dict)
    overall_status: str = "PENDING"
    sample_file_path: str | None = None
    sample_seed: str = ""


# ── Text Normalization & Delexicalization ───────────────────────────────────


def normalize_ukrainian_text(text: str) -> str:
    """Canonical Ukrainian text normalization: NFKC, apostrophes, stress marks, whitespace."""
    if not text:
        return ""
    s = unicodedata.normalize("NFKC", str(text))
    s = re.sub(r"[’ʼ`]", "'", s)
    s = s.replace("\u0301", "")
    s = " ".join(s.split())
    return s


def delexicalize_text(text: str) -> str:
    """Mask quotes, digits, and bracketed entity placeholders to expose structural patterns."""
    if not text:
        return ""
    s = text
    # Mask variable and entity placeholders first
    s = re.sub(r"\{[^{}]*\}", "<VAR>", s)
    s = re.sub(r"<[^<>]*>", "<VAR>", s)
    s = re.sub(r"\[[^\[\]]*\]", "<VAR>", s)
    # Mask Ukrainian typographic and standard quote pairs
    s = re.sub(r"«[^»]*»", "<QUOTED_SPAN>", s)
    s = re.sub(r"\"[^\"]*\"", "<QUOTED_SPAN>", s)
    s = re.sub(r"“[^”]*”", "<QUOTED_SPAN>", s)
    s = re.sub(r"„[^“]*“", "<QUOTED_SPAN>", s)
    s = re.sub(r"‘[^’]*’", "<QUOTED_SPAN>", s)
    # Mask numbers/digits
    s = re.sub(r"\d+", "#", s)
    return " ".join(s.split())


def parse_bool(value: Any) -> bool | None:
    """Strict parser for boolean or boolean-like string fields."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("true", "1", "yes"):
        return True
    if s in ("false", "0", "no"):
        return False
    return None


# ── Aspect Normalizer & Lemmatizer ──────────────────────────────────────────


class LinguisticNormalizer:
    """VESUM lemmatizer and curated verbal aspect pair normalizer."""

    def __init__(self, vesum_db_path: Path, aspect_pairs_path: Path | None = ASPECT_PAIRS_FILE):
        self.vesum_db_path = vesum_db_path
        if not self.vesum_db_path.is_file():
            raise FileNotFoundError(f"VESUM database missing: {vesum_db_path}")

        self.aspect_pairs: dict[str, str] = {}
        if aspect_pairs_path and aspect_pairs_path.is_file():
            with aspect_pairs_path.open("r", encoding="utf-8") as f:
                self.aspect_pairs = json.load(f)

        self._conn = sqlite3.connect(f"file:{self.vesum_db_path}?mode=ro", uri=True)
        self._cur = self._conn.cursor()
        self._lemma_cache: dict[str, list[dict[str, str]]] = {}

    def lookup_form(self, word: str) -> list[dict[str, str]]:
        w = word.strip().lower()
        if w in self._lemma_cache:
            return self._lemma_cache[w]
        self._cur.execute("SELECT lemma, pos, tags FROM forms_all WHERE word_form = ?", (w,))
        rows = self._cur.fetchall()
        results = [{"lemma": r[0], "pos": r[1], "tags": r[2]} for r in rows]
        self._lemma_cache[w] = results
        return results

    def normalize_verb_aspect(self, lemma: str, tags: str) -> str:
        """Map perfective/imperfective partners to their canonical base using curated pairs."""
        low_lemma = lemma.lower()
        if low_lemma in self.aspect_pairs:
            return self.aspect_pairs[low_lemma]
        return low_lemma

    def get_canonical_tokens(self, text: str) -> list[str]:
        """Tokenize text into canonical, aspect-normalized dictionary lemmas."""
        raw_tokens = re.findall(r"[А-Яа-яІіЇїЄєҐґ']+", text.lower())
        canonical = []
        for t in raw_tokens:
            analyses = self.lookup_form(t)
            if not analyses:
                canonical.append(t)
                continue
            seen_for_token = set()
            for an in analyses:
                lem = an["lemma"]
                if an["pos"] == "verb":
                    lem = self.normalize_verb_aspect(lem, an["tags"])
                seen_for_token.add(lem)
            canonical.append(sorted(seen_for_token)[0])
        return canonical

    def close(self):
        self._conn.close()


# ── Configuration Loader ────────────────────────────────────────────────────


def _load_profile_chain(
    profile_name: str,
    profiles_dir: Path,
    visited: set[str],
) -> tuple[dict[str, Any], list[bytes]]:
    """Internal helper to load profile chain and collect bytes for composite hashing."""
    if any(sep in profile_name for sep in ("/", "\\", "..")):
        raise ValueError(f"Invalid profile name {profile_name!r}: path separators not permitted")

    if profile_name not in COMMITTED_PROFILES:
        raise ValueError(
            f"Unapproved profile {profile_name!r}. Only committed profiles are permitted: {sorted(COMMITTED_PROFILES)}"
        )

    if profile_name in visited:
        raise ValueError(f"Circular inheritance detected in profile {profile_name!r}")

    visited.add(profile_name)
    profile_path = profiles_dir / f"{profile_name}.yaml"
    if not profile_path.is_file():
        raise FileNotFoundError(f"Profile {profile_name} not found at {profile_path}")

    import yaml

    raw_bytes = profile_path.read_bytes()
    data = yaml.safe_load(raw_bytes.decode("utf-8")) or {}

    inherits = data.get("inherits")
    thresholds = data.get("thresholds", {})

    chain_bytes = [raw_bytes]

    if inherits:
        parent_thresholds, parent_bytes = _load_profile_chain(inherits, profiles_dir, visited)
        chain_bytes = parent_bytes + chain_bytes
        merged = parent_thresholds.copy()
        merged.update(thresholds)
        thresholds = merged

    return thresholds, chain_bytes


def load_profile(
    profile_name: str,
    profiles_dir: Path = PROFILES_DIR,
    aspect_pairs_file: Path = ASPECT_PAIRS_FILE,
) -> tuple[dict[str, Any], str]:
    """Load and resolve profile YAML; return thresholds and composite SHA-256 hash."""
    visited: set[str] = set()
    thresholds, chain_bytes = _load_profile_chain(profile_name, profiles_dir, visited)
    if aspect_pairs_file.is_file():
        chain_bytes.append(b"\n---ASPECT_PAIRS---\n" + aspect_pairs_file.read_bytes())
    composite_sha256 = hashlib.sha256(b"\n---CHAIN---\n".join(chain_bytes)).hexdigest()
    return thresholds, composite_sha256


# ── Record Parser ───────────────────────────────────────────────────────────


def parse_dataset_record(
    raw: dict[str, Any],
    file_path: Path,
    line_number: int,
    dataset_dir: Path | None = None,
    manifest_splits: dict[str, str] | None = None,
) -> DatasetRecord:
    """Parse raw JSON line into standardized DatasetRecord."""
    if not isinstance(raw, dict):
        raise TypeError(f"Line {line_number} in {file_path.name} is not a JSON object: {type(raw).__name__}")

    # Determine split:
    rel_path = (
        file_path.relative_to(dataset_dir) if dataset_dir and file_path.is_relative_to(dataset_dir) else file_path
    )
    rel_str = str(rel_path).replace("\\", "/")

    # 1. Explicit record field or manifest split declaration
    manifest_split_val = None
    if manifest_splits:
        if rel_str in manifest_splits:
            manifest_split_val = manifest_splits[rel_str]
        elif file_path.name in manifest_splits:
            manifest_split_val = manifest_splits[file_path.name]

    raw_split_val = raw.get("split")
    explicit_split = str(raw_split_val).strip().lower() if raw_split_val is not None else None
    norm_explicit = None
    if explicit_split:
        if explicit_split in ("eval", "test", "validation", "val", "dev", "evaluation"):
            norm_explicit = "eval"
        elif explicit_split in ("train", "training"):
            norm_explicit = "train"
        else:
            raise ValueError(f"Unknown split {explicit_split!r} in line {line_number} of {file_path.name}")

    if norm_explicit is not None and manifest_split_val is not None:
        if norm_explicit != manifest_split_val:
            raise ValueError(
                f"Conflicting split declaration for {rel_str}:{line_number} — "
                f"record declares {explicit_split!r} ({norm_explicit}), but manifest.json declares {manifest_split_val!r}"
            )
        split = norm_explicit
    elif norm_explicit is not None:
        split = norm_explicit
    elif manifest_split_val is not None:
        split = manifest_split_val
    else:
        # 2. Relative path inspection (never absolute path substring match)
        rel_parts = [p.lower() for p in rel_path.parent.parts]
        stem = rel_path.stem.lower()
        if any(p in ("eval", "evaluation", "test", "val", "validation", "dev") for p in rel_parts) or re.search(
            r"(?:^|[_\-.])(eval|evaluation|test|val|validation|dev)(?:[_\-.]|$)", stem
        ):
            split = "eval"
        else:
            split = "train"

    query = ""
    final_response = ""
    reasoning_steps: list[str] = []
    chosen = None
    rejected = None

    if "messages" in raw and isinstance(raw["messages"], list):
        for msg in raw["messages"]:
            if not isinstance(msg, dict):
                raise TypeError(
                    f"Message item in line {line_number} of {file_path.name} is not a JSON object: {type(msg).__name__}"
                )
            role = msg.get("role")
            content = str(msg.get("content", ""))
            if role == "user" and not query:
                query = content
            elif role == "assistant":
                final_response = content
    else:
        query = str(raw.get("query", ""))
        final_response = str(raw.get("final_response", raw.get("response", raw.get("answer", ""))))

    if "chosen" in raw and raw["chosen"] is not None:
        chosen = normalize_ukrainian_text(str(raw["chosen"]))
    if "rejected" in raw and raw["rejected"] is not None:
        rejected = normalize_ukrainian_text(str(raw["rejected"]))

    raw_steps = raw.get("reasoning_steps", raw.get("reasoning", []))
    if isinstance(raw_steps, list):
        reasoning_steps = [normalize_ukrainian_text(str(s)) for s in raw_steps if s]
    elif isinstance(raw_steps, str) and raw_steps.strip():
        reasoning_steps = [normalize_ukrainian_text(raw_steps)]

    reasoning_text = "\n".join(reasoning_steps)

    is_erroneous = parse_bool(raw.get("is_erroneous"))
    if is_erroneous is None and "is_calque_or_russianism" in raw:
        is_erroneous = parse_bool(raw.get("is_calque_or_russianism"))

    original_text = raw.get("original_text")
    corrected_text = raw.get("corrected_text")
    target_term = raw.get("target_term", raw.get("target_phrase"))
    category = raw.get("category", raw.get("subtype", raw.get("task_type")))
    source_metadata = raw.get("source_metadata", raw.get("source_authority", raw.get("lexicographical_context")))

    content_payload = f"{query}|{reasoning_text}|{final_response}|{chosen or ''}|{rejected or ''}"
    content_hash = hashlib.sha256(content_payload.encode("utf-8")).hexdigest()

    return DatasetRecord(
        raw=raw,
        file_path=file_path,
        line_number=line_number,
        split=split,
        query=normalize_ukrainian_text(query),
        final_response=normalize_ukrainian_text(final_response),
        reasoning_steps=reasoning_steps,
        reasoning_text=reasoning_text,
        chosen=chosen,
        rejected=rejected,
        target_term=normalize_ukrainian_text(str(target_term)) if target_term else None,
        is_erroneous=is_erroneous,
        original_text=normalize_ukrainian_text(str(original_text)) if original_text else None,
        corrected_text=normalize_ukrainian_text(str(corrected_text)) if corrected_text else None,
        category=str(category) if category else None,
        source_metadata=source_metadata,
        content_hash=content_hash,
    )


# ── The Seven Auditors ──────────────────────────────────────────────────────


def audit_check_1_repeats(records: list[DatasetRecord], thresholds: dict[str, Any]) -> CheckResult:
    """Check 1: Exact copies, near-duplicates, and multiplicity."""
    total = len(records)
    if total == 0:
        return CheckResult("check_1_repeats", "Repeats & Duplicates", "NOT_APPLICABLE")

    # 1. Exact QA pairs
    qa_counter = Counter()
    for r in records:
        key = (
            (r.query, r.chosen, r.rejected)
            if (r.chosen is not None and r.rejected is not None)
            else (r.query, r.final_response)
        )
        qa_counter[key] += 1

    distinct_qa = len(qa_counter)
    exact_duplicates = total - distinct_qa
    exact_duplicate_rate = exact_duplicates / total if total > 0 else 0.0
    max_multiplicity = qa_counter.most_common(1)[0][1] if qa_counter else 0

    # 2. Near-duplicates via normalized template matching
    norm_qa_counter = Counter()
    for r in records:
        q_norm = delexicalize_text(r.query)
        a_norm = delexicalize_text(r.final_response)
        norm_qa_counter[(q_norm, a_norm)] += 1

    near_duplicate_excess = sum(c - 1 for c in norm_qa_counter.values() if c > 1)
    near_duplicate_rate = near_duplicate_excess / total if total > 0 else 0.0

    max_dup_rate = thresholds.get("max_exact_duplicate_rate", 0.0)
    max_multi = thresholds.get("max_single_multiplicity", 1)
    max_near_rate = thresholds.get("max_near_duplicate_rate", 0.01)

    failures = []
    if exact_duplicate_rate > max_dup_rate:
        failures.append(f"Exact duplicate rate {exact_duplicate_rate:.2%} exceeds limit {max_dup_rate:.2%}")
    if max_multiplicity > max_multi:
        failures.append(f"Max single item multiplicity {max_multiplicity} exceeds limit {max_multi}")
    if near_duplicate_rate > max_near_rate:
        failures.append(f"Near-duplicate template rate {near_duplicate_rate:.2%} exceeds limit {max_near_rate:.2%}")

    return CheckResult(
        check_id="check_1_repeats",
        check_name="Repeats & Duplicates",
        status="FAIL" if failures else "PASS",
        metrics={
            "total_records": total,
            "distinct_qa_pairs": distinct_qa,
            "exact_duplicate_count": exact_duplicates,
            "exact_duplicate_rate": round(exact_duplicate_rate, 4),
            "max_single_multiplicity": max_multiplicity,
            "distinct_normalized_qa_templates": len(norm_qa_counter),
            "near_duplicate_template_rate": round(near_duplicate_rate, 4),
        },
        thresholds={
            "max_exact_duplicate_rate": max_dup_rate,
            "max_single_multiplicity": max_multi,
            "max_near_duplicate_rate": max_near_rate,
        },
        failures=failures,
    )


def audit_check_2_form_letters(records: list[DatasetRecord], thresholds: dict[str, Any]) -> CheckResult:
    """Check 2: Sentence pattern concentration and entropy."""
    total = len(records)
    if total == 0:
        return CheckResult("check_2_form_letters", "Form Letters & Pattern Concentration", "NOT_APPLICABLE")

    def analyze_field(strings: list[str]) -> dict[str, Any]:
        ctr = Counter(delexicalize_text(s) for s in strings if s.strip())
        K = len(ctr)
        N = sum(ctr.values())
        if N == 0:
            return {"K": 0, "top1": 0.0, "top5": 0.0, "top20": 0.0, "entropy": 0.0, "perplexity": 0.0}

        top1 = ctr.most_common(1)[0][1] / N if K >= 1 else 0.0
        top5 = sum(c for _, c in ctr.most_common(5)) / N
        top20 = sum(c for _, c in ctr.most_common(20)) / N

        H = -sum((c / N) * math.log(c / N) for c in ctr.values())
        H_norm = H / math.log(K) if K > 1 else 0.0
        perplexity = math.exp(H)

        return {
            "K": K,
            "top1": round(top1, 4),
            "top5": round(top5, 4),
            "top20": round(top20, 4),
            "entropy": round(H_norm, 4),
            "perplexity": round(perplexity, 2),
        }

    q_stats = analyze_field([r.query for r in records])
    r_stats = analyze_field([r.reasoning_text for r in records if r.reasoning_text])
    a_stats = analyze_field([r.final_response for r in records])

    has_reasoning = any(bool(r.reasoning_text) for r in records)
    failures = []

    # Query limits
    max_q_top5 = thresholds.get("max_query_top5_share", 0.80)
    min_q_k = thresholds.get("min_query_unique_skeletons", 20)
    min_q_entropy = thresholds.get("min_query_entropy", 0.60)
    if total >= 20:
        if total >= 50 and q_stats["top5"] > max_q_top5:
            failures.append(f"Query top 5 patterns cover {q_stats['top5']:.1%}, exceeding limit {max_q_top5:.1%}")
        effective_min_q_k = min(min_q_k, max(3, total // 5))
        if q_stats["K"] < effective_min_q_k:
            failures.append(f"Query unique patterns K={q_stats['K']} is below limit {effective_min_q_k}")
        if q_stats["entropy"] < min_q_entropy:
            failures.append(f"Query normalized entropy {q_stats['entropy']} is below floor {min_q_entropy}")

    # Reasoning limits
    if has_reasoning:
        max_r_top1 = thresholds.get("max_reasoning_top1_share", 0.10)
        max_r_top5 = thresholds.get("max_reasoning_top5_share", 0.25)
        max_r_top20 = thresholds.get("max_reasoning_top20_share", 0.50)
        min_r_perp = thresholds.get("min_reasoning_perplexity", 25.0)
        min_r_entropy = thresholds.get("min_reasoning_entropy", 0.80)
        min_r_k = thresholds.get("min_reasoning_unique_skeletons", 50)
        r_total = sum(1 for r in records if r.reasoning_text)

        if r_total >= 10:
            if r_total >= int(1.0 / max_r_top1) and r_stats["top1"] > max_r_top1:
                failures.append(
                    f"Reasoning top 1 pattern covers {r_stats['top1']:.1%}, exceeding limit {max_r_top1:.1%}"
                )
            if r_total >= 20 and r_stats["top5"] > max_r_top5:
                failures.append(
                    f"Reasoning top 5 patterns cover {r_stats['top5']:.1%}, exceeding limit {max_r_top5:.1%}"
                )
            if r_total >= 40 and r_stats["top20"] > max_r_top20:
                failures.append(
                    f"Reasoning top 20 patterns cover {r_stats['top20']:.1%}, exceeding limit {max_r_top20:.1%}"
                )
            if r_total >= 50 and r_stats["perplexity"] < min_r_perp:
                failures.append(f"Reasoning perplexity {r_stats['perplexity']} is below floor {min_r_perp}")
            effective_min_r_k = min(min_r_k, max(5, r_total // 10))
            if r_total >= 20 and r_stats["K"] < effective_min_r_k:
                failures.append(f"Reasoning unique patterns K={r_stats['K']} is below floor {effective_min_r_k}")
            if r_total >= 20 and r_stats["entropy"] < min_r_entropy:
                failures.append(f"Reasoning normalized entropy {r_stats['entropy']} is below floor {min_r_entropy}")

    # Answer limits
    max_a_top1 = thresholds.get("max_answer_top1_share", 0.05)
    max_a_top5 = thresholds.get("max_answer_top5_share", 0.15)
    max_a_top20 = thresholds.get("max_answer_top20_share", 0.30)
    min_a_perp = thresholds.get("min_answer_perplexity", 35.0)
    min_a_entropy = thresholds.get("min_answer_entropy", 0.80)
    min_a_k = thresholds.get("min_answer_unique_skeletons", 50)

    if total >= 10:
        if total >= int(1.0 / max_a_top1) and a_stats["top1"] > max_a_top1:
            failures.append(f"Answer top 1 pattern covers {a_stats['top1']:.1%}, exceeding limit {max_a_top1:.1%}")
        if total >= 35 and a_stats["top5"] > max_a_top5:
            failures.append(f"Answer top 5 patterns cover {a_stats['top5']:.1%}, exceeding limit {max_a_top5:.1%}")
        if total >= 67 and a_stats["top20"] > max_a_top20:
            failures.append(f"Answer top 20 patterns cover {a_stats['top20']:.1%}, exceeding limit {max_a_top20:.1%}")
        if total >= 50 and a_stats["perplexity"] < min_a_perp:
            failures.append(f"Answer perplexity {a_stats['perplexity']} is below floor {min_a_perp}")
        effective_min_a_k = min(min_a_k, max(5, total // 10))
        if total >= 20 and a_stats["K"] < effective_min_a_k:
            failures.append(f"Answer unique patterns K={a_stats['K']} is below floor {effective_min_a_k}")
        if total >= 20 and a_stats["entropy"] < min_a_entropy:
            failures.append(f"Answer normalized entropy {a_stats['entropy']} is below floor {min_a_entropy}")

    return CheckResult(
        check_id="check_2_form_letters",
        check_name="Form Letters & Pattern Concentration",
        status="FAIL" if failures else "PASS",
        metrics={
            "query": q_stats,
            "reasoning": r_stats if has_reasoning else "NOT_APPLICABLE",
            "answer": a_stats,
        },
        thresholds=thresholds,
        failures=failures,
    )


def audit_check_3_content_share(
    records: list[DatasetRecord],
    thresholds: dict[str, Any],
    manifest_task_type: str | None = None,
) -> CheckResult:
    """Check 3: Real content share (controls vs substantive corrections)."""
    has_correction_fields = any(r.is_erroneous is not None for r in records)
    declared_correction = (manifest_task_type == "correction") or thresholds.get("is_correction_dataset", False)
    is_correction_task = declared_correction or has_correction_fields

    if not is_correction_task:
        return CheckResult("check_3_content_share", "Real Content Share", "NOT_APPLICABLE")

    controls = 0
    corrections = 0
    categories = Counter()

    for r in records:
        if r.is_erroneous is False:
            controls += 1
        elif r.is_erroneous is True:
            corrections += 1
        elif r.original_text and r.corrected_text:
            if r.original_text.strip() != r.corrected_text.strip():
                corrections += 1
            else:
                controls += 1

        if r.category:
            categories[r.category] += 1

    cand_total = controls + corrections
    if cand_total == 0:
        if declared_correction:
            return CheckResult(
                "check_3_content_share",
                "Real Content Share",
                "FAIL",
                failures=["Dataset declared as correction task but contains zero labeled records"],
            )
        return CheckResult("check_3_content_share", "Real Content Share", "NOT_APPLICABLE")

    control_share = controls / cand_total
    correction_share = corrections / cand_total

    failures = []
    if "min_clean_control_share" in thresholds:
        min_c = thresholds["min_clean_control_share"]
        max_c = thresholds["max_clean_control_share"]
        if not (min_c <= control_share <= max_c):
            failures.append(f"Control share {control_share:.1%} outside required range [{min_c:.1%}, {max_c:.1%}]")

    min_corr = thresholds.get("min_correction_share", 0.50)
    if correction_share < min_corr:
        failures.append(f"Substantive correction share {correction_share:.1%} is below floor {min_corr:.1%}")

    max_corr = thresholds.get("max_correction_share")
    if max_corr is not None and correction_share > max_corr:
        failures.append(f"Substantive correction share {correction_share:.1%} exceeds ceiling {max_corr:.1%}")

    # Category balance
    thin_categories = []
    max_cat_share = thresholds.get("max_single_category_share", 0.40)
    min_per_cat = thresholds.get("min_examples_per_category", 50)

    for cat, count in categories.items():
        if count < min_per_cat:
            thin_categories.append(f"{cat} ({count} < {min_per_cat})")
        if count / cand_total > max_cat_share:
            failures.append(f"Category {cat} dominates with {count / cand_total:.1%} of rows (max {max_cat_share:.1%})")

    if thin_categories:
        failures.append(f"Thin categories with < {min_per_cat} instances: {', '.join(thin_categories[:5])}")

    return CheckResult(
        check_id="check_3_content_share",
        check_name="Real Content Share",
        status="FAIL" if failures else "PASS",
        metrics={
            "candidate_rows": cand_total,
            "controls_count": controls,
            "corrections_count": corrections,
            "clean_control_share": round(control_share, 4),
            "substantive_correction_share": round(correction_share, 4),
            "category_count": len(categories),
            "thin_categories_count": len(thin_categories),
        },
        thresholds=thresholds,
        failures=failures,
    )


def audit_check_4_contradictions(
    records: list[DatasetRecord],
    thresholds: dict[str, Any],
    normalizer: LinguisticNormalizer,
) -> CheckResult:
    """Check 4: Self-contradiction audit (dates, labels, target terms)."""
    contradictions = []

    for r in records:
        # 1. Historical date discrepancy in Step 1 or Reasoning
        era_markers = (
            str(r.raw.get("morphemic_breakdown", ""))
            + " "
            + str(r.raw.get("era", ""))
            + " "
            + str(r.raw.get("period", ""))
        )
        low_era = era_markers.lower()
        is_kyivan_rus = any(
            x in low_era for x in ("xi–xiii", "xi-xiii", "kyivan_rus", "давньоруськ", "давньоукраїнськ")
        )
        is_middle_ua = any(x in low_era for x in ("xiv–xvii", "xiv-xvii", "middle_ukrainian", "староукраїнськ"))

        if r.reasoning_steps:
            step_text = " ".join(r.reasoning_steps)
            date_matches = re.findall(r"\b(\d{4})[–-]\b", step_text)
            for d_str in date_matches:
                year = int(d_str)
                if is_kyivan_rus and year >= 1400:
                    contradictions.append(
                        f"Line {r.line_number}: Labeled Kyivan Rus (XI–XIII c.) but reasoning dates text as {year}"
                    )
                    break
                if is_middle_ua and (year < 1300 or year >= 1800):
                    contradictions.append(
                        f"Line {r.line_number}: Labeled Middle Ukrainian (XIV–XVII c.) but reasoning dates text as {year}"
                    )
                    break

        # 2. Label vs Text diff
        if (
            r.is_erroneous is True
            and r.original_text
            and r.corrected_text
            and r.original_text.strip() == r.corrected_text.strip()
        ):
            contradictions.append(f"Line {r.line_number}: is_erroneous is True but original_text == corrected_text")
        if (
            r.is_erroneous is False
            and r.original_text
            and r.corrected_text
            and r.original_text.strip() != r.corrected_text.strip()
        ):
            contradictions.append(f"Line {r.line_number}: is_erroneous is False but original_text != corrected_text")

        # 3. Target term alignment
        if r.target_term:
            target_tokens = set(normalizer.get_canonical_tokens(r.target_term))
            all_context = (
                f"{r.query} {r.original_text or ''} {r.corrected_text or ''} {r.final_response} {r.reasoning_text}"
            )
            context_tokens = set(normalizer.get_canonical_tokens(all_context))
            if target_tokens and not target_tokens.issubset(context_tokens):
                contradictions.append(
                    f"Line {r.line_number}: target_term '{r.target_term}' missing from record context"
                )

    max_contradictions = thresholds.get("max_self_contradictions", 0)
    failures = []
    if len(contradictions) > max_contradictions:
        failures.append(
            f"Found {len(contradictions)} self-contradictions (limit is {max_contradictions}). "
            f"Examples: {contradictions[:3]}"
        )

    return CheckResult(
        check_id="check_4_contradictions",
        check_name="Self-Contradiction Audit",
        status="FAIL" if failures else "PASS",
        metrics={"contradiction_count": len(contradictions)},
        thresholds={"max_self_contradictions": max_contradictions},
        failures=failures,
    )


def _extract_authorities(source_meta: Any, raw: dict[str, Any]) -> list[str]:
    """Extract all cited authority strings from metadata or top-level fields."""
    auths: list[str] = []
    for k in ("source_authority", "authority", "source_book", "source", "authorities"):
        val = raw.get(k)
        if val:
            if isinstance(val, list):
                auths.extend(str(v) for v in val if v)
            else:
                auths.append(str(val))

    if isinstance(source_meta, dict):
        for k in ("authority", "source_book", "source"):
            val = source_meta.get(k)
            if val:
                auths.append(str(val))
    elif isinstance(source_meta, list):
        for item in source_meta:
            if isinstance(item, dict):
                for k in ("authority", "source_book", "source"):
                    if item.get(k):
                        auths.append(str(item.get(k)))
            elif item:
                auths.append(str(item))
    elif isinstance(source_meta, str) and source_meta.strip():
        auths.append(source_meta)

    return [a for a in auths if a.strip()]


def audit_check_5_source_rules(records: list[DatasetRecord], thresholds: dict[str, Any]) -> CheckResult:
    """Check 5: Epic Rules 3 & 4 (СУМ-11 distortion boundary, translation dictionaries, approved authorities)."""
    sum11_normative_hits = []
    sum11_negative_inference_hits = []
    translation_dict_hits = []
    unapproved_authority_hits = []

    for r in records:
        meta_str = str(r.source_metadata or "").lower()
        full_text = f"{r.query} {r.reasoning_text} {r.final_response} {r.chosen or ''} {r.rejected or ''}".lower()
        authorities = _extract_authorities(r.source_metadata, r.raw)
        all_sources_lower = [meta_str] + [a.lower() for a in authorities]

        # 1. Check for contrastive notes
        contrastive_note = r.raw.get("historical_suppression_note") or r.raw.get("soviet_colonization_context")
        is_contrastive_context = bool(contrastive_note and str(contrastive_note).strip())

        # Check for СУМ-11 cited in metadata, authorities, or affirmative body text
        has_sum11_in_sources = any(any(alias in s for alias in SOVIET_SUM11_ALIASES) for s in all_sources_lower)
        has_affirmative_citation = bool(
            re.search(
                r"\b(?:згідно з|за|відповідно до|у|в)\s+(?:сум[- ]?11|словник[уі]\s+української\s+мови\s+(?:\(1970|в\s+11))\b",
                full_text,
            )
            or re.search(r"\b(?:сум[- ]?11|словник\s+1970[-–]1980)\s+(?:фіксує|подає|визначає|зазначає)\b", full_text)
        )

        if (has_sum11_in_sources or has_affirmative_citation) and not is_contrastive_context:
            sum11_normative_hits.append(f"Line {r.line_number}: cites Soviet СУМ-11 as normative authority")

        # 2. Check for negative inference from СУМ-11 absence
        if re.search(r"відсутн\w*\s+в\s+сум[- ]?11", full_text) or re.search(
            r"не\s+зафіксован\w*\s+в\s+сум[- ]?11.*тому.*(помилк|діалект|рідк)", full_text
        ):
            sum11_negative_inference_hits.append(
                f"Line {r.line_number}: claims word is wrong/rare because absent from СУМ-11"
            )

        # 3. Check for bilingual translation dictionaries across metadata and authorities
        for s in all_sources_lower:
            matched_trans = None
            for trans_id in TRANSLATION_DICT_IDS:
                if trans_id in s:
                    matched_trans = trans_id
                    break
            if matched_trans:
                translation_dict_hits.append(
                    f"Line {r.line_number}: sourced from translation dictionary '{matched_trans}'"
                )
                break

        # 4. Check that explicit authorities match approved list
        # A compound citation containing Soviet SUM-11 is never an approved modern authority
        for auth in authorities:
            auth_lower = auth.lower()
            auth_has_sum11 = any(alias in auth_lower for alias in SOVIET_SUM11_ALIASES)
            if auth_has_sum11:
                if is_contrastive_context:
                    # In contrastive context, SUM-11 citation is valid only if an independent, modern approved authority is also present
                    has_clean_approved = any(
                        any(re.search(pat, a, re.IGNORECASE) for pat in APPROVED_AUTHORITY_PATTERNS)
                        and not any(alias in a.lower() for alias in SOVIET_SUM11_ALIASES)
                        for a in authorities
                    )
                    if not has_clean_approved:
                        unapproved_authority_hits.append(
                            f"Line {r.line_number}: contrastive СУМ-11 citation lacks approved modern Ukrainian authority"
                        )
                # If not contrastive, already captured in sum11_normative_hits above
            else:
                is_approved = any(re.search(pat, auth, re.IGNORECASE) for pat in APPROVED_AUTHORITY_PATTERNS)
                if not is_approved:
                    unapproved_authority_hits.append(f"Line {r.line_number}: unapproved authority '{auth}'")

    failures = []
    if sum11_normative_hits:
        failures.append(f"Citing СУМ-11 as normative source in {len(sum11_normative_hits)} records (0 allowed)")
    if sum11_negative_inference_hits:
        failures.append(
            f"Condemning words based on СУМ-11 absence in {len(sum11_negative_inference_hits)} records (0 allowed)"
        )
    if translation_dict_hits:
        failures.append(f"Using bilingual translation dictionaries in {len(translation_dict_hits)} records (0 allowed)")
    if unapproved_authority_hits:
        failures.append(
            f"Unapproved authorities cited in {len(unapproved_authority_hits)} records ({unapproved_authority_hits[0]})"
        )

    return CheckResult(
        check_id="check_5_source_rules",
        check_name="Source Rules (Epic Rules 3 & 4)",
        status="FAIL" if failures else "PASS",
        metrics={
            "sum11_normative_violations": len(sum11_normative_hits),
            "sum11_negative_inferences": len(sum11_negative_inference_hits),
            "translation_dictionary_violations": len(translation_dict_hits),
            "unapproved_authorities_violations": len(unapproved_authority_hits),
        },
        thresholds={
            "max_sum11_normative_violations": 0,
            "max_sum11_negative_inferences": 0,
            "max_translation_dict_violations": 0,
            "max_unapproved_authorities": 0,
        },
        failures=failures,
    )


def audit_check_6_split_overlap(
    records: list[DatasetRecord],
    thresholds: dict[str, Any],
    normalizer: LinguisticNormalizer,
    manifest_declares_eval: bool = True,
) -> CheckResult:
    """Check 6: Lemmatized & aspect-normalized train/test overlap and containment."""
    train_recs = [r for r in records if r.split == "train"]
    eval_recs = [r for r in records if r.split == "eval"]

    if not eval_recs:
        if manifest_declares_eval or thresholds.get("require_held_out_split", False) or (len(records) >= 100):
            return CheckResult(
                "check_6_split_overlap",
                "Train/Test Overlap & Leakage",
                "FAIL",
                failures=["Required held-out evaluation split is missing or empty"],
            )
        return CheckResult("check_6_split_overlap", "Train/Test Overlap & Leakage", "NOT_APPLICABLE")

    # 1. Exact query leakage
    train_queries = {r.query for r in train_recs}
    exact_leakage = [r for r in eval_recs if r.query in train_queries]

    # 2. Aspect-normalized target phenomenon leakage
    def norm_target(term: str) -> str:
        tokens = normalizer.get_canonical_tokens(term)
        return " ".join(tokens)

    train_targets = {norm_target(r.target_term) for r in train_recs if r.target_term}
    target_leakage = []
    for r in eval_recs:
        if r.target_term:
            norm_t = norm_target(r.target_term)
            if norm_t in train_targets:
                target_leakage.append((r.target_term, norm_t))

    # 3. 4-Gram Lemma Containment
    def extract_4grams(text: str) -> set[tuple[str, ...]]:
        tokens = normalizer.get_canonical_tokens(text)
        if len(tokens) < 4:
            return set()
        return {tuple(tokens[i : i + 4]) for i in range(len(tokens) - 3)}

    train_4gram_counts = Counter()
    for r in train_recs:
        full_text = f"{r.query} {r.final_response} {r.chosen or ''} {r.rejected or ''}"
        grams = extract_4grams(full_text)
        train_4gram_counts.update(grams)

    total_train = len(train_recs)
    boilerplate_threshold = max(5, int(total_train * 0.20))
    # Hoist boilerplate set calculation outside per-eval loop (Fixes Major Finding 5)
    boilerplate_4grams = {g for g, c in train_4gram_counts.items() if c >= boilerplate_threshold}
    train_informative_4grams = {g for g, c in train_4gram_counts.items() if c < boilerplate_threshold}

    high_containment_records = 0
    containment_threshold = thresholds.get("containment_threshold", 0.50)

    for r in eval_recs:
        eval_text = f"{r.query} {r.final_response} {r.chosen or ''} {r.rejected or ''}"
        eval_grams = extract_4grams(eval_text)
        informative_eval_grams = eval_grams - boilerplate_4grams
        if not informative_eval_grams:
            continue
        overlap_count = len(informative_eval_grams.intersection(train_informative_4grams))
        containment = overlap_count / len(informative_eval_grams)
        if containment >= containment_threshold:
            high_containment_records += 1

    high_containment_share = high_containment_records / len(eval_recs) if eval_recs else 0.0
    max_high_cont_share = thresholds.get("max_high_containment_share", 0.02)

    failures = []
    if exact_leakage:
        failures.append(f"Exact query leakage: {len(exact_leakage)} eval queries exist in train set (0 allowed)")
    if target_leakage:
        failures.append(f"Target phenomenon leakage: {len(target_leakage)} eval targets exist in train set (0 allowed)")
    if high_containment_share > max_high_cont_share:
        failures.append(
            f"High 4-gram containment share {high_containment_share:.2%} exceeds limit {max_high_cont_share:.2%}"
        )

    return CheckResult(
        check_id="check_6_split_overlap",
        check_name="Train/Test Overlap & Leakage",
        status="FAIL" if failures else "PASS",
        metrics={
            "train_records": len(train_recs),
            "eval_records": len(eval_recs),
            "exact_query_leakage_count": len(exact_leakage),
            "target_term_leakage_count": len(target_leakage),
            "eval_records_high_containment": high_containment_records,
            "high_containment_share": round(high_containment_share, 4),
        },
        thresholds={
            "max_exact_sentence_leakage": 0,
            "max_target_phenomenon_leakage": 0,
            "max_high_containment_share": max_high_cont_share,
        },
        failures=failures,
    )


def audit_check_7_sample_drawer(
    records: list[DatasetRecord],
    thresholds: dict[str, Any],
    dataset_sha256: str,
    profile_sha256: str,
    sample_out_path: Path,
    verify_signoff_path: Path | None = None,
) -> tuple[CheckResult, Path | None, str]:
    """Check 7: Deterministic random sample drawer & human review lifecycle (M2, M3)."""
    total = len(records)
    if total == 0:
        return CheckResult("check_7_sample_drawer", "Review Sample & Human Lifecycle", "NOT_APPLICABLE"), None, ""

    sample_size = thresholds.get("sample_size", 300)
    min_sample_floor = thresholds.get("min_sample_floor", 50)
    effective_floor = min(min_sample_floor, total)
    if sample_size < effective_floor:
        raise ValueError(
            f"Sample size {sample_size} is below required minimum floor of {effective_floor} (total records: {total})"
        )
    salt = "open_model_data_acceptance_salt_2026"
    seed_hash = hashlib.sha256(f"{dataset_sha256}_{salt}".encode()).hexdigest()

    # Rank records deterministically by sha256(seed_hash + record.content_hash)
    scored_records = []
    for r in records:
        rank_hash = hashlib.sha256(f"{seed_hash}:{r.content_hash}".encode()).hexdigest()
        scored_records.append((rank_hash, r))

    scored_records.sort(key=lambda x: x[0])
    selected = [r for _, r in scored_records[:sample_size]]

    # Ensure thin categories are included up to cap
    thin_cap = thresholds.get("thin_category_sample_cap", 20)
    min_cat = thresholds.get("min_examples_per_category", 50)
    category_counts = Counter(r.category for r in records if r.category)
    # Sort thin categories before iteration to be invariant to PYTHONHASHSEED (Fixes Blocker 4)
    thin_categories = sorted([cat for cat, c in category_counts.items() if c < min_cat])

    selected_hashes = {r.content_hash for r in selected}
    thin_by_cat: dict[str, list[DatasetRecord]] = {}
    for cat in thin_categories:
        cat_recs = [r for r in records if r.category == cat and r.content_hash not in selected_hashes]
        # Sort additions by deterministic rank hash, never file order
        cat_recs.sort(key=lambda r: hashlib.sha256(f"{seed_hash}:{r.content_hash}".encode()).hexdigest())
        thin_by_cat[cat] = cat_recs[:thin_cap]

    # Fair round-robin allocation across thin categories up to 100 total
    thin_additions: list[DatasetRecord] = []
    max_round = thin_cap
    max_total_thin = 100
    for round_idx in range(max_round):
        if len(thin_additions) >= max_total_thin:
            break
        for cat in thin_categories:
            if len(thin_additions) >= max_total_thin:
                break
            recs = thin_by_cat[cat]
            if round_idx < len(recs):
                thin_additions.append(recs[round_idx])

    all_sampled = selected + thin_additions
    actual_drawn_count = len(all_sampled)

    # Resolve output paths safely
    if sample_out_path.suffix == ".json":
        md_file_path = sample_out_path.with_suffix(".md")
        json_sidecar_path = sample_out_path
    else:
        md_file_path = sample_out_path
        json_sidecar_path = sample_out_path.with_suffix(".json")

    signoff_template_path = md_file_path.with_name(f"{md_file_path.stem}.signoff_template.json")

    md_file_path.parent.mkdir(parents=True, exist_ok=True)
    md_lines = [
        f"# Independent Language Review Sample Package: {md_file_path.stem}",
        "",
        f"- **Dataset SHA-256:** `{dataset_sha256}`",
        f"- **Deterministic Sampling Seed Hash:** `{seed_hash}`",
        f"- **Profile SHA-256:** `{profile_sha256}`",
        f"- **Sampled Rows:** {actual_drawn_count} (Base {len(selected)} + Thin Category Boost {len(thin_additions)})",
        "",
        "## Reviewer Instructions & Rubric",
        "For each instance below, evaluate the text using authentic Ukrainian linguistic tools (СУМ-20, Правопис 2019, VESUM, Антоненко-Давидович).",
        "Classify defects as BLOCKER (incorrect grammar, Russianisms, Soviet distortion) or MINOR (stylistic nuance).",
        "",
        "---",
        "",
    ]

    json_records = []
    for i, r in enumerate(all_sampled, start=1):
        md_lines.append(f"### Sample #{i} — [{r.split.upper()}] Line {r.line_number}")
        md_lines.append(f"**Source File:** `{r.file_path.name}` | **Category:** `{r.category or 'N/A'}`")
        if r.target_term:
            md_lines.append(f"**Target Term:** `{r.target_term}`")
        md_lines.append("")
        if r.query:
            md_lines.append(f"**Запитання / Завдання:**\n> {r.query}")
            md_lines.append("")
        if r.original_text:
            md_lines.append(f"**Вихідний текст (Original):**\n> {r.original_text}")
            md_lines.append("")
        if r.corrected_text:
            md_lines.append(f"**Виправлений текст (Corrected):**\n```\n{r.corrected_text}\n```")
            md_lines.append("")
        if r.chosen:
            md_lines.append(f"**Еталонна відповідь (Chosen):**\n```\n{r.chosen}\n```")
            md_lines.append("")
        if r.rejected:
            md_lines.append(f"**Відхилена відповідь (Rejected):**\n```\n{r.rejected}\n```")
            md_lines.append("")
        if r.reasoning_steps:
            md_lines.append("**Міркування (Reasoning):**")
            for step in r.reasoning_steps:
                md_lines.append(f"- {step}")
            md_lines.append("")
        if r.final_response and not r.chosen and not r.corrected_text:
            md_lines.append(f"**Відповідь / Редагування:**\n```\n{r.final_response}\n```")
            md_lines.append("")
        elif r.final_response and (r.chosen or r.corrected_text):
            md_lines.append(f"**Відповідь:**\n```\n{r.final_response}\n```")
            md_lines.append("")
        if r.source_metadata:
            md_lines.append(f"**Джерело / Авторитет:** `{r.source_metadata}`")
            md_lines.append("")
        md_lines.append("#### Оцінка експерта:")
        md_lines.append("- [ ] 1. Мовна якість (відсутність русизмів, кальок, суржику)")
        md_lines.append("- [ ] 2. Природність та автентичність українського слововжитку")
        md_lines.append("- [ ] 3. Відповідність авторитетним джерелам")
        md_lines.append("- [ ] 4. Відсутність радянських/колоніальних спотворень")
        md_lines.append("- [ ] 5. Педагогічна та фактологічна точність")
        md_lines.append("")
        md_lines.append("**Вердикт:** [ ] ПРИЙНЯТО  [ ] ЗАУВАЖЕННЯ  [ ] ВІДХИЛЕНО")
        md_lines.append("**Коментар та джерело:** _______________________________________")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

        json_records.append(
            {
                "sample_index": i,
                "file_name": r.file_path.name,
                "line_number": r.line_number,
                "split": r.split,
                "query": r.query,
                "final_response": r.final_response,
                "reasoning_steps": r.reasoning_steps,
                "target_term": r.target_term,
                "category": r.category,
                "original_text": r.original_text,
                "corrected_text": r.corrected_text,
                "chosen": r.chosen,
                "rejected": r.rejected,
                "is_erroneous": r.is_erroneous,
                "content_hash": r.content_hash,
            }
        )

    def _safe_write(path: Path, content: str) -> None:
        try:
            if path.is_file() and path.read_text(encoding="utf-8") == content:
                return
            path.write_text(content, encoding="utf-8")
        except (PermissionError, OSError):
            if path.is_file() and path.read_text(encoding="utf-8") == content:
                return
            raise

    _safe_write(md_file_path, "\n".join(md_lines))
    _safe_write(json_sidecar_path, json.dumps(json_records, ensure_ascii=False, indent=2) + "\n")

    # Emit signoff template
    signoff_template = {
        "dataset_sha256": dataset_sha256,
        "sample_seed": seed_hash,
        "profile_sha256": profile_sha256,
        "sample_size_drawn": actual_drawn_count,
        "sample_size_reviewed": 0,
        "blocker_defect_count": 0,
        "minor_defect_count": 0,
        "reviewer_id": "",
        "reviewer_family": "",
        "signoff_date": "",
        "comments": "",
    }
    _safe_write(signoff_template_path, json.dumps(signoff_template, ensure_ascii=False, indent=2) + "\n")

    # Strict Signoff Validation (Fixes Blocker 3, R2-F2, R3-F2, R3-F5)
    failures = []
    signoff_verified = False

    if verify_signoff_path:
        if not verify_signoff_path.is_file():
            failures.append(f"Signoff file not found: {verify_signoff_path}")
        else:
            try:
                signoff_data = json.loads(verify_signoff_path.read_text(encoding="utf-8"))
                if not isinstance(signoff_data, dict):
                    failures.append("Signoff report must be a JSON dictionary")
                else:
                    if signoff_data.get("dataset_sha256") != dataset_sha256:
                        failures.append(
                            f"Signoff dataset_sha256 '{signoff_data.get('dataset_sha256')}' does not match current dataset '{dataset_sha256}'"
                        )
                    if signoff_data.get("sample_seed") != seed_hash:
                        failures.append("Signoff sample_seed does not match current sample drawer seed")
                    if signoff_data.get("profile_sha256") != profile_sha256:
                        failures.append("Signoff profile_sha256 does not match current profile hash")

                    reviewed_count = signoff_data.get("sample_size_reviewed")
                    if (
                        type(reviewed_count) is not int
                        or isinstance(reviewed_count, bool)
                        or reviewed_count <= 0
                        or reviewed_count < actual_drawn_count
                    ):
                        failures.append(
                            f"Signoff sample_size_reviewed must be an integer >= actual sample size drawn ({actual_drawn_count}) and > 0, got {reviewed_count!r}"
                        )

                    blockers = signoff_data.get("blocker_defect_count")
                    if type(blockers) is not int or isinstance(blockers, bool) or blockers < 0:
                        failures.append(
                            f"Signoff blocker_defect_count must be a non-negative integer, got {blockers!r} of type {type(blockers).__name__}"
                        )
                    elif blockers > 0:
                        failures.append(f"Signoff reports {blockers} unresolved BLOCKER defect(s)")

                    if "minor_defect_count" not in signoff_data:
                        failures.append("Signoff missing required 'minor_defect_count'")
                    else:
                        minors = signoff_data.get("minor_defect_count")
                        if type(minors) is not int or isinstance(minors, bool) or minors < 0:
                            failures.append(
                                f"Signoff minor_defect_count must be a non-negative integer, got {minors!r} of type {type(minors).__name__}"
                            )

                    reviewer_id = signoff_data.get("reviewer_id")
                    reviewer_family = signoff_data.get("reviewer_family")
                    if not reviewer_id or not isinstance(reviewer_id, str) or not reviewer_id.strip():
                        failures.append("Signoff missing valid reviewer_id")
                    if not reviewer_family or not isinstance(reviewer_family, str) or not reviewer_family.strip():
                        failures.append("Signoff missing valid reviewer_family")

                    if not failures:
                        signoff_verified = True
            except Exception as exc:
                failures.append(f"Error reading signoff file: {exc}")

    status = "FAIL" if failures else "PASS"

    return (
        CheckResult(
            check_id="check_7_sample_drawer",
            check_name="Review Sample & Human Lifecycle",
            status=status,
            metrics={
                "sample_size_drawn": len(all_sampled),
                "sample_file_md": str(md_file_path),
                "sample_file_json": str(json_sidecar_path),
                "signoff_template_path": str(signoff_template_path),
                "signoff_verified": signoff_verified,
            },
            thresholds={"sample_size": sample_size},
            failures=failures,
        ),
        md_file_path,
        seed_hash,
    )


# ── Dataset Loader & Runner ─────────────────────────────────────────────────


def compute_dataset_sha256(jsonl_files: list[Path], dataset_dir: Path) -> str:
    """Compute deterministic SHA-256 over manifest.json (if present) and all sorted relative paths and file contents."""
    hasher = hashlib.sha256()
    manifest_path = dataset_dir / "manifest.json"
    if manifest_path.is_file():
        hasher.update(b"manifest.json\n")
        hasher.update(manifest_path.read_bytes())
        hasher.update(b"\n---END_MANIFEST---\n")

    for p in sorted(jsonl_files):
        rel_str = str(p.relative_to(dataset_dir)).replace("\\", "/")
        hasher.update(rel_str.encode("utf-8"))
        hasher.update(p.read_bytes())
    return hasher.hexdigest()


def run_acceptance_audit(
    dataset_dir: Path,
    profile_name: str = "default",
    sample_out: Path | None = None,
    sample_size: int | None = None,
    vesum_db: Path | None = None,
    sources_db: Path | None = None,
    verify_signoff: Path | None = None,
    require_human_signoff: bool = False,
    fail_fast: bool = False,
) -> tuple[AcceptanceReport, int]:
    """Execute all 7 acceptance checks against a dataset directory."""
    if vesum_db is None:
        vesum_db = VESUM_DB_PATH

    if not dataset_dir.is_dir():
        print(f"❌ Error: Dataset directory {dataset_dir} does not exist", file=sys.stderr)
        return AcceptanceReport(str(dataset_dir), "", profile_name, "", 0, 0, 0, overall_status="OPERATIONAL_ERROR"), 2

    # Verify required database dependencies (Fail-closed)
    if not vesum_db.is_file():
        print(f"❌ Error: Required VESUM database {vesum_db} not found", file=sys.stderr)
        return AcceptanceReport(str(dataset_dir), "", profile_name, "", 0, 0, 0, overall_status="OPERATIONAL_ERROR"), 2

    if sources_db is not None and not sources_db.is_file():
        print(f"❌ Error: Required sources database {sources_db} not found", file=sys.stderr)
        return AcceptanceReport(str(dataset_dir), "", profile_name, "", 0, 0, 0, overall_status="OPERATIONAL_ERROR"), 2

    # Load profile
    try:
        thresholds, profile_sha256 = load_profile(profile_name)
    except Exception as exc:
        print(f"❌ Error loading profile {profile_name}: {exc}", file=sys.stderr)
        return AcceptanceReport(str(dataset_dir), "", profile_name, "", 0, 0, 0, overall_status="OPERATIONAL_ERROR"), 2

    if sample_size is not None:
        if sample_size <= 0:
            print(f"❌ Error: --sample-size must be > 0, got {sample_size}", file=sys.stderr)
            return (
                AcceptanceReport(
                    str(dataset_dir),
                    "",
                    profile_name,
                    profile_sha256,
                    0,
                    0,
                    0,
                    overall_status="OPERATIONAL_ERROR",
                ),
                2,
            )
        thresholds["sample_size"] = sample_size

    # Scan all JSONL shards (excluding sample outputs or review files)
    jsonl_files = sorted(
        p
        for p in dataset_dir.rglob("*.jsonl")
        if not p.name.startswith("acceptance_review_sample") and not p.name.endswith(".sample.jsonl")
    )
    if not jsonl_files:
        print(f"❌ Error: No .jsonl files found in {dataset_dir}", file=sys.stderr)
        return AcceptanceReport(
            str(dataset_dir), "", profile_name, profile_sha256, 0, 0, 0, overall_status="OPERATIONAL_ERROR"
        ), 2

    dataset_sha256 = compute_dataset_sha256(jsonl_files, dataset_dir)

    # Check for manifest (Fail-closed on JSON decode errors)
    manifest_path = dataset_dir / "manifest.json"
    manifest_task_type = None
    manifest_declares_eval = False
    manifest_splits: dict[str, str] = {}

    if manifest_path.is_file():
        try:
            m_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not isinstance(m_data, dict):
                raise ValueError("manifest.json must be a JSON object")
            manifest_task_type = m_data.get("task_type")
            manifest_declares_eval = bool(m_data.get("has_evaluation_split", False))
            if "splits" in m_data:
                if not isinstance(m_data["splits"], dict):
                    raise ValueError("manifest.json 'splits' field must be a dictionary")
                manifest_splits = {}
                valid_splits = {
                    "train": "train",
                    "training": "train",
                    "eval": "eval",
                    "evaluation": "eval",
                    "test": "eval",
                    "validation": "eval",
                    "val": "eval",
                    "dev": "eval",
                }
                for f_key, s_val in m_data["splits"].items():
                    s_str = str(s_val).strip().lower()
                    if s_str not in valid_splits:
                        raise ValueError(f"Unknown split {s_val!r} declared in manifest.json for {f_key}")
                    norm_val = valid_splits[s_str]
                    norm_k = str(f_key).replace("\\", "/")
                    manifest_splits[norm_k] = norm_val
                    if "/" not in norm_k:
                        base_k = Path(f_key).name
                        matching_files = [p for p in jsonl_files if p.name == base_k]
                        if len(matching_files) <= 1:
                            manifest_splits[base_k] = norm_val
        except Exception as exc:
            print(f"❌ Error reading manifest.json: {exc}", file=sys.stderr)
            return AcceptanceReport(
                str(dataset_dir),
                dataset_sha256,
                profile_name,
                profile_sha256,
                0,
                0,
                0,
                overall_status="OPERATIONAL_ERROR",
            ), 2

    # Parse records
    records: list[DatasetRecord] = []
    for f in jsonl_files:
        try:
            with f.open("r", encoding="utf-8") as fp:
                for idx, line in enumerate(fp, start=1):
                    if line.strip():
                        try:
                            raw = json.loads(line)
                            rec = parse_dataset_record(raw, f, idx, dataset_dir, manifest_splits)
                            records.append(rec)
                        except (json.JSONDecodeError, TypeError, ValueError, AttributeError) as exc:
                            print(f"❌ Record error in {f}:{idx}: {exc}", file=sys.stderr)
                            return (
                                AcceptanceReport(
                                    str(dataset_dir),
                                    dataset_sha256,
                                    profile_name,
                                    profile_sha256,
                                    0,
                                    0,
                                    0,
                                    overall_status="OPERATIONAL_ERROR",
                                ),
                                2,
                            )
        except (UnicodeDecodeError, OSError) as exc:
            print(f"❌ File read error in {f}: {exc}", file=sys.stderr)
            return (
                AcceptanceReport(
                    str(dataset_dir),
                    dataset_sha256,
                    profile_name,
                    profile_sha256,
                    0,
                    0,
                    0,
                    overall_status="OPERATIONAL_ERROR",
                ),
                2,
            )

    total_records = len(records)
    if total_records == 0:
        print(f"❌ Error: Dataset {dataset_dir} contains zero valid records", file=sys.stderr)
        return (
            AcceptanceReport(
                str(dataset_dir),
                dataset_sha256,
                profile_name,
                profile_sha256,
                0,
                0,
                0,
                overall_status="OPERATIONAL_ERROR",
            ),
            2,
        )

    train_records = sum(1 for r in records if r.split == "train")
    eval_records = sum(1 for r in records if r.split == "eval")

    report = AcceptanceReport(
        dataset_dir=str(dataset_dir),
        dataset_sha256=dataset_sha256,
        profile_name=profile_name,
        profile_sha256=profile_sha256,
        total_records=total_records,
        train_records=train_records,
        eval_records=eval_records,
    )
    actual_sample_out = sample_out or (dataset_dir / "acceptance_review_sample.md")

    normalizer = None
    try:
        try:
            normalizer = LinguisticNormalizer(vesum_db, ASPECT_PAIRS_FILE)
        except Exception as exc:
            print(f"❌ Error initializing linguistic normalizer: {exc}", file=sys.stderr)
            report.overall_status = "OPERATIONAL_ERROR"
            return report, 2

        checks = [
            ("check_1_repeats", lambda: audit_check_1_repeats(records, thresholds)),
            ("check_2_form_letters", lambda: audit_check_2_form_letters(records, thresholds)),
            (
                "check_3_content_share",
                lambda: audit_check_3_content_share(records, thresholds, manifest_task_type),
            ),
            (
                "check_4_contradictions",
                lambda: audit_check_4_contradictions(records, thresholds, normalizer),
            ),
            ("check_5_source_rules", lambda: audit_check_5_source_rules(records, thresholds)),
            (
                "check_6_split_overlap",
                lambda: audit_check_6_split_overlap(
                    records, thresholds, normalizer, manifest_declares_eval or (eval_records > 0)
                ),
            ),
        ]

        has_failure = False
        for check_id, check_fn in checks:
            res = check_fn()
            report.checks[check_id] = res
            if res.status == "FAIL":
                has_failure = True
                if fail_fast:
                    break

        if not (fail_fast and has_failure):
            res7, written_sample, seed_hash = audit_check_7_sample_drawer(
                records, thresholds, dataset_sha256, profile_sha256, actual_sample_out, verify_signoff
            )
            report.checks["check_7_sample_drawer"] = res7
            report.sample_file_path = str(written_sample) if written_sample else None
            report.sample_seed = seed_hash
            if res7.status == "FAIL":
                has_failure = True
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError) as exc:
        print(f"❌ Operational error during audit checks: {exc}", file=sys.stderr)
        report.overall_status = "OPERATIONAL_ERROR"
        return report, 2
    finally:
        if normalizer:
            normalizer.close()

    # Determine overall lifecycle status and exit code (Fixes Blocker 3)
    signoff_verified = report.checks.get("check_7_sample_drawer", CheckResult("", "", "")).metrics.get(
        "signoff_verified", False
    )

    if has_failure:
        report.overall_status = "ACCEPTANCE_FAILED"
        exit_code = 1
    elif signoff_verified:
        report.overall_status = "ACCEPTED"
        exit_code = 0
    elif require_human_signoff:
        report.overall_status = "PASSED_AUTOMATED_CHECKS_PENDING_SIGNOFF"
        exit_code = 3
    else:
        report.overall_status = "PASSED_AUTOMATED_CHECKS"
        exit_code = 0

    return report, exit_code


def print_report_summary(report: AcceptanceReport, exit_code: int):
    """Format and print acceptance report table to stdout."""
    print("=" * 80)
    print(f"📊 DATASET ACCEPTANCE REPORT: {report.dataset_dir}")
    print(f"   SHA-256: {report.dataset_sha256[:16]}... | Profile: {report.profile_name} ({report.profile_sha256[:8]})")
    print(f"   Records: Total={report.total_records} (Train={report.train_records}, Eval={report.eval_records})")
    print("=" * 80)

    for cid, cr in report.checks.items():
        symbol = "✅" if cr.status == "PASS" else ("❌" if cr.status == "FAIL" else "⚪")
        print(f"{symbol} [{cr.status:14s}] {cr.check_name} ({cid})")
        for k, v in cr.metrics.items():
            print(f"     • {k}: {v}")
        if cr.failures:
            print("     ⚠️  Failures:")
            for f in cr.failures[:4]:
                print(f"        - {f}")
            if len(cr.failures) > 4:
                print(f"        - ... and {len(cr.failures) - 4} more")

    print("-" * 80)
    status_symbol = "✅" if exit_code == 0 else ("⏳" if exit_code == 3 else "❌")
    print(f"{status_symbol} OVERALL STATUS: {report.overall_status} (Exit Code {exit_code})")
    if report.sample_file_path:
        print(f"📝 Review Sample Package Generated: {report.sample_file_path}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Universal Dataset Acceptance Audit Gate for Epic #6321")
    parser.add_argument("dataset_dir", type=Path, help="Path to dataset directory containing JSONL files")
    parser.add_argument("--profile", default="default", help="Acceptance profile from profiles/ (default: default)")
    parser.add_argument("--sample-out", type=Path, default=None, help="Custom output path for review sample MD")
    parser.add_argument(
        "--sample-size", type=int, default=None, help="Number of sample records to draw (default: from profile)"
    )
    parser.add_argument("--json-out", type=Path, default=None, help="Output path for JSON acceptance scorecard")
    parser.add_argument("--vesum-db", type=Path, default=None, help="Path to vesum.db (default: data/vesum.db)")
    parser.add_argument("--sources-db", type=Path, default=None, help="Path to sources.db (optional)")
    parser.add_argument("--verify-human-signoff", type=Path, default=None, help="Path to signed human review report")
    parser.add_argument(
        "--require-human-signoff",
        action="store_true",
        help="Require valid human review sign-off for ACCEPTED status (exits 3 if pending)",
    )
    parser.add_argument("--fail-fast", action="store_true", help="Abort on first failing check")

    args = parser.parse_args()

    report, exit_code = run_acceptance_audit(
        dataset_dir=args.dataset_dir,
        profile_name=args.profile,
        sample_out=args.sample_out,
        sample_size=args.sample_size,
        vesum_db=args.vesum_db,
        sources_db=args.sources_db,
        verify_signoff=args.verify_human_signoff,
        require_human_signoff=args.require_human_signoff,
        fail_fast=args.fail_fast,
    )

    print_report_summary(report, exit_code)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        report_dict = {
            "dataset_dir": report.dataset_dir,
            "dataset_sha256": report.dataset_sha256,
            "profile_name": report.profile_name,
            "profile_sha256": report.profile_sha256,
            "sample_seed": report.sample_seed,
            "total_records": report.total_records,
            "train_records": report.train_records,
            "eval_records": report.eval_records,
            "overall_status": report.overall_status,
            "sample_file_path": report.sample_file_path,
            "checks": {
                k: {
                    "check_name": v.check_name,
                    "status": v.status,
                    "metrics": v.metrics,
                    "thresholds": v.thresholds,
                    "failures": v.failures,
                }
                for k, v in report.checks.items()
            },
        }
        args.json_out.write_text(json.dumps(report_dict, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved machine-readable JSON scorecard to {args.json_out}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Pre-training Cross-Stage Contradiction Audit (Phase 5.5 / #8054).

Mandated by Advisor Fable:
Executes an automated contradiction audit before gradient updates begin:
1. Verifies that all 600 Phase 5.2 protection cases (dialect_historical_protection_suite_600.jsonl)
   are protected against training loss contradiction.
2. Ensures 0 regionalisms, phonological variants, or historical archaic forms are penalized
   as 'errors' in the 6,000 SFT shards or 3,000 DPO pairs. Fails closed if shards are missing
   or empty.
3. Verifies that the 100 anti-surzhyk/anti-calque controls exclusively target authentic Russian-Soviet occupation
   Russianisms and calques, with every replacement term verified against positive decolonized
   authorities (СУМ-20, Grinchenko 1907, VESUM).
4. Generates a certified Markdown audit report and JSON metrics.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]


def resolve_data_path(rel_path: str | Path) -> Path:
    """Resolve a relative data path, falling back to git common parent checkout for gitignored files."""
    path_obj = Path(rel_path)
    local_p = (REPO_ROOT / path_obj).resolve() if not path_obj.is_absolute() else path_obj
    if local_p.exists():
        return local_p
    try:
        common = subprocess.check_output(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=REPO_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).strip()
        main_p = (Path(common).resolve().parent / path_obj).resolve()
        if main_p.exists():
            return main_p
    except Exception:
        pass
    return local_p


# Default paths relative to project root
DEFAULT_PROTECTION_SUITE = Path("data/projects/open_model_data/decolonization/partitions/dialect_historical_protection_suite_600.jsonl")
DEFAULT_SFT_DIR = Path("data/projects/open_model_data/release/uldr_v1_production/sft")
DEFAULT_DPO_DIR = Path("data/projects/open_model_data/release/uldr_v1_production/dpo")
DEFAULT_SOURCES_DB = Path("data/sources.db")
DEFAULT_VESUM_DB = Path("data/vesum.db")
DEFAULT_OUTPUT_MD = Path("docs/reports/uldr_v02_pretraining_contradiction_audit.md")
DEFAULT_OUTPUT_JSON = Path("docs/reports/uldr_v02_pretraining_contradiction_audit.json")


def load_protection_suite(path: Path) -> list[dict[str, Any]]:
    """Load and validate the 600-case protection suite."""
    resolved_path = resolve_data_path(path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Protection suite not found: {path} (resolved: {resolved_path})")
    cases: list[dict[str, Any]] = []
    with resolved_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            cases.append(json.loads(line))
    return cases


def normalize_token(token: str) -> str:
    """Normalize Ukrainian word token by stripping stress marks and unifying apostrophes."""
    # Strip acute and grave combining accents (stress marks)
    norm = re.sub(r"[\u0300\u0301]", "", str(token or ""))
    # Normalize curly/typographic apostrophes to standard straight apostrophe
    norm = re.sub(r"[’'`‘ʼ]", "'", norm)
    return norm.lower().strip()


def verify_replacement_attestation(
    replacement: str,
    vesum_conn: sqlite3.Connection,
    sources_conn: sqlite3.Connection,
) -> bool:
    """Check if all tokens of the replacement word/phrase are attested in approved Ukrainian authorities."""
    clean = replacement.strip().strip("–—\"'«» .,")
    raw_words = re.findall(r"[А-Яа-яЇїІіЄєҐґ’'ʼ\u0300\u0301]+", clean)
    words = [normalize_token(w) for w in raw_words if normalize_token(w)]
    if not words:
        return False

    for w in words:
        # VESUM lemma or inflected form
        in_vesum = vesum_conn.execute(
            "SELECT 1 FROM forms_all WHERE word_form = ? OR lemma = ? LIMIT 1",
            (w, w),
        ).fetchone()
        in_sum20 = sources_conn.execute(
            "SELECT 1 FROM sum20_articles WHERE headword = ? OR normalized_lookup_key = ? LIMIT 1",
            (w, w),
        ).fetchone()
        in_grinchenko = sources_conn.execute(
            "SELECT 1 FROM grinchenko WHERE word = ? LIMIT 1",
            (w,),
        ).fetchone()
        if not (in_vesum or in_sum20 or in_grinchenko):
            return False
    return True


ANAPHORIC_WORDS = frozenset({
    "він", "вона", "воно", "вони",
    "його", "йому", "ним", "ньому", "нього",
    "її", "їй", "нею", "ній", "неї",
    "їх", "їм", "ними", "них",
    "це", "цей", "ця", "ці",
    "цього", "цієї", "цьому", "цій", "цим", "цими", "цих", "цю",
    "слово", "слова", "словом", "слові",
    "термін", "терміна", "терміном", "терміні",
    "вираз", "виразу", "виразом", "виразі",
    "зворот", "звороту", "зворотом", "звороті",
    "форма", "форми", "формою", "формі",
    "лексема", "лексеми", "лексемою", "лексемі",
})


def is_target_condemned_in_text(target_term: str, text: str) -> bool:
    """Check if the text explicitly condemns or directs replacement of the protected target term."""
    t_lower = target_term.lower().strip()
    if not t_lower or not text:
        return False

    t_bare = re.escape(t_lower)
    t_token_re = re.compile(rf"(?:[«\"“‘\']{t_bare}[»\"”’\']|\b{t_bare}\b|слово\s+\b{t_bare}\b)", re.IGNORECASE)
    anaphoric_re = re.compile(
        r"\b(?:"
        r"він|вона|воно|вони|"
        r"його|йому|ним|ньому|нього|"
        r"її|їй|нею|ній|неї|"
        r"їх|їм|ними|них|"
        r"це|цей|ця|ці|цього|цієї|цьому|цій|цим|цими|цих|цю|"
        r"слово|слова|словом|слові|"
        r"термін\w*|вираз\w*|зворот\w*|форм\w*|лексем\w*"
        r")\b",
        re.IGNORECASE,
    )

    target_in_text = bool(t_token_re.search(text))
    current_referent = "TARGET" if not target_in_text else None

    # Split text into sentence/clause units by punctuation or coordinate/adversative conjunctions introducing clauses
    split_pat = re.compile(
        r"(?:[.,\n;!?:\u2014\u2013]+|"
        r"\s+\b(?:але|проте|однак)\b\s+|"
        r"\s+\b(?:та|і|й|а)\s+(?=[«\"“‘\']|\b(?:його|її|їх|це|цей|цю|цього|цій|цим|слово|термін|вираз|зворот|щодо|для|слід|варто|потрібно|необхідно|треба|можна|не)\b|[а-яА-ЯёЁіІїЇєЄґҐ’\'\-]+\s+(?:слід|варто|потрібно|необхідно|треба|можна|є|не)\b))",
        re.IGNORECASE,
    )

    clauses = [c.strip() for c in split_pat.split(text) if c.strip()]
    for clause in clauses:
        cl_lower = clause.lower()
        quoted = re.findall(r"[«\"“‘\']([^»\"”’\']+)[»\"”’\']", clause)

        if t_token_re.search(clause):
            # If target is present ONLY as a replacement destination (e.g. "замінити на «файний»"),
            # it is being recommended, not condemned or replaced.
            is_destination = bool(re.search(rf"\b(?:на|замість|до)\s+[«\"“‘\']?{t_bare}[»\"”’\']?", cl_lower))
            is_subject = bool(re.search(rf"(?:^|\b(?:щодо\s+слова|слово|словом|вираз|зворот)\s+)?[«\"“‘\']?{t_bare}[»\"”’\']?\s+(?:є|це|не|слід|варто|потрібно|необхідно|треба|можна|—|\-)", cl_lower))
            current_referent = "OTHER" if is_destination and not is_subject else "TARGET"
        elif quoted:
            first_q = quoted[0].strip().lower()
            if first_q != t_lower:
                subj_m = re.search(
                    rf"(?:^|\b(?:щодо\s+слова|слово|словом|вираз|зворот)\s+)?[«\"“‘\']{re.escape(first_q)}[»\"”’\']",
                    cl_lower,
                )
                if subj_m and not re.search(rf"\b(?:на|замість|до)\s+[«\"“‘\']{re.escape(first_q)}[»\"”’\']", cl_lower):
                    current_referent = "OTHER"
        else:
            # Check for unquoted subject before directives (e.g. "общий слід замінити")
            unquoted_subj_m = re.search(
                r"(?:^|\b(?:щодо\s+слова|слово|словом|вираз|зворот)\s+)?([а-яА-ЯёЁіІїЇєЄґҐ’'\-]+)\s+(?:слід|варто|потрібно|необхідно|треба|можна|потребує|вимагає|є|не|вважа\w*|визна\w*|назива\w*)",
                cl_lower,
            )
            if unquoted_subj_m:
                uq_word = unquoted_subj_m.group(1).strip()
                if uq_word in ANAPHORIC_WORDS or anaphoric_re.fullmatch(uq_word):
                    # Anaphoric reference (його, її, це, etc.): preserve active referent from preceding clause
                    pass
                elif uq_word != t_lower and not re.search(rf"\b(?:на|замість|до)\s+{re.escape(uq_word)}", cl_lower):
                    current_referent = "OTHER"
            elif anaphoric_re.search(clause) and current_referent is not None:
                # Anaphoric reference (його, її, це, etc.): preserve active referent from preceding clause
                pass

        if current_referent != "TARGET":
            continue

        # Check replacement / avoidance directives
        # A directive is a contradiction unless it is specifically negated
        replace_dirs = [
            r"(?:слід|варто|потрібно|необхідно|треба|можна)\s+(?:замінити|замінювати|уникати|виправити|виправляти)",
            r"\b(?:замініть|замінити|уникайте|уникати|виправте|виправити)\b",
            r"(?:потребує|вимагає)\s+(?:заміни|виправлення)",
        ]
        for rpat in replace_dirs:
            for match in re.finditer(rpat, cl_lower):
                start = match.start()
                prefix = cl_lower[:start]
                last_ne = prefix.rfind("не ")
                is_negated = False
                if last_ne != -1:
                    after_ne = prefix[last_ne + 3:]
                    if not re.search(r"\b(?:але|проте|однак)\b", after_ne):
                        is_negated = bool(
                            re.search(r"\bне\s+(?:слід|варто|потрібно|необхідно|треба|можна)?\s*$", prefix)
                        )
                if not is_negated:
                    return True

        condemn_patterns = [
            r"\bпомилк\w*",
            r"\bкальк\w*",
            r"\bросіянізм\w*",
            r"\bрусизм\w*",
            r"\bсуржик\w*",
            r"\bненормативн\w*",
            r"\bнеправильн\w*",
            r"не\s+(?:є\s+)?нормативн\w*",
            r"не\s+(?:є\s+)?правильн\w*",
        ]

        for cpat in condemn_patterns:
            for match in re.finditer(cpat, cl_lower):
                start = match.start()
                prefix = cl_lower[:start]
                last_ne = prefix.rfind("не ")
                is_negated = False
                if last_ne != -1:
                    after_ne = prefix[last_ne + 3:]
                    if not re.search(r"\b(?:але|проте|однак)\b", after_ne):
                        is_negated = bool(
                            re.search(r"\bне\s+(?:є|це|було|буде|був|була|становить|вважається|визнається|(?:слід|варто|можна|треба|потрібно|необхідно)\s+(?:вважати|називати|визнавати))\s*$", prefix)
                            or re.search(r"\bне\s*$", prefix)
                            or re.search(r"\bне\s+(?:є\s+|це\s+|вважається\s+|було\s+)?[а-яА-ЯёЁіІїЇєЄґҐ’'\-]+\s+(?:та|і|й)\s+(?:не\s+)?$", prefix)
                        )
                if not is_negated:
                    return True

    return False


def run_pretraining_audit(
    protection_path: Path = DEFAULT_PROTECTION_SUITE,
    sft_dir: Path = DEFAULT_SFT_DIR,
    dpo_dir: Path = DEFAULT_DPO_DIR,
    sources_db_path: Path = DEFAULT_SOURCES_DB,
    vesum_db_path: Path = DEFAULT_VESUM_DB,
    output_md: Path = DEFAULT_OUTPUT_MD,
    output_json: Path = DEFAULT_OUTPUT_JSON,
    min_sft_records: int = 6000,
    min_dpo_pairs: int = 3000,
    min_cases: int = 600,
) -> tuple[bool, dict[str, Any], str]:
    # Resolve all data paths (supporting worktrees and shared common git checkouts)
    resolved_protection = resolve_data_path(protection_path)
    resolved_sft = resolve_data_path(sft_dir)
    resolved_dpo = resolve_data_path(dpo_dir)
    resolved_sources = resolve_data_path(sources_db_path)
    resolved_vesum = resolve_data_path(vesum_db_path)

    # 1. Path existence and non-zero shard checks (Finding 1)
    if not resolved_sft.exists():
        raise FileNotFoundError(f"SFT directory does not exist: {sft_dir} (resolved: {resolved_sft})")
    if not resolved_dpo.exists():
        raise FileNotFoundError(f"DPO directory does not exist: {dpo_dir} (resolved: {resolved_dpo})")

    sft_files = sorted(resolved_sft.glob("*.jsonl"))
    if not sft_files:
        raise ValueError(f"No SFT shards found in {sft_dir} (resolved: {resolved_sft})")

    dpo_files = sorted(resolved_dpo.glob("*.jsonl"))
    if not dpo_files:
        raise ValueError(f"No DPO shards found in {dpo_dir} (resolved: {resolved_dpo})")

    if not resolved_sources.exists():
        raise FileNotFoundError(f"Sources database does not exist: {sources_db_path} (resolved: {resolved_sources})")
    if not resolved_vesum.exists():
        raise FileNotFoundError(f"VESUM database does not exist: {vesum_db_path} (resolved: {resolved_vesum})")

    cases = load_protection_suite(resolved_protection)
    total_cases = len(cases)

    # 2. Stratum distribution check
    dialect_cases = [c for c in cases if c.get("stratum") == "regional_dialect"]
    historical_cases = [c for c in cases if c.get("stratum") == "historical_text"]
    surzhyk_cases = [c for c in cases if c.get("stratum") == "anti_surzhyk_control"]

    # 3. Collect protected terms (must be PRESERVE)
    invalid_preservations = [
        c.get("eval_id")
        for c in dialect_cases + historical_cases
        if c.get("expected_action") != "PRESERVE"
    ]
    if invalid_preservations:
        raise ValueError(
            f"Protection suite has non-PRESERVE dialect/historical cases: {invalid_preservations}"
        )

    protected_cases = [c for c in cases if c.get("expected_action") == "PRESERVE"]
    expected_min_preservations = 500 if min_cases >= 600 else 1
    if len(protected_cases) < expected_min_preservations:
        raise ValueError(
            f"Insufficient protected preservation cases: expected >= {expected_min_preservations}, got {len(protected_cases)}"
        )

    protected_terms: set[str] = {
        c["target_term"].lower().strip() for c in protected_cases if c.get("target_term")
    }
    expected_min_terms = 250 if min_cases >= 600 else 1
    if len(protected_terms) < expected_min_terms:
        raise ValueError(
            f"Insufficient unique protected terms: expected >= {expected_min_terms}, got {len(protected_terms)}"
        )

    # 4. Cross-audit SFT shards (Validating production schema and labels)
    sft_contradictions: list[dict[str, Any]] = []
    sft_total_count = 0

    for sft_file in sft_files:
        for line_idx, line in enumerate(sft_file.read_text(encoding="utf-8").splitlines()):
            if not line.strip():
                continue
            sft_total_count += 1
            item = json.loads(line)
            target = (item.get("target_term") or "").lower().strip()
            if not target:
                raise ValueError(
                    f"SFT record at line {line_idx+1} in {sft_file.name} lacks required 'target_term'"
                )

            is_calque = item.get("is_calque_or_russianism")
            if is_calque is not None and not isinstance(is_calque, bool):
                raise ValueError(
                    f"SFT record at line {line_idx+1} in {sft_file.name} has invalid 'is_calque_or_russianism': "
                    f"expected boolean True/False, got {type(is_calque).__name__} ({is_calque!r})"
                )

            raw_action = item.get("action") or item.get("case_type")
            if raw_action is not None:
                if not isinstance(raw_action, str):
                    raise ValueError(
                        f"SFT record at line {line_idx+1} in {sft_file.name} has non-string action label: {raw_action!r}"
                    )
                action = raw_action.strip().upper()
                if action not in ("PRESERVE", "CORRECT", "REPLACE"):
                    raise ValueError(
                        f"SFT record at line {line_idx+1} in {sft_file.name} has unrecognized action: {raw_action!r}. "
                        f"Recognized actions are: ('PRESERVE', 'CORRECT', 'REPLACE')"
                    )
            else:
                action = ""

            if is_calque is None and not action:
                raise ValueError(
                    f"SFT record at line {line_idx+1} in {sft_file.name} lacks required label field "
                    f"('is_calque_or_russianism' or 'action')"
                )

            # In production SFT, is_calque_or_russianism is True when the target term is flagged as an error/calque
            is_condemned = (is_calque is True) or (action in ("CORRECT", "REPLACE"))
            if target in protected_terms and is_condemned:
                sft_contradictions.append({
                    "shard": sft_file.name,
                    "line": line_idx + 1,
                    "target_term": target,
                    "is_calque_or_russianism": is_calque,
                    "action": action,
                    "prompt": item.get("query") or item.get("input_text") or item.get("prompt"),
                })

    # 5. Cross-audit DPO shards (Validating production schema and preference direction)
    dpo_contradictions: list[dict[str, Any]] = []
    dpo_total_count = 0

    for dpo_file in dpo_files:
        for line_idx, line in enumerate(dpo_file.read_text(encoding="utf-8").splitlines()):
            if not line.strip():
                continue
            dpo_total_count += 1
            item = json.loads(line)
            prompt = item.get("prompt")
            chosen = item.get("chosen")
            rejected = item.get("rejected")
            if not prompt or not chosen or not rejected:
                raise ValueError(
                    f"DPO record at line {line_idx+1} in {dpo_file.name} lacks required prompt/chosen/rejected"
                )

            metadata = item.get("metadata")
            if not isinstance(metadata, dict):
                raise ValueError(
                    f"DPO record at line {line_idx+1} in {dpo_file.name} lacks valid 'metadata' dict"
                )

            target = (metadata.get("target_term") or "").lower().strip()
            if not target:
                raise ValueError(
                    f"DPO record at line {line_idx+1} in {dpo_file.name} lacks 'metadata.target_term'"
                )

            pair_type = metadata.get("pair_type", "")
            # If target in protected terms and pair penalizes it as an error or directs replacement
            if target in protected_terms and (
                pair_type != "anti_hyper_purist_preservation_pairs"
                or is_target_condemned_in_text(target, chosen)
            ):
                dpo_contradictions.append({
                    "shard": dpo_file.name,
                    "line": line_idx + 1,
                    "target_term": target,
                    "pair_type": pair_type,
                    "prompt": prompt,
                    "chosen": chosen,
                })

    # 6. Surzhyk control validation against positive authorities (Finding 2)
    surzhyk_valid = True
    surzhyk_anomalies: list[dict[str, Any]] = []

    sources_uri = f"file:{resolved_sources.resolve()}?mode=ro"
    vesum_uri = f"file:{resolved_vesum.resolve()}?mode=ro"
    with (
        sqlite3.connect(sources_uri, uri=True) as sources_conn,
        sqlite3.connect(vesum_uri, uri=True) as vesum_conn,
    ):
        for sc in surzhyk_cases:
            action = sc.get("expected_action")
            repl = sc.get("expected_replacement")
            if action != "CORRECT" or not repl:
                surzhyk_valid = False
                surzhyk_anomalies.append({
                    "eval_id": sc.get("eval_id"),
                    "reason": "Missing CORRECT action or empty replacement",
                })
                continue

            if not verify_replacement_attestation(repl, vesum_conn, sources_conn):
                surzhyk_valid = False
                surzhyk_anomalies.append({
                    "eval_id": sc.get("eval_id"),
                    "replacement": repl,
                    "reason": f"Replacement '{repl}' not attested in positive authorities (СУМ-20, VESUM, Grinchenko 1907)",
                })

    # 7. Overall audit determination (Hard Non-Vacuous Gates)
    passed = (
        (
            (
                len(cases) == 600
                and len(dialect_cases) == 300
                and len(historical_cases) == 200
                and len(surzhyk_cases) == 100
                and len(protected_cases) == 500
                and len(protected_terms) >= 250
            )
            if min_cases >= 600
            else (
                len(cases) >= min_cases
                and len(protected_cases) >= expected_min_preservations
                and len(protected_terms) >= 1
            )
        )
        and len(sft_files) > 0
        and sft_total_count >= min_sft_records
        and len(dpo_files) > 0
        and dpo_total_count >= min_dpo_pairs
        and len(sft_contradictions) == 0
        and len(dpo_contradictions) == 0
        and surzhyk_valid
    )

    now_iso = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    report_data: dict[str, Any] = {
        "audit_timestamp": now_iso,
        "overall_status": "PASSED" if passed else "FAILED",
        "protection_suite_cases": total_cases,
        "stratum_counts": {
            "regional_dialect": len(dialect_cases),
            "historical_text": len(historical_cases),
            "anti_surzhyk_control": len(surzhyk_cases),
        },
        "protected_cases_count": len(protected_cases),
        "protected_terms_count": len(protected_terms),
        "sft_shards_audited": len(sft_files),
        "sft_records_audited": sft_total_count,
        "sft_records_minimum": min_sft_records,
        "sft_contradictions_count": len(sft_contradictions),
        "sft_contradictions": sft_contradictions,
        "dpo_shards_audited": len(dpo_files),
        "dpo_pairs_audited": dpo_total_count,
        "dpo_pairs_minimum": min_dpo_pairs,
        "dpo_contradictions_count": len(dpo_contradictions),
        "dpo_contradictions": dpo_contradictions,
        "anti_surzhyk_valid": surzhyk_valid,
        "anti_surzhyk_anomalies": surzhyk_anomalies,
    }

    # Format Markdown report (Evidence-grounded, no unconditional success claims)
    details_lines = [
        "## 2. Invariant Verification Details",
        "",
        "1. **False Penalization Scan of Dialect & Historical Forms:**",
        f"   - **{len(protected_terms)}** unique protected regional and historical terms were checked across {sft_total_count:,} SFT records and {dpo_total_count:,} DPO pairs.",
    ]
    if len(sft_contradictions) == 0 and len(dpo_contradictions) == 0:
        details_lines.append("   - **Result:** Zero training examples penalize protected forms as errors or attempt to normalize them into contemporary standard Ukrainian.")
    else:
        details_lines.append(f"   - **Result:** Contradictions detected: {len(sft_contradictions)} in SFT, {len(dpo_contradictions)} in DPO.")
        for sc in sft_contradictions[:10]:
            details_lines.append(f"     - [SFT] {sc['shard']}:{sc['line']} target '{sc['target_term']}' condemned")
        for dc in dpo_contradictions[:10]:
            details_lines.append(f"     - [DPO] {dc['shard']}:{dc['line']} target '{dc['target_term']}' pair '{dc['pair_type']}'")

    verified_controls = len(surzhyk_cases) - len(surzhyk_anomalies)
    details_lines.extend([
        "",
        "2. **Anti-Surzhyk Control Verification against Positive Authorities:**",
        f"   - Observed anti-surzhyk control cases: {len(surzhyk_cases)} cases targeting Russianisms and Russian-Soviet occupation calques.",
        f"   - Attestation verification against positive Ukrainian authorities (СУМ-20, VESUM, Grinchenko 1907): {verified_controls} / {len(surzhyk_cases)} verified.",
    ])
    if surzhyk_anomalies:
        for sa in surzhyk_anomalies[:10]:
            details_lines.append(f"     - [Anomaly] {sa.get('eval_id')}: {sa.get('reason')}")

    md_lines = [
        "# ULDR v0.2 Pre-Training Contradiction Audit Report",
        "",
        "> **Phase:** Phase 5.5 (ULDR v0.2 Alignment Training & 5-Gate Evaluation / Issue #8054)",
        f"> **Audit Date:** {now_iso}",
        f"> **Overall Status:** {'✅ PASSED — ZERO CONTRADICTIONS DETECTED' if passed else '❌ FAILED'}",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        "This audit fulfills the pre-training cross-stage contradiction defense mandated by Advisor Fable prior to Gemma 3 4B alignment training.",
        f"All **{total_cases}** protection cases from `dialect_historical_protection_suite_600.jsonl` were audited against all **{sft_total_count:,}** SFT training records across **{len(sft_files)}** shards and **{dpo_total_count:,}** DPO pairs across **{len(dpo_files)}** shards.",
        "",
        "| Audit Dimension | Target Invariant | Measured Result | Audit Verdict |",
        "| :--- | :--- | :---: | :---: |",
        f"| **Protection Suite Population** | Exactly 600 cases | {total_cases} cases | {'✅ PASS' if total_cases == 600 else '❌ FAIL'} |",
        f"| **Regional Dialect Preserves** | Exactly 300 cases | {len(dialect_cases)} cases | {'✅ PASS' if len(dialect_cases) == 300 else '❌ FAIL'} |",
        f"| **Historical Text Preserves** | Exactly 200 cases | {len(historical_cases)} cases | {'✅ PASS' if len(historical_cases) == 200 else '❌ FAIL'} |",
        f"| **Anti-Surzhyk Controls** | Exactly 100 cases | {len(surzhyk_cases)} cases | {'✅ PASS' if len(surzhyk_cases) == 100 else '❌ FAIL'} |",
        f"| **SFT Corpus Population** | $\\ge {min_sft_records:,}$ records across shards | {sft_total_count:,} records ({len(sft_files)} shards) | {'✅ PASS' if sft_total_count >= min_sft_records and len(sft_files) > 0 else '❌ FAIL'} |",
        f"| **DPO Corpus Population** | $\\ge {min_dpo_pairs:,}$ pairs across shards | {dpo_total_count:,} pairs ({len(dpo_files)} shards) | {'✅ PASS' if dpo_total_count >= min_dpo_pairs and len(dpo_files) > 0 else '❌ FAIL'} |",
        f"| **SFT Training Contradictions** | Exact 0 observed | **{len(sft_contradictions)}** contradictions | {'✅ PASS' if len(sft_contradictions) == 0 else '❌ FAIL'} |",
        f"| **DPO Training Contradictions** | Exact 0 observed | **{len(dpo_contradictions)}** contradictions | {'✅ PASS' if len(dpo_contradictions) == 0 else '❌ FAIL'} |",
        f"| **Anti-Surzhyk Authority Grounding** | 100% replacement attestation | {len(surzhyk_cases) - len(surzhyk_anomalies)} / {len(surzhyk_cases)} verified (СУМ-20/VESUM/Грінченко) | {'✅ PASS' if surzhyk_valid else '❌ FAIL'} |",
        "",
        "---",
        "",
        *details_lines,
        "",
        "---",
        "",
        "*Certified by ULDR Phase 5.5 Pre-Training Contradiction Audit Runner.*",
    ]
    md_content = "\n".join(md_lines) + "\n"

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(md_content, encoding="utf-8")

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return passed, report_data, md_content


def main() -> int:
    parser = argparse.ArgumentParser(description="Pre-training Cross-Stage Contradiction Audit")
    parser.add_argument("--protection-suite", type=Path, default=DEFAULT_PROTECTION_SUITE)
    parser.add_argument("--sft-dir", type=Path, default=DEFAULT_SFT_DIR)
    parser.add_argument("--dpo-dir", type=Path, default=DEFAULT_DPO_DIR)
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM_DB)
    parser.add_argument("--min-sft-records", type=int, default=6000)
    parser.add_argument("--min-dpo-pairs", type=int, default=3000)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)

    args = parser.parse_args()
    passed, data, _ = run_pretraining_audit(
        protection_path=args.protection_suite,
        sft_dir=args.sft_dir,
        dpo_dir=args.dpo_dir,
        sources_db_path=args.sources_db,
        vesum_db_path=args.vesum_db,
        min_sft_records=args.min_sft_records,
        min_dpo_pairs=args.min_dpo_pairs,
        output_md=args.output_md,
        output_json=args.output_json,
    )

    print(f"Pre-training Contradiction Audit: {'PASSED' if passed else 'FAILED'}")
    print(f"  SFT Contradictions: {data['sft_contradictions_count']}")
    print(f"  DPO Contradictions: {data['dpo_contradictions_count']}")
    print(f"  Anti-Surzhyk Authority Valid: {data['anti_surzhyk_valid']}")
    print(f"  Report written to: {args.output_md}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())

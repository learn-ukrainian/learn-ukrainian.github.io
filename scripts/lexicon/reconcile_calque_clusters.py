#!/usr/bin/env python3
"""Deterministic Decolonization & Calque Cluster Reconciliation Engine (#7914).

Systematically extracts, validates, and cross-wires decolonization alternatives
and mutual synonyms across the Word Atlas with ZERO LLM usage.

Sources:
- data/lt_replacements.json (LanguageTool / curated replacement map)
- data/lexicon/heritage_pairs.yaml & heritage_pairs.wave1-calque.yaml (UA-GEC & curated pairs)
- scripts/lexicon/calque_corrections.py (active participle / calque authority)
- data/sources.db (textbooks_fts, style_guide, ua_gec_errors, sum11, grinchenko)
- data/vesum.db (VESUM morphological validation)

Versioning Contract:
- CURRENT_ENRICHMENT_VERSION = 2
- Stamped with `enrichment_version: 2` and `updated_at` timestamp.
- Skips entries where `entry.get('enrichment_version', 0) >= 2` unless `--force`.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.guardrails.worktree_containment import resolve_main_root
from scripts.lexicon.manifest_fingerprint import build_fingerprint, write_fingerprint
from scripts.verification.vesum import get_vesum_conn, verify_lemma

PRIMARY_ROOT = resolve_main_root(PROJECT_ROOT) or PROJECT_ROOT


def _resolve_repo_path(path: Path) -> Path:
    """Resolve a path against the worktree root first, then primary checkout for gitignored data."""
    if path.exists() and path.stat().st_size > 0:
        return path
    try:
        rel = path.relative_to(PROJECT_ROOT)
        primary_fallback = PRIMARY_ROOT / rel
        if primary_fallback.exists() and primary_fallback.stat().st_size > 0:
            return primary_fallback
    except ValueError:
        pass
    return path


CURRENT_ENRICHMENT_VERSION = 2

DEFAULT_SOURCES_DB = _resolve_repo_path(PROJECT_ROOT / "data" / "sources.db")
DEFAULT_ATLAS_DB = _resolve_repo_path(PROJECT_ROOT / "data" / "atlas.db")
DEFAULT_VESUM_DB = _resolve_repo_path(PROJECT_ROOT / "data" / "vesum.db")
DEFAULT_LT_REPLACEMENTS = _resolve_repo_path(PROJECT_ROOT / "data" / "lt_replacements.json")
DEFAULT_HERITAGE_PAIRS = _resolve_repo_path(PROJECT_ROOT / "data" / "lexicon" / "heritage_pairs.yaml")
DEFAULT_HERITAGE_OVERLAY = _resolve_repo_path(PROJECT_ROOT / "data" / "lexicon" / "heritage_pairs.wave1-calque.yaml")
DEFAULT_INFLOW_QUEUE = PROJECT_ROOT / "data" / "lexicon" / "calque_inflow_queue.json"
DEFAULT_MANIFEST = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
DEFAULT_FINGERPRINT = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.fingerprint.json"

_ACUTE_RE = re.compile(r"[\u0301\u0300]")
_EDGE_PUNCT_RE = re.compile(r"^[\"'«»„”“,.:;!?…\s]+|[\"'«»„”“,.:;!?…\s]+$")
_CLEAN_TOKEN_RE = re.compile(r"^[А-Яа-яЄєІіЇїҐґ'’ʼ-]+$")


def strip_accents(s: str) -> str:
    """Remove combining acute and grave stress accents."""
    return _ACUTE_RE.sub("", s)


def normalize_text(s: str) -> str:
    """Strip accents, normalize spaces, and strip edge quotation/punctuation marks."""
    clean = strip_accents(s).strip()
    return _EDGE_PUNCT_RE.sub("", clean).strip()


@dataclass
class CandidateAlternative:
    term: str
    is_phrase: bool
    vesum_forms_count: int = 0
    pos: str | None = None
    textbook_hits: int = 0
    heritage_attested: bool = False
    sources: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        if self.is_phrase:
            return self.vesum_forms_count > 0
        return self.vesum_forms_count > 0 or self.heritage_attested

    @property
    def ranking_key(self) -> tuple[int, int, int]:
        # Sort key (descending):
        # 1. Textbook hits (>0 = living school textbook vocabulary)
        # 2. Authentic heritage attestation
        # 3. VESUM forms count
        return (
            self.textbook_hits,
            1 if self.heritage_attested else 0,
            self.vesum_forms_count,
        )


class CalqueReconciliationEngine:
    def __init__(
        self,
        sources_db_path: Path = DEFAULT_SOURCES_DB,
        atlas_db_path: Path = DEFAULT_ATLAS_DB,
        vesum_db_path: Path = DEFAULT_VESUM_DB,
        lt_path: Path = DEFAULT_LT_REPLACEMENTS,
        heritage_pairs_path: Path = DEFAULT_HERITAGE_PAIRS,
        heritage_overlay_path: Path = DEFAULT_HERITAGE_OVERLAY,
        manifest_path: Path | None = None,
    ) -> None:
        self.sources_db_path = sources_db_path
        self.atlas_db_path = atlas_db_path
        self.vesum_db_path = vesum_db_path
        self.lt_path = lt_path
        self.heritage_pairs_path = heritage_pairs_path
        self.heritage_overlay_path = heritage_overlay_path
        self.manifest_path = manifest_path

        self._sources_conn: sqlite3.Connection | None = None
        self._atlas_conn: sqlite3.Connection | None = None
        self._vesum_conn: sqlite3.Connection | None = None

        self._cached_atlas_lemmas: set[str] | None = None
        self._cached_candidate_map: dict[str, list[CandidateAlternative]] = {}
        self._lexicalised_safe: set[str] | None = None
        self.curated_heritage_pairs: dict[str, dict[str, Any]] = {}

    def get_lexicalised_safe(self) -> set[str]:
        """Return set of verified lexicalised adjectives and polysemes that must not be blanket-warned."""
        if self._lexicalised_safe is None:
            safe = set()
            try:
                from scripts.lexicon.calque_corrections import (
                    LEXICALISED_SAFE,
                    SENSE_RESTRICTED_CALQUES,
                )

                for w in LEXICALISED_SAFE:
                    w_clean = normalize_text(w).lower()
                    if w_clean:
                        safe.add(w_clean)
                for w in SENSE_RESTRICTED_CALQUES:
                    w_clean = normalize_text(w).lower()
                    if w_clean:
                        safe.add(w_clean)
            except ImportError:
                pass
            self._lexicalised_safe = safe
        return self._lexicalised_safe

    @property
    def sources_conn(self) -> sqlite3.Connection:
        if self._sources_conn is None:
            self._sources_conn = sqlite3.connect(self.sources_db_path)
            self._sources_conn.row_factory = sqlite3.Row
        return self._sources_conn

    @property
    def atlas_conn(self) -> sqlite3.Connection:
        if self._atlas_conn is None:
            self._atlas_conn = sqlite3.connect(self.atlas_db_path)
            self._atlas_conn.row_factory = sqlite3.Row
        return self._atlas_conn

    @property
    def vesum_conn(self) -> sqlite3.Connection:
        return get_vesum_conn(self.vesum_db_path)

    def get_atlas_lemmas(self) -> set[str]:
        if self._cached_atlas_lemmas is None:
            cursor = self.atlas_conn.cursor()
            rows = cursor.execute("SELECT lemma FROM articles").fetchall()
            self._cached_atlas_lemmas = set(r[0] for r in rows)
        return self._cached_atlas_lemmas

    def load_raw_replacements(self) -> dict[str, dict[str, list[str]]]:
        """Collect raw error -> suggestions mappings from all deterministic sources."""
        self.curated_heritage_pairs = {}
        raw_map: dict[str, dict[str, list[str]]] = {}

        # 1. LanguageTool replacements
        if self.lt_path.exists():
            with open(self.lt_path, encoding="utf-8") as f:
                lt_data = json.load(f)
            for k, v in lt_data.items():
                k_clean = normalize_text(k).lower()
                suggs = v.get("suggestions", [])
                if k_clean not in raw_map:
                    raw_map[k_clean] = {}
                raw_map[k_clean]["lt_replacements"] = suggs

        # 2. Curated calques and phrasal calques from calque_corrections.py
        try:
            from scripts.lexicon.calque_corrections import (
                CURATED_CALQUES,
                PHRASAL_CALQUES,
            )

            for k, v in CURATED_CALQUES.items():
                k_clean = normalize_text(k).lower()
                corrections = v.get("corrections", [])
                if isinstance(corrections, list):
                    if k_clean not in raw_map:
                        raw_map[k_clean] = {}
                    raw_map[k_clean]["curated_calques"] = [
                        normalize_text(c).lower() for c in corrections if normalize_text(c)
                    ]

            for k, v in PHRASAL_CALQUES.items():
                k_clean = normalize_text(k).lower()
                corrections = v.get("corrections", [])
                if isinstance(corrections, list):
                    if k_clean not in raw_map:
                        raw_map[k_clean] = {}
                    raw_map[k_clean]["phrasal_calques"] = [
                        normalize_text(c).lower() for c in corrections if normalize_text(c)
                    ]
        except ImportError:
            pass

        # 3. Heritage pairs YAML
        for ypath, src_tag in [
            (self.heritage_pairs_path, "heritage_pairs"),
            (self.heritage_overlay_path, "heritage_overlay"),
        ]:
            if ypath.exists():
                try:
                    import yaml

                    with open(ypath, encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    pairs = (
                        data.get("pairs", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                    )
                    for p in pairs:
                        if isinstance(p, dict):
                            err_raw = p.get("calqueLabel") or p.get("error", "")
                            err = normalize_text(err_raw).lower()
                            if not err:
                                continue

                            clean_corrs: list[str] = []
                            corrs = p.get("corrections")
                            if isinstance(corrs, list):
                                clean_corrs.extend([normalize_text(c).lower() for c in corrs if normalize_text(c)])
                            elif isinstance(corrs, str):
                                c_clean = normalize_text(corrs).lower()
                                if c_clean:
                                    clean_corrs.append(c_clean)

                            correct = p.get("correct")
                            if isinstance(correct, list):
                                clean_corrs.extend([normalize_text(c).lower() for c in correct if normalize_text(c)])
                            elif isinstance(correct, str):
                                c_clean = normalize_text(correct).lower()
                                if c_clean and c_clean not in clean_corrs:
                                    clean_corrs.append(c_clean)

                            native_lemma = p.get("nativeLemma")
                            if isinstance(native_lemma, str):
                                nl_clean = normalize_text(native_lemma).lower()
                                if nl_clean and nl_clean not in clean_corrs:
                                    clean_corrs.append(nl_clean)

                            if clean_corrs:
                                if err not in raw_map:
                                    raw_map[err] = {}
                                raw_map[err][src_tag] = clean_corrs
                                if src_tag in ("heritage_pairs", "heritage_overlay"):
                                    self.curated_heritage_pairs[err] = p
                except Exception:
                    pass

        return raw_map

    def validate_candidate(self, term: str) -> CandidateAlternative:
        """Validate candidate against VESUM, sources.db textbooks, and heritage."""
        term_clean = normalize_text(term).lower()
        is_phrase = " " in term_clean

        if is_phrase:
            # Check if each token is valid non-empty Cyrillic
            tokens = term_clean.split()
            tokens_valid = bool(tokens)
            for tok in tokens:
                tok_clean = normalize_text(tok).lower()
                if not tok_clean or not _CLEAN_TOKEN_RE.match(tok_clean):
                    tokens_valid = False
                    break
            return CandidateAlternative(
                term=term_clean,
                is_phrase=True,
                vesum_forms_count=1 if tokens_valid else 0,
            )

        # Single word: check VESUM
        lemma_lower = term_clean.lower()
        forms = verify_lemma(lemma_lower, db_path=self.vesum_db_path)
        forms_count = len(forms)
        pos = forms[0]["pos"] if forms else None

        # Check textbooks FTS5 hits (double-quoted exact match handles hyphens safely)
        tb_hits = 0
        try:
            cursor = self.sources_conn.cursor()
            fts_term = f'"{lemma_lower.replace('"', "")}"'
            row = cursor.execute(
                "SELECT count(*) FROM textbooks_fts WHERE textbooks_fts MATCH ?",
                (fts_term,),
            ).fetchone()
            if row:
                tb_hits = row[0]
        except Exception:
            tb_hits = 0

        # Check heritage dictionaries (Grinchenko) if 0 VESUM forms
        heritage_attested = False
        if forms_count == 0:
            try:
                cursor = self.sources_conn.cursor()
                row = cursor.execute(
                    "SELECT count(*) FROM grinchenko WHERE word = ?",
                    (lemma_lower,),
                ).fetchone()
                if row and row[0] > 0:
                    heritage_attested = True
            except Exception:
                heritage_attested = False

        return CandidateAlternative(
            term=term_clean,
            is_phrase=False,
            vesum_forms_count=forms_count,
            pos=pos,
            textbook_hits=tb_hits,
            heritage_attested=heritage_attested,
        )

    def resolve_cluster_alternatives(
        self, error_lemma: str, sources_dict: dict[str, list[str]]
    ) -> list[CandidateAlternative]:
        """Aggregate, validate, and rank deduplicated alternatives for an error lemma."""
        seen_terms: set[str] = set()
        candidates: list[CandidateAlternative] = []

        # Merge suggestions in source priority order:
        # 1. curated_calques
        # 2. heritage_pairs
        # 3. lt_replacements
        # 4. heritage_overlay
        source_order = [
            "curated_calques",
            "phrasal_calques",
            "heritage_pairs",
            "lt_replacements",
            "heritage_overlay",
        ]
        for src in source_order:
            if src in sources_dict:
                for raw_sugg in sources_dict[src]:
                    clean = normalize_text(raw_sugg)
                    clean_lower = clean.lower()
                    if not clean or clean_lower == error_lemma.lower():
                        continue
                    if clean_lower in seen_terms:
                        continue
                    seen_terms.add(clean_lower)

                    cand = self.validate_candidate(clean)
                    if cand.is_valid:
                        cand.sources.append(src)
                        candidates.append(cand)

        # Sort candidates deterministically by ranking key descending
        candidates.sort(key=lambda c: c.ranking_key, reverse=True)
        return candidates

    def run_reconciliation(
        self,
        limit: int | None = None,
        dry_run: bool = True,
        force: bool = False,
        single_lemma: str | None = None,
    ) -> dict[str, Any]:
        """Execute decolonization and calque cluster reconciliation."""
        raw_replacements = self.load_raw_replacements()
        atlas_lemmas = self.get_atlas_lemmas()

        target_lemmas = [single_lemma] if single_lemma else sorted(set(raw_replacements.keys()) & atlas_lemmas)
        if limit:
            target_lemmas = target_lemmas[:limit]

        results = {
            "total_candidates": len(target_lemmas),
            "reconciled_entries": 0,
            "peer_synonyms_updated": 0,
            "skipped_up_to_date": 0,
            "inflow_queued_count": 0,
            "entries": {},
            "inflow_queue": [],
        }

        cursor = self.atlas_conn.cursor()
        lexicalised_safe = self.get_lexicalised_safe()
        inflow_map: dict[str, dict[str, Any]] = {}

        manifest_data: dict[str, Any] | None = None
        manifest_by_slug: dict[str, dict[str, Any]] = {}
        if self.manifest_path and self.manifest_path.exists():
            try:
                manifest_data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
                for entry in manifest_data.get("entries", []):
                    entry_slug = entry.get("url_slug") or entry.get("slug")
                    if entry_slug:
                        manifest_by_slug[entry_slug] = entry
            except Exception as e:
                print(f"Warning: could not load manifest for sync: {e}", file=sys.stderr)

        for lemma in target_lemmas:
            # Skip verified lexicalised adjectives (e.g. блискучий)
            if lemma.lower() in lexicalised_safe:
                continue

            sources_dict = raw_replacements.get(lemma.lower(), {})
            if not sources_dict:
                continue

            # Query current article payload
            row = cursor.execute(
                """
                SELECT a.slug, ap.payload_json
                FROM articles a
                JOIN article_payloads ap ON a.slug = ap.slug
                WHERE a.lemma = ?
            """,
                (lemma,),
            ).fetchone()

            if not row:
                continue

            slug = row[0]
            payload = json.loads(row[1])

            # Check enrichment version
            current_ver = payload.get("enrichment_version", 0)
            if current_ver >= CURRENT_ENRICHMENT_VERSION and not force:
                results["skipped_up_to_date"] += 1
                continue

            # Resolve validated alternatives
            candidates = self.resolve_cluster_alternatives(lemma, sources_dict)
            if not candidates:
                continue

            sorted_alts = [c.term for c in candidates]

            # Reconcile entry
            payload["enrichment_version"] = CURRENT_ENRICHMENT_VERSION
            payload["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()

            curated_pair = self.curated_heritage_pairs.get(lemma)
            is_curated_yellow = bool(curated_pair and curated_pair.get("severity") == "calque_yellow")

            # Determine severity and Russianism status:
            # Confirmed calque/Russianism authorities vs general LT replacement
            is_curated_calque = bool(
                {"curated_calques", "phrasal_calques", "heritage_pairs"} & set(sources_dict.keys())
            )
            is_rus = False if is_curated_yellow else bool(payload.get("is_russianism", False) or is_curated_calque)
            payload["is_russianism"] = is_rus

            calque_warning = payload.get("calque_warning", {})
            if not isinstance(calque_warning, dict):
                calque_warning = {}

            first_3 = ", ".join(sorted_alts[:3])
            calque_warning["is_calque"] = True
            calque_warning["severity"] = "red" if is_rus else "orange"
            calque_warning["standard_alternatives"] = sorted_alts
            # Always refresh warning_text so it stays strictly aligned with current alternatives
            if is_curated_yellow:
                calque_warning["warning_text"] = (
                    curated_pair.get("note")
                    or f"Нерекомендоване або ненормативне слововживання. В українській літературній мові слід уживати: {first_3}."
                )
                if curated_pair.get("noteUk"):
                    calque_warning["noteUk"] = curated_pair["noteUk"]
            elif is_rus:
                calque_warning["warning_text"] = (
                    f"Калька / росіянізм. В українській літературній мові слід уживати: {first_3}."
                )
            else:
                calque_warning["warning_text"] = (
                    f"Нерекомендоване або ненормативне слововживання. В українській літературній мові слід уживати: {first_3}."
                )
            payload["calque_warning"] = calque_warning

            # Wire mutual synonyms:
            # 1. On the error lemma (e.g. пилосос):
            # Connect to authentic alternatives that are present in Atlas
            in_atlas_alts = [c.term for c in candidates if c.term in atlas_lemmas]

            # Filter out any alternative that is itself flagged as a Russianism or calque in Atlas
            clean_atlas_alts: list[str] = []
            for alt in in_atlas_alts:
                alt_check_row = cursor.execute(
                    """
                    SELECT ap.payload_json
                    FROM articles a
                    JOIN article_payloads ap ON a.slug = ap.slug
                    WHERE a.lemma = ?
                """,
                    (alt,),
                ).fetchone()
                if alt_check_row:
                    try:
                        p_data = json.loads(alt_check_row[0])
                        if p_data.get("is_russianism") or p_data.get("calque_warning", {}).get("is_calque"):
                            continue
                    except Exception:
                        pass
                clean_atlas_alts.append(alt)

            sections = payload.get("sections", {})
            if not isinstance(sections, dict):
                sections = {}
            synonyms_sec = sections.get("synonyms", {})
            if not isinstance(synonyms_sec, dict):
                synonyms_sec = {}

            existing_syns = synonyms_sec.get("items", [])
            # Prune known WordNet invalid synsets (e.g. 'вакуум' from 'пилосос')
            filtered_syns = [s for s in existing_syns if s != "вакуум" and s != lemma]
            merged_syns = sorted(set(filtered_syns) | set(clean_atlas_alts))
            if merged_syns:
                synonyms_sec["items"] = merged_syns
                synonyms_sec["source"] = "curated standard alternatives"
                sections["synonyms"] = synonyms_sec
            else:
                sections.pop("synonyms", None)
            payload["sections"] = sections

            # 2. On each authentic alternative present in Atlas (e.g. порохотяг, пилосмок, пилотяг):
            # Wire mutual synonyms between authentic peers (excluding the Russianism lemma!)
            for alt_lemma in clean_atlas_alts:
                peer_alts = [a for a in clean_atlas_alts if a != alt_lemma]
                if not peer_alts:
                    continue
                alt_row = cursor.execute(
                    """
                    SELECT a.slug, ap.payload_json
                    FROM articles a
                    JOIN article_payloads ap ON a.slug = ap.slug
                    WHERE a.lemma = ?
                """,
                    (alt_lemma,),
                ).fetchone()
                if not alt_row:
                    continue
                alt_slug = alt_row[0]
                alt_payload = json.loads(alt_row[1])
                alt_sections = alt_payload.setdefault("sections", {})
                alt_syn_sec = alt_sections.setdefault("synonyms", {})
                alt_cur_syns = alt_syn_sec.get("items", [])
                alt_filtered = [s for s in alt_cur_syns if s != "вакуум" and s != alt_lemma and s != lemma]
                alt_merged = sorted(set(alt_filtered) | set(peer_alts))
                if alt_merged != alt_cur_syns:
                    alt_syn_sec["items"] = alt_merged
                    alt_syn_sec["source"] = "curated authentic synonyms"
                    alt_payload["enrichment_version"] = CURRENT_ENRICHMENT_VERSION
                    alt_payload["updated_at"] = datetime.datetime.now(datetime.UTC).isoformat()
                    if not dry_run:
                        cursor.execute(
                            "UPDATE article_payloads SET payload_json = ? WHERE slug = ?",
                            (json.dumps(alt_payload, ensure_ascii=False), alt_slug),
                        )
                        cursor.execute(
                            "INSERT OR REPLACE INTO enrichment (slug, section, payload_json, source, filled_at) VALUES (?, 'synonyms', ?, 'curated authentic synonyms', ?)",
                            (alt_slug, json.dumps(alt_syn_sec, ensure_ascii=False), alt_payload["updated_at"]),
                        )
                    if alt_slug in manifest_by_slug:
                        alt_m_entry = manifest_by_slug[alt_slug]
                        alt_m_entry["enrichment_version"] = CURRENT_ENRICHMENT_VERSION
                        alt_m_entry["updated_at"] = alt_payload["updated_at"]
                        alt_m_sec = alt_m_entry.setdefault("sections", {})
                        alt_m_sec["synonyms"] = alt_syn_sec
                    results["peer_synonyms_updated"] += 1

            # Queue authentic alternatives not in Atlas for inflow
            for cand in candidates:
                if (
                    not cand.is_phrase
                    and cand.vesum_forms_count > 0
                    and cand.pos is not None
                    and cand.term not in atlas_lemmas
                ):
                    if cand.term not in inflow_map:
                        inflow_map[cand.term] = {
                            "lemma": cand.term,
                            "pos": cand.pos,
                            "vesum_forms": cand.vesum_forms_count,
                            "textbook_hits": cand.textbook_hits,
                            "cluster_parent": lemma,
                            "cluster_parents": [lemma],
                            "sources": list(cand.sources),
                        }
                    else:
                        entry = inflow_map[cand.term]
                        if lemma not in entry["cluster_parents"]:
                            entry["cluster_parents"].append(lemma)
                        for s in cand.sources:
                            if s not in entry["sources"]:
                                entry["sources"].append(s)

            results["reconciled_entries"] += 1
            results["entries"][lemma] = {
                "slug": slug,
                "is_russianism": is_rus,
                "standard_alternatives": sorted_alts,
                "in_atlas_alternatives": clean_atlas_alts,
                "synonyms": merged_syns,
            }

            # Sync heritage_status
            heritage_status = payload.get("heritage_status")
            if not isinstance(heritage_status, dict):
                heritage_status = {}
            heritage_status["classification"] = "russianism" if is_rus else "calque"
            heritage_status["is_russianism"] = is_rus
            heritage_status["warning_severity"] = "russianism_red" if is_rus else "calque_yellow"
            heritage_status["calque_warning"] = {"standard_alternatives": sorted_alts}
            if is_rus:
                heritage_status["russian_shadow"] = True
            attestations = [
                att for att in heritage_status.get("attestations", [])
                if not (isinstance(att, dict) and att.get("source") == "standard_alternative")
            ]
            for alt in sorted_alts:
                attestations.append(
                    {
                        "source": "standard_alternative",
                        "ref": alt,
                        "detail": f"Ukrainian standard alternative for {lemma}",
                    }
                )
            heritage_status["attestations"] = attestations
            payload["heritage_status"] = heritage_status

            if slug in manifest_by_slug:
                m_entry = manifest_by_slug[slug]
                m_entry["enrichment_version"] = CURRENT_ENRICHMENT_VERSION
                m_entry["updated_at"] = payload["updated_at"]
                m_entry["is_russianism"] = is_rus
                m_entry["calque_warning"] = calque_warning
                m_entry["heritage_status"] = heritage_status
                m_sec = m_entry.setdefault("sections", {})
                if merged_syns:
                    m_sec["synonyms"] = synonyms_sec
                else:
                    m_sec.pop("synonyms", None)

            if not dry_run:
                # Update SQLite database
                updated_json = json.dumps(payload, ensure_ascii=False)
                cursor.execute(
                    "UPDATE article_payloads SET payload_json = ? WHERE slug = ?",
                    (updated_json, slug),
                )
                cursor.execute(
                    "UPDATE articles SET heritage_classification = ?, updated_at = ? WHERE slug = ?",
                    (heritage_status.get("classification"), payload["updated_at"], slug),
                )
                cursor.execute(
                    "INSERT OR REPLACE INTO enrichment (slug, section, payload_json, source, filled_at) VALUES (?, 'heritage_status', ?, 'curated decolonization alternatives', ?)",
                    (slug, json.dumps(heritage_status, ensure_ascii=False), payload["updated_at"]),
                )
                if merged_syns:
                    cursor.execute(
                        "INSERT OR REPLACE INTO enrichment (slug, section, payload_json, source, filled_at) VALUES (?, 'synonyms', ?, 'curated standard alternatives', ?)",
                        (slug, json.dumps(synonyms_sec, ensure_ascii=False), payload["updated_at"]),
                    )
                else:
                    cursor.execute(
                        "DELETE FROM enrichment WHERE slug = ? AND section = 'synonyms'",
                        (slug,),
                    )

        if not dry_run:
            self.atlas_conn.commit()
            if manifest_data and self.manifest_path:
                if single_lemma is None and limit is None and results["reconciled_entries"] > 0:
                    try:
                        if self.manifest_path.resolve() == DEFAULT_MANIFEST.resolve():
                            fingerprint_payload = write_fingerprint(DEFAULT_FINGERPRINT, root=PROJECT_ROOT)
                        else:
                            fingerprint_payload = build_fingerprint(PROJECT_ROOT)
                        manifest_data["manifest_fingerprint"] = {
                            "schema_version": fingerprint_payload["schema_version"],
                            "fingerprint": fingerprint_payload["fingerprint"],
                        }
                    except Exception as e:
                        print(f"Warning: could not refresh manifest fingerprint: {e}", file=sys.stderr)
                with open(self.manifest_path, "w", encoding="utf-8") as f:
                    json.dump(manifest_data, f, ensure_ascii=False, indent=2)

        results["inflow_queue"] = sorted(
            inflow_map.values(),
            key=lambda x: (-x["textbook_hits"], -x["vesum_forms"], x["lemma"]),
        )
        results["inflow_queued_count"] = len(results["inflow_queue"])
        return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic Calque Cluster Reconciliation")
    parser.add_argument("--report", action="store_true", help="Print report of findings")
    parser.add_argument("--apply", action="store_true", help="Apply updates to atlas.db")
    parser.add_argument("--force", action="store_true", help="Force update even if enrichment_version >= 2")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of processed entries")
    parser.add_argument("--lemma", type=str, default=None, help="Process specific lemma")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Path to manifest JSON")
    parser.add_argument("--no-manifest", action="store_true", help="Do not update manifest file")
    parser.add_argument("--queue-out", type=Path, default=DEFAULT_INFLOW_QUEUE, help="Output path for inflow queue")

    args = parser.parse_args()

    manifest_path = None if args.no_manifest else args.manifest
    engine = CalqueReconciliationEngine(manifest_path=manifest_path)
    results = engine.run_reconciliation(
        limit=args.limit,
        dry_run=not args.apply,
        force=args.force,
        single_lemma=args.lemma,
    )

    print(f"Candidate entries scanned: {results['total_candidates']}")
    print(f"Entries reconciled: {results['reconciled_entries']}")
    print(f"Skipped up-to-date (v{CURRENT_ENRICHMENT_VERSION}): {results['skipped_up_to_date']}")
    print(f"Authentic alternatives queued for admission: {results['inflow_queued_count']}")

    if args.report or not args.apply:
        print("\n--- SAMPLE RECONCILED ENTRIES ---")
        for lemma, info in list(results["entries"].items())[:15]:
            print(f"Lemma: {lemma} (slug: {info['slug']})")
            print(f"  Standard alternatives: {info['standard_alternatives']}")
            print(f"  In Atlas alternatives: {info['in_atlas_alternatives']}")
            print(f"  Mutual synonyms: {info['synonyms']}")

    if results["inflow_queue"]:
        print("\n--- SAMPLE ADMISSION INFLOW QUEUE (Top 10) ---")
        for item in results["inflow_queue"][:10]:
            print(
                f"  {item['lemma']} (forms: {item['vesum_forms']}, textbooks: {item['textbook_hits']}, resolves: {item['cluster_parent']})"
            )

        if args.apply:
            args.queue_out.parent.mkdir(parents=True, exist_ok=True)
            with open(args.queue_out, "w", encoding="utf-8") as f:
                json.dump(results["inflow_queue"], f, ensure_ascii=False, indent=2)
            print(f"\nSaved {len(results['inflow_queue'])} queue items to {args.queue_out}")


if __name__ == "__main__":
    main()

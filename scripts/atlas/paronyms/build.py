"""Build the source-attested, VESUM-verified paronym registry for Atlas word cards.

Reads textbook chunks from ``sources.db`` (read-only) and an optional provenance-pinned
MiyKlas raw snapshot, runs the deterministic extractor, verifies every member in VESUM,
routes any unattested member to ``unverified`` with an explicit reason, computes A1
word-card lemma coverage, and emits deterministic JSON.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from lu_machinery.common.repo_root import main_checkout_root
from lu_machinery.lib.readonly_sqlite import open_readonly
from lu_machinery.storage.topology import StoreBinding, StoreRefusal, resolve_store

from scripts.atlas.paronyms.extractor import (
    MemberNote,
    RawPairAttestation,
    SourceDocument,
    extract_from_document,
    normalize_token,
)
from scripts.atlas.paronyms.miyklas import fetch_miyklas_pages, load_miyklas_documents
from scripts.verification import vesum as vesum_mod

SCHEMA_VERSION = "atlas-paronyms.v1"
DEFAULT_OUTPUT = Path("registry/atlas/paronyms-v1.json")
DEFAULT_A1_INVENTORY = Path("registry/atlas/a1-v1-inventory.json")
DEFAULT_MIYKLAS_RAW = Path("registry/miyklas/paronyms-raw-v1.json")
TEXTBOOK_FTS_QUERY = "паронім*"

VesumBatchLookup = Callable[[list[str]], dict[str, list[dict[str, Any]]]]


def _resolve_sources_db(repo_root: Path, override: Path | None) -> Path:
    binding = StoreBinding("sources", override) if override is not None else None
    resolved = resolve_store("sources", repo_root, binding=binding)
    if isinstance(resolved, StoreRefusal):
        raise FileNotFoundError(f"Unable to resolve sources.db: {resolved.reason}")
    return resolved.path


def load_textbook_paronym_documents(sources_db: Path) -> list[SourceDocument]:
    """Query all textbook chunks matching ``паронім*`` from ``sources.db`` (read-only)."""
    docs: list[SourceDocument] = []
    with open_readonly(sources_db) as conn:
        rows = conn.execute(
            """
            SELECT t.chunk_id, t.source_file, t.title, t.grade, t.author, t.text
            FROM textbooks t
            JOIN textbooks_fts f ON t.id = f.rowid
            WHERE textbooks_fts MATCH ?
            ORDER BY t.source_file, t.chunk_id
            """,
            (TEXTBOOK_FTS_QUERY,),
        ).fetchall()
    for chunk_id, source_file, title, grade, author, text in rows:
        docs.append(
            SourceDocument(
                source_type="textbook",
                source_file=str(source_file or ""),
                chunk_id=str(chunk_id or ""),
                locator=str(title or chunk_id or ""),
                title=str(title or ""),
                text=str(text or ""),
                grade=str(grade or ""),
                author=str(author or ""),
            )
        )
    return docs


def _default_vesum_lookup(vesum_db: Path | None) -> VesumBatchLookup:
    def lookup(words: list[str]) -> dict[str, list[dict[str, Any]]]:
        return vesum_mod.verify_words(words, db_path=vesum_db)

    return lookup


def _unique_sorted(items: list[str]) -> list[str]:
    return sorted({x for x in items if x})


def _resolve_canonical_pair(
    att: RawPairAttestation,
    vesum_results: dict[str, list[dict[str, Any]]],
) -> tuple[str, str, bool, list[dict[str, str]]]:
    """Verify both members against VESUM and resolve canonical lemma pair when appropriate.

    Returns ``(canon_a, canon_b, surface_form_pair, unverified_members)``.
    - If either member is multiword or unattested in VESUM, ``unverified_members`` is non-empty.
    - If a member is already a VESUM lemma, keep it as-is.
    - If an exercise uses inflected forms (e.g. ``(громадською, громадянською)``), resolve
      both to their VESUM lemmas ONLY when both share a compatible POS and each maps to a
      single lemma under that shared POS, and the resulting lemmas differ.
    - Otherwise keep the exact VESUM-attested surface forms with ``surface_form_pair=True``
      (e.g. ``греби`` [verb imp] vs ``гриби`` [noun pl]).
    """
    unverified: list[dict[str, str]] = []
    for member in (att.member_a, att.member_b):
        w = member.word
        if " " in w:
            unverified.append({"word": w, "reason": "multiword_not_in_vesum"})
            continue
        analyses = vesum_results.get(w, [])
        if not analyses:
            unverified.append({"word": w, "reason": "not_attested_in_vesum"})

    if unverified:
        a, b = sorted((att.member_a.word, att.member_b.word))
        return a, b, False, unverified

    wa, wb = att.member_a.word, att.member_b.word
    an_a = vesum_results[wa]
    an_b = vesum_results[wb]

    is_lemma_a = any(normalize_token(str(r.get("lemma", ""))) == wa for r in an_a)
    is_lemma_b = any(normalize_token(str(r.get("lemma", ""))) == wb for r in an_b)

    if is_lemma_a and is_lemma_b:
        return (wa, wb, False, []) if wa <= wb else (wb, wa, False, [])

    # Inflected exercise forms: check if both share a POS with unambiguous distinct lemmas.
    pos_to_lemmas_a: dict[str, set[str]] = defaultdict(set)
    for row in an_a:
        pos = str(row.get("pos") or "")
        lem = normalize_token(str(row.get("lemma") or ""))
        if pos and lem:
            pos_to_lemmas_a[pos].add(lem)

    pos_to_lemmas_b: dict[str, set[str]] = defaultdict(set)
    for row in an_b:
        pos = str(row.get("pos") or "")
        lem = normalize_token(str(row.get("lemma") or ""))
        if pos and lem:
            pos_to_lemmas_b[pos].add(lem)

    shared_pos = sorted(set(pos_to_lemmas_a) & set(pos_to_lemmas_b))
    for pos in shared_pos:
        lemmas_a = pos_to_lemmas_a[pos]
        lemmas_b = pos_to_lemmas_b[pos]
        if len(lemmas_a) == 1 and len(lemmas_b) == 1:
            la = next(iter(lemmas_a))
            lb = next(iter(lemmas_b))
            if la != lb:
                return (la, lb, False, []) if la <= lb else (lb, la, False, [])

    return (wa, wb, True, []) if wa <= wb else (wb, wa, True, [])


def _load_json_dict(path: Path) -> dict[str, Any]:
    """Load a JSON file and fail closed with ValueError if top-level value is not an object."""
    parsed = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected JSON object in {path.name}, got {type(parsed).__name__}")
    return parsed


def load_a1_lemma_sets(
    a1_inventory_path: Path,
) -> dict[str, set[str]]:
    """Load A1 card lemma sets from ``a1-v1-inventory.json`` and sibling slice manifests."""
    inv = _load_json_dict(a1_inventory_path)
    rows = inv.get("rows", [])
    if not isinstance(rows, list):
        raise ValueError(f"Expected 'rows' list in {a1_inventory_path.name}")
    inventory_lemmas: set[str] = set()
    single_token_keys: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"Expected dict row in {a1_inventory_path.name}")
        mapping = row.get("mapping", {})
        if not isinstance(mapping, dict):
            raise ValueError(f"Expected dict 'mapping' in {a1_inventory_path.name}")
        lemma = mapping.get("lemma")
        if isinstance(lemma, str) and lemma.strip():
            inventory_lemmas.add(normalize_token(lemma))
        key = row.get("key", "")
        if isinstance(key, str) and key.strip() and " " not in key and "/" not in key:
            single_token_keys.add(normalize_token(key))

    # Also collect lemmas of cards allocated in A1 slices 2..6 beside this inventory.
    atlas_dir = a1_inventory_path.parent
    slice_lemmas: set[str] = set()
    reg_path = atlas_dir / "identity" / "registry.json"
    if reg_path.exists():
        reg = _load_json_dict(reg_path)
        reg_entries = reg.get("entries", [])
        if not isinstance(reg_entries, list):
            raise ValueError(f"Expected 'entries' list in {reg_path.name}")
        card_to_spelling: dict[str, str] = {}
        for entry in reg_entries:
            if not isinstance(entry, dict):
                raise ValueError(f"Expected dict entry in {reg_path.name}")
            cid = entry.get("card_id")
            key_info = entry.get("key_at_creation")
            spelling = key_info.get("spelling") if isinstance(key_info, dict) else None
            if isinstance(cid, str) and isinstance(spelling, str) and cid and spelling:
                card_to_spelling[cid] = normalize_token(spelling)
        for slice_num in (2, 3, 4, 5, 6):
            comp_path = atlas_dir / "identity" / f"a1-v1-slice{slice_num}.json"
            if comp_path.exists():
                comp = _load_json_dict(comp_path)
                comp_entries = comp.get("entries", [])
                if not isinstance(comp_entries, list):
                    raise ValueError(f"Expected 'entries' list in {comp_path.name}")
                for entry in comp_entries:
                    if not isinstance(entry, dict):
                        raise ValueError(f"Expected dict entry in {comp_path.name}")
                    cid = entry.get("card_id")
                    key_info = entry.get("key_at_creation")
                    spelling = key_info.get("spelling") if isinstance(key_info, dict) else None
                    if isinstance(cid, str) and isinstance(spelling, str) and cid and spelling:
                        card_to_spelling[cid] = normalize_token(spelling)
            slice_path = atlas_dir / f"a1-v1-slice{slice_num}.json"
            if slice_path.exists():
                sdata = _load_json_dict(slice_path)
                selection = sdata.get("selection")
                cids = sdata.get("card_ids")
                if cids is None and isinstance(selection, dict):
                    cids = selection.get("card_ids")
                if cids is None:
                    cids = []
                if not isinstance(cids, list):
                    raise ValueError(f"Expected 'card_ids' list in {slice_path.name}")
                for cid in cids:
                    if isinstance(cid, str) and cid in card_to_spelling:
                        slice_lemmas.add(card_to_spelling[cid])

    return {
        "inventory_lemmas": inventory_lemmas,
        "single_token_keys": single_token_keys,
        "slice_2_to_6_lemmas": slice_lemmas,
    }


def _atomic_write_text(dest: Path, content: str) -> None:
    """Write UTF-8 text atomically via a PID-scoped sibling staging file."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    stage_path = dest.with_name(f".{dest.name}.{os.getpid()}.stage")
    try:
        stage_path.write_text(content, encoding="utf-8")
        os.replace(stage_path, dest)
    except BaseException:
        if stage_path.exists():
            stage_path.unlink()
        raise


def build_paronym_registry(
    documents: list[SourceDocument],
    *,
    vesum_lookup: VesumBatchLookup,
    a1_lemma_sets: dict[str, set[str]],
    miyklas_meta: dict[str, Any] | None = None,
    corpus_recipe_note: str = "",
) -> dict[str, Any]:
    """Run extraction, VESUM verification, aggregation, and A1 coverage accounting."""
    raw_attestations: list[RawPairAttestation] = []
    textbook_chunks_scanned = 0
    textbook_chunks_with_pairs: set[str] = set()
    textbook_files_with_pairs: set[str] = set()

    for doc in documents:
        if doc.source_type == "textbook":
            textbook_chunks_scanned += 1
        atts = extract_from_document(doc)
        if atts and doc.source_type == "textbook":
            textbook_chunks_with_pairs.add(doc.chunk_id)
            textbook_files_with_pairs.add(doc.source_file)
        raw_attestations.extend(atts)

    # Batch-verify every single-token member in VESUM (one lookup pass).
    all_single_words = sorted(
        {
            w
            for att in raw_attestations
            for w in (att.member_a.word, att.member_b.word)
            if " " not in w
        }
    )
    vesum_results = vesum_lookup(all_single_words) if all_single_words else {}

    # Second pass: if any inflected choice pair resolves to lemmas not yet in vesum_results,
    # fetch those lemmas too so every output member carries complete VESUM metadata.
    resolved_rows: list[tuple[RawPairAttestation, str, str, bool, list[dict[str, str]]]] = []
    extra_lemmas: set[str] = set()
    for att in raw_attestations:
        ca, cb, is_surf, unv = _resolve_canonical_pair(att, vesum_results)
        resolved_rows.append((att, ca, cb, is_surf, unv))
        if not unv:
            for w in (ca, cb):
                if w not in vesum_results:
                    extra_lemmas.add(w)
    if extra_lemmas:
        vesum_results = {**vesum_results, **vesum_lookup(sorted(extra_lemmas))}

    verified_groups: dict[tuple[str, str], dict[str, Any]] = {}
    unverified_groups: dict[tuple[str, str], dict[str, Any]] = {}

    def _source_record(att: RawPairAttestation) -> dict[str, Any]:
        rec: dict[str, Any] = {
            "source_type": att.source_type,
            "source_file": att.source_file,
            "chunk_id": att.chunk_id,
            "locator": att.locator,
            "pattern": att.pattern,
            "attested_forms": [att.member_a.attested_form, att.member_b.attested_form],
            "quoted_line": att.quoted_line,
        }
        if att.shared_context:
            rec["shared_context"] = att.shared_context
        if att.source_url:
            rec["source_url"] = att.source_url
        return rec

    def _attach_member_notes(
        bucket: dict[str, Any],
        target_word: str,
        note: MemberNote,
        att: RawPairAttestation,
    ) -> None:
        m_bucket = bucket["members_map"][target_word]
        if note.meaning:
            entry = {
                "text": note.meaning,
                "source_file": att.source_file,
                "chunk_id": att.chunk_id,
                "locator": att.locator,
            }
            if entry not in m_bucket["meanings"]:
                m_bucket["meanings"].append(entry)
        if note.example:
            entry = {
                "text": note.example,
                "source_file": att.source_file,
                "chunk_id": att.chunk_id,
                "locator": att.locator,
            }
            if entry not in m_bucket["examples"]:
                m_bucket["examples"].append(entry)

    def _match_note_to_canonical(
        att: RawPairAttestation,
        ca: str,
        cb: str,
    ) -> tuple[tuple[str, MemberNote], tuple[str, MemberNote]]:
        if att.member_a.word == ca and att.member_b.word == cb:
            return (ca, att.member_a), (cb, att.member_b)
        if att.member_a.word == cb and att.member_b.word == ca:
            return (ca, att.member_b), (cb, att.member_a)
        # Lemmatized inflected pair: match by VESUM lemma membership.
        lemmas_a = {
            normalize_token(str(r.get("lemma", "")))
            for r in vesum_results.get(att.member_a.word, [])
        }
        if ca in lemmas_a:
            return (ca, att.member_a), (cb, att.member_b)
        return (ca, att.member_b), (cb, att.member_a)

    for att, ca, cb, is_surf, unv in resolved_rows:
        pair_key = (ca, cb)
        target_map = unverified_groups if unv else verified_groups
        if pair_key not in target_map:
            target_map[pair_key] = {
                "pair_id": f"{ca}|{cb}",
                "surface_form_pair": is_surf,
                "members_map": {
                    ca: {"meanings": [], "examples": []},
                    cb: {"meanings": [], "examples": []},
                },
                "sources": [],
                "unverified_members": list(unv),
            }
        bucket = target_map[pair_key]
        if not is_surf:
            bucket["surface_form_pair"] = False
        srec = _source_record(att)
        if srec not in bucket["sources"]:
            bucket["sources"].append(srec)
        (w1, n1), (w2, n2) = _match_note_to_canonical(att, ca, cb)
        _attach_member_notes(bucket, w1, n1, att)
        _attach_member_notes(bucket, w2, n2, att)

    def _finalize_member(word: str, m_bucket: dict[str, Any]) -> dict[str, Any]:
        analyses = vesum_results.get(word, []) if " " not in word else []
        lemmas = _unique_sorted([normalize_token(str(r.get("lemma", ""))) for r in analyses])
        pos_list = _unique_sorted([str(r.get("pos", "")) for r in analyses])
        return {
            "word": word,
            "vesum_verified": bool(analyses) and (" " not in word),
            "vesum_lemmas": lemmas,
            "vesum_pos": pos_list,
            "meanings": sorted(
                m_bucket["meanings"],
                key=lambda x: (x["source_file"], x["chunk_id"], x["text"]),
            ),
            "examples": sorted(
                m_bucket["examples"],
                key=lambda x: (x["source_file"], x["chunk_id"], x["text"]),
            ),
        }

    pairs_out: list[dict[str, Any]] = []
    source_type_counts = {"textbook": 0, "miyklas": 0, "both": 0}
    pairs_by_source_file: dict[str, int] = defaultdict(int)
    pairs_with_meaning = 0
    word_to_paronyms: dict[str, set[str]] = defaultdict(set)
    word_to_pair_ids: dict[str, set[str]] = defaultdict(set)

    for (ca, cb), bucket in sorted(verified_groups.items()):
        sources_sorted = sorted(
            bucket["sources"],
            key=lambda s: (s["source_type"], s["source_file"], s["chunk_id"], s["pattern"], s["quoted_line"]),
        )
        stypes = sorted({s["source_type"] for s in sources_sorted})
        if stypes == ["miyklas", "textbook"]:
            source_type_counts["both"] += 1
        elif stypes == ["textbook"]:
            source_type_counts["textbook"] += 1
        elif stypes == ["miyklas"]:
            source_type_counts["miyklas"] += 1
        for sf in {s["source_file"] for s in sources_sorted}:
            pairs_by_source_file[sf] += 1

        m_a = _finalize_member(ca, bucket["members_map"][ca])
        m_b = _finalize_member(cb, bucket["members_map"][cb])
        if m_a["meanings"] or m_b["meanings"]:
            pairs_with_meaning += 1

        pair_id = bucket["pair_id"]
        word_to_paronyms[ca].add(cb)
        word_to_paronyms[cb].add(ca)
        word_to_pair_ids[ca].add(pair_id)
        word_to_pair_ids[cb].add(pair_id)

        pairs_out.append(
            {
                "pair_id": pair_id,
                "members": [m_a, m_b],
                "surface_form_pair": bucket["surface_form_pair"],
                "source_count": len(sources_sorted),
                "source_types": stypes,
                "sources": sources_sorted,
            }
        )

    unverified_out: list[dict[str, Any]] = []
    for (ca, cb), bucket in sorted(unverified_groups.items()):
        sources_sorted = sorted(
            bucket["sources"],
            key=lambda s: (s["source_type"], s["source_file"], s["chunk_id"], s["pattern"], s["quoted_line"]),
        )
        unv_members = sorted(bucket["unverified_members"], key=lambda x: x["word"])
        unverified_out.append(
            {
                "pair_id": bucket["pair_id"],
                "unverified_members": unv_members,
                "members": [
                    _finalize_member(ca, bucket["members_map"][ca]),
                    _finalize_member(cb, bucket["members_map"][cb]),
                ],
                "sources": sources_sorted,
            }
        )

    # A1 coverage accounting (only verified pairs count toward coverage).
    inv_lemmas = a1_lemma_sets.get("inventory_lemmas", set())
    single_keys = a1_lemma_sets.get("single_token_keys", set())
    slice_lemmas = a1_lemma_sets.get("slice_2_to_6_lemmas", set())

    matched_a1 = sorted(inv_lemmas & set(word_to_paronyms))
    matched_a1_keys = sorted(single_keys & set(word_to_paronyms))
    matched_a1_slices = sorted(slice_lemmas & set(word_to_paronyms))

    miyklas_pages_summary = []
    if miyklas_meta:
        for p in miyklas_meta.get("pages", []):
            miyklas_pages_summary.append(
                {
                    "page_id": p["page_id"],
                    "title": p["title"],
                    "url": p["url"],
                    "http_status": p["http_status"],
                    "fetched_at_utc": p["fetched_at_utc"],
                    "raw_html_sha256": p["raw_html_sha256"],
                    "text_sha256": p["text_sha256"],
                }
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "sources_corpus": {
            "textbooks_fts_query": TEXTBOOK_FTS_QUERY,
            "textbooks_chunks_scanned": textbook_chunks_scanned,
            "textbooks_chunks_with_pairs": len(textbook_chunks_with_pairs),
            "textbooks_source_files_with_pairs": len(textbook_files_with_pairs),
            "miyklas_included": bool(miyklas_pages_summary),
            "miyklas_pages": miyklas_pages_summary,
            "corpus_recipe_note": corpus_recipe_note,
        },
        "counts": {
            "verified_pairs": len(pairs_out),
            "unverified_pairs": len(unverified_out),
            "total_attestations_verified": sum(p["source_count"] for p in pairs_out),
            "total_attestations_unverified": sum(len(u["sources"]) for u in unverified_out),
            "distinct_verified_members": len(word_to_paronyms),
            "verified_pairs_by_source_type": source_type_counts,
            "verified_pairs_by_source_file": dict(sorted(pairs_by_source_file.items())),
            "verified_pairs_with_meaning": pairs_with_meaning,
            "a1_inventory_lemmas_total": len(inv_lemmas),
            "a1_inventory_lemmas_with_paronym": len(matched_a1),
            "a1_single_token_keys_total": len(single_keys),
            "a1_single_token_keys_with_paronym": len(matched_a1_keys),
            "a1_slices_2_to_6_lemmas_total": len(slice_lemmas),
            "a1_slices_2_to_6_lemmas_with_paronym": len(matched_a1_slices),
        },
        "a1_coverage": {
            "inventory_path": str(DEFAULT_A1_INVENTORY),
            "matched_a1_lemmas": [
                {
                    "lemma": lemma,
                    "paronyms": sorted(word_to_paronyms[lemma]),
                    "pair_ids": sorted(word_to_pair_ids[lemma]),
                }
                for lemma in matched_a1
            ],
            "matched_a1_slices_2_to_6_lemmas": matched_a1_slices,
        },
        "pairs": pairs_out,
        "unverified": unverified_out,
    }


def serialize_registry(payload: dict[str, Any]) -> str:
    """Deterministic UTF-8 JSON representation."""
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources-db", type=Path, default=None, help="Explicit sources.db path")
    parser.add_argument("--vesum-db", type=Path, default=None, help="Explicit vesum.db path")
    parser.add_argument(
        "--miyklas-raw",
        type=Path,
        default=DEFAULT_MIYKLAS_RAW,
        help="Path to MiyKlas raw provenance snapshot JSON (optional if --textbooks-only)",
    )
    parser.add_argument(
        "--fetch-miyklas",
        action="store_true",
        help="Fetch live MiyKlas pages and write --miyklas-raw before extracting",
    )
    parser.add_argument(
        "--textbooks-only",
        action="store_true",
        help="Run extraction on sources.db textbooks only (skip MiyKlas)",
    )
    parser.add_argument(
        "--a1-inventory",
        type=Path,
        default=DEFAULT_A1_INVENTORY,
        help="Path to registry/atlas/a1-v1-inventory.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output path for paronyms-v1.json",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify --output matches freshly rebuilt bytes without writing",
    )
    args = parser.parse_args(argv)

    worktree_root = Path(__file__).resolve().parents[3]
    primary_root = main_checkout_root(worktree_root)
    sources_db = _resolve_sources_db(primary_root, args.sources_db)

    docs = load_textbook_paronym_documents(sources_db)
    miyklas_meta: dict[str, Any] | None = None
    recipe_note = (
        "MiyKlas raw snapshot stored with URL, UTC fetch timestamp, HTTP status, "
        "and raw HTML + extracted text SHA-256 digests; live data/sources.db left "
        "untouched because bulk_root is unavailable and sources.db is a read-only "
        "generation requiring primary-checkout driver publication."
    )

    if not args.textbooks_only:
        miyklas_path = (
            args.miyklas_raw
            if args.miyklas_raw.is_absolute()
            else worktree_root / args.miyklas_raw
        )
        if args.fetch_miyklas:
            snapshot = fetch_miyklas_pages()
            _atomic_write_text(
                miyklas_path,
                json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
            )
        if not miyklas_path.exists():
            raise FileNotFoundError(
                f"MiyKlas snapshot not found at {miyklas_path}; pass --fetch-miyklas or --textbooks-only"
            )
        miyklas_meta, miyklas_docs = load_miyklas_documents(miyklas_path)
        docs.extend(miyklas_docs)
    else:
        recipe_note = (
            "Textbooks-only mode: MiyKlas excluded because docs/corpus-inventory.md "
            "safe literary-content recipe requires a mounted bulk_root (unavailable) "
            "and primary-checkout sources.db generation publication."
        )

    a1_path = (
        args.a1_inventory
        if args.a1_inventory.is_absolute()
        else worktree_root / args.a1_inventory
    )
    a1_sets = load_a1_lemma_sets(a1_path)
    payload = build_paronym_registry(
        docs,
        vesum_lookup=_default_vesum_lookup(args.vesum_db),
        a1_lemma_sets=a1_sets,
        miyklas_meta=miyklas_meta,
        corpus_recipe_note=recipe_note,
    )
    rendered = serialize_registry(payload)

    out_path = args.output if args.output.is_absolute() else worktree_root / args.output
    if args.check:
        if not out_path.exists():
            print(f"MISSING: {out_path}", file=sys.stderr)
            return 1
        existing = out_path.read_text(encoding="utf-8")
        if existing != rendered:
            print(
                f"DRIFT: {out_path} differs from rebuilt output "
                f"(existing sha256={hashlib.sha256(existing.encode()).hexdigest()[:12]}, "
                f"rebuilt sha256={hashlib.sha256(rendered.encode()).hexdigest()[:12]})",
                file=sys.stderr,
            )
            return 1
        print(json.dumps(payload["counts"], ensure_ascii=False, indent=2))
        return 0

    _atomic_write_text(out_path, rendered)
    print(json.dumps(payload["counts"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Build the source-attested, VESUM-verified paronym registry for Atlas word cards.

Reads textbook chunks from ``sources.db`` (read-only) and the provenance-pinned MiyKlas raw
snapshot, runs the deterministic extractor, verifies every member in VESUM, routes any
unattested member to ``unverified`` with an explicit reason, computes A1 word-card lemma
coverage, and emits deterministic JSON.

This is a one-shot build tool, not a reusable parser: the extractor is certified only on the
reviewed corpus. The registry records that corpus's fingerprint, and the build refuses
(``REFUSED:``, exit 2, nothing written) under build and ``--check`` when the live corpus differs
(``CorpusFingerprintError``) or when any step from reading an input to the final comparison fails.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve(strict=True).parents[3]))

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
from scripts.atlas.paronyms.miyklas import (
    load_miyklas_documents,
    validate_miyklas_page_dict,
)
from scripts.verification import vesum as vesum_mod

SCHEMA_VERSION = "atlas-paronyms.v1"
DEFAULT_OUTPUT = Path("registry/atlas/paronyms-v1.json")
DEFAULT_A1_INVENTORY = Path("registry/atlas/a1-v1-inventory.json")
DEFAULT_MIYKLAS_RAW = Path("registry/miyklas/paronyms-raw-v1.json")
TEXTBOOK_FTS_QUERY = "паронім*"
# A refusal names its cause; an oversize input value must not flood stderr.
_MAX_REFUSAL_CHARS = 2000
_TRUNCATED = " ... (truncated)"

VesumBatchLookup = Callable[[list[str]], dict[str, list[dict[str, Any]]]]
# word -> СУМ-20 article texts whose headword key is that word.
Sum20ArticleLookup = Callable[[list[str]], dict[str, list[str]]]

# A СУМ-20 article that sends its headword to another word ("ПЛАСКИ́Й див. пло́ский",
# "СЛИЗНЯ́К ... Те саме, що слима́к") marks the two as one meaning, not a paronym contrast.
_SUM20_VARIANT_REF_RE = re.compile(r"(?:(?<!\w)див\.|(?<!\w)те\s+саме,\s+що)\s+([^\s,.;:()\d¹²³⁴]+)", re.IGNORECASE)


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


class CorpusFingerprintError(ValueError):
    """The live corpus is not the reviewed corpus pinned in the registry; the build refuses."""


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def compute_corpus_fingerprint(textbook_docs: list[SourceDocument], miyklas_snapshot: dict[str, Any]) -> dict[str, Any]:
    """Digest the textbook query result set and the loaded MiyKlas snapshot the extractor reads.

    Both digests are taken from the data as loaded for extraction (no second read), so the
    fingerprint describes exactly what the extractor saw.
    """
    rows = [
        [d.chunk_id, d.source_file, d.title, d.grade, d.author, d.text]
        for d in textbook_docs
        if d.source_type == "textbook"
    ]
    return {
        "textbooks_fts_query": TEXTBOOK_FTS_QUERY,
        "textbooks_result_rows": len(rows),
        "textbooks_result_sha256": _canonical_sha256(rows),
        "miyklas_pages": len(miyklas_snapshot.get("pages") or []),
        "miyklas_snapshot_sha256": _canonical_sha256(miyklas_snapshot),
    }


def read_pinned_corpus_fingerprint(registry_path: Path) -> dict[str, Any]:
    """Return the corpus fingerprint recorded in the reviewed registry, or refuse."""
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CorpusFingerprintError(
            f"no reviewed registry at {registry_path}: no corpus is pinned, so the build refuses"
        ) from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CorpusFingerprintError(f"unreadable registry {registry_path}: {exc}") from exc
    corpus = payload.get("sources_corpus") if isinstance(payload, dict) else None
    pinned = corpus.get("corpus_fingerprint") if isinstance(corpus, dict) else None
    if not isinstance(pinned, dict) or not pinned:
        raise CorpusFingerprintError(
            f"{registry_path} records no sources_corpus.corpus_fingerprint: no corpus is pinned, so the build refuses"
        )
    return pinned


def require_pinned_corpus(pinned: dict[str, Any], live: dict[str, Any]) -> None:
    """Refuse unless the live corpus fingerprint equals the pinned one, naming every differing field."""
    # Compare key presence and canonical JSON per field, so a missing or extra key (even one set to
    # null) and a value of another type (5.0 for 5, true for 1) all differ.
    missing = "<absent>"
    differing = sorted(
        key
        for key in set(pinned) | set(live)
        if (key in pinned) != (key in live)
        or json.dumps(pinned.get(key), ensure_ascii=False) != json.dumps(live.get(key), ensure_ascii=False)
    )
    if differing:
        detail = "; ".join(
            f"{key}: pinned {pinned.get(key, missing)!r}, live {live.get(key, missing)!r}" for key in differing
        )
        raise CorpusFingerprintError(
            "corpus differs from the reviewed corpus the extractor is certified on "
            f"(one-shot build tool, see docs/atlas/paronyms.md): {detail}"
        )


def _default_sum20_lookup(sources_db: Path) -> Sum20ArticleLookup:
    """Read СУМ-20 mirror articles for the given words from the local sources store (read-only)."""

    def lookup(words: list[str]) -> dict[str, list[str]]:
        found: dict[str, list[str]] = defaultdict(list)
        placeholders = ",".join("?" * len(words))
        with open_readonly(sources_db) as conn:
            if conn.execute("SELECT 1 FROM sum20_mirror_articles LIMIT 1").fetchone() is None:
                # An empty mirror would silently admit every variant; refuse instead.
                raise ValueError(
                    "sum20_mirror_articles is empty in sources.db; same-meaning variants cannot be checked"
                )
            rows = conn.execute(
                "SELECT normalized_lookup_key, article_text FROM sum20_mirror_articles "
                f"WHERE normalized_lookup_key IN ({placeholders}) ORDER BY normalized_lookup_key, id",
                words,
            ).fetchall()
        for key, text in rows:
            found[str(key)].append(str(text or ""))
        return dict(found)

    return lookup


# The primary meaning ends where sense 2 or the next homonym (a headword with a superscript) starts.
_SUM20_PRIMARY_END_RE = re.compile(r"\s2\.\s|[А-ЯІЇЄҐ'’ʼ\u0301]{2,}[²³⁴⁵]")


def _is_sum20_header_token(token: str) -> bool:
    """True for an article-header token: a headword, a sense number or a grammar/usage label."""
    bare = token.replace("\u0301", "").strip(",;")
    if not bare:
        return True
    letters = bare.strip(".¹²³⁴⁵0123456789'’ʼ")
    if not letters:  # "1." and similar sense numbers
        return True
    if letters.isupper() or (letters.islower() and len(letters) <= 5):  # headword; "а́", "ч.", "воді"
        return True
    return bare.endswith(".")  # labels such as "рідко.", "недок.", "розм."


def _sum20_variant_evidence(word: str, other: str, articles: dict[str, list[str]]) -> str | None:
    """The СУМ-20 excerpt whose primary meaning refers ``word`` directly to ``other``, or None.

    Only the first sense of the first homonym counts: textbook paronyms such as
    людний/людяний overlap in a rare or obsolete later sense but differ in their main one.
    A parenthetical cross-reference ("(див. вага́¹ 1)") is not a definition.
    """
    for text in articles.get(word, []):
        end = _SUM20_PRIMARY_END_RE.search(text)
        primary = text[: end.start()] if end else text
        for m in _SUM20_VARIANT_REF_RE.finditer(primary):
            before = primary[: m.start()]
            if before.count("(") > before.count(")") or before.count("[") > before.count("]"):
                continue
            # The reference must open the definition: only the headword and its grammar and
            # usage labels may precede it, never definition or example text.
            header = before.split()
            if header and normalize_token(header[0]) == word:
                header = header[1:]  # the mirror text opens with an echo of the lookup key
            if not all(_is_sum20_header_token(tok) for tok in header):
                continue
            target = normalize_token(unicodedata.normalize("NFC", m.group(1)).replace("\u0301", ""))
            if target == other:
                return " ".join(text[max(0, m.start() - 40) : m.end()].split())
    return None


def _default_vesum_lookup(vesum_db: Path | None) -> VesumBatchLookup:
    def lookup(words: list[str]) -> dict[str, list[dict[str, Any]]]:
        return vesum_mod.verify_words(words, db_path=vesum_db)

    return lookup


def _unique_sorted(items: list[str]) -> list[str]:
    return sorted({x for x in items if x})


_GLOSS_WORD_RE = re.compile(r"(?<![\w'’ʼ-])[а-щьюяєіїґА-ЩЬЮЯЄІЇҐ][а-щьюяєіїґ'’ʼ]*(?:-[а-щьюяєіїґ'’ʼ]+)*")


def _gloss_words(text: str) -> list[str]:
    """Ukrainian words of a gloss, normalised to lower case (Latin text is not checked).

    A sentence-initial capital does not exempt a common word ("Оспівний").
    """
    return [normalize_token(m.group(0)) for m in _GLOSS_WORD_RE.finditer(text)]


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

    # Only a choice exercise inflects its options to fit a sentence. Any other pattern cites the
    # words as the source chose them (e.g. plural-only "в'язи" vs "м'язи"), so keep that pair.
    if att.pattern != "exercise_choice_pair":
        return (wa, wb, True, []) if wa <= wb else (wb, wa, True, [])

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


class A1InventoryError(ValueError):
    """The A1 inventory is missing, unreadable or malformed; coverage cannot be computed."""


def load_a1_lemma_sets(a1_inventory_path: Path) -> dict[str, set[str]]:
    """Load A1 card lemma sets from ``a1-v1-inventory.json`` only.

    Fails closed with :class:`A1InventoryError` naming the file when it is missing,
    unreadable, not JSON, or when any row lacks a unique non-empty ``id``, a valid
    ``mapping`` or a string ``key``. The file is opened directly (no existence probe), so
    permission and other OS errors surface instead of reading as "absent".
    """
    name = a1_inventory_path.name
    try:
        raw = a1_inventory_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise A1InventoryError(f"Missing A1 inventory {a1_inventory_path}") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise A1InventoryError(f"Unreadable A1 inventory {a1_inventory_path}: {exc}") from exc
    try:
        inv = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise A1InventoryError(f"Invalid JSON in {name}: {exc}") from exc
    try:
        # A JSON escape such as \ud800 decodes to a lone surrogate, which is not text.
        json.dumps(inv, ensure_ascii=False).encode("utf-8")
    except UnicodeEncodeError as exc:
        raise A1InventoryError(f"{name} contains a string that is not valid Unicode: {exc}") from exc
    if not isinstance(inv, dict):
        raise A1InventoryError(f"Expected JSON object in {name}, got {type(inv).__name__}")
    rows = inv.get("rows")
    if not isinstance(rows, list) or not rows:
        raise A1InventoryError(f"Missing, non-list or empty 'rows' in {name}")

    inventory_lemmas: set[str] = set()
    single_token_keys: set[str] = set()
    seen_ids: set[str] = set()
    valid_resolutions = {"resolved", "unresolved", "ambiguous"}
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise A1InventoryError(f"Expected object row at index {index} in {name}")
        rid = row.get("id")
        if not isinstance(rid, str) or not rid.strip():
            raise A1InventoryError(f"Missing or empty row 'id' at index {index} in {name}")
        if rid in seen_ids:
            raise A1InventoryError(f"Duplicate row 'id' {rid!r} in {name}")
        seen_ids.add(rid)
        mapping = row.get("mapping")
        if not isinstance(mapping, dict):
            raise A1InventoryError(f"Missing or non-object 'mapping' in row {rid!r} of {name}")
        resolution = mapping.get("resolution")
        if not isinstance(resolution, str) or resolution not in valid_resolutions:
            raise A1InventoryError(f"Missing or invalid 'mapping.resolution' {resolution!r} in row {rid!r} of {name}")
        lemma = mapping.get("lemma")
        if resolution == "resolved":
            if not isinstance(lemma, str) or not normalize_token(lemma):
                raise A1InventoryError(f"Resolved row {rid!r} lacks a non-empty string 'mapping.lemma' in {name}")
            inventory_lemmas.add(normalize_token(lemma))
        elif lemma is not None:
            # The inventory producer (scripts/atlas/a1_vocabulary_inventory.py) writes a null
            # lemma for every unresolved or ambiguous row; anything else is an inconsistent row.
            raise A1InventoryError(
                f"{resolution.capitalize()} row {rid!r} has non-null 'mapping.lemma' {lemma!r} in {name}"
            )
        key = row.get("key")
        if not isinstance(key, str):
            raise A1InventoryError(f"Missing or non-string 'key' in row {rid!r} of {name}")
        if key.strip() and " " not in key and "/" not in key:
            single_token_keys.add(normalize_token(key))

    return {
        "inventory_lemmas": inventory_lemmas,
        "single_token_keys": single_token_keys,
    }


def _atomic_write_text(dest: Path, content: str) -> None:
    """Write UTF-8 text atomically via a PID-scoped sibling staging file."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    stage_path = dest.with_name(f".{dest.name}.{os.getpid()}.stage")
    try:
        stage_path.write_text(content, encoding="utf-8")
        os.replace(stage_path, dest)
    except BaseException:
        stage_path.unlink(missing_ok=True)
        raise


def build_paronym_registry(
    documents: list[SourceDocument],
    *,
    vesum_lookup: VesumBatchLookup,
    sum20_lookup: Sum20ArticleLookup,
    a1_lemma_sets: dict[str, set[str]],
    miyklas_meta: dict[str, Any] | None = None,
    corpus_recipe_note: str = "",
    corpus_fingerprint: dict[str, Any] | None = None,
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
        {w for att in raw_attestations for w in (att.member_a.word, att.member_b.word) if " " not in w}
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
        lemmas_a = {normalize_token(str(r.get("lemma", ""))) for r in vesum_results.get(att.member_a.word, [])}
        if ca in lemmas_a:
            return (ca, att.member_a), (cb, att.member_b)
        return (ca, att.member_b), (cb, att.member_a)

    for att, ca, cb, is_surf, unv in resolved_rows:
        if not unv:
            # Fail closed if pass-2 canonical lemma lookup returned empty analyses.
            canon_unv = [
                {"word": w, "reason": "not_attested_in_vesum"} for w in (ca, cb) if " " in w or not vesum_results.get(w)
            ]
            if canon_unv:
                unv = canon_unv
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

    # Same-meaning variants are not "do not confuse" pairs: withhold a pair when a СУМ-20 article
    # refers one member directly to the other. Antonymic and synonymic paronyms that the sources
    # teach as paronyms stay (see docs/atlas/paronyms.md).
    variant_words = sorted({w for pair_key in verified_groups for w in pair_key})
    sum20_articles = sum20_lookup(variant_words) if variant_words else {}
    for pair_key in sorted(verified_groups):
        ca, cb = pair_key
        for word, other in ((ca, cb), (cb, ca)):
            evidence = _sum20_variant_evidence(word, other, sum20_articles)
            if evidence is None:
                continue
            bucket = verified_groups.pop(pair_key)
            bucket["unverified_members"] = [{"word": word, "reason": "same_meaning_variant", "evidence": evidence}]
            if pair_key in unverified_groups:
                merged = unverified_groups[pair_key]
                merged["sources"].extend(src for src in bucket["sources"] if src not in merged["sources"])
                merged["unverified_members"].extend(bucket["unverified_members"])
            else:
                unverified_groups[pair_key] = bucket
            break

    # A source gloss is shown to learners only when VESUM attests every lowercase word in it;
    # a gloss carrying a source typo (e.g. "оспівний") is withheld. The quoted line stays verbatim.
    gloss_words = sorted(
        {
            w
            for buckets in (verified_groups, unverified_groups)
            for bucket in buckets.values()
            for m_bucket in bucket["members_map"].values()
            for note in m_bucket["meanings"]
            for word in _gloss_words(note["text"])
            for w in (word, *word.split("-"))
            if w
        }
        - set(vesum_results)
    )
    if gloss_words:
        vesum_results = {**vesum_results, **vesum_lookup(gloss_words)}

    def _attested_word(word: str) -> bool:
        # A hyphenated compound ("писемно-літературного") counts when each part is attested.
        return bool(vesum_results.get(word)) or all(vesum_results.get(part) for part in word.split("-"))

    def _attested_gloss(note: dict[str, str]) -> bool:
        return all(_attested_word(w) for w in _gloss_words(note["text"]))

    def _infinitive_gloss_for_non_verb(note: dict[str, str], analyses: list[dict[str, Any]]) -> bool:
        # A gloss headed by a verb infinitive defines an action, so it misdefines a member that
        # VESUM analyses only as a non-verb ("мимохідь" adv: "проходити мимо по дорозі").
        words = _gloss_words(note["text"])
        if not words or not analyses or any(r.get("pos") == "verb" for r in analyses):
            return False
        head = vesum_results.get(words[0], [])
        return bool(head) and all(":inf" in str(r.get("tags", "")) for r in head)

    def _finalize_member(word: str, m_bucket: dict[str, Any], *, surface_form: bool) -> dict[str, Any]:
        analyses = vesum_results.get(word, []) if " " not in word else []
        m_bucket = {
            **m_bucket,
            "meanings": [
                n
                for n in m_bucket["meanings"]
                if _attested_gloss(n) and not _infinitive_gloss_for_non_verb(n, analyses)
            ],
        }
        lexeme_analyses = analyses
        if surface_form:
            # A surface-form pair is about the cited forms. VESUM can tie such a form to an
            # unrelated homonym ("в'язи" 'nape' only as a form of "в'яз" 'elm'), so the registry
            # asserts no lexeme for it beyond the form being its own lemma.
            lexeme_analyses = [r for r in analyses if normalize_token(str(r.get("lemma", ""))) == word]
        lemmas = _unique_sorted([normalize_token(str(r.get("lemma", ""))) for r in lexeme_analyses])
        pos_list = _unique_sorted([str(r.get("pos", "")) for r in lexeme_analyses])
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

        m_a = _finalize_member(ca, bucket["members_map"][ca], surface_form=bucket["surface_form_pair"])
        m_b = _finalize_member(cb, bucket["members_map"][cb], surface_form=bucket["surface_form_pair"])
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
                    _finalize_member(ca, bucket["members_map"][ca], surface_form=bucket["surface_form_pair"]),
                    _finalize_member(cb, bucket["members_map"][cb], surface_form=bucket["surface_form_pair"]),
                ],
                "sources": sources_sorted,
            }
        )

    # A1 coverage accounting (only verified pairs count toward coverage).
    inv_lemmas = a1_lemma_sets.get("inventory_lemmas", set())
    single_keys = a1_lemma_sets.get("single_token_keys", set())

    matched_a1 = sorted(inv_lemmas & set(word_to_paronyms))
    matched_a1_keys = sorted(single_keys & set(word_to_paronyms))

    miyklas_pages_summary = []
    if miyklas_meta is not None:
        if not isinstance(miyklas_meta, dict) or not isinstance(miyklas_meta.get("pages"), list):
            raise ValueError("Expected miyklas_meta dict with 'pages' list")
        for raw_p in miyklas_meta["pages"]:
            p = validate_miyklas_page_dict(raw_p, verify_text_digest=False)
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
            "corpus_fingerprint": corpus_fingerprint or {},
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
        help="Path to the pinned MiyKlas raw provenance snapshot JSON",
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

    worktree_root = Path(__file__).resolve(strict=True).parents[3]
    recipe_note = (
        "MiyKlas raw snapshot stored with canonical URL, UTC fetch timestamp, HTTP status, "
        "and raw HTML + extracted text SHA-256 digests; live data/sources.db is left "
        "untouched because docs/corpus-inventory.md requires a mounted bulk corpus root "
        "and primary-checkout generation publication to add literary sources."
    )
    miyklas_path = args.miyklas_raw if args.miyklas_raw.is_absolute() else worktree_root / args.miyklas_raw
    out_path = args.output if args.output.is_absolute() else worktree_root / args.output

    a1_path = args.a1_inventory if args.a1_inventory.is_absolute() else worktree_root / args.a1_inventory

    # One refusal boundary, fail closed: every step from reading the first input to the final
    # comparison (the pin gate, the rebuild and, under --check, the byte comparison) runs inside it.
    # Any failure there, whatever its type (an unreadable or non-UTF-8 file, wrong JSON types,
    # missing keys, nesting deep enough to exhaust the stack, input too large for memory), means
    # the inputs are not the reviewed ones; nothing has been written yet, so the build refuses.
    try:
        sources_db = _resolve_sources_db(main_checkout_root(worktree_root), args.sources_db)
        docs = load_textbook_paronym_documents(sources_db)
        miyklas_meta, miyklas_docs = load_miyklas_documents(miyklas_path)
        corpus_fingerprint = compute_corpus_fingerprint(docs, miyklas_meta)
        require_pinned_corpus(read_pinned_corpus_fingerprint(out_path), corpus_fingerprint)
        payload = build_paronym_registry(
            [*docs, *miyklas_docs],
            vesum_lookup=_default_vesum_lookup(args.vesum_db),
            sum20_lookup=_default_sum20_lookup(sources_db),
            a1_lemma_sets=load_a1_lemma_sets(a1_path),
            miyklas_meta=miyklas_meta,
            corpus_recipe_note=recipe_note,
            corpus_fingerprint=corpus_fingerprint,
        )
        rendered = serialize_registry(payload)
        drift = None
        if args.check:
            # Compare bytes: a text read would normalize CRLF and hide a byte difference.
            existing = out_path.read_bytes()
            rebuilt = rendered.encode("utf-8")
            if existing != rebuilt:
                drift = (
                    f"DRIFT: {out_path} differs from rebuilt output "
                    f"(existing sha256={hashlib.sha256(existing).hexdigest()[:12]}, "
                    f"rebuilt sha256={hashlib.sha256(rebuilt).hexdigest()[:12]})"
                )
    except Exception as exc:  # the fail-closed boundary above; KeyboardInterrupt still propagates
        reason = str(exc) if isinstance(exc, CorpusFingerprintError) else f"{type(exc).__name__}: {exc}"
        if len(reason) > _MAX_REFUSAL_CHARS:
            reason = reason[: _MAX_REFUSAL_CHARS - len(_TRUNCATED)] + _TRUNCATED
        print(f"REFUSED: {reason}", file=sys.stderr)
        return 2

    if args.check:
        if drift is not None:
            print(drift, file=sys.stderr)
            return 1
        print(json.dumps(payload["counts"], ensure_ascii=False, indent=2))
        return 0

    _atomic_write_text(out_path, rendered)
    print(json.dumps(payload["counts"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

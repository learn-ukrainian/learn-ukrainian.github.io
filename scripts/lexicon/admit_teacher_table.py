#!/usr/bin/env python3
"""Admit and English-enrich a private teacher table in a local Atlas snapshot.

This is a local-only intake command.  It accepts the current table extract and
an Atlas manifest explicitly, uses VESUM only for single-token entries, leaves
multiword rows as expression entries, and writes private deltas plus a named
residual ledger.  ``--write`` never permits replacing the input manifest: it
writes a separate staged snapshot for an operator-controlled promotion.

Example (all generated outputs are gitignored)::

    /absolute/path/to/.venv/bin/python -m scripts.lexicon.admit_teacher_table \
      --extract /secure/input/combined-master-vocabulary-table-3-current.json \
      --queue /secure/input/teacher-table-atlas-work-queue.json \
      --manifest-in /secure/input/lexicon-manifest.json \
      --manifest-out batch_state/atlas/teacher-table/lexicon-manifest.staged.json \
      --write
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sqlite3
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.lexicon import enrich_manifest
from scripts.lexicon.build_data_manifest import _lemma_key, _slug_for_url
from scripts.lexicon.lemma_normalization import strip_acute_stress
from scripts.verification.vesum import verify_words

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_DIR = ROOT / "batch_state" / "atlas" / "teacher-table"
DEFAULT_VESUM = ROOT / "data" / "vesum.db"
DEFAULT_SOURCES_DB = ROOT / "data" / "sources.db"
DEFAULT_KAIKKI = ROOT / "data" / "lexicon" / "kaikki_uk_lookup.json"
TABLE_TRANSLATION_SOURCE = "teacher table #3 English gloss"
TABLE_PROVENANCE = {
    "source_family": "teacher_lesson",
    "source_locator": "teacher_table:3",
    "extraction_mode": "reviewed_inventory",
    "visibility": "private",
    "redistributable": False,
}

VesumLookup = Callable[[list[str], Path], dict[str, list[dict[str, Any]]]]
DictionaryLookup = Callable[[str, str, str], dict[str, Any] | None]

_POS_MAP = {
    "adj": "adjective",
    "adjective": "adjective",
    "adv": "adverb",
    "adverb": "adverb",
    "conj": "conjunction",
    "conjunction": "conjunction",
    "intj": "interjection",
    "interjection": "interjection",
    "noun": "noun",
    "numr": "numeral",
    "numeral": "numeral",
    "part": "particle",
    "particle": "particle",
    "prep": "preposition",
    "preposition": "preposition",
    "pron": "pronoun",
    "pronoun": "pronoun",
    "verb": "verb",
}
_UKRAINIAN_LETTERS = frozenset("абвгґдеєжзиіїйклмнопрстуфхцчшщьюя")


@dataclass(frozen=True)
class TableRow:
    """One distinct table term and its source-provided English learner gloss."""

    lemma: str
    english: str

    @property
    def key(self) -> str:
        return _lemma_key(self.lemma)

    @property
    def is_expression(self) -> bool:
        return " " in self.lemma


@dataclass(frozen=True)
class SingleTokenResolution:
    """A VESUM-proved canonical Atlas headword for one table surface."""

    lemma: str
    pos: str


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _clean_lemma(value: object) -> str:
    return " ".join(strip_acute_stress(str(value or "")).split())


def _is_english(value: str) -> bool:
    letters = {char.casefold() for char in value if char.isalpha()}
    return bool(letters) and any("a" <= char <= "z" for char in letters) and not bool(letters & _UKRAINIAN_LETTERS)


def _has_translation(entry: Mapping[str, Any]) -> bool:
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, Mapping):
        return False
    translation = enrichment.get("translation")
    if not isinstance(translation, Mapping):
        return False
    terms = translation.get("en")
    return isinstance(terms, list) and any(isinstance(term, str) and term.strip() for term in terms)


def _read_extract(path: Path) -> tuple[list[TableRow], dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = payload.get("entries") if isinstance(payload, Mapping) else None
    if not isinstance(entries, list):
        raise ValueError(f"{path}: expected an object with an entries list")

    rows: dict[str, TableRow] = {}
    duplicate_gloss_conflicts = 0
    for index, raw in enumerate(entries):
        if not isinstance(raw, Mapping):
            raise ValueError(f"{path}: entries[{index}] must be an object")
        lemma = _clean_lemma(raw.get("uk"))
        english = " ".join(str(raw.get("en") or "").split())
        if not lemma:
            raise ValueError(f"{path}: entries[{index}] has no Ukrainian term")
        key = _lemma_key(lemma)
        existing = rows.get(key)
        if existing is None:
            rows[key] = TableRow(lemma=lemma, english=english)
        elif existing.english != english:
            duplicate_gloss_conflicts += 1

    if duplicate_gloss_conflicts:
        raise ValueError(
            f"{path}: {duplicate_gloss_conflicts} normalized table key(s) have conflicting English glosses"
        )

    ordered = [rows[key] for key in sorted(rows)]
    return ordered, {
        "extract_entries": len(entries),
        "unique_table_keys": len(ordered),
        "duplicate_gloss_conflicts": duplicate_gloss_conflicts,
    }


def _read_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("entries"), list):
        raise ValueError(f"{path}: expected an object with an entries list")
    return payload


def _manifest_index(manifest: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]], set[str]]:
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("manifest entries must be a list")
    by_key: dict[str, dict[str, Any]] = {}
    slugs: set[str] = set()
    for raw in entries:
        if not isinstance(raw, dict):
            continue
        lemma = _clean_lemma(raw.get("lemma"))
        if lemma:
            by_key.setdefault(_lemma_key(lemma), raw)
        teacher_table_keys = raw.get("teacher_table_keys")
        if isinstance(teacher_table_keys, list):
            for table_key in teacher_table_keys:
                normalized = _clean_lemma(table_key)
                if normalized:
                    by_key.setdefault(_lemma_key(normalized), raw)
        slug = str(raw.get("url_slug") or "").strip()
        if slug:
            slugs.add(slug)
    return by_key, slugs


def measure_table_coverage(rows: Sequence[TableRow], manifest: Mapping[str, Any]) -> dict[str, list[TableRow]]:
    """Measure direct table-key coverage and translation-card coverage."""
    by_key, _ = _manifest_index(manifest)
    missing: list[TableRow] = []
    thin: list[TableRow] = []
    covered: list[TableRow] = []
    for row in rows:
        entry = by_key.get(row.key)
        if entry is None:
            missing.append(row)
        elif not _has_translation(entry):
            thin.append(row)
        else:
            covered.append(row)
    return {"missing": missing, "thin": thin, "covered": covered}


def _queue_alignment(queue_path: Path | None, before: Mapping[str, Sequence[TableRow]]) -> dict[str, Any] | None:
    if queue_path is None:
        return None
    payload = json.loads(queue_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{queue_path}: expected an object")

    def keys(name: str) -> set[str]:
        items = payload.get(name)
        if not isinstance(items, list):
            raise ValueError(f"{queue_path}: {name} must be a list")
        return {_lemma_key(_clean_lemma(item.get("uk"))) for item in items if isinstance(item, Mapping) and _clean_lemma(item.get("uk"))}

    queued_missing = keys("missing_atlas")
    queued_thin = keys("needs_en_enrichment")
    measured_missing = {row.key for row in before["missing"]}
    measured_thin = {row.key for row in before["thin"]}
    return {
        "queue_missing_count": len(queued_missing),
        "queue_thin_count": len(queued_thin),
        "missing_exact_match": queued_missing == measured_missing,
        "thin_exact_match": queued_thin == measured_thin,
    }


def _single_token_resolution(analyses: Sequence[Mapping[str, Any]]) -> SingleTokenResolution | None:
    """Resolve a surface only when VESUM supplies one citation-form lemma/POS.

    ``verify_words`` looks up ``forms.word_form``.  A valid surface form alone
    cannot be promoted as a Word Atlas lemma, because it may be inflected.  The
    table surface is retained separately for local membership remeasurement;
    the new Atlas article always uses VESUM's one unambiguous base lemma.
    """
    lemmas = {
        _clean_lemma(analysis.get("lemma"))
        for analysis in analyses
        if isinstance(analysis, Mapping) and _clean_lemma(analysis.get("lemma"))
    }
    if len(lemmas) != 1:
        return None
    lemma = next(iter(lemmas))
    mapped = {
        _POS_MAP.get(str(analysis.get("pos") or "").casefold())
        for analysis in analyses
        if isinstance(analysis, Mapping) and _clean_lemma(analysis.get("lemma")) == lemma
    }
    mapped.discard(None)
    return SingleTokenResolution(lemma=lemma, pos=next(iter(mapped))) if len(mapped) == 1 else None


def _seed_translation(english: str) -> dict[str, Any]:
    return {"en": [english], "source": TABLE_TRANSLATION_SOURCE}


def _usable_translation(translation: object) -> bool:
    if not isinstance(translation, Mapping):
        return False
    terms = translation.get("en")
    return isinstance(terms, list) and any(_is_english(str(term).strip()) for term in terms)


def _copy_translation(translation: Mapping[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(dict(translation))


def _apply_translation(entry: dict[str, Any], translation: Mapping[str, Any]) -> None:
    enrichment = entry.get("enrichment")
    if not isinstance(enrichment, dict):
        enrichment = {}
        entry["enrichment"] = enrichment
    enrichment["translation"] = _copy_translation(translation)
    source = str(translation.get("source") or "").strip()
    if source:
        sources = {str(value) for value in enrichment.get("sources", []) if str(value).strip()}
        sources.add(source)
        enrichment["sources"] = sorted(sources)


def _new_entry(
    row: TableRow, *, atlas_lemma: str, pos: str, translation: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "lemma": atlas_lemma,
        "url_slug": _slug_for_url(atlas_lemma),
        "gloss": row.english,
        "pos": pos,
        "entry_type": "expression" if row.is_expression else "lemma",
        "review_state": "approved",
        "primary_source": "teacher_table",
        "source_provenance": [copy.deepcopy(TABLE_PROVENANCE)],
        "surface_admission": {"practice": True},
        "teacher_table_keys": [row.lemma],
        "heritage_status": {
            "classification": "unknown",
            "attestations": [],
            "is_russianism": False,
            "russian_shadow": False,
            "vesum_attested": not row.is_expression,
            "calque_warning": None,
            "warning_severity": "none",
        },
        "enrichment": {
            "translation": _copy_translation(translation),
            "sources": [str(translation["source"])],
        },
    }


def _link_teacher_table_key(entry: dict[str, Any], row: TableRow) -> bool:
    """Record a table surface that resolves to an existing canonical article."""
    raw_keys = entry.get("teacher_table_keys")
    keys = [str(value) for value in raw_keys if str(value).strip()] if isinstance(raw_keys, list) else []
    if row.lemma in keys:
        return False
    keys.append(row.lemma)
    entry["teacher_table_keys"] = keys
    return True


def _unique_teacher_table_slug(base_slug: str, occupied: set[str]) -> str:
    """Keep a distinct table expression when an older Atlas slug already exists.

    ``_slug_for_url`` intentionally folds punctuation such as apostrophes.  An
    older entry may therefore own the bare route even though it is not this
    exact table expression.  Folding the table expression into that entry would
    lose the source key, so the local-only intake reserves a deterministic
    teacher-table suffix instead.
    """
    if base_slug not in occupied:
        return base_slug
    candidate = f"{base_slug}-teacher-table"
    suffix = 2
    while candidate in occupied:
        candidate = f"{base_slug}-teacher-table-{suffix}"
        suffix += 1
    return candidate


def _default_vesum_lookup(words: list[str], vesum_db: Path) -> dict[str, list[dict[str, Any]]]:
    return verify_words(words, db_path=vesum_db)


def _build_dictionary_lookup(
    *, sources_db: Path | None, kaikki_path: Path | None
) -> tuple[DictionaryLookup | None, dict[str, Any], sqlite3.Connection | None]:
    if sources_db is None or not sources_db.is_file():
        return None, {"enabled": False, "reason": "sources_db_unavailable"}, None
    kaikki = enrich_manifest._load_kaikki_lookup(kaikki_path) if kaikki_path and kaikki_path.is_file() else {}
    connection = sqlite3.connect(f"file:{sources_db}?mode=ro", uri=True)

    def lookup(lemma: str, pos: str, english: str) -> dict[str, Any] | None:
        # Passing no Slovnyk cache intentionally keeps this intake offline: the
        # existing Dmklinger, Kaikki, and Balla paths remain available.
        result = enrich_manifest._translation(
            connection,
            lemma,
            kaikki,
            entry_pos=pos,
            gloss_hints={english},
            slovnyk_cache=None,
        )
        return result if _usable_translation(result) else None

    return lookup, {"enabled": True, "kaikki_loaded": bool(kaikki)}, connection


def _translation_for(
    row: TableRow,
    pos: str,
    dictionary_lookup: DictionaryLookup | None,
    source_counts: Counter[str],
) -> dict[str, Any]:
    if dictionary_lookup is not None:
        dictionary = dictionary_lookup(row.lemma, pos, row.english)
        if dictionary is not None:
            source_counts[str(dictionary.get("source") or "dictionary")] += 1
            return _copy_translation(dictionary)
    source_counts[TABLE_TRANSLATION_SOURCE] += 1
    return _seed_translation(row.english)


def _residual(row: TableRow, *, stage: str, reason: str, proof: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "uk": row.lemma,
        "en": row.english,
        "stage": stage,
        "reason": reason,
        "proof": dict(proof),
    }


def admit_and_enrich(
    *,
    rows: Sequence[TableRow],
    manifest: Mapping[str, Any],
    vesum_db: Path,
    vesum_lookup: VesumLookup = _default_vesum_lookup,
    dictionary_lookup: DictionaryLookup | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a staged manifest plus private deltas/report content.

    The caller injects VESUM and dictionary lookups in tests; production uses
    the local VESUM database and offline-safe local dictionary indexes.
    """
    staged = copy.deepcopy(dict(manifest))
    before = measure_table_coverage(rows, staged)
    missing = before["missing"]
    single_tokens = [row.lemma for row in missing if not row.is_expression]
    analyses_by_word = vesum_lookup(single_tokens, vesum_db) if single_tokens else {}
    by_key, slugs = _manifest_index(staged)

    residuals: list[dict[str, Any]] = []
    admitted: list[dict[str, Any]] = []
    canonical_links: list[dict[str, Any]] = []
    translation_delta: list[dict[str, Any]] = []
    source_counts: Counter[str] = Counter()
    re_enriched = 0

    for row in missing:
        if not _is_english(row.english):
            residuals.append(
                _residual(
                    row,
                    stage="admit",
                    reason="missing_or_non_english_table_gloss",
                    proof={"english_gloss_present": bool(row.english), "english_gloss_accepted": False},
                )
            )
            continue
        if row.is_expression:
            pos = "phrase"
            atlas_lemma = row.lemma
        else:
            analyses = analyses_by_word.get(row.lemma, [])
            if not analyses:
                residuals.append(
                    _residual(
                        row,
                        stage="admit",
                        reason="vesum_unattested_single_token",
                        proof={"vesum_db": vesum_db.name, "analysis_count": 0},
                    )
                )
                continue
            resolution = _single_token_resolution(analyses)
            if resolution is None:
                candidate_lemmas = {
                    _clean_lemma(analysis.get("lemma"))
                    for analysis in analyses
                    if isinstance(analysis, Mapping) and _clean_lemma(analysis.get("lemma"))
                }
                residuals.append(
                    _residual(
                        row,
                        stage="admit",
                        reason="vesum_ambiguous_lemma_or_pos",
                        proof={
                            "vesum_db": vesum_db.name,
                            "analysis_count": len(analyses),
                            "canonical_lemma_count": len(candidate_lemmas),
                        },
                    )
                )
                continue
            atlas_lemma = resolution.lemma
            pos = resolution.pos

        canonical_entry = by_key.get(_lemma_key(atlas_lemma))
        if canonical_entry is not None:
            linked = _link_teacher_table_key(canonical_entry, row)
            if linked:
                canonical_links.append(
                    {
                        "uk": row.lemma,
                        "canonical_lemma": canonical_entry.get("lemma"),
                        "url_slug": canonical_entry.get("url_slug"),
                    }
                )
            if not _has_translation(canonical_entry):
                translation = _translation_for(
                    TableRow(lemma=atlas_lemma, english=row.english), pos, dictionary_lookup, source_counts
                )
                _apply_translation(canonical_entry, translation)
                re_enriched += 1
                translation_delta.append(
                    {
                        "uk": row.lemma,
                        "url_slug": canonical_entry.get("url_slug"),
                        "translation": canonical_entry["enrichment"]["translation"],
                    }
                )
            continue

        candidate = _new_entry(
            row,
            atlas_lemma=atlas_lemma,
            pos=pos,
            translation=_translation_for(
                TableRow(lemma=atlas_lemma, english=row.english), pos, dictionary_lookup, source_counts
            ),
        )
        base_slug = candidate["url_slug"]
        if not base_slug:
            residuals.append(
                _residual(
                    row,
                    stage="admit",
                    reason="empty_generated_slug",
                    proof={"generated_slug": base_slug},
                )
            )
            continue
        slug = _unique_teacher_table_slug(base_slug, slugs)
        candidate["url_slug"] = slug
        staged["entries"].append(candidate)
        by_key[row.key] = candidate
        slugs.add(slug)
        admitted.append(candidate)
        translation_delta.append(
            {"uk": row.lemma, "url_slug": slug, "translation": candidate["enrichment"]["translation"]}
        )

    # Rebuild the index after all admissions, then fill exactly the current
    # table entries whose translation card is still absent.  Existing non-empty
    # cards are never overwritten.
    by_key, _ = _manifest_index(staged)
    for row in before["thin"]:
        entry = by_key.get(row.key)
        if entry is None:
            raise AssertionError("a pre-existing table key disappeared during teacher-table intake")
        if not _is_english(row.english):
            residuals.append(
                _residual(
                    row,
                    stage="enrich",
                    reason="missing_or_non_english_table_gloss",
                    proof={"english_gloss_present": bool(row.english), "english_gloss_accepted": False},
                )
            )
            continue
        pos = str(entry.get("pos") or "")
        translation = _translation_for(row, pos, dictionary_lookup, source_counts)
        _apply_translation(entry, translation)
        re_enriched += 1
        translation_delta.append(
            {"uk": row.lemma, "url_slug": entry.get("url_slug"), "translation": entry["enrichment"]["translation"]}
        )

    after = measure_table_coverage(rows, staged)
    residual_keys = {(item["stage"], _lemma_key(item["uk"])) for item in residuals}
    unaccounted_missing = [row for row in after["missing"] if ("admit", row.key) not in residual_keys]
    unaccounted_thin = [row for row in after["thin"] if ("enrich", row.key) not in residual_keys]
    if unaccounted_missing or unaccounted_thin:
        raise RuntimeError("teacher-table outcome has an unnamed missing or thin residual")

    artifacts = {
        "admission_delta": {
            "schema": "teacher-table-atlas-admission-delta.v1",
            "entries": admitted,
            "canonical_links": canonical_links,
        },
        "translation_delta": {
            "schema": "teacher-table-atlas-translation-delta.v1",
            "entries": translation_delta,
        },
        "counts": {
            "before_missing_atlas": len(before["missing"]),
            "before_present_without_en": len(before["thin"]),
            "admitted": len(admitted),
            "canonical_links": len(canonical_links),
            "re_enriched": re_enriched,
            "after_missing_atlas": len(after["missing"]),
            "after_present_without_en": len(after["thin"]),
            "residuals": len(residuals),
        },
        "residuals": residuals,
        "translation_sources": dict(sorted(source_counts.items())),
    }
    return staged, artifacts


def _compact_counts(coverage: Mapping[str, Sequence[TableRow]]) -> dict[str, int]:
    return {
        "missing_atlas": len(coverage["missing"]),
        "present_without_en": len(coverage["thin"]),
        "present_with_en": len(coverage["covered"]),
    }


def run(
    *,
    extract_path: Path,
    manifest_in: Path,
    queue_path: Path | None,
    vesum_db: Path,
    sources_db: Path | None,
    kaikki_path: Path | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build a local staged result and a privacy-safe accounting report."""
    rows, extract_counts = _read_extract(extract_path)
    manifest = _read_manifest(manifest_in)
    before = measure_table_coverage(rows, manifest)
    dictionary_lookup, dictionary_info, dictionary_connection = _build_dictionary_lookup(
        sources_db=sources_db, kaikki_path=kaikki_path
    )
    try:
        staged, artifacts = admit_and_enrich(
            rows=rows,
            manifest=manifest,
            vesum_db=vesum_db,
            dictionary_lookup=dictionary_lookup,
        )
    finally:
        if dictionary_connection is not None:
            dictionary_connection.close()
    after = measure_table_coverage(rows, staged)
    report = {
        "schema": "teacher-table-atlas-admit-enrich.v1",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source": {
            "extract_file": extract_path.name,
            "extract_sha256": _sha256(extract_path),
            "manifest_file": manifest_in.name,
            "manifest_sha256": _sha256(manifest_in),
            "vesum_file": vesum_db.name,
            "vesum_sha256": _sha256(vesum_db),
        },
        "denominator": {**extract_counts, "table_unique": len(rows)},
        "before": _compact_counts(before),
        "queue_alignment": _queue_alignment(queue_path, before),
        "dictionary_enrichment": dictionary_info,
        "actions": artifacts["counts"],
        "translation_sources": artifacts["translation_sources"],
        "after": _compact_counts(after),
        "residuals": artifacts["residuals"],
        "local_apply": True,
        "public_cutover": "operator_go_required",
    }
    return staged, artifacts, report


def _output_paths(report_dir: Path) -> dict[str, Path]:
    return {
        "admission_delta": report_dir / "admission-delta.json",
        "translation_delta": report_dir / "translation-delta.json",
        "report": report_dir / "report.json",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", type=Path, required=True, help="Current teacher-table extract JSON")
    parser.add_argument("--manifest-in", type=Path, required=True, help="Read-only Atlas manifest snapshot")
    parser.add_argument("--queue", type=Path, help="Optional current teacher-table work queue for consistency proof")
    parser.add_argument("--vesum-db", type=Path, default=DEFAULT_VESUM)
    parser.add_argument("--sources-db", type=Path, default=DEFAULT_SOURCES_DB)
    parser.add_argument("--kaikki-lookup", type=Path, default=DEFAULT_KAIKKI)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--manifest-out", type=Path, help="Separate local staged manifest written only with --write")
    parser.add_argument("--write", action="store_true", help="Write local deltas, report, and the separate staged manifest")
    args = parser.parse_args(argv)

    if args.write and args.manifest_out is None:
        parser.error("--write requires --manifest-out; the input manifest is never a write target")
    if args.manifest_out and args.manifest_out.resolve() == args.manifest_in.resolve():
        parser.error("--manifest-out must differ from --manifest-in")
    for required in (args.extract, args.manifest_in, args.vesum_db):
        if not required.is_file():
            parser.error(f"required input is missing: {required}")
    if args.queue and not args.queue.is_file():
        parser.error(f"queue is missing: {args.queue}")

    staged, artifacts, report = run(
        extract_path=args.extract,
        manifest_in=args.manifest_in,
        queue_path=args.queue,
        vesum_db=args.vesum_db,
        sources_db=args.sources_db if args.sources_db.is_file() else None,
        kaikki_path=args.kaikki_lookup if args.kaikki_lookup.is_file() else None,
    )
    if args.write:
        assert args.manifest_out is not None
        _atomic_write_json(args.manifest_out, staged)
        paths = _output_paths(args.report_dir)
        _atomic_write_json(paths["admission_delta"], artifacts["admission_delta"])
        _atomic_write_json(paths["translation_delta"], artifacts["translation_delta"])
        _atomic_write_json(paths["report"], report)

    # Terminal output intentionally contains only counts and paths, never table terms.
    print(
        json.dumps(
            {
                "denominator": report["denominator"]["table_unique"],
                "before": report["before"],
                "actions": report["actions"],
                "after": report["after"],
                "residual_count": len(report["residuals"]),
                "wrote": bool(args.write),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

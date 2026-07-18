"""Build the Word Atlas (Лексикон) data manifest for Site static rendering.

Input source:
  every ``curriculum/l2-uk-en/{level}/{slug}/vocabulary.yaml`` file. Entries
  may name the Ukrainian headword as ``lemma``, ``word``, ``uk``, or ``term``;
  A1 uses ``lemma`` while A2 uses ``word``.

Output: ``site/src/data/lexicon-manifest.json`` — versioned JSON the
Astro dynamic route at ``src/pages/lexicon/[lemma].astro`` reads at build time
to materialize one static page per lemma.

The builder stays thin: lemma + course-usage + (when available) translation,
POS, and IPA. Per design §4, additional sections (etymology, definitions,
heritage status, paradigm, etc.) are layered on by enrichment.

Reproducer (run from repo root):

    .venv/bin/python -m scripts.lexicon.build_data_manifest --write

Bare invocation and ``--help`` refuse / print usage without writing the
manifest (``#5393`` sibling guard).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.lexicon.lemma_normalization import strip_acute_stress

CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
CURRICULUM_MANIFEST = CURRICULUM_ROOT / "curriculum.yaml"
MANIFEST_PATH = PROJECT_ROOT / "site" / "src" / "data" / "lexicon-manifest.json"
VESUM_ALIAS_MAP_PATH = PROJECT_ROOT / "data" / "lexicon" / "vesum_inflection_aliases.json"
_STRESS_MARK_RE = re.compile("[\u0300\u0301]")


LEMMA_FIELDS = ("lemma", "word", "uk", "term")

_NON_ATLAS_LEMMA_KEYS = {
    _key
    for _key in (
        "Давай!",
        "Смачного!",
        "Ходімо!",
        "в/у",
        "у/в",
        "і/й",
        "з/із/зі",
        "б/би",
        "най-",
        "-ся",
        "-сь",
        "1к",
        "2к",
        "кв.м",
        "грн/міс",
        "б/м",
        "неозначено-кількісний",
        "палаючий",
        "парковка",
        "пасивноподібний",
        "питально-відносний",
    )
}

VOCATIVE_TO_NOMINATIVE: dict[str, str] = {
    "Богдане": "Богдан",
    "Маріє": "Марія",
    "Олено": "Олена",
    "Соломіє": "Соломія",
    "Тарасе": "Тарас",
}

VESUM_CANONICAL_HEADS: dict[str, tuple[str, str]] = {
    "бірка": (
        "бирка",
        "VESUM and Grinchenko index the label/tag headword as бирка.",
    ),
    "доставка": (
        "доставляння",
        "VESUM indexes the delivery/action noun as доставляння; course surface доставка maps to that Atlas head.",
    ),
    "примірочна": (
        "примірочна кімната",
        "Course shorthand примірочна denotes the fitting-room phrase примірочна кімната.",
    ),
    "прийом": (
        "приймання",
        "СУМ-20/СУМ-11 define прийом as 'те саме, що приймання'; VESUM indexes приймання.",
    ),
}

SURZHYK_TO_AVOID_SEEDS: list[dict[str, str | None]] = [
    {"lemma": "агенство", "gloss": "avoid: агенція", "pos": "noun"},
    {"lemma": "авось", "gloss": "avoid: ану ж / а може", "pos": "adv"},
    {"lemma": "автозагар", "gloss": "avoid: автозасмага", "pos": "noun"},
    {"lemma": "всьо", "gloss": "avoid: все", "pos": "pron"},
    {"lemma": "діюча", "gloss": "avoid: чинна", "pos": "adj"},
    {"lemma": "міроприємство", "gloss": "avoid: захід", "pos": "noun"},
    # протиріччя REMOVED 2026-06-16: over-flag. СУМ-20 codifies it ("Те саме, що
    # суперечність") with literary attestations (Донченко/Копиленко/Харчук/Багряний);
    # NUS textbooks (Grade 6/9/10) use it; absent from Antonenko + UA-GEC;
    # check_russian_shadow=false. Sole flag-basis was LanguageTool replace.txt + the
    # Штепа purist diaspora dictionary — a stylistic preference, not surzhyk. Deeper
    # classifier over-weighting of LT/Штепа vs СУМ-20+literary tracked separately.
    {"lemma": "слідуючий", "gloss": "avoid: наступний", "pos": "adj"},
]

HERITAGE_STATUS_SEEDS: list[dict[str, str | None]] = [
    {"lemma": "вельми", "gloss": "very, exceedingly", "pos": "adv"},
    {"lemma": "глагол", "gloss": "archaic: word, speech", "pos": "noun"},
    {"lemma": "гетьман", "gloss": "hetman", "pos": "noun"},
    {"lemma": "опришок", "gloss": "opryshok", "pos": "noun"},
    {"lemma": "десятина", "gloss": "tithe; historical land unit", "pos": "noun"},
    {"lemma": "кобіта", "gloss": "regional: woman", "pos": "noun"},
]


def _slug_for_url(lemma: str) -> str:
    """URL-safe slug for an atlas lemma.

    Astro's ``[lemma].astro`` dynamic route captures ONE path segment, so a
    slug containing ``/`` would split into multiple segments and break
    routing (caught against ``вчителька / учителька`` 2026-05-22). We
    also fold commas (used as list separators in plan-hint chunks like
    ``він, вона, воно``) and apostrophes (Ukrainian intra-word ``'`` —
    survives in the display lemma but is stripped from the slug).

    Strategy:
      1. casefold + strip surrounding whitespace
      2. replace any non-Cyrillic-letter / non-Latin-letter / non-digit
         character with a hyphen (this folds spaces, slashes, commas,
         apostrophes, parens, etc. — Python's ``\\w`` is Unicode-aware
         and includes Cyrillic letters)
      3. collapse consecutive hyphens and trim leading/trailing ones

    Cyrillic is preserved (Astro handles UTF-8 path segments).
    """
    folded = lemma.strip().casefold()
    # Non-word (Unicode-aware) → hyphen. \w in Python regex is
    # Unicode-aware by default and includes Cyrillic letters + digits +
    # underscore; we strip underscores below to keep slugs clean.
    slug = re.sub(r"[^\w]+", "-", folded, flags=re.UNICODE)
    slug = slug.replace("_", "-")
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def _lemma_key(lemma: str) -> str:
    cleaned = re.sub(r"\s+", " ", lemma.strip())
    cleaned = cleaned.strip(" \t\r\n.,;:!?…")
    normalized = unicodedata.normalize("NFKD", cleaned.casefold())
    normalized = _STRESS_MARK_RE.sub("", normalized)
    return unicodedata.normalize("NFC", normalized)


NON_ATLAS_LEMMA_KEYS = {_lemma_key(lemma) for lemma in _NON_ATLAS_LEMMA_KEYS}
VOCATIVE_TO_NOMINATIVE_BY_KEY = {_lemma_key(source): target for source, target in VOCATIVE_TO_NOMINATIVE.items()}
VESUM_CANONICAL_HEADS_BY_KEY = {
    _lemma_key(source): (target, reason) for source, (target, reason) in VESUM_CANONICAL_HEADS.items()
}


def _load_vesum_inflection_aliases() -> dict[str, str]:
    """Load the committed VESUM inflection→lemma alias map: ``form_key -> target lemma``.

    Generated offline by ``scripts.lexicon.generate_vesum_aliases`` and committed, so the
    build stays deterministic and needs no ``vesum.db`` (CI-safe). A missing/garbled file
    yields no aliases — the build degrades to curated-only normalization.
    """
    try:
        payload = json.loads(VESUM_ALIAS_MAP_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    aliases = payload.get("aliases") if isinstance(payload, dict) else None
    if not isinstance(aliases, dict):
        return {}
    return {
        _lemma_key(form): str(info["lemma"])
        for form, info in aliases.items()
        if isinstance(info, dict) and info.get("lemma")
    }


VESUM_INFLECTION_ALIASES_BY_KEY = _load_vesum_inflection_aliases()


def _course_module_numbers() -> dict[tuple[str, str], int]:
    """Return curriculum-indexed module numbers keyed by ``(track, slug)``."""
    manifest = yaml.safe_load(CURRICULUM_MANIFEST.read_text(encoding="utf-8")) or {}
    levels = manifest.get("levels") or {}
    module_numbers: dict[tuple[str, str], int] = {}
    if not isinstance(levels, dict):
        return module_numbers

    for track, level_data in levels.items():
        if not isinstance(level_data, dict):
            continue
        raw_modules = level_data.get("modules") or []
        if not isinstance(raw_modules, list):
            continue
        for index, raw_slug in enumerate(raw_modules, start=1):
            slug = str(raw_slug).split("#", 1)[0].strip()
            if not slug:
                continue
            if (CURRICULUM_ROOT / str(track) / slug / "vocabulary.yaml").exists():
                module_numbers[(str(track), slug)] = index
    return module_numbers


def _vocabulary_modules() -> list[dict[str, str | int]]:
    """Return every module that has a built ``vocabulary.yaml`` file."""
    indexed_numbers = _course_module_numbers()
    max_index_by_track: dict[str, int] = {}
    for (track, _slug), module_num in indexed_numbers.items():
        max_index_by_track[track] = max(max_index_by_track.get(track, 0), module_num)

    extra_counts_by_track: dict[str, int] = {}
    modules: list[dict[str, str | int]] = []
    for path in sorted(CURRICULUM_ROOT.glob("*/*/vocabulary.yaml")):
        track = path.parent.parent.name
        slug = path.parent.name
        module_num = indexed_numbers.get((track, slug))
        if module_num is None:
            extra_counts_by_track[track] = extra_counts_by_track.get(track, 0) + 1
            module_num = max_index_by_track.get(track, 0) + extra_counts_by_track[track]
        modules.append({"track": track, "module_num": module_num, "slug": slug})
    return modules


def _entry_lemma(entry: dict) -> str | None:
    for field in LEMMA_FIELDS:
        value = entry.get(field)
        if value is not None and str(value).strip():
            return strip_acute_stress(str(value).strip())
    return None


def _load_built_vocab(module: dict[str, str | int]) -> list[dict]:
    """Return list of lemma records from a built ``vocabulary.yaml``."""
    path = CURRICULUM_ROOT / str(module["track"]) / str(module["slug"]) / "vocabulary.yaml"
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    out: list[dict] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        lemma = _entry_lemma(entry)
        if not lemma:
            continue
        out.append(
            {
                "lemma": lemma,
                "gloss": entry.get("translation"),
                "pos": entry.get("pos"),
                "ipa": entry.get("ipa") or None,
                "source": "built_vocabulary",
            }
        )
    return out


_SOURCE_PRIORITY = {
    "built_vocabulary": 0,
    "built_vocabulary_normalized": 1,
    "built_vocabulary_canonicalized": 1,
    "built_vocabulary_form": 1,
    "surzhyk_to_avoid": 1,
    "heritage_status_seed": 2,
}


def _source_priority(source: str) -> int:
    return _SOURCE_PRIORITY.get(source, 99)


def _normalization_record(
    *,
    kind: str,
    source_lemma: str,
    target_lemma: str,
    reason: str,
) -> dict[str, str]:
    return {
        "kind": kind,
        "source_lemma": source_lemma,
        "target_lemma": target_lemma,
        "reason": reason,
    }


def _append_normalization(entry: dict, normalization: dict[str, str] | None) -> None:
    if not normalization:
        return
    normalizations = entry.setdefault("atlas_normalizations", [])
    if normalization not in normalizations:
        normalizations.append(normalization)


_PLURAL_NOUN_SURFACE_HEAD_KEYS = {
    _lemma_key("бризки"),
    _lemma_key("вершки"),
}


def _is_plural_noun_surface_head(rec: dict) -> bool:
    pos = str(rec.get("pos") or "").strip().casefold()
    return pos in {"noun:pl", "noun plural", "plural noun"} and _lemma_key(str(rec.get("lemma") or "")) in (
        _PLURAL_NOUN_SURFACE_HEAD_KEYS
    )


def _atlas_record_for_manifest(rec: dict, taught_lemma_keys: set[str]) -> dict | list[dict] | None:
    """Normalize course surfaces to Atlas lemma heads, or omit non-lemmas."""
    raw_lemma = str(rec["lemma"])
    display_lemma = strip_acute_stress(raw_lemma)
    if display_lemma != raw_lemma:
        rec = {**rec, "lemma": display_lemma}
    key = _lemma_key(display_lemma)
    if key in NON_ATLAS_LEMMA_KEYS:
        return None

    if key in VOCATIVE_TO_NOMINATIVE_BY_KEY:
        target = VOCATIVE_TO_NOMINATIVE_BY_KEY[key]
        if _lemma_key(target) not in taught_lemma_keys:
            return None
        normalized = dict(rec)
        normalized["lemma"] = target
        normalized["source"] = "built_vocabulary_normalized"
        normalized["atlas_normalization"] = _normalization_record(
            kind="vocative_to_nominative",
            source_lemma=display_lemma,
            target_lemma=target,
            reason="Atlas pages are lemma-keyed; course vocative surface maps to taught nominative.",
        )
        return normalized

    if key in VESUM_CANONICAL_HEADS_BY_KEY:
        target, reason = VESUM_CANONICAL_HEADS_BY_KEY[key]
        canonicalized = dict(rec)
        canonicalized["lemma"] = target
        canonicalized["source"] = "built_vocabulary_canonicalized"
        canonicalized["atlas_normalization"] = _normalization_record(
            kind="vesum_canonical_head",
            source_lemma=display_lemma,
            target_lemma=target,
            reason=reason,
        )
        return canonicalized

    # Auto-generated VESUM aliasing: fold an inflected form into its lemma.
    alias_target = VESUM_INFLECTION_ALIASES_BY_KEY.get(key)
    if alias_target:
        if _lemma_key(alias_target) not in taught_lemma_keys and _is_plural_noun_surface_head(rec):
            return dict(rec)
        aliased = dict(rec)
        aliased["lemma"] = alias_target
        aliased["source"] = "built_vocabulary_normalized"
        if _lemma_key(alias_target) not in taught_lemma_keys:
            surface_gloss = aliased.get("gloss")
            surface_pos = aliased.get("pos")
            aliased["gloss"] = None
            aliased["pos"] = None
            reason = (
                f"VESUM: inflected surface «{display_lemma}» "
                f"(surface gloss={surface_gloss!r}, pos={surface_pos!r}) folded into a "
                f"NEWLY-CREATED lemma page «{alias_target}»; surface gloss/pos not asserted on "
                "the citation-form lemma (enrichment supplies the lemma's meaning)."
            )
        else:
            reason = "VESUM: inflected form folded into already-taught lemma."
        aliased["atlas_normalization"] = _normalization_record(
            kind="vesum_inflection_to_lemma",
            source_lemma=display_lemma,
            target_lemma=alias_target,
            reason=reason,
        )

        # If it's a single word, yield a form_of record to preserve the URL and render a canonical card
        if " " not in display_lemma.strip():
            form_rec = dict(rec)
            form_rec["form_of"] = {
                "lemma": alias_target,
                "url_slug": _slug_for_url(alias_target),
            }
            form_rec["source"] = "built_vocabulary_form"
            return [aliased, form_rec]

        return aliased

    return rec


def _merge_lemma_records(
    by_lemma: dict[str, dict],
    module: dict[str, str | int],
    records: list[dict],
) -> None:
    """Fold lemma records from one module into the shared registry.

    Lemmas are merged case-insensitively (key = casefolded form); the
    display ``lemma`` field preserves the first capitalization we see.
    Built-module data wins over plan hints when both are present. Course
    usage is deduped on (track, module_num, slug) — keeping the highest-signal
    context (built > seed/test sources).
    """
    track = str(module["track"])
    module_num = int(module["module_num"])
    slug = str(module["slug"])

    for rec in records:
        display_lemma = strip_acute_stress(str(rec["lemma"]))
        key = _lemma_key(display_lemma)
        usage_entry = {
            "track": track,
            "module_num": module_num,
            "slug": slug,
            "context": rec["source"],
        }
        existing = by_lemma.get(key)
        if existing is None:
            by_lemma[key] = {
                "lemma": display_lemma,
                "url_slug": _slug_for_url(display_lemma),
                "gloss": rec.get("gloss"),
                "pos": rec.get("pos"),
                "ipa": rec.get("ipa"),
                "primary_source": rec["source"],
                "course_usage": [usage_entry],
            }
            if "form_of" in rec:
                by_lemma[key]["form_of"] = rec["form_of"]
            _append_normalization(by_lemma[key], rec.get("atlas_normalization"))
            continue

        # Upgrade thin plan-hint entries when we later see built data.
        is_upgrade = _source_priority(rec["source"]) < _source_priority(existing["primary_source"])
        if is_upgrade:
            existing["lemma"] = display_lemma
            existing["url_slug"] = _slug_for_url(display_lemma)
            existing["primary_source"] = rec["source"]
            if rec.get("gloss"):
                existing["gloss"] = rec["gloss"]
            if rec.get("pos"):
                existing["pos"] = rec["pos"]
            if rec.get("ipa"):
                existing["ipa"] = rec["ipa"]
        if "form_of" in rec and "form_of" not in existing:
            existing["form_of"] = rec["form_of"]
        _append_normalization(existing, rec.get("atlas_normalization"))

        # Dedupe course_usage by module identity, keeping the highest-signal
        # context when a source contributes the same lemma more than once.
        usage_key = (track, module_num, slug)
        for u in existing["course_usage"]:
            if (u["track"], u["module_num"], u["slug"]) == usage_key:
                if _SOURCE_PRIORITY.get(rec["source"], 99) < _SOURCE_PRIORITY.get(u["context"], 99):
                    u["context"] = rec["source"]
                break
        else:
            existing["course_usage"].append(usage_entry)


def _merge_seed_records(by_lemma: dict[str, dict]) -> None:
    for rec in SURZHYK_TO_AVOID_SEEDS:
        display_lemma = strip_acute_stress(str(rec["lemma"]))
        key = _lemma_key(display_lemma)
        if key in by_lemma:
            by_lemma[key]["seed_group"] = "surzhyk-to-avoid"
            continue
        by_lemma[key] = {
            "lemma": display_lemma,
            "url_slug": _slug_for_url(display_lemma),
            "gloss": rec.get("gloss"),
            "pos": rec.get("pos"),
            "ipa": None,
            "primary_source": "surzhyk_to_avoid",
            "seed_group": "surzhyk-to-avoid",
            "course_usage": [],
        }


def _merge_heritage_seed_records(by_lemma: dict[str, dict]) -> None:
    for rec in HERITAGE_STATUS_SEEDS:
        display_lemma = strip_acute_stress(str(rec["lemma"]))
        key = _lemma_key(display_lemma)
        if key in by_lemma:
            by_lemma[key]["seed_group"] = "heritage-status-samples"
            continue
        by_lemma[key] = {
            "lemma": display_lemma,
            "url_slug": _slug_for_url(display_lemma),
            "gloss": rec.get("gloss"),
            "pos": rec.get("pos"),
            "ipa": None,
            "primary_source": "heritage_status_seed",
            "seed_group": "heritage-status-samples",
            "course_usage": [],
        }


def _resolve_slug_collisions(by_lemma: dict[str, dict]) -> None:
    """Guarantee ``url_slug`` uniqueness by folding entries that collide.

    Two distinct lemmas can yield the same slug when they differ only by
    characters ``_slug_for_url`` deliberately folds (commas, spaces, slashes,
    apostrophes) — e.g. ``тому що`` vs ``тому, що`` and ``через те що`` vs
    ``через те, що``, added as separate entries by the §6 calque-correction
    layer (#3098). Astro's ``[lemma].astro`` route keys on the slug, so a
    collision would make two lemmas resolve to one page; ``build_manifest``
    must enforce the invariant ``test_manifest_url_slugs_are_unique`` checks.

    Colliding entries are folded into one deterministic canonical
    (no interior punctuation > highest source priority > shortest lemma >
    alphabetical), merging ``course_usage`` (deduped by module identity) and
    ``atlas_normalizations``, backfilling missing optional fields, and recording
    the folded surface form(s) under ``slug_variants``.
    """
    by_slug: dict[str, list[str]] = {}
    for key, entry in by_lemma.items():
        by_slug.setdefault(entry["url_slug"], []).append(key)

    for collision_keys in by_slug.values():
        if len(collision_keys) < 2:
            continue

        def _rank(k: str) -> tuple:
            e = by_lemma[k]
            has_interior_punct = bool(re.search(r"[^\w\s]", e["lemma"], re.UNICODE))
            return (
                has_interior_punct,
                _source_priority(e["primary_source"]),
                len(e["lemma"]),
                e["lemma"],
            )

        canonical_key, *folded_keys = sorted(collision_keys, key=_rank)
        canonical = by_lemma[canonical_key]
        for fold_key in folded_keys:
            other = by_lemma.pop(fold_key)
            for u in other.get("course_usage", []):
                usage_id = (u["track"], u["module_num"], u["slug"])
                if not any((x["track"], x["module_num"], x["slug"]) == usage_id for x in canonical["course_usage"]):
                    canonical["course_usage"].append(u)
            for norm in other.get("atlas_normalizations", []):
                _append_normalization(canonical, norm)
            for field in ("gloss", "pos", "ipa"):
                if not canonical.get(field) and other.get(field):
                    canonical[field] = other[field]
            if "seed_group" in other and "seed_group" not in canonical:
                canonical["seed_group"] = other["seed_group"]
            variants = canonical.setdefault("slug_variants", [])
            if other["lemma"] != canonical["lemma"] and other["lemma"] not in variants:
                variants.append(other["lemma"])


def build_manifest() -> dict:
    """Build the manifest dict and return it (caller writes to disk)."""
    by_lemma: dict[str, dict] = {}
    modules = _vocabulary_modules()
    raw_records_by_module = [(module, _load_built_vocab(module)) for module in modules]
    taught_lemma_keys = {_lemma_key(rec["lemma"]) for _module, records in raw_records_by_module for rec in records}

    for module, raw_records in raw_records_by_module:
        built_records = []
        for rec in raw_records:
            res = _atlas_record_for_manifest(rec, taught_lemma_keys)
            if res:
                if isinstance(res, list):
                    built_records.extend(res)
                else:
                    built_records.append(res)
        _merge_lemma_records(by_lemma, module, built_records)

    _merge_seed_records(by_lemma)
    _merge_heritage_seed_records(by_lemma)
    _resolve_slug_collisions(by_lemma)

    entries = sorted(by_lemma.values(), key=lambda e: e["lemma"])
    return {
        "version": "0.1",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "stats": {
            "lemmas_total": len(entries),
            "modules_covered": len(modules),
            "from_built": sum(1 for e in entries if e["primary_source"].startswith("built_vocabulary")),
            "from_surzhyk_to_avoid": sum(1 for e in entries if e.get("seed_group") == "surzhyk-to-avoid"),
            "from_heritage_status_seed": sum(1 for e in entries if e.get("seed_group") == "heritage-status-samples"),
            "form_of_count": sum(1 for e in entries if "form_of" in e),
        },
        "modules": modules,
        "seed_groups": [
            {
                "id": "surzhyk-to-avoid",
                "source": "surzhyk_to_avoid",
                "description": "Classifier-verified Russianism/surzhyk examples for visible Atlas warnings.",
                "lemmas": [str(seed["lemma"]) for seed in SURZHYK_TO_AVOID_SEEDS],
            },
            {
                "id": "heritage-status-samples",
                "source": "heritage_status_seed",
                "description": "Source-backed heritage status sample pages for Atlas design conformance QA.",
                "lemmas": [str(seed["lemma"]) for seed in HERITAGE_STATUS_SEEDS],
            },
        ],
        "entries": entries,
    }


def build_parser() -> argparse.ArgumentParser:
    """CLI parser for build_data_manifest (``#5393`` argv guard)."""
    return argparse.ArgumentParser(
        description=(
            "Build the Word Atlas bare lemma lexicon-manifest.json from curriculum vocabulary. "
            "Use when rebuilding the Atlas index from taught vocab; "
            "do NOT use for flag probes — bare invocation must not rewrite the manifest."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  # Print usage without touching any files\n"
            "  .venv/bin/python scripts/lexicon/build_data_manifest.py --help\n\n"
            "  # Build and write the bare lemma manifest\n"
            "  .venv/bin/python scripts/lexicon/build_data_manifest.py --write\n\n"
            "Outputs (only with --write):\n"
            "  site/src/data/lexicon-manifest.json  — bare lemma + course-usage index\n\n"
            "Exit codes:\n"
            "  0  success (--help or successful --write)\n"
            "  2  refused (no --write) or argparse error\n\n"
            "Related:\n"
            "  scripts/lexicon/enrich_manifest.py  — layer dictionary enrichment after build\n"
            "  issue #5393                        — argv guard sibling"
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI args and write the bare manifest only when ``--write`` is given."""
    parser = build_parser()
    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Write site/src/data/lexicon-manifest.json. "
            "Default: refuse with usage and exit non-zero (no files touched)."
        ),
    )
    args = parser.parse_args(argv)
    if not args.write:
        parser.error(
            "refusing to build/write the lexicon manifest without --write "
            "(writes site/src/data/lexicon-manifest.json; pass --write to proceed)"
        )

    manifest = build_manifest()
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    stats = manifest["stats"]
    print(
        f"Wrote {MANIFEST_PATH.relative_to(PROJECT_ROOT)}: "
        f"{stats['lemmas_total']} lemmas across {stats['modules_covered']} modules "
        f"(built={stats['from_built']}, seeds={stats['from_surzhyk_to_avoid'] + stats['from_heritage_status_seed']})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

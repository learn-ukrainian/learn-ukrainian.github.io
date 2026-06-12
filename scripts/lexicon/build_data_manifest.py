"""Build the Word Atlas (Лексикон) data manifest for Starlight static rendering.

Input source:
  every ``curriculum/l2-uk-en/{level}/{slug}/vocabulary.yaml`` file. Entries
  may name the Ukrainian headword as ``lemma``, ``word``, ``uk``, or ``term``;
  A1 uses ``lemma`` while A2 uses ``word``.

Output: ``starlight/src/data/lexicon-manifest.json`` — versioned JSON the
Astro dynamic route at ``src/pages/lexicon/[lemma].astro`` reads at build time
to materialize one static page per lemma.

The builder stays thin: lemma + course-usage + (when available) translation,
POS, and IPA. Per design §4, additional sections (etymology, definitions,
heritage status, paradigm, etc.) are layered on by enrichment.

Reproducer (run from repo root):

    .venv/bin/python -m scripts.lexicon.build_data_manifest

Writes ``starlight/src/data/lexicon-manifest.json`` and prints stats.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
CURRICULUM_MANIFEST = CURRICULUM_ROOT / "curriculum.yaml"
MANIFEST_PATH = PROJECT_ROOT / "starlight" / "src" / "data" / "lexicon-manifest.json"
_STRESS_MARK_RE = re.compile("[\u0300\u0301]")


LEMMA_FIELDS = ("lemma", "word", "uk", "term")

SURZHYK_TO_AVOID_SEEDS: list[dict[str, str | None]] = [
    {"lemma": "агенство", "gloss": "avoid: агенція", "pos": "noun"},
    {"lemma": "авось", "gloss": "avoid: ану ж / а може", "pos": "adv"},
    {"lemma": "автозагар", "gloss": "avoid: автозасмага", "pos": "noun"},
    {"lemma": "всьо", "gloss": "avoid: все", "pos": "pron"},
    {"lemma": "діюча", "gloss": "avoid: чинна", "pos": "adj"},
    {"lemma": "міроприємство", "gloss": "avoid: захід", "pos": "noun"},
    {"lemma": "протиріччя", "gloss": "avoid: суперечність", "pos": "noun"},
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
            return str(value).strip()
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
    "surzhyk_to_avoid": 1,
    "heritage_status_seed": 2,
}


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
        display_lemma = rec["lemma"]
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
            continue

        # Upgrade thin plan-hint entries when we later see built data.
        is_upgrade = (
            existing["primary_source"].startswith("plan_")
            and rec["source"] == "built_vocabulary"
        )
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

        # Dedupe course_usage by module identity, keeping the highest-signal
        # context when a source contributes the same lemma more than once.
        usage_key = (track, module_num, slug)
        for u in existing["course_usage"]:
            if (u["track"], u["module_num"], u["slug"]) == usage_key:
                if _SOURCE_PRIORITY.get(rec["source"], 99) < _SOURCE_PRIORITY.get(
                    u["context"], 99
                ):
                    u["context"] = rec["source"]
                break
        else:
            existing["course_usage"].append(usage_entry)


def _merge_seed_records(by_lemma: dict[str, dict]) -> None:
    for rec in SURZHYK_TO_AVOID_SEEDS:
        display_lemma = str(rec["lemma"])
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
        display_lemma = str(rec["lemma"])
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


def build_manifest() -> dict:
    """Build the manifest dict and return it (caller writes to disk)."""
    by_lemma: dict[str, dict] = {}
    modules = _vocabulary_modules()

    for module in modules:
        built_records = _load_built_vocab(module)
        _merge_lemma_records(by_lemma, module, built_records)

    _merge_seed_records(by_lemma)
    _merge_heritage_seed_records(by_lemma)

    entries = sorted(by_lemma.values(), key=lambda e: e["lemma"])
    return {
        "version": "0.1",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "stats": {
            "lemmas_total": len(entries),
            "modules_covered": len(modules),
            "from_built": sum(
                1 for e in entries if e["primary_source"] == "built_vocabulary"
            ),
            "from_surzhyk_to_avoid": sum(
                1 for e in entries if e["primary_source"] == "surzhyk_to_avoid"
            ),
            "from_heritage_status_seed": sum(
                1 for e in entries if e["primary_source"] == "heritage_status_seed"
            ),
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
            }
        ],
        "entries": entries,
    }


def main() -> None:
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


if __name__ == "__main__":
    main()

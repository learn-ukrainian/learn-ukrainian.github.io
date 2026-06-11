"""Build the Word Atlas (Лексикон) data manifest for Starlight static rendering.

V1 scope (per docs/best-practices/word-atlas-design.md §9):
  Render lemmas referenced by a1/my-morning (built) + a1/sounds-letters-and-hello
  (plan-only) + a1/things-have-gender (plan-only). ~80 lemmas total.

Input sources, in precedence order:
  1. ``curriculum/l2-uk-en/{level}/{slug}/vocabulary.yaml`` — built modules.
     Each entry: ``{lemma, translation, pos, ipa, usage}``.
  2. ``curriculum/l2-uk-en/plans/{level}/{slug}.yaml`` — plans for not-yet-built
     modules. Reads ``vocabulary_hints.required`` and
     ``vocabulary_hints.recommended``; each entry is a ``"lemma (gloss)"``
     string that we split.

Output: ``starlight/src/data/lexicon-manifest.json`` — versioned JSON the
Astro dynamic route at ``src/pages/lexicon/[lemma].astro`` reads at build time
to materialize one static page per lemma.

V1 deliberately ships THIN: lemma + course-usage + (when available) translation
and POS. Per design §4, additional sections (etymology, definitions,
sovietization badge, heritage status, paradigm, etc.) are layered on by
later phases of the build pipeline. Keeping this thin makes the route
land first; enrichment is purely additive to the manifest.

Reproducer (run from repo root):

    .venv/bin/python -m scripts.lexicon.build_data_manifest

Writes ``starlight/src/data/lexicon-manifest.json`` and prints stats.
"""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from argparse import ArgumentParser, Namespace
from datetime import UTC, datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
PLANS_ROOT = CURRICULUM_ROOT / "plans"
MANIFEST_PATH = PROJECT_ROOT / "starlight" / "src" / "data" / "lexicon-manifest.json"
V2_SPIKE_MANIFEST_PATH = PROJECT_ROOT / "starlight" / "src" / "data" / "lexicon-manifest.v2-spike.json"
SOURCES_DB = PROJECT_ROOT / "data" / "sources.db"

V2_SPIKE_LEVELS = ("a1", "a2", "b1")
PULS_CEFR_LEVELS = ("A1", "A2", "B1")
APOSTROPHE_TRANSLATION = str.maketrans({"’": "'", "ʼ": "'", "`": "'", "′": "'"})
STRESS_MARKS = {"\u0301", "\u0300", "\u0341"}
WORD_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЄєІіЇїҐґ0-9'’ʼ-]+")


# v1 module set — per design §9.
V1_MODULES: list[dict[str, str | int]] = [
    {"track": "a1", "module_num": 1, "slug": "sounds-letters-and-hello"},
    {"track": "a1", "module_num": 8, "slug": "things-have-gender"},
    {"track": "a1", "module_num": 20, "slug": "my-morning"},
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


def _strip_stress(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(char for char in decomposed if char not in STRESS_MARKS)
    return unicodedata.normalize("NFC", stripped)


def _normalize_lookup_text(value: object) -> str:
    cleaned = unicodedata.normalize("NFKC", str(value or "")).translate(APOSTROPHE_TRANSLATION)
    cleaned = _strip_stress(cleaned).casefold()
    return re.sub(r"\s+", " ", cleaned).strip()


def _is_multi_word_phrase(value: object) -> bool:
    text = str(value or "").strip()
    return bool(re.search(r"\s", text)) and len(WORD_TOKEN_RE.findall(text)) >= 2


def _parse_plan_hint(raw: str) -> tuple[str, str | None]:
    """Plan hints look like ``"звук (sound)"`` or sometimes just ``"звук"``.

    Returns (lemma, gloss_or_None). Gloss is anything inside the FIRST
    parens; later parenthetical asides are kept inside the lemma string
    (rare, but defensible — multi-paren entries are usually compound notes).
    """
    raw = raw.strip()
    m = re.match(r"^(.+?)\s*\(([^()]+)\)\s*$", raw)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return raw, None


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
        lemma = entry.get("lemma")
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


def _load_plan_hints(module: dict[str, str | int]) -> list[dict]:
    """Return list of lemma records from a plan's ``vocabulary_hints``."""
    path = PLANS_ROOT / str(module["track"]) / f"{module['slug']}.yaml"
    if not path.exists():
        return []
    plan = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    hints = plan.get("vocabulary_hints") or {}
    if not isinstance(hints, dict):
        return []
    out: list[dict] = []
    for bucket_name in ("required", "recommended"):
        for entry in hints.get(bucket_name) or []:
            if not isinstance(entry, str):
                continue
            lemma, gloss = _parse_plan_hint(entry)
            if not lemma:
                continue
            out.append(
                {
                    "lemma": lemma,
                    "gloss": gloss,
                    "pos": None,
                    "ipa": None,
                    "source": f"plan_{bucket_name}",
                }
            )
    return out


def _load_curriculum_modules(levels: tuple[str, ...] = V2_SPIKE_LEVELS) -> list[dict[str, str | int]]:
    """Enumerate level modules from curriculum.yaml, falling back to plan globs."""
    curriculum = yaml.safe_load((CURRICULUM_ROOT / "curriculum.yaml").read_text(encoding="utf-8")) or {}
    level_data = curriculum.get("levels") if isinstance(curriculum, dict) else {}
    modules: list[dict[str, str | int]] = []

    for level in levels:
        raw_modules = []
        if isinstance(level_data, dict):
            current = level_data.get(level) or {}
            if isinstance(current, dict) and isinstance(current.get("modules"), list):
                raw_modules = current["modules"]

        if raw_modules:
            for index, item in enumerate(raw_modules, start=1):
                slug = item if isinstance(item, str) else item.get("slug") if isinstance(item, dict) else None
                if slug:
                    modules.append({"track": level, "module_num": index, "slug": str(slug)})
            continue

        modules.extend(_load_modules_from_plan_glob(level))

    return modules


def _load_modules_from_plan_glob(level: str) -> list[dict[str, str | int]]:
    """Fallback module enumeration when curriculum.yaml omits a level."""
    modules: list[dict[str, str | int]] = []
    for index, path in enumerate(sorted((PLANS_ROOT / level).glob("*.yaml")), start=1):
        plan = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        slug = plan.get("slug") if isinstance(plan, dict) else None
        sequence = plan.get("sequence") if isinstance(plan, dict) else None
        modules.append(
            {
                "track": level,
                "module_num": int(sequence) if isinstance(sequence, int) else index,
                "slug": str(slug or path.stem),
            }
        )
    return sorted(modules, key=lambda module: int(module["module_num"]))


def _load_puls_cefr_lemmas(levels: tuple[str, ...] = PULS_CEFR_LEVELS) -> set[str]:
    """Return normalized single-word PULS CEFR lemmas for the requested levels."""
    if not SOURCES_DB.exists():
        raise FileNotFoundError(f"local sources database not found: {SOURCES_DB}")

    placeholders = ",".join("?" for _ in levels)
    conn = sqlite3.connect(f"file:{SOURCES_DB}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            f"SELECT word FROM puls_cefr WHERE level IN ({placeholders})",
            levels,
        )
        return {
            normalized
            for (word,) in rows
            if (normalized := _normalize_lookup_text(word)) and not _is_multi_word_phrase(word)
        }
    finally:
        conn.close()


_SOURCE_PRIORITY = {
    "built_vocabulary": 0,
    "plan_required": 1,
    "plan_recommended": 2,
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
    usage is deduped on (track, module_num) — keeping the highest-signal
    context (built > plan_required > plan_recommended).
    """
    track = str(module["track"])
    module_num = int(module["module_num"])
    slug = str(module["slug"])

    for rec in records:
        display_lemma = rec["lemma"]
        key = display_lemma.casefold()
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
            existing["primary_source"] = rec["source"]
            if rec.get("gloss"):
                existing["gloss"] = rec["gloss"]
            if rec.get("pos"):
                existing["pos"] = rec["pos"]
            if rec.get("ipa"):
                existing["ipa"] = rec["ipa"]

        # Dedupe course_usage: collapse same (track, module_num) tuples,
        # keeping the highest-signal context. This avoids "module appears
        # twice" when a lemma is in both the plan AND the built vocab.
        usage_key = (track, module_num)
        for u in existing["course_usage"]:
            if (u["track"], u["module_num"]) == usage_key:
                if _SOURCE_PRIORITY.get(rec["source"], 99) < _SOURCE_PRIORITY.get(
                    u["context"], 99
                ):
                    u["context"] = rec["source"]
                break
        else:
            existing["course_usage"].append(usage_entry)


def _build_entries(modules: list[dict[str, str | int]]) -> list[dict]:
    by_lemma: dict[str, dict] = {}

    for module in modules:
        # Built data has higher signal — prefer it when both are available.
        # We still load plan hints first to seed empty modules; built records
        # then upgrade entries that already exist.
        plan_records = _load_plan_hints(module)
        built_records = _load_built_vocab(module)
        _merge_lemma_records(by_lemma, module, plan_records)
        _merge_lemma_records(by_lemma, module, built_records)

    return sorted(by_lemma.values(), key=lambda e: e["lemma"])


def _source_stats(entries: list[dict]) -> dict[str, int]:
    return {
        "from_built": sum(1 for e in entries if e["primary_source"] == "built_vocabulary"),
        "from_plan_only": sum(1 for e in entries if e["primary_source"].startswith("plan_")),
    }


def _build_v1_manifest() -> dict:
    entries = _build_entries(V1_MODULES)
    source_stats = _source_stats(entries)
    return {
        "version": "0.1",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "stats": {
            "lemmas_total": len(entries),
            "modules_covered": len(V1_MODULES),
            "from_built": source_stats["from_built"],
            "from_plan_only": source_stats["from_plan_only"],
        },
        "modules": V1_MODULES,
        "entries": entries,
    }


def _build_v2_spike_manifest() -> dict:
    modules = _load_curriculum_modules()
    candidate_entries = _build_entries(modules)
    puls_lemmas = _load_puls_cefr_lemmas()

    entries: list[dict] = []
    dropped_multi_word = 0
    dropped_not_in_puls = 0
    for entry in candidate_entries:
        lemma = entry["lemma"]
        if _is_multi_word_phrase(lemma):
            dropped_multi_word += 1
            continue
        if _normalize_lookup_text(lemma) not in puls_lemmas:
            dropped_not_in_puls += 1
            continue
        entries.append(entry)

    source_stats = _source_stats(entries)
    return {
        "version": "0.1-v2-spike",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "stats": {
            "lemmas_total": len(entries),
            "modules_covered": len(modules),
            "candidate_lemmas": len(candidate_entries),
            "from_built": source_stats["from_built"],
            "from_plan": source_stats["from_plan_only"],
            "dropped_multi_word": dropped_multi_word,
            "dropped_not_in_puls": dropped_not_in_puls,
        },
        "modules": modules,
        "entries": entries,
    }


def build_manifest(scope: str = "v1") -> dict:
    """Build the manifest dict and return it (caller writes to disk)."""
    if scope == "v1":
        return _build_v1_manifest()
    if scope == "v2-spike":
        return _build_v2_spike_manifest()
    raise ValueError(f"unknown scope: {scope}")


def _manifest_path(scope: str) -> Path:
    return V2_SPIKE_MANIFEST_PATH if scope == "v2-spike" else MANIFEST_PATH


def _parse_args() -> Namespace:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scope",
        choices=("v1", "v2-spike"),
        default="v1",
        help="Manifest scope to build. Defaults to the production v1 subset.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    manifest = build_manifest(args.scope)
    manifest_path = _manifest_path(args.scope)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    stats = manifest["stats"]
    if args.scope == "v2-spike":
        print(
            f"Wrote {manifest_path.relative_to(PROJECT_ROOT)}: "
            f"{stats['lemmas_total']} lemmas across {stats['modules_covered']} modules "
            f"(from_built={stats['from_built']}, from_plan={stats['from_plan']}, "
            f"dropped_not_in_puls={stats['dropped_not_in_puls']}, "
            f"dropped_multi_word={stats['dropped_multi_word']})."
        )
        return

    print(
        f"Wrote {manifest_path.relative_to(PROJECT_ROOT)}: "
        f"{stats['lemmas_total']} lemmas across {stats['modules_covered']} modules "
        f"(built={stats['from_built']}, plan_only={stats['from_plan_only']})."
    )


if __name__ == "__main__":
    main()

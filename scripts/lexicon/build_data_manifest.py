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
from datetime import UTC, datetime, timezone
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRICULUM_ROOT = PROJECT_ROOT / "curriculum" / "l2-uk-en"
PLANS_ROOT = CURRICULUM_ROOT / "plans"
MANIFEST_PATH = PROJECT_ROOT / "starlight" / "src" / "data" / "lexicon-manifest.json"


# v1 module set — per design §9.
V1_MODULES: list[dict[str, str | int]] = [
    {"track": "a1", "module_num": 1, "slug": "sounds-letters-and-hello"},
    {"track": "a1", "module_num": 8, "slug": "things-have-gender"},
    {"track": "a1", "module_num": 20, "slug": "my-morning"},
]


def _slug_for_url(lemma: str) -> str:
    """URL-safe slug for an atlas lemma.

    Keeps Cyrillic (Astro handles UTF-8 in dynamic routes fine), but strips
    whitespace and lowercases. Multi-word lemmas (e.g. ``після цього``) get
    spaces replaced with hyphens.
    """
    return re.sub(r"\s+", "-", lemma.strip().lower())


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


def build_manifest() -> dict:
    """Build the manifest dict and return it (caller writes to disk)."""
    by_lemma: dict[str, dict] = {}

    for module in V1_MODULES:
        # Built data has higher signal — prefer it when both are available.
        # We still load plan hints first to seed empty modules; built records
        # then upgrade entries that already exist.
        plan_records = _load_plan_hints(module)
        built_records = _load_built_vocab(module)
        _merge_lemma_records(by_lemma, module, plan_records)
        _merge_lemma_records(by_lemma, module, built_records)

    entries = sorted(by_lemma.values(), key=lambda e: e["lemma"])
    return {
        "version": "0.1",
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "stats": {
            "lemmas_total": len(entries),
            "modules_covered": len(V1_MODULES),
            "from_built": sum(
                1 for e in entries if e["primary_source"] == "built_vocabulary"
            ),
            "from_plan_only": sum(
                1 for e in entries if e["primary_source"].startswith("plan_")
            ),
        },
        "modules": V1_MODULES,
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
        f"(built={stats['from_built']}, plan_only={stats['from_plan_only']})."
    )


if __name__ == "__main__":
    main()

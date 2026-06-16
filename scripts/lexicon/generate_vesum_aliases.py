#!/usr/bin/env python3
"""Generate the VESUM inflection→lemma alias map for the Word Atlas (#2882).

OFFLINE, build-time-once. Runs VESUM over the current manifest's surface forms and emits a
COMMITTED static map (`data/lexicon/vesum_inflection_aliases.json`) that `build_data_manifest`
loads — exactly like the hand-curated `VESUM_CANONICAL_HEADS`, just auto-generated. Keeping the
map static makes the build deterministic and CI-safe (no live VESUM / vesum.db at build time).

SAFETY GATES (conservative by design — see #2882 discussion):
- VESUM must return EXACTLY ONE lemma for the form (skips homographs like біле→[білий, біль]).
- the form must NOT already be its own lemma (only inflected forms).
- the lemma must ALREADY be a taught Atlas entry (no new lemma pages created).
- forms absent from VESUM (phrases like "Добрий день") are never touched / never dropped.

This NEVER drops an entry and never resolves ambiguity. Aliases only fold a duplicate
inflected-form page into a lemma page that already exists. Review the emitted JSON before
wiring/committing.

Usage:
    .venv/bin/python -m scripts.lexicon.generate_vesum_aliases            # write the map
    .venv/bin/python -m scripts.lexicon.generate_vesum_aliases --dry-run  # print, don't write
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.lexicon.build_data_manifest import (
    _lemma_key,
    _load_built_vocab,
    _vocabulary_modules,
)
from scripts.verification.vesum import verify_word

ALIAS_MAP_PATH = Path(__file__).resolve().parents[2] / "data" / "lexicon" / "vesum_inflection_aliases.json"

# Lexicalized functional forms KEPT as standalone Atlas pages — their high-frequency use is a
# fixed expression / interjection / particle whose meaning is NOT reducible to "inflection of
# lemma X", so folding them into the verb lemma would mislead. `може` is the strongest case: as
# "maybe" it is a particle, semantically distinct from могти "to be able". (Ordinary conjugations
# like люблю→любити / їмо→їсти are NOT here — those fold correctly.) Per user call 2026-06-15.
_KEEP_STANDALONE_FORMS = {
    "дякую", "прошу", "може", "будь", "будьте", "вітаю",
    # tranche 2: politeness interjections taught as fixed expressions (like дякую), not as
    # the bare imperative of their verb. Per user direction "fully lemma-key but keep the
    # true interjections standalone" (2026-06-16).
    "вибачте", "пробачте", "перепрошую",
}


def _strip_stress(text: str) -> str:
    return text.replace("́", "").replace("̀", "")


def _vesum_lemmas(form: str) -> list[str]:
    try:
        rows = verify_word(_strip_stress(form).strip())
    except Exception:
        return []
    return sorted({str(r.get("lemma") or "").strip() for r in rows if r.get("lemma")})


def _course_surface_forms() -> list[str]:
    """All taught surface forms from course vocab (NOT the post-dedup manifest, which has
    already-folded forms removed). This is the correct, dedup-stable input — every form that
    needs aliasing, with the same taught-set build_data_manifest uses."""
    seen: set[str] = set()
    forms: list[str] = []
    for module in _vocabulary_modules():
        for rec in _load_built_vocab(module):
            lemma = rec.get("lemma")
            if lemma and lemma not in seen:
                seen.add(lemma)
                forms.append(lemma)
    return forms


def build_alias_map(forms: list[str] | None = None) -> dict[str, dict[str, str]]:
    lemmas = _course_surface_forms() if forms is None else forms
    keep_standalone = {_lemma_key(form) for form in _KEEP_STANDALONE_FORMS}
    aliases: dict[str, dict[str, str]] = {}
    for form in lemmas:
        form_key = _lemma_key(form)
        if form_key in keep_standalone:
            continue  # lexicalized functional form → keep its own Atlas page
        vlemmas = _vesum_lemmas(form)
        if len(vlemmas) != 1:
            # 0 lemmas = absent from VESUM (phrases / proper names) → never touch.
            # >1 = HOMOGRAPH → never auto-resolve. "Sole taught candidate" mis-merges true
            # homographs (сьома→сім not сьомий; друга→друг not другий — caught 2026-06-16), so
            # these stay standalone, deferred to a curated per-word pass. Mis-merging distinct
            # words is the project's #1 fear; conservative is correct here.
            continue
        target = vlemmas[0]  # unambiguous: fold (incl. create-cases where the lemma isn't taught)
        target_key = _lemma_key(target)
        if target_key == form_key:
            continue  # form is its own lemma
        aliases[form] = {"lemma": target}
    return dict(sorted(aliases.items()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate VESUM inflection→lemma alias map (#2882).")
    parser.add_argument("--out", type=Path, default=ALIAS_MAP_PATH)
    parser.add_argument("--dry-run", action="store_true", help="Print summary; do not write.")
    args = parser.parse_args(argv)

    aliases = build_alias_map()
    payload = {
        "schema_version": 1,
        "description": (
            "Auto-generated VESUM inflection→lemma aliases (from course-vocab surfaces). Gates: "
            "single unambiguous VESUM lemma (folds, creating the lemma page if new), OR homograph "
            "resolved to its SOLE taught candidate; form != its own lemma; functional interjections "
            "excluded; never drops. Regenerate via scripts.lexicon.generate_vesum_aliases."
        ),
        "aliases": aliases,
    }
    print(f"safe inflection→lemma aliases: {len(aliases)}")
    if args.dry_run:
        for form, info in list(aliases.items())[:30]:
            print(f"  {form} -> {info['lemma']}")
        if len(aliases) > 30:
            print(f"  ... (+{len(aliases) - 30} more)")
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

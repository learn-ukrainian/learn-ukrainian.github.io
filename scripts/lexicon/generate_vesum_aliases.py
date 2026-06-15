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

from scripts.lexicon.build_data_manifest import MANIFEST_PATH, _lemma_key
from scripts.verification.vesum import verify_word

ALIAS_MAP_PATH = Path(__file__).resolve().parents[2] / "data" / "lexicon" / "vesum_inflection_aliases.json"


def _strip_stress(text: str) -> str:
    return text.replace("́", "").replace("̀", "")


def _vesum_lemmas(form: str) -> list[str]:
    try:
        rows = verify_word(_strip_stress(form).strip())
    except Exception:
        return []
    return sorted({str(r.get("lemma") or "").strip() for r in rows if r.get("lemma")})


def _manifest_lemmas(manifest_path: Path) -> list[str]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return [e["lemma"] for e in manifest.get("entries", []) if e.get("lemma")]


def build_alias_map(manifest_path: Path = MANIFEST_PATH) -> dict[str, dict[str, str]]:
    lemmas = _manifest_lemmas(manifest_path)
    taught = {_lemma_key(lemma) for lemma in lemmas}
    aliases: dict[str, dict[str, str]] = {}
    for form in lemmas:
        vlemmas = _vesum_lemmas(form)
        if len(vlemmas) != 1:
            continue  # ambiguous (>1) or absent from VESUM (0) → leave alone
        target = vlemmas[0]
        target_key = _lemma_key(target)
        form_key = _lemma_key(form)
        if target_key == form_key:
            continue  # form is its own lemma
        if target_key not in taught:
            continue  # would create a new lemma page → defer to curated human pass
        aliases[form] = {"lemma": target}
    return dict(sorted(aliases.items()))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate VESUM inflection→lemma alias map (#2882).")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--out", type=Path, default=ALIAS_MAP_PATH)
    parser.add_argument("--dry-run", action="store_true", help="Print summary; do not write.")
    args = parser.parse_args(argv)

    aliases = build_alias_map(args.manifest)
    payload = {
        "schema_version": 1,
        "description": (
            "Auto-generated VESUM inflection→lemma aliases. Gates: single unambiguous VESUM "
            "lemma; form is not its own lemma; target lemma already taught. Never drops; never "
            "resolves homographs. Regenerate via scripts.lexicon.generate_vesum_aliases."
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

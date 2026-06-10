"""Append a cited slovnyk.me folk attestation for the VESUM fallback.

Example:
    .venv/bin/python scripts/build/add_folk_attestation.py риндзівка \
        --citation newsum=https://slovnyk.me/dict/newsum/... \
        --gloss "етн. старовинна українська величальна пісня" \
        --surface риндзівки
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ATTESTATIONS_PATH = PROJECT_ROOT / "data" / "folk_heritage_attestations.yaml"


def _parse_citation(value: str) -> dict[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("citation must be DICTIONARY_SLUG=URL")
    dictionary_slug, url = value.split("=", 1)
    dictionary_slug = dictionary_slug.strip()
    url = url.strip()
    if not dictionary_slug:
        raise argparse.ArgumentTypeError("citation dictionary slug is required")
    if not url.startswith("https://slovnyk.me/dict/"):
        raise argparse.ArgumentTypeError("citation URL must start with https://slovnyk.me/dict/")
    return {"dictionary_slug": dictionary_slug, "url": url}


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"attestations": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    rows = data.setdefault("attestations", [])
    if not isinstance(rows, list):
        raise ValueError(f"{path} field 'attestations' must be a list")
    return data


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lemma", help="singular slovnyk.me headword")
    parser.add_argument(
        "--citation",
        action="append",
        required=True,
        type=_parse_citation,
        metavar="DICTIONARY_SLUG=URL",
        help="slovnyk.me citation; repeat for multiple dictionaries",
    )
    parser.add_argument("--gloss", required=True, help="short dictionary gloss")
    parser.add_argument(
        "--surface",
        action="append",
        default=[],
        help="additional exact surface accepted by the cited lemma row",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=ATTESTATIONS_PATH,
        help="attestation YAML path",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    lemma = args.lemma.strip()
    if not lemma:
        raise SystemExit("lemma is required")

    data = _load(args.path)
    rows = data["attestations"]
    if any(isinstance(row, dict) and row.get("lemma") == lemma for row in rows):
        raise SystemExit(f"lemma already exists: {lemma}")

    accepted_surfaces = []
    for surface in [lemma, *args.surface]:
        surface = surface.strip()
        if surface and surface not in accepted_surfaces:
            accepted_surfaces.append(surface)

    rows.append(
        {
            "lemma": lemma,
            "is_russianism": False,
            "citations": args.citation,
            "gloss": args.gloss.strip(),
            "accepted_surfaces": accepted_surfaces,
        }
    )
    args.path.write_text(
        yaml.safe_dump(data, allow_unicode=True, explicit_start=True, sort_keys=False),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

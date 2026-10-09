"""Generate the seat and review-ladder reference from the live catalog (#8512)."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scripts.lint.lint_fleet_roster import SEAT_FIELDS, load_orchestrator_seats
from scripts.review.role_resolution import resolve_routing_reference

ROOT = Path(__file__).resolve().parents[5]
CATALOG = ROOT / "scripts/config/model_catalog.yaml"
OUTPUT = ROOT / "agents_extensions/shared/rules/catalog-routing-tables.md"


def active_model(model: str, catalog: dict) -> str:
    """Refuse a missing or retired identity rather than publish a default."""
    entry = catalog["models"].get(model)
    if entry is None or entry.get("lifecycle", "active") != "active":
        raise ValueError(f"non-active catalog model: {model}")
    return model


def render(catalog_path: Path = CATALOG) -> str:
    """Resolve role references and preserve ladder rank and peer groups exactly."""
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    seats = load_orchestrator_seats(catalog_path)
    lines = [
        "# Catalog routing tables",
        "",
        "Generated from `scripts/config/model_catalog.yaml`; do not edit the tables.",
        "Regenerate with the task-prescribed interpreter:",
        "",
        "```bash",
        ".venv/bin/python -m agents_extensions.shared.skills.drive-epic.scripts.render_catalog_tables --write",
        "```",
        "",
        "These are candidate identities and order, not permission or health evidence.",
        "The reviewer resolver still applies author-family, subject-seat, risk, runtime",
        "attestation, capability, data-egress and live-health gates before selection.",
        "Excluded candidates can appear in a ladder; membership never grants admission.",
        "",
        "## Driver seats",
        "",
        "| seat | model_id | effort | escalate_model_id | escalate_effort |",
        "| --- | --- | --- | --- | --- |",
    ]
    for seat, row in sorted(seats.items()):
        active_model(row["model_id"], catalog)
        active_model(row["escalate_model_id"], catalog)
        lines.append("| " + " | ".join([seat, *(row[field] for field in SEAT_FIELDS)]) + " |")
    lines += [
        "",
        "## Review ladders",
        "",
        "Rank follows the catalog; entries at the same rank are peers.",
        "",
        "| risk | rank | candidate | model_id |",
        "| --- | --- | --- | --- |",
    ]
    for risk, groups in catalog["review_ladders"].items():
        for rank, group in enumerate(groups, 1):
            for reference in group:
                label = resolve_routing_reference(reference, catalog)
                model = resolve_routing_reference({**reference, "field": "model_id"}, catalog)
                active_model(model, catalog)
                lines.append(f"| {risk} | {rank} | {label} | {model} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Write the projection explicitly, or fail closed on missing/drifting output."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Regenerate the canonical reference")
    mode.add_argument("--check", action="store_true", help="Check drift (the default)")
    args = parser.parse_args(argv)
    expected = render()
    if args.write:
        OUTPUT.write_text(expected, encoding="utf-8")
        print("Catalog routing tables regenerated")
        return 0
    if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
        print("Catalog routing tables drift: regenerate with --write")
        return 1
    print("Catalog routing tables OK (seats and ordered review ladders)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

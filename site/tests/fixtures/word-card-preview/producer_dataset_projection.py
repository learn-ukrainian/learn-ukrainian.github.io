"""Versioned assertion-only dataset projection and withdrawal packages (#8988).

Dataset scope comes from the current register. Candidate projection is opt-in;
only exact-artifact dataset certification earns a CERTIFIED row status.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import tempfile
from collections import Counter, defaultdict
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml
from jsonschema import Draft202012Validator

from scripts.atlas import word_card_certification as certification
from scripts.common.jsonl import jsonl_lines
from scripts.projects.open_model_data.review_build.errors import BuildError
from scripts.projects.open_model_data.review_build.output import OutputGuard

SCHEMA_VERSION = "word-card-dataset.v1"
_HISTORICAL_SOURCE_ID = "".join(("sum", "11"))


class ProjectionRefusal(ValueError):
    """A projection cannot preserve its permission or citation contract."""


def canonical(value: object) -> bytes:
    """Canonical UTF-8 JSON, including a final newline, with no nonfinite values."""
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n").encode("utf-8")


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


@dataclass(frozen=True)
class Release:
    dataset: bytes
    manifest: dict
    withdrawal_notice: dict | None = None

    def write(self, output: Path) -> None:
        """Create a fresh package directory, refusing any existing release."""
        if output.exists():
            raise FileExistsError("Release output already exists")
        with OutputGuard(output, (ROOT,)) as guard:
            guard.write(self.manifest["dataset_file"], self.dataset)
            if self.withdrawal_notice is not None:
                guard.write("withdrawal-notice.json", canonical(self.withdrawal_notice))
            # The manifest is the completion marker and is written last.
            guard.write("manifest.json", canonical(self.manifest))


def load_cards(path: Path, register_path: Path) -> list[dict]:
    """Read assembled JSON/JSONL, an assembly directory, or a frozen pilot manifest."""
    if path.is_dir():
        directory = path / "cards" if (path / "cards").is_dir() else path
        return [json.loads(p.read_bytes()) for p in sorted(directory.glob("*.json"))]
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in jsonl_lines(path.read_bytes().decode("utf-8")) if line.strip()]
    value = json.loads(path.read_bytes())
    if isinstance(value, dict) and "selection" in value:
        from scripts.atlas import word_card_assembly as assembly
        from scripts.common.scratch import ensure_scratch_root

        with ExitStack() as stack:
            scratch = Path(stack.enter_context(tempfile.TemporaryDirectory(dir=ensure_scratch_root())))
            inputs = assembly.load_inputs(
                path, ROOT / "registry/atlas/identity/registry.json", register_path,
                assembly.store_path("sources", None), assembly.store_path("vesum", None),
                assembly.store_path("atlas", None), stack, scratch, None,
            )
            return list(assembly.build(inputs)["cards"].values())
    if isinstance(value, dict) and "card_id" in value:
        return [value]
    if isinstance(value, dict) and "cards" in value:
        value = value["cards"]
    if isinstance(value, dict):
        value = list(value.values())
    if not isinstance(value, list):
        raise ProjectionRefusal("Expected an assembled card inventory or pilot manifest")
    return value


def _withdrawals(entries: list[dict]) -> list[dict]:
    if not isinstance(entries, list):
        raise ProjectionRefusal("Withdrawals must be an array")
    result = []
    for entry in entries:
        if (not isinstance(entry, dict) or set(entry) != {"selector", "justification"}
                or not isinstance(entry["justification"], str) or not entry["justification"].strip()):
            raise ProjectionRefusal("Withdrawal requires a selector and nonempty justification")
        selector = entry["selector"]
        if (not isinstance(selector, dict) or not selector or set(selector) - {"source_id", "locator"}
                or any(not isinstance(v, str) or not v.strip() for v in selector.values())):
            raise ProjectionRefusal("Withdrawal selects a source_id, a locator, or both")
        result.append(copy.deepcopy(entry))
    return sorted(result, key=canonical)


def _matches(assertion: dict, selector: dict) -> bool:
    return all(
        assertion["source_id"] == value if key == "source_id" else
        value in {assertion["locator"], assertion.get("source_record_key")}
        for key, value in selector.items()
    )


def _filter_reason(assertion: dict, source: dict | None, withdrawals: list[dict]) -> str | None:
    if assertion["status"] != "active":
        return "inactive"
    if any(_matches(assertion, entry["selector"]) for entry in withdrawals):
        return "withdrawn"
    if source is None or "dataset" not in source.get("appears_in", []):
        return "dataset_scope_absent"
    # Context is retained in the internal card. No Soviet dictionary payload
    # enters this modern-definition dataset, even when its scope says dataset.
    if assertion["source_id"] == _HISTORICAL_SOURCE_ID or assertion["field"] in {
        "russification_exposed", "soviet_colonization_context",
    }:
        return "historical_context_only"
    if assertion["producer"]["kind"] in {"generator", "estimator"}:
        return "derived_without_lineage"
    mapping = assertion.get("mapping", {})
    if mapping.get("confidence") in {"low", "unresolved"} or mapping.get("ambiguous", False):
        return "unresolved_mapping"
    if assertion["review"]["status"] == "rejected":
        return "rejected"
    return None


@certification.certification_run()
def create_release(
    cards: list[dict], *, release_version: str, register_path: Path | None = None,
    format: str = "jsonl", withdrawals: list[dict] | None = None,
    allow_candidates: bool = False,
) -> Release:
    """Classify inputs, filter assertions and build deterministic release bytes.

    Every included assertion becomes one cited field. Cached resolutions,
    headwords, identity metadata and arbitrary outer properties are never copied.
    """
    if not isinstance(release_version, str) or not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?",
                                                             release_version):
        raise ProjectionRefusal("Release version must have form v0.1.0-pilot")
    if format not in {"json", "jsonl"}:
        raise ProjectionRefusal("Dataset format must be json or jsonl")
    withdrawals = _withdrawals([] if withdrawals is None else withdrawals)
    if not cards or len({c["card_id"] for c in cards}) != len(cards):
        raise ProjectionRefusal("Input cards must be nonempty and unique")
    register_bytes = (register_path or certification.PERMISSIONS_REGISTER_PATH).read_bytes()
    register_hash = sha256(register_bytes)
    # Projection annotations extend the assembled card schema, not certification.
    schema = json.loads(certification.SCHEMA_PATH.read_bytes())
    schema["properties"].update({
        "card_version": {"type": "string", "minLength": 1},
        "known_gaps": {"type": "array"},
    })
    validator = Draft202012Validator(schema)
    statuses = {}
    for card in cards:
        if not validator.is_valid(card):
            raise ProjectionRefusal("Invalid word-card schema")
        if card["state"] != "active":
            raise ProjectionRefusal("Only active cards may be projected")
        try:
            certification.load_certified_card_for_export(card, required_approval="dataset")
        except certification.UncertifiedCardRefusal:
            if not allow_candidates:
                raise
            statuses[card["card_id"]] = "CANDIDATE"
        else:
            statuses[card["card_id"]] = "CERTIFIED"
        if card["build"]["inputs"]["R"]["register"]["content_sha256"] != register_hash:
            raise ProjectionRefusal("Projection register differs from card register")
    register = yaml.safe_load(register_bytes)
    sources = {s["id"]: s for s in register["sources"]}
    if len(sources) != len(register["sources"]):
        raise ProjectionRefusal("Duplicate register source")
    for source in sources.values():
        scopes = source.get("appears_in", [])
        if not isinstance(scopes, list) or any(scope not in {"internal", "site", "dataset"} for scope in scopes):
            raise ProjectionRefusal("Invalid register source scopes")
    for entry in withdrawals:
        if not any(_matches(a, entry["selector"]) for card in cards for a in card["assertions"]
                   if a["status"] == "active"):
            raise ProjectionRefusal("Withdrawal selector matches no active assertion")
    rows = []
    counts = defaultdict(Counter)
    source_rows = defaultdict(lambda: {"included": set(), "filtered": set()})
    seen_assertions = set()
    for card in sorted(cards, key=lambda c: c["card_id"]):
        fields = []
        for assertion in sorted(card["assertions"], key=lambda a: a["assertion_id"]):
            assertion_id = assertion["assertion_id"]
            if assertion_id in seen_assertions:
                raise ProjectionRefusal("Duplicate assertion identity")
            seen_assertions.add(assertion_id)
            source_id = assertion.get("source_id")
            # Public tombstones deliberately have no source or payload.
            if source_id is None:
                counts["_tombstone"]["inactive"] += 1
                continue
            source = sources.get(source_id)
            reason = _filter_reason(assertion, source, withdrawals)
            row_key = (assertion["snapshot_id"], assertion.get("source_record_id")
                       or assertion.get("source_record_key") or assertion["locator"])
            counts[source_id][reason or "included"] += 1
            source_rows[source_id]["filtered" if reason else "included"].add(row_key)
            if reason:
                continue
            reference = assertion["licence_ref"]
            if (reference["register_source_id"] != source_id
                    or reference["register_version"] != register["schema_version"]
                    or not assertion["locator"].strip() or not assertion["snapshot_id"].strip()
                    or not source.get("citation", {}).get("form")
                    or not source.get("terms", {}).get("licence", {}).get("name")):
                raise ProjectionRefusal("Incomplete or mismatched field citation")
            fields.append({
                "assertion_id": assertion_id, "subject": copy.deepcopy(assertion["subject"]),
                "field": assertion["field"], "value": copy.deepcopy(assertion["value"]),
                "citation": {
                    "source_id": source_id, "snapshot_id": assertion["snapshot_id"],
                    "locator": assertion["locator"], "source_record_id": assertion.get("source_record_id"),
                    "source_record_key": assertion.get("source_record_key"),
                    "licence_ref": copy.deepcopy(reference), "attribution": source["citation"]["form"],
                    "licence": copy.deepcopy(source["terms"]["licence"]),
                    "terms_ref": f"docs/sources/permissions-register.yaml#sources/{source_id}/terms",
                },
            })
        if fields:
            rows.append({
                "card_id": card["card_id"],
                "card_version": card.get("card_version", card["build"].get("card_version", "0.1.0")),
                "card_kind": card["card_kind"], "status": statuses[card["card_id"]],
                "known_gaps": copy.deepcopy(card.get("known_gaps", [])), "fields": fields,
            })
    dataset = b"".join(canonical(row) for row in rows) if format == "jsonl" else canonical(rows)
    breakdown = {}
    for source_id, tally in sorted(counts.items()):
        included = tally.get("included", 0)
        row_sets = source_rows[source_id]
        breakdown[source_id] = {
            "included_assertions": included, "filtered_assertions": sum(tally.values()) - included,
            "filter_reasons": {k: v for k, v in sorted(tally.items()) if k != "included"},
            "included_source_rows": len(row_sets["included"]),
            "filtered_source_rows": len(row_sets["filtered"]),
            "mixed_source_rows": len(row_sets["included"] & row_sets["filtered"]),
        }
    manifest = {
        "schema_version": SCHEMA_VERSION, "release_version": release_version,
        "dataset_file": f"word-cards.{format}", "dataset_sha256": sha256(dataset), "dataset_bytes": len(dataset),
        "card_count": len(rows), "field_citation_count": sum(len(row["fields"]) for row in rows),
        "certified_count": sum(row["status"] == "CERTIFIED" for row in rows),
        "candidate_count": sum(row["status"] == "CANDIDATE" for row in rows),
        "input_card_count": len(cards), "input_assertion_count": len(seen_assertions),
        "input_cards_sha256": sha256(canonical(sorted(cards, key=lambda c: c["card_id"]))),
        "permissions_register_sha256": register_hash, "source_breakdown": breakdown,
        "operator_decisions": copy.deepcopy(register.get("operator_decisions", [])),
        "withdrawals": withdrawals,
    }
    return Release(dataset, manifest)


@certification.certification_run()
def withdraw_release(
    cards: list[dict], *, previous_version: str, release_version: str, selector: dict, justification: str,
    register_path: Path | None = None, format: str = "jsonl", withdrawals: list[dict] | None = None,
    allow_candidates: bool = False,
) -> Release:
    """Rebuild from original cards with all prior selectors plus one withdrawal."""
    if previous_version == release_version:
        raise ProjectionRefusal("Withdrawal requires a new release version")
    options = {"register_path": register_path, "format": format, "allow_candidates": allow_candidates}
    previous = create_release(cards, release_version=previous_version, withdrawals=withdrawals, **options)
    entries = [*(withdrawals or []), {"selector": selector, "justification": justification}]
    replacement = create_release(cards, release_version=release_version, withdrawals=entries, **options)
    notice = {
        "schema_version": "word-card-withdrawal.v1", "previous_release_version": previous_version,
        "previous_dataset_sha256": previous.manifest["dataset_sha256"],
        "replacement_release_version": release_version,
        "replacement_dataset_sha256": replacement.manifest["dataset_sha256"],
        "withdrawal": _withdrawals(entries[-1:])[0],
        "removed_field_citations": previous.manifest["field_citation_count"]
        - replacement.manifest["field_citation_count"],
    }
    manifest = replacement.manifest | {"withdrawal_notice_sha256": sha256(canonical(notice))}
    return Release(replacement.dataset, manifest, notice)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a versioned, cited word-card dataset with certification status.\n"
        "Use for local release packaging or withdrawal drills, never as certification or publication approval.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.projects.open_model_data.word_cards.dataset_projection \\
    --cards batch_state/reports/assembly --version v0.1.0-pilot --output "$TMPDIR/word-card-release"
  .venv/bin/python -m scripts.projects.open_model_data.word_cards.dataset_projection \\
    --cards cards.json --version v0.1.1-pilot --output "$TMPDIR/word-card-replacement" \\
    --previous-version v0.1.0-pilot --withdraw-source ulif --justification 'Removal request'
Outputs: word-cards.jsonl (or .json), manifest.json, and withdrawal-notice.json for a withdrawal.
Inputs and source databases are read-only. Output must be private, outside checkouts and not exist. Nothing is uploaded.
Exit codes: 0 success; 1 input, certification or output refusal; 2 usage error.
Related: #8988; docs/datasets/word-cards.md; scripts.atlas.word_card_assembly
""",
    )
    parser.add_argument("--cards", type=Path, required=True,
                        help="Assembled JSON/JSONL, cards directory, or pilot manifest, e.g. pilot-v1.json")
    parser.add_argument("--register", type=Path, default=certification.PERMISSIONS_REGISTER_PATH,
                        help="Permissions YAML, default docs/sources/permissions-register.yaml; must match card build inputs")
    parser.add_argument("--version", required=True, help="Release version, e.g. v0.1.0-pilot")
    parser.add_argument("--output", type=Path, required=True,
                        help="New private package directory outside checkouts, e.g. $TMPDIR/word-card-release")
    parser.add_argument("--format", choices=("json", "jsonl"), default="jsonl", help="Dataset encoding, default jsonl")
    parser.add_argument("--allow-candidates", action="store_true",
                        help="Include schema-valid uncertified cards as CANDIDATE; default requires dataset certification")
    parser.add_argument("--withdrawals", type=Path,
                        help="Prior cumulative selector/justification JSON array; default none")
    parser.add_argument("--previous-version", help="Prior version for a withdrawal, e.g. v0.1.0-pilot; default none")
    parser.add_argument("--withdraw-source", help="Source ID to withdraw, e.g. ulif; default none")
    parser.add_argument("--withdraw-locator", help="Exact assertion locator or source_record_key; default none")
    parser.add_argument("--justification", help="Public removal reason, e.g. issue reference; default none")
    args = parser.parse_args(argv)
    selector = {k: v for k, v in {"source_id": args.withdraw_source, "locator": args.withdraw_locator}.items() if v}
    if bool(selector) != bool(args.previous_version and args.justification) or (
        not selector and (args.previous_version or args.justification)
    ):
        parser.error("withdrawal requires a selector, --previous-version and --justification together")
    try:
        options = {"release_version": args.version, "register_path": args.register, "format": args.format,
                   "allow_candidates": args.allow_candidates,
                   "withdrawals": json.loads(args.withdrawals.read_bytes()) if args.withdrawals else None}
        cards = load_cards(args.cards, args.register)
        release = (withdraw_release(cards, previous_version=args.previous_version, selector=selector,
                                    justification=args.justification, **options) if selector else
                   create_release(cards, **options))
        release.write(args.output)
        print(canonical(release.manifest).decode(), end="")
        return 0
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError, BuildError):
        print("Dataset projection refused: invalid input, certification, citation or output", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

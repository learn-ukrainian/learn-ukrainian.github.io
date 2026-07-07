#!/usr/bin/env python3
"""Deterministically build the benchmark-v1 freeze manifest.

The command is inert until a caller writes ``benchmarks/v1/MANIFEST.json``.
Dry-runs print the exact manifest payload without touching the tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit import llm_reviewer, qg_bakeoff, qg_factcheck_scoring, qg_schema, qg_workflow

BENCHMARK_VERSION = "1.0.0"
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / "benchmarks" / "v1" / "MANIFEST.json"
PUBLIC_FIXTURE_DIR = PROJECT_ROOT / "tests" / "fixtures" / "qg_bakeoff"
SCORER_PATHS = (
    PROJECT_ROOT / "scripts" / "audit" / "qg_factcheck_scoring.py",
    PROJECT_ROOT / "scripts" / "audit" / "qg_bakeoff.py",
)
CLAIM_CLASSES = ("true", "U", "M")


class ManifestConfigError(ValueError):
    """Freeze manifest inputs are incomplete or malformed."""


def build_manifest(
    *,
    benchmark_version: str = BENCHMARK_VERSION,
    created_at: str | None,
    created_from: str | None = None,
    heldout_dir: Path | None = None,
    reference_scorecard: Path | None = None,
    gate_version: str | None = None,
    public_fixture_dir: Path | None = None,
) -> dict[str, Any]:
    """Return the deterministic benchmark manifest payload."""
    resolved_public_fixture_dir = public_fixture_dir or qg_bakeoff.FIXTURE_DIR
    resolved_gate_version = gate_version or qg_workflow.DEFAULT_GATE_VERSION
    reference_result = _reference_result(reference_scorecard)
    return {
        "benchmark_version": benchmark_version,
        "created_at": created_at,
        "created_from": created_from or _git_head(),
        "fixtures": {
            "public": _public_fixtures(resolved_public_fixture_dir),
            "heldout": _heldout_fixtures(heldout_dir),
        },
        "scorer": _scorer_block(),
        "gates": _gates_block(resolved_gate_version),
        "matching_surface": {
            "policy": "frozen files are immutable; value-equality diagnostics are not a semantic-refactor license",
            "canary_sentence_scope": (
                "canary sentences are external contamination probes only; compliant enumerate-every-claim "
                "runs may emit one extra unmatched fact_check per canary passage"
            ),
        },
        "DOMAIN_BY_SLUG": dict(qg_bakeoff.DOMAIN_BY_SLUG),
        "reference_result": reference_result,
    }


def manifest_json(manifest: Mapping[str, Any]) -> str:
    """Serialize a manifest with stable formatting."""
    return json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _public_fixtures(fixtures_dir: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    by_class = _empty_counts()
    by_domain: dict[str, Counter[str]] = defaultdict(Counter)
    paths = sorted(fixtures_dir.glob("*.json"))
    if not paths:
        raise ManifestConfigError(f"no public fixture JSON files found under {fixtures_dir}")
    for path in paths:
        fixture = qg_bakeoff.load_fixture(path)
        domain = qg_bakeoff.domain_for_slug(fixture.slug)
        counts = _fixture_claim_counts(fixture)
        _merge_counts(by_class, counts)
        by_domain[domain].update(counts)
        files.append(
            {
                "path": _rel(path),
                "sha256": _sha256_file(path),
                "slug": fixture.slug,
                "domain": domain,
                "claim_totals": dict(counts),
            }
        )
    return {
        "fixtures_dir": _rel(fixtures_dir),
        "files": files,
        "claim_totals": {
            "by_class": dict(by_class),
            "by_domain": {domain: dict(_ordered_counts(counts)) for domain, counts in sorted(by_domain.items())},
        },
    }


def _heldout_fixtures(heldout_dir: Path | None) -> dict[str, Any]:
    if heldout_dir is None:
        return {"count": 0, "sha256": []}
    if not heldout_dir.exists() or not heldout_dir.is_dir():
        raise ManifestConfigError(f"heldout directory does not exist: {heldout_dir}")
    hashes = sorted(
        _sha256_file(path)
        for path in heldout_dir.iterdir()
        if path.is_file() and path.suffix == ".json" and not path.name.startswith(".")
    )
    return {"count": len(hashes), "sha256": hashes}


def _scorer_block() -> dict[str, Any]:
    return {
        "files": {_rel(path): _sha256_file(path) for path in SCORER_PATHS},
        "constants": _constants_snapshot(),
    }


def _constants_snapshot() -> dict[str, Any]:
    verdict_constants = {
        name: value
        for name, value in sorted(vars(qg_factcheck_scoring).items())
        if name.isupper() and isinstance(value, int) and not isinstance(value, bool)
    }
    return {
        "verdict_constants": verdict_constants,
        "FACT_CHECK_VERDICTS": sorted(qg_schema.FACT_CHECK_VERDICTS),
        "MISSING_CLAIM_PENALTY": qg_bakeoff.MISSING_CLAIM_PENALTY,
        "RUN_SCHEMA_VERSION": qg_bakeoff.RUN_SCHEMA_VERSION,
    }


def _gates_block(gate_version: str) -> dict[str, Any]:
    prompt_template = llm_reviewer.load_reviewer_prompt_template()
    taxonomy_slice = qg_bakeoff._reviewer_verdict_taxonomy()
    return {
        "gate_version": gate_version,
        "reviewer_prompt_sha256": _sha256_text(prompt_template),
        "taxonomy_slice_sha256": _sha256_text(taxonomy_slice),
    }


def _reference_result(reference_scorecard: Path | None) -> dict[str, str] | None:
    if reference_scorecard is None:
        return None
    if not reference_scorecard.exists() or not reference_scorecard.is_file():
        raise ManifestConfigError(f"reference scorecard does not exist: {reference_scorecard}")
    return {"path": _rel(reference_scorecard), "sha256": _sha256_file(reference_scorecard)}


def _fixture_claim_counts(fixture: qg_bakeoff.BakeoffFixture) -> Counter[str]:
    counts = Counter({claim_class: 0 for claim_class in CLAIM_CLASSES})
    for claim in fixture.claims:
        claim_class = "true" if claim.is_true else str(claim.fabrication_class)
        if claim_class not in CLAIM_CLASSES:
            raise ManifestConfigError(f"{fixture.slug}: unsupported claim class {claim_class!r}")
        counts[claim_class] += 1
    counts["total"] = sum(counts[claim_class] for claim_class in CLAIM_CLASSES)
    return _ordered_counts(counts)


def _empty_counts() -> Counter[str]:
    return Counter({claim_class: 0 for claim_class in (*CLAIM_CLASSES, "total")})


def _merge_counts(target: Counter[str], source: Mapping[str, int]) -> None:
    for key in (*CLAIM_CLASSES, "total"):
        target[key] += int(source.get(key) or 0)


def _ordered_counts(counts: Mapping[str, int]) -> Counter[str]:
    return Counter({key: int(counts.get(key) or 0) for key in (*CLAIM_CLASSES, "total")})


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.PIPE,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ManifestConfigError(f"could not resolve git HEAD: {exc}") from exc


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--heldout-dir", type=Path, default=None)
    parser.add_argument("--reference-scorecard", type=Path, default=None)
    parser.add_argument("--created-at", default=None, help="Deterministic provenance timestamp; never inferred")
    parser.add_argument("--created-from", default=None, help="Override git commit provenance")
    parser.add_argument("--benchmark-version", default=BENCHMARK_VERSION)
    parser.add_argument("--gate-version", default=None)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--dry-run", action="store_true", help="Print manifest JSON without writing")
    args = parser.parse_args(argv)

    try:
        if not args.dry_run:
            if args.created_at is None:
                raise ManifestConfigError("--created-at is required when writing MANIFEST.json")
            if args.reference_scorecard is None:
                raise ManifestConfigError("--reference-scorecard is required when writing MANIFEST.json")
        manifest = build_manifest(
            benchmark_version=args.benchmark_version,
            created_at=args.created_at,
            created_from=args.created_from,
            heldout_dir=args.heldout_dir,
            reference_scorecard=args.reference_scorecard,
            gate_version=args.gate_version,
        )
        payload = manifest_json(manifest)
        if args.dry_run:
            print(payload, end="")
            return 0
        args.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        args.manifest_path.write_text(payload, encoding="utf-8")
    except ManifestConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"wrote {_rel(args.manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

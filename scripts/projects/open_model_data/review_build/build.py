"""Build/verify orchestration. Inputs and all text-bearing outputs stay host local."""

import json
from collections import Counter, defaultdict
from dataclasses import asdict, replace
from pathlib import Path

import yaml

from .attribution import AttributionAdapter, Resolver, SyntheticAdapter
from .catalog import Catalog
from .contract import Candidate, candidate_from_dict, canonical, digest, record_id, values
from .errors import BuildError, require
from .gate import Gate
from .manifest import code_pins, private_manifest
from .output import OutputGuard
from .snapshot import FileStore, SnapshotReader

FRAMEWORK_VERSION = "1.0.0"


def _jsonl(items: list[dict]) -> bytes:
    return b"".join(canonical(item) + b"\n" for item in items)


def prepare(candidates: list[Candidate], gate: Gate) -> list[Candidate]:
    """Only unresolved attribution/applicability withholds; mechanism faults fail."""
    result = []
    for candidate in candidates:
        if candidate.outcome != "accepted":
            result.append(candidate)
            continue
        try:
            for value in values(candidate):
                for citation in value.citations:
                    # Empty locators are contract errors, not attributed records.
                    require(bool(citation.locator.strip()), "empty_locator")
                    gate.resolver.resolve(citation, gate.reader)
            gate.applicable(candidate)
        except BuildError as exc:
            if exc.code not in {"attribution_unresolved", "locator_unavailable", "catalog_inapplicable"}:
                raise
            candidate = replace(candidate, outcome="withheld", reason=exc.code, evidence=(exc.code,))
        result.append(candidate)
    return result


def artifacts(
    config: dict, candidates: list[Candidate], reader: SnapshotReader, catalog: Catalog, resolver: Resolver, pins: dict
) -> dict[str, bytes]:
    gate = Gate(reader, catalog, resolver, config["components"], config["compatibility"], config.get("corpus"))
    effective = prepare(candidates, gate)
    records, report = gate.run(effective)
    files = {"candidates.jsonl": _jsonl([asdict(c) for c in sorted(effective, key=record_id)])}
    by_component = defaultdict(list)
    for record in records:
        by_component[record["component"]].append(record)
    for component in sorted(config["components"]):
        files[f"{component}/records.jsonl"] = _jsonl(by_component[component])
    notices = sorted(
        {
            (p["source_id"], p["licence_ref"], p["attribution"])
            for record in records
            for p in record["provenance"].values()
        }
    )
    files["licence-notices.jsonl"] = _jsonl(
        [dict(zip(("source_id", "licence_ref", "attribution"), notice, strict=True)) for notice in notices]
    )
    files["accounting.json"] = canonical(report["accounting"]) + b"\n"
    files["metrics.json"] = canonical(report["metrics"]) + b"\n"
    readme = [
        "# Private review build",
        "",
        "Status: review_only. This artifact makes no training-readiness claim.",
        "D2 tool flags and D3 independent language review are required before RB-1 delivery.",
        "No normalization changes source/export bytes. Template metrics normalize comparison text only.",
        "",
        "Unit accounting (accepted / rejected / withheld / excluded):",
    ]
    for component, counts in report["accounting"].items():
        readme.append(
            f"- {component}: {counts['accepted']} / {counts['rejected']} / {counts['withheld']} / {counts['excluded']} of {counts['counted']}."
        )
        readme.append("  Reason counts: " + canonical(counts["reasons"]).decode())
        # Component-reviewed control metadata supplies unit grain and layer/multiplicity description.
        for key in ("unit_grain", "annotation_layer", "reference_multiplicity"):
            if key in config["components"][component]:
                readme.append(f"  {key}: {config['components'][component][key]}")
    for operation, metrics in report["metrics"].items():
        if metrics["status"] != "PASS":
            readme.append(f"- {operation}: {metrics['status']}; not training-ready.")
    files["README.md"] = ("\n".join(readme) + "\n").encode()
    manifest = {
        "schema": "omd-review-build.v1",
        "framework_version": FRAMEWORK_VERSION,
        "record_version": "omd-review-record.v1",
        "catalog_version": catalog.version,
        "status": "review_only",
        "pins": pins,
        **report,
        "files": {name: digest(content) for name, content in sorted(files.items())},
    }
    files["manifest.json"] = canonical(manifest) + b"\n"
    tallies = Counter()
    for counts in report["accounting"].values():
        tallies.update(counts["reasons"])
    public_safe = private_manifest(
        {
            "hashes": {
                "build": digest(files["manifest.json"]),
                "register": pins["register"],
                "catalog": pins["catalog"],
                "parser": pins["code"]["parser_sha256"],
                "candidates": pins["candidates"],
                "spec": pins["spec"],
            },
            "counts": {
                f"{component}.{outcome}": counts[outcome]
                for component, counts in report["accounting"].items()
                for outcome in ("accepted", "rejected", "withheld", "excluded", "counted")
            },
            "versions": {"record": "omd-review-record.v1", "framework": FRAMEWORK_VERSION, "catalog": catalog.version},
            "code_sha": pins["code"]["code_sha"],
            "reason_code_tallies": dict(sorted(tallies.items())),
        }
    )
    files["private-manifest.json"] = canonical(public_safe) + b"\n"
    return files


def execute(
    config_path: Path,
    out: OutputGuard,
    *,
    verify: bool = False,
    adapters: dict[str, AttributionAdapter] | None = None,
    files: dict[str, FileStore] | None = None,
) -> dict:
    """Config is a host-local JSON descriptor, not executable component code.

    Required keys: schema, candidates (JSONL), catalog (YAML), register (YAML),
    databases {store:path}, components {C*: reviewed spec}, compatibility (roles).
    Optional corpus (split field mapping), synthetic_sources (explicit test ids).
    Component specs require unit_query, frozen_count, reasons, operations, binding;
    optional transforms, applicability, context/response serializers. Bindings and
    roles schemas are documented in their modules and exercised by synthetic tests.
    """
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    require(config["schema"] == "omd-review-request.v1", "request_schema")
    root = config_path.parent

    def input_path(value: str) -> Path:
        return (root / value).resolve()

    catalog_bytes = input_path(config["catalog"]).read_bytes()
    register_bytes = input_path(config["register"]).read_bytes()
    candidates_bytes = input_path(config["candidates"]).read_bytes()
    catalog = Catalog(yaml.safe_load(catalog_bytes))
    candidates = [candidate_from_dict(json.loads(line)) for line in candidates_bytes.splitlines() if line.strip()]
    source_adapters = dict(adapters or {})
    for source in config.get("synthetic_sources", []):
        require(source.startswith("synthetic"), "synthetic_adapter_source")
        source_adapters[source] = SyntheticAdapter()
    resolver = Resolver(yaml.safe_load(register_bytes), source_adapters)
    pins = {
        "register": digest(register_bytes),
        "catalog": digest(catalog_bytes),
        "candidates": digest(candidates_bytes),
        "spec": digest(config_bytes),
        "code": code_pins(),
    }
    with SnapshotReader({store: input_path(path) for store, path in config["databases"].items()}, files) as reader:
        result = artifacts(config, candidates, reader, catalog, resolver, pins)
    if verify:
        for name, content in sorted(result.items()):
            require(out.read(name) == content, "artifact_mismatch")
    else:
        for name, content in sorted(result.items()):
            out.write(name, content)
    return {
        "status": "verified" if verify else "built",
        "build_sha256": digest(result["manifest.json"]),
        "files": len(result),
    }

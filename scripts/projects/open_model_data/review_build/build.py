"""Build/verify orchestration. Inputs and all text-bearing outputs stay host local."""

import json
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path

import yaml

from scripts.common.jsonl import jsonl_lines

from .attribution import AttributionAdapter, Resolver, SyntheticAdapter
from .bindings import expand, select
from .catalog import Catalog
from .components import Component, ComponentContext, merge_adapters
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


def verify_mutations(
    config: dict,
    candidates: list[Candidate],
    reader: SnapshotReader,
    catalog: Catalog,
    resolver: Resolver,
    out: OutputGuard,
) -> dict[str, str]:
    """Generate host-local generic must-fail inputs from this build's own rows.

    Run the gate directly: withholding preparation must never hide the defect.
    Each fixture keeps the full accounting stream except the missing-unit case.
    """
    eligible = [
        (i, c, area, j, v)
        for i, c in enumerate(candidates)
        if c.outcome == "accepted"
        for area in ("slots", "context", "response")
        for j, v in enumerate(getattr(c, area))
        if v.citations
    ]
    # A build with no records cannot prove quotation mutations; refuse rather
    # than fabricate a successful generic fixture run.
    require(bool(eligible), "mutation_unavailable")
    i, candidate, area, j, value = eligible[0]

    def changed_value(new_value):
        parts = list(getattr(candidate, area))
        parts[j] = new_value
        stream = list(candidates)
        stream[i] = replace(candidate, **{area: tuple(parts)})
        return stream

    fixtures = {
        "absent_quote": changed_value(replace(value, text=value.text + "\0")),
        "wrong_span": changed_value(replace(value, span=(-1, 0))),
        "empty_locator": changed_value(
            replace(value, citations=(replace(value.citations[0], locator=""), *value.citations[1:]))
        ),
        "missing_unit": candidates[:i] + candidates[i + 1 :],
    }
    # Find an observable swap: a heading's span can quote the same prefix from
    # two different fields, in which case that particular swap is no mutation.
    gate = Gate(reader, catalog, resolver, config["components"], config["compatibility"], config.get("corpus"))
    donors = sorted(
        {c for unit in candidates for v in values(unit) for c in v.citations}, key=lambda c: canonical(asdict(c))
    )
    for index, unit in enumerate(candidates):
        if unit.outcome != "accepted":
            continue
        ref = expand(unit, gate.spec(unit)["unit_id"]["primary"][0]["selector"])[0]
        primary_value = select(unit, ref)
        primary = primary_value.citations[0]
        ordered = sorted(
            donors,
            key=lambda c: (
                (c.store, c.table, c.row_key) == (primary.store, primary.table, primary.row_key),
                canonical(asdict(c)),
            ),
        )
        for donor in ordered:
            if donor == primary:
                continue
            swapped = replace(primary_value, citations=(donor, *primary_value.citations[1:]))
            parts = list(getattr(unit, ref["area"]))
            positions = [j for j, value in enumerate(parts) if value.slot == ref["slot"]]
            parts[positions[ref.get("index", 0)]] = swapped
            mutated = replace(unit, **{ref["area"]: tuple(parts)})
            try:
                require(gate.unit_id(mutated) == unit.unit_id, "unit_id_mismatch")
                gate.quote(mutated)
            except BuildError as exc:
                if exc.code not in {
                    "unit_id_mismatch",
                    "quote_mismatch",
                    "quote_span",
                    "field_digest",
                    "source_compatibility",
                }:
                    continue
                fixtures["swapped_citation"] = list(candidates)
                fixtures["swapped_citation"][index] = mutated
                break
        if "swapped_citation" in fixtures:
            break
    require("swapped_citation" in fixtures, "mutation_unavailable")
    failures = {}
    for name, stream in sorted(fixtures.items()):
        gate = Gate(reader, catalog, resolver, config["components"], config["compatibility"], config.get("corpus"))
        try:
            gate.run(stream)
        except BuildError as exc:
            expected = {
                "absent_quote": {"quote_mismatch"},
                "wrong_span": {"quote_span"},
                "empty_locator": {"empty_locator"},
                "missing_unit": {"missing_unit"},
                "swapped_citation": {
                    "unit_id_mismatch",
                    "quote_mismatch",
                    "quote_span",
                    "field_digest",
                    "source_compatibility",
                },
            }
            require(exc.code in expected[name], "mutation_wrong_failure")
            failures[name] = exc.code
        else:
            raise BuildError("mutation_admitted")
        out.write(f"mutation-fixtures/{name}.jsonl", _jsonl([asdict(c) for c in stream]))
    out.write("mutation-fixtures/results.json", canonical(failures) + b"\n")
    return failures


def execute(
    config_path: Path,
    out: OutputGuard,
    *,
    verify: bool = False,
    adapters: dict[str, AttributionAdapter] | None = None,
    files: dict[str, FileStore] | None = None,
    components: list[str] | None = None,
    component_objects: dict[str, Component] | None = None,
) -> dict:
    """Config is a host-local JSON descriptor, not executable component code.

    Required keys: schema, catalog (YAML), register (YAML),
    databases {store:path}, components {C*: reviewed spec}, compatibility (roles).
    Staged-library mode also requires candidates (JSONL); registered objects extract
    candidates through the shared reader. Optional corpus (split field mapping)
    and synthetic_sources (explicit test ids).
    Component specs require unit_query, unit_id, frozen_count, reasons, operations, binding;
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
    catalog = Catalog(yaml.safe_load(catalog_bytes))
    if components is not None:
        selected = set(components)
        require(bool(selected) and selected <= set(config["components"]), "component_selection")
        config["components"] = {c: spec for c, spec in config["components"].items() if c in selected}
    if component_objects is not None:
        require(set(component_objects) == set(config["components"]), "component_selection")
        config["components"] = {c: deepcopy(obj.spec) for c, obj in component_objects.items()}
    source_adapters = merge_adapters(adapters or {}, *(obj.adapters for obj in (component_objects or {}).values()))
    for source in config.get("synthetic_sources", []):
        require(source.startswith("synthetic"), "synthetic_adapter_source")
        # An explicit adapter cannot be silently overwritten by request data.
        if source not in source_adapters:
            source_adapters[source] = SyntheticAdapter()
    resolver = Resolver(yaml.safe_load(register_bytes), source_adapters)
    source_files = dict(files or {})
    for obj in (component_objects or {}).values():
        for store, adapter in getattr(obj, "files", {}).items():
            require(store not in source_files or source_files[store] is adapter, "file_store_conflict")
            source_files[store] = adapter
    pins = {
        "register": digest(register_bytes),
        "catalog": digest(catalog_bytes),
        "spec": digest(config_bytes),
        "request": digest(canonical(config)),
        "component_specs": digest(canonical(config["components"])),
        "components": sorted(config["components"]),
        "code": code_pins(),
    }
    with SnapshotReader(
        {store: input_path(path) for store, path in config["databases"].items()}, source_files
    ) as reader:
        if component_objects is not None:
            candidates = []
            ctx = ComponentContext(reader, config)
            for component, obj in component_objects.items():
                stream = list(obj.iter_candidates(ctx))
                require(all(c.component == component for c in stream), "component_candidates")
                candidates.extend(stream)
            require(
                digest(canonical({c: obj.spec for c, obj in component_objects.items()})) == pins["component_specs"],
                "spec_mutated",
            )
            candidates.sort(key=record_id)
            candidates_bytes = _jsonl([asdict(c) for c in candidates])
        else:
            candidates_bytes = input_path(config["candidates"]).read_bytes()
            candidates = [
                candidate_from_dict(json.loads(line))
                for line in jsonl_lines(candidates_bytes.decode("utf-8"))
                if line.strip()
            ]
            if components is not None:
                candidates = [c for c in candidates if c.component in set(components)]
        require(digest(canonical(config["components"])) == pins["component_specs"], "spec_mutated")
        require(digest(canonical(config)) == pins["request"], "spec_mutated")
        pins["candidates"] = digest(candidates_bytes)
        result = artifacts(config, candidates, reader, catalog, resolver, pins)
        if verify:
            require(out.read("manifest.json") == result["manifest.json"], "artifact_mismatch")
            for name, content in sorted(result.items()):
                require(out.read(name) == content, "artifact_mismatch")
            verify_mutations(
                config,
                prepare(
                    candidates,
                    Gate(
                        reader, catalog, resolver, config["components"], config["compatibility"], config.get("corpus")
                    ),
                ),
                reader,
                catalog,
                resolver,
                out,
            )
        else:
            for name, content in sorted(result.items()):
                out.write(name, content)
    return {
        "status": "verified" if verify else "built",
        "build_sha256": digest(result["manifest.json"]),
        "files": len(result),
    }

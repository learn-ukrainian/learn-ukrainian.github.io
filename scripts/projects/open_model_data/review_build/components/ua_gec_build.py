"""WP1 host-local integration of the frozen framework, not another build engine.

The WP0 JSON-only CLI cannot inject real FileStore/AttributionAdapter objects.
This entry point calls its documented execute interface without changing WP0.
"""

import argparse
import json
import traceback
from dataclasses import asdict, replace
from pathlib import Path

import yaml

from .. import bindings
from ..__main__ import Parser
from ..attribution import Resolver
from ..build import execute
from ..catalog import Catalog
from ..contract import canonical
from ..errors import BuildError, require
from ..gate import Gate
from ..output import OutputGuard
from ..snapshot import SnapshotReader
from . import c1_ua_gec, c6a_calque
from .ua_gec_split import CORPUS, UaGecAttribution, UaGecFileStore, exclusion, manifest_bytes

COMPONENTS = {"C1": c1_ua_gec, "C6": c6a_calque}


def request(store: UaGecFileStore, selected: list[str], catalog: Path, register: Path) -> tuple[dict, list]:
    require(
        bool(selected) and len(selected) == len(set(selected)) and set(selected) <= set(COMPONENTS), "component_spec"
    )
    specs = {name: COMPONENTS[name].spec() for name in selected}
    candidates = [candidate for name in selected for candidate in COMPONENTS[name].extract(store)]
    return {
        "schema": "omd-review-request.v1",
        "candidates": "input-candidates.jsonl",
        "catalog": str(catalog.resolve()),
        "register": str(register.resolve()),
        "databases": {},
        "components": specs,
        "compatibility": store.compatibility(),
        "corpus": CORPUS,
    }, candidates


def verify_component_mutations(config: dict, candidates: list, store: UaGecFileStore, output: OutputGuard) -> dict:
    """Private component fixtures assert exact mechanism refusals on real rows.

    The framework's execute(verify=True) supplies full-stream accounting and
    generic mutations. These fixtures exercise source-specific quotation,
    binding and role gates; they make no semantic or D3 approval claim.
    """
    catalog = Catalog(yaml.safe_load(Path(config["catalog"]).read_bytes()))
    register = yaml.safe_load(Path(config["register"]).read_bytes())
    results = {}
    with SnapshotReader({}, {"ua-gec": store}) as reader:
        resolver = Resolver(register, {"ua_gec": UaGecAttribution(store)})
        gate = Gate(reader, catalog, resolver, config["components"], config["compatibility"], CORPUS)
        fixtures = []
        for row in store.all_rows("corpus"):
            if row["layer"] != "gec-only" or "C1" not in config["components"]:
                continue
            citation_candidate = c1_ua_gec.candidate(row, store.splits)
            reason = exclusion(row, store.splits)
            if reason and reason not in {name for name, _, _, _ in fixtures}:
                fixtures.append((reason, citation_candidate, "roles", reason))
        if "C6" in config["components"]:
            mixed = next((c for c in candidates if c.component == "C6" and c.reason == "mixed_to_c1"), None)
            require(mixed is not None, "mutation_unavailable")
            fixtures.append(("mixed_edit", mixed, "roles", "mixed_edit"))
        for component in config["components"]:
            admitted = [c for c in candidates if c.component == component and c.outcome == "accepted"]
            require(len(admitted) >= 2, "mutation_unavailable")
            base = admitted[0]
            donors = [c for c in admitted if c.unit_id != base.unit_id]
            swapped = replace(base, response=donors[0].response)
            fixtures.append((component + "_wrong_reference", swapped, "binding", "binding_row"))
            target = replace(base.response[0], text=base.response[0].text + "\0")
            fixtures.append((component + "_absent_quote", replace(base, response=(target,)), "quote", "quote_mismatch"))
            fixtures.append(
                (
                    component + "_paraphrase",
                    replace(base, response=(replace(target, transform="paraphrase"),)),
                    "quote",
                    "unknown_transform",
                )
            )
            # All attribution forms except the authenticated full held form fail.
            fixtures.append((component + "_attribution_placeholder", base, "attribution", "attribution_unresolved"))
        for name, candidate, mechanism, expected in fixtures:
            candidate = replace(
                candidate,
                outcome="accepted",
                reason="aligned_pair" if candidate.component == "C1" else "calque_only",
                evidence=(),
            )
            try:
                if mechanism == "roles":
                    gate.roles.check(candidate.slots[0].citations[0], candidate, set())
                elif mechanism == "binding":
                    bindings.check(candidate, config["components"][candidate.component]["binding"], reader, {})
                elif mechanism == "attribution":
                    citation = candidate.slots[0].citations[0]
                    UaGecAttribution(store).resolve("<author> <year>", citation, reader.row(citation), reader)
                else:
                    gate.quote(candidate)
            except BuildError as exc:
                require(exc.code == expected, "mutation_wrong_failure")
                results[name] = exc.code
            else:
                raise BuildError("mutation_admitted")
            output.write(f"mutation-fixtures/wp1-{name}.jsonl", canonical(asdict(candidate)) + b"\n")
    output.write("mutation-fixtures/wp1-results.json", canonical(results) + b"\n")
    return results


def run(command: str, root: Path, out: OutputGuard, catalog: Path, register: Path, selected: list[str]) -> dict:
    store = UaGecFileStore(root)
    config, candidates = request(store, selected, catalog, register)
    inputs = {
        "request.json": canonical(config) + b"\n",
        "input-candidates.jsonl": b"".join(canonical(asdict(c)) + b"\n" for c in candidates),
        "split-manifest.json": manifest_bytes(store),
    }
    for name, content in inputs.items():
        if command == "verify":
            require(out.read(name) == content, "artifact_mismatch")
        else:
            out.write(name, content)
    result = execute(
        out.path / "request.json",
        out,
        verify=command == "verify",
        adapters={"ua_gec": UaGecAttribution(store)},
        files={"ua-gec": store},
        components=selected,
    )
    if command == "verify":
        result["generic_mutations"] = json.loads(out.read("mutation-fixtures/results.json"))
        result["component_mutations"] = verify_component_mutations(config, candidates, store, out)
    result["split_counts"] = store.splits.counts()
    result["accounting"] = json.loads(out.read("accounting.json"))
    result["metrics"] = json.loads(out.read("metrics.json"))
    return result


def main(argv=None) -> int:
    parser = Parser(
        description="Build or verify WP1 through the frozen RB-1 framework.\n"
        "Use held host-only UA-GEC files and a reviewed catalog; never for uploads or training claims.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  .venv/bin/python -m scripts.projects.open_model_data.review_build.components.ua_gec_build build --ua-gec "$UA_GEC_ROOT" --out "$RB1_OUT" --components C1 C6
  .venv/bin/python -m scripts.projects.open_model_data.review_build.components.ua_gec_build verify --ua-gec "$UA_GEC_ROOT" --out "$RB1_OUT"
Outputs: private candidates, split manifest, request, records, accounting, metrics,
  notices and verification fixtures under --out only. No database changes or network calls.
Exit codes: 0 = succeeded; 1 = gate/input/output failure; 2 = usage refused.
Related: docs/projects/open-model-data/REVIEW_BUILD.md; issues #9819, #9817, #9818, epic #6321.
""",
    )
    parser.add_argument(
        "command",
        choices=("build", "verify"),
        help="build writes private inputs/artifacts; verify compares them and tests mutations.",
    )
    parser.add_argument(
        "--ua-gec", type=Path, required=True, help="Held UA-GEC root containing data/ and python/ua_gec/."
    )
    parser.add_argument("--out", type=Path, required=True, help="Host-only output outside all Git checkouts (0700).")
    parser.add_argument(
        "--components",
        nargs="+",
        choices=tuple(COMPONENTS),
        default=["C1", "C6"],
        help="Selected WP1 components (default: C1 C6; example: C1). C6 denotes C6(a) only.",
    )
    repository = Path(__file__).resolve().parents[5]
    parser.add_argument(
        "--catalog",
        type=Path,
        default=repository / "registry/projects/open_model_data/instruction_catalog.yaml",
        help="Reviewed catalog YAML (default: registry/projects/open_model_data/instruction_catalog.yaml).",
    )
    parser.add_argument(
        "--register",
        type=Path,
        default=repository / "docs/sources/permissions-register.yaml",
        help="Permissions register YAML (default: docs/sources/permissions-register.yaml).",
    )
    output = None
    try:
        args = parser.parse_args(argv)
        output = OutputGuard(args.out, (repository,))
        print(
            json.dumps(
                run(args.command, args.ua_gec, output, args.catalog, args.register, args.components), sort_keys=True
            )
        )
        return 0
    except Exception as exc:
        error = exc if isinstance(exc, BuildError) else BuildError("component_input_invalid")
        if output:
            try:
                output.write("logs/wp1-failure.txt", traceback.format_exc().encode())
            except Exception:
                # A log-write failure must not expose the original exception
                # through Python's implicit exception chain on the console.
                error = BuildError("output_io")
        print(json.dumps(error.diagnostic(), sort_keys=True))
        return 2 if error.code == "cli_usage" else 1
    finally:
        if output:
            output.close()


if __name__ == "__main__":
    raise SystemExit(main())

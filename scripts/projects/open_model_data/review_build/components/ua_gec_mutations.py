"""Host-only WP1 must-fail fixtures, supplementary to CLI verification."""

from dataclasses import asdict, replace
from pathlib import Path

import yaml

from .. import bindings
from ..attribution import Resolver
from ..catalog import Catalog
from ..contract import canonical
from ..errors import BuildError, require
from ..gate import Gate
from ..output import OutputGuard
from ..snapshot import SnapshotReader
from . import c1_ua_gec
from .ua_gec_split import CORPUS, UaGecAttribution, UaGecFileStore, exclusion


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
        if "C6a" in config["components"]:
            mixed = next((c for c in candidates if c.component == "C6a" and c.reason == "mixed_to_c1"), None)
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

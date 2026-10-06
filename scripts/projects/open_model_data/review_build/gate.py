"""Run every mechanism gate over independent pinned inputs before writing records."""

import re
from collections import Counter, defaultdict
from dataclasses import asdict

from . import bindings
from .attribution import Resolver
from .catalog import Catalog
from .contract import Candidate, canonical, digest, record_id, values
from .errors import BuildError, require
from .metrics import measure
from .roles import SourceRoles
from .snapshot import SnapshotReader
from .transforms import transform

REASONING = re.compile(
    r"<\s*(?:think|thought|reasoning)\b|\b(?:Step|Крок)\s+\d|(?:Міркування|Reasoning|Chain.of.thought)\s*:", re.I
)
COMPONENTS = frozenset({"C1", "C2", "C3", "C4", "C5", "C6", "C7", "C9"})


def evidence_id(citation) -> str:
    return digest(canonical(asdict(citation)))


def serialize(parts, mode: str) -> str:
    require(mode in {"text", "json_array"}, "serializer")
    if mode == "json_array":
        return canonical([part.text for part in parts]).decode("utf-8")
    return "\n".join(part.text for part in parts)


class Gate:
    def __init__(
        self,
        reader: SnapshotReader,
        catalog: Catalog,
        resolver: Resolver,
        components: dict,
        compatibility: list[dict],
        corpus: dict | None = None,
    ):
        require(bool(components) and set(components) <= COMPONENTS, "component_spec")
        self.reader, self.catalog, self.resolver = reader, catalog, resolver
        self.components = components
        self.roles = SourceRoles(reader, compatibility, corpus)
        self.attributions: dict = {}

    def quote(self, candidate: Candidate) -> None:
        spec = self.components[candidate.component]
        for value in values(candidate):
            require(isinstance(value.text, str) and isinstance(value.slot, str) and bool(value.slot), "invalid_value")
            require(bool(value.citations), "uncited_value")
            for index, citation in enumerate(value.citations):
                require(bool(citation.locator.strip()), "empty_locator")
                _, field = self.reader.field(citation)
                if index == 0:
                    require(isinstance(field, str), "quote_type")
                    transformed = transform(
                        value.transform, field, spec.get("transforms", {}).get(value.transform), self.reader
                    )
                    text = transformed.text
                    if value.span is not None:
                        require(
                            len(value.span) == 2
                            and all(type(n) is int for n in value.span)
                            and 0 <= value.span[0] < value.span[1] <= len(text),
                            "quote_span",
                        )
                        text = text[value.span[0] : value.span[1]]
                    require(value.text == text, "quote_mismatch")
                self.attributions[citation] = self.resolver.resolve(citation, self.reader)

    def applicable(self, candidate: Candidate) -> tuple[str, ...]:
        spec = self.components[candidate.component]
        # Applicability assertions are themselves selectors into source rows.
        applicability_spec = spec.get("applicability", {})
        discriminating = empty_safe = False
        if candidate.component == "C2":
            if any(v.slot == "sense" and v.text.strip() for v in candidate.slots):
                discriminating = all(
                    bindings.operand(candidate, s, self.reader) == expected
                    for s, expected in applicability_spec.get("with_sense", [])
                )
                require(bool(applicability_spec.get("with_sense")), "catalog_inapplicable")
            else:
                empty_safe = all(
                    bindings.operand(candidate, s, self.reader) == expected
                    for s, expected in applicability_spec.get("without_sense", [])
                )
                require(bool(applicability_spec.get("without_sense")), "catalog_inapplicable")
        return self.catalog.applicable(candidate, discriminating, empty_safe, spec.get("slot_serializers"))

    def run(self, candidates: list[Candidate]) -> tuple[list[dict], dict]:
        try:
            return self._run(candidates)
        except BuildError:
            raise
        except Exception:
            raise BuildError("gate_input_invalid") from None

    def _run(self, candidates: list[Candidate]) -> tuple[list[dict], dict]:
        accounting, seen = {}, set()
        for component, spec in sorted(self.components.items()):
            independent = self.reader.units(spec["unit_query"])
            require(len(independent) == spec["frozen_count"], "frozen_count")
            stream = [c for c in candidates if c.component == component]
            units = [c.unit_id for c in stream]
            require(len(units) == len(set(units)), "duplicate_unit")
            require(set(units) == set(independent), "missing_unit")
            counts = Counter(c.outcome for c in stream)
            require(set(counts) <= {"accepted", "rejected", "withheld", "excluded"}, "outcome")
            require(sum(counts.values()) == len(independent), "accounting")
            require(all(c.reason in spec["reasons"][c.outcome] for c in stream), "reason_code")
            require(all(c.operation in spec["operations"] for c in stream), "operation")
            accounting[component] = {
                "counted": len(independent),
                **{o: counts[o] for o in ("accepted", "rejected", "withheld", "excluded")},
                "reasons": dict(sorted(Counter(c.reason for c in stream).items())),
            }
        require(all(c.component in self.components for c in candidates), "unknown_component")
        accepted = []
        applicability = {}
        for candidate in sorted(candidates, key=record_id):
            rid = record_id(candidate)
            require(rid not in seen, "duplicate_record")
            seen.add(rid)
            try:
                for value in values(candidate):
                    for citation in value.citations:
                        require(
                            (citation.store, citation.table, citation.source_id) in self.roles.compatibility,
                            "source_compatibility",
                        )
                if candidate.outcome not in {"accepted", "rejected"}:
                    require(bool(candidate.evidence), "outcome_evidence")
                    continue
                self.quote(candidate)
                if candidate.outcome == "rejected":
                    cited = {evidence_id(c) for v in values(candidate) for c in v.citations}
                    require(bool(candidate.evidence) and set(candidate.evidence) <= cited, "rejection_evidence")
                    continue
                require(bool(candidate.response) and any(v.text.strip() for v in candidate.response), "empty_response")
                spec = self.components[candidate.component]
                passed = bindings.check(candidate, spec["binding"], self.reader, spec.get("transforms", {}))
                contrast = [rule for rule in spec["binding"]["rules"] if rule["op"] == "contrast_pair"]
                require(candidate.component != "C7" or len(contrast) == 1, "binding_contrast")
                rejected_slot = contrast[0]["rejected"]["slot"] if contrast else ""
                for value in values(candidate):
                    for citation in value.citations:
                        self.roles.check(citation, candidate, passed, rejected_slot)
                require(not any(REASONING.search(v.text) for v in values(candidate)), "reasoning_text")
                applicability[rid] = self.applicable(candidate)
                accepted.append(candidate)
            except BuildError as exc:
                raise BuildError(
                    exc.code,
                    record_id=rid,
                    component=candidate.component,
                    row_key=values(candidate)[0].citations[0].row_key
                    if values(candidate) and values(candidate)[0].citations
                    else "",
                ) from None
        assigned = self.catalog.assign(accepted, applicability)
        snapshots = self.reader.snapshots()
        records, groups, duplicate_pairs = [], defaultdict(list), defaultdict(list)
        for candidate in sorted(accepted, key=record_id):
            rid = record_id(candidate)
            line_id = assigned[rid]
            spec = self.components[candidate.component]
            instruction = self.catalog.render(candidate, line_id, spec.get("slot_serializers"))
            context = serialize(candidate.context, spec.get("context_serializer", "text"))
            response = serialize(candidate.response, spec.get("response_serializer", "text"))
            require(not REASONING.search(instruction + "\n" + context + "\n" + response), "reasoning_text")
            provenance, output_values = {}, []
            for value in values(candidate):
                ids = []
                for citation_index, citation in enumerate(value.citations):
                    licence_ref, attribution = self.attributions[citation]
                    _, field = self.reader.field(citation)
                    trace = transform(
                        value.transform if citation_index == 0 else "verbatim",
                        field,
                        spec.get("transforms", {}).get(value.transform),
                        self.reader,
                    )
                    item = {
                        **asdict(citation),
                        **self.roles.metadata(citation),
                        "snapshot": snapshots[f"{citation.store}:{citation.table}"],
                        "span": value.span if citation_index == 0 else None,
                        "transform": value.transform if citation_index == 0 else "verbatim",
                        "licence_ref": licence_ref,
                        "attribution": attribution,
                        "dropped_lines": trace.dropped_lines,
                        "joins": trace.joins,
                    }
                    pid = digest(canonical(item))
                    provenance[pid] = item
                    ids.append(pid)
                output_values.append(
                    {"slot": value.slot, "text": value.text, "provenance_id": ids[0], "provenance_ids": ids}
                )
            record = {
                "record_id": rid,
                "component": candidate.component,
                "operation": candidate.operation,
                "catalog_line_id": line_id,
                "catalog_version": self.catalog.version,
                "status": "review_only",
                "instruction": instruction,
                "context": context,
                "response": response,
                "values": output_values,
                "provenance": provenance,
                "flags": candidate.flags,
                "tool_flags": [],
            }
            records.append(record)
            groups[candidate.component, candidate.operation].append(line_id)
            duplicate_pairs[instruction, response].append(rid)
        metrics = {}
        for component, spec in sorted(self.components.items()):
            for operation in spec["operations"]:
                report = measure(groups[component, operation], self.catalog)
                require(report["status"] != "FAIL", "instruction_concentration")
                metrics[f"{component}.{operation}"] = report
        duplicates = [sorted(ids) for ids in duplicate_pairs.values() if len(ids) > 1]
        return records, {
            "accounting": accounting,
            "metrics": metrics,
            "duplicate_groups": sorted(duplicates),
            "snapshots": self.reader.snapshots(),
            "ua_gec_files": self.reader.file_hashes(),
            "split_counts": {
                "dev_documents": len(self.roles.dev_documents),
                "test_hashes": len(self.roles.test_hashes),
            },
        }

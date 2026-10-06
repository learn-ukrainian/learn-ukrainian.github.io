"""Run every mechanism gate over independent pinned inputs before writing records."""

import re
from collections import Counter, defaultdict
from dataclasses import asdict

from . import bindings
from .attribution import Resolver
from .catalog import Catalog
from .components import admission_policy
from .contract import Candidate, canonical, digest, record_id, values
from .errors import BuildError, require
from .metrics import measure
from .roles import SourceRoles
from .snapshot import SnapshotReader
from .transforms import transform

REASONING = re.compile(
    r"<\s*(?:think|thought|reasoning)\b|\b(?:Step|Крок)\s+\d|(?:Міркування|Reasoning|Chain.of.thought)\s*:", re.I
)
COMPONENTS = frozenset({"C1", "C2", "C3", "C4", "C5", "C6", "C6a", "C6b", "C7", "C9"})


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
    ):
        require(bool(components) and set(components) <= COMPONENTS, "component_spec")
        self.reader, self.catalog, self.resolver = reader, catalog, resolver
        self.components = components
        for spec in components.values():
            if "operation_specs" in spec:
                require(set(spec["operation_specs"]) == set(spec["operations"]), "operation_spec")
                for operation in spec["operation_specs"].values():
                    require({"binding", "unit_query", "frozen_count", "unit_id"} <= set(operation), "operation_spec")
        compatibility, corpus = admission_policy(components)
        self.roles = SourceRoles(reader, compatibility, corpus)
        self.attributions: dict = {}

    def spec(self, candidate: Candidate) -> dict:
        """Operation declarations override the component's common policies."""
        require(candidate.component in self.components, "unknown_component")
        base = self.components[candidate.component]
        if "operation_specs" in base:
            require(candidate.operation in base["operation_specs"], "operation")
            return {**base, **base["operation_specs"][candidate.operation]}
        return base

    def quote(self, candidate: Candidate) -> None:
        spec = self.spec(candidate)
        for value in values(candidate):
            require(isinstance(value.text, str) and isinstance(value.slot, str) and bool(value.slot), "invalid_value")
            require(bool(value.citations), "uncited_value")
            for index, citation in enumerate(value.citations):
                require(bool(citation.locator.strip()), "empty_locator")
                _, field = self.reader.field(citation)
                if index == 0:
                    require(isinstance(field, str), "quote_type")
                    transformed = transform(
                        value.transform, field, spec.get("transforms", {}).get(value.transform), self.reader, citation
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
        spec = self.spec(candidate)
        # Applicability assertions are themselves selectors into source rows.
        applicability_spec = spec.get("applicability", {})
        declared = self.catalog.variants(candidate)
        serializers = spec.get("slot_serializers")
        variants = set()
        if declared:
            require(set(applicability_spec) == declared, "applicability_spec")
            for variant in self.catalog.variant_slots(candidate, serializers):
                predicates = applicability_spec[variant]
                require(isinstance(predicates, list) and bool(predicates), "applicability_spec")
                results = []
                for predicate in predicates:
                    if isinstance(predicate, dict):
                        require(set(predicate) == {"query", "parameters", "expected"}, "applicability_spec")
                        query = dict(predicate["query"])
                        query["parameters"] = [
                            bindings.operand(candidate, s, self.reader) for s in predicate["parameters"]
                        ]
                        results.append(self.reader.query_values(query) == predicate["expected"])
                    else:
                        require(isinstance(predicate, list) and len(predicate) == 2, "applicability_spec")
                        selector, expected = predicate
                        results.append(bindings.operand(candidate, selector, self.reader) == expected)
                    if not results[-1]:
                        break
                if all(results):
                    variants.add(variant)
        return self.catalog.applicable(candidate, serializers, variants=variants)

    def unit_id(self, candidate: Candidate) -> str:
        spec = self.spec(candidate).get("unit_id", {})
        encoding = spec.get("format", "joined")
        require(encoding in {"joined", "citation.v1"} and bool(spec.get("primary")), "unit_id_spec")
        require(encoding != "joined" or isinstance(spec.get("separator"), str), "unit_id_spec")
        parts = []
        for part in spec["primary"]:
            for ref in bindings.expand(candidate, part["selector"]):
                require(ref.get("citation", 0) == 0 and "field" not in ref, "unit_id_spec")
                value = bindings.select(candidate, ref)
                require(bool(value.citations), "uncited_value")
                citation = bindings.citation_for(candidate, ref)
                require((citation.store, citation.table) == (part["store"], part["table"]), "unit_id_mismatch")
                self.reader.row(citation)
                require(type(part.get("span", False)) is bool, "unit_id_spec")
                if encoding == "citation.v1":
                    require("key" not in part, "unit_id_spec")
                    identity = [citation.store, citation.table, citation.row_key]
                else:
                    keys = dict(pair.split("=", 1) for pair in citation.row_key.split(";"))
                    require("key" not in part or part["key"] in keys, "unit_id_spec")
                    identity = [keys[part["key"]] if "key" in part else citation.row_key]
                if part.get("span"):
                    _, field = self.reader.field(citation)
                    source = transform(
                        value.transform,
                        field,
                        self.spec(candidate).get("transforms", {}).get(value.transform),
                        self.reader,
                        citation,
                    ).text
                    require(
                        value.span is not None
                        and len(value.span) == 2
                        and all(type(n) is int for n in value.span)
                        and 0 <= value.span[0] < value.span[1] <= len(source),
                        "quote_span",
                    )
                    identity.append(list(value.span))
                parts.append(
                    identity
                    if encoding == "citation.v1"
                    else spec["separator"].join(canonical(p).decode() if isinstance(p, list) else p for p in identity)
                )
        return canonical(parts).decode() if encoding == "citation.v1" else spec["separator"].join(parts)

    def run(self, candidates: list[Candidate]) -> tuple[list[dict], dict]:
        try:
            return self._run(candidates)
        except BuildError:
            raise
        except Exception:
            raise BuildError("gate_input_invalid") from None

    def _run(self, candidates: list[Candidate]) -> tuple[list[dict], dict]:
        accounting, operation_accounting, seen = {}, {}, set()
        for component, spec in sorted(self.components.items()):
            domains = spec.get("operation_specs", {None: spec})
            total, counts, reasons = 0, Counter(), Counter()
            stream = [c for c in candidates if c.component == component]
            require(all(c.operation in spec["operations"] for c in stream), "operation")
            for operation, overrides in domains.items():
                domain = {**spec, **overrides}
                independent = self.reader.units(domain["unit_query"])
                require(len(independent) == domain["frozen_count"], "frozen_count")
                subset = [c for c in stream if operation is None or c.operation == operation]
                units = [c.unit_id for c in subset]
                require(len(units) == len(set(units)), "duplicate_unit")
                require(set(units) == set(independent), "missing_unit")
                outcomes = Counter(c.outcome for c in subset)
                require(set(outcomes) <= {"accepted", "rejected", "withheld", "excluded"}, "outcome")
                require(sum(outcomes.values()) == len(independent), "accounting")
                require(all(c.reason in domain["reasons"][c.outcome] for c in subset), "reason_code")
                total += len(independent)
                counts.update(outcomes)
                reasons.update(c.reason for c in subset)
                if operation is not None:
                    operation_accounting[f"{component}.{operation}"] = {
                        "counted": len(independent),
                        **{o: outcomes[o] for o in ("accepted", "rejected", "withheld", "excluded")},
                        "reasons": dict(sorted(Counter(c.reason for c in subset).items())),
                    }
            accounting[component] = {
                "counted": total,
                **{o: counts[o] for o in ("accepted", "rejected", "withheld", "excluded")},
                "reasons": dict(sorted(reasons.items())),
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
                require(candidate.unit_id == self.unit_id(candidate), "unit_id_mismatch")
                if candidate.outcome not in {"accepted", "rejected"}:
                    require(bool(candidate.evidence), "outcome_evidence")
                    continue
                self.quote(candidate)
                if candidate.outcome == "rejected":
                    cited = {evidence_id(c) for v in values(candidate) for c in v.citations}
                    require(bool(candidate.evidence) and set(candidate.evidence) <= cited, "rejection_evidence")
                    continue
                require(bool(candidate.response) and any(v.text.strip() for v in candidate.response), "empty_response")
                spec = self.spec(candidate)
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
            spec = self.spec(candidate)
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
                        citation,
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
            "operation_accounting": operation_accounting,
            "metrics": metrics,
            "duplicate_groups": sorted(duplicates),
            "snapshots": self.reader.snapshots(),
            "ua_gec_files": self.reader.file_hashes(),
            "repository_configs": self.reader.repository_config_hashes(),
            "split_counts": {
                "dev_documents": len(self.roles.dev_documents),
                "test_hashes": len(self.roles.test_hashes),
            },
        }

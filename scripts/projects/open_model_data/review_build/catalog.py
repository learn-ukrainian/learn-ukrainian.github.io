"""Reviewed catalog interpolation and deterministic balanced assignment."""

import re
from collections import defaultdict
from string import Formatter

from .contract import Candidate, canonical, record_id
from .errors import BuildError, require

PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


class Catalog:
    @staticmethod
    def component_id(component: str) -> str:
        return "C6" if component in {"C6a", "C6b"} else component

    def __init__(self, data: dict):
        require(data.get("schema_version") == "instruction-catalog.v1", "catalog_schema")
        require(data.get("status") in {"reviewed", "reviewed_rb1", "approved", "rb1_approved"}, "catalog_unreviewed")
        self.data = data
        self.version = data["version"]
        self.lines = {}
        for component, entry in data["components"].items():
            for line in entry["instructions"]:
                require(line["id"] not in self.lines, "catalog_duplicate")
                require(set(PLACEHOLDER.findall(line["template"])) == set(line["slots"]), "catalog_slots")
                # No conversions, attribute/index access, format specifiers or nested interpolation.
                for _, name, spec, conversion in Formatter().parse(line["template"]):
                    require(name is None or (name in line["slots"] and not spec and not conversion), "catalog_slots")
                self.lines[line["id"]] = (component, line)

    @staticmethod
    def rendered_slots(candidate: Candidate, serializers: dict | None = None) -> dict[str, str]:
        slots = {v.slot: v.text for v in candidate.slots}
        require(len(slots) == len(candidate.slots), "duplicate_slot")
        for slot, definition in (serializers or {}).items():
            require(
                candidate.component == "C2" and slot == "slot" and definition.get("id") == "c2-header-cells.v2",
                "serializer",
            )
            require(slot not in slots and set(definition) == {"id", "section", "row", "column"}, "serializer")
            try:

                def cells(names):
                    if isinstance(names, dict):
                        require(set(names) == {"prefix"} and isinstance(names["prefix"], str), "serializer")
                        selected = {name: text for name, text in slots.items() if name.startswith(names["prefix"])}
                        ordered = [names["prefix"] + str(i) for i in range(len(selected))]
                        require(set(ordered) == set(selected), "serializer")
                        return [selected[name] for name in ordered]
                    return [slots[name] for name in names]

                section = cells(definition["section"])
                row_name = definition["row"]
                if isinstance(row_name, dict):
                    require(set(row_name) == {"slot", "optional"} and row_name["optional"] is True, "serializer")
                    row = slots.get(row_name["slot"], "")
                else:
                    row = slots[row_name] if row_name is not None else ""
                column = cells(definition["column"])
            except KeyError:
                raise BuildError("catalog_inapplicable") from None
            require(
                all(isinstance(s, str) for s in [*section, row, *column])
                and any(s.strip() for s in [*section, row, *column]),
                "catalog_inapplicable",
            )
            slots[slot] = canonical([section, row, column]).decode()
        return slots

    def variant_slots(self, candidate: Candidate, serializers: dict | None = None) -> set[str]:
        """Variant names and presence predicates are declared by catalog lines.

        Varying slots must exist as strings even for the empty variant. A
        populated varying slot cannot be silently hidden by another variant.
        Remaining semantic predicates are authenticated by the component gate.
        """
        lines = [
            line
            for component, line in self.lines.values()
            if component == self.component_id(candidate.component)
            and line["operation"] == candidate.operation
            and line.get("sense_variant")
        ]
        if not lines:
            return set()
        slot_sets = [set(line["slots"]) for line in lines]
        varying = set.union(*slot_sets) - set.intersection(*slot_sets)
        slots = self.rendered_slots(candidate, serializers)
        require(all(isinstance(slots.get(s), str) for s in varying), "catalog_inapplicable")
        present = {s for s in varying if slots[s].strip()}
        return {line["sense_variant"] for line in lines if set(line["slots"]) & varying == present}

    def variants(self, candidate: Candidate) -> set[str]:
        variants = {
            line["sense_variant"]
            for component, line in self.lines.values()
            if component == self.component_id(candidate.component)
            and line["operation"] == candidate.operation
            and line.get("sense_variant")
        }
        entry = self.data["components"].get(self.component_id(candidate.component), {})
        declarations = entry.get(candidate.operation + "_contract", {}).get("applicability")
        if declarations is not None:
            require(variants <= set(declarations), "catalog_applicability")
        return variants

    def applicable(
        self,
        candidate: Candidate,
        serializers: dict | None = None,
        *,
        variants: set[str] | None = None,
    ) -> tuple[str, ...]:
        slots = self.rendered_slots(candidate, serializers)
        declared = self.variants(candidate)
        eligible = self.variant_slots(candidate, serializers)
        if declared:
            require(variants is not None and variants <= declared, "catalog_inapplicable")
            eligible &= variants
            require(len(eligible) == 1, "catalog_inapplicable")
        result = []
        for name, (component, line) in sorted(self.lines.items()):
            if component != self.component_id(candidate.component) or line["operation"] != candidate.operation:
                continue
            variant = line.get("sense_variant")
            if variant and variant not in eligible:
                continue
            if not all(isinstance(slots.get(s), str) and slots[s].strip() for s in line["slots"]):
                continue
            if any("«{" + s + "}»" in line["template"] and re.search("[«»]", slots[s]) for s in line["slots"]):
                continue
            result.append(name)
        require(bool(result), "catalog_inapplicable")
        return tuple(result)

    def assign(self, candidates: list[Candidate], applicability: dict[str, tuple[str, ...]]) -> dict[str, str]:
        groups = defaultdict(list)
        for candidate in candidates:
            rid = record_id(candidate)
            groups[candidate.component, candidate.operation, applicability[rid]].append(rid)
        result = {}
        for (_, _, lines), ids in sorted(groups.items()):
            for index, rid in enumerate(sorted(ids)):
                result[rid] = lines[index % len(lines)]
        return result

    def render(self, candidate: Candidate, line_id: str, serializers: dict | None = None) -> str:
        component, line = self.lines[line_id]
        require(
            component == self.component_id(candidate.component) and line["operation"] == candidate.operation,
            "catalog_line",
        )
        slots = self.rendered_slots(candidate, serializers)
        # re.sub does not revisit source values containing braces.
        try:
            return PLACEHOLDER.sub(lambda m: slots[m[1]], line["template"])
        except KeyError:
            raise BuildError("catalog_inapplicable") from None

    def template(self, line_id: str) -> str:
        return PLACEHOLDER.sub("SLOT", self.lines[line_id][1]["template"])

"""Reviewed catalog interpolation and deterministic balanced assignment."""

import re
from collections import defaultdict
from string import Formatter

from .contract import Candidate, canonical, record_id
from .errors import BuildError, require

PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


class Catalog:
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
                section = [slots[name] for name in definition["section"]]
                row = slots[definition["row"]] if definition["row"] is not None else ""
                column = [slots[name] for name in definition["column"]]
            except KeyError:
                raise BuildError("catalog_inapplicable") from None
            require(
                all(isinstance(s, str) for s in [*section, row, *column])
                and any(s.strip() for s in [*section, row, *column]),
                "catalog_inapplicable",
            )
            slots[slot] = canonical([section, row, column]).decode()
        return slots

    def applicable(
        self,
        candidate: Candidate,
        discriminating: bool = False,
        empty_safe: bool = False,
        serializers: dict | None = None,
    ) -> tuple[str, ...]:
        slots = self.rendered_slots(candidate, serializers)
        sense = slots.get("sense")
        if candidate.component == "C2":
            require(isinstance(sense, str), "catalog_inapplicable")
            require(discriminating if sense.strip() else empty_safe, "catalog_inapplicable")
        result = []
        for name, (component, line) in sorted(self.lines.items()):
            if component != candidate.component or line["operation"] != candidate.operation:
                continue
            variant = line.get("sense_variant")
            if variant and variant != ("with_sense" if sense and sense.strip() else "without_sense"):
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
        require(component == candidate.component and line["operation"] == candidate.operation, "catalog_line")
        slots = self.rendered_slots(candidate, serializers)
        # re.sub does not revisit source values containing braces.
        try:
            return PLACEHOLDER.sub(lambda m: slots[m[1]], line["template"])
        except KeyError:
            raise BuildError("catalog_inapplicable") from None

    def template(self, line_id: str) -> str:
        return PLACEHOLDER.sub("SLOT", self.lines[line_id][1]["template"])

"""Register resolution is provenance, not a copyright permission gate.

Real-source adapters ship with their component. An adapter must affirm that it
mapped the complete bibliographic form; generic interpolation is not admission.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from .contract import Citation
from .errors import BuildError, require
from .snapshot import SnapshotReader


@dataclass(frozen=True)
class Attribution:
    bibliography: str
    mapped_form: str
    instruction_form: bool = False


class AttributionAdapter(Protocol):
    def resolve(self, form: str, citation: Citation, row: Mapping, reader: SnapshotReader) -> Attribution: ...


class SyntheticAdapter:
    """Only maps explicitly marked synthetic register forms (for framework tests)."""

    def resolve(self, form: str, citation: Citation, row: Mapping, reader: SnapshotReader) -> Attribution:
        require(form.startswith("SYNTHETIC "), "attribution_unresolved")
        return Attribution(form, form, bool(re.search(r"\b(?:cite|insert|supply|fill)\b", form, re.I)))


class Resolver:
    def __init__(self, register: dict, adapters: Mapping[str, AttributionAdapter]):
        entries = register["sources"]
        self.entries = {entry["id"]: entry for entry in entries}
        require(len(self.entries) == len(entries), "register_duplicate")
        self.adapters = dict(adapters)

    def resolve(self, citation: Citation, reader: SnapshotReader) -> tuple[str, str]:
        try:
            entry = self.entries[citation.source_id]
            form = entry["citation"]["form"]
            licence = entry["terms"]["licence"]["name"]
            require(
                isinstance(form, str) and bool(form.strip()) and isinstance(licence, str) and bool(licence.strip()),
                "attribution_unresolved",
            )
            require(citation.source_id in self.adapters, "attribution_unresolved")
            result = self.adapters[citation.source_id].resolve(form, citation, reader.row(citation), reader)
            require(result.mapped_form == form and not result.instruction_form, "attribution_unresolved")
            require(
                bool(result.bibliography.strip()) and not re.search(r"<[^>]*>", result.bibliography),
                "attribution_unresolved",
            )
            require(not re.search(r"<[^>]*>", form), "attribution_unresolved")
            require(bool(citation.locator.strip()), "locator_unavailable")
            return (
                f"permissions-register.yaml#{citation.source_id}; {licence}",
                result.bibliography + "; " + citation.locator,
            )
        except (KeyError, TypeError):
            raise BuildError("attribution_unresolved") from None

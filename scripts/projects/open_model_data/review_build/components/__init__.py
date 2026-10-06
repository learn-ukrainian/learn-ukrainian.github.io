"""Closed, lazy component registry. Request data never names executable code."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from importlib import import_module
from typing import Protocol

from ..attribution import AttributionAdapter
from ..contract import Candidate
from ..errors import BuildError, require
from ..snapshot import FileStore, SnapshotReader

REGISTRY = {
    "C1": "c1",
    "C2": "c2",
    "C3": "c3",
    "C4": "c4",
    "C5": "c5",
    "C6a": "c6a",
    "C6b": "c6b",
    "C7": "c7",
    "C9": "c9",
}


@dataclass(frozen=True)
class ComponentContext:
    """Extraction and independent verification share one read transaction."""

    reader: SnapshotReader
    request: dict


class Component(Protocol):
    # spec uses the existing component/operation_specs contract, including reasons.
    spec: dict
    adapters: Mapping[str, AttributionAdapter]
    files: Mapping[str, FileStore]

    def iter_candidates(self, ctx: ComponentContext) -> Iterable[Candidate]: ...


def load_components(
    ids: Iterable[str], *, _test_overrides: Mapping[str, Component] | None = None
) -> dict[str, Component]:
    """Load only literal registry targets; overrides are an in-process test seam."""
    ids = tuple(ids)
    require(bool(ids) and set(ids) <= REGISTRY.keys(), "unknown_component")
    result = {}
    for component in ids:
        if _test_overrides is not None and component in _test_overrides:
            result[component] = _test_overrides[component]
            continue
        target = f"{__name__}.{REGISTRY[component]}"
        try:
            module = import_module(target)
        except ModuleNotFoundError as exc:
            if exc.name != target:
                raise
            raise BuildError("component_unavailable", component=component) from None
        require(hasattr(module, "COMPONENT"), "component_contract")
        result[component] = module.COMPONENT
    return result


def merge_adapters(*groups: Mapping[str, AttributionAdapter]) -> dict[str, AttributionAdapter]:
    """Shared identical adapter objects are safe; competing implementations refuse."""
    result = {}
    for group in groups:
        for source, adapter in group.items():
            require(source not in result or result[source] is adapter, "adapter_conflict")
            result[source] = adapter
    return result

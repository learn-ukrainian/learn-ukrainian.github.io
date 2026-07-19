"""Validation and alias resolution for the v1 endpoint registry."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "config" / "fleet_communications.yaml"
_STATES = frozenset({"live", "draining", "retired", "local_only"})


@dataclass(frozen=True, slots=True)
class Endpoint:
    name: str
    aliases: tuple[str, ...]
    state: str
    successor: str | None
    transports: tuple[str, ...]
    completion_evidence: tuple[str, ...]
    default_ttl_seconds: int
    retry_class: str
    concurrency_limit: int
    formal_review_eligible: bool
    model_family_resolver: str


@dataclass(frozen=True, slots=True)
class EndpointRegistry:
    version: int
    endpoints: tuple[Endpoint, ...]

    def resolve(self, recipient: str) -> tuple[Endpoint, str]:
        aliases = {alias: endpoint for endpoint in self.endpoints for alias in endpoint.aliases}
        try:
            endpoint = aliases[recipient]
        except KeyError as exc:
            raise ValueError(f"Unknown fleet endpoint: {recipient}") from exc
        if endpoint.state == "retired":
            if not endpoint.successor:
                raise ValueError(f"Retired endpoint {endpoint.name} has no successor")
            return aliases[endpoint.successor], endpoint.name
        return endpoint, endpoint.name


def load_endpoint_registry(path: Path = REGISTRY_PATH) -> EndpointRegistry:
    """Load the immutable v1 defaults; future behavior consumes a snapshot."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("version") != 1:
        raise ValueError("fleet communications registry must have version: 1")
    parsed: list[Endpoint] = []
    seen_aliases: set[str] = set()
    for item in raw.get("endpoints", []):
        if not isinstance(item, dict):
            raise ValueError("Each endpoint registry entry must be an object")
        state = item.get("state")
        name = item.get("name")
        aliases = tuple(item.get("aliases", []))
        if not isinstance(name, str) or not name or state not in _STATES or name not in aliases:
            raise ValueError(f"Invalid endpoint registry entry: {item!r}")
        if seen_aliases.intersection(aliases):
            raise ValueError(f"Duplicate endpoint alias in {name}")
        seen_aliases.update(aliases)
        successor = item.get("successor")
        if state == "retired" and (not isinstance(successor, str) or not successor):
            raise ValueError(f"Retired endpoint {name} requires a successor")
        parsed.append(
            Endpoint(
                name=name,
                aliases=aliases,
                state=state,
                successor=successor,
                transports=tuple(item.get("transports", [])),
                completion_evidence=tuple(item.get("completion_evidence", [])),
                default_ttl_seconds=int(item["default_ttl_seconds"]),
                retry_class=str(item["retry_class"]),
                concurrency_limit=int(item["concurrency_limit"]),
                formal_review_eligible=bool(item["formal_review_eligible"]),
                model_family_resolver=str(item["model_family_resolver"]),
            )
        )
    registry = EndpointRegistry(version=1, endpoints=tuple(parsed))
    for endpoint in registry.endpoints:
        if endpoint.successor:
            registry.resolve(endpoint.successor)
    return registry

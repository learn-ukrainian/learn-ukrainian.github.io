"""Restrict Hygiene imports using dependency metadata and resolved module paths."""

import importlib.abc
import importlib.machinery
from pathlib import Path


class HygieneImportsOnly(importlib.abc.MetaPathFinder):
    def __init__(
        self,
        allowed: set[str],
        roots: tuple[Path, ...],
        site_roots: list[Path],
        missing: str = "",
    ) -> None:
        self.allowed = allowed
        self.roots = tuple(root.resolve() for root in roots)
        self.site_roots = [root.resolve() for root in site_roots]
        self.missing = missing

    def find_spec(self, fullname, path=None, target=None):
        top = fullname.partition(".")[0]
        if top == self.missing:
            raise ModuleNotFoundError(f"No module named '{fullname}'", name=fullname)
        if top in self.allowed:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        locations = (
            [spec.origin] if spec and spec.origin else list(spec.submodule_search_locations or ()) if spec else []
        )
        resolved = [Path(location).resolve() for location in locations]
        # CI's .venv may be inside the repo; installed modules are not local.
        if resolved and all(
            any(location.is_relative_to(root) for root in self.roots)
            and not any(location.is_relative_to(root) for root in self.site_roots)
            for location in resolved
        ):
            return spec
        raise ModuleNotFoundError(f"Hygiene dependency not declared: '{fullname}'", name=fullname)

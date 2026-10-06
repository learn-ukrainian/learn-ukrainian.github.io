"""Shared registration for C1/C6a; each CLI run opens fresh held inputs."""

from pathlib import Path

from scripts.common.repo_root import main_checkout_root

from ..errors import require
from .ua_gec_split import UaGecAttribution, UaGecFileStore

FILES = {"ua-gec": UaGecFileStore()}
ADAPTERS = {"ua_gec": UaGecAttribution()}


def held_root():
    """Reader code comes from the held repository, never a request path."""
    return main_checkout_root(Path(__file__).resolve().parents[5]) / "data/ua-gec"


class UaGecComponent:
    files = FILES
    adapters = ADAPTERS

    def mutation_fixtures(self, ctx, candidates, gate):
        """Generate this component's real-row fixtures only during verify."""
        from .ua_gec_mutations import component_mutations

        return component_mutations(ctx, candidates, gate)

    def __init__(self, module):
        self.module = module

    @property
    def spec(self):
        spec = self.module.spec()
        spec["operation_specs"] = {
            spec["operations"][0]: {key: spec.pop(key) for key in ("unit_query", "unit_id", "frozen_count", "binding")}
        }
        return spec

    def iter_candidates(self, ctx):
        root = ctx.request.get("ua_gec", {}).get("root")
        require(isinstance(root, str) and Path(root).is_absolute(), "component_input")
        approved_root = held_root().resolve()
        require(Path(root).resolve() == approved_root, "component_input")
        store = ctx.reader.files["ua-gec"]
        if store is FILES["ua-gec"]:
            store = UaGecFileStore(approved_root)
            ctx.reader.files["ua-gec"] = store
        require(store.root == Path(root).resolve(), "component_input")
        query = self.module.spec()["unit_query"]
        for row in ctx.reader.all_rows("ua-gec", "corpus"):
            if row["split"] != query["split"] or row["layer"] != query["layer"]:
                continue
            if query["selection"] == "contains_calque" and "F/Calque" not in row["edits"]:
                continue
            yield self.module.candidate(row, store.splits)

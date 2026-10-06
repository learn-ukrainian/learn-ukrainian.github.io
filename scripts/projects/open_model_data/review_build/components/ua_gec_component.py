"""Shared registration for C1/C6a; each CLI run opens fresh held inputs."""

from pathlib import Path

from ..errors import require
from .ua_gec_split import CORPUS, UaGecAttribution, UaGecFileStore

FILES = {"ua-gec": UaGecFileStore()}
ADAPTERS = {"ua_gec": UaGecAttribution()}


class UaGecComponent:
    files = FILES
    adapters = ADAPTERS

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
        require(ctx.request.get("corpus") == CORPUS, "component_corpus")
        root = ctx.request.get("ua_gec", {}).get("root")
        require(isinstance(root, str) and Path(root).is_absolute(), "component_input")
        store = ctx.reader.files["ua-gec"]
        if store is FILES["ua-gec"]:
            store = UaGecFileStore(Path(root))
            ctx.reader.files["ua-gec"] = store
        require(store.root == Path(root).resolve(), "component_input")
        compatibility = [row for row in ctx.request["compatibility"] if row["store"] == "ua-gec"]
        require(compatibility == store.compatibility(), "source_compatibility")
        query = self.module.spec()["unit_query"]
        for row in ctx.reader.all_rows("ua-gec", "corpus"):
            if row["split"] != query["split"] or row["layer"] != query["layer"]:
                continue
            if query["selection"] == "contains_calque" and "F/Calque" not in row["edits"]:
                continue
            yield self.module.candidate(row, store.splits)

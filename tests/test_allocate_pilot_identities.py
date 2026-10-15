"""Append-only holding-sense allocation of the pilot registry (schema.md §6, §13; #8981).

The holding step adds one `unsplit` sense to each pilot card whose relation units cannot be aligned and that has
none, under its own build id, and never changes an existing identity or event. The obligations come from the
assembler's own placement check over the synthetic world of tests/test_word_card_assembly.py.
"""

import copy
import json
from pathlib import Path

import pytest

from scripts.atlas import allocate_pilot_identities as allocator
from scripts.atlas import word_card_foundation as foundation
from scripts.guardrails import worktree_containment as containment
from tests.test_word_card_assembly import HOLDING_BUILD, MANIFEST_SHA, build_world

ROOT = Path(__file__).resolve().parents[1]
ADVISED_HOLDING_CARDS = {"wc_02a5cjxcpbcf", "wc_cvkw5nzdg00n", "wc_bgr5q9c06wxg"}


def seed_registry(world):
    """The world's registry as the reviewed allocation left it: no holding senses, version 2."""
    registry = copy.deepcopy({"schema_version": "1", "registry_version": 2, "entries": world.entries,
                              "source_records": world.sr, "events": world.events})
    holding = {e["to"][0] for e in registry["events"] if e["build_id"] == HOLDING_BUILD}
    for entry in registry["entries"]:
        entry["senses"] = [s for s in entry["senses"] if s["sense_id"] not in holding]
    registry["events"] = [e for e in registry["events"] if e["build_id"] != HOLDING_BUILD]
    return registry


def manifest_of(world):
    return {"manifest_sha256": MANIFEST_SHA, "rules_version": "rules-v1-draft", "normaliser_version": "norm-v1",
            "selection": {"units": world.units, "source_records": world.records}}


class Minter:
    def __init__(self, registry):
        self.registry = registry
        self.number = 0

    def mint(self, prefix):
        self.number += 1
        return prefix + str(self.number).rjust(12, "0")

    def event(self, kind, target, evidence, build_id):
        number = max(int(e["event_id"][3:]) for e in self.registry["events"]) + 1
        self.registry["events"].append({"event_id": f"ie_{number:04d}", "kind": kind, "build_id": build_id,
                                        "to": [target], "evidence": foundation.canonical(evidence).decode()})


@pytest.fixture(scope="module")
def world():
    return build_world()


@pytest.fixture
def allocated(world):
    """(manifest, reviewed v2, obligations, v3 after one append)."""
    manifest, allocation = manifest_of(world), seed_registry(world)
    needs = allocator.holding_obligations(manifest, allocation, world.sources)
    registry = copy.deepcopy(allocation)
    minter = Minter(registry)
    assert allocator.append_holding(registry, manifest, needs, minter.mint, minter.event) == 1
    registry["registry_version"] = allocation["registry_version"] + 1
    return manifest, allocation, needs, registry


def test_obligations_come_from_the_assembler_placement_rule(world, allocated):
    _manifest, _allocation, needs, _registry = allocated
    alpha = world.entries[0]["card_id"]  # two active senses and one synonym group
    assert needs == {alpha: ["ulif:section:101"]}


def test_append_is_append_only_and_idempotent(allocated):
    manifest, allocation, needs, registry = allocated
    assert allocator.holding_check(registry, manifest, needs, allocation) == 1
    assert registry["events"][:len(allocation["events"])] == allocation["events"]
    (card_id,) = needs
    entry = next(e for e in registry["entries"] if e["card_id"] == card_id)
    assert [s["state"] for s in entry["senses"]] == ["active", "active", "unsplit"]
    evidence = json.loads(registry["events"][-1]["evidence"])
    assert evidence["held_units"] == ["ulif:section:101"] and evidence["state"] == "unsplit"
    again = copy.deepcopy(registry)
    minter = Minter(again)
    assert allocator.append_holding(again, manifest, needs, minter.mint, minter.event) == 0
    assert again == registry
    sense_ids = [s["sense_id"] for e in registry["entries"] for s in e["senses"]]
    assert len(sense_ids) == len(set(sense_ids))


def test_allocation_alone_is_a_valid_prefix_without_holding_senses(allocated):
    manifest, allocation, _needs, _registry = allocated
    assert allocator.holding_check(allocation, manifest, {}, allocation) == 0


@pytest.mark.parametrize("tamper", [
    "changed_seed_sense", "extra_holding", "missing_holding", "version", "foreign_event", "evidence",
    "source_records", "rewritten_history"])
def test_holding_check_refuses_anything_but_the_exact_append(allocated, tamper):
    manifest, allocation, needs, registry = allocated
    registry = copy.deepcopy(registry)
    (card_id,) = needs
    entry = next(e for e in registry["entries"] if e["card_id"] == card_id)
    other = next(e for e in registry["entries"] if e["card_id"] != card_id and e["senses"])
    if tamper == "changed_seed_sense":
        entry["senses"][0]["state"] = "unsplit"
    elif tamper == "extra_holding":
        other["senses"].append({"sense_id": "ws_" + "9" * 12, "order": len(other["senses"]) + 1, "state": "unsplit"})
    elif tamper == "missing_holding":
        entry["senses"].pop()
    elif tamper == "version":
        registry["registry_version"] += 1
    elif tamper == "foreign_event":
        registry["events"].append(dict(registry["events"][-1], event_id="ie_9999", build_id="other-build"))
    elif tamper == "evidence":
        evidence = json.loads(registry["events"][-1]["evidence"])
        registry["events"][-1]["evidence"] = foundation.canonical(dict(evidence, held_units=[])).decode()
    elif tamper == "source_records":
        registry["source_records"] = registry["source_records"][1:]
    elif tamper == "rewritten_history":
        registry["events"][0] = dict(registry["events"][0], evidence="{}")
    with pytest.raises((AssertionError, KeyError, StopIteration)):
        allocator.holding_check(registry, manifest, needs, allocation)


def test_apply_never_regenerates_an_existing_allocation():
    with pytest.raises(AssertionError, match="--apply would replace"):
        allocator.run(apply=True)


def test_registry_writes_are_refused_in_the_primary_checkout():
    primary = containment.resolve_main_root(ROOT)
    with pytest.raises(AssertionError, match="primary checkout"):
        allocator.require_writable(primary / "registry" / "atlas" / "identity" / "registry.json")
    allocator.require_writable(ROOT / "batch_state" / "reports" / "probe.json")  # ignored scratch: allowed


def test_committed_registry_is_the_reviewed_allocation_plus_three_holding_senses():
    registry = foundation.load(ROOT / "registry/atlas/identity/registry.json")
    manifest = foundation.load(ROOT / "registry/atlas/pilot/pilot-v1.json")
    allocation = allocator.reviewed_allocation(registry, manifest)  # proved by the pinned v2 content digest
    holding_build = allocator.HOLDING_BUILD_PREFIX + manifest["manifest_sha256"]
    assert registry["registry_version"] == allocation["registry_version"] + 1 == 3
    assert registry["events"][:len(allocation["events"])] == allocation["events"]
    assert registry["source_records"] == allocation["source_records"]
    appended = registry["events"][len(allocation["events"]):]
    assert all(e["kind"] == "sense_mint" and e["build_id"] == holding_build for e in appended)
    holders = {e["card_id"] for old, e in zip(allocation["entries"], registry["entries"], strict=True)
               if e["senses"] != old["senses"]}
    assert holders == ADVISED_HOLDING_CARDS
    assert sum(len(json.loads(e["evidence"])["held_units"]) for e in appended) == 7
    foundation.allocation_check(manifest, registry)


def test_reviewed_allocation_refuses_a_changed_prefix():
    registry = foundation.load(ROOT / "registry/atlas/identity/registry.json")
    manifest = foundation.load(ROOT / "registry/atlas/pilot/pilot-v1.json")
    registry["entries"][0]["state"] = "retired"
    with pytest.raises(AssertionError, match="reviewed pilot allocation"):
        allocator.reviewed_allocation(registry, manifest)


def host_stores():
    try:
        from scripts.atlas import word_card_assembly as wa

        return [wa.store_path(name, None) for name in ("sources", "vesum")]
    except Exception:  # an unavailable store binding means the host-only test cannot run here
        return None


@pytest.mark.skipif(not host_stores() or not all(p.exists() for p in host_stores()), reason="held sources are host-only")
def test_host_verify_and_append_are_no_ops_on_the_committed_registry(monkeypatch, capsys):
    """The committed v3 registry verifies, and a further append finds every obligation met (idempotent)."""
    monkeypatch.chdir(ROOT)
    sources, vesum = host_stores()
    path = ROOT / "registry/atlas/identity/registry.json"
    before = path.read_bytes()
    for append in (False, True):
        allocator.run(False, append, sources, vesum)
        report = json.loads(capsys.readouterr().out)
        assert (report["registry_version"], report["holding_senses"], report["holding_appended_now"]) == (3, 3, 0)
        assert report["holding_obligations"] == 3 and report["holding_obligations_unmet"] == 0
        assert report["allocated_pilot_senses"] == 155 and report["pilot_units"] == 150
    assert path.read_bytes() == before

"""Append-only holding-sense allocation of the pilot registry (schema.md §6, §13; #8981).

The holding step adds one `unsplit` sense to each pilot card whose relation units cannot be aligned and that has
none, under its own build id, and never changes an existing identity or event. The obligations come from the
assembler's own placement check over the synthetic world of tests/test_word_card_assembly.py.
"""

import copy
import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from scripts.atlas import allocate_pilot_identities as allocator
from scripts.atlas import word_card_assembly as wa
from scripts.atlas import word_card_foundation as foundation
from scripts.guardrails import worktree_containment as containment
from tests.test_word_card_assembly import (
    CORRESPONDENCE_DAMAGE,
    HOLDING_BUILD,
    MANIFEST_SHA,
    build_world,
    damage_correspondence,
    registry_copy,
    swap_card_ids,
    swap_source_record_ids,
)

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


# --- R3-F1: the frozen identity allocation assembly may consume ---------------------------------------------

ASSEMBLY_LITERAL = "438b54e1995e5069076fb997454f6c3205fa4b5580dd7225ba86e3d295871ee6"
LATER = "later-snapshot@sha256:" + "f" * 64


def committed():
    return (foundation.load(ROOT / "registry/atlas/identity/registry.json"),
            foundation.load(ROOT / "registry/atlas/pilot/pilot-v1.json"))


def tamper_registry(registry, manifest, tamper):
    """One persistent-identity change to the committed allocation (the registry version is bumped separately)."""
    build = allocator.BUILD_PREFIX + manifest["manifest_sha256"]
    holding_build = allocator.HOLDING_BUILD_PREFIX + manifest["manifest_sha256"]
    pilot = [e for e in registry["entries"] if e["created_in_build"] == build]
    holding = [e for e in registry["events"] if e["build_id"] == holding_build]
    holding_ids = {e["to"][0] for e in holding}
    seed = next(s for e in pilot for s in e["senses"] if s["state"] == "unsplit" and s["sense_id"] not in holding_ids)
    multi = next(e for e in pilot if len(e["senses"]) > 1)
    held = next(s for e in pilot for s in e["senses"] if s["sense_id"] in holding_ids)
    if tamper == "card_id_swap":
        swap_card_ids(registry, pilot[0]["card_id"], pilot[1]["card_id"])
    elif tamper == "card_id_retarget":
        old, new = pilot[0]["card_id"], "wc_" + "z" * 12
        pilot[0]["card_id"] = new
        next(e for e in registry["events"] if e.get("cards") == [old])["cards"] = [new]
    elif tamper == "source_record_swap":
        a, b = [r for r in registry["source_records"] if r["source_id"] == "ulif"][:2]
        swap_source_record_ids(registry, a["source_record_id"], b["source_record_id"])
    elif tamper == "source_id":
        record = registry["source_records"][0]
        record["source_id"] = next(r["source_id"] for r in registry["source_records"]
                                   if r["source_id"] != record["source_id"])
    elif tamper == "creation_key":
        pilot[0]["key_at_creation"]["pos"] = "verb" if pilot[0]["key_at_creation"]["pos"] != "verb" else "noun"
    elif tamper == "creation_build":
        pilot[0]["created_in_build"] = holding_build
    elif tamper == "seed_owner":
        sense = multi["senses"].pop()
        other = next(e for e in pilot if e is not multi)
        other["senses"].append(dict(sense, order=len(other["senses"]) + 1))
    elif tamper == "seed_order":
        multi["senses"][0]["order"], multi["senses"][1]["order"] = 2, 1
    elif tamper == "seed_state":
        seed["state"] = "active"
    elif tamper == "holding_id":
        old, new = held["sense_id"], "ws_" + "z" * 12
        held["sense_id"] = new
        next(e for e in holding if e["to"] == [old])["to"] = [new]
    elif tamper == "holding_state":
        held["state"] = "active"
    elif tamper == "holding_mint":
        holding[0]["build_id"] = build
    elif tamper == "holding_evidence":
        evidence = json.loads(holding[0]["evidence"])
        holding[0]["evidence"] = foundation.canonical(dict(evidence, held_units=evidence["held_units"][:-1])).decode()
    elif tamper == "missing_event":
        registry["events"].remove(holding[0])
    elif tamper == "added_event":
        registry["events"].append(dict(registry["events"][-1], event_id="ie_9999"))
    elif tamper == "frozen_snapshot_set":
        manifest["selection"]["source_records"][0]["snapshot_id"] = "selected-row@sha256:" + "0" * 64
    else:
        raise AssertionError(tamper)


IDENTITY_TAMPERS = [
    "card_id_swap", "card_id_retarget", "source_record_swap", "source_id", "creation_key", "creation_build",
    "seed_owner", "seed_order", "seed_state", "holding_id", "holding_state", "holding_mint", "holding_evidence",
    "missing_event", "added_event", "frozen_snapshot_set"]


def test_r3f1_identity_anchor_is_derived_from_the_committed_allocation():
    """Anchor derivation, separate from the mutations: the design projection of the committed registry, by hand."""
    registry, manifest = committed()
    frozen = sorted({r["snapshot_id"] for r in manifest["selection"]["source_records"]})
    projection = {"frozen_snapshots": frozen, "entries": registry["entries"], "events": registry["events"],
                  "source_records": [{
                      "source_record_id": sr["source_record_id"], "source_id": sr["source_id"],
                      "aliases": [x for x in sr["aliases"] if x["snapshot_id"] in frozen],
                      "correspondence": [x for x in sr["correspondence"] if x["snapshot_id"] in frozen]}
                      for sr in registry["source_records"]]}
    assert foundation.digest(projection) == ASSEMBLY_LITERAL == allocator.ASSEMBLY_ALLOCATION_DIGEST
    # Part one of its trust: the reviewed v2 allocation inside it, unchanged.
    assert foundation.digest(allocator.reviewed_allocation(registry, manifest)) == allocator.PILOT_ALLOCATION_DIGEST
    # The assembler's own binding of the committed allocation: 150 units, 155 seed + 3 holding senses.
    entry_by_unit, sense_events = wa.pilot_allocation(manifest, registry)
    assert len(entry_by_unit) == 150 and len(sense_events) == 158


@pytest.mark.parametrize("tamper", [None, *IDENTITY_TAMPERS])
def test_r3f1_identity_check_is_bound_to_frozen_allocation(tamper):
    registry, manifest = committed()
    allocator.identity_allocation_check(registry, manifest)  # unchanged control
    if tamper is None:
        return
    tamper_registry(registry, manifest, tamper)
    registry["registry_version"] += 1  # a version bump never authorises a changed identity
    with pytest.raises(foundation.Refusal, match=allocator.IDENTITY_REFUSAL):
        allocator.identity_allocation_check(registry, manifest)


def test_r3f1_identity_check_refuses_malformed_registries_explicitly():
    registry, manifest = committed()
    for broken in ({k: v for k, v in registry.items() if k != "events"},
                   dict(registry, source_records=[{"source_record_id": "sr_x"}]), None):
        with pytest.raises(foundation.Refusal, match=allocator.IDENTITY_REFUSAL):
            allocator.identity_allocation_check(broken, manifest)


def test_r3f1_identity_check_preserves_source_history_boundary(world):
    registry, manifest = committed()
    # An existing record's later-snapshot history (F16: a reused row locator and a stronger alias) is history.
    later = copy.deepcopy(registry)
    a, b = later["source_records"][:2]
    b["aliases"].append({"kind": "table_row", "key": "later:row:1", "snapshot_id": LATER})
    b["correspondence"].append({"snapshot_id": LATER, "status": "unique", "locator": a["correspondence"][0]["locator"]})
    a["aliases"].append({"kind": "uid", "key": "later:uid:1", "snapshot_id": LATER})
    later["registry_version"] += 1
    foundation.registry_check(later)
    allocator.identity_allocation_check(later, manifest)
    # ... which the full allocator audit still rejects, as before.
    with pytest.raises(AssertionError, match="reviewed pilot allocation"):
        allocator.reviewed_allocation(later, manifest)
    # A competing claim inside a frozen snapshot is identity, not history.
    competing = copy.deepcopy(registry)
    a, b = competing["source_records"][:2]
    snapshot = a["correspondence"][0]["snapshot_id"]
    b["aliases"].append({"kind": "table_row", "key": "competing:row:1", "snapshot_id": snapshot})
    b["correspondence"].append({"snapshot_id": snapshot, "status": "ambiguous", "hold": "test",
                                "candidates": [a["correspondence"][0]["locator"], b["correspondence"][0]["locator"]]})
    foundation.registry_check(competing)
    with pytest.raises(foundation.Refusal, match=allocator.IDENTITY_REFUSAL):
        allocator.identity_allocation_check(competing, manifest)
    # A genuinely new later-snapshot record with its mint is a new persistent identity: refused, as the full audit
    # refuses it, although the permissive foundation audit alone accepts it.
    added = copy.deepcopy(registry)
    added["source_records"].append({
        "source_record_id": "sr_" + "z" * 12, "source_id": "ulif",
        "aliases": [{"kind": "table_row", "key": "later:row:2", "snapshot_id": LATER}],
        "correspondence": [{"snapshot_id": LATER, "status": "unique", "locator": "ulif:ulif_dictua_entries:id:1"}]})
    added["events"].append({"event_id": "ie_9999", "kind": "source_record_mint", "build_id": "later@sha256:" + "e" * 64,
                            "to": ["sr_" + "z" * 12], "evidence": "ulif:ulif_dictua_entries:id:1"})
    foundation.allocation_check(manifest, added)
    with pytest.raises(foundation.Refusal, match=allocator.IDENTITY_REFUSAL):
        allocator.identity_allocation_check(added, manifest)
    # Every downstream frozen-row diagnostic still fires on its own, independently of the identity pin.
    for damage in CORRESPONDENCE_DAMAGE:
        damaged = registry_copy(world)
        locator = damage_correspondence(damaged, damage)
        row = next(r for r in world.records if r["locator"] == locator)
        expected = wa.MissingAllocation if damage == "missing" else wa.AssemblyError
        with pytest.raises(expected, match="own snapshot"):
            wa.bound_source_record(damaged, row)


OPTIMIZED_CHILD = textwrap.dedent("""
    import copy, json, sys
    from pathlib import Path
    from scripts.atlas import allocate_pilot_identities as allocator
    from scripts.atlas import word_card_foundation as foundation

    registry = foundation.load(Path("registry/atlas/identity/registry.json"))
    manifest = foundation.load(Path("registry/atlas/pilot/pilot-v1.json"))
    build = allocator.BUILD_PREFIX + manifest["manifest_sha256"]
    pilot = [i for i, e in enumerate(registry["entries"]) if e["created_in_build"] == build]
    ulif = [i for i, r in enumerate(registry["source_records"]) if r["source_id"] == "ulif"][:2]

    def swap_cards(r):
        a, b = (r["entries"][i] for i in pilot[:2])
        a["card_id"], b["card_id"] = b["card_id"], a["card_id"]

    def promote(r):
        next(s for i in pilot for s in r["entries"][i]["senses"] if s["state"] == "unsplit")["state"] = "active"

    def swap_records(r):
        a, b = (r["source_records"][i]["source_record_id"] for i in ulif)
        swap = {a: b, b: a}
        for record in r["source_records"]:
            record["source_record_id"] = swap.get(record["source_record_id"], record["source_record_id"])
        for event in r["events"]:
            if event["kind"] == "source_record_mint":
                event["to"] = [swap.get(event["to"][0], event["to"][0])]

    def later_history(r):
        r["source_records"][0]["aliases"].append(
            {"kind": "uid", "key": "later:uid:1", "snapshot_id": "later-snapshot@sha256:" + "f" * 64})
        r["registry_version"] += 1

    outcome = {}
    for name, change in (("clean", None), ("later_history", later_history), ("card_id_swap", swap_cards),
                         ("unsplit_promotion", promote), ("source_record_swap", swap_records)):
        candidate = copy.deepcopy(registry)
        if change:
            change(candidate)
        try:
            allocator.identity_allocation_check(candidate, manifest)
            outcome[name] = "accepted"
        except foundation.Refusal as error:
            outcome[name] = "refused: " + str(error)
    print(json.dumps({"optimize": sys.flags.optimize, "outcome": outcome}))
""")


def test_r3f1_runtime_identity_audit_survives_optimized_python():
    proc = subprocess.run([sys.executable, "-O", "-c", OPTIMIZED_CHILD], cwd=ROOT, capture_output=True, text=True,
                          check=False, timeout=120)
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    refused = "refused: " + allocator.IDENTITY_REFUSAL
    assert report == {"optimize": 1, "outcome": {
        "clean": "accepted", "later_history": "accepted", "card_id_swap": refused, "unsplit_promotion": refused,
        "source_record_swap": refused}}

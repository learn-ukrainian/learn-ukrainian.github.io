"""Batch-1 delivery, replay and refusal tests; synthetic words are placeholders.

The host test also checks all 150 real pilot cards against read-only sources.
Neither synthetic checks nor locator authentication certify linguistic accuracy.
"""

import copy
import json
import re
import tempfile
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace

import pytest
from jsonschema import Draft202012Validator

from scripts.atlas import allocate_pilot_identities as allocator
from scripts.atlas import word_card_assembly as assembly
from scripts.atlas import word_card_batch1 as batch
from scripts.atlas import word_card_foundation as foundation
from scripts.atlas import word_card_sources as sources
from scripts.atlas import word_card_verify as verifier
from scripts.common.scratch import ensure_scratch_root
from tests.test_word_card_assembly import LABEL_M, World, make_inputs

# Frozen allocation for the 150 placeholder units constructed below.
SYNTHETIC_PIN = "fd60d57606f9ecdc5d0549a178e58566255bb812b65a71985c5288141bedd46b"


@pytest.fixture(scope="module")
def synthetic_world():
    world = World()
    alphabet = "бвгґджзклмнпрст"
    for index in range(150):
        plain = "а" + alphabet[index // len(alphabet)] + alphabet[index % len(alphabet)]
        stressed = "а\u0301" + plain[1:]
        world.ulif(index + 1, plain, stressed, LABEL_M,
                   rows=[("називний", stressed, ""), ("родовий", stressed + "а", "")])
        world.vesum_form(index + 1, plain, plain, "noun:inanim:m:v_naz", stressed)
        world.vesum_form(index + 1, plain, plain + "а", "noun:inanim:m:v_rod", stressed)
    world.finish({})
    yield world
    world.sources.close()
    world.vesum.close()
    world.raw.close()


@pytest.fixture
def host_output():
    with tempfile.TemporaryDirectory(prefix="batch1-test-", dir=ensure_scratch_root()) as directory:
        yield Path(directory)


@pytest.fixture
def inputs(synthetic_world, host_output, monkeypatch):
    monkeypatch.setattr(allocator, "ASSEMBLY_ALLOCATION_DIGEST", SYNTHETIC_PIN)
    return make_inputs(synthetic_world, host_output / "inputs")


def assert_receipt(result, receipt):
    assert receipt["card_count"] == len(receipt["cards"]) == len(result["cards"]) == 150
    assert [c["card_id"] for c in receipt["cards"]] == sorted(result["cards"])
    assert receipt["status"] == "mechanics_only_uncertified"
    assert receipt["cards_sha256"] == foundation.digest(receipt["cards"])
    assert receipt["locator_count"] == sum(c["locator_count"] for c in receipt["cards"])
    for item in receipt["cards"]:
        card = result["cards"][item["card_id"]]
        assert item["content_sha256"] == foundation.digest(card)
        assert item["locator_count"] == len({(a["source_id"], a["snapshot_id"], a["locator"])
                                             for a in card["assertions"]})
    # A public receipt carries no dictionary text, source locators or machine paths.
    text = json.dumps(receipt, ensure_ascii=False)
    assert not re.search("[А-Яа-яІіЇїЄєҐґ]", text)
    assert set(receipt) == {"schema_version", "batch", "status", "pilot_manifest_sha256", "build_id",
                            "card_count", "locator_count", "content_hash_basis", "cards", "cards_sha256"}


def test_all_150_cards_schema_stress_and_morphology(inputs):
    result, report, receipt = batch.assemble(inputs)
    validator = Draft202012Validator(foundation.load(verifier.SCHEMA))
    assert report["passed"] is True
    assert report["schema"]["cards"] == report["conservation"]["cards"] == 150
    assert report["locators"]["checked"] > 150
    resolver = verifier.Resolver(inputs)
    for card in result["cards"].values():
        assert list(validator.iter_errors(card)) == []
        stress = [a for a in card["assertions"] if a["field"] == "stress"]
        paradigms = [a for a in card["assertions"] if a["field"] == "paradigm"]
        assert stress and paradigms
        assert {a["source_id"] for a in paradigms} == {"ulif", "vesum"}
        for assertion in stress + paradigms:
            assert resolver.check(card, assertion) is None
            if assertion["field"] == "stress":
                readings = assertion["value"]
                for reading in readings if isinstance(readings, list) else [readings]:
                    assert sources.unstressed(reading) == card["key_at_creation"]["spelling"]
                    assert reading.count(sources.ACUTE) == 1
        by_slot = {}
        for assertion in paradigms:
            by_slot.setdefault(assertion["value"]["slot"], {})[assertion["source_id"]] = {
                sources.unstressed(form) for form in assertion["value"]["forms"]}
        assert by_slot
        assert all(forms["ulif"] == forms["vesum"] for forms in by_slot.values())
    assert_receipt(result, receipt)


def test_replay_and_receipt_order_are_deterministic(inputs):
    first, _, receipt = batch.assemble(inputs)
    second, _, replay = batch.assemble(inputs)
    assert foundation.canonical(first["cards"]) == foundation.canonical(second["cards"])
    assert foundation.canonical(receipt) == foundation.canonical(replay)


def test_refuses_a_changed_replay(inputs, monkeypatch):
    first = assembly.build(inputs)
    replay = copy.deepcopy(first)
    replay["build_id"] = "different-build"
    builds = iter([first, replay])
    monkeypatch.setattr(assembly, "build", lambda *args: next(builds))
    with pytest.raises(assembly.AssemblyError, match="integrity verification failed"):
        batch.assemble(inputs)


@pytest.mark.parametrize("size", [0, 149, 151])
def test_refuses_wrong_denominator_before_build(size, monkeypatch):
    def forbidden(*args):
        pytest.fail("A wrong denominator must not reach assembly")
    monkeypatch.setattr(assembly, "build", forbidden)
    with pytest.raises(assembly.AssemblyError, match="exactly 150 frozen units"):
        batch.assemble(SimpleNamespace(units=[{}] * size))


@pytest.mark.parametrize("damage", ["schema", "stress", "morphology", "missing_card"])
def test_rejects_corrupt_cards_before_receipt(inputs, monkeypatch, damage):
    result = assembly.build(inputs)
    broken = copy.deepcopy(result)
    card = next(iter(broken["cards"].values()))
    if damage == "schema":
        card["unexpected"] = True
    elif damage == "missing_card":
        del broken["cards"][card["card_id"]]
    else:
        field = "stress" if damage == "stress" else "paradigm"
        assertion = next(a for a in card["assertions"] if a["field"] == field)
        if field == "stress":
            assertion["value"] = "invalid"
        else:
            assertion["value"]["forms"] = ["invalid"]
    monkeypatch.setattr(assembly, "build", lambda *args: broken)
    message = "exactly 150 cards" if damage == "missing_card" else "integrity verification failed"
    with pytest.raises(assembly.AssemblyError, match=message):
        batch.assemble(inputs)


def test_committed_receipt_accounts_for_frozen_allocations():
    manifest = foundation.load(batch.ROOT / batch.PILOT)
    registry = foundation.load(batch.ROOT / batch.REGISTRY)
    receipt = foundation.load(batch.ROOT / batch.RECEIPT)
    entries, _ = assembly.pilot_allocation(manifest, registry)
    assert receipt["pilot_manifest_sha256"] == manifest["manifest_sha256"]
    assert receipt["card_count"] == len(receipt["cards"]) == len(entries) == 150
    assert [c["card_id"] for c in receipt["cards"]] == sorted(e["card_id"] for e in entries.values())
    assert receipt["cards_sha256"] == foundation.digest(receipt["cards"])
    assert receipt["locator_count"] == sum(c["locator_count"] for c in receipt["cards"])
    assert all(re.fullmatch("[0-9a-f]{64}", c["content_sha256"]) and c["locator_count"] > 0
               for c in receipt["cards"])


def test_cli_build_check_and_tampered_receipt(inputs, host_output, monkeypatch, capsys):
    monkeypatch.setattr(assembly, "load_inputs", lambda *args: inputs)
    output, receipt = host_output / "batch1", host_output / "receipt.json"
    args = ["--output", str(output), "--receipt", str(receipt)]
    assert batch.main(args) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["cards"] == 150 and summary["certified"] is False
    cards = {p.stem: foundation.load(p) for p in (output / "cards").glob("*.json")}
    assert_receipt({"cards": cards}, foundation.load(receipt))
    snapshot = {p: p.read_bytes() for p in output.rglob("*.json")}
    assert batch.main([*args, "--check"]) == 0
    assert {p: p.read_bytes() for p in output.rglob("*.json")} == snapshot
    absent = host_output / "check-does-not-create-output"
    assert batch.main(["--output", str(absent), "--receipt", str(receipt), "--check"]) == 0
    assert not absent.exists()
    receipt.write_text("{}\n")
    assert batch.main([*args, "--check"]) == 1
    assert "receipt differs" in capsys.readouterr().err
    assert receipt.read_text() == "{}\n"


def test_cli_failure_preserves_existing_output(host_output, monkeypatch, capsys):
    receipt = host_output / "receipt.json"
    receipt.write_text("prior receipt\n")
    output = host_output / "batch1"
    output.mkdir()
    sentinel = output / "prior.json"
    sentinel.write_text("prior output\n")
    def refuse(*args):
        raise assembly.AssemblyError("Frozen source row drift")
    monkeypatch.setattr(assembly, "load_inputs", refuse)
    assert batch.main(["--output", str(output), "--receipt", str(receipt)]) == 1
    assert sentinel.read_text() == "prior output\n"
    assert receipt.read_text() == "prior receipt\n"
    assert "Frozen source row drift" in capsys.readouterr().err


def test_cli_refuses_tracked_card_output_before_source_reads(monkeypatch, capsys):
    def forbidden(*args):
        pytest.fail("Protected card output must fail before source access")
    monkeypatch.setattr(assembly, "load_inputs", forbidden)
    assert batch.main(["--output", str(batch.ROOT / "registry/atlas/pilot/cards")]) == 1
    assert "host-only" in capsys.readouterr().err


@pytest.mark.parametrize("target", ["output", "input"])
def test_cli_refuses_receipt_over_an_input_or_card_output(target, host_output, monkeypatch, capsys):
    def forbidden(*args):
        pytest.fail("Receipt target must be checked before source access")
    monkeypatch.setattr(assembly, "load_inputs", forbidden)
    output = host_output / "batch1"
    receipt = output / "receipt.json" if target == "output" else batch.ROOT / batch.PILOT
    assert batch.main(["--output", str(output), "--receipt", str(receipt)]) == 1
    assert "receipt must" in capsys.readouterr().err
    assert not output.exists()


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as error:
        batch.main(["--help"])
    assert error.value.code == 0
    help_text = capsys.readouterr().out
    for text in ("Outputs:", "Exit codes:", "Related:", "--check", "--receipt", "--sources-db"):
        assert text in help_text


def test_real_150_card_batch_with_readonly_sources(host_output):
    primary = batch.main_checkout_root(batch.ROOT)
    stores = {name: primary / "data" / f"{name}.db" for name in ("sources", "vesum", "atlas")}
    if not all(path.is_file() for path in stores.values()) or not assembly.raw_cache_path(stores["sources"]).is_file():
        pytest.skip("Canonical source databases and raw cache are host-only")
    with ExitStack() as stack:
        inputs = assembly.load_inputs(batch.ROOT / batch.PILOT, batch.ROOT / batch.REGISTRY,
                                      batch.ROOT / batch.REGISTER, stores["sources"], stores["vesum"],
                                      stores["atlas"], stack, host_output)
        result, report, receipt = batch.assemble(inputs)
        assert report["passed"] is True
        assert report["schema"]["cards"] == report["conservation"]["cards"] == 150
        assert report["locators"]["errors"] == {}
        assert report["determinism"]["passed"] is True
        assert_receipt(result, receipt)
        committed = foundation.load(batch.ROOT / batch.RECEIPT)
        # Later source versions require an explicit receipt rebuild.
        assert receipt == committed

"""Coordinator-approved AC-01 checks, #11943 issuecomment-6533002392.

Pinned Sources replies permit deterministic replay without live stores in CI.
The separate live builder --check authenticates those replies against stores.
"""

import copy
import hashlib
import json
from collections import Counter
from types import SimpleNamespace

import pytest

from scripts.atlas import a1_vocabulary_inventory as inventory


@pytest.fixture
def frozen():
    return json.loads((inventory.ROOT / inventory.OUTPUT).read_text(encoding="utf-8"))


class FrozenEvidence:
    def __init__(self, frozen):
        self.frozen = frozen
        self.identity = frozen["sources"]["vesum_pipeline_identity"]
        self.words = {}
        self.lemmas = {}

    def word(self, word):
        self.words[word] = self.frozen["word_evidence"][word]
        return self.words[word]

    def lemma(self, lemma):
        self.lemmas[lemma] = self.frozen["lemma_evidence"][lemma]
        self.word(lemma)
        return self.lemmas[lemma]


class FrozenPilotLinks:
    def __init__(self, frozen):
        self.sources = SimpleNamespace(consumed=frozen["sources"]["pilot_consumed_queries"])
        self.matches = {}
        for row in frozen["rows"]:
            mapping = row["mapping"]
            if "entry_id" in mapping:
                self.matches[(mapping["lemma"], mapping["pos"], mapping["entry_id"],
                              mapping["kind"] == "name")] = mapping["pilot"]

    def match(self, *key):
        return self.matches[key]


def replay(frozen):
    files, rows = inventory.frozen_rows(inventory.ROOT)
    return inventory.build(FrozenEvidence(frozen), FrozenPilotLinks(frozen), files, rows)


def test_pinned_inventory_replay_cannot_change_output_order_or_content(frozen):
    """Unstable traversal or a changed mapping must differ from the pinned bytes."""
    first = replay(frozen)
    second = replay(copy.deepcopy(frozen))
    expected = (inventory.ROOT / inventory.OUTPUT).read_bytes()
    for result in (first, second):
        actual = inventory.serialize(result).encode()
        assert actual == expected


def test_every_frozen_row_has_exactly_one_disposition_without_loss_or_duplication(frozen):
    """Row loss, duplication and collapsed vocabulary variants break reconciliation."""
    result = replay(frozen)
    _, source_rows = inventory.frozen_rows(inventory.ROOT)
    assert len(result["rows"]) == 2144
    assert [(r["id"], r["source"]) for r in result["rows"]] == [
        (r["id"], r["source"]) for r in source_rows
    ]
    ids = [r["id"] for r in result["rows"]]
    assert len(set(ids)) == 2144
    assert Counter(i for group in result["keys"].values() for i in group) == Counter(range(2144))
    assert Counter(r["mapping"]["kind"] for r in result["rows"]) == {
        "lemma": 1626, "ambiguous": 149, "name": 73, "phrase": 272,
        "slash_alternatives": 4, "unresolved": 20,
    }
    assert all(r["mapping"]["resolution"] in {"resolved", "ambiguous", "unresolved"}
               for r in result["rows"])


def test_builder_preserves_pilot_and_identity_bytes(frozen):
    """Inventory replay cannot remint or mutate existing pilot identities."""
    expected = {
        "registry/atlas/pilot/pilot-v1.json": "19caa9148c76294156f12b4d1b11c11f4563ba0facac142460dd927543a7bc71",
        "registry/atlas/identity/registry.json": "681be77e60edbe621ca68e680db2bffbbd9e99267b011fb0515e090fe8d8a06d",
    }
    before = {path: (inventory.ROOT / path).read_bytes() for path in expected}
    replay(frozen)
    for path, sha in expected.items():
        assert hashlib.sha256(before[path]).hexdigest() == sha
        assert (inventory.ROOT / path).read_bytes() == before[path]

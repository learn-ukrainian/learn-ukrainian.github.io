from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "agents_extensions/shared/skills/drive-ukrainian-dataset-epic/SKILL.md"


def _skill_text() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_v4_scope_and_safety_contract_is_machine_visible() -> None:
    text = _skill_text()
    frontmatter = yaml.safe_load(text.split("---", 2)[1])
    assert frontmatter["name"] == "drive-ukrainian-dataset-epic"
    assert len(frontmatter["description"]) <= 1024

    scope = text.split("## Frozen V4 scope", 1)[1].split("The slots sum", 1)[0]
    slots = [int(value) for value in re.findall(r"^\| [^|]+ \| (\d+) \|", scope, re.MULTILINE)]
    assert slots == [15, 15, 15, 15, 15, 10, 10, 5]
    assert sum(slots) == 100

    normalized_text = " ".join(text.split())
    for marker in (
        "outcome_sha256 = 78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20",
        "public_control_issue = #7423",
        "private_operational_board = #622",
        "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD",
        "The diagonal is forbidden",
        "leave-one-out views",
        "Human review is optional for silver",
        "source-qualified human adjudication",
        "free_bytes >= incremental_peak_bytes + policy_reserve_bytes",
        "total_bytes >= used_bytes + incremental_peak_bytes + policy_reserve_bytes",
        "do not double-count retained bytes already included in used/free",
        "policy_reserve_bytes",
        "Dedicated non-Ukrainian Slavic programs are out of scope.",
        "Modern Rusyn is not a",
        "Public pilot slot IDs are a source-free stable series",
        "V4-PILOT-SLOT-001",
        "V4-PILOT-SLOT-100",
        "derived row and case IDs may bind sources later",
        "Silver does not require universal human and model agreement.",
        "hypothesis, proposal, vote, confidence, or agreement cannot independently",
        "hypotheses, agreement, majority,",
        "can never independently make a row gold",
        "Model hypotheses cannot independently admit silver or make gold.",
    ):
        assert marker in normalized_text

    for role in (
        "Accountable epic driver",
        "Source-admission steward",
        "Rights-capability steward",
        "Custody/split steward",
        "Identity lead",
        "Independent dissent reviewer",
        "Locked-dispute critic",
        "Candidate builder",
        "Optional silver reviewer",
        "Source-qualified gold adjudicator",
        "Capacity/custody operator",
        "Held-out evaluator",
        "Consumer reproducer",
        "Cross-family PR reviewer",
    ):
        assert role in text

    release_states = (
        "ARENA_SLICE_READY",
        "EVAL_ARTIFACT_READY",
        "TRAINING_READY_SILVER",
        "TRAINING_READY_GOLD_SUBSET",
        "GOLD_UPGRADE_READY",
        "BLOCKED_WITH_RESIDUALS",
    )
    for release_state in release_states:
        assert f"`{release_state}`" in text

    old_release_states = (
        "INVENTORIED",
        "PILOT_VALIDATED",
        "DATASET_PARTIAL",
        "DATASET_READY",
        "BLOCKED",
        "TRAINING_VALIDATED",
    )
    for release_state in old_release_states:
        assert not re.search(
            rf"(?<![A-Z0-9_]){re.escape(release_state)}(?![A-Z0-9_])", text
        )

    exact_ownership = (
        "A0 accountable driver",
        "A1 VPS custody/capacity",
        "A2 source inventory/admission/rights by operation",
        "A3 heldout/source-family split",
        "A4 deterministic extraction",
        "A5 expression-free evidence enrichment",
        "A6 blind arena",
        "A7 independent original-row factory",
        "A8 admission/assembly",
        "A9 evaluation/scorer/manifest/consumer reproduction",
        "A10 pilot review with independent Ukrainian + exact-head CF gates",
        "A11 silver release",
        "A12 later gold overlays",
        "A13 cleanup",
    )
    for marker in exact_ownership:
        assert marker in " ".join(text.split())

    for gate in ("READY_TO_DRIVE", "PRE_BUILDER", "PRE_SCALE"):
        assert f"`{gate}`" in text
    for marker in (
        "main and VPS",
        "VPS reachability",
        "measured capacity for the 100-row pilot",
        "frozen public slot contract",
        "complete functional role map",
        "A1/A2",
        "A1/A2 custody/inventory",
        "custody-and-inventory prerequisite",
        "admitted slice",
        "sealed A3 held-out/source-",
        "pilot high-water measurements",
        "full-scale capacity",
        "source-inventory reconciliation",
        "not a global block",
        "dispatch its named prerequisite",
    ):
        assert marker in normalized_text

    gate_sequence = text.split("The gate sequence is", 1)[1].split(
        "## Driver preflight", 1
    )[0]
    gate_positions = [
        gate_sequence.index(marker)
        for marker in ("READY_TO_DRIVE", "A1/A2 custody/inventory", "PRE_BUILDER", "PRE_SCALE")
    ]
    assert gate_positions == sorted(gate_positions)

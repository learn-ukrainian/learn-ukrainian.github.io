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
        "data/projects/open_model_data/admission/dataset_v4_pilot_slot_manifest_v1.json",
        "schema_version: dataset_v4_pilot_slot_manifest_v1",
        "Generate public pilot slot IDs from its eight `slot_series` entries only",
        "source-free stable per-stratum series",
        "derived row and case IDs may bind sources later",
        "Silver does not require universal human and model agreement.",
        "hypothesis, proposal, vote, confidence, or agreement cannot independently",
        "hypotheses, agreement, majority,",
        "can never independently make a row gold",
        "Model hypotheses cannot independently admit silver or make gold.",
    ):
        assert marker in normalized_text

    slot_section = text.split("## Slot, row, and case identity", 1)[1].split(
        "After a slot is admitted", 1
    )[0]
    slot_rows = re.findall(
        r"^\| `([^`]+)` \| `([^`]+)` \| (\d+) \| (\d+) \| `([^`]+)` … `([^`]+)` \|$",
        slot_section,
        re.MULTILINE,
    )
    assert slot_rows == [
        (
            "standard_correct",
            "v4p-standard-correct",
            "1",
            "15",
            "v4p-standard-correct-001",
            "v4p-standard-correct-015",
        ),
        (
            "correction",
            "v4p-correction",
            "1",
            "15",
            "v4p-correction-001",
            "v4p-correction-015",
        ),
        (
            "literary",
            "v4p-literary",
            "1",
            "15",
            "v4p-literary-001",
            "v4p-literary-015",
        ),
        (
            "dialect_regional",
            "v4p-dialect-regional",
            "1",
            "15",
            "v4p-dialect-regional-001",
            "v4p-dialect-regional-015",
        ),
        (
            "archaic_historical",
            "v4p-archaic-historical",
            "1",
            "15",
            "v4p-archaic-historical-001",
            "v4p-archaic-historical-015",
        ),
        ("mixing", "v4p-mixing", "1", "10", "v4p-mixing-001", "v4p-mixing-010"),
        (
            "quotation_interference",
            "v4p-quotation-interference",
            "1",
            "10",
            "v4p-quotation-interference-001",
            "v4p-quotation-interference-010",
        ),
        ("abstention", "v4p-abstention", "1", "5", "v4p-abstention-001", "v4p-abstention-005"),
    ]
    assert sum(int(row[3]) for row in slot_rows) == 100
    assert "V4-PILOT-SLOT-" not in normalized_text

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

    preflight = text.split("## Driver preflight", 1)[1].split(
        "## Issue-stage ownership and execution", 1
    )[0]
    normalized_preflight = " ".join(preflight.split())
    assert "not an all-at-once checklist" in normalized_preflight
    ready_block = preflight.split("The `A1/A2` prerequisite", 1)[0]
    normalized_ready_block = " ".join(ready_block.split())
    assert "`READY_TO_DRIVE` has exactly these five checks" in normalized_ready_block
    assert len(re.findall(r"^\d\. ", ready_block, re.MULTILINE)) == 5
    for marker in (
        "VPS custody/capacity receipt",
        "source inventory, admission, and rights-by-operation receipt",
        "admitted slice plus the sealed A3 heldout/source-family split",
        "pilot high-water measurements, full-scale capacity evidence, and source-inventory reconciliation",
        "At every dispatch, independently recheck and receipt the live routing",
        "exact code/skill head",
    ):
        assert marker in normalized_preflight
    for marker in (
        "The source manifest is unit-complete",
        "The operation-specific rights ledger is present for the operation being run",
        "The split/held-out firewall, leave-one-out matrix, and Cycle007 deny-list are sealed",
    ):
        assert marker not in normalized_ready_block

    issue_table = text.split(
        "| Stage | Issue | Primary outcome | Functional lead |", 1
    )[1].split("\n\nEach issue has exactly one accountable lead", 1)[0]
    issue_leads = dict(
        re.findall(r"^\| [^|]+ \| (#743[0-3]) \| [^|]+ \| ([^|]+) \|$", issue_table, re.MULTILINE)
    )
    assert issue_leads == {
        "#7430": "A10 pilot-review lead (accountable); A4-A8 producers separated.",
        "#7431": "A9 heldout/evaluation lead (accountable); independent A10 review.",
        "#7432": "A8 scale/admission-assembly lead (accountable); A1/A2/A4/A5/A7 producers.",
        "#7433": "A11 silver-release lead (accountable); separate A9 reproducer and A10 reviewer.",
    }
    for marker in (
        "Candidate builder, with identity/dissent, custody, rights, and capacity stewards.",
        "Held-out evaluator and consumer reproducer.",
        "Driver plus source/capacity stewards and bounded builder lanes.",
        "Consumer reproducer, rights steward, and driver.",
    ):
        assert marker not in issue_table

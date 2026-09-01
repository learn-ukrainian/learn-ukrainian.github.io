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

    for marker in (
        "outcome_sha256 = 78a1edad36f7bab31f77470fcbf95e1542adbcd9ff5701a6c539a2cfdc49ff20",
        "public_control_issue = #7423",
        "private_operational_board = #622",
        "MODEL_AGREEMENT_QUARANTINED_NOT_GOLD",
        "The diagonal is forbidden",
        "leave-one-out views",
        "Human review is optional for silver",
        "source-qualified human adjudication",
        "free_bytes >= required_bytes",
        "free_inodes >= required_inodes",
        "policy_reserve_bytes",
        "Dedicated non-Ukrainian Slavic programs are out of scope.",
        "Modern Rusyn is not a",
    ):
        assert marker in text

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

    for release_state in (
        "INVENTORIED",
        "PILOT_VALIDATED",
        "DATASET_PARTIAL",
        "DATASET_READY",
        "BLOCKED",
        "TRAINING_VALIDATED",
    ):
        assert release_state in text

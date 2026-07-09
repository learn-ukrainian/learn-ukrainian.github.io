from __future__ import annotations

from typing import Any

from scripts.audit.grounding_shadow_compare import compute_summary


def test_compute_summary_synthetic():
    records: list[dict[str, Any]] = [
        # (a) Plain anchored: v1 accepted, v2 anchored
        {
            "fixture": "fix_a",
            "seat_arm": "seat_1/arm_1",
            "v1_admissible": True,
            "v2_anchored": True,
            "v2_abstained": False,
            "similarity": 1.0,
            "abstain_recovered": False,
            "v2_effective": True,
            "gold_is_true": True,
        },
        # (b1) Abstain sim=1.0, v1 rejected: counts as recovered, not regression
        {
            "fixture": "fix_b",
            "seat_arm": "seat_1/arm_1",
            "v1_admissible": False,
            "v2_anchored": False,
            "v2_abstained": True,
            "similarity": 1.0,
            "abstain_recovered": True,
            "v2_effective": True,
            "gold_is_true": True,
        },
        # (b2) Abstain sim=1.0, v1 accepted: counts as NEITHER (no regression)
        {
            "fixture": "fix_b",
            "seat_arm": "seat_1/arm_1",
            "v1_admissible": True,
            "v2_anchored": False,
            "v2_abstained": True,
            "similarity": 1.0,
            "abstain_recovered": True,
            "v2_effective": True,
            "gold_is_true": True,
        },
        # (c) Abstain sim<1.0, v1 accepted: counts as regression (NOT effective)
        {
            "fixture": "fix_c",
            "seat_arm": "seat_2/arm_1",
            "v1_admissible": True,
            "v2_anchored": False,
            "v2_abstained": True,
            "similarity": 0.8,
            "abstain_recovered": False,
            "v2_effective": False,
            "gold_is_true": True,
        },
        # (d) Plain reject: v1 rejected, v2 rejected
        {
            "fixture": "fix_d",
            "seat_arm": "seat_2/arm_1",
            "v1_admissible": False,
            "v2_anchored": False,
            "v2_abstained": False,
            "similarity": 0.0,
            "abstain_recovered": False,
            "v2_effective": False,
            "gold_is_true": None,
        },
    ]

    stats = compute_summary(records)

    # Assert basic totals
    assert stats["total"] == 5
    assert stats["v1_count"] == 3  # (a), (b2), (c)
    assert stats["v2_effective_count"] == 3  # (a), (b1), (b2)
    assert stats["v2_anchored_raw"] == 1  # only (a) is raw anchored
    assert stats["abstain_recovered_count"] == 2  # (b1) and (b2)
    assert stats["abstains"] == 3  # (b1), (b2), (c)

    # (b1) is recovered (v1=False, v2_eff=True).
    # (a) is not recovered (v1=True).
    # (b2) is not recovered (v1=True).
    assert stats["recovered"] == 1

    # (c) is a regression (v1=True, v2_eff=False).
    # Under raw anchored, (b2) would also be a regression (v1=True, v2_anchored=False).
    # Under effective, it is recovered (v2_effective=True), so it is not a regression.
    assert stats["regressions"] == 1

    # Raw anchored regressions would have been: (b2) and (c) -> 2.
    # So raw-vs-effective counts diverge exactly on (b2).
    raw_regressions = sum(1 for r in records if r["v1_admissible"] and not r["v2_anchored"])
    assert raw_regressions == 2
    assert stats["regressions"] != raw_regressions

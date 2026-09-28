# Synonym mode withdrawal (#8714)

Advisor ruling A withdraws every synonym-mode card until #8984 admits cards with checked, per-card sense binding. The source denominator is the published `atlas-practice-v1-c0c3f3242b5134b6` deck. Counts below come from its five `practice-synonym.<level>.json` shards. Antonym-polarity cards in that mode are included because the learner accesses them through the same withdrawn mode.

| Level | Published before withdrawal | Retained | Withdrawn | Reason |
| --- | ---: | ---: | ---: | --- |
| A1 | 0 | 0 | 0 | No inventory |
| A2 | 66 | 0 | 66 | Sense substitutability unproven |
| B1 | 2,299 | 0 | 2,299 | Sense substitutability unproven |
| B2 | 684 | 0 | 684 | Sense substitutability unproven |
| C1 | 195 | 0 | 195 | Sense substitutability unproven |
| **Total** | **3,244** | **0** | **3,244** | **Mode disabled** |

The 9 errors in the GPT review of 120 cards and the 10 identified Gemini rejections are preserved as named regression cases in `tests/fixtures/synonym_withdrawal_cases.json`. ULIF group membership alone does not establish that two words substitute in the card's displayed sense. The unidentified eleventh Gemini error remains an evidence gap for #8984.

Restoration owner: `claude-atlas`, under #8984. Re-enable only after the advisor's per-card evidence, independent held-out evaluation, and delivery gates are met.

The containment asset is `atlas-practice-v1-f1e1cf95470ce319` (`gz_sha256` `d01ed4b4cf10d8f587de214d0e3dd7f4039f4bafe5549d6bed7145bc34e55b19`). It is a hash-checked transform of the original 55-shard release package: the five synonym arrays are empty, synonym mode is absent from each index, and the other card content is unchanged. The normal full regeneration was blocked by 64 unresolved curated membership routes against the available Atlas manifest; this withdrawal does not claim fresh coverage or restore that input mismatch.

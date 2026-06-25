# B2 M16-M21 LLM Score Report

Date: 2026-06-25

Scope: B2 production batch M16-M21 on merged `main`.

Preflight basis: `docs/audits/b2-preflight-readiness-remediation-2026-06-22.md`.

## Score Summary

| Score | Module | Activity/Vocab Coverage | Deterministic Audit | Ready Human Review? | Verdict |
| --- | --- | --- | --- | --- | --- |
| 9/10 | M16 `secondary-sentence-members` | 12 workbook / 0 inline; 32 vocab | PASS | Yes | B+ |
| 9/10 | M17 `sport-i-dozvillia` | 10 workbook / 0 inline; 32 vocab | PASS | Yes | B+ |
| 9/10 | M18 `b2-one-member-sentences` | 10 workbook / 0 inline; 32 vocab | PASS | Yes | B+ |
| 9/10 | M19 `homogeneous-members` | 10 workbook / 0 inline; 32 vocab | PASS | Yes | B+ |
| 9/10 | M20 `detached-members` | 11 workbook / 0 inline; 32 vocab | PASS | Yes | B+ |
| 9/10 | M21 `checkpoint-syntax-i` | 10 workbook / 0 inline; 20 vocab | PASS | Yes | B+ |

Average score: 9.0/10.

## Notes

| Module | Notes |
| --- | --- |
| M16 `secondary-sentence-members` | Strong grammar-production module for secondary sentence members. The independent review initially flagged only stale-base MDX generation drift; after rebase and drift check, the follow-up review found no blockers. Score held at 9 for normal post-build polish risk. |
| M17 `sport-i-dozvillia` | Strong sport and leisure communication module with validated activity and vocabulary coverage. Claude Opus 4.8 blocker review passed with no merge blockers. Score held at 9 for conservative batch scoring rather than content blockers. |
| M18 `b2-one-member-sentences` | Strong one-member sentence module with 100% immersion and 96% richness in the merged PR validation note. Independent review found no merge-blocking issues. Score held at 9 for residual section-balance/advisory risk. |
| M19 `homogeneous-members` | Strong homogeneous-members syntax module with 100% immersion and 96% richness. Independent review passed with no merge blockers. Score held at 9 for ordinary post-build polish risk. |
| M20 `detached-members` | Strong detached-members module. Deterministic audit passed at 4107/4000 words with 96% richness and 100% immersion; Claude Opus 4.8 review found no blockers. Score held at 9 for conservative post-build polish risk. |
| M21 `checkpoint-syntax-i` | Strong final B2.1 syntax checkpoint. Deterministic audit passed with 100% immersion and 99% richness; independent review found no blockers. Score held at 9 because the checkpoint intentionally remains compact and still has non-blocking section-balance warnings. |

## Raw Counts

| Module | Raw Word Count | Vocabulary | Activities |
| --- | ---: | ---: | --- |
| M16 `secondary-sentence-members` | 5396 | 32 | 12 workbook / 0 inline |
| M17 `sport-i-dozvillia` | 4153 | 32 | 10 workbook / 0 inline |
| M18 `b2-one-member-sentences` | 4430 | 32 | 10 workbook / 0 inline |
| M19 `homogeneous-members` | 4569 | 32 | 10 workbook / 0 inline |
| M20 `detached-members` | 4267 | 32 | 11 workbook / 0 inline |
| M21 `checkpoint-syntax-i` | 4334 | 20 | 10 workbook / 0 inline |

## Independent Review

| Reviewer | Module | Result |
| --- | --- | --- |
| Claude Opus 4.8 blocker review + follow-up | M16 `secondary-sentence-members` | Initial stale-base MDX drift blocker resolved; follow-up found no new blockers. |
| Claude Opus 4.8 blocker review | M17 `sport-i-dozvillia` | PASS; no merge blockers. |
| Claude Opus 4.8 blocker review | M18 `b2-one-member-sentences` | PASS; no merge-blocking issues found. |
| Claude Opus 4.8 blocker review | M19 `homogeneous-members` | PASS; no merge-blocking issues found. |
| Claude Opus 4.8 blocker review | M20 `detached-members` | PASS; no merge-blocking issues found. |
| Claude Opus 4.8 blocker review | M21 `checkpoint-syntax-i` | PASS; no merge blockers found. |

## Merge And Telemetry

| Module | PR | Merge Commit | Telemetry Run |
| --- | ---: | --- | --- |
| M16 `secondary-sentence-members` | #3833 | `e33630db23ceb185d835b704ca6a7c464522fa47` | `b2-m16-secondary-sentence-members-pr3833` |
| M17 `sport-i-dozvillia` | #3835 | `34d019cbaecfbcb06bac162702fac76013d80221` | `b2-m17-sport-i-dozvillia-pr3835` |
| M18 `b2-one-member-sentences` | #3837 | `cf588f4239b67c30271a6e79c78796e72f2b1c5f` | `b2-b2-one-member-sentences-codex-b2-m18-b2-one-member-sentences-20260625` |
| M19 `homogeneous-members` | #3839 | `1eee862af996c666599aca7f27ddd932babb0c2b` | `b2-homogeneous-members-codex-b2-m19-homogeneous-members-20260625` |
| M20 `detached-members` | #3840 | `f19b3011a618e6ab59d35627ba814c1380ad9498` | `b2-detached-members-codex-b2-m20-detached-members-20260625` |
| M21 `checkpoint-syntax-i` | #3841 | `10e446d83594b956854f878983338a4afaa5ffdb` | `b2-checkpoint-syntax-i-pr3841` |

All six telemetry records are persisted with `status: merged`, `swarm_used: true`, `swarm_label: thin`, and `token_source: unavailable`.

Forbidden generated artifacts included in module PRs: no.

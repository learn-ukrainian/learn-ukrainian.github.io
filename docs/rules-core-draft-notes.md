# Rules core draft — notes

Draft: `agents_extensions/shared/rules/core.md` (always loaded) and
`agents_extensions/shared/rules/core-curriculum.md` (content-seat addendum). Round 2 reconciles both
against the obligation inventory. Loading, slimming the entry files and migrating the sources stay in
Phase C.

## Coverage

- The inventory assigns 344 units to the core: 245 to P0–P9, 75 unconditional invariants and 24 to the
  content addendum. `agents_extensions/shared/rules/core-manifest.yaml` maps all 344 to an anchor;
  `tests/test_rules_core_coverage.py` checks that every anchor exists once and that each inline
  citation agrees with the manifest. No unit is left unplaced.
- Each rule appears once, in its duplicate group's canonical wording. The 107 duplicates whose
  canonical unit is also in scope map to the canonical's anchor. Q08 is cited directly, because its
  canonical unit is a reference-level linguistics rule.
- Each inline comment cites its anchor and lead unit only; the manifest carries the full mapping. Listing
  every id inline cost about 1.5 KB of the budget.
- Ten units sit under a different heading than their inventory pillar, where the rule reads whole:
  O21, Ed11 (P0 report); G17 (P1 worker); W41, F18, Er01 (P1 reviewer); Em02 (P2 review);
  E17 (P4 worktree); U22 (P5 СУМ-11 line); O23 (P9 immersion).
- Units with private provenance are stated as neutral rules; the provenance is not reproduced.

Units per section: P0 33, P1 32, P2 36, P3 15, P4 69, P5 16, P6 23, P7 10, P8 4, P9 9,
invariants 73, content addendum 24.

## Budget

`core.md` is 19,970 bytes (budget 20,000):

| Section | Bytes |
| --- | ---: |
| Header | 303 |
| P0 | 1,601 |
| P1 | 1,999 |
| P2 | 2,778 |
| P3 | 1,324 |
| P4 | 2,426 |
| P5 | 1,318 |
| P6 | 1,526 |
| P7 | 761 |
| P8 | 941 |
| P9 | 1,025 |
| Invariants | 3,021 |
| Load when | 947 |

**Overflow for curriculum seats.** The spec loads the content addendum only for curriculum seats, so it
is not in `core.md`: every other seat would carry it, and it does not fit. It lives in
`core-curriculum.md` (1,862 bytes). A curriculum seat therefore loads 21,832 bytes, 1,832 over the
20,000 "core rules file(s)" target. The whole overflow is the content addendum. Phase C decides
whether that target counts the addendum.

`core.md` has 30 bytes of headroom. Any Phase C addition needs a matching cut.

## Stale and conflicting sources — resolved from evidence

| Flag | Resolution in the core | Evidence |
| --- | --- | --- |
| S01, S07 | Never force removal; resolve a skipped worktree safely | `merge_closeout.py` treats retained or skipped trees as residual blockers; `reap_worktrees.py` protects active dispatches |
| S02 | Shared project interpreter; no worktree-local recreation recipe | Assigned-interpreter contract in `AGENTS.md` |
| S03 | A pushed deliverable is the worker's milestone, not DoD | DoD in `operator-expectations.md` and `drive-epic` |
| S06 | Primary checkout never holds feature work | Worktree guard in `scripts/delegate.py` |
| S11, S18 | Gemini/AGY never reviews code or infra, in any role | Code-review rule in `model-assignment.md`; dispatch review qualification in `scripts/delegate.py` |
| S15 | Canaries run only inside `thread-rollover` | Rollover-only startup flow in `workflow.md` |
| S34, S35 | CF APPROVE before opening a PR; squash enqueue, no `--auto` | Landing order in `critical-rules.md` §8 and `drive-epic` |
| S40 | Stress: `verify_stress` plus the СУМ-20 headword | `scripts/verification/stress.py` implements `verify_stress` |
| S42 | Missing modern meaning stays unresolved, never an invented gloss | Duplicate group's canonical wording; the СУМ-20 query has no alternate-source fallback |
| S43 | Topology labels are named among the P8 prohibited specifics | Spec P8 |
| S45 | Review is outside the author's family, not "non-Codex" | Outside-author-family rule in `operator-expectations.md` and `model-assignment.md` |
| S46 | A failed call never silently switches provider | A typed, recorded quota substitution is explicit, so it is not silent (`_acp_compat.py`) |
| Sol and Astra ids | `gpt-6.1-sol` everywhere; Astra is a role name | Catalog: `gpt-6-sol` and `gpt-6-astra` are `lifecycle: retired`, `replaced_by: gpt-6.1-sol` |
| Daily driver | Sol and Opus 5.5 first, `grok-4.7` as fallback | Catalog roles: `gpt-6.1-sol` and `claude-opus-5-5` carry `orchestration`; `grok-4.7` does not |
| Kimi scope | Web, UI and backend coding only; no Ukrainian content, reviews, consultations, design or rules | Current policy. Catalog: `kimi` and `kimicc` are not formal-review eligible |
| drive-epic split | Load-when points at `drive-epic/references/*.md` | The skill is now a 9 KB core plus references |

Stale text that Phase C must update to match: Kimi as consultant or reviewer in `model-assignment.md`,
`operator-expectations.md` item 12 and the entry files; `gpt-6-sol` and `gpt-6-astra` in rule prose;
the S11 recommendation rows in `fleet-role-scorecard.md`; the `MEMORY.md` lines behind S32–S35.

## Needs decision (policy conflicts; the core does not pick)

1. **DeepSeek (S12).** The spec says "no DeepSeek". `model-assignment.md` routes DeepSeek V4.1 Flash for
   non-language review volume, and the adapter exists. The core states only what both sides agree on:
   never a Ukrainian, folk or approval-authority seat; Flash first-party; Pro only for hard
   implementation.
2. **Small review fixes by the lead (S13).** `non-negotiable-rules.md` sends every review fix back to the
   authoring lane. `model-assignment.md` lets the lead fix CI failures it caused, up to five lines. The
   core states the first rule as its source does and says nothing about the exemption.
3. **Cursor driver seat (S14).** Driver guidance allows Auto or Composer; dispatch and review policy
   require a concrete pin. The core pins Cursor dispatch and review identities only.
4. **Authority packet before a bounded worker (S21).** One source always requires the advisory packet;
   another allows direct Luna dispatch with exact paths and a scope ceiling. The catalog has both
   routes (`execution_routing` `preferred_worker` and `direct_worker`). The core's bounded-code row
   holds for both.
5. **Grok 4.6.** Catalog notes say it is not admitted, but its `lifecycle` is `active`. The core names
   only `grok-4.7`.

## Spec-only statements (no inventory unit)

The operator role line, the loop, the infra lane's emergency authority (P6) and the publishable list
(P8). They carry no anchor.

## Mechanical changes

- `scripts/deploy_orphan_paths.sh` and `tests/test_deploy_script_idempotency.py`: `core-curriculum.md`
  stays out of Claude autoload, like `core.md`. The name avoids an existing `core-content.md` basename
  that the deploy diff excludes would shadow.
- `tests/test_sum11_source_guard.py`: the one approved СУМ-11 line in `core.md` changed wording.
- `tests/test_rules_core_budget.py` is unchanged. Every P2 model id is still active in the catalog.

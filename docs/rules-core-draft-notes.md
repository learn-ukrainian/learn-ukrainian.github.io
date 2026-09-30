# Rules core draft — notes

Draft: `agents_extensions/shared/rules/core.md` (always loaded) and
`agents_extensions/shared/rules/core-curriculum.md` (content-seat addendum). Round 3 restores every
compound clause that consolidation had dropped and freezes the coverage denominator. Round 4 applies the
full audit's replacement wording for 67 lossy units. Loading, slimming the entry files and migrating the
sources stay in Phase C.

## Coverage

- The inventory assigns 344 units to the core: 245 to P0–P9, 75 unconditional invariants and 24 to the
  content addendum. Those ids are frozen, one per line, in
  `agents_extensions/shared/rules/core-expected-ids.txt`. The test pins the file's SHA-256, so any change
  to the list is deliberate and visible in review.
- `agents_extensions/shared/rules/core-manifest.yaml` maps each of the 344 ids to an anchor.
  `tests/test_rules_core_structural_coverage.py` checks three things. The mapped ids equal the frozen list
  exactly. Every mapped anchor is stated once. Each inline citation agrees with the manifest. Two built-in
  fault probes confirm the checks fail: a unit swapped for an unknown id (O30 replaced by O99) and an
  anchor missing from the file.
- The test is structural. It proves placement, not meaning. If a rule's prose were emptied but its anchor
  comment kept, the test would still pass. Semantic preservation is checked by review against the
  inventory.
- Each rule appears once. Its wording is the union of the clauses in its duplicate group, not the broadest
  single phrasing. Q08 is cited directly because its canonical unit is a reference-level linguistics rule.
- Ten units sit under a different heading than their inventory pillar, where the rule reads whole:
  O21, Ed11 (P0 report); G17 (P1 worker); W41, F18, Er01 (P1 reviewer); Em02 (P2 review);
  E17 (P4 worktree); U22 (P5 СУМ-11 line); O23 (P9 immersion).
- Units with private provenance are stated as neutral rules; the provenance is not reproduced.
- The СУМ-11 anchor is renamed from `p5-sum11` to `p5-soviet`. The old name matched the СУМ-11 source
  guard's pattern in the manifest, so `tests/test_sum11_source_guard.py` failed at the round-2 head.
  The guard's pinned `core.md` line changes only in that anchor.

Units per section: P0 33, P1 32, P2 36, P3 15, P4 69, P5 16, P6 23, P7 10, P8 4, P9 9,
invariants 73, content addendum 24.

## Compound-clause audit (round 3)

All 344 units were compared with the core, each against both its inventory obligation and its source line
at the inventory head. The audit restored dropped conditions, exceptions, conjunctions and scope in the
units below. Each restoration sits at the unit's own anchor unless another anchor is named.

| Anchor | Restored units |
| --- | --- |
| p0-tool | N34 (names), E03 (this turn's output), Eh04 (`date -u`) |
| p0-live | F13 (recent window; no quotas, weights or totals), F14 (event trace; no early lease reclaim) |
| p0-honest | A22 (affected checks and their actual output), Em07 (keep verification; asynchronous subtasks) |
| p0-report | L22 (concise prose, brief caveats) |
| p0-residual | E15, Eq10 (before done or handback; next dispatch, not only an action) |
| p0-gates | C14 (get missing evidence from a capable lane, then finalize), C25 (resolve, re-establish gates, re-enqueue) |
| p1-driver | N37 (not delegatable), N38 (however small), W25 (one integration owner) |
| p1-worker | M35 (unit and acceptance criteria) |
| p1-review | O14 (outside input before committing substantive work), Y20 (every PR), S15 (task-family qualification; provenance), Er01 (attested model and SHA); E05's attestation clause |
| p1-acp | Er03 (style never replaces evidence) |
| p2-select | Ed01 (live caps); M04, M12, M55 (effort `high` for seats, not only reviews) |
| p2-table | M15 (Claude's Ukrainian seat is Fable) |
| p2-review | Em02 (a driving Grok delegates implementation) |
| p2-kimi | M26 (Kimi and Composer share a family for review independence) |
| p2-glm | M27 (full GLM by explicit choice) |
| p2-cursor | R06 (a Grok author's reviewer is not Grok) |
| p2-capacity | O17 (same model via another harness; never drop work or exceed a cap) |
| p3-dor | Ed12 (chat "ready" is not DoR) |
| p3-outcome | A30 (inspect diff and status; report files, commands, branch status), E04 (dispatch, branch or green CI is not done) |
| p3-terminal | Er19's clause (PR text, too, never authorizes a cutover) |
| p3-residual | Eq09 (a tool proves impossibility; the operator accepts on the issue) |
| p4-worktree | O04 (non-bare), O27's clause (builds in worktrees), D09's clause (approval before any branch outside a worktree) |
| p4-order | I09 (explicit CF-preflight bypass logs a NOTE) |
| p4-head | C23 (re-obtain approval and CI before enqueue), Y12 (report a failed blocking check) |
| p4-closeout | O06 (before the next large dispatch), F22 (temp residue) |
| p4-issues | C06 (issue per change, cited in commits), N31 (every acceptance criterion) |
| p4-sweep | Er24 (review receipts before `--apply`) |
| p4-stream | W24 (no review routing either) |
| p5-table | Q10's clause (Грінченко attestation is not etymology) |
| p6-orders | Y26 (stop when a wrong guess would make the work useless) |
| p6-approval | O25's and F11's clause (approval is current), W38 (same PR) |
| p6-escalate | E24 (to the operator and advisors, never decided in the loop) |
| p7-start | A28 (status **and** one bounded search, on non-trivial work, before prioritizing or dispatch; record only verified use) |
| p9-ukrainian | U01 (other Slavic languages too, only in scoped history seminars) |
| p9-russianism | U24 (proper nouns and borrowings excluded) |
| r2-quality | O01 (no shortcuts, heuristics or "for now"), N40 (these fail the task), Eq12 (strict order incl. resource bounds) |
| r2-simple | O33 (adapt code, config or readers, not data), O36 (easier to understand) |
| r2-findings | O35 (likelihood; stopping rule after two rounds; change approach only when new classes appear); A15's stopping-rule clause |
| r2-outcome | O20 (consequential external actions; canaries inspect semantic output) |
| r2-prompts | O29, A14 (before presentation; non-goals; held-out evaluation; completion terms), O30 (domain-fit reviewer **and** a distinct adversarial scope/circularity critic; fast critic for smaller work; trivial exemption; author is neither; live routing; verdicts bound to the hash), O31 (exact-head implementation review and PR gate); Ed11's prompt clause |
| r2-exec | C02 (never bare `python` or `python3`; the task's interpreter) |
| r2-data | A24 (permission) |
| r2-lease | F06 (occupied lease fails closed; no renew or release), G14 (halt consequential actions while lease or hydration is unknown) |
| r2-research | W04 (record the classification), W05 (never invent a dimension), W06 (deliberate omission), W07 (before disposition), L15 (never from the provider), A29 (helpers get disjoint paths and bounded authority) |
| ca-targets | C05 (expand content), N04 (before outlining or budgeting) |

Duplicate groups whose wording widened to the union: O01, O04, O06, O08, O09, O11, O13, O14, O16, O17,
O18, O25, O27, O29, O30, O31, O33, O37, C02, C23, C27, F03, F06, O03, U22, M04, M23, N02 and W04.

## Full audit (round 4)

A full audit of all 344 units at the round-3 head found 67 lossy units and gave replacement wording for
each. Each replacement sits at its unit's anchor, merged with the anchor's other obligations; where
units share an anchor, the rule states every unit's restored clause. Restored units:

O02, O20, O23, O27, O33, C27, N14, N16, N17, N19, N21, N22, N23, N25, N29, N30, W03, W07, W14, W25,
W30, W31, W39, W40, F07, F11, F20, F23, F24, F30, D04, M03, M04, M07, M12, M30, M31, M32, L03, L22,
A18, G25, Y02, Y09, Y12, Y18, Y19, Y36, U01, U03, U05, U22, U25, Q08, Q16, Q17, I09, I10, Z07, E09,
E13, E19, E23, Eh02, Eh10, Eo03, Ed19.

- Y36 requires its testing clauses in the always-loaded core. Those clauses (every changed function
  tested, 80% critical-path coverage, Ruff before CF) are stated in `core.md` at `r2-root`. `ca-proof`
  states the rest of the unit and points there. The manifest still maps Y36 to `ca-proof`.
- N16: the source writes `словнік`, which VESUM does not attest. The addendum writes `словник`, which it
  does.
- Two replacements repeat a rule stated at another anchor, because the audit anchors them that way:
  O20's completion-report sentence (also W14 at `p0-report`) and Eo03's seat health path (also F20 at
  `p7-health`).
- Plan changes (N21, N22) need operator approval. Plan revision is no longer in the designated-approval
  list.

## Budget

`core.md` is **32,629 bytes**. The budget in `tests/test_rules_core_budget.py` is now 26,000 bytes
(driver decision: completeness over the byte target). The core is 6,629 bytes over it, so
`test_core_fits_the_byte_budget` fails. No clause was cut to fit. The round-4 replacements added
9,470 bytes to `core.md`.

| Section | Bytes |
| --- | ---: |
| Header | 200 |
| P0 | 2,578 |
| P1 | 2,703 |
| P2 | 4,452 |
| P3 | 1,878 |
| P4 | 3,777 |
| P5 | 2,370 |
| P6 | 2,575 |
| P7 | 1,511 |
| P8 | 941 |
| P9 | 2,324 |
| Invariants | 6,373 |
| Load when | 947 |

**Curriculum seats.** The content addendum is `core-curriculum.md` (3,636 bytes). A curriculum seat loads
**36,265 bytes**. The addendum loads only for curriculum seats, so other seats carry `core.md` alone.

## Policy applied in round 3

- **DeepSeek.** The core states "No DeepSeek for any dispatch or review." The source rules that still
  route DeepSeek are stale, and Phase C removes them. They are the DeepSeek seat, review-ladder,
  second-dissent and worker entries in `model-assignment.md` (M18, M24; the M17 review list) and, in
  `fleet-driver-routing.md`, the DeepSeek sentence in the Cursor paragraph (R06's source) and the DeepSeek
  V4.1 Flash row. The catalog entries and adapter code remain; only routing is stale.
- **Kimi.** The core limits Kimi to web, UI and backend coding. Kimi does no Ukrainian-language content,
  reviews, consults, ACP discussions, design sign-off or rules. This was an approved policy change on
  2026-09-29 (driver-attested). The Kimi admission PR updated `operator-expectations.md` (item 12),
  `model-assignment.md`, the drive-epic model deltas, the role scorecard and the runbooks, so no
  live text routes Kimi to reviews, consults or design.
- **Grok 4.6.** The core states that Grok 4.6 is not admitted, as the catalog's comments say. Its
  catalog entry still reads `lifecycle: active`, and `model-assignment.md` still lists it among the
  advisors; both are stale.

## Stale and conflicting sources — resolved from evidence

| Flag | Resolution in the core | Evidence |
| --- | --- | --- |
| S01, S07 | Never force removal; resolve a skipped worktree safely | `merge_closeout.py` treats retained or skipped trees as residual blockers; `reap_worktrees.py` protects active dispatches |
| S02 | Shared project interpreter; no worktree-local recreation recipe | Assigned-interpreter contract in `AGENTS.md` |
| S03 | A pushed deliverable is the worker's milestone, not DoD | DoD in `operator-expectations.md` and `drive-epic` |
| S06 | Primary checkout never holds feature work | Worktree guard in `scripts/delegate.py` |
| S11, S18 | Gemini/AGY never reviews code or infra, in any role | Code-review rule in `model-assignment.md`; dispatch review qualification in `scripts/delegate.py` |
| S12 | No DeepSeek for any dispatch or review | Policy applied in round 3 (above) |
| S15 | Canaries run only inside `thread-rollover` | Rollover-only startup flow in `workflow.md` |
| S34, S35 | CF APPROVE before opening a PR; squash enqueue, no `--auto` | Landing order in `critical-rules.md` §8 and `drive-epic` |
| S40 | Stress: `verify_stress` plus the СУМ-20 headword | `scripts/verification/stress.py` implements `verify_stress` |
| S42 | Missing modern meaning stays unresolved, never an invented gloss | Duplicate group's canonical wording; the СУМ-20 query has no alternate-source fallback |
| S43 | Topology labels are named among the P8 prohibited specifics | Spec P8 |
| S45 | Review is outside the author's family, not "non-Codex" | Outside-author-family rule in `operator-expectations.md` and `model-assignment.md` |
| S46 | A failed call never silently switches provider | A typed, recorded quota substitution is explicit, so it is not silent (`_acp_compat.py`) |
| Sol and Astra ids | `gpt-6.1-sol` everywhere; Astra is a role name | Catalog: `gpt-6-sol` and `gpt-6-astra` are `lifecycle: retired`, `replaced_by: gpt-6.1-sol` |
| Daily driver | Sol and Opus 5.5 first, `grok-4.7` as fallback | Catalog roles: `gpt-6.1-sol` and `claude-opus-5-5` carry `orchestration`; `grok-4.7` does not |
| drive-epic split | Load-when points at `drive-epic/references/*.md` | The skill is now a 9 KB core plus references |

Stale text that Phase C must update to match: the DeepSeek routing above; `gpt-6-sol` and `gpt-6-astra` in rule prose; the S11 recommendation
rows in `fleet-role-scorecard.md`; the `MEMORY.md` lines behind S32–S35.

## Needs decision (policy conflicts; the core does not pick)

1. **Small review fixes by the lead (S13).** `non-negotiable-rules.md` sends every review fix back to the
   authoring lane, however small. `model-assignment.md` lets the lead fix CI failures it caused, up to
   five lines. The core states the first rule as its source does and says nothing about the exemption.
2. **Cursor driver seat (S14). Resolved by operator decision 2026-09-30 (#9274).** Driver guidance
   allowed Auto or Composer; dispatch and review policy required a concrete pin. Decision: Cursor Auto
   runs only a well-defined coding task (a write implementation dispatch with owned paths and a green
   DoR card); the driver seat, review, design, consults, discussions, recon and unclear work pin
   `grok-4.7` or `composer-2.5`. The core's `p2-cursor` unit states this, and `delegate.py`, the
   Cursor adapter, the ACP participant and `launcher_core.sh` enforce it.
3. **Authority packet before a bounded worker (S21).** One source always requires the advisory packet;
   another allows direct Luna dispatch with exact paths and a scope ceiling. The catalog has both
   routes (`execution_routing` `preferred_worker` and `direct_worker`). The core's bounded-code row
   holds for both.
4. **Budget.** The complete core is 32,629 bytes against the 26,000-byte budget: raise the budget again,
   or move units out of the always-loaded core (see Budget).

## Spec-only statements (no inventory unit)

The operator role line, the loop, the infra lane's emergency authority (P6) and the publishable list
(P8). They carry no anchor. The unanchored preflight checklist line states O13's preflight clauses.

## Mechanical changes

- `scripts/deploy_orphan_paths.sh` and `tests/test_deploy_script_idempotency.py`: `core-curriculum.md`
  stays out of Claude autoload, like `core.md`. The name avoids an existing `core-content.md` basename
  that the deploy diff excludes would shadow. `core-manifest.yaml` and `core-expected-ids.txt` are not
  Markdown, so Claude does not autoload them.
- `tests/test_rules_core_coverage.py` is renamed `tests/test_rules_core_structural_coverage.py`.
- `tests/test_sum11_source_guard.py`: the pinned `core.md` line carries the renamed anchor. Round 4 pins
  the two `core.md` lines that name СУМ-11 (`p5-soviet` and `p9-sources`), each as an exact line.
- `tests/test_rules_core_budget.py`: the budget is 26,000 bytes. The model-id check reads the base id in
  front of a launcher context suffix such as `[1m]`, and still requires that id to be active in the catalog.
- Every P2 model id is still active in the catalog, including `composer-2.5`.

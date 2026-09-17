# Docs-knowledge program rollout (authority → inventory → optional OpenWiki)

**Status:** Plan of record after #5537 freeze
**Stream:** `docs-knowledge` (epic [#5535](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5535))
**Decision:** [ADR-013](../architecture/adr/adr-013-docs-knowledge-openwiki.md)
**Authority contract:** [docs-authority-lifecycle.md](../architecture/docs-authority-lifecycle.md)
**Version:** 2026-09-17 (incorporates Fable FBL-001–FBL-013)

## Outcome

Future agents orient with less context, fewer repeated scans, and fewer stale
stack claims, while:

- code/tests remain behavioral truth;
- curated `docs/` have explicit authority and lifecycle;
- `openwiki/` stays optional and killable;
- Monitor/session streams remain live-state authority;
- learner UI remains plain Astro under `site/`.

## Wave DAG (executable order)

```
Wave 0  #5537 (this freeze: ADR + contract + stream registry)     ← current
Wave 1  #5536 inventory (tracked-only; baseline canary)  ∥  #5538 Astro truth
Wave 2a #5539 IA + migration tooling → #5540 separation (session-state gate named)
Wave 2b #5541 OpenWiki pilot (code-anchored; allowlist v1)         ∥ parallel with 2a
Wave 3  #5542 validation + bounded updates (after #5541 verdict)
Wave 4  #5543 three-arm measurement → cutover or kill → close
```

Safe parallelism: #5536∥#5538; Wave 2a∥2b (docs-prose vs `openwiki/` worktree).
No other overlap.

## Wave 0 deliverables (#5537) — this PR

- [x] Register `docs-knowledge` in `scripts/config/issue_streams.yaml`
- [x] Mirror row in `docs/WORKSTREAMS.md`
- [x] ADR-013 conditional OpenWiki + provider route + exclusions
- [x] Authority/lifecycle field contract
- [x] FBL checklist incorporated (below)
- [ ] GitHub: update #5535 status to FROZEN; point children at merged paths
- [ ] Independent cross-family review of this PR

**Non-goals for Wave 0:** OpenWiki install, docs path moves, inventory generation.

## Fable checklist → disposition

| ID | Requirement | Where satisfied |
| --- | --- | --- |
| FBL-001 | Dedicated stream + migrate off infra lease | `issue_streams.yaml` + this plan; #5535 is stream epic |
| FBL-002 | Tracked-only inventory; fresh worktree | Authority contract allowlist; #5536 owns enforcement |
| FBL-003 | Hard-exclude root instruction writes | ADR-013 + #5541/#5542 bodies |
| FBL-004 | Named provider route + billing + family | ADR-013 provider table (DeepSeek Flash first-party) |
| FBL-005 | Three-arm measurement vs Monitor baseline | Authority contract + #5543; #5536 captures baseline |
| FBL-006 | Boundary vs Monitor + Research Registry | ADR-013 precedence table |
| FBL-007 | Re-anchor Astro on 2026-06-09 ACCEPTED | #5538 verifies; does not re-author |
| FBL-008 | Session-state gate named | #5540 owns; surfaces listed in authority exclusions |
| FBL-009 | #5541 parallel with allowlist v1 | DAG Wave 2b; #5541 body already amended |
| FBL-010 | Extended authority classes + immersion example | ADR-013 + authority contract |
| FBL-011 | ADR path, >20-file carve-out, link policy | ADR-013 path; authority contract move/link policy; #5536 output path below |
| FBL-012 | CI model calls deferred | ADR-013 automation venue |
| FBL-013 | Ukrainian verbatim-only | ADR-013 + #5541 validator obligation |

## #5536 output path (inventory)

Deterministic inventory tooling writes under a tracked path owned by #5536
(recommended: `docs/knowledge/inventory/` or `audit/docs-inventory/` — exact
path chosen in the #5536 PR). Manifest must record git commit SHA, tracked-file
digest, and exclude gitignored trees.

## #5538 Astro truth

Canonical statement already exists:
`docs/architecture/2026-06-09-ui-astro-without-starlight.md` (ACCEPTED).
#5538 classifies residue and cosmetic renames; it does not mint a second
canonical architecture statement.

## #5539 migration tooling

Must cite lessons from `docs/cleanup-plan-2026-q2.md` and require a smoke build
gate for learner `site/` when moves touch MDX/import surfaces. External-link
policy: breadcrumb stubs for high-traffic paths (default).

## #5540 session-state

Do not move `docs/session-state/` until a named gate owner records predicate
proof that Monitor/session streams remain healthy (FBL-008). Prefer split:
operational pointers stay stream-owned; curated docs never embed live leases.

## #5541 pilot constraints (summary)

- Fresh worktree; tracked allowlist v1 only
- ≤8 code-anchored pages; no docs-prose until allowlist v2
- Disable/revert root instruction outputs
- Record DeepSeek Flash (or GO'd alternate) model/family on the PR
- Independent cross-family review after generation

## #5542 / #5543

Recurring automation and cold-start cutover only after pilot exit criteria in
ADR-013. Program may close successfully with OpenWiki rejected.

## Adjacent programs

- Fleet-comms / Channels work under infra or monitor streams must not be
  measured by the #5543 “how does fleet communication work?” canary without
  coordinating docs with that program (awareness only).
- Predecessor cleanup epic #1863 remains closed; lessons retained.

## Verification for this plan

- Stream registry lists `docs-knowledge` → #5535
- ADR-013 Accepted and indexed
- Authority contract path stable
- Next executable issue after merge: **#5536** (∥ #5538)

# Documentation authority and lifecycle contract

**Status:** Binding for stream `docs-knowledge` (epic #5535)
**Frozen by:** [#5537](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5537) / [ADR-013](adr/adr-013-docs-knowledge-openwiki.md)
**Date:** 2026-09-17

This file is the field-level contract agents and tooling must obey when reading,
moving, generating, or citing repository knowledge. It does not replace
`/api/rules` or code/tests.

## Authority classes

| Class | Location | Lifecycle | Who may change | What it may override |
| --- | --- | --- | --- | --- |
| Behavioral truth | Code + tests | Continuous | PR + CI + CF review | Prose that contradicts observed behavior |
| Config-as-policy | `scripts/config.py`, `scripts/config/*.yaml` (typed policy values) | Continuous | PR + CI + CF | Stale curated docs that restate the same knobs |
| Binding rules (source) | `agents_extensions/shared/rules/`, `contracts/` | Continuous; served at `/api/rules` | PR; deploy regenerates copies | Deployed copies; never OpenWiki paraphrases |
| Deployed rule copies | `.claude/`, `.codex/`, `.agent/`, `.gemini/` | Generated consumers | Deploy command only | Nothing — consumers only; drift is a defect |
| Curated docs | Tracked `docs/**` (see allowlist) | `draft` → `active` → `superseded` → `archive` | PR; owner in frontmatter when present | Nothing over code/config/rules; may guide humans |
| Architecture ADRs | `docs/architecture/adr/` | Permanent | New ADR; never reuse numbers | Prior ADRs only via explicit supersession |
| Decision journal | `docs/decisions/` (dated, expiring) | Expiring | `check_decisions.py` | Nothing permanent; not an ADR substitute |
| Pending decision cards | `docs/decisions/pending/` | Blocking until resolved | Operator/advisor disposition | Blocks related work; does not rewrite code |
| Planning / epics | GitHub issue/epic bodies + `docs/plans/` | Issue state is SSOT | Issue/PR workflow | Plans point at issues; GH issue state wins over stale plan text |
| Agent memory files | Repo `memory/` / harness memory paths when tracked | Behavioral continuity | Owning harness discipline | Never binding policy; locator/continuity only |
| Generated evidence | top-level `audit/`, batch receipts | Append-only / regenerate | Owning pipeline | Not curated docs; cite as evidence, not policy |
| OpenWiki | `openwiki/` (when present) | Generated; killable | Pilot/regen PR only | **Nothing** — locator + citation only |
| Live ops | Monitor API, session streams, Fleet Comms | Live | Runtime systems | **Never** durable docs fact |
| Research registry | ADR-011 surfaces | Task-scoped | Registry tooling | Attributed fetch required when claimed |
| Archives | Named archive trees / closed issues | Frozen | Explicit archive PR | Historical only |

### Conflict-resolution procedure

When two classes disagree on the same fact:

1. **Classify the fact type** (behavior, config knob, binding rule, pedagogy intent, live ops, planning state).
2. **Apply the row above** — higher-authority class wins only for fact types it owns.
3. **If both claim ownership, decide by evidence of staleness**, not by layer name:
   - Prefer the artifact with a newer verified commit, live probe, or explicit supersession link.
   - Prefer tool-backed runtime/config reads over narrative docs.
   - Prefer `/api/rules` / `agents_extensions/` over deployed copies when they drift.
4. **Record the disposition** (issue comment or decision card) when the conflict is load-bearing.
5. OpenWiki **never** breaks ties — it may only cite the winning authority.

**Worked example (immersion):** operator-expectations item 9 + `IMMERSION_POLICIES` in config are the authoritative immersion knobs for runtime. A curated docs page (or historical north-star text) that says “docs win over config” is stale for that fact type; config-as-policy wins until an ADR explicitly supersedes it. OpenWiki must quote the operator-contract / config path, not invent a Ukrainian-only A1 chrome policy.

## Allowlist / exclusion policy (v1)

**Inventory and OpenWiki reads may only use git-tracked paths** from a fresh
dispatch worktree (FBL-002). Gitignored and untracked corpora (`data/`, local
caches, private mounts) are forbidden inputs.

### Allowlist v1 (OpenWiki pilot pages — code-anchored)

Eligible **read** roots for ≤8 pilot pages (#5541):

- `scripts/` (pipeline, Monitor API, agent runtime, orchestration)
- `site/` and `site/src/` (learner Astro product — stack truth only)
- `docs/architecture/` and `docs/best-practices/` (contracts, not live state)
- Selected root instruction files for *inventory classification only*
  (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`) — **never as OpenWiki write targets**

### Explicit exclusions (reads)

- `docs/session-state/**` and any Monitor projection dumps
- Private topology, credentials, tokens, raw IP addresses
- `curriculum/**` lesson bodies as free synthesis (Ukrainian = verbatim quote only)
- `wiki/**` generated seminar wiki (separate authority)
- Deployed harness trees listed above

### Generator write surface (hard — FBL-003)

The **only** approved OpenWiki write surface is `openwiki/**`.

OpenWiki must not create or modify anything outside `openwiki/**`, including
(but not limited to):

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`
- `agents_extensions/`, `.claude/`, `.codex/`, `.agent/`, `.gemini/`
- `docs/`, `scripts/`, `site/`, `curriculum/`, `wiki/`
- `docs/session-state/**`

Disable non-`openwiki/**` outputs if upstream supports it; otherwise **revert
every such path before the pilot PR** and record the revert in the pilot
report. A later human-authored root pointer to `openwiki/quickstart.md` is
separate instruction-file scope under #5543 — never a generator write.

Allowlist v2 (docs-prose synthesis) is owned by #5539/#5540 after IA migration.

## Rollback and archive

| Change type | Rollback |
| --- | --- |
| OpenWiki pilot PR | Revert PR; delete `openwiki/` tree; program continues on deterministic index |
| Docs path move | Breadcrumb stubs for high-traffic paths (#5539 policy); historical GitHub links may break otherwise |
| Authority contract edit | New PR; do not silently edit Accepted ADR — amend via new ADR or dated amendment section |
| Stream registry row | Same PR discipline as `issue_streams.yaml`; auditor must stay green |

## Move-PR carve-out

Documentation moves that touch **>20 files** may ship as a dedicated move PR
without mixing behavior changes (FBL-011). Behavior + move mixtures are
forbidden.

## External inbound links

GitHub issue/PR Markdown links to `docs/` paths are not rewritten by repo
redirects. #5539 must choose: breadcrumb stubs for high-traffic moved paths, or
explicit acceptance of historical breakage. Default for high-traffic paths:
breadcrumb stub files that point to the new location.

## Measurement ownership

| Arm | Owner issue | Baseline |
| --- | --- | --- |
| Pre-migration cold-start | #5536 (capture) | Monitor API orientation + current docs scan cost |
| Post-migration, pre-OpenWiki | #5543 | Same question classes |
| Post-OpenWiki | #5543 | Only if pilot adopt criteria met |

Wrong baseline (empty cold start without Monitor) is forbidden (FBL-005).

## Related

- [ADR-013](adr/adr-013-docs-knowledge-openwiki.md)
- [Rollout plan](../plans/2026-09-17-docs-knowledge-rollout.md)
- [Plain Astro ACCEPTED](2026-06-09-ui-astro-without-starlight.md)
- [Cleanup plan lessons](../cleanup-plan-2026-q2.md)

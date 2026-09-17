# Documentation authority and lifecycle contract

**Status:** Binding for stream `docs-knowledge` (epic #5535)
**Frozen by:** [#5537](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5537) / [ADR-013](adr/adr-013-docs-knowledge-openwiki.md)
**Date:** 2026-09-17

This file is the field-level contract agents and tooling must obey when reading,
moving, generating, or citing repository knowledge. It does not replace
`/api/rules` or code/tests.

## Authority classes

| Class | Location | Lifecycle | Who may change | Citation rule |
| --- | --- | --- | --- | --- |
| Behavioral truth | Code + tests | Continuous | PR + CI + CF review | Prefer tests over prose when they disagree |
| Binding rules | `agents_extensions/shared/rules/` | Continuous; served at `/api/rules` | PR; deploy copies regenerated | Never duplicate binding text into OpenWiki |
| Deployed rule copies | `.claude/`, `.codex/`, `.agent/`, `.gemini/` | Generated consumers | Deploy command only | Out of scope for docs/OpenWiki writes |
| Curated docs | Tracked `docs/**` (see allowlist) | `draft` → `active` → `superseded` → `archive` | PR; owner named in frontmatter when present | Path + date; stale claims fail audits |
| Architecture ADRs | `docs/architecture/adr/` | Permanent | New ADR; never reuse numbers | Cite ID + status |
| Decision journal | `docs/decisions/` | Expiring | `check_decisions.py` | Not permanent architecture |
| Planning / epics | GitHub issues + `docs/plans/` | Issue state is SSOT | Issue/PR workflow | Plans point at issue numbers |
| Generated evidence | top-level `audit/`, batch receipts | Append-only / regenerate | Owning pipeline | Not curated docs |
| OpenWiki | `openwiki/` (when present) | Generated; killable | Pilot/regen PR only | Locator + citation; never authority |
| Live ops | Monitor API, session streams, Fleet Comms | Live | Runtime systems | **Never** assert as durable docs fact |
| Research registry | ADR-011 surfaces | Task-scoped | Registry tooling | Attributed fetch required when claimed |
| Archives | Named archive trees / closed issues | Frozen | Explicit archive PR | Historical only |

## Allowlist / exclusion policy (v1)

**Inventory and OpenWiki reads may only use git-tracked paths** from a fresh
dispatch worktree (FBL-002). Gitignored and untracked corpora (`data/`, local
caches, private mounts) are forbidden inputs.

### Allowlist v1 (OpenWiki pilot pages — code-anchored)

Eligible source roots for ≤8 pilot pages (#5541):

- `scripts/` (pipeline, Monitor API, agent runtime, orchestration)
- `site/` and `site/src/` (learner Astro product — stack truth only)
- `docs/architecture/` and `docs/best-practices/` (contracts, not live state)
- Selected root instruction files for *inventory classification only*
  (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md`) — **never as OpenWiki write targets**

### Explicit exclusions

- `docs/session-state/**` and any Monitor projection dumps
- Private topology, credentials, tokens, raw IP addresses
- `curriculum/**` lesson bodies as free synthesis (Ukrainian = verbatim quote only)
- `wiki/**` generated seminar wiki (separate authority)
- Deployed harness trees listed above
- OpenWiki must not write root instruction files or `agents_extensions/`

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

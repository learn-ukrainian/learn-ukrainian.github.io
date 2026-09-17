# ADR-013: Docs-knowledge authority and conditional OpenWiki

**Status**: Accepted
**Date**: 2026-09-17
**Deciders**: Operator (program charter #5535); infra driver implementing #5537 freeze
**Advisors**: Claude Fable 5 architecture review on #5535 (2026-07-20, READY_AFTER_CHANGES)
**Related**: [#5535](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5535),
[#5537](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5537),
[#5536](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5536)–[#5543](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5543),
[plain-Astro ACCEPTED record](../2026-06-09-ui-astro-without-starlight.md),
[ADR-011 Project Research Registry](adr-011-project-research-registry.md),
[rollout plan](../../plans/2026-09-17-docs-knowledge-rollout.md),
[authority contract](../docs-authority-lifecycle.md)

## Context

Agents waste context on repeated docs scans and stale stack claims
(Docusaurus/Starlight residue, mixed operational state under `docs/`). The
#5535 program separates:

1. code/tests as behavioral truth;
2. curated `docs/` with explicit authority and lifecycle;
3. generated `openwiki/` as a killable navigation/synthesis layer;
4. Monitor / session streams as live operational state;
5. plain Astro under `site/` as the learner-facing product
   ([2026-06-09 ACCEPTED](../2026-06-09-ui-astro-without-starlight.md)).

Fable review (FBL-001–FBL-013) required a dedicated `docs-knowledge` stream, a
tracked-only inventory baseline, hard exclusion of root instruction files from
generator output, a named provider route before any pilot, and a measurement
design that compares against the existing Monitor-API orientation baseline — not
against an empty cold start.

LangChain OpenWiki (upstream MIT, early minor releases) can emit root
`AGENTS.md` / `CLAUDE.md` by default. That conflicts with this repository's
`agents_extensions/` → deploy-copy contract. Full adoption today would duplicate
Monitor orientation and the Project Research Registry (ADR-011) without a
measured gain.

## Decision

**Conditional hybrid — not unconditional OpenWiki adoption.**

1. **No-regret core:** a deterministic documentation inventory/index and
   authority/lifecycle contract (#5536, #5539, this ADR) proceed regardless of
   OpenWiki.
2. **Marginal bet:** OpenWiki may be piloted only under #5541 allowlist v1
   (code-anchored pages; tracked paths only) after this freeze merges.
3. **Killable:** the program may complete on the deterministic-index-only path
   if the pilot is rejected with evidence (#5541–#5542 closed rejected; #5543
   measures migration alone).

### Authority precedence (per fact type)

| Fact type | Authority | Generated OpenWiki role |
| --- | --- | --- |
| Runtime behavior | Code + tests | May cite paths; never redefine behavior |
| Binding agent rules | `agents_extensions/shared/rules/` (+ served `/api/rules`) | Locator only; never duplicate binding text |
| Deployed rule copies | Generated from `agents_extensions/` | Out of scope; never write `.claude/` / `.codex/` / `.agent/` / `.gemini/` |
| Curated docs | Tracked `docs/**` with declared lifecycle | May summarize with citations |
| ADRs / decisions | `docs/architecture/adr/`, `docs/decisions/` | Cite; do not invent supersession |
| Live ops / leases / capacity | Monitor API + session streams | **Forbidden** to mirror or assert as current |
| Research provenance | Project Research Registry (ADR-011) | Cross-link; do not replace attributed fetch |
| Learner UI stack truth | Plain Astro ACCEPTED record + `site/` | Must not claim Starlight/Docusaurus as current |
| Ukrainian language claims | VESUM / `sources` / verbatim quoted curriculum | **Verbatim quote only** in generated pages (FBL-013) |
| Immersion / scaffolding policy | Operator contract item 9 + level rules | Precedence example: A1 English scaffolding is intentional; generated docs must not “correct” it |

Worked immersion example: an OpenWiki page about A1 module chrome may quote the
operator-contract exception and the module plan; it must not invent a
Ukrainian-only A1 chrome policy that contradicts the exception.

### Stream ownership

Dedicated stream key `docs-knowledge`, epic **#5535**, registered in
`scripts/config/issue_streams.yaml`. Infra board #6943 (successor to #4707) is
predecessor/adjacent awareness only — not the lease or membership home for
#5536–#5543 after this freeze.

### OpenWiki provider route (pilot)

| Field | Decision |
| --- | --- |
| Preferred generator | **DeepSeek V4 Flash** via first-party DeepSeek API (`deepseek-direct` / OpenCode seat) |
| Billing bucket | Prepaid DeepSeek USD (`scripts/config/agent_budgets.yaml`) |
| Credential owner | Operator-held DeepSeek API credential already used by the fleet |
| Rejected routes | **OpenRouter** (excluded by #5537); **Hermes host gateway** (removed from this host 2026-08-16) |
| Alternate (if DeepSeek unavailable) | Gemini through existing Google AIS / AGY route — requires present-tense GO before use for OpenWiki |
| Automation venue (pilot #5541) | **Local dispatch worktree only** — one generation pass, PR-bound |
| Automation venue (recurring #5542) | **Not authorized in CI** until #5542 explicitly chooses a venue; default remains local/operator-triggered |
| Generator family on receipts | Record concrete model ID + family on every pilot/regen PR |

No viable named route → skip OpenWiki; continue deterministic index only.

### Hard exclusions (generator output)

OpenWiki must not create or modify:

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md` (root instruction set)
- anything under `agents_extensions/`, `.claude/`, `.codex/`, `.agent/`, `.gemini/`
- live state under `docs/session-state/` or Monitor projections

Disable those outputs if upstream supports it; otherwise revert before the pilot
PR lands (FBL-003).

### Pilot exit criteria (adopt / amend / reject)

On the ≤8-page allowlist v1 set:

1. 100% of material claims trace to a cited current tracked source (full audit, not a sample).
2. Zero authority violations (table above).
3. Zero stale-stack claims (Starlight/Docusaurus-as-current = fail).
4. Zero non-verbatim Ukrainian text.
5. Full generation cost recorded (tokens/calls/$); thresholds set from measurement, not invented here.
6. Cold-start dry-run on ≥3 of the #5543 question classes: non-inferior correctness at ≤ current context bytes for at least one class.

**Reject/kill:** fabricated source path; refuted claim surviving one regeneration;
upstream churn needing >1 compatibility fix in the pilot window; or no viable
provider route.

## Alternatives considered

- **Full OpenWiki adoption now** → rejected: immature upstream, no measured gain over Monitor orientation, root-file write hazard.
- **Deterministic index only (never pilot OpenWiki)** → accepted as the success path if pilot kills; not chosen as the *only* path a priori because a bounded pilot is cheap relative to repeated agent scans *if* exit criteria pass.
- **OpenRouter-hosted generation** → rejected by #5537 charter.
- **CI-native recurring OpenWiki updates** → deferred; new spend/egress class (FBL-012); local pilot first.
- **Keep program under infra-harness #6943** → rejected (FBL-001): lease collision with other infra work; fail-closed own-stream sweep.

## Consequences

**Positive:**
- Clear authority map agents can cite without chat history.
- Stream registry makes #5535 a first-class lane.
- OpenWiki cannot silently rewrite binding instruction files.

**Negative / risks:**
- Two knowledge surfaces (Monitor orientation + optional OpenWiki) until #5543 cutover or kill.
- Provider outage blocks only the pilot, not the deterministic core.

**Neutral / follow-ups:**
- #5536 inventory (tracked-only) owns baseline canary capture.
- #5538 verifies the existing plain-Astro ACCEPTED statement; does not re-author it.
- #5541 may run in parallel with #5539/#5540 on code-anchored pages (allowlist v1).

## Verification

- `scripts/config/issue_streams.yaml` contains `docs-knowledge: {epics: [5535]}`.
- `docs/WORKSTREAMS.md` mirrors the stream row.
- Authority contract file exists and matches the precedence table.
- #5536–#5543 bodies reference `docs-knowledge` / #5535 (not #4707 as live parent).
- No OpenWiki package install and no `docs/` moves in the #5537 PR itself.
- Pilot PRs under #5541 must show generator model/family + exclusion revert proof.

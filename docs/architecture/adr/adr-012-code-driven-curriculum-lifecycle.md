# ADR-012: Code-driven curriculum lifecycle and prompts as versioned source

**Status**: Proposed
**Date**: 2026-07-14
**Deciders**: Krisztian (project owner); Codex orchestrator; Claude Opus and Gemini 3.1 Pro (architecture dissent panel)
**Related**: [#5152](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5152), [#5153](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5153), [#5144](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5144), PR [#5148](https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/5148), ADR-004, [prompt responsibility parity](../curriculum-lifecycle-prompt-responsibility-parity.md)

## Context

Curriculum preparation, building, review, repair, certification, and repository
integration are expressed in several incompatible places. The repository has 39
files and 5,173 lines under `docs/prompts/orchestrators`, in addition to skill
instructions and build-phase prompts. Operators consequently paste large run
prompts that repeat worktree, protected-file, telemetry, review, and lifecycle
rules. Those copies drift and make policy changes difficult to test.

The completed #5144 / PR #5148 introduced `$track-completion`: a manifest-backed,
one-module state machine for built, unbuilt, and partial modules, with a durable
ledger, repair ownership, reviewer-instability handling, independent review, and
publication lifecycle. It deliberately preserves `$post-build-review` as the
canonical read-only, versioned, exact-byte, fail-closed built-module gate. It does
not yet own source/dossier/wiki/rights preparation, track queues and waves, or a
multi-gate certification chain.

The gap is material at repository scale. At this decision, BIO has 410 manifest
modules but only seven at `module-ready` or later and 405 remain unbuilt. FOLK has
40 built modules, including M01, which need certification rather than rebuilding
by default. C1, C2, and most seminar tracks primarily need unbuilt paths. A single
FOLK-specific run prompt cannot cover those states safely.

## Decision

Add one code-driven `$curriculum-lifecycle` entry point. Keep the operator request
short; derive the queue, state, next action, prompt, evidence identity, and resume
behavior from versioned repository source.

### Component boundaries

| Component | Owns | Must not own |
| --- | --- | --- |
| Track coordinator | Manifest queue/DAG, selectors, waves, quota/health pauses, leases, resume, issue/worktree/PR identity | Phase-specific content or track-name branches |
| Module lifecycle | One-module derived state, transition validation, repair ownership, invalidation, instability, integration state | Prompt prose or track-specific prerequisites |
| Phase adapters | PREPARE, PLAN, BUILD, CERTIFY, and integration commands with typed inputs/outputs | Queue policy or hidden readiness state |
| Track/family profiles | Required evidence, validators, adapter IDs, policy/prompt fragment IDs, reviewer restrictions, certification chain | Free-form prompt text or executable code |
| Prompt resolver | Versioned manifests, typed context/result schemas, ordered includes, exact rendered bytes/hash, compatibility checks | A general prompt language or model-selected composition |
| Evidence ledger | Append-only transition evidence and deterministic derived state | Learner artifacts, generated reviews, or certification by assertion |

`curriculum/l2-uk-en/curriculum.yaml` is authoritative for active tracks, module
membership, order, and declared prerequisites. Filesystem globbing may establish
artifact presence but may not create off-manifest work.

The existing `$track-completion` implementation remains the module engine. It is
extended behind compatible schemas rather than replaced. Existing BIO readiness
gates supply the first PREPARE adapter pattern; V7 remains the BUILD adapter;
`$post-build-review` remains the first CERTIFY adapter. No adapter's internal
cache, score, sidecar, or generated report may become lifecycle authority.

### Derived lifecycle

The coordinator derives the earliest unmet or stale state instead of trusting a
mutable status flag:

```text
INVENTORY
  -> PREPARE_REQUIRED <-> PREPARATION_REPAIR_REQUIRED
  -> PLAN_REVIEW_REQUIRED <-> PLAN_REPAIR_REQUIRED
  -> BUILD_REQUIRED | PARTIAL_RECOVERY_REQUIRED
  -> POST_BUILD_REVIEW_REQUIRED <-> ARTIFACT_REPAIR_REQUIRED
  -> INDEPENDENT_REVIEW_REQUIRED
  -> INTEGRATION_REQUIRED
  -> PBR_PASS_QG_PENDING | CERTIFIED_FINAL
  -> PRODUCTION_QG_REQUIRED <-> REPAIR_REQUIRED
  -> CERTIFIED_FINAL
```

`AUDIT_TOOLING_REQUIRED`, `REVIEWER_INSTABILITY`, and `BLOCKED_AUTHORITY` are
fail-closed side states with explicit owner and evidence. A repair finding routes
to preparation, plan workflow, built artifacts, or audit/tooling before mutation.
Ambiguous routing goes to audit/tooling.

`INDEPENDENT_REVIEW_REQUIRED` and `INTEGRATION_REQUIRED` are conditional on a
pending learner-artifact or lifecycle-code mutation. A current built module that
passes without a diff records the evidence in place; the coordinator must not
manufacture an empty review or PR.

A built module enters post-build review directly only when every dependency
declared by its profile is present and current. An unbuilt module enters its
earliest preparation or plan state. A partial or ambiguous bundle enters recovery
without speculative deletion or rebuild.

Repair iteration has no arbitrary numeric cap. Changed evidence warrants another
fresh review. Materially inconsistent findings from unchanged source, prompt,
policy, tool, and reviewer identities are reviewer/tooling instability and stop
content mutation.

### Evidence identities and invalidation

Each transition records the exact identities it consumed. The minimum dependency
sets are:

| Evidence class | Identity basis |
| --- | --- |
| Inventory | Manifest bytes, profile version, track/slug |
| Preparation | Declared dossier, discovery, wiki/source, readings/rights, registry, and preparation-policy hashes |
| Plan | Plan bytes/version/changelog plus plan prompt/policy/schema/tool and reviewer identities |
| Build | Preparation and plan identities; build configuration; writer route/lineage; exact build prompt/tool versions; learner-artifact hashes |
| Post-build | Complete learner bundle, rendered learner output, every deterministic dependency read, prompt/policy/schema/tool versions, reviewer route/identity, exact raw response |
| Production QG | Learner-content hash, gate/prompt/checker/policy versions, reviewer family/model/route, canary and arming identities |
| Independent review | Exact diff and all machine author-family identities |
| Integration | Issue, branch, worktree, commit, PR, CI/review gate, merge SHA, telemetry receipt, cleanup state |

A changed identity invalidates that result and every dependent result. In
particular, dossier/wiki/discovery changes cannot leave a prior post-build result
looking current when the review commands read those inputs. Learner-artifact
changes invalidate both post-build and production-QG evidence.

The runtime event ledger is gitignored and atomically persisted. Versioned schemas,
profiles, and compact evidence contracts are tracked. Generated prompts, raw
responses, review/status files, and telemetry databases are not committed to
learner-artifact PRs. Durable remote continuity uses the linked issue/PR evidence
and the repository thread-rollover protocol.

### Prompts as code

Executable prompts remain human-readable Markdown under
`agents_extensions/shared`. Each has a small versioned manifest declaring:

- stable prompt ID and semantic version;
- typed input and output schemas;
- ordered registered includes and applicable policy IDs;
- compatible family, phase, provider capabilities, and route constraints;
- deprecation/replacement metadata.

The resolver accepts only declared values, expands an acyclic include graph in a
fixed order, preserves exact bytes, and hashes the rendered prompt together with
its manifest/schema/policy identities. Missing fragments, cycles, duplicate or
conflicting sections, unresolved placeholders, and undeclared inputs fail closed.
Golden fixtures cover CORE and seminar variants and historical prompt versions.

Track profiles may select registered IDs and bounded enum/boolean options. They
may not inject prose. This resolves the architecture panel's dissent: it provides
typed boundaries, reproducibility, and tests without creating a second prompt
programming language. `docs/prompts` may hold generated or historical reference
material but is not executable source-of-truth.

### Certification is separate from integration

`$post-build-review` PASS is the current Stage-A gate. A repaired module may be
independently reviewed, merged, and recorded as `PBR-PASS / LLM-QG-PENDING` when
its track profile requires a later production gate. Publication or merge does not
by itself imply final certification.

Production LLM-QG is an optional adapter and remains disarmed. Enabling it requires
a repository-backed qualification artifact, complete dry-run, route/model/prompt/
gate canary, budget rails, circuit breaker, resumable evidence, and explicit human
arming. Its useful cache, lineage, grounding, canary, and cost controls may be
reused. Legacy `llm_qg.json`, numeric score thresholds, file mtimes, SQLite rows,
parser salvage, median sampling, and in-gate mutation remain non-authoritative.

Final certification is a derived state: all gates required by the current track
profile are current and passing, and all material independent-review findings are
resolved.

### Track profiles

Profiles inherit from strict CORE or seminar family bases and declare only data:

- preparation evidence and validators;
- plan/build/certification adapter IDs;
- prompt, policy, and rubric IDs;
- learner bundle/layout requirements;
- author/reviewer family exclusions;
- wave and cost/health constraints;
- track-specific integration side effects.

FOLK, BIO, HIST, ISTORIO, LIT families, OES, RUTH, C1, and C2 may differ without
duplicating the common state machine. Unknown, retired, absent, or contradictory
profiles fail closed.

### Pilot qualification

Broad rollout requires shadow/dry-run qualification followed by bounded live
pilots. Learner-artifact repairs discovered by an infrastructure pilot are filed
under the owning curriculum stream epic.

| Pilot | Required path |
| --- | --- |
| Built FOLK M01 | Current dependency check, direct PBR, no speculative rewrite |
| Built FOLK repair + no-change cases | Repair loop and initial-PASS preservation |
| Built BIO | Biography preparation/policy and direct-certification path |
| Built A1 | Intended English-scaffolding false-positive protection |
| Built A2 | Graduated immersion, no A1 regression, and no premature B1 prose |
| Built B1 and B2 | Higher-immersion and core progression policy |
| Unbuilt BIO | Full PREPARE -> PLAN -> BUILD -> CERTIFY path |
| Unbuilt C1 and C2 | CORE unbuilt paths with distinct level policy |
| Unbuilt non-FOLK seminar | Generic seminar preparation/build/certification |
| Partial/ambiguous fixture | Non-destructive recovery |
| Drift/instability/crash/quota fixtures | Invalidation, stop, resume, and safe pause |

A three-module FOLK wave begins with M01-M03. A module that passes its initial
current review receives no speculative style churn.

## Alternatives considered

- **Expand `$track-completion` into a monolith**: rejected because queue/quota,
  phase execution, prompt composition, and track policy would become inseparable.
- **One giant orchestration skill or prompt per track**: rejected because it
  preserves the current duplication and drift under different filenames.
- **Adopt Temporal, Argo, or another external workflow engine now**: rejected
  because repository-scale leases and append-only evidence are sufficient, while
  external operations would add deployment complexity before semantics stabilize.
- **Create a general typed prompt DSL/compiler**: rejected because prompt prose
  remains the reviewable source; a manifest plus deterministic resolver supplies
  the necessary types and identity without a second language.
- **Keep publication as the terminal certificate**: rejected because Stage-A
  integration may legitimately precede an explicitly pending production gate.
- **Stop repair after a fixed attempt count**: rejected because iteration count is
  not evidence of instability or a genuine blocker.

## Consequences

**Positive**:

- Operators invoke one short, resumable workflow instead of pasting policy.
- Built, unbuilt, partial, and preparation-stale modules share one evidence model.
- Track differences remain explicit and schema-validated without branching the
  common engine.
- Prompt and certification changes become diffable, hash-bound, and testable.
- Provisional integration cannot be mistaken for final certification.

**Negative / risks**:

- The migration needs responsibility-by-responsibility parity; premature prompt
  deletion could silently lose policy.
- Complete dependency hashing will expose stale evidence previously treated as
  current and may increase legitimate re-review work.
- Profile schemas can become accidental complexity and require strict limits on
  free text, inheritance, and conditionals.
- Cross-track pilots may find learner defects; infrastructure issues must not
  absorb curriculum-stream repair scope.

**Neutral / follow-ups**:

- #5155 implements prompt contracts; #5154 preparation; #5158 coordination;
  #5156 certification; #5157 pilots; #5159 migration and rollout.
- Exact production-QG qualification and arming remain a later human decision.
- Cross-track parallel mutation remains disabled until separately authorized.

## Verification

- The companion responsibility-parity document classifies all 39 legacy
  orchestration prompt files before implementation.
- ADR validation and index: `.venv/bin/python scripts/audit/check_adrs.py`.
- Schema, include-graph, exact-byte, golden, tamper, and historical-version tests
  gate prompt contracts.
- State-transition, invalidation, lease, idempotency, crash/resume, quota-pause,
  CORE/seminar, built/unbuilt/partial, and instability fixtures gate the engine.
- Pilot evidence in #5157 covers every row in the qualification matrix.
- Every implementation PR requires independent cross-family review, CI, scoped
  auto-merge, issue evidence, and worktree/branch cleanup.

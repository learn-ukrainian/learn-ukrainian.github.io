# Orchestrator Prompt Suite

Prompt suite version: 0.3
Last reviewed: 2026-06-21

This directory contains reusable prompts for future core-track and seminar-track orchestration threads. They are templates, not source-of-truth curriculum policy. Every production thread that uses them must inspect the current local repository before acting, especially `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `curriculum/l2-uk-en/curriculum.yaml`, `scripts/config.py`, `scripts/audit/config.py`, and the target level files.

## Lifecycle

1. Preflight where needed: B2 and seminar tracks use readiness audits before production because their plans, discovery files, wiki/source coverage, and reading coverage must be checked before module writing starts.
2. Build: create or update only the scoped modules, in small sequential batches, with module-tailored instructions.
3. Quality audit: review that does not modify curriculum or site sources, records every issue, writes a durable report under `docs/audits/`, and proposes remediation batches. The report is durable only when committed and reviewed in its own PR.
4. Remediation: consume the audit report and fix every finding in PR-sized batches without changing unrelated modules.
5. Final review and merge: run deterministic validation, include token telemetry for module-build PRs, get independent review before merge, and keep generated runtime artifacts out of the PR.

## Core Prompt Index

- `a1/quality-audit-orchestrator.md`: beginner-specific read-only audit for emotional safety, scaffolding, decodability, Cyrillic/pronunciation support, activities, vocabulary, and source/wiki coverage.
- `a1/remediation-build-orchestrator.md`: small-batch remediation from an A1 audit report while preserving beginner tone, decodability, and scaffolded progression.
- `a2/quality-audit-orchestrator.md`: transition-track audit for immersion ramp, grammar complexity, B1 readiness, activity variety, vocabulary, and source/wiki coverage.
- `a2/remediation-build-orchestrator.md`: small-batch remediation from an A2 audit report without flattening A2 into B1-style immersion too early.
- `b1/quality-audit-orchestrator.md`: read-only normalization audit for B1 M1-M82 using the current M83-M94 quality bar after verifying those modules in the checkout.
- `b1/remediation-build-orchestrator.md`: B1 normalization remediation that separates targeted patches from rebuilds and avoids finale contamination.
- `b1/finale-build-orchestrator.md`: build or remediation prompt for final B1 synthesis/checkpoint/exam modules such as M93-M94, kept separate from M1-M82 normalization.
- `b2/preflight-readiness-audit-orchestrator.md`: read-only readiness audit before B2 production.
- `b2/production-build-orchestrator.md`: small sequential B2 production batches after preflight passes.
- `b2/quality-audit-orchestrator.md`: post-build B2 audit for advanced syntax, register control, argumentation, and professional/academic readiness.

## Seminar Pilot Index

FOLK is the pilot seminar track. Its prompts should be treated as the model for later HIST, BIO, LIT, active `lit-*`, ISTORIO, OES, and RUTH suites, adjusted to each track's source base.

- `folk/preflight-readiness-audit-orchestrator.md`: read-only readiness audit for FOLK plans, dossiers, wiki/source coverage, reading candidates, copyright status, and quote/source gates.
- `folk/production-build-orchestrator.md`: FOLK module production with mandatory primary readings, `:::primary-reading` blocks, reading-reference wiring, folk text-layer components, and `verify_shippable`.
- `folk/quality-audit-orchestrator.md`: post-build audit for FOLK modules against the exemplar standard, source fidelity, readings, decolonization, and rendered-site behavior.
- `folk/remediation-build-orchestrator.md`: remediation prompt for FOLK findings, including reading-link/copyright fixes and source-grounded content repair.

## Shared Files

- `shared/repo-rules.md`: non-negotiable repo rules to paste into future orchestration prompts.
- `shared/validation-checklist.md`: validation commands and scope checks future agents should adapt to the target batch.
- `shared/telemetry-and-pr.md`: commit, PR, independent review, and module-build telemetry requirements.
- `shared/review-output-schema.md`: durable audit report schema and issue inventory format.
- `shared/seminar-source-rules.md`: seminar-track source, decolonization, quote, and active-track taxonomy rules.
- `shared/reading-section-rules.md`: primary-reading and global reading-reference rules, including copyright decisions.

Each level prompt references these shared files, but also restates the critical rules so it remains usable when pasted alone into Codex, Gemini, or Claude.

## Helper And Swarm Policy

Helpers are optional. Use one to three read-only explorers only when they materially save time, such as surveying module shapes, checking doc references, or validating prompt consistency. Use worker helpers only for mechanical edits with a clearly owned file set. The main orchestrator remains responsible for design, integration, final review, PR creation, and merge decisions.

Every module-build PR must state `swarm_used`, `swarm_label`, and `swarm_note` in token telemetry. Solo runs still need `swarm_used: false`, `swarm_label: none`, and a note such as `solo run; no swarm used`.

## Headroom Policy

Use Headroom compression for helper summaries, logs, searches, or handoffs over roughly 200 lines or 20 KB. Pass the compressed hash plus a short summary, and retrieve the full content only when exact details are needed. Do not treat Headroom memory as the source of truth for curriculum facts, and do not run `headroom learn --apply`.

## Track Creation Order

Use this order unless the user changes priorities:

1. `folk` as the seminar pilot.
2. `b2`.
3. `hist` and `bio`.
4. `c1`.
5. `lit`.
6. Active `lit-*` subtracks from the current manifest.
7. `istorio`.
8. `oes` and `ruth`.
9. `c2`.

Do not infer active tracks from stale plan-only directories. Verify active track names from the current `curriculum/l2-uk-en/` source directories, site content config, landing pages, and `curriculum.yaml`. For example, if `lit-crimea` or `lit-doc` exist only as old plan directories but not as active curriculum/site tracks, do not create prompt suites for them.

## Adding C1, C2, Or Seminar Orchestrators

Add a sibling directory such as `c1/`, `c2/`, `hist/`, `bio/`, `lit/`, `oes/`, or `ruth/`. Reuse only the track-agnostic shared scaffolding: repo hygiene, worktree discipline, PR rules, and report structure. Seminar tracks must not inherit CEFR immersion, decodability, beginner-safety, or grammar-sequencing assumptions by default. Before writing seminar prompts, inspect existing seminar precedents such as `docs/audits/bio-decolonization-checklist.md` and `docs/audits/bio-track-gap-audit-2026-05-26.md` when present, then add track-specific source attribution, factuality, decolonization, Russian-shadow, and bias checks.

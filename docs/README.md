# Learn Ukrainian — Documentation Map

> **Purpose:** Canonical entry point for AI agents orienting cold. Lists the authoritative docs by topic, in priority order. **Read THIS first, not the 36 top-level files alphabetically.**

## Find a document, data store or resource: one entry point

```bash
.venv/bin/python -m scripts.docs.find "<query>"          # add --json, --limit N or --family ID
curl -s 'http://localhost:8765/api/knowledge/find?q=<query>'   # the same search on the Monitor API
```

One query searches the catalogue (`docs/knowledge/catalogue.yaml`: every family under `docs/`, `registry/` and `curriculum/l2-uk-en/evidence/`, plus every local store under `data/`), tracked file names, and the text of every content-searchable family in Git's index. Each hit names its family, its status (current, historical, draft or superseded, with the replacement) and how to query the family further. The library is `scripts/docs/find.py`; the family table at the end of this page is generated from the catalogue.

## Cold-start sequence (fastest orient)

1. **Monitor API** (zero-token state). Try first:
   - `curl -s http://localhost:8765/api/state/manifest`
   - `curl -s http://localhost:8765/api/orient`
   - `curl -s 'http://localhost:8765/api/rules?format=markdown'` (if rules hash changed)
   - `curl -s 'http://localhost:8765/api/session/current?format=markdown'` (if session hash changed)
2. **Behavioral rules:** `memory/MEMORY.md` (cross-session, hard-won lessons)
3. **Agent-specific instructions:** `CLAUDE.md` (Claude), `AGENTS.md` (other AI), `GEMINI.md` (Gemini)
4. **Active task:** latest `docs/session-state/*.md` (chronological handoffs; newest first via `ls -t`)

If Monitor API is down, fall back to: `memory/MEMORY.md` → `CLAUDE.md` → latest `docs/session-state/*.md`.

---

## Spec inheritance — V5/V6 baseline cascades to V7

**Important:** V5/V6 documentation is **historical reference, not deleted policy**. The pipeline is layered:

- V5/V6 baseline specs (pedagogy, lesson contract, quality standards, agent cooperation, audit gates) remain authoritative for anything V7 has not explicitly overridden.
- V7 is a delta layer: it changes the build orchestration (worktrees, linear pipeline, MCP retrieval, new writer architecture) but inherits V5/V6 for pedagogy, content quality, dictionary discipline, etc.
- If V7-era docs don't address a topic, fall back to V5/V6 era docs. They still apply.

When in doubt: V7 doc overrides → V6 doc fills in → V5 doc fills in.

---

## Authoritative docs by topic

### Mission, learner, lesson contract

- `docs/north-star.md` — what we're building and why (DRAFT v3, signed off 2026-05-04 by Codex+Gemini). Authoritative.
- `docs/lesson-contract.md` — what shape every lesson takes (DRAFT v3, same sign-off). Authoritative.

### Pipeline architecture

- `agents_extensions/shared/rules/pipeline.md` (deployed to `.claude/rules/pipeline.md`, `.codex/rules/pipeline.md`, etc.) — **current V7 policy.** Reviewer/writer assignment, decision-card links.
- `docs/architecture/ARCHITECTURE.md` — **V5/V6 era, superseded** by `docs/architecture/v7-pipeline.md` (catalogue override and in-file banner); read it only for historical context.
- `docs/architecture/RFC-410-MANIFEST-DRIVEN-ARCHITECTURE.md` — manifest-driven curriculum structure (Approved 2026-01-17).
- `docs/architecture/adr/*.md` — sequential architectural decision records.
- `docs/decisions/*.md` — dated decision journal (signal-rich, chronological).

### Best practices (per-topic)

`docs/best-practices/` has 33 files. Most-load-bearing:

- `agent-activity-matrix.md` — canonical task-type × agent routing matrix (v1.1, 2026-05-17)
- `module-content-quality.md` — content standards
- `audit-standards.md` — gate definitions
- `vocabulary-activity-standards.md` — vocab + activity formats
- `activity-pedagogy.md` — level → activity type matrix
- `agent-cooperation.md` — inter-agent protocol
- `harness-engineering.md` — orchestration patterns
- `deterministic-over-hallucination.md` — anti-fabrication rule (MEMORY #M-4)
- `prompt-engineering.md`, `context-engineering.md` — agent-prompt design
- `code-quality.md`, `git-hygiene.md`, `gitflow.md` — engineering practices
- `decision-journal.md`, `adr-management.md` — governance

### Behavioral / rules

- `agents_extensions/shared/rules/*.md` — shared source (canonical). `.claude/`, `.agent/`, `.codex/`, `.gemini/` are deploy targets.
- `agents_extensions/codex/` — Codex-owned overlays such as durable memory.
- `docs/archive/2026-07-goal-driven-runs.md` — `/goal` convention (#1884; ARCHIVED 2026-07-07, dormant)
- `agents_extensions/shared/rules/mcp-sources-and-dictionaries.md` — MCP tool inventory
- `agents_extensions/shared/rules/critical-rules.md` (loaded via Monitor API, see `_load-via-api.md`)

### Tracks

- `docs/best-practices/track-architecture.md` — track structure
- `docs/l2-uk-en/` — Ukrainian for English-speakers (main track)
- `docs/l2-uk-direct/` — Ukrainian L1-agnostic (separate schemas)

### State of the project

- `docs/WORKSTREAMS.md` — living workstreams and priorities (replaces `docs/MASTER-PLAN.md`, a March 2026 snapshot)
- `docs/session-state/` — compatibility handoff routers only, not live state (see its README); handoffs go through Fleet Comms and the thread-handoff flow
- `audit/` (top-level, NOT `docs/audits/`) — build-produced reports + recurring audits

### Operational

- `docs/SCRIPTS.md` — commands and scripts
- `docs/MONITOR-API.md` — Monitor API endpoints
- `docs/agent-runtime-guide.md` — agent CLI invocation adapter layer

---

## Navigation hazards (known issues, 2026-05-18)

1. **36 top-level docs/ files, no semantic grouping.** Authoritative `north-star.md` sits among April archives. Use this README as primary index.
2. **18 HTML/MD duplicate pairs.** Prefer `.md` for AI-consumption; `.html` is a human-rendering companion only.
3. **Rule deploy drift risk.** `agents_extensions/` is source; deployed copies may lag if `npm run agents:deploy` hasn't been run. Verify with `scripts/check_rules_deployment.sh`.
4. **V5/V6 era docs not in `_legacy/`.** `docs/architecture/ARCHITECTURE.md` is legacy but at canonical path; its front matter and banner mark it superseded. `scripts.docs.find` reports each hit's status.
5. **`docs/architecture/adr/` vs `docs/decisions/`.** ADRs are architectural decisions; decisions are operational/policy. Both authoritative within scope.

A full spec-gap audit + reorganization plan exists at `audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md`.

---

## Catalogue: document families and data stores

<!-- BEGIN GENERATED: catalogue families. Edit docs/knowledge/catalogue.yaml, then run python -m scripts.docs.catalogue readme -->

120 document families and 29 local data stores, generated from `docs/knowledge/catalogue.yaml`. Status words: current = `active`, historical = `archive`.

### Document families

| Family | Kind | Status | Paths | Purpose |
| --- | --- | --- | --- | --- |
| `ulif-first-stress-contract` | doc_family | current | `docs/verification/ulif-first-stress.md` | ULIF-first stress oracle contract, source identity joins, labelled trie fallback and consumer verification. |
| `docs-entry-map` | doc_family | current | `docs/README.md` | Cold-start documentation map for humans and agents. It names the one search entry point (python -m scripts.docs.find, mirrored at GET /api/knowledge/find) and ends with the family and store tables generated from this catalogue; its topic prose still dates from the V7 era. |
| `docs-knowledge-system` | doc_family | current | `docs/knowledge/**`, `docs/architecture/docs-authority-lifecycle.md`, `docs/plans/2026-09-17-docs-knowledge-rollout.md` | Repository knowledge system - this catalogue and its schema, the deterministic docs inventory contract, the authority and lifecycle contract, and the docs-knowledge rollout plan. |
| `corpus-inventory` | doc_family | current | `docs/corpus-inventory.md` | Prose inventory of data/sources.db tables and the local versus bulk-root storage layout; table counts were last refreshed 2026-07-31 and are stale against the live store. |
| `top-level-references` | doc_family | current | `docs/ACTIVITY-YAML-REFERENCE.md`, `docs/CLAUDE-CODE-FEATURES.md`, `docs/DICTIONARY-PIPELINE-STATUS.md`, `docs/RUNBOOK-BUILD.md`, `docs/SCRIPTS.md`, `docs/WORKSTREAMS.md`, `docs/agent-bridge-setup-guide.md`, `docs/agent-runtime-guide.md`, `docs/review-protocol.md` | Maintained top-level references for scripts and commands, workstreams, the agent runtime, the review protocol, activity YAML and the dictionary pipeline status. |
| `monitor-api-docs` | doc_family | current | `docs/MONITOR-API.md`, `docs/monitor-api/**` | Monitor (Ops) API reference, the read-only work-projection API spec and the agent cold-start measurement log. |
| `core-lesson-contracts` | doc_family | current | `docs/north-star.md`, `docs/lesson-contract.md`, `docs/lesson-schema-design.md`, `docs/style-guide.md`, `docs/lesson-schema.yaml` | Curriculum north star, lesson contract v4, lesson schema design and the generated lesson schema, plus the human-editor style guide. |
| `top-level-point-in-time-audits` | evidence | historical | `docs/api-endpoint-consumer-map-2026-05-06.md`, `docs/api-stability-audit-2026-05-06.md`, `docs/monitor-api-ui-audit-2026-06-07.md`, `docs/corpus-gap-audit.md`, `docs/personal-name-audit.md`, `docs/phase-2-config-audit-report.md`, `docs/phase-4-exemplar-report.md`, `docs/rag-gap-1026.md`, `docs/atlas-data-coverage-strategy.md` | One-time audit evidence at the docs root - Monitor API consumer and stability audits, corpus and RAG gap audits, config and exemplar reports, personal-name and Atlas coverage audits. |
| `top-level-historical-notes` | doc_family | historical | `docs/MASTER-PLAN.md`, `docs/cleanup-plan-2026-q2.md`, `docs/orchestrator-frictions.md`, `docs/prompt-budgets.md`, `docs/rules-core-draft-notes.md`, `docs/salvage-manifest.md`, `docs/session-state-2026-04-04.md`, `docs/state-reconciliation.md`, `docs/v5-v3-to-v6-phase-mapping.md`, `docs/wiki-rebuild-plan.md` | Old plans, V6-era budgets and reconciliation notes, the reboot salvage manifest, a dated session snapshot and draft rule notes kept for history. |
| `architecture-adr` | doc_family | current | `docs/architecture/adr/**` | Numbered architecture decision records with template and generated index; permanent, superseded only by a later ADR. |
| `architecture-research` | evidence | historical | `docs/architecture/research/**` | April 2026 embedder survey and chunk-policy bake-off results. |
| `architecture-specs` | doc_family | current | `docs/architecture/*` | Architecture specs, plans, RFCs and audits - V7 pipeline, system topology, data-foundry architecture, ADR-style notes outside adr/, UI template specs and Astro evaluations. |
| `decisions-journal` | registry | current | `docs/decisions/*` | Dated, expiring decision records plus INDEX.md and decisions.yaml as the structured ledger; not an ADR substitute. |
| `decisions-pending-and-drafts` | doc_family | current | `docs/decisions/pending/**`, `docs/decisions/drafts/**` | The AFK decision-card queue (README only, no open cards) and draft design notes awaiting a decision. |
| `design-docs` | doc_family | current | `docs/design/*` | Subsystem design docs - agent runtime, Monitor API app factory and router inventory, epics graph, control-plane storage seam, cloud-agent pytest advisory, dimensional review. |
| `proposals` | doc_family | historical | `docs/proposals/*` | Early proposals and RFCs - literature expansion syllabi, Gemini review prompts, RFC-001 nine-phase workflow, RFC 4801 module size policy, dialogue-situation fixes. |
| `strategy` | doc_family | current | `docs/strategy/*` | Strategic direction for the Ukrainian open-model data infrastructure. |
| `gemma-finetuning-guides` | doc_family | historical | `docs/guides/**` | July 2026 Gemma fine-tuning, Hugging Face plan and trial budget guides tied to the retired fine-tuning plan. |
| `best-practices` | doc_family | current | `docs/best-practices/**` | Engineering and content standards that CLAUDE.md and the rules point to - code, git, review, prompts, activities, audit, fleet doctrine, module quality, V7 and ULP presentation. |
| `runbooks` | doc_family | current | `docs/runbooks/*` | Operating procedures for driver seats, harnesses, review isolation, sessions, handoffs, CI, storage, backup, worktree cleanup, module gates and builds. |
| `runbooks-atlas` | doc_family | current | `docs/runbooks/atlas-*.md`, `docs/runbooks/word-atlas-*.md`, `docs/runbooks/teacher-curated-*.md`, `docs/runbooks/stem-textbook-*.md` | Word Atlas runbooks - entry model, source census and scope, static API, 20k runner durability, re-enrich campaign, teacher seed rebuild and textbook ingest. |
| `runbooks-data-foundry` | doc_family | current | `docs/runbooks/ukrainian-data-foundry-*.md` | Ukrainian Data Foundry build, admission, treatment, correction and model-view recipes. |
| `templates` | doc_family | current | `docs/templates/**` | Task handoff templates (issue, infrastructure, batch review, module correction, plan review, bug investigation) and the bio research dossier template. |
| `bug-autopsies` | doc_family | current | `docs/bug-autopsies/**` | Root-cause write-ups of past incidents with a one-line-per-bug INDEX.md (date, issue, category, summary). |
| `small-harness-docs` | doc_family | current | `docs/guardrails/**`, `docs/ops/**`, `docs/entire/**`, `docs/examples/**`, `docs/specs/**`, `docs/third-party/**`, `docs/playbooks/**` | Fleet tooling guardrail, fleet session-awareness charter, Entire recall receipts, launchd example, task-family manager spec and vendored third-party licence text. |
| `legacy-agent-docs` | doc_family | historical | `docs/agents/**`, `docs/ai_team/**`, `docs/dispatch-queue/**`, `docs/evidence/**`, `docs/workflows/**` | Legacy agent-team docs - the May 2026 capability snapshot, Blue/Yellow team personas, a fired May dispatch queue, a Gemini CLI dry-run receipt and the old /review-content command. |
| `ocr-setup-note` | doc_family | historical | `docs/ocr/**` | OCR provider note and credential-loading pattern (May 2026). |
| `agent-channels` | registry | current | `docs/agent-channels/**` | Per-channel context files the legacy agent bridge still auto-includes in posts; Fleet Comms now owns durable messages. |
| `session-state-routers` | doc_family | current | `docs/session-state/**` | Compatibility handoff routers per agent served by the session API; body-light pointers only, no new handoffs here. |
| `handoffs-march-2026` | doc_family | historical | `docs/handoffs/**` | End-of-session handoff notes from March 2026; handoffs now go through Fleet Comms and the thread-handoff flow. |
| `token-usage-reports` | generated | historical | `docs/token-usage/**` | A generated April 2026 Claude token report and a hand-written token waste report; not current usage. |
| `dispatch-briefs` | doc_family | historical | `docs/dispatch-briefs/**` | One-shot worker dispatch briefs (April to September 2026) and two batch folders; each describes finished task scope. |
| `dispatch-briefs-reusable` | doc_family | current | `docs/dispatch-briefs/luna-max-closeout-contract.md`, `docs/dispatch-briefs/qg-bakeoff-*-1x17-sweep.md` | Reusable brief fragments - the GPT-6 Luna closeout contract and three QG bake-off 1x17 sweep instructions. |
| `dispatch-briefs-upgrade-pilot` | doc_family | superseded → `docs/epics/fresh-build-build-program.md` | `docs/dispatch-briefs/2026-09-12-cu-p0-pilot-*.md` | Writer, repair and review briefs for the abandoned --upgrade phase-0 pilot. |
| `plans` | doc_family | current | `docs/plans/*` | Named plans of record and roadmaps; GitHub issue state wins over stale plan text. |
| `plans-plan-mode-files` | doc_family | historical | `docs/plans/abstract-pondering-hopper.md`, `docs/plans/agile-baking-harp.md`, `docs/plans/composed-sleeping-spring.md`, `docs/plans/cryptic-tickling-meteor.md`, `docs/plans/encapsulated-honking-abelson.md`, `docs/plans/euphony-engine.md`, `docs/plans/floating-herding-sonnet.md`, `docs/plans/fluttering-painting-crayon.md`, `docs/plans/giggly-exploring-crescent.md`, `docs/plans/glowing-petting-aho.md`, `docs/plans/greedy-bouncing-gizmo.md`, `docs/plans/jiggly-soaring-forest.md`, `docs/plans/lovely-soaring-iverson.md`, `docs/plans/mellow-munching-biscuit.md`, `docs/plans/moonlit-finding-popcorn.md`, `docs/plans/partitioned-plotting-bachman.md`, `docs/plans/partitioned-stirring-ullman.md`, `docs/plans/peaceful-coalescing-glacier.md`, `docs/plans/peaceful-coalescing-glacier-agent-a6cf894859709c20c.md`, `docs/plans/robust-dancing-candle.md`, `docs/plans/soft-wiggling-rabin.md`, `docs/plans/sprightly-brewing-nest.md`, `docs/plans/tranquil-cooking-muffin.md`, `docs/plans/witty-hopping-puddle.md`, `docs/plans/wondrous-toasting-pumpkin.md`, `docs/plans/zippy-watching-moore.md` | Auto-named Claude plan-mode files and the Euphony plan from the V4 to V6 era (February to April 2026). |
| `plans-state-standard-gap-analyses` | evidence | historical | `docs/plans/a2-state-standard-gap-analysis.md`, `docs/plans/b1-state-standard-gap-analysis.md`, `docs/plans/c1-state-standard-gap-analysis.md`, `docs/plans/cross-level-reconciliation.md` | March/April 2026 analyses of the old curriculum plans against the State Standard 2024. |
| `plans-atlas-practice` | doc_family | current | `docs/plans/atlas-*.md`, `docs/plans/2026-07-25-atlas-*.md`, `docs/plans/2026-07-27-atlas-practice-gradual-ramp.md`, `docs/plans/2026-09-21-practice-scouting-synthesis.md` | Atlas and Practice hub plans - open lexical layer, lexical inventory matrix, entry model, gradual ramp and practice scouting. |
| `ci-program` | doc_family | current | `docs/plans/2026-09-02-ci-sweet-spot.md`, `docs/epics/ci-speed-program.md` | CI plan of record and the CI speed program (epic |
| `hramatka-docs` | doc_family | draft | `docs/projects/hramatka/**`, `docs/plans/HRAMATKA_APP_PRODUCT_ROADMAP.md` | Hramatka teacher lesson service - lesson document contract draft and the product roadmap. |
| `epics-fresh-build` | doc_family | current | `docs/epics/fresh-build-*.md` | Core fresh lesson-based build program for A1 to B2 - requirements, build program, plan schema, writer and review contracts and the level arc plans. |
| `epics-upgrade-abandoned` | doc_family | superseded → `docs/epics/fresh-build-build-program.md` | `docs/epics/a1-upgrade-*.md`, `docs/epics/curriculum-upgrade-phase1-spec.md`, `docs/epics/upgrade-combined-qg-prompt*.md` | Landing contract, inventory, operating rules, phase-1 spec and combined QG prompt of the abandoned in-place --upgrade approach. |
| `epics-other` | doc_family | current | `docs/epics/*` | Other epic documents that are not part of the fresh-build or abandoned upgrade sets. |
| `research-bio-dossiers` | doc_family | current | `docs/research/bio/**` | One research dossier per BIO module slug (sources, tiers, cross-track plan paths) feeding bio planning and builds. |
| `research-folk-dossiers` | doc_family | current | `docs/research/folk/**` | One research dossier or reading catalog per FOLK genre or topic, with supporting chunk ids. |
| `research-dataset-notes` | doc_family | current | `docs/research/*` | Research notes, evidence records and decisions behind the Ukrainian dataset and open-model-data work, including the Literary Poltava candidate audit. |
| `research-atlas-session-reports` | evidence | historical | `docs/research/2026-06-12-*.md`, `docs/research/atlas/**`, `docs/research/lexicon/**` | Dated June 2026 Atlas and lexicon run reports and a calque candidate list. |
| `research-retrieval-bakeoff` | evidence | current | `docs/research/retrieval-bakeoff-9233/**` | Query sets, judging rubric and phase-1 results of the |
| `references-reading-notes` | doc_family | current | `docs/references/*` | Reading notes and research surveys - UNLP 2025-2026 findings and a March 2026 lexical resource survey. |
| `research-registry` | registry | current | `docs/references/research-registry.yaml`, `docs/references/research-registry-pilot.md`, `docs/references/research-digests/**` | ADR-011 Project Research Registry of actionable findings with hashed digests, plus its pilot decision; separate from this catalogue. |
| `references-dobra-forma` | resource_catalogue | current | `docs/references/dobra-forma/**` | Local Markdown copy of the CC-licensed Dobra Forma grammar textbook chapters (University of Kansas). |
| `references-textbook-urls` | registry | current | `docs/references/textbook-urls.yaml` | Maps textbook ids to source URLs for stamping textbook links. |
| `references-external` | resource_catalogue | historical | `docs/references/external/**` | A saved external HTML article. |
| `experiments-and-reboot-references` | evidence | historical | `docs/experiments/**`, `docs/reboot/**` | The April 2026 five-writer bake-off (plan, results, prompts) and hand-crafted reboot Phase 8 reference material. |
| `archive` | doc_family | historical | `docs/archive/**` | Frozen archive of retired V5/V6-era guides, analyses, plans, root scratch files and old eval docs. |
| `audits-core` | evidence | historical | `docs/audits/*` | Dated June/July 2026 score ledgers, readiness and quality audits of the old core modules (A1, A2, B1, B2). |
| `audits-bio` | evidence | historical | `docs/audits/bio-*` | BIO track audits - gap audit and its frozen tally, readiness matrix, Bilash gate reviews, expansion research and the decolonization checklist. |
| `audits-bio-lit-cross-reference` | generated | current | `docs/audits/bio-lit-cross-reference-*.md` | Regenerated list of bio modules lacking LIT counterparts, plus exclusions. |
| `audits-folk` | evidence | historical | `docs/audits/folk-*` | June 2026 FOLK preflight readiness and reading coverage audits. |
| `audits-tooling` | evidence | historical | `docs/audits/codeql-*`, `docs/audits/prompt-audit-fable-5-1-2026-09-01.md`, `docs/audits/slovnyk-me-ingestion-feasibility.md` | CodeQL triage and its cleanup diff, a September prompt-size audit and the slovnyk.me ingestion feasibility study. |
| `audits-open-model-data` | evidence | current | `docs/audits/2026-09-11-uldr-program-audit.md` | September 2026 ULDR program audit; earlier verdicts inside apply only to their named heads. |
| `reports-analyses` | evidence | historical | `docs/reports/*` | Dated analysis reports - vocabulary audits, A1 macro review, April diagnoses, dashboard endpoint audit and the July model qualification benchmark. |
| `reports-oneshot-scripts-and-drafts` | generated | historical | `docs/reports/*.py`, `docs/reports/gh_comment_*.md`, `docs/reports/gh_issue_chunking.md` | April 2026 one-off migration scripts and drafted GitHub comments; not wired into any tool. |
| `reports-a1-reviews` | evidence | historical | `docs/reports/a1_reviews/**` | January 2026 per-module AI review scorecards of the old A1 modules. |
| `issues-reports` | evidence | historical | `docs/issues/**` | January/February 2026 B1/B2/C1 rebuild audit reports, completion notes and OES/C1-BIO research artefacts; not GitHub issues. |
| `dev-notes` | doc_family | historical | `docs/dev/**` | January to March 2026 developer notes, migration contexts, vocabulary workflow notes and naturalness scans of the old modules. |
| `status-snapshots` | generated | historical | `docs/status/**` | February 2026 per-level STATUS.md snapshots; live status is the per-module status JSON and the Monitor API. |
| `prompts-legacy-orchestrators` | doc_family | superseded → `agents_extensions/shared/skills/curriculum-lifecycle/SKILL.md` | `docs/prompts/orchestrators/**` | Legacy per-track orchestrator prompt suite kept as hash-checked evaluation and historical reference; not lifecycle authority. |
| `prompts-templates` | doc_family | current | `docs/prompts/*` | Curriculum prompt templates - A2 certification and plan writing, B1 batch build template, tutor prompt reference. |
| `l2en-templates` | doc_family | current | `docs/l2-uk-en/templates/**` | Per-level and per-type module section templates and the detailed meta schema read by the audit template-compliance check. |
| `l2en-archive` | doc_family | historical | `docs/l2-uk-en/_archive/**` | Retired per-level curriculum plans (RFC |
| `l2en-live-config` | registry | current | `docs/l2-uk-en/level-status.yaml`, `docs/l2-uk-en/state-standard-2024-mapping.yaml`, `docs/l2-uk-en/template_mappings.yaml`, `docs/l2-uk-en/v4-seminar-section-templates.yaml` | Machine-read YAML - planned module counts per level, State Standard line mapping, level-to-template rules and seminar section templates. |
| `state-standard-2024` | resource_catalogue | current | `docs/l2-uk-en/UKRAINIAN-STATE-STANDARD-2024.txt`, `docs/l2-uk-en/UKRAINIAN-STANDARD-INDEX.md` | Full text of the Ukrainian State Standard 2024 and an index mapping curriculum modules to the line ranges that define their required competencies. |
| `l2en-generated-plan-snapshots` | generated | historical | `docs/l2-uk-en/*-PLAN-GENERATED.md` | Markdown snapshots generated from the January/February 2026 YAML plans; stale against the live plans. |
| `l2en-authoring-guidelines` | doc_family | historical | `docs/l2-uk-en/ACTIVITY-GUIDELINES.md`, `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`, `docs/l2-uk-en/RICHNESS-BY-MODULE-TYPE.md`, `docs/l2-uk-en/CHECKPOINT-DESIGN-GUIDE.md`, `docs/l2-uk-en/LINGUISTIC-PURITY-GUIDE.md`, `docs/l2-uk-en/MODULE-SKELETON.md`, `docs/l2-uk-en/LEVEL-REVIEW-WORKFLOW.md`, `docs/l2-uk-en/VOCABULARY-HANDLING-SYSTEM.md`, `docs/l2-uk-en/YAML-ACTIVITY-MIGRATION-PLAN.md`, `docs/l2-uk-en/UKRAINIAN-CEFR-RESEARCH.md`, `docs/l2-uk-en/SPECIALIZATION-TRACKS.md`, `docs/l2-uk-en/TRACKS-MASTER-SCORECARD.md` | V5/V6-era module authoring guidelines (richness, activities, checkpoints, purity, review workflow); valid only where current standards are silent. |
| `l2en-dobra-forma-and-media` | doc_family | historical | `docs/l2-uk-en/DOBRA-FORMA-*.md`, `docs/l2-uk-en/OPUS-PROMPT-DOBRA-FORMA-VERB-STUDY.md`, `docs/l2-uk-en/READING-MANIFEST.md`, `docs/l2-uk-en/MEDIA-SOURCES.md`, `docs/l2-uk-en/resources.md` | December 2025/January 2026 mapping of Dobra Forma, reading lists and media sources to modules. |
| `l2en-level-plans-and-proposals` | doc_family | historical | `docs/l2-uk-en/*-IMPROVEMENT-PLAN.md`, `docs/l2-uk-en/*-RESTRUCTURE-*.md`, `docs/l2-uk-en/*-MEDIA-ASSIGNMENT.md`, `docs/l2-uk-en/*-CURRICULUM-V?.md`, `docs/l2-uk-en/B1-GAP-ANALYSIS*.md`, `docs/l2-uk-en/B2-COUNTER-PROPOSAL.md`, `docs/l2-uk-en/B2-GEMINI-EXPANSION-PROPOSAL.md`, `docs/l2-uk-en/C1-REVIEW-PROPOSAL.md`, `docs/l2-uk-en/STEM-TRACK-PROPOSAL.md`, `docs/l2-uk-en/A1_COMPLETION_REPORT.md`, `docs/l2-uk-en/ANTIGRAVITY-BRIEF-A1-M28-34.md`, `docs/l2-uk-en/B1-CEFR-MAPPING.md`, `docs/l2-uk-en/MODULE-WRITING-SUBTICKETS.md`, `docs/l2-uk-en/REORGANIZATION-PLAN.md`, `docs/l2-uk-en/RFC-409-PLAN-VERIFICATION.md`, `docs/l2-uk-en/STATE-STANDARD-COMPLIANCE-ANALYSIS.md`, `docs/l2-uk-en/curriculum-redesign-v5.md` | January to May 2026 level improvement and restructure plans, media assignments, curriculum drafts, gap analyses and proposals for the old curriculum. |
| `l2-uk-direct-plans` | doc_family | historical | `docs/l2-uk-direct/*` | Planning documents for the L1-agnostic l2-uk-direct track (A1 to B2); the track has had no commits since 2026-03-06. |
| `textbook-catalog` | registry | current | `docs/l2-uk-direct/textbook-selection.yaml`, `docs/l2-uk-direct/textbook-map.yaml`, `docs/l2-uk-direct/pidruchnyk-catalog.yaml` | Registries of selected school textbooks, their curriculum mapping and the pidruchnyk catalog, used by the textbook download and Atlas source inventory. |
| `textbook-reading-notes` | evidence | historical | `docs/l2-uk-direct/textbook-reading-notes/**` | Notes on grade 3 to 6 textbooks and the State Standard; cited as provenance by the Atlas source inventory. |
| `style-cards` | registry | current | `docs/style-cards/**` | Writer style cards for the a1, a2 and b1plus bands with pinned SHA-256 digests, injected into core fresh-build writer prompts. |
| `build-rule-data` | registry | current | `docs/rules/**` | Build-tooling data, not binding rules - the VESUM false-positive whitelist, the pedagogy pattern library and the global friction log, read by the pipeline and VESUM checks. |
| `pedagogy` | doc_family | current | `docs/pedagogy/**` | A1/A2 lesson construction standard, retrofit audit protocol, template and report, and the commercial-source use policy. |
| `human-and-exam-eval` | doc_family | current | `docs/eval/**`, `docs/evaluations/**` | Native-speaker module evaluation rubric and template, and the ZNO/NMT exam evaluation harness guide. |
| `content-review-reports` | evidence | historical | `docs/reviews/**` | February/April 2026 dialogue-situations review and hallucinated-proverbs audit of pre-rebuild modules. |
| `folk-epic-specs` | doc_family | current | `docs/folk-epic/**`, `docs/reference/**` | FOLK seminar standards, review rubric, dossier and text-layer specs, quality-gate designs and queue, plus a folk micro-genre reference list. |
| `bio-epic-queues` | doc_family | current | `docs/bio-epic/**` | BIO phase-2 sequence allocation and the phase-4 wiki rewrite queue with its rubric (epic |
| `resources-external-links` | resource_catalogue | current | `docs/resources/external_resources*`, `docs/resources/EXTERNAL_RESOURCES_SCHEMA.md` | Per-module external resource links (articles, videos) read by the audit gate and wiki enrichment, with its schema and two stray copies. |
| `resources-curated-link-maps` | resource_catalogue | current | `docs/resources/trusted_sources.yaml`, `docs/resources/ulp-resources.yaml`, `docs/resources/ulp-alphabet.yaml`, `docs/resources/ulp-articles-index.yaml`, `docs/resources/ulp-article-mappings.yaml`, `docs/resources/miyklas-resources.yaml`, `docs/resources/miyklas-url-index.yaml`, `docs/resources/podcasts/ulp_mapping.yaml` | Curated trusted-source registry and ULP and Miyklas resource-to-module maps (including the recommended ULP podcast episodes per module) used by build enrichment and the resource-catalogue ingest; ULP is link-only (commercial). |
| `resources-scraped-catalogs` | resource_catalogue | current | `docs/resources/dobraforma/**`, `docs/resources/talkukrainian/**`, `docs/resources/verba/**`, `docs/resources/podcasts/*.json`, `docs/resources/podcasts/raw_lists/**`, `docs/resources/ukrainianlessons/*.json` | Scraped catalogs of learning resources - Ukrainian Lessons Podcast episode lists and database, ULP blog, Dobra Forma, TalkUkrainian and Verba - with module relevance scores. |
| `resources-mapping-reports` | evidence | historical | `docs/resources/podcasts/*.md`, `docs/resources/ukrainianlessons/*.md` | January 2026 methodology, review and completion reports for mapping ULP podcasts and blog posts to modules (epic |
| `atlas-word-cards` | doc_family | current | `docs/atlas/word-cards/**` | Word Atlas word-card schema, identity rules, migration, ULIF source-record notes and worked example cards. |
| `registry-atlas-word-cards` | registry | current | `registry/atlas/identity/registry.json`, `registry/atlas/pilot/pilot-v1.json`, `registry/atlas/pilot/pilot-v1.register-pin.json` | Word Atlas word-card foundation data - the identity registry (card entries with keys at creation, source records and lineage events), the frozen pilot manifest (selection, admission record, database fingerprints, counts and manifest hash), and its register pin sidecar. |
| `atlas-evidence` | evidence | current | `docs/atlas/*` | Atlas point-in-time reports - Tatoeba cloze yield, lesson-link removals and curated-membership reconciliation. |
| `practice-specs` | doc_family | current | `docs/practice/*` | Practice hub specifications and operator policy - imperative practice, K3 build, curated membership, teacher deck, layout UX and difficulty calibration. |
| `practice-residual-evidence` | evidence | current | `docs/practice/*-residual*.md`, `docs/practice/IMPERATIVE-HELD-OUT-AUDIT-200.md`, `docs/practice/synonym-withdrawal-8714.md` | Tool-backed practice residual taxonomies (cloze, paronym, relation, calque), the synonym withdrawal record and an imperative held-out audit. |
| `lexicon-sum11-audit` | evidence | current | `docs/lexicon/**` | Audit of SUM-11 references in lexicon scripts plus held and confirmed relation and source TSVs for the Soviet-era dictionary guard. |
| `poc-designs` | doc_family | current | `docs/poc/**` | HTML proof-of-concept page designs (lesson, folk, lit, site) and the Word Atlas per-page designs, route map and hub specs. |
| `sources-permissions-register` | registry | current | `docs/sources/**` | Source citation and provenance register (rights holder, terms, citation, removal route) for word cards, the Atlas and the open dataset; the YAML is authoritative. |
| `projects-open-model-data` | doc_family | current | `docs/projects/open-model-data/**` | ULDR decolonization and reasoning dataset specs, phase plans, runbooks and the paper outline (epics |
| `projects-foundry-evidence` | evidence | current | `docs/projects/ukrainian-data-foundry-evidence/**`, `docs/projects/ukrainian-data-foundry-adoption/**` | Text-free Data Foundry evidence reports on the human-authored source inventory (provenance, custody, extraction, phase 2-3 contracts) and the community adoption kit. |
| `projects-eval-packages` | doc_family | current | `docs/projects/ua-eval-harness/**`, `docs/projects/ua-open-weight-eval/**` | Public docs of the frozen UA Eval 0.1.1 correction benchmark and the UA open-weight evaluation 0.1.0 suite. |
| `projects-qg-quality-gate` | doc_family | current | `docs/projects/qg-quality-gate/**` | Calque and grammar quality-gate evidence schema, gate designs, annotation guides, fixture rights and scoring docs. |
| `projects-fleet-design-memos` | doc_family | current | `docs/projects/arc-layer/**`, `docs/projects/fleet-taxonomy/**`, `docs/projects/fleet-trails/**`, `docs/projects/launcher-consolidation/**`, `docs/projects/vesum/**` | Single-file advisor design memos - arc layer, fleet taxonomy alias audit, fleet trails, launcher consolidation and the VESUM re-ingest design. |
| `projects-folk-remediation` | doc_family | current | `docs/projects/folk-reading-coverage-remediation.md` | FOLK reading coverage remediation tracker. |
| `registry-reference-inputs` | registry | current | `registry/authors_rights.yaml`, `registry/canonical_anchors.yaml`, `registry/folk_heritage_attestations.yaml`, `registry/folk_micro_genres.yaml`, `registry/foreign_proper_noun_attestations.yaml`, `registry/historical_language_corpus_denominator.yaml`, `registry/pidruchnyk_urls.yaml`, `registry/primary_text_sources.yaml`, `registry/textbook_curriculum_denominator.yaml`, `registry/university_corpus_denominator.yaml`, `registry/lexicon-dataset.pointer.json`, `registry/lt_replacements.json`, `registry/russianism-patterns-ua-gec.csv` | Frozen reference inputs and denominators - authors' rights, canonical anchors, folk and proper-noun attestations, primary text sources, textbook, university and historical corpus denominators, Russianism patterns and replacement table. |
| `registry-artifacts` | registry | current | `registry/artifacts/**` | Group manifests that bind content-addressed payloads in the local artifact store, the frozen storage classification table and the tracked-data allowlist. |
| `registry-corpus-audit` | evidence | current | `registry/corpus_audit/**` | Corpus gap taxonomy, ingestion roadmap and NAVSI-200 catalog. |
| `registry-corpus-audit-draft-tickets` | doc_family | draft | `registry/corpus_audit/draft_tickets/**` | Draft ingestion tickets for grammar-source blocker cases, one per source and topic, awaiting human approval before filing. |
| `registry-corpus-channels` | registry | current | `registry/external_articles/**`, `registry/youtube_discovery/**` | External-article channel list and YouTube discovery search patterns for corpus acquisition. |
| `registry-lexicon-curation` | registry | current | `registry/lexicon/**` | Curated lexicon pairs (heritage, paronym, homonym, synonym, antonym), aliases, anchor worksheets, cohort lists, grow-triage ledgers and intake decisions. |
| `registry-lexicon-source-inventory` | registry | current | `registry/lexicon/source-inventory/**`, `registry/lexicon/source-inventory-review-decisions/**` | Tracked per-grade textbook source inventories and review decisions for textbook-derived lexicon admission. |
| `registry-practice` | registry | current | `registry/practice/**` | Part-of-speech mechanics decks, error-correction evidence and withheld lists, textbook error corrections and ZNO markup overlay. |
| `registry-sources` | registry | current | `registry/sources/**` | Publication-rights records for owned corpus sources (owned_cite_only / private_permission), read by scripts/curriculum/evidence/publication.py. |
| `registry-miyklas` | registry | current | `registry/miyklas/**` | Miyklas grammar topic index read by build enrichment. |
| `registry-open-model-data` | registry | current | `registry/projects/open_model_data/**` | Open-model-data contracts, decolonization components and reviews, admission, evidence, release and other program records. |
| `registry-open-model-data-archive` | registry | historical | `registry/projects/open_model_data/archive/**` | Quarantined historical and v1-production archive records of the open-model-data program. |
| `registry-translations` | registry | historical | `registry/translations/**` | Legacy vocabulary translation batches and outputs (issue |
| `registry-ua-gec-gold` | registry | current | `registry/ua-gec-gold/**` | UA-GEC gold set and contested-calque list used for surzhyk and calque scoring. |
| `curriculum-evidence-a1` | evidence | current | `curriculum/l2-uk-en/evidence/a1/**` | Core fresh-build A1 evidence - per-module word records, evidence packs, plan-review manifests, promotion records and verify reports, plus the shared base request and word registry. |

### Local data stores (untracked, under `data/`)

| Store | Names | Status | How to query |
| --- | --- | --- | --- |
| `data-sources-db` | `data/sources.db` | current | mcp: sources MCP search_sources / search_text / search_literary / search_definitions / query_sum20 / search_esum; api: GET /api/sources/search_text?q=<term>; GET /api/sources/stats; sqlite: read-only SQL on data/sources.db (table list via sources MCP collection_stats) |
| `data-vesum-db` | `data/vesum.db`, `data/vesum.db.bak`, `data/vesum.db.bak.*`, `data/vesum_shadow_v680.db` | current | mcp: sources MCP verify_word / verify_words / verify_lemma / inspect_word |
| `data-grac-frequency-db` | `data/grac_frequency.db`, `data/grac-10.db` | current | mcp: sources MCP query_grac with mode frequency or lemma_forms; cache_only=true for offline snapshot lookups |
| `data-atlas-db` | `data/atlas.db` | current | sqlite: Python API in scripts/atlas/atlas_db.py or read-only SQL on data/atlas.db |
| `data-atlas-synthetic` | `data/atlas-synthetic.db` | current | cli: .venv/bin/python scripts/benchmarks/generate_synthetic_atlas.py --help |
| `data-ulif-dumps` | `data/ulif_dump.db`, `data/ulif_scrape.log` | current | mcp: sources MCP query_ulif / query_ulif_records (reads the sources.db copy); sqlite: read-only SQL on data/sources.db (ulif_dictua_* tables) |
| `data-wiki-cache` | `data/wiki_cache.db`, `data/wiki_sources.db` | current | sqlite: read-only SQL on data/wiki_cache.db |
| `data-empty-comms-placeholders` | `data/comms_plane.db`, `data/fleet_comms.db` | historical | api: GET /api/comms/v1/plane-status (the real comms plane) |
| `data-lexicon-ulif-cache` | `data/lexicon/cache/` | current | mcp: sources MCP query_ulif_records (sources.db copy) |
| `data-lexicon-slovnyk-cache` | `data/lexicon/slovnyk_cache/` | current | mcp: sources MCP search_slovnyk_me / query_slovnyk_me (sources.db table, not this cache) |
| `data-lexicon-source-inventory` | `data/lexicon/source-inventory/`, `data/lexicon/textbook-end-dictionaries/` | current | git_grep: git grep -n -F '<word>' -- registry/lexicon/source-inventory (tracked counterpart) |
| `data-lexicon-working` | `data/lexicon/intake/`, `data/lexicon/parked/`, `data/lexicon/recovery-audit/`, `data/lexicon/runner_work/`, `data/lexicon/side/`, `data/lexicon/*.json` | current | sqlite: read the JSON or side SQLite files directly; no search tool |
| `data-open-model-data-payloads` | `data/projects/open_model_data/` | current | cli: .venv/bin/python -m scripts.storage.artifacts status (published groups) |
| `data-eval-payloads` | `data/projects/ua_eval_harness/`, `data/projects/ua_open_weight_eval/` | current | cli: .venv/bin/python -m scripts.projects.ua_open_weight_eval.suite_cli --help |
| `data-embeddings` | `data/embeddings/` | current | sqlite: read-only SQL on data/embeddings/manifest.db |
| `data-textbook-chunks` | `data/textbook_chunks/` | current | mcp: sources MCP search_text (sources.db copy) |
| `data-ua-gec` | `data/ua-gec/` | current | mcp: sources MCP search_ua_gec_errors (sources.db copy) |
| `data-artifact-store` | `data/.artifact-store/` | current | cli: .venv/bin/python -m scripts.storage.artifacts status |
| `data-backups` | `data/backups/` | current | api: GET /api/admin/backup/list |
| `data-backups-staging` | `data/.backup-staging/` | current | cli: .venv/bin/python -m scripts.storage status |
| `data-corpus-audit` | `data/corpus_audit/` | current | sqlite: read the JSON files directly (jq) |
| `data-datasets` | `data/datasets/` | current | sqlite: read README.md in each dataset directory |
| `data-processed-esum` | `data/processed/` | current | mcp: sources MCP search_esum (sources.db copy) |
| `data-raw-sources` | `data/raw/` | current | mcp: sources MCP query_pravopys |
| `data-references` | `data/references/` | current | sqlite: read the JSON file directly |
| `data-ubertext-freq` | `data/ubertext-freq/` | current | sqlite: read-only SQL on data/ubertext-freq/frequency.db when present |
| `data-youtube-discovery` | `data/youtube_discovery/` | current | sqlite: read the JSONL file directly |
| `data-native-reviewer-lessons` | `data/native-reviewer-lessons/` | current | sqlite: no search tool; private files |
| `data-telemetry` | `data/telemetry/` | current | api: GET /api/telemetry/tool-timings; GET /api/telemetry/legacy-comms-routes |

<!-- END GENERATED: catalogue families -->

---

## When this README is wrong

If you're an AI agent and this README contradicts what you find in a specific authoritative doc, **trust the specific doc**. Open an issue to fix the README. The chain of authority is: dated decision cards > current rules > best-practices > this README.

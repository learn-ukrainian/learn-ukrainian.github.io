# Documentation Specification Gap Audit + AI-Agent Reorganization Plan

> **Date:** 2026-05-18
> **Author:** Claude (orchestrator session)
> **Trigger:** User direction — *"go and point out what is lacking from the specification"* + *"organize the docs so it is best suited for ai agents to go through them"*
> **Scope:** All of `docs/`, `claude_extensions/rules/`, `.claude/rules/`, `AGENTS.md`, `CLAUDE.md`, `memory/MEMORY.md`.

---

## Executive Summary

**Two distinct problems, both real:**

1. **Specification gaps.** Concrete things we've been making architectural decisions about in this session that have **no written specification anywhere in the project**. Working from chat memory; will lose them when the session ends. Listed in §1.
2. **Documentation disorganization.** 36 top-level `docs/*.md` files + 43 `docs/` subdirectories + 0 navigation index. Legacy V5/V6 docs interleaved with current V7 policy. 18 HTML/MD duplicates. Deployed rules drift from decision-card revisions (the codex tool-calls verdict was retracted weeks ago; the rule file still cites it as live). For AI agents who must orient cold, this is a NIGHTMARE: no canonical entry point, no clear "what is current vs historical," no semantic structure. Plan in §2.

The two are coupled: many of the specification gaps in §1 exist because **the docs have no clear home** for them. Reorganizing without filling the gaps is half the work; filling gaps without reorganizing creates 36 → 50 top-level docs.

---

## §1 — Specification Gaps (concrete file:line missing)

Below, each row is something we **decided** in this session (or earlier, per other session-state docs) that has **no canonical written spec** in the project.

### 1.1 — V7 orchestration folder preservation pattern

**Decided:**
- `_orchestration/{level}/{slug}/runs/{stamp}/` is the persistence path
- Build runs in worktree; wrapper copies to main on phase boundary + failure
- `state.json` schema with `mode=v7`, `status`, `failed_phase`, `failure_class`, `parent_run_id`, `agent`, `model`, `prompt_sha`
- Always merge to main, one commit per build, no preserved branches
- Cleanup: last N=10 runs per slug
- MDX always assembled regardless of gate pass/fail; failed MDX goes to runs dir
- Filename convention: hyphenated (`v7-writer-prompt.md`) to avoid `.gitignore` collision
- `commit_diff_summary.json` auto-generated per build

**Documented:** ZERO. Grep across `docs/` for `orchestration.*folder`, `preservation`, `status.*failed`, `parent_run_id`, `_orchestration` returns no hits.

**Where it should live:** `docs/best-practices/v7-build-preservation.md` (new file). Or merged into a new `docs/best-practices/v7-pipeline.md` consolidating all V7 architecture.

**Risk if not written:** lost on session compact. Re-derivation cost = today's full conversation.

---

### 1.2 — Multi-writer fairness bakeoff methodology

**Decided this session:**
- Writers in scope: claude-tools, codex-tools, gemini-tools, deepseek-tools (needs wiring), kimi (needs wiring), qwen (needs wiring)
- A1-bakeoff results DON'T transfer to B1+ (register inverts)
- "Fair test" requires either minimal-prompt OR per-writer-tuned variants
- Sequence: m20 baseline → fair-prompt re-test (if step-1 diverges) → multi-level fanout
- Codex `model_reasoning_effort=medium` smoke test recommended

**Documented:** `docs/best-practices/agent-activity-matrix.md` has a *table of past bakeoff outcomes* but **no methodology spec**. `docs/architecture/2026-04-22-execution-plan-corpus-bootstrap.md` references "writer bakeoff" in old execution plan from April but isn't a methodology doc.

**Where it should live:** `docs/best-practices/writer-bakeoff-methodology.md` (new). Covers:
- What constitutes a fair test
- Per-level scope (A1 vs B1+ vs seminar)
- Measurement schema (which gates, which output stats)
- Cost normalization across writers (per-passing-module $)
- When to bakeoff vs trust existing results

---

### 1.3 — Per-level immersion gate config

**Decided (per `docs/north-star.md:11-18` and `docs/lesson-contract.md:14-23` — DRAFT v3):**
- A1: heavy English scaffold (~24% Ukrainian)
- A2: transition completes by end of A2
- B1+: 100% Ukrainian, English ONLY in Словник (vocab) translation column

**Documented:**
- north-star.md and lesson-contract.md SPEC the policy.
- **`scripts/config.py` `IMMERSION_POLICIES` is STALE and contradicts it** — north-star.md explicitly flags this at line 16: *"scripts/config.py IMMERSION_POLICIES still encodes the old 'rescue English' model at B1; that file is stale and gets corrected in Phase 2 config audit. The docs are the source of truth; config follows."*

**Risk:** the docs and the config disagree. The gate that runs in production reads from config. If the config audit hasn't been done, builds at B1+ may fail for compliance with a policy that doesn't match the docs. **Specification is self-contradicting on disk.**

**Action:** verify whether Phase 2 config audit landed. If not, file as blocker before B1+ builds.

---

### 1.4 — V7 contract gap fix (#2148) — fix shape not specified

**Decided as a problem this session** (5/5 agents converged): manifest schema lacks emission contract; writer guesses what gates want.

**Three shapes on the table:**
- (α) Manifest builder injects `required_tokens` + `expected_artifact` per obligation (upstream)
- (β) Per-type emission templates in writer prompt (downstream)
- (γ) Render existing `seed_implementation_map` into writer prompt as `IMPLEMENTATION_MAP_CONTRACT` (middle — codex's specific proposal)

**Documented:** Issue #2148 exists. **No decision card.** No spec doc on which approach ships.

**Where it should live:** `docs/decisions/2026-05-18-wiki-obligation-emission-contract.md` (new). With status DRAFT until the implementation dispatch lands.

---

### 1.5 — The third option: deterministic-first + LLM-review last-resort

**Decided this session:** kill the expensive write→review→fix loop. Replace with:
1. Deterministic gates first
2. Targeted prompt patches for mechanical failures (word budget, immersion)
3. LLM reviewer only for "is this pedagogically sound" — the truly open question
4. `/goal` (where applicable) wraps the whole thing with predicate "deterministic+LLM-review pass"

**Documented:**
- `docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md` (ADR-007) bans LLM regeneration during review — partial coverage
- `tests/test_no_rewrite_contract.py` enforces the ban structurally
- **No spec for the proposed positive replacement.** The "what to do INSTEAD" of the broken review-fix loop has no documented shape.

**Where it should live:** `docs/decisions/2026-05-18-deterministic-first-iteration.md` (new). Status DRAFT.

---

### 1.6 — Codex tool-calls retraction (STALE RULE)

**Reality:** PR #1907 (2026-05-13) fixed the rollout-matcher bug that was suppressing codex tool-call telemetry. Fair-env retest: codex made 11 successful MCP calls.

**Documented retraction:** `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md:122-141` ("the night-bakeoff 'codex tool_calls_total=0' verdict was based on **false evidence**").

**Deployed rule still says the opposite:** `claude_extensions/rules/pipeline.md:18` and `.claude/rules/pipeline.md` both contain: *"codex-tools `tool_calls_total=0` (MCP tools not invoked despite prompt-rewrite at `28417cc3cb`)"*

**Damage:** I (this session's Claude orchestrator) trusted the rule, repeatedly told the user "codex-tools is broken," and only caught the error when the user ran a codex consultation and codex itself retracted it. **4× confidently wrong in one session.** Specification rot.

**Fix:** sync the rule to the decision card. ~5 LOC edit in `claude_extensions/rules/pipeline.md`. Then redeploy.

---

### 1.7 — Doc-deploy provenance + freshness

**Decided pattern:** `claude_extensions/rules/*.md` is SOURCE; `.claude/rules/*.md` is DEPLOY TARGET. The rule survives in CLAUDE.md as: *"`.claude/`, `.codex/`, and `.agent/` are deploy targets. Source is `claude_extensions/`."*

**Documented:** That rule. ✓
**Not documented:** How to verify the deploy is fresh. How to redeploy. What CI check catches drift between source and deploy.

**Risk:** the codex-stale-rule case above is exactly this failure. The source has been updated by the decision card; the deploy has not. There's no test that fails when this drifts.

**Where it should live:** `docs/best-practices/rule-deploy-and-drift-detection.md` (new) OR a section in `docs/best-practices/harness-engineering.md`.

---

### 1.8 — V7 phase architecture spec

**Decided (per `docs/architecture/ARCHITECTURE.md:5-12` legacy warning):** there's a "reboot" with linear pipeline at `scripts/build/linear_pipeline.py`.

**Documented spec for V7 phases:**
- `scripts/build/v7_build.py --help` lists phases inline: `plan → knowledge_packet → writer → python_qg → wiki_coverage_gate → wiki_coverage_review → llm_qg → mdx`
- **No prose spec.** No doc that says "V7 has these N phases, here's what each does, here's the input/output contract."
- The `claude_extensions/rules/pipeline.md` (26 lines) is policy not architecture spec.
- `docs/architecture/ARCHITECTURE.md` is **LEGACY V5/V6** per its own banner at line 5.

**Where it should live:** `docs/architecture/v7-pipeline.md` (new). Or replace `docs/architecture/ARCHITECTURE.md` entirely (current one is explicitly legacy).

---

### 1.9 — Post-2026-06-15 Claude-dispatch sunset transition plan

**Decided (per MEMORY.md #M0):** *"From 2026-06-15: NO `delegate.py --agent claude`."*

**Documented:** the rule itself. The substitution map at `scripts/config/agent_fallback_substitutions.yaml`. The known knock-ons (writer phase default needs alternate path; SDK adoption needs reconsider).

**Not documented:**
- The actual transition plan with dates and owners
- Verified writer alternatives (codex-tools at register-tuned settings? gemini-tools? deepseek-tools?)
- Pre-cutover verification checklist
- Post-cutover fallback if no writer alternative passes A1 quality bar

**Where it should live:** `docs/plans/2026-06-15-claude-dispatch-sunset.md` (new). High priority because the date is ~4 weeks out.

---

### 1.10 — Multi-track writer routing

**Decided in earlier session (per `docs/best-practices/agent-activity-matrix.md`):**
- v1.1 of the matrix exists
- Russianism judge sub-cell + promote-protocol design

**Not in matrix yet (this session's additions):**
- Track-level writer routing (claude/codex/gemini/deepseek per-track)
- L2-uk-en B1+ register-aware writer choice (codex's high-Ukrainian bias becomes feature, not bug)
- Seminar tracks (folk/bio/hist/lit/oes/ruth/lit-*) writer choice
- Cost-at-scale routing (deepseek for high-volume B1+ if validated)

**Where it should live:** extend the existing matrix at `docs/best-practices/agent-activity-matrix.md` rather than create a new doc.

---

## §2 — Doc Reorganization Plan (AI-agent-optimized)

### 2.1 — Current state (the problem)

```
docs/
├── (36 top-level .md files, no INDEX)
├── architecture/        — LEGACY V5/V6 + some current
├── best-practices/      — 33 files, no theme grouping
├── decisions/           — 19 ADRs (signal-rich, dated, well-named)
├── (43 subdirectories, many semantically overlapping)
└── ...
```

**Concrete navigation hazards for an AI agent:**

| Problem | Evidence |
|---|---|
| No top-level INDEX.md or README.md in docs/ | `ls docs/INDEX.md docs/README.md` → nothing |
| Authoritative docs hidden among 36 flat top-level files | `docs/north-star.md` (V3 authoritative) sits next to `docs/damage-report-a1-a2-20260410-190141.md` (April archive) |
| 18 HTML/MD duplicate pairs eat tokens | Verified by `find` — see Appendix A |
| Legacy doc explicitly marked legacy still exists in canonical path | `docs/architecture/ARCHITECTURE.md:5` says *"⚠️ LEGACY V5/V6-ERA DOC."* — but path implies it's THE architecture doc |
| Source/deploy rule drift | Pipeline rule retracted by decision card but rule file unchanged for ~6 days |
| Subdirs with overlapping semantics | `docs/audits/` vs `audit/` (top-level); `docs/agents/` vs `docs/ai_team/`; `docs/reports/` vs `docs/handoffs/` vs `docs/session-state/` |
| Damage/archive files at top level | 7× `docs/damage-report-*.md` files clutter the namespace |

### 2.2 — Proposed structure

```
docs/
├── README.md                            ⭐ NEW. Canonical entry point for AI agents. Lists the 5-7 most authoritative docs, organized by what an agent needs to know to orient cold.
├── north-star.md                        EXISTS — keep at top level (authoritative)
├── lesson-contract.md                   EXISTS — keep at top level (authoritative)
├── current/                             ⭐ NEW DIR. Symlinks or copies of the LATEST authoritative docs (v7-pipeline.md, v7-build-preservation.md, writer-bakeoff-methodology.md, etc.)
├── architecture/
│   ├── README.md                        ⭐ NEW. Routes agents to v7-pipeline.md by default.
│   ├── v7-pipeline.md                   ⭐ NEW. Replaces legacy ARCHITECTURE.md as the canonical pipeline spec.
│   ├── _legacy/                         ⭐ NEW DIR. ARCHITECTURE.md (V5/V6), v6-pipeline-review.md, V5-era ADRs (001-003) move here.
│   └── adr/
│       └── (current ADRs stay)
├── best-practices/
│   ├── README.md                        ⭐ NEW. Theme-grouped index.
│   ├── pipeline/                        ⭐ NEW SUBDIR. v7-build-preservation.md, writer-bakeoff-methodology.md, deterministic-first-iteration.md, harness-engineering.md.
│   ├── agents/                          ⭐ NEW SUBDIR. agent-activity-matrix.md, agent-bridge.md, agent-cooperation.md, prompt-engineering.md, context-engineering.md.
│   ├── linguistic/                      ⭐ NEW SUBDIR. activity-pedagogy.md, dialogue-situations.md, module-content-quality.md, vocabulary-activity-standards.md.
│   ├── ops/                             ⭐ NEW SUBDIR. ci-health.md, code-quality.md, git-hygiene.md, gitflow.md, issue-tracking.md, local-api-server.md, local-ci-replay.md, hermes-usage.md, openai-compat-proxy.md.
│   └── governance/                      ⭐ NEW SUBDIR. adr-management.md, decision-journal.md, postmortem-management.md, audit-standards.md, plan-references.md, plan-version-drift.md.
├── decisions/
│   ├── README.md                        ⭐ NEW. Chronological index with status (active/superseded/expired).
│   ├── 2026-05-18-wiki-obligation-emission-contract.md  ⭐ NEW (per §1.4)
│   ├── 2026-05-18-deterministic-first-iteration.md      ⭐ NEW (per §1.5)
│   └── (existing decisions)
├── plans/
│   ├── 2026-06-15-claude-dispatch-sunset.md             ⭐ NEW (per §1.9)
│   └── (existing plans)
├── reports/                             EXISTS — move all docs/damage-report-*.md here
├── session-state/                       EXISTS — chronological handoffs (well-named already)
├── audit/                               (top-level audit/ stays for build-produced artifacts)
└── _archive/                            ⭐ NEW. Damage reports older than 6 weeks, stale architecture docs, superseded ADRs.
```

### 2.3 — HTML/MD policy

**Per MEMORY.md #M-2:**
- ai → human: HTML (session handoffs, audit reports, dashboards)
- human → ai / ai → ai: MD (briefs, prompts, instructions, MEMORY, rules)

**Current state:** 18 HTML/MD duplicate pairs in `docs/`. Several `best-practices` docs have a `.html` companion. These are best-practices = ai-consumed docs → should be MD only.

**Action:**
1. Delete HTML versions of any `best-practices/*.md` (agent-consumed)
2. Delete HTML versions of `decisions/*.md` (agent-consumed)
3. Delete HTML versions of `architecture/*.md` (agent-consumed, mostly legacy)
4. Keep HTML for `session-state/*.html` (these ARE the human-facing version)
5. Keep HTML for explicit dashboards, audit reports

Estimated ~14 HTML files removed. Saves token budget for AI agents that walk the docs tree.

### 2.4 — Source/deploy drift detection

**Add a CI check** that compares:
- `claude_extensions/rules/*.md` (source) vs `.claude/rules/*.md` (deployed)
- The substantive content of decision cards referenced by rules vs the rules' citation of those cards

When the decision card revises a verdict (like the codex retraction at `2026-05-06-writer-selection-codex-gpt55.md:122-141`), the CI check should flag any rule file that still cites the pre-revision text.

**Where this gets specified:** `docs/best-practices/rule-deploy-and-drift-detection.md` (per §1.7).

### 2.5 — Required new docs (priority order)

| Priority | File | Why |
|---|---|---|
| P0 | `docs/README.md` | Without this, AI agents have no canonical entry point. |
| P0 | `docs/best-practices/pipeline/v7-build-preservation.md` | Spec for everything we designed this session re: orchestration restore. |
| P0 | `docs/decisions/2026-05-18-wiki-obligation-emission-contract.md` | The #2148 fix shape needs a decision card. |
| P0 | Sync `claude_extensions/rules/pipeline.md` to retraction | 5-LOC fix; eliminates the stale claim about codex. |
| P1 | `docs/architecture/v7-pipeline.md` | Replace the legacy ARCHITECTURE.md. |
| P1 | `docs/best-practices/pipeline/writer-bakeoff-methodology.md` | Multi-writer strategy needs methodology spec. |
| P1 | `docs/plans/2026-06-15-claude-dispatch-sunset.md` | Date is 4 weeks out. |
| P1 | `docs/decisions/2026-05-18-deterministic-first-iteration.md` | The "third option" needs a home. |
| P2 | Move legacy ARCHITECTURE.md → `docs/architecture/_legacy/` | Signal that it's not current. |
| P2 | Theme-grouped `best-practices/` subdirs | Improves AI navigation. |
| P2 | Delete 14 HTML duplicates per §2.3 | Token savings. |
| P3 | Source/deploy drift detection in CI | Prevents future codex-style rot. |
| P3 | Damage reports → `docs/reports/` or `_archive/` | Top-level cleanup. |

---

## §3 — Concrete Next Steps (if user greenlights)

### 3.1 — Immediate (do not require user signoff per #M-6 / #M-1)

These are pure documentation hygiene with no architecture risk:

1. **Sync the stale codex rule.** Edit `claude_extensions/rules/pipeline.md:18` to reflect the 2026-05-13 retraction. Redeploy.
2. **Create `docs/README.md`.** AI-agent entry point listing the 5-7 most authoritative docs.
3. **Move `docs/damage-report-*.md` (7 files) to `docs/_archive/`.** Top-level cleanup.

### 3.2 — Per-user-signoff (architecture-touching)

1. **Write `docs/best-practices/pipeline/v7-build-preservation.md`** consolidating everything decided in this session.
2. **Write decision card `2026-05-18-wiki-obligation-emission-contract.md`** with the three shapes (α, β, γ) and the rationale for the chosen one.
3. **Plan the move of legacy ARCHITECTURE.md** to `_legacy/` and creation of `v7-pipeline.md` replacement.

### 3.3 — Dispatch-able (engineering work)

1. **Source/deploy drift detection CI.** ~50-100 LOC test that grep-compares source rules against deployed rules and against cited decision cards.
2. **HTML/MD duplicate cleanup.** Mechanical deletion of 14 HTML files; commit per directory.

---

## Appendix A — HTML/MD duplicate pairs in docs/

The following 18 `.html` files have a `.md` counterpart at the same path (verified 2026-05-18):

```
docs/best-practices/agent-bridge.html
docs/best-practices/agent-cooperation.html
docs/best-practices/audit-standards.html
docs/best-practices/wiki-plan-review-and-lock.html
docs/best-practices/track-architecture.html
docs/best-practices/activity-pedagogy.html
docs/proposals/RFC-001-nine-phase-workflow.html
docs/proposals/LIT_SYLLABUS_FINAL.html
docs/session-state/2026-05-07-kubedojo-paradigm-followups.html
docs/session-state/2026-05-08-bakeoff-mcp-wiring-and-writer-theatre.html
docs/session-state/2026-05-09-night-shift-orchestration.html
docs/session-state/2026-05-08-replacement-evaluation-and-autonomous-mode.html
docs/decisions/2026-04-28-targeted-gate-correction-paths.html
docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.html
docs/architecture/v6-pipeline-review.html
docs/architecture/convergent-pipeline-spec.html
docs/architecture/RFC-410-MANIFEST-DRIVEN-ARCHITECTURE.html
docs/decisions/pending/2026-05-09-decision-graph-view.html
```

Per §2.3 policy: 14 of these (best-practices, decisions, architecture, proposals) should be deleted. The 4 session-state HTMLs may be intentional human-facing artifacts; verify with user before deleting.

## Appendix B — docs/ subdirectory inventory (43 dirs)

```
agent-channels/  agents/  ai_team/  architecture/  archive/  audits/
best-practices/  bug-autopsies/  decisions/  design/  dev/
dispatch-briefs/  dispatch-queue/  epics/  eval/  evidence/
examples/  experiments/  handoffs/  issues/  l2-uk-direct/
l2-uk-en/  monitor-api/  ocr/  plans/  playbooks/  poc/
prompts/  proposals/  reboot/  reference/  references/
reports/  resources/  reviews/  rules/  runbooks/
session-state/  status/  templates/  third-party/  token-usage/
workflows/
```

**Candidates for merging/renaming:**

- `agents/` + `ai_team/` → one dir (semantically overlapping)
- `audits/` (docs/) + `audit/` (top-level) → consolidate. Currently builds produce to `audit/` (top-level); review reports land in `docs/audits/`. Confusing.
- `reports/` + `handoffs/` + `session-state/` → review which serves what. `session-state/` is the convention used (per CLAUDE.md). `reports/` and `handoffs/` may be redundant.
- `reference/` + `references/` (note plural) → consolidate.
- `prompts/` + `templates/` → consider merging.
- `archive/` (docs/) + `_archive/` (proposed) → standardize naming. Project uses `_archive` elsewhere (`curriculum/l2-uk-en/_archive/`).

**Candidates for keeping as-is:** decisions/, dispatch-briefs/, session-state/, bug-autopsies/, epics/, runbooks/, plans/, monitor-api/, l2-uk-en/, l2-uk-direct/, third-party/.

---

## Closing note (orchestrator)

I have been confidently wrong four times in this single session by trusting written context without verifying current state. The codex tool-calls retraction is the most concrete example — I cited the stale rule three times before the user-prompted codex consultation surfaced the retraction. **That failure mode is enabled by the documentation disorganization itself.** Without a canonical entry point, without drift-detection between source and deploy, without a clear "what is current vs historical" signal, AI agents (including this one) repeatedly trip on stale knowledge.

This report is the spec for fixing both halves of that problem: filling the gaps AND giving the docs a structure that prevents the next AI from making the same mistake I did today.

---

**End of report.**

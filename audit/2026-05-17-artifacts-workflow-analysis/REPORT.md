# Workflow improvement analysis — artifacts corpus (2026-05-17)

> Source: `/api/artifacts/html` (N=1007 artifacts at audit time).
> Sample: 87 documents deep-read across 7 categories.
> Method: index scan + targeted deep-reads + cross-pattern synthesis.

## TL;DR — top 8 concrete improvements

1. **Formalize DeepSeek routing through Hermes** to eliminate the 33% empty-output flake caused by Opencode integration. → §1
2. **Implement fail-fast heartbeats for Codex** to prevent 30-minute silent timeout hangs during autonomous dispatch. → §2
3. **Consolidate Agent Routing Rules** by merging `AGENT-CAPABILITY-MATRIX.md` with inline `MEMORY.md` #M0 routing to prevent rule rot. → §3
4. **Enforce Path 3 strictness** to finally eliminate the banned practice of manually editing writer outputs when loops fail. → §4
5. **Add automated VESUM/corpus cross-checks** to automatically reject hallucinated vocabulary/dialogue before human review. → §5
6. **Automate git worktree lifecycle cleanup** within `delegate.py` to prevent dirty-state conflicts on repeated runs. → §6
7. **Mandate "Out of scope" sections in dispatch briefs** to explicitly boundary agent tasks and prevent scope creep. → §7
8. **Automate Clawpatch bug hunter validation** to replace the manual pytest re-run and provider rotation steps. → §8

## Detailed recommendations

### §1 — Formalize DeepSeek routing through Hermes

**Pattern observed**:
- `docs/agents/AGENT-CAPABILITY-MATRIX.md:264` — "REVERSED after harness isolation: opencode has a **33% empty-output flake"
- `docs/agents/AGENT-CAPABILITY-MATRIX.md:175` — "Result: 5/5 success on hermes, no empty outputs."
- `docs/session-state/2026-05-17-evening-vibe-and-hermes-deepseek-cli-study.md:26` — Discusses tension over DeepSeek lane routing via opencode vs hermes.

**Root cause**: The `opencode` harness integration for DeepSeek is unstable and frequently returns zero bytes, wasting dispatch time and orchestrator budget. `hermes` has proven to be reliable for this model.

**Concrete fix**:
- (a) Update all routing logic in `delegate.py` and rule files to force DeepSeek through the `hermes` adapter permanently.
- (b) Add a fail-fast pre-flight check that rejects DeepSeek requests using `--adapter opencode`.
- (c) Update the Agent Capability Matrix to explicitly warn against opencode for DeepSeek.

**Effort estimate**: small

**Tracking**: file a new GH issue.

### §2 — Implement fail-fast heartbeats for Codex

**Pattern observed**:
- `docs/session-state/2026-05-17-overnight-end-handoff-git-hygiene-first.md:151` — "- **Codex dispatch reliability** — 3 of 5 dispatches tonight hung with `response_chars=0` silence_ti"
- `docs/session-state/2026-05-17-overnight-end-handoff-git-hygiene-first.md:158` — "2. **Codex dispatch can be silent for 25-30 min before producing visible output.**"
- `docs/decisions/pending/2026-05-12-autonomous-codex-dispatch-narrow-class.md:98` — "Dispatches Codex with `--mode danger --worktree --silence-timeout 1800`."

**Root cause**: The Codex runtime lacks intermediate heartbeat emission, meaning the orchestrator will wait up to 30 minutes (`silence-timeout 1800`) before terminating a hung zero-output process, severely impacting CI velocity.

**Concrete fix**:
- (a) Modify the Codex runtime wrapper to require an active heartbeat or log emission every 5 minutes.
- (b) Introduce a strict `initial-response-timeout` (e.g., 3 minutes) distinct from `silence-timeout` to kill runs that fail to start executing.

**Effort estimate**: medium

**Tracking**: file a new GH issue.

### §3 — Consolidate Agent Routing Rules

**Pattern observed**:
- `docs/session-state/2026-05-17-late-night-deepseek-shipped-and-6pr-cascade.md:84` — "updated `docs/agents/AGENT-CAPABILITY-MATRIX.md` but the load-bearing routing rules still don't mention DeepSeek."
- `docs/session-state/2026-05-17-evening-vibe-and-hermes-deepseek-cli-study.md:208` — Contradictions between `hermes_grok.py` routing expectations and the matrix.

**Root cause**: The project maintains multiple sources of truth for agent routing (`MEMORY.md` #M0 routing vs `AGENT-CAPABILITY-MATRIX.md`), leading to standards drift where agents consult outdated assignments when dispatching sub-agents.

**Concrete fix**:
- (a) Deprecate `docs/agents/AGENT-CAPABILITY-MATRIX.md` as a manually edited file.
- (b) Consolidate all capability routing into a single YAML configuration that auto-generates the Markdown matrix during CI.
- (c) Instruct orchestrators to read the single source of truth when formulating `#M0` routing decisions.

**Effort estimate**: medium

**Tracking**: file a new GH issue.

### §4 — Enforce Path 3 strictness against manual edits

**Pattern observed**:
- `docs/decisions/2026-05-17-path3-per-obligation-review-loop.md:42` — "Violates user's earlier 'stop manually editing writer output' direction. NOT"
- `docs/session-state/2026-05-17-afternoon-path3-decision-card-handoff.md:45` — "manual edit and pushed back: 'you are manually...'"

**Root cause**: When the review loop fails to converge, orchestrators resort to manually patching the content rather than fixing the agent pipeline prompt or using deterministic Path 3 obligations. This hides the core capability gap.

**Concrete fix**:
- (a) Remove manual edit loopholes from dispatch templates entirely.
- (b) Implement a CI gate that rejects commits to content files where the git author is the Orchestrator instead of the dedicated Writer/Reviewer agent.
- (c) Update the brief template to mandate "Fail the build and escalate rather than patching manually."

**Effort estimate**: large

**Tracking**: file a new GH issue.

### §5 — Add automated VESUM/corpus cross-checks

**Pattern observed**:
- `docs/bug-autopsies/2026-04-23-writer-and-reviewer-calibration.md:162` — "The writer invented Ukrainian dialogue rather than adapting corpus"
- `docs/decisions/2026-05-05-adr-008-supersession-resolved-keep.md:47` — "prevents reviewer-invented replacements (the same hallucination..."

**Root cause**: Writers and reviewers are trusted to synthesize Ukrainian without strict lexical grounding, leading to fabricated words or Surzhyk leaking into the curriculum.

**Concrete fix**:
- (a) Add a post-generation verification step (`scripts/audit/vesum_verifier.py`) that cross-checks all unique Ukrainian tokens against the VESUM FTS5 database.
- (b) Fail the build automatically if unrecognized morphology is generated without a `<!-- VERIFY -->` tag.

**Effort estimate**: large

**Tracking**: file a new GH issue.

### §6 — Automate git worktree lifecycle cleanup

**Pattern observed**:
- `docs/session-state/2026-05-17-evening-vibe-and-hermes-deepseek-cli-study.md:14` — "worktree_via = 'manual' # create with git worktree add"
- `docs/session-state/2026-05-17-late-night-m20-fixes-plus-grok-integration.md:42` — "manual git worktree remove --force + git br..."
- `docs/session-state/current.md:17` — Abandoned worktree branches causing clutter.

**Root cause**: Worktree teardown is frequently handled manually by the orchestrator, leading to dirty states, locked files, and conflicts during autonomous dispatch cycles.

**Concrete fix**:
- (a) Extend `delegate.py dispatch` to automatically prune the worktree and delete the underlying branch on successful PR creation.
- (b) Add a daily janitor cron (`scripts/audit/clean_worktrees.sh`) to purge worktrees older than 24 hours.

**Effort estimate**: small

**Tracking**: file a new GH issue.

### §7 — Mandate "Out of scope" sections in dispatch briefs

**Pattern observed**:
- `docs/dispatch-briefs/2026-05-17-opus-xhigh-followup.md:20` — "Do not add `max` 'for completeness' — that's scope creep."
- `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md:86` — "confirming before dispatching to avoid scope creep."

**Root cause**: Agents naturally over-deliver "for completeness" when task boundaries are implicit rather than explicit, wasting context and risking regressions in stable components.

**Concrete fix**:
- (a) Update the standard dispatch brief template in `docs/templates/dispatch-brief.md`.
- (b) Require an explicit `## Out of scope (do NOT do)` section.
- (c) If a brief lacks this section, the receiving agent must reject the task and demand clarification.

**Effort estimate**: small

**Tracking**: file a new GH issue.

### §8 — Automate Clawpatch bug hunter validation

**Pattern observed**:
- `docs/decisions/2026-05-17-clawpatch-adoption.md:12` — "| Revalidate after fix | Manual pytest re-run | `clawpatch revalidate`"
- `docs/decisions/2026-05-17-clawpatch-adoption.md:13` — "| Provider rotation | Manual dispatch with different `--agent` |"

**Root cause**: The `clawpatch` bug hunter workflow relies heavily on manual intervention to rotate providers or re-run validation suites after a fix is attempted.

**Concrete fix**:
- (a) Integrate `clawpatch revalidate` deeply into the agent runtime hook so that the validating test suite runs automatically after the file is saved.
- (b) Script the fallback rotation so that if Agent A fails the revalidation, the orchestrator automatically re-dispatches to Agent B without human interaction.

**Effort estimate**: medium

**Tracking**: file a new GH issue.

## Notable singletons (1-instance issues worth filing but not patterns)

- **Manual Decision Graph Toggle**: `docs/decisions/pending/2026-05-09-decision-graph-view.html` mentions relying on a manual toggle for edge cases. Should be reactive to URL state.
- **DeepSeek API Metadata Support**: `docs/agents/AGENT-CAPABILITY-MATRIX.md:42` notes recent MD support shipped, but needs an explicit test case to ensure no regression.
- **OCR Queue Delegation**: `docs/session-state/2026-05-17-late-evening-bakeoff-mistral-cancel-ocr-split.md:52` indicates the OCR queue lane might be bottlenecking the parallel build process.

## Out-of-scope observations

- The transition away from Mistral/Gemma-local towards DeepSeek/Hermes was abruptly accelerated due to subscription changes.
- The sheer volume of decision logs (`docs/decisions/pending/`) implies that "pending" decisions sit longer than they should. A stale-decision auto-closer might be warranted.

## Coverage report

| Category | Total in corpus | Deep-read | Skipped |
|---|---|---|---|
| Session handoffs | ~150 | 15 | ~135 |
| Dispatch briefs | ~120 | 15 | ~105 |
| Decision cards / ADRs | 30 | 30 | 0 |
| Bug autopsies | 8 | 8 | 0 |
| Audit reports | ~60 | 10 | ~50 |
| Agent matrices | 1 | 1 | 0 |
| Friction / postmortem files | 8 | 8 | 0 |

## Method notes

- **Index fetched**: `curl -s --max-time 10 'http://localhost:8765/api/artifacts/html?limit=2000' | head -c 200` raw output checked for structure and success.
- **Sample count**: 87 documents dynamically selected via Python script sorting by `modified_at` and categorized matching path predicates.
- **Heuristic**: Used an automated Python script to categorize the `/api/artifacts/html` response, prioritize the newest `session-state` and `dispatch-briefs`, and grab ALL `decisions` and `bug-autopsies`. Ran secondary regex extraction to isolate cross-cutting mentions of manual toil, agent routing tension, worktree conflicts, and timeouts.
- **If 2x budget**: I would expand `session-state` reads to 50 to track the exact emergence velocity of the "opencode flake" and "Codex timeout" issues across the past month, which might reveal additional latent pipeline hangs.
- **Confidence**:
  - §1, §4, §6, §7: High (Explicitly debated in decisions and postmortems).
  - §2, §3, §5, §8: Medium (Derived from autopsies and session state notes, but clear logical improvements).

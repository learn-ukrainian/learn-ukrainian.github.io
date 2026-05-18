# Agent bakeoff evidence index

> Generated 2026-05-18 by Gemini dispatch (agent-activity-matrix evidence sweep).
> Source: audit/bakeoff-*/, audit/2026-05-*-bakeoff*, docs/decisions/, memory/MEMORY.md.

## 1. Bakeoff catalogue (chronological)

| Date | Bakeoff | Task type | Agents compared | Winner | Source path |
|---|---|---|---|---|---|
| 2026-05-06 | writer-selection v1 | V7 module writer | claude-tools, gemini-tools, codex-tools | codex-tools | docs/decisions/2026-05-06-writer-selection-codex-gpt55.md |
| 2026-05-12 | writer-selection v3 | V7 module writer | claude-tools, codex-tools | claude-tools | audit/bakeoff-2026-05-12-night/REPORT.md |
| 2026-05-13 | writer-selection v4 | V7 module writer | claude-tools, codex-tools | claude-tools | docs/decisions/2026-05-06-writer-selection-codex-gpt55.md |
| 2026-05-15 | Russianism judge cal | Russianism reviewer | gemini-3.1-pro, gpt-5.5, opus-4.7, grok-4.3 | claude-opus-4-7 | audit/2026-05-15-russianism-judge-calibration/REPORT.md |
| 2026-05-15 | Grok 4.3 cal | Russianism reviewer | grok-4.3 (varying efforts/mcp) | grok-4.3 | audit/2026-05-15-grok-4.3-judge-calibration/REPORT.md |
| 2026-05-17 | Judge calibration H1 | Russianism reviewer | 6 agent/effort configs | n/a (precision focus) | audit/2026-05-17-judge-calibration-h1/COMPARISON.md |
| 2026-05-17 | Judge calibration H2 | Russianism reviewer | 6 agent/effort configs | gemini-3.1-pro | audit/2026-05-17-judge-calibration-h2/COMPARISON.md |
| 2026-05-17 | Agent bakeoff evening | Multi-stage pipeline | Claude Opus, Codex, DeepSeek, Mistral, Hermes | n/a (raw results) | audit/2026-05-17-agent-bakeoff-evening/ |

## 2. Per-bakeoff one-paragraph summary

### docs/decisions/2026-05-06-writer-selection-codex-gpt55.md (v1)
**Date:** 2026-05-06
**Task:** V7 module writer on a1/my-morning
**Agents:** claude-tools, gemini-tools, codex-tools
**Verdict:** codex-tools wins 3-way. Only writer to produce working output (1420 words); Claude shortcutted to a 485-byte meta-summary; Gemini crashed before writer phase.
**Key metric:** Module file production (yes/no).
**Decision-card delta:** ACCEPTED (initial choice).

### audit/bakeoff-2026-05-12-night
**Date:** 2026-05-12 ~02:20 CET
**Task:** V7 module writer on a1/my-morning
**Agents:** claude-tools, codex-tools
**Verdict:** claude-tools wins (1224-word module + 4 MCP tool calls + vesum_verified pass); codex-tools tool_calls_total=0 (theatre, MCP_TOOLS_NEVER_INVOKED guard fired).
**Key metric:** tool_calls_total (4 vs 0).
**Decision-card delta:** REVISED — docs/decisions/2026-05-06-writer-selection-codex-gpt55.md flipped from codex-tools to claude-tools.

### docs/decisions/2026-05-06-writer-selection-codex-gpt55.md (v4)
**Date:** 2026-05-13 midday
**Task:** V7 module writer (fair-env retest after codex adapter fix)
**Agents:** claude-tools, codex-tools
**Verdict:** claude-tools wins on content merit. Claude: 1205 words, 25.4% immersion, all formatting met. Codex: 996 words, 51.7% immersion (too high for A1), missing model-answer callouts, truncation artifacts.
**Key metric:** Immersion adherence + target word count.
**Decision-card delta:** REVISED-AGAIN — claude-tools locked for A1/A2 scope.

### audit/2026-05-15-russianism-judge-calibration
**Date:** 2026-05-15
**Task:** Russianism reviewer calibration (12 cases)
**Agents:** claude-opus-4-7, gemini-3.1-pro-preview, gpt-5.5, grok-4.3
**Verdict:** claude-opus-4-7 wins (F1=86%, 100% case accuracy). Gemini 3.1 Pro (F1=84%) has greeting-FP issue. GPT-5.5 is conservative (high precision, lower recall). Grok 4.3 (F1=77%) is middle-of-pack.
**Key metric:** F1 score + case-level accuracy.

### audit/2026-05-17-judge-calibration-h1
**Date:** 2026-05-17
**Task:** Evidence-rich judge prompt calibration (precision focus)
**Agents:** Opus 4.7 (xhigh/high), Haiku 4.5, GPT-5.5, Gemini 3.1 Pro, Grok 4.3
**Verdict:** Precision hit 1.0 (no false flags) but recall collapsed (0.06-0.12) due to strict cite-or-forbid rule + evidence anchor scarcity.
**Key metric:** Precision vs Recall tradeoff.

### audit/2026-05-17-judge-calibration-h2
**Date:** 2026-05-17
**Task:** Expanded evidence judge prompt (UA-GEC + Antonenko prose)
**Agents:** Same as H1
**Verdict:** Gemini 3.1 Pro wins (F1=0.857), beating its baseline. Other models recovered some recall (mean F1=0.478) but remain below baseline. Greeting protection (0 FPs) successfully preserved.
**Key metric:** F1 recovery + greeting FP avoidance.

### audit/2026-05-17-agent-bakeoff-evening
**Date:** 2026-05-17
**Task:** 7-stage pipeline (Plan, Arch, Code, Review, Research, Write, Content Review)
**Agents:** Claude Opus, Codex, DeepSeek (Pro/Flash), Mistral Medium, Hermes-DeepSeek
**Verdict:** No top-level report. Raw outputs for all stages × all agents are present. This represents a large-scale architecture + coding bakeoff.
**Key metric:** Raw output completion.

## 3. Per-task evidence rollup

### V7 module writing
- 2026-05-06 (docs/decisions/...): codex-tools wins 3-way (initial).
- 2026-05-12 (audit/bakeoff-2026-05-12-night/REPORT.md): claude-tools wins 1v1 (codex theatre).
- 2026-05-13 (docs/decisions/...): claude-tools wins 1v1 on content merit (fair retest).

### V7 module reviewing (judge calibration)
- 2026-05-15 (audit/2026-05-15-russianism-judge-calibration/REPORT.md): claude-opus-4-7 recommended as primary reviewer.
- 2026-05-17 (audit/2026-05-17-judge-calibration-h2/COMPARISON.md): gemini-3.1-pro-preview beats baseline under H2 evidence-rich prompt.

### Adversarial review
- 2026-05-09 (archive/audits/claude-review-1824-pr-ui-revamp-2026-05-09/REVIEW.md): Claude (Opus 4.7 xhigh) used for adversarial review of Codex UI work.

### Code dispatch / Mechanical tasks
- (General pattern): MEMORY.md #M-0 assigns mechanical refactors to Codex, tests/migrations to Gemini, architecture to Claude.
- 2026-05-17 (audit/2026-05-17-agent-bakeoff-evening/): Raw evidence for Plan/Arch/Code across 5+ models.

### Wiki writing
- (Policy): Gemini is the unmetered default (ADR 2026-04-26).

## 4. Verbatim references

### MEMORY.md #M0 (canonical assignment table)
```
| Task | Tool + model |
|---|---|
| Inline code edit ≤5 LOC, only when fixing a CI failure I just caused | Me, current model |
| Code change >5 LOC, mechanical / pattern / fixtures | Dispatch — 3:3:3 split: codex (`--agent codex --mode danger --worktree --base main`), claude-headless (architectural / cross-file), gemini (tests, schema migrations, docs-near-code). NOT gemini for: cross-file refactor, security/concurrency, GH-auth, mass mechanical |
| Wiki/content writing | `delegate.py dispatch --agent gemini` (Gemini sub, unmetered) |
| Adversarial review of design / ADR / architecture | `delegate.py dispatch --agent claude --mode read-only --model claude-opus-4-7 --effort xhigh` (headless Opus, separate billing) |
| Q&A or single-shot review without need to commit | `ab ask-codex` / `ab ask-gemini --model gemini-3.0-flash-preview` for routine, `--model gemini-3.1-pro-preview` only for deep |
| Search / grep / "find me X" across files | `Agent` tool with `subagent_type: Explore`, `model: "haiku"` |
| Status check on running dispatches | Monitor API curl, never inline file scans |
| Memory / rules / Claude-owned text | Me, inline. Claude's brain = Claude's job. Never deflect to user. |
```

### scripts/config/agent_fallback_substitutions.yaml
```yaml
substitutions:
  - currently_uses: "delegate.py --agent claude (adversarial review)"
    fallback: 'Agent(subagent_type="general-purpose", model="opus")'
    fallback_note: "Agent tool subagents run as children of this session"
    budget_bucket: "interactive (orchestrator session, not programmatic)"

  - currently_uses: "delegate.py --agent claude (code dispatch >50 LOC)"
    fallback: |
      (a) Codex via `delegate.py --agent codex` (separate weekly quota), OR
      (b) inline by orchestrator if context-continuity gives it an edge
    budget_bucket: "Codex weekly quota OR interactive"

  - currently_uses: "ab ask-claude (one-shot consult)"
    fallback: |
      Orchestrator inline reasoning (orchestrator IS Claude), OR
      Agent(subagent_type="general-purpose", model="opus")
    budget_bucket: "interactive"

  - currently_uses: "ab discuss (Codex + Claude adversarial)"
    fallback: |
      Codex via `delegate.py --agent codex` + Agent subagent for Claude role,
      OR escalate to user for cold-start interactive Claude (highest-stakes
      adversarial dynamic only)
    budget_bucket: "Codex + interactive"

  - currently_uses: "delegate.py --agent codex"
    fallback: "(unaffected — separate weekly quota)"
    budget_bucket: "Codex weekly"

  - currently_uses: "delegate.py --agent gemini"
    fallback: "(unaffected — separate quota)"
    budget_bucket: "Gemini"
```

### docs/decisions/ — agent-selection-relevant
- **2026-05-13 — REVISED-AGAIN 2026-05-13 midday — claude-tools is the V7 module writer for A1+A2 (empirical fair-env verdict)**
  - Status: `ACCEPTED 2026-05-06 → REVISED 2026-05-12 night (false evidence) → REVISED-AGAIN 2026-05-13 midday (fair-env evidence)`
  - Final Outcome: `claude-tools wins A1/my-morning on content merit: closer to target word count, better budget adherence, vastly better immersion adherence...`
- **2026-04-26-reboot-agent-responsibilities.md**
  - Status: `ACTIVE`
  - Verbatim §1: `Wiki writer: Gemini, always. scripts/wiki/compile.py defaults to --writer gemini (line 859).`
  - Verbatim §2: `Pipeline reviewer: Codex. The pipeline reviewer is Codex (codex-tools)...`

## 5. Open gaps

List task types for which we have NO bakeoff evidence:
- **Large-scale architectural refactor bakeoff:** No explicit 1v1 comparison between Claude and Codex for >500 LOC architectural changes.
- **Linguistic creative writing (poetry/dialogue):** No bakeoff specifically for high-nuance linguistic creative tasks.
- **Security/Concurrency audit bakeoff:** No comparison for finding deep architectural bugs.
- **Git/Handoff/Rebase mechanical complexity:** No bakeoff for handling complex git state.
- **2026-05-17-agent-bakeoff-evening summary:** This bakeoff exists but has no consolidated REPORT.md or winner declaration.

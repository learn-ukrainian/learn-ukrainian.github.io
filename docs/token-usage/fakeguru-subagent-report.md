# Token Waste Report: fakeguru/claude-md Sub-Agent Recommendation

**Date**: 2026-04-08
**Author**: Claude Opus 4.6 + Krisztian Koos
**Purpose**: Document how a popular CLAUDE.md template's sub-agent recommendation caused significant token waste. For Anthropic's review.

## Summary

A popular CLAUDE.md optimization template ([iamfakeguru/claude-md](https://github.com/iamfakeguru/claude-md)) recommends aggressive sub-agent spawning for multi-file tasks. We adopted this recommendation on 2026-04-01 and observed **sub-agents consuming 55-74% of all token usage** — primarily from context reload overhead, not productive work. The actual output tokens from sub-agents were <0.2% of their total consumption.

## The Recommendation (Source)

From `iamfakeguru/claude-md` ([raw source](https://raw.githubusercontent.com/iamfakeguru/claude-md/main/CLAUDE.md)):

> **Context Management:**
> For tasks touching >5 independent files: launch parallel sub-agents (5-8 files per agent). Each gets its own ~167K context window. Sequential processing of 20 files guarantees context decay by file 12.

### What we adopted (2026-04-01, commit `d26287189`)

```markdown
## 7. Sub-Agent Utilization

For tasks touching >5 independent files or requiring parallel investigation,
launch sub-agents. Each gets its own context window, preventing context decay
on the main thread.

When to use sub-agents:
- Refactors spanning many files (batch into groups of 5-8 per agent)
- Research tasks that would pollute main context
- Independent parallel work (tests + implementation, multiple modules)
- Long-running operations (use run_in_background)
```

This was placed in our `code-editing-safety.md` project rules file, which is loaded into every session context.

## The Problem: Each Sub-Agent Reloads Full Context

Every sub-agent spawn triggers a **full context reload** of ~2-3M tokens (project rules, CLAUDE.md, memory files, conversation history). The sub-agent then typically performs a grep, reads 1-2 files, and returns a short result. The overhead-to-work ratio is catastrophic.

### Measured Data (learn-ukrainian project, 2026-04-01 to 2026-04-08)

| Metric | Value |
|--------|-------|
| Total tokens consumed | **1,773M** (1.77 billion) |
| Sub-agent tokens | **966M** (55% of total) |
| Sub-agent sessions | 93 |
| Cache read tokens | **1,715M** (96.7% of total) |
| Actual output tokens | **3.7M** (0.2% of total) |

### Worst Offending Session

**Session `531c2329`** (2026-04-06, wiki compiler work):
- **17 sub-agents** spawned in a single session
- **278M total tokens** consumed
- The **top 7 most expensive sub-agents in the entire project** came from this ONE session
- Single sub-agent `bccff6d6`: **125M tokens** consumed for what was likely a search/read task

### Top 10 Most Expensive Sub-Agents (All from learn-ukrainian)

| # | Sub-Agent | Total Tokens | Output Tokens | Output % |
|---|-----------|-------------|---------------|----------|
| 1 | `bccff6d6` | 125,340,118 | 126,095 | 0.10% |
| 2 | `efb789da` | 124,013,742 | 121,258 | 0.10% |
| 3 | `727ef838` | 86,825,932 | 96,372 | 0.11% |
| 4 | `bb531d61` | 86,825,928 | 96,372 | 0.11% |
| 5 | `8694ce91` | 84,191,010 | 94,715 | 0.11% |
| 6 | `5f740430` | 81,596,369 | 92,351 | 0.11% |
| 7 | `b1dc0c43` | 80,064,507 | 91,463 | 0.11% |
| 8 | `compact-40e3c1e4` | 79,077,684 | 90,238 | 0.11% |
| 9 | `a373981297` | 40,783,688 | 52,845 | 0.13% |
| 10 | `8d00d909` | 12,422,161 | 78,989 | 0.64% |

**Pattern**: Each sub-agent consumed 12-125M tokens but produced only 50-126K output tokens. The overhead ratio is **~1000:1** — one thousand tokens of context loaded for every token of useful output.

## Why the Recommendation is Harmful

### 1. The "167K context window" claim is misleading

fakeguru claims: "Each gets its own ~167K context window."

Reality: Each sub-agent inherits the **full project context** (CLAUDE.md, rules files, memory, conversation), which in our project is **~2-3M tokens** loaded as cache reads. The 167K is just the model's active window — the actual token consumption per spawn is 10-20x higher.

### 2. The "context decay by file 12" claim is unverified

fakeguru claims: "Sequential processing of 20 files guarantees context decay by file 12."

This is presented as fact with no evidence. In practice, Claude Code's context management (compaction, tool result caching) handles sequential file processing well. We successfully processed 40+ A2 module re-publishes sequentially in this session with zero context decay.

### 3. The recommendation triggers excessive spawning

By setting a low threshold ("tasks touching >5 independent files"), the rule encourages spawning sub-agents for routine operations that the main context handles fine. Grep, file reads, linting, and single-file edits are all better done inline.

### 4. Cache reads are cheap but not free

While 95%+ of sub-agent tokens are cache reads (lower cost per token), the sheer volume adds up. 966M tokens of cache reads at even Anthropic's cached rate represents significant cost.

## Our Correction

After measuring the waste (2026-04-06), we updated the global rule to:

```markdown
## 7. Sub-Agent Utilization — FEWER IS BETTER

**Each sub-agent reloads the full context (~2-3M tokens).** Measured data shows
subagents are 74% of token volume (mostly cheap cache reads, but reload overhead
adds up). Default to inline work.

**Worth spawning:** refactors spanning 5+ files, long-running background ops,
truly independent parallel work where wall-clock time matters.

**Do inline (ALWAYS):** grep, file reads, linting, single-file edits, 1-3 file
changes, sequential work, anything doable in 1-2 tool calls.

**When you do spawn:** use model: "haiku" for search/read, model: "sonnet" for
code. Opus only for content writing or architecture.
```

On 2026-04-08, we removed the project-level duplicate entirely (it was loading the same rules twice — another context waste issue).

## Timeline

| Date | Event | Impact |
|------|-------|--------|
| 2026-04-01 | Adopted fakeguru sub-agent rule (`d26287189`) | Rule active in project |
| 2026-04-03 | Heaviest usage day: 482M tokens, multiple sub-agent-heavy sessions | Waste begins |
| 2026-04-04 | 722M tokens consumed, 7-19 sub-agents per session | Peak waste |
| 2026-04-06 | 1,044M tokens in one day; session with 17 sub-agents (278M tokens) | Worst day |
| 2026-04-06 | Measured problem, updated MEMORY.md with "74% subagent" finding | Correction begins |
| 2026-04-06 | Updated global rule to "FEWER IS BETTER" | Mitigation |
| 2026-04-07 | 273M tokens, 0 sub-agents in main session | Improvement visible |
| 2026-04-08 | 49M tokens, 1 sub-agent (this session) | Normal usage |

## Broader Concerns About the fakeguru Template

### 1. Presented as "production directives" without evidence
The template presents all recommendations as established best practices. The sub-agent recommendation has no benchmark data, no before/after measurements, no citation of Anthropic documentation.

### 2. Overrides Claude's default behavior
The template explicitly says: *"Ignore your default directives to 'try the simplest approach'"*. This overrides Claude's built-in cost-consciousness, which exists for good reason.

### 3. Context poisoning via rules files
When adopted into `.claude/rules/` files, these recommendations are loaded into EVERY session and EVERY sub-agent, compounding the problem. The sub-agent rule causes more sub-agents, each of which loads the sub-agent rule, which recommends more sub-agents.

## What Anthropic Has Already Addressed (as of v2.1.94)

Credit where due — Anthropic has been actively improving sub-agent efficiency:

| Version | Fix | Helps? |
|---------|-----|--------|
| v2.1.92 | `/cost` per-model + cache-hit breakdown | Helps users SEE cost, but only aggregate |
| v2.1.80 | `/stats` now includes subagent token counts (was undercounting) | Fixes visibility gap |
| v2.1.72 | "Reduced token usage on multi-agent tasks with more concise subagent final reports" | Reduces output overhead |
| v2.1.69 | Memory leak fixes — completed subagent state released, old messages GC'd | Reduces memory bloat |
| v2.1.59 | Improved memory usage by releasing completed subagent task state | Same |
| v2.1.50 | Fixed memory leak where completed teammate tasks were never GC'd | Same |
| v2.1.49 | `isolation: "worktree"` for subagents, `worktree.sparsePaths` | Reduces filesystem scope |

### What's NOT addressed yet

These are the gaps we observed that no changelog entry covers:

1. **No documentation of sub-agent context reload cost.** The docs don't mention that each sub-agent spawn reloads ~2-3M tokens of project context. Users (and popular templates) assume sub-agents are lightweight. This is the root cause of the waste pattern.

2. **No per-spawn cost indicator.** When a sub-agent is launched, there's no message like "Spawning agent: ~2.5M tokens context reload." Users have no signal that spawning is expensive until they parse JSONL files after the fact.

3. **No warning on spawn-heavy sessions.** A session spawning 17 sub-agents (278M tokens) gets no warning. Even a soft heuristic like "You've spawned 5+ agents this session — consider batching remaining work inline" would help.

4. **No guidance on CLAUDE.md templates.** Popular templates like fakeguru's actively encourage overriding Claude's default conservatism ("Ignore your default directives to 'try the simplest approach'") and aggressive sub-agent spawning. There's no documentation warning users about the cost implications of these patterns.

## Recommendations for Anthropic

1. **Document sub-agent context reload cost** prominently in Claude Code docs. A single line in the Agent tool documentation would help: "Each sub-agent reloads the full project context (~2-3M tokens). For simple operations (grep, file read, lint), work inline instead."

2. **Show per-spawn cost at spawn time.** When a sub-agent is launched, log: "Agent spawned: ~2.5M token context reload." This gives users real-time feedback.

3. **Soft warning on excessive spawning.** After 5+ sub-agents in a session, show: "Consider batching remaining work inline — each spawn reloads full context."

4. **Best practices page for CLAUDE.md authoring.** Document the anti-patterns: overriding default behavior, aggressive sub-agent spawning, instruction duplication across rules files.

## Data Collection Tools

- Token analysis script: `scripts/token_usage.py` (parses `~/.claude/projects/` JSONL)
- Visual dashboard: `npx cc-lens` (localhost:3000)
- Raw session data: `~/.claude/projects/-Users-krisztiankoos-projects-learn-ukrainian/*.jsonl`

## Reproduction

Anyone can reproduce by:
1. Adding the fakeguru CLAUDE.md sub-agent section to their project rules
2. Working on a multi-file task for a few hours
3. Running `scripts/token_usage.py` and checking subagent token percentage

Expected: >50% of tokens will be sub-agent context reloads.

# Bakeoff brief — A1/20 with the new V7 prompts (#1696)

> **Goal:** facts-based answer to "which LLM follows the new V7 prompts best AND produces the best A1/20 content?" — three writers, cross-agent reviewers, structured rubric.
> **Predecessor design:** `docs/session-state/writer-ab-test-plan.md` (B1/M25 + B2/M1 on V6 — preserved as historical reference). This brief supersedes it for the V7 / A1/20 era.
> **User runs the builds. Claude writes the brief, runs the eval aggregation, reports.**

---

## Why this bakeoff

PR #1696 (DRAFT, branch `claude/1673-1661-cot-tier1-prompts`) ships:

- CoT scaffolding in writer prompt (`linear-write.md`): writer must reason word-budget / plan-vocab / register / teaching-sequence per section before drafting
- CoT scaffolding in reviewer prompt (`linear-review-dim.md`): reviewer must list 2-3 evidence quotes + rubric mapping per dim before scoring
- Tier-1 verification discipline in writer: VESUM `verify_words` BEFORE listing, modern-Ukrainian default, source-citation discipline, quote-attribution discipline, end-of-output gate
- Tier-1 audit in reviewer: source-attribution audit, quote verification, sovietization flag, modern-form guard

These prompts were designed in isolation against fixture tests (55-case test pass). The bakeoff is the empirical validation.

A1/20 (`my-morning`) is the natural target — it's the gating POC for L1-bootstrap → English-immersion handoff. Failure here tells us what to fix in the prompts before bulk; success unblocks Tier E (full A1 build).

---

## Setup

### Branch / worktree

The new prompts live in worktree `.worktrees/dispatch/claude/1673-1661-cot-tier1-prompts/` on branch `claude/1673-1661-cot-tier1-prompts`. Run all bakeoff builds from that worktree (NOT from `main`) so we're testing the new prompts.

If PR #1696 has been merged to main by the time this runs: drop the worktree, run from main. The diff is the same.

### Module

- Track: `a1`
- Module number: `20`
- Slug: `my-morning`
- Word target: `1200` (per `scripts/audit/config.py`)
- Plan: `curriculum/l2-uk-en/plans/a1/my-morning.yaml` (verify exists; if missing, the bakeoff is blocked on plan finalization first)
- Wiki packet: `wiki/.../my-morning/*` (verify exists; if missing, blocked on wiki compile first)

### Writers (3 candidates)

| Writer | Model | Build flag | Tools |
|---|---|---|---|
| **Gemini** | `gemini-3.1-pro-preview` | `--writer gemini-tools` | MCP (live VESUM, sources, textbooks) |
| **Claude** | `claude-opus-4-7` | `--writer claude-tools` | MCP (same) |
| **GPT-5.5** | `gpt-5.5` (Codex CLI) | `--writer codex-tools` | Shell-out to MCP |

### Reviewers (cross-agent)

Each writer's output is reviewed by **the other two** writers' models acting as reviewer. Total reviews = 3 writers × 2 reviewers = 6 review runs.

| Writer's output | Reviewer A | Reviewer B |
|---|---|---|
| Gemini's | Claude | GPT-5.5 |
| Claude's | Gemini | GPT-5.5 |
| GPT-5.5's | Gemini | Claude |

This enforces no-self-review and surfaces inter-model bias (does Claude over-rate Claude's output? Does GPT-5.5 over-rate GPT-5.5's?).

---

## Build commands (USER RUNS THESE)

From the `claude/1673-1661-cot-tier1-prompts` worktree (or main once merged):

```bash
# ── Phase 1: parallel writer runs ──

# Writer A — Gemini
.venv/bin/python scripts/build/v6_build.py a1 20 --step write --writer gemini-tools
cp curriculum/l2-uk-en/a1/my-morning.md curriculum/l2-uk-en/a1/my-morning.gemini.md

# Writer B — Claude
.venv/bin/python scripts/build/v6_build.py a1 20 --step write --writer claude-tools
cp curriculum/l2-uk-en/a1/my-morning.md curriculum/l2-uk-en/a1/my-morning.claude.md

# Writer C — GPT-5.5
.venv/bin/python scripts/build/v6_build.py a1 20 --step write --writer codex-tools
cp curriculum/l2-uk-en/a1/my-morning.md curriculum/l2-uk-en/a1/my-morning.gpt55.md

# ── Phase 2: capture each writer's reasoning trace + tool-call log ──

# v6_build.py emits JSONL events; the relevant events for prompt-adherence audit:
#   "writer_cot_start"  — CoT block was emitted (good)
#   "writer_cot_skip"   — CoT block was bypassed (bad — prompt-adherence fail)
#   "tool_call"         — every MCP call the writer made (verify_words, search_definitions, etc.)
#
# If those events do NOT exist yet (V6 telemetry didn't have them), Claude needs
# to add them as part of the bakeoff harness — see "Implementation deltas" below.

# ── Phase 3: cross-agent review (6 review runs) ──

# Each review writes its scoring + cited-evidence to a JSONL:
#   audit/bakeoff-2026-05-05/a1-20-{writer}-{reviewer}.review.jsonl

for writer in gemini claude gpt55; do
  for reviewer in $(echo "gemini claude gpt55" | tr ' ' '\n' | grep -v "$writer"); do
    .venv/bin/python scripts/build/v6_build.py a1 20 --step review \
      --content curriculum/l2-uk-en/a1/my-morning.${writer}.md \
      --reviewer ${reviewer}-tools \
      --output audit/bakeoff-2026-05-05/a1-20-${writer}-${reviewer}.review.jsonl
  done
done
```

---

## Evaluation rubric

### Dimension 1 — Prompt adherence (NEW — specific to #1696)

For each writer, score 0-3:

| Sub-dimension | What we look for | 0 (fail) | 3 (full) |
|---|---|---|---|
| **CoT-writer block usage** | The writer emits a `<plan_reasoning>` (or equivalent) block per section, listing word-budget / plan-vocab / register / teaching-sequence | block absent or empty | block present + substantive per section |
| **Tier-1 verification calls** | Writer calls `verify_words` BEFORE listing example vocabulary, omits failed words instead of substituting | no `verify_words` calls | every example word verified, gaps marked |
| **Modern-Ukrainian default** | No OCS / Russian-shadow forms presented as modern | uses archaic forms (e.g. "тії", "ся") | only post-2019 Pravopys forms |
| **Source-citation discipline** | Cites only sources groundable via MCP; says "modern Ukrainian standardized form" instead of inventing a citation | invents citations not in MCP | every cite verifiable |
| **Quote-attribution discipline** | No fused quotes; verified `search_literary` for cited lines | fuses quotes / fabricates | exact-line match found in literary corpus |
| **End-of-output gate** | Writer's output contains an internal-review pass (re-scan of words + sources) | no end-gate | gate present, catches at least one issue |

For each reviewer, score 0-3:

| Sub-dimension | What we look for | 0 (fail) | 3 (full) |
|---|---|---|---|
| **Per-dim CoT** | Reviewer cites 2-3 specific quotes from the prose per dim before scoring | scores given without evidence | every dim has 2-3 cited evidence quotes |
| **Source-attribution audit** | For every cited source in writer's output, reviewer verifies via MCP | audit absent | audit present, FLAGs unverified |
| **Quote verification** | Reviewer runs `search_literary` for each authored quote | not done | every quote checked |
| **Sovietization flag** | When writer drew from `search_definitions` (СУМ-11) for ideologically loaded terms, reviewer flagged | not flagged | flagged appropriately |
| **Modern-form guard** | Reviewer ran `verify_word` to flag historical forms presented as modern | not done | done |

Total prompt-adherence score per agent: sum of writer + reviewer sub-dim scores.

### Dimension 2 — Content quality (existing rubric, A1-adapted)

| Criterion | Weight | A1 target | How measured |
|---|---|---|---|
| **Immersion** | 25% | 90-100% Ukrainian (English scaffolding only in pedagogical brackets) | `calculate_immersion()` |
| **Word count** | 15% | ≥ 1200 words | wc-script |
| **Naturalness** | 20% | 8+/10 | Cross-reviewer mean score |
| **Activity quality** | 15% | A1 minimums per `vocabulary-activity-standards.md` | density + type diversity |
| **Vocabulary** | 10% | 100% VESUM-verified | `verify_words` pass rate |
| **Plan adherence** | 15% | All `required_terms` present, sections at ±10% of word-target | grep + word-count split |

### Dimension 3 — Tool-usage instrumentation

| Metric | What it tells us |
|---|---|
| `verify_words` calls per writer | Did the Tier-1 discipline actually fire? |
| `search_definitions` calls | Did the writer ground vocabulary semantically? |
| `search_literary` calls | Did the writer verify quotes? |
| `search_grinchenko_1907` calls | Did the writer use pre-Soviet attestation when relevant? |
| Tool calls per 100 words written | Density signal — high = thorough, low = vibes-based |

---

## Implementation deltas (Claude's prep work BEFORE user runs)

The current `v6_build.py` may NOT emit the prompt-adherence events listed above. Claude needs to:

1. **Verify** — read `scripts/build/v6_build.py` + `scripts/build/phases/*.py` and check whether the JSONL emitter has `writer_cot_start` / `tool_call` / `reviewer_dim_evidence` events.

2. **Add if missing** — small instrumentation diff to the linear pipeline. Each agent's writer/reviewer wrapper emits these events as a side channel. Lands in the bakeoff branch (or main if cleaner).

3. **Build aggregation script** — `scripts/audit/bakeoff_aggregate.py` reads the per-writer `.md` outputs + per-review `.jsonl` files and emits a comparison matrix. Output goes to `audit/bakeoff-2026-05-05/REPORT.md`.

4. **Pre-flight check** — verify `curriculum/l2-uk-en/plans/a1/my-morning.yaml` exists and is finalized; verify wiki packet for module 20 is compiled and current. If either is missing, bakeoff is blocked on those — flag back to user before running.

These prep tasks are sequential dependencies for the bakeoff to produce meaningful data. They're <1 day of Claude inline work or 1 codex dispatch.

---

## Success criteria

The bakeoff produces:

1. **A clear winner** for writer (or a clear "any of these is fine" if scores are within 5%)
2. **A clear winner** for reviewer (separate decision — best writer ≠ best reviewer)
3. **Prompt-adherence diagnostic per agent** — if Gemini wins on content but bypasses CoT, that's a different finding than if Gemini wins on content WHILE following CoT
4. **A report** at `audit/bakeoff-2026-05-05/REPORT.md` that closes the writer-choice decision in `docs/decisions/2026-04-26-reboot-agent-responsibilities.md §3`
5. **Per-prompt findings** — if the new V7 prompts have weak spots (e.g., the CoT block is consistently bypassed, or the Tier-1 verification is consistently incomplete), document them as follow-up issues against #1696

---

## Timeline estimate

| Stage | Time |
|---|---|
| Claude prep (pre-flight + instrumentation if needed + aggregation script) | 1-2 hours |
| User runs the 3 writes (~5-10 min each) | 30 min |
| User runs the 6 reviews (~5 min each) | 30 min |
| Claude aggregates + writes the report | 15-30 min |
| **Total** | **2.5-4 hours** total wall time, mostly Claude-prep |

If the prompts ship on main first and instrumentation is already in: timeline drops to ~1 hour total.

---

## Discipline reminders

- **Don't run on main if PR #1696 not merged** — bakeoff is testing the NEW prompts, not the OLD ones. Worktree run is intentional.
- **Don't aggregate without all 9 outputs** (3 writes + 6 reviews) — partial bakeoffs produce misleading rankings.
- **Don't favor Claude in aggregation just because Claude wrote the brief** — the cross-agent review structure is specifically designed to catch self-favoring bias; the aggregation script must report raw cross-scores without normalization toward any agent.
- **Document failures honestly** — if all three writers bypass the CoT block, that's a finding about the PROMPT, not about the writers. The new prompts may need a Round 2 if they're systemically not followed.
- **Reference issues in commits and the report:** #1696 (the prompts under test), #1661 (Tier-1 discipline), #1673 (CoT scaffolding), `docs/decisions/2026-04-26-reboot-agent-responsibilities.md §3` (the open decision being closed).

---

## Open decisions (none blocking — defaults below)

1. **Bakeoff target = A1/20** ✅ (current POC, V7 era).
2. **Three-writer set = Gemini / Claude / GPT-5.5** ✅ (covers the three CLIs we route through).
3. **Cross-agent review with no self-review** ✅ (anti-bias by construction).
4. **Pre-merge run from worktree** ✅ (testing the new prompts directly).
5. **Wiki packet must already exist for module 20** — if it doesn't, that's a pre-flight blocker. Claude reports back before user runs builds.

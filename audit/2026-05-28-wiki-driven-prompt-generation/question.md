# Wiki-Driven Prompt Generation — Architecture Question

## State of the project

The static writer-prompt template (`scripts/build/phases/linear-write.md`, 550 lines, 49KB) has accumulated m20-specific lesson content over weeks of iteration on a single module. Today's audit found:

- 5 mentions of `прокидаюся` (m20's signature verb)
- 3 mentions of `Захарійчук` (m20's textbook source)
- An entire paragraph citing `m20 round #12, codex-tools, a1-my-morning-20260526-204640, PR #2358, decolonization 8.7 score` as build-history-as-prompt-content
- Example JSON activity using `прокидаюся` as the answer
- Concrete textbook chunk_id `1-klas-bukvar-zaharijchuk-2025-1_s0024` as the canonical citation example

This is genuine contamination. Future a1/m21 (or any other A1 module) generates under this template gets pushed toward morning-routine vocabulary, the wrong textbook citation shape, and m20's decolonization contrast pair.

The contamination is structural: any static-template + iterative-tuning system accumulates per-instance bias over time. We've seen the "gate-vs-prompt drift" pattern cited 4 times in this session's handoffs alone.

## The proposal

Replace static writer + reviewer prompts with **prompt generation at lesson-build time**:

```
INPUTS:
  - universal_rules.md       (~100-200 lines, level-conditional sections, decolonization stance, VESUM/Russianism bans, schema invariants, anti-AI-slop, voice/register rules, gate definitions)
  - wiki/pedagogy/{level}/{slug}.md   (per-lesson teaching brief: methodology, sequence steps, L2 errors, decolonization pairs, vocabulary minimum)
  - plan.references RAG chunks (textbook excerpts, dictionary entries, source materials the writer is asked to ground in)

GENERATOR (deterministic, no LLM):
  - Pick universal sections that apply to this CEFR level / track / activity profile
  - Inline the wiki's teaching brief
  - Inline the RAG content with explicit per-chunk verification obligations
  - Produce: writer_prompt.md + reviewer_prompt.md, both anchored to the SAME inputs

OUTPUTS:
  - writer_prompt.md (per-lesson, lesson-aware, no m20-style contamination because there's no static template to contaminate)
  - reviewer_prompt.md (per-lesson, rubric directly tied to wiki obligations + RAG chunks the writer was asked to cite)
```

The reviewer can no longer miss what the writer was asked to do, because both are built from the same brief.

## Why this is being proposed now

1. Today's V7.1+codex build at `.worktrees/builds/a1-my-morning-20260528-122552` produced clean 1505-word A1 content with 25 codex tool calls / 12 distinct MCP tools. The writer behavior is strong under V7.1's "render the wiki" charter. The remaining blockers are gate-vs-prompt drift bugs (e.g., wiki_coverage_gate not recognizing V7.1 inline implementation_map tags) — exactly the class of bug this proposal eliminates.

2. The team converged on V7.1 over V8 in Pt 11 because V7.1 was 1-2 days vs V8's 2 weeks. V7.1 has shipped its prompt-side rules but the static template still accumulates contamination per-lesson. This proposal completes the move V7.1 deferred, with a tighter scope than the original V8 (no new renderer phase; just replace template+inject with universal+wiki+RAG → generated prompts).

3. The contamination problem is now empirically demonstrated, not theoretical.

## Concrete questions

**Q1 — Universal/per-lesson boundary.** What goes in `universal_rules.md` and what goes in the wiki? Examples:
- VESUM gate, Russianism ban → universal (always true)
- "No children-primary blockquotes" → universal but A1/A2-conditional
- "Include one bad-form contrast pair from the lesson's domain" → universal rule, but the contrast pair itself comes from the wiki
- "Use the S1-S6 ULP scaffolding" → universal but A1/A2-conditional
- "Cover the 5 sequence steps in §Послідовність введення" → wiki-derived (the 5 steps ARE the wiki content)
- "Cite Захарійчук Grade 1 p.24" → wiki+plan-derived (per-lesson RAG references)

Is the universal/wiki split clean enough to implement, or are there cases that genuinely span both and need explicit composition logic?

**Q2 — Reviewer rubric specificity.** Today's reviewer scores on 9 universal dimensions (pedagogical, naturalness, engagement, decolonization, tone, etc.) with `terminal_verdict` driven by decolonization only. Under wiki-driven prompts, the reviewer rubric becomes much more specific per-lesson (did the writer cite chunk X? did the writer cover sequence step 4?). Is the right move:
   (a) Keep universal dimensions + ADD wiki-derived per-lesson checks (broader rubric)?
   (b) Replace universal dimensions with wiki-derived deterministic checks (sharper rubric)?
   (c) Hybrid — universal subjective dimensions for prose quality, wiki-derived deterministic for content coverage?

**Q3 — Generator implementation.** Should the generator be:
   (a) Pure Python (deterministic, no LLM, like the current template renderer but smarter — picks sections by metadata, inlines wiki/RAG)
   (b) LLM-driven (a separate Gemini phase that reads universal + wiki + RAG and writes the writer prompt + reviewer prompt — risk: hallucination, drift)
   (c) Python skeleton + LLM polish (deterministic structure, LLM fills in lesson-specific guidance text)

**Q4 — Implementation cost.** Is this a 1-week project or a 2-week project? What's the riskiest sub-task?

## Voting options (pick ONE; you can override under "Other")

**A.** Yes, build the wiki-driven prompt generator. Ship today's m20 artifact first (the cleanup is independent). Start design tomorrow. Pilot on a1/m21+m22 by end of week.

**B.** Yes in principle, but not now. Ship m20 first, then clean m20 contamination from `linear-write.md` as immediate follow-up, defer the generator to after A1 is half-built (more empirical data on contamination patterns).

**C.** No — stay with the static template + lesson-injection model. Add a regression test that fails the build if rendered prompt contains lesson-specific tokens not in the current lesson's inputs. That's a 1-hour fix vs 1-2 weeks of generator work.

**D.** Different direction (specify in your response).

## Context for new arrivals

- Pt 11 ADR-draft at `docs/decisions/pending/2026-05-27-v8-wiki-driven-writer.md` (NOT on main) discussed V8 = new renderer phase; team converged on V7.1 as cheaper.
- V7.1 Day 1 PR #2377 + Day 2 PR #2379 shipped; V7.1+codex pilot today produced clean writer output blocked only by gate-vs-prompt drift.
- Today's R1+R2 fix PR #2382 (merged) addressed silent pipeline exit + translate schema directive.
- m20 baseline artifact at `.worktrees/builds/a1-my-morning-20260528-122552/curriculum/l2-uk-en/a1/my-morning/module.md` (1505 words, all python_qg green, wiki_completeness PASS, 25 codex tool calls / 12 distinct MCP tools).
- User's framing (which improved on my initial 3-layer proposal): "we have universal rules plus the wiki of the module, plus the related RAG content and we could use those to generate the writer and reviewer prompt."

## Voting protocol

Use `[VOTE: A]` / `[VOTE: B]` / `[VOTE: C]` / `[VOTE: D]` at the end of your response. One vote per round. Substantive reasoning required for any vote — explain your read on Q1-Q4 in the body.

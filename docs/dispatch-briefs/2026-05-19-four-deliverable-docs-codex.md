# Dispatch Brief — 4 deliverable documentation files (Codex)

**Filed:** 2026-05-19
**Owner:** Codex (`gpt-5.5`, `xhigh`)
**Scope:** Doc-writing only. No code changes. Single PR with 4 new files.
**Trigger:** `audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md` §1.1, §1.2, §1.8, §1.9 — four specification gaps surfaced by the 2026-05-18 gap audit, each currently unwritten despite being decided.
**Predecessor work already shipped this morning (do NOT redo):**

- `docs/decisions/pending/2026-05-18-wiki-obligation-emission-contract.md` (P0 — gap §1.4)
- `docs/decisions/2026-05-18-deterministic-first-iteration.md` (P1 — gap §1.5)
- `docs/north-star.md` v3 → v3.1 (gap §1.3 — ULP-derived immersion)
- `docs/best-practices/agent-activity-matrix.md` §8.11 (gap §1.10 — track-level writer routing stubs)

This brief covers the **remaining 4 gaps** the orchestrator chose not to write inline.

---

## The 4 deliverables (one PR, all 4 files)

### File 1 — `docs/best-practices/pipeline/v7-build-preservation.md` (gap §1.1, P0)

**The spec is fully locked in the handoff.** Read `docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md` § "Architecture decisions LOCKED this session → V7 orchestration folder preservation". That section IS the design — your job is to canonicalize it into a best-practices doc, not redesign.

**Required sections:**

1. **Scope** — what V7 build artifacts get preserved and where. Path: `curriculum/l2-uk-en/_orchestration/{level}/{slug}/runs/{stamp}/`. Underscore prefix to keep out of `mcp__sources__*` retrieval namespace.
2. **Build flow** — quote verbatim from the handoff (worktree isolation; wrapper copies on phase boundary + terminal outcome; always merge to main; one commit per build; worktree reaped on completion).
3. **`state.json` schema (V7)** — quote the JSON schema verbatim from the handoff (`mode: "v7"`, `track`, `slug`, `run_id`, `parent_run_id`, `started_at`, `finished_at`, `status`, `failed_phase`, `failure_class`, `agent`, `model`, `effort`, `prompt_sha`, `phases` block).
4. **File naming convention** — hyphenated (`v7-writer-prompt.md`, not `writer_prompt.md` per codex's catch — `*_PROMPT.md` is gitignored).
5. **MDX-on-failure policy** — ALWAYS assemble MDX regardless of gate pass/fail. Success → `starlight/src/content/docs/{level}/{slug}.mdx`. Failure → `_orchestration/.../runs/{stamp}/{slug}.mdx` with `build_status: failed` + `failed_phase: <phase>` frontmatter. NEVER modify the source `module.md` frontmatter (gate-consumed; parser risk).
6. **Auto-generated artifacts** — `commit_diff_summary.json` per build (`git diff --stat` parsing, ~30 LOC). Document expected shape.
7. **Correction iterations preserved** — `python_qg_correction_r{N}.json`, `wiki_coverage_correction_r{N}.json`. Currently swallowed; this is the prompt-engineering blind spot the spec closes.
8. **Per-dim reviewer prompts** — preserved as separate files, not aggregated into `llm_qg.json`.
9. **Cleanup policy** — last N=10 runs per slug; older runs squashed/deleted via scheduled cron (defer cron details to month 3 — document the intent, leave implementation deferred).
10. **Open implementation status** — what's already shipped vs pending. Cross-link `scripts/build/v7_build.py --worktree` (PR #1952, shipped) as the worktree-isolation piece that's live today; preservation/copy-on-phase-boundary is NOT yet shipped.

**Verbatim sources you must quote (with tool evidence per #M-4):**

- The full block from the 2026-05-19 handoff under "V7 orchestration folder preservation (full plan)"
- The `state.json` schema as written in that handoff
- The MDX-on-failure policy as written there

**What NOT to invent:** specific cleanup-cron implementation; specific phase list (defer to v7-pipeline.md doc — File 3). Cross-link instead.

---

### File 2 — `docs/best-practices/pipeline/writer-bakeoff-methodology.md` (gap §1.2, P1)

**Scope:** the methodology spec for running fair multi-writer bakeoffs on the V7 pipeline. The audit (`audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md` §1.2) notes the existing `docs/best-practices/agent-activity-matrix.md` has a *table of past bakeoff outcomes* but **no methodology spec**.

**Required sections:**

1. **Why this doc exists** — link to past bakeoffs that ran without a written methodology, surface the gap.
2. **What a fair test requires** — same prompt, same module, same MCP config, same effort tier, separate worktrees per writer, deterministic prompt-fidelity scoring.
3. **Per-level scope rule** — A1 results do NOT transfer to B1+ (register inverts). Per-level bakeoff is the default; a single A1 bakeoff does not license a B1+ ranking.
4. **Writer roster** (current as of 2026-05-19): claude-tools, codex-tools, gemini-tools, deepseek-tools (PENDING wiring — see task #5), kimi (EXCLUDED per user direction 2026-05-18), qwen-tools (3.6-plus default; 3.6-flash, 3.6-max-preview, 3.6-35b-a3b:thinking variants), grok-tools (known weak per #2039).
5. **Measurement schema (the deterministic prompt-fidelity rubric)** — quote verbatim from the 2026-05-19 handoff "Bakeoff plan for next session → Prompt-fidelity rubric":
   - Word count within ±50 of target
   - All 4 sections in band
   - Lands within derived immersion band (`compute_immersion_band()`)
   - ≥4 MCP tool calls
   - VESUM 100% (no invented forms)
   - `unknown_vocabulary` gate: 0 violations
   - `<!-- bad -->` marker discipline: 100%
   - Implementation map completeness: 100%
6. **Cost normalization** — per-passing-module $. Bakeoff total = sum of per-writer module costs; quality verdict = first-pass pass-rate against the rubric. Do NOT count `correction_pass` iterations toward the first-pass score; track separately as a "correction-responsiveness" sub-score.
7. **Cost reality check** — quote verbatim from the handoff "Cost reality check" section: A1 m20 6-writer bakeoff ~$6-15 total; DeepSeek wiring dispatch ~$3-5; total to populate matrix §8.11 ~$50-80.
8. **When to bakeoff vs trust existing** — if a writer is `last_verified` > 60 days OR has never been tested in the target register (A1 precision vs B1+ register-relaxed vs seminar-narrative), bakeoff is required. Otherwise trust the matrix.
9. **Bakeoff lifecycle** — (a) dispatch all writers in parallel worktrees (within agent cap), (b) wait for all to finalize via Monitor on per-task JSONL, (c) score deterministically against rubric (NO LLM judge for the rubric — the rubric is deterministic), (d) write report at `audit/bakeoff-{date}-{scope}/REPORT.md`, (e) update matrix `last_verified` + `quality status` cells, (f) close the open eval row in §7 if applicable.
10. **Anti-patterns** — what makes a bakeoff *invalid* (different prompts, different MCP configs, different model_reasoning_effort settings, comparing pre- and post-bug-fix outputs as if equivalent, LLM-judge as primary verdict).

**Verbatim sources you must quote:**

- The prompt-fidelity rubric from the 2026-05-19 handoff
- The cost reality check from same handoff
- The agent-activity-matrix §8.1 + §8.10 + §8.11 rankings as the "current state" reference

**What NOT to invent:** an LLM-judge methodology (the rubric is deterministic by design). A bakeoff schedule (let the matrix's `last_verified` + the audit cadence drive). Specific config thresholds (those live in `scripts/audit/config.py` per existing convention).

---

### File 3 — `docs/architecture/v7-pipeline.md` (gap §1.8, P1)

**Scope:** the canonical prose spec of the V7 pipeline. Replaces `docs/architecture/ARCHITECTURE.md` (which is marked legacy V5/V6 at its own line 5). Per the audit (§1.8): *"`scripts/build/v7_build.py --help` lists phases inline: plan → knowledge_packet → writer → python_qg → wiki_coverage_gate → wiki_coverage_review → llm_qg → mdx. No prose spec."*

**Required sections:**

1. **Status banner** — supersedes `docs/architecture/ARCHITECTURE.md` (mark that file as `_legacy/` candidate; this doc is current).
2. **One-line V7 elevator pitch** — single-module linear pipeline; worktree-isolated; deterministic gates first, LLM review last; honest plan_revision_request terminals over thrashing.
3. **Phase-by-phase spec** — read `scripts/build/v7_build.py` directly to enumerate the 8 phases and quote their actual order from `_PIPELINE_PHASES` or equivalent. For each phase, document:
   - **Purpose** — one sentence
   - **Inputs** — file paths consumed
   - **Outputs** — file paths written
   - **Failure modes** — what makes this phase fail
   - **Correction path** — link to `2026-05-18-deterministic-first-iteration.md` L1-L7 layer that handles this phase's failures
4. **V6→V7 deltas** — the audit notes this is undocumented. Read `scripts/build/v6_build.py` (legacy) head + `scripts/build/v7_build.py` head and document what V7 dropped (skeleton phase, chunked write, etc.) and why. If this archaeology is too expensive, document it as a TODO rather than fabricate.
5. **State files emitted per phase** — cross-link `docs/best-practices/pipeline/v7-build-preservation.md` (File 1 above) for the canonical state.json schema.
6. **Worktree isolation requirement** — `--worktree` flag must be passed for agent-run builds (PR #1952 enforces). Cross-link `docs/best-practices/git-hygiene.md` if it covers this.
7. **Writer / reviewer family routing** — cross-link matrix §8.1 + §8.2 rather than restate.
8. **What V7 is NOT** — explicit anti-list: not a multi-module batch (deferred until single-module is locked); not a parallel-build pipeline (worktree isolation is per-module); does not include wiki compilation (that's a separate pipeline at `scripts/wiki/`).
9. **References** — cross-link the relevant decisions: ADR-007, ADR-008, Path 3, ULP-immersion, this morning's deterministic-first synthesis.

**Verbatim sources you must read with tool evidence per #M-4:**

- `scripts/build/v7_build.py` (head + `_PIPELINE_PHASES` constant if present, or equivalent)
- `scripts/build/linear_pipeline.py` (head + entry-point + phase dispatcher)
- `ls scripts/build/phases/` to enumerate phase prompt files
- `docs/architecture/ARCHITECTURE.md:1-30` to quote its legacy banner

**What NOT to invent:** phase names not in `v7_build.py`. Phase ordering not visible in code. Internal data shapes not present in the running pipeline. If the code is ambiguous, document the ambiguity, do not paper over it.

---

### File 4 — `docs/plans/2026-06-15-claude-dispatch-sunset.md` (gap §1.9, P1)

**Scope:** the transition plan for the 2026-06-15 hard rule *"NO `delegate.py --agent claude`"* (per MEMORY.md #M0 + audit §1.9). Date is ~4 weeks out; this plan must be actionable before then.

**Required sections:**

1. **The hard rule** — quote verbatim from MEMORY.md #M0 and from `scripts/config/agent_fallback_substitutions.yaml` `post_2026_06_15_hard_rule` block.
2. **What changes on 2026-06-15** — no orchestrator-fired `delegate.py --agent claude` invocations. The $200/mo agentic credit pool is RESERVED for user's cold-start review sessions, not orchestrator dispatches. NO OVERAGE.
3. **Enumeration of every current Claude-dispatch call site** — read `scripts/config/agent_fallback_substitutions.yaml` for the surface list, but ALSO grep the codebase for every `delegate.py.*--agent claude` invocation in scripts, docs, and dispatch briefs. Cross-reference with `claude_extensions/agents/` + `claude_extensions/rules/model-assignment.md`. For each call site, document:
   - **Where** — file:line
   - **Today's use** — what the dispatch does
   - **Post-June-15 substitute** — pull from the fallback substitution map
   - **Verified or pending** — has the substitute been empirically tested in this role?
4. **The substitution chain** — quote `agent_fallback_substitutions.yaml` verbatim as the canonical mapping.
5. **Pre-cutover verification checklist** — for every substitute that's "pending" in §3, schedule a verification dispatch BEFORE 2026-06-15 so we know it works. Order by call-site frequency / load-bearing-ness.
6. **The V7 writer special case** — `claude-tools` is the current V7 writer (per `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md` REVISED 2026-05-12 night). Post-June-15 alternatives in priority order: codex-tools (register-tuned settings TBD), deepseek-tools (PENDING wiring per matrix §8.1), gemini-tools (re-bakeoff per matrix §8.1). Cite the 2026-05-19 handoff "Strategy direction" subsection for the user-corrected sequence.
7. **Post-cutover fallback if no writer alternative passes A1 quality bar** — what to do if A1 m20 6-writer bakeoff finds nothing matches claude-tools at A1 register. Three options: (a) ship the next-best writer with explicit quality caveat per #1, (b) keep claude-tools for A1 by extending the user's own cold-start sessions to writer dispatches (NO — user direction excludes this), (c) pause A1 module production and ship A2+ tracks first (where claude-tools is less load-bearing per matrix §8.11). Recommend (c) by default; (a) only if user explicitly accepts the quality caveat.
8. **What ALSO needs to change** — SDK Adoption Decision Card (`docs/decisions/pending/2026-05-14-agent-sdk-adoption.md`) — the efficiency premise was on programmatic pool that we're now not using post-June-15. RECONSIDER, not auto-deny.
9. **Calendar** — 4 weeks from 2026-05-18. Per-week milestones: week 1 = enumerate + queue verification dispatches; week 2 = run verifications; week 3 = update routing rules + tests; week 4 = freeze, dry-run, document lessons; June 15 = cutover.
10. **Open questions for user** — single explicit list at the end with the 1-3 things that genuinely need user input before this can be finalized.

**Verbatim sources you must quote:**

- MEMORY.md #M0 `post_2026_06_15` paragraph
- `scripts/config/agent_fallback_substitutions.yaml` entire file
- The agent-activity-matrix §2 Claude row for the credit-pool framing

**What NOT to invent:** new substitution paths not in the YAML. New deadlines. Empirical quality claims about substitutes that haven't been bakeoffed (mark all such claims `❓ pending verification`).

---

## Cross-cutting requirements (apply to ALL 4 files)

### #M-4 deterministic-over-hallucination

Every verifiable claim in these docs must be backed by a tool call you ran in this dispatch. Specifically forbidden:

- Quoting a "current LOC count" without `wc -l` evidence
- Citing a file:line without `grep -n` evidence
- Citing a PR number without `gh pr view N` evidence
- Citing a commit SHA without `git log --oneline` evidence
- Citing a config value without `grep` or `Read` on the actual config file

When you quote a path or schema, include the cwd you ran the verifier in. Per the goal-driven runs rule: command + cwd + raw output line, as a triple.

### Style + voice

- Match the existing best-practices/decisions/architecture docs in tone — direct, no hedging, no marketing language.
- Use the same section-heading style as existing docs in each respective directory.
- Cross-link liberally with relative paths. Every claim that has a doc home should link there.
- No "in this section we will" preambles. Get to the substance.

### Section length budgets

- File 1 (v7-build-preservation): ~400-700 lines. The handoff's design block is dense; canonicalize without diluting.
- File 2 (writer-bakeoff-methodology): ~300-500 lines.
- File 3 (v7-pipeline): ~500-800 lines. Phase-by-phase spec is the bulk.
- File 4 (claude-dispatch-sunset): ~400-600 lines. Enumeration is the bulk.

Hard ceiling per file: 1000 lines. If you're trending past 800, reconsider whether content belongs in this doc or in a cross-linked companion.

### Forbidden content (apply globally)

- No emoji (per project convention; user explicit).
- No "In conclusion" / "It's important to note" / "Let's dive in" / "Buckle up" / "Great job!" — these are caught by the AI-slop banlist.
- No invented thresholds (numbers live in `scripts/config.py` or `scripts/audit/config.py`; docs point at those, do not duplicate).
- No HTML companion files — these are ai → ai docs per MEMORY #M-2. MD only.

---

## Dispatch shape

### Pre-submit checklist (MANDATORY — AGENTS.md:11-26)

1. `git worktree add .worktrees/dispatch/codex/four-deliverable-docs-2026-05-19 -b codex/four-deliverable-docs-2026-05-19`
2. File-level work: 4 new files at the paths above
3. **Tests:** none required (docs-only PR); but if you change `scripts/` for any reason, run `.venv/bin/python -m pytest tests/` against the affected scope
4. Ruff: `.venv/bin/ruff check` if you touch any Python (you should not for this PR)
5. Commit: conventional message — `docs(specs): close gap audit §1.1, §1.2, §1.8, §1.9 — v7 preservation + bakeoff methodology + v7-pipeline spec + claude-dispatch-sunset plan`
6. Push: `git push -u origin codex/four-deliverable-docs-2026-05-19`
7. PR: `gh pr create --title "docs(specs): 4 deliverable docs from gap audit §1.1/§1.2/§1.8/§1.9" --body "<comprehensive description with predicate evidence>"`. Mark as ready for review. **NO auto-merge** — the orchestrator reviews and merges.

### Verification preamble (#M-4)

In your PR body, include a section "Verification evidence" with at least one tool-output line for each verbatim claim:

- One `grep -n` line for each file:line citation
- One `gh pr view` line for each PR cited
- One `Read` excerpt for each YAML/JSON schema quoted
- One `git log` line for each SHA cited

Without this section the orchestrator will request changes before merge.

### Worktree isolation (NON-NEGOTIABLE — `claude_extensions/rules/delegate-must-use-worktree.md`)

All work happens inside the worktree path above. **DO NOT** `git checkout` or `git switch` in the main project directory. If you need to reference a file from main, `git show main:path/to/file` from inside the worktree.

### Cost budget

- Target: 1.5-3 hours of Codex `xhigh` time. Cap: 4 hours; if you trend past 4h, halt at the file you're on, push what's done, open a PR with a clear "halted at <step>" note in the body so the orchestrator can sequence the remaining work.
- The doc-writing task is bounded; do not expand scope. If you discover a real bug in the source material (e.g. a wrong file path in the handoff), file a separate GH issue but do not block this PR.

---

## After the PR opens

Orchestrator will:

1. Read each file end-to-end
2. Verify all `#M-4` claims have tool evidence
3. Verify cross-links land on real anchors
4. Approve + merge (or request changes if any of the above fail)
5. Update `audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md` to mark §1.1, §1.2, §1.8, §1.9 as RESOLVED

---

## Hard rules summary (quick reference for Codex)

- One PR, 4 new files at the specified paths
- All claims tool-backed (#M-4); evidence section in PR body
- Worktree isolation; commit on the branch above; no main-dir touches
- Pre-submit checklist before opening the PR
- No auto-merge; orchestrator reviews
- Halt and push if past 4h cap; do not silently expand scope
- Doc style matches existing best-practices/decisions/architecture conventions
- MD only — no HTML companion files

---

**End of brief.**

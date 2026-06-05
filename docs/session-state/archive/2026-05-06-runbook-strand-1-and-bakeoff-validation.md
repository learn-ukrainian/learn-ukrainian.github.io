# Runbook — Strand 1 + Bakeoff Validation (next-session play-by-play)

> **Predecessors:**
> - `2026-05-06-bakeoff-rerun-and-prompt-merges.md` (this run's foreground work)
> - `2026-05-05-bakeoff-execution-and-prompt-foundations.md` (Dispatch B + prompt strengthening)
>
> **Goal of next session:** ship strand 1 of #1720, re-run the bakeoff, interpret the result. If strand 1 + the re-run validate, we have the **first end-to-end-successful 3-way bakeoff** with real prompt-adherence + tool-grounding data. That's the gate to the writer-selection decision in `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §3.
>
> This is a **runbook**, not a "next steps" list. Execute it top to bottom. Each step has a verification gate. Don't skip; don't reorder.

---

## What's already in main (don't rebuild this)

- `f8bd113bca` — #1721: strand 2 (`<end_gate>` block mandate) + strand 3 (writer-correction single-fence contract + split-based parser)
- `6921e46bfe` — #1719: V7 prompt strengthening (visible `<plan_reasoning>`, per-dim `evidence_quotes`, heritage-MCP routing)
- `4e0934cc1d` — #1713: CodeQL cleanup + `os.path.commonpath` sanitizer
- `567ee66094` — #1717: slovnyk.me MCP tools (`search_heritage`, `search_slovnyk_me`)
- `76b561989a` — #1699: writer + reviewer JSONL telemetry instrumentation

The bakeoff harness is live and functional. The prompts are live and functional. Strand 1 is the last missing piece.

---

## Step 0 — Cold-start

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
source ./.envrc

curl -s http://localhost:8765/api/state/manifest
curl -s http://localhost:8765/api/orient
curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'

git fetch origin main && git pull --ff-only origin main && git status -s
git worktree list
```

**Verification gate:** main at `f453b8e332` or later, no commits ahead/behind, working tree clean of *your own* changes. The orphaned dirty-tree files from #1718 will still be present — leave them alone.

---

## Step 1 — Dispatch Codex to implement strand 1

### Brief content (write this to file, then dispatch)

Save to `docs/dispatch-briefs/2026-05-06-1720-strand-1-tool-theatre.md`:

```markdown
# Codex dispatch brief — #1720 strand 1 (tool-theatre detection)

> **Worktree:** `.worktrees/dispatch/codex/1720-strand-1`
> **Branch:** `codex/1720-strand-1`
> **Base:** `main`
> **Mode:** danger
> **Effort:** medium
> **Hard timeout:** 5400s (90 min)
> **Reviewer:** Claude (cross-family adversarial)

## Goal

The bakeoff at `audit/bakeoff-2026-05-05/` (run 2026-05-06 22:19 UTC, REPORT.md committed via #1720) showed all 3 writers cite MCP tools in `<plan_reasoning verification="...">` blocks WITHOUT actually calling those tools. `tool_calls_total = 0` for all writers despite explicit citations of `mcp__sources__verify_words`, `search_heritage`, etc. This is "CoT theatre" — visible reasoning that performs grounding without doing it.

Strands 2 and 3 of #1720 shipped in #1721 (`f8bd113bca`). Strand 1 is the last missing piece.

## Implementation

### Files to touch

- `scripts/build/linear_pipeline.py` — new `detect_tool_theatre()` function + wiring into `phase_writer_summary` emission + new `writer_tool_theatre` event + `tool_theatre` correction-pass dispatch.
- `scripts/build/phases/linear-write.md` — strengthen §Tier-1 bullet 5 to explicitly forbid citing tools you did not call.
- `scripts/build/phases/linear-writer-correction.md` — extend or add a parallel template for the `tool_theatre` gate (writer must either remove the false citations OR call the cited tools and re-emit).
- `tests/test_writer_correction_no_op_diagnostic.py` — add tool-theatre detection tests.
- `tests/test_prompt_cot_tier1_scaffolding.py` — lock in the new prompt rule.

### Function signature

```python
def detect_tool_theatre(
    writer_output: str,
    tool_calls: list[Mapping[str, Any]],
) -> list[str]:
    """Return the sorted list of tool names CITED in <plan_reasoning>
    verification text but not present in the actual tool_calls trace.

    A non-empty return = tool-theatre violation.

    Normalization: strip the `mcp__sources__` prefix on both sides
    before comparing. So `mcp__sources__verify_words` cited and
    `verify_words` called are treated as a match.
    """
```

### Plumbing

- Add a `_TOOL_CITATION_RE` that finds backtick-enclosed identifiers shaped like `mcp__sources__\w+`, `search_\w+`, `verify_\w+`, `check_\w+`, `query_\w+`, `translate_\w+` inside `<plan_reasoning ...>...</plan_reasoning>` blocks. Cross-reference against `_mapping_from_tool_call(tool_calls)` outputs.
- In `phase_writer_summary` emission (currently emitted around the same site as `writer_end_gate`), add a new field `tool_theatre_violations: list[str]`.
- When the list is non-empty, also emit a separate `writer_tool_theatre` JSONL event with `module`, `writer`, `violations`, and `cited_count` / `called_count`.
- Wire `tool_theatre` into `WRITER_CORRECTION_GATES` so the existing correction-loop infrastructure handles it. Treat it as module-only (not strict_json_parse) so the existing single-fence parser handles the response.

### Correction-pass behavior

The correction prompt for `tool_theatre` should give the writer a binary choice:
1. Call each cited tool you did not call, then re-emit module.md with the actual tool results in the verification block. Single-fence response.
2. Remove the false citations from the verification block. Single-fence response.

Verbatim citation: "every tool name you cite in `<plan_reasoning verification>` must correspond to a tool call you actually made in this turn's trace. Pick (1) call them now, or (2) remove the false citations. No third option."

### Prompt update (linear-write.md §Tier-1 bullet 5)

Add at the end:

> Every tool name cited in `<plan_reasoning verification>` MUST correspond to an actual tool call in this turn's trace. The pipeline cross-references citations against the trace and treats unmatched citations as a hard fail (`tool_theatre`). Citing a tool you did not call to satisfy the verification rubric — without doing the verification — is the canonical theatre failure.

### Risks to address before merging

1. **Tool-family overlap**: writer cites `search_heritage` but trace shows `search_grinchenko_1907` (which is what `search_heritage` wraps). Decide: define a small `_TOOL_FAMILY_MAP` so `search_heritage` is satisfied by any of `[search_heritage, search_grinchenko_1907, search_esum, search_slovnyk_me, search_style_guide]` — or require canonical-only and update the prompt to mandate the umbrella name. Recommended: canonical-only, simpler, harder-to-cheat. Document the choice.
2. **Capture completeness**: verify all 3 writer adapters (claude-tools, gemini-tools, codex-tools) emit tool-call traces in a shape `_mapping_from_tool_call` can read. Test by adding a `dry-run-trace` fixture per adapter and asserting the same trace shape.
3. **Backtick noise**: writer might wrap a tool name in regular prose backticks ("I would call `verify_words` here") without actually intending it as a citation. Constrain the citation extraction to the inside of `<plan_reasoning verification="...">` attribute or block body — not the whole writer output.

### Tests

- `test_detect_tool_theatre_returns_unmatched_citations` — cited tools not in trace are returned.
- `test_detect_tool_theatre_normalizes_mcp_prefix` — `mcp__sources__verify_words` cited, `verify_words` called → no violation.
- `test_detect_tool_theatre_empty_input` — empty trace and empty output return [].
- `test_detect_tool_theatre_only_scans_plan_reasoning_blocks` — backticks in module.md prose are NOT counted as citations.
- `test_writer_correction_handles_tool_theatre_gate` — single-fence response patches module.md and clears the gate.
- `test_writer_prompt_mandates_tool_call_match` — prompt scaffolding test for the new rule.

### Validation before opening PR

1. `pytest tests/test_writer_correction_no_op_diagnostic.py tests/test_prompt_template_render.py tests/test_prompt_cot_tier1_scaffolding.py tests/test_no_rewrite_contract.py` — must pass.
2. `git diff --check` clean.
3. Run a single-writer dry build to verify telemetry emits the new fields without crashing:
   `.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer claude-tools --dry-run`.

### Get Claude review

```bash
git -C .worktrees/dispatch/codex/1720-strand-1 diff origin/main..HEAD > /tmp/strand-1-diff.txt
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
  "Adversarial review for #1720 strand 1. Read /tmp/strand-1-diff.txt. Focus: (A) does _TOOL_CITATION_RE correctly scope to <plan_reasoning> blocks only and not catch backticks in module.md prose? (B) is the canonical-vs-family choice for tool-name normalization sound, or is _TOOL_FAMILY_MAP needed? (C) is the correction-pass binary choice (call-or-remove) prompted clearly enough that a writer won't pick a third path? (D) does the new tool_theatre gate enter the existing correction-loop without ordering bugs vs the existing word_count / plan_sections / mdx_render gates? (E) test gaps?" \
  --task-id 1720-strand-1-review
```

Apply feedback. Commit with `Reviewed-By: claude-opus-4-7 (1720-strand-1-review)` trailer.

### PR

Open as `feat(prompts): tool-theatre detection — cross-check plan_reasoning citations vs trace (#1720 strand 1)`. Constraint: NO auto-merge. Orchestrator (Claude) reviews CI + body, then merges.
```

### Dispatch command

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent codex \
    --task-id 1720-strand-1 \
    --worktree .worktrees/dispatch/codex/1720-strand-1 \
    --base main \
    --mode danger \
    --effort medium \
    --hard-timeout 5400 \
    --prompt-file docs/dispatch-briefs/2026-05-06-1720-strand-1-tool-theatre.md
```

**Verification gate:** dispatch returns exit 0, status `done`, worktree at `.worktrees/dispatch/codex/1720-strand-1` exists with branch `codex/1720-strand-1` ahead of main.

---

## Step 2 — Claude adversarial review of Codex's PR

This is **mandatory** per the workflow rule (step 6 of mandatory task workflow). Codex got Claude's review during the dispatch (per brief), but you (Claude) must also do an independent post-dispatch review on the PR diff.

```bash
PR_NUMBER=$(gh pr list --head codex/1720-strand-1 --json number --jq '.[0].number')
gh pr diff $PR_NUMBER > /tmp/strand-1-pr-diff.txt
```

Read `/tmp/strand-1-pr-diff.txt`. Check specifically:

1. **Citation extraction scope**: does the regex/parser only inspect `<plan_reasoning>` blocks, or does it accidentally see backticks in the artifact `module.md` body? A test like `"\`verify_words\` is the function" inside module.md prose` should NOT count as a citation.
2. **Tool-family normalization decision**: Codex was free to pick canonical-only OR a `_TOOL_FAMILY_MAP`. Whatever they chose, verify it's consistent and documented inline.
3. **Correction-pass loop behavior**: when the tool_theatre gate fails, does the correction prompt give the writer the binary choice cleanly? Is the writer's response handled by the existing module-only parser from #1721, or does it need its own?
4. **Telemetry shape**: new fields (`tool_theatre_violations`, `writer_tool_theatre` event) must NOT break the bakeoff aggregator at `scripts/audit/bakeoff_aggregate.py`. Run the aggregator against the prior run's JSONLs to confirm.
5. **Prompt scaffolding test**: does the new prompt mandate test (`test_writer_prompt_mandates_tool_call_match`) actually catch a regression where the rule is removed? Try mentally deleting the rule from the prompt — does the test fail?

If findings: comment on the PR with concrete fixes. If clean: approve and merge.

```bash
gh pr merge $PR_NUMBER --squash --delete-branch --admin
git fetch origin main && git pull --ff-only origin main
git worktree remove .worktrees/dispatch/codex/1720-strand-1 --force
git branch -D codex/1720-strand-1
```

**Verification gate:** main now has the strand-1 commit. `pytest tests/test_writer_correction_no_op_diagnostic.py tests/test_prompt_cot_tier1_scaffolding.py` passes from main checkout. CodeQL Analyze (python) is the only delayed check; ignore.

---

## Step 3 — Re-run the bakeoff

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent codex \
    --task-id bakeoff-validation-2026-05-06 \
    --worktree .worktrees/dispatch/codex/bakeoff-validation-2026-05-06 \
    --base main \
    --mode danger \
    --effort medium \
    --hard-timeout 7200 \
    --prompt-file docs/dispatch-briefs/2026-05-05-bakeoff-full-execute.md
```

The brief `2026-05-05-bakeoff-full-execute.md` is unchanged and still valid. It wipes `audit/bakeoff-2026-05-05/` per step 1. Expected runtime: 25-90 min (last run was 25 min).

While waiting:
```bash
.venv/bin/python scripts/delegate.py wait bakeoff-validation-2026-05-06 --timeout 7200
```

…in a background shell. Monitor task fires on completion.

**Verification gate:** worker exits 0. `audit/bakeoff-2026-05-05/REPORT.md` exists. Per-writer dirs (`claude/`, `gemini/`, `gpt55/`) exist with `module.md` (and the YAML artifacts). Six `*-*.review.jsonl` files exist (3 writers × 2 cross-reviewers).

---

## Step 4 — Interpret REPORT.md

Read `audit/bakeoff-2026-05-05/REPORT.md`. Three things to evaluate, in order:

### (a) Did the strand fixes hold?

| Strand | Acceptance | What to check |
|---|---|---|
| 2 (end-gate) | `gate_present=true` for ≥1 writer | `phase_writer_summary` events in each `*.write.jsonl` |
| 3 (correction-pass) | ≥1 writer publishes final `module.md` | Filesystem: per-writer dir contains `module.md` |
| 1 (tool-theatre) | `tool_theatre_violations: []` for ≥1 writer AND `tool_calls_total > 0` for that writer | `phase_writer_summary` |

If ALL three are green for ≥1 writer: **proceed to (b).**

If strand 1 is red but 2+3 green: writers still doing theatre even after the new gate. The correction-pass response is unparseable, OR the gate isn't triggering, OR the regex is missing citations. Diagnose with the JSONLs; file follow-up issue.

If strand 2 or 3 is red: regression. Open immediately, debug, cherry-pick fix.

### (b) Did cross-reviews actually score the work?

Read each `*-*.review.jsonl`. For each cross-review, check:
- The reviewer emitted a JSON response with `score`, `evidence_quotes` (3+), `rubric_mapping`, `verdict`.
- No `reviewer_fixes_unparseable` events.
- Scores per dim (immersion, word count, naturalness, activity quality, vocabulary, plan adherence) are populated.

If reviewer protocol is being followed: **first-ever validation that the V7 reviewer prompt works end-to-end.** Note this in the handoff.

### (c) Per-writer comparison + winner heuristic

REPORT.md aggregator already produces this table. Look at:
- `min dim` per writer (the strict-MIN gate from non-negotiable-rules.md §5)
- `weighted score` per writer
- Tool-call density per writer
- Wall time per writer

A "winner" emerges when one writer has min_dim ≥ 8 AND weighted_score ≥ 8.5 AND tool_call_density > 0.5/100w. If no winner: document why and design the next iteration.

---

## Step 5 — Decide what's next

**Outcome A — clean validation (everything green, ≥1 writer wins):**
- Write a celebratory handoff documenting the first-ever successful 3-way bakeoff.
- File issue: "writer-selection decision per ADR `2026-04-26-reboot-agent-responsibilities.md` §3" — propose the winner, get user sign-off.
- Update `pipeline.md` rule to reflect the choice.
- This is the milestone the entire #1577 EPIC has been building toward.

**Outcome B — partial green (some writers pass, some fail):**
- Document which writer wins and which fails.
- Per-writer failure-mode analysis: is it prompt-following? Tool-grounding? Specific dim weakness?
- File a follow-up issue for the weakest writer's failure mode.
- The bakeoff has STILL produced real data — that's a win.

**Outcome C — all writers fail at python_qg again:**
- This means strands 2+3 didn't actually unblock publication. Diagnose with `phase_writer_summary` + `python_qg.json` per writer.
- This is a regression in #1721 and needs immediate root-cause analysis.

**Outcome D — strand 1 broken in some way:**
- Review the dispatch's PR for the specific failure mode.
- File a focused fix dispatch.

---

## Multi-agent cooperation pattern (the user explicitly asked for this)

Throughout this runbook, the agent split is:

| Phase | Codex | Claude | Gemini |
|---|---|---|---|
| Strand 1 implementation | **author** | review (during dispatch + on PR) | n/a |
| Bakeoff dispatch | **runs the harness** (the harness invokes all 3 writers) | review/decide on outcome | participates as one of 3 writers |
| REPORT.md interpretation | n/a (already-aggregated output) | **author** of the analysis | n/a |
| Cross-review of writers | **reviews 2 cross-family** in the bakeoff | **reviews 2 cross-family** in the bakeoff | **reviews 2 cross-family** in the bakeoff |
| Writer-selection decision | n/a | **proposes** to user; user signs off | n/a |

The bakeoff IS the multi-agent cooperation pattern in action — 3 writers + 6 cross-family reviews, no self-review. Strand 1 makes that cooperation honest by requiring writers to actually USE the tools they cite, which is the whole point of giving them tool access.

For Codex+Claude on strand 1 specifically: Codex implements, Claude reviews during the dispatch (via `ask-claude`), Claude reviews again on the PR. That's the "two-agent gate" pattern from `agent-cooperation.md`.

Gemini does NOT touch this strand — it's pipeline code, and per the `pipeline.md` rule + the agent-responsibilities ADR, pipeline writers are Codex/Claude territory. Gemini owns content/wiki.

---

## Failure budget

If after Step 4 the bakeoff still produces nothing useful, the honest conclusion may be: **the writer-bakeoff approach itself isn't producing decision-grade signal**, and the writer-selection decision needs to fall back to qualitative review of a small number of seeded modules. That would be a substantive change to the ADR.

Don't reach for that conclusion until at least ONE more bakeoff has run with strand 1 in place. The 2026-05-06 22:19 run was on prompts-without-end-gate-without-strand-3, so it was structurally broken. We have not yet had a fair bakeoff.

---

## Cleanup checklist (after the run lands)

- [ ] All worktrees gone except active ones (use `git worktree list`)
- [ ] Stale branches deleted
- [ ] Bakeoff artifacts at `audit/bakeoff-2026-05-05/` either committed (if first-ever-success and worth historical record) or noted in the next handoff as untracked
- [ ] Update #1720 with strand-1 PR + final outcome; close if all 3 strands shipped + bakeoff validates
- [ ] Update #1577 EPIC with the bakeoff result + writer-selection status

---

## Stretch: if everything above lands cleanly

Outcome A from Step 5 unlocks Phase 5 of the reboot per ADR — the actual content build of A1 modules using the chosen writer. That's the next-next-session work. Don't start it before the user signs off on the writer choice.

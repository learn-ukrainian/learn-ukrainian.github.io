# Codex dispatch brief — #1720 strand 1 (tool-theatre detection)

> **Worktree:** `.worktrees/dispatch/codex/1720-strand-1`
> **Branch:** `codex/1720-strand-1`
> **Base:** `main`
> **Mode:** danger
> **Effort:** medium
> **Hard timeout:** 5400s (90 min)
> **Reviewer:** Claude (cross-family adversarial — invoked from inside this dispatch via `ask-claude`, then again post-PR by orchestrator)
> **No auto-merge.** Orchestrator (Claude) reviews CI + body, then merges.

---

## Context — why this exists

The bakeoff at `audit/bakeoff-2026-05-05/` (run 2026-05-06 22:19 UTC, REPORT.md committed via #1720) showed all 3 writers cite MCP tools in `<plan_reasoning verification="...">` blocks WITHOUT actually calling those tools. `tool_calls_total = 0` for all writers despite explicit citations of `mcp__sources__verify_words`, `search_heritage`, etc. This is **CoT theatre** — visible reasoning that performs grounding without doing it.

Strands 2 and 3 of #1720 shipped in #1721 (`f8bd113bca`):
- Strand 2: `<end_gate>...</end_gate>` block mandate — already in main.
- Strand 3: writer-correction single-fence module-only contract + split-based parser — already in main.

**Strand 1 (this dispatch) is the last missing piece** before we can run a fair bakeoff and pick a writer winner per `docs/decisions/2026-04-26-reboot-agent-responsibilities.md` §3. The whole #1577 EPIC has been building toward this gate.

---

## Worktree setup (mandatory — do NOT branch in main checkout)

This is a HARD project rule (`.claude/rules/delegate-must-use-worktree.md`). Run **exactly** these steps, in order, BEFORE any code edits:

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main                          # avoid stale base — #1472 lesson
git worktree add -b codex/1720-strand-1 .worktrees/dispatch/codex/1720-strand-1 origin/main
cd .worktrees/dispatch/codex/1720-strand-1
git log --oneline HEAD..origin/main            # MUST be empty (branch == origin/main)
.venv/bin/python -c "import scripts.build.linear_pipeline" # smoke
```

If `git log HEAD..origin/main` returns ANY commit, STOP and rebase before starting work — that's the #1472 stale-base trap.

---

## Goal

Detect "tool-theatre" — writer cites a tool name inside a `<plan_reasoning verification="...">` block that does NOT correspond to an actual tool call in the same writer turn's trace. Surface the violation as a JSONL event, gate publication on it, and route to the existing writer-correction loop.

---

## Implementation

### Files to touch

| File | Change |
|---|---|
| `scripts/build/linear_pipeline.py` | Add `detect_tool_theatre()` function. Wire into `phase_writer_summary` emission site (around line 1396-1404 — the `summary` dict construction). Emit a new `writer_tool_theatre` JSONL event when violations exist. Add `"tool_theatre"` to `WRITER_CORRECTION_GATES` (line 80-88) so the existing correction-pass loop handles it. |
| `scripts/build/phases/linear-write.md` | Strengthen §Tier-1 bullet 5 — see exact wording below. |
| `scripts/build/phases/linear-writer-correction.md` | Extend so the `tool_theatre` gate prompts the writer with a binary call-or-remove choice. Single-fence module-only response (use #1721's contract — the `parse_writer_correction_module_only()` parser handles it). |
| `tests/test_writer_correction_no_op_diagnostic.py` | Add tool-theatre detection unit tests (list below). |
| `tests/test_prompt_cot_tier1_scaffolding.py` | Add `test_writer_prompt_mandates_tool_call_match` to lock the new prompt rule. |

### Function signature (canonical)

Place near the other helpers (after `_mapping_from_tool_call` at line 1189, before `_extract_writer_gate` at 1132 — keep helpers grouped):

```python
_PLAN_REASONING_BLOCK_RE = re.compile(
    r"<plan_reasoning\b[^>]*>(.*?)</plan_reasoning>",
    re.DOTALL | re.IGNORECASE,
)
_TOOL_CITATION_RE = re.compile(
    r"`(?P<name>(?:mcp__sources__|search_|verify_|check_|query_|translate_)\w+)`"
)


def detect_tool_theatre(
    writer_output: str,
    tool_calls: list[Mapping[str, Any]],
) -> list[str]:
    """Return the sorted list of tool names CITED in <plan_reasoning>
    verification blocks but NOT present in the actual tool_calls trace.

    A non-empty return value = tool-theatre violation.

    Normalization: strip the `mcp__sources__` prefix on both cited and
    called sides before comparing, so `mcp__sources__verify_words` cited
    and `verify_words` called are treated as a match.

    Scope: ONLY scans inside <plan_reasoning>...</plan_reasoning> blocks,
    so backticks in module.md prose ("`verify_words` is the function")
    are NOT counted as citations.
    """
```

### Plumbing

1. **Citation extraction:** `_PLAN_REASONING_BLOCK_RE.findall(writer_output)` → for each block body, `_TOOL_CITATION_RE.findall(block)` → strip `mcp__sources__` prefix → set of cited names.
2. **Trace extraction:** for each item in `tool_calls`, get the tool name via `_mapping_from_tool_call(call).get("tool")` (already-existing helper). Strip `mcp__sources__` prefix.
3. **Diff:** `sorted(cited - called)` is the violation list.
4. **Tool-family decision: canonical-only (NOT a family map).**
   Recommended in this brief because it's simpler, harder to game, and the prompt strengthening already says the writer must cite the *actual tool name they call*. If the writer wants `search_heritage` to count as satisfied, they call `search_heritage` (the umbrella). If they call the underlying `search_grinchenko_1907` directly, they cite that. Document this choice with an inline comment near the function.
5. **Wire into `phase_writer_summary`:** after the existing summary dict construction (line 1396-1404), compute `theatre_violations = detect_tool_theatre(output, tool_calls)`. Add `"tool_theatre_violations": theatre_violations` to the summary dict. When non-empty, also emit a separate `writer_tool_theatre` event with `module`, `writer`, `violations`, `cited_count`, `called_count`.
6. **Add to `WRITER_CORRECTION_GATES`:** `"tool_theatre"` joins the existing 5 gates. Treat as module-only (not strict_json_parse) so #1721's split-based `parse_writer_correction_module_only()` parser handles the response.
7. **Wire into `_apply_writer_correction` decision site (around line 2340):** when the writer fails the `tool_theatre` gate, the gate name is passed through the existing path; nothing extra needed beyond gate-set membership and the prompt template update below.

### Prompt update — `scripts/build/phases/linear-write.md` §Tier-1 bullet 5

Add at the END of bullet 5 (after the existing rule):

> **Tool-citation honesty (mandatory).** Every tool name you cite inside a `<plan_reasoning verification="...">` attribute or block body MUST correspond to an actual tool call you made on this turn. The pipeline cross-references citations against the trace and treats unmatched citations as a hard fail (`tool_theatre`). Citing a tool you did not call to satisfy the verification rubric — without doing the verification — is the canonical theatre failure and will block publication. If you intend to cite `search_heritage`, call `search_heritage`. If you intend to cite the underlying `search_grinchenko_1907`, call that. Canonical names only — no family aliases.

### Prompt update — `scripts/build/phases/linear-writer-correction.md`

Add a new conditional section keyed on `gate == tool_theatre` (mirror the existing per-gate sections). The body must give the writer a strict binary choice. Suggested wording:

> ## When `gate = tool_theatre`
>
> Your previous turn cited tool names in `<plan_reasoning verification>` that you did not actually call. The unmatched citations are: `{violations}`.
>
> Pick exactly one path. Single fenced ```` ```markdown file=module.md ```` block as your entire response, no prose around it.
>
> 1. **Call them now.** Make the tool calls you cited (each one), then re-emit `module.md` with the actual tool results in the verification block. The verification text should reference the result, not the tool name in isolation.
> 2. **Remove the false citations.** Delete the unmatched tool names from the verification blocks; replace each removed citation with the verbatim text "verification not performed" so it's auditable.
>
> No third option. Citing the same tools again without calling them = same failure, same gate, exhausted retry.

Verbatim citation rule (so reviewers can grep): "every tool name you cite in `<plan_reasoning verification>` must correspond to a tool call you actually made in this turn's trace."

---

## Tests (mandatory — all must pass before opening PR)

In `tests/test_writer_correction_no_op_diagnostic.py`:

1. **`test_detect_tool_theatre_returns_unmatched_citations`** — writer output cites `verify_words` and `search_heritage`; trace contains only `verify_words` → returns `["search_heritage"]`.
2. **`test_detect_tool_theatre_normalizes_mcp_prefix`** — writer cites `` `mcp__sources__verify_words` ``; trace contains `verify_words` → returns `[]`.
3. **`test_detect_tool_theatre_empty_input`** — empty trace and empty output → returns `[]`.
4. **`test_detect_tool_theatre_only_scans_plan_reasoning_blocks`** — backticked tool name inside module.md prose (outside any `<plan_reasoning>` block) is NOT counted → returns `[]`.
5. **`test_detect_tool_theatre_handles_multiple_blocks`** — two `<plan_reasoning>` blocks, citations spread across both → both contribute to cited set.
6. **`test_writer_correction_handles_tool_theatre_gate`** — single-fence response patches module.md and clears the gate (uses #1721's `parse_writer_correction_module_only`).

In `tests/test_prompt_cot_tier1_scaffolding.py`:

7. **`test_writer_prompt_mandates_tool_call_match`** — asserts the new "Tool-citation honesty" rule text appears in `linear-write.md`. Mentally remove the rule from the prompt; this test must FAIL (prove it's a real regression detector, not a tautology).

---

## Validation before opening PR

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1720-strand-1
.venv/bin/python -m pytest \
  tests/test_writer_correction_no_op_diagnostic.py \
  tests/test_prompt_template_render.py \
  tests/test_prompt_cot_tier1_scaffolding.py \
  tests/test_no_rewrite_contract.py
.venv/bin/ruff check scripts/build/linear_pipeline.py
git diff --check
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer claude-tools --dry-run | tail -40
```

All four MUST pass. The dry-run must emit `phase_writer_summary` with the new `tool_theatre_violations` field present (empty list is fine — the dry-run won't have a real trace).

Also: run the existing aggregator against the prior bakeoff JSONLs to confirm new fields don't crash it:

```bash
.venv/bin/python scripts/audit/bakeoff_aggregate.py audit/bakeoff-2026-05-05/ --dry-run 2>&1 | tail -20
```

If `bakeoff_aggregate.py` lacks a `--dry-run` flag, run it without args; it must complete without TypeError on the new fields.

---

## Get Claude adversarial review (mandatory)

After local validation passes:

```bash
git -C /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1720-strand-1 \
  diff origin/main..HEAD > /tmp/strand-1-diff.txt

cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude \
  "Adversarial review for #1720 strand 1. Read /tmp/strand-1-diff.txt. Focus: (A) does _TOOL_CITATION_RE correctly scope to <plan_reasoning> blocks only and not catch backticks in module.md prose? (B) is the canonical-only normalization choice (no family map) defensible vs the cleaner behavior promised by family aliases? (C) is the correction-pass binary choice (call-or-remove) prompted clearly enough that a writer won't pick a third path or game it? (D) does the new tool_theatre gate enter the existing correction-loop without ordering bugs vs the existing word_count / plan_sections / mdx_render gates? (E) test gaps — specifically: does test #4 (only_scans_plan_reasoning_blocks) actually exercise prose-backticks-outside-block? (F) telemetry shape — would the new tool_theatre_violations field break bakeoff_aggregate.py? Be adversarial." \
  --task-id 1720-strand-1-review \
  --model claude-opus-4-7
```

Apply review feedback inline. Commit it as a separate commit with `Reviewed-By: claude-opus-4-7 (1720-strand-1-review)` trailer.

---

## Open PR

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/1720-strand-1
git push -u origin codex/1720-strand-1

gh pr create \
  --title "feat(prompts): tool-theatre detection — cross-check plan_reasoning citations vs trace (#1720 strand 1)" \
  --body "$(cat <<'EOF'
## Summary

Closes the last open strand of #1720 — the bakeoff blocker.

- New `detect_tool_theatre()` in `linear_pipeline.py` cross-references tool names cited in `<plan_reasoning verification>` blocks against the actual writer turn trace.
- New `writer_tool_theatre` JSONL event surfaces violations to telemetry/aggregator.
- `tool_theatre` joins `WRITER_CORRECTION_GATES`, so the existing correction-pass loop (built in #1721) handles the failure with a single-fence module-only retry.
- Writer prompt mandates "tool-citation honesty" — citing a tool you did not call is a hard fail.
- Correction-pass prompt gives the writer a binary choice: call-the-cited-tools, or remove-the-false-citations.

## Test plan

- [ ] `pytest tests/test_writer_correction_no_op_diagnostic.py` — 6 new cases pass.
- [ ] `pytest tests/test_prompt_cot_tier1_scaffolding.py` — new prompt-rule test passes; mentally-deleting the rule fails the test.
- [ ] `bakeoff_aggregate.py` runs without TypeError on the new fields.
- [ ] `v7_build.py --dry-run` emits `phase_writer_summary` with `tool_theatre_violations` populated.

## Why this is the bakeoff blocker

Strands 2+3 (#1721) made writers emit `<end_gate>` and made the correction pass parseable. But all 3 writers in the 2026-05-06 bakeoff cited tools without calling them — `tool_calls_total = 0` across the board. Until that loop closes, the bakeoff cannot produce decision-grade signal for writer-selection per the agent-responsibilities ADR.

Reviewed-By: claude-opus-4-7 (1720-strand-1-review)
EOF
)"
```

DO NOT enable auto-merge. Orchestrator (Claude) reviews CI + body before merging.

---

## Risks I want you to think about during implementation

1. **Tool-family overlap** — writer cites `search_heritage` but the trace shows `search_grinchenko_1907` (the underlying call when `search_heritage` is the umbrella). The brief says canonical-only. Verify the umbrella tool is actually a separate registered call (not a transparent passthrough) before locking that in. If `search_heritage` is just a documentation alias and the real call is always `search_grinchenko_1907`, the brief's choice is wrong — escalate.
2. **Capture completeness** — verify all 3 writer adapters (claude-tools, gemini-tools, codex-tools) emit tool-call traces in a shape `_mapping_from_tool_call` can read. Look at the write JSONLs at `audit/bakeoff-2026-05-05/{claude,gemini,gpt55}.write.jsonl` and inspect a `function_call` event from each. If shapes differ, the diff is structurally broken before the regex even runs.
3. **Backtick noise** — the regex constrains to inside `<plan_reasoning>` blocks. Verify the regex is greedy/lazy correctly (use the explicit non-greedy `.*?` with DOTALL — the brief's `_PLAN_REASONING_BLOCK_RE` is correct as written; do not "improve" it).
4. **Empty `tool_calls` argument** — what does the function do when the writer made zero tool calls but cited several? Returns the full citation set. That's correct behavior. Add a test for this exact case.

---

## Numbered checklist (so dispatch doesn't stop mid-flight)

1. `git worktree add ... origin/main` (worktree setup, base = `origin/main`).
2. Verify `git log HEAD..origin/main` is empty.
3. Implement `detect_tool_theatre()` + regex constants in `linear_pipeline.py`.
4. Wire into `phase_writer_summary` site + new `writer_tool_theatre` event.
5. Add `tool_theatre` to `WRITER_CORRECTION_GATES`.
6. Update `linear-write.md` Tier-1 bullet 5 (Tool-citation honesty).
7. Update `linear-writer-correction.md` with `gate = tool_theatre` section.
8. Add 6 new tests in `test_writer_correction_no_op_diagnostic.py`.
9. Add 1 new test in `test_prompt_cot_tier1_scaffolding.py`.
10. Run pytest + ruff + dry-run validation. ALL must pass.
11. Run bakeoff_aggregate against existing JSONLs to verify no TypeError.
12. Get Claude adversarial review via `ask-claude` (above command).
13. Apply review fixes as a separate commit with `Reviewed-By:` trailer.
14. `git push -u origin codex/1720-strand-1`.
15. `gh pr create` (above command — explicit body).
16. Do NOT enable auto-merge.

If any step fails, STOP, document where you stopped, do not silently skip.

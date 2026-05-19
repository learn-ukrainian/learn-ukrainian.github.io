# Dispatch — Remove vestigial CoT scaffolding from V7 writer prompt (linear-write.md)

**Agent:** codex
**Model:** `gpt-5.5`
**Effort:** `xhigh`
**Mode:** `danger` (worktree-isolated, can commit + push + open PR)
**Task ID:** `cot-removal-linear-write-20260519`
**Source decision:** 3-agent consensus (Codex GPT-5.5 + Gemini 3.1 Pro + DeepSeek v4 Pro) folded across §6 (DeepSeek introspection) and §7 (CoT architecture) of `audit/2026-05-19-multi-agent-routing-assessment/REPORT.html`. The verdict was unanimous: visible CoT in the V7 writer is **vestigial** — tax on output budget that no downstream gate parses.
**Estimated effort:** 1-2 hours.
**Reviewer policy:** human-merge after CI green; no `--admin` bypass (per `memory/MEMORY.md` #M-0.5).

---

## Why this exists (one paragraph)

The V7 writer prompt at `scripts/build/phases/linear-write.md` carries a heavy CoT scaffolding contract — `<plan_reasoning>` blocks with six XML sub-nodes per section, plus `<implementation_map_audit>` + `<bad_form_audit>` + `<verification_trace>`. Empirically (REPORT.html §5, §6), the highest-content-quality challenger in the multi-model writer bakeoff (deepseek-v4-pro) **dropped the entire scaffolding** and still produced the best Ukrainian. DeepSeek's own introspection identified the scaffolding as "compressed away as a means to the artifact, not the artifact itself." The orchestrator pre-verified the audit fields are not parsed by any downstream Python gate (see "Anchor facts" §4 below). Together: the CoT scaffolding is a tax on output budget without a load-bearing function. Remove it. Add two prompt-clarity directives that the bakeoff identified as universal failures across 8 of 8 challengers (wrong fence syntax, JSON-in-YAML). Then validate with an m20 rebuild.

---

## Pre-flight #M-4 evidence preamble (READ FIRST — mandatory)

This dispatch must obey `memory/MEMORY.md` #M-4 (deterministic-over-hallucination) and `docs/best-practices/deterministic-over-hallucination.md`. Every verifiable claim in the PR body MUST quote a tool-output triple (command + cwd + raw output). The claims and their tools:

| Claim in PR body | Required deterministic tool | Output format |
|---|---|---|
| "Tests pass" | `.venv/bin/python -m pytest tests/build/ tests/test_writer_prompt_structured_cot.py -v` from repo root | quote final `N passed in M.MMs` line raw |
| "Lint clean" | `.venv/bin/ruff check scripts/build/ tests/build/` from repo root | quote `All checks passed!` or zero-error final line raw |
| "Removed plan_reasoning section count" | `git diff scripts/build/phases/linear-write.md | grep -c "^-<plan_reasoning\|^-<verification_trace\|^-<implementation_map_audit\|^-<bad_form_audit"` from worktree | quote the integer raw |
| "No remaining references to removed fields in scripts/" | `grep -rn "implementation_map_audit\|bad_form_audit\|verification_trace" scripts/ --include="*.py" --include="*.md" | grep -v __pycache__ | wc -l` from worktree | quote the integer raw (must be 0) |
| "m20 rebuild passes audit-gate under tightened prompt" (claude-tools baseline) | `.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer claude-tools --worktree 2>&1 \| tail -30` | quote the final audit summary lines raw |
| "Commit landed" | `git log -1 --oneline` from worktree | quote line raw |
| "PR opened" | `gh pr view --json url -q .url` | quote URL raw |

Do NOT write "I confirmed X" without a quoted command+output triple. The reviewer will grep for evidence.

---

## Anchor facts (orchestrator pre-verified — do not re-derive, but DO re-read each file before editing per `code-editing-safety.md` rule 2)

1. **`implementation_map_audit` and `bad_form_audit` are NOT parsed by any Python gate.**
   - Verifier (orchestrator ran 2026-05-19): `grep -rn "implementation_map_audit\|bad_form_audit" scripts/ --include="*.py" 2>/dev/null | grep -v __pycache__`
   - Result: **0 hits**.
   - Disposition: **REMOVE both directives** from `linear-write.md`. They are prompt-side instructions that nothing downstream parses.

2. **`<plan_reasoning>` blocks are also not parsed by any Python gate.**
   - Same grep methodology against the term `plan_reasoning`: only the writer prompt itself contains the string. (You will re-verify this as Step 0.)
   - Disposition: **REMOVE the entire "Mandatory visible verification block" section** (`linear-write.md` lines 11-58) including all six sub-nodes (`<word_budget>`, `<plan_vocab>`, `<register>`, `<teaching_sequence>`, `<verification_plan>`, `<verification_trace>`) and the `<implementation_map>` block nested inside.

3. **`<verification_trace>` is already flagged as tool-theatre risk in `linear_pipeline.py:~2051`.**
   - The handoff already noted: "telemetry (`writer_tool_calls.json`) replaces it."
   - Disposition: **REMOVE** `<verification_trace>` block requirements (already inside the removal scope of #2).

4. **The two universal failures from REPORT.html §5 (lines 576-582) are PROMPT-CLARITY bugs:**
   - **Wrong fence syntax**: every challenger emitted ```` ```markdown file=module.md ```` instead of pipeline-expected ```` ```module.md ````.
   - **JSON in `.yaml` blocks**: every challenger emitted JSON inside `activities.yaml / vocabulary.yaml / resources.yaml` fences instead of YAML.
   - Disposition: **ADD two explicit prompt directives** to address these. Suggested wording (refine as needed):
     > **Fence syntax (mandatory).** Open each artifact fence with the bare filename: ```` ```module.md ````, ```` ```activities.yaml ````, ```` ```vocabulary.yaml ````, ```` ```resources.yaml ````. Do NOT write ```` ```markdown file=module.md ```` or ```` ```yaml file=activities.yaml ```` — those forms are GitHub/Common-Markdown defaults and will be rejected by the pipeline parser.
     >
     > **YAML content (mandatory).** `activities.yaml`, `vocabulary.yaml`, and `resources.yaml` MUST contain YAML — never JSON. Use list-of-mappings with hyphen-prefixed list items and key: value mappings. JSON inside a `.yaml` fence will fail the strict YAML parser at MDX-render time. Acceptable: `- type: quiz\n  title: ...`. Unacceptable: `[{"type": "quiz", "title": "..."}]`.

5. **Note line 296 of the current `linear-write.md`** mentions "fenced JSON code blocks labeled with the language `json`" — verify the context. The 4 artifact files are `module.md` + 3 `.yaml`. If the line 296 reference is to a non-artifact block (example, schema, etc.), preserve it. If it contradicts the YAML directive, reconcile by removing the JSON reference (the v1 REPORT confirms YAML is correct for `.yaml` artifacts).

6. **The "end_gate" block** (lines ~211-244, ~565) and other sections referring to `<plan_reasoning>` must be updated to drop the requirement chain. Same for references on lines 56, 58, 244, 565. Re-grep after edits to ensure zero remaining references.

7. **Heritage-defense + Tier-1 verification + MCP tool guidance** (lines ~75-210) are SUBSTANTIVE content directives — KEEP. The scope of this removal is the CoT *scaffolding*, not the actual verification discipline.

---

## Numbered execution steps (mandatory order)

### Step 0 — Set up worktree and pre-verification

```bash
git worktree add .worktrees/dispatch/codex/cot-removal-linear-write-20260519 origin/main
cd .worktrees/dispatch/codex/cot-removal-linear-write-20260519
```

Re-verify the orchestrator's anchor facts in your own shell. Quote each command + cwd + raw output in the PR body:

1. `grep -rn "implementation_map_audit\|bad_form_audit" scripts/ --include="*.py" | grep -v __pycache__ | wc -l` → expect `0`
2. `grep -rn "plan_reasoning" scripts/ --include="*.py" | grep -v __pycache__` → expect output ONLY from the writer prompt template OR ancillary template-handling helpers (no gates).
3. `grep -n "verification_trace\|implementation_map_audit\|bad_form_audit\|plan_reasoning" scripts/build/linear_pipeline.py` → record matches; if any are parsers/validators, escalate before removing.

If any of these contradict the anchor facts above, **STOP and escalate** — open an issue, do NOT proceed with removal.

### Step 1 — Edit `scripts/build/phases/linear-write.md`

1. **Remove lines 11-58** (the entire "Mandatory visible verification block" section, including the `<implementation_map>` nested block at lines 20-38).
2. **Remove lines 60-73** (the "Pre-emit obligation-count check" section that emits `<implementation_map_audit>`).
3. **Remove lines 127-135** (the "Pre-emit bad-form audit" section that emits `<bad_form_audit>`).
4. **Sweep for orphan references** to the removed fields. At minimum, fix:
   - Line 56: "Keep each `<plan_reasoning>` block to 200 words or fewer..." → remove.
   - Line 58: "Only after all `<plan_reasoning>` blocks are complete..." → remove or rewrite.
   - Line 167: `<plan_reasoning>` mentions — remove.
   - Line 211-244: "End-of-output gate" referring to `<plan_reasoning>` — rewrite to drop the requirement chain.
   - Line 565: "After emitting all required `<plan_reasoning>` blocks..." → rewrite.
   - Line 244: "Return the visible `<plan_reasoning>` blocks first..." → rewrite.
5. **Add the two prompt-clarity directives** from Anchor fact #4. Place them in a new section titled e.g. `## Artifact fence + content-type contract (mandatory)` AFTER any existing markup-conventions section. Keep both directives concise (a single paragraph each, with one acceptable + one unacceptable example).
6. **Re-read the entire `linear-write.md` after editing** — confirm the structure flows: north-star + lesson contract → writer task overview → existing markup/heritage/Tier-1 sections → the new fence+YAML directive → the 4 artifact fences → end-gate (rewritten to drop CoT requirements). The visible word-target instruction (#1673/#1661) remains in the WORD-COUNT enforcement section if there is one; if it was bundled into the removed `<plan_reasoning>` block, surface the word-target constraint as a one-liner in the lesson-contract preamble.

### Step 2 — Apply the same disposition to writer-variant prompts if present

```bash
ls scripts/build/phases/linear-write*.md
```

If `linear-write-grok.md` / `linear-write-codex.md` / `linear-write-claude.md` exist as model-specific variants, apply the same removals + additions to each. Same scope, same disposition.

### Step 3 — Regenerate / update test fixtures that mirror the writer prompt structure

```bash
grep -rn "implementation_map_audit\|bad_form_audit\|<plan_reasoning>" tests/ --include="*.py" | grep -v __pycache__
```

If any test fixture asserts the presence of these blocks, update the assertions to either:
- Remove them (preferred — the gate is gone), OR
- Re-target them at telemetry events instead (e.g., `writer_tool_calls.json`).

Run the existing test that covers the writer prompt structure (worktree has no `.venv/`; `cd` to the main repo first):
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python -m pytest tests/test_writer_prompt_structured_cot.py -v
```

If it asserts the presence of `<plan_reasoning>` and now fails, **update the test** to reflect the new contract (no visible CoT required). DO NOT skip the test — adjust assertions.

### Step 4 — Lint + test sweep

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/ruff check scripts/build/ tests/build/
.venv/bin/python -m pytest tests/build/ tests/test_writer_prompt_structured_cot.py -v
```

Both must pass green. Quote final lines in the PR body. After the test sweep, `cd` back to your worktree for the next step.

### Step 5 — m20 rebuild under tightened prompt (validation gate)

This is the load-bearing empirical test. Run a single-module rebuild via V7 with the claude-tools default writer (from the main repo so `.venv/bin/python` resolves):

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
.venv/bin/python scripts/build/v7_build.py a1 my-morning --writer claude-tools --worktree
```

(Note: `my-morning` is the canonical A1 m20 module per the v1 bakeoff. Use this slug.)

Capture the audit-gate verdict. The test passes if:
- The writer no longer emits the removed scaffolding (verify via stdout: NO `<plan_reasoning>`, NO `<implementation_map_audit>`, NO `<bad_form_audit>`).
- All audit gates pass (the same gates m20 build #8 passed under the previous prompt).
- Output module quality is at least at parity with build #8 (use the existing audit/m20-build-8/ artifacts as reference).

If the audit fails, debug in-worktree (the worktree contains the rebuild artifacts) and re-iterate. Do NOT proceed to PR if the audit fails — the v1 report's empirical claim (deepseek-v4-pro produces best content with NO CoT) was on a single bakeoff; production validation under claude-tools is required.

If the audit fails for a non-content reason (a structural gate the new prompt didn't anticipate), escalate by filing a follow-up issue rather than reverting the change. The v1 REPORT.html section §7 + §8 documents the design intent.

### Step 6 — Commit + PR

```bash
git add scripts/build/phases/linear-write*.md tests/...
git commit -m "$(cat <<'EOF'
fix(writer-prompt): remove vestigial CoT scaffolding from V7 writer prompt

The V7 writer prompt at scripts/build/phases/linear-write.md carried
heavy CoT scaffolding — <plan_reasoning> with six XML sub-nodes per
section, plus <implementation_map_audit>, <bad_form_audit>, and
<verification_trace>. The 2026-05-19 multi-agent routing audit
(audit/2026-05-19-multi-agent-routing-assessment/REPORT.html) showed:

(1) The audit fields are not parsed by any downstream Python gate
    (verified: grep -rn "implementation_map_audit|bad_form_audit"
    scripts/ → 0 hits).
(2) DeepSeek-v4-Pro dropped the entire scaffolding in the bakeoff and
    produced the highest-quality Ukrainian content of any challenger
    (REPORT.html §5 + §6 introspection).
(3) 3-agent consensus (Codex/Gemini/DeepSeek, REPORT.html §7) ruled
    the scaffolding REMOVE not TIGHTEN.

Net change:
- REMOVED: <plan_reasoning> blocks (and all 6 sub-nodes), <implementation_map_audit>,
  <bad_form_audit>, <verification_trace>, and orphan references.
- ADDED: two prompt-clarity directives that the bakeoff identified as
  universal failures across 8 of 8 challengers (wrong fence syntax,
  JSON-in-YAML).
- VALIDATED: m20 a1/my-morning rebuild under claude-tools writer
  passes audit-gate with the tightened prompt (see PR body for
  command + raw audit output).

Co-Authored-By: Codex GPT-5.5 <noreply@openai.com>
EOF
)"
git push -u origin codex/cot-removal-linear-write-20260519
gh pr create --title "fix(writer-prompt): remove vestigial CoT scaffolding from V7 writer prompt" --body "$(cat <<'EOF'
## Summary

Removes vestigial CoT scaffolding from `scripts/build/phases/linear-write.md` per the 2026-05-19 multi-agent routing audit's 3-agent consensus. Adds two prompt-clarity directives that address universal failures observed across 8/8 challenger writers in the same audit.

## #M-4 evidence preamble

(Codex: fill in each row with the actual command + cwd + raw output during execution. Every claim must have a tool triple.)

- Tests pass: …
- Lint clean: …
- Removed plan_reasoning section count: …
- No remaining references to removed fields in scripts/: …
- m20 rebuild passes audit-gate under tightened prompt (claude-tools baseline): …

## Source

3-agent consensus folded into `audit/2026-05-19-multi-agent-routing-assessment/REPORT.html` §5, §6, §7. Decision is unanimous: REMOVE not TIGHTEN. See REPORT.html §7 for the recommendation block.

## Risk

Single empirical data point from the v1 bakeoff (deepseek-v4-pro) supports the "no CoT → better content" claim. Production validation under claude-tools (the V7 default writer) IS load-bearing here — see m20 rebuild gate above. If the rebuild gate fails for any non-trivial reason, this PR should not merge.

## Test plan

- [x] All unit tests pass (`tests/build/`, `tests/test_writer_prompt_structured_cot.py`).
- [x] Ruff lint clean.
- [x] m20 a1/my-morning V7 build passes audit-gate under tightened prompt.
- [x] No remaining references to removed scaffolding in `scripts/`.
- [ ] Manual: human reviewer confirms the new fence-syntax + YAML directives read clearly.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

**DO NOT auto-merge.** Per project policy, human reviews before merge.

---

## Out of scope for this dispatch

- **Re-running m20 build #9 against deepseek-v4-pro as a paired challenger.** That's a follow-up dispatch (cheap — ~$0.06) to confirm the v1 REPORT prediction that deepseek-v4-pro under the tightened prompt would now pass contract AND keep its content lead. Defer to a separate brief after this PR lands; gate on whether the claude-tools rebuild here passes.
- **Promoting deepseek-v4-pro to V7 primary writer.** That's a separate routing decision (REPORT.html §7 P1) requiring agent-activity matrix v1.3 changes. Out of scope here.
- **Editing other phase prompts** (`linear-review*.md`, `linear-fix*.md`, etc.). The CoT verdict was specifically about the WRITER. Reviewer + fixer phase CoT can be addressed in follow-up dispatches if useful.

---

## Decision tree on rebuild failure

| Failure mode | Disposition |
|---|---|
| Audit gate fails, content quality at parity | Diagnose which gate, file follow-up issue with reproducer + the rebuild's audit log link, hold the PR. |
| Audit gate passes, content quality regresses (more Russianisms, immersion violations, lower word-target adherence) | Hold the PR. The prompt is "too tight"; needs an additional content-quality directive added before re-iterating. Document the regression in the PR body and the v1 REPORT.html as evidence the CoT-removal verdict needs revisiting. |
| Audit gate passes, content quality at-or-above parity | Open the PR for human review per Step 6. |
| Hermes / OpenRouter routing error (per the patch in c16e0cffc6) | Confirm `scripts/agent_runtime/adapters/hermes_qwen.py` is on the current main, retry. If the routing-drift bug recurs, escalate — it's outside this dispatch's scope. |

---

## Cross-references

- v1 routing audit: `audit/2026-05-19-multi-agent-routing-assessment/REPORT.html`
- DeepSeek introspection (§6 of v1 report): canonical evidence for the CoT-removal verdict.
- 3-agent CoT consensus (§7 of v1 report): the unanimous REMOVE recommendation.
- Universal-failures block (§5 of v1 report, lines 576-582): the two prompt-clarity bugs this brief addresses.
- Hermes provider-routing fix (preceding commit `c16e0cffc6`): not directly relevant but unblocked the bakeoffs that produced the data behind this verdict.
- DeepSeek-v4-pro discount cliff: 2026-05-31. Landing this PR + a deepseek-v4-pro rebuild before that cliff would unlock the writer rerouting; defer the rerouting decision to a follow-up.

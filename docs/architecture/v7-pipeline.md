# V7 Pipeline

**Status:** CURRENT V7 ARCHITECTURE SPEC.
**Date:** 2026-05-19
**Scope:** Single-module V7 build pipeline.

This document supersedes [`ARCHITECTURE.md`](ARCHITECTURE.md) for build
pipeline architecture. `ARCHITECTURE.md` is a V5/V6-era reference and should be
treated as a `_legacy/` candidate once links are migrated.

The legacy banner in `ARCHITECTURE.md` says this is a
`LEGACY V5/V6-ERA DOC` and that it predates the EPIC #1577 reboot.

Use this file for V7. Use the legacy file only for historical context.

---

## Elevator Pitch

V7 is a single-module linear pipeline: worktree-isolated, deterministic gates
first, LLM review last, and honest `plan_revision_request` terminals over
rewrite thrashing.

The entrypoint is:

```text
.venv/bin/python scripts/build/v7_build.py {level} {slug} --worktree
```

The library implementation is:

```text
scripts/build/linear_pipeline.py
```

---

## Status Banner

V7 replaces the V5/V6 architecture described in `docs/architecture/ARCHITECTURE.md`.
That file's own banner points to `scripts/build/linear_pipeline.py` as the
reboot-era pipeline and tells readers to use the old architecture only for V5/V6
historical context.

The current V7 wrapper describes itself as:

```text
CLI wrapper for the V7 linear module pipeline.
```

The current linear pipeline module describes itself as a one-way path through
plan validation, research packet assembly, prompt rendering, writer invocation,
deterministic Python QG, LLM QG aggregation, and MDX assembly.

---

## Phase Order

`scripts/build/v7_build.py` does not define a `_PIPELINE_PHASES` tuple or enum.
The phase order is the inline assignment sequence inside `_run()`:

```text
plan
knowledge_packet
writer
python_qg
wiki_coverage_gate
wiki_coverage_review
llm_qg
mdx
```

Do not add phase names that are not in the code. If the code grows a phase-list
constant later, update this section from that constant.

---

## Phase 1 - `plan`

**Purpose:** Load and validate the module plan.

**Inputs:**

```text
curriculum/l2-uk-en/plans/{level}/{slug}.yaml
```

**Code path:**

- `linear_pipeline.plan_path_for(level, slug)`
- `plan_path.read_text(encoding="utf-8")`
- `linear_pipeline.load_plan(plan_path)`
- `linear_pipeline.validate_plan(plan)`

**Outputs:**

- `plan_content` in memory.
- `plan` mapping in memory.
- `phase_done` telemetry event.

The phase does not write a plan copy to disk today.

**Failure modes:**

- Plan file does not exist.
- Plan YAML cannot be parsed.
- Required plan keys are missing.
- Plan validation raises `LinearPipelineError`.

**Correction path:**

Plan generation and plan repair are outside the deterministic-first correction
ladder. If the plan is wrong, V7 should terminal honestly and route the fix to
plan work, not mutate the plan during a module build. See
[`2026-05-18-deterministic-first-iteration.md`](../decisions/2026-05-18-deterministic-first-iteration.md)
for the distinction between V7 correction behavior and plan generation.

---

## Phase 2 - `knowledge_packet`

**Purpose:** Build the writer knowledge packet and wiki obligation manifest from
compiled wiki/source material.

**Inputs:**

- Validated `plan` from phase 1.
- Compiled wiki article(s) for `{level}/{slug}`.
- Sources registry and dictionary context used by `linear_pipeline`.

**Code path:**

- `linear_pipeline.build_knowledge_packet(level=level, slug=slug, plan=plan)`
- `linear_pipeline.build_wiki_manifest_data(level=level, slug=slug, plan=plan)`
- `json.dumps(wiki_manifest_data, ensure_ascii=False, indent=2)`

**Outputs:**

- `knowledge_packet` in memory.
- `wiki_manifest` in memory.
- `phase_done` telemetry event.

The current code writes `knowledge_packet.md` and `wiki_manifest.json` during the
writer phase after the writer prompt is rendered. The logical packet phase
itself is in-memory.

**Failure modes:**

- No wiki article exists for the module.
- Wiki manifest extraction fails.
- Wiki manifest validation fails.
- Source or dictionary context assembly fails.

**Correction path:**

Knowledge packet failures are not writer-correction failures. If the packet or
manifest cannot be built, fix the source/wikipedia compilation side or the
manifest extractor. Wiki compilation itself is a separate pipeline under
`scripts/wiki/`, not a V7 module-build phase.

---

## Phase 3 - `writer`

**Purpose:** Seed implementation scaffolding, render the writer prompt, invoke
the selected writer, persist raw writer evidence, parse strict writer output, and
write authoring artifacts.

**Inputs:**

- Validated plan.
- Plan content.
- Knowledge packet.
- Wiki manifest JSON.
- Writer family from `--writer`.
- V7 writer prompt template from `scripts/build/phases/linear-write*.md`.

**Code path:**

- `seed_implementation_map(wiki_manifest_data, plan=plan)`
- `write_implementation_map(impl_map, impl_map_path)`
- `_writer_prompt(...)`
- `linear_pipeline.invoke_writer(...)`
- `linear_pipeline.parse_writer_output(writer_output)`
- `linear_pipeline.write_writer_artifacts(module_dir, artifacts)`

**Outputs:**

```text
{module_dir}/implementation_map.json
{module_dir}/writer_tool_calls.json
{module_dir}/writer_output.raw.md
{module_dir}/writer_prompt.md
{module_dir}/knowledge_packet.md
{module_dir}/wiki_manifest.json
{module_dir}/module.md
{module_dir}/activities.yaml
{module_dir}/vocabulary.yaml
{module_dir}/resources.yaml
```

**Failure modes:**

- Writer subprocess stalls or times out.
- Writer emits no usable output.
- Writer emits malformed strict JSON.
- Writer omits one of the required artifacts.
- Writer artifacts fail shape validation.
- Tool-runtime gate fails, including a tools writer with zero source-tool calls.

**Correction path:**

Writer correction belongs to deterministic-first layers L1 through L3:

- L1: implementation-map skeleton seeding narrows what the writer has to invent.
- L2: deterministic post-write gates identify the failure.
- L3: per-gate correction is append/insert-only and revalidates all gates.

The writer phase does not revive V6 `section_rewrite`, `full_rewrite`, or
`writer_swap` strategies. ADR-007 killed those rewrite paths.

---

## Phase 4 - `python_qg`

**Purpose:** Run deterministic quality gates and bounded deterministic-first
corrections against the writer artifacts.

**Inputs:**

- `module.md`
- `activities.yaml`
- `vocabulary.yaml`
- `resources.yaml`
- `implementation_map.json`
- `writer_tool_calls.json` or compatible trace files
- Source plan path

**Code path:**

- `linear_pipeline.run_python_qg_with_corrections(module_dir, plan_path, writer=writer)`
- `linear_pipeline.write_json(module_dir / "python_qg.json", python_qg)`

`linear_pipeline.py` defines `PYTHON_QG_GATE_ORDER`, which is a gate-order
constant for Python QG, not the full module phase list.

**Outputs:**

```text
{module_dir}/python_qg.json
```

**Failure modes:**

- Any deterministic gate remains failing after its allowed correction path.
- A correction regresses a previously passing gate.
- A zero-retry gate fails.
- Correction output is unparseable or unsafe.

**Correction path:**

Deterministic-first layers L2 and L3 govern this phase. ADR-008 allows one
targeted correction attempt per gate under four hard constraints:
patch-bounded, full revalidation, pipeline-assisted dictionary candidates, and
one attempt per gate. The phase terminals if those constraints do not converge.

---

## Phase 5 - `wiki_coverage_gate`

**Purpose:** Verify obligation-level wiki coverage against the implementation
map and run the bounded batched/narrow correction loop where available.

**Inputs:**

- Plan.
- Wiki manifest.
- Raw writer output.
- Module directory artifacts.
- `implementation_map.json`.

**Code path:**

- `linear_pipeline.run_wiki_coverage_with_corrections(...)`
- `linear_pipeline.write_json(module_dir / "wiki_coverage_gate.json", wiki_coverage_gate)`

**Outputs:**

```text
{module_dir}/wiki_coverage_gate.json
```

Correction attempts should also be preserved once
[`v7-build-preservation.md`](../best-practices/pipeline/v7-build-preservation.md)
is implemented:

```text
wiki_coverage_correction_r{N}.json
```

**Failure modes:**

- Wiki obligation coverage remains below the gate after batched and narrow
  correction passes.
- Reviewer fix is oversize.
- YAML correction output is invalid.
- Correction does not improve coverage or regresses prior state.

**Correction path:**

Deterministic-first layer L5 governs this phase. Path 3 defines batched
correction first, narrow per-obligation fallback second, and
`plan_revision_request` terminal after the cap.

---

## Phase 6 - `wiki_coverage_review`

**Purpose:** Run the semantic Goodhart sentinel over wiki coverage: verify that
obligations are substantively woven into content rather than keyword-stuffed.

**Inputs:**

- Plan.
- Plan content.
- Module artifacts.
- Writer family.
- Wiki manifest.
- `wiki_coverage_gate.json`.

**Code path:**

- `_run_wiki_coverage_review(...)`
- `linear_pipeline.render_wiki_coverage_review_prompt(...)`
- `linear_pipeline.parse_wiki_coverage_review_response(response)`
- `linear_pipeline.write_json(module_dir / "wiki_coverage_review.json", wiki_coverage_review)`

**Outputs:**

```text
{module_dir}/wiki_coverage_review.json
```

The phase emits `wiki_coverage_goodhart_sentinel` telemetry with counts for
keyword-stuffing and partial verdicts.

**Failure modes:**

- Reviewer subprocess stalls or fails.
- Review response cannot be parsed.
- `overall_verdict` is `FAIL`.
- Semantic reviewer flags obligation treatment as insufficient.

**Correction path:**

Deterministic-first layer L6 governs this phase. The Goodhart sentinel runs after
deterministic gates converge. If semantic coverage fails, the build should fail
with an explicit signal rather than forcing more writer prompt load.

---

## Phase 7 - `llm_qg`

**Purpose:** Run per-dimension LLM quality review after deterministic gates pass.

**Inputs:**

- Plan.
- Plan content.
- Module artifacts.
- Writer family.
- Reviewer family selected from writer family.
- Per-dimension review prompt template.

**Code path:**

- `_run_llm_qg(...)`
- `linear_pipeline.run_llm_review(...)` through the helper path.
- `linear_pipeline.aggregate_llm_review(report, str(plan["level"]))`
- `linear_pipeline.write_json(module_dir / "llm_qg.json", llm_qg)`

**Outputs:**

```text
{module_dir}/llm_qg.json
```

Once V7 preservation ships, each per-dimension prompt must also be preserved
separately; do not rely only on the aggregate JSON.

**Failure modes:**

- Reviewer subprocess stalls or fails.
- A dimension response cannot be parsed.
- The dimension set does not match `QG_DIMS`.
- Aggregated verdict is not `PASS`.

**Correction path:**

Deterministic-first layer L4 governs this phase. The reviewer emits `<fixes>`
find/replace blocks only; no regeneration, no section rewrite, no full rewrite.
ADR-007 keeps the reviewer-as-fixer contract and caps the fix loop.

---

## Phase 8 - `mdx`

**Purpose:** Assemble the built MDX artifact.

**Inputs:**

- Module directory artifacts.
- Plan path.
- Output mode: default Starlight path or `--out` sandbox path.

**Code path:**

- `linear_pipeline.assemble_mdx(module_dir, mdx_path, plan_path)`

**Outputs:**

Success path without `--out`:

```text
starlight/src/content/docs/{level}/{slug}.mdx
```

Sandbox path with `--out`:

```text
{module_dir}/{slug}.mdx
```

The preservation spec adds the failure path:

```text
curriculum/l2-uk-en/_orchestration/{level}/{slug}/runs/{stamp}/{slug}.mdx
```

**Failure modes:**

- Required authoring artifact missing.
- MDX generator fails.
- Component props or activity references fail render-time validation.
- Output path cannot be created or written.

**Correction path:**

MDX render failures that are deterministic and local may route through ADR-008's
targeted correction path. If the failure is a schema fault or component contract
fault, terminal honestly and fix the code or authoring schema in a separate PR.

---

## State Files Emitted Per Phase

The current code writes these phase-level files in the module directory:

| Phase | Current file(s) |
| --- | --- |
| `writer` | `implementation_map.json`, `writer_output.raw.md`, `writer_prompt.md`, `knowledge_packet.md`, `wiki_manifest.json`, writer artifacts |
| `python_qg` | `python_qg.json` |
| `wiki_coverage_gate` | `wiki_coverage_gate.json` |
| `wiki_coverage_review` | `wiki_coverage_review.json` |
| `llm_qg` | `llm_qg.json` |
| `mdx` | `{slug}.mdx` or Starlight MDX |

The canonical preserved `state.json` schema lives in
[`docs/best-practices/pipeline/v7-build-preservation.md`](../best-practices/pipeline/v7-build-preservation.md).

---

## Worktree Isolation Requirement

Agent-run V7 builds must pass `--worktree`.

The current CLI help says `--worktree` creates:

```text
.worktrees/builds/{level}-{slug}-{YYYYMMDD-HHMMSS}/
```

and a branch:

```text
build/{level}/{slug}-{YYYYMMDD-HHMMSS}
```

PR #1952 shipped the worktree flag. The current implementation creates the
worktree, runs the child build inside it, prints a summary, and leaves cleanup to
the operator. The preservation spec defines the next step: copy artifacts to
`_orchestration/.../runs/{stamp}/` before the worktree is reaped.

See [`docs/best-practices/git-hygiene.md`](../best-practices/git-hygiene.md) for
general working-tree cleanliness rules. This document is the V7-specific
worktree isolation rule.

---

## Writer And Reviewer Family Routing

Do not duplicate the routing matrix here. Current routing is maintained in
[`docs/best-practices/agent-activity-matrix.md`](../best-practices/agent-activity-matrix.md):

- §8.1 covers V7 module writers.
- §8.2 covers V7 module reviewers.
- §8.11 covers track-level writer routing stubs.

V7 code currently exposes writer choices from `linear_pipeline.WRITER_CHOICES`
plus aliases in `v7_build.py`. The current `linear_pipeline.py` writer choices
are `claude-tools`, `gemini-tools`, `codex-tools`, and `grok-tools`. Matrix
entries for `deepseek-tools` and `qwen-tools` remain routing work until the
pipeline exposes them as writers.

---

## V6 To V7 Deltas

V6 is retired. `scripts/build/v6_build.py` says:

> "V6 Pipeline Build — OBSOLETE (retired 2026-05-10)."

and:

> "Use ``scripts/build/v7_build.py`` for all new builds. This file is kept on disk for forensic reference only — do not invoke, extend, or import."

Documented deltas from the V6 header and V7 code:

| Surface | V6 | V7 |
| --- | --- | --- |
| Build unit | Batch/resume-capable legacy build path. | Single-module build path. |
| Generation shape | Skeleton then flesh two-call content generation. | One writer phase, with deterministic implementation-map seeding. |
| Skeleton phase | Explicit `SKELETON` phase, always on unless skipped. | No separate skeleton phase; `implementation_map.json` is seeded inside writer phase. |
| Exercise fill | Separate exercise placeholder fill and verification phases. | Activities are writer artifacts and deterministic gates validate shape. |
| Rewrite strategy | Historical rewrite and convergence machinery existed in V6-era code. | ADR-007/ADR-008 deterministic-first correction; no regeneration ladder. |
| Knowledge source | Legacy RAG/Qdrant path in old flow. | Compiled wiki plus source registries in `linear_pipeline.build_knowledge_packet`. |
| Publishing | V6 publish assembled four-tab MDX from V6 artifacts. | V7 `mdx` phase calls `linear_pipeline.assemble_mdx`. |
| Worktree isolation | Not the V7 `--worktree` build wrapper. | `--worktree` flag creates isolated build worktree. |

Archaeology caveat: this table is based on the V6 header and the V7 wrapper and
does not claim to enumerate every removed V6 helper. If a future migration needs
line-by-line V6 cleanup, write a separate forensic doc rather than expanding
this spec.

---

## What V7 Is Not

V7 is not a multi-module batch pipeline. Build one module at a time until the
single-module path is fully locked.

V7 is not a parallel-build pipeline. Worktree isolation is per module; it does
not mean one invocation fans out across many modules.

V7 is not the wiki compilation pipeline. Wiki compilation lives under
`scripts/wiki/`. V7 consumes compiled wiki/source material when building the
knowledge packet and manifest.

V7 is not a rewrite ladder. It does not bring back V6 `section_rewrite`,
`full_rewrite`, or `writer_swap` as correction strategies.

V7 is not a place to mutate source plans during a build. A bad plan terminals as
plan work.

---

## Prompt Files

Current prompt-related files under `scripts/build/phases/` include:

```text
linear-write.md
linear-write-grok.md
linear-writer-correction.md
linear-writer-correction-grok.md
linear-correction-wiki-coverage.md
linear-correction-wiki-coverage-narrow.md
linear-review-wiki-coverage.md
linear-review-dim.md
```

The same directory also contains V6 prompt files. Do not infer current V7 phase
order from directory listing alone. The current V7 phase order comes from
`scripts/build/v7_build.py`.

---

## References

- [`docs/decisions/2026-04-23-rewrite-strategies-kill-or-revert.md`](../decisions/2026-04-23-rewrite-strategies-kill-or-revert.md) - ADR-007, reviewer-as-fixer and no rewrite ladder.
- [`docs/decisions/2026-04-28-targeted-gate-correction-paths.md`](../decisions/2026-04-28-targeted-gate-correction-paths.md) - ADR-008, targeted gate-specific correction paths.
- [`docs/decisions/2026-05-17-path3-per-obligation-review-loop.md`](../decisions/2026-05-17-path3-per-obligation-review-loop.md) - Path 3, per-obligation wiki loop.
- [`docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md`](../decisions/2026-05-13-ulp-derived-student-aware-immersion.md) - ULP-derived immersion model.
- [`docs/decisions/2026-05-18-deterministic-first-iteration.md`](../decisions/2026-05-18-deterministic-first-iteration.md) - deterministic-first synthesis.
- [`docs/best-practices/pipeline/v7-build-preservation.md`](../best-practices/pipeline/v7-build-preservation.md) - preserved run archive schema.
- [`scripts/build/v7_build.py`](../../scripts/build/v7_build.py) - CLI wrapper.
- [`scripts/build/linear_pipeline.py`](../../scripts/build/linear_pipeline.py) - implementation library.

---

## Verification Evidence

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/architecture/ARCHITECTURE.md | sed -n '1,30p'
raw: 11  > Read this doc only for V5/V6 historical context. Specific lines below that hardcode "Gemini builds → Claude reviews" are V5/V6 paradigm and are NOT current reboot policy.
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba scripts/build/v7_build.py | sed -n '1,260p'
raw: 2  """CLI wrapper for the V7 linear module pipeline."""
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: rg -n "PIPELINE|PHASE|phase|argparse|--worktree|plan|knowledge_packet|writer|python_qg|wiki_coverage_gate|wiki_coverage_review|llm_qg|mdx" scripts/build/v7_build.py
raw: 670:        phase = "plan"
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: rg -n "PIPELINE|PHASE|phase|argparse|--worktree|plan|knowledge_packet|writer|python_qg|wiki_coverage_gate|wiki_coverage_review|llm_qg|mdx" scripts/build/v7_build.py
raw: 678:        phase = "knowledge_packet"
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: rg -n "PIPELINE|PHASE|phase|argparse|--worktree|plan|knowledge_packet|writer|python_qg|wiki_coverage_gate|wiki_coverage_review|llm_qg|mdx" scripts/build/v7_build.py
raw: 718:        phase = "writer"
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: rg -n "PIPELINE|PHASE|phase|argparse|--worktree|plan|knowledge_packet|writer|python_qg|wiki_coverage_gate|wiki_coverage_review|llm_qg|mdx" scripts/build/v7_build.py
raw: 780:        phase = "python_qg"
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: rg -n "PIPELINE|PHASE|phase|argparse|--worktree|plan|knowledge_packet|writer|python_qg|wiki_coverage_gate|wiki_coverage_review|llm_qg|mdx" scripts/build/v7_build.py
raw: 795:        phase = "wiki_coverage_gate"
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: rg -n "PIPELINE|PHASE|phase|argparse|--worktree|plan|knowledge_packet|writer|python_qg|wiki_coverage_gate|wiki_coverage_review|llm_qg|mdx" scripts/build/v7_build.py
raw: 812:        phase = "wiki_coverage_review"
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: rg -n "PIPELINE|PHASE|phase|argparse|--worktree|plan|knowledge_packet|writer|python_qg|wiki_coverage_gate|wiki_coverage_review|llm_qg|mdx" scripts/build/v7_build.py
raw: 852:        phase = "llm_qg"
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: rg -n "PIPELINE|PHASE|phase|argparse|--worktree|plan|knowledge_packet|writer|python_qg|wiki_coverage_gate|wiki_coverage_review|llm_qg|mdx" scripts/build/v7_build.py
raw: 877:        phase = "mdx"
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba scripts/build/linear_pipeline.py | sed -n '1,220p'
raw: 1  """Linear Phase 4 module pipeline.
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: ls scripts/build/phases
raw: linear-write.md
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba scripts/build/v6_build.py | sed -n '1,70p'
raw: 2  """V6 Pipeline Build — OBSOLETE (retired 2026-05-10).
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: gh pr view 1952 --json number,title,state,mergedAt,url
raw: {"mergedAt":"2026-05-13T09:25:50Z","number":1952,"state":"MERGED","title":"feat(v7_build): --worktree flag for isolated module builds","url":"https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/1952"}
```

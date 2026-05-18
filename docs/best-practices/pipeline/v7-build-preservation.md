# V7 Build Preservation

**Status:** SPECIFICATION - implementation partially shipped.
**Date:** 2026-05-19
**Scope:** V7 single-module build artifact preservation.
**Source:** `audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md` gap
§1.1 and the locked handoff
`docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md`.

---

## Scope

V7 build runs preserve orchestration artifacts under:

```text
curriculum/l2-uk-en/_orchestration/{level}/{slug}/runs/{stamp}/
```

The underscore prefix is part of the contract. The locked source says the
prefix keeps these files out of the `mcp__sources__*` retrieval namespace. Do
not move the run archive under the published module directory, the wiki source
tree, or a non-underscored `orchestration/` path.

This doc covers the preserved build record only. It does not define the V7
phase order; that lives in
[`docs/architecture/v7-pipeline.md`](../../architecture/v7-pipeline.md). It
does not define correction semantics; those live in
[`docs/decisions/2026-05-18-deterministic-first-iteration.md`](../../decisions/2026-05-18-deterministic-first-iteration.md).

The preservation directory is a durable trace for one build attempt. It is not a
second source of truth for lesson content. The source artifacts still live in
the normal V7 module output directory during the build, and successful MDX still
publishes to Starlight.

---

## Locked Source

The following block is the locked source material from the 2026-05-19 handoff.
This doc canonicalizes it without redesigning it.

> **Path:** `curriculum/l2-uk-en/_orchestration/{level}/{slug}/runs/{stamp}/` (underscore prefix to keep out of `mcp__sources__*` retrieval namespace, per claude headless's Q5).
>
> **Build flow:**
> - Build runs in worktree (`.worktrees/builds/...`) — branch isolation preserved
> - Wrapper (in main project dir, on main branch) copies orchestration dir from worktree to main on phase boundary + on terminal outcome
> - Always merge to main (no preserved branches that accumulate over time)
> - One commit per build (success OR failure)
> - Worktree reaped on completion; branch dies with it
>
> **Cleanup:** last N=10 runs per slug; older runs squashed/deleted via scheduled cron (defer details to month 3).
>
> **state.json schema (V7):**
> ```json
> {
>   "mode": "v7",
>   "track": "a1",
>   "slug": "my-morning",
>   "run_id": "20260519-HHMMSS",
>   "parent_run_id": null | "<prior-run-id>",
>   "started_at": "...",
>   "finished_at": "...",
>   "status": "complete | failed | partial",
>   "failed_phase": "<phase>" | null,
>   "failure_class": "<FailureClass enum>" | null,
>   "agent": "claude-tools | codex-tools | gemini-tools | deepseek-tools | qwen-tools",
>   "model": "<model id>",
>   "effort": "low | medium | high | xhigh | max | unknown",
>   "prompt_sha": "<sha of writer prompt template>",
>   "phases": { ... per-phase status + timestamps + attempts ... }
> }
> ```
>
> **File naming convention:** hyphenated to avoid `.gitignore` collision (e.g., `v7-writer-prompt.md`, not `writer_prompt.md` — `*_PROMPT.md` is gitignored per codex's catch).
>
> **MDX-on-failure:** ALWAYS assemble the MDX, regardless of gate pass/fail. Success → `starlight/src/content/docs/{level}/{slug}.mdx`. Failure → `_orchestration/.../runs/{stamp}/{slug}.mdx` with frontmatter `build_status: failed` + `failed_phase: <phase>`. NEVER modify the source `module.md` frontmatter (codex's argument: gate-consumed, parser risk).
>
> **Auto-generated:** `commit_diff_summary.json` per build summarizing changes from `parent_run_id`. `git diff --stat` parsing, ~30 LOC.
>
> **Correction iterations preserved:** `python_qg_correction_r{N}.json`, `wiki_coverage_correction_r{N}.json`. Currently swallowed; this is the actual prompt-engineering blind spot.
>
> **Per-dim reviewer prompts:** preserved as separate files, not aggregated into `llm_qg.json`.

---

## Build Flow

The build flow is intentionally worktree-first:

1. The build runs in `.worktrees/builds/...`.
2. The wrapper in the main project directory copies the orchestration directory
   from the build worktree to the main checkout on every phase boundary.
3. The wrapper copies again when the build reaches a terminal outcome.
4. The build result is always merged to `main`.
5. The build produces one commit, whether the build succeeds or fails.
6. The worktree is removed on completion; the build branch is not preserved as
   the archive.

The archive is therefore the durable evidence trail. The build branch is an
isolation mechanism, not a retention mechanism.

The live shipped part of this flow is the V7 worktree isolation flag. PR #1952
merged `scripts/build/v7_build.py --worktree`, which creates a build worktree at
`.worktrees/builds/{level}-{slug}-{timestamp}/` and a branch named
`build/{level}/{slug}-{timestamp}`. The preservation wrapper that copies the
archive to `_orchestration/.../runs/{stamp}/` is not shipped yet.

Do not preserve long-lived build branches as a substitute for the archive. The
locked design says "Always merge to main" and "Worktree reaped on completion;
branch dies with it." The branch can disappear; the run archive cannot.

---

## Run Directory Contract

Each run directory is a closed record for one V7 build attempt:

```text
curriculum/l2-uk-en/_orchestration/{level}/{slug}/runs/{stamp}/
├── state.json
├── commit_diff_summary.json
├── v7-writer-prompt.md
├── writer_output.raw.md
├── knowledge_packet.md
├── wiki_manifest.json
├── implementation_map.json
├── python_qg.json
├── python_qg_correction_r{N}.json
├── wiki_coverage_gate.json
├── wiki_coverage_correction_r{N}.json
├── wiki_coverage_review.json
├── llm_qg.json
├── llm-qg-{dimension}-prompt.md
└── {slug}.mdx
```

This tree is illustrative for preserved artifact classes. The exact phase list
and exact phase outputs are governed by
[`docs/architecture/v7-pipeline.md`](../../architecture/v7-pipeline.md) and the
current V7 code. Do not add phase names here that are not present in
`scripts/build/v7_build.py`.

The archive must include enough data for a later agent to answer these
questions without re-running the build:

- Which source plan and writer prompt were used?
- Which writer and reviewer families ran?
- Which phase failed, if any?
- Which deterministic gates passed before failure?
- Which correction attempts ran and what did they change?
- Which reviewer prompts were sent per dimension?
- Which MDX would have rendered on the site if the build had succeeded?
- What changed relative to `parent_run_id`?

---

## `state.json` Schema

`state.json` is the canonical run index. It must exist for every preserved run.

The locked V7 schema is:

```json
{
  "mode": "v7",
  "track": "a1",
  "slug": "my-morning",
  "run_id": "20260519-HHMMSS",
  "parent_run_id": null | "<prior-run-id>",
  "started_at": "...",
  "finished_at": "...",
  "status": "complete | failed | partial",
  "failed_phase": "<phase>" | null,
  "failure_class": "<FailureClass enum>" | null,
  "agent": "claude-tools | codex-tools | gemini-tools | deepseek-tools | qwen-tools",
  "model": "<model id>",
  "effort": "low | medium | high | xhigh | max | unknown",
  "prompt_sha": "<sha of writer prompt template>",
  "phases": { ... per-phase status + timestamps + attempts ... }
}
```

Field rules:

| Field | Rule |
| --- | --- |
| `mode` | Literal `"v7"`. |
| `track` | Lowercase curriculum level or track, for example `a1`, `b1`, `hist`. |
| `slug` | Module slug as passed to `v7_build.py`. |
| `run_id` | UTC-ish sortable stamp, matching the run directory stamp. |
| `parent_run_id` | Previous archived run for this slug, or `null` for the first preserved run. |
| `started_at` | Timestamp recorded before the first phase starts. |
| `finished_at` | Timestamp recorded at terminal outcome; `null` only while a run is still active. |
| `status` | One of the locked values: `complete`, `failed`, or `partial`. |
| `failed_phase` | The phase that emitted the terminal failure, or `null`. |
| `failure_class` | Failure class enum name if known, or `null`. |
| `agent` | Writer family for the build. Reviewer families belong inside `phases`. |
| `model` | Concrete model id used by the writer. |
| `effort` | Effort tier used by the writer, or `unknown` when the adapter does not expose it. |
| `prompt_sha` | Hash of the rendered writer prompt or template source, whichever the implementation standardizes. |
| `phases` | Per-phase status, timestamps, attempts, and artifact references. |

The schema is deliberately a run index, not a dump of every gate result. Heavy
phase payloads stay in their own JSON files so `state.json` remains readable and
diffable.

---

## Phase Boundary Copies

Copy-on-phase-boundary is required because the failure class this spec fixes is
"artifact disappeared before anyone could inspect it." A build can fail while the
writer output is only in memory, while the correction JSON is temporary, or while
a worktree is about to be reaped. The archive closes that prompt-engineering
blind spot.

At minimum, the wrapper copies after these transition classes:

| Transition | Required archive action |
| --- | --- |
| Run start | Create run directory and initial `state.json`. |
| Phase start | Update `state.json.phases[phase].started_at`. |
| Phase success | Copy phase outputs and update status. |
| Correction attempt | Copy each attempt artifact with its round number. |
| Phase failure | Copy available failure payloads before returning the exit code. |
| Terminal success | Copy final MDX and `commit_diff_summary.json`. |
| Terminal failure | Copy failed MDX, failure state, and `commit_diff_summary.json`. |

The implementation can optimize the copy mechanics. The behavioral contract is
that a process crash after a phase boundary does not erase the artifacts needed
to debug the previous phase.

---

## File Naming Convention

Preserved files use hyphenated names:

```text
v7-writer-prompt.md
llm-qg-naturalness-prompt.md
wiki-coverage-review-prompt.md
commit-diff-summary-source.txt
```

Do not use uppercase prompt suffix names such as:

```text
WRITER_PROMPT.md
NATURALNESS_PROMPT.md
```

`.gitignore` contains `*_PROMPT.md`. A preserved prompt named with that suffix
will be silently omitted from the diff and defeat the purpose of the archive.

Existing V7 runtime artifacts such as `writer_prompt.md` can remain the live
working filenames while the pipeline is running. Preservation filenames should
be hyphenated when copied into `_orchestration`.

---

## MDX On Failure

MDX assembly is not success-only. The locked policy is:

> **MDX-on-failure:** ALWAYS assemble the MDX, regardless of gate pass/fail. Success → `starlight/src/content/docs/{level}/{slug}.mdx`. Failure → `_orchestration/.../runs/{stamp}/{slug}.mdx` with frontmatter `build_status: failed` + `failed_phase: <phase>`. NEVER modify the source `module.md` frontmatter (codex's argument: gate-consumed, parser risk).

Success path:

```text
starlight/src/content/docs/{level}/{slug}.mdx
```

Failure path:

```text
curriculum/l2-uk-en/_orchestration/{level}/{slug}/runs/{stamp}/{slug}.mdx
```

Failed MDX must include frontmatter keys:

```yaml
build_status: failed
failed_phase: <phase>
```

The source `module.md` frontmatter is not the place for failure metadata. That
file is consumed by gates and parsers. Adding transient build state to it creates
parser risk and can change the gate input while the gate is still being debugged.

---

## `commit_diff_summary.json`

Every preserved build writes `commit_diff_summary.json`. The locked source says
this is generated per build by parsing `git diff --stat` and should be small.

Expected shape:

```json
{
  "run_id": "20260519-HHMMSS",
  "parent_run_id": "<prior-run-id-or-null>",
  "base_ref": "<git ref or sha>",
  "head_ref": "<git ref or sha>",
  "files_changed": 0,
  "insertions": 0,
  "deletions": 0,
  "paths": [
    {
      "path": "starlight/src/content/docs/a1/my-morning.mdx",
      "status": "modified",
      "insertions": 0,
      "deletions": 0
    }
  ]
}
```

The shape is intentionally limited to fields derivable from git state. It is not
a semantic review report and it must not duplicate `python_qg.json`,
`wiki_coverage_gate.json`, or `llm_qg.json`.

For failed builds, the diff summary still matters. It tells the next agent which
source and archive files changed before the failure, and it keeps failure
commits reviewable.

---

## Correction Iterations

Correction iterations are first-class artifacts. Preserve:

```text
python_qg_correction_r{N}.json
wiki_coverage_correction_r{N}.json
```

The round number is required. A later reviewer must be able to reconstruct:

- the first deterministic failure,
- the correction prompt or correction payload,
- the artifact mutation,
- the revalidation result,
- the terminal reason if the correction did not converge.

Do not aggregate correction attempts into the final gate JSON. Aggregation hides
the failed attempts, which are often the most useful prompt-engineering evidence.

The 2026-05-19 handoff names swallowed correction iterations as "the actual
prompt-engineering blind spot." This spec closes that gap by making every
attempt an inspectable file.

---

## Per-Dimension Reviewer Prompts

LLM QG reviewer prompts are preserved as separate prompt files. Do not store only
the aggregate `llm_qg.json`.

Minimum preservation:

```text
llm-qg-{dimension}-prompt.md
llm-qg.json
```

Reason: the aggregate result answers what the reviewer concluded. The prompt
answers why the reviewer saw that task. When a dimension fails, prompt drift,
missing context, or wrong reviewer routing can be the root cause. Aggregation
erases that evidence.

The dimension list is owned by the V7 pipeline code and shared threshold modules,
not by this preservation doc. If the code adds or removes a dimension, the
preservation layer follows the code.

---

## Cleanup Policy

Keep the last `N=10` runs per slug.

Older runs may be squashed or deleted by a scheduled cleanup job. The cron shape,
schedule, retention exception list, and operator UI are deferred to month 3.
This doc intentionally does not invent those details.

Cleanup must preserve reviewability before deletion. At minimum:

- keep enough state to identify the latest success,
- keep the latest failure if it is newer than the latest success,
- do not delete a run that is referenced by an open PR, audit report, or decision
  card,
- do not delete a run before `commit_diff_summary.json` has been generated.

The retention rule is per slug, not global. A high-churn module can age out its
own older attempts without deleting a different module's only preserved failure.

---

## Open Implementation Status

Shipped:

- `scripts/build/v7_build.py --worktree` is live. PR #1952 merged on
  2026-05-13 with title `feat(v7_build): --worktree flag for isolated module
  builds`.
- The current V7 wrapper creates build worktrees under `.worktrees/builds/...`
  and runs the child build inside that worktree.

Pending:

- `_orchestration/{level}/{slug}/runs/{stamp}/` archive creation.
- Copy-on-phase-boundary.
- Copy-on-terminal-outcome.
- `state.json` writer.
- `commit_diff_summary.json` generator.
- Failed-MDX assembly into the run directory.
- Prompt preservation with hyphenated names.
- Correction attempt preservation.
- Per-dimension reviewer prompt preservation.
- Cleanup job for last `N=10` runs per slug.

Do not mark the preservation pattern as implemented until the pending list above
exists in code and a failed V7 build leaves a complete archived run directory.

---

## Non-Goals

This doc does not:

- define the V7 phase order,
- define gate thresholds,
- define writer or reviewer routing,
- define the cron implementation,
- define wiki compilation preservation,
- define Starlight publishing behavior outside the final MDX path,
- authorize preserving long-lived build branches.

Those are separate surfaces. Cross-link them; do not merge them into this file.

---

## References

- [`docs/architecture/v7-pipeline.md`](../../architecture/v7-pipeline.md) - V7
  phase architecture.
- [`docs/decisions/2026-05-18-deterministic-first-iteration.md`](../../decisions/2026-05-18-deterministic-first-iteration.md) - correction ladder.
- [`docs/best-practices/git-hygiene.md`](../git-hygiene.md) - working tree and
  artifact hygiene.
- [`scripts/build/v7_build.py`](../../../scripts/build/v7_build.py) - current
  V7 CLI wrapper.
- [`scripts/build/linear_pipeline.py`](../../../scripts/build/linear_pipeline.py)
  - current pipeline implementation.

---

## Verification Evidence

Each claim above is backed by a command run from this dispatch worktree:

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md | sed -n '52,151p'
raw: 60  ### V7 orchestration folder preservation (full plan)
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md | sed -n '52,151p'
raw: 62  **Path:** `curriculum/l2-uk-en/_orchestration/{level}/{slug}/runs/{stamp}/` (underscore prefix to keep out of `mcp__sources__*` retrieval namespace, per claude headless's Q5).
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md | sed -n '52,151p'
raw: 64  **Build flow:**
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md | sed -n '52,151p'
raw: 73  **state.json schema (V7):**
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba docs/session-state/2026-05-19-handoff-gap-audit-and-qwen-integration.md | sed -n '52,151p'
raw: 96  **MDX-on-failure:** ALWAYS assemble the MDX, regardless of gate pass/fail. Success → `starlight/src/content/docs/{level}/{slug}.mdx`. Failure → `_orchestration/.../runs/{stamp}/{slug}.mdx` with frontmatter `build_status: failed` + `failed_phase: <phase>`. NEVER modify the source `module.md` frontmatter (codex's argument: gate-consumed, parser risk).
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: rg -n '\*_PROMPT\.md' .gitignore
raw: .gitignore:111:*_PROMPT.md
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: gh pr view 1952 --json number,title,state,mergedAt,url
raw: {"mergedAt":"2026-05-13T09:25:50Z","number":1952,"state":"MERGED","title":"feat(v7_build): --worktree flag for isolated module builds","url":"https://github.com/learn-ukrainian/learn-ukrainian.github.io/pull/1952"}
```

```text
cwd: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/four-deliverable-docs-20260519
command: nl -ba scripts/build/v7_build.py | sed -n '528,908p'
raw: 548              "  Pass --worktree to create .worktrees/builds/{level}-{slug}-{timestamp}/ "
```

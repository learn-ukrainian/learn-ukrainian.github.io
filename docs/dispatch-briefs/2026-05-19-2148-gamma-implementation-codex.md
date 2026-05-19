# Dispatch — #2148 γ: render `implementation_map.json` into the V7 writer prompt

**Agent:** codex
**Model:** `gpt-5.5`
**Effort:** `xhigh`
**Mode:** `danger` (worktree-isolated, can commit + push + open PR)
**Task ID:** `2148-gamma-impl-20260519`
**Decision card:** `docs/decisions/pending/2026-05-18-wiki-obligation-emission-contract.md` (γ + bridge A approved by user 2026-05-19; this dispatch implements that decision)
**Issue:** #2148
**Estimated effort:** 1-2 hours (mirrors the shape and risk profile of #1969 and #2127)
**Reviewer policy:** human-merge after CI green; no `--admin` bypass (per `memory/MEMORY.md` #M-0.5).

---

## Why this exists (one paragraph)

m20 build #7 hard-failed at `wiki_coverage_gate` with 22.22% coverage (4 of 18 obligations) — see issue #2148 forensics. The Path 3 architecture (#2117 / #2123-2125) gave the **gate** a per-obligation contract via the `implementation_map.json` sidecar (shipped in PR #2108), but never surfaced that contract to the **writer**. The writer therefore translates obligations → artifact emissions in its head, and that translation step is the failure point. Shape γ from the decision card eliminates the translation step by rendering the seeded `implementation_map.json` directly into the writer prompt under a new placeholder `{IMPLEMENTATION_MAP_CONTRACT}`. Per Path 3's design principle: *"writer fills slots, doesn't invent coverage structure"*.

The seeder already runs unconditionally before every writer invocation. The seed file already lands on disk at `module_dir/implementation_map.json` (see `scripts/build/v7_build.py:722-724`). This dispatch wires the existing artifact into the writer's view — no new schema, no migration.

---

## Pre-flight #M-4 evidence preamble (READ FIRST — mandatory)

This dispatch must obey `memory/MEMORY.md` #M-4 (deterministic-over-hallucination) and `docs/best-practices/deterministic-over-hallucination.md`. Every verifiable claim in the PR body MUST quote a tool-output triple (command + cwd + raw output). The claims and their tools:

| Claim in PR body | Required deterministic tool | Output format |
|---|---|---|
| "Tests pass" | `.venv/bin/python -m pytest tests/build/test_implementation_map.py tests/build/test_implementation_map_render.py tests/test_writer_prompt_structured_cot.py -v` from repo root | quote final `N passed in M.MMs` line raw |
| "Lint clean" | `.venv/bin/ruff check scripts/build/ tests/build/` from repo root | quote `All checks passed!` or zero-error final line raw |
| "Placeholder is fully replaced after render" | the new test `test_placeholder_is_fully_replaced` | quote the assertion line + pass status raw |
| "Every manifest row appears in rendered prompt" | the new test `test_every_seeded_row_appears_in_prompt` | quote the assertion line + pass status raw |
| "Commit landed" | `git log -1 --oneline` from the worktree | quote line raw |
| "PR opened" | `gh pr view --json url -q .url` | quote the URL raw |

Do NOT write "I confirmed X" without a quoted command+output triple. The reviewer will grep for evidence. A polished prose claim with no `$ <cmd>` + raw line is rejected.

---

## Anchor facts (deterministically verified for you)

The orchestrator pre-verified the following with tool calls. You do NOT need to re-derive these — but DO re-check before editing each file (per `code-editing-safety.md` rule 2: re-read before every edit).

1. **Seeder location** — `scripts/build/phases/implementation_map.py::seed_implementation_map` (lines 113-141). Returns `dict[str, Any]` with keys `schema_version`, `slug`, `wiki_path`, `manifest_obligation_count`, `entries`. Each entry is an `ImplementationMapEntry` TypedDict with `obligation_id`, `obligation_type`, `artifact`, `location_hint`, `treatment_template`, `manifest_payload`.

2. **Seeder is already called BEFORE writer prompt render** — `scripts/build/v7_build.py:722-730`:
   ```python
   impl_map = seed_implementation_map(wiki_manifest_data, plan=plan)
   impl_map_path = module_dir / "implementation_map.json"
   write_implementation_map(impl_map, impl_map_path)
   tracker.emit("implementation_map_seeded", ...)
   prompt = _writer_prompt(plan=plan, plan_content=..., knowledge_packet=..., wiki_manifest=..., writer=...)
   ```
   The `impl_map` dict is in scope at the `_writer_prompt(...)` call site. You just need to plumb it through.

3. **Writer prompt rendering chain** — `_writer_prompt` (`v7_build.py:411`) → `linear_pipeline.render_writer_prompt` (`linear_pipeline.py:1524`) → `linear_pipeline.writer_context` (`linear_pipeline.py:2497`) → returns the placeholder dict consumed by `render_phase_prompt`. The placeholder dict currently has keys: `LEVEL, MODULE_NUM, MODULE_SLUG, TOPIC_TITLE, PHASE, WORD_TARGET, PLAN_CONTENT, KNOWLEDGE_PACKET, WIKI_MANIFEST, LEARNER_STATE, IMMERSION_RULE, CONTRACT_YAML, ALLOWED_ACTIVITY_TYPES, FORBIDDEN_ACTIVITY_TYPES, INLINE_ALLOWED_TYPES, WORKBOOK_ALLOWED_TYPES, ACTIVITY_COUNT_TARGET, VOCAB_COUNT_TARGET, COMPONENT_PROPS_SCHEMA`. Add **`IMPLEMENTATION_MAP_CONTRACT`** as a new entry.

4. **Writer prompt templates** that consume `{WIKI_MANIFEST}` today:
   - `scripts/build/phases/linear-write.md:318` — claude-tools default (V7 writer per `2026-05-06-writer-selection-codex-gpt55.md`)
   - `scripts/build/phases/linear-write-grok.md:221` — grok-tools variant
   Both must receive the new section (see step 4 below). The correction prompts `linear-writer-correction.md` / `linear-writer-correction-grok.md` do NOT consume `{WIKI_MANIFEST}` today — keep that out of scope for this PR unless the correction loop also fails on the same gap (verify with `grep -n "WIKI_MANIFEST\|implementation_map" scripts/build/phases/linear-writer-correction*.md`).

5. **Existing seeder contract test** — `tests/build/test_implementation_map.py` — use this file's fixture-manifest pattern (`_fixture_manifest()`) for the new render test. Do NOT duplicate the fixture; import it.

6. **Existing render-shape tests** to keep green — `tests/test_writer_prompt_structured_cot.py`, `tests/test_writer_prompt_preemit_checklist.py`. Adding a new placeholder must NOT change their assertions about the existing structured-CoT blocks or pre-emit checklist lines. If they fail, the contract section was inserted in the wrong place.

---

## What to build (worked example)

### Step 1 — `scripts/build/phases/implementation_map.py`

Add a deterministic renderer at the bottom of the module:

```python
def render_for_writer_prompt(payload: dict[str, Any]) -> str:
    """Render the implementation map as a human-readable contract block for the writer.

    The writer prompt embeds this verbatim under {IMPLEMENTATION_MAP_CONTRACT}.
    Format: one row per entry, sorted by obligation_id for determinism. Each row is
    pedagogically self-contained — obligation_id, artifact, location_hint, and a
    flattened treatment_template the writer can lift directly.
    """
    validate_implementation_map(payload)
    rows: list[str] = []
    for entry in sorted(payload["entries"], key=lambda e: str(e.get("obligation_id") or "")):
        # rendering shape — concrete:
        # - obligation_id: <id>  (obligation_type: <type>)
        #   artifact: <artifact>
        #   location_hint: <hint>
        #   treatment_template:
        #     <key>: <value>
        #     ...
        # Use 2-space indent for the inner key:value pairs to keep the writer's eye
        # tracking the structure inside the rendered block.
        ...
    body = "\n".join(rows)
    header = (
        f"Manifest obligations: {payload['manifest_obligation_count']}.\n"
        "Each row below is a pre-resolved slot the writer MUST fill at the artifact "
        "indicated by `artifact`, located by `location_hint`, populated using "
        "`treatment_template` as the structural blueprint."
    )
    return f"{header}\n\n{body}\n"
```

**Determinism contract:** the output is sorted by `obligation_id` so two builds with the same manifest produce byte-identical rendered text. The shape is plain-text (NOT JSON dump); the writer reads it as if it were a numbered checklist. Cap individual `treatment_template` value lines to a sensible length (use a reasonable default; the existing seeder doesn't emit overly long values, so simple `str()` should suffice — no truncation needed for the m20 case).

**Why not just `json.dumps`:** the writer needs to translate `treatment_template` keys → prose / YAML items / module sections. JSON-dump form pushes the parser-overhead onto the LLM. Plain-text key:value form is what the writer prompt's other rendered blocks (WIKI_MANIFEST, KNOWLEDGE_PACKET) already use — match the existing house style.

### Step 2 — `scripts/build/linear_pipeline.py`

(a) `writer_context()` (line 2497) — add `implementation_map` parameter:

```python
def writer_context(
    plan: Mapping[str, Any],
    plan_content: str,
    knowledge_packet: str,
    wiki_manifest: str | Mapping[str, Any] | None = None,
    *,
    implementation_map: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    ...
    if implementation_map is None:
        # If caller didn't pass a seeded map, render a sentinel that fails loudly at gate
        # time rather than silently embedding empty content. The seeder is always called
        # in the v7_build.py path; this branch is defensive for direct callers / tests.
        impl_map_contract = "(no implementation_map provided to render_writer_prompt — gate will fail)"
    else:
        from scripts.build.phases.implementation_map import render_for_writer_prompt
        impl_map_contract = render_for_writer_prompt(dict(implementation_map))
    return {
        ...existing keys...,
        "IMPLEMENTATION_MAP_CONTRACT": impl_map_contract,
    }
```

(b) `render_writer_prompt()` (line 1524) — accept + forward:

```python
def render_writer_prompt(
    *,
    plan: Mapping[str, Any],
    plan_content: str,
    knowledge_packet: str,
    wiki_manifest: str | Mapping[str, Any] | None = None,
    implementation_map: Mapping[str, Any] | None = None,
    writer: str = "claude-tools",
) -> str:
    return render_phase_prompt(
        writer_prompt_path(writer),
        writer_context(
            plan, plan_content, knowledge_packet, wiki_manifest,
            implementation_map=implementation_map,
        ),
    )
```

### Step 3 — `scripts/build/v7_build.py`

`_writer_prompt()` (line 411) — accept + forward `implementation_map`; call site at line 731 — pass the in-scope `impl_map`:

```python
prompt = _writer_prompt(
    plan=plan,
    plan_content=plan_content,
    knowledge_packet=knowledge_packet,
    wiki_manifest=wiki_manifest,
    implementation_map=impl_map,    # <-- new
    writer=writer,
)
```

### Step 4 — writer prompt templates

**Edit `scripts/build/phases/linear-write.md`** — insert a new section immediately AFTER the `## Wiki Obligations Manifest` block (currently lines 316-319, ending after `{WIKI_MANIFEST}`) and BEFORE the `### External Resources — multimedia search obligation` block. Use this exact body:

```markdown
## Implementation Map Contract

The pipeline has pre-resolved every wiki obligation listed above into a concrete contract: `(obligation_id, artifact, location_hint, treatment_template)`. Your job for this section of the protocol is to **emit each row's required element at the row's `location_hint`, populated using the row's `treatment_template`**. Do NOT invent new obligations beyond those in the manifest. Do NOT skip rows. The deterministic `wiki_coverage_gate` verifies coverage row-by-row against this contract; missing rows produce `fix_proposals` and the rebuild is wasted.

The contract below is generated upstream by `seed_implementation_map` and is byte-stable across runs — if you see a row whose `treatment_template` looks pedagogically thin, do NOT invent extra structure: copy the template's keys/values into the artifact and let the gate report any structural gap so the seeder (not your prose) gets fixed.

{IMPLEMENTATION_MAP_CONTRACT}
```

The rationale prose is intentional — the writer model has been observed (m20 builds #2-#17) to "improve" pre-resolved structure with extra paraphrase. The "do NOT invent" framing matches the same anti-paraphrase guidance already in `## Wiki Obligations Manifest` and the bad-form marker section.

**Edit `scripts/build/phases/linear-write-grok.md`** — apply the same insertion immediately after its `{WIKI_MANIFEST}` line (around line 221). Verify the surrounding section headings; the grok variant uses the same overall structure but you must re-read it before editing (`code-editing-safety.md` rule 2).

**Do NOT edit** `linear-writer-correction.md` / `linear-writer-correction-grok.md` in this PR — verify they don't currently consume `{WIKI_MANIFEST}` (grep confirms zero hits as of `f65bccb617`). If correction loops surface the same contract-gap on a future build, that's a separate follow-up.

### Step 5 — `tests/build/test_implementation_map_render.py` (NEW file)

Place at `tests/build/test_implementation_map_render.py`. Import the fixture manifest from `tests/build/test_implementation_map.py` (do NOT duplicate it — pytest test files at the same path can import each other via `from .test_implementation_map import _fixture_manifest`).

Required test cases:

1. **`test_render_contains_one_row_per_entry`** — call `seed_implementation_map(_fixture_manifest(), plan=None)`, then `render_for_writer_prompt(payload)`, assert every `entry["obligation_id"]` substring is present in the rendered text.

2. **`test_render_is_deterministic`** — call `render_for_writer_prompt` twice on the same payload, assert byte-equality. This guards against dict-iteration nondeterminism leaking into the seeder cache.

3. **`test_render_sorted_by_obligation_id`** — verify rows appear in sorted order by `obligation_id` (sample two ids that sort non-lexically against insertion order in the fixture, e.g. `step-4` should appear after `step-1` regardless of fixture ordering).

4. **`test_placeholder_is_fully_replaced_in_writer_prompt`** — call `render_writer_prompt(plan=..., plan_content=..., knowledge_packet=..., wiki_manifest=..., implementation_map=seeded_payload, writer="claude-tools")`, assert `"{IMPLEMENTATION_MAP_CONTRACT}"` is NOT a substring of the returned prompt (i.e. fully substituted) AND a sample row (`obligation_id` from the fixture) IS a substring.

5. **`test_every_seeded_row_appears_in_writer_prompt`** — same render call as above, iterate over `seeded_payload["entries"]`, assert each `entry["obligation_id"]` appears at least once in the rendered prompt.

6. **`test_grok_variant_also_renders_contract`** — repeat step 4 with `writer="grok-tools"`; confirms the grok prompt template received the same edit.

7. **`test_writer_context_without_map_emits_sentinel`** — call `writer_context(...)` with `implementation_map=None`, assert the value of `IMPLEMENTATION_MAP_CONTRACT` is the sentinel string defined in step 2(a). Guards the defensive branch.

A minimal fixture for steps 4-7 — you can borrow `_minimal_plan_dict()` if it exists in `tests/`, or construct an inline plan dict with the fields `writer_context` requires (`level`, `sequence`, `slug`, `title`, `word_target`, `phase`). The orchestrator's pre-flight grep didn't surface a shared helper, so an inline plan dict scoped to this test file is acceptable.

---

## Out of scope (intentional)

- **Do NOT edit `linear-writer-correction.md` / `linear-writer-correction-grok.md`.** The correction path uses a different prompt that surfaces gate `fix_proposals` directly; it does not currently consume `{WIKI_MANIFEST}`. If the m20 build #8 shows correction-loop regressions, that's a follow-up PR.
- **Do NOT change the seeder semantics.** No edits to `_artifact_for`, `_location_hint`, `_treatment_template`, or the `ImplementationMapEntry` shape. The seeder is treated as a contract dependency for this PR.
- **Do NOT add a `corrector` integration.** The wiki_coverage_correction loop already consumes the seeded sidecar via `_wiki_coverage_seeded_artifact_index` (linear_pipeline.py:4088). No second wiring path needed.
- **Do NOT run the m20 build #8 inside this PR.** The orchestrator will do that after merge as task #4 in the queue (sequenced this way to keep the PR diff scope to ~code+test+prompt-text only). If you have spare effort budget at the end, you MAY do a smoke render with a fixture manifest to confirm the prompt renders end-to-end — but the build itself is downstream.
- **Do NOT touch `gemini-tools` writer wiring or any non-claude/grok prompt template.** gemini-tools is not in the current `WRITER_CHOICES` for V7 builds.

---

## Numbered execution checklist (MANDATORY — do all 8 in order)

Each step has an explicit verification command. Pass MUST be a real tool output, not "I confirmed manually."

1. **Worktree setup.** Create an isolated worktree (per `claude_extensions/rules/delegate-must-use-worktree.md`).
   ```
   git fetch origin
   git worktree add -b codex/2148-gamma-impl-20260519 .worktrees/dispatch/codex/2148-gamma-impl-20260519 origin/main
   cd .worktrees/dispatch/codex/2148-gamma-impl-20260519
   ```
   → verify: `git rev-parse --abbrev-ref HEAD` outputs `codex/2148-gamma-impl-20260519`.

2. **Re-read anchor files BEFORE editing each.** Per `code-editing-safety.md` rule 2: read `scripts/build/phases/implementation_map.py`, then `scripts/build/linear_pipeline.py` (sections around lines 1511-1535 and 2497-2535), then `scripts/build/v7_build.py` (sections around 411-425 and 715-750), then both writer prompt files. No edits before reads.

3. **Implement the renderer in `implementation_map.py`** (step 1 above).
   → verify: `.venv/bin/python -c "from scripts.build.phases.implementation_map import render_for_writer_prompt; print('ok')"` succeeds.

4. **Wire `writer_context` + `render_writer_prompt`** (step 2 above).
   → verify: `.venv/bin/ruff check scripts/build/linear_pipeline.py` clean.

5. **Wire `_writer_prompt` + call site** (step 3 above).
   → verify: `.venv/bin/ruff check scripts/build/v7_build.py` clean.

6. **Edit both writer prompts** (step 4 above) — `linear-write.md` and `linear-write-grok.md`. No edits to correction prompts.
   → verify: `grep -c "IMPLEMENTATION_MAP_CONTRACT" scripts/build/phases/linear-write.md scripts/build/phases/linear-write-grok.md` returns `1\n1`.

7. **Add new test file** (step 5 above) — `tests/build/test_implementation_map_render.py`.
   → verify (test suite, MANDATORY per #M-7) — the worktree has no `.venv/`; either `cd` to the main repo for `pytest`, or symlink the venv into the worktree first:
   ```
   cd /Users/krisztiankoos/projects/learn-ukrainian
   .venv/bin/python -m pytest tests/build/test_implementation_map.py tests/build/test_implementation_map_render.py tests/test_writer_prompt_structured_cot.py tests/test_writer_prompt_preemit_checklist.py -v
   cd -
   ```
   All four files must be green. Quote the final `N passed in M.MMs` line in the PR body.

8. **Commit + push + open PR.** Single commit. Message follows conventional-commits + #M-4 evidence preamble. NO `--no-verify`. NO `--admin` merge planned.
   ```
   git add -A
   git commit -m "feat(writer): render implementation_map contract into V7 writer prompt (#2148 γ)"
   git push -u origin codex/2148-gamma-impl-20260519
   gh pr create --base main --head codex/2148-gamma-impl-20260519 --title "feat(writer): render implementation_map contract into V7 writer prompt (#2148 γ)" --body-file <(... see PR body template below ...)
   ```
   → verify: `gh pr view --json url -q .url` returns the URL. Quote it in the dispatch finalize log.

**Do NOT auto-merge.** The orchestrator will review + merge after CI green.

---

## PR body template (use this shape; substitute your real numbers)

```markdown
## Summary

Implements shape γ of decision `docs/decisions/pending/2026-05-18-wiki-obligation-emission-contract.md` (#2148). The seeded `implementation_map.json` is now rendered into the V7 writer prompt under a new `{IMPLEMENTATION_MAP_CONTRACT}` placeholder, eliminating the writer-side obligation-translation step that produced m20 build #7's 22% coverage failure.

## Files changed

- `scripts/build/phases/implementation_map.py` — new `render_for_writer_prompt()` (deterministic plain-text serializer).
- `scripts/build/linear_pipeline.py` — `writer_context` + `render_writer_prompt` accept new `implementation_map` parameter; new placeholder added.
- `scripts/build/v7_build.py` — `_writer_prompt` forwards the seeded `impl_map` from the build loop.
- `scripts/build/phases/linear-write.md` — new `## Implementation Map Contract` section after `## Wiki Obligations Manifest`.
- `scripts/build/phases/linear-write-grok.md` — mirror edit.
- `tests/build/test_implementation_map_render.py` — 7 test cases covering renderer determinism, prompt substitution, and grok-variant parity.

## Verification evidence

(quote raw `pytest`, `ruff`, and `git log -1 --oneline` outputs here)

## Out of scope

- Correction prompts (`linear-writer-correction*.md`) — separate follow-up if needed.
- m20 build #8 replay — orchestrator runs after merge.

## Cross-links

- Decision card: `docs/decisions/pending/2026-05-18-wiki-obligation-emission-contract.md`
- Parent architecture: `docs/decisions/2026-05-17-path3-per-obligation-review-loop.md`
- Seeder shipped: PR #2108 (`15834d642c`)
- Issue: #2148
```

---

## Failure-mode planning

If you hit any of the following, STOP and report — do NOT push a half-fix:

1. **`tests/test_writer_prompt_structured_cot.py` or `tests/test_writer_prompt_preemit_checklist.py` regresses.** That means the new `## Implementation Map Contract` section was inserted in the wrong place and now breaks an existing structural assertion. Re-read those tests' assertions and pick a different insertion point that doesn't disturb them.

2. **`render_for_writer_prompt` produces non-deterministic output.** Likely cause: iterating over a dict without `sorted(...)` or a `set` in `treatment_template` values. Fix at the renderer layer, not by working around the test.

3. **`v7_build.py` import cycle.** If adding the `from scripts.build.phases.implementation_map import render_for_writer_prompt` inside `writer_context` creates a cycle, move the import to function-local scope (the existing code uses lazy imports in similar paths).

4. **`grok-tools` variant has divergent section structure.** If `linear-write-grok.md` doesn't have a `## Wiki Obligations Manifest` block as the anchor, file the divergence in the PR body and use the closest semantic anchor instead — do not duplicate the contract section in a wrong place.

5. **Build the worktree against an older `origin/main` SHA.** Always `git fetch origin` first; this dispatch was authored against `f65bccb617`.

---

## Status convention (no `/goal` driver here — this is a single PR, not a batch)

This dispatch is a **single bounded code change**, not a `/goal`-driver batch. Status conventions: emit standard conventional-commit subject + an evidence-quoted PR body. The orchestrator will read `delegate.py` task state, NOT a `GOAL_STATUS` line.

If you need to abort mid-flight (e.g. discover an unexpected blocker), leave the worktree branch intact and report the blocker via the dispatch's normal exit channel. The orchestrator will pick up the blocker from the `recent_outcomes` field in `/api/delegate/active`.

---

## Provenance

- Decision card (γ + bridge A approved by user): `docs/decisions/pending/2026-05-18-wiki-obligation-emission-contract.md`
- Issue forensics: #2148
- Architecture parent: `docs/decisions/2026-05-17-path3-per-obligation-review-loop.md`
- Seeder PR: #2108 (`15834d642c`)
- Dispatch authored: 2026-05-19 (Claude orchestrator, this session)
- Predecessor handoff: `docs/session-state/2026-05-19-night-gap-audit-closure-and-qwen-judge-brief.md`

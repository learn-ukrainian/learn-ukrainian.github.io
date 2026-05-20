---
date: 2026-05-21
session: "Night — unblock-Codex-promote-prune + ship A1 plan fixes + diagnose claude-tools silent-fail + fire codex-tools A1 build"
status: green-multiple-shipped + 1-build-running + 2-PRs-open
main_sha: f9609d39b3
main_green: pending (CI green on each merged commit; new commits in pipeline)
working_tree_dirty: true  # starlight/src/content/docs/a1/index.mdx (pre-existing, NOT mine); audit/2026-05-21-flash-3.5-ua-quality/ (empty marker dir); curriculum/l2-uk-en/_orchestration/ (run-archive forensics — gitignored or not yet committed)
prs_merged_this_session: []
prs_opened_this_session:
  - "#2169 (feat(sync): paired promote_module + prune_module_forensics helpers) — Codex authored, Claude shipped after fixing pre-commit env-leak"
direct_commits_to_main:
  - "afc3510364 fix(tests): unblock pre-existing failures stale vs current pipeline"
  - "7a0458cec9 chore(archive): commit 2026-05-21 dispatch briefs"
  - "f9609d39b3 fix(plans/a1): bring two A1 checkpoints to schema (Діалог 200→400)"
active_dispatches: []
active_builds:
  - "a1/my-morning via codex-tools (Monitor task bogkut45c, started 23:37:05 UTC, branch build/a1/my-morning-20260520-233701)"
issues_filed: ["#2170 (hist/hromadske-suspilstvo missing objectives — blocks #2168)"]
issues_closed: []
headline_finding: "Claude CLI is NOT logged in (`claude -p \"echo hello\" --bare` → 'Not logged in · Please run /login'). The default V7 writer `claude-tools` invokes `claude` headless and silently exits at the writer phase after `mcp_config_resolved` — three separate builds tonight died identically. Fired the fourth build with `--writer codex-tools` and it's progressing. Operator: log in claude CLI OR the V7 default-writer should be flipped to `codex-tools` (per pipeline.md the post-2026-06-15 plan anyway)."
next_session_first_item: "Check Monitor task bogkut45c — codex-tools A1 build outcome. If green, run scripts/sync/promote_module.py against the build branch to ship into main's curriculum tree. If gates failed, read the persisted artifacts on the build branch and iterate. Then resolve PR #2168 (Curriculum Plans red on issue #2170)."
---

# Night handoff — Codex promote+prune shipped, A1 plan fixes shipped, build in flight

## TL;DR

Five shippable changes landed; one build running; one diagnosed blocker for the operator.

| # | Status | Subject | Artifact |
|---|---|---|---|
| 1 | shipped to main | unblock stale tests (textbook_grounding, python_qg) | `afc3510364` |
| 2 | PR #2169 MERGED | promote_module + prune_module_forensics helpers | `73604666cd` |
| 3 | shipped to main | commit 2026-05-21 dispatch briefs | `7a0458cec9` |
| 4 | shipped to main | A1 checkpoint-food-shopping + checkpoint-communication schema fix | `f9609d39b3` |
| 5 | filed | hist/hromadske-suspilstvo missing objectives — blocks #2168 | issue #2170 |
| 6 | shipped to main | A1 checkpoint vocabulary_hints doc note (3 plans) | `432f72ea79` |
| 7 | running | a1/my-morning V7 build (gemini-tools, 3rd attempt) | Monitor `bu2qx1fmf` |

## Section 1a — codex-tools ALSO fails: `mcp_tools_never_invoked`

The first attempt with `--writer codex-tools` reached the writer phase, emitted CoT for all four sections (`Діалоги`, `Дієслова на -ся`, `Мій ранок`, `Підсумок`), fired the `writer_end_gate` with `rescanned_words`/`rescanned_sources`/`grammar_claims_grounded`, then HARD-FAILED:

```json
{"event": "writer_tool_theatre", "violations": ["get_chunk_context", "search_external", "search_sources", "search_style_guide", "search_text", "verify_words"], "violation_count": 6, "cited_count": 6, "called_count": 0}
{"event": "phase_writer_summary", "tool_calls_total": 0, "verify_words_calls": 0, "tool_call_telemetry_available": true, "tool_theatre_violation_count": 6}
{"event": "writer_failure_class", "failure_class": "mcp_tools_never_invoked", "severity": "HARD"}
{"event": "module_failed", "reason": "WRITER_RUNTIME_GATE_FAILED: writer='codex-tools' module='a1/20' failures=[mcp_tools_never_invoked]"}
```

Per pipeline.md the 2026-05-12 `tool_calls_total=0` verdict was retracted as a measurement artifact (PR #1907 fixed `_rollout_matches_plan` in `scripts/agent_runtime/adapters/codex.py`). Tonight's repro shows **the symptom is back** OR a new regression — `writer_tool_calls.json` in the build worktree is `[]` (empty list), and `module.md` is byte-identical to main's existing version (codex didn't actually write fresh content, it regurgitated). Auto-commit fired per #M-10: branch `build/a1/my-morning-20260520-233701` retains the forensics at `e408c91ab6 build(a1/my-morning): artifacts (failed)`.

Hypotheses for next session:
1. Codex rollout-matcher regression (look at codex CLI 0.132.0 vs the version PR #1907 was tested on; the rollout location may have changed).
2. MCP server reachable but codex's MCP wiring config drifted (the runtime emits `-c mcp_servers.sources.url="http://127.0.0.1:8766/mcp"` — verify the local sources server is listening).
3. Codex genuinely lying about tool-calls in CoT but not making them — would point to a prompt engineering gap (writer doesn't believe it must call tools, just claims it did).

Diagnostic command for next session:
```
git log build/a1/my-morning-20260520-233701 --oneline
git show build/a1/my-morning-20260520-233701:curriculum/l2-uk-en/a1/my-morning/writer_tool_calls.json
git show build/a1/my-morning-20260520-233701:curriculum/l2-uk-en/a1/my-morning/module.md | diff -q - curriculum/l2-uk-en/a1/my-morning/module.md
```

## Section 1 — claude CLI not logged in (HEADLINE)

Reproducer: `claude -p "echo hello" --bare` → `Not logged in · Please run /login`.

Consequence: `claude-tools` writer invokes `claude` headless and exits silently — V7 build emits events through `mcp_config_resolved` and then nothing. The process is gone but no error, no `phase_done writer`, no `phase_failed`, no artifacts. Three separate a1/my-morning runs reproduced this exactly:

- `build/a1/my-morning-20260520-232732` — stalled silent
- `build/a1/my-morning-20260520-233504` — stalled silent (this one I killed accidentally with `pkill -f v7_build`)
- `build/a1/my-morning-20260520-233549` — stalled silent

Two next-session paths:

1. **Operator: log in claude CLI** (`claude /login`) — restores claude-tools as the default. Caveat: counts against the $200/mo subscription pool reserved for cold-start sessions (per MEMORY #M0).
2. **Flip the default writer** in `scripts/build/v7_build.py` (or `pipeline.md`) to `codex-tools` — aligned with the post-2026-06-15 sunset of `delegate.py --agent claude` anyway. Lower-risk operationally; trades A1 immersion-cap adherence (claude-tools is empirically better per `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`).

Recommend path 2 short-term: codex-tools default until claude CLI auth is sorted; revisit once auth is restored.

The fourth run, fired with `--writer codex-tools`, is currently progressing (Monitor `bogkut45c`, branch `build/a1/my-morning-20260520-233701`).

## Section 2 — Codex promote+prune helpers (#2169)

`scripts/sync/promote_module.py` (~390 LOC) + `scripts/sync/prune_module_forensics.py` (~200 LOC) + paired tests (11/11 passing). Codex authored via `delegate.py dispatch` (2117s, exit 0); Codex correctly refused to commit while the full pytest suite was red.

That blocker was two stale tests, both fixed in `afc3510364`:

- `tests/test_wiki_packet_dictionary_context.py::test_build_knowledge_packet_appends_textbook_excerpts` — PR #1975 introduced `_lookup_textbook_reference_chunk` (direct sqlite lookup) which now pre-empts the `search_sources` call for titles matching `<Author> Grade <N>, p.<M>`. Patch: monkeypatch `_lookup_textbook_reference_chunk` to return None so the search_sources fallback this test pins is actually exercised.
- `tests/build/test_wiki_coverage_correction_yaml_guard.py::test_python_qg_reviewer_correction_rejects_oversize_fix` — `_apply_python_qg_correction` now returns a 3-tuple; test unpacked 2.

**Load-bearing fix on top of Codex's work (pre-commit env-leak):**

Both Codex test fixtures spawned `git -C <tmp_repo> init -b main` with inherited environment. Under pre-commit's pytest hook, the parent repo's `GIT_DIR` / `GIT_INDEX_FILE` leak into the test fixture's git calls and (a) confuse `git -C <repo> add ...` with "must be run in a work tree" exits, and (b) during the early init/config phase write the fixture's test-user identity AND `core.bare=true` into the OUTER repo's `.git/config`. I caught this when my first commit attempts kept polluting main's `.git/config` (mid-session I had to repair `git config user.name` twice).

Fix in #2169:
- New `_sanitized_git_env()` in `promote_module.py`, re-used by `prune_module_forensics.py` and both test fixtures.
- Strips `GIT_*` and `PRE_COMMIT*` env vars before any `subprocess.run(["git", "-C", ...], env=...)` call.
- Verified by hand: full `tests/sync/` batch run with the fix does NOT modify outer `.git/config`.

## Section 3 — A1 plan schema fixes

`scripts/validate_plan_config.py` was rejecting two A1 plans:

```
checkpoint-food-shopping  : content_outline sum (1000) under word_target (1200)
checkpoint-communication  : content_outline sum (1000) under word_target (1200)
```

Healthy A1 checkpoint pattern (verified against the 5 already-passing siblings):

| Section | Words |
|---|---|
| Що ми знаємо? | 200 |
| Читання | 250 |
| Граматика | 200 |
| Діалог | **400** |
| Підсумок | 150 |
| **sum** | 1200 |

Both failing plans had `Діалог=200`. Bumped to 400 by adding two extra dialogue scenes that reinforce module-pegged constructions (А1.6 знахідний відмінок + ціни for food-shopping; А1.7 кличний відмінок + наказовий спосіб + сполучники for communication). Same speaker roles, same `dialogue_situations` peg.

Per `check_plan_immutability.py`: bumped versions (1.2.3→1.2.4 and 1.1.2→1.1.3) and staged `.yaml.bak` snapshots with OLD versions in same commit.

## Section 4 — PR #2168 (Gemini #2164 backfill) — held on #2170

Status: `Test (pytest)` PASS ✅; `Curriculum Plans` FAIL ❌; `review/review` FAIL (advisory — Gemini self-review OFF policy).

The Curriculum Plans failure:

```
❌ HIST: 1/1 plans have errors
   • hromadske-suspilstvo:
      - Missing required field: objectives
```

This is **pre-existing** — main has had this gap. Gemini's PR re-folded all 1124 seminar plan YAMLs (consequence of brief's `width=10**9` instruction — keeps long lines unwrapped on the way out), which made the per-changed-file CI flag `hromadske-suspilstvo.yaml`. Adding `objectives:` is content judgment; deferred to next session per user A1-focus direction. Filed as **issue #2170**.

Recommended unblock path: write 4 objectives derived from the plan's `focus`, `content_outline`, and the `[!decolonization]`/`[!myth-buster]`/`[!anti-hagiography]` section annotations (sibling `hist/afhanistan.yaml` shows the canonical shape). Single-file PR, fast merge. Also worth running a sweep across `hist/`, `bio/`, `lit/`, `istorio/` for the same gap.

Out-of-scope concern (next-session decision): the 1124-file diff has +25319/-39773 net, which destroys git-blame across all seminar plans. The user's brief told Gemini `width=10**9` deliberately; that's the source. May be worth a 2026-Q2 cleanup that re-runs with `default_flow_style=None` + sort_keys preserved, but no priority.

## Section 5 — Open follow-ups for next session

1. **Check Monitor `bogkut45c`** — codex-tools A1 build outcome. If green, use the new `scripts/sync/promote_module.py --latest --level a1 --slug my-morning` to ship artifacts into main's curriculum tree. If gates failed, read the persisted forensics on `build/a1/my-morning-20260520-233701` and iterate. Per #M-10, artifacts auto-commit regardless of outcome.
2. **Decision: claude CLI auth vs writer default flip** (Section 1).
3. **Unblock PR #2168** via issue #2170 (hist/hromadske-suspilstvo objectives) + plan-sweep across other seminar plans.
4. **Merge PR #2169** if CI green (Test pytest pending at handoff).
5. **A1 plan content health** — 5 checkpoint plans have empty `vocabulary_hints: {required: [], recommended: []}`. The healthy pattern is at least a documentation note (e.g. checkpoint-first-contact's `"All vocabulary from №1–6 is recycled — no new required words"`). Quick sweep:
   ```
   .venv/bin/python -c 'import yaml,glob; [print(p) for p in sorted(glob.glob("curriculum/l2-uk-en/plans/a1/checkpoint-*.yaml")) if not yaml.safe_load(open(p)).get("vocabulary_hints", {}).get("required") and not yaml.safe_load(open(p)).get("vocabulary_hints", {}).get("recommended")]'
   ```

## Section 6 — Flash-3.5 / A1 question answered

Operator asked: *"did we try gemini flash 3.5 on a1?"*

**No.** Flash-3.5 (via the new agy CLI) has been smoke-tested on seminars only: `hist/trypillian-civilization`, `lit/natalka-poltavka` (×3 attempts). All three failed before the writer phase on plan-schema bugs. The one that reached the writer surfaced the agy 1.0.0 blocker: no MCP plugin enablement → `tool_calls_total=0` with `tool_call_telemetry_available=true` → `MCP_TOOLS_NEVER_INVOKED` hard-fails by design.

Until kubedojo ships `agy plugin enable sources` upstream, agy cannot pass A1 either (VESUM gate, textbook_grounding, all four russianism gates all blocking). Audit: `audit/2026-05-20-seminar-smoke-builds/REPORT.md`. The `audit/2026-05-21-flash-3.5-ua-quality/flash35-natalka-section.raw.md` file in the local tree is a 0-byte marker — never populated.

## Section 7 — Provenance + cross-links

- Parent handoff: `docs/session-state/2026-05-21-late-orchestrator-challenge-and-codex-blocked.md` (commit `090ef23603`)
- Tonight's commits: `git log f9609d39b3..32593a3876 --oneline`
- PR #2169: feat(sync): paired promote_module + prune_module_forensics helpers
- Issue #2170: [plan] hist/hromadske-suspilstvo.yaml missing required `objectives:` field
- Active Monitor task: `bogkut45c` (codex-tools A1 my-morning build)
- Dead-silent build branches preserved (#M-10): `build/a1/my-morning-20260520-{232732,233504,233549}` — base commit only, no artifacts (writer never got past mcp_config_resolved before claude headless silently exited)

## Section 8 — Sign-off

User went to bed mid-session with explicit night-mode permission and the A1-focus direction. Caught the claude CLI auth blocker after 3 silent build failures; rerouted via codex-tools so a real A1 build is actually running. Five shippable changes shipped (3 to main, 1 PR opened, 1 issue filed). Build status will be in Monitor `bogkut45c` events when next session opens.

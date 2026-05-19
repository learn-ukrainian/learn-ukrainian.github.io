---
date: 2026-05-19
session: "Night — Hermes MCP observability gap CLOSED end-to-end (3-layer fix), a1 build 17/23 gates green with all fixes loaded, a2+b1 landing pages shipped, antigravity migration parked"
status: green-with-content-issues
main_sha: 5db4af10ed
main_green: true
working_tree_dirty: true  # 2 untracked: .antigravitycli/ (agy symlink dir, kubedojo-created) + docs/dispatch-briefs/2026-05-19-etymology-closeout-codex.md (carry-over)
prs_merged_this_session: []
direct_commits_to_main:
  - "9c2b7cf096 fix(hermes-mcp): observability hook + single-underscore prefix normalizer"
  - "8da51b00db fix(textbook-grounding): unwrap Hermes-routed MCP {result: \"<md>\"} shape"
  - "90f292d05c fix(invoke_writer): backfill tool_calls from sidecar JSONL for Hermes writers"
  - "5db4af10ed feat(starlight): a2 + b1 landing-page stubs (69 + 94 modules)"
active_dispatches: []
issues_filed: []
issues_closed: []
headline_finding: "The 'Hermes MCP-invocation gap' framing in the predecessor handoff was wrong on every dimension. DeepSeek-pro under `hermes -z` DOES invoke MCP tools (proved by a 274-char probe returning real VESUM-structured output `noun:inanim:m:v_naz` that could not have been fabricated). The actual gap was OBSERVABILITY: `hermes -z` strips tool-call traces from stdout by design (oneshot.py docstring), so the Hermes adapters returned `tool_calls=[], tool_calls_total=None` and downstream V7 gates saw zero calls. Three commits closed the gap at three layers (post_tool_call shell hook + gate-side result-shape unwrap + invoke_writer sidecar backfill). The a1/my-morning build with all 3 fixes loaded ran 17/23 gates green; remaining failures are CONTENT quality (writer didn't extract verbatim ≥30-word textbook quote despite 4 captured search_text calls), VESUM proper-noun-declension gaps, and orthogonal issues. Diagnostic mistake encoded: I claimed 2 prior builds validated my patches when both worktrees were at 728f47b435 (pre-fix) because pushes landed AFTER build start; MEMORY updated with push-before-worktree-build rule."
next_session_first_item: "Investigate why textbook_grounding rejects with matched=0 despite search_text_calls=4. Writer searched 'Захарійчук 24' four times, got hits, but didn't paste a verbatim ≥30-word block. Either writer-prompt clarity issue (writer doesn't realize it must blockquote contiguous text) or DeepSeek-specific content-shape issue. Also: address NEW-4 fence-sequencing parser (a2 build failed at writer parse for bare ``` inside module.md prose) + VESUM proper-noun-declension whitelist additions (Єнісея, Іртиша, гіперкорекція, Литвінова, etc)."
---

# Handoff — Hermes MCP observability CLOSED end-to-end; a1 build 17/23 green; landing pages + housekeeping

## TL;DR for the next session

The predecessor handoff's "Hermes -z doesn't emit tool-use calls" framing was wrong. A deterministic probe with `hermes -z PROMPT -m deepseek-v4-pro` asking the model to call `mcp_sources_verify_word("стіл")` returned real VESUM-structured output (`noun:inanim:m:v_naz`) that the model could not have hallucinated. Tool execution DOES happen.

The actual gap was three-layer **observability**:

1. **Hook gap**: `hermes -z` strips tool-call traces from stdout by design (oneshot.py:1-5 docstring: "no banner, no spinner, no tool previews"). Hermes adapters returned `tool_calls=[], tool_calls_total=None`. No on-disk evidence of MCP usage anywhere.
2. **Gate-side shape gap**: `_result_items_from_call` only unwrapped two MCP response shapes (`{"results": [...]}` and `{"type": "text", "text": "..."}`). The learn-ukrainian sources MCP server uses a third shape: `{"result": "<markdown>"}`. Result: even hook-captured calls didn't surface textbook hits to the gate.
3. **In-memory gate gap**: `invoke_writer`'s `_runtime_tool_calls(result)` returns `None` when adapter's `tool_calls_total=None`. Downstream in-process gates (`detect_tool_theatre`, `emit_writer_response_telemetry`, `_enforce_writer_runtime_gates`) all saw zero calls and treated every prose-cited tool as a tool-theatre violation.

Three commits closed all three layers:
- `9c2b7cf096` — post_tool_call shell hook + `_normalize_tool_citation_name` accepts both `mcp__sources__` and `mcp_sources_` prefixes
- `8da51b00db` — `_result_items_from_call` unwraps the `{"result": "<md>"}` shape
- `90f292d05c` — `invoke_writer` backfills `tool_calls` from `$cwd/*.write.jsonl` when adapter telemetry is unavailable

End-to-end validation: a1/my-morning build with worktree at `90f292d05c` produced **17/23 python_qg gates green**, with `phase_writer_summary` reporting `tool_calls_total: 10` (was `null` in all prior Hermes-routed builds), `tool_call_telemetry_available: true` (was `false`), `tool_theatre_violations: []` (none), and `textbook_grounding.search_text_calls: 4` (was `0` in b1).

Build still failed at 5 gates — but for separate content-quality reasons, not observability. See § Build outcome detail.

## ⚠️ Diagnostic mistake to NOT repeat

Mid-session I claimed two builds (b1/genitive-nuances, a2/aspect-concept) validated my patches because I re-ran the gate functions on their on-disk JSONLs and they passed. **Both worktrees were at `728f47b435`** — the commit BEFORE my fixes. I had not yet pushed to `origin/main` when the builds were fired, and `v7_build.py --worktree` creates from `origin/main` (v7_build.py:300). So the builds ran the OLD gate code; my LIVE main checkout had the new code that I was confirming worked. Two different code versions, accidentally conflated.

**Rule encoded in MEMORY**: push commits to `origin/main` BEFORE firing `v7_build.py --worktree`. Validating "my patches work" by re-running on the live checkout after the fact only proves the code is correct — it doesn't prove the build benefited.

## Section 1 — What this session shipped

### Commits to main (4 direct, 0 PRs)

1. **`9c2b7cf096`** — `fix(hermes-mcp): observability hook + single-underscore prefix normalizer`. Project shell hook `scripts/agent_runtime/hermes_hooks/log_tool_call.sh` registered via `~/.hermes/config.yaml` (matcher `mcp_sources_.+`, must be regex `fullmatch`, not prefix). Writes one JSONL line per MCP call to `$cwd/hermes.write.jsonl`. Normalizer fix accepts both `mcp__sources__` (canonical) and `mcp_sources_` (Hermes single-underscore) prefixes. 2 new tests pin the single-underscore acceptance.
2. **`8da51b00db`** — `fix(textbook-grounding): unwrap Hermes-routed MCP {result: "<md>"} shape`. Gate's `_result_items_from_call` now handles the third MCP response shape. Pinned by `test_textbook_grounding_gate_unwraps_hermes_inner_result_shape`. Live-data verification: 4 search_text calls → 20 textbook items extracted (was 4 calls → 0 items pre-fix).
3. **`90f292d05c`** — `fix(invoke_writer): backfill tool_calls from sidecar JSONL for Hermes writers`. When `_runtime_tool_calls(result)` returns `None`, `invoke_writer` falls back to `_load_writer_tool_calls(Path(cwd))` so the in-process gate path sees the hook-captured calls. New test `test_invoke_writer_backfills_tool_calls_from_sidecar_jsonl`. 95/95 pytest sweep green.
4. **`5db4af10ed`** — `feat(starlight): a2 + b1 landing-page stubs (69 + 94 modules)`. Was 404 before; seminar-style monolingual UA titles (sourced verbatim from each plan's `title` field), every module pinned `status: "wip"`. b2/c1/c2 deferred until plans firm.

Plus **out-of-repo changes** (user-global, not committed):
- `~/.hermes/config.yaml` — appended `hooks.post_tool_call` block with the project hook + matcher
- `~/.hermes/shell-hooks-allowlist.json` — pre-approved the `(post_tool_call, log_tool_call.sh)` pair (one-time consent; `HERMES_ACCEPT_HOOKS=1` is set inside oneshot.py:172 AFTER `register_from_config` already fires, so env-var alone doesn't allowlist)
- `~/.gemini/config/mcp_config.json` — left empty (probe write was reverted; kubedojo agent is handling the antigravity-cli adapter)

### CI all green on the 4 commits

`Analyze (actions/python/javascript-typescript)` ✓, `changes` ✓, `Frontend (build + vitest)` ✓, `Lesson Schema Drift` ✓, `Lint (ruff)` ✓, `Lint Prompts` ✓, `No new root scripts` ✓, `Quality Gates (radon)` ✓, `Run zizmor 🌈` ✓, `Secret Scanning (gitleaks)` ✓, `Test (pytest)` ✓. 14/14 checks.

## Section 2 — The 3 V7 builds this session

| Module | Worktree SHA | Outcome | Lesson |
|---|---|---|---|
| `b1/genitive-nuances` (20:01) | `728f47b435` (pre-fix) | ❌ python_qg HARD-fail | textbook_grounding blind: `search_text_calls: 0` (gate-side normalizer bug — my fix not in worktree). Plan refs (Заболотний/Литвінова/Авраменко) are also `corpus_missing: true` in knowledge_packet — that's an upstream plan/corpus gap independent of tooling. |
| `a2/aspect-concept` (20:45) | `728f47b435` (pre-fix) | ❌ writer parse | `Writer output contains unnamed fenced block at line 155`. Writer emitted a bare ``` ``` ``` code fence inside module.md content (used for a present-tense example box); parser interpreted it as an artifact-fence open with no name. This is NEW-4 — affects all writers, separate from this session's fix scope. |
| `a1/my-morning` (21:06) | `90f292d05c` (all 3 fixes) | ⚠️ 17/23 gates pass | First Hermes-routed build with my fixes loaded. `phase_writer_summary`: `tool_calls_total: 10, verify_words_calls: 1, tool_call_telemetry_available: true, tool_theatre_violations: []`. textbook_grounding sees `search_text_calls: 4` (informative reject, not blind). 5 gates fail for non-observability reasons — see below. |

### a1/my-morning gate detail

**PASS (17)**: activity_schema, word_count, plan_sections, formatting_standards, citations_resolve, **resources_search_attempted** (was HARD-fail in b1 — my fix unlocked it), immersion_advisory, long_uk_ceiling, component_density, activity_types, ai_slop_clean, component_props, russianisms_clean, surzhyk_clean, calques_clean, paronym_clean, previously_passed_regression.

**FAIL (5)**:
- **`textbook_grounding`** (HARD REJECT): `search_text_calls: 4, textbook_result_hits: ?, matched: 0`. Writer ran 4 searches for "Захарійчук 24" but never copy-pasted a ≥30-word verbatim block from the returned chunk into a module.md blockquote. Writer-prompt-clarity OR writer-content issue, NOT observability.
- **`vesum_verified`**: 15 missing including `**Єнісея**`, `**З-за**`, etc. NEW-5 reframing (encoded in task #5): tokenizer is fine (strips markdown), real issues are VESUM proper-noun-declension gaps (`Єнісей` is in VESUM, `Єнісея` is not), linguistic-term gaps (`гіперкорекція`), textbook-author surname gaps (`Литвінова`), and writer typos missing hyphens (`зза`, `зпід` instead of `з-за`, `з-під`).
- **`l2_exposure_floor`**: details not captured — investigate.
- **`inject_activity_ids`**: pipeline-insert gate, likely knock-on from other failures.
- **`correction_terminal`**: max corrections hit.

## Section 3 — Other threads this session

### Antigravity-CLI migration: PARKED (kubedojo handles)

Per user direction: "we postpone the antigravity migration. let kubedojo handle it, plus the gemini-3.5-flash test."

Findings before parking (in case the kubedojo agent's brief diverges):
- `agy` v1.0.0 is installed at `~/.local/bin/agy` (Go binary, Mach-O arm64)
- Default model: **Gemini 3.5 Flash (High)** — pre-selected, no `--model` flag exists on the CLI
- Invocation: `agy --print PROMPT` (alias `-p`), `--dangerously-skip-permissions`, `--add-dir`, `--sandbox`, `--continue`, `--conversation`
- Auth: silent via keychain, shares gemini-cli's `~/.gemini/oauth_creds.json`
- Runtime state: `~/.gemini/antigravity-cli/` (separate from gemini-cli's runtime; conversations, brain, cache)
- Per-project state: `.antigravitycli/{project-uuid}.json` symlinks to `~/.gemini/config/projects/{uuid}.json`
- MCP config: **`~/.gemini/config/mcp_config.json`** (NOT `.gemini/settings.json.mcpServers`). Currently empty on this machine. Schema (per binary string probe): `{"mcpServers": {"<name>": {...}}}` likely — never validated end-to-end.
- Counter: **separate quota from gemini-cli** per user info; both binaries coexist until 2026-06-18.
- Plugin import: `agy plugin import gemini` accepts gemini-cli extensions (we don't use any).
- Probe with MCP-requiring prompt: timed out (90s) — likely because `mcp_config.json` was empty.

If the kubedojo agent ships a working adapter, port the pattern to learn-ukrainian rather than re-derive. Otherwise, the project-side TODO is: write `scripts/agent_runtime/adapters/agy.py` modeled on `gemini.py` but with the new binary + config path.

The user-flagged **gemini-3.5-flash bakeoff** is blocked on this migration landing — that's the new model agy ships with by default.

### Tracker / pipeline state

Per Monitor API `/api/orient` at session end:
- **Total modules across all tracks**: 1713
- **content_done**: 1 (folk track — research-stage only; no module.md)
- **audit_passing**: 0
- **reviewed**: 1
- **In main checkout**: ONE module — `curriculum/l2-uk-en/a1/my-morning/module.md` (the proving-ground module, last updated 2026-05-15 with citation-matcher fix).
- **In worktrees**: 3 from this session (b1-200131, a2-204548, a1-210615), all failed; should clean up next session.

### Landing-page status

| Level | Landing | Notes |
|---|---|---|
| a1 | ✅ | Bilingual + dynamic (#1927) — references `starlight/src/data/a1-modules.ts` |
| a2 | ✅ shipped today | Seminar-style monolingual, 69 modules wip |
| b1 | ✅ shipped today | Seminar-style monolingual, 94 modules wip |
| b2 / c1 / c2 | ❌ | Defer until plans firm |
| b2-pro / c1-pro | ✅ already existed | Separate "Professional Ukrainian" landings (NOT part of CORE A-B-C progression — user clarified there's no "pro track" tier) |
| All seminars (hist, bio, lit family, oes, ruth, folk, istorio) | ✅ | Pre-existing, monolingual-array template |

### Writers per track — partially documented

Per `scripts/config/agent_fallback_substitutions.yaml` + decision card `2026-05-06-writer-selection-codex-gpt55.md`:
- **CORE (A1-C2)**: `claude-tools` current default → `deepseek-tools xhigh` uniform fallback post-2026-06-15. NO per-level split ("we don't do budget options" — user direction 2026-05-19).
- **Wiki content**: Gemini always (decision 2026-04-26).
- **Pipeline reviewer**: Codex (cross-agent, no self-review).
- **SEMINARS**: implicitly claude-tools (default fallthrough). **No explicit ADR yet.**

User context: "historically everything was written by Gemini" — Gemini handled v3/v4/v5 module writing across both CORE and seminar. Seminars never got an explicit transition, so they implicitly fell through to claude-tools when CORE switched. Task #9 carries the seminar-writer ADR.

## Section 4 — Carry-over task list

Active task IDs from `TaskList`:

| # | Status | Subject |
|---|---|---|
| #1 | completed | Investigate Hermes -z MCP-invocation gap (reframed: observability not invocation) |
| #2 | in_progress | Validate fix with 3-build deepseek re-test (b1 + a2 ran pre-fix worktree; a1 ran post-fix → 17/23 PASS) |
| #3 | pending | 3-build claude-tools parity baseline (not started — claude budget concern) |
| #4 | completed | Ship Hermes post_tool_call hook |
| #5 | pending | VESUM gaps: proper-noun declensions + writer hyphenation (15 missing in b1 build; tokenizer is fine, content fix needed) |
| #6 | deleted | Antigravity-cli migration (kubedojo handles) |
| #7 | deleted | Test gemini-3.5-flash (blocked on #6) |
| #8 | completed | Sync a2 + b1 landing page stubs |
| #9 | pending | ADR: seminar-track writer assignment |

### Next session P0 priorities

1. **textbook_grounding investigate**: writer searched 4× but never quoted ≥30 verbatim words. Read writer prompt lines 184-204 (Step A/B chunk extraction) + writer_output.raw.md from the a1 build. Either prompt clarity issue or DeepSeek-specific content-shape failure. **Highest leverage** because all subsequent module builds will hit the same wall.
2. **NEW-4 fence-sequencing**: a2 build's `Writer output contains unnamed fenced block at line 155`. Parser (`parse_writer_output_strict_json`) needs to either (a) prohibit nested fences in artifact content via writer prompt, or (b) use a 4-backtick outer wrapper for artifacts so 3-backtick inline fences pass through. Same parser bug affects all writers.
3. **VESUM whitelist + writer-prompt hyphenation**: per task #5 — add `Єнісея, Іртиша, Літвінова, гіперкорекція` etc to `PROPER_NAME_WHITELIST` in `scripts/audit/config.py`; revise writer prompt to enforce hyphens in compound prepositions (`з-за`, `з-під` not `зза`, `зпід`).
4. **Worktree cleanup**: 3 failed worktrees from today (b1-200131, a2-204548, a1-210615). `git worktree remove` each + delete the branches.
5. **Seminar-writer ADR** (task #9): bakeoff candidate — codex vs claude vs gemini on a hist or lit module. Gemini is the historical baseline ("everything was Gemini before") so any change requires evidence.
6. **#2151 V7 preservation wrapper** (Tier 1 from WORKSTREAMS): spec exists, impl missing. Without it, parallel module builds don't archive consistently.

## Section 5 — State snapshot for cold-start

- **Main**: `5db4af10ed` (a2+b1 landing stubs). 4 direct commits + 0 PR merges since predecessor handoff's `728f47b435`.
- **Working tree dirty**: `.antigravitycli/` (kubedojo-agent-created symlink dir, gitignore candidate) + `docs/dispatch-briefs/2026-05-19-etymology-closeout-codex.md` (carry-over from morning, deferred per ESUM OCR prereq).
- **Active dispatches**: 0. Build subprocess for a1 ended.
- **Worktrees alive (cleanup queue)**: 3 failed-build worktrees from this session + 3 older ones (a1-my-morning-184814, a2-aspect-concept-184817, b1-genitive-nuances-184819) + 2 dispatch worktrees (codex/cot-removal, codex/deepseek-qwen-writer-tools).
- **Open PRs upstream**: only #1873 (dependabot starlight, user-owned, leave).
- **Hermes log**: `~/.hermes/logs/agent.log` ~1.9MB. Tool-call execution events are NOT logged at INFO level — only registration is. Per-call traces now live in `$module_dir/hermes.write.jsonl` thanks to the hook.
- **MCP server `sources`**: `localhost:8766/mcp`, healthy, 34 tools registered.
- **MEMORY.md**: 150/150 (at hard limit). The `BUILDS — AGENT-RUN ALLOWED with --worktree` entry was extended in place with the push-before-build lesson.

## Cold-start protocol for the next session

1. Read this handoff (you're doing it now).
2. Orient via Monitor API:
   ```
   curl -s http://localhost:8765/api/state/manifest
   curl -s http://localhost:8765/api/orient
   curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'
   ```
3. Read `docs/decisions/pending/` for any blocking signoff items.
4. **First action**: investigate why textbook_grounding rejects with `matched=0` despite `search_text_calls=4` on the a1 build. Read `.worktrees/builds/a1-my-morning-20260519-210615/curriculum/l2-uk-en/a1/my-morning/writer_output.raw.md` for what the writer actually wrote, then `hermes.write.jsonl` for what it actually fetched. The gap between "writer fetched 5 textbook chunks" and "writer's module.md has 0 verbatim ≥30-word blockquotes" is the next surface to fix.
5. **DO NOT fire another V7 build until step 4 is understood AND the writer-prompt clarity fix (or whatever the root cause is) is shipped.** Re-iterating builds without addressing this will just produce more 17/23-or-worse outputs.

## Provenance + cross-links

- This session's hook: `scripts/agent_runtime/hermes_hooks/log_tool_call.sh`
- This session's commits: `git log 728f47b435..5db4af10ed --oneline`
- a1 build artifacts (failed): `.worktrees/builds/a1-my-morning-20260519-210615/curriculum/l2-uk-en/a1/my-morning/`
- Hermes hooks docs: `~/.hermes/hermes-agent/website/docs/user-guide/features/hooks.md` (local install only)
- Predecessor handoff: `docs/session-state/2026-05-19-late-night-hermes-mcp-gap-confirmed-routing-rewritten.md`
- Reframed task #5: VESUM gaps not tokenizer
- agy probe findings: in-session only (no commit) — install ✓, MCP config TBD

## Open dispatches at handoff

None. All work either landed in main or is queued via task list.

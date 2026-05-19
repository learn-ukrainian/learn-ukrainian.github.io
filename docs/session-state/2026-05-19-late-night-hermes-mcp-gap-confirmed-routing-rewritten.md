---
date: 2026-05-19
session: "Late-night — Hermes MCP-invocation gap CONFIRMED as the real B1+ blocker, V7 writer routing rewritten, DeepSeek-pro validated for CODE dispatch but NOT for V7 writer, 3-build deepseek-pro xhigh experiment ALL FAILED"
status: green-with-known-blocker
main_sha: 5bddf2a695
main_green: true
working_tree_dirty: true  # docs/dispatch-briefs/2026-05-19-etymology-closeout-codex.md untracked (deferred, vol5/vol6 OCR prereq not yet met)
prs_merged_this_session:
  - "#2160 — fix(gate): wiki_coverage_gate dispatches decolonization_ban by subtype (closes #2155, m20 67% → 83%)"
  - "#2161 — fix(ci): zizmor MEDIUM triage (closes #2154, 21 MEDIUM → 0, FIRST DeepSeek-pro code dispatch shipped clean)"
  - 8 dependabot bumps merged with --admin (review/review broken-env per #2126):
    - "#2147 ci: github-actions group"
    - "#2146 vitest/coverage-v8"
    - "#2145 @astrojs/react"
    - "#2144 vitest"
    - "#2143 open-clip-torch"
    - "#2141 vulture"
    - "#2140 playwright"
    - "#2138 build"
direct_commits_to_main:
  - "15ecdf4892 feat(bakeoff): --effort flag for V7 writer bakeoff runner"
  - "5f20d357b6 fix(invoke_writer): surface runtime debug fields on no-response errors"
  - "9bfc90f5da docs(autopsy): 2026-05-19 Codex JWT leak — JSON content needs format-specific redactor"
  - "0fc0f0d427 fix(writer-trace): tolerate gemini-cli 0.42.0+ single-underscore MCP tool names + 2 tests"
  - "6535854618 docs(audit): B1 writer bakeoff REPORT.html + xhigh raw artifacts"
  - "eeee7959c0 docs(config): add V7-writer fallback chain to agent_fallback_substitutions (first version, tier-split)"
  - "c31eba4a20 docs(dispatch-brief): scope #2155 wiki_coverage_gate absence-bans fix for Codex"
  - "f80d886271 docs(dispatch-brief): #2154 zizmor MEDIUM triage to DeepSeek-v4-pro"
  - "b5a802b7e8 docs(config): collapse V7-writer fallback to deepseek-pro xhigh uniformly (no budget options per user direction)"
  - "3aa830fa4f fix(hermes): translate mcp__sources__* → mcp_sources_* in prompt before Hermes -z (PARTIAL FIX — does NOT solve MCP invocation gap)"
  - "9e5a6496b9 feat(v7-build): --effort flag for production V7 builds"
  - "5bddf2a695 fix(writer-correction): tolerate 4-backtick wrapper in module-only patch parser + 3 tests"
  - "Plus WORKSTREAMS.md rewrite as living-doc with tiered priority framework (committed during the dispatch sequence; SHA in commit log)"
active_dispatches: []
issues_filed:
  - "#2159 [runtime] codex CLI exits 1 in <1s via agent_runtime PTY+stdin path on large prompts (B1 bakeoff)"
issues_closed:
  - "#2155 wiki_coverage_gate absence-bans (shipped as #2160)"
  - "#2154 zizmor MEDIUM triage (shipped as #2161 — first DeepSeek-pro code dispatch)"
  - "#2157 [blocker] CoT-removal — closed with redirected scope (original brief over-scoped; corrected gate-parsing reality documented; narrower follow-ups noted but not blocking)"
headline_finding: "Hermes MCP-invocation gap is the REAL Tier-1 blocker for the post-2026-06-15 routing. DeepSeek-pro under Hermes -z mode does NOT emit structured tool-use calls — writer fabricates textbook citations, textbook_grounding gate HARD-rejects. Prefix translation (3aa830fa4f) was the wrong fix at the wrong layer. DeepSeek-pro code dispatch (delegate.py path, interactive Hermes) DOES work clean — shipped PR #2161 on first try."
next_session_first_item: "Investigate + fix the Hermes MCP-invocation gap deeper than the prefix-translation. The model needs to actually emit structured tool-use API calls under Hermes -z mode, not just write verification_trace blocks as text. Without this, deepseek-pro V7 writer hallucinates citations and the post-sunset routing is broken."
---

# Handoff — Hermes MCP-invocation gap is the real B1+ blocker; routing rewritten; DeepSeek-pro validated for code but not V7 writer

## TL;DR for the next session

This session set out to validate DeepSeek-pro xhigh as the post-2026-06-15 V7 writer for A1/A2/B1+. Three V7 builds were fired with deepseek-pro xhigh + a Hermes prefix-translation fix shipped mid-session. **All three failed.** The failures revealed that the Hermes-routed writer adapters' MCP-invocation gap is deeper than a name-prefix mismatch — DeepSeek-pro under `hermes -z` doesn't emit structured tool-use calls at all, just writes `<verification_trace>` blocks as text. Textbook citations are fabricated; `textbook_grounding` gate HARD-rejects.

**Separately**, the SAME DeepSeek-pro shipped a clean PR #2161 via `delegate.py dispatch` (interactive Hermes session, not `-z` mode). So DeepSeek-pro is validated as a **code-dispatch** agent but NOT as a **V7 writer** in current state.

**Routing config** was rewritten this session to uniform `deepseek-tools effort=xhigh` post-sunset (user direction: "we don't do budget options DAMMIT"). The routing now reflects the QUALITY policy. But the routing is at risk until the Hermes MCP-invocation gap is fixed — otherwise post-sunset modules will ship with hallucinated citations.

**User direction at close**: fix the Hermes MCP-invocation gap as the highest-priority next-session item. Then re-test deepseek-pro V7 writer (3 builds). Then test claude-tools (validated baseline). Codex tests deferred until #2159 lands.

## ⚠️ FIRST ITEM NEXT SESSION — Hermes MCP-invocation gap deeper investigation

The prefix-translation fix (`3aa830fa4f`) made the writer prompt use `mcp_sources_*` instead of `mcp__sources__*`. Hermes log confirms the names register correctly:

```
2026-05-19 18:48:21 INFO tools.mcp_tool: MCP server 'sources' (HTTP):
  registered 33 tool(s): mcp_sources_search_sources, mcp_sources_search_text, ...
```

But the same log shows ZERO tool *invocation* events across the entire 3-build window (18:48-19:14). The model registers tools, sees them in its tool-use schema, writes `<verification_trace>` blocks listing intended calls — **but never emits a structured tool-use API call**. From the B1 build's `python_qg.json`:

```json
"textbook_grounding": {
  "passed": false, "verdict": "REJECT", "severity": "HARD",
  "search_text_calls": 0,        ← writer never called search_text
  "textbook_result_hits": 0,
  "missing": ["Заболотний, 6 клас, с.93-101", "Литвінова, 6 клас, с.141", "Авраменко, 11 клас, с.42"],
  "reason": "corpus_missing"
},
"resources_search_attempted": {"passed": false, "severity": "HARD", "search_attempt_count": 0}
```

The cited textbooks in the writer's prose are **fabricated** — `search_text_calls: 0` means the writer never queried the textbook corpus, but it still listed Захарійчук / Литвінова / Авраменко references in `<verification_trace>` blocks and in module body prose.

### Hypothesis space for the fix

| Hypothesis | Why plausible | Test |
|---|---|---|
| `hermes -z` one-shot mode doesn't enable iterative tool-use | The flag is for non-interactive; tool-use loops typically need agent/conversation mode | Probe `hermes` interactive mode end-to-end with sources MCP, see if DeepSeek invokes tools |
| DeepSeek-pro itself doesn't aggressively emit tool-use without explicit prompt instruction | Other models (claude, gpt-5.5) chain tool-use because their training rewards it; DeepSeek may need explicit "you MUST call these tools" prompting | Modify the V7 writer prompt to explicitly require tool invocation, not just `verification_trace` |
| Hermes config gate (auxiliary.mcp.provider) is wrong for tool-use routing | The `auxiliary.mcp` section may route MCP-related operations through a different provider than the main writer | Inspect `~/.hermes/config.yaml` `auxiliary.mcp` block + cross-check with hermes docs |
| The HermesDeepSeekAdapter `cmd=[hermes, -z, prompt, -m, model]` is missing a `--tool-use` or similar flag | Code dispatch (which uses interactive session) DOES make tool calls — different invocation flags must exist | `hermes --help` deep dive + study how Hermes invokes tools in interactive code-dispatch mode |

### Concrete next steps

1. Run `hermes --help` exhaustively for tool-use related flags
2. Inspect `~/.hermes/config.yaml`'s `auxiliary.mcp`, `toolsets`, `delegation.inherit_mcp_toolsets` sections — those control tool routing in ways the writer adapter doesn't touch
3. Manually probe: `cat audit/2026-05-19-b1-writer-bakeoff/deepseek-tools-xhigh/writer_prompt.md | hermes -z - -m deepseek-v4-pro` + watch `~/.hermes/logs/agent.log` for invocation events
4. Compare flags + behaviour vs how `delegate.py dispatch --agent deepseek` invokes Hermes (which DOES make tool calls per #2161's clean output)
5. The fix may end up being: switch the writer adapter from `-z` mode to whatever mode delegate.py uses, OR add a flag, OR rewrite the prompt to be more aggressive about requiring actual tool calls

Estimate: 2-4 hours of investigation + a small adapter or prompt fix.

## Section 1 — What this session shipped

### Commits to main (13 direct + 2 PR merges)

1. **`15ecdf4892`** — `feat(bakeoff): --effort flag for V7 writer bakeoff runner`. Unblocked the codex-xhigh re-test that disconfirmed the effort hypothesis.
2. **`5f20d357b6`** — `fix(invoke_writer): surface runtime debug fields on no-response errors`. Turned "Writer call returned no response" into actionable diagnostics with returncode/duration/stderr_excerpt. Made the codex sub-second exit-1 finding deterministic.
3. **`9bfc90f5da`** — `docs(autopsy): 2026-05-19 Codex JWT leak — JSON content needs format-specific redactor`. Third recurrence of the secret-leakage pattern in 9 days (JSON `auth.json` got shell-pattern redactor applied → no-op → token leaked). MEMORY #M-5 expanded to cover format-aware redaction (shell vs JSON vs YAML vs TOML). User rotated Codex auth on direction.
4. **`0fc0f0d427`** — `fix(writer-trace): tolerate gemini-cli 0.42.0+ single-underscore MCP tool names`. Gemini CLI changed its MCP naming convention from `mcp__sources__*` to `mcp_sources_*`; pipeline gate was hardcoded for double-underscore. Both prefixes now accepted in `WRITER_ALLOWED_TOOL_PREFIXES`; built-in gemini tools (`run_shell_command`, `update_topic`) still correctly flagged. 2 new tests.
5. **`6535854618`** — `docs(audit): B1 writer bakeoff REPORT.html + xhigh raw artifacts`. 10-section HTML report with 5-way scoreboard (claude/qwen/deepseek-medium/deepseek-xhigh/codex-high/codex-xhigh/gemini), hypothesis verdicts, routing recommendations.
6. **`eeee7959c0`** — `docs(config): add V7-writer fallback chain to agent_fallback_substitutions`. First version had A1/A2/B1+ tier-split (medium for A1, xhigh for B1+). User pushed back on budget options.
7. **`c31eba4a20`** — `docs(dispatch-brief): scope #2155 wiki_coverage_gate absence-bans fix for Codex`. Dispatch brief that produced PR #2160.
8. **`f80d886271`** — `docs(dispatch-brief): #2154 zizmor MEDIUM triage to DeepSeek-v4-pro`. First project DeepSeek-pro CODE dispatch brief.
9. **`b5a802b7e8`** — `docs(config): collapse V7-writer fallback to deepseek-pro xhigh uniformly`. Per user direction "we don't do budget options DAMMIT": no tier splits, uniform xhigh across A1/A2/B1+ for the post-sunset routing.
10. **`3aa830fa4f`** — `fix(hermes): translate mcp__sources__* → mcp_sources_*`. ⚠️ **This was the wrong fix at the wrong layer.** Translated names in prompt but didn't solve the deeper invocation-mode issue. Keep it (still useful for surface-level alignment) but it's not load-bearing for MCP.
11. **`9e5a6496b9`** — `feat(v7-build): --effort flag for production V7 builds`. Mirrors bakeoff runner; lets builds override `WRITER_DEFAULTS[writer]['effort']` from CLI.
12. **`5bddf2a695`** — `fix(writer-correction): tolerate 4-backtick wrapper in module-only patch parser`. DeepSeek wraps correction responses in 4-backtick fences (CommonMark "code block containing code blocks"); parser now peels one wrapper layer + 3 new tests.
13. **WORKSTREAMS.md rewrite** as living document — V6 references removed, V7 reality + Tier 1-5 framework + operating rhythm + refresh rules + current content-status snapshot.

Plus 2 PR merges (`#2160` + `#2161`) and 8 dependabot bumps merged with `--admin` (advisory `review / review` fail per #2126).

### Issues filed / closed

- **Filed**: #2159 `[runtime] codex CLI exits 1 in <1s via agent_runtime PTY+stdin path on large prompts` — root-cause-blocking for codex-tools as V7 writer
- **Closed completed**: #2155 (shipped as #2160), #2154 (shipped as #2161)
- **Closed redirected**: #2157 (CoT-removal blocker — original brief was over-scoped, narrower follow-ups noted in close comment)

## Section 2 — The 3-build deepseek-pro xhigh experiment (all failed)

Fired three concurrent V7 builds at 18:48 local with `deepseek-tools --effort xhigh --worktree` after shipping the prefix-translation fix:

| Module | Level | Result | Where it failed |
|---|---|---|---|
| `my-morning` (m20) | A1 | ❌ FAILED at writer parse | `Writer output contains unnamed fenced block at line 496` — writer emitted artifact fences in sequence but skipped the explicit close fence between `module.md` and `activities.yaml`. Also dropped ALL plan_reasoning blocks (`sections_with_cot: 0`, consistent with v1 A1 bakeoff finding that deepseek drops CoT contract at A1). |
| `aspect-concept` | A2 | ❌ FAILED at python_qg after ADR-008 correction paths | First writer pass clean (5/5 plan_reasoning, structurally fine). word_count gate fired (output short), pipeline asked writer to expand, **correction response was 4-backtick-wrapped** → unparseable. Then plan_sections gate fired with same wrapper pattern. Both correction attempts unparseable. Parser fix `5bddf2a695` would have saved this build (shipped AFTER the build's worktree was branched). |
| `genitive-nuances` | B1 | ❌ FAILED at python_qg after ADR-008 correction paths | Writer phase clean (7/7 plan_reasoning blocks, all 6 fields per block, 552s duration, structurally fine — 38KB matches B1 bakeoff finding). Audit failures: `word_count` 3644/4000 (short by 9%), `plan_sections` missing "Родовий з прийменниками" entirely + 6 sections under word budget, `vesum_verified` 12 missing (typos: `будьяких`, `ізза`, `ізпід` — missing hyphens), and the **load-bearing finding**: `textbook_grounding` HARD-REJECT with `search_text_calls: 0`, `resources_search_attempted` with `search_attempt_count: 0`. Writer never queried the corpus; cited textbooks fabricated. |

**The B1 build is the smoking gun** for the Hermes MCP-invocation gap. The structurally-clean 38KB output was a mirage — the content is grounded in nothing. Reviewer phase can clean up some Russianisms but cannot rescue fabricated textbook citations; that's a HARD gate and the writer is the only stage with corpus access.

### What this means for the previous session's B1 bakeoff conclusions

The 2026-05-19-evening B1 writer bakeoff REPORT (`audit/2026-05-19-b1-writer-bakeoff/REPORT.html`) said deepseek-pro xhigh produced "full emission, 38 KB output, beats claude-tools by char count" with a caveat that writer-time MCP calls were 0. The interpretation at the time was "structurally complete, just no writer-time linguistic verification — reviewer phase compensates." **That interpretation was wrong.** The B1 build today proves the writer fabricates textbook citations when it doesn't actually invoke `search_text` — and reviewer phase cannot compensate for fabricated source references.

The REPORT.html will need a v2 update once the Hermes MCP-invocation gap is fixed (or proven unfixable). Until then, the existing v1 stands as a "structurally-clean but content-ungrounded" finding, with the gap clearly labeled.

## Section 3 — DeepSeek-pro CODE dispatch shipped clean (PR #2161)

**This is the good news**. Same agent (DeepSeek-v4-pro), same Hermes config — fired via `delegate.py dispatch --agent deepseek --model deepseek-v4-pro --effort xhigh` for #2154 zizmor MEDIUM triage:

- 21 MEDIUM findings → 0 (15 artipacked fixed via `persist-credentials: false`, 2 documented exceptions, 4 secrets-inherit made explicit)
- 11 files changed, all in scope
- Verifiable-claims preamble honored (raw zizmor before/after counts in PR body)
- X-Agent trailer correct
- Branch + PR + commit all clean
- **Even routed Gemini review locally** when the GH `review / review` action failed (per #2126)

This is the first DeepSeek-pro project-internal code dispatch. It validates DeepSeek-pro as a code-dispatch agent for the post-2026-06-15 substitution chain.

### Key insight on the two code paths

| Path | Mode | MCP behaviour | Status |
|---|---|---|---|
| `delegate.py dispatch --agent deepseek` | Interactive Hermes session, full agent loop, multi-turn tool use | Works — DeepSeek emits structured tool calls, Hermes dispatches them, tools execute | ✅ VALIDATED (PR #2161) |
| `invoke_writer(writer='deepseek-tools')` → `hermes -z PROMPT -m MODEL` | One-shot non-interactive | Broken — DeepSeek writes `<verification_trace>` as text, never emits structured tool-use calls | ❌ BLOCKED (need fix per Section "First Item Next Session") |

The two paths produce different DeepSeek behaviour. The writer-side fix is to either make `-z` mode emit tool calls, or switch to a different Hermes invocation mode for the writer adapter. **This is the highest-priority next-session work.**

## Section 4 — Routing recommendations (current state)

Updated in `scripts/config/agent_fallback_substitutions.yaml` at commit `b5a802b7e8`:

- **V7 writer pre-2026-06-15**: claude-tools (Opus 4.7 xhigh) — only writer currently making real writer-time MCP calls
- **V7 writer post-2026-06-15 (forced)**: deepseek-tools effort=xhigh uniformly A1/A2/B1+ — **AT RISK** until Hermes MCP-invocation gap is closed; if not closed, post-sunset modules ship with hallucinated citations
- **Code dispatch**: Codex (validated incumbent) + **DeepSeek-pro xhigh (newly validated via #2161, first try clean)** + Gemini (routine pipeline runs)
- **Not viable currently**: codex-tools writer (blocked by #2159), gemini-tools writer (built-in tools trip wrong_tool_family even with namespace fix)

## Section 5 — Mission framing update (user direction this session)

The user corrected the framing of where the project struggles:

1. **A1/A2 is the actual struggle territory.** B1+ in pure Ukrainian "always looks good" was a per-design statement, not a V7 audit-green proof. Today's failures confirmed: B1 also fails under V7 with deepseek-pro xhigh. The "B1+ is solid" claim must be retired until proven.
2. **History / biographies / literature is exciting but secondary.** Comes AFTER proving foreigners can learn Ukrainian. The language-learning A1/A2 path is the load-bearing thing.
3. **Audience is foreigners in Europe** (Hungarian, German, Dutch, French) — not Ukrainians-relearning-from-Russian (that audience is well-served inside Ukraine).
4. **Strategic frame**: EU welcoming Ukraine soon, Ukraine taking back the cultural and linguistic place Russia stole from it. "Russia spent centuries trying to convince the world that Ukrainian was a 'dialect' or 'regional variant' and that Russian was the gateway to Slavic culture."
5. **Teachers essential.** This is a teacher-ASSIST tool, not a teacher-replacement. The teacher loop (teachers flag pedagogical issues + feedback flows back into content) is part of the product, not an afterthought.

This framing should inform every subsequent decision — including which gaps get Tier 1 priority. The MCP-invocation gap is Tier 1 because without it, A1/A2 modules can't ship trustworthy content.

## Section 6 — Carry-over task list

Pulling forward from this session's queue + adding new items:

| # | Priority | Item | Effort |
|---|---|---|---|
| **NEW-1** | **TIER 1 — FIRST** | Fix Hermes MCP-invocation gap. DeepSeek-pro under `hermes -z` must emit structured tool-use calls, not just `verification_trace` text. Investigation + adapter/prompt fix. | 2-4h |
| NEW-2 | TIER 1 | After NEW-1 lands: re-test deepseek-pro V7 writer (3 builds — m20, a2/aspect-concept, b1/genitive-nuances). Validate that MCP invocation actually happens AND textbook_grounding passes. | ~30 min wall (parallel) |
| NEW-3 | TIER 1 | After NEW-2: claude-tools 3-build comparison (same 3 modules) for parity. Validates the current production default still works in V7 + gives audit-green baseline. | ~30 min wall |
| #2151 | TIER 1 | V7 preservation wrapper — spec exists (`docs/best-practices/pipeline/v7-build-preservation.md`), impl missing. Without it, parallel module builds don't archive consistently. Codex dispatch. | 2-3h |
| #1969 | TIER 1 | `resources_search_attempted=0` regression — multimedia obligation not fulfilled. Direct lesson-quality hit. Relates to MCP-invocation gap. | 1-2h |
| **NEW-4** | TIER 1 | A1 fence-sequence writer-prompt clarity fix. m20 build today failed because writer didn't emit explicit close fence between `module.md` and `activities.yaml`. Different from the 4-backtick wrapper issue (which is patched). Affects all writers, not just deepseek. Prompt edit. | ~30 min |
| **NEW-5** | TIER 2 | VESUM whitelist needs hyphenated-compound forms: `з-за`, `з-поза`, `з-поміж`, `з-під`. Build #8 missing list also showed writer typos `будьяких`, `ізза`, `ізпід` — those are real writer errors, not whitelist gaps. | Mixed — whitelist 15min, typo prevention is prompt work |
| #2159 | TIER 4 | Codex CLI silent-crash via runner PTY+stdin path on large prompts. Blocks codex-tools as V7 writer. Lower priority because post-sunset routing avoids codex-tools per current config; only matters if codex-tools is re-considered. | 2-4h investigation |
| **NEW-6** | TIER 4 | The cumulative DeepSeek-pro routing learning — add a row to MEMORY #M0 distinguishing the two code paths (code-dispatch ✓ vs V7 writer ❌-until-NEW-1). | 5 min |
| **NEW-7** | TIER 5 | B1 bakeoff REPORT.html v2 after Hermes MCP-invocation gap is closed (or proven unfixable). Updates routing recommendations + adds fabricated-citations evidence. | 1h |
| #2126 | TIER 4 | review/review GH action systematically failing — broken-env per the issue. Currently being --admin-merged through. Would save 1 advisory-fail per PR. Low impact, fix when convenient. | 1h |
| #2154 | DONE | Shipped via PR #2161 |
| #2155 | DONE | Shipped via PR #2160 |
| #2157 | CLOSED | Redirected scope (original brief was over-scoped on CoT removal) |

## Section 7 — State snapshot for cold-start

- **Main**: `5bddf2a695` (parser 4-backtick wrapper fix). 8 dependabot merges + 2 dispatch PRs + 13 direct commits since predecessor handoff's `7012043def`.
- **Working tree**: dirty — `docs/dispatch-briefs/2026-05-19-etymology-closeout-codex.md` untracked (deferred per ESUM OCR prereq not met).
- **Active dispatches**: 0. #2154 deepseek + #2155 codex both shipped + merged this session.
- **Open PRs**: 2 (dependabot merge-conflicted ones — #2139 virtualenv + #2142 onnxruntime; dependabot will auto-rebase) + #1873 (starlight 0.39.2 — real Frontend test failure, needs investigation).
- **Hermes log**: `~/.hermes/logs/agent.log` ~1.9MB, contains the 0-invocation evidence in the 18:48-19:14 window today.
- **MCP server**: `localhost:8766/mcp`, sources DB at ~670K entries, healthy.

## Cold-start protocol for the next session

1. Read this handoff (you're doing it now).
2. Orient via Monitor API:
   ```
   curl -s http://localhost:8765/api/state/manifest
   curl -s http://localhost:8765/api/orient
   curl -s 'http://localhost:8765/api/comms/inbox?agent=claude'
   ```
3. Skim `~/.hermes/logs/agent.log` for any MCP `invok` / `tool_call` entries that have appeared since this session — if any, the gap is intermittent rather than total.
4. **Pick up NEW-1 (Hermes MCP-invocation gap investigation) as the immediate first action.** Don't fire any more V7 writer experiments before this lands — they'll just waste minutes producing the same fabricated-content failures.
5. After NEW-1 ships: fire the 3-build deepseek validation (NEW-2), then claude-tools comparison (NEW-3). Codex tests stay deferred until #2159 lands.

## Provenance + cross-links

- v1 B1 bakeoff REPORT: `audit/2026-05-19-b1-writer-bakeoff/REPORT.html`
- Today's 3 V7 build artifacts (failed): `.worktrees/builds/{a1-my-morning,a2-aspect-concept,b1-genitive-nuances}-20260519-184*/curriculum/l2-uk-en/.../`
- B1 python_qg.json with the fabricated-citation evidence: `.worktrees/builds/b1-genitive-nuances-20260519-184819/curriculum/l2-uk-en/b1/genitive-nuances/python_qg.json`
- Hermes config: `~/.hermes/config.yaml` (33 MCP tools registered, single-underscore convention)
- Routing config (current): `scripts/config/agent_fallback_substitutions.yaml` — uniform deepseek-pro xhigh post-sunset
- WORKSTREAMS.md (rewritten as living doc): `docs/WORKSTREAMS.md`
- PR #2160 (m20 wiki_coverage_gate fix): merged at `474096de69`
- PR #2161 (#2154 DeepSeek zizmor — FIRST CODE DISPATCH): merged into main
- Predecessor handoff: `docs/session-state/2026-05-19-evening-b1-bakeoff-deepseek-disconfirmed.md`
- Bug autopsy (JWT leak): `docs/bug-autopsies/secret-leakage.md#2026-05-19`
- Issue filed: #2159
- Issues closed: #2154, #2155, #2157

## Open dispatches at handoff

None. All work either landed or was deferred to next session.

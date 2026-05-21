---
date: 2026-05-21
session: "Evening — gate cascade exposed: 3 gate bugs hidden behind one another; 2 PRs merged, 1 to go"
status: yellow-cascade-pattern + 2-PRs-merged + 0-active-dispatches + 0-active-builds
main_sha: 6807f3ee3f
main_green: clean (PR #2184 merged, blocking checks green; review/review advisory still broken — Gemini CI auth missing)
working_tree_dirty: true  # pre-existing inherited items + this session-state file
prs_merged_this_session:
  - "#2182 feat(agy): V7 writer telemetry parser + prompt directives (codex dispatch agy-v7-integration-2026-05-21)"
  - "#2184 fix(wiki_coverage_gate): scope to deepest heading + drop YAML re-escape (this orchestrator, inline)"
prs_opened_this_session: []
direct_commits_to_main: []  # all changes went through PR
active_dispatches: []
active_builds: []
issues_filed: []
issues_closed: []
builds_completed:
  - "build/a1/my-morning-20260521-140634 (claude-tools #6) — failed wiki_coverage_gate at 83.33% (FALSE POSITIVE — gate bug masked valid content; verified post-fix gate gives 18/18 against unchanged artifacts)"
  - "build/a1/my-morning-20260521-145016 (claude-tools #7) — failed python_qg textbook_grounding (topical_mismatch) — third gate bug exposed in cascade"
headline_finding: "Gate cascade pattern: each fix exposes the next gate's bug. Build #5 hit vesum_verified (fixed PR #2173 by Codex morning); build #6 hit wiki_coverage_gate at 83.33% (fixed PR #2184 inline today — two bugs: _location_text scoped to H1 over H2, _activity_text yaml.safe_dump doubled apostrophes); build #7 hit textbook_grounding topical_mismatch (writer used H3 ### Крок N sub-headings — pedagogically better — but _extract_blockquote_records treats H3 as section_title, flooding topic_tokens with the long technical Крок heading so the blockquote can't overlap). Each previous gate was masking the next. The 22/22 'one rebuild away' from the morning handoff was structurally wrong: gates run sequentially, so earlier failures hide later ones."
next_session_first_item: "Decide between (A) keep grinding gates one at a time (fix _extract_blockquote_records to track H2 only as section_title; ~10 LOC + 1 test; then re-run claude-tools; expect ~22/22 OR another hidden gate) vs (B) hold gate fixes, run a thorough audit-gate review across all 24 python_qg gates + wiki_coverage_gate + their interactions, identify all writer-output-pattern assumptions, fix them as one PR. Option B is the senior-dev move if we want a durable 'first complete V7 module' answer instead of incremental whack-a-mole."
---

# Evening handoff — gate cascade exposed, 2 PRs merged, next fix queued

## TL;DR

The morning handoff's "next rebuild should hit 22/22" was structurally wrong because **gates run sequentially and earlier failures hide later ones**. Three separate gate bugs surfaced one after another today, each only visible after the previous was fixed:

1. **vesum_verified** — failed build #5 on `**користу**-` morphological stem fragment. Fixed by Codex PR #2173 (merged morning).
2. **wiki_coverage_gate** — failed build #6 at 83.33% coverage; two distinct bugs (H1/H2 title collision in `_location_text` + YAML apostrophe re-escape in `_activity_text`). Fixed by inline PR #2184 (merged this session).
3. **textbook_grounding (python_qg)** — failed build #7 with `topical_mismatch` because writer used H3 `### Крок N:` sub-headings (pedagogically better than build #6's inline-bold), and `_extract_blockquote_records` treats H3 as a section heading, flooding `topic_tokens` with the long technical Крок heading. Build #6's inline-bold style passes the same gate.

Diagnosed, brief documented, **not yet fixed** — stopping the cascade so the user can decide between incremental whack-a-mole vs a holistic gate-quality audit.

## Section 1 — Build state matrix at end of session

| Build | Time | Writer | Outcome | Gate that exposed the bug | Resolution |
|---|---|---|---|---|---|
| #5 | 10:10 UTC | claude-tools | 21/22 python_qg | vesum_verified (stem fragment) | Stem exemption PR #2173 (morning, merged) |
| #6 | 14:06 UTC | claude-tools | python_qg ✅ → wiki_coverage_gate ❌ at 83.33% | wiki_coverage detection bugs (location_text + activity_text) | Gate fix PR #2184 (this session, merged at 6807f3ee3f) |
| #7 | 14:50 UTC | claude-tools | python_qg ❌ on textbook_grounding | _extract_blockquote_records (H3 section_title) | Not yet fixed — handed off for decision |

**Smoking-gun verification** that PR #2184 was correct: re-running the **fixed** gate against **unchanged** build #6 artifacts returned **18/18 PASS** (100% coverage). The build's correction loop produced valid content; the gate detection bug ate 7 successful fix applications and reported 83.33%. The two regression tests added to `tests/audit/test_wiki_coverage_gate.py` pin both bugs (H1/H2 collision + apostrophe re-escape) against future regressions.

## Section 2 — PR #2184 details (wiki_coverage_gate two-bug fix)

**Branch**: `fix/wiki-coverage-location-scoping-and-yaml-escape`
**Merged**: `6807f3ee3f`
**Files**: `scripts/audit/wiki_coverage_gate.py` (+58 -3), `tests/audit/test_wiki_coverage_gate.py` (+147 -0)
**CI**: all blocking checks green (pytest, ruff, gitleaks, CodeQL, schema drift, frontend, quality gates radon, lint prompts, lesson schema drift, secret scanning). Only `review / review` failed — Gemini auth missing in workflow env (same advisory failure that PR #2182 had).

### Bug 1 — `_location_text` heading-depth blindness

When `implementation_map.location` matched both an H1 title and an H2 section (e.g. `# Мій ранок` + `## Мій ранок`), the function returned the first match in document order — the 4-line H1 title block — instead of the H2 section that actually held the substance. **Fix**: score candidates by heading depth (deeper wins), tie-break on title-length proximity to the `location_key`.

### Bug 2 — `_activity_text` YAML apostrophe re-escape

The function returned `yaml.safe_dump(activity, ...)`, which round-trips inner apostrophes inside single-quoted YAML strings as `''`. The phonetic IPA pair `Вимова: [прокидайес':а]` in `act-5` became `Вимова: [прокидайес'':а]` in the dump, so the wiki-manifest marker no longer substring-matched and `err-2` / `err-3` failed even though the artifact was correct. **Fix**: recursive `_flatten_strings` walk over the YAML-decoded structure.

## Section 3 — PR #2182 details (agy V7 integration, Codex dispatch)

**Branch**: `feat/agy-v7-integration-2026-05-21`
**Merged**: `67648a1ce2`
**Files**: 7 files, +461 -16
**CI**: all blocking checks green (same `review / review` Gemini-auth advisory failure as PR #2184).

Codex's key catch: the dispatch brief assumed agy's stdout would emit `●` / `⎿` markers (per the morning's curl-via-Bash bust). The Step-0 probe showed `agy -p --dangerously-skip-permissions` print mode produces **no** surface markers — the real tool-call telemetry lives in the Antigravity transcript JSONL (`PLANNER_RESPONSE` events with `tool_calls`, `MCP_TOOL` events with `content`). Codex pivoted to transcript-based parsing, which is the durable approach.

The PR also adds `{WRITER_SPECIFIC_DIRECTIVES}` placeholder + scaffolding in `linear_pipeline.py` + `prompt_builder.py`. For non-agy writers (claude-tools, gemini-tools, codex-tools, deepseek-tools) the directive block is empty — no behavior change. Build #7 confirmed this: claude-tools writer behavior unchanged from #6 except in how the writer chose to structure markdown.

## Section 4 — Build #7 forensics: the third gate bug

### Symptoms

```
{"event": "module_failed", "phase": "python_qg",
 "reason": "Python QG failed after ADR-008 correction paths"}

python_qg.json gates.textbook_grounding:
  passed: false
  verdict: REJECT
  severity: HARD
  required: 1
  matched: []
  missing: ["Захарійчук Grade 1, p.24", "Захарійчук Grade 1, p.52"]
  blockquotes_checked: 2
  long_blockquotes_checked: 2
  search_text_calls: 2
  textbook_result_hits: 10
  reason: "topical_mismatch"
```

### Diagnosis

The writer's two blockquotes (Кнак's day-plan from Захарійчук Grade 1 p.24; Євген's САМ-morning from p.52) are:

- Real, attributed, ≥30 words each ✅
- Returned by the writer's `search_text` calls as chunk_ids `s0024` and `s0052` ✅
- Pedagogically correct content matching the plan's `references` exactly ✅

But the writer organized the module with H3 `### Крок N:` sub-headings under H2 sections (build #6 used **bold-inline** Крок markers instead). The blockquote sat under `### Крок 4: Введення високочастотних зворотних дієслів другої дієвідміни — дивитися`, an H3 heading. Look at `_extract_blockquote_records`:

```python
heading = re.match(r"^\s{0,3}#{1,6}\s+(?P<title>.+?)\s*#*\s*$", line)
if heading:
    current_section = re.sub(r"[*_`~]+", "", heading.group("title")).strip()
```

The regex matches H1–H6, so the deepest heading wins as `section_title`. Then in the topic check:

```python
topic_text = f"{record['section_title']} {plan_reasoning}".strip()
if not _quote_topic_matches(quote, topic_text):
    topical_mismatches.append(ref)
```

With `plan_reasoning` ≈ empty (`<plan_reasoning>` blocks live in the writer output but are stripped from module.md), `topic_text` = the long technical H3 heading. `_topic_token_keys` produces ≥2 tokens, so the early-pass-if-<2 escape doesn't fire, and the literal Захарійчук quote (about a frog named Knack writing a day-plan) doesn't lexically overlap with "Введення високочастотних зворотних дієслів другої дієвідміни".

### Proof

Running `_textbook_grounding_gate` against unchanged **build #6** artifacts (inline-bold Крок, no H3):

```
Build #6 textbook_grounding: passed=True reason=None
  matched=['Захарійчук Grade 1, p.24', 'Захарійчук Grade 1, p.52']
```

Running the same gate against **build #7** artifacts (H3 Крок sub-headings):

```
Build #7 textbook_grounding: passed=False reason=topical_mismatch
  matched=[]
  missing=['Захарійчук Grade 1, p.24', 'Захарійчук Grade 1, p.52']
```

Same writer, same plan, same chunk_id retrievals — only the heading depth differs. The gate is brittle to a markdown-formatting choice that doesn't affect pedagogical quality.

### Proposed fix (queued, not applied)

`scripts/build/linear_pipeline.py:7015` — change the heading regex to only track H1/H2 as `current_section`:

```python
heading = re.match(r"^\s{0,3}#{1,2}\s+(?P<title>.+?)\s*#*\s*$", line)
```

(Or pass the heading depth through and filter at section_title-assignment time.) Add a regression test that puts a blockquote under H3 inside H2 and asserts the H2 wins as section_title. ~10 LOC + 1 test.

## Section 5 — The cascade pattern itself (more important than any single fix)

Every gate fix today exposed the next gate's bug:

```
build #5 [vesum_verified ❌] ──fix #2173──> build #6 [vesum ✅, wiki_coverage_gate ❌]
                                         ──fix #2184──> build #7 [vesum ✅, wiki_coverage ✅, textbook_grounding ❌]
                                                                  ──fix??──> build #8 [?, ?, ?, ??]
```

Two interpretations:

1. **Coincidence + sample-size-of-1**: The first complete-V7 module just happens to be the first module to traverse all 24 python_qg gates + wiki_coverage_gate cleanly. Of course brittle gates surface bugs only when content quality is high enough to reach them. Keep going; the cascade will stop in 1–3 more rounds.

2. **Structural fragility**: The gate suite was incrementally built assuming specific writer-output patterns. Today's writer-prompt directives (≥30-word blockquote, INJECT_ACTIVITY, the agy `{WRITER_SPECIFIC_DIRECTIVES}` scaffold) plus stochastic writer markdown choices (H3 vs inline-bold for Крок markers) push the writer into output shapes the gates weren't validated against. Each gate has its own assumption set; we'll keep finding bugs at the rate the writer surfaces new patterns. A holistic audit beats incremental whack-a-mole.

Both interpretations point at a real signal. The decision is whether to spend another half-day on incremental fixes hoping to hit 22/22, or pause for a thorough audit. **My recommendation: at least a half-day audit pass** on the 24 python_qg gates + wiki_coverage_gate to:

- Catalogue every writer-output assumption each gate makes (regex shapes, marker conventions, section detection rules, claim-text matching).
- Stress-test each gate against 3–4 known good module variants (H2-only vs H3-sub-section, inline-bold vs literal Крок-heading, Cyrillic apostrophe variants, single-section narratives vs four-section).
- File one PR with all required gate-detection fixes + regression tests for each.

This is the kind of work that benefits from a focused dispatch — codex-tools or claude-tools at xhigh with the gate code in scope and explicit "find every brittle pattern" instructions.

## Section 6 — Active state of the session

- **0 active dispatches** — agy-v7-integration done + merged; esum-textpdf-parser and esum-abbyy-parser landed earlier (PR #2180, #2181, plus data regen at #c56835257b and autopsy at #df1d1ecf71).
- **0 active builds** — build #6 + build #7 both finished, artifacts auto-committed per #M-10 to branches `build/a1/my-morning-{stamp}`. Worktrees still on disk for forensic reference.
- **0 unread inbox items** — `comms/inbox?agent=claude` empty at start; nothing new.
- **No scheduled wakeups pending** — wakeup at 16:34 already fired and was logged.
- **Origin/main at** `6807f3ee3f` (PR #2184). Two commits past where this session started.

## Section 7 — Working-tree state at handoff

```
?? .agents/mcp_config.json                                                    # pre-existing morning shim
?? audit/2026-05-21-flash-3.5-ua-quality/                                     # pre-existing morning audit dir
?? curriculum/l2-uk-en/_orchestration/                                        # pre-existing per-build dir (artifacts persisted)
?? docs/dispatch-briefs/2026-05-21-agy-mcp-telemetry-shim-codex.md            # superseded shim brief
?? docs/session-state/2026-05-21-evening-gate-cascade-three-bugs-one-after-another.md  # this file
```

None of these are mine to commit beyond the handoff. The build worktrees `.worktrees/builds/a1-my-morning-20260521-{140634,145016}` are intact per #M-10 (load-bearing forensic evidence; auto-committed to branches `build/a1/my-morning-{stamp}`).

## Section 8 — Cold-start sequence for next session

1. Read this handoff first (you're here).
2. Orient via Monitor API (`/api/state/manifest` → `/api/orient` → `/api/comms/inbox?agent=claude`).
3. **Decision card**: Section 5 above. Pick A (one more gate fix, hope) or B (holistic audit). I recommend B but A is defensible.
4. If A: fix `_extract_blockquote_records` to track H1/H2 only as `section_title`; add 1 regression test; PR; merge; rebuild claude-tools `a1/my-morning`. If 22/22 → promote.
5. If B: scope an audit-gate hardening dispatch brief targeting Codex `xhigh` or Claude headless `xhigh`; brief should include the cascade evidence here + the 3 known gate failure shapes + a list of all python_qg gates + the wiki_coverage_gate, with an instruction to stress-test each against known-good and known-bad module variants.
6. Cross-validate gemini-tools and deepseek-tools rebuilds (P1) come AFTER the gate question resolves.

## Section 9 — Open follow-ups

| # | Subject | Priority | Notes |
|---|---|---|---|
| 1 | Decide A-incremental-fix vs B-holistic-gate-audit | **P0 next session** | Section 5 of this handoff |
| 2 | Fix `_extract_blockquote_records` H3 issue | P0 if A chosen | Section 4 of this handoff; ~10 LOC |
| 3 | Holistic gate-quality audit + fix-all PR | P0 if B chosen | Section 5 of this handoff |
| 4 | gemini-tools + deepseek-tools rebuilds | P1 | Blocked on first complete claude-tools build |
| 5 | codex-tools rollout-flush race | P2 | Inherited from morning handoff |
| 6 | PR #2168 amelina stub blocker | low | Inherited; 1158/1159 plans valid |
| 7 | `review / review` CI auth broken | P2 | Gemini API key missing in workflow env; advisory failure on every PR today |

## Sign-off

This session closed two real bugs (PR #2184 inline + PR #2182 agy dispatch) and exposed a third (build #7 textbook_grounding). The cascade pattern is the durable headline finding. We're closer to "first complete V7 module" but the path keeps revealing new gate-detection brittleness; recommend stopping the whack-a-mole and doing one holistic gate-quality pass.

Each gate fix today is independently load-bearing — the wiki_coverage gate would have continued silently mis-detecting on every future build. Three fixes feels expensive but the alternative was permanent false-fail noise in every dim-aware build going forward.

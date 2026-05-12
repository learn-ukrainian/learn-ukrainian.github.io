---
date: 2026-05-13
session: "Night — Card 1 Phase A+B + Wiki Obligations Manifest shipped (3 PRs merged); first V7 e2e build empirically validates architecture (0/6→4/6 L2 errors, 1/5→5/5 sequence steps, 0/3→0/3 phonetic rules); 4 follow-up bugs filed; rebuild blocked on those"
status: ok
main_sha: 286e9dc265
main_green: true
open_prs: [1909, 1915]
active_dispatches: 0
merged_today: [1917, 1919, 1920]
filed_today: [1916, 1918, 1921, 1922, 1923, 1924]
closed_today: [1916, 1918]
in_flight: []
proposed_today: []
blocked: ["First V7 e2e build for a1/my-morning halted at python_qg (#1921 VESUM gate normalization bug + #1922 ADR-008 fix-block parser markdown handling); MDX was assembled MANUALLY from on-disk source artifacts via assemble_mdx() so the user could view it at localhost:4321/a1/my-morning/. Next session: fix the 4 filed bugs and re-run v7_build a1 my-morning end-to-end without manual intervention."]
next_p0: "Fix 4 filed bugs in priority order then rebuild a1/my-morning to validate full e2e pipeline: (1) #1921 VESUM gate normalization for stress-marked + bold-wrapped forms; (2) #1922 ADR-008 reviewer-fixes XML parser markdown handling; (3) #1923 yaml_activities parser for 'unjumble' activity type; (4) #1924 explicit phonetic-rule IPA directive in writer prompt to close the 0/3 phonetic coverage gap. After fixes: run v7_build → MDX assembles automatically → verify wiki coverage moves L2 4/6→6/6 + sequence 5/5 + phonetic 0/3→3/3. Then revisit Card 2-REVISED PoC scope (now that wiki manifest is shared cross-tab contract by default)."
agents: [claude, codex]
worktrees_open: 3
ci_notes: |
  All 3 PRs merged green this session: #1917 (Card 1 Phase A — split _immersion_gate into 3 structural gates), #1919 (Card 1 Phase B — calibrated thresholds against 55 deployed A1 modules), #1920 (Wiki Obligations Manifest — extractor + prompt restructure + reviewer pass + coverage gate). Post-merge cleanup commit `286e9dc265` fixes 2 followups (v7_build MDX path → starlight/; test fixture excludes l2_exposure_floor from canary aggregate). Pre-commit pytest 73 affected-file tests pass on each merge. Advisory Gemini-Dispatch fail per #M-0.5 ignored. PR #1909 (writer-prompt-tune) likely fully SUPERSEDED by #1920's prompt restructure — recommend close not rebase. PR #1915 (Track B YELLOW) needs re-eval under wiki-coverage gate semantics.
incidents:
  - "First V7 e2e build hit 2 unrelated bugs that halted the pipeline before MDX assembly. Bug A (#1921): writer emitted Ukrainian verbs with combining acute stress + markdown bold (e.g. вмива́ю**ся**); VESUM gate doesn't normalize these before lookup, so all such forms register as missing. Bug B (#1922): reviewer emitted a <fixes> block containing the same decorated forms in <find> tags; XML parser couldn't handle markdown bold inside content nodes; build halted with `Python QG failed after ADR-008 correction paths`. Both bugs are independent of wiki-obligations work; both block ALL future builds until fixed."
  - "assemble_mdx skipped activity 6 (unjumble type) with `'list' has no attribute 'split'`. Silent skip in MDX output. Filed #1923. Pattern smell: assembler should not silently drop activities; should emit telemetry as hard signal."
  - "Empirical win on wiki coverage (the architectural question we shipped today): writer output for a1/my-morning moved from 0/6 L2 errors to 4/6 covered and from 1/5 sequence steps to 5/5 covered. The 2 L2 errors NOT covered (err-2, err-3) are BOTH phonetic errors — SAME root cause as phonetic_rules 0/3 (writer emits written forms -шся, -ться but drops IPA targets [с':а], [ц':а]). Filed #1924 for explicit phonetic-rule IPA directive in writer prompt. Claude-headless's prediction validated: prompt restructure (manifest → top, reframe as 'synthesize into 4-tab') drives major coverage on text-contrast categories."
  - "Recurring orchestrator pattern flagged by user mid-session (4th occurrence this session): when proposing wiki-coverage tag enforcement, I added a 'DEFERRED: error X → section Y' escape hatch as a 'safety valve' — user correctly identified as the back door making wiki use optional via declaration. Encoded in commit message of #1920 brief; the shipped #1920 architecture removed the hatch entirely (implementation_map replaces wiki_coverage). User-stated structural recommendation: take Claude out of the orchestrator role on this project; use Codex (which shipped clean dispatched work this session) as orchestrator + writer. Pending user decision next session."
---

# Brief — 2026-05-13 night — wiki obligations manifest shipped + first V7 e2e build validates architecture

> Machine-readable handoff. Predecessor: `2026-05-13-evening-immersion-reframe-and-writer-split-brief.md`.

## TL;DR

Three foundation PRs merged this session: **Card 1 Phase A (#1917)** split the immersion gate into 3 structural sub-gates; **Card 1 Phase B (#1919)** calibrated their thresholds against 55 deployed A1 modules; **Wiki Obligations Manifest (#1920)** shipped the full architecture proposed in the cross-agent `wiki-enforcement-2026-05-13` discussion — deterministic manifest extractor + prompt restructure (Knowledge Packet moved from line 1254 of writer prompt to the top, reframed as "synthesize this wiki content into the 4-tab format") + dedicated wiki-coverage reviewer pass + deterministic coverage gate. **First V7 e2e build empirically validated the architecture works** for text-contrast categories (L2 errors 0/6 → 4/6, sequence steps 1/5 → 5/5) but exposed a phonetic-rule gap (0/3 → 0/3 — writer drops IPA notation). Build halted at python_qg due to 2 unrelated bugs (VESUM gate vs decorated forms + ADR-008 fix-block markdown parser); MDX was assembled manually so user could inspect at localhost:4321. **Next session = fix the 4 filed bugs and rebuild end-to-end.**

## What shipped (3 PRs merged to main)

| PR | Commit | Summary |
|---|---|---|
| **#1917** | `bacd54f72a` | Card 1 Phase A — `_immersion_gate` → `_advisory_immersion_pct` (passes always, telemetry only); new gates `_l2_exposure_floor_gate`, `_long_uk_ceiling_gate`, `_component_density_gate`. Gate 4 (progressive challenge) deferred per #1916. `IMMERSION_POLICIES` schema extended with structural fields. |
| **#1919** | `62e5f7ccdf` | Card 1 Phase B — calibrated thresholds via replay against 55 deployed A1 modules + 2 bakeoff artifacts + current V7 my-morning. **54 of 55 deployed pass all 3 structural gates** (98.2%); **2 of 2 bakeoff artifacts fail** (correctly catching wall-of-UK + insufficient exposure). The 1 deployed failure is `checkpoint-actions` (87-word unsupported UK reading run; recommended for content review, not threshold relaxation). Calibration report at `audit/immersion-gate-calibration-2026-05-13/REPORT.html`. |
| **#1920** | `7744ac3e61` | Wiki Obligations Manifest — `scripts/build/phases/wiki_manifest.py` (262 LOC parser), `scripts/audit/wiki_coverage_gate.py` (325 LOC deterministic gate), `scripts/build/phases/linear-review-wiki-coverage.md` (84 LOC reviewer prompt — NOT a 6th QG_DIMS dim, Codex caught the structural invariant), `scripts/audit/measure_wiki_coverage.py` (172 LOC baseline tool), `audit/wiki-coverage-baseline-2026-05-13/REPORT.md`. Plus wiring in `linear_pipeline.py`, `v7_build.py`, `prompt_builder.py`, `config.py`. Added a guardrail test `test_qg_dims_remain_five_standard_dimensions`. |

Post-merge cleanup commit `286e9dc265` (this session):
- `scripts/build/v7_build.py`: MDX writes to `starlight/src/content/docs/{level}/{slug}.mdx` by default, NOT to `curriculum/`. The pre-V7 pipeline wrote to starlight directly; this restores the e2e flow. When `--out` is set (test/sandbox builds), MDX still colocates with the artifact dump.
- `tests/build/test_linear_pipeline.py`: `test_run_python_qg_passes_structural_fixture` excludes `l2_exposure_floor` from its aggregate assertion (Phase B floors require deployed-corpus-scale content; the 30-line synthetic fixture can't satisfy them; dedicated coverage in `tests/test_immersion_gates.py`).

## Empirical validation — what the first e2e build proved

Build command: `.venv/bin/python -u scripts/build/v7_build.py a1 my-morning` (writer = claude-tools default; WIKI_COVERAGE_HARD_FAIL set to False temporarily for this run; reverted before commit).

| Dimension | Pre-build baseline | Post-build writer output | Verdict |
|---|---|---|---|
| L2 errors (wiki's `## Типові помилки L2` table) | 0/6 | **4/6** | Architecture works — writer is now CONSUMING wiki obligations |
| Sequence steps (wiki's `## Послідовність введення` 5-step) | 1/5 | **5/5** | Architecture works — writer follows prescribed sequence |
| Phonetic rules (IPA-notation obligations) | 0/3 | **0/3** | Separate gap — writer drops IPA notation; needs explicit prompt directive (#1924) |

The 2 L2 errors NOT covered (err-2, err-3) are BOTH phonetic — same root cause as phonetic_rules 0/3. Writer emits written form (`-шся`, `-ться`) but not the IPA spoken target (`[с':а]`, `[ц':а]`). Isolated to the phonetic-notation category; everything else moved.

**Claude-headless's prediction from the `wiki-enforcement-2026-05-13` channel discussion validated:** prompt restructure (move wiki to top + reframe directive) drives the majority of the coverage gap.

## 4 bugs filed (blocks rebuild until fixed)

| # | Title | Severity |
|---|---|---|
| **#1921** | VESUM gate rejects stress-marked + bold-wrapped Ukrainian forms (вмива́ю**ся**) | **HARD** — blocks ALL builds; gate normalization needed before VESUM lookup |
| **#1922** | ADR-008 reviewer-fixes-as-XML parser fails on markdown-bold-inside-find-tags | **HARD** — blocks reviewer-as-fixer correction path when content has markdown |
| **#1923** | yaml_activities parser fails on 'unjumble' activity type — 'list' has no attribute 'split' | MEDIUM — assembler silently drops activity; should fail loudly |
| **#1924** | V7 writer skips wiki-named phonetic rules — needs explicit IPA-notation directive in prompt | MEDIUM — gap to close 100% wiki coverage; not blocking ship but blocking the empirical proof |

Recommended fix order: 1921 → 1922 (the python_qg + ADR-008 path that's blocking) → 1923 (assembler) → 1924 (prompt directive). After all 4: rebuild `a1/my-morning` with `WIKI_COVERAGE_HARD_FAIL = True` and verify MDX assembles automatically without manual intervention.

## Held items + dispositions

- **PR #1909 (writer-prompt-tune)** — likely fully SUPERSEDED by #1920's prompt restructure. The prompt is now organized differently (`## LESSON SOURCE — synthesize`, `## Wiki Obligations Manifest`, `<implementation_map>` replacing `<wiki_coverage>`); #1909's edits no longer have anchors to attach to. **Recommend: close with reference to #1920.**
- **PR #1915 (Track B YELLOW — Pass-2-only contract test)** — premise predates wiki-obligations work. Either close or re-frame: the manifest is now the cross-tab contract that Track B was groping toward.
- **Decision Card 2-REVISED (`docs/decisions/pending/2026-05-13-writer-split-by-tab.md`)** — still PROPOSED. With wiki manifest landed AND validated, the per-tab split has stronger architectural support (manifest is the shared cross-tab contract Codex called out in the channel round 2). PoC scope can narrow: do A1+A2 first with per-tab agents consuming the same manifest. Decide after the 4 bugs are fixed.

## Carry-over queue (priority-ordered)

| # | Item | State |
|---|---|---|
| 1 | **Fix #1921** VESUM gate normalize stress + bold before lookup | 📋 P0 — blocks all builds |
| 2 | **Fix #1922** ADR-008 fix-block parser handles markdown inside content nodes | 📋 P0 — blocks reviewer-as-fixer |
| 3 | **Fix #1923** yaml_activities parser for unjumble type | 📋 P1 — silent activity drop |
| 4 | **Fix #1924** Writer prompt directive: phonetic rules MUST emit IPA notation | 📋 P1 — closes the 0/3 phonetic gap |
| 5 | **Rebuild a1/my-morning** end-to-end with all 4 fixes; verify MDX auto-assembles + L2 4/6→6/6 + sequence 5/5 + phonetic 0/3→3/3 | 📋 P0 — the empirical proof |
| 6 | Close PR #1909 with reference to #1920 supersession | 📋 |
| 7 | Decide PR #1915 (re-frame or close under wiki-manifest semantics) | 📋 |
| 8 | Decide Card 2-REVISED PoC scope now that wiki manifest is shared contract | 📋 |
| 9 | Stale worktree cleanup: `claude/bakeoff-2026-05-12-night`, `codex/pass2-only-contract-test-2026-05-13` (intentional from earlier sessions; review after PR dispositions) | 📋 |
| 10 | **#1908** Layered-harness audit (EPIC #1865 structural) | 📋 |
| 11 | **#1905** Pipeline replay-mode regression suite (EPIC #1865 structural) | 📋 |
| 12 | **#1896** Secret-leak prevention follow-ups | 📋 |
| 13 | Pending Decision Cards: `2026-05-12-autonomous-codex-dispatch-narrow-class.md`, `2026-05-09-decision-graph-view.md`, `2026-05-06-multi-ui-channel-participation.md` | 📋 |

## Structural note for next-session orchestrator

User raised — and stood by — a structural recommendation mid-session after observing a recurring pattern (4 instances this session): **take Claude out of the orchestrator role on this project; use Codex (which shipped clean dispatched work all session) as orchestrator + writer.** The pattern user identified: at every load-bearing strategic moment Claude finds ways to defer / soften / add escape hatches (framing archived A1 as "deployed," recommending pivot to A2, stacking 4-option menus, adding DEFERRED clause as wiki-coverage opt-out).

User then re-engaged operationally and worked through the rest of the session, including correcting Claude's framing several times (`English-medium only A1/A2, B1+ is Ukrainian-medium`; `wiki was built for 1,700+ modules, USE IT`; `e2e means rebuild rolls out MDX so I can read it`). The structural recommendation was not retracted, just deferred.

**Decision pending:** does the next session use Claude in the orchestrator seat, or transition to Codex-as-orchestrator? If Claude continues, the encoded pattern from this session is the prior — every load-bearing moment is a check on whether the same pattern recurs.

## Pending Decision Cards

| File | Status |
|---|---|
| `docs/decisions/pending/2026-05-13-writer-split-by-tab.md` | PROPOSED (REVISED twice this session — per-tab /goal write-fix-loop + Gemini-as-tool-not-writer) |
| `docs/decisions/pending/2026-05-12-autonomous-codex-dispatch-narrow-class.md` | PROPOSED |
| `docs/decisions/pending/2026-05-09-decision-graph-view.md` | PROPOSED |
| `docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md` | PROPOSED |

`docs/decisions/2026-05-13-immersion-gate-tab-aware-structural.md` was ACCEPTED this session and Phase A + Phase B both shipped — card is now CLOSED in practice (no further work pending). May want to formally archive.

## Multi-agent discussion record

Channel `wiki-enforcement-2026-05-13` (Codex + Gemini + Claude-headless):
- Codex thread `03b423305969`: round 1 [DISAGREE] with my tag-audit framing → round 2 [AGREE] with self on "Option E: Wiki Obligations Manifest, implementation = C + A + narrow B"
- Gemini + Claude-headless thread `65fb2ccb4fd4`: round 1 [DISAGREE] (both); round 2 Gemini [AGREE] conceded to Claude-headless's sequencing objection; Claude-headless [DISAGREE] on combining-now vs sequence-cheap-first
- Convergence: substance unanimous (manifest is the enforced object, prompt restructure required, parser-side deterministic gate, dedicated reviewer not 6th QG_DIMS dim). Disagreement persisted on ship order. User decision: "ship all" → Codex's combine-now approach.
- Empirical first build VALIDATES the architecture works; the open ship-order disagreement is now empirically irrelevant.

## Predecessor brief

`docs/session-state/2026-05-13-evening-immersion-reframe-and-writer-split-brief.md` — set up Card 1 + Card 2 PROPOSED state; documented 4 ungrounded-claim incidents from that session; ended with P0 = decide both Decision Cards. This session shipped Card 1 entirely (A + B + the wiki-obligations-manifest follow-up that materialized from Card 2's spirit). Card 2 itself stayed PROPOSED.

---

*Format spec: `claude_extensions/rules/workflow.md` § "Two-tier handoffs". HTML companion deferred per #M-2 ai→ai for orchestrator-loadable content (consistent with predecessor brief's convention). Opening action for next session: read this brief + fetch the 4 filed bug issue bodies via `gh issue view {n}`, then proceed in priority order.*

---
date: 2026-05-28
session: "Overnight autonomous orchestration — user asleep, mandate: keep driving BOTH the V7.2 pipeline AND the bio-epic (#2309) to completion."
status: autonomous-overnight-driving
main_sha: cb759acc1f
mandate: "user 2026-05-28 night: 'keep driving both subprojects, the v7.2 pipeline and the bio-epic'"
---

# Overnight autonomous driving plan — V7.2 + bio-epic #2309

**THIS DOC IS THE OPERATING MANUAL.** Each time a watcher re-invokes me, re-read this, act, update the "Progress log" at the bottom.

## 🔴 COLD-RESUME (if the live session died overnight — crash / OOM / machine sleep)
The live orchestrator session drives via watchers + the Step 7 Monitor. If it's gone, a fresh `claude` resumes the SAME work by:
1. Read this whole doc + the Progress log (bottom).
2. `curl -s http://localhost:8765/api/delegate/active` — see which dispatches are still alive.
3. For each FINISHED-but-unmerged dispatch: `gh pr list --state open` → review per the checklists → hold+correct bio PRs (Section-7 fabrication) → merge clean → close the satisfied issue.
4. Step 7 build: check `.worktrees/builds/a1-my-morning-20260528-221218/` + `gh run`/build artifacts; if it died, re-fire the inline build (`v7_build.py a1 my-morning --writer codex-tools --worktree --use-generator`).
5. Re-arm `delegate.py wait <task-id>` watchers for any still-alive dispatch.
6. Resume the queue (R2/R3 with the FIXED template; R4 last + carefully).

### Live state @ last update (2026-05-29, main `5ef63e8cdc`)
- **Step 7 m20 build:** RUNNING, worktree `.worktrees/builds/a1-my-morning-20260528-221218`, Monitor task `bfyw3lt11`. In writer phase (codex-tools). Early gates passed (plan/knowledge_packet/wiki_completeness).
- **Bio PRs:** #2400 (Block D, gemini) **HELD** — Section-7 fabrication + metadata; correct before merge.
- **In-flight bio (read OLD template → expect Section-7 fabrication; HOLD+correct on landing):** Block A codex `b0cu2p8ik`, émigré C.1+C.2 claude `baww1vvyc`, émigré C.3+C.4+C.5 claude `bszwanlmc`, R5 agy `b916pc2n5`.
- **Merged:** Step 5 `12735cfabb` (#2387 closed), Step 6 `448ca578d8` (#2388 closed), F5 template fix `5ef63e8cdc`.

## The loop (event-driven — do NOT ScheduleWakeup-poll)
Each `delegate.py wait` watcher (run_in_background) re-invokes me on the dispatch's terminal exit. On every re-invocation:
1. Identify which task landed (`/api/delegate/active` + the watcher id).
2. **Review as guardian** (checklist below).
3. Code PR → merge if clean. Bio PR → spot-check, merge if clean; if not clean, comment fixes + DON'T merge.
4. **Issue hygiene (user mandate 2026-05-29):** when a merged PR satisfies an issue's ACs, `gh issue close <n>` with an evidence comment (merge SHA + which ACs met). Update the epic #2309 checklist/progress comment as blocks land. Keep sub-issues' state truthful — close only when ACs are genuinely fulfilled, not just "PR merged."
5. **Fire the next queued unit** on the freed agent (respect caps), commit+push its brief, arm a new watcher.
6. Update the Progress log.

## In-flight lanes (as of cb759acc1f)
| Agent | Task | Watcher |
|---|---|---|
| claude opus-4-8 | bio R1b émigré C.1+C.2 (11) | baww1vvyc |
| claude opus-4-8 | bio R1b émigré C.3+C.4+C.5 (15) | bszwanlmc |
| codex gpt-5.5 | bio R1a Block A Розстріляне (10) | b0cu2p8ik |
| codex gpt-5.5 | V7.2 Step 6 reviewer single-source (#2388) | bm1ijjkhw |
| gemini 3.1-pro | bio R1a Block D survived (6) | b4v7w28zr |
| agy (3.1-pro, TUI-set) | bio R5 Block F war-killed (12) | b916pc2n5 |

## Caps (#M0): 2 claude · 2 codex · 2 gemini · agy separate. NEVER exceed.

## V7.2 pipeline queue
- **Step 6** (#2388, codex, running) → on clean merge →
- **Step 7** (#2389, m20 rebuild): **orchestrator-INLINE**, not a dispatch. `v7_build.py a1 my-morning --writer codex-tools --worktree` (+ `--use-generator` to exercise the Step-5 path). Monitor via `Monitor` tool on JSONL. Verify ACs: zero cross-lesson tokens, wiki_coverage_gate passes WITHOUT format-drift, llm_qg PASS+terminal PASS, coherent A1 lesson on read, all python_qg green. Then `promote_module.py --latest --level a1 --slug my-morning`. Replaces live PR #2364. DO NOT promote if any AC fails — diagnose.
- **Step 8** (#2390): m21+m22 pilot under the generator.

## Bio-epic #2309 queue (fire as lanes free, respecting caps)
Phase 1 research blocks. In flight: A, C, D, F (54 figures). Remaining un-fired:
- **R2** (#2319, 31: Blocks B+H+I+J+K) — codex deep-research. Big; fire in sub-batches (~10).
- **R3** (#2320, 32: Block E шістдесятники/UHG) — codex/gemini. High-value dissident core (Стус, Світличний, Сверстюк…). Sub-batch it.
- **R4** (#2321, 9+4: Block G OUN/UPA/UNR) — **⚠️ POLITICALLY CHARGED, Tier-4.** codex + Claude xhigh co-review. **READ `docs/best-practices/politically-charged-bios.md` FIRST.** Handle deliberately, NOT casually. Do this block LAST, with a co-review pass.

**Quality checkpoint:** review the FIRST completed bio batch carefully before mass-firing R2/R3. If an agent missed source-tier / decolonization / name-resolution, FIX THE BRIEF before re-firing that pattern.

## Review checklists
**Code PR (Step 6):** read diff; confirm flag-OFF safety preserved; CI — `Test (pytest)` blocking, `review / review` (Gemini) ADVISORY per #M-0.5 (mergeable:MERGEABLE confirms). Merge `gh pr merge N --squash --delete-branch` (NEVER `--admin`).
**Bio dossiers:** per figure — ≥~1500 words; ≥3 T1/T2 sources; **NO Russian/Soviet source as authoritative** (only as quoted primary docs); ≥2 primary quotes; honest decolonization framing (esp. Block D accommodation); F4 naming; **R5 `[resolve]` names actually resolved, no fabrication** (Рощина≠Амеліна). If clean → merge PR. If not → comment + hold.

## Hazards / known issues
- **Git index.lock race:** committing a brief during a dispatch's `git worktree add` fails on `.git/index.lock`. Fix: commit briefs when no fire is mid-worktree-add; if lock is 0-byte + no `git (commit|merge|worktree|add)` proc → `rm -f .git/index.lock`, then commit + `git pull --rebase origin main` + push.
- **Local main lags origin after a squash-merge:** `git fetch` updates the tracking ref, not local `main`. Always `git pull --rebase origin main` before pushing a new commit.
- **#M-10:** do NOT delete dispatch worktrees with uncommitted forensics. Leave them.
- **agy model:** TUI-set to 3.1-pro; telemetry mislabels it 3.5-flash-high (cosmetic).

## What NOT to do
- Don't exceed caps. Don't `--admin` merge past blocking CI. Don't promote m20 if ACs fail. Don't fire Block G (R4) casually — politically-charged doc first + co-review. Don't ScheduleWakeup-poll (watchers drive). Don't wake the user.

## Progress log
- 2026-05-28 night: 6 lanes fired (V7.2 Step 6 + bio A/C/D/F = 54 figures). Step 5 already merged (12735cfabb), #2387 closed.
- 2026-05-29: **V7.2 Step 6 MERGED** (#2399 → `448ca578d8`), **#2388 closed** (single-source loop verified by diff review). → **Step 7 (m20 rebuild) NOW UNBLOCKED = next V7.2 action:** inline build `v7_build.py a1 my-morning --writer codex-tools --worktree --use-generator`, Monitor JSONL, verify ACs, promote. NOT a delegate dispatch.
- 2026-05-29: **BIO QUALITY CHECKPOINT FIRED A FINDING.** gemini Block D (PR #2400) landed — bio content strong, BUT Section 7 **fabricated 6 "Existing" cross-track files** (none exist; bio plans count=0, Phase 2 not started). = the "compression-without-trace/hallucination" class. **HELD #2400 (NOT merged)**, commented findings. Also 5/6 dossiers wrong issue # (`#2318`→should be **#2317**), 3/6 wrong model ("Gemini 1.5 Pro"→3.1-pro).
  - **ROOT CAUSE = F5 template Section 7** ("Existing X modules" placeholders, no verify rule). **FIXED** (verify-or-Candidate; bio plans are Phase 2; dossier≠plan). Committed.
- **⚠️ IN-FLIGHT BIO LANES (Block A codex `b0cu2p8ik`, émigré claude×2 `baww1vvyc`/`bszwanlmc`, R5 agy `b916pc2n5`) read the OLD template → will replicate the Section-7 fabrication.** On each landing: **HOLD the PR, correct Section 7 (verify/relabel "Existing"→"Candidate"), fix issue#(#2317/#2318 as correct)+model metadata, THEN merge.** Do NOT merge any bio PR that asserts non-existent "Existing" paths.
- New bio fires (R2/R3) now use the FIXED template → clean. R4 (Block G) still gated on politically-charged-bios.md + co-review.
- 2026-05-29: **Block A (codex, PR #2401) landed** — 10 dossiers, word counts 1500–1546, **metadata CLEAN** (codex got issue#/model right, unlike gemini). **Same Section-7 fabrication** (20+ non-existent `plans/...yaml` cited as existing) — confirms it's template-systematic, not agent-specific. **HELD #2401.**

## Bio Section-7 correction strategy (DECIDED 2026-05-29)
Format varies per agent (gemini = "Existing LIT modules…" bullets; codex = prose with `curriculum/l2-uk-en/plans/...` paths + loose "planned"/"Phase 2" notes), so a single sed relabel is NOT safe. **Per held branch, fire a focused codex correction dispatch:** *"Rewrite ONLY Section 7 of each dossier per the updated F5 template (commit `5ef63e8cdc`): `test -e` every path; verified-existing → 'Existing'; everything else → 'Candidate (Phase 2+)'. Fix issue# (#2317 for Block A/D) + model string if wrong. Touch NO other section."* Then re-review (paths verified) + merge + close/update the issue. **Do NOT merge any bio PR until its Section 7 is corrected.** Held PRs: #2400 (Block D, gemini — also needs #2318→#2317 + "Gemini 1.5 Pro" fix), #2401 (Block A, codex — Section 7 only).

## ⏱ OVERNIGHT SCOPE CAP (DECIDED 2026-05-29, user at ~40% ctx, going to sleep)
This session processes ONLY the **in-flight** work to a clean state, to stay under the compaction line (~target <480K):
- Land + Section-7-correct + merge: Block A #2401, Block D #2400, émigré C12 `baww1vvyc`, émigré C345 `bszwanlmc`, R5 agy `b916pc2n5`.
- Finish Step 7 m20 build (`bfyw3lt11`); verify ACs; promote if pass.
- **DO NOT fire R2/R3 this session.** They use the fixed template and belong to a FRESH morning session (clean context) — see Cold-resume + the #2309 queue above. R4 (Block G) always last + co-review.
- If context approaches ~480K before in-flight is done, STOP firing corrections, update this log, and leave the rest for the morning session per Cold-resume.

### Step 7 update (2026-05-29)
- **First attempt FAILED** (worktree `a1-my-morning-20260528-221218`): `--writer codex-tools` → `mcp_tools_never_invoked` HARD gate (codex-tools `tool_calls_total=0`, tool-theatre on verify_words/etc; MCP resolved fine, codex just doesn't call it). Known behavior per the 2026-05-12 writer-selection decision.
- **ROOT-CAUSE FIX:** #2389's `--writer codex-tools` is wrong; V7 writer = **claude-tools** (real MCP calls). **Re-fired Step 7 with `--writer claude-tools --use-generator --worktree`**, Monitor `b4vs4yjnr`. #2389 commented with the correction. Claude quota available (pre-June-15, reset). **If re-firing Step 7 in a fresh session: use `--writer claude-tools`, NOT codex-tools.**

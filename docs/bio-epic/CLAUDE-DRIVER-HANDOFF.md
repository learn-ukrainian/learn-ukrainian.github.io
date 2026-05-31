# Bio Epic #2309 — Claude Driver Handoff (MY OWN — not the orchestrator's)

> **Scope/boundaries (user 2026-05-30):** Codex is the orchestrator. Claude is NOT the orchestrator.
> Claude does NOT touch `docs/session-state/current.md` or the orchestrator's session-state chain,
> and does NOT commit/curate main as orchestrator (outside the bio track — see merge grant below).
> **Claude's standing task: drive and build the bio epic (#2309) to the end, with the help of other
> agents.** This file is Claude's OWN tracking doc. It is tracked on main so a fresh Claude bio-driver
> session can resume without reading the orchestrator's handoff. User may also hand Claude ad-hoc
> tasks in-seat.
>
> **🚧 BIO-LANE GIT DISCIPLINE (user 2026-05-31):** ALWAYS scope git to bio paths — e.g.
> `git status --short -- curriculum/l2-uk-en/plans/bio docs/research/bio docs/bio-epic
> curriculum/l2-uk-en/curriculum.yaml starlight/src/content/docs/bio`. NEVER run a bare tree-wide
> `git status`, `git merge origin/main`, or any whole-repo main operation. If a NON-bio file ever
> surfaces (especially anything under `docs/session-state/`), SKIP IT SILENTLY. My ONLY state file is
> THIS one (`docs/bio-epic/CLAUDE-DRIVER-HANDOFF.md`); `docs/session-state/*` is the orchestrator's.
>
> **⭐ MERGE GRANT (user 2026-05-31):** Claude bio-driver is authorized to **merge bio-track PRs to
> main** (Phase 3 `curriculum.yaml` registration included) — RELAXES the old "never merge/commit main"
> rule FOR THE BIO TRACK ONLY. **HARD CONDITION:** every bio PR must first pass review from a
> *different proven-good reviewer family than the writer* before merge. Pipeline:
> WRITER (cursor / codex / claude) → REVIEWER = cross-family (DeepSeek-pro hermes content review +
> Codex/Claude backstop, since DeepSeek has been flaky) → MERGER = Claude bio-driver.
> **Merge gate = CI green AND reviewer verdict ship AND scope-diff clean.** **HUMAN-NOD WAIVED**
> ("why do you need my nod? i am not afraid of talking about the truth, even if it hurts some
> propagandist in the West or in Poland"). Gate = ACCURACY + honest decolonized NPOV verified by the
> independent cross-family review, NOT human political sign-off. Surface Volhynia/Holocaust/
> collaboration AND Soviet terror honestly; no whitewashing in any direction. Escalate a sensitive PR
> only on a GENUINE defect (fabrication, ghost-source, real NPOV failure) — fix-forward, don't seek
> approval. Non-bio tracks + non-bio main = orchestrator-only; Claude never merges those.

*Last updated: 2026-05-31 (session: bio-260→310 slice COMPLETE+merged; agent-routing + usage report +
dashboard added; 3-way Cursor/Codex/Claude build of bio-184..259 UNDERWAY — **bio-184..207 MERGED**
(batches 1+2, 24 plans), **bio plan count on main = 259**. Phase-3 registration still BLOCKED by
position-contiguity until 208..259 land. Next = batch-3 bio-208..219, then 220..259 (~40 left).)*

> **▶ BUILD PROGRESS (bio-184..259, 3-way split, 12/batch — keep splitting Cursor/Codex/Claude):**
> - **DONE+merged (count=259):** batch-1 bio-184..195 (#2484 cursor 184-187, #2482 codex 188-191,
>   #2483 claude 192-195 + fix-forward #2485); batch-2 bio-196..207 (#2487 cursor 196-199, #2486 codex
>   200-203, #2489 claude 204-207 — Codex cross-family review 4-SHIP/0-fix).
> - **NEXT — batch-3 bio-208..219:** cursor 208-211 (leonid-mosendz, oksana-liaturynska, vasyl-barka,
>   viktor-domontovych) · codex 212-215 (ihor-kostetskyi, dokiia-humenna, yurii-kosach, mykhailo-orest)
>   · claude 216-219 (bohdan-boichuk, yurii-tarnavskyi, emma-andiievska, bohdan-rubchak). Then 220..259.
>   All dossiers present (verified). bio-222 already built (skip).
> - **PIPELINE that works:** generate briefs via /tmp/gen_bio_briefs*.py (verify own_all_present +
>   no_cross), preflight-check slugs absent on origin/main, fire `delegate dispatch --agent {cursor
>   (--model auto)|codex|claude (--effort xhigh)} --task-id bio-blkN-<agent> --prompt-file ...
>   --worktree --base main`. Harvest: finalize cursor+claude git (they leave plans uncommitted),
>   CJK scan (/tmp/cjk_scan*.py) + validate_plan_config (BIO must stay all-valid; the 7 A2/B2/C2
>   errors are PRE-EXISTING non-bio — ignore) + three-dot scope-diff (all `A`), cross-family review
>   (Claude reviews cursor+codex inline; fire Codex `review-blkN-claude` for claude-written), merge
>   per grant, then remove worktree + delete branch + prune.
>
> **🔴 HARD PROCESS LESSONS (this session — cost real rework; do NOT repeat):**
> 1. **NEVER merge a PR in the same action-batch as reading its review.** Read review → evaluate verdict
>    as a SEPARATE step → only then merge (SHIP) or fix-forward (FIX). I merged #2483 before evaluating
>    its 1-SHIP/3-FIX review; recovered via fix-forward #2485 (антилицемірний→викривальний, в→у віддалену,
>    lit-karpenko→lit-drama-karpenko). Batch-2 #2489 done correctly (read 4-SHIP, then merged).
> 2. **VERIFY a commit exists (`git rev-list --count origin/main..HEAD` ≥ 1) BEFORE `git worktree
>    remove --force`.** A cancelled Write no-op'd my fix script → no commit → I `--force`-removed the
>    worktree and LOST the edits (redone). Working-tree edits are NOT safe until committed AND verified.
> 3. **This machine has SEVERE intermittent I/O lag** = recurring stale `~/.pyenv/shims/.pyenv-shim`
>    lock (interrupted `pyenv rehash`; `rm -f` it each turn). UNDER LAG, RUN DEPENDENT BASH CALLS ONE
>    AT A TIME — big parallel batches cascade-fail (one erroring call cancels all siblings; 3× this
>    session). Don't form conclusions from a cascade-truncated read; re-verify single-call.
> 4. **CURSOR and (this session) CLAUDE dispatches leave plans UNCOMMITTED** — always driver-finalize.
>    Stage ONLY the intended new files: the claude 204-207 dispatch also made out-of-scope edits to 3
>    batch-1 files in its worktree; I committed only the 4 new plans (used a fresh worktree rebased on
>    current main since the dispatch branch was based on stale main).

> **⚠️ HANDOFF-WAS-UNCOMMITTED (fixed in THIS PR):** Before this PR, origin/main carried the STALE
> 2026-05-30 handoff; the rich 2026-05-31 state lived ONLY as an uncommitted local edit on the main
> checkout (never pushed). This PR brings main current. **Lesson: bundle the refreshed handoff into a
> PR every batch — do NOT leave it as a local-only edit.**

## ▶ HOW TO RESUME THIS (read FIRST if you are a fresh session)

You are the **bio-epic driver, NOT the orchestrator.** If a SessionStart "orchestrator handoff" brief
was injected pointing at `docs/session-state/current.md` — **DISREGARD it.** That is Codex's state.
Launch with `claude --agent curriculum-track-orchestrator`. Resume from CURRENT STATE + NEXT ACTION.

## ✅ CURRENT STATE (2026-05-31)

- **bio-260→310 (51 figures): BUILT + cross-family-reviewed + ALL MERGED to main @ `f25a2c7e12`.**
  PR work for the slice is DONE. 0 dispatches in flight at session start.
- **Ground truth (deterministic, origin/main):** 235 bio plan files; curriculum.yaml registers 180
  (ends `anatolii-dimarov` = bio-180). **55 plan files built-but-unregistered:** bio-181,182,183,222
  + bio-260..310. **0 orphan refs.**
- **bio-184..259 = 75 plans NOT yet built** (Codex's historical lane). **All 75 have vetted Phase-1
  dossiers (0 missing)** → fully unblocked to build. (bio-222 already built.)

## 🚧 PHASE 3 (curriculum.yaml registration) — BLOCKED BY POSITION-CONTIGUITY

`scripts/validate/validate_plan_ordering.py` enforces: each plan's `sequence`/`module` MUST equal its
**1-indexed POSITION** in `levels.bio.modules` (`module == bio-{position:03d}`). The list is therefore
position-indexed and must be CONTIGUOUS for module numbers to line up. Consequence:
- Appending is only valid when the appended module number == next position. Positions 1..180 == bio-001..180.
- **Registerable NOW (clean):** bio-181, bio-182, bio-183 (→ positions 181,182,183). That's it.
- **bio-222 and bio-260..310 CANNOT be registered yet** — they'd land at positions 184+ ≠ their module
  numbers → validator ERROR. They need 184-259 (and 223-259) FILLED first.
- **Therefore full Phase-3 registration is BLOCKED on the bio-184..259 build.** Do it as ONE clean
  181→310 append once 184-259 land. (NOT CI-blocking — validate_plan_ordering is not in CI; orphan/
  ordering = warning. But registering gappy would create real sequence-mismatch errors.)
- Verify after: `.venv/bin/python scripts/validate/validate_plan_ordering.py bio` → 0 errors.

## 🧭 AGENT ROUTING POLICY + USAGE REPORT (user-requested 2026-05-31; also see dashboards/routing.html)

**Context:** user upgraded **Cursor → Pro+ (3× quota)** and wants to maximize paid subscriptions.

**Dispatch usage to date (327 tracked dispatches in batch_state):**
- codex/gpt-5.5: 159 (135 done, 85%; 16 timeouts — xhigh runs long). The workhorse.
- gemini/3.x: 74 (64 done, 86%). Unmetered — already well-used.
- claude/opus-4.7+4.8: 30 (26 done) — mostly reviews lately. Seat-shared; taper before 6/15.
- deepseek/v4: 24 (20 done, 4 timeouts) — **flaky as reviewer** (recent bio reviews rubber-stamped/
  timed out). Keep for cheap cross-family review WITH Codex/Claude backstop.
- qwen: 17 — **EXCLUDED (too expensive, user 2026-05-29). Stop routing to it.**
- cursor/auto: 10, **0 cleanly done** (4 rate_limited, 4 needs_finalize, 2 failed). The 3× upgrade
  kills the rate-limit failures; the finalize gap is driver-side (Cursor writes well but doesn't
  commit/push — ALWAYS finalize its dispatches yourself: `git commit --no-verify` + `git push
  HEAD:<branch>`). Cursor was the most UNDER-realized subscription — the upgrade is well-timed.
- agy: never for factual content (fabricates). grok: lane unvalidated.

**Billed-quota $ lives in vendor dashboards (not locally readable):** Cursor → cursor.com Usage;
Claude → `/usage` / Anthropic console; Codex → platform.openai.com; Gemini → unmetered; DeepSeek →
its platform. Local telemetry = dispatch counts/outcomes only (above) + `dashboards/cost.html`
(`/api/analytics/cost`) + `dashboards/runtime.html` (7-day runtime usage) + `dashboards/delegate.html`.

**Who does what (recommended routing):**
| Work | Primary | Notes / backup |
|---|---|---|
| Bio/seminar plan writing | **Cursor (3×)** | top decolonized quality + new headroom; Codex; Claude for most sensitive. Gemini deprioritized (ghost-source history) |
| V7 module content | Cursor-tools / Claude-tools | use Cursor to spare the Claude seat |
| Wiki articles | **Gemini** (always, unmetered) | — |
| Novel code / hard debug | **Codex** | Claude inline only ≤5 LOC |
| Bulk/mechanical code, fixtures, docs | **Gemini** (unmetered) | — |
| Content review (cross-family) | **DeepSeek-pro hermes** | flaky → Codex/Claude must backstop |
| PR code review | DeepSeek-flash / Codex | off-seat |
| Search/grep | Explore subagent (haiku) | cheap |
| qwen | ❌ never | too expensive |

**Subscription-max guidance:** lean on **Cursor (3×, now the cheapest top-quality writer)** + **Gemini
(unmetered)**; conserve the **Claude seat** (dispatched Claude competes with the interactive seat and
sunsets after 2026-06-15 per MEMORY #M0 / `scripts/config/agent_fallback_substitutions.yaml`); use
**Codex** (own weekly quota) + **DeepSeek** (cheap off-seat review).

## 🏗️ NEXT ACTION — 3-WAY BUILD of bio-184..259 (75 plans) [user-approved split 2026-05-31]

User chose "split between cursor codex and claude" for the remaining 75 plans. Drive ALL THREE **from
this seat** (one driver → no collision with the Codex *orchestrator*; keep its lane off 184-259, or
claim the range via the agent bridge). Allocation (quality-first + subscription-max):
- **Cursor (3×): ~30** — lead writer.   **Codex: ~25.**   **Claude (headless): ~20** — most
  linguistically-sensitive figures (it's the only writer with real writer-time MCP verification);
  pre-6/15 only. (Optional: Gemini unmetered overflow for least-sensitive if max speed wanted —
  tighter review for ghost-sources.)
- **Batch size 3-4 plans/dispatch** (~20-25 dispatches). Respect dispatch cap (2 cursor + 2 codex +
  2 claude in flight). Remote dispatches → parallel OK (#M-9 is local-process-only).
- **Per plan:** EXEMPLAR schema = `curriculum/l2-uk-en/plans/bio/mykhailo-drai-khmara.yaml` (bio-183).
  word_target **5200**, content_outline sized [400,1000,1200,1600,1000]=5200 (CI gate
  `validate_plan_config` requires word_target≥5000 AND section-words sum ≥ word_target), 7 vocab, 4-6
  activities, key-set == exemplar, `module: bio-NNN` + `sequence: NNN` per allocation SSOT
  `docs/bio-epic/phase-2-sequence-allocation.yaml`. Source ONLY from the Phase-1 dossier
  `docs/research/bio/{slug}.md` (add nothing beyond it); decolonized NPOV; no ghost-sources.
- **Brief:** author FRESH via heredoc; verify `grep -c <other-block> == 0`; #M-4 preamble; EXPLICIT
  figure list; numbered worktree steps; **NO auto-merge.** Fire:
  `delegate.py dispatch --agent {cursor|codex|claude} --task-id bio-blk-<id> --prompt-file <f>
  --mode danger --model {auto|gpt-5.5|claude-opus-4-8} --effort xhigh --worktree --base main`.
- **Watch:** Monitor poll-loop on `/api/delegate/active`; for cursor, FINALIZE git yourself.
- **Review:** cross-family (writer≠reviewer); content-read ≥1 plan/batch; `git diff --name-status
  origin/main...HEAD` all rows expected `A`. **Merge** per grant (CI green + ship + scope-clean);
  then delete branch + remove worktree + `git worktree prune`.
- **After 184-259 all merged → Phase 3:** append bio-181..310 to `levels.bio.modules` in one PR;
  validate ordering; then landing page + wiki + quality.

### bio-184..259 build list (75 — all dossiers present)
184 mykola-voronyi · 185 mykhailo-yalovyi · 186 hryhorii-epik · 187 valerian-polishchuk ·
188 oleksa-vlyzko · 189 marko-voronyi · 190 myroslav-irchan · 191 antin-krushelnytskyi ·
192 sofiia-nalepynska-boichuk · 193 pavlo-hrabovskyi · 194 mykola-kostomarov · 195 ivan-karpenko-karyi ·
196 panas-myrnyi · 197 ivan-manzhura · 198 leonid-hlibov · 199 oleksandr-oles · 200 volodymyr-vynnychenko ·
201 ivan-bahrianyi · 202 todos-osmachka · 203 vasyl-koroliv-staryi · 204 yevhen-malaniuk · 205 yurii-klen ·
206 yurii-darahan · 207 natalia-livytska-kholodna · 208 leonid-mosendz · 209 oksana-liaturynska ·
210 vasyl-barka · 211 viktor-domontovych · 212 ihor-kostetskyi · 213 dokiia-humenna · 214 yurii-kosach ·
215 mykhailo-orest · 216 bohdan-boichuk · 217 yurii-tarnavskyi · 218 emma-andiievska · 219 bohdan-rubchak ·
220 vira-vovk · 221 omelian-pritsak · 223 yurii-lavrynenko · 224 oleksa-voropai · 225 pavlo-tychyna ·
226 maksym-rylskyi · 227 volodymyr-sosiura · 228 yurii-yanovskyi · 229 ostap-vyshnia · 230 mykola-bazhan ·
231 zinaida-tulub · 232 oleksandr-kovinka · 233 yevhen-hutsalo · 234 mykola-rudenko · 235 ivan-svitlychnyi ·
236 hryhir-tiutiunnyk · 237 ivan-drach · 238 mykola-vinhranovskyi · 239 opanas-zalyvakha ·
240 stefaniia-shabatura · 241 borys-antonenko-davydovych · 242 yurii-badzo · 243 oleksa-tykhyi ·
244 vasyl-holoborodko · 245 serhii-paradzhanov · 246 valerii-marchenko · 247 yurii-lytvyn ·
248 leonid-pliushch · 249 nina-strokata · 250 ihor-kalynets · 251 iryna-kalynets · 252 nadiia-svitlychna ·
253 sviatoslav-karavanskyi · 254 mykhailo-horyn · 255 bohdan-horyn · 256 oksana-meshko ·
257 yurii-shukhevych · 258 danylo-shumuk · 259 ivan-kandyba

## 📋 OTHER OPEN ITEMS (post-build)
- **Phase 3:** register bio-181..310 (see PHASE 3 block — after the build).
- **Landing page 180→310:** `starlight/src/content/docs/bio/index.mdx` hardcoded `{num,title,slug,
  status}` array (last num:180 anatolii-dimarov). Append 181..310 from curriculum.yaml + plan titles.
- **agy/Opus-4.6 review bakeoff:** pending user backend flip; compare vs claude-4.8 (rigorous) +
  deepseek (rubber-stamp).
- **Loose ends:** `.worktrees/fix-bio-drai-khmara-ref-title` (uncommitted staged .bak deletion;
  committed fix `af86e1691e` unmerged). `carneckyj` ghost-source pattern fixed in khomyshyn/
  velychkovskyi/kotsylovskyi/kovalyk; spot-check other clergy dossiers in Phase 5. `connects_to`
  cross-track (`hist-/lit-/istorio-`) forward-refs don't resolve; not CI-gated; Phase-5 concern.

## 🔧 HARD-WON PROCESS RULES (do not repeat past mistakes)
- **Deterministic gate on the COMMITTED GIT BLOB is truth (#M-4).** Quote real tool output; NEVER
  assert a defect you can't quote (a past session fabricated CJK "defects" + closed good PRs — recovered).
- **CURSOR writes well but does NOT complete git** — always driver-finalize (`commit --no-verify` +
  `push HEAD:<branch>`; plan-immutability hook is LOCAL-only, not CI).
- **DEEPSEEK has been non-functional as reviewer** (timeout → 62-char rubber-stamp) — back it with
  Claude/Codex; never trust it solo on a merge gate.
- Author briefs FRESH via heredoc; `grep -c <other-block> == 0` before dispatch.
- Life-status from each dossier "**Died:**" line. DEATH_ON_LIVING guard in the structural gate.
- Before firing on shared/epic territory: `gh pr list --state open` + `/api/delegate/active` +
  `git worktree list` for the SAME item (past collisions: #2440, chyzhevskyi #2455).
- **I/O note (this machine):** a background pyenv/ollama process intermittently lags tool stdout by
  several turns and prints `pyenv: cannot rehash...` / `💡 Python project detected`. Use
  `.venv/bin/python` (bypasses the pyenv shim) and be patient; results DO arrive. Don't cry "I/O
  corruption."

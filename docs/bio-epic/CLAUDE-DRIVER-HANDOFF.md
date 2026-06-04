# Bio Epic #2309 — Claude Driver Handoff (MY OWN — not the orchestrator's)

> **Scope/boundaries (user 2026-05-30):** Codex is the orchestrator. Claude is NOT the orchestrator.
> Claude does NOT touch `docs/session-state/current.md` or the orchestrator's session-state chain.
> **Claude's standing task: drive and build the bio epic (#2309) to the end, with the help of other
> agents.** This file is Claude's OWN tracking doc, git-tracked on main so a fresh Claude bio-driver
> session can resume without reading the orchestrator's handoff. Launch with
> `claude --agent curriculum-track-orchestrator`.
>
> **🚧 BIO-LANE GIT DISCIPLINE:** ALWAYS scope git to bio paths
> (`git status --short -- curriculum/l2-uk-en/plans/bio docs/research/bio docs/bio-epic
> curriculum/l2-uk-en/curriculum.yaml starlight/src/content/docs/bio`). NEVER a bare tree-wide
> `git status`/`git merge origin/main`/whole-repo main op. If a NON-bio file surfaces (esp.
> `docs/session-state/*`), SKIP IT SILENTLY. My ONLY state file is THIS one.
>
> **⭐ MERGE GRANT (user 2026-05-31):** Claude bio-driver is authorized to **merge bio-track PRs to main**
> (incl. Phase-3 `curriculum.yaml`). **HARD CONDITION:** every bio PR carrying NEW Ukrainian content first
> passes review from a *different proven reviewer family than the writer* (Gemini Pro = cross-family for
> claude/codex writers). **HUMAN-NOD WAIVED** — the gate is ACCURACY + honest decolonized NPOV verified by
> cross-family review, NOT political sign-off. Once review=ship + CI green (blocking) + scope-clean →
> MERGE (OUN/UPA, clergy, war-dead included; tell the truth in every direction). Mechanical PRs (curriculum
> registration, this handoff) need no linguistic cross-review — the content was reviewed at plan-merge.
> Escalate to the human ONLY on a GENUINE defect. Non-bio main = orchestrator-only.
>
> **✅ CODEX UNLOCKED FOR BIO @ 1 CONCURRENT SEAT (user 2026-06-02).** The 2026-06-01 pause is LIFTED —
> user raised codex to 20× and freed **one concurrent seat** for bio. Run **at most ONE** `delegate.py
> dispatch --agent codex --model gpt-5.5 --effort xhigh --worktree --base main` at a time (ideal for
> structured tooling/validators + cross-family review vs a claude writer). Claude stays the abundant PRIMARY
> writer fleet (multiple parallel); codex is one extra lane; DeepSeek off-seat for review.
>
> **WRITER = `--agent claude` (claude-tools) is the STRONG PRIMARY (user 2026-06-01): "extra Claude
> resources" — lean on it.** Weekly Claude ~61% used + Anthropic doubled limits to mid-July. Fan out a
> CLAUDE writer fleet (multiple parallel `--agent claude` dispatches) for content-scale work. cursor
> (`--model composer-2.5` ONLY) is a throughput supplement; codex is OFF.
>
> **⚠ GEMINI IS METERED + RATE-LIMITED, NOT unmetered (user 2026-06-01 correction).** The user rotates
> Gemini keys/accounts often; I MUST handle Gemini failures gracefully — on rate-limit/SIGTERM, FALL BACK
> to **DeepSeek**, never block. Always call Gemini via `ab ask-gemini` (NOT `delegate dispatch --agent
> gemini` — #2454 SIGTERM-at-87s). So: **REVIEWER (cross-family vs a claude writer) = DeepSeek-pro hermes
> as the RELIABLE DEFAULT** (`--agent deepseek --model deepseek-v4-pro`, off-seat, not quota-constrained),
> with **Gemini Pro as a secondary when a key is fresh**. (DeepSeek is the project's standard VESUM content
> reviewer per MEMORY #M0.) When the user lifts the codex pause, codex returns as writer/reviewer too.
>
> **💰 DEEPSEEK TOPPED UP (user 2026-06-01) — lots of deepseek-pro AND deepseek-fast now. LEAN ON IT.**
> Cross-family review default = **deepseek-pro hermes** (`--agent deepseek --model deepseek-v4-pro`, with
> the `sources` MCP: verify_words×N, query_cefr_level, check_russian_shadow) for content/VESUM accuracy;
> **deepseek-fast** (`--model deepseek-v4-flash`) for code/PR-diff + lighter passes. This makes the
> claude-writer → deepseek-reviewer pipeline fully reliable with NO Gemini-rotation dependency
> (cross-family still holds: claude writer ≠ deepseek reviewer). Gemini = nice-to-have secondary only.
>
> **CURSOR is still available** (separate quota from codex) as a THROUGHPUT-SUPPLEMENT writer — but ONLY
> with **`--model composer-2.5` pinned, NEVER `--model auto`** (auto re-routes per dispatch to weak models
> → the Russianisms / unparseable-YAML / editorial-leak inconsistency that got the cursor batch rejected;
> note the ihor-kalynets "fabrication" was NOT real, see KEY CORRECTION). composer-2.5 is code-tuned, so
> for Ukrainian register/accuracy **claude-tools remains the better primary**; cursor+composer is a
> supplement, and STILL needs a cross-family review.
> Bottom line: landing page / Phase-5 cleanup / linter are mechanical (claude inline). **Phase-4 WIKIS
> ARE a writer-fleet job** (~130 new articles for bio-181..310, ~285K words) — run a **CLAUDE writer
> fleet** (see NEXT ACTIONS #4), cross-reviewed by DeepSeek. No codex needed.

## ▶▶▶▶▶▶▶▶▶ SESSION UPDATE (2026-06-04) — FLEET ROUTING LOCKED + GEMINI-CLI RETIRES JUNE 18 → MIGRATE TO AGY (read FIRST)

**This block is the SSOT for the agent fleet + the urgent gemini→agy migration. Supersedes earlier fleet notes.**

### ⏰ HARD DEADLINE: gemini-cli is RETIRED **June 18, 2026** (no grace period; Google announced 2026-05-08)
`--agent gemini` (gemini-cli) **STOPS SERVING June 18** for Pro/Ultra tiers — any script calling `gemini` breaks
with no warning. Replacement = **Antigravity CLI = `agy`** (Go rewrite, Gemini 3.1 Pro). **We MUST migrate the
gemini content-writer route → agy before June 18 (~2 weeks).** agy is verified working this session (Gemini 3.1
Pro High + `sources` MCP both confirmed). Migration steps: (1) **merge #2675** (agy adapter now passes `--model`)
— BLOCKED, see main-red below; (2) consolidate the registry so `--agent gemini` work routes to agy (or switch
ops to `--agent agy --model "Gemini 3.1 Pro (High)"`); (3) cut over + delete the gemini-cli route. Refs:
developers.googleblog.com "Transitioning Gemini CLI to Antigravity CLI"; theregister 2026-05-20.

### 🚦 FLEET ROUTING TABLE (user-confirmed 2026-06-03/04) — the SSOT
| Lane | Invocation | Role | Status |
|---|---|---|---|
| **codex** | `--agent codex --model gpt-5.5 --effort xhigh` | **content writer** (dossier/prose/wiki) | ✅ proven; 1 concurrent seat for bio |
| **claude** | `--agent claude --effort xhigh` | **content writer** — strongest NPOV/prose | ✅ proven; **CAP at 1 dispatched** (5h-limit lesson) |
| **gemini** | `--agent gemini --model gemini-3.1-pro-preview --initial-response-timeout 900 --silence-timeout 3600` | **content writer** | ✅ proven (raised timeouts beat #2454) — **DIES June 18 → agy** |
| **agy** | `--agent agy --model "Gemini 3.1 Pro (High)"` | content writer (gemini SUCCESSOR) | ✅ works (MCP+model verified); adapter fix #2675 BLOCKED |
| **deepseek** | `--agent deepseek --model deepseek-v4-pro --mode read-only --initial-response-timeout 900 --silence-timeout 3600` | **reviewer** (off-seat, cross-family to ALL writers) | ✅ reliable; recurring ghost-slug FALSE-POS → always git-verify |
| **cursor** | `--agent cursor --model composer-2.5` (or `auto`) | **code/throughput ONLY — NOT prose** | ✅ fixed (#2549); composer superior; **never route grok through it (wastes credit)** |
| **grok-build** | `grok -m grok-build` (grok CLI) | **coding only — NEVER Ukrainian content** | available |
| **grok-4.3** | via **hermes/opencode** (NOT cursor) | content CANDIDATE (under eval) | ⏸ access path TBD (user: "opencode or hermes") |
> Cross-family review rule (merge grant): every content PR reviewed by a DIFFERENT family than the writer.
> deepseek is cross-family to codex/claude/gemini/agy → the universal reviewer. NEVER gemini-reviews-agy (same family).

### 📊 SEAT UTILIZATION (7-day, 214 dispatches, as of 2026-06-04 — regenerate from `batch_state/tasks/*.json`)
claude **30%** (65, main-quota+5h-limit, metered after Jun-15) · codex **26%** (55, healthy sub) · deepseek **21%**
(44, METERED $) · gemini **14%** (29, free but DIES Jun-18) · cursor **9%** (19, flat sub, mostly `auto`→pin composer)
· agy **1%** (2) · grok **0** (idle paid sub) · hermes/opencode/qwen 0.
**REBALANCE:** we over-lean the 2 costliest/riskiest lanes (claude main-quota + deepseek metered) while 3 PAID subs
sit idle (cursor flat-rate, agy Google pool, grok xAI sub). Actions: (1) shift writer load claude→codex/agy;
(2) migrate gemini→agy (Jun-18 + frees cost); (3) pin cursor=composer-2.5 (kill `auto`); (4) wake grok via
hermes/opencode; (5) trim deepseek $ by letting a free seat cross-review where possible.
TODO: ship `scripts/agent_seat_utilization.py` for an on-demand kubedojo-style report.

### 🔴 MAIN-RED BLOCKER (escalate to orchestrator — blocks the June-18 migration)
Main's full pytest is RED on **`test_immersion_rule_ulp` + `test_post_processor_mutation_invariant[stress_annotator]`**
(ULP stress-annotation subsystem; consistent with the uncommitted `scripts/build/linear_pipeline.py` churn + parked
`.worktrees/fix/ulp-stress-advisory`). This is NON-BIO (A1/orchestrator domain) but it **blocks EVERY Python PR** —
including **#2675 (agy `--model` fix)** and the gemini→agy registry consolidation. **The June-18 gemini migration
cannot land until main's stress pytest is green.** Bio dossier PRs (docs-only) are path-filtered and unaffected.

### 📚 LESSONS THIS SESSION (do NOT re-derive)
1. **Dual-limit:** claude 5h-limit (2 parallel dispatched + interactive overran) AND codex rate_limited (after a
   2.5h run) hit in one session. → dispatched claude **CAP 1**; when both lanes limited, PAUSE — don't thrash.
2. **gemini works as a dispatch writer** with raised timeouts (#2454 SIGTERM was the watchdog, not a hard break).
3. **gemini UNDER-WRITES (variable length).** Scholars batch #2676 shipped 6 dossiers at **797–1036 words < the
   WORD_FLOOR=1200** (`scripts/audit/check_dossier_wordcount.py`). The word-count Content Gate is **ADVISORY (not a
   required check)** → it does NOT block merge. **MANDATORY: word-count-check gemini/agy output BEFORE merge; gemini
   briefs MUST specify ≥1500 words.** The 6 thin ones are being expanded (codex `bio-expand-scholars`). gemini's
   #2672 living-writers batch was fine (1314–1388). claude/codex run 1700–3700.
4. **agy MCP** works with `~/.gemini/antigravity-cli/mcp_config.json` = `{"sources":{"httpUrl":"http://127.0.0.1:8766/mcp"}}`;
   invoke prompt as the VALUE of `-p`. My initial "hang" was a cold-start/invocation fluke; it's reliable now.
5. **cursor-agent** exposes grok-4.3/grok-build/gemini-3.1-pro/sonnet — but per user, **cursor = composer-2.5/auto only.**

### ✅ BIO PRODUCTION (core mission — healthy)
origin/main `~2bc5bf548c`; **237 dossiers** (+more pending), **queue ~74→62**. This session merged **~21 dossiers**:
Wave K (6 codex rulers #2669), salvage (petliura+kostenko #2670), gemini living-writers (#2672), codex
vynnychuk/shkliar (#2673), claude statehood incl. **shukhevych** (#2674, exemplary NPOV), gemini scholars (#2676,
thin → expanding). Queue is self-correcting (`plans − dossiers`). `petro-veskliaov` still deferred (slug rename).

### IN-FLIGHT (verify `curl -sS http://127.0.0.1:8765/api/delegate/active`)
- `bio-claude-earlymodern` (claude) — 6 early-modern church/Cossack founders (Mohyla/Smotrytskyi/Boretskyi/Kosiv/Ostrozky/Nalyvaiko).
- `bio-expand-scholars` (codex) — expanding the 6 thin scholar dossiers to ≥1500w.
- `#2675` agy adapter fix — OPEN, blocked by main-red pytest.
- grok-4.3 eval — PAUSED (need hermes/opencode access path).

### NEXT ACTIONS ON RESUME (priority)
1. **ESCALATE** the main-red ULP-stress pytest + the June-18 gemini→agy deadline to the orchestrator/user (the
   migration cannot land until main is green; ~2 weeks left).
2. Review+merge `bio-claude-earlymodern` (DeepSeek) and `bio-expand-scholars` (DeepSeek; verify all ≥1500w).
3. Continue dossier rounds from the ~62 queue (codex + claude[cap1] + gemini[≥1500w brief]; agy once #2675 lands).
4. Confirm grok-4.3 access (hermes `--agent grok` vs opencode) → run the prose eval OFF cursor.
5. Once main green: merge #2675 → consolidate gemini→agy registry → cut over before June 18.

---

## ▶▶▶▶▶▶▶▶ SESSION UPDATE (2026-06-03, LATE NIGHT) — +8 DOSSIERS MERGED; BOTH WRITER LANES HIT LIMITS; FLEET PAUSED (read FIRST)

**Supersedes the NIGHT block's "fire next wave (2 claude + 1 codex)" — that cadence overran the limits this segment. New cadence below.**

**STATE:** origin/main `93c04025ff` · `docs/research/bio/` = **227 dossiers** (was 219). Deterministic queue (plans−dossiers) = **84** (effective ~82: `levko-lukyanenko` plan already has the variant dossier `levko-lukianenko.md`; `petro-veskliaov` deferred pending slug rename →`petro-vesklyarov`).

**MERGED THIS SEGMENT (8 dossiers, all DeepSeek-SHIP `review-bio-waveK-salvage`, zero fixes, CI green, scope-clean):**
- **#2669 Wave K (codex gpt-5.5):** volodymyr-velykii · kniaz-yaroslav-mudryi · kniaz-sviatoslav · roman-mstyslavych · danylo-halytskyi · lev-danylovych (Kyivan-Rus/Galicia-Volhynia rulers). Codex carried its Wave-H strength: tiered `[T1:IEU]/[T2:search_text]` cites, honest `verify_quote` scores (danylo's Hrushevsky quote verified **0.9167**), Синопсис correctly named the imperial myth's *carrier* not a decolonial authority, every date-guard resolved (Lev d.~1301-not-1308; Mstislav-co-rule post-1024; father d.1170-not-1173).
- **#2670 salvage (claude):** symon-petliura + lina-kostenko — the 2 fully-written dossiers rescued from the limit-killed claude waves (see lesson). Both SHIP; strong anti-hagiography + honest-gap discipline.

**⚠⚠ DUAL-LIMIT LESSON (do NOT re-derive) — BOTH writer lanes hit limits in one session:**
1. **claude 5h limit:** firing **2 parallel `--agent claude` dispatches (waves I+J) + the interactive driver seat** overran the rolling 5h window (user confirmed: *"we hit 5h limit"*). Both died `returncode 1`, `response_chars 0` at ~532s, having written only their FIRST dossier each (petliura, kostenko — salvaged into #2670). **POLICY: dispatched claude capped at 1 concurrent — NEVER 2. The interactive driver seat counts toward the 5h pool.**
2. **codex rate_limited:** after the ~2.5h Wave K succeeded, Wave L immediately returned `status: rate_limited` / `stderr: "codex/gpt-5.5 rate limited: OpenAI Codex v0.136.0"` (no work written). Codex burned its budget on Wave K. (A `bio-p2-waveL-retry` diagnostic was fired to distinguish per-minute vs hard-cap.)
3. **POLICY: when BOTH lanes are limited, PAUSE writers — do not thrash quota.** DeepSeek (off-seat, Hermes `-z` one-shot) is review-only — NOT an agentic writer (can't drive worktree→lint→commit→PR).

**3RD-WRITER ASSESSMENT (user asked 2026-06-03 "one codex, one claude, and the third who? only if strong trusted"):** **No qualified 3rd strong-trusted agentic writer exists today.** codex+claude are the only two. gemini-3.1-pro = strong model but **dispatch-writer broken (#2454 SIGTERM @87s)** — only `ab ask-gemini` Q&A works; cursor = supplement-grade + **dead until #2549** (unmerged); deepseek/grok = Hermes one-shot (reviewers, not agentic writers); qwen excluded (cost); agy fabricates §7. **THE ONE UNLOCK = fix #2454** → gemini becomes the genuine 3rd agentic writer (it was the cross-family reviewer of record pre-DeepSeek). Pending user nod; note it ALSO needs a live agent lane to dispatch the fix.

**FLEET (this segment, post-limits):** **1 codex** (separate quota, when not rate-limited) + **1 claude capped** (when 5h window clear) + **DeepSeek off-seat reviewer**. gemini = `ab ask-gemini` only; cursor dead.

**RESERVED / QUEUED:**
- **`roman-shukhevych`** — held for the single claude seat once the 5h window clears (the most NPOV-severe figure; claude handled the shukhevych family well before). Brief in `/tmp/brief-bio-p2-waveI.md` (figure 3, full Schutzmannschaft-201 / Volhynia-Motyka / Himka warnings).
- **codex Wave L** (4 statehood: konovalets, bolbochan, mikhnovskyi, chykalenko) — brief `/tmp/brief-bio-p2-waveL.md`; pending codex reset (retry `bio-p2-waveL-retry` in flight).
- **codex Wave M** (5 writers: zabuzhko, zhadan, andrukhovych, vynnychuk, shkliar) — derive from `/tmp/brief-bio-p2-waveJ.md` minus kostenko; pending codex reset.

**2 PHASE-4 BACKFILL NOTES (advisory from DeepSeek — NOT dossier defects, fix at lesson/wiki build):**
- `petliura`: lock the anti-pogrom order number/date (dossier cites наказ ч.131 26.08.1919 per Hunczak; corpus showed a different 17 Jun 1919 order) to the Hunczak edition used in the student module.
- `danylo`: lock the exact Hrushevsky quote edition (full archaic line "на скільки він був сином минувшого, а не чоловіком будущини") before student-facing text.

**NEXT ACTION ON RESUME:** when a writer lane recovers — fire Wave L (4 statehood) + Wave M (5 writers) on codex (1 seat, sequential) and `shukhevych` on the 1 claude seat; DeepSeek cross-review each (inline ONLY the new files); merge per grant once SHIP + CI green + scope-clean; recompute the self-correcting queue. If both lanes stay capped, hold and let quotas reset (don't thrash). Re-offer the #2454 fix to unlock gemini as the 3rd writer.

---

## ▶▶▶▶▶▶▶ SESSION UPDATE (2026-06-03, NIGHT) — P2 DOSSIER PRODUCTION RUNNING (48 merged, ~92 left) (read FIRST)

**Supersedes the block below's "NEXT ACTION: fire P2 batch 1" — P2 waves 1–2 are DONE & merged.**

**STATE:** `docs/research/bio/` on origin/main = **219 dossiers** (was 150 at session start). The original-180
dossier gap is now **~92** (recompute deterministically: `git ls-tree -r --name-only origin/main
curriculum/l2-uk-en/plans/bio/` minus `…docs/research/bio/` = plans-without-dossier; that set IS the queue,
self-correcting, so a resume never redoes finished figures). `petro-veskliaov` still DEFERRED (slug rename
→`petro-vesklyarov` first).

**MERGED THIS SESSION (30 P2 dossiers, all DeepSeek cross-reviewed, §7+word-count CI gates green):**
- **Wave A #2602:** franko · lesya-ukrainka · skovoroda · kotliarevskyi · kobylianska · kotsiubynsky
- **Wave B #2603:** borys-paton · yevhen-paton · lysenko · dovzhenko · bilokur · drahomanov
- **Wave C #2604:** khvylovyi · mykola-kulish · les-kurbas · stus · symonenko · dziuba
- **Wave D #2605:** nechuy-levytskyi · kvitka-osnovianenko · marko-vovchok · mazepa · pylyp-orlyk · khmelnytskyy
- **Wave E #2606:** panteleimon-kulish · hrinchenko · starytsky · kropyvnytskyi · olena-pchilka · stefanyk
- **Wave F #2609 (claude):** boichuk · malevich · arkhypenko · serge-lifar · vira-kholodna · krushelnytska — 6/6 SHIP
- **Wave G #2610 (claude):** korolyov · kondratiuk · vernadskyi · puliui · amosov · antonov — 6/6 SHIP
- **Wave H #2611 (CODEX gpt-5.5):** sahaidachny · ivan-sirko · polubotok · kalnyshevskyy · danylo-apostol · vyhovskyi — 2 SHIP + 4 minor fixes applied (Konotop OS/NS date · Sobieski quote · 2 quote-corroboration notes)
(Plus the prior session's P1 21 dossiers #2595–2600 + prompt PR #2593 — all merged by me this session. **Session total = 69 dossiers.**)

**CODEX-LANE DATA POINT (Wave H = first codex dossier wave):** viable but needs MORE review-fixing than claude
(4 minor fixes vs 0/wave for claude) and writes **leaner** dossiers (~1,640 vs ~2,500 words). All factually
sound; nothing fabricated. Keep codex as the 1 extra lane **WITH DeepSeek cross-review** — the backstop matters
more for codex. (DeepSeek also recurred its ghost-slug false-positive on Wave C; always git-verify "missing-plan" findings.)

**FLEET (user 2026-06-03):** ran 3 writers/wave briefly, user CUT to **2 claude**, then **CONFIRMED add 1
codex** → current cadence = **2 claude + 1 codex writers per wave**. claude = `--agent claude` (claude-tools);
codex = `--agent codex --model gpt-5.5` (separate quota, 1 seat). Reviewer = **DeepSeek-pro** off-seat,
cross-family for BOTH claude and codex writers. gemini = `ab ask-gemini` only (metered); cursor dead until #2549.

**PROVEN LOOP (replicate per wave):** (1) pick ~6 figures/batch from the recomputed queue, embed per-figure
**audit warnings** from `batch_state/tasks/bio-audit-rev-b*.result` (load-bearing). (2) Brief template lives at
`/tmp/brief-bio-p2-wave{A..E}.md` (recompute from those if /tmp lost — TODO: persist to docs/). (3) Fire
`delegate.py dispatch --agent {claude|codex} --task-id bio-p2-wave<X> --prompt-file <f> --mode danger --effort
xhigh --worktree --base main` (codex adds `--model gpt-5.5`). (4) Watch via backgrounded `until`-loop on
`/api/delegate/active`. (5) Per wave: read ≥1 dossier (m20 lesson) + verify scope (`gh pr view --json files`
= 6 `docs/research/bio/*.md`) + gates. (6) DeepSeek cross-review: build prompt inlining ONLY the 6 new files
(NOT a worktree glob — that pulls all 200+ dossiers), `--agent deepseek --model deepseek-v4-pro --mode read-only
--initial-response-timeout 900 --silence-timeout 3600`, prompt MUST end with "your FINAL message must be the
full verdict table" (the first review silent-failed at 32 bytes / "Review complete" without it). (7) Apply FIX
after deterministic verification; merge SHIP per grant; clean worktrees.

**TWO LESSONS THIS SESSION (do NOT re-derive):**
1. **DeepSeek ghost-slug FALSE-POSITIVE recurred (Wave C):** it flagged 15 "Existing BIO plans" as MISSING →
   `git ls-tree origin/main curriculum/l2-uk-en/plans/bio/` proved ALL 15 EXIST. The §7 CI gate (passing) is
   authoritative. **ALWAYS git-verify a DeepSeek "missing plan/ghost slug" finding before acting** (matches the
   prior kateryna-hrushevska note). Wave C was therefore merged as SHIP.
2. **claude writer under-claimed `verify_quote` (Marko Vovchok):** `verify_quote(author="Марко Вовчок")` returned
   0.0 and the dossier wrongly declared "her texts absent from corpus / honest gap." The texts ARE ingested as
   corpus **`ukrlib-vovchok`** and both quotes verify at **1.0**. A bare author-name query can false-0.0; the
   author's own works live under `ukrlib-<surname>`. **Bake into the writer brief** as lesson #5.

**NEXT ACTION ON RESUME:** fire the next wave (**2 claude + 1 codex**) of ~6 figures each from the recomputed
~110-queue, worst/foundational-first, with per-figure audit warnings → DeepSeek review → merge → refresh THIS
handoff. Also still queued: Task-#6 five plan-level fixes (pohribnyi dates · portnikov patronymic · bohomazov
birthplace+date · vasylenko case · pavlychko smear) via plan-versioning; then the wiki half (verify/rebuild 180
original wikis vs the new dossiers + Phase-4 130 new 181–310 wikis).

---

## ▶▶▶▶▶▶ SESSION UPDATE (2026-06-03, EVENING) — P1 (22 worst-first) FULLY LANDED ON MAIN + P2 STARTED (read FIRST)

**Supersedes the "OPEN PRs / awaiting orchestrator promotion / IN-FLIGHT" status in every block below — those P1 PRs are now MERGED to main.**

**MERGED ALL 7 P1 PRs this session** (user 2026-06-03 re-confirmed the merge-grant: *"merge all 7"*):
- **6 dossier PRs → 21 dossiers on main** (#2595 leontovych · #2596 shevchenko · #2597 olha/monomakh/berezovskyy · #2598 wave2-B[6] · #2599 wave2-A[6] · #2600 wave3[4]). `docs/research/bio/` on origin/main = **171** (was 150). Each: DeepSeek cross-reviewed (21/22 SHIP), passed the BLOCKING §7-xref + dossier-word-count CI gates, pure additions, no collisions; leontovych content spot-read = genuinely sourced/decolonized (verbatim Cheka рапорт, unsmoothed source-disagreement notes). main `2a28f1fc7c`.
- **#2593 → wiki VERIFY-marker prompt relaxation + this handoff** (`scripts/wiki/prompts/compile_article.md`). Shared wiki infra. **A2 impact verified BEFORE merge: ZERO effect on the in-flight A2 work** — the 13 A2 PRs (#2579–2592) hand-edit `wiki/grammar/a2/*.md` + `plans/a2/*.yaml` and do NOT recompile via `compile.py`, so no file overlap + no behavioral dependency — and **net-positive for future A2/hist/lit compiles** (removes the over-aggressive VERIFY-marker flood A2 is currently hand-clearing across those 13 PRs). **TODO this session: notify orchestrator the shared prompt changed.**

**P2 METHOD = PROVEN SERIAL LOOP** (user 2026-06-03 chose serial over the capped Workflow). ~5–6 figures/batch · claude writer fleet · DeepSeek cross-review per batch · PRs OPENED then MERGED per the grant once review=SHIP + CI green + scope-clean.

**petro-veskliaov still deferred** until its slug rename →`petro-vesklyarov` (rename via plan-versioning `.bak`+bump first, then its dossier).

**NEXT ACTION (this session, in order):** (1) merge #2593 [done as this PR lands]; (2) notify orchestrator re: shared `compile_article.md` change; (3) fire P2 batch 1 — ~5–6 of the 139 remaining ungrounded original-180 dossiers (priority list `/tmp/dossier-priority2-rest.txt`, recomputable; template `/tmp/brief-bio-dossier-batch-TEMPLATE.md` + 4 lessons + per-figure audit warnings from `batch_state/tasks/bio-audit-rev-b*.result`), DeepSeek-review, merge. Queued after: Task-#6 5 plan-level fixes (pohribnyi dates · portnikov patronymic · bohomazov birthplace+date · vasylenko case · pavlychko smear) via plan-versioning; then the wiki half (verify/rebuild 180 original wikis vs new dossiers + Phase-4 130 new 181–310 wikis).

---

## ▶▶▶▶▶ SESSION UPDATE (2026-06-03) — ORIGINAL 1–180 LACK DOSSIERS (160/180); FULL UPLIFT SCOPED (read FIRST)

**THE HEADLINE (deterministically verified on origin/main, this session):** the original 180 bio
figures were NEVER systematically dossier'd. Only **20/180 have a dossier** (19 exact + the
`levko-lukianenko`→`levko-lukyanenko` variant); **~160 lack one entirely** — including the
foundational figures **Taras Shevchenko, Ivan Franko, Lesya Ukrainka, Skovoroda, both Patons,
Leontovych**. Their wikis are LIVE on the site but **ungrounded** — that is the real root cause
behind the #2535 "ghost/fabricated" audit findings. (Phase 1 produced 137 dossiers, but those were
the 130 NEW figures + 7 documenting existing plans — NOT a pass over the original 180.) No unmerged
dossier work exists (checked: 0 untracked, 0 dossier branches).

**THE MIRROR-IMAGE STATE (origin/main: 310 plans · 150 dossiers · 180 wikis):**
- **Original 1–180:** have WIKIS, lack DOSSIERS (~160/180 missing).
- **New 181–310:** have DOSSIERS (130/130), lack WIKIS (0/130 — Phase 4 pending).
- True epic end-state = **every figure has BOTH a sourced dossier AND a source-grounded wiki.**
- Unified pipeline: **[dossier] → discovery → wiki → dossier-grounded review → gate.** Original-180
  start at `[dossier]`; new-130 start at `discovery`.

**USER DECISIONS (2026-06-03):**
1. **Full uplift** — build ALL ~160 missing dossiers for 1–180 (Phase-1 quality, sourced,
   anti-fabrication gated by `lint_bio_dossier_xref.py`), THEN dossier-grounded wiki verify/rebuild.
   NOT just the ~17 BLOCK ghosts (those are a subset of the dossier gap).
2. **Interleave** the two halves: original-180 dossier-building ∥ Phase-4 new-130 wiki-building,
   across available seats.
3. **Decide the Workflow (capped fan-out) AFTER a pilot** validates both pipelines via the serial
   dispatch loop. (~290 artifacts total → Workflow is the right scale tool; needs the opt-in.)

**SHIPPED THIS SESSION (PR pending — bundle this handoff):** VERIFY-marker prompt relaxation
(`scripts/wiki/prompts/compile_article.md`, commit `2a2bbcf2e7` + cross-review amendment). Narrows
`<!-- VERIFY -->` to *extraordinary/contestable* Wikipedia-only claims (was: every routine
Wikipedia-only fact → 11–18 markers/article → hard write-block → recompiles failed). DeepSeek
cross-review = FIX-BEFORE-MERGE: **Edit 1 ADOPTED** (bullet-2 anchored to "де українські джерела
самі між собою не збігаються" — attested source-disagreement, not the writer's politics). **Edit 2
(inline `(лише wiki)` note) DEFERRED to the review layer** — would pollute published prose; the
signal already exists deterministically (`{slug}.sources.yaml` maps each `[S#]`→chunk_id, so
`ext-wikipedia-*`-backed claims are greppable). Mitigation lives in the wiki-review brief:
"cross-check every `ext-wikipedia-*`-backed claim against the dossier."

**NEXT ACTION ON RESUME:**
1. Land the prompt-relaxation PR (this handoff bundled). Shared wiki infra → orchestrator reconciles
   (or merge per bio merge-grant if treated as bio-scoped; it is motivated by + only affects bio Phase-4
   + #2535 today).
2. **PILOT both pipelines (serial dispatch loop, no Workflow yet):**
   - *Original-180 path:* pick 1 high-value ungrounded figure (e.g. `taras-shevchenko` or
     `ivan-franko`) → build dossier → discovery → recompile wiki (codex `--writer gpt-5.5` + relaxed
     prompt + `--allow-verify-markers`; symlink `<wt>/data/{sources,vesum}.db`→main) → verify subject
     + sources → DeepSeek dossier-grounded review.
   - *New-130 path:* pick 1 figure WITH a dossier (181–310) → build real discovery → compile wiki →
     review. Confirm the relaxed prompt drops the marker count (the empirical proof of the PR).
3. If both pilots clean → bring the user a **capped Workflow proposal** (cost + structure) for the
   ~290-artifact scale-up, then fan out.

**IN-FLIGHT:** none (DeepSeek prompt review harvested + applied; 0 dispatches active).

## ▶ AUTONOMOUS RUN LOG (2026-06-03, user at work — drive without questions)

**Dossier PIPELINE PROVEN + SCALING.** User away; serial dispatch loop (NO Workflow — needs opt-in).
Policy: OPEN dossier PRs, do NOT self-merge (orchestrator promotes; dossiers independent → no blocking).

**Proven assets (reuse):**
- Batch brief template: `/tmp/brief-bio-dossier-batch-TEMPLATE.md` — `{{FIGURES}}` placeholder + 3
  hard-won lessons (verify every source URL actually resolves; self-check must match content, mark
  `[N/A]` otherwise; never conflate completion vs premiere/anniversary dates). **Per-figure warnings
  are load-bearing** — pull each figure's defect from `batch_state/tasks/bio-audit-rev-b*.result`
  (BLOCK rows) and add a `⚠`-note (Синопсис-inversion, Mozart-myth, contested surname, wrong dates,
  unverified smear, ghost-identity) — the writers heed them.
- Dispatch: `delegate.py dispatch --agent claude --task-id <id> --prompt-file <f> --mode danger
  --effort xhigh --worktree --base main`. ~5-6 figures/batch, 2-claude cap. DeepSeek review off-seat
  (`--agent deepseek --model deepseek-v4-pro --mode read-only --initial-response-timeout 900`);
  INLINE dossiers into the review brief via `cat` (read-only deepseek runs on main, can't see branches).
- Priority order in Task-list / here: **P1 = 22 BLOCK+no-dossier (worst-first)**, then **P2 = 139**
  (`/tmp/dossier-priority2-rest.txt`, recomputable). SKIP `petro-veskliaov` until its slug rename
  (→`petro-vesklyarov`) is resolved.

**DONE / OPEN PRs (all awaiting orchestrator promotion — NOT self-merged):**
- #2593 wiki VERIFY-marker prompt relaxation (+ this handoff) — DeepSeek-reviewed.
- #2595 dossier `mykola-leontovych` (PILOT) — DeepSeek FIX applied (opera 1975; dead URLs; self-check).
- #2596 dossier `taras-shevchenko` — spot-read clean (4 quotes verify_quote-confirmed).
- #2597 dossiers `knyahynia-olha` + `volodymyr-monomakh` + `maksym-berezovskyy` — Синопсис critiqued
  (not inverted), cap-myth via anachronism, Mozart-legend in §6. Spot-read clean.

**WAVE-1 REVIEWED (DeepSeek combined):** shevchenko/olha/berezovskyy SHIP; monomakh FIX-BEFORE-MERGE
(self-check claimed verify_quote 0.99 but tool returns 0.0 — quotes genuine, corpus attributes ПВЛ to
"Нестор"). FIXES APPLIED + pushed: monomakh ×3 (#2597), shevchenko arrest-date note (#2596). → batch
brief LESSON 4 added: never claim a tool score you didn't get.

**WAVE-2 DONE + REVIEWED — ALL 12 SHIP (PRs #2598 batchB + #2599 batchA).** DeepSeek `review-wave2-12`:
12/12 SHIP, zero dossier defects; every per-figure trap handled (prymachenko both-sides surname;
pavlychko unverified smear omitted; pohribnyi wrong dates caught). No fixes needed.

**WAVE-3 DONE + REVIEWED — ALL 4 SHIP (PR #2600: kuzma-skryabin, pavlo-sheremet, yuriy-ruf, oleksandra-matviichuk).**
DeepSeek `review-wave3-4`: 4/4 SHIP, no fixes. ruf person-substitution guard PASSED (real Юрій Руф/Дадак,
b.1980 Бережани d.2022; zero Артур Дронь); skryabin death = ДТП not repression (honest); sheremet no
editorial markers; matviichuk Nobel correctly scoped + living-NPOV. **P1 = 21/22 COMPLETE + fully reviewed.**

**P1 STATUS: 21/22 DONE** (5 wave-1 + 12 wave-2 + 4 wave-3). Only `petro-veskliaov` deferred (do its
slug rename →`petro-vesklyarov` first, then dossier).

**⚑ NEW FOLLOW-UP — 5 PLAN-LEVEL errors the wave-2 dossiers caught (fix via plan-versioning flow `.bak`+bump;
NOT dossier defects):** (1) `pohribnyi` dates 1931-2003→1920-05-13..1994-03-31; (2) `vitaly-portnikov`
patronymic Янович→Едуардович; (3) `oleksandr-bohomazov` birthplace Ямпіль→Янків Ріг/Іванівка + «Пилярі»
1914→1927; (4) `mykola-vasylenko` case СВУ→«Київський обласний центр дій» (1923-24); (5) `dmytro-pavlychko`
remove «жидівська мафія» attribution (unsourced) → replace w/ documented controversies.

**OPEN PRs (all awaiting orchestrator promotion):** #2593 (prompt+handoff) · #2595 leontovych · #2596
shevchenko · #2597 olha/monomakh/berezovskyy · #2598 wave2-B (6) · #2599 wave2-A (6) · #2600 wave3 (4).

**IN FLIGHT (2026-06-03):** NONE — 0 dispatches active; all wave PRs open + reviewed; clean milestone.

**RESUME HERE (next session / user):**
1. **P2 — 139 remaining dossiers** (`/tmp/dossier-priority2-rest.txt`, recomputable). Best via the capped
   **Workflow** (user opt-in: "use a workflow" [+budget]); else serial loop with the proven template
   (`/tmp/brief-bio-dossier-batch-TEMPLATE.md`, 4 lessons) + per-figure audit warnings from
   `batch_state/tasks/bio-audit-rev-b*.result`. ~5-6/batch, 2-claude cap, DeepSeek review per batch, PRs open.
2. **petro-veskliaov** — do slug rename →`petro-vesklyarov` first, then its dossier.
3. **Task #6 — 5 plan-level errors** (pohribnyi dates / portnikov patronymic / bohomazov birthplace+date /
   vasylenko case / pavlychko smear) via plan-versioning flow.
4. **Wiki half** (once #2593 on main): verify/rebuild 180 original wikis vs their new dossiers + Phase-4
   (130 new wikis 181-310). Reviewer brief MUST cross-check every `ext-wikipedia-*`-backed claim vs the
   dossier (DeepSeek Edit-2 mitigation from the prompt PR).

**NEXT (resume): harvest wave-2 → DeepSeek review → apply fixes → leave PRs open. Then P1 remainder
(kuzma-skryabin, pavlo-sheremet, yuriy-ruf, oleksandra-matviichuk + petro-veskliaov-after-rename) →
P2 (139) in ~5-6/batch waves. THEN the wiki half (discovery→codex compile w/ relaxed prompt→review→
rebuild) once #2593 is on main + Phase-4. Re-offer the capped Workflow to the user for the ~290-artifact
remainder when they're back (it's the right scale tool; needs opt-in).**

## ▶▶▶▶ SESSION UPDATE (2026-06-02, LATE) — 4-DEFERRED-WIKIS ROOT CAUSE IS SYSTEMIC, NOT A DEAD-DATE GAP (read FIRST)

**Branch `bio/fix-4-deferred-wikis` (PR #2574): DONE — all 4 wikis recompiled to the CORRECT subject and
ship (advisory VERIFY markers as review TODOs), plus authoritative ЕІУ/IEU spine chunks, an opt-in pipeline
flag, a subject-gate ґ/г fix, and this handoff. The gate blocker was bigger than the prior handoff assumed;
I decided option (C) and executed it. 0 dispatches fired (all inline diagnosis + WebFetch + local codex
compiles via `--writer gpt-5.5`). DeepSeek cross-family review DONE: 3 SHIP + 1 FIX (slisarenko
«найвищу кару»→«смертну кару», applied). **PR #2574 MERGED to main (`c3e0e759d2`, 2026-06-02).** The 4
wiki pages on main now name the correct figures (no more Mykola Kulish). **`wiki/index.md` regenerated in a
follow-up (this PR)** — it also corrected 5 OTHER stale #2565 Kulish titles in the index (zerov, petrytskyi,
yohansen, kosynka, pidmohylnyi were rebuilt but the index was never refreshed) and dropped a duplicate
`rutkivsky-dzhury-2` root orphan (real `literature/works/` entry kept; total 1687→1686).

### What the prior handoff got wrong about the 4 deferred wikis
The prior (PM) block said the fix was "add an authoritative ЕІУ/encyclopedic **death-date** chunk so the
date is un-hedgeable, then `compile.py --writer gpt-5.5 --force`." **That is necessary but FAR from
sufficient.** Empirically reproduced (3 falkivskyi + 1 pluzhnyk codex compiles, ~160s each):

- `compile_article` does NOT write the `.md` if codex emits **any** `<!-- VERIFY -->` marker — it raises
  before the atomic write, so the OLD Kulish wiki stays (that's why git shows the wikis unchanged after a
  "failed" compile, and why the H1 is still Kulish). The gate is a hard **write-block**, not advisory.
- The wiki prompt `scripts/wiki/prompts/compile_article.md` (lines 46/50/124) ORDERS the writer: *any*
  historical claim (date, name, **event, education, place, motive**) resting **only on a `source_type:
  wikipedia` chunk** must get `<!-- VERIFY -->`. `compile.py` reads ONLY the discovery, **never the
  dossier** — so even dossier-corroborated facts trip the gate if the discovery's only source for them is
  a Wikipedia chunk.
- So adding ONE ЕІУ death-date chunk just moves the marker to the next Wikipedia-only detail. Observed
  cascade on falkivskyi: death-date → birth/real-surname/birthplace → **surname-change motive**; on
  pluzhnyk → **gymnasium/Kyiv-institute education sequence**. Every figure's discovery is Wikipedia-rich
  but ЕІУ-thin, and ЕІУ never has Wikipedia's granularity, so **there is always a Wikipedia-only detail
  left to flag.** This is SYSTEMIC, not a per-figure data gap.
- Brute-forcing it = stripping granular biographical detail from the Wikipedia chunks until none is
  Wikipedia-only. That is lossy and, for figures like **falkivskyi**, editorially fraught: his
  surname-change motive ("страх помсти за причетність до масових убивств") is a **deliberate
  anti-hagiography / decolonization point in the vetted dossier** (he was perpetrator-then-victim). I will
  NOT silently sanitize that.

### What I DID this session (all #M-4 verified, verbatim sources)
- Added a non-Wikipedia authoritative biographical chunk (`source_type: literary`, so the writer treats it
  as primary, not the demoted `ext-wikipedia-*` tier) to each of the 4 discovery `rag_literary` lists:
  **ЕІУ** (Герасимова Г. П., resource.history.org.ua, verbatim) for falkivskyi / pluzhnyk / slisarenko;
  **IEU** (encyclopediaofukraine.com, Koshelivets, verbatim) for shkurupii. Each covers the full spine
  (name, real surname, birth date+place, death date+place, repression, rehabilitation). Death dates
  cross-checked vs dossiers: falkivskyi 16.12.1934 Київ · pluzhnyk 02.02.1936 Соловки (TB) · slisarenko
  03.11.1937 (Сандармох locus kept in the Wikipedia chunk; ЕІУ says "на Соловках") · shkurupii 08.12.1937
  Ленінград (NOT Sandarmokh; name Ґео). slisarenko surname noted: established = Снісар; ЕІУ minority = Сніцар.
- Fixed an infra gotcha: a manual worktree has NO `data/sources.db` (gitignored 1.68 GB) → enrichment
  `search_sources` crashes (`no such table: textbooks_fts`). FIX: symlink `<wt>/data/sources.db` and
  `vesum.db` → main repo (gitignored, zero git impact). **Bake this into any future manual-worktree compile.**

### DECISION MADE + EXECUTED — option (C): advisory gate, ship now, backfill later (user 2026-06-02: "it's on you, you're the orchestrator")
A wiki about the RIGHT person carrying VERIFY markers is strictly better than a live wiki about the WRONG
person (Mykola Kulish), and the markers are honest source-criticism — a positive signal on a source-first
seminar track, not a defect. The hard write-block was designed to stop bad NEW wikis; on a recompile over a
known-wrong wiki its failure mode is perverse (it preserves the worse artifact). So I shipped:
- **`--allow-verify-markers`** (commit `6f7522c7`): opt-in flag, default OFF (strict gate unchanged), that
  writes the corrected article and logs surviving markers as `verify_marker_advisory` review TODOs. Threaded
  through `compile_article`/`_write_article_bundle_atomic`/`cmd_compile_one`/`cmd_compile_all` + CLI. 3 hermetic tests.
- **4 recompiled wikis** (commit `0807360`): all name the right figure, all pass `check_wiki_subject`.
  Content spot-read (falkivskyi full + slisarenko/shkurupii landmines): decolonized, accurate, dates correct,
  falkivskyi's ВЧК perpetrator-past handled honestly (not sanitized), shkurupii = Ленінград-not-Sandarmokh + Ґео,
  slisarenko surfaces the Снісар/Сніцар variant with attribution. Marker counts 11–18 = backfill TODO.
- **ґ→г subject-gate fix** (`bio_subjects.same_person`): canonical «Ґео» H1 now matches a Soviet-orthography
  «Гео» plan title (same person); without it shkurupii false-positived the H1 gate. Hermetic test added.
- **Infra gotcha**: a manual worktree has NO `data/sources.db` (gitignored 1.68 GB) → enrichment crashes
  (`no such table: textbooks_fts`). FIX: symlink `<wt>/data/{sources,vesum}.db` → main repo. Bake into future compiles.

### KNOWN FOLLOW-UPS (quality-debt, tracked — not blockers)
1. **Marker backfill**: the writer flags routine Wikipedia-sourced facts (journal names, group memberships)
   as well as contestable ones, so counts are 11–18/article. Two durable fixes: (a) relax
   `scripts/wiki/prompts/compile_article.md` so the writer flags only EXTRAORDINARY/contestable claims, not
   every routine biographical fact sourced to Wikipedia; (b) keep backfilling ЕІУ/scholarly chunks into discovery.
2. **shkurupii plan title** uses Soviet-orthography «Гео» — fix to canonical «Ґео» via the plan-versioning flow
   (`.bak` + version bump). The ґ/г gate fix makes this non-urgent (gate passes either way).
3. **wiki/index.md regen: DONE** (this PR) — corrected the 4 figures + 5 stale #2565 titles (zerov,
   petrytskyi, yohansen, kosynka, pidmohylnyi) and removed the duplicate `rutkivsky-dzhury-2` root orphan
   (the real `literature/works/` entry is kept). The "drop" was a phantom-duplicate removal, not a regression.

### NEXT ACTION ON RESUME — the 4-deferred-wikis P0 is CLOSED + merged. Next bio work:
1. **Follow-up #1 — relax the writer prompt** (`scripts/wiki/prompts/compile_article.md`) so the wiki writer
   flags only EXTRAORDINARY/contestable claims, not every routine Wikipedia-sourced biographical fact. This
   cuts the 11–18 advisory-marker counts on future bio recompiles. Cross-review the prompt change.
2. **Phase-4 wikis (bio-181..310)** — the big remaining build: ~130 new wiki articles. `--writer gpt-5.5`
   (codex; claude --writer is broken for wikis — root-cause learning above), DeepSeek cross-review, gated.
   RE-OFFER THE WORKFLOW to the user (capped fan-out is the right tool for 130 artifacts).
3. **Rest of the #2535 existing-180 audit backlog** (the remaining BLOCK/FIX items past the 4 wikis).
4. Optional tidy: shkurupii plan title «Гео»→«Ґео» (follow-up #2 above; non-urgent, gate passes either way).

---

## ▶▶▶ SESSION UPDATE (2026-06-02, PM) — 6 PRs MERGED + 2 ROOT-CAUSE LEARNINGS (read FIRST)

This Claude bio-driver session shipped **6 PRs to main** against #2535, each cross-family (DeepSeek) reviewed:
- **#2561** Stage-0 prevention gates (validators: check_wiki_subject, check_discovery_integrity,
  check_citation_resolution, check_wiki_verify_markers + lint_seminar_quality wiki-scan). NOT yet wired
  BLOCKING in CI (would redden main until the known defects clear).
- **#2564** 3 fabricated-identity plans rebuilt: berta-rapoport (doctor→**first woman sea-captain**),
  klavdiya-latysheva (pilot→**mathematician**), valentyna-radzymovska (Terror-execution myth→**emigrated,
  died USA 1953**). DeepSeek caught + I fixed a ghost `connects_to: mykhailo-kravchuk`.
- **#2565** 5 Розстріляне-відродження wikis rebuilt from Kulish content-dups (zerov, petrytskyi,
  yohansen, kosynka, pidmohylnyi) — real 1841–2861w sourced articles.
- **#2566** dossiers + **enriched discovery** for the 4 source-starved figures (slisarenko, falkivskyi,
  pluzhnyk, shkurupii) + new shkurupii dossier. All SHIP.
- **#2567** mariia-voiakovska rebuilt (Vienna fabrication → **Підгайчики/Галичина 1868, Вояківська**).
- **#2568** decolonization + factual: Синопсис-inversion ×2 (knyahynia-olha, volodymyr-monomakh) +
  Mozart-Bologna myth demoted ×2 (berezovskyy, bortnyanskyy) + date fixes.

### TWO ROOT-CAUSE LEARNINGS (do NOT re-derive)
1. **`compile.py --writer claude` is BROKEN for wikis** — it emits chat-narration ("Done. Here's what I
   did…") instead of article text, and compile.py writes that to the `.md`. **USE `--writer gpt-5.5`
   (codex) for ALL wiki compiles** (clean articles). claude is fine for PLANS / DOSSIERS / agent
   dispatches (Stage 2 + the dossier/plan rebuilds all worked). **Seat split: codex=wikis,
   claude=plans+dossiers, deepseek=review.**
2. **codex hedges thin-source DEATH dates with `<!-- VERIFY -->` → the #2561 check_wiki_verify_markers
   gate correctly BLOCKS the write (rc=1), leaving the old broken wiki.** This is why the **4 wikis
   (slisarenko, falkivskyi, pluzhnyk, shkurupii) are DEFERRED** — their dossiers+discovery are correct
   on main (#2566) but the recompile fails on the hedge. FIX: add an authoritative ЕІУ/encyclopedic
   death-date source chunk to each discovery so the date is un-hedgeable, then `compile.py
   --writer gpt-5.5 --force` → verify H1 → commit.

### DEFERRED FOLLOW-UPS (resume queue, priority order)
- **(P0) 4 deferred wikis** — resolve the death-date hedge (above) → recompile (codex) → verify → PR →
  DeepSeek → merge. DeepSeek-verified dates: slisarenko **3 Nov 1937 Сандармох** · falkivskyi
  **16 Dec 1934 Київ** · pluzhnyk **2 Feb 1936 Соловки** · shkurupii **8 Dec 1937 Ленінград** (a
  SEPARATE execution from the Sandarmokh batch — do not conflate). shkurupii name = **Ґео** (ґ).
- **petro-veskliaov.yaml → petro-vesklyarov.yaml** filename rename (internal `slug:` already correct, content OK).
- **wiki/index.md regen** — excluded from #2565 (stale worktree copy at 1686); run `compile.py --update-index` on main.
- **107 mechanical wiki-path remaps** (cheap-wins) — via the apply-plan-fixes versioning flow (`.bak`+bump).
- Remaining #2535 audit backlog (rest of 30 BLOCK / 82 FIX) + Phase-4 wikis bio-181..310.

### SEAT + BILLING (user 2026-06-02)
- **June-15 cliff**: `claude -p` (all `delegate --agent claude`) moves OFF subscription onto a metered
  Agent SDK credit at full API rates; interactive Claude stays on subscription. → **front-load claude
  NOW** (pre-cliff, ~61% weekly used). User authorized **3× claude seats — USE THEM**. Do NOT build a
  TOS-gray `-p` workaround.
- Fleet that worked this session: **3× claude** (plans/dossiers, parallel) + **1 codex** (wikis,
  `--writer gpt-5.5`) + **deepseek** off-seat (cross-review ~160–230s, reliable, not quota-bound).
  gemini = `ab ask-gemini` only; cursor dead until #2549.
- **DeepSeek can FALSE-POSITIVE ghost slugs** (it flagged kateryna-hrushevska as ghost, but it EXISTS on
  main — `git ls-tree` confirms). ALWAYS deterministically verify a reviewer's ghost-slug finding before acting.

*main observed at `6a4a6e42b6` after this session's 6 merges.*

---

## ▶▶ CURRENT SESSION STATE (2026-06-02) — EXISTING-180 AUDIT COMPLETE + REMEDIATION IN FLIGHT (#2535)

**THIS is the live workstream. Read this block first.** Per user direction: audit + uplift the EXISTING
1–180 bio plans/wikis to the source-first seminar standard (#2535). User chose the **Hybrid** path (cheap
wins now → staged dossier/wiki rebuild). User: "be vigilant", "use the claude compute", codex unlocked @ 1 seat.

### Audit result — ALL 180 original figures reviewed (15-batch Claude source-first review fleet + deterministic checks)
**30 BLOCK · 82 FIX · 56 SHIP (~17% BLOCK).** Review result files: `batch_state/tasks/bio-audit-rev-b{1..15}.result`
(NOT git-tracked — findings captured here). **ROOT CAUSE (unifying): 165/180 lack a dossier** → writer had no
sources → fabricated or off-topic ("ghost") wiki. New 181–310 HAVE dossiers but **0 wikis** (Phase-4 pending) — mirror gap.

**Defect buckets (the remediation work-list):**
1. **Wrong-person (Kulish-dup) wikis — 9 (deterministic, authoritative):** `mykola-zerov, oleksa-slisarenko,
   anatol-petrytskyi, maik-yohansen, dmytro-falkivskyi, yevhen-pluzhnyk, hryhorii-kosynka, valerian-pidmohylnyi,
   heo-shkurupii`. Root cause = their `curriculum/l2-uk-en/bio/discovery/{slug}.yaml` `query_keywords`+`rag_chunks`
   are Mykola Kulish's (2026-04-14 cohort-collapse; all are Розстріляне відродження). #2513 fixed the PLANS only;
   wikis never regenerated. **compile.py builds wikis from DISCOVERY, not the dossier** — so fix = regenerate
   discovery → recompile. (LLM review undercounted [caught 4]; the deterministic wiki-H1 check is authoritative.
   `panteleimon-kulish` is a REAL distinct person — do NOT touch.)
2. **Fabricated identity in the PLAN — ~5 (highest priority, teach falsehoods):** `berta-rapoport` (real: world's
   1st woman sea captain, branded "doctor"), `klavdiya-latysheva` (mathematician, branded "pilot"), `mariia-voiakovska`
   (fabricated Vienna birth + name Вояко→Вояківська), `valentyna-radzymovska` (framed executed — actually emigrated,
   died Illinois 1953; wrong patronymic Павлівна→Василівна), `petro-veskliaov` (malformed slug — needs ID).
3. **Decolonization / myth — 3:** `knyahynia-olha` + `volodymyr-monomakh` cite Синопсис Київський (1674 pan-Russian
   imperial text) as a *decolonial* authority (INVERSION); `maksym-berezovskyy` "beat Mozart at Bologna" myth-as-fact
   + 4 date errors (myth repeated in `dmytro-bortnyanskyy`).
4. **Ghost wikis — ~17 confirmed BLOCK + ~34 suspect pool** (disclaim having sources, fill with off-topic theory):
   incl. mykola-leontovych, both Patons, george-shevelov, josyf-slipyj, serhii-plokhy, yaroslav-hrytsak, serge-lifar,
   taras-shevchenko (citation-grade only). Confirm suspects per-file (the new wiki linter / `check_citation_resolution`).
5. **82 FIX-level:** dates/genealogy/names, `[S#]` non-resolution (no bibliography corpus-wide), `type:primary`
   mislabels (incl. Russian-state portal Історія.РФ, Wikipedia tagged primary).

### IN-FLIGHT right now (watchers armed) — verify via `curl -sS http://127.0.0.1:8765/api/delegate/active`
- **`bio-prevention-gates`** (codex, Stage 0, watcher `by372p7zk`): 5 deterministic gates → PR (no merge). Gates:
  wiki text-scan linter (the task cursor couldn't do), discovery-topic≠figure, wiki-H1≠figure, VERIFY-marker,
  `[S#]`-resolution. Brief: `/tmp/brief-bio-stage0-gates.md`.
- **`bio-fix-kulish-wikis`** (claude, Stage 1, watcher `bbww2pto7`): regen 9 Kulish discovery → recompile wikis → PR
  (no merge). Brief: `/tmp/brief-bio-stage1-kulish.md`. Acceptance = each wiki H1 names the correct figure (not Kulish).
- **PR #2549** (cursor-adapter fix, open, awaiting orchestrator merge): grok's CLI installed `~/.local/bin/agent`
  which shadowed `cursor-agent` in `scripts/agent_runtime/adapters/cursor.py` → every `delegate --agent cursor`
  silently misfired to grok (returncode 2 `--single`). Fix prefers `cursor-agent`. **CURSOR LANE IS DEAD until #2549 merges.**

### MECHANICAL CHEAP-WIN — COMPUTED, NOT yet committed (plan-versioning hook): 107 dead `wiki/bio/`→`wiki/figures/`
reference-path fixes. Deterministic self-ref remap (basename==slug → `wiki/figures/{slug}.md`). **A raw 107-plan edit is
BLOCKED by the `enforce plan version bump + .bak` pre-commit hook — apply via the `apply-plan-fixes` skill / proper
versioning flow (`.bak` + version bump per plan), NOT a raw edit.** This handoff PR therefore carries ONLY the handoff.
Re-run the deterministic remap over all 310 plans, version + commit in the cheap-wins PR. **5 genuine dead NON-self refs
left for Stage 2** (remove/re-cite, NOT self-remap): les-kurbas→`wiki/events/rozstriliane-vidrodzhennia`,
oleh-olzhych→`wiki/history/sachsenhausen`, mariia-prymachenko→`wiki/bio/prymachenko-museum-fire`,
vasyl-kuk→`wiki/sources/avr-org-ua`, vasyl-vyshyvanyi→`wiki/bio/sources/vyshyvanyi-memoirs`.

### NEXT ACTION ON RESUME (in order)
1. **Harvest the 2 in-flight dispatches** (codex gates, claude kulish) → read result/PR. Verify the 9 rebuilt Kulish
   wikis pass the new gates; **DeepSeek-pro cross-review** (cross-family) → merge Stage 1 PR. Promote gates PR (then
   wire them BLOCKING once defects cleared).
2. **PR the mechanical cheap-wins** (107 paths + this handoff) — no cross-review needed (mechanical). Add VERIFY-marker
   strip + `type:primary` re-tag if not folded into the gates PR.
3. **Stage 2 — ~5 fabricated identities:** source-first rebuild (correct dossier→plan→wiki, web/VESUM-verified). Claude
   + the 1 codex seat. Highest priority. + resolve the 5 dead non-self refs + the Синопсис ×2 / Mozart fixes.
4. **Stage 3 — the big uplift:** 165 missing dossiers + ~173 wikis (43 broken original [9 Kulish done in St.1 + ~34 ghost]
   + 130 new 181–310). Claude + codex (1 seat) writer fleets, DeepSeek cross-review, gated. **RE-OFFER THE WORKFLOW** to
   the user here — capped fan-out is the right tool for 300+ artifacts ("workflow" keyword = opt-in).
5. **181–310 deep-audit pass** (only got cross-review at plan-merge; same lens owed; their wikis audited as Phase-4 builds them through the gates).

### Pipeline facts learned this session (don't re-derive)
- `compile.py --slug X --track bio --writer claude --force` builds a wiki from `bio/discovery/{slug}.yaml`
  (`gather_discovery_sources` + `_slug_to_topic`); **dossier is NOT read by compile.py.** Writer options:
  `{gemini, claude, gpt-5.5}`. `rebuild.py` = heavyweight track-phased orchestrator (not per-slug).
- The 180 wikis live in `wiki/figures/{slug}.md`; discovery in `curriculum/l2-uk-en/bio/discovery/{slug}.yaml`.
- Deterministic validators on origin/main: `validate_plan_config.py bio` (✅ 310 valid), `validate_plan_ordering.py`
  (✅ 0 bio err), `lint_bio_dossier_xref.py` (✅), `lint_seminar_quality.py` (plan-only until the wiki-linter PR lands).

---

*Last updated: 2026-06-01 (late). **Phase 2 plan build COMPLETE: main has all 130 new plans, 181→310
contiguous (310 bio plans total).** Phase 3 registration DONE in this PR (curriculum.yaml bio = 310
modules, 181→310 position==sequence). **UPDATE (2026-06-01, later): #2513 fully CLOSED — all 9
Kulish-content-dup rebuilds merged (#2516–2525); `validate_plan_ordering.py` → 0 bio errors. 0 dispatches
in flight. Next bio work = NEXT ACTIONS #1 (landing page 180→310) + #3 (pre-review linter) + #4 (Phase-4 wikis).**
**UPDATE (2026-06-01, session 3): Phase-4 PREREQUISITE DONE — wiki discovery bug fixed (branch
`bio/fix-wiki-discovery`, this PR): `compile.py --track bio --list` now surfaces all 310 (was 180);
`scripts/wiki/sources.py::list_discovery_slugs` reconciles instead of short-circuiting; hermetic regression
test added; wiki suite 75 passed. **Keystone NEXT ACTIONS #3 ALSO DONE — seminar-quality pre-review linter
SHIPPED** (`scripts/validate/lint_seminar_quality.py`, branch `bio/seminar-quality-linter`, 21 tests; triage =
4 HIGH + 2 advisory, all in the new 181–310 plans, zero false positives — see NEXT ACTIONS #3 for the list).
NEXT ACTION on resume = (a) fix the 5 linter findings in a small DeepSeek-cross-reviewed content PR, then
promote the linter to a BLOCKING CI gate; (b) run the Phase-4 discovery pipeline for 181..310, then the CLAUDE
wiki writer fleet (DeepSeek cross-review). 0 dispatches in flight.** *

## ▶ CURRENT STATE (2026-06-01)
- **SESSION 2 (later, 2026-06-01) shipped:** #2513 fully closed (9 Kulish-dup rebuilds, all DeepSeek
  cross-reviewed + merged) · landing page 180→310 (#2527) · VESUM-verified language cleanup of 10 plans
  (#2528) · routing.html monitor-shell CI-unblock (#2529, was reddening main pytest) · handoff (#2515).
  **NEXT = Phase-4 wikis, but fix the discovery bug FIRST (NEXT ACTIONS #4).** main @ `dd2aa20a1c`.
- **origin/main: 310 bio plans, 181→310 contiguous (130/130). Phase 2 plan-writing is FINISHED.**
- **248–259 gap CLOSED this session** (the last gap). Merges: #2505 (248-251 codex), #2507 (252-255
  claude), #2506 (258-259 claude), #2508 (256-257 claude). All cross-family Gemini-Pro reviewed; review
  nits applied + VESUM/web-verified before merge.
- **Phase 3 registration: DONE.** curriculum.yaml `levels.bio.modules` went 180 → 310; the new
  181–310 are position==sequence aligned. `validate_plan_ordering.py` is NOT in CI (advisory).
- **GitHub hygiene DONE (2026-06-01):** closed 12 completed issues #2318–2329 (Phase 1 research, Phase 2
  plans, Phase 3 registration) with evidence; updated epic #2309. Open bio issues now = only unfinished
  work: Phase-4 wikis #2330–2335, Phase-5 quality #2336–2338, cross-track followups #2347/2348/2353.
  (#2513 CLOSED this session; #2526 = lit-track slug follow-up spun off.)

## ✅ #2513 COMPLETE (2026-06-01, later session) — all 9 Kulish-content-dup plans rebuilt + merged
**DONE predicate MET:** `validate_plan_ordering.py` on fresh `origin/main` @ `729f18d651` → **0 bio errors**
(was 23): `Track: bio (310 modules) — ✅ All 310 modules verified`. Issue **#2513 CLOSED**. No file carries
`slug: mykola-kulish` except the real `mykola-kulish.yaml`.
- **Part 1 (11 metadata defects):** #2514 (merged earlier).
- **Part 2 (9 Kulish content-dups, this session):** each rebuilt (research dossier + plan mirroring the
  `mykhailo-drai-khmara` exemplar), DeepSeek-pro cross-family reviewed, `connects_to` corrected, merged:
  Зеров bio-092 #2517 · Слісаренко bio-093 #2518 · Петрицький bio-103 #2516 · Йогансен bio-105 #2519 ·
  Фальківський bio-110 #2520 · Плужник bio-111 #2521 · Косинка bio-112 #2525 · Підмогильний bio-115 #2523 ·
  Шкурупій bio-116 #2524.
- **Spun-off follow-up #2526:** 8 `lit`-track slug-mismatch errors still block promoting
  `validate_plan_ordering.py` to a BLOCKING CI check (mechanism-point-3) — out of bio scope, for lit/orchestrator.

## ▶ KEY CORRECTION (2026-06-01) — ihor-kalynets is REALLY dead; prior "fabrication" finding was WRONG
- The previous handoff claimed **cursor "FABRICATED a death date for ihor-kalynets (250); he is ALIVE
  (b.1939)"** and used it as the headline reason for the cursor→claude/codex writer switch. **That claim
  is FALSE.** Ihor Kalynets **really died 28 June 2025 in Lviv, aged 85** (web-verified: RBC-Ukraine,
  Hromadske, Detector Media, Radio Svoboda, ZAXID, Babel, Glavcom, Fakty + uk.wikipedia; announced by his
  daughter Dzvinka Kalynets-Mamchur). The dossier `docs/research/bio/ihor-kalynets.md` correctly records
  the death (ESU updated + KHPG memorial). Cursor wrote a TRUE fact; the rejecting driver pattern-matched
  it to the death-on-living failure mode without web-checking. **Lesson:** before rejecting a "death on a
  living person" as fabrication, WEB-VERIFY (recent deaths post-date older reference works). The rebuilt
  bio-250 plan (#2505) records the real 2025-06-28 death with an `[!epistemic-humility]` note. The
  writer-switch still stands on cursor's OTHER real defects (unparseable YAML, Russianisms, editorial leaks).

## ▶ THE PROVEN PIPELINE (what worked this session — replicate)
WRITER = claude-tools / codex (NOT cursor for bio) → driver deterministic gate → REVIEWER = Gemini Pro
(cross-family, via `ab ask-gemini --task-id review-bio-NNN --model gemini-3.1-pro-preview --review
--stdout-only --no-github --output-path <f> - < <prompt>`; INLINE the plan YAML into the review prompt —
do NOT rely on Gemini file-reads) → driver VESUM/web-verifies each FIX (reject false positives!) →
driver applies fixes deterministically → CI green (blocking; `review / review` = advisory) → driver MERGES.
- **Driver gate (deterministic):** strict key-set == exemplar `mykhailo-drai-khmara.yaml`; config gate
  (wt=5200, outline [400,1000,1200,1600,1000]); 7 vocab; 4-6 activities w/ `after_section` matching a real
  section; module/sequence; **mixed-script scan EXCLUDING URLs** (uk.wikipedia.org paths legitimately mix
  Latin domain + Cyrillic title — do NOT flag those); russianism scan.
- **#M-4 wins this session:** (1) Gemini false-positively "fixed" «арешт»→«арешт» claiming it read «арест»
  — byte-check (`xxd`: ш=d188 not с=d181) refuted it, no change applied. (2) Verified term→строк (SUM:
  «відсидів строк»), суперлатив→твердження (Anglicism), Огладів→Оглядів (place name, web-verified) BEFORE
  applying. Always verify a reviewer's fix before applying it.
- **Dispatch:** `delegate.py dispatch --agent {claude|codex} --task-id bio-blk5-NNN-MMM --prompt-file <f>
  --mode danger [--model gpt-5.5] --effort xhigh --worktree --base main`. Cancel a runaway with
  `delegate.py cancel <task-id>` (positional). Watch via Monitor poll-loop on `/api/delegate/active`.
- **#2513 session add-ons (2026-06-01, replicate for any future bio batch):**
  - **REVIEWER actually used = DeepSeek-pro** (NOT Gemini): `delegate.py dispatch --agent deepseek
    --model deepseek-v4-pro --mode read-only --initial-response-timeout 900 --silence-timeout 3600`.
    INLINE all dossiers+plans into ONE prompt; ask for a per-figure `SHIP/FIX-BEFORE-MERGE/BLOCK` table.
    It ran `verify_words` + `check_russian_shadow` + `query_cefr_level` + `verify_source_attribution`
    (re-verified primary quotes!) + `test -e` on connects_to. 9/9 confirmed factually sound + VESUM-clean.
  - **RAISE `--initial-response-timeout 900`** — the default `DEFAULT_INITIAL_RESPONSE_TIMEOUT_S=180`
    (scripts/delegate.py) kills DeepSeek mid-MCP-work BEFORE first stdout (our first review died at exactly
    180.6s). Same failure CLASS as the #2454 gemini SIGTERM — a startup-probe kill, not silence-timeout.
  - **`connects_to` convention = BARE slugs** (no `bio-`/`hist-`/`lit-` prefix; must equal the target's
    `slug:` field). EVERY claude rebuild emitted prefixed and/or GHOST targets (oleksa-vlyzko, mykola-bazhan,
    maksym-rylskyi, sandarmoh — none exist as plans). Driver fix: de-prefix + repoint ghosts to a real peer,
    `glob curriculum/.../*/<bare>.yaml` to confirm each resolves, before merge. **Bake the bare-slug + "only
    reference plans that already exist" rule into the writer brief so it stops recurring.** (Forward-refs are
    not CI-gated, but cross-family review flags them FIX-BEFORE-MERGE.)

## ▶ SEMINAR QUALITY STANDARD + EXISTING-180 AUDIT (Codex 2026-06-01, user-endorsed)
**Seminars are source-first, stricter than core.** BIO/HIST/ISTORIO/LIT/OES/RUTH are NOT generic language
lessons — every module needs **source pack · factual checks · decolonization checks · citation discipline ·
domain review** (Codex framing). **BIO stays Claude-owned** — keep that boundary. Other seminars are
DEFERRED (bio only for now).

**NEW WORKSTREAM — audit the EXISTING 180 bio plans + their 180 wikis to this standard.** They predate the
epic and carry real debt — this session proved it: #2513 (9 original plans were Kulish content-duplicates),
#2451 (4 short dossiers), #2528 (постум/арест/Latin-homoglyph defects in ~10 mostly-original-180 plans). The
180 wikis have the same exposure (ghost sources, decolonization gaps, citation drift). Execute EFFICIENTLY —
do NOT blind-LLM-review 360 artifacts:
1. **Deterministic linter FIRST (= NEXT ACTIONS #3, now the keystone):** russianisms/calques + Latin-in-Cyrillic
   (excl. URLs/acronyms like X-променів/STEM/IEU) + ghost `connects_to` (bare-slug resolution) + **ghost sources**
   (`references[].path` URL-slug/title naming a DIFFERENT person than the figure — the real seminar failure mode)
   + word-floor (≥1200 dossier / config word_target) + citation resolution. Run across ALL 310 plans + 180 wikis
   → triage list.
2. **Triage:** mechanical defects → fix deterministically (like #2528); substantive → source-first cross-review.
3. **Source-first cross-review** (DeepSeek of record; grok UNDER VALIDATION) on flagged artifacts + a calibration
   sample, scored against the dossier as ground truth. Fix by severity. Anti-fabrication (#M-4) over count.

## ▶ GROK EVAL (2026-06-01) — PROMISING, UNDER VALIDATION, DO NOT TRUST YET (user: "test more")
New standalone **grok CLI** (`~/.local/bin/grok` v0.2.16, logged in via grok.com) exposes
`grok-composer-2.5-fast` (default) + `grok-build` (NO grok-4.3 in this CLI). `sources` MCP is WIRED into
`~/.grok/config.toml` (34 tools, handshake OK). One-shot reviewer use works TODAY (read-only, no delegate
adapter needed): `grok --prompt-file <f> -m grok-composer-2.5-fast --always-approve`. Tests so far: both models
6/6 on a deterministic VESUM micro-test with raw-quote #M-4 discipline; grok-build self-initiated a follow-up
verify; grok-composer's wave-1 head-to-head **beat DeepSeek once** (it `git ls-tree`-verified `maksym-rylskyi.yaml`
exists on origin/main → DeepSeek had false-positived it a ghost). **STILL: keep DeepSeek-pro hermes as reviewer
OF RECORD; validate grok over more plans first.** WRITER use needs the delegate grok adapter built (currently a
stub `agent_runtime/adapters/grok.py`; registry only knows grok-4.3). The `maksym-rylskyi` finding means zerov's
merged `connects_to` uses `mykhailo-drai-khmara` (also valid, fellow Neoclassicist) — NOT a defect, no fix.

## ▶ GIT/GITHUB HYGIENE (2026-06-01, done) — bio lane clean
Deleted 17 stale bio local branches (merged/backed-up/closed); removed obsolete scratch
`phase2-word-target-defects-2026-05-31.txt`; pruned obsolete `drai-khmara-ref-title` worktree. Bio dirty tree
clean · 0 bio worktrees · 0 open bio PRs. **PENDING user decision:** 4 `cursor/bio-rebuild-block{G7,I1,I2,J2}`
local branches each have 2 local-only (unpushed) commits — the rejected cursor word-target batch, superseded by
the merged plans; NOT deleted (#M-10 — never destroy unmerged work without the nod). Drop on user OK.

## ▶ NEXT ACTIONS (in order)
0. **FIX THE GEMINI DISPATCH BUG #2454 FIRST (user 2026-06-01).** `delegate.py dispatch --agent gemini`
   gets killed by SIGTERM at ~87s with zero output (codex unaffected). Likely root cause: the delegate
   silence-timeout watchdog kills gemini-cli when it goes silent during real work (codex emits liveness,
   gemini doesn't). Investigate `scripts/delegate.py` + `scripts/agent_runtime/` `--silence-timeout` /
   `--initial-response-timeout` handling for the gemini adapter — either raise/disable silence-timeout for
   gemini, or watch gemini's session JSONL (`~/.gemini/...`) for liveness like codex's rollout JSONL. Add a
   regression test. NOTE: delegate.py is shared infra (orchestrator-adjacent) — coordinate / it may be a
   non-bio PR. Fixing this lets the claude-writer→**gemini-reviewer** path work via dispatch; until then
   gemini stays on `ab ask-gemini` ONLY. (Reviewer default remains DeepSeek regardless — see banner.)
1. ✅ **Landing page 180→310: DONE (#2527).** `starlight/src/content/docs/bio/index.mdx` now has 310 cards
   (nums 1..310 contiguous, node-eval validated), subtitle/`totalPlanned`=310. Cards generated
   deterministically from each plan's `sequence`/`title`/`slug`.
2. **Phase-5 cleanup — the #2513 slug/metadata bugs are DONE; only language defects remain:**
   - ✅ DONE: 9 `mykola-kulish` content-dups rebuilt (this session, #2516–2525); 11 legacy
     `level: C1-BIO`/`module: c1-bio-*`/zero-pad/`petro-veskliaov` metadata defects (#2514).
     `validate_plan_ordering.py` → **0 bio errors**.
   - ✅ DONE (#2528, VESUM-verified each fix): постумно/постумне→посмертно/посмертне (mosendz, domontovych,
     liaturynska); арест→арешт / арести→арешти / арестував→заарештував / арестовано→заарештовано (voronyi,
     budka, domontovych, pritsak); Latin-homoglyphs→Cyrillic (`Cлово` mikhnovskyi×2, `риcа` huzar,
     `Оспiщев` lypynskyi, `мистецтвoм` kholodna). Mixed-script re-scan + validate_plan_config clean.
   - STILL PENDING (Phase-5 editorial polish — JUDGMENT calls, not deterministic): English/meta leaking into
     UA content — `LIT-модулі` (domontovych), `L2-студентам` (myroslav-irchan), `hindsight-осуду`
     (antin-krushelnytskyi). NOTE: intentional Latin (`X-променів`, `STEM`, `IEU`, `Ems`, URLs) is FINE — do
     NOT "fix" those.
3. **✅ Deterministic pre-review linter — SHIPPED** (`scripts/validate/lint_seminar_quality.py`, branch
   `bio/seminar-quality-linter`, this PR; 21 hermetic tests). Covers russianism/calque list (арешт-not-арест,
   посмертно-not-постум, коерція, голодовка, інакомисляч [person-form only — `інакомислення` is VESUM-codified,
   NOT flagged], власті, prison-sense термін via imprisonment collocation) + Latin-in-Cyrillic (homoglyph
   intra-word AND lazy abbreviations like LIT-/L2-/hindsight-, allowlisting X-променів/STEM/IEU/Ems/Roman
   numerals/URLs) + `Дебат` singular. NOT a ghost-`connects_to` check (already covered by
   `validate_plan_ordering.py`). Precision-first: HIGH = gating set, advisory = review-list, **systemic rules
   collapse** to one line (the «Дебат N:» template = 540 hits / 190 plans). Run:
   `.venv/bin/python scripts/validate/lint_seminar_quality.py --track bio [--severity high] [--json]`.
   **TRIAGE on origin/main (all VESUM/context-verified, zero false positives):** 4 HIGH + 2 advisory, ALL in the
   NEW 181–310 plans (original 180 clean of these classes):
   `viktor-domontovych` (bio-211) «LIT-модулі» · `myroslav-irchan` (bio-190) «L2-студентам» ·
   `antin-krushelnytskyi` (bio-191) «hindsight-осуду» · `vasyl-barvinskyi` (bio-290) «Арест»→Арешт ·
   `kateryna-zarytska` (bio-284) prison-sense «термін»→строк (advisory) · `vasyl-barka` «властями»→владою/органами
   влади (advisory). **NEXT: fix these 6 in a small cross-reviewed (DeepSeek) content PR, then this linter can be
   promoted to a BLOCKING CI gate (currently manual/pre-review only — it would redden main until they are fixed).**
   The «Дебат» singular systemic finding is a separate template/stylistic call for the orchestrator. (PR-2539
   review by gemini added recall for prefixed «заарестовано» + власть-plurals — adopted after FP-verification.)
4. **Phase 4 — WIKI ARTICLES (writer-fleet job, ~130 articles for bio-181..310, ~285K words):**
   Pipeline = `scripts/wiki/compile.py --track bio --slug <slug> --writer claude [--review]`
   (writer options are only `{gemini, claude, gpt-5.5}`; gpt-5.5=codex=PAUSED; **use `--writer claude`** —
   strong primary, extra Claude resources). **Run a CLAUDE writer fleet** (parallel per-slug, or
   `--all --track bio --limit N`), capped at the in-flight dispatch limit; Monitor on `/api/delegate/active`.
   The original 180 bio wikis are 100% done (~400K w); only 181..310 remain.
   **✅ PHASE-4 PREREQUISITE — DISCOVERY BUG FIXED (PR `bio/fix-wiki-discovery`, this batch).**
   Was: wiki discovery reads `curriculum/l2-uk-en/bio/discovery/*.yaml` (180 files = the original 180); the 130
   new figures (181..310) had NO discovery file → `compile.py --track bio --list` showed **180, not 310**.
   ROOT CAUSE: `scripts/wiki/sources.py::list_discovery_slugs` returned early when the discovery dir already had
   ANY .yaml (`if slugs: return slugs`), never reconciling newly-added plans. FIX (shipped): `list_discovery_slugs`
   now ALWAYS runs `_auto_generate_discovery` (which skips per-file-if-exists, so existing files are untouched and
   only the missing ones are created), then returns the full glob. Verified: `--list` now prints **310 modules**
   and surfaces mykhail-semenko / nariman-dzhelial / dmytro-chyzhevskyi. Hermetic regression test added
   (`tests/test_wiki_sources.py::test_list_discovery_slugs_reconciles_new_plans`); full wiki suite 75 passed.
   NOTE: the auto-generated stubs are EMPTY fallbacks (`rag_chunks: []`, `warning: "Auto-generated from plan"`) —
   NOT committed in the fix PR; they regenerate on compile. Real per-figure discovery data (RAG chunks) for
   181..310 is a Phase-4 sub-step (run the discovery pipeline, then commit those). THEN run the claude wiki fleet
   (`--all --track bio --limit N` or per-slug). Cross-review each article with **DeepSeek** (claude writer →
   non-claude reviewer); Gemini only if a fresh key is at hand.
5. **Phase 5 quality:** decolonization pass (DeepSeek-pro hermes), cross-track `connects_to` verification
   (hist-/lit-/istorio- forward-refs not CI-gated).

## ▶ LOOSE ENDS
- `drai-khmara-ref-title` worktree loose end: **RESOLVED/obsolete** — the ref-title fix is already on main
  (exemplar has all 5 reference titles) and that worktree's commit `af86e1691e` adds a junk `.bak`; do NOT
  PR it. Prune the worktree if it lingers.
- `connects_to` cross-track targets (`hist-/lit-/istorio-`) are forward-refs; not CI-gated; Phase-5 concern.
- Capacity (user 2026-06-01): user authorized **3× claude writers** for the final batch; weekly Claude only
  ~61% used + Anthropic doubled limits to mid-July. claude-tools is an excellent bio plan writer (handled
  the living bohdan-horyn and the NPOV-sensitive yurii-shukhevych with exemplary discipline).

## ▶ EXEMPLAR + REFERENCE
- Plan exemplar (mirror key set, 19 keys): `curriculum/l2-uk-en/plans/bio/mykhailo-drai-khmara.yaml` (bio-183).
- Dossiers: `docs/research/bio/{slug}.md` (Phase-1 complete). Allocation SSOT:
  `docs/bio-epic/phase-2-sequence-allocation.yaml` (seq 181–310; authoritative seq→slug).
- Config gate: `scripts/validate/validate_plan_config.py bio/<slug>` (CI "Curriculum Plans").

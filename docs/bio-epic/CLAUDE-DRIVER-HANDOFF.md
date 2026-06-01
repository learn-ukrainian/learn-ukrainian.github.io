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
> **⛔ NO CODEX FOR BIO (user 2026-06-01) — STANDING UNTIL THE USER LIFTS IT.** All codex quota is
> reserved for building A1. Do **NOT** `delegate.py dispatch --agent codex` (or `ab ask-codex`) for any
> bio work until the user explicitly says codex is available again. **This is fully manageable without
> codex** — proof: 8 of this session's 12 plans (252–259) were claude-tools-written, zero codex.
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

*Last updated: 2026-06-01 (late). **Phase 2 plan build COMPLETE: main has all 130 new plans, 181→310
contiguous (310 bio plans total).** Phase 3 registration DONE in this PR (curriculum.yaml bio = 310
modules, 181→310 position==sequence). **UPDATE (2026-06-01, later): #2513 fully CLOSED — all 9
Kulish-content-dup rebuilds merged (#2516–2525); `validate_plan_ordering.py` → 0 bio errors. 0 dispatches
in flight. Next bio work = NEXT ACTIONS #1 (landing page 180→310) + #3 (pre-review linter) + #4 (Phase-4 wikis).**
**UPDATE (2026-06-01, session 3): Phase-4 PREREQUISITE DONE — wiki discovery bug fixed (branch
`bio/fix-wiki-discovery`, this PR): `compile.py --track bio --list` now surfaces all 310 (was 180);
`scripts/wiki/sources.py::list_discovery_slugs` reconciles instead of short-circuiting; hermetic regression
test added; wiki suite 75 passed. NEXT ACTION on resume = run the Phase-4 discovery pipeline for 181..310,
then the CLAUDE wiki writer fleet (DeepSeek cross-review). Remaining keystone NEXT ACTIONS #3 (seminar-quality
pre-review linter for #2535) still open. 0 dispatches in flight.** *

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
3. **Deterministic pre-review linter** (`scripts/validate/...`): russianism/calque list (арест, постум,
   коерція, голодовка, інакомисляч, місцеві власті, термін-for-sentence) + mixed Latin-in-Cyrillic
   (excluding URLs) + `Дебат` singular. Run BEFORE Gemini to cut review rounds and catch the defects above.
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

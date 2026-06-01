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

*Last updated: 2026-06-01 (late). **Phase 2 plan build COMPLETE: main has all 130 new plans, 181→310
contiguous (310 bio plans total).** Phase 3 registration DONE in this PR (curriculum.yaml bio = 310
modules, 181→310 position==sequence). 0 dispatches in flight at handoff time.*

## ▶ CURRENT STATE (2026-06-01)
- **origin/main: 310 bio plans, 181→310 contiguous (130/130). Phase 2 plan-writing is FINISHED.**
- **248–259 gap CLOSED this session** (the last gap). Merges: #2505 (248-251 codex), #2507 (252-255
  claude), #2506 (258-259 claude), #2508 (256-257 claude). All cross-family Gemini-Pro reviewed; review
  nits applied + VESUM/web-verified before merge.
- **Phase 3 registration: DONE (this PR).** curriculum.yaml `levels.bio.modules` went 180 → 310; the new
  181–310 are position==sequence aligned. `validate_plan_ordering.py` is NOT in CI (advisory).

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

## ▶ NEXT ACTIONS (in order)
1. **Landing page 180→310:** `starlight/src/content/docs/bio/index.mdx` — hardcoded array of
   `{num,title,slug,status}` cards (last num:180 anatolii-dimarov). Append 181..310 from curriculum.yaml +
   plan titles. (Not done this session.)
2. **Phase-5 cleanup of PRE-EXISTING defects (NOT introduced this epic; surfaced by
   `validate_plan_ordering.py` — 23 bio errors, all in the original 1–180 plans):**
   - **`mykola-kulish` slug duplication:** ~8 Executed-Renaissance plan files (anatol-petrytskyi,
     dmytro-falkivskyi, heo-shkurupii, hryhorii-kosynka, maik-yohansen, mykola-zerov, oleksa-slisarenko,
     valerian-pidmohylnyi) carry `slug: mykola-kulish` inside the YAML (filename≠slug). Real data bug — fix
     each plan's `slug`/`module`/`sequence` to match its file.
   - Legacy `level: C1-BIO` / `module: c1-bio-*` on hryhoriy-skovoroda, lev-danylovych, volodymyr-velykii.
   - Zero-padding: `bio-04`→`bio-004` etc. (kniaz-yaroslav-mudryi, knyazhna-anna-yaroslavna, olha-kobylianska).
   - `petro-veskliaov.yaml` slug=`petro-veskliarov` (filename typo vs slug).
   - Pre-existing language defects from earlier handoff still on main: `постумно` (domontovych, mosendz,
     liaturynska), `арест` (voronyi), Latin-in-Cyrillic (`Cлово` mikhnovskyi, `риcа` huzar, `Оспiщев`
     lypynskyi, `мистецтвoм` kholodna). Sweep with the linter below.
3. **Deterministic pre-review linter** (`scripts/validate/...`): russianism/calque list (арест, постум,
   коерція, голодовка, інакомисляч, місцеві власті, термін-for-sentence) + mixed Latin-in-Cyrillic
   (excluding URLs) + `Дебат` singular. Run BEFORE Gemini to cut review rounds and catch the defects above.
4. **Phases 4–5 per epic #2309:** wiki articles (Gemini), decolonization quality pass (DeepSeek-pro
   hermes), cross-track `connects_to` verification (hist-/lit-/istorio- forward-refs not CI-gated).

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

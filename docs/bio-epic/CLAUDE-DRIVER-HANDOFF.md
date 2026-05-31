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
> (incl. Phase-3 `curriculum.yaml`). **HARD CONDITION:** every bio PR first passes review from a
> *different proven reviewer family than the writer*. **HUMAN-NOD WAIVED** — the gate is ACCURACY +
> honest decolonized NPOV verified by cross-family review, NOT political sign-off. Once review=ship +
> CI green + scope-clean → MERGE (OUN/UPA, clergy, war-dead included; tell the truth in every direction).
> Escalate to the human ONLY on a GENUINE defect (fabrication / ghost-source / real NPOV failure) and
> fix-forward. Non-bio main = orchestrator-only.

*Last updated: 2026-06-01. Phase 2 plan build ~96% done: main has **298 bio plans, contiguous 181→247**
+ slice 260→310. **Only 248–259 (12 plans) remain to build**, then Phase 3 registration. 0 dispatches in
flight at handoff time; no temp bio worktrees except this handoff branch.*

## ▶ CURRENT STATE (2026-06-01)

- **origin/main:** 298 bio plans. Contiguous **181→247**. Single remaining gap: **248–259** (12 plans).
  Slice **260→310** fully merged. Phase 3 registration is BLOCKED only until 248–259 lands (registration
  must be contiguous — see Phase 3).
- **Merged this session (23 plans):** gap-fill 220–224 (#2498), 229–232 (#2496), then 233–237 (#2499),
  238–242 (#2500), 243–247 (#2501). All cross-family reviewed by Gemini Pro, all fixes VESUM-verified.

## ▶ NEXT ACTIONS (in order)
1. **Build 248–259** (12 plans, ~2-3 cursor batches) via the PROVEN PIPELINE below. Slugs (allocation
   SSOT `docs/bio-epic/phase-2-sequence-allocation.yaml`):
   248 leonid-pliushch · 249 nina-strokata · 250 ihor-kalynets · 251 iryna-kalynets ·
   252 nadiia-svitlychna · 253 sviatoslav-karavanskyi · 254 mykhailo-horyn · 255 bohdan-horyn ·
   256 oksana-meshko · 257 yurii-shukhevych · 258 danylo-shumuk · 259 ivan-kandyba.
   (Dissidents/Helsinki/political-prisoners; yurii-shukhevych = son of UPA cmdr Roman Shukhevych —
   handle NPOV carefully. All 12 dossiers confirmed present on main.)
2. **Phase 3 registration** (once 181→310 contiguous): append new slugs to `levels.bio.modules` in
   `curriculum/l2-uk-en/curriculum.yaml` in sequence order (currently 180 entries, last
   `anatolii-dimarov`). The list is a FLAT ordered slug list; position i (1-indexed) MUST equal each
   plan's `sequence` field — `scripts/validate/validate_plan_ordering.py` enforces this, so NO GAPS
   (that's why registration waits for contiguity). Verify with that script. NOT in CI (orphan = warning),
   so it's a follow-on, not a merge blocker.
3. **Landing page 180→310:** `starlight/src/content/docs/bio/index.mdx` — hardcoded array of
   `{num,title,slug,status}` cards (last num:180 anatolii-dimarov). Append 181..310 from curriculum.yaml
   + plan titles.
4. **Add deterministic linter gate** (see FINDINGS) + Phase-5 cleanup of pre-existing defects.

## ▶ THE PROVEN PIPELINE (replicate exactly — this is what works)
WRITER = cursor (`--model auto`) → driver gate → REVIEWER = Gemini Pro (cross-family) → driver applies
VESUM-verified fixes → driver MERGES.
1. **Brief** (fresh heredoc per batch): `/tmp/brief-bio-blk5-NNN-MMM.md`. Include #M-4 preamble; the
   explicit slug→seq table; "MIRROR exemplar `curriculum/l2-uk-en/plans/bio/mykhailo-drai-khmara.yaml`";
   HARD constraints (wt=5200, content_outline [400,1000,1200,1600,1000], 5 sections, 7 vocab, 4-6
   activities with real `after_section` anchors, level/phase BIO, cefr_min C1, pedagogy CBI); LANGUAGE
   HYGIENE list (write `арешт` not «арест», `посмертний` not «постумний», `примус` not «коерція»,
   `довічне заслання` not «вічне», `Дебати` not «Дебат», `голодування` not «голодовка», `інакодумець`
   not «інакомисляч», NO Latin-in-Cyrillic, "dialect ≠ language"); "delete any generator scripts before
   commit"; "you are ALREADY in the worktree, do NOT git worktree add"; numbered steps (write→validate→
   `git add` ONLY the N plans→`commit --no-verify`→`push HEAD:cursor/bio-blk5-NNN-MMM`→`gh pr create`→
   NO auto-merge).
2. **Fire:** `.venv/bin/python scripts/delegate.py dispatch --agent cursor --task-id bio-blk5-NNN-MMM
   --prompt-file <brief> --mode danger --model auto --worktree --base main`.
3. **Watch:** Bash `run_in_background` until the task leaves `/api/delegate/active` (cursor marks
   status=`failed` with returncode 0 even on success — it writes+commits but does NOT push/PR; that's
   normal, driver finalizes).
4. **Driver gate** (deterministic, on the worktree files): strict key-set == exemplar; config gate
   (wt≥5000 AND outline sum≥wt); mixed-script scan (Latin letter inside a Cyrillic word — already caught
   `вітражa`); scope = exactly N `A` plan files (no stray `scripts/` generators).
5. **Finalize:** `git push -u origin HEAD:<branch>` + `gh pr create` (cursor usually didn't).
6. **Cross-family review:** `ab ask-gemini --task-id review-bio-NNN-MMM --model gemini-3.1-pro-preview
   --review --stdout-only - < <review-brief>` run in background (NOT `delegate.py dispatch --agent gemini`
   — that hits the #2454 SIGTERM-at-87s bug). Review brief points Gemini at the worktree plan paths;
   dimensions = factual accuracy / decolonized NPOV / source integrity / language hygiene.
7. **Apply fixes:** for each Gemini FIX/BLOCK, VESUM-verify (`mcp__sources__verify_words`) BEFORE applying
   (#M-4 — never apply an unverified "fix"); verify names against the DOSSIER (`docs/research/bio/{slug}.md`).
   Apply deterministically (python str.replace with per-string assert), re-scan, `commit --no-verify` +
   push to update the PR. NOTE: watch case/gender agreement (e.g. `повоєнну коерцію`→`повоєнний примус`);
   line-folded YAML scalars need the embedded `\n    ` in the match.
8. **Merge:** when blocking CI green (`Curriculum Plans`+`Test (pytest)`+`Activities & Vocab`+`Content
   Gate`s pass; `review / review` = advisory, non-blocking; state UNSTABLE is fine if only that fails) AND
   Gemini ship AND scope clean → `gh pr merge N --squash --delete-branch`. Then `git worktree remove
   --force <wt>` + `git branch -D <branch>` + `git worktree prune`. (Local branch delete fails until the
   worktree is removed — remove worktree first.)

## ▶ KEY FINDINGS (2026-06-01 — read before building 248–259)
- **Cursor plan quality is INCONSISTENT.** 233–237 was clean (minor calques); 238–242 + 243–247 needed
  3–12 fixes EACH: Russianisms (`голодовка`, `арест`, `місцевих властей`), calques/hallucinations
  (`коерція`, `постумний`, `інакомисляч`, `Дебат` singular ×5, `поколінних ящиків`, `в лінії`), case
  errors, a misspelled name (`Бадзо`→`Бадзьо`), mixed-script (`вітражa`, `постumне`), and a
  **decolonization error** (`гуцульська мова`→`гуцульський говір` — Hutsul is a dialect, not a language;
  "language" framing = imperial-division). One plan (shabatura) was also thin with placeholder activity
  focuses. **The Gemini Pro cross-family review (user's call) is ESSENTIAL — it catches what cursor and a
  same-family reviewer miss. Do NOT skip it. Do NOT self-review claude-written plans.**
- **TODO — deterministic pre-review linter** (`scripts/validate/...` or a gate): flag russianisms/calques
  from a known list + mixed Latin/Cyrillic-in-word + `Дебат` singular, BEFORE Gemini. Recurring offenders
  are already added to the cursor brief. This same linter catches the **pre-existing defects already on
  main**: `постумно` (domontovych, mosendz, liaturynska), `арест` (voronyi), Latin-in-Cyrillic (`Cлово`
  mikhnovskyi, `риcа` huzar, `Оспiщев` lypynskyi, `мистецтвoм` kholodna). → Phase-5 cleanup pass.
- **pyenv noise FIXED** (env, not bio): `.bashrc` `pyenv init - bash` ran a rehash on every shell init,
  contending on the `~/.pyenv/shims/.pyenv-shim` mutex under concurrent shells → 60s-timeout errors. Fix:
  `--no-rehash` on the init line + cleared the stale lock. Verified. (If it returns: `rm -f
  ~/.pyenv/shims/.pyenv-shim`.)

## ▶ LOOSE ENDS
- `.worktrees/fix-bio-drai-khmara-ref-title` — committed fix `af86e1691e` (adds missing ref title +
  drops a `.bak`) UNMERGED. PR it + merge.
- **carneckyj ghost-source: RESOLVED** on main (Phase-5 sweep clean). Only residual: `zynovii-kovalyk.md`
  dossier line 97 still cites the `_carneckyj_sp.html` combined page while its plan uses the generic
  group page — low-sev (Kovalyk IS on that page); normalize for consistency if touching it.
- `connects_to` cross-track targets (`hist-/lit-/istorio-`) don't resolve (forward-refs); NOT CI-gated;
  Phase-5 cross-track-verify concern.
- agy/Opus-4.6-high review bakeoff still pending user backend flip.

## ▶ EXEMPLAR + REFERENCE
- Plan exemplar (mirror key set): `curriculum/l2-uk-en/plans/bio/mykhailo-drai-khmara.yaml` (bio-183).
- Dossiers: `docs/research/bio/{slug}.md` (Phase-1 complete, all present). Allocation SSOT:
  `docs/bio-epic/phase-2-sequence-allocation.yaml` (130 new plans, seq 181–310).
- Capacity (user 2026-05-31/06-01): 1 EXTRA Claude dispatch slot OK (weekly only ~61% used). Gemini Pro
  endorsed as cross-family reviewer. Writer = cursor (writer swap from gemini, user 2026-05-31).

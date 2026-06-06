# Folk Track — Claude Driver Handoff (MY OWN — not the orchestrator's)

> **Scope/boundaries (user 2026-06-06):** User redirected Claude from the bio epic to **re-research +
> rebuild the FOLK track first** ("leave bio resting, test the system with folk"). Codex/GPT is the
> orchestrator. Claude does NOT touch `docs/session-state/current.md`. This is Claude's OWN git-tracked
> tracking doc so a fresh Claude folk session resumes without the orchestrator's handoff. Launch with
> `claude --agent curriculum-track-orchestrator`. **Bio rests** (310/310 dossiers safe on main, its
> handoff intact at `docs/bio-epic/CLAUDE-DRIVER-HANDOFF.md`, 0 bio dispatches in flight).
>
> **🚧 GIT DISCIPLINE:** scope git to folk paths (`curriculum/l2-uk-en/plans/folk`,
> `curriculum/l2-uk-en/folk`, `docs/research/folk`, `docs/folk-epic`, `docs/poc`,
> `starlight/src/content/docs/folk`, `wiki/folk`). Never a tree-wide `git status`/main op. If a non-folk
> file surfaces (esp. `docs/session-state/*`), SKIP SILENTLY.
>
> **🌲 WORKTREE-ONLY (HARD, user 2026-06-06 — "you do this every fucking time"):** the main project
> checkout's HEAD STAYS ON `main`. NEVER `git checkout -b` / `git switch` / `git branch -f` /
> `git reset --hard` in the main dir. ALL driver branch work goes in a worktree:
> `git worktree add .worktrees/dispatch/claude/<task> -b claude/<task> origin/main` → `cd` in → work →
> PR → self-merge → `git worktree remove`. A local PreToolUse guard enforces this for Claude
> (`.claude/hooks/guard-main-worktree.sh`); git has no abortable pre-checkout hook, so the guard is
> command-level/per-tool. Dispatched agents are already worktree-forced by `delegate.py`.
>
> **⚖ MERGE POLICY (UPDATED 2026-06-06):** the folk driver **HAS a merge grant**. User: *"every track
> has merge grant otherwise we will have a deadlock."* So: branch → PR → CI-green → **self-merge**
> (review body+diff+CI, `gh pr merge N --squash --delete-branch`; hold only on a BLOCKING CI fail per
> #M-0.5). Still **no direct commits to `main`** — everything routes through a PR; the grant only lifts
> the "don't self-merge" restriction, not the "don't push to main" one. Stage-0 PR #2759 self-merged
> under this grant (commit `abf280f490`).

## ▶▶▶ SESSION 2 HANDOFF (2026-06-06 #2 — FOUNDATION + PILOT SHIPPED) — **RESUME HERE**

### ✅ SHIPPED THIS SESSION (all on `main`, self-merged under the folk grant)
- **Stage-0 foundation** (#2759 `abf280f490`): `phase-folk-queue.md` (42-topic de-imperialized
  queue) · `folk-dossier-schema.md` (10-section contract + multimodal hooks) · `folk-review-rubric.md`
  (corpus-hammer) · `folk-experiential-archetype-spec.md` · `curriculum.yaml` folk **27→42**.
- **Merge grant recorded** (#2762): folk driver self-merges green PRs (still no direct commits to main).
- **SSOT migration 27→42** (#2763 `d44931b2e9`): plans/folk 5 renames + 6 folds→`_archive` + 21 stubs ·
  `compile.py FOLK_DOMAIN_MAP` 42 slugs · `module_archetypes.py` **folk-experiential** registered +
  routed (`resolve("folk")→folk-experiential`, bio unchanged). *(I caught + fixed 2 CI bugs GPT left:
  empty stub `references`, stale domain-map test — finalize pattern below.)*
- **★ PILOT DOSSIER** `kalendarna-obriadovist-zvychai` (#2768 `0722cb4c76`, 51KB / +515): GPT wrote,
  **Claude cross-family corpus-hammer review PASSED** — independently re-ran `verify_quote` on 3 of 7
  fragments (all matched 1.0, exact chunk IDs), confirmed the honest Щедрик do-not-quote (matched
  false 0.5 — corpus has the title, not the lyric), re-checked `check_russian_shadow` (clean),
  §9 decolonization exemplary (Берегиня flagged as modern reconstruction; regional variation surfaced).
  **This is the quality bar for every folk dossier.**

### 🔭 IN-FLIGHT: **NONE.** No dispatches active. main clean. (verify: `curl -s :8765/api/delegate/active`)

### ▶ NEXT ACTIONS (optimal order) — RESUME HERE
1. **Wiki-gen the pilot** (validate dossier→wiki half): `.venv/bin/python scripts/wiki/compile.py
   --writer gpt-5.5 --dossier docs/research/folk/kalendarna-obriadovist-zvychai.md` (domain
   `folk/ritual` exists). Review the wiki against `folk-review-rubric.md`, self-merge.
2. **Drive build-order dossiers 2→6** via the PROVEN LOOP (below): `narodna-kultura-yak-systema` →
   `narodni-viruvannia-mifolohiia-demonolohiia` → `koliadky-shchedrivky` → `rodynna-obriadovist-zvychai`
   → `dumy-nevilnytski-lytsarski`. Full queue: `docs/folk-epic/phase-folk-queue.md`.
3. **After June 8:** Claude content-writing bench lifts → Claude can WRITE dossiers too (cross-family:
   GPT writes → Claude reviews, OR Claude writes → GPT reviews). Until then GPT writes, Claude reviews.

### 🔁 THE PROVEN DOSSIER LOOP (what worked this session — reuse it)
1. Brief = `/tmp/<slug>-brief.md` referencing the 3 specs (schema/rubric/queue-row) + #M-4 preamble +
   corpus-hammer mandate (`verify_quote` every text) + "NO auto-merge". (Pilot brief template:
   the structure in this session's `/tmp/folk-pilot-dossier-brief.md`.)
2. Fire: `delegate.py dispatch --agent codex --task-id folk-dossier-<slug> --prompt-file <brief>
   --mode danger --model gpt-5.5 --effort xhigh --worktree --base main` (NO `--allow-merge`).
3. Watch: background poll-loop on `/api/delegate/active` for the task id (it notifies on exit). NB the
   dispatch may end `rc=-9` (silence-timeout SIGKILL) AFTER it committed + opened its PR — check
   `gh pr list --head codex/<branch>`, don't assume failure (#M-8).
4. **REVIEW (mandatory, Claude's lane — analysis, allowed during bench):** read the dossier CONTENT;
   **independently re-run `verify_quote`** on a sample of §4 texts (don't trust self-report, #M-11);
   spot-check `check_russian_shadow`; read §9 decolonization. SHIP only if quote-integrity +
   decolonization hold.
5. If small CI/reconciliation bugs: fix IN THE WORKTREE; if it's a plan-file edit blocked by the
   `version not incremented` gate, `git reset --soft HEAD~1` + recommit so files are "new vs parent"
   (the gate exempts new files) → `git push --force-with-lease`.
6. Self-merge (`gh pr merge N --squash --delete-branch`) → `git worktree remove --force <path>`.

### ⚠ CARRY-FORWARD GAPS / NOTES
- **SigLIP `search_images` is DEFERRED for this track** ("will be available for l2-uk-direct") → folk
  dossiers can't yet capture image `chunk_id`s; symbolic-decode visuals are pending. Don't fabricate
  IDs (pilot recorded the raw tool failure honestly). Revisit when image search is wired for l2-uk-en.
- New plan stubs carry a placeholder `references` (title + "pending dossier" note) to pass
  `validate_plan`; real corpus sources get added when each topic's dossier is written.

---

## ▶▶▶ SESSION 1 HANDOFF (2026-06-06, FOLK SCOPE + TAXONOMY + DESIGN ARCHETYPES) — reference

### ✅ DECISIONS LOCKED THIS SESSION (all user-confirmed)
1. **Track = FOLK, broad scope.** Not oral-folklore-only — **broad folk CULTURE** (oral genres + music +
   dance + material/visual culture + ritual customs). User rationale: without it you can't understand the
   uniqueness of e.g. the opera «Запорожець за Дунаєм».
2. **Register = C1+.** (Folk currently registered as C1 in curriculum.yaml.)
3. **Claude's deliverable boundary = research → dossier → wiki. NO modules.** GPT builds the modules +
   "final experience" and is trending to orchestrator. Claude designs the pages; GPT builds against them.
4. **Writers/reviewers for Ukrainian CULTURE = Claude + GPT only. NO DeepSeek** (user: deepseek lacks the
   intrinsic Ukrainian-culture knowledge to catch subtle framing errors; its corpus-tool use was fine but
   that's not the risk for culture). Cross-family pair = GPT↔Claude.
5. **⛔ Claude BENCHED for content WRITING until June 8 morning reset** (user, quota). Design/analysis/
   orchestration by Claude is fine; only Ukrainian-content WRITING is benched. Sequencing works out: the
   gap-audit + design need no writer; first dossier starts when Claude returns (or GPT writes earlier).
6. **Reviewer MUST hammer the corpus** — `verify_quote` on every folk text (duma/song lyrics must be exact,
   the folk analogue of the bio quote-integrity gate), + search_literary / search_grinchenko_1907 /
   search_heritage / check_russian_shadow / query_cefr_level.
7. **No YT resources for folk** — the dossier is the SOLE knowledge layer, so dossier depth is everything.

### 📋 FOLK TAXONOMY — 27 existing + 10 broad-scope additions (GPT-cross-checked, bridge msg #1148)
**Existing 27** (oral genres): bohatyri-illiya-dobrynia, bylyny-kyivskoho-tsyklu, bylyny-sotsialni,
zastavy-bohatyrski, dumy-{lytsarski,nevilnytski,sotsialno-pobutovi}, pokhodzhennia-dum, kobzarstvo-fenomen,
koliadky-shchedrivky, vesnianky-hayivky, kupalski-pisni, rusalni-pisni, obzhynkovi-pisni, vesilni-pisni,
holosinnya, chumatski-burlatski-pisni, narodni-balady, rodynna-liryka-kolomyiky, charivni-kazky,
kazky-pro-tvaryn, sotsialno-pobutovi-kazky, narodni-lehendy, istorychni-perekazy, prykazky-ta-pryslivia,
zahadky, narodni-anekdoty.

**10 broad-scope additions (user-approved, incl. #10):**
1. `narodni-viruvannia-mifolohiia-demonolohiia` (мавки/русалки/домовик/упир/відьма + дохристиянські вірування)
2. `istorychni-pisni` (historical SONGS — distinct from dumy & from prose perekazy)
3. `vertep-narodna-drama` 4. `dytiachyi-folklor-kolyskovi`
5. `narodni-muzychni-instrumenty` (бандура/кобза/трембіта/цимбали; corpus JACKPOT)
6. `narodni-tantsi` 7. `pysankarstvo` 8. `narodna-vyshyvka-rushnyk-strii`
9. `narodni-remesla-ta-khudozhni-promysly` 10. `kalendarna-obriadovist-zvychai` ✅ KEEP (user: "super folkish")

**GPT cross-check refinements to APPLY when locking the queue (msg #1148):**
- **DE-WEIGHT bylyny 4→1** (de-imperialize; bylyny are the most RU-appropriated genre; do NOT open with them).
  Fold bohatyri/social/zastavy into one; fold `pokhodzhennia-dum` into kobzarstvo.
- **Resistance songs `striletski-povstanski-pisni` = IN** (user: "fofc they are in, fuck the occupiers").
- Add `pisni-literaturnoho-pokhodzhennia` (романси/духовні псальми — the high-culture bridge genre).
- Add `rodynna-obriadovist-zvychai` (family-RITE system) + `rehionalni-etnokulturni-tradytsii`
  (Гуцул/Бойко/Лемко/Полісся — anti-flattening) + `narodna-kukhnia` (борщ/кутя/коровай — UNESCO, RU-flashpoint).
- Add opening **`narodna-kultura-yak-systema`** (systems overview) — GPT's recommended frame.
- Rename: kobzarstvo→`kobzarstvo-lirnytstvo`; chumatski→`suspilno-pobutovi-pisni`; obzhynkovi→`zhnyvarski-obzhynkovi`.
- **#M-4 caution:** do NOT present Перун/Велес/**Берегиня** as a tidy pagan pantheon (Берегиня = modern romantic
  reconstruction). Bake into the belief dossier.
- **Net ≈ 41 topics**, rebalanced (epic 9→5). GPT's pilot pick = `kalendarna-obriadovist-zvychai` (#10) — converges with Claude.

### 📐 FOLK DOSSIER SCHEMA (the quality contract — genre/phenomenon-shaped, NOT bio's person arc)
1. Визначення та класифікація · 2. Походження та історичний контекст · 3. Поетика/форма/техніка ·
4. **Класичні зразки + ВЕРБАТИМ примірники (every quote `verify_quote`-confirmed)** ·
5. Побутування/виконавство/функція · 6. Збирачі та дослідники (corpus-cited) ·
7. **Культуроносна/антиколоніальна роль** (the carrying-identity-under-oppression thesis) ·
8. **Місток до високої культури** (opera/lit/art bridge) · 9. Decolonization/NPOV + source-disagreement ·
10. Acceptance self-check. **+ multimodal-hook capture**: image `chunk_id`s (SigLIP search_images),
named recording/song refs, performance/ritual descriptions — so the eventual module can be experiential.

### 🎨 DESIGN ARCHETYPES (Claude's design lane — POCs built this session, in `docs/poc/`)
**Finding:** there is NO realized seminar module POC (0 built across all 7 seminar tracks). The POC design
(`docs/poc/poc-lesson-design.html`) has core + a generic `seminar-source-analysis` archetype (12 activity
types #20-31, all source/text analysis) on a fixed 4-tab shell (Урок·Словник·Зошит·Ресурси). Resolver:
`scripts/pipeline/module_archetypes.py`; contract: `docs/architecture/module-archetype-contract.md`.

**Coverage verdict (evidence-grounded):**
| Tracks | Archetype |
|---|---|
| bio · hist · istorio · **oes** · **ruth** · lit (+ 7 lit sub-tracks) | `seminar-source-analysis` ✅ (oes/ruth = its NATIVE philology use case: transcription/paleography/etymology/dialect) |
| **folk** | 🆕 `folk-experiential` — **built**: `docs/poc/poc-folk-lesson-design.html` |
| **lit (all 8 sub-tracks)** | one all-round page — **built**: `docs/poc/poc-lit-lesson-design.html` |
| **lit-drama** + **folk** + **bio cultural-figures** (Леонтович/Квітка-Цісик/Бойчук) | **shared performative/multimodal module** (audio + dramatic-reading + image-decode) |

- **folk-experiential POC** (worked example koliadky/Щедрик, corpus-sourced): NEW components = audio block
  (hear the sung text), symbolic-decode (clickable hotspots), high-culture bridge (Щедрик→Леонтович→Carol of
  the Bells), folk activity families #40-45 (aural genre-ID, symbolic decode, ritual sequencing, variant
  compare, motif/formula, performance). Decolonization myth-box ties folk→bio (Leontovych murdered by Cheka 1921).
  **User feedback: WANT MORE PROSE in the Урок body** (activities are the in-prose layer; expository prose must be richer).
- **all-round lit POC** (worked example Леся «Лісова пісня»): close-reading annotation, prosody/scansion,
  narrative-structure map, + the SHARED dramatic-performance module (covers lit-drama), myth-box, lit
  families #50-54. Serves all 8 lit sub-tracks (genre diffs = content/register at plan level).
- **Net: 2 page archetypes + 1 shared module — NOT 13 designs.** oes/ruth/hist/istorio/bio need NO new page.

### ✅ STAGE-0 FOUNDATION LOCKED (2026-06-06, branch `claude/folk-stage0-lock`, PR pending)
NEXT-ACTION item 1 is DONE — the 4 foundation docs now exist (mirror bio's Stage-0):
- `docs/folk-epic/phase-folk-queue.md` — **42-topic** ordered, de-imperialized queue; every GPT #1148
  refinement applied (bylyny 9→1, pokhodzhennia-dum fold, full rename/add set); pilot marked; block
  balance table vs GPT targets.
- `docs/folk-epic/folk-dossier-schema.md` — the 10-section quality contract + REQUIRED multimodal-hook
  block (image chunk_ids / named recordings / ritual sequence / motif inventory).
- `docs/folk-epic/folk-review-rubric.md` — corpus-hammer rubric; `verify_quote` every folk text;
  cross-family (GPT↔Claude), no DeepSeek; OPEN-PR-no-self-merge.
- `docs/folk-epic/folk-experiential-archetype-spec.md` — 4-tab shell + families #40–45 + 3 multimodal
  blocks + myth-box; "more prose in Урок" feedback baked in (item 2 done).
- `docs/folk-epic/folk-ssot-migration.md` — **executable** old-27→new-42 slug map (carry/rename/fold-
  archive/new) + per-file deltas. **`curriculum.yaml` folk block UPDATED to the 42-topic order in this
  PR** (manifest lane, CI-safe). Plan-file migration + the 2 code surfaces (`compile.py
  FOLK_DOMAIN_MAP`, `module_archetypes.py` folk-experiential) = GPT dispatch, gated on merge.

### ▶ NEXT ACTIONS ON RESUME (folk, in order)
0. ✅ **DONE — foundation fully merged.** Stage-0 #2759 (`abf280f490`) + merge-grant #2762 + SSOT
   migration #2763 (`d44931b2e9`). main now carries: `curriculum.yaml` folk **42** · `plans/folk` (42
   files + `_archive/` for the 6 folds) · `compile.py FOLK_DOMAIN_MAP` 42 slugs · `module_archetypes.py`
   **folk-experiential** registered + routed (`resolve("folk")→folk-experiential`, verified) · the 4
   design docs · `folk-ssot-migration.md`. Foundation ↔ registry are now consistent.
1. ✅ **DONE (superseded by SESSION 2 block at top) — pilot dossier** `kalendarna-obriadovist-zvychai`
   shipped (#2768 `0722cb4c76`), corpus-hammer review PASSED. See the SESSION 2 RESUME-HERE block for
   current state + next actions.
2. **Then dossier → grounded wiki:** `compile.py --writer {gpt-5.5|claude} --dossier
   docs/research/folk/kalendarna-obriadovist-zvychai.md` (its `folk/ritual` domain now exists).
3. Then the build-order first-6: `narodna-kultura-yak-systema` → (pilot ✓) → `narodni-viruvannia-…` →
   `koliadky-shchedrivky` → `rodynna-obriadovist-zvychai` → `dumy-nevilnytski-lytsarski`.
   Writer = GPT now / Claude after June 8; cross-family review = the other (no DeepSeek for culture).
4. Optional: design the **lit-drama** variant (≈80% assembled from folk parts) when convenient.

### 📊 CORPUS FACTS (folk is well-sourced — verified)
collection_stats: textbooks 25,714 · literary_texts 137,688 · sum11 127,069 · grinchenko 67,275. Verified
verbatim primary folk texts retrievable: Маруся Богуславка (duma), Щедрик, «Лісова пісня», full ULP lesson
on народні інструменти (бандура/трембіта/цимбали), писанка/вишивка in grades 2-6, троїсті музики + вертеп +
козацьке бароко in history textbooks. **SigLIP `search_images` exists** → material-culture topics get visuals
despite "no YT". `compile.py --writer {gemini,claude,gpt-5.5}` (NO agy arm — would need wiring); dossier
grounding live (#2702). Folk discovery already exists (27 files, real rag_chunks); 0 folk dossiers; 0 folk modules.

### 🗂 ARTIFACTS
**Prior session (merged via #2745):**
- `docs/poc/poc-folk-lesson-design.html` (folk-experiential archetype POC)
- `docs/poc/poc-lit-lesson-design.html` (all-round lit archetype POC)
- GPT folk-taxonomy cross-check = bridge msg #1148 (`ab read 1148`)

**This session (branch `claude/folk-stage0-lock`, Stage-0 lock — PR pending, NO self-merge):**
- `docs/folk-epic/phase-folk-queue.md` (42-topic locked queue)
- `docs/folk-epic/folk-dossier-schema.md` (10-section contract + multimodal hooks)
- `docs/folk-epic/folk-review-rubric.md` (corpus-hammer rubric)
- `docs/folk-epic/folk-experiential-archetype-spec.md` (module archetype spec for GPT)
- This handoff (refreshed). **PR carries all 5 + handoff; orchestrator promotes.**

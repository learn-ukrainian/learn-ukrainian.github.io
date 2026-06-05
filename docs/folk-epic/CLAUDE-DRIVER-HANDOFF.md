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
> **⚖ MERGE POLICY:** the bio merge-grant was bio-specific. For FOLK, **OPEN PRs, do NOT self-merge** —
> user/orchestrator promotes (until the user extends a folk grant).

## ▶▶▶ SESSION HANDOFF (2026-06-06, FOLK SCOPE + TAXONOMY + DESIGN ARCHETYPES) — RESUME HERE

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

### ▶ NEXT ACTIONS ON RESUME (folk, in order)
1. **Lock the folk foundation** (this branch is Stage-0): apply the GPT refinements → final ~41-topic
   ordered queue doc (`docs/folk-epic/phase-folk-queue.md`) + the dossier schema + a corpus-heavy review
   rubric + the `folk-experiential` archetype spec (activity families #40-45 + the 2 multimodal blocks, on
   the existing 4-tab shell) as a hand-off for GPT. Mirror bio's Stage-0.
2. **More prose** in the folk-experiential Урок design (user feedback).
3. **First dossier — pilot `kalendarna-obriadovist-zvychai`** (GPT + Claude both picked it; best shows folk
   as a SYSTEM). Writer = GPT now / Claude after June 8; cross-family review = the other; corpus-hammer
   (`verify_quote` every folk text). Then dossier → grounded wiki (compile.py is dossier-grounded since #2702).
4. Optional: design the **lit-drama** variant (≈80% assembled from folk parts) when convenient.

### 📊 CORPUS FACTS (folk is well-sourced — verified)
collection_stats: textbooks 25,714 · literary_texts 137,688 · sum11 127,069 · grinchenko 67,275. Verified
verbatim primary folk texts retrievable: Маруся Богуславка (duma), Щедрик, «Лісова пісня», full ULP lesson
on народні інструменти (бандура/трембіта/цимбали), писанка/вишивка in grades 2-6, троїсті музики + вертеп +
козацьке бароко in history textbooks. **SigLIP `search_images` exists** → material-culture topics get visuals
despite "no YT". `compile.py --writer {gemini,claude,gpt-5.5}` (NO agy arm — would need wiring); dossier
grounding live (#2702). Folk discovery already exists (27 files, real rag_chunks); 0 folk dossiers; 0 folk modules.

### 🗂 ARTIFACTS THIS SESSION
- `docs/poc/poc-folk-lesson-design.html` (folk-experiential archetype POC)
- `docs/poc/poc-lit-lesson-design.html` (all-round lit archetype POC)
- GPT folk-taxonomy cross-check = bridge msg #1148 (`ab read 1148`)
- This handoff. **PR: OPEN (no self-merge) — folk-foundation Stage-0.**

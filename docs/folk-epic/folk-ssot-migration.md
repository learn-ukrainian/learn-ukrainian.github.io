# Folk SSOT Migration — 27 → 42 (executable spec)

> The locked queue (`phase-folk-queue.md`) is a *plan*; this doc makes it **executable against the
> source-of-truth files** so the registry stops diverging from the design (the #M-11 trap). It is the
> brief for the migration dispatch.
>
> **Done in the Stage-0 PR (Claude, manifest lane, CI-safe):** `curriculum.yaml` `folk:` block updated
> to the 42-topic ordering below.
> **Dispatched to GPT (code + module lane, separate worktree PR, gated on Stage-0 merge):** the
> plan-file migration + the two code surfaces + discovery re-key.
>
> **#M-10 / #M-26:** folded/renamed plan files carry **real rag_chunks + rich plan content** — they are
> ARCHIVED (moved to `plans/folk/_archive/`), **never deleted**. A fold MERGES the archived content
> into the survivor's eventual dossier; it does not discard it.

## Slug map (old 27 → new 42)

### Carry-forward (slug unchanged — 14)
`koliadky-shchedrivky` · `vesnianky-hayivky` · `vesilni-pisni` · `holosinnya` · `dumy-sotsialno-pobutovi`
· `bylyny-kyivskoho-tsyklu` (now the SOLE bylyny topic) · `narodni-balady` · `charivni-kazky` ·
`kazky-pro-tvaryn` · `sotsialno-pobutovi-kazky` · `narodni-lehendy` · `istorychni-perekazy` ·
`prykazky-ta-pryslivia` · `zahadky` · `narodni-anekdoty`.
*(Note: queue prose uses `holosinnia`; the existing slug is `holosinnya` — carry the EXISTING spelling
to avoid orphaning `holosinnya.yaml` + its rag_chunks.)*

### Rename (old → new — 5; `git mv` the plan file, re-key FOLK_DOMAIN_MAP + discovery)
| old slug | new slug | why (GPT #1148) |
|---|---|---|
| `kupalski-pisni` | `kupalski-rusalni-pisni` | summer cycle; **fold** `rusalni-pisni` in |
| `obzhynkovi-pisni` | `zhnyvarski-obzhynkovi-pisni` | harvest naming |
| `kobzarstvo-fenomen` | `kobzarstvo-lirnytstvo` | guilds/ліра/псальми/repression; **fold** `pokhodzhennia-dum` in |
| `chumatski-burlatski-pisni` | `suspilno-pobutovi-pisni` | too narrow → full social-song set |
| `rodynna-liryka-kolomyiky` | `rodynno-pobutovi-pisni` | was mis-scoped; **split** `kolomyiky` out as own topic |

### Fold → archive (8 plan files merged into survivors)
| folded (archive) | into survivor | note |
|---|---|---|
| `rusalni-pisni` | `kupalski-rusalni-pisni` | summer cycle |
| `pokhodzhennia-dum` | `kobzarstvo-lirnytstvo` | theory, not a genre |
| `dumy-lytsarski` | `dumy-nevilnytski-lytsarski` | merge knightly+captivity dumy (rename `dumy-nevilnytski`→`dumy-nevilnytski-lytsarski`) |
| `bohatyri-illiya-dobrynia` | `bylyny-kyivskoho-tsyklu` | **bylyny de-weight 9→1** |
| `bylyny-sotsialni` | `bylyny-kyivskoho-tsyklu` | bylyny de-weight |
| `zastavy-bohatyrski` | `bylyny-kyivskoho-tsyklu` | subcycle/motif, not a peer genre |

### New topics (need plan stubs — 13)
`narodna-kultura-yak-systema` · `narodni-viruvannia-mifolohiia-demonolohiia` ·
`zamovliannia-zaklynannia-prymovky` · `kalendarna-obriadovist-zvychai` ★(pilot) ·
`rodynna-obriadovist-zvychai` · `istorychni-pisni` · `striletski-povstanski-pisni` · `kolomyiky` ·
`pisni-literaturnoho-pokhodzhennia` · `narodni-opovidannia-buvalshchyny-memoraty` ·
`dytiachyi-folklor-kolyskovi` · `vertep-narodna-drama` · `narodni-muzychni-instrumenty` ·
`narodni-tantsi` · `pysankarstvo` · `narodna-vyshyvka-rushnyk-strii` ·
`narodni-remesla-ta-khudozhni-promysly` · `narodne-zhytlo-sadyba-hospodarstvo` ·
`narodna-kukhnia-obriadova-yizha` · `rehionalni-etnokulturni-tradytsii` ·
`narodna-kultura-ta-vysoka-kultura-mistky`.
*(13 named "net-new" beyond the renames; total new plan stubs = 21 once the rename targets that have no
prior file are counted. GPT generates stubs at C1+, schema-valid, marked `status: stub` until built.)*

## Per-file deltas

### 1. `curriculum/l2-uk-en/curriculum.yaml` `folk:` block — DONE in Stage-0 PR
Replaced the 27-slug `modules:` list with the 42-topic build-ordered list (see `phase-folk-queue.md`).
CI-safe: no test enforces module↔plan-file existence; `compile.py` (dossier→wiki) reads discovery +
`FOLK_DOMAIN_MAP`, not this block.

### 2. `plans/folk/*.yaml` — GPT
`git mv` the 5 renames; `git mv` the 6 folded files into `plans/folk/_archive/`; create the new plan
stubs (C1+, schema-valid). Preserve folded files' rag_chunks for the survivor's dossier.

### 3. `scripts/wiki/compile.py` `FOLK_DOMAIN_MAP` — GPT (code)
Re-key to the 42 slugs. **Proposed** domain grouping (GPT finalizes):
`folk/overview` (01) · `folk/belief` (02–03) · `folk/ritual` (04–10 + holosinnya) ·
`folk/genres` (dumy×2, bylyny) · `folk/historical` (istorychni-pisni, striletski-povstanski-pisni) ·
`folk/lyric` (rodynno-pobutovi, kolomyiky, suspilno-pobutovi, narodni-balady, pisni-lit-pokhodzhennia)
· `folk/prose` (kazky×3, lehendy, perekazy, opovidannia-buvalshchyny) ·
`folk/short-forms` (prykazky, zahadky, anekdoty, dytiachyi-folklor) ·
`folk/performance` (vertep, instrumenty, tantsi) ·
`folk/material` (pysankarstvo, vyshyvka, remesla, zhytlo, kukhnia) ·
`folk/synthesis` (rehionalni, vysoka-kultura-mistky).

### 4. `scripts/pipeline/module_archetypes.py` — GPT (code)
Folk currently lands in `SEMINAR_TRACKS` → `resolve_module_archetype` returns `seminar-source-analysis`.
Register the new `folk-experiential` archetype (per `folk-experiential-archetype-spec.md`: 4-tab shell,
activity families #40–45, 3 multimodal blocks, myth-box) and route `track == "folk"` to it. Keep
`oes/ruth/hist/istorio/bio/lit` on `seminar-source-analysis`.

### 5. `scripts/pipeline/config_tables.py` — note only
L45 persona ("Professor of Ukrainian Folklore") + L61 `"folk": "full-rebuild-lit"` skill are fine for
the broad-culture scope. No change required now; revisit only if folk needs a dedicated skill profile.

### 6. discovery files — GPT
Re-key renamed/folded discovery slugs; regenerate from the migrated plans (`compile.py` auto-generates
discovery from plans when absent).

## Sequence
Stage-0 PR (curriculum.yaml + this spec + the 4 design docs) merges → **dispatch GPT** for #2–#4 + #6
(one worktree PR) → that merges → pilot dossier `kalendarna-obriadovist-zvychai` can compile to wiki
(its `FOLK_DOMAIN_MAP` entry now exists).

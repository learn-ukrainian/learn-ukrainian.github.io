# `folk-experiential` Module Archetype — Spec (Stage-0 → GPT build handoff)

> The module-design contract for the FOLK track. Claude designs the page (this spec + the worked POC);
> **GPT builds modules against it** (Claude builds no modules — boundary locked 2026-06-06). Realized
> worked example: `docs/poc/poc-folk-lesson-design.html` (koliadky/Щедрик, corpus-sourced).
> Resolver to wire: `scripts/pipeline/module_archetypes.py`; contract:
> `docs/architecture/module-archetype-contract.md`.

## Why a new archetype
The existing `seminar-source-analysis` archetype (activity types #20–31, all source/text analysis on
the 4-tab shell) fits bio/hist/istorio/oes/ruth/lit. It does NOT fit folk: folk culture is **aural,
performative, symbolic, and material** — a sung text, a ritual sequence, a pysanka motif, a danced
form. `folk-experiential` adds the missing modalities WITHOUT changing the shell.

## Shell — UNCHANGED 4-tab (`Урок · Словник · Зошит · Ресурси`)
Same 4-tab shell as every other module. `folk-experiential` only adds new **block types** inside the
**Урок** tab and new **activity families** inside the **Зошит** tab. No new tab, no shell fork.

## Three new multimodal blocks (Урок tab)
1. **Audio block** (`audio-block`) — lets the student *hear* the sung/performed text (the dossier's
   §"named recording references" resolve here). Pairs the audio with the verbatim, `verify_quote`-
   confirmed text so the learner follows the words while hearing the performance.
2. **Symbolic-decode block** (`symbolic-decode`) — an image (SigLIP `chunk_id` from the dossier) with
   **clickable hotspots**; each hotspot decodes a motif/symbol (pysanka sign, rushnyk pattern, vertep
   tier). Feeds directly from the dossier's motif inventory + image chunk_ids.
3. **High-culture bridge block** (`high-culture bridge`) — the folk→opera/lit/art line made
   interactive (Щедрик → Леонтович → *Carol of the Bells*; folk → «Запорожець за Дунаєм» / «Лісова
   пісня»). This is what makes the module experiential rather than antiquarian — it answers "why does
   this folk form still matter."
- **Decolonization myth-box** (`myth-box`) — a recurring inline callout that corrects an imperial or
  romantic-nationalist myth (e.g. bylyny-as-Russian-epic; Берегиня-as-ancient-goddess) and, where the
  dossier supports it, ties folk→bio (e.g. Leontovych murdered by the Cheka, 1921).

## Six folk activity families (Зошит tab) — #40–#45
These extend the global activity-type registry. Exact labels from the realized POC:

| # | family | what the learner does | dossier input it consumes |
|---|--------|-----------------------|---------------------------|
| #40 | **Aural Genre-ID** | hear a clip → identify the genre/cycle by its aural markers | named recordings + §3 poetics |
| #41 | **Symbolic Decoding** | decode a motif/symbol from an image or text | motif inventory + image chunk_ids |
| #42 | **Ritual Sequencing** | order the steps of a rite/performance correctly | §5 performance/ritual sequence |
| #43 | **Variant Comparison** | compare regional/temporal variants of one text/form | regional variation notes (§5/§9) |
| #44 | **Motif / Formula** | spot the oral-formulaic phrase / recurring epithet | motif/formula inventory (§3) |
| #45 | **Performance** | produce/perform — recite, sing-along, annotate a reading | verbatim exemplars (§4) |

## User feedback baked in (2026-06-06)
**MORE PROSE in the Урок body.** Activities are the in-prose interactive layer, but the expository
prose itself must be richer — a learner reading only the Урок prose should get a full, well-written
account of the genre, not a thin scaffold around activities. The dossier's depth (10 sections) is the
fuel; the module's Урок must spend it.

## Acceptance checklist for a `folk-experiential` module (GPT self-checks before PR)
- [ ] 4-tab shell intact (`Урок · Словник · Зошит · Ресурси`); no tab empty (m20 #M-11 lesson).
- [ ] ≥1 of each multimodal block present where the dossier supports it (audio / symbolic-decode /
      high-culture bridge); every audio text and exemplar is `verify_quote`-confirmed.
- [ ] Зошит draws from families #40–#45 (not all inline; honor the INLINE-vs-WORKBOOK activity-count
      config), not 10 inline same-type items.
- [ ] Урок prose is rich (user feedback), corpus-grounded, C1+ register, `check_russian_shadow` clean.
- [ ] ≥1 decolonization myth-box; framing passes `folk-review-rubric.md` gate 7.
- [ ] Словник + Ресурси populated (Ресурси = dossier-derived references; **no YT**).

## Related designs (not part of folk MVP)
- **all-round lit** archetype — `docs/poc/poc-lit-lesson-design.html` (serves all 8 lit sub-tracks).
- **Shared performative/multimodal module** — lit-drama + folk + bio cultural-figures (Леонтович/
  Квітка-Цісик/Бойчук) reuse ~80% of these blocks. Build the lit-drama variant when convenient
  (≈80% assembled from folk parts).

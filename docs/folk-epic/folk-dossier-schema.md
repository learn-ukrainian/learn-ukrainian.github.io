# Folk Dossier Schema — the quality contract (Stage-0)

> The structural contract for every folk dossier at `docs/research/folk/{slug}.md`. **Genre/
> phenomenon-shaped**, NOT bio's person-arc — a folk dossier explains a *genre, rite, or material
> tradition*, its poetics, its verbatim exemplars, and its anti-colonial carrying-role. The dossier
> is the **sole knowledge layer** (no YT resources), so depth is everything: it must be rich enough
> that the grounded wiki AND GPT's experiential module can both be assembled from it without inventing
> a single fact. Register C1+.

## The 10 sections (all required)

1. **Визначення та класифікація** — what the genre/phenomenon is; its place in the folk-culture
   system; how scholars classify it; boundary cases and sub-forms.
2. **Походження та історичний контекст** — origins, periodization, how it changed across centuries;
   honest about contested datings and reconstruction (esp. pre-Christian / mythological layers).
3. **Поетика / форма / техніка** — verse form, formula, melody/performance technique, materials &
   craft technique (for material culture), symbolic vocabulary.
4. **Класичні зразки + ВЕРБАТИМ примірники** — canonical examples WITH verbatim primary texts.
   **Every quoted text `verify_quote`-confirmed** (the folk analogue of the bio quote-integrity gate)
   and attributed to a named edition/collector. Record the verify_quote score inline. If a text
   cannot be corpus-confirmed verbatim, mark it **do-not-quote / paraphrase-only** — NEVER invent or
   "smooth" a duma line or song lyric.
5. **Побутування / виконавство / функція** — living practice: who performed/performs it, when, in
   what ritual or social function; regional distribution of the practice.
6. **Збирачі та дослідники** — the collectors and scholars (Лановик, Колесса, Грушевський,
   Грінченко, Нудьга, etc.), corpus-cited. Where scholars disagree, name the disagreement.
7. **Культуроносна / антиколоніальна роль** — the carrying-identity-under-oppression thesis made
   concrete for THIS genre: how it preserved language/memory/identity under imperial pressure; what
   was banned/appropriated/russified and how the tradition survived.
8. **Місток до високої культури** — the bridge to opera / literature / art / academic music
   (e.g. Щедрик → Леонтович → Carol of the Bells; folk → «Запорожець за Дунаєм»; → «Лісова пісня»;
   → Бойчук). This is what lets the eventual module be experiential, not antiquarian.
9. **Decolonization / NPOV + source-disagreement** — honest in every direction: no Russocentric
   framing, no romantic-nationalist over-claim (Берегиня-as-ancient-goddess type errors), no
   flattening of regional variation. Surface contested points and source disagreements; don't smooth.
10. **Acceptance self-check** — the writer's own pass against `folk-review-rubric.md` hard gates,
    with the deterministic tool evidence (verify_quote scores, check_russian_shadow result,
    query_cefr_level) quoted raw (#M-4).

## + Multimodal-hook capture (REQUIRED — feeds GPT's experiential module)
The dossier must explicitly capture, in a dedicated block, the raw material the `folk-experiential`
archetype consumes:
- **Image `chunk_id`s** — from SigLIP `search_images` (pysanka motifs, rushnyk patterns, instruments,
  vertep box, regional dress). List the `chunk_id`s so the module's symbolic-decode hotspots resolve.
- **Named recording / song references** — performer + recording/edition names for the audio block
  (the module lets the student *hear* the sung text; the dossier names what to play).
- **Performance / ritual descriptions** — step-by-step ritual or performance sequence (feeds the
  Ritual-Sequencing activity family #42).
- **Motif / formula inventory** — recurring symbols, epithets, oral-formulaic phrases (feeds
  Symbolic-Decode #41 and Motif/Formula #44).

## Grounding rule
Where a retrieved chunk (esp. Wikipedia-only) conflicts with a corpus primary source or named
scholarly edition, **the corpus/edition wins**; Wikipedia-only extraordinary claims are flagged, not
asserted. This mirrors the bio "grounding > breadth" gate.

## Corpus tools the writer must hit (folk-specific)
`verify_quote` (every text), `search_literary`, `search_grinchenko_1907`, `search_heritage`,
`search_text` (textbooks/ULP), `search_images` (SigLIP — material culture), `check_russian_shadow`,
`query_cefr_level`, `search_idioms` (paremiology), `search_esum`/`query_sum20` (etymology where
relevant). Folk is well-sourced (textbooks 25,714 · literary_texts 137,688 · sum11 127,069 ·
grinchenko 67,275) — a thin dossier is a writer failure, not a corpus gap.

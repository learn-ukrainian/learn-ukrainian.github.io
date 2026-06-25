<!-- rule_id: #R-CITE-HONEST -->
**Seminar/FOLK source, length, and form hard stop.** For seminar tracks, especially `LEVEL=folk`, treat the wiki `[S#]` registry and `plan.references` as a CLOSED citation universe. Cite ONLY sources provided in this build. Do NOT add outside source citations, titles, authors, or dates such as `Грушевський М. «Історія української літератури»` or `Леся Українка. «Веснянка» (1890)` unless that exact source appears in the provided registry; mention such works without a citation or omit them. This preserves the earlier `resources.yaml` rule: textbook resources still come only from `plan.references`. `citations_resolve` hard-rejects unresolved citations.

For seminar/FOLK word count, `{WORD_TARGET}` is a true floor. When `{WORD_TARGET}=5000`, the 92% tolerance still requires about 4600 accepted words; self-counted markdown words run high. Budget and write at least ~1.20x the floor by expanding corpus analysis, examples, source comparison, and cultural context from the provided wiki/RAG, never padding.

Before emitting any uncertain Ukrainian term in seminar/FOLK prose, call `mcp__sources__check_russian_shadow` and `mcp__sources__search_style_guide`; if a style-guide or shadow check flags the form, do NOT use it. Use `аранжування`, not `<!-- bad -->аранжировку<!-- /bad -->`; prefer the standard style-guide choice (for example `неоціненний` where `безцінний` is flagged by context). The VESUM/russianism/calque gates reject Russian-pattern forms even when they look inflected.

For FOLK, verbatim song, duma, or ritual fragments may contain authentic archaic/dialectal forms such as `Дівоцькую`, `гаїлки`, `дівочок`, or `рубочки`. Put those fragments in blockquotes or the module's verbatim-quote convention so the quote is visibly evidence, not exposition. Teacher prose around the quote must use modern Ukrainian or explicitly verified VESUM/slovnyk.me heritage terms; bare unattested archaic/dialectal folk forms in exposition fail.

<!-- rule_id: #R-FOLK-RELIGIOUS-FRAMING -->
**FOLK: never frame Christian-folk genres as "magic" or as a pagan core under a Christian shell.** This is a religious-sensitivity AND decolonization hard rule. NEVER describe колядки/щедрівки (or any Christian-folk tradition — Великдень, Різдво, обжинки with a Christian layer) as «прикладна магія», a "magic" act, or with a «дохристиянське ядро / християнська оболонка (нашарування, шар)» pagan-core-Christian-veneer structure. That framing offends religious learners and reproduces the Soviet-atheist "pagan-survival" distortion (it is a known writer-bias trap, not a neutral scholarly default). Instead: present колядки/щедрівки as **величально-побажальні** (praise + well-wishing) and give the Nativity / Eastern-rite religious meaning **parity** with any archaic stratum you discuss; щедрування is a folk-Christian (Eastern-rite) tradition. If you mention the "magic/pagan-survival" reading at all, attribute it explicitly as a contested or Soviet-era frame and balance it — do not assert it as fact. The term `продукувальна магія` is acceptable ONLY for genuinely pre-Christian agrarian rites (e.g. spring веснянки/гаївки, купальські), NEVER for колядки/щедрівки. (Origin: user flag 2026-06-23 + PR #3745.)

<!-- rule_id: #R-FOLK-PRIMARY-TEXTS -->
**FOLK: embed the primary texts.** The dossier's «ВЕРБАТИМ примірники» (§4) are the ONLY quotable folk-primary fragments: they already `verify_quote`'d against this build's corpus/wiki and carry `[S#]` sources. Surface **≥4** of them in the Урок body within **`:::primary-reading` blocks** (`:::primary-reading` + the exact dossier §4 fragment + its `[S#]` + `:::`); quote verbatim, never normalize archaic forms. Anchor «Корпус і контекст» and «Поетика» on quoted lines instead of paraphrasing. `:::primary-reading` quoted lines are word-count-excluded; the surrounding «Корпус і контекст» and «Поетика» exposition fills the budget. Do NOT quote folk songs/chants from memory, even famous traps such as `Щедрик-ведрик`, `Коляд-коляд`, `А ми просо сіяли`, or `Зашуміла діброва`, unless that exact fragment appears in this build's dossier §4 with `[S#]`. Do NOT embed literary-authored verse (Шевченко, Франко, Леся Українка, etc.) as a folk primary text; literary verse is not a folk song and fails `textbook_quote_fidelity`. If dossier §4 has fewer than four fragments, embed only the fragments it has and fill the word budget with grounded exposition, never by backfilling quotes from memory.

Seminar/FOLK `resources.yaml` MUST include at least one `role: reading` entry with a one-line learner task in `notes`. Its `url:` MUST be a public allowlisted URL (`data/primary_text_sources.yaml`): the topic's `uk.wikipedia.org` article is the guaranteed floor, plus a specific `uk.wikisource.org` / `litopys.org.ua` / `ukrlib.com.ua` work page when one resolves. The on-site primary text is surfaced through the `:::primary-reading` block above, NOT a `wiki/...` resources link — internal repo paths are AI-facing, not student-facing, and are rejected. FORBIDDEN: internal `wiki/...` (or `docs/wiki/...`) paths, bare-domain landings, section/category landings, and guessed opaque `?id=N` URLs.

<!-- rule_id: #R-FOLK-GROUNDED-VOCAB -->
**FOLK regional/ethnographic vocabulary — grounded in VESUM or cited slovnyk.me/heritage.** Naming regional genre-variants is a decolonization goal: authentic regional and archaic variants are ENCOURAGED, not flattened away. A folk term used in EXPOSITION is acceptable when it is attested in VESUM OR in slovnyk.me/heritage (`mcp__sources__search_slovnyk_me` / `mcp__sources__search_heritage`) with `is_russianism == false`; `vesum_verified` accepts the committed slovnyk.me/heritage fallback for FOLK/seminar terms. Get it right in the first pass:

1. **Lead with a clear headword** such as `гаївки` or `веснянки`, then name verified regional variants beside it. Regional/archaic forms such as `ягілки`, `гагілки`, and `риндзівки` are welcome when this build's wiki/dossier warrants them and slovnyk.me/heritage verifies them.
2. **Verify every regional variant before emitting it.** Query the singular lemma when slovnyk.me is keyed by headword, check the exact surface you will write, and use only rows where `is_russianism == false`. If neither VESUM nor slovnyk.me/heritage has the term, do not use it.
3. **Never invent a regional genre-name that is absent from the provided wiki/dossier.** If the source does not name a regional variant, do not supply one from memory; unattested names such as `городалька` cannot be verified and will fail the gate.
4. **Do not coin unattested vocabulary in any class.** This applies beyond fused-compound or relational adjectives: reject jargon-borrowing adjectives, invented agent nouns, numeric compounds, hyphenated noun labels, and folk-performance compounds that VESUM and slovnyk.me/heritage lack. Use attested synonyms or rephrase: `дослівний` / `буквальний`, not `вербатимний`; rephrase `подавачка`; `п'ять кроків` / `що має п'ять кроків`, not `п'ятикроковий`; rephrase `слово-дія`; `гра двох гуртів` / `антифонний спів`, not `двохоровий`. Keep legitimate productive and heritage-grounded forms: denominal/deverbal adjectives such as `гаївковий` and `знеособлювальний`, `-ість` nouns, and `-о`-linked compound adjectives whose bases are attested adjectives, such as `імперсько-радянський` and `галицько-західний`, remain allowed when VESUM or the heritage fallback verifies them. Split or rephrase unsupported compounds into attested words: `імперська етнографічна рамка`, not `імперсько-етнографічна`; `пісня з побажаннями` / `з побажаннями`, not `побажальна`.
5. **Keep the verbatim-quote convention for non-expository dialectal fragments.** Song, duma, or ritual fragments may contain authentic archaic/dialectal forms inside cited blockquotes or the module's verbatim-quote convention; do not turn unattested fragments into bare teacher prose.

**FOLK experiential TEXT layer.** For `LEVEL=folk` modules, emit the implemented text-achievable folk layer, not the generic seminar activity mix. In `module.md`, include at least one `:::myth-box` and at least one `:::high-culture-bridge` where wiki/dossier evidence supports them. In `activities.yaml`, use folk activity families `ritual-sequencing` (#42), `variant-comparison` (#43), `motif-formula` (#44), and `performance` (#45) where the wiki/dossier supports the surface, in place of generic `true-false`, `group-sort`, or `match-up` tasks. Do NOT emit `audio-block`, `symbolic-decode`, or `aural-genre-id`; audio and symbolic-decode surfaces are deferred.

**FOLK engagement floor.** Include at least one content-anchored `:::tip`, `:::note`, or `:::caution`; `:::myth-box` does not count for this floor.

Canonical `module.md` source shapes:

```md
:::myth-box
claim: "..."
truth: "..."
claim_source: "..."
truth_source: "..."
:::

:::high-culture-bridge
nodes:
  - "народна форма"
  - "опера / література / мистецтво / культурна циркуляція"
note: "..."
:::

:::primary-reading
> Ой там на горі, ой там на крутій... [S1]
:::
```

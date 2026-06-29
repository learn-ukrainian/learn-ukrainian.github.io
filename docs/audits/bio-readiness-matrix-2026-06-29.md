# BIO Readiness Matrix - 2026-06-29

Base artifact for the #2535 BIO-readiness umbrella (epic #2309). Inventories the readiness surfaces for the 77 new BIO additions appended to `curriculum/l2-uk-en/curriculum.yaml` by the 2026-06-29 expansion research memo (`docs/audits/bio-ukrainian-expansion-research-2026-06-29.md`), before any module is written.

## Summary

- **New BIO slugs:** 77 (`modules[310:387]` in the `levels.bio.modules` list; total BIO roster grew 310 -> 387).
- **SSOT expansion groups:** 6 (all appended after the original 11 groups).
- **Readiness surfaces checked per slug:** plan YAML (`plans/bio/{slug}.yaml`), research dossier (`docs/research/bio/{slug}.md`), site doc (`site/src/content/docs/bio/{slug}.mdx`), wiki page (`wiki/bio/{slug}.md`).

| Surface | Ready / 77 |
| --- | --- |
| Plan YAML (`plans/bio/`) | 0 / 77 |
| Research dossier (`docs/research/bio/`) | 0 / 77 |
| Site doc (`site/src/content/docs/bio/`) | 0 / 77 |
| Wiki page (`wiki/bio/`) | n/a - directory absent |

All 77 new slugs are **greenfield**: none of the four surfaces exist yet. The existing `plans/bio/` (320 files) and `docs/research/bio/` (310 files) artifacts belong to the original pre-expansion roster - **zero** overlap with the new slugs. `wiki/bio/` does not exist (the wiki tree carries `wiki/figures/`, not `wiki/bio/`), so the wiki column is marked absent across all rows per the matrix spec.

- **Living figures among the 77 (canonicity guardrail applies):** 13.
- **High-content-warning figures (required framing before writing):** 5.

## Gate

**No-module-writing gate (#2535).** This matrix is an inventory only. Per the expansion memo and the BIO best-practice docs, **no plan YAML, dossier, site doc, or wiki page may be authored for any new slug until its row is explicitly promoted out of the gate.** Promotion order is fixed by the BIO phase pipeline:

1. Research dossier (`docs/research/bio/{slug}.md`) per `docs/templates/bio-research-dossier-template.md` - >=3 Tier 1/Tier 2 sources, >=2 primary-source quotes, oppression mechanism with dates/document refs, decolonization self-check (`docs/audits/bio-decolonization-checklist.md`).
2. Plan YAML (`plans/bio/{slug}.yaml`) per `docs/best-practices/bio-naming-canonical.md` (slug == filename, BGN/PCGN-2010 transliteration, `aliases:` with forbidden Russian-imperial forms) and `docs/best-practices/bio-image-rights.md` (`portrait:` or `portrait_fallback:`).
3. Site doc / wiki only after plan + dossier pass.

The gate exists because deterministic gates passing is necessary-but-not-sufficient (memory #M-11): a slug is *not* ready just because a row could be filled. Living and high-content-warning rows (below) carry extra blocking framing requirements.

## Matrix

Legend: `Y` = present, `-` = absent. Wiki column omitted from rows (`wiki/bio/` absent for all). `#` is the position in the `levels.bio.modules` list (1-based).

### Ukrainian social resistance and contested memory additions

| # | slug | plan | dossier | site-doc | wiki | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 311 | `ustym-karmaliuk` | - | - | - | absent | CW: contested social resistance, not Robin Hood myth |
| 312 | `oleksa-dovbush` | - | - | - | absent | - |
| 313 | `lukian-kobylytsia` | - | - | - | absent | - |
| 314 | `maksym-zalizniak` | - | - | - | absent | CW-HIGH: Uman/Koliivshchyna content warning; anti-hagiography |
| 315 | `ivan-gonta` | - | - | - | absent | CW-HIGH: Polish/Jewish/Uniate civilian-harm framing |
| 316 | `nestor-makhno` | - | - | - | absent | CW: language/statehood/anarchism complexity explicit; HIST-align |

### Ukrainian state-building, education, and civic institutions additions

| # | slug | plan | dossier | site-doc | wiki | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 317 | `yevhen-petrushevych` | - | - | - | absent | ZUNR statehood; HIST-align checkpoint |
| 318 | `marko-bezruchko` | - | - | - | absent | UNR; HIST-align checkpoint |
| 319 | `dmytro-vitovskyi` | - | - | - | absent | Sich Riflemen/ZUNR; HIST-align checkpoint |
| 320 | `oleksandr-lototskyi` | - | - | - | absent | - |
| 321 | `borys-martos` | - | - | - | absent | - |
| 322 | `volodymyr-chekhivskyi` | - | - | - | absent | UNR; destroyed by Soviet terror; HIST-align |
| 323 | `sofiia-rusova` | - | - | - | absent | - |
| 324 | `khrystyna-alchevska` | - | - | - | absent | - |
| 325 | `mykhailo-tuhan-baranovskyi` | - | - | - | absent | - |
| 326 | `serhii-yefremov` | - | - | - | absent | SVU show-trial oppression arc; HIST-align |
| 327 | `ivan-steshenko` | - | - | - | absent | - |
| 328 | `nadiia-surovtsova` | - | - | - | absent | long-term Soviet political prisoner |
| 329 | `dmytro-doroshenko` | - | - | - | absent | - |
| 330 | `mykola-arkas` | - | - | - | absent | - |
| 331 | `oleksandr-barvinskyi` | - | - | - | absent | - |

### Ukrainian language, ethnography, translation, and scholarship additions

| # | slug | plan | dossier | site-doc | wiki | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 332 | `pavlo-chubynskyi` | - | - | - | absent | - |
| 333 | `markiian-shashkevych` | - | - | - | absent | - |
| 334 | `oleksandr-konyskyi` | - | - | - | absent | - |
| 335 | `fedir-vovk` | - | - | - | absent | Transliteration fix locked: fedir-vovk (NOT fedyr-); sanity-checked |
| 336 | `volodymyr-hnatiuk` | - | - | - | absent | - |
| 337 | `filaret-kolessa` | - | - | - | absent | - |
| 338 | `klyment-kvitka` | - | - | - | absent | - |
| 339 | `mykola-lukash` | - | - | - | absent | translation-as-resistance; some Soviet-era repression |
| 340 | `hryhorii-kochur` | - | - | - | absent | post-repression language culture |
| 341 | `larysa-masenko` | - | - | - | absent | LIVING: completed-work-only, no predictive biography |
| 342 | `ivan-lysiak-rudnytskyi` | - | - | - | absent | - |
| 343 | `yurii-lutskyi` | - | - | - | absent | - |
| 344 | `volodymyr-yermolenko` | - | - | - | absent | LIVING: completed-work-only, no predictive biography |

### Ukrainian music and song-canon additions

| # | slug | plan | dossier | site-doc | wiki | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 345 | `kyrylo-stetsenko` | - | - | - | absent | - |
| 346 | `oleksandr-bilash` | - | - | - | absent | PILOT #4004; Ukrainian song-canon / modern-reception frame |
| 347 | `andrii-malyshko` | - | - | - | absent | SOV: Soviet-era compromise framing |
| 348 | `platon-maiboroda` | - | - | - | absent | - |
| 349 | `levko-revutskyi` | - | - | - | absent | SOV: co-optation framing |
| 350 | `stanislav-liudkevych` | - | - | - | absent | - |
| 351 | `myroslav-skoryk` | - | - | - | absent | - |
| 352 | `ivan-karabyts` | - | - | - | absent | - |
| 353 | `yevhen-stankovych` | - | - | - | absent | LIVING: completed-work-only, no predictive biography |
| 354 | `anatolii-kos-anatolskyi` | - | - | - | absent | - |
| 355 | `dmytro-hnatiuk` | - | - | - | absent | - |
| 356 | `anatolii-solovianenko` | - | - | - | absent | - |
| 357 | `raisa-kyrychenko` | - | - | - | absent | - |

### Ukrainian theater and visual culture additions

| # | slug | plan | dossier | site-doc | wiki | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 358 | `mykola-sadovskyi` | - | - | - | absent | - |
| 359 | `panas-saksahanskyi` | - | - | - | absent | - |
| 360 | `heorhii-narbut` | - | - | - | absent | - |
| 361 | `oleksandr-murashko` | - | - | - | absent | - |
| 362 | `fedir-krychevskyi` | - | - | - | absent | - |
| 363 | `olena-kulchytska` | - | - | - | absent | - |
| 364 | `oleksa-novakivskyi` | - | - | - | absent | - |
| 365 | `ivan-trush` | - | - | - | absent | - |
| 366 | `mykhailo-zhuk` | - | - | - | absent | - |
| 367 | `sofiia-yablonska` | - | - | - | absent | - |

### Ukrainian literary and civic culture additions

| # | slug | plan | dossier | site-doc | wiki | notes |
| --- | --- | --- | --- | --- | --- | --- |
| 368 | `bohdan-lepkyi` | - | - | - | absent | - |
| 369 | `ulas-samchuk` | - | - | - | absent | CW: WWII occupation-era editorship context; avoid hagiography |
| 370 | `andrian-kashchenko` | - | - | - | absent | - |
| 371 | `roman-ivanychuk` | - | - | - | absent | - |
| 372 | `pavlo-zahrebelnyi` | - | - | - | absent | SOV: Soviet-era complexity |
| 373 | `valerii-shevchuk` | - | - | - | absent | LIVING: completed-work-only, no predictive biography |
| 374 | `vsevolod-nestaiko` | - | - | - | absent | - |
| 375 | `volodymyr-rutkivskyi` | - | - | - | absent | - |
| 376 | `ivan-malkovych` | - | - | - | absent | LIVING: completed-work-only, no predictive biography |
| 377 | `oles-berdnyk` | - | - | - | absent | - |
| 378 | `natalena-koroleva` | - | - | - | absent | - |
| 379 | `mykhailo-stelmakh` | - | - | - | absent | SOV: Soviet-era framing nuance |
| 380 | `yurii-shcherbak` | - | - | - | absent | LIVING: completed-work-only, no predictive biography |
| 381 | `vira-aheieva` | - | - | - | absent | LIVING: completed-work-only, no predictive biography |
| 382 | `tamara-hundorova` | - | - | - | absent | LIVING: completed-work-only, no predictive biography |
| 383 | `oksana-kis` | - | - | - | absent | LIVING: completed-work-only, no predictive biography |
| 384 | `mykola-riabchuk` | - | - | - | absent | LIVING: completed-work-only, no predictive biography |
| 385 | `iryna-tsilyk` | - | - | - | absent | LIVING: war-witness; completed-work-only, no predictive biography |
| 386 | `nataliia-vorozhbyt` | - | - | - | absent | LIVING: war-witness; completed-work-only, no predictive biography |
| 387 | `artem-chekh` | - | - | - | absent | LIVING: veteran-writer/war-witness; completed-work-only |

## First Claude Batch

Recommended first 10 dossiers for Claude to prepare. Selection rule: **de-risk the opening batch** - take only figures whose significance is settled (deceased, canonical, encyclopedia-grounded), that were already externally sanity-checked in the 2026-06-29 memo's ESU/IEU pass, that have high PD/CC portrait availability, and that need *no* high-content-warning scaffolding. The batch spans 4 of the 6 groups and is anchored by the gated pilot.

- `oleksandr-bilash` (Олександр Білаш) - **Anchor / pilot (#4004).** Already the gated pilot; song-canon ("Два кольори"), settled legacy (d. 2003). Validates the Ukrainian song-canon / modern-reception workflow while keeping Soviet-era institutional context secondary.
- `pavlo-chubynskyi` (Павло Чубинський) - Author of the anthem text; EIU ground-truth figure; foundational, uncontested, T1-rich. Highest pedagogical leverage.
- `markiian-shashkevych` (Маркіян Шашкевич) - Ruthenian Triad / vernacular literary revival; sanity-checked; PD imagery (pre-1850); no living-person or CW complications.
- `oleksandr-konyskyi` (Олександр Кониський) - NTSh initiator, "Молитва за Україну" text; sanity-checked; settled 19th-c. legacy.
- `fedir-vovk` (Федір Вовк) - Sanity-checked AND the locked transliteration-fix case (fedir- not fedyr-) - good first test that naming-canonical discipline holds end to end.
- `volodymyr-hnatiuk` (Володимир Гнатюк) - NTSh ethnography infrastructure; sanity-checked; deceased 1926; abundant T1/T2.
- `filaret-kolessa` (Філарет Колесса) - Musicologist/folklorist; sanity-checked; deceased 1947; strong NAN/NTSh source base.
- `dmytro-doroshenko` (Дмитро Дорошенко) - Historian/diplomat with a settled diaspora legacy (d. 1951); sanity-checked; exercises the HIST-alignment checkpoint cleanly.
- `heorhii-narbut` (Георгій Нарбут) - UNR visual statehood (currency, seals, alphabet); sanity-checked; deceased 1920; **High** PD imagery (Block-I/visual).
- `oleksandr-murashko` (Олександр Мурашко) - Ukrainian State Academy of Arts cofounder; sanity-checked; deceased 1919; European-level painter with PD portrait holdings.

**Deliberately excluded from the first batch:** the Koliivshchyna/Uman pair (`maksym-zalizniak`, `ivan-gonta`) and `nestor-makhno` (high content-warning, need HIST-alignment + anti-hagiography scaffolding first); `ulas-samchuk` (WWII occupation-era editorship warning); all LIVING figures (canonicity guardrail / non-predictive-biography constraint); and Soviet-era complexity cases beyond the single Bilash pilot.

## Canonicity-Over-Currency Watchlist Policy

From the 2026-06-29 research memo (Claude + AGY/Gemini convergence): **keep living figures in BIO only when significance rests on settled work that would stand regardless of the current war or political outcomes.** Implications for the 77:

- The 13 living figures flagged `LIVING` above may be written **only on completed contributions** - no predictive "future national leader" framing.
- Role-defined **current** wartime / frontline / security / political / civic-defense figures are **excluded** from new BIO additions and held on the memo's watchlist (Берлінська, Вишебаба, Чорногуз, Чмут, Федоров, Буданов, Стерненко, Христов); raise their war-emergent work in HIST / LIT-WAR, not BIO, until the trajectory is stable.
- `Валерій Залужний` is **held** (disputed future trajectory) - this is a deliberate single-case hold, **not** a blanket living-person exclusion.
- `Ігор Сікорський` stays **excluded** (fails the Ukrainian-civic filter); Crimean Tatar expansion beyond Джемілєв/Джелял is held for a separate audit.

## Issue Remap Notes

The original BIO epic tickets (#2330-#2337 Phase 4/5 work, plus #2451) were scoped against the **original** 130/180-figure roster in `docs/audits/bio-track-gap-audit-2026-05-26.md`. They predate the 2026-06-29 +77 expansion and do not reference the six new SSOT groups. Recommended remap **after** this matrix lands:

- **Refresh bodies** of #2330-#2337 (and #2451) to either (a) explicitly scope-exclude the +77 and stay on the original roster, or (b) extend their acceptance criteria to cover the six new groups. Leaving them ambiguous risks an agent treating a +77 slug as in-scope for a phase whose framing/source-tier expectations were written for the original set.
- **Supersede vs. extend:** Phase-1 research tickets (dossier-writing) for the +77 should be **new** sub-issues under #2535, not retrofits of the original Phase-1 tickets - the +77 carry expansion-specific framing (Uman CW, Makhno statehood complexity, Soviet-era complexity, living-figure canonicity) absent from the original ticket bodies.
- **#2535** remains the active Claude-owned umbrella for the +77; **#2309** stays the high-level epic; **#4004** stays the gated `oleksandr-bilash` pilot and should be cross-linked from the first-batch row above.
- Re-run this matrix after any remap so issue scope and surface-readiness stay reconciled.

---

*Generated 2026-06-29 from `curriculum/l2-uk-en/curriculum.yaml` (`levels.bio.modules[310:387]`) and on-disk surface checks. Inventory only - no module content was authored.*

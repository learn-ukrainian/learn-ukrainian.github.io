# Folk Dossier + Wiki Review Rubric (Stage-0)

> ⛔ **Read [`FOLK-FRAMING-STANDARD.md`](FOLK-FRAMING-STANDARD.md) before reviewing.** Its 4 pillars
> (pre-literature · Christian-heritage-first · written-text/school-canonical sourcing · no occult-or-
> pagan-as-belief) and its NEVER list are a **hard, fail-the-artifact gate** here — see Gate 0.

The review scorecard for every folk dossier and the grounded wiki compiled from it. A dossier/wiki
ships only when it passes **all** gates. **Reviewer = cross-family to the writer** (GPT↔Claude).
**NO DeepSeek for folk culture** (user 2026-06-06: lacks the intrinsic Ukrainian-culture knowledge to
catch subtle framing errors — its corpus-tool use was fine, but framing is the risk for culture).
The reviewer MUST hammer the corpus — judging on metrics/structure alone is how a bad artifact ships
(the m20 lesson, MEMORY #M-11).

## Hard gates (deterministic — must pass; quote raw tool output, #M-4)
0. **Framing standard (THE foundational gate — [`FOLK-FRAMING-STANDARD.md`](FOLK-FRAMING-STANDARD.md))** —
   the artifact obeys all 4 pillars and violates none of the NEVER list. A **single** violation = **BLOCK**,
   regardless of every other score:
   - **(a) Christian-heritage-first** — Christian-folk genres (колядки/щедрівки/вертеп/Великдень…) carry the
     Christian meaning at parity/primacy; no «прикладна магія», no "magic-ritual" reduction, no «дохристиянське
     ядро / християнська оболонка» pagan-core-veneer structure; pagan cosmogony is never *the* creation account.
   - **(b) No occult / pagan-as-held-belief** — no demonology/occultism/witchcraft/spell-craft as real practice
     (the Russian "Ukrainians-as-witches/характерники" smear); pre-Christian motifs only as minor poetic/folk-art
     imagery or an explicitly-scholarly older layer, never doctrine, never foregrounded.
   - **(c) Pre-literature identity** — folklore is framed as the oral foundation of *written* Ukrainian literature,
     not as a worldview manual or standalone ethnography; material culture is context, not the subject.
   - **(d) Source provenance** — primary = school-canon textbooks (host the standard school form), secondary =
     ukrlib/wikisource (corroboration); no archaic-dialect reading where a codified school form exists; provenance tagged.
   - If a "pagan-survival / magic" reading is mentioned at all, it is attributed explicitly as a contested/Soviet-era
     frame and balanced — never asserted as neutral fact. Older agrarian strata (spring веснянки/гаївки, купальські)
     appear only as scholarly-noted poetic motifs/formulae, never as the learner-facing thesis; the term
     `продукувальна магія` only inside a cited scholarly note, never as framing and never for колядки/щедрівки.
1. **Quote integrity** — every verbatim folk text (duma line, song lyric, замовляння, proverb) is
   **`verify_quote`-confirmed** (record the score) OR attributed to a named edition and marked
   do-not-quote/paraphrase-only. NEVER an invented or altered line. This is the folk analogue of the
   bio quote gate and is non-negotiable: a "smoothed" Маруся Богуславка line fails the gate.
2. **No Russianisms / surzhyk** — `check_russian_shadow` clean; Ukrainian register correct; no
   Latin-in-Cyrillic homoglyphs (except legit URLs/acronyms).
3. **CEFR / register fit** — `query_cefr_level` consistent with C1+; readable, pedagogically useful,
   not a raw ethnography dump.
4. **Citation / source resolution** — every scholarly attribution (Лановик, Колесса, Грушевський,
   Грінченко…) resolves to a real corpus chunk or a real named edition; no ghost sources, no invented
   collector names.
5. **Public learner register** — rendered lessons, readings, activities, vocabulary, and resources may show public source names/URLs, but must not expose build labels or validation workflow (`source hammer`, `source-first`, `learner-facing`, `chunk_id`, `source_chunk`, corpus/service IDs, `verify_quote`). Student-facing source work is phrased in Ukrainian academic terms such as `першоджерело`, `уривок`, and `джерельна сторінка`.
6. **Schema completeness** — all 10 sections of `folk-dossier-schema.md` present AND the multimodal-
   hook block populated (image `chunk_id`s, named recordings, ritual sequence, motif inventory). An
   empty multimodal block = FIX (it starves GPT's experiential module — the m20 "empty Activities
   tab" failure mode).
6. **Grounding > breadth** — where a Wikipedia-only chunk conflicts with a corpus primary/named
   edition, the corpus wins; Wikipedia-only extraordinary claims flagged, not asserted.

6a. **Learner-page fluency / English leakage** rendered FOLK module pages must read as natural Ukrainian seminar prose. Block English UI labels (`Texts you'll read`), rendered `title_en` glosses in reading lists, English CEFR/register labels (`C1+ learner`), broken syntax, sentence splicing, word salad, and repetitive source/proof boilerplate. Reviewer must read the rendered page like a student, not approve only because source-hygiene gates pass.

## Quality gates (cross-family review — must pass)
7. **Decolonized NPOV (folk-specific)** — honest in every direction:
   - **No Russocentric framing / no appropriation laundering** — esp. bylyny: name the contested
     East-Slavic/Kyivan-inheritance problem, don't inherit the imperial frame.
   - **No romantic-nationalist over-claim** — do NOT present Перун/Велес/Мокоша/**Берегиня** as a
     tidy reconstructed pagan pantheon; Берегиня especially is a modern reconstruction, flag it.
   - **No Soviet-atheist "magic / pagan-core, Christian veneer" framing of Christian-folk genres** —
     this is now the foundational **Gate 0** above (`FOLK-FRAMING-STANDARD.md`): a single «прикладна магія»
     / pagan-core-veneer / pagan-cosmogony-as-creation framing of колядки/щедрівки (or any Christian-folk
     tradition) is a **BLOCK**, not just a quality deduction. See Gate 0 for the full rule and the
     `продукувальна магія` constraint. (Origin: user flag + #3745, superseded by the 2026-06-25 standard.)
   - **No flattening** — regional variation (Гуцул/Бойко/Лемко/Полісся…) surfaced, not pan-Ukrainian-
     smoothed; source disagreements named.
8. **Anti-colonial role is concrete, not slogan** — §7 of the dossier ties THIS genre to specific
   suppression/appropriation/survival facts (e.g. kobzar repression), not a generic "folklore kept
   us alive" line. §8 high-culture bridge is real and corpus-traceable.
9. **Poetics actually explained** — §3 demonstrates the form/technique with the verbatim exemplars,
   not just labels them; a C1+ learner could recognize the genre from the explanation.

## Reviewer's required corpus calls (the "hammer the corpus" mandate)
`verify_quote` on EVERY folk text in the dossier · `check_russian_shadow` on the prose ·
`query_cefr_level` · plus targeted `search_literary` / `search_grinchenko_1907` / `search_heritage` /
`search_text` to independently confirm at least the headline claims and one disputed point. The review
report must quote these tool outputs raw — "I checked the quotes" without the verify_quote scores is a
rejected review (#M-4).

## Verdict
`SHIP` / `FIX-BEFORE-MERGE` (with section/line-anchored fixes) / `BLOCK`. The driver verifies every
fix deterministically (verify_quote / check_russian_shadow / git) before applying. **Folk merge
policy: OPEN PR, do NOT self-merge** — user/orchestrator promotes (until a folk merge-grant is
extended; the bio grant was bio-specific).

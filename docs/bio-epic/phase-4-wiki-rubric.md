# Phase-4 Wiki Quality Rubric (bio #2309)

The review scorecard for every rewritten/new bio wiki. A wiki ships only when it passes **all** gates.
Writer = `compile.py --writer {chosen}` (now dossier-grounded). Reviewer = cross-family to the writer.

## Hard gates (deterministic — must pass)
1. **Subject match** — H1 + body are about the correct figure (`check_wiki_subject`); no ghost/wrong-person content.
2. **Dossier consistency** — every name/date/place/claim is consistent with `docs/research/bio/{slug}.md` (the ground truth). No fact contradicts the dossier.
3. **Citation resolution** — every `[S#]` resolves to a real source chunk; no invented citations (`check_citation_resolution`).
4. **No VERIFY-marker survivors** — `<!-- VERIFY -->` markers resolved or, if `--allow-verify-markers`, logged as explicit review TODOs (advisory), not left silently.
5. **Quote integrity (#M-4)** — every direct quote either `verify_quote`-confirmed (record the score) or attributed to a named edition; NEVER invented or altered (the Ohienko lesson). Dossier "do-not-quote / not-corpus-confirmed" cautions are preserved.
6. **Word floor** — meets the wiki word target for its tier (no padding; sparse-source figures get an honest scarcity note).
7. **Structure** — required sections present; valid MDX/markdown; index entry updated.

## Quality gates (cross-family review — must pass)
8. **Decolonized NPOV** — honest in every direction: no Russocentric framing, no hagiography, no fake-dissident myth; contested points + source disagreements surfaced, not smoothed. Soviet titles/affiliations named honestly.
9. **No Russianisms / surzhyk** — `check_russian_shadow` clean; Ukrainian register correct; no Latin-in-Cyrillic homoglyphs (except legit URLs/acronyms).
10. **CEFR / register fit** — language register appropriate to the article's intended level; readable, pedagogically useful, not a raw fact-dump.
11. **Grounding > breadth** — where a retrieved chunk (esp. Wikipedia-only) conflicts with the dossier, the dossier wins; Wikipedia-only extraordinary claims flagged.

## Verdict
`SHIP` / `FIX-BEFORE-MERGE` (with line-anchored fixes) / `BLOCK`. Driver verifies every fix deterministically
(verify_quote / verify_words / git) before applying. Merge per the bio grant: SHIP + CI green + scope-clean.

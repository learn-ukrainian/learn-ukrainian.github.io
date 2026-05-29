# Claude brief — Bio epic #2309: Ukrainian Helsinki Group founders block

## Scope
Write **6 research dossiers** for core founders of the Ukrainian Helsinki Group (Українська
Гельсінська група, founded 9 Nov 1976) — a major gap in epic #2309 (no Helsinki-Group figures
exist yet under `docs/research/bio/`). These are human-rights resisters persecuted by the Soviet
regime — central to the decolonization narrative.

Figures (one dossier each; verify each is real + not already present before writing):
1. Микола Руденко (Mykola Rudenko) — founder & first head, slug `mykola-rudenko`
2. Олекса Тихий (Oleksa Tykhy) — co-founder, died in camp 1984, slug `oleksa-tykhy`
3. Левко Лук'яненко (Levko Lukianenko) — slug `levko-lukianenko`
4. Іван Кандиба (Ivan Kandyba) — slug `ivan-kandyba`
5. Оксана Мешко (Oksana Meshko) — slug `oksana-meshko`
6. Мирослав Маринович (Myroslav Marynovych) — slug `myroslav-marynovych`
(Do NOT include Vasyl Stus — he's covered on the literary track.)

## Format — follow the EXISTING dossier template EXACTLY
Use a just-merged, clean dossier as your structural model: `docs/research/bio/maks-levin.md` and
`docs/research/bio/hlib-babich.md` (10 numbered sections + "Decolonization self-check"; header block
with Slug/Block/Tier/Issue/Researcher/Completed). Match section headings, depth (~120-140 lines),
and the `**Researcher:**` = the model you actually are. `**Issue:** #2309`. Block = the Helsinki/
dissident block (use the same Block label convention as sibling dossiers).

## ANTI-FABRICATION GUARD (CRITICAL — this is why claude not gemini)
The #1 recurring defect in this corpus is fabricated content. You MUST:
1. **Identities + facts**: verify each figure and every hard fact (dates, camps, sentences, works)
   against `mcp__sources__query_wikipedia` (uk) and/or `mcp__sources__search_*`. No invented dates.
2. **Quotes (§4)**: only include primary-source quotes you can attribute to a real, named source.
   If you cannot verify a quote, omit it — do NOT invent. State the source for each.
3. **§7 Cross-track links**: for EVERY path you cite under an "Existing" bullet, run
   `test -e curriculum/l2-uk-en/<path>` FIRST. If it does not exist, do NOT cite it as Existing —
   either find the real plan (`ls curriculum/l2-uk-en/plans/{hist,lit,bio,istorio}/`) or label it
   "Potential (Phase 2+) candidate". The plans tree uses Ukrainian descriptive slugs
   (e.g. `plans/hist/ukrainska-helsinska-hrupa.yaml`, `plans/hist/destalinizatsiia.yaml`), NEVER
   invented English CEFR-slugs. This is the #2400/#2410 fabrication class — zero tolerance.
4. **Decolonization framing**: clean canonical Ukrainian; frame Soviet persecution accurately; flag
   Russian-imperial transliterations as forbidden forms in §8.

## Verification to report (#M-4 — quote raw)
- For each dossier: the Wikipedia/source line confirming the identity.
- `for p in $(grep -rhoE "plans/[a-z0-9-]+/[a-z0-9-]+\.yaml" docs/research/bio/{mykola-rudenko,oleksa-tykhy,levko-lukianenko,ivan-kandyba,oksana-meshko,myroslav-marynovych}.md | sort -u); do test -e "curriculum/l2-uk-en/$p" && echo "REAL $p" || echo "FAKE $p"; done` → MUST print zero FAKE.

## Steps (dispatch enforces worktree)
1. Confirm worktree root; confirm none of the 6 slugs already exist under `docs/research/bio/`.
2. Research + write the 6 dossiers (use MCP sources tools heavily).
3. Run the §7 `test -e` verification (paste raw, zero FAKE).
4. `git commit` conventional (`docs(bio): Ukrainian Helsinki Group founders — 6 dossiers (#2309)`); Co-Authored-By line.
5. `git push -u origin <branch>` ; `gh pr create --base main`. **No auto-merge.**
Report: PR URL (raw), per-figure identity-verification lines, and the zero-FAKE §7 proof.

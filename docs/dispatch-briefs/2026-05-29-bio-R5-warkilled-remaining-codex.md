# Dispatch — Bio epic #2309 / R5: Block F war-killed/RF-captured, REMAINING 9 (codex)

**Agent:** codex `gpt-5.5`, `--effort xhigh`, `--mode danger`, `--worktree`.
**Epic:** #2309 · **Issue:** #2322 (R5, Tier 5 — Block F war-killed/RF-captured).
**Parallel-safe:** independent of all other lanes (distinct slugs in `docs/research/bio/`).

## Context — 3 of 12 already done (do NOT re-write them)
Already shipped on branch `agy/bio-r5-warkilled-2026-05-28`: **Бабіч (hlib-babich),
Левін (maks-levin), Гурняк (viktor-hurniak)**. You write the REMAINING 9.

## Scope — 9 figures (one ~1500-word dossier each)
Roster surnames from #2322. Resolve EXACT identity + full name against the
canonical PEN Ukraine / RSF / Hero-of-Ukraine / Suspilne / Українська правда
record BEFORE writing, and state the resolution at the top of each dossier:
1. **Сліпак** — Василь Сліпак, opera singer, killed 2016 Donbas (Hero of Ukraine). slug `vasyl-slipak`.
2. **Мацієвський** — Олександр Мацієвський, "Слава Україні" soldier executed by RF 2023 (Hero of Ukraine). slug `oleksandr-matsiievskyi`.
3. **Рощина** — Вікторія Рощина, journalist, died in RF captivity 2024. slug `viktoriia-roshchyna`. **NOT Вікторія Амеліна — do not conflate.**
4. **Асєєв** — Станіслав Асєєв, writer/journalist, held in "Ізоляція" (captured/released). slug `stanislav-asieiev`.
5. **Цибух** — Ілля Цибух ("Most"), combat medic/blogger, killed 2024. slug `illia-tsybukh`. (Confirm given name via Suspilne/UP.)
6. **Єсипенко** — Владислав Єсипенко, RFE/RL contributor, imprisoned in occupied Crimea. slug `vladyslav-yesypenko`. (Confirm given name via RSF.)
7. **Афанасьєв** — [RESOLVE] war-killed/RF-captured figure named Афанасьєв via #2322 sources. slug = canonical per F4.
8. **Козловський** — [RESOLVE] via #2322 sources. slug per F4.
9. **Рибак** — [RESOLVE] via #2322 sources. slug per F4.

**For [RESOLVE] figures: positively identify against PEN/RSF/Hero-of-Ukraine/Suspilne
FIRST. If you cannot positively identify a figure, write a dossier STUB + flag it
`<!-- ORCHESTRATOR-RESOLVE: ambiguous identity -->` rather than inventing biography.
Do NOT guess. Inventing a person is the worst possible failure here.**

## Method — match the pilot bar
- **Template:** `docs/templates/bio-research-dossier-template.md` (F5), section-for-section.
- **Sources (recent figures):** T1 = Hero of Ukraine award records (where applicable);
  T2 = PEN Ukraine, RSF, AP, Українська правда, Suspilne. UA Wikipedia = starting
  point only. **No Russian sources as authoritative — only as quoted primary
  documents (e.g. RF court/POW records cited in UA/international reporting).**
- **Exemplars to match (shape/depth):** `docs/research/bio/pavlo-tychyna.md`,
  `volodymyr-svidzinskyi.md`, and the 3 already-done R5 dossiers on the agy branch.
- **Per-figure ACs (#2317/#2322):** ~1500 words; ≥3 T1/T2 sources; killing/captivity
  mechanism specific (dates, location, documented circumstances, RF unit if known);
  ≥2 primary-source quotes (own words or documented testimony); cross-track links
  (LIT/HIST) where relevant; naming-canonical per F4 (filename = canonical slug);
  image candidates flagged per F7.

## #M-4 — verifiable claims (quote raw output)
- "N dossiers written" → `ls docs/research/bio/*.md` new filenames + `wc -w` raw.
- "identity resolved" → state the resolving source at top of each dossier.
- "commit / PR" → `git log -1 --oneline` + `gh pr view --json url` raw.

## ANTI-FABRICATION (HARD — learned from #2400)
- §7 Cross-track links: every `curriculum/l2-uk-en/plans/.../*.yaml` path cited as
  "existing" MUST be `test -e`-verified first. Cite only existing paths, else
  "Candidate (Phase 2+)". NEVER label a nonexistent plan "Existing."
- No invented people, dates, units, or quotes. Honest "unconfirmed" beats a guess.

## Numbered steps (DISPATCH-BRIEF CHECKLIST)
1. `--worktree` handles isolation; branch `codex/bio-r5-warkilled-remaining-2026-05-29` off `origin/main`. Confirm cwd.
2. Read F5 + F3 + exemplars; resolve all 9 identities; then research + write.
3. Verify each: `wc -w` ≥ ~1500; all template sections; §7 paths `test -e`-verified; identity-resolution line present.
4. Commit, conventional message citing #2322 + #2309. Trailer `X-Agent: codex/bio-r5-warkilled-remaining-2026-05-29`.
5. `git push -u origin codex/bio-r5-warkilled-remaining-2026-05-29`.
6. `gh pr create` — title `docs(bio): R5 war-killed/RF-captured dossiers — remaining 9 (#2322)`; body lists the 9 slugs + word counts + resolution sources + any ORCHESTRATOR-RESOLVE flags. Reference #2322 + #2309.
7. **NO auto-merge** — orchestrator reviews (identity + source-tier + fabrication spot-check).

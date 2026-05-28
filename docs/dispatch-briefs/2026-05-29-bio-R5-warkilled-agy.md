# Dispatch — Bio epic #2309 / R5: Block F war-killed/RF-captured research (agy)

**Agent:** agy (Antigravity, `gemini-3.5-flash-high` — model is TUI-controlled, NO `--model` flag), `--mode danger`, `--worktree`.
**Epic:** #2309 · **Issue:** #2322 (R5, Tier 5 — Block F war-killed).
**Parallel-safe:** independent of all other lanes (distinct slugs in `docs/research/bio/`).

## #M-4 preamble — verifiable claims (quote raw output)
- "N dossiers written" → `ls docs/research/bio/*.md` new filenames + `wc -w` per file raw.
- "commit / PR" → `git log -1 --oneline` + `gh pr view --json url` raw.

## Scope — 12 war-killed / RF-captured figures (one ~1500-word dossier each)
Surnames are the authoritative roster from #2322. Full names are pre-filled ONLY where certain; the rest are marked **[resolve]** — you MUST resolve the exact identity + full name against the canonical PEN Ukraine / RSF / Hero-of-Ukraine / Suspilne record BEFORE writing, and state the resolution at the top of the dossier. Do NOT invent biography; if you cannot positively identify a figure, write the dossier stub + flag it for orchestrator resolution rather than guessing.

1. Василь Сліпак — opera singer (Paris Opera), KIA Donbas 2016.
2. Олександр Мацієвський — the "Слава Україні" POW execution (2023).
3. Левін — **[resolve full name + identity]**
4. Вікторія Рощина — journalist, died in RF captivity (2024). (NOTE: NOT Вікторія Амеліна — a different figure; do not conflate.)
5. Станіслав Асєєв — writer, Izolyatsia concentration-camp survivor/chronicler.
6. Цибух — **[resolve full name + identity]**
7. Владислав Єсипенко — RFE/RL contributor, imprisoned in Russia-occupied Crimea. (Confirm given name via RSF.)
8. Афанасьєв — **[resolve full name + identity]**
9. Гурняк — **[resolve full name + identity]**
10. Бабіч — **[resolve full name + identity]**
11. Козловський — **[resolve full name + identity]**
12. Рибак — **[resolve full name + identity]**

## Method
- **Template:** `docs/templates/bio-research-dossier-template.md` (F5), section-for-section.
- **Sources (recent figures):** T1 = Hero of Ukraine award records (where applicable); T2 = PEN Ukraine, RSF (Reporters Without Borders), AP, Українська правда, Suspilne. UA Wikipedia = starting point only. **No Russian sources as authoritative — only as quoted primary documents (e.g. RF court/POW records cited in UA/international reporting).**
- **Exemplars to match:** `docs/research/bio/pavlo-tychyna.md`, `volodymyr-svidzinskyi.md` (depth/structure; their source tier differs but the dossier shape is the same).

## Per-figure acceptance criteria (from #2317/#2322)
- ~1500 words; ≥3 T1/T2 sources; killing/captivity mechanism specific (dates, location, documented circumstances).
- ≥2 primary-source quotes (their own words, or documented testimony).
- Cross-track links checked (LIT, HIST) where relevant.
- Naming-canonical per F4 (filename = canonical slug).
- Image candidates flagged per F7.

## Numbered steps
1. `--worktree` isolation; confirm cwd = worktree, base `origin/main`.
2. Read F5 + F3 + the exemplars FIRST; then research + write the 12 (verify each name first).
3. Verify each: `wc -w` ≥ ~1500; template sections present; ≥2 primary quotes; name resolved.
4. Commit citing #2322 + #2309; `git push -u origin <branch>`; `gh pr create` listing the 12 + word counts + any name resolutions.
5. **NO auto-merge** — orchestrator reviews (these are recent + sensitive; I verify names + sourcing).

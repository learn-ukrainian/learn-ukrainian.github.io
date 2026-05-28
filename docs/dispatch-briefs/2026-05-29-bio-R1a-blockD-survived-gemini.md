# Dispatch — Bio epic #2309 / R1a: Block D (survived-but-broken) research (Gemini)

**Agent:** gemini `gemini-3.1-pro-preview`, `--mode danger`, `--worktree`.
**Epic:** #2309 · **Issue:** #2317 (R1a, Tier 1a — Block D).
**Parallel-safe:** independent of all other lanes (distinct slugs in `docs/research/bio/`).

## #M-4 preamble — verifiable claims (quote raw output)
- "N dossiers written" → `ls docs/research/bio/*.md` new filenames + `wc -w` per file raw.
- "commit / PR" → `git log -1 --oneline` + `gh pr view --json url` raw.

## Scope — 6 Block D figures (survived-but-broken + camp-returnees)
Already done (do NOT redo): Тичина, Сосюра. Research these 6 (one ~1500-word dossier each):
1. Максим Рильський
2. Юрій Яновський
3. Остап Вишня (Павло Губенко)
4. Микола Бажан
5. Зінаїда Тулуб (camp-returnee)
6. Олександр Ковінька (camp-returnee)

## Decolonization nuance (load-bearing for this block)
These figures **survived via accommodation / capitulation** (or returned from the camps). Present the survival mechanism **honestly** — neither condemning nor whitewashing. The epic exists partly to RESTORE this category the original seed excluded. State plainly: what was demanded, what was conceded, what was preserved. Honest source-disagreement flagging where historians differ.

## Method — match the R1a pilot bar exactly
- **Template:** `docs/templates/bio-research-dossier-template.md` (F5), section-for-section.
- **Source tiers:** `docs/best-practices/bio-research-source-tiers.md` (F3). T1 = НТШ / ЕСУ / Енциклопедія Українознавства; T2 = HURI / CIUS. UA Wikipedia = starting point only. **Russian/Soviet sources ONLY as quoted primary documents, NEVER authoritative claims.**
- **Exemplars to match:** `docs/research/bio/pavlo-tychyna.md`, `volodymyr-sosiura.md` (same Block D pattern), plus `mykhailo-drai-khmara.md`, `volodymyr-svidzinskyi.md`.

## Per-figure acceptance criteria (from #2317)
- ~1500 words; ≥3 T1/T2 sources cited; oppression/accommodation mechanism specific (dates, document refs).
- ≥2 primary-source quotes.
- Cross-track links checked (LIT, HIST).
- Naming-canonical applied per F4 (filename = canonical slug).
- Image candidates flagged per F7.

## Numbered steps
1. `--worktree` isolation; confirm cwd = worktree, base `origin/main`.
2. Read F5 + F3 + the exemplars FIRST; then research + write the 6.
3. Verify each: `wc -w` ≥ ~1500; all template sections present; ≥2 primary quotes.
4. Commit citing #2317 + #2309; `git push -u origin <branch>`; `gh pr create` listing the 6 + word counts.
5. **NO auto-merge** — orchestrator reviews.

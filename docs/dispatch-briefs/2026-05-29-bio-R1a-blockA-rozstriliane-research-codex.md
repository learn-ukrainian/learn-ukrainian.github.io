# Dispatch — Bio epic #2309 / R1a: Block A research dossiers (Розстріляне Відродження)

**Agent:** codex `gpt-5.5`, `--effort high` (deep-research), `--mode danger`, `--worktree`.
**Epic:** #2309 (Bio track expansion — 130 Russia-oppressed Ukrainian patriots) · **Issue:** #2317 (R1a, Tier 1a).
**Parallel-safe:** independent of the V7.2 code leg (different files: `docs/research/bio/` vs `scripts/build/`).

## #M-4 preamble — verifiable claims (quote raw output, never "I checked")
- "N dossiers written" → `ls docs/research/bio/*.md | wc -l` + the new filenames raw.
- "each ≥ ~1500 words" → `wc -w docs/research/bio/<slug>.md` raw per file.
- "commit landed / PR opened" → `git log -1 --oneline` + `gh pr view --json url` raw.

## Scope — the 10 remaining Block A figures (Розстріляне Відродження)
Already done in the R1a pilot (do NOT redo): Драй-Хмара, Свідзінський, Тичина, Сосюра.

Research these 10 (one ~1500-word dossier each):
1. Михайль Семенко
2. Микола Вороний
3. Михайло Яловий
4. Григорій Епік
5. Валер'ян Поліщук
6. Олекса Влизько
7. Марко Вороний
8. Мирослав Ірчан
9. Антін Крушельницький
10. Софія Налепинська-Бойчук

## Method — match the pilot bar exactly
- **Template:** follow `docs/templates/bio-research-dossier-template.md` (F5) section-for-section.
- **Source tiers:** obey `docs/best-practices/bio-research-source-tiers.md` (F3). T1 = NTSh / ЕСУ / Енциклопедія Українознавства; T2 = Harvard URI / CIUS / Carleton. UA Wikipedia = starting point only, never endpoint. **Russian/Soviet sources allowed ONLY as quoted primary documents (e.g. NKVD case files cited in modern UA scholarship), NEVER as authoritative claims about the figure.**
- **Exemplars to match:** `docs/research/bio/mykhailo-drai-khmara.md`, `volodymyr-svidzinskyi.md`, `pavlo-tychyna.md`, `volodymyr-sosiura.md` — same depth, ≥4 T1/T2 sources, hard archival refs (arrest/execution records, case numbers) where they exist, and **honest flagging of source disagreements** (the pilot did this — keep it).
- **Naming/slugs:** apply the F4 naming-canonical + transliteration rules (`docs/best-practices/` naming doc); output filename = canonical slug.

## Output
- `docs/research/bio/<slug>.md` per figure (~1500 words; depth over padding).
- Do NOT write plan YAMLs (Phase 2) or wiki (Phase 4) — research dossiers only.

## Numbered execution steps (DISPATCH-BRIEF CHECKLIST)
1. `--worktree` handles the worktree; confirm cwd is the worktree, base `origin/main`.
2. Read F5 template + F3 source-tier doc + the 4 exemplar dossiers FIRST; then research + write the 10.
3. Verify each: `wc -w` ≥ ~1500; template sections all present.
4. `.venv/bin/ruff check` — N/A (markdown only); skip.
5. Commit, conventional message citing #2317 + #2309.
6. `git push -u origin <branch>`.
7. `gh pr create` — cite #2317, #2309; list the 10 figures + word counts.
8. **NO auto-merge** — orchestrator reviews (decolonization + source-tier spot-check).

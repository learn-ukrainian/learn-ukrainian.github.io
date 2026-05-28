# Dispatch — Bio epic #2309 / R1b: Block C émigré, sub-batches C.3+C.4+C.5 (Claude)

**Agent:** claude `claude-opus-4-8`, `--effort xhigh` (deep-research), `--mode danger`, `--worktree`.
**Epic:** #2309 · **Issue:** #2318 (R1b, Tier 1b — Block C émigré tradition).
**Parallel-safe:** independent of the V7.2 leg + the codex Block-A lane + the Claude C.1+C.2 lane (distinct slugs in `docs/research/bio/`).

## #M-4 preamble — verifiable claims (quote raw output)
- "N dossiers written" → `ls docs/research/bio/*.md` new filenames + `wc -w` per file raw.
- "commit / PR" → `git log -1 --oneline` + `gh pr view --json url` raw.

## Scope — 15 émigré figures (one ~1500-word dossier each)
**C.3 МУР / postwar (6):** Василь Барка, В. Домонтович (Віктор Петров), Ігор Костецький, Докія Гуменна, Юрій Косач, Михайло Орест
**C.4 NY Group (5):** Богдан Бойчук, Юрій Тарнавський, Емма Андієвська, Богдан Рубчак, Віра Вовк
**C.5 scholars (4):** Омелян Пріцак, Дмитро Чижевський, Юрій Лавриненко, Олекса Воропай

⚠️ **DO NOT include Улас Самчук** — flagged (occupation-era publication record); handled separately.

## Method — match the R1a pilot bar exactly
- **Template:** `docs/templates/bio-research-dossier-template.md` (F5), section-for-section.
- **Source tiers:** `docs/best-practices/bio-research-source-tiers.md` (F3). **For Block C, T1 = HURI (Harvard URI), CIUS, Сарсель Енциклопедія Українознавства** — less reliance on UA-side encyclopedias. UA Wikipedia = starting point only. **Russian/Soviet sources ONLY as quoted primary documents, NEVER authoritative.**
- **Exemplars to match:** `docs/research/bio/mykhailo-drai-khmara.md`, `volodymyr-svidzinskyi.md`, `pavlo-tychyna.md`, `volodymyr-sosiura.md` — same depth, ≥4 T1/T2 sources, honest flagging of source disagreements.
- **Special note (C.3):** В. Домонтович = pen name of Віктор Петров (note the espionage-controversy historiography honestly). C.5 scholars: Пріцак/Чижевський have rich HURI/academic source trails — lean on those.
- **Naming/slugs:** apply F4 transliteration rules; filename = canonical slug.

## Output
- `docs/research/bio/<slug>.md` per figure (~1500 words). Research dossiers ONLY — no plan YAMLs, no wiki.

## Numbered steps (DISPATCH-BRIEF CHECKLIST)
1. `--worktree` handles isolation; confirm cwd = worktree, base `origin/main`.
2. Read F5 + F3 + the 4 exemplars FIRST; then research + write the 15.
3. Verify each: `wc -w` ≥ ~1500; all template sections present.
4. Commit, conventional message citing #2318 + #2309.
5. `git push -u origin <branch>`.
6. `gh pr create` — cite #2318, #2309; list the 15 figures + word counts.
7. **NO auto-merge** — orchestrator reviews (source-tier + decolonization spot-check).

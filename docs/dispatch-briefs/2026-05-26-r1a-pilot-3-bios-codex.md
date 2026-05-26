# 2026-05-26 — R1a pilot: 3 research dossiers (Codex)

> Dispatch target: `codex --mode danger --worktree`, model `gpt-5.5` (default), effort `xhigh`.
> Base: `origin/main` (currently `6597f33752`, post PR #2350).
> Tracking issue: #2317 (R1a — Tier 1a, Block A+D).
> Scope: PILOT (3 figures), not full R1a. Orchestrator (Claude) will scale after reviewing your output.

## Why this exists

Epic #2309 Phase 0 (foundation docs/scripts/policies) shipped 2026-05-26. Phase 1 (research dossiers, 130 figures across 6 tiers) is now unblocked. Before fanning out across 5 agent classes, the orchestrator is piloting one Codex dispatch on 3 R1a figures to validate the F5 template + source-tier policy + decolonization checklist holds end-to-end. Your 3 dossiers will be reviewed against the template by Claude; the outcome decides the scale plan.

## What to produce — 3 dossiers

Write three research dossiers to `docs/research/bio/{slug}.md` per F5 template (`docs/templates/bio-research-dossier-template.md`). Each ~1500 words (acceptable range 1200-2000). Each spans a different oppression pattern so the template gets stress-tested:

| Slug | UA name | Block | Oppression pattern |
|---|---|---|---|
| `mykhailo-drai-khmara` | Михайло Опанасович Драй-Хмара | A | Camp death (Kolyma 1939; neoclassicist «ґроно п'ятірне») |
| `volodymyr-svidzinskyi` | Володимир Євтимович Свідзінський | A | NKVD execution during 1941 retreat (burned alive in barn near Bryansk) |
| `volodymyr-sosiura` | Володимир Миколайович Сосюра | D | Censorship/professional destruction (1951 Pravda attack «Об идеологических извращениях…» over «Любіть Україну») |

Slugs are FIXED per the 130-figure appendix in `docs/audits/bio-track-gap-audit-2026-05-26.md` — do not rename them.

## Authority hierarchy (HARD — per #M-4)

Every non-trivial fact in your dossier must trace to a source you LOOKED AT, not a source you remember training on. The source-tier policy at `docs/best-practices/bio-research-source-tiers.md` governs:

1. **Tier 1 (cite as ground truth):** НТШ, ЕСУ, ЕУ Сарсель (Кубійович), ЕІУ.
2. **Tier 2 (institutional):** HURI, CIUS, EURUS, ГДА СБУ (NKVD/MGB/KGB files), Інститут української археографії.
3. **Tier 3 (encyclopedic):** UA Wikipedia (starting point only; corroborate before claiming).
4. **Tier 4 (modern UA scholarly post-1991):** peer-reviewed UA journals.
5. **Tier 5 (general web):** used only with T1-T4 corroboration.

You MUST cite ≥3 Tier 1/Tier 2 sources per dossier. If you cannot find 3 Tier 1/2 sources for a figure, STOP and report — do not pad with Tier 5.

For each figure, the following are MANDATORY:
- §2 Oppression mechanism with specific dates, agency, document/case reference, location.
- §4 ≥2 primary-source quotes IN UKRAINIAN (not translated through Russian) with source citation (title, year, page).
- §6 Contested points (≥1 modern UA scholarly debate, ≥1 Russian-disinformation angle if applicable).
- §8 Naming-canonical with slug + aliases + FORBIDDEN Russian-imperial transliterations.

## Tool usage (#M-4 deterministic-over-hallucination)

Available MCP tools (`mcp__sources__*`):

| Goal | Tool | Notes |
|---|---|---|
| Search across all sources (preferred entry point) | `search_sources` | Hits textbooks, literary, Wikipedia, external, ukrainian_wiki |
| Targeted textbook chunk lookup | `search_text` + `get_chunk_context` | For grade-5-11 UA-lit textbooks |
| Literary primary sources | `search_literary` | 125K chunks; chronicles, poetry, legal texts |
| UA Wikipedia | `query_wikipedia` | Starting point; never citation endpoint |
| Verify a direct quote | `verify_quote(text, source)` | Use BEFORE quoting any primary-source line |
| Verify a claim attribution | `verify_source_attribution(source, claim)` | Use BEFORE saying "X said Y in source Z" |
| Pre-Soviet attestation | `search_grinchenko_1907` | For 1907 lexicographic record |
| Heritage defense (archaism vs Russianism) | `search_heritage` | For any flagged word form |
| External web search | `search_external` | T2-T5 sources outside the corpus |
| Style/calque check | `search_style_guide` (Антоненко-Давидович) | For register notes in §5 |

For each fact-bearing sentence in your dossier, you should be able to point at the tool call that grounded it. Selective verification is silent fabrication.

## Process per figure (~3h each)

1. **Identify** — confirm slug, UA canonical name, life dates from ЕСУ + ЕУ Сарсель. If sources disagree on a date, RECORD the disagreement in §1; do not silently resolve.
2. **Oppression mechanism (§2)** — find the NKVD case number, MGB file ID, court reference, or other primary-source anchor. ГДА СБУ is the canonical repository for declassified case files (`docs/best-practices/bio-research-source-tiers.md` mentions this). If you can't find a document reference, search literature on the figure's death/exile until you find one OR document why no such reference exists.
3. **Major works (§3)** — 5-15 works, chronological. Note suppressed/destroyed/posthumous works specifically.
4. **Primary quotes (§4)** — ≥2 quotes verified via `verify_quote`. If only Russian-language versions exist (red flag), find the UA original or report you couldn't.
5. **Language register (§5)** — pedagogical note for L2 learners; CEFR readiness.
6. **Contested points (§6)** — anti-hagiography section; debates in modern UA scholarship; Russian disinformation angle if applicable. NOTE: Сосюра's Block-D case has notable Russian-Imperial framing online; address it.
7. **Cross-track links (§7)** — grep `curriculum/l2-uk-en/plans/lit/` for existing references; grep `curriculum/l2-uk-en/plans/hist/`. If LIT/HIST gaps surface, file as `bio-expansion-followup` issue (DO NOT add modules unilaterally — audit immutability rule).
8. **Naming-canonical (§8)** — slug + EN canonical (BGN/PCGN 2010) + UA canonical + aliases + FORBIDDEN list (Russian-imperial transliterations like `Drai-Khmara`/`Свидзинский`/`Сосюра` Russified — these must be tracked, not used).
9. **Image candidates (§9)** — PD/CC portrait if attestable, per `docs/best-practices/bio-image-rights.md`.
10. **Sources used (§10)** — tier-labeled bibliography. Every citation MUST be one you accessed.

## Decolonization self-check (REQUIRED before commit)

Per `docs/audits/bio-decolonization-checklist.md`. Scan each dossier for:
- No Russocentric framing
- No Russian-imperial transliterations in body text
- No Russocentric periodization (Civil War vs Українська революція 1917-1921)
- No uncritical Soviet propaganda terms in body text
- No "lost his life" euphemisms for documented executions
- All place names use modern UA canonical form
- Holodomor as Holodomor
- Crimea/2014/2022 as Russian aggression where applicable

## Numbered execution steps

1. `git worktree add ~/projects/.worktrees/dispatch/codex/r1a-pilot-3-bios-2026-05-26 -b codex/r1a-pilot-3-bios-2026-05-26 origin/main` from `/Users/krisztiankoos/projects/learn-ukrainian`. CD into the worktree.
2. Read these references in order before writing:
   - `docs/templates/bio-research-dossier-template.md` (the F5 template)
   - `docs/research/bio/pavlo-tychyna.md` (the F5 worked example — same template applied to Block D Тичина)
   - `docs/best-practices/bio-research-source-tiers.md` (T1-T5 authority policy)
   - `docs/best-practices/bio-naming-canonical.md` (slug + transliteration rules)
   - `docs/best-practices/bio-image-rights.md` (image policy)
   - `docs/audits/bio-decolonization-checklist.md` (decolonization self-check)
   - `docs/audits/bio-track-gap-audit-2026-05-26.md` § "130-figure appendix" (slug + block confirmation for your 3 figures)
3. For each figure, run the 10-step research process above. Use MCP tools, not memory. Aim for ~1500 words/dossier (acceptable 1200-2000).
4. Write each dossier to `docs/research/bio/{slug}.md`. Three files total: `mykhailo-drai-khmara.md`, `volodymyr-svidzinskyi.md`, `volodymyr-sosiura.md`.
5. Self-verify each dossier against the F5 acceptance criteria (the 8 checkboxes at the top of the template). For any criterion you can't meet, leave the checkbox unchecked AND document why in the dossier itself (not just in the PR body).
6. Run the decolonization self-check on each dossier. Document the result in the PR body.
7. `git add docs/research/bio/*.md` then commit with conventional message: `feat(bio-research): R1a pilot — 3 dossiers (Драй-Хмара, Свідзінський, Сосюра)`. Include `X-Agent: codex/r1a-pilot-3-bios-2026-05-26` trailer.
8. `git push -u origin codex/r1a-pilot-3-bios-2026-05-26` then `gh pr create` with title `feat(bio-research): R1a pilot — 3 dossiers (Драй-Хмара, Свідзінський, Сосюра)` and a body that includes: (a) per-figure word count, (b) per-figure ≥3-T1/T2 sources count, (c) per-figure primary-quote count, (d) decolonization self-check result, (e) any acceptance-criterion you couldn't meet + why, (f) "DO NOT MERGE — pilot review pending" warning.

## What we are testing

Beyond the figures themselves, this pilot validates:

- **F5 template** — does it surface the right structure across 3 different oppression patterns?
- **Source-tier policy enforcement** — can a single dispatch reliably produce ≥3 T1/T2 cites per figure?
- **Primary-quote discipline** — can you find ≥2 UA-original primary quotes per figure without translating through Russian?
- **Decolonization self-check** — does it actually catch issues at writer-time or only at reviewer-time?
- **Tool-backed evidence (#M-4)** — can you ground every fact-bearing sentence to a tool call?

Report any friction with the template, the source policies, or the decolonization checklist in the PR body. The orchestrator will fold those into Phase 0 retrofits before scaling to the remaining 127 figures.

## Boundaries

- Do NOT write plan YAMLs (Phase 2).
- Do NOT modify curriculum.yaml (Phase 3).
- Do NOT compile wiki articles (Phase 4).
- Do NOT touch any file outside `docs/research/bio/` plus the optional `bio-expansion-followup` issues you file if you surface LIT/HIST gaps in §7.
- Do NOT auto-merge.

## On unexpected blockers

If you can't satisfy the ≥3-T1/T2-source requirement for a figure, STOP that figure (commit the partial dossier with checkboxes left unchecked + explanation) and surface in the PR body. The orchestrator will adjudicate whether to keep the figure or swap it.

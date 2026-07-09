# Bio Research Dossier — Template

**Use this template for every figure researched in BIO Phase 1** — both the original roster (R1a-R5, issues #2317-#2322 under epic #2309) and the 2026-06-29 **+77 expansion** roster (umbrella #2535; first dossiers tracked as new sub-issues, NOT retrofits of #2317-#2322).

**Target length:** ~1500 words (range: 1200–2000 acceptable).
**File location:** `docs/research/bio/{slug}.md`
**SSOT for module ordering / slugs:** `curriculum/l2-uk-en/curriculum.yaml` (`levels.bio.modules`; derive the live slug count from the manifest rather than hard-coding it).
**Slug source (by roster):**
- Original roster: the 130-figure appendix in `docs/audits/bio-track-gap-audit-2026-05-26.md` (per #2313).
- The dated expansion roster: `docs/audits/bio-ukrainian-expansion-research-2026-06-29.md` and the readiness inventory `docs/audits/bio-readiness-matrix-2026-06-29.md`. Do NOT use their historical totals as the live SSOT.

> **No-module-writing gate (#2535 / #4006 prompt gate before #4005).** A dossier is the FIRST base-prep artifact. Writing a dossier is permitted only after the slug is promoted out of the readiness gate; do NOT write the plan YAML, site doc, or wiki packet from the same pass. Promotion order is fixed: dossier → `plans/bio/{slug}.yaml` → site/wiki. For the +77, honor the canonicity-over-currency and HIST-alignment constraints recorded in the expansion memo (see §6 and §7 below).

**Fleet/worker rule for dossier batches.** A worker drafting this template owns
exactly one file: `docs/research/bio/{slug}.md`. The worker may perform
read-only source discovery and path checks, but must not stage, commit, create
PRs, request independent review, merge, or edit any other file. The BIO
orchestrator reviews and integrates worker output, runs deterministic checks,
routes Claude/AGY (Gemini-family via bridge)/other independent review as
needed, and merges in BIO order. Summarize long source packets or logs
instead of pasting them into agent-to-agent prompts.

**Token-economy rule.** Use deterministic commands before model calls: `rg`,
`test -e`, `npx markdownlint-cli2`,
`.venv/bin/python scripts/audit/lint_bio_dossier_xref.py`, `git diff --check`,
and `.venv/bin/python scripts/audit/lint_agent_trailer.py`. Do not ask models
to re-check facts that local tools can prove. A model review should focus on
source interpretation, Ukrainian-centered framing, contested points, and
overclaiming risk.

**Acceptance criteria for closing the research ticket on a figure**:
- [ ] All 10 sections completed (skip a section only if NA — document why)
- [ ] ≥3 Tier 1/Tier 2 sources cited (per `bio-research-source-tiers.md`)
- [ ] Oppression mechanism is specific (dates, document refs, court case numbers, location)
- [ ] ≥2 primary-source quotes from the figure's own work or recorded speech
- [ ] Cross-track links: every path listed as "Existing" VERIFIED present (`test -e`); unbuilt connections listed under "Candidate (Phase 2+)", NEVER as "Existing" — fabricated/assumed paths = gate failure
- [ ] Naming-canonical applied (slug + aliases listed per #2313)
- [ ] Image candidate(s) identified per #2316 image-rights policy
- [ ] Decolonization checklist (#2310) self-applied during writing
- [ ] **Canonicity-over-currency (+77 roster):** for a LIVING figure, build only on completed, settled contributions — NO predictive "future national leader" framing. Do NOT open a dossier for a current-wartime watchlist figure (Берлінська, Вишебаба, Чорногуз, Чмут, Федоров, Буданов, Стерненко, Христов) or for held cases (Залужний); these are excluded from new BIO additions per `docs/audits/bio-ukrainian-expansion-research-2026-06-29.md`.
- [ ] **HIST-alignment (+77 roster):** for state-building, UNR/ZUNR, dissident, independence, and wartime figures, align the historical frame with HIST rather than inventing one (memo Sequencing Decision). Record the HIST-alignment check in §6/§7.

---

## Template — copy this exactly

```markdown
# {Full canonical UA name} — Research Dossier

**Slug:** `{slug}`
**Block:** {original roster: A | B | C.1 | C.2 | C.3 | C.4 | C.5 | D | E.1 | E.2 | F | G | H | I | J | K — OR +77 expansion-group name from the 2026-06-29 memo, e.g. "Social resistance", "State-building", "Language/ethnography", "Music", "Theatre/visual culture", "Literary/civic"}
**Tier:** {1a | 1b | 2 | 3 | 4 | 5}
**Issue:** #{R-ticket number}
**Researcher:** {agent name + model}
**Completed:** {YYYY-MM-DD}

## 1. Verified facts

- **Full name (UA, canonical):** {full UA form with patronymic where attested}
- **Pseudonyms / aliases:** {list — including Russian-imperial transliterations that body text must NOT use}
- **Born:** {date} | {place} | {then-political-entity}
- **Died:** {date} | {place} | {then-political-entity} | {cause if verified}
- **Family / education key facts:** {3-5 lines max}

Cite at least 2 sources for each non-trivial fact (birth date, death date, oppression mechanism). Disagreements between sources MUST be flagged, not silently resolved.

## 2. Oppression mechanism

This is the load-bearing section. Required specificity:
- **What happened:** {arrested / exiled / executed / forced into emigration / show-trial / persecuted / disappeared / assassinated}
- **When (specific dates):** {YYYY-MM-DD; if uncertain, give the range and source of uncertainty}
- **By whom (specific Russian/Soviet/RF agency):** {Imperial gendarmerie | Cheka | OGPU | NKVD | MGB | KGB | FSB | military unit}
- **Document references:** {court case number, NKVD file ID, show-trial name, etc. — quote the citation, not a paraphrase}
- **Mechanism specifics:** {1-3 paragraphs of factual detail}
- **What survived / what was destroyed:** {if applicable — manuscripts destroyed, family pursued, etc.}

If oppression was indirect (censorship, blacklist, professional destruction) rather than physical: same specificity rules apply. Name the document, the date, the body.

## 3. Major works

5-15 major works, in chronological order:
- `{Year}` — *{title}*, {genre / form}, {publisher / venue}. {1-line significance}

Note any work suppressed, destroyed, or published posthumously.

## 4. Primary-source quotes (≥2 required)

Quote directly from the figure's own work or recorded speech. Each quote:
- Full canonical UA text (with proper Ukrainian orthography)
- Source: title, year, page or section
- 1-2 line context on why this quote matters pedagogically

Do NOT use translations through Russian. If you only have a Russian-language version of a UA figure's quote, treat that as a red flag and find the UA original.

## 5. Language register

Pedagogical note for L2 learners:
- **Register:** {high modernist | folk-dialect | colloquial | bureaucratic | mixed}
- **CEFR readiness for full reading:** {A2 | B1 | B2 | C1 | C2}
- **Lexicon notes:** {neologisms, dialectisms, archaisms, calques to watch}
- **Stylistic features:** {alliteration, neologistic compounding, specific poetic devices}

This section drives where in the curriculum the figure's work fits and at what level learners should encounter them.

## 6. Contested points

For every figure, list:
- **What's debated in modern UA scholarship:** {1-3 bullet points}
- **What gets simplified in popular memory:** {1-2 bullet points}
- **Where modern Russian disinformation attacks them (if applicable):** {1-2 bullet points}
- **Polish / Jewish / other-perspective considerations (if applicable):** {1-2 bullet points}

For Block G (politically charged): this section is mandatory and must be longer (300+ words). See `docs/best-practices/politically-charged-bios.md` (#2311).

## 7. Cross-track links

> **VERIFY BEFORE ASSERTING (hard rule — fabricated paths = gate failure / hallucination class per audit §methodology-lesson-1).**
> List a path under "Existing" ONLY after confirming it exists (`test -e <path>`). **Bio plans (`plans/bio/*.yaml`) are Phase 2 and almost none exist yet** — do NOT list them as "Existing." A research dossier at `docs/research/bio/{slug}.md` is NOT a plan at `plans/bio/{slug}.yaml`; do not confuse the two. Anything not yet built goes under "Candidate," never "Existing."

- **Existing LIT modules (VERIFIED present via `test -e`):**
  - {path to plans/lit/...yaml — only if it actually exists}
- **Existing HIST modules (VERIFIED present via `test -e`):**
  - {path to plans/hist/...yaml — only if it actually exists}
- **Candidate cross-track connections (to create/verify in Phase 2+ — NOT existing files):**
  - {figure / topic + why connected. Bio-to-bio links live HERE until Phase 2 builds the plans. These are research suggestions, not assertions of existing artifacts.}
- **Potential LIT additions surfaced by this research:**
  - {if any — file as `bio-expansion-followup` issue, do NOT add unilaterally per audit immutability rule}

## 8. Naming-canonical

Per `docs/best-practices/bio-naming-canonical.md` (#2313):

- **Slug:** `{slug}`
- **EN canonical (BGN/PCGN 2010):** {form}
- **UA canonical (with patronymic if attested):** {form}
- **Aliases (track these for `aliases:` YAML field):** {list}
- **Forbidden forms (Russian-imperial transliterations to flag in body text):** {list}

## 9. Image candidates

Per `docs/best-practices/bio-image-rights.md` (#2316):

- **Best PD/CC portrait:** {URL or path | license | source}
- **Backup candidates:** {2-3 alternatives}
- **If no PD/CC portrait exists:** note + propose fallback strategy
- **Era-appropriate context image (e.g. NKVD case folder cover, era newspaper):** {if useful}

## 10. Sources used

List with tier labels per `docs/best-practices/bio-research-source-tiers.md` (#2312):

**Tier 1 (authoritative):**
- {citation} | {URL or library reference} | {accessed date}

**Tier 2 (institutional):**
- {citation}

**Tier 3 (encyclopedic):**
- {citation}

**Tier 4 (modern scholarly post-1991):**
- {citation}

**Tier 5 (general web):**
- {citation — used only with T1-T4 corroboration}

**Primary-source documents accessed (NKVD files, KGB files, court records):**
- {citation}

---

## Decolonization self-check (run before submitting)

Per `docs/audits/bio-decolonization-checklist.md` (#2310). At minimum, scan the dossier for:
- [ ] No Russocentric framing
- [ ] No Russian-imperial transliterations in body text (only allowed in `aliases:` field labeled FORBIDDEN)
- [ ] No Russocentric periodization (Civil War vs Українська революція, etc.)
- [ ] No uncritical Soviet propaganda terms (буржуазний націоналізм in body text)
- [ ] No "lost his life" euphemisms for documented executions
- [ ] All place names use modern UA canonical form (Kyiv not Kiev, etc.)
- [ ] Holodomor referenced as Holodomor, not "Soviet famine"
- [ ] Crimea/2014/2022 events framed as Russian aggression where applicable

```

---

## Why each section is mandatory

- **§1 verified facts** — without specific dates / places, the dossier is folklore not history
- **§2 oppression mechanism** — this is THE point of the bio; vague "was persecuted" fails
- **§3 major works** — pedagogical anchor; needed for cross-track links
- **§4 primary-source quotes** — establishes scholarly credibility + gives writers material to work with
- **§5 language register** — drives CEFR placement; without this, learners can't access the work
- **§6 contested points** — anti-hagiography; protects against caricature pedagogy
- **§7 cross-track links** — ensures the bio integrates with existing LIT/HIST coverage
- **§8 naming-canonical** — slug discipline; prevents URL collisions
- **§9 image candidates** — Phase 4 wiki articles will reference these
- **§10 sources used** — scholarly accountability; verifies tier policy adherence

---

## Worked example

See [`docs/research/bio/pavlo-tychyna.md`](../research/bio/pavlo-tychyna.md) — the F5 worked example. This demonstrates the template applied to a Tier 1a figure (Block D survived-but-broken).

Future dossier-writers should read the Тичина example before writing their first dossier — it shows the expected depth and tone.

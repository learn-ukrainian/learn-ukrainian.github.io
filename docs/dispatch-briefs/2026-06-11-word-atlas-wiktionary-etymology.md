# Dispatch brief — Word Atlas roadmap B phase 2: Wiktionary etymology fallback

**Owner lane:** Word Atlas (Claude orchestrator). **Issue:** #2882 (populate Word Atlas).
**Agent:** codex (gpt-5.5, xhigh). **Mode:** danger + worktree. **No auto-merge.**

## Objective
Fill etymology for the single-word A1 lemmas that **Goroh and ЕСУМ both miss**, using a
fallback ingest from the real `uk.wiktionary` XML dump. Etymology coverage is **42/63** on
main; this should lift the **single-word** coverage to near-complete.

## CRITICAL scoping (root-caused by Claude 2026-06-11 — do NOT skip)
The 21 lemmas without etymology are **not** a uniform source gap. They split:

### A) 9 multi-word phrases — DO NOT chase etymology
`До побачення`, `Добрий вечір`, `Добрий день`, `Доброго ранку`, `На все добре`,
`Рада тебе бачити`, `Радий тебе бачити`, `після цього`, `як справи`.
These are **compositional** — no single Wiktionary entry has a unified etymology for a
greeting phrase. **Skip any lemma containing whitespace** in the Wiktionary fetch loop.
Additionally, **exclude whitespace-containing lemmas from the etymology-coverage denominator**
in any progress/report output so the metric reflects reality (a phrase legitimately has no
single etymology). Do not invent a stitched-together etymology for them.

### B) 12 single words — THE REAL TARGET
`вмиватися`, `добре`, `збиратися`, `комп'ютер`, `навчатися`, `нормально`, `одягатися`,
`повертатися`, `пізно`, `робота`, `сьома`, `чудово`.
Notes that informed the source choice:
- These are mostly **derived/inflected forms** whose etymological base IS in ЕСУМ
  (`чудово`→чудо, `пізно`→пізній, `сьома`→сім, `робота`→робити, `збиратися`→брати,
  `одягатися`→одяг, `повертатися`→вертати) — but ЕСУМ is keyed by base lemma and our
  exact-match lookup misses them. uk.wiktionary has clean per-lemma etymology entries that
  resolve this directly.
- A residual tail is genuinely modern/absent from ЕСУМ: `комп'ютер` (borrowing),
  `нормально`/`добре` (adverbs whose bases are weak/absent in our noisy ЕСУМ ingest),
  `вмиватися`/`навчатися` (basic verb `мити`/`учити` absent as clean ЕСУМ lemma keys).
  uk.wiktionary covers these where ЕСУМ cannot — which is exactly why Wiktionary is the
  right fallback source here.

## Vetted technical approach (Codex + agy consulted 2026-06-10 — unchanged)
- Use the **real `ukwiktionary` XML dump**, pinned by date + sha256 checksum.
  **NOT Kaikki** — Codex verified Kaikki's "Ukrainian" = *English* Wiktionary's Ukrainian
  entries, not uk.wiktionary. (Dump URL form:
  `https://dumps.wikimedia.org/ukwiktionary/<DATE>/ukwiktionary-<DATE>-pages-articles.xml.bz2`.)
- Extract the `== Етимологія ==` section **offline** (`mwparserfromhell` preferred, or a
  conservative template stripper/whitelist). Keep raw wikitext for audit; render cleaned
  plain text for display. Watch for: multiple languages per page (keep only the Ukrainian
  `== Українська ==` section), homographs, numbered etymologies, templates `{{etyl}}` /
  `{{похідне}}` / `{{ety}}`.
- Ingest into a **new `wiktionary_etymology` table** in the shared `data/sources.db`.
  ⚠️ A `wiktionary` table already exists (50k rows, NO etymology) at
  `scripts/wiki/build_sources_db.py:~197` — **do not collide**; use `wiktionary_etymology`.
- Idempotent upsert keyed by lemma + content_hash, mirroring the shape of
  `goroh_etymology` (`requested_lemma, headword, etymology_text, source_url, retrieved_at,
  content_hash`). Add a `lang`/`section_raw` column if useful for audit.

## Files to model on / wire into
- **Model the ingest** on `scripts/ingest/goroh_etymology_ingest.py` (14KB; idempotent
  table create + upsert + CLI). New file: `scripts/ingest/wiktionary_etymology_ingest.py`.
- **Wire precedence** in `scripts/lexicon/enrich_manifest.py`. `_etymology()` at **line 536**
  is currently:
  ```python
  return _goroh_etymology(conn, lemma) or _esum_etymology(conn, lemma)
  ```
  Add a third tier → **Goroh → ЕСУМ → Wiktionary** (gap-fill only; never overrides Goroh/ЕСУМ):
  ```python
  return (_goroh_etymology(conn, lemma)
          or _esum_etymology(conn, lemma)
          or _wiktionary_etymology(conn, lemma))
  ```
  Implement `_wiktionary_etymology(conn, lemma)` next to `_esum_etymology` (line ~510),
  **reusing `_etymology_lookup_variants(lemma)`** (line 470) for lemma-variant matching.
  Source label e.g. `Вікісловник (uk.wiktionary)` + `source_url` to the page.
  **Precedence rationale:** academic ЕСУМ must rank above crowd-sourced Wiktionary. This
  supersedes the day-old handoff note that said "Goroh → Wiktionary → ЕСУМ" — that ordering
  was wrong by authority hierarchy.
- After ingest + wiring, **regenerate the manifest** (`scripts/lexicon/enrich_manifest.py`)
  and confirm the coverage lift.

## #M-4 — verifiable claims (quote raw tool output for each; no "I checked X")
| Claim | Deterministic check to run + paste |
|---|---|
| Dump pinned | `sha256sum <dump>` line + the dump date in the script as a constant |
| Table populated | `sqlite3 data/sources.db "SELECT count(*) FROM wiktionary_etymology"` |
| Each target word resolved | `sqlite3` SELECT per the 12 single words → row present or explicitly absent |
| Coverage lifted | the manifest-coverage one-liner (below) before vs after |
| Phrases excluded | show the skip-on-whitespace branch + coverage denominator excludes them |
| Tests pass | `.venv/bin/pytest tests/test_wiktionary_etymology_ingest.py` final summary line raw |
| Lint clean | `.venv/bin/ruff check <files>` final line raw |

Coverage one-liner (single-word denominator):
```bash
python3 -c "import json;m=json.load(open('starlight/src/data/lexicon-manifest.json'));e=[x for x in m['entries'] if ' ' not in x.get('lemma','')];print('single-word etymology',sum(1 for x in e if (x.get('enrichment') or {}).get('etymology')),'/',len(e))"
```

## Numbered steps (DISPATCH-BRIEF CHECKLIST)
1. `git worktree add` off `origin/main` (worktree enforced by dispatch).
2. Download + pin the `ukwiktionary` dump (date + sha256 constant in script). If the full
   dump is impractical to keep, stream-parse the bz2 and discard after extracting the ~12
   target lemmas + keep the extracted rows; document the pinned date/checksum either way.
3. `scripts/ingest/wiktionary_etymology_ingest.py` — offline `== Етимологія ==` extraction →
   `wiktionary_etymology` table (idempotent). CLI mirrors goroh ingest.
4. Wire `_wiktionary_etymology()` + third-tier precedence in `enrich_manifest.py`; reuse
   `_etymology_lookup_variants`. Skip whitespace lemmas; exclude them from coverage denominator.
5. Regenerate manifest; capture before/after coverage with the one-liner above.
6. Tests: `tests/test_wiktionary_etymology_ingest.py` (table create idempotency, section
   extraction on a fixture page incl. a multi-language/homograph case, precedence: Goroh wins
   over Wiktionary when both present, phrase-skip). Run `.venv/bin/pytest` on the new test.
7. `.venv/bin/ruff check` the new/edited files.
8. Commit (conventional): `feat(lexicon): Wiktionary etymology fallback + wire _etymology [#2882]`.
9. `git push -u origin <branch>`.
10. `gh pr create` — body lists the coverage lift + the raw verification table. **NO auto-merge.**

## Acceptance criteria
- `wiktionary_etymology` table created + populated; idempotent on re-run.
- `_etymology()` precedence is Goroh → ЕСУМ → Wiktionary; Wiktionary only gap-fills.
- Single-word etymology coverage materially up from 42/63 (target the 12 single words; a
  word may legitimately stay uncovered if uk.wiktionary truly lacks an etymology section —
  report which, don't fabricate).
- 9 multi-word phrases are skipped, not chased, and excluded from the coverage denominator.
- New tests green; ruff clean; PR opened, not merged.

## Gotchas (from this session's diagnosis + prior handoff)
- GitHub graphql API has intermittently 401'd (secondary rate-limit) — if `gh pr create`
  flakes, use REST `gh api -X POST repos/.../pulls`. Only required check = `Test (pytest)`.
- `data/sources.db` is the **shared** DB (same inode as worktrees) — the ingest writes there;
  that's expected and intended (mirrors goroh ingest).
- Do NOT touch `codex/2888-a2-*` worktrees/PRs — that's the A2 beta lane.

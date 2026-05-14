# Codex Dispatch — Etymology Phase 1: static page generator + foundational scripts

**Dispatched:** 2026-05-15 by orchestrator (Claude)
**Agent:** Codex (gpt-5.5, high effort)
**Worktree:** `.worktrees/dispatch/codex/etymology-phase-1-2026-05-15/`
**Branch:** `codex/etymology-phase-1-2026-05-15`
**Estimated:** ~30 min runtime, ~500 LOC code + tests

---

## Goal (one sentence)

Implement Phase 1 of the public etymology feature: foundational scripts (transliterate, cognate-forms extractor, static-pages generator) + 25k MDX pages emitted into Starlight + Astro build verification. Per merged Decision Card.

## Context — what you need to know

The merged Decision Card lives at `docs/decisions/pending/2026-05-15-etymology-feature-design.md`. **Read it first.** Three decisions are encoded there:

1. **Cognate extraction**: heuristic regex (Option A) over ESUM's consistent `<marker> <form>` template. The `cognates` JSON column in `esum_etymology_meta` already lists which markers are present per lemma — use that to drive the regex search.
2. **Slug strategy**: ASCII transliteration via simplified BGN/PCGN. Polysemy (e.g. `мати` has 3 entries) disambiguates with `-vol-page` suffix. Cyrillic alias map for search.
3. **Bundle strategy**: not relevant to Phase 1 (deferred to Phase 3 explorer).

Source data lives in `data/sources.db`:

```sql
-- 25,205 unique lemmas, 29,171 total entries (multi-page polysemy)
-- Schema:
CREATE TABLE esum_etymology_meta (
    id INTEGER PRIMARY KEY,
    lemma TEXT NOT NULL,
    vol INTEGER NOT NULL,
    page INTEGER NOT NULL,
    entry_hash TEXT NOT NULL DEFAULT '',
    etymology_text TEXT NOT NULL,        -- prose body, 200-2000 chars
    cognates TEXT NOT NULL DEFAULT '[]', -- JSON array of language markers like ["р.", "п.", "псл."]
    source TEXT NOT NULL DEFAULT 'ЕСУМ',
    UNIQUE(lemma, vol, page, entry_hash)
);
```

Sample row:

```
lemma     : дім
vol       : 2
page      : 90
cognates  : ["псл.", "іє.", "дінд.", "ав.", "лит.", "гр.", "лат.", "гот.", "стел.", "др.", "р.", "бр.", "п.", "ч.", "слц.", "болг.", "схв.", "слн."]
etymology_text : дім, [дом], [дома] (жін. р.) «дім», [домйр] «хазяїн», ... [body continues ~500-1500 chars]
```

## #M-4 deterministic-evidence preamble

Every claim in your PR description and commits MUST be tool-backed. The verifiable claims this work will produce + their deterministic tool:

| Claim | Tool | Evidence format |
|---|---|---|
| "Transliteration table covers all 33 Ukrainian letters" | pytest run on `test_transliterate.py` | Quote raw pytest output: `N passed in M.MMs` |
| "Cognate-form extraction emits N forms across M entries" | `sqlite3 data/sources.db "SELECT COUNT(*) FROM <new table>"` OR `jq '.entries | length' <output.json>` | Raw command + output |
| "MDX files generated: N" | `find starlight/src/content/docs/etymology -name '*.mdx' | wc -l` | Raw command + output |
| "Cognate-extraction coverage rate" | telemetry JSON emitted by extractor: `{"entries_with_forms": X, "entries_total": Y}` | Quote JSON |
| "Astro build succeeds with new pages" | `cd starlight && npm run build 2>&1 | tail -10` | Quote final 10 lines |
| "ruff clean" | `.venv/bin/ruff check scripts/etymology/` | Quote final line |

Do NOT claim "I added a test" — show the pytest line. Do NOT claim "build passes" — show the exit code and final lines. Per `docs/best-practices/deterministic-over-hallucination.md`.

---

## Tasks (numbered, sequential)

### 1. Worktree setup

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin
git worktree add .worktrees/dispatch/codex/etymology-phase-1-2026-05-15 -b codex/etymology-phase-1-2026-05-15 origin/main
cd .worktrees/dispatch/codex/etymology-phase-1-2026-05-15
```

### 2. `scripts/etymology/transliterate.py`

Implement Ukrainian-to-ASCII transliteration using simplified BGN/PCGN.

**Mapping table** (use this exact table):

```python
UK_TO_ASCII = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g',
    'д': 'd', 'е': 'e', 'є': 'ie', 'ж': 'zh', 'з': 'z',
    'и': 'y', 'і': 'i', 'ї': 'i', 'й': 'i', 'к': 'k',
    'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
    'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
    'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ь': '', 'ю': 'iu', 'я': 'ia', "'": '', 'ʼ': '',
}
```

**API:**

```python
def transliterate(text: str) -> str:
    """Lower-case Ukrainian Cyrillic → ASCII slug-safe form.

    Strips stress marks (combining acute U+0301), apostrophes, soft signs.
    Collapses non-letter runs to single hyphens. Strips leading/trailing hyphens.

    Examples:
        'серце' → 'sertse'
        'дім' → 'dim'
        'жінка' → 'zhinka'
        'абре́віатура' (with stress mark) → 'abreviatura'
    """
```

**Tests** (`tests/etymology/test_transliterate.py`): cover all 33 letters, stress-mark stripping, apostrophes, edge cases (empty string, all-Latin pass-through, mixed scripts).

### 3. `scripts/etymology/extract_cognate_forms.py`

Read `esum_etymology_meta`, for each entry parse the etymology_text against the language markers in the `cognates` JSON column, emit a sidecar table `esum_cognate_forms`.

**Schema** (add to `data/sources.db`):

```sql
CREATE TABLE IF NOT EXISTS esum_cognate_forms (
    entry_id INTEGER PRIMARY KEY,           -- FK to esum_etymology_meta.id
    cognate_forms TEXT NOT NULL DEFAULT '{}', -- JSON: {"р.": "сéрдце", "п.": "serce", ...}
    proto_form TEXT,                         -- псл./іє./стел. extracted form if present
    extracted_count INTEGER NOT NULL DEFAULT 0,
    expected_count INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(entry_id) REFERENCES esum_etymology_meta(id)
);
CREATE INDEX idx_cognate_forms_entry ON esum_cognate_forms(entry_id);
```

**Regex strategy:**

For each marker `M` in the entry's `cognates` JSON array, search `etymology_text` for:

```
re.compile(rf"\b{re.escape(M)}\s+([^\s,;\(\)\[\]«»\"\.]+(?:\s+[^\s,;\(\)\[\]«»\"\.]+)?)")
```

Captures 1-2 word forms following the marker. Stop at punctuation. Take the FIRST match per marker (the headword cognate; subsequent matches are usually derivatives).

Special handling for proto-language markers (`псл.`, `іє.`, `стел.`): often the form is preceded by `*` (`*sьrdьce`); preserve the asterisk in the captured form.

**Telemetry output** (`audit/etymology-phase-1/cognate_extraction_coverage.json`):

```json
{
  "entries_processed": 29171,
  "entries_with_at_least_one_form": <N>,
  "total_forms_extracted": <N>,
  "coverage_pct": <float>,
  "per_marker_coverage": {
    "р.": {"expected": <N>, "extracted": <N>, "pct": <float>},
    "п.": {...},
    ...
  }
}
```

**Acceptance:** `coverage_pct >= 65%` overall. Major markers (`р.`, `п.`, `ч.`, `псл.`) should each be >75%. If below threshold, halt and write the telemetry — escalate to LLM-assisted backfill (Phase 4) before the public ship.

**Tests** (`tests/etymology/test_extract_cognate_forms.py`):
- Fixture: 5 known ESUM entries with hand-verified expected cognate forms.
- Test cognate extraction matches expected for each.
- Test telemetry JSON shape.
- Test idempotency: running twice produces same result.

### 4. `scripts/etymology/extract_static_pages.py`

Emit one MDX file per UNIQUE LEMMA SLUG into `starlight/src/content/docs/etymology/<slug>.mdx`.

**Polysemy handling:**

- Group entries by their ASCII-transliterated slug.
- If one slug → one entry: emit `<slug>.mdx`.
- If one slug → multiple entries: emit a landing page `<slug>.mdx` listing all senses, plus `<slug>-<vol>-<page>.mdx` for each individual entry.

**MDX template** (per single-entry page):

```mdx
---
title: "{lemma}"
description: "Етимологія слова «{lemma}» — ЕСУМ, том {vol}, с. {page}"
sidebar:
  hidden: true
---

# {lemma}

> **Том {vol}, с. {page}** • Етимологічний словник української мови (ЕСУМ)

## Cognates

| Мова | Форма |
|---|---|
| Російська (р.) | {cognate_form_ru} |
| Польська (п.) | {cognate_form_pl} |
| ...           | ...               |

{if proto_form:}
**Праслов'янське:** {proto_form}
{/if}

## Етимологія

{etymology_text}

## Source

ЕСУМ, том {vol}, с. {page}. [Архів вікі-ресурсів](https://archive.org/...)

---

*[Browse all etymology entries](/etymology/) • [Interactive cognate explorer](/etymology/explore/)*
```

**Landing page template** (per ambiguous slug):

```mdx
---
title: "{lemma}"
description: "Етимологія слова «{lemma}» — кілька значень в ЕСУМ"
sidebar:
  hidden: true
---

# {lemma}

This word has multiple etymological entries in ESUM (possibly from different roots or different senses):

- [том {vol1}, с. {page1}]({slug}-{vol1}-{page1}/) — {first_50_chars_of_etymology_text}…
- [том {vol2}, с. {page2}]({slug}-{vol2}-{page2}/) — {first_50_chars}…
- ...
```

**Frontmatter notes:**
- `sidebar.hidden: true` — etymology pages should NOT appear in main Starlight sidebar (would explode it to 25k items). They're reachable via search + cross-links.
- Use `description:` for SEO + search hits.

**Acceptance:**
- 25,205 unique slugs → corresponding number of base `.mdx` files.
- + ~1,899 polysemy disambig files (`<slug>-<vol>-<page>.mdx`) for multi-entry lemmas.
- + corresponding "landing" pages for the ~1,899 ambiguous slugs.
- Total MDX files: ~29,000 (close to 29,171 total entries).

**Tests** (`tests/etymology/test_extract_static_pages.py`):
- Fixture: 3 lemmas (one unique, one polysemous-3-entries, one with special chars in etymology_text).
- Test single-entry page output structure.
- Test polysemy landing + sub-pages.
- Test MDX frontmatter parses cleanly.

### 5. Astro routing verification

Starlight uses `docsLoader()` which auto-routes from `starlight/src/content/docs/`. So `etymology/sertse.mdx` → `/etymology/sertse/`. **No explicit `getStaticPaths` needed** — Starlight handles it.

**Verify by running:**

```bash
cd starlight
npm run build 2>&1 | tail -30
```

Expect: build succeeds, all 25k pages included in output. Capture build duration.

If build takes >10 min OR exceeds memory, escalate: the brief acknowledges this risk and suggests "tier-split (build only first 5k for first ship)" as fallback. Do NOT silently truncate — surface the issue with measured numbers.

### 6. Lint + test

```bash
.venv/bin/ruff check scripts/etymology/ tests/etymology/
.venv/bin/pytest tests/etymology/ -v
```

All must pass.

### 7. Commit + push + PR

**Commit message:**

```
feat(etymology): Phase 1 — static page generator + foundational scripts

Implements Phase 1 of the public etymology feature per Decision Card
`docs/decisions/pending/2026-05-15-etymology-feature-design.md`:

  1. scripts/etymology/transliterate.py — Ukrainian Cyrillic → ASCII slug
     (BGN/PCGN simplified), strips stress marks, soft signs, apostrophes
  2. scripts/etymology/extract_cognate_forms.py — heuristic regex over
     etymology_text using markers from existing `cognates` JSON column;
     emits sidecar table `esum_cognate_forms` + coverage telemetry
  3. scripts/etymology/extract_static_pages.py — emits 25k MDX pages
     into starlight/src/content/docs/etymology/ with polysemy
     disambiguation via -vol-page suffix
  4. starlight/src/content/docs/etymology/<slug>.mdx — generated pages

Coverage telemetry: <X>% extraction rate overall. Build duration: <T>.

Per Decision Card Q1 (heuristic regex), Q2 (ASCII slugs).

Co-Authored-By: Codex (gpt-5.5) <noreply@openai.com>
```

**PR body:** include the deterministic-evidence quotes per #M-4 preamble above. Specifically:

- Test pass count (raw pytest output)
- Cognate extraction coverage telemetry (raw JSON or key metrics)
- MDX file count (raw `find | wc -l`)
- Astro build last 10 lines

**Title:** `feat(etymology): Phase 1 — static page generator + 25k MDX pages`

**Do NOT auto-merge.** Orchestrator (Claude) will review post-finalize.

```bash
git push -u origin codex/etymology-phase-1-2026-05-15
gh pr create --title "..." --body "$(cat <<'EOF'
...
EOF
)"
```

### 8. Exit summary

Report (at process exit):
- PR URL
- Coverage telemetry summary
- Build outcome + duration
- Any deviations from the brief (with reasoning)

If any acceptance criterion fails (coverage <65%, build fails, tests red), HALT before committing and write a follow-up `audit/etymology-phase-1/HALT-REPORT.md` explaining the failure with raw evidence. The orchestrator will diagnose + iterate.

---

## What's OUT of scope (Phase 2-4)

Do NOT implement in this PR:

- `/etymology/` landing page (Phase 2)
- Search / typeahead (Phase 2)
- Explorer page `/etymology/explore/` (Phase 3)
- Interactive cognate tree (Phase 3)
- D3.js / Lunr / explorer bundle (Phase 3)
- Antonenko style_guide cross-links (Phase 4)
- Грінченко heritage badges (Phase 4)
- LLM-assisted cognate extraction (Phase 4 only if regex coverage <80%)
- Cyrillic alias resolver (Phase 2 will add this)
- Top navigation entry (Phase 2 will add this)

---

## References

- Decision Card: `docs/decisions/pending/2026-05-15-etymology-feature-design.md`
- Predecessor brief: `docs/session-state/2026-05-14-etymology-feature-handoff-brief.md`
- Existing Starlight docs config: `starlight/src/content.config.ts`
- Sample existing MDX: `starlight/src/content/docs/a1/my-morning.mdx` (more complex than etymology will need; etymology pages use only Starlight frontmatter + plain markdown)
- Project rules: `claude_extensions/rules/critical-rules.md`, `claude_extensions/rules/non-negotiable-rules.md`

---

*Dispatch brief format per MEMORY DISPATCH-BRIEF CHECKLIST. Deterministic-evidence preamble per #M-4.*

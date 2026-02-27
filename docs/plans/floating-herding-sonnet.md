# Plan: Phase B RAG Pre-fetch + RAG Recheck + Track Rename

## Context

The D.1 RAG integration (issue #673) is done — Phase D now pre-fetches quotes from module content, searches them against the literary RAG collection (12,049 chunks), and injects results into the Claude review prompt. This works for **verification after the fact**.

The next step is **prevention**: give Gemini access to real primary source passages **during content generation** (Phase B), so it cites real quotes instead of inventing them. Additionally, we need to identify which existing modules should be rechecked now that the RAG database has grown from 177 to 12,049 chunks, and rename three tracks to proper names without level prefixes.

Three workstreams, in dependency order:
1. **Phase B RAG pre-fetch** — inject primary source excerpts into Gemini's content generation prompt
2. **RAG coverage recheck script** — identify modules needing re-review against expanded RAG
3. **Track rename** — `hist` → `hist`, `c1-hist` → `istoriohrafiia`, `c1-bio` → `bio` (with migration script)

---

## Workstream 1: Phase B RAG Pre-fetch

### Approach

Same pattern as Phase D: extract topic keywords from the plan, search RAG before dispatch, inject results as a template placeholder. The difference: Phase D searches for quotes already written; Phase B provides source material Gemini can cite.

### Source of search queries

For Phase B, we don't have module text yet (that's what we're generating). Instead, extract from the **plan file** (`plans/{track}/{slug}.yaml`):
- `content_outline[].section` names (Ukrainian H2 headers)
- `vocabulary_hints.required[]` (key terms)
- `topic_title` from meta

Run 3-5 RAG searches using these terms → get relevant primary source passages.

### Implementation

**File: `scripts/pipeline_lib.py`** — add `_prefetch_sources_for_phase_B()` helper near line 1777

```python
def _prefetch_sources_for_phase_B(ctx: ModuleContext) -> str:
    """Pre-fetch primary source excerpts from RAG for Phase B content generation.

    For seminar tracks: extracts section names + key terms from plan/meta,
    searches literary RAG, returns formatted excerpts Gemini can cite.
    """
    # Only for seminar tracks
    if ctx.track not in SEMINAR_TRACKS and not ctx.track.startswith("lit-"):
        return ""

    # Extract search terms from content_outline section names + vocabulary_hints
    search_terms = []
    for section in ctx.content_outline:
        search_terms.append(section.get("section", ""))
    # Add topic title as search term
    topic = ctx.meta.get("topic_title", ctx.slug.replace("-", " "))
    search_terms.insert(0, topic)
    # Cap at 5 searches
    search_terms = [t for t in search_terms if t][:5]

    try:
        from rag.query import search_literary
    except ImportError:
        return ""

    results = []
    seen_chunks = set()
    for term in search_terms:
        try:
            hits = search_literary(term, limit=2)
        except Exception:
            continue
        for hit in hits:
            cid = hit.get("chunk_id", "")
            if cid in seen_chunks:
                continue
            seen_chunks.add(cid)
            results.append(
                f"**{hit['work']}** ({hit['year']}, {hit['genre']}):\n"
                f"> {hit['text'][:300]}"
            )

    if not results:
        return ""

    return "\n\n".join(results[:8])  # Cap at 8 excerpts
```

**File: `scripts/pipeline_lib.py`** — in `phase_2_content()`, add to `overrides` dict (line ~1807):

```python
primary_sources = _prefetch_sources_for_phase_B(ctx)
overrides["PRIMARY_SOURCE_EXCERPTS"] = primary_sources or "(No primary source excerpts available)"
```

**File: `claude_extensions/phases/gemini/phase-2-content.md`** — add section after "Files to Read" table (line ~18):

```markdown
## Primary Source Excerpts (Cite These — Don't Invent Quotes)

These passages were retrieved from indexed primary sources (litopys.org.ua). When you need to cite a primary source, prefer these verified passages over inventing quotes from memory. You may paraphrase or excerpt, but attribute correctly.

{PRIMARY_SOURCE_EXCERPTS}
```

### Files to edit

| File | Change |
|------|--------|
| `scripts/pipeline_lib.py` | Add `_prefetch_sources_for_phase_B()`, inject into `phase_2_content()` overrides |
| `claude_extensions/phases/gemini/phase-2-content.md` | Add `{PRIMARY_SOURCE_EXCERPTS}` section |

---

## Workstream 2: RAG Coverage Recheck Script

### Approach

New standalone script `scripts/check_rag_coverage.py` that:
1. Scans completed modules in a track
2. Extracts quotes from each module's markdown (same `_extract_quotes_from_content` logic as D.1)
3. Searches each quote against RAG
4. Reports which modules have unverified quotes (candidates for Phase D re-review)

### Implementation

**File: `scripts/check_rag_coverage.py`** (new)

```
Usage:
    .venv/bin/python scripts/check_rag_coverage.py c1-bio
    .venv/bin/python scripts/check_rag_coverage.py c1-bio --json
    .venv/bin/python scripts/check_rag_coverage.py --all-seminar
```

**Logic:**
1. For each module in the track directory:
   - Read `{slug}.md`
   - Extract quotes (`«»` and `>` lines, same regex as `_extract_quotes_from_content`)
   - For each quote, `search_literary(quote, limit=1)` → check if score > 0.5
   - Classify: VERIFIED (match found) / UNVERIFIED (no match) / NO_QUOTES (no quotes to check)
2. Output: sorted table with module slug, quote count, verified count, unverified count, recommendation
3. Recommendations:
   - **RECHECK**: Has unverified quotes AND RAG has relevant works → rerun Phase D
   - **AWAIT**: Has unverified quotes BUT RAG lacks relevant works → needs more ingestion
   - **OK**: All quotes verified OR no quotes to check

**Output format (stdout):**
```
=== RAG Coverage Report: c1-bio ===

| Module                  | Quotes | Verified | Unverified | Action   |
|-------------------------|--------|----------|------------|----------|
| bohdan-khmelnytskyy     | 12     | 8        | 4          | RECHECK  |
| ivan-mazepa             | 28     | 22       | 6          | RECHECK  |
| volodymyr-velykii       | 5      | 0        | 5          | AWAIT    |
| knyahynia-olha          | 3      | 3        | 0          | OK       |

Summary: 53 modules, 12 RECHECK, 8 AWAIT, 33 OK
```

**`--json` flag** outputs machine-readable JSON for piping to batch re-review commands.

### Files to create/edit

| File | Change |
|------|--------|
| `scripts/check_rag_coverage.py` | NEW — standalone recheck script |

---

## Workstream 3: Track Rename (`hist` → `hist`, `c1-hist` → `istoriohrafiia`, `c1-bio` → `bio`)

### Scale

This is a massive rename. Per exploration results:
- `hist`: ~850 files affected (129 Python, 333 YAML, 288 JSON, 100+ MD)
- `c1-hist`: ~720 files affected (53 Python, 281 YAML, 182 JSON, 200+ MD)
- `c1-bio`: ~800+ files affected (similar scope to c1-hist — Python, YAML, JSON, MD)
- Total: ~2,370+ files across the project

### Approach: Migration script

Manual rename is error-prone. Write `scripts/rename_track.py` that handles ALL layers:

**Layer 1 — Filesystem renames (git mv):**

The script takes `(old_slug, new_slug)` and renames these paths (if they exist):
1. `curriculum/l2-uk-en/{old}/` → `curriculum/l2-uk-en/{new}/`
2. `curriculum/l2-uk-en/plans/{old}/` → `curriculum/l2-uk-en/plans/{new}/`
3. `curriculum/l2-uk-en/plans/{old}.yaml` → `curriculum/l2-uk-en/plans/{new}.yaml`
4. `schemas/activities-{old}.schema.json` → `schemas/activities-{new}.schema.json`
5. `claude_extensions/quick-ref/{OLD_UPPER}.md` → `claude_extensions/quick-ref/{NEW_UPPER}.md`
6. `docusaurus/docs/{old}/` → `docusaurus/docs/{new}/` (if exists)
7. `batch_state/checkpoint_{old}.json` → `batch_state/checkpoint_{new}.json`
8. `batch_state/api_usage/summary_{old}.json` → `batch_state/api_usage/summary_{new}.json`

**Layer 2 — Content replacements (all `.py`, `.yaml`, `.json`, `.md`, `.ts`, `.mjs` files):**

For each rename, replace these string variants:
- `{old-slug}` → `{new-slug}` (kebab-case)
- `{OLD-SLUG}` → `{NEW-SLUG}` (uppercase)
- `{Old_config_key}` → `{new_config_key}` (config key in `scripts/audit/config.py`)
- `{old_slug}` → `{new_slug}` (underscore variant, if any)

**Layer 3 — Targeted config updates (files that need semantic, not just string, changes):**
- `scripts/batch_gemini_config.py`: SEMINAR_TRACKS set + TRACK_CONFIGS dict key
- `scripts/audit/config.py`: LEVEL_CONFIG key
- `scripts/api/config.py`: level definitions array + SEMINAR_TRACK_IDS set
- `scripts/api/state_router.py`: PROFILE_MAP dict key
- `scripts/generate_level_status.py`: LEVELS array
- `scripts/generate_playground_data.py`: level configs
- `scripts/audit/checks/yaml_schema_validation.py`: level detection list (line ~350)
- `scripts/audit/checks/content_quality.py`: URL pattern + HISTORICAL_TRACKS set
- `scripts/audit/checks/cross_file_integrity.py`: base level mappings
- `scripts/validate_plan_config.py`: track-to-config mapping
- `package.json`: npm script names (`status:hist` → `status:hist`, `score:hist` → `score:hist`)
- `curriculum/l2-uk-en/curriculum.yaml`: track entry
- `docusaurus/docusaurus.config.ts`: nav links (`to: '/docs/hist/'` → `to: '/docs/hist/'`)
- `docusaurus/sidebars.ts`: sidebar autogenerate dirName + label
- `starlight/astro.config.mjs`: sidebar entry (directory + label)

**Safety features:**
- `--dry-run`: shows what would change without touching files
- Git-aware: uses `git mv` for directory renames to preserve history
- Skips `scripts/_archived/` (dead code, not worth the risk)
- Skips `.git/` directory
- Reports total files changed + lines modified

### Config mapping (three renames)

| Old slug | New slug | Old config key | New config key | Old quick-ref | New quick-ref |
|----------|----------|----------------|----------------|---------------|---------------|
| `hist` | `hist` | `history` | `history` | `HIST.md` | `HIST.md` |
| `c1-hist` | `istoriohrafiia` | `C1-history` | `istoriohrafiia` | `C1-HIST.md` | `ISTORIOHRAFIIA.md` |
| `c1-bio` | `bio` | `C1-biography` | `biography` | `C1-BIO.md` | `BIO.md` |

### Execution order

1. Run `scripts/rename_track.py hist hist --dry-run` → review output
2. Run `scripts/rename_track.py hist hist` → commit
3. Run `scripts/rename_track.py c1-hist istoriohrafiia --dry-run` → review output
4. Run `scripts/rename_track.py c1-hist istoriohrafiia` → commit
5. Run `scripts/rename_track.py c1-bio bio --dry-run` → review output
6. Run `scripts/rename_track.py c1-bio bio` → commit
7. Run full test suite: `pytest tests/ -x`
8. Deploy: `npm run claude:deploy`

### Archived scripts (`scripts/_archived/`)

40+ archived scripts reference old track names. These are dead code but will cause grep noise. The migration script should **skip** `_archived/` — these files are not executed and renaming them adds risk for no value.

### Files to create/edit

| File | Change |
|------|--------|
| `scripts/rename_track.py` | NEW — migration script |
| (everything else) | Automated by the migration script |

---

## Execution Order

1. **Workstream 1** (Phase B RAG pre-fetch) — 2 files, low risk, immediate value
2. **Workstream 2** (Recheck script) — 1 new file, no existing code changes, read-only tool
3. **Workstream 3** (Track rename) — high risk, do LAST after everything else is stable

---

## Verification

```bash
# Workstream 1: Phase B pre-fetch
.venv/bin/python -c "
import sys; sys.path.insert(0, 'scripts')
from pipeline_lib import _prefetch_sources_for_phase_B
# (test with mock ctx)
"
npm run claude:deploy  # deploy template
.venv/bin/python -m pytest tests/test_pipeline_v3.py -x

# Workstream 2: Recheck script
.venv/bin/python scripts/check_rag_coverage.py c1-bio
.venv/bin/python scripts/check_rag_coverage.py c1-bio --json | head -20

# Workstream 3: Track rename (dry-run each, then execute sequentially)
.venv/bin/python scripts/rename_track.py hist hist --dry-run
.venv/bin/python scripts/rename_track.py c1-hist istoriohrafiia --dry-run
.venv/bin/python scripts/rename_track.py c1-bio bio --dry-run
# (review dry-run output, then execute each + commit)
.venv/bin/python -m pytest tests/ -x
```

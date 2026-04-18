# External corpus (YT + blogs) — full indexing + MCP exposure spec

> Scope: transform the existing `external_articles` table from a coarse, under-exploited corpus into a properly-chunked, metadata-rich, MCP-queryable knowledge source for the build pipeline and wiki compiler. "Full solution" per project-owner directive — ship once, no iterative rebuild.

## Current state (as of 2026-04-18)

**Data ingested:** 1367 items across 7 JSONL files in `data/external_articles/`:
- `realna_istoria.jsonl` (344 videos) — Акім Галімов's decolonial Ukrainian history channel
- `ulp_youtube.jsonl` (316) — Ukrainian Lessons Podcast video transcripts
- `imtgsh.jsonl` (203) — «Історія України ім. Т.Г. Шевченка»
- `ulp_blogs.jsonl` (164) — ULP blog posts
- `istoria_movy.jsonl` (158) — «Історія мови» channel
- `komik_istoryk.jsonl` (107) — «Комік Історик»
- `other_blogs.jsonl` (75) — miscellaneous blog content

**Database:** `data/sources.db` table `external_articles` (1199 rows; discrepancy vs JSONL counts worth investigating in migration). Schema:
```sql
CREATE TABLE external_articles (
    id INTEGER PRIMARY KEY,
    chunk_id TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    url_normalized TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL DEFAULT '',
    domain TEXT DEFAULT '',
    char_count INTEGER DEFAULT 0
)
```
FTS5 index `external_fts` wraps it.

**Consumers today:**
- `scripts/wiki/sources_db.py:150 search_external()` — keyword FTS search
- `scripts/wiki/enrichment.py:234` — wiki compiler injects keyword-matched chunks during article compilation as background context
- No MCP exposure — build pipeline writer/reviewer cannot query directly
- No per-channel differentiation — ULP-pedagogy and Realna-Istoria-history ranked equally

## Gaps (what "full solution" fixes)

| # | Gap | Impact | Fix |
|---|---|---|---|
| 1 | **Chunks are whole videos** — avg 18K chars, max 160K, vs textbooks 350 chars | FTS hit returns entire video transcript; useless as citation-grained retrieval | Re-chunk all existing rows to ~2000-char windows with 200-char overlap |
| 2 | **No channel metadata** — `source_file` is only identifier | Can't rank Realna Istoria over random blog | Channel registry YAML + `channel_id` FK column |
| 3 | **No register/decolonization tags** | Writer pulls conversational slang into scripted prose tracks; HIST module can't specifically pull decolonial voices | `register_tag`, `decolonization_tag` columns populated from channel registry |
| 4 | **No speaker / quality tier** | All chunks weighted equally; low-quality hits drown out Плохій | `speaker`, `quality_tier` columns |
| 5 | **No date / duration** | Can't filter to recent material (post-2014 decolonial framing) | `publish_date`, `duration_s` columns |
| 6 | **Timestamp lookup impossible** | Can't cite "at 14:32 Галімов says X" | `chunk_start_ts`, `chunk_end_ts` columns (NULL for existing rows; populated for future re-extractions) |
| 7 | **Not exposed via MCP** | Build pipeline cannot query | New `mcp__sources__search_external` tool with filter params |
| 8 | **No per-track ranking** | HIST track gets ULP-pedagogy hits; A1 track gets decolonial history hits | `TRACK_CHANNEL_AFFINITY` config in `enrichment.py` |

## Target architecture

### Channel registry — `data/external_articles/channels.yaml`

Hand-labeled, checked into git. Single source of truth for per-channel metadata:

```yaml
channels:
  - id: realna_istoria
    name: "Реальна Історія"
    host: "Акім Галімов"
    url: "https://www.youtube.com/channel/UCdlVTngmxbh0oNE1pCwS64g"
    source_file: realna_istoria             # joins to external_articles.source_file
    register_tag: interview                   # spoken | scripted | interview | mixed
    decolonization_tag: strong                # strong | moderate | none | neutral
    quality_tier: 1                           # 1 (highest) .. 3 (background only)
    language_purity: vetted                   # vetted | auto-captions | unreviewed
    track_affinity:
      hist: 1.0
      bio: 0.8
      istorio: 1.0
      lit-hist-fic: 0.6
      oes: 0.4
      ruth: 0.3
      a1: 0.0
      a2: 0.0
    description: "Decolonial Ukrainian history, accessible register, vetted native-speaker host."

  - id: ulp_youtube
    name: "Ukrainian Lessons Podcast"
    host: "Anna Ohoiko"
    url: "https://ukrainianlessons.com/"
    source_file: ulp_youtube
    register_tag: scripted
    decolonization_tag: moderate
    quality_tier: 1
    language_purity: vetted
    track_affinity:
      a1: 1.0
      a2: 1.0
      b1: 0.8
      b2: 0.5
    description: "Professional A1-B2 pedagogy; commercial source (cite only per ULP licensing)."

  # ... full entries for all 7 current source_files + template for future additions
```

Quality tier definition (hard rule, not vibes):
- **1:** native host, vetted language, professional/pedagogical production, <1% Russianism rate
- **2:** native host, occasional Russianisms/Surzhyk, acceptable as background context
- **3:** unreviewed or heavy Surzhyk — search only when explicitly requested, never as default

### Schema enrichment (additive, backwards compatible)

Migration adds columns to `external_articles`; no existing column renamed or removed:

```sql
ALTER TABLE external_articles ADD COLUMN channel_id TEXT DEFAULT '';
ALTER TABLE external_articles ADD COLUMN speaker TEXT DEFAULT '';
ALTER TABLE external_articles ADD COLUMN register_tag TEXT DEFAULT '';
ALTER TABLE external_articles ADD COLUMN decolonization_tag TEXT DEFAULT '';
ALTER TABLE external_articles ADD COLUMN quality_tier INTEGER DEFAULT 2;
ALTER TABLE external_articles ADD COLUMN publish_date TEXT DEFAULT '';  -- ISO date if known
ALTER TABLE external_articles ADD COLUMN duration_s INTEGER DEFAULT 0;
ALTER TABLE external_articles ADD COLUMN chunk_start_ts INTEGER;  -- nullable
ALTER TABLE external_articles ADD COLUMN chunk_end_ts INTEGER;    -- nullable
ALTER TABLE external_articles ADD COLUMN video_id TEXT DEFAULT '';  -- extracted from url
```

FTS5 index rebuild after migration — include `title` + `text` + `speaker` tokenization, exclude metadata columns.

### Re-chunking pass

Current rows are whole-video blobs. Replace with proper chunks:
- Target chunk size: 2000 chars (Ukrainian prose, sentence-aware splitting — don't break mid-word or mid-sentence)
- Overlap: 200 chars (tail of prev chunk prepended to next for retrieval continuity)
- Chunk ID format: `ext-{source_file}-{video_id}-{chunk_idx:03d}` — stable, reproducible
- Preserve title + url + source_file on every chunk (denormalized, FTS-friendly)
- `char_count` per chunk, not per video
- For `ulp_blogs` (avg 78 chars, already tiny) — keep as-is, no re-chunking

Re-chunking strategy:
1. Source: `data/external_articles/*.jsonl` (raw extraction)
2. Delete + recreate `external_articles` rows from JSONL
3. Rebuild `external_fts` after insert batch

Expected row count post-rechunk: ~18K chunks (from current ~1200 blobs) — similar order to textbook FTS (24K chunks).

### Per-track ranking — `scripts/wiki/enrichment.py`

Replace the current `_BACKGROUND_SOURCE_TYPES` / fixed weight logic with channel-aware ranking:

```python
def rank_external_hits(hits: list[dict], *, track: str) -> list[dict]:
    """Re-rank external-article hits by channel affinity for this track.

    Base score comes from FTS5 BM25. Multiply by:
      - channel.track_affinity[track] (0.0 = exclude, 1.0 = full weight)
      - quality_tier weight (tier 1 = 1.0, tier 2 = 0.6, tier 3 = 0.2)
    Quality-tier-3 channels require explicit opt-in (not returned by default search).
    """
```

`TRACK_CHANNEL_AFFINITY` derived at startup from `channels.yaml` — single source of truth.

### MCP tool — `mcp__sources__search_external`

New tool in `.mcp/servers/sources/server.py`:

```python
Tool(
    name="search_external",
    description=(
        "Search the external articles corpus (YouTube transcripts + blogs: "
        "Realna Istoriia, ULP, Istoriia Movy, etc.). Supports filters for channel, "
        "register, decolonization alignment, and track affinity. "
        "Returns chunks with video URL, timestamp (when available), speaker, "
        "and channel metadata for citation."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "FTS5 search query (Ukrainian or English)"},
            "track": {"type": "string", "description": "Optional: apply per-track channel affinity ranking"},
            "channel": {"type": "string", "description": "Optional: filter to one channel (e.g. 'realna_istoria')"},
            "register": {"type": "string", "enum": ["spoken", "scripted", "interview", "mixed"]},
            "decolonization": {"type": "string", "enum": ["strong", "moderate", "none", "neutral"]},
            "min_quality_tier": {"type": "integer", "default": 2, "description": "1=highest only, 3=include background"},
            "max_results": {"type": "integer", "default": 10},
        },
        "required": ["query"],
    },
)
```

Handler returns:
```
[
  {
    chunk_id, text, title, url, channel_id, speaker,
    register_tag, decolonization_tag, quality_tier,
    publish_date, chunk_start_ts, chunk_end_ts,  # nullable
    fts_score, adjusted_score
  },
  ...
]
```

## Deliverables (single implementation pass)

### New files

1. `data/external_articles/channels.yaml` — hand-populated registry for all 7 current `source_file` values + template comment for adding channels later
2. `scripts/wiki/channels.py` — load/validate `channels.yaml`, provide `get_channel(source_file)`, `get_track_affinity(channel_id, track)`, `TRACK_CHANNEL_AFFINITY`
3. `scripts/wiki/migrate_external_chunks.py` — one-shot: re-ingest `*.jsonl` → chunked rows → enriched schema → rebuild FTS5
4. `tests/test_channels_registry.py` — schema validation, coverage of all source_files, affinity-lookup determinism
5. `tests/test_migrate_external_chunks.py` — chunker correctness (2K target, 200 overlap, sentence-aware), chunk_id stability across reruns, zero-data-loss
6. `tests/test_mcp_search_external.py` — MCP handler returns expected shape, filters work, ranking applies

### Modified files

1. `scripts/wiki/sources_db.py` — extend `search_external()` with new filter params (`channel`, `register`, `decolonization`, `min_quality_tier`, `track`); keep old signature backwards-compat via kwargs
2. `scripts/wiki/enrichment.py` — replace fixed `_BACKGROUND_SOURCE_TYPES` weight with `rank_external_hits(track=...)` using channel registry
3. `.mcp/servers/sources/server.py` — add `search_external` tool: definition in `list_tools()`, dispatch in `call_tool()`, handler function `handle_search_external()`
4. `docs/MONITOR-API.md` — document the new MCP tool (or wherever MCP tools are indexed for discoverability)

### Out of scope (explicitly deferred to later workstream)

- **Re-extraction with real timestamps** — current JSONL files don't have `start_ts`/`end_ts`. Schema includes columns as nullable; populating them requires re-running `yt-dlp --write-auto-sub` on 1367 videos and re-parsing. Separate GH issue.
- **New channel ingestion** — user needs to supply the channel list (Plokhii, Hrytsak interviews, Ukrainian philology lectures, etc.). Separate workstream after user provides list.
- **Audio indexing for pronunciation** — different project entirely.

## Channel registry — initial population

Codex must hand-populate `channels.yaml` entries for these 7 `source_file` values (based on best-effort research; flag for user review if unsure):

| source_file | Expected channel name | Initial quality_tier | Initial register | Initial decolonization |
|---|---|---|---|---|
| `realna_istoria` | Реальна Історія | 1 | interview | strong |
| `ulp_youtube` | Ukrainian Lessons Podcast | 1 | scripted | moderate |
| `imtgsh` | Історія України ім. Т.Г. Шевченка | 2 | scripted | strong |
| `istoria_movy` | Історія Мови | 2 | scripted | moderate |
| `komik_istoryk` | Комік Історик | 2 | mixed | moderate |
| `ulp_blogs` | ULP Blog | 1 | scripted | moderate |
| `other_blogs` | Miscellaneous blogs | 3 | mixed | neutral |

Track affinity matrix: use best judgment per channel based on its domain. Mark `# REVIEW` comment on any guess the user should validate.

## Success criteria

- [ ] `data/external_articles/channels.yaml` has entries for all 7 `source_file` values, passes schema validation
- [ ] Schema migration idempotent: running twice doesn't double-add columns or duplicate rows
- [ ] Post-migration: `SELECT COUNT(*) FROM external_articles` ≈ 18K chunks (vs current 1199 whole videos)
- [ ] Post-migration: `SELECT AVG(char_count) FROM external_articles` ≈ 2000 (vs current 18159)
- [ ] FTS5 query "Реальна Історія козаки" returns chunk-grained hits (not whole videos) with channel_id, quality_tier populated
- [ ] MCP tool `search_external` callable, returns structured results with all new fields
- [ ] Filter `search_external(query=..., channel='realna_istoria')` returns only Realna Istoria chunks
- [ ] Filter `search_external(query=..., decolonization='strong')` returns only strong-decolonization channels
- [ ] Per-track ranking: `search_external(query='козаки', track='a1')` deprioritizes Realna Istoria (low a1 affinity)
- [ ] Unit + integration tests green
- [ ] No regression in existing wiki-compilation path (`enrichment.py` still injects external chunks for wiki articles, just with new ranking)

## Coordination with in-flight work

Two other Codex workers are running in parallel (#1322 convergent pipeline + wiki sources refactor). Files likely touched by those:
- #1322: `scripts/build/*`, `scripts/build/v6_build.py`, `audit/*`
- Sources refactor: `scripts/wiki/context.py`, `scripts/wiki/compile.py`, `scripts/wiki/compiler.py`, `scripts/api/main.py`, `wiki/*.md`, `wiki/**/*.sources.yaml` (new)

**This external-corpus work is scoped to avoid collision with both:** `scripts/wiki/sources_db.py`, `scripts/wiki/enrichment.py`, and `.mcp/servers/sources/server.py` are NOT in either other worker's scope per their briefs. If you detect uncommitted changes in those files when you start, pause and report.

## GH issue

Create issue titled "External articles corpus — re-chunk, enrich schema, MCP expose" before starting work. Reference in commits. All ACs checked before close.

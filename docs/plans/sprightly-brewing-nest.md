# Plan: Fix blog scoring + bridge discovery → MDX

## Context

Discovery finds blogs, videos, and RAG chunks → writes to `orchestration/*/discovery.yaml` → appends to research markdown. But the MDX generator reads external resources **only** from the static curated `docs/resources/external_resources.yaml`. Discovery results never reach the rendered Resources tab.

Additionally, blog scoring is too permissive: level-only matches (zero keyword overlap) pass the threshold at 0.35, polluting results with irrelevant ULP episodes (greetings episodes for an alphabet module).

## Change 1: Require keyword match in blog scoring

**File:** `scripts/video_discovery.py` — `search_blogs()` (line ~225)

Problem: `level_match (0.2) + podcast_boost (0.15) = 0.35` passes `score < 0.2` with zero keyword/topic overlap.

Fix: gate on at least one keyword match before the score threshold:

```python
if topic_overlap + title_overlap + desc_overlap == 0:
    continue
```

## Change 2: Move discovery.yaml to a permanent sidecar location

Currently `discovery.yaml` lives in `orchestration/{slug}/` which is disposable. Move canonical copy to `discovery/{slug}.yaml` alongside the other permanent sidecars (meta, vocab, activities, research, audit, review).

**File:** `scripts/video_discovery.py` — `write_discovery_yaml()` already takes a `path` arg, so no changes needed there.

**File:** `scripts/build_module.py` — `phase_discover_v4()` (~line 3825)

Change:
```python
discovery_path = ctx.orch_dir / "discovery.yaml"
```
To:
```python
# Canonical location (permanent sidecar)
discovery_dir = ctx.paths["md"].parent / "discovery"
discovery_dir.mkdir(parents=True, exist_ok=True)
discovery_path = discovery_dir / f"{ctx.slug}.yaml"
# Also write to orchestration for backward compat
orch_discovery = ctx.orch_dir / "discovery.yaml"
```

Write to both locations (canonical + orch copy).

## Change 3: Bridge discovery → MDX resources tab

**File:** `scripts/generate_mdx.py`

### 3a. Add `_load_discovery_resources(level_dir, slug)` (~line 1655)

- Reads `level_dir / 'discovery' / f'{slug}.yaml'` (new canonical path)
- Filters blogs with `relevance_score >= 0.5`
- Maps: `content_type=podcast_episode*` → `podcasts`, others → `articles`
- Returns dict in external_resources format: `{articles: [...], podcasts: [...]}`
- Each item: `{title, url, source, relevance}` matching what `format_resources_for_mdx` expects

### 3b. Add `_merge_resources(curated, discovery)` helper

- For each category (articles, podcasts, youtube, websites, books): merge lists, deduplicate by URL
- Curated items take priority (appear first)

### 3c. Wire into main loop (~line 2032, after curated resources load)

```python
discovery_resources = _load_discovery_resources(level_dir, mod.slug)
module_resources = _merge_resources(module_resources, discovery_resources)
```

## Files to modify

| File | Change |
|------|--------|
| `scripts/video_discovery.py` | Add keyword-match gate in `search_blogs()` |
| `scripts/build_module.py` | Write discovery to `discovery/{slug}.yaml` (+ orch copy) |
| `scripts/generate_mdx.py` | Add `_load_discovery_resources()`, `_merge_resources()`, wire into main loop |
| `tests/test_video_discovery.py` | Add test for keyword-match gate |

## Verification

1. `pytest tests/test_video_discovery.py -x -q`
2. Re-run discover: `.venv/bin/python scripts/build_module.py a1 1 --force-phase discover`
3. Check new path `curriculum/l2-uk-en/a1/discovery/the-cyrillic-code-i.yaml` exists
4. Check irrelevant episodes are gone (keyword-match gate)
5. Re-run MDX: `.venv/bin/python scripts/build_module.py a1 1 --force-phase mdx`
6. Check `starlight/src/content/docs/a1/the-cyrillic-code-i.mdx` — Resources tab shows discovered alphabet articles alongside curated ones

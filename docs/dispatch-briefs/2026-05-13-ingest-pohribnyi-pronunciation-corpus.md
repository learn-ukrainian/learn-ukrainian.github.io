# Dispatch — Ingest Микола Погрібний "Українська літературна вимова" 3LP playlist

**Premise:** User direction 2026-05-13 — ingest YouTube playlist `PLKTBLqy7kMugWc9_dOpw18zaIlhuBVtgz` containing the canonical Ukrainian literary pronunciation reference 3LP (1992) by Микола Погрібний, vinyl rip with subtitles. User: "the nicest Ukrainian I have ever heard." Existing infrastructure: `scripts/wiki/fetch_external_sources.py` already ingests YouTube channels into `external_articles` (962 YouTube rows already present).

**Agent:** codex / gpt-5.5 / high
**Base:** `main` @ `59bee5d87a` (post-routing-budget merge)
**Expected scope:** ~30-80 LOC config + ingestion runtime (~10-30 min). Single PR.
**Why Codex:** mechanical config + script runtime. May need a small extension if `--channel` doesn't accept playlist URLs.

---

## #M-4 Deterministic preamble — verifiable claims

| Claim | Tool | Evidence |
|---|---|---|
| "Channel registered" | `grep pohribnyi data/external_articles/channels.yaml` | Quote raw block |
| "Subtitles fetched" | `ls data/external_articles/pohribnyi_pronunciation*` | List files |
| "External_articles row count increased" | `python3 -c "import sqlite3; c=sqlite3.connect('data/sources.db').cursor(); c.execute(\"SELECT COUNT(*) FROM external_articles WHERE channel_id='pohribnyi_pronunciation'\"); print(c.fetchone())"` | Quote raw integer (>0) |
| "Schema validated" | `.venv/bin/python -m pytest tests/wiki/ -k channel -v` (or relevant test) | Quote final pass line |
| "Ruff clean" | `.venv/bin/ruff check data/external_articles/channels.yaml scripts/wiki/` | Quote `All checks passed!` |
| "PR opened" | `gh pr view --json url` | Quote URL |

---

## Source identification

- **Speaker:** Микола Погрібний (1925-2009), renowned Ukrainian linguist
- **Recording:** "Українська літературна вимова" (Ukrainian Literary Pronunciation) 3LP, 1992
- **Playlist URL:** https://www.youtube.com/playlist?list=PLKTBLqy7kMugWc9_dOpw18zaIlhuBVtgz
- **First video URL:** https://www.youtube.com/watch?v=MlOzm7FQhtk (vinyl rip Side A)
- **Subtitle availability:** YES (per user confirmation 2026-05-13). Should be Ukrainian, may be community or auto-captioned.
- **Pedagogical class:** canonical phonetic / orthoepic reference — the gold standard for Ukrainian literary pronunciation

## Implementation

### 1. Add channel entry to `data/external_articles/channels.yaml`

Add this entry to the `channels:` list (placement: after `ulp_youtube`, before any other entry — keeps grouping by similar register):

```yaml
- id: pohribnyi_pronunciation
  name: "Українська літературна вимова (3LP, 1992)"
  host: "Микола Погрібний"
  url: "https://www.youtube.com/playlist?list=PLKTBLqy7kMugWc9_dOpw18zaIlhuBVtgz"
  source_file: pohribnyi_pronunciation
  register_tag: scripted
  decolonization_tag: strong
  quality_tier: 1
  language_purity: vetted
  track_affinity:  # phonetic-foundation modules benefit most
    a1: 1.0      # phonetic foundations
    a2: 1.0      # continued phonetic refinement
    b1: 0.7      # advanced phonetic awareness
    b2: 0.4
    c1: 0.3
    c2: 0.3
    hist: 0.1    # only narrative segments useful
    bio: 0.1
    ruth: 0.5    # heritage-context phonetic reference
  description: "Canonical Ukrainian literary pronunciation reference recording (3LP vinyl rip, 1992) by linguist Mykola Pohribnyi. Gold-standard phonetic / orthoepic source for A1-A2 phonetic gates. Vetted, scripted reading register."
```

### 2. Verify yt-dlp accepts playlist URLs

Test BEFORE running production ingestion:

```bash
.venv/bin/python scripts/wiki/fetch_external_sources.py --channel "https://www.youtube.com/playlist?list=PLKTBLqy7kMugWc9_dOpw18zaIlhuBVtgz" --out pohribnyi_pronunciation_test.jsonl
```

**If it fails** with "playlist URL not supported" or similar:
- Inspect `normalize_channel_url()` in `scripts/wiki/fetch_external_sources.py:304`
- If the function strips playlist params, extend to accept `?list=...` URLs by detecting playlist mode and skipping `videos_tab=True` normalization for playlists
- Aim for additive change — don't break existing channel-URL flow
- ~10-30 LOC delta

**If it succeeds:** proceed to step 3.

### 3. Production ingestion

```bash
.venv/bin/python scripts/wiki/fetch_external_sources.py --channel-name pohribnyi-pronunciation
# OR if using arbitrary URL form:
.venv/bin/python scripts/wiki/fetch_external_sources.py --channel "https://www.youtube.com/playlist?list=PLKTBLqy7kMugWc9_dOpw18zaIlhuBVtgz" --out pohribnyi_pronunciation.jsonl
```

Wait for completion (likely 5-15 min for 6 videos × ~30 min audio per side). Confirm:
- `data/external_articles/pohribnyi_pronunciation.jsonl` exists
- Row count in JSONL ≈ chunks per video × video count

### 4. Build/refresh sources.db

```bash
.venv/bin/python scripts/wiki/fetch_external_sources.py --build-db
```

Verify `external_articles` table now contains rows with `channel_id='pohribnyi_pronunciation'`.

### 5. Tests

If `tests/wiki/` has channel-validation tests, they should automatically pick up the new entry via the schema validator (`_validate_channel`). If a test explicitly asserts channel COUNT, increment it. Otherwise no test changes needed.

If existing `tests/wiki/test_channels.py` (or similar) doesn't yet exist for the channel-validation flow, do NOT add tests in this PR — keep scope tight.

## Pre-submit checklist

1. `git worktree add -b feat/ingest-pohribnyi-pronunciation ../routing-worktrees/pohribnyi-ingest origin/main`
2. **Edit:** `data/external_articles/channels.yaml` — add channel entry per Section 1.
3. **Test playlist URL acceptance:** Section 2.
4. **If extension needed:** `scripts/wiki/fetch_external_sources.py` `normalize_channel_url` minimal additive change.
5. **Run ingestion:** Section 3 + 4.
6. **Pytest:** `.venv/bin/python -m pytest tests/wiki/ -v` (no `-x`).
7. **Ruff:** `.venv/bin/ruff check scripts/wiki/`.
8. **Commit:** `feat(corpus): ingest Pohribnyi 'Українська літературна вимова' 3LP playlist`. Body cites video count, JSONL row count, sources.db external_articles delta.
9. **Push + PR.** No auto-merge.

Do NOT commit `data/external_articles/pohribnyi_pronunciation.jsonl` directly to git (per existing pattern, JSONL caches likely gitignored — verify against `.gitignore`). If they ARE committed historically, follow precedent.

## Forbidden

- ❌ `pytest -x`.
- ❌ Auto-merge.
- ❌ Modifying writer prompt directives — that's a separate dispatch (writer needs to learn to use the new source). This PR ingests only.
- ❌ Changing other channel entries.
- ❌ Whisper/transcription — subtitles already exist on the videos.

## Halt conditions

- If yt-dlp returns 0 videos (playlist private/region-locked/blocked) → STOP. Report what URL was tried and the error. Do NOT silent-fall-back.
- If subtitle download succeeds but every video has no Ukrainian captions (only auto-en, etc.) → STOP. Report. We need real Ukrainian subtitles to make this worth indexing.
- If `external_articles` schema validation fails on the new rows → STOP, fix schema mismatch, re-run.

## Follow-up issues to file (after this PR lands)

1. Writer-prompt directive update: teach the writer that `pohribnyi_pronunciation` corpus exists for phonetic-class A1/A2 modules. The `phonetic_rules` writer obligation should reference Pohribnyi as canonical source for IPA verification.
2. MCP-tool addition (or extension): a `search_pronunciation_reference` tool that scopes search to `quality_tier=1` `register_tag=scripted` phonetic-class channels (Pohribnyi today; expandable).

---

*Companion: `claude_extensions/rules/dispatch-brief-checklist`. Existing channels precedent: `data/external_articles/channels.yaml` ulp_youtube + realna_istoria entries. Schema validator: `scripts/wiki/channels.py:_validate_channel`.*

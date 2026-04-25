# Wiki rebuild runbook

> Total scope: **1,665 wikis** to compile = **754 rebuild** (existing wikis
> that need to re-emit under the post-#1555 paragraph-aware chunker +
> per-dim review) + **524 NEW** (uncompiled tracks: c2, oes, ruth, lit
> sub-tracks). Estimated 3 days end-to-end with Claude + Gemini running
> in parallel shells.

This runbook is the **single source of truth** for the rebuild flow.
Don't deviate without updating it.

---

## Why `--force`

`compile.py` skips any module whose article + sidecar already exist on
disk. **Every rebuild command in this runbook must include `--force`** —
otherwise the existing 1,141 articles on disk are no-ops and only the
524 NEW ones get compiled, leaving the chunker drift unfixed.

---

## Prereqs (verify ALL before kicking off)

```bash
# 1) sources.db is healthy (1.5 GB, all tables present)
sqlite3 data/sources.db "
  SELECT 'textbooks',         COUNT(*) FROM textbooks UNION ALL
  SELECT 'literary_texts',    COUNT(*) FROM literary_texts UNION ALL
  SELECT 'external_articles', COUNT(*) FROM external_articles UNION ALL
  SELECT 'wikipedia',         COUNT(*) FROM wikipedia UNION ALL
  SELECT 'ukrainian_wiki',    COUNT(*) FROM ukrainian_wiki;
"
ls -lah data/sources.db
# Expected: 1.5 GB, all 5 tables non-empty.

# 2) Dense embeddings up_to_date for all 4 corpora
.venv/bin/python scripts/wiki/cold_encode.py \
    --corpora textbook_sections,external,wikipedia,ukrainian_wiki --dry-run
# Expected: all four show "up_to_date: true"

# 3) GDrive backup is fresh (<24h old)
#    Path resolution: $LU_GDRIVE_DATA env var if set, else glob the
#    per-user GoogleDrive mount. (Email is not hardcoded — see #1577 Phase 1 Q4.)
GDRIVE="${LU_GDRIVE_DATA:-$(ls -d "$HOME/Library/CloudStorage/"GoogleDrive-*/"My Drive/Projects/learn-ukrainian-data" 2>/dev/null | head -1)}"
ls -lah "$GDRIVE/sources.db"

# 4) #1569 multi-agent writer support is merged (compile.py --writer flag exists)
.venv/bin/python scripts/wiki/compile.py --help | grep -A1 -- "--writer"
# Expected: see the --writer choices line. If missing, BLOCK on #1569 merging.

# 5) Both Claude and Gemini CLIs are reachable
claude --version && gemini --version
# Expected: claude ≥ 2.1.116, gemini ≥ 0.39.1

# 6) Disk has space for ~3GB of new compiled markdown + sidecars
df -h "$(pwd)"
# Expected: ≥ 10 GB free.
```

If any of the six checks fail, stop and resolve before continuing.

---

## Snapshot before changes

```bash
cp data/sources.db "data/sources.db.bak-$(date +%Y%m%d-%H%M%S)-pre-wiki-rebuild"
ls -lah data/sources.db.bak-*-pre-wiki-rebuild
```

---

## Per-track compile commands

The split is locked in by the 2026-04-25 wiki retrieval overhaul plan
(#1553). Adjust only after the writer pilot (5 wikis × 3 models) gives
empirical evidence that the intuition was wrong.

### Claude tracks (715 wikis, ~47h serial @ 4 min/wiki, ~24h with parallelism)

Cultural / decolonization-sensitive content. Run in **shell A**.

```bash
# 1. Literature (232 rebuild + 203 NEW = 435 total). The "lit" track in
#    compile.py covers all of literature/works including the sub-tracks
#    (lit-essay, lit-war, lit-hist-fic, lit-youth, lit-fantastika,
#    lit-humor, lit-drama, lit-doc, lit-crimea). One command covers all.
.venv/bin/python scripts/wiki/compile.py \
    --track lit --all --force --writer claude --review

# 2. Figures (180 rebuild)
.venv/bin/python scripts/wiki/compile.py \
    --track bio --all --force --writer claude --review

# 3. Periods (140 rebuild)
.venv/bin/python scripts/wiki/compile.py \
    --track hist --all --force --writer claude --review

# 4. Historiography (136 rebuild)
.venv/bin/python scripts/wiki/compile.py \
    --track istorio --all --force --writer claude --review

# 5. Folk (27 rebuild — covers all sub-genres: genres, lyric, prose,
#    ritual, short-forms, tradition)
.venv/bin/python scripts/wiki/compile.py \
    --track folk --all --force --writer claude --review
```

### Gemini tracks (426 wikis, ~28h serial, ~14h with parallelism)

Structural / grammatical content. Run in **shell B** (concurrent with shell A).

```bash
# 6. A1 (55 rebuild — pedagogy)
.venv/bin/python scripts/wiki/compile.py \
    --track a1 --all --force --writer gemini --review

# 7. A2 (69 rebuild — grammar)
.venv/bin/python scripts/wiki/compile.py \
    --track a2 --all --force --writer gemini --review

# 8. B1 (100 rebuild — grammar)
.venv/bin/python scripts/wiki/compile.py \
    --track b1 --all --force --writer gemini --review

# 9. B2 (89 rebuild — grammar)
.venv/bin/python scripts/wiki/compile.py \
    --track b2 --all --force --writer gemini --review

# 10. C1 (111 rebuild — academic)
.venv/bin/python scripts/wiki/compile.py \
    --track c1 --all --force --writer gemini --review

# 11. C2 (106 NEW — academic, uncompiled track)
.venv/bin/python scripts/wiki/compile.py \
    --track c2 --all --force --writer gemini --review

# 12. OES (101 NEW + 1 rebuild = 102 — Old East Slavic)
.venv/bin/python scripts/wiki/compile.py \
    --track oes --all --force --writer gemini --review

# 13. RUTH (114 NEW + 1 rebuild = 115 — Ruthenian)
.venv/bin/python scripts/wiki/compile.py \
    --track ruth --all --force --writer gemini --review

# 14. Linguistics is covered by oes + ruth above. No separate command.
```

Each command runs `compile + per-dim review + MIN aggregator + lock` on
every slug in the track. Failures are logged in
`wiki/.reviews/{track}/diagnostics/`. Re-run with the same command —
`--force` plus the existing per-track resume logic skips locked
articles.

---

## Post-compile: re-ingest into `ukrainian_wiki`

After all 1,665 wikis are compiled and locked, re-ingest into the
retrieval corpus. **Until #1570 ships**, the per-subdir loop is the
ONLY working invocation — `wiki/ --encode` silently no-ops because
the underlying `_collect_article_paths` glob is non-recursive.

```bash
# Snapshot first — this re-ingest mutates data/sources.db.
cp data/sources.db "data/sources.db.bak-$(date +%Y%m%d-%H%M%S)-pre-reingest"

SUBDIRS="wiki/academic/c1 wiki/academic/c2 \
         wiki/figures wiki/folk/genres wiki/folk/lyric \
         wiki/folk/prose wiki/folk/ritual wiki/folk/short-forms \
         wiki/folk/tradition wiki/grammar/a2 wiki/grammar/b1 \
         wiki/grammar/b2 wiki/historiography wiki/linguistics/oes \
         wiki/linguistics/ruthenian wiki/literature/works \
         wiki/pedagogy/a1 wiki/periods"

for d in $SUBDIRS; do
  echo "==> $d"
  .venv/bin/python scripts/wiki/ingest_ukrainian_wiki.py "$d" \
      --report-path "data/corpus_audit/$(echo "$d" | tr / -)-ingest-report.md"
done

# Verify the new corpus shape
sqlite3 data/sources.db "
  SELECT 'total_chunks',      COUNT(*)                 FROM ukrainian_wiki UNION ALL
  SELECT 'distinct_articles', COUNT(DISTINCT article_slug) FROM ukrainian_wiki;
"
# Expected: ~1665 articles, ~30K chunks (post-paragraph-aware chunker).
```

---

## Cold-encode the new ukrainian_wiki shards

```bash
# Dry-run first to size the work
.venv/bin/python scripts/wiki/cold_encode.py \
    --corpora ukrainian_wiki --dry-run

# Real run with --resume (crash-safe; idempotent recovery)
.venv/bin/python -u scripts/wiki/cold_encode.py \
    --corpora ukrainian_wiki --resume \
    2>&1 | tee /tmp/wiki-rebuild-encode.log

# Verify
.venv/bin/python scripts/wiki/cold_encode.py \
    --corpora ukrainian_wiki --dry-run
# Expected: up_to_date: true, new_units: 0, stale_units: 0
```

Pace: ~15 units/s for compiled-wiki chunks. 30K chunks → ~33 min.

---

## Refresh GDrive backup

```bash
./scripts/backup-data.sh
```

Captures sources.db (now with the new `ukrainian_wiki` corpus) plus
`data/embeddings/` (which has the new dense shards). After this, the
rebuild is durable across hardware failures.

---

## Smoke-test the new corpus

Pick three slugs that should retrieve to the new wikis. Use the
`mcp__sources__*` tools or direct SQL.

```bash
# A1 sanity (a level that already had wikis)
sqlite3 data/sources.db "
  SELECT article_slug, section_path, snippet(ukrainian_wiki_fts, 2, '<<', '>>', '...', 32) AS hit
  FROM ukrainian_wiki_fts
  WHERE ukrainian_wiki_fts MATCH 'привітання NEAR/3 формальне'
  LIMIT 3;
"

# C2 sanity (a level that had ZERO wikis pre-rebuild — proves NEW
# tracks made it in)
sqlite3 data/sources.db "
  SELECT article_slug, section_path
  FROM ukrainian_wiki
  WHERE track='c2'
  GROUP BY article_slug
  LIMIT 5;
"
# Expected: 5 distinct c2 article_slugs.

# OES sanity (another NEW track)
sqlite3 data/sources.db "
  SELECT COUNT(DISTINCT article_slug) FROM ukrainian_wiki WHERE track='oes';
"
# Expected: ~100 articles.
```

If any track returns zero rows, something dropped silently. Likely
suspects: cross-track slug collisions (#1571), citation_audit drops
(#1573), or the per-subdir loop missing a directory in `SUBDIRS` above.

---

## What can go wrong

### A track's compile loop dies halfway

`compile.py` writes per-article state. Re-running the same command
with `--force` will re-attempt failures and skip already-locked
articles. No data loss.

### Claude / Gemini CLI session expires mid-run

Both `call_claude_with_fallback` and `call_gemini_with_fallback` retry
with the model rung ladder. If a whole rung is exhausted, the
compile.py call returns an error for that one article — recorded in
`wiki/.reviews/{track}/diagnostics/{slug}.yaml`. Re-run after the
rate-limit window resets.

### `sources.db` gets wiped mid-rebuild (recurrence of #1563)

The post-#1563 file-size guard makes this nearly impossible — but if it
happens anyway, follow `docs/SCRIPTS.md > Recovery: when data/sources.db
is empty or corrupt`. The pre-rebuild snapshots saved above are also
restoration sources.

### MPS / OOM during cold-encode

Cold-encode uses `--resume` + idempotent shard writes. Kill, restart
with `--resume`, no rework. If 16 GB RAM is tight, reduce
`BENCHMARK_BATCH_SIZE` env var.

### Compile produces lower-quality output than the existing wiki

This is the writer-bakeoff failure mode. Stop. Run the 5×3 wiki writer
pilot (5 representative wikis × {gemini, claude, gpt-5.5}) and pick
the per-track winner empirically. The current Claude/Gemini split is
content-type intuition, not evidence — re-evaluate if the diff is
ugly.

---

## Cleanup

```bash
# Remove the pre-rebuild snapshots once the new state is verified +
# backed up to GDrive.
ls -la data/sources.db.bak-*-pre-*
# After confirming the rebuild looks good, delete:
rm data/sources.db.bak-*-pre-wiki-rebuild
rm data/sources.db.bak-*-pre-reingest

# Old shards in data/embeddings/ukrainian_wiki/ from the pre-rebuild
# corpus are auto-pruned by the manifest's deleted-row mechanism.
# Verify:
sqlite3 data/embeddings/manifest.db "
  SELECT corpus, deleted, COUNT(*) FROM embedding_units
  WHERE corpus='ukrainian_wiki' GROUP BY deleted;
"
# Most rows should have deleted=0 (the new ones); some old ones may
# still be deleted=1 — those don't affect retrieval.
```

---

## Issue references

- **#1553** — Wiki retrieval overhaul (parent epic)
- **#1569** — Multi-agent writer support (PREREQ)
- **#1570** — Non-recursive directory glob in `ingest_ukrainian_wiki.py`
  (working around in this runbook via the per-subdir loop)
- **#1571** — Cross-track slug collisions (14 articles silently dropped
  per current schema; manifest-side fix tracked separately)
- **#1573** — `citation_audit` gate bypass between bulk and per-file
  ingest paths
- **#1567** — Hungarian-language contamination in textbooks corpus
  (independent of this rebuild)

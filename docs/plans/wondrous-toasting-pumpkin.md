# Fix ESU Crawl: Deduplicate URLs and Improve Reporting

## Context

`urls.jsonl` has 123,254 entries but only 81,441 unique article IDs (41,813 duplicates). ESU indexes articles under multiple letter pages, so the same article gets discovered multiple times. The fetch phase handles this via ID-based dedup, but:

1. The printed count is misleading ("123,254 URLs to fetch" vs actual 81,441 unique)
2. `urls.jsonl` is bloated with duplicates
3. Fetch can write the same article twice if it appears with different `letter` values

## Changes

### 1. Deduplicate `urls.jsonl` at discovery time

**File: `scripts/rag/crawl_esu.py`, `run_discover()`**

After discovery completes, deduplicate by article ID before writing. Keep the first occurrence (preserves the canonical letter). This prevents the bloat at source.

### 2. Deduplicate fetch input

**File: `scripts/rag/crawl_esu.py`, `run_fetch()`**

After loading `urls`, deduplicate by ID before filtering against `fetched_ids`. Update the print to show unique count:

```python
# Deduplicate URLs by article ID (same article appears under multiple letters)
seen_ids = set()
unique_urls = []
for entry in urls:
    if entry["id"] not in seen_ids:
        seen_ids.add(entry["id"])
        unique_urls.append(entry)
if len(urls) != len(unique_urls):
    print(f"  Deduplicated: {len(urls)} → {len(unique_urls)} unique articles")
urls = unique_urls

print(f"[fetch] {len(urls)} articles to fetch")
```

### 3. Deduplicate existing `urls.jsonl` (one-time)

Run a one-time dedup of the existing file so the user's current crawl works with clean data:

```bash
.venv/bin/python -c "
import json
seen, unique = set(), []
with open('data/esu/urls.jsonl') as f:
    for line in f:
        rec = json.loads(line)
        if rec['id'] not in seen:
            seen.add(rec['id'])
            unique.append(line)
with open('data/esu/urls.jsonl', 'w') as f:
    f.writelines(unique)
print(f'Deduped: {len(seen) + len(unique) - len(unique)} removed, {len(unique)} kept')
"
```

## Files Modified

| File | Change |
|------|--------|
| `scripts/rag/crawl_esu.py` | Dedup in `run_discover()` + `run_fetch()`, fix print counts |

## Verification

```bash
# Check urls.jsonl is deduplicated
.venv/bin/python -c "
import json
ids = []
with open('data/esu/urls.jsonl') as f:
    for line in f: ids.append(json.loads(line)['id'])
print(f'Total: {len(ids)}, Unique: {len(set(ids))}, Dups: {len(ids) - len(set(ids))}')
"

# Run fetch with --skip-discover and verify counts make sense
.venv/bin/python scripts/rag/crawl_esu.py --skip-discover --workers 2
# Should show ~81K total, not 123K
```

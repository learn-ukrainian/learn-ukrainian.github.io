# Gemini Dispatch Brief — CodeQL Batch C: URL substring + tag-filter (12 warnings)

**Risk class:** LOW (warnings, pattern-fixable)
**Mode:** danger (worktree)
**Goal:** open a single PR fixing all 12 warnings. NOT auto-merged — human reviews.

---

## Worktree instructions (mandatory)

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b gemini-codeql-C-url-tag-validation .worktrees/dispatch/gemini/codeql-C origin/main
cd .worktrees/dispatch/gemini/codeql-C
```

---

## The alerts (12 total)

### `py/incomplete-url-substring-sanitization` (8)

| File |
|---|
| `scripts/content/video_discovery_helpers.py` |
| `scripts/audit/audit_external_resources.py` |
| `scripts/wiki/migrate_sources.py` |
| `scripts/wiki/migrate_external_chunks.py` |
| `tests/test_video_discovery.py` |
| `tests/test_stress_annotation.py` |
| `tests/test_publish_step.py` |
| `tests/test_enrich.py` |

### `py/bad-tag-filter` (4)

| File |
|---|
| `scripts/rag/source_query.py` |
| `scripts/build/phases/wiki_compressor.py` |
| `scripts/build/phases/honesty_annotator.py` |
| `scripts/audit/checks/contract_compliance.py` |

Get fresh details for each alert:
```bash
gh api 'repos/:owner/:repo/code-scanning/alerts?state=open&per_page=100' --paginate \
  -q '.[] | select(.rule.id | test("incomplete-url-substring-sanitization|bad-tag-filter")) | {number, rule: .rule.id, path: .most_recent_instance.location.path, line: .most_recent_instance.location.start_line, msg: .most_recent_instance.message.text}'
```

---

## Fix patterns

### `py/incomplete-url-substring-sanitization`

CodeQL fires on patterns like:
```python
if "youtube.com" in url:  # ← unsafe: matches "evil.com/youtube.com"
    ...
```

**Right fix — anchored URL parsing:**
```python
from urllib.parse import urlparse
parsed = urlparse(url)
if parsed.netloc.lower() in {"youtube.com", "www.youtube.com"} or parsed.netloc.endswith(".youtube.com"):
    ...
```

For tests where the URL is hardcoded in the test fixture, the fix is the same — anchored host check, not substring `in`. CodeQL doesn't distinguish "this is a test."

### `py/bad-tag-filter`

CodeQL fires when HTML/XML tag stripping is done with regex in a way that misses edge cases:
```python
clean = re.sub(r"<[^>]*>", "", html)  # ← misses nested, attributes, comments, CDATA, etc.
```

**Right fix — use a real parser:**
```python
from bs4 import BeautifulSoup
soup = BeautifulSoup(html, "html.parser")
clean = soup.get_text()
```

**For our codebase:** check if BeautifulSoup is already a dependency (`grep beautifulsoup4 pyproject.toml`). If yes, use it. If we'd need to add a dependency just for these 4 sites, prefer `html.parser` from stdlib via `html.parser.HTMLParser` subclass, OR use `markupsafe.Markup.striptags` if `markupsafe` is already in.

For false positives (e.g. the regex is filtering specific known-safe content like our own pre-formatted templates), suppress with justification.

---

## Per-batch execution

1. **Group alerts by class.** Fix all URL ones first (consistent pattern), then all tag-filter ones.
2. **For each, read 20 lines of context** to understand the data flow.
3. **Apply the right fix.** For URL: anchored parse. For tags: real parser or justified suppression.
4. **Run tests** — many of the affected files ARE tests, so make sure your fix doesn't break test behavior:
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -m pytest tests/test_video_discovery.py tests/test_stress_annotation.py tests/test_publish_step.py tests/test_enrich.py -x -q
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -m pytest tests/ -k 'video_discovery or audit_external or wiki_compressor or honesty_annotator or contract_compliance or source_query' -x -q
   ```
5. **Run ruff** on all modified files.
6. **Commit:**
   ```
   fix(security): resolve 12 CodeQL warnings — URL substring + bad-tag-filter (batch C)

   - 8 py/incomplete-url-substring-sanitization: switched to urlparse() with anchored netloc check
   - 4 py/bad-tag-filter: switched to BeautifulSoup parser (or justified suppression)

   Co-Authored-By: Gemini 3.1 Pro <noreply@google.com>
   ```
7. **Push + open DRAFT PR** with per-alert reasoning.
8. **Do NOT enable auto-merge.**

---

## Stop conditions

- If a fix changes test behavior (e.g. test fixture URL no longer matches what production code parses) → STOP, document, propose either updating both or splitting the test/production fix.
- If `BeautifulSoup` isn't a dependency and you can't reach a clean stdlib fix → suppress with justification, leave a TODO referencing this brief.

---

## Deliverable

Draft PR + per-alert reasoning. Same shape as Batches A/B.

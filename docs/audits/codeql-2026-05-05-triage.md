# CodeQL Triage Notes (2026-05-05)

## Overview
Reviewed 12 open CodeQL alerts across Python, JavaScript, and HTML files. 
- 8 alerts were identified as **FALSE POSITIVE**. 6 relate to archived third-party HTML scrapings, and 2 are clear-text storage false positives.
- 4 alerts were identified as **REAL** (or actionable hygiene) and were fixed in code.

*Note: Dismissing alerts via the GitHub API failed with a 403 error due to insufficient token permissions (requires `security_events: write`). The FALSE POSITIVE alerts remain open but are documented here for future dismissal once a properly scoped token is available.*

## Triage Table

| Alert | Rule | File | Verdict | Rationale / Fix |
|---|---|---|---|---|
| #167 | `py/clear-text-storage-sensitive-data` | `scripts/build/linear_pipeline.py` | FALSE POSITIVE | Variable `mdx` contains curriculum text, not secrets. Inline `lgtm` and `codeql` suppression markers do not work in GitHub Code Scanning. To be dismissed via API. |
| #166 | `py/clear-text-storage-sensitive-data` | `scripts/generate_mdx/core.py` | FALSE POSITIVE | Generating `.mdx` curriculum content. To be dismissed via API. |
| #114 | `py/path-injection` | `scripts/tools/image_review_server.py` | REAL | Added `img_path.resolve()` and a check ensuring `img_path.is_relative_to(BASE_DIR.resolve())` to prevent path traversal in the local dev tool. |
| #113 | `py/path-injection` | `scripts/tools/image_review_server.py` | REAL | Same path injection vulnerability in the localhost static server fixed by `is_relative_to()` verification. |
| #23 | `js/functionality-from-untrusted-source` | `docs/resources/podcasts/raw/episode_021.html` | FALSE POSITIVE | Archived scraped HTML; not deployed. To be dismissed via `gh api`. |
| #22 | `js/functionality-from-untrusted-source` | `docs/resources/podcasts/raw/episode_022.html` | FALSE POSITIVE | Archived scraped HTML; not deployed. To be dismissed via `gh api`. |
| #21 | `js/functionality-from-untrusted-source` | `docs/resources/podcasts/raw/episode_022.html` | FALSE POSITIVE | Archived scraped HTML; not deployed. To be dismissed via `gh api`. |
| #20 | `js/functionality-from-untrusted-source` | `docs/resources/podcasts/raw/episode_021.html` | FALSE POSITIVE | Archived scraped HTML; not deployed. To be dismissed via `gh api`. |
| #19 | `js/unvalidated-dynamic-method-call` | `playgrounds/admin.html` | REAL | Modified `sectionLoaders[section]` check to use `Object.prototype.hasOwnProperty.call()` to block malicious property lookups. |
| #18 | `js/xss-through-dom` | `playgrounds/image-explorer.html` | REAL | Updated `escapeHtml` (handling double and single quotes) and applied it to `tb.text` in string interpolation assigned to `innerHTML`. |
| #17 | `js/xss-through-dom` | `docs/resources/podcasts/raw/episode_022.html` | FALSE POSITIVE | Archived scraped HTML; not deployed. To be dismissed via `gh api`. |
| #16 | `js/xss-through-dom` | `docs/resources/podcasts/raw/episode_021.html` | FALSE POSITIVE | Archived scraped HTML; not deployed. To be dismissed via `gh api`. |
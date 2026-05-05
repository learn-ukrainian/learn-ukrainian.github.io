# Gemini dispatch — slovnyk.me paronym structure research (prereq for #1666)

## Context

Issue #1666 wants to ingest Гринчишин/Сербенська «Словник паронімів української мови» (1986 NBU scan). Before writing the ingester, we need to know whether slovnyk.me's `/dict/paronyms/<word>` URLs return cross-paronym navigation (paronym X linked to paronym X-prime) or just isolated entries.

If yes → can scrape slovnyk.me as a structured paronym pair source AND fall back to NBU scan only for entries slovnyk.me doesn't have.
If no → must fall back to OCR-ing the 1986 NBU scan (pdftotext + regex on entry headers), which is messier.

This is a 15-min research dispatch — fetch + inspect + report. No code changes.

## Task

1. **Fetch HTML for 5 paronym pairs:**
   - адресат / адресант
   - болотний / болотяний
   - дипломат / дипломант
   - талан / талант
   - кампанія / компанія

   For each, fetch both URLs:
   - `https://slovnyk.me/dict/paronyms/<paronym1>`
   - `https://slovnyk.me/dict/paronyms/<paronym2>`

2. **Inspect the HTML structure of each entry page.** Specifically check:
   - Does the page for `адресат` contain a link or visible reference to `адресант`?
   - Is the cross-link in a `<nav>` / `<aside>` / inline `<a>` element?
   - Does the entry body contain BOTH paronyms in one definition block, or just the queried word?
   - Is there a sibling URL pattern like `/dict/paronyms-pair/<word1>-<word2>` that might be the canonical pair page?

3. **Capture a representative HTML snippet** (≤500 chars) showing the structure for each pair.

4. **Report findings** in a single concise comment on issue #1666:

   ```
   slovnyk.me paronym page structure research:

   Verdict: <cross-link YES / cross-link NO / hybrid>

   Per-pair findings:
   - адресат/адресант: <yes/no, snippet>
   - болотний/болотяний: <yes/no, snippet>
   - дипломат/дипломант: <yes/no, snippet>
   - талан/талант: <yes/no, snippet>
   - кампанія/компанія: <yes/no, snippet>

   Recommended ingestion path:
   - <If YES, hybrid scrape from slovnyk.me as primary + NBU 1986 PDF as fallback>
   - <If NO, NBU 1986 PDF OCR-only, slovnyk.me only as definition lookup>

   Sample selector for the cross-link / pair block (if applicable):
   <CSS selector or XPath>
   ```

## How to fetch

The simplest path:

```bash
for word in адресат адресант болотний болотяний дипломат дипломант талан талант кампанія компанія; do
  curl -sL --user-agent 'Mozilla/5.0 (research)' "https://slovnyk.me/dict/paronyms/${word}" \
    -o /tmp/slovnyk-${word}.html
done
ls -lah /tmp/slovnyk-*.html
```

Inspect HTML with `htmlq` if available, else `python -c "from bs4 import BeautifulSoup; ..."`.

## Acceptance criteria

- HTML fetched for all 10 URLs (5 pairs × 2 paronyms)
- Findings comment posted to issue #1666
- HTML structure summarized clearly enough that the next agent can write the ingester without re-fetching
- Decision (cross-link YES / NO / hybrid) documented + recommendation actionable

## Why Gemini

This is research/data inspection — Gemini is uncapped and good at HTML structure analysis.

## Discipline

- Per-query fair use (license posture unchanged)
- No automated bulk scraping in this dispatch — just 10 fetches for structure analysis
- Reference issue #1666 in the comment
- No commit / PR — pure research output

# Sources MCP — `sources.tool-result.v1` envelopes

Exam/eval and other LLM consumers should read **structured** tool results, not
parse Markdown prose. Schema id: `sources.tool-result.v1` (issue #7954 / epic #7953).

## Dual emission

| Channel | Content |
| --- | --- |
| MCP `content` (text) | Human prose, including analysis and lemma counts for VESUM verification |
| MCP `structuredContent` | Full envelope JSON (machine path) |

`summary_prose` inside the envelope mirrors the text content so a consumer that
only sees structured payloads still has the human summary.

## Envelope shape

```json
{
  "schema": "sources.tool-result.v1",
  "tool": "verify_word",
  "status": "ok",
  "query": {"word": "синій", "pos_filter": null},
  "match_count": 6,
  "lemma_count": 2,
  "hits": [
    {"lemma": "синій", "pos": "adj", "tags": "adj:m:v_naz:compb", "is_archaic": false, "tag_gloss": "adjective; masculine; nominative; positive degree"},
    {"lemma": "синій", "pos": "adj", "tags": "adj:m:v_zna:rinanim:compb", "is_archaic": false, "tag_gloss": "adjective; masculine; accusative; for inanimate referents; positive degree"},
    {"lemma": "синій", "pos": "adj", "tags": "adj:m:v_kly:compb", "is_archaic": false, "tag_gloss": "adjective; masculine; vocative; positive degree"},
    {"lemma": "синій", "pos": "adj", "tags": "adj:f:v_dav:compb", "is_archaic": false, "tag_gloss": "adjective; feminine; dative; positive degree"},
    {"lemma": "синій", "pos": "adj", "tags": "adj:f:v_mis:compb", "is_archaic": false, "tag_gloss": "adjective; feminine; locative; positive degree"},
    {"lemma": "синіти", "pos": "verb", "tags": "verb:imperf:impr:s:2", "is_archaic": false, "tag_gloss": "verb; imperfective; imperative; singular; second person"}
  ],
  "summary_prose": "6 analyses (2 distinct lemmas)\n\n'синій' — matches in VESUM:\n…"
}
```

- `status`: `ok` | `empty` | `error`
- `match_count`: non-negative integer; equals `len(hits)` when hits are listed
- Empty results use `status: "empty"`, `match_count: 0`, `hits: []` — never raw `[]` alone
- Errors use `status: "error"` plus a stable `error_code` (no stack traces on the wire)

### Optional `diagnostics` (empty only)

When `search_text` / `search_literary` drop query tokens before FTS and the
result is empty, the envelope may include:

```json
"diagnostics": {
  "dropped_tokens": [
    {"token": "я", "reason": "min_token_length"},
    {"token": "є", "reason": "min_token_length"}
  ]
}
```

### V4 verify tools (additive)

`verify_word`, `verify_words`, `verify_lemma`, `verify_stress`, and
`check_modern_form` keep authority keys (`disposition`, `success`,
`evidence_identifiers`, `result`) and **add** the envelope fields above.
Do not fold envelope fields into `result` (evidence ids stay stable).

### VESUM analyses and lemmas (#7955)

For `verify_word`, `verify_words`, and `verify_lemma`:

- `match_count` counts **morphological analysis rows**, exactly `len(hits)`.
  Different analyses of the same word/lemma are retained.
- `lemma_count` is an integer counting distinct exact `lemma` strings in
  `hits`. It does not count homonymous lexeme identities or normalize spellings.
  Empty and invalid-input envelopes have both counts zero.
- Every hit includes `lemma`, `pos`, `tags`, `is_archaic`, and non-empty
  `tag_gloss`. Lemma lookup hits also retain `word_form`; their `lemma` is the
  queried lemma. Batch hits include the input `word`.
- Batch hits contain all analyses for each **distinct input word**, in first
  input occurrence order. Repeating an input does not multiply analyses.
  Lemmas are deduplicated across the entire batch. Existing `result.found`
  and `result.total` still count input occurrences.
- Both `summary_prose` and MCP text state `N analyses (M distinct lemmas)`,
  including zero-count and invalid-input results.

**Presentation choice:** `tag_gloss` is an English, semicolon-separated
translation of explicit [VESUM tag tokens](https://github.com/brown-uk/dict_uk/blob/master/doc/tags.txt).
It does not infer absent features. Unmapped tokens remain visible as
`unrecognized tag [TOKEN]`; missing tags read `No morphological tags supplied`.
Raw `tags` are preserved. These presentation fields are added to copies of
hits, never to V4 `result` or evidence-identifier inputs. No VESUM data changes.

**Batch correction:** the initial #7954 implementation grouped batch `hits`
as `{word, matches}` and counted found words. #7955 corrects that envelope
surface to analysis rows. Consumers of the old batch shape should use
`result.matches` for the unchanged word-to-analyses mapping, or group the
new hits by `word`. This is a shape correction in v1; the V4 authority
payload is unchanged and the new lemma/gloss fields are additive.
Other tools do not acquire `lemma_count` or `tag_gloss` through this change.

The six `синій` rows above were read from the local VESUM database and
corroborated through Sources MCP on 2026-09-11. The offline contract fixture
is `tests/fixtures/vesum_synii_analyses.json`, SHA-256
`df5b93dcc2f4e2f882d6cfb3e08c93ae9eeb61fba34fd75987e832a620c9a0b4`.
The test runs the real SQLite lookup over these pinned rows.

Disposition → status: `supported`/`partial` → `ok` (but `match_count == 0`
forces `empty`); `not_found`/`negative` → `empty` with `hits: []`;
`ambiguous`/`invalid_input` → `error`.

For `check_modern_form`, archaic-only (`disposition=negative`) keeps VESUM rows
in `result` / `supporting_records` and emits the empty triple on the envelope
(`status=empty`, `match_count=0`, `hits=[]`).

### Search / dict tools

`search_text`, `search_literary`, `search_sources`, `query_pravopys`,
`get_chunk_context`, `search_definitions`, `search_idioms`, `search_synonyms`,
`search_style_guide` return the envelope without V4 authority keys (no
disposition recording). Empty hits always use the empty triple above — including
`search_sources` (no bare `[]` text-only responses).

## FTS min-token policy (`search_text` / `search_literary`)

These handlers still require keywords with `len(token) >= 3` before calling
SQLite FTS (short Ukrainian function words otherwise dominate BM25). That
filter is **not** removed in #7956 (option B): when an empty result follows
dropped short tokens, consumers read `diagnostics.dropped_tokens` with
`reason: "min_token_length"` instead of guessing why the query vanished.

`search_sources` uses `_prepare_query` / dense retrieval and does **not** apply
this MCP-side length floor; it still returns the same empty envelope shape.

## Example: integer match_count without prose regex

```python
# structuredContent from tools/call
assert result["schema"] == "sources.tool-result.v1"
assert isinstance(result["match_count"], int)
assert result["match_count"] == len(result["hits"])
```

Beyond the explicitly documented #7955 batch correction, breaking changes
require a new schema id (`sources.tool-result.v2`, …).

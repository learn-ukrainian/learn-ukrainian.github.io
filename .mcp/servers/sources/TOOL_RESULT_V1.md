# Sources MCP — `sources.tool-result.v1` envelopes

Exam/eval and other LLM consumers should read **structured** tool results, not
parse Markdown prose. Schema id: `sources.tool-result.v1` (issue #7954 / epic #7953).

## Dual emission

| Channel | Content |
| --- | --- |
| MCP `content` (text) | Human prose (unchanged for agent workflows) |
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
  "hits": [{"lemma": "синій", "pos": "adj", "tags": "…"}],
  "summary_prose": "'синій' — 6 match(es) in VESUM:\n…"
}
```

- `status`: `ok` | `empty` | `error`
- `match_count`: non-negative integer; equals `len(hits)` when hits are listed
- Empty results use `status: "empty"`, `match_count: 0`, `hits: []` — never raw `[]` alone

### V4 verify tools (additive)

`verify_word`, `verify_words`, `verify_lemma`, `verify_stress`, and
`check_modern_form` keep authority keys (`disposition`, `success`,
`evidence_identifiers`, `result`) and **add** the envelope fields above.
Do not fold envelope fields into `result` (evidence ids stay stable).

Disposition → status: `supported`/`partial` → `ok` (but `match_count == 0`
forces `empty`); `not_found`/`negative` → `empty` with `hits: []`;
`ambiguous`/`invalid_input` → `error`.

For `check_modern_form`, archaic-only (`disposition=negative`) keeps VESUM rows
in `result` / `supporting_records` and emits the empty triple on the envelope
(`status=empty`, `match_count=0`, `hits=[]`).

### Search / dict tools

`search_text`, `search_literary`, `query_pravopys`, `get_chunk_context`,
`search_definitions`, `search_idioms`, `search_synonyms`, `search_style_guide`
return the envelope without V4 authority keys (no disposition recording).

## Example: integer match_count without prose regex

```python
# structuredContent from tools/call
assert result["schema"] == "sources.tool-result.v1"
assert isinstance(result["match_count"], int)
assert result["match_count"] == len(result["hits"])
```

Breaking changes require a new schema id (`sources.tool-result.v2`, …).

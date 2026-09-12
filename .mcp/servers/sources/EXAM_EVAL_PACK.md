# Sources MCP — exam/eval consumer tool pack

Machine contract for LLM exam/eval harnesses that call Sources MCP tools.
Result schema for pack tools: `sources.tool-result.v1` (see `TOOL_RESULT_V1.md`).
Manifest: `exam_eval_pack.v1.json` (this directory).

Parent issues: #7957 / epic #7953.

## Pack membership

| Tool | Purpose | Typical failure |
| --- | --- | --- |
| `verify_word` | Morph attestation for one surface form | `empty` miss; `error` invalid input |
| `verify_words` | Batch morph attestation (prefer over N× verify_word) | Partial found; zero hits → `status=empty` |
| `verify_lemma` | Expand lemma → forms | Empty / invalid lemma |
| `verify_stress` | Stress attestation | Empty / error |
| `check_modern_form` | Modern vs archaic-only forms | Archaic-only → envelope empty triple |
| `search_text` | Textbook FTS chunks | Empty; short tokens → `diagnostics.dropped_tokens` |
| `search_literary` | Literary FTS chunks | Same empty/diagnostics contract |
| `get_chunk_context` | Fetch one chunk by id | `error_code=sources_db_missing` / empty |
| `query_pravopys` | Orthography rules | Empty topic |
| `search_style_guide` | Style guidance (Антоненко-Давидович) | Empty |
| `search_definitions` | СУМ-11 definitions | Empty |
| `search_idioms` | Phraseology | Empty |
| `search_synonyms` | Synonym net | Empty |
| `search_sources` | Unified multi-corpus retrieval | Empty (never bare `[]`) |

### `search_sources` — in pack

**Included.** General retrieval when the consumer does not yet know which corpus
owns the evidence. Prefer corpus-specific tools when scoping is known.

## Non-goals (binding)

- No answer keys, held-out items, or scoring rubrics in this pack.
- A hit / `match_count` is **not** an MCQ letter and must not be treated as one.
- Prefer `verify_words` when batching; respect call budgets.
- Do **not** import Learn Ukrainian fleet code into `ukrainian-llm-eval`.
- Public exam content may appear in Sources corpora — treat as contamination risk;
  do not disclose unpublished items via tool logs.

## Consumer reading path

1. Call tool → read MCP `structuredContent` (envelope).
2. Assert `schema == "sources.tool-result.v1"`.
3. Branch on `status` (`ok` / `empty` / `error`); for `error` read `error_code`.
4. Use integer `match_count` / `lemma_count` (verify tools) — never regex prose.
5. On empty FTS with short tokens, inspect `diagnostics.dropped_tokens`.

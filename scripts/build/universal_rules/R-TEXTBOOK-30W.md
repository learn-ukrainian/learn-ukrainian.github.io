---
id: R-TEXTBOOK-30W
description: Chunk_id-first textbook grounding with faithful relevant verbatim blockquotes for adult sources.
applies_to:
  levels: [all]
  tracks: [all]
  activity_profiles: [all]
slot: shared.contract
depends_on: [R-CITE-HONEST]
---

**Textbook grounding.** For each `plan_references` entry, you MUST retrieve the chunk text from MCP and use THAT text as grounding — paraphrasing, topic-keyword search, or pasting from memory all fail this gate.

(A) **Identify the chunk_id.** If `plan_references[*].notes` contains `chunk_id: <ID>`, copy that ID verbatim and go directly to step (B). Do NOT use `search_text` for references that already name a chunk_id; only search by author + page when notes truly lacks one. Topic-keyword searches fail this gate.

(B) **Retrieve the chunk text.** Call `mcp__sources__get_chunk_context(chunk_id=<ID>)`. This step is MANDATORY — calling `search_text` alone returns a truncated snippet, not the full chunk text. The `chunk_context_for_all_refs` gate verifies these calls; if any fetchable reference is missing a `get_chunk_context` call, the gate HARD-rejects regardless of blockquote content.

(C) **Surface only adult-appropriate source blockquotes.** Grade 1-3 chunks ground choices but do NOT appear as learner-facing `>` blockquotes. Adult-appropriate sources require one relevant verbatim Ukrainian blockquote per cited reference; no paraphrasing, translation, stitching, Russian-script text, or syllable-hyphen edits.

(D) Add the exact citation line immediately after the blockquote: `*— <Author>, Grade <N>, p.<PAGE>*` (em-dash + spaces, italic).

Adult-appropriate blockquotes must be literally contained in the returned chunk. Preserve source fidelity regardless of quotation length. Existing runtime quote-length checks are migrated separately under #12256 AC-02. For Grade 1, 2, or 3 chunks, missing a learner-facing `>` blockquote is correct; the chunk still must be retrieved and used as grounding.

# V6 Writer Prompt Context Budgets

> **Scope:** Documents the intended context budget and shape for each
> v6 build phase that sends a prompt to an LLM writer.  Used by the
> deterministic prompt audit (`_audit_chunk_prompt`,
> `_audit_rewrite_block_prompt`) and by humans reviewing orchestration
> artifacts.

## Phase Overview

| Phase | Budget | Primary Artifact | Scoped To |
|---|---|---|---|
| **research** | N/A (data assembly) | knowledge-packet.md | module |
| **skeleton** | ≤40 000 chars | v6-skeleton-prompt.md | module |
| **write-chunk** | ≤12 000 chars | v6-chunk-NN-prompt.md | section |
| **rewrite-block** | ≤18 000 chars | rewrite-block prompt | section |

---

## research

**Purpose:** Assemble a knowledge packet from wiki articles, discovery
data, and plan references.

**Context shape:**
- Wiki context (primary — compiled from textbooks, literary texts,
  Wikipedia).  Capped at ~30 000 chars in the packet itself.
- Discovery data (RAG literary + textbook chunks from the discovery
  phase).  Capped at 10 literary + 8 textbook chunks.
- Plan references.

**No LLM prompt** — this phase is deterministic data assembly.
The output feeds into skeleton and write phases.

---

## skeleton

**Purpose:** Generate a paragraph-level structural plan that constrains
the writer to balanced sections.

**Budget:** ≤40 000 chars (`SKELETON_PROMPT_MAX_CHARS`).

**Context shape (components):**
1. `template` — the `v6-skeleton.md` prompt template (~2 000 chars).
2. `plan_content` — the full plan YAML wrapped in a literal block.
3. `knowledge_packet` — the full knowledge packet (truncated at
   30 000 chars if larger).

**What is intentionally included:** The skeleton needs the broadest
context because it must allocate word budgets across all sections and
decide which teaching beats go where.

**Machine-readable manifest:** `v6-skeleton-manifest.yaml` in the
module's orchestration directory.

---

## write-chunk

**Purpose:** Generate prose for ONE H2 section of a module.

**Budget:** ≤12 000 chars (`CHUNK_PROMPT_MAX_CHARS`).

**Context shape (components):**
1. `persona` — writer identity (1-2 lines).
2. `section_skeleton` — the skeleton body for this section only.
3. `section_contract` — the contract slice for this section (current
   section's teaching beats, required terms, scoped activity
   obligations).
4. `section_wiki_excerpts` — wiki excerpt items mapped to this section.
5. `previous_sections_summary` — rolling summary of previously written
   sections (max 500 words), included only from section 2 onward.
6. `paragraph_language_rule` — compact immersion/monolingual rule.
7. `section_rules` — level grammar envelope + activity markers.
8. `dialogue_formatting` — blockquote formatting guide, included
   **only** when the section contains dialogue content.
9. `required_vocab_checklist` — per-section vocab focus or final
   sweep-up, included only when vocabulary is defined.
10. `forbidden_words` — hard-banned Russianisms (~300 chars, always
    included).

**What is intentionally excluded:**
- Full write template (`v6-write.md`) — the chunk prompt is
  self-contained; carrying the 8 000+ char template would exceed the
  budget and repeat rules already distilled into compact helpers.
- Full module contract — only the current section's slice is included.
- Full knowledge packet — section-mapped excerpts replace it.
- Dialogue formatting rules (when section has no dialogue content).

**Machine-readable manifest:** `v6-chunk-NN-manifest.yaml` in the
module's orchestration directory.

---

## rewrite-block

**Purpose:** Surgically rewrite one H2 section to fix a specific
review finding.

**Budget:** ≤18 000 chars (`REWRITE_BLOCK_PROMPT_MAX_CHARS`).

**Context shape (components):**
1. `rewrite_directive` — the reviewer's specific fix instruction.
2. `rewrite_guardrails` — heading preservation, marker preservation.
3. `section_mapped_wiki_excerpts` — wiki excerpts for this section.
4. `current_section` — the existing prose being rewritten.

**What is intentionally excluded:**
- Full module contract (`## Shared Module Contract`).
- Other sections' context (`## Previous Sections For Continuity`).
- Skeleton (`## Skeleton For This Section`).

These exclusions are enforced by `REWRITE_BLOCK_FORBIDDEN_HEADINGS`
and `_audit_rewrite_block_prompt`.

**Machine-readable manifest:** saved alongside the rewrite prompt in
the orchestration directory.

---

## Auditing Prompt Composition

Each phase that emits a manifest can be audited deterministically:

```python
from build.v6_build import (
    _audit_chunk_prompt,
    _audit_rewrite_block_prompt,
)

# Load manifest from orchestration dir
manifest = yaml.safe_load(path.read_text())
failures = _audit_chunk_prompt(manifest)  # or _audit_rewrite_block_prompt
assert failures == [], f"Prompt audit failed: {failures}"
```

The manifest YAML files are committed to orchestration directories
alongside the prompt files, enabling CI-level verification that prompt
composition stays within budget.

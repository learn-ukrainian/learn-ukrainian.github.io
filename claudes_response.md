### Migration logic

1. **Failure recovery path (the 680-unknown-entry bug).**
PARTIAL. The `preserve_from_meta` guard prevents reruns from dropping sources, but a critical failure mode remains if the `.sources.yaml` registry is lost/deleted while the `.md` file still contains migrated `[S1]` tags. `load_sources_registry` returns an empty list, so legacy citations still in the text (e.g. `(Source 5: ext-foo)`) are assigned IDs starting from `S1`. This newly assigned `[S1]` silently hijacks the pre-existing `[S1]` tags in the prose, causing silent content corruption.
Evidence: `scripts/wiki/migrate_sources.py:180` (loads empty registry) and `scripts/wiki/sources_schema.py:155` (starts `next_id` at 1).

2. **Idempotence on fresh runs.**
AGREE. A dry-run followed by a real run, or consecutive real runs, leave identical states. `_ordered_inline_files` is empty on a second run, and `assign_source_ids` deterministically propagates `existing.sources`. No hidden ordering dependencies exist because it iterates over the sorted existing registry.
Evidence: `scripts/wiki/migrate_sources.py:307` (`render_diff` safely uses `.preview.sources.yaml`) and `scripts/wiki/sources_schema.py:133` (preserves existing ordered entries).

3. **Citation-order preservation.**
AGREE. The migration strictly maps 1:1 based on the first unique filename seen in the text, assigning `[S1]`, `[S2]`, etc. It consolidates by filename and completely ignores the legacy `Source N` number for ordering.
Evidence: `scripts/wiki/migrate_sources.py:339` (`_ordered_inline_files` collects by appearance top-to-bottom) and `scripts/wiki/sources_schema.py:155` (`next_id` increments per new unique file).

4. **Cyrillic-contamination handling.**
AGREE. The migration automatically dedupes Cyrillic/Latin variants because all files pass through `normalize_source_filename`, which explicitly normalizes the Cyrillic `клас` prefix to Latin `klas`.
Evidence: `scripts/wiki/sources_schema.py:236` (`re.sub(r"^(\d+)-клас-", r"\1-klas-", value, flags=re.IGNORECASE)`).

5. **Legacy sources preservation.**
AGREE. All uncited sources from `wiki-meta` survive in the sibling registry. They are correctly captured in a `preserved_from_meta` set, passed to `assign_source_ids` where they receive `preserved_from_meta=True`, and are kept in the final registry loop.
Evidence: `scripts/wiki/migrate_sources.py:190` (creates `preserved_from_meta` set) and `scripts/wiki/migrate_sources.py:245` (keeps sources where `entry.preserved_from_meta` is True).

### Schema + consumer integration

6. **`get_wiki_context(include_sources_registry=False)` default.**
DISAGREE. Production module-build callers like `v6_build.py` do not pass this flag, so it defaults to `False`. This makes the registry completely invisible to writers, who only see opaque `[S1]` tags. This is unacceptable, as writers (especially for seminar tracks) need provenance to accurately attribute claims to scholars or primary sources.
Evidence: `scripts/wiki/context.py:66` (default `False`) and `scripts/build/v6_build.py:2714` (calls `get_wiki_context` without `include_sources_registry=True`).

7. **Strip-meta correctness.**
DISAGREE. The `strip_meta` regex uses `.*?` with `re.DOTALL`. If a `wiki-meta` comment is unclosed (e.g., missing `-->`), it will greedily consume all prose up to the NEXT `-->` anywhere in the document (such as a `<!-- VERIFY -->` comment), causing silent content loss.
Evidence: `scripts/wiki/context.py:249` (`re.sub(r"<!--\s*wiki-meta\b.*?-->", "", content, flags=re.DOTALL)`).

8. **Registry validation.**
AGREE. `validate_sources_registry` correctly finds orphans and missing entries. However, during production compilation, it only prints warnings to the console and acts as a silent pass without failing the build.
Evidence: `scripts/wiki/compiler.py:246` (`issues = validate_sources_registry...`) and `scripts/wiki/compiler.py:248` (only prints `⚠️ Sources registry validation issues:`).

### Production readiness

9. **Downstream impact.**
AGREE. There is no downstream breakage. `textbook_refs.py` has been safely updated to check the sibling registry first via `load_sources_registry`, and falls back to regex extraction from the legacy `wiki-meta` block if the registry doesn't have chunks.
Evidence: `scripts/build/textbook_refs.py:100` (`registry = load_sources_registry...`) and `scripts/build/textbook_refs.py:108` (fallback `meta_match = re.search(...)`).

10. **Backward compat.**
AGREE. The consumer handles old pre-migration articles gracefully. `load_sources_registry` returns an empty list if `.sources.yaml` is missing, `strip_meta` removes the `wiki-meta` block, and the old inline citations remain visible in the prose without crashing.
Evidence: `scripts/wiki/sources_schema.py:92` (returns empty registry if path doesn't exist).

### Critical bugs only

11. **List any bug that would cause data loss, silent content corruption, or a downstream consumer to break.**
- **Silent Content Loss (Unclosed Meta):** `strip_meta` regex `r"<!--\s*wiki-meta\b.*?-->"` with `re.DOTALL` will silently delete all prose up to the next `-->` (e.g., `<!-- VERIFY -->`) if the `wiki-meta` block is missing its closing tag.
- **Silent Content Corruption (Lost Registry Rerun):** If `.sources.yaml` is deleted but the `.md` has `[S1]` tags, rerunning `migrate_sources.py` will assign `[S1]` to the first remaining legacy citation, silently hijacking the existing `[S1]` tags in the text to point to the wrong source.
- **Opaque Provenance (Consumer Integration):** `get_wiki_context(include_sources_registry=False)` hides source mappings from the LLM writers in `v6_build.py`, making it impossible for them to accurately attribute claims to specific scholars/primary sources.

**Overall Verdict:** BLOCK MERGE.
The critical bugs, specifically the greedy `strip_meta` regex causing silent content loss and the opacity of provenance to writers, must be patched before this can be safely utilized in production.

**Phase**: Phase 0: Research (Seminar)
**Step**: Full research
**Friction Type**: TOOL_REDUNDANCY
**Raw Error**: Unable to read direct text from litopys.org.ua due to encoding issues in `web_fetch`.
**Self-Correction**: Used targeted `google_web_search` queries with snippets to reconstruct Beauplan's specific descriptions (willow, reeds, dimensions) instead of relying on the full text fetch. Verified against general historical knowledge to ensure accuracy.
**Proposed Tooling Fix**: Improve `web_fetch` encoding handling for legacy Cyrillic sites (CP1251/KOI8-U).

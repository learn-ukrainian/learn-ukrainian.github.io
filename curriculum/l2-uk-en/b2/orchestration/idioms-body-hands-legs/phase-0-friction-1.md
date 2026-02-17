**Phase**: Phase 0: Research (Core)
**Step**: Web Search
**Friction Type**: TOOL_USAGE_ERROR
**Raw Error**: "The 'prompt' must contain at least one valid URL" (from web_fetch when passed a search query)
**Self-Correction**: I realized `web_fetch` requires specific URLs, not search queries. I switched to `google_web_search` to find the information directly.
**Proposed Tooling Fix**: N/A

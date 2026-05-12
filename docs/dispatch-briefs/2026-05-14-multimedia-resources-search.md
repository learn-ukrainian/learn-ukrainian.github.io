# Codex dispatch brief — Multimedia resources (YouTube / blog / video) search + render

> **Issue:** Closes #1932
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/multimedia-resources-2026-05-14/`
> **Base:** `origin/main` (post-#1935 merge)
> **Hard timeout:** 5400s
> **Silence timeout:** 1800s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. Prefix every command with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/multimedia-resources-2026-05-14 && ...` or absolute path.

Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

After #1930 (V7 MDX assembler alignment) shipped, the user noticed the rendered `a1/my-morning` Resources tab contains **only textbook citations** — no YouTube, video, blog, podcast, or audio resources. Per `docs/poc/poc-lesson-design.html` the Resources tab is supposed to be multimedia-inclusive.

The user is fine with a specific module having NO multimedia (some topics legitimately don't have great YouTube content), but **must verify the agent is at least LOOKING** for multimedia. Currently it isn't:

- `wiki_manifest.json` schema has NO `external_resources` / `multimedia` section
- Writer prompt has ZERO directives about YouTube/blog/video search
- `resources.yaml` only contains textbook entries

This PR adds the missing piece end-to-end so the writer **searches** for multimedia per module + emits findings (if any) to `resources.yaml` with appropriate `role` fields, and the assembler renders them with proper icons.

After this merges, re-running the build on a1/my-morning may or may not yield multimedia entries — but the writer telemetry (`writer_tool_calls.json`) MUST show search attempts for at least 1 multimedia category.

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "Wiki manifest schema includes `external_resources`" | `grep -n 'external_resources' scripts/build/phases/wiki_manifest.py` | quote schema addition |
| "Writer prompt directs multimedia search" | `grep -inE 'youtube\|blog\|video\|podcast\|multimedia\|external.search' scripts/build/phases/linear-write.md` | quote new directives |
| "Writer telemetry records the search attempts" | new fixture: after a write phase, telemetry contains ≥1 search call with multimedia-targeted query | quote telemetry assertion |
| "Resources renderer differentiates roles" | new test: a `resources.yaml` with mixed roles → output MDX has 📚/📺/🎥/📝/🎧 icons matching | quote test fixture |
| "Tests pass" | `pytest tests/test_wiki_manifest*.py tests/test_writer_prompt*.py tests/test_generate_mdx_v7_resources_vocab.py -x` | quote summary line |
| "Lint clean" | `ruff check scripts/build/phases scripts/generate_mdx` | quote final line |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4.

---

## Scope (3 layers)

### Layer 1 — Wiki manifest extractor (`scripts/build/phases/wiki_manifest.py`)

Currently extracts: `slug`, `wiki_path`, `sequence_steps`, `l2_errors`, `phonetic_rules`, `decolonization_bans`.

**Add:** `external_resources` — a list extracted from the wiki pedagogy markdown's `## Зовнішні ресурси` section (if present). Each entry should have:
```python
{
    "role": str,           # one of: textbook, youtube, video, blog, podcast, audio, article, wiki
    "title": str,
    "url": str | None,     # required for non-textbook roles
    "author": str | None,
    "description": str | None,
}
```

If the wiki markdown has no `## Зовнішні ресурси` section, return empty list (not error).

Update the manifest's JSON Schema (and the gate that validates it).

### Layer 2 — Writer prompt (`scripts/build/phases/linear-write.md`)

Add a directive block (probably near where `## Wiki Obligations Manifest` lives, post-#1920 restructure):

```md
### External Resources — multimedia search obligation

Every module MUST attempt to find at least one multimedia external resource
(YouTube clip, blog post, podcast episode, video documentary, image gallery)
relevant to the lesson topic. The agent MUST make at least ONE call to:
- `mcp__sources__query_wikipedia` for Ukrainian Wikipedia context, OR
- `mcp__sources__search_external` for blog/article search, OR
- Browser-based search (if available in this dispatch's tool set)

If the wiki manifest's `external_resources` section is non-empty, those
URLs are AUTHORITATIVE — include all of them in `resources.yaml` with
the supplied role.

If the search returns nothing usable, that is acceptable — but the search
attempt MUST be recorded in the writer telemetry. The deterministic
`resources_search_attempted` gate (added by this PR) will fail the build
if the writer skipped the search entirely.

In `resources.yaml`, every entry MUST have a `role` field. Valid roles:
`textbook` (📚), `youtube` (📺), `video` (🎥), `blog` (📝), `podcast` (🎧),
`audio` (🎧), `article` (📄), `wiki` (🔗).
```

### Layer 3 — Resources renderer (`scripts/generate_mdx/resources.py`)

`format_resources_for_mdx()` (added/modified in #1930) currently emits one block per resource. Update it to:
- Group resources by `role` (with section headers like "📚 Books", "📺 Videos", "📝 Articles", "🔗 Online resources")
- Emit appropriate icon per entry based on `role` field
- For multimedia entries (youtube/video/blog/podcast), make the URL the primary link (clickable)
- For textbook entries (no URL), keep the current author/pages/description format

Reference the design at `docs/poc/poc-lesson-design.html` (search for "Resources" or look at the resources/source-box CSS classes for the visual contract).

### Layer 4 (new gate) — `resources_search_attempted`

Add a deterministic gate in `scripts/build/linear_pipeline.py`:

```python
def _resources_search_attempted_gate(
    writer_tool_calls: list[dict],
) -> dict[str, Any]:
    """HARD gate — writer must have called at least one external-search tool.
    
    Eligible tools: mcp__sources__query_wikipedia, mcp__sources__search_external,
    mcp__sources__search_images, or @browser-equivalent.
    """
    SEARCH_TOOLS = {
        "mcp__sources__query_wikipedia",
        "mcp__sources__search_external",
        "mcp__sources__search_images",
        # add browser tools when present
    }
    attempted = [c for c in writer_tool_calls if c.get("tool_name") in SEARCH_TOOLS]
    passed = len(attempted) >= 1
    return {
        "passed": passed,
        "severity": "HARD",
        "search_attempt_count": len(attempted),
        "search_tools_used": sorted({c["tool_name"] for c in attempted}),
    }
```

Wire into `python_qg` flow so a writer who skips multimedia search HALTS the build.

---

## Numbered steps (mandatory checklist)

1. **Worktree setup:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && \
   git fetch origin main --quiet && \
   git worktree add -b codex/multimedia-resources-2026-05-14 .worktrees/dispatch/codex/multimedia-resources-2026-05-14 origin/main
   ```
2. **Layer 1**: Update wiki manifest extractor + schema. Add `external_resources` extraction logic. Update existing fixtures if they assert exact schema shape.
3. **Layer 2**: Add multimedia-search directive to writer prompt. Place it adjacent to existing wiki-obligations directives, not as standalone bottom-of-file rule.
4. **Layer 3**: Update `format_resources_for_mdx()` to group by role + emit icons + handle URLs. Reference POC design lines 110-115 (source-box style) and any multimedia-specific styling.
5. **Layer 4**: Add `resources_search_attempted` gate. Wire into `python_qg`.
6. **Tests**:
   - wiki manifest extractor: fixture wiki markdown with `## Зовнішні ресурси` → asserts `external_resources` list populated correctly.
   - resources renderer: fixture resources.yaml with mixed roles → assert grouped sections + correct icons.
   - gate: fixture writer_tool_calls without any search tool → gate fails; with ≥1 → gate passes.
   - end-to-end: regenerate a1/my-morning MDX (with current dirty source yamls in main checkout — read-only reference) → verify renderer doesn't crash + groups output by role.
7. **Pytest:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/multimedia-resources-2026-05-14 && \
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/test_wiki_manifest*.py tests/test_writer*.py tests/test_generate_mdx_v7_resources_vocab.py tests/test_resources_search_gate.py -x
   ```
   Quote summary.
8. **Ruff:**
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/build scripts/generate_mdx
   ```
9. **Commit** — conventional: `feat(content-pipeline): wiki manifest + writer prompt + assembler + gate for multimedia external resources`. Reference `Closes #1932`.
10. **Push + PR.**
11. **DO NOT auto-merge.**

---

## What blocks the merge

- Wiki manifest extractor doesn't add `external_resources`.
- Writer prompt doesn't direct multimedia search.
- Gate doesn't HALT when search was skipped.
- Resources renderer doesn't group by role or render proper icons.
- Tests failing.
- Ruff failing.
- Regression on a1/my-morning rebuild (assembled MDX should still satisfy the 5 design predicates from #1930 + #1935).

---

## What this does NOT do (out of scope)

- Curating the search corpus / building a multimedia DB (separate work).
- Vetting individual YouTube clips for pedagogical fit (writer's pedagogical judgment, not a deterministic gate).
- Forcing every module to have multimedia — the gate only enforces SEARCH ATTEMPT, not search RESULT count > 0.

---

## Pre-submit checklist

- [ ] `.python-version` unchanged (`3.12.8`)
- [ ] `.yamllint` / `.markdownlint.json` unchanged
- [ ] No generated artifacts in diff
- [ ] No `sys.executable` — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass`
- [ ] Every changed file directly related to multimedia resources
- [ ] Total files changed < 15

---

## Related

- Predecessor PRs: #1920 (wiki obligations manifest), #1930 (V7 MDX assembler alignment), #1935 (Tab 3 dedupe + vocab order)
- Design reference: `docs/poc/poc-lesson-design.html`
- Tracked issue: #1932
- Live writer output: `curriculum/l2-uk-en/a1/my-morning/resources.yaml` (read-only reference — currently 3 textbook entries only)
- Live wiki manifest: `curriculum/l2-uk-en/a1/my-morning/wiki_manifest.json` (read-only reference — currently missing `external_resources`)

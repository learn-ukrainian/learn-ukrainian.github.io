# Codex dispatch brief — Writer prompt resources.yaml schema-alignment directive (#1959)

> **Issue:** #1959 — `[writer-prompt] linear-write.md doesn't tell writer that non-textbook resource roles REQUIRE url field`
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/writer-prompt-resources-schema-2026-05-13/`
> **Base:** `origin/main` (currently `7bed977983`)
> **Hard timeout:** 3600s
> **Silence timeout:** 1200s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. CWD does NOT persist. Prefix every command with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/writer-prompt-resources-schema-2026-05-13 && ...` or absolute path. Inside the worktree, `.venv/` is gitignored — use MAIN checkout's `.venv` via absolute path: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

P0 unblock for Phase 2a m20 (`a1/my-morning`) V7 rebuild. Issue #1959 has the full diagnosis. Single-file prompt edit + targeted regression test + commit/push/PR. The wiki ingestion gap (#1960) is a separate, deeper fix not in scope here.

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "Writer prompt now states the schema rule for non-textbook roles" | `grep -n 'role: textbook\|requires url\|OMIT THE ENTRY\|non-textbook' scripts/build/phases/linear-write.md` | quote grep output |
| "Existing prompt template still loads without parse error" | `.venv/bin/python -c 'from pathlib import Path; print(len(Path("scripts/build/phases/linear-write.md").read_text()))'` | quote line length count |
| "Tests pass" | `.venv/bin/pytest tests/build/test_linear_pipeline.py -v` | quote final summary line |
| "Lint clean" | `.venv/bin/ruff check scripts/build/` (no .py changes expected, but sanity) | quote final line |
| "PR opened" | `gh pr view <N> --json url` | quote URL |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4. Quote.

---

## The fix — single insert in linear-write.md

File: `scripts/build/phases/linear-write.md`

Currently lines 199-220 read:

```markdown
### External Resources — multimedia search obligation

Every module MUST attempt to find at least one multimedia external resource
(YouTube clip, blog post, podcast episode, video documentary, image gallery)
relevant to the lesson topic. The agent MUST make at least ONE call to:
- `mcp__sources__query_wikipedia` for Ukrainian Wikipedia context, OR
- `mcp__sources__search_external` for blog/article search, OR
- `mcp__sources__search_images` for image/gallery discovery, OR
- browser-based search if available in this dispatch's tool set.

If the Wiki Obligations Manifest's `external_resources` section is non-empty,
those URLs are AUTHORITATIVE — include all of them in `resources.yaml` with the
supplied role.

If the search returns nothing usable, that is acceptable — but the search
attempt MUST be recorded in the writer telemetry. The deterministic
`resources_search_attempted` gate fails the build if the writer skipped the
search entirely.

In `resources.yaml`, every entry MUST have a `role` field. Valid roles:
`textbook` (📚), `youtube` (📺), `video` (🎥), `blog` (📝), `podcast` (🎧),
`audio` (🎧), `article` (📄), `wiki` (🔗).
```

Insert a new paragraph immediately after the "Valid roles" line (after line 220, before the existing "### Phonetic rules" heading on line 222). The exact insert:

```markdown
**Schema rule for non-textbook roles: `url:` is REQUIRED.**

The deterministic schema enforces:
- `role: textbook` entries do NOT require `url:`.
- All other roles (`youtube`, `video`, `blog`, `podcast`, `audio`, `article`, `wiki`) REQUIRE a non-empty `url:` field. Schema validation halts the build on any missing URL for these roles.

If you cannot provide a **verified** URL for a non-textbook entry — e.g. the multimedia search returned no usable URL, or the wiki source registry shows only a placeholder identifier like `ext-article-N` with no real title and no URL — **OMIT THE ENTRY ENTIRELY**. Do not emit:

- `url: null`
- `url: ""`
- `url: TBD`
- the entry without the `url:` field

All four patterns fail schema validation. The `resources_search_attempted` gate counts the multimedia search **attempt** in your telemetry, so honest omission of an unverifiable entry does NOT regress the search-obligation gate. Truthful omission is preferred over schema violation (compare MEMORY #M-4: deterministic over hallucination).

```

Add ONE blank line after the inserted paragraph before the existing `### Phonetic rules` heading. Do not remove any existing content.

---

## Test — single regression test in test_linear_pipeline.py

Find a small test that exercises the linear-write phase template loading or the `resources.yaml` schema enforcement path. If `tests/build/test_linear_pipeline.py` has a fixture-rendered prompt test, ADD an assertion to it that confirms the new directive is present.

Most likely test pattern: render the template once and grep for the new phrasing:

```python
def test_linear_write_prompt_documents_non_textbook_role_url_requirement() -> None:
    """Regression for #1959. The writer must be told the schema rule that
    non-textbook resource entries require url:. Previously the prompt
    listed valid roles but never explained the schema constraint,
    leaving the writer to discover it via a build halt."""
    template_path = (
        Path(__file__).resolve().parents[2]
        / "scripts/build/phases/linear-write.md"
    )
    template = template_path.read_text(encoding="utf-8")
    assert "role: textbook" in template, (
        "Template should reference role: textbook in the schema-rule explanation"
    )
    assert "OMIT THE ENTRY" in template, (
        "Template should instruct the writer to omit entries without verifiable URL"
    )
    assert "requires url" in template.lower() or "require a non-empty `url:`" in template, (
        "Template should explicitly state non-textbook roles require url"
    )
```

Place this test adjacent to `test_linear_write_prompt_carries_anti_meta_narration_directive` (similar shape — they both validate prompt-template content).

---

## Execution steps (numbered)

1. **Read the current template section to confirm line numbers haven't drifted:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/writer-prompt-resources-schema-2026-05-13 && sed -n '195,225p' scripts/build/phases/linear-write.md
   ```
   Confirm the "Valid roles" line is at the position the brief expects. If the section has been refactored since `main@7bed977983`, **STOP and report** — the insert site may have moved.

2. **Make the insert in `scripts/build/phases/linear-write.md`** as specified above. Use an Edit tool with enough context to make the change unique (e.g. the trailing `audio` (🎧), `article` (📄), `wiki` (🔗).` line + the upcoming `### Phonetic rules` heading).

3. **Add the regression test** in `tests/build/test_linear_pipeline.py` adjacent to `test_linear_write_prompt_carries_anti_meta_narration_directive` (use grep to locate the right spot).

4. **Run targeted pytest:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/writer-prompt-resources-schema-2026-05-13 && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/build/test_linear_pipeline.py -v 2>&1 | tail -30
   ```
   Quote the summary line — must include the new test passing.

5. **Lint:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/writer-prompt-resources-schema-2026-05-13 && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/build/ tests/build/test_linear_pipeline.py 2>&1 | tail -5
   ```
   Quote final line.

6. **Commit:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/writer-prompt-resources-schema-2026-05-13 && git add -A && git commit -m "$(cat <<'INNEREOF'
   fix(writer-prompt): document non-textbook role URL requirement in linear-write.md (#1959)

   m20 (a1/my-morning) V7 build under Card 1 writer-isolation halted at
   resources.yaml schema validation: role 'podcast' requires url. Writer
   behavior was correct per MEMORY #M-4 (refused to fabricate URL when
   external-search returned no verified result), but the writer prompt
   never told the writer that role: textbook is the only role allowed
   without url:. Writer kept the entry instead of dropping it.

   Add an explicit directive after the Valid roles list in
   scripts/build/phases/linear-write.md: state the schema constraint,
   list the four failing url-emission patterns to avoid, and reinforce
   that honest omission is preferred over schema violation. Add a
   regression test in tests/build/test_linear_pipeline.py mirroring the
   adjacent anti-meta-narration directive check.

   Wiki ingestion gap (ext-article-N placeholder stubs in
   wiki/pedagogy/*.sources.yaml without real titles/URLs) is the deeper
   architectural problem this surfaces; tracked separately at #1960.

   Closes #1959.

   X-Agent: codex/writer-prompt-resources-schema-2026-05-13

   Co-Authored-By: Codex GPT-5.5 <noreply@openai.com>
   INNEREOF
   )"
   ```

7. **Push:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/writer-prompt-resources-schema-2026-05-13 && git push -u origin codex/writer-prompt-resources-schema-2026-05-13
   ```

8. **Open PR (NO auto-merge):**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/writer-prompt-resources-schema-2026-05-13 && gh pr create --title "fix(writer-prompt): document non-textbook role url requirement (#1959)" --body "$(cat <<'INNEREOF'
   ## Summary

   - Single-file prompt template edit: adds a "Schema rule for non-textbook roles: \`url:\` is REQUIRED" directive to \`scripts/build/phases/linear-write.md\` § "External Resources" after the Valid roles list.
   - Instructs the writer to OMIT entries with no verifiable URL for non-textbook roles, NOT emit them with placeholder/missing URL (which the schema rejects).
   - Reinforces MEMORY #M-4 alignment: honest omission preferred over schema violation.
   - Regression test in \`tests/build/test_linear_pipeline.py\` asserts the directive's key phrases.

   ## Why

   m20 (\`a1/my-morning\`) V7 build under Card 1 writer-isolation halted on 2026-05-13 at \`resources.yaml\` schema validation with \`role 'podcast' requires url\`. Tier 1 verification (writer-isolation gates) was clean. The writer (\`claude-tools\`) correctly refused to fabricate a URL per #M-4 but kept the entry instead of omitting it — because the writer prompt never explained the schema constraint.

   ## Test plan

   - [x] \`pytest tests/build/test_linear_pipeline.py -v\` — all green including new regression test
   - [x] \`ruff check scripts/build/ tests/build/test_linear_pipeline.py\` — clean
   - [ ] Follow-up: re-run m20 V7 build under Monitor (orchestrator handles post-merge)

   ## Related

   - **Surfaces** #1960 (wiki ingestion gap: \`ext-article-N\` placeholder stubs in \`wiki/pedagogy/*.sources.yaml\` — deeper architectural fix, tracked separately).
   - **Builds on** #1957 (writer-output parser fix — m20's first halt) and #1953 (Card 1 writer-isolation).

   Closes #1959.

   🤖 Generated with [Codex CLI](https://github.com/openai/codex-cli)
   INNEREOF
   )"
   ```

9. **Do NOT merge.** Print the PR URL via \`gh pr view --json url\` so the orchestrator picks it up.

---

## Acceptance criteria

- [ ] Branch `codex/writer-prompt-resources-schema-2026-05-13` pushed.
- [ ] PR opened, URL printed.
- [ ] `pytest tests/build/test_linear_pipeline.py -v` shows new test passing + existing tests still green.
- [ ] `ruff check` clean.
- [ ] Commit body has `Closes #1959` + X-Agent trailer.

## On halt

If you hit any of these, STOP and report in the final task output:

- Lines 199-225 of `linear-write.md` look different from what this brief shows → the section was refactored; the insert site has moved. Report the new section structure.
- The proposed test pattern (`test_linear_write_prompt_carries_anti_meta_narration_directive`) doesn't exist or has a different shape → mirror whatever the adjacent prompt-content test looks like instead, but keep the assertions about the new directive.
- Unrelated test failures appear → quote them, don't try to fix them (those are #1958-class drift).

Do not deviate from the single-file insert + single-test pattern. The fix is intentionally minimal — schema/wiki-ingestion broader work is out of scope.

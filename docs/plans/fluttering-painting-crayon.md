# Plan: Resolve 6 Open Coding Issues (#857, #875, #873, #872, #877, #878)

## Context

20 issues were triaged — 15 review artifacts + 5 completed issues closed. 6 coding issues remain with real work. These are all children of the template stabilization effort (#871). Tackling them together since they're interdependent: #875 (delete stale templates) unblocks #872 (split phases), #873 (port immersion) needs to know which templates survive.

---

## Issue 1: #857 — Clean up v3/v4 refs in dashboards

**Files to change (3 files, ~10 lines):**

| File | Lines | Change |
|------|-------|--------|
| `playgrounds/quality.html` | 79, 414-416 | Remove `.tag-v3` CSS. Change JS to use generic `tag-legacy` or remove the tag entirely |
| `playgrounds/curriculum-dashboard.html` | 61, 226 | Remove `.ver-v3` CSS selector. Simplify version ternary to `v5` vs `unbuilt` |
| `playgrounds/comms.html` | 292-293, 469, 489 | Update `v3-` to `v5-` in task ID regex, template literal, and string replace |

No sandbox or phase-D refs found (already clean).

---

## Issue 2: #875 — Clean up stale beginner templates

**Action:**
1. Delete `claude_extensions/phases/gemini/beginner-full.md` — never selected by code
2. Delete `claude_extensions/phases/gemini/beginner-content.md` — never selected by code
3. `_get_content_template()` at `scripts/pipeline/core.py:578` already always returns `beginner-full-rag.md` for beginner tier — no code change needed
4. Add test in `tests/test_pipeline_v5.py`: assert template selection returns `beginner-full-rag.md` for A1 and A2/1-20

---

## Issue 3: #873 — Port immersion fixes to core and seminar templates

**What's missing in `core-content.md`:**
- No "tables = zero immersion" warning
- No container priority (dialogues/lists over tables)
- No explicit structural containment rule

**What's missing in `content.md` (seminar):**
- Same, adapted for 98-100% immersion (seminar is almost all Ukrainian)

**Action:** Add an immersion rules section to both templates. The rules already exist in `beginner-full-rag.md` lines 115-138. Adapt for each tier's immersion target:
- Core (B1+): 85-100% — tables still zero, but immersion is mostly Ukrainian prose anyway
- Seminar: 98-100% — tables zero is critical since seminars are full Ukrainian

Insert after `{STRUCTURAL_RULES}` placeholder in each template. Keep it brief (5-8 lines) since core/seminar modules have higher immersion naturally.

Also check `beginner-checkpoint.md` and `core-checkpoint.md` — beginner checkpoint already has it, core checkpoint needs it.

---

## Issue 4: #872 — Separate content and activity phases

**Current state:** `full_build` defaults to `False`. Both modes use `beginner-full-rag.md`. In split mode, the activity delimiters in the template output are simply ignored. This already works correctly.

**What's actually broken per the issue:** Nothing in the pipeline code. The issue was filed when `beginner-content.md` (broken placeholders) was selected for `--no-full-build`. Since `_get_content_template()` now always returns `beginner-full-rag.md` regardless of `full_build`, this is already fixed.

**Remaining AC:** "When content fails validate, activities are NOT rebuilt on next attempt" — check if this is true. Activities run AFTER validate in v5 phase order (`PHASES = ["research", "discover", "content", "validate", "activities", "review", "mdx"]`), so if validate loops on fixes, activities haven't been built yet. This is correct by design.

**Action:** Verify all ACs are met, add a comment to the issue documenting this, close it.

---

## Issue 5: #877 — VESUM whitelist for proper names

**Where:** `scripts/rag/rag_batch_verify.py` — add proper name detection before status determination (around line 425).

**Implementation:**
1. Add `PROPER_NAME_WHITELIST` set to `scripts/audit/config.py` with common Ukrainian names (Микола, Олег, Олена, Тарас, Іван, Київ, Україна, etc.) and abbreviations (IT, ІТ, PR, HR, ЗНО, etc.)
2. Add capitalization heuristic: if a word starts with uppercase and is not sentence-initial, treat as potential proper name
3. In `verify_module()` at line 425: before marking as ❌, check if word is in whitelist or matches proper name heuristic → mark as `ℹ️` (INFO) instead of `❌`
4. In `screen.py` line 360: filter proper name results from the `not_found` list so they don't become deterministic issues

**Config location:** `scripts/audit/config.py` alongside existing level configs.

---

## Issue 6: #878 — Gemini interactive mode hangs

**Root cause from investigation:** `gemini-cli -m model -y` opens interactive mode. When Gemini's response is slow or the model enters a "waiting" state, the process hangs until timeout. The `-y` flag auto-approves tool use but doesn't prevent interactive mode hangs.

**Action — add diagnostics (investigation, not a full fix):**
1. In `dispatch.py` `dispatch_gemini_raw()`: log prompt size before dispatch (`len(prompt)` chars)
2. In `_gemini.py` `_run_gemini_attempt()`: log first 200 chars of prompt being sent
3. In `dispatch.py`: when timeout occurs, log the model and prompt size alongside the timeout message
4. In `_gemini.py` `_stream_with_watchdog()`: detect stall (no output for 120s) and log diagnostic before timeout
5. Add stderr capture on timeout — gemini-cli may print diagnostic info to stderr

This addresses the investigation ACs. The actual fix (if `-y` isn't sufficient) would be a follow-up.

---

## Execution Order

1. **#857** — dashboard cleanup (standalone, no deps)
2. **#875** — delete stale templates + add test
3. **#873** — port immersion fixes to surviving templates
4. **#872** — verify ACs met and close
5. **#877** — VESUM whitelist
6. **#878** — Gemini hang diagnostics

## Verification

- `npm run claude:deploy` after template changes (sync claude_extensions → .claude)
- `.venv/bin/ruff check` on all changed .py files
- `.venv/bin/python -m pytest tests/test_pipeline_v5.py -x` after pipeline changes
- Open each dashboard HTML in browser to verify no JS errors (manual)
- Run VESUM verify on a module with proper names to verify whitelist works

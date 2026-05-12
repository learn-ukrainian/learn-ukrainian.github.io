# Codex dispatch brief — VESUM gate normalization + ADR-008 fix-block parser markdown handling

> **Issues:** #1921 (VESUM gate normalization), #1922 (ADR-008 parser)
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/vesum-norm-fixblock-2026-05-14/`
> **Base:** `origin/main` (currently `1d57748f6f`)
> **Hard timeout:** 7200s
> **Silence timeout:** 1800s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. CWD does NOT persist across blocks. Every command that uses `.venv/`, `scripts/`, or files in MAIN checkout MUST be prefixed with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/vesum-norm-fixblock-2026-05-14 && ...` or absolute path.

Inside the worktree, `.venv/` is gitignored. Use MAIN checkout's `.venv` via absolute path: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Bundle the two HARD-blocker bugs that halted the first V7 wiki-obligations e2e build of `a1/my-morning` on 2026-05-12. Both bugs live in `scripts/build/linear_pipeline.py`, both are mechanical normalization/parser fixes, and a single PR is cleaner than two. The bugs are independent in code but co-arise from a common root: writer-emitted Ukrainian forms decorated with combining acute stress marks AND markdown bold wrappers (`вмива́ю**ся**`) that the gate + correction-fix-block parser don't normalize before processing.

After this PR merges, the next V7 e2e build of `a1/my-morning` should not halt at `python_qg`'s vesum gate (#1921) and a `<fixes>` block from the reviewer with markdown formatting inside `<find>` content nodes should parse cleanly (#1922).

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "VESUM gate normalizes stress + markdown before lookup" | `grep -n 'normalize\|combining\|U+0301\|\\\\b\\*\\*' scripts/build/linear_pipeline.py` shows new normalization step in the vesum-lookup path | quote the grep output |
| "Fix-block parser handles markdown chars in content nodes" | `.venv/bin/pytest tests/ -k 'fix_block or fixes_parser or reviewer_fixes' -v` | quote test names + summary |
| "End-to-end repro: `вмива́ю**ся**` passes both gate + parser" | new fixture test asserts: (a) lemma resolves to `вмиваюся` and VESUM-hits; (b) `<find>вмива́ю**ся**</find>` parses to the same find-string | quote the test fixture + assertion |
| "Tests pass" | `.venv/bin/pytest tests/test_linear_pipeline*.py tests/test_*vesum* tests/test_*fix*` | quote final summary line |
| "Lint clean" | `.venv/bin/ruff check scripts/build/linear_pipeline.py` | quote final line |

Inline "I checked X" claims without quoted raw output = hallucination per #M-4. Quote.

---

## Bug 1: VESUM gate rejects stress-marked + bold-wrapped forms (#1921)

**Evidence:** `curriculum/l2-uk-en/a1/my-morning/python_qg.json` (from the 2026-05-12 halted build, still in working tree). The vesum gate received lemmas like `вмива́ю**ся**` (combining acute U+0301 between `а` and `ю`; markdown bold `**ся**`) and reported them as missing.

**Root cause:** the VESUM-lookup path passes raw lemmas to lookup without stripping (a) combining marks (U+0300, U+0301), (b) markdown formatting wrappers (`**...**`, `*...*`, backticks, `_..._`).

**Fix:** normalize lemmas **before VESUM lookup**, in a single helper. Pseudo:

```python
def _normalize_for_vesum(lemma: str) -> str:
    # Strip combining diacritics
    s = unicodedata.normalize("NFD", lemma)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = unicodedata.normalize("NFC", s)
    # Strip markdown formatting wrappers
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)", r"\1", s)  # single * not part of **
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"(?<![_a-zA-Z0-9])_([^_]+)_(?![_a-zA-Z0-9])", r"\1", s)
    return s.strip()
```

Apply at the gate boundary — do NOT mutate the lemma stored in the JSON for telemetry (preserve original in `missing` reports so the writer-side issue stays visible).

**Find the gate:** `grep -n 'vesum\|VESUM\|verify_word\|missing_count' scripts/build/linear_pipeline.py`.

**Test it:** add fixtures in the vesum-gate tests:
- `вмива́ю**ся**` → normalized to `вмиваюся` → VESUM hit (use `mcp__sources__verify_word` indirectly, or mock the VESUM client to assert it received `вмиваюся`).
- `вмива́ю` alone (just stress) → `вмиваю` → VESUM hit.
- `**ся**` alone (just bold) → `ся` → VESUM hit.
- Edge case: `чу́до**в**` (stress + bold not at end) — confirm both strips compose correctly.

---

## Bug 2: ADR-008 reviewer-fixes XML parser fails on markdown bold inside `<find>` (#1922)

**Evidence from telemetry:** `writer_correction_unparseable` / `reviewer_fixes_unparseable` events from the same build:

```
{"event": "reviewer_fixes_unparseable", "gate": "vesum_verified",
 "response_preview": "<fixes>\n  <fix>\n    <find>вмива́ю**ся**</find>\n    <replace>вмиваюся</replace>\n  </fix>...\""}
```

Build halted with: `Python QG failed after ADR-008 correction paths`.

**Root cause:** the parser that extracts `<find>`/`<replace>` pairs from the reviewer's `<fixes>` block (per ADR-008, reviewer-as-fixer pattern) chokes on markdown formatting characters inside content nodes. The parser is likely regex-based or uses naive XML splitting that mishandles `*` inside text payloads.

**Find the parser:** `grep -n 'reviewer_fixes_unparseable\|<fixes>\|extract_fix\|parse_fix\|<find>' scripts/build/linear_pipeline.py` and adjacent helpers (`scripts/build/correction_paths.py` if it exists).

**Fix shape:** prefer a robust XML-fragment parser (e.g. `xml.etree.ElementTree` parsing a wrapped root `<root>{block}</root>`, or `lxml` lenient mode) that treats `<find>` / `<replace>` content as plain text payload. Markdown `*`, `_`, backticks must round-trip verbatim — these are LEGAL inside XML text nodes.

If the parser must remain regex (preserves existing test surface), use non-greedy match with explicit content capture: `<find>(.*?)</find>\s*<replace>(.*?)</replace>` with `re.DOTALL` — but the safer fix is `ElementTree`.

**Test it:** add fixtures in the fix-block-parser test suite:
- Exact failing input from this build: `<fix><find>вмива́ю**ся**</find><replace>вмиваюся</replace></fix>` → 1 find/replace pair, content matches verbatim.
- Multi-pair fixture with mixed markdown chars across pairs (`*italic*`, `**bold**`, `` `code` ``).
- Edge case: empty `<replace></replace>` (deletion); content with `<` or `>` chars NOT meant as XML tags — these need entity-encoding upstream, but the parser should at minimum NOT crash on them.

---

## Numbered steps (mandatory checklist)

1. **Worktree setup:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian && \
   git worktree add -b codex/vesum-norm-fixblock-2026-05-14 .worktrees/dispatch/codex/vesum-norm-fixblock-2026-05-14 origin/main
   ```
2. **File-level work** — fix both bugs in `scripts/build/linear_pipeline.py` (extract helpers if cleaner). Aim for minimal surface; each fix ~20-50 LOC including tests.
3. **Test suite** — add focused tests for both bugs. Then run:
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/vesum-norm-fixblock-2026-05-14 && \
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/test_linear_pipeline*.py tests/test_*vesum* tests/test_*fix* -x
   ```
   Quote final summary line raw.
4. **Ruff:**
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/build/linear_pipeline.py
   ```
   Quote final line raw.
5. **Regression check** — write a small driver that re-runs the gate + fix-block parser on the actual halted artifact at `curriculum/l2-uk-en/a1/my-morning/python_qg.json` (read it from MAIN via absolute path; do NOT modify it). Confirm: (a) the previously-missing decorated forms now hit VESUM after normalization, (b) a synthetic `<fixes>` block with the exact failing content parses cleanly. Capture before/after JSON or assertions in the PR body.
6. **Commit** — one or two commits, conventional message: `fix(linear_pipeline): normalize stress+markdown before VESUM lookup; robust XML parser for reviewer fix-block`. Reference `Closes #1921, #1922`.
7. **Push:** `git push -u origin codex/vesum-norm-fixblock-2026-05-14`.
8. **Open PR** via `gh pr create`. Body must include:
   - Quoted reproducer for each bug (raw failing input + raw fixed input)
   - Test run summary line
   - Ruff summary line
   - `Closes #1921`, `Closes #1922`
9. **DO NOT auto-merge.** Hand back for review.

---

## What blocks the merge

- Either fix not actually resolving the reproducer.
- Tests failing.
- Ruff failing.
- A behavior change to other VESUM-gate callers (e.g. accidentally accepting clearly-malformed lemmas like raw HTML or numeric tokens).
- Normalization applied to TELEMETRY (the missing list should preserve the ORIGINAL decorated form so writer-side issues stay visible).

---

## Pre-submit checklist (per AGENTS.md:11-26)

- [ ] `.python-version` unchanged (must be `3.12.8`)
- [ ] `.yamllint` and `.markdownlint.json` unchanged
- [ ] No `status/*.json`, `audit/*-review.md`, or `review/*-review.md` files in diff
- [ ] No `sys.executable` — use `.venv/bin/python`
- [ ] No `@pytest.mark.skip` with empty `pass` bodies
- [ ] No assertions weakened (`is True` → `isinstance(..., bool)`)
- [ ] Every changed file directly related to the two bug fixes
- [ ] Total files changed < 20

---

## Related

- Predecessor handoff: `docs/session-state/2026-05-13-night-wiki-obligations-e2e-brief.md`
- Halted build artifact: `curriculum/l2-uk-en/a1/my-morning/python_qg.json` (left in working tree intentionally — read-only reference)
- Architecture: ADR-008 (reviewer-as-fixer pattern, `docs/decisions/2026-04-XX-adr-008-reviewer-fix-block.md` or equivalent)

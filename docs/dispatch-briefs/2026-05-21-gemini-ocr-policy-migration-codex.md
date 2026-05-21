# Brief: Migrate bulk_ocr_gemini.py to gemini-cli Policy Engine

> **Agent**: Codex (mechanical-with-design-judgment — novel script modification + needs to read external docs + small test cycle)
> **Mode**: danger (autonomous, dispatched via `scripts/delegate.py`)
> **Scope**: single script + new policy file + small test
> **Why now**: BULK_QUALITY_HALT at 2026-05-21 04:59 traced to deprecated `--allowed-tools` flag silently ignored by gemini-cli 0.42.0; model freely tries `web_fetch` which errors and accumulates to >5% failure rate in 100-page rolling window.

---

## 1. Diagnostic chain (verified, do NOT re-debug)

1. `scripts/etymology/bulk_ocr_gemini.py:374-389` invokes `gemini` with:
   ```
   --allowed-tools read_file
   -y
   ```
2. `gemini --help` on installed version 0.42.0 says:
   ```
   --allowed-tools  [DEPRECATED: Use Policy Engine instead See https://geminicli.com/docs/core/policy-engine] Tools that are allowed to run without confirmation  [array]
   ```
3. Deprecated = silently a no-op. Combined with `-y` (yolo auto-approves ALL tools), the model can call any tool.
4. Observed effect (per `audit/etymology-ocr-feasibility/bulk-run-log.jsonl` last entries):
   ```
   Error executing tool web_fetch: The 'prompt' must contain at least one valid URL (starting with http:// or https://).
   ```
5. 21 such errors in last 100 pages (mostly vol6/p0006–p0047 range) tripped `BULK_QUALITY_HALT page=vol6/p0047 errors_last_100=21`.

Do NOT re-investigate root cause. Build the fix.

---

## 2. Task (numbered, execute in order)

### Step 1 — worktree setup

```bash
git worktree add .worktrees/codex/gemini-ocr-policy -b codex/gemini-ocr-policy origin/main
cd .worktrees/codex/gemini-ocr-policy
```

### Step 2 — read the Policy Engine docs

Fetch and read https://geminicli.com/docs/core/policy-engine (or whatever the canonical URL resolves to). Identify:
- Policy file format (YAML / JSON / TOML?)
- How to deny all tools except an allowlist
- Whether the policy attaches via `--policy <file>` (already confirmed via `gemini --help`) or requires settings.json change
- Whether the policy interacts cleanly with `-y` (yolo mode)

If the docs are unreachable, fall back to inspecting the installed gemini-cli's example policies — try `find $(npm root -g)/@google/gemini-cli -name '*.policy*' -o -name '*policy*.yaml' 2>/dev/null` and `gemini --help policy` if that subcommand exists.

### Step 3 — author the policy file

Create `scripts/etymology/gemini-ocr-policy.yaml` (or whatever format the engine expects; rename file extension accordingly). Policy intent:

- **DENY** every tool by default
- **ALLOW** only `read_file` (the OCR pipeline needs to read the image attached via `@<path>`)
- If the engine requires explicit named denies (some engines don't have a wildcard), at minimum DENY: `web_fetch`, `web_search`, `shell_command`, `bash`, `write_file`, `edit_file`, `code_execution`

Add a header comment in the file explaining: "Tool restriction for bulk OCR; replaces deprecated `--allowed-tools read_file` flag in `bulk_ocr_gemini.py`."

### Step 4 — wire the script to the policy

Edit `scripts/etymology/bulk_ocr_gemini.py` around line 374-389:

- **Remove** `--allowed-tools` and `read_file` args (lines 382-383).
- **Add** `--policy` flag pointing to the policy file (resolve via `ROOT / "scripts/etymology/gemini-ocr-policy.yaml"` or equivalent).
- **Keep** `-y` (yolo) so the script doesn't hang on tool-approval prompts; the policy DENY now does the real restriction work.

Also update the stderr suppression regex around `bulk_ocr_gemini.py:76-81` if it mentions `allowed-tools` — that warning will go away once the flag is removed; the suppression line can be deleted (don't suppress a warning that no longer fires).

### Step 5 — smoke test (verifiable; required)

Run a one-page invocation against an already-OCRed page (or a small known page) to confirm:
1. `gemini` exits 0.
2. No `Error executing tool web_fetch` (or any other tool-execution error) in stderr.
3. Output is non-empty Ukrainian text.

Suggested test command (from worktree root):
```bash
ln -s ../../../.venv .venv  # symlink main project venv into worktree
.venv/bin/python -c "
import asyncio, sys
sys.path.insert(0, 'scripts/etymology')
from bulk_ocr_gemini import Page, run_gemini_once, prepare_gemini_image
from pathlib import Path
# Use a page that already exists so we don't waste tenant quota; just validate the invocation
# Pick any vol1 page since vol1 is 100% complete
async def main():
    # Build a Page object for vol1/p0001 (file paths per script convention)
    # Adjust if the script's Page model needs different construction
    ...
asyncio.run(main())
"
```

If the smoke test is non-trivial to author standalone, the alternative is to run `bulk_ocr_gemini.py` with a tiny page-limit cap (if it supports one) — check `--help` for a flag. If neither works, run the full script for ~3 minutes and SIGTERM once you've confirmed 1-2 fresh pages landed without `Error executing tool` lines in `/tmp/bulk-ocr-2026-05-21-codex.log`.

**Required evidence to include in PR body** (per #M-4):
- Command + cwd + raw stderr proving zero tool-execution errors on the smoke test
- `git diff scripts/etymology/bulk_ocr_gemini.py | head -40` raw output
- `cat scripts/etymology/gemini-ocr-policy.yaml` raw output

### Step 6 — tests + lint

```bash
ln -s ../../../.venv .venv  # symlink main project venv into worktree (if not done in Step 5)
.venv/bin/python -m pytest tests/test_bulk_ocr_gemini.py 2>&1 | tail -20
.venv/bin/ruff check scripts/etymology/bulk_ocr_gemini.py
```

If `tests/test_bulk_ocr_gemini.py` doesn't exist, search for the test file with `find tests -name '*ocr*' -o -name '*gemini*'`. Skip if none exist; note in PR body.

### Step 7 — commit + push + PR

```bash
git add scripts/etymology/bulk_ocr_gemini.py scripts/etymology/gemini-ocr-policy.yaml
git commit -m "$(cat <<'EOF'
fix(ocr): migrate gemini-cli tool restriction from deprecated --allowed-tools to Policy Engine

gemini-cli 0.42.0 deprecated --allowed-tools (silent no-op). Combined with
-y yolo mode, the OCR run could freely invoke web_fetch and other tools,
which errored on invalid prompts and accumulated to BULK_QUALITY_HALT at
21 errors / 100-page window on 2026-05-21 04:59.

Fix: deny-all-by-default policy file; only read_file allowed (needed to
attach the OCR image via @<path>).

Smoke test: <paste command + stderr proving zero Error executing tool lines>
EOF
)"

git push -u origin codex/gemini-ocr-policy

gh pr create --title "fix(ocr): migrate gemini-cli tool restriction to Policy Engine" --body "$(cat <<'EOF'
## Summary
- Replace deprecated `--allowed-tools` flag with `--policy` + new `scripts/etymology/gemini-ocr-policy.yaml`
- Unblocks ESUM OCR (BULK_QUALITY_HALT at 04:59 traced to model wandering into web_fetch tool calls because the old flag is silently no-op in gemini-cli 0.42.0)

## Diagnostic chain
<paste from Step 1 of brief, verbatim>

## Smoke test evidence
\`\`\`
<paste command + cwd + raw stderr>
\`\`\`

## Test plan
- [x] One fresh page OCRs with zero `Error executing tool` lines
- [x] ruff clean
- [x] pytest <skipped if no relevant test file>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### Step 8 — NO auto-merge

Stop after `gh pr create`. The orchestrator (me) merges manually after reviewing the diff + smoke test evidence + checking CI green.

---

## 3. Anti-fabrication guard rails (per #M-4)

| Claim | Required evidence in PR body |
|---|---|
| "Policy Engine docs read" | URL fetched + key fact quoted (e.g. policy file format) |
| "Smoke test passed" | Literal command + raw stderr showing zero tool-execution errors |
| "ruff clean" | `ruff check` raw exit + final line |
| "PR opened" | URL returned by `gh pr create` |

A bare "I tested it and it works" without quoted tool output gets the PR rejected on review.

---

## 4. Out of scope

- Do NOT change the BULK_QUALITY_HALT threshold.
- Do NOT change the writer model from `gemini-2.5-flash`.
- Do NOT touch the audit jsonl format.
- Do NOT re-run the full bulk OCR; the orchestrator handles refire after PR merge.
- Do NOT touch the closeout brief (`docs/dispatch-briefs/2026-05-19-etymology-closeout-codex.md`); that's a separate end-of-run task.

---

## 5. Failure modes — what to surface, not silently work around

- If Policy Engine doesn't support deny-all + allowlist (only allow-listing): use allowlist for `read_file` only, document in commit.
- If `--policy` requires settings.json change rather than CLI flag: update `~/.gemini/settings.json` is NOT acceptable (user-owned file, machine-specific); the policy file MUST be repo-relative and passed via CLI flag.
- If the smoke test still produces `Error executing tool web_fetch`: STOP, the policy isn't working. Surface with full evidence and DO NOT proceed to commit.
- If `gemini --policy` rejects the file format: try alternative formats (yaml/json/toml) and surface what the engine actually accepts.

Surface real failures via the PR body's "Issues encountered" section — fabricating success makes the next orchestrator's life worse.

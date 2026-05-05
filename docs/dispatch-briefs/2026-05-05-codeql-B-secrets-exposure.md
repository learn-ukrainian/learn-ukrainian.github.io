# Gemini Dispatch Brief — CodeQL Batch B: stack-trace + clear-text exposure (7 errors)

**Risk class:** MEDIUM (errors, info-disclosure-class)
**Mode:** danger (worktree)
**Goal:** open a single PR fixing all 7 alerts. NOT auto-merged — human reviews.

---

## Worktree instructions (mandatory)

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b gemini-codeql-B-secrets-exposure .worktrees/dispatch/gemini/codeql-B origin/main
cd .worktrees/dispatch/gemini/codeql-B
```

---

## The alerts (7 total)

### `py/stack-trace-exposure` (3)

| # | File | Line |
|---|---|---|
| 154 | `scripts/api/comms_router.py` | 1423 |
| 153 | `scripts/api/comms_router.py` | 1310 |
| 152 | `scripts/api/gold_router.py` | 310 |

### `py/clear-text-storage-sensitive-data` (2)

| # | File | Line |
|---|---|---|
| 142 | `scripts/build/linear_pipeline.py` | 1582 |
| ?? | `scripts/generate_mdx/core.py` | (query GH for line) |

### `py/clear-text-logging-sensitive-data` (2)

| # | File | Line |
|---|---|---|
| ?? | `scripts/vocab/lexical_sandbox.py` | (query GH) |
| ?? | `scripts/validate/validate_vocab_yaml.py` | (query GH) |

Get fresh details:
```bash
gh api 'repos/:owner/:repo/code-scanning/alerts?state=open&per_page=100' --paginate \
  -q '.[] | select(.rule.id | test("stack-trace|clear-text")) | {number, rule: .rule.id, path: .most_recent_instance.location.path, line: .most_recent_instance.location.start_line, msg: .most_recent_instance.message.text}'
```

---

## Fix patterns

### `py/stack-trace-exposure`

CodeQL flags when a Python exception traceback is sent to an HTTP response (e.g. `return {"error": traceback.format_exc()}`, `raise HTTPException(detail=str(e))` with internal context).

**Right fix:**
1. Log the exception server-side (with full traceback): `logger.exception("comm send failed")` or `logger.error(..., exc_info=True)`.
2. Return a generic message to the client: `"internal error"` with a correlation ID for the user to reference.
3. Optionally include `error_id` (e.g. `uuid4().hex`) in both log and response so users can quote it when reporting.

DO NOT just remove the traceback without preserving server-side observability — silent failures are worse than info disclosure.

### `py/clear-text-storage-sensitive-data` and `py/clear-text-logging-sensitive-data`

CodeQL flags when something that looks like a credential / token / password / API key flows into:
- `open(...).write(...)` (storage)
- `logger.info/debug/print(...)` (logging)

**Right fix:**
1. **Don't store/log the secret.** If it's a token, log `token[:6] + "..."` or `"[REDACTED]"` instead.
2. **If storage is necessary** (e.g. session DB), encrypt at rest or move to a credentials manager. For our project — non-commercial, local-first — environment variables loaded at runtime are usually preferred over disk storage.
3. **For false positives** (e.g. variable named `password_field` that's actually the form input *name*, not a value): add `# nosec` with justification.

**For `scripts/build/linear_pipeline.py:1582`** in particular — read the surrounding code carefully. The build pipeline writes a lot of state files, and CodeQL may be misidentifying a benign field name. Confirm before silencing.

---

## Per-batch execution

1. **Read each affected file fully**, especially the surrounding 30 lines for each alert.
2. **Apply the right fix per pattern above.** Don't blanket-suppress.
3. **Run tests**:
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -m pytest tests/ -k 'comms_router or gold_router or linear_pipeline or generate_mdx or lexical_sandbox or validate_vocab_yaml' -x -q
   ```
4. **Run ruff** on modified files.
5. **Commit:**
   ```
   fix(security): resolve 7 CodeQL alerts — stack-trace + clear-text exposure (batch B)

   - 3 py/stack-trace-exposure alerts: server-side logging + generic client error
   - 2 py/clear-text-storage alerts: redacted/removed from disk writes
   - 2 py/clear-text-logging alerts: redacted/[REDACTED] in log statements

   Co-Authored-By: Gemini 3.1 Pro <noreply@google.com>
   ```
6. **Push:**
   ```bash
   git push -u origin gemini-codeql-B-secrets-exposure
   ```
7. **Open DRAFT PR** with per-alert disposition in body.
8. **Do NOT enable auto-merge.**

---

## Stop conditions

- If you can't tell whether a value is sensitive vs benign → STOP and document for human reviewer in PR description.
- If suppressing requires changing public API contract → STOP, propose alternative.

---

## Deliverable

Draft PR + per-alert reasoning. Same shape as Batch A.

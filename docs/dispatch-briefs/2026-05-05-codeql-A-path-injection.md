# Gemini Dispatch Brief — CodeQL Batch A: py/path-injection (11 errors)

**Issue tracker:** filed inline in PR description
**Risk class:** HIGH (errors, security-class)
**Mode:** danger (worktree)
**Goal:** open a single PR fixing all 11 `py/path-injection` alerts. NOT auto-merged — human reviews.

---

## Worktree instructions (mandatory)

Work in a git worktree. Do NOT create a feature branch in the main checkout.

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin main
git worktree add -b gemini-codeql-A-path-injection .worktrees/dispatch/gemini/codeql-A origin/main
cd .worktrees/dispatch/gemini/codeql-A
```

After PR merges, the user (or next session) cleans up:
```bash
git worktree remove .worktrees/dispatch/gemini/codeql-A
git branch -d gemini-codeql-A-path-injection
```

---

## The alerts (11 total)

| # | File | Line | Notes |
|---|---|---|---|
| 157 | `scripts/path_safety.py` | 23 | Likely false positive — this IS the path-safety helper; line 23 is `return base.resolve()` for empty `parts` |
| 131 | `scripts/research/research_quality.py` | 1042 | |
| 130 | `scripts/research/research_quality.py` | 1034 | |
| 129 | `scripts/research/research_quality.py` | 1002 | |
| 128 | `scripts/research/research_quality.py` | 998 | |
| 127 | `scripts/research/research_quality.py` | 885 | |
| 126 | `scripts/research/research_quality.py` | 200 | |
| 125 | `scripts/research/research_quality.py` | 196 | |
| 114 | `scripts/tools/image_review_server.py` | 232 | |
| 113 | `scripts/tools/image_review_server.py` | 227 | |
| 88 | `scripts/api/consultation_router.py` | 462 | "This path depends on a user-provided value" — twice in same expr |

Get fresh details:
```bash
gh api 'repos/:owner/:repo/code-scanning/alerts/{NUMBER}' -q '{path: .most_recent_instance.location.path, line: .most_recent_instance.location.start_line, msg: .most_recent_instance.message.text, html_url}'
```

---

## Fix patterns (pick the right one per alert)

CodeQL `py/path-injection` fires when a user-controlled string flows into a path operation (`open`, `Path`, `os.path.join`, `os.makedirs`, etc.) without validation that the result stays within an expected root.

**Three valid fixes, in priority order:**

1. **Use `scripts.path_safety.safe_join(base, *parts)`** — already in this repo, validates components and verifies the resolved target stays under `base`. Drop-in replacement for raw `os.path.join` / `Path / part`. Prefer this whenever the call is `base + user_input → file path`.

2. **Add an explicit allow-list / regex check before the path operation.** Example:
   ```python
   if not re.fullmatch(r"[a-z0-9_-]+", user_input):
       raise ValueError("invalid identifier")
   target = base / f"{user_input}.json"
   ```
   Use this when `safe_join` is overkill — e.g. the user input is already constrained to a known shape (slug, level, integer ID).

3. **Suppress with `# nosec ...` comment + justification** when the alert is a genuine false positive (e.g. the input is already validated upstream, or it's a constant). Always pair the suppression with a short comment explaining why. Don't suppress without justification.

**For `path_safety.py:23`** specifically: the line is `return base.resolve()` when `parts` is empty. `base` is typed as `Path` and is the trusted root, not user input. This is almost certainly a false positive — add a CodeQL suppression comment. Do NOT modify the function logic just to silence the scanner.

---

## Per-batch execution

1. **Read each affected file fully** before editing. Understand the surrounding pattern and what the user input represents.
2. **Apply fixes** per the priority above. Prefer `safe_join` where it fits.
3. **Run tests** for affected files (use ./.venv/bin/python from main checkout if worktree lacks it; #1685's fix uses sys.executable):
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -m pytest tests/ -k 'research_quality or image_review or consultation_router or path_safety' -x -q
   ```
4. **Run ruff** on each modified file:
   ```bash
   /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/path_safety.py scripts/research/research_quality.py scripts/tools/image_review_server.py scripts/api/consultation_router.py
   ```
5. **Commit** with conventional message:
   ```
   fix(security): resolve 11 py/path-injection CodeQL alerts (batch A)

   - scripts/path_safety.py:23 — false positive, suppressed with justification
   - scripts/research/research_quality.py — switched to safe_join (7 sites)
   - scripts/tools/image_review_server.py — added regex allow-list (2 sites)
   - scripts/api/consultation_router.py:462 — safe_join (1 site)

   Co-Authored-By: Gemini 3.1 Pro <noreply@google.com>
   ```
6. **Push:**
   ```bash
   git push -u origin gemini-codeql-A-path-injection
   ```
7. **Open DRAFT PR** (human reviews — security-class):
   ```bash
   gh pr create --draft --title "fix(security): resolve 11 py/path-injection CodeQL alerts (batch A)" --body "$(cat <<'EOF'
   ## Summary
   Fixes all 11 open `py/path-injection` CodeQL alerts. Each alert addressed individually — see commit body and per-file comments.

   ## Per-alert disposition
   <FILL IN: per-alert what changed and which fix pattern was applied>

   ## Test plan
   - [x] Affected pytest selectors pass
   - [x] ruff check clean
   - [ ] Human security review (DRAFT — do not auto-merge)
   - [ ] CI green
   - [ ] CodeQL scan re-runs and confirms alerts closed

   🤖 Dispatched by Claude (Opus 4.7) on 2026-05-05 via delegate.py — security-class, draft for human review.
   EOF
   )"
   ```
8. **Do NOT enable auto-merge.** This is security-class; user reviews each fix.

---

## Stop conditions

- If a fix would break public API or change observable behavior beyond path validation → STOP, document in PR description, leave alert open with explanation.
- If `safe_join` doesn't fit and you're unsure between regex allow-list vs suppression → suppress with a clear `# nosec` justification, flag in PR for reviewer.
- If you find ADDITIONAL alerts not in this list (CodeQL was retriggered) → handle them in this same PR if same class, otherwise STOP.
- If pre-commit hook fails for reasons unrelated to your changes → fix the unrelated issue too (Boy Scout) but document it in the PR description.

---

## What to deliver

A draft PR with:
- All 11 alerts addressed (fixed or justified suppression)
- Per-alert reasoning in PR description
- Tests + ruff green
- No auto-merge enabled

Report back via the bridge / GH PR — I'll review and merge after the user's morning review.

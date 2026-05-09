# Codex CLI — Add `codex-desktop` as first-class agent identity in bridge (MVP)

## TL;DR

Per `audit/codex-desktop-comms-research-2026-05-09/REPORT.html` (now on `main`), the orchestrator currently has no real-time channel comms with Codex Desktop — only async via GH PRs/comments (hours-latency). Multi-UI ADR is the canonical full design but gated on bakeoff + signoff.

This brief lands the **MVP unblock**: `codex-desktop` recognised as a valid agent identity throughout the bridge, so we can immediately do:
```
ab post desktop-tasks "<brief>" --to codex-desktop --from-agent claude
ab channel tail desktop-tasks --follow    # codex desktop subscribes
ab inbox show codex-desktop                # codex desktop pulls
```

**No schema change.** Just teach the bridge that `codex-desktop` is a real identity. Multi-UI ADR's 4-tuple identity (`agent_family`, `ui_surface`, `client_id`, `instance_id`) stays out of scope until the ADR ACCEPTS.

Estimated diff: **30–80 LOC**.

---

## Mandatory orientation (#M-4)

1. **`docs/best-practices/deterministic-over-hallucination.md`** — every claim tool-backed.
2. **`audit/codex-desktop-comms-research-2026-05-09/REPORT.html`** — full context. Reachable at `localhost:8765/artifacts/audit/codex-desktop-comms-research-2026-05-09/REPORT.html`.
3. **`docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md`** — Multi-UI ADR. Read enough to confirm: this MVP is intentionally a SUBSET that doesn't preclude the full ADR landing later.
4. **The constraint sites:**
   - `scripts/ai_agent_bridge/_channels.py:73-75` — `VALID_AGENTS` tuples (the hardcoded constraint)
   - `scripts/agent_runtime/registry.py:37` — `AGENTS` dict
   - `scripts/ai_agent_bridge/__main__.py` post argparse — `--from-agent` `choices=` list

## Verifiable claims this work will produce + the tool

| Claim | Tool | Evidence format |
|---|---|---|
| "Bridge accepts `codex-desktop` as `--from-agent`" | `ab post test "msg" --from-agent codex-desktop` (against a test channel) | Quoted output |
| "Bridge accepts `--to codex-desktop` for routing" | `ab post test "msg" --to codex-desktop --from-agent claude` | Quoted output |
| "`ab inbox show codex-desktop` works" | `ab inbox show codex-desktop` | Quoted output |
| "Registry has `codex-desktop` entry" | `grep -A8 '"codex-desktop"' scripts/agent_runtime/registry.py` | Quoted output |
| "Existing claude/codex/gemini paths still work" | Run a pre-existing test that uses `--from-agent codex` | Quoted pytest output |
| "New tests pass" | `.venv/bin/pytest tests/test_ab_post.py tests/test_channels.py` (or appropriate) | Quoted output |
| "Ruff clean" | `.venv/bin/ruff check scripts/ai_agent_bridge/_channels.py scripts/ai_agent_bridge/__main__.py scripts/agent_runtime/registry.py tests/` | Quoted output |

---

## Worktree instructions (mandatory)

Dispatcher creates `.worktrees/dispatch/codex/codex-desktop-comms-mvp/`. All work there. Branch: `codex/codex-desktop-comms-mvp`. Base: `origin/main`.

---

## Workflow (numbered)

1. **Worktree setup** verified.
2. **Read** the research report + the constraint sites listed above.
3. **Implement:**
   - **`scripts/ai_agent_bridge/_channels.py:73-75`** — extend `VALID_AGENTS` to include `"codex-desktop"`. Decide whether to ALSO add `claude-desktop` for symmetry (recommended: yes, even though no immediate use — it's a 1-char addition and avoids the same issue when Claude Desktop comes online). `VALID_POST_AGENTS` and `VALID_RECIPIENT_AGENTS` should pick up the new entries automatically since they derive from `VALID_AGENTS`.
   - **`scripts/agent_runtime/registry.py`** — add `codex-desktop` (and `claude-desktop` if symmetric):
     ```python
     "codex-desktop": {
         "adapter": "scripts.agent_runtime.adapters.codex:CodexAdapter",  # reuse, or stub if no headless invocation
         "default_model": "gpt-5.5",
         "cost_tier": "high",  # human-driven, not subprocess
         "capabilities": frozenset({
             "frontend_design", "ui_review", "multimodal", "visual_inspection",
         }),
         "cli_available": False,  # NOT subprocess-spawnable from this orchestrator
         "resume_policy": "never",
     },
     ```
     Important: `cli_available: False` — this prevents `delegate.py dispatch --agent codex-desktop` from accidentally trying to spawn it as a subprocess. Codex Desktop is human-invoked.
   - **`scripts/ai_agent_bridge/__main__.py`** — wherever `argparse` defines `--from-agent choices=`, add `codex-desktop` (and `claude-desktop` if symmetric).
   - **Optional / consider:** if there's a `discuss --with` choices list, add the new agents there too — but mark `cli_available: False` agents as non-spawnable in the discuss runner so it errors clearly instead of silently failing.
4. **Documentation:**
   - **`docs/best-practices/agent-bridge.md`** — add a "Desktop participation (MVP)" section documenting:
     - How orchestrator dispatches: `ab post desktop-tasks "<brief>" --to codex-desktop --from-agent claude`
     - How Codex Desktop subscribes: `ab channel tail desktop-tasks --follow` (running in the Desktop session)
     - How Codex Desktop pulls inbox: `ab inbox show codex-desktop`
     - How Codex Desktop posts replies: `ab post desktop-tasks "<status>" --from-agent codex-desktop`
     - Limitation: this is a flat-string identity; full Multi-UI ADR (4-tuple identity, claims, SSE, attachments) is the future.
5. **Tests** — add to `tests/test_channels.py` or wherever VALID_AGENTS is tested:
   - Test that `--from-agent codex-desktop` is accepted.
   - Test that `--to codex-desktop` routes correctly.
   - Test that pre-existing `claude`/`codex`/`gemini`/`user` paths still work.
6. **Lint** — `.venv/bin/ruff check` on changed files.
7. **Commit** — conventional message:
   ```
   feat(bridge): add codex-desktop + claude-desktop as first-class agent identities (MVP)

   Closes the gap from audit/codex-desktop-comms-research-2026-05-09/REPORT.html
   §"What I'm executing next." Drops orchestrator ↔ Codex Desktop round-trip
   from "hours via GitHub" to "seconds via channel" — without waiting for the
   full Multi-UI ADR (docs/decisions/pending/2026-05-06-multi-ui-channel-participation.md)
   to ACCEPT.

   - VALID_AGENTS extended in scripts/ai_agent_bridge/_channels.py
   - Registry entries added in scripts/agent_runtime/registry.py with
     cli_available=False (human-invoked, not subprocess-spawnable)
   - argparse --from-agent choices extended in __main__.py
   - Documentation: docs/best-practices/agent-bridge.md "Desktop participation (MVP)"
   - Test coverage for new identities + regression for existing paths

   This is a flat-string identity MVP. Full 4-tuple identity (agent_family,
   ui_surface, client_id, instance_id) per Multi-UI ADR Q1 stays out of scope.

   Refs Multi-UI ADR. Unblocks orchestrator → Codex Desktop comms today.

   Co-Authored-By: Codex (gpt-5.5) <noreply@anthropic.com>
   ```
8. **Push** — `git push -u origin codex/codex-desktop-comms-mvp`.
9. **PR** — `gh pr create` with body referencing the research report + every AC quoted-evidence-backed per #M-4.
10. **NO auto-merge.** Stop. Orchestrator reviews.

---

## What "done" looks like

- `ab post test-channel "hello" --from-agent codex-desktop` works without error.
- `ab post test-channel "hi" --to codex-desktop --from-agent claude` works.
- `ab inbox show codex-desktop` works.
- All ACs ticked with quoted evidence in PR body.
- Pre-commit clean.
- PR opened, **NOT merged**.

## Escalation

If `VALID_AGENTS` or the registry has a downstream constraint you discover (e.g., a hook or a downstream consumer that switches on `agent_family`), document it in the PR body + handle it (extend the constraint OR document why a follow-up issue is needed). Don't silently break behavior.

If the symmetric `claude-desktop` addition introduces test failures, drop it and stick to `codex-desktop` only — file a follow-up issue for `claude-desktop` separately.

# How We Work (Mandatory Workflow)

<critical>

Every task follows this workflow. No exceptions for non-trivial changes.

1. **Create GH issue** — describe the problem, draft a plan
2. **Adversarial review of plan** — send to Gemini, incorporate feedback
3. **Finalize ACs** — update issue with concrete acceptance criteria
4. **Implement** — work through ACs one by one
5. **Verify all ACs** — every AC checked and documented on the issue
6. **Adversarial review of implementation** — send code to Gemini, fix findings
7. **Close** — only when all ACs pass and review is clean

**Skip plan review** (step 2) only for trivial changes (< 50 lines, config/typo fixes).

**Adversarial review command** (steps 2 & 6). Always use `--model gemini-3.1-pro-preview`. Document findings on the GH issue.
```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Adversarial review for #NNN. Read {path}." \
  --task-id issue-NNN --model gemini-3.1-pro-preview
```

## Channel bridge (#1190, shipped 2026-04-12)

The agent bridge now supports **topic-scoped channels** — preferred
for sustained multi-turn conversations because they eliminate the
need to re-paste project context on every round.

**Five seeded channels**: `shared`, `pipeline`, `content`,
`architecture`, `reviews`. Every post auto-prepends:
1. The channel's pinned `context.md` (via the include chain, so
   `shared` is merged into everything)
2. A Monitor API snapshot of volatile project state
3. Recent channel history, character-budget truncated

**Preferred for:** code reviews (multi-round), design debates,
cross-agent discussions, anything that needs pinned context.
**Not preferred for:** one-off drive-by questions — use `ask-*` for
those.

**Quick reference**:
```bash
# List / inspect
ab channel list
ab channel info pipeline
ab channel tail reviews -n 20
ab channel tail reviews --thread THREAD_ID

# Post (short form — single recipient)
ab p reviews gemini "quick question about module X"

# Post (long form — multi-recipient, threading, parent/corr ids)
ab post reviews "Review of #NNN" --to gemini,codex --parent MSG_ID

# Multi-agent bounded discussion
ab discuss architecture "Should we extract the V6 god object?" \
    --with claude,gemini,codex --max-rounds 2
```

`ab discuss` runs rounds in parallel via ThreadPoolExecutor,
short-circuits when all agents end their response with `[AGREE]`,
and caps at 4 rounds. Default: 2 rounds, 1 agent. The transcript
lands in `channel_messages` with proper `parent_id` threading so
you can tail it later with `ab channel tail --thread`.

**Web dashboard**: `http://localhost:8765/channels.html` (localhost
only, read + post).

**Full docs**: `docs/best-practices/agent-bridge.md`.

The legacy `ask-gemini` / `ask-claude` / `ask-codex` commands are
NOT deprecated — they stay alive for one-shot delegations. Use
channels for anything that will have >1 turn.

**Why**: GH issues are persistent memory. Without them, context is lost between sessions and work gets repeated or silently broken.

**Issue discipline (coding issues)**:
- **Never leave half-done.** If you open it, finish it. If you can't finish it now, document exactly where you stopped and what remains.
- **Never close unless ALL acceptance criteria are verified.** Partial completion = still open.
- **Aim to fully resolve and close.** Open issues are debt. Minimize them aggressively.
- **The human manages content generation issues.** Claude owns coding/infrastructure issues. But proactively remind when it's time to start building a new track or batch — initiative is welcome.

**Proactive issue hygiene**: At the start of each session, check open coding issues. Prioritize, resolve, close — don't let them go stale.

</critical>

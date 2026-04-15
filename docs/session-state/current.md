# Session handoff — 2026-04-15 (Claude→Codex)

Claude is at usage limit. Codex takes over A1 build coordination.

## HEAD: `4bfb847ab` on main

## What was shipped this session (do not re-do)

19 commits landed. Key ones:

| Commit | What |
|---|---|
| `4bfb847ab` | **#1260 CRITICAL**: AC3 now in chunked writer path; no-dialogue conditional for phonetics modules; pacing plan conditional; INJECT_ACTIVITY standardized |
| `b77caa507` | **#1260 MAJOR-5/6**: Reviewer Dimension 5 scoped to marker-only; activity_obligations order+type check |
| `4da2b1d73` | **#1260 MAJOR-7**: Plan-patch prompt states 4 allowed roots explicitly |
| `51c0df7bd` | **#1230 AC1**: Plan-hash invalidation + stale detection + --resume stale awareness |
| `b020a86d1` | **#1230 AC2**: Plan contradiction validator (pre-build gate) |
| `de24cb3b5` | **#1230 AC3**: Writer prompt: plan > skeleton precedence |
| `32fae4838` | **#1230 AC4**: Integration tests for plan drift |
| `f10a7d8ab` | **#1234**: Gemini 429 → auto cascade in bridge |
| `accbb4b3f` | **#1239**: Bridge preflight warnings + deadline whitelist |
| `a3fd7c845` | **#1236**: `ab post --model` and `ab inbox run --deadline` flags |
| `591365c84` | **#1260 precursor**: No-dialogue dimension override in reviewer |
| `46a47e7f6` | Fix: INJECT_ACTIVITY contract validation + plan patch output capture |
| `2a49935ed` | Fix: plan_contract makes dialogue_situations optional |
| `f8b972e57` | Fix: plateau test mock (#1259) |

---

## Current primary task: Fix all 17 failing A1 modules

### Status from Monitor API
```bash
curl -s "http://localhost:8765/api/state/failing?track=a1"
```

As of handoff:
- **15 modules with `needs_human_review: true`** — `--resume` SKIPS these. Need fresh builds.
- **1 stale module** (M18 `i-want-i-can`) — `--resume` works.
- **M2 `reading-ukrainian`** — was building at R4 when Claude handed off. Check status first.

### Commands to run

Check M2 status first:
```bash
curl -s "http://localhost:8765/api/state/build-status/a1" | python3 -m json.tool | grep -A3 "reading-ukrainian"
```

Then run the failing modules. Split across two terminals for speed:

```bash
# Terminal 1
for N in 7 8 9 10 11 12 19; do
  .venv/bin/python scripts/build/v6_build.py a1 $N \
    --writer gemini-tools --reviewer codex-tools
done

# Terminal 2
for N in 21 32 38 43 46 52 54 55; do
  .venv/bin/python scripts/build/v6_build.py a1 $N \
    --writer gemini-tools --reviewer codex-tools
done

# M18 separately (stale, resume ok)
.venv/bin/python scripts/build/v6_build.py a1 18 --resume \
  --writer gemini-tools --reviewer codex-tools

# M2 — only if R4 didn't ship:
.venv/bin/python scripts/build/v6_build.py a1 2 \
  --writer gemini-tools --reviewer codex-tools
```

### What to watch for per module

**Healthy run:**
- R1 score ≥ 8.5
- Scores go UP each round (never down)
- No `<!-- INJECT_ACTIVITY: syllable-sort -->` or off-contract types
- No invented dialogue in phonetics modules (M2, M3, M6)

**Intervention needed if:**
- Score drops round-over-round (e.g. R1: 8.8 → R2: 8.0) → read the review + fix blocks, look for wrong INJECT_ACTIVITY types or reviewer hallucinating dialogue in phonetics module
- `needs_human_review` set after plateau → read `orchestration/{slug}/needs-human-review.yaml` for root cause
- `plan patch failed: no parseable payload` → check `v6-plan-patch-output.md`; if empty/noise, the capture bug may have recurred

**If a new pattern of failure emerges across ≥3 modules**: stop the batch, diagnose root cause (read review files + plan_patch output), fix the pipeline, then resume.

---

## How to coordinate with Gemini

The agent bridge handles all inter-agent communication. Use it — do NOT call `gemini` CLI directly.

### Quick one-shot questions
```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Your question here" \
  --task-id task-id-here \
  --model gemini-3.1-pro-preview
```

Result lands in `batch_state/tasks/{task-id}.result`. Also readable via:
```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py read {MSG_ID}
```

### Channel-based sustained conversation (preferred for multi-turn)

Five channels: `shared`, `pipeline`, `content`, `architecture`, `reviews`.

```bash
# Post to a channel
ab post reviews "Your message here" --to gemini

# Post with specific model and extended deadline
ab post reviews "Long review task" --to gemini --model gemini-3.1-pro-preview --deadline 1800

# Read recent channel history
ab channel tail reviews -n 20

# Watch for Gemini's reply live
ab channel tail reviews --follow

# Multi-agent discussion (bounded rounds)
ab discuss pipeline "Should we change X?" --with gemini,codex --max-rounds 2
```

### When to ask Gemini vs decide yourself

**Ask Gemini:**
- Content/pedagogy decisions: "Is this dialogue situation appropriate for A1 learners?"
- Ukrainian linguistics: "Is this VESUM form correct?"
- Review of module content: "Review this module for naturalness"
- Architecture trade-offs you're uncertain about

**Decide yourself:**
- Pipeline code bugs (you're the code agent)
- Test failures (read the failing test, fix it)
- Codex dispatch for coding tasks (you can self-dispatch via `scripts/delegate.py`)

### Gemini review of code changes (mandatory for non-trivial commits)

After any non-trivial commit, send Gemini an adversarial review:
```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Adversarial code review of recent commit. Read git diff HEAD~1..HEAD and check for: correctness, edge cases, test coverage gaps, prompt injection risks. Report findings." \
  --task-id review-$(git rev-parse --short HEAD) \
  --model gemini-3.1-pro-preview
```

---

## Key infrastructure

| What | Where |
|---|---|
| Build pipeline | `.venv/bin/python scripts/build/v6_build.py {level} {num} [--step {step}] [--resume]` |
| Monitor API | `curl -s http://localhost:8765/api/state/track-health/a1` |
| Failing modules | `curl -s http://localhost:8765/api/state/failing?track=a1` |
| Plan files | `curriculum/l2-uk-en/plans/a1/{slug}.yaml` |
| Orchestration artifacts | `curriculum/l2-uk-en/a1/orchestration/{slug}/` |
| Delegate (dispatch Codex/Gemini) | `.venv/bin/python scripts/delegate.py dispatch --agent codex ...` |
| Agent bridge | `.venv/bin/python scripts/ai_agent_bridge/__main__.py` or `ab` alias |

**Always use `.venv/bin/python`, never bare `python3`.**

## Pending minor work (low priority, don't block on these)

- `.bak` file collision on second plan patch (Gemini minor finding from session)
- `insert_after` punctuation spacing (punctuation at start of payload gets rogue space)
- `#1241` A1 regeneration wave tracking issue — update when all 17 modules ship

## Non-negotiable rules (don't skip)

1. `ruff check` after every file edit
2. `pytest` on affected tests after every logical phase
3. Gemini adversarial review after every non-trivial commit
4. Close GH issues only when ALL acceptance criteria verified
5. Word targets are MINIMUMS — never lower the target, expand content
6. Never edit `.claude/` or `.agent/` directly — edit `claude_extensions/` + `npm run claude:deploy`
7. All work on `main`. Use `git worktree` for isolation.

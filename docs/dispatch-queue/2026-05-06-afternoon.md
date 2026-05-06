# Dispatch queue — 2026-05-06 afternoon (14:00-20:00 CET peak window)

**Purpose:** Claude (Opus) goes minimal during peak. Codex + Gemini grind through this stack. Each row is a copy-paste dispatch command.

**Cap discipline:** max 2 Codex concurrent (`git worktree list | grep dispatch/codex | wc -l`). Gemini effectively uncapped (subscription).

**Fire order:** P0 = blocks other work, P1 = high-value standalone, P2 = nice-to-have. Within a tier, top-down.

---

## In flight at queue creation (do not re-fire)

| Task ID | Agent | What | PR/Issue |
|---|---|---|---|
| `1736-comms-fix` | Codex | comms.html crash + broker DB indexes/retention/WAL + main-page nav | #1736 |
| `1731-adr-r3` | Codex | ADR round 3 — Codex's 6 self-review findings | #1735 |

The ADR round 3 dispatch fires from this turn's manifest creation; see fire commands below.

---

## P0 — Codex queue

Each command generates `--prompt-file` from the GitHub issue body. Copy-paste verbatim.

### 1. ADR round 3 — Codex self-review findings (FIRES NOW)

```bash
.venv/bin/python scripts/delegate.py dispatch --agent codex \
  --task-id 1731-adr-r3 --mode danger --worktree \
  --base codex/1731-adr-r2 \
  --prompt-file /tmp/codex-1731-adr-r3-brief.md
```

Brief at `/tmp/codex-1731-adr-r3-brief.md` lists Codex's own 6 REVISE findings (Q1↔Q7 contradiction, Q12 dedup-bug, instance_id concurrency regression, audio underspec, bakeoff anchor rubric gaps, capability profile audio cells).

### 2. `ab review-deep` + `ab dispatch-fix` wrapper commands (model enforcement)

```bash
.venv/bin/python scripts/delegate.py dispatch --agent codex \
  --task-id ab-review-deep-wrapper --mode danger --worktree \
  --base origin/main \
  --prompt-file /tmp/codex-ab-review-deep-brief.md
```

Brief: add `ab review-deep <PR-or-file>` subcommand to `scripts/ai_agent_bridge/__main__.py` that ALWAYS runs `delegate.py dispatch --agent claude --mode read-only --model claude-opus-4-7 --effort xhigh`. Add `ab dispatch-fix <issue>` that ALWAYS runs Codex via worktree. Tooling-enforced model assignment per `claude_extensions/rules/model-assignment.md`.

### 3. #1708 — v7_build.py per-writer subprocess timeout

Issue has the AC. Codex writes a bounded-subprocess wrapper around the writer-phase invocation. Worktree: `codex/1708-writer-subprocess-timeout`.

```bash
gh issue view 1708 --json body --jq .body > /tmp/brief-1708.md
.venv/bin/python scripts/delegate.py dispatch --agent codex \
  --task-id 1708-writer-subprocess-timeout --mode danger --worktree \
  --base origin/main --prompt-file /tmp/brief-1708.md
```

### 4. #1710 — Gemini auth-mode priority flip (API first, OAuth fallback)

Small fix in `scripts/agent_runtime/adapters/gemini.py`. Issue has the AC.

```bash
gh issue view 1710 --json body --jq .body > /tmp/brief-1710.md
.venv/bin/python scripts/delegate.py dispatch --agent codex \
  --task-id 1710-gemini-auth-priority --mode danger --worktree \
  --base origin/main --prompt-file /tmp/brief-1710.md
```

### 5. #1707 — v7_build resume terminal-event check

Resume logic should look for `module_done` JSONL event, not file size.

```bash
gh issue view 1707 --json body --jq .body > /tmp/brief-1707.md
.venv/bin/python scripts/delegate.py dispatch --agent codex \
  --task-id 1707-resume-terminal-event --mode danger --worktree \
  --base origin/main --prompt-file /tmp/brief-1707.md
```

---

## P1 — Codex queue (security + bugs)

### 6. #1701 — agent_runtime os.environ scrub (security)

Spawned child CLIs receive full `os.environ` including secrets. Whitelist allowed env vars.

```bash
gh issue view 1701 --json body --jq .body > /tmp/brief-1701.md
.venv/bin/python scripts/delegate.py dispatch --agent codex \
  --task-id 1701-os-env-scrub --mode danger --worktree \
  --base origin/main --prompt-file /tmp/brief-1701.md
```

### 7. #1702 — ab discuss/post agents have FS write access (security)

Sandbox the agent subprocess writes to `.worktrees/` only.

```bash
gh issue view 1702 --json body --jq .body > /tmp/brief-1702.md
.venv/bin/python scripts/delegate.py dispatch --agent codex \
  --task-id 1702-ab-fs-sandbox --mode danger --worktree \
  --base origin/main --prompt-file /tmp/brief-1702.md
```

### 8. #1570 / #1571 / #1573 — wiki ingestion bugs (kept from cleanup pass)

Three related bugs. Single dispatch can fix all three since they touch the same script.

```bash
cat <<'EOF' > /tmp/brief-wiki-ingest.md
Investigate and fix #1570, #1571, #1573 in scripts/ingest_ukrainian_wiki.py:
- #1570: silent no-op when invoked with top-level wiki/ path
- #1571: cross-track slug collisions silently drop articles
- #1573: bulk-dir path bypasses citation_audit gate

Read all three issues. Reproduce each. Fix in one PR with three commits (one per bug). Tests + ruff + commit + push + gh pr create. Worktree: codex/wiki-ingest-3-bugs.
EOF
.venv/bin/python scripts/delegate.py dispatch --agent codex \
  --task-id wiki-ingest-3-bugs --mode danger --worktree \
  --base origin/main --prompt-file /tmp/brief-wiki-ingest.md
```

### 9. Strand 0 bakeoff framework (post-Codex-Desktop-discussion)

3-way discussion converged on **Option B**: Codex CLI writes text first, Codex Desktop adds visual aids on top of the CLI's output. File a new issue first, then dispatch.

```bash
# Step 1: create issue (Claude does this when back online)
# Step 2: dispatch the framework code
.venv/bin/python scripts/delegate.py dispatch --agent codex \
  --task-id strand0-bakeoff-framework --mode danger --worktree \
  --base origin/main --prompt-file /tmp/brief-strand0.md
```

Framework needs: (a) Ohoiko PNG ingestion as input attachment, (b) 7-anchor scoring rubric script (Python), (c) blob-store stub at `content/blobs/`, (d) MDX `<ParadigmTable>` and `<RegisterPhoto>` placeholder components. Codex CLI run already produces text; the framework is what wraps it for Desktop's visual-aid pass.

Brief lives at `/tmp/brief-strand0.md` once Strand 0 issue filed.

---

## P0 — Gemini queue (uncapped)

### G1. #1663 — Antonenko-Davydovych «Як ми говоримо» full text ingest

Pre-Soviet style guide, ~169 pages. Ingest into `data/sources.db` FTS5 with chunking.

```bash
gh issue view 1663 --json body --jq .body > /tmp/brief-1663.md
.venv/bin/python scripts/delegate.py dispatch --agent gemini \
  --task-id 1663-antonenko-ingest --mode danger --worktree \
  --base origin/main --prompt-file /tmp/brief-1663.md
```

### G2. #1664 — Karavansky «Російсько-український словник складної лексики» (r2u)

Bilingual lexicon for translation lookups.

```bash
gh issue view 1664 --json body --jq .body > /tmp/brief-1664.md
.venv/bin/python scripts/delegate.py dispatch --agent gemini \
  --task-id 1664-karavansky-r2u --mode danger --worktree \
  --base origin/main --prompt-file /tmp/brief-1664.md
```

### G3. #1665 — Holovashchuk «Словник-довідник з українського літературного слововживання»

Modern usage reference.

```bash
gh issue view 1665 --json body --jq .body > /tmp/brief-1665.md
.venv/bin/python scripts/delegate.py dispatch --agent gemini \
  --task-id 1665-holovashchuk-ingest --mode danger --worktree \
  --base origin/main --prompt-file /tmp/brief-1665.md
```

### G4. #1666 — Гринчишин/Сербенська «Словник паронімів української мови» (1986)

Paronym lookup — critical for V7 reviewer's paronym gate.

```bash
gh issue view 1666 --json body --jq .body > /tmp/brief-1666.md
.venv/bin/python scripts/delegate.py dispatch --agent gemini \
  --task-id 1666-paronyms-ingest --mode danger --worktree \
  --base origin/main --prompt-file /tmp/brief-1666.md
```

---

## How the user fires the queue

After `bb43xs79l` (comms-fix) and `1731-adr-r3` finish, slot in row 2 (review-deep wrapper). After that finishes, slot in row 3, etc. Roughly:

```bash
# Watch active dispatches
git worktree list | grep dispatch/codex | wc -l   # if < 2, fire next P0/P1 row
```

For Gemini: fire all 4 ingestion tasks in parallel (no cap concern in practice).

---

## Notes

- Each dispatch lands its own PR. CI runs automatically. Squash-merge each green PR.
- If a CI fail recurs across multiple dispatches, that's a sign of an underlying infra issue — surface in the channel before re-firing.
- The Strand 0 bakeoff framework is best fired AFTER user manually runs the first Codex Desktop trial (just so we know what infra is actually missing).
- Round-3 ADR (`1731-adr-r3`) bases off `codex/1731-adr-r2` (PR #1735's branch tip) — its commits land on a NEW branch `codex/1731-adr-r3` and open a fresh PR superseding #1735.

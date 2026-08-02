# Entire-context handoff dual-write (Option A)

**Status:** operator GO 2026-08-02 · **Authority:** file handoff remains SSOT  
**Skill (git SSOT):** `agents_extensions/shared/skills/drive-epic/SKILL.md` §8  
**Not durable:** `.claude/skills/**` deploy copies (rsync overwrite on agents deploy)

## Purpose

Epic drivers dual-write **public continuity** into entire-context while keeping the
local operational handoff file as seat SSOT. Entire does **not** replace GitHub,
fleet-comms, or file handoffs (ADR-018).

## Durable sinks

| Sink | Content |
| --- | --- |
| File handoff (local gitignored operational) | Residual narrative, next queue |
| `python -m scripts.entire_context` projection | `bootstrap-git`, `handoff` capsule (stdout), `record-use` |
| Fleet-comms channel | Issue/PR numbers only |
| GitHub issues | Product residual / next work |

Do **not** tee capsules into `.claude/` as process storage. Optional scratch only under
`batch_state/` (runtime, gitignored).

## Commands (end of session)

```bash
.venv/bin/python -m scripts.entire_context bootstrap-git <40-hex-sha>   # per merge
.venv/bin/python -m scripts.entire_context handoff --query "<epic keywords>"
.venv/bin/python -m scripts.entire_context record-use \
  --task-id <epic-or-stream-id> --consumer <harness> --purpose handoff \
  --locator-id clink_…
.venv/bin/python -m scripts.fleet_comms channel publish <stream-channel> \
  "handoff dual-write: … Next issues #… Merged PRs #…" \
  --sender "$SESSION_HANDOFF_AGENT" --source <harness> --kind state \
  --idempotency-key "handoff-<epic>-<date>"
```

## Cold start

```bash
.venv/bin/python -m scripts.entire_context status
.venv/bin/python -m scripts.entire_context search --query "<epic keywords>"
```

Empty search = nothing indexed for that needle — fall through to GH + file handoff.

**Needle rules (tool-proved):** ranking treats the query as **one substring**, not
tokenized English. Prefer path fragments / SHAs (`practice`, `generate_practice`,
full 40-hex). Multi-word phrases like `practice membership` often score 0.

- `search --query "practice"` → hits when paths contain `practice`
- `handoff --query "practice"` → capsule when ≥1 scored hit
- `handoff --query "practice membership"` → can return `{"error":"seed_invalid"}`
  when the full phrase matches nothing — then pass `--locator-id clink_…` from
  `bootstrap-git` / `search` instead

## Atlas snapshot (2026-08-02, tool-backed)

Merged: #6267 · #6265 · #6270. Closed: #6135 · #6259 · #6269.  
Measure after hydrate: missing_curated_keys=0, missing_practice_indexes=0, B=5093.  
Next: #6188 · #6137–#6139 · #6143.

X-Agent: grok/handoff-entire-dualwrite

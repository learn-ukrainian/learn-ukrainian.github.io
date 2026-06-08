# Current Session Restart Handoff

Generated-At: 2026-06-08 (Claude orchestrator, user-requested handoff at ~500K)

## Latest Brief

Claude orchestrator session. Shipped this session (all merged to origin/main):
Dependabot sweep; security helper `safe_env.sh` (#1896 closed); agy lane hardening
PR #2839 (#2739+#2362 closed); **agy `--to-model` fix** (pro now selectable, ported
from kubedojo); agy routing flipped to default (wiki/factual held); **autocompact
DISABLED** + brain-rot canary (`scripts/context_canary.py`) + 500/700 graduated
handoff policy; **main-page color de-Sovietization** (flag azure/yellow, navy+goldenrod
retired — needs manual Pages deploy); **#2823 lightweight-UI takeover** (audit + matrix
+ 6-slice plan posted to the issue — foundation only, nothing built to POC fidelity, NO
UI design review yet).

**Full detail:** `docs/session-state/2026-06-08-claude-agy-context-policy-2823-takeover.md`

## Top next actions
1. **#2823 epic**: drive slice 1 (de-Starlight cleanup) → slices 2-6. Slice 6 = the visual
   design review the user asked for ("do pages look nice/best-practice?" → currently NO/UNVERIFIED).
   Architecture is decided (Astro-without-Starlight, already in place). Plan in issue #2823.
2. **Agy wiki-lane flip** (unblocked): rigorous §7 re-test on agy pro + obscure bio + COMPLETE
   reference (this session's probe was corpus-limited); if clean, add `agy` to
   `scripts/wiki/compiler.py` WRITER_CHOICES + flip MEMORY L73/L112.
3. **Trigger manual Pages deploy** (`deploy-pages.yml`) to push the color fix live.

## Context policy (autocompact OFF)
Handoff is the ONLY guard. ~500K this phase, ~700K next. Monitor rot with
`scripts/context_canary.py` (mint immutable anchors at low context, score from memory at
checkpoints; drift → hand off). Log: `batch_state/canary/canary_log.csv`.

## Hands-off (parallel agents)
Session-handoff protocol; #2832 ledger; #2824 M8 MDX.

## Git
- Root branch: `main` | origin/main HEAD: `e4bf1398ee` (fix(ui): de-Sovietize main hero)

## Restart commands
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin -q && git log origin/main --oneline -8
curl -sS http://127.0.0.1:8765/api/orient
gh issue view 2823 --comments
cat docs/session-state/2026-06-08-claude-agy-context-policy-2823-takeover.md
.venv/bin/python scripts/context_canary.py --help
```

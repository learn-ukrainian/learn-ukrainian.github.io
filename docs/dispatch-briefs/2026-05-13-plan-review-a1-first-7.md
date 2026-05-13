# Dispatch Brief — Plan review for first 7 A1 modules

> **Status:** PENDING DISPATCH. Target agent: claude-headless (xhigh, Opus 4.7).
> Purpose: produce per-module audit reports for sequences 1-7 of A1 so the orchestrator can decide LOCKED transitions before the overnight build queue starts.
> Read-only on plan YAMLs (skill writes audit reports only; does NOT modify plans).

## Mission

Run the `plan-review` skill on A1 sequences 1-7 (slugs: `sounds-letters-and-hello`, `reading-ukrainian`, `special-signs`, `stress-and-melody`, `who-am-i`, `my-family`, `checkpoint-first-contact`).

Skill location: `.agent/skills/plan-review/SKILL.md` (project-local, auto-loaded). Invocation: `/plan-review a1 1-7`.

## Worktree setup

```bash
git worktree add -b claude/plan-review-a1-first-7-2026-05-13 \
  .worktrees/dispatch/claude/plan-review-a1-first-7-2026-05-13 \
  origin/main
cd .worktrees/dispatch/claude/plan-review-a1-first-7-2026-05-13
```

## Steps

1. **Invoke the skill.** Read `.agent/skills/plan-review/SKILL.md` for the full prompt + checks. Read the mandatory pre-step `docs/l2-uk-en/state-standard-2024-mapping.yaml` ONCE before any review. Then process sequences 1 through 7 individually.

2. **Per-module audit report.** Save each review to `curriculum/l2-uk-en/a1/audit/{slug}-plan-review.md`. Format per skill spec.

3. **Summary report.** After all 7, produce a roll-up summary at `curriculum/l2-uk-en/a1/audit/first-7-summary-2026-05-13.md`. Required sections:
   - PASS/FAIL count
   - CRITICAL + HIGH issues grouped by pattern (Russianism class, vocab-mismatch class, grammar-scope-mismatch class, factual-error class, etc.)
   - Suggested template fixes per cluster
   - **Per-module LOCK recommendation** — explicit one-line table: `slug | status | severity-summary | LOCK_NOW | NEEDS_FIX | NEEDS_REVISION`
   - **Cross-cutting** — patterns repeated across ≥3 plans

4. **Do NOT modify plan YAMLs.** Reports only. Plan-state transitions are the orchestrator's call after reading the summary.

## Skill notes

- effort: `xhigh` (Opus 4.7) — per CLAUDE.md xhigh routing for plan/content review.
- Uses RAG: `mcp__sources__verify_word`, `mcp__sources__search_text`, `mcp__sources__check_modern_form`, `mcp__sources__search_style_guide` (Russianism class).
- State Standard 2024 mapping file is the curriculum authority — read once, then reference per module.

## Verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| 7 per-module audit files exist | `ls curriculum/l2-uk-en/a1/audit/*-plan-review.md \| wc -l` | raw count line, ≥ 7 |
| Summary report exists with required sections | `grep -c '^## ' curriculum/l2-uk-en/a1/audit/first-7-summary-2026-05-13.md` | raw count, ≥ 4 (per the required-sections list) |
| LOCK-recommendation table present | `grep -A 8 'LOCK_NOW' curriculum/l2-uk-en/a1/audit/first-7-summary-2026-05-13.md` | raw quote |
| State Standard mapping was actually read | `grep -l 'state-standard-2024-mapping' .claude-conversation*.json 2>/dev/null` OR cite the file in the summary's "Authority" section | quote authority line |

Per `#M-4`: paraphrased claims ("I reviewed all 7", "all plans look good") without raw tool output = hallucination. Each review must cite the specific authority page it consulted (textbook page, State Standard map row, VESUM verify output).

## Commit + PR

```bash
git add curriculum/l2-uk-en/a1/audit/
git commit -m "$(cat <<'CMSG'
docs(audit): plan reviews for first 7 A1 modules (sequences 1-7)

7 per-module plan-review audit reports + roll-up summary at
curriculum/l2-uk-en/a1/audit/first-7-summary-2026-05-13.md.

No plan YAMLs modified — review-only per skill spec. Orchestrator
will read summary and decide LOCK_NOW / NEEDS_FIX / NEEDS_REVISION
transitions before the overnight build queue starts.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
CMSG
)"
git push -u origin claude/plan-review-a1-first-7-2026-05-13
gh pr create --title "docs(audit): plan reviews for first 7 A1 modules (sequences 1-7)" --body "$(cat <<'EOF'
## Summary

- Plan-review skill applied to A1 sequences 1-7 (`sounds-letters-and-hello`, `reading-ukrainian`, `special-signs`, `stress-and-melody`, `who-am-i`, `my-family`, `checkpoint-first-contact`).
- 7 per-module audit reports + 1 summary report.
- No plan YAMLs modified.

## Test plan

- [ ] All 7 per-module audit files present.
- [ ] Summary roll-up has PASS/FAIL table + cross-cutting patterns + LOCK recommendations.
- [ ] Skill consulted State Standard 2024 mapping (authority cited).
- [ ] CI: docs-only, only advisory `review/review` likely to fail; non-blocking per `#M-0.5`.

## Next step (orchestrator)

Read summary → lock plans that pass clean → dispatch fixes for plans with HIGH issues → re-review fixed plans → unblock overnight build queue.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

## Pre-submit checklist (MANDATORY per AGENTS.md:11-26)

- [ ] `.python-version` unchanged (`3.12.8`)
- [ ] `.yamllint` / `.markdownlint.json` unchanged
- [ ] No `status/*.json` or `review/*-review.md` files in diff
- [ ] No `sys.executable` (use `.venv/bin/python` for any Python tool invocation)
- [ ] No `@pytest.mark.skip` with empty `pass`
- [ ] Total files in diff < 20 (~9 expected: 7 per-module + 1 summary + maybe `.agent/state/...` if skill writes there)
- [ ] All changed files directly related (audit reports only)

## Scope boundaries (HARD)

May touch ONLY:

- `curriculum/l2-uk-en/a1/audit/*-plan-review.md` (new files)
- `curriculum/l2-uk-en/a1/audit/first-7-summary-2026-05-13.md` (new file)

May NOT touch:

- Plan YAMLs themselves (`curriculum/l2-uk-en/plans/a1/*.yaml`) — read-only
- Any code (`scripts/`, `tests/`)
- Any other curriculum content
- Decision cards or session-state

If a review surfaces a critical issue that would benefit from immediate fix, note it in the summary's "Cross-cutting" + recommend a follow-up dispatch — do NOT fix inline.

---

*Authority: user-overridden Plan A overnight orchestration (CLAUDE.md HARD rule on builds suspended for tonight). Per #M-4 + #DISPATCH-BRIEF-CHECKLIST.*

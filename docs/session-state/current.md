# Current - Codex orchestrator handoff (2026-05-30T20:35Z)

Latest-Brief: docs/session-state/current.md

> Handoff-only update. Treat `origin/main` and this file as authoritative.

## Thread / Role

- Main orchestrator thread is the **Orchestrator watchdog replacement**:
  `019e7836-06ef-7973-a630-07824922dfe5`.
- User explicitly corrected direction:
  - BIO is Claude-owned.
  - Codex drives orchestration, GitHub issue memory, PR queue, and A1 golden
    learner journey.
  - Use agents/compute, but keep ownership boundaries clear.
- Context is near auto-compact; continue in a fresh thread.

## Git State

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Branch: `main`
- HEAD before this handoff update: `2490db006e`
- Upstream: `origin/main`
- Modified file before handoff commit: `docs/session-state/current.md`
- Active delegates after closing the explorer: none known.

Recent commits before this handoff:

- `2490db006e` `docs(session-state): record issue triage board`
- `90235bc878` `docs(session-state): avoid stale BIO handoff head`
- `3ac4e7e7db` `docs(session-state): record BIO Phase 2 unblock`
- `2379c38d4c` `feat(bio): add Phase 2 plan for Mykhailo Drai-Khmara (#2456)`

## Critical Next Order

Do **not** jump straight into A1 implementation while PRs are waiting.

First clear the PR queue:

1. **#2459** `docs(bio): refresh Claude driver handoff — Phase-2 division + session lessons`
   - Branch: `docs/bio-handoff-update-2026-05-30`
   - Status at last check: `UNSTABLE` only because Gemini `review / review`
     was still in progress. Other checks were green.
   - BIO handoff/docs PR, Claude-owned lane. Inspect review result, merge if
     clean or route feedback to Claude.
2. **#2450** `feat(handoff): add agent-specific thread routers`
   - Branch: `codex/agent-thread-handoffs-2026-05-30`
   - This is operationally important: thread-handoff task becomes real on
     `main` only after #2450 lands.
   - It was previously `DIRTY`/`UNKNOWN` after main moved. Rebase/update,
     verify, and merge before relying on agent-specific handoff behavior.
3. **#2447** draft `fix(build): normalize stressed plan section headings`
   - Branch: `codex/m20-plan-section-heading-gate`
   - A1 support/blocker PR, not the product strategy itself.
   - Review/undraft/merge only if still sound after current main.

Only after those PRs are handled should Codex proceed into the A1 epic.

## Correct A1 Direction

Do not treat m20/m21/m22 as the strategy. They are support/validation issues
from the old V7.2 path.

The user’s product direction is:

- Start A1 from the beginning.
- Build the learner experience as the product spine.
- First slice is A1 M1-M7 safe onboarding / first contact.
- Fix pipeline/gates only when they block producing excellent learner content.

Read-only explorer found A1 M1-M7 sequence:

1. `sounds-letters-and-hello` — `Звуки, літери та привіт`
2. `reading-ukrainian` — `Читаємо українською`
3. `special-signs` — `Особливі знаки`
4. `stress-and-melody` — `Наголос і мелодика`
5. `who-am-i` — `Хто я?`
6. `my-family` — `Моя сім'я`
7. `checkpoint-first-contact` — `Підсумок: Перший контакт`

Explorer also found:

- Sequence source: `curriculum/l2-uk-en/curriculum.yaml`
- Each M1-M7 has plan YAML and discovery YAML.
- No populated content bundle was found for M1-M7.
- Only populated A1 lesson bundle found was `curriculum/l2-uk-en/a1/my-morning/`.

## Issue Board State

Issue triage already completed:

- 71 open issues.
- 0 missing `lane:*`.
- 0 missing `state:*`.
- BIO issues labeled Claude-owned.
- A1 golden path labeled Codex-owned.
- No issues closed.

Active board after PR queue:

- A1/Codex: #2389, #2390, #2418, #2419, #2380, plus #2447 PR if not merged.
- Orchestration/Codex: #2450/#2448, #2368, #2126.
- BIO/Claude: #2309, #2451, plus #2459 PR if not merged.

Proposed archive candidates only, do not close without review:

- #2351 likely superseded by #2418.
- #1969 likely superseded by #2418.
- #2132 likely stale promote-protocol result thread.

## Restart Commands

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git status --short
git log --oneline -8 --decorate --no-merges
gh pr list --state open --json number,title,headRefName,mergeStateStatus,statusCheckRollup,url,updatedAt,isDraft,reviewDecision --limit 20
gh issue list --state open --label state:now --limit 100 --json number,title,labels,url
curl -sS http://127.0.0.1:8765/api/delegate/active
```

For A1 M1-M7 inventory:

```bash
sed -n '1,220p' curriculum/l2-uk-en/curriculum.yaml
find curriculum/l2-uk-en/a1 -maxdepth 2 -type f | sort
sed -n '1,80p' curriculum/l2-uk-en/plans/a1/sounds-letters-and-hello.yaml
```

## Guardrails

- Keep main checkout read-only except handoff updates.
- Use `.worktrees/dispatch/<agent>/<task>/` for implementation.
- Do not edit generated status/audit/review artifacts, linter configs, or
  `.python-version`.
- Every commit must carry an `X-Agent` trailer.
- Do not delete/pause old automation unless the user explicitly instructs it.

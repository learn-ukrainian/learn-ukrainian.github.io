# Session Handoff — 2026-04-22 morning: decisions locked, pyenv pain fixed, pre-merge prep

## TL;DR

Overnight autonomous work complete (see [2026-04-22-overnight-bakeoff-and-124-plan-forks.md](2026-04-22-overnight-bakeoff-and-124-plan-forks.md)). User (Krisztian) reviewed the morning handoff and locked decisions A-D and the F4 writer/reviewer pairing. Fixed the pyenv-shim lock that was making every bash command wait 60 seconds. About to start **careful sequential merges**, then dispatch the remaining linguistic-fix + wiki-strip passes, then enter Phase 3 (l1-uk module build).

Main at `d7cdaa68b` (unchanged).

## Decisions locked this session

1. **Phase 0A writer winner: Claude Opus 4.7** — bakeoff mean 7.80, zero FAIL verdicts, most stable. Results at `docs/experiments/2026-04-22-writer-bakeoff-results.md`.
2. **Phase 0B reviewer: Codex primary + Opus escalation** — Codex handles bulk (strict, consistent, 10× capacity through 2026-05-17). Opus escalation for borderline cases (Codex scores 7.0-8.0).
3. **Phase 1B apply scope: full apply across l2-uk-en + l1-uk plans** — 782 English-gloss leaks propagated into l1-uk forks; fix once across both tracks. Gemini proposes, Codex applies.
4. **Phase 2B wiki policy: programmatic strip first, Opus rewrite residue only** — 147 L2-framing findings; deterministic section removal first, escalate specific wikis only if module-build surfaces issues.
5. **Phase 1C leak-inheritance: accept forks as-is** — fix in Phase 1B-apply pass across both tracks.

## Operational fix this session

**pyenv-shim lock removed.** Every `.venv/bin/python` call was waiting 60 seconds for a lock held by a long-dead `pyenv-rehash` process from 9:00 AM (PID 18715 from yesterday's work). Killed-already, cleared stale lock file, Python invocation now ~25 ms. This will make today's merge work dramatically faster.

Root cause: pyenv's rehash uses a file lock at `~/.pyenv/shims/.pyenv-shim`. When a rehash process dies without releasing the lock (crash, SIGKILL by system), the lock persists. Subsequent Python invocations try to rehash, wait 60s for the lock, then proceed. Accumulated ~hours of wait across overnight's 100+ bash calls.

Prevention: periodic check of the lock age. If >5 minutes old and no pyenv-rehash process alive, the lock is stale and can be removed.

## Next work (in order)

1. **Careful sequential merges** (tests between each):
   - `codex/phase-1a-structural-sweep` (9 tests pass)
   - `codex/phase-2a-wiki-metadata` (59 tests pass)
   - 124 plan forks: batch merge across both name patterns (`codex/fork-1c-*-a[12]-*` + `codex/fork-l1uk-a2-*`)
   - `gemini/phase-1b-linguistic-audit` (docs only)
   - `gemini/phase-2b-wiki-audit` (docs only)
   - Writer bakeoff results doc (docs)
   - Experiment raw data (reviews + aggregate)
2. **Phase 1B-apply dispatch** — Gemini proposes fixes per finding, Codex applies across both tracks. ~2 hr.
3. **Phase 2C wiki strip** — deterministic Python script removes L2-framing sections. Gemini reviews output.
4. **Phase 3 gate** — all above green → Phase 3 (l1-uk A1+A2 module build) fires with Opus writer + Codex reviewer.

## Branch naming inconsistency (2 A2 slugs)

When merging, check BOTH prefixes:
- `codex/fork-1c-a2-*` (67 of 69)
- `codex/fork-l1uk-a2-*` (2 of 69: `synonyms-antonyms-style`, `synthetic-future`)

Use `git branch --list 'codex/fork-*-a2-*'` to catch both.

## Git state

- Main: `d7cdaa68b` (unchanged)
- Disk: 35 GB free (85%)
- No worktrees remaining (all cleaned overnight)
- All 124 plan forks + 4 infra/audit branches preserved locally

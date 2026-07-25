# Primary-checkout ref guard (`.githooks/reference-transaction`)

Git-level guard that keeps the **primary checkout attached to `main`** for
every harness, not just the ones with PreToolUse hooks.

## Why (incident 2026-07-25, refs #5389 / #5396)

A `cursor` dispatch worker, running inside its own worktree
(`.worktrees/dispatch/cursor/rebase-5729`), reached out of it and ran git
commands against the primary checkout. Primary reflog:

```
a8d9a8f949 HEAD@{0}: checkout: moving from main to FETCH_HEAD
ba468fdab8 HEAD@{1}: pull: Fast-forward
```

The existing layers did not fire:

- `agents_extensions/shared/hooks/guard-primary-checkout-write.py` and
  `guard-branch-switch-in-main.py` are **harness** PreToolUse hooks — they
  only see Claude/Codex tool calls. Cursor/kimi/agy/deepseek workers never
  consult them.
- `scripts/agent_runtime/shims/git` only works when the shim directory is on
  `PATH` — a worker with the real git binary bypasses it.
- The #5389 heal fragment was installed into `.git/hooks/post-checkout`, but
  `core.hooksPath` is set to `.githooks` — which did not exist — so **no**
  `.git/hooks/*` hook was running at all. The detach was never healed.

A guard that lives in git itself (`core.hooksPath`, tracked `.githooks/`)
binds every harness, every shell, and every `git -C <primary>` reach-across.

## What the guard does

`.githooks/reference-transaction` fires on every ref transaction. In the
`prepared` state (the only state that can veto) it blocks, from
non-interactive contexts without the override:

- any update to `refs/heads/main` / `refs/heads/master` — commit, pull,
  `reset --hard`, `branch -f`, `update-ref` — **from any worktree context**
  (the protected ref is shared);
- any `HEAD` update whose new value is a raw commit — a **detach** — when the
  command targets the primary checkout (`git-dir == git-common-dir`). This is
  the `checkout: moving from main to FETCH_HEAD` incident class.

Deliberately allowed:

- `HEAD` symref retargets (`checkout -b`, `checkout <branch>`,
  `git worktree add`). A worktree-add internal HEAD write is indistinguishable
  from a branch switch inside the hook (verified empirically), and worktree
  creation from the primary is the standard dispatch flow. Wrong-branch
  primaries are auto-healed instead: `.githooks/post-checkout` runs
  `scripts/guardrails/primary_post_checkout_heal.sh` (#4857), which was
  previously dead code shadowed by `core.hooksPath`.
- everything inside linked worktrees (their git dir differs from the common
  dir);
- `fetch` / `refs/remotes/*` / `FETCH_HEAD` / `ORIG_HEAD` / `refs/stash`.

## Operator override

The guard never silently blocks a human:

- an **interactive terminal** (stdout or stderr is a TTY) is always allowed;
- scripted operator/service flows use the documented one-shot override:

```bash
LEARN_UK_ALLOW_PRIMARY_REF_WRITE=1 git <command>
```

The block message on stderr names this variable. The sanctioned heal path
(`assert_primary_on_main.py --heal`) sets it internally for its own
`checkout -B` / `pull --ff-only` subprocesses.

## Activation

`core.hooksPath=.githooks` is already set in the primary's `.git/config`. The
guard becomes active in a checkout as soon as that checkout contains the
tracked `.githooks/` directory (i.e. once the primary fast-forwards past the
merge of this change). To activate manually elsewhere:

```bash
git config core.hooksPath .githooks   # repo-local, relative to worktree top
```

Fresh clones need the same one-line config; the hooks themselves are tracked.

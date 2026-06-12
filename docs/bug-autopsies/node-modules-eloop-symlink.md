# Bug Autopsy: self-referential `node_modules` symlink breaks every Astro/npm build with `spawn ELOOP`

## Symptom

`npm run build` (and `npm run dev`, and `npm ci`) in `starlight/` **fails
instantly with exit code 194 and prints nothing** beyond the npm header:

```
> starlight@0.0.1 build
> astro build
# (no further output; exit 194)
```

npm's debug log shows the real error — `Error: spawn ELOOP` (errno -62) — while
trying to run a child process (e.g. the `sharp@0.34.5` install script, or the
`astro build` script itself). Because there is no output, it looks like "Astro
is broken" or "the build is hung." It is neither: running astro **directly**
(`node node_modules/astro/bin/astro.mjs build`) builds all 2353 pages in ~15s.
This recurs repeatedly across sessions ("why do we have this problem all the
time").

## Root cause

A **self-referential symlink at the repo root**:

```
learn-ukrainian/node_modules  ->  /Users/.../learn-ukrainian/node_modules
```

i.e. `node_modules` points at itself — an infinite symlink loop.

`npm run <script>` (via `@npmcli/run-script` → `@npmcli/promise-spawn`) builds
the child process' `PATH` by walking the directory tree **upward** from the cwd
and prepending every ancestor `node_modules/.bin`. When it spawns the script
shell, the kernel must resolve those PATH directories; resolving the looping
`learn-ukrainian/node_modules` exceeds the symlink-resolution limit and the
`spawn`/`execve` syscall returns **ELOOP**. npm aborts before the script runs —
hence exit 194 with empty output. Every `npm` invocation anywhere under the repo
is affected, because they all walk through that ancestor.

**Why it recurs "all the time": the self-referential symlink is COMMITTED to
git.** `node_modules` is tracked at the repo root as a mode-`120000` (symlink)
blob whose content — the link target — is the absolute self path
`/Users/.../learn-ukrainian/node_modules`. It landed on `origin/main` in commit
`124a1dee1f` (#3041). So **every `git checkout`, `git worktree add`, fresh
clone, and `git reset --hard origin/main` re-materialises the self-loop** at the
repo root. Removing it locally (or healing it with the canary) only lasts until
the next checkout/reset re-creates it from the committed tree — which is exactly
the "happens every time" loop the orchestrator's reconcile-via-`reset --hard`
flow triggers.

How a self-link got committed in the first place: the original loop was an
ad-hoc `ln -sf "$PWD/node_modules" "$PWD"`-style footgun (the link lands *inside*
`DIR` named after `TARGET`'s basename, pointing at itself), and **`.gitignore`
ignored only `node_modules/` (trailing slash = directory-only)**. A symlink
named `node_modules` is a *file*, not a directory, so the dir-only rule did NOT
ignore it — a `git add` then swept the stray self-symlink into #3041. The
gitignore gap is the load-bearing defect: had `node_modules` (no slash) been
ignored, the symlink could never have been staged.

Secondary amplifier: `scripts/delegate.py::_provision_data_symlinks` links the
root `node_modules` into every dispatch worktree (`worktree/node_modules ->
main/node_modules`). Once the root link loops, all those worktree copies loop
too, so a single bad root link breaks builds in N worktrees at once.

## Fix

0. **The cure — stop committing it:** `git rm --cached node_modules` to drop the
   self-referential symlink from the tracked tree, and change `.gitignore` from
   `node_modules/` to `node_modules` (no slash) so a `node_modules` symlink is
   ignored as well as the directory. After this, no checkout/reset/clone
   re-materialises the loop, and a future stray symlink can't be staged again.
1. **Immediate heal:** remove any already-materialised self-referential symlink —
   `rm learn-ukrainian/node_modules` (unlinks the symlink; never touches a real
   directory). Build works again immediately.
2. **Durable, creator-agnostic canary:** `scripts/audit/check_self_symlinks.py`
   detects and (with `--fix`) removes any `node_modules` symlink whose
   resolution raises ELOOP, under the repo root, `starlight/`, and every
   `.worktrees/**`. Valid symlinks (worktree → real main `node_modules`) resolve
   fine and are left alone; real directories are ignored; merely-dangling links
   are out of scope (different, less-severe failure). Wired to auto-heal in two
   always-run places: the SessionStart hook
   (`agents_extensions/shared/hooks/session-setup.sh`, pure-shell self-link
   case) and the API `/api/orient` health collection
   (`scripts/api/main.py::_self_symlink_canary`, general ELOOP case), mirroring
   the `core.bare` canary (#2842 / #2846).
3. **Stop propagation:** `_provision_data_symlinks` now refuses to provision when
   `worktree_path == main_repo_root` and skips any link whose resolved source
   equals the target (self-reference) or whose source already loops — so a bad
   root link is never copied into worktrees.

## Prevention

- The canary runs every session start and every API orient, so no session
  inherits a broken build, and a mid-session recurrence is healed at the next
  orient. This is the primary defense, since the creator is out-of-band.
- delegate worktree provisioning can no longer create or propagate a
  self-referential `node_modules`/`.venv`/`data` link.
- **Diagnostic tell:** `npm` exiting 194 with no output ⇒ check
  `ls -ld node_modules` for a self-pointing symlink and run
  `python scripts/audit/check_self_symlinks.py --fix`. Confirm the toolchain is
  fine by running astro directly: `node node_modules/astro/bin/astro.mjs build`.
- **Root prevention (in this fix):** the symlink is removed from the tree and
  `.gitignore` now matches `node_modules` (no slash), so it can neither
  re-materialise on checkout/reset nor be re-staged by a `git add`. This is the
  cure; the canary is defense-in-depth for already-checked-out copies and any
  future ad-hoc loop.
- **Watch:** any launcher / serve / deploy flow that symlinks dependency dirs
  via the `ln -sf TARGET DIR/` footgun (e.g. a path where `WORKTREE_DIR` resolves
  to `PROJECT_DIR`) can still create a *transient* loop in a working tree;
  it just can't be committed anymore, and the canary heals it.

## Links

- Bug introduced (committed self-symlink): `124a1dee1f` (#3041, 2026-06-12).
- Cure (this change): `git rm --cached node_modules` + `.gitignore`
  `node_modules/` → `node_modules`.
- Canary: `scripts/audit/check_self_symlinks.py`; tests:
  `tests/test_check_self_symlinks.py`
- Wiring: `agents_extensions/shared/hooks/session-setup.sh`,
  `scripts/api/main.py::_self_symlink_canary`
- Propagation guard: `scripts/delegate.py::_provision_data_symlinks`
- Sibling repo-health canary (same pattern): `core.bare` #2842 / #2846,
  `scripts/audit/check_core_bare.py`

# Closeout Review Checklist

> **Scope**: the closeout gate for a change already made — freezes scope,
> resolves the exact target, runs a non-mutating review, resolves a
> cross-family reviewer, and requires separate behavior proof for
> user-visible changes. For PR-comment posting, use `/code-review:code-review`.

All state for one review lives in a single JSON file so every step below
can be a separate CLI call. Pick a path once per review and reuse it:

```
STATE_FILE=.agent/review-closeout/<short-slug>.json
```

Every subcommand is `.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" ...`.

---

## Step 1: Resolve the target — explicit mode, never inferred

```bash
# local: staged + unstaged + untracked, diffed against HEAD
.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" \
  target --mode local --repo-root .

# commit: one already-made commit vs its parent
.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" \
  target --mode commit --commit <sha> --repo-root .

# branch: explicit base, merge-base semantics
.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" \
  target --mode branch --branch <branch> --base <base-ref> --repo-root .

# pr: actual PR base (never an assumed default branch)
.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" \
  target --mode pr --pr <number> --repo-root .
```

**A clean local working tree is not proof that a commit or PR was
reviewed.** `mode=local` on a clean tree returns `clean_tree: true` with
`base_sha`/`head_sha` both `null` — those `null`s are the structural guard:
a report built from that target cannot claim it verified a specific commit
or PR, because there is no SHA to point at. If the user asked you to review
a commit or a PR, resolve that mode explicitly — do not read "nothing
uncommitted right now" as "already reviewed."

This step never pushes. `pr` mode may `git fetch` the two SHAs it needs
(read-only) if they aren't already reachable locally — fetching to obtain a
target is fine; pushing a branch just so a diff exists is not, and this CLI
never does it.

---

## Step 2: Freeze the scope baseline — before the first review pass

```bash
.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" freeze \
  --issue "<issue/request reference>" \
  --intended-behavior "<what this change is supposed to do>" \
  --non-goals "<what it explicitly does not do>" \
  --owner-boundary "<the paths/surfaces this change owns>" \
  --review-profile "<code|infra|content|...>" \
  --risk "<low|medium|high>"
```

This prints the frozen baseline block — display it verbatim before
starting review. It captures the target's **every** changed path and
non-test LOC count, with no file-extension allowlist: shell scripts,
workflow YAML, config, schemas, and documentation are changed paths just
as much as `.py`/`.ts` files, and none of them are silently excluded from
scope or from review in the steps below.

---

## Step 3: Deterministic / static checks (non-mutating)

Run linters and type checks in **check-only** mode. Review preparation
must never mutate the source tree:

- Python: `.venv/bin/ruff check {files}` — **never `--fix`** during review
  prep. A fix is a finding like any other; applying it is Step 6's job,
  done explicitly, by the accountable agent.
- TypeScript/JS: `npx tsc --noEmit`, `npx eslint {files}` (no `--fix`).
- Do not run formatters, code generators, migrations, package installs, or
  any other command that changes files on disk as part of preparing this
  review. If a deterministic check has an autofix flag, run it in
  check/report mode only.

Report failures; do not silently correct them here.

---

## Step 4: Resolve the cross-family reviewer

Pull a fresh routing snapshot, then resolve:

```bash
curl -s 'http://localhost:8765/api/state/routing-budget?fresh_codexbar=true' \
  | .venv/bin/python -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps(d.get("lane_health", d)))' \
  > /tmp/routing-snapshot.json

.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" resolve-reviewer \
  --author-model "<the author's actual model/seat, e.g. claude, codex, deepseek-v4-pro>" \
  --review-profile "<same profile as Step 2>" \
  --risk "<same risk as Step 2>" \
  --domain "<code | folk_content | ... — only set non-default if it applies>" \
  --data-egress-policy "<omit unless this run is genuinely local-interactive>" \
  --routing-snapshot-file /tmp/routing-snapshot.json
```

If the Monitor API isn't reachable, omit `--routing-snapshot-file` — the
resolver is fail-open on health (no signal reads as healthy, so ladder
order alone decides) but **fail-closed on domain/data-egress**: leaving
`--data-egress-policy` unset excludes any candidate that requires a
specific egress policy (e.g. a China-hosted lane), it does not admit them
by default.

Read the `selected` field for the formal, blocking reviewer. Read `advisory`
for consult-only candidates — most notably `openai_frontier`: it always
resolves to a concrete model (currently `gpt-5.6-sol`), and it is
**advisory-only** when the author is OpenAI-family. An advisory verdict is
useful input; it is never a substitute for the formal gate. `trace` shows
every candidate walked and why it was excluded/selected/advisory — quote
it in the report so a substitution is never silent.

Dispatch the actual review to `selected.concrete_model` (or the advisory
model, clearly labeled as advisory, if `selected` is null). Ask it to find
bugs, logic errors, missed edge cases, and security/reuse issues in the
frozen target's diff — nothing outside `frozen_files`.

**Sibling instances**: if the reviewer or you spot the same bug pattern
elsewhere in the codebase, only widen the *look* to sibling instances of
that exact bug class within the frozen touched surfaces — not a general
audit of the owning module, and not files outside `frozen_files` unless a
sibling instance is actually found there (in which case treat it as a new
finding subject to the same breakers as everything else, not a freebie).

---

## Step 5: Record and adjudicate findings — nothing dropped, nothing "as-is"

For every finding, raise it, then adjudicate it:

```bash
.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" finding raise \
  --id F1 --summary "<one-line summary>" --source "reviewer:<concrete_model>"

.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" finding adjudicate \
  --id F1 --disposition "<in_scope_blocker|follow_up|stop_and_escalate>" \
  --rationale "<why this disposition>"
```

Disposition guide:

- **`in_scope_blocker`** — a real, verified bug inside the frozen scope
  that must be fixed before this closes out.
- **`follow_up`** — real but not blocking (out of frozen scope, or minor);
  track it, do not fix it here.
- **`stop_and_escalate`** — fixing it would itself blow a breaker (Step 6):
  it changes the public/task contract, crosses an owner boundary, needs a
  canonical design decision, or the fix/review loop already failed to
  converge. Escalate instead of patching around it.

**If the reviewer/challenger is unavailable**, raise the finding anyway (if
you have one from your own read) and leave it unadjudicated — do not
invent a disposition to unblock yourself, and do not apply it "as-is."
`scripts.review.findings.FindingsLedger.apply` structurally refuses to
apply anything that wasn't adjudicated to `in_scope_blocker`; there is no
CLI path around that. Run `finding report` at any point to see every
finding's full history, including ones still marked `UNADJUDICATED` — they
must appear in your final report, not vanish from it.

Only apply a fix for a finding once it is adjudicated `in_scope_blocker`:

```bash
.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" finding apply --id F1
```

(or `finding skip --id F1 --rationale "..."` for an explicit, rationale-carrying
decision not to act on it.) Applying the fix itself is your explicit
implementation action — the ledger only records that it happened.

---

## Step 6: Re-check scope after any fix

After applying findings, re-check the breakers before calling the review
done:

```bash
.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" check-expansion --repo-root .
.venv/bin/python -m scripts.review.closeout_cli --state-file "$STATE_FILE" record-cycle --outstanding-count <N>
```

Stop and reclassify (treat as `stop_and_escalate`, do not keep patching) when:

- `check-expansion` triggers — review-triggered files or non-test LOC
  exceed 2x the frozen baseline;
- `record-cycle` triggers — two review-triggered patch cycles in a row
  failed to shrink the outstanding-finding count;
- the fix changes the public/task contract or crosses the owner boundary
  frozen in Step 2;
- a canonical contract/design decision is required to proceed.

**Only** these justify pushing through a tripped breaker anyway: active
data loss, a crash, a broken install/upgrade, a release blocker, or a
concrete security exposure. "It would be nice to fix this too" is never
one of them.

---

## Step 7: Behavior proof (separate from code review)

Distinguish three layers explicitly in your report:

1. **Deterministic/static checks** — Step 3's linters/type checks.
2. **Source-aware code review** — Steps 4-5's reviewer verdict.
3. **Source-blind behavior proof** — actually driving the change as a user
   would, with no reference to the diff.

**CLI/API/UI/generated-artifact changes cannot be declared done from code
review alone.** If the frozen target touches any user-visible surface
(a CLI flag, an HTTP endpoint, UI, or a generated artifact like deployed
skill mirrors or built docs), run the project's `verify` skill (or drive it
manually) and record what you actually observed — not what the diff implies
should happen. If nothing in the frozen target has a runtime surface (pure
test/doc-only changes), say so explicitly instead of running a proof that
has nothing to exercise.

---

## Step 8: Report

```
## Closeout Review Report

### Scope baseline (frozen, Step 2)
{verbatim baseline block}

### Deterministic checks (Step 3)
{ruff/tsc/eslint results — clean or failures, never auto-fixed here}

### Reviewer resolution (Step 4)
Selected: {concrete_model or "none — see trace"}
Advisory: {advisory candidates, if any}
Trace: {full candidate trace, so every exclusion/substitution is visible}

### Findings (Step 5)
{every finding: id, summary, disposition, rationale, applied/skipped/unadjudicated —
 from `finding report`, verbatim. Never omit an unadjudicated finding.}

### Scope breakers (Step 6)
{expansion/cycle breaker results; note any stop_and_escalate and why}

### Behavior proof (Step 7)
{what was exercised end-to-end, or "not applicable — no runtime surface changed"}

### Summary
{final disposition: closed out / stop_and_escalate with reason / blocked on X}
```

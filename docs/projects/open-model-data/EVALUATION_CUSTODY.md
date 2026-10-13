# Evaluation custody reader

This module implements the E9 designation and mediated read boundary for #9608.
This delivery proves behavior on synthetic fixtures only. It does not seal, read,
write, or certify a real final set, and it does not complete any of the issue's
five acceptance criteria. AC4 retains its full requirement: "sealed final-set
hashes are committed, and the access log works".

## Trust basis

`scripts.projects.open_model_data.evaluation.custody.resolve_designation()`
accepts no caller identity. It requires all six checks:

1. Dispatch injects a task id matching `eval-steward-6321-*` and a run nonce.
2. `LU_TASKS_DIR` is unset, including the empty-string override.
3. The shared hot task record matches both values, is `running`, and uses
   scope launch mode. An archived record or popen fallback cannot designate
   a current reader.
4. `scope_unit_matches` binds the launch unit to that task and nonce.
5. The process's unified cgroup is the scope cgroup or a descendant. The
   check uses `/proc/self/cgroup`, `scope_cgroup`, and the current uid.
6. The record's model resolves through the catalog to the active
   `openai_frontier` seat, the designated Sol identity.

`recheck(designation)` repeats these checks before returning a payload. Only
non-identity task-record fields may change. The task-record hash is a diagnostic
binding, not a signature. The record, environment, Git refs, filesystem and
cgroup are trusted against ordinary misuse, not deliberate same-user forgery.
The cgroup assumption under the live dispatch sandbox remains unverified until
root runs the separately authorized synthetic canary.

## Reader and synthetic writer

Call `read_sealed(ArtifactRef(component, "final", ruler_version), purpose,
custody_root=private_root)`. The root comes from private ignored local state;
do not put its value in a command transcript or a public artifact.
`custody_verify` returns only `True`; `final_evaluation` returns a
`SealedPayload`. Its `repr` and `str` are redacted. Only evaluator code should
call `.data()`. Printing the returned bytes bypasses that protection.

The reader obtains schema `omd-sealed-rulers.v1` from the Git blob at
`refs/remotes/origin/main`, through `execution_safe_git.run_git`. The reserved
lookup is `docs/projects/open-model-data/sealed-rulers.json`. This task creates
no real manifest. Synthetic tests supply a fixture blob, including one actual
Git repository that proves unmerged and worktree-edited files are insufficient.
Manifest entries contain only component, final split, ruler version, SHA-256,
byte count, issuer task id, and custody-genesis hash. A reader requires one
matching entry, its genesis, a completed steward issuer record with the admitted
model, and a matching `sealed` event bound to the issuer run nonce.

`seal()` exists as synthetic writer support under qualification Q2. It requires
a live steward, creates a random genesis, refuses existing seals and orphaned
artifact files, syncs bytes, and records the digest and issuer. It returns only
the digest. It grants no permission to seal real data. `OutputGuard.append`
and the `review_build.build.execute` steward collision refusal are also covered
only as synthetic implementation support. A steward task cannot build training
data through that builder.

## Durable read outcomes

One bounded `fcntl` exclusive lock covers chain validation, reconciliation,
the attempt, access, and its terminal event. `OutputGuard` checks root and file
ownership, private modes, local filesystem, repository exclusion, symlinks, ACLs
and hard links. Artifacts open only through `OutputGuard.read`.

The `omd-custody-access.v1` JSONL chain uses zero-based sequence numbers and
SHA-256 of the preceding canonical entry. The first entry holds a random custody
id. `append` uses `O_APPEND`, handles short writes, and fsyncs both file and
directory. A durable `attempt` precedes designation validation and artifact
access. The log contains bounded ASCII metadata, nonce hashes and closed codes;
it never includes payloads, membership, Cyrillic or paths. Invalid caller labels
are reduced to fixed markers.

| Outcome | Terminal evidence |
| --- | --- |
| Success | `completed`, fsynced before a payload or `True` returns |
| Refusal | `refused` with a closed code; a digest mismatch discards bytes |
| Open failure | `open_failed` with `artifact_open`; no payload returns |
| Log failure | `access_log_unavailable`; no open if the attempt fails, no payload if a terminal write fails |
| Interruption | Best-effort `interrupted`; the next lock holder reconciles any orphaned attempt |

A corrupt or unreadable log refuses access before an attempt can be appended.
A partially written line is corrupt and is never silently repaired or treated
as proof. A log failure can leave an orphan requiring reconciliation, or a
corrupt chain requiring custody-owner recovery. `custody_busy` is a bounded
pre-attempt timeout and performs no artifact access. The lock's release proves
that no cooperating reader still owns an orphaned attempt. It does not establish
an external process's identity.

mediated reads logged; unmediated reads unknown

## Residuals and completion boundary

| Residual | Owner | Required disposition |
| --- | --- | --- |
| R1: deliberate same-user forgery of dispatch, log, scope or Git state | Operator | Isolated authority requires an operator decision; this code does not prevent it |
| R2: reads bypassing the reader remain unlogged and unknown | Operator | Blocks AC4 until operator acceptance on #9608 or an isolated-authority solution; recording the residual is insufficient |
| R3: evaluator bytes can appear in agent transcripts | E9 implementer and driver | Route bytes only to evaluator code; publish only digests and counts |
| R4: repeated final reads are visible but unrestricted | Root | Enforcing one-shot reads would require a separate policy decision |

The accountable driver, `gemini-open-model-data`, owns this task's remaining
integration. Root must run independent withheld fixtures on the exact merged
SHA, obtain outside-family exact-head critical review, pass CI Gate, and land
through the merge queue. Root also owns the shortened AC4 checklist correction
and the separate live synthetic canary decision. Synthetic tests and local
coverage do not replace those gates or certify real custody.

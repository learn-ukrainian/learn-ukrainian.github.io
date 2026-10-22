# Low-signal test rubric (OO-50, #11226) — t3code rubric, narrowed (A2 restart)

This rubric follows [pingdotgg/t3code#22557](https://github.com/pingdotgg/t3code/pull/22557):
keep the tests that guard the behaviours listed below, delete the noise classes, and let a
third vote decide genuine disagreements. It is applied to every Python test under `tests/`.

History. The first rubric (K1-K13) protected almost everything: 0.26% delete votes. The
first t3code version reached only 10.0% after 53 of 192 batches, because it counted every
gate or policy refusal as a security boundary and kept a `KEEP-other` catch-all. The CTO
decision of 2026-10-21 narrowed K-C, made "one kept test per distinct behaviour" apply to
every K class, and dropped `KEEP-other`. This file is that narrowed version.

Classify each TEST FUNCTION (or individual parametrize case), never a whole file.

## How to decide

1. Read the test body and the fixtures/helpers it uses. Ask: what defect in production
   code would make this test fail, and is that defect one of the KEEP behaviours below?
2. If it checks a KEEP behaviour AND it is the first (clearest) test of that distinct
   behaviour in the file, KEEP it with that class.
3. If a sibling test already checks the same code path and outcome, it is `D-COVERED`,
   whatever its K area. Name the kept sibling in the reason.
4. If it belongs to a DELETE class, DELETE it, even when the file sits in a K area. The K
   classes protect behaviour, not every test in a file.
5. There is no catch-all keep. A behaviour test outside K-A..K-F is DELETE (pick the D
   class that fits best; usually `D-TRIVIAL` or `D-COVERED`). The driver's restore pass and
   the phase B recheck rescue genuinely unique behaviour tests.
6. When genuinely unsure between a K class and DELETE, pick your best answer: two
   independent passes and a tie-break vote settle it. Do not default to KEEP.

## KEEP — one test per distinct behaviour, only for these behaviours

- **K-A orchestration and lifecycle correctness**: state transitions of dispatch, workers,
  leases, push, review, merge, closeout; deterministic race fixes (one test per distinct
  race).
- **K-B protocol and format translation, external-format parsing**: provider/CLI adapters,
  git/gh output parsing, MCP/HTTP protocols, persisted record schemas that other code reads.
- **K-C real security boundaries ONLY**: credential and secret handling, redaction of
  secrets, sandbox confinement, write/push/merge guards that stop unsafe repository or host
  writes, authentication. The allow-versus-refuse behaviour, not the wording of the refusal.
  NOT K-C: dispatch admission, load/memory/capacity checks, DoR, ownership and freeze
  checks, review-routing policy, model-eligibility policy and other gate or policy
  refusals. Those are the gates being relaxed: classify them like any behaviour test (one
  per distinct behaviour, usually K-A, the rest `D-COVERED`).
- **K-D persistence, migrations and store integrity**: sources, lexdata, datasets, exports,
  databases, on-disk stores.
- **K-E Ukrainian-language correctness**: VESUM/`sources` verification, stress, morphology,
  Russianism detection, word-card certification. This project's core domain.
- **K-F regression test for a bug that actually happened**: the test's name, docstring or
  an adjacent comment cites an issue, PR, incident or autopsy, or says it guards a bug that
  happened. Keep one per bug; a second test for the same bug is `D-COVERED`. A module
  docstring that only names the issue which built the feature is not K-F.

"Distinct behaviour" means a different code path or a different outcome (for example
allow versus refuse, success versus each distinct error kind, a different state
transition). Two tests that drive the same path to the same outcome with different inputs
are one behaviour.

## DELETE by default (t3code classes)

- **D-TYPE type- or schema-redundant**: asserts what a type, dataclass or runtime schema
  already guarantees, or re-checks a schema shape another kept test already exercises.
- **D-TRIVIAL trivial logic**: constants, getters/setters, a dataclass storing its fields,
  formatting helpers, string building, tautologies, and behaviour outside the K list.
- **D-COVERED same behaviour as a kept sibling, or basic behaviour exercised by a broader
  kept test**: name that test in the reason ("covered by test_x").
- **D-TIMER timers and wall clock**: real or fake timer / `sleep` tests, wall-clock
  performance asserts ("elapsed < N s"). Exception: a deterministic/injected clock that
  checks a K behaviour (lease expiry, auth TTL, stall guard) keeps that K class — the
  t3code review restored 22 auth tests cut as "timing" for exactly this reason.
- **D-MOCK mock-call mirrors**: asserts a mock was called the way the code calls it,
  where that call is not itself a K behaviour (a refused write, no secret egress, dispatch
  destination are K behaviours).
- **D-SMOKE smoke and import tests** duplicated by behaviour tests.
- **D-DUPCASE duplicate table or parametrize cases** in the same input partition. Keep one
  case per partition; distinct edge partitions (empty, unicode, boundary, error vs
  success) are not duplicates.
- **D-WORDING doc-prose and wording assertions**: a doc, brief, prompt, rule file, help
  text, log or error message contains or lacks a phrase. Exception: the CLI help sections
  the CLI standard requires (`agents_extensions/shared/rules/cli-help-standard.md`) stay
  as K-B.
- **D-RETIRED tests of retired policies or removed features.**

## Output (JSON Lines, one object per line)

`{"nodeid": "...", "verdict": "delete"|"keep", "class": "<class>", "reason": "one short line"}`

- `keep` rows name `K-A`..`K-F`; `delete` rows name a `D-` class. There is no `KEEP-other`.
- One row per listed node id (function level), judged on that test's own body.
- For D-DUPCASE you may add rows for individual case ids exactly as listed
  (`tests/x.py::test_f[a-b]`); the function-level row then states the verdict for the
  remaining cases.

## Process

- Haiku swarm, two independent passes with different batching (path order, shuffled order).
- A test is deleted when both passes say delete; kept when both say keep; a third Haiku
  vote decides disagreements.
- The driver then runs a restore pass over the delete set for K-C (security) and K-E
  (Ukrainian-language) behaviour wrongly cut, plus genuinely unique behaviour tests, and
  records every restore with a one-line reason.
- Mechanical apply (AST-based, by node id), manifests and the PR are phase B, which also
  rechecks the delete set.

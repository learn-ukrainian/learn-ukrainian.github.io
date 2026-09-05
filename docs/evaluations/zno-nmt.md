# ZNO/NMT model and agent evaluation

Run an exam under two conditions: **closed-book** (no tools) and
**Sources-assisted** (only selected reference tools). The evaluator separates
question preparation, candidate execution and answer-key scoring. It does not
require the LU corpus for closed-book runs or offline scoring.

The software is covered by the repository [MIT license](../../LICENSE).
Exam datasets and reference corpora retain their own rights. Do not infer a
dataset license from the software license.

## What “blind” means here

The candidate receives only a validated question packet. Its input has no gold
answers, explanations, source URLs or scoring metadata. A separate scoring
command reads the key after the candidate has submitted its answers.

The native adapter restricts the candidate's tool surface; the HTTP adapter
executes only explicitly permitted reference calls. These are controls on the
model's access through a trusted harness, **not an operating-system sandbox
against a malicious CLI binary, provider or operator**. Keep the grader/key
custodian separate from any untrusted execution host.

Published past papers may have appeared in model training. The term
`public-exposure-possible` records that uncertainty; hiding the key cannot
prove the questions were unseen. Private questions require independent authoring
and review, separate custody, corpus-overlap checks and a frozen test set that
has not been used for prompt tuning. This runner does not manufacture such
evidence or certify a private test's provenance.

The Sources corpus must not contain private held-out questions or their keys.
For public papers, reference search can potentially retrieve the published
question or its solution. Treat that as possible contamination, not proof of
reasoning. An MCP schema hash proves a tool interface, not corpus cleanliness.

## Installation and runtime storage

Use the project's existing Python environment from a dispatch worktree:

```bash
.venv/bin/python -m scripts.eval.zno_nmt --help
```

No services are deployed by this command. For LU operators on the notebook,
the public `services.sh` delegates to the sibling private infrastructure repo:

```bash
./services.sh tunnel start
./services.sh tunnel status
export SOURCES_MCP_URL='http://127.0.0.1:8766/mcp'
```

Community users can point `SOURCES_MCP_URL` at an authorized compatible server.
LU's private server and corpus are not included or made public by this package.
The filtered bridge expects the selected tools' names and JSON schemas to be
available. It refuses missing or unapproved tools.

Create a private runtime directory. All following commands assume you remain
at the worktree root:

```bash
umask 077
mkdir -p batch_state/zno-nmt-demo
```

Runtime output files are created exclusively with owner-only permissions.
Existing trials are never overwritten. Keep source exams, question packets,
keys, private retrievals and raw candidate results out of Git even if you use
a different directory. Do not publish an entire runtime directory.

## Prepare an exam

The normalized input format is `zno-nmt.exam.v1`. The following is a **synthetic
format example**, not an exam-quality benchmark or language evaluation. Save
it as `batch_state/zno-nmt-demo/exam.json`:

```json
{
  "schema": "zno-nmt.exam.v1",
  "title": "Synthetic format demonstration",
  "subject": "synthetic",
  "year": 2026,
  "provenance": {
    "source_url": "https://example.org/synthetic",
    "source_revision": "example-v1",
    "license": "synthetic-example",
    "exposure": "public-exposure-possible"
  },
  "scoring": {
    "kind": "benchmark",
    "policy_url": null,
    "pass_threshold": null,
    "expected_items": 1,
    "expected_points": 1
  },
  "items": [{
    "id": "1",
    "kind": "single",
    "question": "Select the option whose text is exactly X.",
    "options": [{"id": "A", "text": "X"}, {"id": "B", "text": "Y"}],
    "rows": [],
    "correct": "A"
  }]
}
```

For a matching item, use `kind: "matching"`, numbered `rows`, lettered
`options`, and a `correct` object such as `{"1":"B","2":"A"}`. Empty row
text is permitted when the numbered targets already appear in the question.
Preserve order, Unicode punctuation, stress marks and meaningful emphasis;
Markdown can represent emphasis from the source paper. Unsupported task types
are rejected, never silently removed.

```bash
.venv/bin/python -m scripts.eval.zno_nmt prepare \
  --exam batch_state/zno-nmt-demo/exam.json \
  --questions batch_state/zno-nmt-demo/questions.json \
  --key batch_state/zno-nmt-demo/grading-key.json
```

Give the candidate runner only `questions.json`. The key remains with the
grader. The packet and key have independent digests and binding checks.

### Import a public NLPForUA/ZNO paper

Use a pinned upstream revision, inspect the upstream data license, and retain
the source file's SHA-256. Do not download a mutable `main` as a frozen release.
The importer accepts the upstream array of complete papers:

```bash
.venv/bin/python -m scripts.eval.zno_nmt import-zno \
  --input batch_state/zno-nmt-demo/upstream.json \
  --test-id 515 \
  --metadata batch_state/zno-nmt-demo/metadata.json \
  --output batch_state/zno-nmt-demo/exam.json
```

`metadata.json` contains the normalized example's `title`, `subject`, `year`,
`provenance` and `scoring` fields only. Upstream task IDs are zero-based; the
importer maps them to one-based paper numbers, then preparation replaces them
with opaque candidate IDs. Matching headers are retained as row/column IDs.
Image-dependent or malformed items block the complete import.

The initial verification paper is `test_id="515"` from
[NLPForUA/ZNO at revision 35d4c976](https://github.com/NLPForUA/ZNO/tree/35d4c976599243b08dcd04303b557a7c2dc86068).
It corresponds to the Ukrainian-language block of the
[official 2022 demonstration paper](https://testportal.gov.ua/wp-content/uploads/2022/04/NMT_2022_demonstratsijnyj-variant_maket.pdf).
That PDF's SHA-256 is
`4c1dc23303ba919a71eb28210dc04fb4abb472b8d3d288fd63141bfdfd9dc154`.
The block contains 15 single-choice and five four-pair matching items: 20 items,
35 possible points. The [official 2022 FAQ](https://testportal.gov.ua/zapytannya-vidpovidi-2/)
documents scoring and the one-raw-point minimum subject threshold. Crossing
that minimum is weak evidence; report raw points and mistakes prominently.
This is a subject-block simulation, not certification that a model passed the
entire multi-subject NMT or can author curriculum reliably.

Upstream plain text loses some PDF emphasis. Independently compare every
question to the official paper and restore meaningful emphasis in a separately
versioned runtime representation before claiming paper fidelity. Record both
source and presentation hashes. Never tune the representation using a model's
score. ZNO-Eval v2 was still marked
[release in progress](https://huggingface.co/datasets/NLPForUA/zno-eval-v2)
when this workflow was prepared; it is not an implicit dependency.

## Configure a candidate

Save a configuration as `batch_state/zno-nmt-demo/config.json`. Pin a concrete
model ID available through your authenticated CLI instead of a moving alias:

```json
{
  "schema": "zno-nmt.config.v1",
  "adapter": "claude",
  "provider": "anthropic",
  "model": "REPLACE_WITH_CONCRETE_MODEL_ID",
  "effort": "high",
  "timeout_seconds": 300,
  "max_output_tokens": 4096,
  "max_tool_calls": 20,
  "repeats": 3,
  "tools": ["verify_word", "verify_stress", "search_text", "query_pravopys"],
  "corpus_id": "REPLACE_WITH_FROZEN_CORPUS_ID"
}
```

The same configuration is used for both conditions. `tools` defines the
assisted condition only. Closed-book execution exposes none of them. Do not
put endpoint URLs, tokens or private machine details in a checked-in config.
An unsupported effort setting must not silently become a different setting.
Requested effort and proven effective effort are different facts; absent
runtime evidence stays unknown.

## Run without MCP

```bash
.venv/bin/python -m scripts.eval.zno_nmt preflight \
  --config batch_state/zno-nmt-demo/config.json --condition closed-book
.venv/bin/python -m scripts.eval.zno_nmt run \
  --questions batch_state/zno-nmt-demo/questions.json \
  --config batch_state/zno-nmt-demo/config.json \
  --condition closed-book --output batch_state/zno-nmt-demo/closed-book.json
```

No Sources endpoint is needed for this standalone condition. The native
adapter uses a fresh external directory, disables built-in tools, skills and
ambient settings, and supplies an empty strict MCP configuration. It does not
reuse the current coding task's conversation.

## Run with Sources MCP

```bash
.venv/bin/python -m scripts.eval.zno_nmt preflight \
  --config batch_state/zno-nmt-demo/config.json --condition sources
.venv/bin/python -m scripts.eval.zno_nmt run \
  --questions batch_state/zno-nmt-demo/questions.json \
  --config batch_state/zno-nmt-demo/config.json \
  --condition sources --output batch_state/zno-nmt-demo/sources.json
```

Reference calls run through an allowlisted bridge. General browsing, local
files and shell tools are not exposed. Available access and actual tool use
are reported separately: an agent may choose not to use its references.
Time and tool-call limits apply. Missing corpus identity remains a limitation,
not an invented version. A configured corpus label alone is not proof that the
underlying corpus stayed unchanged.

For the paired experiment, prefer the following single command. It freezes
the schedule before execution, checks both conditions, alternates their order
across repeats, and creates a fresh session for every trial:

```bash
.venv/bin/python -m scripts.eval.zno_nmt pair \
  --questions batch_state/zno-nmt-demo/questions.json \
  --config batch_state/zno-nmt-demo/config.json \
  --out-dir batch_state/zno-nmt-demo/paired
```

A failed trial stops the schedule and remains recorded. Do not overwrite it
with a successful retry, select only the best run, or change prompts based on
the scored paper. A deliberately new experiment needs a new output directory
and its own declared configuration. API errors, malformed output and tool
violations are failures, not silently repaired answers.

## Score independently and compare

These commands do not invoke a model or MCP. Run them under the grader's
custody after answers are frozen:

```bash
.venv/bin/python -m scripts.eval.zno_nmt score \
  --questions batch_state/zno-nmt-demo/questions.json \
  --key batch_state/zno-nmt-demo/grading-key.json \
  --run batch_state/zno-nmt-demo/paired/001-closed-book.json \
  --output batch_state/zno-nmt-demo/closed-book-score.json
.venv/bin/python -m scripts.eval.zno_nmt compare \
  --questions batch_state/zno-nmt-demo/questions.json \
  --key batch_state/zno-nmt-demo/grading-key.json \
  --control batch_state/zno-nmt-demo/paired/001-closed-book.json \
  --treatment batch_state/zno-nmt-demo/paired/001-sources.json \
  --output batch_state/zno-nmt-demo/comparison.json
```

Single-choice items earn one point for the correct choice. Matching items earn
one point per correct pair independently; repeated selected columns are flagged
without erasing a correct pair. Missing/invalid answers stay in the denominator. A failed execution is
not a passing exam. `official` scoring needs a policy URL, explicit threshold
and complete expected item/point counts; a `benchmark` score has no pass claim.
For other subjects, years or response types, verify the applicable official
rules before selecting a policy. This implementation does not score essays,
numeric free responses, ordering tasks or images.

Comparisons reject mismatched datasets or generation settings. The output
contains paired item wins/losses/ties and a point difference, not a statistically
significant general ranking. Compare every repeat and report variability;
one paper from one model does not establish a community leaderboard.

## Share results without sharing the corpus

```bash
.venv/bin/python -m scripts.eval.zno_nmt export \
  --input batch_state/zno-nmt-demo/comparison.json \
  --output batch_state/zno-nmt-demo/public-aggregate.json
```

The export command selects numeric aggregate fields; it never copies arbitrary
metadata, exam text, answer values, paths, retrieval text or provider transcripts.
Inspect any additional narrative before publication. Share the model/version,
requested and verified effort, harness version, dataset and scoring policy,
prompt hash, repeat count, tool allowlist, non-sensitive corpus version and
limitations separately. Do not publish private retrieval snippets to make a
result look more reproducible.

Public-paper closed-book results are reproducible with the same accessible
model and data. LU Sources-assisted results depend on a private corpus and
must say so. Community users can substitute their own corpus/MCP and report
that as a distinct treatment, not the same benchmark condition.

## Adapter capability boundary

| Adapter | Closed-book | Reference tools | Model/effort evidence |
| --- | --- | --- | --- |
| Native Claude CLI | Strict empty MCP and built-in tool set | Filtered stdio-to-HTTP Sources bridge | CLI output checked; unreported effective effort remains unknown |
| Chat-completions HTTP | No tools supplied | Controller executes allowed MCP function calls | Exact returned model required; effective effort may remain unknown |
| Other agent harnesses, including native Codex | Not claimed by this version | Requires an independently verified adapter | Do not relabel an imported answer file as a verified isolated run |

HTTP configuration uses `adapter: "chat-http"` and environment-variable names
`endpoint_env` and `key_env`; populate their values privately. The adapter
implements a narrow chat-completions protocol, not every provider API. Local
model endpoints can use it; model-specific effort support still needs a
route-specific canary. The LU fleet's native subscription routing policy
continues to apply; this package does not authorize paid API substitutions.

## Validation and contribution

```bash
.venv/bin/python -m pytest tests/eval/test_zno_nmt*.py
.venv/bin/ruff check scripts/eval/zno_nmt tests/eval/test_zno_nmt*.py
```

The tests exercise packet/key tampering, malformed response structures,
partial credit, denominator retention, comparison drift, denied tool calls,
runtime limits and privacy-safe export. Mocked adapter tests prove mechanics,
not live provider support. A release needs separate full-paper paired live
evidence and independent review of the exact implementation revision.

Useful community contributions include independently audited exam importers,
provider adapters with isolation evidence, public-corpus reference baselines,
and new privately stewarded questions. Keep dataset preparation, prompt tuning
and held-out scoring separate so improvements remain measurable.

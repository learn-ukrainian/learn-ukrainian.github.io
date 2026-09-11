# ULDR program audit — 2026-09-11

## Disposition

**FAIL for the claimed gold linguistic dataset and reliable semantic evaluation readiness.**
The delivered package exists and its reported production counts reconcile. The
findings below concern evidence validity, evaluator correctness, and consumer
validation; they do not imply that all generated linguistic judgments are wrong.
Actual model training was not a completion requirement of this bounded audit.

Requested by the operator; tracking issue: #7930. Audited implementation:
`5fa6d752a50a66fa3498bd007d8a538b727d2e32` (merged PR #7927).
This report changes no implementation or dataset. Gemini retains remediation
ownership. Findings are independent inspection, not authorization to change scope.

## Verified delivery and limits

Read-only checks ran on the custody host. Only aggregate results were exported;
source text and held-out identities are absent from this report.

| Check | Observed result |
| --- | --- |
| Generated trajectories / DPO pairs | 1,200 / 1,200 |
| Train / held-out, each format | 967 / 233 |
| Consumer ShareGPT / DPO | Same 967 / 233 counts |
| Generated shard SHA-256 and byte receipts | All 8 files match |
| Distinct target strings, train / held-out | 967 / 233 |
| Exact normalized target overlap | 0 (strip + lowercase) |
| Generated positive calque labels | 1,200 / 1,200 |
| Designated seed trajectories / seed DPO pairs | 3 / 3 |
| Existing affected test suite | 17 passed in 0.74 seconds |

The seed counts contradict the reported delivery of 100 hand-curated seeds at
`data/projects/open_model_data/decolonization/seeds/`. The plan specifies that
location and an initial 100-item curation milestone. If another authoritative
100-item artifact exists, its immutable location and review evidence are needed.
The 1,200 generated rows are not evidence of 100 individually curated seeds.

The exact target split is real. It does not establish source-family isolation,
semantic independence, or independence from the rules used to generate labels.
This audit does not assert actual cross-partition contamination. Existing source
collection approval is not reopened. Historical human-pilot findings are outside
this ULDR audit. No complete regeneration or model training was performed.

Source references below are repository-relative paths and one-based lines at the
audited SHA. They must be inspected at that SHA, not a moving branch.

## Findings

### F1 — P1: Phrase evidence verifies only the first word

`v4_decolonization_reasoning.py:278–424` (under
`scripts/projects/open_model_data/`) reduces multiword alternatives to their first
word for VESUM, textbook, and dictionary checks. A textbook containing only that
word can therefore be returned as evidence for an absent whole phrase.

A synthetic SQLite textbook probe reproduced acceptance where the requested
phrase's second word was absent. This is a matching defect, independent of any
judgment about the selected Ukrainian example. Require full expression evidence
with appropriate inflection/context handling and separately identify token-level
morphological checks. Add a negative fixture containing only the first word.

### F2 — P1: Generated gold judgments exceed their evidence

`v4_decolonization_reasoning.py:431–620` assigns the target a calque label
unconditionally, accepts a positive VESUM form count as a living-standard fallback,
and emits categorical normative/historical explanations from templates and spelling
heuristics. Candidate `source_tag` and `provenance_note` do not survive in the
trajectory or DPO output. Source evidence is flattened into a string.

A synthetic arbitrary target with one VESUM-positive alternative and no textbook
or dictionary evidence still received a positive calque label and a living-standard
recommendation. The production aggregate confirms all 1,200 labels are positive;
it does not prove every label is incorrect. Inflectional existence alone does not
establish appropriateness, register, or a particular historical account.

Require evidence for the target judgment and each claimed recommendation, keep
uncertain cases out of gold, preserve traceable source records, and substantiate
historical claims individually. The manifest's `vesum_verification_rate`
(`:866–868`) is a constant 1.0 for nonempty output, not a measured full-record
semantic verification rate. Rename or compute it with an explicit denominator.

### F3 — P1: Contradictory answers can score 100 percent

`v4_evaluate_decolonization.py:76–121` uses global critique words, alternative
substrings, and two reasoning keywords as proxies for semantic correctness.
With synthetic target `badtoken` and alternative `goodtoken`, this response scores
1.0 and PASS:

> badtoken — це правильний вибір. Не вживайте goodtoken. Тут немає помилки. Суфікс. Словник.

It recommends the target and rejects the alternative. The keyword-only answer
`goodtoken суфікс словник` also scores 1.0; an empty answer reports
`calque_eliminated=True`. A recognized explicit-affirmation pattern fails correctly
as a positive control, so the issue is incomplete semantic handling.

Treat these outputs as lexical heuristics, not State Standard compliance or
historically grounded reasoning. Add adversarial negation, unrelated-keyword,
quotation, refusal, and unsupported-explanation cases and independently validate
semantic scoring before using these metrics to select a model.

### F4 — P1: Evaluation denominator excludes missing items and accepts duplicates

`v4_evaluate_decolonization.py:152–205` iterates predictions, silently ignores
unmatched records, and divides by matched result rows. A two-item synthetic gold
set with three copies of one passing prediction and one unknown prediction returns
`total_evaluated=3` and `pass_rate=1.0`. The absent gold response, duplicate identity,
and unmatched prediction are not reported.

Reconcile exactly one prediction against every expected gold identity. Reject or
explicitly report duplicates and unknowns; preserve missing predictions in the
expected denominator. Also reject ambiguous fallback matching.

### F5 — P1: Consumer formatter trusts partition labels

`v4_format_decolonization.py:111–130` performs no cross-partition identity/target
reconciliation. A synthetic manifest pointing train and held-out at identical SFT
and DPO rows exports successfully. The existing end-to-end test even reuses the
same DPO record across partitions (`test_v4_format_and_evaluate.py:154,165`).

The actual delivered target strings are disjoint, as verified above. This finding
is a missing enforcement gate, not a demonstrated leak in these artifacts.
Validate within-format and SFT/DPO identity consistency and partition isolation
before publishing consumer outputs.

### F6 — P2: Missing shards and oversized output do not fail closed

`v4_format_decolonization.py:118,125` skips missing declared input files. A manifest
with nonexistent held-out shards still produced an empty consumer manifest with
both quality flags true. Require every declared input, digest, byte size, and count
to reconcile before output publication.

Sharding at `:133–178` uses row count and merely records bytes. A synthetic single
row produced a 2,001,016-byte output successfully, despite the documented size
contract. Enforce the byte limit and explicitly reject an individually oversized
record; row-count sharding cannot guarantee it.

### F7 — P2: Training recipes need model-specific conversation adaptation

The formatter emits `system/human/gpt` roles (`:53–56`), while the training guide
passes them directly to TRL with Gemma 2 (`decolonization-training-guide.md:63–98`).
Inspection and isolated execution of TRL's current conversion helper preserved
those role values. Gemma's documented format places system instructions in the
initial user message. DPO puts instructions in a separate `system` column
(formatter `:72–75`); isolated execution of TRL's tokenization body showed that
column does not enter the prompt/completion tokens.

Convert role values and preserve system instructions using the selected model's
chat template. Pin dependency versions and add a small tokenizer/preprocessing
smoke test that inspects rendered input before training. This is source/helper
compatibility evidence, not a completed full trainer failure: TRL/datasets and
model weights were not installed for this audit.

Official references inspected on the audit date:
[TRL conversion helper](https://github.com/huggingface/trl/blob/main/trl/data_utils.py),
[TRL DPO implementation](https://github.com/huggingface/trl/blob/main/trl/trainer/dpo_trainer.py),
and [Gemma formatting](https://ai.google.dev/gemma/docs/core/prompt-structure).
These upstream links move; the observed helper behavior is date-scoped.

## Validation and reproduction

At the pinned dispatch checkout, the prescribed project interpreter ran:

```sh
.venv/bin/python -m pytest -q \
  tests/projects/open_model_data/test_v1_decolonization_contracts.py \
  tests/projects/open_model_data/test_v4_decolonization_reasoning.py \
  tests/projects/open_model_data/test_v4_format_and_evaluate.py --tb=no
```

Result: **17 passed**. The invocation used the host's shared project interpreter;
`.venv/bin/python` above denotes that prescribed interpreter. Passing schema and
happy-path checks do not cover the reproduced semantic and reconciliation failures.

Minimal reproduction of F3 from the checkout:

```sh
.venv/bin/python - <<'PY'
from scripts.projects.open_model_data.v4_evaluate_decolonization import evaluate_single_response
r = evaluate_single_response(
    'badtoken', ['goodtoken'],
    'badtoken — це правильний вибір. Не вживайте goodtoken. '
    'Тут немає помилки. Суфікс. Словник.',
)
assert r['composite_score'] == 1.0 and r['is_pass']
print(r['composite_score'], r['is_pass'])
PY
```

The remaining probes used temporary synthetic SQLite/JSONL fixtures: first-word
only textbook evidence (F1), an arbitrary candidate without source evidence (F2),
two gold identities with duplicated predictions (F4), identical rows declared in
both partitions (F5), missing shards and a two-million-character row (F6).
No production source text was needed for those reproductions. Read-only helper
reviews were same-provider evidence; they do not satisfy a formal cross-family
merge review. This report is for branch/PR review and is not a merge approval.

## Required disposition

Preserve the reconciled package and counts as delivery evidence, but do not use
the current gold labels or heuristic pass rates as proof of linguistic quality.
Gemini should resolve F1–F6, reconcile the seed milestone, and validate F7's actual
pinned training path. Re-review the resulting exact head with adverse fixtures
and qualified source-grounded linguistic assessment. Closure requires explicit
per-finding evidence; this report does not authorize training, publication, or a
change to the source-collection boundary.

## Remediation re-review — PR #7933

**VERDICT: FAIL** at exact head
`69e72ef4a90990d4edbd7fb9c8ef15f8e8d6a6b6`.
The remediation makes useful changes, but the statement that all findings are
resolved is not supported. The original audit above remains historical evidence;
this section records the new head's disposition.

### Confirmed improvements

- All 20 affected tests pass (0.82 seconds on the custody host); current PR CI is
  green, with some inapplicable jobs skipped.
- F1's original first-word-only textbook counterexample is rejected. VESUM now
  checks every constituent token, and dictionaries have a full-phrase query path.
  Both deployed dictionary tables have the `definition` column used by that path.
- F2 adds provenance strings and measured VESUM count/denominator fields in code.
- F3 rejects the original contradictory answer, empty output, and short keyword
  fragment. These are specific counterexample fixes, not semantic validation.
- F4's original duplicate/missing fixture now reports 2 expected, 1 evaluated,
  1 missing, 2 duplicates, 1 unknown, and a 0.5 pass rate.
- F5 rejects identical IDs and overlapping SFT targets across partitions.
- F6 rejects nonexistent shards and individually oversized records and rolls
  shards by UTF-8 bytes. The nine delivered consumer JSONLs have a maximum size
  of 1,799,218 bytes. A synthetic Unicode rollover also passed.
- F7's DPO system instruction now reaches tokenization in the isolated TRL helper
  probe. Full trainer execution was not performed.

### R1 — P1: The delivered canonical dataset was not remediated

Git-blob comparison between the audited original and remediation heads shows
**all nine files under `generated/` are unchanged**, including all trajectories,
DPO pairs, and the canonical manifest. Aggregate inspection found the new
provenance marker in **0 of 967 training trajectories**. Consumer reformatting
therefore republishes the original reasoning/evidence, not newly generated output
from the revised attestation code.

Regenerate and validate canonical artifacts after the evidence defects are fixed,
then derive consumer artifacts from that exact verified generation. Reconcile
all receipts and describe any changed denominator. Formatter changes alone do
not close findings against the delivered linguistic data.

### R2 — P1: F2 still teaches unconditional gold and living-standard claims

At `v4_decolonization_reasoning.py:553–559`, a VESUM-only alternative is now labeled
`technical_compound` or `classical_regional`. But `:618–630` still calls the primary
alternative a verified living standard and says the target should be avoided;
`:637–648` still sets the target calque flag to true and places the same alternative
in `primary_living_standard`. Historical explanations remain category templates.

A synthetic target with a VESUM-positive `valid phrase` and no textbook/dictionary
evidence receives `technical_compound` while retaining that same phrase as its
primary living standard and a normative final recommendation. Changing one
register field does not remove the contradictory training supervision.

Gate all judgment-bearing fields on evidence. Preserve uncertainty consistently
instead of replacing one unsupported register label with another. Retain
addressable source evidence rather than provenance text alone.

### R3 — P1: F3 still scores non-answers at 100 percent

At `v4_evaluate_decolonization.py:149–179`, length checks augment the same keyword
heuristics. For target `badtoken` and alternative `goodtoken`, both examples
still return **1.0 / PASS**:

> goodtoken суфікс словник суфікс словник суфікс словник

> Я відмовляюся оцінювати badtoken чи goodtoken. Слова «калька» та «суфікс» наведено лише для прикладу.

The second explicitly refuses to evaluate either expression. Additionally, the
new target-independent affirmation pattern at `:51` makes a recommendation of
the alternative followed by “Це не є помилкою” score zero even when the target
is absent. Contextual meaning remains unmeasured. Do not label these heuristics
State Standard compliance or grounded reasoning; validate scoring against an
independently adjudicated adverse set.

### R4 — P1: F5's target firewall excludes DPO targets

`v4_format_decolonization.py:245–255` builds target sets only from SFT trajectories.
A synthetic train SFT target `a`, train DPO target `b`, and held-out SFT/DPO target
`b`, all with distinct IDs, export successfully with
`verified_disjoint_targets=True` and overlap zero.

Validate the combined SFT/DPO target sets and pair-to-trajectory correspondence.
This proves an enforcement gap; it does not assert contamination in the delivered
artifacts.

### R5 — P2: F4 can score an explicit ID against the wrong gold item

`v4_evaluate_decolonization.py:253–258` mixes exact ID and prompt-substring matching
in a first-match loop. With two synthetic gold items, prediction ID
`synthetic.otherbadtoken` and prompt `Compare badtoken with otherbadtoken` is scored
against `badtoken`, leaving the explicitly identified item missing. Resolve exact
identities first and reject conflicting or ambiguous fallback matches.

### R6 — P2: F6 still risks destructive or falsely successful publication

`v4_format_decolonization.py:198–200` deletes existing consumer JSONLs before
parsing and firewall checks. A rejected overlap fixture removed a previous
synthetic output. Validate the full input and stage replacement outputs before
atomically publishing them.

The nonempty check at `:193–196` checks bytes only: whitespace-only shards still
produce successful zero-row exports. Declared input hashes and record counts
also remain unreconciled. Validate parsed records and complete manifest integrity,
not just existence and positive file size.

### R7 — P1: F7's dual SFT fields do not fix the documented TRL path

The formatter emits both legacy `conversations` and adapted `messages`
(`v4_format_decolonization.py:54–65`), while the recipe passes the whole row into
SFTTrainer. Current upstream TRL detects `conversations` and runs
`maybe_convert_to_chatml`, which overwrites `messages` from that field. Executing
that official helper on a synthetic new-format record produces roles
`system/human/gpt`, discarding the intended `user/assistant` adaptation.

Select the intended representation explicitly before training, and test the
actual preprocessing path. The guide's smoke check manually reads `messages`;
it bypasses the conversion that loses the adaptation. Pin dependencies. Evidence
here is official-source and isolated-helper execution, not a full model run.

### R8 — P2: The guide misidentifies Gemma 4 control tokens

`decolonization-training-guide.md:55–71` claims `<thought>...</thought>` is Gemma 4's
native reasoning channel and presents older `<start_of_turn>` syntax as its
shared format. Google's current documentation specifies `<|turn>` / `<turn|>`
and `<|channel>thought` / `<channel|>`, with `<|think|>` enabling thinking.

Plain `<thought>` text can be custom supervision, but it is not the documented
native control channel. Use separate verified model-template paths and a smoke
check of the actual control-token sequence. Merely finding literal tags in the
rendered text does not establish native reasoning-channel training. The claimed
20–30 percent Ukrainian token reduction and comparative linguistic-refusal
behavior have no supporting measurement in this PR and remain unverified.

Official sources checked on 2026-09-11:
[Google Gemma 4 formatting](https://ai.google.dev/gemma/docs/core/prompt-formatting-gemma4),
[TRL conversion code](https://github.com/huggingface/trl/blob/main/trl/data_utils.py),
and [SFT preprocessing](https://github.com/huggingface/trl/blob/main/trl/trainer/sft_trainer.py).
Upstream URLs move; conclusions about TRL are scoped to the inspected source date.

### Seed milestone and closure

The plan now describes three reference anchors instead of the previous 100-item
curation target. That accurately states the observed count, but documents a scope
reduction rather than delivery of the missing 97 curated items. The operator must
accept that changed completion denominator or the curation remains outstanding;
a remediation summary cannot silently redefine completion.

Reproduction used temporary synthetic fixtures and aggregate exact-blob checks;
no protected source text or held-out identities are included. No production
regeneration or training was run. Close the findings only after fresh artifact
reconciliation and exact-head adversarial re-review. This review does not authorize
merging PR #7933.

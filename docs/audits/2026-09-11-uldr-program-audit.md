# ULDR program audit — 2026-09-11

Latest verification: **PASS for the bounded delivered-package audit** on merged
`main` at `303fbadbd171e36bf9c5f025a7c61011ca327847` (PR #7972).
See [final merged-main verification](#final-merged-main-verification--303fbadbd1).
Earlier verdicts below are historical and apply only to their named heads.

## Disposition

**Findings F1–F7 and M1 are remediated.** The delivered dataset, generator,
formatter and evaluator are verified within the artifact, regression and
reference-output checks documented here. M1's final subject-binding correction
is now on merged main, and the held-out reference self-check reproduces
**232/234 passes (99.15%)** with a fully reconciled denominator.

This is not a claim of independently gold linguistic judgments, model
generalization or completed training. The evaluator remains a heuristic proxy;
the two failing reference records and previously documented 97-seed curation
residual remain visible. Those limits are not erased by closing the reproduced
implementation findings.

Requested by the operator; tracking issue: #7930; report PR: #7931.
Initial audited implementation: `5fa6d752a50a66fa3498bd007d8a538b727d2e32`
(merged PR #7927). This report changes no implementation or dataset.
Gemini retains ownership of the documented curation residual.

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

## Regenerated-package re-review — dcc5bced and 3083e356

**VERDICT: FAIL** at final reviewed head
`3083e3569172bc0c43ee5066fa8ab527d0413e05` of PR #7933.
Implementation and artifact checks began at
`dcc5bced7c27dc6f9828a6618541bc2d6ad774aa`. The head advanced during review;
the exact intervening diff adds only a 64-line Gemma-format test. No implementation,
guide, schema, or dataset content changed between those heads. The added test was
inspected and the affected suite rerun: **27 passed in 0.87 seconds**.

### Verified progress and residual disposition

| Prior finding | Disposition at this head |
| --- | --- |
| R1: unchanged canonical artifacts | Fixed: all 9 files regenerated; 1,200/1,200 provenance markers |
| R2: VESUM-only primary standard | Specific fallback rejected; target and historical evidence remain unresolved |
| R3: prior refusal/repetition probes | Those examples fixed; a new semantic non-answer still scores 1.0 |
| R4: combined DPO/SFT firewall | Original example rejected; conflicting target fields bypass the check |
| R5: exact identity precedence | Original wrong-item matching example fixed |
| R6: publication/integrity | Content validation improved; move-failure loss and real count-key mismatch remain |
| R7: dual-column TRL overwrite | Fixed by explicit role mapping and removing conversations before SFT |
| R8: native Gemma 4 formatting | Documentation corrected; actual training conversion still emits literal tags |
| Seed denominator | Correctly restored: 3/100 delivered, 97 outstanding |

The canonical package has 1,200 trajectories and 1,200 DPO pairs, split **966
train / 234 held-out** in each format. All eight generated JSONL hash, byte and
`records_count` checks pass. The maximum canonical shard is **1,794,425 bytes**;
the maximum consumer shard is **1,663,396 bytes**. Consumer counts reconcile.
Exact normalized canonical target overlap is zero. These are actual artifact
checks, not synthetic examples. A provenance marker is source text attribution;
its presence alone does not make evidence independently addressable or verified.

### G1 — Evidence limitation: The reported benchmark is reproducible from packaged reference answers

The untracked `consumer/held_out_evaluation_report.json` reports 234 evaluated,
0.9957 elimination/suggestion rates, 0.9915 grounding/pass rates, and 0.9932 mean
score. A read-only custody-host probe used the existing held-out ShareGPT `gpt`
answer in every row as the prediction and evaluated it against canonical gold.
**The resulting report equals the existing report exactly, including all
per-item evaluation fields.** No model invocation was needed.

This establishes that the reported result can be a generator/evaluator self-check;
it does not establish independently produced model performance, historical
accuracy, or linguistic gold quality. The report has no model, prediction-input
digest, or inference receipt. Label the score as a packaged-reference self-check,
or supply independently produced prediction provenance before describing it as
model evidence. This finding does not add model training to repository scope.
No held-out text or identities leave custody in this audit.

### G2 — P1: Further regex filters still accept semantic non-answers

`v4_evaluate_decolonization.py:189–225` accepts the following synthetic response
for target `badtoken` and alternative `goodtoken` with **1.0 / PASS**:

> Оцінки не буде. На дошці написано goodtoken. Учень читає словник, бо його цікавить суфікс.

The answer withholds evaluation and describes classroom text. It does not
recommend the alternative or give a linguistic diagnosis. Keyword diversity and
a connective are not semantic grounding. The earlier refusal/repetition examples
now fail correctly, but their fixes do not close this broader finding. Preserve
heuristic labels and require independent adverse semantic assessment before
using these scores as evidence of linguistic correctness.

### G3 — P1: Target-field precedence differs between validation and export

`v4_format_decolonization.py:281–285` validates a top-level target before a metadata
target; `:88–89` exports the metadata target first. A synthetic training DPO record
with `target_term="a"` and `metadata.target_term="b"`, alongside training SFT `a`
and held-out SFT/DPO `b`, passes with distinct IDs. The two exported DPO partitions
both contain target `b`, while the manifest reports zero overlap.

Reject conflicting representations or resolve one canonical target and use it
throughout validation and formatting. The original single-representation overlap
fixture is fixed. This counterexample demonstrates an accepted-input failure,
not contamination in the current regenerated artifacts.

### G4 — P2: Tokenless responses crash the evaluation batch

At `v4_evaluate_decolonization.py:185`, a nonempty response can produce zero tokens,
then divide by `len(tokens)`. Synthetic responses `...` and an emoji each raise
`ZeroDivisionError`. Handle tokenless responses as scored failures so one malformed
prediction cannot abort the benchmark. This is separate from empty-string handling,
which already works.

### G5 — P2: Publication is not atomic on filesystem failure

`v4_format_decolonization.py:368–382` deletes previous JSONLs, moves replacements
one at a time, and removes staging in `finally`. Injecting `OSError` on the first
move leaves old shards deleted, the old manifest present, no replacement shards,
and staging removed. Pre-publication content failures now preserve outputs, but
publication itself still needs a recoverable generation switch or rollback.

### G6 — P2: Count validation checks fields the canonical manifest does not use

`v4_format_decolonization.py:243,256` validates optional `trajectories_count` and
`dpo_pairs_count`. Actual canonical shard receipts use `records_count`. A synthetic
manifest declaring `records_count=2` with one trajectory and one DPO row exports
successfully. Reconcile the real contract field against both input streams and
verify aggregate totals. Unknown partition names also still skip processing
(`:209–211`) and can lead to a falsely successful empty publication.

Actual generated receipts reconcile in this audit. This finding concerns missing
protection against inconsistent subsequent inputs. Declared hash mismatches,
whitespace-only shards and the previous missing-file examples are now rejected.

### G7 — P2: Gemma 4 native thinking is still absent from the executed recipe

The guide's `convert_to_chatml` (`decolonization-training-guide.md:114–130`) correctly
maps roles and removes the conflicting column, but copies literal
`<thought>...</thought>` unchanged into assistant `content`. The smoke check
(`:229–232`) still checks for those literal tags rather than native channels.

An isolated probe executed the exact documented converter and Google's current
Gemma 4 Jinja template on synthetic input. It produced `user/assistant` roles,
preserved literal thought tags, and emitted **no native thought channel**. A
positive control supplying the template's `reasoning` field did emit the native
channel. No tokenizer weights, model, or full trainer were loaded.

The latest added test manually constructs the desired Gemma strings inside the
test itself; it does not execute the guide's training path or the official template.
It therefore cannot establish that the training recipe produces those strings.
Implement and validate the intended model-specific transformation, or explicitly
describe the recipe as literal-tag supervision rather than native-channel training.

Sources checked on the audit date:
[Google's Gemma 4 template](https://huggingface.co/google/gemma-4-31B-it/blob/main/chat_template.jinja)
and [official control-token documentation](https://ai.google.dev/gemma/docs/core/prompt-formatting-gemma4).
The upstream template is date-scoped; production recipes should pin it.

### G8 — P1: The new alternative gate does not establish target or historical truth

`v4_decolonization_reasoning.py:575–584` now requires at least one alternative that
was assigned `living_standard`; this genuinely removes the VESUM-only fallback.
But alternative occurrence is not evidence that the target is a calque or that a
specific suppression history applies. The target flag remains unconditional
(`:649`), and the historical explanation remains selected by spelling/category
(`:593–623`). The code still needs evidence tied to those separate claims, not
just evidence that an alternative exists. All 1,200 regenerated targets remain
positively labeled; this aggregate does not prove that every label is wrong.

A concrete alternative-level defect also remains at `:544–546`: candidate-level
`curated_evidence` is assigned to every VESUM-positive suggestion. In a synthetic
case with two alternatives and evidence naming only the second, both become
`living_standard` and the unsupported first alternative becomes primary. Tie
curated evidence to the exact recommendation it supports before selecting the
primary; a nonempty candidate evidence list is not a per-alternative proof.

The source approval boundary is unchanged. The unresolved requirement is to bind
the labels and explanations to the evidence actually supporting them, preserve
uncertainty, and demonstrate linguistic quality independently of the generator's
own templates.

### Required next disposition

Do not report all findings closed. Preserve the verified regeneration, formatting
and reconciliation improvements. Resolve the remaining semantic, identity,
publication and native-template defects with adverse fixtures that exercise the
actual production paths. Keep the 97-seed residual visible. Repeat exact-head
review after those changes; this audit authorizes no merge or model execution.

## Fourth re-review — 2fdd9c25

**VERDICT: FAIL** at `2fdd9c25cdfb7ba1ee6c4cf9e08692e1a9f69c32` of PR #7933.
This section supersedes prior dispositions where it explicitly marks a finding
fixed. The review remains bounded to the existing audit scope.

### Confirmed fixes and validation

- **31 affected tests pass** in 0.85 seconds at this exact head, including the
  four contract tests alongside the 27 generator/formatter/evaluator tests.
- Canonical counts remain 1,200 trajectories and 1,200 DPO pairs, split 966/234.
  All eight canonical hash, byte and record-count checks pass. An exact-ID and
  content reconciliation of all four consumer partitions/formats found zero
  missing IDs, extra IDs or mismatched formatted records.
- **G3 fixed:** conflicting target representations now raise an error; validation
  and DPO formatting use the same resolver.
- **G4 fixed:** punctuation-only and emoji responses now score zero without
  crashing the evaluation batch.
- **G6 fixed:** canonical `records_count` mismatches and unknown partitions are
  rejected; partition and aggregate totals are checked.
- **G7 fixed within the tested scope:** executing the exact documented Gemma 4
  mapper with Google's current official Jinja template produces the native
  thought channel, preserves reasoning/final text and removes literal thought
  tags. This is an isolated template test, not full trainer execution.
- **G1 attribution clarified:** the guide explicitly identifies the 99.15% score
  as a packaged-reference self-check, not external model inference. Its additional
  claims about what that check proves remain excessive, as detailed below.
- **G5 partially fixed:** a replacement-file move failure after backup completion
  now restores the originals. Failure during backup creation remains destructive.

### H1 — P1: A descriptive sentence is still scored as a perfect recommendation

For synthetic target `badtoken` and alternative `goodtoken`, this response scores
**1.0 / PASS**:

> Слово goodtoken записане на дошці. Учень читає словник, бо його цікавить суфікс.

`v4_evaluate_decolonization.py:82` treats “слово … alternative” as a recommendation;
`:172–173,223–230` then accepts unrelated linguistic keywords and a connective as
elimination and reasoning grounding. The response describes text on a board; it
neither recommends a form nor evaluates the target.

The previous “Оцінки не буде” counterexample now fails, but adding its exact evasion
pattern does not resolve the underlying semantic issue. Preserve heuristic metric
labels and validate recommendation, diagnosis and explanation against independently
adjudicated adverse cases. Do not claim linguistic correctness from these proxies.

### H2 — P2: Backup failure still deletes the original dataset

`v4_format_decolonization.py:442` moves existing files into backup before recording
each successful move. If the first backup move raises `OSError`, the backup list
is empty. The exception handler at `:456–458` nevertheless deletes all original
JSONLs and the original manifest, then has nothing to restore. A synthetic
fault-injection probe confirmed both originals gone and no backup remaining.

Track original and newly published files separately. Cleanup must never delete
an original that was not successfully backed up, and failed restoration must
retain recovery files. Cover faults during backup creation as well as after it;
the latter path now passes its recovery probe.

### H3 — P1: Citation mention is still treated as positive evidence

`v4_decolonization_reasoning.py:541–551` now restricts candidate-level evidence
by checking whether the alternative's spelling appears in the citation. This
fixes borrowing evidence that never mentions that alternative, but not evidence
that mentions it as an example to reject.

A synthetic candidate with alternatives `alpha` and `beta`, positive VESUM counts
and no textbook/dictionary attestations, using the sole citation:

> Do not use alpha. Use beta.

still assigns both alternatives `living_standard` and selects **alpha** as the
primary. Evidence must bind a positive recommendation to its source, not merely
contain the lemma as a substring. Source approval is unchanged; what remains
unverified is the inference made from the approved source.

The generic lexical suppression sentence was replaced, but the other historical
category templates remain in the generator. Target classification is still
unconditional once an alternative passes. Do not describe all target/historical
claims as source-grounded until those specific relations are supported.

### H4 — Evidence limitation: Self-check attribution is fixed, validity claims are not

The guide now correctly says no external model inference produced the score.
However, `decolonization-training-guide.md:308–311` says the self-check mathematically
verifies absence of contradictory or ungrounded reasoning and establishes a
“theoretical upper bound.” A heuristic scoring the generator's own answers cannot
establish those properties; H1 directly demonstrates its semantic blind spot.
Describe it as a reference-answer regression/sanity check with those limitations.

The current exact-head aggregate rerun is still 234 evaluated, 99.57% elimination,
99.57% suggestion, 99.15% grounding/pass, and 0.9932 mean score. The new guide's
claim of 100% elimination and suggestions (`:306`) does not match that result.
All evaluation was performed inside custody and only aggregates were exported.

### Current CI blocker

The PR's CodeQL result is **FAILURE** on this head. Its annotation flags
`tests/projects/open_model_data/test_v4_format_and_evaluate.py:169` for constructing
a Jinja environment with `autoescape=False` and reports one high-severity alert.
This is a chat-template test; the annotation alone is not proof of a production
web XSS vulnerability. It still needs a justified, repository-compliant disposition
and a passing check before merge. Do not mark all CI green while it remains open.

### Evidence and next disposition

Synthetic probes cover H1–H3; existing tests and aggregate artifact reconciliation
cover the confirmed fixes. Native Gemma verification executes the documented mapper
and the official template, with no model weights or full trainer run.
[Official Gemma 4 template](https://huggingface.co/google/gemma-4-31B-it/blob/main/chat_template.jinja).
The template evidence is date-scoped. The 97-seed residual remains recorded.

Resolve the remaining recommendation/evidence semantics and backup-loss path;
correct self-check claims and dispose of the CodeQL alert. Then repeat exact-head
review. No merge or implementation change is authorized by this report.

## Fifth re-review — c64d8956

**VERDICT: FAIL** at `c64d8956ba390cde7d8af4c791ef46d8db33257c` of PR #7933.
The remaining issues are semantic qualification of answers and interpretation of
citation evidence. The previously reproduced output-loss paths are fixed.

### Verified fixes and package checks

- **35 affected tests pass** in 1.20 seconds: 31 generator/formatter/evaluator
  tests plus four contract tests.
- Canonical and consumer counts reconcile to 1,200 trajectories and 1,200 DPO
  pairs, split 966/234. All **16 canonical and consumer hash/byte/count receipts**
  match. The four consumer groups exactly match the current formatter's output
  for their canonical records. Maximum shard size: **1,799,051 bytes**.
- **H2 fixed in the exercised failure paths:** original shard and manifest contents
  survive failure on the first backup move, second backup move, and staged-file
  move. When restoration itself fails, the originals remain in the retained backup.
- **H4 fixed:** the guide now uses the observed metrics and calls the score a
  reference regression/sanity check with explicit pattern-matching limitations;
  the mathematical-proof and theoretical-upper-bound claims are removed.
- The original H1 descriptive sentence now scores zero. The original H3
  “Do not use alpha. Use beta.” citation now rejects alpha. These are real
  improvements; the counterexamples below show why they do not fully establish
  the intended semantic properties.
- Sweeping historical suppression templates have been replaced. This audit does
  not independently validate every replacement grammatical claim.

### I1 — P1: Subject binding still accepts quotation and unrelated reasoning

For target `badtoken` and alternative `goodtoken`, both synthetic responses score
**1.0 / PASS**:

> На дошці написано «Вживайте goodtoken», бо учень переписав словник про суфікс. Це лише цитата з вправи.

> Правильно вживати goodtoken. Учень читає словник, бо його цікавить суфікс.

The first reports an instruction as a quotation rather than endorsing it. The
second makes a recommendation but provides no relevant linguistic reasoning.
At `v4_evaluate_decolonization.py:223–243`, a subject-bearing sentence can satisfy
the binding check with a marker or connective, while the other reasoning markers
are counted elsewhere in the response. The checks do not establish that the
explanation supports the recommendation.

The guide's new proxy disclaimer accurately limits what these scores can prove.
Keep that distinction in release claims: a proxy PASS is not independent semantic
qualification, and H1 cannot be called a general non-answer/grounding fix. Use
independently adjudicated contextual cases for that qualification, rather than
adding only the next exact quotation to the refusal patterns.

### I2 — P1: Negated correctness still promotes the rejected alternative

The new `is_positive_citation` rejects the original imperative counterexample,
but still returns positive support for alpha in this synthetic citation:

> alpha is not correct. beta is correct.

With positive VESUM counts and no other attestation, synthesis marks both
alternatives `living_standard` and selects **alpha** as primary.
`v4_decolonization_reasoning.py:502–553` uses negative and positive regex lists;
the positive “correct” pattern matches the negated assertion that is absent from
the rejection list. The training consequence is a recommendation contrary to its
own citation, not merely a weak evaluation score.

Bind an explicit positive recommendation to its evidence and retain uncertainty
when that relation cannot be established. Extending a blacklist for one phrasing
does not establish the positive evidence relation. No source-collection approval
is being reopened; the defect is the inference made from a supplied citation.

### CodeQL disposition is not yet established by the neutral result

The prior high-severity alert is no longer returned as a failing check. However,
the exact-head CodeQL check is **NEUTRAL**, with “1 configuration not found”:
code scanning says it cannot determine introduced alerts because the default
Python configuration present on main was not found. This is not evidence of a
clean Python security comparison or confirmed alert resolution.

Other CI jobs were still running when checked. Resolve or explain that coverage
warning and verify the completed exact-head results before claiming all CI clear.
The original annotation concerned a non-HTML chat-template test; this report still
does not assert a production XSS vulnerability.

### Disposition and validation boundary

The failure-injection fixes, artifact receipts and corrected reference-check
framing are accepted as progress. Semantic scoring remains a documented proxy,
and the citation counterexample continues to block the claim of verified normative
training labels. The 3/100 seed delivery and 97-seed residual are unchanged.

All counterexamples are synthetic. Real artifact checks exported only aggregates
and equality results from custody. No implementation changes, model execution,
merge or publication occurred during this review.

## Sixth diagnostic re-review — c55474b6

**VERDICT: FAIL** at `c55474b6edc39d231adf406ebc2e8f2e2cdcb273` of PR #7933.
The prior exact counterexamples are fixed. The remaining failure class is the
semantic relation between a statement and the evidence used to support it.

### Scope and verification

This head changes only the generator, evaluator and their two test files relative
to `c64d8956`; the formatter, guide and all canonical/consumer artifacts are
unchanged. Their previously verified receipts and recovery behavior are therefore
not being replaced by untested new implementations in this commit.

- **37 affected tests pass** in 0.93 seconds: the reported 33 tests plus four
  contract tests. Check-only Ruff passes for the affected code and tests.
- The prior attributed quotation scores zero; the prior separate unrelated
  reasoning sentence scores 0.4 and fails.
- The prior “alpha is not correct. beta is correct.” citation now selects beta.
- Previously exercised backup, publication and restoration-failure probes still
  pass. Native Gemma template adaptation still passes the isolated mapper probe.

### J1 — I1 remains: sentence membership is not a supporting explanation

For target `badtoken` and alternative `goodtoken`, this synthetic response scores
**1.0 / PASS**:

> Вживайте goodtoken, бо я прочитав словник і вивчив суфікс.

The response recommends the alternative, but the speaker having read a dictionary
and studied a suffix is not a linguistic reason that supports the recommendation.
The evaluator now restricts keywords/connectives to subject-bearing sentences
(`v4_evaluate_decolonization.py:231–245`), but all those words occur in one sentence
here. It still labels the reasoning grounded without establishing the relationship.

The documented heuristic limitation is appropriate; do not convert this proxy
PASS into a claim of independently grounded reasoning. For semantic qualification,
use evidence that evaluates the explanation's relationship to the answer, not
only sentence co-occurrence. Another exact-string refusal pattern would not
resolve this finding class.

### J2 — I2 remains: ordinary contrastive citations are still misinterpreted

Two synthetic citations show opposite errors in `is_positive_citation`:

| Citation | Observed result | Required interpretation |
| --- | --- | --- |
| Do not ever use alpha. Use beta. | Both positive; alpha selected as primary | Reject alpha; recommend beta |
| Replace alpha with beta. | Both rejected; synthesis returns no trajectory | Reject alpha; recommend beta |

The first bypasses an imperative-negation pattern with an intervening adverb,
while the positive use-pattern still matches. The second exposes the new broad
negative pattern: `replace` followed by arbitrary text also reaches the replacement
itself, so beta is rejected (`v4_decolonization_reasoning.py:515–557`).

Both probes use positive VESUM counts and no other evidence. The first can teach
a recommendation contrary to its own citation; the second drops supported output.
Bind positive and negative evidence to the specific alternative and role. A
negative-pattern blacklist plus a broad positive-pattern list does not establish
that binding.

### Review disposition

This is a recurring failure class across successive patch rounds. The next
remediation should establish the positive-evidence and semantic-qualification
approach, with independently assessed contrastive cases, rather than claim closure
from more examples of the same regex strategy. Implementation remains owned by
the author; this audit neither changes the design nor applies fixes.

The local closeout tool independently resolved PR head/base and recorded the
existing two findings. Its formal reviewer resolver selected Claude Sonnet 5;
Astra was eligible, Gemini was excluded as the author family, and unqualified
multi-model or data-egress routes were excluded. No new selected Claude review
was dispatched for this diagnostic pass. The formal ledger therefore leaves
these findings **UNADJUDICATED**; this report is direct reproduced behavioral
evidence and is not a claim of completed formal merge closeout.

Deterministic checks and synthetic behavior probes are recorded above. This is
source-aware diagnostic testing, not an independently blinded linguistic
assessment. No model training, protected payload export or merge occurred.
The existing 97-seed residual is unchanged. Current CI completion and CodeQL
comparison coverage must still be verified before any merge decision.


## Seventh diagnostic re-review — d26cc384

**VERDICT: FAIL** at `d26cc384e6afa8c5bde8aa3676a108f98dce22c2` of PR #7933.
The exact J1/J2 examples are fixed; the two underlying semantic failure classes
remain reproducible.

### Scope and verification

Only the generator, evaluator and their two test files changed from `c55474b6`.
Artifacts, formatter and guide are unchanged; previous artifact receipts retain
their original scope. No new artifact rebuild or model benchmark was run here.

- **39 tests passed in 1.16 seconds**: 16 generator, 19 formatting/evaluation,
  and four contract tests. The initial command used a nonexistent contract-test
  path and collected nothing; the corrected command below produced this result.
- Check-only Ruff passed for both changed implementation and test files.
- “Replace alpha with beta.” and “Do not ever use alpha. Use beta.” now both
  reject alpha, recommend beta and synthesize beta as primary.
- The previous autobiographical explanation now scores **0.4 / FAIL**.

Tests ran with the project interpreter on the reviewed author worktree:

```text
/home/ops/learn-ukrainian/.venv/bin/python -m pytest \
  tests/projects/open_model_data/test_v4_decolonization_reasoning.py \
  tests/projects/open_model_data/test_v4_format_and_evaluate.py \
  tests/projects/open_model_data/test_v1_decolonization_contracts.py -q
```

### K1 — J2 remains: negated replacement reverses the citation's meaning

The new structural replacement branch returns before clause-level negation is
checked (`v4_decolonization_reasoning.py:516–525`). Both synthetic citations below
return alpha=false, beta=true and synthesize **beta** as primary:

> Do not replace alpha with beta.

> Use alpha. Do not replace alpha with beta.

The second explicitly recommends alpha and prohibits its replacement with beta.
The implementation rejects that recommendation and teaches the prohibited one.
The probe supplies positive VESUM counts for both tokens and no other evidence.
This demonstrates polarity loss in the new role extractor, not missing lexical
attestation. Resolve negation and the complete statement before treating a
structural role match as positive evidence.

### K2 — J1 remains: a relation concerning another word earns perfect grounding

For target `badtoken` and alternative `goodtoken`, this synthetic response scores
**1.0 / PASS**, with `reasoning_grounded=true` and two reasoning hits:

> Вживайте goodtoken, бо у словнику подано пояснення суфікса іншого слова.

The dictionary explanation explicitly concerns another word. It supplies no
linguistic support for the recommended alternative. The evaluator still searches
for relation patterns anywhere in subject-bearing sentences
(`v4_evaluate_decolonization.py:282–301`); it does not bind the relation's subject
or object to the recommendation. The added autobiographical exclusions fix J1's
literal example but do not establish semantic grounding.

These checks are useful heuristics, but their PASS must not be represented as
independent semantic qualification. Both findings recur across patch rounds;
closure requires evidence addressing the failure classes and independently
assessed contrastive cases. Remediation ownership remains with the author; no
implementation or new architecture decision is made by this report.

### CI and limits

At inspection, CI was still running. The same-head CodeQL summary was **neutral**,
with “2 configurations not found”: JavaScript/TypeScript and Python comparison
configurations. It explicitly could not determine alerts introduced by the PR.
That is not evidence of alert clearance; later completion may change the result.

All counterexamples are synthetic and were executed against archived exact-head
code. This is a diagnostic re-review, not a completed formal review ledger or
independently blinded linguistic assessment. The existing 97-seed residual is
unchanged. No protected text, dataset mutation, model execution or merge occurred.


## Eighth diagnostic re-review — 082c5157

**VERDICT: FAIL** at `082c51579942fb00bcae9b7d38741708ab02e354` of PR #7933.
The precise K1/K2 examples are fixed, while both semantic failure classes remain.

### Verified improvements and checks

- **41 focused tests passed in 1.37 seconds**: the reported 37 generator and
  formatting/evaluation tests, plus four contract tests. The command is the same
  three-file pytest invocation recorded in the seventh diagnostic review.
- Ruff check and Ruff format --check passed on all four changed files.
- The author worktree was clean and at the reviewed SHA.
- “Use alpha. Do not replace alpha with beta.” now selects alpha; the bare
  prohibition no longer promotes beta.
- The prior explanation explicitly saying “another word” now scores 0.4 / FAIL.
- Same-head GitHub CI Gate and CodeQL were **SUCCESS**. All listed checks were
  successful or skipped, with none pending or failed. The earlier neutral CodeQL
  warning is therefore superseded for this head.

The delta changes the same two implementation and two test files. It also adjusts
textbook fallback lookup to query lowercase, initial-capital and title-case
variants; artifact files are unchanged. The reported 234-row benchmark self-check
was not rerun in this pass and is not independent semantic validation.

### L1 — K1 remains: comma contrast promotes the explicitly rejected alternative

Synthetic citation:

> Use alpha, not beta.

With positive VESUM counts for both alternatives and no other evidence,
`is_positive_citation` returns **true for both**. Supplying suggestions in order
`[beta, alpha]` synthesizes **beta as primary**, contrary to the citation.
The general positive use-pattern reaches beta across the comma, while the
negative patterns fail to bind “not beta” to that alternative.

Two additional counterexamples expose supported-output loss:

| Citation | Observed result |
| --- | --- |
| Do not use beta, use alpha. | Both rejected; no trajectory |
| alpha — нормативне слово. beta — помилка. | Both rejected; no trajectory |

The first lets negation consume a later positive recommendation. The second
classifies an ordinary Ukrainian predicate dash as an error-to-correction pair
and rejects alpha before reaching its positive status. The new two-pass structure
does not resolve these grammatical roles or negation scope.

### L2 — K2 remains: naming the unrelated word bypasses the exclusion

For synthetic target `badtoken` and alternative `goodtoken`:

> Вживайте goodtoken, бо у словнику подано пояснення суфікса слова «будинок».

Observed: **1.0 / PASS**, `reasoning_grounded=true`, two reasoning hits.
The explanation concerns the named word «будинок», not `goodtoken`. The new
OTHER_ENTITY_PATTERNS detect phrases such as “another word”; they do not bind
the dictionary/morphology relation to the recommended alternative. Replacing
the generic description with an explicit name bypasses that exclusion.
This probe makes no linguistic claim about the named word's actual morphology.

### Disposition and limitations

The tests and CI claims are substantiated. They do not resolve the reproduced
semantic errors. The repeated failure pattern warrants author-owned remediation
of evidence interpretation and evaluation validity, with independently assessed
contrastive cases; another literal example exclusion does not establish closure.

This is exact-head diagnostic evidence, not formal merge closeout or a blinded
linguistic assessment. No new model benchmark, artifact rebuild, protected text
export, implementation change or merge occurred. The existing 97-seed residual
retains its prior scope and owner. Only this audit document changes.


## Ninth diagnostic re-review — 056cd964

**VERDICT: FAIL** at `056cd964e5bda283abf465f9a638b4b3cbf7b82f`.
PR #7933 was already merged at 2026-09-12 09:22:20 UTC when this review began,
as `b2aa7cf7893d77e419bc36914a56956543319d03`. The two implementation and two
test files are identical between the reviewed head and that merge commit.
The remaining evaluator finding therefore applies to the merged implementation.

### Verified fixes and checks

- All three L1 citations now select alpha and reject beta: “Use alpha, not beta.”,
  “Do not use beta, use alpha.”, and the Ukrainian normative/error predicate pair.
  The earlier replacement/negation counterexamples also retain their fixes.
- L2's exact named-word example now scores **0.4 / FAIL**.
- **43 tests passed in 0.69 seconds**: 18 generator, 21 formatting/evaluation,
  and four contracts. Ruff check and Ruff format --check passed on all four files.
- Final PR CI Gate and CodeQL succeeded; all listed checks succeeded or skipped.

Testing used an exact-head archive on the custody host with the project
interpreter, committed scripts, configuration, schemas and seed fixtures. The
three-file pytest invocation is unchanged from the seventh diagnostic review.
A temporary detached review worktree disappeared before test execution; the
cause was not established. Initial partial local-archive attempts encountered
import resolution, absent seed fixtures and Ruff package-discovery differences.
The complete remote archive resolved these harness limitations and produced the
passing results above. No source fix or test weakening was needed.

### M1 — L2 remains: grammatical labels and exemptions bypass subject binding

For synthetic target `badtoken` and alternative `goodtoken`, both responses score
**1.0 / PASS**, with `reasoning_grounded=true` and two reasoning hits:

> Вживайте goodtoken, бо у словнику подано пояснення суфікса іменника «будинок».

> Вживайте goodtoken, бо у словнику подано пояснення суфікса слова «мова».

In each case the dictionary explanation concerns a different named word. The
first replaces the exact phrase “слова «будинок»” with “іменника «будинок»”, which
the new named-entity patterns do not capture. The second is captured, but «мова»
appears in EXEMPT_LINGUISTIC_ENTITIES and is exempted even when it is the word
being analyzed rather than an authority or textbook title.

The failure remains semantic subject binding: sentence-level relation matches
plus entity exclusions still label unrelated support as grounded. These probes
make no claim about the actual morphology of either named word. L1's reproduced
cases are accepted as fixed; M1 is sufficient to withhold semantic-qualification
PASS for the merged evaluator.

### Disposition

The implementation fixes the previous literal examples and passes its tests.
The reproduced residual requires author-owned correction and independent
semantic assessment before the score can serve as evidence of grounded
reasoning. Merge status and green CI do not resolve this observed behavior.

This report records diagnostic evidence only. No merge, rollback, implementation
edit, model execution, new artifact rebuild or protected payload export was
performed. Earlier artifact receipts and the 97-seed residual keep their prior
scope. Formal merge-review compliance was not assessed in this pass.


## Round 11 worktree verification — uncommitted

The operator supplied a subsequent PR #7972 remediation summary. The reported
fix exists as two uncommitted modifications on top of
`5502ffdeb14b80b003189869728e83166bb3d30b`; that SHA is still the published PR
head at inspection. This is a bounded verification of those local modifications,
not a PASS stamp on the unchanged published head or merged main.

**Verified:** all 58 focused tests pass in 1.43 seconds; affected Ruff check and
format check pass. Direct synthetic probes confirm the quoted and unquoted
“варіант форми слова goodtoken” examples score 1.0 / PASS. Paired terminal
subjects будинок, форма and іменник score 0.4 / FAIL. Both M1 examples from the
ninth diagnostic review also score 0.4 / FAIL.

The remote self-check using the held-out file as both gold and predictions
reproduces 234 evaluated records, zero missing/duplicate/unknown predictions,
232 passes, 0.9957 elimination and suggestion rates, 0.9915 grounding and pass
rates, and 0.9932 mean composite score. Only aggregates left custody. This checks
consistency with existing outputs; it is not independent semantic assessment or
a model generalization result.

Verified working-file SHA-256 fingerprints:

| File | SHA-256 |
| --- | --- |
| v4_evaluate_decolonization.py | d0aa77deaf9d8d96224d9bf950421d5e4138fdbf963a5a982ee57ba80a5329e8 |
| test_v4_format_and_evaluate.py | 6985ab699ea784fd1530f916bb08a00991d5c08200ab7b86a6dc40925a7e35f6 |

The described descriptor-chain change resolves the supplied Round 11 reproducer
and preserves rejection of the tested unrelated lexical subjects. No new finding
was raised in this bounded verification. Author-owned commit/push and exact-head
review/CI remain necessary before the published implementation can receive this
result. No author files were edited or committed by this audit.


## Final merged-main verification — 303fbadbd1

**VERDICT: PASS for the bounded delivered-package audit**, verified on
2026-09-12 after fetching `origin/main` inside the assigned audit worktree.
PR #7972 (issue #7932) is merged as
`303fbadbd171e36bf9c5f025a7c61011ca327847`. Its final head is
`faf8ca3764442773ce157634f2185b19731098fe`; the evaluator and its test file
are identical between that head and merged main. The operator supplied the
Astra Round 17 review result, “Verdict: PASS — no new findings”, at that head.
This report attributes that review result to the supplied handoff; it does not
claim a new independent review. Live GitHub verification confirms 16 successful
checks, five skipped checks, and no failed or pending checks on PR #7972.

### Reproduced results

All commands ran inside
`/home/ops/learn-ukrainian/.worktrees/dispatch/codex/uldr-audit-20260911`,
using `/home/ops/learn-ukrainian/.venv/bin/python` as the interpreter after
integrating merged main into the audit branch. Only the audit document differs
from main; no evaluator, generator, test or dataset edits were made.

| Verification | Observed result |
| --- | --- |
| Formatter/evaluator pytest file | 36 passed in 1.00 seconds |
| Generator and contract pytest files | 22 passed in 0.91 seconds |
| Original M1 grammatical-label and generic-word probes | Rejected; not grounded |
| Unrelated lexical subjects and terminal carriers | Rejected, composite score at most 0.40 |
| Period, semicolon, end-of-input, parenthesis, en/em dash and spaced hyphen boundaries | All regression assertions pass |
| Quoted/unquoted valid line-wrapped subjects | Grounded, composite score 1.0 / PASS |
| Line-wrapped terminal carriers followed by a stopword | Not grounded, composite score at most 0.40 / FAIL |
| Expected / evaluated held-out records | 234 / 234 |
| Missing / duplicate / unknown predictions | 0 / 0 / 0 |
| Passing reference records | 232 / 234 (99.15%) |
| Elimination / suggestion rates | 0.9957 / 0.9957 |
| Grounding / pass rates | 0.9915 / 0.9915 |
| Mean composite score | 0.9932 |
| Scoped Ruff check / format check | All checks passed / 4 files already formatted |

Reproduction commands (the benchmark prints aggregates only):

```bash
/home/ops/learn-ukrainian/.venv/bin/python -m pytest tests/projects/open_model_data/test_v4_format_and_evaluate.py -q
/home/ops/learn-ukrainian/.venv/bin/python -m pytest tests/projects/open_model_data/test_v4_decolonization_reasoning.py tests/projects/open_model_data/test_v1_decolonization_contracts.py -q
/home/ops/learn-ukrainian/.venv/bin/python - <<'PYCODE'
import json
from scripts.projects.open_model_data.v4_evaluate_decolonization import (
    DEFAULT_HELD_OUT_FILE, evaluate_predictions,
)
summary = evaluate_predictions(DEFAULT_HELD_OUT_FILE, DEFAULT_HELD_OUT_FILE)
passed = sum(row["is_pass"] for row in summary.pop("evaluations"))
assert (passed, summary["expected_gold_records"]) == (232, 234)
print(json.dumps(dict(summary, passed_records=passed), sort_keys=True))
PYCODE
/home/ops/learn-ukrainian/.venv/bin/python -m ruff check scripts/projects/open_model_data/v4_evaluate_decolonization.py scripts/projects/open_model_data/v4_decolonization_reasoning.py tests/projects/open_model_data/test_v4_format_and_evaluate.py tests/projects/open_model_data/test_v4_decolonization_reasoning.py
/home/ops/learn-ukrainian/.venv/bin/python -m ruff format --check scripts/projects/open_model_data/v4_evaluate_decolonization.py scripts/projects/open_model_data/v4_decolonization_reasoning.py tests/projects/open_model_data/test_v4_format_and_evaluate.py tests/projects/open_model_data/test_v4_decolonization_reasoning.py
```

The benchmark uses the held-out artifact as both gold and predictions, matching
the earlier reference self-check. It proves reference-output consistency and
preserves all 234 records in the denominator; it is not independent semantic
assessment or a model generalization result. Two reference records still fail.
Earlier dataset receipts and consumer verification retain their recorded scope;
no artifact regeneration, model execution or new training run occurred here.
The original 3/100 curated-seed delivery remains a separate 97-seed residual
owned by Gemini. Closure of F1–F7 and M1 does not assert completion of that milestone.

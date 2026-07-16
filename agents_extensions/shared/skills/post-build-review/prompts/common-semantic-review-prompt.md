# Common semantic post-build review prompt

Semantic prompt version: `4.0.0`

Review the resolved built module, not an imagined template. Deterministic facts
and mechanically verifiable track rules are already in the resolved context;
do not re-score them or negotiate them down. Investigate the residual judgments
that code cannot decide.

## Evidence rules

- Read every resolved source file before judging it.
- Cite exact locations and concise evidence for each finding.
- Verify Ukrainian word, stress, morphology, grammar, Russicism, false-friend,
  and calque claims with project source tools. Never infer them from intuition.
- Verify factual, quotation, and attribution claims with the appropriate
  authoritative project sources. Plausible but unattested is not supported.
- Treat missing tools, missing source support, or incomplete review coverage as
  `INCOMPLETE`, not `PASS`.
- Distinguish evidence modalities. Metadata can support catalog facts such as
  title, creator, date label, or performer; it cannot verify what is heard,
  seen, or read in the underlying object. Verify perceptual model answers only
  with direct access through a declared reviewer capability. If the reviewer
  cannot inspect required audio, video, image, text, or interactive evidence,
  record `reviewer_unverified` and return `INCOMPLETE`.
- Inventory every learner task that depends on an external or embedded evidence
  object. The task must give learners usable access to that object or a
  sufficient excerpt/transcript. `metadata_only`, `inaccessible`, and
  `not_provided` require a high or blocker grounding/pedagogy finding; they are
  not acceptable substitutes for the evidence.
- Inspect activities for actual learner behavior: answer correctness,
  distractor validity, task clarity, progression, and whether they test the
  intended language or analysis rather than trivia.
- Inspect pedagogy, plan adherence, coherence, learner register, cognitive
  load, naturalness, engagement, and source-backed density. Do not turn a word
  count or Bilash-specific structure into a universal rule.
- Inspect deterministic paragraph-repetition locations and the marginal
  pedagogical value of authored prose throughout the full size band, not only
  above the advisory ceiling. Repeated framing, conclusions, transitions, or
  definitions require revision even when total length is nominally in range.
- Treat long source-dense material and necessary pedagogy as acceptable.
  Advisory-ceiling excess alone is never a semantic failure.
- Detect internal production workflow on learner surfaces. References to an
  accepted dossier, available package, project corpus, hidden search result,
  source packet, or reviewer process are not source literacy. Treat actual
  workflow leakage as a high pedagogy finding even when the plan asks for
  epistemic humility or source evaluation; plan adherence does not excuse it.

## Required quality-dimension coverage

Assess all five dimensions independently: `pedagogical`, `naturalness`,
`decolonization`, `engagement`, and `tone`. For every dimension, return a
status plus at least one exact learner-surface excerpt and its target-file
location. Do not reuse a generic compliment as evidence across dimensions.
`INCOMPLETE` may omit excerpts only when its finding explains why the evidence
could not be inspected.

## Diagnostic score calibration

For every quality dimension, return the exact raw keys `status`, `score`,
`score_rationale`, `evidence`, and `finding_ids`. Scores are diagnostic evidence
inside this result only: they never set readiness, demote a warning, change the
categorical verdict, or authorize a release. `BLOCK` is this contract's name
for the legacy standing-rule `REJECT`; the quality target remains 9+.

Use these bands exactly: `PASS` `[8.0, 10.0]`, `REVISE` `[6.0, 8.0)`,
`BLOCK` `[0.0, 6.0)`, and `INCOMPLETE` `null`. Use at most one decimal place.
Apply the following anchored rubric within the bands:

- Return `10.0` if and only if that dimension has no findings.
- `9.0`–`9.9` meets the quality target with only bounded, low-severity
  headroom; `8.0`–`8.9` is release-safe but has a more consequential,
  concrete low-severity improvement.
- `7.0`–`7.9` needs one focused material revision while most of the dimension
  remains strong; `6.0`–`6.9` has a substantial material defect that requires
  broader revision.
- `4.0`–`5.9` has a blocking defect despite some usable evidence; `0.0`–`3.9`
  is fundamentally unusable, unsafe, or unsupported for that dimension.
- Every score below `10.0` must link to at least one evidence-backed finding in
  that dimension and its rationale must name the concrete gap to `10.0`.
- Every semantic finding must be referenced by at least one quality dimension,
  contradicted/imprecise/unattested claim, or non-verified learner-evidence
  entry. A `10.0` attests that the dimension has no linked finding; it never
  erases a separately owned claim or learner-evidence finding from the result.
- A Russianism, calque, or fabrication-class finding for a dimension caps that
  dimension at `6.0`. The current finding structure has no stable hard-class
  field, so this cap is a reviewer contract exercised by calibration fixtures;
  never evade it by reclassifying or omitting the finding.
- Scores are comparable only when `(semantic_prompt_version, reviewer.family,
  reviewer.model, reviewer.effort)` is identical. Never compare, average, rank,
  or aggregate scores across a different tuple.

`score` is a JSON number for `PASS`, `REVISE`, or `BLOCK`, and `null` if and
only if the status is `INCOMPLETE`. `score_rationale` is a non-empty string for
numeric scores and `null` if and only if the status is `INCOMPLETE`.

Before returning, mechanically search every quality-dimension `excerpt` in its
referenced target file. Each excerpt must be one contiguous, byte-for-byte
substring; never splice fragments, normalize punctuation, or add an ellipsis.

Use stable uppercase-underscore `issue_id` values for semantic findings.
Known calibration classes include `ENGLISH_LEAKAGE`,
`AWKWARD_PASSIVE_RESULT_STATE`, `UNNATURAL_ANTHROPOMORPHISM`,
`UKRAINIAN_GRAMMAR_CALQUE`, `AI_LEAKAGE`, `PATH_LEAKAGE`,
`INTERNAL_LEAKAGE`, and `SEMINAR_REGISTER_PATHOS`. Preserve those names when
applicable; create a precise new class instead of forcing an unrelated one.
Calibration canaries test route and prompt behavior separately; never inject
canary snippets into a real module review.

## Severity and verdict

Use only `blocker`, `high`, `medium`, `low`, or `info`.

- `blocker`: false teaching, fabricated/contradicted fact, unsafe rights or
  provenance failure, or a defect that makes the module unshippable.
- `high`: material correction required before readiness.
- `medium`: actionable quality defect requiring revision.
- `low`/`info`: non-blocking polish or observation.

Verdicts are `PASS`, `REVISE`, `BLOCK`, or `INCOMPLETE`. `PASS` permits only
low/info findings and complete required coverage.

## Semantic result shape

Return exactly one JSON object and no Markdown wrapper, preface, duplicate
object, or trailing commentary. The orchestrator hashes and parses the exact
response bytes. It must not repair, merge, reconcile, or normalize this output.
The first non-whitespace response byte must be `{` and the last must be `}`.
Do not narrate source checks, reasoning, or the verdict outside that object.
Recount both ledgers after the object is complete: every declared total must
equal the corresponding array length and every checked/supported count must
equal the statuses actually present in that array.

```json
{
  "verdict": "PASS|REVISE|BLOCK|INCOMPLETE",
  "summary": "concise evidence-backed summary",
  "quality_dimensions": {
    "pedagogical": {
      "status": "PASS|REVISE|BLOCK|INCOMPLETE",
      "score": 10.0,
      "score_rationale": "No pedagogical finding identifies a gap to 10.0.",
      "evidence": [
        {
          "location": "repo-relative target file and locator",
          "excerpt": "exact learner-surface excerpt"
        }
      ],
      "finding_ids": []
    },
    "naturalness": {
      "status": "PASS|REVISE|BLOCK|INCOMPLETE",
      "score": 10.0,
      "score_rationale": "No naturalness finding identifies a gap to 10.0.",
      "evidence": [{"location": "path:locator", "excerpt": "exact excerpt"}],
      "finding_ids": []
    },
    "decolonization": {
      "status": "PASS|REVISE|BLOCK|INCOMPLETE",
      "score": 10.0,
      "score_rationale": "No decolonization finding identifies a gap to 10.0.",
      "evidence": [{"location": "path:locator", "excerpt": "exact excerpt"}],
      "finding_ids": []
    },
    "engagement": {
      "status": "PASS|REVISE|BLOCK|INCOMPLETE",
      "score": 10.0,
      "score_rationale": "No engagement finding identifies a gap to 10.0.",
      "evidence": [{"location": "path:locator", "excerpt": "exact excerpt"}],
      "finding_ids": []
    },
    "tone": {
      "status": "PASS|REVISE|BLOCK|INCOMPLETE",
      "score": 10.0,
      "score_rationale": "No tone finding identifies a gap to 10.0.",
      "evidence": [{"location": "path:locator", "excerpt": "exact excerpt"}],
      "finding_ids": []
    }
  },
  "claim_coverage": {
    "status": "complete|incomplete|not_applicable",
    "claims_total": 0,
    "claims_checked": 0,
    "claims_supported": 0
  },
  "claim_ledger": [
    {
      "id": "stable-atomic-claim-id",
      "claim": "one checkable claim",
      "location": "repo-relative path and locator",
      "status": "supported|contradicted|imprecise|unattested|unverifiable",
      "evidence": "attributable source/tool evidence or why it is unverifiable",
      "finding_id": null
    }
  ],
  "learner_evidence_ledger": [
    {
      "id": "stable-evidence-object-id",
      "location": "repo-relative task/model-answer locator",
      "task": "what the learner must inspect",
      "modality": "text|audio|video|image|interactive",
      "source": "provided object, excerpt, transcript, or URL",
      "access_status": "verified_access|metadata_only|inaccessible|not_provided|reviewer_unverified",
      "verification_method": "how access and relevant content were checked",
      "finding_id": null
    }
  ],
  "findings": [
    {
      "id": "stable-kebab-id",
      "issue_id": "STABLE_UPPERCASE_ISSUE_CLASS",
      "category": "pedagogy|language|activity|factuality|grounding|decolonization|engagement|tone|rights|size|other",
      "severity": "blocker|high|medium|low|info",
      "message": "what is wrong and why it matters",
      "evidence": "exact text plus source/tool support",
      "location": "repo-relative path and locator"
    }
  ]
}
```

Counts must be derived from `claim_ledger`: total equals its length, checked
excludes only `unverifiable`, and supported counts only `supported`. IDs are
unique. Every non-supported claim and every learner-evidence entry other than
`verified_access` references a finding. `PASS` requires complete coverage and
only supported claims.

Every quality-dimension `finding_id` must reference a semantic finding. A
dimension marked `REVISE` requires a medium/high finding, `BLOCK` requires a
blocker, and `PASS` cannot reference a material finding. The overall verdict
must fail closed when any dimension is not `PASS`. Do not repair, clamp,
downgrade, round, reconcile, or otherwise change a score to fit a band.
Do not emit an orphan semantic finding: every finding must be owned by a
dimension, claim-ledger entry, or learner-evidence-ledger entry.

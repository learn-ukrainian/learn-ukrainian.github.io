# Common semantic post-build review prompt

Semantic prompt version: `1.1.0`

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

Return one JSON object and no Markdown wrapper:

```json
{
  "verdict": "PASS|REVISE|BLOCK|INCOMPLETE",
  "summary": "concise evidence-backed summary",
  "claim_coverage": {
    "status": "complete|incomplete|not_applicable",
    "claims_total": 0,
    "claims_verified": 0
  },
  "findings": [
    {
      "id": "stable-kebab-id",
      "category": "pedagogy|language|activity|factuality|grounding|decolonization|rights|size|other",
      "severity": "blocker|high|medium|low|info",
      "message": "what is wrong and why it matters",
      "evidence": "exact text plus source/tool support",
      "location": "repo-relative path and locator"
    }
  ]
}
```

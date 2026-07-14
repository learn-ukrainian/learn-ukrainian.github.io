---
name: post-build-review
description: Run the canonical read-only, versioned review of a built Ukrainian curriculum module by composing deterministic audit evidence, track policy, the correct core or seminar semantic prompt, and fail-closed combined disposition. Use for short requests such as "Use $post-build-review for bio/oleksandr-bilash", for post-build quality gates, for reproducing a prior versioned review, or before declaring a module ready.
---

# Post-build review

Keep all repository files unchanged. Write packets and results only under `/tmp`.
Do not create curriculum `audit/`, `review/`, `status/`, telemetry, or published
artifacts. Report findings; do not fix the module during this invocation.

## Workflow

1. Parse the argument as `track/slug`. Do not infer an unknown track.
2. Record the current reviewer agent, model family, exact model id, effort, and
   every evidence modality it can directly inspect: `text`, `audio`, `video`,
   `image`, or `interactive`. Do not declare a capability merely because page
   metadata is readable.
3. Allocate one invocation-scoped run directory. Copy the emitted paths exactly
   and use them only for this review. Never reuse another review's run directory
   or fall back to global `/tmp/post-build-review-*.json` names:

   ```bash
   .venv/bin/python scripts/audit/post_build_review.py allocate <track/slug>
   ```

4. Run deterministic preparation with the emitted `packet` path:

   ```bash
   .venv/bin/python scripts/audit/post_build_review.py prepare \
     <track/slug> \
     --reviewer-agent <agent> \
     --reviewer-family <family> \
     --reviewer-model <model> \
     --reviewer-effort <effort> \
     --reviewer-capability text \
     --output <packet_path>
   ```

5. Read `<packet_path>`. Follow its `semantic_prompt`
   exactly. Read every path in `target.files`; use the project source tools for
   Ukrainian, factual, attribution, and quotation claims. Never guess a
   Ukrainian fact. If required tools or evidence are unavailable, return
   `INCOMPLETE`.
6. Preserve the reviewer's exact response bytes at the emitted
   `<semantic_response_path>`. Do not extract, repair,
   normalize, merge, or reconcile malformed output. A malformed response ends
   this review as `INCOMPLETE`; any retry is a distinct review with a new
   packet/result and cannot replace the failed artifact. Allocate a new run
   directory before every retry. Use `apply_patch`, not a shell heredoc, when
   the current agent is the reviewer.
7. Finalize and validate using paths from the same allocated run directory:

   ```bash
   .venv/bin/python scripts/audit/post_build_review.py finalize \
     --packet <packet_path> \
     --semantic-response <semantic_response_path> \
     --output <result_path>
   ```

8. Read the result back, report the combined disposition and material findings,
   and cite `<result_path>`. A non-zero finalize exit means
   `BLOCK`, `REVISE`, or `INCOMPLETE`; it is a review outcome, not a tool crash.
9. Verify `git status --short` is unchanged from before the invocation.

## Canonical resources

- Deterministic contract: [contracts/deterministic-audit-contract.md](contracts/deterministic-audit-contract.md)
- Disposition policy: [contracts/combined-disposition-policy.md](contracts/combined-disposition-policy.md)
- Size policy: [contracts/evidence-derived-size-policy-contract.md](contracts/evidence-derived-size-policy-contract.md)
- Track configuration: [config/track-policy.v1.yaml](config/track-policy.v1.yaml)
- Current output schema: [schema/review-result.v2.schema.json](schema/review-result.v2.schema.json)
- Historical v1 schema: [schema/review-result.v1.schema.json](schema/review-result.v1.schema.json)

The runner assembles the common prompt plus exactly one family prompt. Do not
manually concatenate or substitute other review prompts.

## Safety and maintenance

- Never use `scripts/audit_module.py`, `scripts/audit_module.sh`, `--output` on
  the track audit, or `--run-mdx-generation-validate`; those paths may write to
  the repository.
- Never let semantic `PASS` override a deterministic blocker/high finding.
- Never infer audio, video, image, text, or interactive content from metadata.
  If the reviewer cannot inspect evidence required by a learner task, record it
  as `reviewer_unverified` and return `INCOMPLETE`.
- Never reuse a result after any `source_hashes` value changes.
- Maintain this skill only through the bug-fix workflow in
  `docs/runbooks/post-build-review.md`; bump the responsible version and deploy
  mirrors from this canonical directory.

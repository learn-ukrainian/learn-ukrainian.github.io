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
2. Record the current reviewer agent, model family, exact model id, and effort.
3. Run deterministic preparation:

   ```bash
   .venv/bin/python scripts/audit/post_build_review.py prepare \
     <track/slug> \
     --reviewer-agent <agent> \
     --reviewer-family <family> \
     --reviewer-model <model> \
     --reviewer-effort <effort> \
     --output /tmp/post-build-review-packet.json
   ```

4. Read `/tmp/post-build-review-packet.json`. Follow its `semantic_prompt`
   exactly. Read every path in `target.files`; use the project source tools for
   Ukrainian, factual, attribution, and quotation claims. Never guess a
   Ukrainian fact. If required tools or evidence are unavailable, return
   `INCOMPLETE`.
5. Create `/tmp/post-build-review-semantic.json` with the shape required at the
   end of the effective prompt. Use `apply_patch`, not a shell heredoc.
6. Finalize and validate:

   ```bash
   .venv/bin/python scripts/audit/post_build_review.py finalize \
     --packet /tmp/post-build-review-packet.json \
     --semantic-result /tmp/post-build-review-semantic.json \
     --output /tmp/post-build-review-result.json
   ```

7. Read the result back, report the combined disposition and material findings,
   and cite `/tmp/post-build-review-result.json`. A non-zero finalize exit means
   `BLOCK`, `REVISE`, or `INCOMPLETE`; it is a review outcome, not a tool crash.
8. Verify `git status --short` is unchanged from before the invocation.

## Canonical resources

- Deterministic contract: [contracts/deterministic-audit-contract.md](contracts/deterministic-audit-contract.md)
- Disposition policy: [contracts/combined-disposition-policy.md](contracts/combined-disposition-policy.md)
- Size policy: [contracts/evidence-derived-size-policy-contract.md](contracts/evidence-derived-size-policy-contract.md)
- Track configuration: [config/track-policy.v1.yaml](config/track-policy.v1.yaml)
- Output schema: [schema/review-result.v1.schema.json](schema/review-result.v1.schema.json)

The runner assembles the common prompt plus exactly one family prompt. Do not
manually concatenate or substitute other review prompts.

## Safety and maintenance

- Never use `scripts/audit_module.py`, `scripts/audit_module.sh`, `--output` on
  the track audit, or `--run-mdx-generation-validate`; those paths may write to
  the repository.
- Never let semantic `PASS` override a deterministic blocker/high finding.
- Never reuse a result after any `source_hashes` value changes.
- Maintain this skill only through the bug-fix workflow in
  `docs/runbooks/post-build-review.md`; bump the responsible version and deploy
  mirrors from this canonical directory.

---
name: pr-comments
description: Post an agent-authored comment or reply on GitHub safely and with honest attribution. Use before any PR or issue comment, review reply or written dismissal of a finding.
---

# PR comments

A pointer skill. The rules that govern public text are in
`docs/dev/agent-public-text.md` (the typed publisher) and rules core P8 (operational
security). This file adds only the order of operations; it is not a second copy of them.

## Every agent comment

1. **Attribution first line**: the verified model and harness that wrote the comment, as the
   harness reports them. If the model is not exposed, name the harness only. Never guess, and
   never call AI review human review.
2. **Lead with the conclusion**, then cite the evidence: file:line with repository-relative
   paths, a check, a run id or a reproduction. Keep verified facts apart from judgement. No
   filler, thanks or status narration.
3. **OPSEC check before posting**: no host paths, server or deployment details, credentials,
   private transcripts or the operator's words (rules core P8). The publisher scans every field
   and refuses a match.
4. **Post through the publisher**, never raw `gh` writes:

   ```bash
   .venv/bin/python -m scripts.publish pr-comment --number "$PR" --body-file "$BODY"
   .venv/bin/python -m scripts.publish issue-comment --number "$ISSUE" --body-file "$BODY"
   ```

5. **Verify the result**: the command exited 0, and the comment is visible
   (`gh pr view "$PR" --comments`).
6. **Resolve a review thread only after the reply was posted successfully.** The publisher has
   no thread-resolution verb; resolve it in the GitHub UI or leave it for the PR owner.

## Not covered here

- The review of record is published by `record_cf_verdict` (`review-loop`), not as a comment.
- PR titles and bodies: `full-send` [pr-body](../full-send/references/pr-body.md).
- Do not post a comment nobody needs; a PR comment is not a status report.

Learned from tstack's `leaving-pr-comments` skill (MIT, Theo Browne); the text is our own.

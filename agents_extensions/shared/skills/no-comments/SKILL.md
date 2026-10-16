---
name: no-comments
description: Remove comments that do not earn their place, using a short keep-list.
  Use for /no-comments.
---

# No comments

Apply this to the diff you own. Do not spawn a subagent.

Delete narration, banners, commented-out code, and comments that restate the next line. Keep only:

- A license header.
- A non-obvious constraint forced by a dependency, protocol, or tool that this code cannot change.
- A public-API contract the type cannot express.
- An issue link that records a constraint the code cannot encode.
- A lint suppression whose rule is style-only or itself faulty. A suppression that hides a real bug goes, and the bug is fixed (`principle-fix-root-causes`).

When a comment exists because the code is surprising, fix the code if the brief owns that fix. Do not rewrite a comment into a shorter excuse. Do not delete tests. Uncertainty about a keep-clause means the comment goes only when you have read the surrounding code and it is not on the list above.

Adapted from pstack. Source provenance and license (repository-relative):
`agents_extensions/shared/skills/pstack-provenance.md`.

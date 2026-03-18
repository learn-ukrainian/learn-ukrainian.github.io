===REVIEW_START===

Fixed 2 violations (both targeting the same `## Vocabulary` header):

1. **[HEADING_LEVEL]** — `## Vocabulary` used H2 but spec requires H1 → removed entirely
2. **[FORBIDDEN_HEADER]** — `## Vocabulary` is auto-injected from `vocabulary/greetings-and-politeness.yaml` at build time → removed

The `## Vocabulary` line at the end of the file was deleted. The `# Activities` header remains as the final section marker.

===REVIEW_END===
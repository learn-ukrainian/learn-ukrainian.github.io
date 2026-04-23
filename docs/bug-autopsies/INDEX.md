# Bug Autopsy Index

One-liner per bug. Grep for symptoms or categories to find relevant detail files.

| Date | Issue | Category | Summary |
|------|-------|----------|---------|
| 2026-04-05 | #1150 | score-parsing | Wiki review loop stuck at 8/10 — regex `(\d+)` can't match decimal scores like `8.8/10` |
| 2026-04-08 | — | mdx-parse | `re.sub` unescapes `\n` in JSX replacement strings → acorn parse failure on 39 A2 MDX files |
| 2026-04-08 | — | mdx-parse | Missing blank lines before HTML blocks → MDX parses `<div>` as inline, breaks `<TabItem>` nesting |
| 2026-04-08 | — | mdx-parse | LLM writer artifacts (stray ` ``` `, `<!-- -->`, bare `<br>`) break MDX parser |
| 2026-04-23 | #1431 | prompt-sync | Writer vs reviewer calibration drift on immersion/engagement/dialogue/plan — fixed via shared contract `scripts/build/contracts/module-contract.md` referenced by both sides |

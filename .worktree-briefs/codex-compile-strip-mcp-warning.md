# Defensive: strip gemini MCP-warning leak from compile.py output

## Problem

Tonight a B2 wiki compile produced an article whose first line was:

    MCP issues detected. Run /mcp list for status.# Граматика B2: Академічне письмо

Root cause: the MCP sources server was down, gemini-cli printed an
MCP-connection warning to stdout, and compile.py captured that stdout
as the article content — concatenating the warning directly into the
`.md` file (before the `#` title and with no newline separator).

Also saw a secondary bug — two duplicate `generated_by_model:
gemini-3.1-pro-preview` lines in the frontmatter.

Sources MCP has since been brought up, so the immediate cause is
resolved. But if MCP flickers mid-batch (lost sockets, restart during
a long run, dns hiccup), the same corruption will reappear silently.

## Fix

In `scripts/wiki/compile.py` (and/or `compiler.py` — find where gemini
stdout becomes article bytes):

1. **Strip MCP-warning lines** from gemini stdout before writing to
   the article file. Match pattern: lines matching
   `MCP issues detected\. Run /mcp list for status\.` anywhere, plus
   stripping any leading whitespace they introduce. Logically filter
   by line, not substring, so article content containing the phrase
   (unlikely) isn't accidentally mangled.
2. **Dedupe `generated_by_model:` entries** in the frontmatter comment
   block. If the same key appears twice, keep the first, drop the
   second. (Probably caused by wiki-meta template concatenating into
   an upstream-provided block that already has the key.)
3. **Add a warning-to-stderr path**: if ANY known-noise line is
   stripped from gemini stdout, emit a warning to stderr (not the
   article) so the human operator sees `⚠️  stripped MCP-warning line
   from {slug}` and can investigate.

## Acceptance criteria

- [ ] Unit test: feed a fixture string containing the MCP warning line
      plus the article body; assert output file is clean.
- [ ] Unit test: feed a fixture with duplicate `generated_by_model:`
      keys; assert output has one.
- [ ] Unit test: feed clean gemini output; assert no changes made.
- [ ] Integration: recompile `wiki/grammar/b2/academic-writing.md`
      with `--force` on a temp shard (fake MCP warning stream) and
      verify the output is as expected.
- [ ] No regressions: `pytest tests/test_wiki_compile*` green.

## Worktree

```
git worktree add -b codex/compile-strip-mcp-warning .worktrees/codex-compile-strip-mcp-warning
cd .worktrees/codex-compile-strip-mcp-warning
# work, commit, push, PR. Do NOT auto-merge.
```

## Hard timeout

2700s (45m). Small task.

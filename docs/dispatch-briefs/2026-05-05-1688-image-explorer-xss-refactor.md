# Codex dispatch — #1688 image-explorer playground XSS refactor

## Context

PR #1688 (`gemini/codeql-D-js-html-xss`) is DRAFT and Codex's previous review caught a real XSS hole that the original Gemini fix missed. Per session handoff:

> Codex caught real XSS still open at `playgrounds/image-explorer.html` lines 913-934 + 795-796 — image paths/IDs/metadata/tags still render through `innerHTML`/`insertAdjacentHTML`; only `hit.text` was escaped. The XSS class is NOT closed.

The previous Gemini commit only escaped `hit.text`. The remaining vectors:
- Image paths
- IDs
- Metadata fields
- Tags

All still render through `innerHTML` / `insertAdjacentHTML` — these need refactoring to `createElement` + `textContent` + `setAttribute`.

## Worktree (existing)

Worktree already exists at `.worktrees/dispatch/gemini/codeql-D-js-html-xss` on branch `gemini/codeql-D-js-html-xss` at commit `b62d688dd6`.

Same situation as #1687 — pre-created worktree on gemini branch. Dispatch will use `--agent gemini --task-id codeql-D-js-html-xss` to match. The brief instructs whoever runs it.

## Numbered steps

1. **Verify branch base.** Inside worktree: `git fetch origin main && git log --oneline HEAD..origin/main`. If non-empty: `git rebase origin/main && git push --force-with-lease`.

2. **Read `playgrounds/image-explorer.html` lines 750-1000** in full. Capture:
   - Every `innerHTML =` assignment
   - Every `insertAdjacentHTML(` call
   - The shape of the data object (image, hit, metadata, tags) being injected

3. **Inventory the user-controlled fields.** Anything that traces back to:
   - Search input
   - Image metadata (filename, alt, tags, description)
   - URL parameters
   - localStorage / IndexedDB content

   Each is a potential XSS vector if rendered through `innerHTML`.

4. **Refactor to safe DOM manipulation.** Pattern:

   ```javascript
   // BEFORE (unsafe)
   container.innerHTML = `
     <img src="${hit.path}" alt="${hit.alt}">
     <div class="meta">${hit.metadata}</div>
     <div class="tags">${hit.tags.join(', ')}</div>
   `;

   // AFTER (safe)
   const img = document.createElement('img');
   img.src = hit.path;        // src setter — browsers handle javascript: URLs in modern Chrome but still validate
   img.alt = hit.alt;         // alt is a DOM property — auto-escaped
   container.appendChild(img);

   const meta = document.createElement('div');
   meta.className = 'meta';
   meta.textContent = hit.metadata;  // textContent prevents HTML injection
   container.appendChild(meta);

   const tags = document.createElement('div');
   tags.className = 'tags';
   tags.textContent = hit.tags.join(', ');
   container.appendChild(tags);
   ```

   Key rules:
   - **Use `textContent`, not `innerHTML`,** for any string field
   - **Use `setAttribute(name, value)` or property setter,** not template literal in HTML string, for attributes
   - **Validate URLs** before assigning to `src` / `href`: reject anything starting with `javascript:`, `data:` (unless explicitly allowed for legitimate data-URIs)
   - **For tag lists,** create one element per tag rather than a joined string if hover/click handlers are needed; else `textContent.join(', ')` is fine
   - **Use `createDocumentFragment`** to batch element creation when appending many nodes

5. **URL validation helper.** Add (or extend) a helper:
   ```javascript
   function safeSrc(url) {
     try {
       const parsed = new URL(url, window.location.origin);
       if (!['http:', 'https:', 'data:'].includes(parsed.protocol)) return '';
       // Optionally restrict data: to image MIME types
       if (parsed.protocol === 'data:' && !parsed.pathname.startsWith('image/')) return '';
       return parsed.toString();
     } catch {
       return '';
     }
   }
   ```

6. **Verify all CodeQL alerts in #1688 are addressed.**
   ```bash
   gh api 'repos/learn-ukrainian/learn-ukrainian.github.io/code-scanning/alerts?ref=refs/pull/1688/head&state=open' --jq '.[] | {rule: .rule.id, file: .most_recent_instance.location.path, line: .most_recent_instance.location.start_line}'
   ```
   Cross-check each alert site against your refactor.

7. **Manual smoke test.** Open `playgrounds/image-explorer.html` in Chrome (file:// or via a local server). Search for a known image. Verify:
   - Images render
   - Metadata renders as plain text (no clickable HTML elements injected)
   - Tags render as plain text
   - No console errors

8. **Add a regression test** if the playgrounds dir has existing JS tests. Otherwise document the manual test in a comment near the refactored code.

9. **Run vitest** (frontend tests): `cd <frontend-dir> && npm test 2>&1 | tail -30` — verify nothing else regressed.

10. **Commit.**
    ```
    fix(security): refactor image-explorer playground from innerHTML to safe DOM (#1688)
    ```
    Body explains:
    - Number of `innerHTML`/`insertAdjacentHTML` sites refactored
    - Fields now using `textContent` / `setAttribute`
    - URL validation helper added
    - Manual test result

11. **Push:** `git push origin gemini/codeql-D-js-html-xss`

12. **Update PR (it's DRAFT, ready to mark ready when CI clears):**
    ```bash
    gh pr comment 1688 --body "Refactored to safe DOM manipulation per Codex review. innerHTML/insertAdjacentHTML eliminated for user-controlled fields. URL validation added. Manual smoke test green. cc @user"
    ```
    Do NOT mark ready or merge — wait for cross-review.

13. **Do NOT enable auto-merge.**

## Acceptance criteria

- All user-controlled fields render via `textContent` / `setAttribute` / property setter, NOT `innerHTML`
- URL validation prevents `javascript:` injection
- All open CodeQL alerts on PR #1688 close (`gh api ... alerts state=open` returns empty for this PR)
- Manual smoke test green
- vitest green
- Commit references #1688

## Discipline

- **Read the file first** — memory rule "I already know how it works" is wrong
- **Don't break legitimate functionality** — image rendering, search, hover effects must continue to work
- **No `--no-verify`**
- Reference #1688 in commit + PR comment

## Related

- Predecessor session handoff: `docs/session-state/2026-05-05-codeql-cleanup-and-adr008-resolution.md` (lines 38-42 documenting the Codex catch)
- Predecessor brief: `docs/dispatch-briefs/2026-05-05-codeql-D-js-html-xss.md` (the original Gemini brief that only escaped `hit.text`)

# Secret Leakage

Bugs where Claude (or any agent) accidentally prints, commits, or otherwise
exposes secrets (API keys, tokens, credentials, private content).

This is an autopsy category, not a single bug. Add new entries chronologically.

---

## 2026-05-10 — `GEMINI_API_KEY` printed during graphify-install diagnostic

### Symptom

User asked Claude to verify that `.bash_secrets` was properly comment-out so
graphify would fall through to the OAuth subagent path. Claude ran a diagnostic
to find where `GEMINI_API_KEY` was set across shell startup files. The
diagnostic's `grep -nH "GEMINI_API_KEY"` printed matched lines verbatim — for
`.bash_secrets:3`, that included the literal API key value (`AIzaSy...`).

The key was now in:
- The conversation transcript (visible to user, stored locally and possibly
  uploaded to Anthropic depending on settings)
- The local Claude Code session log (`~/.claude/projects/.../`)
- Any session backups, transcript caches, or telemetry

User had to rotate the key in Google AI Studio.

### Root cause

The diagnostic command had **inconsistent sanitization**:

```bash
# This part redacted properly:
env | grep -E "GEMINI|GOOGLE" | sed 's/=.*/=<REDACTED>/'

# This part DID NOT redact:
matches=$(grep -nH "GEMINI_API_KEY\|GOOGLE_API_KEY" "$full" 2>/dev/null);
echo "$matches"   # full line printed, including the value after =
```

Claude knew about redaction (applied it to one branch of the same command) but
forgot to apply it to the other. Inconsistent sanitization is the failure mode
— the lesson "always redact secrets" is too coarse; the actual rule needs to be
**every command path that touches a secrets file must be wrapped in a redactor
before stdout is reached**.

### Why grep is dangerous

When grepping a file by KEY NAME (`GEMINI_API_KEY`), the matched line by
definition contains the value (`KEY=value`). Unlike grepping by VALUE
prefix (where the leak is the user's own input), grepping by name guarantees
the value gets pulled into stdout unless explicitly stripped.

### Prevention

#### Hard rule (added to MEMORY.md)

> When grepping `.bash_secrets` / `.envrc` / `.env*` / `~/.aws/credentials`
> / any credential file: **never print the matched line directly**. Always
> wrap with `cut -d= -f1` (key only) or `sed 's/=.*/=<REDACTED>/'` (value
> redacted). The "I'll just look at it real quick" pattern always leaks.
> If you only need to know whether the variable is SET, use
> `if [ -n "${VAR:-}" ]` in a fresh-env subshell — never grep the file.

#### Decision tree for "is variable X set?"

| Need | Safe command |
|---|---|
| Just whether it's set | `env -i bash -c 'source ~/.bash_secrets; [ -n "${VAR:-}" ] && echo SET \|\| echo UNSET'` |
| Which file sets it | `grep -l "VAR_NAME" ~/.bash_secrets ~/.bashrc ~/.zshrc 2>/dev/null` (filenames only, `-l` flag) |
| Line number where it's set | `grep -n "VAR_NAME" file \| cut -d= -f1` (drops value) |
| Whether it's commented out | `grep -n "^[[:space:]]*#.*VAR_NAME" file \| cut -d= -f1` |

#### Sibling check

Searched the codebase for any scripts/tools that grep secrets without
redaction. None found in committed scripts (only in agent ad-hoc commands,
which is exactly the failure path here). The fix is a behavioral rule
enforced by Claude's training/memory, not a code change.

### Links

- This autopsy: `docs/bug-autopsies/secret-leakage.md`
- INDEX entry: `docs/bug-autopsies/INDEX.md` (2026-05-10)
- Critical rules: `claude_extensions/rules/critical-rules.md` (rule 4 — no
  direct API keys, OAuth via gemini-cli only — supports the broader posture)
- MEMORY rule: see `memory/MEMORY.md` "secret-handling" section

---

## 2026-05-12 — `DAGGER_CLOUD_TOKEN` printed during Dagger probe

### Symptom

While investigating local Dagger setup, Claude ran an environment probe to
check if `DAGGER_CLOUD_TOKEN` was set (left over from a prior kaizen-project
session). The probe used `env | grep -i DAGGER | grep -v -i secret | head -5`
intending to filter sensitive lines. The token value (`dag_graphtrek_...`)
was printed verbatim to stdout. User flagged the leak and confirmed the token
was probably expired and they don't use Dagger Cloud, but the principle stood
— another credential ended up in the transcript.

### Root cause

The filter `grep -v -i secret` only excludes lines containing the literal
substring "secret". Token variables like `DAGGER_CLOUD_TOKEN`, `API_KEY`,
`*_PAT`, etc. do **not** contain the word "secret" in their name. The filter
was theatrically safety-coded but functionally a no-op for this variable
class.

This is the **same failure mode as 2026-05-10** (inconsistent / shallow
sanitization) — recurrence proves the 2026-05-10 lesson didn't generalize.
The 2026-05-10 fix focused on grepping FILES; this incident shows the same
trap applies to grepping the LIVE ENV.

### Why naive filters fail

The previous incident's MEMORY rule said "never print matched lines
verbatim" for grep on credential FILES. It did not extend to:

- `env | grep <prefix>` (live process env)
- `printenv VARNAME` (one-shot lookup)
- `set | grep <prefix>` (shell builtins + env)
- `cat /proc/$$/environ | tr '\0' '\n'` (raw env dump)

All of these will leak credentials whose **NAME doesn't contain the word
"secret"**, "token", or "key" — and most don't.

### Prevention

#### Generalized rule (extends MEMORY.md #M-5)

> Any command that reads credential-bearing state — including the LIVE
> ENV, not just files — must be wrapped in a value-stripper BEFORE
> stdout. `grep -v -i secret` / `grep -v password` filters are
> **insufficient** because they only catch substring matches in variable
> names. Real-world credential variables are named `DAGGER_CLOUD_TOKEN`,
> `GEMINI_API_KEY`, `ANTHROPIC_KEY`, `GH_TOKEN`, `*_PAT`, `*_AUTH`, etc.
> — none contain the word "secret".

#### Decision tree for "is env var X set?" (revised)

| Need | Safe command |
|---|---|
| Just whether it's set (env) | `[ -n "${X:-}" ] && echo SET \|\| echo UNSET` |
| List which env vars match a prefix | `env \| cut -d= -f1 \| grep -i "^DAGGER"` (keys only, value never read) |
| Sanitized env dump for a prefix | `env \| grep -i "^DAGGER" \| sed 's/=.*/=<REDACTED>/'` |
| Just whether it's set (file) | `env -i bash -c 'source ~/.bash_secrets; [ -n "${X:-}" ] && echo SET \|\| echo UNSET'` |

**The cut-keys-only pattern is the safest default.** If you only need to
know names, never read values.

#### Sibling-check rule

When fixing a sanitization bug, scan for the **failure pattern**
("printing secret-bearing output") across ALL output sources, not just
the one that leaked. The 2026-05-10 fix only covered file-grep; live-env
probes were the obvious next failure mode and weren't covered.

### Links

- Prior incident: `docs/bug-autopsies/secret-leakage.md#2026-05-10`
- This autopsy: `docs/bug-autopsies/secret-leakage.md#2026-05-12`
- INDEX entry: `docs/bug-autopsies/INDEX.md` (2026-05-12)
- MEMORY rule: `memory/MEMORY.md` #M-5 — needs generalization update to
  cover live-env probes (file-only wording was too narrow)

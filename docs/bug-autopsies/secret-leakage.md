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

---

## 2026-05-19 — Codex JWT `id_token` printed via wrong-pattern sed on JSON file

### Symptom

While diagnosing why `codex exec` was exiting with returncode=1 in <1s
under the agent_runtime path (B1 writer bakeoff codex-tools-xhigh
investigation), Claude inspected `~/.codex/auth.json` to check the
ChatGPT subscription state. The command was:

```bash
cat ~/.codex/auth.json 2>/dev/null | head -5 | sed 's/=.*/=<REDACTED>/'
```

The `sed 's/=.*/=<REDACTED>/'` redactor was intended to mask values, but
`auth.json` is a JSON file:

```json
{
  "auth_mode": "chatgpt",
  "OPENAI_API_KEY": null,
  "tokens": {
    "id_token": "eyJhbGciOi...<JWT>...",
```

JSON syntax uses `"key": "value"`, not the shell `KEY=VALUE` shape the
sed pattern was designed to redact. There is no `=` in well-formed JSON
content lines. So the redactor was a no-op, and the JWT id_token printed
verbatim into the conversation transcript.

The token was now in:
- The conversation transcript (visible to user; possibly uploaded to
  Anthropic depending on settings)
- The local Claude Code session log
- Any session backups, transcript caches, or telemetry

User must rotate Codex auth: `codex logout` then `codex login`.

### Root cause

**Format-aware sanitization missing.** The two prior incidents
(2026-05-10 file grep, 2026-05-12 live-env probe) hardened the redaction
pattern for **shell-style `KEY=VALUE` content**. JSON files, YAML files,
TOML files, and other structured configs use different separator syntax,
and the `sed 's/=.*/=<REDACTED>/'` pattern matches NONE of them.

This is the **third recurrence** of the same conceptual failure: a
sanitizer chosen for one content format ran on a different format and
silently degraded to a no-op. 2026-05-10 was `grep -v -i secret`
(substring filter on names). 2026-05-12 was the same substring filter
extended to live env. 2026-05-19 is shell-pattern redaction on JSON.

### Why partial fixes fail

Each previous fix added another row to the "decision tree for is X set?"
table. None of them addressed the underlying generator of the bug: an
agent looking at a credential-bearing file in a format it didn't
fingerprint first picks a redactor on autopilot.

The redactor must be chosen by **content format**, not by reflex:

| File format | Indicator | Safe inspection |
|---|---|---|
| Shell env (`.env`, `.bash_secrets`) | `KEY=VALUE` lines, often `export KEY=...` | `cut -d= -f1` or `sed 's/=.*/=<REDACTED>/'` |
| JSON (`auth.json`, `*.json`) | `{` / `"key":` | `jq 'keys'` (top-level keys) or `jq 'del(.tokens, .api_key, .access_token, .id_token, .refresh_token)'` to strip known fields |
| YAML (`config.yaml`, `~/.hermes/config.yaml`) | `key: value`, indentation | `yq 'keys'` or `yq 'del(.tokens, .api_key)'` |
| TOML (`~/.codex/config.toml`) | `key = "value"`, `[section]` | `tq` or a Python one-liner with `tomllib.loads`; **NOT** the shell sed pattern |
| netrc / curl config | `machine X login Y password Z` | Never cat; check existence + permissions only |

### Prevention

#### Hard rule (extends MEMORY.md #M-5 again)

> Before sanitizing a credential-bearing file, check the FORMAT first:
> shell `KEY=VALUE`, JSON, YAML, TOML, and netrc each need a
> format-specific redactor. **Never apply the shell `sed 's/=.*/=<REDACTED>/'`
> pattern to JSON / YAML / TOML files** — it silently degrades to a
> no-op because those formats don't use `=` as the key/value separator
> (or use it differently — TOML's `=` is per-line key-value, but values
> are quoted/typed and may span lines or contain `=` in URLs).
>
> Default to `jq 'keys'` for JSON, `yq 'keys'` for YAML, and the per-line
> Python `tomllib` extractor for TOML. If you only need to know which
> fields exist (not their values), keys-only is always the right answer.

#### Decision branch added to the inspection tree

```
Need to inspect a credential-bearing file?
├── Shell env (`.bash_secrets`, `.envrc`, `.env*`) → cut -d= -f1
├── JSON (auth.json, *.json) → jq 'keys' or jq 'del(<known-token-fields>)'
├── YAML (config.yaml) → yq 'keys' or yq 'del(<known-token-fields>)'
├── TOML (config.toml) → tomllib.loads + filter known-token keys
└── Just need "is this var set?" → `[ -n "${X:-}" ] && echo SET || echo UNSET`
```

#### Sibling-check rule (reinforces 2026-05-12)

When fixing a sanitization bug, scan EVERY credential-bearing inspection
in the upcoming work for the new failure mode. The 2026-05-12 fix
focused on env probes; JSON content was the obvious next surface and
was not covered. Future fixes must consider all the formats listed in
the table above.

### Links

- Prior incidents:
  `docs/bug-autopsies/secret-leakage.md#2026-05-10` (shell file grep),
  `docs/bug-autopsies/secret-leakage.md#2026-05-12` (live-env probe)
- This autopsy: `docs/bug-autopsies/secret-leakage.md#2026-05-19`
- Trigger: 2026-05-19 B1 writer bakeoff codex-tools-xhigh investigation,
  while diagnosing codex CLI sub-second exit-1 crash
- User direction: rotate Codex auth (`codex logout` + `codex login`)

---

## Links

- Tracking issue: #1896 (Secret-leak prevention follow-ups)
- Prior incident references:
  `docs/bug-autopsies/secret-leakage.md#2026-05-10` (shell file grep),
  `docs/bug-autopsies/secret-leakage.md#2026-05-12` (live-env probe),
  `docs/bug-autopsies/secret-leakage.md#2026-05-19` (JSON content)
- Fix commit (rule expansion): `e64f021fb5 docs(autopsy): 2026-05-12 DAGGER_CLOUD_TOKEN leak — extend #M-5 to live-env probes`
- MEMORY rule: `memory/MEMORY.md` #M-5 (extend again for content-format
  awareness — JSON/YAML/TOML need their own redactors; shell sed pattern
  silently degrades to no-op on those)
- Critical rules: `claude_extensions/rules/critical-rules.md`

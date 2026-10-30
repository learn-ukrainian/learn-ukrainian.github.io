# Claude account labels for ordinary workers (#10619)

Moved from [`docs/agent-runtime-guide.md`](../agent-runtime-guide.md).

`dispatch.py dispatch --claude-account b` runs an ordinary Claude worker on the
bound account's verified login directory. The default label `a` (also what a
dispatch without the flag and without a default-account file, below, resolves
to) leaves the plan unchanged; `tests/fixtures/claude_default_account_plan.json`
pins it.
The label is accounting and attribution for load balancing, not an isolation
boundary against a hostile process of the same user. What it guards against is
a key, key helper, endpoint, proxy or provider switch left in the labelled
login directory, or in a scope the worker still loads, silently changing what
the worker runs on. For label `b` the adapter
(`scripts/agent_runtime/adapters/claude.py`, threat model in its docstring):

- admits only a consumer plan. **Non-goal: organisational policy.** A Team or
  Enterprise organisation's server-managed settings and policy limits arrive
  from the server, can apply endpoint, proxy and provider overrides after every
  local check, and are not attested by `auth status`, so they are out of scope.
  Verification asks the provider's profile endpoint about the login
  directory's own credential and requires organisation type `claude_max` or
  `claude_pro` (`CLAUDE_CONSUMER_PLANS`); Team, Enterprise, unknown or missing
  refuses (`claude_account_plan_unsupported`). The plan Claude Code stored with
  that credential (it decides whether the CLI fetches organisational policy; a
  missing one makes it fetch), the global config's organisation, and the plan
  `auth status` resolves must all agree with that answer
  (`claude_account_plan_unverified`);
- requires a host with no machine policy. Organisational policy remains a
  non-goal (above); machine-level policy is refused outright. Claude Code
  2.1.300 reads all of it on Linux from one machine policy root: managed
  settings and their `managed-settings.d` drop-ins, `managed-mcp.json`, a
  managed `CLAUDE.md` and managed rules, skills and agents. A `policyHelper`
  named in managed settings makes a program's output policy at every CLI
  start, which no launch digest can bind. So any entry in that root, or
  anything but a plain directory in its place, refuses whatever it holds
  (`claude_account_machine_policy_present`; an unreadable root
  `claude_account_machine_policy_unavailable`). An absent root or an empty
  directory admits. Under WSL the CLI also reads the Windows policy chain,
  registry included, so WSL refuses (`claude_account_platform_unsupported`).
  The check runs at dispatch, again after the launch is bound, and in the
  launch guard below;
- refuses server-delivered policy state and profile logins. Claude Code
  2.1.300 caches remote managed settings and policy limits in the login
  directory only for an organisational, unknown-plan or profile login:
  `remote-settings.json`, `policy-limits.json`, each one's `.signature.json`
  and `.signature-iat.json`, `remote-settings.json.synced-at`,
  `policy-limits.json.stamp.json`, `remote-settings-consent.json` and
  `remote-settings-helper-consent` (`CLAUDE_POLICY_CACHE_NAMES`). Any of them,
  as a file, link or directory, refuses (`claude_account_policy_cache_present`;
  an unreadable state `claude_account_policy_cache_unavailable`). A profile
  store (`ANTHROPIC_CONFIG_DIR`, `$XDG_CONFIG_HOME/anthropic` or
  `$HOME/.config/anthropic`) holding `active_config` or `configs` would replace
  the login directory's credential without `auth status` showing it, so it
  refuses (`claude_account_profile_store_present`);
- holds the login directory to allowlists, refusing value-free before any
  spawn: every `env` name in its global config (`.claude.json`, which the CLI
  applies over the process environment whatever the setting sources) must be on
  `CLAUDE_LABELLED_ENV_ALLOWLIST` (`claude_account_config_credential_source`);
  a legacy `.config.json`, which the CLI would read instead, is refused
  (`claude_account_config_ambiguous`); the user `settings.json` may carry only
  allowlisted keys and names (`claude_account_settings_credential_source`);
- passes `--setting-sources project,local`, which turns the login directory's
  user scope off: its env, key helper, hooks, permission rules, plugins and
  user MCP servers are not loaded as settings, and the worker gets the harness
  flags and checkout settings. The flag does not stop every reader: Claude Code
  still reads some names from that file directly (`autoMode`, see below), which
  is why the file is held to the allowlist. Restrictive user rules are dropped
  too; the task record carries `claude_account_user_scope_omitted: true`;
- runs `claude auth status` (JSON and text) with the worker's settings
  arguments, working directory and environment: the JSON must name the
  subscription login, first-party provider and bound directory with no other
  key (`claude_account_auth_method_conflict`, or
  `claude_account_auth_status_unavailable`), and the text must print only the
  login method, organization and email. The text names every endpoint, proxy,
  certificate, token, key or provider override in effect, which the JSON does
  not (`claude_account_status_override`);
- binds a digest of every input those checks depended on (its arguments, the
  login directory's settings, global config `env` and login organisation,
  legacy file, credential record, policy caches and profile store entries
  (absent), and the checkout's project and local files, including a linked
  worktree's main checkout) into the plan, after requiring the credential
  record to be the one whose plan was classified. It runs the CLI behind a
  guard that recomputes the digest in the spawned process and execs the CLI
  only on a match with still no machine policy
  (`claude_account_settings_changed`, exit 78), so a policy cache, profile,
  credential or machine policy that appears between verification and launch
  stops the exec. The
  credential file stays in place (the CLI rotates its refresh token) and the
  CLI reads the global config only from beside it, so a digest bind, not a
  copy, is the strongest construction available. What remains is the moment
  between the guard's check and the CLI reading its files. Two things can land
  inside it: a write by a process of the same user (outside the threat model),
  and an administrative policy deployment that installs machine policy in that
  moment, which needs no access to the user's files. No launch-side check can
  close the second: a worker started in that moment runs under the new machine
  policy. Every later launch and dispatch on that host refuses
  (`claude_account_machine_policy_present`).

Limitation: the preflight requires the access token to have more than 60
seconds left. A token that expires during a long worker is refreshed by the CLI
itself; if that refresh fails, the worker fails. It is never retried as the
default account: runner failover re-sends the same label and there is no Claude
failover chain. A token refresh between verification and launch (by another
worker of the same account, or by the status probe for a token close to
expiry) changes the credential record, so that launch refuses with
`claude_account_settings_changed` (fail-closed; a new dispatch re-verifies).

## Allowlisted login-directory names

Two closed lists in `scripts/agent_runtime/attempt_boundary.py` hold the names
a labelled login directory may carry. Names match exactly (no patterns, no
case folding, no exception for a value, `null` included), and no value of an
admitted name is read into a record or a refusal.

- `CLAUDE_LABELLED_ENV_ALLOWLIST`: `env` names, one list for both the global
  config (`.claude.json`, applied to the run) and the user `settings.json`
  (scope off). Each name only tunes local behaviour: Bash and MCP timeouts and
  output limits, output and thinking token budgets, auto-compaction, the
  terminal title, or switching off the updater, telemetry, error reporting,
  cost warnings, the bug command and nonessential traffic.
- `_CLAUDE_LABELLED_USER_SETTINGS_KEYS`: top-level keys of the user
  `settings.json`, whose scope a labelled run turns off. They configure display
  (`theme`, `tui`, `outputStyle`, `language`, `statusLine`,
  `spinnerTipsEnabled`, `verbose`), model and effort within the account
  (`model`, `modelSettings`, `effortLevel`, `alwaysThinkingEnabled`),
  permissions and automation (`permissions`,
  `skipDangerousModePermissionPrompt`, `hooks`), plugins and MCP servers
  (`enabledPlugins`, `extraKnownMarketplaces`, `enabledMcpjsonServers`,
  `disabledMcpjsonServers`, `enableAllProjectMcpServers`), housekeeping
  (`autoUpdatesChannel`, `cleanupPeriodDays`, `includeCoAuthoredBy`,
  `$schema`) and `env` (held to the list above).

None of them names a credential, key helper, endpoint, proxy, certificate or
provider. Those names (`apiKeyHelper`, `awsAuthRefresh`,
`ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `CLAUDE_CODE_USE_BEDROCK`,
`HTTPS_PROXY` and the like), and every name not listed, still refuse.

Of the four names a real second login carried, three were added after reading
how Claude Code 2.1.300 (the installed binary, `claude --version`) defines and
reads each one, by fixed-string search of that binary. The fourth, `autoMode`,
refuses (next section).

| Name | What 2.1.300 does with it | Why it is inert |
| --- | --- | --- |
| `modelSettings` | Per-model map; each entry is read only for `effortLevel`, `maxEffortLevel` and `autoCompactWindow`. | Effort and compaction for a model the account already runs; no route, endpoint or provider. |
| `tui` | `"default"` or `"fullscreen"`: which terminal renderer to use. | Display only. |
| `DISABLE_AUTO_COMPACT` (`env`) | Read once, as a switch that turns auto-compaction off. | Local behaviour only. In the global config it does apply: that labelled run does not auto-compact. |

Reproduce with the installed binary, for example
`grep -a -c -F "tui:()=>B([\"default\",\"fullscreen\"])" "$(readlink -f "$(command -v claude)")"`
(the minified names are specific to 2.1.300). Behaviour proof:
`tests/agent_runtime/test_claude_account_worker.py::test_real_cli_inert_user_settings_names_change_no_auth_source`
loads the three names with the user scope on and shows the installed CLI's
`auth status` JSON and text unchanged. That proves only that the credential
source, endpoint, proxy and provider are unchanged: equal `auth status` output
cannot show that classifier or permission policy is unchanged, which is why
each name's readers were read in the binary too. Claude Code's own list of
environment names safe to apply before workspace trust also holds
`DISABLE_AUTO_COMPACT`, but that list admits provider switches too, so it is
not used as evidence. Other Claude Code versions are not checked: re-check
these names when the CLI changes how it reads them.

### Why `autoMode` refuses

`autoMode` holds the auto mode classifier's rule lists (`allow`, `soft_deny`,
`hard_deny`, `environment`). In 2.1.300 the classifier's settings reader takes
the user settings through a direct getter that does not check which setting
sources are enabled; it filters only project and local settings ("only
user/flag/managed settings may set classifier rules"). So
`--setting-sources project,local` does not keep these lists out of a labelled
run: they become its classifier policy, which the labelled contract forbids.
Equal `auth status` output, with or without the key, says nothing about this.

Evidence (2.1.300, 2026-10-15, synthetic values only). A fresh, credential-free
login directory whose `settings.json` holds only

```json
{"autoMode": {"allow": ["FIXTURE_ALLOW_ONLY"], "soft_deny": ["FIXTURE_SOFT_ONLY"],
              "hard_deny": ["FIXTURE_HARD_ONLY"], "environment": ["FIXTURE_ENV_ONLY"]}}
```

and an isolated, empty `HOME`, run from an empty working directory:

```sh
env -i PATH="$PATH" HOME=<empty dir> CLAUDE_CONFIG_DIR=<fixture login dir> \
  claude --setting-sources project,local auto-mode config
```

prints a JSON object whose four lists are exactly the four fixture lists. With
the fixture `settings.json` moved away, none of the fixture values appear.
`tests/agent_runtime/test_claude_account_worker.py::test_real_cli_reads_auto_mode_whatever_the_setting_sources`
runs the same check with the labelled run's own `--settings` and
`--setting-sources` arguments, then requires the guard to refuse.

If a labelled login refuses at dispatch with

```text
❌ CLAUDE_ACCOUNT_REFUSED: claude_account_settings_credential_source
```

the user `settings.json` (or the global config's `env` map, which has its own
`claude_account_config_credential_source`) carries a name off the lists. Find
it by name only, never printing values: `jq -r 'keys[]' settings.json` and
`jq -r '.env // {} | keys[]' settings.json` in the login directory, compared
with the two lists. For an `autoMode` hit, the remediation is: remove the
top-level `autoMode` key from that `settings.json` (keep a backup beside it)
and dispatch again.

Other names 2.1.300 reads from the user file through the same direct getter
include `model`, `hooks`, `permissions` (its `defaultMode`) and
`skipDangerousModePermissionPrompt`. They were allowlisted before this change
and were not re-reviewed by it.

Where the lists apply (every labelled entry point uses the same two lists,
through `_validated_claude_selection`):

| Entry point | Check | `autoMode` refusal test |
| --- | --- | --- |
| Dispatch (`scripts/dispatcher/admission.py`, `claude_account`) | `verify_claude_account`: both lists. | `tests/dispatcher/test_core.py` (ordinary v2 account admission; protected bound execution is unavailable) |
| Ordinary worker launch preparation (`adapters/claude.py`, `_claude_account_binding`) | `verify_claude_account`: both lists. | `test_claude_account_worker.py::test_bound_label_auto_mode_is_refused` |
| Launch guard (`env_sanitize.run_claude_launch_guard`) | No second name check: it recomputes the digest that binds the verified `settings.json` and global config `env` map, so any change refuses (`claude_account_settings_changed`). | `test_claude_account_worker.py::test_bound_label_auto_mode_written_after_verification_never_launches` |
| Sealed attempt boundary (`attempt_boundary.linux_claude_auth`) | Both lists. | `test_attempt_boundary.py::test_second_claude_account_refuses_auto_mode` |
| Usage probe (`scripts/api/claude_account_usage.py`) | Not applied: CodexBar's OAuth source reads only the credential file, and no Claude Code process loads that directory's settings. | Not applicable. |

## API-key labels `kk` and `szb` (C-2643)

The two funded Anthropic API keys are labels of their own. Dispatch them with
the label alone; no ambient `CLAUDE_CONFIG_DIR` is needed, and one that names a
different directory is still refused (`claude_account_ambient_conflict`):

```sh
.venv/bin/python scripts/dispatch.py dispatch --agent claude --claude-account kk \
  --model claude-haiku-5-5 --mode read-only --prompt "..."
```

Each label's directory lives only in the private binding file, as an entry with
`config_dir` alone (an API key has no login account):

```json
{"schema_version": 1, "accounts": {"b": {"config_dir": "<absolute directory>", "account_uuid": "<account UUID>"},
 "kk": {"config_dir": "<absolute directory>"}, "szb": {"config_dir": "<absolute directory>"}}}
```

Admission (`attempt_boundary._refuse_claude_api_key_launch`) requires the
directory's `settings.json` to hold exactly one key, a non-empty
`apiKeyHelper`, in a file not writable by group or others; anything else
refuses value-free (`claude_account_credentials_missing`,
`claude_account_settings_credential_source`, `claude_account_settings_invalid`,
`claude_account_settings_not_private`). The global config's `env` map, a legacy
`.config.json`, policy caches, profile stores, machine policy and WSL refuse
exactly as for label `b`. The helper's command is never read into a record, an
argument or a refusal.

At launch (`scripts/dispatcher/admission.py`, `claude_launch`) the run keeps
`--setting-sources project,local`, and its one `--settings` (repeats are
last-wins) is that `settings.json` path: flag settings apply under
`--restricted` too, so read-only and workspace-write runs both get the helper.
`claude auth status` must report `authMethod` `api_key_helper`, `apiKeySource`
`apiKeyHelper`, the bound directory and no other key, and its text exactly
`Auth token: apiKeyHelper` (Claude Code 2.1.312); the launch digest binds the
file, and the launch guard recomputes it. No plan is classified: Claude Code
does not use a helper's key to fetch organisational policy (`claude doctor`:
"apiKeyHelper keys are not used for it").

### Spend cap and prompt cache

An API-key run is billed per token, so every dispatch on `kk` or `szb` passes
Claude Code `--max-budget-usd` (print mode stops the run at that spend). The
default is `CLAUDE_API_KEY_BUDGET_USD` in `scripts/agent_runtime/attempt_boundary.py`,
beside the label list: 20 USD per run for each label. A dispatch can lower it with
`dispatch.py dispatch --max-budget-usd <amount>`; an amount above the configured
one, a non-positive or non-numeric one, or a label with no configured amount
refuses before any worktree exists, naming the account
(`claude_account_budget_cap_invalid`, `claude_account_budget_cap_unresolved`). The
flag on a subscription label (`a`, `b`) or another seat is refused; those runs are
unchanged and carry no cap.

Workspace-write runs on an API-key label also set
`CLAUDE_CODE_PROMPT_CACHE_TTL=1h`. Print mode gives an API key the 5 minute cache
lifetime (only subscription logins get an hour), so a code worker whose tests run
longer than 5 minutes between model requests would pay for the cache write again
each time. Read-only runs are short and keep the default. See
[Claude Code prompt caching](https://code.claude.com/docs/en/prompt-caching).

Limits: an API-key label is never the fleet-wide default (the default file
names `a` or `b` only); the ordinary runtime adapter and sealed review attempts
refuse it (`claude_account_api_key_route_unsupported`), so only
`dispatch.py dispatch` runs it; and the per-account usage meter has no row for
it, because a key has no plan window. Its spend is billed per token to that key.

## Fleet-wide default account file

A claude dispatch without `--claude-account` takes its label from one
per-user file, `learn-ukrainian/claude-default-account` in the user config
directory (`$XDG_CONFIG_HOME`, else `~/.config`). `LU_CLAUDE_DEFAULT_ACCOUNT_FILE`
overrides the path for tests and operations; an empty value disables the file.
The file holds one token, `a` or `b`, optionally surrounded by whitespace. A
missing or empty file means `a`, exactly as before. Editing the file moves every
new Claude dispatch to that account without changing any dispatch command.

- Order: an explicit `--claude-account` (the file is then not read), else the
  file, else `a`. A label from the file is admitted exactly like an explicit
  one, with every check above (binding, credential, consumer plan, machine
  policy, WSL, policy caches and profile store, and the launch digest bind),
  so a file naming `b` on a host or login that `--claude-account b` would
  refuse refuses the dispatch instead of running as `a`. Other seats never
  read the file, and neither does a dispatch whose request names another seat
  that a reviewer resolver routes to claude: like an explicit label there, it
  runs as `a` (source `builtin`).
- A present but invalid file is refused before any worktree or task record is
  created, with a value-free `CLAUDE_ACCOUNT_REFUSED` cause that names neither
  the content nor the path: `claude_account_default_file_invalid` (not exactly
  one known label, binary or non-ASCII), `_oversized` (over 64 bytes),
  `_not_private` (not a regular file, not owned by the current user, or group-
  or world-writable; readable by others is fine) or `_unavailable` (unreadable,
  including a symbolic link).
- The default-account file is read once for a new dispatch. The task records
  `claude_account` and `claude_account_source` (`explicit`, `default-file` or
  `builtin`). Worker launch uses the recorded label. Dispatch v2 refuses a
  reused task ID and has no force-new replay path.

- Dispatch v2 does not automatically forward Claude account dispatches between
  hosts. The manual `scripts/orchestration/job_host_exec.py` CLI remains
  available; pass the intended `--claude-account` explicitly when using it.
- The worker adds `claude_account_auth` to its record: `label`, `source`,
  `method` and `verified`, never a token, identity or path; a `dispatch.py
  dispatch` record carries it for every label but `a`. `method` is
  `api_key_helper` when an API-key label's launch passed the checks above
  (the run is billed to that key), `subscription_login` when the adapter's
  launch preparation passed every check
  above for this run (status probes, unchanged digest, the classified
  credential, no machine policy), `bound_account_token` when a sealed attempt's
  boundary verified the bound credential, `unverified` when no verification
  passed in this run (a refusal, or a failure before launch preparation), and
  `host_login` for label `a`, which runs on the host's own login and is not
  probed (`verified: false`). A launch guard refusal after a verified
  preparation shows as the worker's failure, not in the receipt.

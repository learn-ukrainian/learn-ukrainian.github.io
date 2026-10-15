# Claude account labels for ordinary workers (#10619)

Moved from [`docs/agent-runtime-guide.md`](../agent-runtime-guide.md).

`delegate.py dispatch --claude-account b` runs an ordinary Claude worker on the
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
  (`claude_account_config_ambiguous`); the unloaded user `settings.json` may
  carry only allowlisted keys and names (`claude_account_settings_credential_source`);
- passes `--setting-sources project,local`, so the login directory's user
  scope (env, key helper, hooks, permission rules, plugins, user MCP servers)
  never applies: the worker gets the harness flags and checkout settings and no
  user-scope authority. Restrictive user rules are dropped too; the task record
  carries `claude_account_user_scope_omitted: true`;
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
- The file is read once, at dispatch. The task record keeps `claude_account`
  and `claude_account_source` (`explicit`, `default-file`, `builtin`, or
  `record` for a `--force-new` re-run of the same task id, which keeps the
  earlier record's label; a `--claude-account` that contradicts it is refused
  with `claude_account_record_conflict`, and a record label that is not a known
  one with `claude_account_unknown`). A record without a label (another
  seat's, or one from before labels) has none to keep, so its re-run resolves
  like a new dispatch. A recorded label passes every check above again, like
  an explicit one. The worker, runner failover and re-runs use the recorded
  label and never read the file, so changing it affects only new task ids.
- A dispatch that `delegate.py` forwards to a worker host sends the label
  resolved here as `--claude-account` (an explicit flag is sent as given), so
  the worker host never resolves its own default file or record for it: it
  admits that label with every check above or refuses (its own record naming
  another label refuses with `claude_account_record_conflict`), and records the
  source as `explicit`. A worker host whose `delegate.py` predates the flag
  rejects it as an unknown argument and nothing spawns. If the argv to forward
  cannot be shown to name the label, nothing is forwarded
  (`claude_account_forward_unsupported`). An SSH transport failure falls back
  to this host, which runs the label it resolved. `job_host_exec.py -- …
  delegate.py dispatch` resolves nothing locally: dispatch runs on the worker
  host, with that host's file.
- The worker adds `claude_account_auth` to its record: `label`, `source`,
  `method` and `verified`, never a token, identity or path. `method` is
  `subscription_login` when the adapter's launch preparation passed every check
  above for this run (status probes, unchanged digest, the classified
  credential, no machine policy), `bound_account_token` when a sealed attempt's
  boundary verified the bound credential, `unverified` when no verification
  passed in this run (a refusal, or a failure before launch preparation), and
  `host_login` for label `a`, which runs on the host's own login and is not
  probed (`verified: false`). A launch guard refusal after a verified
  preparation shows as the worker's failure, not in the receipt.

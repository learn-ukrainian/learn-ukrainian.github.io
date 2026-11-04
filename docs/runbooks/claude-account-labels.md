# Claude account labels for ordinary workers (#10619)

Account labels identify the approved runtime identity used by a worker. They
support accounting and attribution; they do not isolate processes running as
the same operating-system user. Provisioning and account selection belong to
the operator's private configuration.

For an already authorized task, inspect the dispatch plan and task record for
non-secret provenance. Confirm that the expected model, provider and identity
verification succeeded before relying on its output. Do not print credentials,
login-directory contents, account names or authentication status containing
personal information.

```bash
.venv/bin/python scripts/dispatch.py status
```

## Allowlisted login-directory names

The runtime validates the configured login directory and the settings that
could change its credential source, endpoint or provider. The two closed lists
live in `scripts/agent_runtime/attempt_boundary.py`:

- `CLAUDE_LABELLED_ENV_ALLOWLIST` admits environment names that control local
  behavior, such as terminal display, compaction, timeouts and output limits.
  It applies to both the global configuration's environment map and the user
  settings' environment map. It admits no credential, endpoint or provider
  selector.
- `_CLAUDE_LABELLED_USER_SETTINGS_KEYS` admits top-level user settings. Its
  display keys cover theme, terminal rendering, language, output style, status
  lines, spinner tips and verbosity. Model and effort keys cover the model's
  settings, effort and thinking behavior. Other keys describe permissions,
  hooks, plugins, MCP servers and housekeeping. The environment map remains
  subject to the environment-name allowlist. These keys are admitted under a
  launch contract that omits the user settings scope; admission is not proof
  that loading that scope would be harmless.

Names match exactly, with no pattern, case-folding or value-based exception,
including for null values. Configuration values must never enter a public
record or refusal. A partial, unreadable or changed configuration stops the
launch rather than silently selecting another identity. Do not expand an
allowlist to silence a refusal.

The recorded compatibility evidence for Claude Code 2.1.300 distinguishes
three inert settings from the classifier policy described below:

| Name | Recorded behavior | Why it does not select a credential source |
| --- | --- | --- |
| `modelSettings` | Per-model entries read `effortLevel`, `maxEffortLevel` and `autoCompactWindow`. | These control effort and compaction for the configured model, without choosing a route, endpoint or provider. |
| `tui` | Selects the `default` or `fullscreen` terminal renderer. | Display only. |
| `DISABLE_AUTO_COMPACT` | Disables automatic compaction when its environment map is loaded. | Local behavior only; it does not select a provider. |

The existing
`tests/agent_runtime/test_claude_account_worker.py::test_real_cli_inert_user_settings_names_change_no_auth_source`
uses synthetic settings to compare the CLI's authentication provenance. Equal
provenance alone cannot prove classifier or permission policy unchanged; the
settings readers must also be checked. The recorded version-specific evidence
is not a claim about every future CLI release. Recheck the readers when their
behavior changes, without using an operator's login as a fixture.

An account label is not permission to copy authentication files, change
organization policy or repair an operator's login. Report a refused launch
with its value-free diagnostic and task identifier privately.

### Why `autoMode` refuses

`autoMode` contains classifier rule lists named `allow`, `soft_deny`,
`hard_deny` and `environment`. In the recorded Claude Code 2.1.300 behavior,
the classifier reads user settings directly even when the enabled setting
sources omit the user scope. Thus `--setting-sources project,local` did not
exclude those lists from classifier policy. Authentication provenance does
not reveal that policy change.

The later recorded 2.1.314 behavior honors that setting-source flag for the
classifier. The refusal remains because the lists are policy wherever their
scope loads, and the labelled-launch contract forbids importing user
classifier policy. This generic compatibility rationale does not describe an
operator's account selection or current host settings.

Synthetic policy fixtures can use distinct sentinel strings in each of the
four lists. The existing
`tests/agent_runtime/test_claude_account_worker.py::test_real_cli_unloads_the_labelled_user_auto_mode`
compares those lists with built-in defaults and requires the launch guard to
refuse the unsupported setting. Neither real credentials nor raw account
status belong in public reproduction evidence.

The entry points retain the same validation and change-detection guarantees:

| Entry point | Generic guarantee | Existing coverage |
| --- | --- | --- |
| Dispatch admission | Both closed name lists are checked before launch. | `tests/dispatcher/test_core_admission.py` |
| Worker launch preparation | The same verification rejects unsupported classifier settings. | `tests/agent_runtime/test_claude_account_worker.py::test_bound_label_auto_mode_is_refused` |
| Launch guard | A changed verified input changes the bound digest and refuses execution. | `tests/agent_runtime/test_claude_account_worker.py::test_bound_label_settings_changed_after_verification_never_launch` |
| Isolated attempt boundary | The same two lists apply at the boundary. | `tests/agent_runtime/test_attempt_boundary.py::test_second_claude_account_refuses_auto_mode` |

Existing admitted names such as `model`, `hooks`, `permissions` and
`skipDangerousModePermissionPrompt` also need reader-specific scrutiny; the
classifier finding is not a blanket safety attestation for every allowed key.
Do not edit a login directory or weaken a check to make a worker start.
Preserve the value-free refusal and use the authorized private provisioning
process for remediation.

## API-key labels

A separately provisioned API identity requires its own approval and budget.
A subscription label does not authorize switching to a key-backed provider.
Keep keys and the mapping from labels to accounts in private configuration.
Record only sanitized provenance in public evidence.

### Spend cap and prompt cache

A prompt cache does not guarantee zero spend. Before an authorized paid run,
confirm its approved budget and stop condition through private operational
evidence. A missing or uncertain budget is not permission to proceed. Never
publish live spending limits, account balances or routing choices here.

## Fleet-wide default account file

Defaults are local operational configuration. Public documentation does not
choose an account or publish the default file's contents or discovery paths.
Use the approved private procedure for changes, then verify a sanitized
result. Do not reinterpret a refused label as an instruction to try a default.

Operational details are in the private infra repository's `runbooks/claude-account-labels.md`.

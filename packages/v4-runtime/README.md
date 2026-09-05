# V4 runtime package

`learn-ukrainian-v4-runtime` supplies the canonical public implementation used
by the existing protected API and Sources services. Repository scripts are
compatibility adapters and require the package to be installed.

The default public receipts remain **0 completed / 100 residual / 0 emitted**,
with A13 open. Execution and admission default OFF. The package contains no
production keys, private membership, packets, corpus, or qualified provider
profile.

The service fixes native reasoning effort by role: original-row authors use
medium, and independent row reviewers use high. Both native CLI invocations
receive explicit effort arguments; requests cannot select another effort.

## Native provider credentials

The parent reads only its harness-selected `v4-provider-claude` or
`v4-provider-codex` systemd credential, after checking the fixed reviewed child
profile. Requests cannot supply credentials, paths, modes, models or effort.
No adapter is qualified in the shipped profile; these interfaces do not enable
execution or admission and do not qualify an installed native CLI.

Adapters may explicitly set `credential_mode` to `api_key` or `subscription`.
The existing profile shape without that field means legacy API-key transport
only, with its exact provider environment name. Mode/environment mismatches
fail closed. There is no subscription-to-API-key fallback.

| Harness | Mode | Required `provider_env` | Typed payload value |
| --- | --- | --- | --- |
| Claude | `api_key` | `ANTHROPIC_API_KEY` | `credential` string |
| Codex | `api_key` | `OPENAI_API_KEY` | `credential` string |
| Claude | `subscription` | `CLAUDE_CODE_OAUTH_TOKEN` | `access_token` string |
| Codex | `subscription` | JSON `null` | `auth_json` string containing selected native JSON bytes |

Typed payloads contain exactly `schema: "hramatka-v4-provider-credential.v1"`,
`harness`, `mode`, and the listed value field. Subscription payloads additionally
require `expires_at`, an integer Unix timestamp in seconds at least 60 seconds
in the future. The legacy `{ "credential": "..." }` payload is accepted only
for an API-key profile. Credential files must be regular, non-symlink, owned
by the service user or root, inaccessible to group/others, and at most 64 KiB.
Duplicate JSON keys, extra fields, invalid types and file changes during reads
are refused. Token strings are bounded printable ASCII without whitespace.

Codex `auth_json` requires `auth_mode: "chatgpt"` and exactly one `tokens`
object with `id_token`, `access_token`, `refresh_token` and `account_id`.
Only optional `OPENAI_API_KEY: null` and an already elapsed, timezone-aware
`last_refresh` timestamp are accepted alongside those fields. Both JWTs must
have a structurally valid RS256 header and a fresh integer `exp`. This is
schema/freshness validation, not signature verification or proof of provider
acceptance. Expired or incompatible credentials require operator action;
the package adds no credential provisioning or refresh service.

Claude receives only its selected OAuth access token, without a provider-home
copy. Codex receives the validated UTF-8 auth bytes via a sealed anonymous Linux
memfd and bwrap `--ro-bind-data`, read-only at `CODEX_HOME/auth.json` inside the
blank disposable home. The libc memfd interface also supports Python builds
without the corresponding `os` wrapper. The FD closes in the parent after
launch, including launch failure, and is consumed by bwrap before native exec.
No host auth path is mounted and child writes cannot mutate host credentials.
Codex is explicitly configured to use file credential storage, consistent with
the [native authentication documentation](https://learn.chatgpt.com/docs/auth#credential-storage).
Native refresh/write compatibility remains part of later protected-unit
qualification; the read-only selected auth file must not be relaxed implicitly.

Credential values are excluded from representations and argv. The argv digest
uses an opaque descriptor placeholder and never hashes auth bytes. Captures
containing a selected token, selected auth JSON, or Sources capability are
refused before artifact retention or digesting. This check detects literal
disclosure, including across pipe reads; it is not a general detector for
arbitrary encodings or transformations by a compromised adapter. Immutable
adapter qualification remains required. Synthetic tests exercise both modes
for both harnesses in the actual source-free bwrap closure, with denial and
cleanup cases. They do not establish actual-unit/provider qualification.

## Build and test

Use the interpreter specified by the dispatch contract. Set
`V4_PROJECT_PYTHON` to that absolute interpreter path. Worktree workers must
use the shared project interpreter and must not create a worktree virtualenv.

Run from the dispatch worktree, with committed package and asset inputs:

```bash
V4_PUBLIC_COMMIT=$(git rev-parse HEAD)
V4_BUILD_ROOT="$PWD/batch_state/v4-build/$V4_PUBLIC_COMMIT"
mkdir -p "$V4_BUILD_ROOT/wheels"
SOURCE_DATE_EPOCH=$(git show -s --format=%ct HEAD) \
  "$V4_PROJECT_PYTHON" -m pip wheel --no-deps --no-build-isolation \
  packages/v4-runtime --wheel-dir "$V4_BUILD_ROOT/wheels"
"$V4_PROJECT_PYTHON" -m pip install --no-deps --no-compile \
  --target "$V4_BUILD_ROOT/installed" "$V4_BUILD_ROOT"/wheels/*.whl
PYTHONPATH="$V4_BUILD_ROOT/installed" \
  "$V4_PROJECT_PYTHON" -m pytest tests/projects/open_model_data
```

The install is an owned test dependency. `PYTHONPATH` supplies that installed
package to pytest and its subprocesses. The shared interpreter environment is
not modified. CI installs this same declared package dependency into its own
job environment. Rebuild into a fresh owned target after changing the commit.

Release builds refuse dirty package or asset inputs and verify every copied
implementation against the actual Git commit. Fixed allowlisted public assets
are copied at build time. Runtime operations use `importlib.resources`; they
need no checkout, Git, or `scripts` namespace.

`build_assets.py --development` permits source inspection with an explicitly
unverified commit when inputs are dirty. Such output cannot pass readiness or
serve as release evidence.

## Preserved provenance

The fixed `provenance/v1/manifest.json` records every occurrence of seventeen
historical implementation bindings and sixteen direct data bindings. Historical
implementations are exact, inert `.blob` resources. Their logical `scripts/...`
paths are metadata. They are never imported or executed.

The relationship is `runtime_successor_validating_frozen_receipt`. The A3
algorithm descriptor is preserved; whole-program equivalence is not asserted.
The repository validator continues to reject current adapter/implementation
bytes against the original sealed source digest.

`_build_identity.py` is generated reproducibly and read as strict byte data.
It anchors the release and provenance manifests. The private verified vendor
manifest supplies the external trust anchor for the actual public commit,
wheel and installed files. A release's self-consistency check alone is not
private vendor verification.

See the [mechanism runbook](../../docs/projects/open-model-data/v4-real-slot-mechanism-runbook.md)
for the public interfaces and deployment residuals.

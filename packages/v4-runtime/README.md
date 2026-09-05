# V4 runtime package

`learn-ukrainian-v4-runtime` supplies the canonical public implementation used
by the existing protected API and Sources services. Repository scripts are
compatibility adapters and require the package to be installed.

The default public receipts remain **0 completed / 100 residual / 0 emitted**,
with A13 open. Execution and admission default OFF. The package contains no
production keys, private membership, packets, corpus, or qualified provider
profile.

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

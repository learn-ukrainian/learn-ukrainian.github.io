# Pinned release preview fixtures

These are synthetic mechanics fixtures produced by `dataset_projection.create_release`
at commit `7d4680686862d4ef2a66870a883aed6583bd64f7`. They contain ASCII placeholders,
not Ukrainian language claims. `CERTIFIED` exercises a presentation branch under
the temporary authority in `tests/word_card_certification_fixtures.py`. It grants
no linguistic certification or publication approval.

`generate_release.py` builds two same-spelling identities with six parallel cited
assertions, one synthetic CERTIFIED card and one CANDIDATE. The JSONL and JSON
packages use the same original inputs and different release versions. The
CI-collected `tests/test_atlas_preview_release_fixture.py` generates both packages
outside the checkout, then compares every byte with these committed fixtures.
It uses the producer's existing permission, citation, certification, and output
guards. Negative controls mutate copies in managed scratch and use the producer's
`canonical()` and `sha256()` functions to rebuild manifests.

`producer_dataset_projection.py` is the byte-identical (19503 bytes, SHA-256
`6fe2cbbb...3da5`) `dataset_projection.py` from that producer commit. It is
trusted committed test code, not a sandbox, and is never imported by the site.
`generate_release.py` executes it from that fixed package-local path only after
checking the full digest, so a newer live producer, a missing copy or a changed
byte can neither alter these fixtures nor run. There is no live-producer, Git
history or network fallback. Freezing this copy does not certify compatibility
with the current producer; that drift is tracked separately.

## Local build configuration

`ATLAS_WORD_CARD_PREVIEW=1` enables `/lexicon-v2/`. The default build excludes
these routes and returns before reading release configuration or artifacts.

`ATLAS_WORD_CARD_RELEASE_PATH` names a local package directory containing
`manifest.json` and the dataset named by that manifest. It is never rendered.
`ATLAS_WORD_CARD_RELEASE_PIN` is JSON configuration with these required keys:

```json
{
  "release_version": "v0.1.0-synthetic",
  "dataset_sha256": "edb0a667ed727597e0ae5187bff82b2ffeea0a03bfbcc48b91934a8b6cb22cbd",
  "manifest_sha256": "24c3b98a65f57294bec78795c179252950eb071ede008320ce03b06f6c5faf6d",
  "provenance": "synthetic-fixture"
}
```

This pin selects `release-jsonl`. The JSON package's independent literal pin is
in `release-controls.ts`. Real releases use `provenance: "producer-declared"`;
their status comes from the producer and implies no publication approval. Pins
are explicit configuration, never regenerated from a changing directory at build
time. Replacing the package under an unchanged pin produces a visible refusal.

Word routes are `/lexicon-v2/release/<card_id>/`; comparison routes are
`/lexicon-v2/compare/release/<card_id>/`. No spelling lookup or current-card
pairing is inferred. Missing configuration or refused input renders its reason
at `/lexicon-v2/release/`. Existing assembled-card diagnostic routes retain their
current identity and comparison behavior.

Report links open a GitHub issue draft only after a user click. The URL contains
only release version, dataset digest, card ID/version, assertion ID, and field.
No source values are copied or hashed, and no issue is submitted automatically.

## Verification boundaries

The focused unit files are `word-card-release.test.ts` and
`word-card-preview.test.tsx`. The Playwright `word-card-preview.spec.ts` retains
90 assembled-card regressions and runs all 17 release controls, R01–R16 plus
R10b. Set `PYTHON` to the task's prescribed absolute project interpreter for
producer-driven mutations. Use managed `TMPDIR` for diagnostic builds.

`buildPreview()` uses the actual route, component, and site configuration in an
isolated scratch root. It omits corpus hydration, content collections, unrelated
pages, and public assets. This is local engine/browser proof, not a full site
build or actual Data-release integration. CI retains the full build obligation;
the driver retains independent held-out review, landing, merged proof, and
cleanup. Actual Data v0.1 integration remains Data+Atlas-owned.

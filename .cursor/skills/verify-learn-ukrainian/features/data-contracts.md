# Data contracts & local CI Gate

Developers prove curriculum and Atlas integrity with the same scripts CI Gate runs: content-contract `checks.sh`, lesson lock freshness, Atlas register pins/manifests, and the licence (permissions) register schema tests — without requiring private corpora when those inputs are absent.

## Sub-features

- `ci-checks-sh` runs `bash scripts/ci/checks.sh` (Ruff + MDX/Atlas/BIO content contracts; see `docs/runbooks/ci-gate.md`).
- `manifest-freshness` runs `scripts/lexicon/check_manifest_freshness.py` (DB-free fingerprint gate).
- `licence-register` validates `docs/sources/permissions-register.yaml` via `tests/validate/test_permissions_register.py`.
- `atlas-register-pins` verifies committed pilot manifest + register pin + identity registry through `scripts.atlas.word_card_foundation verify`.
- `lesson-lock-freshness` checks `lessons.lock.yaml` for a sample module (`a1/sounds-letters-and-hello`).
- `pack-verify-sources` runs evidence pack-verify only when Sources MCP / local sources service is up.

## How to get to it (user POV)

- Contributors run these from a clone with `.venv` after fetching `origin/main` (for diff-scoped checks).
- Verification agents run the bundled helper rather than re-deriving the command list.

## Driving it with run-checks

Preconditions:

- `.venv/bin/python` installed from `requirements.txt`.
- `git fetch origin main` when running `checks.sh` (skipped otherwise).
- No preview server required.

- **Full local check bundle.** Run `bash .cursor/skills/verify-learn-ukrainian/bin/run-checks.sh`. Observable: lines `PASS` / `SKIP` / `FAIL`; summary counts; exit `0` when no `FAIL`.
- **CI Gate checks alone.** Run `EVENT_NAME=local bash scripts/ci/checks.sh`. Exit `0` means every grouped check passed.
- **Licence register.** Run `.venv/bin/python -m pytest tests/validate/test_permissions_register.py -q`. Exit `0`.
- **Atlas pins + manifest.** Run `.venv/bin/python -m scripts.atlas.word_card_foundation verify --manifest registry/atlas/pilot/pilot-v1.json --registry registry/atlas/identity/registry.json`. Exit `0` and JSON stdout with `operation: verify`.
- **Lesson lock.** Run `.venv/bin/python -m scripts.curriculum.evidence lessons-lock a1 sounds-letters-and-hello`. Exit `0` and an `ok:` line when the lock matches current evidence.
- **Sources-backed pack-verify.** Only when Sources is up: `.venv/bin/python -m scripts.curriculum.evidence pack-verify a1 sounds-letters-and-hello`. Otherwise expect `SKIP` from `run-checks.sh`, never a red X for "connection refused".
- **Proof.** Save the `run-checks.sh` transcript under `$LU_VERIFY_EVIDENCE_DIR/run-checks.log`.

## Gotchas

- Install Python deps from `requirements-lock.txt` (or pin `ruff` to the lockfile version). A newer unpinned ruff can fail rules CI does not enforce.
- `checks.sh` needs full history / `origin/main` for changed-vs-base gates; shallow clones should fetch before claiming CI parity.
- VESUM lookups inside plan validate are declared `not_checked` when `data/vesum.db` is absent — that is intentional in CI, not a local failure to "fix" by skipping the whole script.
- Word-card `verify` on committed pilot inputs does not certify evaluation readiness (`--for-evaluation` must refuse).
- A lesson-lock mismatch means the checker ran and the lock is not fresh — that is product/curriculum drift to fix with `lessons-lock --write` under the right authority, not an env skip.
- Private curated-seed `make` targets exit `2` when inputs are missing — `run-checks.sh` skips those rather than calling make.
- Never paste internal hostnames, absolute developer home paths, or secrets into the evidence log you commit; the artifacts directory is gitignored for this reason.

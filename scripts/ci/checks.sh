#!/usr/bin/env bash
# Lint and content-contract gates of the CI "Checks" job, in one place.
#
# Every check runs even when an earlier one fails, so one run reports every
# red check; the script exits non-zero if any failed. Needs the project .venv
# (python-ci-env), root `npm ci`, and full git history (origin/main diffs).
# Inputs from the event: EVENT_NAME, BASE_SHA, HEAD_SHA (all optional).
set -uo pipefail

failed=()
check() {
  local name="$1"
  shift
  echo "::group::${name}"
  if "$@"; then
    echo "::endgroup::"
  else
    echo "::endgroup::"
    echo "::error::${name} failed"
    failed+=("$name")
  fi
}

# Lint only; `ruff format --check` is not a gate (~2,050 files differ).
check "Ruff" .venv/bin/python -m ruff check scripts/ tests/ agents_extensions/ dashboards/

plan_validate() {
  # pull_request: only when the v2 plan inputs changed; other events always.
  if [ "${EVENT_NAME:-}" = pull_request ] && [ -z "$(git diff --name-only origin/main...HEAD -- \
      curriculum/l2-uk-en/lesson-plans curriculum/l2-uk-en/evidence \
      schemas/module-plan-v2.schema.json scripts/curriculum/validate)" ]; then
    echo "No v2 plan inputs changed; skipping the v2 plan validator."
    return 0
  fi
  local level_dir status=0
  for level_dir in curriculum/l2-uk-en/lesson-plans/*/; do
    if find "$level_dir" -maxdepth 1 -name '*.yaml' ! -name '_*' | grep -q .; then
      .venv/bin/python -m scripts.curriculum.validate "$(basename "$level_dir")" --all --strict || status=1
    fi
  done
  return "$status"
}
check "Plan Validate (v2 plans)" plan_validate
# Generated arc landing, module pages and site/src/data/arc-a1.json (#8397).
check "Arc landing drift" .venv/bin/python -m scripts.build.build_arc_landing a1 --check

word_atlas_ratchet() {
  .venv/bin/python -m scripts.practice_deck.io || return 1
  local base_ref="${BASE_SHA:-origin/main}" deck deck_args=()
  for deck in site/public/lexicon/*.json; do
    deck_args+=(--practice-deck "$deck")
  done
  .venv/bin/python scripts/audit/lint_word_atlas.py \
    --manifest site/src/data/lexicon-manifest.json \
    "${deck_args[@]}" --base-ref "$base_ref" \
    --baseline scripts/audit/word_atlas_lint_baseline.json --ratchet --update-baseline || return 1
  git diff --exit-code -- scripts/audit/word_atlas_lint_baseline.json
}
check "Run Word Atlas sense-lint ratchet (#6437)" word_atlas_ratchet

lesson_schema_drift() {
  .venv/bin/python scripts/build/generate_lesson_schema.py && git diff --exit-code docs/lesson-schema.yaml
}
check "Lesson schema drift" lesson_schema_drift
check "MDX source parity" .venv/bin/python scripts/audit/check_mdx_source_parity.py --changed-vs-base origin/main
check "MDX forward parity" .venv/bin/python scripts/audit/check_mdx_forward_parity.py --changed-vs-base origin/main
check "Teacher cloze content" .venv/bin/python scripts/audit/check_teacher_cloze_content.py
check "Locked module not published" .venv/bin/python scripts/audit/check_locked_module_not_published.py --changed-vs-base origin/main
check "MDX generation drift" .venv/bin/python scripts/audit/check_mdx_generation_drift.py --changed-vs-base origin/main
check "Atlas manifest freshness" .venv/bin/python scripts/lexicon/check_manifest_freshness.py
check "Atlas manifest enrichment" .venv/bin/python scripts/audit/check_atlas_manifest_enrichment.py
check "Static practice assets" .venv/bin/python scripts/audit/check_static_practice_assets.py
check "Dossier word counts" .venv/bin/python scripts/audit/check_dossier_wordcount.py --changed
check "Validate BIO preparation capsules and active holds" .venv/bin/python -m scripts.ci.bio_preparation_gate

if [ "${#failed[@]}" -gt 0 ]; then
  printf 'Failed checks:\n'
  printf '  %s\n' "${failed[@]}"
  exit 1
fi
echo "All checks passed."

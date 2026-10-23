from pathlib import Path

import pytest

from scripts.build.linear_pipeline import LinearPipelineError, plan_check

pytestmark = pytest.mark.reads_content


@pytest.mark.slow
def test_all_seminar_plans_pass_validate_plan():
    """
    Iterates every plan in the seminar levels, calls linear_pipeline.plan_check,
    asserts no LinearPipelineError (specifically related to references, as
    other pre-existing structural issues are out of scope for this PR).
    """
    plans_dir = Path("curriculum/l2-uk-en/plans")
    seminar_levels = {
        'hist', 'bio', 'istorio', 'lit', 'lit-essay', 'lit-hist-fic',
        'lit-fantastika', 'lit-war', 'lit-humor', 'lit-youth', 'lit-doc',
        'lit-drama', 'lit-crimea', 'oes', 'ruth', 'folk'
    }

    plans = [p for p in plans_dir.glob("**/*.yaml") if p.parent.name in seminar_levels]

    for plan_path in plans:
        try:
            plan_check(plan_path)
        except LinearPipelineError as e:
            msg = str(e)
            # We assert that the backfilled plans have no reference-related errors.
            # Pre-existing non-references errors (like missing subtitle, non-string points)
            # cannot be fixed due to the hard constraint: "DO NOT modify any non-references field".
            if "Every plan reference must include a title" in msg or \
               "Plan references must be a non-empty list" in msg or \
               "missing required keys: references" in msg:
                pytest.fail(f"Reference validation failed for {plan_path}: {msg}")

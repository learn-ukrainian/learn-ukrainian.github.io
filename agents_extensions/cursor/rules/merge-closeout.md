# Merge closeout (Cursor)

Deployed digest: `.cursor/rules/merge-closeout.mdc` (`alwaysApply`).

`MERGED` is not closeout. Run `LU_PRODUCT_ROOT="$PWD" .venv/bin/python -m lu_machinery.orchestration.merge_closeout <N> --repo-root . --apply`,
the last step of the `full-send` skill. Canonical: `workflow.md` § Post-merge cleanup.

Task-specific proofs (host pull, tunnel, occupancy, restarts) stay on that
task. Do not promote them into standing merge hygiene.

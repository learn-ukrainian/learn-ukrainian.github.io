# Lesson Schema Workflow

`docs/lesson-schema.yaml` is generated. Do not hand-edit it.

When you add or modify a Starlight lesson component:

1. Update the component prop interface and its JSDoc schema tags.
2. If the component is new, add it to `docs/lesson-contract.md` §3 with its tab and scope.
3. If the change adds or removes an activity type, update `scripts/pipeline/config_tables.py` and the matrix in `docs/best-practices/activity-pedagogy.md`.
4. Regenerate the schema:

   ```bash
   .venv/bin/python scripts/build/generate_lesson_schema.py
   ```

5. Review the `docs/lesson-schema.yaml` diff and commit the component/config/contract change together with the regenerated schema.
6. Run the focused checks:

   ```bash
   .venv/bin/pytest tests/test_lesson_schema.py tests/test_prompt_substitution.py -v
   .venv/bin/ruff check scripts/build/generate_lesson_schema.py scripts/build/prompt_builder.py tests/test_lesson_schema.py tests/test_prompt_substitution.py
   ```

The pre-commit hook and CI drift gate regenerate the schema and fail if the committed YAML differs.

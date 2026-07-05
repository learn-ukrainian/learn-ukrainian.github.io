# Nightly Audit Cron Job Prompt

You are running as a nightly read-only automated cron job.

## Instructions
1. Run the nightly audit wrapper script:
   ```bash
   .venv/bin/python scripts/audit/hermes_nightly_audit.py
   ```
2. Read the script's stdout summary and print it.
3. Do **NOTHING** else. Do not run any other tools, do not perform git commands, do not build levels, and do not modify the curriculum files.
4. Do **NOT** write files outside the designated report path `batch_state/hermes_cron/`.
5. Forbid the use of toolsets other than `terminal` and `file`.

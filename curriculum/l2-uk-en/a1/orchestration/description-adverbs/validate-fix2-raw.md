  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=5787 chars: ROLE: You are a SILENT EXECUTION AGENT with FULL read-write access.  TOOLS YOU MUST USE (not simulate): - run_shell_command: scripts/audit_module.sh, .venv/bin/python scripts/*.py, grep, wc - read_fil...
===TAG_START===
Fixed all issues for description-adverbs:
1. Added missing YAML frontmatter to description-adverbs.md.
2. Fixed structure by creating A1-compliant activities sidecar (activities/description-adverbs.yaml).
3. Created vocabulary sidecar (vocabulary/description-adverbs.yaml).
4. Fixed template requirements (Presentation header, Engagement box).
5. Fixed activity prompt length issues.
6. Added missing Tier 1 review file.
All audit checks now pass successfully.
===TAG_END===

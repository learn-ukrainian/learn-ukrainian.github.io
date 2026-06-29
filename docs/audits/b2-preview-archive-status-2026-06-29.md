# B2 Preview Archive Status — 2026-06-29

Status,Scope,Disposition
Superseded preview,B2 M01-M68,"Preserved for provenance and source mining; not a release-candidate learner-facing B2."
Production freeze,M69+,"Do not build additional B2 modules until prompt/gate hardening, source readiness audit, and a golden pilot rebuild complete."
Score interpretation,M01-M68,"Existing LLM scores are content-validity provenance only; they are not teaching-quality approval."

Metric,Count,Interpretation
B1 modules with inline activity YAML,94/94,B1 establishes the current successful lesson-practice baseline.
B1 modules with `INJECT_ACTIVITY` markers,92/94,B1 usually interrupts teaching with in-lesson practice.
B2 modules with inline activity YAML,7/68,B2 preview lacks in-lesson practice in most modules.
B2 modules with `INJECT_ACTIVITY` markers,8/68,B2 preview mostly generated reference-style lessons.
B2 modules with no `INJECT_ACTIVITY` markers,60/68,Most B2 modules cannot render in-lesson practice from source markers.
B2 marker/inline mismatches,2,"M64 and M65 have injection markers but `inline: []` activity YAML."

Affected recent modules,Observed status
M64 `advanced-conjunctions-i`,4 injection markers; 0 inline activities; 10 workbook activities.
M65 `advanced-conjunctions-ii`,4 injection markers; 0 inline activities; 10 workbook activities.
M66 `checkpoint-morphology`,0 injection markers; 0 inline activities; 11 workbook activities.
M67 `synonymy-types-and-rows`,0 injection markers; 0 inline activities; 10 workbook activities.
M68 `synonymy-in-registers`,0 injection markers; 0 inline activities; 10 workbook activities.

Decision,Reference
B2 preview archived and rebuild accepted,`docs/decisions/2026-06-29-b2-preview-archive-and-rebuild.md`

Next stage,Required before module production resumes
PR 2,Prompt and deterministic gate hardening.
PR 3,B2 source/plan/wiki/research readiness audit.
PR 4,Golden pilot rebuild with teaching-quality comparison against B1.
Wave rebuilds,Only after the pilot proves the new teaching contract.

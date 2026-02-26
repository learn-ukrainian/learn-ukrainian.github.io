        # Fix Phase — content-only audit failures

        The following audit errors must be fixed for module `feedback-negotiation-complaints`:

        ## Audit Output (last 60 lines)

        ```
        ============================================================
  OTAMAN VERIFY: feedback-negotiation-complaints
============================================================

[1/3] Running audit with --skip-activities...
[2/3] Reading status JSON...
[3/3] Checking orchestration artifacts...

────────────────────────────────────────────────────────────
  VERDICT: FAIL
  Module:  feedback-negotiation-complaints
────────────────────────────────────────────────────────────
  audit script returned non-zero exit code
  failing gates:
    lesson: 6830/4000 (raw: 7388) | pedagogy: 7 violations | richness: 81% < 95% min (grammar)

  Otaman has NOT completed this module.
  Fix the issues above and re-run this script.

─── Audit output (last 15 lines) ───
       → FIX: Break into shorter sentences. First 5 words: 'Ми також свідомо виправили дуже...'
    [CONTENT_REDUNDANCY] Redundant information detected in lesson (73% overlap): "* ✅ Правильно: Нам потрібно терміново **обговорити фінансові умови** нового великого контракту.". Shares significant keywords with sentence at index 227.
       → FIX: Remove redundant paragraphs. Ensure each section adds new unique value.


  📝 RECOMMENDATION: UPDATE (patch fixes) (severity 30/100)
     → 8 violations (significant)


  Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/audit/feedback-negotiation-complaints-audit.md
  Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/status/feedback-negotiation-complaints.json

  ❌ AUDIT FAILED. Correct errors before proceeding.

  ❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/feedback-negotiation-complaints-audit.log for details)
        ```


        ## Files to Fix

        - Content: `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/feedback-negotiation-complaints.md`



        ## Instructions

        1. Read the audit errors above carefully
        2. Fix ONLY the issues mentioned — do not rewrite working content
        3. Preserve section structure and word counts
        4. After fixing, the audit must pass

        **IMPORTANT:** Do NOT add or remove sections. Do NOT change the module structure.
        Fix only the specific violations listed above.


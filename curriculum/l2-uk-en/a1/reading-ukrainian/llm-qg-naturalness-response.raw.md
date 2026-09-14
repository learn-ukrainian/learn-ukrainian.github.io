{
  "evidence_quotes": [
    "Українське о залишається чистим; читай молоко́ у три відкриті удари.",
    "Ки́їв — це головна {столи́ця} Украї́ни.",
    "Луна́є гарна пі́сня."
  ],
  "rubric_mapping": "Across all three lessons, two concrete residual defects warrant revision. Quote 1: unnatural explanatory collocation—«відкриті удари» transfers English beat terminology into Ukrainian reading instructions; openness describes syllables, and this phrasing does not naturally describe reading. Quote 2: semantic redundancy—«головна столиця» unnecessarily suggests a hierarchy of Ukrainian capitals in an ordinary identification sentence. Quote 3: positive evidence—the verb–noun pairing naturally describes a song being heard, with appropriate adjective agreement. These are linguistic judgments, not repeated vocabulary or formatting gates. Source verification remains unresolved: the attempted VESUM batch and dictionary lookups for «столиця», «удар», and «лунати» all returned approval-policy errors, so none supplies corroborating evidence.",
  "score": 7.0,
  "evidence": "\"Українське о залишається чистим; читай молоко́ у три відкриті удари.\"",
  "issue_ids": [
    "UKRAINIAN_GRAMMAR_CALQUE"
  ],
  "findings": [
    {
      "issue_id": "UKRAINIAN_GRAMMAR_CALQUE",
      "quote": "Українське о залишається чистим; читай молоко́ у три відкриті удари.",
      "severity": "major",
      "explanation": "Lesson 2, act-4: «у три відкриті удари» is unnatural reading metalanguage, apparently transferred from English syllable beats. It obscures the intended instruction to read three open syllables. Dictionary verification was attempted but blocked; this finding rests on editorial linguistic judgment.",
      "replacement": null,
      "dimension": "naturalness"
    },
    {
      "issue_id": "UKRAINIAN_GRAMMAR_CALQUE",
      "quote": "Ки́їв — це головна {столи́ця} Украї́ни.",
      "severity": "moderate",
      "explanation": "Lesson 3, act-l3-wb-fill: «головна столиця» is an unnecessarily inflated collocation in this context. The adjective suggests multiple capitals ranked by importance, whereas the sentence simply identifies Ukraine's capital. Dictionary verification was attempted but blocked.",
      "replacement": null,
      "dimension": "naturalness"
    }
  ],
  "flags": [
    "source_verification_blocked: VESUM and sources dictionary calls require approval, but the active approval policy is never; morphology and collocations were not independently source-verified",
    "unverified citation: attributed textbook quotations across lessons 1–3 could not be independently checked; this does not establish fabrication",
    "audit_line_missing: implementation_map_audit",
    "audit_line_missing: bad_form_audit",
    "audit_line_missing: activity_split_audit"
  ],
  "verdict": "REVISE"
}
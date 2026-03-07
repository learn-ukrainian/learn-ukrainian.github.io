**Phase**: Beginner Content
**Step**: Audit and Content Formatting
**Friction Type**: VALIDATION
**Raw Error**: [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose (19 occurrences): (We saw objects), (We know words), (Now you know more) — breaks immersion target / IMMERSION TOO LOW (9.2% vs 25-40% target)
**Self-Correction**: Radically stripped English text and significantly expanded Ukrainian immersion using pure A1 decodable vocabulary blocks. Iteratively verified using the audit script until the immersion ratio exceeded the strict 25% threshold (hit 25.1%).
**Proposed Tooling Fix**: The audit script applies the `[INLINE_ENGLISH_IN_PROSE]` rule meant for B1+ to A1 prose, forcing an awkward line-break structure for basic translations. Consider exempting A1 from inline translation bans since English scaffolding is heavily relied upon.
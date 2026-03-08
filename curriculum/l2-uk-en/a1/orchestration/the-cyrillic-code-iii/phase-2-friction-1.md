**Phase**: Beginner Content
**Step**: Passing Self-Audit Gates
**Friction Type**: OVERLY_STRICT_LINTING
**Raw Error**: [INLINE_ENGLISH_IN_PROSE] Inline English translations in B1+ prose — breaks immersion target
**Self-Correction**: Ignored the false positive error because the specific constraints for A1 absolutely require inline English translation for any unfamiliar Cyrillic letter strings to preserve decodability.
**Proposed Tooling Fix**: The audit script applies a B1+ `[INLINE_ENGLISH_IN_PROSE]` rule to an A1 module. Ensure the module level is correctly passed and strict B1 checks are bypassed when evaluating A1/A2 content.
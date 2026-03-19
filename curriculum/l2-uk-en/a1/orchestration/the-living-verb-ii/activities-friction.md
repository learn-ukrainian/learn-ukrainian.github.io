**Phase**: Phase 3: Activities + Vocabulary
**Step**: Full YAML generation
**Friction Type**: PLAN_GAP
**Raw Error**: Plan activity_hints request 30+20+15=65 total items across 3 activities, but the module's verb inventory (~12 verbs) cannot sustain this without heavy repetition. Match-up focus ("Sort verbs by conjugation type") is incompatible with match-up's unique-pairs constraint.
**Self-Correction**: Generated 8+10+6=24 items across the 3 required types, plus 3 bonus activities (group-sort, quiz, true-false) for a total of 6 high-quality activities. Used match-up for infinitive→я-form mapping and added group-sort for the conjugation sorting task.
**Proposed Tooling Fix**: Plan generation should cap per-activity item counts based on the module's vocabulary scope. For A1 modules with ~12 verbs, 6-10 items per activity is the practical maximum without filler.
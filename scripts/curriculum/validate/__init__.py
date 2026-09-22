"""Module plan validator (issue #8412, Briefs A and B).

The complete plan-validate gate of docs/epics/fresh-build-plan-schema.md §6:
checks one module plan (curriculum/l2-uk-en/lesson-plans/<level>/<slug>.yaml)
against its evidence pack and the level word store, against every plan at an
earlier arc position (rule 4), against the level arc (rule 5), against the
level grammar registry, and against its own generated scope sidecar and its
module title — §2 rules 1–7 with the semantics of §2a.
"""

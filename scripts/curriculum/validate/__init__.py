"""Single-plan module plan validator (issue #8412, Brief A).

Checks one module plan (curriculum/l2-uk-en/lesson-plans/<level>/<slug>.yaml)
against its evidence pack and the level word store. This is the single-plan
half of plan-validate: rules that need the arc, other plans, the grammar
registry, the scope sidecar or git history are Brief B and are reported as
not_checked: cross_plan_rules_pending.
"""

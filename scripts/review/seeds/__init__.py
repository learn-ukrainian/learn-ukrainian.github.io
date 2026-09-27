"""Seeded-defect measurement of reviewer seats (#8430 Part R3).

R3-A, the data model: ``manifest`` (the private scoring manifests, the set assignment and the
confirmation lock under ``batch_state/review-measurement/``, and the independence rules over the
recorded identities), ``adjudicate`` (blinded adjudication tasks and their validated replies) and
``score`` (every metric of a measurement report with its interval, computed from the findings
database and the adjudications). Planting is R3-B, the runner R3-C.
"""

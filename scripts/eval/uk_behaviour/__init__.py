"""Ukrainian behaviour evaluation, protocol ``uk-behaviour/2`` (G3 of the freeze).

Extends the uk-preamble harness with production adapters, the semantic sidecar
scorer, receipt binding and the no-paid proof. The specification is
``docs/evaluations/uk-behaviour-freeze.md``; its manifest pins this code. The
review prompts and the judge template are private bytes pinned by SHA-256.
Requests, labels, outputs and judgements are private inputs passed by path and
never stored in the repository.
"""

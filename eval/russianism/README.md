# Russianism Eval

This directory contains starter prompts for `scripts/audit/russianism_eval.py`.

Default model names follow the dispatch brief, with one local bridge-name
substitution: `gemini-3.0-pro` is represented as `gemini-3-pro-preview`.
The bridge passes Gemini model IDs through to `gemini -m`; the repository has
current local references for `gemini-3-pro-preview` but none for
`gemini-3.0-pro`.

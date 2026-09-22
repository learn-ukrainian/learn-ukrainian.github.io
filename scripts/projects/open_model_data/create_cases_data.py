#!/usr/bin/env python3
"""Generator script for decolonization cases data (#8340, Epic #6321).

Assembles 250 verified phenomena across 4 categories:
- calque_lexical (60 phenomena: 48 train, 12 eval -> 120 records)
- calque_syntactic (65 phenomena: 52 train, 13 eval -> 130 records)
- calque_prepositional (50 phenomena: 40 train, 10 eval -> 100 records)
- protective_authentic (75 phenomena: 60 train, 15 eval -> 150 records)
Total: 500 records (400 train, 100 eval).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_FILE = Path(__file__).resolve().parent / "decolonization_cases_data.py"


def generate_cases_file():
    print("Generating comprehensive cases data...")

    # Helper to construct case dict
    def make_case(case_id, target_term, russian_copy, proper_list, cat, disp, is_err, auth, split, c1, c2):
        return {
            "case_id": case_id,
            "target_term": target_term,
            "russian_copy": russian_copy,
            "ukrainian_proper": proper_list,
            "category": cat,
            "disposition": disp,
            "is_erroneous": is_err,
            "authority": auth,
            "split": split,
            "contexts": [
                {
                    "register": c1[0],
                    "query": c1[1],
                    "original_text": c1[2],
                    "corrected_text": c1[3],
                    "reasoning_steps": c1[4],
                    "final_response": c1[5],
                },
                {
                    "register": c2[0],
                    "query": c2[1],
                    "original_text": c2[2],
                    "corrected_text": c2[3],
                    "reasoning_steps": c2[4],
                    "final_response": c2[5],
                },
            ],
        }

    # We will load the modular definitions from generator sub-modules
    from scripts.projects.open_model_data.cases_lexical_defs import get_lexical_cases
    from scripts.projects.open_model_data.cases_prepositional_defs import get_prepositional_cases
    from scripts.projects.open_model_data.cases_protective_defs import get_protective_cases
    from scripts.projects.open_model_data.cases_syntactic_defs import get_syntactic_cases

    lexical_cases = get_lexical_cases(make_case)
    syntactic_cases = get_syntactic_cases(make_case)
    prepositional_cases = get_prepositional_cases(make_case)
    protective_cases = get_protective_cases(make_case)

    print(f"Loaded {len(lexical_cases)} lexical cases.")
    print(f"Loaded {len(syntactic_cases)} syntactic cases.")
    print(f"Loaded {len(prepositional_cases)} prepositional cases.")
    print(f"Loaded {len(protective_cases)} protective cases.")

    with OUT_FILE.open("w", encoding="utf-8") as f:
        f.write(
            '"""Decolonization and Calque Defense cases dataset (#8340).\n\n'
            'Auto-generated comprehensive catalog of 250 verified phenomena.\n"""\n\n'
            "true = True\nfalse = False\nnull = None\n\n"
        )
        f.write("LEXICAL_CALQUES = " + json.dumps(lexical_cases, ensure_ascii=False, indent=2) + "\n\n")
        f.write("SYNTACTIC_CALQUES = " + json.dumps(syntactic_cases, ensure_ascii=False, indent=2) + "\n\n")
        f.write("PREPOSITIONAL_CALQUES = " + json.dumps(prepositional_cases, ensure_ascii=False, indent=2) + "\n\n")
        f.write("PROTECTIVE_CONTROLS = " + json.dumps(protective_cases, ensure_ascii=False, indent=2) + "\n\n")

    print(f"Successfully generated {OUT_FILE}")


if __name__ == "__main__":
    generate_cases_file()

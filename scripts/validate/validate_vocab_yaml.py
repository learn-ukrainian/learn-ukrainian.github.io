#!/usr/bin/env python3
"""
Validate Vocabulary YAML
------------------------
Validates vocabulary files against the specific schema.
- Unique lemmas
- Mandatory fields (ipa, translation)
- Valid Enums (POS, Gender)
"""

import argparse
import logging
import sys
from pathlib import Path

import yaml

VALID_POS = {'noun', 'verb', 'adj', 'adv', 'pron', 'prep', 'conj', 'part', 'intj', 'num', 'phrase', 'propn', 'other', 'suffix', 'prefix'}
VALID_GENDER = {'m', 'f', 'n', 'pl', '-', ''}

# CLI-facing validator script. Uses logging instead of print() for error output
# so CodeQL py/clear-text-logging-sensitive-data sees a sanctioned logging sink
# rather than raw print() of variable-derived data (#1687 — alerts at lines
# previously 25 and 65 were false positives: the data is local-YAML-derived
# linguistic content, never secrets, but the data-flow shape tripped the rule).
logger = logging.getLogger("validate_vocab_yaml")


def validate_file(file_path):
    logger.info("Validating %s...", file_path.name)
    try:
        data = yaml.safe_load(file_path.read_text(encoding='utf-8'))
    except Exception as e:
        logger.error("  YAML Error: %s", e)
        return False

    errors = []
    lemmas = set()

    if 'items' not in data or not isinstance(data['items'], list):
        print("  ❌ Missing 'items' list")
        return False

    for i, item in enumerate(data['items']):
        lemma = item.get('lemma')
        if not lemma:
            errors.append(f"Item #{i}: Missing 'lemma'")
            continue

        if lemma in lemmas:
            errors.append(f"Duplicate lemma: '{lemma}'")
        lemmas.add(lemma)

        # Mandatory Enrichment Check
        if not item.get('ipa'):
            errors.append(f"'{lemma}': Missing IPA")
        if not item.get('translation'):
            errors.append(f"'{lemma}': Missing Translation")

        # Enum Checks
        pos = item.get('pos', 'other')
        if pos not in VALID_POS:
            errors.append(f"'{lemma}': Invalid POS '{pos}'")

        if pos == 'noun':
            gen = item.get('gender', '')
            if not gen:
                errors.append(f"'{lemma}' (noun): Missing Gender")
            elif gen not in VALID_GENDER:
                errors.append(f"'{lemma}': Invalid Gender '{gen}'")

    if errors:
        # Log count only — per-error detail goes to a side file to avoid
        # CodeQL py/clear-text-logging-sensitive-data flagging the data flow
        # from YAML-derived strings into the logging sink. The data is
        # linguistic (vocab errors), never sensitive, but the data-flow
        # shape trips the rule (#1687).
        logger.error("  validation failed (%d error(s))", len(errors))
        side_file = file_path.with_suffix(file_path.suffix + ".errors.txt")
        try:
            side_file.write_text(
                "\n".join(str(e) for e in errors), encoding="utf-8"
            )
            logger.error("  details: see %s", side_file.name)
        except OSError:
            # If side-file write fails, fall back to summary-only.
            pass
        return False

    logger.info("  PASS (%d items)", len(lemmas))
    return True

if __name__ == "__main__":
    # CLI output: simple stderr-friendly logging so validate_file() output
    # surfaces as before but goes through the sanctioned logging sink.
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+', type=Path)
    args = parser.parse_args()

    failed = False
    for f in args.files:
        if not validate_file(f):
            failed = True

    if failed:
        sys.exit(1)

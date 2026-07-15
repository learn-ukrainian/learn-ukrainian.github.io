#!/usr/bin/env python3
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def normalize_space(text: str) -> str:
    return " ".join(text.split())


def derive_word(sentence: str, error_word: str, target: str) -> str:
    # If target has no whitespace, it's already a single word
    if target and not any(c.isspace() for c in target.strip()):
        return target.strip()

    norm_sentence = normalize_space(sentence)
    norm_error = normalize_space(error_word)
    norm_target = normalize_space(target)

    # Find the error_word in the sentence
    idx = norm_sentence.find(norm_error)
    if idx == -1:
        return None

    # Ensure there is exactly one occurrence
    if norm_sentence.find(norm_error, idx + 1) != -1:
        return None

    prefix = norm_sentence[:idx]
    suffix = norm_sentence[idx + len(norm_error) :]

    if norm_target.startswith(prefix) and norm_target.endswith(suffix):
        start_idx = len(prefix)
        end_idx = len(norm_target) - len(suffix)
        middle = norm_target[start_idx:end_idx].strip()
        # Clean any trailing punctuation from the middle word if it got matched, but usually prefix/suffix covers it
        return middle

    return None


def main():
    baseline_path = PROJECT_ROOT / "audit/errorcorrection_baseline_report.json"
    if not baseline_path.exists():
        print(f"Error: {baseline_path} does not exist. Run scanner first.")
        sys.exit(1)

    with open(baseline_path, encoding="utf-8") as f:
        report = json.load(f)

    flagged_files = report.get("flagged_files", {})

    candidates = []
    unique_words_to_verify = set()
    non_derivable_count = 0
    derivable_count = 0

    for file_path, items in flagged_files.items():
        for item in items:
            sentence = item.get("sentence", "")
            error_word = item.get("errorWord")
            correct_form = item.get("correctForm", "")
            options = item.get("options", [])

            # If errorWord is None (sentence has no error), we cannot do a word-level correction
            if error_word is None:
                non_derivable_count += 1
                candidates.append({"file": file_path, "item": item, "status": "non_derivable_no_error_word"})
                continue

            # If errorWord itself has whitespace, we can't do single-word level correction
            if any(c.isspace() for c in error_word.strip()):
                non_derivable_count += 1
                candidates.append(
                    {"file": file_path, "item": item, "status": "non_derivable_error_word_has_whitespace"}
                )
                continue

            derived_correct = derive_word(sentence, error_word, correct_form)
            if not derived_correct or any(c.isspace() for c in derived_correct):
                non_derivable_count += 1
                candidates.append({"file": file_path, "item": item, "status": "non_derivable_correct_form"})
                continue

            # Try to derive options
            derived_options = []
            options_failed = False
            for opt in options:
                derived_opt = derive_word(sentence, error_word, opt)
                if not derived_opt or any(c.isspace() for c in derived_opt):
                    options_failed = True
                    break
                derived_options.append(derived_opt)

            if options_failed:
                non_derivable_count += 1
                candidates.append({"file": file_path, "item": item, "status": "non_derivable_options"})
                continue

            # Successful derivation candidate!
            derivable_count += 1
            candidates.append(
                {
                    "file": file_path,
                    "item": item,
                    "status": "derivable",
                    "derived_correctForm": derived_correct,
                    "derived_options": derived_options,
                }
            )
            unique_words_to_verify.add(derived_correct)
            for opt in derived_options:
                unique_words_to_verify.add(opt)

    print(f"Total flagged items: {len(candidates)}")
    print(f"Derivable items:     {derivable_count}")
    print(f"Non-derivable items: {non_derivable_count}")
    print(f"Unique words to verify in VESUM: {len(unique_words_to_verify)}")

    # Save candidates
    candidates_path = PROJECT_ROOT / "audit/errorcorrection_candidates.json"
    with open(candidates_path, "w", encoding="utf-8") as f:
        json.dump(
            {"candidates": candidates, "unique_words": sorted(list(unique_words_to_verify))},
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"Saved candidates to {candidates_path}")


if __name__ == "__main__":
    main()

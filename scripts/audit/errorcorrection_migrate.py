#!/usr/bin/env python3
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Cache of verified words to avoid duplicate queries
_vesum_cache = {}


def verify_word_in_vesum(word: str) -> bool:
    if not word:
        return False
    if word in _vesum_cache:
        return _vesum_cache[word]

    words_to_query = [word]
    if word[0].isupper():
        words_to_query.append(word.lower())

    try:
        req_data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "verify_words", "arguments": {"words": words_to_query}},
            "id": 1,
        }
        req = urllib.request.Request(
            "http://127.0.0.1:8766/mcp",
            data=json.dumps(req_data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            resp_json = json.loads(response.read().decode("utf-8"))
            content = resp_json.get("result", {}).get("content", [])
            if content:
                text_result = content[0].get("text", "")
                for w in words_to_query:
                    escaped_w = re.escape(w)
                    pattern = rf"-\s*\*\*{escaped_w}\*\*\s*—\s*FOUND"
                    if re.search(pattern, text_result):
                        _vesum_cache[word] = True
                        return True
    except Exception as e:
        print(f"Error querying local MCP server for '{word}': {e}")

    _vesum_cache[word] = False
    return False


def normalize_space(text: str) -> str:
    return " ".join(text.split())


def is_valid_word_chars(word: str) -> bool:
    # Forbidden punctuation characters in a clean word
    forbidden = '.,:;!?()[]{}«»"”“/*_+=|\\<>'
    return not any(c in forbidden for c in word)


def derive_word(sentence: str, error_word: str, target: str) -> str:
    # If target has no whitespace, it is already a single word
    if target and not any(c.isspace() for c in target.strip()):
        return target.strip()

    norm_sentence = normalize_space(sentence)
    norm_error = normalize_space(error_word)
    norm_target = normalize_space(target)

    # Find the error_word in the sentence
    idx = norm_sentence.find(norm_error)
    if idx == -1:
        return None

    # Ensure exactly one occurrence
    if norm_sentence.find(norm_error, idx + 1) != -1:
        return None

    prefix = norm_sentence[:idx]
    suffix = norm_sentence[idx + len(norm_error) :]

    if norm_target.startswith(prefix) and norm_target.endswith(suffix):
        start_idx = len(prefix)
        end_idx = len(norm_target) - len(suffix)
        middle = norm_target[start_idx:end_idx].strip()
        return middle

    return None


def dump_safe_json(data) -> str:
    """Canonical serialisation for JSX template literals."""
    s = json.dumps(data, ensure_ascii=False)
    s = s.replace("\\", "\\\\")
    s = s.replace("`", "\\`")
    s = s.replace("${", "\\${")
    return s


def process_file(file_path: Path, manual_queue: list) -> tuple[int, int]:
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0, 0

    # Regex matching <ErrorCorrection ... items={JSON.parse(`...`)} ... />
    # Group 1: JSX start up to JSON.parse(`
    # Group 2: JSON string content inside backticks
    # Group 3: JSX end from `) onwards
    pattern = r"(<ErrorCorrection\b[\s\S]*?items=\{+JSON\.parse\(`)([\s\S]*?)(`\)\}+[\s\S]*?/>)"

    def replacer(match):
        prefix = match.group(1)
        json_str = match.group(2)
        suffix = match.group(3)

        # Unescape JSX template literal string for standard JSON parsing
        cleaned = json_str.replace('\\"', '"')
        cleaned = cleaned.replace("\\`", "`")
        cleaned = cleaned.replace("\\\\", "\\")

        try:
            items = json.loads(cleaned)
        except Exception as e:
            print(f"Error parsing JSON in replacement block: {e}")
            # Return unchanged if parse fails
            return match.group(0)

        new_items = []
        for idx, item in enumerate(items):
            sentence = item.get("sentence", "")
            error_word = item.get("errorWord")
            correct_form = item.get("correctForm", "")
            options = item.get("options", [])
            explanation = item.get("explanation", "")

            # Check if this item is flagged (correctForm has whitespace)
            is_flagged = correct_form and any(c.isspace() for c in correct_form.strip())

            if not is_flagged:
                new_items.append(item)
                continue

            # Attempt derivation
            reason = "derivable"
            derived_correct = None
            derived_options = []

            if error_word is None:
                reason = "non_derivable_no_error_word"
            elif any(c.isspace() for c in error_word.strip()):
                reason = "non_derivable_error_word_has_whitespace"
            else:
                derived_correct = derive_word(sentence, error_word, correct_form)
                if (
                    not derived_correct
                    or any(c.isspace() for c in derived_correct)
                    or not is_valid_word_chars(derived_correct)
                ):
                    reason = "non_derivable_correct_form"
                else:
                    options_ok = True
                    for opt in options:
                        if opt and not any(c.isspace() for c in opt.strip()):
                            derived_opt = opt.strip()
                        else:
                            derived_opt = derive_word(sentence, error_word, opt)

                        if (
                            not derived_opt
                            or any(c.isspace() for c in derived_opt)
                            or not is_valid_word_chars(derived_opt)
                        ):
                            options_ok = False
                            break
                        derived_options.append(derived_opt)

                    if not options_ok:
                        reason = "non_derivable_options"

            # Check VESUM if derivable
            if reason == "derivable":
                words_to_verify = [derived_correct, *derived_options]
                # Filter duplicates to optimize
                unique_to_verify = list(set(words_to_verify))

                verification_ok = True
                for w in unique_to_verify:
                    if not verify_word_in_vesum(w):
                        verification_ok = False
                        reason = f"vesum_rejected_word_{w}"
                        break

                if verification_ok:
                    # Successfully migrated!
                    new_items.append(
                        {
                            "sentence": sentence,
                            "errorWord": error_word,
                            "correctForm": derived_correct,
                            "options": derived_options,
                            "explanation": explanation,
                        }
                    )
                    continue

            # If not successfully migrated, add to manual queue and exclude from JSX
            manual_queue.append(
                {"file": str(file_path.relative_to(PROJECT_ROOT)), "item_index": idx, "reason": reason, "item": item}
            )

        # Return updated tag
        new_json_str = dump_safe_json(new_items)
        return f"{prefix}{new_json_str}{suffix}"

    new_content = re.sub(pattern, replacer, content)

    if new_content != content:
        try:
            file_path.write_text(new_content, encoding="utf-8")
            return 1, len(manual_queue)
        except Exception as e:
            print(f"Error writing to {file_path}: {e}")

    return 0, len(manual_queue)


def main():
    parser = argparse.ArgumentParser(description="Migrate ErrorCorrection embeds to word-level forms")
    parser.add_argument("--dir", default="site/src/content/docs", help="Directory containing MDX docs")
    parser.add_argument(
        "--queue-output", default="audit/errorcorrection_manual_queue.json", help="Path to output manual queue"
    )
    args = parser.parse_args()

    docs_dir = PROJECT_ROOT / args.dir
    queue_output_file = PROJECT_ROOT / args.queue_output

    if not docs_dir.exists():
        print(f"Error: Directory {docs_dir} does not exist.")
        sys.exit(1)

    mdx_files = sorted(docs_dir.glob("**/*.mdx"))
    manual_queue = []
    updated_files_count = 0

    print(f"Starting migration scan on {len(mdx_files)} MDX files...")

    for f in mdx_files:
        updated, _ = process_file(f, manual_queue)
        if updated:
            updated_files_count += 1

    # Save manual queue
    queue_output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(queue_output_file, "w", encoding="utf-8") as mq_file:
        json.dump(manual_queue, mq_file, indent=2, ensure_ascii=False)

    print("\nMigration Summary:")
    print(f"  Files scanned:                {len(mdx_files)}")
    print(f"  Files updated in-place:       {updated_files_count}")
    print(f"  Items sent to manual queue:   {len(manual_queue)}")
    print(f"  Manual queue saved to:        {queue_output_file.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()

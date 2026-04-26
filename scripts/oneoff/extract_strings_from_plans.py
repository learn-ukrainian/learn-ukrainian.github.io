import json
from pathlib import Path
from typing import Any

import yaml

FILES = [
    "curriculum/l2-uk-en/plans/b1/aspect-in-imperatives.yaml",
    "curriculum/l2-uk-en/plans/b1/aspect-in-narration.yaml",
    "curriculum/l2-uk-en/plans/b1/aspect-in-negation.yaml",
    "curriculum/l2-uk-en/plans/b1/aspect-past-tense.yaml",
    "curriculum/l2-uk-en/plans/b1/b1-baseline-future-aspect.yaml",
    "curriculum/l2-uk-en/plans/b1/b1-baseline-past-present.yaml",
    "curriculum/l2-uk-en/plans/b1/cases-with-ordinal-numerals.yaml",
    "curriculum/l2-uk-en/plans/b1/cases-with-quantity-expressions.yaml",
    "curriculum/l2-uk-en/plans/b1/checkpoint-aspect.yaml",
]


def extract_strings(obj: Any, strings: set[str]) -> None:
    if isinstance(obj, str):
        strings.add(obj)
    elif isinstance(obj, dict):
        for value in obj.values():
            extract_strings(value, strings)
    elif isinstance(obj, list):
        for item in obj:
            extract_strings(item, strings)


def main() -> None:
    strings: set[str] = set()
    for filename in FILES:
        path = Path(filename)
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fp:
            extract_strings(yaml.safe_load(fp), strings)

    Path("strings.json").write_text(
        json.dumps(sorted(strings), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

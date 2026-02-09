import re

def extract_delimited(text: str, start_marker: str = "===CONTENT_START===", end_marker: str = "===CONTENT_END===") -> str:
    pattern = f"{re.escape(start_marker)}(.*?){re.escape(end_marker)}"
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return ""

    content = match.group(1).strip()

    # Handle optional code block wrapping
    code_match = re.search(r"```(?:\w+)?\n(.*?)\n```", content, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()

    return content

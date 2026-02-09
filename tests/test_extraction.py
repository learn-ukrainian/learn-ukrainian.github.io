import os
import tempfile
from pathlib import Path
from scripts.utils.extraction import extract_delimited

def test_extract_delimited():
    content = """
Thinking...
===CONTENT_START===
Hello World
===CONTENT_END===
More thinking...
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        extracted = extract_delimited(temp_path, "===CONTENT_START===", "===CONTENT_END===")
        assert extracted == "Hello World"
    finally:
        os.unlink(temp_path)

def test_extract_delimited_not_found():
    content = "No delimiters here"
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        extracted = extract_delimited(temp_path, "===CONTENT_START===", "===CONTENT_END===")
        assert extracted is None
    finally:
        os.unlink(temp_path)

if __name__ == "__main__":
    test_extract_delimited()
    test_extract_delimited_not_found()
    print("Tests passed!")

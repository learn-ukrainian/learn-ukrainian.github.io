"""
Ukrainian text naturalness checker using Claude/Gemini via prompt.
Evaluates content for natural flow, coherence, and authenticity.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def extract_ukrainian_content(markdown_content: str) -> str:
    """Extract Ukrainian text from markdown, excluding English and code blocks."""
    lines = []
    in_code_block = False

    for line in markdown_content.split('\n'):
        # Skip code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Skip frontmatter
        if line.strip().startswith('---'):
            continue

        # Skip HTML comments
        if '<!--' in line or '-->' in line:
            continue

        # Skip headers with only English
        if line.startswith('#') and not has_cyrillic(line):
            continue

        # Skip pure English paragraphs (common in bilingual content)
        if line.strip() and not has_cyrillic(line):
            continue

        # Keep lines with Ukrainian content
        if has_cyrillic(line):
            # Remove markdown formatting but keep text
            clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)  # Remove links
            clean = re.sub(r'\*\*([^\*]+)\*\*', r'\1', clean)  # Remove bold
            clean = re.sub(r'\*([^\*]+)\*', r'\1', clean)  # Remove italic
            lines.append(clean)

    return '\n'.join(lines)


def has_cyrillic(text: str) -> bool:
    """Check if text contains Cyrillic characters."""
    return bool(re.search(r'[а-яА-ЯіїєґІЇЄҐ]', text))


def check_naturalness_claude(content: str, level: str, context: str = "module") -> Dict[str, Any]:
    """
    Check naturalness using Gemini/Claude via prompt.

    Args:
        content: Ukrainian text to evaluate
        level: CEFR level (A1-C2)
        context: Content type (e.g., "module", "activity", "dialogue")

    Returns:
        Dict with score, status, issues, recommendation
    """
    # Load prompt template
    prompt_file = Path(__file__).parent.parent / "ukrainian_naturalness_checker_prompt.md"
    if not prompt_file.exists():
        return {
            "score": 0,
            "status": "ERROR",
            "issues": ["Naturalness checker prompt file not found"],
            "recommendation": "Check scripts/audit/ukrainian_naturalness_checker_prompt.md exists",
            "rewrite_needed": False
        }

    prompt_template = prompt_file.read_text(encoding='utf-8')

    # Format prompt with actual content
    word_count = len(content.split())
    prompt = prompt_template.format(
        level=level,
        context=context,
        word_count=word_count,
        content=content[:8000]  # Limit to ~8000 chars to fit in context
    )

    # Try gemini CLI first (fastest and cheapest)
    try:
        # Set model to flash for quick evaluation
        project_root = Path(__file__).parent.parent.parent.parent
        gemini_config = project_root / ".config" / "gemini" / "config.yaml"

        # Temporarily set model to flash if config exists
        original_config = None
        if gemini_config.exists():
            original_config = gemini_config.read_text(encoding='utf-8')
            updated_config = re.sub(r'^model:.*$', 'model: gemini-2.0-flash', original_config, flags=re.MULTILINE)
            gemini_config.write_text(updated_config, encoding='utf-8')

        # Call gemini with -y (JSON mode)
        result = subprocess.run(
            ['gemini', '-y'],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_root
        )

        # Restore original config
        if original_config and gemini_config.exists():
            gemini_config.write_text(original_config, encoding='utf-8')

        if result.returncode != 0:
            raise Exception(f"Gemini failed: {result.stderr}")

        output = result.stdout.strip()

        # Extract JSON from output (gemini adds extra text around JSON)
        json_match = None

        # Try to extract JSON from code blocks first
        if '```json' in output:
            json_start = output.find('```json') + 7
            json_end = output.find('```', json_start)
            if json_end > json_start:
                json_str = output[json_start:json_end].strip()
                try:
                    json_match = json.loads(json_str)
                except json.JSONDecodeError:
                    pass

        # Try generic code block if json block failed
        if not json_match and '```' in output:
            json_start = output.find('```') + 3
            json_end = output.find('```', json_start)
            if json_end > json_start:
                json_str = output[json_start:json_end].strip()
                # Skip language identifier if present (e.g., "json\n{...")
                if '\n' in json_str and not json_str.startswith('{'):
                    json_str = json_str[json_str.find('\n'):].strip()
                try:
                    json_match = json.loads(json_str)
                except json.JSONDecodeError:
                    pass

        # Last resort: try parsing entire output
        if not json_match:
            try:
                json_match = json.loads(output)
            except json.JSONDecodeError:
                pass

        if json_match:
            # Ensure status is set correctly based on score
            score = json_match.get('score', 0)
            json_match['status'] = 'PASS' if score >= 8 else 'FAIL'
            return json_match
        else:
            # Failed to parse JSON
            raise Exception(f"Could not parse JSON from gemini output (length: {len(output)})")

    except FileNotFoundError:
        # Gemini not installed
        pass
    except subprocess.TimeoutExpired:
        # Gemini took too long
        pass
    except Exception as e:
        # Other gemini errors
        print(f"Gemini naturalness check failed: {e}", file=sys.stderr)

    # Fallback: mark as PENDING for manual review
    return {
        "score": 0,
        "status": "PENDING",
        "issues": ["Automatic LLM checking unavailable - gemini CLI not found or failed"],
        "recommendation": "Install gemini CLI or manually review for naturalness",
        "rewrite_needed": False
    }


def check_naturalness(markdown_file: Path, level: str) -> Optional[Dict[str, Any]]:
    """
    Main entry point for naturalness checking.

    Args:
        markdown_file: Path to module markdown file
        level: CEFR level

    Returns:
        Naturalness evaluation dict or None if check fails
    """
    try:
        content = markdown_file.read_text(encoding='utf-8')
        ukrainian_text = extract_ukrainian_content(content)

        if not ukrainian_text.strip():
            return {
                "score": 0,
                "status": "ERROR",
                "issues": ["No Ukrainian content found in file"],
                "recommendation": "Check file contains Ukrainian text",
                "rewrite_needed": False
            }

        # Check naturalness
        result = check_naturalness_claude(ukrainian_text, level, context="module")

        return result

    except Exception as e:
        return {
            "score": 0,
            "status": "ERROR",
            "issues": [f"Naturalness check failed: {str(e)}"],
            "recommendation": "Check error logs",
            "rewrite_needed": False
        }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python naturalness.py <markdown_file> <level>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    level = sys.argv[2]

    result = check_naturalness(file_path, level)

    if result:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Naturalness check failed")
        sys.exit(1)

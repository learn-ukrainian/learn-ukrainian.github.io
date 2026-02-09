#!/usr/bin/env python3
"""
Naturalness Check v2 - Dual AI validation (Claude + Gemini)

Sends Ukrainian content to BOTH Claude and Gemini for cross-validation.
Results are appended to the audit review file for full transparency.

Usage:
    python scripts/audit/naturalness_check.py <file.md> [--force]
"""

import json
import re
import subprocess
import sys
import tempfile
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, Optional, Dict

PROJECT_ROOT = Path(__file__).parent.parent.parent

# Structured prompt that returns JSON (reliable parsing)
NATURALNESS_PROMPT = """Evaluate the naturalness of this Ukrainian educational text.

CRITERIA:
1. Natural Ukrainian sentence flow (not translated/robotic)
2. Appropriate register for educational content
3. No awkward phrasing or calques from English/Russian
4. Correct Ukrainian grammar and word order
5. Natural discourse markers and transitions

CONTENT TO EVALUATE:
---
{content}
---

RESPOND WITH ONLY THIS JSON (no markdown, no explanation outside JSON):
{{
  "score": <number 1-10>,
  "status": "<PASS if score >= 8, else FAIL>",
  "feedback_uk": "<2-3 речення українською про якість тексту>",
  "issues": ["<issue1>", "<issue2>"]
}}
"""


def extract_ukrainian_content(md_file_path: str, max_chars: int = 4000) -> str:
    """Extract Ukrainian text content from markdown file."""
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove YAML frontmatter
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

    # Remove code blocks
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)

    # Remove markdown links but keep text
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)

    # Remove image syntax
    content = re.sub(r'!\[.*?\]\([^)]+\)', '', content)

    # Remove HTML comments
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

    # Keep only lines with Cyrillic content
    lines = []
    for line in content.split('\n'):
        if re.match(r'^[\s#\-\*|>]+$', line):
            continue
        if not line.strip():
            continue
        if re.search(r'[\u0400-\u04ff]', line):
            lines.append(line.strip())

    result = '\n'.join(lines)

    # Truncate if too long
    if len(result) > max_chars:
        result = result[:max_chars] + "\n\n[...truncated...]"

    return result


def call_gemini(prompt: str, task_id: str) -> Tuple[str, Dict]:
    """Call Gemini and return raw response + parsed JSON."""
    # Use .venv/bin/python as per AGENTS.md
    python_exe = PROJECT_ROOT / ".venv/bin/python"
    if not python_exe.exists():
        python_exe = sys.executable

    raw_output_log = None
    try:
        tf = tempfile.NamedTemporaryFile(suffix=".txt", prefix=f"gemini-nat-{task_id}-", delete=False)
        raw_output_log = Path(tf.name)
        tf.close()

        with open(raw_output_log, "w") as f:
            result = subprocess.run(
                [
                    str(python_exe),
                    str(PROJECT_ROOT / "scripts" / "ai_agent_bridge.py"),
                    "ask-gemini",
                    prompt,
                    "--task-id", task_id,
                    "--from-model", "claude-opus-4-5-20251101",  # Track sender model
                    "--quiet",
                ],
                stdout=f,
                stderr=subprocess.STDOUT,
                timeout=120,
                cwd=str(PROJECT_ROOT)
            )
            if result.returncode != 0:
                print(f"  ❌ Gemini naturalness call failed with exit code {result.returncode}")

        raw_output = raw_output_log.read_text()

        # Extract JSON from response - handle nested brackets for arrays
        # Find JSON block that contains "score"
        json_match = re.search(r'\{[^{}]*"score"\s*:\s*\d+[^{}]*(?:\[[^\]]*\][^{}]*)?\}', raw_output, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return raw_output, parsed
            except json.JSONDecodeError:
                pass

        # Alternative: find complete JSON block between braces
        json_block = re.search(r'\{\s*"score".*?"issues"\s*:\s*\[[^\]]*\]\s*\}', raw_output, re.DOTALL)
        if json_block:
            try:
                parsed = json.loads(json_block.group())
                return raw_output, parsed
            except json.JSONDecodeError:
                pass

        # Fallback: try to extract score
        score_match = re.search(r'"score"\s*:\s*(\d+)', raw_output)
        if score_match:
            score = int(score_match.group(1))
            return raw_output, {
                "score": score,
                "status": "PASS" if score >= 8 else "FAIL",
                "feedback_uk": "Parsed from non-JSON response",
                "issues": []
            }

        return raw_output, {"score": 0, "status": "ERROR", "feedback_uk": "Could not parse response", "issues": []}

    except subprocess.TimeoutExpired:
        return "TIMEOUT", {"score": 0, "status": "ERROR", "feedback_uk": "Request timed out", "issues": []}
    except Exception as e:
        return str(e), {"score": 0, "status": "ERROR", "feedback_uk": f"Error: {e}", "issues": []}
    finally:
        if raw_output_log and raw_output_log.exists():
            raw_output_log.unlink()


def call_claude_headless(prompt: str, task_id: str) -> Tuple[str, Dict]:
    """
    Call headless Claude via gemini_bridge ask-claude command.
    Returns raw response + parsed JSON.
    """
    # Use .venv/bin/python as per AGENTS.md
    python_exe = PROJECT_ROOT / ".venv/bin/python"
    if not python_exe.exists():
        python_exe = sys.executable

    try:
        result = subprocess.run(
            [
                str(python_exe),
                str(PROJECT_ROOT / "scripts" / "ai_agent_bridge.py"),
                "ask-claude",
                prompt,
                "--task-id", task_id,
                "--new-session",  # Fresh session for each evaluation
                "--from", "claude",  # Claude (this session) asking Claude (headless)
                "--from-model", "claude-opus-4-5-20251101",  # Current model
                "--to-model", "claude-sonnet-4"  # Headless typically uses sonnet
            ],
            capture_output=True,
            text=True,
            timeout=180,  # Claude may take longer
            cwd=str(PROJECT_ROOT)
        )
        if result.returncode != 0:
            print(f"  ❌ Claude naturalness call failed with exit code {result.returncode}")

        raw_output = result.stdout + result.stderr

        # Extract JSON from response - same logic as Gemini
        json_match = re.search(r'\{[^{}]*"score"\s*:\s*\d+[^{}]*(?:\[[^\]]*\][^{}]*)?\}', raw_output, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return raw_output, parsed
            except json.JSONDecodeError:
                pass

        # Alternative: find complete JSON block
        json_block = re.search(r'\{\s*"score".*?"issues"\s*:\s*\[[^\]]*\]\s*\}', raw_output, re.DOTALL)
        if json_block:
            try:
                parsed = json.loads(json_block.group())
                return raw_output, parsed
            except json.JSONDecodeError:
                pass

        # Fallback: try to extract score from JSON-like
        score_match = re.search(r'"score"\s*:\s*(\d+)', raw_output)
        if score_match:
            score = int(score_match.group(1))
            return raw_output, {
                "score": score,
                "status": "PASS" if score >= 8 else "FAIL",
                "feedback_uk": "Parsed from non-JSON response",
                "issues": []
            }

        # Fallback for Claude: parse natural language "Score: X/10" or "**Score: X/10**"
        nl_score = re.search(r'\*?\*?[Ss]core:?\*?\*?\s*(\d+)/10', raw_output)
        if nl_score:
            score = int(nl_score.group(1))
            # Try to extract feedback from natural language
            feedback = ""
            feedback_match = re.search(r'(?:PASS|FAIL)[^\n]*[-–]\s*(.+?)(?:\n\n|I also|$)', raw_output, re.DOTALL)
            if feedback_match:
                feedback = feedback_match.group(1).strip()[:300]
            return raw_output, {
                "score": score,
                "status": "PASS" if score >= 8 else "FAIL",
                "feedback_uk": feedback or "Parsed from natural language response",
                "issues": []
            }

        return raw_output, {"score": 0, "status": "ERROR", "feedback_uk": "Could not parse response", "issues": []}

    except subprocess.TimeoutExpired:
        return "TIMEOUT (180s)", {"score": 0, "status": "ERROR", "feedback_uk": "Request timed out", "issues": []}
    except Exception as e:
        return str(e), {"score": 0, "status": "ERROR", "feedback_uk": f"Error: {e}", "issues": []}


def append_to_audit(audit_path: Path, gemini_raw: str, gemini_parsed: Dict,
                    claude_raw: str, claude_parsed: Dict, timestamp: str) -> None:
    """Append naturalness results to audit review file."""

    section = f"""

---

## Naturalness Check (Dual AI Validation)
**Timestamp:** {timestamp}

### Gemini Evaluation
**Score:** {gemini_parsed.get('score', 'N/A')}/10 | **Status:** {gemini_parsed.get('status', 'N/A')}

**Feedback:** {gemini_parsed.get('feedback_uk', 'N/A')}

**Issues:** {', '.join(gemini_parsed.get('issues', [])) or 'None'}

<details>
<summary>Raw Gemini Response</summary>

```
{gemini_raw[-2000:] if len(gemini_raw) > 2000 else gemini_raw}
```

</details>

### Claude Evaluation
**Score:** {claude_parsed.get('score', 'N/A')}/10 | **Status:** {claude_parsed.get('status', 'N/A')}

**Feedback:** {claude_parsed.get('feedback_uk', 'N/A')}

<details>
<summary>Raw Claude Response</summary>

```
{claude_raw[-2000:] if len(claude_raw) > 2000 else claude_raw}
```

</details>

### Consensus
"""

    # Calculate consensus
    g_score = gemini_parsed.get('score', 0)
    c_score = claude_parsed.get('score', 0)

    if c_score > 0 and g_score > 0:
        avg = (g_score + c_score) / 2
        section += f"**Average:** {avg:.1f}/10 | **Gemini:** {g_score} | **Claude:** {c_score}\n"
        if abs(g_score - c_score) > 2:
            section += "⚠️ **Disagreement detected** - scores differ by more than 2 points\n"
    elif g_score > 0:
        section += f"**Gemini only:** {g_score}/10 (Claude skipped)\n"
    else:
        section += "**No valid scores obtained**\n"

    # Append to file
    with open(audit_path, 'a', encoding='utf-8') as f:
        f.write(section)


def update_meta_naturalness(meta_path: Path, score: int, status: str, feedback: str, timestamp: str) -> None:
    """Update meta.yaml with naturalness result."""
    if not meta_path.exists():
        return

    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = yaml.safe_load(f) or {}

    meta['naturalness'] = {
        'score': score,
        'status': status,
        'feedback': feedback,
        'checked_by': 'gemini-auto',
        'checked_at': timestamp
    }

    with open(meta_path, 'w', encoding='utf-8') as f:
        yaml.dump(meta, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def check_naturalness(
    md_file_path: str,
    update_meta: bool = True,
    force: bool = False
) -> Tuple[int, str]:
    """
    Check naturalness with dual AI validation.

    Returns (score, status) - uses Gemini score as primary.
    """
    md_path = Path(md_file_path)
    meta_path = md_path.parent / 'meta' / (md_path.stem + '.yaml')
    audit_path = md_path.parent / 'audit' / (md_path.stem + '-review.md')

    # Check if already evaluated (unless force)
    if not force and meta_path.exists():
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = yaml.safe_load(f)
            if meta and 'naturalness' in meta:
                nat = meta['naturalness']
                if nat.get('status') in ('PASS', 'FAIL') and nat.get('checked_at'):
                    print(f"  ℹ️ Already evaluated: {nat.get('score')}/10 at {nat.get('checked_at')}")
                    return nat.get('score', 0), nat.get('status', 'PASS')
        except Exception:
            pass

    print(f"  🔍 Checking naturalness (dual AI)...")

    # Extract content
    content = extract_ukrainian_content(md_file_path)
    if len(content) < 100:
        print(f"  ⚠️ Insufficient content for naturalness check")
        return 0, "PENDING"

    # Build prompt
    prompt = NATURALNESS_PROMPT.format(content=content)
    timestamp = datetime.now(timezone.utc).isoformat()
    task_id = f"naturalness-{md_path.stem}-{int(datetime.now().timestamp())}"

    # Call Gemini
    print(f"  📤 Sending to Gemini...")
    gemini_raw, gemini_parsed = call_gemini(prompt, task_id)
    print(f"  📥 Gemini: {gemini_parsed.get('score', '?')}/10 - {gemini_parsed.get('status', '?')}")

    # Call Claude (headless)
    print(f"  📤 Sending to Claude (headless)...")
    claude_task_id = f"naturalness-claude-{md_path.stem}-{int(datetime.now().timestamp())}"
    claude_raw, claude_parsed = call_claude_headless(prompt, claude_task_id)
    print(f"  📥 Claude: {claude_parsed.get('score', '?')}/10 - {claude_parsed.get('status', '?')}")

    # Append to audit file
    if audit_path.exists():
        print(f"  📝 Appending to audit file...")
        append_to_audit(audit_path, gemini_raw, gemini_parsed, claude_raw, claude_parsed, timestamp)

    # Use Gemini score as primary
    score = gemini_parsed.get('score', 0)
    status = gemini_parsed.get('status', 'PENDING')
    feedback = gemini_parsed.get('feedback_uk', '')

    # Update meta
    if update_meta and score > 0:
        update_meta_naturalness(meta_path, score, status, feedback, timestamp)
        print(f"  ✅ Updated meta: {score}/10 ({status})")

    return score, status


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Check naturalness with dual AI validation')
    parser.add_argument('file', help='Path to markdown file')
    parser.add_argument('--no-update', action='store_true', help='Do not update meta.yaml')
    parser.add_argument('--force', action='store_true', help='Re-check even if already evaluated')

    args = parser.parse_args()

    score, status = check_naturalness(
        args.file,
        update_meta=not args.no_update,
        force=args.force
    )

    print(f"\nResult: {score}/10 ({status})")
    sys.exit(0 if status == 'PASS' else 1)

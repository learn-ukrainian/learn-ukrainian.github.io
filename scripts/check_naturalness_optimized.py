#!/usr/bin/env python3
"""
Optimized naturalness checker for A1/A2 activities.
Uses persistent MCP subprocess to avoid spawn overhead.
"""

import yaml
import json
import sys
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

class MCPClient:
    """Persistent MCP client that keeps subprocess alive."""

    def __init__(self, server_path: Path):
        self.server_path = server_path
        self.proc = None
        self.msg_id = 0

    def start(self):
        """Start MCP server subprocess."""
        self.proc = subprocess.Popen(
            [sys.executable, str(self.server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Send initialize
        self.msg_id += 1
        init_req = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "naturalness-checker", "version": "2.0.0"}
            }
        }

        self.proc.stdin.write(json.dumps(init_req) + "\n")
        self.proc.stdin.flush()

        # Read initialize response
        self.proc.stdout.readline()

    def check_naturalness(self, text: str, level: str, context: str) -> Dict[str, Any]:
        """Check naturalness via MCP tool."""
        if not self.proc:
            raise RuntimeError("MCP client not started")

        self.msg_id += 1
        tool_req = {
            "jsonrpc": "2.0",
            "id": self.msg_id,
            "method": "tools/call",
            "params": {
                "name": "check_naturalness",
                "arguments": {
                    "content": text,
                    "level": level,
                    "context": context
                }
            }
        }

        try:
            self.proc.stdin.write(json.dumps(tool_req) + "\n")
            self.proc.stdin.flush()

            response_line = self.proc.stdout.readline()
            response = json.loads(response_line)

            if "result" in response and "content" in response["result"]:
                content = response["result"]["content"]
                if content and len(content) > 0:
                    return json.loads(content[0]["text"])

            return {"score": 0, "issues": ["No valid response"], "recommendation": "", "rewrite_needed": True}

        except Exception as e:
            return {"score": 0, "issues": [f"Error: {str(e)}"], "recommendation": "", "rewrite_needed": True}

    def stop(self):
        """Stop MCP server subprocess."""
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=5)


def extract_correct_text(activity: Dict[str, Any], activity_type: str) -> List[Tuple[str, str]]:
    """
    Extract Ukrainian text with CORRECT answers filled in.
    Returns list of (context, text) tuples.
    """
    texts = []

    if activity_type == "cloze":
        if "passage" in activity:
            passage = activity["passage"]
            # Replace {option1|option2|option3} with first option (usually correct)
            # This is a simplification - ideally we'd track which is correct
            clean_passage = re.sub(r'\{([^|}]+)(?:\|[^}]+)*\}', r'\1', passage)
            texts.append((
                f"cloze: {activity.get('title', 'untitled')}",
                clean_passage
            ))

    elif activity_type == "fill-in":
        if "items" in activity:
            # Combine all sentences with correct answers
            sentences = []
            for item in activity["items"]:
                if "sentence" in item and "answer" in item:
                    sentence = item["sentence"].replace("_____", item["answer"]).replace("___", item["answer"])
                    sentences.append(sentence)

            if sentences:
                combined_text = " ".join(sentences)
                texts.append((
                    f"fill-in: {activity.get('title', 'untitled')} ({len(sentences)} items)",
                    combined_text
                ))

    elif activity_type == "true-false":
        if "items" in activity:
            statements = []
            for item in activity["items"]:
                if "statement" in item:
                    statements.append(item["statement"])

            if statements:
                combined_text = " ".join(statements)
                texts.append((
                    f"true-false: {activity.get('title', 'untitled')} ({len(statements)} items)",
                    combined_text
                ))

    elif activity_type == "unjumble":
        if "items" in activity:
            answers = []
            for item in activity["items"]:
                if "answer" in item:
                    answers.append(item["answer"])

            if answers:
                combined_text = " ".join(answers)
                texts.append((
                    f"unjumble: {activity.get('title', 'untitled')} ({len(answers)} items)",
                    combined_text
                ))

    return texts


def scan_activity_file(yaml_file: Path, mcp_client: MCPClient, level: str, threshold: int = 8) -> List[Dict[str, Any]]:
    """Scan single activity file and return flagged results."""
    flagged = []

    try:
        with open(yaml_file, "r", encoding="utf-8") as f:
            activities = yaml.safe_load(f)

        if not isinstance(activities, list):
            return flagged

        for idx, activity in enumerate(activities):
            activity_type = activity.get("type", "unknown")

            # Skip non-prose activity types
            if activity_type in ["match-up", "quiz", "select", "group-sort", "anagram"]:
                continue

            # Extract text with correct answers
            texts = extract_correct_text(activity, activity_type)

            for context, text in texts:
                # Skip very short texts
                if len(text.strip()) < 15:
                    continue

                # Check naturalness
                result = mcp_client.check_naturalness(text, level.upper(), context)

                if result["score"] < threshold:
                    flagged.append({
                        "file": yaml_file.name,
                        "level": level.upper(),
                        "activity_index": idx,
                        "activity_type": activity_type,
                        "context": context,
                        "text": text[:200] + "..." if len(text) > 200 else text,
                        "score": result["score"],
                        "issues": result["issues"],
                        "recommendation": result["recommendation"],
                        "rewrite_needed": result["rewrite_needed"]
                    })

        return flagged

    except Exception as e:
        print(f"      ERROR: {e}")
        return flagged


def main():
    # MCP server path
    mcp_server = Path(__file__).parent.parent / ".mcp" / "servers" / "ukrainian-validator" / "server.py"

    # Quality threshold
    THRESHOLD = 8

    print(f"\n{'='*70}")
    print(f"A1/A2 NATURALNESS SCAN")
    print(f"Quality threshold: Score >= {THRESHOLD}")
    print(f"{'='*70}\n")

    # Start persistent MCP client
    print("Starting MCP server...")
    mcp_client = MCPClient(mcp_server)
    mcp_client.start()
    print("✓ MCP server ready\n")

    all_flagged = []
    total_files = 0
    total_checked = 0

    for level in ["a1", "a2"]:
        activities_dir = Path(f"curriculum/l2-uk-en/{level}/activities")
        yaml_files = sorted(activities_dir.glob("*.yaml"))

        print(f"\n{'='*70}")
        print(f"Scanning {level.upper()} ({len(yaml_files)} files)")
        print(f"{'='*70}\n")

        for yaml_file in yaml_files:
            print(f"  {yaml_file.name:45s} ", end="", flush=True)

            flagged = scan_activity_file(yaml_file, mcp_client, level, THRESHOLD)
            total_files += 1

            if flagged:
                total_checked += len(flagged)
                all_flagged.extend(flagged)
                print(f"⚠️  {len(flagged):2d} flagged")
            else:
                print(f"✓ OK")

    # Stop MCP client
    print("\nStopping MCP server...")
    mcp_client.stop()
    print("✓ MCP server stopped\n")

    # Print summary
    print(f"\n{'='*70}")
    print(f"SCAN COMPLETE")
    print(f"{'='*70}\n")
    print(f"Files scanned: {total_files}")
    print(f"Activities checked: {total_checked}")
    print(f"Flagged (score < {THRESHOLD}): {len(all_flagged)}\n")

    if all_flagged:
        # Group by score
        by_score = {}
        for item in all_flagged:
            score = item["score"]
            by_score.setdefault(score, []).append(item)

        print("Distribution by score:")
        for score in sorted(by_score.keys()):
            count = len(by_score[score])
            print(f"  Score {score}: {count:3d} activities")
        print()

        # Save detailed results
        output_file = Path("scripts/naturalness_scan_results.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_flagged, f, ensure_ascii=False, indent=2)

        print(f"✓ Detailed results saved to: {output_file}\n")

        # Print worst offenders
        print(f"\n{'='*70}")
        print(f"WORST OFFENDERS (Score < 5)")
        print(f"{'='*70}\n")

        worst = [item for item in all_flagged if item["score"] < 5]
        for i, item in enumerate(worst[:10], 1):
            print(f"{i}. {item['file']} - {item['context']}")
            print(f"   Score: {item['score']}/10")
            print(f"   Text: {item['text'][:150]}...")
            print(f"   Issues: {', '.join(item['issues'][:2])}")
            print()

        if len(worst) > 10:
            print(f"   ... and {len(worst) - 10} more with score < 5\n")
    else:
        print("✅ All activities passed quality check!\n")

    return 0 if not all_flagged else 1


if __name__ == "__main__":
    sys.exit(main())

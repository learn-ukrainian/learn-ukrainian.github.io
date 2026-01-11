#!/usr/bin/env python3
"""
Check Ukrainian text in A1/A2 activities for naturalness using MCP tool.
Flags content with naturalness scores < 7.
"""

import yaml
import json
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# MCP server path
MCP_SERVER = Path(__file__).parent.parent / ".mcp" / "servers" / "ukrainian-validator" / "server.py"

def extract_ukrainian_text(activity: Dict[str, Any], activity_type: str) -> List[tuple[str, str]]:
    """Extract Ukrainian text from activity. Returns list of (context, text) tuples."""
    texts = []

    if activity_type == "mark-the-words":
        # Extract the main text
        if "text" in activity:
            texts.append((f"mark-the-words: {activity.get('title', 'untitled')}", activity["text"]))

    elif activity_type == "cloze":
        # Extract passage
        if "passage" in activity:
            # Remove inline options {option1|option2|option3}
            passage = activity["passage"]
            import re
            clean_passage = re.sub(r'\{[^}]+\}', '___', passage)
            texts.append((f"cloze: {activity.get('title', 'untitled')}", clean_passage))

    elif activity_type == "fill-in":
        # Extract sentences
        if "items" in activity:
            for i, item in enumerate(activity["items"]):
                if "sentence" in item:
                    sentence = item["sentence"].replace("_____", "___")
                    texts.append((f"fill-in #{i+1}: {activity.get('title', 'untitled')}", sentence))

    elif activity_type == "true-false":
        # Extract statements
        if "items" in activity:
            for i, item in enumerate(activity["items"]):
                if "statement" in item:
                    texts.append((f"true-false #{i+1}: {activity.get('title', 'untitled')}", item["statement"]))

    elif activity_type == "unjumble":
        # Extract answers
        if "items" in activity:
            for i, item in enumerate(activity["items"]):
                if "answer" in item:
                    texts.append((f"unjumble #{i+1}: {activity.get('title', 'untitled')}", item["answer"]))

    return texts

def check_text_naturalness(text: str, level: str, context: str, msg_id: int = 1) -> Dict[str, Any]:
    """Check naturalness of Ukrainian text using MCP tool via JSON-RPC."""

    # Initialize request
    init_request = {
        "jsonrpc": "2.0",
        "id": msg_id,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "naturalness-checker", "version": "1.0.0"}
        }
    }

    # Tool call request
    tool_request = {
        "jsonrpc": "2.0",
        "id": msg_id + 1,
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
        # Start MCP server
        proc = subprocess.Popen(
            [sys.executable, str(MCP_SERVER)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send initialize
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()

        # Read initialize response
        init_response = proc.stdout.readline()

        # Send tool call
        proc.stdin.write(json.dumps(tool_request) + "\n")
        proc.stdin.flush()

        # Read tool response
        tool_response = json.loads(proc.stdout.readline())

        proc.terminate()

        if "result" in tool_response and "content" in tool_response["result"]:
            content = tool_response["result"]["content"]
            if content and len(content) > 0:
                return json.loads(content[0]["text"])

        return {"score": 0, "issues": ["No valid response"], "recommendation": "", "rewrite_needed": True}

    except Exception as e:
        return {"score": 0, "issues": [f"Error: {str(e)}"], "recommendation": "", "rewrite_needed": True}

def main():
    levels = ["a1", "a2"]
    flagged_results = []
    msg_id_counter = 1

    for level in levels:
        activities_dir = Path(f"curriculum/l2-uk-en/{level}/activities")
        yaml_files = sorted(activities_dir.glob("*.yaml"))

        print(f"\n{'='*60}")
        print(f"Checking {level.upper()} activities ({len(yaml_files)} files)")
        print(f"{'='*60}\n")

        for yaml_file in yaml_files:
            print(f"Processing: {yaml_file.name}...", end=" ", flush=True)

            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    activities = yaml.safe_load(f)

                if not isinstance(activities, list):
                    print("SKIP (not a list)")
                    continue

                file_flagged = []

                for idx, activity in enumerate(activities):
                    activity_type = activity.get("type", "unknown")

                    # Extract text from this activity
                    texts = extract_ukrainian_text(activity, activity_type)

                    for context, text in texts:
                        if len(text.strip()) < 10:  # Skip very short texts
                            continue

                        # Check naturalness
                        result = check_text_naturalness(text, level.upper(), context, msg_id_counter)
                        msg_id_counter += 2

                        if result["score"] < 7:
                            file_flagged.append({
                                "file": yaml_file.name,
                                "activity_index": idx,
                                "activity_type": activity_type,
                                "context": context,
                                "text": text[:100] + "..." if len(text) > 100 else text,
                                "score": result["score"],
                                "issues": result["issues"],
                                "recommendation": result["recommendation"],
                                "rewrite_needed": result["rewrite_needed"]
                            })

                if file_flagged:
                    flagged_results.extend(file_flagged)
                    print(f"⚠️  FLAGGED ({len(file_flagged)} issues)")
                else:
                    print("✓ OK")

            except Exception as e:
                print(f"ERROR: {e}")
                continue

    # Print summary report
    print(f"\n{'='*60}")
    print(f"NATURALNESS CHECK SUMMARY")
    print(f"{'='*60}\n")

    if not flagged_results:
        print("✅ All activities passed naturalness check (score >= 7)")
    else:
        print(f"⚠️  Found {len(flagged_results)} potentially robotic/unnatural text snippets:\n")

        for i, result in enumerate(flagged_results, 1):
            print(f"{i}. {result['file']} - {result['context']}")
            print(f"   Score: {result['score']}/10")
            print(f"   Text: {result['text']}")
            print(f"   Issues: {', '.join(result['issues'])}")
            print(f"   Recommendation: {result['recommendation']}")
            print(f"   Rewrite needed: {result['rewrite_needed']}")
            print()

    # Save results to JSON
    output_file = Path("scripts/naturalness_check_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(flagged_results, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to: {output_file}")

    return 0 if not flagged_results else 1

if __name__ == "__main__":
    sys.exit(main())

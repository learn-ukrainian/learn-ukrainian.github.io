#!/usr/bin/env python3
"""
Test script for Ukrainian Validator MCP Server

This script tests the MCP server directly without requiring Claude Code.
It simulates MCP tool calls to verify the server is working correctly.
"""

import json
import subprocess
import sys
from pathlib import Path

def test_mcp_server():
    """Test the Ukrainian validator MCP server."""

    print("=" * 80)
    print("Ukrainian Validator MCP Server Test")
    print("=" * 80)
    print()

    # Step 1: Check if Ukrainian prompt file exists
    prompt_path = Path("scripts/audit/ukrainian_grammar_validator_prompt.md")
    print(f"1. Checking Ukrainian validator prompt...")
    if prompt_path.exists():
        print(f"   ✅ Found: {prompt_path} ({prompt_path.stat().st_size} bytes)")
    else:
        print(f"   ❌ Not found: {prompt_path}")
        return False
    print()

    # Step 2: Check if gemini CLI is accessible
    print("2. Checking gemini CLI availability...")
    try:
        result = subprocess.run(
            ['which', 'gemini'],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            gemini_path = result.stdout.decode().strip()
            print(f"   ✅ gemini found at: {gemini_path}")
        else:
            print(f"   ❌ gemini not found in PATH")
            print("      The MCP server requires 'gemini' command")
            return False
    except Exception as e:
        print(f"   ❌ Error checking gemini: {e}")
        return False
    print()

    # Step 3: Test MCP server tools/list
    print("3. Testing MCP server tools/list...")
    server_path = Path(".mcp/servers/ukrainian-validator/server.py")

    try:
        # Send tools/list request
        request = {"method": "tools/list", "params": {}}

        process = subprocess.Popen(
            ['.venv/bin/python', str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(input=json.dumps(request) + "\n", timeout=5)

        if stderr:
            print(f"   Server logs: {stderr}")

        response = json.loads(stdout)

        if 'tools' in response:
            print(f"   ✅ Server responded with {len(response['tools'])} tool(s)")
            for tool in response['tools']:
                print(f"      - {tool['name']}: {tool['description']}")
        else:
            print(f"   ❌ Unexpected response: {response}")
            return False

    except subprocess.TimeoutExpired:
        print("   ❌ Server timeout")
        return False
    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON response: {e}")
        print(f"      Raw output: {stdout}")
        return False
    except Exception as e:
        print(f"   ❌ Error testing server: {e}")
        return False
    print()

    # Step 4: Test validation with sample content
    print("4. Testing Ukrainian validation with sample content...")

    sample_content = """
# Тестовий модуль

Селяни любили кушать борщ. Це робить сенс у контексті традицій.

Я допомагав мій брат на городі.
"""

    try:
        request = {
            "method": "tools/call",
            "params": {
                "name": "validate_ukrainian",
                "arguments": {
                    "content": sample_content,
                    "level": "B2"
                }
            }
        }

        process = subprocess.Popen(
            ['.venv/bin/python', str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(input=json.dumps(request) + "\n", timeout=60)

        if stderr:
            print(f"   Server logs: {stderr}")

        response = json.loads(stdout)

        if 'content' in response:
            result_text = response['content'][0]['text']
            result = json.loads(result_text)

            print(f"   ✅ Validation completed")
            print(f"      Response structure:")

            if 'violations' in result:
                print(f"      - violations: {len(result.get('violations', []))} found")
                for v in result['violations'][:3]:  # Show first 3
                    print(f"         * [{v['type']}] {v.get('error', 'N/A')} → {v.get('correction', 'N/A')}")

            if 'summary' in result:
                summary = result['summary']
                print(f"      - summary:")
                print(f"         * total: {summary.get('total', 0)}")
                print(f"         * recommendation: {summary.get('recommendation', 'N/A')}")

            if 'error' in result:
                print(f"      ⚠️  Error in validation: {result['error']}")
                if 'help' in result:
                    print(f"         Help: {result['help']}")
        else:
            print(f"   ❌ Unexpected response: {response}")
            return False

    except subprocess.TimeoutExpired:
        print("   ❌ Validation timeout (>60s)")
        print("      This might be normal if gemini-cli is slow")
        return False
    except json.JSONDecodeError as e:
        print(f"   ❌ Invalid JSON response: {e}")
        print(f"      Raw output: {stdout[:500]}")
        return False
    except Exception as e:
        print(f"   ❌ Error during validation: {e}")
        return False
    print()

    print("=" * 80)
    print("✅ MCP Server Setup Complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Restart Claude Code to load MCP configuration")
    print("2. Try: /validate-ukrainian curriculum/l2-uk-en/b2/[module].md")
    print("3. Or edit a B1+ module - automatic validation will trigger")
    print()

    return True


if __name__ == '__main__':
    success = test_mcp_server()
    sys.exit(0 if success else 1)

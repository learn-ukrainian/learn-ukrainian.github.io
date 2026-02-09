#!/bin/bash
# scripts/mock_gemini.sh

# Mock Gemini CLI for CI/CD

# If called with -y (JSON mode), return a standard success response
if [[ "$*" == *"-y"* ]]; then
  echo '{"score": 9, "status": "PASS", "issues": [], "recommendation": "Mocked naturalness: Excellent Ukrainian.", "rewrite_needed": false}'
  exit 0
fi

# Generic response for other calls
echo "Mocked Gemini Response for: $*"
echo "I am a mock Gemini CLI used for CI testing."

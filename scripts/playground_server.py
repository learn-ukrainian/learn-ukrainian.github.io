#!/usr/bin/env python3
"""
Playground Server - Launch the FastAPI server for playground dashboards.

Usage:
    python scripts/playground_server.py [--port PORT] [--reload]

This starts a uvicorn server serving:
- Playground HTML files from /playgrounds/
- API endpoints at /api/*

Default: http://localhost:8765
"""

import argparse
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(description="Start the playground API server")
    parser.add_argument("--port", type=int, default=8765, help="Port to run on (default: 8765)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes")
    args = parser.parse_args()

    import uvicorn

    print(f"\n🎮 Starting Playground Server")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"   API: http://{args.host}:{args.port}/api/status/levels")
    print(f"   Reload: {'enabled' if args.reload else 'disabled'}")
    print()

    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=["scripts/api"] if args.reload else None,
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
VESUM Client - Python interface to nlp_uk Docker container for Ukrainian word validation.

This client manages the nlp_uk Docker container and provides word validation
against the VESUM (ВЕСУМ) dictionary - the largest Ukrainian morphological database.

Usage:
    from scripts.audit.vesum_client import VesumClient

    client = VesumClient()

    # Start container if needed
    if not client.is_running():
        client.start()

    # Validate words
    result = client.validate_words(["привіт", "кушать", "їсти"])
    print(result.invalid_words)  # ["кушать"]

    # Stop container when done (free RAM)
    client.stop()

CLI Usage:
    python scripts/audit/vesum_client.py start
    python scripts/audit/vesum_client.py stop
    python scripts/audit/vesum_client.py status
    python scripts/audit/vesum_client.py validate "привіт" "кушать" "їсти"
"""

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error

# Default settings
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8899
DEFAULT_TIMEOUT = 60  # seconds to wait for container startup
DOCKER_COMPOSE_DIR = Path(__file__).parent.parent.parent / "docker" / "nlp_uk"
CONTAINER_NAME = "nlp-uk-vesum"


@dataclass
class ValidationResult:
    """Result of word validation against VESUM."""
    results: dict  # word -> {valid: bool, pos: str, lemma: str, ...}
    invalid_words: list[str]
    valid_count: int
    invalid_count: int

    @property
    def all_valid(self) -> bool:
        return self.invalid_count == 0


class VesumClient:
    """Client for VESUM word validation via nlp_uk Docker container."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    def is_running(self) -> bool:
        """Check if the nlp_uk container is running and healthy."""
        try:
            result = self._request("GET", "/health", timeout=5)
            return result.get("status") == "ok"
        except Exception:
            return False

    def start(self, wait: bool = True, timeout: int = DEFAULT_TIMEOUT) -> bool:
        """
        Start the nlp_uk Docker container.

        Args:
            wait: If True, wait for container to be healthy before returning
            timeout: Maximum seconds to wait for startup

        Returns:
            True if container started successfully
        """
        if self.is_running():
            return True

        # Check if docker-compose.yml exists
        compose_file = DOCKER_COMPOSE_DIR / "docker-compose.yml"
        if not compose_file.exists():
            raise FileNotFoundError(
                f"Docker Compose file not found: {compose_file}\n"
                "Run from project root or build container first."
            )

        # Start with docker compose
        try:
            subprocess.run(
                ["docker", "compose", "up", "-d", "--build"],
                cwd=DOCKER_COMPOSE_DIR,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to start container: {e.stderr}")

        if not wait:
            return True

        # Wait for container to be healthy
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_running():
                return True
            time.sleep(2)

        raise TimeoutError(
            f"Container did not become healthy within {timeout} seconds.\n"
            f"Check logs with: docker compose logs -f (in {DOCKER_COMPOSE_DIR})"
        )

    def stop(self) -> bool:
        """Stop the nlp_uk Docker container to free RAM."""
        compose_file = DOCKER_COMPOSE_DIR / "docker-compose.yml"
        if not compose_file.exists():
            return False

        try:
            subprocess.run(
                ["docker", "compose", "down"],
                cwd=DOCKER_COMPOSE_DIR,
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def validate_words(self, words: list[str]) -> ValidationResult:
        """
        Validate Ukrainian words against VESUM dictionary.

        Args:
            words: List of Ukrainian words to validate

        Returns:
            ValidationResult with valid/invalid word info

        Raises:
            RuntimeError: If container is not running
        """
        if not words:
            return ValidationResult(
                results={},
                invalid_words=[],
                valid_count=0,
                invalid_count=0
            )

        if not self.is_running():
            raise RuntimeError(
                "VESUM container is not running. Start it with:\n"
                "  python scripts/audit/vesum_client.py start\n"
                "Or use --no-vesum flag to skip VESUM validation."
            )

        result = self._request("POST", "/validate", {"words": words})

        return ValidationResult(
            results=result.get("results", {}),
            invalid_words=result.get("invalid_words", []),
            valid_count=result.get("valid_count", 0),
            invalid_count=result.get("invalid_count", 0)
        )

    def tag_text(self, text: str) -> dict:
        """
        Tag Ukrainian text with POS and morphological info.

        Args:
            text: Ukrainian text to tag

        Returns:
            Dict with tagged_xml and unknown_words
        """
        if not self.is_running():
            raise RuntimeError("VESUM container is not running")

        return self._request("POST", "/tag", {"text": text})

    def lemmatize(self, words: list[str]) -> dict[str, str]:
        """
        Get lemmas (base forms) for Ukrainian words.

        Args:
            words: List of words to lemmatize

        Returns:
            Dict mapping each word to its lemma
        """
        if not self.is_running():
            raise RuntimeError("VESUM container is not running")

        result = self._request("POST", "/lemmatize", {"words": words})
        return result.get("lemmas", {})

    def _request(self, method: str, path: str, data: dict = None, timeout: int = 30) -> dict:
        """Make HTTP request to the nlp_uk API."""
        url = f"{self.base_url}{path}"

        if data:
            data_bytes = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={'Content-Type': 'application/json'},
                method=method
            )
        else:
            req = urllib.request.Request(url, method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.URLError as e:
            raise ConnectionError(f"Cannot connect to VESUM service: {e}")


def main():
    """CLI interface for VESUM client."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    client = VesumClient()

    if command == "start":
        print("Starting nlp_uk container...")
        try:
            client.start()
            print("Container started and healthy!")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "stop":
        print("Stopping nlp_uk container...")
        if client.stop():
            print("Container stopped. RAM freed!")
        else:
            print("Container was not running or failed to stop.")

    elif command == "status":
        if client.is_running():
            print("nlp_uk container: RUNNING")
            print(f"API available at: http://localhost:{client.port}")
        else:
            print("nlp_uk container: STOPPED")
            print("Start with: python scripts/audit/vesum_client.py start")

    elif command == "validate":
        words = sys.argv[2:]
        if not words:
            print("Usage: vesum_client.py validate word1 word2 ...", file=sys.stderr)
            sys.exit(1)

        if not client.is_running():
            print("Container not running. Starting...", file=sys.stderr)
            client.start()

        result = client.validate_words(words)

        print(f"\nValidation Results ({result.valid_count} valid, {result.invalid_count} invalid):")
        print("-" * 50)

        for word, info in result.results.items():
            status = "VALID" if info.get("valid") else "INVALID"
            pos = info.get("pos", "")
            lemma = info.get("lemma", "")

            details = []
            if pos:
                details.append(f"POS: {pos}")
            if lemma and lemma != word:
                details.append(f"lemma: {lemma}")

            detail_str = f" ({', '.join(details)})" if details else ""
            print(f"  {word}: {status}{detail_str}")

        if result.invalid_words:
            print(f"\nInvalid words (not in VESUM): {', '.join(result.invalid_words)}")

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Commands: start, stop, status, validate", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

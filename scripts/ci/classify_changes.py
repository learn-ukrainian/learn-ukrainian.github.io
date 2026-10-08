#!/usr/bin/env python3
import argparse
import json
import sys

from scripts.ci.test_impact import get_impacted_tests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    result = get_impacted_tests(args.paths)
    json.dump(result, sys.stdout, indent=2)
    print()

if __name__ == "__main__":
    main()

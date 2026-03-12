#!/bin/bash
.venv/bin/python scripts/audit_module.py "$1" --skip-activities --no-rag-verify

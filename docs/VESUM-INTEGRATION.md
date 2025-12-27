# VESUM Integration

Automated Ukrainian word validation using the VESUM dictionary (430k+ lemmas) via nlp_uk Docker container.

## Overview

The VESUM (ВЕСУМ) dictionary is the largest Ukrainian morphological database, maintained by the brown-uk team. We integrate it via a Docker container running nlp_uk with a custom HTTP API.

**Two-Layer Validation Strategy:**

| Layer | Tool | Purpose |
|-------|------|---------|
| **Semantic** | Claude/Gemini + Ukrainian Tutor prompt | Russianisms, calques, grammar context |
| **Dictionary** | VESUM via nlp_uk container | Word existence, spelling, morphology |

LLMs are excellent at semantic understanding but can hallucinate word forms. VESUM provides ground truth for word existence.

## Quick Start

### Start VESUM Container

```bash
# Start container (first build takes ~5 minutes)
cd docker/nlp_uk
docker compose up -d

# Check status
python scripts/audit/vesum_client.py status

# Stop container (free RAM for other work)
docker compose down
```

### Use in Audit

```bash
# With VESUM validation (default if container running)
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/06-*.md

# Skip VESUM (container not running or A1/A2 content)
.venv/bin/python scripts/audit_module.py --no-vesum curriculum/l2-uk-en/a1/01-*.md

# Check container status
.venv/bin/python scripts/audit_module.py --vesum-status
```

## API Endpoints

The nlp_uk container exposes these endpoints on port 8899:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Container health check |
| `/validate` | POST | Validate words exist in VESUM |
| `/tag` | POST | Tag text with POS and morphology |
| `/lemmatize` | POST | Get base forms (lemmas) for words |

### Example: Validate Words

```bash
curl -X POST http://localhost:8899/validate \
  -H "Content-Type: application/json" \
  -d '{"words": ["привіт", "кушать", "їсти"]}'
```

Response:
```json
{
  "results": {
    "привіт": {"valid": true, "pos": "noun"},
    "кушать": {"valid": false, "reason": "not_in_vesum"},
    "їсти": {"valid": true, "pos": "verb"}
  },
  "invalid_words": ["кушать"],
  "valid_count": 2,
  "invalid_count": 1
}
```

## Python Client

```python
from scripts.audit.vesum_client import VesumClient

client = VesumClient()

# Start container if needed
if not client.is_running():
    client.start()  # Blocks until healthy (~60s first time)

# Validate words
result = client.validate_words(["привіт", "їсти", "кушать"])
print(f"Invalid: {result.invalid_words}")  # ["кушать"]

# Stop container to free RAM
client.stop()
```

## When VESUM Validation Runs

| Level | Modules | VESUM Check |
|-------|---------|-------------|
| A1 | 01-34 | ❌ Skip (scaffolded English) |
| A2 | 01-50 | ❌ Skip (transitional immersion) |
| B1 | 01-85 | ✅ **Full validation** |
| B2 | 01-110 | ✅ **Full validation** |
| C1 | 01-160 | ✅ **Full validation** |
| C2 | 01-100 | ✅ **Full validation** |

VESUM validates all B1+ content (100% immersed Ukrainian). B1 M01-M05 are metalanguage bridge modules but still contain valid Ukrainian text worth validating.

## Violation Types

| Type | Severity | Description |
|------|----------|-------------|
| `VESUM_VOCAB_INVALID` | error (blocking) | Vocabulary words not in dictionary |
| `VESUM_BODY_INVALID` | warning | Body text words not in dictionary |
| `VESUM_ERROR` | warning | Container/API error |

## Resource Usage

- **RAM**: Container uses 512MB-2GB depending on cache
- **Startup**: First build ~5 minutes, subsequent starts ~30 seconds
- **Validation Speed**: ~50 words/second

**Recommended Workflow:**
1. Start container before audit session
2. Run audits on multiple modules
3. Stop container when done to free RAM

## Files

| File | Purpose |
|------|---------|
| `docker/nlp_uk/Dockerfile` | Container build instructions |
| `docker/nlp_uk/docker-compose.yml` | Container orchestration |
| `docker/nlp_uk/server.py` | Flask HTTP API wrapper |
| `scripts/audit/vesum_client.py` | Python client for container |
| `scripts/audit/checks/vesum.py` | Audit integration |

## Troubleshooting

### Container Won't Start

```bash
# Check Docker is running
docker info

# Check logs
cd docker/nlp_uk
docker compose logs

# Rebuild from scratch
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Validation Timeout

The first request after container start may be slow (30-60s) as nlp_uk loads the dictionary. Subsequent requests are fast.

### False Positives

Some valid Ukrainian words may not be in VESUM:
- Neologisms
- Technical terms
- Proper nouns
- Dialectal forms

For these, the warning is informational (non-blocking). Vocabulary section words flagged as invalid DO block the audit since they should be verifiable.

## Credits

**Maintained by Andriy Rysin & Vasyl Starko** at [github.com/brown-uk](https://github.com/brown-uk)

| Resource | Description | Link |
|----------|-------------|------|
| **VESUM** | Morphological dictionary (430k+ lemmas) | [vesum.nlp.net.ua](https://vesum.nlp.net.ua/) |
| **BrUK** | Brown Ukrainian Corpus (1M words) | [r2u.org.ua/corpus](https://r2u.org.ua/corpus) |
| **dict_uk** | Source data for VESUM | [github.com/brown-uk/dict_uk](https://github.com/brown-uk/dict_uk) |
| **nlp_uk** | NLP toolkit (tokenization, POS, lemmas) | [github.com/brown-uk/nlp_uk](https://github.com/brown-uk/nlp_uk) |

**License**: Dictionary data CC BY-NC-SA 4.0, Software GPL 3.0

## Related Issues

- [#327](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/327) - Integrate VESUM for automated Ukrainian morphological validation ✅
- [#328](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/328) - Implement nlp_uk Docker container ✅

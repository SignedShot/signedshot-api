# SignedShot API

Backend API for the SignedShot media authenticity protocol.

[![CI](https://github.com/SignedShot/signedshot-api/actions/workflows/ci.yml/badge.svg)](https://github.com/SignedShot/signedshot-api/actions/workflows/ci.yml)

## Overview

SignedShot is an open protocol for proving photos and videos haven't been altered since capture—cryptographically, not by guessing.

This API provides:
- **Publisher and device registration** with optional Firebase App Check attestation
- **Capture session management** with cryptographic nonces
- **Trust token (JWT) issuance** with attestation method tracking
- **Media validation** endpoint for verifying sidecars
- **JWKS endpoint** for offline verification

### Two-Layer Trust Model

```
┌─────────────────────────────────────────────────────────────────┐
│  1. CAPTURE TRUST (Server-side)                                 │
│     • Device verified via Firebase App Check / App Attest       │
│     • Session nonce ensures freshness                           │
│     • JWT signed with server's EC key                           │
├─────────────────────────────────────────────────────────────────┤
│  2. MEDIA INTEGRITY (Device-side)                               │
│     • Content hashed (SHA-256) before any disk write            │
│     • Signed with Secure Enclave key (P-256 ECDSA)              │
│     • Proves content unchanged since capture                    │
└─────────────────────────────────────────────────────────────────┘
```

Together they prove: *"This exact content was captured on a verified device, in a legitimate session, and hasn't been modified."*

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker (for PostgreSQL and Redis)

### Setup

```bash
# Clone the repository
git clone https://github.com/SignedShot/signedshot-api.git
cd signedshot-api

# Install dependencies
uv sync --dev

# Copy environment configuration
cp .env.example .env
# Edit .env with your configuration

# Start PostgreSQL and Redis
docker compose up -d

# Run database migrations
uv run alembic upgrade head

# Start the development server
uv run poe dev
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/publishers` | POST | Register a new publisher |
| `/publishers/{id}` | GET | Get publisher details |
| `/publishers/{id}` | PATCH | Update publisher settings |
| `/devices` | POST | Register a device |
| `/capture/session` | POST | Start a capture session |
| `/capture/trust` | POST | Exchange nonce for trust token (JWT) |
| `/validate` | POST | Validate media + sidecar |
| `/.well-known/jwks.json` | GET | Public keys for JWT verification |
| `/health` | GET | Health check |

## Firebase App Check

Publishers can require device attestation via Firebase App Check:

```bash
# Create publisher with attestation requirement
curl -X POST http://localhost:8000/publishers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My App",
    "firebase_project_id": "my-firebase-project",
    "sandbox": false,
    "attestation_provider": "firebase_app_check",
    "attestation_bundle_id": "com.example.myapp"
  }'
```

### Attestation Modes

| sandbox | attestation_provider | Behavior |
|---------|---------------------|----------|
| `true` | `none` | No attestation required (testing/demo) |
| `true` | `firebase_app_check` | Attestation optional, validated if provided |
| `false` | `firebase_app_check` | Attestation required |

### Environment Variables

```bash
# Firebase (required for App Check)
FIREBASE_CREDENTIALS_JSON=  # JSON string or path to service account
FIREBASE_PROJECT_ID=my-project

# Database
DATABASE_URL=postgresql://user:pass@localhost/signedshot

# Redis
REDIS_URL=redis://localhost:6379

# Security
EC_PRIVATE_KEY=  # EC P-256 private key for JWT signing (auto-generated if not set)
```

## Development

```bash
# Run all checks (lint, format, typecheck)
uv run poe check

# Run unit tests
uv run poe test

# Run integration tests (requires Docker)
uv run poe test-integration

# Run all tests with coverage
uv run poe test-all

# Format code
uv run poe format

# Pre-commit checks
uv run poe pre-commit
```

## Architecture

```
app/
├── api/routes/          # HTTP endpoints
│   ├── publisher.py     # Publisher management
│   ├── device.py        # Device registration
│   ├── capture.py       # Capture sessions
│   └── validate.py      # Media validation
├── services/            # Business logic
│   ├── attestation.py   # App Check verification
│   ├── trust.py         # JWT generation
│   └── session.py       # Session management
├── repositories/        # Database access
├── db/models.py         # SQLAlchemy models
└── schemas/             # Pydantic schemas
```

## Related Repositories

- [signedshot-ios](https://github.com/SignedShot/signedshot-ios) - iOS SDK + Example App
- [signedshot-validator](https://github.com/SignedShot/signedshot-validator) - Verification CLI/library ([PyPI](https://pypi.org/project/signedshot/))
- [signedshot-docs](https://github.com/SignedShot/signedshot-docs) - Documentation

## Links

- [Website](https://signedshot.io)
- [Interactive Demo](https://signedshot.io/demo)
- [Documentation](https://signedshot.io/docs)

## License

[MIT](LICENSE)

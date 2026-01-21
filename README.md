# SignedShot API

Media authenticity verification API - cryptographic proof for photos and videos.

## Overview

SignedShot API provides a way to prove that media (photos/videos) was captured at a specific time by a verified device. It issues signed JWT tokens that can be independently verified by anyone.

### How It Works

```
1. Register Device    →  POST /devices/register
2. Create Session     →  POST /capture/session (before capture)
3. Capture Media      →  📷 (in your app)
4. Get Trust Token    →  POST /capture/trust (after capture)
5. Verify Token       →  GET /.well-known/jwks.json
```

The JWT token proves:
- Media was captured at a specific time
- The capture device was registered with the service
- The token hasn't been tampered with

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/SignedShot/signedshot-api.git
cd signedshot-api

# Install dependencies
uv sync --dev

# Copy environment configuration
cp .env.example .env

# Run the server
uv run poe dev
```

The API will be available at `http://localhost:8000`

## Development

```bash
# Run all checks
uv run poe check

# Run tests
uv run poe test

# Format code
uv run poe format

# Fix linting issues
uv run poe fix
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

[MIT](LICENSE)

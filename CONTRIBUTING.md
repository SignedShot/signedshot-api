# Contributing to SignedShot API

Thank you for your interest in contributing to SignedShot API!

## Development Setup

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) for dependency management

### Getting Started

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/signedshot-api.git
   cd signedshot-api
   ```

2. Install dependencies:
   ```bash
   uv sync --dev
   ```

3. Set up environment:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the development server:
   ```bash
   uv run poe dev
   ```

## Development Workflow

### Before Submitting a PR

Run all checks:
```bash
uv run poe pre-commit
```

This runs:
- `lint` - Code style checks (ruff)
- `format-check` - Formatting verification (ruff)
- `typecheck` - Type checking (pyright)
- `test` - Unit tests (pytest)

### Individual Commands

```bash
uv run poe lint        # Check code style
uv run poe format      # Format code
uv run poe typecheck   # Type checking
uv run poe test        # Run tests
uv run poe test-cov    # Run tests with coverage
uv run poe fix         # Auto-fix linting and formatting
```

## Code Style

- We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting
- Type hints are required (enforced by pyright in strict mode)
- Follow existing code patterns

## Pull Request Guidelines

1. **Branch naming**: Use descriptive branch names
   - `feat/add-device-registration`
   - `fix/session-expiry-bug`
   - `docs/update-readme`

2. **Commit messages**: Be clear and concise
   - Use imperative mood ("Add feature" not "Added feature")
   - Reference issues when applicable

3. **PR description**: Explain what and why
   - Describe the changes
   - Link related issues
   - Include testing steps if applicable

4. **Keep PRs focused**: One feature/fix per PR

## Testing

- Write tests for new functionality
- Ensure existing tests pass
- Aim for meaningful coverage, not 100%

### Running Tests

```bash
# All tests
uv run poe test

# With coverage
uv run poe test-cov

# Specific test file
uv run pytest tests/test_specific.py
```

## Questions?

Open an issue for questions or discussions.

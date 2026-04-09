# Quick Reference - Test Modularization Project

**Last Updated**: 2026-04-09T17:49:28Z (UTC)

## File Locations

| Purpose            | Location                           |
| ------------------ | ---------------------------------- |
| Agent instructions | `AGENTS.md`                        |
| AI transparency    | `AI-DECLARATION.md`                |
| Project context    | `.pi/context.md`                   |
| Progress tracking  | `.pi/progress.md`                  |
| Technical plan     | `.pi/test-modularization-plan.md`  |
| Test docs          | `tests/README.md`                  |
| CI workflow        | `.github/workflows/test-stdio.yml` |

## Current State

- **Phase**: Planning (Phase 1 infrastructure not started)
- **Transport**: Stdio-only tests exist; HTTP/OAuth tests are transport-coupled
- **Goal**: Transport-agnostic test modules

## Quick Commands

```bash
# Current stdio tests
./scripts/test_stdio.sh -v

# Current HTTP tests
./scripts/test_local.sh -v

# Future modular tests (after implementation)
TEST_TRANSPORT=stdio pytest tests/test_modules/ -v
```

## Key Files to Modify

1. `tests/conftest.py` - Add transport markers
2. `tests/fixtures/transports.py` - Transport factory (new)
3. `tests/core/test_client.py` - Abstract client (new)
4. `tests/test_modules/*.py` - Test modules (new)

## Environment Setup

```bash
# Required for all tests
export PLANE_TEST_API_KEY=your_key
export PLANE_TEST_WORKSPACE_SLUG=your_slug

# Optional
export PLANE_TEST_BASE_URL=https://api.plane.so
export TEST_TRANSPORT=stdio  # or http, or oauth
```

## Resume Instructions

1. Read `.pi/context.md` for full project context
2. Check `.pi/progress.md` for current status
3. Review `.idea/test-modularization-plan.md` for technical details
4. Start where we left off (check progress checklist)

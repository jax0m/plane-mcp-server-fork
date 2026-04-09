# Project Context: Test Modularization

**Last Updated**: 2026-04-09T17:49:28Z (UTC)
**Status**: Planning Phase

## Overview

This document tracks the ongoing effort to modularize the Plane MCP Server test suite to support transport-agnostic testing. The goal is to enable comprehensive tests to run against any transport type (stdio, HTTP, OAuth) by separating test logic from transport implementation.

## Problem Statement

### Current State (As of 2026-04-09)

| Test File                         | Transport           | Coverage                          | Issue                                    |
| --------------------------------- | ------------------- | --------------------------------- | ---------------------------------------- |
| `tests/test_stdio_integration.py` | Stdio only          | Basic CRUD, tool availability     | Limited scope - no epics/milestones      |
| `tests/test_integration.py`       | HTTP (api-key) only | Full lifecycle, epics, milestones | Transport-coupled, can't test with stdio |
| `tests/test_oauth_security.py`    | OAuth only          | Security tests                    | Already isolated (by design)             |
| `tests/test_stateless_http.py`    | HTTP only           | Transport validation              | Basic coverage                           |

### The Problem

1. **Transport coupling**: Test logic is tightly coupled to specific transport mechanisms
2. **Incomplete coverage**: Comprehensive tests (epics, milestones, parent relationships) only run on HTTP
3. **Maintenance burden**: Adding new tests requires updates in multiple files
4. **Developer friction**: Contributors can only test with transports they have configured

### The Goal

Enable this workflow:

```bash
# Developer with only stdio access tests comprehensive features
TEST_TRANSPORT=stdio pytest tests/test_modules/test_epics.py -v

# Upstream maintainers with OAuth test the same logic
TEST_TRANSPORT=oauth pytest tests/test_modules/test_epics.py -v

# CI runs all transports in matrix
for transport in stdio http oauth; do
    TEST_TRANSPORT=$transport pytest tests/test_modules/ -v
done
```

## Proposed Architecture

### Directory Structure

```
tests/
├── conftest.py              # Updated with transport markers
├── fixtures/
│   ├── __init__.py
│   ├── transports.py        # Transport-specific client fixtures
│   └── config.py            # Config loading utilities
├── core/
│   ├── __init__.py
│   ├── test_client.py       # Abstract test client wrapper
│   └── helpers.py           # Shared utilities (extract_result, etc.)
├── test_modules/
│   ├── __init__.py
│   ├── test_projects.py     # Project CRUD tests
│   ├── test_work_items.py   # Work item tests
│   ├── test_epics.py        # Epic lifecycle tests
│   ├── test_milestones.py   # Milestone tests
│   ├── test_cycles.py       # Cycle tests
│   ├── test_modules.py      # Module tests
│   └── test_tool_registry.py # Tool availability tests
├── test_stdio_integration.py   # Transport-specific: stdio smoke tests (updated)
├── test_http_integration.py    # Transport-specific: http smoke tests (new)
├── test_oauth_security.py      # OAuth-specific security tests (unchanged)
└── test_stateless_http.py      # Transport validation tests (unchanged)
```

### Key Components

#### 1. Transport Factory (`tests/fixtures/transports.py`)

Provides fixtures that create properly configured clients for each transport type:

- `stdio_client_session` - Stdio transport via mcp.client.stdio
- `http_client_session` - HTTP transport with api-key headers
- `oauth_client_session` - OAuth transport (when credentials available)
- `client` - Generic fixture that routes based on `TEST_TRANSPORT` env var

#### 2. Abstract Client (`tests/core/test_client.py`)

Unified interface for all transports:

```python
class AbstractTestClient:
    async def call_tool(self, tool_name: str, arguments: dict) -> Any
    async def list_tools(self) -> list
```

#### 3. Test Modules (`tests/test_modules/`)

Transport-agnostic test suites using the generic `client` fixture. Test logic written once, runs on all transports.

## Migration Plan

### Phase 1: Infrastructure (Current Phase)

- [ ] Create `tests/fixtures/` directory
- [ ] Create `tests/core/` directory
- [ ] Implement `tests/fixtures/config.py`
- [ ] Implement `tests/fixtures/transports.py`
- [ ] Implement `tests/core/helpers.py`
- [ ] Implement `tests/core/test_client.py`
- [ ] Update `tests/conftest.py` with new markers
- [ ] Create `tests/test_modules/__init__.py`

### Phase 2: Prototype

- [ ] Create `tests/test_modules/test_tool_registry.py` (migrate from test_stdio_integration.py)
- [ ] Create `tests/test_modules/test_projects.py` (migrate from test_integration.py)
- [ ] Update `test_stdio_integration.py` to use new fixtures
- [ ] Validate prototype works with stdio transport

### Phase 3: Full Migration

- [ ] Extract work item tests to `test_work_items.py`
- [ ] Extract epic tests to `test_epics.py`
- [ ] Extract milestone tests to `test_milestones.py`
- [ ] Extract cycle/module tests
- [ ] Create `test_http_integration.py` for HTTP-specific tests
- [ ] Update all transport-specific tests to use new fixtures

### Phase 4: CI/CD Updates

- [ ] Update `.github/workflows/test-stdio.yml` to support transport matrix
- [ ] Add documentation for multi-transport testing
- [ ] Update `tests/README.md` with new architecture
- [ ] Update `CONTRIBUTING.md` with testing guidelines

## Environment Variables

### Test Configuration

| Variable                             | Description                        | Required For      |
| ------------------------------------ | ---------------------------------- | ----------------- |
| `TEST_TRANSPORT`                     | Transport type: stdio, http, oauth | All modular tests |
| `PLANE_TEST_API_KEY`                 | Plane API key                      | stdio, http       |
| `PLANE_TEST_WORKSPACE_SLUG`          | Workspace slug                     | stdio, http       |
| `PLANE_TEST_BASE_URL`                | Plane API URL                      | stdio, http       |
| `PLANE_TEST_MCP_URL`                 | MCP server URL                     | http              |
| `PLANE_OAUTH_PROVIDER_CLIENT_ID`     | OAuth client ID                    | oauth             |
| `PLANE_OAUTH_PROVIDER_CLIENT_SECRET` | OAuth client secret                | oauth             |

### Usage Examples

```bash
# Test with stdio (default for most developers)
TEST_TRANSPORT=stdio pytest tests/test_modules/ -v

# Test with HTTP (requires local server)
TEST_TRANSPORT=http pytest tests/test_modules/ -v

# Test with OAuth (requires OAuth credentials)
TEST_TRANSPORT=oauth pytest tests/test_modules/ -v

# Run specific module
TEST_TRANSPORT=stdio pytest tests/test_modules/test_epics.py -v
```

## Current Progress

### Completed

- [x] Initial analysis of existing test structure
- [x] Documented current state and issues
- [x] Created comprehensive modularization plan (`.idea/test-modularization-plan.md`)
- [x] Created project context file (this file)
- [x] Updated documentation files (README.md, tests/README.md, CONTRIBUTING.md, .env.test)

### In Progress

- [ ] Plan refinement based on stakeholder feedback
- [ ] Decide on implementation approach details

### Pending

- [ ] Phase 1: Infrastructure implementation
- [ ] Phase 2: Prototype validation
- [ ] Phase 3: Full migration
- [ ] Phase 4: CI/CD updates

## Key Decisions Made

1. **Keep transport-specific tests**: Security tests and transport validation remain separate
2. **Generic client fixture**: Uses `TEST_TRANSPORT` env var for flexibility
3. **Abstract client interface**: Ensures consistent API across transports
4. **Module-based organization**: Groups tests by feature (projects, work items, etc.)
5. **No breaking changes**: Existing test files continue to work

## Open Questions

1. Should we support running multiple transports in the same test run (matrix within pytest)?
2. How do we handle transport-specific edge cases (e.g., OAuth flow quirks)?
3. Should we add a `test_all_transports.py` that runs key tests against all transports?
4. What's the strategy for tests that require HTTP-only features?

## Notes for Future Sessions

When resuming this work:

1. Review `.idea/test-modularization-plan.md` for detailed architecture
2. Check this file for current progress and open questions
3. Start with Phase 1 infrastructure if not already complete
4. Prototype with `test_tool_registry.py` first (simplest migration)

## Related Files

- `.idea/test-modularization-plan.md` - Detailed technical plan
- `tests/README.md` - Test documentation
- `.github/workflows/test-stdio.yml` - CI workflow
- `scripts/test_stdio.sh` - Stdio test runner
- `scripts/test_local.sh` - HTTP test runner

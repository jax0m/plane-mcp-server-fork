# Agent Instructions

This file provides guidance for AI coding assistants working on this project.

## Project Overview

Plane MCP Server — a Python-based Model Context Protocol server that exposes Plane's project management API as MCP tools. Built on FastMCP with the official `plane-sdk`.

## Context Files

When working on the **test modularization project**, always read these files first:

| File                              | Purpose                                        |
| --------------------------------- | ---------------------------------------------- |
| `.pi/context.md`                  | Full project context, architecture, and status |
| `.pi/progress.md`                 | Session log and implementation checklist       |
| `.pi/quick-reference.md`          | Commands and file locations                    |
| `.pi/test-modularization-plan.md` | Detailed technical architecture                |

## Conventions

### Timestamp Format

**All timestamps must use UTC in ISO 8601 format:**

```
Format: YYYY-MM-DDTHH:MM:SSZ (UTC)
Example: 2026-04-09T17:49:28Z
```

When updating any `.pi/` files, update the "Last Updated" timestamp to:

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

### File Locations

| Purpose            | Location                  |
| ------------------ | ------------------------- |
| Project context    | `.pi/context.md`          |
| Progress tracking  | `.pi/progress.md`         |
| Technical plans    | `.pi/*.md` (not `.idea/`) |
| Agent instructions | `AGENTS.md` (this file)   |
| Test documentation | `tests/README.md`         |

## Current Project: Test Modularization

### Goal

Separate test logic from transport implementation so tests can run against any transport (stdio, HTTP, OAuth).

### Key Commands

```bash
# After implementation, these will work:
TEST_TRANSPORT=stdio pytest tests/test_modules/ -v
TEST_TRANSPORT=http pytest tests/test_modules/ -v
TEST_TRANSPORT=oauth pytest tests/test_modules/ -v
```

### Current Status

Check `.pi/progress.md` for the latest status and next steps.

## Before Starting Work

1. **Read context files**: `.pi/context.md` and `.pi/progress.md`
2. **Check current status**: What phase are we in? What's complete?
3. **Understand conventions**: UTC timestamps, file locations
4. **Update timestamp**: When you make changes, update the "Last Updated" field

## Session Continuation

If resuming a previous session:

1. Read `.pi/context.md` for full context
2. Check `.pi/progress.md` for last session's timestamp and activities
3. Review `.pi/quick-reference.md` for commands
4. Update the timestamp before making changes

## Repository Structure

```
tests/
├── conftest.py              # Shared fixtures
├── fixtures/                # Transport fixtures (planned)
├── core/                    # Abstract client, helpers (planned)
├── test_modules/            # Transport-agnostic tests (planned)
├── test_stdio_integration.py  # Current: stdio tests
├── test_integration.py        # Current: HTTP tests
├── test_oauth_security.py     # OAuth security tests
└── test_stateless_http.py     # HTTP transport tests
```

## Important Notes

- `.pi/` folder is **git-tracked** and syncs across machines
- All documentation updates should reference `.pi/` files for context

# Deprecated Tests

This folder contains deprecated test files that have been superseded by the
modern transport-agnostic test modules in `tests/test_modules/`.

## Files

- `test_stdio_integration.py` - Legacy stdio integration tests

## Migration

All functionality from these tests has been migrated to:

- `tests/test_modules/test_tool_registry.py` - Tool availability tests
- `tests/test_modules/test_projects.py` - Project lifecycle tests
- `tests/test_modules/test_work_items.py` - Work item lifecycle tests

## Benefits of New Tests

- **Transport-agnostic**: Works with stdio, http, and oauth transports
- **Better organization**: Tests grouped by feature/domain
- **Automatic cleanup**: ResourceCleanup context manager handles cleanup
- **Leftover cleanup**: Automatically cleans up resources from failed runs
- **More comprehensive**: More granular test coverage

## Removal

These files may be removed in a future release. Do not depend on them.

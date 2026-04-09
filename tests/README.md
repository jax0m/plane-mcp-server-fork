# Test Suite Documentation

## Overview

The Plane MCP Server has comprehensive test coverage across multiple transport modes:

### Test Files

| File                        | Type                  | Description                                                |
| --------------------------- | --------------------- | ---------------------------------------------------------- |
| `test_stdio_integration.py` | **Stdio Integration** | Tests MCP server via stdin/stdout (no HTTP server needed)  |
| `test_integration.py`       | **HTTP Integration**  | Full end-to-end tests against HTTP transport               |
| `test_oauth_security.py`    | **OAuth Security**    | Security tests for OAuth flow (requires OAuth credentials) |
| `test_stateless_http.py`    | **HTTP Transport**    | Tests for HTTP transport modes (OAuth + Header auth)       |

### Test Scripts

| Script                  | Purpose                                                  |
| ----------------------- | -------------------------------------------------------- |
| `scripts/test_stdio.sh` | Run stdio-based tests (recommended for CI/CD)            |
| `scripts/test_local.sh` | Run HTTP-based tests (starts local server automatically) |

## Running Tests Locally

### Prerequisites

1. **Plane Instance**: A running Plane API instance (cloud or self-hosted)
2. **Environment Variables**: Configure in `.env` or `.env.test.local`

### Quick Start

```bash
# Copy the example env file
cp .env.test .env.test.local

# Edit .env.test.local with your credentials:
# PLANE_TEST_API_KEY=your_api_key
# PLANE_TEST_WORKSPACE_SLUG=your_workspace_slug
# PLANE_TEST_BASE_URL=https://api.plane.so

# Run stdio tests (recommended - no server needed)
./scripts/test_stdio.sh -v

# Run HTTP tests (starts local server automatically)
./scripts/test_local.sh -v

# Run specific test files
uv run pytest tests/test_stdio_integration.py -v
uv run pytest tests/test_integration.py -v

# Skip OAuth tests (skipped automatically if no OAuth credentials)
uv run pytest tests/ -v -m "not oauth"
```

### Test Markers

- `integration` - Full integration tests (stdio or HTTP)
- `oauth` - Tests requiring OAuth credentials (skipped if not configured)
- `http` - HTTP transport-specific tests

### Test Command Options

```bash
# Run all tests
uv run pytest tests/ -v

# Run only stdio tests
uv run pytest tests/test_stdio_integration.py -v

# Run only HTTP integration tests
uv run pytest tests/test_integration.py -v

# Skip OAuth tests
uv run pytest tests/ -v -m "not oauth"

# Run only OAuth tests (requires credentials)
uv run pytest tests/ -v -m "oauth"

# Run with detailed output
uv run pytest tests/ -v --tb=long
```

## GitHub Actions Workflows

### Stdio Workflow (`test-stdio.yml`)

The primary CI workflow runs stdio-based integration tests on every PR and push:

- **Trigger**: PRs to `main`, `develop`, `master` branches
- **Timeout**: 15 minutes
- **Tests**: `test_stdio_integration.py` via `scripts/test_stdio.sh`

**Tests validate:**

- Tool availability (55+ tools registered)
- Project lifecycle (create → update → delete → verify)
- Work item lifecycle (create → retrieve → delete → verify)
- Resource cleanup after test failures

### Required GitHub Secrets

| Secret                               | Description                | Required For              |
| ------------------------------------ | -------------------------- | ------------------------- |
| `PLANE_TEST_API_KEY`                 | Plane API key for testing  | Stdio & Integration tests |
| `PLANE_TEST_WORKSPACE_SLUG`          | Workspace slug for testing | Stdio & Integration tests |
| `PLANE_TEST_BASE_URL`                | Plane API URL (optional)   | Stdio & Integration tests |
| `PLANE_OAUTH_PROVIDER_CLIENT_ID`     | OAuth client ID            | OAuth tests               |
| `PLANE_OAUTH_PROVIDER_CLIENT_SECRET` | OAuth client secret        | OAuth tests               |

**Note**: The `PLANE_TEST_*` prefix is used to distinguish test credentials from production credentials.

### Secret Setup

1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret from the table above

**For stdio tests (recommended):**

- `PLANE_TEST_API_KEY` - Your Plane API key
- `PLANE_TEST_WORKSPACE_SLUG` - Your workspace slug
- `PLANE_TEST_BASE_URL` - Optional, defaults to `https://api.plane.so`

## Test Structure

### Stdio Integration Tests

**File**: `tests/test_stdio_integration.py`
**Script**: `scripts/test_stdio.sh`

Tests the MCP server via stdin/stdout without requiring an HTTP server. This is the recommended approach for CI/CD as it's faster and more reliable.

**Test cases:**

- `test_tools_list` - Verifies essential tools are registered
- `test_project_lifecycle` - Full project CRUD with cleanup verification
- `test_work_item_lifecycle` - Work item CRUD with parent resource management
- `test_tool_availability` - Validates all expected tools are available

**Test pattern**: Each test follows a lifecycle pattern:

1. Check for existing test resources (cleanup if found from previous run)
2. Create test resources with unique identifiers
3. Verify creation was successful
4. Test operations and relationships
5. Clean up (delete/archive) test resources
6. Verify cleanup was successful

**Requirements**:

- Live Plane instance
- `PLANE_API_KEY` environment variable
- `PLANE_WORKSPACE_SLUG` environment variable
- `PLANE_BASE_URL` (optional, defaults to `https://api.plane.so`)

**Run**:

```bash
# Using the dedicated script (recommended)
./scripts/test_stdio.sh -v

# Or directly with pytest
uv run pytest tests/test_stdio_integration.py -v

# With environment from file
export $(cat .env.test.local | xargs) && ./scripts/test_stdio.sh -v
```

### HTTP Integration Tests

**File**: `tests/test_integration.py`

Full end-to-end tests against the HTTP transport with header-based authentication.

**Test cases:**

- `test_full_integration` - Comprehensive workflow testing:
  - Create project
  - Create work items with parent relationships
  - Create epics and milestones
  - List and filter operations
  - Full cleanup
- `test_tools_availability` - Validates all 55+ tools are registered

**Requirements**:

- MCP server running on `http://localhost:8211`
- `PLANE_TEST_API_KEY` environment variable
- `PLANE_TEST_WORKSPACE_SLUG` environment variable

**Run**:

```bash
# Using the dedicated script (starts server automatically)
./scripts/test_local.sh -v

# Or manually
uv run python -m plane_mcp http &
uv run pytest tests/test_integration.py -v
```

### HTTP Transport Tests

**File**: `tests/test_stateless_http.py`

Tests HTTP transport modes and authentication:

- OAuth HTTP app with stateless flag
- Header-based auth HTTP app
- Endpoint responses

**Requirements**:

- MCP server must be running
- No OAuth credentials required for header auth tests

**Run**:

```bash
./scripts/test_local.sh -v
```

### OAuth Security Tests

**File**: `tests/test_oauth_security.py`

Tests OAuth security features:

- Redirect URI validation
- Attack prevention (OAuth redirect attacks)
- CORS configuration
- Malicious URI rejection

**Requirements**:

- OAuth credentials configured
- Tests run against in-memory OAuth provider (no external Plane needed)

**Run** (requires OAuth credentials):

```bash
export PLANE_OAUTH_PROVIDER_CLIENT_ID=your_client_id
export PLANE_OAUTH_PROVIDER_CLIENT_SECRET=your_client_secret
uv run pytest tests/test_oauth_security.py -v
```

## Troubleshooting

### Stdio Tests Fail

**Error**: "Missing required env vars: PLANE_API_KEY, PLANE_WORKSPACE_SLUG"

**Solution**: Set the required environment variables:

```bash
export PLANE_API_KEY=your_api_key
export PLANE_WORKSPACE_SLUG=your_workspace_slug
./scripts/test_stdio.sh -v
```

**Error**: "PLANE_API_KEY is not configured or is using default value"

**Solution**: Ensure your `.env` or `.env.test.local` file has valid credentials (not placeholder values).

### HTTP Tests Fail to Connect

**Error**: `ConnectionRefusedError` or timeout

**Solution**: Ensure MCP server is running:

```bash
# Check if server is running
curl http://localhost:8211/mcp

# Start server if needed
uv run python -m plane_mcp http &
sleep 5
curl http://localhost:8211/mcp
```

### OAuth Tests Skipped

**Message**: "OAuth credentials not configured"

**Solution**: Set OAuth environment variables:

```bash
export PLANE_OAUTH_PROVIDER_CLIENT_ID=your_client_id
export PLANE_OAUTH_PROVIDER_CLIENT_SECRET=your_client_secret
```

### Integration Tests Fail

**Common causes**:

1. Invalid API key
2. Workspace doesn't exist or incorrect slug
3. Plane API is unreachable

**Debug**:

```bash
# Test direct API connection
curl -H "Authorization: Bearer $PLANE_TEST_API_KEY" \
  -H "X-Workspace-Slug: $PLANE_TEST_WORKSPACE_SLUG" \
  "$PLANE_TEST_BASE_URL/api/me/"

# Expected: JSON response with user data
# If 401: Check API key
# If 403: Check workspace slug
# If 000/timeout: Check BASE_URL and network
```

## CI/CD Best Practices

1. **Use dedicated test workspace** - Don't use production workspace for tests
2. **Use stdio tests** - Faster and more reliable than HTTP tests in CI
3. **Clean up test resources** - Tests create/delete resources automatically
4. **Set timeouts** - Add step timeouts for long-running tests (15 minutes recommended)
5. **Cache dependencies** - Use uv cache in CI for faster builds
6. **Validate secrets early** - Check for required secrets before running tests

## Example: Self-Hosted Plane Instance

If you have a self-hosted Plane instance for testing:

```yaml
# In .github/workflows/test-stdio.yml
env:
  PLANE_TEST_BASE_URL: http://localhost:8000
  PLANE_TEST_API_KEY: ${{ secrets.PLANE_TEST_API_KEY }}
  PLANE_TEST_WORKSPACE_SLUG: ${{ secrets.PLANE_TEST_WORKSPACE_SLUG }}
```

Or configure in your environment file:

```bash
PLANE_TEST_BASE_URL=http://localhost:8000
PLANE_TEST_API_KEY=your_test_key
PLANE_TEST_WORKSPACE_SLUG=your_workspace_slug
```

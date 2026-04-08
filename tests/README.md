# Test Suite Documentation

## Overview

The Plane MCP Server has three types of tests:

1. **Integration Tests** (`test_integration.py`) - Full end-to-end tests against a live Plane API
2. **OAuth Security Tests** (`test_oauth_security.py`) - Security tests for OAuth flow (requires OAuth credentials)
3. **HTTP Transport Tests** (`test_stateless_http.py`) - Tests for HTTP transport modes (OAuth + Header auth)

## Running Tests Locally

### Prerequisites

1. **Plane Instance**: A running Plane API instance
2. **Environment Variables**: Configure in `.env` or `.env.test.local`

### Quick Start

```bash
# Copy the example env file
cp .env .env.test.local

# Edit .env.test.local with your credentials
# PLANE_TEST_BASE_URL=https://your-plane-instance.com
# PLANE_TEST_API_KEY=your_api_key
# PLANE_TEST_WORKSPACE_SLUG=your_workspace_slug

# Run all tests
./scripts/test_local.sh

# Run only specific test files
uv run pytest tests/test_integration.py -v
uv run pytest tests/test_stateless_http.py -v

# Skip OAuth tests (they will be skipped automatically if no OAuth credentials)
uv run pytest tests/ -v -m "not oauth"
```

### Test Markers

- `oauth` - Tests requiring OAuth credentials (skipped if not configured)
- `integration` - Full integration tests
- `http` - HTTP transport tests

### Test Command Options

```bash
# Run all tests
uv run pytest tests/ -v

# Run only non-OAuth tests
uv run pytest tests/ -v -m "not oauth"

# Run only OAuth tests (requires credentials)
uv run pytest tests/ -v -m "oauth"

# Run specific test file
uv run pytest tests/test_integration.py -v

# Run with detailed output
uv run pytest tests/ -v --tb=long
```

## GitHub Actions Workflow

The workflow (`.github/workflows/test.yml`) runs:

1. **HTTP tests** - Uses secrets for Plane API credentials
2. **OAuth tests** - Only runs if OAuth secrets are configured
3. **Lint checks** - Ruff format and linter

### Required GitHub Secrets

| Secret | Description | Required For |
|--------|-------------|--------------|
| `PLANE_API_KEY` | Plane API key | HTTP & Integration tests |
| `PLANE_WORKSPACE_SLUG` | Workspace slug | HTTP & Integration tests |
| `PLANE_BASE_URL` | Plane API URL (optional) | HTTP & Integration tests |
| `PLANE_OAUTH_PROVIDER_CLIENT_ID` | OAuth client ID | OAuth tests |
| `PLANE_OAUTH_PROVIDER_CLIENT_SECRET` | OAuth client secret | OAuth tests |

### Secret Setup

1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add each secret from the table above

## Test Structure

### Integration Tests

**File**: `tests/test_integration.py`

Tests the full workflow:
- Create project
- Create work items
- Update work items (parent relationships)
- Create epics and milestones
- List and filter operations
- Cleanup (delete resources)

**Requirements**:
- Live Plane instance
- Valid API key
- Workspace slug

**Run**:
```bash
uv run pytest tests/test_integration.py -v
```

### HTTP Transport Tests

**File**: `tests/test_stateless_http.py`

Tests HTTP transport modes:
- OAuth HTTP app with stateless flag
- Header-based auth HTTP app
- Endpoint responses

**Requirements**:
- MCP server must be running
- No OAuth credentials required for header auth tests

**Run**:
```bash
# Start server in background
uv run python -m plane_mcp http &

# Run tests
uv run pytest tests/test_stateless_http.py -v
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

### Tests Fail to Connect

**Error**: `ConnectionRefusedError` or timeout

**Solution**: Ensure MCP server is running:
```bash
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
2. Workspace doesn't exist
3. Plane API is unreachable

**Debug**:
```bash
# Test direct API connection
curl -H "Authorization: Bearer $PLANE_TEST_API_KEY" \
  -H "X-Workspace-Slug: $PLANE_TEST_WORKSPACE_SLUG" \
  $PLANE_TEST_BASE_URL/api/workspaces/$PLANE_TEST_WORKSPACE_SLUG
```

## CI/CD Best Practices

1. **Use dedicated test workspace** - Don't use production workspace for tests
2. **Clean up test resources** - Tests create/delete resources automatically
3. **Set timeouts** - Add step timeouts for long-running tests
4. **Cache dependencies** - Use uv cache in CI for faster builds

## Example: Self-Hosted Plane Instance

If you have a self-hosted Plane instance for testing:

```yaml
# In .github/workflows/test.yml
services:
  plane:
    image: planeorg/plane:latest
    ports:
      - 8000:8000
    env:
      DEBUG: "1"
```

Then update test configuration:
```bash
PLANE_TEST_BASE_URL=http://localhost:8000
PLANE_TEST_API_KEY=your_test_key
```

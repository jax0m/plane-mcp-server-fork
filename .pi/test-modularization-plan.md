# Test Modularization Plan

**Document Created**: 2026-04-09T17:45:24Z (UTC)
**Last Updated**: 2026-04-09T17:49:28Z (UTC)
**Status**: Draft - Awaiting Review

**Note**: This file was moved from `.idea/` to `.pi/` for git tracking.

## Current State Analysis

### Existing Test Files

| File                        | Transport      | Coverage                          | Issues            |
| --------------------------- | -------------- | --------------------------------- | ----------------- |
| `test_stdio_integration.py` | Stdio          | Basic CRUD, tool availability     | Limited scope     |
| `test_integration.py`       | HTTP (api-key) | Full lifecycle, epics, milestones | Transport-coupled |
| `test_oauth_security.py`    | OAuth          | Security tests only               | Transport-coupled |
| `test_stateless_http.py`    | HTTP           | Transport validation              | Basic coverage    |

### Key Problems

1. **Transport coupling**: Tests are tightly coupled to specific transport mechanisms
2. **Duplication risk**: Same test logic would need to be written for each transport
3. **Maintenance burden**: Adding new tests requires updates in multiple files
4. **Incomplete coverage**: Comprehensive tests (epics, milestones) only run on HTTP

## Proposed Architecture

### Overview

```
tests/
├── conftest.py              # Shared fixtures, transport factory
├── fixtures/
│   ├── __init__.py
│   ├── transports.py        # Transport-specific fixtures (stdio, http, oauth)
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
├── test_stdio_integration.py   # Transport-specific: stdio smoke tests
├── test_http_integration.py    # Transport-specific: http smoke tests
├── test_oauth_security.py      # OAuth-specific security tests
└── test_stateless_http.py      # Transport validation tests
```

### Component Breakdown

#### 1. Transport Abstraction Layer (`tests/fixtures/transports.py`)

Provide fixtures that create properly configured clients for each transport type:

```python
# tests/fixtures/transports.py

import os
from typing import AsyncContextManager, Callable
import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


class TransportConfig:
    """Configuration for a specific transport."""
    def __init__(
        self,
        transport_type: str,
        api_key: str,
        workspace_slug: str,
        base_url: str = "https://api.plane.so",
        mcp_url: str = "http://localhost:8211",
        oauth_client_id: str = None,
        oauth_client_secret: str = None,
    ):
        self.transport_type = transport_type
        self.api_key = api_key
        self.workspace_slug = workspace_slug
        self.base_url = base_url
        self.mcp_url = mcp_url
        self.oauth_client_id = oauth_client_id
        self.oauth_client_secret = oauth_client_secret


@pytest.fixture
def transport_config():
    """Load transport configuration from environment."""
    return TransportConfig(
        transport_type=os.getenv("TEST_TRANSPORT", "stdio"),
        api_key=os.getenv("PLANE_TEST_API_KEY", ""),
        workspace_slug=os.getenv("PLANE_TEST_WORKSPACE_SLUG", ""),
        base_url=os.getenv("PLANE_TEST_BASE_URL", "https://api.plane.so"),
        mcp_url=os.getenv("PLANE_TEST_MCP_URL", "http://localhost:8211"),
        oauth_client_id=os.getenv("PLANE_OAUTH_PROVIDER_CLIENT_ID"),
        oauth_client_secret=os.getenv("PLANE_OAUTH_PROVIDER_CLIENT_SECRET"),
    )


@pytest.fixture
async def stdio_client_session(transport_config: TransportConfig):
    """Create stdio transport client session."""
    params = StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "plane_mcp", "stdio"],
        env={
            **os.environ,
            "PLANE_API_KEY": transport_config.api_key,
            "PLANE_WORKSPACE_SLUG": transport_config.workspace_slug,
            "PLANE_BASE_URL": transport_config.base_url,
        },
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


@pytest.fixture
async def http_client_session(transport_config: TransportConfig):
    """Create HTTP transport client session (api-key auth)."""
    transport = StreamableHttpTransport(
        f"{transport_config.mcp_url}/http/api-key/mcp",
        headers={
            "x-workspace-slug": transport_config.workspace_slug,
            "Authorization": f"Bearer {transport_config.api_key}",
        },
    )
    async with Client(transport=transport) as client:
        yield client


@pytest.fixture
async def oauth_client_session(transport_config: TransportConfig):
    """Create OAuth transport client session."""
    if not transport_config.oauth_client_id or not transport_config.oauth_client_secret:
        pytest.skip("OAuth credentials not configured")

    transport = StreamableHttpTransport(
        f"{transport_config.mcp_url}/oauth/mcp",
        # OAuth flow handled by server
    )
    async with Client(transport=transport) as client:
        yield client


@pytest.fixture
async def client(transport_config: TransportConfig, request):
    """
    Generic client fixture that routes to appropriate transport.

    Usage:
        - Default: uses TEST_TRANSPORT env var
        - Override with marker: @pytest.mark.transport("stdio")
    """
    transport_type = transport_config.transport_type

    # Allow test to override via marker
    if hasattr(request.node, "transport_override"):
        transport_type = request.node.transport_override

    if transport_type == "stdio":
        async with stdio_client_session(transport_config) as session:
            yield session
    elif transport_type == "http":
        async with http_client_session(transport_config) as client:
            yield client
    elif transport_type == "oauth":
        async with oauth_client_session(transport_config) as client:
            yield client
    else:
        raise ValueError(f"Unknown transport type: {transport_type}")
```

#### 2. Abstract Test Client (`tests/core/test_client.py`)

Wrap the transport-specific clients with a unified interface:

```python
# tests/core/test_client.py

from typing import Any, AsyncContextManager


class AbstractTestClient:
    """
    Abstract interface for MCP test clients.

    All transport-specific clients should implement these methods.
    """

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Call an MCP tool."""
        raise NotImplementedError

    async def list_tools(self) -> list:
        """List available tools."""
        raise NotImplementedError


class StdioTestClient(AbstractTestClient):
    """Stdio transport wrapper."""

    def __init__(self, session):
        self.session = session

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        return await self.session.call_tool(tool_name, arguments)

    async def list_tools(self) -> list:
        result = await self.session.list_tools()
        return result.tools


class HttpTestClient(AbstractTestClient):
    """HTTP transport wrapper."""

    def __init__(self, client):
        self.client = client

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        return await self.client.call_tool(tool_name, arguments)

    async def list_tools(self) -> list:
        return await self.client.list_tools()
```

#### 3. Test Modules (`tests/test_modules/`)

Transport-agnostic test suites:

```python
# tests/test_modules/test_projects.py

import pytest
import uuid
from ..core.helpers import extract_result


@pytest.mark.integration
class TestProjects:
    """Project lifecycle tests - transport agnostic."""

    @pytest.fixture
    def test_id(self):
        return uuid.uuid4().hex[:8]

    @pytest.mark.asyncio
    async def test_create_project(self, client, test_id):
        """Create a project."""
        name = f"TEST-{test_id}"
        result = await client.call_tool("create_project", {
            "name": name,
            "identifier": f"TST{test_id[:3].upper()}",
        })
        project = extract_result(result)
        assert project["id"] is not None
        assert project["name"] == name

        # Cleanup
        await client.call_tool("delete_project", {"project_id": project["id"]})

    @pytest.mark.asyncio
    async def test_project_lifecycle(self, client, test_id):
        """Full project CRUD lifecycle."""
        # Implementation...
        pass
```

#### 4. Updated Conftest (`tests/conftest.py`)

```python
# tests/conftest.py

import os
import pytest


pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "oauth: mark test as requiring OAuth credentials")
    config.addinivalue_line("markers", "integration: full integration test against Plane API")
    config.addinivalue_line("markers", "http: HTTP transport mode test")
    config.addinivalue_line("markers", "stdio: stdio transport mode test")
    config.addinivalue_line("markers", "transport(type): specify transport type for test")


def pytest_collection_modifyitems(config, items):
    """Skip tests based on transport availability."""
    # Check OAuth availability
    oauth_client_id = os.getenv("PLANE_OAUTH_PROVIDER_CLIENT_ID", "").strip()
    oauth_client_secret = os.getenv("PLANE_OAUTH_PROVIDER_CLIENT_SECRET", "").strip()
    has_oauth = bool(oauth_client_id and oauth_client_secret)

    if not has_oauth:
        skip_oauth = pytest.mark.skip(reason="OAuth credentials not configured")
        for item in items:
            if "oauth" in item.keywords:
                item.add_marker(skip_oauth)

    # Check Plane API availability
    api_key = os.getenv("PLANE_TEST_API_KEY", "").strip()
    workspace_slug = os.getenv("PLANE_TEST_WORKSPACE_SLUG", "").strip()
    has_plane = bool(api_key and workspace_slug)

    if not has_plane:
        skip_plane = pytest.mark.skip(reason="Plane API credentials not configured")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_plane)
```

## Migration Strategy

### Phase 1: Infrastructure (Week 1)

1. Create `tests/fixtures/` and `tests/core/` directories
2. Implement transport fixtures (`tests/fixtures/transports.py`)
3. Implement abstract client wrapper (`tests/core/test_client.py`)
4. Create shared helpers (`tests/core/helpers.py`)
5. Update `conftest.py` with new markers

### Phase 2: Module Extraction (Week 2)

1. Move tool availability test to `tests/test_modules/test_tool_registry.py`
2. Extract project tests to `tests/test_modules/test_projects.py`
3. Extract work item tests to `tests/test_modules/test_work_items.py`
4. Extract epic/milestone tests to dedicated modules

### Phase 3: Transport-Specific Tests (Week 3)

1. Update `test_stdio_integration.py` to use new fixtures
2. Create `test_http_integration.py` for HTTP-specific tests
3. Keep OAuth security tests as-is (they're already transport-specific)

### Phase 4: CI/CD Updates (Week 4)

1. Update GitHub Actions to support transport selection
2. Add matrix testing for multiple transports
3. Document new testing approach

## Usage Examples

### Running Tests with Specific Transport

```bash
# Stdio tests (default)
TEST_TRANSPORT=stdio pytest tests/test_modules/ -v

# HTTP tests
TEST_TRANSPORT=http pytest tests/test_modules/ -v

# OAuth tests (requires credentials)
TEST_TRANSPORT=oauth pytest tests/test_modules/ -v
```

### Running Specific Test Modules

```bash
# Just project tests
pytest tests/test_modules/test_projects.py -v

# Just work item tests
pytest tests/test_modules/test_work_items.py -v

# All integration tests
pytest tests/ -m integration -v
```

### Running All Transports (Matrix)

```bash
# In CI/CD or for comprehensive testing
for transport in stdio http; do
    echo "Testing with $transport transport..."
    TEST_TRANSPORT=$transport pytest tests/test_modules/ -v
done
```

## Benefits

1. **Single source of truth**: Test logic written once, runs on all transports
2. **Easier maintenance**: Bug fixes apply to all transport tests
3. **Flexible testing**: Developers can test with available transports
4. **Better coverage**: Comprehensive tests run on all transports
5. **Clear separation**: Transport concerns isolated from test logic

## Potential Issues & Mitigations

| Issue                                     | Mitigation                                     |
| ----------------------------------------- | ---------------------------------------------- |
| Different API behaviors across transports | Add transport-specific fixtures for edge cases |
| OAuth flow complexity                     | Keep OAuth tests separate where needed         |
| Test execution time                       | Use pytest markers to select subsets           |
| Connection pooling issues                 | Use proper async context managers              |

## Next Steps

1. Review and approve this plan
2. Create the directory structure
3. Implement Phase 1 (infrastructure)
4. Test with existing test_stdio_integration.py
5. Migrate test_integration.py tests to modules
6. Update CI/CD workflows

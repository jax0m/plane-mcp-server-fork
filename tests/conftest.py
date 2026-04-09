"""Pytest configuration for Plane MCP Server tests.

This file configures pytest markers, skip logic, and transport-agnostic fixtures.
"""

import os
from collections.abc import AsyncGenerator

import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from .core.test_client import HttpTestClient, OAuthTestClient, StdioTestClient
from .fixtures.config import TransportConfig, load_config


@pytest.fixture(scope="session")
def anyio_backend():
    """Set default async backend for pytest-asyncio."""
    return "asyncio"


@pytest.fixture(scope="function")
def transport_config() -> TransportConfig:
    """Load transport configuration from environment.

    Returns:
        TransportConfig populated from environment variables
    """
    return load_config()


@pytest.fixture(scope="function")
async def client(
    transport_config: TransportConfig,
    request,
) -> AsyncGenerator[StdioTestClient | HttpTestClient | OAuthTestClient, None]:
    """Generic client fixture that routes to the appropriate transport.

    This is the main fixture for transport-agnostic tests. It selects
    the transport based on:
    1. TEST_TRANSPORT environment variable
    2. pytest.mark.transport() marker (if present)
    3. Default: stdio

    Yields:
        AbstractTestClient wrapper for the selected transport
    """
    transport_type = transport_config.transport_type

    for marker in request.node.iter_markers("transport"):
        if marker.args:
            transport_type = marker.args[0].lower()
            break

    # Validate credentials for selected transport
    if transport_type in ("stdio", "http") and not transport_config.has_plane_credentials():
        pytest.skip(f"{transport_type.capitalize()} API credentials not configured")

    if transport_type == "oauth" and not transport_config.has_oauth_credentials():
        pytest.skip("OAuth credentials not configured")

    client_wrapper = None
    read_stream = None
    write_stream = None
    session = None
    http_client = None

    try:
        if transport_type == "stdio":
            # Create stdio client
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

            stdio_context = stdio_client(params)
            read_stream, write_stream = await stdio_context.__aenter__()
            session = ClientSession(read_stream, write_stream)
            await session.__aenter__()
            await session.initialize()
            client_wrapper = StdioTestClient(session)

        elif transport_type == "http":
            # Create HTTP client
            transport = StreamableHttpTransport(
                f"{transport_config.mcp_url}/http/api-key/mcp",
                headers={
                    "x-workspace-slug": transport_config.workspace_slug,
                    "Authorization": f"Bearer {transport_config.api_key}",
                },
            )

            http_client = Client(transport=transport)
            await http_client.__aenter__()
            client_wrapper = HttpTestClient(http_client)

        elif transport_type == "oauth":
            # Create OAuth client
            transport = StreamableHttpTransport(
                f"{transport_config.mcp_url}/oauth/mcp",
            )

            http_client = Client(transport=transport)
            await http_client.__aenter__()
            client_wrapper = OAuthTestClient(http_client)

        else:
            raise ValueError(f"Unknown transport type: {transport_type}")

        yield client_wrapper

    finally:
        # Cleanup in reverse order
        if session is not None:
            try:
                await session.__aexit__(None, None, None)
            except Exception:
                pass

        if read_stream is not None or write_stream is not None:
            try:
                await read_stream.aclose() if read_stream else None
                await write_stream.aclose() if write_stream else None
            except Exception:
                pass

        if http_client is not None:
            try:
                await http_client.__aexit__(None, None, None)
            except Exception:
                pass


@pytest.fixture(scope="function")
async def stdio_client_wrapper(
    transport_config: TransportConfig,
) -> AsyncGenerator[StdioTestClient, None]:
    """Create a stdio transport client wrapper.

    Yields:
        StdioTestClient connected via stdio transport
    """
    if not transport_config.has_plane_credentials():
        pytest.skip("Plane API credentials not configured for stdio transport")

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

    read_stream = None
    write_stream = None
    session = None
    client_wrapper = None

    try:
        stdio_context = stdio_client(params)
        read_stream, write_stream = await stdio_context.__aenter__()
        session = ClientSession(read_stream, write_stream)
        await session.__aenter__()
        await session.initialize()
        client_wrapper = StdioTestClient(session)

        yield client_wrapper
    finally:
        if session is not None:
            try:
                await session.__aexit__(None, None, None)
            except Exception:
                pass
        if read_stream is not None:
            try:
                await read_stream.aclose()
            except Exception:
                pass
        if write_stream is not None:
            try:
                await write_stream.aclose()
            except Exception:
                pass


@pytest.fixture(scope="function")
async def http_client_wrapper(
    transport_config: TransportConfig,
) -> AsyncGenerator[HttpTestClient, None]:
    """Create an HTTP transport client wrapper.

    Yields:
        HttpTestClient connected via HTTP transport
    """
    if not transport_config.has_plane_credentials():
        pytest.skip("Plane API credentials not configured for HTTP transport")

    transport = StreamableHttpTransport(
        f"{transport_config.mcp_url}/http/api-key/mcp",
        headers={
            "x-workspace-slug": transport_config.workspace_slug,
            "Authorization": f"Bearer {transport_config.api_key}",
        },
    )

    http_client = None
    client_wrapper = None

    try:
        http_client = Client(transport=transport)
        await http_client.__aenter__()
        client_wrapper = HttpTestClient(http_client)

        yield client_wrapper
    finally:
        if http_client is not None:
            try:
                await http_client.__aexit__(None, None, None)
            except Exception:
                pass


def pytest_configure(config):
    """Register custom markers for transport-agnostic testing."""
    config.addinivalue_line("markers", "oauth: mark test as requiring OAuth credentials")
    config.addinivalue_line("markers", "integration: full integration test against Plane API")
    config.addinivalue_line("markers", "http: HTTP transport mode test")
    config.addinivalue_line("markers", "stdio: stdio transport mode test")
    config.addinivalue_line("markers", "transport(type): specify transport type for test (stdio, http, oauth)")


def pytest_collection_modifyitems(config, items):
    """Skip tests based on credential availability and transport selection."""
    # Check OAuth availability
    oauth_client_id = os.getenv("PLANE_OAUTH_PROVIDER_CLIENT_ID", "").strip()
    oauth_client_secret = os.getenv("PLANE_OAUTH_PROVIDER_CLIENT_SECRET", "").strip()
    has_oauth = bool(oauth_client_id and oauth_client_secret)

    # Check Plane API availability
    api_key = (os.getenv("PLANE_API_KEY") or os.getenv("PLANE_TEST_API_KEY") or "").strip()
    workspace_slug = (os.getenv("PLANE_WORKSPACE_SLUG") or os.getenv("PLANE_TEST_WORKSPACE_SLUG") or "").strip()
    has_plane = bool(api_key and workspace_slug)

    # Get selected transport
    transport_type = os.getenv("TEST_TRANSPORT", "stdio").lower()

    if not has_oauth:
        skip_oauth = pytest.mark.skip(reason="OAuth credentials not configured")
        for item in items:
            if "oauth" in item.keywords:
                item.add_marker(skip_oauth)

    if not has_plane:
        skip_plane = pytest.mark.skip(reason="Plane API credentials not configured")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_plane)

    if transport_type == "oauth" and not has_oauth:
        skip_msg = "OAuth transport selected but credentials not configured"
        skip_oauth = pytest.mark.skip(reason=skip_msg)
        for item in items:
            item.add_marker(skip_oauth)

    if transport_type in ("stdio", "http") and not has_plane:
        skip_msg = f"{transport_type.capitalize()} transport selected but Plane credentials not configured"
        skip_plane = pytest.mark.skip(reason=skip_msg)
        for item in items:
            item.add_marker(skip_plane)

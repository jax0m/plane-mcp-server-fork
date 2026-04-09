"""Transport fixtures for test modularization.

This module provides pytest fixtures that create properly configured
MCP clients for different transport types.
"""

import os
from collections.abc import AsyncGenerator

import pytest
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from ..core.test_client import HttpTestClient, OAuthTestClient, StdioTestClient
from .config import TransportConfig, load_config


@pytest.fixture(scope="function")
def transport_config() -> TransportConfig:
    """Load transport configuration from environment.

    Returns:
        TransportConfig populated from environment variables
    """
    return load_config()


@pytest.fixture(scope="function")
async def stdio_session(
    transport_config: TransportConfig,
) -> AsyncGenerator[ClientSession, None]:
    """Create a stdio transport client session.

    Args:
        transport_config: Configuration with Plane API credentials

    Yields:
        ClientSession connected via stdio transport

    Raises:
        RuntimeError: If Plane API credentials are not configured
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

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


@pytest.fixture(scope="function")
async def http_client(
    transport_config: TransportConfig,
) -> AsyncGenerator[Client, None]:
    """Create an HTTP transport client with API key authentication.

    Args:
        transport_config: Configuration with Plane API credentials

    Yields:
        Client connected via HTTP transport

    Raises:
        RuntimeError: If Plane API credentials are not configured
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

    async with Client(transport=transport) as client:
        yield client


@pytest.fixture(scope="function")
async def oauth_client(
    transport_config: TransportConfig,
) -> AsyncGenerator[Client, None]:
    """Create an OAuth transport client.

    Args:
        transport_config: Configuration with OAuth credentials

    Yields:
        Client connected via OAuth transport

    Raises:
        SkipTest: If OAuth credentials are not configured
    """
    if not transport_config.has_oauth_credentials():
        pytest.skip("OAuth credentials not configured")

    transport = StreamableHttpTransport(
        f"{transport_config.mcp_url}/oauth/mcp",
    )

    async with Client(transport=transport) as client:
        yield client


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

    Args:
        transport_config: Configuration with credentials
        request: Pytest request object for marker access

    Yields:
        AbstractTestClient wrapper for the selected transport
    """
    # Check for transport override marker
    transport_type = transport_config.transport_type

    for marker in request.node.iter_markers("transport"):
        if marker.args:
            transport_type = marker.args[0].lower()
            break

    # Route to appropriate transport
    if transport_type == "stdio":
        async with stdio_session(transport_config) as session:
            yield StdioTestClient(session)

    elif transport_type == "http":
        async with http_client(transport_config) as http_client_instance:
            yield HttpTestClient(http_client_instance)

    elif transport_type == "oauth":
        async with oauth_client(transport_config) as oauth_client_instance:
            yield OAuthTestClient(oauth_client_instance)

    else:
        raise ValueError(f"Unknown transport type: {transport_type}")


def get_transport_fixture(transport_type: str):
    """Get the appropriate fixture function for a transport type.

    Args:
        transport_type: One of 'stdio', 'http', 'oauth'

    Returns:
        The corresponding fixture function

    Raises:
        ValueError: If transport type is unknown
    """
    fixtures = {
        "stdio": stdio_session,
        "http": http_client,
        "oauth": oauth_client,
    }

    if transport_type not in fixtures:
        raise ValueError(f"Unknown transport type: {transport_type}. Must be one of: {list(fixtures.keys())}")

    return fixtures[transport_type]

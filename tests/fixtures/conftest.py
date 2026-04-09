"""Fixtures for transport-agnostic testing.

This conftest.py makes the transport fixtures available to all tests
in the tests/ directory and subdirectories.
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
    """Create a stdio transport client session."""
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
    """Create an HTTP transport client with API key authentication."""
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
    """Create an OAuth transport client."""
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
    """Generic client fixture that routes to the appropriate transport."""
    transport_type = transport_config.transport_type

    for marker in request.node.iter_markers("transport"):
        if marker.args:
            transport_type = marker.args[0].lower()
            break

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

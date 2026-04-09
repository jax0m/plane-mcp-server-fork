"""Abstract test client interface for transport-agnostic testing.

This module defines a unified interface for MCP clients that works
across all transport types (stdio, http, oauth).
"""

from abc import ABC, abstractmethod
from typing import Any


class AbstractTestClient(ABC):
    """Abstract interface for MCP test clients.

    All transport-specific clients should implement these methods
    to ensure consistent behavior across transports.
    """

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            The tool result
        """
        pass

    @abstractmethod
    async def list_tools(self) -> list:
        """List available tools.

        Returns:
            List of available tools
        """
        pass

    @property
    @abstractmethod
    def transport_type(self) -> str:
        """Get the transport type name."""
        pass


class StdioTestClient(AbstractTestClient):
    """Stdio transport wrapper using mcp.ClientSession.

    Wraps the stdio client session to provide the abstract interface.
    """

    def __init__(self, session):
        """Initialize with a stdio client session.

        Args:
            session: The mcp.ClientSession instance
        """
        self._session = session

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Call a tool via stdio transport."""
        return await self._session.call_tool(tool_name, arguments)

    async def list_tools(self) -> list:
        """List tools via stdio transport."""
        result = await self._session.list_tools()
        return result.tools

    @property
    def transport_type(self) -> str:
        return "stdio"


class HttpTestClient(AbstractTestClient):
    """HTTP transport wrapper using fastmcp.Client.

    Wraps the HTTP client to provide the abstract interface.
    """

    def __init__(self, client):
        """Initialize with an HTTP client.

        Args:
            client: The fastmcp.Client instance
        """
        self._client = client

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Call a tool via HTTP transport."""
        return await self._client.call_tool(tool_name, arguments)

    async def list_tools(self) -> list:
        """List tools via HTTP transport."""
        return await self._client.list_tools()

    @property
    def transport_type(self) -> str:
        return "http"


class OAuthTestClient(AbstractTestClient):
    """OAuth transport wrapper using fastmcp.Client.

    Wraps the OAuth client to provide the abstract interface.
    """

    def __init__(self, client):
        """Initialize with an OAuth client.

        Args:
            client: The fastmcp.Client instance
        """
        self._client = client

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Call a tool via OAuth transport."""
        return await self._client.call_tool(tool_name, arguments)

    async def list_tools(self) -> list:
        """List tools via OAuth transport."""
        return await self._client.list_tools()

    @property
    def transport_type(self) -> str:
        return "oauth"

"""Main entry point for the Plane MCP Server."""

import json
import logging
import os
import sys
from contextlib import asynccontextmanager, aclosing
from datetime import datetime, timezone
from enum import Enum

import uvicorn
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount

from plane_mcp.server import get_header_mcp, get_oauth_mcp, get_stdio_mcp


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging (Datadog, ELK, etc.)."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["error"] = {
                "type": type(record.exc_info[1]).__name__,
                "message": str(record.exc_info[1]),
            }
        return json.dumps(log_entry)


def configure_json_logging():
    """Replace FastMCP's Rich handlers with a JSON formatter on the fastmcp logger."""
    fastmcp_logger = logging.getLogger("fastmcp")

    # Remove all existing handlers (Rich)
    for handler in fastmcp_logger.handlers[:]:
        fastmcp_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JSONFormatter())
    fastmcp_logger.addHandler(handler)
    fastmcp_logger.setLevel(logging.INFO)
    fastmcp_logger.propagate = False


configure_json_logging()

logger = logging.getLogger("fastmcp.plane_mcp")


class ServerMode(Enum):
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"


@asynccontextmanager
async def combined_lifespan(oauth_app=None, header_app=None, sse_app=None):
    """Combine lifespans from OAuth and Header MCP apps."""
    # Collect lifespan context managers
    lifespan_managers = []
    if oauth_app:
        lifespan_managers.append(oauth_app.lifespan(oauth_app))
    if header_app:
        lifespan_managers.append(header_app.lifespan(header_app))
    if sse_app:
        lifespan_managers.append(sse_app.lifespan(sse_app))

    # Enter all lifespan managers
    entered = []
    try:
        for mgr in lifespan_managers:
            await mgr.__aenter__()
            entered.append(mgr)
        yield
    finally:
        # Exit all in reverse order
        for mgr in reversed(entered):
            await mgr.__aexit__(None, None, None)


def main() -> None:
    """Run the MCP server."""
    server_mode = ServerMode.STDIO
    if len(sys.argv) > 1:
        server_mode = ServerMode(sys.argv[1])

    if server_mode == ServerMode.STDIO:
        # Validate API_KEY and PLANE_WORKSPACE_SLUG are set
        if not os.getenv("PLANE_API_KEY"):
            raise ValueError("PLANE_API_KEY is not set")
        if not os.getenv("PLANE_WORKSPACE_SLUG"):
            raise ValueError("PLANE_WORKSPACE_SLUG is not set")

        get_stdio_mcp().run()
        return

    if server_mode == ServerMode.HTTP:
        # Check if OAuth is configured
        oauth_client_id = os.getenv("PLANE_OAUTH_PROVIDER_CLIENT_ID", "").strip()
        oauth_client_secret = os.getenv("PLANE_OAUTH_PROVIDER_CLIENT_SECRET", "").strip()
        oauth_enabled = bool(oauth_client_id and oauth_client_secret)

        # Always initialize header-based auth
        header_app = get_header_mcp().http_app()
        header_routes = [Mount("/http/api-key", app=header_app)]

        # Conditionally initialize OAuth apps
        oauth_app = None
        sse_app = None
        oauth_well_known = []
        sse_well_known = []

        if oauth_enabled:
            oauth_mcp = get_oauth_mcp("/http")
            oauth_app = oauth_mcp.http_app()
            header_routes.append(Mount("/http", app=oauth_app))
            oauth_well_known = oauth_mcp.auth.get_well_known_routes(mcp_path="/mcp")

            sse_mcp = get_oauth_mcp()
            sse_app = sse_mcp.http_app(transport="sse")
            header_routes.append(Mount("/", app=sse_app))
            sse_well_known = sse_mcp.auth.get_well_known_routes(mcp_path="/sse")
            logger.info("OAuth mode enabled")
        else:
            logger.warning("OAuth credentials not configured - running in header-only mode")
            logger.info("Use /http/api-key/mcp endpoint with x-api-key and x-workspace-slug headers")

        # Build app routes with lifespan
        # For header-only mode, use header_app's lifespan
        if oauth_enabled:
            async def app_lifespan(app):
                async with combined_lifespan(oauth_app, header_app, sse_app):
                    yield
        else:
            async def app_lifespan(app):
                async with header_app.lifespan(header_app):
                    yield

        app = Starlette(
            routes=[
                # Well-known routes (OAuth only)
                *oauth_well_known,
                *sse_well_known,
                # MCP endpoints
                *header_routes,
            ],
            lifespan=app_lifespan,
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Configure uvicorn loggers to use JSON formatting too
        for uv_logger_name in ("uvicorn", "uvicorn.error"):
            uv_logger = logging.getLogger(uv_logger_name)
            for h in uv_logger.handlers[:]:
                uv_logger.removeHandler(h)
            uv_handler = logging.StreamHandler(sys.stderr)
            uv_handler.setFormatter(JSONFormatter())
            uv_logger.addHandler(uv_handler)

        logger.info("Starting HTTP server at port 8211")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8211,
            log_level="info",
            access_log=False,
        )
        return


if __name__ == "__main__":
    main()

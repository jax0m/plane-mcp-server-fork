"""
⚠️ DEPRECATED: Legacy stdio integration tests.

These tests have been superseded by the modular transport-agnostic tests
in tests/test_modules/. This file is maintained for backward compatibility.

For new tests, use tests/test_modules/ which provides:
- Transport-agnostic testing (stdio, http, oauth)
- Better code organization
- Automatic cleanup via ResourceCleanup context manager
- Leftover cleanup from previous failed runs

Legacy tests will be removed in a future release.

Environment Variables Required:
    PLANE_API_KEY: API key for authentication
    PLANE_WORKSPACE_SLUG: Workspace slug for testing
    PLANE_BASE_URL: Plane API URL (default: https://api.plane.so)
"""

import os
import uuid
from typing import Any

import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def get_config():
    """Load test configuration from environment."""
    api_key = os.getenv("PLANE_API_KEY", "")
    workspace_slug = os.getenv("PLANE_WORKSPACE_SLUG", "")
    base_url = os.getenv("PLANE_BASE_URL", "https://api.plane.so")

    if not api_key or not workspace_slug:
        raise RuntimeError("Missing required env vars: PLANE_API_KEY, PLANE_WORKSPACE_SLUG")

    return {
        "api_key": api_key,
        "workspace_slug": workspace_slug,
        "base_url": base_url,
    }


def extract_result(result: Any) -> dict | list:
    """Extract data from MCP tool result."""
    if hasattr(result, "structured_content") and result.structured_content is not None:
        return result.structured_content
    if hasattr(result, "content") and result.content:
        import json

        content = result.content[0]
        if hasattr(content, "text"):
            try:
                return json.loads(content.text)
            except json.JSONDecodeError:
                return {"raw": content.text}
    return {}


def generate_test_id() -> str:
    """Generate a unique test identifier."""
    return uuid.uuid4().hex[:8]


@pytest.fixture
def server_params():
    """Create server parameters for stdio mode."""
    config = get_config()
    return StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "plane_mcp", "stdio"],
        env={
            **os.environ,
            "PLANE_API_KEY": config["api_key"],
            "PLANE_WORKSPACE_SLUG": config["workspace_slug"],
            "PLANE_BASE_URL": config["base_url"],
        },
    )


@pytest.fixture
def test_id():
    """Generate unique test ID for resource naming."""
    return generate_test_id()


@pytest.mark.integration
@pytest.mark.legacy
@pytest.mark.asyncio
async def test_tools_list(server_params):
    """Test that we can list available tools."""
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()

            assert len(tools.tools) > 0, "No tools returned from server"
            tool_names = {tool.name for tool in tools.tools}

            # Verify essential tools exist
            essential_tools = ["create_project", "list_projects", "delete_project"]
            for tool in essential_tools:
                assert tool in tool_names, f"Essential tool '{tool}' not found"

            print(f"✓ Found {len(tools.tools)} tools, essential tools verified")


@pytest.mark.integration
@pytest.mark.legacy
@pytest.mark.asyncio
async def test_project_lifecycle(server_params, test_id):
    """
    Full lifecycle test for projects:
    1. Check for any leftover test projects (cleanup)
    2. Create project
    3. Verify creation
    4. Test project operations
    5. Delete project
    6. Verify deletion
    """
    unique_id = test_id
    project_name = f"STDIO-TEST-{unique_id}"
    project_identifier = f"STD{unique_id[:3].upper()}"

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # STEP 1: Check for and cleanup any leftover test projects
            print("Step 1: Checking for leftover test projects...")
            list_result = await session.call_tool("list_projects", {})
            projects = extract_result(list_result)
            if isinstance(projects, dict):
                projects = projects.get("results", [])

            leftover_ids = []
            for proj in projects:
                if isinstance(proj, dict) and proj.get("name", "").startswith("STDIO-TEST-"):
                    leftover_ids.append(proj["id"])
                    print(f"  Found leftover: {proj['name']}")

            for lid in leftover_ids:
                try:
                    await session.call_tool("delete_project", {"project_id": lid})
                    print(f"  Cleaned up: {lid}")
                except Exception as e:
                    print(f"  Note: Could not cleanup {lid}: {e}")

            # STEP 2: Create project
            print("Step 2: Creating test project...")
            create_result = await session.call_tool(
                "create_project",
                {"name": project_name, "identifier": project_identifier},
            )
            created = extract_result(create_result)
            project_id = created.get("id")

            assert project_id, f"Project creation failed: {created}"
            print(f"  ✓ Created project: {project_id}")

            # STEP 3: Verify project exists and is retrievable
            print("Step 3: Verifying project creation...")
            retrieve_result = await session.call_tool("retrieve_project", {"project_id": project_id})
            retrieved = extract_result(retrieve_result)
            assert retrieved.get("id") == project_id, "Retrieved project ID mismatch"
            assert retrieved.get("name") == project_name, "Retrieved project name mismatch"
            print(f"  ✓ Project verified: {retrieved['name']}")

            # STEP 4: Test project update
            print("Step 4: Testing project update...")
            updated_name = f"{project_name}-UPDATED"
            update_result = await session.call_tool(
                "update_project",
                {"project_id": project_id, "name": updated_name},
            )
            updated = extract_result(update_result)
            assert updated.get("name") == updated_name, "Project update failed"
            print(f"  ✓ Project updated to: {updated_name}")

            # STEP 5: Delete project
            print("Step 5: Deleting test project...")
            delete_result = await session.call_tool("delete_project", {"project_id": project_id})
            print(f"  Delete result: {extract_result(delete_result)}")
            print("  ✓ Delete command executed")

            # STEP 6: Verify project is deleted
            print("Step 6: Verifying project deletion...")
            list_result = await session.call_tool("list_projects", {})
            projects = extract_result(list_result)
            if isinstance(projects, dict):
                projects = projects.get("results", [])

            remaining = [p for p in projects if p.get("id") == project_id]
            assert len(remaining) == 0, "Project still exists after deletion"
            print("  ✓ Project confirmed deleted")


@pytest.mark.integration
@pytest.mark.legacy
@pytest.mark.asyncio
async def test_work_item_lifecycle(server_params, test_id):
    """
    Full lifecycle test for work items:
    1. Create project (parent resource)
    2. Create work items
    3. Verify creation and relationships
    4. Test work item operations
    5. Delete work items
    6. Delete project
    7. Verify all cleanup
    """
    unique_id = test_id
    project_name = f"STDIO-WI-TEST-{unique_id}"
    project_identifier = f"WIST{unique_id[:3].upper()}"
    work_item_name_1 = f"Work Item 1-{unique_id}"
    work_item_name_2 = f"Work Item 2-{unique_id}"

    project_id = None
    work_item_ids = []

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # STEP 1: Create parent project
                print("Step 1: Creating parent project...")
                result = await session.call_tool(
                    "create_project",
                    {"name": project_name, "identifier": project_identifier},
                )
                project_id = extract_result(result).get("id")
                assert project_id, "Project creation failed"
                print(f"  ✓ Created project: {project_id}")

                # STEP 2: Create work items
                print("Step 2: Creating work items...")
                for wi_name in [work_item_name_1, work_item_name_2]:
                    result = await session.call_tool(
                        "create_work_item",
                        {"project_id": project_id, "name": wi_name},
                    )
                    wi_id = extract_result(result).get("id")
                    assert wi_id, f"Work item creation failed for {wi_name}"
                    work_item_ids.append(wi_id)
                    print(f"  ✓ Created work item: {wi_id}")

                # STEP 3: Verify work items exist
                print("Step 3: Verifying work items...")
                list_result = await session.call_tool("list_work_items", {"project_id": project_id})
                work_items = extract_result(list_result)
                if isinstance(work_items, dict):
                    work_items = work_items.get("results", [])

                found_ids = {wi.get("id") for wi in work_items if isinstance(wi, dict)}
                for wid in work_item_ids:
                    assert wid in found_ids, f"Work item {wid} not found in list"
                print("  ✓ All work items verified in project")

                # STEP 4: Test work item retrieval
                print("Step 4: Testing work item retrieval...")
                for wi_id in work_item_ids:
                    result = await session.call_tool(
                        "retrieve_work_item",
                        {"project_id": project_id, "work_item_id": wi_id},
                    )
                    retrieved = extract_result(result)
                    assert retrieved.get("id") == wi_id, "Work item retrieval failed"
                print("  ✓ All work items retrievable")

                # STEP 5: Delete work items
                print("Step 5: Deleting work items...")
                for wi_id in work_item_ids:
                    await session.call_tool(
                        "delete_work_item",
                        {"project_id": project_id, "work_item_id": wi_id},
                    )
                    print(f"  ✓ Deleted work item: {wi_id}")

                # STEP 6: Verify work items deleted
                print("Step 6: Verifying work item deletion...")
                list_result = await session.call_tool("list_work_items", {"project_id": project_id})
                work_items = extract_result(list_result)
                if isinstance(work_items, dict):
                    work_items = work_items.get("results", [])

                remaining = [wi for wi in work_items if wi.get("id") in work_item_ids]
                assert len(remaining) == 0, "Work items still exist after deletion"
                print("  ✓ All work items confirmed deleted")

                # STEP 7: Delete parent project
                print("Step 7: Deleting parent project...")
                await session.call_tool("delete_project", {"project_id": project_id})
                print(f"  ✓ Deleted project: {project_id}")

                # STEP 8: Verify project deleted
                print("Step 8: Verifying project deletion...")
                list_result = await session.call_tool("list_projects", {})
                projects = extract_result(list_result)
                if isinstance(projects, dict):
                    projects = projects.get("results", [])

                remaining = [p for p in projects if p.get("id") == project_id]
                assert len(remaining) == 0, "Project still exists after deletion"
                print("  ✓ Project confirmed deleted")

    except Exception:
        # Cleanup on failure
        print("\n⚠ Test failed, cleaning up resources...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                for wi_id in work_item_ids:
                    try:
                        await session.call_tool(
                            "delete_work_item",
                            {"project_id": project_id, "work_item_id": wi_id},
                        )
                    except Exception:
                        pass
                if project_id:
                    try:
                        await session.call_tool("delete_project", {"project_id": project_id})
                    except Exception:
                        pass
        raise


@pytest.mark.integration
@pytest.mark.legacy
@pytest.mark.asyncio
async def test_tool_availability(server_params):
    """
    Verify all expected tools are available and callable.
    This test validates the MCP server has all required tools registered.
    """
    expected_tools = [
        # Project tools
        "create_project",
        "list_projects",
        "retrieve_project",
        "update_project",
        "delete_project",
        # Work item tools
        "create_work_item",
        "list_work_items",
        "retrieve_work_item",
        "update_work_item",
        "delete_work_item",
    ]

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            available = {tool.name for tool in tools.tools}

            missing = []
            for expected in expected_tools:
                if expected not in available:
                    missing.append(expected)

            if missing:
                print(f"Missing tools: {missing}")
                print(f"Available: {sorted(available)}")

            assert len(missing) == 0, f"Missing {len(missing)} expected tools: {missing}"
            print(f"✓ All {len(expected_tools)} expected tools available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

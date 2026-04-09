"""Project lifecycle tests - transport agnostic.

These tests verify project CRUD operations work correctly across all
transport types (stdio, http, oauth).

All tests include:
- Leftover cleanup from previous failed runs
- Automatic cleanup via ResourceCleanup context manager
- Verification of deletion
"""

import pytest

from ..core.helpers import (
    ResourceCleanup,
    cleanup_leftover_projects,
    extract_result,
    generate_test_id,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_delete_project(client):
    """Test basic project creation and deletion.

    Creates a project, verifies it exists, deletes it, and verifies deletion.
    Also cleans up any leftover test projects from previous runs.

    Args:
        client: Transport-agnostic test client fixture
    """
    # Clean up any leftover test projects first
    print("Cleaning up leftover test projects...")
    cleaned = await cleanup_leftover_projects(client, prefix="TEST")
    if cleaned > 0:
        print(f"  ✓ Cleaned up {cleaned} leftover project(s)")

    test_id = generate_test_id()
    project_name = f"TEST-PROJECT-{test_id}"
    project_identifier = f"TST{test_id[:3].upper()}"

    async with ResourceCleanup(client) as cleanup:
        # Create project
        result = await client.call_tool(
            "create_project",
            {"name": project_name, "identifier": project_identifier},
        )
        project = extract_result(result)

        assert "id" in project, "Project creation failed - no ID returned"
        project_id = project["id"]
        cleanup.add_project(project_id)
        print(f"✓ Created project: {project_id}")

        # Verify project exists
        list_result = await client.call_tool("list_projects", {})
        projects = extract_result(list_result)

        if isinstance(projects, dict):
            projects = projects.get("results", [])

        found = any(p.get("id") == project_id for p in projects)
        assert found, f"Created project {project_id} not found in list"
        print("✓ Project verified in list")

        # Delete project
        await client.call_tool("delete_project", {"project_id": project_id})
        print(f"✓ Deleted project: {project_id}")
        cleanup.projects.remove(project_id)

        # Verify deletion
        list_result = await client.call_tool("list_projects", {})
        projects = extract_result(list_result)

        if isinstance(projects, dict):
            projects = projects.get("results", [])

        remaining = [p for p in projects if p.get("id") == project_id]
        assert len(remaining) == 0, f"Project {project_id} still exists after deletion"
        print("✓ Project confirmed deleted")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_project_retrieve(client):
    """Test project retrieval by ID.

    Creates a project, retrieves it by ID, verifies data, then cleans up.

    Args:
        client: Transport-agnostic test client fixture
    """
    test_id = generate_test_id()
    project_name = f"TEST-RETRIEVE-{test_id}"
    project_identifier = f"RET{test_id[:3].upper()}"
    project_description = f"Test project for retrieval {test_id}"

    async with ResourceCleanup(client) as cleanup:
        # Create project
        result = await client.call_tool(
            "create_project",
            {
                "name": project_name,
                "identifier": project_identifier,
                "description": project_description,
            },
        )
        project = extract_result(result)
        project_id = project["id"]
        cleanup.add_project(project_id)

        # Retrieve project
        retrieve_result = await client.call_tool(
            "retrieve_project",
            {"project_id": project_id},
        )
        retrieved = extract_result(retrieve_result)

        assert retrieved.get("id") == project_id, "Retrieved project ID mismatch"
        assert retrieved.get("name") == project_name, "Retrieved project name mismatch"
        assert retrieved.get("description") == project_description, "Retrieved description mismatch"
        print(f"✓ Project retrieved successfully: {retrieved['name']}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_project_update(client):
    """Test project update operations.

    Creates a project, updates it, verifies changes, then cleans up.

    Args:
        client: Transport-agnostic test client fixture
    """
    test_id = generate_test_id()
    project_name = f"TEST-UPDATE-{test_id}"
    project_identifier = f"UPD{test_id[:3].upper()}"
    updated_name = f"{project_name}-UPDATED"
    updated_description = "Updated description"

    async with ResourceCleanup(client) as cleanup:
        # Create project
        result = await client.call_tool(
            "create_project",
            {"name": project_name, "identifier": project_identifier},
        )
        project = extract_result(result)
        project_id = project["id"]
        cleanup.add_project(project_id)

        # Update project
        update_result = await client.call_tool(
            "update_project",
            {
                "project_id": project_id,
                "name": updated_name,
                "description": updated_description,
            },
        )
        updated = extract_result(update_result)

        assert updated.get("id") == project_id, "Updated project ID mismatch"
        assert updated.get("name") == updated_name, "Project name not updated"
        assert updated.get("description") == updated_description, "Description not updated"
        print(f"✓ Project updated: {updated_name}")

        # Verify update persisted
        retrieve_result = await client.call_tool(
            "retrieve_project",
            {"project_id": project_id},
        )
        retrieved = extract_result(retrieve_result)

        assert retrieved.get("name") == updated_name, "Update did not persist"
        print("✓ Update verified persisted")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_projects_pagination(client):
    """Test project listing with basic pagination verification.

    Verifies that list_projects returns a valid response structure.

    Args:
        client: Transport-agnostic test client fixture
    """
    list_result = await client.call_tool("list_projects", {})
    projects = extract_result(list_result)

    # Should return either a dict with 'results' or a list
    assert isinstance(projects, (dict, list)), f"Unexpected response type: {type(projects)}"

    if isinstance(projects, dict):
        assert "results" in projects or "projects" in projects, "Expected 'results' or 'projects' key in response"
        project_list = projects.get("results", projects.get("projects", []))
    else:
        project_list = projects

    assert isinstance(project_list, list), "Project list should be a list"
    print(f"✓ Listed {len(project_list)} projects")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_project_lifecycle_full(client):
    """Full project lifecycle test with leftover cleanup and deletion verification.

    This test provides equivalent coverage to the legacy test_project_lifecycle:
    1. Clean up leftover test projects
    2. Create project
    3. Verify creation
    4. Update project
    5. Delete project
    6. Verify deletion

    Args:
        client: Transport-agnostic test client fixture
    """
    # STEP 1: Clean up any leftover test projects
    print("Step 1: Cleaning up leftover test projects...")
    cleaned = await cleanup_leftover_projects(client, prefix="TEST")
    if cleaned > 0:
        print(f"  ✓ Cleaned up {cleaned} leftover project(s)")

    test_id = generate_test_id()
    project_name = f"TEST-LIFECYCLE-{test_id}"
    project_identifier = f"LFC{test_id[:3].upper()}"

    async with ResourceCleanup(client) as cleanup:
        # STEP 2: Create project
        print("Step 2: Creating test project...")
        create_result = await client.call_tool(
            "create_project",
            {"name": project_name, "identifier": project_identifier},
        )
        created = extract_result(create_result)
        project_id = created.get("id")

        assert project_id, f"Project creation failed: {created}"
        cleanup.add_project(project_id)
        print(f"  ✓ Created project: {project_id}")

        # STEP 3: Verify project exists and is retrievable
        print("Step 3: Verifying project creation...")
        retrieve_result = await client.call_tool(
            "retrieve_project",
            {"project_id": project_id},
        )
        retrieved = extract_result(retrieve_result)
        assert retrieved.get("id") == project_id, "Retrieved project ID mismatch"
        assert retrieved.get("name") == project_name, "Retrieved project name mismatch"
        print(f"  ✓ Project verified: {retrieved['name']}")

        # STEP 4: Test project update
        print("Step 4: Testing project update...")
        updated_name = f"{project_name}-UPDATED"
        update_result = await client.call_tool(
            "update_project",
            {"project_id": project_id, "name": updated_name},
        )
        updated = extract_result(update_result)
        assert updated.get("name") == updated_name, "Project update failed"
        print(f"  ✓ Project updated to: {updated_name}")

        # STEP 5: Delete project
        print("Step 5: Deleting test project...")
        delete_result = await client.call_tool(
            "delete_project",
            {"project_id": project_id},
        )
        print(f"  Delete result: {extract_result(delete_result)}")
        print("  ✓ Delete command executed")
        cleanup.projects.remove(project_id)

        # STEP 6: Verify project is deleted
        print("Step 6: Verifying project deletion...")
        list_result = await client.call_tool("list_projects", {})
        projects = extract_result(list_result)

        if isinstance(projects, dict):
            projects = projects.get("results", [])

        remaining = [p for p in projects if p.get("id") == project_id]
        assert len(remaining) == 0, "Project still exists after deletion"
        print("  ✓ Project confirmed deleted")

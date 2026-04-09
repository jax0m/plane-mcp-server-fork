"""Project lifecycle tests - transport agnostic.

These tests verify project CRUD operations work correctly across all
transport types (stdio, http, oauth).
"""

import pytest

from ..core.helpers import extract_result, generate_test_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_delete_project(client):
    """Test basic project creation and deletion.

    Creates a project, verifies it exists, then deletes it.

    Args:
        client: Transport-agnostic test client fixture
    """
    test_id = generate_test_id()
    project_name = f"TEST-PROJECT-{test_id}"
    project_identifier = f"TST{test_id[:3].upper()}"

    # Create project
    result = await client.call_tool(
        "create_project",
        {"name": project_name, "identifier": project_identifier},
    )
    project = extract_result(result)

    assert "id" in project, "Project creation failed - no ID returned"
    project_id = project["id"]
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

    try:
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

    finally:
        # Cleanup
        await client.call_tool("delete_project", {"project_id": project_id})
        print(f"✓ Cleaned up project: {project_id}")


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

    # Create project
    result = await client.call_tool(
        "create_project",
        {"name": project_name, "identifier": project_identifier},
    )
    project = extract_result(result)
    project_id = project["id"]

    try:
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

    finally:
        # Cleanup
        await client.call_tool("delete_project", {"project_id": project_id})
        print(f"✓ Cleaned up project: {project_id}")


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

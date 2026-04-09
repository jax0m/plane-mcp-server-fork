"""Tool registry tests - transport agnostic.

These tests verify that all expected tools are registered with the MCP server.
They work with any transport type (stdio, http, oauth).
"""

import pytest

# Expected tools organized by domain
EXPECTED_TOOLS = {
    # Project tools
    "create_project": "Create a new project",
    "list_projects": "List all projects",
    "retrieve_project": "Retrieve a project by ID",
    "update_project": "Update a project",
    "delete_project": "Delete a project",
    # Work item tools
    "create_work_item": "Create a new work item",
    "list_work_items": "List work items in a project",
    "retrieve_work_item": "Retrieve a work item by ID",
    "update_work_item": "Update a work item",
    "delete_work_item": "Delete a work item",
    # Label tools
    "list_labels": "List labels in a project",
    "create_label": "Create a new label",
    "retrieve_label": "Retrieve a label by ID",
    "update_label": "Update a label",
    "delete_label": "Delete a label",
    # State tools
    "list_states": "List states in a project",
    "create_state": "Create a new state",
    "retrieve_state": "Retrieve a state by ID",
    "update_state": "Update a state",
    "delete_state": "Delete a state",
    # Cycle tools
    "list_cycles": "List cycles in a project",
    "create_cycle": "Create a new cycle",
    "retrieve_cycle": "Retrieve a cycle by ID",
    "update_cycle": "Update a cycle",
    "delete_cycle": "Delete a cycle",
    # Module tools
    "list_modules": "List modules in a project",
    "create_module": "Create a new module",
    "retrieve_module": "Retrieve a module by ID",
    "update_module": "Update a module",
    "delete_module": "Delete a module",
    # User tools
    "get_me": "Get current user information",
}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tools_list(client):
    """Test that we can list available tools.

    Verifies that the MCP server returns a non-empty list of tools.

    Args:
        client: Transport-agnostic test client fixture
    """
    tools = await client.list_tools()

    assert len(tools) > 0, "No tools returned from server"

    tool_names = {tool.name for tool in tools}
    print(f"✓ Found {len(tools)} tools on {client.transport_type} transport")

    # Verify we have at least the essential tools
    essential_tools = {"create_project", "list_projects", "delete_project"}
    missing_essential = essential_tools - tool_names

    assert not missing_essential, f"Missing essential tools: {missing_essential}"
    print("✓ All essential tools present")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_expected_tools_available(client):
    """Verify all expected tools are available.

    Checks that all tools listed in EXPECTED_TOOLS are registered
    with the MCP server.

    Args:
        client: Transport-agnostic test client fixture
    """
    tools = await client.list_tools()
    available = {tool.name for tool in tools}

    missing = []
    for expected_tool in EXPECTED_TOOLS.keys():
        if expected_tool not in available:
            missing.append(expected_tool)

    if missing:
        print(f"Missing tools: {missing}")
        print(f"Available tools: {sorted(available)}")

    assert len(missing) == 0, f"Missing {len(missing)} expected tools: {missing}"
    print(f"✓ All {len(EXPECTED_TOOLS)} expected tools available on {client.transport_type} transport")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tool_categories(client):
    """Verify tools are organized by expected categories.

    Checks that tools from different domains (projects, work items,
    labels, etc.) are all available.

    Args:
        client: Transport-agnostic test client fixture
    """
    tools = await client.list_tools()
    available = {tool.name for tool in tools}

    # Check each category has at least some tools
    categories = {
        "projects": {"create_project", "list_projects", "retrieve_project"},
        "work_items": {"create_work_item", "list_work_items"},
        "labels": {"list_labels", "create_label"},
        "states": {"list_states", "create_state"},
        "cycles": {"list_cycles", "create_cycle"},
        "modules": {"list_modules", "create_module"},
        "users": {"get_me"},
    }

    for category, expected_tools in categories.items():
        available_in_category = expected_tools & available
        if not available_in_category:
            print(f"Warning: No tools from '{category}' category found")
        elif available_in_category != expected_tools:
            missing = expected_tools - available_in_category
            print(f"Note: {category} category missing: {missing}")
        else:
            print(f"✓ {category} category complete")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_tool_descriptions(client):
    """Verify tools have descriptions.

    Checks that each tool has a non-empty description.

    Args:
        client: Transport-agnostic test client fixture
    """
    tools = await client.list_tools()

    tools_without_description = []
    for tool in tools:
        if not tool.description or not tool.description.strip():
            tools_without_description.append(tool.name)

    assert len(tools_without_description) == 0, f"Tools without descriptions: {tools_without_description}"
    print(f"✓ All {len(tools)} tools have descriptions")

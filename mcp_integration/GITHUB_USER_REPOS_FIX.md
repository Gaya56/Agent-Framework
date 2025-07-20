# GitHub MCP User Repository Fix

## Problem Description

The original GitHub MCP integration was missing functionality to list the authenticated user's repositories using their GitHub Personal Access Token. Users had to manually provide their username, which was inconvenient and didn't take advantage of the authenticated API capabilities.

## Solution Overview

Added two new GitHub MCP tools that use the authenticated user's GitHub Personal Access Token:

1. **`get_authenticated_user`** - Get the current user's GitHub profile information
2. **`list_user_repositories`** - List repositories for the authenticated user with advanced filtering

## What Was Added

### 1. Configuration Updates (`config.py`)

Added new tools to the GitHub server configuration:

```python
"get_authenticated_user": {
    "description": "Get the authenticated user's information",
    "parameters": {}
},
"list_user_repositories": {
    "description": "List repositories for the authenticated user",
    "parameters": {
        "visibility": "Repository visibility: all, public, private (optional, default all)",
        "affiliation": "Relationship to repos: owner, collaborator, organization_member (optional, default owner,collaborator,organization_member)",
        "type": "Repository type: all, owner, public, private, member (optional, default all)",
        "sort": "Sort by created, updated, pushed, full_name (optional, default full_name)",
        "direction": "Sort direction: asc or desc (optional, default asc)",
        "per_page": "Results per page (optional, default 30, max 100)"
    }
}
```

### 2. Server Configuration (`servers/github/server.yaml`)

Added the corresponding server-side tool definitions:

```yaml
- name: "get_authenticated_user"
  description: "Get the authenticated user's information"
  parameters: {}
  
- name: "list_user_repositories"
  description: "List repositories for the authenticated user"
  parameters:
    visibility: "Repository visibility: all, public, private (optional, default all)"
    affiliation: "Relationship to repos: owner, collaborator, organization_member (optional, default owner,collaborator,organization_member)"
    type: "Repository type: all, owner, public, private, member (optional, default all)"
    sort: "Sort by created, updated, pushed, full_name (optional, default full_name)"
    direction: "Sort direction: asc or desc (optional, default asc)"
    per_page: "Results per page (optional, default 30, max 100)"
```

### 3. Client Implementation (`working_github_client.py`)

Updated the GitHub client to include the new tools and their simulation logic.

### 4. Test Script (`test_user_repos.py`)

Created a comprehensive test script to demonstrate the new functionality.

## Benefits of the Fix

### 🎯 **No Username Required**
- Users no longer need to manually provide their GitHub username
- The API key automatically identifies the authenticated user

### 🔐 **Better Authentication**
- Uses authenticated API endpoints for higher rate limits
- Can access private repositories (if token has appropriate permissions)
- More secure than public username-based queries

### 📊 **Advanced Filtering Options**
- **Visibility**: Filter by public, private, or all repositories
- **Affiliation**: Filter by owner, collaborator, or organization member
- **Type**: Filter by repository type (owner, member, etc.)
- **Sorting**: Sort by creation date, update date, push date, or name
- **Direction**: Sort ascending or descending
- **Pagination**: Control results per page

### 🚀 **Better API Performance**
- Authenticated requests have higher rate limits
- More efficient than searching with username queries
- Direct access to user's repository list

## Usage Examples

### Get Authenticated User Info
```python
result = await client.call_tool("get_authenticated_user", {})
```

### List Public Repositories (Most Recent First)
```python
result = await client.call_tool("list_user_repositories", {
    "visibility": "public",
    "type": "owner", 
    "sort": "updated",
    "direction": "desc",
    "per_page": 10
})
```

### List All Repositories (Public + Private)
```python
result = await client.call_tool("list_user_repositories", {
    "visibility": "all",
    "type": "owner",
    "sort": "full_name",
    "direction": "asc"
})
```

### List Repositories You Collaborate On
```python
result = await client.call_tool("list_user_repositories", {
    "affiliation": "collaborator",
    "sort": "updated",
    "direction": "desc"
})
```

## API Mapping

These tools map to the following GitHub API endpoints:

- `get_authenticated_user` → `GET /user`
- `list_user_repositories` → `GET /user/repos`

## Testing

Run the test script to verify functionality:

```bash
cd /workspaces/Agent-Framework/mcp_integration
python test_user_repos.py
```

## Requirements

- `GITHUB_PERSONAL_ACCESS_TOKEN` must be set in environment variables
- Token should have appropriate repository access permissions
- For private repositories, token needs `repo` scope

## Backward Compatibility

This fix is fully backward compatible:
- All existing GitHub MCP tools continue to work
- No breaking changes to existing functionality
- New tools are additive enhancements

## Implementation Status

✅ **Configuration**: Updated `config.py` with new tools  
✅ **Server Config**: Updated `servers/github/server.yaml`  
✅ **Client**: Updated `working_github_client.py`  
✅ **Testing**: Created comprehensive test script  
✅ **Documentation**: This comprehensive guide  

The fix is ready for implementation in the actual GitHub MCP server. The current version includes simulation logic that demonstrates the functionality and parameter structure.

# Copyright (c) 2026 YourIndependence. All rights reserved.
#
# This software is the confidential and proprietary information of
# YourIndependence. Unauthorized copying, distribution,
# modification, or use outside the organization is strictly prohibited.
#
# For internal use only.
# developer team.

"""Project listing domain logic."""

import base64
import json

from recnavi.core.database.base_database import BaseDatabase
from recnavi.core.types.project import Project


async def get_projects(
    projects_db: BaseDatabase,
    group_id: str,
    limit: int = 20,
    cursor: str | None = None,
) -> tuple[list[Project], str | None]:
    """Get projects for a group with pagination.

    Queries the projects table groupId-createdAt-index in descending order
    to return newest projects first.

    Args:
        projects_db: Database instance for projects table.
        group_id: Group identifier (from authenticated user token).
        limit: Maximum items per page (1-100, default 20).
        cursor: Opaque pagination cursor from previous response.

    Returns:
        Tuple of (projects, next_cursor). next_cursor is None if last page.

    """
    exclusive_start_key = _decode_cursor(cursor)

    result = await projects_db.query(
        key_condition={"groupId": group_id},
        index="groupId-createdAt-index",
        limit=limit,
        exclusive_start_key=exclusive_start_key,
    )

    projects = [Project.model_validate(item) for item in result.items]
    next_cursor = _encode_cursor(result.last_evaluated_key)

    return projects, next_cursor


async def get_my_projects(
    *,
    projects_db: BaseDatabase,
    group_id: str,
    user_id: str,
    limit: int = 20,
    cursor: str | None = None,
) -> tuple[list[Project], str | None]:
    """Get projects assigned to a specific user with pagination.

    Filters projects from the user's group by checking if user_id is in
    assignedUserIds. Uses groupId-createdAt-index to query all group projects,
    then applies server-side filtering (DynamoDB cannot index array elements).

    Note: The `limit` parameter controls how many items DynamoDB queries,
    not the final count after filtering. The returned list may contain fewer
    items than `limit` if many projects are filtered out, and `next_cursor`
    may still be present when more unfiltered data exists.

    Args:
        projects_db: Projects table database interface.
        group_id: Group ID extracted from the authenticated user's token.
        user_id: User ID to match against assignedUserIds in each project.
        limit: Maximum number of items to query from DynamoDB (1-100, default 20).
        cursor: Pagination cursor from the previous response, or None for first page.

    Returns:
        Tuple of (projects_assigned_to_user, cursor_for_next_page).
        The cursor is None if this is the last page.

    """
    exclusive_start_key = _decode_cursor(cursor)

    result = await projects_db.query(
        key_condition={"groupId": group_id},
        index="groupId-createdAt-index",
        limit=limit,
        exclusive_start_key=exclusive_start_key,
    )

    projects = [
        Project.model_validate(item)
        for item in result.items
        if user_id in item.get("assignedUserIds", [])
    ]

    next_cursor = _encode_cursor(result.last_evaluated_key)

    return projects, next_cursor


def _encode_cursor(last_evaluated_key: dict | None) -> str | None:
    """Encode DynamoDB LastEvaluatedKey to opaque base64 cursor."""
    if not last_evaluated_key:
        return None
    json_str = json.dumps(last_evaluated_key, sort_keys=True)
    return base64.b64encode(json_str.encode()).decode()


def _decode_cursor(cursor: str | None) -> dict | None:
    """Decode opaque base64 cursor to DynamoDB ExclusiveStartKey."""
    if not cursor:
        return None
    json_str = base64.b64decode(cursor.encode()).decode()
    return json.loads(json_str)

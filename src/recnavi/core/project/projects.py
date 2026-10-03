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
    *,
    projects_db: BaseDatabase,
    user_id: str,
    group_id: str,
    limit: int = 20,
    cursor: str | None = None,
) -> tuple[list[Project], str | None]:
    """Get projects assigned to user_id with pagination.

    Args:
        projects_db: Database instance.
        user_id: User identifier.
        group_id: User group identifier.
        limit: Maximum items per page.
        cursor: Opaque pagination cursor from the previous response.

    Note: limit is the query size, not result count after filtering.

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
    ]

    projects = [project for project in projects
        if (
                user_id in project.assigned_user_ids
                or user_id in project.owner_user_id
        )
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
